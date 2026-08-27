"""Test fixtures.

TEST-ONLY SUBSTITUTION: these tests run against an isolated in-memory SQLite
database, created fresh per test via SQLAlchemy's ``Base.metadata.create_all``
(not Alembic). This is explicitly a test-only stand-in because no live
PostgreSQL instance was reachable in this environment (no DATABASE_URL, no
psql/pg_isready). It is never used for real persistence — real persistence
uses Postgres via Alembic migrations (see migrations/versions/). The CHECK
constraints written for Postgres (`text` + CHECK, per RULING-01) are also
valid, enforced SQLite CHECK constraints, so this still exercises the enum
guard rails, just not the Postgres-specific dialect.

Foreign keys are switched on per connection below. SQLite leaves them off by
default, which would otherwise let this suite pass a DELETE that Postgres
rejects.
"""

from __future__ import annotations

import pathlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # SQLite ignores foreign keys unless each connection opts in, and Postgres
    # — the real target — never does. Without this the two databases disagree
    # about what is legal: a DELETE that Postgres refuses with a
    # ForeignKeyViolation just silently orphans rows here, and the test passes.
    # Turning it on is what makes a missing ORM cascade fail in CI instead of
    # in production.
    @event.listens_for(engine, "connect")
    def _enforce_foreign_keys(dbapi_connection, _record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # `documents.latest_job_id` and `processing_jobs.document_id` reference
        # each other, so with foreign keys enforced there is no order in which
        # every table can be dropped. The schema declares the cycle with
        # `use_alter`, which solves it for CREATE/DROP on Postgres but not on
        # SQLite. Teardown is not what this suite is testing, so the pragma
        # goes off for the drop only.
        with engine.begin() as connection:
            connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def default_org(db_session):
    """The organization every unqualified test acts for.

    Created directly rather than through the registration endpoint: the tests
    that exercise registration want a clean database, and a fixture that posts
    to the API would put a user in every one of them.
    """
    from app.models import Organization, OrganizationMember, User
    from app.services.passwords import hash_password

    org = Organization(name="Tenggara Precision Sdn. Bhd.")
    user = User(email="member@tenggara.example", password_hash=hash_password("fixture passphrase"))
    db_session.add_all([org, user])
    db_session.flush()
    db_session.add(OrganizationMember(user_id=user.id, organization_id=org.id, role="ADMIN"))
    db_session.commit()
    return org, user


@pytest.fixture()
def client(db_session, default_org):
    """An authenticated client, acting for `default_org`.

    Authentication is the default because it is the normal case: nearly every
    endpoint requires it, and a suite whose default client is anonymous would
    make each of 166 tests carry a sign-in it does not care about.

    Tests that need the anonymous case ask for `anonymous_client`.
    """
    from app.auth import SESSION_COOKIE_NAME
    from app.services.sessions import start_session

    org, user = default_org

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    _, token = start_session(db_session, user.id, org.id)
    with TestClient(app, base_url="https://testserver") as c:
        c.cookies.set(SESSION_COOKIE_NAME, token)
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def anonymous_client(db_session):
    """No session cookie. For testing that endpoints refuse the signed-out."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    # This fixture's tests sign in for real and receive a Set-Cookie carrying
    # Secure=True (production requirement). Over http:// httpx silently drops it,
    # making subsequent requests fail authentication. https:// base_url makes
    # httpx honour it over ASGI transport (no TLS/certs needed). The other two
    # clients inject their token with cookies.set(), which httpx forces to
    # secure=False, so https:// does nothing for them — it's here for consistency.
    with TestClient(app, base_url="https://testserver") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def client_other_org(db_session):
    """A second organization's client, for cross-tenant tests.

    Deliberately a different organization *and* a different user: a test that
    shared the user would still pass if isolation were keyed on user rather
    than organization, which is not what this system promises.
    """
    from app.auth import SESSION_COOKIE_NAME
    from app.models import Organization, OrganizationMember, User
    from app.services.passwords import hash_password
    from app.services.sessions import start_session

    org = Organization(name="Somebody Else Sdn. Bhd.")
    user = User(email="outsider@example.com", password_hash=hash_password("another passphrase"))
    db_session.add_all([org, user])
    db_session.flush()
    db_session.add(OrganizationMember(user_id=user.id, organization_id=org.id, role="ADMIN"))
    db_session.commit()

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    _, token = start_session(db_session, user.id, org.id)
    with TestClient(app, base_url="https://testserver") as c:
        c.cookies.set(SESSION_COOKIE_NAME, token)
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def isolated_storage_root(request, monkeypatch):
    """Point the storage root at a per-test directory.

    Without this the suite writes into `backend/var/storage`, the same tree a
    developer's own cases live in, and never cleans up: every uploaded fixture
    left a directory behind. That is where most of the 1,252 orphan
    directories this repository accumulated came from, and it also made tests
    that reconcile storage against the database see each other's files.

    Under `var/` rather than pytest's `tmp_path`, which cannot be created in
    this sandbox - the same restriction that makes `.pytest_cache` unwritable.

    `storage.STORAGE_ROOT` is a module constant read at call time, so patching
    the attribute is enough; nothing captures it at import.
    """
    import shutil
    import uuid

    from app.services import storage

    root = pathlib.Path(__file__).resolve().parents[1] / "var" / "test-storage" / uuid.uuid4().hex
    root.mkdir(parents=True)
    monkeypatch.setattr(storage, "STORAGE_ROOT", root)
    yield root
    shutil.rmtree(root, ignore_errors=True)
