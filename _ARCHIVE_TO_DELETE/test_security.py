"""
Security Module Tests
==================
Tests for the Security / SSO / MFA module.
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from security_models import (
    init_security_tables,
    get_user_sessions,
    get_user_mfa_enrollments,
    get_trusted_devices,
    get_security_events,
    get_security_alerts,
    get_sso_providers,
    get_security_policies,
    create_security_event,
    create_security_alert,
    hash_password,
    verify_password,
    generate_session_id,
    generate_recovery_codes,
    row_to_dict,
    rows_to_list
)


class TestSecurityModels:
    """Test security data models and helper functions."""

    def setup_method(self):
        """Setup test database."""
        init_security_tables()

    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123!"
        hash_value, salt = hash_password(password)

        assert hash_value is not None
        assert salt is not None
        assert len(hash_value) > 0
        assert len(salt) > 0

    def test_verify_password(self):
        """Test password verification."""
        password = "TestPassword123!"
        hash_value, salt = hash_password(password)

        assert verify_password(password, hash_value, salt) is True
        assert verify_password("WrongPassword", hash_value, salt) is False

    def test_generate_session_id(self):
        """Test session ID generation."""
        session_id1 = generate_session_id()
        session_id2 = generate_session_id()

        assert session_id1 is not None
        assert len(session_id1) > 20
        assert session_id1 != session_id2

    def test_generate_recovery_codes(self):
        """Test recovery code generation."""
        codes = generate_recovery_codes(10)

        assert len(codes) == 10
        assert all(len(code) == 8 for code in codes)
        assert len(set(codes)) == 10  # All unique

    def test_create_security_event(self):
        """Test security event creation."""
        event_id = create_security_event(
            event_type='test_event',
            event_category='test',
            severity='info',
            actor_user_id=1,
            actor_username='test_user',
            company_id=1,
            source_ip='127.0.0.1',
            user_agent='Test Agent'
        )

        assert event_id is not None
        assert event_id > 0

    def test_create_security_alert(self):
        """Test security alert creation."""
        alert_id = create_security_alert(
            alert_type='test_alert',
            title='Test Alert',
            description='This is a test alert',
            severity='medium',
            company_id=1,
            triggered_by_user_id=1,
            triggered_by_username='test_user'
        )

        assert alert_id is not None
        assert alert_id > 0

    def test_get_sso_providers(self):
        """Test getting SSO providers."""
        providers = get_sso_providers()
        assert isinstance(providers, list)

        providers_enabled = get_sso_providers(enabled_only=True)
        assert isinstance(providers_enabled, list)

    def test_get_security_policies(self):
        """Test getting security policies."""
        policies = get_security_policies()
        assert isinstance(policies, list)

        password_policies = get_security_policies(policy_type='password')
        assert isinstance(password_policies, list)

    def test_row_to_dict(self):
        """Test row to dict conversion."""
        class MockRow:
            def __init__(self):
                self.id = 1
                self.name = 'test'

        row = MockRow()
        result = row_to_dict(row)
        assert result == {'id': 1, 'name': 'test'}

        result = row_to_dict(None)
        assert result is None


class TestSecurityRoutes:
    """Test security routes."""

    def setup_method(self):
        """Setup test environment."""
        init_security_tables()

    def test_security_overview_route(self):
        """Test security overview route exists."""
        from security_routes import security_bp
        assert security_bp is not None
        assert '/security/' in [rule.rule for rule in security_bp.url_map.iter_rules()]

    def test_mfa_routes_exist(self):
        """Test MFA routes exist."""
        from security_routes import security_bp
        rules = [rule.rule for rule in security_bp.url_map.iter_rules()]
        assert '/security/mfa' in rules
        assert '/security/mfa/enroll' in rules
        assert '/security/mfa/disable' in rules
        assert '/security/mfa/recovery-codes' in rules
        assert '/security/mfa/challenge' in rules

    def test_sso_routes_exist(self):
        """Test SSO routes exist."""
        from security_routes import security_bp
        rules = [rule.rule for rule in security_bp.url_map.iter_rules()]
        assert '/security/sso-providers' in rules
        assert '/security/sso-providers/create' in rules

    def test_session_routes_exist(self):
        """Test session routes exist."""
        from security_routes import security_bp
        rules = [rule.rule for rule in security_bp.url_map.iter_rules()]
        assert '/security/sessions' in rules
        assert '/security/trusted-devices' in rules

    def test_events_routes_exist(self):
        """Test events routes exist."""
        from security_routes import security_bp
        rules = [rule.rule for rule in security_bp.url_map.iter_rules()]
        assert '/security/events' in rules

    def test_alerts_routes_exist(self):
        """Test alerts routes exist."""
        from security_routes import security_bp
        rules = [rule.rule for rule in security_bp.url_map.iter_rules()]
        assert '/security/alerts' in rules


class TestSecurityPermissions:
    """Test security permissions integration."""

    def test_security_module_permissions_exist(self):
        """Test that security module has permissions defined."""
        from permissions import MODULE_PERMISSIONS

        assert 'security' in MODULE_PERMISSIONS
        assert 'security.view' in MODULE_PERMISSIONS
        assert 'security.mfa' in MODULE_PERMISSIONS
        assert 'security.sso' in MODULE_PERMISSIONS
        assert 'security.sessions' in MODULE_PERMISSIONS
        assert 'security.policies' in MODULE_PERMISSIONS
        assert 'security.audit' in MODULE_PERMISSIONS
        assert 'security.alerts' in MODULE_PERMISSIONS
        assert 'security.reports' in MODULE_PERMISSIONS


class TestSecurityNavigation:
    """Test security navigation integration."""

    def test_security_menu_exists(self):
        """Test that security menu exists in navigation."""
        from navigation import MENU_STRUCTURE

        assert 'security' in MENU_STRUCTURE
        assert MENU_STRUCTURE['security']['label'] == 'Security'
        assert 'items' in MENU_STRUCTURE['security']

        items = MENU_STRUCTURE['security']['items']
        assert 'security_overview' in items
        assert 'security_mfa' in items
        assert 'security_sessions' in items
        assert 'security_sso_providers' in items
        assert 'security_policies' in items
        assert 'security_events' in items
        assert 'security_alerts' in items
        assert 'security_reports' in items


class TestSecurityTemplates:
    """Test security templates exist."""

    def test_security_templates_exist(self):
        """Test that security templates are created."""
        import os
        templates_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'templates',
            'security'
        )

        assert os.path.exists(templates_dir)

        required_templates = [
            'overview.html',
            'mfa/index.html',
            'mfa/enroll.html',
            'mfa/recovery_codes.html',
            'mfa/challenge.html',
            'sso/providers.html',
            'sso/create.html',
            'sso/edit.html',
            'sessions/index.html',
            'trusted_devices/index.html',
            'policies/index.html',
            'policies/edit.html',
            'events/index.html',
            'events/detail.html',
            'alerts/index.html',
            'access_reviews/index.html',
            'access_reviews/create.html',
            'access_reviews/detail.html',
            'role_conflicts/index.html',
            'emergency_access/index.html',
            'api_security/index.html',
            'reports/index.html',
            'reports/user_access.html',
            'login_history.html',
            'settings/index.html',
            'admin/users.html'
        ]

        for template in required_templates:
            template_path = os.path.join(templates_dir, template)
            assert os.path.exists(template_path), f"Template missing: {template}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
