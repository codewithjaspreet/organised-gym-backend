"""add_app_info_table

Revision ID: a1b2c3d4e5f6
Revises: 66ff8972076
Create Date: 2026-01-19 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '66ff8972076'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if table already exists
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'app_info' not in tables:
        op.create_table(
            'app_info',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('platform', sa.String(), nullable=False),
            sa.Column('android_app_version', sa.String(), nullable=False),
            sa.Column('ios_app_version', sa.String(), nullable=False),
            sa.Column('android_maintenance_mode', sa.Boolean(), nullable=False),
            sa.Column('ios_maintenance_mode', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('app_info')
