import pytest

from ai_pipeline.relevance import (
    RelevanceRefused,
    build_relevance_prompt,
    parse_relevance,
)


def test_relevance_requires_a_verbatim_source_quote():
    pairs = [
        ("How many employees completed training?", "254 employees completed training."),
        ("How many complaints?", "The policy describes how to file a complaint."),
    ]
    system, user = build_relevance_prompt(pairs)
    assert "254 employees completed training." in user
    assert "source" in system.lower()

    result = parse_relevance(
        '{"results": ['
        '{"verdict": "SUPPORTS", "quote": "254 employees completed training.", "missing": null},'
        '{"verdict": "UNRELATED", "quote": null, "missing": "No complaint count."}'
        "]}",
        pairs=pairs,
    )
    assert [item.verdict for item in result] == ["SUPPORTS", "UNRELATED"]


@pytest.mark.parametrize(
    "raw",
    [
        '{"results": [{"verdict": "SUPPORTS", "quote": "999 employees", "missing": null}]}',
        '{"results": [{"verdict": "VERIFIED", "quote": null, "missing": null}]}',
        '{"results": [{"verdict": "UNRELATED", "quote": null, "missing": "No count", "evidence_status": "MISSING"}]}',
        '{"results": []}',
    ],
)
def test_relevance_refuses_fabricated_or_out_of_contract_answers(raw):
    with pytest.raises(RelevanceRefused):
        parse_relevance(raw, pairs=[("How many?", "One employee.")])
