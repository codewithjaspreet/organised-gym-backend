"""make_announcements_gym_id_nullable

Revision ID: g2d4e5f6a7b8
Revises: f1ca921815ad
Create Date: 2026-02-06

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "g2d4e5f6a7b8"
down_revision: Union[str, None] = "92ec0eb4af63"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "announcements",
        "gym_id",
        existing_type=sa.String(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "announcements",
        "gym_id",
        existing_type=sa.String(),
        nullable=False,
    )
