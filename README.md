# BuktiESG

An ESG customer-questionnaire **Evidence-to-Action** workspace for Malaysian SMEs.

*"Bukti"* means **proof** in Malay. The product thesis is provenance over prose: the system must never help a company claim what it cannot prove.

---

## Data Restriction

**Synthetic data only.** This is a **T1** project. Real employee, customer, payroll, identity-card, health or safety-incident data must never be uploaded, committed or processed — doing so is a stop-and-escalate trigger, not a style preference. No real ESG data, no real customer questionnaires, no production credentials.

**The API has no authentication.** It is a local, single-tenant slice and must not be exposed beyond localhost.

---

## Running It Locally

Two processes. The frontend talks to the backend over HTTP and holds no data of its own.

```bash
# The database — PostgreSQL 16, from the repository root
docker compose up -d

# Terminal 1 — API on :8000
cd backend
uv sync
cp .env.example .env                    # DATABASE_URL for the container above
uv run alembic upgrade head
uv run uvicorn app.main:app --reload

# Terminal 2 — workspace UI on :3000
cd frontend
npm install
npm run dev
```

PostgreSQL is the database this project runs on. `app/config.py` still falls back to a local SQLite file when `DATABASE_URL` is unset, so the app can boot without a live database — that fallback does not enforce foreign keys, has no row-level locking, and cannot be built by the migrations. [`backend/README.md`](backend/README.md) says what breaks and why. The test suite is the one place SQLite is used on purpose: it builds its own in-memory database, so `pytest` needs no Docker.

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

`workers/`, `fixtures/` and `deployment/` are authorized by Gate P0 but do not exist yet.

> **Layout note (2026-08-23).** `apps/web` was removed and `frontend/` is now the only frontend; `apps/api` became `backend/`. `SPEC-AMD-009` recorded this as an **open, unresolved** conflict against Main Spec §16, which specifies `apps/web` + `apps/api`. Deleting that file did not close the conflict.

---

## Walkthrough

Uses the files in [`sample/`](sample/README.md), which explains what each one is for and which rule it exercises. About ten minutes, with both processes up, at <http://localhost:3000>.

1. **Set your reviewer label** — `?` avatar, top right. Every review call carries a `reviewer_name` and the API rejects a blank one, so review stays blocked until this is set. It is a label; there is no authentication behind it.
2. **New case** → title, customer, deadline → reporting period `2025-01-01` to `2025-12-31` → drop in `sample/questionnaire/customer-esg-questionnaire-2026.xlsx` → **Create case**. Parsing is synchronous, so the questionnaire is already read when you land on Evidence. The **Columns detected** panel is a read-back of what the parser used, not an editable mapping.
3. **Questionnaire** → **20 questions · 14 required**, every row `Partial / Unreviewed`, Priority `Not scored`. All three are honest: the priority formula is a protected value not implemented server-side, so the UI shows nothing rather than inventing a number.
4. **Evidence** → upload the files from `sample/evidence/`, setting **Upload as** to the matching type. The type decides whether the server parses a file as a questionnaire or indexes it as evidence. Filenames are prefixed `A-` (sound), `B-` (uncertain) and `C-` (wrong) — [`sample/README.md`](sample/README.md) says what is wrong with each one and, importantly, which of it the product can and cannot detect today.
5. **Break it on purpose** — upload `C-06-unreadable-scan-safety-records.pdf`, then `broken-questionnaire-wrong-headers.xlsx`. Both land on *Needs manual review* naming the actual reason, and the broken questionnaire creates **no** questions rather than silently producing zero.
6. **Review an answer** — open `Q-E-02` (Scope 2 emissions) and work the figure out yourself from `A-01-tnb-electricity-bills-fy2025.pdf` and `reference-malaysia-grid-emission-factor.txt`: 1,847.3 MWh × 0.740 = 1,367.0 tCO2e. **Edit answer** → submit. Readiness moves 0% → **7% (1 of 14)**. Only a human confirmation moves that number.
7. **Find the contradiction the engine cannot** — `Q-E-08` (scheduled waste). `A-03` reports 12.6 tonnes; `C-01` reports 18.4 tonnes for the same site and the same year. The engine still says `Partial`, not `Conflicting`, because it only detects a conflict when two links carry different *values* for the same scope and period, and the keyword matcher never extracts a value at all. That gap is real, and it is the reason this product puts a human in the loop. Reject the draft to record it — review status becomes `Rejected` while evidence status **stays** `Partial`; your verdict on a draft is not a verdict on the evidence.
8. **Raise an action** — owner, next step and deadline are all required. Completing one needs a note; completing one with **Require closure evidence** on needs a link the UI cannot supply, so it cannot be quietly ticked off.
9. **Retire a case** — the `⋯` menu on any Cases row. **Archive** is always available and destroys nothing; the row leaves the list and comes back with **Show archived**, where **Restore** names the exact status it will return to. **Delete** is refused unless the case is `DRAFT` (nothing to lose yet) or `ARCHIVED` (already deliberately retired) — anything in between says so and points at archiving. Deleting removes every question, answer, review decision, document and stored file under the case.
10. **Export** → **Generate marked-up draft** → **Download package**. Four files, generated in the browser — there is no export endpoint. The summary carries a `DRAFT — NOT SUBMISSION-READY` header listing the gaps.

---

## Governance

| Field | Value |
|---|---|
| Gate P0 | **ACCEPTED — 2026-08-22** (mixed human/agent, not a full human sign-off) |
| Feature implementation | **AUTHORIZED — Phase 1** |
| Production state | Not released |
| Enforcement | **Advisory-only** — no CI, no branch protection, no `CODEOWNERS` |
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
