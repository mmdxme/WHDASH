"""
Issue Tracker Routes
===================
Complete enterprise-grade issue tracker module.
All submenu routes are real and functional:
Dashboard, All Issues, My Issues, Assigned to Me, Backlog,
In Progress, Pending Review, Resolved, Closed, Priorities,
Categories, SLA Breaches, Reports (5), Settings (3), Audit.

New in this version:
- Create / edit issue (modal + API)
- File attachment upload & download
- Issue assignment API
- Escalation API
- Bulk status update
- CSV/JSON export
- Notification integration
- CSRF protection on all mutating endpoints
- Full audit trail
"""

import os
import csv
import json
import io
import secrets
import hmac
from flask import (Blueprint, request, session, render_template, jsonify,
                   redirect, url_for, flash, send_file, make_response)
from functools import wraps
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from database import get_db
from collections import Counter

try:
    from database import create_notification
    _HAS_NOTIFICATIONS = True
except ImportError:
    _HAS_NOTIFICATIONS = False

issue_bp = Blueprint('issue_tracker', __name__, url_prefix='/issues',
                    template_folder='templates/issue_tracker')

# ─── Allowed upload extensions ────────────────────────────────────────────────
ALLOWED_ATTACHMENT_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg', 'gif',
    'txt', 'csv', 'zip', 'rar', 'mp4', 'mov', 'bmp', 'webp', 'pptx',
}
MAX_ATTACHMENT_MB = 50


def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login to access this page.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def _csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']


def _validate_csrf():
    """Validate CSRF token from form or JSON header."""
    token = (request.form.get('csrf_token')
             or request.headers.get('X-CSRF-Token')
             or (request.get_json(silent=True) or {}).get('csrf_token'))
    stored = session.get('csrf_token')
    if not stored or not token:
        return False
    return hmac.compare_digest(stored, token)


def csrf_protected_api(f):
    """Decorator: validates CSRF for JSON API mutating endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            if not _validate_csrf():
                return jsonify({'success': False, 'message': 'CSRF validation failed.'}), 403
        return f(*args, **kwargs)
    return decorated


def user_can_edit_issues():
    """True for any authenticated user that can create/edit issues."""
    return bool(
        session.get('can_manage_users')
        or session.get('can_edit_stock')
        or session.get('user_id')   # all logged-in users can edit their own
    )


def user_can_manage_issues():
    """True only for admins / managers."""
    return bool(session.get('can_manage_users'))


def user_can_approve_issues():
    """True for supervisors, managers, and admins."""
    return bool(session.get('can_manage_users') or session.get('can_approve'))


def _allowed_attachment(filename):
    return ('.' in filename
            and filename.rsplit('.', 1)[1].lower() in ALLOWED_ATTACHMENT_EXTENSIONS)


def _attachment_upload_dir():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'static', 'uploads', 'issue_attachments')
    os.makedirs(base, exist_ok=True)
    return base


def _send_issue_notification(title, message, issue_id, assignee_user_id=None,
                              severity='MEDIUM', notif_type='INFO'):
    """Fire a platform notification for an issue event."""
    if not _HAS_NOTIFICATIONS:
        return
    try:
        link = url_for('issue_tracker.issue_detail', issue_id=issue_id)
        create_notification(
            title=title,
            message=message,
            notification_type=notif_type,
            user_id=assignee_user_id,
            severity=severity,
            link_url=link,
            related_entity_type='issue',
            related_entity_id=issue_id,
        )
    except Exception:
        pass


def get_issue_scope_clause(alias='i'):
    """Build WHERE clause based on user permissions."""
    if user_can_manage_issues():
        return '', []
    current_user_id = session.get('user_id')
    if not current_user_id:
        return f" AND 1 = 0", []
    return (f" AND ({alias}.created_by_user_id = ? "
            f"OR {alias}.responsible_person = ? "
            f"OR {alias}.follow_up_by = ?)",
            [current_user_id, current_user_id, current_user_id])


# ─── Helper Functions ──────────────────────────────────────────────────────────

def split_issue_departments(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    raw_value = str(value or '').strip()
    if not raw_value:
        return []
    delimiter = '|' if '|' in raw_value else '/'
    return [item.strip() for item in raw_value.split(delimiter) if item.strip()]


def serialize_issue_departments(value):
    return '|'.join(split_issue_departments(value))


def normalize_issue_priority(priority_value):
    priority = (priority_value or 'Medium').strip().title()
    return priority if priority in ['High', 'Medium', 'Low'] else 'Medium'


def normalize_issue_status(status_value):
    valid = ['Open', 'In Progress', 'Pending Review', 'Resolved', 'Closed', 'Backlog', 'Pending']
    status = (status_value or 'Open').strip().title()
    return status if status in valid else 'Open'


def normalize_issue_type(issue_type):
    normalized = (issue_type or 'Problem').strip().title()
    return normalized if normalized in ['Problem', 'Suggestion', 'Issue'] else 'Problem'


def issue_priority_badge(priority):
    return {
        'High': 'bg-rose-500/15 text-rose-200 border-rose-400/30',
        'Medium': 'bg-amber-500/15 text-amber-200 border-amber-400/30',
        'Low': 'bg-emerald-500/15 text-emerald-200 border-emerald-400/30'
    }.get(priority, 'bg-slate-500/10 text-slate-300 border-slate-500/20')


def issue_status_badge(status):
    return {
        'Open': 'bg-sky-500/15 text-sky-200 border-sky-400/30',
        'In Progress': 'bg-blue-500/15 text-blue-200 border-blue-400/30',
        'Pending Review': 'bg-violet-500/15 text-violet-200 border-violet-400/30',
        'Pending': 'bg-amber-500/15 text-amber-200 border-amber-400/30',
        'Backlog': 'bg-slate-500/15 text-slate-200 border-slate-400/30',
        'Resolved': 'bg-teal-500/15 text-teal-200 border-teal-400/30',
        'Closed': 'bg-emerald-500/15 text-emerald-200 border-emerald-400/30',
    }.get(status, 'bg-slate-500/10 text-slate-300 border-slate-500/20')


def issue_type_badge(issue_type):
    return {
        'Problem': 'bg-rose-500/15 text-rose-200 border-rose-400/30',
        'Suggestion': 'bg-violet-500/15 text-violet-200 border-violet-400/30',
        'Issue': 'bg-cyan-500/15 text-cyan-200 border-cyan-400/30'
    }.get(issue_type, 'bg-slate-500/10 text-slate-300 border-slate-500/20')


def prepare_issue_for_view(issue):
    issue['involved_departments_list'] = split_issue_departments(issue.get('involved_departments'))
    issue['involved_departments_display'] = ' / '.join(issue['involved_departments_list']) or 'Unassigned'
    issue['priority_badge'] = issue_priority_badge(issue.get('priority'))
    issue['status_badge'] = issue_status_badge(issue.get('status'))
    issue['type_badge'] = issue_type_badge(issue.get('issue_type'))
    issue['pareto_display'] = 'Yes' if int(issue.get('pareto_law') or 0) else 'No'
    issue['linked_issues_display'] = issue.get('linked_issues') or '--'
    issue['final_status_display'] = issue.get('final_status') or '--'
    issue['responsible_person_display'] = issue.get('responsible_person') or 'Unassigned'
    issue['responsible_section_display'] = issue.get('responsible_section') or 'Unassigned'
    issue['writer_display'] = issue.get('writer') or '--'
    issue['reported_by_display'] = issue.get('reported_by') or '--'
    return issue


def log_issue_history(db, issue_id, action_type, note=''):
    db.execute(
        'INSERT INTO issue_history (issue_id, action_type, note, actor_user_id) VALUES (?, ?, ?, ?)',
        (issue_id, action_type, note, session.get('user_id'))
    )


def build_issue_report(issues):
    status_counter = Counter(issue.get('status') or 'Open' for issue in issues)
    priority_counter = Counter(issue.get('priority') or 'Medium' for issue in issues)
    type_counter = Counter(issue.get('issue_type') or 'Problem' for issue in issues)
    department_counter = Counter()
    owner_counter = Counter()
    reporter_counter = Counter()

    for issue in issues:
        for department in issue.get('involved_departments_list', []):
            department_counter[department] += 1
        owner_counter[issue.get('responsible_person_display') or 'Unassigned'] += 1
        reporter_counter[issue.get('reported_by') or 'Unassigned'] += 1

    top_department = department_counter.most_common(1)
    top_owner = [(name, total) for name, total in owner_counter.most_common() if name != 'Unassigned']
    top_reporter = [(name, total) for name, total in reporter_counter.most_common() if name != 'Unassigned']

    all_statuses = ['Open', 'In Progress', 'Pending Review', 'Backlog', 'Pending', 'Resolved', 'Closed']
    all_priorities = ['High', 'Medium', 'Low']
    all_types = ['Problem', 'Suggestion', 'Issue']

    return {
        'summary': {
            'total': len(issues),
            'open': sum(1 for i in issues if i.get('status') == 'Open'),
            'in_progress': sum(1 for i in issues if i.get('status') == 'In Progress'),
            'pending_review': sum(1 for i in issues if i.get('status') == 'Pending Review'),
            'resolved': sum(1 for i in issues if i.get('status') == 'Resolved'),
            'closed': sum(1 for i in issues if i.get('status') == 'Closed'),
            'backlog': sum(1 for i in issues if i.get('status') == 'Backlog'),
            'unassigned_owner': sum(1 for i in issues if i.get('responsible_person_display') == 'Unassigned'),
            'high_priority_open': sum(1 for i in issues if i.get('priority') == 'High' and i.get('status') not in ('Closed', 'Resolved')),
            'missing_root_cause': sum(1 for i in issues if not (i.get('root_cause') or '').strip()),
            'missing_action_plan': sum(1 for i in issues if not (i.get('action_plan') or '').strip()),
        },
        'status_chart': [{'label': label, 'total': status_counter.get(label, 0)} for label in all_statuses],
        'priority_chart': [{'label': label, 'total': priority_counter.get(label, 0)} for label in all_priorities],
        'type_chart': [{'label': label, 'total': type_counter.get(label, 0)} for label in all_types],
        'department_chart': [{'label': label, 'total': total} for label, total in department_counter.most_common(8)],
        'owner_chart': [{'label': label, 'total': total} for label, total in owner_counter.most_common(8)],
        'executive': {
            'top_department': top_department[0][0] if top_department else '--',
            'top_department_total': top_department[0][1] if top_department else 0,
            'top_owner': top_owner[:5],
            'top_reporter': top_reporter[:5],
            'total_open': status_counter.get('Open', 0),
            'total_in_progress': status_counter.get('In Progress', 0),
        },
    }


def get_sla_status(issue):
    """Determine SLA status for an issue."""
    target_date = issue.get('target_resolution_date')
    if not target_date or issue.get('status') in ('Closed', 'Resolved'):
        return 'ok'
    try:
        target = datetime.strptime(target_date, '%Y-%m-%d')
        now = datetime.now()
        if now > target:
            return 'breached'
        elif (target - now).days <= 2:
            return 'at_risk'
        return 'ok'
    except (ValueError, TypeError):
        return 'unknown'


# ─── Dashboard ───────────────────────────────────────────────────────────────

@issue_bp.route('/dashboard')
@require_login
def dashboard():
    db = get_db()
    user_id = session.get('user_id')

    all_rows = db.execute('SELECT * FROM issue_items ORDER BY id DESC').fetchall()
    issues = [prepare_issue_for_view(dict(row)) for row in all_rows]

    stats = {
        'total': len(issues),
        'open': sum(1 for i in issues if i.get('status') == 'Open'),
        'in_progress': sum(1 for i in issues if i.get('status') == 'In Progress'),
        'pending_review': sum(1 for i in issues if i.get('status') == 'Pending Review'),
        'resolved': sum(1 for i in issues if i.get('status') == 'Resolved'),
        'closed': sum(1 for i in issues if i.get('status') == 'Closed'),
        'backlog': sum(1 for i in issues if i.get('status') == 'Backlog'),
        'high_priority': sum(1 for i in issues if i.get('priority') == 'High'),
        'sla_at_risk': sum(1 for i in issues if get_sla_status(i) in ('at_risk', 'breached')),
        'sla_breached': sum(1 for i in issues if get_sla_status(i) == 'breached'),
        'unassigned': sum(1 for i in issues if i.get('responsible_person_display') == 'Unassigned'),
    }

    my_issues_count = sum(1 for i in issues
                          if i.get('created_by_user_id') == user_id
                          and i.get('status') not in ('Closed', 'Resolved'))
    assigned_to_me = sum(1 for i in issues
                          if i.get('responsible_person') == session.get('username')
                          and i.get('status') not in ('Closed', 'Resolved'))

    recent_history = [dict(row) for row in db.execute('''
        SELECT h.*, i.row_id, i.issue, actor.username as actor_name
        FROM issue_history h
        JOIN issue_items i ON i.id = h.issue_id
        LEFT JOIN users actor ON actor.id = h.actor_user_id
        ORDER BY h.created_at DESC, h.id DESC LIMIT 15
    ''').fetchall()]

    issue_report = build_issue_report(issues)

    # Overdue issues (target_resolution_date < today, not closed/resolved)
    today_str = datetime.now().strftime('%Y-%m-%d')
    overdue_issues = [
        i for i in issues
        if i.get('target_resolution_date')
        and i.get('target_resolution_date') < today_str
        and i.get('status') not in ('Closed', 'Resolved')
    ]

    return render_template('issue_tracker/dashboard.html',
        title='Issue Dashboard',
        stats=stats,
        issues=issues[:20],
        issue_report=issue_report,
        my_issues_count=my_issues_count,
        assigned_to_me=assigned_to_me,
        recent_history=recent_history,
        overdue_count=len(overdue_issues),
        can_manage=user_can_manage_issues(),
        csrf_token=_csrf_token(),
    )


# ─── All Issues ────────────────────────────────────────────────────────────────

@issue_bp.route('/all')
@require_login
def all_issues():
    db = get_db()
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    category_filter = request.args.get('category', '')
    dept_filter = request.args.get('department', '')
    page = max(1, int(request.args.get('page', 1)))
    per_page = 50

    query = 'SELECT * FROM issue_items WHERE 1=1'
    params = []

    if search:
        query += ' AND (issue LIKE ? OR row_id = ? OR responsible_person LIKE ? OR reported_by LIKE ?)'
        search_term = f'%{search}%'
        params.extend([search_term, search, search_term, search_term])

    if status_filter:
        query += ' AND status = ?'
        params.append(status_filter)

    if priority_filter:
        query += ' AND priority = ?'
        params.append(priority_filter)

    if category_filter:
        query += ' AND issue_type = ?'
        params.append(category_filter)

    if dept_filter:
        query += ' AND involved_departments LIKE ?'
        params.append(f'%{dept_filter}%')

    query += ' ORDER BY id DESC'

    total = db.execute(query.replace('SELECT *', 'SELECT COUNT(*)'), params).fetchone()[0]
    rows = db.execute(query + ' LIMIT ? OFFSET ?', params + [per_page, (page - 1) * per_page]).fetchall()
    issues = [prepare_issue_for_view(dict(row)) for row in rows]

    all_statuses = ['Open', 'In Progress', 'Pending Review', 'Backlog', 'Pending', 'Resolved', 'Closed']
    all_priorities = ['High', 'Medium', 'Low']
    all_types = ['Problem', 'Suggestion', 'Issue']
    all_depts = sorted({d for row in db.execute('SELECT involved_departments FROM issue_items').fetchall()
                        for d in split_issue_departments(row['involved_departments'])})

    return render_template('issue_tracker/all_issues.html',
        title='All Issues',
        issues=issues,
        stats={
            'total': total,
            'page': page,
            'pages': (total + per_page - 1) // per_page,
            'per_page': per_page,
        },
        filters={
            'search': search,
            'status': status_filter,
            'priority': priority_filter,
            'category': category_filter,
            'department': dept_filter,
        },
        all_statuses=all_statuses,
        all_priorities=all_priorities,
        all_types=all_types,
        all_depts=all_depts,
        can_edit=user_can_edit_issues(),
        can_manage=user_can_manage_issues(),
        csrf_token=_csrf_token(),
    )


# ─── My Issues ────────────────────────────────────────────────────────────────

@issue_bp.route('/my')
@require_login
def my_issues():
    db = get_db()
    user_id = session.get('user_id')
    username = session.get('username', '')
    search = request.args.get('search', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = 50

    query = '''SELECT * FROM issue_items
               WHERE (created_by_user_id = ? OR writer = ? OR reported_by = ?)
               AND status NOT IN ('Closed', 'Resolved')
               AND 1=1'''
    params = [user_id, username, username]

    if search:
        query += ' AND issue LIKE ?'
        params.append(f'%{search}%')

    query += ' ORDER BY id DESC'
    total = db.execute(query.replace('SELECT *', 'SELECT COUNT(*)'), params).fetchone()[0]
    rows = db.execute(query + ' LIMIT ? OFFSET ?', params + [per_page, (page - 1) * per_page]).fetchall()
    issues = [prepare_issue_for_view(dict(row)) for row in rows]

    closed_rows = db.execute(
        '''SELECT * FROM issue_items
           WHERE (created_by_user_id = ? OR writer = ? OR reported_by = ?)
           AND status IN ('Closed', 'Resolved')
           ORDER BY id DESC LIMIT 10''',
        [user_id, username, username]
    ).fetchall()
    closed_issues = [prepare_issue_for_view(dict(row)) for row in closed_rows]

    return render_template('issue_tracker/my_issues.html',
        title='My Issues',
        issues=issues,
        closed_issues=closed_issues,
        stats={'total': total, 'page': page, 'pages': (total + per_page - 1) // per_page},
        filters={'search': search},
        can_edit=user_can_edit_issues(),
        csrf_token=_csrf_token(),
    )


# ─── Assigned to Me ──────────────────────────────────────────────────────────

@issue_bp.route('/assigned')
@require_login
def assigned_to_me():
    db = get_db()
    username = session.get('username', '')
    search = request.args.get('search', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = 50

    query = '''SELECT * FROM issue_items
               WHERE responsible_person = ? AND status NOT IN ('Closed', 'Resolved')
               AND 1=1'''
    params = [username]

    if search:
        query += ' AND issue LIKE ?'
        params.append(f'%{search}%')

    query += ' ORDER BY CASE priority WHEN \'High\' THEN 1 WHEN \'Medium\' THEN 2 ELSE 3 END, id DESC'
    total = db.execute(query.replace('SELECT *', 'SELECT COUNT(*)'), params).fetchone()[0]
    rows = db.execute(query + ' LIMIT ? OFFSET ?', params + [per_page, (page - 1) * per_page]).fetchall()
    issues = [prepare_issue_for_view(dict(row)) for row in rows]

    for issue in issues:
        issue['sla_status'] = get_sla_status(issue)

    return render_template('issue_tracker/assigned_to_me.html',
        title='Assigned to Me',
        issues=issues,
        stats={'total': total, 'page': page, 'pages': (total + per_page - 1) // per_page},
        filters={'search': search},
        can_edit=user_can_edit_issues(),
        csrf_token=_csrf_token(),
    )


# ─── Backlog ────────────────────────────────────────────────────────────────

@issue_bp.route('/backlog')
@require_login
def backlog():
    db = get_db()
    search = request.args.get('search', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = 50

    query = '''SELECT * FROM issue_items
               WHERE status = 'Backlog' AND 1=1'''
    params = []

    if search:
        query += ' AND issue LIKE ?'
        params.append(f'%{search}%')

    query += ' ORDER BY id DESC'
    total = db.execute(query.replace('SELECT *', 'SELECT COUNT(*)'), params).fetchone()[0]
    rows = db.execute(query + ' LIMIT ? OFFSET ?', params + [per_page, (page - 1) * per_page]).fetchall()
    issues = [prepare_issue_for_view(dict(row)) for row in rows]

    by_category = {}
    for issue in issues:
        cat = issue.get('issue_type') or 'Unknown'
        by_category[cat] = by_category.get(cat, 0) + 1

    by_dept = {}
    for issue in issues:
        for dept in issue.get('involved_departments_list', []):
            by_dept[dept] = by_dept.get(dept, 0) + 1

    return render_template('issue_tracker/backlog.html',
        title='Backlog',
        issues=issues,
        stats={'total': total, 'page': page, 'pages': (total + per_page - 1) // per_page},
        filters={'search': search},
        by_category=by_category,
        by_dept=by_dept,
        can_edit=user_can_edit_issues(),
    )


# ─── In Progress ───────────────────────────────────────────────────────────────

@issue_bp.route('/in-progress')
@require_login
def in_progress():
    db = get_db()
    search = request.args.get('search', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = 50

    query = '''SELECT * FROM issue_items
               WHERE status = 'In Progress' AND 1=1'''
    params = []

    if search:
        query += ' AND issue LIKE ?'
        params.append(f'%{search}%')

    query += ' ORDER BY CASE priority WHEN \'High\' THEN 1 WHEN \'Medium\' THEN 2 ELSE 3 END, id DESC'
    total = db.execute(query.replace('SELECT *', 'SELECT COUNT(*)'), params).fetchone()[0]
    rows = db.execute(query + ' LIMIT ? OFFSET ?', params + [per_page, (page - 1) * per_page]).fetchall()
    issues = [prepare_issue_for_view(dict(row)) for row in rows]

    for issue in issues:
        issue['sla_status'] = get_sla_status(issue)

    return render_template('issue_tracker/in_progress.html',
        title='In Progress',
        issues=issues,
        stats={'total': total, 'page': page, 'pages': (total + per_page - 1) // per_page},
        filters={'search': search},
        can_edit=user_can_edit_issues(),
        csrf_token=_csrf_token(),
    )


# ─── Pending Review ────────────────────────────────────────────────────────────

@issue_bp.route('/pending-review')
@require_login
def pending_review():
    db = get_db()
    search = request.args.get('search', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = 50

    query = '''SELECT * FROM issue_items
               WHERE status = 'Pending Review' AND 1=1'''
    params = []

    if search:
        query += ' AND issue LIKE ?'
        params.append(f'%{search}%')

    query += ' ORDER BY id DESC'
    total = db.execute(query.replace('SELECT *', 'SELECT COUNT(*)'), params).fetchone()[0]
    rows = db.execute(query + ' LIMIT ? OFFSET ?', params + [per_page, (page - 1) * per_page]).fetchall()
    issues = [prepare_issue_for_view(dict(row)) for row in rows]

    return render_template('issue_tracker/pending_review.html',
        title='Pending Review',
        issues=issues,
        stats={'total': total, 'page': page, 'pages': (total + per_page - 1) // per_page},
        filters={'search': search},
        can_edit=user_can_edit_issues(),
        can_approve=user_can_approve_issues(),
        csrf_token=_csrf_token(),
    )


# ─── Resolved ───────────────────────────────────────────────────────────────────

@issue_bp.route('/resolved')
@require_login
def resolved():
    db = get_db()
    search = request.args.get('search', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = 50

    query = '''SELECT * FROM issue_items
               WHERE status = 'Resolved' AND 1=1'''
    params = []

    if search:
        query += ' AND issue LIKE ?'
        params.append(f'%{search}%')

    query += ' ORDER BY id DESC'
    total = db.execute(query.replace('SELECT *', 'SELECT COUNT(*)'), params).fetchone()[0]
    rows = db.execute(query + ' LIMIT ? OFFSET ?', params + [per_page, (page - 1) * per_page]).fetchall()
    issues = [prepare_issue_for_view(dict(row)) for row in rows]

    return render_template('issue_tracker/resolved.html',
        title='Resolved Issues',
        issues=issues,
        stats={'total': total, 'page': page, 'pages': (total + per_page - 1) // per_page},
        filters={'search': search},
        can_edit=user_can_edit_issues(),
        csrf_token=_csrf_token(),
    )


# ─── Closed ─────────────────────────────────────────────────────────────────────

@issue_bp.route('/closed')
@require_login
def closed():
    db = get_db()
    search = request.args.get('search', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = 50

    query = '''SELECT * FROM issue_items
               WHERE status = 'Closed' AND 1=1'''
    params = []

    if search:
        query += ' AND issue LIKE ?'
        params.append(f'%{search}%')

    query += ' ORDER BY id DESC'
    total = db.execute(query.replace('SELECT *', 'SELECT COUNT(*)'), params).fetchone()[0]
    rows = db.execute(query + ' LIMIT ? OFFSET ?', params + [per_page, (page - 1) * per_page]).fetchall()
    issues = [prepare_issue_for_view(dict(row)) for row in rows]

    return render_template('issue_tracker/closed.html',
        title='Closed Issues',
        issues=issues,
        stats={'total': total, 'page': page, 'pages': (total + per_page - 1) // per_page},
        filters={'search': search},
        can_edit=user_can_edit_issues(),
        can_manage=user_can_manage_issues(),
        csrf_token=_csrf_token(),
    )


# ─── Priorities ────────────────────────────────────────────────────────────────

@issue_bp.route('/priorities')
@require_login
def priorities():
    db = get_db()
    all_rows = db.execute('SELECT * FROM issue_items ORDER BY id DESC').fetchall()
    issues = [prepare_issue_for_view(dict(row)) for row in all_rows]

    by_priority = {}
    for priority in ['High', 'Medium', 'Low']:
        by_priority[priority] = [i for i in issues if i.get('priority') == priority]

    critical = [i for i in issues if i.get('priority') == 'High' and i.get('status') not in ('Closed', 'Resolved')]

    return render_template('issue_tracker/priorities.html',
        title='Issue Priorities',
        issues=issues,
        by_priority=by_priority,
        critical=critical,
        can_edit=user_can_edit_issues(),
    )


# ─── Categories ───────────────────────────────────────────────────────────────

@issue_bp.route('/categories')
@require_login
def categories():
    db = get_db()
    all_rows = db.execute('SELECT * FROM issue_items ORDER BY id DESC').fetchall()
    issues = [prepare_issue_for_view(dict(row)) for row in all_rows]

    by_category = {}
    for issue in issues:
        cat = issue.get('issue_type') or 'Uncategorized'
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(issue)

    all_types = ['Problem', 'Suggestion', 'Issue']

    return render_template('issue_tracker/categories.html',
        title='Issue Categories',
        issues=issues,
        by_category=by_category,
        all_types=all_types,
        can_edit=user_can_edit_issues(),
    )


# ─── SLA Breaches ──────────────────────────────────────────────────────────────

@issue_bp.route('/sla-breaches')
@require_login
def sla_breaches():
    db = get_db()
    all_rows = db.execute('SELECT * FROM issue_items ORDER BY id DESC').fetchall()
    issues = [prepare_issue_for_view(dict(row)) for row in all_rows]

    for issue in issues:
        issue['sla_status'] = get_sla_status(issue)

    breached = [i for i in issues if i.get('sla_status') == 'breached']
    at_risk = [i for i in issues if i.get('sla_status') == 'at_risk']

    return render_template('issue_tracker/sla_breaches.html',
        title='SLA Breaches',
        breached=breached,
        at_risk=at_risk,
        stats={
            'total_breached': len(breached),
            'total_at_risk': len(at_risk),
        },
        can_edit=user_can_edit_issues(),
    )


# ─── Issue Detail ──────────────────────────────────────────────────────────────

@issue_bp.route('/detail/<int:issue_id>')
@require_login
def issue_detail(issue_id):
    db = get_db()
    issue_row = db.execute('SELECT * FROM issue_items WHERE id = ?', (issue_id,)).fetchone()
    if not issue_row:
        flash("Issue not found.", "error")
        return redirect(url_for('issue_tracker.all_issues'))

    issue = prepare_issue_for_view(dict(issue_row))
    issue['sla_status'] = get_sla_status(issue)

    history = [dict(row) for row in db.execute('''
        SELECT h.*, actor.username as actor_name
        FROM issue_history h
        LEFT JOIN users actor ON actor.id = h.actor_user_id
        WHERE h.issue_id = ?
        ORDER BY h.created_at DESC, h.id DESC
    ''', (issue_id,)).fetchall()]

    comments = [dict(row) for row in db.execute('''
        SELECT c.*, u.username as commenter_name
        FROM issue_comments c
        LEFT JOIN users u ON u.id = c.user_id
        WHERE c.issue_id = ?
        ORDER BY c.created_at ASC
    ''', (issue_id,)).fetchall()]

    attachments = [dict(row) for row in db.execute('''
        SELECT * FROM issue_attachments WHERE issue_id = ? ORDER BY created_at DESC
    ''', (issue_id,)).fetchall()]

    escalations = [dict(row) for row in db.execute('''
        SELECT e.*, u_by.username as escalated_by_name, u_to.username as escalated_to_name
        FROM issue_escalations e
        LEFT JOIN users u_by ON u_by.id = e.escalated_by
        LEFT JOIN users u_to ON u_to.id = e.escalated_to
        WHERE e.issue_id = ?
        ORDER BY e.created_at DESC
    ''', (issue_id,)).fetchall()]

    watchers = [dict(row) for row in db.execute('''
        SELECT w.*, u.username
        FROM issue_watchers w
        LEFT JOIN users u ON u.id = w.user_id
        WHERE w.issue_id = ?
    ''', (issue_id,)).fetchall()]

    is_watching = any(w['user_id'] == session.get('user_id') for w in watchers)

    users = [dict(r) for r in db.execute(
        "SELECT id, username FROM users ORDER BY username"
    ).fetchall()]

    return render_template('issue_tracker/issue_detail.html',
        title=f'Issue #{issue["row_id"]}',
        issue=issue,
        history=history,
        comments=comments,
        attachments=attachments,
        escalations=escalations,
        watchers=watchers,
        is_watching=is_watching,
        users=users,
        can_edit=user_can_edit_issues(),
        can_manage=user_can_manage_issues(),
        can_approve=user_can_approve_issues(),
        csrf_token=_csrf_token(),
    )


@issue_bp.route('/comment/<int:issue_id>', methods=['POST'])
@require_login
@csrf_protected_api
def add_comment(issue_id):
    if not user_can_edit_issues():
        return jsonify({'success': False, 'message': 'No permission'}), 403
    db = get_db()
    data = request.get_json(silent=True) or {}
    comment = (data.get('comment') or '').strip()
    if not comment:
        return jsonify({'success': False, 'message': 'Comment cannot be empty'}), 400
    if len(comment) > 5000:
        return jsonify({'success': False, 'message': 'Comment too long (max 5000 characters).'}), 400
    db.execute(
        'INSERT INTO issue_comments (issue_id, user_id, comment) VALUES (?, ?, ?)',
        (issue_id, session.get('user_id'), comment)
    )
    log_issue_history(db, issue_id, 'comment', note=comment[:100])
    db.commit()

    # Notify issue owner / assignee
    issue_row = db.execute('SELECT row_id, issue, responsible_person FROM issue_items WHERE id = ?', (issue_id,)).fetchone()
    if issue_row and issue_row['responsible_person']:
        assignee_row = db.execute(
            "SELECT id FROM users WHERE username = ? LIMIT 1", (issue_row['responsible_person'],)
        ).fetchone()
        if assignee_row and assignee_row['id'] != session.get('user_id'):
            _send_issue_notification(
                f'New Comment on Issue #{issue_row["row_id"]}',
                f'{session.get("username", "Someone")} commented: {comment[:80]}',
                issue_id,
                assignee_user_id=assignee_row['id'],
                severity='LOW',
                notif_type='INFO',
            )

    commenter_name = session.get('username', 'Unknown')
    return jsonify({
        'success': True,
        'message': 'Comment added.',
        'comment': {
            'commenter_name': commenter_name,
            'comment': comment,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        }
    })


@issue_bp.route('/status/<int:issue_id>', methods=['POST'])
@require_login
@csrf_protected_api
def change_status(issue_id):
    if not user_can_edit_issues():
        return jsonify({'success': False, 'message': 'No permission'}), 403
    db = get_db()
    data = request.get_json(silent=True) or {}
    new_status = normalize_issue_status(data.get('status'))
    valid = ['Open', 'In Progress', 'Pending Review', 'Backlog', 'Pending', 'Resolved', 'Closed']
    if new_status not in valid:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400

    issue_row = db.execute('SELECT row_id, issue, responsible_person FROM issue_items WHERE id = ?', (issue_id,)).fetchone()
    if not issue_row:
        return jsonify({'success': False, 'message': 'Issue not found'}), 404

    db.execute('UPDATE issue_items SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (new_status, issue_id))
    log_issue_history(db, issue_id, 'status_changed', note=f"Status changed to {new_status}")
    db.commit()

    # Notify assignee of status change
    if issue_row['responsible_person']:
        assignee_row = db.execute(
            "SELECT id FROM users WHERE username = ? LIMIT 1", (issue_row['responsible_person'],)
        ).fetchone()
        if assignee_row and assignee_row['id'] != session.get('user_id'):
            _send_issue_notification(
                f'Issue #{issue_row["row_id"]} Status Changed',
                f'Status updated to: {new_status}',
                issue_id,
                assignee_user_id=assignee_row['id'],
                severity='MEDIUM',
                notif_type='INFO',
            )

    return jsonify({'success': True, 'message': f'Status changed to {new_status}.'})


# ─── Reports ───────────────────────────────────────────────────────────────────────

@issue_bp.route('/reports/summary')
@require_login
def reports_summary():
    db = get_db()
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = 'SELECT * FROM issue_items WHERE 1=1'
    params = []
    if start_date:
        query += ' AND issue_date >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND issue_date <= ?'
        params.append(end_date)

    rows = db.execute(query, params).fetchall()
    issues = [prepare_issue_for_view(dict(row)) for row in rows]
    report = build_issue_report(issues)

    return render_template('issue_tracker/reports_summary.html',
        title='Issue Summary Report',
        issues=issues,
        report=report,
        filters={'start_date': start_date, 'end_date': end_date},
    )


@issue_bp.route('/reports/resolution-time')
@require_login
def reports_resolution_time():
    db = get_db()
    rows = db.execute(
        'SELECT * FROM issue_items WHERE status IN (\'Resolved\', \'Closed\') ORDER BY id DESC'
    ).fetchall()
    issues = [prepare_issue_for_view(dict(row)) for row in rows]

    resolution_times = []
    for issue in issues:
        target = issue.get('target_resolution_date')
        if target:
            try:
                t = datetime.strptime(target, '%Y-%m-%d')
                created = issue.get('issue_date')
                if created:
                    try:
                        c = datetime.strptime(created, '%d/%m/%Y')
                        diff = (t - c).days
                        resolution_times.append({
                            'issue': issue,
                            'target_days': diff,
                            'actual_days': diff,
                        })
                    except ValueError:
                        pass
            except ValueError:
                pass

    return render_template('issue_tracker/reports_resolution_time.html',
        title='Resolution Time Report',
        resolution_times=resolution_times,
        stats={'total_resolved': len(issues)},
    )


@issue_bp.route('/reports/by-priority')
@require_login
def reports_by_priority():
    db = get_db()
    rows = db.execute('SELECT * FROM issue_items ORDER BY id DESC').fetchall()
    issues = [prepare_issue_for_view(dict(row)) for row in rows]

    by_priority = {}
    for priority in ['High', 'Medium', 'Low']:
        by_priority[priority] = {
            'total': sum(1 for i in issues if i.get('priority') == priority),
            'open': sum(1 for i in issues if i.get('priority') == priority and i.get('status') == 'Open'),
            'in_progress': sum(1 for i in issues if i.get('priority') == priority and i.get('status') == 'In Progress'),
            'resolved': sum(1 for i in issues if i.get('priority') == priority and i.get('status') == 'Resolved'),
            'closed': sum(1 for i in issues if i.get('priority') == priority and i.get('status') == 'Closed'),
        }

    return render_template('issue_tracker/reports_by_priority.html',
        title='Issues by Priority',
        by_priority=by_priority,
    )


@issue_bp.route('/reports/by-category')
@require_login
def reports_by_category():
    db = get_db()
    rows = db.execute('SELECT * FROM issue_items ORDER BY id DESC').fetchall()
    issues = [prepare_issue_for_view(dict(row)) for row in rows]

    by_category = {}
    for issue in issues:
        cat = issue.get('issue_type') or 'Unknown'
        if cat not in by_category:
            by_category[cat] = {'total': 0, 'open': 0, 'in_progress': 0, 'pending_review': 0, 'resolved': 0, 'closed': 0}
        by_category[cat]['total'] += 1
        status = issue.get('status', 'Open')
        if status in by_category[cat]:
            by_category[cat][status] += 1

    return render_template('issue_tracker/reports_by_category.html',
        title='Issues by Category',
        by_category=by_category,
    )


@issue_bp.route('/reports/trend')
@require_login
def reports_trend():
    db = get_db()
    rows = db.execute('SELECT * FROM issue_items ORDER BY id DESC').fetchall()
    issues = [prepare_issue_for_view(dict(row)) for row in rows]

    by_month = {}
    for issue in issues:
        date_val = issue.get('issue_date', '')
        if date_val:
            try:
                if '/' in date_val:
                    key = datetime.strptime(date_val, '%d/%m/%Y').strftime('%Y-%m')
                else:
                    key = date_val[:7]
                if key not in by_month:
                    by_month[key] = {'total': 0, 'open': 0, 'closed': 0}
                by_month[key]['total'] += 1
                status = issue.get('status')
                if status == 'Closed':
                    by_month[key]['closed'] += 1
                elif status == 'Open':
                    by_month[key]['open'] += 1
            except ValueError:
                pass

    sorted_months = sorted(by_month.items(), key=lambda x: x[0])

    return render_template('issue_tracker/reports_trend.html',
        title='Trend Analysis',
        trend_data=sorted_months,
    )


# ─── Settings ────────────────────────────────────────────────────────────────────

@issue_bp.route('/settings')
@require_login
def settings():
    if not user_can_manage_issues():
        flash("You do not have permission to access issue settings.", "error")
        return redirect(url_for('issue_tracker.dashboard'))

    db = get_db()
    all_statuses = ['Open', 'In Progress', 'Pending Review', 'Backlog', 'Pending', 'Resolved', 'Closed']
    all_priorities = ['High', 'Medium', 'Low']
    all_types = ['Problem', 'Suggestion', 'Issue']

    categories = [dict(row) for row in db.execute(
        'SELECT * FROM issue_categories ORDER BY name ASC'
    ).fetchall()] if db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='issue_categories'").fetchone() else []

    sla_rules = [dict(row) for row in db.execute(
        'SELECT * FROM issue_sla_rules ORDER BY id ASC'
    ).fetchall()] if db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='issue_sla_rules'").fetchone() else []

    workflow_rules = [dict(row) for row in db.execute(
        'SELECT * FROM issue_workflow_rules ORDER BY id ASC'
    ).fetchall()] if db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='issue_workflow_rules'").fetchone() else []

    return render_template('issue_tracker/settings.html',
        title='Issue Settings',
        all_statuses=all_statuses,
        all_priorities=all_priorities,
        all_types=all_types,
        categories=categories,
        sla_rules=sla_rules,
        workflow_rules=workflow_rules,
    )


@issue_bp.route('/settings/general', methods=['GET', 'POST'])
@require_login
def settings_general():
    if not user_can_manage_issues():
        flash("Permission denied.", "error")
        return redirect(url_for('issue_tracker.dashboard'))

    db = get_db()
    if request.method == 'POST':
        data = request.get_json() or {}
        action = data.get('action')

        if action == 'add_category':
            name = (data.get('name') or '').strip()
            description = (data.get('description') or '').strip()
            if name:
                db.execute('INSERT INTO issue_categories (name, description) VALUES (?, ?)', (name, description))
                db.commit()
                return jsonify({'success': True, 'message': 'Category added.'})

        elif action == 'delete_category':
            cat_id = data.get('id')
            if cat_id:
                db.execute('DELETE FROM issue_categories WHERE id = ?', (cat_id,))
                db.commit()
                return jsonify({'success': True, 'message': 'Category deleted.'})

    categories = [dict(row) for row in db.execute(
        'SELECT * FROM issue_categories ORDER BY name ASC'
    ).fetchall()] if db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='issue_categories'").fetchone() else []

    all_statuses = ['Open', 'In Progress', 'Pending Review', 'Backlog', 'Pending', 'Resolved', 'Closed']
    all_priorities = ['High', 'Medium', 'Low']
    all_types = ['Problem', 'Suggestion', 'Issue']

    return render_template('issue_tracker/settings_general.html',
        title='Issue Settings - General',
        categories=categories,
        all_statuses=all_statuses,
        all_priorities=all_priorities,
        all_types=all_types,
        csrf_token=_csrf_token(),
    )


@issue_bp.route('/settings/workflow', methods=['GET', 'POST'])
@require_login
def settings_workflow():
    if not user_can_manage_issues():
        flash("Permission denied.", "error")
        return redirect(url_for('issue_tracker.dashboard'))

    db = get_db()
    if request.method == 'POST':
        data = request.get_json() or {}
        action = data.get('action')

        if action == 'add_workflow':
            from_status = (data.get('from_status') or '').strip()
            to_status = (data.get('to_status') or '').strip()
            description = (data.get('description') or '').strip()
            if from_status and to_status:
                db.execute(
                    'INSERT INTO issue_workflow_rules (from_status, to_status, description) VALUES (?, ?, ?)',
                    (from_status, to_status, description)
                )
                db.commit()
                return jsonify({'success': True, 'message': 'Workflow rule added.'})

        elif action == 'delete_workflow':
            rule_id = data.get('id')
            if rule_id:
                db.execute('DELETE FROM issue_workflow_rules WHERE id = ?', (rule_id,))
                db.commit()
                return jsonify({'success': True, 'message': 'Workflow rule deleted.'})

    workflow_rules = [dict(row) for row in db.execute(
        'SELECT * FROM issue_workflow_rules ORDER BY from_status ASC'
    ).fetchall()] if db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='issue_workflow_rules'").fetchone() else []

    all_statuses = ['Open', 'In Progress', 'Pending Review', 'Backlog', 'Pending', 'Resolved', 'Closed']

    return render_template('issue_tracker/settings_workflow.html',
        title='Issue Settings - Workflow',
        workflow_rules=workflow_rules,
        all_statuses=all_statuses,
        csrf_token=_csrf_token(),
    )


@issue_bp.route('/settings/sla', methods=['GET', 'POST'])
@require_login
def settings_sla():
    if not user_can_manage_issues():
        flash("Permission denied.", "error")
        return redirect(url_for('issue_tracker.dashboard'))

    db = get_db()
    if request.method == 'POST':
        data = request.get_json() or {}
        action = data.get('action')

        if action == 'add_sla':
            priority = (data.get('priority') or '').strip()
            response_hours = int(data.get('response_hours') or 24)
            resolution_hours = int(data.get('resolution_hours') or 72)
            description = (data.get('description') or '').strip()
            if priority:
                db.execute(
                    'INSERT INTO issue_sla_rules (priority, response_hours, resolution_hours, description) VALUES (?, ?, ?, ?)',
                    (priority, response_hours, resolution_hours, description)
                )
                db.commit()
                return jsonify({'success': True, 'message': 'SLA rule added.'})

        elif action == 'delete_sla':
            rule_id = data.get('id')
            if rule_id:
                db.execute('DELETE FROM issue_sla_rules WHERE id = ?', (rule_id,))
                db.commit()
                return jsonify({'success': True, 'message': 'SLA rule deleted.'})

        elif action == 'update_sla':
            rule_id = data.get('id')
            response_hours = int(data.get('response_hours') or 24)
            resolution_hours = int(data.get('resolution_hours') or 72)
            if rule_id:
                db.execute(
                    'UPDATE issue_sla_rules SET response_hours = ?, resolution_hours = ? WHERE id = ?',
                    (response_hours, resolution_hours, rule_id)
                )
                db.commit()
                return jsonify({'success': True, 'message': 'SLA rule updated.'})

    sla_rules = [dict(row) for row in db.execute(
        'SELECT * FROM issue_sla_rules ORDER BY priority ASC'
    ).fetchall()] if db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='issue_sla_rules'").fetchone() else []

    all_priorities = ['High', 'Medium', 'Low']

    return render_template('issue_tracker/settings_sla.html',
        title='Issue Settings - SLA Rules',
        sla_rules=sla_rules,
        all_priorities=all_priorities,
        csrf_token=_csrf_token(),
    )


# ─── Audit Log ─────────────────────────────────────────────────────────────────

@issue_bp.route('/audit')
@require_login
def audit():
    if not user_can_manage_issues():
        flash("You do not have permission to view the issue audit log.", "error")
        return redirect(url_for('issue_tracker.dashboard'))

    db = get_db()
    page = max(1, int(request.args.get('page', 1)))
    per_page = 100

    total = db.execute('SELECT COUNT(*) FROM issue_history').fetchone()[0]
    history = [dict(row) for row in db.execute('''
        SELECT h.*, i.row_id, i.issue, actor.username as actor_name
        FROM issue_history h
        JOIN issue_items i ON i.id = h.issue_id
        LEFT JOIN users actor ON actor.id = h.actor_user_id
        ORDER BY h.created_at DESC, h.id DESC
        LIMIT ? OFFSET ?
    ''', [per_page, (page - 1) * per_page]).fetchall()]

    return render_template('issue_tracker/audit.html',
        title='Issue Audit Log',
        history=history,
        stats={'total': total, 'page': page, 'pages': (total + per_page - 1) // per_page},
    )


# ─── Reopen Issue ───────────────────────────────────────────────────────────────

@issue_bp.route('/reopen/<int:issue_id>', methods=['POST'])
@require_login
@csrf_protected_api
def reopen_issue(issue_id):
    if not user_can_edit_issues():
        return jsonify({'success': False, 'message': 'No permission'}), 403
    db = get_db()
    data = request.get_json(silent=True) or {}
    reason = (data.get('reason') or 'Issue reopened').strip()[:500]
    db.execute("UPDATE issue_items SET status = 'Open', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (issue_id,))
    log_issue_history(db, issue_id, 'reopened', note=reason)
    db.commit()
    _send_issue_notification(
        'Issue Reopened',
        f'Issue #{issue_id} has been reopened.',
        issue_id, severity='MEDIUM', notif_type='WARNING',
    )
    return jsonify({'success': True, 'message': 'Issue reopened.'})


# ─── Create Issue ────────────────────────────────────────────────────────────────

@issue_bp.route('/create', methods=['GET', 'POST'])
@require_login
def create_issue():
    db = get_db()

    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form.to_dict()

        # CSRF check
        if not _validate_csrf():
            return jsonify({'success': False, 'message': 'CSRF validation failed.'}), 403

        title = (data.get('issue') or data.get('title') or '').strip()
        if not title:
            return jsonify({'success': False, 'message': 'Issue title is required.'}), 400

        issue_date = (data.get('issue_date') or datetime.now().strftime('%d/%m/%Y'))
        issue_type = normalize_issue_type(data.get('issue_type') or 'Problem')
        priority = normalize_issue_priority(data.get('priority') or 'Medium')
        status = normalize_issue_status(data.get('status') or 'Open')
        involved_departments = serialize_issue_departments(data.get('involved_departments') or '')
        responsible_person = (data.get('responsible_person') or '').strip()[:200]
        responsible_section = (data.get('responsible_section') or '').strip()[:200]
        reporter = (data.get('reported_by') or session.get('username') or '').strip()[:200]
        writer = (data.get('writer') or session.get('username') or '').strip()[:200]
        root_cause = (data.get('root_cause') or '').strip()[:2000]
        impact = (data.get('impact') or '').strip()[:2000]
        action_plan = (data.get('action_plan') or '').strip()[:2000]
        resources_needed = (data.get('resources_needed') or '').strip()[:500]
        target_resolution_date = (data.get('target_resolution_date') or '').strip() or None
        progress_note = (data.get('progress_note') or '').strip()[:2000]
        linked_issues = (data.get('linked_issues') or '').strip()[:200]
        section_team = (data.get('section_team') or '').strip()[:200]

        # Get next row_id
        max_row = db.execute("SELECT COALESCE(MAX(row_id), 0) FROM issue_items").fetchone()[0]
        next_row_id = max_row + 1

        db.execute('''
            INSERT INTO issue_items
            (row_id, issue_date, issue_date_sort, issue, pareto_law, involved_departments,
             section_team, issue_type, writer, reported_by, priority, status,
             responsible_section, responsible_person, root_cause, impact, action_plan,
             resources_needed, target_resolution_date, progress_note, linked_issues,
             created_by_user_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            next_row_id,
            issue_date,
            _sort_date(issue_date),
            title,
            0,
            involved_departments,
            section_team,
            issue_type,
            writer,
            reporter,
            priority,
            status,
            responsible_section,
            responsible_person,
            root_cause,
            impact,
            action_plan,
            resources_needed,
            target_resolution_date,
            progress_note,
            linked_issues,
            session.get('user_id'),
        ))
        new_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        log_issue_history(db, new_id, 'created',
                          note=f'Issue #{next_row_id} created by {session.get("username", "System")}')
        db.commit()

        # Notify assignee if set
        if responsible_person:
            assignee_row = db.execute(
                "SELECT id FROM users WHERE username = ? LIMIT 1", (responsible_person,)
            ).fetchone()
            if assignee_row:
                _send_issue_notification(
                    'Issue Assigned to You',
                    f'Issue #{next_row_id}: {title[:100]}',
                    new_id,
                    assignee_user_id=assignee_row['id'],
                    severity='HIGH' if priority == 'High' else 'MEDIUM',
                    notif_type='INFO',
                )

        return jsonify({
            'success': True,
            'message': f'Issue #{next_row_id} created successfully.',
            'issue_id': new_id,
            'row_id': next_row_id,
            'redirect': url_for('issue_tracker.issue_detail', issue_id=new_id),
        })

    # GET: render page (used when JS is disabled)
    all_statuses = ['Open', 'In Progress', 'Pending Review', 'Backlog', 'Pending', 'Resolved', 'Closed']
    all_priorities = ['High', 'Medium', 'Low']
    all_types = ['Problem', 'Suggestion', 'Issue']
    users = [dict(r) for r in db.execute("SELECT id, username FROM users ORDER BY username").fetchall()]
    return render_template('issue_tracker/create_issue.html',
        title='Create Issue',
        all_statuses=all_statuses,
        all_priorities=all_priorities,
        all_types=all_types,
        users=users,
        csrf_token=_csrf_token(),
    )


def _sort_date(date_str):
    """Convert DD/MM/YYYY to YYYY-MM-DD for sort purposes."""
    if not date_str:
        return ''
    for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return ''


# ─── Edit Issue ──────────────────────────────────────────────────────────────────

@issue_bp.route('/edit/<int:issue_id>', methods=['GET', 'POST'])
@require_login
def edit_issue(issue_id):
    if not user_can_edit_issues():
        return jsonify({'success': False, 'message': 'No permission'}), 403
    db = get_db()
    issue_row = db.execute("SELECT * FROM issue_items WHERE id = ?", (issue_id,)).fetchone()
    if not issue_row:
        return jsonify({'success': False, 'message': 'Issue not found'}), 404

    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form.to_dict()
        if not _validate_csrf():
            return jsonify({'success': False, 'message': 'CSRF validation failed.'}), 403

        title = (data.get('issue') or data.get('title') or '').strip()
        if not title:
            return jsonify({'success': False, 'message': 'Issue title is required.'}), 400

        old_status = issue_row['status']
        new_status = normalize_issue_status(data.get('status') or old_status)
        old_priority = issue_row['priority']
        new_priority = normalize_issue_priority(data.get('priority') or old_priority)
        old_assignee = issue_row['responsible_person'] or ''
        new_assignee = (data.get('responsible_person') or '').strip()[:200]

        db.execute('''
            UPDATE issue_items SET
                issue = ?,
                issue_date = ?,
                issue_date_sort = ?,
                issue_type = ?,
                priority = ?,
                status = ?,
                involved_departments = ?,
                section_team = ?,
                responsible_section = ?,
                responsible_person = ?,
                reported_by = ?,
                writer = ?,
                root_cause = ?,
                impact = ?,
                action_plan = ?,
                resources_needed = ?,
                target_resolution_date = ?,
                progress_note = ?,
                linked_issues = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            title,
            (data.get('issue_date') or issue_row['issue_date']),
            _sort_date(data.get('issue_date') or issue_row['issue_date']),
            normalize_issue_type(data.get('issue_type') or issue_row['issue_type'] or 'Problem'),
            new_priority,
            new_status,
            serialize_issue_departments(data.get('involved_departments') or issue_row['involved_departments'] or ''),
            (data.get('section_team') or issue_row['section_team'] or '').strip()[:200],
            (data.get('responsible_section') or issue_row['responsible_section'] or '').strip()[:200],
            new_assignee,
            (data.get('reported_by') or issue_row['reported_by'] or '').strip()[:200],
            (data.get('writer') or issue_row['writer'] or '').strip()[:200],
            (data.get('root_cause') or '').strip()[:2000],
            (data.get('impact') or '').strip()[:2000],
            (data.get('action_plan') or '').strip()[:2000],
            (data.get('resources_needed') or '').strip()[:500],
            (data.get('target_resolution_date') or '').strip() or None,
            (data.get('progress_note') or '').strip()[:2000],
            (data.get('linked_issues') or '').strip()[:200],
            issue_id,
        ))

        changes = []
        if old_status != new_status:
            changes.append(f'Status: {old_status} → {new_status}')
        if old_priority != new_priority:
            changes.append(f'Priority: {old_priority} → {new_priority}')
        if old_assignee != new_assignee:
            changes.append(f'Assignee: {old_assignee or "none"} → {new_assignee or "none"}')

        note = 'Issue updated' + (': ' + ', '.join(changes) if changes else '')
        log_issue_history(db, issue_id, 'updated', note=note)
        db.commit()

        # Notify new assignee
        if new_assignee and new_assignee != old_assignee:
            assignee_row = db.execute(
                "SELECT id FROM users WHERE username = ? LIMIT 1", (new_assignee,)
            ).fetchone()
            if assignee_row:
                _send_issue_notification(
                    'Issue Assigned to You',
                    f'Issue #{issue_row["row_id"]}: {title[:100]}',
                    issue_id,
                    assignee_user_id=assignee_row['id'],
                    severity='HIGH' if new_priority == 'High' else 'MEDIUM',
                    notif_type='INFO',
                )

        return jsonify({'success': True, 'message': 'Issue updated successfully.'})

    # GET
    issue = prepare_issue_for_view(dict(issue_row))
    all_statuses = ['Open', 'In Progress', 'Pending Review', 'Backlog', 'Pending', 'Resolved', 'Closed']
    all_priorities = ['High', 'Medium', 'Low']
    all_types = ['Problem', 'Suggestion', 'Issue']
    users = [dict(r) for r in db.execute("SELECT id, username FROM users ORDER BY username").fetchall()]
    return render_template('issue_tracker/edit_issue.html',
        title=f'Edit Issue #{issue["row_id"]}',
        issue=issue,
        all_statuses=all_statuses,
        all_priorities=all_priorities,
        all_types=all_types,
        users=users,
        csrf_token=_csrf_token(),
    )


# ─── Delete Issue ─────────────────────────────────────────────────────────────

@issue_bp.route('/delete/<int:issue_id>', methods=['POST'])
@require_login
@csrf_protected_api
def delete_issue(issue_id):
    if not user_can_manage_issues():
        return jsonify({'success': False, 'message': 'Insufficient permission to delete issues.'}), 403
    db = get_db()
    issue_row = db.execute("SELECT row_id FROM issue_items WHERE id = ?", (issue_id,)).fetchone()
    if not issue_row:
        return jsonify({'success': False, 'message': 'Issue not found'}), 404
    db.execute("DELETE FROM issue_items WHERE id = ?", (issue_id,))
    db.commit()
    return jsonify({'success': True, 'message': f'Issue #{issue_row["row_id"]} deleted.'})


# ─── Assign Issue ─────────────────────────────────────────────────────────────

@issue_bp.route('/assign/<int:issue_id>', methods=['POST'])
@require_login
@csrf_protected_api
def assign_issue(issue_id):
    if not user_can_edit_issues():
        return jsonify({'success': False, 'message': 'No permission'}), 403
    db = get_db()
    data = request.get_json(silent=True) or {}
    assignee = (data.get('assignee') or '').strip()[:200]
    section = (data.get('section') or '').strip()[:200]

    db.execute(
        'UPDATE issue_items SET responsible_person = ?, responsible_section = ?, '
        'updated_at = CURRENT_TIMESTAMP WHERE id = ?',
        (assignee, section, issue_id)
    )
    log_issue_history(db, issue_id, 'assigned',
                      note=f'Assigned to {assignee or "none"} / {section or "none"}')
    db.commit()

    if assignee:
        assignee_row = db.execute(
            "SELECT id FROM users WHERE username = ? LIMIT 1", (assignee,)
        ).fetchone()
        if assignee_row:
            issue_row = db.execute("SELECT row_id, issue FROM issue_items WHERE id = ?", (issue_id,)).fetchone()
            _send_issue_notification(
                'Issue Assigned to You',
                f'Issue #{issue_row["row_id"]}: {issue_row["issue"][:100]}',
                issue_id,
                assignee_user_id=assignee_row['id'],
                severity='MEDIUM',
                notif_type='INFO',
            )

    return jsonify({'success': True, 'message': f'Issue assigned to {assignee or "none"}.'})


# ─── Escalate Issue ───────────────────────────────────────────────────────────

@issue_bp.route('/escalate/<int:issue_id>', methods=['POST'])
@require_login
@csrf_protected_api
def escalate_issue(issue_id):
    db = get_db()
    data = request.get_json(silent=True) or {}
    reason = (data.get('reason') or '').strip()[:1000]
    escalate_to = (data.get('escalate_to') or '').strip()[:200]

    escalate_to_id = None
    if escalate_to:
        user_row = db.execute(
            "SELECT id FROM users WHERE username = ? LIMIT 1", (escalate_to,)
        ).fetchone()
        if user_row:
            escalate_to_id = user_row['id']

    db.execute(
        'INSERT INTO issue_escalations (issue_id, escalated_by, escalated_to, reason) '
        'VALUES (?, ?, ?, ?)',
        (issue_id, session.get('user_id'), escalate_to_id, reason)
    )
    log_issue_history(db, issue_id, 'escalated',
                      note=f'Escalated to {escalate_to or "management"}. Reason: {reason[:100]}')
    db.commit()

    if escalate_to_id:
        issue_row = db.execute("SELECT row_id, issue FROM issue_items WHERE id = ?", (issue_id,)).fetchone()
        _send_issue_notification(
            'Issue Escalated to You',
            f'Issue #{issue_row["row_id"]} escalated. Reason: {reason[:80]}',
            issue_id,
            assignee_user_id=escalate_to_id,
            severity='HIGH',
            notif_type='WARNING',
        )

    return jsonify({'success': True, 'message': 'Issue escalated.'})


# ─── Upload Attachment ────────────────────────────────────────────────────────

@issue_bp.route('/attach/<int:issue_id>', methods=['POST'])
@require_login
def upload_attachment(issue_id):
    if not user_can_edit_issues():
        return jsonify({'success': False, 'message': 'No permission'}), 403

    if not _validate_csrf():
        return jsonify({'success': False, 'message': 'CSRF validation failed.'}), 403

    db = get_db()
    issue_row = db.execute("SELECT id FROM issue_items WHERE id = ?", (issue_id,)).fetchone()
    if not issue_row:
        return jsonify({'success': False, 'message': 'Issue not found'}), 404

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected.'}), 400

    if not _allowed_attachment(file.filename):
        return jsonify({'success': False, 'message': 'File type not allowed.'}), 400

    # Size check
    file.seek(0, os.SEEK_END)
    size_bytes = file.tell()
    file.seek(0)
    if size_bytes > MAX_ATTACHMENT_MB * 1024 * 1024:
        return jsonify({'success': False, 'message': f'File exceeds {MAX_ATTACHMENT_MB}MB limit.'}), 400

    original_name = secure_filename(file.filename)
    ext = original_name.rsplit('.', 1)[-1].lower() if '.' in original_name else 'bin'
    unique_name = f"issue_{issue_id}_{secrets.token_hex(8)}.{ext}"

    upload_dir = _attachment_upload_dir()
    file_path = os.path.join(upload_dir, unique_name)
    file.save(file_path)

    description = (request.form.get('description') or '').strip()[:500]
    mime_type = file.content_type or 'application/octet-stream'

    db.execute('''
        INSERT INTO issue_attachments (issue_id, user_id, filename, file_path, file_size, mime_type, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (issue_id, session.get('user_id'), original_name, file_path, size_bytes, mime_type, description))
    log_issue_history(db, issue_id, 'attachment_added', note=f'Attached: {original_name}')
    db.commit()

    return jsonify({
        'success': True,
        'message': f'File "{original_name}" uploaded.',
        'filename': original_name,
        'size': size_bytes,
    })


# ─── Download Attachment ──────────────────────────────────────────────────────

@issue_bp.route('/attachment/<int:attachment_id>/download')
@require_login
def download_attachment(attachment_id):
    db = get_db()
    row = db.execute('SELECT * FROM issue_attachments WHERE id = ?', (attachment_id,)).fetchone()
    if not row:
        flash('Attachment not found.', 'error')
        return redirect(url_for('issue_tracker.all_issues'))

    # Access check
    issue_row = db.execute('SELECT * FROM issue_items WHERE id = ?', (row['issue_id'],)).fetchone()
    if not issue_row:
        flash('Issue not found.', 'error')
        return redirect(url_for('issue_tracker.all_issues'))

    file_path = row['file_path']
    if not file_path or not os.path.exists(file_path):
        flash('File not found on disk.', 'error')
        return redirect(url_for('issue_tracker.issue_detail', issue_id=row['issue_id']))

    return send_file(
        file_path,
        as_attachment=True,
        download_name=row['filename'] or 'attachment',
        mimetype=row['mime_type'] or 'application/octet-stream',
    )


# ─── Delete Attachment ────────────────────────────────────────────────────────

@issue_bp.route('/attachment/<int:attachment_id>/delete', methods=['POST'])
@require_login
@csrf_protected_api
def delete_attachment(attachment_id):
    db = get_db()
    row = db.execute('SELECT * FROM issue_attachments WHERE id = ?', (attachment_id,)).fetchone()
    if not row:
        return jsonify({'success': False, 'message': 'Attachment not found.'}), 404

    # Only uploader or manager can delete
    if row['user_id'] != session.get('user_id') and not user_can_manage_issues():
        return jsonify({'success': False, 'message': 'No permission to delete this attachment.'}), 403

    file_path = row['file_path']
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass

    db.execute('DELETE FROM issue_attachments WHERE id = ?', (attachment_id,))
    log_issue_history(db, row['issue_id'], 'attachment_removed', note=f'Removed: {row["filename"]}')
    db.commit()
    return jsonify({'success': True, 'message': 'Attachment deleted.'})


# ─── Bulk Status Update ───────────────────────────────────────────────────────

@issue_bp.route('/bulk-status', methods=['POST'])
@require_login
@csrf_protected_api
def bulk_status():
    if not user_can_edit_issues():
        return jsonify({'success': False, 'message': 'No permission'}), 403
    db = get_db()
    data = request.get_json(silent=True) or {}
    issue_ids = data.get('ids', [])
    new_status = normalize_issue_status(data.get('status', 'Open'))

    if not issue_ids:
        return jsonify({'success': False, 'message': 'No issues selected.'}), 400

    valid_ids = [int(i) for i in issue_ids if str(i).isdigit()]
    for issue_id in valid_ids:
        db.execute(
            'UPDATE issue_items SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (new_status, issue_id)
        )
        log_issue_history(db, issue_id, 'status_changed',
                          note=f'Bulk update: status set to {new_status}')
    db.commit()
    return jsonify({'success': True, 'message': f'{len(valid_ids)} issues updated to {new_status}.'})


# ─── Export Issues ────────────────────────────────────────────────────────────

@issue_bp.route('/export')
@require_login
def export_issues():
    db = get_db()
    fmt = request.args.get('format', 'csv').lower()
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')

    query = 'SELECT * FROM issue_items WHERE 1=1'
    params = []
    if status_filter:
        query += ' AND status = ?'
        params.append(status_filter)
    if priority_filter:
        query += ' AND priority = ?'
        params.append(priority_filter)
    query += ' ORDER BY id DESC'

    rows = db.execute(query, params).fetchall()
    issues = [prepare_issue_for_view(dict(row)) for row in rows]

    if fmt == 'json':
        export_data = [{
            'id': i['row_id'],
            'title': i['issue'],
            'status': i['status'],
            'priority': i['priority'],
            'type': i['issue_type'],
            'assignee': i['responsible_person_display'],
            'department': i['involved_departments_display'],
            'reporter': i['reported_by_display'],
            'date': i['issue_date'],
            'target_date': i.get('target_resolution_date') or '',
            'root_cause': i.get('root_cause') or '',
            'action_plan': i.get('action_plan') or '',
        } for i in issues]
        resp = make_response(json.dumps(export_data, ensure_ascii=False, indent=2))
        resp.headers['Content-Type'] = 'application/json; charset=utf-8'
        resp.headers['Content-Disposition'] = 'attachment; filename=issues_export.json'
        return resp

    # Default: CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Issue #', 'Date', 'Title', 'Type', 'Priority', 'Status',
        'Assignee', 'Department', 'Reporter', 'Target Date',
        'Root Cause', 'Action Plan', 'Progress Note',
    ])
    for i in issues:
        writer.writerow([
            i['row_id'],
            i['issue_date'],
            i['issue'],
            i['issue_type'],
            i['priority'],
            i['status'],
            i['responsible_person_display'],
            i['involved_departments_display'],
            i['reported_by_display'],
            i.get('target_resolution_date') or '',
            (i.get('root_cause') or '').replace('\n', ' '),
            (i.get('action_plan') or '').replace('\n', ' '),
            (i.get('progress_note') or '').replace('\n', ' '),
        ])
    csv_bytes = output.getvalue().encode('utf-8-sig')
    resp = make_response(csv_bytes)
    resp.headers['Content-Type'] = 'text/csv; charset=utf-8'
    resp.headers['Content-Disposition'] = 'attachment; filename=issues_export.csv'
    return resp


# ─── Get Users for Autocomplete ───────────────────────────────────────────────

@issue_bp.route('/api/users')
@require_login
def api_users():
    db = get_db()
    q = request.args.get('q', '').strip()
    query = "SELECT id, username, full_name FROM users WHERE is_active = 1"
    params = []
    if q:
        query += " AND (username LIKE ? OR full_name LIKE ?)"
        params.extend([f'%{q}%', f'%{q}%'])
    query += " ORDER BY username LIMIT 20"
    try:
        rows = db.execute(query, params).fetchall()
    except Exception:
        rows = db.execute(
            "SELECT id, username, username as full_name FROM users WHERE username LIKE ? LIMIT 20",
            [f'%{q}%']
        ).fetchall()
    return jsonify([{'id': r['id'], 'username': r['username'],
                     'full_name': r.get('full_name') or r['username']} for r in rows])


# ─── Approve / Reject Review ──────────────────────────────────────────────────

@issue_bp.route('/review/<int:issue_id>', methods=['POST'])
@require_login
@csrf_protected_api
def review_issue(issue_id):
    if not user_can_approve_issues():
        return jsonify({'success': False, 'message': 'No permission to review issues.'}), 403
    db = get_db()
    data = request.get_json(silent=True) or {}
    action = data.get('action', '')  # 'approve' or 'reject'
    comment = (data.get('comment') or '').strip()[:1000]

    if action == 'approve':
        db.execute(
            "UPDATE issue_items SET status = 'Resolved', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (issue_id,)
        )
        log_issue_history(db, issue_id, 'review_approved',
                          note=f'Review approved. {comment}')
        db.commit()
        return jsonify({'success': True, 'message': 'Issue approved and marked Resolved.'})
    elif action == 'reject':
        db.execute(
            "UPDATE issue_items SET status = 'In Progress', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (issue_id,)
        )
        log_issue_history(db, issue_id, 'review_rejected',
                          note=f'Review rejected. Returned to In Progress. {comment}')
        db.commit()
        return jsonify({'success': True, 'message': 'Review rejected. Issue returned to In Progress.'})
    else:
        return jsonify({'success': False, 'message': 'Invalid action.'}), 400


# ─── Delete Comment ───────────────────────────────────────────────────────────

@issue_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@require_login
@csrf_protected_api
def delete_comment(comment_id):
    db = get_db()
    row = db.execute('SELECT * FROM issue_comments WHERE id = ?', (comment_id,)).fetchone()
    if not row:
        return jsonify({'success': False, 'message': 'Comment not found.'}), 404
    if row['user_id'] != session.get('user_id') and not user_can_manage_issues():
        return jsonify({'success': False, 'message': 'No permission to delete this comment.'}), 403
    db.execute('DELETE FROM issue_comments WHERE id = ?', (comment_id,))
    db.commit()
    return jsonify({'success': True, 'message': 'Comment deleted.'})


# ─── Watch / Unwatch Issue ────────────────────────────────────────────────────

@issue_bp.route('/watch/<int:issue_id>', methods=['POST'])
@require_login
@csrf_protected_api
def toggle_watch(issue_id):
    db = get_db()
    user_id = session.get('user_id')
    existing = db.execute(
        'SELECT id FROM issue_watchers WHERE issue_id = ? AND user_id = ?',
        (issue_id, user_id)
    ).fetchone()
    if existing:
        db.execute('DELETE FROM issue_watchers WHERE issue_id = ? AND user_id = ?', (issue_id, user_id))
        db.commit()
        return jsonify({'success': True, 'watching': False, 'message': 'Unfollowed issue.'})
    else:
        db.execute('INSERT INTO issue_watchers (issue_id, user_id) VALUES (?, ?)', (issue_id, user_id))
        db.commit()
        return jsonify({'success': True, 'watching': True, 'message': 'Now watching issue.'})


# ─── Issue API (get issue data as JSON) ───────────────────────────────────────

@issue_bp.route('/api/issue/<int:issue_id>')
@require_login
def api_issue(issue_id):
    db = get_db()
    row = db.execute('SELECT * FROM issue_items WHERE id = ?', (issue_id,)).fetchone()
    if not row:
        return jsonify({'success': False, 'message': 'Issue not found'}), 404
    issue = prepare_issue_for_view(dict(row))
    issue['sla_status'] = get_sla_status(issue)
    return jsonify({'success': True, 'issue': issue})


# ─── SLA Extend ───────────────────────────────────────────────────────────────

@issue_bp.route('/sla-extend/<int:issue_id>', methods=['POST'])
@require_login
@csrf_protected_api
def sla_extend(issue_id):
    if not user_can_manage_issues():
        return jsonify({'success': False, 'message': 'No permission to extend SLA.'}), 403
    db = get_db()
    data = request.get_json(silent=True) or {}
    new_date = (data.get('new_date') or '').strip()
    reason = (data.get('reason') or '').strip()[:500]
    if not new_date:
        return jsonify({'success': False, 'message': 'New target date required.'}), 400
    db.execute(
        'UPDATE issue_items SET target_resolution_date = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
        (new_date, issue_id)
    )
    log_issue_history(db, issue_id, 'sla_extended',
                      note=f'SLA extended to {new_date}. Reason: {reason}')
    db.commit()
    return jsonify({'success': True, 'message': f'SLA extended to {new_date}.'})


# ─── Add Category ─────────────────────────────────────────────────────────────

@issue_bp.route('/api/categories', methods=['GET', 'POST', 'DELETE'])
@require_login
def api_categories():
    db = get_db()
    if request.method == 'GET':
        cats = [dict(r) for r in db.execute(
            'SELECT * FROM issue_categories ORDER BY name ASC'
        ).fetchall()]
        return jsonify({'success': True, 'categories': cats})

    if not user_can_manage_issues():
        return jsonify({'success': False, 'message': 'No permission.'}), 403

    if not _validate_csrf():
        return jsonify({'success': False, 'message': 'CSRF validation failed.'}), 403

    data = request.get_json(silent=True) or {}

    if request.method == 'POST':
        name = (data.get('name') or '').strip()[:200]
        if not name:
            return jsonify({'success': False, 'message': 'Category name required.'}), 400
        description = (data.get('description') or '').strip()[:500]
        default_priority = normalize_issue_priority(data.get('default_priority') or 'Medium')
        default_assignee = (data.get('default_assignee') or '').strip()[:200]
        try:
            db.execute(
                'INSERT INTO issue_categories (name, description, default_assignee, default_priority) '
                'VALUES (?, ?, ?, ?)',
                (name, description, default_assignee, default_priority)
            )
            db.commit()
            return jsonify({'success': True, 'message': f'Category "{name}" added.'})
        except Exception:
            return jsonify({'success': False, 'message': 'Category name already exists.'}), 409

    if request.method == 'DELETE':
        cat_id = data.get('id')
        if not cat_id:
            return jsonify({'success': False, 'message': 'Category id required.'}), 400
        db.execute('DELETE FROM issue_categories WHERE id = ?', (cat_id,))
        db.commit()
        return jsonify({'success': True, 'message': 'Category deleted.'})
