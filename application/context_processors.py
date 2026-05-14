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

    @app.context_processor
    def inject_user_preferences():
        """Inject user preferences into all templates."""
        try:
            from flask import session
            from database import get_one

            user_id = session.get('user_id')
            if user_id:
                prefs = get_one("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,))
                if prefs:
                    # Build user_preferences object with computed properties
                    import copy
                    user_prefs = dict(prefs)

                    # Compute direction_resolved
                    interface_direction = user_prefs.get('interface_direction', 'auto')
                    language = user_prefs.get('language', 'en')
                    if interface_direction == 'auto':
                        user_prefs['direction_resolved'] = 'rtl' if language in ('fa', 'ar', 'he', 'ur') else 'ltr'
                    else:
                        user_prefs['direction_resolved'] = interface_direction

                    # Compute is_dark
                    theme = user_prefs.get('theme', 'default')
                    user_prefs['is_dark'] = theme in ('dark', 'midnight', 'AMOLED Dark')

                    # Compute font_size_value
                    density = user_prefs.get('density', 'default')
                    font_size_map = {'compact': '13px', 'default': '14px', 'comfortable': '15px', 'spacious': '16px'}
                    user_prefs['font_size_value'] = font_size_map.get(density, '14px')

                    # Compute font_weight_value
                    font_weight = user_prefs.get('font_weight', 'regular')
                    font_weight_map = {'light': '300', 'regular': '400', 'medium': '500', 'semibold': '600', 'bold': '700'}
                    user_prefs['font_weight_value'] = font_weight_map.get(font_weight, '400')

                    # Font stack
                    user_prefs['font_stack'] = user_prefs.get('font_stack', 'Manrope, Outfit, Space Grotesk, sans-serif')

                    # Currency symbol
                    currency = user_prefs.get('currency', 'AED')
                    currency_symbols = {'AED': 'د.إ', 'USD': '$', 'EUR': '€', 'GBP': '£', 'SAR': '﷼', 'QAR': '﷼', 'KWD': 'د.ك', 'BHD': '.د.ب', 'OMR': 'ر.ع.'}
                    user_prefs['currency_symbol'] = currency_symbols.get(currency, currency)

                    # Timezone label
                    user_prefs['timezone_label'] = user_prefs.get('timezone_label', 'GST (UTC+4)')

                    return {'user_preferences': user_prefs}
            # Return default preferences for anonymous users
            return {
                'user_preferences': {
                    'direction_resolved': 'ltr',
                    'theme': 'default',
                    'is_dark': False,
                    'language': 'en',
                    'density': 'default',
                    'reduced_motion': False,
                    'currency': 'AED',
                    'currency_symbol': 'د.إ',
                    'font_size_value': '14px',
                    'font_weight_value': '400',
                    'font_stack': 'Manrope, Outfit, Space Grotesk, sans-serif',
                    'timezone_label': 'GST (UTC+4)',
                }
            }
        except Exception:
            # Fallback for errors
            return {
                'user_preferences': {
                    'direction_resolved': 'ltr',
                    'theme': 'default',
                    'is_dark': False,
                    'language': 'en',
                    'density': 'default',
                    'reduced_motion': False,
                    'currency': 'AED',
                    'currency_symbol': 'د.إ',
                    'font_size_value': '14px',
                    'font_weight_value': '400',
                    'font_stack': 'Manrope, Outfit, Space Grotesk, sans-serif',
                    'timezone_label': 'GST (UTC+4)',
                }
            }