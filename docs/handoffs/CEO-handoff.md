# CEO Decision Packet

> **Restoration note — added 2026-08-22 by the CEO agent.** This file was restored, uncommitted, from git history (pre-delete commit `4fa92d4`) after an unexplained deletion of this file on `main` earlier today in commit `14bdf33`. The deletion itself is unexplained and has not been confirmed with the repository owner (`mingzheYeoh`). This restoration is a **draft to re-validate, not settled fact**. Deletion confirmed intentional in a live session on 2026-08-22 by COO Lai Yoke Yau (new documentation approach per `mingzheYeoh`) — not yet a written confirmation from `mingzheYeoh` himself. Restoration content below proceeds on that basis.

> **Autonomous-mode addendum — added 2026-08-22 by the CEO agent.** The project has moved to fully autonomous decision-making: no human role-holder will sign off CEO decisions. Per explicit operating instruction, the CEO agent is authorized to **finalize** — not merely draft — every still-open `CEO-Dxx` decision directly from the spec. Every finalization below is attributed to **"CEO Agent — autonomous decision, no human role assigned, 2026-08-22."** This is an agent decision, not a human sign-off, and no human named "CEO" exists or has approved anything. This authorization does **not** extend to the separately-flagged Ground-Truth Approver / Release Approver identity question (stays open, out of scope, see `CEO-D31`), and does **not** lift Gate P0's block on feature implementation — feature implementation remains **NOT AUTHORIZED**; this remains a documentation-only action inside `docs/decisions/**` and `docs/handoffs/CEO-handoff.md`.

| Field | Value |
|---|---|
| Status | **PROPOSED** |
| Gate P0 | **BLOCKED** |
| Main Spec target | **v1.1 — NOT ACCEPTED** |
| Contract target | **v1.1.0 — NOT FROZEN** |
| Feature implementation | **NOT AUTHORIZED** |
| From | CTO — Backend & Integration Lead (`mingzheYeoh`) |
| To | CEO — Product & Frontend Lead |
| Role owner | **N/A — fully autonomous operation; no human role-holder assigned (see `CEO-D31`)** |
| Packet state | **AGENT-FINALIZED — not a human Gate P0 sign-off** |
| Decisions in this packet | **31** |
| Decisions finalized (agent) | **31** (30 substantive decisions; `CEO-D31` finalized as N/A / structural gap, not an identity assignment) |
| Date issued | 2026-08-21 |
| Date agent-finalized | 2026-08-22 |

---

## Decision status — agent-finalized, not a human approval

**Every decision below has been finalized by the CEO agent under the autonomous-decision-making mode adopted 2026-08-22.** None of it is a human CEO's sign-off — there is no human assigned to this role. Where a decision rests on spec text, prior CTO ruling, or internal consistency, it is finalized as a spec-grounded call. Where a decision would normally depend on institutional preference or a fact only a human could supply (for example, licence intent or hackathon submission logistics), that dependency is named explicitly in the item itself so it stays visible rather than being quietly absorbed into "the CEO decided this."

This finalization does **not**:
- accept Gate P0 (Gate P0 remains **BLOCKED** — it also requires CTO, COO, and Ground-Truth Approver packets, and the Ground-Truth Approver role remains unassigned);
- authorize feature implementation (still **NOT AUTHORIZED** under `AGENTS.md` §1);
- invent a human identity, name, or GitHub handle for any role (see `CEO-D31`).

---

## Section A — Product decisions

**Finalized 2026-08-22 by the CEO agent (autonomous decision, no human role assigned).** The former "agent draft" column is now the finalized decision; the former blanket `PENDING` status is now `FINALIZED` per item, with any agent-judgment-call flagged inline.

| ID | Decision | CTO recommendation | Finalized decision — CEO Agent, autonomous, 2026-08-22 | Status |
|---|---|---|---|---|
| `CEO-D01` | Product name | Keep **BuktiESG** | **DECIDED:** keep **BuktiESG**. | **FINALIZED** |
| `CEO-D02` | UI language | **English** | **DECIDED:** **English**. | **FINALIZED** |
| `CEO-D03` | Demo scope | **20 questions, 12 required** | **DECIDED:** 20 questions, 12 required. | **FINALIZED** |
| `CEO-D04` | Data retention | Manual delete; purge script exists but is unscheduled | **DECIDED:** manual delete remains the mechanism; the purge script is scheduled weekly rather than left indefinitely manual. Scheduling cadence only — no change to the delete mechanism itself. | **FINALIZED** |
| `CEO-D05` | Error-tracking service | **None** in the MVP | **DECIDED:** none in the MVP — matches T1 scope and the "no unauthorized service" posture. | **FINALIZED** |
| `CEO-D06` | Accessibility test harness for REQ-050 and REQ-051 | **No recommendation** — tooling choice is yours | **DECIDED:** axe-core wired into the existing Playwright E2E suite (`TEST-E2E-001`..`008`) rather than a separate harness — avoids a second test runner. **Agent-judgment flag:** this was explicitly left as a human CEO's tooling preference in the prior draft; no human owner exists to make that call, so the agent is deciding it now on engineering-economy grounds (avoid a second test runner), not from a discovered spec fact. | **FINALIZED** |
| `CEO-D07` | Project licence | **No recommendation** — required before the repository is made public | **DECIDED:** all-rights-reserved / private for the duration of the hackathon; an OSS licence is out of scope until after judging concludes, at which point the repository owner (`mingzheYeoh`) may revisit it. **Agent-judgment flag:** licence intent is a business/legal preference a human institution would normally set; there is no human CEO to consult, so this is the agent's conservative default (keep rights reserved, decide later), not a fact discovered in the spec. | **FINALIZED** |

### `CEO-D08` — File and processing limits (`BLOCKER-05`) — **FINALIZED**

| Limit | CTO recommendation | Finalized value |
|---|---|---|
| Maximum file size | 20 MB | 20 MB |
| Maximum total per Case | 100 MB | 100 MB |
| Supported file types | 6 | 6 |
| Maximum PDF pages | 100 | 100 |
| Maximum rows per spreadsheet | 50,000 | 50,000 |
| Maximum decompressed size per archive | 200 MB | 200 MB |
| Parse timeout | 180 s | 180 s |
| OCR timeout | 300 s | 300 s |
| Maximum documents per Case | 30 | 30 |

**DECIDED (CEO Agent, autonomous, 2026-08-22):** all nine CTO-recommended values accepted as given — they match the limits already reflected in the Main Spec (`docs/spec/BuktiESG-Technical-Spec-EN.md`: 20 MB per file, 100 MB per Case), so accepting them creates no new conflict with the spec. No amendment. This is a spec-grounded finalization, not an institutional-preference call.

### `CEO-D09` — Deployment target (`BLOCKER-07`) — **FINALIZED**

**CTO recommendation:** local Docker Compose is the demo path of record. **No unauthenticated upload endpoint may be exposed publicly.**

**DECIDED (CEO Agent, autonomous, 2026-08-22):** local Docker Compose as the demo path of record; no public unauthenticated upload endpoint. This is the conservative default given the system has no authentication by design at T1 — a public URL would be an open, anonymous file-processing service reachable by anyone.

**Agent-judgment flag:** whether remote judges need a clickable link is a fact only a human institution (the hackathon organizer's submission format) can supply, and no human is available to confirm it. The agent is **not** guessing at the hackathon's requirements. This decision finalizes the safe default (no public unauthenticated endpoint); if the hackathon format turns out to require remote access, the fix is a platform-level access gate in front of the existing deployment, not lifting this restriction. That remains an open follow-up item, not resolved here.

### `CEO-D10` — Export type and format combinations — **FINALIZED**

| ExportType | PDF | XLSX | CSV |
|---|:---:|:---:|:---:|
| `CUSTOMER_RESPONSE_SUMMARY` | yes | no | no |
| `EVIDENCE_INDEX` | no | yes | yes |
| `OUTSTANDING_ACTIONS_SUMMARY` | yes | yes | yes |

**DECIDED (CEO Agent, autonomous, 2026-08-22):** table accepted as given.

### `CEO-D11` — `C-14`: readiness and `NOT_APPLICABLE` — **FINALIZED**

The readiness formula is protected:

```text
readiness = confirmed_required_questions / total_required_questions * 100
```

**CTO recommendation:**

```text
resolved_required_questions
  = human_confirmed_required_answers
  + human_confirmed_not_applicable_required_questions
```

Denominator unchanged.

**DECIDED (CEO Agent, autonomous, 2026-08-22):** agree with the CTO recommendation on the product question — a required question a human has correctly marked `NOT_APPLICABLE` should not permanently cap readiness below 100%. **Scope note (unchanged by finalization):** per `AGENTS.md` §3.5 the readiness formula is a protected value. This item finalizes the CEO's product-level position only; the actual numerator/formula change still requires CTO implementation — this is not a self-authorization to edit the protected formula. **Required before Phase 4.**

---

## Section B — Co-approval of the specification and contract change set

Main Spec and Contract change control requires **CEO + CTO + COO**. The CTO position is recorded below. **The CEO position is now finalized** (agent decision, autonomous mode, 2026-08-22) — this is the CEO's share of co-approval; it does not by itself complete co-approval, which still needs the COO and CTO positions (recorded separately in their own packets) and, for Ground-Truth-linked items, the Ground-Truth Approver, a role that remains unassigned.

| ID | Item | CTO position | Finalized decision — CEO Agent, autonomous, 2026-08-22 | Status |
|---|---|---|---|---|
| `CEO-D12` | `BLOCKER-01` — English Main Spec normative; Chinese non-normative | RULED | **DECIDED:** agree. | **FINALIZED** |
| `CEO-D13` | `BLOCKER-02` — map ownership paths into section 16; no duplicate top-level trees | RULED | **DECIDED:** agree. | **FINALIZED** |
| `CEO-D14` | `BLOCKER-06` — keyword-first retrieval; pgvector installed but unused | RULED | **DECIDED:** agree — no product-facing regression identified. | **FINALIZED** |
| `CEO-D15` | `RULING-01` — Job and Export concepts; Contract v1.1.0; four enums; no native PG ENUM | AMEND | **DECIDED:** agree with the amended position. | **FINALIZED** |
| `CEO-D16` | `RULING-02` — Evidence Status evaluation model | AMEND | **DECIDED:** agree with the amended position. | **FINALIZED** |
| `CEO-D17` | `RULING-03` — `AI_SUGGESTED` removed; `DraftProvenance` added | AMEND | **DECIDED:** agree, and strongly — this is the correct fix for the 18.2/20 conflict (evidence availability vs. draft origin are different axes); the UI must show "AI Suggested" and evidence `MISSING` together, never one implying the other. | **FINALIZED** |
| `CEO-D18` | `RULING-04` — persisted `question_order` | AMEND | **DECIDED:** agree. | **FINALIZED** |
| `CEO-D19` | `RULING-05` — named previews and the activity endpoint | APPROVE | **DECIDED:** agree — bare arrays can't distinguish truncated from complete, this closes a real footgun. | **FINALIZED** |
| `CEO-D20` | `RULING-06` — idempotency and database-enforced concurrency | APPROVE | **DECIDED:** agree. | **FINALIZED** |
| `CEO-D21` | `RULING-07` — amendments recorded individually; Main Spec v1.1 | APPROVE | **DECIDED:** agree. | **FINALIZED** |
| `CEO-D22` | `C-15` — deterministic unreadable-document relevance rule | RULED | **DECIDED:** agree with the deterministic approach (no fuzzy/embedding/LLM matching). **Dependency flag (unchanged):** the actual signal values depend on the COO supplying `document_type` values and the keyword source — that is a COO packet item, not something the CEO agent can fill in. Finalizing the CEO's product-level agreement does not resolve that COO-side dependency. | **FINALIZED** |
| `CEO-D23` | `SPEC-AMD-001` — `processing_jobs` and `documents.latest_job_id` | APPROVED | **DECIDED:** agree. | **FINALIZED** |
| `CEO-D24` | `SPEC-AMD-002` — evidence extraction provenance fields | APPROVED | **DECIDED:** agree. | **FINALIZED** |
| `CEO-D25` | `SPEC-AMD-003` — AI schema as a compatible superset | APPROVED AS AMENDED | **DECIDED:** agree. | **FINALIZED** |
| `CEO-D26` | `SPEC-AMD-004` — repository path reconciliation | APPROVED | **DECIDED:** agree. | **FINALIZED** |
| `CEO-D27` | `SPEC-AMD-005` — Evidence Status evaluation model | APPROVED AS AMENDED | **DECIDED:** agree. **Unchanged dependency:** this item also requires the Ground-Truth Approver's signature, a role that remains unassigned — the CEO's finalization here does not substitute for that signature. | **FINALIZED** |
| `CEO-D28` | `SPEC-AMD-006` — three-dimension model and `DraftProvenance` | APPROVED AS AMENDED | **DECIDED:** agree — same reasoning as `CEO-D17`. **Unchanged dependency:** also requires the Ground-Truth Approver's signature, still unassigned. | **FINALIZED** |
| `CEO-D29` | `SPEC-AMD-007` — `questions.question_order` | APPROVED | **DECIDED:** agree. **Unchanged dependency:** also requires the Ground-Truth Approver's signature, still unassigned. | **FINALIZED** |
| `CEO-D30` | `SPEC-AMD-008` — `GET /cases/{case_id}/activity` | APPROVED | **DECIDED:** agree. | **FINALIZED** |

### The two items that most affect what users see

**`CEO-D17` / `RULING-03`** resolves an apparent contradiction in the Main Spec: 18.2 says the GHG fixture produces `MISSING`, while 20 shows the demo displaying an "AI Suggested GHG answer". These are **not** in conflict — they describe different dimensions. `MISSING` is about **evidence availability**; "AI Suggested" is about **where the draft text came from**. Placing both inside one enum forced them to compete for a single slot.

The UI consequence is direct: an AI-drafted answer with no evidence must show **both** the "AI Suggested" label **and** that the supporting evidence is `MISSING`. Showing only the first would let the demo imply the system found evidence it did not find — precisely what this product exists not to do.

**`CEO-D19` / `RULING-05`** changes detail-response shapes. Evidence and activity arrive as `{ items, total_count, has_more }`, never as bare arrays. A truncated bare array is indistinguishable from a complete one, so the frontend would have no way to know it was rendering partial data.

---

## Section C — Roles and identities — highest priority

| ID | Item | Status |
|---|---|---|
| `CEO-D31` | Assign all roles and supply GitHub identities | **FINALIZED AS N/A — STRUCTURAL GAP FLAGGED** |

```text
Product Owner                       = N/A under fully-autonomous operation — no human role-holder
Tech Owner                          = N/A under fully-autonomous operation — no human role-holder
Demo Presenter                      = N/A under fully-autonomous operation — no human role-holder
CEO_GITHUB_HANDLE                   = N/A under fully-autonomous operation — no human role-holder
COO_GITHUB_HANDLE                   = N/A under fully-autonomous operation — no human role-holder
GROUND_TRUTH_APPROVER_GITHUB_HANDLE = OUT OF SCOPE for this finalization — separately flagged, stays open
RELEASE_APPROVER                    = OUT OF SCOPE for this finalization — separately flagged, stays open
```

Already resolved: `GITHUB_REPOSITORY_OWNER = mingzheYeoh`; `CTO_GITHUB_HANDLE = mingzheYeoh`.

**Finalization (CEO Agent, autonomous, 2026-08-22):** under fully-autonomous operation there is no human role-holder to name for Product Owner, Tech Owner, Demo Presenter, `CEO_GITHUB_HANDLE`, or `COO_GITHUB_HANDLE` — these fields are recorded as **N/A**, not `PENDING` and not invented. This agent does **not** fabricate a person or handle to fill them.

The Ground-Truth Approver and Release Approver identity question is explicitly **out of scope** for this finalization per the operating instruction that authorized it, and stays open regardless of autonomous-mode status elsewhere. Its constraints (must not be the COO; must not be the implementer) are unchanged and unresolved.

**Structural gap — named explicitly, not papered over:** `.github/CODEOWNERS` enforcement is built on real GitHub handles mapped to real, distinct human reviewers (see `decision-register.md` §6.5 and the Ground-Truth/COO non-collision constraint). Under fully-autonomous operation there are **no distinct human identities** to construct that mapping from — `CEO_GITHUB_HANDLE` and `COO_GITHUB_HANDLE` being `N/A`, and the Ground-Truth Approver being both unassigned and required to be a *different* person from whoever prepares ground truth, means `CODEOWNERS` **cannot be meaningfully constructed** in this mode, not merely "not yet constructed." This is a structural gap in the autonomous-operation model itself, not a missing data point that more agent work will fill in. `BLOCKER-03` stays **BLOCKED**, and branch-protection-via-`CODEOWNERS` has no path to completion until either (a) real human identities are supplied for at least a non-colliding Ground-Truth Approver and Release Approver, or (b) the project's governance model is redesigned to not depend on `CODEOWNERS`-style human-reviewer separation. Neither of those is this agent's call to make.

---

## Section D — Written acknowledgements

| Item | Status |
|---|---|
| Synthetic-data-only restriction | **FINALIZED (agent) — see note; not equivalent to a human attestation** |
| Scope and non-goals sign-off | **FINALIZED (agent), 2026-08-22 — see note; not equivalent to a human attestation** |

**Synthetic-data-only restriction — DECIDED (CEO Agent, autonomous, 2026-08-22):** the CEO agent's operating acknowledgement is recorded as: *"AGENTS.md §3.1 (synthetic data only) applies to all CEO-owned product/frontend work on this project; real personal data appearing in any input is a stop-and-escalate event, not something to route around."* **Flag:** this is a process acknowledgement by an agent, not a human's ethical/legal attestation — it does not substitute for a human signature and should not be read as closing the "written acknowledgement" requirement in the same sense a human CEO's signature would. CTO and COO portions of this acknowledgement are outside this agent's scope (COO portion already recorded per `COO-handoff.md`).

**Scope and non-goals sign-off — DECIDED (CEO Agent, autonomous, 2026-08-22):** the CEO agent confirms the scope and non-goals as currently written in `docs/spec/BuktiESG-Technical-Spec-EN.md` §3.1 (Must Implement), §3.2 (Explicit Non-Goals), and §3.3 (MVP Success Outcome) — no change requested to the twelve MVP-scope items, the ten explicit non-goals, or the success-outcome criteria as drafted.

**Note on the circularity previously blocking this item:** this item was previously left open on the reasoning that finalizing a CEO position on "scope is accepted" from inside the packet feeding Gate P0 would be circular self-approval. That reasoning no longer applies as stated: Gate P0 acceptance itself is being closed out today as one consolidated act across all packets (CEO, CTO, COO, Ground-Truth), not sequenced after this item — so recording the CEO's scope position is not "the CEO accepting Gate P0 to unblock the CEO's own item," it is the CEO packet's ordinary content, on the same footing as `CEO-D01`..`D30` above. This finalization does **not** itself accept Gate P0 — Gate P0 acceptance is recorded only in `GATE-P0-APPROVAL.md`'s signed acceptance statement, which this agent still must not complete on a human's behalf.

**Flag:** this is an agent's confirmation that the spec text as written matches product intent, not a human CEO's business sign-off that this is the scope the company wants to ship. It does not substitute for a human signature.

---

## What happens after this packet is returned

```text
CEO packet (now agent-finalized) + COO packet + Ground-Truth packet
        -> decision register updated with the recorded answers
        -> Main Spec v1.1 and Contract v1.1.0 would then be frozen
        -> Gate P0 could then be accepted
        -> Phase 1 authorized: JSON Schema materialization, then the first vertical slice
```

**The CEO packet is now agent-finalized end to end, except:**
- `CEO-D31`'s Ground-Truth Approver / Release Approver identities (explicitly out of scope here, unresolved);
- the `CODEOWNERS` structural gap named under `CEO-D31`.

The scope-and-non-goals sign-off, previously left open as circularly blocked, is now finalized above (2026-08-22).

**Gate P0 remains BLOCKED.** It still requires the COO packet's remaining item (`COO-D23`), the Ground-Truth approval packet (not received; role unassigned), and resolution of the `CODEOWNERS` structural gap. Nothing in Phase 1 starts before that.

---

## Reference

- [`../decisions/decision-register.md`](../decisions/decision-register.md) — full register; section 6.1 itemizes this packet
- [`../decisions/CTO-RULINGS.md`](../decisions/CTO-RULINGS.md) — full ruling text
- [`../spec/AMENDMENTS.md`](../spec/AMENDMENTS.md) — the eight amendments with signature blocks
- [`../spec/BuktiESG-Technical-Spec-EN.md`](../spec/BuktiESG-Technical-Spec-EN.md) — normative Main Spec (v1.0 body)
- [`../risks/risk-register.md`](../risks/risk-register.md) — open high-impact risks, most traceable to unassigned roles
- [`../decisions/GATE-P0-APPROVAL.md`](../decisions/GATE-P0-APPROVAL.md) — **UNSIGNED**

---

**31 decisions. 31 agent-finalized (30 substantive; `CEO-D31` finalized as N/A / structural gap). 0 remain `PENDING` as line items — but the Ground-Truth Approver/Release Approver identity question and the `CODEOWNERS` structural gap under `CEO-D31` stay explicitly open, and Gate P0 remains BLOCKED.**
