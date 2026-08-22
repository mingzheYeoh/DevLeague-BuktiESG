"""Provider seam for a future LLM-backed step (BLOCKER-08).

Nothing in the current `analyze_question()` keyword-matching path calls a
provider — matching is pure keyword logic and needs no model call. This module
exists so a later LLM-based analysis step can plug in behind `LLMProvider`
without moving the purity boundary: a provider only ever receives plain data
(strings) and returns plain data, never a DB session, credential, or network
handle owned by this package. Wiring the credential/HTTP client itself is the
CTO orchestration layer's job (BLOCKER-04), not this package's.

`FixtureProvider` is the deterministic stand-in used in CI (per BLOCKER-08:
"Never use the live provider in CI") and as the documented outage fallback.
"""

from __future__ import annotations

import hashlib
from typing import Protocol


class LLMProvider(Protocol):
    """Minimal interface a future LLM-backed analysis step would call through.

    Deliberately narrow: takes a prompt string, returns a completion string.
    No method here accepts or returns a database session, HTTP client, or
    credential — an implementation that needs one gets it injected by the
    caller (the CTO orchestration layer), never constructed inside this
    package.
    """

    def complete(self, prompt: str) -> str: ...


class FixtureProvider:
    """Deterministic, offline stand-in for a live LLM provider.

    Returns a stable, content-derived string with no network call and no
    randomness — safe for CI (BLOCKER-08) and safe as a live-provider outage
    fallback. Not used by the current keyword-matching `analyze_question()`;
    provided so a future LLM step has somewhere to plug in without violating
    the pure-function boundary.
    """

    def complete(self, prompt: str) -> str:
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]
        return f"[fixture-response:{digest}]"
