# Decision Register

| Field | Value |
|---|---|
| Status | **PROPOSED** |
| Gate P0 | **BLOCKED** |
| Main Spec target | **v1.1 — NOT ACCEPTED** |
| Contract target | **v1.1.0 — NOT FROZEN** |
| Feature implementation | **NOT AUTHORIZED** |
| Date | 2026-08-21 |

---

## How approval is tracked

Approvals are collected as **one consolidated packet per human role**, not as a scatter of individual signatures. A packet may approve many line items at once while each line item retains its own `APPROVE` / `AMEND` / `REJECT` status.

| Packet | Holder | Decisions | Recorded | State |
|---|---|---|---|---|
| **CTO approval packet** | Yeoh Ming Zhe (`mingzheYeoh`) | — | — | **COMPLETE** |
| **CEO approval packet** | **PENDING** — role unassigned, workstream not started | 31 (`CEO-D01`…`CEO-D31`) | **0** | **NOT RECEIVED** |
| **COO approval packet** | **PENDING** — role unassigned, workstream not started | 27 (`COO-D01`…`COO-D27`) | **0** | **NOT RECEIVED** |
| **Ground-Truth approval packet** | **PENDING** — role unassigned | 4 at Gate P0 | **0** | **NOT RECEIVED** |

Full packets: [`../handoffs/CEO-handoff.md`](../handoffs/CEO-handoff.md) · [`../handoffs/COO-handoff.md`](../handoffs/COO-handoff.md). **Every decision in both is marked `PENDING`.** None has been inferred, simulated, or recorded on a role owner's behalf.

Each outstanding decision is listed in **exactly one** packet, under the role that owns it. Co-approvals are noted on the line but never counted twice.

**Three packets outstanding. Zero received.**

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
| `CEO_GITHUB_HANDLE` | **PENDING** |
| `COO_GITHUB_HANDLE` | **PENDING** |
| `GROUND_TRUTH_APPROVER_GITHUB_HANDLE` | **PENDING** |
| `RELEASE_APPROVER` | **PENDING** |

`.github/CODEOWNERS` cannot be written until all four remaining values are supplied. `BLOCKER-03` remains **BLOCKED**.

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
| 039 | Allowed `ExportType` and `ExportFormat` combinations | PROPOSED | **NO** | CEO |
| 040 | Cost formula and pricing-snapshot versioning | RECOMMENDED | **NO** | COO, CEO |

**13 decisions are FINAL within CTO authority. Every decision that touches the Main Spec, the Shared Contract, a product outcome, the AI pipeline, or an expected fixture value is NOT FINAL.**

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

### 6.1 CEO approval packet — NOT RECEIVED

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

`BLOCKER-01`, `BLOCKER-02`, `BLOCKER-06`, `RULING-01` through `RULING-07`, `SPEC-AMD-001` through `SPEC-AMD-008`, and `C-15`. Individual `APPROVE` / `AMEND` / `REJECT` per line item; one packet.

**C. Identities** — see section 6.4.

**D. Acknowledgements** — written synthetic-data acknowledgement; scope and non-goals sign-off.

### 6.2 COO approval packet — NOT RECEIVED

**A. Boundary and configuration**

| Item | CTO ruling |
|---|---|
| Pure processing core (`BLOCKER-04`) | No database session, no direct persistence, no provider-specific business logic, no write path around schema validation, independently fixture-testable |
| Provider configuration (`BLOCKER-08`) | `anthropic` / `claude-sonnet-5`; `FixtureProvider` in CI and as outage fallback; structured output; **no non-default `temperature`, `top_p`, or `top_k`**; USD 1.60 warning and USD 2.00 hard budget; cost from actual usage; pricing version stored |

**B. Co-approval of the specification and contract change set** — as in 6.1 B.

**C. Technical inputs the COO owns and has not supplied**

- Parser and OCR failure-code catalog, each marked retryable or terminal
- `document_chunks` field shape
- `ExtractionMethod` enum values
- **C-15 signals**: the `document_type` value set and its SEDG mapping; the source and shape of `evidence_requirement_json.keywords`
- Deterministic AI fixtures for CI
- Prompt-injection fixture
- Ground truth preparation, for approval by a non-implementer

**D. Ground-truth impact to confirm**

GHG stays `MISSING` with `draft_provenance = AI_GENERATED`. The management declaration also becomes `MISSING`, with a finding recording that a declaration exists but carries no supporting record. Fixtures gain `expected_draft_provenance` and `expected_question_order`.

**E. Identity and acknowledgement** — GitHub handle; written synthetic-data acknowledgement.

### 6.3 Ground-Truth approval packet — NOT RECEIVED

**The role is unassigned.** It must **not** be the COO, who prepares ground truth, and should not be the CTO, who implements against it. A collision makes the control decorative.

| Item | Why this role |
|---|---|
| `SPEC-AMD-005` | Changes what every fixture is expected to produce |
| `SPEC-AMD-006` | Changes expected status and adds expected provenance |
| `SPEC-AMD-007` | Adds `expected_question_order` |
| `C-15` | Determines when a fixture expects `NEEDS_MANUAL_REVIEW` rather than `MISSING` |
| Ground-truth freeze | Phase 3 — after the COO produces `fixtures/ground_truth/expected.json` |
| Standing attestation | That expected values were never modified by an implementer to make a test pass |

### 6.4 Identities still required

```text
CEO_GITHUB_HANDLE                   = PENDING
COO_GITHUB_HANDLE                   = PENDING
GROUND_TRUTH_APPROVER_GITHUB_HANDLE = PENDING   # must NOT equal COO_GITHUB_HANDLE
RELEASE_APPROVER                    = PENDING   # name and handle; must not be the implementer
```

Also unassigned: Product Owner, Tech Owner, Demo Presenter.

Resolved: `GITHUB_REPOSITORY_OWNER = mingzheYeoh`; `CTO_GITHUB_HANDLE = mingzheYeoh`.

**These values have not been guessed.**

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

**BLOCKED.**

Zero of three outstanding approval packets have been received. The CTO packet is complete and has no outstanding items.

Gate P0 acceptance is recorded in [`GATE-P0-APPROVAL.md`](GATE-P0-APPROVAL.md), which is **unsigned**.
