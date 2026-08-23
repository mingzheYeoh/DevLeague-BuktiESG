# BuktiESG API (`backend/`)

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
cd backend
uv sync
```

## Configuration

Set `DATABASE_URL` (e.g. `postgresql+psycopg://user:pass@localhost:5432/buktiesg`).
If unset, the app defaults to a local SQLite file for ad-hoc manual runs only —
**never use SQLite for real persistence**; it exists so the app can boot without a
live Postgres instance during development. Tests use an isolated in-memory SQLite
database (see `tests/conftest.py`), never the dev database.

### Local SQLite schema

The Alembic migrations are written for PostgreSQL and **cannot run on SQLite** —
`0002_evidence_status_engine.py` adds CHECK constraints via `ALTER`, which the
SQLite dialect rejects. So `alembic upgrade head` against the SQLite fallback
fails, and without a schema every request dies with `no such table: cases`.

For the SQLite fallback, build the schema from the models instead:

```bash
uv run python scripts/init_dev_db.py              # create missing tables
uv run python scripts/init_dev_db.py --recreate   # rebuild; drops local dev data
```

It stamps no Alembic revision and refuses to run against anything but SQLite. It
also reports schema drift, which is what a dev database created before a model
change looks like (`create_all` never alters an existing table).

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

## HTTP surface

Every business route is under `/api/v1/cases`. `GET /health` is the only
unversioned route.

| Method | Path | Notes |
|---|---|---|
| GET | `/health` | Liveness only |
| POST | `/api/v1/cases` | 201, `CaseSummary` |
| GET | `/api/v1/cases` | List, most recently updated first. No pagination |
| GET | `/api/v1/cases/{case_id}` | `CaseSummary` |
| GET | `/api/v1/cases/{case_id}/readiness` | Server-computed readiness formula |
| POST | `/api/v1/cases/{case_id}/documents` | multipart `file` + `document_type`; parses/indexes synchronously; duplicate checksums return the existing row |
| GET | `/api/v1/cases/{case_id}/documents` | List |
| POST | `/api/v1/cases/{case_id}/documents/{id}/retry` | Only from `FAILED` / `NEEDS_MANUAL_REVIEW`, else 409 |
| GET | `/api/v1/cases/{case_id}/questions` | List, in questionnaire order |
| POST | `/api/v1/cases/{case_id}/questions/{id}/review` | The human verdict. Returns `AnswerRecord` |
| POST | `/api/v1/cases/{case_id}/actions` | Requires owner, next step and deadline |
| GET | `/api/v1/cases/{case_id}/actions` | List |
| POST | `/api/v1/cases/{case_id}/actions/{id}/status` | `COMPLETED` requires a note, and closure evidence when flagged |
| POST | `/api/v1/cases/{case_id}/evidence-links/{id}/invalidate` | Cascades: reopens closed Actions, recomputes evidence status |

Errors use `{"detail": {"error": {"code", "message", "details", "request_id"}}}`.
FastAPI's own request-validation failures use its default `{"detail": [...]}`
array instead, so a client has to handle both.

**Not implemented, and relied on by nothing:** no jobs endpoint (despite
`latest_job_id`), no evidence-link listing, no question detail (so draft answer
text is only ever returned by the review endpoint), no export endpoint, no
document download, no `priority_score`, and no `PATCH`/`DELETE` anywhere.

## Security posture

There is **no authentication and no authorisation** on this service, and CORS
is open to the local dev origins only. It is a local, single-tenant slice: do
not expose it beyond localhost, and do not put real personal data in it (see
`AGENTS.md` §3.1). Adding pagination and auth is a prerequisite for anything
beyond local use.

## Consumed by

`frontend/` — the Next.js workspace. Its client lives in `frontend/lib/api/`
and is written against this server's actual shapes.
