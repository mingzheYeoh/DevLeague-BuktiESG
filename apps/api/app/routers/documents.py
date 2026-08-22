"""Document upload endpoint — Contract §6 "Documents and Jobs".

Only POST /cases/{case_id}/documents is implemented in this slice. Retry,
delete, list, and the Job resource (SPEC-AMD-001) are out of scope.

Scope boundary: this endpoint identifies questions synchronously and
in-process when document_type=QUESTIONNAIRE, using the stub parser in
app/services/questionnaire_parser.py. There is no job queue, no
processing_jobs row, and no real document-processing pipeline (Docling,
OCR, chunking with embeddings) — that is the COO's AI pipeline, a later
slice. Non-questionnaire documents are stored and marked UPLOADED only.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.errors import api_error, case_not_found
from app.enums import DOCUMENT_TYPE
from app.models import Case, Document, Question, Questionnaire
from app.schemas import DocumentRecord
from app.services import storage
from app.services.questionnaire_parser import QuestionnaireParseError, parse_questionnaire

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
        # Out of scope for this slice: no processing pipeline for other
        # document types. Left at UPLOADED, which is a valid terminal state
        # for a document nothing has processed yet.
        pass

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

    import json

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
    from app.services.rules import compute_evidence_status

    answer = Answer(
        question_id=question.id,
        evidence_status=compute_evidence_status(evidence_link_count=0),
        review_status="UNREVIEWED",
        draft_provenance="NONE",
    )
    db.add(answer)
