"""
Task Center Routes
==================
All task center submenu routes including dashboard, my-tasks, team-tasks,
overdue, completed, queue, priority board, SLA view, escalations, subtasks,
logs, time logs, reports, settings, and audit.
"""

from flask import Blueprint, request, session, render_template, jsonify, redirect, url_for, flash
from functools import wraps
from datetime import datetime, timedelta
from database import get_db_context, get_db

task_bp = Blueprint('task_center', __name__, url_prefix='/tasks', template_folder='templates/task_center')


def require_login(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login to access this page.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def user_can_manage_all_tasks():
    return bool(session.get('can_manage_users'))


def get_task_scope_clause(alias='t'):
    """Build WHERE clause based on user permissions."""
    if user_can_manage_all_tasks():
        return '', []

    current_user_id = session.get('user_id')
    current_company_id = session.get('company_id')
    scope_parts = []
    scope_params = []

    if current_user_id:
        scope_parts.append(
            f"{alias}.created_by_user_id = ? OR {alias}.assigned_to_user_id = ? OR {alias}.report_to_user_id = ?"
        )
        scope_params.extend([current_user_id, current_user_id, current_user_id])

    if current_company_id:
        scope_parts.append(f"{alias}.company_id = ?")
        scope_params.append(current_company_id)

    if not scope_parts:
        return " AND 1 = 0", []

    return f" AND ({' OR '.join(scope_parts)})", scope_params


# ─── Task Dashboard ──────────────────────────────────────────────────────────

@task_bp.route('/dashboard')
@require_login
def task_dashboard():
    """Main Task Dashboard with overview statistics and quick actions."""
    db = get_db()

    # Ensure session has required fields
    if 'profile_pic' not in session:
        session['profile_pic'] = 'default.png'

    now = datetime.now()

    # Get task stats
    total_tasks = db.execute('SELECT COUNT(*) FROM task_items WHERE is_archived = 0').fetchone()[0]
    my_tasks_count = db.execute(
        'SELECT COUNT(*) FROM task_items WHERE assigned_to_user_id = ? AND is_archived = 0 AND status NOT IN (?, ?)',
        (session['user_id'], 'Completed', 'Canceled')
    ).fetchone()[0]
    team_tasks_count = db.execute(
        'SELECT COUNT(*) FROM task_items WHERE is_archived = 0 AND status NOT IN (?, ?)',
        ('Completed', 'Canceled')
    ).fetchone()[0]
    overdue_tasks_count = db.execute(
        'SELECT COUNT(*) FROM task_items WHERE is_archived = 0 AND status NOT IN (?, ?) AND due_at < ?',
        ('Completed', 'Canceled', now.isoformat())
    ).fetchone()[0]
    completed_tasks_count = db.execute(
        'SELECT COUNT(*) FROM task_items WHERE status = ?', ('Completed',)
    ).fetchone()[0]
    in_progress_count = db.execute(
        'SELECT COUNT(*) FROM task_items WHERE status = ? AND is_archived = 0', ('In Progress',)
    ).fetchone()[0]
    review_count = db.execute(
        'SELECT COUNT(*) FROM task_items WHERE status = ? AND is_archived = 0', ('Review',)
    ).fetchone()[0]

    # SLA metrics - tasks due within 24 hours
    sla_warning = db.execute(
        '''SELECT COUNT(*) FROM task_items
           WHERE is_archived = 0 AND status NOT IN (?, ?)
           AND due_at IS NOT NULL AND due_at > ?
           AND due_at <= ?''',
        ('Completed', 'Canceled', now.isoformat(), (now + timedelta(hours=24)).isoformat())
    ).fetchone()[0]

    # Escalation count (tasks with priority Critical or High and not completed)
    escalation_count = db.execute(
        '''SELECT COUNT(*) FROM task_items
           WHERE is_archived = 0 AND status NOT IN (?, ?)
           AND priority IN (?, ?)''',
        ('Completed', 'Canceled', 'Critical', 'High')
    ).fetchone()[0]

    # Priority breakdown
    priority_breakdown = db.execute('''
        SELECT COALESCE(priority, 'Medium') AS priority, COUNT(*) AS count
        FROM task_items WHERE is_archived = 0
        GROUP BY priority
    ''').fetchall()

    # Status breakdown
    status_breakdown = db.execute('''
        SELECT COALESCE(status, 'Open') AS status, COUNT(*) AS count
        FROM task_items WHERE is_archived = 0
        GROUP BY status
    ''').fetchall()

    # Recent tasks
    recent_tasks = db.execute('''
        SELECT t.*, a.username AS assigned_to_name, d.name AS department_name
        FROM task_items t
        LEFT JOIN users a ON t.assigned_to_user_id = a.id
        LEFT JOIN task_departments d ON t.department_id = d.id
        WHERE t.is_archived = 0
        ORDER BY t.updated_at DESC
        LIMIT 10
    ''').fetchall()

    # Overdue tasks
    overdue_tasks = db.execute('''
        SELECT t.*, a.username AS assigned_to_name
        FROM task_items t
        LEFT JOIN users a ON t.assigned_to_user_id = a.id
        WHERE t.is_archived = 0
        AND t.status NOT IN ('Completed', 'Canceled')
        AND t.due_at IS NOT NULL AND t.due_at < ?
        ORDER BY t.due_at ASC
        LIMIT 10
    ''', (now.isoformat(),)).fetchall()

    # My tasks due today
    my_due_today = db.execute('''
        SELECT t.*, a.username AS assigned_to_name
        FROM task_items t
        LEFT JOIN users a ON t.assigned_to_user_id = a.id
        WHERE t.is_archived = 0
        AND t.assigned_to_user_id = ?
        AND t.status NOT IN ('Completed', 'Canceled')
        AND date(t.due_at) = date(?)
        ORDER BY t.due_at ASC
    ''', (session['user_id'], now.isoformat())).fetchall()

    # Completion trend (last 7 days)
    completion_trend = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0)
        day_end = day.replace(hour=23, minute=59, second=59)
        count = db.execute(
            '''SELECT COUNT(*) FROM task_items
               WHERE status = ? AND updated_at >= ? AND updated_at <= ?''',
            ('Completed', day_start.isoformat(), day_end.isoformat())
        ).fetchone()[0]
        completion_trend.append({
            'date': day.strftime('%a'),
            'count': count
        })

    # Subtask stats
    subtask_total = db.execute('SELECT COUNT(*) FROM task_subtasks').fetchone()[0]
    subtask_completed = db.execute(
        "SELECT COUNT(*) FROM task_subtasks WHERE status = 'Completed'"
    ).fetchone()[0]

    # Get departments for filters
    departments = db.execute("SELECT * FROM task_departments WHERE status = 'Active' ORDER BY name").fetchall()
    task_users = db.execute('SELECT id, username FROM users ORDER BY username').fetchall()

    stats = {
        'total_tasks': total_tasks,
        'my_tasks_count': my_tasks_count,
        'team_tasks_count': team_tasks_count,
        'overdue_tasks_count': overdue_tasks_count,
        'completed_tasks_count': completed_tasks_count,
        'in_progress_count': in_progress_count,
        'review_count': review_count,
        'sla_warning': sla_warning,
        'escalation_count': escalation_count,
        'subtask_total': subtask_total,
        'subtask_completed': subtask_completed,
        'subtask_pending': subtask_total - subtask_completed
    }

    return render_template(
        'task_center/dashboard.html',
        title='Task Dashboard',
        stats=stats,
        priority_breakdown=[dict(r) for r in priority_breakdown],
        status_breakdown=[dict(r) for r in status_breakdown],
        recent_tasks=[dict(r) for r in recent_tasks],
        overdue_tasks=[dict(r) for r in overdue_tasks],
        my_due_today=[dict(r) for r in my_due_today],
        completion_trend=completion_trend,
        departments=[dict(r) for r in departments],
        task_users=[dict(r) for r in task_users]
    )


# ─── My Tasks ────────────────────────────────────────────────────────────────

@task_bp.route('/my-tasks')
@require_login
def my_tasks():
    """Tasks assigned to the current user."""
    db = get_db()
    now = datetime.now()

    status_filter = request.args.get('status', 'all')
    priority_filter = request.args.get('priority', 'all')
    search = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    query = '''
        SELECT t.*, c.name AS company_name, d.name AS department_name,
               r.username AS report_to_name, a.username AS assigned_to_name,
               creator.username AS created_by_name,
               (SELECT COUNT(*) FROM task_subtasks WHERE parent_task_id = t.id) AS subtask_count
        FROM task_items t
        LEFT JOIN companies c ON t.company_id = c.id
        LEFT JOIN task_departments d ON t.department_id = d.id
        LEFT JOIN users r ON t.report_to_user_id = r.id
        LEFT JOIN users a ON t.assigned_to_user_id = a.id
        LEFT JOIN users creator ON t.created_by_user_id = creator.id
        WHERE t.assigned_to_user_id = ? AND t.is_archived = 0
    '''
    params = [session['user_id']]

    if status_filter != 'all':
        query += ' AND t.status = ?'
        params.append(status_filter)

    if priority_filter != 'all':
        query += ' AND t.priority = ?'
        params.append(priority_filter)

    if search:
        query += ''' AND (
            LOWER(t.task_name) LIKE ? OR LOWER(COALESCE(t.description, '')) LIKE ?
        )'''
        like_term = f'%{search.lower()}%'
        params.extend([like_term, like_term])

    # Overdue flag
    query += ''' AND NOT (t.status IN ('Completed', 'Canceled'))'''

    # Count total
    count_query = query.replace(
        'SELECT t.*, c.name AS company_name, d.name AS department_name,',
        'SELECT COUNT(*) FROM task_items t LEFT JOIN task_departments d ON t.department_id = d.id WHERE 1=1'
    ).split('WHERE t.assigned_to_user_id')[0] + 'WHERE t.assigned_to_user_id = ?'
    # Simpler count
    count_query = 'SELECT COUNT(*) FROM task_items t WHERE t.assigned_to_user_id = ? AND t.is_archived = 0 AND t.status NOT IN (?, ?)'
    count_params = [session['user_id'], 'Completed', 'Canceled']
    if status_filter != 'all':
        count_query += ' AND t.status = ?'
        count_params.append(status_filter)
    if priority_filter != 'all':
        count_query += ' AND t.priority = ?'
        count_params.append(priority_filter)
    if search:
        count_query += ' AND (LOWER(t.task_name) LIKE ? OR LOWER(COALESCE(t.description, \'\')) LIKE ?)'
        count_params.extend([f'%{search.lower()}%', f'%{search.lower()}%'])

    total = db.execute(count_query, count_params).fetchone()[0]
    per_page = 25
    total_pages = max((total + per_page - 1) // per_page, 1)
    if page > total_pages:
        page = total_pages
    offset = (page - 1) * per_page

    query += ' ORDER BY CASE WHEN t.due_at IS NULL THEN 1 ELSE 0 END, t.due_at ASC, t.priority DESC LIMIT ? OFFSET ?'
    params.extend([per_page, offset])

    tasks = db.execute(query, params).fetchall()
    departments = db.execute("SELECT * FROM task_departments WHERE status = 'Active' ORDER BY name").fetchall()

    # Stats for this view
    my_overdue = db.execute(
        'SELECT COUNT(*) FROM task_items WHERE assigned_to_user_id = ? AND is_archived = 0 AND status NOT IN (?, ?) AND due_at < ?',
        (session['user_id'], 'Completed', 'Canceled', now.isoformat())
    ).fetchone()[0]
    my_due_today_count = db.execute(
        'SELECT COUNT(*) FROM task_items WHERE assigned_to_user_id = ? AND is_archived = 0 AND status NOT IN (?, ?) AND date(due_at) = date(?)',
        (session['user_id'], 'Completed', 'Canceled', now.isoformat())
    ).fetchone()[0]
    my_upcoming = db.execute(
        'SELECT COUNT(*) FROM task_items WHERE assigned_to_user_id = ? AND is_archived = 0 AND status NOT IN (?, ?) AND due_at >= ? AND due_at <= ?',
        (session['user_id'], 'Completed', 'Canceled', now.isoformat(), (now + timedelta(days=7)).isoformat())
    ).fetchone()[0]

    return render_template(
        'task_center/my_tasks.html',
        title='My Tasks',
        tasks=[dict(r) for r in tasks],
        departments=[dict(r) for r in departments],
        stats={
            'total': total,
            'overdue': my_overdue,
            'due_today': my_due_today_count,
            'upcoming': my_upcoming
        },
        filters={'status': status_filter, 'priority': priority_filter, 'q': search},
        page=page, total_pages=total_pages
    )


# ─── Team Tasks ──────────────────────────────────────────────────────────────

@task_bp.route('/team-tasks')
@require_login
def team_tasks():
    """Tasks for the user's team/department."""
    db = get_db()
    now = datetime.now()

    department_filter = request.args.get('department', 'all')
    status_filter = request.args.get('status', 'all')
    priority_filter = request.args.get('priority', 'all')
    group_by = request.args.get('group_by', 'assignee')
    page = request.args.get('page', 1, type=int)

    query = '''
        SELECT t.*, c.name AS company_name, d.name AS department_name,
               a.username AS assigned_to_name,
               (SELECT COUNT(*) FROM task_subtasks WHERE parent_task_id = t.id) AS subtask_count
        FROM task_items t
        LEFT JOIN companies c ON t.company_id = c.id
        LEFT JOIN task_departments d ON t.department_id = d.id
        LEFT JOIN users a ON t.assigned_to_user_id = a.id
        WHERE t.is_archived = 0 AND t.status NOT IN ('Completed', 'Canceled')
    '''
    params = []

    if department_filter != 'all':
        query += ' AND t.department_id = ?'
        params.append(department_filter)

    if status_filter != 'all':
        query += ' AND t.status = ?'
        params.append(status_filter)

    if priority_filter != 'all':
        query += ' AND t.priority = ?'
        params.append(priority_filter)

    # Permission scope
    scope_clause, scope_params = get_task_scope_clause('t')
    query += scope_clause
    params.extend(scope_params)

    total = db.execute('SELECT COUNT(*) ' + query.split('SELECT t.*')[1].split('WHERE')[0] + query.split('WHERE', 1)[1], params).fetchone()[0]

    per_page = 50
    total_pages = max((total + per_page - 1) // per_page, 1)
    if page > total_pages:
        page = total_pages
    offset = (page - 1) * per_page

    query += f' ORDER BY a.username, CASE WHEN t.due_at IS NULL THEN 1 ELSE 0 END, t.due_at ASC LIMIT ? OFFSET ?'
    params.extend([per_page, offset])

    tasks = db.execute(query, params).fetchall()
    departments = db.execute("SELECT * FROM task_departments WHERE status = 'Active' ORDER BY name").fetchall()
    task_users = db.execute('SELECT id, username FROM users ORDER BY username').fetchall()

    # Workload summary - tasks per user
    workload = db.execute('''
        SELECT a.username, COUNT(*) AS task_count,
               SUM(CASE WHEN t.priority = 'Critical' THEN 1 ELSE 0 END) AS critical_count,
               SUM(CASE WHEN t.due_at IS NOT NULL AND t.due_at < ? THEN 1 ELSE 0 END) AS overdue_count
        FROM task_items t
        LEFT JOIN users a ON t.assigned_to_user_id = a.id
        WHERE t.is_archived = 0 AND t.status NOT IN ('Completed', 'Canceled')
        GROUP BY a.username
        ORDER BY task_count DESC
    ''', (now.isoformat(),)).fetchall()

    return render_template(
        'task_center/team_tasks.html',
        title='Team Tasks',
        tasks=[dict(r) for r in tasks],
        departments=[dict(r) for r in departments],
        task_users=[dict(r) for r in task_users],
        workload=[dict(r) for r in workload],
        filters={'department': department_filter, 'status': status_filter, 'priority': priority_filter, 'group_by': group_by},
        page=page, total_pages=total_pages
    )


# ─── Overdue Tasks ───────────────────────────────────────────────────────────

@task_bp.route('/overdue')
@require_login
def overdue_tasks():
    """Tasks past their due date."""
    db = get_db()
    now = datetime.now()

    priority_filter = request.args.get('priority', 'all')
    department_filter = request.args.get('department', 'all')
    page = request.args.get('page', 1, type=int)

    query = '''
        SELECT t.*, c.name AS company_name, d.name AS department_name,
               a.username AS assigned_to_name, r.username AS report_to_name
        FROM task_items t
        LEFT JOIN companies c ON t.company_id = c.id
        LEFT JOIN task_departments d ON t.department_id = d.id
        LEFT JOIN users a ON t.assigned_to_user_id = a.id
        LEFT JOIN users r ON t.report_to_user_id = r.id
        WHERE t.is_archived = 0 AND t.status NOT IN ('Completed', 'Canceled')
        AND t.due_at IS NOT NULL AND t.due_at < ?
    '''
    params = [now.isoformat()]

    if priority_filter != 'all':
        query += ' AND t.priority = ?'
        params.append(priority_filter)

    if department_filter != 'all':
        query += ' AND t.department_id = ?'
        params.append(department_filter)

    scope_clause, scope_params = get_task_scope_clause('t')
    query += scope_clause
    params.extend(scope_params)

    total = db.execute('SELECT COUNT(*) FROM task_items t WHERE t.is_archived = 0 AND t.status NOT IN (\'Completed\', \'Canceled\') AND t.due_at IS NOT NULL AND t.due_at < ?', [now.isoformat()]).fetchone()[0]

    per_page = 50
    total_pages = max((total + per_page - 1) // per_page, 1)
    if page > total_pages:
        page = total_pages
    offset = (page - 1) * per_page

    query += ' ORDER BY t.due_at ASC LIMIT ? OFFSET ?'
    params.extend([per_page, offset])

    tasks = db.execute(query, params).fetchall()
    departments = db.execute("SELECT * FROM task_departments WHERE status = 'Active' ORDER BY name").fetchall()

    # Calculate overdue duration for each task
    overdue_list = []
    for task in tasks:
        t = dict(task)
        if t.get('due_at'):
            due = datetime.fromisoformat(t['due_at'].replace('Z', '+00:00')) if isinstance(t['due_at'], str) else t['due_at']
            if due.tzinfo:
                due = due.replace(tzinfo=None)
            delta = now - due
            t['overdue_days'] = delta.days
            t['overdue_hours'] = delta.seconds // 3600
            t['overdue_display'] = f"{delta.days}d {delta.seconds // 3600}h overdue"
        overdue_list.append(t)

    # SLA breach count
    sla_breached = db.execute(
        'SELECT COUNT(*) FROM task_items WHERE is_archived = 0 AND status NOT IN (\'Completed\', \'Canceled\') AND due_at IS NOT NULL AND due_at < ?',
        [now.isoformat()]
    ).fetchone()[0]

    return render_template(
        'task_center/overdue_tasks.html',
        title='Overdue Tasks',
        tasks=overdue_list,
        departments=[dict(r) for r in departments],
        stats={'total': total, 'sla_breached': sla_breached},
        filters={'priority': priority_filter, 'department': department_filter},
        page=page, total_pages=total_pages
    )


# ─── Completed Tasks ─────────────────────────────────────────────────────────

@task_bp.route('/completed')
@require_login
def completed_tasks():
    """Completed/closed tasks."""
    db = get_db()
    now = datetime.now()

    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    user_filter = request.args.get('user', 'all')
    priority_filter = request.args.get('priority', 'all')
    page = request.args.get('page', 1, type=int)

    query = '''
        SELECT t.*, c.name AS company_name, d.name AS department_name,
               a.username AS assigned_to_name, r.username AS report_to_name,
               creator.username AS created_by_name
        FROM task_items t
        LEFT JOIN companies c ON t.company_id = c.id
        LEFT JOIN task_departments d ON t.department_id = d.id
        LEFT JOIN users a ON t.assigned_to_user_id = a.id
        LEFT JOIN users r ON t.report_to_user_id = r.id
        LEFT JOIN users creator ON t.created_by_user_id = creator.id
        WHERE t.status = 'Completed'
    '''
    params = []

    if date_from:
        query += ' AND date(t.updated_at) >= date(?)'
        params.append(date_from)
    if date_to:
        query += ' AND date(t.updated_at) <= date(?)'
        params.append(date_to)
    if user_filter != 'all':
        query += ' AND t.assigned_to_user_id = ?'
        params.append(int(user_filter))
    if priority_filter != 'all':
        query += ' AND t.priority = ?'
        params.append(priority_filter)

    scope_clause, scope_params = get_task_scope_clause('t')
    query += scope_clause
    params.extend(scope_params)

    # Count
    total = db.execute('SELECT COUNT(*) FROM task_items t WHERE t.status = ?', ('Completed',)).fetchone()[0]

    per_page = 50
    total_pages = max((total + per_page - 1) // per_page, 1)
    if page > total_pages:
        page = total_pages
    offset = (page - 1) * per_page

    query += ' ORDER BY t.updated_at DESC LIMIT ? OFFSET ?'
    params.extend([per_page, offset])

    tasks = db.execute(query, params).fetchall()
    task_users = db.execute('SELECT id, username FROM users ORDER BY username').fetchall()

    # Calculate completion time (from created to updated)
    completed_list = []
    for task in tasks:
        t = dict(task)
        if t.get('updated_at') and t.get('created_at'):
            created = datetime.fromisoformat(t['created_at'].replace('Z', '+00:00')) if isinstance(t['created_at'], str) else t['created_at']
            updated = datetime.fromisoformat(t['updated_at'].replace('Z', '+00:00')) if isinstance(t['updated_at'], str) else t['updated_at']
            if created.tzinfo: created = created.replace(tzinfo=None)
            if updated.tzinfo: updated = updated.replace(tzinfo=None)
            delta = updated - created
            t['completion_days'] = delta.days
            t['completion_display'] = f"{delta.days}d {delta.seconds // 3600}h"
        completed_list.append(t)

    return render_template(
        'task_center/completed_tasks.html',
        title='Completed Tasks',
        tasks=completed_list,
        task_users=[dict(r) for r in task_users],
        stats={'total': total},
        filters={'date_from': date_from, 'date_to': date_to, 'user': user_filter, 'priority': priority_filter},
        page=page, total_pages=total_pages
    )


# ─── Task Queue ──────────────────────────────────────────────────────────────

@task_bp.route('/queue')
@require_login
def task_queue():
    """Operational queue/control center for all active tasks."""
    db = get_db()
    now = datetime.now()

    status_filter = request.args.get('status', 'all')
    priority_filter = request.args.get('priority', 'all')
    department_filter = request.args.get('department', 'all')
    page = request.args.get('page', 1, type=int)

    # Unassigned tasks
    unassigned_count = db.execute(
        'SELECT COUNT(*) FROM task_items WHERE is_archived = 0 AND assigned_to_user_id IS NULL AND status NOT IN (?, ?)',
        ('Completed', 'Canceled')
    ).fetchone()[0]

    # Blocked tasks (could be status-based or overdue)
    blocked_count = db.execute(
        'SELECT COUNT(*) FROM task_items WHERE is_archived = 0 AND status = ? AND priority = ?',
        ('Open', 'Critical')
    ).fetchone()[0]

    # Pending review
    review_count = db.execute(
        'SELECT COUNT(*) FROM task_items WHERE is_archived = 0 AND status = ?',
        ('Review',)
    ).fetchone()[0]

    query = '''
        SELECT t.*, c.name AS company_name, d.name AS department_name,
               a.username AS assigned_to_name, r.username AS report_to_name
        FROM task_items t
        LEFT JOIN companies c ON t.company_id = c.id
        LEFT JOIN task_departments d ON t.department_id = d.id
        LEFT JOIN users a ON t.assigned_to_user_id = a.id
        LEFT JOIN users r ON t.report_to_user_id = r.id
        WHERE t.is_archived = 0 AND t.status NOT IN ('Completed', 'Canceled')
    '''
    params = []

    if status_filter != 'all':
        query += ' AND t.status = ?'
        params.append(status_filter)
    if priority_filter != 'all':
        query += ' AND t.priority = ?'
        params.append(priority_filter)
    if department_filter != 'all':
        query += ' AND t.department_id = ?'
        params.append(department_filter)

    total = db.execute('SELECT COUNT(*) FROM task_items t WHERE is_archived = 0 AND status NOT IN (\'Completed\', \'Canceled\')').fetchone()[0]

    per_page = 50
    total_pages = max((total + per_page - 1) // per_page, 1)
    if page > total_pages:
        page = total_pages
    offset = (page - 1) * per_page

    query += ' ORDER BY CASE WHEN t.assigned_to_user_id IS NULL THEN 0 ELSE 1 END, t.priority DESC, t.due_at ASC LIMIT ? OFFSET ?'
    params.extend([per_page, offset])

    tasks = db.execute(query, params).fetchall()
    departments = db.execute("SELECT * FROM task_departments WHERE status = 'Active' ORDER BY name").fetchall()
    task_users = db.execute('SELECT id, username FROM users ORDER BY username').fetchall()

    return render_template(
        'task_center/task_queue.html',
        title='Task Queue',
        tasks=[dict(r) for r in tasks],
        departments=[dict(r) for r in departments],
        task_users=[dict(r) for r in task_users],
        stats={'unassigned': unassigned_count, 'blocked': blocked_count, 'review': review_count, 'total': total},
        filters={'status': status_filter, 'priority': priority_filter, 'department': department_filter},
        page=page, total_pages=total_pages
    )


# ─── Priority Board ──────────────────────────────────────────────────────────

@task_bp.route('/priority-board')
@require_login
def priority_board():
    """Priority-based task management board."""
    db = get_db()
    now = datetime.now()

    priority_groups = {}
    for priority in ['Critical', 'High', 'Medium', 'Low']:
        query = '''
            SELECT t.*, c.name AS company_name, d.name AS department_name,
                   a.username AS assigned_to_name, r.username AS report_to_name
            FROM task_items t
            LEFT JOIN companies c ON t.company_id = c.id
            LEFT JOIN task_departments d ON t.department_id = d.id
            LEFT JOIN users a ON t.assigned_to_user_id = a.id
            LEFT JOIN users r ON t.report_to_user_id = r.id
            WHERE t.is_archived = 0 AND t.status NOT IN ('Completed', 'Canceled') AND t.priority = ?
        '''
        scope_clause, scope_params = get_task_scope_clause('t')
        query += scope_clause
        query += ' ORDER BY CASE WHEN t.due_at IS NULL THEN 1 ELSE 0 END, t.due_at ASC'

        tasks = db.execute(query, [priority] + scope_params).fetchall()
        priority_groups[priority] = [dict(t) for t in tasks]

    # SLA critical - tasks due within 4 hours
    sla_critical = db.execute('''
        SELECT COUNT(*) FROM task_items
        WHERE is_archived = 0 AND status NOT IN ('Completed', 'Canceled')
        AND due_at IS NOT NULL AND due_at > ? AND due_at <= ?
    ''', (now.isoformat(), (now + timedelta(hours=4)).isoformat())).fetchone()[0]

    return render_template(
        'task_center/priority_board.html',
        title='Priority Board',
        priority_groups=priority_groups,
        stats={'sla_critical': sla_critical}
    )


# ─── SLA View ────────────────────────────────────────────────────────────────

@task_bp.route('/sla-view')
@require_login
def sla_view():
    """SLA monitoring and compliance view."""
    db = get_db()
    now = datetime.now()

    # Time buckets for SLA
    sla_buckets = {
        'breached': {'label': 'Breached', 'color': 'danger'},
        'critical': {'label': '< 4 hours', 'color': 'danger'},
        'warning': {'label': '4-24 hours', 'color': 'warning'},
        'healthy': {'label': '> 24 hours', 'color': 'success'},
        'no_sla': {'label': 'No Due Date', 'color': 'muted'}
    }

    tasks = db.execute('''
        SELECT t.*, c.name AS company_name, d.name AS department_name,
               a.username AS assigned_to_name
        FROM task_items t
        LEFT JOIN companies c ON t.company_id = c.id
        LEFT JOIN task_departments d ON t.department_id = d.id
        LEFT JOIN users a ON t.assigned_to_user_id = a.id
        WHERE t.is_archived = 0 AND t.status NOT IN ('Completed', 'Canceled')
    ''').fetchall()

    buckets = {'breached': [], 'critical': [], 'warning': [], 'healthy': [], 'no_sla': []}
    for task in tasks:
        t = dict(task)
        if not t.get('due_at'):
            t['sla_status'] = 'no_sla'
            buckets['no_sla'].append(t)
        else:
            due = datetime.fromisoformat(t['due_at'].replace('Z', '+00:00')) if isinstance(t['due_at'], str) else t['due_at']
            if due.tzinfo:
                due = due.replace(tzinfo=None)
            remaining = (due - now).total_seconds()

            if remaining < 0:
                t['sla_status'] = 'breached'
                t['remaining_seconds'] = remaining
                t['remaining_display'] = f"{-int(remaining // 3600)}h overdue"
                buckets['breached'].append(t)
            elif remaining < 14400:  # < 4 hours
                t['sla_status'] = 'critical'
                t['remaining_seconds'] = remaining
                t['remaining_display'] = f"{int(remaining // 3600)}h {int((remaining % 3600) // 60)}m"
                buckets['critical'].append(t)
            elif remaining < 86400:  # < 24 hours
                t['sla_status'] = 'warning'
                t['remaining_seconds'] = remaining
                t['remaining_display'] = f"{int(remaining // 3600)}h"
                buckets['warning'].append(t)
            else:
                t['sla_status'] = 'healthy'
                t['remaining_seconds'] = remaining
                t['remaining_display'] = f"{int(remaining // 86400)}d"
                buckets['healthy'].append(t)

    # Summary counts
    summary = {
        'total': len(tasks),
        'breached': len(buckets['breached']),
        'critical': len(buckets['critical']),
        'warning': len(buckets['warning']),
        'healthy': len(buckets['healthy']),
        'no_sla': len(buckets['no_sla'])
    }

    return render_template(
        'task_center/sla_view.html',
        title='SLA View',
        buckets=buckets,
        sla_buckets=sla_buckets,
        summary=summary
    )


# ─── Escalations ─────────────────────────────────────────────────────────────

@task_bp.route('/escalations')
@require_login
def escalations():
    """Escalation management view."""
    db = get_db()
    now = datetime.now()

    # Ensure escalation table exists
    db.execute('''
        CREATE TABLE IF NOT EXISTS task_escalations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            escalation_level INTEGER DEFAULT 1,
            escalation_reason TEXT,
            escalated_by_user_id INTEGER,
            escalated_to_user_id INTEGER,
            status TEXT DEFAULT 'Pending',
            resolved_at TEXT,
            resolved_by_user_id INTEGER,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES task_items(id) ON DELETE CASCADE,
            FOREIGN KEY (escalated_by_user_id) REFERENCES users(id),
            FOREIGN KEY (escalated_to_user_id) REFERENCES users(id)
        )
    ''')
    db.commit()

    # Get escalated tasks (Critical/High priority or overdue)
    escalated_tasks = db.execute('''
        SELECT t.*, d.name AS department_name, a.username AS assigned_to_name,
               e.escalation_level, e.status AS escalation_status, e.escalation_reason
        FROM task_items t
        LEFT JOIN task_departments d ON t.department_id = d.id
        LEFT JOIN users a ON t.assigned_to_user_id = a.id
        LEFT JOIN task_escalations e ON t.id = e.task_id AND e.status = 'Pending'
        WHERE t.is_archived = 0 AND t.status NOT IN ('Completed', 'Canceled')
        AND (t.priority IN ('Critical', 'High') OR (t.due_at IS NOT NULL AND t.due_at < ?))
        ORDER BY CASE t.priority WHEN 'Critical' THEN 0 WHEN 'High' THEN 1 ELSE 2 END, t.due_at ASC
    ''', (now.isoformat(),)).fetchall()

    # Resolved escalations
    resolved_escalations = db.execute('''
        SELECT t.task_name, e.*, eb.username AS escalated_by_name, er.username AS resolved_by_name
        FROM task_escalations e
        JOIN task_items t ON e.task_id = t.id
        LEFT JOIN users eb ON e.escalated_by_user_id = eb.id
        LEFT JOIN users er ON e.resolved_by_user_id = er.id
        WHERE e.status = 'Resolved'
        ORDER BY e.resolved_at DESC
        LIMIT 20
    ''').fetchall()

    task_users = db.execute('SELECT id, username FROM users ORDER BY username').fetchall()

    return render_template(
        'task_center/escalations.html',
        title='Escalations',
        tasks=[dict(r) for r in escalated_tasks],
        resolved=[dict(r) for r in resolved_escalations],
        task_users=[dict(r) for r in task_users],
        stats={'active': len(escalated_tasks), 'resolved': len(resolved_escalations)}
    )


# ─── Task Reports Menu ─────────────────────────────────────────────────────

@task_bp.route('/reports')
@require_login
def task_reports_menu():
    """Task reports hub with links to all report types."""
    db = get_db()
    return render_template(
        'task_center/reports_menu.html',
        title='Task Reports'
    )


# ─── Sub Tasks ───────────────────────────────────────────────────────────────

@task_bp.route('/subtasks/open')
@require_login
def subtasks_open():
    """Open/pending subtasks."""
    db = get_db()

    subtasks = db.execute('''
        SELECT s.*, t.task_name AS parent_task_name, a.username AS assigned_to_name
        FROM task_subtasks s
        LEFT JOIN task_items t ON s.parent_task_id = t.id
        LEFT JOIN users a ON s.assigned_to_user_id = a.id
        WHERE s.status IN ('Pending', 'In Progress')
        ORDER BY s.due_at ASC, s.priority DESC
    ''').fetchall()

    return render_template(
        'task_center/subtasks.html',
        title='Open Sub Tasks',
        subtasks=[dict(r) for r in subtasks],
        filter_status='open'
    )


@task_bp.route('/subtasks/in-progress')
@require_login
def subtasks_in_progress():
    """In-progress subtasks."""
    db = get_db()

    subtasks = db.execute('''
        SELECT s.*, t.task_name AS parent_task_name, a.username AS assigned_to_name
        FROM task_subtasks s
        LEFT JOIN task_items t ON s.parent_task_id = t.id
        LEFT JOIN users a ON s.assigned_to_user_id = a.id
        WHERE s.status = 'In Progress'
        ORDER BY s.due_at ASC, s.priority DESC
    ''').fetchall()

    return render_template(
        'task_center/subtasks.html',
        title='In Progress Sub Tasks',
        subtasks=[dict(r) for r in subtasks],
        filter_status='in_progress'
    )


@task_bp.route('/subtasks/completed')
@require_login
def subtasks_completed():
    """Completed subtasks."""
    db = get_db()

    subtasks = db.execute('''
        SELECT s.*, t.task_name AS parent_task_name, a.username AS assigned_to_name
        FROM task_subtasks s
        LEFT JOIN task_items t ON s.parent_task_id = t.id
        LEFT JOIN users a ON s.assigned_to_user_id = a.id
        WHERE s.status = 'Completed'
        ORDER BY s.updated_at DESC
        LIMIT 100
    ''').fetchall()

    return render_template(
        'task_center/subtasks.html',
        title='Completed Sub Tasks',
        subtasks=[dict(r) for r in subtasks],
        filter_status='completed'
    )


@task_bp.route('/subtasks/linked')
@require_login
def subtasks_linked():
    """Linked/parent tasks with subtasks."""
    db = get_db()

    parents = db.execute('''
        SELECT t.*,
               (SELECT COUNT(*) FROM task_subtasks WHERE parent_task_id = t.id) AS subtask_count,
               (SELECT COUNT(*) FROM task_subtasks WHERE parent_task_id = t.id AND status = 'Completed') AS completed_count,
               a.username AS assigned_to_name
        FROM task_items t
        LEFT JOIN users a ON t.assigned_to_user_id = a.id
        WHERE EXISTS (SELECT 1 FROM task_subtasks WHERE parent_task_id = t.id)
        ORDER BY t.updated_at DESC
    ''').fetchall()

    # Get subtasks for each parent
    parent_data = []
    for parent in parents:
        p = dict(parent)
        p['subtasks'] = [dict(r) for r in db.execute('''
            SELECT s.*, a.username AS assigned_to_name
            FROM task_subtasks s
            LEFT JOIN users a ON s.assigned_to_user_id = a.id
            WHERE s.parent_task_id = ?
            ORDER BY s.status, s.priority DESC
        ''', (parent['id'],)).fetchall()]
        parent_data.append(p)

    return render_template(
        'task_center/subtasks_linked.html',
        title='Linked Tasks',
        parents=parent_data
    )


# ─── Task Logs ───────────────────────────────────────────────────────────────

@task_bp.route('/logs')
@require_login
def task_logs():
    """Task activity/change logs."""
    db = get_db()

    action_filter = request.args.get('action', 'all')
    page = request.args.get('page', 1, type=int)

    query = '''
        SELECT h.*, t.task_name, a.username AS actor_name
        FROM task_history h
        LEFT JOIN task_items t ON h.task_id = t.id
        LEFT JOIN users a ON h.actor_user_id = a.id
        WHERE 1=1
    '''
    params = []

    if action_filter != 'all':
        query += ' AND h.action_type = ?'
        params.append(action_filter)

    total = db.execute('SELECT COUNT(*) FROM task_history').fetchone()[0]

    per_page = 50
    total_pages = max((total + per_page - 1) // per_page, 1)
    if page > total_pages:
        page = total_pages
    offset = (page - 1) * per_page

    query += ' ORDER BY h.created_at DESC LIMIT ? OFFSET ?'
    params.extend([per_page, offset])

    logs = db.execute(query, params).fetchall()

    # Action types for filter
    action_types = db.execute('SELECT DISTINCT action_type FROM task_history ORDER BY action_type').fetchall()

    return render_template(
        'task_center/task_logs.html',
        title='Task Logs',
        logs=[dict(r) for r in logs],
        action_types=[r['action_type'] for r in action_types],
        filters={'action': action_filter},
        page=page, total_pages=total_pages
    )


# ─── Time Logs ───────────────────────────────────────────────────────────────

@task_bp.route('/time-logs')
@require_login
def time_logs():
    """Time tracking logs for tasks."""
    db = get_db()
    now = datetime.now()

    # Ensure time_logs table exists
    db.execute('''
        CREATE TABLE IF NOT EXISTS task_time_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            user_id INTEGER NOT NULL,
            log_date TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            duration_minutes INTEGER,
            description TEXT,
            billable INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES task_items(id) ON DELETE SET NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    db.commit()

    task_filter = request.args.get('task', 'all')
    user_filter = request.args.get('user', 'all')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    page = request.args.get('page', 1, type=int)

    query = '''
        SELECT l.*, t.task_name, u.username AS user_name
        FROM task_time_logs l
        LEFT JOIN task_items t ON l.task_id = t.id
        LEFT JOIN users u ON l.user_id = u.id
        WHERE 1=1
    '''
    params = []

    if task_filter != 'all':
        query += ' AND l.task_id = ?'
        params.append(int(task_filter))
    if user_filter != 'all':
        query += ' AND l.user_id = ?'
        params.append(int(user_filter))
    if date_from:
        query += ' AND l.log_date >= ?'
        params.append(date_from)
    if date_to:
        query += ' AND l.log_date <= ?'
        params.append(date_to)

    total = db.execute('SELECT COUNT(*) FROM task_time_logs').fetchone()[0]

    per_page = 50
    total_pages = max((total + per_page - 1) // per_page, 1)
    if page > total_pages:
        page = total_pages
    offset = (page - 1) * per_page

    query += ' ORDER BY l.log_date DESC, l.start_time DESC LIMIT ? OFFSET ?'
    params.extend([per_page, offset])

    logs = db.execute(query, params).fetchall()
    tasks = db.execute('SELECT id, task_name FROM task_items ORDER BY task_name').fetchall()
    task_users = db.execute('SELECT id, username FROM users ORDER BY username').fetchall()

    # Summary stats
    total_minutes = db.execute('SELECT COALESCE(SUM(duration_minutes), 0) FROM task_time_logs').fetchone()[0]
    total_hours = total_minutes / 60

    return render_template(
        'task_center/time_logs.html',
        title='Time Logs',
        logs=[dict(r) for r in logs],
        tasks=[dict(r) for r in tasks],
        task_users=[dict(r) for r in task_users],
        stats={'total_logs': total, 'total_hours': round(total_hours, 1), 'total_minutes': total_minutes},
        filters={'task': task_filter, 'user': user_filter, 'date_from': date_from, 'date_to': date_to},
        page=page, total_pages=total_pages
    )


# ─── Status History ──────────────────────────────────────────────────────────

@task_bp.route('/status-history')
@require_login
def status_history():
    """Task status change history."""
    db = get_db()

    logs = db.execute('''
        SELECT h.*, t.task_name, a.username AS actor_name
        FROM task_history h
        LEFT JOIN task_items t ON h.task_id = t.id
        LEFT JOIN users a ON h.actor_user_id = a.id
        WHERE h.field_name = 'status' OR h.action_type = 'status_change'
        ORDER BY h.created_at DESC
        LIMIT 100
    ''').fetchall()

    return render_template(
        'task_center/status_history.html',
        title='Status History',
        logs=[dict(r) for r in logs]
    )


# ─── Assignment History ───────────────────────────────────────────────────────

@task_bp.route('/assignment-history')
@require_login
def assignment_history():
    """Task assignment change history."""
    db = get_db()

    logs = db.execute('''
        SELECT h.*, t.task_name, a.username AS actor_name,
               old_u.username AS old_assignee, new_u.username AS new_assignee
        FROM task_history h
        LEFT JOIN task_items t ON h.task_id = t.id
        LEFT JOIN users a ON h.actor_user_id = a.id
        LEFT JOIN users old_u ON h.old_value = old_u.id
        LEFT JOIN users new_u ON h.new_value = new_u.id
        WHERE h.field_name = 'assigned_to' OR h.action_type = 'assignment_change'
        ORDER BY h.created_at DESC
        LIMIT 100
    ''').fetchall()

    return render_template(
        'task_center/assignment_history.html',
        title='Assignment History',
        logs=[dict(r) for r in logs]
    )


# ─── Task Reports ────────────────────────────────────────────────────────────

@task_bp.route('/reports/productivity')
@require_login
def task_reports_productivity():
    """Productivity report."""
    db = get_db()
    now = datetime.now()

    # Productivity by user
    productivity = db.execute('''
        SELECT u.username,
               COUNT(*) AS total_tasks,
               SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) AS completed,
               SUM(CASE WHEN t.status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress,
               SUM(CASE WHEN t.priority = 'Critical' THEN 1 ELSE 0 END) AS critical_assigned,
               AVG(COALESCE(t.progress, 0)) AS avg_progress
        FROM task_items t
        LEFT JOIN users u ON t.assigned_to_user_id = u.id
        WHERE t.is_archived = 0
        GROUP BY u.id
        ORDER BY completed DESC
    ''').fetchall()

    # Completion trend
    trend = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        count = db.execute(
            '''SELECT COUNT(*) FROM task_items WHERE status = ? AND date(updated_at) = date(?)''',
            ('Completed', day.isoformat())
        ).fetchone()[0]
        trend.append({'date': day.strftime('%a %m/%d'), 'count': count})

    return render_template(
        'task_center/report_productivity.html',
        title='Productivity Report',
        productivity=[dict(r) for r in productivity],
        trend=trend
    )


@task_bp.route('/reports/completion')
@require_login
def task_reports_completion():
    """Completion rate report."""
    db = get_db()
    now = datetime.now()

    # Completion by priority
    completion_by_priority = db.execute('''
        SELECT COALESCE(priority, 'Medium') AS priority,
               COUNT(*) AS total,
               SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed,
               ROUND(SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS completion_rate
        FROM task_items
        GROUP BY priority
        ORDER BY completion_rate ASC
    ''').fetchall()

    # Completion by department
    completion_by_dept = db.execute('''
        SELECT COALESCE(d.name, 'Unassigned') AS department,
               COUNT(*) AS total,
               SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) AS completed,
               ROUND(SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS completion_rate
        FROM task_items t
        LEFT JOIN task_departments d ON t.department_id = d.id
        GROUP BY d.id
        ORDER BY completion_rate ASC
    ''').fetchall()

    # Overall completion rate
    total = db.execute('SELECT COUNT(*) FROM task_items').fetchone()[0]
    completed = db.execute("SELECT COUNT(*) FROM task_items WHERE status = 'Completed'").fetchone()[0]
    overall_rate = round(completed * 100.0 / total, 1) if total > 0 else 0

    return render_template(
        'task_center/report_completion.html',
        title='Completion Rate Report',
        completion_by_priority=[dict(r) for r in completion_by_priority],
        completion_by_dept=[dict(r) for r in completion_by_dept],
        stats={'overall_rate': overall_rate, 'total': total, 'completed': completed}
    )


@task_bp.route('/reports/by-user')
@require_login
def task_reports_by_user():
    """By-user task report."""
    db = get_db()

    user_stats = db.execute('''
        SELECT u.username, u.id,
               COUNT(t.id) AS total_tasks,
               SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) AS completed,
               SUM(CASE WHEN t.status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress,
               SUM(CASE WHEN t.status = 'Open' THEN 1 ELSE 0 END) AS open,
               SUM(CASE WHEN t.status = 'Review' THEN 1 ELSE 0 END) AS review,
               SUM(CASE WHEN t.priority = 'Critical' THEN 1 ELSE 0 END) AS critical,
               SUM(CASE WHEN t.priority = 'High' THEN 1 ELSE 0 END) AS high,
               AVG(COALESCE(t.progress, 0)) AS avg_progress
        FROM users u
        LEFT JOIN task_items t ON u.id = t.assigned_to_user_id AND t.is_archived = 0
        GROUP BY u.id
        ORDER BY total_tasks DESC
    ''').fetchall()

    return render_template(
        'task_center/report_by_user.html',
        title='Tasks By User',
        user_stats=[dict(r) for r in user_stats]
    )


@task_bp.route('/reports/by-department')
@require_login
def task_reports_by_department():
    """By-department task report."""
    db = get_db()

    dept_stats = db.execute('''
        SELECT d.name AS department, d.id,
               COUNT(t.id) AS total_tasks,
               SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) AS completed,
               SUM(CASE WHEN t.status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress,
               SUM(CASE WHEN t.status = 'Open' THEN 1 ELSE 0 END) AS open,
               SUM(CASE WHEN t.status = 'Review' THEN 1 ELSE 0 END) AS review,
               SUM(CASE WHEN t.priority = 'Critical' THEN 1 ELSE 0 END) AS critical,
               AVG(COALESCE(t.progress, 0)) AS avg_progress
        FROM task_departments d
        LEFT JOIN task_items t ON d.id = t.department_id AND t.is_archived = 0
        GROUP BY d.id
        ORDER BY total_tasks DESC
    ''').fetchall()

    return render_template(
        'task_center/report_by_department.html',
        title='Tasks By Department',
        dept_stats=[dict(r) for r in dept_stats]
    )


# ─── Task Settings ──────────────────────────────────────────────────────────

@task_bp.route('/settings')
@require_login
def task_settings():
    """Task settings main page."""
    if not user_can_manage_all_tasks():
        flash("You don't have permission to access task settings.", "error")
        return redirect(url_for('task_center.task_dashboard'))

    db = get_db()

    departments = db.execute("SELECT * FROM task_departments ORDER BY name").fetchall()
    task_types = db.execute("SELECT * FROM task_departments ORDER BY name").fetchall()  # Reuse departments as types

    # Task statistics for settings overview
    total_tasks = db.execute('SELECT COUNT(*) FROM task_items').fetchone()[0]
    total_subtasks = db.execute('SELECT COUNT(*) FROM task_subtasks').fetchone()[0]
    total_users = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]

    return render_template(
        'task_center/settings.html',
        title='Task Settings',
        departments=[dict(r) for r in departments],
        task_types=[dict(r) for r in task_types],
        stats={'tasks': total_tasks, 'subtasks': total_subtasks, 'users': total_users}
    )


@task_bp.route('/settings/types')
@require_login
def task_settings_types():
    """Task types management."""
    if not user_can_manage_all_tasks():
        flash("You don't have permission to access task settings.", "error")
        return redirect(url_for('task_center.task_dashboard'))

    db = get_db()
    departments = db.execute("SELECT * FROM task_departments ORDER BY name").fetchall()

    return render_template(
        'task_center/settings_types.html',
        title='Task Types',
        departments=[dict(r) for r in departments]
    )


@task_bp.route('/settings/workflow')
@require_login
def task_settings_workflow():
    """Workflow settings for tasks."""
    if not user_can_manage_all_tasks():
        flash("You don't have permission to access task settings.", "error")
        return redirect(url_for('task_center.task_dashboard'))

    db = get_db()
    statuses = ['Open', 'In Progress', 'Review', 'Completed', 'Canceled']
    priorities = ['Low', 'Medium', 'High', 'Critical']

    return render_template(
        'task_center/settings_workflow.html',
        title='Workflow Settings',
        statuses=statuses,
        priorities=priorities
    )


@task_bp.route('/audit')
@require_login
def task_audit():
    """Task audit log - comprehensive change history."""
    if not user_can_manage_all_tasks():
        flash("You don't have permission to access the audit log.", "error")
        return redirect(url_for('task_center.task_dashboard'))

    db = get_db()
    page = request.args.get('page', 1, type=int)

    total = db.execute('SELECT COUNT(*) FROM task_history').fetchone()[0]

    per_page = 50
    total_pages = max((total + per_page - 1) // per_page, 1)
    if page > total_pages:
        page = total_pages
    offset = (page - 1) * per_page

    logs = db.execute('''
        SELECT h.*, t.task_name, a.username AS actor_name
        FROM task_history h
        LEFT JOIN task_items t ON h.task_id = t.id
        LEFT JOIN users a ON h.actor_user_id = a.id
        ORDER BY h.created_at DESC
        LIMIT ? OFFSET ?
    ''', [per_page, offset]).fetchall()

    return render_template(
        'task_center/audit.html',
        title='Task Audit Log',
        logs=[dict(r) for r in logs],
        page=page, total_pages=total_pages
    )


# ─── API Endpoints for AJAX operations ───────────────────────────────────────

@task_bp.route('/api/escalate', methods=['POST'])
@require_login
def api_escalate():
    """Escalate a task."""
    db = get_db()
    data = request.get_json() or {}
    task_id = data.get('task_id')
    reason = data.get('reason', 'Manual escalation')
    escalated_to = data.get('escalated_to_user_id')

    if not task_id:
        return jsonify({'success': False, 'message': 'Task ID is required'}), 400

    db.execute('''
        INSERT INTO task_escalations (task_id, escalation_level, escalation_reason, escalated_by_user_id, escalated_to_user_id, status)
        VALUES (?, 1, ?, ?, ?, 'Pending')
    ''', (task_id, reason, session['user_id'], escalated_to))
    db.commit()

    return jsonify({'success': True, 'message': 'Task escalated successfully'})


@task_bp.route('/api/time-log', methods=['POST'])
@require_login
def api_time_log():
    """Log time against a task."""
    db = get_db()
    data = request.get_json() or {}

    task_id = data.get('task_id')
    log_date = data.get('log_date')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    duration = data.get('duration_minutes')
    description = data.get('description', '')
    billable = data.get('billable', 0)

    if not all([log_date, duration]):
        return jsonify({'success': False, 'message': 'Date and duration are required'}), 400

    db.execute('''
        INSERT INTO task_time_logs (task_id, user_id, log_date, start_time, end_time, duration_minutes, description, billable)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (task_id, session['user_id'], log_date, start_time, end_time, int(duration), description, int(billable)))
    db.commit()

    return jsonify({'success': True, 'message': 'Time logged successfully'})


@task_bp.route('/api/reassign', methods=['POST'])
@require_login
def api_reassign():
    """Reassign a task to another user."""
    db = get_db()
    data = request.get_json() or {}
    task_id = data.get('task_id')
    new_assignee = data.get('assigned_to_user_id')

    if not task_id:
        return jsonify({'success': False, 'message': 'Task ID is required'}), 400

    if not user_can_manage_all_tasks():
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    task = db.execute('SELECT assigned_to_user_id, task_name FROM task_items WHERE id = ?', (task_id,)).fetchone()
    if not task:
        return jsonify({'success': False, 'message': 'Task not found'}), 404

    old_assignee = task['assigned_to_user_id']
    db.execute('UPDATE task_items SET assigned_to_user_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
               (new_assignee, task_id))
    db.execute('''
        INSERT INTO task_history (task_id, task_name, action_type, field_name, old_value, new_value, actor_user_id)
        VALUES (?, ?, 'assignment_change', 'assigned_to', ?, ?, ?)
    ''', (task_id, task['task_name'], old_assignee, new_assignee, session['user_id']))
    db.commit()

    return jsonify({'success': True, 'message': 'Task reassigned successfully'})


@task_bp.route('/api/resolve-escalation', methods=['POST'])
@require_login
def api_resolve_escalation():
    """Resolve an escalation."""
    db = get_db()
    data = request.get_json() or {}
    escalation_id = data.get('escalation_id')
    notes = data.get('notes', '')

    if not escalation_id:
        return jsonify({'success': False, 'message': 'Escalation ID is required'}), 400

    db.execute('''
        UPDATE task_escalations
        SET status = 'Resolved', resolved_at = CURRENT_TIMESTAMP, resolved_by_user_id = ?, notes = ?
        WHERE id = ?
    ''', (session['user_id'], notes, escalation_id))
    db.commit()

    return jsonify({'success': True, 'message': 'Escalation resolved'})


# ─── Seed Demo Data ─────────────────────────────────────────────────────────────

@task_bp.route('/seed-demo-data', methods=['POST'])
@require_login
def seed_demo_data():
    """Seed sample demo data for the task center."""
    if not user_can_manage_all_tasks():
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    db = get_db()
    now = datetime.now()

    # Create sample tasks
    sample_tasks = [
        {
            'task_name': 'Complete quarterly inventory audit',
            'description': 'Perform comprehensive inventory audit for Q1',
            'priority': 'High',
            'status': 'In Progress',
            'assigned_to': 1,
            'report_to': 2,
            'due_at': (now + timedelta(days=2)).isoformat(),
            'progress': 45
        },
        {
            'task_name': 'Review supplier contracts',
            'description': 'Review and renew expiring supplier agreements',
            'priority': 'Critical',
            'status': 'Open',
            'assigned_to': 2,
            'report_to': None,
            'due_at': (now - timedelta(days=1)).isoformat(),  # Overdue
            'progress': 0
        },
        {
            'task_name': 'Update warehouse layout',
            'description': 'Optimize warehouse floor plan for better flow',
            'priority': 'Medium',
            'status': 'Review',
            'assigned_to': 1,
            'report_to': 3,
            'due_at': (now + timedelta(days=5)).isoformat(),
            'progress': 80
        },
        {
            'task_name': 'Train new warehouse staff',
            'description': 'Conduct onboarding training for 5 new hires',
            'priority': 'High',
            'status': 'In Progress',
            'assigned_to': 3,
            'report_to': 1,
            'due_at': (now + timedelta(days=3)).isoformat(),
            'progress': 30
        },
        {
            'task_name': 'Implement barcode scanning system',
            'description': 'Deploy new barcode scanning solution',
            'priority': 'Critical',
            'status': 'In Progress',
            'assigned_to': 2,
            'report_to': 1,
            'due_at': (now + timedelta(hours=4)).isoformat(),  # SLA critical
            'progress': 65
        },
        {
            'task_name': 'Monthly safety inspection',
            'description': 'Conduct monthly workplace safety review',
            'priority': 'High',
            'status': 'Completed',
            'assigned_to': 1,
            'report_to': 2,
            'due_at': (now - timedelta(days=7)).isoformat(),
            'progress': 100
        },
        {
            'task_name': 'Update SOP documentation',
            'description': 'Revise standard operating procedures',
            'priority': 'Low',
            'status': 'Open',
            'assigned_to': None,  # Unassigned
            'report_to': 1,
            'due_at': (now + timedelta(days=14)).isoformat(),
            'progress': 0
        },
        {
            'task_name': 'Customer delivery follow-up',
            'description': 'Check status of delayed deliveries',
            'priority': 'High',
            'status': 'In Progress',
            'assigned_to': 2,
            'report_to': 3,
            'due_at': (now - timedelta(days=2)).isoformat(),  # Overdue
            'progress': 20
        },
    ]

    created_tasks = []
    for i, task_data in enumerate(sample_tasks):
        # Check if task already exists
        existing = db.execute(
            'SELECT id FROM task_items WHERE task_name = ?',
            (task_data['task_name'],)
        ).fetchone()

        if not existing:
            cursor = db.execute('''
                INSERT INTO task_items
                (task_name, description, priority, status, assigned_to_user_id, report_to_user_id,
                 due_at, progress, created_by_user_id, company_id, department_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1)
            ''', (
                task_data['task_name'],
                task_data['description'],
                task_data['priority'],
                task_data['status'],
                task_data['assigned_to'],
                task_data['report_to'],
                task_data['due_at'],
                task_data['progress'],
                session.get('user_id', 1)
            ))
            created_tasks.append(cursor.lastrowid)

            # Add history entry
            db.execute('''
                INSERT INTO task_history (task_id, task_name, action_type, field_name, new_value, actor_user_id)
                VALUES (?, ?, 'created', 'task', ?, ?)
            ''', (cursor.lastrowid, task_data['task_name'], task_data['status'], session.get('user_id', 1)))

    # Create sample subtasks for first task
    if created_tasks:
        parent_id = created_tasks[0]
        subtask_data = [
            ('Review current inventory counts', 'In Progress', 'High'),
            ('Verify stock levels', 'Pending', 'Medium'),
            ('Update inventory system', 'Pending', 'Medium'),
        ]
        for title, status, priority in subtask_data:
            existing = db.execute(
                'SELECT id FROM task_subtasks WHERE subtask_title = ? AND parent_task_id = ?',
                (title, parent_id)
            ).fetchone()
            if not existing:
                db.execute('''
                    INSERT INTO task_subtasks
                    (parent_task_id, subtask_title, priority, status, assigned_to_user_id, due_at)
                    VALUES (?, ?, ?, ?, 1, ?)
                ''', (parent_id, title, priority, status, (now + timedelta(days=3)).isoformat()))

    # Create sample time logs
    time_log_entries = [
        (created_tasks[0] if created_tasks else 1, 1, (now - timedelta(days=2)).strftime('%Y-%m-%d'), '08:00', '10:00', 120, 'Inventory counting', 1),
        (created_tasks[0] if created_tasks else 1, 1, (now - timedelta(days=1)).strftime('%Y-%m-%d'), '09:00', '12:00', 180, 'System update prep', 1),
        (created_tasks[3] if len(created_tasks) > 3 else 2, 2, (now - timedelta(days=1)).strftime('%Y-%m-%d'), '14:00', '16:00', 120, 'Training session', 0),
    ]

    for task_id, user_id, log_date, start, end, duration, desc, billable in time_log_entries:
        existing = db.execute(
            'SELECT id FROM task_time_logs WHERE task_id = ? AND log_date = ? AND duration_minutes = ?',
            (task_id, log_date, duration)
        ).fetchone()
        if not existing:
            db.execute('''
                INSERT INTO task_time_logs
                (task_id, user_id, log_date, start_time, end_time, duration_minutes, description, billable)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (task_id, user_id, log_date, start, end, duration, desc, billable))

    # Create sample task history entries
    if created_tasks:
        history_entries = [
            (created_tasks[0], 'Status changed to In Progress', 'status', 'Open', 'In Progress'),
            (created_tasks[0], 'Progress updated to 45%', 'progress', '', '45%'),
            (created_tasks[3], 'Assigned to new team member', 'assigned_to', '', '3'),
        ]
        for task_id, note, field, old_val, new_val in history_entries:
            db.execute('''
                INSERT INTO task_history (task_id, task_name, action_type, field_name, old_value, new_value, note, actor_user_id)
                VALUES (?, ?, 'update', ?, ?, ?, ?, 1)
            ''', (task_id, f'Task #{task_id}', field, old_val, new_val, note))

    db.commit()

    return jsonify({
        'success': True,
        'message': f'Seeded demo data successfully. Created {len(created_tasks)} tasks.',
        'tasks_created': len(created_tasks)
    })


def register_task_center_routes(app):
    """Register Task Center blueprint."""
    app.register_blueprint(task_bp)

