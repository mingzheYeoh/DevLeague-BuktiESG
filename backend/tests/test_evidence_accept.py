"""Accepting an evidence link, and the VERIFIED status it makes reachable.

`compute_evidence_status` has always had a VERIFIED branch, and of its six
conditions the sample data already satisfied five: every link the matcher
writes carries a `claim_supported` and a server-resolved `location_json`, no
link carries a value without a unit, and the questionnaire states no required
period or scope. The sixth, `link_status == 'ACCEPTED'`, had no endpoint that
could set it, so `REASON_NOT_ACCEPTED` applied to all 231 links in the sample
case and VERIFIED was unreachable.

Acceptance is a human verdict, not a computed one (AGENTS.md 3.2 - the AI
never owns a verdict), so it carries no reviewer_name in the request at all -
the server takes the reviewer from the signed-in session
(`app/auth.py::actor_email`), the same source `answers.reviewer_name` now
comes from. VERIFIED is the strongest claim this system makes, and one that
cannot name its author is the kind of unprovable claim the product exists to
refuse.
"""

from __future__ import annotations

import io

from openpyxl import Workbook


def _questionnaire(text: str) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(["external_question_id", "question_text", "section", "is_required"])
    ws.append(["Q-1", text, "Environment", True])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _case_with_one_link(client) -> tuple[str, str, str]:
    """A case whose single question has exactly one candidate evidence link."""
    case_id = client.post("/api/v1/cases", json={"title": "Accept"}).json()["id"]

    client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": ("q.xlsx", _questionnaire(
            "Report the total scheduled waste tonnes disposed during the year."
        ), "application/octet-stream")},
        data={"document_type": "QUESTIONNAIRE"},
    )
    client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": ("waste.txt", b"Scheduled waste disposed: 12.6 tonnes.", "text/plain")},
        data={"document_type": "WASTE_RECORD"},
    )

    questions = client.get(f"/api/v1/cases/{case_id}/questions").json()
    questions = questions["items"] if isinstance(questions, dict) else questions
    question_id = questions[0]["id"]

    listed = client.get(
        f"/api/v1/cases/{case_id}/questions/{question_id}/evidence-links"
    )
    assert listed.status_code == 200, listed.text
    links = listed.json()
    assert links, "the matcher wrote no candidate link for this question"
    return case_id, question_id, links[0]["id"]


def test_a_questions_evidence_links_are_addressable(client):
    """Without this, `/accept` and the existing `/invalidate` are endpoints no
    client can call: both take an evidence_link_id, and until now no GET
    returned one."""
    case_id, question_id, _ = _case_with_one_link(client)

    links = client.get(
        f"/api/v1/cases/{case_id}/questions/{question_id}/evidence-links"
    ).json()

    assert [link["link_status"] for link in links] == ["CANDIDATE"]
    assert links[0]["question_id"] == question_id
    assert links[0]["id"]


def test_accepting_a_link_records_who_accepted_it(client):
    case_id, _question_id, link_id = _case_with_one_link(client)

    resp = client.post(
        f"/api/v1/cases/{case_id}/evidence-links/{link_id}/accept",
    )

    assert resp.status_code == 200, resp.text
    link = resp.json()
    assert link["link_status"] == "ACCEPTED"
    assert link["accepted_by"] == "member@tenggara.example"
    assert link["accepted_at"] is not None


def _status(client, case_id: str) -> str:
    questions = client.get(f"/api/v1/cases/{case_id}/questions").json()
    questions = questions["items"] if isinstance(questions, dict) else questions
    return questions[0]["evidence_status"]


def test_accepting_the_evidence_makes_the_question_verified(client):
    """The point of the endpoint.

    Five of the six VERIFIED conditions were already satisfied by what the
    matcher writes: a claim, a server-resolved location, no value without a
    unit, and a questionnaire that states no required period or scope. The
    sixth was acceptance, and nothing could grant it.
    """
    case_id, _question_id, link_id = _case_with_one_link(client)
    assert _status(client, case_id) == "PARTIAL"

    client.post(
        f"/api/v1/cases/{case_id}/evidence-links/{link_id}/accept",
    )

    assert _status(client, case_id) == "VERIFIED"


def test_the_question_names_the_link_it_is_showing(client):
    """The detail screen shows one link out of possibly many. To accept *that*
    one it needs its id, and to render its state it needs to know whether it
    has been accepted and by whom."""
    case_id, _question_id, link_id = _case_with_one_link(client)

    questions = client.get(f"/api/v1/cases/{case_id}/questions").json()
    question = (questions["items"] if isinstance(questions, dict) else questions)[0]
    assert question["evidence_link_id"] == link_id
    assert question["evidence_accepted_by"] is None

    client.post(
        f"/api/v1/cases/{case_id}/evidence-links/{link_id}/accept",
    )

    questions = client.get(f"/api/v1/cases/{case_id}/questions").json()
    question = (questions["items"] if isinstance(questions, dict) else questions)[0]
    assert question["evidence_accepted_by"] == "member@tenggara.example"
