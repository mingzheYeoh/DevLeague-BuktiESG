# Project Control Status

| Field | Value |
|---|---|
| Status | **PROPOSED** |
| Gate P0 | **BLOCKED** |
| Main Spec target | **v1.1 — NOT ACCEPTED** |
| Contract target | **v1.1.0 — NOT FROZEN** |
| Feature implementation | **NOT AUTHORIZED** |
| Date | 2026-08-21 |

---

## Classification

| Item | Value |
|---|---|
| Project tier | **T1** — maintainable, deployable hackathon and portfolio project; synthetic or de-identified data only |
| Planned build risk | **Yellow** — file uploads, AI file processing, business scoring rules, a database, and exports |
| Phase 0 task risk | Green — documentation only |
| Enforcement | **ADVISORY-ONLY** |
| Production state | Not released |

---

## Enforcement is advisory-only, and this is not a formality

At the time of this commit the repository has:

| Control | State |
|---|---|
| Commits | This is the first |
| Branch protection on `main` | **Not enabled** |
| `.github/CODEOWNERS` | **Does not exist** — blocked on four identities |
| Required status check `ci / verify` | **Does not exist** |
| CI workflows | **Do not exist** |
| Tests | **Do not exist** |
| Protected ground truth | **Does not exist** |

**Nothing in this repository is independently enforced.** Every rule in [`../../AGENTS.md`](../../AGENTS.md) is currently a convention that an agent or a human could violate without any mechanism objecting.

The project must not claim independent enforcement until CI, protected tests, and acceptance evidence actually exist and have been verified.

---

## The bootstrap gap

A branch cannot be protected before it exists, and a repository with zero commits cannot accept a pull request. The first two commits are therefore **necessarily unprotected**:

```text
1. Commit 1  documentation bootstrap        -> main   (unprotected: no branch exists yet)
2. Push to GitHub; main now exists
3. Commit 2  .github/CODEOWNERS             (requires the four pending identities)
4. Enable branch protection and the required status check
5. From here, every change goes through a pull request with non-author approval
```

**No first commit can make itself tamper-proof.** This is the standard bootstrap gap, recorded here so that the gap is deliberate and visible rather than discovered later.

Enforcement stays **advisory-only** through step 4, then becomes **partial**. It can only be recorded as promoted by a later control-only change — never by the commit that installs the controls, because that commit is itself unreviewed.

---

## Role assignments

| Role | Identity | GitHub handle | State |
|---|---|---|---|
| Repository owner | Yeoh Ming Zhe | `mingzheYeoh` | Resolved |
| CTO — Backend & Integration Lead | Yeoh Ming Zhe | `mingzheYeoh` | Resolved |
| CEO — Product & Frontend Lead | **PENDING** | **PENDING** | Blocked |
| COO — AI & ESG Operations Lead | **PENDING** | **PENDING** | Blocked |
| Ground-Truth Approver | **PENDING** | **PENDING** | Blocked |
| Release Approver | **PENDING** | **PENDING** | Blocked |
| Product Owner | **PENDING** | — | Blocked |
| Tech Owner | **PENDING** | — | Blocked |
| Demo Presenter | **PENDING** | — | Blocked |

### Separation rules

Two constraints must hold when these are assigned, or the corresponding control becomes decorative:

- **The Ground-Truth Approver must not be the COO**, who prepares ground truth. A preparer approving their own expected values is not an independent check.
- **The Release Approver must not be the implementer.** An agent or person that implements a feature must never approve its own release.

Migration and security paths carry a **red-risk floor**: they are never self-approvable by the implementer, regardless of the project tier.

**These identities have not been guessed.**

---

## T2 escalation triggers

If any of the following occurs, stop releasing under T1 and redesign security, privacy, and operations **first**:

- Real employee, customer, payroll, identity-card, health, safety-incident, or other personal data is uploaded.
- Real customers or external businesses depend on system outputs.
- Generated questionnaire answers are used directly for contracts, audits, compliance, or regulatory submissions.
- Accounts, organization isolation, role permissions, or multi-tenancy are required.

The current architecture assumes none of these. A single seeded organization row, no authentication, and a local-only deployment are all direct consequences of T1 — each becomes a defect the moment a trigger fires.

---

## Data restriction

**Synthetic data only.** No real ESG data, no real customer questionnaires, no production credentials, no personal data of any kind.

Written acknowledgement is required from the CEO, the CTO, and the COO. **Zero of three have been recorded.**

---

## Current authorization

Documentation of decisions already made. Nothing else.

Not authorized: application code, migrations, runtime schemas, tests, fixtures, dependencies, `.env.example`, Docker Compose, CI workflows, `CODEOWNERS`, deployment configuration, or application initialization in any form.

---

**Gate P0 is BLOCKED. Enforcement is ADVISORY-ONLY.**
