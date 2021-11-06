"""add backend and shots columns to result table

Revision ID: e2f6e8c36cef
Revises: f81b27e6d4ec
Create Date: 2021-11-06 12:35:15.458332

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2f6e8c36cef'
down_revision = 'f81b27e6d4ec'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('result', sa.Column('backend', sa.String(length=1200), nullable=True))
    op.add_column('result', sa.Column('shots', sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table('result') as batch_op:
        batch_op.drop_column('backend')
        batch_op.drop_column('shots')
