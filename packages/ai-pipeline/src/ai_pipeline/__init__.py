"""BuktiESG AI pipeline core (COO-owned).

Pure-function boundary only — see README.md and AGENTS.md §3.2/3.3.
"""

from .models import (
    AnalysisResult,
    CandidateEvidence,
    DocumentChunk,
    ParsedQuestion,
    ParsedQuestionnaire,
    RunMetadata,
)
from .parse import parse_document
from .analyze import AnalysisQuestion, analyze_question
from .provider import FixtureProvider, LLMProvider

__all__ = [
    "AnalysisResult",
    "AnalysisQuestion",
    "CandidateEvidence",
    "DocumentChunk",
    "ParsedQuestion",
    "ParsedQuestionnaire",
    "RunMetadata",
    "parse_document",
    "analyze_question",
    "FixtureProvider",
    "LLMProvider",
]
