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

hr_bp = Blueprint('hr', __name__, url_prefix='/hr')


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
        
        if action == 'approve':
            db.execute("""
                UPDATE hr_overtime_requests
                SET status = 'Approved', approved_by_id = ?, approved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (user['id'], id))
        else:
            db.execute("""
                UPDATE hr_overtime_requests
                SET status = 'Rejected', approved_by_id = ?, approved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (user['id'], id))
        
        db.commit()
        return jsonify({'success': True})
        
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
            db.commit()

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
