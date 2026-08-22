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

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import api_error, case_not_found
from app.models import Action, Case, EvidenceLink
from app.schemas import EvidenceLinkRecord
from app.services import jobs
from app.services.rules import compute_evidence_status

router = APIRouter(prefix="/api/v1/cases", tags=["evidence"])


def _evidence_link_not_found(evidence_link_id: str):
    return api_error(
        404, "EVIDENCE_LINK_NOT_FOUND", f"Evidence link '{evidence_link_id}' was not found."
    )


@router.post(
    "/{case_id}/evidence-links/{evidence_link_id}/invalidate",
    response_model=EvidenceLinkRecord,
)
def invalidate_evidence_link(
    case_id: str, evidence_link_id: str, db: Session = Depends(get_db)
) -> EvidenceLinkRecord:
    case = db.get(Case, case_id)
    if case is None:
        raise case_not_found(case_id)

    link = db.get(EvidenceLink, evidence_link_id)
    if link is None or link.question.questionnaire.case_id != case_id:
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

    # Recompute the owning Answer's evidence_status via the same
    # deterministic rule engine app/services/jobs.py uses, now that this
    # link is excluded (rules.py already drops INVALIDATED links from
    # `live` before conflict/status evaluation).
    question = link.question
    answer = question.answer
    if answer is not None:
        evidence_candidates = jobs._load_evidence_candidates(db, question.id)
        requirement = jobs._build_evidence_requirement(question)
        unreadable_documents = jobs._build_unreadable_documents(db, case_id)
        result = compute_evidence_status(
            candidates=evidence_candidates,
            requirement=requirement,
            unreadable_documents=unreadable_documents,
            current_status=answer.evidence_status,
            not_applicable_reason=answer.not_applicable_reason,
            reviewer_name=answer.reviewer_name,
        )
        answer.evidence_status = result.status
        answer.status_findings_json = json.dumps(result.status_findings)
        if result.status != "NOT_APPLICABLE":
            answer.status_reason = result.status_reason

    db.commit()
    db.refresh(link)
    return EvidenceLinkRecord.from_model(link)
