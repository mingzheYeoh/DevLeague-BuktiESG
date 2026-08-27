"""Session lifecycle: creation, resolution, expiry, revocation."""

from datetime import datetime, timedelta, timezone

from app.models import Organization, SessionRow, User
from app.services.sessions import resolve_session, revoke_session, start_session


def _actor(db):
    user = User(email="a@example.com", password_hash="x")
    org = Organization(name="Tenggara Precision")
    db.add_all([user, org])
    db.commit()
    return user, org


def test_start_session_returns_a_token_that_resolves(db_session):
    user, org = _actor(db_session)
    row, token = start_session(db_session, user.id, org.id)
    assert resolve_session(db_session, token).id == row.id


def test_the_plaintext_token_is_never_stored(db_session):
    user, org = _actor(db_session)
    _, token = start_session(db_session, user.id, org.id)
    assert db_session.query(SessionRow).one().token_hash != token


def test_an_unknown_token_resolves_to_nothing(db_session):
    _actor(db_session)
    assert resolve_session(db_session, "not-a-real-token") is None


def test_a_revoked_session_stops_resolving(db_session):
    user, org = _actor(db_session)
    row, token = start_session(db_session, user.id, org.id)
    revoke_session(db_session, row)
    assert resolve_session(db_session, token) is None


def test_an_expired_session_stops_resolving(db_session):
    user, org = _actor(db_session)
    row, token = start_session(db_session, user.id, org.id)
    row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.commit()
    assert resolve_session(db_session, token) is None


def test_the_session_carries_the_acting_organization(db_session):
    user, org = _actor(db_session)
    _, token = start_session(db_session, user.id, org.id)
    assert resolve_session(db_session, token).organization_id == org.id
