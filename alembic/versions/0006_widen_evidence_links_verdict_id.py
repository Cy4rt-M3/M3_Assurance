"""widen evidence_links.verdict_id to match verdicts.verdict_id

Revision ID: 0006
Revises: 0005
"""

import sqlalchemy as sa

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "evidence_links",
        "verdict_id",
        existing_type=sa.String(64),
        type_=sa.String(128),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "evidence_links",
        "verdict_id",
        existing_type=sa.String(128),
        type_=sa.String(64),
        existing_nullable=False,
    )
