"""
CSRF Protection Module
======================
Provides CSRF token generation and validation for all mutating routes.

Usage:
    from csrf_protection import csrf_protected, generate_csrf_token

    @app.route('/submit', methods=['POST'])
    @csrf_protected
    def submit():
        # Your code here

    # In templates, access csrf_token to include in forms:
    # <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
"""

import hmac
import secrets
import os
from functools import wraps
from flask import session, request, abort, g


# CSRF token configuration
CSRF_TOKEN_LENGTH = 32  # bytes
CSRF_HEADER_NAME = 'X-CSRF-Token'
CSRF_FORM_FIELD = 'csrf_token'


def generate_csrf_token():
    """
    Generate a new CSRF token and store it in the session.
    Call this on login and whenever session is created.

    Returns:
        str: The generated CSRF token
    """
    token = secrets.token_hex(CSRF_TOKEN_LENGTH)
    session['csrf_token'] = token
    session['csrf_token_time'] = os.time.time() if hasattr(os, 'time') else __import__('time').time()
    return token


def get_csrf_token():
    """
    Get the current CSRF token from session.
    Generates a new one if none exists.

    Returns:
        str: The CSRF token
    """
    return session.get('csrf_token', generate_csrf_token())


def validate_csrf_token(token):
    """
    Validate a CSRF token using constant-time comparison.

    Args:
        token: The token to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not token or not session.get('csrf_token'):
        return False

    # Use hmac.compare_digest for timing-safe comparison
    return hmac.compare_digest(token, session['csrf_token'])


def csrf_protected(f):
    """
    Decorator to protect routes from CSRF attacks.
    Validates CSRF token on POST/PUT/PATCH/DELETE requests.

    Usage:
        @app.route('/api/data', methods=['POST'])
        @csrf_protected
        def create_data():
            return jsonify({'status': 'success'})

    Note: This decorator must be applied AFTER @login_required or similar
    authentication decorators to ensure session is available.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Only check CSRF on mutating methods
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            # Get token from header or form field
            token = request.headers.get(CSRF_HEADER_NAME)

            if not token:
                token = request.form.get(CSRF_FORM_FIELD)

            if not token:
                token = request.args.get(CSRF_FORM_FIELD)

            if not token:
                abort(403, description="CSRF token missing")

            if not validate_csrf_token(token):
                abort(403, description="Invalid CSRF token")

        return f(*args, **kwargs)

    return decorated_function


def init_csrf(app):
    """
    Initialize CSRF protection for a Flask app.
    Call this after app is created, before running.

    Args:
        app: Flask application instance

    Usage:
        from flask import Flask
        from csrf_protection import init_csrf

        app = Flask(__name__)
        init_csrf(app)
    """
    @app.before_request
    def check_csrf_exempt():
        # Make csrf_token available in all templates
        pass

    @app.after_request
    def csrf_headers(response):
        # Add CSRF token to response headers for API routes
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            response.headers['X-CSRF-Token'] = get_csrf_token()
        return response

    # Add template context processor
    @app.context_processor
    def csrf_context():
        return {
            'csrf_token': get_csrf_token(),
            'csrf_header_name': CSRF_HEADER_NAME
        }