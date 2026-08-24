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
