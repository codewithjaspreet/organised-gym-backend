"""add_bank_accounts_table

Revision ID: 201ec2fcbbc9
Revises: a1b2c3d4e5f6
Create Date: 2026-01-16 19:38:53.197053

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '201ec2fcbbc9'
down_revision: Union[str, Sequence[str], None] = '0c4e9439c566'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if table already exists
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'bank_accounts' not in tables:
        op.create_table(
            'bank_accounts',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('account_holder_name', sa.String(), nullable=False),
            sa.Column('bank_name', sa.String(), nullable=False),
            sa.Column('account_number', sa.String(), nullable=False),
            sa.Column('ifsc_code', sa.String(), nullable=False),
            sa.Column('upi_id', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Get existing indexes
    indexes = [idx['name'] for idx in inspector.get_indexes('bank_accounts')] if 'bank_accounts' in tables else []
    
    # Create index if it doesn't exist
    if 'ix_bank_accounts_user_id' not in indexes:
        op.create_index(op.f('ix_bank_accounts_user_id'), 'bank_accounts', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_bank_accounts_user_id'), table_name='bank_accounts')
    op.drop_table('bank_accounts')
