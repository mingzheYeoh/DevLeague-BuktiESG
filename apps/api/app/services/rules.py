"""Deterministic evidence-status rule engine — STUB for this slice.

AGENTS.md §3.2: evidence_status and status_findings must be computed by a
deterministic rule engine from validated evidence, never set from AI output.
The real rule set (Main Spec §6, RULING-02's precedence rules, C-15) is the
COO's AI/evidence-matching pipeline's job in a later slice.

This slice has no evidence-matching pipeline at all. Every question created
in this slice has zero evidence_links, so the only deterministic answer this
engine can honestly give is MISSING. This function exists so that "always
MISSING" is one visible, named rule instead of a hand-waved default, and so
that a later slice replaces this one function, not scattered defaults.
"""

from __future__ import annotations


def compute_evidence_status(evidence_link_count: int) -> str:
    """Return the deterministic evidence status for a question.

    Stub rule for this slice only: no evidence-matching pipeline exists yet,
    so any question with zero linked evidence is MISSING. This is NOT the
    full Main Spec precedence rule set (RULING-02) — do not extend this
    function to guess at partial/verified logic; that belongs to the COO's
    evidence-matching slice.
    """
    if evidence_link_count == 0:
        return "MISSING"
    # Deliberately not implemented further in this slice.
    return "NEEDS_MANUAL_REVIEW"
