# BuktiESG

An ESG customer-questionnaire **Evidence-to-Action** workspace for Malaysian SMEs.

*"Bukti"* means **proof** or **evidence** in Malay. The product thesis is provenance over prose: the system must never help a company claim what it cannot prove.

---

## Project Status

| Field | Value |
|---|---|
| Status | **PROPOSED** |
| Gate P0 | **BLOCKED** |
| Main Spec target | **v1.1 — NOT ACCEPTED** |
| Contract target | **v1.1.0 — NOT FROZEN** |
| Feature implementation | **NOT AUTHORIZED** |
| Production state | Not released |
| Repository contents | **Documentation only.** No application code, dependencies, migrations, tests, fixtures, CI, or deployment configuration exist. |

**This repository contains no runnable software.** There are deliberately no setup or run instructions, because there is nothing to set up or run. Implementation is not authorized until Gate P0 is accepted by the CEO, COO, and the Ground-Truth Approver.

---

## Data Restriction

**Synthetic data only.**

This is a **T1** project. Real employee, customer, payroll, identity-card, health, safety-incident, or other personal data must never be uploaded, committed, or processed. Uploading real personal data is an explicit trigger to stop releasing under T1 and redesign security, privacy, and operations first — see Main Spec §0.1.

No real ESG data. No real customer questionnaires. No production credentials.

---

## Project Control Status

| Item | Value |
|---|---|
| Project tier | **T1** — maintainable, deployable hackathon/portfolio project; synthetic or de-identified data only |
| Planned build risk | **Yellow** — file uploads, AI file processing, business scoring rules, a database, and exports |
| Enforcement | **Advisory-only** |
| Release approver | **PENDING** — must not be the agent or person that implemented the feature |

**Enforcement is advisory-only and this is not a formality.** At the time of this commit there is no branch protection, no `CODEOWNERS`, no required status check, and no CI. Nothing in this repository is independently enforced. See [`docs/decisions/project-control-status.md`](docs/decisions/project-control-status.md).

---

## Normative Documents

| Document | Role |
|---|---|
| [`docs/spec/BuktiESG-Technical-Spec-EN.md`](docs/spec/BuktiESG-Technical-Spec-EN.md) | **NORMATIVE.** The Main Technical Spec. |
| [`docs/spec/BuktiESG-Technical-Spec-ZH.md`](docs/spec/BuktiESG-Technical-Spec-ZH.md) | **NON-NORMATIVE** translation. On conflict, the English document governs. |
| [`docs/spec/Shared-Integration-Contract.md`](docs/spec/Shared-Integration-Contract.md) | v1.0.0 baseline. Never accepted, never implemented. |
| [`docs/spec/Shared-Integration-Contract-v1.1.0-PROPOSED.md`](docs/spec/Shared-Integration-Contract-v1.1.0-PROPOSED.md) | Proposed v1.1.0 delta. **Not frozen.** |
| [`docs/spec/AMENDMENTS.md`](docs/spec/AMENDMENTS.md) | `SPEC-AMD-001` … `SPEC-AMD-008`, with per-role signature blocks. |

### Authority Order

1. Main Technical Spec (English)
2. Approved Shared Integration Contract
3. Approved architecture and decision records
4. Role Sub-Specs
5. Individual implementation preferences

Conflicts between documents are escalated, never silently resolved.

---

## Repository Map

```
README.md                        This file
AGENTS.md                        Execution rules binding on every AI agent
docs/
  spec/                          Normative specification and proposed amendments
  decisions/                     ADRs, decision register, CTO rulings, Gate P0 record
  risks/                         Risk register
  handoffs/                      Role handoff notes for CEO and COO
```

Nothing else exists yet. `apps/`, `packages/`, `workers/`, `fixtures/`, `tests/`, `scripts/`, and `deployment/` are described in Main Spec §16 but are **not created** and are not authorized.

---

## Gate P0

Gate P0 is **BLOCKED**.

The CTO has ruled on every item within CTO authority. Outstanding items require written decisions from the **CEO**, the **COO**, and a named **Ground-Truth Approver**.

- Current state: [`docs/decisions/decision-register.md`](docs/decisions/decision-register.md)
- CTO rulings: [`docs/decisions/CTO-RULINGS.md`](docs/decisions/CTO-RULINGS.md)
- Approval record (**unsigned**): [`docs/decisions/GATE-P0-APPROVAL.md`](docs/decisions/GATE-P0-APPROVAL.md)
- Role handoffs: [`docs/handoffs/CEO-handoff.md`](docs/handoffs/CEO-handoff.md) · [`docs/handoffs/COO-handoff.md`](docs/handoffs/COO-handoff.md)

---

## Roles

| Role | Identity | GitHub handle |
|---|---|---|
| Repository owner | Yeoh Ming Zhe | `mingzheYeoh` |
| CTO — Backend & Integration Lead | Yeoh Ming Zhe | `mingzheYeoh` |
| CEO — Product & Frontend Lead | **PENDING** | **PENDING** |
| COO — AI & ESG Operations Lead | **PENDING** | **PENDING** |
| Ground-Truth Approver | **PENDING** | **PENDING** |
| Release Approver | **PENDING** | **PENDING** |

The Ground-Truth Approver **must not** be the COO, who prepares ground truth. The Release Approver **must not** be the implementer.

Unknown identities are recorded as `PENDING` and have not been guessed. `.github/CODEOWNERS` cannot be written until they are supplied.

---

## Standards Referenced

Implemented target: **Capital Markets Malaysia SEDG v2** — 3 pillars, 15 topics, 38 disclosures.

Referenced but **not** implemented: EFRAG VSME, EcoVadis, Sedex.

---

## Licence

Not yet determined. See [`docs/risks/risk-register.md`](docs/risks/risk-register.md).
