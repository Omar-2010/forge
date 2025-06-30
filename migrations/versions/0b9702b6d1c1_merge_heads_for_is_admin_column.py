"""merge heads for is_admin column

Revision ID: 0b9702b6d1c1
Revises: add_is_admin_to_user
Create Date: 2025-06-29 18:48:46.113341

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0b9702b6d1c1'
down_revision = 'add_is_admin_to_user'
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
