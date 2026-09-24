"""Store advisory model relevance separately from human link decisions.

Revision ID: 0011_evidence_relevance_advice
Revises: 0010_case_organization_required
"""

from alembic import op
import sqlalchemy as sa

revision = "0011_evidence_relevance_advice"
down_revision = "0010_case_organization_required"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("evidence_links", sa.Column("ai_relevance", sa.String(16), nullable=True))
    op.add_column("evidence_links", sa.Column("ai_quote", sa.Text(), nullable=True))
    op.add_column("evidence_links", sa.Column("ai_missing", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("evidence_links", "ai_missing")
    op.drop_column("evidence_links", "ai_quote")
    op.drop_column("evidence_links", "ai_relevance")
