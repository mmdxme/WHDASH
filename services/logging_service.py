"""
Logging Service
================
Centralized logging configuration for the platform.

Provides:
- Structured logging configuration
- Request/response logging
- Error logging with context
- Audit logging
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from functools import wraps


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

def setup_logging(app=None, log_level: str = 'INFO', log_file: str = None):
    """
    Configure application logging.

    Args:
        app: Flask application instance
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (None for no file logging)
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create formatter
    detailed_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s '
        '[%(filename)s:%(lineno)d PID:%(process)d]'
    )

    simple_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s'
    )

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)

    # Application-specific logger
    if app:
        app.logger.setLevel(numeric_level)

    return root_logger


# =============================================================================
# REQUEST LOGGING
# =============================================================================

def log_request(request, user_id=None):
    """
    Log an incoming HTTP request.

    Args:
        request: Flask request object
        user_id: ID of authenticated user (if any)
    """
    logger = logging.getLogger('request')
    user_str = f"user={user_id}" if user_id else "anon"

    logger.info(
        f"REQUEST {request.method} {request.path} "
        f"from {request.remote_addr} ({user_str}) "
        f"ua={request.user_agent.string[:50]}"
    )


def log_response(response, request, duration_ms=None, user_id=None):
    """
    Log an HTTP response.

    Args:
        response: Flask response object
        request: Flask request object
        duration_ms: Request processing time in milliseconds
        user_id: ID of authenticated user (if any)
    """
    logger = logging.getLogger('response')
    user_str = f"user={user_id}" if user_id else "anon"
    duration_str = f"{duration_ms:.2f}ms" if duration_ms else ""

    logger.info(
        f"RESPONSE {request.method} {request.path} "
        f"-> {response.status_code} {duration_str} ({user_str})"
    )


# =============================================================================
# ERROR LOGGING
# =============================================================================

def log_error(error, context=None, user_id=None, request=None):
    """
    Log an error with context information.

    Args:
        error: Exception or error object
        context: Additional context dictionary
        user_id: ID of user when error occurred
        request: Flask request object (if available)
    """
    logger = logging.getLogger('error')

    # Build error message
    error_type = type(error).__name__
    error_msg = str(error)

    context_str = f"context={context}" if context else ""
    user_str = f"user={user_id}" if user_id else ""
    request_str = ""

    if request:
        request_str = f"request={request.method} {request.path}"

    logger.error(
        f"ERROR {error_type}: {error_msg} "
        f"{request_str} {user_str} {context_str}",
        exc_info=True  # Include traceback
    )


# =============================================================================
# AUDIT LOGGING
# =============================================================================

def log_audit_action(action: str, entity_type: str = None, entity_id: int = None,
                     user_id: int = None, changes: dict = None,
                     ip_address: str = None, notes: str = None):
    """
    Log an audit action for tracking important events.

    Args:
        action: Action performed (CREATE, UPDATE, DELETE, LOGIN, etc.)
        entity_type: Type of entity affected (e.g., 'user', 'order')
        entity_id: ID of affected entity
        user_id: ID of user performing action
        changes: Dictionary of field changes {field: (old, new)}
        ip_address: Client IP address
        notes: Additional notes
    """
    logger = logging.getLogger('audit')

    changes_str = ""
    if changes:
        changes_str = " changes=" + ",".join([
            f"{k}:{v[0]}->{v[1]}" if isinstance(v, tuple) else f"{k}:{v}"
            for k, v in changes.items()
        ])

    logger.info(
        f"AUDIT {action} "
        f"entity={entity_type}:{entity_id} "
        f"user={user_id} "
        f"ip={ip_address} "
        f"{changes_str} "
        f"notes={notes}"
    )


# =============================================================================
# DECORATORS FOR LOGGING
# =============================================================================

def log_function_call(logger_name: str = None):
    """
    Decorator to log function entry and exit.

    Args:
        logger_name: Name for the logger (defaults to function's module)
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            logger = logging.getLogger(logger_name or f.__module__)
            logger.debug(f"CALL {f.__name__}({args}, {kwargs})")
            try:
                result = f(*args, **kwargs)
                logger.debug(f"RETURN {f.__name__} -> {result}")
                return result
            except Exception as e:
                logger.error(f"EXCEPTION {f.__name__}: {e}")
                raise
        return decorated
    return decorator


def log_api_call(include_request_body: bool = False,
                 include_response_body: bool = False):
    """
    Decorator to log API endpoint calls.

    Args:
        include_request_body: Whether to log request body
        include_response_body: Whether to log response body
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            from flask import request, g
            import time

            logger = logging.getLogger('api')
            start_time = time.time()

            # Log request
            user_id = g.get('user_id')
            log_id = g.get('log_id', id(request))

            logger.info(
                f"API_CALL {request.method} {request.path} "
                f"[{log_id}] user={user_id}"
            )

            try:
                result = f(*args, **kwargs)

                # Log response
                duration_ms = (time.time() - start_time) * 1000
                log_response_info = f"API_RESP {request.path} [{log_id}] {duration_ms:.2f}ms"

                if hasattr(result, 'status_code'):
                    logger.info(f"{log_response_info} -> {result.status_code}")
                else:
                    logger.info(f"{log_response_info} -> OK")

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"API_ERROR {request.path} [{log_id}] "
                    f"{duration_ms:.2f}ms: {type(e).__name__}: {e}"
                )
                raise

        return decorated
    return decorator


# =============================================================================
# DEFAULT LOGGING SETUP
# =============================================================================

def get_default_logger(name: str = None) -> logging.Logger:
    """
    Get a logger with the default configuration.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name or 'whdash')
