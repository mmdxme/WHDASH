"""
Request Hooks Module
====================

Flask before/after request handlers for common operations.
This module centralizes hook logic that was previously scattered in app.py.

Hooks included:
- Authentication checking
- Security headers injection
- Request timing/logging
- Response processing

Usage:
    from app.hooks import register_hooks

    app = create_app()
    register_hooks(app)
"""

from flask import Flask, request, session, redirect, url_for, jsonify, g
from functools import wraps
from typing import Callable, List
import time


# ============================================================================
# Authentication Decorators
# ============================================================================

def require_login(f: Callable) -> Callable:
    """
    Decorator that redirects unauthenticated users to login.

    Usage:
        @app.route('/protected')
        @require_login
        def protected_route():
            return "Protected content"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        allowed_routes = ['login', 'static', 'set_language', 'health', 'ready', 'live']
        if request.endpoint not in allowed_routes and 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def require_api_auth(f: Callable) -> Callable:
    """
    Decorator that returns 401 for unauthenticated API requests.

    Usage:
        @app.route('/api/protected')
        @require_api_auth
        def api_protected():
            return jsonify({'data': 'secret'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# Request Hooks Registration
# ============================================================================

def register_hooks(app: Flask) -> None:
    """
    Register all request hooks with the Flask application.

    Args:
        app: Flask application instance
    """

    @app.before_request
    def before_request_hook():
        """Execute before each request."""
        # Store request start time for performance monitoring
        g.request_start_time = time.time()

        # Additional before-request logic can be added here
        pass

    @app.after_request
    def after_request_hook(response):
        """Execute after each request - add security headers."""
        from config import SECURITY_HEADERS

        # Add security headers
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value

        # Add request timing header (optional, for debugging)
        if hasattr(g, 'request_start_time'):
            elapsed = time.time() - g.request_start_time
            response.headers['X-Request-Time'] = f'{elapsed:.3f}s'

        return response

    @app.teardown_request
    def teardown_request_hook(exception=None):
        """Execute after each request, even if an exception occurred."""
        # Clean up any request-scoped resources here
        pass


def register_api_hooks(app: Flask) -> None:
    """
    Register API-specific hooks.

    Args:
        app: Flask application instance
    """

    @app.before_request
    def check_api_auth():
        """Check authentication for API routes."""
        if request.path.startswith('/api/'):
            allowed_paths = ['/api/health', '/api/login', '/api/healthcheck']
            if request.path not in allowed_paths and 'user_id' not in session:
                return jsonify({'error': 'Authentication required'}), 401


# ============================================================================
# Error Handlers
# ============================================================================

def register_error_handlers(app: Flask) -> None:
    """
    Register custom error handlers.

    Args:
        app: Flask application instance
    """

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


# ============================================================================
# Template Imports Helper
# ============================================================================

def render_template(template_name, **context):
    """Lazy import for render_template to avoid circular imports."""
    from flask import render_template as flask_render
    return flask_render(template_name, **context)