"""The synthetic A-tier pack can support every question in the demo workbook."""

from pathlib import Path

from app.services import storage


SAMPLE = Path(__file__).resolve().parents[2] / "sample"
EXPECTED = {
    "Q-E-01": "A-02", "Q-E-02": "A-02", "Q-E-03": "A-08",
    "Q-E-04": "A-09", "Q-E-05": "A-10", "Q-E-06": "A-11",
    "Q-E-07": "A-03", "Q-E-08": "A-03", "Q-E-09": "A-12",
    "Q-E-10": "A-14", "Q-S-01": "A-07", "Q-S-02": "A-04",
    "Q-S-03": "A-07", "Q-S-04": "A-07", "Q-S-05": "A-06",
    "Q-S-06": "A-06", "Q-S-07": "A-15", "Q-G-01": "A-16",
    "Q-G-02": "A-05", "Q-G-03": "A-13",
}

ANSWERS = {
    "Q-E-01": "58.8 tCO2e of Scope 1 emissions in FY2025.",
    "Q-E-02": "1,367.0 tCO2e of Scope 2 emissions, using the Energy Commission's 2024 Peninsular grid factor of 0.740 tCO2e/MWh.",
    "Q-E-03": "0.0057032 tCO2e per finished production unit (1,425.8 tCO2e / 250,000 units).",
    "Q-E-04": "2,081,380 kWh total: 1,847,300 grid electricity, 0 renewable fuel, 234,080 non-renewable fuel.",
    "Q-E-05": "118,000 kWh saved through LED, compressed-air, and chiller initiatives.",
    "Q-E-06": "8,000 cubic metres withdrawn, all from municipal supply; groundwater and surface water 0.",
    "Q-E-07": "214.7 tonnes generated; 138.2 tonnes diverted and 76.5 tonnes directed to disposal.",
    "Q-E-08": "12.6 tonnes scheduled waste: SW410 4.8, SW305 2.9, SW110 3.1, SW409 1.8 tonnes.",
    "Q-E-09": "23.75% recycled input by mass (190 of 800 tonnes).",
    "Q-E-10": "44 tonnes of packaging: cardboard 22, paper 4, plastic 3, wood 15 tonnes.",
    "Q-S-01": "0 child-labour and 0 forced-labour incidents in FY2025.",
    "Q-S-02": "12.0 average training hours per employee (3,216 hours / 268 employees).",
    "Q-S-03": "268 employees; 12.7% turnover (34 leavers / 268 employees).",
    "Q-S-04": "35.8% women and 64.2% men; age bands under 30 27.6%, 30-50 59.0%, over 50 13.4%; women in management 37.5%.",
    "Q-S-05": "0 fatalities, 4 injuries; LTIFR 5.35 per million hours based on 3 lost-time injuries and 561,000 hours worked.",
    "Q-S-06": "268 of 268 employees trained on health and safety (100%).",
    "Q-S-07": "RM48,000 community investment and donations: RM42,000 cash and RM6,000 in kind.",
    "Q-G-01": "Code of Conduct v2.0 and Anti-Bribery, Anti-Corruption and Whistleblowing Policy v4.0, approved 14 February 2025.",
    "Q-G-02": "254 of 268 employees completed anti-bribery and anti-corruption training (94.8%).",
    "Q-G-03": "0 substantiated privacy complaints and 0 confirmed customer-data losses; one encrypted-device theft was investigated.",
}

EXPECTED_EXCERPT = {
    "Q-E-07": "214.7",
    "Q-E-08": "12.6",
    "Q-S-01": "0 child labour and 0 forced labour",
    "Q-S-02": "3216",
    "Q-S-04": "35.8%",
    "Q-S-05": "fatalities 0",
}

SOURCE_DATES = {
    "A-05": "2025-02-14", "A-06": "2026-01-12",
    "A-08": "2026-01-16", "A-09": "2026-01-18",
    "A-10": "2026-01-20", "A-11": "2026-01-19",
    "A-12": "2026-01-22", "A-13": "2026-01-21",
    "A-14": "2026-01-17", "A-15": "2026-01-23",
    "A-16": "2025-02-14",
}


def test_complete_sample_upload_and_review(client, monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path)
    case = client.post("/api/v1/cases", json={"title": "Complete synthetic trial"})
    assert case.status_code == 201, case.text
    case_id = case.json()["id"]
    upload_url = f"/api/v1/cases/{case_id}/documents"

    questionnaire = SAMPLE / "questionnaire" / "customer-esg-questionnaire-2026.xlsx"
    response = client.post(
        upload_url,
        files={"file": (questionnaire.name, questionnaire.read_bytes())},
        data={"document_type": "QUESTIONNAIRE"},
    )
    assert response.status_code == 201, response.text
    assert response.json()["processing_status"] == "INDEXED"

    document_ids = {}
    for path in sorted((SAMPLE / "evidence").glob("A-*")):
        response = client.post(
            upload_url,
            files={"file": (path.name, path.read_bytes())},
            data={
                "document_type": "OTHER",
                "source_date": SOURCE_DATES.get(path.name[:4], "2025-12-31"),
            },
        )
        assert response.status_code == 201, f"{path.name}: {response.text}"
        assert response.json()["processing_status"] == "INDEXED", path.name
        document_ids[path.name[:4]] = response.json()["id"]

    assert len(document_ids) == 16

    questions = client.get(f"/api/v1/cases/{case_id}/questions").json()
    assert len(questions) == len(EXPECTED) == len(ANSWERS) == 20
    candidate_count = 0
    for question in questions:
        qid = question["external_question_id"]
        links = client.get(
            f"/api/v1/cases/{case_id}/questions/{question['id']}/evidence-links"
        ).json()
        candidate_count += len(links)
        link = next((link for link in links if link["document_id"] == document_ids[EXPECTED[qid]]), None)
        assert link is not None, qid
        assert question["evidence_status"] == "PARTIAL", qid
        if qid in EXPECTED_EXCERPT:
            assert EXPECTED_EXCERPT[qid] in (question["evidence_excerpt"] or ""), qid

        accepted = client.post(f"/api/v1/cases/{case_id}/evidence-links/{link['id']}/accept")
        assert accepted.status_code == 200, (qid, accepted.text)
        reviewed = client.post(
            f"/api/v1/cases/{case_id}/questions/{question['id']}/review",
            json={"action": "EDIT", "edited_answer": ANSWERS[qid]},
        )
        assert reviewed.status_code == 200, (qid, reviewed.text)
        assert reviewed.json()["review_status"] == "HUMAN_CONFIRMED", qid

    assert candidate_count <= 80, f"too many weak keyword candidates: {candidate_count}"

    refreshed = client.get(f"/api/v1/cases/{case_id}/questions").json()
    assert all(q["evidence_status"] == "VERIFIED" for q in refreshed)
    assert client.get(f"/api/v1/cases/{case_id}/readiness").json()[
        "confirmed_required_questions"
    ] == 14
