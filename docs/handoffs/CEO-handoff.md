# CEO Decision Packet

| Field | Value |
|---|---|
| Status | **PROPOSED** |
| Gate P0 | **BLOCKED** |
| Main Spec target | **v1.1 — NOT ACCEPTED** |
| Contract target | **v1.1.0 — NOT FROZEN** |
| Feature implementation | **NOT AUTHORIZED** |
| From | CTO — Backend & Integration Lead (`mingzheYeoh`) |
| To | CEO — Product & Frontend Lead |
| Role owner | **UNASSIGNED — workstream not started** |
| Packet state | **NOT RECEIVED** |
| Decisions in this packet | **31** |
| Decisions recorded | **0** |
| Date issued | 2026-08-21 |

---

## Nothing in this document has been approved

**Every decision below is `PENDING`.**

No decision has been inferred, simulated, assumed, defaulted, or recorded on the CEO's behalf. A "CTO recommendation" column exists so the role owner can respond quickly — it is **advice, not a pre-filled answer**, and it carries no approval weight whatsoever.

The CEO workstream has not started. This packet exists so that when a role owner is assigned, every decision they own is already in one place with the context needed to make it.

---

## How to respond

For each decision ID, reply with exactly one of:

```text
APPROVE   accept the CTO recommendation as written
AMEND     accept with changes  (state the change)
REJECT    do not accept        (state what to do instead)
```

One packet may answer many IDs at once. Partial packets are accepted and recorded item by item. **Any ID left unanswered stays `PENDING`.**

Send responses to the CTO. They will be recorded in [`../decisions/decision-register.md`](../decisions/decision-register.md) and in the signature blocks in [`../spec/AMENDMENTS.md`](../spec/AMENDMENTS.md).

---

## Section A — Product decisions

| ID | Decision | CTO recommendation | Status |
|---|---|---|---|
| `CEO-D01` | Product name | Keep **BuktiESG** | **PENDING** |
| `CEO-D02` | UI language | **English** | **PENDING** |
| `CEO-D03` | Demo scope | **20 questions, 12 required** | **PENDING** |
| `CEO-D04` | Data retention | Manual delete; purge script exists but is unscheduled | **PENDING** |
| `CEO-D05` | Error-tracking service | **None** in the MVP | **PENDING** |
| `CEO-D06` | Accessibility test harness for REQ-050 and REQ-051 | **No recommendation** — tooling choice is yours | **PENDING** |
| `CEO-D07` | Project licence | **No recommendation** — required before the repository is made public | **PENDING** |

### `CEO-D08` — File and processing limits (`BLOCKER-05`) — **PENDING**

| Limit | CTO recommendation |
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

These bound the demo's worst case. The decompression cap is a **security control**, not a convenience limit — without it an archive bomb is a trivial denial of service against a system that has no authentication.

Any individual value may be amended; state which.

### `CEO-D09` — Deployment target (`BLOCKER-07`) — **PENDING**

**CTO recommendation:** local Docker Compose is the demo path of record. **No unauthenticated upload endpoint may be exposed publicly.**

The application has no authentication by design at T1. A public URL would therefore be an open, anonymous file-processing service that anyone on the internet could upload to. A public preview remains possible later, but it requires a platform-level access gate first.

**Consequence to weigh:** remote judges cannot click a link. If the hackathon format requires that, say so — the answer is a platform access gate, not lifting the restriction.

### `CEO-D10` — Export type and format combinations — **PENDING**

| ExportType | PDF | XLSX | CSV |
|---|:---:|:---:|:---:|
| `CUSTOMER_RESPONSE_SUMMARY` | yes | no | no |
| `EVIDENCE_INDEX` | no | yes | yes |
| `OUTSTANDING_ACTIONS_SUMMARY` | yes | yes | yes |

`ExportType` is **what artifact is produced**. `ExportFormat` is **its file format**. Which artifact ships in which format is a product decision, which is why it is yours.

### `CEO-D11` — `C-14`: readiness and `NOT_APPLICABLE` — **PENDING**

The readiness formula is protected:

```text
readiness = confirmed_required_questions / total_required_questions * 100
```

Only `HUMAN_CONFIRMED` required answers count. **A required question a human has marked `NOT_APPLICABLE` is resolved but never confirmed** — so it can never be counted, and readiness is permanently capped below 100% for any Case containing one. In the demo this will look like a bug.

**CTO recommendation:**

```text
resolved_required_questions
  = human_confirmed_required_answers
  + human_confirmed_not_applicable_required_questions
```

Denominator unchanged. `NOT_APPLICABLE` is human-set and carries a reason and a reviewer identity, so it is a human decision of the same weight as a confirmation — which is the property the formula actually cares about.

**Required before Phase 4.**

---

## Section B — Co-approval of the specification and contract change set

Main Spec and Contract change control requires **CEO + CTO + COO**. The CTO position is recorded. **Yours is PENDING on every line.**

| ID | Item | CTO position | Status |
|---|---|---|---|
| `CEO-D12` | `BLOCKER-01` — English Main Spec normative; Chinese non-normative | RULED | **PENDING** |
| `CEO-D13` | `BLOCKER-02` — map ownership paths into section 16; no duplicate top-level trees | RULED | **PENDING** |
| `CEO-D14` | `BLOCKER-06` — keyword-first retrieval; pgvector installed but unused | RULED | **PENDING** |
| `CEO-D15` | `RULING-01` — Job and Export concepts; Contract v1.1.0; four enums; no native PG ENUM | AMEND | **PENDING** |
| `CEO-D16` | `RULING-02` — Evidence Status evaluation model | AMEND | **PENDING** |
| `CEO-D17` | `RULING-03` — `AI_SUGGESTED` removed; `DraftProvenance` added | AMEND | **PENDING** |
| `CEO-D18` | `RULING-04` — persisted `question_order` | AMEND | **PENDING** |
| `CEO-D19` | `RULING-05` — named previews and the activity endpoint | APPROVE | **PENDING** |
| `CEO-D20` | `RULING-06` — idempotency and database-enforced concurrency | APPROVE | **PENDING** |
| `CEO-D21` | `RULING-07` — amendments recorded individually; Main Spec v1.1 | APPROVE | **PENDING** |
| `CEO-D22` | `C-15` — deterministic unreadable-document relevance rule | RULED | **PENDING** |
| `CEO-D23` | `SPEC-AMD-001` — `processing_jobs` and `documents.latest_job_id` | APPROVED | **PENDING** |
| `CEO-D24` | `SPEC-AMD-002` — evidence extraction provenance fields | APPROVED | **PENDING** |
| `CEO-D25` | `SPEC-AMD-003` — AI schema as a compatible superset | APPROVED AS AMENDED | **PENDING** |
| `CEO-D26` | `SPEC-AMD-004` — repository path reconciliation | APPROVED | **PENDING** |
| `CEO-D27` | `SPEC-AMD-005` — Evidence Status evaluation model | APPROVED AS AMENDED | **PENDING** |
| `CEO-D28` | `SPEC-AMD-006` — three-dimension model and `DraftProvenance` | APPROVED AS AMENDED | **PENDING** |
| `CEO-D29` | `SPEC-AMD-007` — `questions.question_order` | APPROVED | **PENDING** |
| `CEO-D30` | `SPEC-AMD-008` — `GET /cases/{case_id}/activity` | APPROVED | **PENDING** |

### The two items that most affect what users see

**`CEO-D17` / `RULING-03`** resolves an apparent contradiction in the Main Spec: 18.2 says the GHG fixture produces `MISSING`, while 20 shows the demo displaying an "AI Suggested GHG answer". These are **not** in conflict — they describe different dimensions. `MISSING` is about **evidence availability**; "AI Suggested" is about **where the draft text came from**. Placing both inside one enum forced them to compete for a single slot.

The UI consequence is direct: an AI-drafted answer with no evidence must show **both** the "AI Suggested" label **and** that the supporting evidence is `MISSING`. Showing only the first would let the demo imply the system found evidence it did not find — precisely what this product exists not to do.

**`CEO-D19` / `RULING-05`** changes detail-response shapes. Evidence and activity arrive as `{ items, total_count, has_more }`, never as bare arrays. A truncated bare array is indistinguishable from a complete one, so the frontend would have no way to know it was rendering partial data.

---

## Section C — Roles and identities — highest priority

| ID | Item | Status |
|---|---|---|
| `CEO-D31` | Assign all roles and supply GitHub identities | **PENDING** |

```text
Product Owner                       = PENDING
Tech Owner                          = PENDING
Demo Presenter                      = PENDING
CEO_GITHUB_HANDLE                   = PENDING
COO_GITHUB_HANDLE                   = PENDING
GROUND_TRUTH_APPROVER_GITHUB_HANDLE = PENDING   # must NOT equal COO_GITHUB_HANDLE
RELEASE_APPROVER                    = PENDING   # name and handle; must not be the implementer
```

Already resolved: `GITHUB_REPOSITORY_OWNER = mingzheYeoh`; `CTO_GITHUB_HANDLE = mingzheYeoh`.

**These values have not been guessed and will not be.**

Two constraints, each of which makes a control decorative if violated:

- The **Ground-Truth Approver must not be the COO**. The COO prepares ground truth; a preparer approving their own expected values is not an independent check.
- The **Release Approver must not be the implementer**.

Until all four handles are supplied, `.github/CODEOWNERS` cannot be written, branch protection has nothing meaningful to enforce, and `BLOCKER-03` stays blocked.

**This is the top of the critical path.** Four amendment signatures are gated on the Ground-Truth Approver simply existing.

---

## Section D — Written acknowledgements

| Item | Status |
|---|---|
| Synthetic-data-only restriction | **PENDING — NOT RECORDED** |
| Scope and non-goals sign-off | **PENDING — NOT RECORDED** |

The synthetic-data acknowledgement is required in writing from the CEO, CTO, and COO. **Zero of three recorded.**

---

## What happens after this packet is returned

```text
CEO packet + COO packet + Ground-Truth packet
        -> decision register updated with the recorded answers
        -> Main Spec v1.1 and Contract v1.1.0 would then be frozen
        -> Gate P0 could then be accepted
        -> Phase 1 authorized: JSON Schema materialization, then the first vertical slice
```

**Nothing in Phase 1 starts before all three packets arrive.**

---

## Reference

- [`../decisions/decision-register.md`](../decisions/decision-register.md) — full register; section 6.1 itemizes this packet
- [`../decisions/CTO-RULINGS.md`](../decisions/CTO-RULINGS.md) — full ruling text
- [`../spec/AMENDMENTS.md`](../spec/AMENDMENTS.md) — the eight amendments with signature blocks
- [`../spec/BuktiESG-Technical-Spec-EN.md`](../spec/BuktiESG-Technical-Spec-EN.md) — normative Main Spec (v1.0 body)
- [`../risks/risk-register.md`](../risks/risk-register.md) — open high-impact risks, most traceable to unassigned roles
- [`../decisions/GATE-P0-APPROVAL.md`](../decisions/GATE-P0-APPROVAL.md) — **UNSIGNED**

---

**31 decisions. 31 PENDING. 0 recorded. Gate P0 is BLOCKED.**
