"""Case endpoints — Contract §6 "Cases".

POST /cases, GET /cases and GET /cases/{case_id} are implemented. PATCH
/cases/{case_id} remains out of scope for this slice.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.errors import case_not_found
from app.models import Case, Question, Questionnaire
from app.schemas import CaseCreate, CaseSummary, ReadinessSummary

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


@router.get("", response_model=list[CaseSummary])
def list_cases(db: Session = Depends(get_db)) -> list[CaseSummary]:
    """List every Case, most recently updated first.

    The frontend's Cases screen is the entry point of the whole workflow, so
    it needs a server-side list — otherwise a reloaded browser loses every
    Case id and the workspace looks empty even though the data is there. No
    pagination: this slice is single-tenant, local-only, and the Case count
    is small (Main Spec §16). Add pagination before this is ever exposed
    beyond localhost.
    """
    cases = db.execute(select(Case).order_by(Case.updated_at.desc())).scalars().all()
    return [CaseSummary.from_model(c) for c in cases]


@router.get("/{case_id}", response_model=CaseSummary)
def get_case(case_id: str, db: Session = Depends(get_db)) -> CaseSummary:
    case = db.get(Case, case_id)
    if case is None:
        raise case_not_found(case_id)
    return CaseSummary.from_model(case)


@router.get("/{case_id}/readiness", response_model=ReadinessSummary)
def get_readiness(case_id: str, db: Session = Depends(get_db)) -> ReadinessSummary:
    """Readiness Dashboard formula — Shared Integration Contract:
    ``confirmed_required_questions / total_required_questions * 100``.

    A minimal, in-scope implementation of the already-defined (protected,
    AGENTS.md §3.5) formula, not a redefinition of it. Gate P5's first
    criterion: an unconfirmed AI Draft never counts toward readiness — only
    Answers with review_status == HUMAN_CONFIRMED are counted as confirmed,
    regardless of draft_provenance or evidence_status. A question the human
    marked NOT_APPLICABLE is also set to HUMAN_CONFIRMED by the review
    endpoint (app/routers/questions.py), so it counts as confirmed rather
    than as an unmet requirement.
    """
    case = db.get(Case, case_id)
    if case is None:
        raise case_not_found(case_id)

    stmt = (
        select(Question)
        .join(Questionnaire, Question.questionnaire_id == Questionnaire.id)
        .options(joinedload(Question.answer))
        .where(Questionnaire.case_id == case_id, Question.is_required.is_(True))
    )
    required_questions = db.execute(stmt).unique().scalars().all()

    total = len(required_questions)
    confirmed = sum(
        1
        for q in required_questions
        if q.answer is not None and q.answer.review_status == "HUMAN_CONFIRMED"
    )
    percentage = (confirmed / total * 100.0) if total else 0.0

    return ReadinessSummary(
        confirmed_required_questions=confirmed,
        total_required_questions=total,
        percentage=percentage,
    )
