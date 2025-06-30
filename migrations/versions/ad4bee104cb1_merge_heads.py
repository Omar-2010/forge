"""merge heads

Revision ID: ad4bee104cb1
Revises: add_admin_reply_to_support, e7d69dcf1031
Create Date: 2025-06-30 20:19:24.848996

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ad4bee104cb1'
down_revision = ('add_admin_reply_to_support', 'e7d69dcf1031')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
