"""Fail the build when a router reaches past the isolation chokepoint.

Two patterns, and the second is the one that earns this file:

  * `db.get(Case` in a router - someone wrote the query by hand again.
  * A `case_id: str` parameter in a router function's signature - a function
    that accepts the unverified identifier. That is precisely how
    `_question_in_case` came to guard a child resource against a case nobody
    had authenticated, and one grep would have found it years before a
    reviewer did.

Using a test to police a source pattern is unusual and worth the awkwardness
here: application-layer isolation was chosen over row-level security, and its
one weakness is that a forgotten filter returns extra rows instead of an error.
Nothing else in the suite turns that into a red build.

The `case_id: str` check parses each router with `ast` and inspects only
function signatures, rather than scanning raw source lines for the text
`case_id: str`. A line scan cannot distinguish a live parameter from that same
text inside a comment or docstring explaining why a function no longer takes
one - which is a natural thing to write right next to the dependency that
replaced it, and previously meant writing that explanation tripped the rule
it was describing. `ast` does not retain comments at all, and a docstring is
just a `Constant` this check never looks at, so prose is structurally
invisible to it.

The `db.get(Case` check stays a line scan: it is looking for a call
expression, not a signature, and a line scan is the honest tool for that.

A third test ties `_EXEMPT` to a verifiable fact: an exempt module must not
declare a route whose path contains `{case_id}`. Today only `auth.py` is
exempt, and it has no case-rooted endpoints - but nothing enforced that
staying true until this test existed.
"""

from __future__ import annotations

import ast
import pathlib
import re

ROUTERS = pathlib.Path(__file__).resolve().parents[1] / "app" / "routers"

_RAW_CASE_LOAD = re.compile(r"db\.get\(\s*Case\b")

#: `auth.py` has no case-rooted endpoints. Nothing else is exempt.
_EXEMPT = {"__init__.py", "auth.py"}


def _router_files():
    return [p for p in ROUTERS.glob("*.py") if p.name not in _EXEMPT]


def _exempt_router_files():
    return [p for p in ROUTERS.glob("*.py") if p.name in _EXEMPT and p.name != "__init__.py"]


def _parse(path: pathlib.Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _functions(tree: ast.Module):
    """Every function def in the module, nested ones included."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node


def _accepts_unverified_case_id(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    params = [*func.args.posonlyargs, *func.args.args, *func.args.kwonlyargs]
    for param in params:
        if param.arg != "case_id":
            continue
        annotation = param.annotation
        if isinstance(annotation, ast.Name) and annotation.id == "str":
            return True
        if isinstance(annotation, ast.Constant) and annotation.value == "str":
            return True
    return False


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
        tree = _parse(path)
        for func in _functions(tree):
            if _accepts_unverified_case_id(func):
                offenders.append(f"{path.name}:{func.lineno}: {func.name}")
    assert not offenders, (
        "A router function still accepts a raw case_id: str. An unverified "
        "identifier in a signature is how an authorization check gets skipped.\n"
        + "\n".join(offenders)
        + "\n\nTake `case: Case = Depends(require_case)` and use `case.id`."
    )


def test_exempt_routers_have_no_case_rooted_routes():
    offenders = []
    for path in _exempt_router_files():
        tree = _parse(path)
        for func in _functions(tree):
            for decorator in func.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                for arg in decorator.args:
                    if (
                        isinstance(arg, ast.Constant)
                        and isinstance(arg.value, str)
                        and "{case_id}" in arg.value
                    ):
                        offenders.append(f"{path.name}:{decorator.lineno}: {arg.value}")
    assert not offenders, (
        "A case-rooted route ({case_id} in its path) appeared in a file the "
        "isolation guard above does not scan, because it is listed in "
        "_EXEMPT. Either move the endpoint to a scanned router, or remove "
        "the file from _EXEMPT so the guard actually checks it.\n"
        + "\n".join(offenders)
    )
