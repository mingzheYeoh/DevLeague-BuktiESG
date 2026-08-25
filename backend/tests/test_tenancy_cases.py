"""One organization cannot see or touch another's cases."""


def _make_case(c, title="Questionnaire"):
    return c.post("/api/v1/cases", json={"title": title}).json()["id"]


def test_a_new_case_belongs_to_the_creators_organization(client, db_session, default_org):
    from app.models import Case

    org, _ = default_org
    case_id = _make_case(client)
    assert db_session.get(Case, case_id).organization_id == org.id


def test_the_case_list_shows_only_your_own(client, client_other_org):
    _make_case(client, "Ours")
    _make_case(client_other_org, "Theirs")

    ours = [c["title"] for c in client.get("/api/v1/cases").json()]
    theirs = [c["title"] for c in client_other_org.get("/api/v1/cases").json()]

    assert ours == ["Ours"]
    assert theirs == ["Theirs"]


def test_reading_another_organizations_case_is_404(client, client_other_org):
    case_id = _make_case(client)
    assert client_other_org.get(f"/api/v1/cases/{case_id}").status_code == 404


def test_reading_another_organizations_readiness_is_404(client, client_other_org):
    case_id = _make_case(client)
    assert client_other_org.get(f"/api/v1/cases/{case_id}/readiness").status_code == 404


def test_archiving_another_organizations_case_is_404(client, client_other_org):
    case_id = _make_case(client)
    assert client_other_org.post(f"/api/v1/cases/{case_id}/archive").status_code == 404


def test_listing_another_organizations_questions_is_404(client, client_other_org):
    case_id = _make_case(client)
    assert client_other_org.get(f"/api/v1/cases/{case_id}/questions").status_code == 404


def test_listing_another_organizations_actions_is_404(client, client_other_org):
    case_id = _make_case(client)
    assert client_other_org.get(f"/api/v1/cases/{case_id}/actions").status_code == 404


def test_signed_out_callers_get_401(anonymous_client):
    assert anonymous_client.get("/api/v1/cases").status_code == 401
