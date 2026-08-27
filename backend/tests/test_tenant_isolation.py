"""One organization cannot see another's case.

This replaced a generated matrix that enumerated every `{case_id}` route from
`app.openapi()` and swapped the actor on each - 39 tests, plus an `ast` walker
that failed the build if a router took a bare `case_id: str`, plus a file
covering ids arriving in request bodies. All of that guarded *future* endpoints
against leaking *real* customer data, and this project is a demo with a fixed
surface. Three hand-written tests are the right size for what remains true.

What is still worth pinning, and why each one:

  * 404, never 403. A 403 confirms the identifier is real and belongs to
    someone else, which is exactly the fact the refusal is meant to withhold.
  * The refusal must be CASE_NOT_FOUND specifically. Asserting only `404` is a
    false assurance: an endpoint that resolved the child resource before
    checking the case would also answer 404 - "document not found" - while
    still disclosing a document whose id the caller guessed correctly.
  * Signed out is 401, not 404 or 200.
"""

from __future__ import annotations


def test_another_organizations_case_is_not_found(client, client_other_org):
    case_id = client.post("/api/v1/cases", json={"title": "Ours"}).json()["id"]

    response = client_other_org.get(f"/api/v1/cases/{case_id}")

    assert response.status_code == 404
    assert response.json()["detail"]["error"]["code"] == "CASE_NOT_FOUND"


def test_a_child_resource_is_refused_on_the_case_not_on_itself(
    client, client_other_org
):
    """The assertion that carries its weight.

    A document id that exists nowhere would produce 404 either way. What this
    pins is *which* 404: `CASE_NOT_FOUND` proves `require_case` ran before the
    document lookup. `DOCUMENT_NOT_FOUND` would mean the case check came
    second, and an attacker naming a real document id would learn it exists.
    """
    case_id = client.post("/api/v1/cases", json={"title": "Ours"}).json()["id"]

    response = client_other_org.get(
        f"/api/v1/cases/{case_id}/documents/does-not-matter/chunks"
    )

    assert response.status_code == 404
    assert response.json()["detail"]["error"]["code"] == "CASE_NOT_FOUND"


def test_a_signed_out_caller_gets_401(client, anonymous_client):
    case_id = client.post("/api/v1/cases", json={"title": "Ours"}).json()["id"]

    assert anonymous_client.get(f"/api/v1/cases/{case_id}").status_code == 401
    assert anonymous_client.get("/api/v1/cases").status_code == 401


def test_the_case_list_shows_only_your_own_organizations_cases(
    client, client_other_org
):
    """The one a viewer would actually notice, and the demo's whole point."""
    ours = client.post("/api/v1/cases", json={"title": "Ours"}).json()["id"]
    theirs = client_other_org.post(
        "/api/v1/cases", json={"title": "Theirs"}
    ).json()["id"]

    ids = {c["id"] for c in client.get("/api/v1/cases").json()}

    assert ours in ids
    assert theirs not in ids
