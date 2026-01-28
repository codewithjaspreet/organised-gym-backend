"""merge multiple heads before announcements update

Revision ID: f1ca921815ad
Revises: 201ec2fcbbc9, b2c3d4e5f6a7
Create Date: 2026-01-25 13:05:28.560565

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1ca921815ad'
down_revision = (
    "201ec2fcbbc9",
    "b2c3d4e5f6a7",
)



branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Check if columns already exist
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Check if announcements table exists
    tables = inspector.get_table_names()
    if 'announcements' not in tables:
        return
    
    # Get existing columns
    columns = [col['name'] for col in inspector.get_columns('announcements')]
    
    # Add send_to column if it doesn't exist
    if 'send_to' not in columns:
        op.add_column(
            "announcements",
            sa.Column("send_to", sa.String(length=50), nullable=False, server_default="All")
        )
        op.alter_column("announcements", "send_to", server_default=None)
    
    # Add member_ids column if it doesn't exist
    if 'member_ids' not in columns:
        op.add_column(
            "announcements",
            sa.Column("member_ids", sa.JSON(), nullable=True)
        )


def downgrade():
    op.drop_column("announcements", "member_ids")
    op.drop_column("announcements", "send_to")
