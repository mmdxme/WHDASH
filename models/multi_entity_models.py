"""
Multi-Entity Management System - Data Models
=============================================
Comprehensive data models for enterprise multi-entity management including:
- Groups/Holdings
- Legal Entities
- Branches/Operating Units
- Sites/Warehouses/Offices
- Entity Relationships
- Shared Master Data Rules
- Intercompany Rules
- Entity Scoping & Access Control
- Entity Numbering Schemes
- Entity Audit & Change Tracking

This module provides a complete platform-wide scoping and governance layer.

Usage:
    from multi_entity_models import (
        run_migrations,
        # Groups
        get_all_groups, get_group_by_id, create_group, update_group, archive_group,
        # Legal Entities
        get_all_entities, get_entity_by_id, create_entity, update_entity, archive_entity,
        # Branches
        get_entity_branches, get_branch_by_id, create_branch, update_branch,
        # Sites
        get_branch_sites, get_site_by_id, create_site, update_site,
        # Relationships
        get_entity_relationships, create_relationship,
        # Access Control
        get_entity_access, assign_entity_access, update_access_scope,
        # Scoping
        get_user_entity_scope, set_user_entity_context, get_current_entity_context,
        # Numbering
        get_numbering_schemes, get_next_entity_number,
        # Intercompany
        get_intercompany_rules, create_intercompany_rule,
        # Shared Data
        get_shared_data_rules, update_shared_data_rule,
        # Audit
        log_entity_audit, get_entity_audit_log,
        # Settings
        get_entity_settings, update_entity_setting,
        # Dashboards
        get_entity_dashboard_stats
    )
"""

import sqlite3
import os
import json
from datetime import datetime
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
# MULTI-ENTITY TABLE DEFINITIONS
# =============================================================================

MULTI_ENTITY_TABLES = [
    # -------------------------------------------------------------------------
    # 1. Entity Groups (Holdings/Parent Organizations)
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS entity_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_code TEXT UNIQUE NOT NULL,
        legal_name TEXT NOT NULL,
        trade_name TEXT,
        short_name TEXT,
        group_type TEXT DEFAULT 'holding',
        registration_number TEXT,
        tax_identification TEXT,
        vat_number TEXT,
        country TEXT DEFAULT 'UAE',
        state_region TEXT,
        city TEXT,
        address_line1 TEXT,
        address_line2 TEXT,
        postal_code TEXT,
        phone TEXT,
        mobile TEXT,
        email TEXT,
        website TEXT,
        default_currency TEXT DEFAULT 'AED',
        fiscal_year_start INTEGER DEFAULT 1,
        fiscal_year_end INTEGER DEFAULT 12,
        base_language TEXT DEFAULT 'en',
        logo_path TEXT,
        primary_color TEXT,
        secondary_color TEXT,
        ownership_structure TEXT,
        parent_group_id INTEGER,
        is_active INTEGER DEFAULT 1,
        is_verified INTEGER DEFAULT 0,
        notes TEXT,
        metadata TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        archived_at DATETIME,
        archived_by INTEGER,
        FOREIGN KEY (parent_group_id) REFERENCES entity_groups(id) ON DELETE SET NULL,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (archived_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 2. Legal Entities
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS legal_entities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_code TEXT UNIQUE NOT NULL,
        legal_name TEXT NOT NULL,
        short_name TEXT,
        trade_name TEXT,
        entity_type TEXT NOT NULL DEFAULT 'subsidiary',
        business_type TEXT,
        registration_number TEXT,
        tax_identification TEXT,
        vat_number TEXT,
        excise_tax_number TEXT,
        customs_code TEXT,
        chamber_of_commerce_number TEXT,
        license_number TEXT,
        license_type TEXT,
        license_expiry DATE,
        country TEXT NOT NULL DEFAULT 'UAE',
        state_region TEXT,
        city TEXT,
        district TEXT,
        address_line1 TEXT,
        address_line2 TEXT,
        postal_code TEXT,
        google_maps_url TEXT,
        phone TEXT,
        mobile TEXT,
        fax TEXT,
        email TEXT,
        website TEXT,
        default_currency TEXT DEFAULT 'AED',
        secondary_currency TEXT,
        timezone TEXT DEFAULT 'Asia/Dubai',
        date_format TEXT DEFAULT 'DD/MM/YYYY',
        fiscal_year_start INTEGER DEFAULT 1,
        fiscal_year_end INTEGER DEFAULT 12,
        base_language TEXT DEFAULT 'en',
        ownership_percentage REAL DEFAULT 100,
        parent_entity_id INTEGER,
        parent_group_id INTEGER,
        intercompany_partner_code TEXT,
        consolidation_flag INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1,
        is_verified INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        primary_contact_name TEXT,
        primary_contact_phone TEXT,
        primary_contact_email TEXT,
        finance_contact_name TEXT,
        finance_contact_email TEXT,
        logo_path TEXT,
        document_prefix TEXT,
        notes TEXT,
        metadata TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        archived_at DATETIME,
        archived_by INTEGER,
        FOREIGN KEY (parent_entity_id) REFERENCES legal_entities(id) ON DELETE SET NULL,
        FOREIGN KEY (parent_group_id) REFERENCES entity_groups(id) ON DELETE SET NULL,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (archived_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 3. Entity Branches (Operating Units)
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS entity_branches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_id INTEGER NOT NULL,
        branch_code TEXT UNIQUE NOT NULL,
        branch_name TEXT NOT NULL,
        short_name TEXT,
        branch_type TEXT NOT NULL DEFAULT 'branch_office',
        branch_category TEXT,
        description TEXT,
        is_head_office INTEGER DEFAULT 0,
        is_operational INTEGER DEFAULT 1,
        contact_name TEXT,
        contact_phone TEXT,
        contact_email TEXT,
        contact_position TEXT,
        address_line1 TEXT,
        address_line2 TEXT,
        city TEXT,
        district TEXT,
        country TEXT,
        postal_code TEXT,
        phone TEXT,
        phone2 TEXT,
        mobile TEXT,
        fax TEXT,
        email TEXT,
        default_warehouse_id INTEGER,
        default_document_prefix TEXT,
        approvals_owner_id INTEGER,
        finance_posting_rules TEXT,
        local_timezone TEXT,
        local_language TEXT,
        operational_hours TEXT,
        is_active INTEGER DEFAULT 1,
        is_verified INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        notes TEXT,
        metadata TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        archived_at DATETIME,
        archived_by INTEGER,
        FOREIGN KEY (entity_id) REFERENCES legal_entities(id) ON DELETE CASCADE,
        FOREIGN KEY (approvals_owner_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (archived_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 4. Entity Sites (Warehouses, Offices, etc.)
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS entity_sites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_id INTEGER NOT NULL,
        branch_id INTEGER,
        site_code TEXT UNIQUE NOT NULL,
        site_name TEXT NOT NULL,
        short_name TEXT,
        site_type TEXT NOT NULL,
        site_subtype TEXT,
        description TEXT,
        address_line1 TEXT,
        address_line2 TEXT,
        city TEXT,
        district TEXT,
        country TEXT,
        postal_code TEXT,
        google_maps_url TEXT,
        phone TEXT,
        mobile TEXT,
        fax TEXT,
        email TEXT,
        contact_name TEXT,
        contact_position TEXT,
        contact_phone TEXT,
        contact_email TEXT,
        responsible_person_id INTEGER,
        site_area_sqm REAL,
        covered_area_sqm REAL,
        yard_area_sqm REAL,
        capacity_pallets INTEGER,
        capacity_items INTEGER,
        is_shared INTEGER DEFAULT 0,
        shared_with_entities TEXT,
        operational_hours TEXT,
        working_days TEXT,
        is_operational INTEGER DEFAULT 1,
        is_verified INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        site_manager_name TEXT,
        site_manager_phone TEXT,
        site_manager_email TEXT,
        notes TEXT,
        metadata TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        archived_at DATETIME,
        archived_by INTEGER,
        FOREIGN KEY (entity_id) REFERENCES legal_entities(id) ON DELETE CASCADE,
        FOREIGN KEY (branch_id) REFERENCES entity_branches(id) ON DELETE SET NULL,
        FOREIGN KEY (responsible_person_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (archived_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 5. Entity Relationships
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS entity_relationships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_entity_id INTEGER NOT NULL,
        target_entity_id INTEGER NOT NULL,
        relationship_type TEXT NOT NULL,
        relationship_subtype TEXT,
        ownership_percentage REAL,
        effective_date DATE,
        end_date DATE,
        is_active INTEGER DEFAULT 1,
        is_verified INTEGER DEFAULT 0,
        approval_required INTEGER DEFAULT 0,
        internal_pricing_policy TEXT,
        trade_terms TEXT,
        credit_limit REAL DEFAULT 0,
        payment_terms TEXT,
        notes TEXT,
        metadata TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        archived_at DATETIME,
        archived_by INTEGER,
        FOREIGN KEY (source_entity_id) REFERENCES legal_entities(id) ON DELETE CASCADE,
        FOREIGN KEY (target_entity_id) REFERENCES legal_entities(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (archived_by) REFERENCES users(id) ON DELETE SET NULL,
        UNIQUE(source_entity_id, target_entity_id, relationship_type)
    )""",

    # -------------------------------------------------------------------------
    # 6. Entity Access Assignments (User-Entity Scoping)
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS entity_access (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        entity_id INTEGER,
        branch_id INTEGER,
        site_id INTEGER,
        group_id INTEGER,
        access_level TEXT NOT NULL DEFAULT 'read',
        access_scope TEXT NOT NULL DEFAULT 'entity',
        role_in_entity TEXT DEFAULT 'user',
        can_view_financials INTEGER DEFAULT 0,
        can_approve_intercompany INTEGER DEFAULT 0,
        can_manage_users INTEGER DEFAULT 0,
        can_manage_documents INTEGER DEFAULT 0,
        cross_entity_reporting INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        is_default INTEGER DEFAULT 0,
        is_inherited INTEGER DEFAULT 0,
        effective_from DATE,
        effective_to DATE,
        granted_by INTEGER,
        granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        revoked_by INTEGER,
        revoked_at DATETIME,
        revoke_reason TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (entity_id) REFERENCES legal_entities(id) ON DELETE CASCADE,
        FOREIGN KEY (branch_id) REFERENCES entity_branches(id) ON DELETE CASCADE,
        FOREIGN KEY (site_id) REFERENCES entity_sites(id) ON DELETE CASCADE,
        FOREIGN KEY (group_id) REFERENCES entity_groups(id) ON DELETE CASCADE,
        FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (revoked_by) REFERENCES users(id) ON DELETE SET NULL,
        UNIQUE(user_id, entity_id, branch_id, site_id, access_scope)
    )""",

    # -------------------------------------------------------------------------
    # 7. Shared Master Data Rules
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS shared_master_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_type TEXT NOT NULL,
        data_subtype TEXT,
        scope TEXT NOT NULL DEFAULT 'entity',
        visibility TEXT NOT NULL DEFAULT 'private',
        sharing_policy TEXT NOT NULL DEFAULT 'none',
        allowed_entity_ids TEXT,
        inheritance_mode TEXT DEFAULT 'inherit',
        override_allowed INTEGER DEFAULT 0,
        override_requires_approval INTEGER DEFAULT 0,
        entity_id INTEGER,
        group_id INTEGER,
        is_active INTEGER DEFAULT 1,
        priority INTEGER DEFAULT 0,
        description TEXT,
        metadata TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (entity_id) REFERENCES legal_entities(id) ON DELETE CASCADE,
        FOREIGN KEY (group_id) REFERENCES entity_groups(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
        UNIQUE(data_type, data_subtype, entity_id, scope)
    )""",

    # -------------------------------------------------------------------------
    # 8. Intercompany Rules
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS intercompany_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_code TEXT UNIQUE NOT NULL,
        rule_name TEXT NOT NULL,
        rule_type TEXT NOT NULL,
        description TEXT,
        source_entity_id INTEGER,
        target_entity_id INTEGER,
        relationship_type TEXT,
        transaction_types TEXT,
        pricing_policy TEXT,
        markup_percentage REAL,
        discount_percentage REAL,
        payment_terms TEXT,
        credit_limit REAL DEFAULT 0,
        approval_workflow_id INTEGER,
        is_auto_approve INTEGER DEFAULT 0,
        auto_approve_conditions TEXT,
        is_active INTEGER DEFAULT 1,
        priority INTEGER DEFAULT 0,
        notes TEXT,
        metadata TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (source_entity_id) REFERENCES legal_entities(id) ON DELETE CASCADE,
        FOREIGN KEY (target_entity_id) REFERENCES legal_entities(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 9. Intercompany Partner Mapping
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS intercompany_partners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        local_entity_id INTEGER NOT NULL,
        partner_entity_id INTEGER NOT NULL,
        partner_type TEXT DEFAULT 'internal',
        partner_code TEXT,
        partner_name TEXT,
        relationship_code TEXT,
        tax_identification TEXT,
        vat_number TEXT,
        bank_account_reference TEXT,
        contact_name TEXT,
        contact_email TEXT,
        contact_phone TEXT,
        credit_limit REAL DEFAULT 0,
        payment_terms TEXT,
        is_active INTEGER DEFAULT 1,
        is_verified INTEGER DEFAULT 0,
        notes TEXT,
        metadata TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (local_entity_id) REFERENCES legal_entities(id) ON DELETE CASCADE,
        FOREIGN KEY (partner_entity_id) REFERENCES legal_entities(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
        UNIQUE(local_entity_id, partner_entity_id)
    )""",

    # -------------------------------------------------------------------------
    # 10. Entity Numbering Schemes
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS entity_numbering_schemes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_id INTEGER,
        group_id INTEGER,
        branch_id INTEGER,
        document_type TEXT NOT NULL,
        scheme_code TEXT UNIQUE NOT NULL,
        scheme_name TEXT NOT NULL,
        prefix TEXT,
        prefix_type TEXT DEFAULT 'fixed',
        include_group_code INTEGER DEFAULT 0,
        include_entity_code INTEGER DEFAULT 1,
        include_branch_code INTEGER DEFAULT 0,
        include_site_code INTEGER DEFAULT 0,
        include_year INTEGER DEFAULT 1,
        include_month INTEGER DEFAULT 0,
        include_day INTEGER DEFAULT 0,
        year_format TEXT DEFAULT 'YYYY',
        sequence_length INTEGER DEFAULT 5,
        sequence_format TEXT DEFAULT 'zero_padded',
        current_sequence INTEGER DEFAULT 0,
        last_used_number TEXT,
        last_used_date DATE,
        suffix TEXT,
        separator TEXT DEFAULT '-',
        reset_frequency TEXT DEFAULT 'yearly',
        is_active INTEGER DEFAULT 1,
        is_locked INTEGER DEFAULT 0,
        notes TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (entity_id) REFERENCES legal_entities(id) ON DELETE CASCADE,
        FOREIGN KEY (group_id) REFERENCES entity_groups(id) ON DELETE CASCADE,
        FOREIGN KEY (branch_id) REFERENCES entity_branches(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
        UNIQUE(entity_id, document_type)
    )""",

    # -------------------------------------------------------------------------
    # 11. Entity Access Reviews
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS entity_access_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        review_code TEXT UNIQUE NOT NULL,
        review_name TEXT NOT NULL,
        entity_id INTEGER,
        group_id INTEGER,
        review_type TEXT DEFAULT 'periodic',
        frequency TEXT DEFAULT 'quarterly',
        assigned_reviewer_id INTEGER,
        status TEXT DEFAULT 'pending',
        started_at DATETIME,
        completed_at DATETIME,
        due_date DATE,
        notes TEXT,
        metadata TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (entity_id) REFERENCES legal_entities(id) ON DELETE CASCADE,
        FOREIGN KEY (group_id) REFERENCES entity_groups(id) ON DELETE CASCADE,
        FOREIGN KEY (assigned_reviewer_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 12. Entity Access Review Items
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS entity_access_review_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        review_id INTEGER NOT NULL,
        access_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        entity_id INTEGER,
        branch_id INTEGER,
        site_id INTEGER,
        previous_level TEXT,
        recommended_level TEXT,
        final_level TEXT,
        action_taken TEXT,
        reviewer_id INTEGER,
        review_notes TEXT,
        reviewed_at DATETIME,
        is_approved INTEGER DEFAULT 0,
        is_rejected INTEGER DEFAULT 0,
        rejection_reason TEXT,
        metadata TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (review_id) REFERENCES entity_access_reviews(id) ON DELETE CASCADE,
        FOREIGN KEY (access_id) REFERENCES entity_access(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (entity_id) REFERENCES legal_entities(id) ON DELETE CASCADE,
        FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 13. Entity Change Requests
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS entity_change_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_code TEXT UNIQUE NOT NULL,
        entity_id INTEGER,
        branch_id INTEGER,
        site_id INTEGER,
        change_type TEXT NOT NULL,
        change_category TEXT,
        field_name TEXT,
        old_value TEXT,
        new_value TEXT,
        reason TEXT,
        requested_by INTEGER,
        requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending',
        reviewed_by INTEGER,
        reviewed_at DATETIME,
        approved_by INTEGER,
        approved_at DATETIME,
        rejected_by INTEGER,
        rejected_at DATETIME,
        rejection_reason TEXT,
        workflow_id INTEGER,
        notes TEXT,
        metadata TEXT,
        FOREIGN KEY (entity_id) REFERENCES legal_entities(id) ON DELETE CASCADE,
        FOREIGN KEY (branch_id) REFERENCES entity_branches(id) ON DELETE CASCADE,
        FOREIGN KEY (site_id) REFERENCES entity_sites(id) ON DELETE CASCADE,
        FOREIGN KEY (requested_by) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (rejected_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 14. Entity Configuration Checks
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS entity_config_checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_id INTEGER,
        group_id INTEGER,
        check_type TEXT NOT NULL,
        check_name TEXT NOT NULL,
        check_category TEXT,
        severity TEXT DEFAULT 'medium',
        status TEXT DEFAULT 'pending',
        is_critical INTEGER DEFAULT 0,
        description TEXT,
        current_value TEXT,
        expected_value TEXT,
        remediation TEXT,
        last_checked_at DATETIME,
        next_check_at DATETIME,
        metadata TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (entity_id) REFERENCES legal_entities(id) ON DELETE CASCADE,
        FOREIGN KEY (group_id) REFERENCES entity_groups(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 15. Entity Audit Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS entity_audit_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_id INTEGER,
        group_id INTEGER,
        branch_id INTEGER,
        site_id INTEGER,
        entity_type TEXT NOT NULL,
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
        source TEXT DEFAULT 'ui',
        reference_type TEXT,
        reference_id INTEGER,
        metadata TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (entity_id) REFERENCES legal_entities(id) ON DELETE CASCADE,
        FOREIGN KEY (group_id) REFERENCES entity_groups(id) ON DELETE CASCADE,
        FOREIGN KEY (branch_id) REFERENCES entity_branches(id) ON DELETE CASCADE,
        FOREIGN KEY (site_id) REFERENCES entity_sites(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 16. Entity Export Presets
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS entity_export_presets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        preset_code TEXT UNIQUE NOT NULL,
        preset_name TEXT NOT NULL,
        preset_type TEXT NOT NULL,
        description TEXT,
        entity_id INTEGER,
        group_id INTEGER,
        columns_config TEXT,
        filters_config TEXT,
        sort_config TEXT,
        format_options TEXT,
        is_default INTEGER DEFAULT 0,
        is_shared INTEGER DEFAULT 0,
        shared_with_groups TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (entity_id) REFERENCES legal_entities(id) ON DELETE CASCADE,
        FOREIGN KEY (group_id) REFERENCES entity_groups(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 17. Entity Dashboard Preferences
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS entity_dashboard_prefs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        entity_id INTEGER,
        group_id INTEGER,
        widget_layout TEXT,
        refresh_interval INTEGER DEFAULT 60,
        date_range_default TEXT,
        filter_defaults TEXT,
        is_default INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (entity_id) REFERENCES legal_entities(id) ON DELETE CASCADE,
        FOREIGN KEY (group_id) REFERENCES entity_groups(id) ON DELETE CASCADE,
        UNIQUE(user_id, entity_id)
    )""",

    # -------------------------------------------------------------------------
    # 18. Entity Settings
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS entity_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_id INTEGER NOT NULL,
        setting_key TEXT NOT NULL,
        setting_value TEXT,
        setting_type TEXT DEFAULT 'text',
        category TEXT DEFAULT 'General',
        is_inherited INTEGER DEFAULT 0,
        inherited_from TEXT,
        is_active INTEGER DEFAULT 1,
        description TEXT,
        metadata TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (entity_id) REFERENCES legal_entities(id) ON DELETE CASCADE,
        UNIQUE(entity_id, setting_key)
    )""",

    # -------------------------------------------------------------------------
    # 19. Entity Notifications
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS entity_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_id INTEGER,
        group_id INTEGER,
        branch_id INTEGER,
        site_id INTEGER,
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
        expires_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (entity_id) REFERENCES legal_entities(id) ON DELETE CASCADE,
        FOREIGN KEY (group_id) REFERENCES entity_groups(id) ON DELETE CASCADE,
        FOREIGN KEY (branch_id) REFERENCES entity_branches(id) ON DELETE CASCADE,
        FOREIGN KEY (site_id) REFERENCES entity_sites(id) ON DELETE CASCADE,
        FOREIGN KEY (read_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 20. User Favorite Entities (for quick access)
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS user_favorite_entities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        entity_id INTEGER,
        group_id INTEGER,
        display_order INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (entity_id) REFERENCES legal_entities(id) ON DELETE CASCADE,
        FOREIGN KEY (group_id) REFERENCES entity_groups(id) ON DELETE CASCADE,
        UNIQUE(user_id, entity_id)
    )""",

    # -------------------------------------------------------------------------
    # 21. Recent Entity Scopes (for session history)
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS user_recent_scopes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        scope_type TEXT NOT NULL,
        scope_entity_id INTEGER,
        scope_group_id INTEGER,
        scope_branch_id INTEGER,
        scope_site_id INTEGER,
        display_name TEXT,
        accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (scope_entity_id) REFERENCES legal_entities(id) ON DELETE CASCADE,
        FOREIGN KEY (scope_group_id) REFERENCES entity_groups(id) ON DELETE CASCADE,
        FOREIGN KEY (scope_branch_id) REFERENCES entity_branches(id) ON DELETE CASCADE,
        FOREIGN KEY (scope_site_id) REFERENCES entity_sites(id) ON DELETE CASCADE
    )""",
]


# =============================================================================
# MIGRATION AND INITIALIZATION
# =============================================================================

def run_migrations():
    """
    Run all multi-entity table migrations.
    Creates all entity management tables if they don't exist.
    """
    conn = get_db()
    try:
        for table_sql in MULTI_ENTITY_TABLES:
            conn.executescript(table_sql)

        conn.commit()

        # Seed default data
        seed_entity_defaults(conn)

        return True, "Multi-entity migrations completed successfully"
    except Exception as e:
        conn.rollback()
        return False, f"Multi-entity migration error: {str(e)}"
    finally:
        conn.close()


def seed_entity_defaults(conn):
    """Seed default entity management data."""

    # Seed default shared master rules
    default_shared_rules = [
        ('country', None, 'global', 'public', 'all', 'inherit', 0, 0, None),
        ('currency', None, 'global', 'public', 'all', 'inherit', 0, 0, None),
        ('uom', None, 'global', 'public', 'all', 'inherit', 0, 0, None),
        ('tax_code', None, 'global', 'public', 'all', 'inherit', 0, 0, None),
        ('customer', None, 'entity', 'private', 'self', 'override', 1, 1, None),
        ('supplier', None, 'entity', 'private', 'self', 'override', 1, 1, None),
        ('employee', None, 'entity', 'private', 'self', 'override', 1, 1, None),
        ('item', None, 'group', 'controlled', 'allowed', 'inherit', 1, 1, None),
        ('price_list', None, 'entity', 'private', 'self', 'override', 1, 0, None),
        ('stock', None, 'entity', 'private', 'self', 'none', 0, 0, None),
        ('order', None, 'entity', 'private', 'self', 'none', 0, 0, None),
        ('document_template', None, 'group', 'controlled', 'allowed', 'inherit', 1, 0, None),
    ]

    for data_type, group_id, scope, visibility, sharing, inheritance, override, approval, entity_id in default_shared_rules:
        existing = conn.execute(
            "SELECT id FROM shared_master_rules WHERE data_type = ? AND scope = ?",
            (data_type, scope)
        ).fetchone()
        if not existing:
            conn.execute("""
                INSERT INTO shared_master_rules
                (data_type, group_id, scope, visibility, sharing_policy, inheritance_mode,
                 override_allowed, override_requires_approval, entity_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (data_type, group_id, scope, visibility, sharing, inheritance, override, approval, entity_id))

    # Seed default intercompany rule types
    default_intercompany_types = [
        ('internal_sales', 'Internal Sales', 'transaction'),
        ('internal_purchase', 'Internal Purchase', 'transaction'),
        ('internal_transfer', 'Internal Stock Transfer', 'transaction'),
        ('internal_service', 'Internal Service Charge', 'transaction'),
        ('expense_allocation', 'Expense Allocation', 'transaction'),
        ('financial_posting', 'Financial Posting', 'transaction'),
        ('approval_routing', 'Approval Routing', 'workflow'),
        ('document_sharing', 'Document Sharing', 'document'),
    ]

    for code, name, rtype in default_intercompany_types:
        existing = conn.execute(
            "SELECT id FROM intercompany_rules WHERE rule_code = ?",
            (code,)
        ).fetchone()
        if not existing:
            conn.execute("""
                INSERT INTO intercompany_rules
                (rule_code, rule_name, rule_type, description, is_active)
                VALUES (?, ?, ?, ?, 1)
            """, (code, name, rtype, f'Default {name} rule'))

    conn.commit()


# =============================================================================
# GROUP/ HOLDING OPERATIONS
# =============================================================================

def get_all_groups(active_only: bool = True) -> List[Dict]:
    """Get all entity groups with statistics."""
    conn = get_db()
    try:
        query = """
            SELECT g.*,
                   pg.legal_name as parent_group_name,
                   (SELECT COUNT(*) FROM legal_entities WHERE parent_group_id = g.id) as entity_count,
                   (SELECT COUNT(*) FROM entity_branches eb
                    JOIN legal_entities le ON eb.entity_id = le.id
                    WHERE le.parent_group_id = g.id AND eb.is_active = 1) as branch_count,
                   (SELECT COUNT(*) FROM entity_sites es
                    JOIN legal_entities le ON es.entity_id = le.id
                    WHERE le.parent_group_id = g.id AND es.is_active = 1) as site_count,
                   u1.username as created_by_name,
                   u2.username as archived_by_name
            FROM entity_groups g
            LEFT JOIN entity_groups pg ON g.parent_group_id = pg.id
            LEFT JOIN users u1 ON g.created_by = u1.id
            LEFT JOIN users u2 ON g.archived_by = u2.id
        """
        if active_only:
            query += " WHERE g.is_active = 1"
        query += " ORDER BY g.legal_name"
        return [dict(row) for row in conn.execute(query).fetchall()]
    finally:
        conn.close()


def get_group_by_id(group_id: int) -> Optional[Dict]:
    """Get a single group by ID."""
    conn = get_db()
    try:
        result = conn.execute("""
            SELECT g.*,
                   pg.legal_name as parent_group_name,
                   u1.username as created_by_name,
                   u2.username as archived_by_name
            FROM entity_groups g
            LEFT JOIN entity_groups pg ON g.parent_group_id = pg.id
            LEFT JOIN users u1 ON g.created_by = u1.id
            LEFT JOIN users u2 ON g.archived_by = u2.id
            WHERE g.id = ?
        """, (group_id,)).fetchone()
        return dict(result) if result else None
    finally:
        conn.close()


def create_group(data: Dict) -> int:
    """Create a new entity group."""
    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO entity_groups (
                group_code, legal_name, trade_name, short_name, group_type,
                registration_number, tax_identification, vat_number,
                country, state_region, city, address_line1, address_line2,
                postal_code, phone, mobile, email, website,
                default_currency, fiscal_year_start, fiscal_year_end,
                base_language, logo_path, ownership_structure,
                parent_group_id, is_active, notes, metadata, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('group_code'), data.get('legal_name'), data.get('trade_name'),
            data.get('short_name'), data.get('group_type', 'holding'),
            data.get('registration_number'), data.get('tax_identification'),
            data.get('vat_number'), data.get('country', 'UAE'), data.get('state_region'),
            data.get('city'), data.get('address_line1'), data.get('address_line2'),
            data.get('postal_code'), data.get('phone'), data.get('mobile'),
            data.get('email'), data.get('website'),
            data.get('default_currency', 'AED'), data.get('fiscal_year_start', 1),
            data.get('fiscal_year_end', 12), data.get('base_language', 'en'),
            data.get('logo_path'), data.get('ownership_structure'),
            data.get('parent_group_id'), data.get('is_active', 1),
            data.get('notes'), json.dumps(data.get('metadata', {})),
            data.get('created_by')
        ))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_group(group_id: int, data: Dict) -> bool:
    """Update an existing entity group."""
    conn = get_db()
    try:
        conn.execute("""
            UPDATE entity_groups SET
                legal_name = COALESCE(?, legal_name),
                trade_name = COALESCE(?, trade_name),
                short_name = COALESCE(?, short_name),
                group_type = COALESCE(?, group_type),
                registration_number = COALESCE(?, registration_number),
                tax_identification = COALESCE(?, tax_identification),
                vat_number = COALESCE(?, vat_number),
                country = COALESCE(?, country),
                state_region = COALESCE(?, state_region),
                city = COALESCE(?, city),
                address_line1 = COALESCE(?, address_line1),
                address_line2 = COALESCE(?, address_line2),
                postal_code = COALESCE(?, postal_code),
                phone = COALESCE(?, phone),
                mobile = COALESCE(?, mobile),
                email = COALESCE(?, email),
                website = COALESCE(?, website),
                default_currency = COALESCE(?, default_currency),
                fiscal_year_start = COALESCE(?, fiscal_year_start),
                fiscal_year_end = COALESCE(?, fiscal_year_end),
                base_language = COALESCE(?, base_language),
                logo_path = COALESCE(?, logo_path),
                ownership_structure = COALESCE(?, ownership_structure),
                parent_group_id = COALESCE(?, parent_group_id),
                notes = COALESCE(?, notes),
                metadata = COALESCE(?, metadata),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get('legal_name'), data.get('trade_name'), data.get('short_name'),
            data.get('group_type'), data.get('registration_number'),
            data.get('tax_identification'), data.get('vat_number'),
            data.get('country'), data.get('state_region'), data.get('city'),
            data.get('address_line1'), data.get('address_line2'),
            data.get('postal_code'), data.get('phone'), data.get('mobile'),
            data.get('email'), data.get('website'),
            data.get('default_currency'), data.get('fiscal_year_start'),
            data.get('fiscal_year_end'), data.get('base_language'),
            data.get('logo_path'), data.get('ownership_structure'),
            data.get('parent_group_id'), data.get('notes'),
            json.dumps(data.get('metadata', {})) if data.get('metadata') else None,
            group_id
        ))
        conn.commit()
        return True
    finally:
        conn.close()


def archive_group(group_id: int, user_id: int = None) -> bool:
    """Archive an entity group (soft delete)."""
    conn = get_db()
    try:
        conn.execute("""
            UPDATE entity_groups SET
                is_active = 0,
                archived_at = CURRENT_TIMESTAMP,
                archived_by = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, group_id))
        conn.commit()
        return True
    finally:
        conn.close()


# =============================================================================
# LEGAL ENTITY OPERATIONS
# =============================================================================

def get_all_entities(active_only: bool = True, group_id: int = None) -> List[Dict]:
    """Get all legal entities with statistics."""
    conn = get_db()
    try:
        query = """
            SELECT e.*,
                   g.legal_name as group_name,
                   pe.legal_name as parent_entity_name,
                   (SELECT COUNT(*) FROM entity_branches WHERE entity_id = e.id AND is_active = 1) as branch_count,
                   (SELECT COUNT(*) FROM entity_sites WHERE entity_id = e.id AND is_active = 1) as site_count,
                   (SELECT COUNT(*) FROM entity_access WHERE entity_id = e.id AND is_active = 1) as user_count,
                   u1.username as created_by_name
            FROM legal_entities e
            LEFT JOIN entity_groups g ON e.parent_group_id = g.id
            LEFT JOIN legal_entities pe ON e.parent_entity_id = pe.id
            LEFT JOIN users u1 ON e.created_by = u1.id
            WHERE 1=1
        """
        params = []
        if active_only:
            query += " AND e.is_active = 1"
        if group_id:
            query += " AND e.parent_group_id = ?"
            params.append(group_id)
        query += " ORDER BY e.legal_name"
        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def get_entity_by_id(entity_id: int) -> Optional[Dict]:
    """Get a single legal entity by ID."""
    conn = get_db()
    try:
        result = conn.execute("""
            SELECT e.*,
                   g.legal_name as group_name,
                   pe.legal_name as parent_entity_name,
                   u1.username as created_by_name,
                   u2.username as archived_by_name
            FROM legal_entities e
            LEFT JOIN entity_groups g ON e.parent_group_id = g.id
            LEFT JOIN legal_entities pe ON e.parent_entity_id = pe.id
            LEFT JOIN users u1 ON e.created_by = u1.id
            LEFT JOIN users u2 ON e.archived_by = u2.id
            WHERE e.id = ?
        """, (entity_id,)).fetchone()
        return dict(result) if result else None
    finally:
        conn.close()


def create_entity(data: Dict) -> int:
    """Create a new legal entity."""
    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO legal_entities (
                entity_code, legal_name, short_name, trade_name, entity_type,
                business_type, registration_number, tax_identification, vat_number,
                excise_tax_number, customs_code, chamber_of_commerce_number,
                license_number, license_type, license_expiry,
                country, state_region, city, district,
                address_line1, address_line2, postal_code, google_maps_url,
                phone, mobile, fax, email, website,
                default_currency, secondary_currency, timezone, date_format,
                fiscal_year_start, fiscal_year_end, base_language,
                ownership_percentage, parent_entity_id, parent_group_id,
                intercompany_partner_code, consolidation_flag, is_active, status,
                primary_contact_name, primary_contact_phone, primary_contact_email,
                finance_contact_name, finance_contact_email,
                logo_path, document_prefix, notes, metadata, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('entity_code'), data.get('legal_name'), data.get('short_name'),
            data.get('trade_name'), data.get('entity_type', 'subsidiary'),
            data.get('business_type'), data.get('registration_number'),
            data.get('tax_identification'), data.get('vat_number'),
            data.get('excise_tax_number'), data.get('customs_code'),
            data.get('chamber_of_commerce_number'), data.get('license_number'),
            data.get('license_type'), data.get('license_expiry'),
            data.get('country', 'UAE'), data.get('state_region'), data.get('city'),
            data.get('district'), data.get('address_line1'), data.get('address_line2'),
            data.get('postal_code'), data.get('google_maps_url'),
            data.get('phone'), data.get('mobile'), data.get('fax'),
            data.get('email'), data.get('website'),
            data.get('default_currency', 'AED'), data.get('secondary_currency'),
            data.get('timezone', 'Asia/Dubai'), data.get('date_format', 'DD/MM/YYYY'),
            data.get('fiscal_year_start', 1), data.get('fiscal_year_end', 12),
            data.get('base_language', 'en'), data.get('ownership_percentage', 100),
            data.get('parent_entity_id'), data.get('parent_group_id'),
            data.get('intercompany_partner_code'), data.get('consolidation_flag', 1),
            data.get('is_active', 1), data.get('status', 'active'),
            data.get('primary_contact_name'), data.get('primary_contact_phone'),
            data.get('primary_contact_email'), data.get('finance_contact_name'),
            data.get('finance_contact_email'), data.get('logo_path'),
            data.get('document_prefix'), data.get('notes'),
            json.dumps(data.get('metadata', {})), data.get('created_by')
        ))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_entity(entity_id: int, data: Dict) -> bool:
    """Update an existing legal entity."""
    conn = get_db()
    try:
        fields = []
        values = []

        allowed_fields = [
            'legal_name', 'short_name', 'trade_name', 'entity_type', 'business_type',
            'registration_number', 'tax_identification', 'vat_number', 'excise_tax_number',
            'customs_code', 'chamber_of_commerce_number', 'license_number', 'license_type',
            'license_expiry', 'country', 'state_region', 'city', 'district',
            'address_line1', 'address_line2', 'postal_code', 'google_maps_url',
            'phone', 'mobile', 'fax', 'email', 'website', 'default_currency',
            'secondary_currency', 'timezone', 'date_format', 'fiscal_year_start',
            'fiscal_year_end', 'base_language', 'ownership_percentage', 'parent_entity_id',
            'parent_group_id', 'intercompany_partner_code', 'consolidation_flag',
            'is_active', 'status', 'primary_contact_name', 'primary_contact_phone',
            'primary_contact_email', 'finance_contact_name', 'finance_contact_email',
            'logo_path', 'document_prefix', 'notes'
        ]

        for field in allowed_fields:
            if field in data:
                fields.append(f"{field} = ?")
                values.append(data[field])

        if data.get('metadata'):
            fields.append("metadata = ?")
            values.append(json.dumps(data['metadata']))

        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(entity_id)

        query = f"UPDATE legal_entities SET {', '.join(fields)} WHERE id = ?"
        conn.execute(query, values)
        conn.commit()
        return True
    finally:
        conn.close()


def archive_entity(entity_id: int, user_id: int = None) -> bool:
    """Archive a legal entity (soft delete)."""
    conn = get_db()
    try:
        conn.execute("""
            UPDATE legal_entities SET
                is_active = 0,
                status = 'archived',
                archived_at = CURRENT_TIMESTAMP,
                archived_by = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, entity_id))
        conn.commit()
        return True
    finally:
        conn.close()


def restore_entity(entity_id: int) -> bool:
    """Restore an archived legal entity."""
    conn = get_db()
    try:
        conn.execute("""
            UPDATE legal_entities SET
                is_active = 1,
                status = 'active',
                archived_at = NULL,
                archived_by = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (entity_id,))
        conn.commit()
        return True
    finally:
        conn.close()


# =============================================================================
# BRANCH OPERATIONS
# =============================================================================

def get_entity_branches(entity_id: int, active_only: bool = True) -> List[Dict]:
    """Get all branches for an entity."""
    conn = get_db()
    try:
        query = """
            SELECT b.*,
                   e.legal_name as entity_name,
                   (SELECT COUNT(*) FROM entity_sites WHERE branch_id = b.id AND is_active = 1) as site_count,
                   u1.username as created_by_name
            FROM entity_branches b
            JOIN legal_entities e ON b.entity_id = e.id
            LEFT JOIN users u1 ON b.created_by = u1.id
            WHERE b.entity_id = ?
        """
        if active_only:
            query += " AND b.is_active = 1"
        query += " ORDER BY b.branch_name"
        return [dict(row) for row in conn.execute(query, (entity_id,)).fetchall()]
    finally:
        conn.close()


def get_all_branches(active_only: bool = True, entity_id: int = None) -> List[Dict]:
    """Get all branches across entities."""
    conn = get_db()
    try:
        query = """
            SELECT b.*,
                   e.legal_name as entity_name,
                   e.entity_code,
                   g.legal_name as group_name
            FROM entity_branches b
            JOIN legal_entities e ON b.entity_id = e.id
            LEFT JOIN entity_groups g ON e.parent_group_id = g.id
            WHERE 1=1
        """
        params = []
        if active_only:
            query += " AND b.is_active = 1"
        if entity_id:
            query += " AND b.entity_id = ?"
            params.append(entity_id)
        query += " ORDER BY e.legal_name, b.branch_name"
        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def get_branch_by_id(branch_id: int) -> Optional[Dict]:
    """Get a single branch by ID."""
    conn = get_db()
    try:
        result = conn.execute("""
            SELECT b.*,
                   e.legal_name as entity_name,
                   e.entity_code,
                   u1.username as created_by_name
            FROM entity_branches b
            JOIN legal_entities e ON b.entity_id = e.id
            LEFT JOIN users u1 ON b.created_by = u1.id
            WHERE b.id = ?
        """, (branch_id,)).fetchone()
        return dict(result) if result else None
    finally:
        conn.close()


def create_branch(data: Dict) -> int:
    """Create a new branch."""
    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO entity_branches (
                entity_id, branch_code, branch_name, short_name, branch_type,
                branch_category, description, is_head_office, is_operational,
                contact_name, contact_phone, contact_email, contact_position,
                address_line1, address_line2, city, district, country, postal_code,
                phone, phone2, mobile, fax, email,
                default_warehouse_id, default_document_prefix, approvals_owner_id,
                finance_posting_rules, local_timezone, local_language,
                operational_hours, is_active, status, notes, metadata, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('entity_id'), data.get('branch_code'), data.get('branch_name'),
            data.get('short_name'), data.get('branch_type', 'branch_office'),
            data.get('branch_category'), data.get('description'),
            data.get('is_head_office', 0), data.get('is_operational', 1),
            data.get('contact_name'), data.get('contact_phone'), data.get('contact_email'),
            data.get('contact_position'), data.get('address_line1'), data.get('address_line2'),
            data.get('city'), data.get('district'), data.get('country'),
            data.get('postal_code'), data.get('phone'), data.get('phone2'),
            data.get('mobile'), data.get('fax'), data.get('email'),
            data.get('default_warehouse_id'), data.get('default_document_prefix'),
            data.get('approvals_owner_id'), json.dumps(data.get('finance_posting_rules', {})),
            data.get('local_timezone'), data.get('local_language'),
            json.dumps(data.get('operational_hours', {})), data.get('is_active', 1),
            data.get('status', 'active'), data.get('notes'),
            json.dumps(data.get('metadata', {})), data.get('created_by')
        ))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_branch(branch_id: int, data: Dict) -> bool:
    """Update an existing branch."""
    conn = get_db()
    try:
        fields = []
        values = []

        allowed_fields = [
            'branch_name', 'short_name', 'branch_type', 'branch_category',
            'description', 'is_head_office', 'is_operational', 'contact_name',
            'contact_phone', 'contact_email', 'contact_position', 'address_line1',
            'address_line2', 'city', 'district', 'country', 'postal_code',
            'phone', 'phone2', 'mobile', 'fax', 'email', 'default_warehouse_id',
            'default_document_prefix', 'approvals_owner_id', 'local_timezone',
            'local_language', 'is_active', 'status', 'notes'
        ]

        for field in allowed_fields:
            if field in data:
                fields.append(f"{field} = ?")
                values.append(data[field])

        if 'finance_posting_rules' in data:
            fields.append("finance_posting_rules = ?")
            values.append(json.dumps(data['finance_posting_rules']))

        if 'operational_hours' in data:
            fields.append("operational_hours = ?")
            values.append(json.dumps(data['operational_hours']))

        if 'metadata' in data:
            fields.append("metadata = ?")
            values.append(json.dumps(data['metadata']))

        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(branch_id)

        query = f"UPDATE entity_branches SET {', '.join(fields)} WHERE id = ?"
        conn.execute(query, values)
        conn.commit()
        return True
    finally:
        conn.close()


def archive_branch(branch_id: int, user_id: int = None) -> bool:
    """Archive a branch."""
    conn = get_db()
    try:
        conn.execute("""
            UPDATE entity_branches SET
                is_active = 0,
                status = 'archived',
                archived_at = CURRENT_TIMESTAMP,
                archived_by = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, branch_id))
        conn.commit()
        return True
    finally:
        conn.close()


# =============================================================================
# SITE OPERATIONS
# =============================================================================

def get_branch_sites(branch_id: int, active_only: bool = True) -> List[Dict]:
    """Get all sites for a branch."""
    conn = get_db()
    try:
        query = """
            SELECT s.*,
                   b.branch_name,
                   u1.username as created_by_name
            FROM entity_sites s
            JOIN entity_branches b ON s.branch_id = b.id
            LEFT JOIN users u1 ON s.created_by = u1.id
            WHERE s.branch_id = ?
        """
        if active_only:
            query += " AND s.is_active = 1"
        query += " ORDER BY s.site_name"
        return [dict(row) for row in conn.execute(query, (branch_id,)).fetchall()]
    finally:
        conn.close()


def get_entity_sites(entity_id: int, active_only: bool = True) -> List[Dict]:
    """Get all sites for an entity."""
    conn = get_db()
    try:
        query = """
            SELECT s.*,
                   b.branch_name,
                   e.legal_name as entity_name,
                   u1.username as created_by_name
            FROM entity_sites s
            JOIN entity_branches b ON s.branch_id = b.id
            JOIN legal_entities e ON s.entity_id = e.id
            LEFT JOIN users u1 ON s.created_by = u1.id
            WHERE s.entity_id = ?
        """
        if active_only:
            query += " AND s.is_active = 1"
        query += " ORDER BY s.site_name"
        return [dict(row) for row in conn.execute(query, (entity_id,)).fetchall()]
    finally:
        conn.close()


def get_all_sites(active_only: bool = True, entity_id: int = None) -> List[Dict]:
    """Get all sites across entities."""
    conn = get_db()
    try:
        query = """
            SELECT s.*,
                   e.legal_name as entity_name,
                   e.entity_code,
                   b.branch_name,
                   g.legal_name as group_name
            FROM entity_sites s
            JOIN legal_entities e ON s.entity_id = e.id
            LEFT JOIN entity_branches b ON s.branch_id = b.id
            LEFT JOIN entity_groups g ON e.parent_group_id = g.id
            WHERE 1=1
        """
        params = []
        if active_only:
            query += " AND s.is_active = 1"
        if entity_id:
            query += " AND s.entity_id = ?"
            params.append(entity_id)
        query += " ORDER BY e.legal_name, b.branch_name, s.site_name"
        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def get_site_by_id(site_id: int) -> Optional[Dict]:
    """Get a single site by ID."""
    conn = get_db()
    try:
        result = conn.execute("""
            SELECT s.*,
                   e.legal_name as entity_name,
                   e.entity_code,
                   b.branch_name,
                   u1.username as created_by_name,
                   u2.username as responsible_person_name
            FROM entity_sites s
            JOIN legal_entities e ON s.entity_id = e.id
            LEFT JOIN entity_branches b ON s.branch_id = b.id
            LEFT JOIN users u1 ON s.created_by = u1.id
            LEFT JOIN users u2 ON s.responsible_person_id = u2.id
            WHERE s.id = ?
        """, (site_id,)).fetchone()
        return dict(result) if result else None
    finally:
        conn.close()


def create_site(data: Dict) -> int:
    """Create a new site."""
    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO entity_sites (
                entity_id, branch_id, site_code, site_name, short_name,
                site_type, site_subtype, description,
                address_line1, address_line2, city, district, country, postal_code,
                google_maps_url, phone, mobile, fax, email,
                contact_name, contact_position, contact_phone, contact_email,
                responsible_person_id, site_area_sqm, covered_area_sqm, yard_area_sqm,
                capacity_pallets, capacity_items, is_shared, shared_with_entities,
                operational_hours, working_days, is_operational, status,
                site_manager_name, site_manager_phone, site_manager_email,
                notes, metadata, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('entity_id'), data.get('branch_id'), data.get('site_code'),
            data.get('site_name'), data.get('short_name'),
            data.get('site_type', 'warehouse'), data.get('site_subtype'),
            data.get('description'), data.get('address_line1'), data.get('address_line2'),
            data.get('city'), data.get('district'), data.get('country'),
            data.get('postal_code'), data.get('google_maps_url'),
            data.get('phone'), data.get('mobile'), data.get('fax'), data.get('email'),
            data.get('contact_name'), data.get('contact_position'),
            data.get('contact_phone'), data.get('contact_email'),
            data.get('responsible_person_id'), data.get('site_area_sqm'),
            data.get('covered_area_sqm'), data.get('yard_area_sqm'),
            data.get('capacity_pallets'), data.get('capacity_items'),
            data.get('is_shared', 0), json.dumps(data.get('shared_with_entities', [])),
            json.dumps(data.get('operational_hours', {})), data.get('working_days'),
            data.get('is_operational', 1), data.get('status', 'active'),
            data.get('site_manager_name'), data.get('site_manager_phone'),
            data.get('site_manager_email'), data.get('notes'),
            json.dumps(data.get('metadata', {})), data.get('created_by')
        ))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_site(site_id: int, data: Dict) -> bool:
    """Update an existing site."""
    conn = get_db()
    try:
        fields = []
        values = []

        allowed_fields = [
            'branch_id', 'site_name', 'short_name', 'site_type', 'site_subtype',
            'description', 'address_line1', 'address_line2', 'city', 'district',
            'country', 'postal_code', 'google_maps_url', 'phone', 'mobile', 'fax',
            'email', 'contact_name', 'contact_position', 'contact_phone',
            'contact_email', 'responsible_person_id', 'site_area_sqm',
            'covered_area_sqm', 'yard_area_sqm', 'capacity_pallets', 'capacity_items',
            'is_shared', 'operational_hours', 'working_days', 'is_operational',
            'status', 'site_manager_name', 'site_manager_phone', 'site_manager_email',
            'notes'
        ]

        for field in allowed_fields:
            if field in data:
                fields.append(f"{field} = ?")
                values.append(data[field])

        if 'shared_with_entities' in data:
            fields.append("shared_with_entities = ?")
            values.append(json.dumps(data['shared_with_entities']))

        if 'metadata' in data:
            fields.append("metadata = ?")
            values.append(json.dumps(data['metadata']))

        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(site_id)

        query = f"UPDATE entity_sites SET {', '.join(fields)} WHERE id = ?"
        conn.execute(query, values)
        conn.commit()
        return True
    finally:
        conn.close()


def archive_site(site_id: int, user_id: int = None) -> bool:
    """Archive a site."""
    conn = get_db()
    try:
        conn.execute("""
            UPDATE entity_sites SET
                is_active = 0,
                status = 'archived',
                archived_at = CURRENT_TIMESTAMP,
                archived_by = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, site_id))
        conn.commit()
        return True
    finally:
        conn.close()


# =============================================================================
# ENTITY RELATIONSHIPS
# =============================================================================

def get_entity_relationships(entity_id: int = None, rel_type: str = None) -> List[Dict]:
    """Get entity relationships."""
    conn = get_db()
    try:
        query = """
            SELECT r.*,
                   e1.legal_name as source_entity_name,
                   e1.entity_code as source_entity_code,
                   e2.legal_name as target_entity_name,
                   e2.entity_code as target_entity_code,
                   u1.username as created_by_name
            FROM entity_relationships r
            JOIN legal_entities e1 ON r.source_entity_id = e1.id
            JOIN legal_entities e2 ON r.target_entity_id = e2.id
            LEFT JOIN users u1 ON r.created_by = u1.id
            WHERE 1=1
        """
        params = []
        if entity_id:
            query += " AND (r.source_entity_id = ? OR r.target_entity_id = ?)"
            params.extend([entity_id, entity_id])
        if rel_type:
            query += " AND r.relationship_type = ?"
            params.append(rel_type)
        query += " ORDER BY e1.legal_name, r.relationship_type"
        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def create_relationship(data: Dict) -> int:
    """Create a new entity relationship."""
    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO entity_relationships (
                source_entity_id, target_entity_id, relationship_type,
                relationship_subtype, ownership_percentage, effective_date,
                end_date, is_active, approval_required, internal_pricing_policy,
                trade_terms, credit_limit, payment_terms, notes, metadata, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('source_entity_id'), data.get('target_entity_id'),
            data.get('relationship_type'), data.get('relationship_subtype'),
            data.get('ownership_percentage'), data.get('effective_date'),
            data.get('end_date'), data.get('is_active', 1),
            data.get('approval_required', 0), data.get('internal_pricing_policy'),
            data.get('trade_terms'), data.get('credit_limit', 0),
            data.get('payment_terms'), data.get('notes'),
            json.dumps(data.get('metadata', {})), data.get('created_by')
        ))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


# =============================================================================
# ACCESS CONTROL
# =============================================================================

def get_entity_access(entity_id: int = None, user_id: int = None) -> List[Dict]:
    """Get entity access assignments."""
    conn = get_db()
    try:
        query = """
            SELECT a.*,
                   e.legal_name as entity_name,
                   b.branch_name,
                   s.site_name,
                   g.legal_name as group_name,
                   u1.username as user_name,
                   u2.username as granted_by_name
            FROM entity_access a
            LEFT JOIN legal_entities e ON a.entity_id = e.id
            LEFT JOIN entity_branches b ON a.branch_id = b.id
            LEFT JOIN entity_sites s ON a.site_id = s.id
            LEFT JOIN entity_groups g ON a.group_id = g.id
            LEFT JOIN users u1 ON a.user_id = u1.id
            LEFT JOIN users u2 ON a.granted_by = u2.id
            WHERE 1=1
        """
        params = []
        if entity_id:
            query += " AND a.entity_id = ?"
            params.append(entity_id)
        if user_id:
            query += " AND a.user_id = ?"
            params.append(user_id)
        query += " ORDER BY e.legal_name, b.branch_name"
        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def get_user_entity_access(user_id: int) -> List[Dict]:
    """Get all entity access for a specific user."""
    conn = get_db()
    try:
        return [dict(row) for row in conn.execute("""
            SELECT a.*,
                   e.legal_name as entity_name,
                   e.entity_code,
                   b.branch_name,
                   s.site_name,
                   g.legal_name as group_name
            FROM entity_access a
            LEFT JOIN legal_entities e ON a.entity_id = e.id
            LEFT JOIN entity_branches b ON a.branch_id = b.id
            LEFT JOIN entity_sites s ON a.site_id = s.id
            LEFT JOIN entity_groups g ON a.group_id = g.id
            WHERE a.user_id = ? AND a.is_active = 1
            ORDER BY a.is_default DESC, e.legal_name
        """, (user_id,)).fetchall()]
    finally:
        conn.close()


def assign_entity_access(data: Dict) -> int:
    """Assign entity access to a user."""
    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO entity_access (
                user_id, entity_id, branch_id, site_id, group_id,
                access_level, access_scope, role_in_entity,
                can_view_financials, can_approve_intercompany, can_manage_users,
                can_manage_documents, cross_entity_reporting,
                is_active, is_default, effective_from, effective_to,
                granted_by, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('user_id'), data.get('entity_id'), data.get('branch_id'),
            data.get('site_id'), data.get('group_id'),
            data.get('access_level', 'read'), data.get('access_scope', 'entity'),
            data.get('role_in_entity', 'user'), data.get('can_view_financials', 0),
            data.get('can_approve_intercompany', 0), data.get('can_manage_users', 0),
            data.get('can_manage_documents', 0), data.get('cross_entity_reporting', 0),
            data.get('is_active', 1), data.get('is_default', 0),
            data.get('effective_from'), data.get('effective_to'),
            data.get('granted_by'), data.get('notes')
        ))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_access_scope(access_id: int, data: Dict) -> bool:
    """Update entity access scope."""
    conn = get_db()
    try:
        conn.execute("""
            UPDATE entity_access SET
                access_level = COALESCE(?, access_level),
                access_scope = COALESCE(?, access_scope),
                role_in_entity = COALESCE(?, role_in_entity),
                can_view_financials = COALESCE(?, can_view_financials),
                can_approve_intercompany = COALESCE(?, can_approve_intercompany),
                can_manage_users = COALESCE(?, can_manage_users),
                can_manage_documents = COALESCE(?, can_manage_documents),
                cross_entity_reporting = COALESCE(?, cross_entity_reporting),
                is_active = COALESCE(?, is_active),
                is_default = COALESCE(?, is_default),
                effective_from = COALESCE(?, effective_from),
                effective_to = COALESCE(?, effective_to),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get('access_level'), data.get('access_scope'),
            data.get('role_in_entity'), data.get('can_view_financials'),
            data.get('can_approve_intercompany'), data.get('can_manage_users'),
            data.get('can_manage_documents'), data.get('cross_entity_reporting'),
            data.get('is_active'), data.get('is_default'),
            data.get('effective_from'), data.get('effective_to'),
            access_id
        ))
        conn.commit()
        return True
    finally:
        conn.close()


def revoke_entity_access(access_id: int, revoked_by: int, reason: str = None) -> bool:
    """Revoke entity access."""
    conn = get_db()
    try:
        conn.execute("""
            UPDATE entity_access SET
                is_active = 0,
                revoked_by = ?,
                revoked_at = CURRENT_TIMESTAMP,
                revoke_reason = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (revoked_by, reason, access_id))
        conn.commit()
        return True
    finally:
        conn.close()


def get_user_entity_scope(user_id: int) -> Dict:
    """Get user's effective entity scope."""
    conn = get_db()
    try:
        access_records = get_user_entity_access(user_id)

        scope = {
            'user_id': user_id,
            'default_entity_id': None,
            'allowed_entity_ids': [],
            'allowed_branch_ids': [],
            'allowed_site_ids': [],
            'group_ids': [],
            'can_view_financials': False,
            'can_approve_intercompany': False,
            'cross_entity_reporting': False,
            'scope_type': 'none'
        }

        for access in access_records:
            if access.get('is_default') and not scope['default_entity_id']:
                scope['default_entity_id'] = access.get('entity_id')

            if access.get('entity_id'):
                if access['entity_id'] not in scope['allowed_entity_ids']:
                    scope['allowed_entity_ids'].append(access['entity_id'])

            if access.get('branch_id'):
                if access['branch_id'] not in scope['allowed_branch_ids']:
                    scope['allowed_branch_ids'].append(access['branch_id'])

            if access.get('site_id'):
                if access['site_id'] not in scope['allowed_site_ids']:
                    scope['allowed_site_ids'].append(access['site_id'])

            if access.get('group_id'):
                if access['group_id'] not in scope['group_ids']:
                    scope['group_ids'].append(access['group_id'])

            if access.get('can_view_financials'):
                scope['can_view_financials'] = True
            if access.get('can_approve_intercompany'):
                scope['can_approve_intercompany'] = True
            if access.get('cross_entity_reporting'):
                scope['cross_entity_reporting'] = True

        if scope['allowed_entity_ids'] or scope['group_ids']:
            if scope['group_ids'] and not scope['allowed_entity_ids']:
                scope['scope_type'] = 'group'
            elif scope['allowed_entity_ids']:
                scope['scope_type'] = 'entity'

        return scope
    finally:
        conn.close()


# =============================================================================
# ENTITY SCOPING ENGINE
# =============================================================================

def set_user_entity_context(user_id: int, entity_id: int = None, branch_id: int = None,
                            site_id: int = None, group_id: int = None) -> bool:
    """Set user's current entity context in session/database."""
    conn = get_db()
    try:
        # Record in recent scopes
        conn.execute("""
            INSERT INTO user_recent_scopes (
                user_id, scope_type, scope_entity_id, scope_group_id,
                scope_branch_id, scope_site_id, display_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            'entity' if entity_id else 'group',
            entity_id, group_id, branch_id, site_id,
            _get_scope_display_name(entity_id, branch_id, site_id, group_id)
        ))

        # Keep only last 20 recent scopes
        conn.execute("""
            DELETE FROM user_recent_scopes
            WHERE user_id = ? AND id NOT IN (
                SELECT id FROM user_recent_scopes
                WHERE user_id = ?
                ORDER BY accessed_at DESC
                LIMIT 20
            )
        """, (user_id, user_id))

        conn.commit()
        return True
    finally:
        conn.close()


def _get_scope_display_name(entity_id: int = None, branch_id: int = None,
                            site_id: int = None, group_id: int = None) -> str:
    """Get display name for a scope."""
    if entity_id:
        entity = get_entity_by_id(entity_id)
        if entity:
            return entity.get('legal_name', entity.get('entity_code', 'Unknown'))
    if group_id:
        group = get_group_by_id(group_id)
        if group:
            return group.get('legal_name', group.get('group_code', 'Unknown'))
    return 'Unknown'


def get_current_entity_context(user_id: int) -> Dict:
    """Get user's current entity context."""
    conn = get_db()
    try:
        recent = conn.execute("""
            SELECT * FROM user_recent_scopes
            WHERE user_id = ?
            ORDER BY accessed_at DESC
            LIMIT 1
        """, (user_id,)).fetchone()

        if recent:
            return dict(recent)

        # Fall back to default entity
        scope = get_user_entity_scope(user_id)
        return {
            'scope_type': scope['scope_type'],
            'scope_entity_id': scope['default_entity_id'],
            'scope_group_id': None,
            'scope_branch_id': None,
            'scope_site_id': None
        }
    finally:
        conn.close()


def get_user_favorite_entities(user_id: int) -> List[Dict]:
    """Get user's favorite entities for quick access."""
    conn = get_db()
    try:
        return [dict(row) for row in conn.execute("""
            SELECT f.*,
                   e.legal_name as entity_name,
                   e.entity_code,
                   g.legal_name as group_name
            FROM user_favorite_entities f
            LEFT JOIN legal_entities e ON f.entity_id = e.id
            LEFT JOIN entity_groups g ON f.group_id = g.id
            WHERE f.user_id = ? AND f.is_active = 1
            ORDER BY f.display_order
        """, (user_id,)).fetchall()]
    finally:
        conn.close()


def add_favorite_entity(user_id: int, entity_id: int = None, group_id: int = None) -> bool:
    """Add an entity to user's favorites."""
    conn = get_db()
    try:
        max_order = conn.execute("""
            SELECT COALESCE(MAX(display_order), 0) + 1 as next_order
            FROM user_favorite_entities WHERE user_id = ?
        """, (user_id,)).fetchone()['next_order']

        conn.execute("""
            INSERT OR REPLACE INTO user_favorite_entities
            (user_id, entity_id, group_id, display_order)
            VALUES (?, ?, ?, ?)
        """, (user_id, entity_id, group_id, max_order))
        conn.commit()
        return True
    finally:
        conn.close()


# =============================================================================
# NUMBERING SCHEMES
# =============================================================================

def get_numbering_schemes(entity_id: int = None, group_id: int = None) -> List[Dict]:
    """Get entity numbering schemes."""
    conn = get_db()
    try:
        query = """
            SELECT n.*,
                   e.legal_name as entity_name,
                   g.legal_name as group_name,
                   b.branch_name
            FROM entity_numbering_schemes n
            LEFT JOIN legal_entities e ON n.entity_id = e.id
            LEFT JOIN entity_groups g ON n.group_id = g.id
            LEFT JOIN entity_branches b ON n.branch_id = b.id
            WHERE 1=1
        """
        params = []
        if entity_id:
            query += " AND n.entity_id = ?"
            params.append(entity_id)
        if group_id:
            query += " AND n.group_id = ?"
            params.append(group_id)
        query += " ORDER BY n.document_type"
        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def get_next_entity_number(entity_id: int, document_type: str) -> str:
    """Generate next document number based on entity numbering scheme."""
    conn = get_db()
    try:
        scheme = conn.execute("""
            SELECT * FROM entity_numbering_schemes
            WHERE entity_id = ? AND document_type = ? AND is_active = 1
        """, (entity_id, document_type)).fetchone()

        if not scheme:
            # Try group-level scheme
            entity = get_entity_by_id(entity_id)
            if entity and entity.get('parent_group_id'):
                scheme = conn.execute("""
                    SELECT * FROM entity_numbering_schemes
                    WHERE group_id = ? AND entity_id IS NULL
                    AND document_type = ? AND is_active = 1
                """, (entity['parent_group_id'], document_type)).fetchone()

        if not scheme:
            return None

        # Generate number
        new_sequence = scheme['current_sequence'] + 1

        parts = []

        # Prefix
        if scheme['prefix']:
            parts.append(scheme['prefix'])

        # Year
        if scheme['include_year']:
            year = datetime.now().year
            if scheme['year_format'] == 'YYYY':
                parts.append(str(year))
            elif scheme['year_format'] == 'YY':
                parts.append(str(year)[-2:])

        # Entity code
        if scheme['include_entity_code'] and entity:
            parts.append(entity['entity_code'])

        # Branch code
        if scheme['include_branch_code']:
            pass  # Would need branch info

        # Sequence
        if scheme['sequence_format'] == 'zero_padded':
            seq_str = str(new_sequence).zfill(scheme['sequence_length'])
        else:
            seq_str = str(new_sequence)

        parts.append(seq_str)

        # Suffix
        if scheme['suffix']:
            parts.append(scheme['suffix'])

        result_number = scheme['separator'].join(parts)

        # Update sequence
        conn.execute("""
            UPDATE entity_numbering_schemes SET
                current_sequence = ?,
                last_used_number = ?,
                last_used_date = DATE('now')
            WHERE id = ?
        """, (new_sequence, result_number, scheme['id']))

        conn.commit()
        return result_number
    finally:
        conn.close()


def create_numbering_scheme(data: Dict) -> int:
    """Create a new numbering scheme."""
    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO entity_numbering_schemes (
                entity_id, group_id, branch_id, document_type, scheme_code,
                scheme_name, prefix, prefix_type, include_group_code,
                include_entity_code, include_branch_code, include_site_code,
                include_year, include_month, include_day, year_format,
                sequence_length, sequence_format, suffix, separator,
                reset_frequency, is_active, notes, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('entity_id'), data.get('group_id'), data.get('branch_id'),
            data.get('document_type'), data.get('scheme_code'),
            data.get('scheme_name'), data.get('prefix'), data.get('prefix_type', 'fixed'),
            data.get('include_group_code', 0), data.get('include_entity_code', 1),
            data.get('include_branch_code', 0), data.get('include_site_code', 0),
            data.get('include_year', 1), data.get('include_month', 0),
            data.get('include_day', 0), data.get('year_format', 'YYYY'),
            data.get('sequence_length', 5), data.get('sequence_format', 'zero_padded'),
            data.get('suffix'), data.get('separator', '-'),
            data.get('reset_frequency', 'yearly'), data.get('is_active', 1),
            data.get('notes'), data.get('created_by')
        ))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


# =============================================================================
# INTERCOMPANY RULES
# =============================================================================

def get_intercompany_rules(entity_id: int = None) -> List[Dict]:
    """Get intercompany rules."""
    conn = get_db()
    try:
        query = """
            SELECT r.*,
                   e1.legal_name as source_entity_name,
                   e1.entity_code as source_entity_code,
                   e2.legal_name as target_entity_name,
                   e2.entity_code as target_entity_code
            FROM intercompany_rules r
            LEFT JOIN legal_entities e1 ON r.source_entity_id = e1.id
            LEFT JOIN legal_entities e2 ON r.target_entity_id = e2.id
            WHERE 1=1
        """
        params = []
        if entity_id:
            query += " AND (r.source_entity_id = ? OR r.target_entity_id = ?)"
            params.extend([entity_id, entity_id])
        query += " ORDER BY r.rule_name"
        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def create_intercompany_rule(data: Dict) -> int:
    """Create a new intercompany rule."""
    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO intercompany_rules (
                rule_code, rule_name, rule_type, description,
                source_entity_id, target_entity_id, relationship_type,
                transaction_types, pricing_policy, markup_percentage,
                discount_percentage, payment_terms, credit_limit,
                approval_workflow_id, is_auto_approve, auto_approve_conditions,
                is_active, priority, notes, metadata, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('rule_code'), data.get('rule_name'), data.get('rule_type'),
            data.get('description'), data.get('source_entity_id'),
            data.get('target_entity_id'), data.get('relationship_type'),
            json.dumps(data.get('transaction_types', [])),
            data.get('pricing_policy'), data.get('markup_percentage'),
            data.get('discount_percentage'), data.get('payment_terms'),
            data.get('credit_limit', 0), data.get('approval_workflow_id'),
            data.get('is_auto_approve', 0),
            json.dumps(data.get('auto_approve_conditions', {})),
            data.get('is_active', 1), data.get('priority', 0),
            data.get('notes'), json.dumps(data.get('metadata', {})),
            data.get('created_by')
        ))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


# =============================================================================
# SHARED MASTER DATA RULES
# =============================================================================

def get_shared_data_rules(data_type: str = None, scope: str = None) -> List[Dict]:
    """Get shared master data rules."""
    conn = get_db()
    try:
        query = """
            SELECT r.*,
                   e.legal_name as entity_name,
                   g.legal_name as group_name
            FROM shared_master_rules r
            LEFT JOIN legal_entities e ON r.entity_id = e.id
            LEFT JOIN entity_groups g ON r.group_id = g.id
            WHERE 1=1
        """
        params = []
        if data_type:
            query += " AND r.data_type = ?"
            params.append(data_type)
        if scope:
            query += " AND r.scope = ?"
            params.append(scope)
        query += " ORDER BY r.data_type, r.scope"
        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def update_shared_data_rule(rule_id: int, data: Dict) -> bool:
    """Update a shared data rule."""
    conn = get_db()
    try:
        conn.execute("""
            UPDATE shared_master_rules SET
                visibility = COALESCE(?, visibility),
                sharing_policy = COALESCE(?, sharing_policy),
                allowed_entity_ids = COALESCE(?, allowed_entity_ids),
                inheritance_mode = COALESCE(?, inheritance_mode),
                override_allowed = COALESCE(?, override_allowed),
                override_requires_approval = COALESCE(?, override_requires_approval),
                is_active = COALESCE(?, is_active),
                priority = COALESCE(?, priority),
                description = COALESCE(?, description),
                metadata = COALESCE(?, metadata),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get('visibility'), data.get('sharing_policy'),
            json.dumps(data.get('allowed_entity_ids')) if data.get('allowed_entity_ids') else None,
            data.get('inheritance_mode'), data.get('override_allowed'),
            data.get('override_requires_approval'), data.get('is_active'),
            data.get('priority'), data.get('description'),
            json.dumps(data.get('metadata')) if data.get('metadata') else None,
            rule_id
        ))
        conn.commit()
        return True
    finally:
        conn.close()


# =============================================================================
# AUDIT LOGGING
# =============================================================================

def log_entity_audit(entity_id: int = None, entity_type: str = None,
                     action: str = None, user_id: int = None,
                     field_name: str = None, old_value: str = None,
                     new_value: str = None, reason: str = None,
                     notes: str = None, source: str = 'ui',
                     group_id: int = None, branch_id: int = None,
                     site_id: int = None, **kwargs) -> int:
    """Log an entity audit record."""
    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO entity_audit_records (
                entity_id, group_id, branch_id, site_id,
                entity_type, action, field_name, old_value, new_value,
                user_id, reason, notes, source, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entity_id, group_id, branch_id, site_id,
            entity_type, action, field_name, old_value, new_value,
            user_id, reason, notes, source,
            json.dumps(kwargs.get('metadata', {}))
        ))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_entity_audit_log(entity_id: int = None, group_id: int = None,
                          entity_type: str = None, action: str = None,
                          user_id: int = None, limit: int = 100) -> List[Dict]:
    """Get entity audit log."""
    conn = get_db()
    try:
        query = """
            SELECT a.*,
                   e.legal_name as entity_name,
                   g.legal_name as group_name,
                   b.branch_name,
                   s.site_name,
                   u.username as user_name
            FROM entity_audit_records a
            LEFT JOIN legal_entities e ON a.entity_id = e.id
            LEFT JOIN entity_groups g ON a.group_id = g.id
            LEFT JOIN entity_branches b ON a.branch_id = b.id
            LEFT JOIN entity_sites s ON a.site_id = s.id
            LEFT JOIN users u ON a.user_id = u.id
            WHERE 1=1
        """
        params = []
        if entity_id:
            query += " AND a.entity_id = ?"
            params.append(entity_id)
        if group_id:
            query += " AND a.group_id = ?"
            params.append(group_id)
        if entity_type:
            query += " AND a.entity_type = ?"
            params.append(entity_type)
        if action:
            query += " AND a.action = ?"
            params.append(action)
        if user_id:
            query += " AND a.user_id = ?"
            params.append(user_id)
        query += " ORDER BY a.created_at DESC LIMIT ?"
        params.append(limit)
        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


# =============================================================================
# ENTITY SETTINGS
# =============================================================================

def get_entity_settings(entity_id: int, category: str = None) -> Dict:
    """Get entity settings."""
    conn = get_db()
    try:
        query = "SELECT * FROM entity_settings WHERE entity_id = ? AND is_active = 1"
        params = [entity_id]
        if category:
            query += " AND category = ?"
            params.append(category)
        settings = {}
        for row in conn.execute(query, params).fetchall():
            settings[row['setting_key']] = row['setting_value']
        return settings
    finally:
        conn.close()


def update_entity_setting(entity_id: int, key: str, value: str,
                           category: str = 'General') -> bool:
    """Update an entity setting."""
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO entity_settings (entity_id, setting_key, setting_value, category)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(entity_id, setting_key) DO UPDATE SET
                setting_value = excluded.setting_value,
                category = COALESCE(excluded.category, entity_settings.category),
                updated_at = CURRENT_TIMESTAMP
        """, (entity_id, key, value, category))
        conn.commit()
        return True
    finally:
        conn.close()


# =============================================================================
# DASHBOARD STATISTICS
# =============================================================================

def get_entity_dashboard_stats(group_id: int = None, entity_id: int = None) -> Dict:
    """Get comprehensive entity dashboard statistics."""
    conn = get_db()
    try:
        stats = {}

        # Group counts
        stats['total_groups'] = conn.execute("""
            SELECT COUNT(*) as cnt FROM entity_groups WHERE is_active = 1
        """).fetchone()['cnt']

        # Entity counts by status
        entity_query = "SELECT status, COUNT(*) as cnt FROM legal_entities WHERE is_active = 1"
        if group_id:
            entity_query += f" AND parent_group_id = {group_id}"
        if entity_id:
            entity_query += f" AND id = {entity_id}"
        entity_query += " GROUP BY status"

        stats['entity_status'] = {row['status']: row['cnt'] for row in
                                   conn.execute(entity_query).fetchall()}
        stats['total_entities'] = sum(stats['entity_status'].values())

        # Branch counts
        branch_query = """
            SELECT COUNT(*) as cnt FROM entity_branches
            JOIN legal_entities ON entity_branches.entity_id = legal_entities.id
            WHERE entity_branches.is_active = 1
        """
        if group_id:
            branch_query += f" AND legal_entities.parent_group_id = {group_id}"
        if entity_id:
            branch_query += f" AND legal_entities.id = {entity_id}"
        stats['total_branches'] = conn.execute(branch_query).fetchone()['cnt']

        # Site counts
        site_query = """
            SELECT COUNT(*) as cnt FROM entity_sites
            JOIN legal_entities ON entity_sites.entity_id = legal_entities.id
            WHERE entity_sites.is_active = 1
        """
        if group_id:
            site_query += f" AND legal_entities.parent_group_id = {group_id}"
        if entity_id:
            site_query += f" AND legal_entities.id = {entity_id}"
        stats['total_sites'] = conn.execute(site_query).fetchone()['cnt']

        # Access counts
        access_query = """
            SELECT COUNT(DISTINCT user_id) as cnt FROM entity_access
            JOIN legal_entities ON entity_access.entity_id = legal_entities.id
            WHERE entity_access.is_active = 1
        """
        if group_id:
            access_query += f" AND legal_entities.parent_group_id = {group_id}"
        if entity_id:
            access_query += f" AND entity_access.entity_id = {entity_id}"
        stats['total_users_with_access'] = conn.execute(access_query).fetchone()['cnt']

        # Relationship counts
        rel_query = "SELECT COUNT(*) as cnt FROM entity_relationships WHERE is_active = 1"
        if entity_id:
            rel_query += f" AND (source_entity_id = {entity_id} OR target_entity_id = {entity_id})"
        stats['total_relationships'] = conn.execute(rel_query).fetchone()['cnt']

        # Recent activity (last 7 days)
        stats['recent_changes'] = conn.execute("""
            SELECT COUNT(*) as cnt FROM entity_audit_records
            WHERE created_at >= datetime('now', '-7 days')
        """).fetchone()['cnt']

        # Pending change requests
        stats['pending_changes'] = conn.execute("""
            SELECT COUNT(*) as cnt FROM entity_change_requests
            WHERE status = 'pending'
        """).fetchone()['cnt']

        # Intercompany transactions (if intercompany_transactions table exists)
        try:
            ic_query = """
                SELECT COUNT(*) as cnt FROM intercompany_transactions
                WHERE status IN ('pending', 'approved')
            """
            stats['intercompany_pending'] = conn.execute(ic_query).fetchone()['cnt']
        except:
            stats['intercompany_pending'] = 0

        return stats
    finally:
        conn.close()


def get_entity_hierarchy(group_id: int = None) -> Dict:
    """Get complete entity hierarchy tree."""
    conn = get_db()
    try:
        hierarchy = {}

        # Get all groups
        groups = get_all_groups(active_only=True)
        for group in groups:
            if group_id and group['id'] != group_id:
                continue
            hierarchy[group['id']] = {
                'type': 'group',
                'data': group,
                'entities': {}
            }

            # Get entities under this group
            entities = get_all_entities(active_only=True, group_id=group['id'])
            for entity in entities:
                hierarchy[group['id']]['entities'][entity['id']] = {
                    'type': 'entity',
                    'data': entity,
                    'branches': {}
                }

                # Get branches under this entity
                branches = get_entity_branches(entity['id'], active_only=True)
                for branch in branches:
                    hierarchy[group['id']]['entities'][entity['id']]['branches'][branch['id']] = {
                        'type': 'branch',
                        'data': branch,
                        'sites': {}
                    }

                    # Get sites under this branch
                    sites = get_branch_sites(branch['id'], active_only=True)
                    for site in sites:
                        hierarchy[group['id']]['entities'][entity['id']]['branches'][branch['id']]['sites'][site['id']] = {
                            'type': 'site',
                            'data': site
                        }

        return hierarchy
    finally:
        conn.close()


# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def check_entity_code_unique(entity_code: str, exclude_id: int = None) -> bool:
    """Check if entity code is unique."""
    conn = get_db()
    try:
        query = "SELECT COUNT(*) as cnt FROM legal_entities WHERE entity_code = ?"
        params = [entity_code]
        if exclude_id:
            query += " AND id != ?"
            params.append(exclude_id)
        return conn.execute(query, params).fetchone()['cnt'] == 0
    finally:
        conn.close()


def check_group_code_unique(group_code: str, exclude_id: int = None) -> bool:
    """Check if group code is unique."""
    conn = get_db()
    try:
        query = "SELECT COUNT(*) as cnt FROM entity_groups WHERE group_code = ?"
        params = [group_code]
        if exclude_id:
            query += " AND id != ?"
            params.append(exclude_id)
        return conn.execute(query, params).fetchone()['cnt'] == 0
    finally:
        conn.close()


def check_branch_code_unique(branch_code: str, exclude_id: int = None) -> bool:
    """Check if branch code is unique."""
    conn = get_db()
    try:
        query = "SELECT COUNT(*) as cnt FROM entity_branches WHERE branch_code = ?"
        params = [branch_code]
        if exclude_id:
            query += " AND id != ?"
            params.append(exclude_id)
        return conn.execute(query, params).fetchone()['cnt'] == 0
    finally:
        conn.close()


def check_site_code_unique(site_code: str, exclude_id: int = None) -> bool:
    """Check if site code is unique."""
    conn = get_db()
    try:
        query = "SELECT COUNT(*) as cnt FROM entity_sites WHERE site_code = ?"
        params = [site_code]
        if exclude_id:
            query += " AND id != ?"
            params.append(exclude_id)
        return conn.execute(query, params).fetchone()['cnt'] == 0
    finally:
        conn.close()


# =============================================================================
# DATA LOOKUP HELPERS
# =============================================================================

def search_entities(query: str, limit: int = 20) -> List[Dict]:
    """Search entities by name, code, or registration."""
    conn = get_db()
    try:
        search_pattern = f"%{query}%"
        return [dict(row) for row in conn.execute("""
            SELECT e.*, g.legal_name as group_name
            FROM legal_entities e
            LEFT JOIN entity_groups g ON e.parent_group_id = g.id
            WHERE e.is_active = 1
            AND (e.legal_name LIKE ? OR e.entity_code LIKE ? OR e.registration_number LIKE ?)
            LIMIT ?
        """, (search_pattern, search_pattern, search_pattern, limit)).fetchall()]
    finally:
        conn.close()


def search_branches(query: str, entity_id: int = None, limit: int = 20) -> List[Dict]:
    """Search branches by name or code."""
    conn = get_db()
    try:
        search_pattern = f"%{query}%"
        sql = """
            SELECT b.*, e.legal_name as entity_name
            FROM entity_branches b
            JOIN legal_entities e ON b.entity_id = e.id
            WHERE b.is_active = 1
            AND (b.branch_name LIKE ? OR b.branch_code LIKE ?)
        """
        params = [search_pattern, search_pattern]
        if entity_id:
            sql += " AND b.entity_id = ?"
            params.append(entity_id)
        sql += " LIMIT ?"
        params.append(limit)
        return [dict(row) for row in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def search_sites(query: str, entity_id: int = None, limit: int = 20) -> List[Dict]:
    """Search sites by name or code."""
    conn = get_db()
    try:
        search_pattern = f"%{query}%"
        sql = """
            SELECT s.*, e.legal_name as entity_name, b.branch_name
            FROM entity_sites s
            JOIN legal_entities e ON s.entity_id = e.id
            LEFT JOIN entity_branches b ON s.branch_id = b.id
            WHERE s.is_active = 1
            AND (s.site_name LIKE ? OR s.site_code LIKE ?)
        """
        params = [search_pattern, search_pattern]
        if entity_id:
            sql += " AND s.entity_id = ?"
            params.append(entity_id)
        sql += " LIMIT ?"
        params.append(limit)
        return [dict(row) for row in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def get_entities_by_group(group_id: int) -> List[Dict]:
    """Get all entities under a group."""
    conn = get_db()
    try:
        return [dict(row) for row in conn.execute("""
            SELECT e.*, (SELECT COUNT(*) FROM entity_branches WHERE entity_id = e.id AND is_active = 1) as branch_count
            FROM legal_entities e
            WHERE e.parent_group_id = ? AND e.is_active = 1
            ORDER BY e.legal_name
        """, (group_id,)).fetchall()]
    finally:
        conn.close()


def get_entity_breadcrumb(entity_id: int) -> List[Dict]:
    """Get breadcrumb path for an entity."""
    breadcrumb = []
    entity = get_entity_by_id(entity_id)
    if not entity:
        return breadcrumb

    # Add group
    if entity.get('parent_group_id'):
        group = get_group_by_id(entity['parent_group_id'])
        if group:
            breadcrumb.append({'type': 'group', 'id': group['id'], 'name': group['legal_name']})

    # Add self
    breadcrumb.append({'type': 'entity', 'id': entity['id'], 'name': entity['legal_name']})

    return breadcrumb
