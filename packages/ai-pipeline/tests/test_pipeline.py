"""Tests for the First Vertical Slice AI pipeline core.

Runs fully offline / deterministic — no live LLM call, no database, no
network (BLOCKER-08: never use the live provider in CI).
"""

from __future__ import annotations

import io

import pytest
from openpyxl import Workbook

from ai_pipeline import (
    AnalysisQuestion,
    DocumentChunk,
    analyze_question,
    parse_document,
)

_FORBIDDEN_FIELDS = {
    "review_status",
    "final_compliance_status",
    "audit_passed",
    "certified",
    "conflict_winner",
    "customer_submission_approved",
    "evidence_status",
    "status_findings",
}


def _build_fixture_xlsx() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Questionnaire"
    ws.append(["external_question_id", "question_text", "section", "is_required"])
    ws.append(["Q-2", "How much electricity did the site consume in 2025?", "Environmental", True])
    ws.append(["Q-10", "Describe the company's employee safety training program.", "Social", True])
    ws.append(["Q-1", "What is the total headcount at year end?", "Social", False])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_parse_document_extracts_rows_in_traversal_order():
    parsed = parse_document(_build_fixture_xlsx(), "questionnaire.xlsx")

    assert parsed.filename == "questionnaire.xlsx"
    assert len(parsed.questions) == 3

    # question_order must follow row/traversal order, never lexical/display
    # order of external_question_id (SPEC-AMD-007: "Q-10" before "Q-2" would be
    # the wrong, lexical-sort answer).
    assert [q.external_question_id for q in parsed.questions] == ["Q-2", "Q-10", "Q-1"]
    assert [q.question_order for q in parsed.questions] == [0, 1, 2]

    first = parsed.questions[0]
    assert first.question_text == "How much electricity did the site consume in 2025?"
    assert first.section == "Environmental"
    assert first.is_required is True
    assert first.source_location.startswith("Questionnaire!")


def test_parse_document_rejects_missing_required_headers():
    wb = Workbook()
    ws = wb.active
    ws.append(["id", "text"])  # wrong header names
    buf = io.BytesIO()
    wb.save(buf)

    with pytest.raises(ValueError):
        parse_document(buf.getvalue(), "bad.xlsx")


def test_analyze_question_matches_best_chunk_by_keyword_overlap():
    question = AnalysisQuestion(
        question_id="question_001",
        question_text="How much electricity did the site consume in 2025?",
    )
    chunks = [
        DocumentChunk(
            chunk_id="chunk_001",
            text="Employee safety training completed for all staff in Q1 2025.",
        ),
        DocumentChunk(
            chunk_id="chunk_002",
            text="Total electricity consumption: 12,840 kWh at the Selangor site in January 2025.",
        ),
    ]

    result = analyze_question(question, chunks)

    assert result.question_id == "question_001"
    assert result.schema_version == "1.0.0"
    assert len(result.candidate_evidence) == 1
    assert result.candidate_evidence[0].chunk_id == "chunk_002"
    assert result.missing_elements  # non-empty: a PARTIAL candidate, not COMPLETE
    assert result.run_metadata.source_ids == ["chunk_002"]
    assert result.run_metadata.provider == "keyword-matcher"


def test_analyze_question_no_match_returns_empty_candidates():
    question = AnalysisQuestion(question_id="question_002", question_text="Zzyzx qwerty unmatched?")
    chunks = [DocumentChunk(chunk_id="chunk_001", text="Totally unrelated content here.")]

    result = analyze_question(question, chunks)

    assert result.candidate_evidence == []
    assert result.missing_elements
    assert result.run_metadata.source_ids == []


def test_analysis_result_schema_has_no_forbidden_fields():
    question = AnalysisQuestion(question_id="question_003", question_text="Electricity usage?")
    chunks = [DocumentChunk(chunk_id="chunk_001", text="Electricity usage was 100 kWh.")]

    result = analyze_question(question, chunks)
    payload = result.model_dump()

    assert _FORBIDDEN_FIELDS.isdisjoint(payload.keys())
    for candidate in payload["candidate_evidence"]:
        assert _FORBIDDEN_FIELDS.isdisjoint(candidate.keys())
        # never a source location — only a chunk_id the server resolves
        assert "source_location" not in candidate
        assert "location" not in candidate

    # additionalProperties:false is enforced by the model itself (extra="forbid");
    # confirm an unknown field is actually rejected, not silently accepted.
    with pytest.raises(Exception):
        type(result)(**{**payload, "evidence_status": "PARTIAL"})
