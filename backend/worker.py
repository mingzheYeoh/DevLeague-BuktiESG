"""Out-of-band polling worker — Main Spec §17 Phase 2 item 3.

The MVP does not use Celery, Kafka, Redis, Kubernetes, or microservices
(Main Spec; decision-register.md §4 item 017, CTO authority). This process
polls the `processing_jobs` database table instead, claiming work with
`SELECT ... FOR UPDATE SKIP LOCKED` on PostgreSQL (see
`app/services/jobs.claim_next_job()` for the query and its documented
SQLite-dev-only fallback — do not run more than one instance of this
process against a SQLite database).

**Why this exists alongside the in-process execution in
`app/routers/documents.py`**: the upload/retry request handlers already run
a job to completion synchronously before the HTTP response is returned
(acceptable for this phase per Main Spec §17 — "a separate worker process
or an in-process background task"). This process exists for the case that
matters despite that: a job left QUEUED/RUNNING because the handling
request process crashed or was killed mid-job. Run it as a second process
next to the API (e.g. `python worker.py`) in any environment where that
matters; it is not required for local dev or the test suite, both of which
only ever exercise the in-process path.

Usage:
    python worker.py                  # poll forever
    python worker.py --once           # claim and run at most one job, then exit
"""

from __future__ import annotations

import sys
import time

from app.db import SessionLocal
from app.services import jobs

_POLL_INTERVAL_SECONDS = 2.0


def run_once() -> bool:
    """Claim and run at most one job. Returns True if a job was found."""
    db = SessionLocal()
    try:
        job = jobs.claim_next_job(db)
        if job is None:
            return False
        jobs.run_document_job(db, job)
        db.commit()
        return True
    finally:
        db.close()


def poll_forever() -> None:
    print("worker: polling processing_jobs (Ctrl+C to stop)...", flush=True)
    while True:
        try:
            found = run_once()
        except Exception as exc:  # noqa: BLE001 — a poll-loop bug must not kill the loop
            print(f"worker: unexpected error while polling: {exc}", flush=True)
            found = False
        if not found:
            time.sleep(_POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    if "--once" in sys.argv:
        ran = run_once()
        print(f"worker: ran one job" if ran else "worker: no job was queued", flush=True)
    else:
        poll_forever()
