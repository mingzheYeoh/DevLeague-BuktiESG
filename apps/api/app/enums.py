"""Shared enum value tuples.

Values come from docs/spec/Shared-Integration-Contract.md §3 and the
amendments in docs/spec/AMENDMENTS.md (SPEC-AMD-006 / RULING-03: three-
dimension model, ``AI_SUGGESTED`` removed from EvidenceStatus and replaced by
``DraftProvenance``).

Per RULING-01 / decision-register.md §4: no native PostgreSQL ENUM type.
These tuples back plain ``TEXT`` columns plus a generated ``CHECK``
constraint (see migrations/versions/0001_initial.py), so adding a value is a
migration, not a type change.
"""

from __future__ import annotations

CASE_STATUS = (
    "DRAFT",
    "PROCESSING",
    "IN_REVIEW",
    "READY",
    "EXPORTED",
    "ARCHIVED",
)

DOCUMENT_TYPE = (
    "QUESTIONNAIRE",
    "UTILITY_BILL",
    "POLICY",
    "HR_DATA",
    "WASTE_RECORD",
    "SAFETY_RECORD",
    "OTHER",
)

DOCUMENT_PROCESSING_STATUS = (
    "UPLOADED",
    "PARSING",
    "PARSED",
    "INDEXED",
    "FAILED",
    "NEEDS_MANUAL_REVIEW",
)

PILLAR = ("E", "S", "G", "UNCATEGORIZED")

# EvidenceStatus — 7 values. AI_SUGGESTED removed per SPEC-AMD-006 / RULING-03.
EVIDENCE_STATUS = (
    "VERIFIED",
    "PARTIAL",
    "OUTDATED",
    "CONFLICTING",
    "MISSING",
    "NOT_APPLICABLE",
    "NEEDS_MANUAL_REVIEW",
)

REVIEW_STATUS = (
    "UNREVIEWED",
    "HUMAN_CONFIRMED",
    "REJECTED",
    "NEEDS_REVISION",
)

# DraftProvenance — SPEC-AMD-006 / RULING-03.
DRAFT_PROVENANCE = (
    "NONE",
    "AI_GENERATED",
    "AI_ASSISTED_EDIT",
    "USER_ENTERED",
)

EVIDENCE_LINK_STATUS = ("CANDIDATE", "ACCEPTED", "REJECTED", "INVALIDATED")

EVIDENCE_CREATED_BY = ("SYSTEM", "USER")

# Human Review actions (Main Spec §17 Phase 5). Not a DB-column allow-list
# (no table column stores the action verb itself — it drives which
# Answer fields get written), so this is a plain tuple, not a CHECK
# constraint source.
REVIEW_ACTION = ("ACCEPT", "EDIT", "REJECT", "NOT_APPLICABLE")

ACTION_TYPE = ("SUBMISSION", "IMPROVEMENT")

ACTION_STATUS = ("TODO", "IN_PROGRESS", "BLOCKED", "NEEDS_REVIEW", "COMPLETED")

# JobType / JobStatus — SPEC-AMD-001, CTO-RULINGS.md RULING-01 (amended).
JOB_TYPE = ("DOCUMENT_PARSE", "DOCUMENT_INDEX", "QUESTION_ANALYZE", "EXPORT_RENDER")

# Terminal states per RULING-01: SUCCEEDED, FAILED, CANCELLED. Valid
# transitions: QUEUED -> RUNNING -> {SUCCEEDED, FAILED}; QUEUED -> CANCELLED;
# RUNNING -> CANCELLED.
JOB_STATUS = ("QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED")


def check_in(column: str, values: tuple[str, ...]) -> str:
    """Render a SQL CHECK-constraint expression for an allow-list column."""
    quoted = ", ".join(f"'{v}'" for v in values)
    return f"{column} IN ({quoted})"
