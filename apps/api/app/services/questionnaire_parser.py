"""Questionnaire question-identification — backed by the real AI pipeline.

Real parsing (`ai_pipeline.parse_document()`, COO-owned, packages/ai-pipeline)
replaces the earlier JSON/plain-text stub. That package is a pure function:
bytes in, structured `ParsedQuestionnaire` out — no DB session, no HTTP
client, no persistence (AGENTS.md §3.2/3.3). This module is the thin,
backend-owned adapter that converts its output into the shape
`app/routers/documents.py` persists.

Supported input for this slice: a single `.xlsx` workbook, header row 1:
`external_question_id | question_text | section | is_required` (see
packages/ai-pipeline/src/ai_pipeline/parse.py for the exact traversal rules).

`question_order` is assigned by `ai_pipeline.parse_document()` from workbook
traversal order — sheet order, then row order (SPEC-AMD-007) — and is passed
through unchanged here. It is never re-derived from `external_question_id`,
`section`, or any other display string.

Pillar/SEDG mapping (Main Spec §17 Phase 3): every parsed question is now
run through `ai_pipeline.map_question_to_sedg()`, a pure, keyword-based
function against a representative SEDG taxonomy (see
packages/ai-pipeline/src/ai_pipeline/sedg_taxonomy.py's honesty caveat --
it is not a verified transcription of the real published standard). The
result is a **recommendation** for human review: it is stored in
`questions.pillar` / `sedg_topic_code` / `sedg_disclosure_code` /
`mapping_rationale`, and must never be conflated with `evidence_status` or
`review_status` (AGENTS.md §3.2) -- nothing here sets either of those.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ai_pipeline import ParsedQuestionnaire, map_question_to_sedg, parse_document


@dataclass
class ParsedQuestion:
    question_text: str
    question_order: int
    external_question_id: str | None = None
    section: str | None = None
    is_required: bool = True
    pillar: str = "UNCATEGORIZED"
    sedg_topic_code: str | None = None
    sedg_disclosure_code: str | None = None
    mapping_rationale: str | None = None
    source_location: dict = field(default_factory=dict)


@dataclass
class ParsedQuestionnaireResult:
    """Adapter-shaped output of `parse_questionnaire()`.

    `column_mapping` (header name -> spreadsheet column letter) is display
    metadata only, for a column-mapping confirmation UI (Main Spec §17
    Phase 3) -- it is never persisted to a DB column and never re-derives
    any parsed value.
    """

    questions: list[ParsedQuestion]
    column_mapping: dict[str, str] = field(default_factory=dict)


class QuestionnaireParseError(ValueError):
    """Raised when `ai_pipeline.parse_document()` cannot parse the upload.

    Wraps the pipeline's `ValueError` so callers in this app only ever catch
    one app-owned exception type, without hiding the underlying message.
    """


def _location_dict(raw_location: str) -> dict:
    """Convert the pipeline's display-only `"Sheet!Cell"` string into a
    Contract §4 `sheet_cell` location object.

    This describes where in the *questionnaire workbook* the question text
    was found. It is unrelated to evidence source locations, which are
    resolved separately by `app/routers/documents.py` from persisted
    `document_chunks` — never from anything the pipeline returns.
    """
    if "!" in raw_location:
        sheet_name, cell_range = raw_location.split("!", 1)
    else:
        sheet_name, cell_range = None, raw_location
    return {"type": "sheet_cell", "sheet_name": sheet_name, "cell_range": cell_range}


def parse_questionnaire(raw: bytes, filename: str) -> ParsedQuestionnaireResult:
    """Parse an uploaded questionnaire via the real AI pipeline.

    Raises `QuestionnaireParseError` on anything `ai_pipeline.parse_document()`
    rejects (missing headers, empty file, unsupported format).

    Each question is additionally run through `ai_pipeline.map_question_to_sedg()`
    (pure, keyword-based) to produce a draft pillar/topic/disclosure
    recommendation -- never a verdict, always human-reviewable.
    """
    try:
        parsed: ParsedQuestionnaire = parse_document(raw, filename)
    except ValueError as exc:
        raise QuestionnaireParseError(str(exc)) from exc

    questions = []
    for q in parsed.questions:
        mapping = map_question_to_sedg(q.question_text)
        questions.append(
            ParsedQuestion(
                question_text=q.question_text,
                question_order=q.question_order,
                external_question_id=q.external_question_id or None,
                section=q.section,
                is_required=q.is_required,
                pillar=mapping.pillar or "UNCATEGORIZED",
                sedg_topic_code=mapping.sedg_topic_code,
                sedg_disclosure_code=mapping.sedg_disclosure_code,
                mapping_rationale=mapping.rationale,
                source_location=_location_dict(q.source_location),
            )
        )

    return ParsedQuestionnaireResult(
        questions=questions, column_mapping=dict(parsed.column_mapping)
    )
