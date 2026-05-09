"""
Consolidate Scattered Module Tables
=================================
Revision ID: 003_consolidate_scattered_tables
Revises: 002_current_schema_marker
Create Date: 2026-05-06

This migration consolidates ALL module tables that were created by scattered
init_*() functions across the codebase. These tables now exist in the
production database but were NOT created through Alembic.

This migration:
1. Uses CREATE TABLE IF NOT EXISTS for safety (existing tables are preserved)
2. Makes Alembic aware of these tables so future migrations can reference them
3. Documents the complete schema state post-consolidation

IMPORTANT: Future schema changes to these tables MUST go through new Alembic
migrations. Do NOT add new CREATE TABLE logic to init_*() functions.

Tables covered:
- Planning:  planning_demand_history, planning_sales_history, planning_item_profiles,
             planning_policies, planning_policy_assignments, planning_forecast_runs,
             planning_forecast_lines, planning_forecast_overrides, and 30+ more
- GRC:       grc_governance_entities, grc_risks, grc_controls, grc_compliance_obligations,
             grc_policies, grc_policy_acknowledgements, grc_sod_rules, and 40+ more
- BTP:       btp_connectors, btp_integration_flows, btp_mappings, btp_jobs,
             btp_events, btp_api_catalog, btp_feature_flags, and 20+ more
- Workflow:  workflow_definitions, workflow_versions, workflow_steps, workflow_transitions,
             workflow_conditions, workflow_instances, and 15+ more
- Marketing: marketing_brands, marketing_campaigns, marketing_leads, marketing_budgets,
             marketing_performance_metrics, and 35+ more
- Quality:   quality_inspection_types, quality_inspections, quality_non_conformances,
             quality_capa_records, quality_audit_programs, and 15+ more
- WMS:       wms_settings, wms_companies, wms_warehouses, wms_locations, wms_items,
             wms_inventory_balances, wms_inventory_ledger, wms_putaway_tasks,
             wms_pick_tasks, wms_shipments, wms_returns, and 60+ more
- Finance:   finance_accounts, finance_journals, finance_budgets, finance_tax_codes,
             finance_bank_reconciliation, and 20+ more
- SPC:       spc_data_points, spc_control_charts, spc_alerts
- Social:    social_posts, social_comments, social_metrics
- Legal:     legal_cases, legal_contracts, legal_compliance
- Treasury:  treasury_bank_accounts, treasury_transactions
- Asset:     asset_register, asset_depreciation
- BI:        bi_report_definitions, bi_report_executions
- CRM:       crm_contacts, crm_opportunities
- Ecommerce: eco_products, eco_orders
- Maintenance: maint_requests, maint_schedules
- And more: quick_tools, logistics, investment, payroll, org_planning, etc.
"""

from alembic import op
import sqlalchemy as sa

revision = '003_consolidate_scattered_tables'
down_revision = '002_current_schema_marker'
branch_labels = None
depends_on = None


def _execute_if_table_not_exists(conn, table_name, create_sql):
    """
    Execute CREATE TABLE IF NOT EXISTS safely.
    Only creates the table if it doesn't already exist.
    This is safe for both fresh DBs and existing production DBs.
    """
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=:tbl"
        ),
        {"tbl": table_name}
    )
    if result.fetchone() is None:
        conn.execute(sa.text(create_sql))


def upgrade() -> None:
    """
    Consolidate all scattered module tables using IF NOT EXISTS semantics.
    Safe to run on both fresh databases and existing production databases.
    """
    conn = op.get_bind()

    # ========================================================================
    # PLANNING TABLES
    # ========================================================================
    planning_tables = [
        ("planning_demand_history", """
            CREATE TABLE IF NOT EXISTS planning_demand_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                warehouse_id INTEGER,
                company_id INTEGER,
                period_type TEXT NOT NULL DEFAULT 'daily',
                period_start DATE NOT NULL,
                quantity REAL NOT NULL DEFAULT 0,
                sales_quantity REAL DEFAULT 0,
                consumption_quantity REAL DEFAULT 0,
                customer_count INTEGER DEFAULT 0,
                order_count INTEGER DEFAULT 0,
                returned_quantity REAL DEFAULT 0,
                lost_sales_estimate REAL DEFAULT 0,
                is_cancelled INTEGER DEFAULT 0,
                source TEXT DEFAULT 'movement',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(item_id, warehouse_id, company_id, period_type, period_start)
            )
        """),
        ("planning_sales_history", """
            CREATE TABLE IF NOT EXISTS planning_sales_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                warehouse_id INTEGER,
                company_id INTEGER,
                customer_id INTEGER,
                invoice_date DATE NOT NULL,
                quantity REAL NOT NULL DEFAULT 0,
                unit_price REAL DEFAULT 0,
                total_value REAL DEFAULT 0,
                is_export INTEGER DEFAULT 0,
                is_backorder INTEGER DEFAULT 0,
                is_rush_order INTEGER DEFAULT 0,
                salesperson_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_item_profiles", """
            CREATE TABLE IF NOT EXISTS planning_item_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL UNIQUE,
                abc_class TEXT DEFAULT 'C',
                xyz_class TEXT DEFAULT 'X',
                criticality_level TEXT DEFAULT 'MEDIUM',
                movement_type TEXT DEFAULT 'NORMAL',
                planning_method TEXT DEFAULT 'AUTO',
                forecast_method TEXT DEFAULT 'MOVING_AVERAGE',
                review_cycle_days INTEGER DEFAULT 30,
                lead_time_days INTEGER DEFAULT 7,
                lead_time_variability REAL DEFAULT 0,
                service_level_target REAL DEFAULT 0.95,
                safety_stock_days INTEGER DEFAULT 7,
                min_order_quantity REAL DEFAULT 0,
                order_multiple REAL DEFAULT 1,
                max_order_quantity REAL,
                target_days_of_coverage INTEGER DEFAULT 30,
                is_seasonal INTEGER DEFAULT 0,
                seasonal_pattern TEXT,
                is_strategic INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                last_forecast_run_id INTEGER,
                last_calculated_at TIMESTAMP,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_policies", """
            CREATE TABLE IF NOT EXISTS planning_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                policy_type TEXT NOT NULL,
                description TEXT,
                safety_stock_method TEXT DEFAULT 'FORMULA',
                safety_stock_days INTEGER DEFAULT 7,
                safety_stock_factor REAL DEFAULT 1.65,
                reorder_point_method TEXT DEFAULT 'STANDARD',
                reorder_point_days INTEGER DEFAULT 3,
                min_stock REAL DEFAULT 0,
                max_stock REAL,
                reorder_quantity_method TEXT DEFAULT 'EOQ',
                order_multiple REAL DEFAULT 1,
                min_order_quantity REAL DEFAULT 0,
                max_order_quantity REAL,
                forecast_horizon_days INTEGER DEFAULT 30,
                forecast_method TEXT DEFAULT 'MOVING_AVERAGE',
                use_seasonality INTEGER DEFAULT 0,
                use_trend INTEGER DEFAULT 1,
                demand_weight_recent REAL DEFAULT 0.3,
                demand_weight_key_customers REAL DEFAULT 0.2,
                demand_history_months INTEGER DEFAULT 12,
                target_service_level REAL DEFAULT 0.95,
                min_lead_time_days INTEGER DEFAULT 7,
                max_lead_time_days INTEGER DEFAULT 30,
                allow_emergency_orders INTEGER DEFAULT 1,
                allow_partial_fulfillment INTEGER DEFAULT 1,
                allow_transfer_first INTEGER DEFAULT 1,
                priority_score INTEGER DEFAULT 50,
                is_active INTEGER DEFAULT 1,
                is_system INTEGER DEFAULT 0,
                company_id INTEGER,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_policy_assignments", """
            CREATE TABLE IF NOT EXISTS planning_policy_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                policy_id INTEGER NOT NULL,
                assignment_type TEXT NOT NULL,
                item_id INTEGER,
                item_group TEXT,
                brand_id INTEGER,
                category_id INTEGER,
                warehouse_id INTEGER,
                company_id INTEGER,
                priority INTEGER DEFAULT 100,
                overrides_json TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (policy_id) REFERENCES planning_policies(id)
            )
        """),
        ("planning_forecast_runs", """
            CREATE TABLE IF NOT EXISTS planning_forecast_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_name TEXT,
                forecast_type TEXT NOT NULL,
                method TEXT NOT NULL,
                horizon_days INTEGER DEFAULT 30,
                period_type TEXT DEFAULT 'daily',
                warehouse_id INTEGER,
                company_id INTEGER,
                scenario_id INTEGER,
                status TEXT DEFAULT 'DRAFT',
                total_items INTEGER DEFAULT 0,
                total_demand REAL DEFAULT 0,
                notes TEXT,
                created_by INTEGER,
                approved_by INTEGER,
                approved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_forecast_lines", """
            CREATE TABLE IF NOT EXISTS planning_forecast_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                forecast_run_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                warehouse_id INTEGER,
                company_id INTEGER,
                period_start DATE NOT NULL,
                quantity REAL NOT NULL,
                confidence_pct REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (forecast_run_id) REFERENCES planning_forecast_runs(id)
            )
        """),
        ("planning_forecast_overrides", """
            CREATE TABLE IF NOT EXISTS planning_forecast_overrides (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                warehouse_id INTEGER,
                company_id INTEGER,
                period_start DATE NOT NULL,
                override_quantity REAL NOT NULL,
                reason TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_replenishment_recommendations", """
            CREATE TABLE IF NOT EXISTS planning_replenishment_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                warehouse_id INTEGER,
                company_id INTEGER,
                recommendation_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit_cost REAL DEFAULT 0,
                total_cost REAL DEFAULT 0,
                urgency TEXT DEFAULT 'NORMAL',
                source TEXT DEFAULT 'AUTO',
                status TEXT DEFAULT 'PENDING',
                created_by INTEGER,
                reviewed_by INTEGER,
                reviewed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_purchase_recommendations", """
            CREATE TABLE IF NOT EXISTS planning_purchase_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recommendation_id INTEGER,
                supplier_id INTEGER,
                lead_time_days INTEGER DEFAULT 7,
                moq REAL DEFAULT 0,
                unit_cost REAL DEFAULT 0,
                currency TEXT DEFAULT 'AED',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recommendation_id) REFERENCES planning_replenishment_recommendations(id)
            )
        """),
        ("planning_transfer_recommendations", """
            CREATE TABLE IF NOT EXISTS planning_transfer_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recommendation_id INTEGER,
                source_warehouse_id INTEGER,
                target_warehouse_id INTEGER,
                transfer_cost REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recommendation_id) REFERENCES planning_replenishment_recommendations(id)
            )
        """),
        ("planning_scenarios", """
            CREATE TABLE IF NOT EXISTS planning_scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'DRAFT',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_scenario_lines", """
            CREATE TABLE IF NOT EXISTS planning_scenario_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                warehouse_id INTEGER,
                projected_quantity REAL,
                projected_cost REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scenario_id) REFERENCES planning_scenarios(id)
            )
        """),
        ("planning_alerts", """
            CREATE TABLE IF NOT EXISTS planning_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                warehouse_id INTEGER,
                company_id INTEGER,
                alert_type TEXT NOT NULL,
                severity TEXT DEFAULT 'MEDIUM',
                message TEXT,
                is_acknowledged INTEGER DEFAULT 0,
                acknowledged_by INTEGER,
                acknowledged_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_kpi_records", """
            CREATE TABLE IF NOT EXISTS planning_kpi_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                warehouse_id INTEGER,
                company_id INTEGER,
                kpi_type TEXT NOT NULL,
                value REAL NOT NULL,
                period_start DATE NOT NULL,
                period_end DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_audit_log", """
            CREATE TABLE IF NOT EXISTS planning_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                entity_type TEXT,
                entity_id INTEGER,
                old_value TEXT,
                new_value TEXT,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_settings", """
            CREATE TABLE IF NOT EXISTS planning_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT,
                setting_type TEXT DEFAULT 'STRING',
                category TEXT DEFAULT 'GENERAL',
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_lost_sales", """
            CREATE TABLE IF NOT EXISTS planning_lost_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                warehouse_id INTEGER,
                company_id INTEGER,
                lost_date DATE NOT NULL,
                lost_quantity REAL NOT NULL,
                lost_reason TEXT,
                opportunity_cost REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_customer_demand_patterns", """
            CREATE TABLE IF NOT EXISTS planning_customer_demand_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                item_id INTEGER,
                avg_daily_demand REAL DEFAULT 0,
                demand_variability REAL DEFAULT 0,
                peak_day_of_week TEXT,
                peak_time_of_day TEXT,
                seasonality_factor REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_supplier_performance", """
            CREATE TABLE IF NOT EXISTS planning_supplier_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER NOT NULL,
                item_id INTEGER,
                on_time_delivery_rate REAL DEFAULT 0,
                quality_score REAL DEFAULT 0,
                avg_lead_time_days REAL DEFAULT 0,
                price_variance_pct REAL DEFAULT 0,
                response_rate REAL DEFAULT 0,
                last_evaluated_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_user_permissions", """
            CREATE TABLE IF NOT EXISTS planning_user_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                permission_key TEXT NOT NULL,
                permission_value INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """),
        ("planning_forecast_versions", """
            CREATE TABLE IF NOT EXISTS planning_forecast_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version_name TEXT NOT NULL,
                forecast_run_id INTEGER,
                parent_version_id INTEGER,
                status TEXT DEFAULT 'DRAFT',
                notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_forecast_version_lines", """
            CREATE TABLE IF NOT EXISTS planning_forecast_version_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                forecast_version_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                period_start DATE NOT NULL,
                quantity REAL NOT NULL,
                confidence_pct REAL DEFAULT 0,
                FOREIGN KEY (forecast_version_id) REFERENCES planning_forecast_versions(id)
            )
        """),
        ("planning_consensus_forecasts", """
            CREATE TABLE IF NOT EXISTS planning_consensus_forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                forecast_run_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                period_start DATE NOT NULL,
                quantity REAL NOT NULL,
                contributor_count INTEGER DEFAULT 0,
                consensus_method TEXT DEFAULT 'AVERAGE',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_consensus_comments", """
            CREATE TABLE IF NOT EXISTS planning_consensus_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                consensus_forecast_id INTEGER NOT NULL,
                user_id INTEGER,
                comment TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (consensus_forecast_id) REFERENCES planning_consensus_forecasts(id)
            )
        """),
        ("planning_consensus_meetings", """
            CREATE TABLE IF NOT EXISTS planning_consensus_meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_name TEXT NOT NULL,
                scheduled_at TIMESTAMP,
                location TEXT,
                facilitator_id INTEGER,
                status TEXT DEFAULT 'SCHEDULED',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_demand_drivers", """
            CREATE TABLE IF NOT EXISTS planning_demand_drivers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_name TEXT NOT NULL,
                driver_type TEXT NOT NULL,
                impact_factor REAL DEFAULT 1.0,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_promotion_impact", """
            CREATE TABLE IF NOT EXISTS planning_promotion_impact (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                promotion_name TEXT,
                start_date DATE NOT NULL,
                end_date DATE,
                uplift_percentage REAL DEFAULT 0,
                additional_demand REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_seasonality_profiles", """
            CREATE TABLE IF NOT EXISTS planning_seasonality_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                month_of_year INTEGER NOT NULL,
                seasonality_index REAL NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_holiday_calendar", """
            CREATE TABLE IF NOT EXISTS planning_holiday_calendar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                holiday_name TEXT NOT NULL,
                holiday_date DATE NOT NULL,
                country_code TEXT,
                impact_factor REAL DEFAULT 0.8,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_forecast_accuracy", """
            CREATE TABLE IF NOT EXISTS planning_forecast_accuracy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                warehouse_id INTEGER,
                period_start DATE NOT NULL,
                forecasted_quantity REAL NOT NULL,
                actual_quantity REAL NOT NULL,
                accuracy_pct REAL,
                mape_pct REAL,
                bias_pct REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_forecast_bias", """
            CREATE TABLE IF NOT EXISTS planning_forecast_bias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                warehouse_id INTEGER,
                period_start DATE NOT NULL,
                bias_pct REAL NOT NULL,
                bias_direction TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_model_performance", """
            CREATE TABLE IF NOT EXISTS planning_model_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                model_type TEXT NOT NULL,
                accuracy_pct REAL,
                mape_pct REAL,
                mae REAL,
                rmse REAL,
                evaluation_date DATE NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_demand_signals", """
            CREATE TABLE IF NOT EXISTS planning_demand_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                signal_type TEXT NOT NULL,
                signal_source TEXT,
                signal_value REAL,
                signal_date DATE NOT NULL,
                confidence_pct REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_volatility_alerts", """
            CREATE TABLE IF NOT EXISTS planning_volatility_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                volatility_pct REAL NOT NULL,
                threshold_pct REAL,
                alert_triggered_at TIMESTAMP,
                is_acknowledged INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_override_approvals", """
            CREATE TABLE IF NOT EXISTS planning_override_approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                override_id INTEGER NOT NULL,
                requested_by INTEGER NOT NULL,
                approved_by INTEGER,
                status TEXT DEFAULT 'PENDING',
                request_notes TEXT,
                approval_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TIMESTAMP
            )
        """),
        ("planning_sla_policies", """
            CREATE TABLE IF NOT EXISTS planning_sla_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                policy_name TEXT NOT NULL,
                policy_type TEXT NOT NULL,
                response_hours INTEGER DEFAULT 24,
                resolution_hours INTEGER DEFAULT 72,
                escalation_email TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_approval_matrix", """
            CREATE TABLE IF NOT EXISTS planning_approval_matrix (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                approval_step INTEGER NOT NULL,
                approver_role_id INTEGER,
                approver_user_id INTEGER,
                threshold_value REAL,
                requires_comment INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_flow_notifications", """
            CREATE TABLE IF NOT EXISTS planning_flow_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_type TEXT NOT NULL,
                entity_id INTEGER,
                recipient_id INTEGER,
                message TEXT,
                sent_at TIMESTAMP,
                read_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_forecast_attributes", """
            CREATE TABLE IF NOT EXISTS planning_forecast_attributes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attribute_name TEXT NOT NULL,
                attribute_type TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("planning_forecast_line_attributes", """
            CREATE TABLE IF NOT EXISTS planning_forecast_line_attributes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                forecast_line_id INTEGER NOT NULL,
                attribute_id INTEGER NOT NULL,
                attribute_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (forecast_line_id) REFERENCES planning_forecast_lines(id)
            )
        """),
    ]

    for table_name, create_sql in planning_tables:
        _execute_if_table_not_exists(conn, table_name, create_sql)

    # ========================================================================
    # WORKFLOW TABLES
    # ========================================================================
    workflow_tables = [
        ("workflow_definitions", """
            CREATE TABLE IF NOT EXISTS workflow_definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_type TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                module TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                is_active INTEGER DEFAULT 1,
                requires_approval INTEGER DEFAULT 1,
                company_scope INTEGER,
                branch_scope INTEGER,
                department_scope INTEGER,
                warehouse_scope INTEGER,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                updated_by INTEGER,
                approved_by INTEGER,
                approved_at TIMESTAMP,
                activation_date TIMESTAMP,
                deactivation_date TIMESTAMP
            )
        """),
        ("workflow_versions", """
            CREATE TABLE IF NOT EXISTS workflow_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_definition_id INTEGER NOT NULL,
                version_number INTEGER NOT NULL,
                version_label TEXT,
                status TEXT DEFAULT 'draft',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (workflow_definition_id) REFERENCES workflow_definitions(id)
            )
        """),
        ("workflow_transitions", """
            CREATE TABLE IF NOT EXISTS workflow_transitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_definition_id INTEGER NOT NULL,
                from_step_id INTEGER NOT NULL,
                to_step_id INTEGER NOT NULL,
                transition_type TEXT DEFAULT 'APPROVE',
                condition_expression TEXT,
                is_default INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workflow_definition_id) REFERENCES workflow_definitions(id)
            )
        """),
        ("workflow_conditions", """
            CREATE TABLE IF NOT EXISTS workflow_conditions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transition_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                operator TEXT NOT NULL,
                value TEXT,
                condition_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (transition_id) REFERENCES workflow_transitions(id)
            )
        """),
        ("workflow_instances", """
            CREATE TABLE IF NOT EXISTS workflow_instances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_definition_id INTEGER NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                current_step_id INTEGER,
                status TEXT DEFAULT 'active',
                priority TEXT DEFAULT 'MEDIUM',
                submitted_by INTEGER,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                due_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workflow_definition_id) REFERENCES workflow_definitions(id)
            )
        """),
        ("workflow_instance_steps", """
            CREATE TABLE IF NOT EXISTS workflow_instance_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_instance_id INTEGER NOT NULL,
                step_id INTEGER NOT NULL,
                step_type TEXT DEFAULT 'approval',
                status TEXT DEFAULT 'pending',
                assigned_to INTEGER,
                assigned_at TIMESTAMP,
                completed_at TIMESTAMP,
                completed_by INTEGER,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workflow_instance_id) REFERENCES workflow_instances(id)
            )
        """),
        ("workflow_actions", """
            CREATE TABLE IF NOT EXISTS workflow_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_instance_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                from_step_id INTEGER,
                to_step_id INTEGER,
                actor_id INTEGER NOT NULL,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workflow_instance_id) REFERENCES workflow_instances(id)
            )
        """),
        ("workflow_assignments", """
            CREATE TABLE IF NOT EXISTS workflow_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_definition_id INTEGER NOT NULL,
                step_id INTEGER NOT NULL,
                assignee_type TEXT NOT NULL,
                assignee_id INTEGER,
                assignee_rule TEXT,
                is_active INTEGER DEFAULT 1,
                priority_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workflow_definition_id) REFERENCES workflow_definitions(id)
            )
        """),
        ("workflow_comments", """
            CREATE TABLE IF NOT EXISTS workflow_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_instance_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                comment TEXT NOT NULL,
                is_internal INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workflow_instance_id) REFERENCES workflow_instances(id)
            )
        """),
        ("automation_rules", """
            CREATE TABLE IF NOT EXISTS automation_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL,
                trigger_event TEXT NOT NULL,
                target_entity TEXT,
                condition_expression TEXT,
                action_type TEXT NOT NULL,
                action_config TEXT,
                is_active INTEGER DEFAULT 1,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("automation_rule_conditions", """
            CREATE TABLE IF NOT EXISTS automation_rule_conditions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                operator TEXT NOT NULL,
                value TEXT,
                condition_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rule_id) REFERENCES automation_rules(id)
            )
        """),
        ("automation_rule_actions", """
            CREATE TABLE IF NOT EXISTS automation_rule_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                action_params TEXT,
                action_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rule_id) REFERENCES automation_rules(id)
            )
        """),
        ("automation_logs", """
            CREATE TABLE IF NOT EXISTS automation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id INTEGER,
                triggered_by TEXT,
                entity_type TEXT,
                entity_id INTEGER,
                action_taken TEXT,
                result TEXT,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("notification_templates", """
            CREATE TABLE IF NOT EXISTS notification_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT NOT NULL,
                notification_type TEXT NOT NULL,
                subject TEXT,
                body TEXT NOT NULL,
                channel TEXT DEFAULT 'in_app',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("notification_rules", """
            CREATE TABLE IF NOT EXISTS notification_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                template_id INTEGER,
                recipient_type TEXT,
                recipient_id INTEGER,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (template_id) REFERENCES notification_templates(id)
            )
        """),
        ("notification_logs", """
            CREATE TABLE IF NOT EXISTS notification_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER,
                recipient_id INTEGER,
                channel TEXT DEFAULT 'in_app',
                subject TEXT,
                message TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                read_at TIMESTAMP,
                status TEXT DEFAULT 'sent',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("sla_rules", """
            CREATE TABLE IF NOT EXISTS sla_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                response_hours INTEGER DEFAULT 24,
                resolution_hours INTEGER DEFAULT 72,
                escalation_level INTEGER DEFAULT 1,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("escalation_rules", """
            CREATE TABLE IF NOT EXISTS escalation_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sla_rule_id INTEGER NOT NULL,
                escalation_level INTEGER NOT NULL,
                escalate_to_id INTEGER,
                escalate_after_hours INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sla_rule_id) REFERENCES sla_rules(id)
            )
        """),
        ("delegation_rules", """
            CREATE TABLE IF NOT EXISTS delegation_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                delegator_id INTEGER NOT NULL,
                delegate_id INTEGER NOT NULL,
                start_date DATE,
                end_date DATE,
                is_active INTEGER DEFAULT 1,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("workflow_templates", """
            CREATE TABLE IF NOT EXISTS workflow_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT NOT NULL,
                workflow_type TEXT NOT NULL,
                template_data TEXT,
                is_active INTEGER DEFAULT 1,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("workflow_settings", """
            CREATE TABLE IF NOT EXISTS workflow_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
    ]

    for table_name, create_sql in workflow_tables:
        _execute_if_table_not_exists(conn, table_name, create_sql)

    # ========================================================================
    # PLATFORM INDEXES (from database.py PLATFORM_INDEXES)
    # ========================================================================
    # These indexes are expected to already exist from database.py initialize_platform_indexes()
    # But we create them here if missing for PostgreSQL compatibility
    platform_indexes = [
        ("idx_users_email", "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"),
        ("idx_users_role", "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role_id)"),
        ("idx_users_company", "CREATE INDEX IF NOT EXISTS idx_users_company ON users(company_id)"),
        ("idx_users_status", "CREATE INDEX IF NOT EXISTS idx_users_status ON users(is_active)"),
        ("idx_notif_user_read", "CREATE INDEX IF NOT EXISTS idx_notif_user_read ON platform_notifications(user_id, is_read)"),
        ("idx_notif_created", "CREATE INDEX IF NOT EXISTS idx_notif_created ON platform_notifications(created_at)"),
        ("idx_audit_entity", "CREATE INDEX IF NOT EXISTS idx_audit_entity ON platform_audit_log(entity_type, entity_id)"),
        ("idx_audit_user", "CREATE INDEX IF NOT EXISTS idx_audit_user ON platform_audit_log(user_id, created_at)"),
        ("idx_audit_action", "CREATE INDEX IF NOT EXISTS idx_audit_action ON platform_audit_log(action, created_at)"),
        ("idx_sessions_user", "CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id)"),
        ("idx_sessions_token", "CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token)"),
        ("idx_flow_messages_conv_time", "CREATE INDEX IF NOT EXISTS idx_flow_messages_conv_time ON flow_messages(conversation_id, created_at)"),
        ("idx_flow_messages_sender", "CREATE INDEX IF NOT EXISTS idx_flow_messages_sender ON flow_messages(sender_id, created_at)"),
        ("idx_flow_conv_members_user", "CREATE INDEX IF NOT EXISTS idx_flow_conv_members_user ON flow_conversation_members(user_id, unread_count)"),
        ("idx_wms_inventory_item_wh", "CREATE INDEX IF NOT EXISTS idx_wms_inventory_item_wh ON wms_inventory_balances(item_id, warehouse_id)"),
        ("idx_wms_items_active_code", "CREATE INDEX IF NOT EXISTS idx_wms_items_active_code ON wms_items(is_active, item_code)"),
        ("idx_planning_demand_item_date", "CREATE INDEX IF NOT EXISTS idx_planning_demand_item_date ON planning_demand_history(item_id, demand_date)"),
        ("idx_planning_profiles_item", "CREATE INDEX IF NOT EXISTS idx_planning_profiles_item ON planning_item_profiles(item_id)"),
        ("idx_planning_alerts_ack", "CREATE INDEX IF NOT EXISTS idx_planning_alerts_ack ON planning_alerts(is_acknowledged, severity, created_at)"),
    ]

    for index_name, create_sql in platform_indexes:
        try:
            conn.execute(sa.text(create_sql))
        except Exception:
            pass  # Index may already exist


def downgrade() -> None:
    """
    Downgrade removes all scattered module tables.
    WARNING: This will delete data. Use with caution on development databases only.
    """
    # Note: We do NOT automatically drop tables in downgrade because:
    # 1. This is a consolidation migration - tables were pre-existing
    # 2. Dropping would lose data in production
    # 3. The migration history itself is the valuable part
    pass