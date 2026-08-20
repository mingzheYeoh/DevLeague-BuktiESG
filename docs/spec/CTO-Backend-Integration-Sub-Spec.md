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

# CTO — Backend & Integration Lead Sub-Spec

Version: 1.0  
Date: 2026-08-21  
Status: `planned`  
Role owner: To be assigned  
Project tier: T1  
Task risk: Yellow  
Enforcement: Advisory-only

## 1. Authority

This Sub-Spec must be used together with `BuktiESG-Technical-Spec-ZH.md`.

The Main Technical Spec is authoritative. This document assigns backend, data, integration, and deployment responsibility only. It cannot override the Main Spec, Shared Integration Contract, evidence rules, priority formula, acceptance criteria, or synthetic-data restriction.

The CTO is the Integration Owner but is not authorized to redefine product success or approve production release alone.

## 2. Mission

Provide a stable, traceable, and recoverable system backbone that connects the web experience to document processing and AI analysis without losing evidence provenance.

The CTO role combines:

- System architecture owner;
- Backend and database lead;
- OpenAPI and shared-contract implementation owner;
- File and job lifecycle owner;
- Export and deployment lead;
- Main-branch integration coordinator.

## 3. Success Outcome

The combined system can persist and reload a complete Case, safely process file lifecycle events, expose stable APIs, accept validated AI results, calculate deterministic business rules, track actions, and generate exports without duplicating or corrupting data.

## 4. Scope

### 4.1 Included

- FastAPI application and OpenAPI contract;
- PostgreSQL schema, constraints, and migrations;
- File-upload validation, checksum, storage adapter, and invalidation;
- Processing job lifecycle and worker integration boundary;
- Case, Document, Question, Answer, Evidence, Priority, Action, Activity Log, and Export services;
- Server-side evidence-state and priority-rule enforcement;
- Idempotency, transactions, pagination, and error envelopes;
- Export renderer and history;
- Integration tests and critical E2E support;
- Local environment, CI proposal, deployment, health checks, and rollback evidence.

### 4.2 Excluded

- Frontend visual implementation;
- OCR, parsing accuracy, SEDG mapping model, retrieval, or LLM prompt design;
- Changing protected ground truth;
- Automatically confirming AI answers;
- Implementing custom authentication for the MVP;
- Processing real sensitive data;
- Production release without accountable approval.

## 5. File Ownership

Primary writable ownership:

```text
apps/api/**
database/**
storage/**
export/**
scripts/dev/**
docker-compose.yml
.env.example
```

Integration ownership, with cross-role review required:

```text
packages/contracts/**
OpenAPI schema
database migrations
.github/workflows/**
deployment/**
```

Protected files require separate review. The CTO may implement migrations and CI changes but must not self-approve them.

## 6. Required Inputs

The CTO depends on:

- Approved Main Spec and Phase 0 decisions;
- Page data needs and visible recovery behavior from the CEO;
- AI Analysis Result schema and processing failure modes from the COO;
- Synthetic fixtures and source-location ground truth;
- Shared enums and contract version;
- Approved storage and deployment decisions;
- Approved file, case, and retention limits.

## 7. Deliverables

### 7.1 Architecture and Contracts

- Architecture decision record;
- OpenAPI specification;
- Shared JSON schemas;
- Service and repository boundaries;
- Database ERD or schema documentation;
- File and job state machines;
- Error-code catalog;
- Integration and rollback plan.

### 7.2 Backend Features

- Case CRUD;
- Document upload, checksum, storage, listing, retry, and soft delete;
- Job status endpoint;
- Questionnaire and Question persistence;
- Answer review and confirmation persistence;
- Evidence candidate, acceptance, rejection, and invalidation;
- Priority assessment and server-side score calculation;
- Action creation, update, completion, and evidence invalidation;
- Activity Log;
- Export validation, generation, history, and download metadata.

### 7.3 Operational Deliverables

- Local startup workflow;
- Health and readiness endpoints;
- Migration commands;
- CI checks;
- Structured logs with request, case, and job identifiers;
- Deployment instructions;
- Demo reset/seed command;
- Rollback instructions and known limitations.

## 8. Core Data Responsibilities

The CTO must implement the Main Spec entities and integrity rules, including:

- Organizations and Cases;
- Documents and Document Chunks;
- Questionnaires and Questions;
- Answers and Evidence Links;
- Priority Assessments;
- Actions;
- AI Runs;
- Activity Logs;
- Exports.

Minimum integrity rules:

- Priority factors are constrained to 0–5;
- Priority score is recalculated on the server;
- Question and Document in an Evidence Link belong to the same Case;
- Document deletion is soft by default;
- Invalidated evidence causes affected answer/action state recalculation;
- Activity Logs cannot be edited through ordinary user APIs;
- Duplicate upload checksum within a Case does not create duplicate processing;
- Mutations use transactions and idempotency where required.

## 9. API Responsibilities

Implement the API families defined by the Main Spec and Shared Integration Contract:

```text
/api/v1/cases
/api/v1/cases/{case_id}/documents
/api/v1/documents/{document_id}
/api/v1/jobs/{job_id}
/api/v1/cases/{case_id}/questions
/api/v1/questions/{question_id}
/api/v1/questions/{question_id}/answer
/api/v1/questions/{question_id}/confirm
/api/v1/questions/{question_id}/reject
/api/v1/questions/{question_id}/evidence
/api/v1/evidence/{evidence_id}
/api/v1/questions/{question_id}/priority
/api/v1/cases/{case_id}/actions
/api/v1/actions/{action_id}
/api/v1/cases/{case_id}/exports
/api/v1/exports/{export_id}
```

API rules:

- Use the shared error envelope;
- Use UTC timestamps and render Asia/Kuala_Lumpur in the UI;
- Support pagination for list endpoints;
- Validate all browser and worker inputs on the server;
- Support `Idempotency-Key` for mutations identified by the contract;
- Never return internal storage paths, prompts, or secrets;
- Keep OpenAPI and implementation compatible through contract tests.

## 10. Deterministic Rule Responsibilities

The CTO owns the executable server-side implementation of rules approved in the Main Spec. The COO may produce recommendations and extracted facts, but the backend determines persisted state.

### Priority Formula

```text
priority_score = 7 * impact
               + 5 * urgency
               + 4 * evidence_gap
               + 4 * feasibility
```

Each factor is an integer from 0 to 5. The server must reject out-of-range input and calculate a score from 0 to 100.

### Human Confirmation

- LLM output cannot set `HUMAN_CONFIRMED`;
- Only a user review endpoint can set confirmation fields;
- Confirmation records reviewer, timestamp, answer text, and evidence IDs;
- Rejection records a reason;
- Unconfirmed AI content is excluded from readiness.

### Evidence Invalidation

- Deleted or invalidated source evidence cannot remain accepted;
- A formerly completed action requiring that evidence returns to `NEEDS_REVIEW`;
- A previously verified answer is recalculated and cannot remain verified without qualifying evidence.

## 11. Task Plan

### Phase 0 — Architecture Freeze

- `CTO-001`: Confirm stack, versions, repository layout, deployment target, and storage approach.
- `CTO-002`: Confirm API, AI output, error, and enum contracts with CEO and COO.
- `CTO-003`: Record ADR-001 for stack and architecture.
- `CTO-004`: Record limits, dependencies, licenses, and material costs.
- `CTO-005`: Define migration, backup, reset, and rollback paths.
- `CTO-006`: Do not implement business features before Gate P0.

### Phase 1 — Repository and Data Foundation

- `CTO-010`: Bootstrap FastAPI and PostgreSQL.
- `CTO-011`: Create health checks and local Docker Compose environment.
- `CTO-012`: Implement the initial versioned schema migration.
- `CTO-013`: Publish OpenAPI and typed contract fixtures.
- `CTO-014`: Configure backend format, lint, type, unit, contract, and secret checks.
- `CTO-015`: Document a one-command local startup path.

### Phase 2 — Case, Files, and Jobs

- `CTO-020`: Implement Case CRUD.
- `CTO-021`: Implement server-side MIME/signature, size, and filename validation.
- `CTO-022`: Implement checksum deduplication and storage adapter.
- `CTO-023`: Implement processing jobs and retry behavior.
- `CTO-024`: Persist chunks and source-location metadata received from the worker.
- `CTO-025`: Implement soft delete and evidence invalidation.

### Phase 3 — Questions and Evidence Integration

- `CTO-030`: Persist questionnaire and question source locations.
- `CTO-031`: Implement mapping read/update history.
- `CTO-032`: Accept only schema-valid AI Analysis Results.
- `CTO-033`: Persist candidate evidence and AI Run metadata.
- `CTO-034`: Expose Question Detail and Evidence endpoints.
- `CTO-035`: Implement candidate acceptance and rejection.

### Phase 4 — Status and Priority

- `CTO-040`: Implement deterministic evidence-state calculation.
- `CTO-041`: Implement period, scope, unit, and conflict inputs from validated evidence.
- `CTO-042`: Implement the priority formula and factor constraints.
- `CTO-043`: Implement user override reason and Activity Log.
- `CTO-044`: Implement readiness calculation from confirmed required answers only.

### Phase 5 — Review and Actions

- `CTO-050`: Implement answer edit, confirm, reject, and not-applicable endpoints.
- `CTO-051`: Implement SUBMISSION and IMPROVEMENT actions.
- `CTO-052`: Require owner, next step, deadline, and action type.
- `CTO-053`: Implement completion note and closure evidence.
- `CTO-054`: Reopen affected actions after closure-evidence invalidation.

### Phase 6 — Export

- `CTO-060`: Implement pre-export validation warnings.
- `CTO-061`: Generate Customer Response Summary.
- `CTO-062`: Generate Evidence Index in CSV/XLSX.
- `CTO-063`: Generate Outstanding Actions Summary.
- `CTO-064`: Generate PDF and preserve export version, content hash, and warnings.
- `CTO-065`: Implement failure and retry without modifying Case state.

### Phase 7 — Reliability and Security

- `CTO-070`: Test malformed input, duplicate submission, refresh, concurrency, and wrong-Case IDs.
- `CTO-071`: Run dependency, license, secret, path traversal, and MIME spoofing checks.
- `CTO-072`: Measure API, parsing orchestration, export, and cost metrics.
- `CTO-073`: Implement structured logs without sensitive full text.
- `CTO-074`: Create reset, seed, and backup/recovery instructions.

### Phase 8 — Deployment and Handoff

- `CTO-080`: Produce an immutable build and preview deployment.
- `CTO-081`: Rehearse migrations and rollback.
- `CTO-082`: Run critical smoke and E2E tests.
- `CTO-083`: Provide build, dependency, data, permission, cost, and recovery evidence.
- `CTO-084`: Wait for explicit release approval.

## 12. Acceptance Criteria

- `CTO-AC-001`: WHEN the same file checksum is uploaded twice to one Case, THE SYSTEM SHALL return the existing document and SHALL NOT create duplicate processing.
- `CTO-AC-002`: WHEN an AI result fails the shared JSON schema, THE SYSTEM SHALL reject it as a persisted answer result and record a recoverable failure.
- `CTO-AC-003`: WHEN evidence has no valid source location, THE SYSTEM SHALL NOT persist the answer as VERIFIED.
- `CTO-AC-004`: WHEN a user submits an out-of-range priority factor, THE SYSTEM SHALL reject the request and SHALL NOT trust the client-calculated score.
- `CTO-AC-005`: WHEN a user confirms an answer, THE SYSTEM SHALL persist reviewer, timestamp, final text, and evidence IDs.
- `CTO-AC-006`: WHEN source evidence is invalidated, THE SYSTEM SHALL recalculate affected answers and actions.
- `CTO-AC-007`: WHEN an export fails, THE SYSTEM SHALL keep Case data unchanged and allow retry.
- `CTO-AC-008`: WHEN a mutation is repeated with the same required Idempotency-Key, THE SYSTEM SHALL NOT create a duplicate business object.
- `CTO-AC-009`: WHEN a request references an object from another Case, THE SYSTEM SHALL reject the request.
- `CTO-AC-010`: WHEN the application restarts, persisted Case, processing, review, and Action state SHALL remain available.

## 13. Tests and Evidence

Required evidence:

- Build, format, lint, type, and unit results;
- OpenAPI and JSON-schema contract tests;
- Migration up/down or rollback evidence appropriate to the chosen tool;
- Data-integrity and transaction tests;
- Idempotency and concurrency tests;
- Wrong-Case object tests;
- File validation and path tests;
- Export integration tests;
- Health, deployment, and recovery evidence;
- Dependency, license, secret, and cost reports;
- Critical E2E support traces.

## 14. Integration Responsibilities

The CTO is responsible for scheduling merge windows and preserving a runnable main branch.

Rules:

- Use short-lived branches;
- Merge shared contracts before dependent implementation;
- Require contract tests before merging API or AI changes;
- Do not merge a migration that has not been reviewed;
- Do not rewrite frontend or AI work to bypass a contract disagreement;
- Record breaking changes and version the contract;
- Publish stable mock fixtures so the CEO and COO can work in parallel.

## 15. Handoffs

### To CEO

- OpenAPI and typed fixtures;
- Error-code and recovery behavior;
- Processing and export states;
- Preview environment and reproduction steps;
- Known backend limits.

### To COO

- Worker input/output endpoints or service interface;
- Document and chunk persistence format;
- AI Run persistence format;
- Retry, timeout, and validation-failure handling;
- Contract-test fixtures.

### From CEO and COO

- CEO provides visible data requirements and error/recovery expectations;
- COO provides schema-valid parsing and AI fixtures plus expected failure modes.

## 16. Stop Conditions

Stop and escalate when:

- A proposed integration requires real sensitive data;
- A contract change breaks another role and has not been approved;
- A migration is destructive or lacks recovery evidence;
- An AI output would bypass deterministic validation;
- Authentication, authorization, or multi-tenancy is added without reclassification;
- The same gate fails three repair cycles without materially new evidence.

## 17. AI Agent Start Prompt

```text
You are the AI implementation agent for the CTO — Backend & Integration Lead workstream.

Read, in this order:
1. BuktiESG-Technical-Spec-ZH.md
2. Shared-Integration-Contract.md
3. CTO-Backend-Integration-Sub-Spec.md
4. Integration-Checklist.md

The Main Spec is authoritative. You are the integration implementer, not the authority
to change product outcomes, evidence rules, priority rules, ground truth, critical tests,
migrations, release gates, or protected contracts without approval.

Before writing code, return:
- your understanding of the architecture and non-goals;
- your owned paths and protected paths;
- required inputs from CEO and COO;
- Phase tasks and migration plan;
- contract, integrity, security, and recovery tests;
- blocking decisions.

Do not start feature implementation until Gate P0 is accepted.
```

