"""The identity tables: shape, constraints and cascades."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import EmailToken, Invitation, Organization, OrganizationMember, SessionRow, User


def _user(db, email="a@example.com"):
    user = User(email=email, password_hash="x")
    db.add(user)
    db.commit()
    return user


def _org(db, name="Tenggara Precision"):
    org = Organization(name=name)
    db.add(org)
    db.commit()
    return org


def test_email_is_unique(db_session):
    _user(db_session)
    db_session.add(User(email="a@example.com", password_hash="y"))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_membership_carries_a_role(db_session):
    user, org = _user(db_session), _org(db_session)
    db_session.add(OrganizationMember(user_id=user.id, organization_id=org.id, role="ADMIN"))
    db_session.commit()
    assert db_session.query(OrganizationMember).one().role == "ADMIN"


def test_membership_rejects_an_unknown_role(db_session):
    user, org = _user(db_session), _org(db_session)
    db_session.add(OrganizationMember(user_id=user.id, organization_id=org.id, role="OWNER"))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_a_user_can_belong_to_two_organizations(db_session):
    user = _user(db_session)
    first, second = _org(db_session, "First"), _org(db_session, "Second")
    db_session.add_all(
        [
            OrganizationMember(user_id=user.id, organization_id=first.id, role="ADMIN"),
            OrganizationMember(user_id=user.id, organization_id=second.id, role="MEMBER"),
        ]
    )
    db_session.commit()
    assert db_session.query(OrganizationMember).count() == 2


def test_session_token_hash_is_unique(db_session):
    user, org = _user(db_session), _org(db_session)
    for _ in range(2):
        db_session.add(
            SessionRow(user_id=user.id, organization_id=org.id, token_hash="same-hash")
        )
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_deleting_a_user_deletes_their_sessions(db_session):
    user, org = _user(db_session), _org(db_session)
    db_session.add(SessionRow(user_id=user.id, organization_id=org.id, token_hash="h"))
    db_session.commit()
    db_session.delete(user)
    db_session.commit()
    assert db_session.query(SessionRow).count() == 0


def test_email_token_rejects_an_unknown_purpose(db_session):
    user = _user(db_session)
    db_session.add(EmailToken(user_id=user.id, purpose="LOGIN", token_hash="h"))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_invitation_needs_no_user_row(db_session):
    # The whole reason invitations are a separate table: the recipient may not
    # have an account yet, so there is no user_id to hang the token on.
    org, inviter = _org(db_session), _user(db_session)
    db_session.add(
        Invitation(
            organization_id=org.id,
            email="new@example.com",
            role="MEMBER",
            token_hash="h",
            invited_by_user_id=inviter.id,
        )
    )
    db_session.commit()
    assert db_session.query(Invitation).one().accepted_at is None
