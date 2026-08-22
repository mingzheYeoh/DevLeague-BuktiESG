"""Deterministic evidence-status rule engine — MISSING/PARTIAL subset.

AGENTS.md §3.2: `evidence_status` must be computed by a deterministic rule
engine from validated evidence, never set from AI output. SPEC-AMD-005
defines the full four-step, seven-status precedence model (`CONFLICTING >
OUTDATED > PARTIAL > VERIFIED`, else `NEEDS_MANUAL_REVIEW`/`MISSING`) for the
Main Spec §6.2 rule engine.

This slice implements only the minimum honest subset of that model:

    no resolvable evidence candidate  -> MISSING
    a resolvable candidate exists     -> PARTIAL

`PARTIAL` is the only non-`MISSING` outcome reachable here because this
slice has no validation logic for full coverage, staleness, or conflict
detection between multiple sources (`VERIFIED`, `OUTDATED`, `CONFLICTING`,
`NEEDS_MANUAL_REVIEW` are simply never computed yet). `NOT_APPLICABLE`
remains human-controlled only (SPEC-AMD-005 step 1) and is never touched by
this function. Do not extend this function to guess at the remaining
statuses — that is a later slice's job, replacing this one function rather
than scattering ad-hoc status logic elsewhere.

The caller (`app/routers/documents.py`) is responsible for ensuring
`evidence_link_count` only counts links whose source location the SERVER
resolved from persisted `document_chunks` — never a location an AI pipeline
claimed directly (AGENTS.md §3.3).
"""

from __future__ import annotations


def compute_evidence_status(evidence_link_count: int) -> str:
    """Return the deterministic evidence status for a question, for this
    slice's MISSING/PARTIAL-only subset of SPEC-AMD-005.

    `evidence_link_count` must be the count of server-resolved evidence_links
    rows for the question (any `link_status`), not an AI-reported count.
    """
    if evidence_link_count == 0:
        return "MISSING"
    return "PARTIAL"
