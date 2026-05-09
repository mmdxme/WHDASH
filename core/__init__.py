"""
Core package - Extracted modules from the app.py monolith.

This package contains cleanly separated concerns:
- template_filters: Jinja2 template filters
- context_processors: Template context injection
- request_hooks: Before/after request middleware
- auth: Authentication decorators and helpers
- health: Health check endpoints
- constants: Application-wide constants
- user_preferences: User preference management
- db_init: Database schema initialization
- module_registration: Blueprint and module registration
"""
