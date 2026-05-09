"""
HR Leave Service
================
Business logic for leave management, balances, approvals
— extracted from hr_routes.py section 6 (Leave Management).
"""

from datetime import datetime


class HRLeaveService:
    """Handles all leave-related business logic."""

    def __init__(self, get_db):
        self.get_db = get_db

    def get_leave_requests(self, filters=None):
        """Get leave requests with filters."""
        db = self.get_db()
        filters = filters or {}

        query = """
            SELECT lr.*, lt.name as leave_type_name, lt.code as leave_type_code,
                   e.first_name, e.last_name, e.employee_code,
                   d.name as department_name,
                   u.username as approved_by_name
            FROM hr_leave_requests lr
            JOIN hr_leave_types lt ON lr.leave_type_id = lt.id
            JOIN hr_employees e ON lr.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            LEFT JOIN users u ON lr.approved_by = u.id
            WHERE 1=1
        """
        params = []

        if filters.get('status'):
            query += " AND lr.status = ?"
            params.append(filters['status'])
        if filters.get('employee_id'):
            query += " AND lr.employee_id = ?"
            params.append(filters['employee_id'])
        if filters.get('department_id'):
            query += " AND ee.department_id = ?"
            params.append(filters['department_id'])

        query += " ORDER BY lr.created_at DESC"

        page = int(filters.get('page', 1))
        per_page = int(filters.get('per_page', 20))
        all_rows = db.execute(query, params).fetchall()
        total = len(all_rows)

        query += f" LIMIT {per_page} OFFSET {(page - 1) * per_page}"
        items = db.execute(query, params).fetchall()

        return {
            'items': [dict(r) for r in items],
            'total': total,
            'page': page,
            'total_pages': (total + per_page - 1) // per_page,
        }

    def create_leave_request(self, employee_id, data, user_id):
        """Create a new leave request."""
        db = self.get_db()
        now = datetime.now().isoformat()

        # Validate leave balance
        leave_type_id = data['leave_type_id']
        days = float(data['total_days'])
        current_year = datetime.now().year

        balance = db.execute("""
            SELECT * FROM hr_leave_balances
            WHERE employee_id = ? AND leave_type_id = ? AND year = ?
        """, (employee_id, leave_type_id, current_year)).fetchone()

        if balance:
            available = (balance['total_days'] or 0) - (balance['used_days'] or 0)
            if days > available:
                raise ValueError(
                    f'Insufficient leave balance. Available: {available} days, '
                    f'Requested: {days} days.'
                )

        db.execute("""
            INSERT INTO hr_leave_requests
            (employee_id, leave_type_id, start_date, end_date,
             total_days, reason, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?, ?)
        """, (employee_id, leave_type_id,
              data['start_date'], data['end_date'],
              days, data.get('reason', ''), now, now))

        request_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        db.commit()

        from hr_models import log_hr_audit
        log_hr_audit('hr_leave_requests', request_id, 'CREATE', user_id,
                     new_value=f"Leave request for {days} days")

        return request_id

    def approve_leave(self, request_id, approver_id, notes=None):
        """Approve a leave request and deduct from balance."""
        db = self.get_db()
        now = datetime.now().isoformat()

        req = db.execute(
            "SELECT * FROM hr_leave_requests WHERE id = ?", (request_id,)
        ).fetchone()
        if not req:
            raise ValueError('Leave request not found.')
        if req['status'] != 'Pending':
            raise ValueError('Leave request is not pending.')

        # Approve
        db.execute("""
            UPDATE hr_leave_requests
            SET status = 'Approved', approved_by = ?, approved_at = ?,
                approval_notes = ?, updated_at = ?
            WHERE id = ?
        """, (approver_id, now, notes, now, request_id))

        # Deduct from balance
        current_year = datetime.now().year
        db.execute("""
            UPDATE hr_leave_balances
            SET used_days = used_days + ?
            WHERE employee_id = ? AND leave_type_id = ? AND year = ?
        """, (req['total_days'], req['employee_id'],
              req['leave_type_id'], current_year))

        db.commit()

    def reject_leave(self, request_id, rejector_id, reason=None):
        """Reject a leave request."""
        db = self.get_db()
        now = datetime.now().isoformat()

        db.execute("""
            UPDATE hr_leave_requests
            SET status = 'Rejected', approved_by = ?, approved_at = ?,
                approval_notes = ?, updated_at = ?
            WHERE id = ? AND status = 'Pending'
        """, (rejector_id, now, reason, now, request_id))
        db.commit()

    def get_employee_balances(self, employee_id, year=None):
        """Get leave balances for an employee."""
        db = self.get_db()
        year = year or datetime.now().year

        return [dict(r) for r in db.execute("""
            SELECT lb.*, lt.name as leave_type_name, lt.code as leave_type_code,
                   (lb.total_days - COALESCE(lb.used_days, 0)) as remaining_days
            FROM hr_leave_balances lb
            JOIN hr_leave_types lt ON lb.leave_type_id = lt.id
            WHERE lb.employee_id = ? AND lb.year = ?
        """, (employee_id, year)).fetchall()]
