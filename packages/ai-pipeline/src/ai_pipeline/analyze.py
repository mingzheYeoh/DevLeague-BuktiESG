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


def _excerpt(text: str, limit: int = 200) -> str:
    stripped = text.strip()
    return stripped if len(stripped) <= limit else stripped[: limit - 1].rstrip() + "…"


def _input_hash(question: AnalysisQuestion, chunks: list[DocumentChunk]) -> str:
    payload = question.question_id + "|" + question.question_text
    payload += "|" + "|".join(f"{c.chunk_id}:{c.text}" for c in chunks)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def analyze_question(
    question: AnalysisQuestion, document_chunks: list[DocumentChunk]
) -> AnalysisResult:
    """Match `question` against `document_chunks` by keyword overlap only.

    Returns an `AnalysisResult` shaped per
    docs/spec/Shared-Integration-Contract.md §8. At most one candidate is
    returned in this slice. `missing_elements` is always non-empty when a
    candidate is present, because this slice never asserts full coverage —
    it hands the server enough (a candidate plus an explicit gap) to compute
    `PARTIAL`, not `COMPLETE`. Never emits `evidence_status` or a location.
    """

    q_keywords = _keywords(question.question_text)

    best_chunk: Optional[DocumentChunk] = None
    best_score = 0
    best_matched: set[str] = set()

    for chunk in document_chunks:
        c_keywords = _keywords(chunk.text)
        matched = q_keywords & c_keywords
        score = len(matched)
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
                    + ", ".join(sorted(best_matched))
                ),
                quoted_excerpt=_excerpt(best_chunk.text),
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
