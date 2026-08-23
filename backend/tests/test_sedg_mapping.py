"""Questionnaire upload -> questions carry pillar/SEDG mapping data.

Main Spec §17 Phase 3: E/S/G + SEDG mapping wiring and the column-mapping
confirmation UI's backend support. The mapping is produced by
`ai_pipeline.map_question_to_sedg()` against a representative taxonomy (see
packages/ai-pipeline/src/ai_pipeline/sedg_taxonomy.py's honesty caveat) --
it is a draft recommendation, never a verdict, and must never be conflated
with `evidence_status` / `review_status`.
"""

from __future__ import annotations

import io

from openpyxl import Workbook


def _build_questionnaire_xlsx(rows: list[dict]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Questionnaire"
    ws.append(["external_question_id", "question_text", "section", "is_required"])
    for row in rows:
        ws.append(
            [
                row.get("external_question_id", ""),
                row["question_text"],
                row.get("section", ""),
                row.get("is_required", True),
            ]
        )
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _upload_questionnaire(client, case_id: str, rows: list[dict]):
    xlsx_bytes = _build_questionnaire_xlsx(rows)
    return client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={
            "file": (
                "questionnaire.xlsx",
                xlsx_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        data={"document_type": "QUESTIONNAIRE"},
    )


def test_upload_populates_pillar_and_sedg_mapping_on_questions(client):
    resp = client.post("/api/v1/cases", json={"title": "Case"})
    case_id = resp.json()["id"]

    _upload_questionnaire(
        client,
        case_id,
        [
            {
                "external_question_id": "Q-1",
                "question_text": (
                    "What were the total Scope 1 and Scope 2 GHG emissions "
                    "for the reporting year?"
                ),
            },
            {
                "external_question_id": "Q-2",
                "question_text": "What is your favourite colour?",
            },
        ],
    )

    questions = client.get(f"/api/v1/cases/{case_id}/questions").json()
    assert len(questions) == 2

    by_ext_id = {q["external_question_id"]: q for q in questions}

    ghg_question = by_ext_id["Q-1"]
    assert ghg_question["pillar"] == "E"
    assert ghg_question["sedg_topic_code"] == "E1"
    assert ghg_question["mapping_rationale"]

    uncategorized_question = by_ext_id["Q-2"]
    assert uncategorized_question["pillar"] == "UNCATEGORIZED"
    assert uncategorized_question["sedg_topic_code"] is None
    assert uncategorized_question["mapping_rationale"]


def test_mapping_never_sets_evidence_or_review_status(client):
    """The mapping recommendation must never leak into a verdict field --
    a freshly-imported question always starts MISSING/UNREVIEWED regardless
    of how confidently it was mapped to a pillar (AGENTS.md §3.2)."""
    resp = client.post("/api/v1/cases", json={"title": "Case"})
    case_id = resp.json()["id"]

    _upload_questionnaire(
        client,
        case_id,
        [{"external_question_id": "Q-1", "question_text": "What were Scope 1 emissions?"}],
    )

    question = client.get(f"/api/v1/cases/{case_id}/questions").json()[0]
    assert question["pillar"] == "E"
    assert question["evidence_status"] == "MISSING"
    assert question["review_status"] == "UNREVIEWED"


def test_questionnaire_upload_response_carries_detected_column_mapping(client):
    resp = client.post("/api/v1/cases", json={"title": "Case"})
    case_id = resp.json()["id"]

    upload_resp = _upload_questionnaire(
        client, case_id, [{"external_question_id": "Q-1", "question_text": "Headcount?"}]
    )
    document = upload_resp.json()

    assert document["detected_columns"] is not None
    assert document["detected_columns"]["question_text"] == "B"
    assert document["detected_columns"]["external_question_id"] == "A"
