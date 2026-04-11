"""
HR Module Database Models and Migrations
=========================================
This file contains all HR-related database table definitions and migration functions.
Tables are designed to be added to the existing SQLite database without conflicts.

HR Tables:
- hr_departments: Company departments/org structure
- hr_positions: Job titles and positions
- hr_employees: Employee master data
- hr_employee_employment: Employment details per employee
- hr_shifts: Work shifts templates
- hr_attendance_records: Daily attendance data
- hr_leave_types: Types of leave (annual, sick, etc.)
- hr_leave_requests: Leave request records
- hr_payroll_periods: Monthly payroll periods
- hr_payroll_records: Payroll records per employee per period
- hr_payroll_components: Salary components (basic, allowances, deductions)
- hr_overtime_requests: Overtime requests
- hr_bonus_records: Bonuses and rewards
- hr_deduction_records: Deductions and penalties
- hr_loans: Employee loans/advances
- hr_loan_installments: Loan installment schedule
- hr_training_programs: Training program definitions
- hr_training_sessions: Scheduled training sessions
- hr_training_enrollments: Employee enrollments in training
- hr_employee_documents: Employee document management
- hr_announcements: HR announcements/notices
- hr_candidates: Recruitment candidates
- hr_job_requisitions: Job requisitions/vacancies
- hr_approvals: Approval workflow records
- hr_settings: HR configurable settings
- hr_kpis: KPI definitions
- hr_performance_reviews: Performance review records
- hr_successors: Successor/deputy planning
- hr_audit_logs: Audit trail for HR changes
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'warehouse.db'))


def get_db():
    """Get database connection with Row factory for dict-like access."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# =============================================================================
# HR TABLE DEFINITIONS
# =============================================================================

HR_TABLES = [
    # -------------------------------------------------------------------------
    # 1. HR Departments - Organizational Structure
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        parent_id INTEGER,
        code TEXT,
        description TEXT,
        head_id INTEGER,
        budget DECIMAL(12,2) DEFAULT 0,
        cost_center TEXT,
        status TEXT DEFAULT 'Active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_id) REFERENCES hr_departments(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 2. HR Positions - Job Titles
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        department_id INTEGER,
        description TEXT,
        salary_band_min DECIMAL(12,2) DEFAULT 0,
        salary_band_max DECIMAL(12,2) DEFAULT 0,
        grade TEXT,
        is_critical INTEGER DEFAULT 0,
        requires_successor INTEGER DEFAULT 0,
        status TEXT DEFAULT 'Active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (department_id) REFERENCES hr_departments(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 3. HR Employees - Employee Master
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_code TEXT UNIQUE,
        user_id INTEGER,
        first_name TEXT NOT NULL,
        middle_name TEXT,
        last_name TEXT NOT NULL,
        preferred_name TEXT,
        arabic_name TEXT,
        gender TEXT,
        nationality TEXT,
        date_of_birth DATE,
        marital_status TEXT,
        mobile TEXT,
        email TEXT,
        emergency_contact_name TEXT,
        emergency_contact_phone TEXT,
        address TEXT,
        city TEXT,
        country TEXT,
        passport_number TEXT,
        passport_expiry DATE,
        emirates_id TEXT,
        visa_number TEXT,
        visa_expiry DATE,
        labour_card_number TEXT,
        photo TEXT,
        bank_name TEXT,
        bank_account_number TEXT,
        iban TEXT,
        status TEXT DEFAULT 'Active',
        employment_type TEXT DEFAULT 'Full-time',
        hire_date DATE,
        confirmation_date DATE,
        probation_end_date DATE,
        termination_date DATE,
        termination_reason TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 4. HR Employee Employment - Employment Details
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_employee_employment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        company_id INTEGER,
        branch_id INTEGER,
        department_id INTEGER,
        position_id INTEGER,
        shift_id INTEGER,
        reporting_to_id INTEGER,
        employment_status TEXT DEFAULT 'Active',
        contract_type TEXT DEFAULT 'Permanent',
        start_date DATE,
        end_date DATE,
        is_primary INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL,
        FOREIGN KEY (department_id) REFERENCES hr_departments(id) ON DELETE SET NULL,
        FOREIGN KEY (position_id) REFERENCES hr_positions(id) ON DELETE SET NULL,
        FOREIGN KEY (shift_id) REFERENCES hr_shifts(id) ON DELETE SET NULL,
        FOREIGN KEY (reporting_to_id) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 5. HR Shifts - Work Shift Templates
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_shifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        grace_minutes INTEGER DEFAULT 15,
        working_hours DECIMAL(4,2) DEFAULT 8.0,
        is_night_shift INTEGER DEFAULT 0,
        working_days TEXT DEFAULT '1,2,3,4,5',
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 6. HR Attendance Records - Daily Attendance
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_attendance_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        date DATE NOT NULL,
        check_in TIME,
        check_out TIME,
        shift_id INTEGER,
        work_hours DECIMAL(4,2) DEFAULT 0,
        overtime_hours DECIMAL(4,2) DEFAULT 0,
        late_minutes INTEGER DEFAULT 0,
        early_leave_minutes INTEGER DEFAULT 0,
        status TEXT DEFAULT 'Present',
        remarks TEXT,
        is_manual INTEGER DEFAULT 0,
        approved_by_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (shift_id) REFERENCES hr_shifts(id) ON DELETE SET NULL,
        FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL,
        UNIQUE(employee_id, date)
    )""",

    # -------------------------------------------------------------------------
    # 7. HR Leave Types - Types of Leave
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_leave_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        description TEXT,
        default_days INTEGER DEFAULT 0,
        is_paid INTEGER DEFAULT 1,
        requires_approval INTEGER DEFAULT 1,
        requires_document INTEGER DEFAULT 0,
        max_consecutive_days INTEGER DEFAULT 0,
        can_carry_forward INTEGER DEFAULT 0,
        max_carry_forward_days INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 8. HR Leave Requests - Leave Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_leave_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        leave_type_id INTEGER NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        total_days DECIMAL(4,2) NOT NULL,
        reason TEXT,
        status TEXT DEFAULT 'Pending',
        approved_by_id INTEGER,
        approved_at DATETIME,
        approved_remarks TEXT,
        is_cancelled INTEGER DEFAULT 0,
        cancellation_reason TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (leave_type_id) REFERENCES hr_leave_types(id) ON DELETE RESTRICT,
        FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 9. HR Leave Balances - Employee Leave Balances
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_leave_balances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        leave_type_id INTEGER NOT NULL,
        year INTEGER NOT NULL,
        total_days DECIMAL(5,2) DEFAULT 0,
        used_days DECIMAL(5,2) DEFAULT 0,
        pending_days DECIMAL(5,2) DEFAULT 0,
        balance_days DECIMAL(5,2) GENERATED ALWAYS AS (total_days - used_days - pending_days) STORED,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (leave_type_id) REFERENCES hr_leave_types(id) ON DELETE CASCADE,
        UNIQUE(employee_id, leave_type_id, year)
    )""",

    # -------------------------------------------------------------------------
    # 10. HR Payroll Periods - Monthly Payroll Periods
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_payroll_periods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        month INTEGER NOT NULL,
        year INTEGER NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        status TEXT DEFAULT 'Draft',
        total_employees INTEGER DEFAULT 0,
        total_gross DECIMAL(12,2) DEFAULT 0,
        total_deductions DECIMAL(12,2) DEFAULT 0,
        total_net DECIMAL(12,2) DEFAULT 0,
        processed_by_id INTEGER,
        processed_at DATETIME,
        approved_by_id INTEGER,
        approved_at DATETIME,
        locked_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (processed_by_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL,
        UNIQUE(month, year)
    )""",

    # -------------------------------------------------------------------------
    # 11. HR Payroll Records - Per Employee Payroll
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_payroll_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        basic_salary DECIMAL(12,2) DEFAULT 0,
        total_allowances DECIMAL(12,2) DEFAULT 0,
        total_overtime DECIMAL(12,2) DEFAULT 0,
        total_bonuses DECIMAL(12,2) DEFAULT 0,
        total_deductions DECIMAL(12,2) DEFAULT 0,
        gross_salary DECIMAL(12,2) DEFAULT 0,
        net_salary DECIMAL(12,2) DEFAULT 0,
        days_worked DECIMAL(4,2) DEFAULT 0,
        days_absent DECIMAL(4,2) DEFAULT 0,
        status TEXT DEFAULT 'Draft',
        approved_by_id INTEGER,
        approved_at DATETIME,
        locked INTEGER DEFAULT 0,
        locked_at DATETIME,
        lock_reason TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (period_id) REFERENCES hr_payroll_periods(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL,
        UNIQUE(period_id, employee_id)
    )""",

    # -------------------------------------------------------------------------
    # 12. HR Payroll Components - Salary Component Definitions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_payroll_components (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        component_type TEXT NOT NULL,
        is_taxable INTEGER DEFAULT 1,
        is_default INTEGER DEFAULT 0,
        calculation_type TEXT DEFAULT 'Fixed',
        amount DECIMAL(10,2) DEFAULT 0,
        percentage DECIMAL(5,2) DEFAULT 0,
        order_index INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 13. HR Employee Salary - Employee Salary Details
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_employee_salary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        component_id INTEGER NOT NULL,
        amount DECIMAL(12,2) NOT NULL,
        is_active INTEGER DEFAULT 1,
        effective_from DATE NOT NULL,
        effective_to DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (component_id) REFERENCES hr_payroll_components(id) ON DELETE RESTRICT,
        UNIQUE(employee_id, component_id, effective_from)
    )""",

    # -------------------------------------------------------------------------
    # 14. HR Overtime Requests
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_overtime_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        date DATE NOT NULL,
        hours DECIMAL(4,2) NOT NULL,
        overtime_type TEXT DEFAULT 'Regular',
        reason TEXT,
        status TEXT DEFAULT 'Pending',
        approved_by_id INTEGER,
        approved_at DATETIME,
        approved_remarks TEXT,
        rate_multiplier DECIMAL(3,2) DEFAULT 1.50,
        calculated_amount DECIMAL(10,2) DEFAULT 0,
        included_in_payroll_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (included_in_payroll_id) REFERENCES hr_payroll_records(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 15. HR Bonus Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_bonus_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        bonus_type TEXT NOT NULL,
        amount DECIMAL(10,2) NOT NULL,
        reason TEXT,
        effective_month INTEGER,
        effective_year INTEGER,
        status TEXT DEFAULT 'Pending',
        approved_by_id INTEGER,
        approved_at DATETIME,
        included_in_payroll_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (included_in_payroll_id) REFERENCES hr_payroll_records(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 16. HR Deduction Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_deduction_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        deduction_type TEXT NOT NULL,
        amount DECIMAL(10,2) NOT NULL,
        reason TEXT,
        is_recurring INTEGER DEFAULT 0,
        start_month INTEGER,
        start_year INTEGER,
        end_month INTEGER,
        end_year INTEGER,
        status TEXT DEFAULT 'Pending',
        approved_by_id INTEGER,
        approved_at DATETIME,
        included_in_payroll_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (included_in_payroll_id) REFERENCES hr_payroll_records(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 17. HR Loans - Employee Loans and Advances
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        loan_type TEXT DEFAULT 'Personal',
        principal_amount DECIMAL(10,2) NOT NULL,
        interest_rate DECIMAL(5,2) DEFAULT 0,
        total_amount DECIMAL(10,2) NOT NULL,
        monthly_installment DECIMAL(10,2) NOT NULL,
        tenure_months INTEGER NOT NULL,
        amount_paid DECIMAL(10,2) DEFAULT 0,
        amount_remaining DECIMAL(10,2) NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE,
        status TEXT DEFAULT 'Active',
        approved_by_id INTEGER,
        approved_at DATETIME,
        remarks TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 18. HR Loan Installments
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_loan_installments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_id INTEGER NOT NULL,
        period_id INTEGER,
        due_date DATE NOT NULL,
        installment_amount DECIMAL(10,2) NOT NULL,
        principal_amount DECIMAL(10,2) NOT NULL,
        interest_amount DECIMAL(10,2) DEFAULT 0,
        amount_paid DECIMAL(10,2) DEFAULT 0,
        paid_on DATE,
        status TEXT DEFAULT 'Pending',
        included_in_payroll_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (loan_id) REFERENCES hr_loans(id) ON DELETE CASCADE,
        FOREIGN KEY (period_id) REFERENCES hr_payroll_periods(id) ON DELETE SET NULL,
        FOREIGN KEY (included_in_payroll_id) REFERENCES hr_payroll_records(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 19. HR Training Programs
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_training_programs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        title_ar TEXT,
        title_fa TEXT,
        description TEXT,
        category TEXT,
        training_type TEXT DEFAULT 'Technical',
        provider TEXT,
        duration_hours INTEGER DEFAULT 0,
        duration_days INTEGER DEFAULT 0,
        cost_per_participant DECIMAL(10,2) DEFAULT 0,
        currency TEXT DEFAULT 'AED',
        certification_validity_months INTEGER,
        is_mandatory INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 20. HR Training Sessions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_training_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        program_id INTEGER NOT NULL,
        session_title TEXT,
        trainer_name TEXT,
        trainer_contact TEXT,
        location TEXT,
        online_link TEXT,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        start_time TEXT,
        end_time TEXT,
        max_participants INTEGER DEFAULT 20,
        enrolled_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'Scheduled',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (program_id) REFERENCES hr_training_programs(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 21. HR Training Enrollments
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_training_enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        enrollment_date DATE DEFAULT (date('now')),
        status TEXT DEFAULT 'Enrolled',
        attendance_status TEXT,
        completion_date DATE,
        score DECIMAL(5,2),
        grade TEXT,
        certificate_number TEXT,
        feedback TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES hr_training_sessions(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 22. HR Employee Documents
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_employee_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        document_type TEXT NOT NULL,
        document_name TEXT NOT NULL,
        file_path TEXT,
        document_number TEXT,
        issue_date DATE,
        expiry_date DATE,
        is_verified INTEGER DEFAULT 0,
        verified_by_id INTEGER,
        verified_at DATETIME,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (verified_by_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 20. HR Announcements
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        announcement_type TEXT DEFAULT 'General',
        priority TEXT DEFAULT 'Normal',
        is_active INTEGER DEFAULT 1,
        valid_from DATE,
        valid_to DATE,
        created_by_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 21. HR Candidates - Recruitment
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        requisition_id INTEGER,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        position_applied TEXT,
        source TEXT,
        current_stage TEXT DEFAULT 'Applied',
        interview_score DECIMAL(4,2),
        status TEXT DEFAULT 'Active',
        cv_path TEXT,
        notes TEXT,
        assigned_recruiter_id INTEGER,
        offer_salary DECIMAL(10,2),
        offer_status TEXT,
        joining_date DATE,
        rejection_reason TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (requisition_id) REFERENCES hr_job_requisitions(id) ON DELETE SET NULL,
        FOREIGN KEY (assigned_recruiter_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 22. HR Job Requisitions - Vacancies
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_job_requisitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        department_id INTEGER,
        position_id INTEGER,
        employment_type TEXT DEFAULT 'Full-time',
        salary_min DECIMAL(10,2),
        salary_max DECIMAL(10,2),
        vacancy_count INTEGER DEFAULT 1,
        description TEXT,
        requirements TEXT,
        status TEXT DEFAULT 'Draft',
        requested_by_id INTEGER,
        approved_by_id INTEGER,
        approved_at DATETIME,
        closed_reason TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (department_id) REFERENCES hr_departments(id) ON DELETE SET NULL,
        FOREIGN KEY (position_id) REFERENCES hr_positions(id) ON DELETE SET NULL,
        FOREIGN KEY (requested_by_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 23. HR Approvals - Approval Workflow
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        approval_type TEXT NOT NULL,
        reference_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        approver_id INTEGER NOT NULL,
        sequence INTEGER DEFAULT 1,
        status TEXT DEFAULT 'Pending',
        remarks TEXT,
        actioned_by_id INTEGER,
        actioned_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (approver_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (actioned_by_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 24. HR Settings - Configurable Settings
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_key TEXT UNIQUE NOT NULL,
        setting_value TEXT,
        setting_type TEXT DEFAULT 'Text',
        category TEXT,
        description TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 25. HR KPIs - Key Performance Indicators
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_kpis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        target_type TEXT DEFAULT 'Number',
        target_value DECIMAL(10,2) DEFAULT 0,
        weight DECIMAL(5,2) DEFAULT 1.0,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 26. HR Performance Reviews
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_performance_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        review_period TEXT NOT NULL,
        review_date DATE NOT NULL,
        reviewer_id INTEGER NOT NULL,
        overall_score DECIMAL(4,2),
        kpi_scores TEXT,
        strengths TEXT,
        areas_for_improvement TEXT,
        comments TEXT,
        status TEXT DEFAULT 'Draft',
        acknowledged_by_employee INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 27. HR Successors - Successor/Deputy Planning
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_successors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        successor_id INTEGER,
        deputy_id INTEGER,
        relationship_type TEXT DEFAULT 'Successor',
        readiness_level TEXT,
        training_required TEXT,
        handover_notes TEXT,
        is_primary INTEGER DEFAULT 1,
        effective_from DATE,
        effective_to DATE,
        status TEXT DEFAULT 'Active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (successor_id) REFERENCES hr_employees(id) ON DELETE SET NULL,
        FOREIGN KEY (deputy_id) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 28. HR Tasks - Employee Tasks
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        task_title TEXT NOT NULL,
        task_description TEXT,
        priority TEXT DEFAULT 'Medium',
        due_date DATE,
        status TEXT DEFAULT 'Pending',
        completed_at DATETIME,
        assigned_by_id INTEGER,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (assigned_by_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 29. HR Audit Logs
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,
        entity_id INTEGER,
        action TEXT NOT NULL,
        field_name TEXT,
        old_value TEXT,
        new_value TEXT,
        user_id INTEGER,
        ip_address TEXT,
        user_agent TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 30. HR Notification Templates
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_notification_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_key TEXT UNIQUE NOT NULL,
        template_name TEXT NOT NULL,
        subject TEXT,
        body TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 31. HR Employee History - Employment History
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS hr_employee_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        history_type TEXT NOT NULL,
        field_name TEXT,
        old_value TEXT,
        new_value TEXT,
        effective_from DATE,
        effective_to DATE,
        reason TEXT,
        created_by_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL
    )""",
]


def run_hr_migrations():
    """
    Run all HR table migrations.
    Creates all HR tables if they don't exist.
    Also seeds default data for essential lookups.
    """
    conn = get_db()
    try:
        # Create all HR tables
        for table_sql in HR_TABLES:
            conn.executescript(table_sql)
        
        conn.commit()
        
        # Seed default data
        seed_hr_defaults(conn)
        
        return True, "HR migrations completed successfully"
    except Exception as e:
        conn.rollback()
        return False, f"HR migration error: {str(e)}"
    finally:
        conn.close()


def seed_hr_defaults(conn):
    """Seed default HR data for essential lookups."""
    
    # Seed default leave types
    default_leave_types = [
        ('Annual Leave', 'AL', 'Paid annual leave', 21, 1, 1, 0, 30, 1, 5),
        ('Sick Leave', 'SL', 'Medical sick leave', 14, 1, 1, 1, 7, 0, 0),
        ('Emergency Leave', 'EL', 'Emergency family leave', 5, 1, 1, 0, 3, 0, 0),
        ('Unpaid Leave', 'UL', 'Unpaid leave of absence', 0, 0, 1, 0, 0, 0, 0),
        ('Maternity Leave', 'ML', 'Maternity leave', 90, 1, 1, 1, 0, 0, 0),
        ('Paternity Leave', 'PL', 'Paternity leave', 5, 1, 1, 0, 0, 0, 0),
        ('Hajj Leave', 'HL', 'Religious hajj leave', 10, 1, 1, 0, 0, 0, 0),
    ]
    
    for lt in default_leave_types:
        conn.execute("""
            INSERT OR IGNORE INTO hr_leave_types 
            (name, code, description, default_days, is_paid, requires_approval, 
             requires_document, max_consecutive_days, can_carry_forward, max_carry_forward_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, lt)
    
    # Seed default payroll components
    default_components = [
        ('Basic Salary', 'BASIC', 'Basic', 1, 1, 'Fixed', 0, 0, 1),
        ('Housing Allowance', 'HOUSING', 'Allowance', 1, 1, 'Percentage', 0, 25, 2),
        ('Transport Allowance', 'TRANSPORT', 'Allowance', 1, 1, 'Fixed', 0, 500, 3),
        ('Food Allowance', 'FOOD', 'Allowance', 1, 1, 'Fixed', 0, 300, 4),
        ('Communication Allowance', 'COMM', 'Allowance', 1, 1, 'Fixed', 0, 150, 5),
        ('Overtime', 'OT', 'Deduction', 1, 0, 'Hourly', 0, 0, 10),
        ('Bonus', 'BONUS', 'Bonus', 0, 1, 'Variable', 0, 0, 11),
        ('Commission', 'COMMISSION', 'Bonus', 0, 1, 'Percentage', 0, 0, 12),
        ('Absence Deduction', 'ABSENCE', 'Deduction', 0, 0, 'Daily', 0, 0, 20),
        ('Late Deduction', 'LATE', 'Deduction', 0, 0, 'PerMinute', 0, 0, 21),
        ('Loan Deduction', 'LOAN', 'Deduction', 0, 0, 'Installment', 0, 0, 22),
        ('Advance Deduction', 'ADVANCE', 'Deduction', 0, 0, 'Fixed', 0, 0, 23),
        ('Penalty', 'PENALTY', 'Deduction', 0, 0, 'Fixed', 0, 0, 24),
    ]
    
    for comp in default_components:
        conn.execute("""
            INSERT OR IGNORE INTO hr_payroll_components 
            (name, code, component_type, is_taxable, is_default, calculation_type, 
             amount, percentage, order_index)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, comp)
    
    # Seed default shifts
    default_shifts = [
        ('Morning Shift', 'MORN', '08:00', '17:00', 15, 8.0, 0, '1,2,3,4,5'),
        ('Evening Shift', 'EVE', '14:00', '23:00', 15, 8.0, 0, '1,2,3,4,5'),
        ('Night Shift', 'NIGHT', '22:00', '07:00', 0, 8.0, 1, '1,2,3,4,5'),
        ('Day Shift (UAE)', 'DAY-UAE', '09:00', '18:00', 30, 8.0, 0, '1,2,3,4,5'),
        ('Half Day', 'HALF', '08:00', '12:00', 0, 4.0, 0, '1,2,3,4,5'),
    ]
    
    for shift in default_shifts:
        conn.execute("""
            INSERT OR IGNORE INTO hr_shifts 
            (name, code, start_time, end_time, grace_minutes, working_hours, 
             is_night_shift, working_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, shift)
    
    # Seed default HR settings
    default_settings = [
        ('payroll_cycle', 'monthly', 'Text', 'Payroll', 'Monthly or bi-weekly payroll cycle'),
        ('currency', 'AED', 'Text', 'General', 'Default currency for payroll'),
        ('overtime_rate_weekday', '1.50', 'Number', 'Overtime', 'Overtime multiplier for weekdays'),
        ('overtime_rate_weekend', '2.00', 'Number', 'Overtime', 'Overtime multiplier for weekends'),
        ('overtime_rate_holiday', '2.50', 'Number', 'Overtime', 'Overtime multiplier for holidays'),
        ('late_grace_minutes', '15', 'Number', 'Attendance', 'Grace period for late arrival in minutes'),
        ('max_ot_hours_monthly', '40', 'Number', 'Overtime', 'Maximum overtime hours per month'),
        ('probation_months', '3', 'Number', 'Employment', 'Default probation period in months'),
        ('annual_leave_default', '21', 'Number', 'Leave', 'Default annual leave days for new employees'),
        ('working_days_week', '5', 'Number', 'Attendance', 'Number of working days per week'),
        ('weekend_days', '0,6', 'Text', 'Attendance', 'Weekend days (0=Sunday, 6=Saturday)'),
        ('probation_leave_entitlement', '0', 'Number', 'Leave', 'Leave days during probation (0 = no leave)'),
        ('email_notifications', '1', 'Boolean', 'Notifications', 'Enable HR email notifications'),
        ('auto_lock_attendance', '1', 'Boolean', 'Attendance', 'Auto-lock attendance after payroll close'),
    ]
    
    for setting in default_settings:
        conn.execute("""
            INSERT OR IGNORE INTO hr_settings 
            (setting_key, setting_value, setting_type, category, description)
            VALUES (?, ?, ?, ?, ?)
        """, setting)
    
    conn.commit()


def get_hr_setting(setting_key: str, default: str = None) -> str:
    """Get a specific HR setting value."""
    conn = get_db()
    try:
        result = conn.execute(
            "SELECT setting_value FROM hr_settings WHERE setting_key = ? AND is_active = 1",
            (setting_key,)
        ).fetchone()
        return result['setting_value'] if result else default
    finally:
        conn.close()


def update_hr_setting(setting_key: str, value: str) -> bool:
    """Update a specific HR setting value."""
    conn = get_db()
    try:
        conn.execute(
            "UPDATE hr_settings SET setting_value = ?, updated_at = CURRENT_TIMESTAMP WHERE setting_key = ?",
            (value, setting_key)
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def log_hr_audit(entity_type: str, entity_id: int, action: str, user_id: int,
                  field_name: str = None, old_value: str = None, 
                  new_value: str = None, ip_address: str = None,
                  user_agent: str = None) -> int:
    """Log an HR audit entry."""
    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO hr_audit_logs 
            (entity_type, entity_id, action, field_name, old_value, new_value, 
             user_id, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (entity_type, entity_id, action, field_name, old_value, new_value,
              user_id, ip_address, user_agent))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


# =============================================================================
# HELPER FUNCTIONS FOR COMMON HR OPERATIONS
# =============================================================================

def get_employee_by_code(employee_code: str) -> Optional[Dict[str, Any]]:
    """Get employee by employee code."""
    conn = get_db()
    try:
        result = conn.execute(
            "SELECT * FROM hr_employees WHERE employee_code = ?",
            (employee_code,)
        ).fetchone()
        return dict(result) if result else None
    finally:
        conn.close()


def get_employee_with_employment(employee_id: int) -> Optional[Dict[str, Any]]:
    """Get employee with employment details."""
    conn = get_db()
    try:
        emp = conn.execute(
            "SELECT * FROM hr_employees WHERE id = ?",
            (employee_id,)
        ).fetchone()
        
        if not emp:
            return None
        
        employment = conn.execute("""
            SELECT ee.*, 
                   d.name as department_name,
                   p.title as position_title,
                   s.name as shift_name,
                   m.first_name || ' ' || m.last_name as manager_name
            FROM hr_employee_employment ee
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            LEFT JOIN hr_positions p ON ee.position_id = p.id
            LEFT JOIN hr_shifts s ON ee.shift_id = s.id
            LEFT JOIN hr_employees m ON ee.reporting_to_id = m.id
            WHERE ee.employee_id = ? AND ee.is_primary = 1
        """, (employee_id,)).fetchone()
        
        result = dict(emp)
        if employment:
            result['employment'] = dict(employment)
        
        return result
    finally:
        conn.close()


def get_active_employee_count() -> int:
    """Get count of active employees."""
    conn = get_db()
    try:
        result = conn.execute(
            "SELECT COUNT(*) as cnt FROM hr_employees WHERE status = 'Active'"
        ).fetchone()
        return result['cnt'] if result else 0
    finally:
        conn.close()


def get_department_employee_count(department_id: int) -> int:
    """Get employee count for a department."""
    conn = get_db()
    try:
        result = conn.execute("""
            SELECT COUNT(DISTINCT ee.employee_id) as cnt
            FROM hr_employee_employment ee
            WHERE ee.department_id = ? AND ee.employment_status = 'Active'
        """, (department_id,)).fetchone()
        return result['cnt'] if result else 0
    finally:
        conn.close()


def get_employees_on_leave_today() -> List[Dict[str, Any]]:
    """Get employees currently on leave."""
    conn = get_db()
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        result = conn.execute("""
            SELECT e.*, lt.name as leave_type_name, lr.start_date, lr.end_date, lr.reason
            FROM hr_leave_requests lr
            JOIN hr_employees e ON lr.employee_id = e.id
            JOIN hr_leave_types lt ON lr.leave_type_id = lt.id
            WHERE lr.status = 'Approved'
            AND lr.start_date <= ?
            AND lr.end_date >= ?
            AND lr.is_cancelled = 0
            ORDER BY e.first_name, e.last_name
        """, (today, today)).fetchall()
        return [dict(r) for r in result]
    finally:
        conn.close()


def get_upcoming_leave_requests(days: int = 7) -> List[Dict[str, Any]]:
    """Get upcoming leave requests within specified days."""
    conn = get_db()
    try:
        today = datetime.now().date()
        end_date = today + timedelta(days=days)
        result = conn.execute("""
            SELECT e.*, lt.name as leave_type_name, lr.start_date, lr.end_date
            FROM hr_leave_requests lr
            JOIN hr_employees e ON lr.employee_id = e.id
            JOIN hr_leave_types lt ON lr.leave_type_id = lt.id
            WHERE lr.status = 'Pending'
            AND lr.start_date BETWEEN ? AND ?
            ORDER BY lr.start_date
        """, (today.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))).fetchall()
        return [dict(r) for r in result]
    finally:
        conn.close()


def calculate_employee_leave_balance(employee_id: int, leave_type_id: int, year: int = None) -> Dict[str, float]:
    """Calculate employee leave balance for a specific leave type and year."""
    if year is None:
        year = datetime.now().year
    
    conn = get_db()
    try:
        balance = conn.execute("""
            SELECT * FROM hr_leave_balances 
            WHERE employee_id = ? AND leave_type_id = ? AND year = ?
        """, (employee_id, leave_type_id, year)).fetchone()
        
        if balance:
            return {
                'total': balance['total_days'],
                'used': balance['used_days'],
                'pending': balance['pending_days'],
                'balance': balance['balance_days']
            }
        
        # Get default from leave type if no balance record
        leave_type = conn.execute(
            "SELECT default_days FROM hr_leave_types WHERE id = ?",
            (leave_type_id,)
        ).fetchone()
        
        default_days = leave_type['default_days'] if leave_type else 0
        
        return {
            'total': default_days,
            'used': 0,
            'pending': 0,
            'balance': default_days
        }
    finally:
        conn.close()


def get_monthly_payroll_summary(month: int, year: int) -> Dict[str, Any]:
    """Get payroll summary for a specific month/year."""
    conn = get_db()
    try:
        period = conn.execute("""
            SELECT * FROM hr_payroll_periods WHERE month = ? AND year = ?
        """, (month, year)).fetchone()
        
        if not period:
            return None
        
        return {
            'period': dict(period),
            'employee_count': conn.execute("""
                SELECT COUNT(*) as cnt FROM hr_payroll_records WHERE period_id = ?
            """, (period['id'],)).fetchone()['cnt'],
            'total_gross': conn.execute("""
                SELECT SUM(gross_salary) as total FROM hr_payroll_records WHERE period_id = ?
            """, (period['id'],)).fetchone()['total'] or 0,
            'total_deductions': conn.execute("""
                SELECT SUM(total_deductions) as total FROM hr_payroll_records WHERE period_id = ?
            """, (period['id'],)).fetchone()['total'] or 0,
            'total_net': conn.execute("""
                SELECT SUM(net_salary) as total FROM hr_payroll_records WHERE period_id = ?
            """, (period['id'],)).fetchone()['total'] or 0,
        }
    finally:
        conn.close()


def get_attendance_summary(employee_id: int, month: int, year: int) -> Dict[str, Any]:
    """Get attendance summary for an employee for a specific month."""
    conn = get_db()
    try:
        start_date = f"{year}-{month:02d}-01"
        # Calculate end date
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"
        
        records = conn.execute("""
            SELECT * FROM hr_attendance_records
            WHERE employee_id = ? AND date >= ? AND date < ?
        """, (employee_id, start_date, end_date)).fetchall()
        
        present = sum(1 for r in records if r['status'] == 'Present')
        absent = sum(1 for r in records if r['status'] == 'Absent')
        late = sum(1 for r in records if r['late_minutes'] > 0)
        total_ot = sum(float(r['overtime_hours'] or 0) for r in records)
        
        return {
            'total_days': len(records),
            'present': present,
            'absent': absent,
            'late_arrivals': late,
            'overtime_hours': total_ot,
            'records': [dict(r) for r in records]
        }
    finally:
        conn.close()


if __name__ == '__main__':
    # Run migrations when executed directly
    success, message = run_hr_migrations()
    print(message)
