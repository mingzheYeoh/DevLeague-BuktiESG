"""Every case belongs to an organization.

Split from `0009`, which created the identity tables. The two are separate
because this one may only run once `create_case` populates the column — a
constraint applied before the code that satisfies it fails every write that
predates it.

`cases` predates organizations entirely, so existing rows carry NULL and the
constraint cannot be added until they have a value.

This migration backfills. It does not delete. Deleting the rows would satisfy
the constraint too, and it is rejected on the same grounds as editing a
protected value to make a test pass: a constraint is not evidence that the data
it rejects was disposable. An operator who wants those cases gone can remove
them afterwards, deliberately, through the API that already supports it.

The placeholder organization is named to be conspicuous rather than plausible,
so anyone who later finds cases inside it understands they predate the tenancy
model instead of mistaking them for a customer's.

Revision ID: 0010_case_organization_required
Revises: 0009_identity_and_tenancy
"""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from alembic import op

revision = "0010_case_organization_required"
down_revision = "0009_identity_and_tenancy"
branch_labels = None
depends_on = None

PLACEHOLDER_ORG_NAME = "Unassigned (pre-authentication)"


def upgrade() -> None:
    connection = op.get_bind()
    orphaned = connection.execute(
        sa.text("SELECT count(*) FROM cases WHERE organization_id IS NULL")
    ).scalar_one()

    if orphaned:
        placeholder_id = str(uuid.uuid4())
        connection.execute(
            sa.text(
                "INSERT INTO organizations (id, name, created_at) "
                "VALUES (:id, :name, now())"
            ),
            {"id": placeholder_id, "name": PLACEHOLDER_ORG_NAME},
        )
        connection.execute(
            sa.text(
                "UPDATE cases SET organization_id = :id WHERE organization_id IS NULL"
            ),
            {"id": placeholder_id},
        )

    op.alter_column("cases", "organization_id", nullable=False)


def downgrade() -> None:
    # The placeholder organization and its case assignments are deliberately
    # left in place. Removing them would have to guess which cases were NULL
    # before the upgrade ran, and guessing wrong silently detaches a real
    # customer's case from its owner.
    op.alter_column("cases", "organization_id", nullable=True)
