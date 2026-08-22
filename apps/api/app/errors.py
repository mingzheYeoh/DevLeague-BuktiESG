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
