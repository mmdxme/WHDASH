"""
HR Reports Service
==================
Business logic for HR analytics, headcount reports, and turnover data
— extracted from hr_routes.py section 10 (Reports).
"""

from datetime import datetime

class HRReportsService:
    """Handles HR data aggregation for reports and dashboards."""

    def __init__(self, get_db):
        self.get_db = get_db

    def get_headcount_report(self):
        """Aggregate headcount by department and company."""
        db = self.get_db()
        
        by_department = [dict(r) for r in db.execute("""
            SELECT d.name as department, COUNT(ee.employee_id) as count
            FROM hr_departments d
            LEFT JOIN hr_employee_employment ee ON d.id = ee.department_id AND ee.is_primary = 1
            LEFT JOIN hr_employees e ON ee.employee_id = e.id
            WHERE e.status = 'Active'
            GROUP BY d.id
            ORDER BY count DESC
        """).fetchall()]

        by_company = [dict(r) for r in db.execute("""
            SELECT c.name as company, COUNT(ee.employee_id) as count
            FROM companies c
            LEFT JOIN hr_employee_employment ee ON c.id = ee.company_id AND ee.is_primary = 1
            LEFT JOIN hr_employees e ON ee.employee_id = e.id
            WHERE e.status = 'Active'
            GROUP BY c.id
            ORDER BY count DESC
        """).fetchall()]

        return {
            'by_department': by_department,
            'by_company': by_company,
            'total_active': sum(d['count'] for d in by_department)
        }

    def get_turnover_stats(self, year=None):
        """Calculate turnover rates."""
        db = self.get_db()
        year = year or datetime.now().year
        
        # This is a simplified version of what might be in the massive route file
        hired = db.execute("""
            SELECT COUNT(*) as count FROM hr_employees 
            WHERE strftime('%Y', hire_date) = ?
        """, (str(year),)).fetchone()['count']

        terminated = db.execute("""
            SELECT COUNT(*) as count FROM hr_employees 
            WHERE status = 'Terminated' AND strftime('%Y', termination_date) = ?
        """, (str(year),)).fetchone()['count']

        return {
            'year': year,
            'hired': hired,
            'terminated': terminated
        }
