"""add_gym_id_to_bank_accounts

Revision ID: c3939bca9fa1
Revises: 8acf2823c0bb
Create Date: 2026-01-18 14:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3939bca9fa1'
down_revision: Union[str, Sequence[str], None] = None
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
    
    # Add gym_id column if it doesn't exist
    if 'gym_id' not in columns:
        op.add_column('bank_accounts', sa.Column('gym_id', sa.String(), nullable=True))
    
    # Get existing indexes
    indexes = [idx['name'] for idx in inspector.get_indexes('bank_accounts')]
    
    # Create index on gym_id if it doesn't exist
    if 'ix_bank_accounts_gym_id' not in indexes:
        op.create_index(op.f('ix_bank_accounts_gym_id'), 'bank_accounts', ['gym_id'], unique=False)
    
    # Get existing foreign keys
    foreign_keys = [fk['name'] for fk in inspector.get_foreign_keys('bank_accounts')]
    
    # Add foreign key constraint if it doesn't exist
    if 'fk_bank_accounts_gym_id' not in foreign_keys:
        op.create_foreign_key(
            'fk_bank_accounts_gym_id',
            'bank_accounts',
            'gyms',
            ['gym_id'],
            ['id']
        )
    
    # Make user_id nullable (for future user-level accounts)
    # Check current nullable status first
    user_id_col = next((col for col in inspector.get_columns('bank_accounts') if col['name'] == 'user_id'), None)
    if user_id_col and not user_id_col['nullable']:
        op.alter_column('bank_accounts', 'user_id', nullable=True)
    
    # Note: If you have existing data, you may need to populate gym_id
    # based on user_id. Uncomment and modify the following if needed:
    # op.execute("""
    #     UPDATE bank_accounts 
    #     SET gym_id = (SELECT gym_id FROM users WHERE users.id = bank_accounts.user_id)
    #     WHERE gym_id IS NULL
    # """)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove foreign key constraint
    op.drop_constraint('fk_bank_accounts_gym_id', 'bank_accounts', type_='foreignkey')
    
    # Drop index
    op.drop_index(op.f('ix_bank_accounts_gym_id'), table_name='bank_accounts')
    
    # Drop gym_id column
    op.drop_column('bank_accounts', 'gym_id')
    
    # Make user_id not nullable again
    op.alter_column('bank_accounts', 'user_id', nullable=False)
