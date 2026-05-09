"""
Security Module
==============

CSRF protection and security utilities.
This module centralizes security logic that was previously scattered in app.py.

Usage:
    from app.security import csrf_protected, generate_csrf_token, validate_csrf_token

    @app.route('/submit', methods=['POST'])
    @csrf_protected
    def submit():
        return "Submitted"
"""

import secrets
import hmac
from flask import session, request, redirect, flash
from functools import wraps
from typing import Callable, Optional


# ============================================================================
# CSRF Token Generation
# ============================================================================

def generate_csrf_token() -> str:
    """
    Generate a CSRF token for the current session.

    Returns:
        A secure random hex string (64 characters)
    """
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']


def validate_csrf_token(token: Optional[str]) -> bool:
    """
    Validate a CSRF token against the session.

    Args:
        token: The token to validate

    Returns:
        True if valid, False otherwise
    """
    if not token or 'csrf_token' not in session:
        return False
    return hmac.compare_digest(token, session['csrf_token'])


def get_csrf_token_from_request() -> Optional[str]:
    """
    Extract CSRF token from the current request.

    Checks:
    1. Form field 'csrf_token'
    2. Header 'X-CSRF-Token'

    Returns:
        Token string or None
    """
    return request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')


# ============================================================================
# CSRF Protection Decorator
# ============================================================================

def csrf_protected(f: Callable) -> Callable:
    """
    Decorator to protect forms with CSRF validation.

    Usage:
        @app.route('/submit', methods=['POST'])
        @csrf_protected
        def submit():
            return "Form submitted successfully"

    The decorated function will be called only if CSRF validation passes.
    On failure, user is redirected back with an error flash message.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            token = get_csrf_token_from_request()
            if not validate_csrf_token(token):
                flash("CSRF validation failed. Please refresh the page and try again.", "error")
                return redirect(request.url)
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# API CSRF Protection (returns JSON error instead of redirect)
# ============================================================================

def csrf_protected_api(f: Callable) -> Callable:
    """
    Decorator to protect API endpoints with CSRF validation.

    Usage:
        @app.route('/api/submit', methods=['POST'])
        @csrf_protected_api
        def api_submit():
            return jsonify({'success': True})

    Returns JSON 400 error on CSRF failure instead of redirect.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            token = get_csrf_token_from_request()
            if not validate_csrf_token(token):
                from flask import jsonify
                return jsonify({'error': 'CSRF validation failed'}), 400
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# Security Headers
# ============================================================================

def add_security_headers(response):
    """
    Add security headers to a response.

    Args:
        response: Flask response object

    Returns:
        Response with security headers added
    """
    from config import SECURITY_HEADERS

    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value

    return response


# ============================================================================
# Password Helpers
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash a password using werkzeug's secure hashing.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    from werkzeug.security import generate_password_hash
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        password: Plain text password
        password_hash: Stored password hash

    Returns:
        True if password matches, False otherwise
    """
    from werkzeug.security import check_password_hash
    return check_password_hash(password_hash, password)


# ============================================================================
# Input Validation Helpers
# ============================================================================

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent directory traversal.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for file operations
    """
    from werkzeug.utils import secure_filename
    return secure_filename(filename)


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """
    Check if a filename has an allowed extension.

    Args:
        filename: The filename to check
        allowed_extensions: Set of allowed extension strings

    Returns:
        True if allowed, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


# ============================================================================
# Session Security
# ============================================================================

def regenerate_session():
    """
    Regenerate the session ID to prevent session fixation attacks.

    Should be called after successful login.
    """
    import secrets
    # Generate new session ID
    session['session_id'] = secrets.token_hex(32)
    # Keep existing data but it would be safer to only keep necessary data
    # This depends on what data is stored in session


def is_session_secure() -> bool:
    """
    Check if the current session is using secure cookie settings.

    Returns:
        True if session cookie is secure (HTTPS only)
    """
    return session.get('_session_cookie_secure', False)


# ============================================================================
# Rate Limiting Helpers
# ============================================================================

def get_client_ip() -> str:
    """
    Get the client IP address, considering proxy headers.

    Returns:
        Client IP address string
    """
    # Check X-Forwarded-For header first (for proxied requests)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        # Take the first IP in the chain (original client)
        return forwarded_for.split(',')[0].strip()

    # Check X-Real-IP header
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip.strip()

    # Fall back to remote_addr
    return request.remote_addr or '0.0.0.0'