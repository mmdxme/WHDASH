"""
HR Recruitment Service
======================
Business logic for job requisitions, applicants, hiring pipeline
— extracted from hr_routes.py section 13 (Recruitment).
"""

from datetime import datetime


class HRRecruitmentService:
    """Handles all recruitment-related business logic."""

    def __init__(self, get_db):
        self.get_db = get_db

    def get_requisitions(self, filters=None):
        """Get job requisitions with filters."""
        db = self.get_db()
        filters = filters or {}

        query = """
            SELECT jr.*, d.name as department_name, p.title as position_title,
                   u.username as requested_by_name,
                   (SELECT COUNT(*) FROM hr_applicants a WHERE a.requisition_id = jr.id) as applicant_count
            FROM hr_job_requisitions jr
            LEFT JOIN hr_departments d ON jr.department_id = d.id
            LEFT JOIN hr_positions p ON jr.position_id = p.id
            LEFT JOIN users u ON jr.requested_by = u.id
            WHERE 1=1
        """
        params = []
        if filters.get('status'):
            query += " AND jr.status = ?"
            params.append(filters['status'])
        if filters.get('department_id'):
            query += " AND jr.department_id = ?"
            params.append(filters['department_id'])

        query += " ORDER BY jr.created_at DESC"
        return [dict(r) for r in db.execute(query, params).fetchall()]

    def get_applicants(self, requisition_id=None, filters=None):
        """Get applicants list, optionally for a specific requisition."""
        db = self.get_db()
        filters = filters or {}

        query = """
            SELECT a.*, jr.title as requisition_title,
                   d.name as department_name
            FROM hr_applicants a
            LEFT JOIN hr_job_requisitions jr ON a.requisition_id = jr.id
            LEFT JOIN hr_departments d ON jr.department_id = d.id
            WHERE 1=1
        """
        params = []
        if requisition_id:
            query += " AND a.requisition_id = ?"
            params.append(requisition_id)
        if filters.get('status'):
            query += " AND a.status = ?"
            params.append(filters['status'])

        query += " ORDER BY a.applied_date DESC"
        return [dict(r) for r in db.execute(query, params).fetchall()]

    def create_requisition(self, user_id, data):
        """Create a new job requisition."""
        db = self.get_db()
        now = datetime.now().isoformat()

        db.execute("""
            INSERT INTO hr_job_requisitions
            (title, department_id, position_id, vacancies,
             employment_type, description, requirements,
             salary_range_min, salary_range_max,
             status, requested_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Draft', ?, ?)
        """, (
            data['title'], data.get('department_id'),
            data.get('position_id'), data.get('vacancies', 1),
            data.get('employment_type', 'Full-time'),
            data.get('description'), data.get('requirements'),
            data.get('salary_range_min'), data.get('salary_range_max'),
            user_id, now
        ))
        req_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        db.commit()
        return req_id

    def update_applicant_status(self, applicant_id, new_status, user_id, notes=None):
        """Update applicant pipeline status."""
        db = self.get_db()
        now = datetime.now().isoformat()

        db.execute("""
            UPDATE hr_applicants
            SET status = ?, status_updated_by = ?,
                status_updated_at = ?, status_notes = ?,
                updated_at = ?
            WHERE id = ?
        """, (new_status, user_id, now, notes, now, applicant_id))
        db.commit()
