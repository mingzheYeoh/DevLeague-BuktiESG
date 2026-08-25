"""Fail the build when a router reaches past the isolation chokepoint.

Two patterns, and the second is the one that earns this file:

  * `db.get(Case` in a router - someone wrote the query by hand again.
  * `case_id: str` in a router signature - a function that accepts the
    unverified identifier. That is precisely how `_question_in_case` came to
    guard a child resource against a case nobody had authenticated, and one
    grep would have found it years before a reviewer did.

Using a test to police a source pattern is unusual and worth the awkwardness
here: application-layer isolation was chosen over row-level security, and its
one weakness is that a forgotten filter returns extra rows instead of an error.
Nothing else in the suite turns that into a red build.
"""

from __future__ import annotations

import pathlib
import re

ROUTERS = pathlib.Path(__file__).resolve().parents[1] / "app" / "routers"

_RAW_CASE_LOAD = re.compile(r"db\.get\(\s*Case\b")
_UNVERIFIED_CASE_ID = re.compile(r"case_id:\s*str")

#: `auth.py` has no case-rooted endpoints. Nothing else is exempt.
_EXEMPT = {"__init__.py", "auth.py"}


def _router_files():
    return [p for p in ROUTERS.glob("*.py") if p.name not in _EXEMPT]


def test_no_router_loads_a_case_directly():
    offenders = []
    for path in _router_files():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _RAW_CASE_LOAD.search(line):
                offenders.append(f"{path.name}:{number}: {line.strip()}")
    assert not offenders, (
        "A router loaded a Case directly, bypassing the organization check.\n"
        + "\n".join(offenders)
        + "\n\nUse `case: Case = Depends(require_case)` instead."
    )


def test_no_router_accepts_an_unverified_case_id():
    offenders = []
    for path in _router_files():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _UNVERIFIED_CASE_ID.search(line):
                offenders.append(f"{path.name}:{number}: {line.strip()}")
    assert not offenders, (
        "A router function still accepts a raw case_id: str. An unverified "
        "identifier in a signature is how an authorization check gets skipped.\n"
        + "\n".join(offenders)
        + "\n\nTake `case: Case = Depends(require_case)` and use `case.id`."
    )
