"""
Revision ID: add_is_admin_to_user
Revises: 
Create Date: 2025-06-29
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_is_admin_to_user'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('user', sa.Column('is_admin', sa.Boolean(), nullable=True, server_default=sa.false()))

def downgrade():
    op.drop_column('user', 'is_admin')
