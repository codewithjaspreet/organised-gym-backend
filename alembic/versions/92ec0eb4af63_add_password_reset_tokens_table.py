"""add_password_reset_tokens_table

Revision ID: 92ec0eb4af63
Revises: f1ca921815ad
Create Date: 2026-01-26 19:33:59.717134

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '92ec0eb4af63'
down_revision: Union[str, Sequence[str], None] = 'f1ca921815ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
