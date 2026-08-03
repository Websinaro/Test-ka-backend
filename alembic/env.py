from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 1. Import your database Base and DATABASE_URL
from database.database import Base
from config.config import DATABASE_URL
from model import model  # Ensures models are registered with Base.metadata

# 2. Retrieve Alembic config object
config = context.config

# 3. Inject your database URL into Alembic's config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# 4. Setup Python logging
if config.config_file_name:
    fileConfig(config.config_file_name)

# 5. Set target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
