"""`questions.evidence_requirement_json` — written at parse time, at last.

The column was read in two places and written in none. Empty, it silently
disabled four separate rules: the C-15 unreadable-document keyword gate, the
VERIFIED period-coverage check, the VERIFIED scope-match check, and OUTDATED's
ability to measure against a question's own period.

Only the keywords are populated here, and the reason is measured rather than
assumed: with `required_period_start`/`_end` set, the period-coverage check
demands `link.period_start <= required_start and link.period_end >=
required_end`, and no link carries a period because nothing extracts one from a
chunk. Setting it turns every VERIFIED back into PARTIAL, and OUTDATED with it
— the `source_date` fallback only applies when the question states no period.
See `test_a_required_period_would_break_both`, which pins that.
"""

from __future__ import annotations

import io
import json
from datetime import date

from openpyxl import Workbook

from app.services.rules import EvidenceCandidate, EvidenceRequirement, compute_evidence_status


def _questionnaire(*texts: str) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(["external_question_id", "question_text", "section", "is_required"])
    for i, text in enumerate(texts, start=1):
        ws.append([f"Q-{i}", text, "Social", True])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_a_parsed_question_carries_its_requirement_keywords(client, db_session):
    from app.models import Question

    case_id = client.post("/api/v1/cases", json={"title": "Requirement"}).json()["id"]
    client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": ("q.xlsx", _questionnaire(
            "Report the number of work-related injuries recorded during the year.",
            "Describe the anti-bribery controls in place across the business.",
        ), "application/octet-stream")},
        data={"document_type": "QUESTIONNAIRE"},
    )

    questions = db_session.query(Question).order_by(Question.question_order).all()
    assert len(questions) == 2

    first = json.loads(questions[0].evidence_requirement_json)
    assert "injuries" in first["keywords"]
    # Stopwords and short words are not requirements.
    assert "the" not in first["keywords"]
    assert not first.get("required_period_start")
    assert not first.get("required_scope")


def test_a_question_whose_only_relevant_file_is_unreadable_says_so(client):
    """The difference between "no evidence" and "evidence we could not read".

    This is what the keywords are for. Without them `_find_relevant_unreadable`
    returns None on its first line and the question reports MISSING, which
    tells the reviewer to go and find a document they have already uploaded.
    """
    case_id = client.post("/api/v1/cases", json={"title": "Unreadable only"}).json()["id"]
    client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": ("q.xlsx", _questionnaire(
            "Report the number of work-related injuries recorded during the year.",
        ), "application/octet-stream")},
        data={"document_type": "QUESTIONNAIRE"},
    )

    # The only supporting file, and the parser cannot read a word of it. Its
    # filename is all the engine has to go on, which is exactly the C-15 case.
    doc = client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": ("injuries-register-2025.pdf", b"%PDF-1.4\nnot really a pdf\n",
                        "application/pdf")},
        data={"document_type": "SAFETY_RECORD"},
    ).json()
    assert doc["processing_status"] == "NEEDS_MANUAL_REVIEW"

    questions = client.get(f"/api/v1/cases/{case_id}/questions").json()
    questions = questions["items"] if isinstance(questions, dict) else questions
    assert questions[0]["evidence_status"] == "NEEDS_MANUAL_REVIEW"
    assert "injuries-register-2025.pdf" in (questions[0]["status_reason"] or "")


def test_a_required_period_would_break_both_verified_and_outdated(client):
    """Why `required_period_start`/`_end` are not populated, pinned.

    Inheriting the Case's reporting period reads like an obvious improvement.
    It is a regression, and this test is here so that the next person to reach
    for it sees the cost before paying it rather than after.
    """
    def link(**kw):
        base = dict(
            link_id="l1", link_status="CANDIDATE", extraction_valid=True,
            claim_supported="Keyword overlap with question terms: injuries",
            quoted_excerpt="Recordable work-related injuries: 2.",
            # NULL, as every link the running system writes is: nothing
            # extracts a period from a chunk.
            period_start=None, period_end=None,
            scope_description=None, unit=None, value=None, source_date=None,
            source_location='{"type": "paragraph", "paragraph_index": 3}',
        )
        base.update(kw)
        return EvidenceCandidate(**base)

    def status(candidates, requirement):
        return compute_evidence_status(
            candidates=candidates, requirement=requirement, unreadable_documents=[],
            current_status="PARTIAL", not_applicable_reason=None, reviewer_name=None,
        ).status

    no_period = EvidenceRequirement(keywords=("injuries",))
    with_period = EvidenceRequirement(
        keywords=("injuries",),
        required_period_start=date(2025, 1, 1),
        required_period_end=date(2025, 12, 31),
    )

    accepted = [link(link_status="ACCEPTED")]
    stale = [link(source_date=date(2022, 12, 31))]

    assert status(accepted, no_period) == "VERIFIED"
    assert status(stale, no_period) == "OUTDATED"

    # Both collapse, because the period check needs link periods that do not exist.
    assert status(accepted, with_period) == "PARTIAL"
    assert status(stale, with_period) == "PARTIAL"
