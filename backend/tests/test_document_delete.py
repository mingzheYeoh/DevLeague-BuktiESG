"""Deleting a document the parser could not read.

`NEEDS_MANUAL_REVIEW` had no exit. `/retry` re-runs the same parser over the
same bytes, so a scan with no extractable text stays in that state for the life
of the Case - and since the C-15 rule started firing, such a file also holds a
question in `NEEDS_MANUAL_REVIEW` indefinitely. A reviewer who has looked at
the file and confirmed it is unusable needs a way to say so.

Only documents that failed to parse may be deleted. Such a document has no
chunks and no evidence links, so removing it destroys no citation and no review
decision - which is the whole reason the gate is this narrow.
"""

from __future__ import annotations

import io

from openpyxl import Workbook

BROKEN_PDF = b"%PDF-1.4\nnot really a pdf\n"


def _case(client, title: str = "Delete document") -> str:
    return client.post("/api/v1/cases", json={"title": title}).json()["id"]


def _upload(client, case_id: str, name: str, data: bytes, doc_type: str) -> dict:
    resp = client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": (name, data, "application/octet-stream")},
        data={"document_type": doc_type},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _questionnaire(*texts: str) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(["external_question_id", "question_text", "section", "is_required"])
    for i, text in enumerate(texts, start=1):
        ws.append([f"Q-{i}", text, "Social", True])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_an_unreadable_document_can_be_deleted(client, db_session):
    from app.models import Document, ProcessingJob
    from app.services import storage

    case_id = _case(client)
    doc = _upload(client, case_id, "scan.pdf", BROKEN_PDF, "SAFETY_RECORD")
    assert doc["processing_status"] == "NEEDS_MANUAL_REVIEW"
    assert storage.exists(
        db_session.get(Document, doc["id"]).storage_key
    ), "the upload should have stored the bytes"
    storage_key = db_session.get(Document, doc["id"]).storage_key

    resp = client.delete(f"/api/v1/cases/{case_id}/documents/{doc['id']}")
    assert resp.status_code == 204, resp.text

    assert db_session.get(Document, doc["id"]) is None
    assert (
        db_session.query(ProcessingJob).filter(ProcessingJob.document_id == doc["id"]).count() == 0
    ), "the job rows must go with the document, not outlive it"
    assert not storage.exists(storage_key), "the stored bytes must go too"

    listed = client.get(f"/api/v1/cases/{case_id}/documents").json()
    assert (listed["items"] if isinstance(listed, dict) else listed) == []


def test_a_document_that_parsed_cannot_be_deleted(client, db_session):
    """The gate, and the reason for it: this document has chunks, and chunks
    carry citations. A refused delete must also change nothing."""
    from app.models import Document, DocumentChunk

    case_id = _case(client)
    doc = _upload(client, case_id, "waste.txt", b"Scheduled waste disposed: 12.6 tonnes.\n", "WASTE_RECORD")
    assert doc["processing_status"] == "INDEXED"
    chunks_before = db_session.query(DocumentChunk).filter(
        DocumentChunk.document_id == doc["id"]
    ).count()
    assert chunks_before > 0

    resp = client.delete(f"/api/v1/cases/{case_id}/documents/{doc['id']}")

    assert resp.status_code == 409, resp.text
    error = resp.json()["detail"]["error"]
    assert error["code"] == "DOCUMENT_NOT_DELETABLE"
    assert error["details"]["processing_status"] == "INDEXED"
    assert error["details"]["deletable_from"] == ["NEEDS_MANUAL_REVIEW"]

    db_session.expire_all()
    assert db_session.get(Document, doc["id"]) is not None
    assert db_session.query(DocumentChunk).filter(
        DocumentChunk.document_id == doc["id"]
    ).count() == chunks_before


def test_a_document_from_another_case_is_not_found(client):
    """The document id is not a capability. Addressing one through the wrong
    Case must not reveal that it exists, let alone delete it."""
    from app.models import Document

    owner = _case(client, "Owner")
    other = _case(client, "Other")
    doc = _upload(client, owner, "scan.pdf", BROKEN_PDF, "SAFETY_RECORD")

    resp = client.delete(f"/api/v1/cases/{other}/documents/{doc['id']}")

    assert resp.status_code == 404, resp.text
    assert client.get(f"/api/v1/cases/{owner}/documents").json()[0]["id"] == doc["id"]


def test_deleting_it_releases_the_question_it_was_holding(client):
    """The part that is easy to miss.

    Since the C-15 rule started firing, an unreadable document holds any
    question whose keywords match its filename in NEEDS_MANUAL_REVIEW. Delete
    the file without recomputing and the question keeps a status justified by
    a document that no longer exists - and names it in the reason.
    """
    case_id = _case(client, "Release")
    client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": ("q.xlsx", _questionnaire(
            "Report the number of work-related injuries recorded during the year.",
        ), "application/octet-stream")},
        data={"document_type": "QUESTIONNAIRE"},
    )
    doc = _upload(client, case_id, "injuries-register-2025.pdf", BROKEN_PDF, "SAFETY_RECORD")

    def question():
        payload = client.get(f"/api/v1/cases/{case_id}/questions").json()
        return (payload["items"] if isinstance(payload, dict) else payload)[0]

    held = question()
    assert held["evidence_status"] == "NEEDS_MANUAL_REVIEW"
    assert "injuries-register-2025.pdf" in held["status_reason"]

    assert client.delete(f"/api/v1/cases/{case_id}/documents/{doc['id']}").status_code == 204

    released = question()
    assert released["evidence_status"] == "MISSING"
    assert "injuries-register-2025.pdf" not in (released["status_reason"] or "")


def test_a_storage_failure_does_not_turn_a_successful_delete_into_a_500(
    client, monkeypatch
):
    """The row is committed before the file is unlinked, deliberately.

    So a storage error must be logged and swallowed: the delete really did
    happen, and reporting 500 for work that was done is worse than a stranded
    file. This module used `logger.exception` in that handler while never
    importing `logging` or defining `logger`, so the handler itself raised
    NameError and produced exactly the 500 the design says it avoids.

    Nothing caught it because no test ever made `delete_file` fail - the happy
    path never enters the `except`.
    """
    from app.services import storage

    case_id = _case(client, "Storage failure")
    doc = _upload(client, case_id, "scan.pdf", BROKEN_PDF, "SAFETY_RECORD")

    def _explode(_key):
        raise OSError("the file is gone")

    monkeypatch.setattr(storage, "delete_file", _explode)

    response = client.delete(f"/api/v1/cases/{case_id}/documents/{doc['id']}")

    assert response.status_code == 204, response.text

    # And the row is really gone - the point is that the delete stands.
    listed = client.get(f"/api/v1/cases/{case_id}/documents").json()
    assert all(d["id"] != doc["id"] for d in listed)
