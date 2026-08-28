#!/usr/bin/env bash
#
# Local demo driver for BuktiESG on macOS and Linux: start the stack, reset
# between runs, stop it. The companion to demo.ps1, which does the same three
# things on Windows.
#
#   ./demo.sh up      Postgres -> migrations -> API, worker and web, then waits
#                     until both HTTP ports actually answer.
#   ./demo.sh reset   Deletes every case in the demo organization through the
#                     API, so the next run starts from account + org only.
#   ./demo.sh down    Stops Postgres and frees ports 8000 and 3000.
#
# For demonstrating on a developer machine. This is not a deployment tool, and
# it assumes `uv sync` and `npm ci` have already been run.
#
# Written for bash 3.2, which is what macOS still ships: no associative arrays,
# no `readarray`, no `${var,,}`.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

API_BASE="http://127.0.0.1:8000"

# `localhost`, not 127.0.0.1, and only for the browser. The frontend calls
# NEXT_PUBLIC_API_BASE_URL, which defaults to http://localhost:8000, so opening
# the UI on 127.0.0.1:3000 makes every API call cross-origin. That path is worse
# than it sounds - see the note in demo.ps1 and the timeout in lib/api/client.ts.
WEB_BASE="http://localhost:3000"

LOG_DIR="$ROOT/backend/var/log"

if [ -t 1 ]; then
  C_STEP=$'\033[36m'; C_OK=$'\033[32m'; C_NOTE=$'\033[33m'; C_OFF=$'\033[0m'
else
  C_STEP=''; C_OK=''; C_NOTE=''; C_OFF=''
fi

step() { printf '%s==> %s%s\n' "$C_STEP" "$1" "$C_OFF"; }
ok()   { printf '%s    %s%s\n' "$C_OK" "$1" "$C_OFF"; }
note() { printf '%s    %s%s\n' "$C_NOTE" "$1" "$C_OFF"; }
die()  { printf 'error: %s\n' "$1" >&2; exit 1; }

# Read one key out of the repository-root .env - the same file docker-compose.yml
# and backend/app/config.py read. Parsed rather than sourced: sourcing a file of
# unknown content executes it.
dotenv() {
  local key="$1"
  [ -f "$ROOT/.env" ] || return 0
  sed -n "s/^[[:space:]]*${key}[[:space:]]*=[[:space:]]*//p" "$ROOT/.env" \
    | head -n 1 \
    | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//"
}

# Polls for a real signal instead of sleeping a guessed number of seconds. Every
# step that could plausibly "probably be ready by now" goes through here: the
# failure mode of guessing is opening a dead link in front of an audience.
#
# Returns 1 on timeout rather than exiting, so a caller that only wants to warn
# can. `up` turns that into a hard failure; `down` reports it and carries on.
wait_until() {
  local timeout="$1"; shift 2
  local deadline=$(( $(date +%s) + timeout ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    if "$@" >/dev/null 2>&1; then return 0; fi
    sleep 1
  done
  return 1
}

http_ok() { curl -fsS --max-time 3 -o /dev/null "$1"; }

postgres_healthy() {
  [ "$(docker inspect --format '{{.State.Health.Status}}' buktiesg-postgres 2>/dev/null)" = healthy ]
}

# Run a JSON helper on the backend's interpreter. uv is already a prerequisite,
# so this needs no jq and no system python.
py() { (cd "$ROOT/backend" && uv run --quiet python -c "$1" "${@:2}"); }

start_processes() {
  local api='uv run uvicorn app.main:app --reload'
  local worker='uv run python worker.py'
  local web='npm run dev'

  if command -v tmux >/dev/null 2>&1; then
    # Three panes in one window, which is what demo.ps1 gets from Windows
    # Terminal. Killing the session in `down` takes every process in it.
    tmux kill-session -t buktiesg 2>/dev/null || true
    tmux new-session  -d -s buktiesg -c "$ROOT/backend"  "$api"
    tmux split-window -t buktiesg   -c "$ROOT/backend"  "$worker"
    tmux split-window -t buktiesg   -c "$ROOT/frontend" "$web"
    tmux select-layout -t buktiesg even-vertical >/dev/null
    ok 'three panes in tmux - attach with: tmux attach -t buktiesg'
    return
  fi

  note 'tmux not found - starting in the background, logs under backend/var/log'
  mkdir -p "$LOG_DIR"

  # `nohup ... </dev/null &`, not setsid. setsid is util-linux: Linux has it,
  # macOS does not - so a `command -v setsid` fallback would never once take the
  # setsid branch on the platform this file exists for. Redirecting all three
  # streams is what actually detaches: leave stdout on the caller's pipe and a
  # `demo.sh up | tail` never reaches EOF, because the children still hold the
  # write end open long after the script has finished.
  ( cd "$ROOT/backend"  && nohup $api    >"$LOG_DIR/api.log"    2>&1 </dev/null & )
  ( cd "$ROOT/backend"  && nohup $worker >"$LOG_DIR/worker.log" 2>&1 </dev/null & )
  ( cd "$ROOT/frontend" && nohup $web    >"$LOG_DIR/web.log"    2>&1 </dev/null & )
  ok "api.log worker.log web.log in $LOG_DIR"
}

cmd_up() {
  step 'Checking configuration'
  local password; password="$(dotenv POSTGRES_PASSWORD)"
  [ -n "$password" ] || die "POSTGRES_PASSWORD is not set in $ROOT/.env - copy .env.example and set it."
  ok '.env has POSTGRES_PASSWORD'

  # The demo is meant to show real extraction. Without the key the worker falls
  # back to NullExtractor: jobs still complete and every value stays null, so
  # nothing errors and the demo is quietly less than intended. Worth a warning
  # precisely because it does not announce itself.
  if [ -z "$(dotenv DEEPSEEK_API_KEY)" ]; then
    note 'DEEPSEEK_API_KEY is not set - the worker will use NullExtractor and extract no values.'
  else
    ok 'DEEPSEEK_API_KEY is set - real extraction.'
    note 'Upload only from sample/ while the key is set (AGENTS.md 3.1).'
  fi

  step 'Starting PostgreSQL'
  (cd "$ROOT" && docker compose up -d >/dev/null) || die 'docker compose up failed - is Docker running?'
  wait_until 60 'postgres healthcheck' postgres_healthy || die 'postgres never became healthy'
  ok 'buktiesg-postgres healthy'

  step 'Applying migrations'
  (cd "$ROOT/backend" && uv run alembic upgrade head) || die 'alembic upgrade head failed'
  ok 'schema at head'

  step 'Launching API, worker and web'
  start_processes

  step 'Waiting for both ports to answer'
  wait_until 90  "$API_BASE/health" http_ok "$API_BASE/health" || die "the API never answered at $API_BASE"
  ok "API   $API_BASE/health"
  wait_until 150 "$WEB_BASE"        http_ok "$WEB_BASE" || die "the web app never answered at $WEB_BASE"
  ok "Web   $WEB_BASE"

  printf '\n%sReady. Open %s%s\n' "$C_OK" "$WEB_BASE" "$C_OFF"
  printf '%sRunbook: DEMO.md%s\n' "$C_OK" "$C_OFF"
}

cmd_reset() {
  http_ok "$API_BASE/health" || die "the API is not answering at $API_BASE - run ./demo.sh up first."

  # Never generated or stored by this script. It reads what you set and
  # otherwise asks; the password is not echoed and not written anywhere.
  local email="${DEMO_EMAIL:-$(dotenv DEMO_EMAIL)}"
  [ -n "$email" ] || read -r -p 'Demo account email: ' email
  local password="${DEMO_PASSWORD:-$(dotenv DEMO_PASSWORD)}"
  if [ -z "$password" ]; then
    read -r -s -p "Password for $email: " password
    printf '\n'
  fi

  local jar; jar="$(mktemp)"
  trap 'rm -f "$jar"' EXIT

  step 'Signing in'
  local body; body="$(py 'import json,sys; print(json.dumps({"email": sys.argv[1], "password": sys.argv[2]}))' "$email" "$password")"
  curl -fsS --max-time 15 -c "$jar" -H 'Content-Type: application/json' \
    -d "$body" -o /dev/null "$API_BASE/api/v1/auth/login" \
    || die "login failed for $email"
  ok "signed in as $email"

  # Deleted through the API rather than by truncating tables, because nothing in
  # the database owns the uploaded bytes and the row cascade alone would leave
  # them on disk forever. DELETE /cases/{id} takes the stored directory too -
  # backend/tests/test_case_delete.py pins that.
  step 'Deleting cases'
  local ids; ids="$(curl -fsS --max-time 15 -b "$jar" "$API_BASE/api/v1/cases" \
    | py 'import json,sys; print("\n".join(c["id"] for c in json.load(sys.stdin)))')"
  if [ -z "$ids" ]; then
    ok 'nothing to delete'
  else
    local id
    for id in $ids; do
      curl -fsS --max-time 30 -b "$jar" -X DELETE -o /dev/null "$API_BASE/api/v1/cases/$id"
      ok "deleted $id"
    done
  fi

  step 'Verifying'
  local remaining; remaining="$(curl -fsS --max-time 15 -b "$jar" "$API_BASE/api/v1/cases" \
    | py 'import json,sys; print(len(json.load(sys.stdin)))')"
  [ "$remaining" = 0 ] || die "reset incomplete: $remaining case(s) still listed."
  ok 'API lists 0 cases'

  # Checked independently of the API's own answer, the same way a live database
  # is worth a look with psql rather than trusting the endpoint that wrote to it.
  local storage="$ROOT/backend/var/storage"
  if [ -d "$storage" ]; then
    local leftover; leftover="$(find "$storage" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
    if [ "$leftover" != 0 ]; then
      note "$leftover director(ies) left under backend/var/storage, owned by no case:"
      find "$storage" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | while read -r d; do note "  $d"; done
    else
      ok 'backend/var/storage is empty'
    fi
  else
    ok 'backend/var/storage does not exist yet'
  fi

  printf '\n%sClean. Account and organization kept.%s\n' "$C_OK" "$C_OFF"
}

stop_port() {
  local port="$1" pids pid pgid
  pids="$(lsof -ti "tcp:$port" -sTCP:LISTEN 2>/dev/null || true)"
  [ -n "$pids" ] || return 1
  for pid in $pids; do
    # Kill the process group, not the pid. `uvicorn --reload` is a supervisor
    # plus a child, and the child is the one listening - kill it alone and the
    # supervisor spawns a replacement, so the port is free for about a second
    # and then held again. Unix gives this for free; the Windows script has to
    # walk the parent chain by hand to get the same effect.
    pgid="$(ps -o pgid= -p "$pid" 2>/dev/null | tr -d ' ' || true)"
    [ -n "$pgid" ] && kill -TERM "-$pgid" 2>/dev/null || true
    kill -TERM "$pid" 2>/dev/null || true
  done
  return 0
}

port_free() { ! lsof -ti "tcp:$1" -sTCP:LISTEN >/dev/null 2>&1; }

cmd_down() {
  step "Stopping this repository's processes"
  if command -v tmux >/dev/null 2>&1 && tmux has-session -t buktiesg 2>/dev/null; then
    tmux kill-session -t buktiesg
    ok 'tmux session buktiesg killed'
  fi

  # The worker listens on nothing, so freeing ports never reaches it. Identify it
  # the only way that is actually specific: a process whose command line names
  # this repository. Matching on the path is what keeps this safe - other node
  # and python processes point somewhere else. This script excludes itself.
  local pids pid count=0
  pids="$(pgrep -f "$ROOT" 2>/dev/null | grep -v "^$$\$" || true)"
  for pid in $pids; do
    case "$(ps -o command= -p "$pid" 2>/dev/null)" in
      *demo.sh*) continue ;;
    esac
    kill -TERM "$pid" 2>/dev/null && count=$((count + 1)) || true
  done
  ok "$count process(es) named this repository"

  step 'Freeing ports'
  local port
  for port in 8000 3000; do
    if stop_port "$port"; then ok "stopped whatever held $port"; else ok "$port already free"; fi
  done

  # Checked after a wait, not immediately: a killed group takes a moment to
  # release its socket, and an instant check reports a failure that is not one.
  for port in 8000 3000; do
    if wait_until 15 "port $port to be released" port_free "$port"; then
      ok "$port released"
    else
      note "$port is still held - close its window manually"
    fi
  done

  step 'Stopping PostgreSQL'
  (cd "$ROOT" && docker compose stop >/dev/null)
  ok 'buktiesg-postgres stopped (the named volume keeps the data)'
}

case "${1:-up}" in
  up)    cmd_up ;;
  reset) cmd_reset ;;
  down)  cmd_down ;;
  *)     die "unknown command '${1}'. Use: up | reset | down" ;;
esac
