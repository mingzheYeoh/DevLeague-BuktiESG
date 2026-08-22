# BuktiESG API (`apps/api`)

FastAPI backend — Phase 1, First Vertical Slice only:

```
Create Case -> upload one questionnaire -> identify questions
            -> persist a SUBMISSION action -> persist/reload
```

Scope is deliberately narrow. This is **not** the full Main Spec backend — no AI
pipeline, no evidence matching, no exports, no jobs/queue. See
`docs/decisions/GATE-P0-APPROVAL.md` and `docs/spec/README-Team-Specs.md` (First
Vertical Slice) for the authorization and scope boundary.

## Stack

Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PostgreSQL (via
`psycopg`), `uv` for dependency management. See `docs/decisions/decision-register.md`
§4 (items 001, 004, 005, 011).

## Setup

```bash
cd apps/api
uv sync
```

## Configuration

Set `DATABASE_URL` (e.g. `postgresql+psycopg://user:pass@localhost:5432/buktiesg`).
If unset, the app defaults to a local SQLite file for ad-hoc manual runs only —
**never use SQLite for real persistence**; it exists so the app can boot without a
live Postgres instance during development. Tests use an isolated in-memory SQLite
database (see `tests/conftest.py`), never the dev database.

## Run

```bash
uv run uvicorn app.main:app --reload
```

## Migrations

```bash
uv run alembic upgrade head
```

Enums are modelled as `TEXT` + `CHECK` constraints, not native PostgreSQL `ENUM`
types, per `RULING-01` (`docs/decisions/decision-register.md`).

## Tests

```bash
uv run pytest
```
