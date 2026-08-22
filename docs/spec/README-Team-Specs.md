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

# BuktiESG Team Execution Pack

Version: 1.0  
Date: 2026-08-21  
Status: `planned`  
Project tier: T1  
Planned build risk: Yellow  
Enforcement: Advisory-only until repository CI and protected review gates are verified

## Purpose

This pack divides the BuktiESG implementation across three team roles while keeping one product and one source of truth.

The role documents are execution briefs. They do not create three independent products, and they do not override the Main Technical Spec.

## Source of Truth

All team members and AI agents must read:

1. `BuktiESG-Technical-Spec-ZH.md` — authoritative product and technical specification.
2. `Shared-Integration-Contract.md` — authoritative interface agreement between workstreams.
3. Their assigned Role Sub-Spec.
4. `Integration-Checklist.md` — merge, verification, and demo coordination.

If two documents conflict, use this order:

1. Main Technical Spec
2. Approved shared contract
3. Approved decision record
4. Role Sub-Spec
5. Individual implementation preference

No role document may weaken the Main Spec's evidence rules, priority formula, acceptance criteria, synthetic-data restriction, security boundaries, or human-review requirement.

## Role Assignment

| Role | Execution brief | Primary ownership |
|---|---|---|
| CEO — Product & Frontend Lead | `CEO-Product-Frontend-Sub-Spec.md` | Product decisions, web UI, user journey, visual acceptance, pitch and live demo |
| CTO — Backend & Integration Lead | `CTO-Backend-Integration-Sub-Spec.md` | Architecture, database, APIs, file lifecycle, exports, deployment and integration |
| COO — AI & ESG Operations Lead | `COO-AI-ESG-Operations-Sub-Spec.md` | Synthetic ESG data, document processing, SEDG mapping, evidence analysis and evaluation |

## Shared Files

| File | Purpose |
|---|---|
| `Shared-Integration-Contract.md` | Shared enums, API shapes, AI output schema, errors and contract-change process |
| `Integration-Checklist.md` | Phase gates, merge cadence, handoffs, critical E2E and demo readiness |

## Mandatory Team Rule

Completing one Role Sub-Spec does not mean the product is complete.

The product becomes `verified` only when the combined implementation passes the Main Spec's critical end-to-end journeys and the Integration Checklist. It becomes `accepted` only after accountable human review.

## Recommended Working Order

1. All members complete Phase 0 together.
2. Freeze the Shared Integration Contract.
3. CEO builds the UI against contract fixtures.
4. CTO implements the same contract through API and persistence.
5. COO produces the same contract through the document and AI pipeline.
6. Integrate one vertical slice before expanding features.
7. Merge and test at least every two to three hours.
8. Stop feature growth before the final demo-hardening window.

## First Vertical Slice

The first shared milestone is:

```text
Create Case
→ Upload one questionnaire
→ Parse one question
→ Match one evidence source
→ Display PARTIAL with a source location
→ Create one SUBMISSION action
→ Persist and reload the result
```

Do not wait for all screens, endpoints, or AI features before proving this slice.

## AI Agent Instruction

Every role owner should give their AI agent the Main Spec, the Shared Integration Contract, and their Role Sub-Spec. The agent must first return its understanding, file ownership, dependencies, planned tasks, tests, and blockers. It must not start coding before Phase 0 is accepted.

