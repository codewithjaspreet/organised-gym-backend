"""add_focus_to_attendance

Revision ID: 0c4e9439c566
Revises: 9e2a0695b941
Create Date: 2026-01-16 18:43:26.096738

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0c4e9439c566'
down_revision: Union[str, Sequence[str], None] = '9e2a0695b941'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if column already exists
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Check if attendance table exists
    tables = inspector.get_table_names()
    if 'attendance' not in tables:
        return
    
    # Get existing columns
    columns = [col['name'] for col in inspector.get_columns('attendance')]
    
    # Add focus column if it doesn't exist
    if 'focus' not in columns:
        op.add_column('attendance', sa.Column('focus', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('attendance', 'focus')
