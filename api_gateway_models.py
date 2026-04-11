"""
API Gateway Data Models
=======================
Centralized data models for the enterprise API Gateway module.

This module defines all database tables and data access functions for:
- API versioning and route registry
- API clients and credential management
- Authentication, authorization scopes, and access policies
- Rate limiting profiles and enforcement
- Request/response logging and error tracking
- External integration profiles and sync jobs
- Webhook event catalog, subscriptions, and delivery
- API documentation registry
- Approval workflows for API governance
- Audit trail for all API Gateway operations

All tables follow consistent naming conventions and include proper indexes
for performance. Every entity supports audit trail through the unified
platform_audit_log when available.

Usage:
    from api_gateway_models import (
        init_api_gateway_tables,
        get_api_clients, create_api_client,
        get_webhook_subscriptions, deliver_webhook_event,
        # ... many more
    )
"""

import sqlite3
import hashlib
import secrets
import hmac
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from database import (
    get_db, get_db_context, get_one, get_all, get_count,
    table_exists, column_exists, add_column_if_not_exists,
    log_audit, exists
)


# =============================================================================
# TABLE INITIALIZATION
# =============================================================================

def init_api_gateway_tables():
    """
    Initialize all API Gateway database tables.
    Called during app startup to ensure all tables exist.
    """
    _ensure_api_versions_table()
    _ensure_api_route_registry()
    _ensure_api_clients_table()
    _ensure_api_client_credentials_table()
    _ensure_api_scopes_table()
    _ensure_api_access_policies_table()
    _ensure_api_rate_limit_profiles_table()
    _ensure_api_request_logs_table()
    _ensure_api_error_logs_table()
    _ensure_integration_profiles_table()
    _ensure_integration_runs_table()
    _ensure_integration_exceptions_table()
    _ensure_webhook_events_table()
    _ensure_webhook_subscriptions_table()
    _ensure_webhook_deliveries_table()
    _ensure_webhook_retry_logs_table()
    _ensure_api_docs_registry_table()
    _ensure_api_settings_table()
    _ensure_approval_records_table()

    # Seed default data
    _seed_default_api_gateway_data()


# -----------------------------------------------------------------------------
# API Versions Table
# -----------------------------------------------------------------------------

def _ensure_api_versions_table():
    """Create api_versions table if not exists."""
    if table_exists('api_versions'):
        return

    with get_db_context() as db:
        db.execute("""
            CREATE TABLE api_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version_code TEXT NOT NULL UNIQUE,
                version_name TEXT NOT NULL,
                description TEXT,
                base_path TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                is_default INTEGER DEFAULT 0,
                deprecation_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                notes TEXT
            )
        """)
        db.execute("CREATE INDEX idx_api_ver_code ON api_versions(version_code)")
        db.execute("CREATE INDEX idx_api_ver_active ON api_versions(is_active)")
        db.commit()


# -----------------------------------------------------------------------------
# API Route Registry Table
# -----------------------------------------------------------------------------

def _ensure_api_route_registry():
    """Create api_route_registry table if not exists."""
    if table_exists('api_route_registry'):
        return

    with get_db_context() as db:
        db.execute("""
            CREATE TABLE api_route_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_code TEXT UNIQUE NOT NULL,
                version_id INTEGER,
                method TEXT NOT NULL,
                path TEXT NOT NULL,
                module TEXT NOT NULL,
                resource TEXT NOT NULL,
                action TEXT,
                description TEXT,
                auth_required INTEGER DEFAULT 1,
                scopes_required TEXT,
                rate_limit_profile TEXT,
                is_active INTEGER DEFAULT 1,
                is_deprecated INTEGER DEFAULT 0,
                deprecated_path TEXT,
                request_schema TEXT,
                response_schema TEXT,
                query_params TEXT,
                path_params TEXT,
                example_request TEXT,
                example_response TEXT,
                error_codes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                notes TEXT,
                FOREIGN KEY (version_id) REFERENCES api_versions(id)
            )
        """)
        db.execute("CREATE INDEX idx_route_ver ON api_route_registry(version_id)")
        db.execute("CREATE INDEX idx_route_module ON api_route_registry(module)")
        db.execute("CREATE INDEX idx_route_method ON api_route_registry(method)")
        db.execute("CREATE INDEX idx_route_path ON api_route_registry(path)")
        db.execute("CREATE UNIQUE INDEX idx_route_unique ON api_route_registry(method, path, version_id)")
        db.commit()


# -----------------------------------------------------------------------------
# API Clients Table
# -----------------------------------------------------------------------------

def _ensure_api_clients_table():
    """Create api_clients table if not exists."""
    if table_exists('api_clients'):
        return

    with get_db_context() as db:
        db.execute("""
            CREATE TABLE api_clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_code TEXT UNIQUE NOT NULL,
                client_name TEXT NOT NULL,
                client_type TEXT DEFAULT 'external',
                owner_name TEXT,
                owner_email TEXT,
                department TEXT,
                integration_purpose TEXT,
                company_id INTEGER,
                branch_id INTEGER,
                status TEXT DEFAULT 'active',
                allowed_scopes TEXT,
                allowed_modules TEXT,
                allowed_ip_addresses TEXT,
                rate_limit_profile TEXT DEFAULT 'default',
                webhook_permissions TEXT,
                max_requests_per_day INTEGER,
                max_requests_per_month INTEGER,
                require_approval INTEGER DEFAULT 0,
                approval_status TEXT DEFAULT 'pending',
                approved_by INTEGER,
                approved_at TEXT,
                rejection_reason TEXT,
                last_used_at TEXT,
                last_ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                metadata TEXT
            )
        """)
        db.execute("CREATE INDEX idx_client_code ON api_clients(client_code)")
        db.execute("CREATE INDEX idx_client_status ON api_clients(status)")
        db.execute("CREATE INDEX idx_client_company ON api_clients(company_id)")
        db.commit()


# -----------------------------------------------------------------------------
# API Client Credentials Table
# -----------------------------------------------------------------------------

def _ensure_api_client_credentials_table():
    """Create api_client_credentials table if not exists."""
    if table_exists('api_client_credentials'):
        return

    with get_db_context() as db:
        db.execute("""
            CREATE TABLE api_client_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                credential_type TEXT NOT NULL,
                api_key_hash TEXT,
                api_key_prefix TEXT,
                secret_hash TEXT,
                jwt_secret TEXT,
                oauth_client_id TEXT,
                oauth_client_secret_hash TEXT,
                token_endpoint TEXT,
                refresh_token_hash TEXT,
                expires_at TEXT,
                is_active INTEGER DEFAULT 1,
                is_primary INTEGER DEFAULT 0,
                last_used_at TEXT,
                last_used_ip TEXT,
                rotated_at TEXT,
                rotated_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                notes TEXT,
                FOREIGN KEY (client_id) REFERENCES api_clients(id) ON DELETE CASCADE
            )
        """)
        db.execute("CREATE INDEX idx_cred_client ON api_client_credentials(client_id)")
        db.execute("CREATE INDEX idx_cred_type ON api_client_credentials(credential_type)")
        db.execute("CREATE INDEX idx_cred_key_prefix ON api_client_credentials(api_key_prefix)")
        db.commit()


# -----------------------------------------------------------------------------
# API Scopes Table
# -----------------------------------------------------------------------------

def _ensure_api_scopes_table():
    """Create api_scopes table if not exists."""
    if table_exists('api_scopes'):
        return

    with get_db_context() as db:
        db.execute("""
            CREATE TABLE api_scopes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scope_code TEXT UNIQUE NOT NULL,
                scope_name TEXT NOT NULL,
                description TEXT,
                module TEXT NOT NULL,
                resource TEXT,
                action TEXT,
                parent_scope TEXT,
                is_system INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                danger_level TEXT DEFAULT 'low',
                requires_approval INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        """)
        db.execute("CREATE INDEX idx_scope_code ON api_scopes(scope_code)")
        db.execute("CREATE INDEX idx_scope_module ON api_scopes(module)")
        db.execute("CREATE INDEX idx_scope_active ON api_scopes(is_active)")
        db.commit()


# -----------------------------------------------------------------------------
# API Access Policies Table
# -----------------------------------------------------------------------------

def _ensure_api_access_policies_table():
    """Create api_access_policies table if not exists."""
    if table_exists('api_access_policies'):
        return

    with get_db_context() as db:
        db.execute("""
            CREATE TABLE api_access_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                policy_code TEXT UNIQUE NOT NULL,
                policy_name TEXT NOT NULL,
                description TEXT,
                policy_type TEXT NOT NULL,
                priority INTEGER DEFAULT 100,
                target_type TEXT NOT NULL,
                target_id INTEGER,
                scope_id INTEGER,
                module TEXT,
                resource TEXT,
                action TEXT,
                effect TEXT NOT NULL,
                conditions TEXT,
                is_active INTEGER DEFAULT 1,
                requires_approval INTEGER DEFAULT 0,
                approval_status TEXT DEFAULT 'approved',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                notes TEXT,
                FOREIGN KEY (scope_id) REFERENCES api_scopes(id),
                FOREIGN KEY (target_id) REFERENCES api_clients(id)
            )
        """)
        db.execute("CREATE INDEX idx_policy_code ON api_access_policies(policy_code)")
        db.execute("CREATE INDEX idx_policy_type ON api_access_policies(policy_type)")
        db.execute("CREATE INDEX idx_policy_target ON api_access_policies(target_type, target_id)")
        db.commit()


# -----------------------------------------------------------------------------
# API Rate Limit Profiles Table
# -----------------------------------------------------------------------------

def _ensure_api_rate_limit_profiles_table():
    """Create api_rate_limit_profiles table if not exists."""
    if table_exists('api_rate_limit_profiles'):
        return

    with get_db_context() as db:
        db.execute("""
            CREATE TABLE api_rate_limit_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_code TEXT UNIQUE NOT NULL,
                profile_name TEXT NOT NULL,
                description TEXT,
                requests_per_second INTEGER DEFAULT 10,
                requests_per_minute INTEGER DEFAULT 100,
                requests_per_hour INTEGER DEFAULT 1000,
                requests_per_day INTEGER DEFAULT 10000,
                burst_size INTEGER DEFAULT 20,
                is_active INTEGER DEFAULT 1,
                is_system INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                notes TEXT
            )
        """)
        db.execute("CREATE INDEX idx_rl_profile_code ON api_rate_limit_profiles(profile_code)")
        db.commit()


# -----------------------------------------------------------------------------
# API Request Logs Table
# -----------------------------------------------------------------------------

def _ensure_api_request_logs_table():
    """Create api_request_logs table if not exists."""
    if table_exists('api_request_logs'):
        return

    with get_db_context() as db:
        db.execute("""
            CREATE TABLE api_request_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT UNIQUE NOT NULL,
                trace_id TEXT,
                client_id INTEGER,
                client_code TEXT,
                api_key_prefix TEXT,
                user_id INTEGER,
                user_username TEXT,
                method TEXT NOT NULL,
                path TEXT NOT NULL,
                query_string TEXT,
                request_headers TEXT,
                request_body_preview TEXT,
                request_body_size INTEGER,
                response_status_code INTEGER,
                response_body_preview TEXT,
                response_body_size INTEGER,
                response_time_ms INTEGER,
                ip_address TEXT,
                user_agent TEXT,
                auth_type TEXT,
                auth_scopes TEXT,
                rate_limit_remaining INTEGER,
                rate_limit_reset_at TEXT,
                company_id INTEGER,
                branch_id INTEGER,
                module TEXT,
                resource TEXT,
                action TEXT,
                is_cached INTEGER DEFAULT 0,
                cache_hit INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES api_clients(id)
            )
        """)
        db.execute("CREATE INDEX idx_req_client ON api_request_logs(client_id)")
        db.execute("CREATE INDEX idx_req_user ON api_request_logs(user_id)")
        db.execute("CREATE INDEX idx_req_path ON api_request_logs(path)")
        db.execute("CREATE INDEX idx_req_status ON api_request_logs(response_status_code)")
        db.execute("CREATE INDEX idx_req_created ON api_request_logs(created_at)")
        db.execute("CREATE INDEX idx_req_trace ON api_request_logs(trace_id)")
        db.commit()


# -----------------------------------------------------------------------------
# API Error Logs Table
# -----------------------------------------------------------------------------

def _ensure_api_error_logs_table():
    """Create api_error_logs table if not exists."""
    if table_exists('api_error_logs'):
        return

    with get_db_context() as db:
        db.execute("""
            CREATE TABLE api_error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_id TEXT UNIQUE NOT NULL,
                request_id TEXT,
                trace_id TEXT,
                error_code TEXT NOT NULL,
                error_type TEXT NOT NULL,
                error_message TEXT NOT NULL,
                error_details TEXT,
                stack_trace TEXT,
                client_id INTEGER,
                client_code TEXT,
                user_id INTEGER,
                method TEXT,
                path TEXT,
                query_string TEXT,
                request_body_preview TEXT,
                ip_address TEXT,
                user_agent TEXT,
                company_id INTEGER,
                module TEXT,
                resource TEXT,
                action TEXT,
                response_status_code INTEGER,
                is_resolved INTEGER DEFAULT 0,
                resolved_at TEXT,
                resolved_by INTEGER,
                resolution_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES api_clients(id)
            )
        """)
        db.execute("CREATE INDEX idx_err_code ON api_error_logs(error_code)")
        db.execute("CREATE INDEX idx_err_type ON api_error_logs(error_type)")
        db.execute("CREATE INDEX idx_err_client ON api_error_logs(client_id)")
        db.execute("CREATE INDEX idx_err_created ON api_error_logs(created_at)")
        db.execute("CREATE INDEX idx_err_trace ON api_error_logs(trace_id)")
        db.commit()


# -----------------------------------------------------------------------------
# Integration Profiles Table
# -----------------------------------------------------------------------------

def _ensure_integration_profiles_table():
    """Create integration_profiles table if not exists."""
    if table_exists('integration_profiles'):
        return

    with get_db_context() as db:
        db.execute("""
            CREATE TABLE integration_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                integration_code TEXT UNIQUE NOT NULL,
                integration_name TEXT NOT NULL,
                integration_type TEXT NOT NULL,
                module TEXT NOT NULL,
                direction TEXT NOT NULL,
                description TEXT,
                connection_config TEXT,
                credential_id INTEGER,
                webhook_subscription_id INTEGER,
                module_scope TEXT,
                payload_mapping_rules TEXT,
                transformation_rules TEXT,
                sync_schedule TEXT,
                sync_trigger TEXT,
                retry_policy TEXT,
                timeout_seconds INTEGER DEFAULT 30,
                is_active INTEGER DEFAULT 1,
                requires_approval INTEGER DEFAULT 0,
                approval_status TEXT DEFAULT 'approved',
                approved_by INTEGER,
                approved_at TEXT,
                last_successful_run TEXT,
                last_failed_run TEXT,
                last_run_status TEXT,
                total_runs INTEGER DEFAULT 0,
                successful_runs INTEGER DEFAULT 0,
                failed_runs INTEGER DEFAULT 0,
                owner_id INTEGER,
                owner_name TEXT,
                owner_email TEXT,
                department TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                metadata TEXT,
                FOREIGN KEY (credential_id) REFERENCES api_client_credentials(id),
                FOREIGN KEY (webhook_subscription_id) REFERENCES webhook_subscriptions(id)
            )
        """)
        db.execute("CREATE INDEX idx_int_code ON integration_profiles(integration_code)")
        db.execute("CREATE INDEX idx_int_type ON integration_profiles(integration_type)")
        db.execute("CREATE INDEX idx_int_module ON integration_profiles(module)")
        db.execute("CREATE INDEX idx_int_active ON integration_profiles(is_active)")
        db.commit()


# -----------------------------------------------------------------------------
# Integration Runs Table
# -----------------------------------------------------------------------------

def _ensure_integration_runs_table():
    """Create integration_runs table if not exists."""
    if table_exists('integration_runs'):
        return

    with get_db_context() as db:
        db.execute("""
            CREATE TABLE integration_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT UNIQUE NOT NULL,
                integration_id INTEGER NOT NULL,
                integration_code TEXT NOT NULL,
                run_type TEXT NOT NULL,
                direction TEXT NOT NULL,
                status TEXT NOT NULL,
                trigger_type TEXT,
                trigger_source TEXT,
                request_headers TEXT,
                request_body_preview TEXT,
                request_body_size INTEGER,
                response_status_code INTEGER,
                response_body_preview TEXT,
                response_body_size INTEGER,
                records_processed INTEGER DEFAULT 0,
                records_success INTEGER DEFAULT 0,
                records_failed INTEGER DEFAULT 0,
                execution_time_ms INTEGER,
                error_message TEXT,
                error_details TEXT,
                ip_address TEXT,
                company_id INTEGER,
                branch_id INTEGER,
                started_at TEXT,
                completed_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (integration_id) REFERENCES integration_profiles(id)
            )
        """)
        db.execute("CREATE INDEX idx_run_integration ON integration_runs(integration_id)")
        db.execute("CREATE INDEX idx_run_status ON integration_runs(status)")
        db.execute("CREATE INDEX idx_run_created ON integration_runs(created_at)")
        db.commit()


# -----------------------------------------------------------------------------
# Integration Exceptions Table
# -----------------------------------------------------------------------------

def _ensure_integration_exceptions_table():
    """Create integration_exceptions table if not exists."""
    if table_exists('integration_exceptions'):
        return

    with get_db_context() as db:
        db.execute("""
            CREATE TABLE integration_exceptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exception_code TEXT UNIQUE NOT NULL,
                integration_id INTEGER,
                integration_run_id INTEGER,
                exception_type TEXT NOT NULL,
                error_code TEXT,
                error_message TEXT NOT NULL,
                error_details TEXT,
                payload_preview TEXT,
                affected_records TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                next_retry_at TEXT,
                is_resolved INTEGER DEFAULT 0,
                resolved_at TEXT,
                resolved_by INTEGER,
                resolution_notes TEXT,
                company_id INTEGER,
                branch_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (integration_id) REFERENCES integration_profiles(id),
                FOREIGN KEY (integration_run_id) REFERENCES integration_runs(id)
            )
        """)
        db.execute("CREATE INDEX idx_int_exc_integration ON integration_exceptions(integration_id)")
        db.execute("CREATE INDEX idx_int_exc_status ON integration_exceptions(is_resolved)")
        db.execute("CREATE INDEX idx_int_exc_created ON integration_exceptions(created_at)")
        db.commit()


# -----------------------------------------------------------------------------
# Webhook Events Table
# -----------------------------------------------------------------------------

def _ensure_webhook_events_table():
    """Create webhook_events table if not exists."""
    if table_exists('webhook_events'):
        return

    with get_db_context() as db:
        db.execute("""
            CREATE TABLE webhook_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_code TEXT UNIQUE NOT NULL,
                event_name TEXT NOT NULL,
                module TEXT NOT NULL,
                resource TEXT NOT NULL,
                description TEXT,
                payload_schema TEXT,
                example_payload TEXT,
                version TEXT,
                is_active INTEGER DEFAULT 1,
                is_system INTEGER DEFAULT 0,
                danger_level TEXT DEFAULT 'low',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                notes TEXT
            )
        """)
        db.execute("CREATE INDEX idx_wh_event_code ON webhook_events(event_code)")
        db.execute("CREATE INDEX idx_wh_event_module ON webhook_events(module)")
        db.execute("CREATE INDEX idx_wh_event_active ON webhook_events(is_active)")
        db.commit()


# -----------------------------------------------------------------------------
# Webhook Subscriptions Table
# -----------------------------------------------------------------------------

def _ensure_webhook_subscriptions_table():
    """Create webhook_subscriptions table if not exists."""
    if table_exists('webhook_subscriptions'):
        return

    with get_db_context() as db:
        db.execute("""
            CREATE TABLE webhook_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscription_code TEXT UNIQUE NOT NULL,
                endpoint_name TEXT NOT NULL,
                target_url TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                subscribed_events TEXT NOT NULL,
                auth_method TEXT DEFAULT 'none',
                auth_secret TEXT,
                auth_header_name TEXT DEFAULT 'X-Webhook-Signature',
                signing_algorithm TEXT DEFAULT 'sha256',
                include_filters TEXT,
                exclude_filters TEXT,
                retry_policy TEXT DEFAULT '{"max_retries":3,"backoff":"exponential"}',
                timeout_seconds INTEGER DEFAULT 30,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                success_rate REAL DEFAULT 0.0,
                total_deliveries INTEGER DEFAULT 0,
                successful_deliveries INTEGER DEFAULT 0,
                failed_deliveries INTEGER DEFAULT 0,
                last_delivery_at TEXT,
                last_delivery_status TEXT,
                last_response_code INTEGER,
                last_error_message TEXT,
                environment_tag TEXT,
                integration_profile_id INTEGER,
                owner_name TEXT,
                owner_email TEXT,
                is_verified INTEGER DEFAULT 0,
                verified_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                metadata TEXT,
                FOREIGN KEY (integration_profile_id) REFERENCES integration_profiles(id)
            )
        """)
        db.execute("CREATE INDEX idx_wh_sub_code ON webhook_subscriptions(subscription_code)")
        db.execute("CREATE INDEX idx_wh_sub_active ON webhook_subscriptions(active)")
        db.execute("CREATE INDEX idx_wh_sub_events ON webhook_subscriptions(subscribed_events)")
        db.commit()


# -----------------------------------------------------------------------------
# Webhook Deliveries Table
# -----------------------------------------------------------------------------

def _ensure_webhook_deliveries_table():
    """Create webhook_deliveries table if not exists."""
    if table_exists('webhook_deliveries'):
        return

    with get_db_context() as db:
        db.execute("""
            CREATE TABLE webhook_deliveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                delivery_id TEXT UNIQUE NOT NULL,
                event_id INTEGER NOT NULL,
                event_code TEXT NOT NULL,
                subscription_id INTEGER NOT NULL,
                subscription_code TEXT NOT NULL,
                delivery_status TEXT NOT NULL,
                http_status_code INTEGER,
                response_body_preview TEXT,
                response_time_ms INTEGER,
                attempt_number INTEGER DEFAULT 1,
                max_attempts INTEGER DEFAULT 3,
                next_retry_at TEXT,
                request_headers TEXT,
                request_body TEXT,
                request_body_hash TEXT,
                request_timestamp TEXT,
                response_headers TEXT,
                ip_address TEXT,
                error_code TEXT,
                error_message TEXT,
                error_details TEXT,
                is_idempotent INTEGER DEFAULT 1,
                idempotency_key TEXT,
                webhook_signature TEXT,
                signature_valid INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                delivered_at TEXT,
                completed_at TEXT,
                FOREIGN KEY (event_id) REFERENCES webhook_events(id),
                FOREIGN KEY (subscription_id) REFERENCES webhook_subscriptions(id)
            )
        """)
        db.execute("CREATE INDEX idx_wh_delivery_sub ON webhook_deliveries(subscription_id)")
        db.execute("CREATE INDEX idx_wh_delivery_status ON webhook_deliveries(delivery_status)")
        db.execute("CREATE INDEX idx_wh_delivery_event ON webhook_deliveries(event_code)")
        db.execute("CREATE INDEX idx_wh_delivery_created ON webhook_deliveries(created_at)")
        db.execute("CREATE INDEX idx_wh_delivery_idemp ON webhook_deliveries(idempotency_key)")
        db.commit()


# -----------------------------------------------------------------------------
# Webhook Retry Logs Table
# -----------------------------------------------------------------------------

def _ensure_webhook_retry_logs_table():
    """Create webhook_retry_logs table if not exists."""
    if table_exists('webhook_retry_logs'):
        return

    with get_db_context() as db:
        db.execute("""
            CREATE TABLE webhook_retry_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                retry_id TEXT UNIQUE NOT NULL,
                delivery_id TEXT NOT NULL,
                subscription_id INTEGER NOT NULL,
                event_code TEXT NOT NULL,
                attempt_number INTEGER NOT NULL,
                retry_status TEXT NOT NULL,
                http_status_code INTEGER,
                response_body_preview TEXT,
                response_time_ms INTEGER,
                error_code TEXT,
                error_message TEXT,
                error_details TEXT,
                next_retry_at TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                FOREIGN KEY (delivery_id) REFERENCES webhook_deliveries(id),
                FOREIGN KEY (subscription_id) REFERENCES webhook_subscriptions(id)
            )
        """)
        db.execute("CREATE INDEX idx_wh_retry_delivery ON webhook_retry_logs(delivery_id)")
        db.execute("CREATE INDEX idx_wh_retry_sub ON webhook_retry_logs(subscription_id)")
        db.execute("CREATE INDEX idx_wh_retry_created ON webhook_retry_logs(created_at)")
        db.commit()


# -----------------------------------------------------------------------------
# API Docs Registry Table
# -----------------------------------------------------------------------------

def _ensure_api_docs_registry_table():
    """Create api_docs_registry table if not exists."""
    if table_exists('api_docs_registry'):
        return

    with get_db_context() as db:
        db.execute("""
            CREATE TABLE api_docs_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_code TEXT UNIQUE NOT NULL,
                module TEXT NOT NULL,
                version_id INTEGER,
                version_code TEXT,
                route_id INTEGER,
                route_path TEXT,
                route_method TEXT,
                doc_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                content TEXT,
                request_schema TEXT,
                response_schema TEXT,
                query_params_schema TEXT,
                path_params_schema TEXT,
                example_request TEXT,
                example_response TEXT,
                error_codes TEXT,
                auth_mode TEXT,
                auth_scopes TEXT,
                rate_limit_info TEXT,
                changelog TEXT,
                is_published INTEGER DEFAULT 0,
                published_at TEXT,
                published_by INTEGER,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                notes TEXT,
                metadata TEXT,
                FOREIGN KEY (version_id) REFERENCES api_versions(id),
                FOREIGN KEY (route_id) REFERENCES api_route_registry(id)
            )
        """)
        db.execute("CREATE INDEX idx_doc_module ON api_docs_registry(module)")
        db.execute("CREATE INDEX idx_doc_version ON api_docs_registry(version_id)")
        db.execute("CREATE INDEX idx_doc_type ON api_docs_registry(doc_type)")
        db.execute("CREATE INDEX idx_doc_published ON api_docs_registry(is_published)")
        db.commit()


# -----------------------------------------------------------------------------
# API Settings Table
# -----------------------------------------------------------------------------

def _ensure_api_settings_table():
    """Create api_settings table if not exists."""
    if table_exists('api_settings'):
        return

    with get_db_context() as db:
        db.execute("""
            CREATE TABLE api_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_name TEXT NOT NULL,
                setting_value TEXT,
                setting_type TEXT DEFAULT 'string',
                category TEXT NOT NULL,
                description TEXT,
                is_encrypted INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                requires_approval INTEGER DEFAULT 0,
                approval_status TEXT DEFAULT 'approved',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by INTEGER,
                notes TEXT,
                validation_rules TEXT
            )
        """)
        db.execute("CREATE INDEX idx_set_key ON api_settings(setting_key)")
        db.execute("CREATE INDEX idx_set_category ON api_settings(category)")
        db.commit()


# -----------------------------------------------------------------------------
# Approval Records Table
# -----------------------------------------------------------------------------

def _ensure_approval_records_table():
    """Create approval_records table if not exists."""
    if table_exists('approval_records'):
        return

    with get_db_context() as db:
        db.execute("""
            CREATE TABLE approval_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                approval_code TEXT UNIQUE NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                entity_code TEXT,
                approval_type TEXT NOT NULL,
                current_status TEXT NOT NULL,
                priority TEXT DEFAULT 'normal',
                requester_id INTEGER NOT NULL,
                requester_name TEXT,
                requester_email TEXT,
                approver_id INTEGER,
                approver_name TEXT,
                submitted_at TEXT NOT NULL,
                decided_at TEXT,
                decision_notes TEXT,
                rejection_reason TEXT,
                previous_value TEXT,
                new_value TEXT,
                change_summary TEXT,
                is_revoked INTEGER DEFAULT 0,
                revoked_at TEXT,
                revoked_by INTEGER,
                revocation_reason TEXT,
                is_expired INTEGER DEFAULT 0,
                expired_at TEXT,
                workflow_config TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                metadata TEXT
            )
        """)
        db.execute("CREATE INDEX idx_approval_entity ON approval_records(entity_type, entity_id)")
        db.execute("CREATE INDEX idx_approval_status ON approval_records(current_status)")
        db.execute("CREATE INDEX idx_approval_type ON approval_records(approval_type)")
        db.execute("CREATE INDEX idx_approval_requester ON approval_records(requester_id)")
        db.commit()


# =============================================================================
# SEED DEFAULT DATA
# =============================================================================

def _seed_default_api_gateway_data():
    """Seed default API Gateway configuration data."""

    # Seed API Versions
    default_versions = [
        {
            'version_code': 'v1',
            'version_name': 'Version 1',
            'description': 'Initial API version with core endpoints',
            'base_path': '/api/v1',
            'is_active': 1,
            'is_default': 1,
        },
        {
            'version_code': 'v2',
            'version_name': 'Version 2',
            'description': 'Enhanced API with improved filtering and pagination',
            'base_path': '/api/v2',
            'is_active': 1,
            'is_default': 0,
        },
    ]

    for ver in default_versions:
        existing = get_one("SELECT id FROM api_versions WHERE version_code = ?", (ver['version_code'],))
        if not existing:
            with get_db_context() as db:
                db.execute("""
                    INSERT INTO api_versions (version_code, version_name, description, base_path,
                                            is_active, is_default)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (ver['version_code'], ver['version_name'], ver['description'],
                      ver['base_path'], ver['is_active'], ver['is_default']))
                db.commit()

    # Seed Rate Limit Profiles
    default_rl_profiles = [
        {
            'profile_code': 'default',
            'profile_name': 'Default Rate Limit',
            'description': 'Standard rate limit for regular API clients',
            'requests_per_second': 10,
            'requests_per_minute': 100,
            'requests_per_hour': 1000,
            'requests_per_day': 10000,
            'burst_size': 20,
            'is_system': 1,
        },
        {
            'profile_code': 'basic',
            'profile_name': 'Basic Rate Limit',
            'description': 'Limited rate for basic tier clients',
            'requests_per_second': 1,
            'requests_per_minute': 10,
            'requests_per_hour': 100,
            'requests_per_day': 1000,
            'burst_size': 5,
            'is_system': 1,
        },
        {
            'profile_code': 'premium',
            'profile_name': 'Premium Rate Limit',
            'description': 'Higher rate limits for premium partners',
            'requests_per_second': 50,
            'requests_per_minute': 500,
            'requests_per_hour': 5000,
            'requests_per_day': 50000,
            'burst_size': 100,
            'is_system': 1,
        },
        {
            'profile_code': 'enterprise',
            'profile_name': 'Enterprise Rate Limit',
            'description': 'Unlimited rate for enterprise clients',
            'requests_per_second': 100,
            'requests_per_minute': 1000,
            'requests_per_hour': 10000,
            'requests_per_day': 100000,
            'burst_size': 200,
            'is_system': 1,
        },
    ]

    for profile in default_rl_profiles:
        existing = get_one("SELECT id FROM api_rate_limit_profiles WHERE profile_code = ?",
                          (profile['profile_code'],))
        if not existing:
            with get_db_context() as db:
                db.execute("""
                    INSERT INTO api_rate_limit_profiles (profile_code, profile_name, description,
                        requests_per_second, requests_per_minute, requests_per_hour,
                        requests_per_day, burst_size, is_system)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (profile['profile_code'], profile['profile_name'], profile['description'],
                      profile['requests_per_second'], profile['requests_per_minute'],
                      profile['requests_per_hour'], profile['requests_per_day'],
                      profile['burst_size'], profile['is_system']))
                db.commit()

    # Seed API Scopes
    _seed_api_scopes()

    # Seed Webhook Events
    _seed_webhook_events()

    # Seed API Settings
    _seed_api_settings()


def _seed_api_scopes():
    """Seed default API scopes for all modules."""

    scope_templates = [
        # Sales & CRM
        ('sales.customers.read', 'Read Customers', 'sales', 'customers', 'view', 'low', 0),
        ('sales.customers.write', 'Create/Update Customers', 'sales', 'customers', 'create', 'medium', 0),
        ('sales.customers.delete', 'Delete Customers', 'sales', 'customers', 'delete', 'high', 1),
        ('sales.orders.read', 'Read Sales Orders', 'sales', 'orders', 'view', 'low', 0),
        ('sales.orders.write', 'Create/Update Orders', 'sales', 'orders', 'create', 'medium', 0),
        ('sales.quotations.read', 'Read Quotations', 'sales', 'quotations', 'view', 'low', 0),
        ('sales.invoices.read', 'Read Invoices', 'sales', 'invoices', 'view', 'medium', 0),

        # Inventory & Warehouse
        ('inventory.items.read', 'Read Inventory Items', 'wms', 'items', 'view', 'low', 0),
        ('inventory.items.write', 'Create/Update Items', 'wms', 'items', 'create', 'medium', 0),
        ('inventory.stock.read', 'Read Stock Levels', 'wms', 'inventory', 'view', 'low', 0),
        ('inventory.stock.adjust', 'Adjust Stock', 'wms', 'inventory', 'adjust', 'high', 1),
        ('inventory.transfers.read', 'Read Transfers', 'wms', 'transfers', 'view', 'low', 0),
        ('inventory.warehouses.read', 'Read Warehouses', 'wms', 'warehouses', 'view', 'low', 0),

        # Procurement
        ('procurement.suppliers.read', 'Read Suppliers', 'procurement', 'suppliers', 'view', 'low', 0),
        ('procurement.orders.read', 'Read Purchase Orders', 'procurement', 'orders', 'view', 'low', 0),
        ('procurement.orders.write', 'Create Purchase Orders', 'procurement', 'orders', 'create', 'medium', 0),
        ('procurement.receipts.read', 'Read Receipts', 'procurement', 'receiving', 'view', 'low', 0),

        # Finance
        ('finance.invoices.read', 'Read Invoices', 'finance', 'ar_invoices', 'view', 'medium', 0),
        ('finance.invoices.write', 'Create/Update Invoices', 'finance', 'ar_invoices', 'create', 'high', 1),
        ('finance.payments.read', 'Read Payments', 'finance', 'ar_receipts', 'view', 'medium', 0),
        ('finance.accounts.read', 'Read Chart of Accounts', 'finance', 'accounts', 'view', 'medium', 0),
        ('finance.journals.read', 'Read Journal Entries', 'finance', 'journals', 'view', 'high', 0),
        ('finance.journals.write', 'Create Journal Entries', 'finance', 'journals', 'create', 'critical', 1),

        # HR & Users
        ('hr.employees.read', 'Read Employees', 'hr', 'employees', 'view', 'medium', 0),
        ('hr.employees.write', 'Create/Update Employees', 'hr', 'employees', 'create', 'high', 1),
        ('hr.attendance.read', 'Read Attendance', 'hr', 'attendance', 'view', 'medium', 0),
        ('users.read', 'Read Users', 'platform', 'users', 'view', 'high', 0),
        ('users.write', 'Create/Update Users', 'platform', 'users', 'create', 'critical', 1),

        # Assets
        ('assets.assets.read', 'Read Assets', 'assets', 'assets', 'view', 'low', 0),
        ('assets.assets.write', 'Create/Update Assets', 'assets', 'assets', 'create', 'medium', 0),
        ('assets.depreciation.read', 'Read Depreciation', 'assets', 'depreciation', 'view', 'medium', 0),
        ('assets.maintenance.read', 'Read Maintenance', 'assets', 'maintenance', 'view', 'low', 0),

        # Quality
        ('quality.inspections.read', 'Read Inspections', 'quality', 'inspections', 'view', 'low', 0),
        ('quality.ncr.read', 'Read NCRs', 'quality', 'ncr', 'view', 'medium', 0),
        ('quality.capa.read', 'Read CAPAs', 'quality', 'capa', 'view', 'medium', 0),

        # Logistics
        ('logistics.trips.read', 'Read Trips', 'logistics', 'trips', 'view', 'low', 0),
        ('logistics.deliveries.read', 'Read Deliveries', 'logistics', 'deliveries', 'view', 'low', 0),

        # Reports
        ('reports.dashboard.read', 'Read Dashboard', 'reports', 'dashboard', 'view', 'low', 0),
        ('reports.export', 'Export Reports', 'reports', 'export', 'export', 'medium', 0),
    ]

    for scope_code, scope_name, module, resource, action, danger, approval in scope_templates:
        existing = get_one("SELECT id FROM api_scopes WHERE scope_code = ?", (scope_code,))
        if not existing:
            with get_db_context() as db:
                db.execute("""
                    INSERT INTO api_scopes (scope_code, scope_name, module, resource, action,
                                          danger_level, requires_approval, is_system)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """, (scope_code, scope_name, module, resource, action, danger, approval))
                db.commit()


def _seed_webhook_events():
    """Seed default webhook event catalog."""

    webhook_templates = [
        # Sales & CRM
        ('customer.created', 'Customer Created', 'sales', 'customers',
         'Fired when a new customer is created', 'low'),
        ('customer.updated', 'Customer Updated', 'sales', 'customers',
         'Fired when customer details are updated', 'low'),
        ('customer.deleted', 'Customer Deleted', 'sales', 'customers',
         'Fired when a customer is deleted', 'medium'),
        ('order.created', 'Order Created', 'sales', 'orders',
         'Fired when a new sales order is created', 'low'),
        ('order.updated', 'Order Updated', 'sales', 'orders',
         'Fired when order status or details change', 'low'),
        ('order.confirmed', 'Order Confirmed', 'sales', 'orders',
         'Fired when an order is confirmed', 'low'),
        ('order.cancelled', 'Order Cancelled', 'sales', 'orders',
         'Fired when an order is cancelled', 'medium'),
        ('order.shipped', 'Order Shipped', 'sales', 'orders',
         'Fired when an order is shipped', 'low'),
        ('order.delivered', 'Order Delivered', 'sales', 'orders',
         'Fired when an order is delivered', 'low'),
        ('quotation.created', 'Quotation Created', 'sales', 'quotations',
         'Fired when a quotation is created', 'low'),
        ('quotation.sent', 'Quotation Sent', 'sales', 'quotations',
         'Fired when a quotation is sent to customer', 'low'),
        ('invoice.created', 'Invoice Created', 'finance', 'ar_invoices',
         'Fired when an AR invoice is created', 'medium'),
        ('invoice.posted', 'Invoice Posted', 'finance', 'ar_invoices',
         'Fired when an invoice is posted', 'medium'),
        ('invoice.paid', 'Invoice Paid', 'finance', 'ar_invoices',
         'Fired when an invoice is fully paid', 'low'),

        # Inventory
        ('inventory.updated', 'Inventory Updated', 'wms', 'inventory',
         'Fired when stock levels change', 'low'),
        ('inventory.low_stock', 'Low Stock Alert', 'wms', 'inventory',
         'Fired when stock falls below reorder point', 'medium'),
        ('inventory.transfer.created', 'Transfer Created', 'wms', 'transfers',
         'Fired when a stock transfer is created', 'low'),
        ('inventory.transfer.completed', 'Transfer Completed', 'wms', 'transfers',
         'Fired when a transfer is completed', 'low'),
        ('inventory.adjustment.created', 'Adjustment Created', 'wms', 'adjustments',
         'Fired when a stock adjustment is made', 'medium'),

        # Procurement
        ('supplier.created', 'Supplier Created', 'procurement', 'suppliers',
         'Fired when a new supplier is added', 'low'),
        ('purchase_order.created', 'PO Created', 'procurement', 'orders',
         'Fired when a purchase order is created', 'low'),
        ('purchase_order.approved', 'PO Approved', 'procurement', 'orders',
         'Fired when a PO is approved', 'medium'),
        ('purchase_order.received', 'PO Received', 'procurement', 'receiving',
         'Fired when goods are received against a PO', 'low'),

        # Finance
        ('payment.received', 'Payment Received', 'finance', 'ar_receipts',
         'Fired when a payment is received', 'medium'),
        ('payment.processed', 'Payment Processed', 'finance', 'ap_payments',
         'Fired when an AP payment is processed', 'medium'),
        ('journal.posted', 'Journal Posted', 'finance', 'journals',
         'Fired when a journal entry is posted', 'high'),
        ('budget.exceeded', 'Budget Exceeded', 'finance', 'budgets',
         'Fired when spending exceeds budget', 'high'),

        # HR
        ('user.created', 'User Created', 'platform', 'users',
         'Fired when a new user is created', 'high'),
        ('user.updated', 'User Updated', 'platform', 'users',
         'Fired when user details change', 'medium'),
        ('employee.created', 'Employee Created', 'hr', 'employees',
         'Fired when a new employee is added', 'medium'),
        ('employee.terminated', 'Employee Terminated', 'hr', 'employees',
         'Fired when an employee record is terminated', 'high'),

        # Assets
        ('asset.created', 'Asset Created', 'assets', 'assets',
         'Fired when a new asset is registered', 'low'),
        ('asset.updated', 'Asset Updated', 'assets', 'assets',
         'Fired when asset details change', 'low'),
        ('asset.transferred', 'Asset Transferred', 'assets', 'transfers',
         'Fired when an asset is transferred', 'medium'),
        ('asset.depreciation.run', 'Depreciation Run', 'assets', 'depreciation',
         'Fired when depreciation is calculated', 'medium'),
        ('asset.disposed', 'Asset Disposed', 'assets', 'disposal',
         'Fired when an asset is disposed', 'high'),
        ('maintenance.scheduled', 'Maintenance Scheduled', 'assets', 'maintenance_schedules',
         'Fired when preventive maintenance is scheduled', 'low'),
        ('maintenance.completed', 'Maintenance Completed', 'assets', 'maintenance_work_orders',
         'Fired when maintenance work is completed', 'low'),
        ('work_order.created', 'Work Order Created', 'maintenance', 'work_orders',
         'Fired when a maintenance work order is created', 'low'),
        ('work_order.completed', 'Work Order Completed', 'maintenance', 'work_orders',
         'Fired when a work order is completed', 'low'),

        # Quality
        ('quality.ncr.created', 'NCR Created', 'quality', 'ncr',
         'Fired when a non-conformance report is created', 'high'),
        ('quality.ncr.resolved', 'NCR Resolved', 'quality', 'ncr',
         'Fired when an NCR is resolved', 'medium'),
        ('quality.capa.created', 'CAPA Created', 'quality', 'capa',
         'Fired when a corrective action is created', 'medium'),
        ('quality.inspection.completed', 'Inspection Completed', 'quality', 'inspections',
         'Fired when a quality inspection is completed', 'low'),

        # Logistics
        ('shipment.updated', 'Shipment Updated', 'logistics', 'shipments',
         'Fired when shipment status changes', 'low'),
        ('delivery.updated', 'Delivery Updated', 'logistics', 'deliveries',
         'Fired when delivery status changes', 'low'),
        ('driver.assigned', 'Driver Assigned', 'logistics', 'drivers',
         'Fired when a driver is assigned to a route', 'low'),

        # E-commerce
        ('ecommerce.order.imported', 'Order Imported', 'ecommerce', 'orders',
         'Fired when an order is imported from e-commerce channel', 'medium'),
        ('ecommerce.inventory.synced', 'Inventory Synced', 'ecommerce', 'inventory',
         'Fired when inventory is synced to e-commerce', 'low'),
        ('ecommerce.customer.imported', 'Customer Imported', 'ecommerce', 'customers',
         'Fired when a customer is imported from e-commerce', 'low'),

        # Platform
        ('platform.alert', 'Platform Alert', 'platform', 'alerts',
         'Fired for platform-level alerts and notifications', 'high'),
    ]

    for event_code, event_name, module, resource, description, danger in webhook_templates:
        existing = get_one("SELECT id FROM webhook_events WHERE event_code = ?", (event_code,))
        if not existing:
            with get_db_context() as db:
                db.execute("""
                    INSERT INTO webhook_events (event_code, event_name, module, resource,
                                               description, danger_level, is_system)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (event_code, event_name, module, resource, description, danger))
                db.commit()


def _seed_api_settings():
    """Seed default API settings."""

    default_settings = [
        ('api.default_version', 'Default API Version', 'v1', 'string', 'API_VERSIONING',
         'The default API version for new requests'),
        ('api.max_page_size', 'Max Page Size', '100', 'integer', 'API_VERSIONING',
         'Maximum number of records per page'),
        ('api.default_page_size', 'Default Page Size', '20', 'integer', 'API_VERSIONING',
         'Default number of records per page'),
        ('api.enable_cors', 'Enable CORS', 'true', 'boolean', 'SECURITY',
         'Enable Cross-Origin Resource Sharing'),
        ('api.cors_origins', 'CORS Allowed Origins', '*', 'string', 'SECURITY',
         'Allowed CORS origins (comma-separated)'),
        ('api.require_https', 'Require HTTPS', 'false', 'boolean', 'SECURITY',
         'Require HTTPS for all API requests'),
        ('api.rate_limit_enabled', 'Enable Rate Limiting', 'true', 'boolean', 'RATE_LIMITING',
         'Enable rate limiting globally'),
        ('api.default_rate_limit_profile', 'Default Rate Limit Profile', 'default', 'string', 'RATE_LIMITING',
         'Rate limit profile applied to all clients'),
        ('api.webhook_timeout', 'Webhook Timeout (seconds)', '30', 'integer', 'WEBHOOKS',
         'Default timeout for webhook deliveries'),
        ('api.webhook_max_retries', 'Webhook Max Retries', '3', 'integer', 'WEBHOOKS',
         'Maximum retry attempts for failed webhook deliveries'),
        ('api.webhook_retry_backoff', 'Webhook Retry Backoff', 'exponential', 'string', 'WEBHOOKS',
         'Backoff strategy: linear, exponential'),
        ('api.enable_request_logging', 'Enable Request Logging', 'true', 'boolean', 'LOGGING',
         'Log all API requests'),
        ('api.log_request_bodies', 'Log Request Bodies', 'false', 'boolean', 'LOGGING',
         'Include request bodies in logs (careful with sensitive data)'),
        ('api.enable_error_logging', 'Enable Error Logging', 'true', 'boolean', 'LOGGING',
         'Log all API errors'),
        ('api.enable_audit_trail', 'Enable Audit Trail', 'true', 'boolean', 'AUDIT',
         'Track all API configuration changes'),
        ('api.idempotency_required', 'Require Idempotency', 'false', 'boolean', 'IDEMPOTENCY',
         'Require idempotency keys for write operations'),
        ('api.idempotency_expiry_hours', 'Idempotency Key Expiry', '24', 'integer', 'IDEMPOTENCY',
         'Hours before idempotency keys expire'),
        ('api.jwt_expiry_hours', 'JWT Expiry (hours)', '24', 'integer', 'AUTH',
         'Hours before JWT tokens expire'),
        ('api.refresh_token_expiry_days', 'Refresh Token Expiry (days)', '30', 'integer', 'AUTH',
         'Days before refresh tokens expire'),
        ('api.require_api_key', 'Require API Key', 'true', 'boolean', 'AUTH',
         'Require API key for all API requests'),
        ('api.allow_client_credentials', 'Allow Client Credentials', 'true', 'boolean', 'AUTH',
         'Allow OAuth client credentials flow'),
        ('api.allow_password_grant', 'Allow Password Grant', 'true', 'boolean', 'AUTH',
         'Allow OAuth password grant flow'),
    ]

    for key, name, value, vtype, category, desc in default_settings:
        existing = get_one("SELECT id FROM api_settings WHERE setting_key = ?", (key,))
        if not existing:
            with get_db_context() as db:
                db.execute("""
                    INSERT INTO api_settings (setting_key, setting_name, setting_value, setting_type,
                                             category, description, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (key, name, value, vtype, category, desc))
                db.commit()


# =============================================================================
# API CLIENT MANAGEMENT
# =============================================================================

def generate_api_key():
    """Generate a secure API key."""
    return f"sk_{secrets.token_urlsafe(32)}"


def generate_api_secret():
    """Generate a secure API secret."""
    return secrets.token_urlsafe(48)


def hash_api_key(api_key):
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key, stored_hash):
    """Verify an API key against its hash."""
    return hmac.compare_digest(hash_api_key(api_key), stored_hash)


def get_api_clients(filters=None, page=1, per_page=50):
    """Get paginated list of API clients."""
    conditions = []
    params = []

    if filters:
        if filters.get('search'):
            conditions.append("(client_code LIKE ? OR client_name LIKE ?)")
            params.extend([f"%{filters['search']}%", f"%{filters['search']}%"])
        if filters.get('status'):
            conditions.append("status = ?")
            params.append(filters['status'])
        if filters.get('client_type'):
            conditions.append("client_type = ?")
            params.append(filters['client_type'])
        if filters.get('department'):
            conditions.append("department = ?")
            params.append(filters['department'])

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    offset = (page - 1) * per_page
    total = get_count("api_clients", where[6:] if where else "", params)
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    sql = f"""
        SELECT ac.*,
               (SELECT COUNT(*) FROM api_request_logs WHERE client_id = ac.id) as total_requests,
               (SELECT COUNT(*) FROM api_request_logs WHERE client_id = ac.id AND response_status_code >= 400) as error_requests
        FROM api_clients ac
        {where}
        ORDER BY ac.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    clients = get_all(sql, params)

    return {
        'clients': clients,
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    }


def get_api_client_by_id(client_id):
    """Get a single API client by ID."""
    return get_one("SELECT * FROM api_clients WHERE id = ?", (client_id,))


def get_api_client_by_code(client_code):
    """Get a single API client by code."""
    return get_one("SELECT * FROM api_clients WHERE client_code = ?", (client_code,))


def create_api_client(data, created_by=None):
    """Create a new API client."""
    import uuid
    client_code = data.get('client_code') or f"CLI-{uuid.uuid4().hex[:8].upper()}"

    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO api_clients (
                client_code, client_name, client_type, owner_name, owner_email,
                department, integration_purpose, company_id, branch_id, status,
                allowed_scopes, allowed_modules, allowed_ip_addresses,
                rate_limit_profile, webhook_permissions, max_requests_per_day,
                max_requests_per_month, require_approval, approval_status,
                created_by, notes, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            client_code,
            data.get('client_name'),
            data.get('client_type', 'external'),
            data.get('owner_name'),
            data.get('owner_email'),
            data.get('department'),
            data.get('integration_purpose'),
            data.get('company_id'),
            data.get('branch_id'),
            data.get('status', 'pending'),
            json.dumps(data.get('allowed_scopes', [])) if isinstance(data.get('allowed_scopes'), list) else data.get('allowed_scopes'),
            json.dumps(data.get('allowed_modules', [])) if isinstance(data.get('allowed_modules'), list) else data.get('allowed_modules'),
            data.get('allowed_ip_addresses'),
            data.get('rate_limit_profile', 'default'),
            json.dumps(data.get('webhook_permissions', [])) if isinstance(data.get('webhook_permissions'), list) else data.get('webhook_permissions'),
            data.get('max_requests_per_day'),
            data.get('max_requests_per_month'),
            1 if data.get('require_approval') else 0,
            'approved' if not data.get('require_approval') else 'pending',
            created_by,
            data.get('notes'),
            json.dumps(data.get('metadata', {})) if isinstance(data.get('metadata'), dict) else data.get('metadata')
        ))
        db.commit()
        return cursor.lastrowid


def update_api_client(client_id, data):
    """Update an existing API client."""
    fields = []
    values = []

    updateable = [
        'client_name', 'client_type', 'owner_name', 'owner_email',
        'department', 'integration_purpose', 'company_id', 'branch_id',
        'status', 'allowed_scopes', 'allowed_modules', 'allowed_ip_addresses',
        'rate_limit_profile', 'webhook_permissions', 'max_requests_per_day',
        'max_requests_per_month', 'require_approval', 'notes', 'metadata'
    ]

    for field in updateable:
        if field in data:
            val = data[field]
            if isinstance(val, (list, dict)):
                val = json.dumps(val)
            fields.append(f"{field} = ?")
            values.append(val)

    fields.append("updated_at = CURRENT_TIMESTAMP")

    if fields:
        values.append(client_id)
        with get_db_context() as db:
            db.execute(f"UPDATE api_clients SET {', '.join(fields)} WHERE id = ?", values)
            db.commit()

    return get_api_client_by_id(client_id)


def deactivate_api_client(client_id):
    """Deactivate an API client."""
    return update_api_client(client_id, {'status': 'inactive'})


def get_api_client_credentials(client_id):
    """Get all credentials for an API client."""
    return get_all("SELECT * FROM api_client_credentials WHERE client_id = ? ORDER BY created_at DESC",
                   (client_id,))


def create_api_client_credential(client_id, credential_type, created_by=None, notes=None):
    """Create a new credential for an API client."""
    import uuid

    credential_data = {
        'api_key': generate_api_key(),
        'api_secret': generate_api_secret() if credential_type in ('api_key', 'oauth') else None,
        'jwt_secret': generate_api_secret() if credential_type == 'jwt' else None,
    }

    credential_data['api_key_hash'] = hash_api_key(credential_data['api_key'])
    if credential_data['api_secret']:
        credential_data['api_secret_hash'] = hashlib.sha256(credential_data['api_secret'].encode()).hexdigest()

    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO api_client_credentials (
                client_id, credential_type, api_key_hash, api_key_prefix,
                secret_hash, jwt_secret, is_primary, created_by, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            client_id,
            credential_type,
            credential_data['api_key_hash'],
            credential_data['api_key'][:12] if credential_type == 'api_key' else None,
            credential_data.get('api_secret_hash'),
            credential_data.get('jwt_secret'),
            1 if credential_type == 'api_key' else 0,
            created_by,
            notes
        ))
        db.commit()
        cred_id = cursor.lastrowid

    return {
        'id': cred_id,
        'credential_type': credential_type,
        'api_key': credential_data['api_key'],
        'api_secret': credential_data.get('api_secret'),
        'jwt_secret': credential_data.get('jwt_secret'),
    }


def revoke_api_client_credential(credential_id):
    """Revoke an API client credential."""
    with get_db_context() as db:
        db.execute("UPDATE api_client_credentials SET is_active = 0 WHERE id = ?", (credential_id,))
        db.commit()


# =============================================================================
# API SCOPE MANAGEMENT
# =============================================================================

def get_api_scopes(filters=None):
    """Get API scopes with optional filtering."""
    conditions = []
    params = []

    if filters:
        if filters.get('module'):
            conditions.append("module = ?")
            params.append(filters['module'])
        if filters.get('is_active') is not None:
            conditions.append("is_active = ?")
            params.append(1 if filters['is_active'] else 0)
        if filters.get('search'):
            conditions.append("(scope_code LIKE ? OR scope_name LIKE ?)")
            params.extend([f"%{filters['search']}%", f"%{filters['search']}%"])

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    return get_all(f"SELECT * FROM api_scopes {where} ORDER BY module, scope_code", params)


def get_scope_by_code(scope_code):
    """Get a scope by its code."""
    return get_one("SELECT * FROM api_scopes WHERE scope_code = ?", (scope_code,))


def get_client_allowed_scopes(client_id):
    """Get the list of allowed scopes for a client."""
    client = get_api_client_by_id(client_id)
    if not client:
        return []

    scopes_str = client.get('allowed_scopes', '[]')
    if isinstance(scopes_str, str):
        try:
            return json.loads(scopes_str)
        except:
            return []

    return scopes_str if isinstance(scopes_str, list) else []


def validate_client_scopes(client_id, required_scopes):
    """Validate that a client has all required scopes."""
    allowed = get_client_allowed_scopes(client_id)
    if not allowed:
        return False

    # '*' means all scopes
    if '*' in allowed:
        return True

    allowed_set = set(allowed)
    required_set = set(required_scopes)
    return required_set.issubset(allowed_set)


# =============================================================================
# RATE LIMIT MANAGEMENT
# =============================================================================

def get_rate_limit_profile(profile_code):
    """Get rate limit profile by code."""
    return get_one("SELECT * FROM api_rate_limit_profiles WHERE profile_code = ?", (profile_code,))


def get_rate_limit_profiles():
    """Get all rate limit profiles."""
    return get_all("SELECT * FROM api_rate_limit_profiles ORDER BY profile_name")


def check_rate_limit(client_id, profile_code):
    """
    Check if a client is within rate limits.
    Returns (allowed, remaining, reset_at, retry_after)
    """
    profile = get_rate_limit_profile(profile_code) if profile_code else get_rate_limit_profile('default')
    if not profile:
        return True, None, None, None

    now = datetime.utcnow()

    with get_db_context() as db:
        # Check second window
        window_start = now.replace(microsecond=0)
        second_count = db.execute("""
            SELECT COUNT(*) FROM api_request_logs
            WHERE client_id = ? AND created_at >= ?
        """, (client_id, window_start.isoformat())).fetchone()[0]

        if second_count >= profile['requests_per_second']:
            reset_at = window_start + timedelta(seconds=1)
            return False, 0, reset_at.isoformat(), 1

        # Check minute window
        minute_start = now.replace(second=0, microsecond=0)
        minute_count = db.execute("""
            SELECT COUNT(*) FROM api_request_logs
            WHERE client_id = ? AND created_at >= ?
        """, (client_id, minute_start.isoformat())).fetchone()[0]

        if minute_count >= profile['requests_per_minute']:
            reset_at = minute_start + timedelta(minutes=1)
            return False, 0, reset_at.isoformat(), 60

        # Check hour window
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        hour_count = db.execute("""
            SELECT COUNT(*) FROM api_request_logs
            WHERE client_id = ? AND created_at >= ?
        """, (client_id, hour_start.isoformat())).fetchone()[0]

        if hour_count >= profile['requests_per_hour']:
            reset_at = hour_start + timedelta(hours=1)
            return False, 0, reset_at.isoformat(), 3600

        # Check day window
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_count = db.execute("""
            SELECT COUNT(*) FROM api_request_logs
            WHERE client_id = ? AND created_at >= ?
        """, (client_id, day_start.isoformat())).fetchone()[0]

        remaining = profile['requests_per_day'] - day_count
        reset_at = day_start + timedelta(days=1)

        if day_count >= profile['requests_per_day']:
            return False, 0, reset_at.isoformat(), int((reset_at - now).total_seconds())

        return True, remaining, reset_at.isoformat(), None


# =============================================================================
# REQUEST/ERROR LOGGING
# =============================================================================

def log_api_request(request_data):
    """Log an API request."""
    import uuid

    request_id = request_data.get('request_id') or str(uuid.uuid4())

    with get_db_context() as db:
        db.execute("""
            INSERT INTO api_request_logs (
                request_id, trace_id, client_id, client_code, api_key_prefix,
                user_id, user_username, method, path, query_string,
                request_headers, request_body_preview, request_body_size,
                response_status_code, response_body_preview, response_body_size,
                response_time_ms, ip_address, user_agent, auth_type, auth_scopes,
                rate_limit_remaining, rate_limit_reset_at, company_id, branch_id,
                module, resource, action, is_cached, cache_hit
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request_id,
            request_data.get('trace_id'),
            request_data.get('client_id'),
            request_data.get('client_code'),
            request_data.get('api_key_prefix'),
            request_data.get('user_id'),
            request_data.get('user_username'),
            request_data.get('method'),
            request_data.get('path'),
            request_data.get('query_string'),
            json.dumps(request_data.get('request_headers', {})),
            request_data.get('request_body_preview'),
            request_data.get('request_body_size'),
            request_data.get('response_status_code'),
            request_data.get('response_body_preview'),
            request_data.get('response_body_size'),
            request_data.get('response_time_ms'),
            request_data.get('ip_address'),
            request_data.get('user_agent'),
            request_data.get('auth_type'),
            json.dumps(request_data.get('auth_scopes', [])),
            request_data.get('rate_limit_remaining'),
            request_data.get('rate_limit_reset_at'),
            request_data.get('company_id'),
            request_data.get('branch_id'),
            request_data.get('module'),
            request_data.get('resource'),
            request_data.get('action'),
            1 if request_data.get('is_cached') else 0,
            1 if request_data.get('cache_hit') else 0
        ))
        db.commit()

    return request_id


def log_api_error(error_data):
    """Log an API error."""
    import uuid

    error_id = error_data.get('error_id') or str(uuid.uuid4())

    with get_db_context() as db:
        db.execute("""
            INSERT INTO api_error_logs (
                error_id, request_id, trace_id, error_code, error_type,
                error_message, error_details, stack_trace, client_id, client_code,
                user_id, method, path, query_string, request_body_preview,
                ip_address, user_agent, company_id, module, resource, action,
                response_status_code, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            error_id,
            error_data.get('request_id'),
            error_data.get('trace_id'),
            error_data.get('error_code'),
            error_data.get('error_type'),
            error_data.get('error_message'),
            json.dumps(error_data.get('error_details', {})) if error_data.get('error_details') else None,
            error_data.get('stack_trace'),
            error_data.get('client_id'),
            error_data.get('client_code'),
            error_data.get('user_id'),
            error_data.get('method'),
            error_data.get('path'),
            error_data.get('query_string'),
            error_data.get('request_body_preview'),
            error_data.get('ip_address'),
            error_data.get('user_agent'),
            error_data.get('company_id'),
            error_data.get('module'),
            error_data.get('resource'),
            error_data.get('action'),
            error_data.get('response_status_code'),
            datetime.utcnow().isoformat()
        ))
        db.commit()

    return error_id


def get_api_request_logs(filters=None, page=1, per_page=50):
    """Get paginated API request logs."""
    conditions = []
    params = []

    if filters:
        if filters.get('client_id'):
            conditions.append("client_id = ?")
            params.append(filters['client_id'])
        if filters.get('user_id'):
            conditions.append("user_id = ?")
            params.append(filters['user_id'])
        if filters.get('method'):
            conditions.append("method = ?")
            params.append(filters['method'])
        if filters.get('path'):
            conditions.append("path LIKE ?")
            params.append(f"%{filters['path']}%")
        if filters.get('status_code'):
            conditions.append("response_status_code = ?")
            params.append(filters['status_code'])
        if filters.get('date_from'):
            conditions.append("created_at >= ?")
            params.append(filters['date_from'])
        if filters.get('date_to'):
            conditions.append("created_at <= ?")
            params.append(filters['date_to'])

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    offset = (page - 1) * per_page
    total = get_count("api_request_logs", where[6:] if where else "", params)
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    sql = f"""
        SELECT * FROM api_request_logs
        {where}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    logs = get_all(sql, params)

    return {
        'logs': logs,
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    }


def get_api_error_logs(filters=None, page=1, per_page=50):
    """Get paginated API error logs."""
    conditions = []
    params = []

    if filters:
        if filters.get('client_id'):
            conditions.append("client_id = ?")
            params.append(filters['client_id'])
        if filters.get('error_code'):
            conditions.append("error_code = ?")
            params.append(filters['error_code'])
        if filters.get('error_type'):
            conditions.append("error_type = ?")
            params.append(filters['error_type'])
        if filters.get('is_resolved') is not None:
            conditions.append("is_resolved = ?")
            params.append(1 if filters['is_resolved'] else 0)
        if filters.get('date_from'):
            conditions.append("created_at >= ?")
            params.append(filters['date_from'])
        if filters.get('date_to'):
            conditions.append("created_at <= ?")
            params.append(filters['date_to'])

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    offset = (page - 1) * per_page
    total = get_count("api_error_logs", where[6:] if where else "", params)
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    sql = f"""
        SELECT * FROM api_error_logs
        {where}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    logs = get_all(sql, params)

    return {
        'logs': logs,
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    }


# =============================================================================
# WEBHOOK MANAGEMENT
# =============================================================================

def get_webhook_events(filters=None):
    """Get webhook events with optional filtering."""
    conditions = []
    params = []

    if filters:
        if filters.get('module'):
            conditions.append("module = ?")
            params.append(filters['module'])
        if filters.get('is_active') is not None:
            conditions.append("is_active = ?")
            params.append(1 if filters['is_active'] else 0)
        if filters.get('search'):
            conditions.append("(event_code LIKE ? OR event_name LIKE ?)")
            params.extend([f"%{filters['search']}%", f"%{filters['search']}%"])

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    return get_all(f"SELECT * FROM webhook_events {where} ORDER BY module, event_code", params)


def get_webhook_event_by_code(event_code):
    """Get a webhook event by its code."""
    return get_one("SELECT * FROM webhook_events WHERE event_code = ?", (event_code,))


def get_webhook_subscriptions(filters=None, page=1, per_page=50):
    """Get webhook subscriptions with pagination."""
    conditions = []
    params = []

    if filters:
        if filters.get('active') is not None:
            conditions.append("active = ?")
            params.append(1 if filters['active'] else 0)
        if filters.get('search'):
            conditions.append("(subscription_code LIKE ? OR endpoint_name LIKE ? OR target_url LIKE ?)")
            params.extend([f"%{filters['search']}%", f"%{filters['search']}%"])
        if filters.get('event_code'):
            conditions.append("subscribed_events LIKE ?")
            params.append(f"%{filters['event_code']}%")

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    offset = (page - 1) * per_page
    total = get_count("webhook_subscriptions", where[6:] if where else "", params)
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    sql = f"""
        SELECT ws.*,
               (SELECT COUNT(*) FROM webhook_deliveries WHERE subscription_id = ws.id) as total_deliveries
        FROM webhook_subscriptions ws
        {where}
        ORDER BY ws.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    subs = get_all(sql, params)

    return {
        'subscriptions': subs,
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    }


def get_webhook_subscription_by_id(sub_id):
    """Get a webhook subscription by ID."""
    return get_one("SELECT * FROM webhook_subscriptions WHERE id = ?", (sub_id,))


def get_webhook_subscription_by_code(sub_code):
    """Get a webhook subscription by code."""
    return get_one("SELECT * FROM webhook_subscriptions WHERE subscription_code = ?", (sub_code,))


def create_webhook_subscription(data, created_by=None):
    """Create a new webhook subscription."""
    import uuid
    sub_code = data.get('subscription_code') or f"SUB-{uuid.uuid4().hex[:8].upper()}"

    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO webhook_subscriptions (
                subscription_code, endpoint_name, target_url, active,
                subscribed_events, auth_method, auth_secret, auth_header_name,
                signing_algorithm, include_filters, exclude_filters,
                retry_policy, timeout_seconds, max_retries, environment_tag,
                integration_profile_id, owner_name, owner_email,
                created_by, notes, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sub_code,
            data.get('endpoint_name'),
            data.get('target_url'),
            1 if data.get('active', True) else 0,
            json.dumps(data.get('subscribed_events', [])) if isinstance(data.get('subscribed_events'), list) else data.get('subscribed_events'),
            data.get('auth_method', 'none'),
            data.get('auth_secret'),
            data.get('auth_header_name', 'X-Webhook-Signature'),
            data.get('signing_algorithm', 'sha256'),
            json.dumps(data.get('include_filters', [])) if isinstance(data.get('include_filters'), list) else data.get('include_filters'),
            json.dumps(data.get('exclude_filters', [])) if isinstance(data.get('exclude_filters'), list) else data.get('exclude_filters'),
            json.dumps(data.get('retry_policy', {'max_retries': 3, 'backoff': 'exponential'})),
            data.get('timeout_seconds', 30),
            data.get('max_retries', 3),
            data.get('environment_tag'),
            data.get('integration_profile_id'),
            data.get('owner_name'),
            data.get('owner_email'),
            created_by,
            data.get('notes'),
            json.dumps(data.get('metadata', {})) if isinstance(data.get('metadata'), dict) else data.get('metadata')
        ))
        db.commit()
        return cursor.lastrowid


def update_webhook_subscription(sub_id, data):
    """Update a webhook subscription."""
    fields = []
    values = []

    updateable = [
        'endpoint_name', 'target_url', 'active', 'subscribed_events',
        'auth_method', 'auth_secret', 'auth_header_name', 'signing_algorithm',
        'include_filters', 'exclude_filters', 'retry_policy', 'timeout_seconds',
        'max_retries', 'environment_tag', 'owner_name', 'owner_email', 'notes', 'metadata'
    ]

    for field in updateable:
        if field in data:
            val = data[field]
            if isinstance(val, (list, dict)):
                val = json.dumps(val)
            fields.append(f"{field} = ?")
            values.append(val)

    fields.append("updated_at = CURRENT_TIMESTAMP")

    if fields:
        values.append(sub_id)
        with get_db_context() as db:
            db.execute(f"UPDATE webhook_subscriptions SET {', '.join(fields)} WHERE id = ?", values)
            db.commit()

    return get_webhook_subscription_by_id(sub_id)


def delete_webhook_subscription(sub_id):
    """Delete a webhook subscription."""
    with get_db_context() as db:
        db.execute("DELETE FROM webhook_subscriptions WHERE id = ?", (sub_id,))
        db.commit()


def get_webhook_deliveries(filters=None, page=1, per_page=50):
    """Get webhook deliveries with pagination."""
    conditions = []
    params = []

    if filters:
        if filters.get('subscription_id'):
            conditions.append("subscription_id = ?")
            params.append(filters['subscription_id'])
        if filters.get('event_code'):
            conditions.append("event_code = ?")
            params.append(filters['event_code'])
        if filters.get('status'):
            conditions.append("delivery_status = ?")
            params.append(filters['status'])
        if filters.get('date_from'):
            conditions.append("created_at >= ?")
            params.append(filters['date_from'])
        if filters.get('date_to'):
            conditions.append("created_at <= ?")
            params.append(filters['date_to'])

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    offset = (page - 1) * per_page
    total = get_count("webhook_deliveries", where[6:] if where else "", params)
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    sql = f"""
        SELECT wd.*, ws.endpoint_name, ws.target_url
        FROM webhook_deliveries wd
        LEFT JOIN webhook_subscriptions ws ON wd.subscription_id = ws.id
        {where}
        ORDER BY wd.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    deliveries = get_all(sql, params)

    return {
        'deliveries': deliveries,
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    }


def deliver_webhook_event(event_code, payload, delivery_id=None, subscription_id=None, attempt=1):
    """
    Deliver a webhook event to all subscribed endpoints.
    Returns the number of successful deliveries.
    """
    import uuid
    import urllib.request
    import urllib.error

    event = get_webhook_event_by_code(event_code)
    if not event or not event.get('is_active'):
        return 0

    # Get subscriptions for this event
    if subscription_id:
        subs = [get_webhook_subscription_by_id(subscription_id)]
    else:
        subs = get_all("""
            SELECT * FROM webhook_subscriptions
            WHERE active = 1 AND subscribed_events LIKE ?
        """, (f"%{event_code}%",))

    if not subs:
        return 0

    successful = 0
    delivery_id = delivery_id or str(uuid.uuid4())

    for sub in subs:
        # Parse subscribed events
        try:
            sub_events = json.loads(sub['subscribed_events']) if isinstance(sub['subscribed_events'], str) else sub.get('subscribed_events', [])
        except:
            sub_events = []

        if event_code not in sub_events and '*' not in sub_events:
            continue

        # Build request
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'MMDx-Webhook/1.0',
            'X-Webhook-Event': event_code,
            'X-Delivery-ID': delivery_id,
            'X-Timestamp': datetime.utcnow().isoformat(),
        }

        # Add signature if configured
        if sub.get('auth_method') == 'secret' and sub.get('auth_secret'):
            import hmac
            timestamp = headers['X-Timestamp']
            payload_str = json.dumps(payload) if isinstance(payload, dict) else payload
            signature_payload = f"{timestamp}.{payload_str}"
            signature = hmac.new(
                sub['auth_secret'].encode(),
                signature_payload.encode(),
                hashlib.sha256
            ).hexdigest()
            headers[sub.get('auth_header_name', 'X-Webhook-Signature')] = signature

        body = json.dumps({
            'event': event_code,
            'timestamp': datetime.utcnow().isoformat(),
            'data': payload,
            'delivery_id': delivery_id,
        })

        try:
            req = urllib.request.Request(
                sub['target_url'],
                data=body.encode(),
                headers=headers,
                method='POST'
            )

            start = time.time()
            with urllib.request.urlopen(req, timeout=sub.get('timeout_seconds', 30)) as resp:
                response_body = resp.read().decode('utf-8', errors='replace')[:1000]
                response_code = resp.getcode()
            elapsed_ms = int((time.time() - start) * 1000)

            # Success
            _record_webhook_delivery(
                delivery_id=delivery_id,
                event_id=event['id'],
                event_code=event_code,
                subscription_id=sub['id'],
                status='success',
                http_status_code=response_code,
                response_body_preview=response_body[:500],
                response_time_ms=elapsed_ms,
                attempt_number=attempt,
                request_body=body,
                request_headers=headers
            )

            # Update subscription stats
            _update_subscription_stats(sub['id'], 'success')
            successful += 1

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8', errors='replace')[:500]
            _record_webhook_delivery(
                delivery_id=delivery_id,
                event_id=event['id'],
                event_code=event_code,
                subscription_id=sub['id'],
                status='failed',
                http_status_code=e.code,
                response_body_preview=error_body,
                response_time_ms=int((time.time() - start) * 1000) if 'start' in dir() else 0,
                attempt_number=attempt,
                error_code=f"HTTP_{e.code}",
                error_message=str(e),
                request_body=body,
                request_headers=headers
            )
            _update_subscription_stats(sub['id'], 'failed', str(e))

        except Exception as ex:
            _record_webhook_delivery(
                delivery_id=delivery_id,
                event_id=event['id'],
                event_code=event_code,
                subscription_id=sub['id'],
                status='failed',
                attempt_number=attempt,
                error_code='DELIVERY_ERROR',
                error_message=str(ex),
                request_body=body if 'body' in dir() else None,
                request_headers=headers if 'headers' in dir() else None
            )
            _update_subscription_stats(sub['id'], 'failed', str(ex))

    return successful


def _record_webhook_delivery(delivery_id, event_id, event_code, subscription_id, status,
                              http_status_code=None, response_body_preview=None,
                              response_time_ms=None, attempt_number=1, max_attempts=3,
                              next_retry_at=None, error_code=None, error_message=None,
                              error_details=None, request_body=None, request_headers=None):
    """Record a webhook delivery attempt."""
    import uuid

    if not delivery_id:
        delivery_id = str(uuid.uuid4())

    delivery_hash = hashlib.sha256(request_body.encode()).hexdigest() if request_body else None

    with get_db_context() as db:
        db.execute("""
            INSERT INTO webhook_deliveries (
                delivery_id, event_id, event_code, subscription_id, delivery_status,
                http_status_code, response_body_preview, response_time_ms,
                attempt_number, max_attempts, next_retry_at, error_code,
                error_message, error_details, request_body, request_body_hash,
                request_headers, request_timestamp, delivered_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            delivery_id, event_id, event_code, subscription_id, status,
            http_status_code, response_body_preview, response_time_ms,
            attempt_number, max_attempts, next_retry_at, error_code,
            error_message, json.dumps(error_details) if error_details else None,
            request_body[:2000] if request_body else None,
            delivery_hash,
            json.dumps(request_headers) if request_headers else None,
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat() if status == 'success' else None,
            datetime.utcnow().isoformat()
        ))
        db.commit()


def _update_subscription_stats(subscription_id, status, error_message=None):
    """Update webhook subscription statistics."""
    with get_db_context() as db:
        sub = db.execute("SELECT * FROM webhook_subscriptions WHERE id = ?", (subscription_id,)).fetchone()
        if not sub:
            return

        total = sub['total_deliveries'] + 1
        success = sub['successful_deliveries'] + (1 if status == 'success' else 0)
        failed = sub['failed_deliveries'] + (1 if status == 'failed' else 0)
        rate = (success / total * 100) if total > 0 else 0

        db.execute("""
            UPDATE webhook_subscriptions SET
                total_deliveries = ?,
                successful_deliveries = ?,
                failed_deliveries = ?,
                success_rate = ?,
                last_delivery_at = ?,
                last_delivery_status = ?,
                last_response_code = ?,
                last_error_message = ?
            WHERE id = ?
        """, (
            total, success, failed, rate,
            datetime.utcnow().isoformat(),
            status,
            None,  # Could capture from delivery
            error_message if status == 'failed' else None,
            subscription_id
        ))
        db.commit()


def retry_webhook_delivery(delivery_id):
    """Retry a failed webhook delivery."""
    delivery = get_one("SELECT * FROM webhook_deliveries WHERE delivery_id = ?", (delivery_id,))
    if not delivery:
        return False

    if delivery['attempt_number'] >= delivery['max_attempts']:
        return False

    # Re-attempt delivery
    success = deliver_webhook_event(
        event_code=delivery['event_code'],
        payload=json.loads(delivery['request_body']) if delivery['request_body'] else {},
        delivery_id=delivery_id,
        subscription_id=delivery['subscription_id'],
        attempt=delivery['attempt_number'] + 1
    )

    return success > 0


# =============================================================================
# INTEGRATION PROFILE MANAGEMENT
# =============================================================================

def get_integration_profiles(filters=None, page=1, per_page=50):
    """Get integration profiles with pagination."""
    conditions = []
    params = []

    if filters:
        if filters.get('integration_type'):
            conditions.append("integration_type = ?")
            params.append(filters['integration_type'])
        if filters.get('module'):
            conditions.append("module = ?")
            params.append(filters['module'])
        if filters.get('direction'):
            conditions.append("direction = ?")
            params.append(filters['direction'])
        if filters.get('is_active') is not None:
            conditions.append("is_active = ?")
            params.append(1 if filters['is_active'] else 0)
        if filters.get('search'):
            conditions.append("(integration_code LIKE ? OR integration_name LIKE ?)")
            params.extend([f"%{filters['search']}%", f"%{filters['search']}%"])

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    offset = (page - 1) * per_page
    total = get_count("integration_profiles", where[6:] if where else "", params)
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    sql = f"""
        SELECT ip.*,
               (SELECT COUNT(*) FROM integration_runs WHERE integration_id = ip.id) as total_runs
        FROM integration_profiles ip
        {where}
        ORDER BY ip.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    profiles = get_all(sql, params)

    return {
        'profiles': profiles,
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    }


def get_integration_profile_by_id(profile_id):
    """Get an integration profile by ID."""
    return get_one("SELECT * FROM integration_profiles WHERE id = ?", (profile_id,))


def get_integration_profile_by_code(profile_code):
    """Get an integration profile by code."""
    return get_one("SELECT * FROM integration_profiles WHERE integration_code = ?", (profile_code,))


def create_integration_profile(data, created_by=None):
    """Create a new integration profile."""
    import uuid
    code = data.get('integration_code') or f"INT-{uuid.uuid4().hex[:8].upper()}"

    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO integration_profiles (
                integration_code, integration_name, integration_type, module,
                direction, description, connection_config, credential_id,
                webhook_subscription_id, module_scope, payload_mapping_rules,
                transformation_rules, sync_schedule, sync_trigger, retry_policy,
                timeout_seconds, is_active, requires_approval, approval_status,
                owner_id, owner_name, owner_email, department,
                created_by, notes, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            code,
            data.get('integration_name'),
            data.get('integration_type'),
            data.get('module'),
            data.get('direction'),
            data.get('description'),
            json.dumps(data.get('connection_config', {})) if isinstance(data.get('connection_config'), dict) else data.get('connection_config'),
            data.get('credential_id'),
            data.get('webhook_subscription_id'),
            json.dumps(data.get('module_scope', [])) if isinstance(data.get('module_scope'), list) else data.get('module_scope'),
            json.dumps(data.get('payload_mapping_rules', {})) if isinstance(data.get('payload_mapping_rules'), dict) else data.get('payload_mapping_rules'),
            json.dumps(data.get('transformation_rules', {})) if isinstance(data.get('transformation_rules'), dict) else data.get('transformation_rules'),
            data.get('sync_schedule'),
            data.get('sync_trigger', 'manual'),
            json.dumps(data.get('retry_policy', {'max_retries': 3, 'backoff': 'exponential'})),
            data.get('timeout_seconds', 30),
            1 if data.get('is_active', True) else 0,
            1 if data.get('requires_approval') else 0,
            'approved' if not data.get('requires_approval') else 'pending',
            data.get('owner_id'),
            data.get('owner_name'),
            data.get('owner_email'),
            data.get('department'),
            created_by,
            data.get('notes'),
            json.dumps(data.get('metadata', {})) if isinstance(data.get('metadata'), dict) else data.get('metadata')
        ))
        db.commit()
        return cursor.lastrowid


def update_integration_profile(profile_id, data):
    """Update an integration profile."""
    fields = []
    values = []

    updateable = [
        'integration_name', 'integration_type', 'module', 'direction',
        'description', 'connection_config', 'credential_id', 'webhook_subscription_id',
        'module_scope', 'payload_mapping_rules', 'transformation_rules',
        'sync_schedule', 'sync_trigger', 'retry_policy', 'timeout_seconds',
        'is_active', 'owner_id', 'owner_name', 'owner_email', 'department', 'notes', 'metadata'
    ]

    for field in updateable:
        if field in data:
            val = data[field]
            if isinstance(val, (dict)):
                val = json.dumps(val)
            fields.append(f"{field} = ?")
            values.append(val)

    fields.append("updated_at = CURRENT_TIMESTAMP")

    if fields:
        values.append(profile_id)
        with get_db_context() as db:
            db.execute(f"UPDATE integration_profiles SET {', '.join(fields)} WHERE id = ?", values)
            db.commit()

    return get_integration_profile_by_id(profile_id)


def delete_integration_profile(profile_id):
    """Delete an integration profile."""
    with get_db_context() as db:
        db.execute("DELETE FROM integration_profiles WHERE id = ?", (profile_id,))
        db.commit()


def get_integration_runs(filters=None, page=1, per_page=50):
    """Get integration run history with pagination."""
    conditions = []
    params = []

    if filters:
        if filters.get('integration_id'):
            conditions.append("integration_id = ?")
            params.append(filters['integration_id'])
        if filters.get('status'):
            conditions.append("status = ?")
            params.append(filters['status'])
        if filters.get('date_from'):
            conditions.append("created_at >= ?")
            params.append(filters['date_from'])
        if filters.get('date_to'):
            conditions.append("created_at <= ?")
            params.append(filters['date_to'])

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    offset = (page - 1) * per_page
    total = get_count("integration_runs", where[6:] if where else "", params)
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    sql = f"""
        SELECT ir.*, ip.integration_name, ip.integration_type
        FROM integration_runs ir
        LEFT JOIN integration_profiles ip ON ir.integration_id = ip.id
        {where}
        ORDER BY ir.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    runs = get_all(sql, params)

    return {
        'runs': runs,
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    }


def get_integration_exceptions(filters=None, page=1, per_page=50):
    """Get integration exceptions with pagination."""
    conditions = []
    params = []

    if filters:
        if filters.get('integration_id'):
            conditions.append("integration_id = ?")
            params.append(filters['integration_id'])
        if filters.get('is_resolved') is not None:
            conditions.append("is_resolved = ?")
            params.append(1 if filters['is_resolved'] else 0)
        if filters.get('exception_type'):
            conditions.append("exception_type = ?")
            params.append(filters['exception_type'])

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    offset = (page - 1) * per_page
    total = get_count("integration_exceptions", where[6:] if where else "", params)
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    sql = f"""
        SELECT ie.*, ip.integration_name, ip.integration_code
        FROM integration_exceptions ie
        LEFT JOIN integration_profiles ip ON ie.integration_id = ip.id
        {where}
        ORDER BY ie.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    exceptions = get_all(sql, params)

    return {
        'exceptions': exceptions,
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    }


# =============================================================================
# API ROUTE REGISTRY
# =============================================================================

def get_api_routes(filters=None, page=1, per_page=100):
    """Get API routes with pagination."""
    conditions = []
    params = []

    if filters:
        if filters.get('version_id'):
            conditions.append("version_id = ?")
            params.append(filters['version_id'])
        if filters.get('module'):
            conditions.append("module = ?")
            params.append(filters['module'])
        if filters.get('method'):
            conditions.append("method = ?")
            params.append(filters['method'])
        if filters.get('is_active') is not None:
            conditions.append("is_active = ?")
            params.append(1 if filters['is_active'] else 0)
        if filters.get('is_deprecated') is not None:
            conditions.append("is_deprecated = ?")
            params.append(1 if filters['is_deprecated'] else 0)
        if filters.get('search'):
            conditions.append("(route_code LIKE ? OR path LIKE ? OR description LIKE ?)")
            params.extend([f"%{filters['search']}%", f"%{filters['search']}%", f"%{filters['search']}%"])

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    offset = (page - 1) * per_page
    total = get_count("api_route_registry", where[6:] if where else "", params)
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    sql = f"""
        SELECT arr.*, av.version_code, av.version_name
        FROM api_route_registry arr
        LEFT JOIN api_versions av ON arr.version_id = av.id
        {where}
        ORDER BY arr.module, arr.method, arr.path
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    routes = get_all(sql, params)

    return {
        'routes': routes,
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    }


def get_api_versions():
    """Get all API versions."""
    return get_all("SELECT * FROM api_versions ORDER BY version_code DESC")


def get_active_api_version():
    """Get the default active API version."""
    return get_one("SELECT * FROM api_versions WHERE is_default = 1 AND is_active = 1")


# =============================================================================
# API SETTINGS
# =============================================================================

def get_api_setting(key, default=None):
    """Get an API setting value."""
    result = get_one("SELECT setting_value FROM api_settings WHERE setting_key = ? AND is_active = 1", (key,))
    return result['setting_value'] if result else default


def set_api_setting(key, value, updated_by=None, notes=None):
    """Set an API setting value."""
    existing = get_one("SELECT id FROM api_settings WHERE setting_key = ?", (key,))

    with get_db_context() as db:
        if existing:
            db.execute("""
                UPDATE api_settings SET setting_value = ?, updated_at = CURRENT_TIMESTAMP,
                updated_by = ?, notes = ? WHERE setting_key = ?
            """, (str(value), updated_by, notes, key))
        else:
            db.execute("""
                INSERT INTO api_settings (setting_key, setting_value, updated_by, notes)
                VALUES (?, ?, ?, ?)
            """, (key, str(value), updated_by, notes))
        db.commit()


def get_api_settings_by_category(category):
    """Get all API settings in a category."""
    return get_all("SELECT * FROM api_settings WHERE category = ? AND is_active = 1 ORDER BY setting_key",
                   (category,))


# =============================================================================
# API DOCS
# =============================================================================

def get_api_docs(filters=None, page=1, per_page=50):
    """Get API documentation entries with pagination."""
    conditions = []
    params = []

    if filters:
        if filters.get('module'):
            conditions.append("module = ?")
            params.append(filters['module'])
        if filters.get('version_id'):
            conditions.append("version_id = ?")
            params.append(filters['version_id'])
        if filters.get('doc_type'):
            conditions.append("doc_type = ?")
            params.append(filters['doc_type'])
        if filters.get('is_published') is not None:
            conditions.append("is_published = ?")
            params.append(1 if filters['is_published'] else 0)
        if filters.get('search'):
            conditions.append("(title LIKE ? OR doc_code LIKE ?)")
            params.extend([f"%{filters['search']}%", f"%{filters['search']}%"])

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    offset = (page - 1) * per_page
    total = get_count("api_docs_registry", where[6:] if where else "", params)
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    sql = f"""
        SELECT adr.*, av.version_code
        FROM api_docs_registry adr
        LEFT JOIN api_versions av ON adr.version_id = av.id
        {where}
        ORDER BY adr.module, adr.doc_type, adr.title
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    docs = get_all(sql, params)

    return {
        'docs': docs,
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    }


# =============================================================================
# DASHBOARD STATISTICS
# =============================================================================

def get_api_gateway_stats():
    """Get API Gateway dashboard statistics."""
    stats = {}

    # Client stats
    stats['total_clients'] = get_count("api_clients", "")
    stats['active_clients'] = get_count("api_clients", "status='active'")
    stats['pending_clients'] = get_count("api_clients", "status='pending'")

    # Request stats (last 24 hours)
    from datetime import datetime, timedelta
    yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
    stats['requests_today'] = get_count("api_request_logs", f"created_at >= '{yesterday}'")
    stats['errors_today'] = get_count("api_error_logs", f"is_resolved = 0 AND created_at >= '{yesterday}'")

    # Webhook stats
    stats['total_subscriptions'] = get_count("webhook_subscriptions", "")
    stats['active_subscriptions'] = get_count("webhook_subscriptions", "active=1")
    stats['deliveries_today'] = get_count("webhook_deliveries", f"created_at >= '{yesterday}'")
    stats['failed_deliveries_today'] = get_count("webhook_deliveries", f"delivery_status='failed' AND created_at >= '{yesterday}'")

    # Integration stats
    stats['total_integrations'] = get_count("integration_profiles", "")
    stats['active_integrations'] = get_count("integration_profiles", "is_active=1")

    # Route stats
    stats['total_routes'] = get_count("api_route_registry", "")

    # Scope stats
    stats['total_scopes'] = get_count("api_scopes", "is_active=1")

    return stats


def get_api_usage_metrics(days=7):
    """Get API usage metrics for the last N days."""
    from datetime import datetime, timedelta

    metrics = []
    for i in range(days):
        day = (datetime.utcnow() - timedelta(days=i)).date().isoformat()
        day_start = f"{day} 00:00:00"
        day_end = f"{day} 23:59:59"

        with get_db_context() as db:
            total = db.execute("""
                SELECT COUNT(*) FROM api_request_logs
                WHERE created_at >= ? AND created_at <= ?
            """, (day_start, day_end)).fetchone()[0]

            errors = db.execute("""
                SELECT COUNT(*) FROM api_error_logs
                WHERE created_at >= ? AND created_at <= ?
            """, (day_start, day_end)).fetchone()[0]

            avg_response = db.execute("""
                SELECT AVG(response_time_ms) FROM api_request_logs
                WHERE created_at >= ? AND created_at <= ? AND response_time_ms IS NOT NULL
            """, (day_start, day_end)).fetchone()[0] or 0

        metrics.append({
            'date': day,
            'requests': total,
            'errors': errors,
            'error_rate': (errors / total * 100) if total > 0 else 0,
            'avg_response_ms': round(avg_response, 2)
        })

    return list(reversed(metrics))


# =============================================================================
# APPROVAL MANAGEMENT
# =============================================================================

def get_pending_approvals(entity_type=None):
    """Get pending approval records."""
    sql = "SELECT * FROM approval_records WHERE current_status = 'pending'"
    params = []

    if entity_type:
        sql += " AND entity_type = ?"
        params.append(entity_type)

    sql += " ORDER BY submitted_at DESC"

    return get_all(sql, params)


def create_approval_record(data):
    """Create a new approval record."""
    import uuid
    code = data.get('approval_code') or f"APR-{uuid.uuid4().hex[:8].upper()}"

    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO approval_records (
                approval_code, entity_type, entity_id, entity_code,
                approval_type, current_status, priority, requester_id,
                requester_name, requester_email, submitted_at,
                previous_value, new_value, change_summary, workflow_config, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            code,
            data.get('entity_type'),
            data.get('entity_id'),
            data.get('entity_code'),
            data.get('approval_type'),
            'pending',
            data.get('priority', 'normal'),
            data.get('requester_id'),
            data.get('requester_name'),
            data.get('requester_email'),
            datetime.utcnow().isoformat(),
            data.get('previous_value'),
            data.get('new_value'),
            data.get('change_summary'),
            json.dumps(data.get('workflow_config', {})),
            data.get('notes')
        ))
        db.commit()
        return cursor.lastrowid


def approve_record(approval_id, approver_id, approver_name, notes=None):
    """Approve a record."""
    with get_db_context() as db:
        db.execute("""
            UPDATE approval_records SET
                current_status = 'approved',
                approver_id = ?,
                approver_name = ?,
                decided_at = ?,
                decision_notes = ?
            WHERE id = ?
        """, (approver_id, approver_name, datetime.utcnow().isoformat(), notes, approval_id))
        db.commit()


def reject_record(approval_id, approver_id, approver_name, reason):
    """Reject a record."""
    with get_db_context() as db:
        db.execute("""
            UPDATE approval_records SET
                current_status = 'rejected',
                approver_id = ?,
                approver_name = ?,
                decided_at = ?,
                rejection_reason = ?
            WHERE id = ?
        """, (approver_id, approver_name, datetime.utcnow().isoformat(), reason, approval_id))
        db.commit()


# =============================================================================
# INITIALIZATION
# =============================================================================

# Initialize tables when module is imported
init_api_gateway_tables()
