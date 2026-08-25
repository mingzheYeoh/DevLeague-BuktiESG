"""Store a chunk's measurement on the chunk

Revision ID: 0008_chunk_extracted_values
Revises: 0007_evidence_link_acceptance
Create Date: 2026-08-25 00:00:00.000000

CONFLICTING needs two links reporting different values for the same scope and
period. Nothing ever filled `evidence_links.value`, so the comparison had
nothing to compare and the status was unreachable. Three deterministic
extraction strategies were measured against all 231 links in the sample case
and none worked; a model does, and these columns are where its answer lands.

On `document_chunks` rather than `evidence_links`, deliberately. A measurement
is a property of the fragment that reports it: the same chunk cited by three
questions still reports the same number. Links are re-created every time
another document is indexed, so storing it there would mean paying a model
again for a number it had already read, and leaving links created after an
extraction with no value at all.

All nullable. Most chunks are prose and carry no measurement, and a null here
means "no measurement", which is what the rule engine has always assumed and
reads correctly.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.enums import JOB_TYPE, check_in

revision: str = "0008_chunk_extracted_values"
down_revision: Union[str, None] = "0007_evidence_link_acceptance"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_JOB_TYPE_CK = "ck_processing_jobs_job_type"
_JOB_TYPE_BEFORE = ("DOCUMENT_PARSE", "DOCUMENT_INDEX", "QUESTION_ANALYZE", "EXPORT_RENDER")


def upgrade() -> None:
    # EXTRACT_VALUES is a new job_type, and job_type carries a CHECK. Without
    # widening it here the constraint rejects every extraction job the moment
    # this runs against PostgreSQL - the tests would not catch it, because a
    # database built by create_all derives the constraint from the enum.
    #
    # SQLite cannot ALTER a CHECK, and does not need to: init_dev_db.py builds
    # its schema from the models.
    if op.get_bind().dialect.name != "sqlite":
        op.drop_constraint(_JOB_TYPE_CK, "processing_jobs", type_="check")
        op.create_check_constraint(_JOB_TYPE_CK, "processing_jobs", check_in("job_type", JOB_TYPE))

    op.add_column(
        "document_chunks", sa.Column("extracted_value", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "document_chunks", sa.Column("extracted_unit", sa.String(length=32), nullable=True)
    )
    op.add_column(
        "document_chunks", sa.Column("extracted_scope", sa.String(length=255), nullable=True)
    )
    op.add_column("document_chunks", sa.Column("extracted_period_start", sa.Date(), nullable=True))
    op.add_column("document_chunks", sa.Column("extracted_period_end", sa.Date(), nullable=True))


def downgrade() -> None:
    if op.get_bind().dialect.name != "sqlite":
        op.drop_constraint(_JOB_TYPE_CK, "processing_jobs", type_="check")
        op.create_check_constraint(
            _JOB_TYPE_CK, "processing_jobs", check_in("job_type", _JOB_TYPE_BEFORE)
        )

    op.drop_column("document_chunks", "extracted_period_end")
    op.drop_column("document_chunks", "extracted_period_start")
    op.drop_column("document_chunks", "extracted_scope")
    op.drop_column("document_chunks", "extracted_unit")
    op.drop_column("document_chunks", "extracted_value")
