"""Archiving a Case, and the gate on deleting one.

`ARCHIVED` had been a legal `cases.status` value since migration 0001 with no
way to reach it: the Cases router exposed no PATCH and no DELETE, so every Case
was created DRAFT and stayed DRAFT permanently. There was no way to get a
finished or abandoned Case out of the list short of editing the database.

The rule these tests pin down: archiving is always available and destroys
nothing; deleting is refused unless the Case is DRAFT (nothing to lose yet) or
ARCHIVED (already deliberately retired). Anything in between has to be archived
first, so removing a reviewed Case is never one click.
"""

from __future__ import annotations

import io

import pytest
from openpyxl import Workbook

from app.models import (
    Action,
    Answer,
    Case,
    Document,
    ProcessingJob,
    Question,
    Questionnaire,
)
from app.services import storage

# Every status a Case can hold that is neither DRAFT nor ARCHIVED.
WORKED_ON = ("PROCESSING", "IN_REVIEW", "READY", "EXPORTED")


def _questionnaire_bytes() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Questionnaire"
    ws.append(["external_question_id", "question_text", "section", "is_required"])
    ws.append(["Q-E-01", "Report total annual electricity consumption in kWh.", "Environment", True])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _case(client, title: str = "Retirement") -> str:
    return client.post("/api/v1/cases", json={"title": title}).json()["id"]


def _set_status(db_session, case_id: str, status: str) -> None:
    """Put a Case into a status no endpoint can currently produce.

    Nothing in the app advances a Case past DRAFT yet, so the only way to test
    the deletion gate against a worked-on Case is to write the column. The
    CHECK constraint still applies, so a typo here fails rather than passing
    silently.
    """
    case = db_session.get(Case, case_id)
    case.status = status
    db_session.commit()


def _upload_questionnaire(client, case_id: str) -> dict:
    return client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={
            "file": (
                "q.xlsx",
                _questionnaire_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        data={"document_type": "QUESTIONNAIRE"},
    ).json()


# ---- Archiving ---------------------------------------------------------------


def test_a_draft_case_can_be_deleted(client):
    case_id = _case(client)

    resp = client.delete(f"/api/v1/cases/{case_id}")

    assert resp.status_code == 204
    assert client.get(f"/api/v1/cases/{case_id}").status_code == 404
    assert case_id not in {c["id"] for c in client.get("/api/v1/cases").json()}


def test_deleting_a_case_takes_its_questions_answers_documents_and_actions(
    client, db_session
):
    """There is no ON DELETE CASCADE in the schema — the cascade is declared on
    the ORM relationships, which is why the endpoint deletes through the session
    instead of issuing a bulk DELETE. A bulk delete would leave every child row
    behind, pointing at a Case that no longer exists.
    """
    case_id = _case(client)
    _upload_questionnaire(client, case_id)
    question_id = client.get(f"/api/v1/cases/{case_id}/questions").json()[0]["id"]

    client.post(
        f"/api/v1/cases/{case_id}/questions/{question_id}/review",
        json={"action": "EDIT", "edited_answer": "1,200 kWh."},
    )
    client.post(
        f"/api/v1/cases/{case_id}/actions",
        json={
            "question_id": question_id,
            "title": "Get the FY2025 bills",
            "owner_name": "Aina",
            "next_step": "Ask finance",
            "deadline_at": "2026-12-31T00:00:00Z",
        },
    )

    # Everything is really there before the delete, or the assertions after it
    # would pass for the wrong reason.
    assert db_session.query(Questionnaire).count() == 1
    assert db_session.query(Question).count() == 1
    assert db_session.query(Answer).count() == 1
    assert db_session.query(Document).count() == 1
    assert db_session.query(Action).count() == 1
    # Uploading anything queues a parse job. processing_jobs.case_id is NOT
    # NULL, so these rows are the reason the delete needs a cascade rather than
    # a bulk DELETE — Postgres refuses to remove a Case while they point at it.
    assert db_session.query(ProcessingJob).count() >= 1

    assert client.delete(f"/api/v1/cases/{case_id}").status_code == 204

    assert db_session.query(Case).count() == 0
    assert db_session.query(Questionnaire).count() == 0
    assert db_session.query(Question).count() == 0
    assert db_session.query(Answer).count() == 0
    assert db_session.query(Document).count() == 0
    assert db_session.query(Action).count() == 0
    assert db_session.query(ProcessingJob).count() == 0


def test_deleting_a_case_takes_its_stored_files(client):
    """Nothing in the database owns the uploaded bytes, so the row cascade alone
    would leave them on disk forever."""
    case_id = _case(client)
    _upload_questionnaire(client, case_id)
    case_dir = storage.STORAGE_ROOT / case_id
    assert case_dir.is_dir()

    client.delete(f"/api/v1/cases/{case_id}")

    assert not case_dir.exists()


def test_deleting_a_case_that_never_uploaded_anything_is_not_an_error(client):
    """No upload means no storage directory. Removing nothing is fine."""
    case_id = _case(client)
    assert not (storage.STORAGE_ROOT / case_id).exists()

    assert client.delete(f"/api/v1/cases/{case_id}").status_code == 204


def test_a_case_id_that_escapes_the_storage_root_is_refused():
    """`case_id` comes off the URL and is handed to shutil.rmtree, so it gets the
    same escape check as the read path."""
    with pytest.raises(storage.StorageKeyOutsideRoot):
        storage.delete_case_tree("../../etc")


def test_a_case_that_has_been_worked_on_can_be_deleted(client, db_session):
    """The demo line ends at EXPORTED, and that case has to be deletable.

    Deletion used to be refused for anything past DRAFT, with the error saying
    "archive it first". Archiving is gone, so that gate would have made every
    case that completed the flow permanently undeletable - the exact opposite
    of what removing a feature was supposed to achieve.

    Replaces `test_a_case_that_has_been_worked_on_cannot_be_deleted_directly`,
    which asserted the gate this removes.
    """
    case_id = _case(client, "Worked on")
    _set_status(db_session, case_id, "EXPORTED")

    assert client.delete(f"/api/v1/cases/{case_id}").status_code == 204
    assert client.get(f"/api/v1/cases/{case_id}").status_code == 404
