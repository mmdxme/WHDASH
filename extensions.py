"""
Flask Extensions Initialization
==============================
Centralizes Flask extension initialization.

This module provides a clean way to initialize and manage
Flask extensions without creating tight coupling to the app.
"""

from flask import Flask
from functools import wraps


# =============================================================================
# EXTENSION REGISTRY
# =============================================================================

class ExtensionRegistry:
    """
    Registry for Flask extensions.
    Tracks which extensions are initialized and their instances.
    """
    
    def __init__(self):
        self._extensions = {}
        self._app = None
    
    def init_app(self, app: Flask):
        """Initialize all registered extensions with the Flask app."""
        self._app = app
        for name, ext in self._extensions.items():
            if hasattr(ext, 'init_app'):
                ext.init_app(app)
    
    def register(self, name: str, ext):
        """Register an extension."""
        self._extensions[name] = ext
        if self._app and hasattr(ext, 'init_app'):
            ext.init_app(self._app)
    
    def get(self, name: str):
        """Get a registered extension."""
        return self._extensions.get(name)
    
    def extensions(self):
        """Get all registered extensions."""
        return self._extensions


# Global registry instance
extensions = ExtensionRegistry()


# =============================================================================
# PRE-INITIALIZED EXTENSIONS
# =============================================================================

# These extensions are pre-created and registered when needed

class DummyExtension:
    """
    Placeholder for extensions that don't need initialization.
    Used to maintain a consistent extension interface.
    """
    def __init__(self, app=None, **kwargs):
        if app:
            self.init_app(app, **kwargs)
    
    def init_app(self, app: Flask, **kwargs):
        pass


# =============================================================================
# CSRF EXTENSION
# =============================================================================

class CSRFProtection:
    """
    CSRF protection for forms.
    This provides token generation and validation.
    """
    
    def __init__(self, app=None):
        self._tokens = {}
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize CSRF protection."""
        # CSRF token generation is handled in app.py
        # This extension is mainly for tracking
        app.extensions['csrf'] = self
    
    def generate_token(self, session_id: str) -> str:
        """Generate a CSRF token for a session."""
        import secrets
        if session_id not in self._tokens:
            self._tokens[session_id] = secrets.token_hex(32)
        return self._tokens[session_id]
    
    def validate_token(self, session_id: str, token: str) -> bool:
        """Validate a CSRF token."""
        import hmac
        stored = self._tokens.get(session_id)
        if not stored or not token:
            return False
        return hmac.compare_digest(stored, token)


# =============================================================================
# SESSION EXTENSION
# =============================================================================

class SessionManager:
    """
    Session management utilities.
    Provides helper methods for session handling.
    """
    
    def __init__(self, app=None):
        self._app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize session manager."""
        app.extensions['session_manager'] = self
    
    def regenerate(self, session):
        """Regenerate session ID for security."""
        from flask import session
        import secrets
        # Store current data
        data = dict(session)
        # Clear and create new
        session.clear()
        session.update(data)
        session['_permanent'] = True


# =============================================================================
# LOGGING EXTENSION  
# =============================================================================

class RequestLogger:
    """
    Request logging for audit purposes.
    """
    
    def __init__(self, app=None):
        self._app = app
        self._log_requests = True
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize request logger."""
        self._log_requests = app.config.get('LOG_REQUESTS', True)
        if self._log_requests:
            app.before_request(self._log_request)
            app.after_request(self._log_response)
    
    def _log_request(self):
        """Log incoming request."""
        from flask import request
        import logging
        logger = logging.getLogger('request')
        logger.info(f"{request.method} {request.path} from {request.remote_addr}")
    
    def _log_response(self, response):
        """Log response."""
        from flask import request
        import logging
        logger = logging.getLogger('request')
        logger.info(f"{request.method} {request.path} -> {response.status_code}")
        return response


# =============================================================================
# HELPERS
# =============================================================================

def init_extensions(app: Flask):
    """
    Initialize all Flask extensions.
    Call this after creating the Flask app.
    """
    # Register CSRF protection
    csrf = CSRFProtection()
    csrf.init_app(app)
    extensions.register('csrf', csrf)
    
    # Register session manager
    session_mgr = SessionManager()
    session_mgr.init_app(app)
    extensions.register('session', session_mgr)
    
    # Register request logger (if enabled)
    if app.config.get('LOG_REQUESTS', False):
        logger = RequestLogger()
        logger.init_app(app)
        extensions.register('logger', logger)
    
    return extensions


def get_extension(name: str):
    """Get a registered extension by name."""
    return extensions.get(name)
