"""Action endpoints — Contract §6 "Priority and Actions".

Only POST /cases/{case_id}/actions is implemented in this slice (the
"persist a SUBMISSION action" step of the First Vertical Slice). GET is
added too since "persist and reload" requires reading it back.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_case
from app.db import get_db
from app.errors import api_error
from app.enums import ACTION_STATUS, ACTION_TYPE
from app.models import Action, Case, EvidenceLink, Question
from app.schemas import ActionCreate, ActionRecord, ActionStatusUpdate

router = APIRouter(prefix="/api/v1/cases", tags=["actions"])

# Evidence statuses for which an Action's closure evidence is required by
# default (Main Spec §17 Phase 5 "an Action addressing MISSING/CONFLICTING
# evidence should require a closure evidence_link"). A caller may still
# override this explicitly via ActionCreate.requires_closure_evidence.
_STATUSES_REQUIRING_CLOSURE_EVIDENCE = ("MISSING", "CONFLICTING")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/{case_id}/actions", response_model=ActionRecord, status_code=201)
def create_action(
    payload: ActionCreate,
    case: Case = Depends(require_case),
    db: Session = Depends(get_db),
) -> ActionRecord:
    if payload.type not in ACTION_TYPE:
        raise api_error(
            422, "VALIDATION_ERROR", f"Unknown action type '{payload.type}'.", allowed=list(ACTION_TYPE)
        )

    # Gate P5: "An Action cannot be created without an owner, next step, and
    # deadline" — enforced here at the API layer, not just at the DB layer
    # (the columns stay nullable so a pre-Phase-5 row is never invalidated).
    missing = [
        field
        for field, value in (
            ("owner_name", payload.owner_name),
            ("next_step", payload.next_step),
            ("deadline_at", payload.deadline_at),
        )
        if value is None or (isinstance(value, str) and not value.strip())
    ]
    if missing:
        raise api_error(
            422,
            "VALIDATION_ERROR",
            "An Action requires an owner, a next step, and a deadline.",
            missing_fields=missing,
        )

    question = None
    if payload.question_id is not None:
        question = db.get(Question, payload.question_id)
        if question is None:
            raise api_error(
                422,
                "OBJECT_CASE_MISMATCH",
                f"question_id {payload.question_id} does not exist.",
            )

    requires_closure_evidence = payload.requires_closure_evidence
    if requires_closure_evidence is None:
        requires_closure_evidence = bool(
            question is not None
            and question.answer is not None
            and question.answer.evidence_status in _STATUSES_REQUIRING_CLOSURE_EVIDENCE
        )

    action = Action(
        case_id=case.id,
        question_id=payload.question_id,
        type=payload.type,
        title=payload.title,
        owner_name=payload.owner_name,
        owner_role=payload.owner_role,
        next_step=payload.next_step,
        deadline_at=payload.deadline_at,
        status="TODO",
        requires_closure_evidence=requires_closure_evidence,
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return ActionRecord.from_model(action)


@router.get("/{case_id}/actions", response_model=list[ActionRecord])
def list_actions(
    case: Case = Depends(require_case), db: Session = Depends(get_db)
) -> list[ActionRecord]:
    actions = (
        db.query(Action)
        .filter(Action.case_id == case.id)
        .order_by(Action.created_at.asc())
        .all()
    )
    return [ActionRecord.from_model(a) for a in actions]


def _action_not_found(action_id: str):
    return api_error(404, "ACTION_NOT_FOUND", f"Action '{action_id}' was not found.")


@router.post("/{case_id}/actions/{action_id}/status", response_model=ActionRecord)
def update_action_status(
    action_id: str,
    payload: ActionStatusUpdate,
    case: Case = Depends(require_case),
    db: Session = Depends(get_db),
) -> ActionRecord:
    """Action lifecycle transitions (Main Spec §17 Phase 5).

    OPEN (TODO) -> ... -> COMPLETED. A COMPLETED transition requires a
    completion_note, and — when the Action was flagged
    requires_closure_evidence=True at creation — a closure_evidence_link_id
    referencing a still-valid (not INVALIDATED) evidence_links row for the
    same question. Enforced server-side; never bypassable from the client.
    """
    action = db.get(Action, action_id)
    if action is None or action.case_id != case.id:
        raise _action_not_found(action_id)

    if payload.status not in ACTION_STATUS:
        raise api_error(
            422,
            "VALIDATION_ERROR",
            f"Unknown action status '{payload.status}'.",
            allowed=list(ACTION_STATUS),
        )

    if payload.status == "COMPLETED":
        note = payload.completion_note or action.completion_note
        if not note or not note.strip():
            raise api_error(
                422,
                "VALIDATION_ERROR",
                "A completion_note is required to mark an Action COMPLETED.",
            )

        link_id = payload.closure_evidence_link_id or action.closure_evidence_link_id
        if action.requires_closure_evidence:
            if not link_id:
                raise api_error(
                    422,
                    "VALIDATION_ERROR",
                    "This Action requires closure evidence before it can be "
                    "marked COMPLETED — supply closure_evidence_link_id.",
                )
            link = db.get(EvidenceLink, link_id)
            if link is None or link.question_id != action.question_id:
                raise api_error(
                    422,
                    "OBJECT_CASE_MISMATCH",
                    f"closure_evidence_link_id {link_id} does not reference "
                    "evidence for this Action's question.",
                )
            if link.link_status == "INVALIDATED":
                raise api_error(
                    422,
                    "VALIDATION_ERROR",
                    "The referenced closure evidence has been invalidated and "
                    "cannot close this Action.",
                )
            action.closure_evidence_link_id = link_id

        action.completion_note = note
        action.status = "COMPLETED"
        action.completed_at = _utcnow()
    else:
        action.status = payload.status
        if payload.completion_note is not None:
            action.completion_note = payload.completion_note
        if payload.status != "COMPLETED":
            action.completed_at = None

    db.commit()
    db.refresh(action)
    return ActionRecord.from_model(action)
