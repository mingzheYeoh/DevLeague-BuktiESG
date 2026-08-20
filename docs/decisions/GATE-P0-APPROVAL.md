# Gate P0 Approval Record

# THIS RECORD IS UNSIGNED

# GATE P0 IS BLOCKED

| Field | Value |
|---|---|
| Status | **PROPOSED** |
| Gate P0 | **BLOCKED** |
| Main Spec target | **v1.1 — NOT ACCEPTED** |
| Contract target | **v1.1.0 — NOT FROZEN** |
| Feature implementation | **NOT AUTHORIZED** |
| Signatures obtained | **0 of 3 outstanding packets** |
| Date opened | 2026-08-21 |
| Date accepted | **NOT ACCEPTED** |

**This document does not accept Gate P0.** It is the record into which acceptance will be written once the required approvals exist. Nothing below constitutes an approval, and no part of this file may be read as one.

---

## Scope of the approval being sought

Accepting Gate P0 would authorize the start of **Phase 1** and would freeze:

- **Main Technical Spec v1.1** — the v1.0 English document plus amendments `SPEC-AMD-001` through `SPEC-AMD-008`
- **Shared Integration Contract v1.1.0**
- The decision register at [`decision-register.md`](decision-register.md)
- The CTO rulings at [`CTO-RULINGS.md`](CTO-RULINGS.md), including `C-15`
- `ADR-001`

It would **not** authorize: production deployment, real data of any kind, T2 activity, or release.

---

## Signature blocks

### CTO approval packet

```text
Role            CTO — Backend & Integration Lead
Identity        Yeoh Ming Zhe
GitHub handle   mingzheYeoh
Packet state    COMPLETE
Date            2026-08-21

Scope           All items within CTO authority: system architecture, FastAPI
                backend, PostgreSQL and migrations, OpenAPI and shared
                contracts, file and processing-job lifecycle, deterministic
                evidence and priority rules, action-tracking persistence,
                export services, CI, deployment, observability, rollback,
                integration, and main-branch coordination.

                RULING-01 .. RULING-07      ruled
                BLOCKER-01 .. BLOCKER-08    ruled or recommended
                C-14                        recommendation to CEO
                C-15                        ruled
                SPEC-AMD-001 .. 008         CTO position recorded

Outstanding     None within CTO authority.

Limitation      A CTO ruling is NOT a Gate P0 acceptance and is NOT
                sufficient for any item touching product outcomes, the AI
                pipeline, expected fixture values, the Main Spec, or the
                Shared Contract.

Signed          Yeoh Ming Zhe / mingzheYeoh
```

### CEO approval packet

```text
Role            CEO — Product & Frontend Lead
Identity        [ ] PENDING
GitHub handle   [ ] PENDING
Packet state    NOT RECEIVED
Date            [ ]

Required        Product decisions; co-approval of the specification and
                contract change set; role assignments; GitHub identities;
                synthetic-data acknowledgement; scope and non-goals sign-off.
                Itemized in decision-register.md section 6.1.

Signature       [ ] NOT OBTAINED
```

### COO approval packet

```text
Role            COO — AI & ESG Operations Lead
Identity        [ ] PENDING
GitHub handle   [ ] PENDING
Packet state    NOT RECEIVED
Date            [ ]

Required        Pure processing-core boundary; provider configuration;
                co-approval of the specification and contract change set;
                failure-code catalog; document_chunks shape; ExtractionMethod
                values; C-15 document_type and keyword signals; deterministic
                AI fixtures; prompt-injection fixture; ground-truth impact
                confirmation; synthetic-data acknowledgement.
                Itemized in decision-register.md section 6.2.

Signature       [ ] NOT OBTAINED
```

### Ground-Truth approval packet

```text
Role            Ground-Truth Approver
Identity        [ ] PENDING — ROLE UNASSIGNED
GitHub handle   [ ] PENDING
Packet state    NOT RECEIVED
Date            [ ]

Constraint      MUST NOT be the COO, who prepares ground truth.
                SHOULD NOT be the CTO, who implements against it.
                A collision makes this control decorative.

Required        SPEC-AMD-005, SPEC-AMD-006, SPEC-AMD-007, C-15.
                Ground-truth freeze and standing attestation follow at Phase 3.
                Itemized in decision-register.md section 6.3.

Signature       [ ] NOT OBTAINED
```

### Release Approver

```text
Role            Release Approver
Identity        [ ] PENDING
GitHub handle   [ ] PENDING

Constraint      MUST NOT be the agent or person that implemented the change.
                Migration and security paths carry a red-risk floor and are
                never self-approvable by the implementer.

Note            Not required for Gate P0. Required from Phase 7 onward, and
                the identity is needed now because CODEOWNERS cannot be
                written without it.

Signature       [ ] NOT OBTAINED
```

---

## Acceptance criteria

| Criterion | State |
|---|---|
| All blocking decisions confirmed | **NOT MET** — CTO rulings complete; 0 of 3 external packets received |
| Scope and non-goals signed off | **NOT MET** — awaiting CEO |
| Synthetic-data restriction acknowledged in writing | **NOT MET** — 0 of 3 acknowledgements |
| Tier, risk, and enforcement recorded | **MET** — [`project-control-status.md`](project-control-status.md) |
| Governance artifacts exist in the repository | **MET** — this commit |
| Roles assigned, including Ground-Truth Approver | **NOT MET** |
| GitHub identities supplied | **NOT MET** — 4 of 6 pending |

**5 criteria unmet.**

---

## Critical path

```text
Name the Ground-Truth Approver  (gates 4 amendment signatures; no way around it)
        |
CEO and COO co-approve BLOCKER-01 and BLOCKER-02
        |
SPEC-AMD-001..008 signed, with Ground-Truth signatures on 005, 006, 007
        |
CEO supplies limits, deployment, roles, and the 4 GitHub identities
COO confirms BLOCKER-04, BLOCKER-08, C-15 signals, schema, and fixtures
        |
GATE P0 ACCEPTED  -->  Phase 1 authorized
```

---

## Acceptance statement — TO BE COMPLETED BY A HUMAN

Gate P0 is accepted **only** when the statement below is completed and signed by all required roles. Until then this section is a template and nothing more.

```text
Gate P0 accepted against Contract v1.1.0 and the approved decision register.

CEO             ______________________  handle: ____________  date: __________
CTO             ______________________  handle: ____________  date: __________
COO             ______________________  handle: ____________  date: __________
Ground Truth    ______________________  handle: ____________  date: __________
```

**The template above is unsigned and must not be treated as an acceptance.**

An AI agent must never complete this block on a human's behalf, and must never output the acceptance statement as though it had been given.

---

# GATE P0 IS BLOCKED. PHASE 1 IS NOT AUTHORIZED.
