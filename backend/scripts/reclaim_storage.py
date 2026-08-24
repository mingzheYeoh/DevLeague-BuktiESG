"""Report, and optionally remove, stored bytes no database row references.

    uv run python scripts/reclaim_storage.py            # report only
    uv run python scripts/reclaim_storage.py --delete   # remove the orphans

Reports by default because the destructive direction should be the one you
have to ask for. Reads `DATABASE_URL` like the app, so it reconciles against
whichever database the app is actually using.

Rows whose blob is missing are reported and never touched: a document that
cannot be produced is a problem for a human, and deleting the row would
destroy the record that the evidence was ever cited.
"""

from __future__ import annotations

import argparse
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

from app.db import SessionLocal  # noqa: E402
from app.services import storage  # noqa: E402
from app.services.reclaim import find_orphans, reclaim_orphans  # noqa: E402


def _human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n / 1:.1f} {unit}"
        n /= 1024
    return f"{n} B"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delete", action="store_true", help="remove the orphaned files")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        report = find_orphans(db)
        print(f"storage root: {storage.STORAGE_ROOT}")
        print(f"orphaned files : {len(report.orphan_keys)}  ({_human(report.orphan_bytes)})")
        print(f"missing blobs  : {len(report.missing_blobs)}")

        for doc_id, key in report.missing_blobs[:10]:
            print(f"  MISSING  document {doc_id}  ->  {key}")
        if len(report.missing_blobs) > 10:
            print(f"  ...and {len(report.missing_blobs) - 10} more")
        if report.missing_blobs:
            print("\nA row whose file is gone is evidence that cannot be produced.")
            print("This script never deletes those - investigate them.")

        if not args.delete:
            if report.orphan_keys:
                print("\nRe-run with --delete to remove the orphaned files.")
            return 0

        removed = reclaim_orphans(db)
        print(f"\nremoved {len(removed)} files, reclaiming {_human(report.orphan_bytes)}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
