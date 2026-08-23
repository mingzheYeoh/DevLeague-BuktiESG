"""Document upload/retry endpoints — Contract §6 "Documents and Jobs".

Upload creates a `processing_jobs` row (SPEC-AMD-001) and runs it
immediately, in-process (see app/services/jobs.py module docstring for why
that execution model was chosen for this phase). Retry re-attempts
processing for a Document stuck in FAILED/NEEDS_MANUAL_REVIEW by creating a
new `processing_jobs` row and running it the same way.

Scope boundary: `document_type=QUESTIONNAIRE` runs a DOCUMENT_PARSE job
(identifies questions, using the real AI pipeline parser,
app/services/questionnaire_parser.py, wrapping packages/ai-pipeline's
`parse_document()`). Any other `document_type` runs a DOCUMENT_INDEX job:
its content is chunked by the appropriate evidence parser (PDF/DOCX/XLSX/
plain-text, dispatched by mime_type/filename — app/services/jobs.py) and
then `ai_pipeline.analyze_question()` is run for every question already on
the Case against those chunks. The AI pipeline returns a `chunk_id`-only
candidate (never a location, never a status — AGENTS.md §3.2/3.3); the
server is the only thing that resolves that `chunk_id` back to a persisted
`document_chunks` row and its location, and the only thing that decides
`evidence_status` (via app/services/rules.py).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.errors import api_error, case_not_found
from app.enums import DOCUMENT_TYPE
from app.models import Case, Document
from app.schemas import DocumentRecord
from app.services import jobs, storage

router = APIRouter(prefix="/api/v1/cases", tags=["documents"])

_RETRYABLE_STATUSES = {"FAILED", "NEEDS_MANUAL_REVIEW"}


def _job_type_for(document_type: str) -> str:
    return "DOCUMENT_PARSE" if document_type == "QUESTIONNAIRE" else "DOCUMENT_INDEX"


def _document_not_found(document_id: str):
    return api_error(404, "DOCUMENT_NOT_FOUND", f"Document '{document_id}' was not found.")


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

    job = jobs.create_job(
        db,
        case_id=case_id,
        job_type=_job_type_for(document_type),
        document_id=document.id,
    )
    jobs.run_document_job(db, job)

    db.commit()
    db.refresh(document)
    return DocumentRecord.from_model(document)


@router.get("/{case_id}/documents", response_model=list[DocumentRecord])
def list_documents(case_id: str, db: Session = Depends(get_db)) -> list[DocumentRecord]:
    case = db.get(Case, case_id)
    if case is None:
        raise case_not_found(case_id)

    documents = (
        db.query(Document)
        .filter(Document.case_id == case_id)
        .order_by(Document.created_at)
        .all()
    )
    return [DocumentRecord.from_model(doc) for doc in documents]


@router.post(
    "/{case_id}/documents/{document_id}/retry",
    response_model=DocumentRecord,
    status_code=200,
)
def retry_document(
    case_id: str, document_id: str, db: Session = Depends(get_db)
) -> DocumentRecord:
    """Re-attempt processing for a Document currently stuck in FAILED or
    NEEDS_MANUAL_REVIEW. Creates a new `processing_jobs` row (a fresh
    attempt, not a mutation of the failed one — the failed job's row is
    left as an honest historical record) and runs it the same way the
    initial upload does.
    """
    case = db.get(Case, case_id)
    if case is None:
        raise case_not_found(case_id)

    document = db.get(Document, document_id)
    if document is None or document.case_id != case_id:
        raise _document_not_found(document_id)

    if document.processing_status not in _RETRYABLE_STATUSES:
        raise api_error(
            409,
            "DOCUMENT_NOT_RETRYABLE",
            f"Document '{document_id}' has processing_status "
            f"'{document.processing_status}', which is not retryable.",
            retryable_statuses=sorted(_RETRYABLE_STATUSES),
        )

    document.error_code = None
    document.error_message = None
    document.processing_status = "PARSING"

    job = jobs.create_job(
        db,
        case_id=case_id,
        job_type=_job_type_for(document.document_type),
        document_id=document.id,
    )
    jobs.run_document_job(db, job)

    db.commit()
    db.refresh(document)
    return DocumentRecord.from_model(document)
