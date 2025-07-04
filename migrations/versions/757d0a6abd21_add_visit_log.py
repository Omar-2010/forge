"""add visit log

Revision ID: 757d0a6abd21
Revises: 3f3e1408a363
Create Date: 2025-06-29 20:43:19.507043

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '757d0a6abd21'
down_revision = '3f3e1408a363'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('visit_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('ip_address', sa.String(length=64), nullable=True),
    sa.Column('user_agent', sa.String(length=256), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('visit_log')
    # ### end Alembic commands ###
