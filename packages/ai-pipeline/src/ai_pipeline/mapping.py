"""map_question_to_sedg() — pure, keyword-based E/S/G + SEDG mapping.

Consistent with this package's keyword-first philosophy (BLOCKER-06, see
analyze.py): no LLM call, no embeddings, no fuzzy matching. A question's
text is scored against the keyword list of every SEDG disclosure in
`sedg_taxonomy.SEDG_TAXONOMY`; the best-scoring disclosure wins.

Purity boundary (AGENTS.md §3.2/3.3, same as every other function in this
package): no DB session, no HTTP client, no credentials. Input is a plain
string, output is a `MappingResult`. The caller (`backend/`) decides what to
do with it — persisting it into `questions.pillar` /
`questions.sedg_topic_code` / `questions.sedg_disclosure_code` /
`questions.mapping_rationale` is the server's job, never this package's.

This is a **recommendation**, never a verdict: `MappingResult` is not
`evidence_status`, `review_status`, or any other forbidden field in
AGENTS.md §3.2, and must never be conflated with them by a caller.

See `sedg_taxonomy.py`'s module docstring for the taxonomy's honesty
caveat — it is a representative working taxonomy, not a verified
transcription of the real published SEDG v2 standard.
"""

from __future__ import annotations

import re

from .models import MappingResult
from .sedg_taxonomy import SEDG_TAXONOMY, SedgDisclosure, SedgTopic

_WORD_RE = re.compile(r"[a-z0-9]+")

# A keyword may itself be a multi-word phrase ("scope 1", "board diversity").
# Matching is done by substring search against the lowercased question text
# rather than by set-intersection of single tokens, so multi-word keywords
# are matched too.


def _normalize(text: str) -> str:
    return " ".join(_WORD_RE.findall(text.lower()))


def _score_disclosure(question_norm: str, disclosure: SedgDisclosure) -> tuple[int, list[str]]:
    matched: list[str] = []
    for keyword in disclosure.keywords:
        keyword_norm = _normalize(keyword)
        if keyword_norm and keyword_norm in question_norm:
            matched.append(keyword)
    return len(matched), matched


def map_question_to_sedg(
    question_text: str,
    taxonomy: tuple[SedgTopic, ...] = SEDG_TAXONOMY,
) -> MappingResult:
    """Map one question's text to the best-matching SEDG pillar/topic/disclosure.

    Returns `pillar="UNCATEGORIZED"` with no topic/disclosure and
    `confidence=0.0` when no keyword in the taxonomy overlaps the question
    text at all — an honest "we don't know", not a guess.

    `confidence` is a simple heuristic (matched keyword count, capped),
    not a calibrated probability — it exists to let a human reviewer
    triage which mappings need the most scrutiny, nothing more.
    """
    question_norm = _normalize(question_text)

    best_topic: SedgTopic | None = None
    best_disclosure: SedgDisclosure | None = None
    best_score = 0
    best_matched: list[str] = []

    if question_norm:
        for topic in taxonomy:
            for disclosure in topic.disclosures:
                score, matched = _score_disclosure(question_norm, disclosure)
                if score > best_score:
                    best_score = score
                    best_topic = topic
                    best_disclosure = disclosure
                    best_matched = matched

    if best_topic is None or best_disclosure is None or best_score == 0:
        return MappingResult(
            pillar="UNCATEGORIZED",
            sedg_topic_code=None,
            sedg_disclosure_code=None,
            rationale=(
                "No keyword overlap with the representative SEDG taxonomy "
                "(packages/ai-pipeline/src/ai_pipeline/sedg_taxonomy.py) — "
                "requires manual mapping by a human reviewer."
            ),
            confidence=0.0,
        )

    confidence = round(min(best_score / 3.0, 1.0), 2)

    rationale = (
        f"Matched keyword(s) {sorted(best_matched)!r} against SEDG topic "
        f"'{best_topic.code} {best_topic.name}', disclosure "
        f"'{best_disclosure.code} {best_disclosure.name}'. Keyword-based "
        "suggestion from a representative taxonomy — pending human review, "
        "not a verified SEDG classification."
    )

    return MappingResult(
        pillar=best_topic.pillar,
        sedg_topic_code=best_topic.code,
        sedg_disclosure_code=best_disclosure.code,
        rationale=rationale,
        confidence=confidence,
    )
