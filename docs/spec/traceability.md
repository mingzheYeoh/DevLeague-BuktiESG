# Requirement-to-Test Traceability Matrix

| Field | Value |
|---|---|
| Status | **PROPOSED** |
| Gate P0 | **BLOCKED** |
| Main Spec target | **v1.1 — NOT ACCEPTED** |
| Contract target | **v1.1.0 — NOT FROZEN** |
| Feature implementation | **NOT AUTHORIZED** |
| Tests written | **Zero.** Every row below is `planned`. |

**No test in this document exists.** No test file, no fixture, and no CI job has been created. This matrix records the intended mapping so that coverage gaps are visible before implementation rather than discovered after it.

Requirement text is quoted from the normative English Main Spec. Where a requirement is affected by a proposed amendment, the amendment is named.

---

## Discrepancy found while building this matrix

The Main Spec defines **eight** critical end-to-end tests, `TEST-E2E-001` through `TEST-E2E-008`. The Integration Checklist section 11 lists only **seven**, `E2E-001` through `E2E-007`. **`E2E-008` — repeated uploads, repeated clicks, and refresh must not create duplicate data — is absent from the checklist.**

This is escalated, not silently resolved. Under the authority order the Main Spec governs, so eight critical tests are required. The Integration Checklist needs a corresponding correction, which is **not** applied in this commit.

Recorded as an open item in [`../decisions/decision-register.md`](../decisions/decision-register.md).

---

## 1. Critical End-to-End Tests

These are **protected**. An implementing agent must never edit them to make an implementation pass.

| Test | Covers | Assertion | Status |
|---|---|---|---|
| `TEST-E2E-001` | REQ-001, REQ-010, REQ-011 | Create Case, upload questionnaire, identify 20 questions | planned |
| `TEST-E2E-002` | REQ-002, REQ-020, REQ-021 | Upload evidence, view a VERIFIED source location | planned |
| `TEST-E2E-003` | REQ-022, REQ-023, REQ-024 | Display PARTIAL, OUTDATED, CONFLICTING, and MISSING | planned |
| `TEST-E2E-004` | REQ-025, REQ-026 | Unconfirmed AI draft does not count toward readiness | planned |
| `TEST-E2E-005` | REQ-030, REQ-032, REQ-033 | Gap to Action to owner/deadline to closure evidence | planned |
| `TEST-E2E-006` | REQ-040, REQ-041, REQ-042 | Warning before export, then PDF and Evidence Index generated | planned |
| `TEST-E2E-007` | REQ-005, REQ-011 | Parser failure, retry, manual review | planned |
| `TEST-E2E-008` | REQ-003, REQ-052, REQ-053 | Repeated uploads, repeated clicks, and refresh do not create duplicate data | planned |

`TEST-E2E-004` is directly affected by `SPEC-AMD-006`. Its assertion becomes: `evidence_status = MISSING`, `draft_provenance = AI_GENERATED`, `human_confirmed = false`, `counts_toward_readiness = false` — all four simultaneously, because the point of the amendment is that these are independent dimensions.

---

## 2. Requirements

31 requirements exist. They are numbered with deliberate gaps, not contiguously to 053.

### 2.1 Case and file intake

| REQ | Requirement | Tests | Owner | Status |
|---|---|---|---|---|
| REQ-001 | Create Case with customer, deadline, reporting period; display unique Case ID | `TEST-E2E-001`, `TEST-API-001` | CTO | planned |
| REQ-002 | Display filename, type, size, checksum, processing status | `TEST-E2E-002`, `TEST-API-002` | CTO | planned |
| REQ-003 | Same checksum in same Case must not create a duplicate; link to existing | `TEST-E2E-008`, `TEST-UNIT-003`, `CTO-AC-001` | CTO | planned |
| REQ-004 | Reject unsupported type or size; display allowed types and limits | `TEST-API-004` | CTO | planned |
| REQ-005 | Parser failure saves error reason; offers retry and manual entry | `TEST-E2E-007`, `TEST-UNIT-005` | CTO + COO | planned |

### 2.2 Questionnaire parsing and mapping

| REQ | Requirement | Tests | Owner | Status |
|---|---|---|---|---|
| REQ-010 | Extract question text, section, required flag, source row/cell | `TEST-E2E-001`, `TEST-UNIT-010` | COO | planned |
| REQ-011 | Unreliable header requires user selection; must not publish a guess | `TEST-E2E-007`, `TEST-UNIT-011` | COO + CEO | planned |
| REQ-012 | Save pillar, SEDG Topic, optional Disclosure ID, mapping rationale | `TEST-UNIT-012` | COO | planned |
| REQ-013 | Human mapping becomes current; previous value preserved in history | `TEST-UNIT-013`, `TEST-API-013` | CTO + COO | planned |

**Affected by `SPEC-AMD-007`:** REQ-010 additionally assigns `question_order` during import. New test `TEST-UNIT-014` asserts a fixture of more than 20 questions returns `question_order ASC, id ASC` across page boundaries.

### 2.3 Evidence and answer status

| REQ | Requirement | Tests | Owner | Status |
|---|---|---|---|---|
| REQ-020 | Display exact source location and excerpt for each candidate | `TEST-E2E-002`, `TEST-UNIT-020` | CTO + CEO | planned |
| REQ-021 | No source location must never be VERIFIED | `TEST-UNIT-020`, `CTO-AC-003` | CTO | planned |
| REQ-022 | Conflicting records for same scope/period marked CONFLICTING; both sources shown | `TEST-E2E-003`, `TEST-UNIT-022` | CTO | planned |
| REQ-023 | Partial coverage marked PARTIAL with the missing coverage explained | `TEST-E2E-003`, `TEST-UNIT-023` | CTO | planned |
| REQ-024 | Evidence outside required period marked OUTDATED with dates shown | `TEST-E2E-003`, `TEST-UNIT-024` | CTO | planned |
| REQ-025 | **AMENDED** — see below | `TEST-E2E-004`, `TEST-UNIT-025` | CTO + COO | planned |
| REQ-026 | Confirmation saves answer, reviewer, timestamp, used evidence IDs | `TEST-E2E-004`, `CTO-AC-005` | CTO | planned |
| REQ-027 | Rejected AI draft saves reason; must not auto-resubmit the same draft | `TEST-UNIT-027` | CTO | planned |

**REQ-025 as written in Main Spec v1.0:**

> "WHEN AI generates an answer without sufficient evidence, THE SYSTEM SHALL mark it AI_SUGGESTED."

**Proposed amended text under `SPEC-AMD-006`:**

> WHEN AI generates an answer without sufficient evidence, THE SYSTEM SHALL set `draft_provenance = AI_GENERATED`, SHALL set `review_status = UNREVIEWED`, SHALL NOT count the answer toward readiness, and SHALL compute `evidence_status` independently from the available evidence — which in this case is `MISSING`.

This is the single requirement where the three-dimension model is most visible: the v1.0 text conflates provenance with evidence availability by assigning one enum value to both.

**Affected by `SPEC-AMD-005`:** REQ-022, REQ-023, and REQ-024 currently define statuses independently, with no rule for what happens when two conditions hold at once. New test `TEST-UNIT-026` asserts the frozen precedence `CONFLICTING > OUTDATED > PARTIAL > VERIFIED` **and** that every non-winning condition is still present in `status_findings`.

New tests required by `SPEC-AMD-005` and the C-15 rule:

| Test | Asserts |
|---|---|
| `TEST-UNIT-028` | An unreadable candidate does **not** suppress a genuine conflict between two other reliable sources |
| `TEST-UNIT-029` | Unreadable OCR output **never** creates a conflict |
| `TEST-UNIT-030A` | `NEEDS_MANUAL_REVIEW` is returned only when the C-15 relevance rule is satisfied; otherwise `MISSING` |
| `TEST-UNIT-030B` | `status_findings` records which `document_type` and which keyword produced the relevance result |
| `TEST-UNIT-030C` | An AI-only relevance recommendation alone never triggers `NEEDS_MANUAL_REVIEW` |

### 2.4 Priority and actions

| REQ | Requirement | Tests | Owner | Status |
|---|---|---|---|---|
| REQ-030 | Display 0–100 priority score, four factors, and reasons | `TEST-E2E-005`, `TEST-UNIT-030` | CTO + CEO | planned |
| REQ-031 | Factor change recalculates total and records the reason | `TEST-UNIT-031`, `CTO-AC-004` | CTO | planned |
| REQ-032 | Converting a gap to an Action requires type, owner, next step, deadline | `TEST-E2E-005` | CTO | planned |
| REQ-033 | COMPLETED requires a note; closure evidence if the Action requires it | `TEST-E2E-005`, `TEST-UNIT-033` | CTO | planned |
| REQ-034 | Invalidated closure evidence returns the Action to NEEDS_REVIEW | `TEST-UNIT-034`, `CTO-AC-006` | CTO | planned |

The priority formula is **protected**:

```text
priority_score = 7*impact + 5*urgency + 4*evidence_gap + 4*feasibility
```

Each factor is an integer 0–5; maximum 100; **computed on the server**. `TEST-UNIT-030` must assert the server ignores any client-supplied score entirely, not merely that it validates it.

REQ-034 is the cascade requirement. It is served by the bounded transitive invalidation cascade: worklist to fixed point, `MAX_ROUNDS = 16`, deterministic lock ordering by `(table_rank, id ASC)`, single transaction, rollback on non-convergence, and the Case boundary enforced by composite foreign keys that make a cross-Case link unrepresentable rather than merely rejected.

Stated honestly: termination rests on the round cap, **not** on a monotonicity proof. Removing a conflict can move a status *up*, so the cascade is not monotone and cannot be argued to terminate on that basis. `TEST-UNIT-035` must assert that exceeding `MAX_ROUNDS` rolls back rather than committing a partial cascade.

### 2.5 Export

| REQ | Requirement | Tests | Owner | Status |
|---|---|---|---|---|
| REQ-040 | Before export, display unresolved conflicts, missing required answers, unconfirmed AI suggestions | `TEST-E2E-006` | CTO + CEO | planned |
| REQ-041 | Customer Response Summary distinguishes confirmed answers, evidence status, assumptions, outstanding items | `TEST-E2E-006` | CTO | planned |
| REQ-042 | Evidence Index includes question ID, document, location, period, scope, review status | `TEST-E2E-006` | CTO | planned |
| REQ-043 | Export failure leaves Case data unchanged and allows retry | `TEST-UNIT-043`, `CTO-AC-007` | CTO | planned |
| REQ-044 | AI Suggested content in a report carries a prominent disclaimer | `TEST-E2E-006` | CEO | planned |

**Affected by `SPEC-AMD-006`:** REQ-044's trigger becomes `draft_provenance IN (AI_GENERATED, AI_ASSISTED_EDIT)`, not an `AI_SUGGESTED` evidence status that no longer exists.

### 2.6 Usability and reliability

| REQ | Requirement | Tests | Owner | Status |
|---|---|---|---|---|
| REQ-050 | Keyboard support for all major review and Action operations except upload | `TEST-A11Y-050` | CEO | planned |
| REQ-051 | Status colors accompanied by text and an icon | `TEST-A11Y-051` | CEO | planned |
| REQ-052 | Network failure during save shows unsaved state; must not falsely report success | `TEST-E2E-008` | CEO + CTO | planned |
| REQ-053 | Refresh restores server-persisted state | `TEST-E2E-008`, `CTO-AC-010` | CTO | planned |

REQ-053 is the requirement that made `SPEC-AMD-001` necessary: without `documents.latest_job_id`, a refreshed client cannot recover the `job_id` and therefore cannot restore processing state at all.

---

## 3. CTO Acceptance Criteria

| ID | Criterion | Tests | Status |
|---|---|---|---|
| `CTO-AC-001` | Same checksum twice in one Case returns the existing document, no duplicate processing | `TEST-E2E-008`, `TEST-API-002` | planned |
| `CTO-AC-002` | AI result failing the shared JSON schema is rejected and recorded as a recoverable failure | `CT-021`, `TEST-UNIT-002` | planned |
| `CTO-AC-003` | Evidence with no valid source location is never persisted as VERIFIED | `TEST-UNIT-020`, `CT-022` | planned |
| `CTO-AC-004` | Out-of-range priority factor rejected; client-calculated score never trusted | `TEST-UNIT-030`, `TEST-API-030` | planned |
| `CTO-AC-005` | Confirmation persists reviewer, timestamp, final text, evidence IDs | `TEST-API-026` | planned |
| `CTO-AC-006` | Invalidated evidence recalculates affected answers and actions | `TEST-UNIT-034`, `TEST-UNIT-035` | planned |
| `CTO-AC-007` | Export failure leaves Case data unchanged and allows retry | `TEST-UNIT-043` | planned |
| `CTO-AC-008` | Repeated mutation with the same Idempotency-Key creates no duplicate business object | `CT-017`, `CT-018` | planned |
| `CTO-AC-009` | A request referencing an object from another Case is rejected | `CT-016`, `TEST-API-009` | planned |
| `CTO-AC-010` | Case, processing, review, and Action state survive an application restart | `TEST-E2E-008` | planned |

---

## 4. Contract Tests

`CT-001` through `CT-010` are inherited from Contract v1.0.0 section 12. `CT-011` through `CT-022` are added by the proposed v1.1.0. All are enumerated in [`contract-test-plan.md`](contract-test-plan.md).

---

## 5. Coverage Gaps Known at Phase 0

These are recorded now rather than discovered during Phase 4.

| Gap | Detail | Blocks |
|---|---|---|
| `E2E-008` missing from the Integration Checklist | Main Spec defines 8 critical tests; the checklist lists 7 | Checklist correction |
| Ground truth does not exist | `fixtures/ground_truth/expected.json` has not been produced | Phase 3 |
| C-15 relevance rule unimplemented | The rule is ruled by the CTO but requires COO confirmation of `document_type` and keyword signals | `SPEC-AMD-005` final signature; Phase 4 |
| Failure-code catalog absent | COO has not supplied the parser and OCR failure codes, or marked each retryable or terminal | REQ-005, `TEST-E2E-007` |
| C-14 undecided | Whether `NOT_APPLICABLE` counts toward the readiness denominator | REQ-041, readiness tests |
| No accessibility test tooling chosen | REQ-050 and REQ-051 have no named harness | CEO decision |

---

**Every row in this document is `planned`. No test exists. Gate P0 is BLOCKED.**
