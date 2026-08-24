"""Case retirement: archive, and delete gated on status

Revision ID: 0005_case_retirement
Revises: 0004_review_and_action_lifecycle
Create Date: 2026-08-23 00:00:00.000000

Adds the two columns that make archiving a Case reversible and dated.

``ARCHIVED`` was already a legal ``cases.status`` value (enums.CASE_STATUS,
constrained by ck_cases_status since 0001) but nothing could ever write it:
the Cases router exposed no PATCH and no DELETE, so every Case was created
DRAFT and stayed DRAFT for life. The status existed as vocabulary with no
transition into it.

- cases.archived_at: when the Case was retired. Distinct from updated_at,
  which the next write — including the unarchive — overwrites.
- cases.status_before_archive: the status the Case held when it was archived,
  so POST /cases/{id}/unarchive can put it back exactly. Without it, archiving
  a READY or EXPORTED Case would destroy the fact that it reached that point,
  and unarchiving could only guess. Compare the REOPEN review action
  (enums.REVIEW_ACTION): the same one-way-door problem, already ruled on once.

Deletion needs no schema change. DELETE /cases/{id} is refused unless status
is in enums.CASE_DELETABLE_FROM ("DRAFT", "ARCHIVED"), and the removal itself
rides the existing ORM ``cascade="all, delete-orphan"`` on Case.documents,
Case.questionnaires and Case.actions.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.enums import CASE_STATUS, check_in

# revision identifiers, used by Alembic.
revision: str = "0005_case_retirement"
down_revision: Union[str, None] = "0004_review_and_action_lifecycle"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CK_NAME = "ck_cases_status_before_archive"


def upgrade() -> None:
    op.add_column("cases", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "cases", sa.Column("status_before_archive", sa.String(length=20), nullable=True)
    )

    # RULING-01's convention is a plain TEXT column plus a generated CHECK.
    # Postgres is the real target (app/config.py: SQLite exists only so the app
    # can boot without a live Postgres), and only Postgres can ALTER TABLE ADD
    # CONSTRAINT. On SQLite it would need batch_alter_table, which rebuilds the
    # table from a reflection that does not reliably carry existing CHECK
    # constraints — that risks silently dropping ck_cases_status to add a
    # constraint on a column the server only ever fills by copying an
    # already-constrained value. Not worth it.
    #
    # A database created by Base.metadata.create_all (the test suite) does get
    # the constraint, because it is declared in Case.__table_args__.
    if op.get_bind().dialect.name != "sqlite":
        op.create_check_constraint(
            _CK_NAME,
            "cases",
            f"status_before_archive IS NULL OR {check_in('status_before_archive', CASE_STATUS)}",
        )


def downgrade() -> None:
    if op.get_bind().dialect.name != "sqlite":
        op.drop_constraint(_CK_NAME, "cases", type_="check")
    op.drop_column("cases", "status_before_archive")
    op.drop_column("cases", "archived_at")
