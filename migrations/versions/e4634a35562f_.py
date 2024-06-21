"""empty message

Revision ID: e4634a35562f
Revises: e2f6e8c36cef
Create Date: 2024-06-21 12:26:54.919731

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e4634a35562f'
down_revision = 'e2f6e8c36cef'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('generated__circuit',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('generated_circuit', sa.String(length=1200), nullable=True),
    sa.Column('input_params', sa.String(length=1200), nullable=True),
    sa.Column('original_depth', sa.Integer(), nullable=True),
    sa.Column('original_width', sa.Integer(), nullable=True),
    sa.Column('original_total_number_of_operations', sa.Integer(), nullable=True),
    sa.Column('original_number_of_multi_qubit_gates', sa.Integer(), nullable=True),
    sa.Column('original_number_of_measurement_operations', sa.Integer(), nullable=True),
    sa.Column('original_number_of_single_qubit_gates', sa.Integer(), nullable=True),
    sa.Column('original_multi_qubit_gate_depth', sa.Integer(), nullable=True),
    sa.Column('complete', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('result', sa.Column('generated_circuit_id', sa.String(length=36), nullable=True))
    op.add_column('result', sa.Column('post_processing_result', sa.String(length=1200), nullable=True))
    op.create_foreign_key(None, 'result', 'generated__circuit', ['generated_circuit_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'result', type_='foreignkey')
    op.drop_column('result', 'post_processing_result')
    op.drop_column('result', 'generated_circuit_id')
    op.drop_table('generated__circuit')
    # ### end Alembic commands ###
