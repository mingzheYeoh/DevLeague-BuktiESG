"""Application configuration.

Scope note: this is Phase 1 / First Vertical Slice configuration only. No
provider/AI settings live here — the AI pipeline is out of scope for this
slice (see docs/spec/README-Team-Specs.md, "First Vertical Slice").
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Per docs/decisions/decision-register.md §4 item 003: PostgreSQL 16.
    # Falls back to a local SQLite file ONLY so the app can boot without a
    # live Postgres during ad-hoc development. Never used for real
    # persistence and never used by the test suite (see tests/conftest.py,
    # which uses its own isolated in-memory SQLite and is explicitly called
    # out as a test-only substitution).
    database_url: str = "sqlite:///./buktiesg_dev.db"

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


settings = Settings()
