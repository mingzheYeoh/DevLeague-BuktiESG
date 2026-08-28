<#
.SYNOPSIS
    Local demo driver for BuktiESG: start the stack, reset between runs, stop it.

.DESCRIPTION
    Three subcommands.

      .\demo.ps1 up      Postgres -> migrations -> API, worker and web in panes,
                         then waits until both HTTP ports actually answer.
      .\demo.ps1 reset   Deletes every case in the demo organization through the
                         API, so the next run starts from account + org only.
      .\demo.ps1 down    Stops Postgres and frees ports 8000 and 3000.

    For demonstrating on a developer machine. This is not a deployment tool, and
    it assumes `uv sync` and `npm install` have already been run.
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('up', 'reset', 'down')]
    [string]$Command = 'up'
)

$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot

# 127.0.0.1 rather than `localhost`, for the reason app/config.py gives about its
# own database URL: on Windows `localhost` resolves to ::1 first, nothing is
# listening there, and the connection stalls until that attempt times out before
# retrying IPv4. A demo that pauses on every call looks broken.
$ApiBase = 'http://127.0.0.1:8000'

# `localhost`, not 127.0.0.1, and only for the browser. The frontend calls
# NEXT_PUBLIC_API_BASE_URL, which defaults to http://localhost:8000, so opening
# the UI on 127.0.0.1:3000 makes every API call cross-origin. Measured on this
# machine, that page hangs on "Checking your session..." indefinitely - no
# request, no console error, no way for the user to tell what is wrong. The
# origins are configured as equals in cors_allow_origins and they do not behave
# as equals; the demo opens the one that works.
$WebBase = 'http://localhost:3000'
$Ports = @(8000, 3000)

function Write-Step($Message) { Write-Host "==> $Message" -ForegroundColor Cyan }
function Write-Ok($Message) { Write-Host "    $Message" -ForegroundColor Green }
function Write-Note($Message) { Write-Host "    $Message" -ForegroundColor Yellow }

function Read-DotEnv {
    # The one .env at the repository root - the same file docker-compose.yml and
    # app/config.py read. Parsed rather than sourced: PowerShell has no `source`,
    # and only a few keys are wanted.
    $path = Join-Path $Root '.env'
    $map = @{}
    if (-not (Test-Path $path)) { return $map }
    foreach ($line in Get-Content $path) {
        $trimmed = $line.Trim()
        if ($trimmed -eq '' -or $trimmed.StartsWith('#')) { continue }
        $split = $trimmed.IndexOf('=')
        if ($split -lt 1) { continue }
        $key = $trimmed.Substring(0, $split).Trim()
        $value = $trimmed.Substring($split + 1).Trim().Trim('"').Trim("'")
        $map[$key] = $value
    }
    return $map
}

function Wait-Until {
    param(
        [scriptblock]$Condition,
        [string]$Description,
        [int]$TimeoutSeconds = 60
    )
    # Polls for a real signal instead of sleeping a guessed number of seconds.
    # Every step below that could plausibly "probably be ready by now" goes
    # through here: the failure mode of guessing is opening a dead link in front
    # of an audience.
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try { if (& $Condition) { return $true } } catch { }
        Start-Sleep -Milliseconds 700
    }
    throw "Timed out after $TimeoutSeconds s waiting for: $Description"
}

function Test-HttpOk($Url) {
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
        return $response.StatusCode -eq 200
    }
    catch { return $false }
}

function Stop-Port($Port) {
    # Closing a pane can leave its port held: both `npm run dev` and
    # `uvicorn --reload` outlive the window that started them.
    #
    # Killing the process that owns the socket is not enough. `uvicorn --reload`
    # is a supervisor plus a child, and the child is the one listening - kill it
    # and the supervisor immediately spawns a replacement, so the port is free
    # for about a second and then held by a new pid. Walk up to the outermost
    # runtime process and kill that subtree instead.
    #
    # The walk stops as soon as the parent is not itself a runtime, so it can
    # never climb out of the dev server and into the terminal that launched it.
    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $connections) { return $false }

    $targets = New-Object 'System.Collections.Generic.HashSet[int]'

    foreach ($reported in ($connections.OwningProcess | Select-Object -Unique)) {
        # The table's OwningProcess is not reliably the live listener. Uvicorn
        # spawns its server through multiprocessing; kill the supervisor and the
        # child is orphaned but goes on listening, while the socket keeps naming
        # the pid that has already exited. Observed here: the table said 46924,
        # that pid did not exist, and the real listener was 40152 - its child.
        # So take the reported pid and anything parented to it.
        [void]$targets.Add([int]$reported)
        Get-CimInstance Win32_Process -Filter "ParentProcessId=$reported" -ErrorAction SilentlyContinue |
        ForEach-Object { [void]$targets.Add([int]$_.ProcessId) }

        # Then walk up, for the opposite case: the supervisor is alive, and
        # killing only the listening child lets it spawn a replacement.
        $top = [int]$reported
        while ($true) {
            $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$top" -ErrorAction SilentlyContinue
            if (-not $proc) { break }
            $parent = Get-CimInstance Win32_Process -Filter "ProcessId=$($proc.ParentProcessId)" -ErrorAction SilentlyContinue
            if (-not $parent) { break }
            if ($parent.Name -notmatch '^(python|uv|node|npm)') { break }
            $top = [int]$parent.ProcessId
            [void]$targets.Add($top)
        }
    }

    foreach ($processId in $targets) {
        # /T takes the children the walk above deliberately did not enumerate.
        #
        # Run through cmd so that cmd swallows both streams. Redirecting a native
        # command's stderr inside Windows PowerShell wraps each line in a
        # NativeCommandError, which $ErrorActionPreference = 'Stop' turns into a
        # terminating error - so `taskkill` reporting that an already-exited pid
        # was not found would abort the teardown it was asked to perform.
        cmd /c "taskkill /PID $processId /T /F >nul 2>&1"
    }
    return $true
}

function Stop-RepoProcess {
    # The worker listens on nothing, so freeing ports never reaches it and an
    # earlier version of this script left it polling after `down` reported
    # success. Identify it the only way that is actually specific: a runtime
    # process whose command line names this repository.
    #
    # Matching on the path is what keeps this safe. Other node processes - and
    # on this machine there are several - are untouched because their command
    # lines point somewhere else.
    $matched = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -match '^(python|uv|node|npm)' -and
        $_.CommandLine -and
        $_.CommandLine.Contains($Root)
    }

    $count = 0
    foreach ($proc in $matched) {
        cmd /c "taskkill /PID $($proc.ProcessId) /T /F >nul 2>&1"
        $count++
    }
    return $count
}

function Start-Panes {
    $backend = Join-Path $Root 'backend'
    $frontend = Join-Path $Root 'frontend'

    # One pre-quoted string per process, never an array. Start-Process joins an
    # -ArgumentList array with spaces and quotes nothing, so any element holding
    # a space is silently split into several arguments - and this repository's
    # own path contains one. The symptom was a terminal window that opened with
    # no processes in it, nothing on either port, and no error anywhere: the same
    # shape as an unescaped password moving a URL's host boundary, one layer up.
    $api = "powershell -NoExit -Command `"uv run uvicorn app.main:app --reload`""
    $worker = "powershell -NoExit -Command `"uv run python worker.py`""
    $web = "powershell -NoExit -Command `"npm run dev`""

    $wt = Get-Command wt -ErrorAction SilentlyContinue
    if ($wt) {
        $layout = "new-tab --title API -d `"$backend`" $api" +
        " ; split-pane --title worker -d `"$backend`" $worker" +
        " ; split-pane --title web -d `"$frontend`" $web"
        Start-Process wt -ArgumentList $layout
        Write-Ok 'three panes in Windows Terminal'
        return
    }

    Write-Note 'wt not found - falling back to three separate windows'
    Start-Process powershell -ArgumentList "-NoExit -Command `"Set-Location '$backend'; uv run uvicorn app.main:app --reload`""
    Start-Process powershell -ArgumentList "-NoExit -Command `"Set-Location '$backend'; uv run python worker.py`""
    Start-Process powershell -ArgumentList "-NoExit -Command `"Set-Location '$frontend'; npm run dev`""
}

function Invoke-Up {
    $envMap = Read-DotEnv

    Write-Step 'Checking configuration'
    if (-not $envMap.ContainsKey('POSTGRES_PASSWORD') -or -not $envMap['POSTGRES_PASSWORD']) {
        throw "POSTGRES_PASSWORD is not set in $Root\.env - copy .env.example and set it."
    }
    Write-Ok '.env has POSTGRES_PASSWORD'

    # The demo is meant to show real extraction. Without the key the worker falls
    # back to NullExtractor: jobs still complete and every value stays null, so
    # nothing errors and the demo is quietly less than intended. Worth a warning
    # precisely because it does not announce itself.
    if (-not $envMap['DEEPSEEK_API_KEY']) {
        Write-Note 'DEEPSEEK_API_KEY is not set - the worker will use NullExtractor and extract no values.'
    }
    else {
        Write-Ok 'DEEPSEEK_API_KEY is set - real extraction.'
        Write-Note 'Upload only from sample/ while the key is set (AGENTS.md 3.1).'
    }

    Write-Step 'Starting PostgreSQL'
    docker compose up -d | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'docker compose up failed - is Docker Desktop running?' }
    Wait-Until -Description 'postgres healthcheck' -Condition {
        (docker inspect --format '{{.State.Health.Status}}' buktiesg-postgres 2>$null) -eq 'healthy'
    } | Out-Null
    Write-Ok 'buktiesg-postgres healthy'

    Write-Step 'Applying migrations'
    Push-Location (Join-Path $Root 'backend')
    try {
        uv run alembic upgrade head
        if ($LASTEXITCODE -ne 0) { throw 'alembic upgrade head failed' }
    }
    finally { Pop-Location }
    Write-Ok 'schema at head'

    Write-Step 'Launching API, worker and web'
    Start-Panes

    Write-Step 'Waiting for both ports to answer'
    Wait-Until -Description "$ApiBase/health" -TimeoutSeconds 90 -Condition { Test-HttpOk "$ApiBase/health" } | Out-Null
    Write-Ok "API   $ApiBase/health"
    Wait-Until -Description $WebBase -TimeoutSeconds 150 -Condition { Test-HttpOk $WebBase } | Out-Null
    Write-Ok "Web   $WebBase"

    Write-Host ''
    Write-Host "Ready. Open $WebBase" -ForegroundColor Green
    Write-Host 'Runbook: DEMO.md' -ForegroundColor Green
}

function Get-DemoCredential {
    # Never generated or stored by this script. It reads what you set and
    # otherwise asks; the password is not echoed and not written anywhere.
    $envMap = Read-DotEnv

    $email = $env:DEMO_EMAIL
    if (-not $email) { $email = $envMap['DEMO_EMAIL'] }
    if (-not $email) { $email = Read-Host 'Demo account email' }

    $password = $env:DEMO_PASSWORD
    if (-not $password) { $password = $envMap['DEMO_PASSWORD'] }
    if (-not $password) {
        $secure = Read-Host "Password for $email" -AsSecureString
        $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        try { $password = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr) }
        finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
    }

    return @{ email = $email; password = $password }
}

function Invoke-Reset {
    if (-not (Test-HttpOk "$ApiBase/health")) {
        throw "The API is not answering at $ApiBase - run .\demo.ps1 up first."
    }

    $credential = Get-DemoCredential
    $session = $null

    Write-Step 'Signing in'
    $body = @{ email = $credential.email; password = $credential.password } | ConvertTo-Json
    try {
        Invoke-RestMethod -Uri "$ApiBase/api/v1/auth/login" -Method Post -Body $body `
            -ContentType 'application/json' -SessionVariable session | Out-Null
    }
    catch {
        throw "Login failed for $($credential.email): $($_.Exception.Message)"
    }
    Write-Ok "signed in as $($credential.email)"

    # Deleted through the API rather than by truncating tables, because nothing in
    # the database owns the uploaded bytes and the row cascade alone would leave
    # them on disk forever. DELETE /cases/{id} takes the stored directory too -
    # backend/tests/test_case_delete.py pins that.
    Write-Step 'Deleting cases'
    $cases = @(Invoke-RestMethod -Uri "$ApiBase/api/v1/cases" -WebSession $session)
    if ($cases.Count -eq 0) {
        Write-Ok 'nothing to delete'
    }
    else {
        foreach ($case in $cases) {
            Invoke-RestMethod -Uri "$ApiBase/api/v1/cases/$($case.id)" -Method Delete -WebSession $session | Out-Null
            Write-Ok "deleted $($case.id)"
        }
    }

    Write-Step 'Verifying'
    $remaining = @(Invoke-RestMethod -Uri "$ApiBase/api/v1/cases" -WebSession $session)
    if ($remaining.Count -ne 0) { throw "Reset incomplete: $($remaining.Count) case(s) still listed." }
    Write-Ok 'API lists 0 cases'

    # Checked independently of the API's own answer, the same way a live database
    # is worth a look with psql rather than trusting the endpoint that wrote to it.
    $storage = Join-Path $Root 'backend\var\storage'
    if (Test-Path $storage) {
        $leftover = @(Get-ChildItem $storage -Directory -ErrorAction SilentlyContinue)
        if ($leftover.Count -ne 0) {
            Write-Note "$($leftover.Count) directory(ies) left under backend\var\storage, owned by no case:"
            $leftover | ForEach-Object { Write-Note "  $($_.Name)" }
        }
        else {
            Write-Ok 'backend\var\storage is empty'
        }
    }
    else {
        Write-Ok 'backend\var\storage does not exist yet'
    }

    Write-Host ''
    Write-Host 'Clean. Account and organization kept.' -ForegroundColor Green
}

function Invoke-Down {
    Write-Step 'Stopping this repository''s processes'
    $stopped = Stop-RepoProcess
    Write-Ok "$stopped process(es) named this repository"

    Write-Step 'Freeing ports'
    foreach ($port in $Ports) {
        if (Stop-Port $port) { Write-Ok "stopped whatever held $port" } else { Write-Ok "$port already free" }
    }

    # Checked after a wait, not immediately: a killed tree takes a moment to
    # release its socket, and an instant check reports a failure that is not one.
    foreach ($port in $Ports) {
        try {
            Wait-Until -TimeoutSeconds 15 -Description "port $port to be released" -Condition {
                -not (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
            } | Out-Null
            Write-Ok "$port released"
        }
        catch {
            Write-Note "$port is still held - close its window manually"
        }
    }

    Write-Step 'Stopping PostgreSQL'
    docker compose stop | Out-Null
    Write-Ok 'buktiesg-postgres stopped (the named volume keeps the data)'
}

switch ($Command) {
    'up' { Invoke-Up }
    'reset' { Invoke-Reset }
    'down' { Invoke-Down }
}

