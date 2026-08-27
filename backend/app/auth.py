"""Who is acting, and what they may reach.

This module is the whole of tenant isolation. The design chose application-layer
filtering over Postgres row-level security, which puts one obligation on this
file: every case-rooted endpoint must be unable to obtain a Case without coming
through `require_case`.

That is enforced by type rather than by discipline. An endpoint declares
`case: Case = Depends(require_case)` instead of `case_id: str`, so there is no
unchecked case in scope to use by accident. A tenancy check written as the first
line of a function body is a check the next person to add an endpoint can leave
out; a check in the signature has to be deliberately routed around.

`backend/tests/test_isolation_guard.py` fails the build if a router reaches past
this module.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import case_not_found, not_authenticated, not_permitted
from app.models import Case, OrganizationMember, User
from app.services.sessions import resolve_session

#: Read by the browser only as an opaque cookie. HttpOnly, so no script on the
#: page can read it even if one is injected.
SESSION_COOKIE_NAME = "bukti_session"


@dataclass(frozen=True)
class Actor:
    """The authenticated caller, reduced to what authorization needs.

    Frozen and free of ORM objects on purpose: an Actor is passed into every
    endpoint, and a mutable one carrying a live `User` would let a handler
    change identity halfway through a request.
    """

    user_id: str
    organization_id: str
    role: str


def current_actor(
    bukti_session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Actor:
    if not bukti_session:
        raise not_authenticated()

    session_row = resolve_session(db, bukti_session)
    if session_row is None:
        raise not_authenticated()

    membership = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.user_id == session_row.user_id,
            OrganizationMember.organization_id == session_row.organization_id,
        )
        .one_or_none()
    )
    if membership is None:
        # The session names an organization this user no longer belongs to -
        # they were removed while signed in. The session is stale, not the
        # credential invalid, but the answer is the same and says less.
        raise not_authenticated()

    return Actor(
        user_id=session_row.user_id,
        organization_id=session_row.organization_id,
        role=membership.role,
    )


def require_case(
    case_id: str,
    actor: Actor = Depends(current_actor),
    db: Session = Depends(get_db),
) -> Case:
    """The Case named in the path, if it belongs to the actor's organization.

    404 for both "no such case" and "not yours", from the same helper, so the
    two are byte-identical to a caller. A 403 would confirm the identifier is
    real, which is free intelligence for enumeration.
    """
    case = db.get(Case, case_id)
    if case is None or case.organization_id != actor.organization_id:
        raise case_not_found(case_id)
    return case


def require_admin(actor: Actor = Depends(current_actor)) -> Actor:
    """For actions only an ADMIN may take: deleting a case, managing members.

    403 here, not 404: the actor is already established as a member of the
    organization, so confirming the resource exists tells them nothing they
    could not already see.
    """
    if actor.role != "ADMIN":
        raise not_permitted()
    return actor


def actor_email(db: Session, actor: Actor) -> str:
    """The signed-in user's email, for the columns that record who ruled.

    Deliberately not a field on `Actor`. That dataclass is "reduced to what
    authorization needs", and email is needed to authorize nothing - putting it
    there would add a `User` lookup to all 21 endpoints in order to serve the
    three that record a human verdict.

    Email rather than `user_id` because these columns are read by people: a
    reviewer looking at "who accepted this evidence" needs an answer, not a
    ULID.
    """
    user = db.get(User, actor.user_id)
    if user is None:
        # The session resolved but its user is gone - deleted mid-request. The
        # credential is not invalid, but there is no one to attribute the
        # verdict to, and an unattributed verdict is the thing this function
        # exists to prevent.
        raise not_authenticated()
    return user.email
