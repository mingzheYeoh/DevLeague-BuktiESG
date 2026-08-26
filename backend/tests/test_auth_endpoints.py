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


def test_registration_hashes_on_both_paths(client, db_session, monkeypatch):
    """A taken address and a fresh one must cost the same.

    The response bodies are already identical - that is asserted elsewhere.
    This asserts the other half: that the two paths do the same *work*, so the
    clock cannot answer what the body refuses to.

    Counting the argon2 call rather than measuring elapsed time, because a
    timing assertion on a shared CI box is a coin flip.

    Be clear about what this does NOT prove. Counting is a proxy: it pins that
    both paths *invoke* the hash, not that both paths *cost* the same. If
    `hash_password` ever gained a fast path - memoisation on the password, a
    cache - this test would stay green while the timing oracle reopened.

    Nor is the gap fully closed: measured after the fix, a fresh address takes
    ~72ms and a taken one ~42ms, because only the fresh path performs three
    inserts and a commit. This test guards the specific regression of moving
    the hash back behind the existence check. The residual ~30ms is recorded
    in the endpoint's comment and is not covered by anything here.
    """
    from app.routers import auth as auth_router

    calls: list[str] = []
    real = auth_router.hash_password

    def _counting(password: str) -> str:
        calls.append(password)
        return real(password)

    monkeypatch.setattr(auth_router, "hash_password", _counting)

    body = {
        "email": "timing@tenggara.example",
        "password": "a sufficiently long passphrase",
        "organization_name": "Timing Sdn. Bhd.",
    }

    first = client.post("/api/v1/auth/register", json=body)
    assert first.status_code == 201
    assert len(calls) == 1, "the fresh-address path must hash"

    second = client.post("/api/v1/auth/register", json=body)
    assert second.status_code == 201
    assert second.json() == first.json(), "the bodies must stay identical"
    assert len(calls) == 2, (
        "the taken-address path returned without hashing, so the response "
        "clock still says whether the address is registered"
    )
