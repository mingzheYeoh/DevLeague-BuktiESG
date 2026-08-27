"""Application configuration.

Read from the repository-root `.env` - the same file docker-compose.yml reads,
so the database password is written once rather than in two files that could
disagree. The path is anchored to this module, not to the working directory;
see `_REPO_ROOT` for what that used to cost.

(This docstring previously said "no provider/AI settings live here". A
`deepseek_api_key` has lived here since extraction was added.)
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> backend/app -> backend -> the repository root, where
# `.env` sits beside docker-compose.yml so that both readers read one file.
#
# Anchored, not relative. `env_file=".env"` is resolved against the *current
# working directory*, so this only ever loaded when the process was launched
# from `backend/`. Started from anywhere else it read nothing, took the SQLite
# default below, and came up normally against an empty local file - no error,
# no warning, just the wrong database.
_REPO_ROOT = Path(__file__).resolve().parents[2]

# Fixed by docker-compose.yml: POSTGRES_USER, POSTGRES_DB, and a port published
# on the IPv4 loopback only. Change them there and change them here.
#
# 127.0.0.1 rather than `localhost` deliberately - on Windows `localhost`
# resolves to ::1 first, which nothing is listening on, and the connection
# stalls until that attempt times out before retrying IPv4.
_COMPOSE_DATABASE_URL = "postgresql+psycopg://buktiesg:{password}@127.0.0.1:5432/buktiesg"

# Per docs/decisions/decision-register.md §4 item 003: PostgreSQL 16. This
# exists ONLY so the app can boot without a live Postgres during ad-hoc
# development. Never used for real persistence and never used by the test
# suite (see tests/conftest.py, which uses its own isolated in-memory SQLite
# and is explicitly called out as a test-only substitution).
_SQLITE_FALLBACK = "sqlite:///./buktiesg_dev.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_REPO_ROOT / ".env", extra="ignore")

    # The one place the local database password is written. docker-compose.yml
    # reads the same variable from the same file, so there is no second copy
    # to drift out of step - `database_url` is built from it below. It used to
    # be written twice, and the symptom of disagreement was an authentication
    # failure that named neither file.
    postgres_password: str | None = None

    # Normally left unset and derived from `postgres_password`. Set it to point
    # at a database that is not the Compose one; CI's migration job does
    # exactly that, and an OS environment variable beats the file.
    database_url: str = ""

    # Absence is a supported configuration, not a misconfiguration. Without a
    # key `build_extractor` returns NullExtractor and the system behaves
    # exactly as it did before extraction existed, which is what makes
    # introducing a model reversible and lets CI run the path with no bill.
    #
    # Read from the environment or `.env`, never committed: `.gitignore`
    # covers `.env` and `.env.example` carries the name only.
    deepseek_api_key: str | None = None

    app_name: str = "BuktiESG API"

    # 10 MB, arbitrary slice-scope limit for the demo upload path. Not the
    # final Main Spec file-limit decision (Phase 0 "Confirm file limits").
    max_upload_bytes: int = 10 * 1024 * 1024

    # Local dev origins only (the Next.js dev server in `frontend/`). Not a
    # production CORS policy decision.
    #
    # This list must stay explicit and must never become ["*"]: the API now
    # sets `allow_credentials=True` so that the browser will send the session
    # cookie, and a browser refuses a wildcard origin in a credentialed
    # exchange. Every entry here is an origin permitted to act as a signed-in
    # user, so adding one is an authorization decision.
    cors_allow_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # How long a session stays valid without re-authenticating. Fourteen days
    # is a working fortnight either side of a weekend: long enough that a
    # reviewer is not signed out mid-questionnaire, short enough that a
    # forgotten laptop stops being a credential within a sprint.
    session_ttl_hours: int = 24 * 14

    # `Secure` is dropped only for local HTTP development. Any deployment that
    # holds real data serves HTTPS, where this must be True - a session cookie
    # sent in clear text is the whole authentication system given away.
    cookie_secure: bool = True

    @model_validator(mode="after")
    def _derive_database_url(self) -> "Settings":
        if not self.database_url:
            self.database_url = (
                # Escaped because the URL is built by interpolation: an
                # unescaped `@` or `/` in the password moves the host boundary
                # and the driver reports a hostname nobody configured.
                _COMPOSE_DATABASE_URL.format(password=quote(self.postgres_password, safe=""))
                if self.postgres_password
                else _SQLITE_FALLBACK
            )
        return self


settings = Settings()
