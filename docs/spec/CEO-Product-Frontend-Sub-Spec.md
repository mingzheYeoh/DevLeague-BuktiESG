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

# CEO — Product & Frontend Lead Sub-Spec

Version: 1.0  
Date: 2026-08-21  
Status: `planned`  
Role owner: To be assigned  
Project tier: T1  
Task risk: Yellow  
Enforcement: Advisory-only

## 1. Authority

This Sub-Spec must be used together with `BuktiESG-Technical-Spec-ZH.md`.

The Main Technical Spec is the source of truth. This document assigns product and frontend execution responsibility only. It must not override the Main Spec, Shared Integration Contract, evidence status rules, priority formula, acceptance criteria, protected assets, or synthetic-data restriction.

If a conflict is found, stop the affected task, record the conflict, and request a shared decision. Do not silently choose the easier behavior.

## 2. Mission

Own the user-facing BuktiESG experience and make the complete Evidence-to-Action journey understandable to a non-ESG expert.

The CEO role combines:

- Product owner for MVP scope and visible behavior;
- Frontend lead for the Next.js application;
- Visual acceptance owner;
- Pitch and live-demo lead;
- Final decision coordinator when team trade-offs affect product outcome.

## 3. Success Outcome

A first-time user can complete the following journey without ESG training:

1. Create a questionnaire case;
2. Upload a customer questionnaire and supporting documents;
3. Understand overall readiness;
4. Open a question and inspect exact evidence sources;
5. Distinguish verified information from partial, outdated, conflicting, missing, and AI-suggested information;
6. Confirm or reject an answer;
7. Convert a gap into an owned action;
8. Export a transparent summary.

## 4. Scope

### 4.1 Included

- Product-flow decisions within the approved Main Spec;
- Information architecture and page navigation;
- Next.js frontend implementation;
- Shared UI components and status presentation;
- Contract-based mock data for parallel development;
- Loading, empty, error, recovery, and unconfirmed states;
- Keyboard interaction and core accessibility;
- Visual review of exported reports;
- Demo script, pitch narrative, screenshots, and fallback demo assets;
- Human acceptance coordination.

### 4.2 Excluded

- Database design and migrations;
- Backend business-rule implementation;
- Document parsing, OCR, embeddings, retrieval, or LLM prompts;
- Changing evidence status rules or the priority formula;
- Declaring an answer compliant, audited, or certified;
- Production deployment approval without the CTO's evidence and owner approval;
- Editing protected ground truth to match the UI.

## 5. File Ownership

Primary writable ownership:

```text
apps/web/**
packages/ui/**
docs/demo/**
docs/evidence/visual/**
```

Shared or protected files that require coordination:

```text
packages/contracts/**
docs/spec/**
docs/decisions/**
fixtures/ground_truth/**
.github/workflows/**
```

The CEO may propose changes to shared files but must not merge a shared-contract change without CTO and COO review.

## 6. Required Inputs

The CEO depends on:

- Approved Main Spec and Phase 0 decisions;
- `Shared-Integration-Contract.md`;
- OpenAPI schema or contract fixtures from the CTO;
- Evidence Analysis Result fixture from the COO;
- Shared status enums;
- Synthetic demo dataset descriptions;
- Export preview from the CTO;
- Verified source-location examples from the COO.

If a live API is unavailable, build against the frozen shared mock response. Do not invent a frontend-only shape.

## 7. Deliverables

### 7.1 Product Deliverables

- Confirmed page map and normal user journey;
- MVP scope board with Must-have, Should-have, and Deferred items;
- Product decisions recorded with impact and owner;
- Demo narrative aligned with judging criteria;
- Visual acceptance checklist.

### 7.2 Frontend Deliverables

- Case list and Create Case page;
- Intake and upload-processing page;
- Readiness Dashboard;
- Questions Workbench;
- Question Detail and Evidence Drawer/Viewer;
- Human Review controls;
- Priority factor breakdown;
- Actions page with SUBMISSION and IMPROVEMENT separation;
- Export validation and history page;
- Global loading, empty, error, and recovery components;
- Responsive demo layout for agreed viewports.

### 7.3 Demo Deliverables

- Six-to-seven-minute live demo script;
- Reset instructions;
- Backup screenshots or short recording;
- Presenter notes;
- Known-limitations slide;
- Final value statement.

## 8. Page Responsibilities

| Route | Required behavior | Main dependencies |
|---|---|---|
| `/` | List cases with deadline and readiness; create a new case | Case API |
| `/cases/new` | Collect company, customer, deadline, and reporting period | Create Case API |
| `/cases/:id/intake` | Upload files; show processing, failure, retry, and manual-review states | Document and Job APIs |
| `/cases/:id/readiness` | Show status counts, deadline, top gaps, confirmation count, and E/S/G distribution | Case summary API |
| `/cases/:id/questions` | Filter by pillar, evidence status, required flag, priority, and owner | Questions API |
| `/cases/:id/questions/:questionId` | Show original question, mapping, answer, citations, evidence state, review actions, and history | Question Detail API |
| `/cases/:id/actions` | Separate SUBMISSION and IMPROVEMENT actions; manage status and deadlines | Actions API |
| `/cases/:id/export` | Show blocking warnings, export options, history, and download state | Export API |

## 9. Visual and Interaction Rules

Mandatory status presentation:

| Status | Visual treatment | Required supporting content |
|---|---|---|
| VERIFIED | Green | Exact citation and source location |
| PARTIAL | Amber | Missing period, scope, unit, or breakdown |
| OUTDATED | Amber | Source date and required period |
| CONFLICTING | Red | Both conflicting sources |
| MISSING | Red | Explicit missing requirement |
| AI_SUGGESTED | Purple | “Not human confirmed” label |
| NOT_APPLICABLE | Neutral | Human-entered reason |
| NEEDS_MANUAL_REVIEW | Neutral warning | Failure or ambiguity reason |

Rules:

- Never communicate status by color alone;
- Always pair color with text and an icon;
- Never label Submission Readiness as an ESG Performance Score;
- Only `HUMAN_CONFIRMED` required answers count toward readiness;
- AI-generated content must remain visibly distinct until confirmed;
- Conflict screens must not imply that the system selected the correct source;
- Source location must be visible without opening developer tools;
- Destructive actions require confirmation and clear consequences.

## 10. Task Plan

### Phase 0 — Product Freeze

- `CEO-001`: Confirm the product name, user, outcome, and non-goals with the team.
- `CEO-002`: Confirm English UI and Chinese Main Spec, or record another approved language decision.
- `CEO-003`: Confirm the 20-question demo limit and 14-day scenario.
- `CEO-004`: Approve the visible evidence statuses and the distinction between Submission Readiness and ESG Performance.
- `CEO-005`: Approve the first vertical-slice story.
- `CEO-006`: Record blocking decisions and do not authorize feature coding before Gate P0.

### Phase 1 — Frontend Foundation

- `CEO-010`: Bootstrap the web app and shared UI package after stack approval.
- `CEO-011`: Create navigation, layout, typography, and status tokens.
- `CEO-012`: Implement typed contract fixtures; do not use ad hoc page-local mock shapes.
- `CEO-013`: Build Case List and Create Case pages.
- `CEO-014`: Add global loading, empty, error, and retry components.
- `CEO-015`: Add frontend format, lint, type, and component-test commands.

### Phase 2 — Intake

- `CEO-020`: Implement upload drop zone and file table.
- `CEO-021`: Display filename, type, size, checksum availability, and processing status.
- `CEO-022`: Display duplicate, unsupported, parser-failed, retrying, and manual-review states.
- `CEO-023`: Preserve visible state after reload using server data.

### Phase 3 — Questions and Evidence

- `CEO-030`: Implement Questions Workbench with contract-driven filters.
- `CEO-031`: Implement Question Detail and Evidence Drawer.
- `CEO-032`: Display page, sheet/cell, paragraph, or manual source location.
- `CEO-033`: Display the original question and original source row/cell.
- `CEO-034`: Display mapping rationale and allow an approved mapping edit flow.

### Phase 4 — Readiness and Priority

- `CEO-040`: Implement Readiness Dashboard.
- `CEO-041`: Display the five required demo states plus AI Suggested.
- `CEO-042`: Display priority score, all four factors, and each rationale.
- `CEO-043`: Require a reason when users override a factor.
- `CEO-044`: Show top gaps without hiding lower-scored required questions.

### Phase 5 — Review and Actions

- `CEO-050`: Implement Accept, Edit, Reject, and Not Applicable flows.
- `CEO-051`: Make unconfirmed AI drafts visibly excluded from readiness.
- `CEO-052`: Implement Action creation with required type, owner, next step, and deadline.
- `CEO-053`: Separate SUBMISSION and IMPROVEMENT actions.
- `CEO-054`: Implement TODO, IN_PROGRESS, BLOCKED, NEEDS_REVIEW, and COMPLETED states.

### Phase 6 — Export UI

- `CEO-060`: Implement pre-export warning summary.
- `CEO-061`: Display missing required answers, unresolved conflicts, and unconfirmed suggestions.
- `CEO-062`: Implement export generation, failure, retry, ready, and history states.
- `CEO-063`: Review PDF and Evidence Index for clarity, truncation, and citation consistency.

### Phase 7 — Demo Hardening

- `CEO-070`: Complete keyboard flow and focus behavior.
- `CEO-071`: Verify 1366×768 and 1440×900 layouts.
- `CEO-072`: Run visual scenario acceptance with screenshots or traces.
- `CEO-073`: Prepare and rehearse the live demo.
- `CEO-074`: Freeze visual scope before the final integration window.

## 11. Acceptance Criteria

- `CEO-AC-001`: WHEN a first-time user opens the app, THE UI SHALL make the next primary action clear without ESG terminology knowledge.
- `CEO-AC-002`: WHEN a question has any evidence status, THE UI SHALL show text, icon, rationale, and applicable source information.
- `CEO-AC-003`: WHEN an answer is AI_SUGGESTED and unconfirmed, THE UI SHALL NOT present it as verified or count it toward readiness.
- `CEO-AC-004`: WHEN two sources conflict, THE UI SHALL show both sources and SHALL NOT imply that one was selected as correct.
- `CEO-AC-005`: WHEN a user creates an action, THE UI SHALL require type, owner, next step, and deadline.
- `CEO-AC-006`: WHEN export blockers exist, THE UI SHALL show them before export generation.
- `CEO-AC-007`: WHEN a save fails, THE UI SHALL show an unsaved state and SHALL NOT report success.
- `CEO-AC-008`: WHEN the user refreshes a persisted screen, THE UI SHALL restore server state.
- `CEO-AC-009`: WHEN status is communicated by color, THE UI SHALL also communicate it through text and icon.
- `CEO-AC-010`: WHEN the agreed demo dataset is used, THE presenter SHALL complete the core story in seven minutes or less.

## 12. Tests and Evidence

Required evidence:

- Frontend build, lint, type, and component-test results;
- Contract fixture validation;
- Playwright traces for critical user journeys;
- Screenshots at agreed viewports;
- Keyboard and focus test notes;
- Visual review of PDF export;
- Demo rehearsal timing;
- Known visual limitations and deferred work.

The CEO must not approve their own frontend as `accepted` without another team member reviewing the critical scenarios.

## 13. Handoffs

### To CTO

- Page data needs and approved interaction states;
- Contract questions or change proposals;
- Required error codes and recovery behavior;
- Export layout requirements;
- Frontend reproduction steps for integration bugs.

### To COO

- Evidence-card information needs;
- Required source-viewer metadata;
- UI examples of unclear status rationale;
- Demo questions that need a specific AI/evidence result.

### From CTO and COO

- CTO provides stable API fixtures, error envelopes, and persisted behavior;
- COO provides valid AI output fixtures, ground-truth examples, and evidence location samples.

## 14. Stop Conditions

Stop and escalate when:

- A proposed UI would hide uncertainty or unsupported claims;
- The API and UI contracts disagree;
- A shared enum is missing or renamed without approval;
- The design requires real personal or customer data;
- A feature requires changing Main Spec acceptance criteria;
- The final demo cannot be completed reliably and scope must be reduced.

## 15. AI Agent Start Prompt

```text
You are the AI implementation agent for the CEO — Product & Frontend Lead workstream.

Read, in this order:
1. BuktiESG-Technical-Spec-ZH.md
2. Shared-Integration-Contract.md
3. CEO-Product-Frontend-Sub-Spec.md
4. Integration-Checklist.md

The Main Spec is authoritative. Do not change shared contracts, evidence rules,
priority rules, ground truth, critical tests, or protected files to fit your implementation.

Before writing code, return:
- your understanding of the product outcome and non-goals;
- your owned paths and protected paths;
- required inputs from CTO and COO;
- the exact Phase tasks you propose to execute;
- tests and acceptance evidence;
- blocking questions.

Do not start feature implementation until Gate P0 is accepted.
```

