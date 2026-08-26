"""Foreign object ids arriving in a *request body*.

`require_case` authorises the Case named in the **path**. It says nothing about
ids the caller puts in the body, and neither of this project's two isolation
mechanisms can see them:

  * `test_isolation_guard.py` walks function *signatures*, so a body field
    typed `str | None` inside a Pydantic model is invisible to it.
  * `test_tenant_isolation.py` enumerates routes carrying `{case_id}` in the
    path and swaps the actor. A body-borne reference is not a route.

So a body reference is exactly the shape both guards were built to catch and
cannot. This file covers it directly.

The failure it was written for: `create_action` resolved `payload.question_id`
with a bare `db.get(Question, ...)` and checked only that the row existed. An
actor from organization B could name organization A's question and receive 201,
which leaked three things - that the id is real, a persisted foreign-key edge
into another tenant's data, and one bit of the victim's `evidence_status`,
because `requires_closure_evidence` is derived from it and returned in the
response.
"""

from __future__ import annotations

from tests.test_phase5_review_and_actions import _make_case_with_question


def _action_body(question_id: str | None = None) -> dict:
    body = {
        "type": "IMPROVEMENT",
        "title": "Close the gap",
        "owner_name": "Nur Aina",
        "owner_role": "Sustainability Lead",
        "next_step": "Collect the disposal receipts",
        "deadline_at": "2026-12-31T00:00:00Z",
    }
    if question_id is not None:
        body["question_id"] = question_id
    return body


def test_an_action_cannot_reference_another_organizations_question(
    client, client_other_org
):
    """The whole point of this file.

    Organization A owns a question. Organization B owns its own case. B may
    create actions on its own case all day, but naming A's question must fail -
    and must fail the same way as naming an id that does not exist anywhere,
    or the response is an existence oracle.
    """
    victim_case_id, victim_question_id = _make_case_with_question(client)

    attacker_case_id = client_other_org.post(
        "/api/v1/cases", json={"title": "Attacker's own case"}
    ).json()["id"]

    response = client_other_org.post(
        f"/api/v1/cases/{attacker_case_id}/actions",
        json=_action_body(victim_question_id),
    )

    assert response.status_code != 201, (
        "organization B created an Action referencing organization A's question"
    )
    assert response.status_code == 422
    assert response.json()["detail"]["error"]["code"] == "OBJECT_CASE_MISMATCH"


def test_a_foreign_question_is_refused_identically_to_one_that_does_not_exist(
    client, client_other_org
):
    """Absent and not-yours must be indistinguishable.

    Distinguishing them turns this endpoint into the same enumeration oracle
    that `require_case`'s 404-never-403 rule exists to prevent - just reached
    through the body instead of the path.
    """
    _victim_case_id, victim_question_id = _make_case_with_question(client)

    attacker_case_id = client_other_org.post(
        "/api/v1/cases", json={"title": "Attacker's own case"}
    ).json()["id"]

    foreign = client_other_org.post(
        f"/api/v1/cases/{attacker_case_id}/actions",
        json=_action_body(victim_question_id),
    )
    nonexistent = client_other_org.post(
        f"/api/v1/cases/{attacker_case_id}/actions",
        json=_action_body("question-that-never-existed"),
    )

    assert foreign.status_code == nonexistent.status_code
    assert (
        foreign.json()["detail"]["error"]["code"]
        == nonexistent.json()["detail"]["error"]["code"]
    )


def test_a_question_from_another_case_in_the_same_organization_is_also_refused(
    client,
):
    """Not only a tenancy rule.

    An Action hangs off one Case; a question belonging to a different Case is
    a broken edge regardless of who owns it. Asserted separately because a fix
    that only compared organizations would pass the tests above and still let
    an actor wire an Action to a question in a sibling case.
    """
    _first_case_id, question_id = _make_case_with_question(client)

    other_case_id = client.post(
        "/api/v1/cases", json={"title": "A second case, same organization"}
    ).json()["id"]

    response = client.post(
        f"/api/v1/cases/{other_case_id}/actions", json=_action_body(question_id)
    )

    assert response.status_code == 422
    assert response.json()["detail"]["error"]["code"] == "OBJECT_CASE_MISMATCH"


def test_an_action_on_its_own_case_question_still_works(client):
    """The guard must refuse foreign ids without refusing the real workflow."""
    case_id, question_id = _make_case_with_question(client)

    response = client.post(
        f"/api/v1/cases/{case_id}/actions", json=_action_body(question_id)
    )

    assert response.status_code == 201, response.text
    assert response.json()["question_id"] == question_id


def test_an_action_id_from_another_organization_is_not_found(client, client_other_org):
    """The other half of the same class: a child id in the PATH.

    The cross-tenant matrix swaps the case_id and keeps everything else, so it
    never tries "my own case, someone else's action". Every child lookup in
    every router was checked by hand and does verify ownership; this pins the
    one that would hurt most, so the next person to add an endpoint has an
    example rather than a promise.
    """
    victim_case_id, victim_question_id = _make_case_with_question(client)
    victim_action_id = client.post(
        f"/api/v1/cases/{victim_case_id}/actions", json=_action_body(victim_question_id)
    ).json()["id"]

    attacker_case_id = client_other_org.post(
        "/api/v1/cases", json={"title": "Attacker's own case"}
    ).json()["id"]

    response = client_other_org.post(
        f"/api/v1/cases/{attacker_case_id}/actions/{victim_action_id}/status",
        json={"status": "IN_PROGRESS"},
    )

    assert response.status_code == 404
    assert response.json()["detail"]["error"]["code"] == "ACTION_NOT_FOUND"
