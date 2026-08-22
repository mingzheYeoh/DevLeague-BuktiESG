# Risk Register

| Field | Value |
|---|---|
| Status | **PROPOSED** |
| Gate P0 | **BLOCKED** |
| Main Spec target | **v1.1 — NOT ACCEPTED** |
| Contract target | **v1.1.0 — NOT FROZEN** |
| Feature implementation | **NOT AUTHORIZED** |
| Date | 2026-08-21 |
| Owner | CTO |

Likelihood and impact are **High / Medium / Low**. No mitigation below has been implemented — implementation is not authorized.

---

## 1. Governance and process

| ID | Risk | L | I | Mitigation | Owner | State |
|---|---|---|---|---|---|---|
| `R-G01` | Gate P0 never clears because three roles are unassigned | **High** | **High** | Assign CEO, COO, Ground-Truth Approver, Release Approver before any other work. This is the top of the critical path. | CEO | **OPEN** |
| `R-G02` | Ground-Truth Approver collides with the COO, making the control decorative | Medium | **High** | Explicit constraint recorded; validate handle inequality on receipt | CEO | **OPEN** |
| `R-G03` | Enforcement is advisory-only and mistaken for real enforcement | **High** | Medium | Stated in README, AGENTS.md, and project-control-status.md. Promote only after controls are verified, and never by the commit that installs them. | CTO | Mitigated in documentation |
| `R-G04` | The first two commits are necessarily unprotected | **High** | Low | Bootstrap gap recorded explicitly. `CODEOWNERS` and branch protection installed immediately after. | CTO | Accepted |
| `R-G05` | An implementer edits protected ground truth to make a test pass | Medium | **High** | `CODEOWNERS` over `fixtures/ground_truth/**`; standing attestation by the Ground-Truth Approver; rule in AGENTS.md | Ground Truth | **OPEN** — no CODEOWNERS |
| `R-G06` | An agent self-approves a migration or security change | Medium | **High** | Red-risk floor: never self-approvable by the implementer. Requires `CODEOWNERS`. | CTO | **OPEN** |
| `R-G07` | Specification conflicts silently resolved by whoever hits them first | Medium | **High** | Eleven found and escalated, not resolved. Rule in AGENTS.md. `E2E-008` remains open. | CTO | Partially mitigated |

---

## 2. Security and privacy

| ID | Risk | L | I | Mitigation | Owner | State |
|---|---|---|---|---|---|---|
| `R-S01` | Real personal data uploaded, triggering T2 | Medium | **High** | Synthetic-data-only restriction in README, AGENTS.md, control status. Written acknowledgement from all three roles. | All | **OPEN** — 0 of 3 acknowledged |
| `R-S02` | A `.env` or credential committed to history | Medium | **High** | `.gitignore` present in the **first** commit, before any secret can exist. A history rewrite is forbidden, so prevention is the only control. | CTO | **Mitigated** |
| `R-S03` | Prompt injection via uploaded document content | **High** | **High** | TB-3: document text is untrusted data, never instructions. Dedicated injection fixture. The model cannot set a status regardless of what it is told. | COO | **OPEN** |
| `R-S04` | Model fabricates a citation and it is persisted | **High** | **High** | The model never supplies a source location. It returns `chunk_id`; the server resolves from `document_chunks`. A fabricated citation cannot resolve. **Structural, not probabilistic.** | CTO | Designed |
| `R-S05` | Model output sets a verdict field | Medium | **High** | Deny-list extended with `evidence_status` and `status_findings`. Presence is a **validation failure**, not a field to strip — stripping teaches the pipeline that emitting it is harmless. `CT-021`. | CTO + COO | Designed |
| `R-S06` | Unauthenticated upload endpoint exposed publicly | Medium | **High** | Local Docker Compose only. No public unauthenticated upload. A public preview requires a platform-level access gate. | CEO | Recommended |
| `R-S07` | Cross-Case data leak through an id from another Case | Medium | **High** | Composite foreign keys make a cross-Case link unrepresentable rather than merely rejected. `CTO-AC-009`, `CT-016`. | CTO | Designed |
| `R-S08` | Secrets or document content leaked into logs | Medium | Medium | structlog with a field deny-list | CTO | Designed |
| `R-S09` | Archive decompression bomb | Low | **High** | 200 MB decompressed cap per archive | CEO | Recommended |

---

## 3. Integration

| ID | Risk | L | I | Mitigation | Owner | State |
|---|---|---|---|---|---|---|
| `R-I01` | Contract v1.0.0 implemented as written and found unimplementable | **High** | **High** | Four defects documented. v1.1.0 proposed. Neither version may be implemented before approval. | CTO | Documented |
| `R-I02` | Generated `CHECK` constraints drift from the contract enums | Medium | **High** | `CT-011` asserts parity in **both** directions. Without it, a value added and not regenerated leaves a schema silently accepting what the contract forbids, and nothing fails until the data is wrong. | CTO | Designed |
| `R-I03` | Three workstreams diverge on shared shapes | **High** | **High** | 22 contract tests; JSON Schema materialization is the first Phase 1 task | CTO | Planned |
| `R-I04` | COO pipeline gains a database session, dissolving the purity boundary | Medium | **High** | `BLOCKER-04`: no session, no persistence, no write path around validation; independently fixture-testable | COO | **OPEN** |
| `R-I05` | Cross-page question ordering broken and undetected | Medium | Medium | Persisted `question_order`; fixture of **more than 20** questions. A 20-question fixture at `page_size = 20` would pass while ordering is broken. | CTO | Designed |
| `R-I06` | Truncated embedded array mistaken for a complete one | Medium | Medium | Named preview objects with `total_count` and `has_more`; never bare arrays | CTO | Designed |
| `R-I07` | Concurrent analyze requests produce duplicate provider calls and duplicate cost | Medium | Medium | Database-enforced partial unique index. Application checks lose races. `CT-018` must use genuine concurrency. | CTO | Designed |

---

## 4. AI and evidence quality

| ID | Risk | L | I | Mitigation | Owner | State |
|---|---|---|---|---|---|---|
| `R-A01` | An unreadable scan masks every genuine conflict in a Case | Medium | **High** | The rejected rank-2 override would have caused exactly this. Four-step model: unreadable evidence is excluded and never suppresses a conflict. | CTO | Designed |
| `R-A02` | Unreadable OCR output fabricates a conflict | Medium | **High** | Explicit rule: unreadable OCR must never create a conflict | CTO | Designed |
| `R-A03` | C-15 relevance rule unimplementable without COO signals | **High** | Medium | Requires `document_type` values and the `keywords` source. Blocks `SPEC-AMD-005` finalization and Phase 4. | COO | **OPEN** |
| `R-A04` | Relevance threshold tuned until a failing test passes | Medium | **High** | C-15 prohibits fuzzy matching, embedding similarity, and LLM classification. Exact token matching has no threshold to tune. | CTO | Designed |
| `R-A05` | AI draft presented to a customer as evidence | Medium | **High** | Three-dimension model. The UI must show "AI Suggested" **and** that evidence is `MISSING`. REQ-044 disclaimer. | CEO | Designed |
| `R-A06` | Keyword-first retrieval misses required evidence | Medium | Medium | Evaluate against protected ground truth. Hybrid requires a recorded decision plus evidence, in either direction. | COO | **OPEN** |

---

## 5. Demo and delivery

| ID | Risk | L | I | Mitigation | Owner | State |
|---|---|---|---|---|---|---|
| `R-D01` | Gate P0 delay consumes the hackathon window | **High** | **High** | CTO packet complete; three packets outstanding. Nothing further can be unblocked from the CTO side. | CEO | **OPEN** |
| `R-D02` | Live provider outage during the demo | Medium | **High** | `FixtureProvider` is both the CI provider and the outage fallback | CTO | Designed |
| `R-D03` | Provider cost exceeds budget mid-demo | Low | Medium | USD 1.60 warning, USD 2.00 hard stop requiring explicit human approval | CTO | Designed |
| `R-D04` | Local-only deployment prevents remote judging | Medium | Medium | Accepted. Strictly better than an open upload endpoint. | CEO | Accepted |
| `R-D05` | Demo shows a status the ground truth does not expect | Medium | **High** | Ground truth is protected and approved by a non-implementer | Ground Truth | **OPEN** |
| `R-D06` | Only 7 of 8 critical E2E tests tracked, because the checklist omits `E2E-008` | Medium | Medium | Discrepancy recorded in traceability.md. Checklist correction **not yet applied.** | CTO | **OPEN** |

---

## 6. Cost, dependency, and licensing

| ID | Risk | L | I | Mitigation | Owner | State |
|---|---|---|---|---|---|---|
| `R-C01` | Provider price change silently rewrites historical cost records | Low | Medium | Pricing version and date stored per AI Run. Cost computed from actual usage, never re-derived. | CTO | Designed |
| `R-C02` | Live provider called in CI, incurring cost per run | Medium | Medium | **Never use the live provider in CI.** A test that costs money is a test that gets skipped. | CTO | Designed |
| `R-C03` | Docling or OCR dependency unavailable on the chosen Python version | Medium | Medium | Python 3.12.x chosen over 3.13 for wheel availability | CTO | Mitigated |
| `R-C04` | Dependency introduced without review | Medium | Medium | Lockfiles are protected files requiring non-author review | CTO | **OPEN** — no CODEOWNERS |
| `R-C05` | Project licence undetermined | **High** | Low | No licence chosen. Required before the repository is made public. | CEO | **OPEN** |

---

## Summary

| Severity | Count | Notes |
|---|---|---|
| Open, high impact | 12 | Dominated by unassigned roles and missing `CODEOWNERS` |
| Designed, not implemented | 16 | Implementation is not authorized |
| Mitigated now | 3 | `.gitignore` in the first commit; Python 3.12; advisory-only stated |
| Accepted | 2 | Bootstrap gap; local-only deployment |

**The single highest-leverage action is naming the Ground-Truth Approver and the CEO.** Almost every open high-impact risk traces back to an unassigned role, and no amount of further CTO work reduces any of them.
