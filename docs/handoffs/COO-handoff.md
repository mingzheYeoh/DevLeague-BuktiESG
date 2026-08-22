# COO Decision Packet

> **2026-08-22 note (COO agent):** This file was restored (uncommitted, working-tree only) from pre-delete commit `4fa92d4` after an unexplained upstream deletion commit `14bdf33` on `main` today (authored `mingzheYeoh`). Restoration is a **draft to re-validate, not settled fact**. Deletion confirmed intentional in a live session on 2026-08-22 by COO Lai Yoke Yau (new documentation approach per `mingzheYeoh`) — not yet a written confirmation from `mingzheYeoh` himself. Restoration content below proceeds on that basis. Content was checked for internal consistency against the current `AGENTS.md` and `docs/spec/BuktiESG-Technical-Spec-EN.md`; no contradictions were found.
>
> **2026-08-22, later same day — recorded decisions added:** The real human COO, Lai Yoke Yau (`kaneki016`), acting directly in this live session, authorized (a) recording `COO-D01`–`COO-D20` and `COO-D27` as `APPROVE`, and (b) adopting the COO agent's prior draft recommendations for `COO-D21`, `COO-D22`, `COO-D24`, and `COO-D25` as the recorded COO decision. This **supersedes and re-establishes** an earlier approval session whose edits never made it into git history (per the CTO/COO note above, that prior session's file changes were lost to the unexplained `14bdf33` deletion before being committed). This new recording is a fresh act, dated 2026-08-22, not a recovery of the lost session's content. `COO-D26` (ground-truth impact) is recorded as the COO's **preparer input only**, adopting the prior draft — this is explicitly **not** an approval/sign-off. Ground Truth approval is structurally reserved to a separately named Ground-Truth Approver, a role that remains unassigned; the COO agent did not and will not approve it.
>
> **2026-08-22, later still — `COO-D23` finalized:** `COO-D23` had **no prior draft** on file at the time of the recording above. The real human COO, Lai Yoke Yau (`kaneki016`), acting directly in a live session, has now authorized deciding it directly from a set of suggestions already surfaced in conversation, recorded below as `APPROVE`. This closes the last open decision in the packet — `COO-D26` remains the sole non-sign-off item (preparer input only, by design).

| Field | Value |
|---|---|
| Status | **PROPOSED** |
| Gate P0 | **BLOCKED** |
| Main Spec target | **v1.1 — NOT ACCEPTED** |
| Contract target | **v1.1.0 — NOT FROZEN** |
| Feature implementation | **NOT AUTHORIZED** |
| From | CTO — Backend & Integration Lead (`mingzheYeoh`) |
| To | COO — AI & ESG Operations Lead |
| Role owner | **Lai Yoke Yau (`kaneki016`)** — recorded 2026-08-22 |
| Packet state | **PARTIALLY RECEIVED** — 26 of 27 recorded `APPROVE`; `COO-D26` preparer input only, not a sign-off |
| Decisions in this packet | **27** |
| Decisions recorded | **26** (`APPROVE`) + 1 preparer-input-only (`COO-D26`, not a sign-off) |
| Date issued | 2026-08-21 |
| Date recorded (this packet) | **2026-08-22** |

---

## Recorded status

**26 of 27 decisions are recorded `APPROVE`, attributed to Lai Yoke Yau (`kaneki016`), dated 2026-08-22.** `COO-D26` carries a recorded **preparer input** (not an approval/sign-off) — Ground Truth approval stays with the separately named Ground-Truth Approver, a role still unassigned.

The COO workstream is now active under role owner Lai Yoke Yau (`kaneki016`). This recording supersedes an earlier approval session whose edits never reached git history.

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

### `COO-D01` — Pure processing core (`BLOCKER-04`) — **APPROVE** (Lai Yoke Yau / `kaneki016`, 2026-08-22)

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

### `COO-D02` — Provider configuration (`BLOCKER-08`) — **APPROVE** (Lai Yoke Yau / `kaneki016`, 2026-08-22)

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

Change control requires **CEO + CTO + COO**. The CTO position is recorded. **The COO position below is now recorded — `APPROVE` on every line, Lai Yoke Yau (`kaneki016`), 2026-08-22.**

| ID | Item | CTO position | Status |
|---|---|---|---|
| `COO-D03` | `BLOCKER-01` — English Main Spec normative; Chinese non-normative | RULED | **APPROVE** |
| `COO-D04` | `BLOCKER-02` — map ownership paths into section 16 | RULED | **APPROVE** |
| `COO-D05` | `BLOCKER-06` — keyword-first retrieval; pgvector installed but unused | RULED | **APPROVE** |
| `COO-D06` | `RULING-01` — Job and Export concepts; Contract v1.1.0; four enums | AMEND | **APPROVE** |
| `COO-D07` | `RULING-02` — Evidence Status evaluation model | AMEND | **APPROVE** |
| `COO-D08` | `RULING-03` — `AI_SUGGESTED` removed; `DraftProvenance` added | AMEND | **APPROVE** |
| `COO-D09` | `RULING-04` — persisted `question_order` | AMEND | **APPROVE** |
| `COO-D10` | `RULING-05` — named previews and the activity endpoint | APPROVE | **APPROVE** |
| `COO-D11` | `RULING-06` — idempotency and database-enforced concurrency | APPROVE | **APPROVE** |
| `COO-D12` | `RULING-07` — amendments recorded individually; Main Spec v1.1 | APPROVE | **APPROVE** |
| `COO-D13` | `C-15` — deterministic unreadable-document relevance rule | RULED | **APPROVE** |
| `COO-D14` | `SPEC-AMD-001` — `processing_jobs` and `documents.latest_job_id` | APPROVED | **APPROVE** |
| `COO-D15` | `SPEC-AMD-002` — evidence extraction provenance fields | APPROVED | **APPROVE** |
| `COO-D16` | `SPEC-AMD-003` — AI schema as a compatible superset | APPROVED AS AMENDED | **APPROVE** |
| `COO-D17` | `SPEC-AMD-004` — repository path reconciliation | APPROVED | **APPROVE** |
| `COO-D18` | `SPEC-AMD-005` — Evidence Status evaluation model | APPROVED AS AMENDED | **APPROVE** |
| `COO-D19` | `SPEC-AMD-006` — three-dimension model and `DraftProvenance` | APPROVED AS AMENDED | **APPROVE** |
| `COO-D20` | `SPEC-AMD-007` — `questions.question_order` | APPROVED | **APPROVE** |

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
| `COO-D21` | C-15 relevance signals | `SPEC-AMD-005` final signature; Phase 4 | **APPROVE** (Lai Yoke Yau / `kaneki016`, 2026-08-22 — adopts agent draft below) |
| `COO-D22` | Parser and OCR failure-code catalog | REQ-005; `TEST-E2E-007` | **APPROVE** (Lai Yoke Yau / `kaneki016`, 2026-08-22 — adopts agent draft below) |
| `COO-D23` | `document_chunks` field shape | Retrieval layer; server-side location resolution | **APPROVE** (Lai Yoke Yau / `kaneki016`, 2026-08-22 — decided directly, no prior draft) |
| `COO-D24` | `ExtractionMethod` enum values | `SPEC-AMD-002` | **APPROVE** (Lai Yoke Yau / `kaneki016`, 2026-08-22 — adopts agent draft below) |
| `COO-D25` | Deterministic AI fixtures | All AI-dependent CI tests | **APPROVE** (Lai Yoke Yau / `kaneki016`, 2026-08-22 — adopts agent draft below) |

### `COO-D21` — C-15 relevance signals — **APPROVE** (Lai Yoke Yau / `kaneki016`, 2026-08-22)

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

> **DRAFT RECOMMENDATION — COO agent, 2026-08-22 (not an approval; for human role-owner review):**
>
> - **`document_type` value set** — Main Spec §"documents" table already fixes this enum: `QUESTIONNAIRE, UTILITY_BILL, POLICY, HR_DATA, WASTE_RECORD, SAFETY_RECORD, OTHER`. Recommend adopting it as-is for C-15 condition 2 — no new values needed.
> - **SEDG mapping** — the Main Spec maps SEDG Topic/Disclosure at the **question** level (`questions.sedg_topic_code`, `questions.sedg_disclosure_code`), not at the document-type level. Recommend condition 2 read as: "`document_type` is in `evidence_requirement_json.accepted_document_types`" where `accepted_document_types` is a subset of the 7 values above, authored per-question alongside the existing SEDG mapping — no separate document_type→SEDG lookup table is needed.
> - **`evidence_requirement_json` shape (recommended)**:
>   ```json
>   {
>     "accepted_document_types": ["UTILITY_BILL", "POLICY"],
>     "keywords": ["electricity", "kwh", "tenaga nasional"],
>     "metric": "string|null",
>     "period_required": true,
>     "scope_description": "string|null",
>     "unit": "string|null"
>   }
>   ```
>   Source: derived from Main Spec §12.4 retrieval-signal list (keywords, possible document types, SEDG Topic, metric/period/scope/unit) plus the existing `questions.evidence_requirement_json` column. Authored by whoever builds the questionnaire/SEDG mapping (COO workstream), one JSON object per question, at questionnaire-classification time.
> - **Metadata/heading fields that survive a failed extraction** — this is a **gap**, not settled by the current spec. `document_chunks` (with `heading_path`, `metadata_json`, page/sheet/cell) is populated by the parser; a document that fails extraction (`NEEDS_MANUAL_REVIEW`) may never reach chunking, so those fields may not exist for it. Recommend: the "Security and format validation" stage (Main Spec §12.1, pipeline stage B) captures a lightweight `original_filename` plus any embedded container metadata (PDF `/Title`, `/Author`, `/Subject`; DOCX/XLSX core-properties title/subject) **before** attempting the parser, independent of parse success, and this is what condition 3 matches against for a failed document. This needs a schema field to hold it (e.g. `documents.pre_parse_metadata_json`) that does not exist in the current Main Spec — **flagging as a proposed spec amendment for CTO/CEO co-review**, not something the COO agent can add unilaterally.

> **RECORDED DECISION — Lai Yoke Yau (`kaneki016`), 2026-08-22:** The draft recommendation above is adopted as the COO's technical input for `COO-D21`, in full, including the flagged gap (pre-parse metadata field) being forwarded as a proposed spec amendment rather than resolved here.

### `COO-D22` — Failure-code catalog — **APPROVE** (Lai Yoke Yau / `kaneki016`, 2026-08-22)

Parser and OCR failure codes, **each marked retryable or terminal**. The orchestration layer cannot decide whether to retry without this, and defaulting to retry on a terminal failure burns the provider budget on work that can never succeed.

> **DRAFT RECOMMENDATION — COO agent, 2026-08-22 (not an approval; for human role-owner review):**
>
> | `error_code` | Meaning | Retryable? | Notes |
> |---|---|---|---|
> | `FILE_CORRUPT` | Container unreadable / truncated | Terminal | — |
> | `UNSUPPORTED_FORMAT` | MIME type outside the 6 allowed types | Terminal | Per `BLOCKER-05` file-type limit |
> | `PASSWORD_PROTECTED` | Encrypted, no password supplied | Terminal | Route to `NEEDS_MANUAL_REVIEW` for manual re-upload |
> | `FILE_TOO_LARGE` / `PAGE_LIMIT_EXCEEDED` / `ROW_LIMIT_EXCEEDED` | Exceeds `BLOCKER-05` limits (20 MB, 100 pages, 50,000 rows) | Terminal | Reject at validation stage, before parse |
> | `OCR_NO_TEXT_LAYER_UNRECOVERABLE` | OCR ran, still produced no usable text | Terminal | Per Main Spec §4.2: mark `NEEDS_MANUAL_REVIEW` |
> | `OCR_TIMEOUT` | OCR exceeded the 300 s budget (`BLOCKER-05`) | Retryable (max 2, exponential backoff) | Matches Main Spec §4.3 "retry no more than twice" |
> | `PARSER_TIMEOUT` | Parse exceeded 180 s budget | Retryable (max 2) | Same backoff rule |
> | `PARSER_CRASH` | Unhandled parser exception | Retryable (max 2) | If still failing, terminal → manual entry |
> | `STORAGE_WRITE_FAILURE` | Content-addressed storage write failed | Retryable (max 2) | Transient infra fault |
> | `EMBEDDING_FAILURE` | Embedding step failed | Retryable (max 2), else degrade | Per Main Spec §4.3: file stays available via keyword search |
>
> This list is a starting proposal derived from limits and rules already stated in the Main Spec (§4.3 Failure and Recovery, `BLOCKER-05` limits, §12.3 Document Parsing) — it has not been validated against real parser/OCR library error surfaces (Docling / Tesseract / openpyxl) and should be treated as provisional until whoever integrates those libraries confirms the actual error taxonomy.

> **RECORDED DECISION — Lai Yoke Yau (`kaneki016`), 2026-08-22:** The draft failure-code catalog above is adopted as the COO's recorded input for `COO-D22`, including its provisional-until-library-integration caveat.

### `COO-D23` — `document_chunks` field shape — **APPROVE** (Lai Yoke Yau / `kaneki016`, 2026-08-22)

`document_chunks` is the retrieval unit the AI pipeline cites by `chunk_id`; the server resolves the actual source location from this table, never from a model-claimed location (`AGENTS.md` §3.3). This item had no prior draft on file — the real human COO decided it directly in a live session, from a set of suggestions already surfaced in conversation.

**Nullability by source type:**

| Source type | `page_number` | `sheet_name` | `cell_range` | `heading_path` |
|---|---|---|---|---|
| PDF | **set** | null | null | not the position carrier for this type |
| XLSX | null | **set** | **set** | null |
| DOCX | null | null | null | **set** — carries the position instead |

- **`heading_path` format**: a `">"`-joined string, e.g. `"Policy > 3. Scope > 3.2 Coverage"`. This is **for display only, not machine logic** — nothing in the pipeline or server parses or splits it to derive structure.
- **`metadata_json` expected keys**: pinned to a minimal fixed set now, not an unconstrained free-form bag:
  ```json
  {
    "ocr_confidence": "float|null",
    "extraction_method": "<ExtractionMethod enum value, per COO-D24>"
  }
  ```
- **`embedding`**: stays nullable and unused until/unless semantic retrieval is evaluated — the Main Spec treats pgvector as optional, keyword-first MVP (`BLOCKER-06` / `COO-D05`).
- **`sequence_no` semantics**: document-order chunk index, 1-based, unique per `document_id`, so ordering ties are deterministic. This is exactly what the `questionnaire_25plus.xlsx` fixture (`COO-D25`) is designed to catch.

> **RECORDED DECISION — Lai Yoke Yau (`kaneki016`), 2026-08-22:** The field shape above — nullability by source type, `heading_path` format, pinned `metadata_json` keys, `embedding` nullable/unused, and `sequence_no` semantics — is adopted directly as the COO's technical input for `COO-D23`, authorized directly in this live session from suggestions already surfaced in conversation. No prior draft existed for this item.

### `COO-D24` — `ExtractionMethod` values — **APPROVE** (Lai Yoke Yau / `kaneki016`, 2026-08-22)

Note that `extraction_confidence` is **nullable** by design, because a deterministic extraction path has no meaningful confidence value. A null must never be coerced to `1.000` — that would silently promote "we did not measure" into "we are certain".

> **DRAFT RECOMMENDATION — COO agent, 2026-08-22 (not an approval; for human role-owner review):**
>
> ```text
> ExtractionMethod: NATIVE_TEXT | OCR_DOCLING | OCR_TESSERACT | XLSX_CELL | CSV_ROW | MANUAL_ENTRY
> ```
>
> - `NATIVE_TEXT` — PDF/DOCX text layer present, no OCR needed. `extraction_confidence` may be null (deterministic) or a text-coverage ratio if the pipeline chooses to measure it.
> - `OCR_DOCLING` / `OCR_TESSERACT` — scanned PDF/image path (Main Spec §"Backend" table: Docling OCR primary, Tesseract fallback). `extraction_confidence` is **non-null** — this is the one path where a real quality signal exists.
> - `XLSX_CELL` / `CSV_ROW` — deterministic cell/row extraction (§12.3). `extraction_confidence` is **null** — there is nothing probabilistic to score.
> - `MANUAL_ENTRY` — user-entered, no extraction occurred. `extraction_confidence` is **null**.

> **RECORDED DECISION — Lai Yoke Yau (`kaneki016`), 2026-08-22:** The `ExtractionMethod` enum and nullability rules above are adopted as the COO's recorded input for `COO-D24`.

### `COO-D25` — Deterministic AI fixtures — **APPROVE** (Lai Yoke Yau / `kaneki016`, 2026-08-22)

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

> **DRAFT RECOMMENDATION — COO agent, 2026-08-22 (not an approval; for human role-owner review):**
>
> The fixture list above looks sufficient to cover `CT-021`, `CT-022`, `TB-3`, and `CT-014`. Recommend adding two more, matching the `COO-D22` failure-code catalog so every terminal/retryable branch has CI coverage without a live provider call:
>
> | Fixture | Purpose |
> |---|---|
> | `password_protected.pdf` | Exercises `PASSWORD_PROTECTED` → `NEEDS_MANUAL_REVIEW`, no retry |
> | `ocr_timeout_then_recover.pdf` | Exercises the retry-twice-then-terminal path for `OCR_TIMEOUT` |
>
> Confirm `FixtureProvider` is the only provider path exercised in CI (per `COO-D02` / `BLOCKER-08`) — never the live `anthropic` provider.

> **RECORDED DECISION — Lai Yoke Yau (`kaneki016`), 2026-08-22:** The fixture list plus the two additional fixtures above are adopted as the COO's recorded input for `COO-D25`.

---

## Section D — Ground-truth impact to confirm

| ID | Item | Status |
|---|---|---|
| `COO-D26` | Confirm the ground-truth impact below | **COO preparer input recorded — NOT a sign-off.** Ground-Truth Approver sign-off still required; role unassigned. |

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

> **DRAFT RECOMMENDATION — COO agent, 2026-08-22 (not an approval; not a Ground-Truth approval — the COO structurally must never approve ground truth it prepares):**
>
> The impact table above reads consistent with the Main Spec's own Evidence Status rules (§6: `MISSING` = no sufficient source found; a signed declaration with no supporting record is exactly that) and with `RULING-02`/`RULING-03`. Recommend confirming all five rows as-is. This confirmation is only a **preparer's** recommendation; it still requires sign-off from the separately named **Ground-Truth Approver** (role currently unassigned — see `decision-register.md` §6.3/§6.4), who must not be the COO.

> **RECORDED — Lai Yoke Yau (`kaneki016`), COO, 2026-08-22:** The preparer view above is adopted and recorded as the **COO's preparer input** on the ground-truth impact table. **This is explicitly not an approval or sign-off of Ground Truth.** COO approval of `COO-D26` is **structurally impossible** by design — Ground Truth approval belongs solely to a separately named Ground-Truth Approver, and that role does not yet exist as an assigned identity (see `decision-register.md` §6.3/§6.4 and `GATE-P0-APPROVAL.md`). `COO-D26` remains blocked on that assignment regardless of this preparer input.

---

## Section E — Identity and acknowledgement

| ID | Item | Status |
|---|---|---|
| `COO-D27` | Supply `COO_GITHUB_HANDLE` and the written synthetic-data acknowledgement | **APPROVE** (Lai Yoke Yau / `kaneki016`, 2026-08-22) |

```text
COO_GITHUB_HANDLE = kaneki016
```

Written synthetic-data-only acknowledgement, COO portion: **RECORDED** — Lai Yoke Yau (`kaneki016`), 2026-08-22: acknowledges synthetic data only, no real personal data, per `AGENTS.md` §3.1. CEO and CTO portions remain outstanding — 1 of 3 recorded.

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

**27 decisions. 26 recorded APPROVE (Lai Yoke Yau / `kaneki016`, 2026-08-22). 1 preparer-input-only, not a sign-off (`COO-D26`). All 27 addressed — nothing remains PENDING. Gate P0 is BLOCKED — the CEO packet and the Ground-Truth Approver assignment are still outstanding, and `COO-D26` sign-off remains open even within the COO packet (structurally, by design — it can never be signed off by the COO).**
