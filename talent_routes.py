"""
Talent Management Module Routes
==============================
This file contains all Talent Management route definitions.
Routes follow RESTful conventions and integrate with the existing HR blueprint.

Route Prefix: /hr/talent/*
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from functools import wraps
from datetime import datetime, timedelta, date
import sqlite3
import json
import io
import csv
from urllib.parse import urlencode

# Try to import talent_models, fall back gracefully if not available
try:
    from talent_models import (
        get_db, run_talent_migrations, get_talent_profile,
        get_employee_competencies, get_talent_pool_members,
        get_succession_plans, get_development_plans,
        get_talent_review_participants, log_talent_audit,
        calculate_bench_strength, get_talent_dashboard_metrics,
        TALENT_TABLES
    )
    TALENT_MODELS_AVAILABLE = True
except ImportError:
    TALENT_MODELS_AVAILABLE = False
    get_db = None

# Try to import from hr_models for shared utilities
try:
    from hr_models import get_db as hr_get_db
except ImportError:
    hr_get_db = None

# Import flow integration if available
try:
    from flow_routes import create_flow_notification
    FLOW_AVAILABLE = True
except ImportError:
    FLOW_AVAILABLE = False
    create_flow_notification = None

# Import translations helper
try:
    from translations import get_translation
    TRANSLATIONS_AVAILABLE = True
except ImportError:
    TRANSLATIONS_AVAILABLE = False
    get_translation = lambda lang, key, default: default

# Import permissions helper
try:
    from permissions import check_permission
    PERMISSIONS_AVAILABLE = True
except ImportError:
    PERMISSIONS_AVAILABLE = False
    check_permission = lambda *args, **kwargs: True


def get_t_db():
    """Get database connection - tries talent_models first, then falls back to hr_models."""
    if get_db:
        return get_db()
    elif hr_get_db:
        return hr_get_db()
    else:
        raise Exception("No database connection available")


# =============================================================================
# TALENT BLUEPRINT
# =============================================================================

talent_bp = Blueprint('talent', __name__, 
                      template_folder='../templates/talent',
                      url_prefix='/hr/talent')


def talent_login_required(f):
    """Decorator for talent module login required."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access Talent Management.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def talent_permission_required(action: str = 'view'):
    """Decorator for talent module permission required."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'hr_permissions' in session:
                perms = session.get('hr_permissions', [])
                module_perms = [p for p in perms if isinstance(p, dict)]
                for perm in module_perms:
                    if perm.get('module') == 'talent' and perm.get(action):
                        return f(*args, **kwargs)
            # Fallback: check if user has any HR permission
            if 'hr_permissions' not in session:
                return f(*args, **kwargs)  # Allow if no HR system at all
            flash(f'You do not have permission to perform this action.', 'error')
            return redirect(url_for('hr.dashboard'))
        return decorated_function
    return decorator


def t(key, default=None, lang=None):
    """Translation helper for talent routes."""
    if not TRANSLATIONS_AVAILABLE:
        return default or key
    if lang is None:
        lang = session.get('language', 'en')
    return get_translation(lang, key, default)


def get_current_user_id():
    """Get current user ID from session."""
    return session.get('user_id')


def get_user_ip():
    """Get user IP address."""
    return request.remote_addr or '0.0.0.0'


# =============================================================================
# TALENT DASHBOARD
# =============================================================================

@talent_bp.route('/')
@talent_bp.route('/dashboard')
@talent_login_required
@talent_permission_required('view')
def dashboard():
    """Main Talent Management Dashboard."""
    db = get_t_db()
    try:
        # Get dashboard metrics
        metrics = _get_talent_metrics(db)
        
        # Get recent talent activity
        recent_activity = _get_recent_talent_activity(db, limit=10)
        
        # Get pending approvals
        pending_approvals = _get_pending_talent_approvals(db, limit=5)
        
        # Get Hi-Po summary
        hipo_summary = _get_hipo_summary(db)
        
        # Get succession overview
        succession_overview = _get_succession_overview(db)
        
        # Get development plan summary
        dev_summary = _get_dev_plan_summary(db)
        
        return render_template('talent/dashboard.html',
                             title=t('talent_dashboard', 'Talent Dashboard'),
                             metrics=metrics,
                             recent_activity=recent_activity,
                             pending_approvals=pending_approvals,
                             hipo_summary=hipo_summary,
                             succession_overview=succession_overview,
                             dev_summary=dev_summary)
    finally:
        db.close()


@talent_bp.route('/executive-dashboard')
@talent_login_required
@talent_permission_required('view')
def executive_dashboard():
    """Executive Talent Dashboard - CEO/CHRO view."""
    db = get_t_db()
    try:
        # Get executive-level metrics
        exec_metrics = _get_executive_talent_metrics(db)
        
        # Get talent risk indicators
        risk_indicators = _get_talent_risk_indicators(db)
        
        # Get succession risk positions
        critical_risk_positions = _get_critical_risk_positions(db)
        
        # Get Hi-Po pipeline health
        hipo_pipeline = _get_hipo_pipeline(db)
        
        # Get workforce capability summary
        capability_summary = _get_workforce_capability_summary(db)
        
        return render_template('talent/executive_dashboard.html',
                             title=t('executive_talent_dashboard', 'Executive Talent Dashboard'),
                             exec_metrics=exec_metrics,
                             risk_indicators=risk_indicators,
                             critical_risk_positions=critical_risk_positions,
                             hipo_pipeline=hipo_pipeline,
                             capability_summary=capability_summary)
    finally:
        db.close()


# =============================================================================
# TALENT PROFILES
# =============================================================================

@talent_bp.route('/profiles')
@talent_login_required
@talent_permission_required('view')
def profiles():
    """List all talent profiles."""
    db = get_t_db()
    try:
        search = request.args.get('search', '').strip()
        department = request.args.get('department', '').strip()
        readiness = request.args.get('readiness', '').strip()
        potential = request.args.get('potential', '').strip()
        page = int(request.args.get('page', 1))
        per_page = 20
        
        # Build query
        query = """
            SELECT tp.*, e.first_name, e.last_name, e.employee_code, e.email, e.status,
                   d.name as department_name, p.title as position_title,
                   m.first_name || ' ' || m.last_name as manager_name
            FROM tm_talent_profiles tp
            JOIN hr_employees e ON tp.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            LEFT JOIN hr_positions p ON ee.position_id = p.id
            LEFT JOIN hr_employees m ON ee.reporting_to_id = m.id
            WHERE e.status = 'Active'
        """
        count_query = """
            SELECT COUNT(*) as cnt FROM tm_talent_profiles tp
            JOIN hr_employees e ON tp.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            WHERE e.status = 'Active'
        """
        params = []
        
        if search:
            query += " AND (e.first_name LIKE ? OR e.last_name LIKE ? OR e.employee_code LIKE ?)"
            count_query += " AND (e.first_name LIKE ? OR e.last_name LIKE ? OR e.employee_code LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])
        
        if department:
            query += " AND ee.department_id = ?"
            count_query += " AND ee.department_id = ?"
            params.append(department)
        
        if readiness:
            query += " AND tp.readiness_level = ?"
            count_query += " AND tp.readiness_level = ?"
            params.append(readiness)
        
        if potential:
            query += " AND tp.potential_rating = ?"
            count_query += " AND tp.potential_rating = ?"
            params.append(potential)
        
        # Get total count
        total = db.execute(count_query, params).fetchone()['cnt']
        
        # Add pagination
        query += " ORDER BY tp.potential_score DESC, e.last_name LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        
        profiles = db.execute(query, params).fetchall()
        
        # Get filter options
        departments = db.execute("SELECT id, name FROM hr_departments WHERE status = 'Active' ORDER BY name").fetchall()
        
        return render_template('talent/profiles/list.html',
                             title=t('talent_profiles', 'Talent Profiles'),
                             profiles=[dict(p) for p in profiles],
                             departments=[dict(d) for d in departments],
                             search=search,
                             department=department,
                             readiness=readiness,
                             potential=potential,
                             page=page,
                             total=total,
                             total_pages=(total + per_page - 1) // per_page)
    finally:
        db.close()


@talent_bp.route('/profiles/<int:employee_id>')
@talent_login_required
@talent_permission_required('view')
def profile_detail(employee_id):
    """View detailed talent profile."""
    db = get_t_db()
    try:
        # Get talent profile
        profile = db.execute("""
            SELECT tp.*, e.first_name, e.last_name, e.employee_code, e.email, e.status,
                   e.hire_date, e.profile_image,
                   d.name as department_name, p.title as position_title,
                   m.first_name || ' ' || m.last_name as manager_name,
                   m.employee_code as manager_code
            FROM tm_talent_profiles tp
            JOIN hr_employees e ON tp.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            LEFT JOIN hr_positions p ON ee.position_id = p.id
            LEFT JOIN hr_employees m ON ee.reporting_to_id = m.id
            WHERE tp.employee_id = ?
        """, (employee_id,)).fetchone()
        
        if not profile:
            flash(t('profile_not_found', 'Talent profile not found.'), 'warning')
            return redirect(url_for('talent.profiles'))
        
        # Get employee competencies
        competencies = _get_employee_competencies_with_gaps(db, employee_id)
        
        # Get talent pool memberships
        pool_memberships = _get_employee_pool_memberships(db, employee_id)
        
        # Get development plans
        dev_plans = _get_employee_development_plans(db, employee_id)
        
        # Get succession plans (if this employee is an incumbent)
        succession_as_incumbent = _get_succession_for_employee(db, employee_id)
        
        # Get talent notes
        notes = _get_talent_notes(db, employee_id)
        
        # Get talent history
        history = _get_talent_history(db, employee_id, limit=20)
        
        # Get performance reviews
        performance = _get_employee_performance(db, employee_id)
        
        # Get training history
        training = _get_employee_training(db, employee_id)
        
        return render_template('talent/profiles/detail.html',
                             title=t('talent_profile_detail', 'Talent Profile'),
                             profile=dict(profile),
                             competencies=competencies,
                             pool_memberships=pool_memberships,
                             dev_plans=dev_plans,
                             succession_as_incumbent=succession_as_incumbent,
                             notes=notes,
                             history=history,
                             performance=performance,
                             training=training)
    finally:
        db.close()


@talent_bp.route('/profiles/<int:employee_id>/edit', methods=['GET', 'POST'])
@talent_login_required
@talent_permission_required('edit')
def profile_edit(employee_id):
    """Edit talent profile."""
    db = get_t_db()
    try:
        if request.method == 'POST':
            # Handle profile update
            potential_rating = request.form.get('potential_rating')
            readiness_level = request.form.get('readiness_level')
            career_interests = request.form.get('career_interests')
            mobility_preference = request.form.get('mobility_preference')
            development_priority = request.form.get('development_priority')
            notes = request.form.get('notes')
            
            # Update talent profile
            db.execute("""
                UPDATE tm_talent_profiles SET
                    potential_rating = ?, readiness_level = ?, career_interests = ?,
                    mobility_preference = ?, development_priority = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE employee_id = ?
            """, (potential_rating, readiness_level, career_interests,
                  mobility_preference, development_priority, notes, employee_id))
            
            # Log audit
            log_talent_audit('talent_profile', employee_id, 'UPDATE', 
                           user_id=get_current_user_id(),
                           ip_address=get_user_ip())
            
            db.commit()
            
            flash(t('profile_updated', 'Talent profile updated successfully.'), 'success')
            return redirect(url_for('talent.profile_detail', employee_id=employee_id))
        
        # GET: Show edit form
        profile = db.execute("""
            SELECT tp.*, e.first_name, e.last_name, e.employee_code
            FROM tm_talent_profiles tp
            JOIN hr_employees e ON tp.employee_id = e.id
            WHERE tp.employee_id = ?
        """, (employee_id,)).fetchone()
        
        if not profile:
            flash(t('profile_not_found', 'Talent profile not found.'), 'warning')
            return redirect(url_for('talent.profiles'))
        
        return render_template('talent/profiles/edit.html',
                             title=t('edit_talent_profile', 'Edit Talent Profile'),
                             profile=dict(profile))
    finally:
        db.close()


# =============================================================================
# TALENT POOLS
# =============================================================================

@talent_bp.route('/pools')
@talent_login_required
@talent_permission_required('view')
def pools():
    """List all talent pools."""
    db = get_t_db()
    try:
        pools = db.execute("""
            SELECT tp.*, 
                   (SELECT COUNT(*) FROM tm_talent_pool_members WHERE pool_id = tp.id AND status = 'Active') as member_count,
                   o.first_name || ' ' || o.last_name as owner_name
            FROM tm_talent_pools tp
            LEFT JOIN hr_employees o ON tp.owner_id = o.id
            WHERE tp.is_active = 1
            ORDER BY tp.pool_type, tp.name
        """).fetchall()
        
        return render_template('talent/pools/list.html',
                             title=t('talent_pools', 'Talent Pools'),
                             pools=[dict(p) for p in pools])
    finally:
        db.close()


@talent_bp.route('/pools/<int:pool_id>')
@talent_login_required
@talent_permission_required('view')
def pool_detail(pool_id):
    """View talent pool details and members."""
    db = get_t_db()
    try:
        pool = db.execute("""
            SELECT tp.*, o.first_name || ' ' || o.last_name as owner_name
            FROM tm_talent_pools tp
            LEFT JOIN hr_employees o ON tp.owner_id = o.id
            WHERE tp.id = ?
        """, (pool_id,)).fetchone()
        
        if not pool:
            flash(t('pool_not_found', 'Talent pool not found.'), 'warning')
            return redirect(url_for('talent.pools'))
        
        members = get_talent_pool_members(pool_id) if TALENT_MODELS_AVAILABLE else []
        
        return render_template('talent/pools/detail.html',
                             title=t('talent_pool_detail', 'Talent Pool'),
                             pool=dict(pool),
                             members=members)
    finally:
        db.close()


@talent_bp.route('/pools/<int:pool_id>/members/add', methods=['POST'])
@talent_login_required
@talent_permission_required('edit')
def pool_add_member(pool_id):
    """Add employee to talent pool."""
    db = get_t_db()
    try:
        employee_id = request.form.get('employee_id')
        nominated_by = get_current_user_id()
        
        if not employee_id:
            flash(t('employee_required', 'Please select an employee.'), 'warning')
            return redirect(url_for('talent.pool_detail', pool_id=pool_id))
        
        # Check if already a member
        existing = db.execute("""
            SELECT id FROM tm_talent_pool_members 
            WHERE pool_id = ? AND employee_id = ? AND status = 'Active'
        """, (pool_id, employee_id)).fetchone()
        
        if existing:
            flash(t('already_member', 'Employee is already a member of this pool.'), 'info')
            return redirect(url_for('talent.pool_detail', pool_id=pool_id))
        
        db.execute("""
            INSERT INTO tm_talent_pool_members 
            (pool_id, employee_id, nominated_by, joined_date, status, membership_type)
            VALUES (?, ?, ?, date('now'), 'Active', 'Manual')
        """, (pool_id, employee_id, nominated_by))
        
        # Update talent profile flag if Hi-Po pool
        pool = db.execute("SELECT pool_type FROM tm_talent_pools WHERE id = ?", (pool_id,)).fetchone()
        if pool and pool['pool_type'] == 'HiPo':
            db.execute("UPDATE tm_talent_profiles SET hi_po = 1 WHERE employee_id = ?", (employee_id,))
        
        log_talent_audit('talent_pool_member', pool_id, 'ADD_MEMBER',
                        new_value=str(employee_id), user_id=get_current_user_id(),
                        ip_address=get_user_ip())
        
        db.commit()
        
        flash(t('member_added', 'Employee added to talent pool.'), 'success')
        return redirect(url_for('talent.pool_detail', pool_id=pool_id))
    finally:
        db.close()


@talent_bp.route('/pools/<int:pool_id>/members/<int:member_id>/remove', methods=['POST'])
@talent_login_required
@talent_permission_required('edit')
def pool_remove_member(pool_id, member_id):
    """Remove employee from talent pool."""
    db = get_t_db()
    try:
        db.execute("""
            UPDATE tm_talent_pool_members SET
                status = 'Inactive', exit_date = date('now')
            WHERE id = ?
        """, (member_id,))
        
        # Update talent profile flag
        member = db.execute("SELECT employee_id FROM tm_talent_pool_members WHERE id = ?", (member_id,)).fetchone()
        if member:
            # Check if still in any Hi-Po pool
            remaining = db.execute("""
                SELECT COUNT(*) as cnt FROM tm_talent_pool_members m
                JOIN tm_talent_pools p ON m.pool_id = p.id
                WHERE m.employee_id = ? AND m.status = 'Active' AND p.pool_type = 'HiPo'
            """, (member['employee_id'],)).fetchone()['cnt']
            
            if remaining == 0:
                db.execute("UPDATE tm_talent_profiles SET hi_po = 0 WHERE employee_id = ?", 
                          (member['employee_id'],))
        
        log_talent_audit('talent_pool_member', pool_id, 'REMOVE_MEMBER',
                        old_value=str(member_id), user_id=get_current_user_id(),
                        ip_address=get_user_ip())
        
        db.commit()
        
        flash(t('member_removed', 'Employee removed from talent pool.'), 'success')
        return redirect(url_for('talent.pool_detail', pool_id=pool_id))
    finally:
        db.close()


# =============================================================================
# SUCCESSION PLANNING
# =============================================================================

@talent_bp.route('/succession')
@talent_login_required
@talent_permission_required('view')
def succession():
    """Succession planning main view."""
    db = get_t_db()
    try:
        # Get critical roles
        critical_roles = db.execute("""
            SELECT cr.*, p.title as position_title, d.name as department_name,
                   e.first_name || ' ' || e.last_name as incumbent_name,
                   (SELECT COUNT(*) FROM tm_succession_plans WHERE critical_role_id = cr.id AND status = 'Approved') as successor_count
            FROM tm_critical_roles cr
            JOIN hr_positions p ON cr.position_id = p.id
            LEFT JOIN hr_departments d ON cr.department_id = d.id
            LEFT JOIN hr_employees e ON cr.incumbent_id = e.id
            WHERE cr.status = 'Active'
            ORDER BY cr.criticality_level, p.title
        """).fetchall()
        
        # Get succession plans summary
        plans_summary = db.execute("""
            SELECT sp.*, e.first_name || ' ' || e.last_name as incumbent_name,
                   s.first_name || ' ' || s.last_name as successor_name,
                   p.title as position_title
            FROM tm_succession_plans sp
            JOIN hr_employees e ON sp.employee_id = e.id
            LEFT JOIN hr_employees s ON sp.successor_id = s.id
            JOIN tm_critical_roles cr ON sp.critical_role_id = cr.id
            LEFT JOIN hr_positions p ON cr.position_id = p.id
            WHERE sp.status IN ('Draft', 'Approved')
            ORDER BY cr.criticality_level, sp.readiness_level
        """).fetchall()
        
        return render_template('talent/succession/list.html',
                             title=t('succession_planning', 'Succession Planning'),
                             critical_roles=[dict(cr) for cr in critical_roles],
                             plans_summary=[dict(p) for p in plans_summary])
    finally:
        db.close()


@talent_bp.route('/succession/<int:role_id>')
@talent_login_required
@talent_permission_required('view')
def succession_detail(role_id):
    """View succession plan for a critical role."""
    db = get_t_db()
    try:
        # Get critical role
        cr = db.execute("""
            SELECT cr.*, p.title as position_title, d.name as department_name,
                   e.first_name || ' ' || e.last_name as incumbent_name,
                   e.employee_code as incumbent_code
            FROM tm_critical_roles cr
            JOIN hr_positions p ON cr.position_id = p.id
            LEFT JOIN hr_departments d ON cr.department_id = d.id
            LEFT JOIN hr_employees e ON cr.incumbent_id = e.id
            WHERE cr.id = ?
        """, (role_id,)).fetchone()
        
        if not cr:
            flash(t('critical_role_not_found', 'Critical role not found.'), 'warning')
            return redirect(url_for('talent.succession'))
        
        # Get succession plans for this role
        plans = get_succession_plans(role_id) if TALENT_MODELS_AVAILABLE else []
        
        # Calculate bench strength
        bench = calculate_bench_strength(role_id) if TALENT_MODELS_AVAILABLE else None
        
        # Get potential successors
        potential_successors = _get_potential_successors(db, role_id)
        
        return render_template('talent/succession/detail.html',
                             title=t('succession_plan', 'Succession Plan'),
                             critical_role=dict(cr),
                             plans=plans,
                             bench=bench,
                             potential_successors=potential_successors)
    finally:
        db.close()


@talent_bp.route('/succession/<int:role_id>/plan/add', methods=['GET', 'POST'])
@talent_login_required
@talent_permission_required('edit')
def succession_add_plan(role_id):
    """Add succession plan for a critical role."""
    db = get_t_db()
    try:
        if request.method == 'POST':
            successor_id = request.form.get('successor_id')
            deputy_id = request.form.get('deputy_id')
            readiness_level = request.form.get('readiness_level')
            development_needs = request.form.get('development_needs')
            
            db.execute("""
                INSERT INTO tm_succession_plans 
                (critical_role_id, employee_id, successor_id, deputy_id, readiness_level,
                 development_needs, status, effective_from)
                VALUES (?, (SELECT incumbent_id FROM tm_critical_roles WHERE id = ?),
                       ?, ?, ?, ?, 'Draft', date('now'))
            """, (role_id, role_id, successor_id, deputy_id, readiness_level, development_needs))
            
            log_talent_audit('succession_plan', role_id, 'CREATE',
                           new_value=f"successor:{successor_id}", user_id=get_current_user_id(),
                           ip_address=get_user_ip())
            
            db.commit()
            
            flash(t('succession_plan_created', 'Succession plan created.'), 'success')
            return redirect(url_for('talent.succession_detail', role_id=role_id))
        
        # GET: Show form
        cr = db.execute("SELECT * FROM tm_critical_roles WHERE id = ?", (role_id,)).fetchone()
        if not cr:
            flash(t('critical_role_not_found', 'Critical role not found.'), 'warning')
            return redirect(url_for('talent.succession'))
        
        # Get potential successors
        potential_successors = _get_potential_successors(db, role_id)
        
        return render_template('talent/succession/plan_add.html',
                             title=t('add_succession_plan', 'Add Succession Plan'),
                             critical_role=dict(cr),
                             potential_successors=potential_successors)
    finally:
        db.close()


@talent_bp.route('/succession/plans/<int:plan_id>/approve', methods=['POST'])
@talent_login_required
@talent_permission_required('approve')
def succession_approve_plan(plan_id):
    """Approve a succession plan."""
    db = get_t_db()
    try:
        db.execute("""
            UPDATE tm_succession_plans SET
                status = 'Approved', approved_by = ?, approved_at = date('now')
            WHERE id = ?
        """, (get_current_user_id(), plan_id))
        
        log_talent_audit('succession_plan', plan_id, 'APPROVE',
                        user_id=get_current_user_id(), ip_address=get_user_ip())
        
        db.commit()
        
        flash(t('plan_approved', 'Succession plan approved.'), 'success')
        return redirect(url_for('talent.succession'))
    finally:
        db.close()


# =============================================================================
# DEVELOPMENT PLANS
# =============================================================================

@talent_bp.route('/development')
@talent_login_required
@talent_permission_required('view')
def development():
    """Development plans main view."""
    db = get_t_db()
    try:
        status = request.args.get('status', '').strip()
        
        plans = get_development_plans(db=db, status=status) if TALENT_MODELS_AVAILABLE else _get_dev_plans_fallback(db, status)
        
        return render_template('talent/development/list.html',
                             title=t('development_plans', 'Development Plans'),
                             plans=plans,
                             status=status)
    finally:
        db.close()


@talent_bp.route('/development/<int:plan_id>')
@talent_login_required
@talent_permission_required('view')
def development_detail(plan_id):
    """View development plan details."""
    db = get_t_db()
    try:
        # Get plan
        plan = db.execute("""
            SELECT dp.*, e.first_name || ' ' || e.last_name as employee_name,
                   e.employee_code,
                   m.first_name || ' ' || m.last_name as manager_name,
                   a.first_name || ' ' || a.last_name as approved_by_name
            FROM tm_development_plans dp
            JOIN hr_employees e ON dp.employee_id = e.id
            LEFT JOIN hr_employees m ON dp.manager_id = m.id
            LEFT JOIN hr_employees a ON dp.approved_by = a.id
            WHERE dp.id = ?
        """, (plan_id,)).fetchone()
        
        if not plan:
            flash(t('plan_not_found', 'Development plan not found.'), 'warning')
            return redirect(url_for('talent.development'))
        
        # Get goals
        goals = db.execute("""
            SELECT g.*, 
                   (SELECT COUNT(*) FROM tm_development_actions WHERE goal_id = g.id) as action_count,
                   (SELECT COUNT(*) FROM tm_development_actions WHERE goal_id = g.id AND status = 'Completed') as completed_actions
            FROM tm_development_goals g
            WHERE g.plan_id = ?
            ORDER BY g.priority, g.target_date
        """, (plan_id,)).fetchall()
        
        # Get actions for each goal
        goals_with_actions = []
        for goal in goals:
            goal_dict = dict(goal)
            actions = db.execute("""
                SELECT a.*, l.title as learning_title
                FROM tm_development_actions a
                LEFT JOIN hr_training_programs l ON a.linked_learning_id = l.id
                WHERE a.goal_id = ?
                ORDER BY a.due_date
            """, (goal['id'],)).fetchall()
            goal_dict['actions'] = [dict(a) for a in actions]
            goals_with_actions.append(goal_dict)
        
        return render_template('talent/development/detail.html',
                             title=t('development_plan_detail', 'Development Plan'),
                             plan=dict(plan),
                             goals=goals_with_actions)
    finally:
        db.close()


@talent_bp.route('/development/<int:plan_id>/goal/add', methods=['POST'])
@talent_login_required
@talent_permission_required('edit')
def development_add_goal(plan_id):
    """Add goal to development plan."""
    db = get_t_db()
    try:
        goal_title = request.form.get('goal_title')
        goal_description = request.form.get('goal_description')
        priority = request.form.get('priority', 'Medium')
        target_date = request.form.get('target_date')
        competency_focus = request.form.get('competency_focus')
        
        db.execute("""
            INSERT INTO tm_development_goals 
            (plan_id, goal_title, goal_description, priority, target_date, competency_focus, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Not Started')
        """, (plan_id, goal_title, goal_description, priority, target_date, competency_focus))
        
        # Update plan's goal count
        db.execute("""
            UPDATE tm_development_plans SET total_goals = (
                SELECT COUNT(*) FROM tm_development_goals WHERE plan_id = ?
            )
            WHERE id = ?
        """, (plan_id, plan_id))
        
        log_talent_audit('development_goal', plan_id, 'CREATE',
                        new_value=goal_title, user_id=get_current_user_id(),
                        ip_address=get_user_ip())
        
        db.commit()
        
        flash(t('goal_added', 'Development goal added.'), 'success')
        return redirect(url_for('talent.development_detail', plan_id=plan_id))
    finally:
        db.close()


@talent_bp.route('/development/actions/<int:action_id>/complete', methods=['POST'])
@talent_login_required
@talent_permission_required('edit')
def development_complete_action(action_id):
    """Mark development action as complete."""
    db = get_t_db()
    try:
        db.execute("""
            UPDATE tm_development_actions SET
                status = 'Completed', completed_at = datetime('now'),
                completed_by = ?
            WHERE id = ?
        """, (get_current_user_id(), action_id))
        
        # Update goal progress
        db.execute("""
            UPDATE tm_development_goals SET 
                completed_at = datetime('now'),
                status = CASE 
                    WHEN (SELECT COUNT(*) FROM tm_development_actions WHERE goal_id = ? AND status != 'Completed') = 0 
                    THEN 'Completed' ELSE status END
            WHERE id = (SELECT goal_id FROM tm_development_actions WHERE id = ?)
        """, (action_id, action_id))
        
        # Update plan completion percentage
        db.execute("""
            UPDATE tm_development_plans SET 
                completion_percentage = (
                    SELECT (CAST(SUM(CASE WHEN a.status = 'Completed' THEN 1 ELSE 0 END) AS FLOAT) / 
                            NULLIF(COUNT(*), 0) * 100)
                    FROM tm_development_actions a
                    JOIN tm_development_goals g ON a.goal_id = g.id
                    WHERE g.plan_id = (SELECT plan_id FROM tm_development_actions WHERE id = ?)
                ),
                completed_goals = (
                    SELECT COUNT(*) FROM tm_development_goals 
                    WHERE plan_id = (SELECT plan_id FROM tm_development_actions WHERE id = ?) 
                    AND status = 'Completed'
                )
            WHERE id = (SELECT plan_id FROM tm_development_actions WHERE id = ?)
        """, (action_id, action_id, action_id))
        
        db.commit()
        
        flash(t('action_completed', 'Development action marked as complete.'), 'success')
        return redirect(request.referrer or url_for('talent.development'))
    finally:
        db.close()


# =============================================================================
# TALENT REVIEWS
# =============================================================================

@talent_bp.route('/reviews')
@talent_login_required
@talent_permission_required('view')
def reviews():
    """Talent review cycles."""
    db = get_t_db()
    try:
        reviews = db.execute("""
            SELECT r.*, 
                   (SELECT COUNT(*) FROM tm_talent_review_participants WHERE review_id = r.id) as participants,
                   (SELECT COUNT(*) FROM tm_talent_review_participants WHERE review_id = r.id AND status = 'Submitted') as completed,
                   c.first_name || ' ' || c.last_name as created_by_name
            FROM tm_talent_reviews r
            LEFT JOIN hr_employees c ON r.created_by = c.id
            ORDER BY r.period_start DESC
        """).fetchall()
        
        return render_template('talent/reviews/list.html',
                             title=t('talent_reviews', 'Talent Reviews'),
                             reviews=[dict(r) for r in reviews])
    finally:
        db.close()


@talent_bp.route('/reviews/<int:review_id>')
@talent_login_required
@talent_permission_required('view')
def review_detail(review_id):
    """View talent review details."""
    db = get_t_db()
    try:
        review = db.execute("SELECT * FROM tm_talent_reviews WHERE id = ?", (review_id,)).fetchone()
        
        if not review:
            flash(t('review_not_found', 'Talent review not found.'), 'warning')
            return redirect(url_for('talent.reviews'))
        
        participants = get_talent_review_participants(review_id) if TALENT_MODELS_AVAILABLE else []
        
        # Get 9-box data
        nine_box_data = _get_nine_box_data(db, review_id)
        
        return render_template('talent/reviews/detail.html',
                             title=t('talent_review_detail', 'Talent Review'),
                             review=dict(review),
                             participants=participants,
                             nine_box_data=nine_box_data)
    finally:
        db.close()


@talent_bp.route('/reviews/<int:review_id>/participant/<int:participant_id>/rate', methods=['POST'])
@talent_login_required
@talent_permission_required('edit')
def review_rate_participant(review_id, participant_id):
    """Rate a participant in talent review."""
    db = get_t_db()
    try:
        potential_rating = request.form.get('potential_rating')
        performance_rating = request.form.get('performance_rating')
        readiness_rating = request.form.get('readiness_rating')
        recommended_actions = request.form.get('recommended_actions')
        notes = request.form.get('notes')
        
        db.execute("""
            UPDATE tm_talent_review_participants SET
                potential_rating = ?, performance_rating = ?, readiness_rating = ?,
                recommended_actions = ?, review_notes = ?,
                status = 'Submitted', submitted_at = datetime('now')
            WHERE id = ? AND review_id = ?
        """, (potential_rating, performance_rating, readiness_rating,
              recommended_actions, notes, participant_id, review_id))
        
        log_talent_audit('talent_review_participant', participant_id, 'RATE',
                        user_id=get_current_user_id(), ip_address=get_user_ip())
        
        db.commit()
        
        flash(t('rating_saved', 'Talent review rating saved.'), 'success')
        return redirect(url_for('talent.review_detail', review_id=review_id))
    finally:
        db.close()


# =============================================================================
# COMPETENCY FRAMEWORK
# =============================================================================

@talent_bp.route('/competencies')
@talent_login_required
@talent_permission_required('view')
def competencies():
    """Competency library."""
    db = get_t_db()
    try:
        category_id = request.args.get('category_id', '').strip()
        
        query = """
            SELECT c.*, cat.name as category_name,
                   (SELECT COUNT(*) FROM tm_employee_competencies WHERE competency_id = c.id AND status = 'Active') as assessed_count
            FROM tm_competencies c
            LEFT JOIN tm_competency_categories cat ON c.category_id = cat.id
            WHERE c.is_active = 1
        """
        params = []
        
        if category_id:
            query += " AND c.category_id = ?"
            params.append(category_id)
        
        query += " ORDER BY cat.sort_order, c.name"
        
        competencies = db.execute(query, params).fetchall()
        categories = db.execute("SELECT * FROM tm_competency_categories WHERE is_active = 1 ORDER BY sort_order").fetchall()
        
        return render_template('talent/competencies/list.html',
                             title=t('competency_library', 'Competency Library'),
                             competencies=[dict(c) for c in competencies],
                             categories=[dict(cat) for cat in categories],
                             category_id=category_id)
    finally:
        db.close()


@talent_bp.route('/competencies/gap-analysis')
@talent_login_required
@talent_permission_required('view')
def competency_gap_analysis():
    """Competency gap analysis for employees."""
    db = get_t_db()
    try:
        department_id = request.args.get('department_id', '').strip()
        
        query = """
            SELECT ec.*, e.first_name, e.last_name, e.employee_code,
                   c.name as competency_name, cat.name as category_name,
                   c.proficiency_levels, c.weight_factor
            FROM tm_employee_competencies ec
            JOIN hr_employees e ON ec.employee_id = e.id
            JOIN tm_competencies c ON ec.competency_id = c.id
            LEFT JOIN tm_competency_categories cat ON c.category_id = cat.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            WHERE ec.status = 'Active' AND ec.gap_score < 0
        """
        params = []
        
        if department_id:
            query += " AND ee.department_id = ?"
            params.append(department_id)
        
        query += " ORDER BY ec.gap_score, e.last_name"
        
        gaps = db.execute(query, params).fetchall()
        departments = db.execute("SELECT id, name FROM hr_departments WHERE status = 'Active'").fetchall()
        
        return render_template('talent/competencies/gap_analysis.html',
                             title=t('competency_gap_analysis', 'Competency Gap Analysis'),
                             gaps=[dict(g) for g in gaps],
                             departments=[dict(d) for d in departments],
                             department_id=department_id)
    finally:
        db.close()


# =============================================================================
# WORKFORCE CAPABILITY
# =============================================================================

@talent_bp.route('/workforce-capability')
@talent_login_required
@talent_permission_required('view')
def workforce_capability():
    """Workforce capability overview."""
    db = get_t_db()
    try:
        # Get bench strength by department
        bench_by_dept = _get_bench_strength_by_department(db)
        
        # Get readiness distribution
        readiness_dist = _get_readiness_distribution(db)
        
        # Get capability heatmap data
        heatmap_data = _get_capability_heatmap(db)
        
        # Get leadership pipeline
        leadership_pipeline = _get_leadership_pipeline(db)
        
        return render_template('talent/workforce_capability.html',
                             title=t('workforce_capability', 'Workforce Capability'),
                             bench_by_dept=bench_by_dept,
                             readiness_dist=readiness_dist,
                             heatmap_data=heatmap_data,
                             leadership_pipeline=leadership_pipeline)
    finally:
        db.close()


# =============================================================================
# REPORTS & EXPORTS
# =============================================================================

@talent_bp.route('/reports')
@talent_login_required
@talent_permission_required('view')
def reports():
    """Talent reports center."""
    return render_template('talent/reports/index.html',
                         title=t('talent_reports', 'Talent Reports & Analytics'))


@talent_bp.route('/reports/talent-profile')
@talent_login_required
@talent_permission_required('view')
def report_talent_profile():
    """Talent profile report."""
    db = get_t_db()
    try:
        profiles = db.execute("""
            SELECT tp.*, e.first_name, e.last_name, e.employee_code,
                   d.name as department_name, p.title as position_title
            FROM tm_talent_profiles tp
            JOIN hr_employees e ON tp.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            LEFT JOIN hr_positions p ON ee.position_id = p.id
            WHERE e.status = 'Active'
            ORDER BY e.last_name
        """).fetchall()
        
        return render_template('talent/reports/talent_profile.html',
                             title=t('talent_profile_report', 'Talent Profile Report'),
                             profiles=[dict(p) for p in profiles])
    finally:
        db.close()


@talent_bp.route('/reports/succession-coverage')
@talent_login_required
@talent_permission_required('view')
def report_succession_coverage():
    """Succession coverage report."""
    db = get_t_db()
    try:
        coverage = _get_succession_coverage_report(db)
        
        return render_template('talent/reports/succession_coverage.html',
                             title=t('succession_coverage_report', 'Succession Coverage Report'),
                             coverage=coverage)
    finally:
        db.close()


@talent_bp.route('/reports/hipo')
@talent_login_required
@talent_permission_required('view')
def report_hipo():
    """Hi-Po identification report."""
    db = get_t_db()
    try:
        hipos = db.execute("""
            SELECT tp.*, e.first_name, e.last_name, e.employee_code,
                   d.name as department_name, p.title as position_title,
                   m.first_name || ' ' || m.last_name as manager_name
            FROM tm_talent_profiles tp
            JOIN hr_employees e ON tp.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            LEFT JOIN hr_positions p ON ee.position_id = p.id
            LEFT JOIN hr_employees m ON ee.reporting_to_id = m.id
            WHERE tp.hi_po = 1 AND e.status = 'Active'
            ORDER BY tp.potential_score DESC, e.last_name
        """).fetchall()
        
        return render_template('talent/reports/hipo.html',
                             title=t('hipo_report', 'High Potential Report'),
                             hipos=[dict(h) for h in hipos])
    finally:
        db.close()


@talent_bp.route('/export')
@talent_login_required
@talent_permission_required('view')
def export_center():
    """Export center for talent data."""
    return render_template('talent/export/index.html',
                         title=t('export_center', 'Export Center'))


@talent_bp.route('/export/profiles', methods=['POST'])
@talent_login_required
@talent_permission_required('view')
def export_profiles():
    """Export talent profiles."""
    db = get_t_db()
    try:
        format_type = request.form.get('format', 'csv')
        columns = request.form.getlist('columns')
        department = request.form.get('department', '')
        
        # Build query
        query = """
            SELECT e.employee_code, e.first_name, e.last_name, e.email,
                   d.name as department_name, p.title as position_title,
                   tp.potential_rating, tp.readiness_level, tp.performance_rating,
                   tp.hi_po, tp.succession_candidate, tp.career_interests
            FROM tm_talent_profiles tp
            JOIN hr_employees e ON tp.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            LEFT JOIN hr_positions p ON ee.position_id = p.id
            WHERE e.status = 'Active'
        """
        params = []
        
        if department:
            query += " AND ee.department_id = ?"
            params.append(department)
        
        query += " ORDER BY e.last_name"
        
        profiles = db.execute(query, params).fetchall()
        
        if format_type == 'csv':
            return _export_csv([dict(p) for p in profiles], 'talent_profiles')
        elif format_type == 'excel':
            return _export_excel([dict(p) for p in profiles], 'talent_profiles')
        else:
            flash(t('invalid_format', 'Invalid export format.'), 'warning')
            return redirect(url_for('talent.export_center'))
    finally:
        db.close()


# =============================================================================
# SETTINGS
# =============================================================================

@talent_bp.route('/settings')
@talent_login_required
@talent_permission_required('admin')
def settings():
    """Talent management settings."""
    db = get_t_db()
    try:
        settings_list = db.execute("""
            SELECT * FROM tm_talent_settings ORDER BY category, setting_key
        """).fetchall()
        
        # Group by category
        settings_by_cat = {}
        for s in settings_list:
            cat = s['category'] or 'General'
            if cat not in settings_by_cat:
                settings_by_cat[cat] = []
            settings_by_cat[cat].append(dict(s))
        
        return render_template('talent/settings/index.html',
                             title=t('talent_settings', 'Talent Settings'),
                             settings_by_cat=settings_by_cat)
    finally:
        db.close()


@talent_bp.route('/settings/update', methods=['POST'])
@talent_login_required
@talent_permission_required('admin')
def settings_update():
    """Update talent settings."""
    db = get_t_db()
    try:
        for key, value in request.form.items():
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                db.execute("""
                    UPDATE tm_talent_settings SET setting_value = ?, updated_at = datetime('now')
                    WHERE setting_key = ?
                """, (value, setting_key))
        
        log_talent_audit('talent_settings', 0, 'UPDATE_ALL',
                        user_id=get_current_user_id(), ip_address=get_user_ip())
        
        db.commit()
        flash(t('settings_updated', 'Talent settings updated.'), 'success')
        return redirect(url_for('talent.settings'))
    finally:
        db.close()


# =============================================================================
# API ENDPOINTS
# =============================================================================

@talent_bp.route('/api/metrics')
@talent_login_required
def api_talent_metrics():
    """API endpoint for talent dashboard metrics."""
    db = get_t_db()
    try:
        metrics = _get_talent_metrics(db)
        return jsonify({'success': True, 'data': metrics})
    finally:
        db.close()


@talent_bp.route('/api/competencies/<int:employee_id>')
@talent_login_required
def api_employee_competencies(employee_id):
    """API endpoint for employee competencies."""
    competencies = _get_employee_competencies_with_gaps(get_t_db(), employee_id)
    return jsonify({'success': True, 'data': competencies})


@talent_bp.route('/api/pools/<int:pool_id>/members')
@talent_login_required
def api_pool_members(pool_id):
    """API endpoint for pool members."""
    if TALENT_MODELS_AVAILABLE:
        members = get_talent_pool_members(pool_id)
    else:
        members = _get_pool_members_fallback(get_t_db(), pool_id)
    return jsonify({'success': True, 'data': members})


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_talent_metrics(db):
    """Get talent dashboard metrics."""
    try:
        metrics = {
            'total_profiles': 0,
            'hi_po_count': 0,
            'critical_without_successor': 0,
            'succession_coverage': 0,
            'idp_in_progress': 0,
            'active_reviews': 0,
            'readiness_dist': {}
        }
        
        if TALENT_MODELS_AVAILABLE:
            metrics = get_talent_dashboard_metrics(db)
        else:
            # Fallback queries
            metrics['total_profiles'] = db.execute("SELECT COUNT(*) as cnt FROM tm_talent_profiles").fetchone()['cnt']
            metrics['hi_po_count'] = db.execute("SELECT COUNT(*) as cnt FROM tm_talent_profiles WHERE hi_po = 1").fetchone()['cnt']
            metrics['critical_without_successor'] = db.execute("""
                SELECT COUNT(*) as cnt FROM tm_critical_roles cr
                LEFT JOIN tm_succession_plans sp ON cr.id = sp.critical_role_id
                WHERE cr.status = 'Active' AND sp.id IS NULL
            """).fetchone()['cnt']
            metrics['idp_in_progress'] = db.execute("SELECT COUNT(*) as cnt FROM tm_development_plans WHERE status = 'In Progress'").fetchone()['cnt']
            metrics['active_reviews'] = db.execute("SELECT COUNT(*) as cnt FROM tm_talent_reviews WHERE status IN ('Planning', 'In Progress')").fetchone()['cnt']
        
        return metrics
    except Exception as e:
        return {
            'total_profiles': 0, 'hi_po_count': 0, 'critical_without_successor': 0,
            'succession_coverage': 0, 'idp_in_progress': 0, 'active_reviews': 0,
            'readiness_dist': {}
        }


def _get_recent_talent_activity(db, limit=10):
    """Get recent talent management activity."""
    try:
        activities = db.execute(f"""
            SELECT h.*, e.first_name || ' ' || e.last_name as employee_name
            FROM tm_talent_history h
            JOIN hr_employees e ON h.employee_id = e.id
            ORDER BY h.changed_at DESC LIMIT {limit}
        """).fetchall()
        return [dict(a) for a in activities]
    except:
        return []


def _get_pending_talent_approvals(db, limit=5):
    """Get pending talent approvals."""
    try:
        approvals = db.execute(f"""
            SELECT a.*, e.first_name || ' ' || e.last_name as employee_name,
                   t.table_name as approval_type_name
            FROM approvals a
            JOIN hr_employees e ON a.employee_id = e.id
            LEFT JOIN approval_types t ON a.approval_type = t.id
            WHERE a.status = 'Pending'
            ORDER BY a.created_at DESC LIMIT {limit}
        """).fetchall()
        return [dict(a) for a in approvals]
    except:
        return []


def _get_hipo_summary(db):
    """Get Hi-Po summary."""
    try:
        hipos = db.execute("""
            SELECT tp.*, e.first_name, e.last_name,
                   d.name as department_name
            FROM tm_talent_profiles tp
            JOIN hr_employees e ON tp.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            WHERE tp.hi_po = 1 AND e.status = 'Active'
            ORDER BY tp.potential_score DESC
            LIMIT 10
        """).fetchall()
        return [dict(h) for h in hipos]
    except:
        return []


def _get_succession_overview(db):
    """Get succession overview."""
    try:
        overview = {
            'critical_roles': 0,
            'covered': 0,
            'at_risk': 0,
            'emergency_ready': 0
        }
        
        overview['critical_roles'] = db.execute("SELECT COUNT(*) as cnt FROM tm_critical_roles WHERE status = 'Active'").fetchone()['cnt']
        overview['covered'] = db.execute("""
            SELECT COUNT(DISTINCT cr.id) as cnt
            FROM tm_critical_roles cr
            JOIN tm_succession_plans sp ON cr.id = sp.critical_role_id
            WHERE cr.status = 'Active' AND sp.status = 'Approved'
        """).fetchone()['cnt']
        overview['at_risk'] = overview['critical_roles'] - overview['covered']
        overview['emergency_ready'] = db.execute("""
            SELECT COUNT(*) as cnt FROM tm_critical_roles WHERE status = 'Active' AND emergency_ready = 1
        """).fetchone()['cnt']
        
        return overview
    except:
        return {'critical_roles': 0, 'covered': 0, 'at_risk': 0, 'emergency_ready': 0}


def _get_dev_plan_summary(db):
    """Get development plan summary."""
    try:
        summary = {
            'total': 0,
            'draft': 0,
            'in_progress': 0,
            'completed': 0,
            'completion_rate': 0
        }
        
        counts = db.execute("""
            SELECT status, COUNT(*) as cnt
            FROM tm_development_plans
            GROUP BY status
        """).fetchall()
        
        for c in counts:
            summary['total'] += c['cnt']
            if c['status'] == 'Draft':
                summary['draft'] = c['cnt']
            elif c['status'] == 'In Progress':
                summary['in_progress'] = c['cnt']
            elif c['status'] == 'Completed':
                summary['completed'] = c['cnt']
        
        if summary['total'] > 0:
            summary['completion_rate'] = round((summary['completed'] / summary['total']) * 100, 1)
        
        return summary
    except:
        return {'total': 0, 'draft': 0, 'in_progress': 0, 'completed': 0, 'completion_rate': 0}


def _get_executive_talent_metrics(db):
    """Get executive-level talent metrics."""
    metrics = _get_talent_metrics(db)
    
    # Add executive-specific metrics
    metrics['board_ready_count'] = db.execute("""
        SELECT COUNT(*) as cnt FROM tm_talent_profiles 
        WHERE hi_po = 1 AND readiness_level = 'Ready Now'
    """).fetchone()['cnt']
    
    metrics['flight_risk_count'] = db.execute("SELECT COUNT(*) as cnt FROM tm_talent_profiles WHERE flight_risk = 1").fetchone()['cnt']
    
    return metrics


def _get_talent_risk_indicators(db):
    """Get talent risk indicators."""
    try:
        risks = []
        
        # Critical roles without successors
        at_risk = db.execute("""
            SELECT cr.*, p.title as position_title
            FROM tm_critical_roles cr
            JOIN hr_positions p ON cr.position_id = p.id
            LEFT JOIN tm_succession_plans sp ON cr.id = sp.critical_role_id AND sp.status = 'Approved'
            WHERE cr.status = 'Active' AND sp.id IS NULL
        """).fetchall()
        
        for r in at_risk:
            risks.append({
                'type': 'critical_role',
                'severity': 'high',
                'position': r['position_title'],
                'description': t('no_successor', 'No successor identified')
            })
        
        # Retention risks
        flight_risks = db.execute("""
            SELECT tp.*, e.first_name, e.last_name
            FROM tm_talent_profiles tp
            JOIN hr_employees e ON tp.employee_id = e.id
            WHERE tp.flight_risk = 1
        """).fetchall()
        
        for r in flight_risks:
            risks.append({
                'type': 'retention',
                'severity': 'medium',
                'employee': f"{r['first_name']} {r['last_name']}",
                'description': t('flight_risk', 'Flight risk identified')
            })
        
        return risks
    except:
        return []


def _get_critical_risk_positions(db):
    """Get critical positions at risk."""
    try:
        positions = db.execute("""
            SELECT cr.*, p.title as position_title, d.name as department_name,
                   e.first_name || ' ' || e.last_name as incumbent_name,
                   (SELECT COUNT(*) FROM tm_succession_plans WHERE critical_role_id = cr.id AND status = 'Approved') as successor_count
            FROM tm_critical_roles cr
            JOIN hr_positions p ON cr.position_id = p.id
            LEFT JOIN hr_departments d ON cr.department_id = d.id
            LEFT JOIN hr_employees e ON cr.incumbent_id = e.id
            WHERE cr.status = 'Active'
            ORDER BY cr.criticality_level
        """).fetchall()
        return [dict(p) for p in positions]
    except:
        return []


def _get_hipo_pipeline(db):
    """Get Hi-Po pipeline health."""
    try:
        pipeline = {
            'ready_now': 0,
            'ready_1yr': 0,
            'developing': 0,
            'total': 0
        }
        
        counts = db.execute("""
            SELECT tp.readiness_level, COUNT(*) as cnt
            FROM tm_talent_profiles tp
            JOIN hr_employees e ON tp.employee_id = e.id
            WHERE tp.hi_po = 1 AND e.status = 'Active'
            GROUP BY tp.readiness_level
        """).fetchall()
        
        for c in counts:
            pipeline['total'] += c['cnt']
            if c['readiness_level'] == 'Ready Now':
                pipeline['ready_now'] = c['cnt']
            elif c['readiness_level'] in ('6 Months', '1 Year'):
                pipeline['ready_1yr'] += c['cnt']
            else:
                pipeline['developing'] += c['cnt']
        
        return pipeline
    except:
        return {'ready_now': 0, 'ready_1yr': 0, 'developing': 0, 'total': 0}


def _get_workforce_capability_summary(db):
    """Get workforce capability summary."""
    try:
        summary = {
            'leadership_ready': 0,
            'leadership_pipeline': 0,
            'critical_skills_count': 0,
            'skills_gap_count': 0
        }
        
        summary['leadership_ready'] = db.execute("""
            SELECT COUNT(*) as cnt FROM tm_talent_profiles 
            WHERE hi_po = 1 AND readiness_level = 'Ready Now'
        """).fetchone()['cnt']
        
        summary['leadership_pipeline'] = db.execute("""
            SELECT COUNT(*) as cnt FROM tm_talent_profiles 
            WHERE hi_po = 1 AND readiness_level IN ('6 Months', '1 Year')
        """).fetchone()['cnt']
        
        summary['skills_gap_count'] = db.execute("""
            SELECT COUNT(*) as cnt FROM tm_employee_competencies WHERE gap_score < 0 AND status = 'Active'
        """).fetchone()['cnt']
        
        return summary
    except:
        return {'leadership_ready': 0, 'leadership_pipeline': 0, 'critical_skills_count': 0, 'skills_gap_count': 0}


def _get_employee_competencies_with_gaps(db, employee_id):
    """Get employee competencies with gap analysis."""
    try:
        competencies = db.execute("""
            SELECT ec.*, c.name as competency_name, c.name_ar, c.name_fa,
                   cat.name as category_name,
                   c.proficiency_levels
            FROM tm_employee_competencies ec
            JOIN tm_competencies c ON ec.competency_id = c.id
            LEFT JOIN tm_competency_categories cat ON c.category_id = cat.id
            WHERE ec.employee_id = ? AND ec.status = 'Active'
            ORDER BY cat.name, c.name
        """, (employee_id,)).fetchall()
        return [dict(c) for c in competencies]
    except:
        return []


def _get_employee_pool_memberships(db, employee_id):
    """Get employee's talent pool memberships."""
    try:
        memberships = db.execute("""
            SELECT m.*, tp.name as pool_name, tp.pool_type, tp.color_code, tp.icon_class,
                   n.first_name || ' ' || n.last_name as nominated_by_name
            FROM tm_talent_pool_members m
            JOIN tm_talent_pools tp ON m.pool_id = tp.id
            LEFT JOIN hr_employees n ON m.nominated_by = n.id
            WHERE m.employee_id = ? AND m.status = 'Active'
            ORDER BY tp.pool_type, m.joined_date
        """, (employee_id,)).fetchall()
        return [dict(m) for m in memberships]
    except:
        return []


def _get_employee_development_plans(db, employee_id):
    """Get employee's development plans."""
    try:
        plans = db.execute("""
            SELECT dp.*, 
                   (SELECT COUNT(*) FROM tm_development_goals WHERE plan_id = dp.id) as total_goals,
                   (SELECT COUNT(*) FROM tm_development_goals WHERE plan_id = dp.id AND status = 'Completed') as completed_goals
            FROM tm_development_plans dp
            WHERE dp.employee_id = ?
            ORDER BY dp.plan_year DESC
        """, (employee_id,)).fetchall()
        return [dict(p) for p in plans]
    except:
        return []


def _get_succession_for_employee(db, employee_id):
    """Get succession plans where this employee is incumbent."""
    try:
        plans = db.execute("""
            SELECT sp.*, cr.position_id, p.title as position_title,
                   s.first_name || ' ' || s.last_name as successor_name
            FROM tm_succession_plans sp
            JOIN tm_critical_roles cr ON sp.critical_role_id = cr.id
            JOIN hr_positions p ON cr.position_id = p.id
            LEFT JOIN hr_employees s ON sp.successor_id = s.id
            WHERE sp.employee_id = ? AND sp.status IN ('Draft', 'Approved')
        """, (employee_id,)).fetchall()
        return [dict(p) for p in plans]
    except:
        return []


def _get_talent_notes(db, employee_id):
    """Get talent notes for employee."""
    try:
        notes = db.execute("""
            SELECT n.*, e.first_name || ' ' || e.last_name as created_by_name
            FROM tm_talent_notes n
            JOIN hr_employees e ON n.created_by = e.id
            WHERE n.employee_id = ?
            ORDER BY n.created_at DESC
        """, (employee_id,)).fetchall()
        return [dict(n) for n in notes]
    except:
        return []


def _get_talent_history(db, employee_id, limit=20):
    """Get talent change history."""
    try:
        history = db.execute(f"""
            SELECT h.*, e.first_name || ' ' || e.last_name as changed_by_name
            FROM tm_talent_history h
            JOIN hr_employees e ON h.changed_by = e.id
            WHERE h.employee_id = ?
            ORDER BY h.changed_at DESC LIMIT {limit}
        """, (employee_id,)).fetchall()
        return [dict(h) for h in history]
    except:
        return []


def _get_employee_performance(db, employee_id):
    """Get employee performance reviews."""
    try:
        perf = db.execute("""
            SELECT * FROM hr_performance_reviews
            WHERE employee_id = ?
            ORDER BY review_date DESC
            LIMIT 5
        """, (employee_id,)).fetchall()
        return [dict(p) for p in perf]
    except:
        return []


def _get_employee_training(db, employee_id):
    """Get employee training history."""
    try:
        training = db.execute("""
            SELECT te.*, tp.title as program_name, ts.session_title
            FROM hr_training_enrollments te
            JOIN hr_training_sessions ts ON te.session_id = ts.id
            JOIN hr_training_programs tp ON ts.program_id = tp.id
            WHERE te.employee_id = ?
            ORDER BY te.enrollment_date DESC
        """, (employee_id,)).fetchall()
        return [dict(t) for t in training]
    except:
        return []


def _get_potential_successors(db, role_id):
    """Get potential successors for a critical role."""
    try:
        # Get position requirements
        cr = db.execute("SELECT position_id FROM tm_critical_roles WHERE id = ?", (role_id,)).fetchone()
        if not cr:
            return []
        
        position_id = cr['position_id']
        
        # Get high-performing, high-potential employees who could be successors
        successors = db.execute("""
            SELECT tp.*, e.first_name, e.last_name, e.employee_code,
                   d.name as department_name, p.title as position_title,
                   m.first_name || ' ' || m.last_name as manager_name
            FROM tm_talent_profiles tp
            JOIN hr_employees e ON tp.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            LEFT JOIN hr_positions p ON ee.position_id = p.id
            LEFT JOIN hr_employees m ON ee.reporting_to_id = m.id
            WHERE e.status = 'Active' 
            AND (tp.performance_score >= 3 OR tp.performance_rating IN ('Exceeds', 'Exceptional'))
            AND (tp.potential_score >= 3 OR tp.potential_rating IN ('High', 'Very High'))
            ORDER BY tp.potential_score DESC, tp.performance_score DESC
        """).fetchall()
        
        return [dict(s) for s in successors]
    except:
        return []


def _get_nine_box_data(db, review_id):
    """Get 9-box grid data for talent review."""
    try:
        participants = db.execute("""
            SELECT * FROM tm_talent_review_participants WHERE review_id = ?
        """, (review_id,)).fetchall()
        
        grid = {
            '9_high_perf_high_pot': [],    # Top right
            '8_high_perf_mid_pot': [],
            '7_high_perf_low_pot': [],     # Top left
            '6_mid_perf_high_pot': [],
            '5_mid_perf_mid_pot': [],      # Center
            '4_mid_perf_low_pot': [],
            '3_low_perf_high_pot': [],
            '2_low_perf_mid_pot': [],
            '1_low_perf_low_pot': []       # Bottom left
        }
        
        for p in participants:
            perf = p.get('performance_rating', '')
            pot = p.get('potential_rating', '')
            
            if perf in ('Exceeds', 'Exceptional', '5') and pot in ('Very High', 'High', '5'):
                grid['9_high_perf_high_pot'].append(dict(p))
            elif perf in ('Exceeds', 'Exceptional', '5') and pot in ('Medium', '4'):
                grid['8_high_perf_mid_pot'].append(dict(p))
            elif perf in ('Exceeds', 'Exceptional', '5') and pot in ('Low', 'Developing', '3'):
                grid['7_high_perf_low_pot'].append(dict(p))
            elif perf in ('Meets', '4') and pot in ('Very High', 'High', '5'):
                grid['6_mid_perf_high_pot'].append(dict(p))
            elif perf in ('Meets', '4') and pot in ('Medium', '4'):
                grid['5_mid_perf_mid_pot'].append(dict(p))
            elif perf in ('Meets', '4') and pot in ('Low', 'Developing', '3'):
                grid['4_mid_perf_low_pot'].append(dict(p))
            elif perf in ('Below', 'Does Not Meet', '3') and pot in ('Very High', 'High', '5'):
                grid['3_low_perf_high_pot'].append(dict(p))
            elif perf in ('Below', 'Does Not Meet', '3') and pot in ('Medium', '4'):
                grid['2_low_perf_mid_pot'].append(dict(p))
            else:
                grid['1_low_perf_low_pot'].append(dict(p))
        
        return grid
    except:
        return {k: [] for k in ['9_high_perf_high_pot', '8_high_perf_mid_pot', '7_high_perf_low_pot',
                                '6_mid_perf_high_pot', '5_mid_perf_mid_pot', '4_mid_perf_low_pot',
                                '3_low_perf_high_pot', '2_low_perf_mid_pot', '1_low_perf_low_pot']}


def _get_bench_strength_by_department(db):
    """Get bench strength metrics by department."""
    try:
        bench = db.execute("""
            SELECT d.name as department_name,
                   COUNT(DISTINCT cr.id) as critical_roles,
                   SUM(CASE WHEN sp.id IS NOT NULL AND sp.status = 'Approved' THEN 1 ELSE 0 END) as covered_roles,
                   (SELECT COUNT(*) FROM tm_succession_plans sp2
                    JOIN tm_critical_roles cr2 ON sp2.critical_role_id = cr2.id
                    WHERE cr2.department_id = d.id AND sp2.status = 'Approved' 
                    AND sp2.readiness_level = 'Ready Now') as ready_now
            FROM hr_departments d
            LEFT JOIN tm_critical_roles cr ON d.id = cr.department_id AND cr.status = 'Active'
            LEFT JOIN tm_succession_plans sp ON cr.id = sp.critical_role_id AND sp.status = 'Approved'
            WHERE d.status = 'Active'
            GROUP BY d.id, d.name
        """).fetchall()
        return [dict(b) for b in bench]
    except:
        return []


def _get_readiness_distribution(db):
    """Get readiness level distribution."""
    try:
        dist = db.execute("""
            SELECT readiness_level, COUNT(*) as cnt
            FROM tm_talent_profiles
            WHERE readiness_level IS NOT NULL
            GROUP BY readiness_level
        """).fetchall()
        return {d['readiness_level']: d['cnt'] for d in dist}
    except:
        return {}


def _get_capability_heatmap(db):
    """Get capability heatmap data."""
    try:
        heatmap = db.execute("""
            SELECT c.name as competency_name, cat.name as category_name,
                   AVG(ec.proficiency_level) as avg_proficiency,
                   AVG(ec.required_level) as avg_required,
                   MIN(ec.gap_score) as min_gap,
                   COUNT(DISTINCT ec.employee_id) as employee_count
            FROM tm_employee_competencies ec
            JOIN tm_competencies c ON ec.competency_id = c.id
            LEFT JOIN tm_competency_categories cat ON c.category_id = cat.id
            WHERE ec.status = 'Active'
            GROUP BY c.id, c.name
            ORDER BY cat.sort_order, c.name
        """).fetchall()
        return [dict(h) for h in heatmap]
    except:
        return []


def _get_leadership_pipeline(db):
    """Get leadership pipeline data."""
    try:
        pipeline = {
            'executive': [],
            'senior_manager': [],
            'manager': [],
            'senior_individual': []
        }
        
        # This would typically join with position grades/salary bands
        # Simplified version
        leaders = db.execute("""
            SELECT tp.*, e.first_name, e.last_name,
                   p.title as position_title, d.name as department_name
            FROM tm_talent_profiles tp
            JOIN hr_employees e ON tp.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_positions p ON ee.position_id = p.id
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            WHERE tp.hi_po = 1 AND e.status = 'Active'
            ORDER BY tp.potential_score DESC
        """).fetchall()
        
        return [dict(l) for l in leaders]
    except:
        return []


def _get_succession_coverage_report(db):
    """Get detailed succession coverage report."""
    try:
        coverage = db.execute("""
            SELECT cr.*, p.title as position_title, d.name as department_name,
                   e.first_name || ' ' || e.last_name as incumbent_name,
                   (SELECT COUNT(*) FROM tm_succession_plans WHERE critical_role_id = cr.id AND status = 'Approved') as successor_count,
                   (SELECT GROUP_CONCAT(e2.first_name || ' ' || e2.last_name) 
                    FROM tm_succession_plans sp2 
                    JOIN hr_employees e2 ON sp2.successor_id = e2.id
                    WHERE sp2.critical_role_id = cr.id AND sp2.status = 'Approved') as successor_names,
                   (SELECT sp3.readiness_level FROM tm_succession_plans sp3 
                    WHERE sp3.critical_role_id = cr.id AND sp3.status = 'Approved'
                    ORDER BY sp3.readiness_level LIMIT 1) as best_readiness
            FROM tm_critical_roles cr
            JOIN hr_positions p ON cr.position_id = p.id
            LEFT JOIN hr_departments d ON cr.department_id = d.id
            LEFT JOIN hr_employees e ON cr.incumbent_id = e.id
            WHERE cr.status = 'Active'
            ORDER BY cr.criticality_level, p.title
        """).fetchall()
        return [dict(c) for c in coverage]
    except:
        return []


def _get_dev_plans_fallback(db, status=None):
    """Fallback for development plans if TM models not available."""
    try:
        query = """
            SELECT dp.*, e.first_name || ' ' || e.last_name as employee_name
            FROM tm_development_plans dp
            JOIN hr_employees e ON dp.employee_id = e.id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND dp.status = ?"
            params.append(status)
        
        query += " ORDER BY dp.plan_year DESC"
        
        plans = db.execute(query, params).fetchall()
        return [dict(p) for p in plans]
    except:
        return []


def _get_pool_members_fallback(db, pool_id):
    """Fallback for pool members if TM models not available."""
    try:
        members = db.execute("""
            SELECT m.*, e.first_name, e.last_name, e.employee_code,
                   d.name as department_name
            FROM tm_talent_pool_members m
            JOIN hr_employees e ON m.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            WHERE m.pool_id = ? AND m.status = 'Active'
        """, (pool_id,)).fetchall()
        return [dict(m) for m in members]
    except:
        return []


def _export_csv(data, filename):
    """Export data as CSV."""
    output = io.StringIO()
    if data:
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{filename}_{datetime.now().strftime("%Y%m%d")}.csv'
    )


def _export_excel(data, filename):
    """Export data as Excel."""
    output = io.BytesIO()
    if data:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = filename[:31]
        
        # Write headers
        headers = list(data[0].keys())
        ws.append(headers)
        
        # Write data
        for row in data:
            ws.append(list(row.values()))
        
        wb.save(output)
        output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'{filename}_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )


# =============================================================================
# BLUEPRINT REGISTRATION
# =============================================================================

def register_talent_routes(app, get_database):
    """Register talent routes with Flask app."""
    global get_db
    if get_database:
        get_db = get_database
    
    app.register_blueprint(talent_bp)
    
    # Initialize talent tables if models available
    if TALENT_MODELS_AVAILABLE:
        try:
            run_talent_migrations()
        except Exception as e:
            print(f"Talent migrations warning: {e}")
    
    return talent_bp


# Export blueprint for registration
__all__ = ['talent_bp', 'register_talent_routes']
