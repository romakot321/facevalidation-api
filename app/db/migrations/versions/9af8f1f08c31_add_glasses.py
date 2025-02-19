"""add glasses

Revision ID: 9af8f1f08c31
Revises: 6a3ca0794f91
Create Date: 2025-02-19 17:19:28.960544

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9af8f1f08c31'
down_revision = '6a3ca0794f91'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('task_items', sa.Column('with_glasses', sa.Boolean(), nullable=False, server_default=sa.false()))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('task_items', 'with_glasses')
    # ### end Alembic commands ###
