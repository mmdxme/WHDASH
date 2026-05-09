"""
Application Package
===================

This package contains the core application infrastructure modules that were
extracted from the monolithic app.py file.

Modules:
- bootstrap: Application startup and initialization
- extensions: Flask extension initialization
- hooks: Request/response hooks and middleware
- context_processors: Template context processors
- template_filters: Jinja2 template filters
- routes_registry: Blueprint and route registration
- security: CSRF and security utilities
- database_init: Database initialization functions

Usage:
    from application.bootstrap import create_app

    app = create_app()
"""

from .bootstrap import create_app, init_app

__all__ = ['create_app', 'init_app']