"""
MMDx Application Entry Point
============================

This is the main Flask application file for the MMDx ERP system.

ARCHITECTURAL CHANGE:
This file has been refactored from a ~10,000 line monolith to a thin
orchestration layer. All implementation has been moved to the `application/` package:

- application/bootstrap.py - Application creation and initialization
- application/extensions.py - Flask extension setup
- application/hooks.py - Before/after request handlers
- application/context_processors.py - Template context processors
- application/template_filters.py - Jinja2 template filters
- application/routes_registry.py - Blueprint and route registration
- application/security.py - CSRF and security utilities
- application/database_init.py - Database initialization logic
- translation_loader.py - JSON-based translation loading

Usage:
    from application.bootstrap import create_app
    app = create_app()

For development:
    python app.py

For production (using gunicorn):
    gunicorn -c gunicorn_config.py wsgi:app
"""

import os
import sys

# Add parent directory to path for imports
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# SUPPORT FOR LAYERED ARCHITECTURE (MVC)
# Automatically resolve imports from structural directories
sys.path.insert(0, os.path.join(BASE_DIR, 'controllers'))
sys.path.insert(0, os.path.join(BASE_DIR, 'models'))
sys.path.insert(0, os.path.join(BASE_DIR, 'services'))
sys.path.insert(0, os.path.join(BASE_DIR, 'repositories'))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import the application factory and initialization
from application.bootstrap import create_app, init_app
from application.extensions import init_extensions
from application.hooks import register_hooks, register_error_handlers
from application.context_processors import register_context_processors
from application.template_filters import register_template_filters
from application.routes_registry import register_blueprints, register_all_routes, register_health_routes
from application.security import generate_csrf_token

# Import translation loader for template access
from translation_loader import (
    get_translation,
    get_translations,
    is_rtl,
    get_language_direction,
    LANGUAGES,
    RTL_LANGUAGES
)

# Import platform utilities (for template context)
from database import (
    get_db,
    get_db_context,
    get_one,
    get_all,
    initialize_platform_schema,
    log_audit,
    get_user_notifications,
    get_platform_setting,
    set_platform_setting,
    STANDARD_STATUSES,
    STATUS_COLORS,
    cached_query,
    get_cache,
    QueryCache
)

from permissions import (
    get_user_permissions,
    get_role_permissions,
    user_has_permission,
    require_permission,
    require_module_access,
    get_module_resources,
    initialize_permissions,
    invalidate_user_permission_cache
)

from settings import (
    get_setting,
    set_setting,
    get_settings_by_category,
    DEFAULT_SETTINGS,
    initialize_settings
)

from navigation import (
    MENU_STRUCTURE,
    get_main_menu,
    get_breadcrumbs,
    get_page_title,
    get_active_module,
    prepare_menu_for_template,
    get_notification_badge,
    get_task_badge,
    get_menu_label
)

from master_data import (
    get_canonical_customer,
    get_all_canonical_customers,
    get_canonical_item,
    get_all_canonical_items,
    get_canonical_employee,
    get_all_canonical_employees,
    resolve_customer,
    resolve_item,
    run_master_data_health_check,
    initialize_master_data
)

from reporting import (
    get_dashboard_stats,
    build_inventory_report,
    build_sales_report,
    build_delivery_report,
    build_hr_attendance_report,
    build_planning_alerts_report,
    export_to_excel,
    export_to_csv,
    initialize_reporting
)

from theme_system import (
    get_available_themes,
    get_theme_config,
    get_theme_tokens,
    get_chart_palette,
    is_dark_theme,
    validate_theme,
    get_default_theme,
    get_all_theme_ids,
    CHART_PALETTES,
    AVAILABLE_THEMES
)

from theme_engine import (
    theme_css_variables,
    theme_inline_style,
    theme_data_attrs,
    chartjs_config,
    theme_preview_data,
    get_status_color_classes,
    get_priority_classes
)

# Import the database initialization function
from application.database_init import init_db

# NOTE: Manual route and model imports have been removed.
# Routes are now loaded dynamically via application.routes_registry
# Database initialization is now handled by scripts/init_db.py


# ============================================================================
# Application Factory
# ============================================================================

def setup_application():
    """
    Create and configure the Flask application.

    This replaces the monolithic app.py initialization with a clean,
    modular setup process.
    """
    # Create the Flask app
    app = create_app()

    # Load configuration from config module
    from config import (
        SECRET_KEY, ENV, DEBUG, DATABASE_PATH as CONFIG_DATABASE_PATH,
        UPLOAD_FOLDER as CONFIG_UPLOAD_FOLDER
    )
    import config as app_config

    app.secret_key = SECRET_KEY
    app.config['TEMPLATES_AUTO_RELOAD'] = DEBUG
    app.jinja_env.auto_reload = DEBUG

    # Configure paths
    DATABASE = os.environ.get('DATABASE_PATH', CONFIG_DATABASE_PATH)
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', CONFIG_UPLOAD_FOLDER)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Session security
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = ENV.lower() == 'production'

    # Session directory
    if hasattr(app_config, 'SESSION_FILE_DIR'):
        app.config['SESSION_FILE_DIR'] = app_config.SESSION_FILE_DIR
        os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

    # Register template filters
    register_template_filters(app)

    # Register context processors
    register_context_processors(app)

    # Register request hooks
    register_hooks(app)

    # Register error handlers
    register_error_handlers(app)

    # Initialize extensions
    init_extensions(app)

    # Register blueprints
    register_blueprints(app)

    # Register health check routes
    register_health_routes(app)

    # Register module routes using dynamic registry
    register_all_routes(app)

    # Register admin routes (function-based pattern)
    from admin_routes import register_admin_routes
    register_admin_routes(app)

    # Add simple login route
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        from flask import render_template, request, redirect, url_for, session, flash
        if request.method == 'POST':
            username = request.form.get('username', '')
            password = request.form.get('password', '')
            if username and password:
                from database import get_db
                db = get_db()
                user = db.execute("""
                    SELECT id, username, email, role_id, password
                    FROM users WHERE username = ? AND is_active = 1 LIMIT 1
                """, (username,)).fetchone()
                db.close()
                if user and user['password'] == password:
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['email'] = user['email']
                    session['role_id'] = user['role_id']
                    flash('Login successful', 'success')
                    return redirect(url_for('index'))
            flash('Invalid credentials', 'error')
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        from flask import session, flash, redirect, url_for
        session.clear()
        flash('Logged out', 'info')
        return redirect(url_for('login'))

    return app


# NOTE: _register_all_module_routes and _run_module_initializations have been 
# removed to prevent runtime blocking. Use scripts/init_db.py for DB setup.


# ============================================================================
# Application Instance
# ============================================================================

# Create the application instance
app = setup_application()


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    # Always enable debug mode for local development
    os.environ['FLASK_DEBUG'] = '1'
    app.debug = True
    host = '0.0.0.0'
    port = 5000
    print(f"Starting Flask server on http://localhost:{port}")
    print(f"Debug mode: ON")
    # Disable reloader on Windows to avoid import issues with debug mode
    app.run(host=host, port=port, debug=True, use_reloader=False)
    print(f"Server stopped")