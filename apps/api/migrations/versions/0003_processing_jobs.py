"""processing_jobs table and documents.latest_job_id — SPEC-AMD-001

Revision ID: 0003_processing_jobs
Revises: 0002_evidence_status_engine
Create Date: 2026-08-22 00:00:00.000000

Adds the `processing_jobs` entity per docs/spec/AMENDMENTS.md SPEC-AMD-001
and RULING-01 (amended): id, case_id, job_type, status, document_id,
question_id, idempotency_key, attempt_count, lease_expires_at, error_code,
error_message, created_at, started_at, finished_at.

Also adds `documents.latest_job_id` (nullable FK) so a refreshed client can
reach the Job resource without any other lookup.

`processing_jobs` is created first (its `document_id` FK is nullable, so no
ordering problem); `documents.latest_job_id` is added afterwards as a
separate nullable column/FK, since the two tables reference each other.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0003_processing_jobs"
down_revision: Union[str, None] = "0002_evidence_status_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("case_id", sa.String(length=36), nullable=False),
        sa.Column("job_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=True),
        sa.Column("question_id", sa.String(length=36), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=120), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "job_type IN ('DOCUMENT_PARSE', 'DOCUMENT_INDEX', 'QUESTION_ANALYZE', 'EXPORT_RENDER')",
            name="ck_processing_jobs_job_type",
        ),
        sa.CheckConstraint(
            "status IN ('QUEUED', 'RUNNING', 'SUCCEEDED', 'FAILED', 'CANCELLED')",
            name="ck_processing_jobs_status",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column(
        "documents",
        sa.Column("latest_job_id", sa.String(length=36), nullable=True),
    )
    op.create_foreign_key(
        "fk_documents_latest_job_id",
        "documents",
        "processing_jobs",
        ["latest_job_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_documents_latest_job_id", "documents", type_="foreignkey")
    op.drop_column("documents", "latest_job_id")
    op.drop_table("processing_jobs")
