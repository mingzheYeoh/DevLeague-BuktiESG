"""Notify the hosted queue after an evidence upload has committed."""

from __future__ import annotations

import logging
import os

from sqlalchemy.orm import Session
from vercel import queue

from app.config import settings
from app.models import ProcessingJob

logger = logging.getLogger(__name__)


async def notify_queued_extraction(db: Session, document_id: str) -> None:
    # Local development uses worker.py. Never consume a job with NullExtractor
    # just because a Vercel deployment has no provider credential yet.
    if not os.getenv("VERCEL") or not settings.openrouter_api_key:
        return

    job = (
        db.query(ProcessingJob)
        .filter(
            ProcessingJob.document_id == document_id,
            ProcessingJob.job_type == "EXTRACT_VALUES",
            ProcessingJob.status == "QUEUED",
        )
        .order_by(ProcessingJob.created_at.desc())
        .first()
    )
    if job is None:
        return

    try:
        await queue.send("extract-values", {"job_id": job.id}, idempotency_key=job.id)
    except Exception:
        # The stored document and DB job remain intact. A duplicate upload can
        # republish this queued job after a transient queue failure.
        logger.exception("could not publish extraction job %s", job.id)
