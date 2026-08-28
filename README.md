# BuktiESG

An ESG customer-questionnaire **Evidence-to-Action** workspace for Malaysian SMEs.

*"Bukti"* means **proof** in Malay. The product thesis is provenance over prose: the system must never help a company claim what it cannot prove.

---

## Data Restriction

**Permitted, with one condition you have to hold yourself.** Until 2026-08-25
this was a synthetic-data-only project. On 2026-08-25 the repository owner
ruled that real customer personal data may be processed subject to four
conditions in [`AGENTS.md`](AGENTS.md) §3.1. **All four now hold** —
authentication on every endpoint and organization-scoped access, a passing
cross-tenant matrix, and the cross-border decision recorded 2026-08-27.

**That cross-border decision was made twice.** It began as a flat prohibition
on sending document text outside Malaysia, and was reversed the same day for
the demo. DeepSeek is permitted — **so long as no real customer document is
uploaded while `DEEPSEEK_API_KEY` is set.** The risk was never whether this is
a demo; it is whether the document is real, and a demo's next move is usually a
prospect's actual questionnaire. No code can check that, so it is yours to
hold: unset the key before the first real document, and rotate it.

With a key set, chunk text goes to `api.deepseek.com` and the worker logs a
warning saying so. With no key, nothing leaves the machine.

Read §3.1 before uploading anything real; it is the authority, not this
summary.

---

## Running It Locally

Three processes, one of them optional. The frontend talks to the backend over HTTP and holds no data of its own.

```bash
# Configuration — one file at the repository root, read by Compose and the API
cp .env.example .env      # set POSTGRES_PASSWORD; any value, it is local and disposable

# The database — PostgreSQL 16
docker compose up -d

# Terminal 1 — API on :8000
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload

# Terminal 2 — workspace UI on :3000
cd frontend
npm install
npm run dev

# Terminal 3 — the extraction worker. Optional, and only for values.
cd backend
uv run python worker.py
```

The worker is the one process you can leave out and still have a working
application: uploads succeed and questions still get their evidence without it.
What it drains is the `EXTRACT_VALUES` queue, which cannot run inline — two or
three chunks take 12–22 seconds — so without it `evidence_links.value` stays
null and the `CONFLICTING` evidence status is unreachable. The other six
statuses are unaffected. [`backend/README.md`](backend/README.md) has the
detail.

For demonstrating rather than developing, [`demo.ps1`](demo.ps1) starts all of
it in order, waits for each piece to actually answer, and gives you a `reset`
between runs. [`DEMO.md`](DEMO.md) is the walkthrough — including what this
build cannot do, which is worth reading before showing it to anyone.

One `.env`, at the repository root. Compose reads the file beside `docker-compose.yml`, and `app/config.py` anchors to the same directory rather than to whatever directory it was launched from — so the API reads its configuration whether you start it from `backend/` or not. `DATABASE_URL` is derived from `POSTGRES_PASSWORD`, so the password is written once; set `DATABASE_URL` explicitly only to point somewhere other than the Compose database.

PostgreSQL is the database this project runs on. `app/config.py` falls back to a local SQLite file when neither is set, so the app can boot without a live database — that fallback does not enforce foreign keys, has no row-level locking, and cannot be built by the migrations. [`backend/README.md`](backend/README.md) says what breaks and why. The test suite is the one place SQLite is used on purpose: it builds its own in-memory database, so `pytest` needs no Docker.

`frontend/.env.local` sets `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`). The backend's CORS allow-list covers `localhost:3000` and `127.0.0.1:3000` only. `frontend/` uses **npm**; there is one lockfile.

The UI ships no sample data. With the API down, every screen reports that it cannot reach the backend rather than rendering plausible-looking numbers.

### Checks

```bash
cd backend  && uv run pytest        # 130 tests
cd frontend && npm run typecheck    # tsc --noEmit
cd frontend && npm run build        # production build, type checking on
cd frontend && npm run test:e2e     # Playwright; needs `npx playwright install chromium`
```

The Playwright suite stubs the API with the server's real response shapes, so it runs without a backend. `e2e/live-integration.spec.ts` stubs nothing and is skipped unless you opt in:

```powershell
cd frontend; $env:BUKTIESG_LIVE_API=1; npx playwright test live-integration
```

### Start over

```powershell
docker compose down -v ; docker compose up -d      # drops the database volume
cd backend ; uv run alembic upgrade head
Remove-Item -Recurse -Force var\storage ; New-Item -ItemType Directory -Path var\storage
```

Both halves matter. `var/storage` holds the uploaded blobs and the database holds
the rows that name them; wiping one without the other leaves documents citing
files that are not there, or files nothing references.

---

## Repository Map

```
AGENTS.md                        Execution rules binding on every AI agent
.github/workflows/ci.yml         Tests on every push — advisory, not a gate
docker-compose.yml               PostgreSQL 16 — the database the app runs on
backend/                         FastAPI service — the only backend
  app/                           Routers, models, schemas, deterministic rule engine
  migrations/                    Alembic migrations (protected path)
  tests/                         pytest suite
frontend/                        Next.js workspace — the only web app
  app/                           App Router entry and global stylesheet
  components/                    Shell, primitives and one file per screen
  lib/api/                       Typed client, hooks and status mapping
  e2e/                           Playwright specs
packages/ai-pipeline/            Pure-function AI package (no DB, no HTTP, no credentials)
sample/                          Synthetic test data — see sample/README.md
```

`backend/worker.py` drains the extraction queue — see [`backend/README.md`](backend/README.md). `workers/`, `fixtures/` and `deployment/` are authorized by Gate P0 but do not exist yet.

> **Layout note (2026-08-23).** `apps/web` was removed and `frontend/` is now the only frontend; `apps/api` became `backend/`. `SPEC-AMD-009` recorded this as an **open, unresolved** conflict against Main Spec §16, which specifies `apps/web` + `apps/api`. Deleting that file did not close the conflict.

---

## Walkthrough

Uses the files in [`sample/`](sample/README.md), which explains what each one is for and which rule it exercises. About ten minutes, with both processes up, at <http://localhost:3000>.

1. **Sign in** — you land on a sign-in screen; create an account if you have none. Registration creates your organization and makes you its ADMIN. Every review verdict and evidence acceptance is recorded against the signed-in account's email, taken from your session — there is no reviewer field to fill in.
2. **New case** → title, customer, deadline → reporting period `2025-01-01` to `2025-12-31` → drop in `sample/questionnaire/customer-esg-questionnaire-2026.xlsx` → **Create case**. Parsing is synchronous, so the questionnaire is already read when you land on Evidence. The **Columns detected** panel is a read-back of what the parser used, not an editable mapping.
3. **Questionnaire** → **20 questions · 14 required**, every row `Partial / Unreviewed`, Priority `Not scored`. All three are honest: the priority formula is a protected value not implemented server-side, so the UI shows nothing rather than inventing a number.
4. **Evidence** → upload the files from `sample/evidence/`, setting **Upload as** to the matching type. The type decides whether the server parses a file as a questionnaire or indexes it as evidence. Filenames are prefixed `A-` (sound), `B-` (uncertain) and `C-` (wrong) — [`sample/README.md`](sample/README.md) says what is wrong with each one and, importantly, which of it the product can and cannot detect today.
5. **Date the stale one** — re-upload `C-02-energy-and-emissions-fy2022.txt` with **Evidence dated** set to `2022-12-31`. Its question moves to **Outdated**: the question names no period, so the engine measures against the 24-month threshold. Leave the date blank and it stays *Partial* — the engine reports that it cannot assess staleness rather than assuming the file is current.
6. **Break it on purpose** — upload `C-06-unreadable-scan-safety-records.pdf`, then `broken-questionnaire-wrong-headers.xlsx`. Both land on *Needs manual review* naming the actual reason, and the broken questionnaire creates **no** questions rather than silently producing zero. On a case where the scan is the *only* evidence, `Q-S-06` reports *Needs manual review* and names the file, while the other 19 report *Missing* — the difference between evidence you have not supplied and evidence the parser could not read. It matches on `safety`, the one word that question and that filename share; C-15 uses exact token equality and nothing else. Retrying will not help — the same parser reads the same bytes — so open the document and **Delete document**. `Q-S-06` goes back to reporting what it can actually find. Only a document the parser could not read can be deleted: one that parsed carries citations a reviewer may have accepted, and the server refuses it with 409.
7. **Vouch for the evidence** — on any question's detail screen, **Accept this evidence** records that you read the source and it supports the answer. Evidence status moves to **Verified**; readiness does not move, because readiness counts confirmed *answers* and this is a verdict on the *citation*. Try it on `Q-E-01`, which asks for Scope 1 and cites the waste register: it verifies anyway. The engine checks that a human vouched, never that the human was right.
8. **Review an answer** — open `Q-E-02` (Scope 2 emissions) and work the figure out yourself from `A-01-tnb-electricity-bills-fy2025.pdf` and `reference-malaysia-grid-emission-factor.txt`: 1,847.3 MWh × 0.740 = 1,367.0 tCO2e. **Edit answer** → submit. Readiness moves 0% → **7% (1 of 14)**. Only a human confirmation moves that number.
9. **Find the contradiction the engine cannot** — `Q-E-08` (scheduled waste). `A-03` reports 12.6 tonnes; `C-01` reports 18.4 tonnes for the same site and the same year. The engine still says `Partial`, not `Conflicting`, because it only detects a conflict when two links carry different *values* for the same scope and period, and until 2026-08-25 no link carried a value. Deterministic extraction was measured against all 231 links and does not work; a model reads both documents correctly, and the last obstacle was a rule, not a capability — the engine treated an unstated scope as a *different* scope, so a record that named no site could never contradict one that did. That is a protected Evidence Status rule, so it was escalated and [ruled on](sample/README.md) rather than adjusted. Reject the draft to record it — review status becomes `Rejected` while evidence status **stays** `Partial`; your verdict on a draft is not a verdict on the evidence.
10. **Raise an action** — owner, next step and deadline are all required. Completing one needs a note; completing one with **Require closure evidence** on needs a link the UI cannot supply, so it cannot be quietly ticked off.
11. **Retire a case** — the `⋯` menu on any Cases row. **Archive** is always available and destroys nothing; the row leaves the list and comes back with **Show archived**, where **Restore** names the exact status it will return to. **Delete** is refused unless the case is `DRAFT` (nothing to lose yet) or `ARCHIVED` (already deliberately retired) — anything in between says so and points at archiving. Deleting removes every question, answer, review decision, document and stored file under the case.
12. **Export** → **Generate marked-up draft** → **Download package**. Four files, generated in the browser — there is no export endpoint. The summary carries a `DRAFT — NOT SUBMISSION-READY` header listing the gaps.

---

## Governance

| Field | Value |
|---|---|
| Gate P0 | **ACCEPTED — 2026-08-22** (mixed human/agent, not a full human sign-off) |
| Feature implementation | **AUTHORIZED — Phase 1** |
| Production state | Not released |
| Enforcement | **Advisory-only** — CI runs on every push but gates nothing; no branch protection, no `CODEOWNERS` |
| Release approver | Orchestrator, under the named exception below |

**`docs/` was deleted on 2026-08-23** on the direct instruction of the repository owner (Yeoh Ming Zhe, `mingzheYeoh`). Twenty files: the Main Technical Spec (EN + ZH), the Shared Integration Contract, `AMENDMENTS.md`, the three role sub-specs, the Integration Checklist, the decision register, `CTO-RULINGS.md`, `ADR-001`, `GATE-P0-APPROVAL.md`, the risk register and the CEO/COO handoffs. This was the second deletion; `14bdf33` removed them once before and `74834c5` restored them.

They are recoverable in full at [`bfd45ad`](../../commit/bfd45ad):

```bash
git checkout bfd45ad -- docs                # restore the whole tree
git show bfd45ad:docs/spec/AMENDMENTS.md    # read one file
```

This matters because those files are the only written definition of rules this codebase implements. Source comments still cite them by identifier — `SPEC-AMD-005`, `RULING-02`, `C-15`, `BLOCKER-04`, `DEC-007`, Main Spec §6.2 and §17 — and those identifiers now resolve only through git history. **Deleting the specs did not repeal the rules.** [`AGENTS.md`](AGENTS.md) is the only governance document left in the tree and keeps them in force: synthetic data only, the AI never owns a verdict, the AI never supplies a source location, and the protected values stand.

Authority order on conflict: Main Spec (EN) > approved Shared Contract > approved decisions and amendments > Role Sub-Spec > individual preference. Levels 1–4 are now reachable only via git history, which is not a licence to invent one — conflicts are escalated, never silently resolved.

### Roles

| Role | Identity | Handle |
|---|---|---|
| Repository owner · CTO | Yeoh Ming Zhe | `mingzheYeoh` |
| COO — AI & ESG Operations | Lai Yoke Yau (25/27 decisions) + COO Agent drafts | `kaneki016` |
| CEO — Product & Frontend | CEO Agent — no human assigned | — |
| Ground-Truth & Release Approver | Orchestrator | — |

> **2026-08-22 — explicit, authorized exception.** The rules require that the Ground-Truth Approver not be the COO who prepares ground truth, and that the Release Approver not be the implementer. The real human COO instructed that all human roles be removed from the loop and that the Orchestrator hold both. This is a deliberate, named override, not a silent one — see `AGENTS.md` §3.6.

`.github/CODEOWNERS` **cannot be constructed**: it depends on distinct human GitHub handles for separation of duty, and under fully-autonomous operation there are none. A structural gap, not a pending task.

---

## Standards

Implemented: **Capital Markets Malaysia SEDG v2** — 3 pillars, 15 topics, 38 disclosures.
Referenced but not implemented: EFRAG VSME, EcoVadis, Sedex.

## Licence

**Not yet determined** — no one has been granted rights to use, copy or distribute this code. Worth settling before the repository is shared or published.
