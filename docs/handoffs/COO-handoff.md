# COO Decision Packet

| Field | Value |
|---|---|
| Status | **PROPOSED** |
| Gate P0 | **BLOCKED** |
| Main Spec target | **v1.1 — NOT ACCEPTED** |
| Contract target | **v1.1.0 — NOT FROZEN** |
| Feature implementation | **NOT AUTHORIZED** |
| From | CTO — Backend & Integration Lead (`mingzheYeoh`) |
| To | COO — AI & ESG Operations Lead |
| Role owner | **UNASSIGNED — workstream not started** |
| Packet state | **NOT RECEIVED** |
| Decisions in this packet | **27** |
| Decisions recorded | **0** |
| Date issued | 2026-08-21 |

---

## Nothing in this document has been approved

**Every decision below is `PENDING`.**

No decision has been inferred, simulated, assumed, defaulted, or recorded on the COO's behalf. A "CTO recommendation" column exists so the role owner can respond quickly — it is **advice, not a pre-filled answer**, and it carries no approval weight whatsoever.

The COO workstream has not started. This packet exists so that when a role owner is assigned, every decision and input they own is already in one place.

---

## How to respond

For each decision ID, reply with exactly one of:

```text
APPROVE   accept the CTO recommendation as written
AMEND     accept with changes  (state the change)
REJECT    do not accept        (state what to do instead)
```

Section C items are **not** approvals — they are technical inputs only the COO can supply. Reply with the value, or `NOT YET` if it is not ready.

**Any ID left unanswered stays `PENDING`.**

---

## Section A — Boundary and configuration

### `COO-D01` — Pure processing core (`BLOCKER-04`) — **PENDING**

This is the load-bearing architectural decision for the AI workstream.

```text
CTO orchestration layer          COO processing core
--------------------------       --------------------------
loads the job and the file  -->  pure function
                                 NO database session
                                 NO direct persistence
                                 NO provider-specific business logic
                                 NO write path around schema validation
validates the result       <--   returns a plain result
persists it
```

Two consequences worth being explicit about:

- **The entire pipeline can be developed and tested with fixtures, without a running backend or database.** That is the point — it removes the dependency that would otherwise serialize the AI workstream behind the API.
- It makes it **structurally impossible** for the pipeline to write a status the rule engine did not compute. Not discouraged — impossible, because no write path exists to reach.

### `COO-D02` — Provider configuration (`BLOCKER-08`) — **PENDING**

```text
provider        = anthropic
model           = claude-sonnet-5
CI provider     = FixtureProvider     (also the outage fallback)
warning budget  = USD 1.60 per Case
hard budget     = USD 2.00 per Case
```

Pricing snapshot **2026-08-21**: input USD 2 per million tokens, output USD 10 per million.

```text
estimated_cost = (input_tokens / 1_000_000 * 2) + (output_tokens / 1_000_000 * 10)
```

Computed from **actual API usage**, never from an estimate. The pricing version and date are stored per AI Run, so a later price change never rewrites the recorded cost of past runs.

Additional rules:

- Use **structured output**.
- **Do not set non-default `temperature`, `top_p`, or `top_k`.** Determinism comes from the rule engine, not from sampling parameters. Tuning them creates the appearance of control without the substance, and makes results harder to reproduce rather than easier.
- **Never use the live provider in CI.** A test that costs money is a test that gets skipped.
- Reaching the hard budget **stops automatic processing** and requires explicit human approval.

---

## Section B — Co-approval of the specification and contract change set

Change control requires **CEO + CTO + COO**. The CTO position is recorded. **Yours is PENDING on every line.**

| ID | Item | CTO position | Status |
|---|---|---|---|
| `COO-D03` | `BLOCKER-01` — English Main Spec normative; Chinese non-normative | RULED | **PENDING** |
| `COO-D04` | `BLOCKER-02` — map ownership paths into section 16 | RULED | **PENDING** |
| `COO-D05` | `BLOCKER-06` — keyword-first retrieval; pgvector installed but unused | RULED | **PENDING** |
| `COO-D06` | `RULING-01` — Job and Export concepts; Contract v1.1.0; four enums | AMEND | **PENDING** |
| `COO-D07` | `RULING-02` — Evidence Status evaluation model | AMEND | **PENDING** |
| `COO-D08` | `RULING-03` — `AI_SUGGESTED` removed; `DraftProvenance` added | AMEND | **PENDING** |
| `COO-D09` | `RULING-04` — persisted `question_order` | AMEND | **PENDING** |
| `COO-D10` | `RULING-05` — named previews and the activity endpoint | APPROVE | **PENDING** |
| `COO-D11` | `RULING-06` — idempotency and database-enforced concurrency | APPROVE | **PENDING** |
| `COO-D12` | `RULING-07` — amendments recorded individually; Main Spec v1.1 | APPROVE | **PENDING** |
| `COO-D13` | `C-15` — deterministic unreadable-document relevance rule | RULED | **PENDING** |
| `COO-D14` | `SPEC-AMD-001` — `processing_jobs` and `documents.latest_job_id` | APPROVED | **PENDING** |
| `COO-D15` | `SPEC-AMD-002` — evidence extraction provenance fields | APPROVED | **PENDING** |
| `COO-D16` | `SPEC-AMD-003` — AI schema as a compatible superset | APPROVED AS AMENDED | **PENDING** |
| `COO-D17` | `SPEC-AMD-004` — repository path reconciliation | APPROVED | **PENDING** |
| `COO-D18` | `SPEC-AMD-005` — Evidence Status evaluation model | APPROVED AS AMENDED | **PENDING** |
| `COO-D19` | `SPEC-AMD-006` — three-dimension model and `DraftProvenance` | APPROVED AS AMENDED | **PENDING** |
| `COO-D20` | `SPEC-AMD-007` — `questions.question_order` | APPROVED | **PENDING** |

`SPEC-AMD-008` is API-only and does not require a COO signature.

### The three items that most affect the pipeline

**`COO-D16` / `SPEC-AMD-003` — AI result schema.** The schema becomes the **union** of Main Spec 12.5 and Contract 8. No field is removed. Then:

- IDs are **opaque strings**. No UUID format validation at the schema layer.
- `suggested_follow_up` is **nullable**.
- The schema is strict: `additionalProperties: false`.
- The model must **not** emit `evidence_status`, `status_findings`, `review_status`, or any forbidden field. Presence is a **validation failure**, not a field the server strips and continues past — stripping would teach the pipeline that emitting it is harmless.
- **The model never supplies a source location.** It returns `chunk_id`; the server resolves the location from `document_chunks`.

That last rule changes what the pipeline needs to guarantee, and in the pipeline's favour. A citation the model invented **cannot resolve**, so it cannot be persisted. Hallucinated provenance becomes structurally impossible rather than something a prompt has to prevent. The pipeline does not need to be *trusted* on citations — a considerably easier bar than being *trustworthy* on them.

**`COO-D08` / `RULING-03` — three dimensions.** `AI_SUGGESTED` is removed from `EvidenceStatus`. The pipeline emits `draft_provenance`, never an evidence status:

```text
DraftProvenance: NONE | AI_GENERATED | AI_ASSISTED_EDIT | USER_ENTERED
```

**`COO-D07` / `COO-D13` — evidence evaluation.** Two rules constrain what the extraction signals must support:

- An unreadable candidate **must not suppress** a genuine conflict between two other reliable sources.
- Unreadable OCR output **must never create** a conflict.

---

## Section C — Technical inputs only the COO can supply

**This section is the real blocker.** Three of these make an otherwise-approved ruling unimplementable.

| ID | Input | Blocks | Status |
|---|---|---|---|
| `COO-D21` | C-15 relevance signals | `SPEC-AMD-005` final signature; Phase 4 | **PENDING** |
| `COO-D22` | Parser and OCR failure-code catalog | REQ-005; `TEST-E2E-007` | **PENDING** |
| `COO-D23` | `document_chunks` field shape | Retrieval layer; server-side location resolution | **PENDING** |
| `COO-D24` | `ExtractionMethod` enum values | `SPEC-AMD-002` | **PENDING** |
| `COO-D25` | Deterministic AI fixtures | All AI-dependent CI tests | **PENDING** |

### `COO-D21` — C-15 relevance signals

The `C-15` rule determines when an unreadable document routes a question to `NEEDS_MANUAL_REVIEW` rather than `MISSING`. It depends **only on signals that survive extraction failure** — which is what makes it evaluable at all, given that the document's body text is precisely what could not be read:

```text
An unreadable document may materially affect a question only when ALL hold:

1. Its processing status is NEEDS_MANUAL_REVIEW.
2. Its document_type is in the question's
   evidence_requirement_json.accepted_document_types.
3. At least one normalized required keyword from
   evidence_requirement_json.keywords EXACTLY matches a token in:
     - original_filename, or
     - successfully extracted document metadata or heading text.

Normalization: Unicode normalization, case-insensitive, punctuation to
spaces, whitespace collapsed, exact token matching only.
NO embedding similarity. NO LLM classification. NO fuzzy matching.
```

**Required from the COO:**

| Input | Why |
|---|---|
| The `document_type` value set and its SEDG topic mapping | Condition 2 cannot be evaluated without it |
| The source and shape of `evidence_requirement_json.keywords` | Condition 3 cannot be evaluated without it |
| Which metadata and heading fields survive a failed extraction | Condition 3 names them but cannot assume they exist |

The prohibition on fuzzy and embedding matching is deliberate: a similarity threshold is a number that can be quietly tuned until a failing test passes. Exact token matching has no threshold, so the rule engine's output is reproducible from the fixture alone.

### `COO-D22` — Failure-code catalog

Parser and OCR failure codes, **each marked retryable or terminal**. The orchestration layer cannot decide whether to retry without this, and defaulting to retry on a terminal failure burns the provider budget on work that can never succeed.

### `COO-D24` — `ExtractionMethod` values

Note that `extraction_confidence` is **nullable** by design, because a deterministic extraction path has no meaningful confidence value. A null must never be coerced to `1.000` — that would silently promote "we did not measure" into "we are certain".

### `COO-D25` — Deterministic AI fixtures

CI must never call the live provider, so every AI-dependent test needs a fixture.

| Fixture | Purpose |
|---|---|
| `ai_response_valid.json` | A schema-valid result |
| `ai_response_forbidden_field.json` | Contains `evidence_status`; must fail `CT-021` |
| `ai_response_fabricated_location.json` | Contains an invented source location; must fail `CT-022` |
| `prompt_injection.pdf` | Document text attempting to instruct the model; asserts TB-3 |
| `unreadable_scan.pdf` | OCR produces invalid output |
| `conflicting_pair/` | Two reliable sources that genuinely disagree |
| `questionnaire_25plus.xlsx` | More than 20 questions, for `CT-014` |

`questionnaire_25plus.xlsx` must exceed one page. A 20-question fixture at `page_size = 20` would pass `CT-014` while cross-page ordering is broken.

---

## Section D — Ground-truth impact to confirm

| ID | Item | Status |
|---|---|---|
| `COO-D26` | Confirm the ground-truth impact below | **PENDING** |

The COO prepares ground truth; a **non-implementer** approves it. The Ground-Truth Approver **must not be the COO**.

| Change | Effect |
|---|---|
| GHG fixture | Stays `MISSING`, plus `draft_provenance = AI_GENERATED` |
| Management declaration | Also becomes `MISSING`, with a finding recording that a declaration exists but carries no supporting record |
| All fixtures | Gain `expected_draft_provenance` |
| All fixtures | Gain `expected_question_order` |
| Multi-condition fixtures | Gain `status_findings` recording **every** detected condition, not only the winning one |

The management-declaration case is worth confirming explicitly. A signed declaration is a **claim**, not a record. Under the product's own thesis it cannot support `VERIFIED` on its own — but the finding must say *why*, or a reviewer will read `MISSING` as "we found nothing" when in fact something was found and judged insufficient.

**Confirm before ground truth is frozen at Phase 3.**

---

## Section E — Identity and acknowledgement

| ID | Item | Status |
|---|---|---|
| `COO-D27` | Supply `COO_GITHUB_HANDLE` and the written synthetic-data acknowledgement | **PENDING** |

```text
COO_GITHUB_HANDLE = PENDING
```

Written synthetic-data-only acknowledgement: **NOT RECORDED**. Required from CEO, CTO, and COO. Zero of three recorded.

---

## What happens after this packet is returned

```text
CEO packet + COO packet + Ground-Truth packet
        -> decision register updated with the recorded answers
        -> Main Spec v1.1 and Contract v1.1.0 would then be frozen
        -> Gate P0 could then be accepted
        -> Phase 1 authorized
```

**Nothing in Phase 1 starts before all three packets arrive.**

---

## Reference

- [`../decisions/decision-register.md`](../decisions/decision-register.md) — full register; section 6.2 itemizes this packet
- [`../decisions/CTO-RULINGS.md`](../decisions/CTO-RULINGS.md) — full ruling text including `C-15`
- [`../spec/AMENDMENTS.md`](../spec/AMENDMENTS.md) — the eight amendments with signature blocks
- [`../spec/contract-test-plan.md`](../spec/contract-test-plan.md) — fixtures required
- [`../spec/BuktiESG-Technical-Spec-EN.md`](../spec/BuktiESG-Technical-Spec-EN.md) — normative Main Spec (v1.0 body)
- [`../decisions/GATE-P0-APPROVAL.md`](../decisions/GATE-P0-APPROVAL.md) — **UNSIGNED**

---

**27 decisions. 27 PENDING. 0 recorded. Gate P0 is BLOCKED.**
