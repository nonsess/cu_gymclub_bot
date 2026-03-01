"""Add is_banned parametr to user

Revision ID: 588238634b4c
Revises: b8557fa5aa33
Create Date: 2026-02-27 12:22:02.857207

Checked

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '588238634b4c'
down_revision: Union[str, Sequence[str], None] = 'b8557fa5aa33'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_banned', sa.Boolean(), nullable=False))

def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_banned')
