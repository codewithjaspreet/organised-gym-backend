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
    # Check if columns already exist
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Check if users table exists
    tables = inspector.get_table_names()
    if 'users' not in tables:
        return
    
    # Get existing columns
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    # Add app_version column if it doesn't exist
    if 'app_version' not in columns:
        op.add_column('users', sa.Column('app_version', sa.String(255), nullable=True))
    
    # Add platform column if it doesn't exist
    if 'platform' not in columns:
        op.add_column('users', sa.Column('platform', sa.String(50), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'platform')
    op.drop_column('users', 'app_version')
