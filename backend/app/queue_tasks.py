"""Vercel Queue subscriber for the existing database extraction jobs."""

from __future__ import annotations

import asyncio

from vercel.queue import subscribe

from app.config import settings
from app.db import SessionLocal
from app.services import jobs


def _run(job_id: str) -> None:
    db = SessionLocal()
    try:
        jobs.run_extraction_jobs(db, job_id=job_id, limit=1)
    finally:
        db.close()


@subscribe(topic="extract-values", max_concurrency=1)
async def extract_values(message: dict[str, str]) -> None:
    if not settings.openrouter_api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required for extraction")
    await asyncio.to_thread(_run, message["job_id"])
