"""Evidence-link invalidation endpoint — Main Spec §17 Phase 5.

Only POST /cases/{case_id}/evidence-links/{evidence_link_id}/invalidate is
implemented here. This is the trigger point Phase 5 needs for "Evidence
invalidation effect on Actions": when the evidence_link an Action's closure
depended on later gets invalidated, that Action must be reopened/flagged,
not silently stay COMPLETED.

This also recomputes the owning Answer's evidence_status through the same
deterministic rule engine app/services/jobs.py already uses (never through
AI output — AGENTS.md §3.2), since an invalidated link is exactly the kind
of input change that engine is meant to react to.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_case
from app.db import get_db
from app.errors import api_error
from app.models import Action, Case, EvidenceLink, Question
from app.schemas import EvidenceAcceptRequest, EvidenceLinkRecord
from app.services import jobs
from app.services.rules import compute_evidence_status

router = APIRouter(prefix="/api/v1/cases", tags=["evidence"])


def _evidence_link_not_found(evidence_link_id: str):
    return api_error(
        404, "EVIDENCE_LINK_NOT_FOUND", f"Evidence link '{evidence_link_id}' was not found."
    )



def _recompute_answer_status(db: Session, case: Case, link: EvidenceLink) -> None:
    """Re-run the deterministic rule engine over the question this link belongs
    to, after the link's status has changed.

    Both endpoints below change an input the engine reads - acceptance
    satisfies a VERIFIED condition, invalidation removes a candidate - so both
    must recompute, and neither may write a status itself. The verdict comes
    from `rules.compute_evidence_status` and nowhere else (AGENTS.md 3.2 - the
    AI never owns a verdict, and neither does a router).
    """
    question = link.question
    answer = question.answer
    if answer is None:
        return
    result = compute_evidence_status(
        candidates=jobs._load_evidence_candidates(db, question.id),
        requirement=jobs._build_evidence_requirement(question),
        unreadable_documents=jobs._build_unreadable_documents(db, case.id),
        current_status=answer.evidence_status,
        not_applicable_reason=answer.not_applicable_reason,
        reviewer_name=answer.reviewer_name,
    )
    answer.evidence_status = result.status
    answer.status_findings_json = json.dumps(result.status_findings)
    if result.status != "NOT_APPLICABLE":
        answer.status_reason = result.status_reason


def _question_in_case(db: Session, case: Case, question_id: str) -> Question:
    question = db.get(Question, question_id)
    if question is None or question.questionnaire.case_id != case.id:
        raise api_error(
            404, "QUESTION_NOT_FOUND", f"Question '{question_id}' was not found in this case."
        )
    return question


@router.get(
    "/{case_id}/questions/{question_id}/evidence-links",
    response_model=list[EvidenceLinkRecord],
)
def list_evidence_links(
    question_id: str,
    case: Case = Depends(require_case),
    db: Session = Depends(get_db),
) -> list[EvidenceLinkRecord]:
    """Every evidence link on one question, newest match first.

    This exists because `/accept` and `/invalidate` are addressed by
    `evidence_link_id` and, until now, no endpoint handed one out - both were
    reachable only by reading the database. `QuestionListItem` describes the
    single best-matching link for display, deliberately, and is not a place to
    put ids for the others.

    REJECTED and INVALIDATED links are included rather than filtered. The rule
    engine ignores them, but a reviewer deciding what to accept needs to see
    that a link was already set aside - a list that silently omits them reads
    as if the evidence never existed.
    """
    _question_in_case(db, case, question_id)
    links = (
        db.query(EvidenceLink)
        .filter(EvidenceLink.question_id == question_id)
        .order_by(EvidenceLink.match_score.desc().nullslast(), EvidenceLink.created_at.desc())
        .all()
    )
    return [EvidenceLinkRecord.from_model(link) for link in links]


@router.post(
    "/{case_id}/evidence-links/{evidence_link_id}/accept",
    response_model=EvidenceLinkRecord,
)
def accept_evidence_link(
    evidence_link_id: str,
    payload: EvidenceAcceptRequest,
    case: Case = Depends(require_case),
    db: Session = Depends(get_db),
) -> EvidenceLinkRecord:
    """Accept an evidence link: a human vouching for this citation.

    This is the sixth and last VERIFIED condition. The other five are decided
    by the matcher and the questionnaire; this one cannot be, because an
    unreviewed AI-proposed candidate must not satisfy VERIFIED on its own
    (Main Spec 17 Gate P4 - AI confidence does not participate in the VERIFIED
    determination).
    """
    if not payload.reviewer_name or not payload.reviewer_name.strip():
        raise api_error(
            422, "VALIDATION_ERROR", "reviewer_name is required to accept evidence."
        )

    link = db.get(EvidenceLink, evidence_link_id)
    if link is None or link.question.questionnaire.case_id != case.id:
        raise _evidence_link_not_found(evidence_link_id)

    link.link_status = "ACCEPTED"
    link.accepted_by = payload.reviewer_name.strip()
    link.accepted_at = datetime.now(timezone.utc)
    db.flush()
    _recompute_answer_status(db, case, link)
    db.commit()
    db.refresh(link)
    return EvidenceLinkRecord.from_model(link)

@router.post(
    "/{case_id}/evidence-links/{evidence_link_id}/invalidate",
    response_model=EvidenceLinkRecord,
)
def invalidate_evidence_link(
    evidence_link_id: str,
    case: Case = Depends(require_case),
    db: Session = Depends(get_db),
) -> EvidenceLinkRecord:
    link = db.get(EvidenceLink, evidence_link_id)
    if link is None or link.question.questionnaire.case_id != case.id:
        raise _evidence_link_not_found(evidence_link_id)

    link.link_status = "INVALIDATED"
    db.flush()

    # Reopen/flag any COMPLETED Action whose closure depended on this link —
    # it must never silently stay COMPLETED once its evidence is gone.
    affected_actions = (
        db.query(Action)
        .filter(Action.closure_evidence_link_id == link.id, Action.status == "COMPLETED")
        .all()
    )
    reopen_note = (
        "Reopened automatically: the closure evidence for this Action was "
        "invalidated after completion."
    )
    for action in affected_actions:
        action.status = "NEEDS_REVIEW"
        action.completed_at = None
        action.completion_note = (
            f"{action.completion_note}\n{reopen_note}" if action.completion_note else reopen_note
        )

    _recompute_answer_status(db, case, link)

    db.commit()
    db.refresh(link)
    return EvidenceLinkRecord.from_model(link)
