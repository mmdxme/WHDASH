"""
Security Service
================
Centralized security utilities for the platform.

This service provides:
- CSRF token generation and validation
- Security header management
- Input sanitization
- File upload validation
"""

import secrets
import hmac
import re
import os
from typing import Optional, List
from urllib.parse import urlparse, urljoin


class CSRFProtectionService:
    """
    CSRF protection service using token-based validation.
    """

    TOKEN_LENGTH = 32  # 32 bytes = 64 hex characters

    @staticmethod
    def generate_token() -> str:
        """
        Generate a cryptographically secure CSRF token.

        Returns:
            Hex-encoded random token
        """
        return secrets.token_hex(CSRFProtectionService.TOKEN_LENGTH)

    @staticmethod
    def validate_token(expected: str, actual: str) -> bool:
        """
        Validate a CSRF token using constant-time comparison.

        Args:
            expected: The expected token (from session)
            actual: The token from the request

        Returns:
            True if tokens match
        """
        if not expected or not actual:
            return False
        return hmac.compare_digest(expected, actual)


class SecurityHeadersService:
    """
    Service for managing security headers on responses.
    """

    DEFAULT_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
    }

    HSTS_MAX_AGE = 31536000  # 1 year in seconds

    @classmethod
    def get_headers(cls, include_hsts: bool = False) -> dict:
        """
        Get security headers dictionary.

        Args:
            include_hsts: Whether to include HSTS header (for HTTPS)

        Returns:
            Dictionary of security headers
        """
        headers = cls.DEFAULT_HEADERS.copy()
        if include_hsts:
            headers['Strict-Transport-Security'] = f'max-age={cls.HSTS_MAX_AGE}; includeSubDomains'
        return headers


class InputSanitizer:
    """
    Input sanitization utilities for preventing XSS and injection attacks.
    """

    # HTML tags that should be stripped
    DANGEROUS_TAGS = ['script', 'iframe', 'object', 'embed', 'link', 'style']

    # Attribute patterns that can be used for XSS
    DANGEROUS_ATTRS = [
        r'on\w+\s*=',
        r'javascript:',
        r'vbscript:',
        r'data:',
    ]

    @classmethod
    def sanitize_html(cls, value: str) -> str:
        """
        Remove potentially dangerous HTML from a string.

        Args:
            value: Input string that may contain HTML

        Returns:
            Sanitized string safe for display
        """
        if not value:
            return value

        # Convert to string if not already
        value = str(value)

        # Remove dangerous tags
        for tag in cls.DANGEROUS_TAGS:
            value = re.sub(rf'<{tag}[^>]*>.*?</{tag}>', '', value, flags=re.IGNORECASE | re.DOTALL)
            value = re.sub(rf'<{tag}[^>]*/?>', '', value, flags=re.IGNORECASE)

        # Remove dangerous attributes
        for pattern in cls.DANGEROUS_ATTRS:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE)

        return value

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitize a filename to prevent path traversal attacks.

        Args:
            filename: The filename to sanitize

        Returns:
            Sanitized filename safe for file system operations
        """
        if not filename:
            return filename

        # Remove path components
        filename = os.path.basename(filename)

        # Remove null bytes
        filename = filename.replace('\x00', '')

        # Replace potentially dangerous characters
        filename = re.sub(r'[^\w\s\-\.]', '_', filename)

        return filename

    @classmethod
    def validate_safe_redirect(cls, redirect_url: str, allowed_hosts: Optional[List[str]] = None) -> bool:
        """
        Validate that a redirect URL is safe (no open redirect vulnerability).

        Args:
            redirect_url: The redirect URL to validate
            allowed_hosts: List of allowed hosts for redirect

        Returns:
            True if redirect is safe
        """
        if not redirect_url:
            return True

        try:
            parsed = urlparse(redirect_url)

            # Relative URLs are safe
            if not parsed.netloc and not parsed.scheme:
                return True

            # Absolute URLs must be to allowed hosts
            if allowed_hosts:
                return parsed.netloc in allowed_hosts

            # If no allowed hosts specified, reject open redirect
            return False
        except Exception:
            return False


class PasswordValidator:
    """
    Password strength validation.
    """

    @classmethod
    def validate_strength(cls, password: str, min_length: int = 8,
                        require_uppercase: bool = True,
                        require_lowercase: bool = True,
                        require_digit: bool = True,
                        require_special: bool = False) -> tuple:
        """
        Validate password strength.

        Args:
            password: The password to validate
            min_length: Minimum password length
            require_uppercase: Require at least one uppercase letter
            require_lowercase: Require at least one lowercase letter
            require_digit: Require at least one digit
            require_special: Require at least one special character

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        if len(password) < min_length:
            errors.append(f"Password must be at least {min_length} characters")

        if require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")

        if require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")

        if require_digit and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")

        if require_special and not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:\'",.<>?]', password):
            errors.append("Password must contain at least one special character")

        return len(errors) == 0, errors


class FileUploadValidator:
    """
    File upload security validation.
    """

    DEFAULT_ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'csv', 'zip', 'rar'}

    MAX_SIZES = {
        'avatar': 5 * 1024 * 1024,  # 5MB
        'document': 50 * 1024 * 1024,  # 50MB
        'image': 10 * 1024 * 1024,  # 10MB
        'default': 10 * 1024 * 1024,  # 10MB
    }

    @classmethod
    def validate_extension(cls, filename: str, allowed: Optional[set] = None) -> bool:
        """
        Validate that file extension is allowed.

        Args:
            filename: The filename to check
            allowed: Set of allowed extensions (or None for default)

        Returns:
            True if extension is allowed
        """
        if not filename:
            return False

        allowed = allowed or cls.DEFAULT_ALLOWED_EXTENSIONS
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        return ext in allowed

    @classmethod
    def validate_size(cls, content_length: int, file_type: str = 'default') -> bool:
        """
        Validate that file size is within limits.

        Args:
            content_length: Size of file in bytes
            file_type: Type of file ('avatar', 'document', 'image', 'default')

        Returns:
            True if size is acceptable
        """
        max_size = cls.MAX_SIZES.get(file_type, cls.MAX_SIZES['default'])
        return 0 < content_length <= max_size

    @classmethod
    def validate_upload(cls, file, file_type: str = 'default',
                       allowed_extensions: Optional[set] = None) -> tuple:
        """
        Perform all upload validations.

        Args:
            file: The uploaded file object
            file_type: Type of file for size validation
            allowed_extensions: Set of allowed extensions

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file:
            return False, "No file provided"

        if file.filename == '':
            return False, "No file selected"

        if not cls.validate_extension(file.filename, allowed_extensions):
            return False, "File type not allowed"

        content_length = request.content_length if hasattr(file, 'content_length') else 0
        if content_length and not cls.validate_size(content_length, file_type):
            max_size = cls.MAX_SIZES.get(file_type, cls.MAX_SIZES['default'])
            max_mb = max_size / (1024 * 1024)
            return False, f"File size exceeds maximum allowed ({max_mb}MB)"

        return True, None
