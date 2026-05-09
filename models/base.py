"""
SQLAlchemy Base and Database Utilities
======================================
Provides a DB-agnostic SQLAlchemy base and connection management.

This module serves as the foundation for database operations in MMDx.
The raw sqlite3 approach in database.py coexists with this module, but
new code should prefer SQLAlchemy for migrations and schema operations.

For runtime queries, continue using database.py (get_db, get_one, get_all).

Usage:
    from models.base import get_engine, get_session, Base
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import NullPool
import config

# ==============================================================================
# SQLAlchemy Base
# ==============================================================================

Base = declarative_base()

# ==============================================================================
# Engine Factory
# ==============================================================================

def get_engine():
    """
    Create a SQLAlchemy engine based on DB_ENGINE setting.
    Supports SQLite and PostgreSQL.
    """
    db_engine = os.environ.get('DB_ENGINE', 'sqlite').lower()

    if db_engine == 'postgresql':
        password = config.POSTGRESQL_PASSWORD
        if password:
            url = f"postgresql://{config.POSTGRESQL_USER}:{password}@{config.POSTGRESQL_HOST}:{config.POSTGRESQL_PORT}/{config.POSTGRESQL_DATABASE}"
        else:
            url = f"postgresql://{config.POSTGRESQL_USER}@{config.POSTGRESQL_HOST}:{config.POSTGRESQL_PORT}/{config.POSTGRESQL_DATABASE}"
        return create_engine(url, poolclass=NullPool)
    else:
        db_path = os.environ.get('DATABASE_PATH', config.DATABASE_PATH)
        if not os.path.isabs(db_path):
            db_path = os.path.abspath(os.path.join(os.path.dirname(config.BASE_DIR), db_path))
        url = f"sqlite:///{db_path}"
        engine = create_engine(url, poolclass=NullPool)

        # Apply SQLite WAL mode for concurrency
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine


_engine = None
_SessionFactory = None


def get_session_factory():
    """Get or create the session factory."""
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine())
    return _SessionFactory


def get_session() -> Session:
    """Get a new SQLAlchemy session."""
    return get_session_factory()()


# NOTE: SQLite WAL mode pragmas are applied in migrations/env.py when migrations run.
# The models/base.py is primarily for migrations and future ORM use.
# For runtime queries, continue using database.py (get_db, get_one, get_all).