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
    op.add_column('users', sa.Column('plan_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_users_plan_id'), 'users', ['plan_id'], unique=False)
    op.create_foreign_key('fk_users_plan_id_plans', 'users', 'plans', ['plan_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_users_plan_id_plans', 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_plan_id'), table_name='users')
    op.drop_column('users', 'plan_id')
