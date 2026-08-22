"""Questionnaire question-identification — STUB for this slice.

Scope boundary: real document parsing/extraction (Docling, OCR, sheet
traversal, chunking into document_chunks with embeddings) is the COO's
document-processing pipeline (Main Spec §6/§12), not backend/CTO scope, and
is not implemented here. This module implements only the minimum "identify
questions" step the First Vertical Slice needs, synchronously, with no job
queue (the Job/processing_jobs resource is SPEC-AMD-001 / decision 012, out
of scope for this slice).

Supported input formats, deliberately simple:

1. JSON: a top-level array of objects, each with at least
   ``question_text``, and optionally ``external_question_id``, ``section``,
   ``is_required``, ``pillar``.
2. Plain text: one question per non-blank line.

Row order in the source (JSON array order / line order) becomes
``question_order`` directly (SPEC-AMD-007 / RULING-04) — captured once, at
traversal time, never re-derived from external_question_id or section later.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class ParsedQuestion:
    question_text: str
    question_order: int
    external_question_id: str | None = None
    section: str | None = None
    is_required: bool = True
    pillar: str = "UNCATEGORIZED"
    source_location: dict = field(default_factory=dict)


class QuestionnaireParseError(ValueError):
    pass


_VALID_PILLARS = {"E", "S", "G", "UNCATEGORIZED"}


def parse_questionnaire(raw: bytes, filename: str) -> list[ParsedQuestion]:
    text = raw.decode("utf-8", errors="replace").strip()
    if not text:
        raise QuestionnaireParseError("Questionnaire file is empty.")

    if text.startswith("["):
        return _parse_json(text)
    return _parse_plain_text(text)


def _parse_json(text: str) -> list[ParsedQuestion]:
    try:
        rows = json.loads(text)
    except json.JSONDecodeError as exc:
        raise QuestionnaireParseError(f"Invalid JSON questionnaire: {exc}") from exc

    if not isinstance(rows, list):
        raise QuestionnaireParseError("JSON questionnaire must be a top-level array.")

    parsed: list[ParsedQuestion] = []
    for order, row in enumerate(rows):
        if not isinstance(row, dict) or not row.get("question_text"):
            raise QuestionnaireParseError(
                f"Row {order} is missing required field 'question_text'."
            )
        pillar = row.get("pillar", "UNCATEGORIZED") or "UNCATEGORIZED"
        if pillar not in _VALID_PILLARS:
            pillar = "UNCATEGORIZED"
        parsed.append(
            ParsedQuestion(
                question_text=row["question_text"],
                question_order=order,
                external_question_id=row.get("external_question_id"),
                section=row.get("section"),
                is_required=bool(row.get("is_required", True)),
                pillar=pillar,
                source_location={
                    "type": "paragraph",
                    "heading_path": [row["section"]] if row.get("section") else [],
                    "paragraph_index": order,
                },
            )
        )
    if not parsed:
        raise QuestionnaireParseError("Questionnaire contains no questions.")
    return parsed


def _parse_plain_text(text: str) -> list[ParsedQuestion]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        raise QuestionnaireParseError("Questionnaire contains no questions.")
    return [
        ParsedQuestion(
            question_text=line,
            question_order=order,
            source_location={
                "type": "paragraph",
                "heading_path": [],
                "paragraph_index": order,
            },
        )
        for order, line in enumerate(lines)
    ]
