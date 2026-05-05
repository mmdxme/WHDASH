"""
Organizational Planning & BPM Routes
=====================================
Comprehensive Flask routes for the Organizational Planning & BPM platform.

Routes cover:
- Dashboard
- Organizational Structure (companies, org units, hierarchy)
- Positions & Roles
- Reporting Lines
- Headcount & Workforce Planning
- Delegation & Substitution
- Approval Matrix
- Workflow Designer
- Process Instances
- SLA & Escalation
- Automation Rules
- Process Monitoring
- Simulations
- Reports
- Settings
"""

import json
from datetime import datetime, date, timedelta
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database import get_one, get_all, get_db_context
from org_planning_models import (
    get_companies, get_company, create_company,
    get_org_units, get_org_unit, get_org_unit_tree, create_org_unit, update_org_unit,
    get_positions, get_position, create_position,
    get_reporting_lines, create_reporting_line, detect_circular_reporting,
    get_headcount_plans, get_headcount_metrics, create_headcount_plan,
    get_delegations, create_delegation, check_delegation_conflict,
    get_approval_matrices, get_approval_matrix_steps, create_approval_matrix, add_approval_matrix_step, find_approval_route,
    get_workflow_definitions, get_workflow_definition, create_workflow_definition,
    get_workflow_steps, add_workflow_step, add_workflow_transition,
    get_process_instances, create_process_instance, perform_instance_action,
    get_sla_policies, create_sla_policy, calculate_sla_due_date,
    get_automation_rules, create_automation_rule, add_automation_condition, add_automation_action,
    get_simulation_scenarios, create_simulation_scenario, add_simulation_change, analyze_simulation_impacts,
    get_process_metrics, get_sla_compliance_stats, get_bottleneck_steps,
    create_notification, get_user_notifications, mark_notification_read,
    log_org_change, ORG_UNIT_TYPES, POSITION_LEVELS, EMPLOYMENT_TYPES,
    WORKFLOW_STATES, PROCESS_STATES, STEP_STATES, SLA_PRIORITIES,
    AUTOMATION_TRIGGERS, AUTOMATION_ACTIONS, DELEGATION_TYPES
)
from translations import get_translation, is_rtl, get_language_direction
from permissions import user_has_permission, get_user_permissions

# ============================================================================
# BLUEPRINT SETUP
# ============================================================================

org_planning_bp = Blueprint('org_planning', __name__, 
                           url_prefix='/org-planning',
                           template_folder='templates/org_planning')

def op_login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Please log in first.', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def op_permission_required(resource, action='view'):
    """Decorator to check module permissions."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                flash('Please log in first.', 'error')
                return redirect(url_for('login'))
            
            if not user_has_permission(user_id, 'org_planning', resource, action):
                flash(f"Access denied. You need '{action}' permission for '{resource}'.", "error")
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_user_language():
    """Get current user's language preference."""
    return session.get('language', 'en')

def t(key, lang=None):
    """Get translation for key."""
    if lang is None:
        lang = get_user_language()
    return get_translation(key, lang)

def get_current_user():
    """Get current user info."""
    if 'user_id' not in session:
        return None
    user = get_one("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    return user

def get_user_role():
    """Get current user's role."""
    user = get_current_user()
    if user:
        return user.get('role', 'user')
    return 'guest'

def is_admin():
    """Check if current user is admin."""
    role = get_user_role()
    return role in ['admin', 'super_admin']

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_module_stats():
    """Get dashboard statistics for the module."""
    user_id = session.get('user_id')
    
    # Count companies
    companies = get_companies()
    
    # Count org units
    org_units = get_org_units()
    
    # Count positions
    positions = get_positions()
    
    # Count delegations
    delegations = get_delegations(delegator_id=user_id) if user_id else []
    
    # Count workflows
    workflows = get_workflow_definitions(status='published')
    
    # Count process instances
    pending_instances = get_process_instances(status='in_progress')[:10]
    my_pending = get_process_instances(status='in_progress', assigned_to_id=user_id) if user_id else []
    
    # SLA compliance
    sla_stats = get_sla_compliance_stats()
    total_sla = sum(s['total_records'] or 0 for s in sla_stats)
    breached_sla = sum(s['breaches'] or 0 for s in sla_stats)
    compliance_pct = ((total_sla - breached_sla) / total_sla * 100) if total_sla > 0 else 100
    
    # Process metrics
    metrics = get_process_metrics(days=30)
    total_instances = sum(m['total_instances'] or 0 for m in metrics)
    completed = sum(m['completed'] or 0 for m in metrics)
    
    return {
        'companies': len(companies),
        'org_units': len(org_units),
        'positions': len(positions),
        'active_delegations': len(delegations),
        'active_workflows': len(workflows),
        'pending_instances': len(pending_instances),
        'my_pending_count': len(my_pending),
        'sla_compliance': round(compliance_pct, 1),
        'total_instances_30d': total_instances,
        'completed_30d': completed,
        'completion_rate': round((completed / total_instances * 100) if total_instances > 0 else 100, 1)
    }

def get_breadcrumbs(items):
    """Generate breadcrumb trail."""
    return items

# ============================================================================
# MAIN DASHBOARD ROUTE
# ============================================================================

@org_planning_bp.route('/')
@org_planning_bp.route('/dashboard')
@op_login_required
@op_permission_required('dashboard', 'view')
def dashboard():
    """Main Organizational Planning Dashboard."""
    user = get_current_user()
    lang = get_user_language()
    stats = get_module_stats()
    
    # Get recent notifications
    notifications = get_user_notifications(session['user_id'], limit=5)
    
    # Get pending approvals for current user
    my_pending = get_process_instances(status='in_progress', assigned_to_id=session['user_id'])
    
    # Get SLA-breached instances
    breached = get_process_instances(sla_breached=True)[:5]
    
    # Get bottleneck steps
    bottlenecks = get_bottleneck_steps(days=14)[:5]
    
    # Get process metrics
    metrics = get_process_metrics(days=30)
    
    return render_template('org_planning/dashboard.html',
        page_title=t('org_planning_dashboard', lang),
        lang=lang,
        stats=stats,
        notifications=notifications,
        my_pending=my_pending[:5],
        breached_instances=breached,
        bottlenecks=bottlenecks,
        metrics=metrics,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('dashboard', lang), 'url': '#'}
        ]
    )

# ============================================================================
# ORGANIZATIONAL STRUCTURE ROUTES
# ============================================================================

@org_planning_bp.route('/structure')
@org_planning_bp.route('/structure/')
@op_login_required
@op_permission_required('structure', 'view')
def structure():
    """Organizational Structure Overview."""
    user = get_current_user()
    lang = get_user_language()
    
    view_mode = request.args.get('view', 'tree')
    company_id = request.args.get('company', type=int)
    
    companies = get_companies()
    
    if view_mode == 'tree':
        if company_id:
            org_tree = get_org_unit_tree(company_id=company_id)
        else:
            org_tree = get_org_unit_tree(company_id=companies[0]['id'] if companies else 1)
        return render_template('org_planning/structure/tree.html',
            page_title=t('org_structure', lang),
            lang=lang,
            view_mode='tree',
            companies=companies,
            selected_company=company_id,
            org_tree=org_tree,
            org_unit_types=ORG_UNIT_TYPES,
            breadcrumbs=[
                {'label': t('home', lang), 'url': '/'},
                {'label': t('org_planning', lang), 'url': '/org-planning'},
                {'label': t('org_structure', lang), 'url': '#'}
            ]
        )
    elif view_mode == 'list':
        units = get_org_units(company_id=company_id)
        return render_template('org_planning/structure/list.html',
            page_title=t('org_structure', lang),
            lang=lang,
            view_mode='list',
            companies=companies,
            selected_company=company_id,
            units=units,
            org_unit_types=ORG_UNIT_TYPES,
            breadcrumbs=[
                {'label': t('home', lang), 'url': '/'},
                {'label': t('org_planning', lang), 'url': '/org-planning'},
                {'label': t('org_structure', lang), 'url': '#'}
            ]
        )
    else:
        return render_template('org_planning/structure/table.html',
            page_title=t('org_structure', lang),
            lang=lang,
            view_mode='table',
            companies=companies,
            selected_company=company_id,
            org_unit_types=ORG_UNIT_TYPES,
            breadcrumbs=[
                {'label': t('home', lang), 'url': '/'},
                {'label': t('org_planning', lang), 'url': '/org-planning'},
                {'label': t('org_structure', lang), 'url': '#'}
            ]
        )

@org_planning_bp.route('/structure/unit/<int:unit_id>')
@op_login_required
@op_permission_required('structure', 'view')
def structure_unit_detail(unit_id):
    """View details of a specific org unit."""
    user = get_current_user()
    lang = get_user_language()

    unit = get_org_unit(unit_id)
    if not unit:
        flash(t('org_unit_not_found', lang), 'error')
        return redirect(url_for('org_planning.structure'))

    # Check if user has access to this company's org structure
    if unit.get('company_id'):
        user_companies = get_all("""
            SELECT company_id FROM op_org_unit_access
            WHERE user_id = ? AND company_id = ?
        """, (session['user_id'], unit['company_id']))
        if not user_companies and not is_admin():
            flash(t('access_denied_unit', lang), 'error')
            return redirect(url_for('org_planning.structure'))

    # Get child units
    children = get_org_units(parent_id=unit_id)
    
    # Get positions in this unit
    positions = get_positions(org_unit_id=unit_id)
    
    # Get headcount metrics
    headcount = get_headcount_metrics(org_unit_id=unit_id)
    
    # Get parent chain
    parent_chain = []
    current = unit
    while current and current.get('parent_id'):
        parent = get_org_unit(current['parent_id'])
        if parent:
            parent_chain.append(parent)
            current = parent
        else:
            break
    
    return render_template('org_planning/structure/unit_detail.html',
        page_title=unit['name'],
        unit=unit,
        children=children,
        positions=positions,
        headcount=headcount[0] if headcount else None,
        parent_chain=parent_chain,
        org_unit_types=ORG_UNIT_TYPES,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('org_structure', lang), 'url': '/org-planning/structure'},
            {'label': unit['name'], 'url': '#'}
        ]
    )

@org_planning_bp.route('/structure/unit/create', methods=['GET', 'POST'])
@op_login_required
@op_permission_required('structure', 'create')
def structure_create_unit():
    """Create a new organizational unit."""
    lang = get_user_language()
    
    if request.method == 'POST':
        company_id = request.form.get('company_id', type=int)
        parent_id = request.form.get('parent_id', type=int)
        unit_type = request.form.get('unit_type')
        name = request.form.get('name')
        code = request.form.get('code')
        description = request.form.get('description')
        cost_center = request.form.get('cost_center')
        budget = request.form.get('budget', type=float, default=0)
        location = request.form.get('location')
        address = request.form.get('address')
        
        if not all([company_id, unit_type, name]):
            flash('Company, unit type, and name are required.', 'error')
            return redirect(request.url)
        
        unit_id = create_org_unit(
            company_id=company_id,
            unit_type=unit_type,
            name=name,
            name_ar=request.form.get('name_ar'),
            name_fa=request.form.get('name_fa'),
            parent_id=parent_id if parent_id else None,
            code=code,
            description=description,
            cost_center=cost_center,
            budget=budget,
            location=location,
            address=address,
            phone=request.form.get('phone'),
            email=request.form.get('email')
        )
        
        log_org_change('org_unit', unit_id, 'create', session['user_id'],
                      change_reason='Created new org unit', 
                      data_json={'name': name, 'unit_type': unit_type})
        
        flash(f'Organization unit "{name}" created successfully.', 'success')
        return redirect(url_for('org_planning.structure_unit_detail', unit_id=unit_id))
    
    companies = get_companies()
    return render_template('org_planning/structure/create_unit.html',
        page_title=t('create_org_unit', lang),
        lang=lang,
        companies=companies,
        org_unit_types=ORG_UNIT_TYPES,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('org_structure', lang), 'url': '/org-planning/structure'},
            {'label': t('create_org_unit', lang), 'url': '#'}
        ]
    )

@org_planning_bp.route('/structure/unit/<int:unit_id>/edit', methods=['GET', 'POST'])
@op_login_required
@op_permission_required('structure', 'edit')
def structure_edit_unit(unit_id):
    """Edit an organizational unit."""
    lang = get_user_language()
    unit = get_org_unit(unit_id)
    
    if not unit:
        flash('Organization unit not found.', 'error')
        return redirect(url_for('org_planning.structure'))
    
    if request.method == 'POST':
        update_org_unit(unit_id,
            name=request.form.get('name'),
            name_ar=request.form.get('name_ar'),
            name_fa=request.form.get('name_fa'),
            code=request.form.get('code'),
            description=request.form.get('description'),
            cost_center=request.form.get('cost_center'),
            budget=request.form.get('budget', type=float),
            location=request.form.get('location'),
            address=request.form.get('address'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            head_position_id=request.form.get('head_position_id', type=int),
            head_employee_id=request.form.get('head_employee_id', type=int),
            is_active=request.form.get('is_active') == '1'
        )
        
        log_org_change('org_unit', unit_id, 'update', session['user_id'],
                      change_reason='Updated org unit')
        
        flash('Organization unit updated successfully.', 'success')
        return redirect(url_for('org_planning.structure_unit_detail', unit_id=unit_id))
    
    companies = get_companies()
    return render_template('org_planning/structure/edit_unit.html',
        page_title=t('edit_org_unit', lang),
        lang=lang,
        unit=unit,
        companies=companies,
        org_unit_types=ORG_UNIT_TYPES,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('org_structure', lang), 'url': '/org-planning/structure'},
            {'label': unit['name'], 'url': url_for('org_planning.structure_unit_detail', unit_id=unit_id)},
            {'label': t('edit', lang), 'url': '#'}
        ]
    )

# ============================================================================
# COMPANIES ROUTES
# ============================================================================

@org_planning_bp.route('/companies')
@op_login_required
@op_permission_required('companies', 'view')
def companies():
    """List all companies."""
    lang = get_user_language()
    companies_list = get_companies(active_only=False)
    
    return render_template('org_planning/companies/list.html',
        page_title=t('companies', lang),
        lang=lang,
        companies=companies_list,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('companies', lang), 'url': '#'}
        ]
    )

@org_planning_bp.route('/companies/<int:company_id>')
@op_login_required
@op_permission_required('companies', 'view')
def company_detail(company_id):
    """View company details."""
    lang = get_user_language()
    company = get_company(company_id)
    
    if not company:
        flash('Company not found.', 'error')
        return redirect(url_for('org_planning.companies'))
    
    # Get org units for this company
    units = get_org_units(company_id=company_id)
    
    # Get children companies
    children = get_all("SELECT * FROM op_companies WHERE parent_company_id = ?", (company_id,))
    
    return render_template('org_planning/companies/detail.html',
        page_title=company['name'],
        company=company,
        org_units=units,
        child_companies=children,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('companies', lang), 'url': '/org-planning/companies'},
            {'label': company['name'], 'url': '#'}
        ]
    )

@org_planning_bp.route('/companies/create', methods=['GET', 'POST'])
@op_login_required
@op_permission_required('companies', 'create')
def company_create():
    """Create a new company."""
    lang = get_user_language()
    
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        
        if not all([name, code]):
            flash('Company name and code are required.', 'error')
            return redirect(request.url)
        
        company_id = create_company(
            name=name,
            code=code,
            name_ar=request.form.get('name_ar'),
            name_fa=request.form.get('name_fa'),
            registration_number=request.form.get('registration_number'),
            tax_id=request.form.get('tax_id'),
            address=request.form.get('address'),
            city=request.form.get('city'),
            country=request.form.get('country'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            website=request.form.get('website'),
            parent_company_id=request.form.get('parent_company_id', type=int)
        )
        
        flash(f'Company "{name}" created successfully.', 'success')
        return redirect(url_for('org_planning.company_detail', company_id=company_id))
    
    companies = get_companies()
    return render_template('org_planning/companies/create.html',
        page_title=t('create_company', lang),
        lang=lang,
        companies=companies,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('companies', lang), 'url': '/org-planning/companies'},
            {'label': t('create_company', lang), 'url': '#'}
        ]
    )

# ============================================================================
# POSITIONS & ROLES ROUTES
# ============================================================================

@org_planning_bp.route('/positions')
@op_login_required
@op_permission_required('positions', 'view')
def positions():
    """List all positions."""
    lang = get_user_language()
    
    org_unit_id = request.args.get('org_unit', type=int)
    level = request.args.get('level')
    
    positions_list = get_positions(org_unit_id=org_unit_id, level=level)
    org_units = get_org_units()
    
    return render_template('org_planning/positions/list.html',
        page_title=t('positions', lang),
        lang=lang,
        positions=positions_list,
        org_units=org_units,
        selected_org_unit=org_unit_id,
        selected_level=level,
        position_levels=POSITION_LEVELS,
        employment_types=EMPLOYMENT_TYPES,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('positions', lang), 'url': '#'}
        ]
    )

@org_planning_bp.route('/positions/<int:position_id>')
@op_login_required
@op_permission_required('positions', 'view')
def position_detail(position_id):
    """View position details."""
    lang = get_user_language()
    position = get_position(position_id)
    
    if not position:
        flash('Position not found.', 'error')
        return redirect(url_for('org_planning.positions'))
    
    # Get reporting line
    reporting_lines = get_reporting_lines(position_id=position_id)
    
    # Get subordinates (positions that report to this one)
    subordinates = get_all("""
        SELECT * FROM op_positions 
        WHERE reports_to_position_id = ? AND is_active = 1
    """, (position_id,))
    
    return render_template('org_planning/positions/detail.html',
        page_title=position['title'],
        position=position,
        reporting_lines=reporting_lines,
        subordinates=subordinates,
        position_levels=POSITION_LEVELS,
        employment_types=EMPLOYMENT_TYPES,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('positions', lang), 'url': '/org-planning/positions'},
            {'label': position['title'], 'url': '#'}
        ]
    )

@org_planning_bp.route('/positions/create', methods=['GET', 'POST'])
@op_login_required
@op_permission_required('positions', 'create')
def position_create():
    """Create a new position."""
    lang = get_user_language()
    
    if request.method == 'POST':
        title = request.form.get('title')
        level = request.form.get('level')
        org_unit_id = request.form.get('org_unit_id', type=int)
        
        if not all([title, level]):
            flash('Position title and level are required.', 'error')
            return redirect(request.url)
        
        position_id = create_position(
            org_unit_id=org_unit_id if org_unit_id else None,
            title=title,
            level=level,
            title_ar=request.form.get('title_ar'),
            title_fa=request.form.get('title_fa'),
            position_code=request.form.get('position_code'),
            grade=request.form.get('grade'),
            salary_band_min=request.form.get('salary_band_min', type=float),
            salary_band_max=request.form.get('salary_band_max', type=float),
            employment_type=request.form.get('employment_type'),
            headcount_approved=request.form.get('headcount_approved') == '1',
            headcount_budgeted=request.form.get('headcount_budgeted') == '1',
            is_critical=request.form.get('is_critical') == '1',
            is_supervisor=request.form.get('is_supervisor') == '1',
            requires_approval=request.form.get('requires_approval') == '1',
            parent_position_id=request.form.get('parent_position_id', type=int),
            reports_to_position_id=request.form.get('reports_to_position_id', type=int),
            responsibilities=request.form.get('responsibilities'),
            requirements=request.form.get('requirements'),
            skills_required=request.form.get('skills_required')
        )
        
        # Create reporting line if specified
        reports_to = request.form.get('reports_to_position_id', type=int)
        if reports_to:
            create_reporting_line(position_id, reports_to, 'direct')
        
        flash(f'Position "{title}" created successfully.', 'success')
        return redirect(url_for('org_planning.position_detail', position_id=position_id))
    
    org_units = get_org_units()
    positions = get_positions()
    return render_template('org_planning/positions/create.html',
        page_title=t('create_position', lang),
        lang=lang,
        org_units=org_units,
        positions=positions,
        position_levels=POSITION_LEVELS,
        employment_types=EMPLOYMENT_TYPES,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('positions', lang), 'url': '/org-planning/positions'},
            {'label': t('create_position', lang), 'url': '#'}
        ]
    )

# ============================================================================
# HEADCOUNT PLANNING ROUTES
# ============================================================================

@org_planning_bp.route('/headcount')
@op_login_required
@op_permission_required('headcount', 'view')
def headcount():
    """Headcount planning overview."""
    lang = get_user_language()
    
    plan_year = request.args.get('year', date.today().year, type=int)
    org_unit_id = request.args.get('org_unit', type=int)
    
    plans = get_headcount_plans(plan_year=plan_year)
    if org_unit_id:
        plans = [p for p in plans if p['org_unit_id'] == org_unit_id]
    
    metrics = get_headcount_metrics()
    
    return render_template('org_planning/headcount/list.html',
        page_title=t('headcount_planning', lang),
        lang=lang,
        plans=plans,
        metrics=metrics,
        selected_year=plan_year,
        selected_org_unit=org_unit_id,
        org_units=get_org_units(),
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('headcount_planning', lang), 'url': '#'}
        ]
    )

@org_planning_bp.route('/headcount/create', methods=['GET', 'POST'])
@op_login_required
@op_permission_required('headcount', 'create')
def headcount_create():
    """Create a headcount plan."""
    lang = get_user_language()
    
    if request.method == 'POST':
        org_unit_id = request.form.get('org_unit_id', type=int)
        plan_year = request.form.get('plan_year', date.today().year, type=int)
        
        plan_id = create_headcount_plan(
            org_unit_id=org_unit_id,
            position_id=request.form.get('position_id', type=int),
            plan_year=plan_year,
            plan_period=request.form.get('plan_period'),
            headcount_approved=request.form.get('headcount_approved', type=int),
            headcount_planned=request.form.get('headcount_planned', type=int),
            headcount_current=request.form.get('headcount_current', type=int),
            headcount_vacant=request.form.get('headcount_vacant', type=int),
            headcount_requested=request.form.get('headcount_requested', type=int),
            headcount_frozen=request.form.get('headcount_frozen', type=int),
            budget_allocated=request.form.get('budget_allocated', type=float),
            budget_used=request.form.get('budget_used', type=float),
            notes=request.form.get('notes'),
            status=request.form.get('status'),
            created_by=session['user_id']
        )
        
        flash('Headcount plan created successfully.', 'success')
        return redirect(url_for('org_planning.headcount'))
    
    return render_template('org_planning/headcount/create.html',
        page_title=t('create_headcount_plan', lang),
        lang=lang,
        org_units=get_org_units(),
        years=range(date.today().year - 2, date.today().year + 3),
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('headcount_planning', lang), 'url': '/org-planning/headcount'},
            {'label': t('create_headcount_plan', lang), 'url': '#'}
        ]
    )

# ============================================================================
# DELEGATION ROUTES
# ============================================================================

@org_planning_bp.route('/delegations')
@op_login_required
@op_permission_required('delegations', 'view')
def delegations():
    """List delegations."""
    lang = get_user_language()
    user_id = session['user_id']
    
    # Get delegations where user is delegator or delegate
    my_delegations = get_delegations(delegator_id=user_id)
    delegated_to_me = get_delegations(delegate_id=user_id)
    
    return render_template('org_planning/delegations/list.html',
        page_title=t('delegations', lang),
        lang=lang,
        my_delegations=my_delegations,
        delegated_to_me=delegated_to_me,
        delegation_types=DELEGATION_TYPES,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('delegations', lang), 'url': '#'}
        ]
    )

@org_planning_bp.route('/delegations/create', methods=['GET', 'POST'])
@op_login_required
@op_permission_required('delegations', 'create')
def delegation_create():
    """Create a delegation."""
    lang = get_user_language()
    
    if request.method == 'POST':
        delegate_id = request.form.get('delegate_id', type=int)
        delegation_type = request.form.get('delegation_type')
        
        if delegate_id == session['user_id']:
            flash('You cannot delegate to yourself.', 'error')
            return redirect(request.url)
        
        # Check for conflicts
        conflict = check_delegation_conflict(session['user_id'], delegate_id)
        if conflict:
            flash('An active delegation to this user already exists.', 'warning')
        
        delegation_id = create_delegation(
            delegator_id=session['user_id'],
            delegate_id=delegate_id,
            delegation_type=delegation_type,
            scope=request.form.get('scope'),
            modules=request.form.getlist('modules'),
            transaction_types=request.form.getlist('transaction_types'),
            limit_amount=request.form.get('limit_amount', type=float),
            currency=request.form.get('currency'),
            priority=request.form.get('priority', type=int, default=1),
            reason=request.form.get('reason'),
            start_date=request.form.get('start_date'),
            end_date=request.form.get('end_date')
        )
        
        flash('Delegation created successfully.', 'success')
        return redirect(url_for('org_planning.delegations'))
    
    # Get all users except current
    users = get_all("""
        SELECT id, full_name, email FROM users 
        WHERE id != ? AND is_active = 1
        ORDER BY full_name
    """, (session['user_id'],))
    
    return render_template('org_planning/delegations/create.html',
        page_title=t('create_delegation', lang),
        lang=lang,
        users=users,
        delegation_types=DELEGATION_TYPES,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('delegations', lang), 'url': '/org-planning/delegations'},
            {'label': t('create_delegation', lang), 'url': '#'}
        ]
    )

# ============================================================================
# APPROVAL MATRIX ROUTES
# ============================================================================

@org_planning_bp.route('/approvals')
@op_login_required
@op_permission_required('approval_matrix', 'view')
def approval_matrix():
    """Approval matrix overview."""
    lang = get_user_language()
    
    module = request.args.get('module')
    matrices = get_approval_matrices(module=module)
    
    return render_template('org_planning/approvals/list.html',
        page_title=t('approval_matrix', lang),
        lang=lang,
        matrices=matrices,
        selected_module=module,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('approval_matrix', lang), 'url': '#'}
        ]
    )

@org_planning_bp.route('/approvals/create', methods=['GET', 'POST'])
@op_login_required
@op_permission_required('approval_matrix', 'create')
def approval_matrix_create():
    """Create an approval matrix."""
    lang = get_user_language()
    
    if request.method == 'POST':
        name = request.form.get('name')
        module = request.form.get('module')
        document_type = request.form.get('document_type')
        
        matrix_id = create_approval_matrix(
            name=name,
            name_ar=request.form.get('name_ar'),
            name_fa=request.form.get('name_fa'),
            module=module,
            document_type=document_type,
            approval_type=request.form.get('approval_type'),
            min_amount=request.form.get('min_amount', type=float, default=0),
            max_amount=request.form.get('max_amount', type=float, default=999999999),
            currency=request.form.get('currency', default='USD'),
            conditions={'conditions': []},
            priority=request.form.get('priority', type=int, default=1)
        )
        
        # Add approval steps
        step_count = request.form.get('step_count', type=int, default=0)
        for i in range(step_count):
            add_approval_matrix_step(
                matrix_id=matrix_id,
                step_order=i + 1,
                approver_type=request.form.get(f'step_{i}_type'),
                approver_id=request.form.get(f'step_{i}_user', type=int),
                approver_role=request.form.get(f'step_{i}_role'),
                approval_level=request.form.get(f'step_{i}_level', type=int, default=1),
                is_final=request.form.get(f'step_{i}_final') == '1',
                skip_if_no_approver=request.form.get(f'step_{i}_skip') == '1'
            )
        
        flash(f'Approval matrix "{name}" created successfully.', 'success')
        return redirect(url_for('org_planning.approval_matrix'))
    
    return render_template('org_planning/approvals/create.html',
        page_title=t('create_approval_matrix', lang),
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('approval_matrix', lang), 'url': '/org-planning/approvals'},
            {'label': t('create_approval_matrix', lang), 'url': '#'}
        ]
    )

# ============================================================================
# WORKFLOW/BPM ROUTES
# ============================================================================

@org_planning_bp.route('/workflows')
@op_login_required
@op_permission_required('workflows', 'view')
def workflows():
    """List workflow definitions."""
    lang = get_user_language()
    
    category = request.args.get('category')
    workflows_list = get_workflow_definitions(category=category)
    
    return render_template('org_planning/workflows/list.html',
        page_title=t('workflows', lang),
        lang=lang,
        workflows=workflows_list,
        selected_category=category,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('workflows', lang), 'url': '#'}
        ]
    )

@org_planning_bp.route('/workflows/<int:workflow_id>')
@op_login_required
@op_permission_required('workflows', 'view')
def workflow_detail(workflow_id):
    """View workflow definition details."""
    lang = get_user_language()
    workflow = get_workflow_definition(workflow_id)
    
    if not workflow:
        flash('Workflow not found.', 'error')
        return redirect(url_for('org_planning.workflows'))
    
    steps = get_workflow_steps(workflow_id)
    
    return render_template('org_planning/workflows/detail.html',
        page_title=workflow['name'],
        workflow=workflow,
        steps=steps,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('workflows', lang), 'url': '/org-planning/workflows'},
            {'label': workflow['name'], 'url': '#'}
        ]
    )

@org_planning_bp.route('/workflows/create', methods=['GET', 'POST'])
@op_login_required
@op_permission_required('workflows', 'create')
def workflow_create():
    """Create a new workflow definition."""
    lang = get_user_language()
    
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        category = request.form.get('category')
        module = request.form.get('module')
        
        workflow_id = create_workflow_definition(
            name=name,
            name_ar=request.form.get('name_ar'),
            name_fa=request.form.get('name_fa'),
            code=code,
            description=request.form.get('description'),
            category=category,
            module=module,
            entity_type=request.form.get('entity_type'),
            estimated_duration_hours=request.form.get('estimated_duration_hours', type=int),
            risk_level=request.form.get('risk_level', default='medium'),
            owner_id=session['user_id']
        )
        
        # Add steps from form
        step_count = request.form.get('step_count', type=int, default=0)
        prev_step_id = None
        for i in range(step_count):
            step_id = add_workflow_step(
                workflow_definition_id=workflow_id,
                step_key=request.form.get(f'step_{i}_key'),
                name=request.form.get(f'step_{i}_name'),
                name_ar=request.form.get(f'step_{i}_name_ar'),
                step_type=request.form.get(f'step_{i}_type'),
                description=request.form.get(f'step_{i}_desc'),
                assignee_type=request.form.get(f'step_{i}_assignee_type'),
                assignee_role=request.form.get(f'step_{i}_role'),
                timeout_hours=request.form.get(f'step_{i}_timeout', type=int, default=24),
                sort_order=i
            )
            
            if prev_step_id:
                add_workflow_transition(
                    workflow_definition_id=workflow_id,
                    from_step_id=prev_step_id,
                    to_step_id=step_id
                )
            
            prev_step_id = step_id
        
        flash(f'Workflow "{name}" created successfully.', 'success')
        return redirect(url_for('org_planning.workflow_detail', workflow_id=workflow_id))
    
    return render_template('org_planning/workflows/create.html',
        page_title=t('create_workflow', lang),
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('workflows', lang), 'url': '/org-planning/workflows'},
            {'label': t('create_workflow', lang), 'url': '#'}
        ]
    )

# ============================================================================
# PROCESS INSTANCES ROUTES
# ============================================================================

@org_planning_bp.route('/processes')
@op_login_required
@op_permission_required('processes', 'view')
def processes():
    """List process instances."""
    lang = get_user_language()
    user_id = session['user_id']
    
    status = request.args.get('status')
    view = request.args.get('view', 'all')
    
    if view == 'my_work':
        instances = get_process_instances(status='in_progress', assigned_to_id=user_id)
    elif view == 'my_requests':
        instances = get_process_instances(requester_id=user_id)
    elif view == 'pending':
        instances = get_process_instances(status='in_progress')
    elif view == 'completed':
        instances = get_process_instances(status='completed')
    else:
        instances = get_process_instances()
    
    if status:
        instances = [i for i in instances if i['status'] == status]
    
    return render_template('org_planning/processes/list.html',
        page_title=t('process_instances', lang),
        lang=lang,
        instances=instances,
        selected_view=view,
        selected_status=status,
        process_states=PROCESS_STATES,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('process_instances', lang), 'url': '#'}
        ]
    )

@org_planning_bp.route('/processes/<int:instance_id>')
@op_login_required
@op_permission_required('processes', 'view')
def process_detail(instance_id):
    """View process instance details."""
    lang = get_user_language()
    
    instance = get_one("""
        SELECT pi.*, wd.name as workflow_name, wd.category
        FROM op_process_instances pi
        LEFT JOIN op_workflow_definitions wd ON pi.workflow_definition_id = wd.id
        WHERE pi.id = ?
    """, (instance_id,))
    
    if not instance:
        flash('Process instance not found.', 'error')
        return redirect(url_for('org_planning.processes'))
    
    # Get instance actions
    actions = get_all("""
        SELECT * FROM op_instance_actions 
        WHERE instance_id = ? ORDER BY created_at DESC
    """, (instance_id,))
    
    # Get comments
    comments = get_all("""
        SELECT * FROM op_instance_comments 
        WHERE instance_id = ? ORDER BY created_at DESC
    """, (instance_id,))
    
    return render_template('org_planning/processes/detail.html',
        page_title=instance['title'],
        instance=instance,
        actions=actions,
        comments=comments,
        process_states=PROCESS_STATES,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('process_instances', lang), 'url': '/org-planning/processes'},
            {'label': instance['title'][:50], 'url': '#'}
        ]
    )

@org_planning_bp.route('/processes/<int:instance_id>/action', methods=['POST'])
@op_login_required
@op_permission_required('processes', 'edit')
def process_action(instance_id):
    """Perform an action on a process instance."""
    lang = get_user_language()
    
    action = request.form.get('action')
    comments = request.form.get('comments')
    
    user = get_current_user()
    
    new_status = perform_instance_action(
        instance_id=instance_id,
        action_type=action,
        performed_by=session['user_id'],
        performed_by_name=user['full_name'] if user else 'Unknown',
        comments=comments
    )
    
    if new_status:
        flash(f'Action "{action}" completed successfully.', 'success')
        
        # Create notification for relevant parties
        instance = get_one("SELECT * FROM op_process_instances WHERE id = ?", (instance_id,))
        if instance and instance['requester_id']:
            create_notification(
                user_id=instance['requester_id'],
                notification_type='process_update',
                title=f'Process {action.capitalize()}',
                message=f'Your request "{instance["title"]}" has been {action.capitalize()}d.',
                reference_type='process_instance',
                reference_id=instance_id,
                priority='high' if action in ['reject', 'return'] else 'medium'
            )
    else:
        flash('Failed to perform action.', 'error')
    
    return redirect(url_for('org_planning.process_detail', instance_id=instance_id))

@org_planning_bp.route('/processes/start', methods=['GET', 'POST'])
@op_login_required
@op_permission_required('processes', 'create')
def process_start():
    """Start a new process instance."""
    lang = get_user_language()
    
    if request.method == 'POST':
        workflow_id = request.form.get('workflow_id', type=int)
        title = request.form.get('title')
        
        if not all([workflow_id, title]):
            flash('Workflow and title are required.', 'error')
            return redirect(request.url)
        
        instance_id = create_process_instance(
            workflow_definition_id=workflow_id,
            title=title,
            description=request.form.get('description'),
            priority=request.form.get('priority', default='medium'),
            requester_id=session['user_id'],
            requester_name=get_current_user()['full_name'] if get_current_user() else None,
            reference_id=request.form.get('reference_id'),
            reference_type=request.form.get('reference_type'),
            metadata_json={'source': 'org_planning'}
        )
        
        flash(f'Process "{title}" started successfully.', 'success')
        return redirect(url_for('org_planning.process_detail', instance_id=instance_id))
    
    workflows = get_workflow_definitions(status='published')
    return render_template('org_planning/processes/start.html',
        page_title=t('start_process', lang),
        lang=lang,
        workflows=workflows,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('process_instances', lang), 'url': '/org-planning/processes'},
            {'label': t('start_process', lang), 'url': '#'}
        ]
    )

# ============================================================================
# SLA & ESCALATION ROUTES
# ============================================================================

@org_planning_bp.route('/sla')
@op_login_required
@op_permission_required('sla', 'view')
def sla():
    """SLA policies overview."""
    lang = get_user_language()
    
    module = request.args.get('module')
    policies = get_sla_policies(module=module)
    
    return render_template('org_planning/sla/list.html',
        page_title=t('sla_policies', lang),
        lang=lang,
        policies=policies,
        selected_module=module,
        sla_priorities=SLA_PRIORITIES,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('sla_policies', lang), 'url': '#'}
        ]
    )

@org_planning_bp.route('/sla/create', methods=['GET', 'POST'])
@op_login_required
@op_permission_required('sla', 'create')
def sla_create():
    """Create an SLA policy."""
    lang = get_user_language()
    
    if request.method == 'POST':
        name = request.form.get('name')
        module = request.form.get('module')
        
        policy_id = create_sla_policy(
            name=name,
            name_ar=request.form.get('name_ar'),
            name_fa=request.form.get('name_fa'),
            module=module,
            document_type=request.form.get('document_type'),
            priority=request.form.get('priority', default='medium'),
            response_hours=request.form.get('response_hours', type=int, default=24),
            resolution_hours=request.form.get('resolution_hours', type=int, default=72),
            warning_threshold_pct=request.form.get('warning_threshold_pct', type=int, default=75),
            pause_on_holidays=request.form.get('pause_on_holidays') == '1',
            auto_escalate=request.form.get('auto_escalate') == '1',
            business_hours_only=request.form.get('business_hours_only') == '1',
            working_days=request.form.get('working_days', default='1,2,3,4,5'),
            working_start_time=request.form.get('working_start_time', default='09:00'),
            working_end_time=request.form.get('working_end_time', default='18:00')
        )
        
        flash(f'SLA policy "{name}" created successfully.', 'success')
        return redirect(url_for('org_planning.sla'))
    
    return render_template('org_planning/sla/create.html',
        page_title=t('create_sla_policy', lang),
        lang=lang,
        sla_priorities=SLA_PRIORITIES,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('sla_policies', lang), 'url': '/org-planning/sla'},
            {'label': t('create_sla_policy', lang), 'url': '#'}
        ]
    )

@org_planning_bp.route('/escalations')
@op_login_required
@op_permission_required('escalations', 'view')
def escalations():
    """View escalation logs."""
    lang = get_user_language()
    
    logs = get_all("""
        SELECT el.*, pi.title as instance_title, pi.reference_type
        FROM op_escalation_logs el
        LEFT JOIN op_process_instances pi ON el.instance_id = pi.id
        ORDER BY el.created_at DESC
        LIMIT 100
    """)
    
    return render_template('org_planning/escalations/list.html',
        page_title=t('escalations', lang),
        lang=lang,
        logs=logs,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('escalations', lang), 'url': '#'}
        ]
    )

# ============================================================================
# AUTOMATION RULES ROUTES
# ============================================================================

@org_planning_bp.route('/automation')
@op_login_required
@op_permission_required('automation', 'view')
def automation():
    """List automation rules."""
    lang = get_user_language()
    
    module = request.args.get('module')
    trigger = request.args.get('trigger')
    
    rules = get_automation_rules(module=module, trigger_type=trigger)
    
    return render_template('org_planning/automation/list.html',
        page_title=t('automation_rules', lang),
        lang=lang,
        rules=rules,
        selected_module=module,
        selected_trigger=trigger,
        automation_triggers=AUTOMATION_TRIGGERS,
        automation_actions=AUTOMATION_ACTIONS,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('automation_rules', lang), 'url': '#'}
        ]
    )

@org_planning_bp.route('/automation/create', methods=['GET', 'POST'])
@op_login_required
@op_permission_required('automation', 'create')
def automation_create():
    """Create an automation rule."""
    lang = get_user_language()
    
    if request.method == 'POST':
        name = request.form.get('name')
        module = request.form.get('module')
        trigger_type = request.form.get('trigger_type')
        
        rule_id = create_automation_rule(
            name=name,
            name_ar=request.form.get('name_ar'),
            name_fa=request.form.get('name_fa'),
            description=request.form.get('description'),
            module=module,
            trigger_type=trigger_type,
            trigger_condition={'field': request.form.get('condition_field'),
                              'operator': request.form.get('condition_operator'),
                              'value': request.form.get('condition_value')},
            schedule_cron=request.form.get('schedule_cron'),
            priority=request.form.get('priority', type=int, default=1),
            created_by=session['user_id']
        )
        
        # Add conditions
        condition_count = request.form.get('condition_count', type=int, default=0)
        for i in range(condition_count):
            add_automation_condition(
                rule_id=rule_id,
                field_name=request.form.get(f'cond_{i}_field'),
                operator=request.form.get(f'cond_{i}_operator'),
                field_value=request.form.get(f'cond_{i}_value'),
                condition_group=request.form.get(f'cond_{i}_group', default='all'),
                sort_order=i
            )
        
        # Add actions
        action_count = request.form.get('action_count', type=int, default=0)
        for i in range(action_count):
            add_automation_action(
                rule_id=rule_id,
                action_type=request.form.get(f'action_{i}_type'),
                action_config={'config': request.form.get(f'action_{i}_config')},
                execution_order=i + 1,
                continue_on_failure=request.form.get(f'action_{i}_continue') == '1'
            )
        
        flash(f'Automation rule "{name}" created successfully.', 'success')
        return redirect(url_for('org_planning.automation'))
    
    return render_template('org_planning/automation/create.html',
        page_title=t('create_automation', lang),
        lang=lang,
        automation_triggers=AUTOMATION_TRIGGERS,
        automation_actions=AUTOMATION_ACTIONS,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('automation_rules', lang), 'url': '/org-planning/automation'},
            {'label': t('create_automation', lang), 'url': '#'}
        ]
    )

# ============================================================================
# MONITORING & ANALYTICS ROUTES
# ============================================================================

@org_planning_bp.route('/monitoring')
@op_login_required
@op_permission_required('monitoring', 'view')
def monitoring():
    """Process monitoring dashboard."""
    lang = get_user_language()
    
    metrics = get_process_metrics(days=30)
    sla_stats = get_sla_compliance_stats()
    bottlenecks = get_bottleneck_steps(days=30)
    
    # Calculate summary stats
    total_instances = sum(m['total_instances'] or 0 for m in metrics)
    completed = sum(m['completed'] or 0 for m in metrics)
    rejected = sum(m['rejected'] or 0 for m in metrics)
    avg_completion = sum(m['avg_hours'] or 0 for m in metrics) / len(metrics) if metrics else 0
    
    total_sla = sum(s['total_records'] or 0 for s in sla_stats)
    breached_sla = sum(s['breaches'] or 0 for s in sla_stats)
    
    return render_template('org_planning/monitoring/dashboard.html',
        page_title=t('process_monitoring', lang),
        lang=lang,
        metrics=metrics,
        sla_stats=sla_stats,
        bottlenecks=bottlenecks,
        summary={
            'total_instances': total_instances,
            'completed': completed,
            'rejected': rejected,
            'avg_completion_hours': round(avg_completion, 1),
            'sla_compliance': round((total_sla - breached_sla) / total_sla * 100, 1) if total_sla > 0 else 100,
            'total_sla_records': total_sla
        },
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('process_monitoring', lang), 'url': '#'}
        ]
    )

@org_planning_bp.route('/monitoring/bottlenecks')
@op_login_required
@op_permission_required('monitoring', 'view')
def monitoring_bottlenecks():
    """Bottleneck analysis."""
    lang = get_user_language()
    
    days = request.args.get('days', 30, type=int)
    bottlenecks = get_bottleneck_steps(days=days)
    
    return render_template('org_planning/monitoring/bottlenecks.html',
        page_title=t('bottleneck_analysis', lang),
        lang=lang,
        bottlenecks=bottlenecks,
        days=days,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('monitoring', lang), 'url': '/org-planning/monitoring'},
            {'label': t('bottleneck_analysis', lang), 'url': '#'}
        ]
    )

# ============================================================================
# SIMULATION ROUTES
# ============================================================================

@org_planning_bp.route('/simulations')
@op_login_required
@op_permission_required('simulations', 'view')
def simulations():
    """List simulation scenarios."""
    lang = get_user_language()
    
    scenarios = get_simulation_scenarios(created_by=session['user_id'])
    
    return render_template('org_planning/simulations/list.html',
        page_title=t('simulations', lang),
        lang=lang,
        scenarios=scenarios,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('simulations', lang), 'url': '#'}
        ]
    )

@org_planning_bp.route('/simulations/create', methods=['GET', 'POST'])
@op_login_required
@op_permission_required('simulations', 'create')
def simulation_create():
    """Create a simulation scenario."""
    lang = get_user_language()
    
    if request.method == 'POST':
        name = request.form.get('name')
        scenario_type = request.form.get('scenario_type')
        
        scenario_id = create_simulation_scenario(
            name=name,
            name_ar=request.form.get('name_ar'),
            description=request.form.get('description'),
            scenario_type=scenario_type,
            planned_effective_date=request.form.get('planned_effective_date'),
            created_by=session['user_id']
        )
        
        # Add changes from form
        change_count = request.form.get('change_count', type=int, default=0)
        for i in range(change_count):
            add_simulation_change(
                simulation_id=scenario_id,
                change_type=request.form.get(f'change_{i}_type'),
                entity_type=request.form.get(f'change_{i}_entity'),
                entity_id=request.form.get(f'change_{i}_entity_id', type=int),
                field_name=request.form.get(f'change_{i}_field'),
                old_value=request.form.get(f'change_{i}_old'),
                new_value=request.form.get(f'change_{i}_new')
            )
        
        # Analyze impacts
        impacts = analyze_simulation_impacts(scenario_id)
        
        flash(f'Simulation scenario "{name}" created successfully.', 'success')
        return redirect(url_for('org_planning.simulation_detail', scenario_id=scenario_id))
    
    return render_template('org_planning/simulations/create.html',
        page_title=t('create_simulation', lang),
        lang=lang,
        org_units=get_org_units(),
        positions=get_positions(),
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('simulations', lang), 'url': '/org-planning/simulations'},
            {'label': t('create_simulation', lang), 'url': '#'}
        ]
    )

@org_planning_bp.route('/simulations/<int:scenario_id>')
@op_login_required
@op_permission_required('simulations', 'view')
def simulation_detail(scenario_id):
    """View simulation details."""
    lang = get_user_language()
    
    scenario = get_one("SELECT * FROM op_simulation_scenarios WHERE id = ?", (scenario_id,))
    if not scenario:
        flash('Simulation not found.', 'error')
        return redirect(url_for('org_planning.simulations'))
    
    changes = get_all("SELECT * FROM op_simulation_changes WHERE simulation_id = ?", (scenario_id,))
    impacts = get_all("SELECT * FROM op_simulation_impacts WHERE simulation_id = ?", (scenario_id,))
    
    return render_template('org_planning/simulations/detail.html',
        page_title=scenario['name'],
        scenario=scenario,
        changes=changes,
        impacts=impacts,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('simulations', lang), 'url': '/org-planning/simulations'},
            {'label': scenario['name'], 'url': '#'}
        ]
    )

# ============================================================================
# REPORTS ROUTES
# ============================================================================

@org_planning_bp.route('/reports')
@op_login_required
@op_permission_required('reports', 'view')
def reports():
    """Reports overview."""
    lang = get_user_language()
    
    return render_template('org_planning/reports/index.html',
        page_title=t('reports', lang),
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('reports', lang), 'url': '#'}
        ]
    )

@org_planning_bp.route('/reports/structure')
@op_login_required
@op_permission_required('reports', 'view')
def report_structure():
    """Organization structure report."""
    lang = get_user_language()

    companies = get_companies()
    selected_company = request.args.get('company', type=int)
    if selected_company:
        org_units = get_org_units(company_id=selected_company)
    else:
        org_units = get_org_units()

    total_units = len(org_units)
    total_companies = len(companies)
    total_employees = sum(u.employee_count or 0 for u in org_units)
    active_units = sum(1 for u in org_units if u.is_active == 1)

    units_by_type = {}
    for u in org_units:
        utype = u.unit_type or 'unknown'
        units_by_type[utype] = units_by_type.get(utype, 0) + 1

    units_by_company = {}
    for u in org_units:
        cname = u.company_name or 'Unknown'
        units_by_company[cname] = units_by_company.get(cname, 0) + 1

    return render_template('org_planning/reports/structure.html',
        page_title=t('org_structure_report', lang),
        lang=lang,
        companies=companies,
        org_units=org_units,
        selected_company=selected_company,
        total_units=total_units,
        total_companies=total_companies,
        total_employees=total_employees,
        active_units=active_units,
        units_by_type=units_by_type.items(),
        units_by_company=units_by_company.items(),
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('reports', lang), 'url': '/org-planning/reports'},
            {'label': t('org_structure_report', lang), 'url': '#'}
        ]
    )

@org_planning_bp.route('/reports/headcount')
@op_login_required
@op_permission_required('reports', 'view')
def report_headcount():
    """Headcount report."""
    lang = get_user_language()

    year = request.args.get('year', date.today().year, type=int)
    metrics = get_headcount_metrics()
    plans = get_headcount_plans(plan_year=year)

    total_approved = sum(m.total_approved or 0 for m in metrics)
    total_current = sum(m.total_current or 0 for m in metrics)
    total_vacant = sum(m.total_vacant or 0 for m in metrics)

    return render_template('org_planning/reports/headcount.html',
        page_title=t('headcount_report', lang),
        lang=lang,
        metrics=metrics,
        plans=plans,
        selected_year=year,
        total_approved=total_approved,
        total_current=total_current,
        total_vacant=total_vacant,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('reports', lang), 'url': '/org-planning/reports'},
            {'label': t('headcount_report', lang), 'url': '#'}
        ]
    )

@org_planning_bp.route('/reports/process-performance')
@op_login_required
@op_permission_required('reports', 'view')
def report_process_performance():
    """Process performance report."""
    lang = get_user_language()

    days = request.args.get('days', 30, type=int)
    metrics = get_process_metrics(days=days)
    sla_stats = get_sla_compliance_stats(days=days)
    bottlenecks = get_bottleneck_steps(days=days)

    total_instances = sum(m.total_instances or 0 for m in metrics)
    total_completed = sum(m.completed or 0 for m in metrics)
    total_rejected = sum(m.rejected or 0 for m in metrics)
    completion_rate = round((total_completed / total_instances * 100) if total_instances > 0 else 100, 1)
    avg_cycle_time = round(sum((m.avg_hours or 0) for m in metrics) / len(metrics) if metrics else 0, 1)

    return render_template('org_planning/reports/process_performance.html',
        page_title=t('process_performance_report', lang),
        lang=lang,
        metrics=metrics,
        sla_stats=sla_stats,
        bottlenecks=bottlenecks,
        days=days,
        total_instances=total_instances,
        total_completed=total_completed,
        total_rejected=total_rejected,
        completion_rate=completion_rate,
        avg_cycle_time=avg_cycle_time,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('reports', lang), 'url': '/org-planning/reports'},
            {'label': t('process_performance_report', lang), 'url': '#'}
        ]
    )

@org_planning_bp.route('/reports/sla-compliance')
@op_login_required
@op_permission_required('reports', 'view')
def report_sla_compliance():
    """SLA compliance report."""
    lang = get_user_language()

    days = request.args.get('days', 30, type=int)
    sla_stats = get_sla_compliance_stats(days=days)

    total_records = sum(s.total_records or 0 for s in sla_stats)
    total_breaches = sum(s.breaches or 0 for s in sla_stats)
    total_on_time = total_records - total_breaches
    compliance_rate = round((total_on_time / total_records * 100) if total_records > 0 else 100, 1)
    critical_breaches = [s for s in sla_stats if s.get('breaches', 0) > 0 and s.get('priority') in ['critical', 'high']]

    return render_template('org_planning/reports/sla_compliance.html',
        page_title=t('sla_compliance_report', lang),
        lang=lang,
        sla_stats=sla_stats,
        days=days,
        total_records=total_records,
        total_breaches=total_breaches,
        total_on_time=total_on_time,
        compliance_rate=compliance_rate,
        critical_breaches=critical_breaches,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('reports', lang), 'url': '/org-planning/reports'},
            {'label': t('sla_compliance_report', lang), 'url': '#'}
        ]
    )

@org_planning_bp.route('/reports/workflow')
@op_login_required
@op_permission_required('reports', 'view')
def report_workflow():
    """Workflow report with cycle time analysis."""
    lang = get_user_language()

    workflow_stats = get_all("""
        SELECT
            wd.name as workflow_name,
            wd.category,
            COUNT(CASE WHEN pi.status = 'in_progress' THEN 1 END) as active_instances,
            COUNT(CASE WHEN pi.status = 'completed' AND pi.completed_at >= date('now', '-30 days') THEN 1 END) as completed_30d,
            COUNT(CASE WHEN pi.status = 'rejected' AND pi.completed_at >= date('now', '-30 days') THEN 1 END) as rejected_30d,
            AVG(CASE WHEN pi.status = 'completed' AND pi.completed_at >= date('now', '-30 days')
                THEN (julianday(pi.completed_at) - julianday(pi.started_at)) * 24 END) as avg_cycle_hours
        FROM op_workflow_definitions wd
        LEFT JOIN op_process_instances pi ON pi.workflow_definition_id = wd.id
        GROUP BY wd.id, wd.name, wd.category
        ORDER BY completed_30d DESC
    """)

    for w in workflow_stats:
        total = (w.completed_30d or 0) + (w.rejected_30d or 0)
        w['approval_rate'] = round((w.completed_30d or 0) / total * 100) if total > 0 else 100

    active_workflows = get_one("SELECT COUNT(*) as cnt FROM op_workflow_definitions WHERE status = 'published'")[0]['cnt'] if get_one("SELECT COUNT(*) as cnt FROM op_workflow_definitions WHERE status = 'published'") else 0

    completed_week = get_one("SELECT COUNT(*) as cnt FROM op_process_instances WHERE status = 'completed' AND completed_at >= date('now', '-7 days')")[0]['cnt'] if get_one("SELECT COUNT(*) as cnt FROM op_process_instances WHERE status = 'completed' AND completed_at >= date('now', '-7 days')") else 0

    avg_cycle_result = get_one("""
        SELECT AVG((julianday(completed_at) - julianday(started_at)) * 24) as avg_hours
        FROM op_process_instances
        WHERE status = 'completed' AND completed_at >= date('now', '-30 days')
    """)
    avg_cycle_time = round(avg_cycle_result[0]['avg_hours'] or 0, 1) if avg_cycle_result and avg_cycle_result[0] else 0

    outcome_result = get_one("""
        SELECT
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as approved,
            SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected,
            SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
        FROM op_process_instances
        WHERE completed_at >= date('now', '-30 days')
    """)
    total_approved = outcome_result[0]['approved'] if outcome_result and outcome_result[0] else 0
    total_rejected = outcome_result[0]['rejected'] if outcome_result and outcome_result[0] else 0
    total_cancelled = outcome_result[0]['cancelled'] if outcome_result and outcome_result[0] else 0

    total_outcomes = total_approved + total_rejected + total_cancelled
    approval_rate = round(total_approved / total_outcomes * 100) if total_outcomes > 0 else 100

    recent_completions = get_all("""
        SELECT pi.title, wd.name as workflow_name, pi.completed_at,
               (julianday(pi.completed_at) - julianday(pi.started_at)) * 24 as cycle_hours
        FROM op_process_instances pi
        JOIN op_workflow_definitions wd ON pi.workflow_definition_id = wd.id
        WHERE pi.status = 'completed' AND pi.completed_at >= date('now', '-7 days')
        ORDER BY pi.completed_at DESC
    """)

    return render_template('org_planning/reports/workflow.html',
        page_title=t('workflow_report', lang),
        lang=lang,
        workflow_stats=workflow_stats,
        active_workflows=active_workflows or 0,
        completed_week=completed_week or 0,
        avg_cycle_time=avg_cycle_time,
        approval_rate=approval_rate,
        total_approved=total_approved,
        total_rejected=total_rejected,
        total_cancelled=total_cancelled,
        recent_completions=recent_completions,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('reports', lang), 'url': '/org-planning/reports'},
            {'label': t('workflow_report', lang), 'url': '#'}
        ]
    )

# ============================================================================
# SETTINGS ROUTES
# ============================================================================

@org_planning_bp.route('/settings')
@op_login_required
@op_permission_required('settings', 'view')
def settings():
    """Module settings."""
    lang = get_user_language()
    
    settings_list = get_all("SELECT * FROM op_settings ORDER BY category, setting_key")
    
    return render_template('org_planning/settings/index.html',
        page_title=t('settings', lang),
        lang=lang,
        settings=settings_list,
        breadcrumbs=[
            {'label': t('home', lang), 'url': '/'},
            {'label': t('org_planning', lang), 'url': '/org-planning'},
            {'label': t('settings', lang), 'url': '#'}
        ]
    )

@org_planning_bp.route('/settings/update', methods=['POST'])
@op_login_required
@op_permission_required('settings', 'edit')
def settings_update():
    """Update module settings."""
    lang = get_user_language()
    
    for key, value in request.form.items():
        if key.startswith('setting_'):
            setting_key = key.replace('setting_', '')
            with get_db_context() as db:
                db.execute("""
                    INSERT INTO op_settings (setting_key, setting_value, updated_by, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(setting_key) DO UPDATE SET setting_value = ?, updated_by = ?, updated_at = CURRENT_TIMESTAMP
                """, (setting_key, value, session['user_id'], value, session['user_id']))
    
    flash('Settings updated successfully.', 'success')
    return redirect(url_for('org_planning.settings'))

# ============================================================================
# API ROUTES
# ============================================================================

@org_planning_bp.route('/api/stats')
@op_login_required
def api_stats():
    """API endpoint for dashboard stats."""
    stats = get_module_stats()
    return jsonify(stats)

@org_planning_bp.route('/api/org-tree')
@op_login_required
def api_org_tree():
    """API endpoint for org tree data."""
    company_id = request.args.get('company_id', type=int)
    tree = get_org_unit_tree(company_id=company_id)
    return jsonify(tree)

@org_planning_bp.route('/api/process/<int:instance_id>')
@op_login_required
def api_process(instance_id):
    """API endpoint for process instance."""
    instance = get_one("""
        SELECT pi.*, wd.name as workflow_name
        FROM op_process_instances pi
        LEFT JOIN op_workflow_definitions wd ON pi.workflow_definition_id = wd.id
        WHERE pi.id = ?
    """, (instance_id,))
    return jsonify(dict(instance) if instance else {})

@org_planning_bp.route('/api/approval-route')
@op_login_required
def api_approval_route():
    """Find approval route for a transaction."""
    module = request.args.get('module')
    doc_type = request.args.get('document_type')
    amount = request.args.get('amount', type=float, default=0)
    
    route = find_approval_route(module, doc_type, amount)
    return jsonify(route if route else {'error': 'No approval route found'})

# ============================================================================
# BLUEPRINT REGISTRATION FUNCTION
# ============================================================================

def register_org_planning_routes(app):
    """Register org planning blueprint with the Flask app."""
    app.register_blueprint(org_planning_bp)
    print("[OK] Registered Organizational Planning & BPM routes")
