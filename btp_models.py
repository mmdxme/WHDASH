"""
BTP (Business Technology Platform) Module Database Models
============================================================
Comprehensive database models for the Technology Platform module.

Tables:
- btp_connectors: Integration connector registry
- btp_connector_logs: Connector execution logs
- btp_integration_flows: Integration flow definitions
- btp_flow_versions: Flow version history
- btp_mappings: Data mapping definitions
- btp_mapping_versions: Mapping version history
- btp_transformation_rules: Transformation rule definitions
- btp_file_templates: File import/export templates
- btp_jobs: Job definitions and history
- btp_job_attempts: Individual job attempt records
- btp_retry_queue: Retry queue entries
- btp_dead_letters: Dead letter queue entries
- btp_events: Event registry
- btp_event_subscriptions: Event subscription definitions
- btp_api_catalog: API endpoint catalog
- btp_api_versions: API version history
- btp_api_clients: API client applications
- btp_api_policies: API policies and rate limits
- btp_feature_flags: Feature flag definitions
- btp_environment_profiles: Environment configuration profiles
- btp_ai_providers: AI provider definitions
- btp_provider_usage_logs: AI provider usage logs
- btp_incidents: Platform incidents
- btp_change_requests: Change requests
- btp_export_history: Export history records
- btp_data_quality_checks: Data quality check records
- btp_reconciliations: Reconciliation records
- btp_extension_fields: Custom field definitions
- btp_extension_rules: Automation rules
- btp_secret_references: Secret references
- btp_platform_settings: Platform settings
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from functools import wraps

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'warehouse.db'))


def get_db():
    """Get database connection with Row factory for dict-like access."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# =============================================================================
# BTP TABLE DEFINITIONS
# =============================================================================

BTP_TABLES = [
    # -------------------------------------------------------------------------
    # 1. BTP Connectors
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_connectors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL,
        direction TEXT DEFAULT 'bidirectional',
        source_system TEXT,
        target_system TEXT,
        auth_type TEXT,
        base_url TEXT,
        file_format TEXT,
        owner TEXT,
        team TEXT,
        company_id INTEGER,
        environment TEXT DEFAULT 'production',
        status TEXT DEFAULT 'active',
        retry_policy TEXT DEFAULT '{"max_retries": 3, "retry_interval": 60}',
        timeout INTEGER DEFAULT 30,
        is_active INTEGER DEFAULT 1,
        health_score REAL DEFAULT 100.0,
        last_success TEXT,
        last_failure TEXT,
        notes TEXT,
        tags TEXT,
        related_flow_room_id TEXT,
        related_document_ids TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 2. Connector Logs
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_connector_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        connector_id INTEGER NOT NULL,
        run_id TEXT,
        status TEXT,
        direction TEXT,
        request_payload TEXT,
        response_payload TEXT,
        error_message TEXT,
        duration_ms INTEGER,
        http_status_code INTEGER,
        attempted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (connector_id) REFERENCES btp_connectors(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 3. Integration Flows
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_integration_flows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flow_name TEXT NOT NULL,
        flow_code TEXT UNIQUE NOT NULL,
        connector_ids TEXT,
        trigger_type TEXT DEFAULT 'manual',
        schedule TEXT,
        source_entity TEXT,
        target_entity TEXT,
        mapping_version TEXT,
        transformation_set TEXT,
        validation_set TEXT,
        pre_checks TEXT,
        post_actions TEXT,
        notification_rules TEXT,
        retry_rules TEXT,
        requires_approval INTEGER DEFAULT 0,
        status TEXT DEFAULT 'draft',
        last_run TEXT,
        next_run TEXT,
        sla_duration_minutes INTEGER,
        owner TEXT,
        environment TEXT DEFAULT 'production',
        related_module TEXT,
        company_id INTEGER,
        created_by_user_id INTEGER,
        updated_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 4. Flow Versions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_flow_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flow_id INTEGER NOT NULL,
        version_number INTEGER NOT NULL,
        flow_config TEXT,
        status TEXT DEFAULT 'draft',
        changelog TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (flow_id) REFERENCES btp_integration_flows(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 5. Data Mappings
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_mappings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        source_type TEXT,
        target_type TEXT,
        field_mappings TEXT,
        default_values TEXT,
        conditional_rules TEXT,
        validation_rules TEXT,
        status TEXT DEFAULT 'draft',
        version INTEGER DEFAULT 1,
        mapping_config TEXT,
        last_test_at TEXT,
        last_success_at TEXT,
        last_failure_at TEXT,
        owner TEXT,
        reviewer TEXT,
        approver TEXT,
        related_connector_id INTEGER,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 6. Mapping Versions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_mapping_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mapping_id INTEGER NOT NULL,
        version_number INTEGER NOT NULL,
        field_mappings TEXT,
        status TEXT DEFAULT 'draft',
        changelog TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (mapping_id) REFERENCES btp_mappings(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 7. Transformation Rules
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_transformation_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        rule_type TEXT NOT NULL,
        source_field TEXT,
        target_field TEXT,
        transformation_logic TEXT,
        parameters TEXT,
        is_active INTEGER DEFAULT 1,
        mapping_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 8. File Templates
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_file_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        template_type TEXT NOT NULL,
        file_format TEXT NOT NULL,
        columns_definition TEXT,
        header_row INTEGER DEFAULT 1,
        column_order TEXT,
        filter_config TEXT,
        sort_config TEXT,
        sample_data TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 9. Jobs
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT UNIQUE NOT NULL,
        job_type TEXT NOT NULL,
        name TEXT NOT NULL,
        flow_id INTEGER,
        connector_id INTEGER,
        related_entity TEXT,
        trigger_source TEXT,
        schedule TEXT,
        run_mode TEXT DEFAULT 'manual',
        priority INTEGER DEFAULT 5,
        status TEXT DEFAULT 'queued',
        queued_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        started_at DATETIME,
        finished_at DATETIME,
        duration_seconds INTEGER,
        attempts INTEGER DEFAULT 0,
        max_attempts INTEGER DEFAULT 3,
        last_error TEXT,
        owner TEXT,
        environment TEXT DEFAULT 'production',
        company_id INTEGER,
        payload_summary TEXT,
        output_files TEXT,
        related_flow_thread_id TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 10. Job Attempts
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_job_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        attempt_number INTEGER NOT NULL,
        status TEXT,
        error_message TEXT,
        payload TEXT,
        result TEXT,
        started_at DATETIME,
        finished_at DATETIME,
        duration_ms INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES btp_jobs(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 11. Retry Queue
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_retry_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        connector_id INTEGER,
        reason TEXT,
        payload_snapshot TEXT,
        retry_count INTEGER DEFAULT 0,
        max_retries INTEGER DEFAULT 5,
        next_retry_at DATETIME,
        status TEXT DEFAULT 'pending',
        assigned_to TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES btp_jobs(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 12. Dead Letter Queue
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_dead_letters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        connector_id INTEGER,
        event_type TEXT,
        reason TEXT,
        original_payload TEXT,
        failure_reason TEXT,
        attempts INTEGER DEFAULT 0,
        last_attempt_at DATETIME,
        status TEXT DEFAULT 'failed',
        resolution_notes TEXT,
        resolved_by_user_id INTEGER,
        resolved_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 13. Events
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        category TEXT,
        payload_schema TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 14. Event Subscriptions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_event_subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        subscriber_name TEXT NOT NULL,
        endpoint_url TEXT,
        webhook_url TEXT,
        delivery_mode TEXT DEFAULT 'webhook',
        retry_policy TEXT,
        headers_config TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 15. API Catalog
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_api_catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        api_name TEXT NOT NULL,
        api_code TEXT UNIQUE NOT NULL,
        version TEXT DEFAULT 'v1',
        base_path TEXT,
        description TEXT,
        endpoint_group TEXT,
        scopes TEXT,
        auth_type TEXT,
        rate_limit_requests INTEGER,
        rate_limit_period TEXT DEFAULT 'minute',
        ip_rules TEXT,
        is_active INTEGER DEFAULT 1,
        is_deprecated INTEGER DEFAULT 0,
        deprecation_notice TEXT,
        owner_team TEXT,
        swagger_spec TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 16. API Versions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_api_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        api_id INTEGER NOT NULL,
        version TEXT NOT NULL,
        spec_content TEXT,
        changelog TEXT,
        status TEXT DEFAULT 'active',
        released_at DATETIME,
        deprecated_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (api_id) REFERENCES btp_api_catalog(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 17. API Clients
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_api_clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT NOT NULL,
        client_code TEXT UNIQUE NOT NULL,
        api_id INTEGER,
        app_type TEXT,
        scopes TEXT,
        redirect_uris TEXT,
        owner_user_id INTEGER,
        team TEXT,
        company_id INTEGER,
        status TEXT DEFAULT 'active',
        key_prefix TEXT,
        key_hash TEXT,
        last_used_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 18. API Policies
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_api_policies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        policy_name TEXT NOT NULL,
        policy_code TEXT UNIQUE NOT NULL,
        policy_type TEXT NOT NULL,
        api_id INTEGER,
        rules_config TEXT,
        priority INTEGER DEFAULT 100,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 19. Feature Flags
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_feature_flags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flag_key TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        flag_type TEXT DEFAULT 'boolean',
        default_value TEXT,
        current_value TEXT,
        environments TEXT,
        owner_team TEXT,
        requires_approval INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 20. Environment Profiles
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_environment_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_name TEXT NOT NULL,
        profile_code TEXT UNIQUE NOT NULL,
        environment_type TEXT,
        description TEXT,
        config_json TEXT,
        is_default INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 21. AI Providers
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_ai_providers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        provider_name TEXT NOT NULL,
        provider_code TEXT UNIQUE NOT NULL,
        provider_type TEXT NOT NULL,
        api_endpoint TEXT,
        auth_type TEXT,
        credentials_ref TEXT,
        model_name TEXT,
        max_tokens INTEGER,
        usage_limit_monthly INTEGER,
        current_usage_monthly INTEGER DEFAULT 0,
        cost_per_token REAL DEFAULT 0.0,
        is_active INTEGER DEFAULT 1,
        owner_team TEXT,
        last_test_at DATETIME,
        status TEXT DEFAULT 'active',
        config_json TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 21b. AI Chats
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_ai_chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT,
        provider_id INTEGER,
        message_count INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (provider_id) REFERENCES btp_ai_providers(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 21c. AI Messages
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_ai_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        provider_id INTEGER,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        tokens_used INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (chat_id) REFERENCES btp_ai_chats(id) ON DELETE CASCADE,
        FOREIGN KEY (provider_id) REFERENCES btp_ai_providers(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 22. Provider Usage Logs
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_provider_usage_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        provider_id INTEGER NOT NULL,
        request_type TEXT,
        model_used TEXT,
        tokens_used INTEGER,
        estimated_cost REAL,
        response_time_ms INTEGER,
        status TEXT,
        error_message TEXT,
        user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (provider_id) REFERENCES btp_ai_providers(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 23. Incidents
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        severity TEXT DEFAULT 'medium',
        category TEXT,
        related_connector_id INTEGER,
        related_job_id INTEGER,
        related_entity_type TEXT,
        related_entity_id INTEGER,
        status TEXT DEFAULT 'open',
        assigned_to TEXT,
        assigned_team TEXT,
        flow_thread_id TEXT,
        resolution_notes TEXT,
        resolved_by_user_id INTEGER,
        resolved_at DATETIME,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 24. Change Requests
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_change_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cr_number TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        change_type TEXT,
        priority TEXT DEFAULT 'medium',
        status TEXT DEFAULT 'draft',
        risk_level TEXT,
        impact_assessment TEXT,
        rollback_plan TEXT,
        affected_items TEXT,
        approval_required INTEGER DEFAULT 1,
        approvers TEXT,
        approved_by_user_id INTEGER,
        approved_at DATETIME,
        implemented_by_user_id INTEGER,
        implemented_at DATETIME,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 25. Export History
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_export_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        export_name TEXT NOT NULL,
        export_type TEXT NOT NULL,
        file_name TEXT,
        format TEXT NOT NULL,
        row_count INTEGER,
        columns_included TEXT,
        filter_summary TEXT,
        user_id INTEGER,
        user_name TEXT,
        company_id INTEGER,
        environment TEXT,
        file_size_bytes INTEGER,
        download_url TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 26. Data Quality Checks
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_data_quality_checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        check_name TEXT NOT NULL,
        check_code TEXT UNIQUE NOT NULL,
        entity_type TEXT,
        check_type TEXT,
        validation_rule TEXT,
        threshold_warning TEXT,
        threshold_critical TEXT,
        last_run_at DATETIME,
        last_result TEXT,
        record_count INTEGER,
        error_count INTEGER,
        status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 27. Reconciliations
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_reconciliations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reconciliation_name TEXT NOT NULL,
        reconciliation_code TEXT UNIQUE NOT NULL,
        source_system TEXT,
        target_system TEXT,
        match_fields TEXT,
        tolerance_percent REAL DEFAULT 0.0,
        last_run_at DATETIME,
        records_matched INTEGER,
        records_mismatched INTEGER,
        status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 28. Extension Fields
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_extension_fields (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        field_name TEXT NOT NULL,
        field_code TEXT UNIQUE NOT NULL,
        entity_type TEXT NOT NULL,
        field_type TEXT DEFAULT 'string',
        default_value TEXT,
        is_required INTEGER DEFAULT 0,
        display_order INTEGER DEFAULT 0,
        searchable INTEGER DEFAULT 1,
        reportable INTEGER DEFAULT 1,
        exportable INTEGER DEFAULT 1,
        visible_to_roles TEXT,
        translation_labels TEXT,
        section_placement TEXT,
        audit_flag INTEGER DEFAULT 0,
        flow_mention_flag INTEGER DEFAULT 0,
        workflow_hook_flag INTEGER DEFAULT 0,
        validation_rules TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 29. Extension Rules
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_extension_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_name TEXT NOT NULL,
        rule_code TEXT UNIQUE NOT NULL,
        rule_type TEXT NOT NULL,
        trigger_event TEXT,
        conditions TEXT,
        actions TEXT,
        is_active INTEGER DEFAULT 1,
        priority INTEGER DEFAULT 100,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 30. Secret References
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_secret_references (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        secret_name TEXT NOT NULL,
        secret_code TEXT UNIQUE NOT NULL,
        secret_type TEXT NOT NULL,
        masked_value TEXT,
        holder_user_id INTEGER,
        environment TEXT,
        description TEXT,
        expires_at DATETIME,
        is_active INTEGER DEFAULT 1,
        last_rotated_at DATETIME,
        rotation_policy_days INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 31. Platform Settings
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_platform_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_key TEXT UNIQUE NOT NULL,
        setting_value TEXT,
        setting_type TEXT,
        category TEXT,
        description TEXT,
        is_encrypted INTEGER DEFAULT 0,
        updated_by_user_id INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 32. Webhook Deliveries
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_webhook_deliveries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        webhook_id INTEGER,
        subscription_id INTEGER,
        event_type TEXT,
        payload TEXT,
        delivery_status TEXT DEFAULT 'pending',
        response_code INTEGER,
        response_body TEXT,
        attempts INTEGER DEFAULT 0,
        next_retry_at DATETIME,
        delivered_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 33. Platform Audit Logs
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS btp_audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT,
        entity_id INTEGER,
        action TEXT,
        user_id INTEGER,
        user_name TEXT,
        changes TEXT,
        ip_address TEXT,
        user_agent TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
]


# =============================================================================
# BTP MODELS (Dataclasses)
# =============================================================================

@dataclass
class BTPConnector:
    id: int = 0
    name: str = ""
    code: str = ""
    category: str = ""
    direction: str = "bidirectional"
    source_system: str = ""
    target_system: str = ""
    auth_type: str = ""
    base_url: str = ""
    file_format: str = ""
    owner: str = ""
    team: str = ""
    company_id: int = 0
    environment: str = "production"
    status: str = "active"
    retry_policy: str = '{"max_retries": 3, "retry_interval": 60}'
    timeout: int = 30
    is_active: int = 1
    health_score: float = 100.0
    last_success: str = ""
    last_failure: str = ""
    notes: str = ""
    tags: str = ""
    related_flow_room_id: str = ""
    related_document_ids: str = ""
    created_by_user_id: int = 0
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class BTPIntegrationFlow:
    id: int = 0
    flow_name: str = ""
    flow_code: str = ""
    connector_ids: str = ""
    trigger_type: str = "manual"
    schedule: str = ""
    source_entity: str = ""
    target_entity: str = ""
    mapping_version: str = ""
    transformation_set: str = ""
    validation_set: str = ""
    pre_checks: str = ""
    post_actions: str = ""
    notification_rules: str = ""
    retry_rules: str = ""
    requires_approval: int = 0
    status: str = "draft"
    last_run: str = ""
    next_run: str = ""
    sla_duration_minutes: int = 0
    owner: str = ""
    environment: str = "production"
    related_module: str = ""
    company_id: int = 0
    created_by_user_id: int = 0
    updated_by_user_id: int = 0
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class BTPJob:
    id: int = 0
    job_id: str = ""
    job_type: str = ""
    name: str = ""
    flow_id: int = 0
    connector_id: int = 0
    related_entity: str = ""
    trigger_source: str = ""
    schedule: str = ""
    run_mode: str = "manual"
    priority: int = 5
    status: str = "queued"
    queued_at: str = ""
    started_at: str = ""
    finished_at: str = ""
    duration_seconds: int = 0
    attempts: int = 0
    max_attempts: int = 3
    last_error: str = ""
    owner: str = ""
    environment: str = "production"
    company_id: int = 0
    payload_summary: str = ""
    output_files: str = ""
    related_flow_thread_id: str = ""
    created_by_user_id: int = 0
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class BTPIncident:
    id: int = 0
    incident_code: str = ""
    title: str = ""
    description: str = ""
    severity: str = "medium"
    category: str = ""
    related_connector_id: int = 0
    related_job_id: int = 0
    related_entity_type: str = ""
    related_entity_id: int = 0
    status: str = "open"
    assigned_to: str = ""
    assigned_team: str = ""
    flow_thread_id: str = ""
    resolution_notes: str = ""
    resolved_by_user_id: int = 0
    resolved_at: str = ""
    created_by_user_id: int = 0
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class BTPFeatureFlag:
    id: int = 0
    flag_key: str = ""
    name: str = ""
    description: str = ""
    flag_type: str = "boolean"
    default_value: str = "false"
    current_value: str = "false"
    environments: str = ""
    owner_team: str = ""
    requires_approval: int = 0
    is_active: int = 1
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def init_btp_tables():
    """Initialize all BTP module tables."""
    db = get_db()
    try:
        for table_sql in BTP_TABLES:
            db.execute(table_sql)
        db.commit()
    finally:
        db.close()


def get_btp_stats() -> Dict:
    """Get BTP module statistics."""
    db = get_db()
    try:
        stats = {}

        # Connector stats
        stats['total_connectors'] = db.execute("SELECT COUNT(*) as c FROM btp_connectors").fetchone()['c']
        stats['active_connectors'] = db.execute("SELECT COUNT(*) as c FROM btp_connectors WHERE is_active = 1").fetchone()['c']
        stats['failed_connectors'] = db.execute("SELECT COUNT(*) as c FROM btp_connectors WHERE last_failure IS NOT NULL AND last_failure > datetime('now', '-24 hours')").fetchone()['c']

        # Job stats
        stats['jobs_today'] = db.execute("SELECT COUNT(*) as c FROM btp_jobs WHERE DATE(created_at) = DATE('now')").fetchone()['c']
        stats['failed_jobs'] = db.execute("SELECT COUNT(*) as c FROM btp_jobs WHERE status = 'failed'").fetchone()['c']
        stats['pending_retries'] = db.execute("SELECT COUNT(*) as c FROM btp_retry_queue WHERE status = 'pending'").fetchone()['c']

        # Flow stats
        stats['total_flows'] = db.execute("SELECT COUNT(*) as c FROM btp_integration_flows").fetchone()['c']
        stats['active_flows'] = db.execute("SELECT COUNT(*) as c FROM btp_integration_flows WHERE status = 'active'").fetchone()['c']

        # API stats
        stats['total_apis'] = db.execute("SELECT COUNT(*) as c FROM btp_api_catalog").fetchone()['c']
        stats['api_requests_today'] = db.execute("SELECT COUNT(*) as c FROM btp_api_clients WHERE DATE(last_used_at) = DATE('now')").fetchone()['c']

        # Feature flags
        stats['active_flags'] = db.execute("SELECT COUNT(*) as c FROM btp_feature_flags WHERE is_active = 1").fetchone()['c']

        # Incidents
        stats['open_incidents'] = db.execute("SELECT COUNT(*) as c FROM btp_incidents WHERE status = 'open'").fetchone()['c']
        stats['critical_incidents'] = db.execute("SELECT COUNT(*) as c FROM btp_incidents WHERE severity = 'critical' AND status = 'open'").fetchone()['c']

        return stats
    finally:
        db.close()


def get_all_btp_connectors(status=None, category=None) -> List[Dict]:
    """Get all connectors with optional filtering."""
    db = get_db()
    try:
        query = "SELECT * FROM btp_connectors WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)
        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY name"
        return [dict(row) for row in db.execute(query, params).fetchall()]
    finally:
        db.close()


def get_all_btp_jobs(status=None, job_type=None, limit=100) -> List[Dict]:
    """Get all jobs with optional filtering."""
    db = get_db()
    try:
        query = "SELECT * FROM btp_jobs WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)
        if job_type:
            query += " AND job_type = ?"
            params.append(job_type)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        return [dict(row) for row in db.execute(query, params).fetchall()]
    finally:
        db.close()


def get_btp_incidents(status=None, severity=None, limit=100) -> List[Dict]:
    """Get incidents with optional filtering."""
    db = get_db()
    try:
        query = "SELECT * FROM btp_incidents WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)
        if severity:
            query += " AND severity = ?"
            params.append(severity)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        return [dict(row) for row in db.execute(query, params).fetchall()]
    finally:
        db.close()


def get_btp_export_history(limit=50) -> List[Dict]:
    """Get export history."""
    db = get_db()
    try:
        return [dict(row) for row in db.execute(
            "SELECT * FROM btp_export_history ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()]
    finally:
        db.close()


def get_retry_queue_entries(status='pending') -> List[Dict]:
    """Get retry queue entries."""
    db = get_db()
    try:
        return [dict(row) for row in db.execute(
            "SELECT * FROM btp_retry_queue WHERE status = ? ORDER BY created_at DESC", (status,)
        ).fetchall()]
    finally:
        db.close()


def get_dead_letter_entries(status='failed', limit=100) -> List[Dict]:
    """Get dead letter queue entries."""
    db = get_db()
    try:
        return [dict(row) for row in db.execute(
            "SELECT * FROM btp_dead_letters WHERE status = ? ORDER BY created_at DESC LIMIT ?", (status, limit,)
        ).fetchall()]
    finally:
        db.close()


def get_api_catalog_list() -> List[Dict]:
    """Get API catalog entries."""
    db = get_db()
    try:
        return [dict(row) for row in db.execute(
            "SELECT * FROM btp_api_catalog ORDER BY api_name"
        ).fetchall()]
    finally:
        db.close()


def get_api_clients() -> List[Dict]:
    """Get API clients."""
    db = get_db()
    try:
        return [dict(row) for row in db.execute(
            "SELECT * FROM btp_api_clients ORDER BY client_name"
        ).fetchall()]
    finally:
        db.close()


def get_feature_flags() -> List[Dict]:
    """Get all feature flags."""
    db = get_db()
    try:
        return [dict(row) for row in db.execute(
            "SELECT * FROM btp_feature_flags ORDER BY name"
        ).fetchall()]
    finally:
        db.close()


def get_btp_mappings(status=None) -> List[Dict]:
    """Get data mappings."""
    db = get_db()
    try:
        query = "SELECT * FROM btp_mappings"
        params = []

        if status:
            query += " WHERE status = ?"
            params.append(status)

        query += " ORDER BY name"
        return [dict(row) for row in db.execute(query, params).fetchall()]
    finally:
        db.close()


def get_btp_file_templates() -> List[Dict]:
    """Get file templates."""
    db = get_db()
    try:
        return [dict(row) for row in db.execute(
            "SELECT * FROM btp_file_templates ORDER BY name"
        ).fetchall()]
    finally:
        db.close()


def get_btp_event_subscriptions() -> List[Dict]:
    """Get event subscriptions."""
    db = get_db()
    try:
        return [dict(row) for row in db.execute(
            "SELECT * FROM btp_event_subscriptions ORDER BY event_type"
        ).fetchall()]
    finally:
        db.close()


def get_btp_events() -> List[Dict]:
    """Get events."""
    db = get_db()
    try:
        return [dict(row) for row in db.execute(
            "SELECT * FROM btp_events ORDER BY event_type"
        ).fetchall()]
    finally:
        db.close()


def get_ai_providers() -> List[Dict]:
    """Get AI providers."""
    db = get_db()
    try:
        return [dict(row) for row in db.execute(
            "SELECT * FROM btp_ai_providers ORDER BY provider_name"
        ).fetchall()]
    finally:
        db.close()


def get_btp_secret_references() -> List[Dict]:
    """Get secret references."""
    db = get_db()
    try:
        return [dict(row) for row in db.execute(
            "SELECT * FROM btp_secret_references ORDER BY secret_name"
        ).fetchall()]
    finally:
        db.close()


def get_btp_environment_profiles() -> List[Dict]:
    """Get environment profiles."""
    db = get_db()
    try:
        return [dict(row) for row in db.execute(
            "SELECT * FROM btp_environment_profiles ORDER BY profile_name"
        ).fetchall()]
    finally:
        db.close()


def get_btp_extension_fields(entity_type=None) -> List[Dict]:
    """Get extension fields."""
    db = get_db()
    try:
        query = "SELECT * FROM btp_extension_fields"
        params = []

        if entity_type:
            query += " WHERE entity_type = ?"
            params.append(entity_type)

        query += " ORDER BY entity_type, display_order"
        return [dict(row) for row in db.execute(query, params).fetchall()]
    finally:
        db.close()


def get_btp_extension_rules(rule_type=None) -> List[Dict]:
    """Get extension rules."""
    db = get_db()
    try:
        query = "SELECT * FROM btp_extension_rules"
        params = []

        if rule_type:
            query += " WHERE rule_type = ?"
            params.append(rule_type)

        query += " ORDER BY priority DESC"
        return [dict(row) for row in db.execute(query, params).fetchall()]
    finally:
        db.close()


def get_btp_data_quality_checks() -> List[Dict]:
    """Get data quality checks."""
    db = get_db()
    try:
        return [dict(row) for row in db.execute(
            "SELECT * FROM btp_data_quality_checks ORDER BY check_name"
        ).fetchall()]
    finally:
        db.close()


def get_btp_reconciliations() -> List[Dict]:
    """Get reconciliations."""
    db = get_db()
    try:
        return [dict(row) for row in db.execute(
            "SELECT * FROM btp_reconciliations ORDER BY reconciliation_name"
        ).fetchall()]
    finally:
        db.close()


def get_btp_change_requests(status=None) -> List[Dict]:
    """Get change requests."""
    db = get_db()
    try:
        query = "SELECT * FROM btp_change_requests"
        params = []

        if status:
            query += " WHERE status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC"
        return [dict(row) for row in db.execute(query, params).fetchall()]
    finally:
        db.close()


def get_webhook_deliveries(status=None, limit=100) -> List[Dict]:
    """Get webhook deliveries."""
    db = get_db()
    try:
        query = "SELECT * FROM btp_webhook_deliveries WHERE 1=1"
        params = []

        if status:
            query += " AND delivery_status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        return [dict(row) for row in db.execute(query, params).fetchall()]
    finally:
        db.close()


def get_btp_audit_logs(entity_type=None, limit=100) -> List[Dict]:
    """Get audit logs."""
    db = get_db()
    try:
        query = "SELECT * FROM btp_audit_logs WHERE 1=1"
        params = []

        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        return [dict(row) for row in db.execute(query, params).fetchall()]
    finally:
        db.close()


def seed_btp_sample_data():
    """Seed comprehensive sample data for BTP module."""
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM btp_connectors")
        if cursor.fetchone()[0] > 0:
            print("[BTP] Sample data already exists, skipping seed...")
            return

        connectors = [
            ("SAP ERP Connector", "SAP_ERP_001", "ERP", "bidirectional", "SAP ECC", "Warehouse DB", "api_key", "https://sap-api.company.com", "JSON", "Ahmed Hassan", "Integration Team", "production", 95.5, "2026-04-22 08:00:00"),
            ("Salesforce CRM", "SF_CRM_002", "CRM", "bidirectional", "Salesforce", "Internal CRM", "oauth2", "https://salesforce-api.company.com", "JSON", "Sarah Johnson", "Sales Ops", "production", 88.2, "2026-04-22 09:30:00"),
            ("WMS Warehouse System", "WMS_001", "WMS", "bidirectional", "Internal WMS", "ERP", "basic", "https://wms-api.company.com", "JSON", "Mohammed Ali", "Warehouse Team", "production", 99.1, "2026-04-22 10:15:00"),
            ("Email Gateway - SendGrid", "EMAIL_SG_001", "Email", "outbound", "Internal", "SendGrid", "api_key", "https://api.sendgrid.com", "JSON", "Fatima Zahra", "IT Team", "production", 100.0, "2026-04-22 07:45:00"),
            ("SMS Gateway - Twilio", "SMS_TW_001", "SMS", "outbound", "Internal", "Twilio", "api_key", "https://api.twilio.com", "JSON", "Omar Khalid", "IT Team", "production", 97.8, "2026-04-22 08:30:00"),
            ("Finance System - QuickBooks", "FIN_QB_001", "Finance", "bidirectional", "QuickBooks Online", "ERP", "oauth2", "https://quickbooks-api.company.com", "JSON", "Youssef Ibrahim", "Finance Team", "staging", 75.0, "2026-04-21 16:00:00"),
            ("HR System - Workday", "HR_WD_001", "HR", "inbound", "Workday", "Internal HR", "oauth2", "https://workday-api.company.com", "JSON", "Layla Mansour", "HR Team", "production", 92.3, "2026-04-22 11:00:00"),
            ("E-commerce Platform - Shopify", "ECOMM_SH_001", "E-commerce", "bidirectional", "Shopify", "ERP", "api_key", "https://shopify-api.company.com", "JSON", "Rashid Hamad", "E-commerce Team", "production", 94.7, "2026-04-22 09:00:00"),
            ("Logistics - DHL", "LOG_DHL_001", "Logistics", "outbound", "Internal", "DHL", "api_key", "https://dhl-api.company.com", "XML", "Nadia Fadel", "Logistics Team", "production", 89.5, "2026-04-22 10:45:00"),
            ("Marketing - HubSpot", "MKT_HS_001", "Marketing", "inbound", "HubSpot", "Internal CRM", "api_key", "https://hubspot-api.company.com", "JSON", "Karim Reda", "Marketing Team", "production", 96.2, "2026-04-22 08:15:00"),
            ("CSV File Import - Suppliers", "FILE_CSV_SUP_001", "File", "inbound", "Suppliers", "Internal", "none", "", "CSV", "System", "Integration Team", "production", 85.0, "2026-04-22 06:00:00"),
            ("REST API - External Partner", "REST_PARTNER_001", "REST", "bidirectional", "Partner System", "Internal", "bearer", "https://partner-api.example.com", "JSON", "Tariq Awad", "Partnership Team", "testing", 78.4, "2026-04-21 14:30:00"),
            ("AI Service - OpenAI", "AI_OPENAI_001", "AI", "outbound", "Internal", "OpenAI", "api_key", "https://api.openai.com", "JSON", "Data Science Team", "AI Team", "production", 99.5, "2026-04-22 11:30:00"),
            ("AI Service - Azure Cognitive", "AI_AZURE_001", "AI", "outbound", "Internal", "Azure", "api_key", "https://azure-ai.cognitiveservices.azure.com", "JSON", "Data Science Team", "AI Team", "production", 97.0, "2026-04-22 10:00:00"),
            ("Weather API - OpenWeather", "EXT_WEATHER_001", "REST", "inbound", "OpenWeatherMap", "Internal", "api_key", "https://api.openweathermap.org", "JSON", "Operations Team", "IT Team", "production", 100.0, "2026-04-22 07:00:00"),
        ]

        for conn in connectors:
            cursor.execute("""
                INSERT INTO btp_connectors (name, code, category, direction, source_system, target_system,
                    auth_type, base_url, file_format, owner, team, environment, health_score, last_success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, conn)

        flows = [
            ("SAP to Warehouse Sync", "FLOW_SAP_WMS_001", "SAP_ERP_001,WMS_001", "scheduled", "0 */6 * * *", "SAP.SALES_ORDERS", "WMS.PURCHASE_ORDERS", "Ahmed Hassan"),
            ("Salesforce Lead Sync", "FLOW_SF_LEAD_001", "SF_CRM_002", "event_based", None, "SF.LEADS", "CRM.PROSPECTS", "Sarah Johnson"),
            ("Shopify Order Processing", "FLOW_SH_ORD_001", "ECOMM_SH_001", "event_based", None, "SHOP.ORDERS", "ERP.SALES_ORDERS", "Rashid Hamad"),
            ("Daily Financial Export", "FLOW_FIN_DAILY_001", "FIN_QB_001", "scheduled", "0 2 * * *", "ERP.INVOICES", "QB.INVOICES", "Youssef Ibrahim"),
            ("HR Employee onboarding", "FLOW_HR_ONBOARD_001", "HR_WD_001", "event_based", None, "WD.EMPLOYEES", "ERP.CONTACTS", "Layla Mansour"),
            ("Marketing Campaign Analytics", "FLOW_MKT_CAMP_001", "MKT_HS_001", "scheduled", "0 */4 * * *", "HS.CAMPAIGNS", "BI.MARKETING", "Karim Reda"),
            ("Supplier CSV Import", "FLOW_CSV_SUP_001", "FILE_CSV_SUP_001", "scheduled", "0 8 * * *", "FILE.SUPPLIERS", "ERP.SUPPLIERS", "System"),
            ("DHL Shipment Tracking", "FLOW_DHL_TRACK_001", "LOG_DHL_001", "event_based", None, "ERP.SHIPPING", "DHL.TRACKING", "Nadia Fadel"),
            ("AI Document Classification", "FLOW_AI_DOC_001", "AI_OPENAI_001", "event_based", None, "DOCS.UPLOAD", "AI.CLASSIFIED", "Data Science Team"),
            ("Email Notification Flow", "FLOW_EMAIL_NOTIFY_001", "EMAIL_SG_001", "event_based", None, "SYSTEM.NOTIFY", "EMAIL_queue", "IT Team"),
            ("QuickBooks Invoice Sync", "FLOW_QB_INV_001", "FIN_QB_001", "bidirectional", "0 */2 * * *", "ERP.INVOICES", "QB.INVOICES", "Youssef Ibrahim"),
            ("Workday Employee Updates", "FLOW_WD_EMP_001", "HR_WD_001", "scheduled", "0 1 * * *", "WD.EMPLOYEES", "ERP.EMPLOYEES", "Layla Mansour"),
            ("Shopify Inventory Update", "FLOW_SH_INV_001", "ECOMM_SH_001,WMS_001", "scheduled", "*/15 * * * *", "WMS.INVENTORY", "SHOP.INVENTORY", "Rashid Hamad"),
            ("Partner API Data Exchange", "FLOW_PARTNER_001", "REST_PARTNER_001", "scheduled", "0 6 * * *", "PARTNER.DATA", "ERP.DATA", "Tariq Awad"),
            ("Weather-Based Alerts", "FLOW_WEATHER_001", "EXT_WEATHER_001", "scheduled", "*/30 * * * *", "WEATHER.ALERTS", "SYSTEM.ALERTS", "Operations Team"),
        ]

        for flow in flows:
            cursor.execute("""
                INSERT INTO btp_integration_flows (flow_name, flow_code, connector_ids, trigger_type, schedule,
                    source_entity, target_entity, owner)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, flow)

        mappings = [
            ("SAP Order to WMS PO", "MAP_SAP_WMS_001", "SAP.SALES_ORDER", "WMS.PURCHASE_ORDER", "Ahmed Hassan", "active"),
            ("Salesforce Lead Mapping", "MAP_SF_LEAD_001", "SF.LEAD", "CRM.PROSPECT", "Sarah Johnson", "active"),
            ("Shopify Customer Sync", "MAP_SH_CUST_001", "SHOP.CUSTOMER", "ERP.CUSTOMER", "Rashid Hamad", "active"),
            ("QuickBooks Invoice Fields", "MAP_QB_INV_001", "ERP.INVOICE", "QB.INVOICE", "Youssef Ibrahim", "draft"),
            ("Workday Employee Fields", "MAP_WD_EMP_001", "WD.EMPLOYEE", "ERP.EMPLOYEE", "Layla Mansour", "active"),
            ("DHL Shipment Update", "MAP_DHL_SHIP_001", "ERP.SHIPPING", "DHL.SHIPMENT", "Nadia Fadel", "active"),
            ("HubSpot Contact Fields", "MAP_HS_CONT_001", "HS.CONTACT", "CRM.CONTACT", "Karim Reda", "active"),
            ("Supplier CSV Import Layout", "MAP_CSV_SUP_001", "FILE.CSV", "ERP.SUPPLIER", "System", "active"),
            ("AI Classification Response", "MAP_AI_DOC_001", "DOC.ORIGINAL", "AI.CLASSIFIED", "Data Science Team", "draft"),
            ("Email Template Mapping", "MAP_EMAIL_TMPL_001", "SYSTEM.NOTIFY", "EMAIL.MESSAGE", "IT Team", "active"),
        ]

        for mapping in mappings:
            cursor.execute("""
                INSERT INTO btp_mappings (name, code, source_type, target_type, owner, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, mapping)

        jobs = [
            ("JOB_SAP_WMS_001", "flow", "SAP to Warehouse Sync", "FLOW_SAP_WMS_001", "SAP_ERP_001", "scheduled", "completed", "Ahmed Hassan"),
            ("JOB_SF_LEAD_001", "flow", "Salesforce Lead Processing", "FLOW_SF_LEAD_001", "SF_CRM_002", "event", "completed", "Sarah Johnson"),
            ("JOB_SH_ORD_001", "flow", "Shopify Order Import", "FLOW_SH_ORD_001", "ECOMM_SH_001", "manual", "completed", "Rashid Hamad"),
            ("JOB_FIN_EXP_001", "export", "Daily Financial Export", None, "FIN_QB_001", "scheduled", "failed", "Youssef Ibrahim"),
            ("JOB_HR_EMP_001", "flow", "HR Onboarding Process", "FLOW_HR_ONBOARD_001", "HR_WD_001", "event", "queued", "Layla Mansour"),
            ("JOB_MKT_ANA_001", "export", "Marketing Analytics Report", None, "MKT_HS_001", "scheduled", "completed", "Karim Reda"),
            ("JOB_CSV_IMP_001", "import", "Supplier CSV Import", None, "FILE_CSV_SUP_001", "scheduled", "processing", "System"),
            ("JOB_DHL_TRK_001", "flow", "DHL Tracking Update", "FLOW_DHL_TRACK_001", "LOG_DHL_001", "event", "completed", "Nadia Fadel"),
            ("JOB_AI_DOC_001", "ai", "Document Classification", None, "AI_OPENAI_001", "event", "failed", "Data Science Team"),
            ("JOB_EMAIL_001", "notification", "Email Notification Batch", None, "EMAIL_SG_001", "manual", "completed", "IT Team"),
            ("JOB_QB_SYNC_001", "sync", "QuickBooks Sync", "FLOW_QB_INV_001", "FIN_QB_001", "scheduled", "queued", "Youssef Ibrahim"),
            ("JOB_WD_EMP_001", "sync", "Workday Employee Sync", "FLOW_WD_EMP_001", "HR_WD_001", "scheduled", "completed", "Layla Mansour"),
            ("JOB_SH_INV_001", "sync", "Shopify Inventory Sync", "FLOW_SH_INV_001", "ECOMM_SH_001,WMS_001", "scheduled", "completed", "Rashid Hamad"),
            ("JOB_PARTNER_001", "sync", "Partner Data Exchange", "FLOW_PARTNER_001", "REST_PARTNER_001", "scheduled", "failed", "Tariq Awad"),
            ("JOB_WEATHER_001", "api", "Weather API Check", None, "EXT_WEATHER_001", "scheduled", "completed", "Operations Team"),
            ("JOB_AZURE_AI_001", "ai", "Azure AI Processing", None, "AI_AZURE_001", "event", "completed", "Data Science Team"),
            ("JOB_SAP_WMS_002", "flow", "SAP to Warehouse Sync #2", "FLOW_SAP_WMS_001", "SAP_ERP_001", "scheduled", "completed", "Ahmed Hassan"),
            ("JOB_SAP_WMS_003", "flow", "SAP to Warehouse Sync #3", "FLOW_SAP_WMS_001", "SAP_ERP_001", "scheduled", "completed", "Ahmed Hassan"),
            ("JOB_SF_LEAD_002", "flow", "Salesforce Lead Processing #2", "FLOW_SF_LEAD_001", "SF_CRM_002", "event", "completed", "Sarah Johnson"),
            ("JOB_SH_ORD_002", "flow", "Shopify Order Import #2", "FLOW_SH_ORD_001", "ECOMM_SH_001", "manual", "queued", "Rashid Hamad"),
            ("JOB_FIN_EXP_002", "export", "Daily Financial Export #2", None, "FIN_QB_001", "scheduled", "completed", "Youssef Ibrahim"),
            ("JOB_HR_EMP_002", "flow", "HR Onboarding Process #2", "FLOW_HR_ONBOARD_001", "HR_WD_001", "event", "completed", "Layla Mansour"),
            ("JOB_MKT_ANA_002", "export", "Marketing Analytics Report #2", None, "MKT_HS_001", "scheduled", "completed", "Karim Reda"),
            ("JOB_DHL_TRK_002", "flow", "DHL Tracking Update #2", "FLOW_DHL_TRACK_001", "LOG_DHL_001", "event", "completed", "Nadia Fadel"),
            ("JOB_AI_DOC_002", "ai", "Document Classification #2", None, "AI_OPENAI_001", "event", "failed", "Data Science Team"),
        ]

        for i, job in enumerate(jobs):
            status = job[6]
            duration = 0 if status in ['queued', 'processing'] else (120 if status == 'completed' else 45)
            cursor.execute("""
                INSERT INTO btp_jobs (job_id, job_type, name, flow_id, connector_id, trigger_source,
                    status, owner, attempts, max_attempts, duration_seconds, last_error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (job[0], job[1], job[2], job[3], job[4], job[5], job[6], job[7], 1 if status == 'failed' else 0, 3, duration, "Connection timeout" if status == "failed" else None))

        apis = [
            ("Customer API", "CUST_API_001", "v1", "/api/v1/customers", "CRM Team", 1000, "minute", 1),
            ("Order API", "ORD_API_001", "v1", "/api/v1/orders", "ERP Team", 500, "minute", 1),
            ("Inventory API", "INV_API_001", "v1", "/api/v1/inventory", "WMS Team", 2000, "minute", 1),
            ("Invoice API", "INV_API_002", "v1", "/api/v1/invoices", "Finance Team", 500, "minute", 1),
            ("Employee API", "EMP_API_001", "v1", "/api/v1/employees", "HR Team", 300, "minute", 1),
            ("Product Catalog API", "PROD_API_001", "v1", "/api/v1/products", "E-commerce Team", 1000, "minute", 1),
            ("Shipping API", "SHIP_API_001", "v1", "/api/v1/shipping", "Logistics Team", 500, "minute", 1),
            ("Analytics API", "ANA_API_001", "v1", "/api/v1/analytics", "BI Team", 200, "minute", 1),
            ("Marketing API", "MKT_API_001", "v1", "/api/v1/marketing", "Marketing Team", 300, "minute", 1),
            ("AI Inference API", "AI_API_001", "v1", "/api/v1/ai/inference", "AI Team", 100, "minute", 1),
            ("Webhook Receiver API", "WH_API_001", "v1", "/api/v1/webhooks", "Integration Team", 5000, "minute", 1),
            ("Integration Sync API", "SYNC_API_001", "v1", "/api/v1/sync", "Integration Team", 500, "minute", 1),
        ]

        for api in apis:
            cursor.execute("""
                INSERT INTO btp_api_catalog (api_name, api_code, version, base_path, owner_team,
                    rate_limit_requests, rate_limit_period, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, api)

        events = [
            ("record.created", "Record Created", "Fired when a new record is created in the system", "system"),
            ("record.updated", "Record Updated", "Fired when a record is modified", "system"),
            ("record.approved", "Record Approved", "Fired when a record is approved through workflow", "workflow"),
            ("record.rejected", "Record Rejected", "Fired when a record is rejected", "workflow"),
            ("job.failed", "Job Failed", "Fired when a scheduled job fails", "integration"),
            ("job.completed", "Job Completed", "Fired when a job completes successfully", "integration"),
            ("export.completed", "Export Completed", "Fired when a data export finishes", "integration"),
            ("connector.offline", "Connector Offline", "Fired when a connector becomes unreachable", "integration"),
            ("connector.online", "Connector Online", "Fired when a connector comes back online", "integration"),
            ("api.key.rotated", "API Key Rotated", "Fired when an API key is rotated", "security"),
            ("feature_flag.changed", "Feature Flag Changed", "Fired when a feature flag is toggled", "platform"),
            ("incident.created", "Incident Created", "Fired when a new incident is created", "platform"),
            ("incident.resolved", "Incident Resolved", "Fired when an incident is marked resolved", "platform"),
            ("user.login", "User Login", "Fired when a user logs into the system", "security"),
            ("ai.request", "AI Request Made", "Fired when an AI service request is processed", "ai"),
        ]

        for event in events:
            cursor.execute("""
                INSERT INTO btp_events (event_type, name, description, category)
                VALUES (?, ?, ?, ?)
            """, event)

        flags = [
            ("enable_ai_classification", "AI Document Classification", "Enable AI-based document classification feature", "boolean", "false", "production,staging", "AI Team", 1),
            ("enable_new_dashboard", "New Dashboard Design", "Show the redesigned dashboard with new widgets", "boolean", "true", "all", "Product Team", 0),
            ("enable_rtl_support", "RTL Interface Support", "Enable right-to-left language interface support", "boolean", "true", "all", "Platform Team", 0),
            ("max_csv_rows", "CSV Import Row Limit", "Maximum number of rows allowed in CSV imports", "number", "10000", "all", "Integration Team", 0),
            ("enable_webhook_retry", "Webhook Retry Logic", "Enable automatic retry for failed webhook deliveries", "boolean", "true", "production", "Integration Team", 1),
            ("api_rate_limit_tier", "API Rate Limit Tier", "API rate limit tier for the platform (basic, standard, premium)", "string", "standard", "all", "Platform Team", 0),
            ("enable_export_pdf", "PDF Export Format", "Enable PDF export option in reports", "boolean", "false", "all", "Product Team", 0),
            ("maintenance_mode", "Maintenance Mode", "Put the entire platform into maintenance mode", "boolean", "false", "production", "Admin", 1),
            ("enable_partner_integration", "Partner Integration Features", "Enable third-party partner integration endpoints", "boolean", "true", "production,staging", "Partnership Team", 1),
            ("sync_interval_minutes", "Data Sync Interval", "Default interval (in minutes) between data synchronization jobs", "number", "15", "all", "Integration Team", 0),
        ]

        for flag in flags:
            cursor.execute("""
                INSERT INTO btp_feature_flags (flag_key, name, description, flag_type, default_value,
                    current_value, environments, owner_team)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, flag)

        ai_providers = [
            ("OpenAI GPT-4", "OPENAI_GPT4", "openai", "https://api.openai.com/v1", "gpt-4", 128000, 100000, 45000, 0.0001, "Data Science Team", 1),
            ("Azure OpenAI", "AZURE_OAI", "azure", "https://azure-openai.company.com", "gpt-4", 128000, 80000, 32000, 0.00012, "Data Science Team", 1),
            ("Anthropic Claude", "ANT_CLAUDE", "anthropic", "https://api.anthropic.com", "claude-3-opus", 200000, 50000, 0, 0.00015, "AI Research Team", 1),
            ("Google Gemini", "GOOGLE_GEMINI", "google", "https://generativelanguage.googleapis.com", "gemini-pro", 32000, 50000, 0, 0.0001, "AI Team", 1),
            ("Whisper Transcription", "OPENAI_WHISPER", "openai", "https://api.openai.com/v1", "whisper-1", 0, 50000, 0, 0.00006, "IT Team", 1),
            ("DALL-E Image Gen", "OPENAI_DALLE", "openai", "https://api.openai.com/v1", "dall-e-3", 0, 10000, 0, 0.04, "Marketing Team", 1),
        ]

        for provider in ai_providers:
            cursor.execute("""
                INSERT INTO btp_ai_providers (provider_name, provider_code, provider_type, api_endpoint,
                    model_name, max_tokens, usage_limit_monthly, current_usage_monthly, cost_per_token,
                    owner_team, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (provider[0], provider[1], provider[2], provider[3], provider[4], provider[5], provider[6], provider[7], provider[8], provider[9], provider[10]))

        incidents = [
            ("INC-2026-0001", "SAP Connector Timeout", "SAP ERP connector experiencing timeouts during peak hours", "critical", "integration", 1, None, "open", "Ahmed Hassan", "Integration Team"),
            ("INC-2026-0002", "Failed Financial Export", "Daily financial export to QuickBooks failed", "high", "integration", 4, None, "in_progress", "Youssef Ibrahim", "Finance Team"),
            ("INC-2026-0003", "Shopify Inventory Desync", "Inventory levels not syncing properly with Shopify", "medium", "integration", 7, None, "open", "Rashid Hamad", "E-commerce Team"),
            ("INC-2026-0004", "API Rate Limit Exceeded", "Customer API hitting rate limits during high traffic", "high", "api", 1, None, "resolved", "CRM Team", "IT Team"),
            ("INC-2026-0005", "AI Service Degradation", "Azure AI service responding slowly", "medium", "ai", 12, None, "open", "Data Science Team", "AI Team"),
            ("INC-2026-0006", "Webhook Delivery Delays", "Webhook deliveries experiencing 5+ minute delays", "high", "integration", 3, None, "in_progress", "Tariq Awad", "Integration Team"),
            ("INC-2026-0007", "Workday Sync Failure", "Workday employee sync failing since yesterday", "medium", "integration", 6, None, "open", "Layla Mansour", "HR Team"),
            ("INC-2026-0008", "Partner API Outage", "External partner API returning 503 errors", "critical", "integration", 8, None, "open", "Tariq Awad", "Partnership Team"),
            ("INC-2026-0009", "DHL Tracking Update Delay", "Shipment tracking updates delayed by 2+ hours", "low", "integration", 9, None, "resolved", "Nadia Fadel", "Logistics Team"),
            ("INC-2026-0010", "CSV Import Processing Slow", "Large CSV imports taking excessive time", "low", "integration", 11, None, "open", "System", "IT Team"),
        ]

        for inc in incidents:
            cursor.execute("""
                INSERT INTO btp_incidents (incident_code, title, description, severity, category,
                    related_connector_id, related_job_id, status, assigned_to, assigned_team)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (inc[0], inc[1], inc[2], inc[3], inc[4], inc[5], inc[6], inc[7], inc[8], inc[9]))

        api_clients = [
            ("Mobile App - iOS", "CLIENT_IOS_001", 1, "mobile,read,customers", 1, "active"),
            ("Mobile App - Android", "CLIENT_AND_001", 1, "mobile,read,customers,orders", 2, "active"),
            ("Partner Portal", "CLIENT_PARTNER_001", 11, "partner,read,write", 3, "active"),
            ("BI Dashboard", "CLIENT_BI_001", 8, "analytics,read", 4, "active"),
            ("Marketing Automation", "CLIENT_MKT_001", 9, "marketing,read,write", 5, "active"),
            ("Mobile App - iOS v2", "CLIENT_IOS_002", 1, "mobile,v2,read,customers,orders", 1, "active"),
            ("Third-party Integration", "CLIENT_3RD_001", 12, "integration,read,write,sync", 6, "active"),
            ("AI Service Account", "CLIENT_AI_001", 10, "ai,inference", 7, "active"),
            ("Admin Dashboard", "CLIENT_ADMIN_001", 1, "admin,full", 8, "active"),
            ("External Reporting Tool", "CLIENT_REP_001", 8, "reports,read,export", 9, "active"),
            ("Mobile App - Android v2", "CLIENT_AND_002", 1, "mobile,v2,read,customers,orders", 2, "active"),
            ("Legacy System Integration", "CLIENT_LEG_001", 12, "legacy,read", 10, "inactive"),
        ]

        for client in api_clients:
            cursor.execute("""
                INSERT INTO btp_api_clients (client_name, client_code, api_id, scopes,
                    owner_user_id, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (client[0], client[1], client[2], client[3], client[4], client[5]))

        retry_items = [
            (5, 1, "Connection timeout after 30s", 2, 5),
            (9, 8, "API returned 503 Service Unavailable", 1, 5),
            (14, 12, "Partner API authentication failed", 3, 5),
            (25, 9, "AI request quota exceeded", 1, 3),
        ]

        for retry in retry_items:
            cursor.execute("""
                INSERT INTO btp_retry_queue (job_id, connector_id, reason, retry_count,
                    max_retries, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
            """, (retry[0], retry[1], retry[2], retry[3], retry[4]))

        dlq_items = [
            (4, 4, "export", "Invalid invoice data format - missing required field 'customer_id'", 3, "failed"),
            (9, 9, "ai", "AI classification failed - unsupported document format", 5, "failed"),
            (14, 12, "sync", "Partner sync failed after 3 retries - authentication expired", 4, "failed"),
            (25, 13, "ai", "Azure AI timeout - request exceeded 60s limit", 2, "failed"),
        ]

        for dlq in dlq_items:
            cursor.execute("""
                INSERT INTO btp_dead_letters (job_id, connector_id, event_type, failure_reason,
                    attempts, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (dlq[0], dlq[1], dlq[2], dlq[3], dlq[4], dlq[5]))

        env_profiles = [
            ("Production", "ENV_PROD_001", "production", "Primary production environment", '{"sync_interval": 5, "max_retries": 5, "timeout": 60}', 1),
            ("Staging", "ENV_STAGING_001", "staging", "Pre-production staging environment", '{"sync_interval": 10, "max_retries": 3, "timeout": 45}', 0),
            ("Testing", "ENV_TEST_001", "testing", "QA and testing environment", '{"sync_interval": 15, "max_retries": 2, "timeout": 30}', 0),
            ("Development", "ENV_DEV_001", "development", "Local development environment", '{"sync_interval": 30, "max_retries": 1, "timeout": 20}', 0),
        ]

        for env in env_profiles:
            cursor.execute("""
                INSERT INTO btp_environment_profiles (profile_name, profile_code, environment_type,
                    description, config_json, is_default)
                VALUES (?, ?, ?, ?, ?, ?)
            """, env)

        extension_fields = [
            ("Custom Color Code", "cust_color_code", "orders", "string", "", 0, 1, 1, 1, "Sales Team"),
            ("Shipping Priority", "ship_priority", "orders", "number", "5", 0, 1, 1, 1, "Logistics Team"),
            ("Partner ID", "partner_reference_id", "customers", "string", "", 0, 1, 1, 1, "Partnership Team"),
            ("AI Classification", "ai_classification", "documents", "string", "", 0, 1, 1, 1, "AI Team"),
            ("Budget Code", "budget_code", "projects", "string", "", 0, 1, 1, 1, "Finance Team"),
            ("Department Code", "dept_code", "employees", "string", "", 0, 1, 1, 1, "HR Team"),
            ("Warehouse Zone", "wh_zone", "inventory", "string", "", 0, 1, 1, 1, "Warehouse Team"),
            ("Campaign Type", "campaign_type", "marketing", "string", "", 0, 1, 1, 1, "Marketing Team"),
        ]

        for field in extension_fields:
            cursor.execute("""
                INSERT INTO btp_extension_fields (field_name, field_code, entity_type, field_type,
                    default_value, is_required, searchable, reportable, exportable, visible_to_roles)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, field)

        audit_logs = [
            ("btp_connector", 1, "create", 1, "Admin", "Created connector: SAP ERP Connector", "192.168.1.100"),
            ("btp_connector", 2, "update", 1, "Admin", "Updated connector: Salesforce CRM", "192.168.1.101"),
            ("btp_flow", 1, "run", 1, "Admin", "Ran flow: SAP to Warehouse Sync", "192.168.1.100"),
            ("btp_job", 1, "complete", 1, "Admin", "Job completed successfully", "192.168.1.100"),
            ("btp_incident", 1, "create", 1, "Admin", "Created incident: SAP Connector Timeout", "192.168.1.102"),
            ("btp_feature_flag", 1, "toggle", 1, "Admin", "Toggled flag: enable_ai_classification", "192.168.1.101"),
            ("btp_api_client", 1, "create", 1, "Admin", "Created API client: Mobile App - iOS", "192.168.1.100"),
            ("btp_mapping", 1, "approve", 1, "Admin", "Approved mapping: SAP Order to WMS PO", "192.168.1.103"),
        ]

        for log in audit_logs:
            cursor.execute("""
                INSERT INTO btp_audit_logs (entity_type, entity_id, action, user_id, user_name,
                    changes, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, log)

        print("[BTP] Sample data seeded successfully!")
        db.commit()

    except Exception as e:
        print(f"[BTP] Error seeding sample data: {e}")
        db.rollback()
    finally:
        db.close()
