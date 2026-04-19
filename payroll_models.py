"""
Enterprise Payroll Module Database Models
==========================================
This file contains all enterprise payroll-related database table definitions.

These tables are designed to extend the existing HR module with a comprehensive
enterprise-grade payroll system including:
- Payroll configuration (components, groups, profiles)
- Payroll period management and calendar
- Payroll run processing and lifecycle
- Employee payroll inputs and adjustments
- Payslip generation and output
- Loan and advance management
- Retro adjustments and arrears
- Payroll compliance and audit trail
- Finance integration
- HR integration hooks

Database: Uses the same warehouse.db as the HR module
"""

import sqlite3
import os
from datetime import datetime, timedelta, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Any, Tuple

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'warehouse.db'))


def get_db():
    """Get database connection with Row factory for dict-like access."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# =============================================================================
# PAYROLL TABLE DEFINITIONS
# =============================================================================

PAYROLL_TABLES = [
    # ==========================================================================
    # 1. PAYROLL COMPONENTS - Earnings, Deductions, Allowances Configuration
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_components (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        name_ar TEXT,
        name_fa TEXT,
        name_ru TEXT,
        name_hi TEXT,
        name_es TEXT,
        name_zh TEXT,
        name_de TEXT,
        component_type TEXT NOT NULL,
        sub_type TEXT,
        category TEXT,
        description TEXT,
        is_taxable INTEGER DEFAULT 1,
        is_insurable INTEGER DEFAULT 1,
        is_default INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        calculation_type TEXT DEFAULT 'Fixed',
        amount DECIMAL(12,2) DEFAULT 0,
        percentage DECIMAL(6,2) DEFAULT 0,
        percentage_of TEXT,
        max_amount DECIMAL(12,2),
        min_amount DECIMAL(12,2),
        order_index INTEGER DEFAULT 0,
        gl_account TEXT,
        cost_center_required INTEGER DEFAULT 0,
        requires_approval INTEGER DEFAULT 0,
        effective_from DATE,
        effective_to DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        CONSTRAINT chk_component_type CHECK (component_type IN ('Earning', 'Deduction', 'Allowance', 'Benefit', 'Tax', 'Contribution', 'Loan', 'Advance', 'Arrears', 'Adjustment'))
    )""",

    # ==========================================================================
    # 2. PAYROLL GROUPS - Employee groupings for payroll processing
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        name_ar TEXT,
        name_fa TEXT,
        description TEXT,
        is_active INTEGER DEFAULT 1,
        is_default INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER
    )""",

    # ==========================================================================
    # 3. PAYROLL GROUP MEMBERS - Employees assigned to payroll groups
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_group_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        effective_from DATE NOT NULL,
        effective_to DATE,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (group_id) REFERENCES payroll_groups(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        UNIQUE(group_id, employee_id, effective_from)
    )""",

    # ==========================================================================
    # 4. PAYROLL PROFILES - Employee-specific payroll configuration
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL UNIQUE,
        payroll_group_id INTEGER,
        pay_frequency TEXT DEFAULT 'Monthly',
        currency TEXT DEFAULT 'AED',
        bank_name TEXT,
        bank_account_number TEXT,
        iban TEXT,
        payment_method TEXT DEFAULT 'Bank Transfer',
        tax_id TEXT,
        social_insurance_number TEXT,
        is_taxable INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1,
        effective_from DATE NOT NULL,
        effective_to DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (payroll_group_id) REFERENCES payroll_groups(id) ON DELETE SET NULL
    )""",

    # ==========================================================================
    # 5. PAYROLL PROFILE COMPONENTS - Employee-specific component amounts
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_profile_components (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id INTEGER NOT NULL,
        component_id INTEGER NOT NULL,
        amount DECIMAL(12,2) NOT NULL,
        percentage DECIMAL(6,2),
        calculation_type TEXT DEFAULT 'Fixed',
        is_active INTEGER DEFAULT 1,
        effective_from DATE NOT NULL,
        effective_to DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (profile_id) REFERENCES payroll_profiles(id) ON DELETE CASCADE,
        FOREIGN KEY (component_id) REFERENCES payroll_components(id) ON DELETE RESTRICT,
        UNIQUE(profile_id, component_id, effective_from)
    )""",

    # ==========================================================================
    # 6. PAYROLL CALENDAR - Defines payroll cycles and important dates
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_calendar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        description TEXT,
        country TEXT,
        pay_frequency TEXT NOT NULL,
        cycle_type TEXT DEFAULT 'Monthly',
        period_start_day INTEGER DEFAULT 1,
        period_end_day INTEGER DEFAULT 31,
        cutoff_day INTEGER DEFAULT 25,
        payment_day INTEGER DEFAULT 28,
        overtime_cutoff_day INTEGER DEFAULT 26,
        leave_cutoff_day INTEGER DEFAULT 26,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        CONSTRAINT chk_pay_frequency CHECK (pay_frequency IN ('Monthly', 'Bi-Weekly', 'Weekly', 'Semi-Monthly', 'Annual'))
    )""",

    # ==========================================================================
    # 7. PAYROLL PERIODS - Individual payroll periods
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_periods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        calendar_id INTEGER,
        name TEXT NOT NULL,
        period_key TEXT UNIQUE NOT NULL,
        month INTEGER NOT NULL,
        year INTEGER NOT NULL,
        period_start DATE NOT NULL,
        period_end DATE NOT NULL,
        cutoff_date DATE,
        payment_date DATE,
        status TEXT DEFAULT 'Open',
        run_status TEXT DEFAULT 'Not Started',
        total_employees INTEGER DEFAULT 0,
        total_gross DECIMAL(14,2) DEFAULT 0,
        total_deductions DECIMAL(14,2) DEFAULT 0,
        total_net DECIMAL(14,2) DEFAULT 0,
        total_tax DECIMAL(14,2) DEFAULT 0,
        total_insurance DECIMAL(14,2) DEFAULT 0,
        total_arrears DECIMAL(14,2) DEFAULT 0,
        processed_by_id INTEGER,
        processed_at DATETIME,
        approved_by_id INTEGER,
        approved_at DATETIME,
        locked_by_id INTEGER,
        locked_at DATETIME,
        closed_by_id INTEGER,
        closed_at DATETIME,
        fiscal_year TEXT,
        quarter TEXT,
        is_adjustment_period INTEGER DEFAULT 0,
        adjustment_for_period_id INTEGER,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (calendar_id) REFERENCES payroll_calendar(id) ON DELETE SET NULL,
        FOREIGN KEY (processed_by_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (locked_by_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (closed_by_id) REFERENCES users(id) ON DELETE SET NULL,
        CONSTRAINT chk_period_status CHECK (status IN ('Open', 'Processing', 'Pending Approval', 'Approved', 'Locked', 'Closed', 'Archived')),
        CONSTRAINT chk_run_status CHECK (run_status IN ('Not Started', 'Pre-Validation', 'Draft', 'Calculated', 'In Review', 'Approved', 'Locked', 'Closed', 'Failed'))
    )""",

    # ==========================================================================
    # 8. PAYROLL PERIOD LOCKS - Track period lock/unlock events
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_period_locks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period_id INTEGER NOT NULL,
        lock_type TEXT NOT NULL,
        is_locked INTEGER DEFAULT 1,
        locked_by_id INTEGER NOT NULL,
        locked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        unlocked_by_id INTEGER,
        unlocked_at DATETIME,
        reason TEXT,
        approved_by_id INTEGER,
        approved_at DATETIME,
        FOREIGN KEY (period_id) REFERENCES payroll_periods(id) ON DELETE CASCADE,
        FOREIGN KEY (locked_by_id) REFERENCES users(id) ON DELETE RESTRICT,
        FOREIGN KEY (unlocked_by_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # ==========================================================================
    # 9. PAYROLL RUNS - Each payroll run instance
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period_id INTEGER NOT NULL,
        run_type TEXT DEFAULT 'Regular',
        name TEXT NOT NULL,
        status TEXT DEFAULT 'Draft',
        total_records INTEGER DEFAULT 0,
        total_gross DECIMAL(14,2) DEFAULT 0,
        total_deductions DECIMAL(14,2) DEFAULT 0,
        total_net DECIMAL(14,2) DEFAULT 0,
        total_exceptions INTEGER DEFAULT 0,
        validation_status TEXT DEFAULT 'Pending',
        validation_errors TEXT,
        started_at DATETIME,
        completed_at DATETIME,
        created_by_id INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (period_id) REFERENCES payroll_periods(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE RESTRICT,
        CONSTRAINT chk_run_status CHECK (status IN ('Draft', 'Pre-Validation', 'Calculating', 'Calculated', 'In Review', 'Approved', 'Locked', 'Closed', 'Cancelled'))
    )""",

    # ==========================================================================
    # 10. PAYROLL RUN VALIDATIONS - Pre-run validation checks
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_run_validations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER NOT NULL,
        validation_type TEXT NOT NULL,
        validation_rule TEXT,
        entity_type TEXT,
        entity_id INTEGER,
        status TEXT DEFAULT 'Pending',
        error_message TEXT,
        error_details TEXT,
        resolved_by_id INTEGER,
        resolved_at DATETIME,
        resolution_notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (run_id) REFERENCES payroll_runs(id) ON DELETE CASCADE,
        FOREIGN KEY (resolved_by_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # ==========================================================================
    # 11. PAYROLL EMPLOYEE RECORDS - Per-employee payroll calculation results
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_employee_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER NOT NULL,
        period_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        profile_id INTEGER,
        department_id INTEGER,
        branch_id INTEGER,
        basic_salary DECIMAL(12,2) DEFAULT 0,
        total_earnings DECIMAL(12,2) DEFAULT 0,
        total_allowances DECIMAL(12,2) DEFAULT 0,
        total_overtime DECIMAL(12,2) DEFAULT 0,
        total_bonuses DECIMAL(12,2) DEFAULT 0,
        total_deductions DECIMAL(12,2) DEFAULT 0,
        total_tax DECIMAL(12,2) DEFAULT 0,
        total_insurance DECIMAL(12,2) DEFAULT 0,
        total_loan_deductions DECIMAL(12,2) DEFAULT 0,
        total_arrears DECIMAL(12,2) DEFAULT 0,
        gross_salary DECIMAL(12,2) DEFAULT 0,
        net_salary DECIMAL(12,2) DEFAULT 0,
        days_worked DECIMAL(5,2) DEFAULT 0,
        days_absent DECIMAL(5,2) DEFAULT 0,
        days_leave DECIMAL(5,2) DEFAULT 0,
        overtime_hours DECIMAL(6,2) DEFAULT 0,
        currency TEXT DEFAULT 'AED',
        exchange_rate DECIMAL(10,4) DEFAULT 1.0000,
        status TEXT DEFAULT 'Draft',
        has_exceptions INTEGER DEFAULT 0,
        exception_count INTEGER DEFAULT 0,
        approved_by_id INTEGER,
        approved_at DATETIME,
        approved_remarks TEXT,
        locked INTEGER DEFAULT 0,
        locked_by_id INTEGER,
        locked_at DATETIME,
        lock_reason TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (run_id) REFERENCES payroll_runs(id) ON DELETE CASCADE,
        FOREIGN KEY (period_id) REFERENCES payroll_periods(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (profile_id) REFERENCES payroll_profiles(id) ON DELETE SET NULL,
        FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (locked_by_id) REFERENCES users(id) ON DELETE SET NULL,
        UNIQUE(run_id, employee_id),
        CONSTRAINT chk_record_status CHECK (status IN ('Draft', 'Calculated', 'In Review', 'Approved', 'Locked', 'Excluded', 'Error'))
    )""",

    # ==========================================================================
    # 12. PAYROLL EMPLOYEE EARNINGS - Itemized earnings per employee
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_employee_earnings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id INTEGER NOT NULL,
        component_id INTEGER NOT NULL,
        component_code TEXT NOT NULL,
        component_name TEXT NOT NULL,
        amount DECIMAL(12,2) NOT NULL,
        quantity DECIMAL(8,2) DEFAULT 1,
        rate DECIMAL(10,4) DEFAULT 1.0000,
        is_taxable INTEGER DEFAULT 1,
        is_insurable INTEGER DEFAULT 1,
        calculation_details TEXT,
        period_start DATE,
        period_end DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (record_id) REFERENCES payroll_employee_records(id) ON DELETE CASCADE,
        FOREIGN KEY (component_id) REFERENCES payroll_components(id) ON DELETE RESTRICT
    )""",

    # ==========================================================================
    # 13. PAYROLL EMPLOYEE DEDUCTIONS - Itemized deductions per employee
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_employee_deductions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id INTEGER NOT NULL,
        component_id INTEGER NOT NULL,
        component_code TEXT NOT NULL,
        component_name TEXT NOT NULL,
        amount DECIMAL(12,2) NOT NULL,
        deduction_type TEXT DEFAULT 'Fixed',
        is_pre_tax INTEGER DEFAULT 0,
        is_taxable INTEGER DEFAULT 1,
        calculation_details TEXT,
        period_start DATE,
        period_end DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (record_id) REFERENCES payroll_employee_records(id) ON DELETE CASCADE,
        FOREIGN KEY (component_id) REFERENCES payroll_components(id) ON DELETE RESTRICT
    )""",

    # ==========================================================================
    # 14. PAYROLL ATTENDANCE INPUTS - Attendance data feeding payroll
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_attendance_inputs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        date DATE NOT NULL,
        shift_id INTEGER,
        work_hours DECIMAL(5,2) DEFAULT 0,
        overtime_hours DECIMAL(5,2) DEFAULT 0,
        late_minutes INTEGER DEFAULT 0,
        early_leave_minutes INTEGER DEFAULT 0,
        status TEXT DEFAULT 'Present',
        is_paid INTEGER DEFAULT 1,
        deduction_amount DECIMAL(12,2) DEFAULT 0,
        approved_by_id INTEGER,
        approved_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (period_id) REFERENCES payroll_periods(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL,
        UNIQUE(period_id, employee_id, date)
    )""",

    # ==========================================================================
    # 15. PAYROLL OVERTIME INPUTS - Overtime hours feeding payroll
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_overtime_inputs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        date DATE NOT NULL,
        hours DECIMAL(5,2) NOT NULL,
        overtime_type TEXT NOT NULL,
        rate_multiplier DECIMAL(3,2) DEFAULT 1.50,
        rate_per_hour DECIMAL(10,2) DEFAULT 0,
        total_amount DECIMAL(12,2) DEFAULT 0,
        status TEXT DEFAULT 'Pending',
        approved_by_id INTEGER,
        approved_at DATETIME,
        approved_remarks TEXT,
        included_in_run_id INTEGER,
        included_in_record_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (period_id) REFERENCES payroll_periods(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (included_in_run_id) REFERENCES payroll_runs(id) ON DELETE SET NULL,
        FOREIGN KEY (included_in_record_id) REFERENCES payroll_employee_records(id) ON DELETE SET NULL,
        UNIQUE(period_id, employee_id, date, overtime_type)
    )""",

    # ==========================================================================
    # 16. PAYROLL LEAVE IMPACTS - Leave affecting payroll
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_leave_impacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        leave_request_id INTEGER,
        leave_type_id INTEGER,
        leave_type_name TEXT,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        total_days DECIMAL(5,2) NOT NULL,
        is_paid INTEGER DEFAULT 1,
        deduction_rate DECIMAL(5,2) DEFAULT 0,
        deduction_amount DECIMAL(12,2) DEFAULT 0,
        status TEXT DEFAULT 'Calculated',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (period_id) REFERENCES payroll_periods(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (leave_request_id) REFERENCES hr_leave_requests(id) ON DELETE SET NULL,
        FOREIGN KEY (leave_type_id) REFERENCES hr_leave_types(id) ON DELETE SET NULL
    )""",

    # ==========================================================================
    # 17. PAYROLL MANUAL ADJUSTMENTS - Manual adjustments to payroll
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_manual_adjustments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        adjustment_type TEXT NOT NULL,
        component_id INTEGER,
        amount DECIMAL(12,2) NOT NULL,
        is_addition INTEGER DEFAULT 1,
        reason TEXT NOT NULL,
        status TEXT DEFAULT 'Pending',
        requested_by_id INTEGER NOT NULL,
        requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        approved_by_id INTEGER,
        approved_at DATETIME,
        approved_remarks TEXT,
        included_in_run_id INTEGER,
        included_in_record_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (period_id) REFERENCES payroll_periods(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (component_id) REFERENCES payroll_components(id) ON DELETE SET NULL,
        FOREIGN KEY (requested_by_id) REFERENCES users(id) ON DELETE RESTRICT,
        FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (included_in_run_id) REFERENCES payroll_runs(id) ON DELETE SET NULL,
        FOREIGN KEY (included_in_record_id) REFERENCES payroll_employee_records(id) ON DELETE SET NULL,
        CONSTRAINT chk_adjustment_type CHECK (adjustment_type IN ('Bonus', 'Deduction', 'Correction', 'Arrears', 'Reimbursement', 'Other'))
    )""",

    # ==========================================================================
    # 18. PAYROLL EXCEPTIONS - Exceptions during payroll processing
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_exceptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER,
        period_id INTEGER NOT NULL,
        employee_id INTEGER,
        exception_type TEXT NOT NULL,
        exception_code TEXT,
        severity TEXT DEFAULT 'Medium',
        error_message TEXT NOT NULL,
        error_details TEXT,
        field_name TEXT,
        field_value TEXT,
        status TEXT DEFAULT 'Open',
        resolved_by_id INTEGER,
        resolved_at DATETIME,
        resolution_notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (run_id) REFERENCES payroll_runs(id) ON DELETE SET NULL,
        FOREIGN KEY (period_id) REFERENCES payroll_periods(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE SET NULL,
        FOREIGN KEY (resolved_by_id) REFERENCES users(id) ON DELETE SET NULL,
        CONSTRAINT chk_severity CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
        CONSTRAINT chk_exception_status CHECK (status IN ('Open', 'Resolved', 'Ignored', 'Escalated'))
    )""",

    # ==========================================================================
    # 19. PAYSLIPS - Generated payslip records
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_payslips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payslip_number TEXT UNIQUE NOT NULL,
        period_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        record_id INTEGER,
        generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        generated_by_id INTEGER NOT NULL,
        file_path TEXT,
        file_size INTEGER,
        is_secure INTEGER DEFAULT 1,
        is_delivered INTEGER DEFAULT 0,
        delivered_at DATETIME,
        delivery_method TEXT,
        delivery_email TEXT,
        status TEXT DEFAULT 'Generated',
        approved_by_id INTEGER,
        approved_at DATETIME,
        employee_viewed INTEGER DEFAULT 0,
        employee_viewed_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (period_id) REFERENCES payroll_periods(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (record_id) REFERENCES payroll_employee_records(id) ON DELETE SET NULL,
        FOREIGN KEY (generated_by_id) REFERENCES users(id) ON DELETE RESTRICT,
        FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # ==========================================================================
    # 20. PAYSLIP EARNINGS/DEDUCTIONS - Itemized payslip details
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_payslip_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payslip_id INTEGER NOT NULL,
        component_id INTEGER,
        component_code TEXT NOT NULL,
        component_name TEXT NOT NULL,
        category TEXT NOT NULL,
        amount DECIMAL(12,2) NOT NULL,
        is_earning INTEGER DEFAULT 1,
        calculation_details TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (payslip_id) REFERENCES payroll_payslips(id) ON DELETE CASCADE,
        FOREIGN KEY (component_id) REFERENCES payroll_components(id) ON DELETE SET NULL
    )""",

    # ==========================================================================
    # 21. PAYROLL LOANS - Employee loans and advances
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_number TEXT UNIQUE NOT NULL,
        employee_id INTEGER NOT NULL,
        loan_type TEXT NOT NULL,
        component_id INTEGER,
        principal_amount DECIMAL(12,2) NOT NULL,
        interest_rate DECIMAL(5,2) DEFAULT 0,
        total_amount DECIMAL(12,2) NOT NULL,
        tenure_months INTEGER NOT NULL,
        monthly_installment DECIMAL(12,2) NOT NULL,
        amount_paid DECIMAL(12,2) DEFAULT 0,
        amount_remaining DECIMAL(12,2) NOT NULL,
        installments_paid INTEGER DEFAULT 0,
        installments_remaining INTEGER NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE,
        recovery_start_period_id INTEGER,
        recovery_end_period_id INTEGER,
        status TEXT DEFAULT 'Active',
        is_interest_free INTEGER DEFAULT 0,
        is_salary_advance INTEGER DEFAULT 0,
        max_advance_percentage DECIMAL(5,2),
        approved_by_id INTEGER,
        approved_at DATETIME,
        remarks TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (component_id) REFERENCES payroll_components(id) ON DELETE SET NULL,
        FOREIGN KEY (recovery_start_period_id) REFERENCES payroll_periods(id) ON DELETE SET NULL,
        FOREIGN KEY (recovery_end_period_id) REFERENCES payroll_periods(id) ON DELETE SET NULL,
        FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL,
        CONSTRAINT chk_loan_status CHECK (status IN ('Pending', 'Active', 'Completed', 'Cancelled', 'Suspended', 'Written Off'))
    )""",

    # ==========================================================================
    # 22. PAYROLL LOAN INSTALLMENTS - Individual installment records
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_loan_installments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_id INTEGER NOT NULL,
        installment_number INTEGER NOT NULL,
        period_id INTEGER,
        due_date DATE NOT NULL,
        installment_amount DECIMAL(12,2) NOT NULL,
        principal_amount DECIMAL(12,2) NOT NULL,
        interest_amount DECIMAL(12,2) DEFAULT 0,
        amount_paid DECIMAL(12,2) DEFAULT 0,
        paid_on DATE,
        status TEXT DEFAULT 'Pending',
        included_in_run_id INTEGER,
        included_in_record_id INTEGER,
        paid_by_id INTEGER,
        paid_at DATETIME,
        remarks TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (loan_id) REFERENCES payroll_loans(id) ON DELETE CASCADE,
        FOREIGN KEY (period_id) REFERENCES payroll_periods(id) ON DELETE SET NULL,
        FOREIGN KEY (included_in_run_id) REFERENCES payroll_runs(id) ON DELETE SET NULL,
        FOREIGN KEY (included_in_record_id) REFERENCES payroll_employee_records(id) ON DELETE SET NULL,
        FOREIGN KEY (paid_by_id) REFERENCES users(id) ON DELETE SET NULL,
        UNIQUE(loan_id, installment_number),
        CONSTRAINT chk_installment_status CHECK (status IN ('Pending', 'Due', 'Paid', 'Overdue', 'Waived', 'Cancelled'))
    )""",

    # ==========================================================================
    # 23. PAYROLL ADVANCES - Salary advances
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_advances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        advance_number TEXT UNIQUE NOT NULL,
        employee_id INTEGER NOT NULL,
        amount DECIMAL(12,2) NOT NULL,
        recovery_amount DECIMAL(12,2),
        recovery_months INTEGER DEFAULT 1,
        monthly_recovery DECIMAL(12,2),
        currency TEXT DEFAULT 'AED',
        reason TEXT,
        status TEXT DEFAULT 'Pending',
        approved_by_id INTEGER,
        approved_at DATETIME,
        recovery_start_period_id INTEGER,
        recovery_end_period_id INTEGER,
        fully_recovered INTEGER DEFAULT 0,
        fully_recovered_on DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (recovery_start_period_id) REFERENCES payroll_periods(id) ON DELETE SET NULL,
        FOREIGN KEY (recovery_end_period_id) REFERENCES payroll_periods(id) ON DELETE SET NULL,
        CONSTRAINT chk_advance_status CHECK (status IN ('Pending', 'Approved', 'Rejected', 'In Recovery', 'Completed', 'Cancelled'))
    )""",

    # ==========================================================================
    # 24. PAYROLL RETRO ADJUSTMENTS - Retroactive adjustments
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_retro_adjustments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        retro_number TEXT UNIQUE NOT NULL,
        employee_id INTEGER NOT NULL,
        period_id INTEGER NOT NULL,
        original_period_id INTEGER,
        adjustment_type TEXT NOT NULL,
        component_id INTEGER,
        component_code TEXT,
        component_name TEXT,
        original_amount DECIMAL(12,2) DEFAULT 0,
        new_amount DECIMAL(12,2) DEFAULT 0,
        difference DECIMAL(12,2) NOT NULL,
        difference_type TEXT DEFAULT 'Arrears',
        is_taxable INTEGER DEFAULT 1,
        tax_adjustment DECIMAL(12,2) DEFAULT 0,
        total_adjustment DECIMAL(12,2) NOT NULL,
        reason TEXT NOT NULL,
        effective_date DATE,
        status TEXT DEFAULT 'Pending',
        approved_by_id INTEGER,
        approved_at DATETIME,
        included_in_run_id INTEGER,
        included_in_record_id INTEGER,
        processed INTEGER DEFAULT 0,
        processed_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (period_id) REFERENCES payroll_periods(id) ON DELETE RESTRICT,
        FOREIGN KEY (original_period_id) REFERENCES payroll_periods(id) ON DELETE SET NULL,
        FOREIGN KEY (component_id) REFERENCES payroll_components(id) ON DELETE SET NULL,
        FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (included_in_run_id) REFERENCES payroll_runs(id) ON DELETE SET NULL,
        FOREIGN KEY (included_in_record_id) REFERENCES payroll_employee_records(id) ON DELETE SET NULL,
        CONSTRAINT chk_retro_status CHECK (status IN ('Pending', 'Approved', 'Rejected', 'In Payroll', 'Processed', 'Cancelled'))
    )""",

    # ==========================================================================
    # 25. PAYROLL ARREARS - Arrears register
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_arrears (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        arrears_number TEXT UNIQUE NOT NULL,
        employee_id INTEGER NOT NULL,
        period_id INTEGER NOT NULL,
        retro_adjustment_id INTEGER,
        component_id INTEGER,
        arrears_type TEXT NOT NULL,
        amount DECIMAL(12,2) NOT NULL,
        tax_amount DECIMAL(12,2) DEFAULT 0,
        total_amount DECIMAL(12,2) NOT NULL,
        periods_due INTEGER DEFAULT 1,
        installments_plan INTEGER,
        status TEXT DEFAULT 'Pending',
        recovery_start_period_id INTEGER,
        recovery_method TEXT DEFAULT 'Lump Sum',
        approved_by_id INTEGER,
        approved_at DATETIME,
        included_in_run_id INTEGER,
        included_in_record_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (period_id) REFERENCES payroll_periods(id) ON DELETE RESTRICT,
        FOREIGN KEY (retro_adjustment_id) REFERENCES payroll_retro_adjustments(id) ON DELETE SET NULL,
        FOREIGN KEY (component_id) REFERENCES payroll_components(id) ON DELETE SET NULL,
        FOREIGN KEY (recovery_start_period_id) REFERENCES payroll_periods(id) ON DELETE SET NULL,
        FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (included_in_run_id) REFERENCES payroll_runs(id) ON DELETE SET NULL,
        FOREIGN KEY (included_in_record_id) REFERENCES payroll_employee_records(id) ON DELETE SET NULL,
        CONSTRAINT chk_arrears_status CHECK (status IN ('Pending', 'Approved', 'In Recovery', 'Recovered', 'Waived', 'Cancelled'))
    )""",

    # ==========================================================================
    # 26. PAYROLL COMPLIANCE VALIDATIONS - Compliance rule definitions
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_compliance_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_code TEXT UNIQUE NOT NULL,
        rule_name TEXT NOT NULL,
        description TEXT,
        rule_type TEXT NOT NULL,
        severity TEXT DEFAULT 'High',
        is_active INTEGER DEFAULT 1,
        validation_query TEXT,
        error_message TEXT,
        error_message_ar TEXT,
        error_message_fa TEXT,
        remediation TEXT,
        requires_approval INTEGER DEFAULT 0,
        auto_resolve INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT chk_rule_type CHECK (rule_type IN ('Validation', 'SOD', 'Security', 'Audit', 'Regulatory', 'Custom'))
    )""",

    # ==========================================================================
    # 27. PAYROLL COMPLIANCE RESULTS - Results of compliance checks
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_compliance_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period_id INTEGER NOT NULL,
        rule_id INTEGER NOT NULL,
        employee_id INTEGER,
        run_id INTEGER,
        status TEXT DEFAULT 'Pass',
        details TEXT,
        remediation_notes TEXT,
        resolved_by_id INTEGER,
        resolved_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (period_id) REFERENCES payroll_periods(id) ON DELETE CASCADE,
        FOREIGN KEY (rule_id) REFERENCES payroll_compliance_rules(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE SET NULL,
        FOREIGN KEY (run_id) REFERENCES payroll_runs(id) ON DELETE SET NULL,
        FOREIGN KEY (resolved_by_id) REFERENCES users(id) ON DELETE SET NULL,
        CONSTRAINT chk_compliance_status CHECK (status IN ('Pass', 'Fail', 'Warning', 'Ignored', 'Escalated'))
    )""",

    # ==========================================================================
    # 28. PAYROLL FINANCE POSTING - Integration with finance module
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_finance_postings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        posting_number TEXT UNIQUE NOT NULL,
        period_id INTEGER NOT NULL,
        run_id INTEGER,
        posting_type TEXT NOT NULL,
        journal_date DATE,
        description TEXT,
        total_amount DECIMAL(14,2) DEFAULT 0,
        currency TEXT DEFAULT 'AED',
        exchange_rate DECIMAL(10,4) DEFAULT 1.0000,
        status TEXT DEFAULT 'Draft',
        posted_by_id INTEGER,
        posted_at DATETIME,
        approved_by_id INTEGER,
        approved_at DATETIME,
        posting_reference TEXT,
        source_module TEXT DEFAULT 'Payroll',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (period_id) REFERENCES payroll_periods(id) ON DELETE CASCADE,
        FOREIGN KEY (run_id) REFERENCES payroll_runs(id) ON DELETE SET NULL,
        FOREIGN KEY (posted_by_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL,
        CONSTRAINT chk_posting_type CHECK (posting_type IN ('Salary', 'Tax', 'Insurance', 'Loan', 'Bonus', 'Allowance', 'Deduction', 'Arrears', 'Reconciliation')),
        CONSTRAINT chk_posting_status CHECK (status IN ('Draft', 'Pending', 'Posted', 'Rejected', 'Cancelled'))
    )""",

    # ==========================================================================
    # 29. PAYROLL FINANCE LINES - Individual journal lines
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_finance_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        posting_id INTEGER NOT NULL,
        employee_id INTEGER,
        gl_account TEXT NOT NULL,
        cost_center TEXT,
        department_id INTEGER,
        branch_id INTEGER,
        line_type TEXT NOT NULL,
        description TEXT,
        debit_amount DECIMAL(12,2) DEFAULT 0,
        credit_amount DECIMAL(12,2) DEFAULT 0,
        currency TEXT DEFAULT 'AED',
        exchange_rate DECIMAL(10,4) DEFAULT 1.0000,
        base_amount DECIMAL(12,2) DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (posting_id) REFERENCES payroll_finance_postings(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE SET NULL,
        CONSTRAINT chk_line_type CHECK (line_type IN ('Debit', 'Credit'))
    )""",

    # ==========================================================================
    # 30. PAYROLL COST CENTER ALLOCATION - Cost center distribution
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_cost_allocations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        cost_center TEXT NOT NULL,
        percentage DECIMAL(6,2) NOT NULL,
        amount DECIMAL(12,2) DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        effective_from DATE NOT NULL,
        effective_to DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (period_id) REFERENCES payroll_periods(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        UNIQUE(period_id, employee_id, cost_center)
    )""",

    # ==========================================================================
    # 31. PAYROLL APPROVAL WORKFLOW - Approval workflow definitions
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_approval_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_name TEXT NOT NULL,
        rule_code TEXT UNIQUE NOT NULL,
        approval_type TEXT NOT NULL,
        priority INTEGER DEFAULT 1,
        conditions TEXT,
        approver_role TEXT,
        approver_user_id INTEGER,
        escalation_user_id INTEGER,
        escalation_days INTEGER DEFAULT 3,
        requires_all_approvals INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (approver_user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (escalation_user_id) REFERENCES users(id) ON DELETE SET NULL,
        CONSTRAINT chk_approval_type CHECK (approval_type IN ('Payroll Run', 'Period Close', 'Adjustment', 'Exception', 'Retro', 'Payslip Release', 'Period Unlock'))
    )""",

    # ==========================================================================
    # 32. PAYROLL APPROVAL INSTANCES - Active approval records
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_approval_instances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        approval_rule_id INTEGER,
        period_id INTEGER,
        run_id INTEGER,
        employee_id INTEGER,
        approval_type TEXT NOT NULL,
        status TEXT DEFAULT 'Pending',
        priority INTEGER DEFAULT 1,
        requested_by_id INTEGER NOT NULL,
        requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        approver_id INTEGER,
        approver_action TEXT,
        approver_comments TEXT,
        approver_action_at DATETIME,
        escalated INTEGER DEFAULT 0,
        escalated_at DATETIME,
        escalation_reason TEXT,
        due_date DATE,
        completed_at DATETIME,
        sla_breached INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (approval_rule_id) REFERENCES payroll_approval_rules(id) ON DELETE SET NULL,
        FOREIGN KEY (period_id) REFERENCES payroll_periods(id) ON DELETE SET NULL,
        FOREIGN KEY (run_id) REFERENCES payroll_runs(id) ON DELETE SET NULL,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE SET NULL,
        FOREIGN KEY (requested_by_id) REFERENCES users(id) ON DELETE RESTRICT,
        FOREIGN KEY (approver_id) REFERENCES users(id) ON DELETE SET NULL,
        CONSTRAINT chk_approval_status CHECK (status IN ('Pending', 'Approved', 'Rejected', 'Returned', 'Escalated', 'Cancelled'))
    )""",

    # ==========================================================================
    # 33. PAYROLL APPROVAL DELEGATIONS - User delegations
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_approval_delegations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        delegator_id INTEGER NOT NULL,
        delegate_id INTEGER NOT NULL,
        approval_type TEXT,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        reason TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (delegator_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (delegate_id) REFERENCES users(id) ON DELETE CASCADE
    )""",

    # ==========================================================================
    # 34. PAYROLL AUDIT LOG - Comprehensive audit trail
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period_id INTEGER,
        run_id INTEGER,
        employee_id INTEGER,
        action TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id INTEGER,
        field_name TEXT,
        old_value TEXT,
        new_value TEXT,
        change_details TEXT,
        ip_address TEXT,
        user_agent TEXT,
        user_id INTEGER NOT NULL,
        user_role TEXT,
        approval_instance_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (period_id) REFERENCES payroll_periods(id) ON DELETE SET NULL,
        FOREIGN KEY (run_id) REFERENCES payroll_runs(id) ON DELETE SET NULL,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE SET NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
        FOREIGN KEY (approval_instance_id) REFERENCES payroll_approval_instances(id) ON DELETE SET NULL
    )""",

    # ==========================================================================
    # 35. PAYROLL SETTINGS - Module configuration
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_key TEXT UNIQUE NOT NULL,
        setting_value TEXT,
        setting_type TEXT DEFAULT 'String',
        description TEXT,
        category TEXT,
        is_encrypted INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_by INTEGER,
        CONSTRAINT chk_setting_type CHECK (setting_type IN ('String', 'Number', 'Boolean', 'JSON', 'Password'))
    )""",

    # ==========================================================================
    # 36. PAYROLL TAX BRACKETS - Tax configuration
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_tax_brackets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bracket_name TEXT NOT NULL,
        country TEXT NOT NULL,
        min_income DECIMAL(12,2) NOT NULL,
        max_income DECIMAL(12,2),
        tax_rate DECIMAL(6,2) NOT NULL,
        fixed_amount DECIMAL(12,2) DEFAULT 0,
        effective_from DATE NOT NULL,
        effective_to DATE,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT chk_country CHECK (country IN ('UAE', 'SA', 'KW', 'BH', 'OM', 'QA', 'EG', 'JO', 'Other'))
    )""",

    # ==========================================================================
    # 37. PAYROLL INSURANCE RATES - Insurance contribution rates
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_insurance_rates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rate_name TEXT NOT NULL,
        country TEXT NOT NULL,
        employee_rate DECIMAL(6,2) NOT NULL,
        employer_rate DECIMAL(6,2) NOT NULL,
        minimum_salary DECIMAL(12,2) DEFAULT 0,
        maximum_salary DECIMAL(12,2),
        is_active INTEGER DEFAULT 1,
        effective_from DATE NOT NULL,
        effective_to DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # ==========================================================================
    # 38. PAYROLL ATTENDANCE INTEGRATION - HR attendance to payroll linkage
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_attendance_integration (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        attendance_record_id INTEGER,
        leave_request_id INTEGER,
        late_deduction_amount DECIMAL(12,2) DEFAULT 0,
        absent_deduction_amount DECIMAL(12,2) DEFAULT 0,
        leave_deduction_amount DECIMAL(12,2) DEFAULT 0,
        net_attendance_amount DECIMAL(12,2) DEFAULT 0,
        status TEXT DEFAULT 'Pending',
        processed INTEGER DEFAULT 0,
        processed_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (period_id) REFERENCES payroll_periods(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (attendance_record_id) REFERENCES hr_attendance_records(id) ON DELETE SET NULL,
        FOREIGN KEY (leave_request_id) REFERENCES hr_leave_requests(id) ON DELETE SET NULL
    )""",

    # ==========================================================================
    # 39. PAYROLL EXPORT CONFIGURATIONS - Export settings
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_export_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        config_name TEXT NOT NULL,
        export_type TEXT NOT NULL,
        columns_selected TEXT,
        column_order TEXT,
        filters TEXT,
        grouping TEXT,
        sort_order TEXT,
        file_format TEXT DEFAULT 'Excel',
        is_default INTEGER DEFAULT 0,
        created_by_id INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE RESTRICT,
        CONSTRAINT chk_export_type CHECK (export_type IN ('Payroll Summary', 'Earnings Report', 'Deductions Report', 'Payslip', 'Bank File', 'Tax Report', 'Custom'))
    )""",

    # ==========================================================================
    # 40. PAYROLL EXPORT HISTORY - Export audit trail
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_export_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        export_config_id INTEGER,
        period_id INTEGER,
        export_type TEXT NOT NULL,
        file_name TEXT,
        file_path TEXT,
        file_size INTEGER,
        record_count INTEGER,
        exported_by_id INTEGER NOT NULL,
        exported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (export_config_id) REFERENCES payroll_export_configs(id) ON DELETE SET NULL,
        FOREIGN KEY (period_id) REFERENCES payroll_periods(id) ON DELETE SET NULL,
        FOREIGN KEY (exported_by_id) REFERENCES users(id) ON DELETE RESTRICT
    )""",

    # ==========================================================================
    # 41. PAYROLL FLOW NOTIFICATIONS - Flow integration
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_flow_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        notification_key TEXT NOT NULL,
        period_id INTEGER,
        run_id INTEGER,
        title TEXT NOT NULL,
        message TEXT,
        notification_type TEXT DEFAULT 'Info',
        priority TEXT DEFAULT 'Normal',
        channels TEXT,
        recipient_roles TEXT,
        recipient_user_ids TEXT,
        is_sent INTEGER DEFAULT 0,
        sent_at DATETIME,
        sent_by_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (period_id) REFERENCES payroll_periods(id) ON DELETE SET NULL,
        FOREIGN KEY (run_id) REFERENCES payroll_runs(id) ON DELETE SET NULL,
        FOREIGN KEY (sent_by_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # ==========================================================================
    # 42. PAYROLL LETTERS - Payroll letters scaffold
    # ==========================================================================
    """CREATE TABLE IF NOT EXISTS payroll_letters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        letter_number TEXT UNIQUE NOT NULL,
        period_id INTEGER,
        employee_id INTEGER NOT NULL,
        letter_type TEXT NOT NULL,
        subject TEXT,
        content TEXT,
        status TEXT DEFAULT 'Draft',
        approved_by_id INTEGER,
        approved_at DATETIME,
        delivered INTEGER DEFAULT 0,
        delivered_at DATETIME,
        delivery_method TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (period_id) REFERENCES payroll_periods(id) ON DELETE SET NULL,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (approved_by_id) REFERENCES users(id) ON DELETE SET NULL,
        CONSTRAINT chk_letter_type CHECK (letter_type IN ('Salary Certificate', 'Salary Increase', 'Employment Confirmation', 'Tax Certificate', 'Bank Letter', 'Custom')),
        CONSTRAINT chk_letter_status CHECK (status IN ('Draft', 'Pending Approval', 'Approved', 'Delivered', 'Cancelled'))
    )""",
]


# =============================================================================
# MIGRATION FUNCTION
# =============================================================================

def run_payroll_migrations():
    """Run all payroll table migrations."""
    db = get_db()
    try:
        for table_sql in PAYROLL_TABLES:
            db.execute(table_sql)
        db.commit()
        
        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_payroll_period_status ON payroll_periods(status)",
            "CREATE INDEX IF NOT EXISTS idx_payroll_period_year_month ON payroll_periods(year, month)",
            "CREATE INDEX IF NOT EXISTS idx_payroll_runs_period ON payroll_runs(period_id)",
            "CREATE INDEX IF NOT EXISTS idx_payroll_records_run ON payroll_employee_records(run_id)",
            "CREATE INDEX IF NOT EXISTS idx_payroll_records_employee ON payroll_employee_records(employee_id)",
            "CREATE INDEX IF NOT EXISTS idx_payroll_records_period ON payroll_employee_records(period_id)",
            "CREATE INDEX IF NOT EXISTS idx_payroll_exceptions_period ON payroll_exceptions(period_id)",
            "CREATE INDEX IF NOT EXISTS idx_payroll_exceptions_status ON payroll_exceptions(status)",
            "CREATE INDEX IF NOT EXISTS idx_payroll_loans_employee ON payroll_loans(employee_id)",
            "CREATE INDEX IF NOT EXISTS idx_payroll_loans_status ON payroll_loans(status)",
            "CREATE INDEX IF NOT EXISTS idx_payroll_advances_employee ON payroll_advances(employee_id)",
            "CREATE INDEX IF NOT EXISTS idx_payroll_retro_employee ON payroll_retro_adjustments(employee_id)",
            "CREATE INDEX IF NOT EXISTS idx_payroll_audit_period ON payroll_audit_log(period_id)",
            "CREATE INDEX IF NOT EXISTS idx_payroll_audit_employee ON payroll_audit_log(employee_id)",
            "CREATE INDEX IF NOT EXISTS idx_payroll_audit_user ON payroll_audit_log(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_payroll_payslips_employee ON payroll_payslips(employee_id)",
            "CREATE INDEX IF NOT EXISTS idx_payroll_payslips_period ON payroll_payslips(period_id)",
            "CREATE INDEX IF NOT EXISTS idx_payroll_finance_postings_period ON payroll_finance_postings(period_id)",
            "CREATE INDEX IF NOT EXISTS idx_payroll_approval_instances_status ON payroll_approval_instances(status)",
            "CREATE INDEX IF NOT EXISTS idx_payroll_components_type ON payroll_components(component_type)",
        ]
        for index_sql in indexes:
            db.execute(index_sql)
        db.commit()
        
        print(f"Payroll migrations completed successfully. Created {len(PAYROLL_TABLES)} tables.")
    except Exception as e:
        db.rollback()
        print(f"Payroll migration error: {str(e)}")
        raise
    finally:
        db.close()


def seed_payroll_default_data():
    """Seed default payroll configuration data."""
    db = get_db()
    try:
        # Check if already seeded
        existing = db.execute("SELECT COUNT(*) as cnt FROM payroll_settings").fetchone()['cnt']
        if existing > 0:
            print("Payroll default data already exists.")
            return
        
        # Seed default settings
        default_settings = [
            ('payroll_currency', 'AED', 'String', 'Default payroll currency'),
            ('payroll_decimal_places', '2', 'Number', 'Decimal places for amounts'),
            ('overtime_rate_weekday', '1.50', 'Number', 'Overtime multiplier for weekdays'),
            ('overtime_rate_weekend', '2.00', 'Number', 'Overtime multiplier for weekends'),
            ('overtime_rate_holiday', '2.50', 'Number', 'Overtime multiplier for holidays'),
            ('late_minute_deduction_rate', '0.00', 'Number', 'Deduction rate per late minute'),
            ('absent_day_deduction_rate', '1.00', 'Number', 'Deduction rate per absent day'),
            ('auto_generate_payslips', 'true', 'Boolean', 'Auto-generate payslips after payroll'),
            ('require_payslip_approval', 'false', 'Boolean', 'Require approval before payslip release'),
            ('default_payment_method', 'Bank Transfer', 'String', 'Default salary payment method'),
            ('enable_payroll_approval_workflow', 'true', 'Boolean', 'Enable payroll approval workflow'),
            ('payroll_run_validation_required', 'true', 'Boolean', 'Require pre-run validation'),
            ('lock_period_on_approval', 'true', 'Boolean', 'Lock period when payroll is approved'),
            ('retro_processing_enabled', 'true', 'Boolean', 'Enable retroactive adjustments'),
            ('loan_recovery_auto', 'true', 'Boolean', 'Auto-deduct loan installments'),
            ('tax_calculation_method', 'UAE_WPS', 'String', 'Tax calculation method'),
        ]
        
        for key, value, stype, desc in default_settings:
            db.execute("""
                INSERT INTO payroll_settings (setting_key, setting_value, setting_type, description)
                VALUES (?, ?, ?, ?)
            """, (key, value, stype, desc))
        
        # Seed default payroll components
        default_components = [
            # Earnings
            ('BASIC', 'Basic Salary', 'Basic Salary', 'Basic Salary', 'Basic Salary', 'Basic Salary', 'Basic Salary', 'Basic Salary', 'Basic Salary', 'Earning', 'Salary', 'Base salary component', 1, 1, 1, 'Fixed', 0, 0, NULL, NULL, 1, 0, 0, 1),
            ('HRA', 'House Rent Allowance', 'بدل إيجار السكن', 'کمک هزینه مسکن', 'Housing Allowance', 'Allocation de logement', '房屋补贴', 'Mietzulage', 'Allowance', 'Housing', 'House rent allowance', 1, 1, 0, 'Percentage', 0, 25.0, 'BASIC', NULL, NULL, 2, 0, 0, 1),
            ('TRANSPORT', 'Transport Allowance', 'بدل انتقالات', 'کمک هزینه حمل و نقل', 'Transport Allowance', 'Allocation transport', '交通补贴', 'Transportzulage', 'Allowance', 'Transport', 'Transport allowance', 0, 0, 0, 'Fixed', 0, 0, NULL, NULL, 3, 0, 0, 1),
            ('MEDICAL', 'Medical Allowance', 'بدل طبي', 'کمک هزینه پزشکی', 'Medical Allowance', 'Allocation médicale', '医疗补贴', 'Medizinische Zulage', 'Allowance', 'Medical', 'Medical allowance', 0, 0, 0, 'Fixed', 0, 0, NULL, NULL, 4, 0, 0, 1),
            ('OT_REG', 'Overtime - Regular', 'عمل إضافي - عادي', 'اضافه کاری - عادی', 'Overtime - Regular', 'Heures supplémentaires - Régulier', '加班 - 常规', 'Überstunden - Regulär', 'Earning', 'Overtime', 'Regular overtime hours', 1, 1, 0, 'Hourly', 0, 0, NULL, NULL, 10, 0, 0, 1),
            ('OT_Wknd', 'Overtime - Weekend', 'عمل إضافي - نهاية الأسبوع', 'اضافه کاری - آخر هفته', 'Overtime - Weekend', 'Heures supplémentaires - Week-end', '加班 - 周末', 'Überstunden - Wochenende', 'Earning', 'Overtime', 'Weekend overtime', 1, 1, 0, 'Hourly', 0, 0, NULL, NULL, 11, 0, 0, 1),
            ('OT_Hol', 'Overtime - Holiday', 'عمل إضافي - يوم عطل', 'اضافه کاری - تعطیل', 'Overtime - Holiday', 'Heures supplémentaires - Jour férié', '加班 - 假日', 'Überstunden - Feiertag', 'Earning', 'Overtime', 'Holiday overtime', 1, 1, 0, 'Hourly', 0, 0, NULL, NULL, 12, 0, 0, 1),
            ('BONUS', 'Bonus', 'مكافأة', 'پاداش', 'Bonus', 'Prime', '奖金', 'Bonus', 'Earning', 'Bonus', 'Performance bonus', 1, 1, 0, 'Variable', 0, 0, NULL, NULL, 15, 0, 1, 1),
            ('COMMISSION', 'Commission', 'عمولة', 'کمیسیون', 'Commission', 'Commission', '佣金', 'Provision', 'Earning', 'Variable', 'Sales commission', 1, 1, 0, 'Variable', 0, 0, NULL, NULL, 16, 0, 1, 1),
            # Deductions
            ('TAX', 'Income Tax', 'ضريبة الدخل', 'مالیات', 'Income Tax', 'Impôt sur le revenu', '所得税', 'Einkommensteuer', 'Tax', 'Tax', 'Income tax deduction', 0, 0, 0, 'calculated', 0, 0, NULL, NULL, 50, 0, 1, 1),
            ('PF_EE', 'Provident Fund - Employee', 'صندوق التقاعد - الموظف', 'صندوق بازنشستگی - کارمند', 'Provident Fund - Employee', 'CPF - Employé', '公积金 - 员工', 'Rentenversicherung - AN', 'Contribution', 'PF', 'Employee provident fund contribution', 0, 0, 0, 'Percentage', 0, 5.0, 'BASIC', 5000, 15000, 51, 0, 1, 1),
            ('PF_ER', 'Provident Fund - Employer', 'صندوق التقاعد - صاحب العمل', 'صندوق بازنشستگی - کارفرما', 'Provident Fund - Employer', 'CPF - Employeur', '公积金 - 雇主', 'Rentenversicherung - AG', 'Contribution', 'PF', 'Employer provident fund contribution', 0, 0, 0, 'Percentage', 0, 12.0, 'BASIC', 5000, 15000, 52, 0, 1, 1),
            ('LOAN_RECV', 'Loan Recovery', 'استرداد قرض', 'بازپرداخت وام', 'Loan Recovery', 'Remboursement prêt', '贷款还款', 'Kreditrückzahlung', 'Deduction', 'Loan', 'Loan installment recovery', 0, 0, 0, 'calculated', 0, 0, NULL, NULL, 55, 0, 0, 1),
            ('ADV_RECV', 'Advance Recovery', 'استرداد سلفة', 'بازپرداخت پیش پرداخت', 'Advance Recovery', 'Remboursement avance', '预付款还款', 'Vorschussrückzahlung', 'Deduction', 'Advance', 'Salary advance recovery', 0, 0, 0, 'calculated', 0, 0, NULL, NULL, 56, 0, 0, 1),
            ('ABSENT', 'Absent Deduction', 'خصم الغياب', 'کسر غیبت', 'Absent Deduction', 'Déduction absence', '缺勤扣除', 'Abwesenheitsabzug', 'Deduction', 'Attendance', 'Deduction for absent days', 0, 0, 0, 'calculated', 0, 0, NULL, NULL, 60, 0, 0, 1),
            ('LATE', 'Late Deduction', 'خصم التأخير', 'کسر دیرکرد', 'Late Deduction', 'Déduction retard', '迟到扣除', 'Verspätungsabzug', 'Deduction', 'Attendance', 'Deduction for late arrivals', 0, 0, 0, 'calculated', 0, 0, NULL, NULL, 61, 0, 0, 1),
            ('PENALTY', 'Penalty Deduction', 'خصم جزائي', 'کسر جریمه', 'Penalty Deduction', 'Déduction pénalité', '罚款扣除', 'Strafabzug', 'Deduction', 'Penalty', 'Penalty deduction', 0, 0, 0, 'Variable', 0, 0, NULL, NULL, 65, 0, 1, 1),
            # Arrears/Adjustments
            ('ARREARS', 'Arrears', 'العدادات', 'معوقات', 'Arrears', 'Arriérés', '欠款', 'Rückstände', 'Arrears', 'Adjustment', 'Arrears payment', 1, 1, 0, 'Variable', 0, 0, NULL, NULL, 70, 0, 0, 1),
            ('ADJUST', 'Adjustment', 'تعديل', 'تعدیل', 'Adjustment', 'Ajustement', '调整', 'Anpassung', 'Adjustment', 'Correction', 'Manual adjustment', 1, 1, 0, 'Variable', 0, 0, NULL, NULL, 71, 0, 1, 1),
        ]
        
        for comp in default_components:
            db.execute("""
                INSERT INTO payroll_components (
                    code, name, name_ar, name_fa, name_ru, name_hi, name_es, name_zh, name_de,
                    component_type, sub_type, description, is_taxable, is_insurable, is_default,
                    calculation_type, amount, percentage, percentage_of, max_amount, min_amount,
                    order_index, requires_approval, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, comp)
        
        # Seed default payroll groups
        default_groups = [
            ('GRP_ALL', 'All Employees', 'جميع الموظفين', 'همه کارکنان', 'Default group for all employees', 1, 1),
            ('GRP_EXEC', 'Executive', 'التنفيذي', 'مدیران', 'Executive staff group', 1, 0),
            ('GRP_MGR', 'Managers', 'المدراء', 'مدیران', 'Management staff group', 1, 0),
            ('GRP_STAFF', 'Staff', 'الموظفين', 'کارکنان', 'Regular staff group', 1, 0),
        ]
        
        for grp in default_groups:
            db.execute("""
                INSERT INTO payroll_groups (code, name, name_ar, name_fa, description, is_active, is_default)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, grp)
        
        # Seed compliance rules
        compliance_rules = [
            ('PAY_001', 'Minimum Salary Check', 'Verify employee salary meets minimum wage requirements', 'Validation', 'High', 'Minimum salary not met for employee', 'Ensure salary meets statutory minimum'),
            ('PAY_002', 'Maximum Overtime Hours', 'Verify overtime hours do not exceed statutory limits', 'Validation', 'Medium', 'Overtime hours exceed maximum limit', 'Review and reduce overtime or split with another employee'),
            ('PAY_003', 'Bank Details Complete', 'Verify all employees have complete bank account details', 'Validation', 'High', 'Incomplete bank account details', 'Request employee to update bank details'),
            ('PAY_004', 'Tax ID Validation', 'Verify all employees have valid tax IDs', 'Regulatory', 'High', 'Missing or invalid tax ID', 'Request employee to provide valid tax documentation'),
            ('PAY_005', 'SOD Payroll Processor', 'Separation of duties - payroll processor cannot approve', 'SOD', 'Critical', 'SOD violation detected', 'Assign approval to different role'),
            ('PAY_006', 'Period Lock Check', 'Verify no changes to locked periods', 'Security', 'Critical', 'Attempt to modify locked period', 'Contact administrator immediately'),
            ('PAY_007', 'Duplicate Payment Check', 'Verify no duplicate salary payments', 'Validation', 'Critical', 'Potential duplicate payment detected', 'Review and verify payment before processing'),
            ('PAY_008', 'Leave Without Pay', 'Track employees on leave without pay', 'Audit', 'Medium', 'Employee on leave without pay detected', 'Verify leave documentation'),
        ]
        
        for rule in compliance_rules:
            db.execute("""
                INSERT INTO payroll_compliance_rules (rule_code, rule_name, description, rule_type, severity, error_message, remediation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, rule)
        
        # Seed tax brackets for UAE
        tax_brackets = [
            ('UAE Tax Bracket 1', 'UAE', 0, 10000, 0, 0, '2023-01-01', None, 1),
            ('UAE Tax Bracket 2', 'UAE', 10000, 20000, 10, 0, '2023-01-01', None, 1),
            ('UAE Tax Bracket 3', 'UAE', 20000, 30000, 15, 1000, '2023-01-01', None, 1),
            ('UAE Tax Bracket 4', 'UAE', 30000, None, 20, 2500, '2023-01-01', None, 1),
        ]
        
        for bracket in tax_brackets:
            db.execute("""
                INSERT INTO payroll_tax_brackets (bracket_name, country, min_income, max_income, tax_rate, fixed_amount, effective_from, effective_to, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, bracket)
        
        db.commit()
        print("Payroll default data seeded successfully.")
    except Exception as e:
        db.rollback()
        print(f"Payroll seed error: {str(e)}")
        raise
    finally:
        db.close()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_payroll_setting(key: str, default: str = None) -> Optional[str]:
    """Get a payroll setting value."""
    db = get_db()
    try:
        row = db.execute(
            "SELECT setting_value FROM payroll_settings WHERE setting_key = ? AND is_active = 1",
            (key,)
        ).fetchone()
        return row['setting_value'] if row else default
    finally:
        db.close()


def update_payroll_setting(key: str, value: str, updated_by: int = None) -> bool:
    """Update a payroll setting."""
    db = get_db()
    try:
        db.execute("""
            UPDATE payroll_settings 
            SET setting_value = ?, updated_at = CURRENT_TIMESTAMP, updated_by = ?
            WHERE setting_key = ?
        """, (value, updated_by, key))
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()


def get_active_payroll_period() -> Optional[Dict]:
    """Get the currently active payroll period."""
    db = get_db()
    try:
        row = db.execute("""
            SELECT * FROM payroll_periods 
            WHERE status IN ('Open', 'Processing') 
            ORDER BY year DESC, month DESC 
            LIMIT 1
        """).fetchone()
        return dict(row) if row else None
    finally:
        db.close()


def get_payroll_period(year: int, month: int) -> Optional[Dict]:
    """Get a specific payroll period."""
    db = get_db()
    try:
        row = db.execute("""
            SELECT * FROM payroll_periods 
            WHERE year = ? AND month = ?
        """, (year, month)).fetchone()
        return dict(row) if row else None
    finally:
        db.close()


def get_employee_payroll_profile(employee_id: int) -> Optional[Dict]:
    """Get an employee's payroll profile."""
    db = get_db()
    try:
        row = db.execute("""
            SELECT pp.*, pg.name as group_name
            FROM payroll_profiles pp
            LEFT JOIN payroll_groups pg ON pp.payroll_group_id = pg.id
            WHERE pp.employee_id = ? AND pp.is_active = 1
        """, (employee_id,)).fetchone()
        return dict(row) if row else None
    finally:
        db.close()


def get_employee_components(employee_id: int, effective_date: date = None) -> List[Dict]:
    """Get an employee's payroll components with amounts."""
    db = get_db()
    try:
        if effective_date is None:
            effective_date = date.today()
        
        rows = db.execute("""
            SELECT pc.*, ppc.amount, ppc.percentage, ppc.calculation_type
            FROM payroll_profile_components ppc
            JOIN payroll_components pc ON ppc.component_id = pc.id
            JOIN payroll_profiles pp ON ppc.profile_id = pp.id
            WHERE pp.employee_id = ? 
            AND pp.is_active = 1
            AND ppc.is_active = 1
            AND pc.is_active = 1
            AND ppc.effective_from <= ?
            AND (ppc.effective_to IS NULL OR ppc.effective_to >= ?)
            ORDER BY pc.order_index
        """, (employee_id, effective_date, effective_date)).fetchall()
        return [dict(row) for row in rows]
    finally:
        db.close()


def calculate_employee_net_salary(employee_id: int, period_id: int) -> Dict:
    """Calculate net salary for an employee for a given period."""
    db = get_db()
    try:
        # Get employee profile
        profile = get_employee_payroll_profile(employee_id)
        if not profile:
            return {'error': 'No payroll profile found'}
        
        # Get components
        components = get_employee_components(employee_id)
        
        # Get attendance/leave impacts
        attendance = db.execute("""
            SELECT COALESCE(SUM(work_hours), 0) as work_hours,
                   COALESCE(SUM(overtime_hours), 0) as overtime_hours,
                   COUNT(CASE WHEN status = 'Absent' THEN 1 END) as absent_days
            FROM payroll_attendance_inputs
            WHERE period_id = ? AND employee_id = ?
        """, (period_id, employee_id)).fetchone()
        
        # Calculate basic (could be pro-rated based on attendance)
        basic = next((c['amount'] for c in components if c['code'] == 'BASIC'), 0)
        total_earnings = sum(c['amount'] for c in components if c['component_type'] == 'Earning')
        total_deductions = sum(c['amount'] for c in components if c['component_type'] == 'Deduction')
        
        gross = total_earnings
        net = gross - total_deductions
        
        return {
            'employee_id': employee_id,
            'basic_salary': basic,
            'total_earnings': total_earnings,
            'total_deductions': total_deductions,
            'gross_salary': gross,
            'net_salary': net,
            'components': components,
            'attendance_hours': dict(attendance) if attendance else None
        }
    finally:
        db.close()


def get_payroll_summary_stats(period_id: int) -> Dict:
    """Get payroll summary statistics for a period."""
    db = get_db()
    try:
        stats = db.execute("""
            SELECT 
                COUNT(*) as total_employees,
                SUM(total_earnings) as total_earnings,
                SUM(total_deductions) as total_deductions,
                SUM(gross_salary) as total_gross,
                SUM(net_salary) as total_net,
                SUM(total_tax) as total_tax,
                SUM(total_overtime) as total_overtime,
                SUM(total_loan_deductions) as total_loans,
                SUM(has_exceptions) as employees_with_exceptions
            FROM payroll_employee_records
            WHERE period_id = ?
        """, (period_id,)).fetchone()
        
        return dict(stats) if stats else {}
    finally:
        db.close()


def get_pending_payroll_approvals(user_id: int = None) -> List[Dict]:
    """Get pending payroll approvals."""
    db = get_db()
    try:
        query = """
            SELECT pai.*, 
                   pp.name as period_name,
                   pp.month, pp.year,
                   u1.full_name as requested_by_name,
                   u2.full_name as approver_name
            FROM payroll_approval_instances pai
            LEFT JOIN payroll_periods pp ON pai.period_id = pp.id
            LEFT JOIN users u1 ON pai.requested_by_id = u1.id
            LEFT JOIN users u2 ON pai.approver_id = u2.id
            WHERE pai.status = 'Pending'
        """
        params = []
        
        if user_id:
            query += " AND (pai.approver_id = ? OR pai.approver_id IS NULL)"
            params.append(user_id)
        
        query += " ORDER BY pai.priority DESC, pai.created_at"
        
        rows = db.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        db.close()


def log_payroll_audit(
    action: str,
    entity_type: str,
    entity_id: int,
    user_id: int,
    period_id: int = None,
    run_id: int = None,
    employee_id: int = None,
    field_name: str = None,
    old_value: str = None,
    new_value: str = None,
    change_details: str = None,
    approval_instance_id: int = None
) -> bool:
    """Log a payroll audit entry."""
    db = get_db()
    try:
        db.execute("""
            INSERT INTO payroll_audit_log (
                action, entity_type, entity_id, user_id, period_id, run_id, employee_id,
                field_name, old_value, new_value, change_details, approval_instance_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            action, entity_type, entity_id, user_id, period_id, run_id, employee_id,
            field_name, old_value, new_value, change_details, approval_instance_id
        ))
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()


def create_payslip_number() -> str:
    """Generate a unique payslip number."""
    db = get_db()
    try:
        year = datetime.now().year
        prefix = f"PS{year}"
        
        row = db.execute("""
            SELECT payslip_number FROM payroll_payslips 
            WHERE payslip_number LIKE ? 
            ORDER BY payslip_number DESC LIMIT 1
        """, (f'{prefix}%',)).fetchone()
        
        if row:
            last_num = int(row['payslip_number'][len(prefix):])
            next_num = last_num + 1
        else:
            next_num = 1
        
        return f"{prefix}{next_num:06d}"
    finally:
        db.close()


def create_loan_number() -> str:
    """Generate a unique loan number."""
    db = get_db()
    try:
        year = datetime.now().year
        prefix = f"LN{year}"
        
        row = db.execute("""
            SELECT loan_number FROM payroll_loans 
            WHERE loan_number LIKE ? 
            ORDER BY loan_number DESC LIMIT 1
        """, (f'{prefix}%',)).fetchone()
        
        if row:
            last_num = int(row['loan_number'][len(prefix):])
            next_num = last_num + 1
        else:
            next_num = 1
        
        return f"{prefix}{next_num:06d}"
    finally:
        db.close()


def create_advance_number() -> str:
    """Generate a unique advance number."""
    db = get_db()
    try:
        year = datetime.now().year
        prefix = f"ADV{year}"
        
        row = db.execute("""
            SELECT advance_number FROM payroll_advances 
            WHERE advance_number LIKE ? 
            ORDER BY advance_number DESC LIMIT 1
        """, (f'{prefix}%',)).fetchone()
        
        if row:
            last_num = int(row['advance_number'][len(prefix):])
            next_num = last_num + 1
        else:
            next_num = 1
        
        return f"{prefix}{next_num:06d}"
    finally:
        db.close()


def create_retro_number() -> str:
    """Generate a unique retro adjustment number."""
    db = get_db()
    try:
        year = datetime.now().year
        prefix = f"RETRO{year}"
        
        row = db.execute("""
            SELECT retro_number FROM payroll_retro_adjustments 
            WHERE retro_number LIKE ? 
            ORDER BY retro_number DESC LIMIT 1
        """, (f'{prefix}%',)).fetchone()
        
        if row:
            last_num = int(row['retro_number'][len(prefix):])
            next_num = last_num + 1
        else:
            next_num = 1
        
        return f"{prefix}{next_num:06d}"
    finally:
        db.close()


def create_arrears_number() -> str:
    """Generate a unique arrears number."""
    db = get_db()
    try:
        year = datetime.now().year
        prefix = f"ARR{year}"
        
        row = db.execute("""
            SELECT arrears_number FROM payroll_arrears 
            WHERE arrears_number LIKE ? 
            ORDER BY arrears_number DESC LIMIT 1
        """, (f'{prefix}%',)).fetchone()
        
        if row:
            last_num = int(row['arrears_number'][len(prefix):])
            next_num = last_num + 1
        else:
            next_num = 1
        
        return f"{prefix}{next_num:06d}"
    finally:
        db.close()


def create_posting_number() -> str:
    """Generate a unique finance posting number."""
    db = get_db()
    try:
        year = datetime.now().year
        prefix = f"PP{year}"
        
        row = db.execute("""
            SELECT posting_number FROM payroll_finance_postings 
            WHERE posting_number LIKE ? 
            ORDER BY posting_number DESC LIMIT 1
        """, (f'{prefix}%',)).fetchone()
        
        if row:
            last_num = int(row['posting_number'][len(prefix):])
            next_num = last_num + 1
        else:
            next_num = 1
        
        return f"{prefix}{next_num:06d}"
    finally:
        db.close()


def create_letter_number(letter_type: str) -> str:
    """Generate a unique letter number."""
    db = get_db()
    try:
        year = datetime.now().year
        type_code = letter_type[:3].upper()
        prefix = f"{type_code}{year}"
        
        row = db.execute("""
            SELECT letter_number FROM payroll_letters 
            WHERE letter_number LIKE ? 
            ORDER BY letter_number DESC LIMIT 1
        """, (f'{prefix}%',)).fetchone()
        
        if row:
            last_num = int(row['letter_number'][len(prefix):])
            next_num = last_num + 1
        else:
            next_num = 1
        
        return f"{prefix}{next_num:06d}"
    finally:
        db.close()


def get_payroll_exceptions(period_id: int, status: str = None, severity: str = None) -> List[Dict]:
    """Get payroll exceptions for a period."""
    db = get_db()
    try:
        query = """
            SELECT pe.*, 
                   e.first_name || ' ' || e.last_name as employee_name,
                   e.employee_code
            FROM payroll_exceptions pe
            LEFT JOIN hr_employees e ON pe.employee_id = e.id
            WHERE pe.period_id = ?
        """
        params = [period_id]
        
        if status:
            query += " AND pe.status = ?"
            params.append(status)
        
        if severity:
            query += " AND pe.severity = ?"
            params.append(severity)
        
        query += " ORDER BY pe.severity DESC, pe.created_at DESC"
        
        rows = db.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        db.close()


def get_loan_installment_due(loan_id: int, period_id: int) -> Optional[Dict]:
    """Get the installment due for a loan in a specific period."""
    db = get_db()
    try:
        row = db.execute("""
            SELECT * FROM payroll_loan_installments
            WHERE loan_id = ? AND period_id = ? AND status = 'Pending'
        """, (loan_id, period_id)).fetchone()
        return dict(row) if row else None
    finally:
        db.close()


def get_outstanding_loans(employee_id: int) -> List[Dict]:
    """Get all outstanding loans for an employee."""
    db = get_db()
    try:
        rows = db.execute("""
            SELECT * FROM payroll_loans
            WHERE employee_id = ? AND status = 'Active' AND amount_remaining > 0
            ORDER BY start_date DESC
        """, (employee_id,)).fetchall()
        return [dict(row) for row in rows]
    finally:
        db.close()


def get_active_advances(employee_id: int) -> List[Dict]:
    """Get all active advances for an employee."""
    db = get_db()
    try:
        rows = db.execute("""
            SELECT * FROM payroll_advances
            WHERE employee_id = ? AND status IN ('Approved', 'In Recovery') AND fully_recovered = 0
            ORDER BY created_at DESC
        """, (employee_id,)).fetchall()
        return [dict(row) for row in rows]
    finally:
        db.close()


def run_payroll_validations(run_id: int) -> Tuple[bool, List[Dict]]:
    """Run pre-payroll validations and return results."""
    db = get_db()
    try:
        run = db.execute("SELECT * FROM payroll_runs WHERE id = ?", (run_id,)).fetchone()
        if not run:
            return False, [{'error': 'Run not found'}]
        
        errors = []
        
        # Validation 1: Check period is open
        period = db.execute("SELECT * FROM payroll_periods WHERE id = ?", (run['period_id'],)).fetchone()
        if period and period['status'] not in ('Open', 'Processing'):
            errors.append({
                'type': 'Period Status',
                'message': f"Period is {period['status']}, must be Open or Processing"
            })
        
        # Validation 2: Check employees have payroll profiles
        employees_without_profile = db.execute("""
            SELECT COUNT(*) as cnt FROM hr_employees e
            WHERE e.status = 'Active'
            AND NOT EXISTS (SELECT 1 FROM payroll_profiles pp WHERE pp.employee_id = e.id AND pp.is_active = 1)
        """).fetchone()['cnt']
        
        if employees_without_profile > 0:
            errors.append({
                'type': 'Missing Profile',
                'message': f"{employees_without_profile} active employees do not have payroll profiles"
            })
        
        # Validation 3: Check for existing runs in same period
        existing_runs = db.execute("""
            SELECT COUNT(*) as cnt FROM payroll_runs 
            WHERE period_id = ? AND id != ? AND status NOT IN ('Cancelled', 'Failed')
        """, (run['period_id'], run_id)).fetchone()['cnt']
        
        if existing_runs > 0:
            errors.append({
                'type': 'Duplicate Run',
                'message': f"{existing_runs} other run(s) exist for this period"
            })
        
        # Log validation results
        for error in errors:
            db.execute("""
                INSERT INTO payroll_run_validations (run_id, validation_type, validation_rule, status, error_message)
                VALUES (?, ?, ?, ?, ?)
            """, (run_id, 'Pre-Run', 'System', 'Failed' if errors else 'Pass', error['message']))
        
        db.commit()
        return len(errors) == 0, errors
    finally:
        db.close()


# =============================================================================
# INITIALIZATION
# =============================================================================

if __name__ == '__main__':
    print("Running payroll migrations...")
    run_payroll_migrations()
    print("Seeding payroll default data...")
    seed_payroll_default_data()
    print("Payroll module initialization complete.")
