# Contract Test Plan

| Field | Value |
|---|---|
| Status | **PROPOSED** |
| Gate P0 | **BLOCKED** |
| Contract target | **v1.1.0 — NOT FROZEN** |
| Main Spec target | **v1.1 — NOT ACCEPTED** |
| Feature implementation | **NOT AUTHORIZED** |
| Tests written | **Zero.** |

**No test file exists.** This plan defines what must be verified once implementation is authorized. It is written now so that the contract is testable before anyone writes code against it — an untestable clause in a contract is a clause that will be interpreted differently by each workstream.

---

## Purpose

Contract tests protect the boundary between the three workstreams. They are not unit tests of business logic. Each one answers a single question: **can the frontend, backend, and AI pipeline still agree on a shape?**

A contract test must fail when a workstream unilaterally changes a shared shape. If it can pass while the shapes have diverged, it is not a contract test.

---

## Inherited from Contract v1.0.0

| ID | Asserts | Owner |
|---|---|---|
| `CT-001` | All IDs are opaque strings; no endpoint requires a client to parse an ID | CTO |
| `CT-002` | All timestamps are ISO 8601 UTC with a `Z` suffix | CTO |
| `CT-003` | Enum values are uppercase snake case and match the contract exactly | CTO |
| `CT-004` | Optional values are `null`; a missing required field fails validation | CTO |
| `CT-005` | An AI result is validated against the JSON Schema **before** persistence, not after | CTO + COO |
| `CT-006` | Frontend requests are validated by the API and never trusted | CTO |
| `CT-007` | No response exposes secrets, internal server paths, provider credentials, or another Case's data | CTO |
| `CT-008` | The error envelope shape is identical across every error code | CTO |
| `CT-009` | Every documented error code is reachable by at least one request | CTO |
| `CT-010` | A breaking change without a version bump fails the build | CTO |

---

## Added by proposed Contract v1.1.0

| ID | Asserts | Owner | Why it matters |
|---|---|---|---|
| `CT-011` | The `CHECK` constraint value set equals the contract enum value set, in both directions | CTO | Enums are stored as `text` with generated `CHECK` constraints rather than native PostgreSQL ENUM types. That preserves the "unknown value is unstorable" guarantee **only if generation is verified.** Without this test, a value added to the contract and not regenerated leaves a schema that silently accepts what the contract forbids, and nothing fails until the data is already wrong. |
| `CT-012` | An unknown enum value returns `ENUM_COMPATIBILITY_ERROR`, never a silent fallback | CTO | Contract rule 6. A fallback turns a version mismatch into corrupted data. |
| `CT-013` | Out-of-range `page` or `page_size` returns `400`, and is **not** clamped | CTO | A clamped page returns data the client did not request and cannot detect. |
| `CT-014` | `GET /cases/{id}/questions` returns `question_order ASC, id ASC` across a fixture of **more than 20 questions**, spanning at least two pages | CTO | The fixture must exceed one page or cross-page ordering is never exercised. A 20-question fixture with `page_size = 20` would pass while the ordering is broken. |
| `CT-015` | `evidence_preview.has_more` is `true` whenever `total_count` exceeds the cap, and `items` length never exceeds it | CTO | A truncated array that claims completeness is worse than an error. |
| `CT-016` | `GET /cases/{id}/activity` returns `404` for an `entity_id` outside the Case | CTO | Must be `404`, not an empty `200`. An empty success hides the boundary violation from both the client and the audit log. |
| `CT-017` | Same `Idempotency-Key` with a different payload returns `409 IDEMPOTENCY_KEY_REUSED` | CTO | |
| `CT-018` | Concurrent analyze requests produce **exactly one** AI Run and **exactly one** provider call | CTO | Must be tested with genuine concurrency against the database, not sequentially. A sequential test passes even when the application-level guard loses every race. |
| `CT-019` | An invalid job status transition returns `409 INVALID_STATE_TRANSITION` **and leaves the row unmutated** | CTO | Both halves matter. A rejected transition that still wrote a timestamp is a silent corruption. |
| `CT-020` | A disallowed `ExportType` and `ExportFormat` pair returns `400` and the detail lists the allowed formats | CTO + CEO | A client must never have to discover the table by trial and error. |
| `CT-021` | An AI response containing `evidence_status`, `status_findings`, or any forbidden field **fails schema validation** | CTO + COO | It must fail, not be stripped. Stripping teaches the pipeline that emitting a forbidden field is harmless. |
| `CT-022` | A model-supplied source location is ignored; the server resolves it from `chunk_id` | CTO + COO | The test must send a response containing a plausible but fabricated location and assert the persisted value came from `document_chunks`. |

---

## Fixtures required

None of these exist. All must contain **synthetic data only**.

| Fixture | Purpose | Owner |
|---|---|---|
| `questionnaire_20.xlsx` | The demo questionnaire: 20 questions, 12 required | COO |
| `questionnaire_25plus.xlsx` | More than 20 questions, to exercise `CT-014` across pages | COO |
| `ai_response_valid.json` | A schema-valid AI analysis result | COO |
| `ai_response_forbidden_field.json` | Contains `evidence_status`; must fail `CT-021` | COO |
| `ai_response_fabricated_location.json` | Contains an invented source location; must fail `CT-022` | COO |
| `prompt_injection.pdf` | A document whose text attempts to instruct the model; asserts trust boundary TB-3 | COO |
| `unreadable_scan.pdf` | OCR produces invalid output; exercises `TEST-UNIT-028`, `TEST-UNIT-029` | COO |
| `conflicting_pair/` | Two reliable sources that genuinely disagree | COO |
| `ground_truth/expected.json` | **Protected.** Expected values for every fixture. | COO prepares; **Ground-Truth Approver** approves |

---

## Execution rules

1. **CI must never call the live provider.** The `FixtureProvider` is the only provider permitted in CI. A contract test that costs money is a contract test that will be skipped.
2. Contract tests run against a real PostgreSQL instance, not a mock. `CT-011`, `CT-018`, and `CT-019` are meaningless without a real database — they test constraints and races that only a database can enforce.
3. `CT-018` must use genuine concurrency.
4. Ground truth is **protected**. An implementing agent must never edit `expected.json` to make a test pass. If an implementation disagrees with ground truth, the implementation is wrong until a human rules otherwise.
5. A contract test failure blocks merge. It is never marked expected-to-fail.

---

## Not yet decidable

| Item | Blocked on |
|---|---|
| Parser and OCR failure codes, each marked retryable or terminal | COO |
| `document_chunks` field shape | COO |
| `ExtractionMethod` enum values | COO |
| C-15 relevance signals — `document_type` mapping and keyword source | COO |
| Accessibility test harness for REQ-050 and REQ-051 | CEO |
| Whether `NOT_APPLICABLE` counts toward the readiness denominator (C-14) | CEO |

---

**No test exists. Gate P0 is BLOCKED.**
