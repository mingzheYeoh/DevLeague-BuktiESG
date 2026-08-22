"""Tests for map_question_to_sedg() — Main Spec §17 Phase 3.

The taxonomy in sedg_taxonomy.py is a representative working taxonomy, not
a verified transcription of the real published SEDG v2 standard (see its
module docstring). These tests therefore check pillar-level correctness at
minimum, and topic/disclosure codes loosely -- exact disclosure identity is
not a ground-truth claim.
"""

from __future__ import annotations

from ai_pipeline import MappingResult, map_question_to_sedg
from ai_pipeline.sedg_taxonomy import SEDG_TAXONOMY, DISCLOSURE_COUNT, TOPIC_COUNT

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


def test_taxonomy_has_three_pillars_and_representative_size():
    pillars = {topic.pillar for topic in SEDG_TAXONOMY}
    assert pillars == {"E", "S", "G"}
    assert TOPIC_COUNT == 15
    assert DISCLOSURE_COUNT == 38


def test_mapping_module_imports_no_db_or_http_client():
    import inspect

    import ai_pipeline.mapping as mapping_module

    source = inspect.getsource(mapping_module)
    for forbidden in ("sqlalchemy", "requests", "httpx", "psycopg"):
        assert forbidden not in source.lower()


def test_energy_question_maps_to_environmental_pillar():
    result = map_question_to_sedg(
        "What were the total Scope 1 and Scope 2 GHG emissions for the reporting year?"
    )
    assert isinstance(result, MappingResult)
    assert result.pillar == "E"
    assert result.sedg_topic_code == "E1"
    assert result.confidence is not None and result.confidence > 0


def test_safety_question_maps_to_social_pillar():
    result = map_question_to_sedg(
        "How many work-related injuries (lost time injury) occurred at the site?"
    )
    assert result.pillar == "S"
    assert result.sedg_topic_code == "S2"


def test_board_question_maps_to_governance_pillar():
    result = map_question_to_sedg(
        "What percentage of the Board is composed of independent directors?"
    )
    assert result.pillar == "G"
    assert result.sedg_topic_code == "G1"


def test_water_question_maps_to_environmental_pillar():
    result = map_question_to_sedg("Describe total water withdrawal and water source for the year.")
    assert result.pillar == "E"
    assert result.sedg_topic_code == "E2"


def test_gender_diversity_question_maps_to_social_pillar():
    result = map_question_to_sedg("What is the gender diversity of management, i.e. women in management?")
    assert result.pillar == "S"
    assert result.sedg_topic_code == "S4"


def test_unmatched_question_returns_uncategorized_with_zero_confidence():
    result = map_question_to_sedg("What is your favourite colour?")
    assert result.pillar == "UNCATEGORIZED"
    assert result.sedg_topic_code is None
    assert result.sedg_disclosure_code is None
    assert result.confidence == 0.0
    assert result.rationale is not None


def test_result_never_carries_a_forbidden_verdict_field():
    result = map_question_to_sedg("What were Scope 1 emissions?")
    dumped = result.model_dump()
    assert _FORBIDDEN_FIELDS.isdisjoint(dumped.keys())


def test_mapping_is_deterministic():
    text = "How many work-related injuries occurred at the facility this year?"
    first = map_question_to_sedg(text)
    second = map_question_to_sedg(text)
    assert first == second
