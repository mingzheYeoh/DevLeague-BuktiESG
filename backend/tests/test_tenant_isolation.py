"""Every case-rooted route, checked against a second organization.

Generated from `app.routes` rather than written by hand, and that is the whole
point. A hand-written list would have been derived from the places the code
already loads a case - which is exactly the list that omitted
`list_evidence_links`. Enumerating the router instead means a new endpoint joins
this matrix the moment it is added, whether or not anyone remembers to.
"""

from __future__ import annotations

import pytest

from app.main import app

def _case_rooted_routes():
    """Every (method, path) that takes a case_id, from the OpenAPI schema.

    Not from `app.routes`. This FastAPI version does not flatten
    `include_router` into that list — each included router appears there as a
    single `_IncludedRouter` object with no `path` and no `methods`, so walking
    it finds four documentation endpoints, `/health`, and nothing else. A
    generator written that way yields an empty matrix, and every parametrised
    test below then passes by vacuum. `test_the_matrix_is_not_empty` exists
    because that failure is silent.

    `app.openapi()` is a public, documented surface and reports the resolved
    paths whatever the router machinery looks like underneath.
    """
    paths = app.openapi()["paths"]
    return sorted(
        (method.upper(), path)
        for path, operations in paths.items()
        for method in operations
        if "{case_id}" in path and method.upper() not in ("HEAD", "OPTIONS")
    )


CASE_ROOTED_ROUTES = _case_rooted_routes()


def test_the_matrix_is_not_empty():
    # A generator that silently found nothing would make every test below pass
    # by vacuum. This is the canary for that.
    assert len(CASE_ROOTED_ROUTES) >= 15


@pytest.mark.parametrize("method,path", CASE_ROOTED_ROUTES)
def test_another_organization_gets_404(method, path, client, client_other_org):
    case_id = client.post("/api/v1/cases", json={"title": "Ours"}).json()["id"]

    # Placeholder ids for nested resources. They do not need to exist, because
    # the assertion below is on the error *code*, not the status.
    #
    # Asserting only `status_code == 404` would be a false assurance, and this
    # is the trap worth naming: an implementation that resolved the child
    # resource before checking the case would also answer 404 here - "document
    # not found" - and pass, while still disclosing a document whose id an
    # attacker actually knew. CASE_NOT_FOUND is the only answer that proves the
    # case check ran first.
    url = path.format(
        case_id=case_id,
        document_id="00000000-0000-0000-0000-000000000001",
        question_id="00000000-0000-0000-0000-000000000002",
        action_id="00000000-0000-0000-0000-000000000003",
        evidence_link_id="00000000-0000-0000-0000-000000000004",
    )

    response = client_other_org.request(method, url)
    assert response.status_code == 404, (
        f"{method} {path} returned {response.status_code} to another organization. "
        "Every case-rooted route must resolve its Case through require_case."
    )
    assert response.json()["detail"]["error"]["code"] == "CASE_NOT_FOUND", (
        f"{method} {path} refused another organization, but not on the case. "
        f"Got {response.json()['detail']['error']['code']}, which means a child resource "
        "was resolved before the Case was authorised. Take "
        "`case: Case = Depends(require_case)` so the case check runs first."
    )


@pytest.mark.parametrize("method,path", CASE_ROOTED_ROUTES)
def test_signed_out_callers_get_401(method, path, client, anonymous_client):
    case_id = client.post("/api/v1/cases", json={"title": "Ours"}).json()["id"]
    url = path.format(
        case_id=case_id,
        document_id="00000000-0000-0000-0000-000000000001",
        question_id="00000000-0000-0000-0000-000000000002",
        action_id="00000000-0000-0000-0000-000000000003",
        evidence_link_id="00000000-0000-0000-0000-000000000004",
    )
    assert anonymous_client.request(method, url).status_code == 401
