"""
Context Processors Module
=========================

Flask template context processors that inject variables into all templates.
This module centralizes context processor logic that was previously in app.py.

Usage:
    from app.context_processors import register_context_processors

    app = create_app()
    register_context_processors(app)
"""

from flask import Flask, session


def register_context_processors(app: Flask) -> None:
    """
    Register all context processors with the Flask application.

    Args:
        app: Flask application instance
    """

    @app.context_processor
    def inject_user():
        """Inject user session data into all templates."""
        return {
            'user_id': session.get('user_id'),
            'username': session.get('username'),
            'role_name': session.get('role_name'),
            'company_id': session.get('company_id'),
        }

    @app.context_processor
    def inject_csrf_token():
        """Inject CSRF token into all templates."""
        import secrets
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
        return {'csrf_token': session.get('csrf_token')}

    @app.context_processor
    def inject_format_time():
        """Inject format_time function for human-readable timestamps."""
        from datetime import datetime

        def format_time(value):
            if value is None:
                return ''
            if isinstance(value, str):
                try:
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    return value
            elif isinstance(value, datetime):
                dt = value
            else:
                return str(value)

            now = datetime.now()
            diff = now - dt
            total_seconds = diff.total_seconds()

            if total_seconds < 0:
                return dt.strftime('%H:%M')
            if total_seconds < 60:
                return 'now'
            if total_seconds < 3600:
                minutes = int(total_seconds / 60)
                return f'{minutes}m'
            if total_seconds < 86400:
                hours = int(total_seconds / 3600)
                return f'{hours}h'
            if total_seconds < 604800:
                days = int(total_seconds / 86400)
                return f'{days}d'
            return dt.strftime('%Y-%m-%d')

        return {'format_time': format_time}

    @app.context_processor
    def inject_app_config():
        """Inject application configuration into templates."""
        from config import APP_NAME, DEFAULT_LANGUAGE, DEFAULT_THEME

        return {
            'app_name': APP_NAME,
            'default_language': DEFAULT_LANGUAGE,
            'default_theme': DEFAULT_THEME,
        }

    @app.context_processor
    def inject_navigation():
        """Inject navigation helpers into templates."""
        try:
            from flask import session, request
            from navigation import get_main_menu, prepare_menu_for_template
            user_id = session.get('user_id')
            if user_id:
                language = session.get('language', 'en')
                current_path = request.path
                return {
                    'main_menu': prepare_menu_for_template(get_main_menu(user_id, language), current_path),
                }
            return {'main_menu': []}
        except ImportError:
            return {'main_menu': []}

    @app.context_processor
    def inject_translation_helpers():
        """Inject translation helpers into templates."""
        try:
            from translation_loader import get_translations, is_rtl, get_language_direction
            return {
                'get_translations': get_translations,
                'is_rtl': is_rtl,
                'get_language_direction': get_language_direction,
            }
        except ImportError:
            # Fallback if translations not available
            return {
                'get_translations': lambda lang: {},
                'is_rtl': lambda lang: False,
                'get_language_direction': lambda lang: 'ltr',
            }