"""
Multi-Entity Management Routes
=============================
Flask routes for comprehensive multi-entity management including:
- Group/Holding Management
- Legal Entity Management
- Branch/Operating Unit Management
- Site/Warehouse/Office Management
- Entity Relationships & Intercompany Rules
- Entity Access Scoping & User Permissions
- Shared Master Data Rules
- Entity Numbering Schemes
- Entity Scoping Engine
- Audit & Change History
- Dashboards & Reports
- Export Center
- Settings

Routes are organized under /multi-entity prefix with comprehensive CRUD operations.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, Response
from functools import wraps
import json
import csv
import io
from datetime import datetime

from multi_entity_models import (
    run_migrations,
    get_all_groups, get_group_by_id, create_group, update_group, archive_group,
    get_all_entities, get_entity_by_id, create_entity, update_entity, archive_entity, restore_entity,
    get_entity_branches, get_all_branches, get_branch_by_id, create_branch, update_branch, archive_branch,
    get_entity_sites, get_all_sites, get_site_by_id, create_site, update_site, archive_site,
    get_entity_relationships, create_relationship,
    get_entity_access, get_user_entity_access, assign_entity_access, update_access_scope, revoke_entity_access,
    get_user_entity_scope, set_user_entity_context, get_current_entity_context,
    get_user_favorite_entities, add_favorite_entity,
    get_numbering_schemes, get_next_entity_number, create_numbering_scheme,
    get_intercompany_rules, create_intercompany_rule,
    get_shared_data_rules, update_shared_data_rule,
    log_entity_audit, get_entity_audit_log,
    get_entity_settings, update_entity_setting,
    get_entity_dashboard_stats, get_entity_hierarchy,
    check_entity_code_unique, check_group_code_unique, check_branch_code_unique, check_site_code_unique,
    search_entities, search_branches, search_sites, get_entities_by_group, get_entity_breadcrumb
)

# Import database utilities
from database import get_db, get_db_context, log_audit
from permissions import require_permission, get_user_permissions

# Create blueprint
multi_entity_bp = Blueprint('multi_entity', __name__, url_prefix='/multi-entity')


# =============================================================================
# DECORATORS AND HELPERS
# =============================================================================

def require_multientity_access(permission: str = 'view'):
    """Decorator to require multi-entity access permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                return redirect(url_for('login'))

            permissions = get_user_permissions(user_id)

            # Check specific permission or any multientity permission
            perm_map = {
                'view': 'multientity.dashboard.view',
                'create': 'multientity.groups.create',
                'edit': 'multientity.groups.edit',
                'delete': 'multientity.groups.delete',
                'manage_group': 'multientity.groups.view',
                'manage_entities': 'multientity.entities.view',
                'manage_branches': 'multientity.branches.view',
                'manage_sites': 'multientity.sites.view',
                'manage_scopes': 'multientity.access.view',
                'manage_intercompany': 'multientity.intercompany.view',
                'audit_view': 'multientity.audit.view',
                'export': 'multientity.export.view',
                'settings': 'multientity.settings.view',
            }

            required_perm = perm_map.get(permission, 'multientity.dashboard.view')

            # Super admins can access everything
            if 'platform.settings.manage' in permissions:
                return f(*args, **kwargs)

            # Check for exact permission or wildcard match
            if required_perm not in permissions:
                # Try wildcard - if user has 'multientity.*' or 'multientity.view'
                has_any = any(p.startswith('multientity.') for p in permissions)
                if not has_any:
                    flash('You do not have access to Multi-Entity Management.', 'danger')
                    return redirect(url_for('index'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def set_entity_context(entity_id: int = None, branch_id: int = None, site_id: int = None):
    """Set the current entity context in session."""
    if entity_id:
        session['current_entity_id'] = entity_id
        entity = get_entity_by_id(entity_id)
        if entity:
            session['current_entity_name'] = entity.get('legal_name', '')
            session['current_entity_code'] = entity.get('entity_code', '')
    if branch_id:
        session['current_branch_id'] = branch_id
        branch = get_branch_by_id(branch_id)
        if branch:
            session['current_branch_name'] = branch.get('branch_name', '')
    if site_id:
        session['current_site_id'] = site_id
        site = get_site_by_id(site_id)
        if site:
            session['current_site_name'] = site.get('site_name', '')

    user_id = session.get('user_id')
    if user_id:
        set_user_entity_context(user_id, entity_id, branch_id, site_id)


def get_current_entity_id():
    """Get the current entity ID from session or user's default."""
    user_id = session.get('user_id')
    entity_id = session.get('current_entity_id')

    if not entity_id and user_id:
        scope = get_user_entity_scope(user_id)
        entity_id = scope.get('default_entity_id')

    return entity_id


def log_change(entity_type, entity_id, action, field_name=None, old_value=None,
               new_value=None, notes=None, **kwargs):
    """Log an entity change to audit trail."""
    user_id = session.get('user_id')
    entity_id_ctx = kwargs.get('entity_id') or get_current_entity_id()

    log_entity_audit(
        entity_id=entity_id_ctx,
        entity_type=entity_type,
        action=action,
        user_id=user_id,
        field_name=field_name,
        old_value=str(old_value) if old_value else None,
        new_value=str(new_value) if new_value else None,
        notes=notes,
        source='ui',
        group_id=kwargs.get('group_id'),
        branch_id=kwargs.get('branch_id'),
        site_id=kwargs.get('site_id')
    )


# =============================================================================
# INITIALIZATION
# =============================================================================

def register_multi_entity_routes(app):
    """Register multi-entity routes with the Flask app."""
    run_migrations()
    app.register_blueprint(multi_entity_bp)


# =============================================================================
# DASHBOARD & OVERVIEW
# =============================================================================

@multi_entity_bp.route('/')
@multi_entity_bp.route('/dashboard')
@require_multientity_access('view')
def dashboard():
    """Multi-entity management dashboard."""
    stats = get_entity_dashboard_stats()
    recent_audit = get_entity_audit_log(limit=20)
    hierarchy = get_entity_hierarchy()

    return render_template('multi_entity/dashboard.html',
        page_title='Multi-Entity Dashboard',
        stats=stats,
        recent_audit=recent_audit,
        hierarchy=hierarchy
    )


@multi_entity_bp.route('/overview')
@require_multientity_access('view')
def overview():
    """Overview page with key metrics."""
    stats = get_entity_dashboard_stats()

    # Get entity status breakdown
    entities = get_all_entities(active_only=False)
    entity_status = {}
    for e in entities:
        status = e.get('status', 'unknown')
        entity_status[status] = entity_status.get(status, 0) + 1

    # Get recent activity
    recent_changes = get_entity_audit_log(limit=10)

    return render_template('multi_entity/overview.html',
        page_title='Multi-Entity Overview',
        stats=stats,
        entity_status=entity_status,
        recent_changes=recent_changes
    )


# =============================================================================
# GROUP/HOLDING MANAGEMENT
# =============================================================================

@multi_entity_bp.route('/groups')
@require_multientity_access('view')
def group_list():
    """List all entity groups."""
    groups = get_all_groups(active_only=False)

    # Apply filters
    status_filter = request.args.get('status')
    search_query = request.args.get('q')

    if status_filter == 'active':
        groups = [g for g in groups if g.get('is_active') == 1]
    elif status_filter == 'archived':
        groups = [g for g in groups if g.get('is_active') == 0]

    if search_query:
        groups = [g for g in groups if search_query.lower() in g.get('legal_name', '').lower()
                 or search_query.lower() in g.get('group_code', '').lower()]

    return render_template('multi_entity/groups/list.html',
        page_title='Entity Groups',
        groups=groups,
        status_filter=status_filter,
        search_query=search_query
    )


@multi_entity_bp.route('/groups/create', methods=['GET', 'POST'])
@require_multientity_access('create')
def group_create():
    """Create a new entity group."""
    if request.method == 'POST':
        data = {
            'group_code': request.form.get('group_code'),
            'legal_name': request.form.get('legal_name'),
            'trade_name': request.form.get('trade_name'),
            'short_name': request.form.get('short_name'),
            'group_type': request.form.get('group_type', 'holding'),
            'registration_number': request.form.get('registration_number'),
            'tax_identification': request.form.get('tax_identification'),
            'vat_number': request.form.get('vat_number'),
            'country': request.form.get('country', 'UAE'),
            'state_region': request.form.get('state_region'),
            'city': request.form.get('city'),
            'address_line1': request.form.get('address_line1'),
            'address_line2': request.form.get('address_line2'),
            'postal_code': request.form.get('postal_code'),
            'phone': request.form.get('phone'),
            'mobile': request.form.get('mobile'),
            'email': request.form.get('email'),
            'website': request.form.get('website'),
            'default_currency': request.form.get('default_currency', 'AED'),
            'fiscal_year_start': request.form.get('fiscal_year_start', 1),
            'fiscal_year_end': request.form.get('fiscal_year_end', 12),
            'base_language': request.form.get('base_language', 'en'),
            'parent_group_id': request.form.get('parent_group_id') or None,
            'notes': request.form.get('notes'),
            'created_by': session.get('user_id')
        }

        if not data['group_code']:
            flash('Group code is required.', 'danger')
            return redirect(url_for('multi_entity.group_create'))

        if not check_group_code_unique(data['group_code']):
            flash('Group code already exists.', 'danger')
            return redirect(url_for('multi_entity.group_create'))

        try:
            group_id = create_group(data)
            log_change('group', group_id, 'CREATE', notes=f'Created group {data["legal_name"]}')
            flash('Entity group created successfully.', 'success')
            return redirect(url_for('multi_entity.group_detail', group_id=group_id))
        except Exception as e:
            flash(f'Error creating group: {str(e)}', 'danger')

    # Get parent groups for dropdown
    parent_groups = get_all_groups(active_only=True)

    return render_template('multi_entity/groups/create.html',
        page_title='Create Entity Group',
        parent_groups=parent_groups
    )


@multi_entity_bp.route('/groups/<int:group_id>')
@require_multientity_access('view')
def group_detail(group_id):
    """View entity group details."""
    group = get_group_by_id(group_id)
    if not group:
        flash('Entity group not found.', 'danger')
        return redirect(url_for('multi_entity.group_list'))

    # Get entities under this group
    entities = get_entities_by_group(group_id)

    # Get audit history
    audit_log = get_entity_audit_log(group_id=group_id, limit=50)

    # Get statistics
    stats = get_entity_dashboard_stats(group_id=group_id)

    return render_template('multi_entity/groups/detail.html',
        page_title=f'{group.get("legal_name", "Group")} - Details',
        group=group,
        entities=entities,
        audit_log=audit_log,
        stats=stats
    )


@multi_entity_bp.route('/groups/<int:group_id>/edit', methods=['GET', 'POST'])
@require_multientity_access('edit')
def group_edit(group_id):
    """Edit an entity group."""
    group = get_group_by_id(group_id)
    if not group:
        flash('Entity group not found.', 'danger')
        return redirect(url_for('multi_entity.group_list'))

    if request.method == 'POST':
        data = {
            'legal_name': request.form.get('legal_name'),
            'trade_name': request.form.get('trade_name'),
            'short_name': request.form.get('short_name'),
            'group_type': request.form.get('group_type'),
            'registration_number': request.form.get('registration_number'),
            'tax_identification': request.form.get('tax_identification'),
            'vat_number': request.form.get('vat_number'),
            'country': request.form.get('country'),
            'state_region': request.form.get('state_region'),
            'city': request.form.get('city'),
            'address_line1': request.form.get('address_line1'),
            'address_line2': request.form.get('address_line2'),
            'postal_code': request.form.get('postal_code'),
            'phone': request.form.get('phone'),
            'mobile': request.form.get('mobile'),
            'email': request.form.get('email'),
            'website': request.form.get('website'),
            'default_currency': request.form.get('default_currency'),
            'fiscal_year_start': request.form.get('fiscal_year_start'),
            'fiscal_year_end': request.form.get('fiscal_year_end'),
            'base_language': request.form.get('base_language'),
            'parent_group_id': request.form.get('parent_group_id') or None,
            'notes': request.form.get('notes'),
        }

        try:
            update_group(group_id, data)
            log_change('group', group_id, 'UPDATE', notes=f'Updated group {data["legal_name"]}')
            flash('Entity group updated successfully.', 'success')
            return redirect(url_for('multi_entity.group_detail', group_id=group_id))
        except Exception as e:
            flash(f'Error updating group: {str(e)}', 'danger')

    parent_groups = get_all_groups(active_only=True)

    return render_template('multi_entity/groups/edit.html',
        page_title=f'Edit {group.get("legal_name", "Group")}',
        group=group,
        parent_groups=parent_groups
    )


@multi_entity_bp.route('/groups/<int:group_id>/archive', methods=['POST'])
@require_multientity_access('delete')
def group_archive(group_id):
    """Archive an entity group."""
    try:
        archive_group(group_id, session.get('user_id'))
        log_change('group', group_id, 'ARCHIVE', notes='Archived entity group')
        flash('Entity group archived successfully.', 'success')
    except Exception as e:
        flash(f'Error archiving group: {str(e)}', 'danger')

    return redirect(url_for('multi_entity.group_list'))


# =============================================================================
# LEGAL ENTITY MANAGEMENT
# =============================================================================

@multi_entity_bp.route('/entities')
@require_multientity_access('view')
def entity_list():
    """List all legal entities."""
    group_id = request.args.get('group_id', type=int)
    status_filter = request.args.get('status')
    search_query = request.args.get('q')

    entities = get_all_entities(active_only=False, group_id=group_id)

    if status_filter == 'active':
        entities = [e for e in entities if e.get('is_active') == 1]
    elif status_filter == 'archived':
        entities = [e for e in entities if e.get('is_active') == 0]
    elif status_filter == 'suspended':
        entities = [e for e in entities if e.get('status') == 'suspended']

    if search_query:
        entities = [e for e in entities if search_query.lower() in e.get('legal_name', '').lower()
                   or search_query.lower() in e.get('entity_code', '').lower()
                   or search_query.lower() in e.get('trade_name', '').lower()]

    groups = get_all_groups(active_only=True)

    return render_template('multi_entity/entities/list.html',
        page_title='Legal Entities',
        entities=entities,
        groups=groups,
        selected_group_id=group_id,
        status_filter=status_filter,
        search_query=search_query
    )


@multi_entity_bp.route('/entities/create', methods=['GET', 'POST'])
@require_multientity_access('create')
def entity_create():
    """Create a new legal entity."""
    if request.method == 'POST':
        data = {
            'entity_code': request.form.get('entity_code'),
            'legal_name': request.form.get('legal_name'),
            'short_name': request.form.get('short_name'),
            'trade_name': request.form.get('trade_name'),
            'entity_type': request.form.get('entity_type', 'subsidiary'),
            'business_type': request.form.get('business_type'),
            'registration_number': request.form.get('registration_number'),
            'tax_identification': request.form.get('tax_identification'),
            'vat_number': request.form.get('vat_number'),
            'excise_tax_number': request.form.get('excise_tax_number'),
            'customs_code': request.form.get('customs_code'),
            'chamber_of_commerce_number': request.form.get('chamber_of_commerce_number'),
            'license_number': request.form.get('license_number'),
            'license_type': request.form.get('license_type'),
            'license_expiry': request.form.get('license_expiry'),
            'country': request.form.get('country', 'UAE'),
            'state_region': request.form.get('state_region'),
            'city': request.form.get('city'),
            'district': request.form.get('district'),
            'address_line1': request.form.get('address_line1'),
            'address_line2': request.form.get('address_line2'),
            'postal_code': request.form.get('postal_code'),
            'phone': request.form.get('phone'),
            'mobile': request.form.get('mobile'),
            'fax': request.form.get('fax'),
            'email': request.form.get('email'),
            'website': request.form.get('website'),
            'default_currency': request.form.get('default_currency', 'AED'),
            'secondary_currency': request.form.get('secondary_currency'),
            'timezone': request.form.get('timezone', 'Asia/Dubai'),
            'date_format': request.form.get('date_format', 'DD/MM/YYYY'),
            'fiscal_year_start': request.form.get('fiscal_year_start', 1),
            'fiscal_year_end': request.form.get('fiscal_year_end', 12),
            'base_language': request.form.get('base_language', 'en'),
            'ownership_percentage': request.form.get('ownership_percentage', 100),
            'parent_entity_id': request.form.get('parent_entity_id') or None,
            'parent_group_id': request.form.get('parent_group_id') or None,
            'intercompany_partner_code': request.form.get('intercompany_partner_code'),
            'consolidation_flag': 1 if request.form.get('consolidation_flag') else 0,
            'primary_contact_name': request.form.get('primary_contact_name'),
            'primary_contact_phone': request.form.get('primary_contact_phone'),
            'primary_contact_email': request.form.get('primary_contact_email'),
            'finance_contact_name': request.form.get('finance_contact_name'),
            'finance_contact_email': request.form.get('finance_contact_email'),
            'document_prefix': request.form.get('document_prefix'),
            'notes': request.form.get('notes'),
            'created_by': session.get('user_id')
        }

        if not data['entity_code']:
            flash('Entity code is required.', 'danger')
            return redirect(url_for('multi_entity.entity_create'))

        if not check_entity_code_unique(data['entity_code']):
            flash('Entity code already exists.', 'danger')
            return redirect(url_for('multi_entity.entity_create'))

        try:
            entity_id = create_entity(data)
            log_change('entity', entity_id, 'CREATE', entity_id=entity_id,
                      notes=f'Created entity {data["legal_name"]}')
            flash('Legal entity created successfully.', 'success')
            return redirect(url_for('multi_entity.entity_detail', entity_id=entity_id))
        except Exception as e:
            flash(f'Error creating entity: {str(e)}', 'danger')

    groups = get_all_groups(active_only=True)
    entities = get_all_entities(active_only=True)

    return render_template('multi_entity/entities/create.html',
        page_title='Create Legal Entity',
        groups=groups,
        entities=entities
    )


@multi_entity_bp.route('/entities/<int:entity_id>')
@require_multientity_access('view')
def entity_detail(entity_id):
    """View legal entity details."""
    entity = get_entity_by_id(entity_id)
    if not entity:
        flash('Legal entity not found.', 'danger')
        return redirect(url_for('multi_entity.entity_list'))

    # Get related data
    branches = get_entity_branches(entity_id, active_only=False)
    sites = get_entity_sites(entity_id, active_only=False)
    relationships = get_entity_relationships(entity_id=entity_id)
    access_list = get_entity_access(entity_id=entity_id)
    audit_log = get_entity_audit_log(entity_id=entity_id, limit=50)

    # Get breadcrumbs
    breadcrumbs = get_entity_breadcrumb(entity_id)

    return render_template('multi_entity/entities/detail.html',
        page_title=f'{entity.get("legal_name", "Entity")} - Details',
        entity=entity,
        branches=branches,
        sites=sites,
        relationships=relationships,
        access_list=access_list,
        audit_log=audit_log,
        breadcrumbs=breadcrumbs
    )


@multi_entity_bp.route('/entities/<int:entity_id>/edit', methods=['GET', 'POST'])
@require_multientity_access('edit')
def entity_edit(entity_id):
    """Edit a legal entity."""
    entity = get_entity_by_id(entity_id)
    if not entity:
        flash('Legal entity not found.', 'danger')
        return redirect(url_for('multi_entity.entity_list'))

    if request.method == 'POST':
        data = {
            'legal_name': request.form.get('legal_name'),
            'short_name': request.form.get('short_name'),
            'trade_name': request.form.get('trade_name'),
            'entity_type': request.form.get('entity_type'),
            'business_type': request.form.get('business_type'),
            'registration_number': request.form.get('registration_number'),
            'tax_identification': request.form.get('tax_identification'),
            'vat_number': request.form.get('vat_number'),
            'excise_tax_number': request.form.get('excise_tax_number'),
            'customs_code': request.form.get('customs_code'),
            'chamber_of_commerce_number': request.form.get('chamber_of_commerce_number'),
            'license_number': request.form.get('license_number'),
            'license_type': request.form.get('license_type'),
            'license_expiry': request.form.get('license_expiry'),
            'country': request.form.get('country'),
            'state_region': request.form.get('state_region'),
            'city': request.form.get('city'),
            'district': request.form.get('district'),
            'address_line1': request.form.get('address_line1'),
            'address_line2': request.form.get('address_line2'),
            'postal_code': request.form.get('postal_code'),
            'phone': request.form.get('phone'),
            'mobile': request.form.get('mobile'),
            'fax': request.form.get('fax'),
            'email': request.form.get('email'),
            'website': request.form.get('website'),
            'default_currency': request.form.get('default_currency'),
            'secondary_currency': request.form.get('secondary_currency'),
            'timezone': request.form.get('timezone'),
            'date_format': request.form.get('date_format'),
            'fiscal_year_start': request.form.get('fiscal_year_start'),
            'fiscal_year_end': request.form.get('fiscal_year_end'),
            'base_language': request.form.get('base_language'),
            'ownership_percentage': request.form.get('ownership_percentage'),
            'parent_entity_id': request.form.get('parent_entity_id') or None,
            'parent_group_id': request.form.get('parent_group_id') or None,
            'intercompany_partner_code': request.form.get('intercompany_partner_code'),
            'consolidation_flag': 1 if request.form.get('consolidation_flag') else 0,
            'status': request.form.get('status'),
            'primary_contact_name': request.form.get('primary_contact_name'),
            'primary_contact_phone': request.form.get('primary_contact_phone'),
            'primary_contact_email': request.form.get('primary_contact_email'),
            'finance_contact_name': request.form.get('finance_contact_name'),
            'finance_contact_email': request.form.get('finance_contact_email'),
            'document_prefix': request.form.get('document_prefix'),
            'notes': request.form.get('notes'),
        }

        try:
            update_entity(entity_id, data)
            log_change('entity', entity_id, 'UPDATE', entity_id=entity_id,
                      notes=f'Updated entity {data["legal_name"]}')
            flash('Legal entity updated successfully.', 'success')
            return redirect(url_for('multi_entity.entity_detail', entity_id=entity_id))
        except Exception as e:
            flash(f'Error updating entity: {str(e)}', 'danger')

    groups = get_all_groups(active_only=True)
    entities = get_all_entities(active_only=True)

    return render_template('multi_entity/entities/edit.html',
        page_title=f'Edit {entity.get("legal_name", "Entity")}',
        entity=entity,
        groups=groups,
        entities=entities
    )


@multi_entity_bp.route('/entities/<int:entity_id>/archive', methods=['POST'])
@require_multientity_access('delete')
def entity_archive(entity_id):
    """Archive a legal entity."""
    try:
        archive_entity(entity_id, session.get('user_id'))
        log_change('entity', entity_id, 'ARCHIVE', entity_id=entity_id, notes='Archived entity')
        flash('Legal entity archived successfully.', 'success')
    except Exception as e:
        flash(f'Error archiving entity: {str(e)}', 'danger')

    return redirect(url_for('multi_entity.entity_list'))


@multi_entity_bp.route('/entities/<int:entity_id>/restore', methods=['POST'])
@require_multientity_access('edit')
def entity_restore(entity_id):
    """Restore an archived legal entity."""
    try:
        restore_entity(entity_id)
        log_change('entity', entity_id, 'RESTORE', entity_id=entity_id, notes='Restored entity')
        flash('Legal entity restored successfully.', 'success')
    except Exception as e:
        flash(f'Error restoring entity: {str(e)}', 'danger')

    return redirect(url_for('multi_entity.entity_detail', entity_id=entity_id))


# =============================================================================
# BRANCH MANAGEMENT
# =============================================================================

@multi_entity_bp.route('/branches')
@require_multientity_access('view')
def branch_list():
    """List all branches."""
    entity_id = request.args.get('entity_id', type=int)
    status_filter = request.args.get('status')
    search_query = request.args.get('q')

    branches = get_all_branches(active_only=False, entity_id=entity_id)

    if status_filter == 'active':
        branches = [b for b in branches if b.get('is_active') == 1]
    elif status_filter == 'inactive':
        branches = [b for b in branches if b.get('is_active') == 0]

    if search_query:
        branches = [b for b in branches if search_query.lower() in b.get('branch_name', '').lower()
                   or search_query.lower() in b.get('branch_code', '').lower()]

    entities = get_all_entities(active_only=True)

    return render_template('multi_entity/branches/list.html',
        page_title='Branches / Operating Units',
        branches=branches,
        entities=entities,
        selected_entity_id=entity_id,
        status_filter=status_filter,
        search_query=search_query
    )


@multi_entity_bp.route('/entities/<int:entity_id>/branches/create', methods=['GET', 'POST'])
@require_multientity_access('create')
def branch_create(entity_id):
    """Create a new branch for an entity."""
    entity = get_entity_by_id(entity_id)
    if not entity:
        flash('Legal entity not found.', 'danger')
        return redirect(url_for('multi_entity.entity_list'))

    if request.method == 'POST':
        data = {
            'entity_id': entity_id,
            'branch_code': request.form.get('branch_code'),
            'branch_name': request.form.get('branch_name'),
            'short_name': request.form.get('short_name'),
            'branch_type': request.form.get('branch_type', 'branch_office'),
            'branch_category': request.form.get('branch_category'),
            'description': request.form.get('description'),
            'is_head_office': 1 if request.form.get('is_head_office') else 0,
            'is_operational': 1 if request.form.get('is_operational') else 0,
            'contact_name': request.form.get('contact_name'),
            'contact_phone': request.form.get('contact_phone'),
            'contact_email': request.form.get('contact_email'),
            'contact_position': request.form.get('contact_position'),
            'address_line1': request.form.get('address_line1'),
            'address_line2': request.form.get('address_line2'),
            'city': request.form.get('city'),
            'district': request.form.get('district'),
            'country': request.form.get('country'),
            'postal_code': request.form.get('postal_code'),
            'phone': request.form.get('phone'),
            'phone2': request.form.get('phone2'),
            'mobile': request.form.get('mobile'),
            'fax': request.form.get('fax'),
            'email': request.form.get('email'),
            'default_document_prefix': request.form.get('default_document_prefix'),
            'local_timezone': request.form.get('local_timezone'),
            'local_language': request.form.get('local_language'),
            'operational_hours': {
                'monday': request.form.get('hours_monday', '09:00-18:00'),
                'tuesday': request.form.get('hours_tuesday', '09:00-18:00'),
                'wednesday': request.form.get('hours_wednesday', '09:00-18:00'),
                'thursday': request.form.get('hours_thursday', '09:00-18:00'),
                'friday': request.form.get('hours_friday', '09:00-18:00'),
                'saturday': request.form.get('hours_saturday', ''),
                'sunday': request.form.get('hours_sunday', ''),
            },
            'status': request.form.get('status', 'active'),
            'notes': request.form.get('notes'),
            'created_by': session.get('user_id')
        }

        if not data['branch_code']:
            flash('Branch code is required.', 'danger')
            return redirect(url_for('multi_entity.branch_create', entity_id=entity_id))

        if not check_branch_code_unique(data['branch_code']):
            flash('Branch code already exists.', 'danger')
            return redirect(url_for('multi_entity.branch_create', entity_id=entity_id))

        try:
            branch_id = create_branch(data)
            log_change('branch', branch_id, 'CREATE', entity_id=entity_id,
                      notes=f'Created branch {data["branch_name"]}')
            flash('Branch created successfully.', 'success')
            return redirect(url_for('multi_entity.branch_detail', branch_id=branch_id))
        except Exception as e:
            flash(f'Error creating branch: {str(e)}', 'danger')

    return render_template('multi_entity/branches/create.html',
        page_title=f'Create Branch for {entity.get("legal_name", "")}',
        entity=entity
    )


@multi_entity_bp.route('/branches/<int:branch_id>')
@require_multientity_access('view')
def branch_detail(branch_id):
    """View branch details."""
    branch = get_branch_by_id(branch_id)
    if not branch:
        flash('Branch not found.', 'danger')
        return redirect(url_for('multi_entity.branch_list'))

    entity = get_entity_by_id(branch['entity_id'])
    sites = get_branch_sites(branch_id, active_only=False)
    audit_log = get_entity_audit_log(branch_id=branch_id, limit=50)

    return render_template('multi_entity/branches/detail.html',
        page_title=f'{branch.get("branch_name", "Branch")} - Details',
        branch=branch,
        entity=entity,
        sites=sites,
        audit_log=audit_log
    )


@multi_entity_bp.route('/branches/<int:branch_id>/edit', methods=['GET', 'POST'])
@require_multientity_access('edit')
def branch_edit(branch_id):
    """Edit a branch."""
    branch = get_branch_by_id(branch_id)
    if not branch:
        flash('Branch not found.', 'danger')
        return redirect(url_for('multi_entity.branch_list'))

    if request.method == 'POST':
        data = {
            'branch_name': request.form.get('branch_name'),
            'short_name': request.form.get('short_name'),
            'branch_type': request.form.get('branch_type'),
            'branch_category': request.form.get('branch_category'),
            'description': request.form.get('description'),
            'is_head_office': 1 if request.form.get('is_head_office') else 0,
            'is_operational': 1 if request.form.get('is_operational') else 0,
            'contact_name': request.form.get('contact_name'),
            'contact_phone': request.form.get('contact_phone'),
            'contact_email': request.form.get('contact_email'),
            'contact_position': request.form.get('contact_position'),
            'address_line1': request.form.get('address_line1'),
            'address_line2': request.form.get('address_line2'),
            'city': request.form.get('city'),
            'district': request.form.get('district'),
            'country': request.form.get('country'),
            'postal_code': request.form.get('postal_code'),
            'phone': request.form.get('phone'),
            'phone2': request.form.get('phone2'),
            'mobile': request.form.get('mobile'),
            'fax': request.form.get('fax'),
            'email': request.form.get('email'),
            'default_document_prefix': request.form.get('default_document_prefix'),
            'local_timezone': request.form.get('local_timezone'),
            'local_language': request.form.get('local_language'),
            'status': request.form.get('status'),
            'notes': request.form.get('notes'),
        }

        # Parse operational hours
        if request.form.get('hours_monday'):
            data['operational_hours'] = {
                'monday': request.form.get('hours_monday', '09:00-18:00'),
                'tuesday': request.form.get('hours_tuesday', '09:00-18:00'),
                'wednesday': request.form.get('hours_wednesday', '09:00-18:00'),
                'thursday': request.form.get('hours_thursday', '09:00-18:00'),
                'friday': request.form.get('hours_friday', '09:00-18:00'),
                'saturday': request.form.get('hours_saturday', ''),
                'sunday': request.form.get('hours_sunday', ''),
            }

        try:
            update_branch(branch_id, data)
            log_change('branch', branch_id, 'UPDATE', entity_id=branch['entity_id'],
                      notes=f'Updated branch {data["branch_name"]}')
            flash('Branch updated successfully.', 'success')
            return redirect(url_for('multi_entity.branch_detail', branch_id=branch_id))
        except Exception as e:
            flash(f'Error updating branch: {str(e)}', 'danger')

    entity = get_entity_by_id(branch['entity_id'])

    return render_template('multi_entity/branches/edit.html',
        page_title=f'Edit {branch.get("branch_name", "Branch")}',
        branch=branch,
        entity=entity
    )


@multi_entity_bp.route('/branches/<int:branch_id>/archive', methods=['POST'])
@require_multientity_access('delete')
def branch_archive(branch_id):
    """Archive a branch."""
    branch = get_branch_by_id(branch_id)
    try:
        archive_branch(branch_id, session.get('user_id'))
        log_change('branch', branch_id, 'ARCHIVE', entity_id=branch['entity_id'] if branch else None,
                  notes='Archived branch')
        flash('Branch archived successfully.', 'success')
    except Exception as e:
        flash(f'Error archiving branch: {str(e)}', 'danger')

    return redirect(url_for('multi_entity.branch_list'))


# =============================================================================
# SITE MANAGEMENT
# =============================================================================

@multi_entity_bp.route('/sites')
@require_multientity_access('view')
def site_list():
    """List all sites."""
    entity_id = request.args.get('entity_id', type=int)
    branch_id = request.args.get('branch_id', type=int)
    status_filter = request.args.get('status')
    search_query = request.args.get('q')

    sites = get_all_sites(active_only=False, entity_id=entity_id)

    if branch_id:
        sites = [s for s in sites if s.get('branch_id') == branch_id]

    if status_filter == 'active':
        sites = [s for s in sites if s.get('is_active') == 1]
    elif status_filter == 'inactive':
        sites = [s for s in sites if s.get('is_active') == 0]

    if search_query:
        sites = [s for s in sites if search_query.lower() in s.get('site_name', '').lower()
                or search_query.lower() in s.get('site_code', '').lower()]

    entities = get_all_entities(active_only=True)
    branches = get_all_branches(active_only=True) if entity_id else []

    return render_template('multi_entity/sites/list.html',
        page_title='Sites / Warehouses / Offices',
        sites=sites,
        entities=entities,
        branches=branches,
        selected_entity_id=entity_id,
        selected_branch_id=branch_id,
        status_filter=status_filter,
        search_query=search_query
    )


@multi_entity_bp.route('/branches/<int:branch_id>/sites/create', methods=['GET', 'POST'])
@require_multientity_access('create')
def site_create(branch_id):
    """Create a new site for a branch."""
    branch = get_branch_by_id(branch_id)
    if not branch:
        flash('Branch not found.', 'danger')
        return redirect(url_for('multi_entity.branch_list'))

    if request.method == 'POST':
        data = {
            'entity_id': branch['entity_id'],
            'branch_id': branch_id,
            'site_code': request.form.get('site_code'),
            'site_name': request.form.get('site_name'),
            'short_name': request.form.get('short_name'),
            'site_type': request.form.get('site_type', 'warehouse'),
            'site_subtype': request.form.get('site_subtype'),
            'description': request.form.get('description'),
            'address_line1': request.form.get('address_line1'),
            'address_line2': request.form.get('address_line2'),
            'city': request.form.get('city'),
            'district': request.form.get('district'),
            'country': request.form.get('country'),
            'postal_code': request.form.get('postal_code'),
            'phone': request.form.get('phone'),
            'mobile': request.form.get('mobile'),
            'fax': request.form.get('fax'),
            'email': request.form.get('email'),
            'contact_name': request.form.get('contact_name'),
            'contact_position': request.form.get('contact_position'),
            'contact_phone': request.form.get('contact_phone'),
            'contact_email': request.form.get('contact_email'),
            'site_area_sqm': request.form.get('site_area_sqm'),
            'covered_area_sqm': request.form.get('covered_area_sqm'),
            'yard_area_sqm': request.form.get('yard_area_sqm'),
            'capacity_pallets': request.form.get('capacity_pallets'),
            'capacity_items': request.form.get('capacity_items'),
            'is_shared': 1 if request.form.get('is_shared') else 0,
            'working_days': request.form.get('working_days'),
            'is_operational': 1 if request.form.get('is_operational') else 0,
            'status': request.form.get('status', 'active'),
            'site_manager_name': request.form.get('site_manager_name'),
            'site_manager_phone': request.form.get('site_manager_phone'),
            'site_manager_email': request.form.get('site_manager_email'),
            'notes': request.form.get('notes'),
            'created_by': session.get('user_id')
        }

        if not data['site_code']:
            flash('Site code is required.', 'danger')
            return redirect(url_for('multi_entity.site_create', branch_id=branch_id))

        if not check_site_code_unique(data['site_code']):
            flash('Site code already exists.', 'danger')
            return redirect(url_for('multi_entity.site_create', branch_id=branch_id))

        try:
            site_id = create_site(data)
            log_change('site', site_id, 'CREATE', entity_id=branch['entity_id'],
                      branch_id=branch_id, notes=f'Created site {data["site_name"]}')
            flash('Site created successfully.', 'success')
            return redirect(url_for('multi_entity.site_detail', site_id=site_id))
        except Exception as e:
            flash(f'Error creating site: {str(e)}', 'danger')

    return render_template('multi_entity/sites/create.html',
        page_title=f'Create Site for {branch.get("branch_name", "")}',
        branch=branch
    )


@multi_entity_bp.route('/sites/<int:site_id>')
@require_multientity_access('view')
def site_detail(site_id):
    """View site details."""
    site = get_site_by_id(site_id)
    if not site:
        flash('Site not found.', 'danger')
        return redirect(url_for('multi_entity.site_list'))

    entity = get_entity_by_id(site['entity_id'])
    branch = get_branch_by_id(site['branch_id']) if site.get('branch_id') else None
    audit_log = get_entity_audit_log(site_id=site_id, limit=50)

    return render_template('multi_entity/sites/detail.html',
        page_title=f'{site.get("site_name", "Site")} - Details',
        site=site,
        entity=entity,
        branch=branch,
        audit_log=audit_log
    )


@multi_entity_bp.route('/sites/<int:site_id>/edit', methods=['GET', 'POST'])
@require_multientity_access('edit')
def site_edit(site_id):
    """Edit a site."""
    site = get_site_by_id(site_id)
    if not site:
        flash('Site not found.', 'danger')
        return redirect(url_for('multi_entity.site_list'))

    if request.method == 'POST':
        data = {
            'site_name': request.form.get('site_name'),
            'short_name': request.form.get('short_name'),
            'site_type': request.form.get('site_type'),
            'site_subtype': request.form.get('site_subtype'),
            'description': request.form.get('description'),
            'address_line1': request.form.get('address_line1'),
            'address_line2': request.form.get('address_line2'),
            'city': request.form.get('city'),
            'district': request.form.get('district'),
            'country': request.form.get('country'),
            'postal_code': request.form.get('postal_code'),
            'phone': request.form.get('phone'),
            'mobile': request.form.get('mobile'),
            'fax': request.form.get('fax'),
            'email': request.form.get('email'),
            'contact_name': request.form.get('contact_name'),
            'contact_position': request.form.get('contact_position'),
            'contact_phone': request.form.get('contact_phone'),
            'contact_email': request.form.get('contact_email'),
            'site_area_sqm': request.form.get('site_area_sqm'),
            'covered_area_sqm': request.form.get('covered_area_sqm'),
            'yard_area_sqm': request.form.get('yard_area_sqm'),
            'capacity_pallets': request.form.get('capacity_pallets'),
            'capacity_items': request.form.get('capacity_items'),
            'is_shared': 1 if request.form.get('is_shared') else 0,
            'working_days': request.form.get('working_days'),
            'is_operational': 1 if request.form.get('is_operational') else 0,
            'status': request.form.get('status'),
            'site_manager_name': request.form.get('site_manager_name'),
            'site_manager_phone': request.form.get('site_manager_phone'),
            'site_manager_email': request.form.get('site_manager_email'),
            'notes': request.form.get('notes'),
        }

        try:
            update_site(site_id, data)
            log_change('site', site_id, 'UPDATE', entity_id=site['entity_id'],
                      notes=f'Updated site {data["site_name"]}')
            flash('Site updated successfully.', 'success')
            return redirect(url_for('multi_entity.site_detail', site_id=site_id))
        except Exception as e:
            flash(f'Error updating site: {str(e)}', 'danger')

    entity = get_entity_by_id(site['entity_id'])

    return render_template('multi_entity/sites/edit.html',
        page_title=f'Edit {site.get("site_name", "Site")}',
        site=site,
        entity=entity
    )


@multi_entity_bp.route('/sites/<int:site_id>/archive', methods=['POST'])
@require_multientity_access('delete')
def site_archive(site_id):
    """Archive a site."""
    site = get_site_by_id(site_id)
    try:
        archive_site(site_id, session.get('user_id'))
        log_change('site', site_id, 'ARCHIVE', entity_id=site['entity_id'] if site else None,
                  notes='Archived site')
        flash('Site archived successfully.', 'success')
    except Exception as e:
        flash(f'Error archiving site: {str(e)}', 'danger')

    return redirect(url_for('multi_entity.site_list'))


# =============================================================================
# ENTITY RELATIONSHIPS
# =============================================================================

@multi_entity_bp.route('/relationships')
@require_multientity_access('view')
def relationship_list():
    """List all entity relationships."""
    entity_id = request.args.get('entity_id', type=int)
    rel_type = request.args.get('type')

    relationships = get_entity_relationships(entity_id=entity_id, rel_type=rel_type)
    entities = get_all_entities(active_only=True)

    return render_template('multi_entity/relationships/list.html',
        page_title='Entity Relationships',
        relationships=relationships,
        entities=entities,
        selected_entity_id=entity_id,
        selected_rel_type=rel_type
    )


@multi_entity_bp.route('/relationships/create', methods=['GET', 'POST'])
@require_multientity_access('manage_intercompany')
def relationship_create():
    """Create a new entity relationship."""
    if request.method == 'POST':
        data = {
            'source_entity_id': request.form.get('source_entity_id'),
            'target_entity_id': request.form.get('target_entity_id'),
            'relationship_type': request.form.get('relationship_type'),
            'relationship_subtype': request.form.get('relationship_subtype'),
            'ownership_percentage': request.form.get('ownership_percentage'),
            'effective_date': request.form.get('effective_date'),
            'end_date': request.form.get('end_date'),
            'internal_pricing_policy': request.form.get('internal_pricing_policy'),
            'trade_terms': request.form.get('trade_terms'),
            'credit_limit': request.form.get('credit_limit', 0),
            'payment_terms': request.form.get('payment_terms'),
            'approval_required': 1 if request.form.get('approval_required') else 0,
            'notes': request.form.get('notes'),
            'created_by': session.get('user_id')
        }

        try:
            rel_id = create_relationship(data)
            log_change('relationship', rel_id, 'CREATE',
                      notes=f'Created {data["relationship_type"]} relationship')
            flash('Relationship created successfully.', 'success')
            return redirect(url_for('multi_entity.relationship_list'))
        except Exception as e:
            flash(f'Error creating relationship: {str(e)}', 'danger')

    entities = get_all_entities(active_only=True)

    return render_template('multi_entity/relationships/create.html',
        page_title='Create Entity Relationship',
        entities=entities
    )


# =============================================================================
# ACCESS SCOPES
# =============================================================================

@multi_entity_bp.route('/access')
@require_multientity_access('manage_scopes')
def access_list():
    """List all entity access assignments."""
    entity_id = request.args.get('entity_id', type=int)
    user_id = request.args.get('user_id', type=int)

    access_list = get_entity_access(entity_id=entity_id)
    entities = get_all_entities(active_only=True)

    # Get all users
    conn = get_db()
    try:
        users = [dict(row) for row in conn.execute("""
            SELECT id, username, email FROM users WHERE is_active = 1 ORDER BY username
        """).fetchall()]
    finally:
        conn.close()

    return render_template('multi_entity/access/list.html',
        page_title='Entity Access Scopes',
        access_list=access_list,
        entities=entities,
        users=users,
        selected_entity_id=entity_id,
        selected_user_id=user_id
    )


@multi_entity_bp.route('/access/assign', methods=['GET', 'POST'])
@require_multientity_access('manage_scopes')
def access_assign():
    """Assign entity access to a user."""
    if request.method == 'POST':
        data = {
            'user_id': request.form.get('user_id'),
            'entity_id': request.form.get('entity_id') or None,
            'branch_id': request.form.get('branch_id') or None,
            'site_id': request.form.get('site_id') or None,
            'group_id': request.form.get('group_id') or None,
            'access_level': request.form.get('access_level', 'read'),
            'access_scope': request.form.get('access_scope', 'entity'),
            'role_in_entity': request.form.get('role_in_entity', 'user'),
            'can_view_financials': 1 if request.form.get('can_view_financials') else 0,
            'can_approve_intercompany': 1 if request.form.get('can_approve_intercompany') else 0,
            'can_manage_users': 1 if request.form.get('can_manage_users') else 0,
            'can_manage_documents': 1 if request.form.get('can_manage_documents') else 0,
            'cross_entity_reporting': 1 if request.form.get('cross_entity_reporting') else 0,
            'is_default': 1 if request.form.get('is_default') else 0,
            'effective_from': request.form.get('effective_from') or None,
            'effective_to': request.form.get('effective_to') or None,
            'granted_by': session.get('user_id'),
            'notes': request.form.get('notes')
        }

        try:
            access_id = assign_entity_access(data)
            log_change('access', access_id, 'CREATE',
                      entity_id=data['entity_id'],
                      notes=f'Assigned {data["access_level"]} access to user {data["user_id"]}')
            flash('Entity access assigned successfully.', 'success')
            return redirect(url_for('multi_entity.access_list'))
        except Exception as e:
            flash(f'Error assigning access: {str(e)}', 'danger')

    entities = get_all_entities(active_only=True)
    groups = get_all_groups(active_only=True)

    conn = get_db()
    try:
        users = [dict(row) for row in conn.execute("""
            SELECT id, username, email FROM users WHERE is_active = 1 ORDER BY username
        """).fetchall()]
    finally:
        conn.close()

    return render_template('multi_entity/access/assign.html',
        page_title='Assign Entity Access',
        entities=entities,
        groups=groups,
        users=users
    )


@multi_entity_bp.route('/access/<int:access_id>/revoke', methods=['POST'])
@require_multientity_access('manage_scopes')
def access_revoke(access_id):
    """Revoke entity access."""
    reason = request.form.get('reason', '')

    try:
        revoke_entity_access(access_id, session.get('user_id'), reason)
        log_change('access', access_id, 'REVOKE', notes=f'Revoked access: {reason}')
        flash('Entity access revoked successfully.', 'success')
    except Exception as e:
        flash(f'Error revoking access: {str(e)}', 'danger')

    return redirect(url_for('multi_entity.access_list'))


# =============================================================================
# INTERCOMPANY RULES
# =============================================================================

@multi_entity_bp.route('/intercompany')
@require_multientity_access('manage_intercompany')
def intercompany_list():
    """List all intercompany rules."""
    entity_id = request.args.get('entity_id', type=int)

    rules = get_intercompany_rules(entity_id=entity_id)
    entities = get_all_entities(active_only=True)

    return render_template('multi_entity/intercompany/list.html',
        page_title='Intercompany Rules',
        rules=rules,
        entities=entities,
        selected_entity_id=entity_id
    )


@multi_entity_bp.route('/intercompany/create', methods=['GET', 'POST'])
@require_multientity_access('manage_intercompany')
def intercompany_create():
    """Create a new intercompany rule."""
    if request.method == 'POST':
        data = {
            'rule_code': request.form.get('rule_code'),
            'rule_name': request.form.get('rule_name'),
            'rule_type': request.form.get('rule_type'),
            'description': request.form.get('description'),
            'source_entity_id': request.form.get('source_entity_id') or None,
            'target_entity_id': request.form.get('target_entity_id') or None,
            'relationship_type': request.form.get('relationship_type'),
            'transaction_types': request.form.getlist('transaction_types'),
            'pricing_policy': request.form.get('pricing_policy'),
            'markup_percentage': request.form.get('markup_percentage'),
            'discount_percentage': request.form.get('discount_percentage'),
            'payment_terms': request.form.get('payment_terms'),
            'credit_limit': request.form.get('credit_limit', 0),
            'is_auto_approve': 1 if request.form.get('is_auto_approve') else 0,
            'is_active': 1 if request.form.get('is_active') else 0,
            'priority': request.form.get('priority', 0),
            'notes': request.form.get('notes'),
            'created_by': session.get('user_id')
        }

        try:
            rule_id = create_intercompany_rule(data)
            log_change('intercompany_rule', rule_id, 'CREATE',
                      notes=f'Created intercompany rule {data["rule_name"]}')
            flash('Intercompany rule created successfully.', 'success')
            return redirect(url_for('multi_entity.intercompany_list'))
        except Exception as e:
            flash(f'Error creating rule: {str(e)}', 'danger')

    entities = get_all_entities(active_only=True)

    return render_template('multi_entity/intercompany/create.html',
        page_title='Create Intercompany Rule',
        entities=entities
    )


# =============================================================================
# SHARED MASTER DATA RULES
# =============================================================================

@multi_entity_bp.route('/shared-data')
@require_multientity_access('view')
def shared_data_list():
    """List all shared master data rules."""
    data_type = request.args.get('type')
    scope = request.args.get('scope')

    rules = get_shared_data_rules(data_type=data_type, scope=scope)

    return render_template('multi_entity/shared_data/list.html',
        page_title='Shared Master Data Rules',
        rules=rules,
        selected_data_type=data_type,
        selected_scope=scope
    )


@multi_entity_bp.route('/shared-data/<int:rule_id>/edit', methods=['GET', 'POST'])
@require_multientity_access('edit')
def shared_data_edit(rule_id):
    """Edit a shared data rule."""
    rules = get_shared_data_rules()
    rule = next((r for r in rules if r['id'] == rule_id), None)

    if not rule:
        flash('Rule not found.', 'danger')
        return redirect(url_for('multi_entity.shared_data_list'))

    if request.method == 'POST':
        data = {
            'visibility': request.form.get('visibility'),
            'sharing_policy': request.form.get('sharing_policy'),
            'inheritance_mode': request.form.get('inheritance_mode'),
            'override_allowed': 1 if request.form.get('override_allowed') else 0,
            'override_requires_approval': 1 if request.form.get('override_requires_approval') else 0,
            'is_active': 1 if request.form.get('is_active') else 0,
            'description': request.form.get('description'),
        }

        try:
            update_shared_data_rule(rule_id, data)
            log_change('shared_rule', rule_id, 'UPDATE',
                      notes=f'Updated shared data rule for {rule["data_type"]}')
            flash('Shared data rule updated successfully.', 'success')
            return redirect(url_for('multi_entity.shared_data_list'))
        except Exception as e:
            flash(f'Error updating rule: {str(e)}', 'danger')

    return render_template('multi_entity/shared_data/edit.html',
        page_title='Edit Shared Data Rule',
        rule=rule
    )


# =============================================================================
# NUMBERING SCHEMES
# =============================================================================

@multi_entity_bp.route('/numbering')
@require_multientity_access('view')
def numbering_list():
    """List all numbering schemes."""
    entity_id = request.args.get('entity_id', type=int)

    schemes = get_numbering_schemes(entity_id=entity_id)
    entities = get_all_entities(active_only=True)

    return render_template('multi_entity/numbering/list.html',
        page_title='Entity Numbering Schemes',
        schemes=schemes,
        entities=entities,
        selected_entity_id=entity_id
    )


@multi_entity_bp.route('/numbering/create', methods=['GET', 'POST'])
@require_multientity_access('create')
def numbering_create():
    """Create a new numbering scheme."""
    if request.method == 'POST':
        data = {
            'entity_id': request.form.get('entity_id') or None,
            'group_id': request.form.get('group_id') or None,
            'document_type': request.form.get('document_type'),
            'scheme_code': request.form.get('scheme_code'),
            'scheme_name': request.form.get('scheme_name'),
            'prefix': request.form.get('prefix'),
            'prefix_type': request.form.get('prefix_type', 'fixed'),
            'include_group_code': 1 if request.form.get('include_group_code') else 0,
            'include_entity_code': 1 if request.form.get('include_entity_code') else 0,
            'include_branch_code': 1 if request.form.get('include_branch_code') else 0,
            'include_year': 1 if request.form.get('include_year') else 0,
            'include_month': 1 if request.form.get('include_month') else 0,
            'include_day': 1 if request.form.get('include_day') else 0,
            'year_format': request.form.get('year_format', 'YYYY'),
            'sequence_length': request.form.get('sequence_length', 5),
            'sequence_format': request.form.get('sequence_format', 'zero_padded'),
            'suffix': request.form.get('suffix'),
            'separator': request.form.get('separator', '-'),
            'reset_frequency': request.form.get('reset_frequency', 'yearly'),
            'notes': request.form.get('notes'),
            'created_by': session.get('user_id')
        }

        try:
            scheme_id = create_numbering_scheme(data)
            log_change('numbering_scheme', scheme_id, 'CREATE',
                      entity_id=data['entity_id'],
                      notes=f'Created numbering scheme {data["scheme_name"]}')
            flash('Numbering scheme created successfully.', 'success')
            return redirect(url_for('multi_entity.numbering_list'))
        except Exception as e:
            flash(f'Error creating scheme: {str(e)}', 'danger')

    entities = get_all_entities(active_only=True)
    groups = get_all_groups(active_only=True)

    return render_template('multi_entity/numbering/create.html',
        page_title='Create Numbering Scheme',
        entities=entities,
        groups=groups
    )


# =============================================================================
# ENTITY SCOPING ENGINE
# =============================================================================

@multi_entity_bp.route('/scope/switch', methods=['POST'])
def scope_switch():
    """Switch current entity context."""
    entity_id = request.form.get('entity_id', type=int)
    branch_id = request.form.get('branch_id', type=int)
    site_id = request.form.get('site_id', type=int)

    set_entity_context(entity_id, branch_id, site_id)

    return jsonify({
        'success': True,
        'message': 'Entity context updated',
        'entity_id': entity_id,
        'branch_id': branch_id,
        'site_id': site_id
    })


@multi_entity_bp.route('/scope/current')
def scope_current():
    """Get current entity scope."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    context = get_current_entity_context(user_id)
    favorites = get_user_favorite_entities(user_id)
    scope = get_user_entity_scope(user_id)

    return jsonify({
        'context': context,
        'favorites': favorites,
        'scope': scope
    })


@multi_entity_bp.route('/scope/favorites/add', methods=['POST'])
def add_favorite():
    """Add entity to favorites."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    entity_id = request.form.get('entity_id', type=int)
    group_id = request.form.get('group_id', type=int)

    add_favorite_entity(user_id, entity_id, group_id)

    return jsonify({'success': True})


# =============================================================================
# AUDIT & CHANGE HISTORY
# =============================================================================

@multi_entity_bp.route('/audit')
@require_multientity_access('audit_view')
def audit_list():
    """List all entity audit records."""
    entity_id = request.args.get('entity_id', type=int)
    entity_type = request.args.get('type')
    action = request.args.get('action')
    limit = request.args.get('limit', 100, type=int)

    audit_log = get_entity_audit_log(
        entity_id=entity_id,
        entity_type=entity_type,
        action=action,
        limit=limit
    )

    entities = get_all_entities(active_only=True)

    return render_template('multi_entity/audit/list.html',
        page_title='Entity Audit History',
        audit_log=audit_log,
        entities=entities,
        selected_entity_id=entity_id,
        selected_type=entity_type,
        selected_action=action
    )


# =============================================================================
# HIERARCHY VIEW
# =============================================================================

@multi_entity_bp.route('/hierarchy')
@require_multientity_access('view')
def hierarchy_view():
    """View entity hierarchy tree."""
    group_id = request.args.get('group_id', type=int)
    hierarchy = get_entity_hierarchy(group_id=group_id)
    groups = get_all_groups(active_only=True)

    return render_template('multi_entity/hierarchy.html',
        page_title='Entity Hierarchy',
        hierarchy=hierarchy,
        groups=groups,
        selected_group_id=group_id
    )


# =============================================================================
# REPORTS
# =============================================================================

@multi_entity_bp.route('/reports')
@require_multientity_access('view')
def reports_list():
    """List available reports."""
    return render_template('multi_entity/reports/list.html',
        page_title='Multi-Entity Reports'
    )


@multi_entity_bp.route('/reports/entity-register')
@require_multientity_access('view')
def report_entity_register():
    """Entity master register report."""
    entities = get_all_entities(active_only=False)
    groups = get_all_groups(active_only=True)

    # Apply filters
    group_id = request.args.get('group_id', type=int)
    status = request.args.get('status')

    if group_id:
        entities = [e for e in entities if e.get('parent_group_id') == group_id]
    if status:
        entities = [e for e in entities if e.get('status') == status]

    return render_template('multi_entity/reports/entity_register.html',
        page_title='Entity Master Register',
        entities=entities,
        groups=groups,
        selected_group_id=group_id,
        selected_status=status
    )


@multi_entity_bp.route('/reports/branch-register')
@require_multientity_access('view')
def report_branch_register():
    """Branch master register report."""
    branches = get_all_branches(active_only=False)
    entities = get_all_entities(active_only=True)

    return render_template('multi_entity/reports/branch_register.html',
        page_title='Branch Master Register',
        branches=branches,
        entities=entities
    )


@multi_entity_bp.route('/reports/site-register')
@require_multientity_access('view')
def report_site_register():
    """Site master register report."""
    sites = get_all_sites(active_only=False)
    entities = get_all_entities(active_only=True)

    return render_template('multi_entity/reports/site_register.html',
        page_title='Site Master Register',
        sites=sites,
        entities=entities
    )


@multi_entity_bp.route('/reports/access-matrix')
@require_multientity_access('manage_scopes')
def report_access_matrix():
    """User entity access matrix report."""
    conn = get_db()
    try:
        access_data = [dict(row) for row in conn.execute("""
            SELECT
                u.username,
                u.email,
                e.legal_name as entity_name,
                b.branch_name,
                s.site_name,
                ea.access_level,
                ea.role_in_entity,
                ea.can_view_financials,
                ea.can_approve_intercompany,
                ea.is_active
            FROM entity_access ea
            JOIN users u ON ea.user_id = u.id
            LEFT JOIN legal_entities e ON ea.entity_id = e.id
            LEFT JOIN entity_branches b ON ea.branch_id = b.id
            LEFT JOIN entity_sites s ON ea.site_id = s.id
            ORDER BY u.username, e.legal_name
        """).fetchall()]
    finally:
        conn.close()

    return render_template('multi_entity/reports/access_matrix.html',
        page_title='User Entity Access Matrix',
        access_data=access_data
    )


@multi_entity_bp.route('/reports/change-history')
@require_multientity_access('audit_view')
def report_change_history():
    """Entity change history report."""
    entity_id = request.args.get('entity_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    audit_log = get_entity_audit_log(entity_id=entity_id, limit=500)
    entities = get_all_entities(active_only=True)

    return render_template('multi_entity/reports/change_history.html',
        page_title='Entity Change History',
        audit_log=audit_log,
        entities=entities,
        selected_entity_id=entity_id
    )


# =============================================================================
# EXPORT CENTER
# =============================================================================

@multi_entity_bp.route('/export')
@require_multientity_access('export')
def export_center():
    """Export center for multi-entity data."""
    return render_template('multi_entity/export/index.html',
        page_title='Export Center'
    )


@multi_entity_bp.route('/export/entities')
@require_multientity_access('export')
def export_entities():
    """Export entities to CSV/Excel."""
    format_type = request.args.get('format', 'csv')
    entity_ids = request.args.getlist('entity_ids')

    entities = get_all_entities(active_only=False)

    if entity_ids:
        entities = [e for e in entities if e['id'] in [int(id) for id in entity_ids]]

    # Prepare data
    data = []
    for e in entities:
        data.append({
            'Entity Code': e.get('entity_code', ''),
            'Legal Name': e.get('legal_name', ''),
            'Short Name': e.get('short_name', ''),
            'Trade Name': e.get('trade_name', ''),
            'Entity Type': e.get('entity_type', ''),
            'Country': e.get('country', ''),
            'City': e.get('city', ''),
            'Status': e.get('status', ''),
            'Group': e.get('group_name', ''),
            'Default Currency': e.get('default_currency', ''),
            'Tax ID': e.get('tax_identification', ''),
            'VAT Number': e.get('vat_number', ''),
            'Registration Number': e.get('registration_number', ''),
            'Branch Count': e.get('branch_count', 0),
            'Site Count': e.get('site_count', 0),
            'Created At': e.get('created_at', ''),
        })

    if format_type == 'json':
        return jsonify(data)
    elif format_type == 'csv':
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        return Response(output.getvalue(), mimetype='text/csv',
                       headers={'Content-Disposition': 'attachment; filename=entities_export.csv'})
    else:
        # Excel format - return JSON for client-side processing
        return jsonify(data)


@multi_entity_bp.route('/export/branches')
@require_multientity_access('export')
def export_branches():
    """Export branches to CSV/Excel."""
    format_type = request.args.get('format', 'csv')
    branches = get_all_branches(active_only=False)

    data = []
    for b in branches:
        data.append({
            'Branch Code': b.get('branch_code', ''),
            'Branch Name': b.get('branch_name', ''),
            'Type': b.get('branch_type', ''),
            'Entity': b.get('entity_name', ''),
            'City': b.get('city', ''),
            'Country': b.get('country', ''),
            'Status': b.get('status', ''),
            'Is Head Office': 'Yes' if b.get('is_head_office') else 'No',
            'Contact': b.get('contact_name', ''),
            'Phone': b.get('phone', ''),
            'Email': b.get('email', ''),
        })

    if format_type == 'json':
        return jsonify(data)
    elif format_type == 'csv':
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        return Response(output.getvalue(), mimetype='text/csv',
                       headers={'Content-Disposition': 'attachment; filename=branches_export.csv'})
    else:
        return jsonify(data)


@multi_entity_bp.route('/export/sites')
@require_multientity_access('export')
def export_sites():
    """Export sites to CSV/Excel."""
    format_type = request.args.get('format', 'csv')
    sites = get_all_sites(active_only=False)

    data = []
    for s in sites:
        data.append({
            'Site Code': s.get('site_code', ''),
            'Site Name': s.get('site_name', ''),
            'Type': s.get('site_type', ''),
            'Entity': s.get('entity_name', ''),
            'Branch': s.get('branch_name', ''),
            'City': s.get('city', ''),
            'Country': s.get('country', ''),
            'Status': s.get('status', ''),
            'Is Shared': 'Yes' if s.get('is_shared') else 'No',
            'Area (sqm)': s.get('site_area_sqm', ''),
            'Capacity (Pallets)': s.get('capacity_pallets', ''),
        })

    if format_type == 'json':
        return jsonify(data)
    elif format_type == 'csv':
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        return Response(output.getvalue(), mimetype='text/csv',
                       headers={'Content-Disposition': 'attachment; filename=sites_export.csv'})
    else:
        return jsonify(data)


@multi_entity_bp.route('/export/audit')
@require_multientity_access('export')
def export_audit():
    """Export audit log to CSV/Excel."""
    format_type = request.args.get('format', 'csv')
    entity_id = request.args.get('entity_id', type=int)
    limit = request.args.get('limit', 500, type=int)

    audit_log = get_entity_audit_log(entity_id=entity_id, limit=limit)

    data = []
    for a in audit_log:
        data.append({
            'Timestamp': a.get('created_at', ''),
            'Entity Type': a.get('entity_type', ''),
            'Entity Name': a.get('entity_name', ''),
            'Action': a.get('action', ''),
            'Field': a.get('field_name', ''),
            'Old Value': a.get('old_value', ''),
            'New Value': a.get('new_value', ''),
            'User': a.get('user_name', ''),
            'Notes': a.get('notes', ''),
        })

    if format_type == 'json':
        return jsonify(data)
    elif format_type == 'csv':
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        return Response(output.getvalue(), mimetype='text/csv',
                       headers={'Content-Disposition': 'attachment; filename=audit_export.csv'})
    else:
        return jsonify(data)


# =============================================================================
# SETTINGS
# =============================================================================

@multi_entity_bp.route('/settings')
@require_multientity_access('settings')
def settings():
    """Multi-entity settings page."""
    return render_template('multi_entity/settings/index.html',
        page_title='Multi-Entity Settings'
    )


# =============================================================================
# SEARCH API
# =============================================================================

@multi_entity_bp.route('/api/search/entities')
def api_search_entities():
    """API endpoint for entity search."""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 20, type=int)

    if len(query) < 2:
        return jsonify([])

    results = search_entities(query, limit)
    return jsonify(results)


@multi_entity_bp.route('/api/search/branches')
def api_search_branches():
    """API endpoint for branch search."""
    query = request.args.get('q', '')
    entity_id = request.args.get('entity_id', type=int)
    limit = request.args.get('limit', 20, type=int)

    if len(query) < 2:
        return jsonify([])

    results = search_branches(query, entity_id, limit)
    return jsonify(results)


@multi_entity_bp.route('/api/search/sites')
def api_search_sites():
    """API endpoint for site search."""
    query = request.args.get('q', '')
    entity_id = request.args.get('entity_id', type=int)
    limit = request.args.get('limit', 20, type=int)

    if len(query) < 2:
        return jsonify([])

    results = search_sites(query, entity_id, limit)
    return jsonify(results)


@multi_entity_bp.route('/api/next-number')
def api_next_number():
    """API endpoint to get next document number."""
    entity_id = request.args.get('entity_id', type=int)
    document_type = request.args.get('document_type', 'invoice')

    if not entity_id:
        return jsonify({'error': 'Entity ID required'}), 400

    number = get_next_entity_number(entity_id, document_type)
    return jsonify({'number': number})
