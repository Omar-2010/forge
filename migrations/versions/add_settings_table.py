"""Create settings table for app-wide configuration (discounts, etc.)

Revision ID: add_settings_table
Revises: 
Create Date: 2025-06-30
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_settings_table'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'settings',
        sa.Column('key', sa.String(length=64), primary_key=True),
        sa.Column('value', sa.String(length=255), nullable=True)
    )

def downgrade():
    op.drop_table('settings')
