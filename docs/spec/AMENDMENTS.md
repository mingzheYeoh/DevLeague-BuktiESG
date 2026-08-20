# Proposed Amendments to the Main Technical Spec

| Field | Value |
|---|---|
| Status | **PROPOSED** |
| Gate P0 | **BLOCKED** |
| Main Spec target | **v1.1 — NOT ACCEPTED** |
| Contract target | **v1.1.0 — NOT FROZEN** |
| Feature implementation | **NOT AUTHORIZED** |
| Amendments recorded | `SPEC-AMD-001` … `SPEC-AMD-008` |
| Applied to the Main Spec body | **None.** All eight are proposals. |

**None of these amendments has been applied to `BuktiESG-Technical-Spec-EN.md`.** That document remains v1.0. Main Spec v1.1 comes into existence only when every amendment below carries the signatures its row requires.

Approval requirement: Main Spec and Contract change control requires **CEO + CTO + COO**. Amendments that change what a fixture is expected to produce additionally require the **Ground-Truth Approver**.

---

## Signature Legend

| Mark | Meaning |
|---|---|
| `CTO` | CTO ruling recorded. Binding within CTO authority only. Not a final approval. |
| `[ ]` | Signature **not** obtained. |
| `n/a` | This role's signature is not required for this amendment. |

---

## Summary

| ID | Change | Main Spec sections | CTO | CEO | COO | Ground Truth | FINAL |
|---|---|---|---|---|---|---|---|
| `SPEC-AMD-001` | Add `processing_jobs` entity and `documents.latest_job_id` | 10.1, 11 | APPROVED | `[ ]` | `[ ]` | n/a | **NO** |
| `SPEC-AMD-002` | Add `extraction_method` and `extraction_confidence` to `evidence_links` | 10.1 | APPROVED | `[ ]` | `[ ]` | n/a | **NO** |
| `SPEC-AMD-003` | AI result schema becomes a compatible superset; no field removed | 12.5 | APPROVED AS AMENDED | `[ ]` | `[ ]` | n/a | **NO** |
| `SPEC-AMD-004` | Map Sub-Spec ownership paths into the section 16 repository tree | 16 | APPROVED | `[ ]` | `[ ]` | n/a | **NO** |
| `SPEC-AMD-005` | Evidence Status evaluation model | 6.2 | APPROVED AS AMENDED | `[ ]` | `[ ]` | `[ ]` | **NO** |
| `SPEC-AMD-006` | Three-dimension model; `DraftProvenance`; `AI_SUGGESTED` removed from EvidenceStatus | 5.2, 5.4, 6.1, 6.2, REQ-025, 10.1 | APPROVED AS AMENDED | `[ ]` | `[ ]` | `[ ]` | **NO** |
| `SPEC-AMD-007` | Add `questions.question_order` (integer) | 10.1, 11 | APPROVED | `[ ]` | `[ ]` | `[ ]` | **NO** |
| `SPEC-AMD-008` | Add `GET /cases/{case_id}/activity` | 11 | APPROVED | `[ ]` | `[ ]` | n/a | **NO** |

**0 of 8 amendments are FINAL.**

---

## SPEC-AMD-001 — Processing Job resource

**Category:** Additive. Non-breaking.
**Affects:** Main Spec 10.1 (data model), 11 (API); Contract 6, 7.

### Problem

Shared Integration Contract v1.0.0 declares `GET /api/v1/jobs/{job_id}` but defines no Job resource, no schema, no enum, no lifecycle, and no owning role. Worse, **no client can obtain a `job_id` after a page refresh**, because nothing on the Document links to its job. The endpoint is unreachable as specified.

### Change

Add a `processing_jobs` entity:

```text
id                opaque string
case_id           FK, NOT NULL
job_type          text, CHECK in JobType
status            text, CHECK in JobStatus
document_id       FK, nullable
question_id       FK, nullable
idempotency_key   text, nullable
attempt_count     integer, NOT NULL, default 0
lease_expires_at  timestamptz, nullable
error_code        text, nullable
error_message     text, nullable
created_at        timestamptz, NOT NULL
started_at        timestamptz, nullable
finished_at       timestamptz, nullable
```

Add `documents.latest_job_id` (FK, nullable) so a refreshed client can reach the job.

### Lifecycle

```text
QUEUED   -> RUNNING   -> SUCCEEDED
QUEUED   -> RUNNING   -> FAILED
QUEUED   -> CANCELLED
RUNNING  -> CANCELLED
```

Terminal states are `SUCCEEDED`, `FAILED`, `CANCELLED`. An invalid transition returns `409 INVALID_STATE_TRANSITION` and must not mutate the row.

### Owner

CTO.

### Approval

```text
CTO             APPROVED                 date: 2026-08-21
CEO             [ ] not obtained
COO             [ ] not obtained
Ground Truth    n/a
FINAL           NO
```

---

## SPEC-AMD-002 — Evidence extraction provenance

**Category:** Additive. Non-breaking.
**Affects:** Main Spec 10.1 `evidence_links`.

### Problem

Main Spec 6.3 and Contract 7.4 both require `extraction_method` and `extraction_confidence` on evidence, but Main Spec 10.1 `evidence_links` omits both fields. The response shape cannot be produced from the persisted model.

### Change

Add to `evidence_links`:

```text
extraction_method      text, CHECK in ExtractionMethod, NOT NULL
extraction_confidence  numeric(4,3), nullable, range 0.000 to 1.000
```

`extraction_confidence` is nullable because a deterministic extraction path has no meaningful confidence value. A null must never be coerced to `1.000` — that would silently promote "we did not measure" into "we are certain".

### Owner

CTO, with COO confirmation of the `ExtractionMethod` value set.

### Approval

```text
CTO             APPROVED                 date: 2026-08-21
CEO             [ ] not obtained
COO             [ ] not obtained
Ground Truth    n/a
FINAL           NO
```

---

## SPEC-AMD-003 — AI result schema as a compatible superset

**Category:** Clarifying and additive. Non-breaking. **No field is removed.**
**Affects:** Main Spec 12.5; Contract 8.

### Problem

Main Spec 12.5 and Contract 8 define different field sets for the AI analysis result. A field-by-field diff found **6 shared top-level fields, 4 added by Contract 8, and 0 removed**. All 8 `candidate_evidence` item fields are identical. Two genuine conflicts exist:

1. `question_id` and `chunk_id` are UUID-format-validated in one document and opaque strings in the other. Contract rule 1 states all IDs are opaque strings and clients must not infer meaning from them.
2. `suggested_follow_up` is non-nullable in one document and nullable in the other.

### Correction to an earlier CTO position

An earlier CTO analysis concluded that "the smaller Contract section 8 schema legally wins today." **That conclusion was rejected and is not the ruling.** Under the authority order, **Main Spec 12.5 remains authoritative** unless an approved decision explicitly versions and amends the Main Spec. This amendment is that explicit amendment.

### Change

Amend Main Spec 12.5 to the **union** of both field sets. Remove nothing. Then:

- IDs are opaque strings. Do **not** apply UUID format validation at the schema layer.
- `suggested_follow_up` is nullable.
- The schema is strict: `additionalProperties: false`.
- The model **must not** emit `evidence_status`, `status_findings`, `review_status`, or any field in the forbidden list. Presence of any such field is a validation failure, not a field to ignore.
- **The model never supplies a source location.** It returns `chunk_id`. The server resolves the source location from `document_chunks`. A hallucinated citation cannot resolve and therefore cannot be persisted — the impossibility is structural, not probabilistic.

### Owner

CTO for the schema; COO for the pipeline that must satisfy it.

### Approval

```text
CTO             APPROVED AS AMENDED      date: 2026-08-21
CEO             [ ] not obtained
COO             [ ] not obtained
Ground Truth    n/a
FINAL           NO
```

---

## SPEC-AMD-004 — Repository path reconciliation

**Category:** Editorial. Non-breaking.
**Affects:** Main Spec 16; all three Role Sub-Specs section 5.

### Problem

The Role Sub-Specs name ownership paths such as `database/`, `storage/`, `export/`, and `ai/` that do not exist in the Main Spec section 16 repository tree. Implemented literally this produces duplicate top-level trees and two competing layouts.

### Change

Map every Sub-Spec ownership path onto the existing section 16 tree. **Create no duplicate top-level trees.** The section 16 tree is the single layout; Sub-Spec paths are expressed as subpaths within it.

### Owner

CTO.

### Approval

```text
CTO             APPROVED                 date: 2026-08-21
CEO             [ ] not obtained
COO             [ ] not obtained
Ground Truth    n/a
FINAL           NO
```

---

## SPEC-AMD-005 — Evidence Status evaluation model

**Category:** Behavioural. Changes what fixtures are expected to produce.
**Affects:** Main Spec 6.2; Contract 13.
**Requires the Ground-Truth Approver.**

### Problem

Main Spec 6.2 defines eight statuses independently, with **no rule for what happens when more than one condition is true at once**. A document that is simultaneously outdated and contradicted by another document has no defined status.

### Change

**Frozen precedence** among evidence-quality outcomes:

```text
CONFLICTING > OUTDATED > PARTIAL > VERIFIED
```

Lower-priority findings are **never discarded.** Every detected condition is preserved in structured `status_findings` and summarized in `status_reason`. `VERIFIED` is permitted only when no blocking condition remains.

**Four-step evaluation:**

```text
1. NOT_APPLICABLE
   Human-controlled only. Requires a reason and a reviewer identity.
   Survives recalculation unless a human reopens the question.
   The rule engine may never set or clear it.

2. Exclude unreadable or extraction-invalid evidence
   from the evidence-quality computation entirely.

3. Evaluate the remaining readable evidence using the frozen precedence.
   If it yields CONFLICTING, OUTDATED, PARTIAL, or VERIFIED, that is the result.

4. Otherwise:
     NEEDS_MANUAL_REVIEW  if a relevant unreadable document may materially
                          affect the answer, per the C-15 relevance rule
     MISSING              otherwise
```

**Two rules that constrain step 2 and are easy to get wrong:**

- An unreadable candidate **must not suppress** a genuine conflict found between two other reliable sources.
- Unreadable OCR output **must never create** a conflict.

An earlier CTO proposal made `NEEDS_MANUAL_REVIEW` an unconditional rank-2 override. **That proposal was rejected.** Under it, a single unreadable scan anywhere in a Case would have masked every real conflict in it.

The relevance test in step 4 is defined by the **C-15 ruling** in [`../decisions/CTO-RULINGS.md`](../decisions/CTO-RULINGS.md).

### Ground-truth impact

Every fixture's expected status may change. The Ground-Truth Approver must sign before ground truth is frozen.

### Owner

CTO for the engine; CEO for product meaning; COO for the extraction signals it consumes; Ground-Truth Approver for expected values.

### Approval

```text
CTO             APPROVED AS AMENDED      date: 2026-08-21
CEO             [ ] not obtained
COO             [ ] not obtained
Ground Truth    [ ] not obtained
FINAL           NO
```

---

## SPEC-AMD-006 — Three-dimension model and DraftProvenance

**Category:** Behavioural, and **removes an enum value from a never-implemented baseline**.
**Affects:** Main Spec 5.2, 5.4, 6.1, 6.2, **REQ-025**, 10.1 `answers`; Contract 3.4, 3.15, 7.1, 7.3, 7.6, 9.
**Requires the Ground-Truth Approver.**

### Problem

Main Spec 18.2 states the GHG fixture produces `MISSING`. Main Spec 20 shows the demo displaying an "AI Suggested GHG answer". These read as contradictory only because `AI_SUGGESTED` was placed inside the Evidence Status enum, where it competes with `MISSING` for one slot.

**They are not in conflict. They describe different dimensions.** `MISSING` describes **evidence availability**. `AI_SUGGESTED` described **draft provenance and human-review state**. An earlier CTO attempt to resolve this by precedence ranking was rejected on exactly this ground: it is not a precedence contest.

### Change

Model three **independent** dimensions:

| Dimension | Field | Meaning |
|---|---|---|
| Evidence availability and quality | `evidence_status` | What the evidence supports. Computed by the rule engine. |
| Draft provenance | `draft_provenance` | Where the draft text came from. |
| Human review state | `review_status`, `human_confirmed` | Whether a human has confirmed it. |

**`AI_SUGGESTED` is removed from `EvidenceStatus`,** which drops from 8 values to 7.

New enum:

```text
DraftProvenance: NONE | AI_GENERATED | AI_ASSISTED_EDIT | USER_ENTERED
```

Invariant:

```text
draft_provenance IN (AI_GENERATED, AI_ASSISTED_EDIT)  ->  ai_run_id IS NOT NULL
```

An earlier proposal used the biconditional `draft_provenance = AI_GENERATED` if and only if `ai_run_id IS NOT NULL`. **That was rejected**: it contradicts retaining `ai_run_id` after a human edits an AI draft. The one-directional implication above is the correct form, and `AI_ASSISTED_EDIT` is the value that makes the edited case representable.

The purple "AI Suggested" UI indicator is driven by `draft_provenance_counts`, **not** by a permanently-zero `AI_SUGGESTED` key in `evidence_status_counts`.

### The GHG scenario, stated exactly

```text
evidence_status         = MISSING
draft_answer            = populated by AI
ai_run_id               = present
draft_provenance        = AI_GENERATED
review_status           = UNREVIEWED
human_confirmed         = false
counts_toward_readiness = false
```

The UI may display an "AI Suggested" label, **but it must also display that the supporting evidence is MISSING.** Protected ground truth continues to expect `MISSING`. The demo may show an AI-generated draft but must never represent that draft as evidence.

### Note on removing an enum value

Removing `AI_SUGGESTED` would normally be a breaking change requiring a major version under Contract section 13. It is recorded here as a **pre-implementation baseline correction**: Contract v1.0.0 status is `planned`, it was never accepted, and there are zero implementations and zero clients. This rationale is committed so the exception is auditable and does not silently become precedent. Once v1.1.0 is frozen, normal versioning applies without exception.

### Ground-truth impact

Fixtures gain an `expected_draft_provenance` field. The Ground-Truth Approver must sign.

### Approval

```text
CTO             APPROVED AS AMENDED      date: 2026-08-21
CEO             [ ] not obtained
COO             [ ] not obtained
Ground Truth    [ ] not obtained
FINAL           NO
```

---

## SPEC-AMD-007 — Deterministic questionnaire ordering

**Category:** Additive to the data model. Changes an expected fixture value.
**Affects:** Main Spec 10.1 `questions`, 11; Contract 6.1, 7.3.
**Requires the Ground-Truth Approver.**

### Problem

The questions list has no defined ordering. An earlier CTO proposal ordered by `section ASC, source_location ASC, external_question_id ASC, id ASC`. **That was rejected.** Those are display identifiers, not sequence, and **lexical sorting places row 10 before row 2, and `Q-10` before `Q-2`** — which breaks precisely the questionnaires large enough to paginate.

### Change

Add a persisted column:

```text
question_order  integer, NOT NULL
```

Assigned deterministically during import, from workbook order, then sheet order, then row order. The true sequence is known exactly once — at traversal time — so it is captured there and never re-derived from display strings.

Default ordering becomes:

```text
GET /cases/{case_id}/questions  ->  ORDER BY question_order ASC, id ASC
```

A fixture with **more than 20 questions** is required, so cross-page ordering is actually exercised rather than assumed.

### Ground-truth impact

Fixtures gain `expected_question_order`.

### Approval

```text
CTO             APPROVED                 date: 2026-08-21
CEO             [ ] not obtained
COO             [ ] not obtained
Ground Truth    [ ] not obtained
FINAL           NO
```

---

## SPEC-AMD-008 — Case activity endpoint

**Category:** Additive. Non-breaking.
**Affects:** Main Spec 11; Contract 6, 6.1, 7.6.

### Problem

Detail responses embed unbounded arrays of evidence and activity. A silently truncated array is indistinguishable from a complete one, so a client cannot tell whether it has all the data. There is also no endpoint from which the full activity history can be fetched.

### Change

Detail responses carry **named preview objects**, never bare arrays:

```text
evidence_preview: { items: [...], total_count: int, has_more: bool }   # items capped at 50
activity_preview: { items: [...], total_count: int, has_more: bool }   # items capped at 20
```

Add the endpoint that makes the preview honest:

```text
GET /cases/{case_id}/activity
  query: entity_type, entity_id, page, page_size
```

It **must enforce Case ownership**: a caller must not read activity for an entity outside the named Case, and a mismatched `entity_id` returns `404`, never another Case's rows.

### Approval

```text
CTO             APPROVED                 date: 2026-08-21
CEO             [ ] not obtained
COO             [ ] not obtained
Ground Truth    n/a
FINAL           NO
```

---

## Status

**0 of 8 amendments are FINAL. Main Spec v1.1 does not exist. Gate P0 is BLOCKED.**
