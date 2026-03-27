import os
import sys
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 1. Add your project root to the sys.path so Alembic can find the 'app' folder
sys.path.append(os.getcwd())

# 2. Import your settings and the Base
from app.core.config import settings 
from app.db.base import Base 

# 3. CRITICAL: Import all models so Alembic "sees" them.
# If these aren't imported here, Alembic will try to DELETE these tables.
# Ensure these import paths match your actual file structure.
try:
    from app.db.models import (
        Patient, 
        ChatHistory, 
        Diagnosis, 
        VoiceInteraction, 
        MedicalDocument
    )
except ImportError as e:
    print(f"Import Warning: {e}. Check your model paths in alembic/env.py")

# 4. Support for PGVector (RAG system)
try:
    import pgvector.sqlalchemy
except ImportError:
    pass

# 5. Initialize Alembic Config
# This object provides access to the values within the .ini file in use.
config = context.config

# 6. Dynamically set the database URL from your .env file
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql+asyncpg://"):
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)

    split = urlsplit(database_url)
    filtered = [
        (k, v)
        for k, v in parse_qsl(split.query, keep_blank_values=True)
        if k not in {"prepared_statement_cache_size", "statement_cache_size"}
    ]
    database_url = urlunsplit((split.scheme, split.netloc, split.path, urlencode(filtered), split.fragment))

config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 7. Set the metadata for autogenerate comparison
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
            target_metadata=target_metadata,
            # This ensures Alembic ignores the system tables in Postgres
            compare_type=True 
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()