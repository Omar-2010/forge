"""
Revision ID: add_admin_reply_to_support
Revises: add_admin_audit_log
Create Date: 2025-06-30
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_admin_reply_to_support'
down_revision = 'add_admin_audit_log'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('support_request', sa.Column('admin_reply', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('support_request', 'admin_reply')
