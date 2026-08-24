"""processing_jobs lifecycle + document-processing dispatch — SPEC-AMD-001.

Main Spec §17 Phase 2 item 3: "Job table and worker." This project's Main
Spec explicitly excludes Celery/Kafka/Redis/Kubernetes/microservices for the
MVP; decision-register.md §4 item 017 (CTO authority) instead specifies a
plain database job table claimed with ``SELECT ... FOR UPDATE SKIP LOCKED``
and a lease.

**Chosen execution model for this phase**: the document-upload request path
creates a QUEUED `processing_jobs` row and then runs it immediately,
in-process, via `run_document_job()` (an in-process "worker" call, which
Main Spec §17 explicitly allows as acceptable for this phase — "a separate
worker process or an in-process background task"). This keeps the request
synchronous (the client still gets a final `processing_status` in the
upload response, matching the existing First Vertical Slice contract) while
giving every processing attempt a real, queryable job row — history,
`error_code`/`error_message`, and a retry path — instead of the ad-hoc
try/except that lived directly in the router before this change.

`backend/worker.py` additionally implements a real polling loop
(`claim_next_job()` below) so a QUEUED job can also be picked up out-of-band
(e.g. a crash mid-request, or a future async upload path) without any
schema change. See `claim_next_job()` for the Postgres `SKIP LOCKED` query
and its documented SQLite-dev-only fallback.

Purity boundary (unchanged): this module does all persistence and all
`document_type`/`mime_type`-based dispatch. The actual parsing is delegated
to `ai_pipeline`'s pure functions (`packages/ai-pipeline`) — no DB/HTTP
inside that package, ever (AGENTS.md §3.2/3.3, CTO-RULINGS BLOCKER-04).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from ai_pipeline import (
    AnalysisQuestion,
    DocumentChunk as PipelineDocumentChunk,
    ExtractedChunk,
    analyze_question,
    keyword_weights,
    parse_docx_evidence,
    parse_pdf_evidence,
    parse_plain_text_evidence,
    parse_xlsx_evidence,
    question_keywords,
)

from app.models import Case, Document, DocumentChunk, EvidenceLink, ProcessingJob, Question, Questionnaire
from app.services.questionnaire_parser import QuestionnaireParseError, parse_questionnaire
from app.services.rules import (
    EvidenceCandidate,
    EvidenceRequirement,
    UnreadableDocument,
    compute_evidence_status,
    normalize_tokens,
)

_XLSX_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
}
_DOCX_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}
_PDF_MIME_TYPES = {"application/pdf"}

# A claimed-but-not-finished job is considered abandoned (crashed worker,
# killed process) after this long, and becomes claimable again. Only
# meaningful for the out-of-band worker.py poll loop, since the in-process
# path above always resolves a job to a terminal state before its request
# returns.
_LEASE_DURATION = timedelta(minutes=10)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Job lifecycle
# --------------------------------------------------------------------------- #


def create_job(
    db: Session,
    *,
    case_id: str,
    job_type: str,
    document_id: str | None = None,
    question_id: str | None = None,
) -> ProcessingJob:
    """Create a QUEUED `processing_jobs` row and, if it's for a Document,
    point `documents.latest_job_id` at it so a refreshed client can reach
    the Job resource (SPEC-AMD-001)."""
    job = ProcessingJob(
        case_id=case_id,
        job_type=job_type,
        status="QUEUED",
        document_id=document_id,
        question_id=question_id,
        attempt_count=0,
    )
    db.add(job)
    db.flush()

    if document_id is not None:
        document = db.get(Document, document_id)
        if document is not None:
            document.latest_job_id = job.id

    return job


def claim_next_job(db: Session) -> ProcessingJob | None:
    """Claim the oldest QUEUED (or lease-expired RUNNING) job for
    out-of-band processing (backend/worker.py).

    On PostgreSQL this uses ``SELECT ... FOR UPDATE SKIP LOCKED`` so
    multiple worker processes can poll the same table concurrently without
    blocking each other or double-claiming a row.

    **SQLite limitation, stated explicitly rather than faked**: SQLite has
    no row-level locking and no `FOR UPDATE SKIP LOCKED` — this whole
    concept only exists for concurrent, multi-connection access. For local
    dev / the test suite (which run on SQLite — see tests/conftest.py) this
    degrades to a simple claim-by-conditional-UPDATE: select a candidate
    row, then `UPDATE ... WHERE id = :id AND status = :expected_status`,
    trusting the single-row-affected count rather than a DB-level lock.
    That is race-safe against a *second SQLite connection in the same
    process* only by accident of the GIL/serialized access, not by design —
    it is not safe against real concurrent workers. Do not run more than one
    worker process against a SQLite database.
    """
    dialect = db.bind.dialect.name if db.bind is not None else ""
    now = _utcnow()
    lease_cutoff = now - _LEASE_DURATION

    if dialect == "postgresql":
        row = db.execute(
            text(
                """
                UPDATE processing_jobs
                SET status = 'RUNNING', started_at = :now,
                    attempt_count = attempt_count + 1,
                    lease_expires_at = :lease_expires
                WHERE id = (
                    SELECT id FROM processing_jobs
                    WHERE status = 'QUEUED'
                       OR (status = 'RUNNING' AND lease_expires_at < :now)
                    ORDER BY created_at
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING id
                """
            ),
            {"now": now, "lease_expires": now + _LEASE_DURATION},
        ).first()
        if row is None:
            return None
        db.commit()
        return db.get(ProcessingJob, row[0])

    # SQLite (and any other non-Postgres dialect) fallback — see docstring.
    candidate = (
        db.query(ProcessingJob)
        .filter(
            (ProcessingJob.status == "QUEUED")
            | ((ProcessingJob.status == "RUNNING") & (ProcessingJob.lease_expires_at < now))
        )
        .order_by(ProcessingJob.created_at)
        .first()
    )
    if candidate is None:
        return None

    result = db.query(ProcessingJob).filter(
        ProcessingJob.id == candidate.id, ProcessingJob.status == candidate.status
    ).update(
        {
            "status": "RUNNING",
            "started_at": now,
            "attempt_count": ProcessingJob.attempt_count + 1,
            "lease_expires_at": now + _LEASE_DURATION,
        },
        synchronize_session=False,
    )
    db.commit()
    if result == 0:
        return None  # another connection claimed it first
    return db.get(ProcessingJob, candidate.id)


# --------------------------------------------------------------------------- #
# Document-processing dispatch (the actual "worker" logic)
# --------------------------------------------------------------------------- #


def run_document_job(db: Session, job: ProcessingJob) -> None:
    """Run one Document-processing job to a terminal state.

    Never raises past this function on a parser/content failure — those are
    caught, recorded as FAILED with `error_code`/`error_message` on both the
    job and the Document, and left for a human to retry
    (`POST /cases/{id}/documents/{doc_id}/retry`). An unexpected bug would
    still raise (deliberately — that is not a "bad input" case to swallow).
    """
    if job.status == "QUEUED":
        job.status = "RUNNING"
        job.started_at = _utcnow()
        job.attempt_count += 1

    document = job.document
    if document is None:
        _fail_job(job, "JOB_HAS_NO_DOCUMENT", "processing_jobs row has no linked document.")
        return

    case = db.get(Case, document.case_id)
    data = _load_document_bytes(document)

    try:
        if job.job_type == "DOCUMENT_PARSE":
            _run_questionnaire_parse(db, case, document, data)
        else:
            _run_evidence_index(db, case, document, data)
    except (QuestionnaireParseError, ValueError) as exc:
        document.processing_status = "NEEDS_MANUAL_REVIEW"
        document.error_code = "DOCUMENT_PARSE_FAILED"
        document.error_message = str(exc)
        _fail_job(job, "DOCUMENT_PARSE_FAILED", str(exc))
        # A document that could not be read is an input the rule engine reacts
        # to, not the end of the story. Returning here left every question on
        # whatever status it already had, so the C-15 rule -- an unreadable
        # document may materially affect a question -- could never fire, and a
        # reviewer was told MISSING about a file they had just uploaded.
        db.flush()
        _recompute_case_question_statuses(db, case)
        return

    job.status = "SUCCEEDED"
    job.finished_at = _utcnow()


def _fail_job(job: ProcessingJob, error_code: str, error_message: str) -> None:
    job.status = "FAILED"
    job.error_code = error_code
    job.error_message = error_message
    job.finished_at = _utcnow()


def _load_document_bytes(document: Document) -> bytes:
    from app.services import storage

    return storage.load(document.storage_key)


# --------------------------------------------------------------------------- #
# DOCUMENT_PARSE — questionnaire ingestion
# --------------------------------------------------------------------------- #


def _run_questionnaire_parse(db: Session, case: Case, document: Document, data: bytes) -> None:
    parse_result = parse_questionnaire(data, document.original_filename)

    questionnaire = Questionnaire(
        case_id=case.id,
        document_id=document.id,
        name=document.original_filename,
        version="1",
    )
    db.add(questionnaire)
    db.flush()

    for pq in parse_result.questions:
        question = Question(
            questionnaire_id=questionnaire.id,
            external_question_id=pq.external_question_id,
            source_location=json.dumps(pq.source_location),
            section=pq.section,
            question_text=pq.question_text,
            is_required=pq.is_required,
            pillar=pq.pillar,
            sedg_topic_code=pq.sedg_topic_code,
            sedg_disclosure_code=pq.sedg_disclosure_code,
            mapping_rationale=pq.mapping_rationale,
            question_order=pq.question_order,
            evidence_requirement_json=_build_requirement_json(pq.question_text),
        )
        db.add(question)
        db.flush()
        _create_default_answer(db, question)

    document.processing_status = "INDEXED"
    document.error_code = None
    document.error_message = None

    # Column-mapping confirmation UI (Main Spec §17 Phase 3): a transient,
    # non-persisted Python attribute for THIS request/response cycle only --
    # not a mapped column, never flushed to the DB. The router reads it off
    # this same `document` instance before the response is built. See
    # app/services/questionnaire_parser.py's ParsedQuestionnaireResult
    # docstring for why this stays display-only rather than a new migration.
    document._detected_columns = parse_result.column_mapping  # type: ignore[attr-defined]



def _build_requirement_json(question_text: str) -> str:
    """What this question requires of its evidence, as the rule engine reads it.

    Only `keywords` is filled, and the omissions are deliberate:

    * `required_period_start`/`_end` would look natural to inherit from the
      Case's reporting period, and would be a regression. The VERIFIED
      period-coverage check demands `link.period_start <= required_start and
      link.period_end >= required_end`, and no link carries a period, because
      nothing extracts one from a chunk. Every VERIFIED would fall back to
      PARTIAL. OUTDATED would go with it: the `source_date` fallback in
      `_is_outdated` only applies when the question states no period.
    * `required_scope` fails the same way against a NULL `scope_description`.
    * `accepted_document_types` is not inferable from question text without
      guessing, and a wrong guess silently narrows the C-15 gate below.

    The keywords are the question's own distinctive words, matched by exact
    token equality only (C-15 — no fuzzy matching, no embeddings, no model).
    They gate one rule: whether an unreadable document may materially affect
    this question, which is the difference between "no evidence" and "evidence
    we could not read".
    """
    return json.dumps({"keywords": question_keywords(question_text)})

def _create_default_answer(db: Session, question: Question) -> None:
    from app.models import Answer

    result = compute_evidence_status(candidates=[])
    answer = Answer(
        question_id=question.id,
        evidence_status=result.status,
        status_reason=result.status_reason,
        status_findings_json=json.dumps(result.status_findings),
        review_status="UNREVIEWED",
        draft_provenance="NONE",
    )
    db.add(answer)


# --------------------------------------------------------------------------- #
# DOCUMENT_INDEX — evidence chunking + analysis
# --------------------------------------------------------------------------- #


def _select_evidence_parser(document: Document):
    """Dispatch by mime_type, falling back to filename extension — the
    server's decision, never the pipeline's (AGENTS.md §3.2/3.3)."""
    mime_type = (document.mime_type or "").lower()
    suffix = Path(document.original_filename or "").suffix.lower()

    if mime_type in _PDF_MIME_TYPES or suffix == ".pdf":
        return parse_pdf_evidence
    if mime_type in _DOCX_MIME_TYPES or suffix == ".docx":
        return parse_docx_evidence
    if mime_type in _XLSX_MIME_TYPES or suffix == ".xlsx":
        return parse_xlsx_evidence
    return parse_plain_text_evidence


def _run_evidence_index(db: Session, case: Case, document: Document, data: bytes) -> None:
    """Chunk an evidence document (PDF/DOCX/XLSX/plain-text, dispatched by
    document mime_type/filename) and analyze every question on the Case
    against it. Refactored out of app/routers/documents.py so both the
    initial-upload path and the retry endpoint share one implementation.
    """
    parser = _select_evidence_parser(document)
    extracted_chunks: list[ExtractedChunk] = parser(data)  # raises ValueError on failure

    chunk_rows: list[DocumentChunk] = []
    for extracted in extracted_chunks:
        chunk = DocumentChunk(
            document_id=document.id,
            sequence_no=extracted.sequence_no,
            text=extracted.text,
            page_number=extracted.page_number,
            sheet_name=extracted.sheet_name,
            cell_range=extracted.cell_range,
            heading_path=json.dumps(extracted.heading_path),
        )
        db.add(chunk)
        chunk_rows.append(chunk)
    db.flush()  # assign chunk.id for each row before referencing it below

    document.processing_status = "INDEXED"
    document.error_code = None
    document.error_message = None

    pipeline_chunks = [PipelineDocumentChunk(chunk_id=c.id, text=c.text) for c in chunk_rows]
    chunk_by_id = {c.id: c for c in chunk_rows}

    questions = (
        db.query(Question)
        .join(Questionnaire, Question.questionnaire_id == Questionnaire.id)
        .filter(Questionnaire.case_id == case.id)
        .all()
    )

    # Computed once for the whole questionnaire, not per question: the weights
    # answer "how distinctive is this word across the questions this customer
    # asked", which is a property of the set, not of any one question.
    weights = keyword_weights([q.question_text for q in questions])

    for question in questions:
        _analyze_question_against_evidence(
            db, question, document, pipeline_chunks, chunk_by_id, weights
        )



def _recompute_case_question_statuses(db: Session, case: Case) -> None:
    """Re-run the rule engine for every question in a Case, adding no evidence.

    Used when something changed that the engine reads but that produces no new
    links -- so far, a document failing to parse. The status text comes from
    `compute_evidence_status` unmodified: the "candidate evidence located by
    automated keyword match against X" preamble the indexing path adds would be
    a lie here, because nothing was matched and X could not be read.
    """
    questions = (
        db.query(Question)
        .join(Questionnaire, Question.questionnaire_id == Questionnaire.id)
        .filter(Questionnaire.case_id == case.id)
        .all()
    )
    unreadable_documents = _build_unreadable_documents(db, case.id)
    for question in questions:
        answer = question.answer
        if answer is None:
            continue
        result = compute_evidence_status(
            candidates=_load_evidence_candidates(db, question.id),
            requirement=_build_evidence_requirement(question),
            unreadable_documents=unreadable_documents,
            current_status=answer.evidence_status,
            not_applicable_reason=answer.not_applicable_reason,
            reviewer_name=answer.reviewer_name,
        )
        answer.evidence_status = result.status
        answer.status_findings_json = json.dumps(result.status_findings)
        if result.status != "NOT_APPLICABLE":
            answer.status_reason = result.status_reason

def _analyze_question_against_evidence(
    db: Session,
    question: Question,
    document: Document,
    pipeline_chunks: list[PipelineDocumentChunk],
    chunk_by_id: dict[str, DocumentChunk],
    weights: dict[str, float] | None = None,
) -> None:
    result = analyze_question(
        AnalysisQuestion(question_id=question.id, question_text=question.question_text),
        pipeline_chunks,
        keyword_weights=weights,
    )
    # Hard boundary (AGENTS.md §3.2/3.3): `result` never carries a status or a
    # location. Only its `chunk_id` is trusted, and only if it resolves to a
    # chunk WE persisted for THIS document — a chunk_id an AI pipeline
    # invented cannot resolve, which is what makes a hallucinated citation
    # structurally impossible here rather than merely unlikely.
    if not result.candidate_evidence:
        return

    candidate = result.candidate_evidence[0]
    chunk_row = chunk_by_id.get(candidate.chunk_id)
    if chunk_row is None:
        return

    location = _location_for_chunk(chunk_row)

    evidence_link = EvidenceLink(
        question_id=question.id,
        answer_id=question.answer.id if question.answer else None,
        document_id=document.id,
        chunk_id=chunk_row.id,
        location_json=json.dumps(location),
        quoted_excerpt=candidate.quoted_excerpt,
        claim_supported=candidate.claim_supported,
        period_start=_parse_iso_date(candidate.period_start),
        period_end=_parse_iso_date(candidate.period_end),
        scope_description=candidate.scope_description,
        unit=candidate.unit,
        value=candidate.value,
        match_score=candidate.match_score,
        extraction_valid=True,
        link_status="CANDIDATE",
        created_by="SYSTEM",
    )
    db.add(evidence_link)
    db.flush()

    answer = question.answer
    if answer is None:
        return

    evidence_candidates = _load_evidence_candidates(db, question.id)
    requirement = _build_evidence_requirement(question)
    unreadable_documents = _build_unreadable_documents(db, question.questionnaire.case_id)

    result = compute_evidence_status(
        candidates=evidence_candidates,
        requirement=requirement,
        unreadable_documents=unreadable_documents,
        current_status=answer.evidence_status,
        not_applicable_reason=answer.not_applicable_reason,
        reviewer_name=answer.reviewer_name,
    )
    answer.evidence_status = result.status
    answer.status_findings_json = json.dumps(result.status_findings)
    if result.status == "NOT_APPLICABLE":
        return
    answer.status_reason = (
        "Candidate evidence located by automated keyword match against "
        f"'{document.original_filename}'; coverage is not yet verified by "
        "a human reviewer. " + result.status_reason
    )


def _location_for_chunk(chunk_row: DocumentChunk) -> dict:
    """Build a Contract §4 location object from a persisted document_chunks
    row — the server's job, never the pipeline's (AGENTS.md §3.3)."""
    if chunk_row.page_number is not None:
        return {"type": "page", "page_number": chunk_row.page_number, "bounding_box": None}
    if chunk_row.sheet_name is not None:
        return {
            "type": "sheet_cell",
            "sheet_name": chunk_row.sheet_name,
            "cell_range": chunk_row.cell_range,
        }
    heading_path: list[str] = []
    if chunk_row.heading_path:
        try:
            heading_path = json.loads(chunk_row.heading_path)
        except ValueError:
            heading_path = []
    return {
        "type": "paragraph",
        "heading_path": heading_path,
        "paragraph_index": chunk_row.sequence_no,
    }


def _parse_iso_date(value: str | None):
    """`ai_pipeline.CandidateEvidence.period_start`/`period_end` are plain
    ISO-8601 strings (the package returns no DB types — BLOCKER-04). Return
    `None` rather than raising on anything that doesn't parse; a malformed
    date from the pipeline is untrusted data, not a crash (AGENTS.md §3.4).
    """
    if not value:
        return None
    try:
        from datetime import date as _date

        return _date.fromisoformat(value)
    except ValueError:
        return None


def _load_evidence_candidates(db: Session, question_id: str) -> list[EvidenceCandidate]:
    rows = (
        db.query(EvidenceLink, Document)
        .join(Document, EvidenceLink.document_id == Document.id)
        .filter(EvidenceLink.question_id == question_id)
        .all()
    )
    candidates: list[EvidenceCandidate] = []
    for link, doc in rows:
        candidates.append(
            EvidenceCandidate(
                link_id=link.id,
                link_status=link.link_status,
                extraction_valid=link.extraction_valid,
                claim_supported=link.claim_supported,
                quoted_excerpt=link.quoted_excerpt,
                period_start=link.period_start,
                period_end=link.period_end,
                scope_description=link.scope_description,
                unit=link.unit,
                value=link.value,
                source_date=doc.source_date,
                source_location=link.location_json,
            )
        )
    return candidates


def _build_evidence_requirement(question: Question) -> EvidenceRequirement:
    if not question.evidence_requirement_json:
        return EvidenceRequirement()
    try:
        data = json.loads(question.evidence_requirement_json)
    except ValueError:
        return EvidenceRequirement()
    return EvidenceRequirement(
        required_period_start=_parse_iso_date(data.get("required_period_start")),
        required_period_end=_parse_iso_date(data.get("required_period_end")),
        required_scope=data.get("required_scope"),
        accepted_document_types=tuple(data.get("accepted_document_types") or ()),
        keywords=tuple(data.get("keywords") or ()),
    )


def _build_unreadable_documents(db: Session, case_id: str) -> list[UnreadableDocument]:
    docs = (
        db.query(Document)
        .filter(Document.case_id == case_id, Document.processing_status == "NEEDS_MANUAL_REVIEW")
        .all()
    )
    return [
        UnreadableDocument(
            document_id=doc.id,
            document_type=doc.document_type,
            processing_status=doc.processing_status,
            original_filename=doc.original_filename,
            extracted_tokens=tuple(normalize_tokens(doc.original_filename)),
        )
        for doc in docs
    ]
