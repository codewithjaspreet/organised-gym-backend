"""add_plan_id_to_users

Revision ID: 22290ff7109a
Revises: 215182e47602
Create Date: 2026-01-14 18:27:56.789051

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '22290ff7109a'
down_revision: Union[str, Sequence[str], None] = '215182e47602'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if column already exists
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Check if users table exists
    tables = inspector.get_table_names()
    if 'users' not in tables:
        return
    
    # Get existing columns
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    # Add plan_id column if it doesn't exist
    if 'plan_id' not in columns:
        op.add_column('users', sa.Column('plan_id', sa.String(), nullable=True))
    
    # Get existing indexes
    indexes = [idx['name'] for idx in inspector.get_indexes('users')]
    
    # Create index if it doesn't exist
    if 'ix_users_plan_id' not in indexes:
        op.create_index(op.f('ix_users_plan_id'), 'users', ['plan_id'], unique=False)
    
    # Get existing foreign keys
    foreign_keys = [fk['name'] for fk in inspector.get_foreign_keys('users')]
    
    # Add foreign key constraint if it doesn't exist
    if 'fk_users_plan_id_plans' not in foreign_keys:
        op.create_foreign_key('fk_users_plan_id_plans', 'users', 'plans', ['plan_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_users_plan_id_plans', 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_plan_id'), table_name='users')
    op.drop_column('users', 'plan_id')
