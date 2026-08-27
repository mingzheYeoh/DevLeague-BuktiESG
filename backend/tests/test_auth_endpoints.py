"""Registration, sign-in, sign-out, and what they refuse to disclose."""

from app.models import Organization, OrganizationMember, User

REGISTRATION = {
    "email": "director@tenggara.example",
    "password": "a long enough passphrase",
    "organization_name": "Tenggara Precision Sdn. Bhd.",
}


def test_registration_creates_user_org_and_admin_membership(anonymous_client, db_session):
    response = anonymous_client.post("/api/v1/auth/register", json=REGISTRATION)
    assert response.status_code == 201

    user = db_session.query(User).filter(User.email == REGISTRATION["email"]).one()
    membership = (
        db_session.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .one()
    )
    assert membership.role == "ADMIN"
    assert db_session.get(Organization, membership.organization_id).name == REGISTRATION["organization_name"]


def test_registration_stores_the_email_lowercased(anonymous_client, db_session):
    anonymous_client.post("/api/v1/auth/register", json={**REGISTRATION, "email": "DIRECTOR@Tenggara.Example"})
    assert db_session.query(User).filter(User.email == "director@tenggara.example").count() == 1


def test_registering_an_existing_address_looks_identical(anonymous_client):
    first = anonymous_client.post("/api/v1/auth/register", json=REGISTRATION)
    second = anonymous_client.post("/api/v1/auth/register", json=REGISTRATION)
    # The response must not reveal that the address is taken. A different
    # status or body here is a registered-user oracle.
    assert first.status_code == second.status_code == 201
    assert first.json() == second.json()


def test_registering_an_existing_address_creates_no_second_user(anonymous_client, db_session):
    anonymous_client.post("/api/v1/auth/register", json=REGISTRATION)
    anonymous_client.post("/api/v1/auth/register", json=REGISTRATION)
    assert db_session.query(User).filter(User.email == REGISTRATION["email"]).count() == 1


def test_login_sets_a_session_cookie(anonymous_client):
    anonymous_client.post("/api/v1/auth/register", json=REGISTRATION)
    response = anonymous_client.post(
        "/api/v1/auth/login",
        json={"email": REGISTRATION["email"], "password": REGISTRATION["password"]},
    )
    assert response.status_code == 200
    assert "bukti_session" in response.cookies


def test_login_with_a_wrong_password_is_401(anonymous_client):
    anonymous_client.post("/api/v1/auth/register", json=REGISTRATION)
    response = anonymous_client.post(
        "/api/v1/auth/login",
        json={"email": REGISTRATION["email"], "password": "not the passphrase"},
    )
    assert response.status_code == 401


def test_wrong_password_and_unknown_address_are_indistinguishable(anonymous_client):
    anonymous_client.post("/api/v1/auth/register", json=REGISTRATION)
    wrong_password = anonymous_client.post(
        "/api/v1/auth/login",
        json={"email": REGISTRATION["email"], "password": "not the passphrase"},
    )
    unknown_address = anonymous_client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@nowhere.example", "password": "not the passphrase"},
    )
    assert wrong_password.status_code == unknown_address.status_code
    assert wrong_password.json() == unknown_address.json()


def test_me_returns_the_actor(anonymous_client):
    anonymous_client.post("/api/v1/auth/register", json=REGISTRATION)
    anonymous_client.post(
        "/api/v1/auth/login",
        json={"email": REGISTRATION["email"], "password": REGISTRATION["password"]},
    )
    body = anonymous_client.get("/api/v1/auth/me").json()
    assert body["email"] == REGISTRATION["email"]
    assert body["role"] == "ADMIN"


def test_logout_stops_the_session_working(anonymous_client):
    anonymous_client.post("/api/v1/auth/register", json=REGISTRATION)
    anonymous_client.post(
        "/api/v1/auth/login",
        json={"email": REGISTRATION["email"], "password": REGISTRATION["password"]},
    )
    anonymous_client.post("/api/v1/auth/logout")
    assert anonymous_client.get("/api/v1/auth/me").status_code == 401

