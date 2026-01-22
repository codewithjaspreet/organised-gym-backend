"""add_qr_code_url_to_bank_accounts

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-19 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if column already exists
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Check if bank_accounts table exists
    tables = inspector.get_table_names()
    if 'bank_accounts' not in tables:
        return
    
    # Get existing columns
    columns = [col['name'] for col in inspector.get_columns('bank_accounts')]
    
    # Add qr_code_url column if it doesn't exist
    if 'qr_code_url' not in columns:
        op.add_column(
            'bank_accounts',
            sa.Column('qr_code_url', sa.String(), nullable=True)
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Check if column exists before dropping
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    tables = inspector.get_table_names()
    if 'bank_accounts' not in tables:
        return
    
    columns = [col['name'] for col in inspector.get_columns('bank_accounts')]
    
    if 'qr_code_url' in columns:
        op.drop_column('bank_accounts', 'qr_code_url')
