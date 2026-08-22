"""Document upload endpoint — Contract §6 "Documents and Jobs".

Only POST /cases/{case_id}/documents is implemented in this slice. Retry,
delete, list, and the Job resource (SPEC-AMD-001) are out of scope.

Scope boundary: this endpoint identifies questions synchronously and
in-process when document_type=QUESTIONNAIRE, using the real AI pipeline
parser (app/services/questionnaire_parser.py, wrapping
packages/ai-pipeline's `parse_document()`). There is no job queue and no
processing_jobs row (SPEC-AMD-001 is out of scope for this slice).

Any other document_type is treated, for this slice, as an evidence source:
its text is chunked (one `document_chunks` row per non-blank line — the
simplest chunking that still exercises the real analyze/evidence-resolution
path) and then `ai_pipeline.analyze_question()` is run for every question
already on the Case against those chunks. The AI pipeline returns a
`chunk_id`-only candidate (never a location, never a status — AGENTS.md
§3.2/3.3); THIS module is the only place that resolves that `chunk_id` back
to a persisted `document_chunks` row and its location, and the only place
that decides `evidence_status` (via app/services/rules.py). A real
production pipeline would chunk far more richly (page/sheet/heading-aware,
PDF/DOCX-aware) — that is out of scope here; this is deliberately the
minimum chunking that keeps the MISSING -> PARTIAL wiring honest.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from ai_pipeline import AnalysisQuestion, DocumentChunk as PipelineDocumentChunk, analyze_question

from app.config import settings
from app.db import get_db
from app.errors import api_error, case_not_found
from app.enums import DOCUMENT_TYPE
from app.models import Case, Document, DocumentChunk, EvidenceLink, Question, Questionnaire
from app.schemas import DocumentRecord
from app.services import storage
from app.services.questionnaire_parser import QuestionnaireParseError, parse_questionnaire
from app.services.rules import compute_evidence_status

router = APIRouter(prefix="/api/v1/cases", tags=["documents"])


@router.post("/{case_id}/documents", response_model=DocumentRecord, status_code=201)
async def upload_document(
    case_id: str,
    file: UploadFile = File(...),
    document_type: str = Form("OTHER"),
    db: Session = Depends(get_db),
) -> DocumentRecord:
    case = db.get(Case, case_id)
    if case is None:
        raise case_not_found(case_id)

    if document_type not in DOCUMENT_TYPE:
        raise api_error(
            422,
            "VALIDATION_ERROR",
            f"Unknown document_type '{document_type}'.",
            allowed=list(DOCUMENT_TYPE),
        )

    data = await file.read()
    if len(data) > settings.max_upload_bytes:
        raise api_error(
            413,
            "FILE_TOO_LARGE",
            "Uploaded file exceeds the configured size limit.",
            max_bytes=settings.max_upload_bytes,
        )

    sha256 = storage.sha256_of(data)

    existing = (
        db.query(Document)
        .filter(Document.case_id == case_id, Document.sha256 == sha256)
        .one_or_none()
    )
    if existing is not None:
        # Contract §2.2 / §11: duplicate file checksum within one Case
        # returns the existing Document rather than creating a duplicate.
        return DocumentRecord.from_model(existing)

    storage_key = storage.storage_key_for(case_id, sha256, file.filename or "upload")
    storage.save(storage_key, data)

    document = Document(
        case_id=case_id,
        original_filename=file.filename or "upload",
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(data),
        sha256=sha256,
        storage_key=storage_key,
        document_type=document_type,
        processing_status="UPLOADED",
    )
    db.add(document)
    db.flush()  # assign document.id before referencing it below

    if document_type == "QUESTIONNAIRE":
        _identify_questions(db, case, document, data)
    else:
        _index_and_analyze_evidence(db, case, document, data)

    db.commit()
    db.refresh(document)
    return DocumentRecord.from_model(document)


def _identify_questions(db: Session, case: Case, document: Document, data: bytes) -> None:
    """Parse the questionnaire and persist Questionnaire + Questions.

    On parse failure, the document is marked FAILED/NEEDS_MANUAL_REVIEW per
    Contract §3.3 document processing statuses, and the error is recorded —
    it does not raise past the upload response, since the file itself was
    still received and stored successfully.
    """
    try:
        parsed_questions = parse_questionnaire(data, document.original_filename)
    except QuestionnaireParseError as exc:
        document.processing_status = "NEEDS_MANUAL_REVIEW"
        document.error_code = "DOCUMENT_PARSE_FAILED"
        document.error_message = str(exc)
        return

    questionnaire = Questionnaire(
        case_id=case.id,
        document_id=document.id,
        name=document.original_filename,
        version="1",
    )
    db.add(questionnaire)
    db.flush()

    for pq in parsed_questions:
        question = Question(
            questionnaire_id=questionnaire.id,
            external_question_id=pq.external_question_id,
            source_location=json.dumps(pq.source_location),
            section=pq.section,
            question_text=pq.question_text,
            is_required=pq.is_required,
            pillar=pq.pillar,
            question_order=pq.question_order,
        )
        db.add(question)
        db.flush()
        _create_default_answer(db, question)

    document.processing_status = "INDEXED"


def _create_default_answer(db: Session, question: Question) -> None:
    from app.models import Answer

    answer = Answer(
        question_id=question.id,
        evidence_status=compute_evidence_status(evidence_link_count=0),
        review_status="UNREVIEWED",
        draft_provenance="NONE",
    )
    db.add(answer)


def _chunk_evidence_text(data: bytes) -> list[str]:
    """Simplest honest chunking for this slice: one chunk per non-blank line.

    Real page/sheet/heading-aware chunking (PDF, DOCX, XLSX evidence) is out
    of scope here — this only needs to exercise the real
    resolve-a-chunk-id-to-a-location path end to end.
    """
    text = data.decode("utf-8", errors="replace")
    return [line.strip() for line in text.splitlines() if line.strip()]


def _index_and_analyze_evidence(db: Session, case: Case, document: Document, data: bytes) -> None:
    """Chunk an evidence document and analyze every question on the Case
    against it.

    This is the server-owned wiring the AI pipeline is never trusted with:
    `analyze_question()` returns only a `chunk_id` (AGENTS.md §3.3), and this
    function is the only place that resolves that id back to a persisted
    `document_chunks` row (and therefore a real location) before creating an
    `evidence_links` row. `evidence_status` is then computed here by the
    deterministic rule engine (app/services/rules.py) from the resulting
    evidence_links count — never copied from anything the pipeline returned.
    """
    chunk_texts = _chunk_evidence_text(data)
    if not chunk_texts:
        document.processing_status = "NEEDS_MANUAL_REVIEW"
        document.error_code = "DOCUMENT_PARSE_FAILED"
        document.error_message = "No chunkable text content found in the uploaded document."
        return

    chunk_rows: list[DocumentChunk] = []
    for seq, text in enumerate(chunk_texts):
        chunk = DocumentChunk(
            document_id=document.id,
            sequence_no=seq,
            text=text,
            heading_path=json.dumps([]),
        )
        db.add(chunk)
        chunk_rows.append(chunk)
    db.flush()  # assign chunk.id for each row before referencing it below

    document.processing_status = "INDEXED"

    pipeline_chunks = [PipelineDocumentChunk(chunk_id=c.id, text=c.text) for c in chunk_rows]
    chunk_by_id = {c.id: c for c in chunk_rows}

    questions = (
        db.query(Question)
        .join(Questionnaire, Question.questionnaire_id == Questionnaire.id)
        .filter(Questionnaire.case_id == case.id)
        .all()
    )

    for question in questions:
        _analyze_question_against_evidence(db, question, document, pipeline_chunks, chunk_by_id)


def _analyze_question_against_evidence(
    db: Session,
    question: Question,
    document: Document,
    pipeline_chunks: list[PipelineDocumentChunk],
    chunk_by_id: dict[str, DocumentChunk],
) -> None:
    result = analyze_question(
        AnalysisQuestion(question_id=question.id, question_text=question.question_text),
        pipeline_chunks,
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

    location = {
        "type": "paragraph",
        "heading_path": [],
        "paragraph_index": chunk_row.sequence_no,
    }

    evidence_link = EvidenceLink(
        question_id=question.id,
        answer_id=question.answer.id if question.answer else None,
        document_id=document.id,
        chunk_id=chunk_row.id,
        location_json=json.dumps(location),
        quoted_excerpt=candidate.quoted_excerpt,
        claim_supported=candidate.claim_supported,
        link_status="CANDIDATE",
        created_by="SYSTEM",
    )
    db.add(evidence_link)
    db.flush()

    link_count = db.query(EvidenceLink).filter(EvidenceLink.question_id == question.id).count()
    new_status = compute_evidence_status(evidence_link_count=link_count)

    answer = question.answer
    if answer is not None:
        answer.evidence_status = new_status
        answer.status_reason = (
            "Candidate evidence located by automated keyword match against "
            f"'{document.original_filename}'; coverage is not yet verified by "
            "a human reviewer."
        )
