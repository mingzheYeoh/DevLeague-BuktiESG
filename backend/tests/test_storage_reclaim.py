"""Reclaiming stored bytes no row references.

`delete_case_tree` runs only on a successful delete. Anything that fails
between writing the blob and committing the row - a crashed upload, an
interrupted delete, a database rebuilt from scratch under the same storage
root - leaves the bytes with nothing pointing at them and no way to notice.

Left alone the number only goes up: this repository accumulated 1,252 orphan
directories and 8.8 MB across one development cycle.

The rule is one-directional on purpose. A blob with no row is garbage; a row
with no blob is evidence that cannot be produced, which is the failure this
product exists to prevent - so this reports those and never touches them.
"""

from __future__ import annotations

from app.services import storage
from app.services.reclaim import find_orphans, reclaim_orphans


def _stored(case_id: str, name: str, data: bytes) -> str:
    key = storage.storage_key_for(case_id, storage.sha256_of(data), name)
    storage.save(key, data)
    return key


def test_a_blob_no_document_references_is_an_orphan(client, db_session):
    case_id = client.post("/api/v1/cases", json={"title": "Reclaim"}).json()["id"]
    kept = client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": ("kept.txt", b"Scheduled waste: 12.6 tonnes.", "text/plain")},
        data={"document_type": "WASTE_RECORD"},
    ).json()
    orphan_key = _stored(case_id, "orphan.txt", b"nothing in the database points at this")

    report = find_orphans(db_session)

    assert orphan_key in report.orphan_keys
    assert report.missing_blobs == []
    from app.models import Document
    assert db_session.get(Document, kept["id"]).storage_key not in report.orphan_keys


def test_reclaiming_removes_only_the_orphans(client, db_session):
    case_id = client.post("/api/v1/cases", json={"title": "Reclaim"}).json()["id"]
    kept = client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": ("kept.txt", b"Scheduled waste: 12.6 tonnes.", "text/plain")},
        data={"document_type": "WASTE_RECORD"},
    ).json()
    orphan_key = _stored(case_id, "orphan.txt", b"nothing in the database points at this")

    from app.models import Document
    kept_key = db_session.get(Document, kept["id"]).storage_key

    removed = reclaim_orphans(db_session)

    assert removed == [orphan_key]
    assert not storage.exists(orphan_key)
    assert storage.exists(kept_key), "a referenced blob must survive"
    assert find_orphans(db_session).orphan_keys == []


def test_a_row_whose_blob_is_gone_is_reported_never_deleted(client, db_session):
    """The asymmetry. A missing blob is a document that cannot be produced, so
    it is surfaced for a human and the row is left exactly where it is."""
    from app.models import Document

    case_id = client.post("/api/v1/cases", json={"title": "Reclaim"}).json()["id"]
    doc = client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": ("gone.txt", b"Scheduled waste: 12.6 tonnes.", "text/plain")},
        data={"document_type": "WASTE_RECORD"},
    ).json()
    key = db_session.get(Document, doc["id"]).storage_key
    storage.delete_file(key)

    report = find_orphans(db_session)
    assert report.missing_blobs == [(doc["id"], key)]

    reclaim_orphans(db_session)
    assert db_session.get(Document, doc["id"]) is not None
