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
    # Check if column already exists
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Check if gyms table exists
    tables = inspector.get_table_names()
    if 'gyms' not in tables:
        return
    
    # Get existing columns
    columns = [col['name'] for col in inspector.get_columns('gyms')]
    
    # Add gym_code column if it doesn't exist
    if 'gym_code' not in columns:
        op.add_column('gyms', sa.Column('gym_code', sa.String(), nullable=True))
    
    # Get existing indexes
    indexes = [idx['name'] for idx in inspector.get_indexes('gyms')]
    
    # Create unique index on gym_code if it doesn't exist
    if 'ix_gyms_gym_code' not in indexes:
        op.create_index(op.f('ix_gyms_gym_code'), 'gyms', ['gym_code'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_gyms_gym_code'), table_name='gyms')
    op.drop_column('gyms', 'gym_code')
