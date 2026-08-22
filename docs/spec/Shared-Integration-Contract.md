<!-- Phase 0 document-control banner. Added by the documentation-only Phase 0 bootstrap commit. -->

## Document Control Banner

| Field | Value |
|---|---|
| Status | **PROPOSED** |
| Gate P0 | **BLOCKED** |
| Version of the text below | **v1.0.0** (unchanged) |
| Contract target | **v1.1.0 — NOT FROZEN** |
| Main Spec target | **v1.1 — NOT ACCEPTED** |
| Feature implementation | **NOT AUTHORIZED** |
| Implementations | **Zero.** This contract has never been accepted, implemented, or consumed by any client. |

**The body below is unchanged v1.0.0 text and is retained as the auditable baseline.**

Contract **v1.1.0 is proposed, not frozen.** Every proposed change is recorded as a delta in [`Shared-Integration-Contract-v1.1.0-PROPOSED.md`](Shared-Integration-Contract-v1.1.0-PROPOSED.md) and has **not** been merged into the text below.

Contract change control requires **CEO + CTO + COO** approval. Only the CTO has ruled. Do not implement against either version.

**Known defects in the v1.0.0 text below** (all addressed in the v1.1.0 proposal, none corrected here): `GET /api/v1/jobs/{job_id}` references a resource that is never defined; `pillar` and `export_type` appear in example payloads with no canonical enum; pagination is declared but never shaped; the concurrency guard and idempotency scope are both deferred to "Phase 0" with no value supplied.

---

# BuktiESG Shared Integration Contract

Contract version: 1.0.0  
Date: 2026-08-21  
Status: `planned` until Phase 0 approval  
Authority: Below Main Technical Spec; above Role Sub-Specs  
Change approval: CEO + CTO + COO

## 1. Purpose

This contract allows the frontend, backend, and AI/document workstreams to operate in parallel without inventing incompatible data shapes.

The Main Technical Spec remains authoritative. This contract defines shared names, interface shapes, ownership boundaries, and change control. It does not replace the Main Spec's full data model or acceptance criteria.

## 2. Contract Rules

1. All IDs are opaque strings. UUID is recommended but clients must not infer meaning from IDs.
2. All timestamps use ISO 8601 UTC, for example `2026-08-21T14:30:00Z`.
3. The UI renders local time using `Asia/Kuala_Lumpur`.
4. Enum values are uppercase snake case and must not be renamed locally.
5. Optional values use `null`; missing required fields fail validation.
6. Unknown enum values must produce an explicit compatibility error, not a silent fallback.
7. AI results must pass JSON Schema before persistence.
8. Frontend requests and worker outputs are untrusted and must be validated by the API.
9. No interface may expose secrets, internal server paths, raw provider credentials, or unrelated Case data.
10. Breaking changes require a contract version update and all-role approval.

## 3. Shared Enums

### 3.1 Case Status

```text
DRAFT
PROCESSING
IN_REVIEW
READY
EXPORTED
ARCHIVED
```

### 3.2 Document Type

```text
QUESTIONNAIRE
UTILITY_BILL
POLICY
HR_DATA
WASTE_RECORD
SAFETY_RECORD
OTHER
```

### 3.3 Document Processing Status

```text
UPLOADED
PARSING
PARSED
INDEXED
FAILED
NEEDS_MANUAL_REVIEW
```

### 3.4 Evidence Status

```text
VERIFIED
PARTIAL
OUTDATED
CONFLICTING
MISSING
AI_SUGGESTED
NOT_APPLICABLE
NEEDS_MANUAL_REVIEW
```

### 3.5 Review Status

```text
UNREVIEWED
HUMAN_CONFIRMED
REJECTED
NEEDS_REVISION
```

### 3.6 Evidence Link Status

```text
CANDIDATE
ACCEPTED
REJECTED
INVALIDATED
```

### 3.7 Action Type

```text
SUBMISSION
IMPROVEMENT
```

### 3.8 Action Status

```text
TODO
IN_PROGRESS
BLOCKED
NEEDS_REVIEW
COMPLETED
```

### 3.9 Export Status

```text
QUEUED
GENERATING
READY
FAILED
```

## 4. Source Location Contract

Every evidence item must include one location object.

### Page Location

```json
{
  "type": "page",
  "page_number": 2,
  "bounding_box": null
}
```

### Spreadsheet Location

```json
{
  "type": "sheet_cell",
  "sheet_name": "Energy Data",
  "cell_range": "B12:F12"
}
```

### Paragraph Location

```json
{
  "type": "paragraph",
  "heading_path": ["Anti-Bribery Policy", "Approval"],
  "paragraph_index": 14
}
```

### Manual Location

```json
{
  "type": "manual",
  "description": "User-entered statement; no source document"
}
```

A manual location cannot independently qualify an answer as VERIFIED.

## 5. Common Error Envelope

All API errors use:

```json
{
  "error": {
    "code": "DOCUMENT_PARSE_FAILED",
    "message": "The document could not be parsed.",
    "details": {
      "document_id": "doc_123",
      "retry_allowed": true
    },
    "request_id": "req_123"
  }
}
```

Minimum shared error codes:

```text
VALIDATION_ERROR
UNSUPPORTED_FILE_TYPE
FILE_TOO_LARGE
DUPLICATE_DOCUMENT
DOCUMENT_PARSE_FAILED
OCR_FAILED
AI_TIMEOUT
AI_SCHEMA_INVALID
CASE_NOT_FOUND
OBJECT_CASE_MISMATCH
CONCURRENT_UPDATE
EXPORT_BLOCKED
EXPORT_FAILED
INTERNAL_ERROR
```

## 6. API Contract Summary

The OpenAPI document implemented by the CTO is the executable API contract. The following endpoints are required by the Main Spec.

### Cases

```text
POST   /api/v1/cases
GET    /api/v1/cases
GET    /api/v1/cases/{case_id}
PATCH  /api/v1/cases/{case_id}
```

### Documents and Jobs

```text
POST   /api/v1/cases/{case_id}/documents
GET    /api/v1/cases/{case_id}/documents
GET    /api/v1/documents/{document_id}
POST   /api/v1/documents/{document_id}/retry
DELETE /api/v1/documents/{document_id}
GET    /api/v1/jobs/{job_id}
```

### Questions and Answers

```text
GET    /api/v1/cases/{case_id}/questions
GET    /api/v1/questions/{question_id}
PATCH  /api/v1/questions/{question_id}/mapping
POST   /api/v1/questions/{question_id}/analyze
PATCH  /api/v1/questions/{question_id}/answer
POST   /api/v1/questions/{question_id}/confirm
POST   /api/v1/questions/{question_id}/reject
```

### Evidence

```text
GET    /api/v1/questions/{question_id}/evidence
POST   /api/v1/questions/{question_id}/evidence
PATCH  /api/v1/evidence/{evidence_id}
POST   /api/v1/evidence/{evidence_id}/accept
POST   /api/v1/evidence/{evidence_id}/reject
```

### Priority and Actions

```text
GET    /api/v1/questions/{question_id}/priority
PUT    /api/v1/questions/{question_id}/priority
POST   /api/v1/cases/{case_id}/actions
GET    /api/v1/cases/{case_id}/actions
PATCH  /api/v1/actions/{action_id}
POST   /api/v1/actions/{action_id}/complete
```

### Exports

```text
POST   /api/v1/cases/{case_id}/exports
GET    /api/v1/cases/{case_id}/exports
GET    /api/v1/exports/{export_id}
```

## 7. Shared Response Shapes

### 7.1 Case Summary

```json
{
  "id": "case_123",
  "title": "Major Customer ESG Questionnaire",
  "customer_name": "Demo FMCG Customer",
  "deadline_at": "2026-09-04T16:00:00Z",
  "reporting_period": {
    "start": "2025-01-01",
    "end": "2025-12-31"
  },
  "status": "IN_REVIEW",
  "readiness": {
    "confirmed_required_questions": 7,
    "total_required_questions": 12,
    "percentage": 58.33
  },
  "evidence_status_counts": {
    "VERIFIED": 4,
    "PARTIAL": 3,
    "OUTDATED": 2,
    "CONFLICTING": 2,
    "MISSING": 5,
    "AI_SUGGESTED": 4,
    "NOT_APPLICABLE": 0,
    "NEEDS_MANUAL_REVIEW": 0
  },
  "unconfirmed_answer_count": 5,
  "updated_at": "2026-08-21T14:30:00Z"
}
```

### 7.2 Document Record

```json
{
  "id": "doc_123",
  "case_id": "case_123",
  "original_filename": "tnb-bills-jan-mar-2025.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 482310,
  "sha256": "hex-string",
  "document_type": "UTILITY_BILL",
  "processing_status": "INDEXED",
  "source_date": "2025-03-31",
  "period_start": "2025-01-01",
  "period_end": "2025-03-31",
  "error": null,
  "created_at": "2026-08-21T14:30:00Z"
}
```

### 7.3 Question List Item

```json
{
  "id": "question_001",
  "external_question_id": "Q-E-01",
  "question_text": "Report annual electricity consumption.",
  "is_required": true,
  "pillar": "E",
  "sedg_topic_code": "E2",
  "sedg_disclosure_code": "SEDG-E2.1",
  "evidence_status": "PARTIAL",
  "review_status": "UNREVIEWED",
  "priority_score": 82,
  "owner_name": "Finance Manager",
  "source_location": {
    "type": "sheet_cell",
    "sheet_name": "Questionnaire",
    "cell_range": "B7"
  }
}
```

### 7.4 Evidence Candidate

```json
{
  "id": "evidence_001",
  "document_id": "doc_123",
  "chunk_id": "chunk_123",
  "document_name": "tnb-bills-jan-mar-2025.pdf",
  "location": {
    "type": "page",
    "page_number": 2,
    "bounding_box": null
  },
  "quoted_excerpt": "Total consumption: 12,840 kWh",
  "claim_supported": "Electricity consumed in January 2025",
  "period_start": "2025-01-01",
  "period_end": "2025-01-31",
  "scope_description": "Selangor manufacturing site",
  "value": "12840",
  "unit": "kWh",
  "extraction_method": "docling_text",
  "extraction_confidence": 0.96,
  "link_status": "CANDIDATE",
  "created_by": "SYSTEM"
}
```

### 7.5 Priority Assessment

```json
{
  "impact": 3,
  "urgency": 5,
  "evidence_gap": 4,
  "feasibility": 5,
  "score": 82,
  "rationale": {
    "impact": "Energy use is a core environmental disclosure.",
    "urgency": "The required customer question is due within 14 days.",
    "evidence_gap": "Nine months of bills are missing.",
    "feasibility": "Finance can retrieve the remaining bills."
  },
  "source": "SYSTEM_SUGGESTED"
}
```

### 7.6 Question Detail

```json
{
  "id": "question_001",
  "external_question_id": "Q-E-01",
  "question_text": "Report annual electricity consumption.",
  "is_required": true,
  "source_location": {
    "type": "sheet_cell",
    "sheet_name": "Questionnaire",
    "cell_range": "B7"
  },
  "mapping": {
    "pillar": "E",
    "sedg_topic_code": "E2",
    "sedg_disclosure_code": "SEDG-E2.1",
    "rationale": "The question requests electricity consumption."
  },
  "answer": {
    "draft_answer": "38,420 kWh is evidenced for January to March 2025.",
    "confirmed_answer": null,
    "evidence_status": "PARTIAL",
    "status_reason": "Only 3 of the required 12 months are supported.",
    "review_status": "UNREVIEWED",
    "reviewer_name": null,
    "reviewed_at": null
  },
  "evidence": [],
  "missing_elements": ["Electricity bills for April to December 2025"],
  "possible_conflicts": [],
  "suggested_follow_up": "Ask Finance to retrieve the remaining nine monthly bills.",
  "priority": {},
  "activity": []
}
```

### 7.7 Action

```json
{
  "id": "action_001",
  "case_id": "case_123",
  "question_id": "question_001",
  "type": "SUBMISSION",
  "title": "Collect missing electricity bills",
  "owner_name": "Finance Manager",
  "owner_role": "Finance",
  "next_step": "Download April to December 2025 bills.",
  "deadline_at": "2026-08-28T09:00:00Z",
  "status": "TODO",
  "completion_note": null,
  "closure_evidence_document_id": null,
  "created_at": "2026-08-21T14:30:00Z",
  "updated_at": "2026-08-21T14:30:00Z"
}
```

## 8. AI Analysis Result Contract

The COO pipeline returns the following object to the backend. The backend validates and persists it. It does not accept final review state from AI.

```json
{
  "schema_version": "1.0.0",
  "question_id": "question_001",
  "draft_answer": "38,420 kWh is evidenced for January to March 2025.",
  "mapping": {
    "pillar": "E",
    "sedg_topic_code": "E2",
    "sedg_disclosure_code": "SEDG-E2.1",
    "rationale": "The question requests electricity consumption."
  },
  "candidate_evidence": [
    {
      "chunk_id": "chunk_123",
      "claim_supported": "Electricity consumed in January 2025",
      "quoted_excerpt": "Total consumption: 12,840 kWh",
      "period_start": "2025-01-01",
      "period_end": "2025-01-31",
      "scope_description": "Selangor manufacturing site",
      "value": "12840",
      "unit": "kWh"
    }
  ],
  "missing_elements": ["Electricity bills for April to December 2025"],
  "possible_conflicts": [],
  "suggested_follow_up": "Ask Finance to retrieve the remaining nine monthly bills.",
  "priority_recommendation": {
    "impact": 3,
    "urgency": 5,
    "evidence_gap": 4,
    "feasibility": 5,
    "rationale": {
      "impact": "Energy use is a core environmental disclosure.",
      "urgency": "The question is required and due within 14 days.",
      "evidence_gap": "Nine months are missing.",
      "feasibility": "Finance can retrieve existing bills."
    }
  },
  "run_metadata": {
    "provider": "provider-adapter-name",
    "model": "model-name",
    "prompt_version": "evidence-analysis-v1",
    "input_hash": "hex-string",
    "source_ids": ["chunk_123"],
    "latency_ms": 1240,
    "estimated_cost": 0.01
  }
}
```

Forbidden AI fields:

```text
review_status = HUMAN_CONFIRMED
final_compliance_status
audit_passed
certified
conflict_winner
customer_submission_approved
```

If these appear, schema or business validation must reject them.

## 9. Readiness Contract

```text
readiness_percentage = confirmed_required_questions
                     / total_required_questions
                     * 100
```

Only required answers with `review_status = HUMAN_CONFIRMED` count in the numerator.

Readiness is response readiness, not an ESG score or ESG performance rating.

## 10. Priority Contract

```text
score = 7 * impact
      + 5 * urgency
      + 4 * evidence_gap
      + 4 * feasibility
```

Rules:

- Each factor is an integer from 0 to 5;
- The server calculates the final score;
- AI and UI may recommend or edit factors, but cannot provide the authoritative score;
- User overrides require a reason and Activity Log entry;
- The factor rationale is visible in the UI and export.

## 11. Idempotency and Concurrency

- Case creation, upload, action creation, answer confirmation, and export creation should accept `Idempotency-Key` where implemented by the OpenAPI contract;
- Duplicate file checksum within one Case returns the existing Document;
- Concurrent updates use a version, ETag, or updated-at guard chosen in Phase 0;
- A stale update returns `CONCURRENT_UPDATE` and does not silently overwrite newer state;
- Retried worker output uses job and input hash to avoid duplicate AI Run/evidence creation.

## 12. Contract Tests

Minimum tests:

1. Frontend fixtures validate against OpenAPI/shared schemas;
2. API responses validate against OpenAPI;
3. AI Analysis Results validate against the AI schema;
4. Unknown enum values fail visibly;
5. Missing source locations fail evidence validation;
6. Forbidden AI fields fail validation;
7. Priority score is recomputed on the server;
8. Wrong-Case object references fail;
9. Duplicate idempotent mutations do not duplicate objects;
10. Contract version is included in fixture and AI result tests.

## 13. Contract Change Process

Any change must include:

- Change ID and proposer;
- Reason and user-visible impact;
- Affected CEO, CTO, and COO tasks;
- Backward-compatible or breaking classification;
- Updated schema/OpenAPI and fixtures;
- Updated contract tests;
- Migration or rollout note where applicable;
- Approval from all three role owners.

Breaking changes increment the major version. Additive compatible changes increment the minor version. Clarifications or non-behavioral fixes increment the patch version.

No role may silently rename fields, enums, routes, or status semantics in its own implementation.
