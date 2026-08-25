"""Every datetime the API emits must carry a UTC offset.

The models declare `DateTime(timezone=True)` and write aware UTC values, but
SQLite has no timezone type: it stores the naive text and hands it back with
`tzinfo=None`. Pydantic then serialises it without an offset, and
`new Date("2026-08-24T02:35:29")` in a browser is defined to mean *local*
time. In UTC+8 that reads eight hours early — an evidence document uploaded
seconds ago is labelled "8 hrs ago", and a deadline set for 4 September
displays as 3 September.

Postgres returns aware values, so this is invisible in production and wrong
everywhere the dev database is used — the same "green locally, broken on the
other engine" shape as the foreign-key ordering bug in
test_schema_integrity.py.

The guarantee pinned here is that the ORM honours what the column declares,
on every dialect: what goes in aware comes back aware, and what was stored
before this existed is read as UTC rather than as an ambiguous local time.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.models import Case, Organization
from app.schemas import CaseSummary


def _scaffold_org(db):
    """A bare Organization to satisfy `Case.organization_id`.

    These tests are about `UtcDateTime` round-tripping, not tenancy, and
    construct `Case` directly rather than through `create_case` (which
    normally supplies this). Named to read as test scaffolding, not a
    plausible customer.
    """
    org = Organization(name="Datetime Test Scaffold Org")
    db.add(org)
    db.commit()
    return org


def test_datetimes_come_back_from_the_database_timezone_aware(db_session):
    org = _scaffold_org(db_session)
    case = Case(
        organization_id=org.id,
        title="Aware",
        deadline_at=datetime(2026, 9, 4, 0, 0, tzinfo=timezone.utc),
    )
    db_session.add(case)
    db_session.commit()
    db_session.expire_all()

    stored = db_session.query(Case).one()

    assert stored.updated_at.tzinfo is not None, "updated_at lost its timezone"
    assert stored.deadline_at.tzinfo is not None, "deadline_at lost its timezone"
    assert stored.deadline_at == datetime(2026, 9, 4, 0, 0, tzinfo=timezone.utc)


def test_a_non_utc_input_is_normalised_rather_than_stored_as_written(db_session):
    """A caller may legitimately send `+08:00`. Storing the wall-clock digits
    and dropping the offset would move the instant by eight hours."""
    kuala_lumpur = timezone(timedelta(hours=8))
    org = _scaffold_org(db_session)
    case = Case(
        organization_id=org.id,
        title="Offset",
        deadline_at=datetime(2026, 9, 4, 8, 0, tzinfo=kuala_lumpur),
    )
    db_session.add(case)
    db_session.commit()
    db_session.expire_all()

    stored = db_session.query(Case).one()

    assert stored.deadline_at == datetime(2026, 9, 4, 0, 0, tzinfo=timezone.utc)


def test_the_serialised_api_payload_carries_an_offset(db_session):
    """What the browser actually receives. Without an offset a browser reads
    the value as local time, which is the bug."""
    org = _scaffold_org(db_session)
    case = Case(
        organization_id=org.id,
        title="Payload",
        deadline_at=datetime(2026, 9, 4, 0, 0, tzinfo=timezone.utc),
    )
    db_session.add(case)
    db_session.commit()
    db_session.expire_all()

    payload = json.loads(CaseSummary.from_model(db_session.query(Case).one()).model_dump_json())

    for field in ("deadline_at", "updated_at"):
        value = payload[field]
        assert value.endswith("Z") or "+00:00" in value, (
            f"{field} serialised as {value!r} — no offset, so a browser reads it as local time"
        )


def test_a_row_written_before_this_guarantee_is_read_as_utc(db_session):
    """Existing rows hold naive text. They were always UTC — the column has
    only ever been written by `datetime.now(timezone.utc)` — so reading them
    as anything else would silently shift historical timestamps."""
    org = _scaffold_org(db_session)
    case = Case(organization_id=org.id, title="Legacy")
    db_session.add(case)
    db_session.commit()
    # Raw SQL on purpose: going through the ORM would apply the new bind
    # processor, which is the thing under test. This writes the bare text an
    # older build left behind.
    db_session.execute(
        text("UPDATE cases SET deadline_at = :v WHERE id = :id"),
        {"v": "2026-09-04 00:00:00.000000", "id": case.id},
    )
    db_session.commit()
    db_session.expire_all()

    stored = db_session.query(Case).one()

    assert stored.deadline_at == datetime(2026, 9, 4, 0, 0, tzinfo=timezone.utc)
