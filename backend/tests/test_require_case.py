"""The isolation chokepoint, tested directly rather than through a route."""

import pytest
from fastapi import HTTPException

from app.auth import Actor, require_case
from app.models import Case, Organization


def _case_in_new_org(db, org_name):
    org = Organization(name=org_name)
    db.add(org)
    db.commit()
    case = Case(title="Questionnaire", organization_id=org.id)
    db.add(case)
    db.commit()
    return case, org


def test_an_actor_of_the_owning_organization_gets_the_case(db_session):
    case, org = _case_in_new_org(db_session, "Tenggara Precision")
    actor = Actor(user_id="u", organization_id=org.id, role="MEMBER")
    assert require_case(case.id, actor, db_session).id == case.id


def test_an_actor_of_another_organization_gets_404_not_403(db_session):
    case, _ = _case_in_new_org(db_session, "Tenggara Precision")
    _, other = _case_in_new_org(db_session, "Somebody Else Sdn Bhd")
    actor = Actor(user_id="u", organization_id=other.id, role="ADMIN")
    with pytest.raises(HTTPException) as caught:
        require_case(case.id, actor, db_session)
    # 403 would confirm the id is real and owned by someone else. Absent and
    # forbidden have to be indistinguishable from outside.
    assert caught.value.status_code == 404


def test_a_missing_case_and_another_organizations_case_are_indistinguishable(db_session):
    case, _ = _case_in_new_org(db_session, "Tenggara Precision")
    _, other = _case_in_new_org(db_session, "Somebody Else Sdn Bhd")
    actor = Actor(user_id="u", organization_id=other.id, role="ADMIN")

    with pytest.raises(HTTPException) as forbidden:
        require_case(case.id, actor, db_session)
    with pytest.raises(HTTPException) as missing:
        require_case("00000000-0000-0000-0000-000000000000", actor, db_session)

    assert forbidden.value.status_code == missing.value.status_code
    # `api_error` nests under an "error" key: detail["error"]["code"].
    assert forbidden.value.detail["error"]["code"] == missing.value.detail["error"]["code"]
