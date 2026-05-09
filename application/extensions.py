"""
Extensions Module
================

Centralized initialization for Flask extensions and third-party integrations.
This module handles extension setup that was previously mixed into app.py.

Currently the project uses a custom database layer rather than SQLAlchemy,
but this module provides a clean structure for future extension additions.

Usage:
    from app.extensions import init_extensions

    app = create_app()
    init_extensions(app)
"""

from flask import Flask
from typing import Optional


def init_extensions(app: Flask) -> None:
    """
    Initialize Flask extensions.

    Currently minimal as the project uses custom database/session handling.
    This module provides a clean structure for adding extensions later.

    Args:
        app: Flask application instance
    """
    # Future extension initialization goes here
    # Examples:
    # - Flask-SQLAlchemy for ORM
    # - Flask-Login for authentication
    # - Flask-Caching for caching
    # - Flask-Migrate for database migrations

    # For now, we initialize the session backend
    _init_session_backend(app)


def _init_session_backend(app: Flask) -> None:
    """
    Initialize session backend based on configuration.

    Supports:
    - Redis (production recommended)
    - Filesystem (development default)
    """
    from config import SESSION_TYPE, REDIS_URL, SESSION_FILE_DIR

    if SESSION_TYPE == 'redis' and REDIS_URL:
        try:
            from flask_session import Session
            app.config['SESSION_TYPE'] = 'redis'
            app.config['SESSION_PERMANENT'] = True
            app.config['PERMANENT_SESSION_LIFETIME'] = 120  # minutes
            Session(app)
        except ImportError:
            # Fallback to filesystem if redis unavailable
            app.config['SESSION_TYPE'] = 'filesystem'
            app.config['SESSION_FILE_DIR'] = SESSION_FILE_DIR
    else:
        # Filesystem sessions (default for development)
        app.config['SESSION_TYPE'] = 'filesystem'
        app.config['SESSION_PERMANENT'] = True
        app.config['SESSION_FILE_DIR'] = SESSION_FILE_DIR


def init_optional_extensions(app: Flask) -> None:
    """
    Initialize optional extensions that may not be installed.

    This allows the app to run without certain optional dependencies.

    Args:
        app: Flask application instance
    """
    # Redis cache (optional)
    try:
        import redis
        from config import REDIS_CACHE_URL, REDIS_URL

        redis_url = REDIS_CACHE_URL or REDIS_URL
        if redis_url:
            client = redis.from_url(redis_url)
            client.ping()
            app.config['REDIS_CLIENT'] = client
    except Exception:
        pass

    # Celery (optional - for background tasks)
    try:
        from celery import Celery
        from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

        if CELERY_BROKER_URL:
            app.config['CELERY_BROKER_URL'] = CELERY_BROKER_URL
            app.config['CELERY_RESULT_BACKEND'] = CELERY_RESULT_BACKEND
    except Exception:
        pass