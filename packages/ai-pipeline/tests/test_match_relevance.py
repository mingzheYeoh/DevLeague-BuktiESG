"""Matching must be driven by the distinctive words in a question.

Found by uploading the twenty-document sample evidence set: all twenty
questions, across all three pillars, cited the same document — a superseded
2019 employee handbook — and the winning link for "Report total Scope 1 direct
GHG emissions" matched on the words `report` and `reporting`.

Two causes, both fixed here:

1. Every matched keyword counted equally. `report`, `total`, `period`,
   `metric` and `tonnes` appear in nearly every ESG question, so a chunk could
   win on vocabulary that carries no information about *which* question it is.
   Measured on the real sample corpus, the correct document for Q-E-01 scored
   exactly the same as two wrong ones (three matches each).

2. A single shared word created an evidence link at all, so eighteen of the
   twenty documents became candidates for a greenhouse-gas question.

The fix weights each keyword by how rare it is across the questionnaire — the
natural corpus for "what is distinctive about this question" — and refuses to
build a link out of generic words alone. It stays keyword-only: no embeddings,
no model call (BLOCKER-06).
"""

from __future__ import annotations

import pytest

from ai_pipeline.analyze import AnalysisQuestion, analyze_question, keyword_weights
from ai_pipeline.models import DocumentChunk

# A questionnaire in the shape of the real one: every question repeats the
# reporting boilerplate, and each has its own subject.
QUESTIONNAIRE = [
    "Report total Scope 1 direct GHG emissions in metric tonnes of CO2 equivalent for the reporting period.",
    "Report the total water withdrawal from all areas for the reporting period, with a breakdown by source.",
    "Report total waste generated and total waste diverted from disposal in metric tonnes for the reporting period.",
    "Report the average hours of training per employee for the reporting period.",
    "Report the total number of employees and the employee turnover rate for the reporting period.",
]


@pytest.fixture()
def weights() -> dict[str, float]:
    return keyword_weights(QUESTIONNAIRE)


def _chunk(chunk_id: str, text: str) -> DocumentChunk:
    return DocumentChunk(chunk_id=chunk_id, text=text)


def test_boilerplate_words_carry_less_weight_than_subject_words(weights):
    """`report` and `period` are in every question; `ghg` is in one."""
    assert weights["ghg"] > weights["report"]
    assert weights["ghg"] > weights["reporting"]
    assert weights["water"] > weights["total"]


def test_the_document_about_the_subject_wins_over_reporting_boilerplate(weights):
    question = AnalysisQuestion(
        question_id="q1",
        question_text=QUESTIONNAIRE[0],
    )
    on_topic = _chunk(
        "ghg-inventory",
        "Scope 1 direct GHG emissions from diesel and LPG combustion: 58.8 tonnes CO2 equivalent.",
    )
    boilerplate = _chunk(
        "handbook",
        "Employees should report hours worked to their supervisor for the reporting "
        "period. The company reports total leave taken each period.",
    )

    result = analyze_question(question, [boilerplate, on_topic], keyword_weights=weights)

    assert result.candidate_evidence
    assert result.candidate_evidence[0].chunk_id == "ghg-inventory"


def test_a_match_made_only_of_generic_words_produces_no_candidate(weights):
    """This is what stopped `MISSING` from ever occurring: any single shared
    word was enough to attach evidence to a question."""
    question = AnalysisQuestion(question_id="q2", question_text=QUESTIONNAIRE[0])
    unrelated = _chunk(
        "leave-policy",
        "Annual leave entitlement begins at twelve days per reporting period and "
        "rises with length of service. Report requests to your supervisor.",
    )

    result = analyze_question(question, [unrelated], keyword_weights=weights)

    assert result.candidate_evidence == [], (
        "a chunk sharing only reporting boilerplate must not become evidence"
    )
    assert result.missing_elements


def test_the_match_score_is_reported_so_links_can_be_ranked(weights):
    """`schemas.py` used to show whichever link was created last as 'the
    evidence', which made the displayed document depend on upload order. It
    can only rank by quality if the score survives the pipeline."""
    question = AnalysisQuestion(question_id="q3", question_text=QUESTIONNAIRE[1])
    strong = _chunk("water", "Total water withdrawal by source: 4,120 cubic metres, purchased supply.")

    result = analyze_question(question, [strong], keyword_weights=weights)

    assert result.candidate_evidence[0].match_score is not None
    assert result.candidate_evidence[0].match_score > 0


def test_without_weights_the_behaviour_is_unchanged(weights):
    """The parameter is optional so existing callers keep working; a caller
    that supplies nothing gets the old uniform-weight scoring."""
    question = AnalysisQuestion(question_id="q4", question_text=QUESTIONNAIRE[0])
    chunk = _chunk("any", "Report the reporting period.")

    result = analyze_question(question, [chunk])

    assert result.candidate_evidence, "uniform scoring still matches on any overlap"


def test_a_single_question_questionnaire_falls_back_to_uniform_weights():
    """With one question there is nothing to be distinctive *against*.

    Every term would have a document frequency equal to the corpus size and
    score 0.0, so the generic-term guard would reject all evidence for the
    only question there is. Saying "I cannot tell" is the honest answer.
    """
    assert keyword_weights(["Report total electricity consumption in kWh."]) == {}
    assert keyword_weights([]) == {}


def test_two_questions_are_enough_to_separate_shared_from_unique_terms():
    weights = keyword_weights(
        [
            "Report total electricity consumption in kWh for the reporting period.",
            "Report total water withdrawal in cubic metres for the reporting period.",
        ]
    )

    # In both questions -> pure boilerplate.
    assert weights["report"] == 0.0
    assert weights["reporting"] == 0.0
    # In one of two -> exactly the generic/distinctive boundary, and kept.
    assert weights["electricity"] == 0.5
    assert weights["water"] == 0.5
