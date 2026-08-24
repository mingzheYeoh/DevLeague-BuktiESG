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
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
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
