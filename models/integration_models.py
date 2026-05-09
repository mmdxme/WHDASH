"""
Integration / Middleware Module - Data Models
==============================================
Enterprise-grade integration orchestration layer for the ERP system.
Supports internal module-to-module integrations, third-party system integrations,
inbound/outbound APIs, scheduled sync jobs, transformation rules, webhooks,
message queues, dead-letter handling, and operational monitoring.

Author: Enterprise Architecture Team
Version: 1.0.0
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import hashlib
import json
import uuid


def get_integration_db():
    """Get database connection for integration module."""
    from database import get_db
    return get_db()


def init_integration_tables():
    """
    Initialize all integration module tables.
    Called during module registration and startup.
    """
    conn = get_integration_db()
    cursor = conn.cursor()
    
    # =====================================================================
    # TABLE 1: integration_connectors
    # Central registry of all integration connectors (internal and external)
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_connectors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            name_ar TEXT,
            name_fa TEXT,
            name_ru TEXT,
            name_zh TEXT,
            name_es TEXT,
            name_hi TEXT,
            name_de TEXT,
            description TEXT,
            description_ar TEXT,
            description_fa TEXT,
            connector_type TEXT NOT NULL,
            owner_module TEXT NOT NULL,
            direction TEXT NOT NULL DEFAULT 'bidirectional',
            auth_method TEXT,
            active_status TEXT DEFAULT 'inactive',
            health_status TEXT DEFAULT 'unknown',
            test_status TEXT DEFAULT 'untested',
            last_success_at TEXT,
            last_failure_at TEXT,
            last_tested_at TEXT,
            retry_policy TEXT DEFAULT '{"max_retries": 3, "retry_delay": 60}',
            timeout_seconds INTEGER DEFAULT 30,
            payload_format TEXT DEFAULT 'json',
            rate_limit_per_minute INTEGER,
            environment TEXT DEFAULT 'production',
            tags TEXT,
            notes TEXT,
            config_schema TEXT,
            metadata_json TEXT,
            company_id INTEGER,
            branch_id INTEGER,
            business_unit_id INTEGER,
            is_deleted INTEGER DEFAULT 0,
            created_by INTEGER,
            updated_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id),
            FOREIGN KEY (branch_id) REFERENCES company_branches(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_connector_code ON integration_connectors(code)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_connector_type ON integration_connectors(connector_type)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_connector_status ON integration_connectors(active_status, health_status)
    """)
    
    # =====================================================================
    # TABLE 2: integration_connector_types
    # Master list of supported connector types
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_connector_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            icon TEXT,
            color TEXT,
            is_bidirectional INTEGER DEFAULT 0,
            auth_types TEXT,
            payload_formats TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # =====================================================================
    # TABLE 3: integration_environments
    # Environment definitions (production, staging, development, testing)
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_environments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            color TEXT,
            is_default INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            company_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    # =====================================================================
    # TABLE 4: integration_flows
    # Integration flow definitions (header/parent record)
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_flows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            name_ar TEXT,
            name_fa TEXT,
            name_ru TEXT,
            name_zh TEXT,
            name_es TEXT,
            name_hi TEXT,
            name_de TEXT,
            description TEXT,
            version INTEGER DEFAULT 1,
            source_system TEXT NOT NULL,
            destination_system TEXT NOT NULL,
            trigger_type TEXT NOT NULL,
            direction TEXT NOT NULL,
            data_entity TEXT,
            flow_status TEXT DEFAULT 'draft',
            is_test_mode INTEGER DEFAULT 0,
            is_production_mode INTEGER DEFAULT 0,
            company_id INTEGER,
            branch_id INTEGER,
            owner_id INTEGER,
            approver_id INTEGER,
            rollback_strategy TEXT,
            timeout_strategy TEXT,
            retry_strategy TEXT,
            idempotency_key_strategy TEXT,
            conflict_strategy TEXT,
            duplicate_handling TEXT,
            logging_level TEXT DEFAULT 'info',
            alerting_level TEXT DEFAULT 'warning',
            config_json TEXT,
            tags TEXT,
            notes TEXT,
            published_at TEXT,
            archived_at TEXT,
            is_deleted INTEGER DEFAULT 0,
            created_by INTEGER,
            updated_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id),
            FOREIGN KEY (owner_id) REFERENCES users(id),
            FOREIGN KEY (approver_id) REFERENCES users(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_flow_code ON integration_flows(code)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_flow_status ON integration_flows(flow_status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_flow_trigger ON integration_flows(trigger_type)
    """)
    
    # =====================================================================
    # TABLE 5: integration_flow_steps
    # Individual steps within an integration flow
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_flow_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flow_id INTEGER NOT NULL,
            step_order INTEGER NOT NULL,
            step_type TEXT NOT NULL,
            step_name TEXT NOT NULL,
            description TEXT,
            config_json TEXT,
            condition_expression TEXT,
            error_handling TEXT,
            continue_on_error INTEGER DEFAULT 0,
            timeout_seconds INTEGER DEFAULT 30,
            retry_count INTEGER DEFAULT 0,
            step_status TEXT DEFAULT 'active',
            is_enabled INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (flow_id) REFERENCES integration_flows(id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_step_flow ON integration_flow_steps(flow_id, step_order)
    """)
    
    # =====================================================================
    # TABLE 6: integration_flow_versions
    # Version history for integration flows
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_flow_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flow_id INTEGER NOT NULL,
            version INTEGER NOT NULL,
            config_json TEXT,
            steps_json TEXT,
            status TEXT DEFAULT 'archived',
            changed_by INTEGER,
            change_summary TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (flow_id) REFERENCES integration_flows(id) ON DELETE CASCADE,
            FOREIGN KEY (changed_by) REFERENCES users(id)
        )
    """)
    
    # =====================================================================
    # TABLE 7: integration_triggers
    # Trigger configurations for flows
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_triggers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flow_id INTEGER NOT NULL,
            trigger_type TEXT NOT NULL,
            name TEXT NOT NULL,
            config_json TEXT,
            condition_expression TEXT,
            is_active INTEGER DEFAULT 1,
            last_triggered_at TEXT,
            trigger_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (flow_id) REFERENCES integration_flows(id) ON DELETE CASCADE
        )
    """)
    
    # =====================================================================
    # TABLE 8: integration_schedules
    # Scheduled execution configurations
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flow_id INTEGER NOT NULL,
            schedule_name TEXT NOT NULL,
            cron_expression TEXT,
            frequency TEXT,
            interval_minutes INTEGER,
            day_of_week TEXT,
            day_of_month TEXT,
            time_of_day TEXT,
            timezone TEXT DEFAULT 'UTC',
            start_date TEXT,
            end_date TEXT,
            is_active INTEGER DEFAULT 1,
            last_run_at TEXT,
            next_run_at TEXT,
            run_count INTEGER DEFAULT 0,
            skip_count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            created_by INTEGER,
            updated_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (flow_id) REFERENCES integration_flows(id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_schedule_flow ON integration_schedules(flow_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_schedule_active ON integration_schedules(is_active, next_run_at)
    """)
    
    # =====================================================================
    # TABLE 9: integration_endpoints
    # API endpoint definitions
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_endpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            endpoint_type TEXT NOT NULL,
            http_method TEXT,
            url_path TEXT NOT NULL,
            auth_type TEXT,
            allowed_methods TEXT,
            schema_definition TEXT,
            sample_request TEXT,
            sample_response TEXT,
            timeout_seconds INTEGER DEFAULT 30,
            rate_limit_per_minute INTEGER,
            ip_allowlist TEXT,
            active_status TEXT DEFAULT 'active',
            deprecated_status TEXT DEFAULT 'active',
            usage_count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            health_check_result TEXT,
            last_health_check TEXT,
            endpoint_group TEXT,
            tags TEXT,
            version TEXT DEFAULT 'v1',
            approval_workflow_id INTEGER,
            company_id INTEGER,
            is_deleted INTEGER DEFAULT 0,
            created_by INTEGER,
            updated_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_endpoint_code ON integration_endpoints(code)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_endpoint_group ON integration_endpoints(endpoint_group)
    """)
    
    # =====================================================================
    # TABLE 10: integration_endpoint_versions
    # Version history for endpoints
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_endpoint_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint_id INTEGER NOT NULL,
            version TEXT NOT NULL,
            schema_definition TEXT,
            sample_request TEXT,
            sample_response TEXT,
            changelog TEXT,
            is_active INTEGER DEFAULT 1,
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (endpoint_id) REFERENCES integration_endpoints(id) ON DELETE CASCADE
        )
    """)
    
    # =====================================================================
    # TABLE 11: integration_webhooks
    # Webhook subscription definitions
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_webhooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            event_type TEXT NOT NULL,
            source_system TEXT,
            target_url TEXT NOT NULL,
            http_method TEXT DEFAULT 'POST',
            auth_type TEXT,
            secret_key TEXT,
            headers_json TEXT,
            retry_policy TEXT DEFAULT '{"max_retries": 5, "retry_delay": 300}',
            timeout_seconds INTEGER DEFAULT 30,
            active_status TEXT DEFAULT 'active',
            health_status TEXT DEFAULT 'unknown',
            is_inbound INTEGER DEFAULT 0,
            is_outbound INTEGER DEFAULT 1,
            filter_expression TEXT,
            transformation_rule_id INTEGER,
            connector_id INTEGER,
            usage_count INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0,
            last_success_at TEXT,
            last_failure_at TEXT,
            company_id INTEGER,
            owner_id INTEGER,
            tags TEXT,
            is_deleted INTEGER DEFAULT 0,
            created_by INTEGER,
            updated_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id),
            FOREIGN KEY (connector_id) REFERENCES integration_connectors(id),
            FOREIGN KEY (owner_id) REFERENCES users(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_webhook_event ON integration_webhooks(event_type)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_webhook_status ON integration_webhooks(active_status)
    """)
    
    # =====================================================================
    # TABLE 12: integration_webhook_deliveries
    # Individual webhook delivery attempts
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_webhook_deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            webhook_id INTEGER NOT NULL,
            delivery_id TEXT UNIQUE NOT NULL,
            event_id TEXT,
            payload TEXT,
            transformed_payload TEXT,
            headers_json TEXT,
            http_status_code INTEGER,
            response_body TEXT,
            error_message TEXT,
            attempt_number INTEGER DEFAULT 1,
            delivery_status TEXT DEFAULT 'pending',
            latency_ms INTEGER,
            retry_scheduled_at TEXT,
            correlation_id TEXT,
            trace_id TEXT,
            source_entity_type TEXT,
            source_entity_id TEXT,
            delivered_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (webhook_id) REFERENCES integration_webhooks(id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_delivery_webhook ON integration_webhook_deliveries(webhook_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_delivery_status ON integration_webhook_deliveries(delivery_status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_delivery_correlation ON integration_webhook_deliveries(correlation_id)
    """)
    
    # =====================================================================
    # TABLE 13: integration_events
    # Event registry for the internal event bus
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            event_type TEXT NOT NULL,
            event_name TEXT,
            source_system TEXT NOT NULL,
            source_entity_type TEXT,
            source_entity_id TEXT,
            payload TEXT,
            priority TEXT DEFAULT 'normal',
            business_impact TEXT DEFAULT 'medium',
            correlation_id TEXT,
            trace_id TEXT,
            deduplication_hash TEXT,
            event_status TEXT DEFAULT 'published',
            published_at TEXT,
            processed_at TEXT,
            processing_duration_ms INTEGER,
            subscriber_count INTEGER DEFAULT 0,
            is_deduplicated INTEGER DEFAULT 0,
            company_id INTEGER,
            metadata_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_type ON integration_events(event_type)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_status ON integration_events(event_status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_dedup ON integration_events(deduplication_hash)
    """)
    
    # =====================================================================
    # TABLE 14: integration_event_subscriptions
    # Event subscription rules
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_event_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            event_type TEXT NOT NULL,
            source_system TEXT,
            filter_expression TEXT,
            delivery_method TEXT DEFAULT 'queue',
            target_endpoint TEXT,
            target_flow_id INTEGER,
            transformation_rule_id INTEGER,
            is_active INTEGER DEFAULT 1,
            priority INTEGER DEFAULT 5,
            retry_policy TEXT,
            dead_letter_threshold INTEGER DEFAULT 3,
            owner_id INTEGER,
            created_by INTEGER,
            updated_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (target_flow_id) REFERENCES integration_flows(id),
            FOREIGN KEY (owner_id) REFERENCES users(id)
        )
    """)
    
    # =====================================================================
    # TABLE 15: integration_messages
    # Message queue items (working queue)
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE NOT NULL,
            queue_name TEXT NOT NULL,
            message_type TEXT NOT NULL,
            payload TEXT,
            headers_json TEXT,
            priority TEXT DEFAULT 'normal',
            correlation_id TEXT,
            reply_to TEXT,
            content_type TEXT,
            deduplication_hash TEXT,
            delivery_count INTEGER DEFAULT 0,
            max_deliveries INTEGER DEFAULT 10,
            message_status TEXT DEFAULT 'pending',
            processing_started_at TEXT,
            processed_at TEXT,
            expires_at TEXT,
            delay_seconds INTEGER DEFAULT 0,
            latency_ms INTEGER,
            source_system TEXT,
            destination_system TEXT,
            flow_id INTEGER,
            step_id INTEGER,
            error_message TEXT,
            company_id INTEGER,
            metadata_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (flow_id) REFERENCES integration_flows(id),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_message_queue ON integration_messages(queue_name, message_status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_message_status ON integration_messages(message_status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_message_dedup ON integration_messages(deduplication_hash)
    """)
    
    # =====================================================================
    # TABLE 16: integration_queue_items
    # Working queue tracking (alias/enhanced view of messages)
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_queue_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            queue_item_id TEXT UNIQUE NOT NULL,
            queue_name TEXT NOT NULL,
            source_system TEXT,
            destination_system TEXT,
            message_type TEXT,
            payload_preview TEXT,
            priority TEXT DEFAULT 'normal',
            message_status TEXT DEFAULT 'queued',
            retry_count INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 5,
            next_retry_at TEXT,
            last_error TEXT,
            flow_id INTEGER,
            connector_id INTEGER,
            correlation_id TEXT,
            processing_duration_ms INTEGER,
            completed_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (flow_id) REFERENCES integration_flows(id),
            FOREIGN KEY (connector_id) REFERENCES integration_connectors(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_queue_item_status ON integration_queue_items(message_status, queue_name)
    """)
    
    # =====================================================================
    # TABLE 17: integration_dlq_items
    # Dead Letter Queue - failed messages that exceeded retry limits
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_dlq_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dlq_item_id TEXT UNIQUE NOT NULL,
            original_message_id TEXT,
            queue_name TEXT NOT NULL,
            message_type TEXT,
            payload TEXT,
            headers_json TEXT,
            error_message TEXT,
            error_code TEXT,
            stack_trace TEXT,
            failure_count INTEGER DEFAULT 1,
            last_failure_at TEXT,
            source_system TEXT,
            destination_system TEXT,
            flow_id INTEGER,
            step_id INTEGER,
            correlation_id TEXT,
            review_status TEXT DEFAULT 'pending',
            reviewed_by INTEGER,
            reviewed_at TEXT,
            review_notes TEXT,
            resolution_action TEXT,
            replayed_to_message_id TEXT,
            company_id INTEGER,
            metadata_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (flow_id) REFERENCES integration_flows(id),
            FOREIGN KEY (reviewed_by) REFERENCES users(id),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_dlq_queue ON integration_dlq_items(queue_name)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_dlq_status ON integration_dlq_items(review_status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_dlq_created ON integration_dlq_items(created_at)
    """)
    
    # =====================================================================
    # TABLE 18: integration_job_runs
    # Scheduled job execution history
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_job_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_run_id TEXT UNIQUE NOT NULL,
            schedule_id INTEGER,
            flow_id INTEGER NOT NULL,
            job_type TEXT NOT NULL,
            trigger_type TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            duration_ms INTEGER,
            job_status TEXT DEFAULT 'running',
            records_processed INTEGER DEFAULT 0,
            records_succeeded INTEGER DEFAULT 0,
            records_failed INTEGER DEFAULT 0,
            records_skipped INTEGER DEFAULT 0,
            error_message TEXT,
            error_code TEXT,
            warning_count INTEGER DEFAULT 0,
            info_count INTEGER DEFAULT 0,
            checkpoint_data TEXT,
            execution_mode TEXT DEFAULT 'production',
            execution_context TEXT,
            started_by TEXT,
            company_id INTEGER,
            metadata_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (schedule_id) REFERENCES integration_schedules(id),
            FOREIGN KEY (flow_id) REFERENCES integration_flows(id),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_job_run_flow ON integration_job_runs(flow_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_job_run_status ON integration_job_runs(job_status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_job_run_time ON integration_job_runs(start_time)
    """)
    
    # =====================================================================
    # TABLE 19: integration_logs
    # Centralized integration logging
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_id TEXT UNIQUE NOT NULL,
            log_level TEXT NOT NULL,
            log_category TEXT NOT NULL,
            source_system TEXT,
            destination_system TEXT,
            flow_id INTEGER,
            step_id INTEGER,
            connector_id INTEGER,
            endpoint_id INTEGER,
            job_run_id TEXT,
            message TEXT NOT NULL,
            details TEXT,
            payload_preview TEXT,
            error_code TEXT,
            error_message TEXT,
            stack_trace TEXT,
            correlation_id TEXT,
            trace_id TEXT,
            span_id TEXT,
            user_id INTEGER,
            ip_address TEXT,
            user_agent TEXT,
            execution_time_ms INTEGER,
            company_id INTEGER,
            is_archived INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (flow_id) REFERENCES integration_flows(id),
            FOREIGN KEY (connector_id) REFERENCES integration_connectors(id),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_log_flow ON integration_logs(flow_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_log_level ON integration_logs(log_level)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_log_time ON integration_logs(created_at)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_log_correlation ON integration_logs(correlation_id)
    """)
    
    # =====================================================================
    # TABLE 20: integration_errors
    # Error tracking and aggregation
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            error_id TEXT UNIQUE NOT NULL,
            error_code TEXT NOT NULL,
            error_type TEXT NOT NULL,
            error_message TEXT NOT NULL,
            severity TEXT DEFAULT 'medium',
            source_system TEXT,
            destination_system TEXT,
            flow_id INTEGER,
            step_id INTEGER,
            connector_id INTEGER,
            endpoint_id INTEGER,
            job_run_id TEXT,
            entity_type TEXT,
            entity_id TEXT,
            payload_preview TEXT,
            stack_trace TEXT,
            resolution_hint TEXT,
            is_resolved INTEGER DEFAULT 0,
            resolved_by INTEGER,
            resolved_at TEXT,
            resolution_notes TEXT,
            occurrence_count INTEGER DEFAULT 1,
            first_occurrence_at TEXT,
            last_occurrence_at TEXT,
            company_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (flow_id) REFERENCES integration_flows(id),
            FOREIGN KEY (resolved_by) REFERENCES users(id),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_error_code ON integration_errors(error_code)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_error_status ON integration_errors(is_resolved)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_error_severity ON integration_errors(severity)
    """)
    
    # =====================================================================
    # TABLE 21: integration_credentials
    # Secure credential storage
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            credential_id TEXT UNIQUE NOT NULL,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            credential_type TEXT NOT NULL,
            auth_method TEXT,
            connector_id INTEGER,
            username TEXT,
            encrypted_password TEXT,
            api_key TEXT,
            encrypted_secret TEXT,
            certificate_data TEXT,
            private_key_data TEXT,
            token_value TEXT,
            token_secret TEXT,
            refresh_token TEXT,
            token_expiry TEXT,
            is_active INTEGER DEFAULT 1,
            last_rotated_at TEXT,
            last_tested_at TEXT,
            test_status TEXT DEFAULT 'untested',
            expiry_warning_days INTEGER DEFAULT 30,
            expires_at TEXT,
            environment TEXT,
            owner_id INTEGER,
            tags TEXT,
            notes TEXT,
            is_deleted INTEGER DEFAULT 0,
            created_by INTEGER,
            updated_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (connector_id) REFERENCES integration_connectors(id),
            FOREIGN KEY (owner_id) REFERENCES users(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_cred_connector ON integration_credentials(connector_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_cred_type ON integration_credentials(credential_type)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_cred_expiry ON integration_credentials(expires_at)
    """)
    
    # =====================================================================
    # TABLE 22: integration_field_mappings
    # Field mapping definitions
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_field_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mapping_id TEXT UNIQUE NOT NULL,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            source_system TEXT NOT NULL,
            target_system TEXT NOT NULL,
            entity_type TEXT,
            mapping_version INTEGER DEFAULT 1,
            source_entity TEXT,
            target_entity TEXT,
            source_fields_json TEXT,
            target_fields_json TEXT,
            mappings_json TEXT NOT NULL,
            default_values_json TEXT,
            validation_rules_json TEXT,
            is_active INTEGER DEFAULT 1,
            is_template INTEGER DEFAULT 0,
            template_category TEXT,
            usage_count INTEGER DEFAULT 0,
            last_used_at TEXT,
            owner_id INTEGER,
            approved_by INTEGER,
            approved_at TEXT,
            company_id INTEGER,
            tags TEXT,
            notes TEXT,
            is_deleted INTEGER DEFAULT 0,
            created_by INTEGER,
            updated_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(id),
            FOREIGN KEY (approved_by) REFERENCES users(id),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_mapping_code ON integration_field_mappings(code)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_mapping_systems ON integration_field_mappings(source_system, target_system)
    """)
    
    # =====================================================================
    # TABLE 23: integration_transformation_rules
    # Data transformation rule definitions
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_transformation_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id TEXT UNIQUE NOT NULL,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            rule_type TEXT NOT NULL,
            category TEXT NOT NULL,
            source_data_type TEXT,
            target_data_type TEXT,
            transformation_logic TEXT NOT NULL,
            expression TEXT,
            parameters_json TEXT,
            input_mapping TEXT,
            output_mapping TEXT,
            is_active INTEGER DEFAULT 1,
            execution_order INTEGER DEFAULT 100,
            is_sandboxed INTEGER DEFAULT 1,
            requires_approval INTEGER DEFAULT 0,
            risk_level TEXT DEFAULT 'low',
            usage_count INTEGER DEFAULT 0,
            last_used_at TEXT,
            version INTEGER DEFAULT 1,
            owner_id INTEGER,
            approved_by INTEGER,
            approved_at TEXT,
            company_id INTEGER,
            tags TEXT,
            notes TEXT,
            is_deleted INTEGER DEFAULT 0,
            created_by INTEGER,
            updated_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(id),
            FOREIGN KEY (approved_by) REFERENCES users(id),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_rule_type ON integration_transformation_rules(rule_type)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_rule_code ON integration_transformation_rules(code)
    """)
    
    # =====================================================================
    # TABLE 24: integration_payload_templates
    # Reusable payload templates
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_payload_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id TEXT UNIQUE NOT NULL,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            template_type TEXT NOT NULL,
            source_system TEXT,
            target_system TEXT,
            template_content TEXT NOT NULL,
            variables_json TEXT,
            sample_data_json TEXT,
            is_active INTEGER DEFAULT 1,
            usage_count INTEGER DEFAULT 0,
            last_used_at TEXT,
            version INTEGER DEFAULT 1,
            owner_id INTEGER,
            company_id INTEGER,
            tags TEXT,
            is_deleted INTEGER DEFAULT 0,
            created_by INTEGER,
            updated_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(id),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    # =====================================================================
    # TABLE 25: integration_reconciliation_batches
    # Reconciliation batch tracking
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_reconciliation_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT UNIQUE NOT NULL,
            batch_name TEXT NOT NULL,
            description TEXT,
            reconciliation_type TEXT NOT NULL,
            source_system TEXT NOT NULL,
            destination_system TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            period_start TEXT,
            period_end TEXT,
            source_count INTEGER DEFAULT 0,
            destination_count INTEGER DEFAULT 0,
            matched_count INTEGER DEFAULT 0,
            mismatch_count INTEGER DEFAULT 0,
            missing_in_source_count INTEGER DEFAULT 0,
            missing_in_destination_count INTEGER DEFAULT 0,
            duplicate_count INTEGER DEFAULT 0,
            batch_status TEXT DEFAULT 'pending',
            run_start_time TEXT,
            run_end_time TEXT,
            run_duration_ms INTEGER,
            comparison_method TEXT,
            tolerance_percentage REAL,
            owner_id INTEGER,
            reviewed_by INTEGER,
            reviewed_at TEXT,
            review_notes TEXT,
            company_id INTEGER,
            metadata_json TEXT,
            is_deleted INTEGER DEFAULT 0,
            created_by INTEGER,
            updated_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(id),
            FOREIGN KEY (reviewed_by) REFERENCES users(id),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_recon_batch ON integration_reconciliation_batches(batch_status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_recon_systems ON integration_reconciliation_batches(source_system, destination_system)
    """)
    
    # =====================================================================
    # TABLE 26: integration_reconciliation_items
    # Individual reconciliation mismatch items
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_reconciliation_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id TEXT UNIQUE NOT NULL,
            batch_id INTEGER NOT NULL,
            mismatch_type TEXT NOT NULL,
            source_record_id TEXT,
            destination_record_id TEXT,
            source_value TEXT,
            destination_value TEXT,
            field_name TEXT,
            difference_amount REAL,
            tolerance_amount REAL,
            status TEXT DEFAULT 'open',
            resolution_action TEXT,
            resolved_by INTEGER,
            resolved_at TEXT,
            resolution_notes TEXT,
            source_entity_type TEXT,
            destination_entity_type TEXT,
            retry_count INTEGER DEFAULT 0,
            last_retry_at TEXT,
            flow_id INTEGER,
            correlation_id TEXT,
            company_id INTEGER,
            metadata_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (batch_id) REFERENCES integration_reconciliation_batches(id) ON DELETE CASCADE,
            FOREIGN KEY (resolved_by) REFERENCES users(id),
            FOREIGN KEY (flow_id) REFERENCES integration_flows(id),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_recon_item_batch ON integration_reconciliation_items(batch_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_recon_item_status ON integration_reconciliation_items(status)
    """)
    
    # =====================================================================
    # TABLE 27: integration_usage_metrics
    # Usage metrics and analytics
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_usage_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_id TEXT UNIQUE NOT NULL,
            metric_date TEXT NOT NULL,
            metric_hour INTEGER,
            connector_id INTEGER,
            flow_id INTEGER,
            endpoint_id INTEGER,
            webhook_id INTEGER,
            metric_type TEXT NOT NULL,
            metric_value REAL NOT NULL,
            unit TEXT,
            source_system TEXT,
            destination_system TEXT,
            company_id INTEGER,
            branch_id INTEGER,
            metadata_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (connector_id) REFERENCES integration_connectors(id),
            FOREIGN KEY (flow_id) REFERENCES integration_flows(id),
            FOREIGN KEY (endpoint_id) REFERENCES integration_endpoints(id),
            FOREIGN KEY (webhook_id) REFERENCES integration_webhooks(id),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_metrics_date ON integration_usage_metrics(metric_date)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_metrics_connector ON integration_usage_metrics(connector_id, metric_date)
    """)
    
    # =====================================================================
    # TABLE 28: integration_alert_rules
    # Alert rule definitions
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_alert_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id TEXT UNIQUE NOT NULL,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            alert_type TEXT NOT NULL,
            severity TEXT DEFAULT 'medium',
            source_system TEXT,
            destination_system TEXT,
            connector_id INTEGER,
            flow_id INTEGER,
            condition_expression TEXT NOT NULL,
            threshold_value REAL,
            time_window_minutes INTEGER,
            evaluation_period_minutes INTEGER DEFAULT 5,
            notification_channels TEXT,
            flow_channel_id INTEGER,
            flow_group_id INTEGER,
            notification_template TEXT,
            is_active INTEGER DEFAULT 1,
            auto_actions_json TEXT,
            cooldown_minutes INTEGER DEFAULT 15,
            last_triggered_at TEXT,
            trigger_count INTEGER DEFAULT 0,
            owner_id INTEGER,
            created_by INTEGER,
            updated_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (connector_id) REFERENCES integration_connectors(id),
            FOREIGN KEY (flow_id) REFERENCES integration_flows(id),
            FOREIGN KEY (flow_channel_id) REFERENCES flow_channels(id),
            FOREIGN KEY (owner_id) REFERENCES users(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_alert_rule_active ON integration_alert_rules(is_active)
    """)
    
    # =====================================================================
    # TABLE 29: integration_alert_events
    # Triggered alert events
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_alert_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_event_id TEXT UNIQUE NOT NULL,
            rule_id INTEGER NOT NULL,
            severity TEXT NOT NULL,
            alert_title TEXT NOT NULL,
            alert_message TEXT,
            source_system TEXT,
            destination_system TEXT,
            connector_id INTEGER,
            flow_id INTEGER,
            entity_type TEXT,
            entity_id TEXT,
            metric_value REAL,
            threshold_value REAL,
            notification_sent INTEGER DEFAULT 0,
            notification_sent_at TEXT,
            flow_posted INTEGER DEFAULT 0,
            flow_posted_at TEXT,
            acknowledged INTEGER DEFAULT 0,
            acknowledged_by INTEGER,
            acknowledged_at TEXT,
            resolved INTEGER DEFAULT 0,
            resolved_by INTEGER,
            resolved_at TEXT,
            resolution_notes TEXT,
            company_id INTEGER,
            metadata_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (rule_id) REFERENCES integration_alert_rules(id),
            FOREIGN KEY (connector_id) REFERENCES integration_connectors(id),
            FOREIGN KEY (flow_id) REFERENCES integration_flows(id),
            FOREIGN KEY (acknowledged_by) REFERENCES users(id),
            FOREIGN KEY (resolved_by) REFERENCES users(id),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_alert_event_rule ON integration_alert_events(rule_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_alert_event_status ON integration_alert_events(acknowledged, resolved)
    """)
    
    # =====================================================================
    # TABLE 30: integration_export_profiles
    # Saved export configurations
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_export_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id TEXT UNIQUE NOT NULL,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            export_type TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            columns_json TEXT,
            column_order_json TEXT,
            filter_config_json TEXT,
            sort_config_json TEXT,
            include_summary INTEGER DEFAULT 1,
            include_raw_data INTEGER DEFAULT 1,
            include_audit_sheet INTEGER DEFAULT 0,
            include_metadata_sheet INTEGER DEFAULT 0,
            excel_format TEXT DEFAULT 'text',
            file_naming_pattern TEXT,
            is_default INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            usage_count INTEGER DEFAULT 0,
            last_used_at TEXT,
            owner_id INTEGER,
            company_id INTEGER,
            is_deleted INTEGER DEFAULT 0,
            created_by INTEGER,
            updated_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(id),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    # =====================================================================
    # TABLE 31: integration_saved_filters
    # Saved filter configurations
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_saved_filters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filter_id TEXT UNIQUE NOT NULL,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            filter_config_json TEXT NOT NULL,
            is_default INTEGER DEFAULT 0,
            is_shared INTEGER DEFAULT 0,
            owner_id INTEGER,
            company_id INTEGER,
            is_deleted INTEGER DEFAULT 0,
            created_by INTEGER,
            updated_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(id),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    # =====================================================================
    # TABLE 32: integration_favorite_views
    # Favorite view configurations
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_favorite_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            view_id TEXT UNIQUE NOT NULL,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            view_config_json TEXT NOT NULL,
            is_default INTEGER DEFAULT 0,
            owner_id INTEGER,
            company_id INTEGER,
            is_deleted INTEGER DEFAULT 0,
            created_by INTEGER,
            updated_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(id),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    # =====================================================================
    # TABLE 33: integration_annotations
    # User annotations on integration entities
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_annotations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            annotation_id TEXT UNIQUE NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            annotation_type TEXT,
            annotation_text TEXT NOT NULL,
            is_pinned INTEGER DEFAULT 0,
            owner_id INTEGER,
            company_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(id),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_annotation_entity ON integration_annotations(entity_type, entity_id)
    """)
    
    # =====================================================================
    # TABLE 34: integration_tags
    # Tag definitions for categorizing integration entities
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag TEXT UNIQUE NOT NULL,
            label TEXT,
            label_ar TEXT,
            label_fa TEXT,
            label_ru TEXT,
            label_zh TEXT,
            label_es TEXT,
            label_hi TEXT,
            label_de TEXT,
            color TEXT,
            category TEXT,
            description TEXT,
            usage_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # =====================================================================
    # TABLE 35: integration_runbook_links
    # Links to runbooks and documentation
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_runbook_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link_id TEXT UNIQUE NOT NULL,
            code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            url TEXT NOT NULL,
            document_type TEXT,
            entity_type TEXT,
            entity_id INTEGER,
            connector_id INTEGER,
            flow_id INTEGER,
            is_featured INTEGER DEFAULT 0,
            tags TEXT,
            language TEXT,
            version TEXT,
            owner_id INTEGER,
            company_id INTEGER,
            is_deleted INTEGER DEFAULT 0,
            created_by INTEGER,
            updated_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (connector_id) REFERENCES integration_connectors(id),
            FOREIGN KEY (flow_id) REFERENCES integration_flows(id),
            FOREIGN KEY (owner_id) REFERENCES users(id),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    # =====================================================================
    # TABLE 36: integration_file_exchange
    # File-based integration tracking
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_file_exchange (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT UNIQUE NOT NULL,
            exchange_type TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size_bytes INTEGER,
            checksum TEXT,
            source_system TEXT,
            destination_system TEXT,
            direction TEXT NOT NULL,
            staging_path TEXT,
            processed_path TEXT,
            failed_path TEXT,
            file_status TEXT DEFAULT 'pending',
            row_count INTEGER,
            success_count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            error_file_path TEXT,
            duplicate_file_id TEXT,
            is_duplicate INTEGER DEFAULT 0,
            validation_status TEXT,
            validation_errors_json TEXT,
            processing_started_at TEXT,
            processing_completed_at TEXT,
            processing_duration_ms INTEGER,
            correlation_id TEXT,
            flow_id INTEGER,
            connector_id INTEGER,
            company_id INTEGER,
            metadata_json TEXT,
            notes TEXT,
            is_deleted INTEGER DEFAULT 0,
            created_by INTEGER,
            updated_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (flow_id) REFERENCES integration_flows(id),
            FOREIGN KEY (connector_id) REFERENCES integration_connectors(id),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_file_exchange_status ON integration_file_exchange(file_status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_file_exchange_direction ON integration_file_exchange(direction)
    """)
    
    # =====================================================================
    # TABLE 37: integration_api_clients
    # API client credentials for endpoint access
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_api_clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT UNIQUE NOT NULL,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            client_type TEXT DEFAULT 'confidential',
            connector_id INTEGER,
            endpoint_id INTEGER,
            allowed_scopes TEXT,
            token_endpoint_auth_method TEXT DEFAULT 'client_secret_post',
            encryption_key_id TEXT,
            is_active INTEGER DEFAULT 1,
            approval_status TEXT DEFAULT 'pending',
            approved_by INTEGER,
            approved_at TEXT,
            last_rotated_at TEXT,
            expiry_date TEXT,
            rate_limit_override INTEGER,
            owner_id INTEGER,
            company_id INTEGER,
            is_deleted INTEGER DEFAULT 0,
            created_by INTEGER,
            updated_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (connector_id) REFERENCES integration_connectors(id),
            FOREIGN KEY (endpoint_id) REFERENCES integration_endpoints(id),
            FOREIGN KEY (approved_by) REFERENCES users(id),
            FOREIGN KEY (owner_id) REFERENCES users(id),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    # =====================================================================
    # TABLE 38: integration_api_client_secrets
    # API client secrets (encrypted storage)
    # =====================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_api_client_secrets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            secret_id TEXT UNIQUE NOT NULL,
            client_id INTEGER NOT NULL,
            encrypted_secret TEXT NOT NULL,
            secret_type TEXT DEFAULT 'client_secret',
            hash_algorithm TEXT DEFAULT 'sha256',
            is_active INTEGER DEFAULT 1,
            expires_at TEXT,
            last_used_at TEXT,
            rotated_by INTEGER,
            rotated_at TEXT,
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES integration_api_clients(id) ON DELETE CASCADE,
            FOREIGN KEY (rotated_by) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    return True


def seed_integration_connector_types():
    """Seed initial connector type definitions."""
    conn = get_integration_db()
    cursor = conn.cursor()
    
    connector_types = [
        ('INTERNAL_MODULE', 'Internal Module Connector', 'Internal ERP module integration', 'internal', 'fa-plug', '#3498db', 1, 'internal', 'json'),
        ('REST_API', 'REST API Connector', 'Generic REST API integration', 'api', 'fa-plug', '#2ecc71', 1, 'api_key,bearer_token,oauth2,basic', 'json,xml'),
        ('WEBHOOK', 'Webhook Connector', 'Webhook-based integration', 'webhook', 'fa-bolt', '#9b59b6', 0, 'hmac_sha256', 'json'),
        ('FILE_UPLOAD', 'File Upload Connector', 'File-based data exchange', 'file', 'fa-file-upload', '#e67e22', 0, 'none', 'csv,excel,json'),
        ('CSV', 'CSV Connector', 'CSV file import/export', 'file', 'fa-file-csv', '#f39c12', 0, 'none', 'csv'),
        ('EXCEL', 'Excel Connector', 'Excel file import/export', 'file', 'fa-file-excel', '#27ae60', 0, 'none', 'excel'),
        ('SFTP', 'SFTP Connector', 'Secure FTP file transfer', 'file', 'fa-server', '#34495e', 0, 'ssh_key,password', 'csv,json,xml'),
        ('EMAIL_INBOUND', 'Email Inbound Connector', 'Receive data via email', 'email', 'fa-envelope', '#1abc9c', 0, 'oauth2', 'json,csv'),
        ('EMAIL_OUTBOUND', 'Email Outbound Connector', 'Send data via email', 'email', 'fa-paper-plane', '#16a085', 0, 'oauth2,smtp', 'json'),
        ('DATABASE', 'Database Connector', 'Direct database connection', 'database', 'fa-database', '#2980b9', 1, 'username_password,windows_auth', 'json,csv'),
        ('ECOMMERCE', 'E-commerce Connector', 'E-commerce platform integration', 'ecommerce', 'fa-shopping-cart', '#8e44ad', 1, 'api_key,oauth2', 'json,csv'),
        ('ACCOUNTING', 'Accounting Connector', 'Accounting system integration', 'accounting', 'fa-calculator', '#2c3e50', 1, 'api_key,oauth2', 'json,csv'),
        ('CRM', 'CRM Connector', 'CRM platform integration', 'crm', 'fa-users', '#c0392b', 1, 'api_key,oauth2', 'json'),
        ('LOGISTICS', 'Logistics Provider Connector', 'Shipping and logistics integration', 'logistics', 'fa-truck', '#d35400', 1, 'api_key', 'json,csv'),
        ('SUPPLIER_PORTAL', 'Supplier Portal Connector', 'B2B supplier integration', 'b2b', 'fa-building', '#7f8c8d', 1, 'api_key,oauth2,saml', 'json,csv'),
        ('CUSTOMER_PORTAL', 'Customer Portal Connector', 'B2C customer portal integration', 'b2c', 'fa-user-circle', '#95a5a6', 1, 'oauth2,saml', 'json'),
        ('CUSTOM_SCRIPT', 'Custom Script Connector', 'Custom transformation script', 'script', 'fa-code', '#666666', 0, 'none', 'json'),
    ]
    
    for ct in connector_types:
        cursor.execute("""
            INSERT OR IGNORE INTO integration_connector_types 
            (code, name, description, category, icon, color, is_bidirectional, auth_types, payload_formats)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ct)
    
    conn.commit()


def seed_integration_environments():
    """Seed initial environment definitions."""
    conn = get_integration_db()
    cursor = conn.cursor()
    
    environments = [
        ('production', 'Production', 'Production environment', '#27ae60', 1),
        ('staging', 'Staging', 'Staging/QA environment', '#f39c12', 0),
        ('development', 'Development', 'Development environment', '#3498db', 0),
        ('testing', 'Testing', 'Testing environment', '#9b59b6', 0),
    ]
    
    for env in environments:
        cursor.execute("""
            INSERT OR IGNORE INTO integration_environments 
            (code, name, description, color, is_default)
            VALUES (?, ?, ?, ?, ?)
        """, env)
    
    conn.commit()


def seed_integration_tags():
    """Seed initial tag definitions."""
    conn = get_integration_db()
    cursor = conn.cursor()
    
    tags = [
        ('critical', 'Critical', '#e74c3c', 'priority'),
        ('high-priority', 'High Priority', '#f39c12', 'priority'),
        ('scheduled', 'Scheduled', '#3498db', 'type'),
        ('real-time', 'Real-time', '#2ecc71', 'type'),
        ('batch', 'Batch', '#9b59b6', 'type'),
        ('inbound', 'Inbound', '#1abc9c', 'direction'),
        ('outbound', 'Outbound', '#16a085', 'direction'),
        ('bidirectional', 'Bidirectional', '#34495e', 'direction'),
        ('finance', 'Finance', '#2c3e50', 'domain'),
        ('sales', 'Sales', '#c0392b', 'domain'),
        ('procurement', 'Procurement', '#d35400', 'domain'),
        ('warehouse', 'Warehouse', '#27ae60', 'domain'),
        ('hr', 'HR', '#8e44ad', 'domain'),
        ('marketing', 'Marketing', '#e67e22', 'domain'),
        ('ecommerce', 'E-commerce', '#9b59b6', 'domain'),
    ]
    
    for tag in tags:
        cursor.execute("""
            INSERT OR IGNORE INTO integration_tags 
            (tag, label, color, category)
            VALUES (?, ?, ?, ?)
        """, tag)
    
    conn.commit()


def generate_uuid():
    """Generate a unique identifier."""
    return str(uuid.uuid4())


def generate_code(prefix):
    """Generate a unique code with prefix."""
    return f"{prefix.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
