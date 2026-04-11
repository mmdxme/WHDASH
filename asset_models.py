"""
Asset Management Module Database Models
=======================================
Enterprise-grade Asset Management for the MMDx platform.

This module provides comprehensive fixed asset tracking including:
- Asset Master Data
- Asset Categories and Classifications
- Depreciation Methods and Calculations
- Depreciation Schedules and Runs
- Asset Maintenance Planning (Preventive/Corrective)
- Maintenance Work Orders and Logs
- Asset Transfers and Relocations
- Asset Disposal/Retirement workflows
- Asset Assignment to Departments/Employees/Custodians
- Asset Audit Trail

Tables:
- asset_categories: Asset classification hierarchy
- assets: Central asset master record
- asset_acquisitions: Acquisition/capitalization records
- asset_assignments: Current assignment to dept/custodian
- asset_transfer_history: Location/custodian change history
- depreciation_methods: Available depreciation calculation methods
- asset_depreciation_profiles: Per-asset depreciation configuration
- depreciation_runs: Batch depreciation run headers
- depreciation_entries: Individual asset depreciation entries
- maintenance_types: Types of maintenance (preventive/corrective)
- maintenance_schedules: Preventive maintenance schedules
- maintenance_work_orders: Maintenance work orders
- maintenance_work_logs: Completed maintenance records
- maintenance_cost_entries: Maintenance cost tracking
- disposal_requests: Disposal request headers
- asset_disposals: Completed disposal records
- asset_settings: Configuration settings
- asset_audit_log: Audit trail for all asset changes
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'warehouse.db'))


def get_db():
    """Get database connection with Row factory for dict-like access."""
    conn = sqlite3.connect(DATABASE, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


# =============================================================================
# ASSET MANAGEMENT TABLE DEFINITIONS
# =============================================================================

ASSET_TABLES = [
    # -------------------------------------------------------------------------
    # 1. Asset Categories - Asset Classification Hierarchy
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS asset_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        parent_id INTEGER,
        description TEXT,
        depreciation_method_id INTEGER,
        default_useful_life_years INTEGER DEFAULT 5,
        default_salvage_percent REAL DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_id) REFERENCES asset_categories(id) ON DELETE SET NULL,
        FOREIGN KEY (depreciation_method_id) REFERENCES depreciation_methods(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 2. Depreciation Methods - Calculation Methods
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS depreciation_methods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        description TEXT,
        formula TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 3. Assets - Central Asset Master Record
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        category_id INTEGER,
        asset_type TEXT DEFAULT 'Tangible',
        serial_number TEXT,
        brand TEXT,
        model TEXT,
        manufacturer TEXT,
        tag_number TEXT,

        -- Acquisition Information
        acquisition_date DATE,
        capitalization_date DATE,
        in_service_date DATE,
        acquisition_cost DECIMAL(15,2) DEFAULT 0,
        additional_capitalization DECIMAL(15,2) DEFAULT 0,
        total_cost DECIMAL(15,2) GENERATED ALWAYS AS (acquisition_cost + additional_capitalization) STORED,

        -- Supplier/Procurement Reference
        supplier_id INTEGER,
        purchase_order_number TEXT,
        invoice_number TEXT,
        warranty_expiry_date DATE,

        -- Depreciation Configuration
        depreciation_method_id INTEGER,
        useful_life_years INTEGER,
        salvage_value DECIMAL(15,2) DEFAULT 0,
        salvage_percent REAL DEFAULT 0,
        depreciation_start_date DATE,

        -- Organization Structure
        company_id INTEGER,
        branch_id INTEGER,
        warehouse_id INTEGER,
        location TEXT,
        department_id INTEGER,
        cost_center TEXT,
        custodian_id INTEGER,

        -- Status and Condition
        status TEXT DEFAULT 'Draft',
        condition_rating TEXT DEFAULT 'Good',
        asset_condition TEXT DEFAULT 'Good',

        -- Depreciation Tracking
        accumulated_depreciation DECIMAL(15,2) DEFAULT 0,
        net_book_value DECIMAL(15,2) DEFAULT 0,
        last_depreciation_date DATE,
        depreciation_status TEXT DEFAULT 'Not Started',

        -- Quantity/Unit
        quantity INTEGER DEFAULT 1,
        unit_of_measure TEXT DEFAULT 'Unit',

        -- Files/Attachments
        notes TEXT,
        attachment_urls TEXT,

        -- Audit Fields
        created_by INTEGER,
        approved_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES asset_categories(id) ON DELETE SET NULL,
        FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL,
        FOREIGN KEY (department_id) REFERENCES hr_departments(id) ON DELETE SET NULL,
        FOREIGN KEY (custodian_id) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 4. Asset Acquisitions - Capitalization Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS asset_acquisitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER NOT NULL,
        acquisition_type TEXT DEFAULT 'Purchase',
        acquisition_date DATE NOT NULL,
        capitalization_date DATE,
        supplier_id INTEGER,
        purchase_order_id INTEGER,
        invoice_number TEXT,
        invoice_date DATE,
        invoice_amount DECIMAL(15,2) DEFAULT 0,
        currency TEXT DEFAULT 'AED',
        exchange_rate DECIMAL(10,4) DEFAULT 1.0,
        local_amount DECIMAL(15,2) DEFAULT 0,
        additional_costs DECIMAL(15,2) DEFAULT 0,
        total_capitalized_cost DECIMAL(15,2) DEFAULT 0,
        payment_terms TEXT,
        payment_status TEXT DEFAULT 'Pending',
        approval_status TEXT DEFAULT 'Pending',
        approved_by INTEGER,
        approved_at DATETIME,
        notes TEXT,
        attachment_urls TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
        FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 5. Asset Assignments - Current Assignment Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS asset_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER NOT NULL,
        assignment_type TEXT NOT NULL,
        assigned_to_type TEXT DEFAULT 'Employee',
        assigned_to_id INTEGER,
        department_id INTEGER,
        cost_center TEXT,
        location TEXT,
        effective_date DATE NOT NULL,
        return_date DATE,
        status TEXT DEFAULT 'Active',
        condition_at_assignment TEXT,
        notes TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
        FOREIGN KEY (assigned_to_id) REFERENCES hr_employees(id) ON DELETE SET NULL,
        FOREIGN KEY (department_id) REFERENCES hr_departments(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 6. Asset Transfer History - Movement/Transfer Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS asset_transfer_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER NOT NULL,
        transfer_type TEXT NOT NULL,
        from_company_id INTEGER,
        from_branch_id INTEGER,
        from_warehouse_id INTEGER,
        from_location TEXT,
        from_department_id INTEGER,
        from_custodian_id INTEGER,
        to_company_id INTEGER,
        to_branch_id INTEGER,
        to_warehouse_id INTEGER,
        to_location TEXT,
        to_department_id INTEGER,
        to_custodian_id INTEGER,
        transfer_date DATE NOT NULL,
        reason TEXT,
        approved_by INTEGER,
        notes TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
        FOREIGN KEY (from_department_id) REFERENCES hr_departments(id) ON DELETE SET NULL,
        FOREIGN KEY (to_department_id) REFERENCES hr_departments(id) ON DELETE SET NULL,
        FOREIGN KEY (from_custodian_id) REFERENCES hr_employees(id) ON DELETE SET NULL,
        FOREIGN KEY (to_custodian_id) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 7. Asset Depreciation Profiles - Per-Asset Depreciation Config
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS asset_depreciation_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER NOT NULL UNIQUE,
        depreciation_method_id INTEGER NOT NULL,
        acquisition_cost DECIMAL(15,2) NOT NULL,
        salvage_value DECIMAL(15,2) DEFAULT 0,
        depreciable_amount DECIMAL(15,2) GENERATED ALWAYS AS (acquisition_cost - salvage_value) STORED,
        useful_life_months INTEGER NOT NULL,
        useful_life_years INTEGER NOT NULL,
        monthly_depreciation DECIMAL(15,2) DEFAULT 0,
        accumulated_depreciation DECIMAL(15,2) DEFAULT 0,
        net_book_value DECIMAL(15,2) DEFAULT 0,
        depreciation_start_date DATE NOT NULL,
        last_depreciation_date DATE,
        next_depreciation_date DATE,
        is_active INTEGER DEFAULT 1,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
        FOREIGN KEY (depreciation_method_id) REFERENCES depreciation_methods(id) ON DELETE RESTRICT
    )""",

    # -------------------------------------------------------------------------
    # 8. Depreciation Runs - Batch Run Headers
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS depreciation_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_number TEXT UNIQUE NOT NULL,
        run_date DATE NOT NULL,
        period_month INTEGER NOT NULL,
        period_year INTEGER NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'Draft',
        total_assets INTEGER DEFAULT 0,
        total_depreciation DECIMAL(15,2) DEFAULT 0,
        total_accumulated DECIMAL(15,2) DEFAULT 0,
        total_net_book_value DECIMAL(15,2) DEFAULT 0,
        processed_by INTEGER,
        approved_by INTEGER,
        approved_at DATETIME,
        posted_at DATETIME,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (processed_by) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 9. Depreciation Entries - Per-Asset Depreciation Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS depreciation_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER NOT NULL,
        asset_id INTEGER NOT NULL,
        asset_code TEXT NOT NULL,
        asset_name TEXT NOT NULL,
        period_month INTEGER NOT NULL,
        period_year INTEGER NOT NULL,
        depreciation_amount DECIMAL(15,2) NOT NULL,
        accumulated_depreciation DECIMAL(15,2) NOT NULL,
        net_book_value DECIMAL(15,2) NOT NULL,
        is_reversal INTEGER DEFAULT 0,
        reversed_entry_id INTEGER,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (run_id) REFERENCES depreciation_runs(id) ON DELETE CASCADE,
        FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 10. Maintenance Types - Types of Maintenance
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        category TEXT DEFAULT 'Preventive',
        description TEXT,
        default_priority TEXT DEFAULT 'Medium',
        estimated_duration_hours DECIMAL(6,2) DEFAULT 0,
        estimated_cost DECIMAL(12,2) DEFAULT 0,
        requires_downtime INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 11. Maintenance Schedules - Preventive Maintenance Schedules
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER NOT NULL,
        maintenance_type_id INTEGER NOT NULL,
        schedule_name TEXT,
        frequency TEXT DEFAULT 'Monthly',
        interval_days INTEGER DEFAULT 30,
        next_due_date DATE NOT NULL,
        last_performed_date DATE,
        last_work_order_id INTEGER,
        is_active INTEGER DEFAULT 1,
        is_recurring INTEGER DEFAULT 1,
        priority TEXT DEFAULT 'Medium',
        assigned_technician_id INTEGER,
        estimated_duration_hours DECIMAL(6,2) DEFAULT 0,
        estimated_cost DECIMAL(12,2) DEFAULT 0,
        notes TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
        FOREIGN KEY (maintenance_type_id) REFERENCES maintenance_types(id) ON DELETE RESTRICT,
        FOREIGN KEY (assigned_technician_id) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 12. Maintenance Work Orders - Work Order Headers
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_work_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_order_number TEXT UNIQUE NOT NULL,
        asset_id INTEGER NOT NULL,
        schedule_id INTEGER,
        maintenance_type_id INTEGER NOT NULL,
        work_order_type TEXT DEFAULT 'Corrective',
        priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'Open',
        issue_date DATE NOT NULL,
        issue_description TEXT,
        assigned_technician_id INTEGER,
        assigned_vendor_id INTEGER,
        scheduled_start_date DATE,
        scheduled_end_date DATE,
        actual_start_date DATE,
        actual_end_date DATE,
        downtime_hours DECIMAL(6,2) DEFAULT 0,
        estimated_cost DECIMAL(12,2) DEFAULT 0,
        actual_cost DECIMAL(12,2) DEFAULT 0,
        resolution_notes TEXT,
        completed_by INTEGER,
        completed_at DATETIME,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
        FOREIGN KEY (schedule_id) REFERENCES maintenance_schedules(id) ON DELETE SET NULL,
        FOREIGN KEY (maintenance_type_id) REFERENCES maintenance_types(id) ON DELETE RESTRICT,
        FOREIGN KEY (assigned_technician_id) REFERENCES hr_employees(id) ON DELETE SET NULL,
        FOREIGN KEY (assigned_vendor_id) REFERENCES suppliers(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 13. Maintenance Work Logs - Completed Maintenance Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_work_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_order_id INTEGER,
        asset_id INTEGER NOT NULL,
        maintenance_type_id INTEGER NOT NULL,
        work_date DATE NOT NULL,
        technician_id INTEGER,
        vendor_id INTEGER,
        work_performed TEXT,
        action_taken TEXT,
        parts_used TEXT,
        labor_hours DECIMAL(6,2) DEFAULT 0,
        labor_cost DECIMAL(12,2) DEFAULT 0,
        parts_cost DECIMAL(12,2) DEFAULT 0,
        total_cost DECIMAL(12,2) DEFAULT 0,
        downtime_hours DECIMAL(6,2) DEFAULT 0,
        condition_after TEXT,
        next_recommendation TEXT,
        follow_up_required INTEGER DEFAULT 0,
        follow_up_date DATE,
        is_billable INTEGER DEFAULT 0,
        invoice_number TEXT,
        attachment_urls TEXT,
        notes TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (work_order_id) REFERENCES maintenance_work_orders(id) ON DELETE SET NULL,
        FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
        FOREIGN KEY (maintenance_type_id) REFERENCES maintenance_types(id) ON DELETE RESTRICT,
        FOREIGN KEY (technician_id) REFERENCES hr_employees(id) ON DELETE SET NULL,
        FOREIGN KEY (vendor_id) REFERENCES suppliers(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 14. Maintenance Cost Entries - Cost Tracking
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_cost_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER NOT NULL,
        work_order_id INTEGER,
        work_log_id INTEGER,
        cost_type TEXT NOT NULL,
        cost_date DATE NOT NULL,
        description TEXT,
        amount DECIMAL(12,2) NOT NULL,
        currency TEXT DEFAULT 'AED',
        vendor_id INTEGER,
        invoice_number TEXT,
        attachment_urls TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
        FOREIGN KEY (work_order_id) REFERENCES maintenance_work_orders(id) ON DELETE SET NULL,
        FOREIGN KEY (work_log_id) REFERENCES maintenance_work_logs(id) ON DELETE SET NULL,
        FOREIGN KEY (vendor_id) REFERENCES suppliers(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 15. Disposal Requests - Disposal Request Headers
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS disposal_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_number TEXT UNIQUE NOT NULL,
        asset_id INTEGER NOT NULL,
        request_date DATE NOT NULL,
        disposal_type TEXT NOT NULL,
        reason_code TEXT,
        reason_description TEXT,
        estimated_proceeds DECIMAL(12,2) DEFAULT 0,
        net_book_value DECIMAL(15,2) DEFAULT 0,
        gain_loss DECIMAL(15,2) DEFAULT 0,
        status TEXT DEFAULT 'Pending Approval',
        approved_by INTEGER,
        approved_at DATETIME,
        rejection_reason TEXT,
        notes TEXT,
        attachment_urls TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE RESTRICT,
        FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 16. Asset Disposals - Completed Disposal Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS asset_disposals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        disposal_number TEXT UNIQUE NOT NULL,
        request_id INTEGER,
        asset_id INTEGER NOT NULL,
        disposal_date DATE NOT NULL,
        disposal_type TEXT NOT NULL,
        reason_code TEXT,
        proceeds DECIMAL(15,2) DEFAULT 0,
        cost_of_disposal DECIMAL(15,2) DEFAULT 0,
        net_proceeds DECIMAL(15,2) DEFAULT 0,
        gain_loss DECIMAL(15,2) DEFAULT 0,
        buyer_name TEXT,
        buyer_contact TEXT,
        payment_received INTEGER DEFAULT 0,
        payment_date DATE,
        approval_status TEXT DEFAULT 'Approved',
        approved_by INTEGER,
        approved_at DATETIME,
        notes TEXT,
        attachment_urls TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (request_id) REFERENCES disposal_requests(id) ON DELETE SET NULL,
        FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE RESTRICT,
        FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 17. Asset Settings - Configuration Settings
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS asset_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_key TEXT UNIQUE NOT NULL,
        setting_value TEXT,
        category TEXT DEFAULT 'General',
        description TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 18. Asset Audit Log - Comprehensive Audit Trail
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS asset_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,
        entity_id INTEGER NOT NULL,
        asset_id INTEGER,
        action TEXT NOT NULL,
        field_name TEXT,
        old_value TEXT,
        new_value TEXT,
        user_id INTEGER,
        ip_address TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",
]


# =============================================================================
# INDEXES FOR PERFORMANCE
# =============================================================================

ASSET_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_assets_code ON assets(asset_code)",
    "CREATE INDEX IF NOT EXISTS idx_assets_status ON assets(status)",
    "CREATE INDEX IF NOT EXISTS idx_assets_category ON assets(category_id)",
    "CREATE INDEX IF NOT EXISTS idx_assets_company ON assets(company_id)",
    "CREATE INDEX IF NOT EXISTS idx_assets_department ON assets(department_id)",
    "CREATE INDEX IF NOT EXISTS idx_assets_custodian ON assets(custodian_id)",
    "CREATE INDEX IF NOT EXISTS idx_assets_acquisition_date ON assets(acquisition_date)",
    "CREATE INDEX IF NOT EXISTS idx_depreciation_runs_period ON depreciation_runs(period_year, period_month)",
    "CREATE INDEX IF NOT EXISTS idx_depreciation_entries_run ON depreciation_entries(run_id)",
    "CREATE INDEX IF NOT EXISTS idx_depreciation_entries_asset ON depreciation_entries(asset_id)",
    "CREATE INDEX IF NOT EXISTS idx_maintenance_schedules_asset ON maintenance_schedules(asset_id)",
    "CREATE INDEX IF NOT EXISTS idx_maintenance_schedules_due ON maintenance_schedules(next_due_date)",
    "CREATE INDEX IF NOT EXISTS idx_maintenance_work_orders_asset ON maintenance_work_orders(asset_id)",
    "CREATE INDEX IF NOT EXISTS idx_maintenance_work_orders_status ON maintenance_work_orders(status)",
    "CREATE INDEX IF NOT EXISTS idx_maintenance_work_logs_asset ON maintenance_work_logs(asset_id)",
    "CREATE INDEX IF NOT EXISTS idx_asset_disposals_asset ON asset_disposals(asset_id)",
    "CREATE INDEX IF NOT EXISTS idx_asset_transfer_history_asset ON asset_transfer_history(asset_id)",
    "CREATE INDEX IF NOT EXISTS idx_asset_audit_asset ON asset_audit_log(asset_id)",
    "CREATE INDEX IF NOT EXISTS idx_asset_audit_entity ON asset_audit_log(entity_type, entity_id)",
]


# =============================================================================
# INITIALIZATION FUNCTION
# =============================================================================

def init_asset_tables():
    """
    Initialize all asset management tables.
    Called during app startup to ensure tables exist.
    """
    conn = get_db()
    try:
        cursor = conn.cursor()

        # Create tables
        for table_sql in ASSET_TABLES:
            cursor.execute(table_sql)

        # Create indexes
        for index_sql in ASSET_INDEXES:
            cursor.execute(index_sql)

        conn.commit()

        # Seed default data
        _seed_default_data(conn)

    finally:
        conn.close()


def _seed_default_data(conn):
    """Seed default reference data for asset management."""

    # Seed depreciation methods
    depreciation_methods = [
        ('Straight-Line', 'STRAIGHT_LINE', 'Equal depreciation over useful life', '(Cost - Salvage) / Useful Life'),
        ('Declining Balance', 'DECLINING_BALANCE', 'Accelerated depreciation - higher in early years', 'Book Value x Rate'),
        ('Double Declining Balance', 'DOUBLE_DECLINING', '2x the straight-line rate', '2 x Straight-Line Rate x Book Value'),
        ('Sum-of-Years Digits', 'SUM_OF_YEARS', 'Accelerated - declining fraction', '(Remaining Life / Sum of Years) x Depreciable Amount'),
        ('Units of Production', 'UNITS_OF_PRODUCTION', 'Based on usage/units produced', '(Units Produced / Total Units) x Depreciable Amount'),
    ]

    cursor = conn.cursor()

    # Check if methods already exist
    cursor.execute("SELECT COUNT(*) as cnt FROM depreciation_methods")
    if cursor.fetchone()['cnt'] == 0:
        for name, code, description, formula in depreciation_methods:
            cursor.execute("""
                INSERT INTO depreciation_methods (name, code, description, formula, is_active)
                VALUES (?, ?, ?, ?, 1)
            """, (name, code, description, formula))

    # Seed asset categories
    cursor.execute("SELECT COUNT(*) as cnt FROM asset_categories")
    if cursor.fetchone()['cnt'] == 0:
        # Get straight-line method ID
        cursor.execute("SELECT id FROM depreciation_methods WHERE code = 'STRAIGHT_LINE' LIMIT 1")
        sl_method = cursor.fetchone()
        sl_method_id = sl_method['id'] if sl_method else 1

        categories = [
            ('IT Equipment', 'IT-EQUIP', None, sl_method_id, 3, 0),
            ('Office Furniture', 'OFF-FURN', None, sl_method_id, 10, 0),
            ('Office Equipment', 'OFF-EQUIP', None, sl_method_id, 5, 0),
            ('Vehicles', 'VEHICLES', None, sl_method_id, 5, 10),
            ('Machinery', 'MACHINERY', None, sl_method_id, 10, 5),
            ('Warehouse Equipment', 'WH-EQUIP', None, sl_method_id, 7, 0),
            ('Communication Devices', 'COMM-DEV', None, sl_method_id, 5, 0),
            ('Leasehold Improvements', 'LEASEHOLD', None, sl_method_id, 10, 0),
            ('Tools', 'TOOLS', None, sl_method_id, 5, 0),
            ('Other Assets', 'OTHER', None, sl_method_id, 5, 0),
        ]

        for name, code, parent_id, method_id, life, salvage in categories:
            cursor.execute("""
                INSERT INTO asset_categories (name, code, parent_id, depreciation_method_id, default_useful_life_years, default_salvage_percent, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (name, code, parent_id, method_id, life, salvage))

    # Seed maintenance types
    cursor.execute("SELECT COUNT(*) as cnt FROM maintenance_types")
    if cursor.fetchone()['cnt'] == 0:
        maintenance_types = [
            ('Preventive Maintenance', 'PREV-MAINT', 'Preventive', 'Scheduled routine maintenance', 'Medium', 2, 0, 1),
            ('Corrective Maintenance', 'CORR-MAINT', 'Corrective', 'Repair after breakdown', 'High', 4, 500, 1),
            ('Inspection', 'INSPECTION', 'Preventive', 'Regular inspection and testing', 'Low', 1, 0, 0),
            ('Calibration', 'CALIBRATION', 'Preventive', 'Equipment calibration', 'Medium', 2, 100, 1),
            ('Replacement', 'REPLACEMENT', 'Corrective', 'Parts replacement', 'High', 3, 300, 0),
            ('Overhaul', 'OVERHAUL', 'Preventive', 'Complete system overhaul', 'Low', 8, 1000, 1),
            ('Emergency Repair', 'EMERGENCY', 'Corrective', 'Urgent repair work', 'Critical', 4, 800, 1),
            ('Software Update', 'SW-UPDATE', 'Preventive', 'Software/firmware updates', 'Low', 1, 0, 0),
        ]

        for name, code, category, desc, priority, duration, cost, downtime in maintenance_types:
            cursor.execute("""
                INSERT INTO maintenance_types (name, code, category, description, default_priority, estimated_duration_hours, estimated_cost, requires_downtime, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (name, code, category, desc, priority, duration, cost, downtime))

    # Seed asset settings
    cursor.execute("SELECT COUNT(*) as cnt FROM asset_settings")
    if cursor.fetchone()['cnt'] == 0:
        settings = [
            ('asset_code_prefix', 'AST-', 'Numbering', 'Prefix for asset codes'),
            ('asset_code_sequence', '10001', 'Numbering', 'Next asset code sequence number'),
            ('default_depreciation_method', 'STRAIGHT_LINE', 'Depreciation', 'Default depreciation method for new assets'),
            ('default_useful_life_years', '5', 'Depreciation', 'Default useful life in years'),
            ('default_salvage_percent', '0', 'Depreciation', 'Default salvage value percentage'),
            ('auto_capitalize_threshold', '5000', 'Capitalization', 'Minimum cost to capitalize (AED)'),
            ('enable_depreciation_lock', '1', 'Depreciation', 'Lock depreciation after period close'),
            ('require_approval_capitalization', '1', 'Approval', 'Require approval for asset capitalization'),
            ('require_approval_disposal', '1', 'Approval', 'Require approval for asset disposal'),
            ('require_approval_transfer', '0', 'Approval', 'Require approval for asset transfers'),
            ('maintenance_reminder_days', '7', 'Maintenance', 'Days before due to send reminder'),
            ('enable_maintenance_alerts', '1', 'Maintenance', 'Enable maintenance due alerts'),
            ('default_work_order_prefix', 'WO-', 'Numbering', 'Prefix for work order numbers'),
            ('default_disposal_prefix', 'DSP-', 'Numbering', 'Prefix for disposal numbers'),
        ]

        for key, value, category, desc in settings:
            cursor.execute("""
                INSERT INTO asset_settings (setting_key, setting_value, category, description, is_active)
                VALUES (?, ?, ?, ?, 1)
            """, (key, value, category, desc))

    conn.commit()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_asset_setting(key: str, default: str = None) -> str:
    """Get an asset configuration setting value."""
    conn = get_db()
    try:
        result = conn.execute(
            "SELECT setting_value FROM asset_settings WHERE setting_key = ? AND is_active = 1",
            (key,)
        ).fetchone()
        return result['setting_value'] if result else default
    finally:
        conn.close()


def set_asset_setting(key: str, value: str, category: str = 'General'):
    """Set an asset configuration setting value."""
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM asset_settings WHERE setting_key = ?",
            (key,)
        ).fetchone()

        if existing:
            conn.execute(
                "UPDATE asset_settings SET setting_value = ?, updated_at = CURRENT_TIMESTAMP WHERE setting_key = ?",
                (value, key)
            )
        else:
            conn.execute(
                "INSERT INTO asset_settings (setting_key, setting_value, category) VALUES (?, ?, ?)",
                (key, value, category)
            )
        conn.commit()
    finally:
        conn.close()


def get_next_asset_code() -> str:
    """Generate the next asset code based on settings."""
    prefix = get_asset_setting('asset_code_prefix', 'AST-')
    seq_str = get_asset_setting('asset_code_sequence', '10001')
    seq = int(seq_str)

    # Increment sequence
    set_asset_setting('asset_code_sequence', str(seq + 1), 'Numbering')

    return f"{prefix}{seq}"


def get_next_work_order_number() -> str:
    """Generate the next work order number."""
    prefix = get_asset_setting('default_work_order_prefix', 'WO-')
    seq_str = get_asset_setting('work_order_sequence', '1')
    seq = int(seq_str)
    set_asset_setting('work_order_sequence', str(seq + 1), 'Numbering')
    return f"{prefix}{seq}"


def get_next_disposal_number() -> str:
    """Generate the next disposal number."""
    prefix = get_asset_setting('default_disposal_prefix', 'DSP-')
    seq_str = get_asset_setting('disposal_sequence', '1')
    seq = int(seq_str)
    set_asset_setting('disposal_sequence', str(seq + 1), 'Numbering')
    return f"{prefix}{seq}"


def get_next_depreciation_run_number() -> str:
    """Generate the next depreciation run number."""
    seq_str = get_asset_setting('depreciation_run_sequence', '1')
    seq = int(seq_str)
    set_asset_setting('depreciation_run_sequence', str(seq + 1), 'Numbering')
    today = datetime.now().strftime('%Y%m')
    return f"DEP-{today}-{seq}"


# =============================================================================
# DEPRECIATION CALCULATION ENGINE
# =============================================================================

def calculate_straight_line_monthly(acquisition_cost: float, salvage_value: float,
                                     useful_life_months: int, start_date: str,
                                     as_of_date: str = None) -> Dict:
    """
    Calculate straight-line depreciation.

    Args:
        acquisition_cost: Original acquisition cost
        salvage_value: Expected salvage/residual value
        useful_life_months: Total useful life in months
        start_date: Depreciation start date (YYYY-MM-DD)
        as_of_date: Calculate up to this date (optional)

    Returns:
        Dict with depreciation schedule and current values
    """
    depreciable_amount = acquisition_cost - salvage_value
    monthly_depreciation = depreciable_amount / useful_life_months if useful_life_months > 0 else 0

    # Calculate accumulated depreciation as of as_of_date
    if as_of_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(as_of_date, '%Y-%m-%d')
        months_elapsed = (end.year - start.year) * 12 + (end.month - start.month)
        months_elapsed = max(0, min(months_elapsed, useful_life_months))
    else:
        months_elapsed = 0

    accumulated = monthly_depreciation * months_elapsed
    current_book_value = acquisition_cost - accumulated

    return {
        'depreciable_amount': depreciable_amount,
        'monthly_depreciation': monthly_depreciation,
        'annual_depreciation': monthly_depreciation * 12,
        'accumulated_depreciation': accumulated,
        'net_book_value': current_book_value,
        'months_elapsed': months_elapsed,
        'months_remaining': useful_life_months - months_elapsed,
        'percent_depreciated': (accumulated / depreciable_amount * 100) if depreciable_amount > 0 else 0,
    }


def calculate_depreciation_for_asset(asset_id: int, period_month: int = None,
                                     period_year: int = None) -> Dict:
    """
    Calculate depreciation for a specific asset.

    Args:
        asset_id: The asset ID
        period_month: Target period month (optional - defaults to current month)
        period_year: Target period year (optional - defaults to current year)

    Returns:
        Dict with depreciation calculation results
    """
    conn = get_db()
    try:
        # Get asset details
        asset = conn.execute("""
            SELECT a.*, dm.formula as depreciation_formula
            FROM assets a
            LEFT JOIN depreciation_methods dm ON a.depreciation_method_id = dm.id
            WHERE a.id = ?
        """, (asset_id,)).fetchone()

        if not asset:
            return {'error': 'Asset not found'}

        if asset['depreciation_status'] == 'Disposed' or asset['status'] == 'Disposed':
            return {'error': 'Asset has been disposed', 'can_depreciate': False}

        if not asset['depreciation_method_id']:
            return {'error': 'No depreciation method defined', 'can_depreciate': False}

        # Get depreciation profile
        profile = conn.execute("""
            SELECT * FROM asset_depreciation_profiles WHERE asset_id = ?
        """, (asset_id,)).fetchone()

        if not profile:
            # Create profile if it doesn't exist
            if not asset['useful_life_years'] or not asset['acquisition_cost']:
                return {'error': 'Missing depreciation configuration'}

            useful_life_months = asset['useful_life_years'] * 12
            salvage = asset['salvage_value'] or (asset['acquisition_cost'] * 0.1)  # Default 10%
            start_date = asset['depreciation_start_date'] or asset['in_service_date'] or asset['capitalization_date']

            if not start_date:
                return {'error': 'No depreciation start date'}

            # Calculate initial profile
            calc = calculate_straight_line_monthly(
                asset['acquisition_cost'],
                salvage,
                useful_life_months,
                start_date
            )

            # Insert profile
            conn.execute("""
                INSERT INTO asset_depreciation_profiles
                (asset_id, depreciation_method_id, acquisition_cost, salvage_value,
                 useful_life_months, useful_life_years, monthly_depreciation,
                 accumulated_depreciation, net_book_value, depreciation_start_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                asset_id,
                asset['depreciation_method_id'],
                asset['acquisition_cost'],
                salvage,
                useful_life_months,
                asset['useful_life_years'],
                calc['monthly_depreciation'],
                0,
                asset['acquisition_cost'],
                start_date
            ))
            conn.commit()

            profile = conn.execute("""
                SELECT * FROM asset_depreciation_profiles WHERE asset_id = ?
            """, (asset_id,)).fetchone()

        # Calculate current depreciation
        if period_month is None:
            period_month = datetime.now().month
        if period_year is None:
            period_year = datetime.now().year

        # Calculate as of end of target period
        last_day = calendar.monthrange(period_year, period_month)[1]
        as_of_date = f"{period_year}-{period_month:02d}-{last_day:02d}"

        calc = calculate_straight_line_monthly(
            profile['acquisition_cost'],
            profile['salvage_value'],
            profile['useful_life_months'],
            profile['depreciation_start_date'],
            as_of_date
        )

        # Calculate current period's depreciation
        current_period_start = f"{period_year}-{period_month:02d}-01"
        period_calc = calculate_straight_line_monthly(
            profile['acquisition_cost'],
            profile['salvage_value'],
            profile['useful_life_months'],
            profile['depreciation_start_date'],
            current_period_start
        )

        period_depreciation = calc['monthly_depreciation']

        return {
            'can_depreciate': True,
            'asset_id': asset_id,
            'asset_code': asset['asset_code'],
            'period_month': period_month,
            'period_year': period_year,
            'acquisition_cost': profile['acquisition_cost'],
            'salvage_value': profile['salvage_value'],
            'depreciable_amount': profile['acquisition_cost'] - profile['salvage_value'],
            'monthly_depreciation': calc['monthly_depreciation'],
            'current_accumulated': calc['accumulated_depreciation'],
            'current_net_book_value': calc['net_book_value'],
            'period_depreciation': period_depreciation,
            'is_full_depreciated': calc['net_book_value'] <= profile['salvage_value'],
        }

    finally:
        conn.close()


import calendar


# =============================================================================
# ASSET STATUS WORKFLOW
# =============================================================================

ASSET_STATUSES = [
    'Draft',
    'Pending Approval',
    'Active',
    'Under Maintenance',
    'Transferred',
    'Pending Disposal',
    'Disposed',
    'Retired',
    'Inactive',
]

ASSET_STATUS_TRANSITIONS = {
    'Draft': ['Pending Approval', 'Active', 'Inactive'],
    'Pending Approval': ['Draft', 'Active', 'Inactive'],
    'Active': ['Under Maintenance', 'Transferred', 'Pending Disposal', 'Inactive'],
    'Under Maintenance': ['Active'],
    'Transferred': ['Active', 'Pending Disposal'],
    'Pending Disposal': ['Active', 'Disposed'],
    'Disposed': [],
    'Retired': [],
    'Inactive': ['Active', 'Pending Disposal'],
}


def can_transition_status(current_status: str, new_status: str) -> bool:
    """Check if a status transition is valid."""
    allowed = ASSET_STATUS_TRANSITIONS.get(current_status, [])
    return new_status in allowed


# =============================================================================
# RUN INITIALIZATION
# =============================================================================

if __name__ == '__main__' or True:
    init_asset_tables()
