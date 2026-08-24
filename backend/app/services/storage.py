"""Minimal content-addressed local storage adapter.

Per docs/decisions/decision-register.md §4 item 016: "Storage adapter;
content-addressed" (CTO authority). This slice implements only a local-disk
adapter — enough to prove the upload -> persist -> reload path. Swapping in
an object-store adapter later is an implementation detail behind this same
function, not a schema change (documents.storage_key is adapter-opaque).
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

STORAGE_ROOT = Path(__file__).resolve().parents[2] / "var" / "storage"


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def storage_key_for(case_id: str, sha256: str, filename: str) -> str:
    suffix = Path(filename).suffix
    return f"{case_id}/{sha256}{suffix}"


def save(storage_key: str, data: bytes) -> None:
    path = STORAGE_ROOT / storage_key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def load(storage_key: str) -> bytes:
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
        return resolve(storage_key).is_file()
    except StorageKeyOutsideRoot:
        return False


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
    if path.is_dir():
        shutil.rmtree(path)
