"""analyze_question() — pure keyword-first question/evidence matcher.

First Vertical Slice scope: match one question to at most one candidate
evidence chunk, using keyword overlap only (BLOCKER-06 — keyword-first
retrieval; no embeddings, no fuzzy matching, no LLM call for this slice).

Structural boundary (AGENTS.md §3.2/3.3, BLOCKER-04):
- No DB session, no HTTP client, no credentials.
- Only `document_chunks` passed in by the caller are considered — never any
  other Case's data.
- Returns a `chunk_id` only, never a source location. The server resolves the
  location from `document_chunks` (AGENTS.md §3.3).
- Never sets `evidence_status`, `review_status`, `final_compliance_status`, or
  any other verdict field — those belong to the server's deterministic rule
  engine. This module always leaves that computation to the caller by
  supplying `candidate_evidence` and `missing_elements`, never a status.

Uploaded document text is untrusted data (trust boundary TB-3): it is only
ever tokenized and compared for keyword overlap here, never interpreted as an
instruction.
"""

from __future__ import annotations

import hashlib
import re
from typing import Optional

from pydantic import BaseModel, ConfigDict

from .models import AnalysisResult, CandidateEvidence, DocumentChunk, RunMetadata

_STOPWORDS = {
    "the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "is", "are",
    "was", "were", "does", "do", "did", "has", "have", "had", "please",
    "provide", "what", "which", "how", "your", "you", "this", "that", "with",
    "from", "by", "as", "at", "be", "it", "its",
}

_WORD_RE = re.compile(r"[a-z0-9]+")

_PROMPT_VERSION = "keyword-match-v1"


class AnalysisQuestion(BaseModel):
    """Minimal question shape `analyze_question()` needs.

    Deliberately decoupled from `ParsedQuestion`: the server assigns the
    persisted `question_id` after `parse_document()` output is stored, and
    that is the id passed back in here — this package never sees a DB id
    generator or session.
    """

    model_config = ConfigDict(extra="forbid")

    question_id: str
    question_text: str


def _keywords(text: str) -> set[str]:
    return {w for w in _WORD_RE.findall(text.lower()) if len(w) >= 3 and w not in _STOPWORDS}


# A matched term is "generic" when it appears in more than half the
# questionnaire, and a match built only from generic terms is not evidence.
#
# This is a fraction of the weight scale below, not an absolute score, and that
# distinction matters: an inverse-document-frequency value depends on how many
# questions there are, so an absolute floor that behaves correctly for a
# twenty-question questionnaire silently rejects everything in a two-question
# one. The weights below are therefore scale-free by construction.
_GENERIC_TERM_WEIGHT = 0.5


def keyword_weights(question_texts: list[str]) -> dict[str, float]:
    """How much each keyword distinguishes one question from the others.

    The questionnaire is the right corpus for this. Every ESG question repeats
    the same reporting vocabulary — `report`, `total`, `period`, `metric`,
    `tonnes` — so those words say nothing about *which* question a chunk
    answers, while `ghg`, `ltifr` or `withdrawal` say almost everything.
    Counting them equally is what let a paragraph about annual leave outrank a
    GHG inventory row.

    The weight is the fraction of questions that do *not* contain the term, so
    it always lands in [0, 1) and means the same thing whatever the
    questionnaire's size:

        in every question      -> 0.0    (pure boilerplate)
        in half of them        -> 0.5    (the generic/distinctive boundary)
        in 1 of 20             -> 0.95   (highly distinctive)

    A log-scaled inverse document frequency would rank much the same, but its
    magnitude depends on the number of questions — which makes any fixed
    threshold quietly wrong for a questionnaire of a different size. Ranking
    here is only ever within one question, so the linear form is enough and it
    can be reasoned about.

    Pure function, no I/O: the server computes this once per questionnaire and
    passes it in, because this package never touches a database
    (AGENTS.md §3.3).
    """
    # One question is no corpus. "How distinctive is this word across the
    # questions" has no answer when there is nothing to contrast against, and
    # the formula below would score every term 0.0 and reject all evidence.
    # Returning nothing makes the caller fall back to uniform weights, which
    # says "I cannot tell" rather than "none of this counts".
    if len(question_texts) < 2:
        return {}
    total = len(question_texts)
    document_frequency: dict[str, int] = {}
    for text in question_texts:
        for word in _keywords(text):
            document_frequency[word] = document_frequency.get(word, 0) + 1
    return {word: 1.0 - freq / total for word, freq in document_frequency.items()}


def _excerpt(text: str, limit: int = 200) -> str:
    stripped = text.strip()
    return stripped if len(stripped) <= limit else stripped[: limit - 1].rstrip() + "…"


def _input_hash(question: AnalysisQuestion, chunks: list[DocumentChunk]) -> str:
    payload = question.question_id + "|" + question.question_text
    payload += "|" + "|".join(f"{c.chunk_id}:{c.text}" for c in chunks)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def analyze_question(
    question: AnalysisQuestion,
    document_chunks: list[DocumentChunk],
    *,
    keyword_weights: dict[str, float] | None = None,
) -> AnalysisResult:
    """Match `question` against `document_chunks` by keyword overlap only.

    `keyword_weights` comes from the module-level function of the same name and
    scores each matched term by how rare it is across the questionnaire. Supply
    it: without it every word counts the same, which is how a paragraph about
    annual leave came to be cited as evidence of Scope 1 emissions. It stays
    optional so existing callers keep their behaviour rather than silently
    changing it.

    Returns an `AnalysisResult` shaped per
    docs/spec/Shared-Integration-Contract.md §8. At most one candidate is
    returned in this slice. `missing_elements` is always non-empty when a
    candidate is present, because this slice never asserts full coverage —
    it hands the server enough (a candidate plus an explicit gap) to compute
    `PARTIAL`, not `COMPLETE`. Never emits `evidence_status` or a location.
    """

    q_keywords = _keywords(question.question_text)
    weights = keyword_weights or {}

    def _weight(term: str) -> float:
        # 1.0 when no weights are supplied, so the unweighted path is exactly
        # the old raw-count scoring.
        return weights.get(term, 1.0) if weights else 1.0

    best_chunk: Optional[DocumentChunk] = None
    best_score = 0.0
    best_matched: set[str] = set()

    for chunk in document_chunks:
        c_keywords = _keywords(chunk.text)
        matched = q_keywords & c_keywords
        if not matched:
            continue
        # A match built only from words that appear all over the questionnaire
        # is not evidence of anything. Without this, one shared `report` was
        # enough to attach a document to a question, so every question had a
        # candidate and MISSING could never occur.
        if weights and max(_weight(term) for term in matched) < _GENERIC_TERM_WEIGHT:
            continue
        score = sum(_weight(term) for term in matched)
        if score > best_score:
            best_score = score
            best_chunk = chunk
            best_matched = matched

    candidate_evidence: list[CandidateEvidence] = []
    missing_elements: list[str] = []
    source_ids: list[str] = []

    if best_chunk is not None and best_score > 0:
        candidate_evidence.append(
            CandidateEvidence(
                chunk_id=best_chunk.chunk_id,
                claim_supported=(
                    "Keyword overlap with question terms: "
                    + ", ".join(sorted(best_matched, key=lambda t: (-_weight(t), t)))
                ),
                quoted_excerpt=_excerpt(best_chunk.text),
                match_score=round(best_score, 4),
            )
        )
        source_ids.append(best_chunk.chunk_id)
        missing_elements.append(
            "Automated keyword match only — coverage of the full question is "
            "not verified and requires human review before this can be "
            "treated as complete evidence."
        )
        draft_answer = (
            "Candidate evidence located via keyword match; not yet human-reviewed."
        )
    else:
        missing_elements.append(
            f"No document chunk matched any keyword from the question: "
            f"'{question.question_text}'."
        )
        draft_answer = None

    return AnalysisResult(
        question_id=question.question_id,
        draft_answer=draft_answer,
        mapping=None,
        candidate_evidence=candidate_evidence,
        missing_elements=missing_elements,
        possible_conflicts=[],
        suggested_follow_up=None,
        priority_recommendation=None,
        run_metadata=RunMetadata(
            provider="keyword-matcher",
            model="keyword-first-v1",
            prompt_version=_PROMPT_VERSION,
            input_hash=_input_hash(question, document_chunks),
            source_ids=source_ids,
            latency_ms=0,
            estimated_cost=0.0,
        ),
    )
