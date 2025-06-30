"""Create admin_audit_log table for admin action logging

Revision ID: add_admin_audit_log
Revises: add_settings_table
Create Date: 2025-06-30
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_admin_audit_log'
down_revision = 'add_settings_table'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'admin_audit_log',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('admin_id', sa.Integer, nullable=False),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('details', sa.Text, nullable=True),
        sa.Column('timestamp', sa.DateTime, nullable=False)
    )

def downgrade():
    op.drop_table('admin_audit_log')
