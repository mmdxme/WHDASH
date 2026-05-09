"""
HR Attendance Service
=====================
Business logic for attendance tracking, check-in/out, reports
— extracted from hr_routes.py section 5 (Attendance).
"""

from datetime import datetime, timedelta


class HRAttendanceService:
    """Handles all attendance-related business logic."""

    def __init__(self, get_db):
        self.get_db = get_db

    def get_attendance_records(self, filters=None):
        """Get attendance records with filters."""
        db = self.get_db()
        filters = filters or {}

        query = """
            SELECT ar.*, e.first_name, e.last_name, e.employee_code,
                   d.name as department_name
            FROM hr_attendance_records ar
            JOIN hr_employees e ON ar.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            WHERE 1=1
        """
        params = []

        if filters.get('date'):
            query += " AND ar.date = ?"
            params.append(filters['date'])
        elif filters.get('date_from') and filters.get('date_to'):
            query += " AND ar.date BETWEEN ? AND ?"
            params.extend([filters['date_from'], filters['date_to']])
        else:
            query += " AND ar.date = ?"
            params.append(datetime.now().strftime('%Y-%m-%d'))

        if filters.get('department_id'):
            query += " AND ee.department_id = ?"
            params.append(filters['department_id'])

        if filters.get('status'):
            query += " AND ar.status = ?"
            params.append(filters['status'])

        query += " ORDER BY e.first_name, e.last_name"
        return [dict(r) for r in db.execute(query, params).fetchall()]

    def get_today_summary(self):
        """Get attendance summary for today."""
        db = self.get_db()
        today = datetime.now().strftime('%Y-%m-%d')

        summary = db.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present,
                SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent,
                SUM(CASE WHEN late_minutes > 0 THEN 1 ELSE 0 END) as late
            FROM hr_attendance_records
            WHERE date = ?
        """, (today,)).fetchone()

        return dict(summary) if summary else {
            'total': 0, 'present': 0, 'absent': 0, 'late': 0
        }

    def record_check_in(self, employee_id, user_id, check_time=None):
        """Record employee check-in."""
        db = self.get_db()
        now = datetime.now()
        check_time = check_time or now.strftime('%H:%M:%S')
        today = now.strftime('%Y-%m-%d')

        existing = db.execute("""
            SELECT id FROM hr_attendance_records
            WHERE employee_id = ? AND date = ?
        """, (employee_id, today)).fetchone()

        if existing:
            db.execute("""
                UPDATE hr_attendance_records
                SET check_in = ?, status = 'Present', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (check_time, existing['id']))
        else:
            db.execute("""
                INSERT INTO hr_attendance_records
                (employee_id, date, check_in, status, created_at)
                VALUES (?, ?, ?, 'Present', CURRENT_TIMESTAMP)
            """, (employee_id, today, check_time))

        db.commit()

    def record_check_out(self, employee_id, user_id, check_time=None):
        """Record employee check-out."""
        db = self.get_db()
        now = datetime.now()
        check_time = check_time or now.strftime('%H:%M:%S')
        today = now.strftime('%Y-%m-%d')

        record = db.execute("""
            SELECT id, check_in FROM hr_attendance_records
            WHERE employee_id = ? AND date = ?
        """, (employee_id, today)).fetchone()

        if not record:
            raise ValueError('No check-in record found for today.')

        # Calculate hours worked
        hours_worked = 0
        if record['check_in']:
            try:
                cin = datetime.strptime(record['check_in'], '%H:%M:%S')
                cout = datetime.strptime(check_time, '%H:%M:%S')
                hours_worked = (cout - cin).total_seconds() / 3600
            except ValueError:
                pass

        db.execute("""
            UPDATE hr_attendance_records
            SET check_out = ?, hours_worked = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (check_time, round(hours_worked, 2), record['id']))

        db.commit()

    def get_monthly_summary(self, employee_id, year, month):
        """Get monthly attendance summary for an employee."""
        db = self.get_db()
        month_str = f"{year}-{month:02d}"

        summary = db.execute("""
            SELECT
                COUNT(*) as total_days,
                SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present,
                SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent,
                SUM(CASE WHEN late_minutes > 0 THEN 1 ELSE 0 END) as late,
                SUM(hours_worked) as total_hours,
                SUM(overtime_hours) as overtime_hours
            FROM hr_attendance_records
            WHERE employee_id = ? AND strftime('%Y-%m', date) = ?
        """, (employee_id, month_str)).fetchone()

        return dict(summary) if summary else None
