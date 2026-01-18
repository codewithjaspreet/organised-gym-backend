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
down_revision: Union[str, Sequence[str], None] = '8acf2823c0bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add gym_id column to bank_accounts table
    op.add_column('bank_accounts', sa.Column('gym_id', sa.String(), nullable=True))
    
    # Create index on gym_id
    op.create_index(op.f('ix_bank_accounts_gym_id'), 'bank_accounts', ['gym_id'], unique=False)
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_bank_accounts_gym_id',
        'bank_accounts',
        'gyms',
        ['gym_id'],
        ['id']
    )
    
    # Make user_id nullable (for future user-level accounts)
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
