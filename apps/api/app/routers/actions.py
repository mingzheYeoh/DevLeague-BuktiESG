"""Action endpoints — Contract §6 "Priority and Actions".

Only POST /cases/{case_id}/actions is implemented in this slice (the
"persist a SUBMISSION action" step of the First Vertical Slice). GET is
added too since "persist and reload" requires reading it back.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import api_error, case_not_found
from app.enums import ACTION_TYPE
from app.models import Action, Case, Question
from app.schemas import ActionCreate, ActionRecord

router = APIRouter(prefix="/api/v1/cases", tags=["actions"])


@router.post("/{case_id}/actions", response_model=ActionRecord, status_code=201)
def create_action(
    case_id: str, payload: ActionCreate, db: Session = Depends(get_db)
) -> ActionRecord:
    case = db.get(Case, case_id)
    if case is None:
        raise case_not_found(case_id)

    if payload.type not in ACTION_TYPE:
        raise api_error(
            422, "VALIDATION_ERROR", f"Unknown action type '{payload.type}'.", allowed=list(ACTION_TYPE)
        )

    if payload.question_id is not None:
        question = db.get(Question, payload.question_id)
        if question is None:
            raise api_error(
                422,
                "OBJECT_CASE_MISMATCH",
                f"question_id {payload.question_id} does not exist.",
            )

    action = Action(
        case_id=case_id,
        question_id=payload.question_id,
        type=payload.type,
        title=payload.title,
        owner_name=payload.owner_name,
        owner_role=payload.owner_role,
        next_step=payload.next_step,
        deadline_at=payload.deadline_at,
        status="TODO",
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return ActionRecord.from_model(action)


@router.get("/{case_id}/actions", response_model=list[ActionRecord])
def list_actions(case_id: str, db: Session = Depends(get_db)) -> list[ActionRecord]:
    case = db.get(Case, case_id)
    if case is None:
        raise case_not_found(case_id)
    actions = (
        db.query(Action)
        .filter(Action.case_id == case_id)
        .order_by(Action.created_at.asc())
        .all()
    )
    return [ActionRecord.from_model(a) for a in actions]
