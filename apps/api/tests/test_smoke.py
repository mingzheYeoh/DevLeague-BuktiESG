"""Smoke test for the First Vertical Slice:

    Create Case -> upload one questionnaire -> identify questions
                -> persist a SUBMISSION action -> persist/reload

See docs/spec/README-Team-Specs.md, "First Vertical Slice".
"""

from __future__ import annotations

import json


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

    # 3. Upload one questionnaire (JSON stub format), out of order on purpose
    #    to prove question_order (SPEC-AMD-007) reflects source order, not id.
    questionnaire_rows = [
        {
            "question_text": "Report annual electricity consumption.",
            "external_question_id": "Q-E-01",
            "section": "Environment",
            "is_required": True,
            "pillar": "E",
        },
        {
            "question_text": "Describe your anti-bribery policy.",
            "external_question_id": "Q-G-01",
            "section": "Governance",
            "is_required": True,
            "pillar": "G",
        },
    ]
    files = {
        "file": (
            "questionnaire.json",
            json.dumps(questionnaire_rows).encode("utf-8"),
            "application/json",
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

    # 4. Identify questions -> two questions, in source order
    resp = client.get(f"/api/v1/cases/{case_id}/questions")
    assert resp.status_code == 200
    questions = resp.json()
    assert len(questions) == 2
    assert questions[0]["question_text"] == "Report annual electricity consumption."
    assert questions[0]["pillar"] == "E"
    assert questions[1]["question_text"] == "Describe your anti-bribery policy."

    # Stubbed rule engine: no evidence pipeline exists in this slice, so
    # every fresh question is deterministically MISSING (AGENTS.md §3.2).
    assert questions[0]["evidence_status"] == "MISSING"
    assert questions[0]["review_status"] == "UNREVIEWED"

    question_id = questions[0]["id"]

    # 5. Persist a SUBMISSION action
    resp = client.post(
        f"/api/v1/cases/{case_id}/actions",
        json={
            "question_id": question_id,
            "type": "SUBMISSION",
            "title": "Collect missing electricity bills",
            "owner_name": "Finance Manager",
            "owner_role": "Finance",
            "next_step": "Download the remaining monthly bills.",
        },
    )
    assert resp.status_code == 201, resp.text
    action = resp.json()
    assert action["type"] == "SUBMISSION"
    assert action["status"] == "TODO"
    action_id = action["id"]

    # 6. Persist and reload: re-fetch case, questions, and actions
    #    independently to prove nothing lives only in-memory.
    resp = client.get(f"/api/v1/cases/{case_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == case_id

    resp = client.get(f"/api/v1/cases/{case_id}/questions")
    reloaded_questions = resp.json()
    assert len(reloaded_questions) == 2
    assert reloaded_questions[0]["id"] == question_id

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
        files={"file": ("x.json", b"[]", "application/json")},
        data={"document_type": "NOT_A_REAL_TYPE"},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"]["code"] == "VALIDATION_ERROR"


def test_malformed_questionnaire_marked_needs_manual_review(client):
    resp = client.post("/api/v1/cases", json={"title": "Case"})
    case_id = resp.json()["id"]

    resp = client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": ("bad.json", b"[not valid json", "application/json")},
        data={"document_type": "QUESTIONNAIRE"},
    )
    assert resp.status_code == 201, resp.text
    document = resp.json()
    assert document["processing_status"] == "NEEDS_MANUAL_REVIEW"
    assert document["error"]

    resp = client.get(f"/api/v1/cases/{case_id}/questions")
    assert resp.json() == []
