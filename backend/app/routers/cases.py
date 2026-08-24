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

from app.db import get_db
from app.enums import CASE_DELETABLE_FROM
from app.errors import (
    case_already_archived,
    case_not_archived,
    case_not_deletable,
    case_not_found,
)
from app.models import Case, Question, Questionnaire
from app.schemas import CaseCreate, CaseSummary, ReadinessSummary
from app.services import storage

logger = logging.getLogger(__name__)

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


@router.post("/{case_id}/archive", response_model=CaseSummary)
def archive_case(case_id: str, db: Session = Depends(get_db)) -> CaseSummary:
    """Retire a Case without destroying anything.

    Allowed from every status except ARCHIVED. Notably including PROCESSING:
    archiving is a filing decision, and refusing it because a parse job is in
    flight would leave the operator unable to tidy a Case that failed halfway.
    It does not cancel jobs, and it does not claim to — nothing in
    processing_jobs is touched.
    """
    case = db.get(Case, case_id)
    if case is None:
        raise case_not_found(case_id)
    if case.status == "ARCHIVED":
        raise case_already_archived(case_id)

    case.status_before_archive = case.status
    case.status = "ARCHIVED"
    case.archived_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(case)
    return CaseSummary.from_model(case)


@router.post("/{case_id}/unarchive", response_model=CaseSummary)
def unarchive_case(case_id: str, db: Session = Depends(get_db)) -> CaseSummary:
    """Put an archived Case back exactly where it was."""
    case = db.get(Case, case_id)
    if case is None:
        raise case_not_found(case_id)
    if case.status != "ARCHIVED":
        raise case_not_archived(case_id, case.status)

    # The fallback only applies to a row whose status was set to ARCHIVED by
    # something other than the archive endpoint — direct SQL, or a database
    # predating migration 0005. DRAFT is the honest answer there: the previous
    # status was not recorded, so it is not known, and inventing IN_REVIEW or
    # READY would assert progress that cannot be substantiated.
    case.status = case.status_before_archive or "DRAFT"
    case.status_before_archive = None
    case.archived_at = None
    db.commit()
    db.refresh(case)
    return CaseSummary.from_model(case)


@router.delete("/{case_id}", status_code=204)
def delete_case(case_id: str, db: Session = Depends(get_db)) -> Response:
    """Delete a Case and everything under it. Refused unless the Case is in
    one of `CASE_DELETABLE_FROM`.

    Goes through the ORM rather than a bulk DELETE so the
    ``cascade="all, delete-orphan"`` declared on Case.documents,
    Case.questionnaires and Case.actions actually runs. There is no
    ``ON DELETE CASCADE`` in the schema, so a plain
    ``DELETE FROM cases WHERE id = ...`` would orphan every child row instead.

    Order matters: the row goes first and is committed, then the blobs. The
    other way round, a failure between the two steps would leave documents rows
    citing files that no longer exist — evidence that cannot be produced, which
    is worse than bytes nobody references.
    """
    case = db.get(Case, case_id)
    if case is None:
        raise case_not_found(case_id)
    if case.status not in CASE_DELETABLE_FROM:
        raise case_not_deletable(case_id, case.status, CASE_DELETABLE_FROM)

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
