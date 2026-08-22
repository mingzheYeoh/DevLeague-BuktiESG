"""Phase 5 — Human Review and Action Tracking (Main Spec §17 Phase 5).

Covers:
  - Accept/Edit/Reject/NotApplicable review transitions
  - Action requires owner/next_step/deadline at creation
  - An Action cannot be marked COMPLETED without a completion_note, and,
    when flagged requires_closure_evidence, without valid closure evidence
  - Evidence invalidation reopens a COMPLETED Action that depended on it
  - An unconfirmed AI draft never counts toward readiness (minimal
    readiness formula: confirmed_required_questions / total_required_questions)
"""

from __future__ import annotations

import io

from openpyxl import Workbook


def _build_questionnaire_xlsx(rows: list[dict]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Questionnaire"
    ws.append(["external_question_id", "question_text", "section", "is_required"])
    for row in rows:
        ws.append(
            [
                row.get("external_question_id", ""),
                row["question_text"],
                row.get("section", ""),
                row.get("is_required", True),
            ]
        )
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _make_case_with_question(client, question_text="Report annual electricity consumption."):
    resp = client.post("/api/v1/cases", json={"title": "Phase 5 Case"})
    case_id = resp.json()["id"]
    xlsx_bytes = _build_questionnaire_xlsx([{"question_text": question_text, "is_required": True}])
    resp = client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={
            "file": (
                "q.xlsx",
                xlsx_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        data={"document_type": "QUESTIONNAIRE"},
    )
    assert resp.status_code == 201, resp.text
    resp = client.get(f"/api/v1/cases/{case_id}/questions")
    question_id = resp.json()[0]["id"]
    return case_id, question_id


# --------------------------------------------------------------------------- #
# Review transitions
# --------------------------------------------------------------------------- #


def test_review_accept_sets_human_confirmed(client):
    case_id, question_id = _make_case_with_question(client)

    resp = client.post(
        f"/api/v1/cases/{case_id}/questions/{question_id}/review",
        json={"action": "ACCEPT", "reviewer_name": "Alice"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["review_status"] == "HUMAN_CONFIRMED"
    assert body["reviewer_name"] == "Alice"
    assert body["reviewed_at"]


def test_review_edit_persists_edited_answer_and_confirms(client):
    case_id, question_id = _make_case_with_question(client)

    resp = client.post(
        f"/api/v1/cases/{case_id}/questions/{question_id}/review",
        json={
            "action": "EDIT",
            "reviewer_name": "Bob",
            "edited_answer": "Our FY2025 electricity consumption was 12,840 kWh.",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["confirmed_answer"] == "Our FY2025 electricity consumption was 12,840 kWh."
    assert body["review_status"] == "HUMAN_CONFIRMED"


def test_review_edit_without_edited_answer_is_rejected(client):
    case_id, question_id = _make_case_with_question(client)

    resp = client.post(
        f"/api/v1/cases/{case_id}/questions/{question_id}/review",
        json={"action": "EDIT", "reviewer_name": "Bob"},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"]["code"] == "VALIDATION_ERROR"


def test_review_reject_requires_reason(client):
    case_id, question_id = _make_case_with_question(client)

    resp = client.post(
        f"/api/v1/cases/{case_id}/questions/{question_id}/review",
        json={"action": "REJECT", "reviewer_name": "Carol"},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"]["code"] == "VALIDATION_ERROR"

    resp = client.post(
        f"/api/v1/cases/{case_id}/questions/{question_id}/review",
        json={"action": "REJECT", "reviewer_name": "Carol", "reason": "Not credible source."},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["review_status"] == "REJECTED"
    assert body["review_reason"] == "Not credible source."


def test_review_not_applicable_requires_reason_and_sets_evidence_status(client):
    case_id, question_id = _make_case_with_question(client)

    resp = client.post(
        f"/api/v1/cases/{case_id}/questions/{question_id}/review",
        json={"action": "NOT_APPLICABLE", "reviewer_name": "Dana"},
    )
    assert resp.status_code == 422

    resp = client.post(
        f"/api/v1/cases/{case_id}/questions/{question_id}/review",
        json={
            "action": "NOT_APPLICABLE",
            "reviewer_name": "Dana",
            "reason": "Business does not operate a fleet.",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["evidence_status"] == "NOT_APPLICABLE"
    assert body["not_applicable_reason"] == "Business does not operate a fleet."
    assert body["review_status"] == "HUMAN_CONFIRMED"

    # The rule engine must never clear/recompute NOT_APPLICABLE once a human
    # has set it (app/services/rules.py step 1) — verified indirectly via
    # GET questions still reporting NOT_APPLICABLE after a reload.
    resp = client.get(f"/api/v1/cases/{case_id}/questions")
    q = next(q for q in resp.json() if q["id"] == question_id)
    assert q["evidence_status"] == "NOT_APPLICABLE"


def test_review_requires_reviewer_name(client):
    case_id, question_id = _make_case_with_question(client)

    resp = client.post(
        f"/api/v1/cases/{case_id}/questions/{question_id}/review",
        json={"action": "ACCEPT"},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"]["code"] == "VALIDATION_ERROR"


def test_review_unknown_action_rejected(client):
    case_id, question_id = _make_case_with_question(client)

    resp = client.post(
        f"/api/v1/cases/{case_id}/questions/{question_id}/review",
        json={"action": "APPROVE_FOREVER", "reviewer_name": "Alice"},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"]["code"] == "VALIDATION_ERROR"


# --------------------------------------------------------------------------- #
# Action creation requires owner/next_step/deadline
# --------------------------------------------------------------------------- #


def test_action_creation_requires_owner_next_step_deadline(client):
    resp = client.post("/api/v1/cases", json={"title": "Case"})
    case_id = resp.json()["id"]

    resp = client.post(
        f"/api/v1/cases/{case_id}/actions",
        json={"type": "SUBMISSION", "title": "Collect utility bills"},
    )
    assert resp.status_code == 422
    body = resp.json()["detail"]["error"]
    assert body["code"] == "VALIDATION_ERROR"
    assert set(body["details"]["missing_fields"]) == {"owner_name", "next_step", "deadline_at"}

    resp = client.post(
        f"/api/v1/cases/{case_id}/actions",
        json={
            "type": "IMPROVEMENT",
            "title": "Collect utility bills",
            "owner_name": "Finance",
            "next_step": "Request Jan-Dec bills",
            "deadline_at": "2026-12-31T00:00:00Z",
        },
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["type"] == "IMPROVEMENT"


# --------------------------------------------------------------------------- #
# Action lifecycle: completion requires note, and closure evidence when
# required
# --------------------------------------------------------------------------- #


def _create_action(client, case_id, question_id=None, requires_closure_evidence=None):
    payload = {
        "type": "SUBMISSION",
        "title": "Fix missing evidence",
        "owner_name": "Finance",
        "next_step": "Get the bill",
        "deadline_at": "2026-12-31T00:00:00Z",
    }
    if question_id is not None:
        payload["question_id"] = question_id
    if requires_closure_evidence is not None:
        payload["requires_closure_evidence"] = requires_closure_evidence
    resp = client.post(f"/api/v1/cases/{case_id}/actions", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_action_auto_requires_closure_evidence_for_missing_question(client):
    case_id, question_id = _make_case_with_question(client)
    # Question has zero evidence -> MISSING -> requires_closure_evidence auto True.
    action = _create_action(client, case_id, question_id=question_id)
    assert action["requires_closure_evidence"] is True


def test_action_cannot_complete_without_completion_note(client):
    case_id, _ = _make_case_with_question(client)
    action = _create_action(client, case_id, requires_closure_evidence=False)

    resp = client.post(
        f"/api/v1/cases/{case_id}/actions/{action['id']}/status",
        json={"status": "COMPLETED"},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"]["code"] == "VALIDATION_ERROR"

    resp = client.post(
        f"/api/v1/cases/{case_id}/actions/{action['id']}/status",
        json={"status": "COMPLETED", "completion_note": "Done, bill collected."},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "COMPLETED"


def test_action_cannot_complete_without_required_closure_evidence(client, db_session):
    case_id, question_id = _make_case_with_question(client)
    action = _create_action(client, case_id, question_id=question_id)
    assert action["requires_closure_evidence"] is True

    # No closure evidence at all -> rejected even with a completion_note.
    resp = client.post(
        f"/api/v1/cases/{case_id}/actions/{action['id']}/status",
        json={"status": "COMPLETED", "completion_note": "Should not be allowed."},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"]["code"] == "VALIDATION_ERROR"

    # Upload evidence to create a real evidence_links row for this question.
    resp = client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={
            "file": (
                "utility-bill.txt",
                b"Total electricity consumption: 12,840 kWh at the Selangor site in January 2025.\n",
                "text/plain",
            )
        },
        data={"document_type": "UTILITY_BILL"},
    )
    assert resp.status_code == 201, resp.text

    resp = client.get(f"/api/v1/cases/{case_id}/questions")
    q = next(q for q in resp.json() if q["id"] == question_id)
    assert q["evidence_status"] in ("PARTIAL", "VERIFIED", "CONFLICTING")

    # The QuestionListItem response never exposes a raw evidence_links id
    # (by design — only server-resolved locations/excerpts are surfaced), so
    # pull the id straight from the shared db_session fixture the `client`
    # fixture is bound to.
    from app.models import EvidenceLink

    link = db_session.query(EvidenceLink).filter(EvidenceLink.question_id == question_id).first()
    assert link is not None
    link_id = link.id

    resp = client.post(
        f"/api/v1/cases/{case_id}/actions/{action['id']}/status",
        json={
            "status": "COMPLETED",
            "completion_note": "Bill collected and linked.",
            "closure_evidence_link_id": link_id,
        },
    )
    assert resp.status_code == 200, resp.text
    completed = resp.json()
    assert completed["status"] == "COMPLETED"
    assert completed["closure_evidence_link_id"] == link_id


def test_evidence_invalidation_reopens_action(client, db_session):
    case_id, question_id = _make_case_with_question(client)
    action = _create_action(client, case_id, question_id=question_id)

    resp = client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={
            "file": (
                "utility-bill.txt",
                b"Total electricity consumption: 12,840 kWh at the Selangor site in January 2025.\n",
                "text/plain",
            )
        },
        data={"document_type": "UTILITY_BILL"},
    )
    assert resp.status_code == 201, resp.text

    from app.models import EvidenceLink

    link = db_session.query(EvidenceLink).filter(EvidenceLink.question_id == question_id).first()
    assert link is not None
    link_id = link.id

    resp = client.post(
        f"/api/v1/cases/{case_id}/actions/{action['id']}/status",
        json={
            "status": "COMPLETED",
            "completion_note": "Bill collected and linked.",
            "closure_evidence_link_id": link_id,
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "COMPLETED"

    # Now invalidate that evidence link -> the Action must be reopened.
    resp = client.post(f"/api/v1/cases/{case_id}/evidence-links/{link_id}/invalidate")
    assert resp.status_code == 200, resp.text
    assert resp.json()["link_status"] == "INVALIDATED"

    resp = client.get(f"/api/v1/cases/{case_id}/actions")
    reopened = next(a for a in resp.json() if a["id"] == action["id"])
    assert reopened["status"] != "COMPLETED"
    assert reopened["completed_at"] is None


# --------------------------------------------------------------------------- #
# Readiness: unconfirmed AI draft never counts
# --------------------------------------------------------------------------- #


def test_readiness_excludes_unconfirmed_answers(client):
    case_id, question_id = _make_case_with_question(client)

    resp = client.get(f"/api/v1/cases/{case_id}/readiness")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total_required_questions"] == 1
    assert body["confirmed_required_questions"] == 0
    assert body["percentage"] == 0.0

    resp = client.post(
        f"/api/v1/cases/{case_id}/questions/{question_id}/review",
        json={"action": "ACCEPT", "reviewer_name": "Alice"},
    )
    assert resp.status_code == 200, resp.text

    resp = client.get(f"/api/v1/cases/{case_id}/readiness")
    body = resp.json()
    assert body["confirmed_required_questions"] == 1
    assert body["percentage"] == 100.0
