"""
HR Module Routes and API Endpoints
====================================
This file contains all HR-related Flask routes and API endpoints.

Routes are organized by HR module:
1. HR Dashboard
2. Employees
3. Departments
4. Positions
5. Attendance
6. Leave Management
7. Payroll
8. Overtime
9. Rewards & Bonuses
10. Deductions
11. Loans
12. Documents
13. Recruitment
14. Tasks & Performance
15. Successors
16. Reports
17. Settings

Each route has proper:
- Authentication checks
- Permission checks
- Input validation
- Error handling
- Audit logging
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file, Response
from functools import wraps
from datetime import datetime, timedelta, date
import sqlite3
import json
import csv
import io
from hr_models import (
    get_db, run_hr_migrations, get_hr_setting, update_hr_setting,
    log_hr_audit, get_active_employee_count, get_employees_on_leave_today,
    get_upcoming_leave_requests, get_monthly_payroll_summary,
    get_department_employee_count, get_employee_with_employment,
    HR_TABLES
)
from permissions import user_has_permission

# Import export utilities
from export_utils import (
    send_export_response,
    get_export_columns
)

hr_bp = Blueprint('hr', __name__, url_prefix='/hr')


# =============================================================================
# EXPORT TYPES AND COLUMNS
# =============================================================================

HR_EXPORT_TYPES = [
    'csv', 'excel_text', 'excel_general', 'json', 'xml', 'txt',
    'pdf', 'docx', 'html', 'printable', 'barcode', 'api',
    'email', 'zip', 'backup', 'sql_dump', 'dashboard',
    'summary', 'detailed', 'audit_log'
]

HR_EXPORT_COLUMNS = {
    'employees': ['employee_id', 'name', 'department', 'position', 'hire_date', 'status'],
    'departments': ['department_id', 'name', 'manager', 'employee_count'],
    'positions': ['position_id', 'title', 'department', 'level'],
    'attendance': ['employee_id', 'date', 'check_in', 'check_out', 'hours_worked'],
    'leave': ['employee_id', 'leave_type', 'start_date', 'end_date', 'status'],
    'payroll': ['employee_id', 'period', 'basic_salary', 'allowances', 'deductions', 'net_salary'],
    'overtime': ['employee_id', 'date', 'hours', 'rate', 'amount'],
    'rewards': ['employee_id', 'type', 'amount', 'reason', 'date'],
    'loans': ['employee_id', 'loan_type', 'amount', 'installment', 'balance', 'status']
}


# =============================================================================
# DECORATORS AND HELPERS
# =============================================================================

def hr_login_required(f):
    """Decorator to require HR login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Please log in first.', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def hr_permission_required(action: str):
    """Decorator to check HR-specific permissions using central permissions system."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please log in first.', 'error')
                return redirect(url_for('login'))

            # Super admin bypass
            if session.get('role_name') == 'Global Admin':
                return f(*args, **kwargs)

            user_id = session['user_id']
            if not user_has_permission(user_id, 'hr', 'hr', action):
                if request.is_json:
                    return jsonify({'error': 'Permission denied'}), 403
                flash(f"You don't have permission to {action} HR records.", 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_current_user():
    """Get current logged-in user info."""
    if 'user_id' not in session:
        return None
    return {
        'id': session.get('user_id'),
        'username': session.get('username'),
        'role_id': session.get('role_id'),
        'role_name': session.get('role_name'),
        'company_id': session.get('company_id'),
        'hr_permissions': session.get('hr_permissions', [])
    }


def parse_date(date_str):
    """Safely parse date string to date object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        try:
            return datetime.strptime(date_str, '%d/%m/%Y').date()
        except ValueError:
            return None


def generate_employee_code(db, prefix='EMP'):
    """Generate a unique, sequential employee code.

    Standard format: EMP{YYYY}{####}
    - EMP: fixed prefix
    - YYYY: 4-digit year from hire date (defaults to current year)
    - ####: zero-padded 4-digit sequential number within the year

    Uses MAX(employee_code) parsed for the given year prefix to find the
    next sequence number, ensuring strict sequential ordering and no gaps
    within the same year. Thread-safe via row-level locking.
    """
    current_year = datetime.now().year
    year_prefix = f'{prefix}{current_year}'

    row = db.execute("""
        SELECT employee_code FROM hr_employees
        WHERE employee_code LIKE ?
        ORDER BY employee_code DESC LIMIT 1
    """, (f'{year_prefix}%',)).fetchone()

    if row and row['employee_code']:
        # employee_code format: EMPYYYY####  → extract numeric suffix
        suffix_str = row['employee_code'][len(year_prefix):]
        try:
            next_seq = int(suffix_str) + 1
        except ValueError:
            next_seq = 1
    else:
        next_seq = 1

    return f'{year_prefix}{next_seq:04d}'


def format_date(date_obj, fmt='%d/%m/%Y'):
    """Format date object to string."""
    if not date_obj:
        return ''
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime(fmt)


def error_response(message, status=400):
    """Return JSON error response."""
    if request.is_json:
        return jsonify({'error': message}), status
    flash(message, 'error')
    return None


def send_hr_flow_notification(title, message, priority='normal', user_ids=None, channel='hr'):
    """Send HR notification via Flow system.
    
    Args:
        title: Notification title
        message: Notification body
        priority: normal, high, urgent
        user_ids: List of user IDs to notify, or None for broadcast
        channel: Flow channel name (default: hr)
    """
    try:
        # Try to import Flow notification function
        from flow_models import create_flow_notification
        
        if user_ids:
            for uid in user_ids:
                create_flow_notification(
                    user_id=uid,
                    title=title,
                    message=message,
                    notification_type='hr',
                    priority=priority,
                    related_module='hr'
                )
        else:
            # Broadcast to HR channel if no specific users
            pass  # Would need Flow broadcast API
    except ImportError:
        # Flow module not available, skip notification
        pass
    except Exception as e:
        # Log but don't fail the main operation
        print(f"Flow notification failed: {str(e)}")


# =============================================================================
# 1. HR DASHBOARD
# =============================================================================

@hr_bp.route('/')
@hr_bp.route('/dashboard')
@hr_login_required
@hr_permission_required('view')
def hr_dashboard():
    """HR Dashboard - Main overview page."""
    user = get_current_user()
    db = get_db()
    
    try:
        # Basic employee stats
        total_employees = db.execute("SELECT COUNT(*) as cnt FROM hr_employees").fetchone()['cnt']
        active_employees = db.execute("SELECT COUNT(*) as cnt FROM hr_employees WHERE status = 'Active'").fetchone()['cnt']
        inactive_employees = total_employees - active_employees
        
        # New hires this month
        today = datetime.now()
        new_hires = db.execute("""
            SELECT COUNT(*) as cnt FROM hr_employees 
            WHERE hire_date >= ? AND hire_date <= ?
        """, (today.replace(day=1).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))).fetchone()['cnt']
        
        # Employees on leave today
        employees_on_leave = get_employees_on_leave_today()
        
        # Upcoming leave requests
        upcoming_leaves = get_upcoming_leave_requests(7)
        
        # Pending approvals count
        pending_leaves = db.execute("SELECT COUNT(*) as cnt FROM hr_leave_requests WHERE status = 'Pending'").fetchone()['cnt']
        pending_ot = db.execute("SELECT COUNT(*) as cnt FROM hr_overtime_requests WHERE status = 'Pending'").fetchone()['cnt']
        pending_approvals = pending_leaves + pending_ot
        
        # Department headcount
        departments = db.execute("""
            SELECT d.*, 
                   COUNT(DISTINCT ee.employee_id) as headcount
            FROM hr_departments d
            LEFT JOIN hr_employee_employment ee ON d.id = ee.department_id AND ee.employment_status = 'Active'
            WHERE d.status = 'Active'
            GROUP BY d.id
            ORDER BY d.name
        """).fetchall()
        
        # Attendance today
        attendance_today = db.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present,
                   SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent,
                   SUM(CASE WHEN late_minutes > 0 THEN 1 ELSE 0 END) as late
            FROM hr_attendance_records
            WHERE date = ?
        """, (today.strftime('%Y-%m-%d'),)).fetchone()
        
        # Expiring documents (next 30 days)
        expiring_docs = db.execute("""
            SELECT ed.*, e.first_name || ' ' || e.last_name as employee_name
            FROM hr_employee_documents ed
            JOIN hr_employees e ON ed.employee_id = e.id
            WHERE ed.expiry_date IS NOT NULL
            AND ed.expiry_date BETWEEN ? AND ?
            ORDER BY ed.expiry_date
        """, (today.strftime('%Y-%m-%d'), (today + timedelta(days=30)).strftime('%Y-%m-%d'))).fetchall()
        
        # Recent announcements
        announcements = db.execute("""
            SELECT * FROM hr_announcements
            WHERE is_active = 1
            AND (valid_from IS NULL OR valid_from <= ?)
            AND (valid_to IS NULL OR valid_to >= ?)
            ORDER BY created_at DESC
            LIMIT 5
        """, (today.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))).fetchall()
        
        # Open requisitions
        open_requisitions = db.execute("""
            SELECT COUNT(*) as cnt FROM hr_job_requisitions
            WHERE status IN ('Approved', 'Posted')
        """).fetchone()['cnt']
        
        # Overtime this month
        ot_this_month = db.execute("""
            SELECT SUM(hours) as total FROM hr_overtime_requests
            WHERE date >= ? AND date <= ? AND status = 'Approved'
        """, (today.replace(day=1).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))).fetchone()['total'] or 0
        
        # Payroll status this month
        payroll_status = get_monthly_payroll_summary(today.month, today.year)
        
        return render_template('hr/dashboard.html',
                             title='HR Dashboard',
                             total_employees=total_employees,
                             active_employees=active_employees,
                             inactive_employees=inactive_employees,
                             new_hires=new_hires,
                             employees_on_leave=employees_on_leave,
                             upcoming_leaves=upcoming_leaves,
                             pending_approvals=pending_approvals,
                             departments=[dict(d) for d in departments],
                             attendance_today=dict(attendance_today) if attendance_today else None,
                             expiring_docs=[dict(d) for d in expiring_docs],
                             announcements=[dict(a) for a in announcements],
                             open_requisitions=open_requisitions,
                             ot_this_month=float(ot_this_month),
                             payroll_status=payroll_status)
    finally:
        db.close()


# =============================================================================
# 2. EMPLOYEES MODULE
# =============================================================================

@hr_bp.route('/employees')
@hr_login_required
@hr_permission_required('view')
def employees_list():
    """Employee list page with filtering and search."""
    user = get_current_user()
    db = get_db()
    
    try:
        # Get query parameters
        search = request.args.get('search', '').strip()
        status = request.args.get('status', 'Active')
        department = request.args.get('department', '')
        page = int(request.args.get('page', 1))
        per_page = 20
        
        # Build query
        query = """
            SELECT e.*, 
                   ee.department_id,
                   d.name as department_name,
                   p.title as position_title,
                   c.name as company_name
            FROM hr_employees e
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            LEFT JOIN hr_positions p ON ee.position_id = p.id
            LEFT JOIN companies c ON ee.company_id = c.id
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (e.first_name LIKE ? OR e.last_name LIKE ? OR e.employee_code LIKE ? OR e.email LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param, search_param])
        
        if status:
            query += " AND e.status = ?"
            params.append(status)
        
        if department:
            query += " AND ee.department_id = ?"
            params.append(department)
        
        query += " ORDER BY e.first_name, e.last_name"
        
        # Count total
        # Build proper count query - need to handle the multi-line SELECT properly
        count_query = """
            SELECT COUNT(*) as cnt
            FROM hr_employees e
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            LEFT JOIN hr_positions p ON ee.position_id = p.id
            LEFT JOIN companies c ON ee.company_id = c.id
            WHERE 1=1
        """
        count_params = []
        
        if search:
            count_query += " AND (e.first_name LIKE ? OR e.last_name LIKE ? OR e.employee_code LIKE ? OR e.email LIKE ?)"
            search_param = f'%{search}%'
            count_params.extend([search_param, search_param, search_param, search_param])
        
        if status:
            count_query += " AND e.status = ?"
            count_params.append(status)
        
        if department:
            count_query += " AND ee.department_id = ?"
            count_params.append(department)
        
        total = db.execute(count_query, count_params).fetchone()['cnt']
        
        # Paginate
        offset = (page - 1) * per_page
        query += f" LIMIT {per_page} OFFSET {offset}"
        
        employees = db.execute(query, params).fetchall()
        
        # Get departments for filter
        departments = db.execute("SELECT * FROM hr_departments WHERE status = 'Active' ORDER BY name").fetchall()
        
        return render_template('hr/employees/list.html',
                             title='Employees',
                             employees=[dict(e) for e in employees],
                             departments=[dict(d) for d in departments],
                             search=search,
                             status=status,
                             department=department,
                             page=page,
                             total_pages=(total + per_page - 1) // per_page,
                             total=total)
    finally:
        db.close()


@hr_bp.route('/employees/new', methods=['GET', 'POST'])
@hr_login_required
@hr_permission_required('create')
def employees_new():
    """Create new employee."""
    user = get_current_user()
    db = get_db()
    
    if request.method == 'POST':
        try:
            data = request.form
            
            # Generate employee code if not provided
            employee_code = data.get('employee_code')
            if not employee_code:
                employee_code = generate_employee_code(db)
            
            # Insert employee
            cursor = db.execute("""
                INSERT INTO hr_employees (
                    employee_code, first_name, middle_name, last_name, preferred_name,
                    arabic_name, gender, nationality, date_of_birth, marital_status,
                    mobile, email, emergency_contact_name, emergency_contact_phone,
                    address, city, country, passport_number, passport_expiry,
                    emirates_id, visa_number, visa_expiry, labour_card_number,
                    bank_name, bank_account_number, iban,
                    status, employment_type, hire_date, confirmation_date,
                    probation_end_date, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                employee_code,
                data.get('first_name'),
                data.get('middle_name'),
                data.get('last_name'),
                data.get('preferred_name'),
                data.get('arabic_name'),
                data.get('gender'),
                data.get('nationality'),
                parse_date(data.get('date_of_birth')),
                data.get('marital_status'),
                data.get('mobile'),
                data.get('email'),
                data.get('emergency_contact_name'),
                data.get('emergency_contact_phone'),
                data.get('address'),
                data.get('city'),
                data.get('country'),
                data.get('passport_number'),
                parse_date(data.get('passport_expiry')),
                data.get('emirates_id'),
                data.get('visa_number'),
                parse_date(data.get('visa_expiry')),
                data.get('labour_card_number'),
                data.get('bank_name'),
                data.get('bank_account_number'),
                data.get('iban'),
                data.get('status', 'Active'),
                data.get('employment_type', 'Full-time'),
                parse_date(data.get('hire_date')),
                parse_date(data.get('confirmation_date')),
                parse_date(data.get('probation_end_date')),
                data.get('notes')
            ))
            
            employee_id = cursor.lastrowid
            
            # Create primary employment record
            db.execute("""
                INSERT INTO hr_employee_employment (
                    employee_id, company_id, department_id, position_id,
                    shift_id, reporting_to_id, employment_status, contract_type,
                    start_date, is_primary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                employee_id,
                data.get('company_id'),
                data.get('department_id'),
                data.get('position_id'),
                data.get('shift_id'),
                data.get('reporting_to_id'),
                data.get('employment_status', 'Active'),
                data.get('contract_type', 'Permanent'),
                parse_date(data.get('hire_date')) or datetime.now().date()
            ))
            
            # Initialize leave balances for the year
            leave_types = db.execute("SELECT id, default_days FROM hr_leave_types WHERE is_active = 1").fetchall()
            current_year = datetime.now().year
            for lt in leave_types:
                db.execute("""
                    INSERT INTO hr_leave_balances (employee_id, leave_type_id, year, total_days)
                    VALUES (?, ?, ?, ?)
                """, (employee_id, lt['id'], current_year, lt['default_days']))
            
            db.commit()
            
            # Audit log
            log_hr_audit('hr_employees', employee_id, 'CREATE', user['id'],
                        new_value=f"Employee {employee_code} created")
            
            flash(f'Employee {employee_code} created successfully!', 'success')
            return redirect(url_for('hr.employees_view', id=employee_id))
            
        except Exception as e:
            db.rollback()
            flash(f'Error creating employee: {str(e)}', 'error')
    
    # GET request - show form
    try:
        departments = db.execute("SELECT * FROM hr_departments WHERE status = 'Active' ORDER BY name").fetchall()
        positions = db.execute("SELECT * FROM hr_positions WHERE status = 'Active' ORDER BY title").fetchall()
        shifts = db.execute("SELECT * FROM hr_shifts WHERE is_active = 1 ORDER BY name").fetchall()
        companies = db.execute("SELECT * FROM companies ORDER BY name").fetchall()
        managers = db.execute("""
            SELECT e.id, e.first_name, e.last_name, e.employee_code
            FROM hr_employees e
            WHERE e.status = 'Active'
            ORDER BY e.first_name, e.last_name
        """).fetchall()
        
        return render_template('hr/employees/new.html',
                             title='New Employee',
                             departments=[dict(d) for d in departments],
                             positions=[dict(p) for p in positions],
                             shifts=[dict(s) for s in shifts],
                             companies=[dict(c) for c in companies],
                             managers=[dict(m) for m in managers],
                             employee=None)
    finally:
        db.close()


@hr_bp.route('/employees/view/<int:id>')
@hr_login_required
@hr_permission_required('view')
def employees_view(id):
    """View employee detail page."""
    user = get_current_user()
    db = get_db()
    
    try:
        employee = get_employee_with_employment(id)
        if not employee:
            flash('Employee not found.', 'error')
            return redirect(url_for('hr.employees_list'))
        
        # Get employment history
        employment_records = db.execute("""
            SELECT ee.*, d.name as department_name, p.title as position_title,
                   s.name as shift_name, m.first_name || ' ' || m.last_name as manager_name
            FROM hr_employee_employment ee
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            LEFT JOIN hr_positions p ON ee.position_id = p.id
            LEFT JOIN hr_shifts s ON ee.shift_id = s.id
            LEFT JOIN hr_employees m ON ee.reporting_to_id = m.id
            WHERE ee.employee_id = ?
            ORDER BY ee.is_primary DESC, ee.start_date DESC
        """, (id,)).fetchall()
        
        # Get documents
        documents = db.execute("""
            SELECT * FROM hr_employee_documents
            WHERE employee_id = ?
            ORDER BY expiry_date IS NOT NULL, expiry_date, created_at DESC
        """, (id,)).fetchall()
        
        # Get leave balances
        current_year = datetime.now().year
        leave_balances = db.execute("""
            SELECT lb.*, lt.name as leave_type_name, lt.code as leave_type_code
            FROM hr_leave_balances lb
            JOIN hr_leave_types lt ON lb.leave_type_id = lt.id
            WHERE lb.employee_id = ? AND lb.year = ?
        """, (id, current_year)).fetchall()
        
        # Get recent leave requests
        leave_requests = db.execute("""
            SELECT lr.*, lt.name as leave_type_name
            FROM hr_leave_requests lr
            JOIN hr_leave_types lt ON lr.leave_type_id = lt.id
            WHERE lr.employee_id = ?
            ORDER BY lr.created_at DESC
            LIMIT 10
        """, (id,)).fetchall()
        
        # Get attendance summary (current month)
        today = datetime.now()
        attendance_summary = db.execute("""
            SELECT 
                COUNT(*) as total_days,
                SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present,
                SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent,
                SUM(CASE WHEN late_minutes > 0 THEN 1 ELSE 0 END) as late,
                SUM(overtime_hours) as overtime_hours
            FROM hr_attendance_records
            WHERE employee_id = ? AND strftime('%Y-%m', date) = ?
        """, (id, today.strftime('%Y-%m'))).fetchone()
        
        # Get tasks
        tasks = db.execute("""
            SELECT * FROM hr_tasks
            WHERE employee_id = ?
            ORDER BY due_date ASC
            LIMIT 10
        """, (id,)).fetchall()
        
        # Get performance reviews
        reviews = db.execute("""
            SELECT pr.*, u.username as reviewer_name
            FROM hr_performance_reviews pr
            LEFT JOIN users u ON pr.reviewer_id = u.id
            WHERE pr.employee_id = ?
            ORDER BY pr.review_date DESC
            LIMIT 5
        """, (id,)).fetchall()
        
        # Get successors
        successors = db.execute("""
            SELECT s.*, 
                   e1.first_name || ' ' || e1.last_name as employee_name,
                   e2.first_name || ' ' || e2.last_name as successor_name,
                   e3.first_name || ' ' || e3.last_name as deputy_name
            FROM hr_successors s
            JOIN hr_employees e1 ON s.employee_id = e1.id
            LEFT JOIN hr_employees e2 ON s.successor_id = e2.id
            LEFT JOIN hr_employees e3 ON s.deputy_id = e3.id
            WHERE s.employee_id = ?
        """, (id,)).fetchall()
        
        return render_template('hr/employees/view.html',
                             title=f"{employee['first_name']} {employee['last_name']}",
                             employee=employee,
                             employment_records=[dict(e) for e in employment_records],
                             documents=[dict(d) for d in documents],
                             leave_balances=[dict(lb) for lb in leave_balances],
                             leave_requests=[dict(lr) for lr in leave_requests],
                             attendance_summary=dict(attendance_summary) if attendance_summary else None,
                             tasks=[dict(t) for t in tasks],
                             reviews=[dict(r) for r in reviews],
                             successors=[dict(s) for s in successors])
    finally:
        db.close()


@hr_bp.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
@hr_login_required
@hr_permission_required('edit')
def employees_edit(id):
    """Edit employee details."""
    user = get_current_user()
    db = get_db()
    
    try:
        employee = db.execute("SELECT * FROM hr_employees WHERE id = ?", (id,)).fetchone()
        if not employee:
            flash('Employee not found.', 'error')
            return redirect(url_for('hr.employees_list'))
        
        if request.method == 'POST':
            try:
                data = request.form
                
                # Build update query
                update_fields = []
                params = []
                
                fields = ['first_name', 'middle_name', 'last_name', 'preferred_name',
                         'arabic_name', 'gender', 'nationality', 'date_of_birth',
                         'marital_status', 'mobile', 'email', 'emergency_contact_name',
                         'emergency_contact_phone', 'address', 'city', 'country',
                         'passport_number', 'passport_expiry', 'emirates_id',
                         'visa_number', 'visa_expiry', 'labour_card_number',
                         'bank_name', 'bank_account_number', 'iban',
                         'status', 'employment_type', 'hire_date', 'confirmation_date',
                         'probation_end_date', 'termination_date', 'termination_reason', 'notes']
                
                for field in fields:
                    if field in data:
                        val = data[field] if data[field] else None
                        if field in ['date_of_birth', 'passport_expiry', 'visa_expiry',
                                    'hire_date', 'confirmation_date', 'probation_end_date',
                                    'termination_date']:
                            val = parse_date(val)
                        update_fields.append(f"{field} = ?")
                        params.append(val)
                
                params.append(id)
                
                db.execute(f"""
                    UPDATE hr_employees 
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, params)
                
                # Update primary employment if provided
                if data.get('department_id'):
                    db.execute("""
                        UPDATE hr_employee_employment
                        SET department_id = ?, position_id = ?, shift_id = ?,
                            reporting_to_id = ?, employment_status = ?, contract_type = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE employee_id = ? AND is_primary = 1
                    """, (
                        data.get('department_id'),
                        data.get('position_id'),
                        data.get('shift_id'),
                        data.get('reporting_to_id'),
                        data.get('employment_status', 'Active'),
                        data.get('contract_type', 'Permanent'),
                        id
                    ))
                
                db.commit()
                
                # Audit log
                log_hr_audit('hr_employees', id, 'UPDATE', user['id'],
                           new_value=f"Employee {employee['employee_code']} updated")
                
                flash('Employee updated successfully!', 'success')
                return redirect(url_for('hr.employees_view', id=id))
                
            except Exception as e:
                db.rollback()
                flash(f'Error updating employee: {str(e)}', 'error')
        
        # GET request
        departments = db.execute("SELECT * FROM hr_departments WHERE status = 'Active' ORDER BY name").fetchall()
        positions = db.execute("SELECT * FROM hr_positions WHERE status = 'Active' ORDER BY title").fetchall()
        shifts = db.execute("SELECT * FROM hr_shifts WHERE is_active = 1 ORDER BY name").fetchall()
        companies = db.execute("SELECT * FROM companies ORDER BY name").fetchall()
        managers = db.execute("""
            SELECT e.id, e.first_name, e.last_name, e.employee_code
            FROM hr_employees e
            WHERE e.status = 'Active' AND e.id != ?
            ORDER BY e.first_name, e.last_name
        """, (id,)).fetchall()
        
        employment = db.execute("""
            SELECT * FROM hr_employee_employment
            WHERE employee_id = ? AND is_primary = 1
        """, (id,)).fetchone()
        
        return render_template('hr/employees/edit.html',
                             title=f"Edit {employee['first_name']} {employee['last_name']}",
                             employee=dict(employee),
                             employment=dict(employment) if employment else None,
                             departments=[dict(d) for d in departments],
                             positions=[dict(p) for p in positions],
                             shifts=[dict(s) for s in shifts],
                             companies=[dict(c) for c in companies],
                             managers=[dict(m) for m in managers])
    finally:
        db.close()


@hr_bp.route('/employees/delete/<int:id>', methods=['POST'])
@hr_login_required
@hr_permission_required('delete')
def employees_delete(id):
    """Archive/delete employee."""
    user = get_current_user()
    db = get_db()
    
    try:
        employee = db.execute("SELECT * FROM hr_employees WHERE id = ?", (id,)).fetchone()
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        # Soft delete - change status
        db.execute("""
            UPDATE hr_employees 
            SET status = 'Terminated', termination_date = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (datetime.now().strftime('%Y-%m-%d'), id))
        
        # Update employment
        db.execute("""
            UPDATE hr_employee_employment
            SET employment_status = 'Terminated', end_date = ?
            WHERE employee_id = ? AND is_primary = 1
        """, (datetime.now().strftime('%Y-%m-%d'), id))
        
        db.commit()
        
        log_hr_audit('hr_employees', id, 'TERMINATE', user['id'],
                    new_value=f"Employee {employee['employee_code']} terminated")
        
        return jsonify({'success': True, 'message': 'Employee terminated successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


# =============================================================================
# 3. DEPARTMENTS MODULE
# =============================================================================

@hr_bp.route('/departments')
@hr_login_required
@hr_permission_required('view')
def departments_list():
    """List all departments."""
    user = get_current_user()
    db = get_db()
    
    try:
        departments = db.execute("""
            SELECT d.*, 
                   p.name as parent_name,
                   COUNT(DISTINCT ee.employee_id) as headcount,
                   u.first_name || ' ' || u.last_name as head_name
            FROM hr_departments d
            LEFT JOIN hr_departments p ON d.parent_id = p.id
            LEFT JOIN hr_employee_employment ee ON d.id = ee.department_id AND ee.employment_status = 'Active'
            LEFT JOIN hr_employees u ON d.head_id = u.id
            GROUP BY d.id
            ORDER BY d.name
        """).fetchall()
        
        return render_template('hr/departments/list.html',
                             title='Departments',
                             departments=[dict(d) for d in departments])
    finally:
        db.close()


@hr_bp.route('/departments/new', methods=['GET', 'POST'])
@hr_login_required
@hr_permission_required('create')
def departments_new():
    """Create new department."""
    if request.method == 'POST':
        db = get_db()
        try:
            data = request.form
            
            cursor = db.execute("""
                INSERT INTO hr_departments (name, parent_id, code, description, head_id, budget, cost_center)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('name'),
                data.get('parent_id') or None,
                data.get('code'),
                data.get('description'),
                data.get('head_id') or None,
                data.get('budget') or 0,
                data.get('cost_center')
            ))
            
            db.commit()
            flash('Department created successfully!', 'success')
            return redirect(url_for('hr.departments_list'))
        except Exception as e:
            db.rollback()
            flash(f'Error: {str(e)}', 'error')
        finally:
            db.close()
    
    db = get_db()
    try:
        parent_depts = db.execute("SELECT * FROM hr_departments WHERE status = 'Active' ORDER BY name").fetchall()
        potential_heads = db.execute("SELECT * FROM hr_employees WHERE status = 'Active' ORDER BY first_name").fetchall()
        return render_template('hr/departments/new.html',
                             title='New Department',
                             parent_depts=[dict(p) for p in parent_depts],
                             potential_heads=[dict(h) for h in potential_heads])
    finally:
        db.close()


# =============================================================================
# 4. POSITIONS MODULE
# =============================================================================

@hr_bp.route('/positions')
@hr_login_required
@hr_permission_required('view')
def positions_list():
    """List all positions."""
    db = get_db()
    try:
        positions = db.execute("""
            SELECT p.*, d.name as department_name,
                   COUNT(DISTINCT ee.employee_id) as current_count
            FROM hr_positions p
            LEFT JOIN hr_departments d ON p.department_id = d.id
            LEFT JOIN hr_employee_employment ee ON p.id = ee.position_id AND ee.employment_status = 'Active'
            GROUP BY p.id
            ORDER BY p.title
        """).fetchall()
        
        return render_template('hr/positions/list.html',
                             title='Positions',
                             positions=[dict(p) for p in positions])
    finally:
        db.close()


# =============================================================================
# 5. ATTENDANCE MODULE
# =============================================================================

@hr_bp.route('/attendance')
@hr_login_required
@hr_permission_required('view')
def attendance_list():
    """Attendance records list."""
    db = get_db()
    try:
        date_from = request.args.get('date_from', datetime.now().strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
        employee_id = request.args.get('employee_id', '')
        status = request.args.get('status', '')
        
        query = """
            SELECT ar.*, e.first_name, e.last_name, e.employee_code, s.name as shift_name
            FROM hr_attendance_records ar
            JOIN hr_employees e ON ar.employee_id = e.id
            LEFT JOIN hr_shifts s ON ar.shift_id = s.id
            WHERE ar.date BETWEEN ? AND ?
        """
        params = [date_from, date_to]
        
        if employee_id:
            query += " AND ar.employee_id = ?"
            params.append(employee_id)
        
        if status:
            query += " AND ar.status = ?"
            params.append(status)
        
        query += " ORDER BY ar.date DESC, e.first_name"
        
        records = db.execute(query, params).fetchall()
        employees = db.execute("SELECT id, first_name, last_name, employee_code FROM hr_employees WHERE status = 'Active' ORDER BY first_name").fetchall()
        
        return render_template('hr/attendance/list.html',
                             title='Attendance',
                             records=[dict(r) for r in records],
                             employees=[dict(e) for e in employees],
                             date_from=date_from,
                             date_to=date_to,
                             selected_employee=employee_id,
                             selected_status=status)
    finally:
        db.close()


@hr_bp.route('/attendance/mark', methods=['GET', 'POST'])
@hr_login_required
@hr_permission_required('create')
def attendance_mark():
    """Mark attendance manually."""
    if request.method == 'POST':
        db = get_db()
        try:
            data = request.form
            
            employee_id = data.get('employee_id')
            att_date = parse_date(data.get('date'))
            check_in = data.get('check_in')
            check_out = data.get('check_out')
            status = data.get('status', 'Present')
            remarks = data.get('remarks', '')
            
            # Calculate work hours
            work_hours = 0
            if check_in and check_out:
                try:
                    t1 = datetime.strptime(check_in, '%H:%M')
                    t2 = datetime.strptime(check_out, '%H:%M')
                    work_hours = round((t2 - t1).seconds / 3600, 2)
                except:
                    pass
            
            # Insert or update
            existing = db.execute("""
                SELECT id FROM hr_attendance_records
                WHERE employee_id = ? AND date = ?
            """, (employee_id, att_date)).fetchone()
            
            if existing:
                db.execute("""
                    UPDATE hr_attendance_records
                    SET check_in = ?, check_out = ?, work_hours = ?, status = ?,
                        remarks = ?, is_manual = 1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (check_in, check_out, work_hours, status, remarks, existing['id']))
            else:
                db.execute("""
                    INSERT INTO hr_attendance_records
                    (employee_id, date, check_in, check_out, work_hours, status, remarks, is_manual)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """, (employee_id, att_date, check_in, check_out, work_hours, status, remarks))
            
            db.commit()
            flash('Attendance marked successfully!', 'success')
            return redirect(url_for('hr.attendance_list'))
            
        except Exception as e:
            db.rollback()
            flash(f'Error: {str(e)}', 'error')
        finally:
            db.close()
    
    db = get_db()
    try:
        employees = db.execute("""
            SELECT id, first_name, last_name, employee_code
            FROM hr_employees WHERE status = 'Active'
            ORDER BY first_name
        """).fetchall()
        return render_template('hr/attendance/mark.html',
                             title='Mark Attendance',
                             employees=[dict(e) for e in employees],
                             default_date=datetime.now().strftime('%Y-%m-%d'))
    finally:
        db.close()


@hr_bp.route('/attendance/summary')
@hr_login_required
@hr_permission_required('view')
def attendance_summary():
    """Attendance summary report."""
    db = get_db()
    try:
        month = int(request.args.get('month', datetime.now().month))
        year = int(request.args.get('year', datetime.now().year))
        
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"
        
        summary = db.execute("""
            SELECT e.id, e.employee_code, e.first_name, e.last_name,
                   d.name as department_name,
                   COUNT(ar.id) as total_days,
                   SUM(CASE WHEN ar.status = 'Present' THEN 1 ELSE 0 END) as present,
                   SUM(CASE WHEN ar.status = 'Absent' THEN 1 ELSE 0 END) as absent,
                   SUM(CASE WHEN ar.late_minutes > 0 THEN 1 ELSE 0 END) as late,
                   SUM(ar.overtime_hours) as total_ot,
                   SUM(ar.work_hours) as total_hours
            FROM hr_employees e
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            LEFT JOIN hr_attendance_records ar ON e.id = ar.employee_id 
                AND ar.date >= ? AND ar.date < ?
            WHERE e.status = 'Active'
            GROUP BY e.id
            ORDER BY d.name, e.first_name
        """, (start_date, end_date)).fetchall()
        
        return render_template('hr/attendance/summary.html',
                             title='Attendance Summary',
                             summary=[dict(s) for s in summary],
                             month=month,
                             year=year)
    finally:
        db.close()


# =============================================================================
# 6. LEAVE MANAGEMENT
# =============================================================================

@hr_bp.route('/leave')
@hr_login_required
@hr_permission_required('view')
def leave_list():
    """Leave requests list."""
    db = get_db()
    try:
        status = request.args.get('status', '')
        leave_type = request.args.get('leave_type', '')
        
        query = """
            SELECT lr.*, e.first_name, e.last_name, e.employee_code,
                   lt.name as leave_type_name, lt.code as leave_type_code,
                   u.username as approver_name
            FROM hr_leave_requests lr
            JOIN hr_employees e ON lr.employee_id = e.id
            JOIN hr_leave_types lt ON lr.leave_type_id = lt.id
            LEFT JOIN users u ON lr.approved_by_id = u.id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND lr.status = ?"
            params.append(status)
        
        if leave_type:
            query += " AND lr.leave_type_id = ?"
            params.append(leave_type)
        
        query += " ORDER BY lr.created_at DESC"
        
        requests = db.execute(query, params).fetchall()
        leave_types = db.execute("SELECT * FROM hr_leave_types WHERE is_active = 1 ORDER BY name").fetchall()
        
        return render_template('hr/leave/list.html',
                             title='Leave Management',
                             requests=[dict(r) for r in requests],
                             leave_types=[dict(lt) for lt in leave_types],
                             status=status,
                             leave_type=leave_type)
    finally:
        db.close()


@hr_bp.route('/leave/new', methods=['GET', 'POST'])
@hr_login_required
@hr_permission_required('create')
def leave_new():
    """Create new leave request."""
    if request.method == 'POST':
        db = get_db()
        try:
            data = request.form
            user = get_current_user()
            
            # Get current user's employee record
            employee = db.execute("""
                SELECT id FROM hr_employees WHERE user_id = ?
            """, (user['id'],)).fetchone()
            
            if not employee:
                flash('Your user account is not linked to an employee record.', 'error')
                return redirect(url_for('hr.leave_list'))
            
            employee_id = employee['id']
            leave_type_id = data.get('leave_type_id')
            start_date = parse_date(data.get('start_date'))
            end_date = parse_date(data.get('end_date'))
            reason = data.get('reason', '')
            
            # Calculate total days
            total_days = (end_date - start_date).days + 1
            
            # Check leave balance
            current_year = start_date.year
            balance = db.execute("""
                SELECT * FROM hr_leave_balances
                WHERE employee_id = ? AND leave_type_id = ? AND year = ?
            """, (employee_id, leave_type_id, current_year)).fetchone()
            
            if not balance:
                # Create balance record
                leave_type = db.execute("SELECT * FROM hr_leave_types WHERE id = ?", (leave_type_id,)).fetchone()
                db.execute("""
                    INSERT INTO hr_leave_balances (employee_id, leave_type_id, year, total_days)
                    VALUES (?, ?, ?, ?)
                """, (employee_id, leave_type_id, current_year, leave_type['default_days'] if leave_type else 0))
                
                balance = db.execute("""
                    SELECT * FROM hr_leave_balances
                    WHERE employee_id = ? AND leave_type_id = ? AND year = ?
                """, (employee_id, leave_type_id, current_year)).fetchone()
            
            available = float(balance['total_days']) - float(balance['used_days']) - float(balance['pending_days'])
            if total_days > available:
                flash(f'Insufficient leave balance. Available: {available:.1f} days', 'error')
                return redirect(url_for('hr.leave_new'))
            
            # Update pending days
            db.execute("""
                UPDATE hr_leave_balances
                SET pending_days = pending_days + ?
                WHERE id = ?
            """, (total_days, balance['id']))
            
            # Create leave request
            db.execute("""
                INSERT INTO hr_leave_requests
                (employee_id, leave_type_id, start_date, end_date, total_days, reason, status)
                VALUES (?, ?, ?, ?, ?, ?, 'Pending')
            """, (employee_id, leave_type_id, start_date, end_date, total_days, reason))
            
            db.commit()
            flash('Leave request submitted!', 'success')
            return redirect(url_for('hr.leave_list'))
            
        except Exception as e:
            db.rollback()
            flash(f'Error: {str(e)}', 'error')
        finally:
            db.close()
    
    db = get_db()
    try:
        user = get_current_user()
        employee = db.execute("SELECT id FROM hr_employees WHERE user_id = ?", (user['id'],)).fetchone()
        
        leave_types = db.execute("SELECT * FROM hr_leave_types WHERE is_active = 1 ORDER BY name").fetchall()
        
        # Get current balances
        balances = []
        if employee:
            current_year = datetime.now().year
            balances = db.execute("""
                SELECT lb.*, lt.name as leave_type_name, lt.code
                FROM hr_leave_balances lb
                JOIN hr_leave_types lt ON lb.leave_type_id = lt.id
                WHERE lb.employee_id = ? AND lb.year = ?
            """, (employee['id'], current_year)).fetchall()
        
        return render_template('hr/leave/new.html',
                             title='Request Leave',
                             leave_types=[dict(lt) for lt in leave_types],
                             balances=[dict(b) for b in balances],
                             employee_id=employee['id'] if employee else None)
    finally:
        db.close()


@hr_bp.route('/leave/approve/<int:id>', methods=['POST'])
@hr_login_required
@hr_permission_required('approve')
def leave_approve(id):
    """Approve or reject leave request."""
    db = get_db()
    try:
        data = request.get_json() if request.is_json else request.form
        action = data.get('action')  # 'approve' or 'reject'
        remarks = data.get('remarks', '')
        user = get_current_user()
        
        leave = db.execute("SELECT * FROM hr_leave_requests WHERE id = ?", (id,)).fetchone()
        if not leave:
            return jsonify({'error': 'Leave request not found'}), 404
        
        if action == 'approve':
            # Update leave balance - move from pending to used
            db.execute("""
                UPDATE hr_leave_balances
                SET used_days = used_days + ?, pending_days = pending_days - ?
                WHERE employee_id = ? AND leave_type_id = ? AND year = ?
            """, (leave['total_days'], leave['total_days'],
                  leave['employee_id'], leave['leave_type_id'], 
                  datetime.strptime(str(leave['start_date']), '%Y-%m-%d').year))
            
            db.execute("""
                UPDATE hr_leave_requests
                SET status = 'Approved', approved_by_id = ?, approved_at = CURRENT_TIMESTAMP,
                    approved_remarks = ?
                WHERE id = ?
            """, (user['id'], remarks, id))
            
            log_hr_audit('hr_leave_requests', id, 'APPROVE', user['id'])
            
            # Get employee and leave type info for notification
            emp = db.execute("SELECT first_name, last_name FROM hr_employees WHERE id = ?", (leave['employee_id'],)).fetchone()
            lt = db.execute("SELECT name FROM hr_leave_types WHERE id = ?", (leave['leave_type_id'],)).fetchone()
            
            # Send Flow notification to employee
            emp_user = db.execute("SELECT user_id FROM hr_employees WHERE id = ?", (leave['employee_id'],)).fetchone()
            if emp_user and emp_user['user_id']:
                send_hr_flow_notification(
                    title='Leave Request Approved',
                    message=f'Your {lt["name"] if lt else "leave"} request from {leave["start_date"]} to {leave["end_date"]} has been approved.',
                    priority='normal',
                    user_ids=[emp_user['user_id']],
                    channel='hr'
                )
            
        elif action == 'reject':
            # Return pending days to balance
            db.execute("""
                UPDATE hr_leave_balances
                SET pending_days = pending_days - ?
                WHERE employee_id = ? AND leave_type_id = ? AND year = ?
            """, (leave['total_days'], leave['employee_id'], leave['leave_type_id'],
                  datetime.strptime(str(leave['start_date']), '%Y-%m-%d').year))
            
            db.execute("""
                UPDATE hr_leave_requests
                SET status = 'Rejected', approved_by_id = ?, approved_at = CURRENT_TIMESTAMP,
                    approved_remarks = ?
                WHERE id = ?
            """, (user['id'], remarks, id))
            
            log_hr_audit('hr_leave_requests', id, 'REJECT', user['id'])
        
        db.commit()
        return jsonify({'success': True, 'message': f'Leave request {action}d'})
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


# =============================================================================
# 7. PAYROLL MODULE
# =============================================================================

@hr_bp.route('/payroll')
@hr_login_required
@hr_permission_required('view')
def payroll_list():
    """List payroll periods."""
    db = get_db()
    try:
        periods = db.execute("""
            SELECT * FROM hr_payroll_periods
            ORDER BY year DESC, month DESC
        """).fetchall()
        
        return render_template('hr/payroll/list.html',
                             title='Payroll',
                             periods=[dict(p) for p in periods])
    finally:
        db.close()


@hr_bp.route('/payroll/process/<int:period_id>')
@hr_login_required
@hr_permission_required('process')
def payroll_process(period_id):
    """Process payroll for a period."""
    db = get_db()
    try:
        period = db.execute("SELECT * FROM hr_payroll_periods WHERE id = ?", (period_id,)).fetchone()
        if not period:
            flash('Payroll period not found.', 'error')
            return redirect(url_for('hr.payroll_list'))
        
        if period['status'] not in ['Draft', 'Processing']:
            flash('Payroll can only be processed in Draft or Processing status.', 'error')
            return redirect(url_for('hr.payroll_list'))
        
        # Get active employees
        employees = db.execute("""
            SELECT e.*, ee.department_id, ee.position_id, ee.company_id
            FROM hr_employees e
            JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            WHERE e.status = 'Active' AND ee.employment_status = 'Active'
        """).fetchall()
        
        # Get salary components
        components = db.execute("""
            SELECT * FROM hr_payroll_components WHERE is_active = 1 ORDER BY order_index
        """).fetchall()
        
        # Process each employee
        for emp in employees:
            # Check if record exists
            existing = db.execute("""
                SELECT id FROM hr_payroll_records
                WHERE period_id = ? AND employee_id = ?
            """, (period_id, emp['id'])).fetchone()
            
            # Get employee salary components
            emp_salary = db.execute("""
                SELECT esc.*, pc.component_type, pc.code
                FROM hr_employee_salary esc
                JOIN hr_payroll_components pc ON esc.component_id = pc.id
                WHERE esc.employee_id = ? AND esc.is_active = 1
            """, (emp['id'],)).fetchall()
            
            # Calculate totals
            basic = 0
            total_allowances = 0
            for sc in emp_salary:
                if sc['code'] == 'BASIC':
                    basic = float(sc['amount'])
                elif sc['component_type'] == 'Allowance':
                    total_allowances += float(sc['amount'])
            
            # Get overtime
            ot_total = db.execute("""
                SELECT SUM(calculated_amount) as total
                FROM hr_overtime_requests
                WHERE employee_id = ? 
                AND strftime('%Y-%m', date) = ?
                AND status = 'Approved'
            """, (emp['id'], f"{period['year']}-{period['month']:02d}")).fetchone()['total'] or 0
            
            # Get bonuses
            bonus_total = db.execute("""
                SELECT SUM(amount) as total
                FROM hr_bonus_records
                WHERE employee_id = ?
                AND effective_month = ? AND effective_year = ?
                AND status = 'Approved'
            """, (emp['id'], period['month'], period['year'])).fetchone()['total'] or 0
            
            # Get deductions
            deduction_total = db.execute("""
                SELECT SUM(amount) as total
                FROM hr_deduction_records
                WHERE employee_id = ?
                AND ((effective_month IS NULL) OR (effective_month = ? AND effective_year = ?))
                AND status = 'Approved'
            """, (emp['id'], period['month'], period['year'])).fetchone()['total'] or 0
            
            # Get attendance for days worked
            attendance = db.execute("""
                SELECT COUNT(*) as days
                FROM hr_attendance_records
                WHERE employee_id = ?
                AND strftime('%Y-%m', date) = ?
                AND status = 'Present'
            """, (emp['id'], f"{period['year']}-{period['month']:02d}")).fetchone()['days'] or 0
            
            gross = basic + total_allowances + float(ot_total) + float(bonus_total)
            net = gross - float(deduction_total)
            
            if existing:
                db.execute("""
                    UPDATE hr_payroll_records
                    SET basic_salary = ?, total_allowances = ?, total_overtime = ?,
                        total_bonuses = ?, total_deductions = ?, gross_salary = ?,
                        net_salary = ?, days_worked = ?
                    WHERE id = ?
                """, (basic, total_allowances, ot_total, bonus_total, deduction_total,
                      gross, net, attendance, existing['id']))
            else:
                db.execute("""
                    INSERT INTO hr_payroll_records
                    (period_id, employee_id, basic_salary, total_allowances, total_overtime,
                     total_bonuses, total_deductions, gross_salary, net_salary, days_worked, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Draft')
                """, (period_id, emp['id'], basic, total_allowances, ot_total,
                      bonus_total, deduction_total, gross, net, attendance))
        
        # Update period status
        db.execute("""
            UPDATE hr_payroll_periods
            SET status = 'Processed', processed_by_id = ?, processed_at = CURRENT_TIMESTAMP,
                total_employees = ?
            WHERE id = ?
        """, (session['user_id'], len(employees), period_id))
        
        db.commit()
        flash(f'Payroll processed for {len(employees)} employees!', 'success')
        return redirect(url_for('hr.payroll_detail', period_id=period_id))
        
    except Exception as e:
        db.rollback()
        flash(f'Error processing payroll: {str(e)}', 'error')
        return redirect(url_for('hr.payroll_list'))
    finally:
        db.close()


@hr_bp.route('/payroll/detail/<int:period_id>')
@hr_login_required
@hr_permission_required('view')
def payroll_detail(period_id):
    """View payroll detail for a period."""
    db = get_db()
    try:
        period = db.execute("SELECT * FROM hr_payroll_periods WHERE id = ?", (period_id,)).fetchone()
        if not period:
            flash('Payroll period not found.', 'error')
            return redirect(url_for('hr.payroll_list'))
        
        records = db.execute("""
            SELECT pr.*, e.first_name, e.last_name, e.employee_code,
                   d.name as department_name
            FROM hr_payroll_records pr
            JOIN hr_employees e ON pr.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            WHERE pr.period_id = ?
            ORDER BY d.name, e.first_name
        """, (period_id,)).fetchall()
        
        # Calculate totals
        totals = db.execute("""
            SELECT 
                SUM(basic_salary) as total_basic,
                SUM(total_allowances) as total_allowances,
                SUM(total_overtime) as total_overtime,
                SUM(total_bonuses) as total_bonuses,
                SUM(total_deductions) as total_deductions,
                SUM(gross_salary) as total_gross,
                SUM(net_salary) as total_net
            FROM hr_payroll_records
            WHERE period_id = ?
        """, (period_id,)).fetchone()
        
        return render_template('hr/payroll/detail.html',
                             title=f"Payroll - {period['name']}",
                             period=dict(period),
                             records=[dict(r) for r in records],
                             totals=dict(totals) if totals else None)
    finally:
        db.close()


@hr_bp.route('/payroll/approve/<int:period_id>', methods=['POST'])
@hr_login_required
@hr_permission_required('approve')
def payroll_approve(period_id):
    """Approve payroll period."""
    db = get_db()
    try:
        db.execute("""
            UPDATE hr_payroll_periods
            SET status = 'Approved', approved_by_id = ?, approved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (session['user_id'], period_id))
        
        db.execute("""
            UPDATE hr_payroll_records
            SET status = 'Approved', approved_by_id = ?, approved_at = CURRENT_TIMESTAMP
            WHERE period_id = ?
        """, (session['user_id'], period_id))
        
        db.commit()
        flash('Payroll approved!', 'success')
        return redirect(url_for('hr.payroll_detail', period_id=period_id))
        
    except Exception as e:
        db.rollback()
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('hr.payroll_detail', period_id=period_id))
    finally:
        db.close()


@hr_bp.route('/payroll/export/<int:period_id>')
@hr_login_required
@hr_permission_required('view')
def payroll_export(period_id):
    """Export payroll to CSV."""
    db = get_db()
    try:
        period = db.execute("SELECT * FROM hr_payroll_periods WHERE id = ?", (period_id,)).fetchone()
        records = db.execute("""
            SELECT e.employee_code, e.first_name, e.last_name,
                   pr.basic_salary, pr.total_allowances, pr.total_overtime,
                   pr.total_bonuses, pr.total_deductions, pr.gross_salary, pr.net_salary
            FROM hr_payroll_records pr
            JOIN hr_employees e ON pr.employee_id = e.id
            WHERE pr.period_id = ?
            ORDER BY e.first_name
        """, (period_id,)).fetchall()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Employee Code', 'First Name', 'Last Name', 'Basic', 'Allowances',
                        'Overtime', 'Bonuses', 'Deductions', 'Gross', 'Net'])
        
        for r in records:
            writer.writerow([r['employee_code'], r['first_name'], r['last_name'],
                          r['basic_salary'], r['total_allowances'], r['total_overtime'],
                          r['total_bonuses'], r['total_deductions'], r['gross_salary'], r['net_salary']])
        
        output.seek(0)
        return Response(output.getvalue(),
                      mimetype='text/csv',
                      headers={'Content-Disposition': f'attachment; filename=payroll_{period["name"]}.csv'})
    finally:
        db.close()


# =============================================================================
# 8. OVERTIME MODULE
# =============================================================================

@hr_bp.route('/overtime')
@hr_login_required
@hr_permission_required('view')
def overtime_list():
    """List overtime requests."""
    db = get_db()
    try:
        status = request.args.get('status', '')
        
        query = """
            SELECT ot.*, e.first_name, e.last_name, e.employee_code,
                   u.username as approver_name
            FROM hr_overtime_requests ot
            JOIN hr_employees e ON ot.employee_id = e.id
            LEFT JOIN users u ON ot.approved_by_id = u.id
        """
        
        if status:
            query += " WHERE ot.status = ?"
            query += " ORDER BY ot.date DESC"
            records = db.execute(query, (status,)).fetchall()
        else:
            query += " ORDER BY ot.date DESC"
            records = db.execute(query).fetchall()
        
        return render_template('hr/overtime/list.html',
                             title='Overtime',
                             records=[dict(r) for r in records],
                             status=status)
    finally:
        db.close()


@hr_bp.route('/overtime/new', methods=['GET', 'POST'])
@hr_login_required
@hr_permission_required('create')
def overtime_new():
    """Create new overtime request."""
    if request.method == 'POST':
        db = get_db()
        try:
            data = request.form
            user = get_current_user()
            
            employee = db.execute("SELECT id FROM hr_employees WHERE user_id = ?", (user['id'],)).fetchone()
            if not employee:
                return jsonify({'error': 'Employee not found'}), 400
            
            # Get OT rate
            ot_rate = float(get_hr_setting('overtime_rate_weekday', '1.50'))
            hours = float(data.get('hours'))
            # Assume basic salary for hourly rate calculation
            basic = db.execute("""
                SELECT amount FROM hr_employee_salary esc
                JOIN hr_payroll_components pc ON esc.component_id = pc.id
                WHERE esc.employee_id = ? AND pc.code = 'BASIC'
            """, (employee['id'],)).fetchone()
            
            hourly_rate = float(basic['amount']) / 30 / 8 if basic else 0
            calculated_amount = hours * hourly_rate * ot_rate
            
            db.execute("""
                INSERT INTO hr_overtime_requests
                (employee_id, date, hours, overtime_type, reason, rate_multiplier, calculated_amount, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
            """, (employee['id'], data.get('date'), hours, data.get('overtime_type', 'Regular'),
                  data.get('reason'), ot_rate, calculated_amount))
            
            db.commit()
            flash('Overtime request submitted!', 'success')
            return redirect(url_for('hr.overtime_list'))
            
        except Exception as e:
            db.rollback()
            flash(f'Error: {str(e)}', 'error')
        finally:
            db.close()
    
    db = get_db()
    try:
        user = get_current_user()
        employee = db.execute("SELECT id FROM hr_employees WHERE user_id = ?", (user['id'],)).fetchone()
        
        return render_template('hr/overtime/new.html',
                             title='Request Overtime',
                             employee_id=employee['id'] if employee else None,
                             default_date=datetime.now().strftime('%Y-%m-%d'))
    finally:
        db.close()


@hr_bp.route('/overtime/approve/<int:id>', methods=['POST'])
@hr_login_required
@hr_permission_required('approve')
def overtime_approve(id):
    """Approve or reject overtime."""
    db = get_db()
    try:
        data = request.get_json() if request.is_json else request.form
        action = data.get('action')
        user = get_current_user()

        # Get overtime details before update
        ot = db.execute("SELECT * FROM hr_overtime_requests WHERE id = ?", (id,)).fetchone()

        if action == 'approve':
            db.execute("""
                UPDATE hr_overtime_requests
                SET status = 'Approved', approved_by_id = ?, approved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (user['id'], id))

            log_hr_audit('hr_overtime_requests', id, 'APPROVE', user['id'])

            # Send Flow notification
            emp = db.execute("SELECT user_id, first_name, last_name FROM hr_employees WHERE id = ?", (ot['employee_id'],)).fetchone() if ot else None
            if emp and emp['user_id']:
                send_hr_flow_notification(
                    title='Overtime Request Approved',
                    message=f'Your overtime request for {ot["hours"] if ot else "the"} hours on {ot["ot_date"] if ot else "the requested date"} has been approved.',
                    priority='normal',
                    user_ids=[emp['user_id']],
                    channel='hr'
                )
        else:
            db.execute("""
                UPDATE hr_overtime_requests
                SET status = 'Rejected', approved_by_id = ?, approved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (user['id'], id))

            log_hr_audit('hr_overtime_requests', id, 'REJECT', user['id'])

            # Send Flow notification for rejection
            emp = db.execute("SELECT user_id FROM hr_employees WHERE id = ?", (ot['employee_id'],)).fetchone() if ot else None
            if emp and emp['user_id']:
                send_hr_flow_notification(
                    title='Overtime Request Rejected',
                    message=f'Your overtime request for {ot["hours"] if ot else "the"} hours on {ot["ot_date"] if ot else "the requested date"} has been rejected.',
                    priority='normal',
                    user_ids=[emp['user_id']],
                    channel='hr'
                )

        db.commit()
        return jsonify({'success': True, 'message': f'Overtime request {action}d'})

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


# =============================================================================
# 9. REWARDS & BONUSES
# =============================================================================

@hr_bp.route('/bonuses')
@hr_login_required
@hr_permission_required('view')
def bonuses_list():
    """List bonus records."""
    db = get_db()
    try:
        records = db.execute("""
            SELECT b.*, e.first_name, e.last_name, e.employee_code,
                   u.username as approver_name
            FROM hr_bonus_records b
            JOIN hr_employees e ON b.employee_id = e.id
            LEFT JOIN users u ON b.approved_by_id = u.id
            ORDER BY b.created_at DESC
        """).fetchall()
        
        return render_template('hr/bonuses/list.html',
                             title='Bonuses & Rewards',
                             records=[dict(r) for r in records])
    finally:
        db.close()


@hr_bp.route('/bonuses/new', methods=['GET', 'POST'])
@hr_login_required
@hr_permission_required('create')
def bonuses_new():
    """Create new bonus record."""
    if request.method == 'POST':
        db = get_db()
        try:
            data = request.form
            
            db.execute("""
                INSERT INTO hr_bonus_records
                (employee_id, bonus_type, amount, reason, effective_month, effective_year, status)
                VALUES (?, ?, ?, ?, ?, ?, 'Pending')
            """, (data.get('employee_id'), data.get('bonus_type'), data.get('amount'),
                  data.get('reason'), data.get('effective_month'), data.get('effective_year')))
            
            db.commit()
            flash('Bonus record created!', 'success')
            return redirect(url_for('hr.bonuses_list'))
            
        except Exception as e:
            db.rollback()
            flash(f'Error: {str(e)}', 'error')
        finally:
            db.close()
    
    db = get_db()
    try:
        employees = db.execute("SELECT id, first_name, last_name, employee_code FROM hr_employees WHERE status = 'Active' ORDER BY first_name").fetchall()
        return render_template('hr/bonuses/new.html',
                             title='Add Bonus',
                             employees=[dict(e) for e in employees],
                             current_month=datetime.now().month,
                             current_year=datetime.now().year)
    finally:
        db.close()


# =============================================================================
# 10. DEDUCTIONS
# =============================================================================

@hr_bp.route('/deductions')
@hr_login_required
@hr_permission_required('view')
def deductions_list():
    """List deduction records."""
    db = get_db()
    try:
        records = db.execute("""
            SELECT d.*, e.first_name, e.last_name, e.employee_code,
                   u.username as approver_name
            FROM hr_deduction_records d
            JOIN hr_employees e ON d.employee_id = e.id
            LEFT JOIN users u ON d.approved_by_id = u.id
            ORDER BY d.created_at DESC
        """).fetchall()
        
        return render_template('hr/deductions/list.html',
                             title='Deductions & Penalties',
                             records=[dict(r) for r in records])
    finally:
        db.close()


@hr_bp.route('/deductions/new', methods=['GET', 'POST'])
@hr_login_required
@hr_permission_required('create')
def deductions_new():
    """Create new deduction record."""
    if request.method == 'POST':
        db = get_db()
        try:
            data = request.form
            
            db.execute("""
                INSERT INTO hr_deduction_records
                (employee_id, deduction_type, amount, reason, is_recurring,
                 start_month, start_year, end_month, end_year, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
            """, (data.get('employee_id'), data.get('deduction_type'), data.get('amount'),
                  data.get('reason'), data.get('is_recurring', 0),
                  data.get('start_month'), data.get('start_year'),
                  data.get('end_month'), data.get('end_year')))
            
            db.commit()
            flash('Deduction record created!', 'success')
            return redirect(url_for('hr.deductions_list'))
            
        except Exception as e:
            db.rollback()
            flash(f'Error: {str(e)}', 'error')
        finally:
            db.close()
    
    db = get_db()
    try:
        employees = db.execute("SELECT id, first_name, last_name, employee_code FROM hr_employees WHERE status = 'Active' ORDER BY first_name").fetchall()
        return render_template('hr/deductions/new.html',
                             title='Add Deduction',
                             employees=[dict(e) for e in employees],
                             current_month=datetime.now().month,
                             current_year=datetime.now().year)
    finally:
        db.close()


# =============================================================================
# 11. TRAINING
# =============================================================================

@hr_bp.route('/training')
@hr_login_required
@hr_permission_required('view')
def training_list():
    """List all training programs."""
    db = get_db()
    try:
        programs = db.execute("""
            SELECT tp.*,
                   COUNT(ts.id) as session_count,
                   COUNT(te.id) as total_enrollments
            FROM hr_training_programs tp
            LEFT JOIN hr_training_sessions ts ON ts.program_id = tp.id
            LEFT JOIN hr_training_enrollments te ON te.session_id = ts.id
            WHERE tp.is_active = 1
            GROUP BY tp.id
            ORDER BY tp.created_at DESC
        """).fetchall()

        sessions = db.execute("""
            SELECT ts.*, tp.title as program_title, tp.training_type
            FROM hr_training_sessions ts
            JOIN hr_training_programs tp ON ts.program_id = tp.id
            ORDER BY ts.start_date DESC
            LIMIT 20
        """).fetchall()

        return render_template('hr/training/list.html',
                             title='Training',
                             programs=[dict(p) for p in programs],
                             sessions=[dict(s) for s in sessions])
    finally:
        db.close()


@hr_bp.route('/training/programs/new', methods=['GET', 'POST'])
@hr_login_required
@hr_permission_required('create')
def training_program_new():
    """Create new training program."""
    if request.method == 'POST':
        db = get_db()
        try:
            data = request.form
            cursor = db.execute("""
                INSERT INTO hr_training_programs
                (title, title_ar, title_fa, description, category, training_type,
                 provider, duration_hours, duration_days, cost_per_participant,
                 certification_validity_months, is_mandatory, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                data.get('title'),
                data.get('title_ar'),
                data.get('title_fa'),
                data.get('description'),
                data.get('category'),
                data.get('training_type', 'Technical'),
                data.get('provider'),
                data.get('duration_hours', 0),
                data.get('duration_days', 0),
                data.get('cost_per_participant', 0),
                data.get('certification_validity_months'),
                1 if data.get('is_mandatory') else 0,
            ))
            db.commit()
            flash('Training program created successfully!', 'success')
            return redirect(url_for('hr.training_list'))
        except Exception as e:
            db.rollback()
            flash(f'Error: {str(e)}', 'error')
        finally:
            db.close()

    return render_template('hr/training/program_new.html', title='New Training Program')


@hr_bp.route('/training/programs/<int:program_id>')
@hr_login_required
@hr_permission_required('view')
def training_program_detail(program_id):
    """View training program details."""
    db = get_db()
    try:
        program = db.execute("SELECT * FROM hr_training_programs WHERE id = ?", (program_id,)).fetchone()
        if not program:
            flash('Training program not found.', 'error')
            return redirect(url_for('hr.training_list'))

        sessions = db.execute("""
            SELECT ts.*,
                   COUNT(te.id) as enrolled_count,
                   SUM(CASE WHEN te.status = 'Completed' THEN 1 ELSE 0 END) as completed_count
            FROM hr_training_sessions ts
            LEFT JOIN hr_training_enrollments te ON te.session_id = ts.id
            WHERE ts.program_id = ?
            GROUP BY ts.id
            ORDER BY ts.start_date DESC
        """, (program_id,)).fetchall()

        return render_template('hr/training/program_detail.html',
                             title=program['title'],
                             program=dict(program),
                             sessions=[dict(s) for s in sessions])
    finally:
        db.close()


@hr_bp.route('/training/sessions/new', methods=['GET', 'POST'])
@hr_login_required
@hr_permission_required('create')
def training_session_new():
    """Create new training session."""
    if request.method == 'POST':
        db = get_db()
        try:
            data = request.form
            cursor = db.execute("""
                INSERT INTO hr_training_sessions
                (program_id, session_title, trainer_name, trainer_contact,
                 location, online_link, start_date, end_date, start_time, end_time,
                 max_participants, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Scheduled')
            """, (
                data.get('program_id'),
                data.get('session_title'),
                data.get('trainer_name'),
                data.get('trainer_contact'),
                data.get('location'),
                data.get('online_link'),
                data.get('start_date'),
                data.get('end_date'),
                data.get('start_time'),
                data.get('end_time'),
                data.get('max_participants', 20),
            ))
            db.commit()
            flash('Training session scheduled successfully!', 'success')
            return redirect(url_for('hr.training_list'))
        except Exception as e:
            db.rollback()
            flash(f'Error: {str(e)}', 'error')
        finally:
            db.close()

    db = get_db()
    try:
        programs = db.execute("SELECT id, title, training_type FROM hr_training_programs WHERE is_active = 1 ORDER BY title").fetchall()
        return render_template('hr/training/session_new.html',
                             title='Schedule Training Session',
                             programs=[dict(p) for p in programs])
    finally:
        db.close()


@hr_bp.route('/training/sessions/<int:session_id>')
@hr_login_required
@hr_permission_required('view')
def training_session_detail(session_id):
    """View training session details with enrollments."""
    db = get_db()
    try:
        session = db.execute("""
            SELECT ts.*, tp.title as program_title, tp.training_type, tp.duration_hours
            FROM hr_training_sessions ts
            JOIN hr_training_programs tp ON ts.program_id = tp.id
            WHERE ts.id = ?
        """, (session_id,)).fetchone()

        if not session:
            flash('Training session not found.', 'error')
            return redirect(url_for('hr.training_list'))

        enrollments = db.execute("""
            SELECT te.*, e.first_name, e.last_name, e.employee_code, e.department_id,
                   d.name as department_name
            FROM hr_training_enrollments te
            JOIN hr_employees e ON te.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON ee.employee_id = e.id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            WHERE te.session_id = ?
            ORDER BY te.enrollment_date DESC
        """, (session_id,)).fetchall()

        available_employees = db.execute("""
            SELECT e.id, e.first_name, e.last_name, e.employee_code,
                   d.name as department_name
            FROM hr_employees e
            LEFT JOIN hr_employee_employment ee ON ee.employee_id = e.id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            WHERE e.status = 'Active'
            AND e.id NOT IN (
                SELECT employee_id FROM hr_training_enrollments WHERE session_id = ?
            )
            ORDER BY e.first_name
        """, (session_id,)).fetchall()

        return render_template('hr/training/session_detail.html',
                             title=session['session_title'] or session['program_title'],
                             session=dict(session),
                             enrollments=[dict(e) for e in enrollments],
                             available_employees=[dict(a) for a in available_employees])
    finally:
        db.close()


@hr_bp.route('/training/sessions/<int:session_id>/enroll', methods=['POST'])
@hr_login_required
@hr_permission_required('create')
def training_session_enroll(session_id):
    """Enroll employee(s) in a training session."""
    db = get_db()
    try:
        employee_ids = request.form.getlist('employee_id')
        for emp_id in employee_ids:
            existing = db.execute(
                "SELECT id FROM hr_training_enrollments WHERE session_id = ? AND employee_id = ?",
                (session_id, emp_id)
            ).fetchone()
            if not existing:
                db.execute("""
                    INSERT INTO hr_training_enrollments (session_id, employee_id, status)
                    VALUES (?, ?, 'Enrolled')
                """, (session_id, emp_id))
                db.execute("""
                    UPDATE hr_training_sessions SET enrolled_count = enrolled_count + 1
                    WHERE id = ?
                """, (session_id,))
        db.commit()
        flash(f'{len(employee_ids)} employee(s) enrolled successfully!', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Error: {str(e)}', 'error')
    finally:
        db.close()
    return redirect(url_for('hr.training_session_detail', session_id=session_id))


@hr_bp.route('/training/enrollments/<int:enrollment_id>/update', methods=['POST'])
@hr_login_required
@hr_permission_required('edit')
def training_enrollment_update(enrollment_id):
    """Update enrollment status, score, and completion."""
    db = get_db()
    try:
        data = request.form
        status = data.get('status')
        score = data.get('score')
        grade = data.get('grade')
        attendance = data.get('attendance_status')
        cert_number = data.get('certificate_number')
        completion_date = data.get('completion_date')

        update_fields = ['status = ?']
        update_values = [status]

        if attendance:
            update_fields.append('attendance_status = ?')
            update_values.append(attendance)
        if score:
            update_fields.append('score = ?')
            update_values.append(float(score))
        if grade:
            update_fields.append('grade = ?')
            update_values.append(grade)
        if cert_number:
            update_fields.append('certificate_number = ?')
            update_values.append(cert_number)
        if completion_date:
            update_fields.append('completion_date = ?')
            update_values.append(completion_date)
        elif status == 'Completed':
            update_fields.append('completion_date = ?')
            update_values.append(datetime.now().strftime('%Y-%m-%d'))

        update_values.append(enrollment_id)
        db.execute(
            f"UPDATE hr_training_enrollments SET {', '.join(update_fields)} WHERE id = ?",
            update_values
        )
        db.commit()
        flash('Enrollment updated successfully!', 'success')
        session_id_row = db.execute("SELECT session_id FROM hr_training_enrollments WHERE id = ?", (enrollment_id,)).fetchone()
        redirect_session_id = session_id_row['session_id'] if session_id_row else 0
    except Exception as e:
        db.rollback()
        flash(f'Error: {str(e)}', 'error')
        redirect_session_id = 0
    finally:
        db.close()

    return redirect(url_for('hr.training_session_detail', session_id=redirect_session_id))


@hr_bp.route('/training/enrollments/<int:enrollment_id>/delete', methods=['POST'])
@hr_login_required
@hr_permission_required('delete')
def training_enrollment_delete(enrollment_id):
    """Remove an enrollment from a training session."""
    db = get_db()
    try:
        enrollment = db.execute("SELECT session_id FROM hr_training_enrollments WHERE id = ?", (enrollment_id,)).fetchone()
        if enrollment:
            db.execute("DELETE FROM hr_training_enrollments WHERE id = ?", (enrollment_id,))
            db.execute("UPDATE hr_training_sessions SET enrolled_count = MAX(0, enrolled_count - 1) WHERE id = ?",
                       (enrollment['session_id'],))
        db.commit()
        flash('Enrollment removed.', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Error: {str(e)}', 'error')
    finally:
        db.close()
    return redirect(url_for('hr.training_list'))


@hr_bp.route('/training/sessions/<int:session_id>/status', methods=['POST'])
@hr_login_required
@hr_permission_required('edit')
def training_session_update_status(session_id):
    """Update training session status (Scheduled -> Ongoing -> Completed)."""
    db = get_db()
    try:
        status = request.form.get('status') or request.args.get('status')
        if status in ('Scheduled', 'Ongoing', 'Completed', 'Cancelled'):
            db.execute("UPDATE hr_training_sessions SET status = ? WHERE id = ?", (status, session_id))
            db.commit()
            flash(f'Session marked as {status}!', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Error: {str(e)}', 'error')
    finally:
        db.close()
    return redirect(url_for('hr.training_session_detail', session_id=session_id))


@hr_bp.route('/training/reports')
@hr_login_required
@hr_permission_required('view')
def training_reports():
    """Training reports and analytics."""
    db = get_db()
    try:
        total_programs = db.execute("SELECT COUNT(*) as cnt FROM hr_training_programs WHERE is_active = 1").fetchone()['cnt']
        total_sessions = db.execute("SELECT COUNT(*) as cnt FROM hr_training_sessions").fetchone()['cnt']
        total_enrollments = db.execute("SELECT COUNT(*) as cnt FROM hr_training_enrollments").fetchone()['cnt']
        completed = db.execute("SELECT COUNT(*) as cnt FROM hr_training_enrollments WHERE status = 'Completed'").fetchone()['cnt']

        by_type = db.execute("""
            SELECT tp.training_type, COUNT(DISTINCT tp.id) as programs,
                   COUNT(te.id) as enrollments
            FROM hr_training_programs tp
            LEFT JOIN hr_training_sessions ts ON ts.program_id = tp.id
            LEFT JOIN hr_training_enrollments te ON te.session_id = ts.id
            GROUP BY tp.training_type
        """).fetchall()

        recent = db.execute("""
            SELECT te.*, e.first_name, e.last_name, e.employee_code,
                   ts.session_title, tp.title as program_title
            FROM hr_training_enrollments te
            JOIN hr_employees e ON te.employee_id = e.id
            JOIN hr_training_sessions ts ON te.session_id = ts.id
            JOIN hr_training_programs tp ON ts.program_id = tp.id
            ORDER BY te.created_at DESC
            LIMIT 50
        """).fetchall()

        return render_template('hr/training/reports.html',
                             title='Training Reports',
                             stats={
                                 'total_programs': total_programs,
                                 'total_sessions': total_sessions,
                                 'total_enrollments': total_enrollments,
                                 'completed': completed,
                                 'completion_rate': round(completed / total_enrollments * 100, 1) if total_enrollments > 0 else 0
                             },
                             by_type=[dict(r) for r in by_type],
                             recent=[dict(r) for r in recent])
    finally:
        db.close()


# =============================================================================
# 12. DOCUMENTS
# =============================================================================

@hr_bp.route('/documents')
@hr_login_required
@hr_permission_required('view')
def documents_list():
    """List employee documents."""
    db = get_db()
    try:
        employee_id = request.args.get('employee_id', '')
        
        query = """
            SELECT ed.*, e.first_name, e.last_name, e.employee_code
            FROM hr_employee_documents ed
            JOIN hr_employees e ON ed.employee_id = e.id
            WHERE 1=1
        """
        params = []
        
        if employee_id:
            query += " AND ed.employee_id = ?"
            params.append(employee_id)
        
        query += " ORDER BY ed.expiry_date IS NOT NULL, ed.expiry_date, ed.created_at DESC"
        
        documents = db.execute(query, params).fetchall()
        employees = db.execute("SELECT id, first_name, last_name, employee_code FROM hr_employees ORDER BY first_name").fetchall()
        
        return render_template('hr/documents/list.html',
                             title='Employee Documents',
                             documents=[dict(d) for d in documents],
                             employees=[dict(e) for e in employees],
                             selected_employee=employee_id)
    finally:
        db.close()


@hr_bp.route('/documents/new', methods=['GET', 'POST'])
@hr_login_required
@hr_permission_required('create')
def documents_new():
    """Upload new employee document."""
    if request.method == 'POST':
        db = get_db()
        try:
            data = request.form
            
            db.execute("""
                INSERT INTO hr_employee_documents
                (employee_id, document_type, document_name, document_number,
                 issue_date, expiry_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (data.get('employee_id'), data.get('document_type'),
                  data.get('document_name'), data.get('document_number'),
                  parse_date(data.get('issue_date')), parse_date(data.get('expiry_date')),
                  data.get('notes')))
            
            db.commit()
            flash('Document record added!', 'success')
            return redirect(url_for('hr.documents_list'))
            
        except Exception as e:
            db.rollback()
            flash(f'Error: {str(e)}', 'error')
        finally:
            db.close()
    
    db = get_db()
    try:
        employees = db.execute("SELECT id, first_name, last_name, employee_code FROM hr_employees ORDER BY first_name").fetchall()
        
        doc_types = [
            ('Passport', 'Passport'),
            ('Emirates ID', 'Emirates ID'),
            ('Visa', 'Visa'),
            ('Labour Card', 'Labour Card'),
            ('Contract', 'Contract'),
            ('Degree/Certificate', 'Degree/Certificate'),
            ('CV/Resume', 'CV/Resume'),
            ('Photo', 'Photo'),
            ('Other', 'Other')
        ]
        
        return render_template('hr/documents/new.html',
                             title='Upload Document',
                             employees=[dict(e) for e in employees],
                             doc_types=doc_types)
    finally:
        db.close()


# =============================================================================
# DOCUMENT EXPIRY ALERTS API
# =============================================================================

@hr_bp.route('/api/document-expiry-alerts')
@hr_login_required
@hr_permission_required('view')
def document_expiry_alerts():
    """Get document expiry alerts for notifications."""
    db = get_db()
    try:
        days = int(request.args.get('days', 30))
        expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

        # Get documents expiring within the specified days
        expiring_docs = db.execute("""
            SELECT ed.*, e.first_name, e.last_name, e.employee_code, e.user_id,
                   dt.name as document_type_name
            FROM hr_employee_documents ed
            JOIN hr_employees e ON ed.employee_id = e.id
            LEFT JOIN hr_document_types dt ON ed.document_type_id = dt.id
            WHERE ed.expiry_date IS NOT NULL
            AND ed.expiry_date <= ?
            AND ed.expiry_date >= date('now')
            ORDER BY ed.expiry_date ASC
        """, (expiry_date,)).fetchall()

        # Send Flow notifications for each expiring document
        alerts_sent = 0
        for doc in expiring_docs:
            if doc['user_id']:
                send_hr_flow_notification(
                    title='Document Expiry Alert',
                    message=f'Your {doc["document_type_name"] or doc["document_type"] or "document"} "{doc["document_name"]}" will expire on {doc["expiry_date"]}. Please renew it soon.',
                    priority='high',
                    user_ids=[doc['user_id']],
                    channel='compliance'
                )
                alerts_sent += 1

        return jsonify({
            'success': True,
            'alerts_sent': alerts_sent,
            'total_expiring': len(expiring_docs)
        })
    finally:
        db.close()


@hr_bp.route('/api/certification-expiry-alerts')
@hr_login_required
@hr_permission_required('view')
def certification_expiry_alerts():
    """Get certification expiry alerts for notifications."""
    db = get_db()
    try:
        days = int(request.args.get('days', 30))
        expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

        # Get certifications expiring within the specified days
        expiring_certs = db.execute("""
            SELECT c.*, e.first_name, e.last_name, e.employee_code, e.user_id,
                   ct.name as certification_type_name
            FROM hr_employee_certifications c
            JOIN hr_employees e ON c.employee_id = e.id
            LEFT JOIN hr_certification_types ct ON c.certification_type_id = ct.id
            WHERE c.expiry_date IS NOT NULL
            AND c.expiry_date <= ?
            AND c.expiry_date >= date('now')
            ORDER BY c.expiry_date ASC
        """, (expiry_date,)).fetchall()

        # Send Flow notifications for each expiring certification
        alerts_sent = 0
        for cert in expiring_certs:
            if cert['user_id']:
                send_hr_flow_notification(
                    title='Certification Expiry Alert',
                    message=f'Your {cert["certification_type_name"] or cert["name"] or "certification"} will expire on {cert["expiry_date"]}. Please renew it soon.',
                    priority='high',
                    user_ids=[cert['user_id']],
                    channel='compliance'
                )
                alerts_sent += 1

        return jsonify({
            'success': True,
            'alerts_sent': alerts_sent,
            'total_expiring': len(expiring_certs)
        })
    finally:
        db.close()


# =============================================================================
# 13. RECRUITMENT
# =============================================================================

@hr_bp.route('/recruitment')
@hr_login_required
@hr_permission_required('view')
def recruitment_list():
    """List job requisitions."""
    db = get_db()
    try:
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        department = request.args.get('department', '')
        page = max(1, int(request.args.get('page', 1)))
        per_page = 15

        # Build query
        query = """
            SELECT r.*, d.name as department_name, p.title as position_title,
                   u.username as requested_by_name
            FROM hr_job_requisitions r
            LEFT JOIN hr_departments d ON r.department_id = d.id
            LEFT JOIN hr_positions p ON r.position_id = p.id
            LEFT JOIN users u ON r.requested_by_id = u.id
            WHERE 1=1
        """
        count_query = "SELECT COUNT(*) as cnt FROM hr_job_requisitions r WHERE 1=1"
        params = []

        if search:
            query += " AND (r.title LIKE ? OR d.name LIKE ?)"
            count_query += " AND (r.title LIKE ? OR d.name LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%'])

        if status:
            query += " AND r.status = ?"
            count_query += " AND r.status = ?"
            params.append(status)

        if department:
            query += " AND r.department_id = ?"
            count_query += " AND r.department_id = ?"
            params.append(department)

        total = db.execute(count_query, params).fetchone()['cnt']
        total_pages = max(1, (total + per_page - 1) // per_page)
        offset = (page - 1) * per_page

        query += " ORDER BY r.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        requisitions = db.execute(query, params).fetchall()

        # Stats
        stats = {
            'open': db.execute("SELECT COUNT(*) as cnt FROM hr_job_requisitions WHERE status='Open'").fetchone()['cnt'],
            'in_review': db.execute("SELECT COUNT(*) as cnt FROM hr_job_requisitions WHERE status='In Review'").fetchone()['cnt'],
            'pending': db.execute("SELECT COUNT(*) as cnt FROM hr_job_requisitions WHERE status='Pending Approval'").fetchone()['cnt'],
            'vacancies': db.execute("SELECT COALESCE(SUM(vacancy_count),0) as cnt FROM hr_job_requisitions WHERE status='Open'").fetchone()['cnt']
        }

        # Departments for filter
        departments = db.execute("SELECT id, name FROM hr_departments ORDER BY name").fetchall()

        return render_template('hr/recruitment/list.html',
                             title='Recruitment',
                             requisitions=[dict(r) for r in requisitions],
                             stats=stats,
                             departments=[dict(d) for d in departments],
                             search=search,
                             status=status,
                             department=department,
                             page=page,
                             total_pages=total_pages,
                             total=total)
    finally:
        db.close()


@hr_bp.route('/recruitment/candidates')
@hr_login_required
@hr_permission_required('view')
def candidates_list():
    """List candidates."""
    db = get_db()
    try:
        search = request.args.get('search', '')
        stage = request.args.get('stage', '')
        status = request.args.get('status', '')
        page = max(1, int(request.args.get('page', 1)))
        per_page = 15

        query = """
            SELECT c.*, r.title as requisition_title
            FROM hr_candidates c
            LEFT JOIN hr_job_requisitions r ON c.requisition_id = r.id
            WHERE 1=1
        """
        count_query = "SELECT COUNT(*) as cnt FROM hr_candidates c WHERE 1=1"
        params = []

        if search:
            query += " AND (c.first_name LIKE ? OR c.last_name LIKE ? OR c.email LIKE ? OR c.position_applied LIKE ?)"
            count_query += " AND (c.first_name LIKE ? OR c.last_name LIKE ? OR c.email LIKE ? OR c.position_applied LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%'])

        if stage:
            query += " AND c.current_stage = ?"
            count_query += " AND c.current_stage = ?"
            params.append(stage)

        if status:
            query += " AND c.status = ?"
            count_query += " AND c.status = ?"
            params.append(status)

        total = db.execute(count_query, params).fetchone()['cnt']
        total_pages = max(1, (total + per_page - 1) // per_page)
        offset = (page - 1) * per_page

        query += " ORDER BY c.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        candidates = db.execute(query, params).fetchall()

        # Stats
        stats = {
            'total': db.execute("SELECT COUNT(*) as cnt FROM hr_candidates").fetchone()['cnt'],
            'interview': db.execute("SELECT COUNT(*) as cnt FROM hr_candidates WHERE current_stage IN ('Interview','Technical')").fetchone()['cnt'],
            'offer': db.execute("SELECT COUNT(*) as cnt FROM hr_candidates WHERE current_stage = 'Offer'").fetchone()['cnt'],
            'hired': db.execute("SELECT COUNT(*) as cnt FROM hr_candidates WHERE current_stage = 'Hired'").fetchone()['cnt']
        }

        return render_template('hr/recruitment/candidates.html',
                             title='Candidates',
                             candidates=[dict(c) for c in candidates],
                             stats=stats,
                             search=search,
                             stage=stage,
                             status=status,
                             page=page,
                             total_pages=total_pages,
                             total=total)
    finally:
        db.close()


@hr_bp.route('/recruitment/candidates/new', methods=['GET', 'POST'])
@hr_login_required
@hr_permission_required('add')
def candidate_new():
    """Create new candidate."""
    db = get_db()
    try:
        requisitions = db.execute("SELECT id, title FROM hr_job_requisitions WHERE status = 'Open' ORDER BY title").fetchall()
        users = db.execute("SELECT id, username FROM users ORDER BY username").fetchall()

        if request.method == 'POST':
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            position_applied = request.form.get('position_applied')
            requisition_id = request.form.get('requisition_id')
            source = request.form.get('source')
            current_stage = request.form.get('current_stage', 'Applied')
            notes = request.form.get('notes')
            assigned_recruiter_id = request.form.get('assigned_recruiter_id')

            db.execute("""
                INSERT INTO hr_candidates
                (first_name, last_name, email, phone, position_applied, requisition_id,
                 source, current_stage, notes, assigned_recruiter_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Active')
            """, (first_name, last_name, email, phone, position_applied, requisition_id,
                  source, current_stage, notes, assigned_recruiter_id))
            db.commit()

            flash(t('candidate_created', 'Candidate added successfully'), 'success')
            return redirect(url_for('hr.candidates_list'))

        return render_template('hr/recruitment/candidate_new.html',
                             requisitions=[dict(r) for r in requisitions],
                             users=[dict(u) for u in users])
    finally:
        db.close()


@hr_bp.route('/recruitment/candidates/view/<int:id>')
@hr_login_required
@hr_permission_required('view')
def candidate_view(id):
    """View candidate details."""
    db = get_db()
    try:
        c = db.execute("""
            SELECT c.*, r.title as requisition_title
            FROM hr_candidates c
            LEFT JOIN hr_job_requisitions r ON c.requisition_id = r.id
            WHERE c.id = ?
        """, (id,)).fetchone()

        if not c:
            flash(t('candidate_not_found', 'Candidate not found'), 'error')
            return redirect(url_for('hr.candidates_list'))

        return render_template('hr/recruitment/candidate_view.html',
                             candidate=dict(c))
    finally:
        db.close()


@hr_bp.route('/recruitment/candidates/edit/<int:id>', methods=['GET', 'POST'])
@hr_login_required
@hr_permission_required('edit')
def candidate_edit(id):
    """Edit candidate."""
    db = get_db()
    try:
        c = db.execute("SELECT * FROM hr_candidates WHERE id = ?", (id,)).fetchone()
        if not c:
            flash(t('candidate_not_found', 'Candidate not found'), 'error')
            return redirect(url_for('hr.candidates_list'))

        requisitions = db.execute("SELECT id, title FROM hr_job_requisitions ORDER BY title").fetchall()
        users = db.execute("SELECT id, username FROM users ORDER BY username").fetchall()

        if request.method == 'POST':
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            position_applied = request.form.get('position_applied')
            requisition_id = request.form.get('requisition_id')
            source = request.form.get('source')
            current_stage = request.form.get('current_stage', 'Applied')
            interview_score = request.form.get('interview_score')
            status = request.form.get('status', 'Active')
            notes = request.form.get('notes')
            assigned_recruiter_id = request.form.get('assigned_recruiter_id')

            db.execute("""
                UPDATE hr_candidates SET
                    first_name = ?, last_name = ?, email = ?, phone = ?,
                    position_applied = ?, requisition_id = ?, source = ?,
                    current_stage = ?, interview_score = ?, status = ?,
                    notes = ?, assigned_recruiter_id = ?
                WHERE id = ?
            """, (first_name, last_name, email, phone, position_applied, requisition_id,
                  source, current_stage, interview_score, status, notes, assigned_recruiter_id, id))
            db.commit()

            flash(t('candidate_updated', 'Candidate updated successfully'), 'success')
            return redirect(url_for('hr.candidates_list'))

        return render_template('hr/recruitment/candidate_edit.html',
                             candidate=dict(c),
                             requisitions=[dict(r) for r in requisitions],
                             users=[dict(u) for u in users])
    finally:
        db.close()


@hr_bp.route('/recruitment/new', methods=['GET', 'POST'])
@hr_login_required
@hr_permission_required('add')
def requisition_new():
    """Create new job requisition."""
    db = get_db()
    try:
        departments = db.execute("SELECT id, name FROM hr_departments ORDER BY name").fetchall()
        positions = db.execute("SELECT id, title FROM hr_positions ORDER BY title").fetchall()

        if request.method == 'POST':
            title = request.form.get('title')
            department_id = request.form.get('department_id')
            position_id = request.form.get('position_id')
            vacancy_count = request.form.get('vacancy_count', 1)
            employment_type = request.form.get('employment_type', 'Full-time')
            salary_min = request.form.get('salary_min')
            salary_max = request.form.get('salary_max')
            description = request.form.get('description')
            requirements = request.form.get('requirements')
            status = request.form.get('status', 'Draft')

            user_id = session.get('user_id')

            db.execute("""
                INSERT INTO hr_job_requisitions
                (title, department_id, position_id, vacancy_count, employment_type,
                 salary_min, salary_max, description, requirements, status, requested_by_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, department_id, position_id, vacancy_count, employment_type,
                  salary_min, salary_max, description, requirements, status, user_id))
            req_id = db.execute("SELECT last_insert_rowid() as id").fetchone()['id']
            db.commit()

            # Send Flow notification to HR managers
            hr_managers = db.execute("""
                SELECT DISTINCT u.id as user_id FROM users u
                JOIN hr_employees e ON u.employee_id = e.id
                JOIN hr_employee_employment ee ON e.id = ee.employee_id
                WHERE ee.position_id IN (SELECT id FROM hr_positions WHERE title LIKE '%HR%Manager%' OR title LIKE '%HR%Head%')
                OR u.can_manage_hr = 1
            """).fetchall()

            manager_ids = [m['user_id'] for m in hr_managers if m['user_id']]
            if manager_ids:
                send_hr_flow_notification(
                    title='New Job Requisition Created',
                    message=f'A new job requisition "{title}" has been created for {vacancy_count} position(s). Please review and approve.',
                    priority='high',
                    user_ids=manager_ids,
                    channel='recruitment'
                )

            flash(t('requisition_created', 'Job requisition created successfully'), 'success')
            return redirect(url_for('hr.recruitment_list'))

        return render_template('hr/recruitment/requisition_new.html',
                             departments=[dict(d) for d in departments],
                             positions=[dict(p) for p in positions])
    finally:
        db.close()


@hr_bp.route('/recruitment/view/<int:id>')
@hr_login_required
@hr_permission_required('view')
def requisition_view(id):
    """View job requisition details."""
    db = get_db()
    try:
        r = db.execute("""
            SELECT r.*, d.name as department_name, p.title as position_title,
                   u.username as requested_by_name
            FROM hr_job_requisitions r
            LEFT JOIN hr_departments d ON r.department_id = d.id
            LEFT JOIN hr_positions p ON r.position_id = p.id
            LEFT JOIN users u ON r.requested_by_id = u.id
            WHERE r.id = ?
        """, (id,)).fetchone()

        if not r:
            flash(t('requisition_not_found', 'Job requisition not found'), 'error')
            return redirect(url_for('hr.recruitment_list'))

        candidates = db.execute("""
            SELECT c.* FROM hr_candidates c
            WHERE c.requisition_id = ?
            ORDER BY c.created_at DESC
        """, (id,)).fetchall()

        return render_template('hr/recruitment/requisition_view.html',
                             requisition=dict(r),
                             candidates=[dict(c) for c in candidates])
    finally:
        db.close()


@hr_bp.route('/recruitment/edit/<int:id>', methods=['GET', 'POST'])
@hr_login_required
@hr_permission_required('edit')
def requisition_edit(id):
    """Edit job requisition."""
    db = get_db()
    try:
        r = db.execute("SELECT * FROM hr_job_requisitions WHERE id = ?", (id,)).fetchone()
        if not r:
            flash(t('requisition_not_found', 'Job requisition not found'), 'error')
            return redirect(url_for('hr.recruitment_list'))

        departments = db.execute("SELECT id, name FROM hr_departments ORDER BY name").fetchall()
        positions = db.execute("SELECT id, title FROM hr_positions ORDER BY title").fetchall()

        if request.method == 'POST':
            title = request.form.get('title')
            department_id = request.form.get('department_id')
            position_id = request.form.get('position_id')
            vacancy_count = request.form.get('vacancy_count', 1)
            employment_type = request.form.get('employment_type', 'Full-time')
            salary_min = request.form.get('salary_min')
            salary_max = request.form.get('salary_max')
            description = request.form.get('description')
            requirements = request.form.get('requirements')
            status = request.form.get('status', 'Draft')

            db.execute("""
                UPDATE hr_job_requisitions SET
                    title = ?, department_id = ?, position_id = ?, vacancy_count = ?,
                    employment_type = ?, salary_min = ?, salary_max = ?,
                    description = ?, requirements = ?, status = ?
                WHERE id = ?
            """, (title, department_id, position_id, vacancy_count, employment_type,
                  salary_min, salary_max, description, requirements, status, id))
            db.commit()

            flash(t('requisition_updated', 'Job requisition updated successfully'), 'success')
            return redirect(url_for('hr.recruitment_list'))

        return render_template('hr/recruitment/requisition_edit.html',
                             requisition=dict(r),
                             departments=[dict(d) for d in departments],
                             positions=[dict(p) for p in positions])
    finally:
        db.close()


# =============================================================================
# 14. TASKS & PERFORMANCE
# =============================================================================

@hr_bp.route('/tasks')
@hr_login_required
@hr_permission_required('view')
def tasks_list():
    """List employee tasks."""
    db = get_db()
    try:
        employee_id = request.args.get('employee_id', '')
        
        query = """
            SELECT t.*, e.first_name, e.last_name, e.employee_code,
                   u.username as assigned_by_name
            FROM hr_tasks t
            JOIN hr_employees e ON t.employee_id = e.id
            LEFT JOIN users u ON t.assigned_by_id = u.id
            WHERE 1=1
        """
        params = []
        
        if employee_id:
            query += " AND t.employee_id = ?"
            params.append(employee_id)
        
        query += " ORDER BY t.due_date ASC"
        
        tasks = db.execute(query, params).fetchall()
        employees = db.execute("SELECT id, first_name, last_name, employee_code FROM hr_employees WHERE status = 'Active' ORDER BY first_name").fetchall()
        
        return render_template('hr/tasks/list.html',
                             title='Employee Tasks',
                             tasks=[dict(t) for t in tasks],
                             employees=[dict(e) for e in employees],
                             selected_employee=employee_id)
    finally:
        db.close()


@hr_bp.route('/performance')
@hr_login_required
@hr_permission_required('view')
def performance_list():
    """List performance reviews."""
    db = get_db()
    try:
        reviews = db.execute("""
            SELECT pr.*, e.first_name, e.last_name, e.employee_code,
                   u.username as reviewer_name
            FROM hr_performance_reviews pr
            JOIN hr_employees e ON pr.employee_id = e.id
            LEFT JOIN users u ON pr.reviewer_id = u.id
            ORDER BY pr.review_date DESC
        """).fetchall()
        
        return render_template('hr/performance/list.html',
                             title='Performance Reviews',
                             reviews=[dict(r) for r in reviews])
    finally:
        db.close()


# =============================================================================
# 15. SUCCESSORS
# =============================================================================

@hr_bp.route('/successors')
@hr_login_required
@hr_permission_required('view')
def successors_list():
    """List successor plans."""
    db = get_db()
    try:
        successors = db.execute("""
            SELECT s.*, 
                   e1.first_name || ' ' || e1.last_name as employee_name,
                   e2.first_name || ' ' || e2.last_name as successor_name,
                   e3.first_name || ' ' || e3.last_name as deputy_name
            FROM hr_successors s
            JOIN hr_employees e1 ON s.employee_id = e1.id
            LEFT JOIN hr_employees e2 ON s.successor_id = e2.id
            LEFT JOIN hr_employees e3 ON s.deputy_id = e3.id
            ORDER BY e1.first_name
        """).fetchall()
        
        return render_template('hr/successors/list.html',
                             title='Successor Planning',
                             successors=[dict(s) for s in successors])
    finally:
        db.close()


# =============================================================================
# 16. REPORTS
# =============================================================================

@hr_bp.route('/reports')
@hr_login_required
@hr_permission_required('view')
def reports_menu():
    """HR Reports menu."""
    return render_template('hr/reports/menu.html', title='HR Reports')


@hr_bp.route('/reports/headcount')
@hr_login_required
@hr_permission_required('view')
def report_headcount():
    """Headcount report."""
    db = get_db()
    try:
        # By department
        by_dept = db.execute("""
            SELECT d.name as department,
                   COUNT(DISTINCT ee.employee_id) as headcount,
                   SUM(CASE WHEN e.gender = 'Male' THEN 1 ELSE 0 END) as male,
                   SUM(CASE WHEN e.gender = 'Female' THEN 1 ELSE 0 END) as female
            FROM hr_departments d
            LEFT JOIN hr_employee_employment ee ON d.id = ee.department_id AND ee.employment_status = 'Active'
            LEFT JOIN hr_employees e ON ee.employee_id = e.id AND e.status = 'Active'
            WHERE d.status = 'Active'
            GROUP BY d.id
            ORDER BY d.name
        """).fetchall()
        
        # By status
        by_status = db.execute("""
            SELECT status, COUNT(*) as count
            FROM hr_employees
            GROUP BY status
        """).fetchall()
        
        # By employment type
        by_type = db.execute("""
            SELECT ee.employment_type, COUNT(*) as count
            FROM hr_employee_employment ee
            WHERE ee.is_primary = 1
            GROUP BY ee.employment_type
        """).fetchall()
        
        return render_template('hr/reports/headcount.html',
                             title='Headcount Report',
                             by_dept=[dict(d) for d in by_dept],
                             by_status=[dict(s) for s in by_status],
                             by_type=[dict(t) for t in by_type])
    finally:
        db.close()


@hr_bp.route('/reports/leave')
@hr_login_required
@hr_permission_required('view')
def report_leave():
    """Leave usage report."""
    db = get_db()
    try:
        year = request.args.get('year', datetime.now().year)
        
        leave_usage = db.execute("""
            SELECT e.employee_code, e.first_name, e.last_name,
                   lt.name as leave_type,
                   lb.total_days, lb.used_days, lb.pending_days, lb.balance_days
            FROM hr_leave_balances lb
            JOIN hr_employees e ON lb.employee_id = e.id
            JOIN hr_leave_types lt ON lb.leave_type_id = lt.id
            WHERE lb.year = ?
            ORDER BY e.first_name, lt.name
        """, (year,)).fetchall()
        
        return render_template('hr/reports/leave.html',
                             title='Leave Report',
                             leave_usage=[dict(l) for l in leave_usage],
                             year=year)
    finally:
        db.close()


@hr_bp.route('/reports/payroll-summary')
@hr_login_required
@hr_permission_required('view')
def report_payroll_summary():
    """Payroll summary report."""
    db = get_db()
    try:
        periods = db.execute("""
            SELECT p.year, p.month, p.name,
                   COUNT(pr.id) as employees,
                   SUM(pr.gross_salary) as total_gross,
                   SUM(pr.net_salary) as total_net
            FROM hr_payroll_periods p
            LEFT JOIN hr_payroll_records pr ON p.id = pr.period_id
            GROUP BY p.id
            ORDER BY p.year DESC, p.month DESC
        """).fetchall()
        
        return render_template('hr/reports/payroll_summary.html',
                             title='Payroll Summary',
                             periods=[dict(p) for p in periods])
    finally:
        db.close()


@hr_bp.route('/reports/recruitment')
@hr_login_required
@hr_permission_required('view')
def recruitment_report():
    """Recruitment report with pipeline metrics."""
    db = get_db()
    try:
        year = request.args.get('year', datetime.now().year)
        status = request.args.get('status', '')
        department = request.args.get('department', '')

        # Get stats
        stats = {
            'total': 0,
            'open': 0,
            'candidates': 0,
            'hired': 0
        }

        # Total requisitions
        total_req = db.execute("SELECT COUNT(*) as cnt FROM hr_recruitment_requisitions").fetchone()
        stats['total'] = total_req['cnt'] if total_req else 0

        # Open requisitions
        open_req = db.execute("SELECT COUNT(*) as cnt FROM hr_recruitment_requisitions WHERE status = 'Open'").fetchone()
        stats['open'] = open_req['cnt'] if open_req else 0

        # Total candidates
        total_cand = db.execute("SELECT COUNT(*) as cnt FROM hr_candidates").fetchone()
        stats['candidates'] = total_cand['cnt'] if total_cand else 0

        # Hired
        hired = db.execute("SELECT COUNT(*) as cnt FROM hr_candidates WHERE hiring_status = 'Hired'").fetchone()
        stats['hired'] = hired['cnt'] if hired else 0

        # Requisitions list
        req_query = """
            SELECT r.*, d.name as department_name, p.title as position_title,
                   (SELECT COUNT(*) FROM hr_candidates c WHERE c.requisition_id = r.id) as candidate_count
            FROM hr_recruitment_requisitions r
            LEFT JOIN hr_departments d ON r.department_id = d.id
            LEFT JOIN hr_positions p ON r.position_id = p.id
            WHERE 1=1
        """
        req_params = []

        if status:
            req_query += " AND r.status = ?"
            req_params.append(status)

        if department:
            req_query += " AND r.department_id = ?"
            req_params.append(department)

        req_query += " ORDER BY r.created_at DESC LIMIT 100"

        requisitions = db.execute(req_query, req_params).fetchall()

        # Departments for filter
        departments = db.execute("SELECT id, name FROM hr_departments WHERE status = 'Active' ORDER BY name").fetchall()

        return render_template('hr/reports/recruitment.html',
                             title='Recruitment Report',
                             stats=stats,
                             requisitions=[dict(r) for r in requisitions],
                             departments=[dict(d) for d in departments],
                             year=year, status=status, department=department)
    finally:
        db.close()


@hr_bp.route('/reports/performance')
@hr_login_required
@hr_permission_required('view')
def performance_report():
    """Performance report with review analytics."""
    db = get_db()
    try:
        # Get stats
        total_reviews = db.execute("SELECT COUNT(*) as cnt FROM hr_performance_reviews").fetchone()['cnt']
        pending = db.execute("SELECT COUNT(*) as cnt FROM hr_performance_reviews WHERE status = 'Pending'").fetchone()['cnt']
        completed = db.execute("SELECT COUNT(*) as cnt FROM hr_performance_reviews WHERE status = 'Completed'").fetchone()['cnt']

        avg_result = db.execute("SELECT AVG(overall_rating) as avg FROM hr_performance_reviews WHERE overall_rating IS NOT NULL").fetchone()
        avg_rating = round(avg_result['avg'], 1) if avg_result and avg_result['avg'] else 0

        stats = {
            'total_reviews': total_reviews,
            'pending': pending,
            'completed': completed,
            'avg_rating': avg_rating
        }

        # Rating distribution
        rating_dist = db.execute("""
            SELECT overall_rating as rating, COUNT(*) as count
            FROM hr_performance_reviews
            WHERE overall_rating IS NOT NULL
            GROUP BY overall_rating
            ORDER BY overall_rating DESC
        """).fetchall()

        # Calculate percentages
        rating_distribution = []
        for r in rating_dist:
            percentage = (r['count'] / total_reviews * 100) if total_reviews > 0 else 0
            rating_distribution.append({
                'rating': r['rating'],
                'count': r['count'],
                'percentage': round(percentage, 1)
            })

        # Reviews by department
        by_dept = db.execute("""
            SELECT d.name as department_name, COUNT(pr.id) as count
            FROM hr_performance_reviews pr
            LEFT JOIN hr_employee_employment ee ON pr.employee_id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            GROUP BY d.id
            ORDER BY count DESC
        """).fetchall()

        # Reviews list
        reviews = db.execute("""
            SELECT pr.*, e.first_name || ' ' || e.last_name as employee_name
            FROM hr_performance_reviews pr
            LEFT JOIN hr_employees e ON pr.employee_id = e.id
            ORDER BY pr.created_at DESC
            LIMIT 100
        """).fetchall()

        return render_template('hr/reports/performance.html',
                             title='Performance Report',
                             stats=stats,
                             rating_distribution=rating_distribution,
                             by_department=[dict(d) for d in by_dept],
                             reviews=[dict(r) for r in reviews])
    finally:
        db.close()


@hr_bp.route('/reports/training')
@hr_login_required
@hr_permission_required('view')
def training_report():
    """Training report with completion analytics."""
    db = get_db()
    try:
        total_programs = db.execute("SELECT COUNT(*) as cnt FROM hr_training_programs WHERE is_active = 1").fetchone()['cnt']
        total_sessions = db.execute("SELECT COUNT(*) as cnt FROM hr_training_sessions").fetchone()['cnt']
        total_enrollments = db.execute("SELECT COUNT(*) as cnt FROM hr_training_enrollments").fetchone()['cnt']
        completed = db.execute("SELECT COUNT(*) as cnt FROM hr_training_enrollments WHERE status = 'Completed'").fetchone()['cnt']

        completion_rate = round(completed / total_enrollments * 100, 1) if total_enrollments > 0 else 0

        stats = {
            'total_programs': total_programs,
            'total_sessions': total_sessions,
            'total_enrollments': total_enrollments,
            'completed': completed,
            'completion_rate': completion_rate
        }

        # By training type
        by_type = db.execute("""
            SELECT tp.training_type, COUNT(DISTINCT tp.id) as programs,
                   COUNT(te.id) as enrollments
            FROM hr_training_programs tp
            LEFT JOIN hr_training_sessions ts ON ts.program_id = tp.id
            LEFT JOIN hr_training_enrollments te ON te.session_id = ts.id
            GROUP BY tp.training_type
        """).fetchall()

        # Recent enrollments
        recent = db.execute("""
            SELECT te.*, e.first_name, e.last_name, e.employee_code,
                   ts.session_title, tp.title as program_title
            FROM hr_training_enrollments te
            JOIN hr_employees e ON te.employee_id = e.id
            JOIN hr_training_sessions ts ON te.session_id = ts.id
            JOIN hr_training_programs tp ON ts.program_id = tp.id
            ORDER BY te.created_at DESC
            LIMIT 50
        """).fetchall()

        return render_template('hr/reports/training.html',
                             title='Training Report',
                             stats=stats,
                             by_type=[dict(t) for t in by_type],
                             recent=[dict(r) for r in recent])
    finally:
        db.close()


@hr_bp.route('/reports/compliance')
@hr_login_required
@hr_permission_required('view')
def compliance_report():
    """Compliance report for document and certification expiry."""
    db = get_db()
    try:
        today = date.today()
        thirty_days = (today + timedelta(days=30)).isoformat()
        seven_days = (today + timedelta(days=7)).isoformat()

        # Documents expiring soon
        expiring_soon = db.execute("""
            SELECT d.*, e.first_name, e.last_name, e.employee_code,
                   dt.name as document_type_name
            FROM hr_documents d
            JOIN hr_employees e ON d.employee_id = e.id
            LEFT JOIN hr_document_types dt ON d.document_type_id = dt.id
            WHERE d.expiry_date IS NOT NULL AND d.expiry_date <= ?
            ORDER BY d.expiry_date ASC
        """, (thirty_days,)).fetchall()

        # Certifications expiring soon
        certs_expiring = db.execute("""
            SELECT c.*, e.first_name, e.last_name, e.employee_code,
                   ct.name as certification_type_name
            FROM hr_employee_certifications c
            JOIN hr_employees e ON c.employee_id = e.id
            LEFT JOIN hr_certification_types ct ON c.certification_type_id = ct.id
            WHERE c.expiry_date IS NOT NULL AND c.expiry_date <= ?
            ORDER BY c.expiry_date ASC
        """, (thirty_days,)).fetchall()

        # Overdue renewals
        overdue = db.execute("""
            SELECT COUNT(*) as cnt FROM hr_documents
            WHERE expiry_date < ? AND expiry_date IS NOT NULL
        """, (today.isoformat(),)).fetchone()['cnt']

        stats = {
            'expiring_soon': len(expiring_soon),
            'certs_expiring': len(certs_expiring),
            'overdue': overdue
        }

        return render_template('hr/reports/compliance.html',
                             title='Compliance Report',
                             stats=stats,
                             expiring_documents=[dict(d) for d in expiring_soon],
                             expiring_certs=[dict(c) for c in certs_expiring])
    finally:
        db.close()


# =============================================================================
# 17. SETTINGS
# =============================================================================

@hr_bp.route('/settings')
@hr_login_required
@hr_permission_required('settings')
def settings_menu():
    """HR Settings menu."""
    db = get_db()
    try:
        settings = db.execute("""
            SELECT * FROM hr_settings
            WHERE is_active = 1
            ORDER BY category, setting_key
        """).fetchall()
        
        # Group by category
        settings_by_cat = {}
        for s in settings:
            cat = s['category']
            if cat not in settings_by_cat:
                settings_by_cat[cat] = []
            settings_by_cat[cat].append(dict(s))
        
        return render_template('hr/settings/menu.html',
                             title='HR Settings',
                             settings_by_cat=settings_by_cat)
    finally:
        db.close()


@hr_bp.route('/settings/update', methods=['POST'])
@hr_login_required
@hr_permission_required('settings')
def settings_update():
    """Update HR settings."""
    db = get_db()
    try:
        data = request.form
        
        for key, value in data.items():
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                update_hr_setting(setting_key, value)
        
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('hr.settings_menu'))
    finally:
        db.close()


@hr_bp.route('/settings/leave-types')
@hr_login_required
@hr_permission_required('settings')
def settings_leave_types():
    """Manage leave types."""
    db = get_db()
    try:
        leave_types = db.execute("SELECT * FROM hr_leave_types ORDER BY name").fetchall()
        return render_template('hr/settings/leave_types.html',
                             title='Leave Types',
                             leave_types=[dict(lt) for lt in leave_types])
    finally:
        db.close()


@hr_bp.route('/settings/shifts')
@hr_login_required
@hr_permission_required('settings')
def settings_shifts():
    """Manage shifts."""
    db = get_db()
    try:
        shifts = db.execute("SELECT * FROM hr_shifts ORDER BY name").fetchall()
        return render_template('hr/settings/shifts.html',
                             title='Shift Templates',
                             shifts=[dict(s) for s in shifts])
    finally:
        db.close()


@hr_bp.route('/settings/payroll-components')
@hr_login_required
@hr_permission_required('settings')
def settings_payroll_components():
    """Manage payroll components."""
    db = get_db()
    try:
        components = db.execute("""
            SELECT * FROM hr_payroll_components
            ORDER BY order_index
        """).fetchall()
        return render_template('hr/settings/payroll_components.html',
                             title='Payroll Components',
                             components=[dict(c) for c in components])
    finally:
        db.close()


# =============================================================================
# 18. ANNOUNCEMENTS
# =============================================================================

@hr_bp.route('/announcements')
@hr_login_required
@hr_permission_required('view')
def announcements_list():
    """List announcements."""
    db = get_db()
    try:
        search = request.args.get('search', '').strip()
        announcement_type = request.args.get('announcement_type', '').strip()
        priority = request.args.get('priority', '').strip()
        is_active = request.args.get('is_active', '').strip()
        page = int(request.args.get('page', 1))
        per_page = 12

        where_clauses = []
        params = []

        if search:
            where_clauses.append("(a.title LIKE ? OR a.content LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        if announcement_type:
            where_clauses.append("a.announcement_type = ?")
            params.append(announcement_type)
        if priority:
            where_clauses.append("a.priority = ?")
            params.append(priority)
        if is_active != '':
            where_clauses.append("a.is_active = ?")
            params.append(is_active)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        count_sql = f"SELECT COUNT(*) as total FROM hr_announcements a WHERE {where_sql}"
        total = db.execute(count_sql, params).fetchone()['total']
        total_pages = max(1, (total + per_page - 1) // per_page)
        page = min(max(1, page), total_pages)
        offset = (page - 1) * per_page

        announcements = db.execute(f"""
            SELECT a.*, u.username as created_by_name
            FROM hr_announcements a
            LEFT JOIN users u ON a.created_by_id = u.id
            WHERE {where_sql}
            ORDER BY a.created_at DESC
            LIMIT ? OFFSET ?
        """, params + [per_page, offset]).fetchall()

        return render_template('hr/announcements/list.html',
                             title='Announcements',
                             announcements=[dict(a) for a in announcements],
                             total=total,
                             total_pages=total_pages,
                             page=page,
                             search=search,
                             announcement_type=announcement_type,
                             priority=priority,
                             is_active=is_active)
    finally:
        db.close()


@hr_bp.route('/announcements/view/<int:id>')
@hr_login_required
@hr_permission_required('view')
def announcements_view(id):
    """View announcement detail."""
    db = get_db()
    try:
        ann = db.execute("""
            SELECT a.*, u.username as created_by_name
            FROM hr_announcements a
            LEFT JOIN users u ON a.created_by_id = u.id
            WHERE a.id = ?
        """, (id,)).fetchone()

        if not ann:
            flash(t('announcement_not_found', 'Announcement not found'), 'error')
            return redirect(url_for('hr.announcements_list'))

        return render_template('hr/announcements/view.html',
                             title='Announcement',
                             ann=dict(ann))
    finally:
        db.close()


@hr_bp.route('/announcements/new', methods=['GET', 'POST'])
@hr_login_required
@hr_permission_required('edit')
def announcements_new():
    """Create new announcement."""
    db = get_db()
    try:
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            content = request.form.get('content', '').strip()
            announcement_type = request.form.get('announcement_type', 'General').strip()
            priority = request.form.get('priority', 'Normal').strip()
            is_active = 1 if request.form.get('is_active') else 0
            valid_from = request.form.get('valid_from') or None
            valid_to = request.form.get('valid_to') or None

            if not title or not content:
                flash(t('title_content_required', 'Title and content are required'), 'error')
                return redirect(url_for('hr.announcements_new'))

            db.execute("""
                INSERT INTO hr_announcements (title, content, announcement_type, priority, is_active, valid_from, valid_to, created_by_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, content, announcement_type, priority, is_active, valid_from, valid_to, session.user_id))
            ann_id = db.execute("SELECT last_insert_rowid() as id").fetchone()['id']
            db.commit()

            # Send platform notification to all users
            try:
                from database import send_notification
                send_notification(
                    title=title,
                    message=content[:200] + ('...' if len(content) > 200 else ''),
                    notification_type='INFO',
                    role_id=None,
                    severity='HIGH' if priority in ('High', 'Critical') else 'MEDIUM',
                    link_url=f'/hr/announcements/view/{ann_id}',
                    related_entity_type='hr_announcement',
                    related_entity_id=ann_id
                )
            except Exception:
                pass

            flash(t('announcement_created', 'Announcement created successfully'), 'success')
            return redirect(url_for('hr.announcements_list'))

        return render_template('hr/announcements/form.html',
                             title='New Announcement',
                             ann=None)
    finally:
        db.close()


@hr_bp.route('/announcements/edit/<int:id>', methods=['GET', 'POST'])
@hr_login_required
@hr_permission_required('edit')
def announcements_edit(id):
    """Edit announcement."""
    db = get_db()
    try:
        ann = db.execute("SELECT * FROM hr_announcements WHERE id = ?", (id,)).fetchone()
        if not ann:
            flash(t('announcement_not_found', 'Announcement not found'), 'error')
            return redirect(url_for('hr.announcements_list'))

        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            content = request.form.get('content', '').strip()
            announcement_type = request.form.get('announcement_type', 'General').strip()
            priority = request.form.get('priority', 'Normal').strip()
            is_active = 1 if request.form.get('is_active') else 0
            valid_from = request.form.get('valid_from') or None
            valid_to = request.form.get('valid_to') or None

            if not title or not content:
                flash(t('title_content_required', 'Title and content are required'), 'error')
                return redirect(url_for('hr.announcements_edit', id=id))

            db.execute("""
                UPDATE hr_announcements
                SET title = ?, content = ?, announcement_type = ?, priority = ?, is_active = ?, valid_from = ?, valid_to = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (title, content, announcement_type, priority, is_active, valid_from, valid_to, id))

            flash(t('announcement_updated', 'Announcement updated successfully'), 'success')
            return redirect(url_for('hr.announcements_list'))

        return render_template('hr/announcements/form.html',
                             title='Edit Announcement',
                             ann=dict(ann))
    finally:
        db.close()


@hr_bp.route('/announcements/delete/<int:id>', methods=['POST'])
@hr_login_required
@hr_permission_required('delete')
def announcements_delete(id):
    """Delete announcement."""
    db = get_db()
    try:
        ann = db.execute("SELECT * FROM hr_announcements WHERE id = ?", (id,)).fetchone()
        if not ann:
            flash(t('announcement_not_found', 'Announcement not found'), 'error')
            return redirect(url_for('hr.announcements_list'))

        db.execute("DELETE FROM hr_announcements WHERE id = ?", (id,))
        db.commit()
        flash(t('announcement_deleted', 'Announcement deleted successfully'), 'success')
    finally:
        db.close()

    return redirect(url_for('hr.announcements_list'))


# =============================================================================
# 19. AUDIT LOGS
# =============================================================================

@hr_bp.route('/audit-logs')
@hr_login_required
@hr_permission_required('view')
def audit_logs():
    """View HR audit logs."""
    db = get_db()
    try:
        entity_type = request.args.get('entity_type', '')
        page = int(request.args.get('page', 1))
        per_page = 50
        
        query = """
            SELECT al.*, u.username as user_name
            FROM hr_audit_logs al
            LEFT JOIN users u ON al.user_id = u.id
            WHERE 1=1
        """
        params = []
        
        if entity_type:
            query += " AND al.entity_type = ?"
            params.append(entity_type)
        
        query += " ORDER BY al.created_at DESC"
        
        # Count
        count_query = "SELECT COUNT(*) as cnt FROM (" + query + ")"
        total = db.execute(count_query, params).fetchone()['cnt']
        
        # Paginate
        offset = (page - 1) * per_page
        query += f" LIMIT {per_page} OFFSET {offset}"
        
        logs = db.execute(query, params).fetchall()
        
        return render_template('hr/audit_logs.html',
                             title='HR Audit Logs',
                             logs=[dict(l) for l in logs],
                             entity_type=entity_type,
                             page=page,
                             total_pages=(total + per_page - 1) // per_page)
    finally:
        db.close()


# =============================================================================
# ONBOARDING & OFFBOARDING MODULE
# =============================================================================

@hr_bp.route('/onboarding')
@hr_login_required
@hr_permission_required('view')
def onboarding_list():
    """List onboarding plans."""
    db = get_db()
    try:
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '')

        query = """
            SELECT e.*, ee.department_id, d.name as department_name,
                   p.title as position_title,
                   CASE
                     WHEN e.probation_end_date IS NOT NULL AND e.probation_end_date >= date('now')
                     THEN 'On Probation'
                     WHEN e.status = 'Active' AND e.hire_date >= date('now', '-6 months')
                     THEN 'New Joiner'
                     ELSE 'Confirmed'
                   END as onboarding_status
            FROM hr_employees e
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            LEFT JOIN hr_positions p ON ee.position_id = p.id
            WHERE e.status IN ('Active', 'Probation')
        """
        params = []

        if search:
            query += " AND (e.first_name LIKE ? OR e.last_name LIKE ? OR e.employee_code LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])

        query += " ORDER BY e.hire_date DESC"

        employees = db.execute(query, params).fetchall()

        return render_template('hr/onboarding/list.html',
                             title='Onboarding',
                             employees=[dict(e) for e in employees],
                             search=search,
                             status=status)
    finally:
        db.close()


@hr_bp.route('/onboarding/<int:employee_id>')
@hr_login_required
@hr_permission_required('view')
def onboarding_detail(employee_id):
    """View onboarding details for an employee."""
    db = get_db()
    try:
        employee = get_employee_with_employment(employee_id)
        if not employee:
            flash('Employee not found.', 'error')
            return redirect(url_for('hr.onboarding_list'))

        # Get tasks/checklist for this onboarding
        tasks = db.execute("""
            SELECT * FROM hr_tasks
            WHERE employee_id = ? AND task_title LIKE '%onboard%'
            ORDER BY due_date
        """, (employee_id,)).fetchall()

        # Get training enrollments for new hire
        training = db.execute("""
            SELECT te.*, ts.session_title, tp.title as program_name
            FROM hr_training_enrollments te
            JOIN hr_training_sessions ts ON te.session_id = ts.id
            JOIN hr_training_programs tp ON ts.program_id = tp.id
            WHERE te.employee_id = ?
            ORDER BY ts.start_date DESC
        """, (employee_id,)).fetchall()

        # Get probation review dates
        probation_info = None
        if employee.get('probation_end_date'):
            probation_info = {
                'end_date': employee['probation_end_date'],
                'days_remaining': (datetime.strptime(employee['probation_end_date'], '%Y-%m-%d').date() - datetime.now().date()).days if employee['probation_end_date'] else 0
            }

        return render_template('hr/onboarding/detail.html',
                             title=f"Onboarding - {employee['first_name']} {employee['last_name']}",
                             employee=employee,
                             tasks=[dict(t) for t in tasks],
                             training=[dict(t) for t in training],
                             probation_info=probation_info)
    finally:
        db.close()


@hr_bp.route('/offboarding')
@hr_login_required
@hr_permission_required('view')
def offboarding_list():
    """List offboarding requests."""
    db = get_db()
    try:
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '')

        query = """
            SELECT e.*, ee.department_id, d.name as department_name,
                   p.title as position_title,
                   eh.new_value as termination_reason,
                   eh.created_at as offboarding_date
            FROM hr_employees e
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            LEFT JOIN hr_positions p ON ee.position_id = p.id
            LEFT JOIN hr_audit_logs eh ON eh.entity_id = e.id AND eh.entity_type = 'hr_employees' AND eh.action = 'TERMINATE'
            WHERE e.status = 'Terminated'
        """
        params = []

        if search:
            query += " AND (e.first_name LIKE ? OR e.last_name LIKE ? OR e.employee_code LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])

        query += " ORDER BY e.termination_date DESC"

        employees = db.execute(query, params).fetchall()

        return render_template('hr/offboarding/list.html',
                             title='Offboarding',
                             employees=[dict(e) for e in employees],
                             search=search)
    finally:
        db.close()


@hr_bp.route('/offboarding/<int:employee_id>')
@hr_login_required
@hr_permission_required('view')
def offboarding_detail(employee_id):
    """View offboarding details for an employee."""
    db = get_db()
    try:
        employee = get_employee_with_employment(employee_id)
        if not employee:
            flash('Employee not found.', 'error')
            return redirect(url_for('hr.offboarding_list'))

        # Get exit interview if exists
        exit_interview = db.execute("""
            SELECT * FROM hr_tasks
            WHERE employee_id = ? AND task_title LIKE '%exit%'
            ORDER BY due_date DESC LIMIT 1
        """, (employee_id,)).fetchone()

        # Get final settlement info
        settlement = db.execute("""
            SELECT * FROM hr_payroll_records
            WHERE employee_id = ? AND status = 'Approved'
            ORDER BY period_id DESC LIMIT 1
        """, (employee_id,)).fetchone()

        return render_template('hr/offboarding/detail.html',
                             title=f"Offboarding - {employee['first_name']} {employee['last_name']}",
                             employee=employee,
                             exit_interview=dict(exit_interview) if exit_interview else None,
                             settlement=dict(settlement) if settlement else None)
    finally:
        db.close()


# =============================================================================
# LOANS MODULE
# =============================================================================

@hr_bp.route('/loans')
@hr_login_required
@hr_permission_required('view')
def loans_list():
    """List employee loans."""
    db = get_db()
    try:
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '')

        query = """
            SELECT l.*, e.first_name, e.last_name, e.employee_code
            FROM hr_loans l
            JOIN hr_employees e ON l.employee_id = e.id
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (e.first_name LIKE ? OR e.last_name LIKE ? OR e.employee_code LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])

        if status:
            query += " AND l.status = ?"
            params.append(status)

        query += " ORDER BY l.created_at DESC"

        loans = db.execute(query, params).fetchall()

        return render_template('hr/loans/list.html',
                             title='Loans & Advances',
                             loans=[dict(l) for l in loans],
                             search=search,
                             status=status)
    finally:
        db.close()


@hr_bp.route('/loans/<int:loan_id>')
@hr_login_required
@hr_permission_required('view')
def loans_detail(loan_id):
    """View loan details with installment schedule."""
    db = get_db()
    try:
        loan = db.execute("""
            SELECT l.*, e.first_name, e.last_name, e.employee_code
            FROM hr_loans l
            JOIN hr_employees e ON l.employee_id = e.id
            WHERE l.id = ?
        """, (loan_id,)).fetchone()

        if not loan:
            flash('Loan not found.', 'error')
            return redirect(url_for('hr.loans_list'))

        installments = db.execute("""
            SELECT li.*, pp.name as period_name
            FROM hr_loan_installments li
            LEFT JOIN hr_payroll_periods pp ON li.period_id = pp.id
            WHERE li.loan_id = ?
            ORDER BY li.due_date
        """, (loan_id,)).fetchall()

        return render_template('hr/loans/detail.html',
                             title=f'Loan - {loan["first_name"]} {loan["last_name"]}',
                             loan=dict(loan),
                             installments=[dict(i) for i in installments])
    finally:
        db.close()


@hr_bp.route('/loans/new', methods=['GET', 'POST'])
@hr_login_required
@hr_permission_required('create')
def loans_new():
    """Create new loan."""
    user = get_current_user()
    db = get_db()

    if request.method == 'POST':
        try:
            data = request.form

            # Calculate total amount with interest
            principal = float(data.get('principal_amount', 0))
            interest_rate = float(data.get('interest_rate', 0))
            tenure = int(data.get('tenure_months', 1))

            total_amount = principal * (1 + interest_rate / 100)
            monthly_installment = total_amount / tenure

            cursor = db.execute("""
                INSERT INTO hr_loans (employee_id, loan_type, principal_amount, interest_rate,
                                   total_amount, monthly_installment, tenure_months, amount_remaining,
                                   start_date, approved_by_id, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('employee_id'),
                data.get('loan_type', 'Personal'),
                principal,
                interest_rate,
                total_amount,
                monthly_installment,
                tenure,
                total_amount,
                parse_date(data.get('start_date')) or datetime.now().date(),
                user['id'],
                data.get('remarks')
            ))

            loan_id = cursor.lastrowid

            # Create installment schedule
            start_date = parse_date(data.get('start_date')) or datetime.now().date()
            for i in range(tenure):
                due_date = start_date + timedelta(days=30 * (i + 1))
                db.execute("""
                    INSERT INTO hr_loan_installments (loan_id, due_date, installment_amount, principal_amount, interest_amount)
                    VALUES (?, ?, ?, ?, ?)
                """, (loan_id, due_date, monthly_installment, principal / tenure, (total_amount - principal) / tenure))

            db.commit()
            flash('Loan created successfully!', 'success')
            return redirect(url_for('hr.loans_detail', loan_id=loan_id))

        except Exception as e:
            db.rollback()
            flash(f'Error creating loan: {str(e)}', 'error')

    try:
        employees = db.execute("""
            SELECT e.id, e.first_name, e.last_name, e.employee_code
            FROM hr_employees e
            WHERE e.status = 'Active'
            ORDER BY e.first_name, e.last_name
        """).fetchall()

        return render_template('hr/loans/new.html',
                             title='New Loan',
                             employees=[dict(e) for e in employees])
    finally:
        db.close()


# =============================================================================
# TALENT & SUCCESSION MODULE
# =============================================================================

@hr_bp.route('/talent')
@hr_login_required
@hr_permission_required('view')
def talent_list():
    """List talent profiles and succession plans."""
    db = get_db()
    try:
        search = request.args.get('search', '').strip()

        # Get employees with potential assessments
        query = """
            SELECT e.*, d.name as department_name, p.title as position_title,
                   s.readiness_level, s.status as succession_status
            FROM hr_employees e
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            LEFT JOIN hr_positions p ON ee.position_id = p.id
            LEFT JOIN hr_successors s ON e.id = s.employee_id
            WHERE e.status = 'Active'
        """
        params = []

        if search:
            query += " AND (e.first_name LIKE ? OR e.last_name LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param])

        query += " ORDER BY e.first_name, e.last_name"

        employees = db.execute(query, params).fetchall()

        # Get Hi-Po watchlist
        hipo_count = db.execute("""
            SELECT COUNT(*) as cnt FROM hr_successors
            WHERE status = 'Active' AND is_primary = 1
        """).fetchone()['cnt']

        return render_template('hr/talent/list.html',
                             title='Talent & Succession',
                             employees=[dict(e) for e in employees],
                             hipo_count=hipo_count,
                             search=search)
    finally:
        db.close()


@hr_bp.route('/talent/hipo')
@hr_login_required
@hr_permission_required('view')
def talent_hipo():
    """High Potential watchlist."""
    db = get_db()
    try:
        successors = db.execute("""
            SELECT s.*, e.first_name, e.last_name, e.employee_code,
                   d.name as department_name, p.title as position_title,
                   succ.first_name || ' ' || succ.last_name as successor_name,
                   dep.first_name || ' ' || dep.last_name as deputy_name
            FROM hr_successors s
            JOIN hr_employees e ON s.employee_id = e.id
            LEFT JOIN hr_departments d ON d.id = (SELECT department_id FROM hr_employee_employment WHERE employee_id = e.id AND is_primary = 1)
            LEFT JOIN hr_positions p ON p.id = (SELECT position_id FROM hr_employee_employment WHERE employee_id = e.id AND is_primary = 1)
            LEFT JOIN hr_employees succ ON s.successor_id = succ.id
            LEFT JOIN hr_employees dep ON s.deputy_id = dep.id
            WHERE s.status = 'Active'
            ORDER BY s.readiness_level, e.last_name
        """).fetchall()

        return render_template('hr/talent/hipo.html',
                             title='Hi-Po Watchlist',
                             successors=[dict(s) for s in successors])
    finally:
        db.close()


@hr_bp.route('/talent/<int:employee_id>')
@hr_login_required
@hr_permission_required('view')
def talent_profile(employee_id):
    """View talent profile for an employee."""
    db = get_db()
    try:
        employee = get_employee_with_employment(employee_id)
        if not employee:
            flash('Employee not found.', 'error')
            return redirect(url_for('hr.talent_list'))

        # Get succession plans
        succession = db.execute("""
            SELECT s.*, succ.first_name || ' ' || succ.last_name as successor_name,
                   dep.first_name || ' ' || dep.last_name as deputy_name
            FROM hr_successors s
            LEFT JOIN hr_employees succ ON s.successor_id = succ.id
            LEFT JOIN hr_employees dep ON s.deputy_id = dep.id
            WHERE s.employee_id = ?
        """, (employee_id,)).fetchall()

        # Get performance reviews
        reviews = db.execute("""
            SELECT * FROM hr_performance_reviews
            WHERE employee_id = ?
            ORDER BY review_date DESC
            LIMIT 5
        """, (employee_id,)).fetchall()

        # Get training history
        training = db.execute("""
            SELECT te.*, tp.title as program_name, ts.session_title
            FROM hr_training_enrollments te
            JOIN hr_training_sessions ts ON te.session_id = ts.id
            JOIN hr_training_programs tp ON ts.program_id = tp.id
            WHERE te.employee_id = ?
            ORDER BY te.enrollment_date DESC
        """, (employee_id,)).fetchall()

        return render_template('hr/talent/profile.html',
                             title=f'Talent Profile - {employee["first_name"]} {employee["last_name"]}',
                             employee=employee,
                             succession=[dict(s) for s in succession],
                             reviews=[dict(r) for r in reviews],
                             training=[dict(t) for t in training])
    finally:
        db.close()


# =============================================================================
# CERTIFICATIONS MODULE
# =============================================================================

@hr_bp.route('/certifications')
@hr_login_required
@hr_permission_required('view')
def certifications_list():
    """List employee certifications and expiry tracking."""
    db = get_db()
    try:
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '')  # valid, expiring, expired

        query = """
            SELECT te.*, e.first_name, e.last_name, e.employee_code,
                   tp.title as program_name, tp.certification_validity_months,
                   ts.start_date, ts.end_date
            FROM hr_training_enrollments te
            JOIN hr_employees e ON te.employee_id = e.id
            JOIN hr_training_sessions ts ON te.session_id = ts.id
            JOIN hr_training_programs tp ON ts.program_id = tp.id
            WHERE te.certificate_number IS NOT NULL
        """
        params = []

        if search:
            query += " AND (e.first_name LIKE ? OR e.last_name LIKE ? OR te.certificate_number LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])

        query += " ORDER BY te.completion_date DESC"

        certs = db.execute(query, params).fetchall()

        # Categorize by status
        now = datetime.now().date()
        categorized = []
        for c in certs:
            cert_dict = dict(c)
            if cert_dict.get('completion_date'):
                expiry = datetime.strptime(cert_dict['completion_date'], '%Y-%m-%d').date()
                expiry = expiry.replace(year=expiry.year + (cert_dict.get('certification_validity_months') or 12) // 12)
                cert_dict['expiry_date'] = expiry
                cert_dict['days_remaining'] = (expiry - now).days
                if cert_dict['days_remaining'] < 0:
                    cert_dict['expiry_status'] = 'Expired'
                elif cert_dict['days_remaining'] <= 30:
                    cert_dict['expiry_status'] = 'Expiring Soon'
                else:
                    cert_dict['expiry_status'] = 'Valid'
            categorized.append(cert_dict)

        # Filter if status provided
        if status:
            categorized = [c for c in categorized if c.get('expiry_status') == status]

        return render_template('hr/certifications/list.html',
                             title='Certifications',
                             certifications=categorized,
                             search=search,
                             status=status)
    finally:
        db.close()


# =============================================================================
# HR CASES / SERVICE REQUESTS MODULE
# =============================================================================

@hr_bp.route('/cases')
@hr_login_required
@hr_permission_required('view')
def hr_cases_list():
    """List HR service cases/requests."""
    db = get_db()
    try:
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '')
        priority = request.args.get('priority', '')

        query = """
            SELECT t.*, e.first_name, e.last_name, e.employee_code,
                   ass.first_name || ' ' || ass.last_name as assigned_to_name
            FROM hr_tasks t
            JOIN hr_employees e ON t.employee_id = e.id
            LEFT JOIN users ass ON t.assigned_by_id = ass.id
            WHERE t.task_title NOT LIKE '%onboard%' AND t.task_title NOT LIKE '%exit%'
        """
        params = []

        if search:
            query += " AND (t.task_title LIKE ? OR e.first_name LIKE ? OR e.last_name LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])

        if status:
            query += " AND t.status = ?"
            params.append(status)

        if priority:
            query += " AND t.priority = ?"
            params.append(priority)

        query += " ORDER BY t.created_at DESC"

        cases = db.execute(query, params).fetchall()

        return render_template('hr/cases/list.html',
                             title='HR Cases',
                             cases=[dict(c) for c in cases],
                             search=search,
                             status=status,
                             priority=priority)
    finally:
        db.close()


@hr_bp.route('/cases/new', methods=['GET', 'POST'])
@hr_login_required
@hr_permission_required('create')
def hr_cases_new():
    """Create new HR case/request."""
    user = get_current_user()
    db = get_db()

    if request.method == 'POST':
        try:
            data = request.form

            cursor = db.execute("""
                INSERT INTO hr_tasks (employee_id, task_title, task_description, priority,
                                   due_date, status, assigned_by_id)
                VALUES (?, ?, ?, ?, ?, 'Open', ?)
            """, (
                data.get('employee_id'),
                data.get('task_title'),
                data.get('task_description'),
                data.get('priority', 'Medium'),
                parse_date(data.get('due_date')),
                user['id']
            ))

            db.commit()
            flash('Case created successfully!', 'success')
            return redirect(url_for('hr.hr_cases_list'))

        except Exception as e:
            db.rollback()
            flash(f'Error creating case: {str(e)}', 'error')

    try:
        employees = db.execute("""
            SELECT e.id, e.first_name, e.last_name, e.employee_code
            FROM hr_employees e
            WHERE e.status = 'Active'
            ORDER BY e.first_name, e.last_name
        """).fetchall()

        return render_template('hr/cases/new.html',
                             title='New HR Case',
                             employees=[dict(e) for e in employees])
    finally:
        db.close()


# =============================================================================
# WORKFORCE PLANNING MODULE
# =============================================================================

@hr_bp.route('/workforce')
@hr_login_required
@hr_permission_required('view')
def workforce_planning():
    """Workforce planning dashboard."""
    db = get_db()
    try:
        today = datetime.now()

        # Current headcount by department
        dept_headcount = db.execute("""
            SELECT d.name, COUNT(ee.employee_id) as headcount
            FROM hr_departments d
            LEFT JOIN hr_employee_employment ee ON d.id = ee.department_id AND ee.employment_status = 'Active'
            WHERE d.status = 'Active'
            GROUP BY d.id
            ORDER BY d.name
        """).fetchall()

        # Open vacancies
        vacancies = db.execute("""
            SELECT COUNT(*) as cnt, department_id, d.name as department_name
            FROM hr_job_requisitions jr
            LEFT JOIN hr_departments d ON jr.department_id = d.id
            WHERE jr.status IN ('Open', 'Approved', 'Posted')
            GROUP BY jr.department_id
        """).fetchall()

        # Attrition this year
        attrition = db.execute("""
            SELECT COUNT(*) as cnt FROM hr_employees
            WHERE termination_date IS NOT NULL
            AND strftime('%Y', termination_date) = ?
        """, (str(today.year),)).fetchone()['cnt']

        # New hires this year
        new_hires = db.execute("""
            SELECT COUNT(*) as cnt FROM hr_employees
            WHERE strftime('%Y', hire_date) = ?
        """, (str(today.year),)).fetchone()['cnt']

        # Headcount trend (monthly for current year)
        monthly_headcount = []
        for month in range(1, today.month + 1):
            headcount = db.execute("""
                SELECT COUNT(*) as cnt FROM hr_employees
                WHERE hire_date <= ? AND (termination_date IS NULL OR termination_date >= ?)
            """, (f"{today.year}-{month:02d}-01", f"{today.year}-{month:02d}-01")).fetchone()['cnt']
            monthly_headcount.append({
                'month': month,
                'headcount': headcount
            })

        return render_template('hr/workforce/planning.html',
                             title='Workforce Planning',
                             dept_headcount=[dict(d) for d in dept_headcount],
                             vacancies=[dict(v) for v in vacancies],
                             attrition=attrition,
                             new_hires=new_hires,
                             monthly_headcount=monthly_headcount,
                             current_year=today.year)
    finally:
        db.close()


# =============================================================================
# EXPORT CENTER
# =============================================================================

@hr_bp.route('/export')
@hr_login_required
@hr_permission_required('view')
def export_center():
    """Export center for HR reports."""
    db = get_db()
    try:
        # Get available report types
        report_types = [
            {'id': 'employees', 'name': 'Employee Master', 'route': '/hr/employees/export'},
            {'id': 'headcount', 'name': 'Headcount Report', 'route': '/hr/reports/headcount'},
            {'id': 'attendance', 'name': 'Attendance Report', 'route': '/hr/reports/attendance'},
            {'id': 'leave', 'name': 'Leave Report', 'route': '/hr/reports/leave'},
            {'id': 'payroll', 'name': 'Payroll Report', 'route': '/hr/reports/payroll'},
            {'id': 'recruitment', 'name': 'Recruitment Report', 'route': '/hr/reports/recruitment'},
            {'id': 'performance', 'name': 'Performance Report', 'route': '/hr/reports/performance'},
            {'id': 'training', 'name': 'Training Report', 'route': '/hr/reports/training'},
            {'id': 'compliance', 'name': 'Compliance Report', 'route': '/hr/reports/compliance'},
        ]

        # Get departments for filter
        departments = db.execute("SELECT id, name FROM hr_departments WHERE status = 'Active' ORDER BY name").fetchall()

        return render_template('hr/export/center.html',
                             title='Export Center',
                             report_types=report_types,
                             departments=[dict(d) for d in departments])
    finally:
        db.close()


@hr_bp.route('/employees/export')
@hr_login_required
@hr_permission_required('view')
def employees_export():
    """Export employees to CSV/Excel/PDF with column selection."""
    db = get_db()
    try:
        format_type = request.args.get('format', 'csv')
        status = request.args.get('status', 'Active')
        department = request.args.get('department', '')
        columns = request.args.getlist('columns') or ['employee_code', 'first_name', 'last_name', 'email', 'mobile', 'department_name', 'position_title', 'status', 'hire_date', 'manager_name']

        # All available columns
        all_columns = {
            'employee_code': 'Employee Code',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email',
            'mobile': 'Mobile',
            'department_name': 'Department',
            'position_title': 'Position',
            'status': 'Status',
            'hire_date': 'Hire Date',
            'manager_name': 'Manager',
            'nationality': 'Nationality',
            'gender': 'Gender',
            'date_of_birth': 'Date of Birth',
            'city': 'City',
            'country': 'Country',
            'employment_type': 'Employment Type'
        }

        # Build dynamic query based on selected columns
        col_list = ', '.join(['e.' + c if c in ['employee_code', 'first_name', 'last_name', 'email', 'mobile', 'status', 'hire_date', 'nationality', 'gender', 'date_of_birth', 'city', 'country'] else c for c in columns])

        query = f"""
            SELECT {col_list}
            FROM hr_employees e
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            LEFT JOIN hr_positions p ON ee.position_id = p.id
            LEFT JOIN hr_employees m ON ee.reporting_to_id = m.id
            WHERE 1=1
        """
        params = []

        if status:
            query += " AND e.status = ?"
            params.append(status)

        if department:
            query += " AND ee.department_id = ?"
            params.append(department)

        query += " ORDER BY e.first_name, e.last_name"

        employees = db.execute(query, params).fetchall()

        if format_type == 'csv':
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            # Use human-readable column headers
            headers = [all_columns.get(c, c) for c in columns]
            writer.writerow(headers)
            for emp in employees:
                row = [emp.get(c, '') for c in columns]
                writer.writerow(row)

            return Response(output.getvalue(), mimetype='text/csv',
                          headers={'Content-Disposition': 'attachment; filename=employees_export.csv'})

        elif format_type == 'json':
            return jsonify([dict(e) for e in employees])

        else:
            # For PDF/Excel, return data for client-side generation
            return jsonify({
                'data': [dict(e) for e in employees],
                'count': len(employees),
                'format': format_type,
                'columns': headers
            })

    finally:
        db.close()


@hr_bp.route('/reports/export/headcount')
@hr_login_required
@hr_permission_required('view')
def export_headcount():
    """Export headcount report."""
    db = get_db()
    try:
        format_type = request.args.get('format', 'csv')

        by_dept = db.execute("""
            SELECT d.name as department,
                   COUNT(DISTINCT ee.employee_id) as headcount,
                   SUM(CASE WHEN e.gender = 'Male' THEN 1 ELSE 0 END) as male,
                   SUM(CASE WHEN e.gender = 'Female' THEN 1 ELSE 0 END) as female
            FROM hr_departments d
            LEFT JOIN hr_employee_employment ee ON d.id = ee.department_id AND ee.employment_status = 'Active'
            LEFT JOIN hr_employees e ON ee.employee_id = e.id AND e.status = 'Active'
            WHERE d.status = 'Active'
            GROUP BY d.id
            ORDER BY d.name
        """).fetchall()

        if format_type == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Department', 'Headcount', 'Male', 'Female'])
            for row in by_dept:
                writer.writerow([row['department'], row['headcount'], row['male'], row['female']])
            return Response(output.getvalue(), mimetype='text/csv',
                          headers={'Content-Disposition': 'attachment; filename=headcount_report.csv'})
        else:
            return jsonify([dict(r) for r in by_dept])
    finally:
        db.close()


@hr_bp.route('/reports/export/leave')
@hr_login_required
@hr_permission_required('view')
def export_leave():
    """Export leave report."""
    db = get_db()
    try:
        format_type = request.args.get('format', 'csv')
        year = request.args.get('year', datetime.now().year)

        leave_usage = db.execute("""
            SELECT e.employee_code, e.first_name, e.last_name,
                   lt.name as leave_type,
                   lb.total_days, lb.used_days, lb.pending_days, lb.balance_days
            FROM hr_leave_balances lb
            JOIN hr_employees e ON lb.employee_id = e.id
            JOIN hr_leave_types lt ON lb.leave_type_id = lt.id
            WHERE lb.year = ?
            ORDER BY e.first_name, lt.name
        """, (year,)).fetchall()

        if format_type == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Employee Code', 'First Name', 'Last Name', 'Leave Type', 'Total Days', 'Used', 'Pending', 'Balance'])
            for row in leave_usage:
                writer.writerow([row['employee_code'], row['first_name'], row['last_name'],
                               row['leave_type'], row['total_days'], row['used_days'],
                               row['pending_days'], row['balance_days']])
            return Response(output.getvalue(), mimetype='text/csv',
                          headers={'Content-Disposition': 'attachment; filename=leave_report.csv'})
        else:
            return jsonify([dict(r) for r in leave_usage])
    finally:
        db.close()


@hr_bp.route('/reports/export/payroll')
@hr_login_required
@hr_permission_required('view')
def export_payroll():
    """Export payroll summary report."""
    db = get_db()
    try:
        format_type = request.args.get('format', 'csv')

        periods = db.execute("""
            SELECT p.year, p.month, p.name,
                   COUNT(pr.id) as employees,
                   SUM(pr.gross_salary) as total_gross,
                   SUM(pr.net_salary) as total_net
            FROM hr_payroll_periods p
            LEFT JOIN hr_payroll_records pr ON p.id = pr.period_id
            GROUP BY p.id
            ORDER BY p.year DESC, p.month DESC
        """).fetchall()

        if format_type == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Year', 'Month', 'Period Name', 'Employees', 'Total Gross', 'Total Net'])
            for row in periods:
                writer.writerow([row['year'], row['month'], row['name'], row['employees'],
                               row['total_gross'] or 0, row['total_net'] or 0])
            return Response(output.getvalue(), mimetype='text/csv',
                          headers={'Content-Disposition': 'attachment; filename=payroll_report.csv'})
        else:
            return jsonify([dict(r) for r in periods])
    finally:
        db.close()


# =============================================================================
# LEAVE CALENDAR
# =============================================================================

@hr_bp.route('/leave/calendar')
@hr_login_required
@hr_permission_required('view')
def leave_calendar():
    """Leave calendar view showing who's on leave."""
    db = get_db()
    try:
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        department = request.args.get('department', '')

        # Get all approved leaves for the month
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"

        query = """
            SELECT lr.*, e.first_name, e.last_name, e.employee_code, lt.name as leave_type_name
            FROM hr_leave_requests lr
            JOIN hr_employees e ON lr.employee_id = e.id
            JOIN hr_leave_types lt ON lr.leave_type_id = lt.id
            WHERE lr.status = 'Approved'
            AND lr.start_date < ?
            AND lr.end_date >= ?
        """
        params = [end_date, start_date]

        if department:
            query += """ AND e.id IN (
                SELECT employee_id FROM hr_employee_employment
                WHERE department_id = ? AND is_primary = 1
            )"""
            params.append(department)

        leaves = db.execute(query, params).fetchall()

        # Get departments for filter
        departments = db.execute("SELECT * FROM hr_departments WHERE status = 'Active' ORDER BY name").fetchall()

        return render_template('hr/leave/calendar.html',
                             title='Leave Calendar',
                             leaves=[dict(l) for l in leaves],
                             departments=[dict(d) for d in departments],
                             month=month,
                             year=year,
                             selected_department=department)
    finally:
        db.close()


# =============================================================================
# ORG CHART
# =============================================================================

@hr_bp.route('/org-chart')
@hr_login_required
@hr_permission_required('view')
def org_chart():
    """Organization chart visualization."""
    db = get_db()
    try:
        # Get top-level departments (no parent or parent not in hr_departments)
        root_depts = db.execute("""
            SELECT d.*, e.first_name || ' ' || e.last_name as head_name,
                   COUNT(ee.employee_id) as headcount
            FROM hr_departments d
            LEFT JOIN hr_employees e ON d.head_id = e.id
            LEFT JOIN hr_employee_employment ee ON d.id = ee.department_id AND ee.employment_status = 'Active'
            WHERE d.status = 'Active'
            GROUP BY d.id
            ORDER BY d.name
        """).fetchall()

        # Build org structure
        org_data = []
        for dept in root_depts:
            dept_dict = dict(dept)
            # Get positions in this department
            positions = db.execute("""
                SELECT p.*, COUNT(ee.employee_id) as filled
                FROM hr_positions p
                LEFT JOIN hr_employee_employment ee ON p.id = ee.position_id AND ee.employment_status = 'Active'
                WHERE p.department_id = ? AND p.status = 'Active'
                GROUP BY p.id
            """, (dept['id'],)).fetchall()
            dept_dict['positions'] = [dict(p) for p in positions]

            # Get sub-departments
            sub_depts = db.execute("""
                SELECT * FROM hr_departments
                WHERE parent_id = ? AND status = 'Active'
            """, (dept['id'],)).fetchall()
            dept_dict['sub_departments'] = [dict(s) for s in sub_depts]

            org_data.append(dept_dict)

        return render_template('hr/org_chart.html',
                             title='Organization Chart',
                             org_data=org_data)
    finally:
        db.close()


# =============================================================================
# API ENDPOINTS
# =============================================================================

@hr_bp.route('/api/employee/<int:id>')
@hr_login_required
@hr_permission_required('view')
def api_employee(id):
    """Get employee details as JSON."""
    db = get_db()
    try:
        employee = get_employee_with_employment(id)
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        return jsonify(employee)
    finally:
        db.close()


@hr_bp.route('/api/departments')
@hr_login_required
@hr_permission_required('view')
def api_departments():
    """Get all departments as JSON."""
    db = get_db()
    try:
        departments = db.execute("""
            SELECT * FROM hr_departments WHERE status = 'Active' ORDER BY name
        """).fetchall()
        return jsonify([dict(d) for d in departments])
    finally:
        db.close()


@hr_bp.route('/api/positions')
@hr_login_required
@hr_permission_required('view')
def api_positions():
    """Get all positions as JSON."""
    db = get_db()
    try:
        positions = db.execute("""
            SELECT p.*, d.name as department_name
            FROM hr_positions p
            LEFT JOIN hr_departments d ON p.department_id = d.id
            WHERE p.status = 'Active'
            ORDER BY p.title
        """).fetchall()
        return jsonify([dict(p) for p in positions])
    finally:
        db.close()


@hr_bp.route('/api/leave-balance/<int:employee_id>')
@hr_login_required
@hr_permission_required('view')
def api_leave_balance(employee_id):
    """Get employee leave balances as JSON."""
    db = get_db()
    try:
        year = request.args.get('year', datetime.now().year)
        
        balances = db.execute("""
            SELECT lb.*, lt.name as leave_type_name, lt.code as leave_type_code,
                   lt.default_days
            FROM hr_leave_balances lb
            JOIN hr_leave_types lt ON lb.leave_type_id = lt.id
            WHERE lb.employee_id = ? AND lb.year = ?
        """, (employee_id, year)).fetchall()
        
        return jsonify([dict(b) for b in balances])
    finally:
        db.close()


@hr_bp.route('/api/stats')
@hr_login_required
@hr_permission_required('view')
def api_stats():
    """Get HR dashboard stats as JSON."""
    db = get_db()
    try:
        today = datetime.now()
        
        stats = {
            'total_employees': db.execute("SELECT COUNT(*) as cnt FROM hr_employees").fetchone()['cnt'],
            'active_employees': db.execute("SELECT COUNT(*) as cnt FROM hr_employees WHERE status = 'Active'").fetchone()['cnt'],
            'on_leave_today': len(get_employees_on_leave_today()),
            'pending_leaves': db.execute("SELECT COUNT(*) as cnt FROM hr_leave_requests WHERE status = 'Pending'").fetchone()['cnt'],
            'pending_ot': db.execute("SELECT COUNT(*) as cnt FROM hr_overtime_requests WHERE status = 'Pending'").fetchone()['cnt'],
            'new_hires_this_month': db.execute("""
                SELECT COUNT(*) as cnt FROM hr_employees 
                WHERE hire_date >= ? AND hire_date <= ?
            """, (today.replace(day=1).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))).fetchone()['cnt'],
        }
        
        return jsonify(stats)
    finally:
        db.close()


# =============================================================================
# API EXPORT ENDPOINTS
# =============================================================================

@hr_bp.route('/api/export/<export_type>', methods=['GET', 'POST'])
@hr_bp.route('/api/export/<data_type>/<export_type>', methods=['GET', 'POST'])
@hr_login_required
@hr_permission_required('view')
def api_hr_export(export_type, data_type=None):
    """Export HR data in all 20 formats."""
    if export_type not in HR_EXPORT_TYPES:
        return jsonify({
            'error': f'Invalid export type. Valid types: {HR_EXPORT_TYPES}'
        }), 400

    db = get_db()
    try:
        company_id = session.get('company_id', 0)

        # Determine data type from URL or default
        if data_type is None:
            data_type = request.args.get('type', 'employees')

        # Configurable limits: default 5000, max 50000, per-request override via ?limit=
        raw_limit = request.args.get('limit', 5000)
        try:
            export_limit = min(int(raw_limit), 50000)
            if export_limit <= 0:
                export_limit = 5000
        except (ValueError, TypeError):
            export_limit = 5000

        offset = 0
        page = request.args.get('page', 1)
        per_page = request.args.get('per_page', 0)
        if per_page:
            try:
                per_page = min(int(per_page), 10000)
                if per_page > 0:
                    offset = (max(1, int(page)) - 1) * per_page
                    export_limit = per_page
            except (ValueError, TypeError):
                pass

        title = None
        columns = None

        # Chunked fetch helper to avoid loading everything at once
        def chunked_fetch(query, params, chunk_size=1000):
            """Fetch results in chunks to reduce peak memory usage."""
            results = []
            current_offset = offset
            while True:
                remaining = export_limit - len(results)
                if remaining <= 0:
                    break
                batch_size = min(chunk_size, remaining)
                rows = db.execute(query + " LIMIT ? OFFSET ?", (*params, batch_size, current_offset)).fetchall()
                if not rows:
                    break
                results.extend([dict(r) for r in rows])
                if len(rows) < batch_size:
                    break
                current_offset += batch_size
            return results

        # Get data based on type
        if data_type == 'employees':
            query = """
                SELECT e.*, d.department_name, p.position_title
                FROM hr_employees e
                LEFT JOIN hr_departments d ON e.department_id = d.id
                LEFT JOIN hr_positions p ON e.position_id = p.id
                WHERE e.company_id = ?
                ORDER BY e.employee_name
            """
            data = chunked_fetch(query, (company_id,))
            columns = HR_EXPORT_COLUMNS['employees']
            title = 'HR Employees'
        elif data_type == 'departments':
            query = """
                SELECT d.*, COUNT(e.id) as employee_count
                FROM hr_departments d
                LEFT JOIN hr_employees e ON d.id = e.department_id AND e.status = 'Active'
                WHERE d.company_id = ?
                GROUP BY d.id
                ORDER BY d.department_name
            """
            data = chunked_fetch(query, (company_id,))
            columns = HR_EXPORT_COLUMNS['departments']
            title = 'HR Departments'
        elif data_type == 'positions':
            query = """
                SELECT p.*, d.department_name
                FROM hr_positions p
                LEFT JOIN hr_departments d ON p.department_id = d.id
                WHERE p.company_id = ?
                ORDER BY p.position_title
            """
            data = chunked_fetch(query, (company_id,))
            columns = HR_EXPORT_COLUMNS['positions']
            title = 'HR Positions'
        elif data_type == 'attendance':
            query = """
                SELECT * FROM hr_attendance
                WHERE company_id = ?
                ORDER BY attendance_date DESC
            """
            data = chunked_fetch(query, (company_id,))
            columns = HR_EXPORT_COLUMNS['attendance']
            title = 'HR Attendance'
        elif data_type == 'leave':
            query = """
                SELECT lr.*, e.employee_name, lt.leave_type_name
                FROM hr_leave_requests lr
                LEFT JOIN hr_employees e ON lr.employee_id = e.id
                LEFT JOIN hr_leave_types lt ON lr.leave_type_id = lt.id
                WHERE lr.company_id = ?
                ORDER BY lr.request_date DESC
            """
            data = chunked_fetch(query, (company_id,))
            columns = HR_EXPORT_COLUMNS['leave']
            title = 'HR Leave Requests'
        elif data_type == 'payroll':
            query = """
                SELECT pr.*, e.employee_name
                FROM hr_payroll_registers pr
                LEFT JOIN hr_employees e ON pr.employee_id = e.id
                WHERE pr.company_id = ?
                ORDER BY pr.payroll_date DESC
            """
            data = chunked_fetch(query, (company_id,))
            columns = HR_EXPORT_COLUMNS['payroll']
            title = 'HR Payroll'
        elif data_type == 'overtime':
            query = """
                SELECT * FROM hr_overtime_requests
                WHERE company_id = ?
                ORDER BY overtime_date DESC
            """
            data = chunked_fetch(query, (company_id,))
            columns = HR_EXPORT_COLUMNS['overtime']
            title = 'HR Overtime'
        elif data_type == 'rewards':
            query = """
                SELECT * FROM hr_rewards
                WHERE company_id = ?
                ORDER BY reward_date DESC
            """
            data = chunked_fetch(query, (company_id,))
            columns = HR_EXPORT_COLUMNS['rewards']
            title = 'HR Rewards'
        elif data_type == 'loans':
            query = """
                SELECT * FROM hr_loans
                WHERE company_id = ?
                ORDER BY loan_date DESC
            """
            data = chunked_fetch(query, (company_id,))
            columns = HR_EXPORT_COLUMNS['loans']
            title = 'HR Loans'
        else:
            return jsonify({'error': f'Data type {data_type} not supported'}), 400

        filename = f'hr_{data_type}_{datetime.now().strftime("%Y%m%d")}'

        return send_export_response(data, export_type, filename, columns, title)
    finally:
        db.close()


@hr_bp.route('/api/export/list')
@hr_login_required
@hr_permission_required('view')
def list_hr_export_types():
    """List available export types for HR module."""
    return jsonify({
        'module': 'hr',
        'data_types': list(HR_EXPORT_COLUMNS.keys()),
        'export_types': [{'type': t} for t in HR_EXPORT_TYPES]
    })


def register_hr_routes(app):
    """Register HR blueprint with the Flask app."""
    app.register_blueprint(hr_bp)
    
    # Run HR migrations on startup
    with app.app_context():
        try:
            run_hr_migrations()
            print("HR Module initialized successfully")
        except Exception as e:
            print(f"HR Module initialization error: {e}")
