"""
Security Module Data Models
==========================
Enterprise-grade security models for the MMDx platform covering:
- SSO Providers (OIDC, SAML, Azure AD, Google Workspace)
- MFA Enrollments (TOTP, Email OTP, Recovery Codes)
- Trusted Devices
- User Sessions
- Security Events & Audit Trail
- Security Alerts & Incidents
- Access Reviews & Governance
- Role Conflict Rules
- Emergency Access / Break-glass
- API Security Events
- Security Policies (Password, Session, MFA, etc.)
"""

import sqlite3
import os
import secrets
import hashlib
import base64
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else ''
DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'warehouse.db'))


def get_db():
    """Get database connection with Row factory."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    for pragma in [
        "PRAGMA journal_mode=WAL",
        "PRAGMA foreign_keys=ON",
        "PRAGMA busy_timeout=5000",
    ]:
        conn.execute(pragma)
    return conn


@contextmanager
def get_db_context():
    """Context manager for database operations with automatic commit/rollback."""
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row) -> Dict:
    """Convert sqlite3.Row to dict."""
    return dict(row) if row else None


def rows_to_list(rows: List[sqlite3.Row]) -> List[Dict]:
    """Convert list of sqlite3.Row to list of dicts."""
    return [dict(row) for row in rows] if rows else []


# =============================================================================
# SSO PROVIDER MODELS
# =============================================================================

@dataclass
class SSOProvider:
    """SSO Identity Provider configuration."""
    id: int = 0
    provider_code: str = ""  # azure_ad, google_workspace, okta, generic_oidc, saml
    provider_name: str = ""
    provider_type: str = ""  # oidc, saml
    client_id: str = ""
    client_secret: str = ""  # encrypted
    discovery_url: str = ""  # OIDC discovery endpoint
    issuer: str = ""  # OIDC issuer
    authorization_endpoint: str = ""
    token_endpoint: str = ""
    userinfo_endpoint: str = ""
    jwks_uri: str = ""
    logout_endpoint: str = ""
    sign_cert: str = ""  # SAML sign certificate
    sign_key: str = ""  # SAML sign private key
    enc_cert: str = ""  # SAML encryption certificate
    scopes: str = "openid profile email"  # OIDC scopes
    claim_mappings: str = ""  # JSON: {"username": "preferred_username", "email": "email", ...}
    role_mappings: str = ""  # JSON: {"group_name": ["role_permission_tuple"], ...}
    auto_link_policy: str = "email"  # email, username, disabled
    default_role_id: int = 0
    default_company_id: int = 0
    default_branch_id: int = 0
    default_department_id: int = 0
    domain_hint: str = ""  # Email domain for routing
    icon_url: str = ""
    button_style: str = "full"  # full, rounded, icon
    is_enabled: bool = False
    is_visible: bool = True
    is_default: bool = False
    force_authn: bool = False  # SAML force auth
    want_assertions_signed: bool = True  # SAML
    jit_provisioning_enabled: bool = False
    session_duration: int = 480  # minutes
    allowed_company_ids: str = ""  # comma-separated company IDs, empty = all
    ip_whitelist: str = ""  # comma-separated IPs
    created_at: str = ""
    created_by: int = 0
    updated_at: str = ""
    updated_by: int = 0
    notes: str = ""
    last_test_at: str = ""
    last_test_result: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    def get_claim_mappings(self) -> Dict:
        import json
        try:
            return json.loads(self.claim_mappings) if self.claim_mappings else {}
        except:
            return {}

    def get_role_mappings(self) -> Dict:
        import json
        try:
            return json.loads(self.role_mappings) if self.role_mappings else {}
        except:
            return {}


@dataclass
class SSOProviderCertificate:
    """Certificate storage for SSO providers."""
    id: int = 0
    provider_id: int = 0
    cert_type: str = ""  # sign, encryption, tls
    cert_content: str = ""  # PEM content
    key_content: str = ""  # PEM private key (encrypted storage)
    serial_number: str = ""
    subject_cn: str = ""
    issuer_cn: str = ""
    valid_from: str = ""
    valid_to: str = ""
    fingerprint_sha256: str = ""
    is_active: bool = True
    created_at: str = ""
    created_by: int = 0


@dataclass
class SSOAuditLog:
    """SSO authentication audit trail."""
    id: int = 0
    provider_id: int = 0
    provider_code: str = ""
    event_type: str = ""  # login_success, login_failure, link_success, link_failure, logout
    subject_user: str = ""  # IdP subject
    email: str = ""
    username: str = ""
    display_name: str = ""
    mapped_user_id: int = 0
    mapped_username: str = ""
    idp_session_id: str = ""
    sp_session_id: str = ""
    source_ip: str = ""
    user_agent: str = ""
    auth_method: str = ""  # authorization_code, implicit, saml, etc.
    requested_scopes: str = ""
    granted_roles: str = ""
    failure_reason: str = ""
    event_timestamp: str = ""
    correlation_id: str = ""


# =============================================================================
# MFA MODELS
# =============================================================================

@dataclass
class MFAMethod:
    """Available MFA methods configuration."""
    id: int = 0
    method_code: str = ""  # totp, email_otp, sms_otp, push, passkey
    method_name: str = ""
    description: str = ""
    icon: str = "fa-mobile-alt"
    instructions: str = ""
    config_schema: str = ""  # JSON schema for provider config
    is_enabled: bool = True
    is_builtin: bool = True
    priority: int = 100
    setup_timeout_minutes: int = 10
    otp_length: int = 6
    otp_expiry_seconds: int = 300
    max_attempts: int = 3
    requiresecure_channel: bool = False
    created_at: str = ""


@dataclass
class UserMFAEnrollment:
    """User MFA enrollment record."""
    id: int = 0
    user_id: int = 0
    method_code: str = ""
    method_name: str = ""
    is_primary: bool = False
    is_enabled: bool = True
    name: str = ""  # "Authenticator App", "Work Email"
    identifier: str = ""  # email address, phone last 4, device_id
    TOTP_secret: str = ""  # encrypted TOTP secret
    TOTP_issuer: str = ""  # issuer for QR code
    last_used_at: str = ""
    used_count: int = 0
    verified_at: str = ""
    enrolled_at: str = ""
    expires_at: str = ""
    created_at: str = ""
    company_id: int = 0
    device_name: str = ""
    device_fingerprint: str = ""


@dataclass
class RecoveryCode:
    """MFA recovery codes."""
    id: int = 0
    user_id: int = 0
    enrollment_id: int = 0
    code_hash: str = ""  # hashed recovery code
    code_index: int = 0  # 1-10
    is_used: bool = False
    used_at: str = ""
    used_for_session: str = ""
    created_at: str = ""
    expires_at: str = ""


# =============================================================================
# TRUSTED DEVICES
# =============================================================================

@dataclass
class TrustedDevice:
    """Trusted device for simplified MFA."""
    id: int = 0
    user_id: int = 0
    device_id: str = ""
    device_name: str = ""
    device_type: str = ""  # desktop, mobile, tablet
    browser: str = ""
    browser_version: str = ""
    os: str = ""
    os_version: str = ""
    device_fingerprint: str = ""
    ip_address: str = ""
    last_ip: str = ""
    user_agent: str = ""
    trusted_from: str = ""
    last_used_at: str = ""
    expires_at: str = ""
    is_current: bool = False
    is_active: bool = True
    created_at: str = ""
    challenge_sent_at: str = ""
    challenge_expires_at: str = ""
    company_id: int = 0


# =============================================================================
# USER SESSIONS
# =============================================================================

@dataclass
class UserSession:
    """Active user session."""
    id: int = 0
    session_id: str = ""  # token/handle
    user_id: int = 0
    username: str = ""
    device_id: str = ""
    ip_address: str = ""
    ip_country: str = ""
    user_agent: str = ""
    browser: str = ""
    browser_version: str = ""
    os: str = ""
    os_version: str = ""
    device_type: str = ""
    login_method: str = ""  # password, sso, mfa
    sso_provider_id: int = 0
    sso_provider_code: str = ""
    mfa_verified: bool = False
    mfa_method: str = ""
    session_started: str = ""
    last_activity: str = ""
    last_page: str = ""
    ip_binding_strict: bool = False
    is_active: bool = True
    is_suspicious: bool = False
    risk_score: int = 0  # 0-100
    risk_factors: str = ""  # JSON array of risk factors
    terminated_at: str = ""
    termination_reason: str = ""  # user_logout, admin_revoke, timeout, security, password_change
    company_id: int = 0
    branch_id: int = 0


# =============================================================================
# SECURITY EVENTS
# =============================================================================

@dataclass
class SecurityEvent:
    """Security event audit log."""
    id: int = 0
    event_type: str = ""  # login_success, login_failure, password_changed, mfa_enrolled, etc.
    event_category: str = ""  # authentication, authorization, session, policy, config
    severity: str = ""  # info, warning, critical
    timestamp: str = ""
    actor_user_id: int = 0
    actor_username: str = ""
    target_user_id: int = 0
    target_username: str = ""
    company_id: int = 0
    branch_id: int = 0
    session_id: str = ""
    provider_id: int = 0
    provider_code: str = ""
    device_id: int = 0
    source_ip: str = ""
    user_agent: str = ""
    event_data: str = ""  # JSON with event-specific details
    old_values: str = ""  # JSON for before state
    new_values: str = ""  # JSON for after state
    reason: str = ""
    correlation_id: str = ""
    status: str = ""  # success, failure, blocked
    failure_code: str = ""  # reason code for failures
    failure_message: str = ""
    browser_fingerprint: str = ""
    geo_location: str = ""


# =============================================================================
# SECURITY ALERTS
# =============================================================================

@dataclass
class SecurityAlert:
    """Security alert/incident."""
    id: int = 0
    alert_type: str = ""  # suspicious_login, mass_lockout, mfa_disabled, admin_outside_office, etc.
    title: str = ""
    description: str = ""
    severity: str = ""  # low, medium, high, critical
    status: str = ""  # new, acknowledged, investigating, resolved, false_positive
    owner_user_id: int = 0
    owner_username: str = ""
    assigned_to_user_id: int = 0
    assigned_to_username: str = ""
    company_id: int = 0
    branch_id: int = 0
    triggered_by_user_id: int = 0
    triggered_by_username: str = ""
    source_event_ids: str = ""  # comma-separated event IDs
    source_ip: str = ""
    ip_country: str = ""
    user_agent: str = ""
    session_id: str = ""
    provider_id: int = 0
    provider_code: str = ""
    alert_data: str = ""  # JSON with alert-specific data
    triggered_at: str = ""
    acknowledged_at: str = ""
    acknowledged_by: int = 0
    resolved_at: str = ""
    resolved_by: int = 0
    resolution_notes: str = ""
    false_positive_reason: str = ""
    escalation_level: int = 0
    flow_channel_id: str = ""  # linked Flow channel for incident discussion
    correlation_id: str = ""


# =============================================================================
# ACCESS REVIEWS
# =============================================================================

@dataclass
class AccessReviewCampaign:
    """Access review campaign."""
    id: int = 0
    campaign_name: str = ""
    campaign_type: str = ""  # periodic, triggered, onboarding, offboarding
    review_frequency: str = ""  # monthly, quarterly, annually, one_time
    description: str = ""
    owner_user_id: int = 0
    owner_username: str = ""
    reviewer_ids: str = ""  # comma-separated user IDs
    reviewer_names: str = ""
    start_date: str = ""
    end_date: str = ""
    due_date: str = ""
    status: str = ""  # draft, active, in_progress, overdue, completed, cancelled
    company_id: int = 0
    branch_id: int = 0
    scope_type: str = ""  # all, department, role, privilege_level
    scope_filter: str = ""  # JSON filter criteria
    include_mfa_status: bool = True
    include_sso_status: bool = True
    include_permissions: bool = True
    include_role_conflicts: bool = True
    include_inactive_users: bool = True
    inactive_threshold_days: int = 90
    auto_revoke_enabled: bool = False
    auto_revoke_after_days: int = 30
    reminder_days: str = "7,3,1"  # comma-separated days
    created_at: str = ""
    created_by: int = 0
    updated_at: str = ""
    updated_by: int = 0


@dataclass
class AccessReviewItem:
    """Individual access review item."""
    id: int = 0
    campaign_id: int = 0
    user_id: int = 0
    username: str = ""
    display_name: str = ""
    email: str = ""
    company_id: int = 0
    branch_id: int = 0
    department_id: int = 0
    department_name: str = ""
    role_name: str = ""
    privilege_level: str = ""  # standard, privileged, admin, super_admin
    has_mfa_enabled: bool = False
    has_sso_configured: bool = False
    last_login: str = ""
    login_count_30d: int = 0
    permission_count: int = 0
    role_conflict_count: int = 0
    status: str = ""  # pending, approved, revoked, escalated, skipped
    reviewer_user_id: int = 0
    reviewer_username: str = ""
    review_decision: str = ""  # approve, revoke, escalate, request_change
    review_comments: str = ""
    review_decided_at: str = ""
    reviewed_at: str = ""
    delegation_reason: str = ""
    next_review_date: str = ""
    company_policy_id: int = 0
    created_at: str = ""


# =============================================================================
# ROLE CONFLICT RULES
# =============================================================================

@dataclass
class RoleConflictRule:
    """Separation of Duties conflict rule."""
    id: int = 0
    rule_name: str = ""
    rule_description: str = ""
    conflict_type: str = ""  # mutual_exclusion, requires_supervision, hierarchy_violation
    role_a_id: int = 0
    role_a_name: str = ""
    role_b_id: int = 0
    role_b_name: str = ""
    permission_a: str = ""  # module.resource.action
    permission_b: str = ""
    severity: str = ""  # warning, error
    enforcement_mode: str = ""  # none, warning, soft_block, hard_block
    is_active: bool = True
    is_system: bool = False
    created_at: str = ""
    created_by: int = 0


@dataclass
class UserRoleConflict:
    """User with detected role conflicts."""
    id: int = 0
    user_id: int = 0
    username: str = ""
    display_name: str = ""
    company_id: int = 0
    rule_id: int = 0
    rule_name: str = ""
    role_a_id: int = 0
    role_a_name: str = ""
    role_b_id: int = 0
    role_b_name: str = ""
    detected_at: str = ""
    status: str = ""  # active, waived, resolved
    waiver_reason: str = ""
    waiver_by: int = 0
    waiver_at: str = ""


# =============================================================================
# EMERGENCY ACCESS / BREAK-GLASS
# =============================================================================

@dataclass
class EmergencyAccessAccount:
    """Break-glass emergency access accounts."""
    id: int = 0
    user_id: int = 0
    username: str = ""
    display_name: str = ""
    email: str = ""
    phone: str = ""
    emergency_role_id: int = 0
    emergency_role_name: str = ""
    is_active: bool = True
    activation_window_start: str = ""  # time window when break-glass is allowed
    activation_window_end: str = ""
    allowed_days: str = ""  # comma-separated: mon, tue, wed, thu, fri, sat, sun
    reason: str = ""
    approver_user_id: int = 0
    approver_username: str = ""
    approved_at: str = ""
    expiry_date: str = ""
    max_duration_hours: int = 8
    notify_security_on_use: bool = True
    notify_manager_on_use: bool = True
    company_id: int = 0
    branch_id: int = 0
    created_at: str = ""
    created_by: int = 0


@dataclass
class EmergencyAccessLog:
    """Break-glass usage log."""
    id: int = 0
    emergency_account_id: int = 0
    user_id: int = 0
    username: str = ""
    display_name: str = ""
    activated_at: str = ""
    deactivated_at: str = ""
    duration_minutes: int = 0
    reason_given: str = ""
    ticket_reference: str = ""
    ip_address: str = ""
    user_agent: str = ""
    session_id: str = ""
    actions_performed: str = ""  # JSON array of actions taken
    is_approved_expost: bool = False
    approved_by: int = 0
    approved_by_username: str = ""
    approval_notes: str = ""
    approved_at: str = ""
    denied_by: int = 0
    denied_by_username: str = ""
    denial_reason: str = ""
    denied_at: str = ""
    status: str = ""  # active, deactivated, expired, approved_expost, denied
    correlation_id: str = ""


# =============================================================================
# SECURITY POLICIES
# =============================================================================

@dataclass
class SecurityPolicy:
    """Security policy configuration."""
    id: int = 0
    policy_type: str = ""  # password, session, mfa, lockout, sso, ip, api, alerts
    policy_name: str = ""
    description: str = ""
    company_id: int = 0  # 0 = global
    is_enabled: bool = True
    is_system: bool = True
    rules: str = ""  # JSON: {"min_length": 12, "require_uppercase": true, ...}
    applies_to: str = ""  # all, admins, privileged, department_ids
    applies_to_roles: str = ""  # comma-separated role IDs
    applies_to_departments: str = ""
    priority: int = 100
    grace_period_hours: int = 0
    notification_template_id: int = 0
    enforcement_start: str = ""
    created_at: str = ""
    created_by: int = 0
    updated_at: str = ""
    updated_by: int = 0
    version: int = 1


@dataclass
class SecurityPolicyVersion:
    """Version history for security policies."""
    id: int = 0
    policy_id: int = 0
    version: int = 1
    rules: str = ""
    changed_by: int = 0
    changed_by_username: str = ""
    changed_at: str = ""
    change_reason: str = ""
    old_rules: str = ""


# =============================================================================
# API SECURITY
# =============================================================================

@dataclass
class APISecurityEvent:
    """API authentication and usage events."""
    id: int = 0
    api_client_id: str = ""
    api_key_id: str = ""
    user_id: int = 0
    username: str = ""
    event_type: str = ""  # auth_success, auth_failure, key_created, key_revoked, key_used
    endpoint: str = ""
    method: str = ""
    source_ip: str = ""
    user_agent: str = ""
    response_code: int = 0
    response_time_ms: int = 0
    event_data: str = ""  # JSON
    timestamp: str = ""
    correlation_id: str = ""


# =============================================================================
# LOGIN ATTEMPTS TRACKING
# =============================================================================

@dataclass
class LoginAttempt:
    """Login attempt tracking."""
    id: int = 0
    user_id: int = 0
    username: str = ""
    email: str = ""
    source_ip: str = ""
    user_agent: str = ""
    login_method: str = ""  # password, sso, mfa
    sso_provider_id: int = 0
    sso_provider_code: str = ""
    mfa_method: str = ""
    mfa_passed: bool = False
    success: bool = False
    failure_reason: str = ""
    country: str = ""
    city: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    is_proxy: bool = False
    is_tor: bool = False
    is_vpn: bool = False
    is_datacenter: bool = False
    timestamp: str = ""


# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

def init_security_tables():
    """Initialize all security tables."""
    with get_db_context() as db:
        # SSO Providers
        db.execute("""
            CREATE TABLE IF NOT EXISTS sso_providers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_code TEXT UNIQUE NOT NULL,
                provider_name TEXT NOT NULL,
                provider_type TEXT NOT NULL DEFAULT 'oidc',
                client_id TEXT DEFAULT '',
                client_secret TEXT DEFAULT '',
                discovery_url TEXT DEFAULT '',
                issuer TEXT DEFAULT '',
                authorization_endpoint TEXT DEFAULT '',
                token_endpoint TEXT DEFAULT '',
                userinfo_endpoint TEXT DEFAULT '',
                jwks_uri TEXT DEFAULT '',
                logout_endpoint TEXT DEFAULT '',
                sign_cert TEXT DEFAULT '',
                sign_key TEXT DEFAULT '',
                enc_cert TEXT DEFAULT '',
                scopes TEXT DEFAULT 'openid profile email',
                claim_mappings TEXT DEFAULT '{}',
                role_mappings TEXT DEFAULT '{}',
                auto_link_policy TEXT DEFAULT 'email',
                default_role_id INTEGER DEFAULT 0,
                default_company_id INTEGER DEFAULT 0,
                default_branch_id INTEGER DEFAULT 0,
                default_department_id INTEGER DEFAULT 0,
                domain_hint TEXT DEFAULT '',
                icon_url TEXT DEFAULT '',
                button_style TEXT DEFAULT 'full',
                is_enabled INTEGER DEFAULT 0,
                is_visible INTEGER DEFAULT 1,
                is_default INTEGER DEFAULT 0,
                force_authn INTEGER DEFAULT 0,
                want_assertions_signed INTEGER DEFAULT 1,
                jit_provisioning_enabled INTEGER DEFAULT 0,
                session_duration INTEGER DEFAULT 480,
                allowed_company_ids TEXT DEFAULT '',
                ip_whitelist TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                created_by INTEGER DEFAULT 0,
                updated_at TEXT DEFAULT (datetime('now')),
                updated_by INTEGER DEFAULT 0,
                notes TEXT DEFAULT '',
                last_test_at TEXT DEFAULT '',
                last_test_result TEXT DEFAULT ''
            )
        """)

        # SSO Provider Certificates
        db.execute("""
            CREATE TABLE IF NOT EXISTS sso_provider_certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_id INTEGER NOT NULL,
                cert_type TEXT NOT NULL DEFAULT 'sign',
                cert_content TEXT DEFAULT '',
                key_content TEXT DEFAULT '',
                serial_number TEXT DEFAULT '',
                subject_cn TEXT DEFAULT '',
                issuer_cn TEXT DEFAULT '',
                valid_from TEXT DEFAULT '',
                valid_to TEXT DEFAULT '',
                fingerprint_sha256 TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                created_by INTEGER DEFAULT 0,
                FOREIGN KEY (provider_id) REFERENCES sso_providers(id) ON DELETE CASCADE
            )
        """)

        # SSO Audit Log
        db.execute("""
            CREATE TABLE IF NOT EXISTS sso_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_id INTEGER DEFAULT 0,
                provider_code TEXT DEFAULT '',
                event_type TEXT NOT NULL,
                subject_user TEXT DEFAULT '',
                email TEXT DEFAULT '',
                username TEXT DEFAULT '',
                mapped_user_id INTEGER DEFAULT 0,
                mapped_username TEXT DEFAULT '',
                idp_session_id TEXT DEFAULT '',
                sp_session_id TEXT DEFAULT '',
                source_ip TEXT DEFAULT '',
                user_agent TEXT DEFAULT '',
                auth_method TEXT DEFAULT '',
                requested_scopes TEXT DEFAULT '',
                granted_roles TEXT DEFAULT '',
                failure_reason TEXT DEFAULT '',
                event_timestamp TEXT DEFAULT (datetime('now')),
                correlation_id TEXT DEFAULT ''
            )
        """)

        # MFA Methods
        db.execute("""
            CREATE TABLE IF NOT EXISTS mfa_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method_code TEXT UNIQUE NOT NULL,
                method_name TEXT NOT NULL,
                description TEXT DEFAULT '',
                icon TEXT DEFAULT 'fa-mobile-alt',
                instructions TEXT DEFAULT '',
                config_schema TEXT DEFAULT '{}',
                is_enabled INTEGER DEFAULT 1,
                is_builtin INTEGER DEFAULT 1,
                priority INTEGER DEFAULT 100,
                setup_timeout_minutes INTEGER DEFAULT 10,
                otp_length INTEGER DEFAULT 6,
                otp_expiry_seconds INTEGER DEFAULT 300,
                max_attempts INTEGER DEFAULT 3,
                requiresecure_channel INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # User MFA Enrollments
        db.execute("""
            CREATE TABLE IF NOT EXISTS user_mfa_enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                method_code TEXT NOT NULL,
                method_name TEXT NOT NULL,
                is_primary INTEGER DEFAULT 0,
                is_enabled INTEGER DEFAULT 1,
                name TEXT DEFAULT '',
                identifier TEXT DEFAULT '',
                TOTP_secret TEXT DEFAULT '',
                TOTP_issuer TEXT DEFAULT '',
                last_used_at TEXT DEFAULT '',
                used_count INTEGER DEFAULT 0,
                verified_at TEXT DEFAULT '',
                enrolled_at TEXT DEFAULT (datetime('now')),
                expires_at TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                company_id INTEGER DEFAULT 0,
                device_name TEXT DEFAULT '',
                device_fingerprint TEXT DEFAULT ''
            )
        """)

        # Recovery Codes
        db.execute("""
            CREATE TABLE IF NOT EXISTS recovery_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                enrollment_id INTEGER DEFAULT 0,
                code_hash TEXT NOT NULL,
                code_index INTEGER DEFAULT 0,
                is_used INTEGER DEFAULT 0,
                used_at TEXT DEFAULT '',
                used_for_session TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                expires_at TEXT DEFAULT ''
            )
        """)

        # Trusted Devices
        db.execute("""
            CREATE TABLE IF NOT EXISTS trusted_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                device_id TEXT NOT NULL,
                device_name TEXT DEFAULT '',
                device_type TEXT DEFAULT 'desktop',
                browser TEXT DEFAULT '',
                browser_version TEXT DEFAULT '',
                os TEXT DEFAULT '',
                os_version TEXT DEFAULT '',
                device_fingerprint TEXT DEFAULT '',
                ip_address TEXT DEFAULT '',
                last_ip TEXT DEFAULT '',
                user_agent TEXT DEFAULT '',
                trusted_from TEXT DEFAULT (datetime('now')),
                last_used_at TEXT DEFAULT '',
                expires_at TEXT DEFAULT '',
                is_current INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                challenge_sent_at TEXT DEFAULT '',
                challenge_expires_at TEXT DEFAULT '',
                company_id INTEGER DEFAULT 0
            )
        """)

        # User Sessions
        db.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT DEFAULT '',
                device_id TEXT DEFAULT '',
                ip_address TEXT DEFAULT '',
                ip_country TEXT DEFAULT '',
                user_agent TEXT DEFAULT '',
                browser TEXT DEFAULT '',
                browser_version TEXT DEFAULT '',
                os TEXT DEFAULT '',
                os_version TEXT DEFAULT '',
                device_type TEXT DEFAULT '',
                login_method TEXT DEFAULT 'password',
                sso_provider_id INTEGER DEFAULT 0,
                sso_provider_code TEXT DEFAULT '',
                mfa_verified INTEGER DEFAULT 0,
                mfa_method TEXT DEFAULT '',
                session_started TEXT DEFAULT (datetime('now')),
                last_activity TEXT DEFAULT (datetime('now')),
                last_page TEXT DEFAULT '',
                ip_binding_strict INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                is_suspicious INTEGER DEFAULT 0,
                risk_score INTEGER DEFAULT 0,
                risk_factors TEXT DEFAULT '[]',
                terminated_at TEXT DEFAULT '',
                termination_reason TEXT DEFAULT '',
                company_id INTEGER DEFAULT 0,
                branch_id INTEGER DEFAULT 0
            )
        """)

        # Security Events
        db.execute("""
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                event_category TEXT DEFAULT '',
                severity TEXT DEFAULT 'info',
                timestamp TEXT DEFAULT (datetime('now')),
                actor_user_id INTEGER DEFAULT 0,
                actor_username TEXT DEFAULT '',
                target_user_id INTEGER DEFAULT 0,
                target_username TEXT DEFAULT '',
                company_id INTEGER DEFAULT 0,
                branch_id INTEGER DEFAULT 0,
                session_id TEXT DEFAULT '',
                provider_id INTEGER DEFAULT 0,
                provider_code TEXT DEFAULT '',
                device_id INTEGER DEFAULT 0,
                source_ip TEXT DEFAULT '',
                user_agent TEXT DEFAULT '',
                event_data TEXT DEFAULT '{}',
                old_values TEXT DEFAULT '{}',
                new_values TEXT DEFAULT '{}',
                reason TEXT DEFAULT '',
                correlation_id TEXT DEFAULT '',
                status TEXT DEFAULT 'success',
                failure_code TEXT DEFAULT '',
                failure_message TEXT DEFAULT '',
                browser_fingerprint TEXT DEFAULT '',
                geo_location TEXT DEFAULT ''
            )
        """)

        # Security Alerts
        db.execute("""
            CREATE TABLE IF NOT EXISTS security_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                severity TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'new',
                owner_user_id INTEGER DEFAULT 0,
                owner_username TEXT DEFAULT '',
                assigned_to_user_id INTEGER DEFAULT 0,
                assigned_to_username TEXT DEFAULT '',
                company_id INTEGER DEFAULT 0,
                branch_id INTEGER DEFAULT 0,
                triggered_by_user_id INTEGER DEFAULT 0,
                triggered_by_username TEXT DEFAULT '',
                source_event_ids TEXT DEFAULT '',
                source_ip TEXT DEFAULT '',
                ip_country TEXT DEFAULT '',
                user_agent TEXT DEFAULT '',
                session_id TEXT DEFAULT '',
                provider_id INTEGER DEFAULT 0,
                provider_code TEXT DEFAULT '',
                alert_data TEXT DEFAULT '{}',
                triggered_at TEXT DEFAULT (datetime('now')),
                acknowledged_at TEXT DEFAULT '',
                acknowledged_by INTEGER DEFAULT 0,
                resolved_at TEXT DEFAULT '',
                resolved_by INTEGER DEFAULT 0,
                resolution_notes TEXT DEFAULT '',
                false_positive_reason TEXT DEFAULT '',
                escalation_level INTEGER DEFAULT 0,
                flow_channel_id TEXT DEFAULT '',
                correlation_id TEXT DEFAULT ''
            )
        """)

        # Access Review Campaigns
        db.execute("""
            CREATE TABLE IF NOT EXISTS access_review_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_name TEXT NOT NULL,
                campaign_type TEXT DEFAULT 'periodic',
                review_frequency TEXT DEFAULT 'quarterly',
                description TEXT DEFAULT '',
                owner_user_id INTEGER DEFAULT 0,
                owner_username TEXT DEFAULT '',
                reviewer_ids TEXT DEFAULT '',
                reviewer_names TEXT DEFAULT '',
                start_date TEXT DEFAULT '',
                end_date TEXT DEFAULT '',
                due_date TEXT DEFAULT '',
                status TEXT DEFAULT 'draft',
                company_id INTEGER DEFAULT 0,
                branch_id INTEGER DEFAULT 0,
                scope_type TEXT DEFAULT 'all',
                scope_filter TEXT DEFAULT '{}',
                include_mfa_status INTEGER DEFAULT 1,
                include_sso_status INTEGER DEFAULT 1,
                include_permissions INTEGER DEFAULT 1,
                include_role_conflicts INTEGER DEFAULT 1,
                include_inactive_users INTEGER DEFAULT 1,
                inactive_threshold_days INTEGER DEFAULT 90,
                auto_revoke_enabled INTEGER DEFAULT 0,
                auto_revoke_after_days INTEGER DEFAULT 30,
                reminder_days TEXT DEFAULT '7,3,1',
                created_at TEXT DEFAULT (datetime('now')),
                created_by INTEGER DEFAULT 0,
                updated_at TEXT DEFAULT (datetime('now')),
                updated_by INTEGER DEFAULT 0
            )
        """)

        # Access Review Items
        db.execute("""
            CREATE TABLE IF NOT EXISTS access_review_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT DEFAULT '',
                display_name TEXT DEFAULT '',
                email TEXT DEFAULT '',
                company_id INTEGER DEFAULT 0,
                branch_id INTEGER DEFAULT 0,
                department_id INTEGER DEFAULT 0,
                department_name TEXT DEFAULT '',
                role_name TEXT DEFAULT '',
                privilege_level TEXT DEFAULT 'standard',
                has_mfa_enabled INTEGER DEFAULT 0,
                has_sso_configured INTEGER DEFAULT 0,
                last_login TEXT DEFAULT '',
                login_count_30d INTEGER DEFAULT 0,
                permission_count INTEGER DEFAULT 0,
                role_conflict_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                reviewer_user_id INTEGER DEFAULT 0,
                reviewer_username TEXT DEFAULT '',
                review_decision TEXT DEFAULT '',
                review_comments TEXT DEFAULT '',
                review_decided_at TEXT DEFAULT '',
                reviewed_at TEXT DEFAULT '',
                delegation_reason TEXT DEFAULT '',
                next_review_date TEXT DEFAULT '',
                company_policy_id INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # Role Conflict Rules
        db.execute("""
            CREATE TABLE IF NOT EXISTS role_conflict_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL,
                rule_description TEXT DEFAULT '',
                conflict_type TEXT DEFAULT 'mutual_exclusion',
                role_a_id INTEGER NOT NULL,
                role_a_name TEXT DEFAULT '',
                role_b_id INTEGER NOT NULL,
                role_b_name TEXT DEFAULT '',
                permission_a TEXT DEFAULT '',
                permission_b TEXT DEFAULT '',
                severity TEXT DEFAULT 'warning',
                enforcement_mode TEXT DEFAULT 'warning',
                is_active INTEGER DEFAULT 1,
                is_system INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                created_by INTEGER DEFAULT 0
            )
        """)

        # User Role Conflicts
        db.execute("""
            CREATE TABLE IF NOT EXISTS user_role_conflicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT DEFAULT '',
                display_name TEXT DEFAULT '',
                company_id INTEGER DEFAULT 0,
                rule_id INTEGER NOT NULL,
                rule_name TEXT DEFAULT '',
                role_a_id INTEGER DEFAULT 0,
                role_a_name TEXT DEFAULT '',
                role_b_id INTEGER DEFAULT 0,
                role_b_name TEXT DEFAULT '',
                detected_at TEXT DEFAULT (datetime('now')),
                status TEXT DEFAULT 'active',
                waiver_reason TEXT DEFAULT '',
                waiver_by INTEGER DEFAULT 0,
                waiver_at TEXT DEFAULT ''
            )
        """)

        # Emergency Access Accounts
        db.execute("""
            CREATE TABLE IF NOT EXISTS emergency_access_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT DEFAULT '',
                display_name TEXT DEFAULT '',
                email TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                emergency_role_id INTEGER DEFAULT 0,
                emergency_role_name TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                activation_window_start TEXT DEFAULT '',
                activation_window_end TEXT DEFAULT '',
                allowed_days TEXT DEFAULT '',
                reason TEXT DEFAULT '',
                approver_user_id INTEGER DEFAULT 0,
                approver_username TEXT DEFAULT '',
                approved_at TEXT DEFAULT '',
                expiry_date TEXT DEFAULT '',
                max_duration_hours INTEGER DEFAULT 8,
                notify_security_on_use INTEGER DEFAULT 1,
                notify_manager_on_use INTEGER DEFAULT 1,
                company_id INTEGER DEFAULT 0,
                branch_id INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                created_by INTEGER DEFAULT 0
            )
        """)

        # Emergency Access Logs
        db.execute("""
            CREATE TABLE IF NOT EXISTS emergency_access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emergency_account_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT DEFAULT '',
                display_name TEXT DEFAULT '',
                activated_at TEXT DEFAULT (datetime('now')),
                deactivated_at TEXT DEFAULT '',
                duration_minutes INTEGER DEFAULT 0,
                reason_given TEXT DEFAULT '',
                ticket_reference TEXT DEFAULT '',
                ip_address TEXT DEFAULT '',
                user_agent TEXT DEFAULT '',
                session_id TEXT DEFAULT '',
                actions_performed TEXT DEFAULT '[]',
                is_approved_expost INTEGER DEFAULT 0,
                approved_by INTEGER DEFAULT 0,
                approved_by_username TEXT DEFAULT '',
                approval_notes TEXT DEFAULT '',
                approved_at TEXT DEFAULT '',
                denied_by INTEGER DEFAULT 0,
                denied_by_username TEXT DEFAULT '',
                denial_reason TEXT DEFAULT '',
                denied_at TEXT DEFAULT '',
                status TEXT DEFAULT 'active',
                correlation_id TEXT DEFAULT ''
            )
        """)

        # Security Policies
        db.execute("""
            CREATE TABLE IF NOT EXISTS security_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                policy_type TEXT NOT NULL,
                policy_name TEXT NOT NULL,
                description TEXT DEFAULT '',
                company_id INTEGER DEFAULT 0,
                is_enabled INTEGER DEFAULT 1,
                is_system INTEGER DEFAULT 1,
                rules TEXT DEFAULT '{}',
                applies_to TEXT DEFAULT 'all',
                applies_to_roles TEXT DEFAULT '',
                applies_to_departments TEXT DEFAULT '',
                priority INTEGER DEFAULT 100,
                grace_period_hours INTEGER DEFAULT 0,
                notification_template_id INTEGER DEFAULT 0,
                enforcement_start TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                created_by INTEGER DEFAULT 0,
                updated_at TEXT DEFAULT (datetime('now')),
                updated_by INTEGER DEFAULT 0,
                version INTEGER DEFAULT 1
            )
        """)

        # Security Policy Versions
        db.execute("""
            CREATE TABLE IF NOT EXISTS security_policy_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                policy_id INTEGER NOT NULL,
                version INTEGER DEFAULT 1,
                rules TEXT DEFAULT '{}',
                changed_by INTEGER DEFAULT 0,
                changed_by_username TEXT DEFAULT '',
                changed_at TEXT DEFAULT (datetime('now')),
                change_reason TEXT DEFAULT '',
                old_rules TEXT DEFAULT '{}'
            )
        """)

        # API Security Events
        db.execute("""
            CREATE TABLE IF NOT EXISTS api_security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_client_id TEXT DEFAULT '',
                api_key_id TEXT DEFAULT '',
                user_id INTEGER DEFAULT 0,
                username TEXT DEFAULT '',
                event_type TEXT NOT NULL,
                endpoint TEXT DEFAULT '',
                method TEXT DEFAULT '',
                source_ip TEXT DEFAULT '',
                user_agent TEXT DEFAULT '',
                response_code INTEGER DEFAULT 0,
                response_time_ms INTEGER DEFAULT 0,
                event_data TEXT DEFAULT '{}',
                timestamp TEXT DEFAULT (datetime('now')),
                correlation_id TEXT DEFAULT ''
            )
        """)

        # Login Attempts
        db.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 0,
                username TEXT DEFAULT '',
                email TEXT DEFAULT '',
                source_ip TEXT DEFAULT '',
                user_agent TEXT DEFAULT '',
                login_method TEXT DEFAULT 'password',
                sso_provider_id INTEGER DEFAULT 0,
                sso_provider_code TEXT DEFAULT '',
                mfa_method TEXT DEFAULT '',
                mfa_passed INTEGER DEFAULT 0,
                success INTEGER DEFAULT 0,
                failure_reason TEXT DEFAULT '',
                country TEXT DEFAULT '',
                city TEXT DEFAULT '',
                latitude REAL DEFAULT 0.0,
                longitude REAL DEFAULT 0.0,
                is_proxy INTEGER DEFAULT 0,
                is_tor INTEGER DEFAULT 0,
                is_vpn INTEGER DEFAULT 0,
                is_datacenter INTEGER DEFAULT 0,
                timestamp TEXT DEFAULT (datetime('now'))
            )
        """)

        # Create indexes
        indexes = [
            ("idx_sso_providers_enabled", "sso_providers", "is_enabled"),
            ("idx_sso_audit_timestamp", "sso_audit_log", "event_timestamp"),
            ("idx_sso_audit_user", "sso_audit_log", "subject_user"),
            ("idx_user_mfa_user", "user_mfa_enrollments", "user_id"),
            ("idx_recovery_user", "recovery_codes", "user_id"),
            ("idx_trusted_devices_user", "trusted_devices", "user_id"),
            ("idx_sessions_user", "user_sessions", "user_id"),
            ("idx_sessions_session_id", "user_sessions", "session_id"),
            ("idx_sessions_active", "user_sessions", "is_active"),
            ("idx_security_events_timestamp", "security_events", "timestamp"),
            ("idx_security_events_type", "security_events", "event_type"),
            ("idx_security_events_user", "security_events", "actor_user_id"),
            ("idx_security_alerts_status", "security_alerts", "status"),
            ("idx_security_alerts_severity", "security_alerts", "severity"),
            ("idx_access_review_campaigns_status", "access_review_campaigns", "status"),
            ("idx_access_review_items_campaign", "access_review_items", "campaign_id"),
            ("idx_access_review_items_user", "access_review_items", "user_id"),
            ("idx_user_role_conflicts_user", "user_role_conflicts", "user_id"),
            ("idx_emergency_access_logs_user", "emergency_access_logs", "user_id"),
            ("idx_login_attempts_user", "login_attempts", "user_id"),
            ("idx_login_attempts_ip", "login_attempts", "source_ip"),
            ("idx_login_attempts_timestamp", "login_attempts", "timestamp"),
        ]

        for idx_name, table, column in indexes:
            try:
                db.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})")
            except Exception:
                pass


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
    """Hash password with SHA-256 + salt."""
    if salt is None:
        salt = secrets.token_hex(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return base64.b64encode(key).decode(), salt


def verify_password(password: str, hash_value: str, salt: str) -> bool:
    """Verify password against hash."""
    computed_hash, _ = hash_password(password, salt)
    return computed_hash == hash_value


def generate_session_id() -> str:
    """Generate secure session ID."""
    return secrets.token_urlsafe(48)


def generate_device_id() -> str:
    """Generate device ID."""
    return secrets.token_hex(24)


def generate_recovery_codes(count: int = 10) -> List[str]:
    """Generate recovery codes."""
    return [secrets.token_hex(4).upper() for _ in range(count)]


def create_security_event(
    event_type: str,
    event_category: str,
    severity: str,
    actor_user_id: int = 0,
    actor_username: str = "",
    target_user_id: int = 0,
    target_username: str = "",
    company_id: int = 0,
    source_ip: str = "",
    user_agent: str = "",
    event_data: Dict = None,
    status: str = "success",
    failure_reason: str = "",
    session_id: str = "",
    provider_id: int = 0,
    provider_code: str = "",
) -> int:
    """Create a security event."""
    import json
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO security_events (
                event_type, event_category, severity, actor_user_id, actor_username,
                target_user_id, target_username, company_id, source_ip, user_agent,
                event_data, status, failure_message, session_id, provider_id, provider_code
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_type, event_category, severity, actor_user_id, actor_username,
            target_user_id, target_username, company_id, source_ip, user_agent,
            json.dumps(event_data or {}), status, failure_reason, session_id,
            provider_id, provider_code
        ))
        return cursor.lastrowid


def create_security_alert(
    alert_type: str,
    title: str,
    description: str,
    severity: str,
    company_id: int = 0,
    triggered_by_user_id: int = 0,
    triggered_by_username: str = "",
    source_ip: str = "",
    source_event_ids: str = "",
    alert_data: Dict = None,
) -> int:
    """Create a security alert."""
    import json
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO security_alerts (
                alert_type, title, description, severity, company_id,
                triggered_by_user_id, triggered_by_username, source_ip,
                source_event_ids, alert_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert_type, title, description, severity, company_id,
            triggered_by_user_id, triggered_by_username, source_ip,
            source_event_ids, json.dumps(alert_data or {})
        ))
        return cursor.lastrowid


def get_user_sessions(user_id: int, active_only: bool = True) -> List[Dict]:
    """Get user sessions."""
    with get_db_context() as db:
        query = "SELECT * FROM user_sessions WHERE user_id = ?"
        if active_only:
            query += " AND is_active = 1"
        query += " ORDER BY last_activity DESC"
        return rows_to_list(db.execute(query, (user_id,)).fetchall())


def get_user_mfa_enrollments(user_id: int) -> List[Dict]:
    """Get user MFA enrollments."""
    with get_db_context() as db:
        return rows_to_list(db.execute(
            "SELECT * FROM user_mfa_enrollments WHERE user_id = ? AND is_enabled = 1",
            (user_id,)
        ).fetchall())


def get_trusted_devices(user_id: int) -> List[Dict]:
    """Get user trusted devices."""
    with get_db_context() as db:
        return rows_to_list(db.execute(
            "SELECT * FROM trusted_devices WHERE user_id = ? AND is_active = 1",
            (user_id,)
        ).fetchall())


def get_security_events(
    event_type: str = None,
    severity: str = None,
    user_id: int = None,
    company_id: int = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict]:
    """Get security events with filters."""
    with get_db_context() as db:
        query = "SELECT * FROM security_events WHERE 1=1"
        params = []

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        if user_id:
            query += " AND (actor_user_id = ? OR target_user_id = ?)"
            params.extend([user_id, user_id])
        if company_id:
            query += " AND company_id = ?"
            params.append(company_id)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        return rows_to_list(db.execute(query, params).fetchall())


def get_security_alerts(
    status: str = None,
    severity: str = None,
    company_id: int = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict]:
    """Get security alerts with filters."""
    with get_db_context() as db:
        query = "SELECT * FROM security_alerts WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        if company_id:
            query += " AND company_id = ?"
            params.append(company_id)

        query += " ORDER BY triggered_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        return rows_to_list(db.execute(query, params).fetchall())


def get_sso_providers(enabled_only: bool = False) -> List[Dict]:
    """Get SSO providers."""
    with get_db_context() as db:
        query = "SELECT * FROM sso_providers"
        if enabled_only:
            query += " WHERE is_enabled = 1"
        query += " ORDER BY is_default DESC, provider_name ASC"
        return rows_to_list(db.execute(query).fetchall())


def get_security_policies(policy_type: str = None, company_id: int = 0) -> List[Dict]:
    """Get security policies."""
    with get_db_context() as db:
        query = "SELECT * FROM security_policies WHERE (company_id = 0 OR company_id = ?)"
        params = [company_id]

        if policy_type:
            query += " AND policy_type = ?"
            params.append(policy_type)

        query += " ORDER BY priority DESC, is_system DESC"
        return rows_to_list(db.execute(query, params).fetchall())


def get_access_review_campaigns(status: str = None) -> List[Dict]:
    """Get access review campaigns."""
    with get_db_context() as db:
        query = "SELECT * FROM access_review_campaigns"
        if status:
            query += " WHERE status = ?"
            return rows_to_list(db.execute(query, (status,)).fetchall())
        query += " ORDER BY created_at DESC"
        return rows_to_list(db.execute(query).fetchall())


if __name__ == "__main__":
    init_security_tables()
    print("Security tables initialized successfully.")
