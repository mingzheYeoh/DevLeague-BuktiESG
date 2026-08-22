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

# BuktiESG Integration Checklist

Version: 1.0  
Date: 2026-08-21  
Status: `planned`  
Applies to: CEO, CTO, and COO workstreams

## 1. Authority and Goal

This checklist coordinates the three Role Sub-Specs. It does not replace the Main Technical Spec or Shared Integration Contract.

Goal: keep the application runnable, contracts aligned, and the end-to-end demo verifiable throughout the hackathon.

## 2. Team Operating Rules

- Read the Main Spec before any Role Sub-Spec;
- Complete Phase 0 together;
- Use synthetic data only;
- Freeze shared contracts before parallel feature work;
- Integrate at least every two to three hours;
- Keep branches short-lived;
- Keep `main` runnable;
- Do not change another role's owned files without coordination;
- Do not change protected files to make a failing implementation pass;
- Stop feature growth before the final hardening window;
- After three failed cycles on the same gate, return to specification or design.

## 3. Required Files Before Coding

- [ ] Main Technical Spec is available to all members.
- [ ] CEO Sub-Spec is assigned.
- [ ] CTO Sub-Spec is assigned.
- [ ] COO Sub-Spec is assigned.
- [ ] Shared Integration Contract is reviewed.
- [ ] Phase 0 decisions are recorded.
- [ ] Contract version is recorded.
- [ ] Synthetic-data restriction is acknowledged.
- [ ] Product Owner, Tech Owner, and Demo Presenter are named.
- [ ] Main-branch Integration Owner is named.

## 4. Phase 0 Decision Gate

- [ ] Product name confirmed.
- [ ] Primary user and 14-day scenario confirmed.
- [ ] English UI confirmed or changed through a recorded decision.
- [ ] Recommended stack confirmed or replaced through ADR.
- [ ] Deployment target confirmed.
- [ ] File-size, Case-size, and retention defaults confirmed.
- [ ] 20-question demo scope confirmed.
- [ ] Supported file types confirmed.
- [ ] Keyword-first vs hybrid retrieval decision confirmed.
- [ ] API, enum, error, and AI schemas frozen at version 1.0.0.
- [ ] First vertical slice confirmed.
- [ ] Gate P0 accepted by the accountable owner.

No role starts business-feature implementation until all blocking Phase 0 items are resolved.

## 5. Ownership Map

| Area | Primary owner | Required reviewers |
|---|---|---|
| Product outcome and scope | CEO | CTO, COO |
| Web UI and visual behavior | CEO | CTO for contract; COO for evidence clarity |
| OpenAPI and API implementation | CTO | CEO, COO |
| Database and migrations | CTO | At least one non-author reviewer |
| File/job lifecycle | CTO | COO |
| AI/document pipeline | COO | CTO for contract; CEO for visible rationale |
| SEDG taxonomy and fixtures | COO | CEO or non-implementer for Ground Truth |
| Shared contracts | CTO coordinates | CEO + CTO + COO approve |
| Ground Truth | COO prepares | Non-implementer approves |
| Critical E2E expectations | Main Spec | All roles; not changed unilaterally |
| Demo and visual acceptance | CEO coordinates | CTO + COO |
| Deployment and rollback | CTO | CEO approval; COO validates pipeline |

## 6. Branch and Merge Checklist

Recommended branch examples:

```text
feat/frontend-readiness
feat/core-api
feat/document-evidence
```

Before opening a PR or merge request:

- [ ] Task ID from the Role Sub-Spec is included.
- [ ] Changed paths match role ownership.
- [ ] Shared/protected changes are called out separately.
- [ ] Contract version is unchanged or an approved contract change is attached.
- [ ] Relevant build, lint, type, and unit checks pass.
- [ ] Fixture or migration impact is disclosed.
- [ ] Data, dependency, security, cost, and rollback impact is disclosed.
- [ ] Reproduction or preview evidence is available.
- [ ] Known limitations are listed.

Before merging:

- [ ] Main branch is current.
- [ ] Contract tests pass.
- [ ] A non-author reviewed protected changes.
- [ ] Migration review is complete where applicable.
- [ ] Visual difference is approved where applicable.
- [ ] Merge does not disable an existing gate.
- [ ] Main remains runnable after merge.

## 7. Two-to-Three-Hour Sync

At each sync, every role answers:

1. What was implemented?
2. What was verified?
3. What is blocked?
4. What contract or dependency changed?
5. What will be delivered by the next sync?
6. Is the first vertical slice still runnable?

Use precise status:

```text
planned
implemented
verified
accepted
blocked
failed
```

Do not report “done” without a gate and evidence.

## 8. First Vertical Slice Gate

- [ ] CEO can create a Case through the UI.
- [ ] CTO persists and returns the Case.
- [ ] CEO can upload the synthetic questionnaire.
- [ ] CTO creates Document and Job state.
- [ ] COO parses one question with original cell location.
- [ ] COO returns one schema-valid evidence candidate.
- [ ] CTO validates and persists the AI result.
- [ ] CTO calculates PARTIAL through deterministic rules.
- [ ] CEO displays PARTIAL with source location and missing period.
- [ ] CEO creates a SUBMISSION action.
- [ ] CTO persists the Action.
- [ ] Browser refresh restores the complete state.
- [ ] Contract and integration tests pass.

This gate should pass before the team expands to all 20 questions.

## 9. Phase Integration Matrix

| Phase | CEO deliverable | CTO deliverable | COO deliverable | Shared gate |
|---|---|---|---|---|
| 0 | Product decisions and user flow | ADR and contract proposal | Dataset/AI decisions | P0 frozen and accepted |
| 1 | Frontend shell and typed fixtures | API/DB foundation and CI | Synthetic dataset and taxonomy | App starts; fixtures validate |
| 2 | Intake UI | Case/upload/job persistence | Parsers and source locations | Upload→parse trace works |
| 3 | Questions and Evidence UI | Question/Evidence APIs | Mapping/retrieval/extraction | One source-located result end to end |
| 4 | Readiness and priority UI | Status/priority engine | Status inputs and rationales | Required demo states appear correctly |
| 5 | Review and Actions UI | Review/Action persistence | Follow-up suggestions | Confirmation and action journey works |
| 6 | Export UI and visual review | PDF/Index generation | Citation and missing-text support | Export is honest and readable |
| 7 | Accessibility and demo | Reliability/security/observability | Evaluation/cost/fallback | Critical E2E and demo rehearsal pass |
| 8 | Acceptance coordination | Deployment/rollback | Pipeline validation | Explicit release decision |

## 10. Shared Contract Verification

- [ ] All roles use the same Evidence Status enums.
- [ ] All roles use the same Review Status enums.
- [ ] All roles use SUBMISSION and IMPROVEMENT action types.
- [ ] Frontend fixtures validate against the shared contract.
- [ ] API responses validate against OpenAPI.
- [ ] AI results validate against the AI schema.
- [ ] Source locations use one of the approved shapes.
- [ ] Errors use the shared envelope.
- [ ] Unknown enum values fail visibly.
- [ ] Contract version is included in automated checks.

## 11. Critical End-to-End Checklist

### E2E-001 — Case and Questionnaire

- [ ] Create a Case with customer, deadline, and reporting period.
- [ ] Upload the synthetic questionnaire.
- [ ] Parse 20 questions.
- [ ] Preserve original sheet/cell references.

### E2E-002 — Evidence

- [ ] Upload supporting documents.
- [ ] Open a question.
- [ ] Display exact source location and excerpt.
- [ ] Confirm that missing location cannot be VERIFIED.

### E2E-003 — Required Statuses

- [ ] VERIFIED candidate appears only with qualifying evidence.
- [ ] PARTIAL shows missing period or scope.
- [ ] OUTDATED shows source date and required period.
- [ ] CONFLICTING shows both sources and no winner.
- [ ] MISSING shows the absent requirement.
- [ ] AI_SUGGESTED is visibly unconfirmed.

### E2E-004 — Human Review

- [ ] Accept an answer.
- [ ] Edit an answer.
- [ ] Reject a draft with a reason.
- [ ] Confirm that unreviewed AI content does not count toward readiness.

### E2E-005 — Priority and Action

- [ ] Display all four factors and rationales.
- [ ] Server calculates score from 0 to 100.
- [ ] Override requires a reason.
- [ ] Create an Action with type, owner, next step, and deadline.
- [ ] Separate SUBMISSION and IMPROVEMENT actions.
- [ ] Invalidate closure evidence and confirm Action returns to NEEDS_REVIEW.

### E2E-006 — Export

- [ ] Pre-export warnings show unresolved problems.
- [ ] Customer Summary distinguishes confirmed, assumed, and missing information.
- [ ] Evidence Index contains question, document, location, period, scope, and review status.
- [ ] PDF is readable and citations match the UI.
- [ ] Export failure can retry without changing Case data.

### E2E-007 — Failure and Recovery

- [ ] Empty or malformed input is handled.
- [ ] Duplicate upload does not duplicate processing.
- [ ] Double-click does not duplicate business objects.
- [ ] Refresh restores persisted state.
- [ ] Failed network does not report save success.
- [ ] Parser failure offers retry/manual review.
- [ ] AI timeout produces a recoverable state.
- [ ] Wrong-Case object ID is rejected.

## 12. Final Demo Readiness

- [ ] Synthetic dataset is seeded and repeatable.
- [ ] Demo reset command works.
- [ ] No real personal or customer data is present.
- [ ] Prototype disclaimer is visible.
- [ ] Live path completes in seven minutes or less.
- [ ] Backup screenshots or recording are available.
- [ ] Precomputed AI fallback is clearly marked as fixture data.
- [ ] Presenter handoffs are rehearsed.
- [ ] Known limitations are prepared for Q&A.
- [ ] Internet outage fallback is tested.
- [ ] Last-minute features are frozen.

## 13. Presentation Handoff

### CEO — Opening and Product

- Problem and user;
- Why a score or carbon calculator is insufficient;
- Product journey and visible value.

### COO — Evidence and AI

- Document/question processing;
- Source-located evidence;
- Partial, outdated, conflicting, missing, and AI-suggested distinctions;
- Human-in-the-loop honesty.

### CTO — Action and Feasibility

- Priority breakdown;
- Owner, next step, and deadline;
- Export and audit trail;
- Architecture, deployment, and business feasibility.

### CEO — Closing

Recommended final line:

> BuktiESG does not help a company pretend it is sustainable. It helps the company know what it can prove, what is still missing, and who must act next.

## 14. Release Decision Record

Before any shared deployment, record:

```text
Version/build:
Environment:
Tier/risk/enforcement:
Critical E2E result:
Contract version:
Data/privacy status:
Security/dependency status:
Known limitations:
Rollback action:
Approver:
Decision: approved / rejected / changes requested
Approval scope: behavior / preview / staging / demo / production
Timestamp:
```

Approval of the demo behavior is not approval for production use.

