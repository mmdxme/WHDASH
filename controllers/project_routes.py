"""
Project Management Routes
=========================
Comprehensive route handlers for the Project Management module.

ROUTE STRUCTURE:
- /project/dashboard - Main dashboard
- /project/executive - Executive dashboard
- /project/pmo - PMO Workspace
- /project/portfolio/ - Portfolio management
- /project/intake/ - Project intake/requests
- /project/list - Project list
- /project/create - Create project
- /project/<id>/detail - Project detail
- /project/<id>/edit - Edit project
- /project/<id>/charter - Project charter
- /project/<id>/phases - Project phases
- /project/<id>/wbs - WBS builder
- /project/<id>/milestones - Milestones
- /project/<id>/tasks - Task list
- /project/<id>/resources - Resource allocation
- /project/<id>/budget - Budget management
- /project/<id>/procurement - Procurement linkage
- /project/<id>/timesheet - Timesheet
- /project/<id>/risks - Risk register
- /project/<id>/issues - Issue register
- /project/<id>/changes - Change requests
- /project/<id>/documents - Documents
- /project/<id>/governance - Status & governance
- /project/reports/ - Reports section
- /project/settings/ - Settings

USAGE:
    from project_routes import register_project_routes
    register_project_routes(app)
"""

import json
import sqlite3
import io
import csv
from datetime import datetime, timedelta, date
from flask import Blueprint, request, session, redirect, url_for, flash, render_template, jsonify, send_file, make_response
from functools import wraps

from database import get_db, get_db_context, get_one, get_all, log_audit, create_notification
from permissions import user_has_permission, get_user_permissions
from navigation import get_main_menu, get_breadcrumbs, get_page_title, prepare_menu_for_template
from theme_engine import get_available_themes

# Import export utilities
from export_utils import (
    send_export_response,
    get_export_columns
)
from project_models import (
    init_project_tables, get_project_stats, get_active_projects, get_project_with_details,
    calculate_project_progress, log_project_audit, get_project_count,
    get_user_workload,
    PROJECT_TABLES
)


# Create blueprint
project_bp = Blueprint('project', __name__, url_prefix='/project')


# =============================================================================
# DECORATORS
# =============================================================================

def require_project_permission(resource: str, action: str = 'view'):
    """Decorator to require project management permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please login to access this page.", "error")
                return redirect(url_for('login'))
            
            user_id = session['user_id']
            if not user_has_permission(user_id, 'project', resource, action):
                flash(f"Access Denied. You don't have permission to {action} {resource}.", "error")
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_login(f):
    """Decorator requiring authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user_id():
    """Get current user ID from session."""
    return session.get('user_id', 0)


def get_current_user_name():
    """Get current user name."""
    user_id = session.get('user_id', 0)
    if user_id:
        user = get_one("SELECT username FROM users WHERE id = ?", (user_id,))
        if user:
            return user['username']
    return "System"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def init_project():
    """Initialize project management module."""
    init_project_tables()


def _build_context(user_id, language='en', extra_context=None):
    """Build common template context."""
    user_perms = get_user_permissions(user_id)
    menu = get_main_menu(user_id, language)
    current_path = request.path
    
    context = {
        'user_id': user_id,
        'username': session.get('username', 'User'),
        'language': language,
        'direction': 'rtl' if language in ['ar', 'fa'] else 'ltr',
        'menu': prepare_menu_for_template(menu, current_path),
        'permissions': user_perms,
        'available_themes': get_available_themes(),
        'notifications': [],  # Populated by notification system
    }
    
    if extra_context:
        context.update(extra_context)
    
    return context


def _has_project_access(user_id):
    """Check if user has any project module access."""
    return (user_has_permission(user_id, 'project', 'dashboard', 'view') or
            user_has_permission(user_id, 'project', 'projects', 'view') or
            user_has_permission(user_id, 'project', 'portfolio', 'view'))


def _can_access_project(user_id, project_id):
    """Check if user can access a specific project."""
    # Project managers, owners, sponsors can always access
    project = get_one("""
        SELECT owner_user_id, manager_user_id, sponsor_user_id, company_id
        FROM projects WHERE id = ?
    """, (project_id,))
    
    if not project:
        return False
    
    if project['owner_user_id'] == user_id or project['manager_user_id'] == user_id or project['sponsor_user_id'] == user_id:
        return True
    
    # Company-level access
    if session.get('company_id') == project['company_id']:
        return user_has_permission(user_id, 'project', 'projects', 'view')
    
    return False


def _get_project_settings():
    """Get project management settings."""
    settings = {}
    rows = get_all("SELECT setting_key, setting_value FROM project_settings")
    for row in rows:
        settings[row['setting_key']] = row['setting_value']
    return settings


def _generate_project_code():
    """Generate next project code."""
    prefix = 'PRJ'
    result = get_one("SELECT MAX(CAST(SUBSTR(project_code, 4) AS INTEGER)) as max_num FROM projects WHERE project_code LIKE ?", (f'{prefix}%',))
    next_num = (result['max_num'] or 0) + 1
    return f'{prefix}{next_num:05d}'


def _generate_task_code():
    """Generate next task code."""
    prefix = 'TSK'
    result = get_one("SELECT MAX(CAST(SUBSTR(task_code, 4) AS INTEGER)) as max_num FROM project_tasks WHERE task_code LIKE ?", (f'{prefix}%',))
    next_num = (result['max_num'] or 0) + 1
    return f'{prefix}{next_num:05d}'


def _generate_milestone_code():
    """Generate next milestone code."""
    prefix = 'MS'
    result = get_one("SELECT MAX(CAST(SUBSTR(milestone_code, 3) AS INTEGER)) as max_num FROM project_milestones WHERE milestone_code LIKE ?", (f'{prefix}%',))
    next_num = (result['max_num'] or 0) + 1
    return f'{prefix}{next_num:04d}'


def _generate_issue_number():
    """Generate next issue number."""
    prefix = 'ISS'
    result = get_one("SELECT MAX(CAST(SUBSTR(issue_number, 4) AS INTEGER)) as max_num FROM project_issues WHERE issue_number LIKE ?", (f'{prefix}%',))
    next_num = (result['max_num'] or 0) + 1
    return f'{prefix}{next_num:05d}'


# =============================================================================
# FLOW NOTIFICATION HELPERS
# =============================================================================

def create_project_flow_notification(
    notification_type: str,
    title: str,
    message: str,
    project_id: int = 0,
    project_code: str = "",
    entity_type: str = "",
    entity_id: int = 0,
    priority: str = "NORMAL",
    action_url: str = "",
    company_id: int = 0
):
    """Create a Flow notification for project events."""
    user_id = get_current_user_id()

    try:
        with get_db_context() as db:
            db.execute("""
                INSERT INTO flow_notifications 
                (notification_type, title, message, entity_type, entity_id,
                 entity_reference, project_id, priority, action_url, created_by, company_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                notification_type, title, message, entity_type, entity_id,
                project_code, project_id, priority, action_url, user_id, company_id
            ))
            db.commit()
            return True
    except Exception as e:
        print(f"Failed to create Flow notification: {e}")
        return False


def notify_project_created(project_id: int, project_code: str, project_name: str, company_id: int = 0):
    """Notify when a new project is created."""
    return create_project_flow_notification(
        notification_type="PROJECT_CREATED",
        title=f"New Project: {project_code}",
        message=f"Project '{project_name}' has been created",
        project_id=project_id,
        project_code=project_code,
        entity_type="project",
        entity_id=project_id,
        priority="NORMAL",
        action_url=f"/project/{project_id}/detail",
        company_id=company_id
    )


def notify_project_status_changed(project_id: int, project_code: str, old_status: str, new_status: str, company_id: int = 0):
    """Notify when project status changes."""
    priority = "HIGH" if new_status in ('On Hold', 'Cancelled') else "NORMAL"
    return create_project_flow_notification(
        notification_type="PROJECT_STATUS_CHANGED",
        title=f"Project Status Update: {project_code}",
        message=f"Status changed from '{old_status}' to '{new_status}'",
        project_id=project_id,
        project_code=project_code,
        entity_type="project",
        entity_id=project_id,
        priority=priority,
        action_url=f"/project/{project_id}/detail",
        company_id=company_id
    )


def notify_milestone_due(project_id: int, project_code: str, milestone_name: str, due_date: str, company_id: int = 0):
    """Notify when a milestone is approaching."""
    return create_project_flow_notification(
        notification_type="MILESTONE_DUE",
        title=f"Milestone Due: {milestone_name}",
        message=f"Milestone '{milestone_name}' is due on {due_date}",
        project_id=project_id,
        project_code=project_code,
        entity_type="milestone",
        priority="HIGH",
        action_url=f"/project/{project_id}/milestones",
        company_id=company_id
    )


def notify_task_assigned(project_id: int, project_code: str, task_name: str, assignee_name: str, company_id: int = 0):
    """Notify when a task is assigned."""
    return create_project_flow_notification(
        notification_type="TASK_ASSIGNED",
        title=f"Task Assigned: {task_name[:40]}",
        message=f"Task has been assigned to {assignee_name}",
        project_id=project_id,
        project_code=project_code,
        entity_type="task",
        priority="NORMAL",
        action_url=f"/project/{project_id}/tasks",
        company_id=company_id
    )


def notify_risk_identified(project_id: int, project_code: str, risk_title: str, severity: str, company_id: int = 0):
    """Notify when a new risk is identified."""
    priority = "HIGH" if severity in ('High', 'Critical') else "NORMAL"
    return create_project_flow_notification(
        notification_type="RISK_IDENTIFIED",
        title=f"Risk Identified: {risk_title[:40]}",
        message=f"Severity: {severity}",
        project_id=project_id,
        project_code=project_code,
        entity_type="risk",
        priority=priority,
        action_url=f"/project/{project_id}/risks",
        company_id=company_id
    )


def notify_issue_logged(project_id: int, project_code: str, issue_title: str, severity: str, company_id: int = 0):
    """Notify when a new issue is logged."""
    priority = "HIGH" if severity in ('High', 'Critical') or severity == 'Blocker' else "NORMAL"
    return create_project_flow_notification(
        notification_type="ISSUE_LOGGED",
        title=f"Issue Logged: {issue_title[:40]}",
        message=f"Severity: {severity}",
        project_id=project_id,
        project_code=project_code,
        entity_type="issue",
        priority=priority,
        action_url=f"/project/{project_id}/issues",
        company_id=company_id
    )


# =============================================================================
# PAGINATION & FILTERING HELPERS
# =============================================================================

def apply_filters(query, filters, allowed_fields):
    """Apply filters to a query string."""
    params = []
    for field, value in filters.items():
        if field in allowed_fields and value and value != '' and value != 'all':
            if field.endswith('_from'):
                base_field = field[:-4]
                if base_field in allowed_fields:
                    query += f" AND {base_field} >= ?"
                    params.append(value)
            elif field.endswith('_to'):
                base_field = field[:-3]
                if base_field in allowed_fields:
                    query += f" AND {base_field} <= ?"
                    params.append(value)
            elif field.endswith('_ids'):
                base_field = field[:-4]
                if base_field in allowed_fields and isinstance(value, list):
                    placeholders = ','.join('?' * len(value))
                    query += f" AND {base_field} IN ({placeholders})"
                    params.extend(value)
            else:
                query += f" AND {field} = ?"
                params.append(value)
    return query, params


def paginate_query(query, params, page=1, per_page=25, order_by='id DESC'):
    """Apply pagination to a query."""
    # Add ordering
    query += f" ORDER BY {order_by}"
    
    # Get total count
    count_query = f"SELECT COUNT(*) as cnt FROM ({query})"
    total = get_one(count_query, params)
    total_count = total['cnt'] if total else 0
    
    # Apply pagination
    offset = (page - 1) * per_page
    query += f" LIMIT {per_page} OFFSET {offset}"
    
    return query, params, total_count


# =============================================================================
# ROUTE: DASHBOARD
# =============================================================================

@project_bp.route('/')
@project_bp.route('/dashboard')
@require_login
def dashboard():
    """Main project management dashboard."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    if not _has_project_access(user_id):
        flash("Access denied. You don't have access to the Project Management module.", "error")
        return redirect(url_for('index'))
    
    company_id = session.get('company_id', 0)
    context = _build_context(user_id, language)
    context['page_title'] = get_page_title('/project/dashboard', 'Project Dashboard')
    
    # Get dashboard statistics
    stats = get_project_stats(company_id)
    context['stats'] = stats
    
    # Get active projects for the user
    active_projects = get_active_projects(company_id, limit=20)
    context['active_projects'] = active_projects
    
    # Get recent projects
    recent_projects = get_all("""
        SELECT p.*, pt.name as type_name, u.username as manager_name
        FROM projects p
        LEFT JOIN project_types pt ON p.project_type_id = pt.id
        LEFT JOIN users u ON p.manager_user_id = u.id
        WHERE p.is_archived = 0
        ORDER BY p.updated_at DESC
        LIMIT 10
    """)
    context['recent_projects'] = recent_projects
    
    # Get upcoming milestones
    upcoming_milestones = get_all("""
        SELECT pm.*, p.project_name, p.project_code
        FROM project_milestones pm
        JOIN projects p ON pm.project_id = p.id
        WHERE pm.status = 'Pending' 
        AND pm.planned_date BETWEEN date('now') AND date('now', '+30 days')
        ORDER BY pm.planned_date
        LIMIT 10
    """)
    context['upcoming_milestones'] = upcoming_milestones
    
    # Get overdue tasks
    overdue_tasks = get_all("""
        SELECT t.*, p.project_name, p.project_code, u.username as assigned_name
        FROM project_tasks t
        JOIN projects p ON t.project_id = p.id
        LEFT JOIN users u ON t.assigned_user_id = u.id
        WHERE t.status NOT IN ('Completed', 'Cancelled')
        AND t.planned_end_date < date('now')
        ORDER BY t.planned_end_date
        LIMIT 10
    """)
    context['overdue_tasks'] = overdue_tasks
    
    # Get my tasks
    my_tasks = get_all("""
        SELECT t.*, p.project_name, p.project_code
        FROM project_tasks t
        JOIN projects p ON t.project_id = p.id
        WHERE t.assigned_user_id = ?
        AND t.status NOT IN ('Completed', 'Cancelled')
        ORDER BY t.priority DESC, t.planned_end_date
        LIMIT 10
    """, (user_id,))
    context['my_tasks'] = my_tasks
    
    # Status breakdown for charts
    context['status_breakdown'] = stats.get('by_status', [])
    context['priority_breakdown'] = stats.get('by_priority', [])
    
    return render_template('project/dashboard.html', **context)


# =============================================================================
# ROUTE: EXECUTIVE DASHBOARD
# =============================================================================

@project_bp.route('/executive')
@require_login
def executive_dashboard():
    """Executive dashboard with portfolio overview."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    company_id = session.get('company_id', 0)
    
    context = _build_context(user_id, language)
    context['page_title'] = get_page_title('/project/executive', 'Executive Dashboard')
    
    # Portfolio statistics
    with get_db_context() as db:
        # Total portfolio value
        portfolio = db.execute("""
            SELECT 
                COUNT(*) as total_projects,
                SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'On Hold' THEN 1 ELSE 0 END) as on_hold,
                SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled,
                AVG(COALESCE(progress, 0)) as avg_progress
            FROM projects
            WHERE is_archived = 0
        """).fetchone()
        context['portfolio'] = dict(portfolio) if portfolio else {}
        
        # Projects by type
        by_type = [dict(row) for row in db.execute("""
            SELECT pt.name as type_name, COUNT(*) as cnt
            FROM projects p
            LEFT JOIN project_types pt ON p.project_type_id = pt.id
            WHERE p.is_archived = 0
            GROUP BY pt.id
            ORDER BY cnt DESC
        """).fetchall()]
        context['by_type'] = by_type
        
        # Projects by priority
        by_priority = [dict(row) for row in db.execute("""
            SELECT COALESCE(priority, 'Medium') as priority, COUNT(*) as cnt
            FROM projects
            WHERE is_archived = 0
            GROUP BY priority
            ORDER BY cnt DESC
        """).fetchall()]
        context['by_priority'] = by_priority
        
        # Resource utilization
        resource_util = db.execute("""
            SELECT 
                COUNT(DISTINCT resource_id) as total_resources,
                SUM(planned_hours) as total_planned_hours,
                SUM(actual_hours) as total_actual_hours,
                AVG(allocation_percentage) as avg_allocation
            FROM project_resource_allocations
        """).fetchone()
        context['resource_utilization'] = dict(resource_util) if resource_util else {}
        
        # Budget overview
        budget_overview = db.execute("""
            SELECT 
                COUNT(DISTINCT project_id) as projects_with_budget,
                SUM(planned_hours * 100) as estimated_cost
            FROM project_resource_allocations
        """).fetchone()
        context['budget_overview'] = dict(budget_overview) if budget_overview else {}
    
    return render_template('project/executive.html', **context)


# =============================================================================
# ROUTE: PMO WORKSPACE
# =============================================================================

@project_bp.route('/pmo')
@require_login
def pmo_workspace():
    """PMO Workspace with project management office tools."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    company_id = session.get('company_id', 0)
    
    context = _build_context(user_id, language)
    context['page_title'] = get_page_title('/project/pmo', 'PMO Workspace')
    
    # PMO-specific stats
    with get_db_context() as db:
        # Pending approvals
        pending_approvals = db.execute("""
            SELECT COUNT(*) as cnt FROM project_approval_records
            WHERE status = 'Pending'
        """).fetchone()
        context['pending_approvals'] = pending_approvals['cnt'] if pending_approvals else 0
        
        # Active blockers
        active_blockers = db.execute("""
            SELECT COUNT(*) as cnt FROM project_issues
            WHERE is_blocker = 1 AND status NOT IN ('Resolved', 'Closed')
        """).fetchone()
        context['active_blockers'] = active_blockers['cnt'] if active_blockers else 0
        
        # Projects needing attention
        at_risk_projects = db.execute("""
            SELECT COUNT(*) as cnt FROM projects
            WHERE is_archived = 0
            AND status NOT IN ('Completed', 'Cancelled')
            AND (
                planned_end_date < date('now', '+7 days')
                OR progress < 50
            )
        """).fetchone()
        context['at_risk_projects'] = at_risk_projects['cnt'] if at_risk_projects else 0
        
        # Templates available
        templates = db.execute("""
            SELECT COUNT(*) as cnt FROM project_templates
            WHERE is_active = 1
        """).fetchone()
        context['template_count'] = templates['cnt'] if templates else 0
        
        # All projects for management
        all_projects = [dict(row) for row in db.execute("""
            SELECT p.*, pt.name as type_name,
                   u.username as manager_name,
                   (SELECT COUNT(*) FROM project_tasks WHERE project_id = p.id AND is_archived = 0) as task_count,
                   (SELECT COUNT(*) FROM project_milestones WHERE project_id = p.id AND is_overdue = 1) as overdue_milestones
            FROM projects p
            LEFT JOIN project_types pt ON p.project_type_id = pt.id
            LEFT JOIN users u ON p.manager_user_id = u.id
            WHERE p.is_archived = 0
            ORDER BY p.priority DESC, p.planned_end_date
        """).fetchall()]
        context['all_projects'] = all_projects
    
    return render_template('project/pmo.html', **context)


# =============================================================================
# ROUTE: PORTFOLIO MANAGEMENT
# =============================================================================

@project_bp.route('/portfolio/')
@require_login
def portfolio_list():
    """List all project portfolios."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    context = _build_context(user_id, language)
    context['page_title'] = get_page_title('/project/portfolio/', 'Portfolio Management')
    
    # Get project categories as portfolios
    portfolios = get_all("""
        SELECT pc.*,
               (SELECT COUNT(*) FROM projects WHERE category_id = pc.id AND is_archived = 0) as project_count,
               (SELECT AVG(progress) FROM projects WHERE category_id = pc.id AND is_archived = 0) as avg_progress
        FROM project_categories pc
        WHERE pc.is_active = 1
        ORDER BY pc.name
    """)
    context['portfolios'] = portfolios
    
    return render_template('project/portfolio/list.html', **context)


@project_bp.route('/portfolio/<int:category_id>')
@require_login
def portfolio_detail(category_id):
    """View portfolio details with all related projects."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    context = _build_context(user_id, language)
    
    # Get category
    category = get_one("SELECT * FROM project_categories WHERE id = ?", (category_id,))
    if not category:
        flash("Portfolio not found.", "error")
        return redirect(url_for('project.portfolio_list'))
    
    context['category'] = category
    context['page_title'] = get_page_title('/project/portfolio/', f'Portfolio: {category["name"]}')
    
    # Get projects in this portfolio
    projects = get_all("""
        SELECT p.*, pt.name as type_name, u.username as manager_name,
               (SELECT COUNT(*) FROM project_tasks WHERE project_id = p.id AND is_archived = 0) as task_count,
               (SELECT COUNT(*) FROM project_milestones WHERE project_id = p.id AND status != 'Completed') as active_milestones
        FROM projects p
        LEFT JOIN project_types pt ON p.project_type_id = pt.id
        LEFT JOIN users u ON p.manager_user_id = u.id
        WHERE p.category_id = ? AND p.is_archived = 0
        ORDER BY p.priority DESC, p.planned_end_date
    """, (category_id,))
    context['projects'] = projects
    
    # Portfolio stats
    with get_db_context() as db:
        stats = db.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(COALESCE(progress, 0)) as avg_progress,
                SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed
            FROM projects
            WHERE category_id = ? AND is_archived = 0
        """, (category_id,)).fetchone()
        context['stats'] = dict(stats) if stats else {}
    
    return render_template('project/portfolio/detail.html', **context)


# =============================================================================
# ROUTE: PROJECT INTAKE
# =============================================================================

@project_bp.route('/intake/')
@require_login
def intake_list():
    """List project intake requests."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    context = _build_context(user_id, language)
    context['page_title'] = get_page_title('/project/intake/', 'Project Intake')
    
    # Get project types for filtering
    project_types = get_all("SELECT * FROM project_types WHERE is_active = 1 ORDER BY name")
    context['project_types'] = project_types
    
    # Get request priorities
    context['priorities'] = ['Low', 'Medium', 'High', 'Critical']
    
    # Get intake requests (projects with status Draft or Request)
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = """
        SELECT p.*, pt.name as type_name, u.username as requester_name
        FROM projects p
        LEFT JOIN project_types pt ON p.project_type_id = pt.id
        LEFT JOIN users u ON p.created_by_user_id = u.id
        WHERE p.status IN ('Draft', 'Request', 'Pending Approval')
    """
    params = []
    
    if status_filter != 'all':
        query += " AND p.status = ?"
        params.append(status_filter)
    
    query += " ORDER BY p.priority DESC, p.created_at DESC"
    
    # Pagination
    offset = (page - 1) * 25
    count_query = f"SELECT COUNT(*) as cnt FROM projects WHERE status IN ('Draft', 'Request', 'Pending Approval')"
    total = get_one(count_query)
    total_count = total['cnt'] if total else 0
    
    query += f" LIMIT 25 OFFSET {offset}"
    intakes = get_all(query, params)
    context['intakes'] = intakes
    context['pagination'] = {
        'page': page,
        'per_page': 25,
        'total': total_count,
        'pages': (total_count + 24) // 25
    }
    
    return render_template('project/intake/list.html', **context)


@project_bp.route('/intake/create', methods=['GET', 'POST'])
@require_login
def intake_create():
    """Create new project intake request."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    company_id = session.get('company_id', 0)
    
    context = _build_context(user_id, language)
    context['page_title'] = get_page_title('/project/intake/create', 'New Project Request')
    
    if request.method == 'POST':
        data = request.form
        
        project_code = _generate_project_code()
        project_name = data.get('project_name', '')
        project_type_id = data.get('project_type_id')
        category_id = data.get('category_id')
        description = data.get('description', '')
        priority = data.get('priority', 'Medium')
        planned_start_date = data.get('planned_start_date') or None
        planned_end_date = data.get('planned_end_date') or None
        target_completion_date = data.get('target_completion_date') or None
        manager_user_id = data.get('manager_user_id') or None
        sponsor_user_id = data.get('sponsor_user_id') or None
        department_id = session.get('department_id', 0)
        
        if not project_name:
            flash("Project name is required.", "error")
            return render_template('project/intake/create.html', **context)
        
        with get_db_context() as db:
            cursor = db.execute("""
                INSERT INTO projects (
                    project_code, project_name, project_type_id, category_id, description,
                    priority, status, planned_start_date, planned_end_date, target_completion_date,
                    manager_user_id, sponsor_user_id, department_id, company_id,
                    created_by_user_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'Draft', ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                project_code, project_name, project_type_id, category_id, description,
                priority, planned_start_date, planned_end_date, target_completion_date,
                manager_user_id, sponsor_user_id, department_id, company_id,
                user_id
            ))
            project_id = cursor.lastrowid
            db.commit()
        
        # Log audit
        log_project_audit(None, project_id, None, 'INTAKE_CREATED', 
                        new_value=f'Project {project_code} created via intake',
                        actor_user_id=user_id)
        
        # Notify
        notify_project_created(project_id, project_code, project_name, company_id)
        
        flash(f"Project request '{project_code}' created successfully.", "success")
        return redirect(url_for('project.intake_detail', project_id=project_id))
    
    # Get project types
    project_types = get_all("SELECT * FROM project_types WHERE is_active = 1 ORDER BY name")
    context['project_types'] = project_types
    
    # Get categories
    categories = get_all("SELECT * FROM project_categories WHERE is_active = 1 ORDER BY name")
    context['categories'] = categories
    
    # Get users for manager/sponsor dropdowns
    users = get_all("""
        SELECT id, username, first_name, last_name 
        FROM users 
        WHERE is_active = 1 
        ORDER BY username
    """)
    context['users'] = users
    
    return render_template('project/intake/create.html', **context)


@project_bp.route('/intake/<int:project_id>')
@require_login
def intake_detail(project_id):
    """View project intake request details."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    context = _build_context(user_id, language)
    
    project = get_project_with_details(get_db(), project_id)
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for('project.intake_list'))
    
    context['project'] = project
    context['page_title'] = get_page_title('/project/intake/', f'Request: {project["project_code"]}')
    
    return render_template('project/intake/detail.html', **context)


@project_bp.route('/intake/<int:project_id>/submit', methods=['POST'])
@require_login
def intake_submit(project_id):
    """Submit intake request for approval."""
    user_id = get_current_user_id()
    company_id = session.get('company_id', 0)
    
    project = get_one("SELECT * FROM projects WHERE id = ?", (project_id,))
    if not project:
        return jsonify({'success': False, 'message': 'Project not found'})
    
    old_status = project['status']
    
    with get_db_context() as db:
        db.execute("""
            UPDATE projects 
            SET status = 'Pending Approval', updated_at = datetime('now')
            WHERE id = ?
        """, (project_id,))
        
        # Log status update
        db.execute("""
            INSERT INTO project_status_updates (project_id, user_id, previous_status, new_status, update_note)
            VALUES (?, ?, ?, ?, ?)
        """, (project_id, user_id, old_status, 'Pending Approval', 'Submitted for approval'))
        db.commit()
    
    log_project_audit(None, project_id, None, 'INTAKE_SUBMITTED',
                    old_value=old_status, new_value='Pending Approval',
                    actor_user_id=user_id)
    
    notify_project_status_changed(project_id, project['project_code'], old_status, 'Pending Approval', company_id)
    
    flash("Project request submitted for approval.", "success")
    return redirect(url_for('project.intake_detail', project_id=project_id))


# =============================================================================
# ROUTE: PROJECT LIST
# =============================================================================

@project_bp.route('/list')
@require_login
def project_list():
    """List all projects with filtering and pagination."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    context = _build_context(user_id, language)
    context['page_title'] = get_page_title('/project/list', 'Projects')
    
    # Get filter parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', 'all')
    priority = request.args.get('priority', 'all')
    project_type = request.args.get('project_type', 'all')
    manager = request.args.get('manager', 'all')
    sort_by = request.args.get('sort', 'priority_desc')
    
    # Build query
    query = """
        SELECT p.*, pt.name as type_name, pc.name as category_name,
               u.username as manager_name, u2.username as owner_name
        FROM projects p
        LEFT JOIN project_types pt ON p.project_type_id = pt.id
        LEFT JOIN project_categories pc ON p.category_id = pc.id
        LEFT JOIN users u ON p.manager_user_id = u.id
        LEFT JOIN users u2 ON p.owner_user_id = u.id
        WHERE p.is_archived = 0
    """
    params = []
    
    # Apply filters
    if search:
        query += " AND (p.project_name LIKE ? OR p.project_code LIKE ?)"
        search_term = f'%{search}%'
        params.extend([search_term, search_term])
    
    if status != 'all':
        query += " AND p.status = ?"
        params.append(status)
    
    if priority != 'all':
        query += " AND p.priority = ?"
        params.append(priority)
    
    if project_type != 'all':
        query += " AND p.project_type_id = ?"
        params.append(project_type)
    
    if manager != 'all':
        query += " AND p.manager_user_id = ?"
        params.append(manager)
    
    # Apply sorting
    sort_mapping = {
        'priority_desc': 'p.priority DESC, p.project_code',
        'priority_asc': 'p.priority ASC, p.project_code',
        'name_asc': 'p.project_name ASC',
        'name_desc': 'p.project_name DESC',
        'date_asc': 'p.planned_start_date ASC',
        'date_desc': 'p.planned_start_date DESC',
        'progress_asc': 'p.progress ASC',
        'progress_desc': 'p.progress DESC',
        'updated_desc': 'p.updated_at DESC'
    }
    order_by = sort_mapping.get(sort_by, 'p.priority DESC, p.project_code')
    
    # Get total count
    count_query = query.replace(
        'SELECT p.*, pt.name as type_name, pc.name as category_name, u.username as manager_name, u2.username as owner_name',
        'SELECT COUNT(*) as cnt'
    )
    total = get_one(count_query, params)
    total_count = total['cnt'] if total else 0
    
    # Apply pagination
    offset = (page - 1) * per_page
    query += f" ORDER BY {order_by} LIMIT {per_page} OFFSET {offset}"
    
    projects = get_all(query, params)
    context['projects'] = projects
    context['pagination'] = {
        'page': page,
        'per_page': per_page,
        'total': total_count,
        'pages': (total_count + per_page - 1) // per_page
    }
    
    # Filter options for dropdowns
    context['project_types'] = get_all("SELECT * FROM project_types WHERE is_active = 1 ORDER BY name")
    context['statuses'] = ['Draft', 'Pending Approval', 'Active', 'On Hold', 'Completed', 'Cancelled']
    context['priorities'] = ['Low', 'Medium', 'High', 'Critical']
    context['managers'] = get_all("""
        SELECT DISTINCT u.id, u.username
        FROM users u
        JOIN projects p ON p.manager_user_id = u.id
        WHERE p.is_archived = 0
        ORDER BY u.username
    """)
    
    # Preserve filter values
    context['filters'] = {
        'search': search,
        'status': status,
        'priority': priority,
        'project_type': project_type,
        'manager': manager,
        'sort': sort_by
    }
    
    return render_template('project/list.html', **context)


# =============================================================================
# ROUTE: CREATE PROJECT
# =============================================================================

@project_bp.route('/create', methods=['GET', 'POST'])
@require_login
def project_create():
    """Create a new project."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    company_id = session.get('company_id', 0)
    department_id = session.get('department_id', 0)
    
    context = _build_context(user_id, language)
    context['page_title'] = get_page_title('/project/create', 'Create Project')
    
    if request.method == 'POST':
        data = request.form
        
        project_code = _generate_project_code()
        project_name = data.get('project_name', '')
        project_type_id = data.get('project_type_id') or None
        category_id = data.get('category_id') or None
        description = data.get('description', '')
        priority = data.get('priority', 'Medium')
        status = data.get('status', 'Draft')
        planned_start_date = data.get('planned_start_date') or None
        planned_end_date = data.get('planned_end_date') or None
        target_completion_date = data.get('target_completion_date') or None
        owner_user_id = data.get('owner_user_id') or None
        manager_user_id = data.get('manager_user_id') or None
        sponsor_user_id = data.get('sponsor_user_id') or None
        cost_center = data.get('cost_center', '')
        budget_code = data.get('budget_code', '')
        notes = data.get('notes', '')
        
        if not project_name:
            flash("Project name is required.", "error")
            return render_template('project/create.html', **context)
        
        with get_db_context() as db:
            cursor = db.execute("""
                INSERT INTO projects (
                    project_code, project_name, project_type_id, category_id, description,
                    priority, status, planned_start_date, planned_end_date, target_completion_date,
                    owner_user_id, manager_user_id, sponsor_user_id, cost_center, budget_code,
                    notes, department_id, company_id, created_by_user_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                project_code, project_name, project_type_id, category_id, description,
                priority, status, planned_start_date, planned_end_date, target_completion_date,
                owner_user_id, manager_user_id, sponsor_user_id, cost_center, budget_code,
                notes, department_id, company_id, user_id
            ))
            project_id = cursor.lastrowid
            db.commit()
        
        # Create initial approval record if status is Pending Approval
        if status == 'Pending Approval':
            with get_db_context() as db:
                db.execute("""
                    INSERT INTO project_approval_records
                    (project_id, approval_type, requester_user_id, status, submitted_at)
                    VALUES (?, 'Project Approval', ?, 'Pending', datetime('now'))
                """, (project_id, user_id))
                db.commit()
        
        log_project_audit(None, project_id, None, 'PROJECT_CREATED',
                        new_value=f'Project {project_code} created',
                        actor_user_id=user_id)
        
        notify_project_created(project_id, project_code, project_name, company_id)
        
        flash(f"Project '{project_code}' created successfully.", "success")
        return redirect(url_for('project.project_detail', project_id=project_id))
    
    # Get project types
    context['project_types'] = get_all("SELECT * FROM project_types WHERE is_active = 1 ORDER BY name")
    
    # Get categories
    context['categories'] = get_all("SELECT * FROM project_categories WHERE is_active = 1 ORDER BY name")
    
    # Get users
    context['users'] = get_all("""
        SELECT id, username, first_name, last_name 
        FROM users 
        WHERE is_active = 1 
        ORDER BY username
    """)
    
    return render_template('project/create.html', **context)


# =============================================================================
# ROUTE: PROJECT DETAIL
# =============================================================================

@project_bp.route('/<int:project_id>/detail')
@require_login
def project_detail(project_id):
    """View project details."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    if not _can_access_project(user_id, project_id):
        flash("You don't have access to this project.", "error")
        return redirect(url_for('project.project_list'))
    
    context = _build_context(user_id, language)
    
    project = get_project_with_details(get_db(), project_id)
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for('project.project_list'))
    
    context['project'] = project
    context['page_title'] = get_page_title('/project/', f'Project: {project["project_code"]}')
    
    # Calculate overall progress
    progress = calculate_project_progress(get_db(), project_id)
    context['calculated_progress'] = progress
    
    # Update project progress if different
    if project['progress'] != progress:
        with get_db_context() as db:
            db.execute("UPDATE projects SET progress = ? WHERE id = ?", (progress, project_id))
            db.commit()
    
    # Get audit log
    audit_log = get_all("""
        SELECT * FROM project_audit_logs
        WHERE project_id = ?
        ORDER BY created_at DESC
        LIMIT 20
    """, (project_id,))
    context['audit_log'] = audit_log
    
    # Get status updates
    status_updates = get_all("""
        SELECT su.*, u.username as updater_name
        FROM project_status_updates su
        LEFT JOIN users u ON su.user_id = u.id
        WHERE su.project_id = ?
        ORDER BY su.created_at DESC
        LIMIT 10
    """, (project_id,))
    context['status_updates'] = status_updates
    
    return render_template('project/detail.html', **context)


# =============================================================================
# ROUTE: EDIT PROJECT
# =============================================================================

@project_bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@require_login
def project_edit(project_id):
    """Edit project details."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    if not _can_access_project(user_id, project_id):
        flash("You don't have access to this project.", "error")
        return redirect(url_for('project.project_list'))
    
    context = _build_context(user_id, language)
    
    project = get_one("SELECT * FROM projects WHERE id = ?", (project_id,))
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for('project.project_list'))
    
    context['project'] = project
    context['page_title'] = get_page_title('/project/', f'Edit: {project["project_code"]}')
    
    if request.method == 'POST':
        data = request.form
        
        old_status = project['status']
        
        # Build update query dynamically
        update_fields = []
        params = []
        
        fields_to_update = [
            'project_name', 'project_type_id', 'category_id', 'description',
            'priority', 'status', 'planned_start_date', 'planned_end_date',
            'target_completion_date', 'actual_start_date', 'actual_end_date',
            'owner_user_id', 'manager_user_id', 'sponsor_user_id',
            'cost_center', 'budget_code', 'notes'
        ]
        
        for field in fields_to_update:
            if field in data:
                value = data[field] if data[field] else None
                update_fields.append(f"{field} = ?")
                params.append(value)
        
        update_fields.append("updated_at = datetime('now')")
        params.append(project_id)
        
        with get_db_context() as db:
            db.execute(f"""
                UPDATE projects 
                SET {', '.join(update_fields)}
                WHERE id = ?
            """, params)
            
            # Log status change
            new_status = data.get('status')
            if new_status and new_status != old_status:
                db.execute("""
                    INSERT INTO project_status_updates (project_id, user_id, previous_status, new_status, update_note)
                    VALUES (?, ?, ?, ?, ?)
                """, (project_id, user_id, old_status, new_status, data.get('status_note', '')))
            
            db.commit()
        
        # Audit
        log_project_audit(None, project_id, None, 'PROJECT_UPDATED',
                          new_value='Project details updated',
                          actor_user_id=user_id)
        
        # Notify on status change
        if new_status and new_status != old_status:
            company_id = session.get('company_id', 0)
            notify_project_status_changed(project_id, project['project_code'], old_status, new_status, company_id)
        
        flash("Project updated successfully.", "success")
        return redirect(url_for('project.project_detail', project_id=project_id))
    
    # Get dropdown options
    context['project_types'] = get_all("SELECT * FROM project_types WHERE is_active = 1 ORDER BY name")
    context['categories'] = get_all("SELECT * FROM project_categories WHERE is_active = 1 ORDER BY name")
    context['users'] = get_all("SELECT id, username, first_name, last_name FROM users WHERE is_active = 1 ORDER BY username")
    context['statuses'] = ['Draft', 'Pending Approval', 'Active', 'On Hold', 'Completed', 'Cancelled']
    context['priorities'] = ['Low', 'Medium', 'High', 'Critical']
    
    return render_template('project/edit.html', **context)


# =============================================================================
# ROUTE: PROJECT CHARTER
# =============================================================================

@project_bp.route('/<int:project_id>/charter')
@require_login
def project_charter(project_id):
    """View project charter."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    if not _can_access_project(user_id, project_id):
        flash("You don't have access to this project.", "error")
        return redirect(url_for('project.project_list'))
    
    context = _build_context(user_id, language)
    
    project = get_project_with_details(get_db(), project_id)
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for('project.project_list'))
    
    context['project'] = project
    context['page_title'] = get_page_title('/project/', f'Charter: {project["project_code"]}')
    
    return render_template('project/charter.html', **context)


# =============================================================================
# ROUTE: PROJECT PHASES
# =============================================================================

@project_bp.route('/<int:project_id>/phases')
@require_login
def project_phases(project_id):
    """View and manage project phases."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    if not _can_access_project(user_id, project_id):
        flash("You don't have access to this project.", "error")
        return redirect(url_for('project.project_list'))
    
    context = _build_context(user_id, language)
    
    project = get_one("SELECT * FROM projects WHERE id = ?", (project_id,))
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for('project.project_list'))
    
    context['project'] = project
    context['page_title'] = get_page_title('/project/', f'Phases: {project["project_code"]}')
    
    # Get phases with progress
    phases = get_all("""
        SELECT ph.*,
               (SELECT COUNT(*) FROM project_tasks WHERE phase_id = ph.id AND is_archived = 0) as task_count,
               (SELECT AVG(progress) FROM project_tasks WHERE phase_id = ph.id AND is_archived = 0) as avg_task_progress
        FROM project_phases ph
        WHERE ph.project_id = ?
        ORDER BY ph.phase_order
    """, (project_id,))
    context['phases'] = phases
    
    return render_template('project/phases.html', **context)


@project_bp.route('/<int:project_id>/phases/create', methods=['POST'])
@require_login
def phase_create(project_id):
    """Create a new phase."""
    user_id = get_current_user_id()
    
    if not _can_access_project(user_id, project_id):
        return jsonify({'success': False, 'message': 'Access denied'})
    
    data = request.get_json() or {}
    phase_name = data.get('phase_name', '')
    description = data.get('description', '')
    planned_start = data.get('planned_start_date')
    planned_end = data.get('planned_end_date')
    
    if not phase_name:
        return jsonify({'success': False, 'message': 'Phase name is required'})
    
    # Get next order
    max_order = get_one("SELECT MAX(phase_order) as max_order FROM project_phases WHERE project_id = ?", (project_id,))
    next_order = (max_order['max_order'] or 0) + 1
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO project_phases (project_id, phase_name, description, phase_order, 
                                       planned_start_date, planned_end_date, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending')
        """, (project_id, phase_name, description, next_order, planned_start, planned_end))
        phase_id = cursor.lastrowid
        db.commit()
    
    log_project_audit(None, project_id, None, 'PHASE_CREATED',
                     new_value=f'Phase {phase_name} created',
                     actor_user_id=user_id)
    
    return jsonify({'success': True, 'phase_id': phase_id})


@project_bp.route('/phase/<int:phase_id>', methods=['PUT', 'DELETE'])
@require_login
def phase_manage(phase_id):
    """Update or delete a phase."""
    user_id = get_current_user_id()
    
    phase = get_one("SELECT * FROM project_phases WHERE id = ?", (phase_id,))
    if not phase:
        return jsonify({'success': False, 'message': 'Phase not found'})
    
    if not _can_access_project(user_id, phase['project_id']):
        return jsonify({'success': False, 'message': 'Access denied'})
    
    if request.method == 'DELETE':
        with get_db_context() as db:
            db.execute("DELETE FROM project_phases WHERE id = ?", (phase_id,))
            db.commit()
        
        log_project_audit(None, phase['project_id'], None, 'PHASE_DELETED',
                        old_value=f'Phase {phase["phase_name"]}',
                        actor_user_id=user_id)
        
        return jsonify({'success': True})
    
    # PUT - Update
    data = request.get_json() or {}
    
    with get_db_context() as db:
        db.execute("""
            UPDATE project_phases
            SET phase_name = ?, description = ?, planned_start_date = ?, planned_end_date = ?,
                actual_start_date = ?, actual_end_date = ?, status = ?, progress = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (
            data.get('phase_name', phase['phase_name']),
            data.get('description', phase['description']),
            data.get('planned_start_date'),
            data.get('planned_end_date'),
            data.get('actual_start_date'),
            data.get('actual_end_date'),
            data.get('status', phase['status']),
            data.get('progress', 0),
            phase_id
        ))
        db.commit()
    
    log_project_audit(None, phase['project_id'], None, 'PHASE_UPDATED',
                     new_value=f'Phase {phase["phase_name"]} updated',
                     actor_user_id=user_id)
    
    return jsonify({'success': True})


# =============================================================================
# ROUTE: WBS BUILDER
# =============================================================================

@project_bp.route('/<int:project_id>/wbs')
@require_login
def project_wbs(project_id):
    """View and manage Work Breakdown Structure."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    if not _can_access_project(user_id, project_id):
        flash("You don't have access to this project.", "error")
        return redirect(url_for('project.project_list'))
    
    context = _build_context(user_id, language)
    
    project = get_one("SELECT * FROM projects WHERE id = ?", (project_id,))
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for('project.project_list'))
    
    context['project'] = project
    context['page_title'] = get_page_title('/project/', f'WBS: {project["project_code"]}')
    
    # Get WBS nodes in hierarchical order
    wbs_nodes = get_all("""
        SELECT w.*, u.username as created_by_name
        FROM project_wbs w
        LEFT JOIN users u ON w.created_at = w.created_at
        WHERE w.project_id = ?
        ORDER BY w.level, w.sort_order
    """, (project_id,))
    context['wbs_nodes'] = wbs_nodes
    
    # Build tree structure
    tree = []
    node_map = {}
    for node in wbs_nodes:
        node['children'] = []
        node_map[node['id']] = node
    
    for node in wbs_nodes:
        if node['parent_wbs_id']:
            if node['parent_wbs_id'] in node_map:
                node_map[node['parent_wbs_id']]['children'].append(node)
        else:
            tree.append(node)
    
    context['wbs_tree'] = tree
    
    return render_template('project/wbs.html', **context)


@project_bp.route('/<int:project_id>/wbs/create', methods=['POST'])
@require_login
def wbs_create(project_id):
    """Create a WBS node."""
    user_id = get_current_user_id()
    
    if not _can_access_project(user_id, project_id):
        return jsonify({'success': False, 'message': 'Access denied'})
    
    data = request.get_json() or {}
    wbs_code = data.get('wbs_code', '')
    wbs_name = data.get('wbs_name', '')
    parent_wbs_id = data.get('parent_wbs_id') or None
    level = data.get('level', 1)
    
    if not wbs_code or not wbs_name:
        return jsonify({'success': False, 'message': 'WBS code and name are required'})
    
    # Get sort order
    max_order = get_one("""
        SELECT MAX(sort_order) as max_order FROM project_wbs 
        WHERE project_id = ? AND parent_wbs_id IS ?
    """, (project_id, parent_wbs_id))
    next_order = (max_order['max_order'] or 0) + 1
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO project_wbs (project_id, parent_wbs_id, wbs_code, wbs_name, level, sort_order)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (project_id, parent_wbs_id, wbs_code, wbs_name, level, next_order))
        wbs_id = cursor.lastrowid
        db.commit()
    
    log_project_audit(None, project_id, None, 'WBS_CREATED',
                    new_value=f'WBS {wbs_code} created',
                    actor_user_id=user_id)
    
    return jsonify({'success': True, 'wbs_id': wbs_id})


# =============================================================================
# ROUTE: MILESTONES
# =============================================================================

@project_bp.route('/<int:project_id>/milestones')
@require_login
def project_milestones(project_id):
    """View and manage project milestones."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    if not _can_access_project(user_id, project_id):
        flash("You don't have access to this project.", "error")
        return redirect(url_for('project.project_list'))
    
    context = _build_context(user_id, language)
    
    project = get_one("SELECT * FROM projects WHERE id = ?", (project_id,))
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for('project.project_list'))
    
    context['project'] = project
    context['page_title'] = get_page_title('/project/', f'Milestones: {project["project_code"]}')
    
    # Get milestones
    milestones = get_all("""
        SELECT pm.*, u.username as owner_name,
               (SELECT task_name FROM project_tasks WHERE id IN (SELECT value FROM json_each(pm.related_task_ids))) as related_task
        FROM project_milestones pm
        LEFT JOIN users u ON pm.owner_user_id = u.id
        WHERE pm.project_id = ?
        ORDER BY pm.planned_date
    """, (project_id,))
    context['milestones'] = milestones
    
    # Get users for assignment
    context['users'] = get_all("SELECT id, username FROM users WHERE is_active = 1 ORDER BY username")
    
    return render_template('project/milestones.html', **context)


@project_bp.route('/<int:project_id>/milestones/create', methods=['POST'])
@require_login
def milestone_create(project_id):
    """Create a new milestone."""
    user_id = get_current_user_id()
    company_id = session.get('company_id', 0)
    
    if not _can_access_project(user_id, project_id):
        return jsonify({'success': False, 'message': 'Access denied'})
    
    data = request.get_json() or {}
    milestone_name = data.get('milestone_name', '')
    milestone_type = data.get('milestone_type', 'General')
    planned_date = data.get('planned_date')
    owner_user_id = data.get('owner_user_id')
    related_task_ids = data.get('related_task_ids', '')
    
    if not milestone_name:
        return jsonify({'success': False, 'message': 'Milestone name is required'})
    
    milestone_code = _generate_milestone_code()
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO project_milestones (project_id, milestone_code, milestone_name, milestone_type,
                                           owner_user_id, planned_date, target_date, status, related_task_ids)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending', ?)
        """, (project_id, milestone_code, milestone_name, milestone_type, owner_user_id, 
              planned_date, planned_date, related_task_ids))
        milestone_id = cursor.lastrowid
        db.commit()
    
    project = get_one("SELECT project_code FROM projects WHERE id = ?", (project_id,))
    log_project_audit(None, project_id, None, 'MILESTONE_CREATED',
                    new_value=f'Milestone {milestone_code} created',
                    actor_user_id=user_id)
    
    notify_milestone_due(project_id, project['project_code'], milestone_name, planned_date, company_id)
    
    return jsonify({'success': True, 'milestone_id': milestone_id})


@project_bp.route('/milestone/<int:milestone_id>', methods=['PUT', 'DELETE'])
@require_login
def milestone_manage(milestone_id):
    """Update or delete a milestone."""
    user_id = get_current_user_id()
    
    milestone = get_one("SELECT * FROM project_milestones WHERE id = ?", (milestone_id,))
    if not milestone:
        return jsonify({'success': False, 'message': 'Milestone not found'})
    
    if not _can_access_project(user_id, milestone['project_id']):
        return jsonify({'success': False, 'message': 'Access denied'})
    
    if request.method == 'DELETE':
        with get_db_context() as db:
            db.execute("DELETE FROM project_milestones WHERE id = ?", (milestone_id,))
            db.commit()
        
        log_project_audit(None, milestone['project_id'], None, 'MILESTONE_DELETED',
                         old_value=f'Milestone {milestone["milestone_code"]}',
                         actor_user_id=user_id)
        
        return jsonify({'success': True})
    
    # PUT
    data = request.get_json() or {}
    
    with get_db_context() as db:
        db.execute("""
            UPDATE project_milestones
            SET milestone_name = ?, milestone_type = ?, owner_user_id = ?,
                planned_date = ?, target_date = ?, actual_completion_date = ?,
                status = ?, notes = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (
            data.get('milestone_name', milestone['milestone_name']),
            data.get('milestone_type', milestone['milestone_type']),
            data.get('owner_user_id'),
            data.get('planned_date'),
            data.get('target_date'),
            data.get('actual_completion_date'),
            data.get('status', milestone['status']),
            data.get('notes', ''),
            milestone_id
        ))
        db.commit()
    
    return jsonify({'success': True})


# =============================================================================
# ROUTE: TASKS
# =============================================================================

@project_bp.route('/<int:project_id>/tasks')
@require_login
def project_tasks(project_id):
    """View and manage project tasks."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    if not _can_access_project(user_id, project_id):
        flash("You don't have access to this project.", "error")
        return redirect(url_for('project.project_list'))
    
    context = _build_context(user_id, language)
    
    project = get_one("SELECT * FROM projects WHERE id = ?", (project_id,))
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for('project.project_list'))
    
    context['project'] = project
    context['page_title'] = get_page_title('/project/', f'Tasks: {project["project_code"]}')
    
    # Get tasks with filtering
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    priority_filter = request.args.get('priority', 'all')
    assigned_filter = request.args.get('assigned', 'all')
    
    query = """
        SELECT t.*, u.username as assigned_name, ph.phase_name,
               (SELECT COUNT(*) FROM project_task_checklists WHERE parent_task_id = t.id) as subtask_count
        FROM project_tasks t
        LEFT JOIN users u ON t.assigned_user_id = u.id
        LEFT JOIN project_phases ph ON t.phase_id = ph.id
        WHERE t.project_id = ? AND t.is_archived = 0
    """
    params = [project_id]
    
    if status_filter != 'all':
        query += " AND t.status = ?"
        params.append(status_filter)
    
    if priority_filter != 'all':
        query += " AND t.priority = ?"
        params.append(priority_filter)
    
    if assigned_filter != 'all':
        query += " AND t.assigned_user_id = ?"
        params.append(assigned_filter)
    
    query += " ORDER BY t.priority DESC, t.planned_start_date"
    
    # Pagination
    offset = (page - 1) * 25
    count_query = query.replace("SELECT t.*, u.username as assigned_name, ph.phase_name,", "SELECT COUNT(*) as cnt ")
    total = get_one(count_query, query.replace("SELECT t.*, u.username as assigned_name, ph.phase_name,", "SELECT COUNT(*) as cnt FROM project_tasks t WHERE t.project_id = ? AND t.is_archived = 0"), params)
    
    # Simpler count
    count_result = get_one("SELECT COUNT(*) as cnt FROM project_tasks WHERE project_id = ? AND is_archived = 0", (project_id,))
    total_count = count_result['cnt'] if count_result else 0
    
    query += f" LIMIT 25 OFFSET {offset}"
    tasks = get_all(query, params)
    context['tasks'] = tasks
    
    context['pagination'] = {
        'page': page,
        'per_page': 25,
        'total': total_count,
        'pages': (total_count + 24) // 25
    }
    
    # Filter options
    context['phases'] = get_all("SELECT id, phase_name FROM project_phases WHERE project_id = ? ORDER BY phase_order", (project_id,))
    context['users'] = get_all("SELECT id, username FROM users WHERE is_active = 1 ORDER BY username")
    context['statuses'] = ['Draft', 'Pending', 'In Progress', 'Review', 'Completed', 'Cancelled']
    context['priorities'] = ['Low', 'Medium', 'High', 'Critical']
    
    context['filters'] = {
        'status': status_filter,
        'priority': priority_filter,
        'assigned': assigned_filter
    }
    
    return render_template('project/tasks.html', **context)


@project_bp.route('/<int:project_id>/tasks/create', methods=['GET', 'POST'])
@require_login
def task_create(project_id):
    """Create a new task."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    company_id = session.get('company_id', 0)
    
    if not _can_access_project(user_id, project_id):
        flash("You don't have access to this project.", "error")
        return redirect(url_for('project.project_list'))
    
    project = get_one("SELECT * FROM projects WHERE id = ?", (project_id,))
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for('project.project_list'))
    
    context = _build_context(user_id, language)
    context['project'] = project
    context['page_title'] = get_page_title('/project/', f'Create Task: {project["project_code"]}')
    
    if request.method == 'POST':
        data = request.form
        
        task_code = _generate_task_code()
        task_name = data.get('task_name', '')
        description = data.get('description', '')
        phase_id = data.get('phase_id') or None
        wbs_id = data.get('wbs_id') or None
        priority = data.get('priority', 'Medium')
        status = data.get('status', 'Draft')
        assigned_user_id = data.get('assigned_user_id') or None
        planned_start_date = data.get('planned_start_date') or None
        planned_end_date = data.get('planned_end_date') or None
        estimated_hours = data.get('estimated_hours', 0)
        deliverable = data.get('deliverable', '')
        notes = data.get('notes', '')
        
        if not task_name:
            flash("Task name is required.", "error")
            return render_template('project/task_create.html', **context)
        
        with get_db_context() as db:
            cursor = db.execute("""
                INSERT INTO project_tasks (
                    project_id, task_code, task_name, description, phase_id, wbs_id,
                    priority, status, assigned_user_id, planned_start_date, planned_end_date,
                    estimated_hours, deliverable, notes, created_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (project_id, task_code, task_name, description, phase_id, wbs_id,
                  priority, status, assigned_user_id, planned_start_date, planned_end_date,
                  estimated_hours, deliverable, notes, user_id))
            task_id = cursor.lastrowid
            db.commit()
        
        log_project_audit(None, project_id, task_id, 'TASK_CREATED',
                         new_value=f'Task {task_code} created',
                         actor_user_id=user_id)
        
        # Notify assignee
        if assigned_user_id:
            assignee = get_one("SELECT username FROM users WHERE id = ?", (assigned_user_id,))
            notify_task_assigned(project_id, project['project_code'], task_name, 
                               assignee['username'] if assignee else 'Unknown', company_id)
        
        flash(f"Task '{task_code}' created successfully.", "success")
        return redirect(url_for('project.project_tasks', project_id=project_id))
    
    context['phases'] = get_all("SELECT id, phase_name FROM project_phases WHERE project_id = ? ORDER BY phase_order", (project_id,))
    context['wbs_nodes'] = get_all("SELECT id, wbs_code, wbs_name FROM project_wbs WHERE project_id = ? ORDER BY sort_order", (project_id,))
    context['users'] = get_all("SELECT id, username FROM users WHERE is_active = 1 ORDER BY username")
    context['priorities'] = ['Low', 'Medium', 'High', 'Critical']
    context['statuses'] = ['Draft', 'Pending', 'In Progress', 'Review', 'Completed', 'Cancelled']
    
    return render_template('project/task_create.html', **context)


@project_bp.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
@require_login
def task_edit(task_id):
    """Edit a task."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    task = get_one("SELECT * FROM project_tasks WHERE id = ?", (task_id,))
    if not task:
        flash("Task not found.", "error")
        return redirect(url_for('project.project_list'))
    
    if not _can_access_project(user_id, task['project_id']):
        flash("You don't have access to this project.", "error")
        return redirect(url_for('project.project_list'))
    
    project = get_one("SELECT * FROM projects WHERE id = ?", (task['project_id'],))
    
    context = _build_context(user_id, language)
    context['project'] = project
    context['task'] = task
    context['page_title'] = get_page_title('/project/', f'Edit Task: {task["task_code"]}')
    
    if request.method == 'POST':
        data = request.form
        
        old_status = task['status']
        old_assignee = task['assigned_user_id']
        
        with get_db_context() as db:
            db.execute("""
                UPDATE project_tasks
                SET task_name = ?, description = ?, phase_id = ?, wbs_id = ?,
                    priority = ?, status = ?, assigned_user_id = ?,
                    planned_start_date = ?, planned_end_date = ?,
                    actual_start_date = ?, actual_end_date = ?,
                    estimated_hours = ?, actual_hours = ?, progress = ?,
                    deliverable = ?, notes = ?, updated_at = datetime('now')
                WHERE id = ?
            """, (
                data.get('task_name', task['task_name']),
                data.get('description', task['description']),
                data.get('phase_id') or None,
                data.get('wbs_id') or None,
                data.get('priority', task['priority']),
                data.get('status', task['status']),
                data.get('assigned_user_id') or None,
                data.get('planned_start_date'),
                data.get('planned_end_date'),
                data.get('actual_start_date'),
                data.get('actual_end_date'),
                data.get('estimated_hours', 0),
                data.get('actual_hours', 0),
                data.get('progress', 0),
                data.get('deliverable', ''),
                data.get('notes', ''),
                task_id
            ))
            db.commit()
        
        log_project_audit(None, task['project_id'], task_id, 'TASK_UPDATED',
                         new_value=f'Task {task["task_code"]} updated',
                         actor_user_id=user_id)
        
        # Notify new assignee
        new_assignee = data.get('assigned_user_id')
        if new_assignee and new_assignee != old_assignee:
            assignee = get_one("SELECT username FROM users WHERE id = ?", (new_assignee,))
            notify_task_assigned(task['project_id'], project['project_code'], 
                               task['task_name'], assignee['username'] if assignee else 'Unknown')
        
        flash("Task updated successfully.", "success")
        return redirect(url_for('project.project_tasks', project_id=task['project_id']))
    
    context['phases'] = get_all("SELECT id, phase_name FROM project_phases WHERE project_id = ? ORDER BY phase_order", (task['project_id'],))
    context['wbs_nodes'] = get_all("SELECT id, wbs_code, wbs_name FROM project_wbs WHERE project_id = ? ORDER BY sort_order", (task['project_id'],))
    context['users'] = get_all("SELECT id, username FROM users WHERE is_active = 1 ORDER BY username")
    context['priorities'] = ['Low', 'Medium', 'High', 'Critical']
    context['statuses'] = ['Draft', 'Pending', 'In Progress', 'Review', 'Completed', 'Cancelled']
    
    return render_template('project/task_edit.html', **context)


@project_bp.route('/task/<int:task_id>/delete', methods=['POST'])
@require_login
def task_delete(task_id):
    """Delete a task."""
    user_id = get_current_user_id()
    
    task = get_one("SELECT * FROM project_tasks WHERE id = ?", (task_id,))
    if not task:
        return jsonify({'success': False, 'message': 'Task not found'})
    
    if not _can_access_project(user_id, task['project_id']):
        return jsonify({'success': False, 'message': 'Access denied'})
    
    with get_db_context() as db:
        db.execute("DELETE FROM project_tasks WHERE id = ?", (task_id,))
        db.commit()
    
    log_project_audit(None, task['project_id'], task_id, 'TASK_DELETED',
                     old_value=f'Task {task["task_code"]}',
                     actor_user_id=user_id)
    
    return jsonify({'success': True})


# =============================================================================
# ROUTE: RESOURCES
# =============================================================================

@project_bp.route('/<int:project_id>/resources')
@require_login
def project_resources(project_id):
    """View and manage project resources."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    if not _can_access_project(user_id, project_id):
        flash("You don't have access to this project.", "error")
        return redirect(url_for('project.project_list'))
    
    context = _build_context(user_id, language)
    
    project = get_one("SELECT * FROM projects WHERE id = ?", (project_id,))
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for('project.project_list'))
    
    context['project'] = project
    context['page_title'] = get_page_title('/project/', f'Resources: {project["project_code"]}')
    
    # Get resource allocations
    resources = get_all("""
        SELECT pra.*, u.username as resource_name, u.email as resource_email,
               t.task_name, ph.phase_name
        FROM project_resource_allocations pra
        LEFT JOIN users u ON pra.resource_type = 'user' AND pra.resource_id = u.id
        LEFT JOIN project_tasks t ON pra.task_id = t.id
        LEFT JOIN project_phases ph ON pra.task_id IS NULL AND pra.project_id = ph.project_id
        WHERE pra.project_id = ?
        ORDER BY pra.resource_type, pra.allocation_status
    """, (project_id,))
    context['resources'] = resources
    
    # Get team members (users with project access)
    context['team_members'] = get_all("""
        SELECT DISTINCT u.id, u.username, u.email, u.first_name, u.last_name
        FROM users u
        WHERE u.is_active = 1
        AND (u.department_id = ? OR u.id IN (?, ?))
        ORDER BY u.username
    """, (project.get('department_id', 0), project.get('manager_user_id'), project.get('sponsor_user_id')))
    
    return render_template('project/resources.html', **context)


@project_bp.route('/<int:project_id>/resources/add', methods=['POST'])
@require_login
def resource_add(project_id):
    """Add a resource to the project."""
    user_id = get_current_user_id()
    
    if not _can_access_project(user_id, project_id):
        return jsonify({'success': False, 'message': 'Access denied'})
    
    data = request.get_json() or {}
    resource_type = data.get('resource_type', 'user')
    resource_id = data.get('resource_id')
    role_on_project = data.get('role_on_project', '')
    allocation_percentage = data.get('allocation_percentage', 100)
    planned_hours = data.get('planned_hours', 0)
    planned_start_date = data.get('planned_start_date')
    planned_end_date = data.get('planned_end_date')
    
    if not resource_id:
        return jsonify({'success': False, 'message': 'Resource is required'})
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO project_resource_allocations
            (project_id, resource_type, resource_id, role_on_project, allocation_percentage,
             planned_hours, planned_start_date, planned_end_date, allocation_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Allocated')
        """, (project_id, resource_type, resource_id, role_on_project, 
              allocation_percentage, planned_hours, planned_start_date, planned_end_date))
        allocation_id = cursor.lastrowid
        db.commit()
    
    log_project_audit(None, project_id, None, 'RESOURCE_ADDED',
                    new_value=f'Resource {resource_type}:{resource_id} allocated',
                    actor_user_id=user_id)
    
    return jsonify({'success': True, 'allocation_id': allocation_id})


# =============================================================================
# ROUTE: BUDGET
# =============================================================================

@project_bp.route('/<int:project_id>/budget')
@require_login
def project_budget(project_id):
    """View and manage project budget."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    if not _can_access_project(user_id, project_id):
        flash("You don't have access to this project.", "error")
        return redirect(url_for('project.project_list'))
    
    context = _build_context(user_id, language)
    
    project = get_one("SELECT * FROM projects WHERE id = ?", (project_id,))
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for('project.project_list'))
    
    context['project'] = project
    context['page_title'] = get_page_title('/project/', f'Budget: {project["project_code"]}')
    
    # Get resource allocations as budget items
    budget_items = get_all("""
        SELECT pra.*, u.username as resource_name
        FROM project_resource_allocations pra
        LEFT JOIN users u ON pra.resource_type = 'user' AND pra.resource_id = u.id
        WHERE pra.project_id = ?
        ORDER BY pra.resource_type
    """, (project_id,))
    context['budget_items'] = budget_items
    
    # Calculate totals
    with get_db_context() as db:
        totals = db.execute("""
            SELECT 
                SUM(planned_hours) as total_planned_hours,
                SUM(actual_hours) as total_actual_hours,
                AVG(allocation_percentage) as avg_allocation
            FROM project_resource_allocations
            WHERE project_id = ?
        """, (project_id,)).fetchone()
        context['totals'] = dict(totals) if totals else {}
    
    return render_template('project/budget.html', **context)


# =============================================================================
# ROUTE: PROCUREMENT
# =============================================================================

@project_bp.route('/<int:project_id>/procurement')
@require_login
def project_procurement(project_id):
    """View procurement linkage for project."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    if not _can_access_project(user_id, project_id):
        flash("You don't have access to this project.", "error")
        return redirect(url_for('project.project_list'))
    
    context = _build_context(user_id, language)
    
    project = get_one("SELECT * FROM projects WHERE id = ?", (project_id,))
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for('project.project_list'))
    
    context['project'] = project
    context['page_title'] = get_page_title('/project/', f'Procurement: {project["project_code"]}')
    
    # Get vendor if linked
    if project.get('vendor_id'):
        vendor = get_one("SELECT * FROM vendors WHERE id = ?", (project['vendor_id'],))
        context['vendor'] = vendor
    
    # Get related purchase orders if any (from vendor linkage)
    context['purchase_orders'] = []
    
    return render_template('project/procurement.html', **context)


# =============================================================================
# ROUTE: TIMESHEET
# =============================================================================

@project_bp.route('/<int:project_id>/timesheet')
@require_login
def project_timesheet(project_id):
    """View project timesheet/work logs."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    if not _can_access_project(user_id, project_id):
        flash("You don't have access to this project.", "error")
        return redirect(url_for('project.project_list'))
    
    context = _build_context(user_id, language)
    
    project = get_one("SELECT * FROM projects WHERE id = ?", (project_id,))
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for('project.project_list'))
    
    context['project'] = project
    context['page_title'] = get_page_title('/project/', f'Timesheet: {project["project_code"]}')
    
    # Get tasks with actual hours logged
    timesheet_data = get_all("""
        SELECT t.task_code, t.task_name, t.assigned_user_id, u.username as assigned_name,
               t.estimated_hours, t.actual_hours, t.progress, t.status
        FROM project_tasks t
        LEFT JOIN users u ON t.assigned_user_id = u.id
        WHERE t.project_id = ? AND t.is_archived = 0
        ORDER BY t.task_code
    """, (project_id,))
    context['timesheet_data'] = timesheet_data
    
    # Calculate totals
    with get_db_context() as db:
        totals = db.execute("""
            SELECT 
                SUM(estimated_hours) as total_estimated,
                SUM(actual_hours) as total_actual
            FROM project_tasks
            WHERE project_id = ? AND is_archived = 0
        """, (project_id,)).fetchone()
        context['totals'] = dict(totals) if totals else {}
    
    return render_template('project/timesheet.html', **context)


# =============================================================================
# ROUTE: RISKS
# =============================================================================

@project_bp.route('/<int:project_id>/risks')
@require_login
def project_risks(project_id):
    """View and manage project risk register."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    company_id = session.get('company_id', 0)
    
    if not _can_access_project(user_id, project_id):
        flash("You don't have access to this project.", "error")
        return redirect(url_for('project.project_list'))
    
    context = _build_context(user_id, language)
    
    project = get_one("SELECT * FROM projects WHERE id = ?", (project_id,))
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for('project.project_list'))
    
    context['project'] = project
    context['page_title'] = get_page_title('/project/', f'Risk Register: {project["project_code"]}')
    
    # Get risks (using issues table with risk category)
    risks = get_all("""
        SELECT * FROM project_issues
        WHERE project_id = ? AND category = 'Risk'
        ORDER BY severity DESC, created_at DESC
    """, (project_id,))
    context['risks'] = risks
    
    context['severities'] = ['Low', 'Medium', 'High', 'Critical']
    
    return render_template('project/risks.html', **context)


@project_bp.route('/<int:project_id>/risks/create', methods=['POST'])
@require_login
def risk_create(project_id):
    """Create a new risk."""
    user_id = get_current_user_id()
    company_id = session.get('company_id', 0)
    
    if not _can_access_project(user_id, project_id):
        return jsonify({'success': False, 'message': 'Access denied'})
    
    data = request.get_json() or {}
    issue_title = data.get('issue_title', '')
    severity = data.get('severity', 'Medium')
    impact = data.get('impact', '')
    mitigation_plan = data.get('mitigation_plan', '')
    owner_user_id = data.get('owner_user_id')
    due_date = data.get('due_date')
    
    if not issue_title:
        return jsonify({'success': False, 'message': 'Risk title is required'})
    
    issue_number = _generate_issue_number()
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO project_issues (
                project_id, issue_number, issue_title, category, severity, impact,
                mitigation_plan, owner_user_id, due_date, status, reported_by_user_id, reported_date
            ) VALUES (?, ?, ?, 'Risk', ?, ?, ?, ?, ?, 'Open', ?, date('now'))
        """, (project_id, issue_number, issue_title, severity, impact, 
              mitigation_plan, owner_user_id, due_date, user_id))
        risk_id = cursor.lastrowid
        db.commit()
    
    project = get_one("SELECT project_code FROM projects WHERE id = ?", (project_id,))
    log_project_audit(None, project_id, None, 'RISK_CREATED',
                     new_value=f'Risk {issue_number} created',
                     actor_user_id=user_id)
    
    notify_risk_identified(project_id, project['project_code'], issue_title, severity, company_id)
    
    return jsonify({'success': True, 'risk_id': risk_id})


# =============================================================================
# ROUTE: ISSUES
# =============================================================================

@project_bp.route('/<int:project_id>/issues')
@require_login
def project_issues(project_id):
    """View and manage project issue register."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    company_id = session.get('company_id', 0)
    
    if not _can_access_project(user_id, project_id):
        flash("You don't have access to this project.", "error")
        return redirect(url_for('project.project_list'))
    
    context = _build_context(user_id, language)
    
    project = get_one("SELECT * FROM projects WHERE id = ?", (project_id,))
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for('project.project_list'))
    
    context['project'] = project
    context['page_title'] = get_page_title('/project/', f'Issue Register: {project["project_code"]}')
    
    # Get issues
    issues = get_all("""
        SELECT pi.*, u.username as owner_name, u2.username as reporter_name
        FROM project_issues pi
        LEFT JOIN users u ON pi.owner_user_id = u.id
        LEFT JOIN users u2 ON pi.reported_by_user_id = u2.id
        WHERE pi.project_id = ? AND pi.category != 'Risk'
        ORDER BY pi.is_blocker DESC, pi.severity DESC, pi.created_at DESC
    """, (project_id,))
    context['issues'] = issues
    
    context['severities'] = ['Low', 'Medium', 'High', 'Critical']
    context['statuses'] = ['Open', 'In Progress', 'Resolved', 'Closed']
    context['users'] = get_all("SELECT id, username FROM users WHERE is_active = 1 ORDER BY username")
    
    return render_template('project/issues.html', **context)


@project_bp.route('/<int:project_id>/issues/create', methods=['POST'])
@require_login
def issue_create(project_id):
    """Create a new issue."""
    user_id = get_current_user_id()
    company_id = session.get('company_id', 0)
    
    if not _can_access_project(user_id, project_id):
        return jsonify({'success': False, 'message': 'Access denied'})
    
    data = request.get_json() or {}
    issue_title = data.get('issue_title', '')
    category = data.get('category', 'General')
    severity = data.get('severity', 'Medium')
    impact = data.get('impact', '')
    is_blocker = 1 if data.get('is_blocker') else 0
    owner_user_id = data.get('owner_user_id')
    due_date = data.get('due_date')
    root_cause = data.get('root_cause', '')
    
    if not issue_title:
        return jsonify({'success': False, 'message': 'Issue title is required'})
    
    issue_number = _generate_issue_number()
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO project_issues (
                project_id, issue_number, issue_title, category, severity, impact,
                is_blocker, owner_user_id, due_date, root_cause,
                status, reported_by_user_id, reported_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open', ?, date('now'))
        """, (project_id, issue_number, issue_title, category, severity, impact,
              is_blocker, owner_user_id, due_date, root_cause, user_id))
        issue_id = cursor.lastrowid
        db.commit()
    
    project = get_one("SELECT project_code FROM projects WHERE id = ?", (project_id,))
    log_project_audit(None, project_id, None, 'ISSUE_CREATED',
                     new_value=f'Issue {issue_number} created',
                     actor_user_id=user_id)
    
    notify_issue_logged(project_id, project['project_code'], issue_title, severity, company_id)
    
    return jsonify({'success': True, 'issue_id': issue_id})


@project_bp.route('/issue/<int:issue_id>', methods=['PUT', 'DELETE'])
@require_login
def issue_manage(issue_id):
    """Update or delete an issue."""
    user_id = get_current_user_id()
    
    issue = get_one("SELECT * FROM project_issues WHERE id = ?", (issue_id,))
    if not issue:
        return jsonify({'success': False, 'message': 'Issue not found'})
    
    if not _can_access_project(user_id, issue['project_id']):
        return jsonify({'success': False, 'message': 'Access denied'})
    
    if request.method == 'DELETE':
        with get_db_context() as db:
            db.execute("DELETE FROM project_issues WHERE id = ?", (issue_id,))
            db.commit()
        
        log_project_audit(None, issue['project_id'], None, 'ISSUE_DELETED',
                        old_value=f'Issue {issue["issue_number"]}',
                        actor_user_id=user_id)
        
        return jsonify({'success': True})
    
    # PUT
    data = request.get_json() or {}
    
    with get_db_context() as db:
        db.execute("""
            UPDATE project_issues
            SET issue_title = ?, category = ?, severity = ?, impact = ?,
                is_blocker = ?, owner_user_id = ?, due_date = ?,
                status = ?, root_cause = ?, mitigation_plan = ?,
                resolution_date = ?, closure_notes = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (
            data.get('issue_title', issue['issue_title']),
            data.get('category', issue['category']),
            data.get('severity', issue['severity']),
            data.get('impact', issue['impact']),
            1 if data.get('is_blocker') else 0,
            data.get('owner_user_id'),
            data.get('due_date'),
            data.get('status', issue['status']),
            data.get('root_cause', ''),
            data.get('mitigation_plan', ''),
            data.get('resolution_date'),
            data.get('closure_notes', ''),
            issue_id
        ))
        db.commit()
    
    return jsonify({'success': True})


# =============================================================================
# ROUTE: CHANGES (Change Requests)
# =============================================================================

@project_bp.route('/<int:project_id>/changes')
@require_login
def project_changes(project_id):
    """View and manage project change requests."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    if not _can_access_project(user_id, project_id):
        flash("You don't have access to this project.", "error")
        return redirect(url_for('project.project_list'))
    
    context = _build_context(user_id, language)
    
    project = get_one("SELECT * FROM projects WHERE id = ?", (project_id,))
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for('project.project_list'))
    
    context['project'] = project
    context['page_title'] = get_page_title('/project/', f'Change Requests: {project["project_code"]}')
    
    # Get approval records as change requests
    changes = get_all("""
        SELECT ar.*, u.username as requester_name, u2.username as approver_name
        FROM project_approval_records ar
        LEFT JOIN users u ON ar.requester_user_id = u.id
        LEFT JOIN users u2 ON ar.approver_user_id = u2.id
        WHERE ar.project_id = ?
        ORDER BY ar.submitted_at DESC
    """, (project_id,))
    context['changes'] = changes
    
    return render_template('project/changes.html', **context)


@project_bp.route('/<int:project_id>/changes/create', methods=['POST'])
@require_login
def change_create(project_id):
    """Create a change request (approval record)."""
    user_id = get_current_user_id()
    
    if not _can_access_project(user_id, project_id):
        return jsonify({'success': False, 'message': 'Access denied'})
    
    data = request.get_json() or {}
    approval_type = data.get('approval_type', 'Change Request')
    remarks = data.get('remarks', '')
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO project_approval_records
            (project_id, approval_type, requester_user_id, status, remarks, submitted_at)
            VALUES (?, ?, ?, 'Pending', ?, datetime('now'))
        """, (project_id, approval_type, user_id, remarks))
        change_id = cursor.lastrowid
        db.commit()
    
    log_project_audit(None, project_id, None, 'CHANGE_REQUEST_CREATED',
                     new_value=f'Change request created',
                     actor_user_id=user_id)
    
    return jsonify({'success': True, 'change_id': change_id})


# =============================================================================
# ROUTE: DOCUMENTS
# =============================================================================

@project_bp.route('/<int:project_id>/documents')
@require_login
def project_documents(project_id):
    """View and manage project documents."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    if not _can_access_project(user_id, project_id):
        flash("You don't have access to this project.", "error")
        return redirect(url_for('project.project_list'))
    
    context = _build_context(user_id, language)
    
    project = get_one("SELECT * FROM projects WHERE id = ?", (project_id,))
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for('project.project_list'))
    
    context['project'] = project
    context['page_title'] = get_page_title('/project/', f'Documents: {project["project_code"]}')
    
    # Get documents
    documents = get_all("""
        SELECT pd.*, u.username as uploaded_by_name
        FROM project_documents pd
        LEFT JOIN users u ON pd.uploaded_by_user_id = u.id
        WHERE pd.project_id = ?
        ORDER BY pd.created_at DESC
    """, (project_id,))
    context['documents'] = documents
    
    context['document_types'] = ['Project Charter', 'Requirements', 'Design', 'Contract', 'Report', 'Other']
    
    return render_template('project/documents.html', **context)


@project_bp.route('/<int:project_id>/documents/upload', methods=['POST'])
@require_login
def document_upload(project_id):
    """Upload a document."""
    user_id = get_current_user_id()
    
    if not _can_access_project(user_id, project_id):
        return jsonify({'success': False, 'message': 'Access denied'})
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    title = request.form.get('title', file.filename)
    document_type = request.form.get('document_type', 'Other')
    description = request.form.get('description', '')
    
    # In production, save file to storage
    # For now, just record in database
    file_path = f"projects/{project_id}/documents/{file.filename}"
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO project_documents
            (project_id, document_type, title, description, file_name, file_path, 
             uploaded_by_user_id, mime_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (project_id, document_type, title, description, file.filename, 
              file_path, user_id, file.content_type))
        doc_id = cursor.lastrowid
        db.commit()
    
    log_project_audit(None, project_id, None, 'DOCUMENT_UPLOADED',
                    new_value=f'Document {title} uploaded',
                    actor_user_id=user_id)
    
    return jsonify({'success': True, 'document_id': doc_id})


# =============================================================================
# ROUTE: GOVERNANCE
# =============================================================================

@project_bp.route('/<int:project_id>/governance')
@require_login
def project_governance(project_id):
    """View project status and governance information."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    if not _can_access_project(user_id, project_id):
        flash("You don't have access to this project.", "error")
        return redirect(url_for('project.project_list'))
    
    context = _build_context(user_id, language)
    
    project = get_project_with_details(get_db(), project_id)
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for('project.project_list'))
    
    context['project'] = project
    context['page_title'] = get_page_title('/project/', f'Governance: {project["project_code"]}')
    
    # Get status updates history
    status_history = get_all("""
        SELECT su.*, u.username as updater_name
        FROM project_status_updates su
        LEFT JOIN users u ON su.user_id = u.id
        WHERE su.project_id = ?
        ORDER BY su.created_at DESC
    """, (project_id,))
    context['status_history'] = status_history
    
    # Get approval records
    approvals = get_all("""
        SELECT ar.*, u.username as requester_name, u2.username as approver_name
        FROM project_approval_records ar
        LEFT JOIN users u ON ar.requester_user_id = u.id
        LEFT JOIN users u2 ON ar.approver_user_id = u.id
        WHERE ar.project_id = ?
        ORDER BY ar.submitted_at DESC
    """, (project_id,))
    context['approvals'] = approvals
    
    # Calculate health indicators
    with get_db_context() as db:
        health = db.execute("""
            SELECT 
                (SELECT COUNT(*) FROM project_tasks WHERE project_id = ? AND is_archived = 0 AND delay_flag = 1) as delayed_tasks,
                (SELECT COUNT(*) FROM project_milestones WHERE project_id = ? AND is_overdue = 1 AND status != 'Completed') as overdue_milestones,
                (SELECT COUNT(*) FROM project_issues WHERE project_id = ? AND is_blocker = 1 AND status NOT IN ('Resolved', 'Closed')) as active_blockers,
                (SELECT AVG(progress) FROM project_tasks WHERE project_id = ? AND is_archived = 0) as task_progress_avg
        """, (project_id, project_id, project_id, project_id)).fetchone()
        context['health'] = dict(health) if health else {}
    
    return render_template('project/governance.html', **context)


# =============================================================================
# ROUTE: REPORTS
# =============================================================================

@project_bp.route('/reports/')
@require_login
def reports_list():
    """List available project reports."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    context = _build_context(user_id, language)
    context['page_title'] = get_page_title('/project/reports/', 'Project Reports')
    
    return render_template('project/reports/list.html', **context)


@project_bp.route('/reports/summary')
@require_login
def report_summary():
    """Generate project summary report."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    context = _build_context(user_id, language)
    context['page_title'] = get_page_title('/project/reports/', 'Project Summary Report')
    
    # Get all projects summary
    with get_db_context() as db:
        summary = db.execute("""
            SELECT 
                p.*, pt.name as type_name,
                (SELECT COUNT(*) FROM project_tasks WHERE project_id = p.id AND is_archived = 0) as task_count,
                (SELECT COUNT(*) FROM project_milestones WHERE project_id = p.id) as milestone_count,
                (SELECT COUNT(*) FROM project_issues WHERE project_id = p.id) as issue_count
            FROM projects p
            LEFT JOIN project_types pt ON p.project_type_id = pt.id
            WHERE p.is_archived = 0
            ORDER BY p.status, p.priority DESC
        """).fetchall()
        context['projects'] = [dict(row) for row in summary.fetchall()] if summary else []
    
    return render_template('project/reports/summary.html', **context)


@project_bp.route('/reports/export')
@require_login
def report_export():
    """Export projects report to CSV."""
    user_id = get_current_user_id()
    
    # Get projects for export
    projects = get_all("""
        SELECT p.project_code, p.project_name, pt.name as type_name,
               pc.name as category_name, p.status, p.priority,
               p.planned_start_date, p.planned_end_date, p.actual_start_date, p.actual_end_date,
               p.progress, u1.username as manager_name, u2.username as owner_name,
               (SELECT COUNT(*) FROM project_tasks WHERE project_id = p.id AND is_archived = 0) as task_count,
               (SELECT COUNT(*) FROM project_tasks WHERE project_id = p.id AND status = 'Completed' AND is_archived = 0) as completed_tasks
        FROM projects p
        LEFT JOIN project_types pt ON p.project_type_id = pt.id
        LEFT JOIN project_categories pc ON p.category_id = pc.id
        LEFT JOIN users u1 ON p.manager_user_id = u1.id
        LEFT JOIN users u2 ON p.owner_user_id = u2.id
        WHERE p.is_archived = 0
        ORDER BY p.project_code
    """)
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Project Code', 'Project Name', 'Type', 'Category', 'Status', 'Priority',
        'Planned Start', 'Planned End', 'Actual Start', 'Actual End',
        'Progress %', 'Manager', 'Owner', 'Total Tasks', 'Completed Tasks'
    ])
    
    # Data
    for p in projects:
        writer.writerow([
            p['project_code'], p['project_name'], p['type_name'], p['category_name'],
            p['status'], p['priority'], p['planned_start_date'], p['planned_end_date'],
            p['actual_start_date'], p['actual_end_date'], p['progress'],
            p['manager_name'], p['owner_name'], p['task_count'], p['completed_tasks']
        ])
    
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=projects_export_{datetime.now().strftime("%Y%m%d")}.csv'
    
    return response


# =============================================================================
# ROUTE: SETTINGS
# =============================================================================

@project_bp.route('/settings/')
@require_login
def settings_list():
    """List project settings."""
    user_id = get_current_user_id()
    language = session.get('language', 'en')
    
    context = _build_context(user_id, language)
    context['page_title'] = get_page_title('/project/settings/', 'Project Settings')
    
    # Get all settings
    settings = get_all("""
        SELECT * FROM project_settings
        ORDER BY category, setting_key
    """)
    context['settings'] = settings
    
    # Group by category
    grouped = {}
    for s in settings:
        cat = s['category'] or 'General'
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(s)
    context['grouped_settings'] = grouped
    
    return render_template('project/settings/list.html', **context)


@project_bp.route('/settings/update', methods=['POST'])
@require_login
def settings_update():
    """Update project settings."""
    user_id = get_current_user_id()
    
    data = request.get_json() or {}
    setting_key = data.get('setting_key')
    setting_value = data.get('setting_value')
    
    if not setting_key:
        return jsonify({'success': False, 'message': 'Setting key is required'})
    
    with get_db_context() as db:
        db.execute("""
            UPDATE project_settings
            SET setting_value = ?, updated_at = datetime('now')
            WHERE setting_key = ?
        """, (setting_value, setting_key))
        db.commit()
    
    log_project_audit(None, None, None, 'SETTING_UPDATED',
                     new_value=f'{setting_key} = {setting_value}',
                     actor_user_id=user_id)
    
    return jsonify({'success': True})


# =============================================================================
# API ENDPOINTS FOR AJAX OPERATIONS
# =============================================================================

@project_bp.route('/api/stats')
@require_login
def api_stats():
    """Get project statistics for dashboard widgets."""
    company_id = session.get('company_id', 0)
    stats = get_project_stats(company_id)
    return jsonify(stats)


@project_bp.route('/api/my-tasks')
@require_login
def api_my_tasks():
    """Get current user's assigned tasks."""
    user_id = get_current_user_id()
    
    tasks = get_all("""
        SELECT t.*, p.project_name, p.project_code
        FROM project_tasks t
        JOIN projects p ON t.project_id = p.id
        WHERE t.assigned_user_id = ?
        AND t.status NOT IN ('Completed', 'Cancelled')
        ORDER BY t.priority DESC, t.planned_end_date
        LIMIT 20
    """, (user_id,))
    
    return jsonify([dict(t) for t in tasks])


@project_bp.route('/api/user-workload/<int:target_user_id>')
@require_login
def api_user_workload(target_user_id):
    """Get workload for a specific user."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    workload = get_user_workload(get_db(), target_user_id, start_date, end_date)
    return jsonify(workload)


@project_bp.route('/api/project/<int:project_id>/progress')
@require_login
def api_project_progress(project_id):
    """Get calculated project progress."""
    if not _can_access_project(get_current_user_id(), project_id):
        return jsonify({'success': False, 'message': 'Access denied'})
    
    progress = calculate_project_progress(get_db(), project_id)
    return jsonify({'project_id': project_id, 'progress': progress})


@project_bp.route('/api/search')
@require_login
def api_search():
    """Search projects by name or code."""
    query = request.args.get('q', '')
    
    if len(query) < 2:
        return jsonify([])
    
    projects = get_all("""
        SELECT id, project_code, project_name, status, priority
        FROM projects
        WHERE (project_name LIKE ? OR project_code LIKE ?) AND is_archived = 0
        ORDER BY project_name
        LIMIT 10
    """, (f'%{query}%', f'%{query}%'))
    
    return jsonify([dict(p) for p in projects])


# =============================================================================
# EXPORT ENDPOINTS - ALL 20 EXPORT TYPES
# =============================================================================

PROJECT_EXPORT_TYPES = [
    'csv', 'excel_text', 'excel_general', 'json', 'xml', 'txt',
    'pdf', 'docx', 'html', 'printable', 'barcode', 'api',
    'email', 'zip', 'backup', 'sql_dump', 'dashboard',
    'summary', 'detailed', 'audit_log'
]

PROJECT_EXPORT_COLUMNS = {
    'projects': ['project_id', 'name', 'status', 'priority', 'project_type', 'start_date', 'end_date', 'budget'],
    'phases': ['phase_id', 'project_id', 'name', 'start_date', 'end_date', 'status', 'budget'],
    'tasks': ['task_id', 'phase_id', 'name', 'assigned_to', 'status', 'due_date', 'priority'],
    'resources': ['resource_id', 'project_id', 'name', 'role', 'allocation', 'cost'],
    'risks': ['risk_id', 'project_id', 'title', 'severity', 'probability', 'impact', 'status'],
    'issues': ['issue_id', 'project_id', 'title', 'severity', 'status', 'assigned_to', 'created_at'],
    'changes': ['change_id', 'project_id', 'title', 'type', 'status', 'impact', 'created_at'],
    'milestones': ['milestone_id', 'project_id', 'name', 'due_date', 'status', 'deliverable'],
    'documents': ['doc_id', 'project_id', 'name', 'type', 'version', 'uploaded_by', 'uploaded_at']
}


@project_bp.route('/api/export/<export_type>', methods=['GET', 'POST'])
@project_bp.route('/api/export/<data_type>/<export_type>', methods=['GET', 'POST'])
@require_project_permission('reports', 'read')
def api_project_export(export_type, data_type=None):
    """Export project data in all 20 formats."""
    if export_type not in PROJECT_EXPORT_TYPES:
        return jsonify({
            'error': f'Invalid export type. Valid types: {PROJECT_EXPORT_TYPES}'
        }), 400

    company_id = session.get('company_id', 0)

    # Determine data type from URL or default
    if data_type is None:
        data_type = request.args.get('type', 'projects')

    # Get data based on type
    if data_type == 'projects':
        data = get_all("""
            SELECT * FROM projects
            WHERE company_id = ?
            ORDER BY created_at DESC
            LIMIT 5000
        """, (company_id,))
        columns = PROJECT_EXPORT_COLUMNS['projects']
        title = 'Projects'
    elif data_type == 'phases':
        data = get_all("""
            SELECT * FROM project_phases
            WHERE company_id = ?
            ORDER BY start_date DESC
            LIMIT 5000
        """, (company_id,))
        columns = PROJECT_EXPORT_COLUMNS['phases']
        title = 'Project Phases'
    elif data_type == 'tasks':
        data = get_all("""
            SELECT * FROM project_tasks
            WHERE company_id = ?
            ORDER BY due_date DESC
            LIMIT 5000
        """, (company_id,))
        columns = PROJECT_EXPORT_COLUMNS['tasks']
        title = 'Project Tasks'
    elif data_type == 'risks':
        data = get_all("""
            SELECT * FROM project_risks
            WHERE company_id = ?
            ORDER BY created_at DESC
            LIMIT 5000
        """, (company_id,))
        columns = PROJECT_EXPORT_COLUMNS['risks']
        title = 'Risk Register'
    elif data_type == 'issues':
        data = get_all("""
            SELECT * FROM project_issues
            WHERE company_id = ?
            ORDER BY created_at DESC
            LIMIT 5000
        """, (company_id,))
        columns = PROJECT_EXPORT_COLUMNS['issues']
        title = 'Issue Register'
    elif data_type == 'changes':
        data = get_all("""
            SELECT * FROM project_changes
            WHERE company_id = ?
            ORDER BY created_at DESC
            LIMIT 5000
        """, (company_id,))
        columns = PROJECT_EXPORT_COLUMNS['changes']
        title = 'Change Requests'
    elif data_type == 'milestones':
        data = get_all("""
            SELECT * FROM project_milestones
            WHERE company_id = ?
            ORDER BY due_date DESC
            LIMIT 5000
        """, (company_id,))
        columns = PROJECT_EXPORT_COLUMNS['milestones']
        title = 'Milestones'
    else:
        return jsonify({'error': f'Data type {data_type} not supported'}), 400

    filename = f'project_{data_type}_{datetime.now().strftime("%Y%m%d")}'

    return send_export_response(data, export_type, filename, columns, title)


    @project_bp.route('/api/export/list')
    @require_project_permission('reports', 'read')
    def list_project_export_types():
        """List available export types for project module."""
        return jsonify({
            'module': 'project',
            'data_types': list(PROJECT_EXPORT_COLUMNS.keys()),
            'export_types': [{'type': t} for t in PROJECT_EXPORT_TYPES]
        })


# =============================================================================
# REGISTER BLUEPRINT
# =============================================================================

def register_project_routes(app):
    """Register project routes with Flask app."""
    init_project()
    app.register_blueprint(project_bp)

    # =========================================================================
    # ENDPOINT ALIASES - backward compatibility for template references
    # =========================================================================
    # Templates reference endpoints without blueprint prefix (e.g., 'project_list')
    # but blueprint routes register with prefix 'project.' (e.g., 'project.project_list')
    # These aliases ensure url_for('project_X') resolves correctly.
    # =========================================================================

    # Build URL mapping from registered blueprint routes
    endpoint_to_url = {}
    for rule in app.url_map.iter_rules():
        if rule.endpoint.startswith('project.'):
            # Strip the blueprint prefix to get the short name
            short_name = rule.endpoint[len('project.'):]
            endpoint_to_url[short_name] = rule.rule

    # Helper to create endpoint alias with proper URL
    def _add_alias(endpoint_name, view_func):
        # Find the URL from the blueprint registration
        url_path = endpoint_to_url.get(endpoint_name)
        if url_path:
            app.add_url_rule(
                url_path,
                endpoint=endpoint_name,
                view_func=view_func,
                methods=['GET', 'POST']
            )

    # Get the registered view functions from the blueprint
    project_view_functions = {
        'project_list': project_list,
        'project_create': project_create,
        'project_detail': project_detail,
        'project_edit': project_edit,
        'project_charter': project_charter,
        'project_phases': project_phases,
        'project_wbs': project_wbs,
        'project_milestones': project_milestones,
        'project_tasks': project_tasks,
        'project_resources': project_resources,
        'project_budget': project_budget,
        'project_procurement': project_procurement,
        'project_timesheet': project_timesheet,
        'project_risks': project_risks,
        'project_issues': project_issues,
        'project_changes': project_changes,
        'project_documents': project_documents,
        'project_governance': project_governance,
        'project_reports': reports_list,
        'project_settings': settings_list,
    }

    for endpoint_name, view_func in project_view_functions.items():
        _add_alias(endpoint_name, view_func)
