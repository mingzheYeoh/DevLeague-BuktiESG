"""Record who accepted an evidence link, and when

Revision ID: 0007_evidence_link_acceptance
Revises: 0006_evidence_link_match_score
Create Date: 2026-08-24 00:00:00.000000

`compute_evidence_status` has always had a VERIFIED branch, and one of its six
conditions is `link_status == 'ACCEPTED'`. Nothing could set it: the only
endpoint that wrote `link_status` moved a link to INVALIDATED. So
`REASON_NOT_ACCEPTED` applied to every link ever written and VERIFIED was
unreachable — 231 links in the sample case, none of them acceptable.

Acceptance is a human verdict (AGENTS.md §3.2 — the AI never owns one), so the
endpoint that performs it carries a `reviewer_name`. These two columns keep it.
VERIFIED is the strongest claim this system makes about a piece of evidence,
and one that cannot name its author is exactly the unprovable claim the product
exists to refuse.

Nullable, because most links are never accepted and rows written before this
migration carry no record of it. A NULL `accepted_by` on an ACCEPTED link means
"accepted before this column existed", not "accepted by nobody" — but no such
row can exist, because nothing could produce an ACCEPTED link until now.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0007_evidence_link_acceptance"
down_revision: Union[str, None] = "0006_evidence_link_match_score"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("evidence_links", sa.Column("accepted_by", sa.String(length=120), nullable=True))
    op.add_column(
        "evidence_links",
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("evidence_links", "accepted_at")
    op.drop_column("evidence_links", "accepted_by")
