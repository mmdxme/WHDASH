"""
Application Factory
================
Provides a clean way to create and configure the Flask application.

This module implements the Application Factory pattern, allowing for:
- Multiple app instances with different configurations
- Easier testing
- Better code organization

Usage:
    from app_factory import create_app, register_all_routes
    
    app = create_app('production')
    # or for development
    app = create_app('development')
"""

import os
from flask import Flask, session
from functools import wraps


# =============================================================================
# APPLICATION FACTORY
# =============================================================================

def create_app(config_name: str = None) -> Flask:
    """
    Create and configure the Flask application.
    
    Args:
        config_name: Configuration to use ('development', 'production', 'testing')
    
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    load_config(app, config_name)
    
    # Initialize core systems
    initialize_core(app)
    
    return app


def load_config(app: Flask, config_name: str = None):
    """Load configuration from config module and environment."""
    from config import (
        SECRET_KEY, DATABASE_PATH, DEBUG, ENV,
        UPLOAD_FOLDER, PERMANENT_SESSION_LIFETIME,
        APP_NAME, DEFAULT_LANGUAGE, DEFAULT_THEME
    )
    
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['DEBUG'] = DEBUG
    app.config['ENV'] = ENV
    app.config['DATABASE_PATH'] = DATABASE_PATH
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['PERMANENT_SESSION_LIFETIME'] = PERMANENT_SESSION_LIFETIME
    
    app.config['APP_NAME'] = APP_NAME
    app.config['DEFAULT_LANGUAGE'] = DEFAULT_LANGUAGE
    app.config['DEFAULT_THEME'] = DEFAULT_THEME
    
    # Session
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = True


def initialize_core(app: Flask):
    """
    Initialize core Flask functionality.
    """
    # Import database
    from database import get_db, get_db_context, initialize_platform_schema
    app.get_db = get_db
    app.get_db_context = get_db_context
    
    # Initialize platform schema
    initialize_platform_schema()
    
    # Initialize permissions
    from permissions import initialize_permissions
    initialize_permissions()
    
    # Initialize settings
    from settings import initialize_settings
    initialize_settings()


# =============================================================================
# ROUTE REGISTRATION HELPERS
# =============================================================================

def register_all_routes(app: Flask):
    """
    Register all module routes with the application.
    This replaces the manual route registration in app.py.
    """
    from functools import partial
    
    # Get shared helpers
    from permissions import require_permission, user_has_permission
    from database import get_db
    
    # Define which modules need which arguments
    modules_with_db = [
        'wms_routes',
        'planning_routes',
        'sales_routes',
        'sales_suite_routes',
        'procurement_routes',
        'google_workspace_routes',
        'email_manager',
    ]
    
    modules_with_permissions = [
        'sales_routes',
        'sales_suite_routes',
    ]
    
    # Import route registration functions
    from hr_routes import register_hr_routes
    from wms_routes import register_wms_routes
    from logistics_routes import register_logistics_routes
    from company_routes import register_company_routes
    from planning_routes import register_planning_routes
    from marketing_routes import register_marketing_routes
    from customer_intelligence_routes import register_ci_routes
    from social_media_routes import register_social_media_routes
    from sales_routes import register_sales_routes
    from sales_suite_routes import register_sales_suite_routes
    from admin_routes import register_admin_routes
    from procurement_routes import register_procurement_routes
    from profile_routes import register_profile_routes
    from asset_routes import register_asset_routes
    from maintenance_routes import register_maintenance_routes
    from finance_routes import register_finance_routes
    from quality_routes import register_quality_routes
    from ecommerce_routes import register_ecommerce_routes
    from document_routes import register_document_routes
    from bi_routes import register_bi_routes
    from bi_advanced_routes import register_advanced_bi_routes
    from api_gateway_routes import register_api_gateway_routes
    from rest_api import register_rest_api
    
    # Create require_login decorator
    from functools import wraps
    from flask import request, redirect, url_for, flash
    
    def require_login(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            allowed_routes = ['login', 'static', 'set_language']
            if request.endpoint not in allowed_routes and 'user_id' not in session:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    
    # Register routes
    register_hr_routes(app)
    register_wms_routes(app, get_db)
    register_logistics_routes(app)
    register_company_routes(app)
    register_planning_routes(app, get_db)
    register_marketing_routes(app)
    register_ci_routes(app)
    register_social_media_routes(app)
    
    # Modules with permission helpers
    register_sales_routes(app, require_login, user_has_permission, get_db)
    register_sales_suite_routes(app, require_login, user_has_permission, get_db)
    
    register_admin_routes(app)
    register_procurement_routes(app, get_db)
    register_profile_routes(app)
    register_asset_routes(app)
    register_maintenance_routes(app)
    register_finance_routes(app)
    register_quality_routes(app)
    register_ecommerce_routes(app)
    register_document_routes(app)
    register_bi_routes(app)
    register_advanced_bi_routes(app)
    register_api_gateway_routes(app, require_login, user_has_permission, get_db)
    register_rest_api(app)


# =============================================================================
# BLUEPRINT REGISTRATION (FUTURE)
# =============================================================================

def create_module_blueprint(module_name: str, url_prefix: str = None):
    """
    Create a Flask Blueprint for a module.
    This is for future refactoring to use proper Flask Blueprints.
    
    Args:
        module_name: Name of the module
        url_prefix: URL prefix for all routes in this blueprint
    
    Returns:
        Flask Blueprint
    """
    from flask import Blueprint
    
    bp = Blueprint(
        module_name,
        module_name,
        url_prefix=url_prefix or f'/{module_name}',
        template_folder='templates',
        static_folder='static'
    )
    
    return bp


# =============================================================================
# CONTEXT PROCESSORS
# =============================================================================

def register_context_processors(app: Flask):
    """Register context processors for template variables."""
    
    @app.context_processor
    def inject_user():
        """Inject user info into all templates."""
        from flask import session
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


# =============================================================================
# ERROR HANDLERS
# =============================================================================

def register_error_handlers(app: Flask):
    """Register custom error handlers."""
    
    from flask import render_template, jsonify
    
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Not found'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Access forbidden'}), 403
        return render_template('errors/403.html'), 403


# =============================================================================
# BEFORE/AFTER REQUEST HANDLERS
# =============================================================================

def register_request_handlers(app: Flask):
    """Register before/after request handlers."""
    
    from flask import session, request, redirect, url_for
    from datetime import datetime
    
    @app.before_request
    def check_session_auth():
        """Check authentication before each request."""
        allowed_routes = ['login', 'static', 'set_language', 'api_health']
        if request.endpoint not in allowed_routes and 'user_id' not in session:
            # Don't redirect API requests
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
    
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses."""
        from config import SECURITY_HEADERS
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        return response


# =============================================================================
# CLI COMMANDS
# =============================================================================

def register_cli_commands(app: Flask):
    """Register Flask CLI commands."""
    
    @app.cli.command('init-db')
    def init_db_command():
        """Initialize the database."""
        from database import initialize_platform_schema
        initialize_platform_schema()
        print('Database initialized.')
    
    @app.cli.command('init-perms')
    def init_perms_command():
        """Initialize permissions."""
        from permissions import initialize_permissions
        initialize_permissions()
        print('Permissions initialized.')
    
    @app.cli.command('init-settings')
    def init_settings_command():
        """Initialize settings."""
        from settings import initialize_settings
        initialize_settings()
        print('Settings initialized.')
    
    @app.cli.command('seed-test')
    def seed_test_command():
        """Seed test data."""
        from seed_sample_data import seed_all_data
        seed_all_data()
        print('Test data seeded.')


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point for running the application."""
    import os
    
    # Create app
    app = create_app()
    
    # Register components
    register_context_processors(app)
    register_error_handlers(app)
    register_request_handlers(app)
    register_cli_commands(app)
    register_all_routes(app)
    
    # Run
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config.get('DEBUG', False))


if __name__ == '__main__':
    main()
