"""Server-side sessions.

A session is a row, not a signed token. The requirement that decides this is
revocation: a departing employee must lose access at once, and a JWT cannot be
withdrawn before it expires without a server-side revocation list - at which
point the token's self-contained property has been paid for and then given
away. A row is the honest form of the same requirement, and it also gives
`last_seen_at`, which a stateless token cannot.

The plaintext token leaves this module exactly once, from `start_session`, on
its way into a cookie. Everything afterwards works from the hash.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models import SessionRow
from app.services.tokens import hash_token, new_token


def start_session(db: Session, user_id: str, organization_id: str) -> tuple[SessionRow, str]:
    """Create a session and return it with its plaintext token.

    The token is returned rather than stored so the caller can set a cookie.
    It cannot be recovered afterwards: only its hash is persisted.
    """
    token = new_token()
    now = datetime.now(timezone.utc)
    row = SessionRow(
        user_id=user_id,
        organization_id=organization_id,
        token_hash=hash_token(token),
        expires_at=now + timedelta(hours=settings.session_ttl_hours),
        last_seen_at=now,
    )
    db.add(row)
    db.commit()
    return row, token


def resolve_session(db: Session, token: str) -> SessionRow | None:
    """The live session for this token, or None.

    Revoked and expired both return None rather than raising, and the caller
    cannot tell them apart from a token that never existed. That is deliberate:
    "this session was revoked" confirms the token was once real.

    Lookup is by hash equality on a unique column - an index probe, not a scan -
    so no comparison happens in Python at all. The database either finds the
    row or does not.
    """
    row = db.query(SessionRow).filter(SessionRow.token_hash == hash_token(token)).one_or_none()
    if row is None or row.revoked_at is not None:
        return None
    if row.expires_at is not None and row.expires_at <= datetime.now(timezone.utc):
        return None
    row.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    return row


def revoke_session(db: Session, row: SessionRow) -> None:
    """Sign out. The row is kept, not deleted.

    A revoked row is evidence that a session existed and when it ended, which
    is what an audit trail will want later. Deleting it would destroy that for
    no gain - the row is small and `resolve_session` already refuses it.
    """
    row.revoked_at = datetime.now(timezone.utc)
    db.commit()
