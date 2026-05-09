"""
Security Module Sample Data Seeder
================================
Seeds the security module with demo data for testing and demonstration.
"""

import sqlite3
import secrets
import hashlib
import base64
import random
import os
from datetime import datetime, timedelta

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'warehouse.db')


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def get_table_columns(cursor, table_name):
    """Get column names for a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def hash_password(password: str) -> tuple:
    """Hash password with SHA-256 + salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return base64.b64encode(key).decode(), salt


def generate_session_id() -> str:
    """Generate secure session ID."""
    return secrets.token_urlsafe(48)


def seed_security_data():
    """Seed all security module data."""
    conn = get_db()
    cursor = conn.cursor()

    print("Seeding security module data...")

    # Get existing users
    cursor.execute("SELECT id, username FROM users LIMIT 10")
    users = cursor.fetchall()

    # =====================================================================
    # SSO Providers
    # =====================================================================
    print("  - Creating SSO providers...")

    # Check if table has the expected columns
    sso_cols = get_table_columns(cursor, 'sso_providers')

    if 'provider_code' in sso_cols:
        sso_providers = [
            {
                'provider_code': 'azure_ad',
                'provider_name': 'Microsoft Entra ID',
                'provider_type': 'oidc',
                'client_id': 'demo-azure-client-id',
                'client_secret': 'demo-azure-secret',
                'discovery_url': 'https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration',
                'scopes': 'openid profile email',
                'is_enabled': 1,
                'is_visible': 1,
                'is_default': 1,
            },
            {
                'provider_code': 'google_workspace',
                'provider_name': 'Google Workspace',
                'provider_type': 'oidc',
                'client_id': 'demo-google-client-id',
                'client_secret': 'demo-google-secret',
                'discovery_url': 'https://accounts.google.com/.well-known/openid-configuration',
                'scopes': 'openid profile email',
                'is_enabled': 1,
                'is_visible': 1,
                'is_default': 0,
            },
            {
                'provider_code': 'okta',
                'provider_name': 'Okta',
                'provider_type': 'oidc',
                'client_id': 'demo-okta-client-id',
                'client_secret': 'demo-okta-secret',
                'discovery_url': 'https://demo.okta.com/.well-known/openid-configuration',
                'scopes': 'openid profile email groups',
                'is_enabled': 0,
                'is_visible': 1,
                'is_default': 0,
            }
        ]

        for provider in sso_providers:
            # Check if already exists
            cursor.execute("SELECT id FROM sso_providers WHERE provider_code = ?", (provider['provider_code'],))
            if cursor.fetchone():
                continue

            cols = ', '.join([k for k in provider.keys() if k in sso_cols])
            placeholders = ', '.join(['?'] * len([k for k in provider.keys() if k in sso_cols]))
            vals = [v for k, v in provider.items() if k in sso_cols]
            cursor.execute(f"""
                INSERT INTO sso_providers ({cols}) VALUES ({placeholders})
            """, vals)

    # =====================================================================
    # MFA Methods
    # =====================================================================
    print("  - Creating MFA methods...")

    mfa_cols = get_table_columns(cursor, 'mfa_methods')

    if 'method_code' in mfa_cols:
        mfa_methods = [
            {'method_code': 'totp', 'method_name': 'Authenticator App', 'description': 'Use an authenticator app like Google Authenticator or Authy.', 'icon': 'fa-mobile-alt', 'is_enabled': 1, 'priority': 100},
            {'method_code': 'email_otp', 'method_name': 'Email OTP', 'description': 'Receive a one-time code via email.', 'icon': 'fa-envelope', 'is_enabled': 1, 'priority': 90},
            {'method_code': 'sms_otp', 'method_name': 'SMS OTP', 'description': 'Receive a one-time code via SMS.', 'icon': 'fa-comment', 'is_enabled': 0, 'priority': 80},
            {'method_code': 'push', 'method_name': 'Push Notification', 'description': 'Receive a push notification for approval.', 'icon': 'fa-bell', 'is_enabled': 0, 'priority': 70}
        ]

        for method in mfa_methods:
            cursor.execute("SELECT id FROM mfa_methods WHERE method_code = ?", (method['method_code'],))
            if cursor.fetchone():
                continue
            cols = ', '.join([k for k in method.keys() if k in mfa_cols])
            placeholders = ', '.join(['?'] * len([k for k in method.keys() if k in mfa_cols]))
            vals = [v for k, v in method.items() if k in mfa_cols]
            cursor.execute(f"INSERT INTO mfa_methods ({cols}) VALUES ({placeholders})", vals)

    # =====================================================================
    # Security Policies
    # =====================================================================
    print("  - Creating security policies...")

    policy_cols = get_table_columns(cursor, 'security_policies')

    if 'policy_code' in policy_cols or 'policy_type' in policy_cols:
        policies = [
            {'policy_type': 'password', 'policy_name': 'Default Password Policy', 'description': 'Standard password requirements', 'rules': '{"min_length": 8, "require_uppercase": true, "require_numbers": true}', 'is_enabled': 1, 'is_system': 1, 'priority': 100},
            {'policy_type': 'session', 'policy_name': 'Default Session Policy', 'description': 'Standard session settings', 'rules': '{"idle_timeout_minutes": 120, "max_lifetime_hours": 8}', 'is_enabled': 1, 'is_system': 1, 'priority': 100},
            {'policy_type': 'mfa', 'policy_name': 'MFA Policy', 'description': 'MFA requirements', 'rules': '{"required_for_admins": true}', 'is_enabled': 1, 'is_system': 1, 'priority': 100},
            {'policy_type': 'lockout', 'policy_name': 'Account Lockout Policy', 'description': 'Failed login lockout', 'rules': '{"max_attempts": 5, "lockout_duration_minutes": 15}', 'is_enabled': 1, 'is_system': 1, 'priority': 100}
        ]

        for policy in policies:
            name = policy.get('policy_name', policy.get('policy_code', ''))
            cursor.execute("SELECT id FROM security_policies WHERE policy_name = ?", (name,))
            if cursor.fetchone():
                continue
            cols = ', '.join([k for k in policy.keys() if k in policy_cols])
            placeholders = ', '.join(['?'] * len([k for k in policy.keys() if k in policy_cols]))
            vals = [v for k, v in policy.items() if k in policy_cols]
            if cols:
                cursor.execute(f"INSERT INTO security_policies ({cols}) VALUES ({placeholders})", vals)

    # =====================================================================
    # User MFA Enrollments (for existing demo users)
    # =====================================================================
    print("  - Creating MFA enrollments...")

    mfa_enroll_cols = get_table_columns(cursor, 'user_mfa_enrollments')

    if 'user_id' in mfa_enroll_cols and 'method_code' in mfa_enroll_cols:
        for user in users[:5]:  # First 5 users
            if random.random() > 0.3:  # 70% have MFA
                cursor.execute("SELECT id FROM user_mfa_enrollments WHERE user_id = ?", (user['id'],))
                if cursor.fetchone():
                    continue

                secret = secrets.token_hex(20)
                cols = 'user_id, method_code, method_name, is_primary, is_enabled, name, identifier, TOTP_secret, TOTP_issuer, enrolled_at, verified_at, used_count'
                placeholders = '?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?'
                vals = (user['id'], 'totp', 'Authenticator App', 1, 1, 'Authenticator App', f'app_{user["username"]}', secret, 'MMDx Enterprise', datetime.now().isoformat(), datetime.now().isoformat(), random.randint(5, 50))

                # Only insert if columns match
                existing_cols = get_table_columns(cursor, 'user_mfa_enrollments')
                if all(c in existing_cols for c in ['user_id', 'method_code', 'TOTP_secret']):
                    try:
                        cursor.execute(f"INSERT INTO user_mfa_enrollments ({cols}) VALUES ({placeholders})", vals)
                    except:
                        pass

                # Generate recovery codes
                for j in range(10):
                    code = secrets.token_hex(4).upper()
                    code_hash = hashlib.sha256(code.encode()).hexdigest()
                    try:
                        cursor.execute("""
                            INSERT INTO recovery_codes (user_id, code_hash, code_index, is_used, created_at)
                            VALUES (?, ?, ?, 0, datetime('now'))
                        """, (user['id'], code_hash, j + 1))
                    except:
                        pass

    # =====================================================================
    # Trusted Devices
    # =====================================================================
    print("  - Creating trusted devices...")

    device_cols = get_table_columns(cursor, 'trusted_devices')

    if 'user_id' in device_cols and 'device_id' in device_cols:
        for user in users[:3]:
            cursor.execute("SELECT id FROM trusted_devices WHERE user_id = ? LIMIT 1", (user['id'],))
            if cursor.fetchone():
                continue

            device_id = secrets.token_hex(12)
            cols = 'user_id, device_id, device_name, device_type, browser, browser_version, os, os_version, ip_address, last_ip, user_agent, trusted_from, last_used_at, is_current, is_active, company_id'
            placeholders = '?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?'
            vals = (user['id'], device_id, 'Work Laptop', 'desktop', 'Chrome', '120.0', 'Windows', '11', f'192.168.1.{100 + user["id"]}', f'192.168.1.{100 + user["id"]}', 'Mozilla/5.0 Chrome/120.0', datetime.now().isoformat(), datetime.now().isoformat(), 1, 1, 1)

            existing_cols = get_table_columns(cursor, 'trusted_devices')
            if all(c in existing_cols for c in ['user_id', 'device_id']):
                try:
                    cursor.execute(f"INSERT INTO trusted_devices ({cols}) VALUES ({placeholders})", vals)
                except:
                    pass

    # =====================================================================
    # User Sessions - Handle different schemas
    # =====================================================================
    print("  - Creating user sessions...")

    session_cols = get_table_columns(cursor, 'user_sessions')

    if 'session_token' in session_cols:
        # Old schema with session_token
        for user in users:
            for j in range(random.randint(1, 2)):
                session_token = generate_session_id()
                try:
                    cursor.execute("""
                        INSERT INTO user_sessions (user_id, session_token, ip_address, user_agent, device_info, is_current, is_active, last_activity, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        user['id'], session_token, f'192.168.1.{random.randint(100, 200)}',
                        'Mozilla/5.0 Chrome/120.0', 'desktop',
                        1 if j == 0 else 0, 1,
                        datetime.now().isoformat(), datetime.now().isoformat()
                    ))
                except:
                    pass
    elif 'session_id' in session_cols:
        # New schema with session_id
        for user in users:
            for j in range(random.randint(1, 2)):
                session_id = generate_session_id()
                try:
                    cursor.execute("""
                        INSERT INTO user_sessions (user_id, username, session_id, ip_address, user_agent, browser, browser_version, os, os_version, device_type, login_method, mfa_verified, session_started, last_activity, is_active, is_suspicious, risk_score, company_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        user['id'], user['username'], session_id,
                        f'192.168.1.{random.randint(100, 200)}',
                        'Mozilla/5.0 Chrome/120.0', 'Chrome', '120.0', 'Windows', '11', 'desktop',
                        random.choice(['password', 'sso']),
                        1 if random.random() > 0.3 else 0,
                        datetime.now().isoformat(), datetime.now().isoformat(),
                        1, 0, random.randint(0, 20), 1
                    ))
                except:
                    pass

    # =====================================================================
    # Security Events
    # =====================================================================
    print("  - Creating security events...")

    event_cols = get_table_columns(cursor, 'security_events')

    if 'event_type' in event_cols:
        event_types = [
            ('login_success', 'authentication', 'info'),
            ('login_failure', 'authentication', 'warning'),
            ('mfa_enrolled', 'authentication', 'info'),
            ('mfa_challenge_success', 'authentication', 'info'),
            ('password_changed', 'authentication', 'info'),
            ('session_revoked', 'session', 'info'),
            ('trusted_device_added', 'authentication', 'info'),
        ]

        for _ in range(50):
            event_type, category, severity = random.choice(event_types)
            user = random.choice(users) if users else None

            try:
                cursor.execute("""
                    INSERT INTO security_events (
                        event_type, event_category, severity, timestamp,
                        actor_user_id, actor_username, target_user_id, target_username,
                        source_ip, user_agent, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event_type, category, severity,
                    (datetime.now() - timedelta(hours=random.randint(1, 168))).isoformat(),
                    user['id'] if user else 1, user['username'] if user else 'admin',
                    user['id'] if user else 1, user['username'] if user else 'admin',
                    f'192.168.1.{random.randint(100, 200)}',
                    'Mozilla/5.0 Chrome/120.0',
                    'success' if 'success' in event_type or 'enrolled' in event_type or 'changed' in event_type else 'failure'
                ))
            except:
                pass

    # =====================================================================
    # Security Alerts
    # =====================================================================
    print("  - Creating security alerts...")

    alert_cols = get_table_columns(cursor, 'security_alerts')

    if 'alert_type' in alert_cols:
        alert_types = [
            ('suspicious_login', 'Suspicious Login Detected', 'A login from an unusual location was detected.', 'medium'),
            ('mass_lockout', 'Mass Account Lockout', 'Multiple account lockouts detected.', 'high'),
            ('mfa_disabled', 'MFA Disabled', 'User has disabled MFA.', 'high'),
            ('admin_outside_hours', 'Admin Login Outside Office Hours', 'Admin logged in outside normal hours.', 'low'),
            ('multiple_failed', 'Multiple Failed Login Attempts', 'User has failed multiple login attempts.', 'medium'),
        ]

        for _ in range(10):
            alert_type, title, desc, severity = random.choice(alert_types)
            user = random.choice(users) if users else None
            status = random.choice(['new', 'acknowledged', 'resolved'])

            try:
                cursor.execute("""
                    INSERT INTO security_alerts (
                        alert_type, title, description, severity, status,
                        triggered_by_user_id, triggered_by_username, source_ip,
                        triggered_at, acknowledged_at, resolved_at, company_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert_type, title, desc, severity, status,
                    user['id'] if user else 1, user['username'] if user else 'admin',
                    f'192.168.1.{random.randint(100, 200)}',
                    (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
                    datetime.now().isoformat() if status != 'new' else '',
                    datetime.now().isoformat() if status == 'resolved' else '',
                    1
                ))
            except:
                pass

    # =====================================================================
    # Login Attempts
    # =====================================================================
    print("  - Creating login attempts...")

    login_cols = get_table_columns(cursor, 'login_attempts')

    if 'user_id' in login_cols:
        for _ in range(100):
            user = random.choice(users) if users else None
            success = random.random() > 0.15

            try:
                cursor.execute("""
                    INSERT INTO login_attempts (
                        user_id, username, email, source_ip, user_agent,
                        login_method, mfa_passed, success, failure_reason,
                        country, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user['id'] if user else 1,
                    user['username'] if user else 'admin',
                    f'{user["username"] if user else "admin"}@example.com',
                    f'192.168.1.{random.randint(100, 200)}',
                    'Mozilla/5.0 Chrome/120.0',
                    random.choice(['password', 'sso', 'mfa']),
                    1 if success else 0,
                    1 if success else 0,
                    '' if success else random.choice(['Invalid password', 'Invalid MFA code', 'Account locked']),
                    random.choice(['United States', 'United Kingdom', 'Germany', 'Iran', 'China', 'Russia']),
                    (datetime.now() - timedelta(hours=random.randint(1, 336))).isoformat()
                ))
            except:
                pass

    # =====================================================================
    # Access Review Campaigns
    # =====================================================================
    print("  - Creating access review campaigns...")

    campaign_cols = get_table_columns(cursor, 'access_review_campaigns')

    if 'campaign_name' in campaign_cols:
        campaigns = [
            {'campaign_name': 'Q2 2026 Access Review', 'campaign_type': 'periodic', 'review_frequency': 'quarterly', 'description': 'Quarterly access review', 'status': 'active', 'start_date': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'), 'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')},
            {'campaign_name': 'Admin Access Review - March 2026', 'campaign_type': 'periodic', 'review_frequency': 'monthly', 'description': 'Monthly admin review', 'status': 'in_progress', 'start_date': (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d'), 'due_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}
        ]

        for campaign in campaigns:
            cursor.execute("SELECT id FROM access_review_campaigns WHERE campaign_name = ?", (campaign['campaign_name'],))
            if cursor.fetchone():
                continue

            try:
                cursor.execute("""
                    INSERT INTO access_review_campaigns (
                        campaign_name, campaign_type, review_frequency, description,
                        owner_user_id, owner_username, start_date, due_date, status,
                        include_mfa_status, include_sso_status, include_permissions,
                        include_role_conflicts, include_inactive_users, created_by, company_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    campaign['campaign_name'], campaign['campaign_type'], campaign['review_frequency'],
                    campaign['description'], 1, 'admin',
                    campaign['start_date'], campaign['due_date'], campaign['status'],
                    1, 1, 1, 1, 1, 1, 1
                ))
            except:
                pass

    # =====================================================================
    # Role Conflict Rules
    # =====================================================================
    print("  - Creating role conflict rules...")

    conflict_cols = get_table_columns(cursor, 'role_conflict_rules')

    if 'rule_name' in conflict_cols:
        conflict_rules = [
            {'rule_name': 'Finance - No Dual Access', 'rule_description': 'Users cannot have both AP Clerk and AR Clerk roles', 'conflict_type': 'mutual_exclusion', 'severity': 'warning', 'enforcement_mode': 'warning'},
            {'rule_name': 'Admin Separation', 'rule_description': 'System admin cannot have data entry roles', 'conflict_type': 'mutual_exclusion', 'severity': 'error', 'enforcement_mode': 'soft_block'}
        ]

        for rule in conflict_rules:
            cursor.execute("SELECT id FROM role_conflict_rules WHERE rule_name = ?", (rule['rule_name'],))
            if cursor.fetchone():
                continue

            try:
                cursor.execute("""
                    INSERT INTO role_conflict_rules (
                        rule_name, rule_description, conflict_type,
                        severity, enforcement_mode, is_active, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    rule['rule_name'], rule['rule_description'], rule['conflict_type'],
                    rule['severity'], rule['enforcement_mode'], 1, 1
                ))
            except:
                pass

    # =====================================================================
    # Emergency Access Accounts
    # =====================================================================
    print("  - Creating emergency access accounts...")

    emg_cols = get_table_columns(cursor, 'emergency_access_accounts')

    if 'username' in emg_cols:
        cursor.execute("SELECT id FROM emergency_access_accounts WHERE username = ?", ('emergency_admin',))
        if not cursor.fetchone():
            try:
                cursor.execute("""
                    INSERT INTO emergency_access_accounts (
                        user_id, username, display_name, email, phone,
                        emergency_role_id, emergency_role_name, is_active,
                        max_duration_hours, reason, approver_user_id, approver_username,
                        approved_at, notify_security_on_use, notify_manager_on_use, company_id, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    1, 'emergency_admin', 'Emergency Admin Account', 'emergency_admin@example.com',
                    '+1-555-0100', 10, 'Break-Glass Admin', 1,
                    4, 'Emergency access for critical incidents',
                    1, 'system', datetime.now().isoformat(), 1, 1, 1, 1
                ))
            except:
                pass

    conn.commit()
    conn.close()

    print("Security module data seeded successfully!")


if __name__ == '__main__':
    seed_security_data()
