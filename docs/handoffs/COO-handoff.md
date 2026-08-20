# COO Handoff — Decisions and Inputs Required

| Field | Value |
|---|---|
| Status | **PROPOSED** |
| Gate P0 | **BLOCKED** |
| Main Spec target | **v1.1 — NOT ACCEPTED** |
| Contract target | **v1.1.0 — NOT FROZEN** |
| Feature implementation | **NOT AUTHORIZED** |
| From | CTO — Backend & Integration Lead |
| To | COO — AI & ESG Operations Lead |
| Date | 2026-08-21 |

---

## Summary

The CTO has ruled on everything within CTO authority. Gate P0 waits on one consolidated packet from you, one from the CEO, and one from a Ground-Truth Approver who has not been named.

Your packet has two halves: **decisions to confirm** (sections A and B) and **technical inputs only you can supply** (section C). Section C is the larger blocker — three of those items make otherwise-approved rulings unimplementable.

---

## A. Boundary and configuration

### A1. Pure processing core — `BLOCKER-04`

This is the load-bearing architectural decision for your workstream.

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

- **You can develop and test the entire pipeline with fixtures, without a running backend or database.** That is the point — it removes the dependency that would otherwise serialize your work behind the API.
- It makes it **structurally impossible** for the pipeline to write a status the rule engine did not compute. Not discouraged — impossible, because there is no write path to reach.

**Your call:** `APPROVE` / `AMEND` / `REJECT`

### A2. Provider configuration — `BLOCKER-08`

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

**Your call:** `APPROVE` / `AMEND` / `REJECT`

---

## B. Co-approval of the specification and contract change set

Change control requires **CEO + CTO + COO**.

| Item | CTO | Your call |
|---|---|---|
| `BLOCKER-01` — English normative | RULED | |
| `BLOCKER-02` — map paths into section 16 | RULED | |
| `BLOCKER-06` — keyword-first retrieval | RULED | |
| `RULING-01` … `RULING-07` | ruled | one call each |
| `SPEC-AMD-001` … `SPEC-AMD-007` | ruled | one call each |
| `C-15` — relevance rule | RULED | |

`SPEC-AMD-008` is API-only and does not require your signature.

### The three that most affect your pipeline

**`SPEC-AMD-003` — AI result schema.** The schema becomes the **union** of Main Spec 12.5 and Contract 8. No field is removed. Then:

- IDs are **opaque strings**. No UUID format validation at the schema layer.
- `suggested_follow_up` is **nullable**.
- The schema is strict: `additionalProperties: false`.
- The model must **not** emit `evidence_status`, `status_findings`, `review_status`, or any forbidden field. Presence is a **validation failure**, not a field the server strips and continues past — stripping would teach the pipeline that emitting it is harmless.
- **The model never supplies a source location.** It returns `chunk_id`; the server resolves the location from `document_chunks`.

That last rule is worth dwelling on, because it changes what your pipeline needs to guarantee. A citation the model invented **cannot resolve**, so it cannot be persisted. Hallucinated provenance becomes structurally impossible rather than something your prompt has to prevent. Your pipeline does not need to be trusted on citations — which is a considerably easier bar than being trustworthy on them.

**`RULING-03` — three dimensions.** `AI_SUGGESTED` is removed from `EvidenceStatus`. Your pipeline emits `draft_provenance`, never an evidence status:

```text
DraftProvenance: NONE | AI_GENERATED | AI_ASSISTED_EDIT | USER_ENTERED
```

**`RULING-02` and `C-15` — evidence evaluation.** Two rules constrain what your extraction signals must support:

- An unreadable candidate **must not suppress** a genuine conflict between two other reliable sources.
- Unreadable OCR output **must never create** a conflict.

---

## C. Technical inputs only you can supply

**This section is the real blocker.** Three of these items make an otherwise-approved ruling unimplementable.

### C1. C-15 relevance signals — blocks `SPEC-AMD-005` and Phase 4

The `C-15` rule determines when an unreadable document routes a question to `NEEDS_MANUAL_REVIEW` rather than `MISSING`. It depends only on signals that **survive extraction failure**:

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

**What is needed from you:**

| Input | Why |
|---|---|
| The `document_type` value set and its SEDG topic mapping | Condition 2 cannot be evaluated without it |
| The source and shape of `evidence_requirement_json.keywords` | Condition 3 cannot be evaluated without it |
| Which metadata and heading fields survive a failed extraction | Condition 3 names them but cannot assume they exist |

The prohibition on fuzzy and embedding matching is deliberate and worth understanding: a similarity threshold is a number that can be quietly tuned until a failing test passes. Exact token matching has no threshold, so the rule engine's output is reproducible from the fixture alone.

### C2. Failure-code catalog — blocks REQ-005 and `TEST-E2E-007`

Parser and OCR failure codes, **each marked retryable or terminal**. The orchestration layer cannot decide whether to retry without this, and defaulting to retry on a terminal failure burns the provider budget on work that can never succeed.

### C3. `document_chunks` field shape

Needed before the retrieval layer or `SPEC-AMD-003`'s server-side location resolution can be built.

### C4. `ExtractionMethod` enum values — `SPEC-AMD-002`

Note that `extraction_confidence` is **nullable** by design, because a deterministic extraction path has no meaningful confidence value. A null must never be coerced to `1.000` — that would silently promote "we did not measure" into "we are certain".

### C5. Deterministic AI fixtures

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

## D. Ground-truth impact to confirm

You prepare ground truth; a **non-implementer** approves it. The Ground-Truth Approver **must not be you**.

| Change | Effect |
|---|---|
| GHG fixture | Stays `MISSING`, plus `draft_provenance = AI_GENERATED` |
| Management declaration | Also becomes `MISSING`, with a finding recording that a declaration exists but carries no supporting record |
| All fixtures | Gain `expected_draft_provenance` |
| All fixtures | Gain `expected_question_order` |
| Multi-condition fixtures | Gain `status_findings` recording **every** detected condition, not only the winning one |

The management declaration case is worth confirming explicitly. A signed declaration is a claim, not a record. Under the product's own thesis it cannot support `VERIFIED` on its own — but the finding must say *why*, or a reviewer will read `MISSING` as "we found nothing" when in fact something was found and judged insufficient.

**Confirm before ground truth is frozen at Phase 3.**

---

## E. Identity and acknowledgement

```text
COO_GITHUB_HANDLE = PENDING
```

Written synthetic-data-only acknowledgement: **NOT RECORDED**.

---

## Reference

- [`../decisions/decision-register.md`](../decisions/decision-register.md) — section 6.2 itemizes your packet
- [`../decisions/CTO-RULINGS.md`](../decisions/CTO-RULINGS.md) — full ruling text including `C-15`
- [`../spec/AMENDMENTS.md`](../spec/AMENDMENTS.md) — the eight amendments
- [`../spec/contract-test-plan.md`](../spec/contract-test-plan.md) — fixtures required
- [`../decisions/GATE-P0-APPROVAL.md`](../decisions/GATE-P0-APPROVAL.md) — **unsigned**

**Gate P0 is BLOCKED.**
