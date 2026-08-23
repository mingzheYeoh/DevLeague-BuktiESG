"""GET /api/v1/cases — the Case list the frontend's entry screen reads.

Added alongside the frontend binding work: without a server-side list, a
reloaded browser has no way to recover the Case ids it created, so the
workspace renders empty even though the rows exist.
"""

from __future__ import annotations


def test_list_cases_is_empty_before_any_case_exists(client):
    resp = client.get("/api/v1/cases")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_cases_returns_every_created_case(client):
    created_ids = []
    for title in ("Case A", "Case B", "Case C"):
        resp = client.post(
            "/api/v1/cases",
            json={"title": title, "customer_name": f"{title} Customer"},
        )
        assert resp.status_code == 201, resp.text
        created_ids.append(resp.json()["id"])

    resp = client.get("/api/v1/cases")
    assert resp.status_code == 200
    listed = resp.json()
    assert len(listed) == 3
    # Set comparison, not order: three Cases created in the same tick can
    # share an updated_at value, so a strict ordering assertion would be
    # flaky rather than meaningful.
    assert {c["id"] for c in listed} == set(created_ids)

    # Same shape as GET /cases/{case_id} — CaseSummary, so the frontend can
    # reuse one type for both.
    one = listed[0]
    assert set(one) == {
        "id",
        "title",
        "customer_name",
        "deadline_at",
        "status",
        "updated_at",
    }
    assert one["status"] == "DRAFT"


def test_list_cases_does_not_shadow_get_case_by_id(client):
    """`GET /cases` and `GET /cases/{case_id}` must both keep working — the
    list route is registered on the empty path, so it must not swallow a
    request carrying an id segment."""
    case_id = client.post("/api/v1/cases", json={"title": "Case"}).json()["id"]

    resp = client.get(f"/api/v1/cases/{case_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == case_id

    resp = client.get("/api/v1/cases/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"]["code"] == "CASE_NOT_FOUND"
