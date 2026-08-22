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
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
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
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
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
