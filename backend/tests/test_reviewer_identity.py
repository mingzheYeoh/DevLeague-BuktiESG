"""Who signed the verdict.

Until authentication existed, `reviewer_name` was whatever the client typed,
and the UI said so: "it proves nothing and grants nothing". AGENTS.md 3.2
requires that a human owns the verdict, and a signature anyone can type proves
no more than one the model issued.

Each endpoint gets two tests, and the second is the one that matters. Asserting
only that the server stores the right value would also pass against an
implementation that reads the body when present and falls back to the actor -
and that implementation closes nothing.
"""

from __future__ import annotations

from tests.test_evidence_accept import _case_with_one_link
from tests.test_phase5_review_and_actions import _make_case_with_question

#: The `default_org` fixture's user (backend/tests/conftest.py:83).
FIXTURE_EMAIL = "member@tenggara.example"


def test_review_records_the_signed_in_user(client):
    case_id, question_id = _make_case_with_question(client)

    response = client.post(
        f"/api/v1/cases/{case_id}/questions/{question_id}/review",
        json={"action": "ACCEPT"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["reviewer_name"] == FIXTURE_EMAIL


def test_review_ignores_a_reviewer_name_in_the_body(client, db_session):
    """The body cannot reach the column.

    Whether the server ignores the extra field or rejects the request is not
    what is pinned here - either is acceptable. What must be impossible is
    "Someone Else" ending up in `answers.reviewer_name`.
    """
    from app.models import Answer

    case_id, question_id = _make_case_with_question(client)

    response = client.post(
        f"/api/v1/cases/{case_id}/questions/{question_id}/review",
        json={"action": "ACCEPT", "reviewer_name": "Someone Else"},
    )
    assert response.status_code in (200, 422), response.text

    answer = db_session.query(Answer).filter(Answer.question_id == question_id).one()

    # Positive, not "is not the attacker's value". `!=` against a column that
    # happened to be NULL - or read from a payload field that does not exist -
    # passes by vacuum, which is exactly the failure this branch has already
    # produced twice.
    if response.status_code == 200:
        assert answer.reviewer_name == FIXTURE_EMAIL
    else:
        assert answer.reviewer_name is None


def test_review_no_longer_demands_a_reviewer_name(client):
    """The 422 guard is gone, not relaxed.

    A value the client cannot supply cannot be blank, so the old
    "reviewer_name is required" refusal has nothing left to refuse. This test
    fails loudly if the guard is left behind reading a field that no longer
    exists on the schema.
    """
    case_id, question_id = _make_case_with_question(client)

    response = client.post(
        f"/api/v1/cases/{case_id}/questions/{question_id}/review",
        json={"action": "ACCEPT"},
    )

    assert response.status_code == 200, response.text


def test_accept_records_the_signed_in_user(client, db_session):
    """`evidence_links.accepted_by`, a different column from
    `answers.reviewer_name` and written by different code - so it needs its own
    assertion, not a shared one."""
    case_id, _question_id, link_id = _case_with_one_link(client)

    response = client.post(
        f"/api/v1/cases/{case_id}/evidence-links/{link_id}/accept",
    )

    assert response.status_code == 200
    assert response.json()["accepted_by"] == FIXTURE_EMAIL


def test_accept_ignores_a_reviewer_name_in_the_body(client, db_session):
    case_id, _question_id, link_id = _case_with_one_link(client)

    response = client.post(
        f"/api/v1/cases/{case_id}/evidence-links/{link_id}/accept",
        json={"reviewer_name": "Someone Else"},
    )

    from app.models import EvidenceLink

    link = db_session.get(EvidenceLink, link_id)
    assert link.accepted_by != "Someone Else"
    if response.status_code == 200:
        assert link.accepted_by == FIXTURE_EMAIL
