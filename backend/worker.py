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


def run_once(extractor=None) -> bool:
    """Claim and run at most one job. Returns True if a job was found.

    `extractor` is built once by `poll_forever` and passed down, rather than
    left for `run_extraction_jobs` to build per call. Building it per call
    re-emits its "chunk text will be sent to api.deepseek.com" warning on
    every poll - one line every two seconds, forever - which is precisely the
    "train people to ignore warnings" failure that `build_extractor`'s own
    docstring says it is avoiding. It is the one line that distinguishes
    "extraction is running" from "extraction is off", so it has to stay
    readable.
    """
    db = SessionLocal()
    try:
        # Extraction first, and by its own query rather than through
        # `claim_next_job`. That claim is written for parse/index jobs and
        # calls `run_document_job`, which would not know what to do with an
        # EXTRACT_VALUES row. Keeping the two paths apart is smaller than
        # generalising a claim that has exactly one other caller.
        if jobs.run_extraction_jobs(db, limit=1, extractor=extractor):
            return True

        job = jobs.claim_next_job(db)
        if job is None:
            return False
        if job.job_type == "EXTRACT_VALUES":
            # Claimed by the generic path in a race with the branch above.
            # Hand it back rather than passing it to a runner that cannot
            # execute it: the next poll picks it up through the right door.
            job.status = "QUEUED"
            job.started_at = None
            db.commit()
            return True
        jobs.run_document_job(db, job)
        db.commit()
        return True
    finally:
        db.close()


def poll_forever() -> None:
    from app.config import settings
    from app.services.extractor import build_extractor

    # Once, here, so the provider warning is emitted once per worker start.
    extractor = build_extractor(settings)

    print("worker: polling processing_jobs (Ctrl+C to stop)...", flush=True)
    while True:
        try:
            found = run_once(extractor)
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
