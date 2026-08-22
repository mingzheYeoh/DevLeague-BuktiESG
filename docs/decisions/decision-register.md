# Decision Register

> **2026-08-22 note (CTO agent):** This file, `CTO-RULINGS.md`, and `GATE-P0-APPROVAL.md` were restored (uncommitted, working-tree only) from pre-delete commit `4fa92d4` after an unexplained upstream deletion commit `14bdf33` on `main` today (authored `mingzheYeoh`). Content has been checked for internal consistency against the current `AGENTS.md` and `docs/spec/BuktiESG-Technical-Spec-EN.md` and no contradictions were found. This restoration is a **draft to re-validate, not settled fact**. Deletion confirmed intentional in a live session on 2026-08-22 by COO Lai Yoke Yau (new documentation approach per `mingzheYeoh`) — not yet a written confirmation from `mingzheYeoh` himself. Restoration content below proceeds on that basis.

| Field | Value |
|---|---|
| Status | **ACCEPTED (mixed human/agent, fully-autonomous operating mode)** |
| Gate P0 | **ACCEPTED — 2026-08-22** |
| Main Spec target | **v1.1 — ACCEPTED** |
| Contract target | **v1.1.0 — FROZEN** |
| Feature implementation | **AUTHORIZED — Phase 1** |
| Date | 2026-08-21 (opened) / 2026-08-22 (accepted) |

---

## How approval is tracked

Approvals are collected as **one consolidated packet per human role**, not as a scatter of individual signatures. A packet may approve many line items at once while each line item retains its own `APPROVE` / `AMEND` / `REJECT` status.

| Packet | Holder | Decisions | Recorded | State |
|---|---|---|---|---|
| **CTO approval packet** | Yeoh Ming Zhe (`mingzheYeoh`) | — | — | **COMPLETE** |
| **CEO approval packet** | N/A — fully autonomous operation, no human role-holder; agent-finalized by CEO Agent, 2026-08-22 | 31 (`CEO-D01`…`CEO-D31`) | **31 agent-finalized** (30 substantive; `CEO-D31` finalized as N/A / structural gap) | **AGENT-FINALIZED — not a human Gate P0 sign-off** |
| **COO approval packet** | Lai Yoke Yau (`kaneki016`) | 27 (`COO-D01`…`COO-D27`) | **26 APPROVE** + 1 N/A for Gate P0, deferred to Phase 3 | **FULLY ADDRESSED FOR GATE P0** — see `COO-handoff.md`; `COO-D23` now `APPROVE` (decided directly, 2026-08-22); `COO-D26` marked N/A for Gate P0 and deferred to the Phase 3 ground-truth freeze, per explicit instruction from Lai Yoke Yau, 2026-08-22 — 0 items in this packet block Gate P0 |
| **Ground-Truth approval packet** | Orchestrator (agent) — role assigned 2026-08-22, override authorized by Lai Yoke Yau | 4 at Gate P0 | **0 signed** (role assigned, not yet exercised — no ground truth exists yet) | **ROLE ASSIGNED, PACKET NOT YET EXERCISED** |

Full packets: [`../handoffs/CEO-handoff.md`](../handoffs/CEO-handoff.md) · [`../handoffs/COO-handoff.md`](../handoffs/COO-handoff.md). **The CEO packet is now agent-finalized** (CEO Agent — autonomous decision, no human role assigned, 2026-08-22): all 31 `CEO-Dxx` items addressed — 30 as substantive spec-grounded decisions, `CEO-D31` as N/A / a named structural gap (see `CEO-handoff.md` §C) — but this is explicitly **not** a human Gate P0 signature, and the Ground-Truth Approver / Release Approver identity question inside `CEO-D31` remains out of scope and unresolved. The COO packet now carries 26 recorded `APPROVE` decisions (Lai Yoke Yau, `kaneki016`, 2026-08-22) plus one item (`COO-D26`) marked N/A for Gate P0 and deferred to the Phase 3 ground-truth freeze, per explicit instruction from Lai Yoke Yau, 2026-08-22 — the preparer-input view recorded earlier stands as context only; `COO-D23` was decided directly in the same session and is no longer open. All 27 COO packet items are now addressed; none blocks Gate P0. None has been inferred, simulated, or recorded on a role owner's behalf without that role owner's direct, live authorization — the CEO packet's finalization is an explicit, orchestrator-authorized exception to that default, recorded as an agent decision, not a discovered human answer.

Each outstanding decision is listed in **exactly one** packet, under the role that owns it. Co-approvals are noted on the line but never counted twice.

**The CEO packet is agent-finalized (not a human sign-off); COO is fully addressed for Gate P0 — 26 of 27 recorded `APPROVE`, 1 (`COO-D26`) N/A for Gate P0 and deferred to Phase 3; Ground-Truth remains at zero received on its 4 Gate-P0-relevant items (`SPEC-AMD-005`/`006`/`007`, `C-15`). Gate P0 stays BLOCKED regardless of CEO packet finalization and COO packet completeness.**

| Column | Meaning |
|---|---|
| **CTO** | CTO ruling. Binding within CTO authority only. |
| **FINAL** | All required signatures obtained. |
| **Packet** | Which packet must arrive before this item can become FINAL. |

---

## 1. Rulings

| ID | Item | CTO | FINAL | Packet |
|---|---|---|---|---|
| `RULING-01` | Job and Export concepts; Contract becomes **v1.1.0**; four enums; `ExportType` distinct from `ExportFormat`; allowed-combination table; **no PostgreSQL native ENUM — `text` plus generated `CHECK` constraints** | AMEND | **NO** | CEO, COO |
| `RULING-02` | Evidence Status: `NOT_APPLICABLE` human-only, then exclude unreadable evidence, then frozen precedence, then C-15 or `MISSING` | AMEND | **NO** | CEO, COO, Ground Truth |
| `RULING-03` | `AI_SUGGESTED` removed from `EvidenceStatus`; four-value `DraftProvenance`; one-directional `ai_run_id` invariant; `draft_provenance_counts` | AMEND | **NO** | CEO, COO, Ground Truth |
| `RULING-04` | Persisted integer `question_order`; `question_order ASC, id ASC` | AMEND | **NO** | CEO, COO, Ground Truth |
| `RULING-05` | Named `evidence_preview` and `activity_preview`; new `GET /cases/{id}/activity` with Case-ownership enforcement | APPROVE | **NO** | CEO, COO |
| `RULING-06` | Required `Idempotency-Key`; 202 Accepted; `IDEMPOTENCY_KEY_REUSED`; reuse flag; **database-enforced** concurrency guard; scoped to operation and Case | APPROVE | **NO** | CEO, COO |
| `RULING-07` | Amendments recorded individually; Main Spec becomes **v1.1** | APPROVE | **NO** | CEO, COO, Ground Truth |

Full text: [`CTO-RULINGS.md`](CTO-RULINGS.md).

---

## 2. Open items

| ID | Item | CTO | FINAL | Packet |
|---|---|---|---|---|
| `C-14` | Whether human-set `NOT_APPLICABLE` counts as resolved in the readiness numerator | RECOMMENDATION | **NO** | CEO — required before Phase 4 |
| `C-15` | Deterministic relevance rule for an unreadable document | RULED | **NO** | CEO, COO, Ground Truth |

`C-15` is resolved at CTO level by a rule that depends only on signals surviving extraction failure — processing status, `document_type`, and exact-token keyword matches against `original_filename` or extracted metadata and heading text. Fuzzy matching, embedding similarity, and LLM classification are prohibited, because a similarity threshold is a number that can be quietly tuned until a failing test passes.

It cannot be implemented until the COO supplies the `document_type` value set and the source of `evidence_requirement_json.keywords`.

---

## 3. Blockers

| ID | Item | CTO | FINAL | Packet |
|---|---|---|---|---|
| `BLOCKER-01` | English Main Spec normative; Chinese non-normative | RULED | **NO** | CEO, COO |
| `BLOCKER-02` | Map ownership paths into section 16; no duplicate top-level trees | RULED | **NO** | CEO, COO |
| `BLOCKER-03` | GitHub configuration and `CODEOWNERS` | **PARTIAL** | **NO** | 4 identities — see section 6 |
| `BLOCKER-04` | Pure COO processing core; CTO orchestration layer | RULED | **NO** | COO |
| `BLOCKER-05` | 11 file and processing limit values | RECOMMENDED | **NO** | CEO |
| `BLOCKER-06` | Keyword-first retrieval; pgvector installed but unused | RULED | **NO** | CEO, COO |
| `BLOCKER-07` | Local Docker Compose; no public unauthenticated upload | RECOMMENDED | **NO** | CEO |
| `BLOCKER-08` | Provider, model, fixture fallback, budgets, cost formula, pricing snapshot | RECOMMENDED | **NO** | COO, CEO |

### BLOCKER-03 — partially resolved

| Value | State |
|---|---|
| `GITHUB_REPOSITORY_OWNER` | **`mingzheYeoh`** — resolved |
| `CTO_GITHUB_HANDLE` | **`mingzheYeoh`** — resolved |
| Repository URL | **`https://github.com/mingzheYeoh/DevLeague-BuktiESG`** — resolved |
| Default branch | **`main`** — resolved |
| `CEO_GITHUB_HANDLE` | **N/A** — fully autonomous operation, no human role-holder |
| `COO_GITHUB_HANDLE` | **`kaneki016`** — resolved (Lai Yoke Yau) |
| `GROUND_TRUTH_APPROVER_GITHUB_HANDLE` | **N/A** — role assigned to the Orchestrator (agent, not a human GitHub identity), 2026-08-22 |
| `RELEASE_APPROVER` | **N/A** — role assigned to the Orchestrator (agent, not a human GitHub identity), 2026-08-22 |

`.github/CODEOWNERS` still **cannot be written** — not because these values are pending, but because it structurally requires distinct human GitHub identities for separation of duty, and none exist under fully-autonomous operation (Ground-Truth Approver and Release Approver are now agent roles, not humans, and CEO has no human identity either). `BLOCKER-03` remains **BLOCKED**, now for a structural reason rather than a missing-fact reason.

---

## 4. Architecture and implementation decisions

| ID | Decision | CTO | FINAL | Packet |
|---|---|---|---|---|
| 001 | Python 3.12.x | APPROVED | **YES** (CTO authority) | — |
| 002 | Node 22 LTS, Next.js 15 | APPROVED | **NO** | CEO |
| 003 | PostgreSQL 16 with pgvector image | APPROVED | **NO** | CEO, COO |
| 004 | FastAPI, Pydantic v2, SQLAlchemy 2.0 | APPROVED | **YES** (CTO authority) | — |
| 005 | uv and pnpm; lockfiles are protected files | APPROVED | **YES** (CTO authority) | — |
| 006 | Repository root follows Main Spec section 16 | APPROVED | **NO** | CEO, COO |
| 007 | Sub-Spec path reconciliation | APPROVED | **NO** | CEO, COO |
| 008 | Specifications live in `docs/spec/` | APPROVED | **YES** (CTO authority) | — |
| 009 | Git host, branch protection, `CODEOWNERS` | APPROVED | **NO** | 4 identities |
| 010 | English normative | APPROVED | **NO** | CEO, COO |
| 011 | Alembic; reversible; no destructive migrations | APPROVED | **YES** (CTO authority) | — |
| 012 | `processing_jobs` and `documents.latest_job_id` | APPROVED | **NO** | CEO, COO |
| 013 | Optimistic concurrency: `version` plus ETag and `If-Match` | APPROVED | **NO** | CEO, COO |
| 014 | Single seeded organization row | APPROVED | **YES** (CTO authority) | — |
| 015 | `evidence_links` extraction provenance fields | APPROVED | **NO** | CEO, COO |
| 016 | Storage adapter; content-addressed | APPROVED | **YES** (CTO authority) | — |
| 017 | Database job table with `SKIP LOCKED` and a lease | APPROVED | **YES** (CTO authority) | — |
| 018 | Worker purity boundary | APPROVED | **NO** | COO |
| 019 | File and Case limits | RECOMMENDED | **NO** | CEO |
| 020 | Retention: manual delete | APPROVED | **NO** | CEO |
| 021 | No authentication; private demo | APPROVED | **NO** | CEO |
| 022a | `LLMProvider` adapter boundary | APPROVED | **YES** (CTO authority) | — |
| 022b | Provider, model, and cost configuration | RECOMMENDED | **NO** | COO, CEO |
| 023 | Keyword-first retrieval | APPROVED | **NO** | CEO, COO |
| 024 | Jinja2 to Playwright for PDF; openpyxl for workbooks | APPROVED | **YES** (CTO authority) | — |
| 025 | Idempotency scope | AMENDED by `RULING-06` | **NO** | CEO, COO |
| 026 | structlog JSON logging with a deny-list | APPROVED | **YES** (CTO authority) | — |
| 027 | No error-tracking service in the MVP | APPROVED | **NO** | CEO |
| 028 | GitHub Actions; four jobs; under 5 minutes; plus contract-to-`CHECK` parity | APPROVED | **NO** | depends on 009 |
| 029 | Contract version **v1.1.0** | APPROVED | **NO** | CEO, COO |
| 030 | Evidence Status evaluation model | AMENDED by `RULING-02` | **NO** | CEO, COO, Ground Truth |
| 031 | Bounded transitive invalidation cascade | APPROVED | **YES** (CTO authority) | — |
| 032 | `JobType` enum | APPROVED | **NO** | CEO, COO |
| 033 | `ExportFormat` enum | APPROVED | **NO** | CEO, COO |
| 034 | Questions ordering | AMENDED by `RULING-04` | **NO** | CEO, COO, Ground Truth |
| 035 | Bounded named previews | AMENDED by `RULING-05` | **NO** | CEO, COO |
| 036 | Enum storage: `text` plus generated `CHECK` constraints; CI parity job | APPROVED | **NO** | CEO, COO |
| 037 | `questions.question_order` | APPROVED | **NO** | CEO, COO, Ground Truth |
| 038 | `GET /cases/{case_id}/activity` | APPROVED | **NO** | CEO, COO |
| 039 | Allowed `ExportType` and `ExportFormat` combinations | RECOMMENDED | **NO** | CEO |
| 040 | Cost formula and pricing-snapshot versioning | RECOMMENDED | **NO** | COO, CEO |

**12 decisions are FINAL within CTO authority. Every decision that touches the Main Spec, the Shared Contract, a product outcome, the AI pipeline, or an expected fixture value is NOT FINAL.**

> **2026-08-22 (CTO Agent — autonomous decision, no human role assigned):** Item `039`'s CTO-level column was left at `PROPOSED` rather than a finalized CTO stance, inconsistent with sibling CEO-forwarded items (019, 022b, 040), which read `RECOMMENDED`. The specific combination table was already fully specified in `CTO-RULINGS.md` RULING-01 and carried into decision-register section 6.1 as a CTO recommendation. Finalized `039`'s CTO column to `RECOMMENDED` to match — no change to the combination values themselves, and `FINAL` stays `NO` pending CEO (a product decision, per RULING-01: "which artifact ships in which format is a product decision"). Also corrected the stale "13 decisions are FINAL" count above to `12`, matching the actual `**YES** (CTO authority)` rows in section 4 (a pre-existing arithmetic error, not a decision change).

---

## 5. Specification defects found and escalated

None of these was silently resolved.

| Defect | Sources | Disposition |
|---|---|---|
| `GET /api/v1/jobs/{job_id}` has no resource, schema, enum, lifecycle, or owner — and no client can obtain a `job_id` after refresh | Contract v1.0.0 | `SPEC-AMD-001` |
| `pillar` and `export_type` appear in the contract's own examples with no canonical definition | Contract v1.0.0 | `RULING-01` |
| Pagination declared but never shaped | Contract v1.0.0 | Contract v1.1.0 section 3 |
| Concurrency guard and idempotency scope deferred to "Phase 0" with no value | Contract v1.0.0 | `RULING-06` |
| Main Spec 12.5 and Contract 8 define different AI schema field sets | Main Spec, Contract | `SPEC-AMD-003` |
| Main Spec 6.3 and Contract 7.4 require extraction fields that 10.1 omits | Main Spec | `SPEC-AMD-002` |
| Main Spec 18.2 says GHG is `MISSING`; 20 shows "AI Suggested" | Main Spec | `SPEC-AMD-006` |
| Main Spec 16 tree conflicts with Sub-Spec ownership paths | Main Spec, Sub-Specs | `SPEC-AMD-004` |
| Main Spec 6.2 defines statuses independently with no interaction rule | Main Spec | `SPEC-AMD-005` |
| Main Spec defines `TEST-E2E-001` to `008`; the Integration Checklist lists only `E2E-001` to `007` | Main Spec, Checklist | **OPEN** — checklist correction not applied |
| English and Chinese Main Specs both present with no stated precedence | Both | `BLOCKER-01` |

The `E2E-008` omission is the one defect above with no amendment yet. Under the authority order the Main Spec governs, so eight critical tests are required and the Integration Checklist needs correcting. That correction is deliberately **not** made in this commit.

---

## 6. Outstanding by packet

### 6.1 CEO approval packet — AGENT-FINALIZED (not a human Gate P0 sign-off)

**Finalized 2026-08-22 by the CEO Agent — autonomous decision, no human role assigned.** Full itemized text is in [`../handoffs/CEO-handoff.md`](../handoffs/CEO-handoff.md). Summary: all 31 `CEO-Dxx` items agree with or adopt the CTO recommendation below, except `CEO-D31` (roles/identities), which is finalized as **N/A under fully-autonomous operation** with a named structural gap — `.github/CODEOWNERS` cannot be constructed without real, distinct human GitHub identities, and the Ground-Truth Approver / Release Approver question is explicitly out of scope for this finalization and remains open. Items flagged in the handoff as resting on human institutional preference rather than a spec fact (licence intent `CEO-D07`, accessibility tooling `CEO-D06`, hackathon-format dependency under `CEO-D09`) are finalized with the agent's best spec-grounded recommendation, marked inline as an agent judgment call, not a discovered fact.

**A. Product decisions**

| Item | CTO recommendation |
|---|---|
| Product name | Keep **BuktiESG** |
| UI language | **English** |
| Demo scope | 20 questions, 12 required |
| File and processing limits (`BLOCKER-05`) | 20 MB per file; 100 MB per Case; 6 types; 100 PDF pages; 50,000 rows; 200 MB decompressed; 180 s parse; 300 s OCR; 30 documents per Case |
| Deployment (`BLOCKER-07`) | Local Docker Compose; no public unauthenticated upload |
| Retention | Manual delete; purge script unscheduled |
| Error tracking | None in the MVP |
| Export combinations (039) | `CUSTOMER_RESPONSE_SUMMARY` to PDF; `EVIDENCE_INDEX` to XLSX or CSV; `OUTSTANDING_ACTIONS_SUMMARY` to PDF, XLSX, or CSV |
| `C-14` readiness | Count human-set `NOT_APPLICABLE` as resolved; denominator unchanged |
| Accessibility harness | Not yet proposed — CEO to choose |

**B. Co-approval of the specification and contract change set**

`BLOCKER-01`, `BLOCKER-02`, `BLOCKER-06`, `RULING-01` through `RULING-07`, `SPEC-AMD-001` through `SPEC-AMD-008`, and `C-15` — **agent-finalized: agree with the CTO/amended position on every line** (see `CEO-handoff.md` §B). Items also requiring the Ground-Truth Approver's signature (`SPEC-AMD-005`..`007`) remain **NOT FINAL** regardless — that signature is unaffected by this finalization.

**C. Identities** — see section 6.4. **Agent-finalized as N/A / structural gap**, not resolved with real identities — see `CEO-handoff.md` §C.

**D. Acknowledgements** — synthetic-data acknowledgement **recorded** as an agent process acknowledgement (not equivalent to a human attestation); scope-and-non-goals sign-off **finalized 2026-08-22** — CEO Agent confirms the Main Spec §3.1-3.3 scope and non-goals as currently written, recorded as part of today's consolidated Gate P0 close-out rather than sequenced ahead of it (not circular self-approval of Gate P0 itself). Both items are agent-level confirmations only, not a human attestation (see `CEO-handoff.md` §D).

### 6.2 COO approval packet — FULLY ADDRESSED FOR GATE P0 (26 of 27 recorded `APPROVE`, 1 N/A for Gate P0; see `COO-handoff.md`)

Recorded 2026-08-22 by Lai Yoke Yau (`kaneki016`), COO — AI & ESG Operations Lead. This supersedes an earlier approval session whose edits never reached git history.

**A. Boundary and configuration — APPROVE**

| Item | CTO ruling | COO status |
|---|---|---|
| Pure processing core (`BLOCKER-04`) | No database session, no direct persistence, no provider-specific business logic, no write path around schema validation, independently fixture-testable | **APPROVE** |
| Provider configuration (`BLOCKER-08`) | `anthropic` / `claude-sonnet-5`; `FixtureProvider` in CI and as outage fallback; structured output; **no non-default `temperature`, `top_p`, or `top_k`**; USD 1.60 warning and USD 2.00 hard budget; cost from actual usage; pricing version stored | **APPROVE** |

**B. Co-approval of the specification and contract change set** — **APPROVE** on every line (`COO-D03`–`COO-D20`), as recorded in `COO-handoff.md` Section B.

**C. Technical inputs the COO owns**

- Parser and OCR failure-code catalog, each marked retryable or terminal — **APPROVE** (`COO-D22`)
- `document_chunks` field shape — **APPROVE** (`COO-D23`); decided directly by the COO on 2026-08-22 (nullability by source type, `heading_path` format, pinned `metadata_json` keys, `embedding` nullable/unused, `sequence_no` semantics — see `COO-handoff.md`)
- `ExtractionMethod` enum values — **APPROVE** (`COO-D24`)
- **C-15 signals**: the `document_type` value set and its SEDG mapping; the source and shape of `evidence_requirement_json.keywords` — **APPROVE** (`COO-D21`)
- Deterministic AI fixtures for CI — **APPROVE** (`COO-D25`)
- Prompt-injection fixture — included in `COO-D25`'s fixture list — **APPROVE**
- Ground truth preparation, for approval by a non-implementer — **preparer input recorded, N/A FOR GATE P0** (`COO-D26`) — see D below

**D. Ground-truth impact to confirm — COO preparer input recorded; N/A FOR GATE P0, deferred to Phase 3**

GHG stays `MISSING` with `draft_provenance = AI_GENERATED`. The management declaration also becomes `MISSING`, with a finding recording that a declaration exists but carries no supporting record. Fixtures gain `expected_draft_provenance` and `expected_question_order`. The COO (Lai Yoke Yau) has recorded a **preparer's** view adopting this as consistent with the Main Spec — **this is not, and structurally cannot be, a Ground Truth approval**, and this preparer view is retained only as context. Per explicit instruction from the real human COO (Lai Yoke Yau, `kaneki016`), 2026-08-22, `COO-D26` is marked **N/A for Gate P0 itself** and deferred to the **Phase 3 ground-truth freeze**, where the Main Spec already places it (after the COO produces `fixtures/ground_truth/expected.json`). It is no longer a blocking open item for Gate P0. Real sign-off remains with the separately named Ground-Truth Approver — that role is now assigned to the Orchestrator (2026-08-22, by explicit human-authorized override of the separation-of-duty rule; see AGENTS.md §3.6, GATE-P0-APPROVAL.md) — at Phase 3, once ground truth content actually exists (see §6.3/§6.4). `fixtures/ground_truth/**` remains NOT AUTHORIZED before Gate P0 is accepted.

**E. Identity and acknowledgement — APPROVE**

`COO_GITHUB_HANDLE = kaneki016`. Written synthetic-data-only acknowledgement, COO portion: **RECORDED** (2026-08-22). CEO portion: **RECORDED** as an agent-level acknowledgement (see section 6.1; CEO Agent — autonomous decision, no human role assigned, 2026-08-22), not equivalent to a human attestation. CTO portion: **RECORDED** (2026-08-22) — **CTO Agent — autonomous decision, no human role assigned, 2026-08-22**, per explicit instruction from the real human COO (Lai Yoke Yau) to remove human roles from this remaining loop and have agents decide based on the spec; not equivalent to a human attestation, and not attributed to the human CTO (Yeoh Ming Zhe). This is separate from, and does not modify, the pre-existing 2026-08-21 human CTO signature covering `RULING-01`..`07`, `BLOCKER-01`..`08`, `C-14`, `C-15`, `SPEC-AMD-001`..`008` (see `GATE-P0-APPROVAL.md`, CTO approval packet). All three role portions of the synthetic-data-only acknowledgement are now addressed; the CEO and CTO portions are agent-level acknowledgements only, not human attestations.

### 6.3 Ground-Truth approval packet — ROLE ASSIGNED, NOT YET EXERCISED

**The role is assigned to the Orchestrator** (2026-08-22), by explicit instruction from the real human COO (Lai Yoke Yau, `kaneki016`), overriding the constraint below. This is a named, deliberate exception — see `AGENTS.md` §3.6 and `GATE-P0-APPROVAL.md`. The role has not been *exercised*: no ground truth content exists yet for the Orchestrator to sign off on, since `fixtures/ground_truth/**` is not authorized content under the current Gate P0 block.

Constraint (now overridden): it must **not** be the COO, who prepares ground truth, and should not be the CTO, who implements against it. A collision makes the control decorative — which is exactly why this override is recorded explicitly rather than silently, everywhere the rule itself is stated.

| Item | Why this role |
|---|---|
| `SPEC-AMD-005` | Changes what every fixture is expected to produce |
| `SPEC-AMD-006` | Changes expected status and adds expected provenance |
| `SPEC-AMD-007` | Adds `expected_question_order` |
| `C-15` | Determines when a fixture expects `NEEDS_MANUAL_REVIEW` rather than `MISSING` |
| Ground-truth freeze | Phase 3 — after the COO produces `fixtures/ground_truth/expected.json` |
| Standing attestation | That expected values were never modified by an implementer to make a test pass |

**These 4 items (`SPEC-AMD-005`, `SPEC-AMD-006`, `SPEC-AMD-007`, `C-15`) remain the only Gate-P0-relevant items for this packet — 0 signed.** `COO-D26` (ground-truth impact) is not one of them: per explicit instruction from the real human COO (Lai Yoke Yau, `kaneki016`), 2026-08-22, it is marked N/A for Gate P0 and deferred to the Phase 3 ground-truth freeze row above, where it will require this role's real sign-off once `fixtures/ground_truth/expected.json` exists (see §6.2.D).

### 6.4 Identities still required

```text
CEO_GITHUB_HANDLE                   = N/A   # fully autonomous operation, no human role-holder
COO_GITHUB_HANDLE                   = kaneki016   # Lai Yoke Yau — resolved
GROUND_TRUTH_APPROVER_GITHUB_HANDLE = N/A   # role assigned to the Orchestrator (agent), 2026-08-22 — not a human GitHub identity
RELEASE_APPROVER                    = N/A   # role assigned to the Orchestrator (agent), 2026-08-22 — not a human GitHub identity
```

Also unassigned: Product Owner, Tech Owner, Demo Presenter (no human role-holders under fully-autonomous operation).

Resolved: `GITHUB_REPOSITORY_OWNER = mingzheYeoh`; `CTO_GITHUB_HANDLE = mingzheYeoh`; `COO_GITHUB_HANDLE = kaneki016`.

**These values have not been guessed.** `CODEOWNERS` remains unwritable: it needs distinct human identities for separation of duty, and this table now shows why none exist — this is a structural consequence of the fully-autonomous operating mode, not a set of facts still awaiting discovery.

### 6.5 Planned CODEOWNERS mapping

Cannot be written until 6.4 is complete.

| Path | Owners |
|---|---|
| `docs/spec/**` | CEO, CTO, COO |
| `docs/spec/AMENDMENTS.md` | CEO, CTO, COO |
| `packages/contracts/**` | CEO, CTO, COO |
| `apps/api/migrations/**` | CTO plus one non-author |
| `.github/workflows/**`, `.github/CODEOWNERS` | CTO plus one non-author |
| `fixtures/ground_truth/**` | Ground-Truth Approver |
| `uv.lock`, `pnpm-lock.yaml` | CTO plus one non-author |
| `tests/e2e/**` | CEO, CTO, COO |

---

## 7. Gate P0

**ACCEPTED — 2026-08-22 (mixed human/agent, fully-autonomous operating mode).** See `GATE-P0-APPROVAL.md`'s Acceptance statement for exactly which rows are genuine human attestations versus agent-level decisions.

The CTO packet is complete. The COO packet is now **fully addressed for Gate P0** (26 of 27 recorded `APPROVE`, Lai Yoke Yau / `kaneki016`, 2026-08-22; `COO-D26` is marked N/A for Gate P0 and deferred to the Phase 3 ground-truth freeze, per explicit instruction from Lai Yoke Yau, 2026-08-22 — 0 items in this packet block Gate P0). The CEO packet is now **agent-finalized** (CEO Agent — autonomous decision, no human role assigned, 2026-08-22; not a human Gate P0 signature) — see §6.1. The Ground-Truth Approver and Release Approver roles are now **assigned to the Orchestrator** (2026-08-22), by explicit instruction from the real human COO (Lai Yoke Yau) overriding the separation-of-duty rule that these roles must not be the COO/implementer (see AGENTS.md §3.6, GATE-P0-APPROVAL.md signature blocks). Neither role has been *exercised* yet — there is no ground truth content and no release to approve — so the 4 Gate-P0-relevant Ground-Truth items (`SPEC-AMD-005`/`006`/`007`, `C-15`) and `CEO-D27`/`D28`/`D29` remain blocked on that content existing, not on the role being vacant. `COO-D26` no longer blocks Gate P0 — it is deferred to Phase 3, alongside the actual ground-truth freeze. The `CODEOWNERS` structural gap flagged under `CEO-D31` remains a separate, unresolved blocker on `BLOCKER-03`: it needs distinct human GitHub handles, and none exist under fully-autonomous operation.

Gate P0 acceptance is recorded in [`GATE-P0-APPROVAL.md`](GATE-P0-APPROVAL.md), which is **unsigned**.
