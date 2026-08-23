"""Create the local SQLite dev schema from the ORM models.

**Development only. Not a migration path, and not for any real database.**

Why this exists: `app/config.py` falls back to `sqlite:///./buktiesg_dev.db` so the
app can boot without a live PostgreSQL instance, but the Alembic migrations in
`migrations/versions/` are written for PostgreSQL and cannot run on SQLite —
`0002_evidence_status_engine.py` adds CHECK constraints via `ALTER`, which the
SQLite dialect rejects outright ("No support for ALTER of constraints in SQLite
dialect"). So the documented fallback previously had no way to get a schema, and
every request against a fresh checkout failed with `no such table: cases`.

This script closes that gap the same way `tests/conftest.py` does: straight
`Base.metadata.create_all`, no Alembic. That means:

  - It does **not** record an Alembic revision. Never point it at a database you
    intend to migrate afterwards.
  - Real persistence is PostgreSQL via `uv run alembic upgrade head`
    (`docs/decisions/decision-register.md` §4 item 003). This is a local
    convenience only.
  - It refuses to touch anything that is not SQLite, so it cannot be pointed at
    a Postgres instance by accident.

`create_all` only creates tables that are missing; it never alters an existing
one. So a dev database created before a model change keeps its old columns and
fails at insert time with something like "table answers has no column named
review_reason". Pass `--recreate` to drop and rebuild every table when that
happens. That destroys the local synthetic dev data, which is why it is opt-in.

Usage:

    uv run python scripts/init_dev_db.py
    uv run python scripts/init_dev_db.py --recreate    # drops local dev data
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, inspect  # noqa: E402

from app.config import settings  # noqa: E402
from app.db import Base  # noqa: E402
from app import models  # noqa: E402,F401  (import registers every table on Base)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Drop every table first. Destroys local synthetic dev data.",
    )
    args = parser.parse_args()

    url = settings.database_url

    if not url.startswith("sqlite"):
        print(
            f"Refusing to run: database_url is {url!r}, which is not SQLite.\n"
            "This script is a local SQLite convenience only. For PostgreSQL use\n"
            "  uv run alembic upgrade head",
            file=sys.stderr,
        )
        return 2

    engine = create_engine(url)

    if args.recreate:
        print(f"Dropping every table in {url} …")
        Base.metadata.drop_all(engine)

    Base.metadata.create_all(engine)

    tables = sorted(inspect(engine).get_table_names())
    print(f"Created or verified {len(tables)} tables in {url}:")
    for name in tables:
        print(f"  - {name}")

    # create_all cannot add a column to a table that already exists, so a dev
    # database from an older model revision looks fine here and only fails on
    # insert. Check the columns that arrived with the most recent migrations.
    drift = _schema_drift(engine)
    if drift:
        print("\nSchema drift detected — this dev database predates the models:")
        for line in drift:
            print(f"  - {line}")
        print("\nRun again with --recreate to rebuild it (local dev data is lost).")
        engine.dispose()
        return 1

    print(
        "\nDevelopment schema only — no Alembic revision was stamped.\n"
        "Synthetic data only (AGENTS.md §3.1)."
    )
    engine.dispose()
    return 0


def _schema_drift(engine) -> list[str]:
    """Report model columns missing from the live SQLite schema."""
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    problems: list[str] = []

    for table in Base.metadata.sorted_tables:
        if table.name not in existing:
            problems.append(f"{table.name}: table missing")
            continue
        live = {col["name"] for col in inspector.get_columns(table.name)}
        missing = [c.name for c in table.columns if c.name not in live]
        if missing:
            problems.append(f"{table.name}: missing column(s) {', '.join(sorted(missing))}")

    return problems


if __name__ == "__main__":
    raise SystemExit(main())
