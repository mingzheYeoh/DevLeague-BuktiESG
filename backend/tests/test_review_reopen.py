"""REOPEN, and the refusal that makes it necessary.

Two defects are covered here, both found by using the UI in a normal way —
marking a question not applicable and then trying to answer it anyway:

1. ACCEPT and EDIT used to succeed on a NOT_APPLICABLE question, leaving a
   record that said "does not apply", "the answer is X", and "reason: <old
   not-applicable reason>" all at once.
2. Nothing could clear NOT_APPLICABLE. Not ACCEPT, not EDIT, not REJECT, and not
   uploading genuinely relevant evidence — the rule engine returns
   NOT_APPLICABLE unchanged by design, so the status was a one-way door.
   RULING-02 says a human action may "set or clear" it; only the setting half
   existed.
"""

from __future__ import annotations

import io

from openpyxl import Workbook

#: The `default_org` fixture's user (backend/tests/conftest.py:83). The
#: server now takes the reviewer from the session, not the request body.
REVIEWER = "member@tenggara.example"


def _questionnaire(question_text: str = "Report total annual electricity consumption in kWh.") -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Questionnaire"
    ws.append(["external_question_id", "question_text", "section", "is_required"])
    ws.append(["Q-E-01", question_text, "Environment", True])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _case_with_one_question(client) -> tuple[str, str]:
    case_id = client.post("/api/v1/cases", json={"title": "Reopen"}).json()["id"]
    client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={
            "file": (
                "q.xlsx",
                _questionnaire(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        data={"document_type": "QUESTIONNAIRE"},
    )
    question_id = client.get(f"/api/v1/cases/{case_id}/questions").json()[0]["id"]
    return case_id, question_id


def _review(client, case_id: str, question_id: str, **body):
    return client.post(
        f"/api/v1/cases/{case_id}/questions/{question_id}/review",
        json=body,
    )


def _mark_not_applicable(client, case_id: str, question_id: str, reason: str = "No meter on site."):
    resp = _review(client, case_id, question_id, action="NOT_APPLICABLE", reason=reason)
    assert resp.status_code == 200, resp.text
    assert resp.json()["evidence_status"] == "NOT_APPLICABLE"
    return resp.json()


# --------------------------------------------------------------------------- #
# 1. A not-applicable question cannot also be answered
# --------------------------------------------------------------------------- #


def test_edit_is_refused_on_a_not_applicable_question(client):
    case_id, question_id = _case_with_one_question(client)
    _mark_not_applicable(client, case_id, question_id)

    resp = _review(client, case_id, question_id, action="EDIT", edited_answer="Not sure")

    assert resp.status_code == 422
    error = resp.json()["detail"]["error"]
    assert error["code"] == "QUESTION_NOT_APPLICABLE"
    assert error["details"]["required_action"] == "REOPEN"
    # The old reason is surfaced so the caller can see what it is overriding.
    assert error["details"]["not_applicable_reason"] == "No meter on site."


def test_accept_is_refused_on_a_not_applicable_question(client):
    case_id, question_id = _case_with_one_question(client)
    _mark_not_applicable(client, case_id, question_id)

    resp = _review(client, case_id, question_id, action="ACCEPT")

    assert resp.status_code == 422
    assert resp.json()["detail"]["error"]["code"] == "QUESTION_NOT_APPLICABLE"


def test_the_refusal_leaves_the_answer_untouched(client):
    """A rejected request must not half-apply."""
    case_id, question_id = _case_with_one_question(client)
    before = _mark_not_applicable(client, case_id, question_id)

    _review(client, case_id, question_id, action="EDIT", edited_answer="Not sure")

    after = client.get(f"/api/v1/cases/{case_id}/questions").json()[0]
    assert after["evidence_status"] == before["evidence_status"]
    assert after["review_status"] == before["review_status"]
    assert after["status_reason"] == before["status_reason"]


def test_reject_is_still_allowed_on_a_not_applicable_question(client):
    """REJECT is a verdict on the draft, not an answer, so it stays available."""
    case_id, question_id = _case_with_one_question(client)
    _mark_not_applicable(client, case_id, question_id)

    resp = _review(client, case_id, question_id, action="REJECT", reason="Wrong call.")

    assert resp.status_code == 200
    assert resp.json()["review_status"] == "REJECTED"


# --------------------------------------------------------------------------- #
# 2. REOPEN is the way out
# --------------------------------------------------------------------------- #


def test_reopen_clears_not_applicable_and_hands_status_back_to_the_engine(client):
    case_id, question_id = _case_with_one_question(client)
    _mark_not_applicable(client, case_id, question_id)

    resp = _review(client, case_id, question_id, action="REOPEN", reason="It does apply after all.")

    assert resp.status_code == 200, resp.text
    answer = resp.json()
    # The engine recomputed from actual evidence. With no evidence uploaded that
    # is MISSING — a value the engine chose, not one this endpoint picked.
    assert answer["evidence_status"] == "MISSING"
    assert answer["not_applicable_reason"] is None
    assert answer["review_status"] == "UNREVIEWED"
    assert answer["confirmed_answer"] is None
    assert f"Reopened by {REVIEWER}" in answer["status_reason"]
    assert "It does apply after all." in answer["status_reason"]


def test_reopen_then_the_evidence_engine_works_again(client):
    """The point of reopening: uploading relevant evidence has an effect again.

    Before REOPEN existed, this upload changed nothing — the engine short-circuits
    on NOT_APPLICABLE.
    """
    case_id, question_id = _case_with_one_question(client)
    _mark_not_applicable(client, case_id, question_id)

    # While not applicable: evidence has no effect.
    client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={
            "file": (
                "bill.txt",
                b"Total electricity consumption: 12,840 kWh for January 2025.\n",
                "text/plain",
            )
        },
        data={"document_type": "UTILITY_BILL"},
    )
    stuck = client.get(f"/api/v1/cases/{case_id}/questions").json()[0]
    assert stuck["evidence_status"] == "NOT_APPLICABLE"

    # After reopening, the same evidence is evaluated.
    _review(client, case_id, question_id, action="REOPEN", reason="Meter was found.")
    reopened = client.get(f"/api/v1/cases/{case_id}/questions").json()[0]

    assert reopened["evidence_status"] == "PARTIAL"
    assert reopened["status_points"]
    assert reopened["evidence_candidate_count"] >= 1


def test_reopen_withdraws_a_confirmation_and_drops_readiness(client):
    """REOPEN on a confirmed answer, not a not-applicable one."""
    case_id, question_id = _case_with_one_question(client)

    _review(client, case_id, question_id, action="EDIT", edited_answer="12,840 kWh in Jan 2025.")
    assert client.get(f"/api/v1/cases/{case_id}/readiness").json()[
        "confirmed_required_questions"
    ] == 1

    resp = _review(client, case_id, question_id, action="REOPEN", reason="Figure was wrong.")

    answer = resp.json()
    assert answer["review_status"] == "UNREVIEWED"
    assert answer["confirmed_answer"] is None
    assert answer["draft_provenance"] == "NONE"
    # A withdrawn confirmation must stop counting as ready.
    assert client.get(f"/api/v1/cases/{case_id}/readiness").json()[
        "confirmed_required_questions"
    ] == 0


def test_reopen_does_not_disturb_evidence_status_when_it_was_not_not_applicable(client):
    case_id, question_id = _case_with_one_question(client)
    client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={
            "file": (
                "bill.txt",
                b"Total electricity consumption: 12,840 kWh for January 2025.\n",
                "text/plain",
            )
        },
        data={"document_type": "UTILITY_BILL"},
    )
    before = client.get(f"/api/v1/cases/{case_id}/questions").json()[0]
    assert before["evidence_status"] == "PARTIAL"

    _review(client, case_id, question_id, action="EDIT", edited_answer="12,840 kWh.")
    resp = _review(client, case_id, question_id, action="REOPEN", reason="Recheck.")

    assert resp.json()["evidence_status"] == "PARTIAL"


def test_reopen_requires_a_reason(client):
    case_id, question_id = _case_with_one_question(client)
    _mark_not_applicable(client, case_id, question_id)

    for body in ({"action": "REOPEN"}, {"action": "REOPEN", "reason": "   "}):
        resp = _review(client, case_id, question_id, **body)
        assert resp.status_code == 422, resp.text
        assert resp.json()["detail"]["error"]["code"] == "VALIDATION_ERROR"

    # Still not applicable — the failed attempts changed nothing.
    assert (
        client.get(f"/api/v1/cases/{case_id}/questions").json()[0]["evidence_status"]
        == "NOT_APPLICABLE"
    )


def test_the_full_round_trip_leaves_no_contradiction(client):
    """The exact sequence a user hit: mark N/A, try to answer, reopen, answer.

    The end state must assert one thing, not three.
    """
    case_id, question_id = _case_with_one_question(client)

    _mark_not_applicable(client, case_id, question_id, reason="No electricity use mentioned.")
    refused = _review(client, case_id, question_id, action="EDIT", edited_answer="Not sure")
    assert refused.status_code == 422

    _review(client, case_id, question_id, action="REOPEN", reason="It does apply.")
    final = _review(
        client,
        case_id,
        question_id,
        action="EDIT",
        edited_answer="38,420 kWh evidenced for Jan-Mar 2025; Apr-Dec outstanding.",
    ).json()

    assert final["evidence_status"] != "NOT_APPLICABLE"
    assert final["not_applicable_reason"] is None
    assert final["review_status"] == "HUMAN_CONFIRMED"
    assert final["confirmed_answer"].startswith("38,420 kWh")
    assert "NOT_APPLICABLE" not in (final["status_reason"] or "")


def test_reopen_is_an_accepted_action_verb(client):
    """A bad verb still 422s with the allow-list, and REOPEN is now in it."""
    case_id, question_id = _case_with_one_question(client)

    resp = _review(client, case_id, question_id, action="UNMARK", reason="x")

    assert resp.status_code == 422
    assert "REOPEN" in resp.json()["detail"]["error"]["details"]["allowed"]


def test_reopening_a_normal_question_keeps_the_rule_engine_s_reason(client):
    """REOPEN on a question that was never NOT_APPLICABLE.

    That branch leaves `evidence_status` and `status_findings_json` exactly as
    the rule engine set them — only the review decision is being withdrawn. So
    the prose has to survive too. Overwriting it with the reopen note alone
    leaves the record reporting a status whose stated reason names nobody but
    the person who pressed Undo, and nothing recomputes the engine's sentence
    until the document is analysed again.
    """
    case_id, question_id = _case_with_one_question(client)
    before = client.get(f"/api/v1/cases/{case_id}/questions").json()[0]
    engine_reason = before["status_reason"]
    assert engine_reason, "no engine reason to preserve — test setup is wrong"

    _review(client, case_id, question_id, action="ACCEPT")
    resp = _review(client, case_id, question_id, action="REOPEN", reason="Confirmed too early.")

    assert resp.status_code == 200, resp.text
    answer = resp.json()
    assert f"Reopened by {REVIEWER}" in answer["status_reason"]
    assert engine_reason in answer["status_reason"], (
        "the rule engine's audit sentence was destroyed by the reopen; "
        f"got {answer['status_reason']!r}"
    )
    # The engine's own verdict is untouched — only the review was withdrawn.
    assert answer["evidence_status"] == before["evidence_status"]
