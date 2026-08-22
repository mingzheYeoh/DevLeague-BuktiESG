"""SQLAlchemy 2.0 ORM models — First Vertical Slice schema.

Field lists follow docs/spec/BuktiESG-Technical-Spec-EN.md §10.1, narrowed to
what the First Vertical Slice needs (docs/spec/README-Team-Specs.md):

    Create Case -> upload one questionnaire -> identify questions
                -> persist a SUBMISSION action -> persist/reload

Tables built: organizations (minimal, only to satisfy cases.organization_id
per decision-register.md §4 item 014 — "single seeded organization row"),
cases, documents, document_chunks, questionnaires, questions, answers,
evidence_links, actions.

NOT built in this slice (deliberately out of scope): priority_assessments,
ai_runs, activity_logs, exports, processing_jobs. `answers.ai_run_id` and
`evidence_links` extraction-provenance columns are present as plain nullable
columns (spec fields) but nothing in this slice writes a real AI run — see
app/services/rules.py, the stubbed deterministic rule engine.

Enums: TEXT + CHECK constraint, never native PostgreSQL ENUM (RULING-01).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.enums import (
    ACTION_STATUS,
    ACTION_TYPE,
    CASE_STATUS,
    DOCUMENT_PROCESSING_STATUS,
    DOCUMENT_TYPE,
    DRAFT_PROVENANCE,
    EVIDENCE_CREATED_BY,
    EVIDENCE_LINK_STATUS,
    EVIDENCE_STATUS,
    PILLAR,
    REVIEW_STATUS,
    check_in,
)


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255))
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employee_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    cases: Mapped[list["Case"]] = relationship(back_populates="organization")


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=True
    )
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(500))
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reporting_period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    reporting_period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    organization: Mapped[Organization | None] = relationship(back_populates="cases")
    documents: Mapped[list["Document"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    questionnaires: Mapped[list["Questionnaire"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    actions: Mapped[list["Action"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )

    __table_args__ = (CheckConstraint(check_in("status", CASE_STATUS), name="ck_cases_status"),)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str] = mapped_column(String(255))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(String(1000))
    document_type: Mapped[str] = mapped_column(String(30), default="OTHER")
    processing_status: Mapped[str] = mapped_column(String(30), default="UPLOADED")
    source_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    case: Mapped[Case] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(check_in("document_type", DOCUMENT_TYPE), name="ck_documents_type"),
        CheckConstraint(
            check_in("processing_status", DOCUMENT_PROCESSING_STATUS),
            name="ck_documents_processing_status",
        ),
        UniqueConstraint("case_id", "sha256", name="uq_documents_case_sha256"),
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id"), nullable=False
    )
    sequence_no: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sheet_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cell_range: Mapped[str | None] = mapped_column(String(60), nullable=True)
    heading_path: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-encoded list
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    # embedding intentionally omitted: pgvector is out of scope for this slice
    # (no evidence-matching pipeline is implemented here).

    document: Mapped[Document] = relationship(back_populates="chunks")


class Questionnaire(Base):
    __tablename__ = "questionnaires"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(500))
    version: Mapped[str | None] = mapped_column(String(60), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    case: Mapped[Case] = relationship(back_populates="questionnaires")
    questions: Mapped[list["Question"]] = relationship(
        back_populates="questionnaire", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    questionnaire_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("questionnaires.id"), nullable=False
    )
    external_question_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_location: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-encoded
    section: Mapped[str | None] = mapped_column(String(255), nullable=True)
    question_text: Mapped[str] = mapped_column(Text)
    is_required: Mapped[bool] = mapped_column(default=True)
    pillar: Mapped[str] = mapped_column(String(20), default="UNCATEGORIZED")
    sedg_topic_code: Mapped[str | None] = mapped_column(String(30), nullable=True)
    sedg_disclosure_code: Mapped[str | None] = mapped_column(String(30), nullable=True)
    mapping_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_requirement_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    # SPEC-AMD-007 / RULING-04: persisted deterministic ordering, assigned at
    # import time from workbook/sheet/row traversal order. Never re-derived
    # from display strings (external_question_id, section, ...).
    question_order: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    questionnaire: Mapped[Questionnaire] = relationship(back_populates="questions")
    answer: Mapped["Answer | None"] = relationship(
        back_populates="question", uselist=False, cascade="all, delete-orphan"
    )
    evidence_links: Mapped[list["EvidenceLink"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )
    actions: Mapped[list["Action"]] = relationship(back_populates="question")

    __table_args__ = (CheckConstraint(check_in("pillar", PILLAR), name="ck_questions_pillar"),)


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    question_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("questions.id"), unique=True, nullable=False
    )
    draft_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    confirmed_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Computed only by the deterministic rule engine (app/services/rules.py).
    # Never set from AI output directly — see AGENTS.md §3.2.
    evidence_status: Mapped[str] = mapped_column(String(30), default="MISSING")
    status_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # SPEC-AMD-005 step 3: every detected condition (not just the winning
    # one under the frozen CONFLICTING > OUTDATED > PARTIAL > VERIFIED
    # precedence) is preserved here as a JSON-encoded list of finding dicts.
    # AGENTS.md §3.2 lists `status_findings` alongside `evidence_status` as a
    # field the rule engine computes and AI output may never set directly.
    status_findings_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_status: Mapped[str] = mapped_column(String(30), default="UNREVIEWED")
    reviewer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # RULING-02 "NOT_APPLICABLE" step: human-controlled only, requires a
    # reason and a reviewer identity (reviewer_name/reviewed_at above serve
    # as the reviewer identity). The rule engine (app/services/rules.py)
    # never sets or clears evidence_status == "NOT_APPLICABLE" or this
    # reason field — only a human-facing endpoint may.
    not_applicable_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # SPEC-AMD-006 / RULING-03: draft provenance dimension, independent of
    # evidence_status. Invariant enforced by ck_answers_provenance_ai_run
    # below: AI_GENERATED/AI_ASSISTED_EDIT -> ai_run_id IS NOT NULL
    # (one-directional; does NOT require the converse).
    draft_provenance: Mapped[str] = mapped_column(String(30), default="NONE")
    ai_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    question: Mapped[Question] = relationship(back_populates="answer")

    __table_args__ = (
        CheckConstraint(
            check_in("evidence_status", EVIDENCE_STATUS), name="ck_answers_evidence_status"
        ),
        CheckConstraint(check_in("review_status", REVIEW_STATUS), name="ck_answers_review_status"),
        CheckConstraint(
            check_in("draft_provenance", DRAFT_PROVENANCE), name="ck_answers_draft_provenance"
        ),
        CheckConstraint(
            "draft_provenance NOT IN ('AI_GENERATED', 'AI_ASSISTED_EDIT') "
            "OR ai_run_id IS NOT NULL",
            name="ck_answers_provenance_ai_run",
        ),
    )


class EvidenceLink(Base):
    __tablename__ = "evidence_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    question_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("questions.id"), nullable=False
    )
    answer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("answers.id"), nullable=True
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id"), nullable=False
    )
    chunk_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("document_chunks.id"), nullable=False
    )
    location_json: Mapped[str] = mapped_column(Text)
    quoted_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    claim_supported: Mapped[str | None] = mapped_column(Text, nullable=True)
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    scope_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(60), nullable=True)
    # Added for SPEC-AMD-005: the reported numeric/text value this evidence
    # carries (mirrors ai_pipeline.CandidateEvidence.value), needed to detect
    # CONFLICTING (two records, same scope/period, different values) and to
    # check VERIFIED condition 5 (a numerical value has an explainable unit).
    value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Added for SPEC-AMD-005 step 2: whether extraction of THIS specific
    # evidence candidate was valid/readable. Independent of the parent
    # Document's processing_status — a document can be INDEXED overall while
    # one extracted candidate is OCR-garbled. Extraction-invalid evidence is
    # excluded entirely from the evidence-quality computation but must never
    # itself manufacture or suppress a conflict (AMENDMENTS.md SPEC-AMD-005,
    # "two rules that constrain step 2").
    extraction_valid: Mapped[bool] = mapped_column(default=True)
    link_status: Mapped[str] = mapped_column(String(30), default="CANDIDATE")
    created_by: Mapped[str] = mapped_column(String(20), default="SYSTEM")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    question: Mapped[Question] = relationship(back_populates="evidence_links")

    __table_args__ = (
        CheckConstraint(
            check_in("link_status", EVIDENCE_LINK_STATUS), name="ck_evidence_links_status"
        ),
        CheckConstraint(
            check_in("created_by", EVIDENCE_CREATED_BY), name="ck_evidence_links_created_by"
        ),
    )


class Action(Base):
    __tablename__ = "actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    question_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("questions.id"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(500))
    owner_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner_role: Mapped[str | None] = mapped_column(String(120), nullable=True)
    next_step: Mapped[str | None] = mapped_column(Text, nullable=True)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="TODO")
    completion_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    closure_evidence_document_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("documents.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    case: Mapped[Case] = relationship(back_populates="actions")
    question: Mapped[Question | None] = relationship(back_populates="actions")

    __table_args__ = (
        CheckConstraint(check_in("type", ACTION_TYPE), name="ck_actions_type"),
        CheckConstraint(check_in("status", ACTION_STATUS), name="ck_actions_status"),
    )
