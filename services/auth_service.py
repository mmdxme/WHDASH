"""
Authentication Service
======================
Centralized authentication and session management service.

This service provides:
- User authentication (login/logout)
- Password hashing and verification
- Session management
- Login rate limiting
- Brute-force protection
"""

import time
import hmac
import secrets
from typing import Optional, Dict, Any, Tuple
from functools import wraps
from flask import request, redirect, url_for, flash, session


class AuthenticationService:
    """
    Centralized authentication service for the platform.
    Provides secure login, logout, and session management.
    """

    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 900  # 15 minutes in seconds
    SESSION_LIFETIME = 120  # minutes

    def __init__(self, get_db_func):
        """
        Initialize the authentication service.

        Args:
            get_db_func: Function that returns a database connection
        """
        self.get_db = get_db_func

    def authenticate_user(self, username: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Authenticate a user with username/email and password.

        Args:
            username: Username or email address
            password: Plain text password

        Returns:
            Tuple of (success, user_data, error_message)
        """
        if not username or not password:
            return False, None, "Please fill in all fields."

        db = self.get_db()
        try:
            user = db.execute(
                "SELECT * FROM users WHERE username = ? OR email = ?",
                (username, username)
            ).fetchone()

            if not user:
                return False, None, "Invalid username or password."

            from werkzeug.security import check_password_hash
            if not check_password_hash(user['password'], password):
                return False, None, "Invalid username or password."

            return True, dict(user), None
        finally:
            db.close()

    def create_session(self, user: Dict[str, Any]) -> bool:
        """
        Create a new session for an authenticated user.

        Args:
            user: User dictionary from database

        Returns:
            True if session created successfully
        """
        from werkzeug.security import check_password_hash

        # Clear any existing session data to prevent session fixation
        session.clear()
        session.permanent = True

        # Store user data in session
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role_id'] = user['role_id']
        session['profile_pic'] = user.get('profile_pic', 'default.png')

        # Get role information
        db = self.get_db()
        try:
            role = db.execute(
                "SELECT role_name, company_id, can_edit_stock, can_manage_users FROM roles WHERE id = ?",
                (user['role_id'],)
            ).fetchone()

            if role:
                session['role_name'] = role['role_name']
                session['company_id'] = role['company_id']
                session['can_edit_stock'] = bool(role['can_edit_stock'])
                session['can_manage_users'] = bool(role['can_manage_users'])

            # Load marketing permissions
            try:
                from marketing_models import get_user_marketing_permissions
                session['marketing_permissions'] = get_user_marketing_permissions(user['id'])
            except Exception:
                session['marketing_permissions'] = []

            # Load Customer Intelligence permissions
            try:
                from customer_intelligence_routes import get_ci_permissions
                session['ci_permissions'] = get_ci_permissions(user['id'])
            except Exception:
                session['ci_permissions'] = []

            return True
        finally:
            db.close()

    def destroy_session(self) -> None:
        """Clear the current session."""
        session.clear()

    def is_authenticated(self) -> bool:
        """Check if current session is authenticated."""
        return 'user_id' in session

    def get_current_user_id(self) -> Optional[int]:
        """Get the current authenticated user ID."""
        return session.get('user_id')

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get the current user data from database."""
        user_id = session.get('user_id')
        if not user_id:
            return None

        db = self.get_db()
        try:
            user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return dict(user) if user else None
        finally:
            db.close()


class LoginRateLimiter:
    """
    Rate limiter for login attempts to prevent brute-force attacks.
    """

    def __init__(self):
        self._attempts = {}
        self._lockouts = {}

    def record_failed_attempt(self, identifier: str) -> int:
        """
        Record a failed login attempt.

        Args:
            identifier: IP address or username

        Returns:
            Number of failed attempts
        """
        current_time = time.time()

        # Clean up old entries
        self._clean_old_attempts(identifier)

        if identifier not in self._attempts:
            self._attempts[identifier] = []

        self._attempts[identifier].append(current_time)
        return len(self._attempts[identifier])

    def record_successful_attempt(self, identifier: str) -> None:
        """Clear failed attempts after successful login."""
        if identifier in self._attempts:
            del self._attempts[identifier]
        if identifier in self._lockouts:
            del self._lockouts[identifier]

    def is_locked_out(self, identifier: str) -> Tuple[bool, int]:
        """
        Check if an identifier is locked out.

        Args:
            identifier: IP address or username

        Returns:
            Tuple of (is_locked, seconds_remaining)
        """
        current_time = time.time()

        if identifier in self._lockouts:
            lockout_until = self._lockouts[identifier]
            if current_time < lockout_until:
                return True, int(lockout_until - current_time)
            else:
                # Lockout expired
                del self._lockouts[identifier]
                if identifier in self._attempts:
                    del self._attempts[identifier]

        return False, 0

    def lock_out(self, identifier: str, duration: int = 900) -> None:
        """
        Lock out an identifier for specified duration.

        Args:
            identifier: IP address or username
            duration: Duration in seconds (default 15 minutes)
        """
        self._lockouts[identifier] = time.time() + duration

    def get_failed_attempts(self, identifier: str) -> int:
        """Get number of failed attempts for identifier."""
        self._clean_old_attempts(identifier)
        return len(self._attempts.get(identifier, []))

    def _clean_old_attempts(self, identifier: str) -> None:
        """Remove attempts older than lockout duration."""
        current_time = time.time()
        if identifier in self._attempts:
            self._attempts[identifier] = [
                t for t in self._attempts[identifier]
                if current_time - t < AuthenticationService.LOCKOUT_DURATION
            ]
            if not self._attempts[identifier]:
                del self._attempts[identifier]


# Global rate limiter instance
_rate_limiter = LoginRateLimiter()


def get_rate_limiter() -> LoginRateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter


# Decorator for routes that require authentication
def require_login(f):
    """
    Decorator that redirects unauthenticated users to login.
    Use this instead of checking session manually in routes.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        allowed_routes = ['login', 'static', 'set_language']
        if request.endpoint not in allowed_routes and 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Admin-only decorator
def require_admin(f):
    """
    Decorator that requires admin privileges.
    Must be used after @require_login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('can_manage_users'):
            flash("Access denied. Admin privileges required.", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# Stock admin decorator
def require_stock_admin(f):
    """
    Decorator that requires stock management privileges.
    Must be used after @require_login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('can_edit_stock'):
            flash("Access denied. Stock management privileges required.", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
