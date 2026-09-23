"""Minimal content-addressed local storage adapter.

Per docs/decisions/decision-register.md §4 item 016: "Storage adapter;
content-addressed" (CTO authority). This slice implements only a local-disk
adapter — enough to prove the upload -> persist -> reload path. Swapping in
an object-store adapter later is an implementation detail behind this same
function, not a schema change (documents.storage_key is adapter-opaque).
"""

from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path

from vercel.blob import BlobClient
from vercel.blob.errors import BlobError, BlobNotFoundError

STORAGE_ROOT = Path(__file__).resolve().parents[2] / "var" / "storage"


def using_blob() -> bool:
    if os.getenv("VERCEL") and not os.getenv("BLOB_READ_WRITE_TOKEN"):
        raise RuntimeError("Vercel deployment has no private Blob store token")
    return bool(os.getenv("BLOB_READ_WRITE_TOKEN"))


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def storage_key_for(case_id: str, sha256: str, filename: str) -> str:
    suffix = Path(filename).suffix
    return f"{case_id}/{sha256}{suffix}"


def save(storage_key: str, data: bytes) -> None:
    path = resolve(storage_key)
    if using_blob():
        with BlobClient() as client:
            client.put(storage_key, data, access="private", add_random_suffix=False, overwrite=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def load(storage_key: str) -> bytes:
    resolve(storage_key)
    if using_blob():
        with BlobClient() as client:
            result = client.get(storage_key, access="private")
        if result is None:
            raise FileNotFoundError(storage_key)
        return result.content
    return resolve(storage_key).read_bytes()


class StorageKeyOutsideRoot(ValueError):
    """A storage_key resolved outside STORAGE_ROOT.

    Should be impossible: keys are built by `storage_key_for()` from a case id
    and a checksum, and `Path.suffix` cannot contain a path separator. Raised
    rather than trusted because the value round-trips through the database, and
    the endpoint that serves file bytes must not be one traversal bug away from
    reading arbitrary files.
    """


def resolve(storage_key: str) -> Path:
    """Resolve a storage_key to a real path, refusing anything that escapes
    STORAGE_ROOT. Callers serving bytes to a client must use this, not
    `STORAGE_ROOT / key`."""
    root = STORAGE_ROOT.resolve()
    path = (root / storage_key).resolve()
    if path != root and root not in path.parents:
        raise StorageKeyOutsideRoot(storage_key)
    return path


def exists(storage_key: str) -> bool:
    try:
        path = resolve(storage_key)
    except StorageKeyOutsideRoot:
        return False
    if using_blob():
        try:
            with BlobClient() as client:
                client.head(storage_key)
        except BlobNotFoundError:
            return False
        return True
    return path.is_file()


def delete_file(storage_key: str) -> None:
    """Remove one stored blob. Missing is success - the caller's goal is that
    the bytes are gone, and they are.

    Safe against another Document in another Case holding identical bytes:
    `storage_key_for` puts the Case id in the key, so blobs are not shared
    across Cases. Within one Case identical bytes are one Document, because
    upload de-duplicates by checksum.
    """
    path = resolve(storage_key)
    if using_blob():
        with BlobClient() as client:
            client.delete(storage_key)
        return
    path.unlink(missing_ok=True)


def delete_case_tree(case_id: str) -> None:
    """Remove every stored file belonging to one Case.

    Keys are ``<case_id>/<sha256><suffix>`` (see `storage_key_for`), so a
    Case's blobs are exactly one directory. Deleting the Case row cascades
    through the ORM to its `documents`, but nothing in the database owns the
    bytes on disk — without this, a deleted Case leaves its uploads behind.

    `case_id` arrives from a URL path, so it goes through the same escape check
    as `resolve()`: this function calls `shutil.rmtree`, and that is not a
    traversal bug worth risking. A Case that never had an upload has no
    directory, which is not an error.
    """
    root = STORAGE_ROOT.resolve()
    path = (root / case_id).resolve()
    if path == root or root not in path.parents:
        raise StorageKeyOutsideRoot(case_id)
    if using_blob():
        with BlobClient() as client:
            for blob in client.iter_objects(prefix=f"{case_id}/"):
                client.delete(blob.pathname)
        return
    if path.is_dir():
        shutil.rmtree(path)
