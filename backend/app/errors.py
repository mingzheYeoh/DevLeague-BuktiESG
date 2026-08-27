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
