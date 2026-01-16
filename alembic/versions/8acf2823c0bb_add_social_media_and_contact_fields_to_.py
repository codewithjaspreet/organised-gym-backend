"""add_social_media_and_contact_fields_to_gyms

Revision ID: 8acf2823c0bb
Revises: 201ec2fcbbc9
Create Date: 2026-01-16 20:17:56.945257

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8acf2823c0bb'
down_revision: Union[str, Sequence[str], None] = '201ec2fcbbc9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('gyms', sa.Column('whatsapp_number', sa.String(), nullable=True))
    op.add_column('gyms', sa.Column('mobile_no', sa.String(), nullable=True))
    op.add_column('gyms', sa.Column('website', sa.String(), nullable=True))
    op.add_column('gyms', sa.Column('email', sa.String(), nullable=True))
    op.add_column('gyms', sa.Column('insta', sa.String(), nullable=True))
    op.add_column('gyms', sa.Column('facebook', sa.String(), nullable=True))
    op.add_column('gyms', sa.Column('youtube', sa.String(), nullable=True))
    op.add_column('gyms', sa.Column('twitter', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('gyms', 'twitter')
    op.drop_column('gyms', 'youtube')
    op.drop_column('gyms', 'facebook')
    op.drop_column('gyms', 'insta')
    op.drop_column('gyms', 'email')
    op.drop_column('gyms', 'website')
    op.drop_column('gyms', 'mobile_no')
    op.drop_column('gyms', 'whatsapp_number')
