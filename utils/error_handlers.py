"""
Standardized error handling for WHDASH.

This module provides consistent error handling across all routes and modules.
Use APIError for structured API errors, and register_error_handlers() in app.py.

Usage:
    from utils.error_handlers import APIError, register_error_handlers, safe_api_call

    # In app.py:
    from utils.error_handlers import register_error_handlers
    register_error_handlers(app)

    # In routes for API errors:
    raise APIError("Invalid input", status_code=400)

    # For safe route wrapping:
    @safe_api_call
    def my_api_route():
        ...
"""

from flask import jsonify, render_template, request
from werkzeug.exceptions import HTTPException
from functools import wraps
from typing import Optional, Dict, Any


class APIError(Exception):
    """
    Standard API error with status code and optional payload.

    Use this for structured API errors that should return JSON responses
    with consistent formatting.

    Args:
        message: Error message
        status_code: HTTP status code (default 400)
        payload: Optional dict with additional error data
    """

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        payload: Optional[Dict[str, Any]] = None
    ):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON response."""
        rv = dict(self.payload or {})
        rv['error'] = self.message
        rv['status_code'] = self.status_code
        return rv


def register_error_handlers(app):
    """
    Register all error handlers with the Flask app.

    Args:
        app: Flask application instance

    Usage:
        from flask import Flask
        from utils.error_handlers import register_error_handlers

        app = Flask(__name__)
        register_error_handlers(app)
    """

    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle custom APIError exceptions."""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        if request.is_json:
            return jsonify({
                'error': 'Bad request',
                'status_code': 400,
                'message': str(error.description) if hasattr(error, 'description') else 'Invalid request'
            }), 400
        return render_template('components/error_400.html', error=error), 400

    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors."""
        if request.is_json:
            return jsonify({
                'error': 'Unauthorized',
                'status_code': 401,
                'message': 'Authentication required'
            }), 401
        return render_template('components/error_401.html', error=error), 401

    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors."""
        if request.is_json:
            return jsonify({
                'error': 'Forbidden',
                'status_code': 403,
                'message': 'Access denied'
            }), 403
        return render_template('components/error_403.html', error=error), 403

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        if request.is_json:
            return jsonify({
                'error': 'Not found',
                'status_code': 404,
                'message': 'Resource not found'
            }), 404
        return render_template('components/error_404.html', error=error), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed errors."""
        if request.is_json:
            return jsonify({
                'error': 'Method not allowed',
                'status_code': 405,
                'message': f'Method {request.method} not allowed for this endpoint'
            }), 405
        return render_template('components/error_405.html', error=error), 405

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server Error."""
        app.logger.error(f"Internal error: {str(error)}", exc_info=True)
        if request.is_json:
            return jsonify({
                'error': 'Internal server error',
                'status_code': 500,
                'message': 'An unexpected error occurred'
            }), 500
        return render_template('components/error_500.html', error=error), 500

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle all other HTTP exceptions."""
        if request.is_json:
            return jsonify({
                'error': str(error),
                'status_code': error.code,
                'message': error.description if hasattr(error, 'description') else str(error)
            }), error.code
        return render_template('components/error_generic.html', error=error), error.code


def safe_api_call(func):
    """
    Decorator for safe API calls with standardized error handling.

    Wraps a route function to catch all exceptions and return
    consistent JSON error responses.

    Usage:
        @app.route('/api/data')
        @safe_api_call
        def my_api_endpoint():
            # Your code here
            return jsonify({'data': 'value'})
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            return jsonify(e.to_dict()), e.status_code
        except HTTPException:
            raise  # Let Flask's error handlers handle HTTP exceptions
        except Exception as e:
            from flask import current_app
            current_app.logger.error(
                f"Unexpected error in {func.__name__}: {str(e)}",
                exc_info=True
            )
            return jsonify({
                'error': 'An unexpected error occurred',
                'status_code': 500,
                'message': str(e) if current_app.config.get('DEBUG') else 'Internal server error'
            }), 500
    return wrapper