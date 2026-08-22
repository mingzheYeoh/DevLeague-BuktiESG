"""evidence status engine — SPEC-AMD-005

Revision ID: 0002_evidence_status_engine
Revises: 0001_initial_schema
Create Date: 2026-08-22 00:00:00.000000

Adds the minimal columns needed to make the real SPEC-AMD-005 deterministic
Evidence Status engine (app/services/rules.py) actually computable, rather
than only theoretically defined:

- answers.status_findings_json: structured findings preserved per SPEC-AMD-005
  step 3 ("lower-priority findings are never discarded"). AGENTS.md §3.2
  already names `status_findings` as a rule-engine-only field; this is its
  persisted column.
- answers.not_applicable_reason: RULING-02's NOT_APPLICABLE step requires a
  reason plus a reviewer identity (reviewer_name/reviewed_at already exist).
- evidence_links.value: the reported value this evidence carries (mirrors
  ai_pipeline.CandidateEvidence.value), needed for CONFLICTING detection and
  the VERIFIED "explainable unit" check.
- evidence_links.extraction_valid: per-evidence-link readability flag for
  step 2's "exclude unreadable or extraction-invalid evidence" rule,
  independent of the parent document's processing_status.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_evidence_status_engine"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("answers", sa.Column("status_findings_json", sa.Text(), nullable=True))
    op.add_column("answers", sa.Column("not_applicable_reason", sa.Text(), nullable=True))
    op.add_column("evidence_links", sa.Column("value", sa.String(length=255), nullable=True))
    op.add_column(
        "evidence_links",
        sa.Column(
            "extraction_valid",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade() -> None:
    op.drop_column("evidence_links", "extraction_valid")
    op.drop_column("evidence_links", "value")
    op.drop_column("answers", "not_applicable_reason")
    op.drop_column("answers", "status_findings_json")
