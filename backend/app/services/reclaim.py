"""Find stored bytes no database row references, and remove them.

`storage.delete_case_tree` and `storage.delete_file` run only on a successful
delete. Anything that fails between writing the blob and committing the row -
a crashed upload, an interrupted delete, a database rebuilt under the same
storage root - leaves bytes with nothing pointing at them and nothing that
notices. Left alone the number only rises; this repository reached 1,252
orphan directories across one development cycle.

The reconciliation is deliberately one-directional.

    blob with no row  -> garbage, safe to remove
    row with no blob  -> evidence that cannot be produced

The second is the failure this product exists to prevent, so it is reported
for a human and never acted on. Deleting such a row would destroy the record
that the evidence was ever cited, which is worse than the inconsistency.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models import Document
from app.services import storage


@dataclass(frozen=True)
class ReclaimReport:
    """What reconciling the storage root against `documents` found."""

    orphan_keys: list[str] = field(default_factory=list)
    missing_blobs: list[tuple[str, str]] = field(default_factory=list)
    orphan_bytes: int = 0


def find_orphans(db: Session) -> ReclaimReport:
    """Compare every file under the storage root against `documents`.

    Reads nothing outside `STORAGE_ROOT` and writes nothing at all, so it is
    safe to run against a live database.
    """
    root = storage.STORAGE_ROOT
    referenced = {key for (key,) in db.query(Document.storage_key).all() if key}

    on_disk: dict[str, int] = {}
    if root.exists():
        for path in root.rglob("*"):
            if path.is_file():
                on_disk[path.relative_to(root).as_posix()] = path.stat().st_size

    orphans = sorted(set(on_disk) - referenced)
    missing = sorted(
        (doc_id, key)
        for doc_id, key in db.query(Document.id, Document.storage_key).all()
        if key and key not in on_disk
    )
    return ReclaimReport(
        orphan_keys=orphans,
        missing_blobs=missing,
        orphan_bytes=sum(on_disk[k] for k in orphans),
    )


def reclaim_orphans(db: Session) -> list[str]:
    """Delete every blob no `documents` row references. Returns what went.

    Empty directories are pruned afterwards: a Case whose files are all gone
    leaves a directory that reads like remaining evidence in a file browser.
    """
    report = find_orphans(db)
    for key in report.orphan_keys:
        storage.delete_file(key)

    root = storage.STORAGE_ROOT
    if root.exists():
        # Deepest first, so a directory emptied by pruning its children is
        # itself considered.
        for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            if path.is_dir() and not any(path.iterdir()):
                path.rmdir()

    return report.orphan_keys
