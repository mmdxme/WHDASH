"""
Quality Management Module - Minimal Working Version
=================================================
This is a simplified version that provides the basic structure.
The full implementation can be added incrementally.
"""

from database import get_db
import sqlite3
from datetime import datetime

def get_db():
    """Get database connection."""
    conn = sqlite3.connect('warehouse.db')
    conn.row_factory = sqlite3.Row
    return conn

def initialize_quality_tables():
    """Initialize quality management tables."""
    with get_db() as db:
        # Inspection Types
        db.execute("""
            CREATE TABLE IF NOT EXISTS quality_inspection_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                applicable_types TEXT,
                result_type TEXT DEFAULT 'pass_fail',
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        
        # Inspection Templates
        db.execute("""
            CREATE TABLE IF NOT EXISTS quality_inspection_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_code TEXT UNIQUE NOT NULL,
                template_name TEXT NOT NULL,
                inspection_type TEXT,
                description TEXT,
                company_id INTEGER,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        
        # Inspections
        db.execute("""
            CREATE TABLE IF NOT EXISTS quality_inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inspection_number TEXT UNIQUE,
                inspection_type TEXT NOT NULL,
                template_id INTEGER,
                source_type TEXT,
                source_reference TEXT,
                company_id INTEGER,
                warehouse_id INTEGER,
                supplier_id INTEGER,
                customer_id INTEGER,
                item_id INTEGER,
                item_name TEXT,
                quantity_inspected REAL DEFAULT 0,
                quantity_passed REAL DEFAULT 0,
                quantity_failed REAL DEFAULT 0,
                result TEXT,
                status TEXT DEFAULT 'pending',
                inspector_id INTEGER,
                inspection_date TEXT,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                created_by INTEGER
            )
        """)
        
        # Defect Categories
        db.execute("""
            CREATE TABLE IF NOT EXISTS quality_defect_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                severity_levels TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        # Non-Conformances
        db.execute("""
            CREATE TABLE IF NOT EXISTS quality_non_conformances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ncr_number TEXT UNIQUE,
                source_type TEXT,
                source_id INTEGER,
                severity TEXT,
                description TEXT,
                status TEXT DEFAULT 'open',
                item_id INTEGER,
                quantity_affected REAL DEFAULT 0,
                initiator_id INTEGER,
                open_date TEXT,
                target_close_date TEXT,
                actual_close_date TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        
        # CAPA Records
        db.execute("""
            CREATE TABLE IF NOT EXISTS quality_capa_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capa_number TEXT UNIQUE,
                title TEXT NOT NULL,
                capa_type TEXT,
                severity TEXT,
                description TEXT,
                root_cause TEXT,
                status TEXT DEFAULT 'open',
                owner_id INTEGER,
                open_date TEXT,
                target_date TEXT,
                close_date TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        
        # CAPA Actions
        db.execute("""
            CREATE TABLE IF NOT EXISTS quality_capa_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capa_id INTEGER NOT NULL,
                action_description TEXT,
                responsible_id INTEGER,
                due_date TEXT,
                status TEXT DEFAULT 'open',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        
        # Audit Plans
        db.execute("""
            CREATE TABLE IF NOT EXISTS quality_audit_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_number TEXT UNIQUE,
                audit_title TEXT NOT NULL,
                audit_type TEXT,
                auditor_id INTEGER,
                scheduled_start_date TEXT,
                status TEXT DEFAULT 'scheduled',
                company_id INTEGER,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        
        # Audit Findings
        db.execute("""
            CREATE TABLE IF NOT EXISTS quality_audit_findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                finding_number TEXT,
                severity TEXT,
                description TEXT,
                corrective_action TEXT,
                status TEXT DEFAULT 'open',
                due_date TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        
        # Quality Settings
        db.execute("""
            CREATE TABLE IF NOT EXISTS quality_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT,
                description TEXT,
                category TEXT,
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        
        # CAPA Categories
        db.execute("""
            CREATE TABLE IF NOT EXISTS quality_capa_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        # Root Cause Categories
        db.execute("""
            CREATE TABLE IF NOT EXISTS quality_root_cause_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        # Quality Audit Log
        db.execute("""
            CREATE TABLE IF NOT EXISTS quality_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_number TEXT UNIQUE,
                entity_type TEXT,
                entity_id INTEGER,
                action TEXT,
                user_id INTEGER,
                timestamp TEXT DEFAULT (datetime('now')),
                notes TEXT
            )
        """)
        
        db.commit()
    
    # Seed default data
    _seed_default_data()
    
    return True

def _seed_default_data():
    """Seed default configuration data."""
    defaults = [
        ('QUALITY_AUTO_NCR_ON_FAIL', '1', 'Auto-create NCR when inspection fails'),
        ('QUALITY_NCR_NUMBERING_PREFIX', 'NCR', 'NCR number prefix'),
        ('QUALITY_INSPECTION_NUMBERING_PREFIX', 'INS', 'Inspection number prefix'),
        ('QUALITY_CAPA_NUMBERING_PREFIX', 'CAPA', 'CAPA number prefix'),
        ('QUALITY_AUDIT_NUMBERING_PREFIX', 'AUD', 'Audit number prefix'),
        ('QUALITY_DEFAULT_SEVERITY', 'MINOR', 'Default severity for NCRs'),
        ('QUALITY_OVERDUE_DAYS_WARNING', '7', 'Days before due to send warning'),
    ]
    
    with get_db() as db:
        for key, value, description in defaults:
            db.execute("""
                INSERT OR IGNORE INTO quality_settings (setting_key, setting_value, description)
                VALUES (?, ?, ?)
            """, (key, value, description))
        db.commit()

# Basic query functions
def get_quality_dashboard_stats(company_id=None, branch_id=None):
    """Get basic dashboard statistics."""
    with get_db() as db:
        stats = {}
        
        # Count inspections by status
        result = db.execute("""
            SELECT status, COUNT(*) as count
            FROM quality_inspections
            GROUP BY status
        """).fetchall()
        stats['inspections_by_status'] = [dict(r) for r in result]
        
        # Count NCRs by status
        result = db.execute("""
            SELECT status, COUNT(*) as count
            FROM quality_non_conformances
            GROUP BY status
        """).fetchall()
        stats['ncrs_by_status'] = [dict(r) for r in result]
        
        # Count CAPAs by status
        result = db.execute("""
            SELECT status, COUNT(*) as count
            FROM quality_capa_records
            GROUP BY status
        """).fetchall()
        stats['capas_by_status'] = [dict(r) for r in result]
        
        # Recent inspections
        result = db.execute("""
            SELECT * FROM quality_inspections
            ORDER BY created_at DESC LIMIT 10
        """).fetchall()
        stats['recent_inspections'] = [dict(r) for r in result]
        
        return stats

def get_inspections(filters=None):
    """Get inspections with optional filters."""
    with get_db() as db:
        query = "SELECT * FROM quality_inspections WHERE 1=1"
        params = []
        
        if filters:
            if filters.get('status'):
                query += " AND status = ?"
                params.append(filters['status'])
            if filters.get('type'):
                query += " AND inspection_type = ?"
                params.append(filters['type'])
        
        query += " ORDER BY created_at DESC"
        
        result = db.execute(query, params).fetchall()
        return [dict(r) for r in result]

def get_inspection_by_id(inspection_id):
    """Get a single inspection by ID."""
    with get_db() as db:
        result = db.execute(
            "SELECT * FROM quality_inspections WHERE id = ?",
            (inspection_id,)
        ).fetchone()
        return dict(result) if result else None

def create_inspection(data):
    """Create a new inspection."""
    with get_db() as db:
        cursor = db.execute("""
            INSERT INTO quality_inspections (
                inspection_number, inspection_type, template_id,
                source_type, source_reference, company_id,
                warehouse_id, supplier_id, customer_id, item_id, item_name,
                quantity_inspected, quantity_passed, quantity_failed,
                result, status, inspector_id, inspection_date, notes,
                created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('inspection_number'),
            data.get('inspection_type'),
            data.get('template_id'),
            data.get('source_type'),
            data.get('source_reference'),
            data.get('company_id'),
            data.get('warehouse_id'),
            data.get('supplier_id'),
            data.get('customer_id'),
            data.get('item_id'),
            data.get('item_name'),
            data.get('quantity_inspected', 0),
            data.get('quantity_passed', 0),
            data.get('quantity_failed', 0),
            data.get('result'),
            data.get('status', 'pending'),
            data.get('inspector_id'),
            data.get('inspection_date'),
            data.get('notes'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid

def update_inspection(inspection_id, data):
    """Update an inspection record."""
    with get_db() as db:
        current = db.execute("SELECT * FROM quality_inspections WHERE id = ?", (inspection_id,)).fetchone()
        
        fields = []
        values = []
        for key in ['inspection_type', 'template_id', 'quantity_inspected',
                    'quantity_passed', 'quantity_failed',
                    'result', 'status', 'inspector_id', 'inspection_date', 'notes']:
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])
        
        if fields:
            fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(inspection_id)
            
            db.execute(f"UPDATE quality_inspections SET {', '.join(fields[:-1])} WHERE id = ?", values[:-1])
            db.commit()
        
        if current:
            for key in data:
                if data[key] != current[key]:
                    _log_quality_change('INSPECTION', inspection_id, current['inspection_number'], 
                                       f'FIELD_UPDATE:{key}', 
                                       old_value=str(current.get(key)), 
                                       new_value=str(data[key]),
                                       user_id=data.get('updated_by'))

def get_inspection_lines(inspection_id):
    """Get inspection checklist lines."""
    with get_db() as db:
        return db.execute("""
            SELECT * FROM quality_inspection_lines
            WHERE inspection_id = ?
            ORDER BY line_number
        """, (inspection_id,)).fetchall()

def add_inspection_line(inspection_id, data):
    """Add a checklist line to an inspection."""
    with get_db() as db:
        db.execute("""
            INSERT INTO quality_inspection_lines (
                inspection_id, template_line_id, line_number, criterion, description,
                inspection_method, acceptance_criteria, result_type, result,
                measurement_value, measurement_unit, is_conforming, findings,
                severity, is_mandatory, weight, notes, attachments
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            inspection_id, data.get('template_line_id'), data.get('line_number'),
            data.get('criterion'), data.get('description'), data.get('inspection_method'),
            data.get('acceptance_criteria'), data.get('result_type', 'PASS_FAIL'),
            data.get('result'), data.get('measurement_value'), data.get('measurement_unit'),
            data.get('is_conforming'), data.get('findings'), data.get('severity'),
            data.get('is_mandatory', 1), data.get('weight', 1.0), data.get('notes'),
            data.get('attachments')
        ))
        db.commit()
        return db.execute("SELECT last_insert_rowid()").fetchone()[0]

def get_ncrs(filters=None):
    """Get NCRs with optional filters."""
    with get_db() as db:
        query = "SELECT * FROM quality_non_conformances WHERE 1=1"
        params = []
        
        if filters:
            if filters.get('status'):
                query += " AND status = ?"
                params.append(filters['status'])
            if filters.get('severity'):
                query += " AND severity = ?"
                params.append(filters['severity'])
        
        query += " ORDER BY created_at DESC"
        
        result = db.execute(query, params).fetchall()
        return [dict(r) for r in result]

def get_ncr_by_id(ncr_id):
    """Get a single NCR by ID."""
    with get_db() as db:
        result = db.execute(
            "SELECT * FROM quality_non_conformances WHERE id = ?",
            (ncr_id,)
        ).fetchone()
        return dict(result) if result else None

def create_ncr(data):
    """Create a new NCR."""
    with get_db() as db:
        cursor = db.execute("""
            INSERT INTO quality_non_conformances (
                ncr_number, source_type, source_id, severity,
                description, status, item_id, quantity_affected,
                initiator_id, open_date, target_close_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('ncr_number'),
            data.get('source_type'),
            data.get('source_id'),
            data.get('severity'),
            data.get('description'),
            data.get('status', 'open'),
            data.get('item_id'),
            data.get('quantity_affected', 0),
            data.get('initiator_id'),
            data.get('open_date'),
            data.get('target_close_date')
        ))
        db.commit()
        return cursor.lastrowid

def update_ncr(ncr_id, data):
    """Update an NCR record."""
    with get_db() as db:
        current = db.execute("SELECT * FROM quality_non_conformances WHERE id = ?", (ncr_id,)).fetchone()
        
        updatable_fields = [
            'status', 'owner_id', 'owner_name', 'assigned_to_id', 'assigned_to_name',
            'containment_required', 'containment_status', 'root_cause_required', 'root_cause_status',
            'capa_required', 'capa_id', 'immediate_action', 'disposition',
            'hold_quantity', 'return_quantity', 'rework_quantity', 'scrap_quantity', 'use_as_is_quantity',
            'financial_impact', 'target_close_date', 'actual_close_date',
            'closure_notes', 'notes', 'attachments'
        ]
        
        fields = []
        values = []
        for key in updatable_fields:
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])
        
        if fields:
            fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(ncr_id)
            
            db.execute(f"UPDATE quality_non_conformances SET {', '.join(fields[:-1])} WHERE id = ?", values[:-1])
            db.commit()
        
        if current:
            for key in data:
                if data[key] != current[key]:
                    _log_quality_change('NCR', ncr_id, current['ncr_number'], f'FIELD_UPDATE:{key}',
                                       old_value=str(current.get(key)), new_value=str(data[key]),
                                       user_id=data.get('updated_by'))

def get_containment_actions(ncr_id):
    """Get containment actions for an NCR."""
    with get_db() as db:
        return db.execute("""
            SELECT * FROM quality_containment_actions
            WHERE ncr_id = ?
            ORDER BY created_at
        """, (ncr_id,)).fetchall()

def create_containment_action(ncr_id, data):
    """Create a containment action for an NCR."""
    with get_db() as db:
        action_number = get_next_containment_action_number()
        
        db.execute("""
            INSERT INTO quality_containment_actions (
                ncr_id, action_number, action_type, description,
                responsible_id, responsible_name, due_date, completed_date,
                status, evidence, notes, verified_by, verified_at,
                created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ncr_id, action_number, data.get('action_type'), data.get('description'),
            data.get('responsible_id'), data.get('responsible_name'), data.get('due_date'),
            data.get('completed_date'), data.get('status', 'PENDING'),
            data.get('evidence'), data.get('notes'), data.get('verified_by'),
            data.get('verified_at'), datetime.now().isoformat(), data.get('created_by')
        ))
        db.commit()
        
        action_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        db.execute("""
            UPDATE quality_non_conformances
            SET containment_status = 'IN_PROGRESS'
            WHERE id = ?
        """, (ncr_id,))
        db.commit()
        
        return action_id, action_number

def update_containment_action(action_id, data):
    """Update a containment action."""
    with get_db() as db:
        db.execute("""
            UPDATE quality_containment_actions
            SET action_type = COALESCE(?, action_type),
                description = COALESCE(?, description),
                responsible_id = COALESCE(?, responsible_id),
                responsible_name = COALESCE(?, responsible_name),
                due_date = COALESCE(?, due_date),
                completed_date = COALESCE(?, completed_date),
                status = COALESCE(?, status),
                evidence = COALESCE(?, evidence),
                notes = COALESCE(?, notes),
                verified_by = COALESCE(?, verified_by),
                verified_at = COALESCE(?, verified_at)
            WHERE id = ?
        """, (
            data.get('action_type'), data.get('description'),
            data.get('responsible_id'), data.get('responsible_name'),
            data.get('due_date'), data.get('completed_date'),
            data.get('status'), data.get('evidence'),
            data.get('notes'), data.get('verified_by'),
            data.get('verified_at'), action_id
        ))
        db.commit()

def get_capas(filters=None):
    """Get CAPAs with optional filters."""
    with get_db() as db:
        query = "SELECT * FROM quality_capa_records WHERE 1=1"
        params = []
        
        if filters:
            if filters.get('status'):
                query += " AND status = ?"
                params.append(filters['status'])
            if filters.get('type'):
                query += " AND capa_type = ?"
                params.append(filters['type'])
        
        query += " ORDER BY created_at DESC"
        
        result = db.execute(query, params).fetchall()
        return [dict(r) for r in result]

def get_capa_by_id(capa_id):
    """Get a single CAPA by ID."""
    with get_db() as db:
        result = db.execute(
            "SELECT * FROM quality_capa_records WHERE id = ?",
            (capa_id,)
        ).fetchone()
        return dict(result) if result else None

def create_capa(data):
    """Create a new CAPA."""
    with get_db() as db:
        cursor = db.execute("""
            INSERT INTO quality_capa_records (
                capa_number, title, capa_type, severity,
                description, root_cause, status, owner_id,
                open_date, target_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('capa_number'),
            data.get('title'),
            data.get('capa_type'),
            data.get('severity'),
            data.get('description'),
            data.get('root_cause'),
            data.get('status', 'open'),
            data.get('owner_id'),
            data.get('open_date'),
            data.get('target_date')
        ))
        db.commit()
        return cursor.lastrowid

def get_capa_by_id(capa_id):
    """Get a single CAPA by ID."""
    with get_db() as db:
        return db.execute("""
            SELECT qcr.*, qcc.name as category_name, qrc.name as root_cause_category_name
            FROM quality_capa_records qcr
            LEFT JOIN quality_capa_categories qcc ON qcr.category_id = qcc.id
            LEFT JOIN quality_root_cause_categories qrc ON qcr.root_cause_category_id = qrc.id
            WHERE qcr.id = ?
        """, (capa_id,)).fetchone()

def update_capa(capa_id, data):
    """Update a CAPA record."""
    with get_db() as db:
        current = db.execute("SELECT * FROM quality_capa_records WHERE id = ?", (capa_id,)).fetchone()
        
        updatable_fields = [
            'category_id', 'capa_type', 'severity', 'priority', 'title', 'description',
            'root_cause_summary', 'root_cause_category_id', 'root_cause_description',
            'owner_id', 'owner_name', 'approver_id', 'approver_name',
            'target_date', 'actual_completion_date', 'status',
            'effectiveness_verification_required', 'effectiveness_review_status',
            'effectiveness_review_date', 'effectiveness_reviewer_id', 'effectiveness_result',
            'effectiveness_notes', 'effectiveness_evidence',
            'closed_by', 'closed_at', 'closure_notes',
            'reopen_count', 'reopen_reason', 'notes', 'attachments'
        ]
        
        fields = []
        values = []
        for key in updatable_fields:
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])
        
        if fields:
            fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(capa_id)
            
            db.execute(f"UPDATE quality_capa_records SET {', '.join(fields[:-1])} WHERE id = ?", values[:-1])
            db.commit()
        
        if current:
            for key in data:
                if data[key] != current[key]:
                    _log_quality_change('CAPA', capa_id, current['capa_number'], f'FIELD_UPDATE:{key}',
                                       old_value=str(current.get(key)), new_value=str(data[key]),
                                       user_id=data.get('updated_by'))

def get_capa_actions(capa_id):
    """Get CAPA actions for a CAPA record."""
    with get_db() as db:
        return db.execute("""
            SELECT * FROM quality_capa_actions
            WHERE capa_id = ?
            ORDER BY created_at
        """, (capa_id,)).fetchall()

def create_capa_action(capa_id, data):
    """Create a CAPA action."""
    with get_db() as db:
        action_number = get_next_capa_action_number()
        
        db.execute("""
            INSERT INTO quality_capa_actions (
                capa_id, action_number, action_type, description,
                responsible_id, responsible_name, due_date, completed_date,
                status, evidence, notes, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            capa_id, action_number, data.get('action_type'), data.get('description'),
            data.get('responsible_id'), data.get('responsible_name'), data.get('due_date'),
            data.get('completed_date'), data.get('status', 'PENDING'),
            data.get('evidence'), data.get('notes'), datetime.now().isoformat(), data.get('created_by')
        ))
        db.commit()
        return db.execute("SELECT last_insert_rowid()").fetchone()[0]

def update_capa_action(action_id, data):
    """Update a CAPA action."""
    with get_db() as db:
        db.execute("""
            UPDATE quality_capa_actions
            SET action_type = COALESCE(?, action_type),
                description = COALESCE(?, description),
                responsible_id = COALESCE(?, responsible_id),
                responsible_name = COALESCE(?, responsible_name),
                due_date = COALESCE(?, due_date),
                completed_date = COALESCE(?, completed_date),
                status = COALESCE(?, status),
                evidence = COALESCE(?, evidence),
                notes = COALESCE(?, notes)
            WHERE id = ?
        """, (
            data.get('action_type'), data.get('description'),
            data.get('responsible_id'), data.get('responsible_name'),
            data.get('due_date'), data.get('completed_date'),
            data.get('status'), data.get('evidence'),
            data.get('notes'), action_id
        ))
        db.commit()

def create_effectiveness_review(capa_id, data):
    """Create an effectiveness review for a CAPA."""
    with get_db() as db:
        db.execute("""
            INSERT INTO quality_effectiveness_reviews (
                capa_id, review_date, reviewer_id, reviewer_name,
                overall_result, findings, recommendations,
                next_review_date, notes, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            capa_id, data.get('review_date'), data.get('reviewer_id'),
            data.get('reviewer_name'), data.get('overall_result'),
            data.get('findings'), data.get('recommendations'),
            data.get('next_review_date'), data.get('notes'),
            datetime.now().isoformat(), data.get('created_by')
        ))
        db.commit()
        return db.execute("SELECT last_insert_rowid()").fetchone()[0]

def get_audit_plans(filters=None):
    """Get audit plans with optional filters."""
    with get_db() as db:
        query = "SELECT * FROM quality_audit_plans WHERE 1=1"
        params = []
        
        if filters:
            if filters.get('status'):
                query += " AND status = ?"
                params.append(filters['status'])
        
        query += " ORDER BY created_at DESC"
        
        result = db.execute(query, params).fetchall()
        return [dict(r) for r in result]

def get_audit_plan_by_id(plan_id):
    """Get a single audit plan by ID."""
    with get_db() as db:
        result = db.execute(
            "SELECT * FROM quality_audit_plans WHERE id = ?",
            (plan_id,)
        ).fetchone()
        return dict(result) if result else None

def create_audit_plan(data):
    """Create a new audit plan."""
    with get_db() as db:
        cursor = db.execute("""
            INSERT INTO quality_audit_plans (
                plan_number, audit_title, audit_type,
                auditor_id, scheduled_start_date, status,
                company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('plan_number'),
            data.get('audit_title'),
            data.get('audit_type'),
            data.get('auditor_id'),
            data.get('scheduled_start_date'),
            data.get('status', 'scheduled'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid

def update_audit_plan(plan_id, data):
    """Update an audit plan."""
    with get_db() as db:
        current = db.execute("SELECT * FROM quality_audit_plans WHERE id = ?", (plan_id,)).fetchone()
        
        updatable_fields = [
            'audit_type', 'scope', 'objectives', 'warehouse_id', 'site_location',
            'department', 'process_area', 'scheduled_start_date', 'scheduled_end_date',
            'actual_start_date', 'actual_end_date', 'lead_auditor_id', 'lead_auditor_name',
            'auditor_ids', 'auditor_names', 'auditee_id', 'auditee_name', 'auditee_department',
            'checklist_template_id', 'status', 'preparation_status', 'document_review_notes',
            'notification_sent', 'opening_meeting_held', 'closing_meeting_held',
            'notes', 'attachments'
        ]
        
        fields = []
        values = []
        for key in updatable_fields:
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])
        
        if fields:
            fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(plan_id)
            
            db.execute(f"UPDATE quality_audit_plans SET {', '.join(fields[:-1])} WHERE id = ?", values[:-1])
            db.commit()
        
        if current:
            for key in data:
                if data[key] != current[key]:
                    _log_quality_change('AUDIT_PLAN', plan_id, current['plan_number'], f'FIELD_UPDATE:{key}',
                                       old_value=str(current.get(key)), new_value=str(data[key]),
                                       user_id=data.get('updated_by'))

def get_audit_findings(filters=None):
    """Get audit findings with optional filters."""
    with get_db() as db:
        query = """
            SELECT qaf.*, qap.plan_number, qap.audit_title
            FROM quality_audit_findings qaf
            LEFT JOIN quality_audit_plans qap ON qaf.audit_plan_id = qap.id
            WHERE 1=1
        """
        params = []
        
        if filters:
            if filters.get('audit_plan_id'):
                query += " AND qaf.audit_plan_id = ?"
                params.append(filters['audit_plan_id'])
            if filters.get('status'):
                query += " AND qaf.status = ?"
                params.append(filters['status'])
            if filters.get('severity'):
                query += " AND qaf.severity = ?"
                params.append(filters['severity'])
        
        query += " ORDER BY qaf.created_at DESC"
        
        result = db.execute(query, params).fetchall()
        return [dict(r) for r in result]

def get_finding_by_id(finding_id):
    """Get a single audit finding by ID."""
    with get_db() as db:
        result = db.execute(
            "SELECT * FROM quality_audit_findings WHERE id = ?",
            (finding_id,)
        ).fetchone()
        return dict(result) if result else None

def create_audit_finding(plan_id, data):
    """Create a new audit finding."""
    with get_db() as db:
        finding_number = get_next_audit_finding_number()
        
        cursor = db.execute("""
            INSERT INTO quality_audit_findings (
                audit_plan_id, finding_number, category, severity, title,
                description, root_cause, suggested_corrective_action,
                due_date, status, owner_id, owner_name,
                verified_by, verified_at, closure_date, closure_notes,
                company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            plan_id, finding_number, data.get('category'),
            data.get('severity', 'MINOR'), data.get('title'),
            data.get('description'), data.get('root_cause'),
            data.get('suggested_corrective_action'), data.get('due_date'),
            data.get('status', 'OPEN'), data.get('owner_id'),
            data.get('owner_name'), data.get('verified_by'),
            data.get('verified_at'), data.get('closure_date'),
            data.get('closure_notes'), data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid

def update_audit_finding(finding_id, data):
    """Update an audit finding."""
    with get_db() as db:
        db.execute("""
            UPDATE quality_audit_findings
            SET category = COALESCE(?, category),
                severity = COALESCE(?, severity),
                title = COALESCE(?, title),
                description = COALESCE(?, description),
                root_cause = COALESCE(?, root_cause),
                suggested_corrective_action = COALESCE(?, suggested_corrective_action),
                due_date = COALESCE(?, due_date),
                status = COALESCE(?, status),
                owner_id = COALESCE(?, owner_id),
                owner_name = COALESCE(?, owner_name),
                verified_by = COALESCE(?, verified_by),
                verified_at = COALESCE(?, verified_at),
                closure_date = COALESCE(?, closure_date),
                closure_notes = COALESCE(?, closure_notes)
            WHERE id = ?
        """, (
            data.get('category'), data.get('severity'), data.get('title'),
            data.get('description'), data.get('root_cause'),
            data.get('suggested_corrective_action'), data.get('due_date'),
            data.get('status'), data.get('owner_id'), data.get('owner_name'),
            data.get('verified_by'), data.get('verified_at'),
            data.get('closure_date'), data.get('closure_notes'), finding_id
        ))
        db.commit()

def get_audit_checklist_templates():
    """Get all active audit checklist templates."""
    with get_db() as db:
        return db.execute("""
            SELECT * FROM quality_audit_checklist_templates
            WHERE is_active = 1
            ORDER BY template_name
        """).fetchall()

def get_audit_programs():
    """Get all active audit programs."""
    with get_db() as db:
        return db.execute("""
            SELECT * FROM quality_audit_programs
            WHERE status = 'ACTIVE'
            ORDER BY program_name
        """).fetchall()

def get_quality_setting(key, default=None):
    """Get a quality setting value."""
    with get_db() as db:
        result = db.execute(
            "SELECT setting_value FROM quality_settings WHERE setting_key = ?",
            (key,)
        ).fetchone()
        return result['setting_value'] if result else default

def set_quality_setting(key, value):
    """Set a quality setting value."""
    with get_db() as db:
        db.execute("""
            INSERT OR REPLACE INTO quality_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, datetime('now'))
        """, (key, value))
        db.commit()

def get_quality_audit_log(filters=None):
    """Get quality audit log."""
    with get_db() as db:
        query = "SELECT * FROM quality_audit_log WHERE 1=1"
        params = []
        
        if filters:
            if filters.get('entity_type'):
                query += " AND entity_type = ?"
                params.append(filters['entity_type'])
        
        query += " ORDER BY timestamp DESC LIMIT 100"
        
        result = db.execute(query, params).fetchall()
        return [dict(r) for r in result]

def get_inspection_types():
    """Get all active inspection types."""
    with get_db() as db:
        result = db.execute(
            "SELECT * FROM quality_inspection_types WHERE is_active = 1"
        ).fetchall()
        return [dict(r) for r in result]

def get_defect_categories():
    """Get all active defect categories."""
    with get_db() as db:
        result = db.execute(
            "SELECT * FROM quality_defect_categories WHERE is_active = 1"
        ).fetchall()
        return [dict(r) for r in result]

def get_capa_categories():
    """Get all active CAPA categories."""
    with get_db() as db:
        result = db.execute(
            "SELECT * FROM quality_capa_categories WHERE is_active = 1"
        ).fetchall()
        return [dict(r) for r in result]

def get_root_cause_categories():
    """Get all active root cause categories."""
    with get_db() as db:
        result = db.execute(
            "SELECT * FROM quality_root_cause_categories WHERE is_active = 1"
        ).fetchall()
        return [dict(r) for r in result]

def get_inspection_templates():
    """Get all active inspection templates."""
    with get_db() as db:
        result = db.execute(
            "SELECT * FROM quality_inspection_templates WHERE is_active = 1"
        ).fetchall()
        return [dict(r) for r in result]

# Stub for report functions to avoid import errors
def get_inspection_report_data(filters=None):
    """Stub for inspection report data."""
    return []

def get_ncr_summary_report(*args, **kwargs):
    """Stub for NCR summary report."""
    return {'by_status': [], 'by_severity': [], 'by_category': []}

def get_capa_summary_report(*args, **kwargs):
    """Stub for CAPA summary report."""
    return {'by_status': [], 'by_type': [], 'effectiveness_summary': []}

def get_supplier_quality_report(*args, **kwargs):
    """Stub for supplier quality report."""
    return {'ncr_by_supplier': []}

if __name__ == '__main__':
    initialize_quality_tables()
    print("Quality tables initialized successfully!")
