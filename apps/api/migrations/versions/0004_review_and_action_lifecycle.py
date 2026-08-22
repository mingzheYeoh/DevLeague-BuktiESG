"""review_reason + Action closure-evidence lifecycle — Main Spec §17 Phase 5

Revision ID: 0004_review_and_action_lifecycle
Revises: 0003_processing_jobs
Create Date: 2026-08-22 00:00:00.000000

Adds the minimal columns needed for Phase 5 ("Human Review and Action
Tracking"):

- answers.review_reason: human-supplied reason for a REJECT review action
  (POST /cases/{id}/questions/{question_id}/review). Distinct from the
  existing answers.not_applicable_reason column, which only the
  NOT_APPLICABLE review action ever sets — never REJECT.
- actions.requires_closure_evidence: an Action addressing MISSING/
  CONFLICTING evidence must supply closure evidence before it can be marked
  COMPLETED (Gate P5). Boolean, defaults false; set at Action-creation time,
  auto-derived from the question's evidence_status or explicitly overridden
  by the caller — never flipped implicitly afterward.
- actions.closure_evidence_link_id: the evidence_links row an Action's
  closure depended on. Nullable FK. Checked by
  POST /cases/{id}/evidence-links/{id}/invalidate to decide whether a
  COMPLETED Action must be reopened when its closure evidence is
  invalidated.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0004_review_and_action_lifecycle"
down_revision: Union[str, None] = "0003_processing_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("answers", sa.Column("review_reason", sa.Text(), nullable=True))
    op.add_column(
        "actions",
        sa.Column(
            "requires_closure_evidence",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "actions", sa.Column("closure_evidence_link_id", sa.String(length=36), nullable=True)
    )
    op.create_foreign_key(
        "fk_actions_closure_evidence_link_id",
        "actions",
        "evidence_links",
        ["closure_evidence_link_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_actions_closure_evidence_link_id", "actions", type_="foreignkey")
    op.drop_column("actions", "closure_evidence_link_id")
    op.drop_column("actions", "requires_closure_evidence")
    op.drop_column("answers", "review_reason")
