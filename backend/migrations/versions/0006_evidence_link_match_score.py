"""Record how strongly each evidence link matched

Revision ID: 0006_evidence_link_match_score
Revises: 0005_case_retirement
Create Date: 2026-08-24 00:00:00.000000

The matcher computed a score for every candidate chunk and threw it away.
`evidence_links` had no orderable measure of quality, so the question-detail
payload picked its one displayed citation with `max(links, key=created_at)` —
the most recently created link. In practice that means **whichever document was
uploaded last**, regardless of what the question is about.

Uploading the twenty-document sample evidence set made that plain: all twenty
questions, across all three pillars, displayed the same document — the
superseded 2019 employee handbook, because it happened to be uploaded
nineteenth.

`match_score` is the sum of the weight of each matched keyword
(`ai_pipeline.analyze.keyword_weights`). It is nullable because rows written
before this migration have no score, and a link with no score must not
outrank one that has a real score of zero.

It is a ranking aid for presentation, not an input to the rule engine.
`evidence_status` is computed only from the conditions in
`app/services/rules.py`, and nothing in this column may be allowed to influence
it (AGENTS.md §3.2 — the AI never owns a verdict).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0006_evidence_link_match_score"
down_revision: Union[str, None] = "0005_case_retirement"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("evidence_links", sa.Column("match_score", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("evidence_links", "match_score")
