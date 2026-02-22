"""Add name column to profiles

Revision ID: aebafe5c56df
Revises: 453d3fc0db61
Create Date: 2026-02-22 10:36:13.210505

Checked

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'aebafe5c56df'
down_revision: Union[str, Sequence[str], None] = '453d3fc0db61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name', sa.String(length=100), nullable=False))
        batch_op.drop_index(batch_op.f('idx_profiles_embedding'), postgresql_ops={'embedding': 'vector_cosine_ops'}, postgresql_with={'lists': '100'}, postgresql_using='ivfflat')

    with op.batch_alter_table('user_actions', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('uq_actions_from_to'), type_='unique')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('users_telegram_id_key'), type_='unique')

def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f('users_telegram_id_key'), ['telegram_id'], postgresql_nulls_not_distinct=False)

    with op.batch_alter_table('user_actions', schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f('uq_actions_from_to'), ['from_user_id', 'to_user_id'], postgresql_nulls_not_distinct=False)

    with op.batch_alter_table('profiles', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('idx_profiles_embedding'), ['embedding'], unique=False, postgresql_ops={'embedding': 'vector_cosine_ops'}, postgresql_with={'lists': '100'}, postgresql_using='ivfflat')
        batch_op.drop_column('name')
