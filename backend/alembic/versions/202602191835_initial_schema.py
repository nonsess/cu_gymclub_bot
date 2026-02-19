"""Initial schema

Revision ID: 453d3fc0db61
Revises: 
Create Date: 2026-02-19 18:35:28.625366

Checked

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

revision: str = '453d3fc0db61'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE gender_enum AS ENUM ('male', 'female', 'other');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE action_type_enum AS ENUM ('like', 'dislike', 'report');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table('users',
        sa.Column('telegram_id', sa.String(length=50), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id')
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_users_telegram_id'), ['telegram_id'], unique=True)

    op.create_table('profiles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=False),
        sa.Column('gender', postgresql.ENUM('male', 'female', 'other', name='gender_enum', create_type=False), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('photo_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    with op.batch_alter_table('profiles', schema=None) as batch_op:
        batch_op.create_index('idx_profiles_active', ['is_active'], unique=False)
        batch_op.create_index('idx_profiles_gender', ['gender'], unique=False)
        batch_op.create_index(batch_op.f('ix_profiles_id'), ['id'], unique=False)

    op.create_table('user_actions',
        sa.Column('from_user_id', sa.Integer(), nullable=False),
        sa.Column('to_user_id', sa.Integer(), nullable=False),
        sa.Column('action_type', postgresql.ENUM('like', 'dislike', 'report', name='action_type_enum', create_type=False), nullable=False),
        sa.Column('report_reason', sa.String(length=200), nullable=True),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('from_user_id', 'to_user_id', name='uq_actions_from_to'),  # ✅ Уникальность
        sa.CheckConstraint('from_user_id != to_user_id', name='chk_actions_not_self'),
        sa.ForeignKeyConstraint(['from_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user_actions', schema=None) as batch_op:
        batch_op.create_index('idx_actions_from_user', ['from_user_id'], unique=False)
        batch_op.create_index('idx_actions_to_user', ['to_user_id'], unique=False)
        batch_op.create_index('idx_actions_type', ['action_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_actions_id'), ['id'], unique=False)

    op.create_table('matches',
        sa.Column('user1_id', sa.Integer(), nullable=False),
        sa.Column('user2_id', sa.Integer(), nullable=False),
        sa.Column('is_notified', sa.Boolean(), nullable=False),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('user1_id < user2_id', name='chk_matches_order'),
        sa.ForeignKeyConstraint(['user1_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user2_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('matches', schema=None) as batch_op:
        batch_op.create_index('idx_matches_user1', ['user1_id'], unique=False)
        batch_op.create_index('idx_matches_user2', ['user2_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_matches_id'), ['id'], unique=False)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_profiles_embedding 
        ON profiles 
        USING ivfflat (embedding vector_cosine_ops) 
        WITH (lists = 100)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_profiles_embedding")

    with op.batch_alter_table('matches', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_matches_id'))
        batch_op.drop_index('idx_matches_user2')
        batch_op.drop_index('idx_matches_user1')
    op.drop_table('matches')

    with op.batch_alter_table('user_actions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_actions_id'))
        batch_op.drop_index('idx_actions_type')
        batch_op.drop_index('idx_actions_to_user')
        batch_op.drop_index('idx_actions_from_user')
    op.drop_table('user_actions')

    with op.batch_alter_table('profiles', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_profiles_id'))
        batch_op.drop_index('idx_profiles_gender')
        batch_op.drop_index('idx_profiles_active')
    op.drop_table('profiles')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_telegram_id'))
        batch_op.drop_index(batch_op.f('ix_users_id'))
    op.drop_table('users')

    op.execute("DROP TYPE IF EXISTS action_type_enum")
    op.execute("DROP TYPE IF EXISTS gender_enum")