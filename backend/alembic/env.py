from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from sqlalchemy import create_engine
from alembic import context

from src.db.base import Base
from src.models.user import User
from src.models.profile import Profile
from src.models.action import UserAction
from src.models.match import Match

from src.core.config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

db_url = settings.POSTGRES_DSN
if db_url.startswith("postgresql+asyncpg"):
    db_url = db_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
elif db_url.startswith("asyncpg"):
    db_url = db_url.replace("asyncpg", "psycopg2")
    
config.set_main_option('sqlalchemy.url', db_url)


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()