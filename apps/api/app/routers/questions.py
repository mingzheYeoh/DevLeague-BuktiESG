"""Question listing endpoint — Contract §6 "Questions and Answers".

Only GET /cases/{case_id}/questions is implemented in this slice.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.errors import case_not_found
from app.models import Case, Question, Questionnaire
from app.schemas import QuestionListItem

router = APIRouter(prefix="/api/v1/cases", tags=["questions"])


@router.get("/{case_id}/questions", response_model=list[QuestionListItem])
def list_questions(case_id: str, db: Session = Depends(get_db)) -> list[QuestionListItem]:
    case = db.get(Case, case_id)
    if case is None:
        raise case_not_found(case_id)

    # SPEC-AMD-007 / RULING-04: ORDER BY question_order ASC, id ASC.
    stmt = (
        select(Question)
        .join(Questionnaire, Question.questionnaire_id == Questionnaire.id)
        .options(joinedload(Question.answer))
        .where(Questionnaire.case_id == case_id)
        .order_by(Question.question_order.asc(), Question.id.asc())
    )
    questions = db.execute(stmt).unique().scalars().all()
    return [QuestionListItem.from_model(q) for q in questions]
