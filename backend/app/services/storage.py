"""Minimal content-addressed local storage adapter.

Per docs/decisions/decision-register.md §4 item 016: "Storage adapter;
content-addressed" (CTO authority). This slice implements only a local-disk
adapter — enough to prove the upload -> persist -> reload path. Swapping in
an object-store adapter later is an implementation detail behind this same
function, not a schema change (documents.storage_key is adapter-opaque).
"""

from __future__ import annotations

import hashlib
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
    path = STORAGE_ROOT / storage_key
    return path.read_bytes()
