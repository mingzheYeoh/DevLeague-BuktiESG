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

import logging
from datetime import date
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import require_case
from app.config import settings
from app.db import get_db
from app.errors import api_error
from app.enums import DOCUMENT_DELETABLE_FROM, DOCUMENT_TYPE
from app.models import Case, Document, DocumentChunk
from app.schemas import DocumentChunkRecord, DocumentRecord
from app.services import jobs, storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cases", tags=["documents"])

# Types that may be rendered inline by a browser, keyed by file extension.
#
# Deliberately an allow-list keyed on the extension rather than on the stored
# `mime_type`, because that column holds whatever the uploading client claimed.
# Anything not listed here is served as an opaque download.
#
# `.svg` and `.html` are absent on purpose: both execute script when rendered
# inline, and uploaded document content is untrusted (trust boundary TB-3). An
# uploaded `.html` served inline would be stored XSS. Authentication raised the
# stakes here rather than lowering them: a payload now runs inside a signed-in
# session and can act as that user against their own organization's data.
#
# `.csv` maps to text/plain, not text/csv, so a browser shows it rather than
# handing it to a spreadsheet application.
_INLINE_CONTENT_TYPES: dict[str, str] = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".txt": "text/plain; charset=utf-8",
    ".csv": "text/plain; charset=utf-8",
}

# Nothing served here should ever execute or fetch anything. Verified in a real
# browser: `sandbox` does not stop Chrome rendering a PDF or an image inline.
#
# It does stop Playwright's bundled headless Chromium, which ships without the
# PDF viewer and falls back to downloading — a limitation of that browser build,
# not of this policy. Do not relax this because a headless test downloaded
# instead of rendering.
_CSP_SERVED_FILE = "default-src 'none'; sandbox"

_RETRYABLE_STATUSES = {"FAILED", "NEEDS_MANUAL_REVIEW"}


def _job_type_for(document_type: str) -> str:
    return "DOCUMENT_PARSE" if document_type == "QUESTIONNAIRE" else "DOCUMENT_INDEX"


def _document_not_found(document_id: str):
    return api_error(404, "DOCUMENT_NOT_FOUND", f"Document '{document_id}' was not found.")



def _parse_source_date(raw: str | None) -> date | None:
    """The date the evidence speaks as of - a policy's approval date, a
    report's period end.

    The rule engine needs it: `_is_outdated` compares it against the
    question's required period, or against the 24-month threshold when the
    question states none (DEC-007). Without it every document looks current.

    Optional, because a reviewer uploading a batch will not always know it and
    a required field would be answered with a guess. An unparseable one is
    refused rather than dropped: a silently ignored date reads to the uploader
    as an accepted one, and the document would then be treated as current
    forever.
    """
    if raw is None or not raw.strip():
        return None
    try:
        return date.fromisoformat(raw.strip())
    except ValueError:
        raise api_error(
            422,
            "VALIDATION_ERROR",
            f"source_date '{raw}' is not a valid ISO 8601 date.",
            expected_format="YYYY-MM-DD",
        ) from None

@router.post("/{case_id}/documents", response_model=DocumentRecord, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form("OTHER"),
    source_date: str | None = Form(None),
    case: Case = Depends(require_case),
    db: Session = Depends(get_db),
) -> DocumentRecord:
    case_id = case.id

    if document_type not in DOCUMENT_TYPE:
        raise api_error(
            422,
            "VALIDATION_ERROR",
            f"Unknown document_type '{document_type}'.",
            allowed=list(DOCUMENT_TYPE),
        )

    parsed_source_date = _parse_source_date(source_date)

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
        source_date=parsed_source_date,
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
def list_documents(
    case: Case = Depends(require_case), db: Session = Depends(get_db)
) -> list[DocumentRecord]:
    documents = (
        db.query(Document)
        .filter(Document.case_id == case.id)
        .order_by(Document.created_at)
        .all()
    )
    return [DocumentRecord.from_model(doc) for doc in documents]


def _load_document(db: Session, case: Case, document_id: str) -> Document:
    """A Document belonging to this Case, or 404.

    Takes the resolved `Case` rather than a `case_id: str`. The case check that
    used to open this function has moved into `require_case`, which the caller
    already went through - so this function can no longer be handed an
    identifier nobody authenticated. What remains here is the second half of the
    same boundary: the document must belong to *this* case, so that knowing a
    document id is not enough to read it through a case that happens to be
    yours.
    """
    document = db.get(Document, document_id)
    if document is None or document.case_id != case.id:
        raise _document_not_found(document_id)
    return document


@router.get(
    "/{case_id}/documents/{document_id}/chunks",
    response_model=list[DocumentChunkRecord],
)
def list_document_chunks(
    document_id: str,
    case: Case = Depends(require_case),
    db: Session = Depends(get_db),
) -> list[DocumentChunkRecord]:
    """The document as the server parsed it, in order.

    This is the format-independent view: PDFs, DOCX, spreadsheets and plain
    text all end up here as ordered fragments, each carrying whatever location
    its format supports. It is also exactly the text the evidence matcher ran
    against, which makes it the honest thing to show someone verifying a
    citation — a rendered original can differ from what extraction produced,
    and the citation rests on the extraction.

    Empty for a document that failed to parse; the document's `error` field
    says why.
    """
    _load_document(db, case, document_id)

    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.sequence_no)
        .all()
    )
    return [DocumentChunkRecord.from_model(c) for c in chunks]


@router.get("/{case_id}/documents/{document_id}/content")
def get_document_content(
    document_id: str,
    download: bool = False,
    case: Case = Depends(require_case),
    db: Session = Depends(get_db),
) -> FileResponse:
    """The stored file itself, for preview or download.

    `?download=1` forces `Content-Disposition: attachment`. The frontend runs
    on a different origin from this API, and a browser ignores the `download`
    attribute on a cross-origin `<a>` — so a plain link to an inline-allowed
    type (PDF, image, text) navigates the tab to the file and discards the
    single-page app's state instead of saving anything. The disposition is the
    only part of that a link can control, so the server has to offer it.

    Security posture, because this endpoint hands back user-uploaded bytes:

    * Every caller is authenticated, and `_load_document` resolves the
      document through the actor's organization, so this endpoint hands back
      bytes only to a signed-in member of the owning organization. A document
      belonging to another organization answers 404, never 403.
    * The content type is chosen from an extension allow-list, never from the
      client-supplied `mime_type`. Anything unlisted is `application/octet-stream`
      as an attachment, so an uploaded `.html` or `.svg` cannot execute script
      on this origin.
    * `X-Content-Type-Options: nosniff` stops a browser second-guessing that.
    * `Content-Security-Policy: default-src 'none'; sandbox` neuters anything
      that does get rendered. Confirmed in a real browser that this still allows
      inline PDF and image display.
    * The filename goes out RFC 5987-encoded, so a filename containing quotes
      or newlines cannot inject a header.

    What actually keeps this safe is the allow-list, not the CSP: no `.html` or
    `.svg` is ever served inline, and the three inline families that remain
    cannot script this origin. Images are inert; `text/plain` plus `nosniff` is
    never parsed as markup; and PDF script runs inside the viewer's own sandbox,
    with no access to the embedding origin.
    """
    document = _load_document(db, case, document_id)

    try:
        path = storage.resolve(document.storage_key)
    except storage.StorageKeyOutsideRoot:
        # Not a 404: a key that escapes the storage root means stored data is
        # wrong, and quietly returning "not found" would hide that.
        raise api_error(
            500,
            "STORAGE_KEY_INVALID",
            "The stored path for this document is not inside the storage root.",
        ) from None

    if not path.is_file():
        raise api_error(
            404,
            "DOCUMENT_CONTENT_MISSING",
            f"Document '{document_id}' has a database row but no stored file.",
            storage_key=document.storage_key,
        )

    suffix = Path(document.original_filename).suffix.lower()
    inline_type = _INLINE_CONTENT_TYPES.get(suffix)
    # `download` can only ever make this stricter: it turns an inline type into
    # an attachment, and never turns an attachment into an inline render. A
    # query parameter must not be able to widen what the allow-list permits.
    if download:
        content_type = "application/octet-stream"
        disposition = "attachment"
    else:
        content_type = inline_type or "application/octet-stream"
        disposition = "inline" if inline_type else "attachment"

    encoded_name = quote(document.original_filename, safe="")
    return FileResponse(
        path,
        media_type=content_type,
        headers={
            "Content-Disposition": f"{disposition}; filename*=UTF-8''{encoded_name}",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": _CSP_SERVED_FILE,
            # Uploaded content is synthetic test data, but it is still nobody
            # else's business to cache it.
            "Cache-Control": "private, no-store",
        },
    )



@router.delete("/{case_id}/documents/{document_id}", status_code=204)
def delete_document(
    document_id: str,
    case: Case = Depends(require_case),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a Document the parser could not read, and its stored bytes.

    Refused unless the Document is in `DOCUMENT_DELETABLE_FROM`. That gate is
    the whole safety argument: a document that parsed has chunks, and those
    chunks carry evidence links a reviewer may have accepted. A document that
    failed to parse has neither.

    `latest_job_id` is cleared before the job rows go. `documents.latest_job_id`
    and `processing_jobs.document_id` reference each other, so there is no
    order in which both can be deleted while both constraints hold - the
    pointer has to be broken first. PostgreSQL enforces this; SQLite with its
    default PRAGMA does not, which is exactly how such a bug reaches
    production unnoticed.

    Row first and committed, then the blob, for the same reason as
    `delete_case`: bytes nobody references are a janitor's problem, a row
    citing a file that is gone is a correctness one.
    """
    document = _load_document(db, case, document_id)

    if document.processing_status not in DOCUMENT_DELETABLE_FROM:
        raise api_error(
            409,
            "DOCUMENT_NOT_DELETABLE",
            f"A document in '{document.processing_status}' cannot be deleted. "
            "Only a document the parser could not read may be removed, because "
            "it carries no evidence anyone has cited.",
            document_id=document_id,
            processing_status=document.processing_status,
            deletable_from=list(DOCUMENT_DELETABLE_FROM),
        )

    storage_key = document.storage_key
    case = document.case

    document.latest_job_id = None
    db.flush()
    db.delete(document)
    db.flush()

    # The unreadable document was an input to the C-15 rule, so a question it
    # was holding in NEEDS_MANUAL_REVIEW has to be told it is gone. Without
    # this the question keeps a status justified by a file that no longer
    # exists, and names it in the reason.
    jobs._recompute_case_question_statuses(db, case)
    db.commit()

    try:
        storage.delete_file(storage_key)
    except OSError:
        logger.exception("Deleted document %s but could not remove its stored file", document_id)

    return Response(status_code=204)

@router.post(
    "/{case_id}/documents/{document_id}/retry",
    response_model=DocumentRecord,
    status_code=200,
)
def retry_document(
    document_id: str,
    case: Case = Depends(require_case),
    db: Session = Depends(get_db),
) -> DocumentRecord:
    """Re-attempt processing for a Document currently stuck in FAILED or
    NEEDS_MANUAL_REVIEW. Creates a new `processing_jobs` row (a fresh
    attempt, not a mutation of the failed one — the failed job's row is
    left as an honest historical record) and runs it the same way the
    initial upload does.
    """
    document = _load_document(db, case, document_id)

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
        case_id=case.id,
        job_type=_job_type_for(document.document_type),
        document_id=document.id,
    )
    jobs.run_document_job(db, job)

    db.commit()
    db.refresh(document)
    return DocumentRecord.from_model(document)
