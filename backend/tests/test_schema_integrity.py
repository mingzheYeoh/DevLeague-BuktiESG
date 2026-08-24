"""Every foreign key must be reachable through a mapped relationship.

Deleting a Case goes through the ORM so the declared cascades run
(`routers/cases.py`), and the unit of work decides what order to delete rows
in from the *relationships* it knows about — not from the foreign keys in the
schema. A foreign key with no relationship on either side is therefore
invisible to that ordering: SQLAlchemy happily emits `DELETE FROM documents`
while `evidence_links` rows still cite them.

Postgres answers that with a ForeignKeyViolation and the request 500s. The
symptom is a delete that works locally, passes review, and fails in
production on the first Case that has evidence attached.

This test is the structural guard. It does not care what a relationship is
called or whether it cascades — only that the ORM can see the dependency.
Adding a foreign key without a relationship fails here, at the point the
column is added, rather than in a stack trace months later.
"""

from __future__ import annotations

from sqlalchemy.orm import configure_mappers

import app.models  # noqa: F401  (registers every mapper)
from app.db import Base


def test_every_foreign_key_is_covered_by_a_relationship():
    configure_mappers()

    covered: set[tuple[str, str]] = set()
    for mapper in Base.registry.mappers:
        for relationship in mapper.relationships:
            for local, remote in relationship.local_remote_pairs:
                covered.add((local.table.name, local.name))
                covered.add((remote.table.name, remote.name))

    unmapped = sorted(
        f"{table.name}.{fk.parent.name} -> {fk.column.table.name}.{fk.column.name}"
        for table in Base.metadata.sorted_tables
        for fk in table.foreign_keys
        if (table.name, fk.parent.name) not in covered
    )

    assert unmapped == [], (
        "These foreign keys have no relationship mapping, so the ORM cannot "
        "order deletes around them:\n  " + "\n  ".join(unmapped)
    )
