"""Add to action is_responded

Revision ID: 61ce5491813d
Revises: 588238634b4c
Create Date: 2026-03-14 11:24:14.873615
Checked

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '61ce5491813d'
down_revision: Union[str, Sequence[str], None] = '588238634b4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('user_actions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_responded', sa.Boolean(), nullable=False))
        batch_op.create_index('idx_actions_incoming', ['to_user_id', 'is_responded', 'action_type'], unique=False)

def downgrade() -> None:
    with op.batch_alter_table('user_actions', schema=None) as batch_op:
        batch_op.drop_index('idx_actions_incoming')
        batch_op.drop_column('is_responded')
