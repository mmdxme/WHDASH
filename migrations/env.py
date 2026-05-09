"""
Alembic Migration Environment
=============================
MMDx Alembic migration environment with dual DB support.

URL is resolved dynamically without importing config.py (to avoid SECRET_KEY check).
"""

import os
import sys
from logging.config import fileConfig

from alembic import context

# ==============================================================================
# Logging Setup
# ==============================================================================

try:
    _cfg = context.config
    if _cfg and hasattr(_cfg, 'config_file_name') and _cfg.config_file_name:
        fileConfig(_cfg.config_file_name)
except Exception:
    pass

# ==============================================================================
# Database URL Resolution (no config.py import)
# ==============================================================================

def get_database_url():
    """
    Resolve database URL dynamically without importing config.py.
    """
    db_engine = os.environ.get('DB_ENGINE', 'sqlite').lower()

    if db_engine == 'postgresql':
        password = os.environ.get('POSTGRESQL_PASSWORD', '')
        user = os.environ.get('POSTGRESQL_USER', 'postgres')
        host = os.environ.get('POSTGRESQL_HOST', 'localhost')
        port = int(os.environ.get('POSTGRESQL_PORT', '5432'))
        database = os.environ.get('POSTGRESQL_DATABASE', 'whdash')
        if password:
            return f"postgresql://{user}:{password}@{host}:{port}/{database}"
        return f"postgresql://{user}@{host}:{port}/{database}"
    else:
        db_path = os.environ.get('DATABASE_PATH', 'warehouse.db')
        if not os.path.isabs(db_path):
            base = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(base, db_path)
        return f"sqlite:///{db_path}"


target_metadata = None


def run_migrations_offline() -> None:
    from sqlalchemy import engine_from_config, pool

    url = get_database_url()
    context.config.set_main_option('sqlalchemy.url', url)

    engine = engine_from_config(
        context.config.get_section(context.config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )
        with context.begin_transaction():
            context.run_migrations()


def run_migrations_online() -> None:
    from sqlalchemy import engine_from_config, pool, text

    url = get_database_url()
    context.config.set_main_option('sqlalchemy.url', url)

    engine = engine_from_config(
        context.config.get_section(context.config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    db_engine = os.environ.get('DB_ENGINE', 'sqlite').lower()

    with engine.connect() as connection:
        if db_engine == 'sqlite':
            with connection.begin():
                connection.execute(text("PRAGMA journal_mode=WAL"))
                connection.execute(text("PRAGMA foreign_keys=ON"))

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=False,
        )
        with context.begin_transaction():
            context.run_migrations()


try:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
except Exception:
    raise