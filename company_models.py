"""
Multi-Company Management System - Data Models
==============================================
This module defines all data models for the multi-company management system.

Tables:
- company_profiles: Extended company information and settings
- company_branches: Branch/facility hierarchy under companies
- company_facilities: Warehouses, offices, and operational units
- company_warehouses: Warehouse-to-company mapping with ownership
- company_relationships: Intercompany relationships and trade rules
- user_company_access: User-company access control matrix
- company_settings: Company-specific settings
- company_numbering_rules: Company-specific document numbering
- company_policies: Company-specific business policies
- intercompany_workflows: Intercompany workflow definitions
- intercompany_transactions: Intercompany transaction records
- company_audit_log: Company-level audit trail
- shared_data_rules: Data sharing governance rules

Usage:
    from company_models import (
        get_all_companies, get_company_by_id,
        get_company_branches, create_branch,
        get_user_companies, assign_user_to_company,
        get_company_settings, update_company_setting
    )
"""

import sqlite3
import os
from datetime import datetime
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
# MULTI-COMPANY TABLE DEFINITIONS
# =============================================================================

MULTI_COMPANY_TABLES = [
    # -------------------------------------------------------------------------
    # 1. Company Profiles - Extended company information
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS company_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        trade_name TEXT,
        short_name TEXT,
        company_type TEXT DEFAULT 'subsidiary',
        company_type_detail TEXT,
        registration_number TEXT,
        tax_id TEXT,
        vat_number TEXT,
        license_number TEXT,
        main_currency TEXT DEFAULT 'AED',
        timezone TEXT DEFAULT 'Asia/Dubai',
        date_format TEXT DEFAULT 'DD/MM/YYYY',
        fiscal_year_start INTEGER DEFAULT 1,
        fiscal_year_end INTEGER DEFAULT 12,
        default_language TEXT DEFAULT 'en',
        logo_path TEXT,
        primary_color TEXT DEFAULT '#0066CC',
        secondary_color TEXT DEFAULT '#6C757D',
        address_line1 TEXT,
        address_line2 TEXT,
        city TEXT,
        country TEXT,
        postal_code TEXT,
        phone TEXT,
        mobile TEXT,
        email TEXT,
        website TEXT,
        contact_person TEXT,
        parent_company_id INTEGER,
        is_parent INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
        FOREIGN KEY (parent_company_id) REFERENCES companies(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 2. Company Branches - Branch/facility hierarchy
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS company_branches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        branch_code TEXT UNIQUE NOT NULL,
        branch_name TEXT NOT NULL,
        branch_type TEXT DEFAULT 'branch',
        description TEXT,
        address TEXT,
        city TEXT,
        country TEXT,
        postal_code TEXT,
        phone TEXT,
        email TEXT,
        manager_name TEXT,
        manager_contact TEXT,
        is_active INTEGER DEFAULT 1,
        is_operational INTEGER DEFAULT 1,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 3. Company Facilities - Warehouses, offices, operational units
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS company_facilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        facility_code TEXT UNIQUE NOT NULL,
        facility_name TEXT NOT NULL,
        company_id INTEGER NOT NULL,
        branch_id INTEGER,
        facility_type TEXT NOT NULL,
        facility_subtype TEXT,
        address TEXT,
        city TEXT,
        country TEXT,
        postal_code TEXT,
        phone TEXT,
        email TEXT,
        manager_name TEXT,
        manager_contact TEXT,
        capacity_sqm REAL,
        capacity_pallets INTEGER,
        is_active INTEGER DEFAULT 1,
        is_shared INTEGER DEFAULT 0,
        shared_with_companies TEXT,
        operational_hours TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
        FOREIGN KEY (branch_id) REFERENCES company_branches(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 4. Company Warehouses - Warehouse ownership and access mapping
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS company_warehouses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse_id INTEGER NOT NULL,
        company_id INTEGER NOT NULL,
        ownership_type TEXT DEFAULT 'owned',
        ownership_percentage REAL DEFAULT 100,
        is_primary INTEGER DEFAULT 0,
        stock_visibility TEXT DEFAULT 'company_only',
        access_level TEXT DEFAULT 'full',
        operational_rules TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (warehouse_id) REFERENCES warehouses(id) ON DELETE CASCADE,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
        UNIQUE(warehouse_id, company_id)
    )""",

    # -------------------------------------------------------------------------
    # 5. Company Relationships - Intercompany relationships
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS company_relationships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        related_company_id INTEGER NOT NULL,
        relationship_type TEXT NOT NULL,
        relationship_subtype TEXT,
        is_active INTEGER DEFAULT 1,
        start_date DATE,
        end_date DATE,
        internal_pricing_policy TEXT,
        trade_terms TEXT,
        credit_limit REAL DEFAULT 0,
        payment_terms TEXT,
        approval_required INTEGER DEFAULT 0,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
        FOREIGN KEY (related_company_id) REFERENCES companies(id) ON DELETE CASCADE,
        UNIQUE(company_id, related_company_id, relationship_type)
    )""",

    # -------------------------------------------------------------------------
    # 6. User Company Access - User-company access control matrix
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS user_company_access (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        company_id INTEGER NOT NULL,
        branch_id INTEGER,
        facility_id INTEGER,
        role_in_company TEXT DEFAULT 'user',
        is_active INTEGER DEFAULT 1,
        is_default INTEGER DEFAULT 0,
        can_view_financials INTEGER DEFAULT 0,
        can_approve_intercompany INTEGER DEFAULT 0,
        cross_company_reporting INTEGER DEFAULT 0,
        allowed_company_ids TEXT,
        allowed_branch_ids TEXT,
        allowed_facility_ids TEXT,
        access_scope TEXT DEFAULT 'company',
        effective_from DATE,
        effective_to DATE,
        granted_by INTEGER,
        granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        revoked_by INTEGER,
        revoked_at DATETIME,
        revoke_reason TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
        FOREIGN KEY (branch_id) REFERENCES company_branches(id) ON DELETE SET NULL,
        FOREIGN KEY (facility_id) REFERENCES company_facilities(id) ON DELETE SET NULL,
        FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (revoked_by) REFERENCES users(id) ON DELETE SET NULL,
        UNIQUE(user_id, company_id)
    )""",

    # -------------------------------------------------------------------------
    # 7. Company Settings - Company-specific settings
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS company_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        setting_key TEXT NOT NULL,
        setting_value TEXT,
        setting_type TEXT DEFAULT 'text',
        category TEXT DEFAULT 'General',
        description TEXT,
        is_inherited INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
        UNIQUE(company_id, setting_key)
    )""",

    # -------------------------------------------------------------------------
    # 8. Company Numbering Rules - Company-specific document numbering
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS company_numbering_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        document_type TEXT NOT NULL,
        prefix TEXT,
        prefix_type TEXT DEFAULT 'fixed',
        sequence_length INTEGER DEFAULT 5,
        sequence_format TEXT DEFAULT 'zero_padded',
        include_year INTEGER DEFAULT 1,
        include_month INTEGER DEFAULT 0,
        include_day INTEGER DEFAULT 0,
        year_position TEXT DEFAULT 'after_prefix',
        reset_frequency TEXT DEFAULT 'yearly',
        current_sequence INTEGER DEFAULT 0,
        last_used_number TEXT,
        last_used_date DATE,
        suffix TEXT,
        separator TEXT DEFAULT '-',
        is_active INTEGER DEFAULT 1,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
        UNIQUE(company_id, document_type)
    )""",

    # -------------------------------------------------------------------------
    # 9. Company Policies - Company-specific business policies
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS company_policies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        policy_type TEXT NOT NULL,
        policy_name TEXT NOT NULL,
        policy_value TEXT,
        policy_config TEXT,
        description TEXT,
        is_active INTEGER DEFAULT 1,
        effective_from DATE,
        effective_to DATE,
        applies_to TEXT DEFAULT 'all',
        priority INTEGER DEFAULT 0,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
        UNIQUE(company_id, policy_type, policy_name)
    )""",

    # -------------------------------------------------------------------------
    # 10. Intercompany Workflows - Intercompany workflow definitions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS intercompany_workflows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workflow_code TEXT UNIQUE NOT NULL,
        workflow_name TEXT NOT NULL,
        workflow_type TEXT NOT NULL,
        description TEXT,
        source_company_id INTEGER,
        destination_company_id INTEGER,
        workflow_steps TEXT,
        approval_required INTEGER DEFAULT 1,
        auto_approve_conditions TEXT,
        is_active INTEGER DEFAULT 1,
        priority TEXT DEFAULT 'Normal',
        sla_hours INTEGER,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (source_company_id) REFERENCES companies(id) ON DELETE SET NULL,
        FOREIGN KEY (destination_company_id) REFERENCES companies(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 11. Intercompany Transactions - Intercompany transaction records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS intercompany_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_code TEXT UNIQUE NOT NULL,
        workflow_id INTEGER,
        source_company_id INTEGER NOT NULL,
        destination_company_id INTEGER NOT NULL,
        transaction_type TEXT NOT NULL,
        reference_type TEXT,
        reference_id INTEGER,
        reference_number TEXT,
        amount REAL DEFAULT 0,
        currency TEXT DEFAULT 'AED',
        exchange_rate REAL DEFAULT 1,
        base_amount REAL DEFAULT 0,
        status TEXT DEFAULT 'pending',
        priority TEXT DEFAULT 'Normal',
        requested_by INTEGER,
        requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        approved_by INTEGER,
        approved_at DATETIME,
        rejected_by INTEGER,
        rejected_at DATETIME,
        rejection_reason TEXT,
        completed_at DATETIME,
        notes TEXT,
        metadata TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workflow_id) REFERENCES intercompany_workflows(id) ON DELETE SET NULL,
        FOREIGN KEY (source_company_id) REFERENCES companies(id) ON DELETE CASCADE,
        FOREIGN KEY (destination_company_id) REFERENCES companies(id) ON DELETE CASCADE,
        FOREIGN KEY (requested_by) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (rejected_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 12. Company Audit Log - Company-level audit trail
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS company_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER,
        entity_type TEXT NOT NULL,
        entity_id INTEGER,
        entity_name TEXT,
        action TEXT NOT NULL,
        field_name TEXT,
        old_value TEXT,
        new_value TEXT,
        user_id INTEGER,
        ip_address TEXT,
        user_agent TEXT,
        reason TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 13. Shared Data Rules - Data sharing governance
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS shared_data_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_type TEXT NOT NULL,
        scope TEXT DEFAULT 'company',
        visibility TEXT DEFAULT 'private',
        sharing_policy TEXT DEFAULT 'none',
        allowed_company_ids TEXT,
        access_roles TEXT,
        is_active INTEGER DEFAULT 1,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 14. Company Notifications - Company-level notifications
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS company_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        notification_type TEXT DEFAULT 'info',
        title TEXT NOT NULL,
        message TEXT,
        severity TEXT DEFAULT 'medium',
        link_url TEXT,
        related_entity_type TEXT,
        related_entity_id INTEGER,
        is_read INTEGER DEFAULT 0,
        read_at DATETIME,
        read_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
        FOREIGN KEY (read_by) REFERENCES users(id) ON DELETE SET NULL
    )""",
]


# =============================================================================
# MIGRATION AND INITIALIZATION
# =============================================================================

def run_company_migrations():
    """
    Run all multi-company table migrations.
    Creates all company management tables if they don't exist.
    """
    conn = get_db()
    try:
        for table_sql in MULTI_COMPANY_TABLES:
            conn.executescript(table_sql)

        conn.commit()

        # Seed default data
        seed_company_defaults(conn)

        return True, "Multi-company migrations completed successfully"
    except Exception as e:
        conn.rollback()
        return False, f"Company migration error: {str(e)}"
    finally:
        conn.close()


def seed_company_defaults(conn):
    """Seed default company management data."""

    # Check if companies already exist
    existing = conn.execute("SELECT COUNT(*) as cnt FROM companies").fetchone()
    if existing['cnt'] == 0:
        return

    # Get existing companies
    companies = conn.execute("SELECT id, name FROM companies").fetchall()

    for company in companies:
        company_id = company['id']

        # Ensure company profile exists
        profile = conn.execute(
            "SELECT id FROM company_profiles WHERE company_id = ?",
            (company_id,)
        ).fetchone()

        if not profile:
            conn.execute("""
                INSERT INTO company_profiles (company_id, company_type, is_active)
                VALUES (?, 'subsidiary', 1)
            """, (company_id,))

        # Seed default settings
        default_settings = [
            (company_id, 'date_format', 'DD/MM/YYYY', 'text', 'General'),
            (company_id, 'currency', 'AED', 'text', 'General'),
            (company_id, 'timezone', 'Asia/Dubai', 'text', 'General'),
            (company_id, 'decimal_places', '2', 'number', 'General'),
            (company_id, 'thousand_separator', ',', 'text', 'General'),
        ]

        for company_id, key, value, stype, category in default_settings:
            conn.execute("""
                INSERT OR IGNORE INTO company_settings
                (company_id, setting_key, setting_value, setting_type, category)
                VALUES (?, ?, ?, ?, ?)
            """, (company_id, key, value, stype, category))

        # Seed default numbering rules
        default_numbering = [
            (company_id, 'customer', 'CUST', 'fixed', 5, 1, 0, 0),
            (company_id, 'quotation', 'QUO', 'fixed', 5, 1, 0, 0),
            (company_id, 'sales_order', 'ORD', 'fixed', 5, 1, 0, 0),
            (company_id, 'purchase_order', 'PO', 'fixed', 5, 1, 0, 0),
            (company_id, 'delivery', 'DEL', 'fixed', 5, 1, 0, 0),
            (company_id, 'invoice', 'INV', 'fixed', 5, 1, 0, 0),
            (company_id, 'employee', 'EMP', 'fixed', 5, 1, 0, 0),
        ]

        for company_id, doc_type, prefix, prefix_type, seq_len, inc_year, inc_month, inc_day in default_numbering:
            conn.execute("""
                INSERT OR IGNORE INTO company_numbering_rules
                (company_id, document_type, prefix, prefix_type, sequence_length,
                 include_year, include_month, include_day)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (company_id, doc_type, prefix, prefix_type, seq_len, inc_year, inc_month, inc_day))

        # Seed default policies
        default_policies = [
            (company_id, 'approval', 'auto_approve_threshold', '0', '{"threshold": 0}', 'Auto-approve transactions below threshold'),
            (company_id, 'credit', 'credit_check_required', 'true', None, 'Require credit check before sales'),
            (company_id, 'inventory', 'negative_stock_allowed', 'false', None, 'Allow negative stock levels'),
        ]

        for company_id, pol_type, pol_name, pol_value, pol_config, desc in default_policies:
            conn.execute("""
                INSERT OR IGNORE INTO company_policies
                (company_id, policy_type, policy_name, policy_value, policy_config, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (company_id, pol_type, pol_name, pol_value, pol_config, desc))

    # Seed shared data rules
    shared_rules = [
        ('country', 'global', 'public', 'all', None),
        ('currency', 'global', 'public', 'all', None),
        ('uom', 'global', 'public', 'all', None),
        ('customer', 'company', 'private', 'self', None),
        ('supplier', 'company', 'private', 'self', None),
        ('employee', 'company', 'private', 'self', None),
        ('item', 'shared', 'controlled', 'allowed', None),
        ('price_list', 'company', 'private', 'self', None),
        ('stock', 'company', 'private', 'self', None),
        ('order', 'company', 'private', 'self', None),
    ]

    for data_type, scope, visibility, sharing, desc in shared_rules:
        conn.execute("""
            INSERT OR IGNORE INTO shared_data_rules
            (data_type, scope, visibility, sharing_policy, description)
            VALUES (?, ?, ?, ?, ?)
        """, (data_type, scope, visibility, sharing, desc))

    conn.commit()


# =============================================================================
# COMPANY CRUD OPERATIONS
# =============================================================================

def get_all_companies(active_only: bool = True) -> List[Dict]:
    """Get all companies with their profiles."""
    conn = get_db()
    try:
        query = """
            SELECT c.*, cp.trade_name, cp.short_name, cp.company_type,
                   cp.registration_number, cp.tax_id, cp.vat_number,
                   cp.main_currency, cp.timezone, cp.is_active as profile_active,
                   pc.name as parent_company_name,
                   (SELECT COUNT(*) FROM company_branches WHERE company_id = c.id) as branch_count,
                   (SELECT COUNT(*) FROM company_facilities WHERE company_id = c.id) as facility_count,
                   (SELECT COUNT(*) FROM user_company_access WHERE company_id = c.id) as user_count
            FROM companies c
            LEFT JOIN company_profiles cp ON c.id = cp.company_id
            LEFT JOIN companies pc ON cp.parent_company_id = pc.id
        """

        if active_only:
            query += " WHERE c.is_active = 1"

        query += " ORDER BY c.name"

        return [dict(row) for row in conn.execute(query).fetchall()]
    finally:
        conn.close()


def get_company_by_id(company_id: int) -> Optional[Dict]:
    """Get a single company by ID with full profile."""
    conn = get_db()
    try:
        company = conn.execute("""
            SELECT c.*, cp.trade_name, cp.short_name, cp.company_type,
                   cp.company_type_detail, cp.registration_number, cp.tax_id,
                   cp.vat_number, cp.license_number, cp.main_currency,
                   cp.timezone, cp.date_format, cp.fiscal_year_start,
                   cp.fiscal_year_end, cp.default_language, cp.logo_path,
                   cp.primary_color, cp.secondary_color,
                   cp.address_line1, cp.address_line2, cp.city, cp.country,
                   cp.postal_code, cp.phone, cp.mobile, cp.email, cp.website,
                   cp.contact_person, cp.parent_company_id, cp.is_parent,
                   cp.notes, cp.is_active as profile_active,
                   pc.name as parent_company_name
            FROM companies c
            LEFT JOIN company_profiles cp ON c.id = cp.company_id
            LEFT JOIN companies pc ON cp.parent_company_id = pc.id
            WHERE c.id = ?
        """, (company_id,)).fetchone()

        return dict(company) if company else None
    finally:
        conn.close()


def create_company(data: Dict) -> int:
    """Create a new company with profile."""
    conn = get_db()
    try:
        # Create base company
        cursor = conn.execute("""
            INSERT INTO companies (name, is_active)
            VALUES (?, ?)
        """, (data.get('name'), data.get('is_active', 1)))
        company_id = cursor.lastrowid

        # Create company profile
        conn.execute("""
            INSERT INTO company_profiles (
                company_id, trade_name, short_name, company_type,
                company_type_detail, registration_number, tax_id, vat_number,
                license_number, main_currency, timezone, date_format,
                fiscal_year_start, fiscal_year_end, default_language,
                primary_color, secondary_color, address_line1, address_line2,
                city, country, postal_code, phone, mobile, email, website,
                contact_person, parent_company_id, is_parent, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            company_id,
            data.get('trade_name'),
            data.get('short_name'),
            data.get('company_type', 'subsidiary'),
            data.get('company_type_detail'),
            data.get('registration_number'),
            data.get('tax_id'),
            data.get('vat_number'),
            data.get('license_number'),
            data.get('main_currency', 'AED'),
            data.get('timezone', 'Asia/Dubai'),
            data.get('date_format', 'DD/MM/YYYY'),
            data.get('fiscal_year_start', 1),
            data.get('fiscal_year_end', 12),
            data.get('default_language', 'en'),
            data.get('primary_color', '#0066CC'),
            data.get('secondary_color', '#6C757D'),
            data.get('address_line1'),
            data.get('address_line2'),
            data.get('city'),
            data.get('country'),
            data.get('postal_code'),
            data.get('phone'),
            data.get('mobile'),
            data.get('email'),
            data.get('website'),
            data.get('contact_person'),
            data.get('parent_company_id'),
            data.get('is_parent', 0),
            data.get('notes')
        ))

        # Seed default settings for new company
        default_settings = [
            ('date_format', 'DD/MM/YYYY', 'text', 'General'),
            ('currency', 'AED', 'text', 'General'),
            ('timezone', 'Asia/Dubai', 'text', 'General'),
            ('decimal_places', '2', 'number', 'General'),
        ]

        for key, value, stype, category in default_settings:
            conn.execute("""
                INSERT INTO company_settings (company_id, setting_key, setting_value, setting_type, category)
                VALUES (?, ?, ?, ?, ?)
            """, (company_id, key, value, stype, category))

        # Seed default numbering rules
        default_numbering = [
            ('customer', 'CUST', 'fixed', 5, 1, 0, 0),
            ('quotation', 'QUO', 'fixed', 5, 1, 0, 0),
            ('sales_order', 'ORD', 'fixed', 5, 1, 0, 0),
            ('purchase_order', 'PO', 'fixed', 5, 1, 0, 0),
            ('delivery', 'DEL', 'fixed', 5, 1, 0, 0),
            ('invoice', 'INV', 'fixed', 5, 1, 0, 0),
            ('employee', 'EMP', 'fixed', 5, 1, 0, 0),
        ]

        for doc_type, prefix, prefix_type, seq_len, inc_year, inc_month, inc_day in default_numbering:
            conn.execute("""
                INSERT INTO company_numbering_rules
                (company_id, document_type, prefix, prefix_type, sequence_length,
                 include_year, include_month, include_day)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (company_id, doc_type, prefix, prefix_type, seq_len, inc_year, inc_month, inc_day))

        conn.commit()
        return company_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_company(company_id: int, data: Dict) -> bool:
    """Update company and its profile."""
    conn = get_db()
    try:
        # Update base company
        if 'name' in data:
            conn.execute("UPDATE companies SET name = ? WHERE id = ?",
                        (data['name'], company_id))

        # Update profile
        profile_fields = [
            'trade_name', 'short_name', 'company_type', 'company_type_detail',
            'registration_number', 'tax_id', 'vat_number', 'license_number',
            'main_currency', 'timezone', 'date_format', 'fiscal_year_start',
            'fiscal_year_end', 'default_language', 'logo_path', 'primary_color',
            'secondary_color', 'address_line1', 'address_line2', 'city',
            'country', 'postal_code', 'phone', 'mobile', 'email', 'website',
            'contact_person', 'parent_company_id', 'is_parent', 'notes', 'is_active'
        ]

        updates = []
        params = []
        for field in profile_fields:
            if field in data:
                updates.append(f"{field} = ?")
                params.append(data[field])

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(company_id)
            conn.execute(f"""
                UPDATE company_profiles SET {', '.join(updates)}
                WHERE company_id = ?
            """, params)

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# =============================================================================
# BRANCH OPERATIONS
# =============================================================================

def get_company_branches(company_id: int, active_only: bool = True) -> List[Dict]:
    """Get all branches for a company."""
    conn = get_db()
    try:
        query = """
            SELECT cb.*,
                   (SELECT COUNT(*) FROM company_facilities WHERE branch_id = cb.id) as facility_count
            FROM company_branches cb
            WHERE cb.company_id = ?
        """

        if active_only:
            query += " AND cb.is_active = 1"

        query += " ORDER BY cb.branch_name"

        return [dict(row) for row in conn.execute(query, (company_id,)).fetchall()]
    finally:
        conn.close()


def get_branch_by_id(branch_id: int) -> Optional[Dict]:
    """Get a single branch by ID."""
    conn = get_db()
    try:
        branch = conn.execute("""
            SELECT cb.*, c.name as company_name
            FROM company_branches cb
            JOIN companies c ON cb.company_id = c.id
            WHERE cb.id = ?
        """, (branch_id,)).fetchone()

        if branch:
            result = dict(branch)
            result['facilities'] = [dict(r) for r in conn.execute("""
                SELECT * FROM company_facilities WHERE branch_id = ? ORDER BY facility_name
            """, (branch_id,)).fetchall()]
            return result

        return None
    finally:
        conn.close()


def create_branch(data: Dict) -> int:
    """Create a new branch."""
    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO company_branches (
                company_id, branch_code, branch_name, branch_type,
                description, address, city, country, postal_code,
                phone, email, manager_name, manager_contact,
                is_active, is_operational, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('company_id'),
            data.get('branch_code'),
            data.get('branch_name'),
            data.get('branch_type', 'branch'),
            data.get('description'),
            data.get('address'),
            data.get('city'),
            data.get('country'),
            data.get('postal_code'),
            data.get('phone'),
            data.get('email'),
            data.get('manager_name'),
            data.get('manager_contact'),
            data.get('is_active', 1),
            data.get('is_operational', 1),
            data.get('notes')
        ))
        conn.commit()
        return cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_branch(branch_id: int, data: Dict) -> bool:
    """Update a branch."""
    conn = get_db()
    try:
        fields = [
            'branch_name', 'branch_type', 'description', 'address', 'city',
            'country', 'postal_code', 'phone', 'email', 'manager_name',
            'manager_contact', 'is_active', 'is_operational', 'notes'
        ]

        updates = []
        params = []
        for field in fields:
            if field in data:
                updates.append(f"{field} = ?")
                params.append(data[field])

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(branch_id)
            conn.execute(f"""
                UPDATE company_branches SET {', '.join(updates)}
                WHERE id = ?
            """, params)

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# =============================================================================
# FACILITY OPERATIONS
# =============================================================================

def get_company_facilities(company_id: int = None, branch_id: int = None,
                           active_only: bool = True) -> List[Dict]:
    """Get facilities with optional filters."""
    conn = get_db()
    try:
        query = """
            SELECT cf.*, cb.branch_name, c.name as company_name
            FROM company_facilities cf
            LEFT JOIN company_branches cb ON cf.branch_id = cb.id
            JOIN companies c ON cf.company_id = c.id
            WHERE 1=1
        """
        params = []

        if company_id:
            query += " AND cf.company_id = ?"
            params.append(company_id)

        if branch_id:
            query += " AND cf.branch_id = ?"
            params.append(branch_id)

        if active_only:
            query += " AND cf.is_active = 1"

        query += " ORDER BY cf.facility_name"

        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def get_facility_by_id(facility_id: int) -> Optional[Dict]:
    """Get a single facility by ID."""
    conn = get_db()
    try:
        facility = conn.execute("""
            SELECT cf.*, cb.branch_name, c.name as company_name
            FROM company_facilities cf
            LEFT JOIN company_branches cb ON cf.branch_id = cb.id
            JOIN companies c ON cf.company_id = c.id
            WHERE cf.id = ?
        """, (facility_id,)).fetchone()
        return dict(facility) if facility else None
    finally:
        conn.close()


def create_facility(data: Dict) -> int:
    """Create a new facility."""
    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO company_facilities (
                facility_code, facility_name, company_id, branch_id,
                facility_type, facility_subtype, address, city, country,
                postal_code, phone, email, manager_name, manager_contact,
                capacity_sqm, capacity_pallets, is_active, is_shared,
                shared_with_companies, operational_hours, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('facility_code'),
            data.get('facility_name'),
            data.get('company_id'),
            data.get('branch_id'),
            data.get('facility_type'),
            data.get('facility_subtype'),
            data.get('address'),
            data.get('city'),
            data.get('country'),
            data.get('postal_code'),
            data.get('phone'),
            data.get('email'),
            data.get('manager_name'),
            data.get('manager_contact'),
            data.get('capacity_sqm'),
            data.get('capacity_pallets'),
            data.get('is_active', 1),
            data.get('is_shared', 0),
            data.get('shared_with_companies'),
            data.get('operational_hours'),
            data.get('notes')
        ))
        conn.commit()
        return cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# =============================================================================
# USER-COMPANY ACCESS OPERATIONS
# =============================================================================

def get_user_companies(user_id: int, active_only: bool = True) -> List[Dict]:
    """Get all companies a user has access to."""
    conn = get_db()
    try:
        query = """
            SELECT c.*, uca.role_in_company, uca.is_default, uca.access_scope,
                   uca.can_view_financials, uca.cross_company_reporting,
                   uca.branch_id, uca.facility_id,
                   cb.branch_name, cf.facility_name
            FROM user_company_access uca
            JOIN companies c ON uca.company_id = c.id
            LEFT JOIN company_branches cb ON uca.branch_id = cb.id
            LEFT JOIN company_facilities cf ON uca.facility_id = cf.id
            WHERE uca.user_id = ?
        """

        if active_only:
            query += " AND uca.is_active = 1 AND c.is_active = 1"

        query += " ORDER BY uca.is_default DESC, c.name"

        return [dict(row) for row in conn.execute(query, (user_id,)).fetchall()]
    finally:
        conn.close()


def get_user_default_company(user_id: int) -> Optional[Dict]:
    """Get user's default company."""
    conn = get_db()
    try:
        result = conn.execute("""
            SELECT c.*, uca.role_in_company, uca.access_scope
            FROM user_company_access uca
            JOIN companies c ON uca.company_id = c.id
            WHERE uca.user_id = ? AND uca.is_default = 1 AND uca.is_active = 1
        """, (user_id,)).fetchone()

        return dict(result) if result else None
    finally:
        conn.close()


def assign_user_to_company(data: Dict, granted_by: int = None) -> int:
    """Assign a user to a company with specific access."""
    conn = get_db()
    try:
        # If this is set as default, unset other defaults for this user
        if data.get('is_default'):
            conn.execute("""
                UPDATE user_company_access SET is_default = 0
                WHERE user_id = ? AND is_default = 1
            """, (data['user_id'],))

        cursor = conn.execute("""
            INSERT INTO user_company_access (
                user_id, company_id, branch_id, facility_id,
                role_in_company, is_active, is_default,
                can_view_financials, can_approve_intercompany,
                cross_company_reporting, allowed_company_ids,
                allowed_branch_ids, allowed_facility_ids,
                access_scope, effective_from, effective_to,
                granted_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('user_id'),
            data.get('company_id'),
            data.get('branch_id'),
            data.get('facility_id'),
            data.get('role_in_company', 'user'),
            data.get('is_active', 1),
            data.get('is_default', 0),
            data.get('can_view_financials', 0),
            data.get('can_approve_intercompany', 0),
            data.get('cross_company_reporting', 0),
            data.get('allowed_company_ids'),
            data.get('allowed_branch_ids'),
            data.get('allowed_facility_ids'),
            data.get('access_scope', 'company'),
            data.get('effective_from'),
            data.get('effective_to'),
            granted_by
        ))
        conn.commit()
        return cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_user_company_access(access_id: int, data: Dict) -> bool:
    """Update user company access."""
    conn = get_db()
    try:
        if data.get('is_default'):
            access = conn.execute("SELECT user_id FROM user_company_access WHERE id = ?",
                                 (access_id,)).fetchone()
            if access:
                conn.execute("""
                    UPDATE user_company_access SET is_default = 0
                    WHERE user_id = ? AND is_default = 1 AND id != ?
                """, (access['user_id'], access_id))

        fields = [
            'branch_id', 'facility_id', 'role_in_company', 'is_active',
            'is_default', 'can_view_financials', 'can_approve_intercompany',
            'cross_company_reporting', 'allowed_company_ids',
            'allowed_branch_ids', 'allowed_facility_ids', 'access_scope',
            'effective_from', 'effective_to'
        ]

        updates = []
        params = []
        for field in fields:
            if field in data:
                updates.append(f"{field} = ?")
                params.append(data[field])

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(access_id)
            conn.execute(f"""
                UPDATE user_company_access SET {', '.join(updates)}
                WHERE id = ?
            """, params)

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def revoke_user_company_access(access_id: int, revoked_by: int, reason: str = None) -> bool:
    """Revoke a user's company access."""
    conn = get_db()
    try:
        conn.execute("""
            UPDATE user_company_access
            SET is_active = 0, revoked_by = ?, revoked_at = CURRENT_TIMESTAMP, revoke_reason = ?
            WHERE id = ?
        """, (revoked_by, reason, access_id))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def user_has_company_access(user_id: int, company_id: int) -> bool:
    """Check if user has access to a specific company."""
    conn = get_db()
    try:
        result = conn.execute("""
            SELECT 1 FROM user_company_access
            WHERE user_id = ? AND company_id = ? AND is_active = 1
            LIMIT 1
        """, (user_id, company_id)).fetchone()
        return result is not None
    finally:
        conn.close()


def user_can_access_company_data(user_id: int, company_id: int, data_scope: str = 'company') -> bool:
    """
    Check if user can access data for a specific company.
    Handles cross-company access scenarios.
    """
    conn = get_db()
    try:
        # Get user's access record for this company
        access = conn.execute("""
            SELECT * FROM user_company_access
            WHERE user_id = ? AND company_id = ? AND is_active = 1
        """, (user_id, company_id)).fetchone()

        if not access:
            return False

        # If access_scope is 'all' or 'allowed', they can access
        if access['access_scope'] in ('all', 'allowed'):
            return True

        # If specific scope, check if company_id matches
        return access['company_id'] == company_id
    finally:
        conn.close()


# =============================================================================
# COMPANY SETTINGS OPERATIONS
# =============================================================================

def get_company_settings(company_id: int, category: str = None) -> Dict:
    """Get all settings for a company."""
    conn = get_db()
    try:
        query = """
            SELECT setting_key, setting_value, setting_type, category, description
            FROM company_settings
            WHERE company_id = ? AND is_active = 1
        """
        params = [company_id]

        if category:
            query += " AND category = ?"
            params.append(category)

        settings = {row['setting_key']: row['setting_value']
                   for row in conn.execute(query, params).fetchall()}

        # Get global defaults for missing keys
        from database import get_platform_setting
        for key in ['date_format', 'currency', 'timezone']:
            if key not in settings:
                settings[key] = get_platform_setting(key, 'AED' if key == 'currency' else 'DD/MM/YYYY' if key == 'date_format' else 'Asia/Dubai')

        return settings
    finally:
        conn.close()


def get_company_setting(company_id: int, key: str, default: str = None) -> str:
    """Get a specific company setting."""
    conn = get_db()
    try:
        result = conn.execute("""
            SELECT setting_value FROM company_settings
            WHERE company_id = ? AND setting_key = ? AND is_active = 1
        """, (company_id, key)).fetchone()

        if result:
            return result['setting_value']

        # Fall back to global setting
        from database import get_platform_setting
        return get_platform_setting(key, default)
    finally:
        conn.close()


def update_company_setting(company_id: int, key: str, value: str,
                          setting_type: str = 'text', category: str = 'General') -> bool:
    """Update or create a company setting."""
    conn = get_db()
    try:
        existing = conn.execute("""
            SELECT id FROM company_settings
            WHERE company_id = ? AND setting_key = ?
        """, (company_id, key)).fetchone()

        if existing:
            conn.execute("""
                UPDATE company_settings
                SET setting_value = ?, setting_type = ?, category = ?, updated_at = CURRENT_TIMESTAMP
                WHERE company_id = ? AND setting_key = ?
            """, (value, setting_type, category, company_id, key))
        else:
            conn.execute("""
                INSERT INTO company_settings
                (company_id, setting_key, setting_value, setting_type, category)
                VALUES (?, ?, ?, ?, ?)
            """, (company_id, key, value, setting_type, category))

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# =============================================================================
# NUMBERING RULES OPERATIONS
# =============================================================================

def get_numbering_rules(company_id: int) -> List[Dict]:
    """Get all numbering rules for a company."""
    conn = get_db()
    try:
        return [dict(row) for row in conn.execute("""
            SELECT * FROM company_numbering_rules
            WHERE company_id = ? AND is_active = 1
            ORDER BY document_type
        """, (company_id,)).fetchall()]
    finally:
        conn.close()


def get_next_document_number(company_id: int, document_type: str) -> str:
    """Generate the next document number based on company rules."""
    conn = get_db()
    try:
        rule = conn.execute("""
            SELECT * FROM company_numbering_rules
            WHERE company_id = ? AND document_type = ? AND is_active = 1
        """, (company_id, document_type)).fetchone()

        if not rule:
            # No rule, use simple format
            year = datetime.now().year
            return f"{document_type.upper()}-{year}-00001"

        # Increment sequence
        new_sequence = rule['current_sequence'] + 1
        conn.execute("""
            UPDATE company_numbering_rules
            SET current_sequence = ?, last_used_date = CURRENT_DATE
            WHERE company_id = ? AND document_type = ?
        """, (new_sequence, company_id, document_type))
        conn.commit()

        # Build the number
        prefix = rule['prefix'] or document_type.upper()
        sep = rule['separator'] or '-'
        seq_len = rule['sequence_length'] or 5
        seq_str = str(new_sequence).zfill(seq_len)

        if rule['include_year']:
            year = datetime.now().year
            if rule['year_position'] == 'before_prefix':
                return f"{year}{sep}{prefix}{sep}{seq_str}"
            else:
                prefix = f"{prefix}{sep}{year}"

        if rule['include_month']:
            month = datetime.now().month
            prefix = f"{prefix}{sep}{month:02d}"

        if rule['include_day']:
            day = datetime.now().day
            prefix = f"{prefix}{sep}{day:02d}"

        return f"{prefix}{sep}{seq_str}"
    finally:
        conn.close()


# =============================================================================
# COMPANY RELATIONSHIPS
# =============================================================================

def get_company_relationships(company_id: int, relationship_type: str = None) -> List[Dict]:
    """Get all relationships for a company."""
    conn = get_db()
    try:
        query = """
            SELECT cr.*,
                   c1.name as company_name,
                   c2.name as related_company_name
            FROM company_relationships cr
            JOIN companies c1 ON cr.company_id = c1.id
            JOIN companies c2 ON cr.related_company_id = c2.id
            WHERE cr.company_id = ? AND cr.is_active = 1
        """
        params = [company_id]

        if relationship_type:
            query += " AND cr.relationship_type = ?"
            params.append(relationship_type)

        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def create_company_relationship(data: Dict) -> int:
    """Create a new company relationship."""
    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO company_relationships (
                company_id, related_company_id, relationship_type,
                relationship_subtype, is_active, start_date, end_date,
                internal_pricing_policy, trade_terms, credit_limit,
                payment_terms, approval_required, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('company_id'),
            data.get('related_company_id'),
            data.get('relationship_type'),
            data.get('relationship_subtype'),
            data.get('is_active', 1),
            data.get('start_date'),
            data.get('end_date'),
            data.get('internal_pricing_policy'),
            data.get('trade_terms'),
            data.get('credit_limit', 0),
            data.get('payment_terms'),
            data.get('approval_required', 0),
            data.get('notes')
        ))
        conn.commit()
        return cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# =============================================================================
# INTERCOMPANY WORKFLOWS
# =============================================================================

def get_intercompany_workflows(company_id: int = None, workflow_type: str = None) -> List[Dict]:
    """Get intercompany workflows."""
    conn = get_db()
    try:
        query = """
            SELECT iw.*,
                   c1.name as source_company_name,
                   c2.name as destination_company_name
            FROM intercompany_workflows iw
            LEFT JOIN companies c1 ON iw.source_company_id = c1.id
            LEFT JOIN companies c2 ON iw.destination_company_id = c2.id
            WHERE iw.is_active = 1
        """
        params = []

        if company_id:
            query += " AND (iw.source_company_id = ? OR iw.destination_company_id = ?)"
            params.extend([company_id, company_id])

        if workflow_type:
            query += " AND iw.workflow_type = ?"
            params.append(workflow_type)

        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def create_intercompany_transaction(data: Dict) -> int:
    """Create a new intercompany transaction."""
    conn = get_db()
    try:
        # Generate transaction code
        year = datetime.now().year
        last = conn.execute("""
            SELECT transaction_code FROM intercompany_transactions
            WHERE transaction_code LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f'ICT-{year}%',)).fetchone()

        if last:
            last_num = int(last['transaction_code'].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        txn_code = f"ICT-{year}-{new_num:05d}"

        cursor = conn.execute("""
            INSERT INTO intercompany_transactions (
                transaction_code, workflow_id, source_company_id,
                destination_company_id, transaction_type, reference_type,
                reference_id, reference_number, amount, currency,
                exchange_rate, base_amount, status, priority,
                requested_by, notes, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            txn_code,
            data.get('workflow_id'),
            data.get('source_company_id'),
            data.get('destination_company_id'),
            data.get('transaction_type'),
            data.get('reference_type'),
            data.get('reference_id'),
            data.get('reference_number'),
            data.get('amount', 0),
            data.get('currency', 'AED'),
            data.get('exchange_rate', 1),
            data.get('base_amount', 0),
            data.get('status', 'pending'),
            data.get('priority', 'Normal'),
            data.get('requested_by'),
            data.get('notes'),
            data.get('metadata')
        ))
        conn.commit()
        return cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_intercompany_transactions(company_id: int = None, status: str = None) -> List[Dict]:
    """Get intercompany transactions."""
    conn = get_db()
    try:
        query = """
            SELECT ict.*,
                   c1.name as source_company_name,
                   c2.name as destination_company_name,
                   u1.username as requested_by_name,
                   u2.username as approved_by_name
            FROM intercompany_transactions ict
            JOIN companies c1 ON ict.source_company_id = c1.id
            JOIN companies c2 ON ict.destination_company_id = c2.id
            LEFT JOIN users u1 ON ict.requested_by = u1.id
            LEFT JOIN users u2 ON ict.approved_by = u2.id
            WHERE 1=1
        """
        params = []

        if company_id:
            query += " AND (ict.source_company_id = ? OR ict.destination_company_id = ?)"
            params.extend([company_id, company_id])

        if status:
            query += " AND ict.status = ?"
            params.append(status)

        query += " ORDER BY ict.created_at DESC"

        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def update_transaction_status(transaction_id: int, status: str,
                               user_id: int, reason: str = None) -> bool:
    """Update intercompany transaction status."""
    conn = get_db()
    try:
        if status == 'approved':
            conn.execute("""
                UPDATE intercompany_transactions
                SET status = ?, approved_by = ?, approved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, user_id, transaction_id))
        elif status == 'rejected':
            conn.execute("""
                UPDATE intercompany_transactions
                SET status = ?, rejected_by = ?, rejected_at = CURRENT_TIMESTAMP, rejection_reason = ?
                WHERE id = ?
            """, (status, user_id, reason, transaction_id))
        elif status == 'completed':
            conn.execute("""
                UPDATE intercompany_transactions
                SET status = ?, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, transaction_id))
        else:
            conn.execute("""
                UPDATE intercompany_transactions
                SET status = ?
                WHERE id = ?
            """, (status, transaction_id))

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# =============================================================================
# COMPANY POLICIES
# =============================================================================

def get_company_policies(company_id: int, policy_type: str = None) -> List[Dict]:
    """Get all policies for a company."""
    conn = get_db()
    try:
        query = """
            SELECT * FROM company_policies
            WHERE company_id = ? AND is_active = 1
        """
        params = [company_id]

        if policy_type:
            query += " AND policy_type = ?"
            params.append(policy_type)

        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def get_policy_value(company_id: int, policy_type: str, policy_name: str, default: str = None) -> str:
    """Get a specific policy value."""
    conn = get_db()
    try:
        result = conn.execute("""
            SELECT policy_value FROM company_policies
            WHERE company_id = ? AND policy_type = ? AND policy_name = ?
            AND is_active = 1 AND (effective_from IS NULL OR effective_from <= CURRENT_DATE)
            AND (effective_to IS NULL OR effective_to >= CURRENT_DATE)
        """, (company_id, policy_type, policy_name)).fetchone()
        return result['policy_value'] if result else default
    finally:
        conn.close()


# =============================================================================
# COMPANY AUDIT LOG
# =============================================================================

def log_company_audit(company_id: int, entity_type: str, entity_id: int,
                      entity_name: str, action: str, user_id: int = None,
                      field_name: str = None, old_value: str = None,
                      new_value: str = None, reason: str = None,
                      ip_address: str = None, notes: str = None) -> int:
    """Log a company-level audit entry."""
    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO company_audit_log (
                company_id, entity_type, entity_id, entity_name, action,
                field_name, old_value, new_value, user_id, reason, ip_address, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (company_id, entity_type, entity_id, entity_name, action,
              field_name, old_value, new_value, user_id, reason, ip_address, notes))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_company_audit_log(company_id: int, entity_type: str = None,
                          user_id: int = None, limit: int = 100) -> List[Dict]:
    """Get company audit log entries."""
    conn = get_db()
    try:
        query = """
            SELECT cal.*, u.username as user_name
            FROM company_audit_log cal
            LEFT JOIN users u ON cal.user_id = u.id
            WHERE cal.company_id = ?
        """
        params = [company_id]

        if entity_type:
            query += " AND cal.entity_type = ?"
            params.append(entity_type)

        if user_id:
            query += " AND cal.user_id = ?"
            params.append(user_id)

        query += " ORDER BY cal.created_at DESC LIMIT ?"
        params.append(limit)

        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


# =============================================================================
# SHARED DATA RULES
# =============================================================================

def get_shared_data_rules(data_type: str = None) -> List[Dict]:
    """Get shared data governance rules."""
    conn = get_db()
    try:
        query = "SELECT * FROM shared_data_rules WHERE is_active = 1"
        params = []

        if data_type:
            query += " AND data_type = ?"
            params.append(data_type)

        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def get_data_visibility(data_type: str, company_id: int) -> Dict:
    """Get data visibility rules for a specific data type and company."""
    conn = get_db()
    try:
        rule = conn.execute("""
            SELECT * FROM shared_data_rules
            WHERE data_type = ? AND is_active = 1
        """, (data_type,)).fetchone()

        if not rule:
            return {'scope': 'company', 'visibility': 'private', 'sharing_policy': 'none'}

        result = dict(rule)

        # Determine if company is allowed based on sharing policy
        if result['sharing_policy'] == 'all':
            result['can_access'] = True
        elif result['sharing_policy'] == 'allowed' and result['allowed_company_ids']:
            allowed = [int(x) for x in result['allowed_company_ids'].split(',')]
            result['can_access'] = company_id in allowed
        elif result['sharing_policy'] == 'none':
            result['can_access'] = False
        else:
            result['can_access'] = result['scope'] in ('global', 'shared')

        return result
    finally:
        conn.close()


# =============================================================================
# COMPANY STATISTICS AND DASHBOARD
# =============================================================================

def get_company_dashboard_stats(company_id: int = None) -> Dict:
    """Get company-level statistics for dashboard."""
    conn = get_db()
    try:
        stats = {}

        # Overall company counts
        stats['total_companies'] = conn.execute(
            "SELECT COUNT(*) as cnt FROM companies WHERE is_active = 1"
        ).fetchone()['cnt']

        stats['total_branches'] = conn.execute(
            "SELECT COUNT(*) as cnt FROM company_branches WHERE is_active = 1"
        ).fetchone()['cnt']

        stats['total_facilities'] = conn.execute(
            "SELECT COUNT(*) as cnt FROM company_facilities WHERE is_active = 1"
        ).fetchone()['cnt']

        stats['active_users'] = conn.execute(
            "SELECT COUNT(DISTINCT user_id) as cnt FROM user_company_access WHERE is_active = 1"
        ).fetchone()['cnt']

        stats['pending_intercompany'] = conn.execute(
            "SELECT COUNT(*) as cnt FROM intercompany_transactions WHERE status = 'pending'"
        ).fetchone()['cnt']

        # Per-company breakdown if no specific company
        if not company_id:
            stats['by_company'] = [dict(row) for row in conn.execute("""
                SELECT c.id, c.name,
                       COUNT(DISTINCT cb.id) as branches,
                       COUNT(DISTINCT cf.id) as facilities,
                       COUNT(DISTINCT uca.user_id) as users
                FROM companies c
                LEFT JOIN company_branches cb ON c.id = cb.company_id AND cb.is_active = 1
                LEFT JOIN company_facilities cf ON c.id = cf.company_id AND cf.is_active = 1
                LEFT JOIN user_company_access uca ON c.id = uca.company_id AND uca.is_active = 1
                WHERE c.is_active = 1
                GROUP BY c.id
                ORDER BY c.name
            """).fetchall()]
        else:
            # Specific company stats
            stats['company'] = get_company_by_id(company_id)
            stats['branches'] = get_company_branches(company_id)
            stats['facilities'] = get_company_facilities(company_id)
            stats['relationships'] = get_company_relationships(company_id)
            stats['pending_transactions'] = [dict(row) for row in conn.execute("""
                SELECT * FROM intercompany_transactions
                WHERE (source_company_id = ? OR destination_company_id = ?)
                AND status = 'pending'
                ORDER BY created_at DESC
            """, (company_id, company_id)).fetchall()]

        return stats
    finally:
        conn.close()


def get_company_hierarchy(company_id: int = None) -> Dict:
    """Get complete company hierarchy."""
    conn = get_db()
    try:
        if company_id:
            # Get specific company with all related entities
            company = get_company_by_id(company_id)
            if not company:
                return None

            company['branches'] = get_company_branches(company_id)
            for branch in company['branches']:
                branch['facilities'] = get_company_facilities(branch_id=branch['id'])

            return company
        else:
            # Get all companies with hierarchy
            companies = get_all_companies()
            for company in companies:
                company['branches'] = get_company_branches(company['id'])
                for branch in company['branches']:
                    branch['facilities'] = get_company_facilities(branch_id=branch['id'])

            return companies
    finally:
        conn.close()


if __name__ == '__main__':
    success, message = run_company_migrations()
    print(message)
