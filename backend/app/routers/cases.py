"""Case endpoints — Contract §6 "Cases".

POST /cases, GET /cases and GET /cases/{case_id} are implemented, plus the
retirement path: POST /cases/{case_id}/archive, POST /cases/{case_id}/unarchive
and DELETE /cases/{case_id}. A general-purpose PATCH /cases/{case_id} remains
out of scope — the three endpoints here are the only status transitions a
client can drive, so "archive" cannot be spelled as an arbitrary field write.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.auth import Actor, current_actor, require_admin, require_case
from app.db import get_db
from app.models import Case, Question, Questionnaire
from app.schemas import CaseCreate, CaseSummary, ReadinessSummary
from app.services import storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])


@router.post("", response_model=CaseSummary, status_code=201)
def create_case(
    payload: CaseCreate,
    actor: Actor = Depends(current_actor),
    db: Session = Depends(get_db),
) -> CaseSummary:
    case = Case(
        organization_id=actor.organization_id,
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
def list_cases(
    actor: Actor = Depends(current_actor), db: Session = Depends(get_db)
) -> list[CaseSummary]:
    """List every Case belonging to the actor's organization, most recently
    updated first.

    The frontend's Cases screen is the entry point of the whole workflow, so
    it needs a server-side list — otherwise a reloaded browser loses every
    Case id and the workspace looks empty even though the data is there. No
    pagination: this slice is organization-scoped, local-only, and the Case count
    is small (Main Spec §16). Add pagination before this is ever exposed
    beyond localhost.
    """
    cases = (
        db.execute(
            select(Case)
            .where(Case.organization_id == actor.organization_id)
            .order_by(Case.updated_at.desc())
        )
        .scalars()
        .all()
    )
    return [CaseSummary.from_model(c) for c in cases]


@router.get("/{case_id}", response_model=CaseSummary)
def get_case(case: Case = Depends(require_case)) -> CaseSummary:
    return CaseSummary.from_model(case)


@router.delete("/{case_id}", status_code=204)
def delete_case(
    case: Case = Depends(require_case),
    _: Actor = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a Case and everything under it.

    Goes through the ORM rather than a bulk DELETE so the
    ``cascade="all, delete-orphan"`` declared on Case.documents,
    Case.questionnaires and Case.actions actually runs. There is no
    ``ON DELETE CASCADE`` in the schema, so a plain
    ``DELETE FROM cases WHERE id = ...`` would orphan every child row instead.

    Order matters: the row goes first and is committed, then the blobs. The
    other way round, a failure between the two steps would leave documents rows
    citing files that no longer exist — evidence that cannot be produced, which
    is worse than bytes nobody references.

    ADMIN-only: deletion destroys another member's work, which is the line the
    two roles exist to draw.

    Deletable from any status. It used to be refused unless the Case was DRAFT
    or ARCHIVED, with the error telling you to archive it first - and archiving
    is gone, so that check would have made every case that reached EXPORTED
    permanently undeletable.
    """
    case_id = case.id
    db.delete(case)
    db.commit()

    # The row is gone and committed, so the delete has succeeded as far as the
    # client is concerned. Raising here would report 500 for work that was
    # done: the caller would leave the Case on screen and retry against an id
    # that no longer exists. Leftover bytes under the storage root are a
    # janitor's problem; a Case that says it failed to delete but did is a
    # correctness one.
    try:
        storage.delete_case_tree(case_id)
    except OSError:
        logger.exception("Deleted case %s but could not remove its stored files", case_id)

    return Response(status_code=204)


@router.get("/{case_id}/readiness", response_model=ReadinessSummary)
def get_readiness(
    case: Case = Depends(require_case), db: Session = Depends(get_db)
) -> ReadinessSummary:
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
    stmt = (
        select(Question)
        .join(Questionnaire, Question.questionnaire_id == Questionnaire.id)
        .options(joinedload(Question.answer))
        .where(Questionnaire.case_id == case.id, Question.is_required.is_(True))
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
