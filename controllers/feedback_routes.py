"""
Feedback & Issue Reporting Routes
================================
Complete enterprise-grade feedback, bug report, and issue tracking system.

Routes:
- Dashboard: Overview statistics and recent activity
- Reports List: Filterable list with search, pagination
- My Reports: Reports submitted by current user
- Assigned to Me: Reports assigned to current user
- Report Detail: Full report view with attachments, comments, history
- Create Report: Rich submission form
- Edit Report: Update report details
- API endpoints: Attachment upload, comments, status changes, assignment

Features:
- Rich report creation with all fields
- File attachment upload (images, videos, documents, audio)
- Voice recording support (real browser audio recording)
- Status workflow management
- Assignment to users/teams
- Internal and public comments
- Full activity history
- Search, filters, export
- Notifications
- RBAC permissions
"""

import os
import io
import re
import json
import uuid
import secrets
import hmac
import mimetypes
import csv
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Blueprint, request, session, render_template, jsonify,
    redirect, url_for, flash, send_file, make_response, current_app
)
from werkzeug.utils import secure_filename

from database import get_db, get_db_context, get_one, get_all, create_notification, log_audit
from permissions import user_has_permission, check_permission
from flow_models import get_flow_profile
from feedback_models import (
    init_feedback_tables, get_categories, get_reports, get_report_by_id,
    get_report_attachments, get_report_comments, get_report_activity,
    get_report_status_history, create_report, update_report, change_status,
    assign_report, add_comment, add_attachment, delete_report, get_stats,
    search_reports, generate_reference_number, get_platform_setting,
    REPORT_TYPES, REPORT_TYPE_LABELS, STATUS_CHOICES, STATUS_COLORS,
    PRIORITY_CHOICES, PRIORITY_COLORS, SEVERITY_CHOICES, SEVERITY_COLORS,
    IMPACT_CHOICES, URGENCY_CHOICES, FREQUENCY_CHOICES, VISIBILITY_CHOICES,
    STATUS_DRAFT, STATUS_SUBMITTED, STATUS_NEW, STATUS_CLOSED, STATUS_RESOLVED,
)

# Create blueprint
feedback_bp = Blueprint('feedback', __name__, url_prefix='/feedback',
                       template_folder='templates/feedback')

# =============================================================================
# UPLOAD CONFIGURATION
# =============================================================================

FEEDBACK_UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 
    'static', 'feedback_uploads'
)
os.makedirs(os.path.join(FEEDBACK_UPLOAD_FOLDER, 'images'), exist_ok=True)
os.makedirs(os.path.join(FEEDBACK_UPLOAD_FOLDER, 'videos'), exist_ok=True)
os.makedirs(os.path.join(FEEDBACK_UPLOAD_FOLDER, 'audio'), exist_ok=True)
os.makedirs(os.path.join(FEEDBACK_UPLOAD_FOLDER, 'files'), exist_ok=True)
os.makedirs(os.path.join(FEEDBACK_UPLOAD_FOLDER, 'voice'), exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx', 
                      'xls', 'xlsx', 'txt', 'csv', 'zip', 'rar', 'mp4', 'mov',
                      'webm', 'mp3', 'wav', 'ogg', 'm4a', 'bmp', 'svg'}
MAX_FILE_SIZE_MB = 50
MAX_VOICE_SIZE_MB = 10

# =============================================================================
# AUTHENTICATION & PERMISSIONS
# =============================================================================

def require_login(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Please login first'}), 401
            flash("Please login to access this page.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def can_view_feedback():
    """Check if current user can view feedback reports."""
    if 'user_id' not in session:
        return False
    # All authenticated users can view
    return True


def can_create_feedback():
    """Check if current user can create feedback reports."""
    if 'user_id' not in session:
        return False
    return True


def can_manage_feedback():
    """Check if current user can manage (edit/delete) any feedback."""
    if 'user_id' not in session:
        return False
    return check_permission(session['user_id'], 'feedback', 'reports', 'manage')


def can_assign_feedback():
    """Check if current user can assign feedback reports."""
    if 'user_id' not in session:
        return False
    return (can_manage_feedback() or 
            check_permission(session['user_id'], 'feedback', 'reports', 'assign'))


def can_view_internal():
    """Check if current user can view internal comments."""
    if 'user_id' not in session:
        return False
    return (can_manage_feedback() or 
            check_permission(session['user_id'], 'feedback', 'reports', 'view_internal'))


def can_delete_feedback():
    """Check if current user can delete feedback reports."""
    if 'user_id' not in session:
        return False
    return can_manage_feedback()


# =============================================================================
# CSRF PROTECTION
# =============================================================================

def _csrf_token():
    """Get or generate CSRF token."""
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


def csrf_protected(f):
    """Decorator: validates CSRF for mutating endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            if not _validate_csrf():
                if request.is_json:
                    return jsonify({'success': False, 'message': 'CSRF validation failed'}), 403
                flash("Security validation failed. Please try again.", "error")
                return redirect(request.referrer or url_for('feedback.dashboard'))
        return f(*args, **kwargs)
    return decorated


# =============================================================================
# FILE UPLOAD HELPERS
# =============================================================================

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_type(filename):
    """Determine file type category."""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext in {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'}:
        return 'image'
    elif ext in {'mp4', 'mov', 'webm'}:
        return 'video'
    elif ext in {'mp3', 'wav', 'ogg', 'm4a'}:
        return 'audio'
    elif ext in {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'csv'}:
        return 'document'
    elif ext in {'zip', 'rar'}:
        return 'archive'
    return 'file'


def save_uploaded_file(file, subfolder=''):
    """Save an uploaded file and return info dict."""
    if not file or not file.filename:
        return None
    
    if not allowed_file(file.filename):
        return None
    
    # Check file size
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    
    max_size = MAX_VOICE_SIZE_MB * 1024 * 1024 if subfolder == 'voice' else MAX_FILE_SIZE_MB * 1024 * 1024
    if size > max_size:
        return None
    
    # Generate unique filename
    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    unique_name = f"{uuid.uuid4().hex}_{secrets.token_hex(8)}.{ext}"
    
    # Determine subfolder
    if subfolder:
        folder = os.path.join(FEEDBACK_UPLOAD_FOLDER, subfolder)
    else:
        file_type = get_file_type(original_filename)
        folder = os.path.join(FEEDBACK_UPLOAD_FOLDER, file_type)
    
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, unique_name)
    file.save(filepath)
    
    return {
        'file_name': original_filename,
        'file_path': os.path.relpath(filepath, os.path.join(os.path.dirname(__file__), 'static')).replace('\\', '/'),
        'file_type': get_file_type(original_filename),
        'file_size': size,
        'mime_type': mimetypes.guess_type(original_filename)[0] or 'application/octet-stream',
    }


# =============================================================================
# NOTIFICATION HELPERS
# =============================================================================

def notify_report_submitted(report_id, report):
    """Send notification when a report is submitted."""
    try:
        # Notify admins/support
        create_notification(
            title=f"New Feedback: {report.get('title', '')[:50]}",
            message=f"A new {report.get('report_type', 'feedback')} report has been submitted.",
            notification_type='INFO',
            severity='MEDIUM',
            link_url=url_for('feedback.report_detail', report_id=report_id),
            related_entity_type='feedback_report',
            related_entity_id=report_id,
        )
    except Exception:
        pass


def notify_report_assigned(report_id, report, assignee_id):
    """Send notification when a report is assigned."""
    try:
        create_notification(
            title=f"Feedback Assigned: {report.get('title', '')[:50]}",
            message=f"A feedback report has been assigned to you.",
            notification_type='INFO',
            user_id=assignee_id,
            severity='MEDIUM',
            link_url=url_for('feedback.report_detail', report_id=report_id),
            related_entity_type='feedback_report',
            related_entity_id=report_id,
        )
    except Exception:
        pass


def notify_status_changed(report_id, report, old_status, new_status, user_id):
    """Send notification when status changes."""
    try:
        # Notify reporter if different from changer
        if report.get('reporter_user_id') and report.get('reporter_user_id') != user_id:
            create_notification(
                title=f"Feedback Status Updated",
                message=f"Your report '{report.get('title', '')[:50]}' status changed from {old_status} to {new_status}.",
                notification_type='INFO',
                user_id=report.get('reporter_user_id'),
                severity='LOW',
                link_url=url_for('feedback.report_detail', report_id=report_id),
                related_entity_type='feedback_report',
                related_entity_id=report_id,
            )
    except Exception:
        pass


# =============================================================================
# TEMPLATE HELPERS
# =============================================================================

def prepare_report_for_view(report):
    """Prepare a report for template rendering."""
    if not report:
        return None
    
    # Status badge
    status_info = STATUS_COLORS.get(report.get('status', ''), ('gray', 'bg-gray-500/10 text-gray-400 border-gray-500/20'))
    report['status_color'] = status_info[0]
    report['status_badge_class'] = status_info[1]
    
    # Priority badge
    report['priority_badge_class'] = PRIORITY_COLORS.get(report.get('priority', 'Medium'), 'bg-gray-500/10 text-gray-400 border-gray-500/20')
    
    # Severity badge
    report['severity_badge_class'] = SEVERITY_COLORS.get(report.get('severity', 'Minor'), 'bg-gray-500/10 text-gray-400 border-gray-500/20')
    
    # Impact badge
    report['impact_badge_class'] = IMPACT_COLORS.get(report.get('impact', 'Low'), 'bg-gray-500/10 text-gray-400 border-gray-500/20')
    
    # Urgency badge
    report['urgency_badge_class'] = URGENCY_COLORS.get(report.get('urgency', 'Normal'), 'bg-gray-500/10 text-gray-400 border-gray-500/20')
    
    # Type label
    report['type_label'] = REPORT_TYPE_LABELS.get(report.get('report_type'), report.get('report_type', 'Feedback').replace('_', ' ').title())
    
    # Format dates
    for date_field in ['created_at', 'updated_at', 'submitted_at', 'resolved_at', 'closed_at', 'occurrence_date']:
        if report.get(date_field) and isinstance(report[date_field], str):
            try:
                dt = datetime.fromisoformat(report[date_field])
                report[f'{date_field}_formatted'] = dt.strftime('%b %d, %Y %H:%M')
                report[f'{date_field}_date'] = dt.strftime('%Y-%m-%d')
            except:
                report[f'{date_field}_formatted'] = report[date_field]
                report[f'{date_field}_date'] = report[date_field]
    
    # Tags list
    if report.get('tags'):
        try:
            report['tags_list'] = json.loads(report['tags']) if isinstance(report['tags'], str) else report['tags']
        except:
            report['tags_list'] = []
    else:
        report['tags_list'] = []
    
    return report


def get_user_display_name(user_id):
    """Get display name for a user."""
    if not user_id:
        return 'System'
    profile = get_flow_profile(user_id)
    if profile:
        return profile.get('display_name') or profile.get('username', f'User {user_id}')
    return f'User {user_id}'


# =============================================================================
# ROUTES: DASHBOARD
# =============================================================================

@feedback_bp.route('/')
@feedback_bp.route('/dashboard')
@require_login
def dashboard():
    """Main dashboard with statistics and recent reports."""
    if not can_view_feedback():
        flash("You don't have permission to view feedback.", "error")
        return redirect(url_for('index'))
    
    user_id = session.get('user_id')
    stats = get_stats()
    
    # Get recent reports
    recent_result = get_reports(page=1, per_page=10, order_by='created_at DESC')
    recent_reports = [prepare_report_for_view(r) for r in recent_result['reports']]
    
    # Get my reports count
    my_reports_result = get_reports(filters={'reporter': user_id})
    my_reports_count = my_reports_result['total']
    
    # Get assigned to me count
    assigned_result = get_reports(filters={'assigned_to': user_id})
    assigned_count = assigned_result['total']
    
    # Get open reports (not closed/resolved)
    open_statuses = ['New', 'Acknowledged', 'Under Review', 'Assigned', 'In Progress', 
                     'Waiting for User', 'Waiting for Internal', 'Submitted', 'Reopened', 'Escalated']
    open_result = get_reports(filters={'status': open_statuses})
    open_count = open_result['total']
    
    # Get status breakdown
    status_breakdown = stats.get('by_status', {})
    
    # Priority breakdown
    priority_breakdown = stats.get('by_priority', {})
    
    # Type breakdown
    type_breakdown = stats.get('by_type', {})
    
    # Category breakdown
    category_breakdown = stats.get('by_category', {})
    
    # Recent activity
    recent_activity = get_all("""
        SELECT fal.*, fr.reference_number, fr.title as report_title
        FROM feedback_activity_log fal
        JOIN feedback_reports fr ON fal.report_id = fr.id
        WHERE fr.is_deleted = 0
        ORDER BY fal.created_at DESC
        LIMIT 20
    """)
    recent_activity = [dict(row) for row in recent_activity] if recent_activity else []
    
    # Trend data (last 14 days for dashboard)
    from collections import Counter
    from datetime import date as dt_date
    today = dt_date.today()
    trend_data = []
    for i in range(14, -1, -1):
        day = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        day_stats = get_stats(filters={'date_from': day, 'date_to': day})
        trend_data.append({
            'date': day,
            'total': day_stats['total'],
            'open': day_stats['open'],
            'resolved': day_stats['resolved'],
        })
    
    return render_template('feedback/dashboard.html',
        title='Feedback Dashboard',
        stats=stats,
        recent_reports=recent_reports,
        my_reports_count=my_reports_count,
        assigned_count=assigned_count,
        open_count=open_count,
        status_breakdown=status_breakdown,
        priority_breakdown=priority_breakdown,
        type_breakdown=type_breakdown,
        category_breakdown=category_breakdown,
        recent_activity=recent_activity,
        trend_data=trend_data,
        date=today,
        can_create=can_create_feedback(),
        can_manage=can_manage_feedback(),
        csrf_token=_csrf_token(),
    )


# =============================================================================
# ROUTES: REPORTS LIST
# =============================================================================

@feedback_bp.route('/reports')
@require_login
def reports_list():
    """List all reports with filtering."""
    if not can_view_feedback():
        flash("You don't have permission to view feedback.", "error")
        return redirect(url_for('index'))
    
    # Parse filters
    filters = {}
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    if request.args.get('type'):
        filters['type'] = request.args.get('type')
    if request.args.get('priority'):
        filters['priority'] = request.args.get('priority')
    if request.args.get('category'):
        filters['category'] = int(request.args.get('category'))
    if request.args.get('assigned_to'):
        filters['assigned_to'] = int(request.args.get('assigned_to'))
    if request.args.get('search'):
        filters['search'] = request.args.get('search')
    if request.args.get('date_from'):
        filters['date_from'] = request.args.get('date_from')
    if request.args.get('date_to'):
        filters['date_to'] = request.args.get('date_to')
    
    page = max(1, int(request.args.get('page', 1)))
    per_page = int(request.args.get('per_page', 25))
    
    order_by = request.args.get('sort', 'created_at DESC')
    if order_by not in ['created_at DESC', 'created_at ASC', 'updated_at DESC', 'updated_at ASC',
                        'priority DESC', 'priority ASC', 'status ASC']:
        order_by = 'created_at DESC'
    
    result = get_reports(filters=filters, page=page, per_page=per_page, order_by=order_by)
    reports = [prepare_report_for_view(r) for r in result['reports']]
    
    categories = get_categories()
    
    # Status counts for filter tabs
    all_statuses_result = get_reports(page=1, per_page=1)
    status_counts = {}
    for status in STATUS_CHOICES:
        count_result = get_reports(filters={'status': status}, page=1, per_page=1)
        status_counts[status] = count_result['total']
    
    return render_template('feedback/reports_list.html',
        title='All Reports',
        reports=reports,
        categories=categories,
        filters=filters,
        result=result,
        status_counts=status_counts,
        report_types=REPORT_TYPES,
        priority_choices=PRIORITY_CHOICES,
        order_by=order_by,
        can_create=can_create_feedback(),
        can_manage=can_manage_feedback(),
        csrf_token=_csrf_token(),
    )


# =============================================================================
# ROUTES: MY REPORTS
# =============================================================================

@feedback_bp.route('/my-reports')
@require_login
def my_reports():
    """Reports submitted by the current user."""
    user_id = session.get('user_id')
    
    filters = {'reporter': user_id}
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    if request.args.get('search'):
        filters['search'] = request.args.get('search')
    
    page = max(1, int(request.args.get('page', 1)))
    result = get_reports(filters=filters, page=page, per_page=25)
    reports = [prepare_report_for_view(r) for r in result['reports']]
    
    return render_template('feedback/my_reports.html',
        title='My Reports',
        reports=reports,
        result=result,
        filters=filters,
        can_create=can_create_feedback(),
        csrf_token=_csrf_token(),
    )


# =============================================================================
# ROUTES: ASSIGNED TO ME
# =============================================================================

@feedback_bp.route('/assigned-to-me')
@require_login
def assigned_to_me():
    """Reports assigned to the current user."""
    user_id = session.get('user_id')
    
    filters = {'assigned_to': user_id}
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    if request.args.get('search'):
        filters['search'] = request.args.get('search')
    
    page = max(1, int(request.args.get('page', 1)))
    result = get_reports(filters=filters, page=page, per_page=25)
    reports = [prepare_report_for_view(r) for r in result['reports']]
    
    return render_template('feedback/assigned_to_me.html',
        title='Assigned to Me',
        reports=reports,
        result=result,
        filters=filters,
        can_create=can_create_feedback(),
        can_assign=can_assign_feedback(),
        csrf_token=_csrf_token(),
    )


# =============================================================================
# ROUTES: REPORT DETAIL
# =============================================================================

@feedback_bp.route('/report/<int:report_id>')
@feedback_bp.route('/report/<int:report_id>/')
@require_login
def report_detail(report_id):
    """View a single report with all details."""
    report = get_report_by_id(report_id)
    if not report:
        flash("Report not found.", "error")
        return redirect(url_for('feedback.reports_list'))
    
    report = prepare_report_for_view(report)
    
    # Check if user can view confidential reports
    if report.get('is_confidential') and not can_manage_feedback():
        flash("You don't have permission to view this confidential report.", "error")
        return redirect(url_for('feedback.reports_list'))
    
    # Get attachments
    attachments = get_report_attachments(report_id)
    
    # Get comments (internal only if permitted)
    include_internal = can_view_internal()
    comments = get_report_comments(report_id, include_internal=include_internal)
    
    # Get activity history
    activity = get_report_activity(report_id)
    
    # Get status history
    status_history = get_report_status_history(report_id)
    
    # Prepare comments for display
    for c in comments:
        if c.get('created_at') and isinstance(c['created_at'], str):
            try:
                dt = datetime.fromisoformat(c['created_at'])
                c['created_at_formatted'] = dt.strftime('%b %d, %Y %H:%M')
            except:
                c['created_at_formatted'] = c['created_at']
    
    # Check if current user is the reporter or assignee or manager
    user_id = session.get('user_id')
    is_reporter = report.get('reporter_user_id') == user_id
    is_assignee = report.get('assigned_to') == user_id
    can_edit = is_reporter or is_assignee or can_manage_feedback()
    
    return render_template('feedback/report_detail.html',
        title=f"Report {report.get('reference_number', '')}",
        report=report,
        attachments=attachments,
        comments=comments,
        activity=activity,
        status_history=status_history,
        can_edit=can_edit,
        can_assign=can_assign_feedback(),
        can_view_internal=can_view_internal(),
        can_delete=can_delete_feedback(),
        can_manage=can_manage_feedback(),
        status_choices=STATUS_CHOICES,
        priority_choices=PRIORITY_CHOICES,
        severity_choices=SEVERITY_CHOICES,
        categories=get_categories(),
        csrf_token=_csrf_token(),
    )


# =============================================================================
# ROUTES: CREATE REPORT
# =============================================================================

@feedback_bp.route('/create', methods=['GET', 'POST'])
@feedback_bp.route('/create/', methods=['GET', 'POST'])
@require_login
def create_report_view():
    """Create a new feedback report."""
    if not can_create_feedback():
        flash("You don't have permission to create reports.", "error")
        return redirect(url_for('feedback.dashboard'))
    
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        # Handle form submission
        data = {
            'title': request.form.get('title', '').strip(),
            'report_type': request.form.get('report_type', 'bug'),
            'category_id': int(request.form.get('category_id')) if request.form.get('category_id') else None,
            'priority': request.form.get('priority', 'Medium'),
            'severity': request.form.get('severity', 'Minor'),
            'impact': request.form.get('impact', 'Low'),
            'urgency': request.form.get('urgency', 'Normal'),
            'summary': request.form.get('summary', ''),
            'description': request.form.get('description', ''),
            'expected_behavior': request.form.get('expected_behavior', ''),
            'actual_behavior': request.form.get('actual_behavior', ''),
            'steps_to_reproduce': request.form.get('steps_to_reproduce', ''),
            'page_url': request.form.get('page_url', ''),
            'page_route': request.form.get('page_route', ''),
            'affected_module': request.form.get('affected_module', ''),
            'affected_department': request.form.get('affected_department', ''),
            'browser_info': request.form.get('browser_info', ''),
            'device_info': request.form.get('device_info', ''),
            'operating_system': request.form.get('operating_system', ''),
            'occurrence_date': request.form.get('occurrence_date', ''),
            'frequency': request.form.get('frequency', 'unknown'),
            'visibility': request.form.get('visibility', 'public'),
            'is_confidential': request.form.get('is_confidential') == '1',
            'reporter_name': get_user_display_name(user_id),
            'reporter_department': request.form.get('reporter_department', ''),
            'submit_now': request.form.get('submit') == 'true',
        }
        
        # Validate required fields
        if not data['title']:
            flash("Title is required.", "error")
            return render_template('feedback/create_report.html',
                title='Create Report',
                categories=get_categories(),
                report_types=REPORT_TYPES,
                priority_choices=PRIORITY_CHOICES,
                severity_choices=SEVERITY_CHOICES,
                impact_choices=IMPACT_CHOICES,
                urgency_choices=URGENCY_CHOICES,
                frequency_choices=FREQUENCY_CHOICES,
                visibility_choices=VISIBILITY_CHOICES,
                form_data=data,
                csrf_token=_csrf_token(),
            )
        
        # Create report
        report_id = create_report(data, user_id)
        
        # Handle file attachments
        files = request.files.getlist('attachments')
        for file in files:
            if file and file.filename:
                file_info = save_uploaded_file(file)
                if file_info:
                    add_attachment(report_id, file_info, user_id, get_user_display_name(user_id))
        
        # Handle voice recordings
        voice_files = request.files.getlist('voice_recordings')
        for voice_file in voice_files:
            if voice_file and voice_file.filename:
                file_info = save_uploaded_file(voice_file, subfolder='voice')
                if file_info:
                    file_info['file_type'] = 'audio'
                    add_attachment(report_id, file_info, user_id, get_user_display_name(user_id))
        
        flash("Report created successfully!", "success")
        
        if request.form.get('submit') == 'true':
            report = get_report_by_id(report_id)
            if report:
                notify_report_submitted(report_id, report)
        
        return redirect(url_for('feedback.report_detail', report_id=report_id))
    
    # GET request - show form
    categories = get_categories()
    
    # Pre-fill some data
    form_data = {
        'reporter_name': get_user_display_name(user_id),
        'priority': get_platform_setting('feedback_default_priority', 'Medium'),
        'report_type': 'bug',
    }
    
    return render_template('feedback/create_report.html',
        title='Create Report',
        categories=categories,
        report_types=REPORT_TYPES,
        priority_choices=PRIORITY_CHOICES,
        severity_choices=SEVERITY_CHOICES,
        impact_choices=IMPACT_CHOICES,
        urgency_choices=URGENCY_CHOICES,
        frequency_choices=FREQUENCY_CHOICES,
        visibility_choices=VISIBILITY_CHOICES,
        form_data=form_data,
        csrf_token=_csrf_token(),
    )


# =============================================================================
# ROUTES: EDIT REPORT
# =============================================================================

@feedback_bp.route('/report/<int:report_id>/edit', methods=['GET', 'POST'])
@require_login
def edit_report(report_id):
    """Edit an existing report."""
    report = get_report_by_id(report_id)
    if not report:
        flash("Report not found.", "error")
        return redirect(url_for('feedback.reports_list'))
    
    user_id = session.get('user_id')
    is_reporter = report.get('reporter_user_id') == user_id
    is_assignee = report.get('assigned_to') == user_id
    
    if not (is_reporter or is_assignee or can_manage_feedback()):
        flash("You don't have permission to edit this report.", "error")
        return redirect(url_for('feedback.report_detail', report_id=report_id))
    
    if request.method == 'POST':
        data = {
            'title': request.form.get('title', '').strip(),
            'report_type': request.form.get('report_type', 'bug'),
            'category_id': int(request.form.get('category_id')) if request.form.get('category_id') else None,
            'priority': request.form.get('priority', 'Medium'),
            'severity': request.form.get('severity', 'Minor'),
            'impact': request.form.get('impact', 'Low'),
            'urgency': request.form.get('urgency', 'Normal'),
            'summary': request.form.get('summary', ''),
            'description': request.form.get('description', ''),
            'expected_behavior': request.form.get('expected_behavior', ''),
            'actual_behavior': request.form.get('actual_behavior', ''),
            'steps_to_reproduce': request.form.get('steps_to_reproduce', ''),
            'page_url': request.form.get('page_url', ''),
            'affected_module': request.form.get('affected_module', ''),
            'affected_department': request.form.get('affected_department', ''),
            'occurrence_date': request.form.get('occurrence_date', ''),
            'frequency': request.form.get('frequency', 'unknown'),
            'visibility': request.form.get('visibility', 'public'),
            'is_confidential': request.form.get('is_confidential') == '1',
        }
        
        update_report(report_id, data, user_id, get_user_display_name(user_id))
        
        flash("Report updated successfully!", "success")
        return redirect(url_for('feedback.report_detail', report_id=report_id))
    
    # GET request - show form
    report = prepare_report_for_view(report)
    
    return render_template('feedback/edit_report.html',
        title=f"Edit Report {report.get('reference_number', '')}",
        report=report,
        categories=get_categories(),
        report_types=REPORT_TYPES,
        priority_choices=PRIORITY_CHOICES,
        severity_choices=SEVERITY_CHOICES,
        impact_choices=IMPACT_CHOICES,
        urgency_choices=URGENCY_CHOICES,
        frequency_choices=FREQUENCY_CHOICES,
        visibility_choices=VISIBILITY_CHOICES,
        csrf_token=_csrf_token(),
    )


# =============================================================================
# ROUTES: API ENDPOINTS
# =============================================================================

@feedback_bp.route('/api/reports/<int:report_id>/status', methods=['POST'])
@require_login
@csrf_protected
def api_change_status(report_id):
    """API endpoint to change report status."""
    report = get_report_by_id(report_id)
    if not report:
        return jsonify({'success': False, 'message': 'Report not found'}), 404
    
    user_id = session.get('user_id')
    
    # Check permission
    if not (can_manage_feedback() or report.get('assigned_to') == user_id):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    data = request.get_json() or {}
    new_status = data.get('status')
    reason = data.get('reason', '')
    
    if not new_status or new_status not in STATUS_CHOICES:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400
    
    old_status = report['status']
    success = change_status(report_id, new_status, user_id, get_user_display_name(user_id), reason)
    
    if success:
        notify_status_changed(report_id, report, old_status, new_status, user_id)
        return jsonify({'success': True, 'message': f'Status changed to {new_status}'})
    
    return jsonify({'success': False, 'message': 'Failed to change status'}), 500


@feedback_bp.route('/api/reports/<int:report_id>/assign', methods=['POST'])
@require_login
@csrf_protected
def api_assign_report(report_id):
    """API endpoint to assign a report."""
    report = get_report_by_id(report_id)
    if not report:
        return jsonify({'success': False, 'message': 'Report not found'}), 404
    
    if not can_assign_feedback():
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    data = request.get_json() or {}
    assignee_id = data.get('assignee_id')
    assignee_name = data.get('assignee_name', 'Unknown')
    team = data.get('team', '')
    department = data.get('department', '')
    reason = data.get('reason', '')
    
    user_id = session.get('user_id')
    
    success = assign_report(
        report_id, assignee_id, assignee_name, team, department,
        user_id, get_user_display_name(user_id), reason
    )
    
    if success:
        # Change status to Assigned if not already
        if report['status'] in [STATUS_NEW, STATUS_SUBMITTED]:
            change_status(report_id, 'Assigned', user_id, get_user_display_name(user_id), 'Auto-assigned')
        
        if assignee_id:
            notify_report_assigned(report_id, report, assignee_id)
        
        return jsonify({'success': True, 'message': f'Report assigned to {assignee_name}'})
    
    return jsonify({'success': False, 'message': 'Failed to assign report'}), 500


@feedback_bp.route('/api/reports/<int:report_id>/comments', methods=['GET', 'POST'])
@require_login
def api_comments(report_id):
    """API endpoint to get or add comments."""
    report = get_report_by_id(report_id)
    if not report:
        return jsonify({'success': False, 'message': 'Report not found'}), 404
    
    user_id = session.get('user_id')
    
    if request.method == 'GET':
        include_internal = can_view_internal()
        comments = get_report_comments(report_id, include_internal=include_internal)
        return jsonify({
            'success': True,
            'comments': [{
                'id': c['id'],
                'content': c['content'],
                'author_name': c['author_name'],
                'is_internal': bool(c['is_internal']),
                'created_at': c['created_at'],
                'is_edited': bool(c['is_edited']),
            } for c in comments]
        })
    
    # POST - add comment
    data = request.get_json() or {}
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'success': False, 'message': 'Comment cannot be empty'}), 400
    
    is_internal = data.get('is_internal', False) and can_view_internal()
    
    comment_id = add_comment(
        report_id, content, user_id, get_user_display_name(user_id),
        is_internal=is_internal
    )
    
    return jsonify({
        'success': True,
        'message': 'Comment added',
        'comment_id': comment_id
    })


@feedback_bp.route('/api/reports/<int:report_id>/attachments', methods=['POST'])
@require_login
def api_upload_attachment(report_id):
    """API endpoint to upload an attachment."""
    report = get_report_by_id(report_id)
    if not report:
        return jsonify({'success': False, 'message': 'Report not found'}), 404
    
    user_id = session.get('user_id')
    
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    file_info = save_uploaded_file(file)
    
    if not file_info:
        return jsonify({'success': False, 'message': 'Invalid file or file too large'}), 400
    
    attachment_id = add_attachment(
        report_id, file_info, user_id, get_user_display_name(user_id)
    )
    
    return jsonify({
        'success': True,
        'message': 'File uploaded',
        'attachment_id': attachment_id,
        'file_name': file_info['file_name'],
        'file_path': file_info['file_path'],
        'file_type': file_info['file_type'],
    })


@feedback_bp.route('/api/reports/<int:report_id>/voice', methods=['POST'])
@require_login
def api_upload_voice(report_id):
    """API endpoint to upload a voice recording."""
    report = get_report_by_id(report_id)
    if not report:
        return jsonify({'success': False, 'message': 'Report not found'}), 404
    
    # Check if voice recording is enabled
    if not get_platform_setting('feedback_allow_voice', '1') == '1':
        return jsonify({'success': False, 'message': 'Voice recordings not allowed'}), 403
    
    user_id = session.get('user_id')
    
    if 'voice' not in request.files:
        return jsonify({'success': False, 'message': 'No voice file provided'}), 400
    
    voice_file = request.files['voice']
    
    if voice_file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    file_info = save_uploaded_file(voice_file, subfolder='voice')
    
    if not file_info:
        return jsonify({'success': False, 'message': 'Invalid file or file too large'}), 400
    
    file_info['file_type'] = 'audio'
    
    attachment_id = add_attachment(
        report_id, file_info, user_id, get_user_display_name(user_id)
    )
    
    return jsonify({
        'success': True,
        'message': 'Voice recording uploaded',
        'attachment_id': attachment_id,
        'file_name': file_info['file_name'],
        'file_path': file_info['file_path'],
        'file_type': 'audio',
    })


@feedback_bp.route('/api/reports/search', methods=['GET'])
@require_login
def api_search():
    """API endpoint to search reports."""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify({'success': False, 'message': 'Query too short'}), 400
    
    filters = {}
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    
    results = search_reports(query, filters=filters, limit=20)
    results = [prepare_report_for_view(r) for r in results]
    
    return jsonify({
        'success': True,
        'results': [{
            'id': r['id'],
            'reference_number': r['reference_number'],
            'title': r['title'],
            'status': r['status'],
            'priority': r['priority'],
            'report_type': r.get('report_type'),
        } for r in results]
    })


@feedback_bp.route('/api/users', methods=['GET'])
@require_login
def api_get_users():
    """API endpoint to get users for assignment."""
    if not can_assign_feedback():
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    query = request.args.get('q', '').strip()
    
    if query:
        users = get_all("""
            SELECT id, username, display_name, email
            FROM users
            WHERE (username LIKE ? OR display_name LIKE ? OR email LIKE ?)
            LIMIT 20
        """, (f'%{query}%', f'%{query}%', f'%{query}%'))
    else:
        users = get_all("""
            SELECT id, username, display_name, email
            FROM users
            LIMIT 20
        """)
    
    return jsonify({
        'success': True,
        'users': [{
            'id': u['id'],
            'username': u['username'],
            'display_name': u['display_name'] or u['username'],
            'email': u.get('email', ''),
        } for u in users]
    })


@feedback_bp.route('/api/stats', methods=['GET'])
@require_login
def api_stats():
    """API endpoint to get statistics."""
    filters = {}
    if request.args.get('date_from'):
        filters['date_from'] = request.args.get('date_from')
    if request.args.get('date_to'):
        filters['date_to'] = request.args.get('date_to')
    
    stats = get_stats(filters=filters)
    
    return jsonify({
        'success': True,
        'stats': stats
    })


# =============================================================================
# ROUTES: ATTACHMENTS
# =============================================================================

@feedback_bp.route('/attachment/<int:attachment_id>')
@require_login
def download_attachment(attachment_id):
    """Download an attachment."""
    attachment = get_one("""
        SELECT fa.*, fr.reference_number
        FROM feedback_attachments fa
        JOIN feedback_reports fr ON fa.report_id = fr.id
        WHERE fa.id = ?
    """, (attachment_id,))
    
    if not attachment:
        flash("Attachment not found.", "error")
        return redirect(url_for('feedback.reports_list'))
    
    # Check permission to view the report
    report = get_report_by_id(attachment['report_id'])
    if report.get('is_confidential') and not can_manage_feedback():
        flash("You don't have permission to download this attachment.", "error")
        return redirect(url_for('feedback.reports_list'))
    
    filepath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'static', attachment['file_path']
    )
    
    if not os.path.exists(filepath):
        flash("File not found on server.", "error")
        return redirect(url_for('feedback.report_detail', report_id=attachment['report_id']))
    
    return send_file(
        filepath,
        download_name=attachment['file_name'],
        as_attachment=True
    )


# =============================================================================
# ROUTES: DELETE REPORT
# =============================================================================

@feedback_bp.route('/report/<int:report_id>/delete', methods=['POST'])
@require_login
@csrf_protected
def delete_report(report_id):
    """Delete a report (soft delete)."""
    report = get_report_by_id(report_id)
    if not report:
        flash("Report not found.", "error")
        return redirect(url_for('feedback.reports_list'))
    
    user_id = session.get('user_id')
    
    # Only managers/admins or the reporter can delete
    if not can_delete_feedback():
        if report.get('reporter_user_id') != user_id:
            flash("You don't have permission to delete this report.", "error")
            return redirect(url_for('feedback.report_detail', report_id=report_id))
    
    delete_report(report_id, user_id, get_user_display_name(user_id))
    flash("Report deleted successfully.", "success")
    return redirect(url_for('feedback.reports_list'))


# =============================================================================
# ROUTES: EXPORT
# =============================================================================

@feedback_bp.route('/export')
@require_login
def export_reports():
    """Export reports to CSV."""
    if not can_manage_feedback():
        flash("You don't have permission to export reports.", "error")
        return redirect(url_for('feedback.dashboard'))
    
    filters = {}
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    if request.args.get('type'):
        filters['type'] = request.args.get('type')
    if request.args.get('priority'):
        filters['priority'] = request.args.get('priority')
    if request.args.get('date_from'):
        filters['date_from'] = request.args.get('date_from')
    if request.args.get('date_to'):
        filters['date_to'] = request.args.get('date_to')
    
    result = get_reports(filters=filters, page=1, per_page=10000)
    reports = result['reports']
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Reference', 'Title', 'Type', 'Status', 'Priority', 'Severity',
        'Reporter', 'Assigned To', 'Category', 'Created At', 'Updated At',
        'Resolved At', 'Description'
    ])
    
    # Data
    for r in reports:
        writer.writerow([
            r.get('reference_number', ''),
            r.get('title', ''),
            r.get('report_type', ''),
            r.get('status', ''),
            r.get('priority', ''),
            r.get('severity', ''),
            r.get('reporter_name', ''),
            r.get('assigned_to_name', ''),
            r.get('category_name', ''),
            r.get('created_at', ''),
            r.get('updated_at', ''),
            r.get('resolved_at', ''),
            (r.get('description') or '')[:500],
        ])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=feedback_export_{datetime.now().strftime("%Y%m%d")}.csv'
    
    return response


@feedback_bp.route('/export/pdf')
@require_login
def export_reports_pdf():
    """Export reports summary to PDF-friendly HTML for printing."""
    if not can_manage_feedback():
        flash("You don't have permission to export reports.", "error")
        return redirect(url_for('feedback.dashboard'))
    
    filters = {}
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    if request.args.get('type'):
        filters['type'] = request.args.get('type')
    if request.args.get('priority'):
        filters['priority'] = request.args.get('priority')
    if request.args.get('date_from'):
        filters['date_from'] = request.args.get('date_from')
    if request.args.get('date_to'):
        filters['date_to'] = request.args.get('date_to')
    
    result = get_reports(filters=filters, page=1, per_page=100)
    reports = [prepare_report_for_view(r) for r in result['reports']]
    stats = get_stats(filters=filters)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Feedback Report Export - {datetime.now().strftime('%Y-%m-%d')}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
            h1 {{ color: #1a1a1a; border-bottom: 2px solid #3b82f6; padding-bottom: 10px; }}
            .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
            .stat-box {{ background: #f1f5f9; padding: 15px; border-radius: 8px; text-align: center; flex: 1; }}
            .stat-value {{ font-size: 24px; font-weight: bold; color: #3b82f6; }}
            .stat-label {{ font-size: 12px; color: #64748b; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #e2e8f0; padding: 10px; text-align: left; }}
            th {{ background: #3b82f6; color: white; }}
            tr:nth-child(even) {{ background: #f8fafc; }}
            .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; }}
            .status-{{'New'}} {{ background: #dbeafe; color: #1d4ed8; }}
            .status-{{'In Progress'}} {{ background: #fef3c7; color: #b45309; }}
            .status-{{'Resolved'}} {{ background: #d1fae5; color: #059669; }}
            .status-{{'Closed'}} {{ background: #f1f5f9; color: #475569; }}
            .footer {{ margin-top: 30px; text-align: center; font-size: 11px; color: #94a3b8; }}
        </style>
    </head>
    <body>
        <h1>Feedback Report Summary</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-value">{stats['total']}</div>
                <div class="stat-label">Total Reports</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{stats['open']}</div>
                <div class="stat-label">Open</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{stats['resolved']}</div>
                <div class="stat-label">Resolved</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{stats.get('avg_resolution_hours', 0)}h</div>
                <div class="stat-label">Avg Resolution</div>
            </div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Reference</th>
                    <th>Title</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th>Assignee</th>
                    <th>Created</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for report in reports:
        status_class = report.get('status', '').replace(' ', '-')
        html_content += f"""
                <tr>
                    <td>{report.get('reference_number', '')}</td>
                    <td>{report.get('title', '')[:50]}</td>
                    <td><span class="badge status-{status_class}">{report.get('status', '')}</span></td>
                    <td>{report.get('priority', '')}</td>
                    <td>{report.get('assigned_to_name') or report.get('assigned_username') or 'Unassigned'}</td>
                    <td>{report.get('created_at', '')[:10] if report.get('created_at') else '-'}</td>
                </tr>
        """
    
    html_content += """
            </tbody>
        </table>
        
        <div class="footer">
            <p>WHDASH Feedback Management System - Page 1</p>
        </div>
    </body>
    </html>
    """
    
    response = make_response(html_content)
    response.headers['Content-Type'] = 'text/html'
    response.headers['Content-Disposition'] = f'attachment; filename=feedback_report_{datetime.now().strftime("%Y%m%d")}.html'
    
    return response


# =============================================================================
# ROUTES: REPORTS (REPORTING/ANALYTICS)
# =============================================================================

@feedback_bp.route('/reports/analytics')
@require_login
def reports_analytics():
    """Analytics and reporting page."""
    if not can_view_feedback():
        flash("You don't have permission to view this page.", "error")
        return redirect(url_for('feedback.dashboard'))
    
    stats = get_stats()
    
    # Trend data (last 30 days)
    from collections import Counter
    trend_data = []
    for i in range(30):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        day_stats = get_stats(filters={'date_from': date, 'date_to': date})
        trend_data.append({
            'date': date,
            'total': day_stats['total'],
            'open': day_stats['open'],
            'resolved': day_stats['resolved'],
        })
    trend_data.reverse()
    
    # Team performance data
    team_stats = get_all("""
        SELECT 
            fr.assigned_to_name as assignee_name,
            COUNT(*) as total_assigned,
            SUM(CASE WHEN fr.status IN ('Resolved', 'Verified', 'Closed') THEN 1 ELSE 0 END) as resolved_count,
            AVG(CASE 
                WHEN fr.resolved_at IS NOT NULL AND fr.created_at IS NOT NULL 
                THEN (julianday(fr.resolved_at) - julianday(fr.created_at)) * 24 
                ELSE NULL END) as avg_resolution_hours
        FROM feedback_reports fr
        WHERE fr.is_deleted = 0 AND fr.assigned_to_name IS NOT NULL
        GROUP BY fr.assigned_to_name
        ORDER BY total_assigned DESC
        LIMIT 10
    """)
    team_stats = [dict(row) for row in team_stats] if team_stats else []
    
    # SLA compliance
    sla_stats = get_all("""
        SELECT 
            COUNT(*) as total_with_sla,
            SUM(CASE WHEN sla_breached = 1 THEN 1 ELSE 0 END) as breached_count,
            SUM(CASE WHEN status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) as completed_count
        FROM feedback_reports
        WHERE is_deleted = 0 AND sla_due_date IS NOT NULL AND sla_due_date != ''
    """)
    sla_data = dict(sla_stats[0]) if sla_stats else {'total_with_sla': 0, 'breached_count': 0, 'completed_count': 0}
    
    # Category performance
    category_stats = get_all("""
        SELECT 
            fc.name as category_name,
            COUNT(fr.id) as total_count,
            AVG(CASE 
                WHEN fr.resolved_at IS NOT NULL AND fr.created_at IS NOT NULL 
                THEN (julianday(fr.resolved_at) - julianday(fr.created_at)) * 24 
                ELSE NULL END) as avg_resolution_hours
        FROM feedback_categories fc
        LEFT JOIN feedback_reports fr ON fc.id = fr.category_id AND fr.is_deleted = 0
        WHERE fc.is_active = 1
        GROUP BY fc.id, fc.name
        ORDER BY total_count DESC
    """)
    category_stats = [dict(row) for row in category_stats] if category_stats else []
    
    return render_template('feedback/reports_analytics.html',
        title='Feedback Analytics',
        stats=stats,
        trend_data=trend_data,
        team_stats=team_stats,
        sla_data=sla_data,
        category_stats=category_stats,
        can_manage=can_manage_feedback(),
        csrf_token=_csrf_token(),
    )


# =============================================================================
# INITIALIZATION
# =============================================================================

def register_feedback_routes(app):
    """Register feedback routes with the Flask app."""
    init_feedback_tables()
    app.register_blueprint(feedback_bp)
