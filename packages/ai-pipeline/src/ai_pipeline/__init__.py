"""BuktiESG AI pipeline core (COO-owned).

Pure-function boundary only — see README.md and AGENTS.md §3.2/3.3.
"""

from .models import (
    AnalysisResult,
    CandidateEvidence,
    DocumentChunk,
    ExtractedChunk,
    ParsedQuestion,
    ParsedQuestionnaire,
    RunMetadata,
)
from .parse import parse_document
from .evidence_parse import (
    parse_docx_evidence,
    parse_pdf_evidence,
    parse_plain_text_evidence,
    parse_xlsx_evidence,
)
from .analyze import AnalysisQuestion, analyze_question
from .provider import FixtureProvider, LLMProvider

__all__ = [
    "AnalysisResult",
    "AnalysisQuestion",
    "CandidateEvidence",
    "DocumentChunk",
    "ExtractedChunk",
    "ParsedQuestion",
    "ParsedQuestionnaire",
    "RunMetadata",
    "parse_document",
    "parse_pdf_evidence",
    "parse_docx_evidence",
    "parse_xlsx_evidence",
    "parse_plain_text_evidence",
    "analyze_question",
    "FixtureProvider",
    "LLMProvider",
]
