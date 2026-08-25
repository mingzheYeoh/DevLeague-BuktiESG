"""Document read endpoints — parsed chunks and raw file content.

These two exist so a reviewer can actually open the evidence a citation points
at. Both hand back user-uploaded material, so the tests here care as much about
what they refuse as about what they return.
"""

from __future__ import annotations

import io

import pytest
from openpyxl import Workbook


def _case(client, title: str = "Preview") -> str:
    return client.post("/api/v1/cases", json={"title": title}).json()["id"]


def _upload(client, case_id: str, name: str, data: bytes, doc_type: str = "OTHER") -> dict:
    resp = client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": (name, data, "application/octet-stream")},
        data={"document_type": doc_type},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _xlsx_bytes() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "FY2025"
    ws.append(["Month", "Recycled (kg)"])
    ws.append(["2025-01", 7360])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# Parsed chunks
# --------------------------------------------------------------------------- #


def test_plain_text_chunks_are_one_per_line_and_ordered(client):
    case_id = _case(client)
    doc = _upload(
        client,
        case_id,
        "register.txt",
        b"First line.\n\nSecond line.\n   \nThird line.\n",
        "SAFETY_RECORD",
    )

    resp = client.get(f"/api/v1/cases/{case_id}/documents/{doc['id']}/chunks")
    assert resp.status_code == 200
    chunks = resp.json()

    assert [c["text"] for c in chunks] == ["First line.", "Second line.", "Third line."]
    assert [c["sequence_no"] for c in chunks] == [0, 1, 2]
    # A line of plain text has no page, sheet or heading.
    assert all(c["page_number"] is None for c in chunks)
    assert all(c["sheet_name"] is None for c in chunks)
    assert all(c["heading_path"] == [] for c in chunks)


def test_spreadsheet_chunks_carry_sheet_and_cell_range(client):
    case_id = _case(client)
    doc = _upload(client, case_id, "waste.xlsx", _xlsx_bytes(), "WASTE_RECORD")

    chunks = client.get(f"/api/v1/cases/{case_id}/documents/{doc['id']}/chunks").json()

    assert len(chunks) == 2
    assert all(c["sheet_name"] == "FY2025" for c in chunks)
    assert [c["cell_range"] for c in chunks] == ["A1:B1", "A2:B2"]
    assert "7360" in chunks[1]["text"]


def test_a_document_that_failed_to_parse_has_no_chunks_but_still_answers(client):
    """An unreadable file must not 500 the chunks endpoint. The empty list plus
    the document's own error message is the honest answer."""
    case_id = _case(client)
    doc = _upload(client, case_id, "scan.pdf", b"%PDF-1.4\nnot really a pdf\n", "SAFETY_RECORD")

    assert doc["processing_status"] == "NEEDS_MANUAL_REVIEW"
    assert doc["error"]

    resp = client.get(f"/api/v1/cases/{case_id}/documents/{doc['id']}/chunks")
    assert resp.status_code == 200
    assert resp.json() == []


def test_chunks_refuse_a_document_belonging_to_another_case(client):
    """The case id in the path is the authorisation boundary. Knowing a document
    id must not be enough to read it through a different case's URL."""
    case_a = _case(client, "Case A")
    case_b = _case(client, "Case B")
    doc = _upload(client, case_a, "a.txt", b"Case A content.\n")

    resp = client.get(f"/api/v1/cases/{case_b}/documents/{doc['id']}/chunks")
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"]["code"] == "DOCUMENT_NOT_FOUND"


def test_chunks_404_for_unknown_case_and_document(client):
    case_id = _case(client)

    resp = client.get(f"/api/v1/cases/nope/documents/nope/chunks")
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"]["code"] == "CASE_NOT_FOUND"

    resp = client.get(f"/api/v1/cases/{case_id}/documents/nope/chunks")
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"]["code"] == "DOCUMENT_NOT_FOUND"


# --------------------------------------------------------------------------- #
# Raw content
# --------------------------------------------------------------------------- #


def test_content_returns_the_exact_bytes_that_were_uploaded(client):
    case_id = _case(client)
    payload = b"Total days lost to work-related injury: 11.\n"
    doc = _upload(client, case_id, "register.txt", payload, "SAFETY_RECORD")

    resp = client.get(f"/api/v1/cases/{case_id}/documents/{doc['id']}/content")

    assert resp.status_code == 200
    assert resp.content == payload


@pytest.mark.parametrize(
    ("filename", "expected_type"),
    [
        ("bill.pdf", "application/pdf"),
        ("photo.png", "image/png"),
        ("photo.JPG", "image/jpeg"),
        ("notes.txt", "text/plain; charset=utf-8"),
        ("rows.csv", "text/plain; charset=utf-8"),
    ],
)
def test_previewable_types_are_served_inline(client, filename, expected_type):
    case_id = _case(client)
    doc = _upload(client, case_id, filename, b"some bytes\n")

    resp = client.get(f"/api/v1/cases/{case_id}/documents/{doc['id']}/content")

    assert resp.headers["content-type"] == expected_type
    assert resp.headers["content-disposition"].startswith("inline;")


@pytest.mark.parametrize(
    "filename",
    [
        "evil.html",
        "evil.svg",
        "evil.htm",
        "policy.docx",
        "sheet.xlsx",
        "archive.zip",
        "noextension",
    ],
)
def test_everything_else_is_an_opaque_attachment(client, filename):
    """Anything that could execute script, or that a browser cannot render
    safely, must come back as an octet-stream download.

    `.html` and `.svg` are the ones that matter: served inline they would be
    stored XSS against an API with no authentication.
    """
    case_id = _case(client)
    doc = _upload(client, case_id, filename, b"<script>alert(1)</script>")

    resp = client.get(f"/api/v1/cases/{case_id}/documents/{doc['id']}/content")

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/octet-stream"
    assert resp.headers["content-disposition"].startswith("attachment;")


def test_content_sets_hardening_headers(client):
    case_id = _case(client)
    doc = _upload(client, case_id, "notes.txt", b"hello\n")

    resp = client.get(f"/api/v1/cases/{case_id}/documents/{doc['id']}/content")

    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["content-security-policy"] == "default-src 'none'; sandbox"
    assert resp.headers["cache-control"] == "private, no-store"


def test_content_does_not_trust_the_client_supplied_mime_type(client):
    """The uploader controls `mime_type`. Echoing it back for an inline
    response would hand an attacker the content type of their choice."""
    case_id = _case(client)
    resp = client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": ("payload.bin", b"<script>alert(1)</script>", "text/html")},
        data={"document_type": "OTHER"},
    )
    doc = resp.json()
    assert doc["mime_type"] == "text/html"  # stored as claimed

    served = client.get(f"/api/v1/cases/{case_id}/documents/{doc['id']}/content")
    assert served.headers["content-type"] == "application/octet-stream"
    assert served.headers["content-disposition"].startswith("attachment;")


def test_content_encodes_the_filename_so_it_cannot_inject_a_header(client):
    case_id = _case(client)
    doc = _upload(client, case_id, 'we"ird name.txt', b"hello\n")

    resp = client.get(f"/api/v1/cases/{case_id}/documents/{doc['id']}/content")

    disposition = resp.headers["content-disposition"]
    assert "\n" not in disposition and "\r" not in disposition
    assert "filename*=UTF-8''" in disposition
    # The raw quote never reaches the header unescaped.
    assert 'we"ird' not in disposition


def test_content_refuses_a_document_belonging_to_another_case(client):
    case_a = _case(client, "Case A")
    case_b = _case(client, "Case B")
    doc = _upload(client, case_a, "a.txt", b"Case A content.\n")

    resp = client.get(f"/api/v1/cases/{case_b}/documents/{doc['id']}/content")

    assert resp.status_code == 404
    assert resp.json()["detail"]["error"]["code"] == "DOCUMENT_NOT_FOUND"


def test_content_404s_when_the_row_exists_but_the_file_is_gone(client, db_session):
    """A missing file is a real state — storage is not transactional with the
    database. It must be a clean 404, not a stack trace."""
    from app.models import Document
    from app.services import storage

    case_id = _case(client)
    doc = _upload(client, case_id, "notes.txt", b"hello\n")

    # `db_session` is the same session the app is using, per conftest.
    key = db_session.get(Document, doc["id"]).storage_key
    storage.resolve(key).unlink()

    resp = client.get(f"/api/v1/cases/{case_id}/documents/{doc['id']}/content")
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"]["code"] == "DOCUMENT_CONTENT_MISSING"


# --------------------------------------------------------------------------- #
# Storage path safety
# --------------------------------------------------------------------------- #


def test_storage_resolve_refuses_keys_that_escape_the_root():
    from app.services import storage

    for key in ("../secrets.env", "../../etc/passwd", "case/../../outside.txt"):
        with pytest.raises(storage.StorageKeyOutsideRoot):
            storage.resolve(key)


def test_storage_resolve_accepts_a_normal_key():
    from app.services import storage

    path = storage.resolve("case-1/abc123.pdf")
    assert path.name == "abc123.pdf"
    assert storage.STORAGE_ROOT.resolve() in path.parents


@pytest.mark.parametrize("filename", ["report.pdf", "photo.png", "notes.txt"])
def test_download_forces_an_attachment_for_types_that_would_render_inline(
    client, filename
):
    """`?download=1` is what makes "Download original" save a file.

    The app and this API are on different origins, and a browser ignores the
    `download` attribute on a cross-origin `<a>`. Without this parameter a
    click on an inline-allowed type navigates the tab to the file and discards
    the single-page app's state — the user loses their place instead of
    getting a download.
    """
    case_id = _case(client)
    doc = _upload(client, case_id, filename, b"some bytes\n")
    url = f"/api/v1/cases/{case_id}/documents/{doc['id']}/content"

    assert client.get(url).headers["content-disposition"].startswith("inline;")

    resp = client.get(f"{url}?download=1")

    assert resp.status_code == 200
    assert resp.headers["content-disposition"].startswith("attachment;")
    assert resp.headers["content-type"] == "application/octet-stream"
    assert resp.content == b"some bytes\n"


def test_download_cannot_widen_what_the_allow_list_permits(client):
    """The parameter may only ever make the response stricter.

    `.html` is never served inline (TB-3: uploaded content is untrusted, and
    an inline `.html` is stored XSS). A query parameter must not be able to
    reach past that, in either direction.
    """
    case_id = _case(client)
    doc = _upload(client, case_id, "page.html", b"<script>alert(1)</script>")
    url = f"/api/v1/cases/{case_id}/documents/{doc['id']}/content"

    for suffix in ("", "?download=1", "?download=0", "?download=false"):
        resp = client.get(f"{url}{suffix}")
        assert resp.headers["content-disposition"].startswith("attachment;"), suffix
        assert resp.headers["content-type"] == "application/octet-stream", suffix
