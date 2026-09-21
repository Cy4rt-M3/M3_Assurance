"""Widen the controls attack_mapping array element past VARCHAR(32).

Registry definitions list ATT&CK tactic labels such as
"N/A – not directly mapped to ATT&CK Enterprise" (46 chars) alongside
technique ids, so the element type must grow to VARCHAR(64).

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "controls",
        "attack_mapping",
        existing_type=sa.ARRAY(sa.String(32)),
        type_=sa.ARRAY(sa.String(64)),
    )


def downgrade() -> None:
    op.alter_column(
        "controls",
        "attack_mapping",
        existing_type=sa.ARRAY(sa.String(64)),
        type_=sa.ARRAY(sa.String(32)),
    )
