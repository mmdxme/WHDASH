"""
Services Package
================
Centralized service layer for business logic and security.

Services:
- auth_service: Authentication and session management
- security_service: CSRF, headers, input validation
- logging_service: Centralized logging configuration
"""

from .auth_service import (
    AuthenticationService,
    LoginRateLimiter,
    get_rate_limiter,
    require_login,
    require_admin,
    require_stock_admin,
)

from .security_service import (
    CSRFProtectionService,
    SecurityHeadersService,
    InputSanitizer,
    PasswordValidator,
    FileUploadValidator,
)

from .logging_service import (
    setup_logging,
    log_request,
    log_response,
    log_error,
    log_audit_action,
    log_function_call,
    log_api_call,
    get_default_logger,
)

__all__ = [
    # Auth service
    'AuthenticationService',
    'LoginRateLimiter',
    'get_rate_limiter',
    'require_login',
    'require_admin',
    'require_stock_admin',
    # Security service
    'CSRFProtectionService',
    'SecurityHeadersService',
    'InputSanitizer',
    'PasswordValidator',
    'FileUploadValidator',
    # Logging service
    'setup_logging',
    'log_request',
    'log_response',
    'log_error',
    'log_audit_action',
    'log_function_call',
    'log_api_call',
    'get_default_logger',
]
