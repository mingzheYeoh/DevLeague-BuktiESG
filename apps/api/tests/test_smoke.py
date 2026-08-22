"""Smoke tests for the First Vertical Slice, wired to the real AI pipeline:

    Create Case -> upload one real .xlsx questionnaire (ai_pipeline.parse_document)
                -> upload an evidence document -> ai_pipeline.analyze_question()
                -> server resolves chunk_id -> real location, computes PARTIAL
                -> persist a SUBMISSION action -> persist/reload

See docs/spec/README-Team-Specs.md, "First Vertical Slice", and
docs/spec/AMENDMENTS.md SPEC-AMD-005/006/007.
"""

from __future__ import annotations

import io

from openpyxl import Workbook


def _build_questionnaire_xlsx(rows: list[dict]) -> bytes:
    """Build a minimal .xlsx questionnaire matching ai_pipeline.parse_document()'s
    expected header layout: external_question_id | question_text | section |
    is_required."""
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


def test_first_vertical_slice(client):
    # 1. Create Case
    resp = client.post(
        "/api/v1/cases",
        json={"title": "Demo FMCG ESG Questionnaire", "customer_name": "Demo Customer"},
    )
    assert resp.status_code == 201, resp.text
    case = resp.json()
    case_id = case["id"]
    assert case["status"] == "DRAFT"

    # 2. List questions before any upload -> empty
    resp = client.get(f"/api/v1/cases/{case_id}/questions")
    assert resp.status_code == 200
    assert resp.json() == []

    # 3. Upload one real .xlsx questionnaire, out of order on purpose to
    #    prove question_order (SPEC-AMD-007) reflects workbook row order,
    #    not id or external_question_id lexical order ("Q-10" before "Q-2").
    questionnaire_rows = [
        {
            "question_text": "Report annual electricity consumption.",
            "external_question_id": "Q-E-01",
            "section": "Environment",
            "is_required": True,
        },
        {
            "question_text": "Describe your anti-bribery policy.",
            "external_question_id": "Q-G-01",
            "section": "Governance",
            "is_required": True,
        },
    ]
    xlsx_bytes = _build_questionnaire_xlsx(questionnaire_rows)
    files = {
        "file": (
            "questionnaire.xlsx",
            xlsx_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    resp = client.post(
        f"/api/v1/cases/{case_id}/documents",
        files=files,
        data={"document_type": "QUESTIONNAIRE"},
    )
    assert resp.status_code == 201, resp.text
    document = resp.json()
    assert document["document_type"] == "QUESTIONNAIRE"
    assert document["processing_status"] == "INDEXED"
    assert document["sha256"]

    # Uploading the identical bytes again returns the same Document
    # (Contract §2.2 duplicate-checksum rule), not a new one.
    resp = client.post(
        f"/api/v1/cases/{case_id}/documents",
        files=files,
        data={"document_type": "QUESTIONNAIRE"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] == document["id"]

    # 4. Identify questions -> two questions, in source (workbook) order
    resp = client.get(f"/api/v1/cases/{case_id}/questions")
    assert resp.status_code == 200
    questions = resp.json()
    assert len(questions) == 2
    assert questions[0]["question_text"] == "Report annual electricity consumption."
    assert questions[1]["question_text"] == "Describe your anti-bribery policy."

    # Before any evidence document exists, both questions are MISSING —
    # there are zero evidence_links, which is the only honest answer the
    # deterministic rule engine can give (app/services/rules.py).
    assert questions[0]["evidence_status"] == "MISSING"
    assert questions[0]["review_status"] == "UNREVIEWED"
    assert questions[0]["evidence_location"] is None

    question_id = questions[0]["id"]

    # 5. Upload a small evidence document (plain text -> one document_chunks
    #    row per non-blank line, per app/routers/documents.py). It contains
    #    a line whose keywords overlap the electricity question, and nothing
    #    matching the anti-bribery question.
    evidence_text = (
        "Employee headcount summary for FY2025.\n"
        "Total electricity consumption: 12,840 kWh at the Selangor site in January 2025.\n"
        "Waste diverted from landfill: 42 tonnes.\n"
    )
    files = {"file": ("utility-bill.txt", evidence_text.encode("utf-8"), "text/plain")}
    resp = client.post(
        f"/api/v1/cases/{case_id}/documents",
        files=files,
        data={"document_type": "UTILITY_BILL"},
    )
    assert resp.status_code == 201, resp.text
    evidence_document = resp.json()
    assert evidence_document["processing_status"] == "INDEXED"

    # 6. GET questions again: the electricity question now has a
    #    server-resolved PARTIAL status and a real source_location that the
    #    AI pipeline never supplied (it only ever returned a chunk_id —
    #    packages/ai-pipeline/src/ai_pipeline/analyze.py). The anti-bribery
    #    question has no keyword overlap with the evidence text and stays
    #    MISSING, proving this isn't a blanket "any upload -> PARTIAL" bug.
    resp = client.get(f"/api/v1/cases/{case_id}/questions")
    assert resp.status_code == 200
    questions = resp.json()
    electricity_q = next(q for q in questions if q["id"] == question_id)
    bribery_q = next(q for q in questions if q["id"] != question_id)

    assert electricity_q["evidence_status"] == "PARTIAL"
    assert electricity_q["evidence_location"] is not None
    assert electricity_q["evidence_location"]["type"] == "paragraph"
    assert isinstance(electricity_q["evidence_location"]["paragraph_index"], int)
    assert electricity_q["status_reason"]
    assert "utility-bill.txt" in electricity_q["status_reason"]

    assert bribery_q["evidence_status"] == "MISSING"
    assert bribery_q["evidence_location"] is None

    # 7. Persist a SUBMISSION action
    resp = client.post(
        f"/api/v1/cases/{case_id}/actions",
        json={
            "question_id": question_id,
            "type": "SUBMISSION",
            "title": "Collect missing electricity bills",
            "owner_name": "Finance Manager",
            "owner_role": "Finance",
            "next_step": "Download the remaining monthly bills.",
            "deadline_at": "2026-09-30T00:00:00Z",
        },
    )
    assert resp.status_code == 201, resp.text
    action = resp.json()
    assert action["type"] == "SUBMISSION"
    assert action["status"] == "TODO"
    action_id = action["id"]

    # 8. Persist and reload: re-fetch case, questions, and actions
    #    independently to prove nothing lives only in-memory.
    resp = client.get(f"/api/v1/cases/{case_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == case_id

    resp = client.get(f"/api/v1/cases/{case_id}/questions")
    reloaded_questions = resp.json()
    assert len(reloaded_questions) == 2
    reloaded_electricity_q = next(q for q in reloaded_questions if q["id"] == question_id)
    assert reloaded_electricity_q["evidence_status"] == "PARTIAL"
    assert reloaded_electricity_q["evidence_location"]["paragraph_index"] == 1

    resp = client.get(f"/api/v1/cases/{case_id}/actions")
    assert resp.status_code == 200
    reloaded_actions = resp.json()
    assert len(reloaded_actions) == 1
    assert reloaded_actions[0]["id"] == action_id
    assert reloaded_actions[0]["title"] == "Collect missing electricity bills"


def test_case_not_found_error_envelope(client):
    resp = client.get("/api/v1/cases/does-not-exist")
    assert resp.status_code == 404
    body = resp.json()["detail"]
    assert body["error"]["code"] == "CASE_NOT_FOUND"


def test_upload_rejects_unknown_document_type(client):
    resp = client.post("/api/v1/cases", json={"title": "Case"})
    case_id = resp.json()["id"]

    resp = client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": ("x.xlsx", b"not a real xlsx", "application/octet-stream")},
        data={"document_type": "NOT_A_REAL_TYPE"},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"]["code"] == "VALIDATION_ERROR"


def test_malformed_questionnaire_marked_needs_manual_review(client):
    resp = client.post("/api/v1/cases", json={"title": "Case"})
    case_id = resp.json()["id"]

    # A workbook missing the required headers is a legitimate ValueError from
    # ai_pipeline.parse_document(), not a crash — the endpoint must catch it
    # and mark the document NEEDS_MANUAL_REVIEW rather than 500ing.
    wb = Workbook()
    ws = wb.active
    ws.append(["id", "text"])  # wrong header names
    buf = io.BytesIO()
    wb.save(buf)

    resp = client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={
            "file": (
                "bad.xlsx",
                buf.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        data={"document_type": "QUESTIONNAIRE"},
    )
    assert resp.status_code == 201, resp.text
    document = resp.json()
    assert document["processing_status"] == "NEEDS_MANUAL_REVIEW"
    assert document["error"]

    resp = client.get(f"/api/v1/cases/{case_id}/questions")
    assert resp.json() == []


def test_evidence_document_with_no_keyword_overlap_leaves_questions_missing(client):
    resp = client.post("/api/v1/cases", json={"title": "Case"})
    case_id = resp.json()["id"]

    xlsx_bytes = _build_questionnaire_xlsx(
        [{"question_text": "What is the total headcount at year end?", "is_required": True}]
    )
    resp = client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={
            "file": (
                "q.xlsx",
                xlsx_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        data={"document_type": "QUESTIONNAIRE"},
    )
    assert resp.status_code == 201, resp.text

    resp = client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": ("unrelated.txt", b"Totally unrelated content here.", "text/plain")},
        data={"document_type": "OTHER"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["processing_status"] == "INDEXED"

    resp = client.get(f"/api/v1/cases/{case_id}/questions")
    questions = resp.json()
    assert len(questions) == 1
    assert questions[0]["evidence_status"] == "MISSING"
    assert questions[0]["evidence_location"] is None
