"""add_gym_rules_table

Revision ID: 1fad4f00e753
Revises: 22290ff7109a
Create Date: 2026-01-14 23:03:00.461847

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1fad4f00e753'
down_revision: Union[str, Sequence[str], None] = '22290ff7109a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if table already exists
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'gym_rules' not in tables:
        op.create_table(
            'gym_rules',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('gym_id', sa.String(), nullable=False),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('description', sa.String(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['gym_id'], ['gyms.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Check if index exists before creating
    indexes = [idx['name'] for idx in inspector.get_indexes('gym_rules')] if 'gym_rules' in tables else []
    if 'ix_gym_rules_gym_id' not in indexes:
        op.create_index(op.f('ix_gym_rules_gym_id'), 'gym_rules', ['gym_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_gym_rules_gym_id'), table_name='gym_rules')
    op.drop_table('gym_rules')
