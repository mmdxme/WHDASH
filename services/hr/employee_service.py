"""
HR Employee Service
===================
Business logic for employee CRUD, employment records, documents
— extracted from hr_routes.py sections 2 (Employees) and 12 (Documents).
"""

from datetime import datetime


class HREmployeeService:
    """Handles all employee-related business logic."""

    def __init__(self, get_db):
        self.get_db = get_db

    def get_employees(self, filters=None):
        """Get paginated employee list with filters."""
        db = self.get_db()
        filters = filters or {}

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

        if filters.get('search'):
            query += (" AND (e.first_name LIKE ? OR e.last_name LIKE ? "
                      "OR e.employee_code LIKE ? OR e.email LIKE ?)")
            s = f"%{filters['search']}%"
            params.extend([s, s, s, s])

        if filters.get('status'):
            query += " AND e.status = ?"
            params.append(filters['status'])

        if filters.get('department'):
            query += " AND ee.department_id = ?"
            params.append(filters['department'])

        # Count
        count_query = query.replace(
            "SELECT e.*,", "SELECT COUNT(*) as cnt FROM hr_employees e"
        ).split("FROM hr_employees e", 1)
        count_sql = "SELECT COUNT(*) as cnt FROM hr_employees e" + count_query[1].split("WHERE", 1)[0] + " WHERE" + query.split("WHERE", 1)[1]
        # Simpler approach
        all_rows = db.execute(query + " ORDER BY e.first_name, e.last_name", params).fetchall()
        total = len(all_rows)

        page = int(filters.get('page', 1))
        per_page = int(filters.get('per_page', 20))
        offset = (page - 1) * per_page

        query += f" ORDER BY e.first_name, e.last_name LIMIT {per_page} OFFSET {offset}"
        employees = db.execute(query, params).fetchall()

        return {
            'employees': [dict(e) for e in employees],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
        }

    def get_employee_detail(self, employee_id):
        """Get full employee profile with all related data."""
        db = self.get_db()

        employee = db.execute("""
            SELECT e.*, d.name as department_name, p.title as position_title,
                   c.name as company_name, s.name as shift_name,
                   m.first_name || ' ' || m.last_name as manager_name
            FROM hr_employees e
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            LEFT JOIN hr_positions p ON ee.position_id = p.id
            LEFT JOIN companies c ON ee.company_id = c.id
            LEFT JOIN hr_shifts s ON ee.shift_id = s.id
            LEFT JOIN hr_employees m ON ee.reporting_to_id = m.id
            WHERE e.id = ?
        """, (employee_id,)).fetchone()

        if not employee:
            return None

        result = dict(employee)

        # Employment records
        result['employment_records'] = [dict(r) for r in db.execute("""
            SELECT ee.*, d.name as department_name, p.title as position_title,
                   s.name as shift_name,
                   m.first_name || ' ' || m.last_name as manager_name
            FROM hr_employee_employment ee
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            LEFT JOIN hr_positions p ON ee.position_id = p.id
            LEFT JOIN hr_shifts s ON ee.shift_id = s.id
            LEFT JOIN hr_employees m ON ee.reporting_to_id = m.id
            WHERE ee.employee_id = ?
            ORDER BY ee.is_primary DESC, ee.start_date DESC
        """, (employee_id,)).fetchall()]

        # Documents
        result['documents'] = [dict(r) for r in db.execute("""
            SELECT * FROM hr_employee_documents
            WHERE employee_id = ?
            ORDER BY expiry_date IS NOT NULL, expiry_date, created_at DESC
        """, (employee_id,)).fetchall()]

        # Leave balances
        current_year = datetime.now().year
        result['leave_balances'] = [dict(r) for r in db.execute("""
            SELECT lb.*, lt.name as leave_type_name, lt.code as leave_type_code
            FROM hr_leave_balances lb
            JOIN hr_leave_types lt ON lb.leave_type_id = lt.id
            WHERE lb.employee_id = ? AND lb.year = ?
        """, (employee_id, current_year)).fetchall()]

        # Recent leave requests
        result['leave_requests'] = [dict(r) for r in db.execute("""
            SELECT lr.*, lt.name as leave_type_name
            FROM hr_leave_requests lr
            JOIN hr_leave_types lt ON lr.leave_type_id = lt.id
            WHERE lr.employee_id = ?
            ORDER BY lr.created_at DESC LIMIT 10
        """, (employee_id,)).fetchall()]

        return result

    def create_employee(self, user_id, data):
        """Create a new employee with employment record and leave balances."""
        db = self.get_db()

        # Generate employee code
        employee_code = data.get('employee_code')
        if not employee_code:
            employee_code = self._generate_employee_code(db)

        cursor = db.execute("""
            INSERT INTO hr_employees (
                employee_code, first_name, middle_name, last_name,
                preferred_name, arabic_name, gender, nationality,
                date_of_birth, marital_status, mobile, email,
                emergency_contact_name, emergency_contact_phone,
                address, city, country, passport_number, passport_expiry,
                emirates_id, visa_number, visa_expiry, labour_card_number,
                bank_name, bank_account_number, iban,
                status, employment_type, hire_date,
                confirmation_date, probation_end_date, notes
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            employee_code,
            data.get('first_name'), data.get('middle_name'),
            data.get('last_name'), data.get('preferred_name'),
            data.get('arabic_name'), data.get('gender'),
            data.get('nationality'), data.get('date_of_birth'),
            data.get('marital_status'), data.get('mobile'),
            data.get('email'), data.get('emergency_contact_name'),
            data.get('emergency_contact_phone'), data.get('address'),
            data.get('city'), data.get('country'),
            data.get('passport_number'), data.get('passport_expiry'),
            data.get('emirates_id'), data.get('visa_number'),
            data.get('visa_expiry'), data.get('labour_card_number'),
            data.get('bank_name'), data.get('bank_account_number'),
            data.get('iban'), data.get('status', 'Active'),
            data.get('employment_type', 'Full-time'),
            data.get('hire_date'), data.get('confirmation_date'),
            data.get('probation_end_date'), data.get('notes')
        ))
        employee_id = cursor.lastrowid

        # Primary employment record
        db.execute("""
            INSERT INTO hr_employee_employment (
                employee_id, company_id, department_id, position_id,
                shift_id, reporting_to_id, employment_status,
                contract_type, start_date, is_primary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            employee_id, data.get('company_id'),
            data.get('department_id'), data.get('position_id'),
            data.get('shift_id'), data.get('reporting_to_id'),
            data.get('employment_status', 'Active'),
            data.get('contract_type', 'Permanent'),
            data.get('hire_date') or datetime.now().strftime('%Y-%m-%d')
        ))

        # Initialize leave balances
        leave_types = db.execute(
            "SELECT id, default_days FROM hr_leave_types WHERE is_active = 1"
        ).fetchall()
        current_year = datetime.now().year
        for lt in leave_types:
            db.execute("""
                INSERT INTO hr_leave_balances
                (employee_id, leave_type_id, year, total_days)
                VALUES (?, ?, ?, ?)
            """, (employee_id, lt['id'], current_year, lt['default_days']))

        db.commit()

        from hr_models import log_hr_audit
        log_hr_audit('hr_employees', employee_id, 'CREATE', user_id,
                     new_value=f"Employee {employee_code} created")

        return employee_id, employee_code

    def get_departments(self, active_only=True):
        """Get list of departments."""
        db = self.get_db()
        if active_only:
            return [dict(r) for r in db.execute(
                "SELECT * FROM hr_departments WHERE status = 'Active' ORDER BY name"
            ).fetchall()]
        return [dict(r) for r in db.execute(
            "SELECT * FROM hr_departments ORDER BY name"
        ).fetchall()]

    def get_positions(self, active_only=True):
        """Get list of positions."""
        db = self.get_db()
        if active_only:
            return [dict(r) for r in db.execute(
                "SELECT * FROM hr_positions WHERE status = 'Active' ORDER BY title"
            ).fetchall()]
        return [dict(r) for r in db.execute(
            "SELECT * FROM hr_positions ORDER BY title"
        ).fetchall()]

    def _generate_employee_code(self, db, prefix='EMP'):
        """Generate a unique sequential employee code."""
        current_year = datetime.now().year
        year_prefix = f'{prefix}{current_year}'
        row = db.execute("""
            SELECT employee_code FROM hr_employees
            WHERE employee_code LIKE ?
            ORDER BY employee_code DESC LIMIT 1
        """, (f'{year_prefix}%',)).fetchone()

        if row and row['employee_code']:
            suffix_str = row['employee_code'][len(year_prefix):]
            try:
                next_seq = int(suffix_str) + 1
            except ValueError:
                next_seq = 1
        else:
            next_seq = 1
        return f'{year_prefix}{next_seq:04d}'
