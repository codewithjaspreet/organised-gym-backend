"""add_bonus_duration_and_discounted_plan_price_to_memberships

Revision ID: 56035a2d5bca
Revises: 1fad4f00e753
Create Date: 2026-01-15 19:56:42.213633

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '56035a2d5bca'
down_revision: Union[str, Sequence[str], None] = '1fad4f00e753'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add bonus_duration column (integer, nullable)
    op.add_column('memberships', sa.Column('bonus_duration', sa.Integer(), nullable=True))
    
    # Add discounted_plan_price column (numeric/decimal, nullable)
    op.add_column('memberships', sa.Column('discounted_plan_price', sa.Numeric(precision=10, scale=2), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('memberships', 'discounted_plan_price')
    op.drop_column('memberships', 'bonus_duration')
