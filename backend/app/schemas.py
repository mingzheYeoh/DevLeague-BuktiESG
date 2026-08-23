"""Pydantic v2 request/response schemas.

Response shapes follow docs/spec/Shared-Integration-Contract.md §7, narrowed
to the fields this slice actually populates. Fields the Contract examples
show but this slice does not compute (evidence, priority, activity, ...) are
included where the Contract marks them as always-present with an empty/
default value (e.g. Question List Item), and omitted where the endpoint
itself is out of this slice's scope.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)
    request_id: str | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


class ReportingPeriod(BaseModel):
    start: date | None = None
    end: date | None = None


class CaseCreate(BaseModel):
    title: str
    customer_name: str | None = None
    deadline_at: datetime | None = None
    reporting_period_start: date | None = None
    reporting_period_end: date | None = None


class ReadinessSummary(BaseModel):
    confirmed_required_questions: int = 0
    total_required_questions: int = 0
    percentage: float = 0.0


class CaseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    customer_name: str | None
    deadline_at: datetime | None
    status: str
    updated_at: datetime

    @classmethod
    def from_model(cls, case) -> "CaseSummary":
        return cls(
            id=case.id,
            title=case.title,
            customer_name=case.customer_name,
            deadline_at=case.deadline_at,
            status=case.status,
            updated_at=case.updated_at,
        )


class DocumentRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    original_filename: str
    mime_type: str
    size_bytes: int
    sha256: str
    document_type: str
    processing_status: str
    source_date: date | None = None
    period_start: date | None = None
    period_end: date | None = None
    error: str | None = None
    # SPEC-AMD-001: lets a refreshed client reach GET /api/v1/jobs/{job_id}
    # without any other lookup. Null only for a Document created before this
    # column existed (pre-migration data).
    latest_job_id: str | None = None
    created_at: datetime
    # Additive, display-only (Main Spec §17 Phase 3 "column-mapping
    # confirmation UI"): header name -> spreadsheet column letter, as
    # detected for a QUESTIONNAIRE document on this same upload/retry
    # response. Not persisted anywhere -- read off a transient attribute set
    # during this request's job run (app/services/jobs.py
    # `_run_questionnaire_parse`) -- so it is only present on the response
    # to the request that actually parsed the file, never on a later
    # GET /documents. Null for any non-QUESTIONNAIRE document, or if the
    # attribute wasn't set (e.g. parse failed before reaching that point).
    detected_columns: dict[str, str] | None = None

    @classmethod
    def from_model(cls, doc) -> "DocumentRecord":
        return cls(
            id=doc.id,
            case_id=doc.case_id,
            original_filename=doc.original_filename,
            mime_type=doc.mime_type,
            size_bytes=doc.size_bytes,
            sha256=doc.sha256,
            document_type=doc.document_type,
            processing_status=doc.processing_status,
            source_date=doc.source_date,
            period_start=doc.period_start,
            period_end=doc.period_end,
            error=doc.error_message,
            latest_job_id=doc.latest_job_id,
            created_at=doc.created_at,
            detected_columns=getattr(doc, "_detected_columns", None) or None,
        )


class SourceLocation(BaseModel):
    """One of the Contract §4 location shapes. Kept loose (extra fields
    allowed per type) rather than a discriminated union, since this slice
    only ever produces the ``manual``/``paragraph`` shapes from the stub
    questionnaire parser."""

    model_config = ConfigDict(extra="allow")

    type: str


class QuestionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    external_question_id: str | None
    question_text: str
    is_required: bool
    pillar: str
    sedg_topic_code: str | None
    sedg_disclosure_code: str | None
    evidence_status: str
    review_status: str
    priority_score: int | None = None
    owner_name: str | None = None
    source_location: SourceLocation | None = None
    status_reason: str | None = None
    # Additive, slice-scope field: the SERVER-resolved location of the most
    # recent evidence_links candidate for this question, resolved from
    # persisted document_chunks (never a location the AI pipeline supplied —
    # AGENTS.md §3.3). Distinct from `source_location` above, which is where
    # the QUESTION itself was found in the questionnaire, not where its
    # evidence was found.
    evidence_location: SourceLocation | None = None
    # Additive (Main Spec §17 Phase 3): draft rationale from
    # ai_pipeline.map_question_to_sedg() for this question's pillar/SEDG
    # mapping. A human-reviewable recommendation, never a verdict — must
    # never be read as equivalent to evidence_status or review_status
    # (AGENTS.md §3.2).
    mapping_rationale: str | None = None
    # Additive (Main Spec §17 Phase 3 "Question Detail source viewer"): the
    # excerpt text and claim from the most recent evidence_links candidate
    # for this question — the actual quoted text, not just its location
    # chip. Same AI-suggestion status as evidence_location: unconfirmed
    # until a human reviews it.
    evidence_excerpt: str | None = None
    evidence_claim_supported: str | None = None

    @classmethod
    def from_model(cls, question) -> "QuestionListItem":
        import json

        answer = question.answer
        loc = None
        if question.source_location:
            try:
                loc = SourceLocation.model_validate(json.loads(question.source_location))
            except (ValueError, TypeError):
                loc = None

        evidence_loc = None
        evidence_excerpt = None
        evidence_claim_supported = None
        links = list(question.evidence_links or [])
        if links:
            latest_link = max(links, key=lambda link: link.created_at)
            try:
                evidence_loc = SourceLocation.model_validate(
                    json.loads(latest_link.location_json)
                )
            except (ValueError, TypeError):
                evidence_loc = None
            evidence_excerpt = latest_link.quoted_excerpt
            evidence_claim_supported = latest_link.claim_supported

        return cls(
            id=question.id,
            external_question_id=question.external_question_id,
            question_text=question.question_text,
            is_required=question.is_required,
            pillar=question.pillar,
            sedg_topic_code=question.sedg_topic_code,
            sedg_disclosure_code=question.sedg_disclosure_code,
            evidence_status=answer.evidence_status if answer else "MISSING",
            review_status=answer.review_status if answer else "UNREVIEWED",
            priority_score=None,
            owner_name=None,
            source_location=loc,
            status_reason=answer.status_reason if answer else None,
            evidence_location=evidence_loc,
            mapping_rationale=question.mapping_rationale,
            evidence_excerpt=evidence_excerpt,
            evidence_claim_supported=evidence_claim_supported,
        )


class ActionCreate(BaseModel):
    question_id: str | None = None
    type: str = "SUBMISSION"
    title: str
    # Optional at the Pydantic layer on purpose: the API layer
    # (app/routers/actions.py) enforces "owner, next_step, and deadline
    # required" per Gate P5, and returns the project's custom
    # VALIDATION_ERROR envelope rather than FastAPI's default 422 shape.
    owner_name: str | None = None
    owner_role: str | None = None
    next_step: str | None = None
    deadline_at: datetime | None = None
    # Optional override. When omitted, the server auto-derives this from
    # the linked question's current evidence_status (MISSING/CONFLICTING
    # -> True) at creation time — see app/routers/actions.py.
    requires_closure_evidence: bool | None = None


class ActionStatusUpdate(BaseModel):
    status: str
    completion_note: str | None = None
    closure_evidence_link_id: str | None = None


class ActionRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    question_id: str | None
    type: str
    title: str
    owner_name: str | None
    owner_role: str | None
    next_step: str | None
    deadline_at: datetime | None
    status: str
    completion_note: str | None
    requires_closure_evidence: bool
    closure_evidence_link_id: str | None
    closure_evidence_document_id: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    @classmethod
    def from_model(cls, action) -> "ActionRecord":
        return cls(
            id=action.id,
            case_id=action.case_id,
            question_id=action.question_id,
            type=action.type,
            title=action.title,
            owner_name=action.owner_name,
            owner_role=action.owner_role,
            next_step=action.next_step,
            deadline_at=action.deadline_at,
            status=action.status,
            completion_note=action.completion_note,
            requires_closure_evidence=action.requires_closure_evidence,
            closure_evidence_link_id=action.closure_evidence_link_id,
            closure_evidence_document_id=action.closure_evidence_document_id,
            created_at=action.created_at,
            updated_at=action.updated_at,
            completed_at=action.completed_at,
        )


class QuestionReviewRequest(BaseModel):
    action: str
    reviewer_name: str | None = None
    edited_answer: str | None = None
    reason: str | None = None


class AnswerRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question_id: str
    draft_answer: str | None
    confirmed_answer: str | None
    evidence_status: str
    status_reason: str | None
    review_status: str
    review_reason: str | None
    reviewer_name: str | None
    reviewed_at: datetime | None
    not_applicable_reason: str | None
    draft_provenance: str
    updated_at: datetime

    @classmethod
    def from_model(cls, answer) -> "AnswerRecord":
        return cls(
            id=answer.id,
            question_id=answer.question_id,
            draft_answer=answer.draft_answer,
            confirmed_answer=answer.confirmed_answer,
            evidence_status=answer.evidence_status,
            status_reason=answer.status_reason,
            review_status=answer.review_status,
            review_reason=answer.review_reason,
            reviewer_name=answer.reviewer_name,
            reviewed_at=answer.reviewed_at,
            not_applicable_reason=answer.not_applicable_reason,
            draft_provenance=answer.draft_provenance,
            updated_at=answer.updated_at,
        )


class EvidenceLinkRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question_id: str
    document_id: str
    link_status: str
    value: str | None
    scope_description: str | None
    period_start: date | None
    period_end: date | None

    @classmethod
    def from_model(cls, link) -> "EvidenceLinkRecord":
        return cls(
            id=link.id,
            question_id=link.question_id,
            document_id=link.document_id,
            link_status=link.link_status,
            value=link.value,
            scope_description=link.scope_description,
            period_start=link.period_start,
            period_end=link.period_end,
        )
