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

from app.enums import CASE_DELETABLE_FROM
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

REVIEWER = "Nur Aina"

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


def test_archiving_a_draft_case_records_where_it_came_from_and_when(client):
    case_id = _case(client)

    resp = client.post(f"/api/v1/cases/{case_id}/archive")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ARCHIVED"
    assert body["status_before_archive"] == "DRAFT"
    assert body["archived_at"] is not None


@pytest.mark.parametrize("status", WORKED_ON)
def test_archive_remembers_the_exact_status_and_unarchive_restores_it(
    client, db_session, status
):
    """The point of `status_before_archive`.

    Archiving a READY Case and restoring it as DRAFT would silently destroy the
    fact that it ever got to READY — the same one-way-door problem that
    produced the REOPEN review action.
    """
    case_id = _case(client)
    _set_status(db_session, case_id, status)

    archived = client.post(f"/api/v1/cases/{case_id}/archive").json()
    assert archived["status"] == "ARCHIVED"
    assert archived["status_before_archive"] == status

    restored = client.post(f"/api/v1/cases/{case_id}/unarchive")

    assert restored.status_code == 200
    body = restored.json()
    assert body["status"] == status
    # Both columns are cleared, so a second archive records the new status
    # rather than a stale one.
    assert body["status_before_archive"] is None
    assert body["archived_at"] is None


def test_archiving_an_already_archived_case_is_refused(client):
    """Silently succeeding would overwrite `status_before_archive` with
    ARCHIVED, and the restore target would be lost."""
    case_id = _case(client)
    client.post(f"/api/v1/cases/{case_id}/archive")

    resp = client.post(f"/api/v1/cases/{case_id}/archive")

    assert resp.status_code == 409
    assert resp.json()["detail"]["error"]["code"] == "CASE_ALREADY_ARCHIVED"


def test_unarchiving_a_case_that_is_not_archived_is_refused(client):
    case_id = _case(client)

    resp = client.post(f"/api/v1/cases/{case_id}/unarchive")

    assert resp.status_code == 409
    error = resp.json()["detail"]["error"]
    assert error["code"] == "CASE_NOT_ARCHIVED"
    assert error["details"]["status"] == "DRAFT"


def test_archiving_destroys_nothing(client):
    """Archive is the safe option, so everything under the Case survives it and
    stays readable."""
    case_id = _case(client)
    _upload_questionnaire(client, case_id)
    questions_before = client.get(f"/api/v1/cases/{case_id}/questions").json()
    assert questions_before

    client.post(f"/api/v1/cases/{case_id}/archive")

    assert client.get(f"/api/v1/cases/{case_id}").status_code == 200
    assert client.get(f"/api/v1/cases/{case_id}/questions").json() == questions_before
    assert client.get(f"/api/v1/cases/{case_id}/documents").json()


def test_archived_cases_are_still_listed(client):
    """The list endpoint stays complete. Hiding archived Cases by default is a
    presentation choice, and the client makes it — an API that drops rows leaves
    no way to find them again."""
    kept = _case(client, "Kept")
    archived = _case(client, "Archived")
    client.post(f"/api/v1/cases/{archived}/archive")

    listed = {c["id"]: c["status"] for c in client.get("/api/v1/cases").json()}

    assert listed[kept] == "DRAFT"
    assert listed[archived] == "ARCHIVED"


# ---- Deleting ----------------------------------------------------------------


def test_a_draft_case_can_be_deleted(client):
    case_id = _case(client)

    resp = client.delete(f"/api/v1/cases/{case_id}")

    assert resp.status_code == 204
    assert client.get(f"/api/v1/cases/{case_id}").status_code == 404
    assert case_id not in {c["id"] for c in client.get("/api/v1/cases").json()}


def test_an_archived_case_can_be_deleted(client, db_session):
    """Archiving is the way through the gate: a Case that could not be deleted
    directly can be deleted once retired."""
    case_id = _case(client)
    _set_status(db_session, case_id, "READY")
    assert client.delete(f"/api/v1/cases/{case_id}").status_code == 409

    client.post(f"/api/v1/cases/{case_id}/archive")

    assert client.delete(f"/api/v1/cases/{case_id}").status_code == 204


@pytest.mark.parametrize("status", WORKED_ON)
def test_a_case_that_has_been_worked_on_cannot_be_deleted_directly(
    client, db_session, status
):
    case_id = _case(client)
    _set_status(db_session, case_id, status)

    resp = client.delete(f"/api/v1/cases/{case_id}")

    assert resp.status_code == 409
    error = resp.json()["detail"]["error"]
    assert error["code"] == "CASE_NOT_DELETABLE"
    assert error["details"]["status"] == status
    assert error["details"]["deletable_from"] == list(CASE_DELETABLE_FROM)
    # The refusal has to say what to do instead, not just "no".
    assert "archive" in error["message"].lower()
    # And the Case is untouched.
    assert client.get(f"/api/v1/cases/{case_id}").status_code == 200


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
        json={"action": "EDIT", "reviewer_name": REVIEWER, "edited_answer": "1,200 kWh."},
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


def test_retirement_endpoints_404_on_an_unknown_case(client):
    missing = "00000000-0000-0000-0000-000000000000"

    assert client.post(f"/api/v1/cases/{missing}/archive").status_code == 404
    assert client.post(f"/api/v1/cases/{missing}/unarchive").status_code == 404
    assert client.delete(f"/api/v1/cases/{missing}").status_code == 404


def test_a_case_id_that_escapes_the_storage_root_is_refused():
    """`case_id` comes off the URL and is handed to shutil.rmtree, so it gets the
    same escape check as the read path."""
    with pytest.raises(storage.StorageKeyOutsideRoot):
        storage.delete_case_tree("../../etc")
