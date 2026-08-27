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

# Statuses a Case may be deleted from. Not a DB-column allow-list — it gates
# DELETE /cases/{id}, so adding a value here needs no migration.
#
# Deleting a Case destroys the record of what evidence was reviewed and by
# whom, which is the thing this product exists to keep. So it is a two-step
# action for any Case that has been worked on: archive it, then delete it.
# DRAFT is exempt because it has nothing to destroy yet; ARCHIVED is exempt
# because reaching it was already a deliberate human decision to retire the
# Case.
CASE_DELETABLE_FROM = ("DRAFT", "ARCHIVED")

DOCUMENT_TYPE = (
    "QUESTIONNAIRE",
    "UTILITY_BILL",
    "POLICY",
    "HR_DATA",
    "WASTE_RECORD",
    "SAFETY_RECORD",
    "OTHER",
)

ORG_ROLE = ("ADMIN", "MEMBER")

EMAIL_TOKEN_PURPOSE = ("VERIFY", "RESET")

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

# Processing states a Document may be deleted from. Like CASE_DELETABLE_FROM
# this is not a DB-column allow-list - it gates DELETE
# /cases/{id}/documents/{id} only, so widening it needs no migration.
#
# Narrow on purpose. A document that parsed has chunks, and those chunks carry
# evidence links that a reviewer may have accepted; deleting it would destroy
# citations and review decisions, which is the thing this product exists to
# keep. A document that failed to parse has neither - nothing was extracted, so
# nothing cites it - and it is the only state with no other way out: `/retry`
# re-runs the same parser over the same bytes.
DOCUMENT_DELETABLE_FROM = ("NEEDS_MANUAL_REVIEW",)

EVIDENCE_LINK_STATUS = ("CANDIDATE", "ACCEPTED", "REJECTED", "INVALIDATED")

EVIDENCE_CREATED_BY = ("SYSTEM", "USER")

# Human Review actions (Main Spec §17 Phase 5). Not a DB-column allow-list
# (no table column stores the action verb itself — it drives which
# Answer fields get written), so this is a plain tuple, not a CHECK
# constraint source. Adding a verb here therefore needs no migration.
#
# REOPEN withdraws a review decision and hands evidence_status back to the rule
# engine. RULING-02 says only a human action may "set or clear"
# evidence_status == NOT_APPLICABLE; the four original verbs could only set it,
# so NOT_APPLICABLE was a one-way door with no way back. REOPEN is the "clear"
# half the ruling already assumed existed.
REVIEW_ACTION = ("ACCEPT", "EDIT", "REJECT", "NOT_APPLICABLE", "REOPEN")

ACTION_TYPE = ("SUBMISSION", "IMPROVEMENT")

ACTION_STATUS = ("TODO", "IN_PROGRESS", "BLOCKED", "NEEDS_REVIEW", "COMPLETED")

# JobType / JobStatus — SPEC-AMD-001, CTO-RULINGS.md RULING-01 (amended).
# EXTRACT_VALUES is the first job type that genuinely cannot run inline.
# Measured against deepseek-v4-pro, two to three chunks take 12-22 seconds,
# so a 21-document case at 175 chunks would add roughly three minutes to an
# upload. Every other job type has always been executed synchronously.
JOB_TYPE = (
    "DOCUMENT_PARSE",
    "DOCUMENT_INDEX",
    "QUESTION_ANALYZE",
    "EXTRACT_VALUES",
    "EXPORT_RENDER",
)

# Terminal states per RULING-01: SUCCEEDED, FAILED, CANCELLED. Valid
# transitions: QUEUED -> RUNNING -> {SUCCEEDED, FAILED}; QUEUED -> CANCELLED;
# RUNNING -> CANCELLED.
JOB_STATUS = ("QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED")


def check_in(column: str, values: tuple[str, ...]) -> str:
    """Render a SQL CHECK-constraint expression for an allow-list column."""
    quoted = ", ".join(f"'{v}'" for v in values)
    return f"{column} IN ({quoted})"
