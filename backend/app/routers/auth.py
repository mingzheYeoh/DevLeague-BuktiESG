"""Registration, sign-in and sign-out.

One principle runs through this file and explains what looks redundant: the
HTTP response never says whether an address is registered. Registering a taken
address returns exactly what registering a fresh one returns; a failed sign-in
returns one message whichever half was wrong. Anything else turns these
endpoints into a directory of a company's staff.

The *timing* of those responses does still say it - a missing account skips
argon2, a taken address skips the inserts. That was closed once and is
deliberately reopened: this is a demo, and an attacker with a stopwatch and a
staff list is not in its threat model. It is the first thing to restore if that
stops being true.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.auth import SESSION_COOKIE_NAME, Actor, actor_email, current_actor
from app.config import settings
from app.db import get_db
from app.errors import invalid_credentials
from app.models import Organization, OrganizationMember, User
from app.schemas import ActorSummary, LoginRequest, RegistrationRequest
from app.services.passwords import hash_password, verify_password
from app.services.sessions import revoke_session, start_session

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

#: Returned by `register` whatever happened. A constant, so that the "address
#: already exists" path cannot drift into saying something different later.
_REGISTRATION_ACCEPTED = {"status": "check your email to finish signing up"}


@router.post("/register", status_code=201)
def register(payload: RegistrationRequest, db: Session = Depends(get_db)) -> dict:
    email = payload.email.strip().lower()

    # Hash before the existence check, never after.
    #
    # The taken-address branch below returns without creating anything. If
    # hashing happened only on the fresh path, the two responses would be
    if db.query(User).filter(User.email == email).one_or_none() is not None:
        # Already registered. Say nothing, do nothing, and return the same body
        # as a successful registration. Task 11 adds the "you already have an
        # account" email that makes this recoverable for the real owner.
        return _REGISTRATION_ACCEPTED

    # One transaction. A user with no organization, or an organization with no
    # ADMIN, is a state nothing in the API can repair - there would be no one
    # authorised to invite the first member.
    user = User(email=email, password_hash=hash_password(payload.password))
    organization = Organization(name=payload.organization_name.strip())
    db.add_all([user, organization])
    db.flush()
    db.add(
        OrganizationMember(
            user_id=user.id, organization_id=organization.id, role="ADMIN"
        )
    )
    db.commit()
    return _REGISTRATION_ACCEPTED


@router.post("/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> dict:
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).one_or_none()

    if user is None or not verify_password(payload.password, user.password_hash):
        raise invalid_credentials()

    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .order_by(OrganizationMember.created_at)
        .first()
    )
    if membership is None:
        raise invalid_credentials()

    _, token = start_session(db, user.id, membership.organization_id)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.session_ttl_hours * 3600,
    )
    return {"status": "signed in"}


@router.post("/logout")
def logout(
    response: Response,
    actor: Actor = Depends(current_actor),
    db: Session = Depends(get_db),
) -> dict:
    from app.models import SessionRow

    rows = (
        db.query(SessionRow)
        .filter(
            SessionRow.user_id == actor.user_id,
            SessionRow.organization_id == actor.organization_id,
            SessionRow.revoked_at.is_(None),
        )
        .all()
    )
    for row in rows:
        revoke_session(db, row)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"status": "signed out"}


@router.get("/me", response_model=ActorSummary)
def me(actor: Actor = Depends(current_actor), db: Session = Depends(get_db)) -> ActorSummary:
    organization = db.get(Organization, actor.organization_id)
    return ActorSummary(
        user_id=actor.user_id,
        email=actor_email(db, actor),
        organization_id=actor.organization_id,
        organization_name=organization.name,
        role=actor.role,
    )
