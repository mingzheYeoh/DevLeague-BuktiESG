"""Data models for the AI pipeline core.

These models are plain data containers (pydantic `BaseModel`, `extra="forbid"` —
i.e. `additionalProperties: false`). None of them import a database/session module,
an HTTP client, or credentials. That is a deliberate, enforced boundary: see
AGENTS.md §3.2/3.3 and docs/decisions/CTO-RULINGS.md BLOCKER-04.

`AnalysisResult` mirrors docs/spec/Shared-Integration-Contract.md §8 exactly by field
name. Fields out of scope for the First Vertical Slice (SEDG mapping, priority
scoring, conflict detection, follow-up suggestion) are typed as optional and left
`None` rather than fabricated — see README.md "Scope of this slice".
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

_STRICT = ConfigDict(extra="forbid")


# --------------------------------------------------------------------------- #
# parse_document() output
# --------------------------------------------------------------------------- #


class ParsedQuestion(BaseModel):
    """One row extracted from an uploaded questionnaire.

    `question_order` is assigned deterministically from workbook/sheet/row
    traversal order at parse time (SPEC-AMD-007) — never re-derived later from
    `external_question_id` or any other display string.
    """

    model_config = _STRICT

    external_question_id: str
    question_text: str
    section: Optional[str] = None
    is_required: bool
    source_location: str  # e.g. "Sheet1!B7" — display/reference only, not a DB pointer
    question_order: int = Field(ge=0)


class ParsedQuestionnaire(BaseModel):
    model_config = _STRICT

    filename: str
    questions: list[ParsedQuestion]


# --------------------------------------------------------------------------- #
# analyze_question() input
# --------------------------------------------------------------------------- #


class DocumentChunk(BaseModel):
    """A chunk of evidence document text supplied by the caller (server-owned
    persistence resolves `chunk_id` back to a source location; this package never
    sees or returns a location).
    """

    model_config = _STRICT

    chunk_id: str
    text: str


# --------------------------------------------------------------------------- #
# analyze_question() output — Shared-Integration-Contract.md §8
# --------------------------------------------------------------------------- #


class CandidateEvidence(BaseModel):
    model_config = _STRICT

    chunk_id: str
    claim_supported: str
    quoted_excerpt: str
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    scope_description: Optional[str] = None
    value: Optional[str] = None
    unit: Optional[str] = None


class MappingResult(BaseModel):
    model_config = _STRICT

    pillar: Optional[str] = None
    sedg_topic_code: Optional[str] = None
    sedg_disclosure_code: Optional[str] = None
    rationale: Optional[str] = None


class PriorityRecommendationRationale(BaseModel):
    model_config = _STRICT

    impact: Optional[str] = None
    urgency: Optional[str] = None
    evidence_gap: Optional[str] = None
    feasibility: Optional[str] = None


class PriorityRecommendation(BaseModel):
    model_config = _STRICT

    impact: int = Field(ge=0, le=5)
    urgency: int = Field(ge=0, le=5)
    evidence_gap: int = Field(ge=0, le=5)
    feasibility: int = Field(ge=0, le=5)
    rationale: PriorityRecommendationRationale


class RunMetadata(BaseModel):
    model_config = _STRICT

    provider: str
    model: str
    prompt_version: str
    input_hash: str
    source_ids: list[str]
    latency_ms: int
    estimated_cost: float


class AnalysisResult(BaseModel):
    """The object `analyze_question()` returns. Validated and persisted by the
    backend; never accepted as final review state (Contract §8).

    Forbidden fields (never present, enforced structurally by `extra="forbid"`
    plus simply never being declared here): `review_status`,
    `final_compliance_status`, `audit_passed`, `certified`, `conflict_winner`,
    `customer_submission_approved`, `evidence_status`, `status_findings`.
    """

    model_config = _STRICT

    schema_version: str = "1.0.0"
    question_id: str
    draft_answer: Optional[str] = None
    mapping: Optional[MappingResult] = None
    candidate_evidence: list[CandidateEvidence]
    missing_elements: list[str]
    possible_conflicts: list[str]
    suggested_follow_up: Optional[str] = None
    priority_recommendation: Optional[PriorityRecommendation] = None
    run_metadata: RunMetadata
