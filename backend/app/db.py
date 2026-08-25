"""Database engine/session wiring (SQLAlchemy 2.0)."""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone

from sqlalchemy import DateTime, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.types import TypeDecorator

from app.config import settings


class UtcDateTime(TypeDecorator):
    """A timestamp column that is UTC-aware on every dialect.

    `DateTime(timezone=True)` is a promise Postgres keeps and SQLite cannot:
    SQLite has no timezone type, so it stores the naive text and returns
    `tzinfo=None`. Pydantic then serialises without an offset, and a browser
    reads an offset-less ISO string as *local* time — eight hours out in
    UTC+8. Same class of divergence as foreign keys being unenforced here and
    enforced there: correct in production, wrong in dev, invisible in review.

    On the way in, a naive value is taken to be UTC (nothing in this codebase
    writes local time) and an aware one is converted, so the instant is
    preserved rather than the wall clock. On the way out, a naive value read
    from an existing row is labelled UTC, which is what it has always been.

    The rendered DDL is unchanged, so this needs no migration.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:  # noqa: ANN001
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:  # noqa: ANN001
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


def _connect_args(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


engine = create_engine(
    settings.database_url,
    connect_args=_connect_args(settings.database_url),
    future=True,
)

if settings.database_url.startswith("sqlite"):
    # SQLite ignores foreign keys unless each connection asks for them;
    # Postgres, the real target, always enforces them. Left off, the local
    # database accepts writes and deletes that production rejects — the
    # difference surfaces as a 500 after deploy rather than a failure here.
    @event.listens_for(engine, "connect")
    def _sqlite_enforce_foreign_keys(dbapi_connection, _connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
