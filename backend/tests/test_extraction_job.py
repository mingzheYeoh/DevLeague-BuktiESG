"""Extraction as a background job, and the CONFLICTING it finally makes reachable.

Extraction cannot run inside the upload request: measured against
deepseek-v4-pro, two to three chunks take 12-22 seconds, so a 21-document case
at 175 chunks would add roughly three minutes to an upload. `processing_jobs`,
`claim_next_job` and `worker.py` were built for exactly this and had never been
used for anything - every job so far ran inline.

Values are stored on `document_chunks`, not on `evidence_links`. A measurement
is a property of the fragment that reports it, and links are re-created every
time another document is indexed; storing it on the link would mean re-asking
the model for a number it had already read.
"""

from __future__ import annotations

import io

import pytest
from openpyxl import Workbook

from ai_pipeline import Extracted


class FakeExtractor:
    """Answers from a table keyed by chunk text. No network, no credential."""

    def __init__(self, by_text: dict[str, Extracted]):
        self.by_text = by_text
        self.calls: list[list[str]] = []

    def extract(self, chunk_texts: list[str]) -> list[Extracted]:
        self.calls.append(list(chunk_texts))
        return [self.by_text.get(t.strip(), Extracted()) for t in chunk_texts]


def _questionnaire(*texts: str) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(["external_question_id", "question_text", "section", "is_required"])
    for i, text in enumerate(texts, start=1):
        ws.append([f"Q-{i}", text, "Environment", True])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.fixture()
def waste_case(client):
    """One question about scheduled waste, and two documents that disagree."""
    case_id = client.post("/api/v1/cases", json={"title": "Conflict"}).json()["id"]
    client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": ("q.xlsx", _questionnaire(
            "Report total scheduled waste generated in metric tonnes for the year."
        ), "application/octet-stream")},
        data={"document_type": "QUESTIONNAIRE"},
    )
    return case_id


def _upload(client, case_id, name, body):
    return client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": (name, body, "text/plain")},
        data={"document_type": "WASTE_RECORD"},
    ).json()


def test_indexing_a_document_queues_an_extraction_job(client, db_session, waste_case):
    """Queued, not run. The upload returns as soon as the bytes are stored and
    indexed; the model is somebody else's problem."""
    from app.models import ProcessingJob

    doc = _upload(client, waste_case, "a03.txt", b"Total scheduled waste FY2025: 12.6 tonnes.\n")

    jobs = (
        db_session.query(ProcessingJob)
        .filter(ProcessingJob.document_id == doc["id"], ProcessingJob.job_type == "EXTRACT_VALUES")
        .all()
    )
    assert len(jobs) == 1
    assert jobs[0].status == "QUEUED", "extraction must not run inside the upload"


def test_running_the_job_writes_the_measurement_onto_the_chunk(client, db_session, waste_case):
    from app.models import DocumentChunk
    from app.services import jobs as jobs_service

    doc = _upload(client, waste_case, "a03.txt", b"Total scheduled waste FY2025: 12.6 tonnes.\n")
    fake = FakeExtractor(
        {"Total scheduled waste FY2025: 12.6 tonnes.": Extracted(value="12.6", unit="t")}
    )

    jobs_service.run_extraction_jobs(db_session, extractor=fake)

    chunk = (
        db_session.query(DocumentChunk).filter(DocumentChunk.document_id == doc["id"]).one()
    )
    assert chunk.extracted_value == "12.6"
    assert chunk.extracted_unit == "t"


def test_two_documents_reporting_different_values_make_the_question_conflicting(
    client, db_session, waste_case
):
    """The point of all of this.

    A-03 reports 12.6 tonnes and C-01 reports 18.4 for the same site and the
    same year. That contradiction is the most useful thing in the sample set
    and the engine could not see it, because no link carried a value.
    """
    from app.services import jobs as jobs_service

    def status() -> str:
        payload = client.get(f"/api/v1/cases/{waste_case}/questions").json()
        return (payload["items"] if isinstance(payload, dict) else payload)[0]["evidence_status"]

    _upload(client, waste_case, "a03.txt", b"Total scheduled waste FY2025: 12.6 tonnes.\n")
    _upload(client, waste_case, "c01.txt", b"Total scheduled waste FY2025: 18.4 metric tonnes.\n")
    assert status() == "PARTIAL", "without values the engine has nothing to compare"

    same_scope_and_period = dict(scope="Klang plant", period_start=None, period_end=None)
    jobs_service.run_extraction_jobs(
        db_session,
        extractor=FakeExtractor(
            {
                "Total scheduled waste FY2025: 12.6 tonnes.":
                    Extracted(value="12.6", unit="t", **same_scope_and_period),
                "Total scheduled waste FY2025: 18.4 metric tonnes.":
                    Extracted(value="18.4", unit="t", **same_scope_and_period),
            }
        ),
    )

    assert status() == "CONFLICTING"


def test_a_chunk_the_model_could_not_measure_stays_empty_and_is_not_retried(
    client, db_session, waste_case
):
    """A null is an answer. Re-asking would cost money to be told the same
    thing, so a job that completes is done regardless of what it found."""
    from app.models import ProcessingJob

    _upload(client, waste_case, "prose.txt", b"The company is committed to reducing waste.\n")
    fake = FakeExtractor({})

    from app.services import jobs as jobs_service
    jobs_service.run_extraction_jobs(db_session, extractor=fake)
    first_call_count = len(fake.calls)

    jobs_service.run_extraction_jobs(db_session, extractor=fake)

    assert len(fake.calls) == first_call_count, "a completed extraction must not re-run"
    assert (
        db_session.query(ProcessingJob)
        .filter(ProcessingJob.job_type == "EXTRACT_VALUES", ProcessingJob.status == "SUCCEEDED")
        .count()
        >= 1
    )


def test_extraction_moves_the_citation_off_a_row_with_no_measurement(client, db_session):
    """The end-to-end shape of the tie-break.

    A spreadsheet's header row ties with its data rows on keyword overlap -
    the header holds exactly the vocabulary the question uses - and wins by
    being first. It is also the one row that can never carry a number. Once
    extraction knows which rows do, the citation moves.
    """
    from app.models import DocumentChunk, EvidenceLink, Question
    from app.services import jobs as jobs_service

    case_id = client.post("/api/v1/cases", json={"title": "Tie"}).json()["id"]
    client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": ("q.xlsx", _questionnaire(
            "Report total scheduled waste generated in metric tonnes."
        ), "application/octet-stream")},
        data={"document_type": "QUESTIONNAIRE"},
    )
    header = "Waste code | Description | Metric tonnes | Year"
    row = "Total scheduled waste | All codes, FY2025 | 12.6 | 2025"
    _upload(client, case_id, "a03.txt", f"{header}\n{row}\n".encode())

    def cited_text() -> str:
        question = db_session.query(Question).one()
        link = (
            db_session.query(EvidenceLink)
            .filter(EvidenceLink.question_id == question.id)
            .one()
        )
        return db_session.get(DocumentChunk, link.chunk_id).text

    assert cited_text() == header, "the header wins the tie before extraction"

    jobs_service.run_extraction_jobs(
        db_session,
        extractor=FakeExtractor({row: Extracted(value="12.6", unit="t")}),
    )

    assert cited_text() == row
