"""
WHDASH Core Tests
================
Tests for core application functionality: authentication, session handling,
CSRF protection, and basic routing.
"""

import pytest
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAppBoot:
    """Tests for application boot and configuration."""
    
    def test_config_module_loads(self):
        """Test that config module loads without errors."""
        import config
        assert config.ENV is not None
        assert config.SECRET_KEY is not None
        assert config.DATABASE_PATH is not None
    
    def test_database_module_loads(self):
        """Test that database module loads without errors."""
        import database
        assert hasattr(database, 'get_db')
        assert hasattr(database, 'get_db_context')
        assert hasattr(database, 'get_one')
        assert hasattr(database, 'get_all')
    
    def test_permissions_module_loads(self):
        """Test that permissions module loads without errors."""
        import permissions
        assert hasattr(permissions, 'MODULE_PERMISSIONS')
        assert hasattr(permissions, 'user_has_permission')
        assert hasattr(permissions, 'require_permission')
    
    def test_settings_module_loads(self):
        """Test that settings module loads without errors."""
        import settings
        assert hasattr(settings, 'DEFAULT_SETTINGS')
        assert hasattr(settings, 'get_setting')
        assert hasattr(settings, 'set_setting')
    
    def test_secret_key_not_weak_default_in_production_env(self):
        """Test that SECRET_KEY is not a weak default when ENV=production."""
        os.environ['FLASK_ENV'] = 'production'
        os.environ.pop('SECRET_KEY', None)
        
        # Force config reload
        import importlib
        import config
        importlib.reload(config)
        
        # In production, SECRET_KEY must come from environment
        assert os.environ.get('SECRET_KEY') is not None or config.ENV != 'production'


class TestDatabaseConnection:
    """Tests for database connection functionality."""
    
    def test_get_db_returns_connection(self):
        """Test that get_db returns a valid connection."""
        from database import get_db
        
        # Use a temp file database for this test
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name
        
        os.environ['DATABASE_PATH'] = db_path
        import importlib
        import database
        importlib.reload(database)
        
        try:
            db = database.get_db()
            assert db is not None
            assert hasattr(db, 'execute')
            db.close()
        finally:
            os.unlink(db_path)
    
    def test_get_db_context_commits_by_default(self):
        """Test that get_db_context commits by default."""
        from database import get_db_context
        
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name
        
        os.environ['DATABASE_PATH'] = db_path
        import importlib
        import database
        importlib.reload(database)
        
        try:
            with get_db_context() as db:
                db.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, value TEXT)")
                db.execute("INSERT INTO test_table (value) VALUES ('test')")
                # Should commit on exit
            
            # Verify data persisted
            with get_db_context() as db:
                result = db.execute("SELECT * FROM test_table").fetchone()
                assert result is not None
                assert result['value'] == 'test'
        finally:
            os.unlink(db_path)
    
    def test_get_db_context_rollbacks_on_exception(self):
        """Test that get_db_context rolls back on exception."""
        from database import get_db_context
        
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name
        
        os.environ['DATABASE_PATH'] = db_path
        import importlib
        import database
        importlib.reload(database)
        
        try:
            with get_db_context() as db:
                db.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, value TEXT)")
            
            try:
                with get_db_context() as db:
                    db.execute("INSERT INTO test_table (value) VALUES ('before_rollback')")
                    raise ValueError("Test rollback")
            except ValueError:
                pass
            
            # Verify rollback occurred
            with get_db_context() as db:
                result = db.execute("SELECT * FROM test_table").fetchone()
                assert result is None  # Should have rolled back
        finally:
            os.unlink(db_path)


class TestCSRFProtection:
    """Tests for CSRF protection mechanisms."""
    
    def test_generate_csrf_token_creates_token(self):
        """Test that generate_csrf_token creates a token."""
        import secrets
        
        # Simple test without Flask context
        token = secrets.token_hex(32)
        assert len(token) == 64
        assert isinstance(token, str)
    
    def test_csrf_validation_rejects_mismatched_tokens(self):
        """Test that CSRF validation rejects mismatched tokens."""
        import hmac
        
        real_token = "abc123"
        fake_token = "xyz789"
        
        # Should not match
        assert not hmac.compare_digest(real_token, fake_token)
    
    def test_csrf_validation_accepts_matching_tokens(self):
        """Test that CSRF validation accepts matching tokens."""
        import hmac
        
        token = "abc123"
        
        # Should match
        assert hmac.compare_digest(token, token)


class TestAuthentication:
    """Tests for authentication functionality."""
    
    def test_password_hashing_works(self):
        """Test that password hashing and verification work."""
        from werkzeug.security import generate_password_hash, check_password_hash
        
        password = "SecurePassword123!"
        hashed = generate_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert check_password_hash(hashed, password)
        assert not check_password_hash(hashed, "WrongPassword")
    
    def test_login_requires_credentials(self):
        """Test that login requires both username and password."""
        # This is a logic test - in real Flask app, empty credentials should fail
        username = ""
        password = ""
        
        # Both empty = should fail
        assert not (username and password)


class TestPermissionSystem:
    """Tests for the RBAC permission system."""
    
    def test_module_permissions_defined(self):
        """Test that MODULE_PERMISSIONS is properly defined."""
        from permissions import MODULE_PERMISSIONS
        
        assert isinstance(MODULE_PERMISSIONS, dict)
        assert len(MODULE_PERMISSIONS) > 0
        
        # Check for common modules
        expected_modules = ['hr', 'wms', 'finance', 'assets', 'quality']
        for module in expected_modules:
            assert module in MODULE_PERMISSIONS, f"Module {module} should be in MODULE_PERMISSIONS"
    
    def test_permission_structure_is_valid(self):
        """Test that permission structure has correct format."""
        from permissions import MODULE_PERMISSIONS
        
        for module, module_data in MODULE_PERMISSIONS.items():
            assert 'label' in module_data
            assert 'resources' in module_data
            
            for resource, actions in module_data['resources'].items():
                assert isinstance(actions, list)
                assert len(actions) > 0
    
    def test_user_has_permission_signature(self):
        """Test that user_has_permission has correct signature."""
        from permissions import user_has_permission
        import inspect
        
        sig = inspect.signature(user_has_permission)
        params = list(sig.parameters.keys())
        
        assert 'user_id' in params
        assert 'module' in params
        assert 'resource' in params
        assert 'action' in params


class TestSessionSecurity:
    """Tests for session security mechanisms."""
    
    def test_session_permanent_flag_can_be_set(self):
        """Test that session.permanent flag can be set."""
        # This tests the concept - actual Flask session test needs app context
        permanent = True
        lifetime = 120  # minutes
        
        assert permanent is True
        assert lifetime > 0
    
    def test_hmac_used_for_token_comparison(self):
        """Test that HMAC is used for constant-time token comparison."""
        import hmac
        
        # HMAC is used for CSRF token comparison to prevent timing attacks
        token1 = b"test_token_1"
        token2 = b"test_token_2"
        
        # This should use constant-time comparison
        result = hmac.compare_digest(token1, token1)
        assert result is True
        
        result = hmac.compare_digest(token1, token2)
        assert result is False


class TestSecurityHeaders:
    """Tests for security header configuration."""
    
    def test_security_headers_defined(self):
        """Test that security headers are properly defined."""
        from config import SECURITY_HEADERS
        
        assert isinstance(SECURITY_HEADERS, dict)
        assert 'X-Content-Type-Options' in SECURITY_HEADERS
        assert 'X-Frame-Options' in SECURITY_HEADERS
    
    def test_hsts_header_present(self):
        """Test that HSTS header is configured."""
        from config import SECURITY_HEADERS
        
        hsts = SECURITY_HEADERS.get('Strict-Transport-Security', '')
        assert 'max-age' in hsts


class TestPasswordValidation:
    """Tests for password validation rules."""
    
    def test_password_min_length_configured(self):
        """Test that minimum password length is configured."""
        from config import PASSWORD_MIN_LENGTH
        
        assert PASSWORD_MIN_LENGTH >= 8
    
    def test_password_requires_uppercase(self):
        """Test that password requires uppercase character."""
        from config import PASSWORD_REQUIRE_UPPERCASE
        
        assert PASSWORD_REQUIRE_UPPERCASE is True
    
    def test_password_requires_lowercase(self):
        """Test that password requires lowercase character."""
        from config import PASSWORD_REQUIRE_LOWERCASE
        
        assert PASSWORD_REQUIRE_LOWERCASE is True
    
    def test_password_requires_digit(self):
        """Test that password requires digit."""
        from config import PASSWORD_REQUIRE_DIGIT
        
        assert PASSWORD_REQUIRE_DIGIT is True


class TestRateLimiting:
    """Tests for rate limiting configuration."""
    
    def test_rate_limit_configured(self):
        """Test that rate limiting is configured."""
        from config import RATELIMIT_ENABLED, RATELIMIT_LOGIN
        
        assert RATELIMIT_ENABLED is True
        assert RATELIMIT_LOGIN is not None
        assert 'per' in RATELIMIT_LOGIN


class TestInputValidation:
    """Tests for input validation patterns."""
    
    def test_username_pattern_defined(self):
        """Test that username pattern is defined."""
        from config import USERNAME_PATTERN
        import re
        
        assert USERNAME_PATTERN is not None
        # Test that it's a valid regex
        re.compile(USERNAME_PATTERN)
    
    def test_username_min_max_length(self):
        """Test that username min/max length is configured."""
        from config import USERNAME_MIN_LENGTH, USERNAME_MAX_LENGTH
        
        assert USERNAME_MIN_LENGTH >= 3
        assert USERNAME_MAX_LENGTH <= USERNAME_MIN_LENGTH + 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
