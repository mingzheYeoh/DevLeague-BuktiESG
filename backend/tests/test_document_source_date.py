"""`source_date` on upload, and the OUTDATED status it makes reachable.

The rule engine has always known how to decide OUTDATED: `_is_outdated` in
`app/services/rules.py` compares a candidate's `source_date` (falling back to
`period_end`) against the question's required period, or against a 24-month
threshold when the question states no period (DEC-007 / Main Spec 6.2). The
column existed, and `jobs.py` already passed `doc.source_date` into every
`EvidenceCandidate`.

What did not exist was any way to fill it in. The upload endpoint accepted a
file and a document type and nothing else, so `documents.source_date` was NULL
for every row ever written, and the whole OUTDATED branch was dead code.
"""

from __future__ import annotations

import io

from openpyxl import Workbook


def _case(client, title: str = "Source date") -> str:
    return client.post("/api/v1/cases", json={"title": title}).json()["id"]


def test_upload_stores_the_source_date_it_was_given(client):
    case_id = _case(client)

    created = client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": ("policy.txt", b"Approved by the board.", "text/plain")},
        data={"document_type": "POLICY", "source_date": "2019-06-30"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["source_date"] == "2019-06-30"

    # Read it back rather than trusting the write response.
    listed = client.get(f"/api/v1/cases/{case_id}/documents").json()
    rows = listed["items"] if isinstance(listed, dict) else listed
    assert [d["source_date"] for d in rows] == ["2019-06-30"]


def test_an_unparseable_source_date_is_refused(client):
    """A date the server cannot read must fail the upload, not be dropped.

    Dropping it reads to the uploader as an accepted date, and the document is
    then treated as current for the rest of its life - the exact failure this
    field exists to prevent.
    """
    case_id = _case(client)

    resp = client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": ("policy.txt", b"Approved by the board.", "text/plain")},
        data={"document_type": "POLICY", "source_date": "30/06/2019"},
    )

    assert resp.status_code == 422, resp.text
    error = resp.json()["detail"]["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "30/06/2019" in error["message"]
    assert error["details"]["expected_format"] == "YYYY-MM-DD"

    # And nothing was stored.
    listed = client.get(f"/api/v1/cases/{case_id}/documents").json()
    assert (listed["items"] if isinstance(listed, dict) else listed) == []


def _questionnaire(question_text: str) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(["external_question_id", "question_text", "section", "is_required"])
    ws.append(["Q-1", question_text, "Environment", True])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_evidence_older_than_the_threshold_makes_the_question_outdated(client):
    """The point of the field: a stale document stops reading as current.

    The question states no required period, so the engine falls back to the
    24-month threshold (DEC-007), measured from `source_date`. Before this
    field existed the fallback had nothing to measure and every document,
    however old, counted as current evidence.
    """
    case_id = _case(client, "Waste FY2025")

    client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": ("q.xlsx", _questionnaire(
            "What were the total scheduled waste tonnes disposed in the reporting year?"
        ), "application/octet-stream")},
        data={"document_type": "QUESTIONNAIRE"},
    )

    client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": ("waste-2018.txt", b"Scheduled waste disposed: 12.6 tonnes.", "text/plain")},
        data={"document_type": "WASTE_RECORD", "source_date": "2018-12-31"},
    )

    payload = client.get(f"/api/v1/cases/{case_id}/questions").json()
    questions = payload["items"] if isinstance(payload, dict) else payload
    assert len(questions) == 1, questions
    assert questions[0]["evidence_status"] == "OUTDATED"
