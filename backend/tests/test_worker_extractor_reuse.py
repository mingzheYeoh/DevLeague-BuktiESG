"""The worker builds its extractor once, not once per poll.

`worker.py` had no tests at all, and this is the failure that showed why.

`build_extractor` logs a warning when a provider key is set — the one line
that distinguishes "chunk text is leaving the machine" from "extraction is
off". `run_once` called `run_extraction_jobs` without an extractor, so one was
built on every poll, and the warning was re-emitted every two seconds forever.
That is precisely the "a warning on every upload would train people to ignore
warnings" failure that `build_extractor`'s own docstring says it avoids.

Nothing caught it. 209 tests passed, CI was green, and the unit test for
`build_extractor` calls it exactly once and sees exactly one warning. The
defect only exists across repeated calls, which only happen in the poll loop,
which nothing exercised. It took running the worker for six seconds and
reading the log.
"""

from __future__ import annotations

import worker


def test_run_once_uses_the_extractor_it_is_given(monkeypatch):
    """The wiring that broke: the extractor must travel down, not be rebuilt.

    Asserted by identity. A test that only checked "an extractor was passed"
    would pass against a `run_once` that built its own and handed that over,
    which is the bug.
    """
    sentinel = object()
    seen = {}

    def _fake_run_extraction_jobs(db, *, limit=10, extractor=None):
        seen["extractor"] = extractor
        return True  # claim to have run something, so run_once returns early

    monkeypatch.setattr(worker.jobs, "run_extraction_jobs", _fake_run_extraction_jobs)
    monkeypatch.setattr(worker, "SessionLocal", lambda: _NullSession())

    assert worker.run_once(sentinel) is True
    assert seen["extractor"] is sentinel


def test_run_once_without_one_lets_the_job_layer_decide(monkeypatch):
    """`worker.py --once` passes nothing, and that must stay valid.

    A single run has no loop to repeat a warning in, so building the extractor
    inside `run_extraction_jobs` is the right behaviour there. Pinning it so a
    future change that makes `extractor` required does not silently break the
    one-shot entry point.
    """
    seen = {}

    def _fake_run_extraction_jobs(db, *, limit=10, extractor=None):
        seen["extractor"] = extractor
        return True

    monkeypatch.setattr(worker.jobs, "run_extraction_jobs", _fake_run_extraction_jobs)
    monkeypatch.setattr(worker, "SessionLocal", lambda: _NullSession())

    assert worker.run_once() is True
    assert seen["extractor"] is None


class _NullSession:
    """Enough of a Session for `run_once`'s try/finally. It never reaches a
    query, because the patched `run_extraction_jobs` returns True first."""

    def close(self) -> None:
        pass
