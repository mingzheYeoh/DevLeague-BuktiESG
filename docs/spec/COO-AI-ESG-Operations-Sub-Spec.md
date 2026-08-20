<!-- Phase 0 document-control banner. Added by the documentation-only Phase 0 bootstrap commit. -->

## Document Control Banner

| Field | Value |
|---|---|
| Status | **PROPOSED** |
| Gate P0 | **BLOCKED** |
| Version of the text below | **v1.0** (unchanged) |
| Main Spec target | **v1.1 — NOT ACCEPTED** |
| Contract target | **v1.1.0 — NOT FROZEN** |
| Feature implementation | **NOT AUTHORIZED** |
| Authority | Below the Main Technical Spec and the Shared Integration Contract. |
| Normative source of truth | [`BuktiESG-Technical-Spec-EN.md`](BuktiESG-Technical-Spec-EN.md) — **English is normative.** The Chinese translation is non-normative; on conflict, English governs. |

**The body below is unchanged v1.0 text.** Two proposed changes affect this document and are **not applied here**:

- `SPEC-AMD-004` — file-ownership paths are mapped into the Main Spec §16 repository tree; no duplicate top-level trees are created.
- Pointer correction — the "source of truth" reference is the English Main Spec.

Both are recorded in [`AMENDMENTS.md`](AMENDMENTS.md) and [`../decisions/decision-register.md`](../decisions/decision-register.md). Neither is final: Contract and Main Spec change control requires **CEO + CTO + COO** approval, and only the CTO has ruled.

---

# COO — AI & ESG Operations Lead Sub-Spec

Version: 1.0  
Date: 2026-08-21  
Status: `planned`  
Role owner: To be assigned  
Project tier: T1  
Task risk: Yellow  
Enforcement: Advisory-only

## 1. Authority

This Sub-Spec must be used together with `BuktiESG-Technical-Spec-ZH.md`.

The Main Technical Spec is authoritative. This document assigns AI, document-processing, ESG taxonomy, fixture, and evaluation responsibility only. It cannot override the Main Spec, Shared Integration Contract, evidence status rules, priority formula, human-review requirement, or synthetic-data restriction.

AI recommendations are inputs to deterministic rules and human review. They are not final compliance or assurance decisions.

## 2. Mission

Turn synthetic questionnaires and business documents into structured, source-located evidence candidates that help the team identify what can be answered, what is missing or unreliable, and what operational follow-up is needed.

The COO role combines:

- AI and document-processing lead;
- ESG operations and SEDG taxonomy lead;
- Synthetic demo data owner;
- Evidence extraction and retrieval owner;
- AI evaluation and failure-analysis owner;
- Demo scenario validator.

## 3. Success Outcome

For the approved synthetic demo dataset, the pipeline preserves questionnaire and document locations, maps questions to E/S/G and SEDG topics, returns schema-valid evidence candidates, identifies missing elements and possible conflicts, and supplies enough structured facts for the backend to calculate explainable evidence states and priorities.

## 4. Scope

### 4.1 Included

- Synthetic ESG questionnaire and supporting documents;
- SEDG v2 topic/disclosure machine-readable reference data;
- XLSX/CSV question parsing;
- PDF, DOCX, spreadsheet, and optional image parsing;
- OCR fallback for scanned documents;
- Page, sheet/cell, paragraph, and excerpt preservation;
- Chunking and metadata normalization;
- Keyword and optional semantic retrieval;
- E/S/G and SEDG mapping recommendation;
- Structured evidence extraction;
- Missing-element and possible-conflict recommendations;
- Evidence-status inputs and rationale;
- Priority-factor recommendations and rationale;
- Prompt-injection fixtures and AI evaluation;
- Demo scenario and ground-truth preparation.

### 4.2 Excluded

- Final persisted evidence-state authority;
- Human confirmation;
- Choosing the true source in a conflict;
- Legal, regulatory, audit, or certification decisions;
- Frontend implementation;
- Database migrations and API ownership;
- Changing the priority formula;
- Real employee, customer, salary, health, identity, or contract data.

## 5. File Ownership

Primary writable ownership:

```text
workers/document_processor/**
packages/taxonomy/**
fixtures/demo_company/**
ai/prompts/**
ai/schemas/**
ai/evaluation/**
docs/evidence/ai/**
```

Prepared by COO but protected from unilateral acceptance:

```text
fixtures/ground_truth/**
AI system prompts
evidence-status rule fixtures
priority expectation fixtures
```

The COO may prepare Ground Truth, but a non-implementing teammate must review and approve expected values before they are used as acceptance authority.

## 6. Required Inputs

The COO depends on:

- Approved Main Spec and Phase 0 decisions;
- Shared Integration Contract and JSON schemas;
- Database chunk and AI Run formats from the CTO;
- Evidence-card and source-viewer needs from the CEO;
- Approved 20-question demo scope;
- Official SEDG v2 references listed in the Main Spec;
- Approved file limits and processing budgets;
- Synthetic-only data rule.

## 7. Deliverables

### 7.1 Demo Data

- Synthetic company profile for BuktiPack Manufacturing Sdn. Bhd.;
- `customer-esg-questionnaire.xlsx` with 20 questions and 12 required questions;
- Three-month synthetic TNB-style bills for PARTIAL evidence;
- Waste summary and contractor receipt with a controlled conflict;
- Synthetic employee register with training and diversity fields;
- Outdated anti-bribery policy;
- Current safety policy without an incident register;
- Unsupported management declaration;
- Intentionally missing GHG calculation and forced-labour assessment;
- Ground Truth mapping and source-location expectations.

### 7.2 Processing Pipeline

- Questionnaire parser with row/cell preservation;
- PDF/DOCX/XLSX/CSV parser adapters;
- OCR fallback and manual-review state;
- Normalized chunks with source-location metadata;
- Hybrid retrieval or a documented keyword-first MVP;
- Structured extraction conforming to the shared schema;
- Prompt and schema versioning;
- AI Run metadata and cost/latency reporting.

### 7.3 Evaluation

- Question-to-pillar/topic evaluation;
- Evidence-retrieval evaluation against protected ground truth;
- Source-location accuracy checks;
- Schema-validity checks;
- Prompt-injection test fixture;
- Failure-mode report;
- Known AI limitations and manual-review guidance.

## 8. Dataset Requirements

All fixture data must be synthetic and internally consistent except where a documented conflict is intentionally introduced.

Required demonstration states:

| Demo question type | Expected state input | Intended lesson |
|---|---|---|
| Electricity consumption | Only Jan–Mar data for a 12-month period | PARTIAL |
| Anti-bribery policy | Policy approval older than the approved threshold | OUTDATED |
| Waste total | Two sources disagree for the same period and scope | CONFLICTING |
| Formal Scope 1/2 result | No formal calculation document | MISSING |
| Management claim of no incidents | Unsupported statement without register | AI_SUGGESTED or unsupported, never VERIFIED |
| Current supported metric | Exact period, scope, unit, and source location | VERIFIED candidate |

Each intentional state must have a clear Ground Truth explanation.

## 9. Parsing Requirements

### Questionnaire

Prefer deterministic parsing before LLM use:

1. Detect sheets and header candidates;
2. Identify question, required, comments, answer, and evidence columns;
3. Preserve original sheet, row, and cell;
4. Request user confirmation if header confidence is insufficient;
5. Use AI only after structural confirmation for taxonomy mapping.

### Documents

- PDF: preserve page number, heading, table, and paragraph order;
- Scanned PDF: detect weak text layer before OCR;
- DOCX: preserve heading path and paragraph index;
- XLSX: preserve sheet, cell range, displayed value, and formula metadata where relevant;
- CSV: preserve row and column names;
- Image: preserve original image reference and OCR coordinates where available.

No candidate evidence may be returned without a resolvable source locator.

## 10. Retrieval and Extraction

### Keyword-First MVP

The minimum acceptable retrieval path is:

1. Normalize the question;
2. Extract topic, metric, period, scope, unit, and likely document type;
3. Run full-text/keyword retrieval;
4. Return ranked chunks with locations;
5. Apply structured extraction to top candidates.

### Hybrid Stretch

If time permits:

1. Add embeddings;
2. Merge full-text and semantic candidates;
3. Deduplicate;
4. Rerank;
5. Evaluate improvement against the same protected Ground Truth.

Do not add pgvector or reranking merely for appearance. Keep it only if measured retrieval improves or if it materially helps the demo.

### Structured Extraction

Output must conform to the Shared Integration Contract. It must include:

- Question ID;
- Draft answer or null;
- Evidence candidates with chunk IDs and excerpts;
- Period, scope, value, and unit where available;
- Missing elements;
- Possible conflicts;
- Suggested follow-up;
- Model, prompt version, input hash, source IDs, latency, and estimated cost in AI Run metadata.

## 11. Evidence and AI Boundaries

The COO pipeline may recommend:

- E/S/G pillar;
- SEDG topic and disclosure;
- Candidate evidence;
- Missing requirements;
- Possible conflicts;
- Draft answer;
- Priority-factor values and rationale.

The COO pipeline may not set:

- `HUMAN_CONFIRMED`;
- Final legal applicability;
- Final conflict resolution;
- Certification or audit status;
- Final persisted VERIFIED state without deterministic validation;
- Customer-submission approval.

`extraction_confidence` describes parsing or extraction quality. It is not Evidence Status.

## 12. Prompt Injection Controls

- Treat uploaded content as untrusted data, never as system instructions;
- Do not allow document text to request tools, secrets, unrelated files, or different cases;
- Limit model context to approved top chunks from the same Case;
- Use schema-constrained output;
- Validate all IDs against the current job and Case;
- Do not log unnecessary full document or prompt content;
- Add a fixture containing instructions such as “ignore previous rules” and prove the pipeline still follows the system contract.

## 13. Task Plan

### Phase 0 — ESG and AI Freeze

- `COO-001`: Confirm the 20 demo questions and their SEDG coverage.
- `COO-002`: Confirm supported file types, source-location formats, and OCR scope.
- `COO-003`: Confirm the shared AI result schema with CTO and CEO.
- `COO-004`: Confirm keyword-first MVP and optional hybrid-search stretch.
- `COO-005`: Document model/provider adapter assumptions, privacy, cost, and fallback.
- `COO-006`: Do not generate production code before Gate P0.

### Phase 1 — Synthetic Dataset and Taxonomy

- `COO-010`: Create the synthetic company and questionnaire.
- `COO-011`: Create all evidence fixtures required by the Main Spec.
- `COO-012`: Create machine-readable SEDG pillar/topic/disclosure reference data.
- `COO-013`: Create Ground Truth for mapping, retrieval, location, state input, and priority rationale.
- `COO-014`: Request non-implementer review and freeze approved Ground Truth.

### Phase 2 — Parsing

- `COO-020`: Implement questionnaire parsing with source cell preservation.
- `COO-021`: Implement PDF, DOCX, XLSX, and CSV adapters.
- `COO-022`: Implement OCR fallback or manual-review state.
- `COO-023`: Normalize chunks and source locations.
- `COO-024`: Produce parser tests against approved fixtures.

### Phase 3 — Mapping and Retrieval

- `COO-030`: Implement E/S/G and SEDG mapping recommendation.
- `COO-031`: Implement keyword retrieval.
- `COO-032`: Add hybrid retrieval only if justified by evaluation.
- `COO-033`: Implement schema-constrained evidence extraction.
- `COO-034`: Return exact excerpts and source locators.
- `COO-035`: Record AI Run metadata.

### Phase 4 — Evidence and Priority Inputs

- `COO-040`: Extract period, scope, value, unit, and breakdown availability.
- `COO-041`: Identify missing elements.
- `COO-042`: Identify possible conflicts without selecting a winner.
- `COO-043`: Recommend evidence-state inputs and rationale.
- `COO-044`: Recommend priority factors and rationale without calculating a different formula.
- `COO-045`: Validate all outputs against Ground Truth and schema.

### Phase 5 — Review and Action Support

- `COO-050`: Generate suggested follow-up text for missing or partial evidence.
- `COO-051`: Generate action-title and next-step suggestions as unconfirmed recommendations.
- `COO-052`: Ensure recommendations distinguish SUBMISSION from IMPROVEMENT.
- `COO-053`: Ensure no AI result sets completion or confirmation state.

### Phase 6 — Export Support

- `COO-060`: Provide clear evidence excerpts and missing-element text for export.
- `COO-061`: Provide model and prompt provenance for internal records, not customer-facing detail unless approved.
- `COO-062`: Verify exported citations match parsed source locations.

### Phase 7 — Evaluation and Demo Hardening

- `COO-070`: Run mapping and retrieval evaluation.
- `COO-071`: Run prompt-injection and malformed-output tests.
- `COO-072`: Measure latency and estimated cost for one complete demo Case.
- `COO-073`: Freeze deterministic demo fixtures and seed behavior.
- `COO-074`: Prepare fallback precomputed AI results for a live model outage, visibly marked as fixture data.

## 14. Acceptance Criteria

- `COO-AC-001`: WHEN the questionnaire is parsed, THE PIPELINE SHALL preserve every demo question's original sheet and cell reference.
- `COO-AC-002`: WHEN a document chunk is returned as evidence, THE PIPELINE SHALL include a resolvable page, sheet/cell, paragraph, or approved manual locator.
- `COO-AC-003`: WHEN only three months support a twelve-month question, THE PIPELINE SHALL identify the missing period and SHALL NOT describe the evidence as complete.
- `COO-AC-004`: WHEN two same-period and same-scope sources disagree, THE PIPELINE SHALL return both as a possible conflict and SHALL NOT choose a winner.
- `COO-AC-005`: WHEN no supporting source exists, THE PIPELINE SHALL return missing elements and SHALL NOT invent a citation.
- `COO-AC-006`: WHEN a document contains prompt-injection text, THE PIPELINE SHALL continue following the system contract and SHALL NOT access unrelated data or tools.
- `COO-AC-007`: WHEN model output fails schema validation, THE PIPELINE SHALL produce a recoverable failure or one bounded repair attempt, not an accepted answer.
- `COO-AC-008`: WHEN the pipeline recommends a priority, IT SHALL use the four approved factors and provide rationale for each.
- `COO-AC-009`: WHEN AI creates a draft answer, IT SHALL remain unconfirmed and SHALL NOT set HUMAN_CONFIRMED.
- `COO-AC-010`: WHEN the approved demo fixtures are processed, THE PIPELINE SHALL produce the intended Verified-candidate, Partial, Outdated, Conflicting, Missing, and AI-Suggested scenarios.

## 15. Tests and Evidence

Required evidence:

- Parser unit tests by file type;
- Page, sheet/cell, and paragraph location checks;
- JSON Schema validation tests;
- Mapping evaluation against protected Ground Truth;
- Retrieval evaluation against protected Ground Truth;
- Missing and conflict scenario tests;
- Prompt-injection test results;
- Model timeout and malformed-output recovery tests;
- Latency and estimated cost report;
- Known failure modes and manual-review guidance.

## 16. Handoffs

### To CTO

- Worker input and AI Analysis Result schema;
- Chunk and source-location records;
- AI Run metadata;
- Parser and model failure codes;
- Deterministic fixtures for contract tests;
- Expected invalidation or retry behavior.

### To CEO

- Example evidence cards for every status;
- Source-location examples;
- Human-readable status rationale;
- Demo question sequence;
- Known AI uncertainty and user-review language.

### From CTO and CEO

- CTO provides persistence, job, validation, and retry interface;
- CEO provides visible metadata needs and feedback when rationale is unclear.

## 17. Stop Conditions

Stop and escalate when:

- Real personal, customer, payroll, health, identity, or contract data is requested;
- A model output would be treated as verified without a source location;
- A conflict is being auto-resolved without human authority;
- Ground Truth is changed to improve the implementation score;
- A new model, external service, or dependency introduces unapproved cost or data handling;
- The same evaluation gate fails three repair cycles without materially new evidence.

## 18. AI Agent Start Prompt

```text
You are the AI implementation agent for the COO — AI & ESG Operations Lead workstream.

Read, in this order:
1. BuktiESG-Technical-Spec-ZH.md
2. Shared-Integration-Contract.md
3. COO-AI-ESG-Operations-Sub-Spec.md
4. Integration-Checklist.md

The Main Spec is authoritative. AI output is advisory and must not bypass deterministic
validation or human confirmation. Do not change shared contracts, evidence rules,
priority rules, protected Ground Truth, or critical tests to fit the implementation.

Before writing code, return:
- your understanding of the AI/ESG outcome and non-goals;
- your owned paths and protected paths;
- required inputs from CEO and CTO;
- Phase tasks, dataset plan, and parser plan;
- evaluation, prompt-injection, cost, and recovery tests;
- blocking decisions.

Do not start feature implementation until Gate P0 is accepted.
```

