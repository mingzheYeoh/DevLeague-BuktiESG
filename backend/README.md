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

## Database

PostgreSQL 16, from the repository root:

```bash
docker compose up -d          # postgres:16 on 127.0.0.1:5432
cd backend
cp .env.example .env          # DATABASE_URL, already pointing at that container
uv run alembic upgrade head
```

`.env.example` uses `127.0.0.1` rather than `localhost` on purpose: Compose binds
the port to the IPv4 loopback only, and on Windows `localhost` resolves to `::1`
first, so a `localhost` URL stalls until that attempt times out.

The data lives in the named volume `buktiesg-postgres-data`, not in the
container, so `docker compose down` and a rebuild lose nothing. `docker compose
down -v` does delete it.

### The SQLite fallback

With `DATABASE_URL` unset, `app/config.py` falls back to a local SQLite file so
the app can boot without a live database. That is for emergencies. **It is not a
supported way to run this application**, and the difference is not cosmetic:

- SQLite does not enforce foreign keys unless `PRAGMA foreign_keys=ON` is set per
  connection. A cascade-ordering bug that Postgres rejects outright can pass
  unnoticed on SQLite — one did, and `tests/test_schema_integrity.py` exists
  because of it.
- `claim_next_job` has no row-level locking on SQLite (`app/services/jobs.py`
  documents exactly how it degrades). Never run more than one worker against it.
- The Alembic migrations are written for PostgreSQL and **cannot run on SQLite** —
  `0002_evidence_status_engine.py` adds CHECK constraints via `ALTER`, which the
  SQLite dialect rejects. Its schema comes from `scripts/init_dev_db.py`
  (`create_all`) instead, which stamps no Alembic revision:

```bash
uv run python scripts/init_dev_db.py              # create missing tables
uv run python scripts/init_dev_db.py --recreate   # rebuild; drops local dev data
```

The test suite is the one place SQLite is used deliberately: `tests/conftest.py`
builds an isolated in-memory database per test, with `PRAGMA foreign_keys=ON`, so
the suite runs on a fresh clone without Docker. It never touches a dev database.

### Reclaiming stored bytes

`var/storage` has no garbage collector. `delete_case_tree` and `delete_file`
run only on a successful delete, so anything that fails between writing a blob
and committing its row leaves bytes nothing references — and nothing notices.
This repository reached 1,252 orphan directories and 8.8 MB in one development
cycle, most of it from a test suite that wrote into the real storage root
(`tests/conftest.py` now isolates it per test).

```bash
uv run python scripts/reclaim_storage.py            # report only
uv run python scripts/reclaim_storage.py --delete   # remove the orphans
```

The reconciliation is one-directional. A blob with no row is garbage. A row
with no blob is evidence that cannot be produced — reported for a human, never
deleted, because losing the record that evidence was cited is worse than the
inconsistency.

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
