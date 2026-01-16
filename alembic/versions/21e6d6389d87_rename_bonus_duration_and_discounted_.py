"""rename_bonus_duration_and_discounted_price_to_new_duration_and_new_price

Revision ID: 21e6d6389d87
Revises: 56035a2d5bca
Create Date: 2026-01-16 15:52:27.280362

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '21e6d6389d87'
down_revision: Union[str, Sequence[str], None] = '56035a2d5bca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename bonus_duration to new_duration
    op.alter_column('memberships', 'bonus_duration', new_column_name='new_duration')
    
    # Rename discounted_plan_price to new_price
    op.alter_column('memberships', 'discounted_plan_price', new_column_name='new_price')


def downgrade() -> None:
    """Downgrade schema."""
    # Rename new_duration back to bonus_duration
    op.alter_column('memberships', 'new_duration', new_column_name='bonus_duration')
    
    # Rename new_price back to discounted_plan_price
    op.alter_column('memberships', 'new_price', new_column_name='discounted_plan_price')
