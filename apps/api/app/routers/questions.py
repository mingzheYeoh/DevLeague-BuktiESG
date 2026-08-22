"""Question listing endpoint — Contract §6 "Questions and Answers".

Only GET /cases/{case_id}/questions is implemented in this slice.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.errors import api_error, case_not_found
from app.enums import REVIEW_ACTION
from app.models import Case, Question, Questionnaire
from app.schemas import AnswerRecord, QuestionListItem, QuestionReviewRequest

router = APIRouter(prefix="/api/v1/cases", tags=["questions"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/{case_id}/questions", response_model=list[QuestionListItem])
def list_questions(case_id: str, db: Session = Depends(get_db)) -> list[QuestionListItem]:
    case = db.get(Case, case_id)
    if case is None:
        raise case_not_found(case_id)

    # SPEC-AMD-007 / RULING-04: ORDER BY question_order ASC, id ASC.
    stmt = (
        select(Question)
        .join(Questionnaire, Question.questionnaire_id == Questionnaire.id)
        .options(joinedload(Question.answer), joinedload(Question.evidence_links))
        .where(Questionnaire.case_id == case_id)
        .order_by(Question.question_order.asc(), Question.id.asc())
    )
    questions = db.execute(stmt).unique().scalars().all()
    return [QuestionListItem.from_model(q) for q in questions]


def _question_not_found(question_id: str):
    return api_error(404, "QUESTION_NOT_FOUND", f"Question '{question_id}' was not found.")


@router.post(
    "/{case_id}/questions/{question_id}/review",
    response_model=AnswerRecord,
)
def review_question(
    case_id: str,
    question_id: str,
    payload: QuestionReviewRequest,
    db: Session = Depends(get_db),
) -> AnswerRecord:
    """Human Review transitions on an Answer — Main Spec §17 Phase 5.

    ACCEPT/EDIT/REJECT/NOT_APPLICABLE. `review_status = HUMAN_CONFIRMED` and
    `evidence_status = NOT_APPLICABLE` are only ever set here, by an explicit
    human action carrying a reviewer_name — never by the deterministic rule
    engine (app/services/rules.py, AGENTS.md §3.2 / RULING-02).
    """
    case = db.get(Case, case_id)
    if case is None:
        raise case_not_found(case_id)

    question = db.get(Question, question_id)
    if question is None or question.questionnaire.case_id != case_id:
        raise _question_not_found(question_id)

    answer = question.answer
    if answer is None:
        raise api_error(
            404,
            "ANSWER_NOT_FOUND",
            f"Question '{question_id}' has no Answer row to review yet.",
        )

    if payload.action not in REVIEW_ACTION:
        raise api_error(
            422,
            "VALIDATION_ERROR",
            f"Unknown review action '{payload.action}'.",
            allowed=list(REVIEW_ACTION),
        )

    if not payload.reviewer_name or not payload.reviewer_name.strip():
        raise api_error(
            422, "VALIDATION_ERROR", "reviewer_name is required for every review action."
        )

    if payload.action == "ACCEPT":
        answer.confirmed_answer = answer.draft_answer
        answer.review_status = "HUMAN_CONFIRMED"

    elif payload.action == "EDIT":
        if not payload.edited_answer or not payload.edited_answer.strip():
            raise api_error(
                422, "VALIDATION_ERROR", "edited_answer is required for an EDIT review action."
            )
        answer.confirmed_answer = payload.edited_answer
        answer.review_status = "HUMAN_CONFIRMED"
        # Preserve the AI-provenance invariant (ck_answers_provenance_ai_run):
        # an edit of an AI-originated draft stays AI_ASSISTED_EDIT (keeps
        # ai_run_id); an edit of a draft with no AI run becomes USER_ENTERED.
        if answer.draft_provenance in ("AI_GENERATED", "AI_ASSISTED_EDIT"):
            answer.draft_provenance = "AI_ASSISTED_EDIT"
        else:
            answer.draft_provenance = "USER_ENTERED"

    elif payload.action == "REJECT":
        if not payload.reason or not payload.reason.strip():
            raise api_error(
                422, "VALIDATION_ERROR", "reason is required for a REJECT review action."
            )
        answer.review_status = "REJECTED"
        answer.review_reason = payload.reason

    elif payload.action == "NOT_APPLICABLE":
        if not payload.reason or not payload.reason.strip():
            raise api_error(
                422,
                "VALIDATION_ERROR",
                "reason is required for a NOT_APPLICABLE review action.",
            )
        # RULING-02: only this human-facing action may ever set or clear
        # evidence_status == NOT_APPLICABLE. The rule engine
        # (app/services/rules.py) only ever preserves it once set here.
        answer.evidence_status = "NOT_APPLICABLE"
        answer.not_applicable_reason = payload.reason
        answer.review_status = "HUMAN_CONFIRMED"
        answer.status_reason = (
            f"Marked NOT_APPLICABLE by {payload.reviewer_name}. Reason: {payload.reason}"
        )

    answer.reviewer_name = payload.reviewer_name
    answer.reviewed_at = _utcnow()

    db.commit()
    db.refresh(answer)
    return AnswerRecord.from_model(answer)
