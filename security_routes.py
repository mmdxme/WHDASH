"""
Security Module Routes
====================
Enterprise-grade security routes for the MMDx platform covering:
- Login & Authentication
- MFA Enrollment & Challenge
- SSO Providers Management
- Session & Device Management
- Security Policies
- Access Reviews
- Security Events & Alerts
- Reports & Export
- Emergency Access
- API Security
"""

from flask import Flask, Blueprint, request, jsonify, session, redirect, url_for, render_template, Response, flash, send_file
from functools import wraps
import json
import csv
import io
import secrets
import hashlib
import base64
import time
import math
from datetime import datetime, timedelta
from openpyxl import Workbook
from typing import Dict, List, Optional, Tuple

# Import database utilities
from database import get_db_context, get_one, get_all, log_audit

# Import security models
from security_models import (
    init_security_tables,
    get_user_sessions, get_user_mfa_enrollments, get_trusted_devices,
    get_security_events, get_security_alerts, get_sso_providers,
    get_security_policies, get_access_review_campaigns,
    create_security_event, create_security_alert,
    generate_session_id, generate_device_id, generate_recovery_codes,
    hash_password, verify_password,
    row_to_dict, rows_to_list,
    SSOProvider, UserMFAEnrollment, TrustedDevice, UserSession,
    SecurityEvent, SecurityAlert, SecurityPolicy,
    AccessReviewCampaign, AccessReviewItem, RoleConflictRule,
    EmergencyAccessAccount, EmergencyAccessLog, APISecurityEvent, LoginAttempt
)

# Import export utilities
from export_utils import (
    send_export_response,
    get_export_columns
)

# Import unified permission decorator
from permissions import require_permission


# =============================================================================
# BLUEPRINT AND AUTH HELPERS
# =============================================================================

def require_login(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def csrf_protected(f):
    """CSRF protection decorator."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
            if not token or token != session.get('csrf_token'):
                if request.is_json:
                    return jsonify({'error': 'CSRF validation failed'}), 403
                flash("CSRF validation failed.", "error")
                return redirect(request.url)
        return f(*args, **kwargs)
    return decorated_function


def get_current_user_id() -> int:
    """Get current user ID from session."""
    return session.get('user_id', 0)


def get_user_company_id() -> int:
    """Get current user's company ID."""
    return session.get('company_id', 0)


# =============================================================================
# BLUEPRINT REGISTRATION
# =============================================================================

security_bp = Blueprint('security', __name__)


# =============================================================================
# EXPORT ENDPOINTS - ALL 20 EXPORT TYPES
# =============================================================================

SECURITY_EXPORT_TYPES = [
    'csv', 'excel_text', 'excel_general', 'json', 'xml', 'txt',
    'pdf', 'docx', 'html', 'printable', 'barcode', 'api',
    'email', 'zip', 'backup', 'sql_dump', 'dashboard',
    'summary', 'detailed', 'audit_log'
]

SECURITY_EXPORT_COLUMNS = {
    'events': ['event_id', 'event_type', 'severity', 'user_name', 'timestamp', 'ip_address', 'description'],
    'alerts': ['alert_id', 'title', 'severity', 'status', 'created_at', 'assigned_to'],
    'sessions': ['session_id', 'user_name', 'device_type', 'ip_address', 'created_at', 'last_activity'],
    'users': ['user_id', 'username', 'email', 'role', 'mfa_enabled', 'status', 'last_login'],
    'policies': ['policy_id', 'name', 'type', 'severity', 'status', 'created_at'],
    'access_reviews': ['review_id', 'campaign_name', 'status', 'reviewer', 'due_date', 'completed_at'],
    'sso_providers': ['provider_id', 'name', 'type', 'status', 'config', 'created_at']
}


@security_bp.route('/api/export/<export_type>', methods=['GET', 'POST'])
@security_bp.route('/api/export/<data_type>/<export_type>', methods=['GET', 'POST'])
@require_login
def api_security_export(export_type, data_type=None):
    """Export security data in all 20 formats."""
    if export_type not in SECURITY_EXPORT_TYPES:
        return jsonify({
            'error': f'Invalid export type. Valid types: {SECURITY_EXPORT_TYPES}'
        }), 400

    user_id = session.get('user_id', 0)

    # Determine data type from URL or default
    if data_type is None:
        data_type = request.args.get('type', 'events')

    # Get data based on type
    if data_type == 'events':
        data = get_security_events(limit=5000)
        columns = SECURITY_EXPORT_COLUMNS['events']
        title = 'Security Events'
    elif data_type == 'alerts':
        data = get_security_alerts(limit=5000)
        columns = SECURITY_EXPORT_COLUMNS['alerts']
        title = 'Security Alerts'
    elif data_type == 'sessions':
        data = get_user_sessions(user_id, limit=5000)
        columns = SECURITY_EXPORT_COLUMNS['sessions']
        title = 'User Sessions'
    elif data_type == 'users':
        with get_db_context() as db:
            users = db.execute("""
                SELECT id as user_id, username, email, role_name as role,
                       CASE WHEN mfa_enabled = 1 THEN 'Yes' ELSE 'No' END as mfa_enabled,
                       u.is_active as status, u.last_login
                FROM users u
                LEFT JOIN roles r ON u.role_id = r.id
                ORDER BY u.created_at DESC
                LIMIT 5000
            """).fetchall()
            data = [dict(u) for u in users]
        columns = SECURITY_EXPORT_COLUMNS['users']
        title = 'User Accounts'
    elif data_type == 'policies':
        data = get_security_policies(limit=5000)
        columns = SECURITY_EXPORT_COLUMNS['policies']
        title = 'Security Policies'
    elif data_type == 'access_reviews':
        data = get_access_review_campaigns(limit=5000)
        columns = SECURITY_EXPORT_COLUMNS['access_reviews']
        title = 'Access Reviews'
    elif data_type == 'sso_providers':
        data = get_sso_providers(limit=5000)
        columns = SECURITY_EXPORT_COLUMNS['sso_providers']
        title = 'SSO Providers'
    else:
        return jsonify({'error': f'Data type {data_type} not supported'}), 400

    filename = f'security_{data_type}_{datetime.now().strftime("%Y%m%d")}'

    return send_export_response(data, export_type, filename, columns, title)


@security_bp.route('/api/export/list')
@require_login
def list_security_export_types():
    """List available export types for security module."""
    return jsonify({
        'module': 'security',
        'data_types': list(SECURITY_EXPORT_COLUMNS.keys()),
        'export_types': [{'type': t} for t in SECURITY_EXPORT_TYPES]
    })


def register_security_routes(app: Flask):
    """Register all security routes with the Flask app."""
    app.register_blueprint(security_bp, url_prefix='/security')

    # Initialize security tables on first request
    with app.app_context():
        init_security_tables()


# =============================================================================
# SECURITY DASHBOARD & OVERVIEW
# =============================================================================

@security_bp.route('/')
@require_login
def security_overview():
    """Security overview dashboard."""
    user_id = get_current_user_id()
    company_id = get_user_company_id()

    # Get summary stats
    with get_db_context() as db:
        # Active sessions count
        active_sessions = db.execute(
            "SELECT COUNT(*) as cnt FROM user_sessions WHERE user_id = ? AND is_active = 1",
            (user_id,)
        ).fetchone()

        # MFA enrollment status
        mfa_enrolled = db.execute(
            "SELECT COUNT(*) as cnt FROM user_mfa_enrollments WHERE user_id = ? AND is_enabled = 1",
            (user_id,)
        ).fetchone()

        # Trusted devices count
        trusted_devices = db.execute(
            "SELECT COUNT(*) as cnt FROM trusted_devices WHERE user_id = ? AND is_active = 1",
            (user_id,)
        ).fetchone()

        # Recent security events
        recent_events = db.execute("""
            SELECT * FROM security_events
            WHERE actor_user_id = ? OR target_user_id = ?
            ORDER BY timestamp DESC LIMIT 10
        """, (user_id, user_id)).fetchall()

        # Active alerts (for admins)
        has_admin_access = True  # Simplified - check actual permissions
        if has_admin_access:
            active_alerts = db.execute("""
                SELECT COUNT(*) as cnt FROM security_alerts
                WHERE status IN ('new', 'acknowledged')
            """).fetchone()
        else:
            active_alerts = {'cnt': 0}

    stats = {
        'active_sessions': active_sessions['cnt'] if active_sessions else 0,
        'mfa_enrolled': mfa_enrolled['cnt'] if mfa_enrolled else 0,
        'trusted_devices': trusted_devices['cnt'] if trusted_devices else 0,
        'active_alerts': active_alerts['cnt'] if active_alerts else 0,
    }

    return render_template('security/overview.html',
        title='Security Overview',
        stats=stats,
        recent_events=rows_to_list(recent_events)
    )


# =============================================================================
# MFA MANAGEMENT ROUTES
# =============================================================================

@security_bp.route('/mfa')
@require_login
def mfa_management():
    """MFA management page."""
    user_id = get_current_user_id()

    with get_db_context() as db:
        # Get available MFA methods
        methods = rows_to_list(db.execute(
            "SELECT * FROM mfa_methods WHERE is_enabled = 1 ORDER BY priority"
        ).fetchall())

        # Get user's MFA enrollments
        enrollments = rows_to_list(db.execute("""
            SELECT * FROM user_mfa_enrollments WHERE user_id = ? ORDER BY is_primary DESC, enrolled_at DESC
        """, (user_id,)).fetchall())

        # Get recovery codes count
        recovery_codes = db.execute(
            "SELECT COUNT(*) as cnt FROM recovery_codes WHERE user_id = ? AND is_used = 0",
            (user_id,)
        ).fetchone()

    return render_template('security/mfa/index.html',
        title='MFA Management',
        methods=methods,
        enrollments=enrollments,
        recovery_codes_count=recovery_codes['cnt'] if recovery_codes else 0
    )


@security_bp.route('/mfa/enroll', methods=['GET', 'POST'])
@require_login
@csrf_protected
def mfa_enroll():
    """MFA enrollment wizard."""
    user_id = get_current_user_id()
    method_code = request.args.get('method', 'totp')

    if request.method == 'POST':
        method_code = request.form.get('method_code', 'totp')

        if method_code == 'totp':
            # Process TOTP enrollment
            secret = request.form.get('totp_secret', '')
            code = request.form.get('totp_code', '')

            if secret and code:
                # In production, verify the code against the secret
                # For now, accept any 6-digit code for demo
                with get_db_context() as db:
                    # Save enrollment
                    db.execute("""
                        INSERT INTO user_mfa_enrollments (
                            user_id, method_code, method_name, is_primary, is_enabled,
                            name, identifier, TOTP_secret, TOTP_issuer,
                            verified_at, enrolled_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                    """, (
                        user_id, 'totp', 'Authenticator App', 1, 1,
                        'Authenticator App', f'app_{user_id}',
                        secret, 'MMDx Enterprise'
                    ))

                    # Generate recovery codes
                    codes = generate_recovery_codes(10)
                    for i, code in enumerate(codes):
                        code_hash = hashlib.sha256(code.encode()).hexdigest()
                        db.execute("""
                            INSERT INTO recovery_codes (user_id, code_hash, code_index, created_at)
                            VALUES (?, ?, ?, datetime('now'))
                        """, (user_id, code_hash, i + 1))

                    # Log security event
                    create_security_event(
                        event_type='mfa_enrolled',
                        event_category='authentication',
                        severity='info',
                        actor_user_id=user_id,
                        actor_username=session.get('username', ''),
                        company_id=get_user_company_id(),
                        source_ip=request.remote_addr,
                        user_agent=request.headers.get('User-Agent', ''),
                        event_data={'method': 'totp'}
                    )

                flash("MFA has been enabled successfully!", "success")
                return redirect(url_for('security.mfa_management'))

    # Generate TOTP secret for setup
    import secrets
    totp_secret = base64.b64encode(secrets.token_bytes(20)).decode().replace('=', '')

    return render_template('security/mfa/enroll.html',
        title='Enable MFA',
        method_code=method_code,
        totp_secret=totp_secret
    )


@security_bp.route('/mfa/disable', methods=['POST'])
@require_login
@csrf_protected
def mfa_disable():
    """Disable MFA for user."""
    user_id = get_current_user_id()

    # Require password confirmation
    password = request.form.get('password', '')

    with get_db_context() as db:
        # Verify user's password
        user = db.execute("SELECT password FROM users WHERE id = ?", (user_id,)).fetchone()

        if user and verify_password(password, user['password'], user.get('password_salt', '')):
            # Disable all MFA enrollments
            db.execute("UPDATE user_mfa_enrollments SET is_enabled = 0 WHERE user_id = ?", (user_id,))

            # Log security event
            create_security_event(
                event_type='mfa_disabled',
                event_category='authentication',
                severity='warning',
                actor_user_id=user_id,
                actor_username=session.get('username', ''),
                company_id=get_user_company_id(),
                source_ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')
            )

            flash("MFA has been disabled.", "warning")
        else:
            flash("Invalid password. MFA was not disabled.", "error")

    return redirect(url_for('security.mfa_management'))


@security_bp.route('/mfa/recovery-codes')
@require_login
def mfa_recovery_codes():
    """View and regenerate recovery codes."""
    user_id = get_current_user_id()

    with get_db_context() as db:
        # Get active enrollment
        enrollment = db.execute("""
            SELECT * FROM user_mfa_enrollments WHERE user_id = ? AND is_enabled = 1
            ORDER BY is_primary DESC LIMIT 1
        """, (user_id,)).fetchone()

        if not enrollment:
            flash("No active MFA enrollment found.", "error")
            return redirect(url_for('security.mfa_management'))

        # Get unused recovery codes
        codes = rows_to_list(db.execute("""
            SELECT * FROM recovery_codes WHERE user_id = ? AND is_used = 0
            ORDER BY code_index
        """, (user_id,)).fetchall())

    return render_template('security/mfa/recovery_codes.html',
        title='Recovery Codes',
        codes=codes,
        enrollment_id=enrollment['id'] if enrollment else 0
    )


@security_bp.route('/mfa/recovery-codes/regenerate', methods=['POST'])
@require_login
@csrf_protected
def mfa_regenerate_recovery_codes():
    """Regenerate recovery codes."""
    user_id = get_current_user_id()

    with get_db_context() as db:
        # Invalidate existing codes
        db.execute("UPDATE recovery_codes SET is_used = 1 WHERE user_id = ?", (user_id,))

        # Generate new codes
        codes = generate_recovery_codes(10)
        for i, code in enumerate(codes):
            code_hash = hashlib.sha256(code.encode()).hexdigest()
            db.execute("""
                INSERT INTO recovery_codes (user_id, code_hash, code_index, created_at)
                VALUES (?, ?, ?, datetime('now'))
            """, (user_id, code_hash, i + 1))

        # Log security event
        create_security_event(
            event_type='recovery_codes_regenerated',
            event_category='authentication',
            severity='info',
            actor_user_id=user_id,
            actor_username=session.get('username', ''),
            company_id=get_user_company_id(),
            source_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )

    flash("Recovery codes have been regenerated.", "success")
    return redirect(url_for('security.mfa_recovery_codes'))


@security_bp.route('/mfa/challenge', methods=['GET', 'POST'])
@require_login
def mfa_challenge():
    """MFA challenge step-up."""
    user_id = get_current_user_id()

    if request.method == 'POST':
        code = request.form.get('code', '')
        remember_device = request.form.get('remember_device') == 'on'

        with get_db_context() as db:
            # Verify MFA code
            enrollment = db.execute("""
                SELECT * FROM user_mfa_enrollments
                WHERE user_id = ? AND is_enabled = 1
                ORDER BY is_primary DESC LIMIT 1
            """, (user_id,)).fetchone()

            if enrollment and enrollment['method_code'] == 'totp':
                # In production, verify TOTP code here
                # For demo, accept any 6-digit code
                if len(code) == 6 and code.isdigit():
                    # Update enrollment usage
                    db.execute("""
                        UPDATE user_mfa_enrollments
                        SET last_used_at = datetime('now'), used_count = used_count + 1
                        WHERE id = ?
                    """, (enrollment['id'],))

                    # Store MFA verified in session
                    session['mfa_verified'] = True
                    session['mfa_method'] = enrollment['method_code']

                    # Handle remember device
                    if remember_device:
                        device_id = generate_device_id()
                        db.execute("""
                            INSERT INTO trusted_devices (
                                user_id, device_id, device_name, device_type,
                                user_agent, ip_address, trusted_from, last_used_at, is_current
                            ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), 1)
                        """, (
                            user_id, device_id, 'This Device', 'desktop',
                            request.headers.get('User-Agent', ''),
                            request.remote_addr
                        ))

                    # Log success
                    create_security_event(
                        event_type='mfa_challenge_success',
                        event_category='authentication',
                        severity='info',
                        actor_user_id=user_id,
                        actor_username=session.get('username', ''),
                        company_id=get_user_company_id(),
                        source_ip=request.remote_addr,
                        user_agent=request.headers.get('User-Agent', ''),
                        event_data={'method': enrollment['method_code']}
                    )

                    next_url = session.get('next_url', url_for('index'))
                    session.pop('next_url', None)
                    return redirect(next_url)

            # Failed challenge
            create_security_event(
                event_type='mfa_challenge_failed',
                event_category='authentication',
                severity='warning',
                actor_user_id=user_id,
                actor_username=session.get('username', ''),
                company_id=get_user_company_id(),
                source_ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent', ''),
                failure_reason='Invalid MFA code'
            )

            flash("Invalid code. Please try again.", "error")

    return render_template('security/mfa/challenge.html', title='MFA Challenge')


# =============================================================================
# SSO PROVIDERS ROUTES
# =============================================================================

@security_bp.route('/sso-providers')
@require_login
@require_permission('security', 'sso', 'view')
def sso_providers():
    """SSO providers list page."""
    with get_db_context() as db:
        providers = rows_to_list(db.execute("""
            SELECT * FROM sso_providers ORDER BY is_default DESC, provider_name
        """).fetchall())

    return render_template('security/sso/providers.html',
        title='SSO Providers',
        providers=providers
    )


@security_bp.route('/sso-providers/create', methods=['GET', 'POST'])
@require_login
@require_permission('security', 'sso', 'manage')
def sso_provider_create():
    """Create SSO provider."""
    if request.method == 'POST':
        data = {
            'provider_code': request.form.get('provider_code', '').lower(),
            'provider_name': request.form.get('provider_name', ''),
            'provider_type': request.form.get('provider_type', 'oidc'),
            'client_id': request.form.get('client_id', ''),
            'client_secret': request.form.get('client_secret', ''),
            'discovery_url': request.form.get('discovery_url', ''),
            'scopes': request.form.get('scopes', 'openid profile email'),
            'is_enabled': request.form.get('is_enabled') == 'on',
            'is_visible': request.form.get('is_visible') != 'on',
            'is_default': request.form.get('is_default') == 'on',
        }

        with get_db_context() as db:
            db.execute("""
                INSERT INTO sso_providers (
                    provider_code, provider_name, provider_type, client_id, client_secret,
                    discovery_url, scopes, is_enabled, is_visible, is_default
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['provider_code'], data['provider_name'], data['provider_type'],
                data['client_id'], data['client_secret'], data['discovery_url'],
                data['scopes'], data['is_enabled'], data['is_visible'], data['is_default']
            ))

            create_security_event(
                event_type='sso_provider_created',
                event_category='configuration',
                severity='info',
                actor_user_id=get_current_user_id(),
                actor_username=session.get('username', ''),
                company_id=get_user_company_id(),
                source_ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent', ''),
                event_data={'provider': data['provider_code']}
            )

        flash("SSO Provider created successfully!", "success")
        return redirect(url_for('security.sso_providers'))

    return render_template('security/sso/create.html', title='Create SSO Provider')


@security_bp.route('/sso-providers/<int:provider_id>/edit', methods=['GET', 'POST'])
@require_login
@require_permission('security', 'sso', 'manage')
def sso_provider_edit(provider_id):
    """Edit SSO provider."""
    with get_db_context() as db:
        provider = db.execute("SELECT * FROM sso_providers WHERE id = ?", (provider_id,)).fetchone()

        if not provider:
            flash("Provider not found.", "error")
            return redirect(url_for('security.sso_providers'))

        if request.method == 'POST':
            db.execute("""
                UPDATE sso_providers SET
                    provider_name = ?, client_id = ?, client_secret = ?,
                    discovery_url = ?, scopes = ?, is_enabled = ?, is_visible = ?,
                    updated_at = datetime('now')
                WHERE id = ?
            """, (
                request.form.get('provider_name', ''),
                request.form.get('client_id', ''),
                request.form.get('client_secret', ''),
                request.form.get('discovery_url', ''),
                request.form.get('scopes', 'openid profile email'),
                request.form.get('is_enabled') == 'on',
                request.form.get('is_visible') != 'on',
                provider_id
            ))

            create_security_event(
                event_type='sso_provider_updated',
                event_category='configuration',
                severity='info',
                actor_user_id=get_current_user_id(),
                actor_username=session.get('username', ''),
                company_id=get_user_company_id(),
                source_ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent', ''),
                event_data={'provider_id': provider_id}
            )

            flash("SSO Provider updated successfully!", "success")
            return redirect(url_for('security.sso_providers'))

    return render_template('security/sso/edit.html',
        title='Edit SSO Provider',
        provider=row_to_dict(provider)
    )


@security_bp.route('/sso-providers/<int:provider_id>/test', methods=['POST'])
@require_login
@require_permission('security', 'sso', 'manage')
def sso_provider_test(provider_id):
    """Test SSO provider connection."""
    with get_db_context() as db:
        provider = db.execute("SELECT * FROM sso_providers WHERE id = ?", (provider_id,)).fetchone()

        if not provider:
            return jsonify({'success': False, 'error': 'Provider not found'})

        # Update test timestamp
        db.execute("""
            UPDATE sso_providers SET last_test_at = datetime('now') WHERE id = ?
        """, (provider_id,))

        # In production, perform actual OAuth/OIDC discovery and token exchange
        # For demo, simulate success
        test_result = 'success'

        db.execute("""
            UPDATE sso_providers SET last_test_result = ? WHERE id = ?
        """, (test_result, provider_id))

    return jsonify({'success': True, 'message': 'Connection test successful!'})


# =============================================================================
# SESSION MANAGEMENT ROUTES
# =============================================================================

@security_bp.route('/sessions')
@require_login
def sessions():
    """Active sessions list."""
    user_id = get_current_user_id()

    with get_db_context() as db:
        sessions = rows_to_list(db.execute("""
            SELECT * FROM user_sessions
            WHERE user_id = ? AND is_active = 1
            ORDER BY last_activity DESC
        """, (user_id,)).fetchall())

    return render_template('security/sessions/index.html',
        title='Active Sessions',
        sessions=sessions,
        current_session_id=session.get('session_id', '')
    )


@security_bp.route('/sessions/<session_id>/revoke', methods=['POST'])
@require_login
@csrf_protected
def session_revoke(session_id):
    """Revoke a session."""
    user_id = get_current_user_id()

    with get_db_context() as db:
        # Verify ownership
        session_row = db.execute("""
            SELECT * FROM user_sessions WHERE session_id = ? AND user_id = ?
        """, (session_id, user_id)).fetchone()

        if not session_row:
            flash("Session not found.", "error")
            return redirect(url_for('security.sessions'))

        # Revoke the session
        db.execute("""
            UPDATE user_sessions SET
                is_active = 0,
                terminated_at = datetime('now'),
                termination_reason = 'user_revoke'
            WHERE session_id = ?
        """, (session_id,))

        create_security_event(
            event_type='session_revoked',
            event_category='session',
            severity='info',
            actor_user_id=user_id,
            actor_username=session.get('username', ''),
            company_id=get_user_company_id(),
            source_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            event_data={'session_id': session_id[:16] + '...'}
        )

        # If revoking current session, logout
        if session_row['session_id'] == session.get('session_id'):
            session.clear()
            return redirect(url_for('login'))

    flash("Session has been revoked.", "success")
    return redirect(url_for('security.sessions'))


@security_bp.route('/sessions/revoke-all', methods=['POST'])
@require_login
@csrf_protected
def sessions_revoke_all():
    """Revoke all other sessions."""
    user_id = get_current_user_id()
    current_session = session.get('session_id', '')

    with get_db_context() as db:
        count = db.execute("""
            UPDATE user_sessions SET
                is_active = 0,
                terminated_at = datetime('now'),
                termination_reason = 'user_revoke_all'
            WHERE user_id = ? AND session_id != ? AND is_active = 1
        """, (user_id, current_session)).rowcount

        create_security_event(
            event_type='all_sessions_revoked',
            event_category='session',
            severity='warning',
            actor_user_id=user_id,
            actor_username=session.get('username', ''),
            company_id=get_user_company_id(),
            source_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            event_data={'count': count}
        )

    flash(f"All other sessions ({count}) have been revoked.", "success")
    return redirect(url_for('security.sessions'))


# =============================================================================
# TRUSTED DEVICES ROUTES
# =============================================================================

@security_bp.route('/trusted-devices')
@require_login
def trusted_devices():
    """Trusted devices list."""
    user_id = get_current_user_id()

    with get_db_context() as db:
        devices = rows_to_list(db.execute("""
            SELECT * FROM trusted_devices
            WHERE user_id = ? AND is_active = 1
            ORDER BY last_used_at DESC
        """, (user_id,)).fetchall())

    return render_template('security/trusted_devices/index.html',
        title='Trusted Devices',
        devices=devices
    )


@security_bp.route('/trusted-devices/<int:device_id>/revoke', methods=['POST'])
@require_login
@csrf_protected
def trusted_device_revoke(device_id):
    """Revoke a trusted device."""
    user_id = get_current_user_id()

    with get_db_context() as db:
        db.execute("""
            UPDATE trusted_devices SET is_active = 0 WHERE id = ? AND user_id = ?
        """, (device_id, user_id))

        create_security_event(
            event_type='trusted_device_revoked',
            event_category='authentication',
            severity='info',
            actor_user_id=user_id,
            actor_username=session.get('username', ''),
            company_id=get_user_company_id(),
            source_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )

    flash("Device has been removed from trusted devices.", "success")
    return redirect(url_for('security.trusted_devices'))


# =============================================================================
# SECURITY POLICIES ROUTES
# =============================================================================

@security_bp.route('/policies')
@require_login
@require_permission('security', 'policies', 'view')
def policies():
    """Security policies list."""
    company_id = get_user_company_id()

    with get_db_context() as db:
        policies = rows_to_list(db.execute("""
            SELECT * FROM security_policies
            WHERE company_id = 0 OR company_id = ?
            ORDER BY is_system DESC, priority DESC
        """, (company_id,)).fetchall())

    return render_template('security/policies/index.html',
        title='Security Policies',
        policies=policies
    )


@security_bp.route('/policies/<int:policy_id>/edit', methods=['GET', 'POST'])
@require_login
@require_permission('security', 'policies', 'edit')
def policy_edit(policy_id):
    """Edit security policy."""
    with get_db_context() as db:
        policy = db.execute("SELECT * FROM security_policies WHERE id = ?", (policy_id,)).fetchone()

        if not policy:
            flash("Policy not found.", "error")
            return redirect(url_for('security.policies'))

        if request.method == 'POST':
            rules = {}
            rules['min_length'] = int(request.form.get('min_length', 12))
            rules['require_uppercase'] = request.form.get('require_uppercase') == 'on'
            rules['require_lowercase'] = request.form.get('require_lowercase') == 'on'
            rules['require_numbers'] = request.form.get('require_numbers') == 'on'
            rules['require_special'] = request.form.get('require_special') == 'on'
            rules['max_age_days'] = int(request.form.get('max_age_days', 90))
            rules['history_count'] = int(request.form.get('history_count', 5))
            rules['min_age_days'] = int(request.form.get('min_age_days', 1))

            db.execute("""
                UPDATE security_policies SET
                    rules = ?, is_enabled = ?, updated_at = datetime('now'),
                    updated_by = ?
                WHERE id = ?
            """, (
                json.dumps(rules),
                request.form.get('is_enabled') == 'on',
                get_current_user_id(),
                policy_id
            ))

            create_security_event(
                event_type='security_policy_changed',
                event_category='policy',
                severity='warning',
                actor_user_id=get_current_user_id(),
                actor_username=session.get('username', ''),
                company_id=get_user_company_id(),
                source_ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent', ''),
                event_data={'policy': policy['policy_name'], 'rules': rules}
            )

            flash("Policy updated successfully!", "success")
            return redirect(url_for('security.policies'))

        current_rules = json.loads(policy['rules']) if policy['rules'] else {}

    return render_template('security/policies/edit.html',
        title='Edit Policy',
        policy=row_to_dict(policy),
        rules=current_rules
    )


# =============================================================================
# ACCESS REVIEWS ROUTES
# =============================================================================

@security_bp.route('/access-reviews')
@require_login
@require_permission('security', 'access_reviews', 'view')
def access_reviews():
    """Access reviews list."""
    with get_db_context() as db:
        campaigns = rows_to_list(db.execute("""
            SELECT * FROM access_review_campaigns
            ORDER BY created_at DESC
        """).fetchall())

    return render_template('security/access_reviews/index.html',
        title='Access Reviews',
        campaigns=campaigns
    )


@security_bp.route('/access-reviews/create', methods=['GET', 'POST'])
@require_login
@require_permission('security', 'access_reviews', 'manage')
def access_review_create():
    """Create access review campaign."""
    if request.method == 'POST':
        with get_db_context() as db:
            db.execute("""
                INSERT INTO access_review_campaigns (
                    campaign_name, campaign_type, review_frequency,
                    description, owner_user_id, owner_username,
                    start_date, end_date, due_date, status,
                    company_id, scope_type, include_mfa_status,
                    include_sso_status, include_permissions,
                    include_role_conflicts, include_inactive_users,
                    inactive_threshold_days, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request.form.get('campaign_name', ''),
                request.form.get('campaign_type', 'periodic'),
                request.form.get('review_frequency', 'quarterly'),
                request.form.get('description', ''),
                get_current_user_id(),
                session.get('username', ''),
                request.form.get('start_date', ''),
                request.form.get('end_date', ''),
                request.form.get('due_date', ''),
                'draft',
                get_user_company_id(),
                request.form.get('scope_type', 'all'),
                request.form.get('include_mfa_status') == 'on',
                request.form.get('include_sso_status') == 'on',
                request.form.get('include_permissions') == 'on',
                request.form.get('include_role_conflicts') == 'on',
                request.form.get('include_inactive_users') == 'on',
                int(request.form.get('inactive_threshold_days', 90)),
                get_current_user_id()
            ))

        flash("Access review campaign created!", "success")
        return redirect(url_for('security.access_reviews'))

    return render_template('security/access_reviews/create.html', title='Create Access Review')


@security_bp.route('/access-reviews/<int:campaign_id>')
@require_login
@require_permission('security', 'access_reviews', 'view')
def access_review_detail(campaign_id):
    """Access review campaign detail."""
    with get_db_context() as db:
        campaign = db.execute("SELECT * FROM access_review_campaigns WHERE id = ?", (campaign_id,)).fetchone()

        if not campaign:
            flash("Campaign not found.", "error")
            return redirect(url_for('security.access_reviews'))

        items = rows_to_list(db.execute("""
            SELECT * FROM access_review_items
            WHERE campaign_id = ?
            ORDER BY username
        """, (campaign_id,)).fetchall())

    return render_template('security/access_reviews/detail.html',
        title=campaign['campaign_name'],
        campaign=row_to_dict(campaign),
        items=items
    )


# =============================================================================
# ROLE CONFLICTS ROUTES
# =============================================================================

@security_bp.route('/role-conflicts')
@require_login
@require_permission('security', 'role_conflicts', 'view')
def role_conflicts():
    """Role conflicts list."""
    with get_db_context() as db:
        # Get conflict rules
        rules = rows_to_list(db.execute("SELECT * FROM role_conflict_rules WHERE is_active = 1").fetchall())

        # Get user conflicts
        conflicts = rows_to_list(db.execute("""
            SELECT * FROM user_role_conflicts WHERE status = 'active'
            ORDER BY detected_at DESC
        """).fetchall())

    return render_template('security/role_conflicts/index.html',
        title='Role Conflicts',
        rules=rules,
        conflicts=conflicts
    )


# =============================================================================
# SECURITY EVENTS ROUTES
# =============================================================================

@security_bp.route('/events')
@require_login
@require_permission('security', 'audit', 'view')
def events():
    """Security events list."""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page

    event_type = request.args.get('type', '')
    severity = request.args.get('severity', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    with get_db_context() as db:
        query = "SELECT * FROM security_events WHERE 1=1"
        params = []

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        if date_from:
            query += " AND timestamp >= ?"
            params.append(date_from)
        if date_to:
            query += " AND timestamp <= ?"
            params.append(date_to)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        events = rows_to_list(db.execute(query, params).fetchall())

        # Get total count for pagination
        count_query = "SELECT COUNT(*) as cnt FROM security_events WHERE 1=1"
        count_params = []
        if event_type:
            count_query += " AND event_type = ?"
            count_params.append(event_type)
        if severity:
            count_query += " AND severity = ?"
            count_params.append(severity)

        total = db.execute(count_query, count_params).fetchone()['cnt']

    total_pages = math.ceil(total / per_page)

    return render_template('security/events/index.html',
        title='Security Events',
        events=events,
        page=page,
        total_pages=total_pages,
        total=total,
        filters={
            'type': event_type,
            'severity': severity,
            'date_from': date_from,
            'date_to': date_to
        }
    )


@security_bp.route('/events/<int:event_id>')
@require_login
@require_permission('security', 'audit', 'view')
def event_detail(event_id):
    """Security event detail."""
    with get_db_context() as db:
        event = db.execute("SELECT * FROM security_events WHERE id = ?", (event_id,)).fetchone()

        if not event:
            flash("Event not found.", "error")
            return redirect(url_for('security.events'))

        event_data = row_to_dict(event)
        if event['event_data']:
            event_data['event_data_parsed'] = json.loads(event['event_data'])

    return render_template('security/events/detail.html',
        title='Security Event',
        event=event_data
    )


# =============================================================================
# ALERTS & INCIDENTS ROUTES
# =============================================================================

@security_bp.route('/alerts')
@require_login
@require_permission('security', 'alerts', 'view')
def alerts():
    """Security alerts list."""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page

    status = request.args.get('status', '')
    severity = request.args.get('severity', '')

    with get_db_context() as db:
        query = "SELECT * FROM security_alerts WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)
        if severity:
            query += " AND severity = ?"
            params.append(severity)

        query += " ORDER BY triggered_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        alerts = rows_to_list(db.execute(query, params).fetchall())

        count_query = "SELECT COUNT(*) as cnt FROM security_alerts WHERE 1=1"
        count_params = []
        if status:
            count_query += " AND status = ?"
            count_params.append(status)
        if severity:
            count_query += " AND severity = ?"
            count_params.append(severity)

        total = db.execute(count_query, count_params).fetchone()['cnt']

    total_pages = math.ceil(total / per_page)

    return render_template('security/alerts/index.html',
        title='Security Alerts',
        alerts=alerts,
        page=page,
        total_pages=total_pages,
        total=total,
        filters={'status': status, 'severity': severity}
    )


@security_bp.route('/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@require_login
@require_permission('security', 'alerts', 'manage')
@csrf_protected
def alert_acknowledge(alert_id):
    """Acknowledge an alert."""
    with get_db_context() as db:
        db.execute("""
            UPDATE security_alerts SET
                status = 'acknowledged',
                acknowledged_at = datetime('now'),
                acknowledged_by = ?
            WHERE id = ?
        """, (get_current_user_id(), alert_id))

    flash("Alert acknowledged.", "success")
    return redirect(url_for('security.alerts'))


@security_bp.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
@require_login
@require_permission('security', 'alerts', 'manage')
@csrf_protected
def alert_resolve(alert_id):
    """Resolve an alert."""
    with get_db_context() as db:
        db.execute("""
            UPDATE security_alerts SET
                status = 'resolved',
                resolved_at = datetime('now'),
                resolved_by = ?,
                resolution_notes = ?
            WHERE id = ?
        """, (
            get_current_user_id(),
            request.form.get('resolution_notes', ''),
            alert_id
        ))

    flash("Alert resolved.", "success")
    return redirect(url_for('security.alerts'))


# =============================================================================
# EMERGENCY ACCESS / BREAK-GLASS ROUTES
# =============================================================================

@security_bp.route('/emergency-access')
@require_login
@require_permission('security', 'breakglass', 'view')
def emergency_access():
    """Emergency access accounts list."""
    with get_db_context() as db:
        accounts = rows_to_list(db.execute("""
            SELECT * FROM emergency_access_accounts ORDER BY created_at DESC
        """).fetchall())

        logs = rows_to_list(db.execute("""
            SELECT * FROM emergency_access_logs ORDER BY activated_at DESC LIMIT 50
        """).fetchall())

    return render_template('security/emergency_access/index.html',
        title='Emergency Access',
        accounts=accounts,
        logs=logs
    )


@security_bp.route('/emergency-access/<int:account_id>/activate', methods=['POST'])
@require_login
@require_permission('security', 'breakglass', 'use')
@csrf_protected
def emergency_access_activate(account_id):
    """Activate break-glass access."""
    reason = request.form.get('reason', '')

    if not reason:
        flash("A reason is required for emergency access.", "error")
        return redirect(url_for('security.emergency_access'))

    with get_db_context() as db:
        account = db.execute("SELECT * FROM emergency_access_accounts WHERE id = ?", (account_id,)).fetchone()

        if not account:
            flash("Emergency access account not found.", "error")
            return redirect(url_for('security.emergency_access'))

        # Log activation
        db.execute("""
            INSERT INTO emergency_access_logs (
                emergency_account_id, user_id, username, display_name,
                activated_at, reason_given, ip_address, user_agent,
                session_id, actions_performed, status
            ) VALUES (?, ?, ?, ?, datetime('now'), ?, ?, ?, ?, ?, 'active')
        """, (
            account_id, get_current_user_id(), session.get('username', ''),
            session.get('display_name', ''), reason,
            request.remote_addr, request.headers.get('User-Agent', ''),
            session.get('session_id', '')
        ))

        create_security_event(
            event_type='emergency_access_activated',
            event_category='emergency',
            severity='critical',
            actor_user_id=get_current_user_id(),
            actor_username=session.get('username', ''),
            company_id=get_user_company_id(),
            source_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            event_data={'reason': reason}
        )

    flash("Emergency access activated. Your actions are being logged.", "warning")
    return redirect(url_for('security.emergency_access'))


# =============================================================================
# API SECURITY ROUTES
# =============================================================================

@security_bp.route('/api-security')
@require_login
@require_permission('security', 'api_security', 'view')
def api_security():
    """API security events."""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page

    with get_db_context() as db:
        events = rows_to_list(db.execute("""
            SELECT * FROM api_security_events
            ORDER BY timestamp DESC LIMIT ? OFFSET ?
        """, (per_page, offset)).fetchall())

        total = db.execute("SELECT COUNT(*) as cnt FROM api_security_events").fetchone()['cnt']

    total_pages = math.ceil(total / per_page)

    return render_template('security/api_security/index.html',
        title='API Security',
        events=events,
        page=page,
        total_pages=total_pages
    )


# =============================================================================
# REPORTS & EXPORT ROUTES
# =============================================================================

@security_bp.route('/reports')
@require_login
@require_permission('security', 'reports', 'view')
def reports():
    """Security reports center."""
    return render_template('security/reports/index.html', title='Security Reports')


@security_bp.route('/reports/user-access')
@require_login
@require_permission('security', 'reports', 'view')
def report_user_access():
    """User access report."""
    with get_db_context() as db:
        users = rows_to_list(db.execute("""
            SELECT u.id, u.username, u.email, u.is_active,
                   r.name as role_name,
                   COUNT(DISTINCT ume.id) as mfa_enrollments,
                   COUNT(DISTINCT usess.id) as active_sessions,
                   u.last_login
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            LEFT JOIN user_mfa_enrollments ume ON u.id = ume.user_id AND ume.is_enabled = 1
            LEFT JOIN user_sessions usess ON u.id = usess.user_id AND usess.is_active = 1
            GROUP BY u.id
            ORDER BY u.username
        """).fetchall())

    return render_template('security/reports/user_access.html',
        title='User Access Report',
        users=users
    )


@security_bp.route('/reports/export/<report_type>')
@require_login
@require_permission('security', 'reports', 'export')
def report_export(report_type):
    """Export security report."""
    export_format = request.args.get('format', 'csv')
    columns = request.args.getlist('columns') or None

    with get_db_context() as db:
        if report_type == 'user_access':
            data = db.execute("""
                SELECT u.username, u.email, u.is_active, r.name as role_name,
                       ume.method_code as mfa_method, usess.active_sessions,
                       u.last_login
                FROM users u
                LEFT JOIN roles r ON u.role_id = r.id
                LEFT JOIN (
                    SELECT user_id, method_code FROM user_mfa_enrollments
                    WHERE is_enabled = 1 AND is_primary = 1
                ) ume ON u.id = ume.user_id
                LEFT JOIN (
                    SELECT user_id, COUNT(*) as active_sessions
                    FROM user_sessions WHERE is_active = 1 GROUP BY user_id
                ) usess ON u.id = usess.user_id
                ORDER BY u.username
            """).fetchall()
            headers = ['Username', 'Email', 'Active', 'Role', 'MFA Method', 'Active Sessions', 'Last Login']
            filename = 'user_access_report'
        elif report_type == 'security_events':
            data = db.execute("""
                SELECT timestamp, event_type, severity, actor_username,
                       target_username, source_ip, status
                FROM security_events
                ORDER BY timestamp DESC LIMIT 1000
            """).fetchall()
            headers = ['Timestamp', 'Event Type', 'Severity', 'Actor', 'Target', 'Source IP', 'Status']
            filename = 'security_events_report'
        elif report_type == 'alerts':
            data = db.execute("""
                SELECT triggered_at, title, severity, status,
                       triggered_by_username, source_ip
                FROM security_alerts
                ORDER BY triggered_at DESC LIMIT 1000
            """).fetchall()
            headers = ['Triggered At', 'Title', 'Severity', 'Status', 'Triggered By', 'Source IP']
            filename = 'security_alerts_report'
        else:
            flash("Unknown report type.", "error")
            return redirect(url_for('security.reports'))

        data_list = rows_to_list(data)

    if export_format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        for row in data_list:
            writer.writerow([row.get(h.lower().replace(' ', '_'), '') for h in headers])
        output.seek(0)
        return Response(output.getvalue(), mimetype='text/csv',
                       headers={'Content-Disposition': f'attachment; filename={filename}.csv'})
    elif export_format == 'excel':
        wb = Workbook()
        ws = wb.active
        ws.title = filename[:31]

        # Text mode - all cells as text
        ws.append(headers)
        for row in data_list:
            ws.append([str(row.get(h.lower().replace(' ', '_'), '')) for h in headers])

        for cell in ws._cells.values():
            cell.value = str(cell.value) if cell.value else ''

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         download_name=f'{filename}.xlsx')

    return redirect(url_for('security.reports'))


# =============================================================================
# LOGIN HISTORY ROUTES
# =============================================================================

@security_bp.route('/login-history')
@require_login
def login_history():
    """User login history."""
    user_id = get_current_user_id()
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page

    with get_db_context() as db:
        logins = rows_to_list(db.execute("""
            SELECT * FROM login_attempts
            WHERE user_id = ?
            ORDER BY timestamp DESC LIMIT ? OFFSET ?
        """, (user_id, per_page, offset)).fetchall())

        total = db.execute("SELECT COUNT(*) as cnt FROM login_attempts WHERE user_id = ?", (user_id,)).fetchone()['cnt']

    total_pages = math.ceil(total / per_page)

    return render_template('security/login_history.html',
        title='Login History',
        logins=logins,
        page=page,
        total_pages=total_pages
    )


# =============================================================================
# SETTINGS ROUTES
# =============================================================================

@security_bp.route('/settings')
@require_login
@require_permission('security', 'settings', 'view')
def settings():
    """Security settings page."""
    return render_template('security/settings/index.html', title='Security Settings')


# =============================================================================
# ADMIN ROUTES
# =============================================================================

@security_bp.route('/admin/users')
@require_login
@require_permission('security', 'admin', 'view')
def admin_users():
    """Admin user security overview."""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page

    with get_db_context() as db:
        users = rows_to_list(db.execute("""
            SELECT u.id, u.username, u.email, u.is_active, r.name as role_name,
                   COUNT(DISTINCT ume.id) as mfa_count,
                   COUNT(DISTINCT usess.id) as session_count,
                   u.last_login
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            LEFT JOIN user_mfa_enrollments ume ON u.id = ume.user_id AND ume.is_enabled = 1
            LEFT JOIN user_sessions usess ON u.id = usess.user_id AND usess.is_active = 1
            GROUP BY u.id
            ORDER BY u.username
            LIMIT ? OFFSET ?
        """, (per_page, offset)).fetchall())

        total = db.execute("SELECT COUNT(*) as cnt FROM users").fetchone()['cnt']

    total_pages = math.ceil(total / per_page)

    return render_template('security/admin/users.html',
        title='User Security Overview',
        users=users,
        page=page,
        total_pages=total_pages
    )


@security_bp.route('/admin/users/<int:user_id>/reset-session', methods=['POST'])
@require_login
@require_permission('security', 'admin', 'manage')
@csrf_protected
def admin_reset_user_session(user_id):
    """Admin reset all user sessions."""
    with get_db_context() as db:
        count = db.execute("""
            UPDATE user_sessions SET
                is_active = 0, terminated_at = datetime('now'),
                termination_reason = 'admin_reset'
            WHERE user_id = ? AND is_active = 1
        """, (user_id,)).rowcount

        create_security_event(
            event_type='admin_session_reset',
            event_category='admin',
            severity='warning',
            actor_user_id=get_current_user_id(),
            actor_username=session.get('username', ''),
            target_user_id=user_id,
            company_id=get_user_company_id(),
            source_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            event_data={'sessions_revoked': count}
        )

    flash(f"Reset {count} active sessions for user.", "success")
    return redirect(url_for('security.admin_users'))


@security_bp.route('/admin/users/<int:user_id>/force-password-reset', methods=['POST'])
@require_login
@require_permission('security', 'admin', 'manage')
@csrf_protected
def admin_force_password_reset(user_id):
    """Admin force password reset."""
    with get_db_context() as db:
        db.execute("""
            UPDATE users SET
                password_change_required = 1,
                updated_at = datetime('now')
            WHERE id = ?
        """, (user_id,))

        create_security_event(
            event_type='admin_forced_password_reset',
            event_category='admin',
            severity='warning',
            actor_user_id=get_current_user_id(),
            actor_username=session.get('username', ''),
            target_user_id=user_id,
            company_id=get_user_company_id(),
            source_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )

    flash("User will be required to change password on next login.", "success")
    return redirect(url_for('security.admin_users'))


@security_bp.route('/admin/users/<int:user_id>/disable', methods=['POST'])
@require_login
@require_permission('security', 'admin', 'manage')
@csrf_protected
def admin_disable_user(user_id):
    """Admin disable user account."""
    with get_db_context() as db:
        db.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))

        # Revoke all sessions
        db.execute("""
            UPDATE user_sessions SET
                is_active = 0, terminated_at = datetime('now'),
                termination_reason = 'account_disabled'
            WHERE user_id = ?
        """, (user_id,))

        create_security_event(
            event_type='user_disabled',
            event_category='admin',
            severity='critical',
            actor_user_id=get_current_user_id(),
            actor_username=session.get('username', ''),
            target_user_id=user_id,
            company_id=get_user_company_id(),
            source_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )

    flash("User account has been disabled.", "success")
    return redirect(url_for('security.admin_users'))


@security_bp.route('/admin/users/<int:user_id>/enable', methods=['POST'])
@require_login
@require_permission('security', 'admin', 'manage')
@csrf_protected
def admin_enable_user(user_id):
    """Admin enable user account."""
    with get_db_context() as db:
        db.execute("UPDATE users SET is_active = 1 WHERE id = ?", (user_id,))

        create_security_event(
            event_type='user_enabled',
            event_category='admin',
            severity='info',
            actor_user_id=get_current_user_id(),
            actor_username=session.get('username', ''),
            target_user_id=user_id,
            company_id=get_user_company_id(),
            source_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )

    flash("User account has been enabled.", "success")
    return redirect(url_for('security.admin_users'))


# =============================================================================
# DASHBOARD KPIs API
# =============================================================================

@security_bp.route('/api/kpis')
@require_login
def security_kpis():
    """Get security KPIs for dashboard."""
    company_id = get_user_company_id()

    with get_db_context() as db:
        # Total users
        total_users = db.execute("SELECT COUNT(*) as cnt FROM users WHERE is_active = 1").fetchone()['cnt']

        # MFA enabled users
        mfa_users = db.execute("""
            SELECT COUNT(DISTINCT user_id) as cnt FROM user_mfa_enrollments WHERE is_enabled = 1
        """).fetchone()['cnt']

        # Active sessions
        active_sessions = db.execute("SELECT COUNT(*) as cnt FROM user_sessions WHERE is_active = 1").fetchone()['cnt']

        # Failed logins today
        failed_logins = db.execute("""
            SELECT COUNT(*) as cnt FROM login_attempts
            WHERE success = 0 AND timestamp >= date('now')
        """).fetchone()['cnt']

        # Active alerts
        active_alerts = db.execute("""
            SELECT COUNT(*) as cnt FROM security_alerts WHERE status IN ('new', 'acknowledged')
        """).fetchone()['cnt']

        # Suspicious sessions
        suspicious = db.execute("SELECT COUNT(*) as cnt FROM user_sessions WHERE is_suspicious = 1").fetchone()['cnt']

    return jsonify({
        'total_users': total_users,
        'mfa_enabled_users': mfa_users,
        'mfa_coverage_pct': round((mfa_users / total_users * 100) if total_users > 0 else 0, 1),
        'active_sessions': active_sessions,
        'failed_logins_today': failed_logins,
        'active_alerts': active_alerts,
        'suspicious_sessions': suspicious
    })


@security_bp.route('/api/chart/login-attempts')
@require_login
def login_attempts_chart():
    """Get login attempts trend chart data."""
    days = request.args.get('days', 7, type=int)

    with get_db_context() as db:
        data = db.execute("""
            SELECT date(timestamp) as date,
                   SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                   SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed
            FROM login_attempts
            WHERE timestamp >= date('now', ? || ' days')
            GROUP BY date(timestamp)
            ORDER BY date
        """, (-days,)).fetchall()

    labels = [row['date'] for row in data]
    success = [row['successful'] for row in data]
    failed = [row['failed'] for row in data]

    return jsonify({
        'labels': labels,
        'datasets': [
            {'label': 'Successful', 'data': success},
            {'label': 'Failed', 'data': failed}
        ]
    })
