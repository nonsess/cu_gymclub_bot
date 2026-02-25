"""Dle photos_id add media

Revision ID: b8557fa5aa33
Revises: aebafe5c56df
Create Date: 2026-02-25 14:00:10.336196

Checked

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'b8557fa5aa33'
down_revision: Union[str, Sequence[str], None] = 'aebafe5c56df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('media', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        batch_op.drop_column('photo_ids')

def downgrade() -> None:
    with op.batch_alter_table('profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('photo_ids', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True))
        batch_op.drop_column('media')
