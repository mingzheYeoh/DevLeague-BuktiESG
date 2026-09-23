"""Cloud storage must survive a new function instance and stay case-scoped."""

from types import SimpleNamespace

from app.services import storage


def test_private_blob_round_trip_and_case_delete(monkeypatch):
    blobs = {}

    class FakeBlobClient:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def put(self, key, data, **options):
            assert options == {"access": "private", "add_random_suffix": False, "overwrite": True}
            blobs[key] = data

        def get(self, key, **options):
            assert options == {"access": "private"}
            return SimpleNamespace(content=blobs[key]) if key in blobs else None

        def head(self, key):
            if key not in blobs:
                raise storage.BlobNotFoundError()

        def delete(self, key):
            blobs.pop(key, None)

        def iter_objects(self, *, prefix):
            return (SimpleNamespace(pathname=key) for key in list(blobs) if key.startswith(prefix))

    monkeypatch.setenv("BLOB_READ_WRITE_TOKEN", "test-token")
    monkeypatch.setattr(storage, "BlobClient", FakeBlobClient)
    storage.save("case-a/hash.pdf", b"private bytes")
    storage.save("case-b/other.pdf", b"other bytes")
    assert storage.exists("case-a/hash.pdf")
    assert storage.load("case-a/hash.pdf") == b"private bytes"
    storage.delete_case_tree("case-a")
    assert not storage.exists("case-a/hash.pdf")
    assert storage.exists("case-b/other.pdf")


def test_authenticated_content_endpoint_serves_private_blob(client, monkeypatch):
    case_id = client.post("/api/v1/cases", json={"title": "Cloud preview"}).json()["id"]
    uploaded = client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": ("sample.txt", b"synthetic evidence", "text/plain")},
    ).json()
    monkeypatch.setattr(storage, "using_blob", lambda: True)
    monkeypatch.setattr(storage, "load", lambda key: b"synthetic evidence")

    response = client.get(f"/api/v1/cases/{case_id}/documents/{uploaded['id']}/content")

    assert response.status_code == 200
    assert response.content == b"synthetic evidence"
    assert response.headers["content-security-policy"] == "default-src 'none'; sandbox"
