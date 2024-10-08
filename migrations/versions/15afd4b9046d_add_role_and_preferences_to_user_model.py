"""Add role and preferences to User model

Revision ID: 15afd4b9046d
Revises: 8b1206db2256
Create Date: 2024-10-02 21:35:20.241568

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '15afd4b9046d'
down_revision = '8b1206db2256'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('role', sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column('preferences', sa.Text(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('preferences')
        batch_op.drop_column('role')

    # ### end Alembic commands ###
