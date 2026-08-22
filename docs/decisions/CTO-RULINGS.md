# CTO Rulings

| Field | Value |
|---|---|
| Status | **PROPOSED** |
| Gate P0 | **BLOCKED** |
| Main Spec target | **v1.1 — NOT ACCEPTED** |
| Contract target | **v1.1.0 — NOT FROZEN** |
| Feature implementation | **NOT AUTHORIZED** |
| Ruling authority | CTO — Backend & Integration Lead |
| Date | 2026-08-21 |

**These are CTO rulings, not final approvals.**

A CTO ruling is binding within CTO authority: system architecture, the FastAPI backend, PostgreSQL and migrations, OpenAPI and shared contracts, file and processing-job lifecycle, deterministic evidence and priority rules, action-tracking persistence, export services, CI, deployment, observability, rollback, integration, and main-branch coordination.

A CTO ruling is **not** sufficient where the item touches:

- **product outcomes or UX** — CEO;
- **AI pipeline, parsing, OCR, SEDG mapping, or evidence extraction** — COO;
- **what a fixture is expected to produce** — Ground-Truth Approver;
- **the Main Spec or the Shared Contract** — CEO + CTO + COO jointly.

Approval state for every item is tracked in [`decision-register.md`](decision-register.md).

---

## RULING-01 — Job and Export concepts — **AMEND**

Approved in concept. Amended in four respects.

### Version classification

An earlier proposal shipped these changes as **v1.0.1**. **Reversed.** These are additive behavioural contract changes including new resources, enums, fields, fixtures, and endpoints. Under the contract's own versioning rules the amended contract is **v1.1.0**.

### Enums

```text
JobType:          DOCUMENT_PARSE | DOCUMENT_INDEX | QUESTION_ANALYZE | EXPORT_RENDER
JobStatus:        QUEUED | RUNNING | SUCCEEDED | FAILED | CANCELLED
ExportType:       CUSTOMER_RESPONSE_SUMMARY | EVIDENCE_INDEX | OUTSTANDING_ACTIONS_SUMMARY
ExportFormat:     PDF | XLSX | CSV
```

**`ExportType` describes what artifact is produced. `ExportFormat` describes its file format. Do not substitute one for the other.**

The allowed combinations must be defined explicitly in the contract. The CTO proposal is in [`../spec/Shared-Integration-Contract-v1.1.0-PROPOSED.md`](../spec/Shared-Integration-Contract-v1.1.0-PROPOSED.md) section 1.1 and requires CEO approval, because which artifact ships in which format is a product decision.

An earlier proposal used the value `OUTSTANDING_ACTIONS`. The ruled value is **`OUTSTANDING_ACTIONS_SUMMARY`**.

### Enum storage

**Do not use PostgreSQL native ENUM types in the initial migration.**

Use `text` fields with server-side validation and database `CHECK` constraints **generated from the shared contract**.

Rationale worth preserving: native ENUM types make an unknown value unstorable by construction, which was the original attraction. Generated `CHECK` constraints give the same guarantee while remaining alterable without a type migration. The guarantee moves from the type system to the generator — so `CT-011` must assert contract-to-constraint parity in both directions, or the guarantee silently rots the first time someone adds a value and forgets to regenerate.

**Status:** CTO AMENDED. CEO and COO approval pending.

---

## RULING-02 — Evidence Status evaluation — **AMEND**

### Frozen precedence

```text
CONFLICTING > OUTDATED > PARTIAL > VERIFIED
```

Lower-priority findings are **never discarded.** Every detected condition is preserved in `status_findings` and summarized in `status_reason`. `VERIFIED` is permitted only when no blocking condition remains.

### NOT_APPLICABLE

Human-controlled only. Requires a **reason** and a **reviewer identity**. It survives recalculation unless a human reopens the question. The rule engine may never set it and may never clear it.

### Four-step evaluation

```text
1. If NOT_APPLICABLE was set by a human, that is the result.

2. Exclude unreadable and extraction-invalid evidence
   from the evidence-quality computation entirely.

3. Evaluate the remaining readable evidence using the frozen precedence.
   If it yields CONFLICTING, OUTDATED, PARTIAL, or VERIFIED, that is the result.

4. Otherwise:
     NEEDS_MANUAL_REVIEW  if a relevant unreadable document may materially
                          affect the answer (see C-15)
     MISSING              otherwise
```

### Two constraints that are easy to violate

- An unreadable candidate **must not suppress** a genuine conflict found between two other reliable sources.
- Unreadable OCR output **must never create** a conflict.

### Rejected proposal

An earlier CTO proposal made `NEEDS_MANUAL_REVIEW` an unconditional rank-2 override, above `CONFLICTING`. **Rejected.** Under that model a single unreadable scan anywhere in a Case would mask every genuine conflict in it — the exact failure the product exists to prevent.

**Status:** CTO AMENDED. CEO, COO, and Ground-Truth Approver approval pending.

---

## RULING-03 — Draft provenance — **AMEND**

### AI_SUGGESTED removed

`AI_SUGGESTED` is **removed** from `EvidenceStatus`, which drops from 8 values to 7.

An earlier proposal deprecated the value but retained it, with a permanently-zero key in `evidence_status_counts` for compatibility. **Rejected.** The contract has never been accepted or implemented, so there is no client to be compatible with. A permanently-dead enum value and a permanently-zero count key in a clean pre-implementation baseline are debt with no corresponding asset.

### DraftProvenance

```text
DraftProvenance: NONE | AI_GENERATED | AI_ASSISTED_EDIT | USER_ENTERED
```

### Invariant

```text
draft_provenance IN (AI_GENERATED, AI_ASSISTED_EDIT)  ->  ai_run_id IS NOT NULL
```

An earlier proposal used a biconditional. **Rejected**: it contradicts retaining `ai_run_id` after a human edits an AI draft. `AI_ASSISTED_EDIT` is the value that makes the edited case representable, and the one-directional implication is the form that survives it.

### Counts

The purple "AI Suggested" UI indicator is driven by `draft_provenance_counts`. There is no permanently-zero key in `evidence_status_counts`.

### Three independent dimensions

| Dimension | Field | Source |
|---|---|---|
| Evidence availability and quality | `evidence_status` | Deterministic rule engine |
| Draft provenance | `draft_provenance` | Where the text came from |
| Human review state | `review_status`, `human_confirmed` | A human |

The AI pipeline never emits any of `evidence_status`, `status_findings`, or review state.

**Status:** CTO AMENDED. CEO, COO, and Ground-Truth Approver approval pending.

---

## RULING-04 — Questionnaire ordering — **AMEND**

### Rejected proposal

Ordering by `section ASC, source_location ASC, external_question_id ASC, id ASC`. **Rejected.** **Lexical sorting can place row 10 before row 2, and `Q-10` before `Q-2`.** Those fields are display identifiers, not sequence.

### Ruling

Add a persisted integer column `question_order`, assigned deterministically during import from workbook order, then sheet order, then row order.

```text
GET /cases/{case_id}/questions  ->  ORDER BY question_order ASC, id ASC
```

A fixture with **more than 20 questions** is required so cross-page ordering is genuinely exercised.

This adds a field to Main Spec 10.1 `questions`, a protected section, and therefore requires **`SPEC-AMD-007`**.

**Status:** CTO AMENDED. CEO and COO approval pending. Ground-Truth Approver approval required for `expected_question_order`.

---

## RULING-05 — Bounded previews — **APPROVE WITH CONTRACT DETAIL**

Detail responses carry **named preview objects**, never bare arrays:

```text
evidence_preview: { items: [...], total_count: int, has_more: bool }   # cap 50
activity_preview: { items: [...], total_count: int, has_more: bool }   # cap 20
```

A bare array that has been truncated is indistinguishable from a complete one. A named object with `total_count` and `has_more` cannot lie by omission.

New endpoint:

```text
GET /cases/{case_id}/activity
  query: entity_type, entity_id, page, page_size
```

**Must enforce Case ownership.** An `entity_id` outside `case_id` returns `404` — never another Case's rows, and never an empty `200` that conceals the boundary violation.

This adds an endpoint absent from Main Spec 11 and therefore requires **`SPEC-AMD-008`**.

**Status:** CTO APPROVED. CEO and COO approval pending.

---

## RULING-06 — Idempotency and concurrency — **APPROVE OPTION C WITH ADDITIONAL RULES**

`Idempotency-Key` is **required** on `POST /questions/{question_id}/analyze`.

| Situation | Response |
|---|---|
| New key, no active job | **202 Accepted**, new job, `job_reused: false` |
| Same key, same payload, in progress | **202 Accepted**, original job, `job_reused: true` |
| Same key, different payload | **409 `IDEMPOTENCY_KEY_REUSED`** |
| Different key, active job exists | **202 Accepted**, existing job, `job_reused: true` |

The response indicates whether the job was reused. A client that cannot distinguish "I started this" from "this was already running" will double-count progress.

**Exactly one AI Run and exactly one provider call**, regardless of concurrent request count.

Idempotency is scoped to the **operation and the Case**:

```text
UNIQUE (case_id, operation, idempotency_key)
```

**The concurrency guard must be enforced by the database, not only by application code:**

```text
UNIQUE (question_id) WHERE job_type = 'QUESTION_ANALYZE'
                       AND status IN ('QUEUED', 'RUNNING')
```

Application-level checks lose races; a partial unique index does not.

An earlier proposal named the error `IDEMPOTENCY_KEY_CONFLICT`. The ruled name is **`IDEMPOTENCY_KEY_REUSED`**.

**Status:** CTO APPROVED. CEO and COO informed.

---

## RULING-07 — Amendments recorded individually — **APPROVE INDIVIDUALLY WITH AMENDMENTS**

Six amendments recorded separately for auditability; Main Spec target becomes **v1.1**.

| ID | CTO ruling |
|---|---|
| `SPEC-AMD-001` | APPROVED |
| `SPEC-AMD-002` | APPROVED |
| `SPEC-AMD-003` | APPROVED AS AMENDED |
| `SPEC-AMD-004` | APPROVED |
| `SPEC-AMD-005` | APPROVED AS AMENDED |
| `SPEC-AMD-006` | APPROVED AS AMENDED |

Two further amendments arise as consequences of RULING-04 and RULING-05 and were not in the original six:

| ID | CTO ruling | Arises from |
|---|---|---|
| `SPEC-AMD-007` | APPROVED | RULING-04 adds a column to protected Main Spec 10.1 |
| `SPEC-AMD-008` | APPROVED | RULING-05 adds an endpoint absent from Main Spec 11 |

**These are CTO approvals only. Final approval is not recorded until the required CEO, COO, and Ground-Truth Approver signatures are obtained.**

Full text: [`../spec/AMENDMENTS.md`](../spec/AMENDMENTS.md).

---

## C-14 — NOT_APPLICABLE and the readiness denominator — **CTO RECOMMENDATION TO CEO**

### The question

The readiness formula is protected:

```text
readiness = confirmed_required_questions / total_required_questions * 100
```

Only `HUMAN_CONFIRMED` required answers count. A required question a human has marked `NOT_APPLICABLE` is resolved but never confirmed, so it can never be counted — which caps readiness below 100% permanently for any Case containing one.

### CTO recommendation

```text
resolved_required_questions
  = human_confirmed_required_answers
  + human_confirmed_not_applicable_required_questions
```

The denominator is unchanged. `NOT_APPLICABLE` is human-set and carries a reason and a reviewer identity, so it is a human decision of the same weight as a confirmation — which is the property the formula actually cares about.

**This is a product decision. The CEO decides. Required before Phase 4.**

**Status:** CTO recommendation only. CEO decision pending.

---

## C-15 — Relevance of an unreadable document — **CTO RULING**

### The problem

RULING-02 step 4 returns `NEEDS_MANUAL_REVIEW` when "a relevant unreadable document may materially affect the answer." That phrase is not deterministically evaluable as written, and the reason is circular: the document is unreadable, so its content cannot be consulted to judge its relevance.

The rule below resolves this by depending **only on signals that survive extraction failure**. None of them require the body text that extraction failed to produce.

### Ruling

An unreadable document may materially affect a question **only when all three conditions hold**:

1. Its processing status is `NEEDS_MANUAL_REVIEW`.
2. Its `document_type` is included in the question's `evidence_requirement_json.accepted_document_types`.
3. At least one normalized required keyword from `evidence_requirement_json.keywords` **exactly matches** a token found in:
   - `original_filename`; or
   - successfully extracted document metadata or heading text.

### Normalization — deterministic

```text
Unicode normalization
Case-insensitive
Punctuation replaced by spaces
Repeated whitespace collapsed
Exact token matching only

NO embedding similarity
NO LLM classification
NO fuzzy matching
```

The prohibition on fuzzy and embedding matching is what keeps this auditable. A similarity threshold is a number someone can quietly tune until a failing test passes; exact token matching cannot be tuned, so the rule engine's output is reproducible from the fixture alone.

### Evaluation

```text
if readable evidence produces CONFLICTING, OUTDATED, PARTIAL, or VERIFIED:
    use that result
elif a relevant unreadable document satisfies the rule above:
    NEEDS_MANUAL_REVIEW
else:
    MISSING
```

### Auditability

The rule engine **must record which `document_type` and which keyword caused the relevance result** in `status_findings`. A reviewer must be able to see why a question was routed to manual review without re-running the engine.

### AI boundary

An AI-only relevance recommendation **may be shown to a reviewer, but it cannot independently trigger `NEEDS_MANUAL_REVIEW`.** The status remains a deterministic computation.

### Dependencies

This ruling requires two things the COO owns and has not yet supplied:

- the `document_type` value set and its mapping to SEDG topics;
- the source and shape of `evidence_requirement_json.keywords`.

**Status:** CTO ruling recorded. CEO, COO, and Ground-Truth Approver approval pending. Required before `SPEC-AMD-005` can be finalized and before Phase 4.

---

## Blocker Rulings

| ID | Ruling | CTO | Outstanding |
|---|---|---|---|
| `BLOCKER-01` | The **English** Main Spec is normative. The Chinese document is a non-normative translation; on conflict English governs. | RULED | CEO, COO |
| `BLOCKER-02` | Map Sub-Spec ownership paths into the Main Spec section 16 tree. **No duplicate top-level trees.** | RULED | CEO, COO |
| `BLOCKER-03` | GitHub; protected `main`; PR required; at least one non-author approval; required `ci / verify` check; `CODEOWNERS` over contracts, migrations, workflows, ground truth, lockfiles, Main Spec, and protected rules. | RULED (policy) | 4 identities — see [`decision-register.md`](decision-register.md) |
| `BLOCKER-04` | A **pure COO-owned processing core**: no database session, no direct persistence, no provider-specific business logic, no write path around schema validation, independently testable with fixtures. A **CTO-owned orchestration layer** loads jobs and files, calls the core, validates the result, and persists it. | RULED | COO |
| `BLOCKER-05` | 20 MB per file; 100 MB per Case; 6 supported types; 100 PDF pages; 50,000 rows per file; 200 MB decompressed per archive; 180 s parse timeout; 300 s OCR timeout; 30 documents per Case. | RECOMMENDED | CEO / Product Owner |
| `BLOCKER-06` | **Keyword-first.** PostgreSQL full-text active. pgvector may be installed. `document_chunks.embedding` nullable and unused. No embedding pipeline until evaluation against protected ground truth shows measurable value. Enabling hybrid requires a recorded decision plus evaluation evidence. | RULED | CEO, COO |
| `BLOCKER-07` | **Local Docker Compose** is the demo path of record. **No unauthenticated upload endpoint may be exposed publicly.** A public preview is a later stretch decision requiring a platform-level access gate. | RECOMMENDED | CEO / Product Owner |
| `BLOCKER-08` | See below. | RECOMMENDED | COO, Product Owner |

### BLOCKER-08 — Provider configuration

```text
provider          = anthropic
model             = claude-sonnet-5
CI provider       = FixtureProvider          (also the outage fallback)
warning budget    = USD 1.60 per Case
hard budget       = USD 2.00 per Case
```

Pricing snapshot **2026-08-21**: input USD 2 per million tokens, output USD 10 per million tokens.

```text
estimated_cost = (input_tokens / 1_000_000 * 2) + (output_tokens / 1_000_000 * 10)
```

Computed from **actual API usage**, never from an estimate. The pricing version and date are stored with each AI Run, so a later price change never rewrites the recorded cost of past runs.

Additional rules:

- Use structured output.
- **Do not set non-default `temperature`, `top_p`, or `top_k`.** Determinism in the pipeline comes from the rule engine, not from sampling parameters; tuning them creates the appearance of control without the substance.
- Provider configuration lives behind the `LLMProvider` adapter.
- **Never use the live provider in CI.**
- Reaching the hard budget **stops automatic processing** and requires explicit human approval to continue.

---

**All rulings above are CTO rulings. None is a final approval. Gate P0 is BLOCKED.**
