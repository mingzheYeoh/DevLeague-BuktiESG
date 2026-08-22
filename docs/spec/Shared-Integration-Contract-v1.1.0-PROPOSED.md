# Shared Integration Contract — v1.1.0 PROPOSED

| Field | Value |
|---|---|
| Status | **PROPOSED** |
| Gate P0 | **BLOCKED** |
| Contract target | **v1.1.0 — NOT FROZEN** |
| Main Spec target | **v1.1 — NOT ACCEPTED** |
| Feature implementation | **NOT AUTHORIZED** |
| Baseline | [`Shared-Integration-Contract.md`](Shared-Integration-Contract.md) v1.0.0, unmodified |
| Change approval required | **CEO + CTO + COO** |
| Approvals held | **CTO only** |

**This document is a delta, not a replacement.** The v1.0.0 baseline is retained unmodified so the change is auditable. Nothing here has been merged into the baseline, and no client may implement against either document.

---

## Why v1.1.0 and not v1.0.1

An earlier CTO proposal classified these changes as a patch release, v1.0.1, on the reasoning that they clarify a contract with zero clients. **That classification was reversed.**

These are **additive behavioural contract changes** including new resources, new enums, new fields, new fixtures, and new endpoints. Under the contract's own versioning rules that is a **minor** release. The amended contract is **v1.1.0**.

The earlier flag that `JobType` and `ExportFormat` are genuinely additive rather than clarifying was the correct reading.

---

## Defects in v1.0.0 this release addresses

Contract v1.0.0 is **not implementable as written**. Recorded here so the gaps are not rediscovered later:

| Defect | Detail |
|---|---|
| Unreachable endpoint | `GET /api/v1/jobs/{job_id}` exists with no resource, no schema, no enum, no lifecycle, and no owning role. No client can obtain a `job_id` after a page refresh, because nothing on the Document links to its job. |
| Undefined enums in own examples | `pillar` and `export_type` appear in the contract's own example payloads with no canonical definition anywhere. |
| Pagination declared but unshaped | Paginated endpoints are named; no parameter names, bounds, defaults, response envelope, or ordering are given. |
| Deferred values never supplied | The concurrency guard and the idempotency scope are both deferred to "Phase 0" with no value. |

---

## 1. Enums added

```text
JobType:          DOCUMENT_PARSE | DOCUMENT_INDEX | QUESTION_ANALYZE | EXPORT_RENDER
JobStatus:        QUEUED | RUNNING | SUCCEEDED | FAILED | CANCELLED
ExportType:       CUSTOMER_RESPONSE_SUMMARY | EVIDENCE_INDEX | OUTSTANDING_ACTIONS_SUMMARY
ExportFormat:     PDF | XLSX | CSV
DraftProvenance:  NONE | AI_GENERATED | AI_ASSISTED_EDIT | USER_ENTERED
```

**`ExportType` and `ExportFormat` are distinct concepts and must never be substituted for one another.**
`ExportType` describes **what artifact is produced**. `ExportFormat` describes **its file format**.

### 1.1 Allowed ExportType × ExportFormat combinations

**CTO proposal. Pending CEO approval** — which artifacts ship in which formats is a product decision.

| ExportType | PDF | XLSX | CSV |
|---|:---:|:---:|:---:|
| `CUSTOMER_RESPONSE_SUMMARY` | yes | no | no |
| `EVIDENCE_INDEX` | no | yes | yes |
| `OUTSTANDING_ACTIONS_SUMMARY` | yes | yes | yes |

A combination outside this table returns `400 VALIDATION_ERROR` and the error detail **must list the allowed formats for the requested type**. A client must never have to guess the table by trial and error.

### 1.2 Enum removed

`AI_SUGGESTED` is **removed** from `EvidenceStatus`, which drops from 8 values to 7. See `SPEC-AMD-006` in [`AMENDMENTS.md`](AMENDMENTS.md) for the full rationale and the audit note explaining why a removal is recorded in a minor release.

Remaining `EvidenceStatus` values:

```text
VERIFIED | PARTIAL | OUTDATED | CONFLICTING | MISSING | NOT_APPLICABLE | NEEDS_MANUAL_REVIEW
```

### 1.3 Storage rule

**Do not use PostgreSQL native ENUM types in the initial migration.**

Enums are stored as `text` with:

- server-side validation from the shared contract, and
- database `CHECK` constraints **generated from the shared contract**.

The v1.0.0 guarantee that an unknown enum value is unstorable is **preserved** — it moves from the type system to a generated constraint. That guarantee only holds if the generation is verified, so a CI job must assert that the `CHECK` constraint value set is exactly equal to the contract enum value set. Without that job, a value added to the contract and not regenerated into the constraint produces a schema that silently accepts what the contract forbids, and nothing fails until the data is already wrong.

### 1.4 Unknown enum values

Contract rule 6 is unchanged: an unknown enum value produces an explicit compatibility error, never a silent fallback.

---

## 2. Processing Job resource

Defined in `SPEC-AMD-001`. Contract additions:

```text
GET /api/v1/jobs/{job_id}     -> Job
GET /cases/{case_id}/jobs     -> paginated Job list
```

`Document` responses gain `latest_job_id` (nullable), which is what makes `GET /jobs/{job_id}` reachable after a refresh.

Job response shape:

```text
{
  "id": "opaque string",
  "case_id": "opaque string",
  "job_type": "JobType",
  "status": "JobStatus",
  "document_id": "opaque string | null",
  "question_id": "opaque string | null",
  "attempt_count": 0,
  "error_code": "string | null",
  "error_message": "string | null",
  "created_at": "2026-08-21T14:30:00Z",
  "started_at": "2026-08-21T14:30:00Z | null",
  "finished_at": "2026-08-21T14:30:00Z | null"
}
```

`idempotency_key` and `lease_expires_at` are **internal** and are never exposed on the wire.

Invalid transitions return `409 INVALID_STATE_TRANSITION` and must not mutate the row.

---

## 3. Pagination — frozen

Applied consistently to every paginated endpoint unless a specific exception is approved below.

**Request:**

| Parameter | Type | Min | Max | Default |
|---|---|---|---|---|
| `page` | integer | 1 | — | 1 |
| `page_size` | integer | 1 | 100 | 20 |

**Response envelope:**

```text
{
  "items": [...],
  "page": 1,
  "page_size": 20,
  "total_items": 137,
  "total_pages": 7,
  "has_next": true
}
```

**Default ordering:** `created_at DESC`, then `id DESC`.

Out-of-range parameters return `400 VALIDATION_ERROR`. They are never silently clamped — a clamped page number returns data the client did not ask for and cannot detect.

### 3.1 Approved exceptions

| ID | Endpoint | Exception | Reason |
|---|---|---|---|
| `EXC-01` | `GET /cases/{case_id}/questions` | Ordering is `question_order ASC, id ASC` | A questionnaire has an inherent sequence. Newest-first would scramble it. See `SPEC-AMD-007`. |
| `EXC-02` | Detail-response previews | Not paginated; bounded named objects instead | See section 4. |

---

## 4. Bounded previews

Detail responses must never embed a bare array that could be truncated, because a truncated array is indistinguishable from a complete one.

```text
"evidence_preview": {
  "items": [...],          // capped at 50
  "total_count": 213,
  "has_more": true
},
"activity_preview": {
  "items": [...],          // capped at 20
  "total_count": 88,
  "has_more": true
}
```

Full data is retrieved from:

```text
GET /questions/{question_id}/evidence
GET /cases/{case_id}/activity
```

### 4.1 New endpoint

```text
GET /cases/{case_id}/activity
  query: entity_type, entity_id, page, page_size
```

**Must enforce Case ownership.** An `entity_id` that does not belong to `case_id` returns `404` — never another Case's rows, and never an empty `200` that hides the boundary violation.

---

## 5. Idempotency and concurrency

### 5.1 Analyze endpoint

`Idempotency-Key` is **required** on `POST /questions/{question_id}/analyze`.

| Situation | Response |
|---|---|
| New key, no active job | **202 Accepted**, new job, `job_reused: false` |
| Same key, same payload, job in progress | **202 Accepted**, original job, `job_reused: true` |
| Same key, **different** payload | **409 `IDEMPOTENCY_KEY_REUSED`** |
| Different key, active job already exists for the question | **202 Accepted**, the existing active job, `job_reused: true` |

The response body indicates whether the job was reused. A client that cannot distinguish "I started this" from "this was already running" will double-count progress.

**Exactly one AI Run and exactly one provider call** may result, regardless of how many concurrent requests arrive.

### 5.2 Scope

Idempotency is scoped to the **operation and the Case**:

```text
UNIQUE (case_id, operation, idempotency_key)
```

A key is not global. The same key used for a different operation, or in a different Case, is a different request.

### 5.3 Concurrency guard

**The concurrency guard must be enforced by the database, not only by application code.**

At most one active `QUESTION_ANALYZE` job per question, enforced by a partial unique index:

```text
UNIQUE (question_id) WHERE job_type = 'QUESTION_ANALYZE'
                       AND status IN ('QUEUED', 'RUNNING')
```

Application-level checks lose races. An index does not.

### 5.4 Optimistic concurrency on mutations

Resources carry `version` (integer). Mutations require `If-Match` with the current ETag. A mismatch returns `409 VERSION_CONFLICT`.

---

## 6. Error codes

Added in v1.1.0:

| Code | HTTP | Meaning |
|---|---|---|
| `IDEMPOTENCY_KEY_REUSED` | 409 | Same key presented with a different payload |
| `INVALID_STATE_TRANSITION` | 409 | Job status transition not permitted by the lifecycle |
| `VERSION_CONFLICT` | 409 | `If-Match` did not match the current version |
| `UNSUPPORTED_EXPORT_COMBINATION` | 400 | `ExportType` and `ExportFormat` pair not in the allowed table |
| `ENUM_COMPATIBILITY_ERROR` | 400 | Unknown enum value received |

An earlier CTO proposal named the first code `IDEMPOTENCY_KEY_CONFLICT`. The ruled name is **`IDEMPOTENCY_KEY_REUSED`**.

The error envelope from v1.0.0 section 5 is unchanged.

---

## 7. Evidence Status

The evaluation model is defined in `SPEC-AMD-005` and the C-15 relevance rule in [`../decisions/CTO-RULINGS.md`](../decisions/CTO-RULINGS.md). Contract-relevant consequences:

- `evidence_status` is **computed by the server**. It is never accepted from a client and never emitted by the model.
- `status_findings` is a structured array preserving **every** detected condition, not only the winning one.
- `status_reason` is a human-readable summary of `status_findings`.
- `evidence_status_counts` has **7 keys**, not 8. There is no permanently-zero `AI_SUGGESTED` key.
- `draft_provenance_counts` is a separate map with 4 keys, and it is what drives the "AI Suggested" indicator.

---

## 8. Forbidden AI-owned fields

Contract section 8 deny-list, extended:

```text
review_status = HUMAN_CONFIRMED
final_compliance_status
audit_passed
certified
conflict_winner
customer_submission_approved
evidence_status                  <- added in v1.1.0
status_findings                  <- added in v1.1.0
```

Presence of any of these in a model response is a **validation failure**, not a field to strip and continue. Stripping teaches the pipeline that emitting them is harmless.

---

## 9. Contract tests added

Beyond the 10 tests in v1.0.0 section 12:

| ID | Asserts |
|---|---|
| `CT-011` | Every enum value in the contract has a matching `CHECK` constraint value, and vice versa |
| `CT-012` | Unknown enum value returns `ENUM_COMPATIBILITY_ERROR`, never a fallback |
| `CT-013` | Pagination bounds rejected, not clamped |
| `CT-014` | `GET /cases/{id}/questions` returns `question_order ASC, id ASC` across a fixture of more than 20 questions, spanning pages |
| `CT-015` | `evidence_preview.has_more` is true whenever `total_count` exceeds the cap |
| `CT-016` | `GET /cases/{id}/activity` returns 404 for an `entity_id` outside the Case |
| `CT-017` | Same idempotency key with a different payload returns 409 `IDEMPOTENCY_KEY_REUSED` |
| `CT-018` | Concurrent analyze requests produce exactly one AI Run and one provider call |
| `CT-019` | Invalid job transition returns 409 and leaves the row unmutated |
| `CT-020` | Disallowed ExportType/ExportFormat pair returns 400 listing allowed formats |
| `CT-021` | AI response containing `evidence_status` fails schema validation |
| `CT-022` | Model-supplied source location is ignored; server resolves from `chunk_id` |

---

## 10. Breaking-change assessment

| Change | Class |
|---|---|
| Job resource and endpoints | Additive |
| New enums | Additive |
| Pagination shape | Clarifying — no shape previously existed |
| Preview objects | Additive |
| Idempotency and concurrency rules | Clarifying — values were previously deferred |
| New error codes | Additive |
| `AI_SUGGESTED` removed from `EvidenceStatus` | **Would be breaking.** Recorded as a pre-implementation baseline correction; see `SPEC-AMD-006`. |

---

## 11. Approval

```text
CTO             APPROVED AS AMENDED      date: 2026-08-21
CEO             [ ] not obtained
COO             [ ] not obtained
FINAL           NO

Contract v1.1.0 is NOT FROZEN.
Contract v1.0.0 was never accepted and has zero implementations.
No client may implement against either version.
```
