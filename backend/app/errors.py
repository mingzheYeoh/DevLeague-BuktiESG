"""Shared error envelope helpers (Contract §5)."""

from __future__ import annotations

from fastapi import HTTPException


def api_error(status_code: int, code: str, message: str, **details) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": None,
            }
        },
    )


def case_not_found(case_id: str) -> HTTPException:
    return api_error(404, "CASE_NOT_FOUND", f"Case {case_id} was not found.", case_id=case_id)


def case_already_archived(case_id: str) -> HTTPException:
    return api_error(
        409,
        "CASE_ALREADY_ARCHIVED",
        f"Case {case_id} is already archived.",
        case_id=case_id,
    )


def case_not_archived(case_id: str, status: str) -> HTTPException:
    return api_error(
        409,
        "CASE_NOT_ARCHIVED",
        f"Case {case_id} is {status}, not archived, so there is nothing to restore.",
        case_id=case_id,
        status=status,
    )


def case_not_deletable(case_id: str, status: str, deletable_from: tuple[str, ...]) -> HTTPException:
    """A Case that has been worked on must be archived before it can be deleted.

    Deliberately names the allowed statuses: the client needs to be able to say
    "archive it first" rather than just "no".
    """
    return api_error(
        409,
        "CASE_NOT_DELETABLE",
        (
            f"Case {case_id} is {status}. A Case can only be deleted from "
            f"{' or '.join(deletable_from)} — archive it first."
        ),
        case_id=case_id,
        status=status,
        deletable_from=list(deletable_from),
    )


def not_authenticated() -> HTTPException:
    return api_error(401, "NOT_AUTHENTICATED", "Sign in to continue.")


def invalid_credentials() -> HTTPException:
    """One message for every failed sign-in.

    Never says whether the address is registered. "No such account" and "wrong
    password" as separate answers turn the login form into a membership oracle
    that confirms who a company's employees are.
    """
    return api_error(401, "INVALID_CREDENTIALS", "That email and password do not match.")


def not_permitted() -> HTTPException:
    """For role checks *inside* an organization the actor already belongs to.

    Distinct from cross-tenant refusal, which is a 404 and must stay one: here
    the actor is already known to be a member, so acknowledging the resource
    exists gives nothing away.
    """
    return api_error(403, "NOT_PERMITTED", "Your role does not allow this action.")
