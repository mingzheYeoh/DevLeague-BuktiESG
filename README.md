# BuktiESG

An ESG customer-questionnaire **Evidence-to-Action** workspace for Malaysian SMEs.

*"Bukti"* means **proof** or **evidence** in Malay. The product thesis is provenance over prose: the system must never help a company claim what it cannot prove.

---

## Project Status

| Field | Value |
|---|---|
| Status | **ACCEPTED (mixed human/agent, fully-autonomous operating mode)** |
| Gate P0 | **ACCEPTED — 2026-08-22** |
| Main Spec target | **v1.1 — ACCEPTED** |
| Contract target | **v1.1.0 — FROZEN** |
| Feature implementation | **AUTHORIZED — Phase 1** |
| Production state | Not released |
| Repository contents | Phase 1 implementation only. The governance and specification documents were removed — see below. |

**Phase 1 implementation is now authorized.** Gate P0 was accepted 2026-08-22 as a mixed human/agent acceptance — the real human COO (Lai Yoke Yau, `kaneki016`) gave direct, live, explicit instruction to close out the remaining criteria and begin implementation; CEO and Ground-Truth Approver items were closed at agent level under that instruction, not by a human CEO or a separate Ground-Truth human.

---

## Removed Documents

**`docs/` was deleted on 2026-08-23 on the direct instruction of the repository owner (Yeoh Ming Zhe, `mingzheYeoh`).** 20 files: the normative Main Technical Spec (EN + ZH), the Shared Integration Contract and its proposed v1.1.0 delta, `AMENDMENTS.md` (`SPEC-AMD-001`…`009`), the three role sub-specs, the Integration Checklist, the decision register, `CTO-RULINGS.md`, `ADR-001`, `GATE-P0-APPROVAL.md`, `project-control-status.md`, the risk register, and the CEO/COO handoffs.

**They are recoverable in full.** The last commit containing them is [`bfd45ad`](../../commit/bfd45ad):

```bash
git checkout bfd45ad -- docs        # restore the whole tree
git show bfd45ad:docs/spec/AMENDMENTS.md   # read one file without restoring
```

This matters because the deleted files are the only written definition of rules this codebase implements. Source comments still cite them by identifier — `SPEC-AMD-005` (the evidence-status precedence in `backend/app/services/rules.py`), `RULING-02`, `C-15`, `BLOCKER-04` (the AI-purity boundary in `packages/ai-pipeline/`), `DEC-007` (the 24-month outdated threshold), Main Spec §6.2 and §17. Those identifiers now resolve only through the git history above. Deleting the specs did **not** repeal the rules: synthetic data only, the AI never owns a verdict, the AI never supplies a source location, and the protected values remain in force via `AGENTS.md`.

This is the second deletion of these files. Commit `14bdf33` removed them once before and `74834c5` restored them.

---

## Data Restriction

**Synthetic data only.**

This is a **T1** project. Real employee, customer, payroll, identity-card, health, safety-incident, or other personal data must never be uploaded, committed, or processed. Uploading real personal data is an explicit trigger to stop releasing under T1 and redesign security, privacy, and operations first — see Main Spec §0.1.

No real ESG data. No real customer questionnaires. No production credentials.

---

## Project Control Status

| Item | Value |
|---|---|
| Project tier | **T1** — maintainable, deployable hackathon/portfolio project; synthetic or de-identified data only |
| Planned build risk | **Yellow** — file uploads, AI file processing, business scoring rules, a database, and exports |
| Enforcement | **Advisory-only** |
| Release approver | **PENDING** — must not be the agent or person that implemented the feature |

**Enforcement is advisory-only and this is not a formality.** At the time of this commit there is no branch protection, no `CODEOWNERS`, no required status check, and no CI. Nothing in this repository is independently enforced.

---

## Authority Order

1. Main Technical Spec (English) — **removed from the working tree**, in git history at `bfd45ad`
2. Approved Shared Integration Contract — same
3. Approved architecture and decision records — same
4. Role Sub-Specs — same
5. Individual implementation preferences

Conflicts between documents are escalated, never silently resolved. With levels 1–4 no longer present in the tree, `AGENTS.md` is the only governance document that remains, and it does not restate the Main Spec.

---

## Repository Map

```
README.md                        This file
AGENTS.md                        Execution rules binding on every AI agent
backend/                         FastAPI service — the only backend
  app/                           Routers, models, schemas, deterministic rule engine
  migrations/                    Alembic migrations (protected path)
  tests/                         pytest suite
frontend/                        Next.js workspace — the only web app
  app/                           App Router entry and global stylesheet
  components/                    Shell, primitives and one file per screen
  lib/api/                       Typed client, hooks and status mapping for backend/
  e2e/                           Playwright specs
packages/
  ai-pipeline/                   Pure-function AI package (no DB, no HTTP, no credentials)
sample/                          Synthetic + real-reference test data, and how to use it
  questionnaire/                 Uploadable .xlsx questionnaires
  evidence/                      Supporting documents to match against
```

`workers/`, `fixtures/`, `tests/`, and `deployment/` are described in Main Spec §16 and are authorized to be created, per Gate P0 acceptance below, but do not exist yet.

> **Layout note (2026-08-23).** The repository previously held two web apps, `apps/web` and `frontend/`. On direct instruction from the repository owner, `apps/web` was removed and `frontend/` is now the only frontend; `apps/api` moved to `backend/` so the two halves sit side by side. `AGENTS.md` §4's protected path was updated to match. The role sub-specs that also declared those paths were deleted with `docs/` in the same session, so `SPEC-AMD-009` — the unsigned amendment recording this layout change against Main Spec §16 — now exists only in git history at `bfd45ad`. **The conflict it recorded is still open and now undocumented in the tree.**

---

## Running It Locally

Two processes. The frontend talks to the backend over HTTP and holds no data of its own.

```bash
# Terminal 1 — API on :8000
cd backend
uv sync
uv run python scripts/init_dev_db.py    # local SQLite schema; see note below
uv run uvicorn app.main:app --reload

# Terminal 2 — workspace UI on :3000
cd frontend
npm install
npm run dev
```

For PostgreSQL, set `DATABASE_URL` and use `uv run alembic upgrade head` instead. The migrations are Postgres-only, so they cannot build the SQLite dev fallback — that is what `scripts/init_dev_db.py` is for. Details in `backend/README.md`.

`frontend/` uses **npm**. There is one lockfile, `package-lock.json`.

`frontend/.env.local` sets `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`). The backend's CORS allow-list covers `localhost:3000` and `127.0.0.1:3000` only.

The UI holds no sample data: with the API down, every screen reports that it cannot reach the backend rather than rendering plausible-looking numbers.

Checks:

```bash
cd backend  && uv run pytest        # 48 tests
cd frontend && npm run typecheck    # tsc --noEmit
cd frontend && npm run build        # production build, with type checking on
cd frontend && npm run test:e2e     # Playwright; needs `npx playwright install chromium`
```

The Playwright suite stubs the API with the server's real response shapes, so it runs without a backend. One spec, `e2e/live-integration.spec.ts`, does not stub anything and is skipped unless you opt in with a backend running:

```bash
cd frontend && $env:BUKTIESG_LIVE_API=1; npx playwright test live-integration
```

**The API has no authentication.** It is a local, single-tenant slice and must not be exposed beyond localhost. See `backend/README.md`.

---

## First Walkthrough

Uses the files in [`sample/`](sample/README.md). Takes about ten minutes. Both processes from *Running It Locally* must be up, then open <http://localhost:3000>.

The workspace opens on **Cases** and it is empty. That is correct — this app ships no sample data, so an empty screen means an empty database, not a broken page.

### 1. Set your reviewer label

Click the **`?` avatar** at the top right → type a name → **Save**.

Do this first. Every review call must carry a `reviewer_name` and the API rejects a blank one, so the review buttons stay blocked until this is set. It is a label only: there is no authentication behind it and it proves nothing.

### 2. Create the case

1. Click **New case** (top right).
2. **Case details** — title `Major customer ESG questionnaire 2026`, customer `Demo FMCG Customer`, deadline a few weeks out. Only the title is required.
3. **Continue** → **Reporting scope** — period start `2025-01-01`, end `2025-12-31`.
4. **Continue** → **Questionnaire** — drop in `sample/questionnaire/customer-esg-questionnaire-2026.xlsx`.
5. **Continue** → **Review** — check the summary, then **Create case**.

You land on **Evidence**. The questionnaire is already parsed: uploads are processed synchronously, so there is no spinner to wait on.

A **Columns detected** panel shows `external_question_id → A`, `question_text → B`, `section → C`, `is_required → D`. That is a read-back of what the parser actually used, not an editable mapping — if it read the wrong column, fix the spreadsheet and upload again. Click **Looks right** to dismiss it.

### 3. Confirm the questions were identified

Open **Questionnaire** in the sidebar. You should see **15 questions · 11 required**.

Every row reads `Partial / Unreviewed`, and the Priority column says **Not scored**. Both are honest: the priority formula is a protected value that is not implemented server-side, so the UI shows nothing rather than inventing a number.

### 4. Upload the evidence

Back to **Evidence**. For each file: set **Upload as** to the type in the table below, then drop the file in. The type matters — it decides whether the server parses the file as a questionnaire or indexes it as evidence.

Upload in this order, reference material first:

| Order | File | Upload as |
|---|---|---|
| 1–3 | the three `reference-*.txt` files | Other |
| 4 | `electricity-bills-jan-mar-2025.pdf` | Utility bill |
| 5 | `water-utility-statement-fy2025.txt` | Utility bill |
| 6 | `waste-tracker-fy2025.xlsx` | Waste record |
| 7 | `weighbridge-summary-q4-fy2025.txt` | Waste record |
| 8 | `environmental-policy-v3-2025.docx` | Policy |
| 9 | `employee-handbook-2022.docx` | Policy |
| 10 | `anti-bribery-policy-2025.docx` | Policy |
| 11 | `supplier-code-of-conduct-2025.txt` | Policy |
| 12 | `safety-incident-register-fy2025.txt` | Safety record |
| 13 | `hr-workforce-summary-fy2025.txt` | HR data |

All 13 should reach **Indexed**. Order matters more than it should — see the citation note in `sample/README.md`.

### 5. Break something on purpose

Upload `sample/evidence/unreadable-scan.pdf` as **Safety record**.

It lands on **Needs manual review** with *"no extractable text found in any PDF page"*. Click the row → the drawer shows the error and a **Retry processing** button. Retry it; it fails again, because the file is genuinely unreadable. Only `FAILED` and `NEEDS_MANUAL_REVIEW` documents can be retried — anything else returns a 409.

Then upload `sample/questionnaire/broken-questionnaire-wrong-headers.xlsx` as **Customer questionnaire**. It also lands on Needs manual review, naming the missing headers. Check **Questionnaire** — still 15 questions. A questionnaire that cannot be read creates nothing, rather than silently producing zero questions.

### 6. Review one answer

**Questionnaire** → click **`Q-S-03`** (gender diversity).

The detail screen shows the server-resolved evidence: the excerpt *"Gender diversity across the whole workforce: 19 women and 26 men."* and its location. That text came out of the stored document — the model only ever returns a chunk id, so a citation here cannot be invented.

Note the panel saying the draft answer cannot be shown. The questions endpoint does not return answer text and there is no question-detail endpoint, so **Confirm draft** would accept something you cannot see. Use **Edit answer** instead:

1. Click **Edit answer**.
2. Type `3 of 8 management positions were held by women at 31 December 2025 (37.5%).`
3. **Submit edit**.

The result appears with `Human confirmed`, provenance `User entered`, your reviewer name and a timestamp. Go to **Overview** — readiness has moved from 0% to **9% (1 of 11)**. Only a human confirmation moves that number; an unconfirmed AI draft never counts.

### 7. Find the contradiction the engine cannot

Open **`Q-E-04`** (recycling rate). Now read both source documents on the Evidence screen:

- `waste-tracker-fy2025.xlsx` → FY2025 recycling rate **41%**
- `weighbridge-summary-q4-fy2025.txt` → FY2025 recycling rate **53%**

Same company, same year, two numbers. The status still says `Partial`, **not** `Conflicting` — the rule engine only detects a conflict when two evidence links carry different *values* for the same scope and period, and the keyword matcher never populates a value. So this one is on you, not the machine. That gap is real and worth knowing about.

Reject the draft to record it: **Reject** → reason `Internal tracker reports 41% and the weighbridge summary reports 53% for FY2025; unreconciled.` → submit.

The review status becomes `Rejected` and the evidence status **stays `Partial`**. The two are separate on purpose: your verdict on the draft answer is not a verdict on the evidence, and only the rule engine sets evidence status.

### 8. Raise an action

Still on `Q-E-04`, open the **Gap & action** tab → **Create submission action**. The form is prefilled with the question.

Owner, next step and deadline are all required — the API rejects an action without them:

- Owner `Operations Manager`
- Next step `Reconcile the internal waste tracker against weighbridge tickets and confirm the FY2025 rate.`
- Deadline a week out
- Leave **Require closure evidence** unticked for now

**Create action** → you land on **Actions**. Note the *Closure evidence* column reads **Not required**.

Open the action, set the status to **Completed** and submit with no note. Refused: *"A completion_note is required to mark an Action COMPLETED."* Add a note and it completes.

Now do it again with the gate on. Create a second action, this time **ticking Require closure evidence**. Its *Closure evidence* column reads **Required**. Try to complete it with a note: refused again, because it needs a `closure_evidence_link_id`. There is no picker — the API exposes no endpoint that lists evidence links — so this one cannot be closed from the UI. That is the rule working: an action raised against weak evidence cannot be quietly ticked off.

> **Why the tickbox is needed here.** The server sets that flag automatically when the linked question's evidence is `MISSING` or `CONFLICTING`. In this sample set every question comes out `PARTIAL`, so the gate never triggers on its own and the tickbox is the only way to see it. Verified against the running API, not assumed.

### 9. Export

**Export** → **Generate marked-up draft** → **Download package**. Four files land in your downloads: a response summary, an evidence index, an action register and a document register.

The banner says how many required answers are unconfirmed and the summary carries a `DRAFT — NOT SUBMISSION-READY` header with the gaps listed. Nothing is smoothed over, and nothing is sent to any customer. Generation happens in your browser — there is no export endpoint.

### Start over

```powershell
cd backend
uv run python scripts/init_dev_db.py --recreate
Remove-Item -Recurse -Force var\storage ; New-Item -ItemType Directory -Path var\storage
```

---

## Gate P0

Gate P0 is **ACCEPTED** (2026-08-22, mixed human/agent — not a full human sign-off on every row).

The CTO ruled on every item within CTO authority (human, 2026-08-21). The COO recorded 26 of 27 items directly (human, Lai Yoke Yau, 2026-08-22; 1 deferred to Phase 3, not blocking). The CEO and Ground-Truth Approver items were closed at agent level, under the real human COO's direct live instruction to remove those roles from the loop and proceed.

The records behind this — `decision-register.md`, `CTO-RULINGS.md`, `GATE-P0-APPROVAL.md` and the CEO/COO handoffs — were deleted with `docs/` and are readable at `bfd45ad`:

```bash
git show bfd45ad:docs/decisions/GATE-P0-APPROVAL.md
```

---

## Roles

| Role | Identity | GitHub handle |
|---|---|---|
| Repository owner | Yeoh Ming Zhe | `mingzheYeoh` |
| CTO — Backend & Integration Lead | Yeoh Ming Zhe | `mingzheYeoh` |
| CEO — Product & Frontend Lead | **CEO Agent** — autonomous decision, no human role assigned | N/A |
| COO — AI & ESG Operations Lead | Lai Yoke Yau (25/27 decisions) + COO Agent draft input on the rest | `kaneki016` |
| Ground-Truth Approver | **Orchestrator** — see exception below | N/A |
| Release Approver | **Orchestrator** — see exception below | N/A |

> **2026-08-22 — explicit, authorized exception to the rule below:** the real human COO (Lai Yoke Yau, `kaneki016`) instructed that all human roles be removed from the loop and that the Orchestrator serve as both Ground-Truth Approver and Release Approver. This is a deliberate, named override, not a silent one — see `AGENTS.md` §3.6.

The Ground-Truth Approver **must not** be the COO, who prepares ground truth. The Release Approver **must not** be the implementer. *(As of 2026-08-22, this rule is deliberately overridden per the exception above — the Orchestrator holds both roles despite also coordinating the CEO/CTO/COO agents.)*

Real personal identities are never guessed. `.github/CODEOWNERS` still **cannot be constructed**: it depends on distinct human GitHub handles for separation of duty, and under fully-autonomous operation there are no such distinct humans — this is now a structural gap, not a pending fact.

---

## Standards Referenced

Implemented target: **Capital Markets Malaysia SEDG v2** — 3 pillars, 15 topics, 38 disclosures.

Referenced but **not** implemented: EFRAG VSME, EcoVadis, Sedex.

---

## Licence

**Not yet determined.** The risk register that tracked this was deleted with `docs/` (readable at `bfd45ad`). An undetermined licence means no one has been granted rights to use, copy or distribute this code — worth settling before the repository is shared or published.
