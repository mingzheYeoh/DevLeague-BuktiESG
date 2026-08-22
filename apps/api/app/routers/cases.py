"""Case endpoints — Contract §6 "Cases".

Only POST /cases and GET /cases/{case_id} are needed for this slice. The
other Case endpoints in the Contract (list, PATCH) are out of scope.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import case_not_found
from app.models import Case
from app.schemas import CaseCreate, CaseSummary

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])


@router.post("", response_model=CaseSummary, status_code=201)
def create_case(payload: CaseCreate, db: Session = Depends(get_db)) -> CaseSummary:
    case = Case(
        title=payload.title,
        customer_name=payload.customer_name,
        deadline_at=payload.deadline_at,
        reporting_period_start=payload.reporting_period_start,
        reporting_period_end=payload.reporting_period_end,
        status="DRAFT",
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return CaseSummary.from_model(case)


@router.get("/{case_id}", response_model=CaseSummary)
def get_case(case_id: str, db: Session = Depends(get_db)) -> CaseSummary:
    case = db.get(Case, case_id)
    if case is None:
        raise case_not_found(case_id)
    return CaseSummary.from_model(case)
