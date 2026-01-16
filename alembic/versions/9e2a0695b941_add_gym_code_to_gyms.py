"""add_gym_code_to_gyms

Revision ID: 9e2a0695b941
Revises: 21e6d6389d87
Create Date: 2026-01-16 18:11:18.786720

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e2a0695b941'
down_revision: Union[str, Sequence[str], None] = '21e6d6389d87'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add gym_code column (nullable for existing records)
    op.add_column('gyms', sa.Column('gym_code', sa.String(), nullable=True))
    
    # Create unique index on gym_code
    op.create_index(op.f('ix_gyms_gym_code'), 'gyms', ['gym_code'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_gyms_gym_code'), table_name='gyms')
    op.drop_column('gyms', 'gym_code')
