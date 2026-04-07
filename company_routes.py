"""
Multi-Company Management Routes
==============================
Flask routes for multi-company management functionality.

Routes:
- /company/dashboard - Company management dashboard
- /company/list - List all companies
- /company/create - Create new company
- /company/<id> - View/edit company
- /company/<id>/branches - Manage company branches
- /company/<id>/facilities - Manage company facilities
- /company/<id>/settings - Company settings
- /company/<id>/users - User-company access
- /company/<id>/relationships - Company relationships
- /company/<id>/numbering - Numbering rules
- /company/<id>/policies - Company policies
- /company/<id>/audit - Company audit log
- /company/<id>/hierarchy - Company hierarchy view
- /intercompany/workflows - Intercompany workflows
- /intercompany/transactions - Intercompany transactions
- /shared-data/rules - Shared data governance
- /api/company-context - API: Get current company context
- /api/company-switch - API: Switch active company
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
import json

# Import database and utility functions
from database import get_db, get_db_context, get_one, get_all, log_audit
from permissions import require_permission, get_user_permissions
from company_models import (
    # Company CRUD
    get_all_companies, get_company_by_id, create_company, update_company,
    # Branch operations
    get_company_branches, get_branch_by_id, create_branch, update_branch,
    # Facility operations
    get_company_facilities, get_facility_by_id, create_facility,
    # User access
    get_user_companies, get_user_default_company, assign_user_to_company,
    update_user_company_access, revoke_user_company_access,
    user_has_company_access, user_can_access_company_data,
    # Settings
    get_company_settings, get_company_setting, update_company_setting,
    # Numbering
    get_numbering_rules, get_next_document_number,
    # Relationships
    get_company_relationships, create_company_relationship,
    # Policies
    get_company_policies, get_policy_value,
    # Workflows
    get_intercompany_workflows, get_intercompany_transactions,
    create_intercompany_transaction, update_transaction_status,
    # Audit
    get_company_audit_log, log_company_audit,
    # Shared data
    get_shared_data_rules, get_data_visibility,
    # Dashboard
    get_company_dashboard_stats, get_company_hierarchy,
    run_company_migrations
)


# Create blueprint
company_bp = Blueprint('company', __name__, url_prefix='/company')


# =============================================================================
# DECORATORS AND HELPERS
# =============================================================================

def require_company_access(f):
    """Decorator to require company access for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        company_id = kwargs.get('company_id')

        if not company_id:
            return f(*args, **kwargs)

        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))

        # Check if user has access to this company
        if not user_has_company_access(user_id, company_id):
            # Check if user is super admin
            permissions = get_user_permissions(user_id)
            if 'platform.settings.manage' not in permissions:
                flash('You do not have access to this company.', 'danger')
                return redirect(url_for('company.company_list'))

        return f(*args, **kwargs)
    return decorated_function


def set_company_context(company_id):
    """Set the current company context in session."""
    if company_id:
        session['current_company_id'] = company_id
        company = get_company_by_id(company_id)
        if company:
            session['current_company_name'] = company.get('name', '')


def get_current_company_id():
    """Get the current company ID from session or default."""
    user_id = session.get('user_id')
    company_id = session.get('current_company_id')

    if not company_id and user_id:
        # Try to get user's default company
        default = get_user_default_company(user_id)
        if default:
            company_id = default['id']
            set_company_context(company_id)

    return company_id


def require_platform_admin(f):
    """Decorator to require platform admin permissions."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))

        permissions = get_user_permissions(user_id)
        if 'platform.settings.manage' not in permissions:
            flash('Platform admin access required.', 'danger')
            return redirect(url_for('index'))

        return f(*args, **kwargs)
    return decorated_function


# =============================================================================
# COMPANY DASHBOARD
# =============================================================================

@company_bp.route('/dashboard')
@require_permission('platform', 'settings', 'view')
def company_dashboard():
    """Company management dashboard."""
    stats = get_company_dashboard_stats()
    recent_audit = get_company_audit_log(company_id=None, limit=20) if stats else []

    return render_template('company/dashboard.html',
        page_title='Company Dashboard',
        stats=stats,
        recent_audit=recent_audit
    )


# =============================================================================
# COMPANY LIST AND CRUD
# =============================================================================

@company_bp.route('/')
@company_bp.route('/list')
@require_permission('platform', 'settings', 'view')
def company_list():
    """List all companies."""
    companies = get_all_companies(active_only=True)
    return render_template('company/list.html',
        page_title='Companies',
        companies=companies
    )


@company_bp.route('/create', methods=['GET', 'POST'])
@require_permission('platform', 'settings', 'manage')
def company_create():
    """Create a new company."""
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'trade_name': request.form.get('trade_name'),
            'short_name': request.form.get('short_name'),
            'company_type': request.form.get('company_type', 'subsidiary'),
            'company_type_detail': request.form.get('company_type_detail'),
            'registration_number': request.form.get('registration_number'),
            'tax_id': request.form.get('tax_id'),
            'vat_number': request.form.get('vat_number'),
            'license_number': request.form.get('license_number'),
            'main_currency': request.form.get('main_currency', 'AED'),
            'timezone': request.form.get('timezone', 'Asia/Dubai'),
            'date_format': request.form.get('date_format', 'DD/MM/YYYY'),
            'default_language': request.form.get('default_language', 'en'),
            'address_line1': request.form.get('address_line1'),
            'city': request.form.get('city'),
            'country': request.form.get('country'),
            'phone': request.form.get('phone'),
            'email': request.form.get('email'),
            'parent_company_id': request.form.get('parent_company_id') or None,
            'notes': request.form.get('notes')
        }

        try:
            company_id = create_company(data)
            log_audit('company', company_id, 'CREATE', session.get('user_id'),
                     notes=f'Created company: {data["name"]}')
            flash(f'Company "{data["name"]}" created successfully.', 'success')
            return redirect(url_for('company.company_detail', company_id=company_id))
        except Exception as e:
            flash(f'Error creating company: {str(e)}', 'danger')

    # Get existing companies for parent selection
    companies = get_all_companies(active_only=True)
    return render_template('company/create.html',
        page_title='Create Company',
        companies=companies
    )


@company_bp.route('/<int:company_id>')
@require_company_access
def company_detail(company_id):
    """View company details."""
    company = get_company_by_id(company_id)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('company.company_list'))

    branches = get_company_branches(company_id)
    facilities = get_company_facilities(company_id)
    relationships = get_company_relationships(company_id)
    settings = get_company_settings(company_id)
    policies = get_company_policies(company_id)

    return render_template('company/detail.html',
        page_title=f'{company.get("name", "Company")}',
        company=company,
        branches=branches,
        facilities=facilities,
        relationships=relationships,
        settings=settings,
        policies=policies
    )


@company_bp.route('/<int:company_id>/edit', methods=['GET', 'POST'])
@require_company_access
def company_edit(company_id):
    """Edit company details."""
    company = get_company_by_id(company_id)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('company.company_list'))

    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'trade_name': request.form.get('trade_name'),
            'short_name': request.form.get('short_name'),
            'company_type': request.form.get('company_type'),
            'company_type_detail': request.form.get('company_type_detail'),
            'registration_number': request.form.get('registration_number'),
            'tax_id': request.form.get('tax_id'),
            'vat_number': request.form.get('vat_number'),
            'license_number': request.form.get('license_number'),
            'main_currency': request.form.get('main_currency'),
            'timezone': request.form.get('timezone'),
            'date_format': request.form.get('date_format'),
            'default_language': request.form.get('default_language'),
            'address_line1': request.form.get('address_line1'),
            'address_line2': request.form.get('address_line2'),
            'city': request.form.get('city'),
            'country': request.form.get('country'),
            'postal_code': request.form.get('postal_code'),
            'phone': request.form.get('phone'),
            'mobile': request.form.get('mobile'),
            'email': request.form.get('email'),
            'website': request.form.get('website'),
            'contact_person': request.form.get('contact_person'),
            'parent_company_id': request.form.get('parent_company_id') or None,
            'is_parent': 1 if request.form.get('is_parent') else 0,
            'is_active': 1 if request.form.get('is_active') else 0,
            'notes': request.form.get('notes')
        }

        try:
            update_company(company_id, data)
            log_company_audit(company_id, 'company', company_id, company['name'],
                            'UPDATE', session.get('user_id'),
                            notes=f'Updated company: {data["name"]}')
            flash('Company updated successfully.', 'success')
            return redirect(url_for('company.company_detail', company_id=company_id))
        except Exception as e:
            flash(f'Error updating company: {str(e)}', 'danger')

    companies = get_all_companies(active_only=True)
    return render_template('company/edit.html',
        page_title=f'Edit {company.get("name", "Company")}',
        company=company,
        companies=[c for c in companies if c['id'] != company_id]
    )


# =============================================================================
# BRANCH MANAGEMENT
# =============================================================================

@company_bp.route('/<int:company_id>/branches')
@require_company_access
def company_branches(company_id):
    """List company branches."""
    company = get_company_by_id(company_id)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('company.company_list'))

    branches = get_company_branches(company_id)

    return render_template('company/branches.html',
        page_title=f'{company.get("name", "Company")} - Branches',
        company=company,
        branches=branches
    )


@company_bp.route('/<int:company_id>/branches/create', methods=['GET', 'POST'])
@require_company_access
def branch_create(company_id):
    """Create a new branch."""
    company = get_company_by_id(company_id)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('company.company_list'))

    if request.method == 'POST':
        data = {
            'company_id': company_id,
            'branch_code': request.form.get('branch_code'),
            'branch_name': request.form.get('branch_name'),
            'branch_type': request.form.get('branch_type', 'branch'),
            'description': request.form.get('description'),
            'address': request.form.get('address'),
            'city': request.form.get('city'),
            'country': request.form.get('country'),
            'postal_code': request.form.get('postal_code'),
            'phone': request.form.get('phone'),
            'email': request.form.get('email'),
            'manager_name': request.form.get('manager_name'),
            'manager_contact': request.form.get('manager_contact'),
            'is_active': 1 if request.form.get('is_active') else 0,
            'is_operational': 1 if request.form.get('is_operational') else 0,
            'notes': request.form.get('notes')
        }

        try:
            branch_id = create_branch(data)
            log_company_audit(company_id, 'branch', branch_id, data['branch_name'],
                            'CREATE', session.get('user_id'),
                            notes=f'Created branch: {data["branch_name"]}')
            flash(f'Branch "{data["branch_name"]}" created successfully.', 'success')
            return redirect(url_for('company.company_branches', company_id=company_id))
        except Exception as e:
            flash(f'Error creating branch: {str(e)}', 'danger')

    return render_template('company/branch_create.html',
        page_title=f'{company.get("name", "Company")} - Create Branch',
        company=company
    )


@company_bp.route('/branches/<int:branch_id>/edit', methods=['GET', 'POST'])
def branch_edit(branch_id):
    """Edit a branch."""
    branch = get_branch_by_id(branch_id)
    if not branch:
        flash('Branch not found.', 'danger')
        return redirect(url_for('company.company_list'))

    if request.method == 'POST':
        data = {
            'branch_name': request.form.get('branch_name'),
            'branch_type': request.form.get('branch_type'),
            'description': request.form.get('description'),
            'address': request.form.get('address'),
            'city': request.form.get('city'),
            'country': request.form.get('country'),
            'postal_code': request.form.get('postal_code'),
            'phone': request.form.get('phone'),
            'email': request.form.get('email'),
            'manager_name': request.form.get('manager_name'),
            'manager_contact': request.form.get('manager_contact'),
            'is_active': 1 if request.form.get('is_active') else 0,
            'is_operational': 1 if request.form.get('is_operational') else 0,
            'notes': request.form.get('notes')
        }

        try:
            update_branch(branch_id, data)
            log_company_audit(branch['company_id'], 'branch', branch_id, data['branch_name'],
                            'UPDATE', session.get('user_id'),
                            notes=f'Updated branch: {data["branch_name"]}')
            flash('Branch updated successfully.', 'success')
            return redirect(url_for('company.company_branches', company_id=branch['company_id']))
        except Exception as e:
            flash(f'Error updating branch: {str(e)}', 'danger')

    company = get_company_by_id(branch['company_id'])
    return render_template('company/branch_edit.html',
        page_title=f'Edit {branch.get("branch_name", "Branch")}',
        branch=branch,
        company=company
    )


# =============================================================================
# FACILITY MANAGEMENT
# =============================================================================

@company_bp.route('/<int:company_id>/facilities')
@require_company_access
def company_facilities(company_id):
    """List company facilities."""
    company = get_company_by_id(company_id)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('company.company_list'))

    branches = get_company_branches(company_id)
    facilities = get_company_facilities(company_id)

    return render_template('company/facilities.html',
        page_title=f'{company.get("name", "Company")} - Facilities',
        company=company,
        branches=branches,
        facilities=facilities
    )


@company_bp.route('/<int:company_id>/facilities/create', methods=['GET', 'POST'])
@require_company_access
def facility_create(company_id):
    """Create a new facility."""
    company = get_company_by_id(company_id)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('company.company_list'))

    branches = get_company_branches(company_id)

    if request.method == 'POST':
        data = {
            'company_id': company_id,
            'facility_code': request.form.get('facility_code'),
            'facility_name': request.form.get('facility_name'),
            'branch_id': request.form.get('branch_id') or None,
            'facility_type': request.form.get('facility_type'),
            'facility_subtype': request.form.get('facility_subtype'),
            'address': request.form.get('address'),
            'city': request.form.get('city'),
            'country': request.form.get('country'),
            'postal_code': request.form.get('postal_code'),
            'phone': request.form.get('phone'),
            'email': request.form.get('email'),
            'manager_name': request.form.get('manager_name'),
            'manager_contact': request.form.get('manager_contact'),
            'capacity_sqm': request.form.get('capacity_sqm'),
            'capacity_pallets': request.form.get('capacity_pallets'),
            'is_active': 1 if request.form.get('is_active') else 0,
            'is_shared': 1 if request.form.get('is_shared') else 0,
            'shared_with_companies': request.form.get('shared_with_companies'),
            'operational_hours': request.form.get('operational_hours'),
            'notes': request.form.get('notes')
        }

        try:
            facility_id = create_facility(data)
            log_company_audit(company_id, 'facility', facility_id, data['facility_name'],
                            'CREATE', session.get('user_id'),
                            notes=f'Created facility: {data["facility_name"]}')
            flash(f'Facility "{data["facility_name"]}" created successfully.', 'success')
            return redirect(url_for('company.company_facilities', company_id=company_id))
        except Exception as e:
            flash(f'Error creating facility: {str(e)}', 'danger')

    return render_template('company/facility_create.html',
        page_title=f'{company.get("name", "Company")} - Create Facility',
        company=company,
        branches=branches
    )


# =============================================================================
# USER-COMPANY ACCESS MANAGEMENT
# =============================================================================

@company_bp.route('/<int:company_id>/users')
@require_company_access
def company_users(company_id):
    """List company users and their access."""
    company = get_company_by_id(company_id)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('company.company_list'))

    # Get all users with access to this company
    conn = get_db()
    try:
        users = [dict(row) for row in conn.execute("""
            SELECT uca.*, u.username, u.email, u.is_active as user_active,
                   cb.branch_name, cf.facility_name
            FROM user_company_access uca
            JOIN users u ON uca.user_id = u.id
            LEFT JOIN company_branches cb ON uca.branch_id = cb.id
            LEFT JOIN company_facilities cf ON uca.facility_id = cf.id
            WHERE uca.company_id = ?
            ORDER BY uca.is_default DESC, u.username
        """, (company_id,)).fetchall()]
    finally:
        conn.close()

    return render_template('company/users.html',
        page_title=f'{company.get("name", "Company")} - Users',
        company=company,
        users=users
    )


@company_bp.route('/<int:company_id>/users/assign', methods=['GET', 'POST'])
@require_company_access
def assign_user(company_id):
    """Assign a user to a company."""
    company = get_company_by_id(company_id)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('company.company_list'))

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        if not user_id:
            flash('Please select a user.', 'danger')
            return redirect(url_for('company.assign_user', company_id=company_id))

        # Check if user already has access
        if user_has_company_access(user_id, company_id):
            flash('User already has access to this company.', 'warning')
            return redirect(url_for('company.company_users', company_id=company_id))

        data = {
            'user_id': user_id,
            'company_id': company_id,
            'branch_id': request.form.get('branch_id') or None,
            'facility_id': request.form.get('facility_id') or None,
            'role_in_company': request.form.get('role_in_company', 'user'),
            'is_default': 1 if request.form.get('is_default') else 0,
            'can_view_financials': 1 if request.form.get('can_view_financials') else 0,
            'can_approve_intercompany': 1 if request.form.get('can_approve_intercompany') else 0,
            'cross_company_reporting': 1 if request.form.get('cross_company_reporting') else 0,
            'access_scope': request.form.get('access_scope', 'company'),
            'effective_from': request.form.get('effective_from') or None,
            'effective_to': request.form.get('effective_to') or None
        }

        try:
            access_id = assign_user_to_company(data, granted_by=session.get('user_id'))
            log_company_audit(company_id, 'user_access', access_id, None,
                            'ASSIGN', session.get('user_id'),
                            notes=f'Assigned user {user_id} to company')
            flash('User assigned to company successfully.', 'success')
            return redirect(url_for('company.company_users', company_id=company_id))
        except Exception as e:
            flash(f'Error assigning user: {str(e)}', 'danger')

    # Get available users (not already assigned to this company)
    conn = get_db()
    try:
        available_users = [dict(row) for row in conn.execute("""
            SELECT u.id, u.username, u.email
            FROM users u
            WHERE u.is_active = 1
            AND u.id NOT IN (
                SELECT user_id FROM user_company_access
                WHERE company_id = ? AND is_active = 1
            )
            ORDER BY u.username
        """, (company_id,)).fetchall()]

        branches = get_company_branches(company_id)
        facilities = get_company_facilities(company_id)
    finally:
        conn.close()

    return render_template('company/assign_user.html',
        page_title=f'{company.get("name", "Company")} - Assign User',
        company=company,
        users=available_users,
        branches=branches,
        facilities=facilities
    )


@company_bp.route('/users/access/<int:access_id>/edit', methods=['GET', 'POST'])
def edit_user_access(access_id):
    """Edit user company access."""
    conn = get_db()
    try:
        access = conn.execute("""
            SELECT uca.*, c.name as company_name
            FROM user_company_access uca
            JOIN companies c ON uca.company_id = c.id
            WHERE uca.id = ?
        """, (access_id,)).fetchone()

        if not access:
            flash('Access record not found.', 'danger')
            return redirect(url_for('company.company_list'))

        access = dict(access)
    finally:
        conn.close()

    if request.method == 'POST':
        data = {
            'branch_id': request.form.get('branch_id') or None,
            'facility_id': request.form.get('facility_id') or None,
            'role_in_company': request.form.get('role_in_company'),
            'is_active': 1 if request.form.get('is_active') else 0,
            'is_default': 1 if request.form.get('is_default') else 0,
            'can_view_financials': 1 if request.form.get('can_view_financials') else 0,
            'can_approve_intercompany': 1 if request.form.get('can_approve_intercompany') else 0,
            'cross_company_reporting': 1 if request.form.get('cross_company_reporting') else 0,
            'access_scope': request.form.get('access_scope'),
            'effective_from': request.form.get('effective_from') or None,
            'effective_to': request.form.get('effective_to') or None
        }

        try:
            update_user_company_access(access_id, data)
            log_company_audit(access['company_id'], 'user_access', access_id, None,
                            'UPDATE', session.get('user_id'),
                            notes=f'Updated user access')
            flash('User access updated successfully.', 'success')
            return redirect(url_for('company.company_users', company_id=access['company_id']))
        except Exception as e:
            flash(f'Error updating access: {str(e)}', 'danger')

    branches = get_company_branches(access['company_id'])
    facilities = get_company_facilities(access['company_id'])

    return render_template('company/edit_user_access.html',
        page_title='Edit User Access',
        access=access,
        branches=branches,
        facilities=facilities
    )


@company_bp.route('/users/access/<int:access_id>/revoke', methods=['POST'])
def revoke_user_access(access_id):
    """Revoke user company access."""
    conn = get_db()
    try:
        access = conn.execute("""
            SELECT * FROM user_company_access WHERE id = ?
        """, (access_id,)).fetchone()

        if not access:
            flash('Access record not found.', 'danger')
            return redirect(url_for('company.company_list'))

        access = dict(access)
    finally:
        conn.close()

    reason = request.form.get('reason', 'Revoked by admin')

    try:
        revoke_user_company_access(access_id, session.get('user_id'), reason)
        log_company_audit(access['company_id'], 'user_access', access_id, None,
                        'REVOKE', session.get('user_id'),
                        notes=f'Revoked user access: {reason}')
        flash('User access revoked successfully.', 'success')
    except Exception as e:
        flash(f'Error revoking access: {str(e)}', 'danger')

    return redirect(url_for('company.company_users', company_id=access['company_id']))


# =============================================================================
# COMPANY SETTINGS
# =============================================================================

@company_bp.route('/<int:company_id>/settings')
@require_company_access
def company_settings(company_id):
    """View and manage company settings."""
    company = get_company_by_id(company_id)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('company.company_list'))

    settings = get_company_settings(company_id)
    numbering_rules = get_numbering_rules(company_id)

    return render_template('company/settings.html',
        page_title=f'{company.get("name", "Company")} - Settings',
        company=company,
        settings=settings,
        numbering_rules=numbering_rules
    )


@company_bp.route('/<int:company_id>/settings/update', methods=['POST'])
@require_company_access
def company_settings_update(company_id):
    """Update company settings."""
    company = get_company_by_id(company_id)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('company.company_list'))

    # Update individual settings
    for key, value in request.form.items():
        if key.startswith('setting_'):
            setting_key = key.replace('setting_', '')
            try:
                update_company_setting(company_id, setting_key, value)
            except Exception as e:
                flash(f'Error updating {setting_key}: {str(e)}', 'warning')

    log_company_audit(company_id, 'settings', None, None,
                     'UPDATE', session.get('user_id'),
                     notes='Updated company settings')

    flash('Settings updated successfully.', 'success')
    return redirect(url_for('company.company_settings', company_id=company_id))


@company_bp.route('/<int:company_id>/numbering')
@require_company_access
def company_numbering(company_id):
    """Manage company numbering rules."""
    company = get_company_by_id(company_id)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('company.company_list'))

    numbering_rules = get_numbering_rules(company_id)

    return render_template('company/numbering.html',
        page_title=f'{company.get("name", "Company")} - Numbering Rules',
        company=company,
        numbering_rules=numbering_rules
    )


# =============================================================================
# COMPANY RELATIONSHIPS
# =============================================================================

@company_bp.route('/<int:company_id>/relationships')
@require_company_access
def company_relationships(company_id):
    """View company relationships."""
    company = get_company_by_id(company_id)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('company.company_list'))

    relationships = get_company_relationships(company_id)
    all_companies = get_all_companies(active_only=True)

    return render_template('company/relationships.html',
        page_title=f'{company.get("name", "Company")} - Relationships',
        company=company,
        relationships=relationships,
        companies=[c for c in all_companies if c['id'] != company_id]
    )


@company_bp.route('/<int:company_id>/relationships/create', methods=['POST'])
@require_company_access
def relationship_create(company_id):
    """Create a company relationship."""
    data = {
        'company_id': company_id,
        'related_company_id': request.form.get('related_company_id'),
        'relationship_type': request.form.get('relationship_type'),
        'relationship_subtype': request.form.get('relationship_subtype'),
        'start_date': request.form.get('start_date') or None,
        'end_date': request.form.get('end_date') or None,
        'internal_pricing_policy': request.form.get('internal_pricing_policy'),
        'trade_terms': request.form.get('trade_terms'),
        'credit_limit': request.form.get('credit_limit', 0),
        'payment_terms': request.form.get('payment_terms'),
        'approval_required': 1 if request.form.get('approval_required') else 0,
        'notes': request.form.get('notes')
    }

    try:
        rel_id = create_company_relationship(data)
        log_company_audit(company_id, 'relationship', rel_id, None,
                         'CREATE', session.get('user_id'),
                         notes=f'Created relationship with company {data["related_company_id"]}')
        flash('Relationship created successfully.', 'success')
    except Exception as e:
        flash(f'Error creating relationship: {str(e)}', 'danger')

    return redirect(url_for('company.company_relationships', company_id=company_id))


# =============================================================================
# COMPANY POLICIES
# =============================================================================

@company_bp.route('/<int:company_id>/policies')
@require_company_access
def company_policies(company_id):
    """View company policies."""
    company = get_company_by_id(company_id)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('company.company_list'))

    policies = get_company_policies(company_id)

    return render_template('company/policies.html',
        page_title=f'{company.get("name", "Company")} - Policies',
        company=company,
        policies=policies
    )


# =============================================================================
# COMPANY AUDIT LOG
# =============================================================================

@company_bp.route('/<int:company_id>/audit')
@require_company_access
def company_audit(company_id):
    """View company audit log."""
    company = get_company_by_id(company_id)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('company.company_list'))

    entity_type = request.args.get('entity_type')
    audit_log = get_company_audit_log(company_id, entity_type=entity_type)

    return render_template('company/audit.html',
        page_title=f'{company.get("name", "Company")} - Audit Log',
        company=company,
        audit_log=audit_log,
        entity_type=entity_type
    )


# =============================================================================
# COMPANY HIERARCHY
# =============================================================================

@company_bp.route('/hierarchy')
@company_bp.route('/hierarchy/<int:company_id>')
@require_permission('platform', 'settings', 'view')
def company_hierarchy(company_id=None):
    """View company hierarchy."""
    if company_id:
        hierarchy = get_company_hierarchy(company_id)
        if not hierarchy:
            flash('Company not found.', 'danger')
            return redirect(url_for('company.company_list'))
    else:
        hierarchy = get_company_hierarchy()

    return render_template('company/hierarchy.html',
        page_title='Company Hierarchy',
        hierarchy=hierarchy,
        selected_company_id=company_id
    )


# =============================================================================
# INTERCOMPANY WORKFLOWS
# =============================================================================

@company_bp.route('/intercompany/workflows')
@require_permission('platform', 'settings', 'view')
def intercompany_workflows():
    """List intercompany workflows."""
    workflows = get_intercompany_workflows()

    return render_template('company/intercompany_workflows.html',
        page_title='Intercompany Workflows',
        workflows=workflows
    )


@company_bp.route('/intercompany/transactions')
@require_permission('platform', 'settings', 'view')
def intercompany_transactions():
    """List intercompany transactions."""
    status = request.args.get('status')
    company_id = get_current_company_id()
    transactions = get_intercompany_transactions(company_id=company_id, status=status)

    return render_template('company/intercompany_transactions.html',
        page_title='Intercompany Transactions',
        transactions=transactions,
        status=status
    )


@company_bp.route('/intercompany/transactions/create', methods=['POST'])
@require_permission('platform', 'settings', 'view')
def intercompany_transaction_create():
    """Create a new intercompany transaction."""
    data = {
        'source_company_id': request.form.get('source_company_id'),
        'destination_company_id': request.form.get('destination_company_id'),
        'transaction_type': request.form.get('transaction_type'),
        'reference_type': request.form.get('reference_type'),
        'reference_id': request.form.get('reference_id'),
        'reference_number': request.form.get('reference_number'),
        'amount': request.form.get('amount', 0),
        'currency': request.form.get('currency', 'AED'),
        'exchange_rate': request.form.get('exchange_rate', 1),
        'base_amount': request.form.get('base_amount', 0),
        'priority': request.form.get('priority', 'Normal'),
        'requested_by': session.get('user_id'),
        'notes': request.form.get('notes'),
        'metadata': request.form.get('metadata')
    }

    try:
        txn_id = create_intercompany_transaction(data)
        flash('Intercompany transaction created successfully.', 'success')
    except Exception as e:
        flash(f'Error creating transaction: {str(e)}', 'danger')

    return redirect(url_for('company.intercompany_transactions'))


@company_bp.route('/intercompany/transactions/<int:txn_id>/<string:action>', methods=['POST'])
@require_permission('platform', 'settings', 'view')
def intercompany_transaction_action(txn_id, action):
    """Approve/reject/complete an intercompany transaction."""
    reason = request.form.get('reason')

    try:
        if action == 'approve':
            update_transaction_status(txn_id, 'approved', session.get('user_id'))
            flash('Transaction approved.', 'success')
        elif action == 'reject':
            update_transaction_status(txn_id, 'rejected', session.get('user_id'), reason)
            flash('Transaction rejected.', 'warning')
        elif action == 'complete':
            update_transaction_status(txn_id, 'completed', session.get('user_id'))
            flash('Transaction completed.', 'success')
    except Exception as e:
        flash(f'Error updating transaction: {str(e)}', 'danger')

    return redirect(url_for('company.intercompany_transactions'))


# =============================================================================
# SHARED DATA GOVERNANCE
# =============================================================================

@company_bp.route('/shared-data/rules')
@require_permission('platform', 'settings', 'view')
def shared_data_rules():
    """View and manage shared data rules."""
    rules = get_shared_data_rules()

    return render_template('company/shared_data_rules.html',
        page_title='Shared Data Governance',
        rules=rules
    )


# =============================================================================
# API ENDPOINTS
# =============================================================================

@company_bp.route('/api/context')
def api_company_context():
    """Get current company context for the user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    company_id = get_current_company_id()
    companies = get_user_companies(user_id)
    default_company = get_user_default_company(user_id)

    context = {
        'current_company_id': company_id,
        'current_company': get_company_by_id(company_id) if company_id else None,
        'user_companies': companies,
        'default_company': default_company,
        'can_switch': len(companies) > 1
    }

    return jsonify(context)


@company_bp.route('/api/switch', methods=['POST'])
def api_company_switch():
    """Switch the current active company."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    company_id = request.json.get('company_id')
    if not company_id:
        return jsonify({'error': 'Company ID required'}), 400

    # Verify user has access to this company
    if not user_has_company_access(user_id, company_id):
        return jsonify({'error': 'Access denied'}), 403

    # Set the company context
    set_company_context(company_id)

    return jsonify({
        'success': True,
        'current_company_id': company_id,
        'current_company_name': session.get('current_company_name')
    })


@company_bp.route('/api/next-number/<string:document_type>')
def api_next_number(document_type):
    """Get the next document number for a company."""
    company_id = get_current_company_id()
    if not company_id:
        return jsonify({'error': 'No company context'}), 400

    try:
        number = get_next_document_number(company_id, document_type)
        return jsonify({'number': number})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@company_bp.route('/api/policy/<string:policy_type>/<string:policy_name>')
def api_get_policy(policy_type, policy_name):
    """Get a policy value for the current company."""
    company_id = get_current_company_id()
    if not company_id:
        return jsonify({'error': 'No company context'}), 400

    value = get_policy_value(company_id, policy_type, policy_name)
    return jsonify({'value': value})


@company_bp.route('/api/data-visibility/<string:data_type>')
def api_data_visibility(data_type):
    """Get data visibility rules for a data type."""
    company_id = get_current_company_id() or 0
    visibility = get_data_visibility(data_type, company_id)
    return jsonify(visibility)


# =============================================================================
# REGISTRATION HELPER
# =============================================================================

def register_company_routes(app):
    """Register company routes with the Flask app."""
    app.register_blueprint(company_bp)

    # Initialize company tables on startup
    with app.app_context():
        success, message = run_company_migrations()
        if success:
            print(f"Company management system initialized: {message}")
        else:
            print(f"Company management system initialization warning: {message}")
