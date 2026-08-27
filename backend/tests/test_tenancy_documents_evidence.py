"""Documents and evidence links are reachable only through their own case."""


def _make_case(c):
    return c.post("/api/v1/cases", json={"title": "Questionnaire"}).json()["id"]


def _upload_evidence(c, case_id, name="A-06-safety.txt", body=b"Injuries: 4."):
    return c.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": (name, body, "text/plain")},
        data={"document_type": "SAFETY_RECORD"},
    ).json()["id"]


def test_listing_another_organizations_documents_is_404(client, client_other_org):
    case_id = _make_case(client)
    assert client_other_org.get(f"/api/v1/cases/{case_id}/documents").status_code == 404


def test_downloading_another_organizations_file_is_404(client, client_other_org):
    case_id = _make_case(client)
    document_id = _upload_evidence(client, case_id)
    response = client_other_org.get(
        f"/api/v1/cases/{case_id}/documents/{document_id}/content"
    )
    assert response.status_code == 404


def test_deleting_another_organizations_document_is_404(client, client_other_org):
    case_id = _make_case(client)
    document_id = _upload_evidence(client, case_id)
    response = client_other_org.delete(f"/api/v1/cases/{case_id}/documents/{document_id}")
    assert response.status_code == 404


def test_a_document_cannot_be_reached_through_another_case_of_your_own(client):
    # The pre-existing guarantee in _load_document, kept intact by the change:
    # it must still refuse a document that belongs to a different case, even
    # when both cases are yours.
    first, second = _make_case(client), _make_case(client)
    document_id = _upload_evidence(client, first)
    response = client.get(f"/api/v1/cases/{second}/documents/{document_id}/content")
    assert response.status_code == 404


def test_listing_another_organizations_evidence_links_is_404(client, client_other_org):
    # The endpoint that had no case check at all. Before this task it verified
    # only that the question belonged to the case named in the URL - never that
    # the case belonged to the caller.
    case_id = _make_case(client)
    response = client_other_org.get(
        f"/api/v1/cases/{case_id}/questions/any-question-id/evidence-links"
    )
    assert response.status_code == 404
    # Both a correct implementation (case check fails first) and the original,
    # entirely unguarded implementation (question lookup fails on a fabricated id)
    # return 404. Only the error code distinguishes them: CASE_NOT_FOUND means
    # the case was checked and rejected before attempting to resolve the question;
    # QUESTION_NOT_FOUND means the question was resolved without authorising the case.
    assert response.json()["detail"]["error"]["code"] == "CASE_NOT_FOUND"
