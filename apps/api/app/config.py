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

    app_name: str = "BuktiESG API"

    # 10 MB, arbitrary slice-scope limit for the demo upload path. Not the
    # final Main Spec file-limit decision (Phase 0 "Confirm file limits").
    max_upload_bytes: int = 10 * 1024 * 1024

    # Local dev origins only (apps/web's Next.js dev server). Not a
    # production CORS policy decision — BLOCKER-07 already restricts this
    # slice to local, non-public operation.
    cors_allow_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


settings = Settings()
