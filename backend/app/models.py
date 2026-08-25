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
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, UtcDateTime
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
    JOB_STATUS,
    JOB_TYPE,
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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=_utcnow)

    cases: Mapped[list["Case"]] = relationship(back_populates="organization")


class User(Base):
    """A person who signs in. Not a customer contact and not a Case subject.

    `email` is stored lowercased by the registration path rather than by a
    database-level collation, so the uniqueness constraint means what a person
    would expect it to mean on every dialect. SQLite has no CITEXT and the test
    suite runs on SQLite, so a citext column would be enforced in production and
    silently absent in the tests - the class of divergence `UtcDateTime` exists
    to prevent.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime, default=_utcnow, onupdate=_utcnow
    )

    memberships: Mapped[list["OrganizationMember"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    sessions: Mapped[list["SessionRow"]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True
    )
    email_tokens: Mapped[list["EmailToken"]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True
    )


class OrganizationMember(Base):
    """Which people act for which organization, and with what authority."""

    __tablename__ = "organization_members"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=_utcnow)

    user: Mapped["User"] = relationship(back_populates="memberships")
    organization: Mapped["Organization"] = relationship()

    __table_args__ = (
        CheckConstraint(
            "role IN ('ADMIN', 'MEMBER')", name="ck_organization_members_role"
        ),
    )


class SessionRow(Base):
    """One signed-in session.

    Named `SessionRow` because `sqlalchemy.orm.Session` is imported in nearly
    every module here and a second `Session` would be read as that one.

    `organization_id` is on the session, not derived per request: a user who
    belongs to two organizations acts as one of them at a time, and putting the
    active one here means no endpoint has to infer which tenant a request speaks
    for.
    """

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=_utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)

    organization: Mapped["Organization"] = relationship()


class EmailToken(Base):
    """A single-use link sent to an address that already has an account."""

    __tablename__ = "email_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    purpose: Mapped[str] = mapped_column(String(20), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=_utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    used_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "purpose IN ('VERIFY', 'RESET')", name="ck_email_tokens_purpose"
        ),
    )


class Invitation(Base):
    """An offer of membership, addressed to an email rather than to a user.

    Separate from `EmailToken` for exactly one reason: the recipient may have no
    `users` row yet, so there is no `user_id` to hang the token on. Folding the
    two together would mean a nullable `user_id` whose NULL means something
    entirely different from an absent value elsewhere.
    """

    __tablename__ = "invitations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    invited_by_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=_utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)

    organization: Mapped["Organization"] = relationship()
    invited_by: Mapped["User"] = relationship(foreign_keys=[invited_by_user_id])

    __table_args__ = (
        CheckConstraint("role IN ('ADMIN', 'MEMBER')", name="ck_invitations_role"),
    )


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=True
    )
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(500))
    deadline_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    reporting_period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    reporting_period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT")
    # Retirement. ARCHIVED is an ordinary `status` value, already in
    # CASE_STATUS, so nothing downstream needs a new concept. These two columns
    # exist only so the transition is dated and reversible: without
    # status_before_archive, archiving a READY or EXPORTED Case would silently
    # destroy the fact that it got that far. Same reasoning that produced the
    # REOPEN review action (see enums.py REVIEW_ACTION) — a status a human can
    # set and never clear is a trap.
    #
    # archived_at rather than reading updated_at: updated_at is overwritten by
    # the next write, including the unarchive.
    archived_at: Mapped[datetime | None] = mapped_column(
        UtcDateTime, nullable=True
    )
    status_before_archive: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime, default=_utcnow, onupdate=_utcnow
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
    # processing_jobs.case_id is NOT NULL with no ON DELETE rule, so deleting a
    # Case without this cascade leaves rows pointing at an id that is gone.
    # Postgres refuses the DELETE outright (ForeignKeyViolation); SQLite, which
    # does not enforce foreign keys unless asked, silently orphans them. Every
    # Case that ever uploaded a document has at least one job row, so this is
    # the common path through DELETE /cases/{id}, not an edge case.
    processing_jobs: Mapped[list["ProcessingJob"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(check_in("status", CASE_STATUS), name="ck_cases_status"),
        CheckConstraint(
            f"status_before_archive IS NULL OR {check_in('status_before_archive', CASE_STATUS)}",
            name="ck_cases_status_before_archive",
        ),
    )


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
    # SPEC-AMD-001: lets a refreshed client reach the Job resource without
    # any other lookup. Nullable FK, set by the server after it creates the
    # processing_jobs row (never by the job/worker itself before it exists).
    latest_job_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("processing_jobs.id", use_alter=True, name="fk_documents_latest_job_id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=_utcnow)

    case: Mapped[Case] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    latest_job: Mapped["ProcessingJob | None"] = relationship(
        foreign_keys=[latest_job_id], post_update=True
    )
    # Ordering only, deliberately without a cascade. Without this relationship
    # the ORM cannot see that processing_jobs depends on documents, and emits
    # `DELETE FROM documents` while job rows still reference them. A job is
    # owned by its Case, not by a document, so deleting a document on its own
    # clears the reference rather than destroying the job's record.
    processing_jobs: Mapped[list["ProcessingJob"]] = relationship(
        foreign_keys="ProcessingJob.document_id", back_populates="document"
    )
    evidence_links: Mapped[list["EvidenceLink"]] = relationship(
        back_populates="document", cascade="all, delete"
    )
    questionnaires: Mapped[list["Questionnaire"]] = relationship(
        back_populates="document", cascade="all, delete"
    )
    closing_actions: Mapped[list["Action"]] = relationship(
        foreign_keys="Action.closure_evidence_document_id",
        back_populates="closure_evidence_document",
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
    # What a model read out of this fragment. On the chunk, not on the link:
    # a measurement belongs to the text that reports it, and links are
    # re-created whenever another document is indexed. Nullable because most
    # chunks are prose - a null means "no measurement", which is what the rule
    # engine has always assumed.
    extracted_value: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extracted_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    extracted_scope: Mapped[str | None] = mapped_column(String(255), nullable=True)
    extracted_period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    extracted_period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    # embedding intentionally omitted: pgvector is out of scope for this slice
    # (no evidence-matching pipeline is implemented here).

    document: Mapped[Document] = relationship(back_populates="chunks")
    # Ordering + ownership, same reason as Document.evidence_links.
    evidence_links: Mapped[list["EvidenceLink"]] = relationship(
        back_populates="chunk", cascade="all, delete"
    )


class ProcessingJob(Base):
    """SPEC-AMD-001 — the Job resource the Shared Integration Contract
    already declared `GET /api/v1/jobs/{job_id}` for, but never defined.

    Backs a simple polling worker using ``SELECT ... FOR UPDATE SKIP
    LOCKED`` (decision-register.md §4 item 017; RULING-01) rather than
    Celery/Kafka/Redis, which the Main Spec explicitly excludes from the
    MVP. See app/services/jobs.py for the claim/lease logic and its
    documented SQLite-dev-only limitation (SQLite has no `FOR UPDATE SKIP
    LOCKED`).
    """

    __tablename__ = "processing_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    case: Mapped[Case] = relationship(back_populates="processing_jobs")
    job_type: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), default="QUEUED")
    document_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("documents.id"), nullable=True
    )
    question_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("questions.id"), nullable=True
    )
    question: Mapped["Question | None"] = relationship(back_populates="processing_jobs")
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    lease_expires_at: Mapped[datetime | None] = mapped_column(
        UtcDateTime, nullable=True
    )
    error_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=_utcnow)
    started_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)

    document: Mapped["Document | None"] = relationship(
        foreign_keys=[document_id], back_populates="processing_jobs"
    )

    __table_args__ = (
        CheckConstraint(check_in("job_type", JOB_TYPE), name="ck_processing_jobs_job_type"),
        CheckConstraint(check_in("status", JOB_STATUS), name="ck_processing_jobs_status"),
    )


class Questionnaire(Base):
    __tablename__ = "questionnaires"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(500))
    version: Mapped[str | None] = mapped_column(String(60), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=_utcnow)

    case: Mapped[Case] = relationship(back_populates="questionnaires")
    # NOT NULL, so a Questionnaire cannot outlive the Document it was parsed
    # from. Ordering, same reason as the other document back-references.
    document: Mapped[Document] = relationship(back_populates="questionnaires")
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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime, default=_utcnow, onupdate=_utcnow
    )

    questionnaire: Mapped[Questionnaire] = relationship(back_populates="questions")
    answer: Mapped["Answer | None"] = relationship(
        back_populates="question", uselist=False, cascade="all, delete-orphan"
    )
    # Ordering only, same reason as Document.processing_jobs above.
    processing_jobs: Mapped[list["ProcessingJob"]] = relationship(back_populates="question")
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
    reviewed_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    # RULING-02 "NOT_APPLICABLE" step: human-controlled only, requires a
    # reason and a reviewer identity (reviewer_name/reviewed_at above serve
    # as the reviewer identity). The rule engine (app/services/rules.py)
    # never sets or clears evidence_status == "NOT_APPLICABLE" or this
    # reason field — only a human-facing endpoint may.
    not_applicable_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Phase 5 (Main Spec §17): human-supplied reason for a REJECT review
    # action. Distinct from not_applicable_reason above (that one is only
    # ever set by the NOT_APPLICABLE review action, never REJECT).
    review_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # SPEC-AMD-006 / RULING-03: draft provenance dimension, independent of
    # evidence_status. Invariant enforced by ck_answers_provenance_ai_run
    # below: AI_GENERATED/AI_ASSISTED_EDIT -> ai_run_id IS NOT NULL
    # (one-directional; does NOT require the converse).
    draft_provenance: Mapped[str] = mapped_column(String(30), default="NONE")
    ai_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime, default=_utcnow, onupdate=_utcnow
    )

    question: Mapped[Question] = relationship(back_populates="answer")
    # Ordering. Nullable, so deleting an Answer alone just clears the back
    # reference; the edge exists so the ORM does not emit `DELETE FROM answers`
    # while links still cite them.
    evidence_links: Mapped[list["EvidenceLink"]] = relationship(back_populates="answer")

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
    # Both are NOT NULL, so an EvidenceLink cannot outlive the document or
    # chunk it cites. These relationships exist so the ORM knows that and
    # orders the deletes; without them it emits `DELETE FROM documents` while
    # links still point at the row. `delete-orphan` stays on
    # Question.evidence_links alone — a link is owned by its Question, and
    # giving one object two delete-orphan parents is what SQLAlchemy warns
    # about.
    # How strongly the matcher scored this link (sum of matched-keyword
    # weights). Ranking aid for presentation only — the rule engine must never
    # read it, or the model would be influencing a verdict (AGENTS.md §3.2).
    # Nullable: rows written before migration 0006 have no score.
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Who accepted this link, and when. VERIFIED is the strongest claim this
    # system makes about a piece of evidence; one that cannot name its author
    # is the kind of unprovable claim the product exists to refuse. Nullable
    # because most links are never accepted, and because rows written before
    # migration 0007 have no record of it.
    accepted_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    chunk: Mapped["DocumentChunk"] = relationship(back_populates="evidence_links")
    answer: Mapped["Answer | None"] = relationship(back_populates="evidence_links")
    closing_actions: Mapped[list["Action"]] = relationship(
        foreign_keys="Action.closure_evidence_link_id",
        back_populates="closure_evidence_link",
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
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=_utcnow)

    question: Mapped[Question] = relationship(back_populates="evidence_links")
    # ORM mapping only -- no schema change. Without it a caller holding an
    # EvidenceLink can reach the document's id but not its name, so a citation
    # could only ever say "Paragraph 8" without saying paragraph 8 *of what*.
    document: Mapped[Document] = relationship(
        foreign_keys=[document_id], back_populates="evidence_links"
    )

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
    deadline_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="TODO")
    completion_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Phase 5: an Action addressing MISSING/CONFLICTING evidence must supply
    # closure evidence before it can be marked COMPLETED (Gate P5). Set at
    # creation time (auto-derived from the question's evidence_status, or
    # explicit override) — never flipped true/false implicitly afterward.
    requires_closure_evidence: Mapped[bool] = mapped_column(default=False)
    # The evidence_links row an Action's closure depended on. Distinct from
    # closure_evidence_document_id below (kept for backward compatibility,
    # unused by new code): this is what app/routers/evidence.py's invalidate
    # endpoint checks to decide whether to reopen a COMPLETED Action.
    closure_evidence_link_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("evidence_links.id"), nullable=True
    )
    closure_evidence_document_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("documents.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime, default=_utcnow, onupdate=_utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)

    case: Mapped[Case] = relationship(back_populates="actions")
    question: Mapped[Question | None] = relationship(back_populates="actions")
    # Ordering, same reason as the other closure references: without these the
    # ORM cannot know an Action outlives neither the document nor the link its
    # closure cites, and deletes those first.
    closure_evidence_document: Mapped[Document | None] = relationship(
        foreign_keys=[closure_evidence_document_id], back_populates="closing_actions"
    )
    closure_evidence_link: Mapped["EvidenceLink | None"] = relationship(
        foreign_keys=[closure_evidence_link_id], back_populates="closing_actions"
    )

    __table_args__ = (
        CheckConstraint(check_in("type", ACTION_TYPE), name="ck_actions_type"),
        CheckConstraint(check_in("status", ACTION_STATUS), name="ck_actions_status"),
    )
