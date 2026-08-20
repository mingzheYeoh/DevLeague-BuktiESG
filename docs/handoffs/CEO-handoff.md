# CEO Handoff — Decisions Required

| Field | Value |
|---|---|
| Status | **PROPOSED** |
| Gate P0 | **BLOCKED** |
| Main Spec target | **v1.1 — NOT ACCEPTED** |
| Contract target | **v1.1.0 — NOT FROZEN** |
| Feature implementation | **NOT AUTHORIZED** |
| From | CTO — Backend & Integration Lead |
| To | CEO — Product & Frontend Lead |
| Date | 2026-08-21 |

---

## Summary

The CTO has ruled on everything within CTO authority. **Nothing further can be unblocked from the backend side.** Gate P0 now waits on one consolidated approval packet from you, one from the COO, and one from a Ground-Truth Approver who has not yet been named.

Every item below carries a CTO recommendation, so the fastest path is to confirm, amend, or reject each line rather than to design from scratch.

**The single highest-leverage decision is section C: naming the roles.** Four amendment signatures are gated on the Ground-Truth Approver existing at all.

---

## A. Product decisions

| # | Decision | CTO recommendation | Your call |
|---|---|---|---|
| A1 | Product name | Keep **BuktiESG** | `APPROVE` / `AMEND` / `REJECT` |
| A2 | UI language | **English** | |
| A3 | Demo scope | **20 questions, 12 required** | |
| A4 | Retention | Manual delete; purge script exists but is unscheduled | |
| A5 | Error tracking | **None** in the MVP | |
| A6 | Accessibility harness for REQ-050 and REQ-051 | No recommendation — your choice of tooling | |

### A7. File and processing limits — `BLOCKER-05`

| Limit | Recommended |
|---|---|
| Maximum file size | 20 MB |
| Maximum total per Case | 100 MB |
| Supported file types | 6 |
| Maximum PDF pages | 100 |
| Maximum rows per spreadsheet | 50,000 |
| Maximum decompressed size per archive | 200 MB |
| Parse timeout | 180 s |
| OCR timeout | 300 s |
| Maximum documents per Case | 30 |

These bound the demo's worst case. The decompression cap is a security control, not a convenience limit — without it an archive bomb is a trivial denial of service.

### A8. Deployment — `BLOCKER-07`

**Recommendation: local Docker Compose is the demo path of record. No unauthenticated upload endpoint may be exposed publicly.**

The application has no authentication by design at T1. A public URL would therefore be an open, anonymous file-processing service that anyone could upload to. A public preview remains possible later, but it requires a platform-level access gate first.

**Consequence you should weigh:** remote judges cannot click a link. If that matters for the hackathon format, say so now — the answer is a platform access gate, not removing the restriction.

### A9. Export combinations

| ExportType | PDF | XLSX | CSV |
|---|:---:|:---:|:---:|
| `CUSTOMER_RESPONSE_SUMMARY` | yes | no | no |
| `EVIDENCE_INDEX` | no | yes | yes |
| `OUTSTANDING_ACTIONS_SUMMARY` | yes | yes | yes |

`ExportType` is **what artifact is produced**. `ExportFormat` is **its file format**. Which artifact ships in which format is a product decision, which is why it is yours.

### A10. `C-14` — readiness and NOT_APPLICABLE

The readiness formula is protected:

```text
readiness = confirmed_required_questions / total_required_questions * 100
```

Only `HUMAN_CONFIRMED` required answers count. **A required question a human has marked `NOT_APPLICABLE` is resolved but never confirmed** — so it can never be counted, and readiness is permanently capped below 100% for any Case containing one. In the demo this looks like a bug.

**CTO recommendation:**

```text
resolved_required_questions
  = human_confirmed_required_answers
  + human_confirmed_not_applicable_required_questions
```

Denominator unchanged. `NOT_APPLICABLE` is human-set and carries a reason and a reviewer identity, so it is a human decision of the same weight as a confirmation — which is the property the formula actually cares about.

**Required before Phase 4.**

---

## B. Co-approval of the specification and contract change set

Main Spec and Contract change control requires **CEO + CTO + COO**. The CTO position is recorded; yours is needed on each line.

| Item | CTO | Your call |
|---|---|---|
| `BLOCKER-01` — English Main Spec normative, Chinese non-normative | RULED | |
| `BLOCKER-02` — map ownership paths into section 16, no duplicate top-level trees | RULED | |
| `BLOCKER-06` — keyword-first retrieval, pgvector installed but unused | RULED | |
| `RULING-01` — Job and Export concepts; Contract v1.1.0; four enums; no native PG ENUM | AMEND | |
| `RULING-02` — Evidence Status evaluation model | AMEND | |
| `RULING-03` — `AI_SUGGESTED` removed; `DraftProvenance` added | AMEND | |
| `RULING-04` — persisted `question_order` | AMEND | |
| `RULING-05` — named previews and the activity endpoint | APPROVE | |
| `RULING-06` — idempotency and database-enforced concurrency | APPROVE | |
| `RULING-07` — amendments recorded individually; Main Spec v1.1 | APPROVE | |
| `SPEC-AMD-001` … `SPEC-AMD-008` | see AMENDMENTS.md | one call per amendment |
| `C-15` — deterministic unreadable-document relevance rule | RULED | |

### The two that most affect what users see

**`RULING-03`** resolves an apparent contradiction in the Main Spec: 18.2 says the GHG fixture produces `MISSING`, while 20 shows the demo displaying an "AI Suggested GHG answer". These are not in conflict — they describe different dimensions. `MISSING` is about **evidence availability**; "AI Suggested" is about **where the draft text came from**. Placing both in one enum forced them to compete for one slot.

The UI consequence is direct: an AI-drafted answer with no evidence must show **both** the "AI Suggested" label **and** that the supporting evidence is `MISSING`. Showing only the first would let the demo imply the system found evidence it did not find — which is exactly what this product exists not to do.

**`RULING-05`** changes detail-response shapes. Evidence and activity arrive as `{ items, total_count, has_more }`, never as bare arrays. A truncated bare array is indistinguishable from a complete one, so the frontend would have no way to know it was showing partial data.

---

## C. Roles and identities — highest priority

```text
Product Owner                       = PENDING
Tech Owner                          = PENDING
Demo Presenter                      = PENDING
CEO_GITHUB_HANDLE                   = PENDING
COO_GITHUB_HANDLE                   = PENDING
GROUND_TRUTH_APPROVER_GITHUB_HANDLE = PENDING   # must NOT equal COO_GITHUB_HANDLE
RELEASE_APPROVER                    = PENDING   # name and handle; must not be the implementer
```

Resolved: `GITHUB_REPOSITORY_OWNER = mingzheYeoh`; `CTO_GITHUB_HANDLE = mingzheYeoh`.

**These have not been guessed and will not be.**

Two constraints, each of which makes a control decorative if violated:

- The **Ground-Truth Approver must not be the COO**. The COO prepares ground truth; a preparer approving their own expected values is not an independent check.
- The **Release Approver must not be the implementer**.

Until all four are supplied, `.github/CODEOWNERS` cannot be written, branch protection has nothing to enforce, and `BLOCKER-03` stays blocked.

---

## D. Written acknowledgements

| Item | State |
|---|---|
| Synthetic-data-only restriction | **NOT RECORDED** |
| Scope and non-goals sign-off | **NOT RECORDED** |

---

## What happens after you respond

```text
Your packet + COO packet + Ground-Truth packet
        -> decision register updated
        -> Main Spec v1.1 and Contract v1.1.0 would then be frozen
        -> Gate P0 could then be accepted
        -> Phase 1 authorized: JSON Schema materialization, then the first vertical slice
```

Nothing in Phase 1 starts before all three packets arrive.

---

## Reference

- [`../decisions/decision-register.md`](../decisions/decision-register.md) — full register, section 6.1 itemizes your packet
- [`../decisions/CTO-RULINGS.md`](../decisions/CTO-RULINGS.md) — full ruling text
- [`../spec/AMENDMENTS.md`](../spec/AMENDMENTS.md) — the eight amendments with signature blocks
- [`../risks/risk-register.md`](../risks/risk-register.md) — 12 open high-impact risks, most traceable to unassigned roles
- [`../decisions/GATE-P0-APPROVAL.md`](../decisions/GATE-P0-APPROVAL.md) — **unsigned**

**Gate P0 is BLOCKED.**
