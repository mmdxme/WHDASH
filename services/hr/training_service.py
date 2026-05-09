"""
HR Training Service
===================
Business logic for training programs, enrollment, tracking
— extracted from hr_routes.py section 11 (Training).
"""

from datetime import datetime


class HRTrainingService:
    """Handles all training-related business logic."""

    def __init__(self, get_db):
        self.get_db = get_db

    def get_programs(self, filters=None):
        """Get training programs with filters."""
        db = self.get_db()
        filters = filters or {}

        query = """
            SELECT tp.*,
                   (SELECT COUNT(*) FROM hr_training_enrollments te
                    WHERE te.program_id = tp.id) as enrolled_count
            FROM hr_training_programs tp
            WHERE 1=1
        """
        params = []
        if filters.get('status'):
            query += " AND tp.status = ?"
            params.append(filters['status'])
        if filters.get('category'):
            query += " AND tp.category = ?"
            params.append(filters['category'])

        query += " ORDER BY tp.start_date DESC"
        return [dict(r) for r in db.execute(query, params).fetchall()]

    def get_program_detail(self, program_id):
        """Get training program with enrollments."""
        db = self.get_db()
        program = db.execute(
            "SELECT * FROM hr_training_programs WHERE id = ?", (program_id,)
        ).fetchone()
        if not program:
            return None

        result = dict(program)
        result['enrollments'] = [dict(r) for r in db.execute("""
            SELECT te.*, e.first_name, e.last_name, e.employee_code
            FROM hr_training_enrollments te
            JOIN hr_employees e ON te.employee_id = e.id
            WHERE te.program_id = ?
            ORDER BY e.first_name
        """, (program_id,)).fetchall()]

        return result

    def enroll_employee(self, program_id, employee_id, user_id):
        """Enroll an employee in a training program."""
        db = self.get_db()
        now = datetime.now().isoformat()

        existing = db.execute("""
            SELECT id FROM hr_training_enrollments
            WHERE program_id = ? AND employee_id = ?
        """, (program_id, employee_id)).fetchone()

        if existing:
            raise ValueError('Employee is already enrolled in this program.')

        db.execute("""
            INSERT INTO hr_training_enrollments
            (program_id, employee_id, enrollment_date, status, enrolled_by, created_at)
            VALUES (?, ?, ?, 'Enrolled', ?, ?)
        """, (program_id, employee_id, now, user_id, now))
        db.commit()
