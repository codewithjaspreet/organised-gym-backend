"""add_app_version_and_platform_to_users

Revision ID: 215182e47602
Revises: 
Create Date: 2026-01-05 23:30:38.956467

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '215182e47602'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('app_version', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('platform', sa.String(50), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'platform')
    op.drop_column('users', 'app_version')
