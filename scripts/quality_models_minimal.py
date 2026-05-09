"""
Quality Management Module Database Models
=========================================
Enterprise-grade Quality Management for the MMDx platform.

Tables:
- quality_inspection_types
- quality_inspection_templates  
- quality_inspection_template_lines
- quality_inspection_plans
- quality_inspections
- quality_inspection_lines
- quality_inspection_findings
- quality_defect_categories
- quality_non_conformances
- quality_containment_actions
- quality_capa_categories
- quality_capa_records
- quality_capa_actions
- quality_root_cause_categories
- quality_effectiveness_reviews
- quality_audit_programs
- quality_audit_plans
- quality_audit_checklist_templates
- quality_audit_checklist_template_lines
- quality_audit_checklists
- quality_audit_checklist_lines
- quality_audit_findings
- quality_settings
- quality_approval_records
- quality_audit_log
"""

from database import get_db
import sqlite3
from datetime import datetime

def get_db():
    """Get database connection."""
    conn = sqlite3.connect('warehouse.db')
    conn.row_factory = sqlite3.Row
    return conn

QUALITY_TABLES = [
    """CREATE TABLE IF NOT EXISTS quality_inspection_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        description TEXT,
        category TEXT,
        applicable_inspection_types TEXT,
        result_type TEXT DEFAULT 'pass_fail',
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS quality_inspections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inspection_number TEXT UNIQUE,
        inspection_type TEXT NOT NULL,
        template_id INTEGER,
        source_type TEXT,
        source_reference TEXT,
        source_reference_id INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        warehouse_id INTEGER,
        location TEXT,
        department TEXT,
        supplier_id INTEGER,
        customer_id INTEGER,
        item_id INTEGER,
        item_code TEXT,
        item_name TEXT,
        lot_number TEXT,
        serial_number TEXT,
        batch_number TEXT,
        quantity_received REAL DEFAULT 0,
        quantity_inspected REAL DEFAULT 0,
        sample_size INTEGER DEFAULT 0,
        quantity_accepted REAL DEFAULT 0,
        quantity_rejected REAL DEFAULT 0,
        quantity_held REAL DEFAULT 0,
        quantity_conditionally_accepted REAL DEFAULT 0,
        inspection_date TEXT,
        inspection_time TEXT,
        inspector_id INTEGER,
        inspector_name TEXT,
        team_members TEXT,
        result TEXT,
        status TEXT DEFAULT 'pending',
        disposition TEXT,
        disposition_notes TEXT,
        reinspection_required INTEGER DEFAULT 0,
        reinspection_of_id INTEGER,
        ncr_id INTEGER,
        notes TEXT,
        attachments TEXT,
        completed_at TEXT,
        completed_by INTEGER,
        created_at TEXT DEFAULT (datetime('now')),
        created_by INTEGER,
        updated_at TEXT DEFAULT (datetime('now'))
    )""",
]

def initialize_quality_tables():
    """Initialize all quality management tables."""
    with get_db() as db:
        for table_sql in QUALITY_TABLES:
            db.execute(table_sql)
        db.commit()
    print("Quality tables initialized")

if __name__ == '__main__':
    initialize_quality_tables()
    print("Done")
