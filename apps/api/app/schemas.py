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
    created_at: datetime

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
            created_at=doc.created_at,
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
        links = list(question.evidence_links or [])
        if links:
            latest_link = max(links, key=lambda link: link.created_at)
            try:
                evidence_loc = SourceLocation.model_validate(
                    json.loads(latest_link.location_json)
                )
            except (ValueError, TypeError):
                evidence_loc = None

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
        )


class ActionCreate(BaseModel):
    question_id: str | None = None
    type: str = "SUBMISSION"
    title: str
    owner_name: str | None = None
    owner_role: str | None = None
    next_step: str | None = None
    deadline_at: datetime | None = None


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
    closure_evidence_document_id: str | None
    created_at: datetime
    updated_at: datetime

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
            closure_evidence_document_id=action.closure_evidence_document_id,
            created_at=action.created_at,
            updated_at=action.updated_at,
        )
