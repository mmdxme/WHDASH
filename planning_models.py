"""
Planning Models - Enterprise Demand Forecasting & Inventory Planning System

This module defines all database tables, helper functions, and constants
required for the enterprise Demand Forecasting and Inventory Planning System.

Tables:
- planning_demand_history: Aggregated demand/consumption data per item/period
- planning_sales_history: Sales transaction records for forecasting
- planning_item_profiles: Per-item planning configuration
- planning_policies: Configurable planning policies (safety stock, reorder, etc.)
- planning_policy_assignments: Links policies to items/groups/brands/warehouses
- planning_forecast_runs: Forecast generation runs
- planning_forecast_lines: Individual forecast quantities per item/period
- planning_forecast_overrides: Manual forecast overrides
- planning_replenishment_recommendations: Replenishment suggestions
- planning_purchase_recommendations: Purchase order suggestions
- planning_transfer_recommendations: Transfer suggestions
- planning_scenarios: What-if scenario definitions
- planning_scenario_lines: Scenario impact results
- planning_alerts: Active planning exceptions and alerts
- planning_kpi_records: Historical KPI snapshots
- planning_audit_log: Full audit trail for planning actions
- planning_settings: Global and per-company planning configuration

ENTERPRISE EXTENSIONS:
- planning_forecast_versions: Version control for forecast snapshots
- planning_forecast_version_lines: Lines within each version snapshot
- planning_consensus_forecasts: Collaborative/consensus forecast entries
- planning_consensus_comments: Discussion notes on consensus forecasts
- planning_demand_drivers: Causal factors and demand drivers
- planning_promotion_impact: Promotion and campaign impact records
- planning_seasonality_profiles: Seasonality patterns and indices
- planning_forecast_accuracy: Per-item/period accuracy metrics
- planning_forecast_bias: Bias tracking per item/planner
- planning_demand_signals: Short-term demand signal records
- planning_override_approvals: Override approval workflow records
- planning_sla_policies: SLA and approval routing policies
- planning_approval_matrix: Role-based approval routing
- planning_flow_notifications: Flow integration notification records
"""

import sqlite3
import json
import math
from datetime import datetime, timedelta
from collections import defaultdict


# ============================================================
# TABLE CREATION SQL
# ============================================================

PLANNING_TABLES_SQL = [
    """
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
    """,
    """
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
    """,
    """
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
    """,
    """
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
    """,
    """
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
    """,
    """
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
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_forecast_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        warehouse_id INTEGER,
        company_id INTEGER,
        period_start DATE NOT NULL,
        period_type TEXT DEFAULT 'daily',
        base_quantity REAL DEFAULT 0,
        trend_factor REAL DEFAULT 1.0,
        seasonal_factor REAL DEFAULT 1.0,
        override_quantity REAL,
        final_quantity REAL DEFAULT 0,
        confidence REAL DEFAULT 0.5,
        is_frozen INTEGER DEFAULT 0,
        notes TEXT,
        override_reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (run_id) REFERENCES planning_forecast_runs(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_forecast_overrides (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        warehouse_id INTEGER,
        company_id INTEGER,
        forecast_run_id INTEGER,
        period_start DATE NOT NULL,
        period_type TEXT DEFAULT 'daily',
        original_quantity REAL NOT NULL,
        override_quantity REAL NOT NULL,
        override_reason TEXT,
        override_type TEXT DEFAULT 'MANUAL',
        status TEXT DEFAULT 'PENDING',
        reviewed_by INTEGER,
        reviewed_at TIMESTAMP,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_replenishment_recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        warehouse_id INTEGER,
        company_id INTEGER,
        recommendation_type TEXT NOT NULL,
        action TEXT NOT NULL,
        priority INTEGER DEFAULT 50,
        current_stock REAL DEFAULT 0,
        safety_stock_level REAL DEFAULT 0,
        reorder_point_level REAL DEFAULT 0,
        forecasted_demand REAL DEFAULT 0,
        open_demand REAL DEFAULT 0,
        open_supply REAL DEFAULT 0,
        recommended_quantity REAL DEFAULT 0,
        recommended_date DATE,
        suggested_supplier_id INTEGER,
        estimated_cost REAL DEFAULT 0,
        service_level_impact REAL,
        stockout_risk TEXT,
        notes TEXT,
        scenario_id INTEGER,
        status TEXT DEFAULT 'OPEN',
        created_by INTEGER,
        reviewed_by INTEGER,
        reviewed_at TIMESTAMP,
        approved_by INTEGER,
        approved_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_purchase_recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        warehouse_id INTEGER,
        company_id INTEGER,
        supplier_id INTEGER NOT NULL,
        recommendation_type TEXT DEFAULT 'NORMAL',
        action TEXT NOT NULL,
        priority INTEGER DEFAULT 50,
        current_stock REAL DEFAULT 0,
        forecasted_demand REAL DEFAULT 0,
        open_po_quantity REAL DEFAULT 0,
        in_transit_quantity REAL DEFAULT 0,
        recommended_quantity REAL DEFAULT 0,
        suggested_order_date DATE,
        suggested_arrival_date DATE,
        suggested_unit_cost REAL DEFAULT 0,
        estimated_total_cost REAL DEFAULT 0,
        moq REAL DEFAULT 0,
        order_multiple REAL DEFAULT 1,
        lead_time_days INTEGER DEFAULT 7,
        shortage_date DATE,
        shortage_risk TEXT,
        budget_impact REAL,
        service_level_impact REAL,
        risk_notes TEXT,
        scenario_id INTEGER,
        status TEXT DEFAULT 'OPEN',
        created_by INTEGER,
        approved_by INTEGER,
        approved_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_transfer_recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        source_warehouse_id INTEGER NOT NULL,
        destination_warehouse_id INTEGER NOT NULL,
        source_company_id INTEGER,
        destination_company_id INTEGER,
        action TEXT NOT NULL,
        priority INTEGER DEFAULT 50,
        source_current_stock REAL DEFAULT 0,
        destination_current_stock REAL DEFAULT 0,
        source_excess_quantity REAL DEFAULT 0,
        destination_shortage_quantity REAL DEFAULT 0,
        recommended_quantity REAL DEFAULT 0,
        urgency TEXT DEFAULT 'NORMAL',
        suggested_transfer_date DATE,
        suggested_arrival_date DATE,
        estimated_transfer_cost REAL,
        purchase_avoidance_value REAL,
        service_level_impact REAL,
        notes TEXT,
        scenario_id INTEGER,
        status TEXT DEFAULT 'OPEN',
        created_by INTEGER,
        reviewed_by INTEGER,
        reviewed_at TIMESTAMP,
        approved_by INTEGER,
        approved_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_scenarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        scenario_type TEXT NOT NULL,
        parameters_json TEXT,
        is_active INTEGER DEFAULT 1,
        is_base INTEGER DEFAULT 0,
        parent_scenario_id INTEGER,
        total_impact_items INTEGER DEFAULT 0,
        total_shortage_impact REAL DEFAULT 0,
        total_excess_impact REAL DEFAULT 0,
        total_cost_impact REAL DEFAULT 0,
        notes TEXT,
        created_by INTEGER,
        approved_by INTEGER,
        approved_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_scenario_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scenario_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        warehouse_id INTEGER,
        company_id INTEGER,
        metric_name TEXT NOT NULL,
        base_value REAL DEFAULT 0,
        scenario_value REAL DEFAULT 0,
        impact_value REAL DEFAULT 0,
        impact_percent REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (scenario_id) REFERENCES planning_scenarios(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_type TEXT NOT NULL,
        severity TEXT NOT NULL DEFAULT 'MEDIUM',
        title TEXT NOT NULL,
        message TEXT,
        item_id INTEGER,
        warehouse_id INTEGER,
        company_id INTEGER,
        supplier_id INTEGER,
        customer_id INTEGER,
        recommendation_id INTEGER,
        scenario_id INTEGER,
        is_acknowledged INTEGER DEFAULT 0,
        acknowledged_by INTEGER,
        acknowledged_at TIMESTAMP,
        resolved_by INTEGER,
        resolved_at TIMESTAMP,
        resolved_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_kpi_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kpi_name TEXT NOT NULL,
        period_type TEXT NOT NULL,
        period_start DATE NOT NULL,
        company_id INTEGER,
        warehouse_id INTEGER,
        item_id INTEGER,
        brand_id INTEGER,
        category_id INTEGER,
        value REAL NOT NULL,
        target REAL,
        variance REAL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(kpi_name, period_type, period_start, company_id, warehouse_id, item_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_type TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id INTEGER,
        item_id INTEGER,
        warehouse_id INTEGER,
        company_id INTEGER,
        user_id INTEGER,
        changes_json TEXT,
        notes TEXT,
        ip_address TEXT,
        user_agent TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_key TEXT NOT NULL UNIQUE,
        setting_value TEXT,
        setting_type TEXT DEFAULT 'STRING',
        category TEXT DEFAULT 'GENERAL',
        description TEXT,
        is_active INTEGER DEFAULT 1,
        company_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_lost_sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        warehouse_id INTEGER,
        company_id INTEGER,
        customer_id INTEGER,
        lost_date DATE NOT NULL,
        requested_quantity REAL NOT NULL,
        fulfilled_quantity REAL DEFAULT 0,
        lost_quantity REAL DEFAULT 0,
        unit_price REAL DEFAULT 0,
        lost_value REAL DEFAULT 0,
        lost_reason TEXT,
        customer_type TEXT,
        is_export INTEGER DEFAULT 0,
        salesperson_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_customer_demand_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        item_id INTEGER,
        warehouse_id INTEGER,
        company_id INTEGER,
        total_orders INTEGER DEFAULT 0,
        total_quantity REAL DEFAULT 0,
        total_value REAL DEFAULT 0,
        avg_order_quantity REAL DEFAULT 0,
        avg_order_interval_days REAL DEFAULT 0,
        last_order_date DATE,
        first_order_date DATE,
        demand_trend TEXT DEFAULT 'STABLE',
        demand_variability REAL DEFAULT 0,
        seasonality_pattern TEXT,
        is_key_customer INTEGER DEFAULT 0,
        is_at_risk INTEGER DEFAULT 0,
        concentration_percent REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_supplier_performance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_id INTEGER NOT NULL,
        item_id INTEGER,
        company_id INTEGER,
        period_type TEXT DEFAULT 'MONTHLY',
        period_start DATE NOT NULL,
        total_orders INTEGER DEFAULT 0,
        total_quantity_ordered REAL DEFAULT 0,
        total_quantity_received REAL DEFAULT 0,
        on_time_count INTEGER DEFAULT 0,
        on_time_percent REAL DEFAULT 0,
        fill_rate REAL DEFAULT 0,
        avg_lead_time_days REAL DEFAULT 0,
        quality_issues INTEGER DEFAULT 0,
        emergency_order_count INTEGER DEFAULT 0,
        avg_unit_cost REAL DEFAULT 0,
        cost_variance_percent REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_demand_history_item_period
        ON planning_demand_history(item_id, period_type, period_start)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_demand_history_warehouse
        ON planning_demand_history(warehouse_id, company_id, period_start)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_forecast_lines_run
        ON planning_forecast_lines(run_id, item_id, period_start)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_replenishment_status
        ON planning_replenishment_recommendations(status, priority, created_at)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_purchase_rec_status
        ON planning_purchase_recommendations(status, priority, suggested_order_date)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_transfer_rec_status
        ON planning_transfer_recommendations(status, priority)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_planning_alerts_active
        ON planning_alerts(is_acknowledged, severity, created_at)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_kpi_records_period
        ON planning_kpi_records(kpi_name, period_type, period_start)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_audit_log_entity
        ON planning_audit_log(entity_type, entity_id, created_at)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_lost_sales_item_date
        ON planning_lost_sales(item_id, lost_date)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_customer_patterns_customer
        ON planning_customer_demand_patterns(customer_id, item_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_supplier_perf_period
        ON planning_supplier_performance(supplier_id, period_start)
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_user_permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        permission_key TEXT NOT NULL,
        granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        granted_by INTEGER,
        UNIQUE(user_id, permission_key)
    )
    """,
    # ============================================================
    # ENTERPRISE FORECAST VERSIONS & SNAPSHOTS
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS planning_forecast_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version_name TEXT NOT NULL,
        version_number INTEGER NOT NULL DEFAULT 1,
        description TEXT,
        status TEXT NOT NULL DEFAULT 'DRAFT',
        forecast_run_id INTEGER,
        parent_version_id INTEGER,
        is_baseline INTEGER DEFAULT 0,
        is_frozen INTEGER DEFAULT 0,
        published_at TIMESTAMP,
        published_by INTEGER,
        total_items INTEGER DEFAULT 0,
        total_quantity REAL DEFAULT 0,
        notes TEXT,
        created_by INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (forecast_run_id) REFERENCES planning_forecast_runs(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_forecast_version_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        warehouse_id INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        period_start DATE NOT NULL,
        period_type TEXT DEFAULT 'daily',
        baseline_quantity REAL DEFAULT 0,
        override_quantity REAL DEFAULT 0,
        consensus_quantity REAL DEFAULT 0,
        approved_quantity REAL DEFAULT 0,
        final_quantity REAL DEFAULT 0,
        confidence_level REAL DEFAULT 0.5,
        source TEXT DEFAULT 'BASELINE',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (version_id) REFERENCES planning_forecast_versions(id)
    )
    """,
    # ============================================================
    # CONSENSUS PLANNING
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS planning_consensus_forecasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        warehouse_id INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        customer_segment TEXT,
        channel TEXT,
        period_start DATE NOT NULL,
        period_type TEXT DEFAULT 'daily',
        sales_input REAL,
        sales_confidence REAL DEFAULT 0.5,
        planner_input REAL,
        planner_confidence REAL DEFAULT 0.5,
        marketing_input REAL,
        marketing_confidence REAL DEFAULT 0.5,
        consensus_value REAL,
        final_approved_value REAL,
        status TEXT DEFAULT 'DRAFT',
        disagreement_level TEXT DEFAULT 'LOW',
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (version_id) REFERENCES planning_forecast_versions(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_consensus_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        consensus_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        user_role TEXT,
        comment_text TEXT NOT NULL,
        is_internal INTEGER DEFAULT 1,
        parent_comment_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (consensus_id) REFERENCES planning_consensus_forecasts(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_consensus_meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_title TEXT NOT NULL,
        meeting_date DATE NOT NULL,
        version_id INTEGER,
        status TEXT DEFAULT 'SCHEDULED',
        attendees TEXT,
        notes TEXT,
        decisions TEXT,
        action_items TEXT,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # ============================================================
    # DEMAND DRIVERS & CAUSAL FACTORS
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS planning_demand_drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_name TEXT NOT NULL,
        driver_type TEXT NOT NULL,
        description TEXT,
        impact_factor REAL DEFAULT 1.0,
        start_date DATE,
        end_date DATE,
        is_active INTEGER DEFAULT 1,
        item_id INTEGER,
        brand_id INTEGER,
        category_id INTEGER,
        company_id INTEGER,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_promotion_impact (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        promotion_name TEXT NOT NULL,
        promotion_type TEXT NOT NULL,
        item_id INTEGER,
        brand_id INTEGER,
        category_id INTEGER,
        warehouse_id INTEGER,
        company_id INTEGER,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        expected_uplift_percent REAL DEFAULT 0,
        actual_uplift_percent REAL,
        expected_additional_demand REAL DEFAULT 0,
        actual_additional_demand REAL,
        budget_allocated REAL,
        budget_spent REAL,
        status TEXT DEFAULT 'PLANNED',
        notes TEXT,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_seasonality_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_name TEXT NOT NULL,
        item_id INTEGER,
        brand_id INTEGER,
        category_id INTEGER,
        company_id INTEGER,
        period_type TEXT DEFAULT 'monthly',
        jan_factor REAL DEFAULT 1.0,
        feb_factor REAL DEFAULT 1.0,
        mar_factor REAL DEFAULT 1.0,
        apr_factor REAL DEFAULT 1.0,
        may_factor REAL DEFAULT 1.0,
        jun_factor REAL DEFAULT 1.0,
        jul_factor REAL DEFAULT 1.0,
        aug_factor REAL DEFAULT 1.0,
        sep_factor REAL DEFAULT 1.0,
        oct_factor REAL DEFAULT 1.0,
        nov_factor REAL DEFAULT 1.0,
        dec_factor REAL DEFAULT 1.0,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_holiday_calendar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        holiday_name TEXT NOT NULL,
        holiday_date DATE NOT NULL,
        holiday_type TEXT DEFAULT 'NATIONAL',
        region TEXT,
        impact_factor REAL DEFAULT 1.0,
        affected_days INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1,
        company_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # ============================================================
    # FORECAST ACCURACY & BIAS TRACKING
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS planning_forecast_accuracy (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        warehouse_id INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        version_id INTEGER,
        period_start DATE NOT NULL,
        period_type TEXT DEFAULT 'daily',
        forecast_quantity REAL DEFAULT 0,
        actual_quantity REAL DEFAULT 0,
        error_quantity REAL DEFAULT 0,
        absolute_error REAL DEFAULT 0,
        percent_error REAL,
        absolute_percent_error REAL,
        squared_error REAL DEFAULT 0,
        mape REAL,
        wape REAL,
        bias REAL DEFAULT 0,
        tracking_signal REAL,
        calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (version_id) REFERENCES planning_forecast_versions(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_forecast_bias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        warehouse_id INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        planner_id INTEGER,
        period_type TEXT DEFAULT 'monthly',
        period_start DATE NOT NULL,
        total_forecast REAL DEFAULT 0,
        total_actual REAL DEFAULT 0,
        bias_amount REAL DEFAULT 0,
        bias_percent REAL DEFAULT 0,
        forecast_count INTEGER DEFAULT 0,
        over_forecast_count INTEGER DEFAULT 0,
        under_forecast_count INTEGER DEFAULT 0,
        calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_model_performance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,
        model_name TEXT NOT NULL,
        period_start DATE NOT NULL,
        period_end DATE NOT NULL,
        mape REAL,
        wape REAL,
        mae REAL,
        bias REAL,
        rmse REAL,
        theil_u REAL,
        is_best_fit INTEGER DEFAULT 0,
        parameters_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # ============================================================
    # DEMAND SIGNALS (DEMAND SENSING SCAFFOLD)
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS planning_demand_signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        warehouse_id INTEGER,
        company_id INTEGER,
        signal_type TEXT NOT NULL,
        signal_source TEXT,
        signal_value REAL,
        signal_direction TEXT,
        volatility_score REAL DEFAULT 0,
        anomaly_score REAL DEFAULT 0,
        signal_date DATE NOT NULL,
        period_start DATE,
        period_end DATE,
        confidence REAL DEFAULT 0.5,
        is_reviewed INTEGER DEFAULT 0,
        reviewed_by INTEGER,
        reviewed_at TIMESTAMP,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_volatility_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        warehouse_id INTEGER,
        company_id INTEGER,
        alert_type TEXT NOT NULL,
        severity TEXT DEFAULT 'MEDIUM',
        threshold_value REAL,
        actual_value REAL,
        cv_value REAL,
        z_score REAL,
        is_acknowledged INTEGER DEFAULT 0,
        acknowledged_by INTEGER,
        acknowledged_at TIMESTAMP,
        resolution_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # ============================================================
    # OVERRIDE APPROVAL WORKFLOW
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS planning_override_approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        override_id INTEGER NOT NULL,
        approval_status TEXT DEFAULT 'PENDING',
        requested_by INTEGER NOT NULL,
        requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        reviewed_by INTEGER,
        reviewed_at TIMESTAMP,
        review_notes TEXT,
        approval_level INTEGER DEFAULT 1,
        escalation_reason TEXT,
        FOREIGN KEY (override_id) REFERENCES planning_forecast_overrides(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_sla_policies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        policy_name TEXT NOT NULL,
        policy_type TEXT NOT NULL,
        priority_level TEXT DEFAULT 'MEDIUM',
        response_hours INTEGER DEFAULT 24,
        resolution_hours INTEGER DEFAULT 48,
        escalation_hours INTEGER DEFAULT 8,
        auto_escalate INTEGER DEFAULT 1,
        notify_users TEXT,
        is_active INTEGER DEFAULT 1,
        company_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_approval_matrix (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,
        action_type TEXT NOT NULL,
        threshold_value REAL,
        threshold_operator TEXT DEFAULT 'GREATER',
        requires_approval_level INTEGER DEFAULT 1,
        approver_role TEXT,
        approver_user_id INTEGER,
        bypass_role TEXT,
        is_active INTEGER DEFAULT 1,
        company_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # ============================================================
    # FLOW INTEGRATION
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS planning_flow_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        notification_type TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT,
        entity_type TEXT,
        entity_id INTEGER,
        priority TEXT DEFAULT 'NORMAL',
        is_read INTEGER DEFAULT 0,
        read_at TIMESTAMP,
        read_by INTEGER,
        action_url TEXT,
        flow_thread_id TEXT,
        created_by INTEGER,
        company_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # ============================================================
    # FORECAST ATTRIBUTES & TAGS
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS planning_forecast_attributes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attribute_name TEXT NOT NULL UNIQUE,
        attribute_type TEXT DEFAULT 'STRING',
        possible_values TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS planning_forecast_line_attributes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        forecast_line_id INTEGER NOT NULL,
        attribute_id INTEGER NOT NULL,
        attribute_value TEXT,
        FOREIGN KEY (forecast_line_id) REFERENCES planning_forecast_lines(id),
        FOREIGN KEY (attribute_id) REFERENCES planning_forecast_attributes(id)
    )
    """,
]


# ============================================================
# DEFAULT SETTINGS
# ============================================================

DEFAULT_PLANNING_SETTINGS = {
    "DEFAULT_FORECAST_METHOD": {"value": "MOVING_AVERAGE", "type": "STRING", "category": "FORECAST"},
    "FORECAST_HORIZON_DAYS": {"value": "30", "type": "INTEGER", "category": "FORECAST"},
    "FORECAST_PERIOD_TYPE": {"value": "daily", "type": "STRING", "category": "FORECAST"},
    "DEMAND_HISTORY_MONTHS": {"value": "12", "type": "INTEGER", "category": "FORECAST"},
    "USE_SEASONALITY": {"value": "1", "type": "BOOLEAN", "category": "FORECAST"},
    "USE_TREND": {"value": "1", "type": "BOOLEAN", "category": "FORECAST"},
    "RECENT_DEMAND_WEIGHT": {"value": "0.3", "type": "FLOAT", "category": "FORECAST"},
    "DEFAULT_SAFETY_STOCK_DAYS": {"value": "7", "type": "INTEGER", "category": "INVENTORY"},
    "DEFAULT_SERVICE_LEVEL": {"value": "0.95", "type": "FLOAT", "category": "INVENTORY"},
    "DEFAULT_REORDER_POINT_DAYS": {"value": "3", "type": "INTEGER", "category": "INVENTORY"},
    "DEFAULT_LEAD_TIME_DAYS": {"value": "7", "type": "INTEGER", "category": "INVENTORY"},
    "DEFAULT_MIN_ORDER_QTY": {"value": "0", "type": "FLOAT", "category": "INVENTORY"},
    "DEFAULT_ORDER_MULTIPLE": {"value": "1", "type": "FLOAT", "category": "INVENTORY"},
    "DEFAULT_REVIEW_CYCLE_DAYS": {"value": "30", "type": "INTEGER", "category": "INVENTORY"},
    "ALLOW_EMERGENCY_ORDERS": {"value": "1", "type": "BOOLEAN", "category": "PROCUREMENT"},
    "ALLOW_PARTIAL_FULFILLMENT": {"value": "1", "type": "BOOLEAN", "category": "PROCUREMENT"},
    "ALLOW_TRANSFER_FIRST": {"value": "1", "type": "BOOLEAN", "category": "PROCUREMENT"},
    "MAX_EMERGENCY_LEAD_TIME_DAYS": {"value": "3", "type": "INTEGER", "category": "PROCUREMENT"},
    "STOCKOUT_ALERT_THRESHOLD_DAYS": {"value": "7", "type": "INTEGER", "category": "ALERTS"},
    "LOW_STOCK_ALERT_PERCENT": {"value": "20", "type": "INTEGER", "category": "ALERTS"},
    "OVERSTOCK_ALERT_PERCENT": {"value": "150", "type": "INTEGER", "category": "ALERTS"},
    "DEAD_STOCK_DAYS": {"value": "365", "type": "INTEGER", "category": "ALERTS"},
    "SLOW_MOVING_DAYS": {"value": "180", "type": "INTEGER", "category": "ALERTS"},
    "FORECAST_ACCURACY_WINDOW": {"value": "3", "type": "INTEGER", "category": "KPI"},
    "FORECAST_BIAS_THRESHOLD": {"value": "0.1", "type": "FLOAT", "category": "KPI"},
    "SERVICE_LEVEL_TARGET": {"value": "0.95", "type": "FLOAT", "category": "KPI"},
    "INVENTORY_TURNOVER_TARGET": {"value": "8", "type": "INTEGER", "category": "KPI"},
    "ALLOW_AUTO_REPLENISHMENT": {"value": "0", "type": "BOOLEAN", "category": "AUTO"},
    "ALLOW_AUTO_PURCHASE_CREATE": {"value": "0", "type": "BOOLEAN", "category": "AUTO"},
    "ALLOW_AUTO_TRANSFER_CREATE": {"value": "0", "type": "BOOLEAN", "category": "AUTO"},
    "FORECAST_AUTO_APPROVE_THRESHOLD": {"value": "0.1", "type": "FLOAT", "category": "WORKFLOW"},
    "REQUIRE_PURCHASE_APPROVAL_ABOVE": {"value": "10000", "type": "FLOAT", "category": "WORKFLOW"},
    "REQUIRE_TRANSFER_APPROVAL": {"value": "1", "type": "BOOLEAN", "category": "WORKFLOW"},
}


# ============================================================
# INIT FUNCTION
# ============================================================

def init_planning_tables(db):
    """Initialize all planning tables and default settings."""
    for sql in PLANNING_TABLES_SQL:
        db.execute(sql)
    db.commit()

    for key, props in DEFAULT_PLANNING_SETTINGS.items():
        existing = db.execute(
            "SELECT id FROM planning_settings WHERE setting_key = ?", (key,)
        ).fetchone()
        if not existing:
            db.execute(
                """INSERT INTO planning_settings
                (setting_key, setting_value, setting_type, category)
                VALUES (?, ?, ?, ?)""",
                (key, props["value"], props["type"], props["category"])
            )
    db.commit()


# ============================================================
# DEMAND AGGREGATION HELPERS
# ============================================================

def aggregate_demand_from_ledger(db, item_id, warehouse_id=None, company_id=None,
                                  months=12, period_type='daily'):
    """
    Aggregate demand data from the WMS inventory ledger for a given item.
    This feeds the demand history table used by the forecast engine.
    """
    from datetime import datetime, timedelta

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=months * 30)

    query = """
        SELECT
            il.item_id,
            il.warehouse_id,
            CAST(julianday(il.created_at) - julianday(?) AS INTEGER) / :day_div as period_offset,
            DATE(il.created_at) as movement_date,
            il.transaction_type,
            il.quantity_moved
        FROM wms_inventory_ledger il
        WHERE il.item_id = ?
          AND DATE(il.created_at) >= ?
          AND il.transaction_type IN ('SALE', 'CONSUMPTION', 'ISSUE', 'PICK', 'DISPATCH', 'RETURN', 'ADJUSTMENT')
    """
    params = {'day_div': 1 if period_type == 'daily' else 7 if period_type == 'weekly' else 30, '_start': start_date}
    params['item'] = item_id

    if warehouse_id:
        query += " AND il.warehouse_id = :wh"
        params['wh'] = warehouse_id
    if company_id:
        query += " AND il.company_id = :co"
        params['co'] = company_id

    ledger_rows = db.execute(query, params).fetchall()

    demand_by_period = defaultdict(lambda: {
        'sales': 0, 'consumption': 0, 'returns': 0, 'orders': 0
    })

    for row in ledger_rows:
        period_key = row['movement_date']
        qty = abs(row['quantity_moved']) if row['quantity_moved'] < 0 else 0

        if row['transaction_type'] in ('SALE', 'DISPATCH', 'ISSUE'):
            demand_by_period[period_key]['sales'] += qty
            demand_by_period[period_key]['orders'] += 1
        elif row['transaction_type'] in ('CONSUMPTION', 'PICK'):
            demand_by_period[period_key]['consumption'] += qty
        elif row['transaction_type'] == 'RETURN':
            demand_by_period[period_key]['returns'] += qty

    for period_start, data in demand_by_period.items():
        db.execute("""
            INSERT OR REPLACE INTO planning_demand_history
            (item_id, warehouse_id, company_id, period_type, period_start,
             sales_quantity, consumption_quantity, order_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item_id, warehouse_id, company_id, period_type, period_start,
            data['sales'], data['consumption'], data['orders']
        ))

    db.commit()


def get_demand_stats(db, item_id, warehouse_id=None, months=12):
    """Calculate demand statistics for an item over the specified period."""
    from datetime import datetime, timedelta

    start_date = (datetime.now() - timedelta(days=months * 30)).strftime('%Y-%m-%d')

    query = """
        SELECT
            SUM(sales_quantity + consumption_quantity) as total_demand,
            AVG(sales_quantity + consumption_quantity) as avg_demand,
            COUNT(*) as periods_with_demand,
            SUM(sales_quantity) as total_sales,
            SUM(consumption_quantity) as total_consumption,
            SUM(order_count) as total_orders,
            MAX(sales_quantity + consumption_quantity) as max_demand,
            MIN(CASE WHEN sales_quantity + consumption_quantity > 0
                     THEN sales_quantity + consumption_quantity END) as min_demand
        FROM planning_demand_history
        WHERE item_id = ?
          AND period_start >= ?
    """
    params = [item_id, start_date]

    if warehouse_id:
        query += " AND warehouse_id = ?"
        params.append(warehouse_id)

    row = db.execute(query, params).fetchone()
    if not row or row['total_demand'] is None:
        return None

    total_periods = db.execute(
        "SELECT COUNT(DISTINCT period_start) FROM planning_demand_history WHERE item_id = ? AND period_start >= ?",
        [item_id, start_date]
    ).fetchone()[0] or 1

    mean_demand = row['total_demand'] / total_periods if total_periods > 0 else 0

    variance_query = """
        SELECT AVG((demand - :mean) * (demand - :mean)) as variance FROM (
            SELECT (sales_quantity + consumption_quantity) as demand
            FROM planning_demand_history
            WHERE item_id = ? AND period_start >= ?
    """
    var_params = [item_id, start_date]
    if warehouse_id:
        variance_query += " AND warehouse_id = ?"
        var_params.append(warehouse_id)
    variance_query += ")"
    var_row = db.execute(variance_query, var_params).fetchone()

    std_dev = (var_row['variance'] or 0) ** 0.5
    cv = std_dev / mean_demand if mean_demand > 0 else 0

    return {
        'total_demand': row['total_demand'] or 0,
        'avg_demand': mean_demand,
        'std_dev': std_dev,
        'cv': cv,
        'total_sales': row['total_sales'] or 0,
        'total_consumption': row['total_consumption'] or 0,
        'total_orders': row['total_orders'] or 0,
        'max_demand': row['max_demand'] or 0,
        'min_demand': row['min_demand'] or 0,
        'periods_with_demand': row['periods_with_demand'] or 0,
        'total_periods': total_periods
    }


# ============================================================
# FORECAST ENGINE HELPERS
# ============================================================

def calculate_moving_average(demand_values, window=3):
    """Simple moving average forecast."""
    if not demand_values:
        return 0
    relevant = demand_values[-window:] if len(demand_values) >= window else demand_values
    return sum(relevant) / len(relevant)


def calculate_weighted_moving_average(demand_values, weights=None):
    """
    Weighted moving average - more weight on recent periods.
    Default: more recent = higher weight (linear decay).
    """
    if not demand_values:
        return 0
    n = len(demand_values)
    if weights is None:
        weights = [(i + 1) / sum(range(1, n + 1)) for i in range(n)]
    else:
        weights = weights[-n:]
        total = sum(weights)
        weights = [w / total for w in weights]
    return sum(v * w for v, w in zip(demand_values, weights))


def calculate_seasonal_index(demand_by_period, period_length=12):
    """
    Calculate seasonal indices for each period within a cycle.
    Returns a dict of period_index -> seasonal_factor.
    """
    if len(demand_by_period) < period_length:
        return {i: 1.0 for i in range(period_length)}

    cycle_count = len(demand_by_period) // period_length
    if cycle_count == 0:
        return {i: 1.0 for i in range(len(demand_by_period))}

    period_totals = [0.0] * period_length
    period_counts = [0] * period_length

    for idx, demand in enumerate(demand_by_period):
        period_idx = idx % period_length
        period_totals[period_idx] += demand
        period_counts[period_idx] += 1

    avg_demand = sum(demand_by_period) / len(demand_by_period)
    indices = {}
    for i in range(period_length):
        if period_counts[i] > 0:
            indices[i] = (period_totals[i] / period_counts[i]) / avg_demand if avg_demand > 0 else 1.0
        else:
            indices[i] = 1.0

    return indices


def calculate_trend(demand_values):
    """
    Simple linear trend calculation using least squares.
    Returns (slope, intercept) tuple.
    """
    if len(demand_values) < 2:
        return 0, sum(demand_values) / len(demand_values) if demand_values else 0

    n = len(demand_values)
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(demand_values) / n

    numerator = sum((x[i] - x_mean) * (demand_values[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

    slope = numerator / denominator if denominator != 0 else 0
    intercept = y_mean - slope * x_mean
    return slope, intercept


def classify_demand_pattern(demand_values):
    """
    Classify demand pattern based on statistical analysis.
    Returns: STABLE, VOLATILE, SEASONAL, TREND_UP, TREND_DOWN, INTERMITTENT, SPORADIC
    """
    if not demand_values:
        return 'NO_HISTORY'

    n = len(demand_values)
    mean = sum(demand_values) / n
    variance = sum((x - mean) ** 2 for x in demand_values) / n
    std_dev = variance ** 0.5
    cv = std_dev / mean if mean > 0 else 0

    if mean == 0:
        return 'ZERO_DEMAND'

    if cv > 1.5:
        return 'VOLATILE'

    zero_count = sum(1 for x in demand_values if x == 0)
    if zero_count > n * 0.4:
        return 'INTERMITTENT'

    if n >= 12:
        seasonal_indices = calculate_seasonal_index(demand_values, 12)
        seasonal_variance = sum((v - 1) ** 2 for v in seasonal_indices.values()) / len(seasonal_indices)
        if seasonal_variance > 0.2:
            return 'SEASONAL'

    slope, _ = calculate_trend(demand_values)
    if slope > mean * 0.05:
        return 'TREND_UP'
    elif slope < -mean * 0.05:
        return 'TREND_DOWN'

    return 'STABLE'


def classify_abc(item_id, db, metric='total_demand_value'):
    """
    Classify items into A/B/C based on Pareto principle.
    A = top 20% items (80% of value/volume)
    B = next 30% items (15% of value/volume)
    C = remaining 50% (5% of value/volume)
    """
    rows = db.execute("""
        SELECT item_id,
               SUM(sales_quantity * COALESCE(
                   (SELECT MAX(unit_cost) FROM wms_item_suppliers WHERE item_id = planning_demand_history.item_id),
                   0)) as demand_value
        FROM planning_demand_history
        WHERE period_start >= DATE('now', '-12 months')
        GROUP BY item_id
        ORDER BY demand_value DESC
    """).fetchall()

    if not rows:
        return {}

    total_value = sum(r['demand_value'] for r in rows)
    if total_value == 0:
        return {r['item_id']: 'C' for r in rows}

    cumulative = 0
    classifications = {}
    for idx, row in enumerate(rows):
        cumulative += row['demand_value']
        percentile = cumulative / total_value
        position = (idx + 1) / len(rows)
        if position <= 0.2:
            classifications[row['item_id']] = 'A'
        elif position <= 0.5:
            classifications[row['item_id']] = 'B'
        else:
            classifications[row['item_id']] = 'C'

    return classifications


def classify_xyz(item_id, db, warehouse_id=None):
    """
    Classify items by demand variability (coefficient of variation).
    X = low variability (CV < 0.2)
    Y = medium variability (CV 0.2 - 0.5)
    Z = high variability (CV > 0.5)
    """
    stats = get_demand_stats(db, item_id, warehouse_id)
    if not stats or stats['avg_demand'] == 0:
        return 'Z'

    cv = stats['cv']
    if cv < 0.2:
        return 'X'
    elif cv < 0.5:
        return 'Y'
    else:
        return 'Z'


# ============================================================
# SAFETY STOCK CALCULATIONS
# ============================================================

def calculate_safety_stock(item_id, db, warehouse_id=None, method='FORMULA'):
    """
    Calculate safety stock using different methods.
    FORMULA: SS = Z * sigma_demand * sqrt(lead_time)
    DAYS_BASED: SS = avg_daily_demand * safety_stock_days
    PERCENTAGE: SS = avg_demand * safety_stock_percent
    """
    stats = get_demand_stats(db, item_id, warehouse_id)
    if not stats:
        return 0

    profile = db.execute(
        "SELECT lead_time_days, safety_stock_days, safety_stock_factor, service_level_target FROM planning_item_profiles WHERE item_id = ?",
        (item_id,)
    ).fetchone()

    if profile:
        lt = profile['lead_time_days'] or 7
        ss_days = profile['safety_stock_days'] or 7
        z = profile['safety_stock_factor'] or 1.65
    else:
        settings = get_planning_settings(db)
        lt = int(settings.get('DEFAULT_LEAD_TIME_DAYS', '7'))
        ss_days = int(settings.get('DEFAULT_SAFETY_STOCK_DAYS', '7'))
        z = 1.65

    if method == 'FORMULA':
        lead_time_demand = stats['avg_demand'] * lt
        ss = z * stats['std_dev'] * (lt ** 0.5)
        return max(ss, stats['avg_demand'] * ss_days / 30)
    elif method == 'DAYS_BASED':
        return stats['avg_demand'] * ss_days
    else:
        return stats['avg_demand'] * ss_days


def calculate_reorder_point(item_id, db, warehouse_id=None):
    """
    Calculate reorder point: ROP = avg_demand_during_lead_time + safety_stock
    """
    stats = get_demand_stats(db, item_id, warehouse_id)
    if not stats:
        return 0

    profile = db.execute(
        "SELECT lead_time_days FROM planning_item_profiles WHERE item_id = ?",
        (item_id,)
    ).fetchone()

    lt = profile['lead_time_days'] if profile else 7
    avg_daily = stats['avg_demand'] / 30 if stats['avg_demand'] > 0 else 0
    safety_stock = calculate_safety_stock(item_id, db, warehouse_id)

    return avg_daily * lt + safety_stock


# ============================================================
# NET REQUIREMENT CALCULATION
# ============================================================

def calculate_net_requirement(item_id, db, warehouse_id=None, company_id=None,
                              forecast_run_id=None, days_ahead=30):
    """
    Core net requirement calculation for an item.

    Net Requirement =
        Forecast Demand (or historical avg)
      + Firm Customer Orders / Reservations
      - Sellable Available Stock
      - Reliable In-Transit Supply

    Returns a dict with all components for transparency.
    """
    from datetime import datetime, timedelta

    settings = get_planning_settings(db)
    today = datetime.now().date()
    horizon = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

    item = db.execute(
        "SELECT * FROM wms_items WHERE id = ?", (item_id,)
    ).fetchone()
    if not item:
        return None

    current_stock = 0
    reserved = 0
    allocated = 0
    blocked = 0

    stock_rows = db.execute("""
        SELECT SUM(quantity) as total_stock,
               SUM(reserved) as reserved,
               SUM(allocated) as allocated,
               SUM(blocked) as blocked
        FROM wms_inventory_balances
        WHERE item_id = ?
    """, (item_id,)).fetchall()

    if stock_rows:
        current_stock = stock_rows[0]['total_stock'] or 0
        reserved = stock_rows[0]['reserved'] or 0
        allocated = stock_rows[0]['allocated'] or 0
        blocked = stock_rows[0]['blocked'] or 0

    sellable = max(0, current_stock - reserved - allocated - blocked)

    in_transit = db.execute("""
        SELECT SUM(quantity - COALESCE(received_quantity, 0)) as in_transit
        FROM wms_inbound_receipts
        WHERE item_id = ?
          AND status IN ('APPROVED', 'IN_TRANSIT', 'RECEIVING')
          AND expected_arrival_date <= ?
    """, (item_id, horizon)).fetchone()['in_transit'] or 0

    open_orders = db.execute("""
        SELECT SUM(ol.ordered_quantity - COALESCE(ol.shipped_quantity, 0)) as open_qty
        FROM wms_dispatch_plans od
        JOIN wms_dispatch_plan_lines ol ON od.id = ol.dispatch_plan_id
        WHERE ol.item_id = ?
          AND od.status IN ('CONFIRMED', 'PICKING', 'PACKING', 'READY')
          AND od.scheduled_date <= ?
    """, (item_id, horizon)).fetchone()['open_qty'] or 0

    open_po = db.execute("""
        SELECT SUM(quantity - COALESCE(received_quantity, 0)) as open_po
        FROM wms_inbound_receipts
        WHERE item_id = ?
          AND status IN ('APPROVED', 'SENT', 'IN_TRANSIT', 'RECEIVING')
    """, (item_id,)).fetchone()['open_po'] or 0

    if forecast_run_id:
        forecast_qty = db.execute("""
            SELECT SUM(final_quantity) as total
            FROM planning_forecast_lines
            WHERE run_id = ? AND item_id = ?
              AND period_start BETWEEN ? AND ?
        """, (forecast_run_id, item_id, today.strftime('%Y-%m-%d'), horizon)).fetchone()['total'] or 0
    else:
        stats = get_demand_stats(db, item_id, warehouse_id)
        forecast_qty = (stats['avg_demand'] / 30 * days_ahead) if stats else 0

    profile = db.execute(
        "SELECT safety_stock FROM planning_item_profiles WHERE item_id = ?",
        (item_id,)
    ).fetchone()
    safety_stock = profile['safety_stock'] if profile else 0

    net_requirement = max(0, forecast_qty + open_orders - sellable - in_transit)

    profile = db.execute(
        "SELECT min_order_quantity, order_multiple FROM planning_item_profiles WHERE item_id = ?",
        (item_id,)
    ).fetchone()
    moq = profile['min_order_quantity'] if profile else 0
    multiple = profile['order_multiple'] if profile else 1

    if moq > 0 and net_requirement < moq and net_requirement > 0:
        recommended_qty = moq
    elif multiple > 1:
        recommended_qty = ((net_requirement / multiple) + 1) * multiple
    else:
        recommended_qty = net_requirement

    days_remaining = 0
    if current_stock > 0 and stats:
        daily_demand = stats['avg_demand'] / 30
        if daily_demand > 0:
            days_remaining = sellable / daily_demand
    elif in_transit > 0:
        days_remaining = 7

    stockout_risk = 'NONE'
    if days_remaining < 3:
        stockout_risk = 'CRITICAL'
    elif days_remaining < 7:
        stockout_risk = 'HIGH'
    elif days_remaining < 14:
        stockout_risk = 'MEDIUM'
    elif days_remaining < 30:
        stockout_risk = 'LOW'

    return {
        'item_id': item_id,
        'warehouse_id': warehouse_id,
        'company_id': company_id,
        'current_stock': current_stock,
        'sellable_stock': sellable,
        'reserved': reserved,
        'allocated': allocated,
        'blocked': blocked,
        'in_transit': in_transit,
        'open_orders': open_orders,
        'open_po': open_po,
        'forecast_demand': forecast_qty,
        'safety_stock': safety_stock,
        'net_requirement': net_requirement,
        'recommended_quantity': recommended_qty,
        'days_of_coverage': days_remaining,
        'stockout_risk': stockout_risk,
        'horizon_days': days_ahead
    }


# ============================================================
# SETTINGS HELPERS
# ============================================================

def get_planning_settings(db, category=None, company_id=None):
    """Get planning settings as a flat dict."""
    query = "SELECT setting_key, setting_value FROM planning_settings WHERE is_active = 1"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if company_id:
        query += " AND (company_id IS NULL OR company_id = ?)"
        params.append(company_id)
    rows = db.execute(query, params).fetchall()
    return {r['setting_key']: r['setting_value'] for r in rows}


def save_planning_setting(db, key, value, category='GENERAL', company_id=None):
    """Upsert a planning setting."""
    existing = db.execute(
        "SELECT id FROM planning_settings WHERE setting_key = ? AND (company_id IS NULL OR company_id = ?)",
        (key, company_id)
    ).fetchone()
    if existing:
        db.execute(
            "UPDATE planning_settings SET setting_value = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (str(value), existing['id'])
        )
    else:
        db.execute(
            "INSERT INTO planning_settings (setting_key, setting_value, setting_type, category, company_id) VALUES (?, ?, ?, ?, ?)",
            (key, str(value), 'STRING', category, company_id)
        )
    db.commit()


# ============================================================
# ALERT HELPERS
# ============================================================

def create_planning_alert(db, alert_type, severity, title, message,
                           item_id=None, warehouse_id=None, company_id=None,
                           supplier_id=None, customer_id=None,
                           recommendation_id=None, scenario_id=None):
    """Create a new planning alert."""
    db.execute("""
        INSERT INTO planning_alerts
        (alert_type, severity, title, message, item_id, warehouse_id, company_id,
         supplier_id, customer_id, recommendation_id, scenario_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (alert_type, severity, title, message, item_id, warehouse_id, company_id,
          supplier_id, customer_id, recommendation_id, scenario_id))
    db.commit()


def generate_planning_alerts(db):
    """Scan inventory and generate proactive planning alerts."""
    from datetime import datetime, timedelta

    settings = get_planning_settings(db)
    stockout_days = int(settings.get('STOCKOUT_ALERT_THRESHOLD_DAYS', '7'))
    low_stock_pct = float(settings.get('LOW_STOCK_ALERT_PERCENT', '20')) / 100
    dead_days = int(settings.get('DEAD_STOCK_DAYS', '365'))
    slow_days = int(settings.get('SLOW_MOVING_DAYS', '180'))

    items = db.execute("""
        SELECT i.id, i.item_code, i.name, i.min_stock_level, i.reorder_point,
               i.safety_stock, ib.quantity
        FROM wms_items i
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        WHERE i.is_active = 1
    """).fetchall()

    today = datetime.now().date()
    cutoff = (today - timedelta(days=dead_days)).strftime('%Y-%m-%d')
    slow_cutoff = (today - timedelta(days=slow_days)).strftime('%Y-%m-%d')

    for item in items:
        if item['quantity'] is None:
            item_qty = 0
        else:
            item_qty = item['quantity']

        rop = item['reorder_point'] or 0
        ss = item['safety_stock'] or 0
        min_stock = item['min_stock_level'] or 0

        if item_qty <= 0:
            existing = db.execute(
                "SELECT id FROM planning_alerts WHERE item_id = ? AND alert_type = 'STOCKOUT' AND is_acknowledged = 0",
                (item['id'],)
            ).fetchone()
            if not existing:
                create_planning_alert(db, 'STOCKOUT', 'CRITICAL',
                    f"Stockout: {item['item_code']}",
                    f"Item {item['item_code']} - {item['name']} has zero stock.",
                    item_id=item['id'])
        elif item_qty < ss:
            existing = db.execute(
                "SELECT id FROM planning_alerts WHERE item_id = ? AND alert_type = 'SAFETY_STOCK_BREACH' AND is_acknowledged = 0",
                (item['id'],)
            ).fetchone()
            if not existing:
                create_planning_alert(db, 'SAFETY_STOCK_BREACH', 'HIGH',
                    f"Below Safety Stock: {item['item_code']}",
                    f"Item {item['item_code']} stock ({item_qty}) is below safety stock ({ss}).",
                    item_id=item['id'])
        elif item_qty < rop:
            existing = db.execute(
                "SELECT id FROM planning_alerts WHERE item_id = ? AND alert_type = 'REORDER_POINT_BREACH' AND is_acknowledged = 0",
                (item['id'],)
            ).fetchone()
            if not existing:
                create_planning_alert(db, 'REORDER_POINT_BREACH', 'MEDIUM',
                    f"Below Reorder Point: {item['item_code']}",
                    f"Item {item['item_code']} stock ({item_qty}) is below reorder point ({rop}).",
                    item_id=item['id'])

        has_recent_movement = db.execute("""
            SELECT 1 FROM wms_inventory_ledger
            WHERE item_id = ? AND created_at >= ?
            LIMIT 1
        """, (item['id'], slow_cutoff)).fetchone()

        if not has_recent_movement and item_qty > 0:
            existing = db.execute(
                "SELECT id FROM planning_alerts WHERE item_id = ? AND alert_type = 'DEAD_STOCK' AND is_acknowledged = 0",
                (item['id'],)
            ).fetchone()
            if not existing:
                create_planning_alert(db, 'DEAD_STOCK', 'MEDIUM',
                    f"Dead Stock: {item['item_code']}",
                    f"Item {item['item_code']} has no movement in {slow_days}+ days.",
                    item_id=item['id'])


# ============================================================
# AUDIT LOG HELPERS
# ============================================================

def log_planning_action(db, action_type, entity_type, entity_id=None,
                         item_id=None, warehouse_id=None, company_id=None,
                         user_id=None, changes=None, notes=None):
    """Log a planning action to the audit trail."""
    changes_json = json.dumps(changes) if changes else None
    db.execute("""
        INSERT INTO planning_audit_log
        (action_type, entity_type, entity_id, item_id, warehouse_id, company_id,
         user_id, changes_json, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (action_type, entity_type, entity_id, item_id, warehouse_id, company_id,
          user_id, changes_json, notes))
    db.commit()


# ============================================================
# KPI CALCULATION HELPERS
# ============================================================

def calculate_kpi_fill_rate(db, company_id=None, warehouse_id=None, days=30):
    """Calculate fill rate: % of orders fulfilled completely from stock."""
    from datetime import datetime, timedelta

    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    query = """
        SELECT SUM(ordered_quantity) as total_ordered,
               SUM(shipped_quantity) as total_shipped
        FROM wms_dispatch_plan_lines dl
        JOIN wms_dispatch_plans d ON dl.dispatch_plan_id = d.id
        WHERE d.created_at >= ?
    """
    params = [cutoff]

    if company_id:
        query += " AND d.company_id = ?"
        params.append(company_id)
    if warehouse_id:
        query += " AND d.warehouse_id = ?"
        params.append(warehouse_id)

    row = db.execute(query, params).fetchone()
    if not row or row['total_ordered'] == 0:
        return 1.0

    return min(1.0, (row['total_shipped'] or 0) / row['total_ordered'])


def calculate_kpi_service_level(db, company_id=None, days=30):
    """Calculate service level: % of demand met from stock."""
    from datetime import datetime, timedelta

    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    total_demand = db.execute("""
        SELECT SUM(sales_quantity + consumption_quantity) as total
        FROM planning_demand_history
        WHERE period_start >= ?
    """, (cutoff,)).fetchone()['total'] or 0

    fulfilled = db.execute("""
        SELECT SUM(quantity) as total
        FROM wms_inventory_ledger
        WHERE created_at >= ? AND transaction_type IN ('SALE', 'DISPATCH')
    """, (cutoff,)).fetchone()['total'] or 0

    if total_demand == 0:
        return 1.0

    return min(1.0, fulfilled / total_demand)


def calculate_kpi_stockout_rate(db, days=30):
    """Calculate stockout rate: % of items that experienced stockout."""
    from datetime import datetime, timedelta

    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    total_item_days = db.execute("""
        SELECT COUNT(DISTINCT item_id) as count FROM planning_demand_history
        WHERE period_start >= ?
    """, (cutoff,)).fetchone()['count'] or 0

    stockout_items = db.execute("""
        SELECT COUNT(DISTINCT item_id) as count FROM planning_alerts
        WHERE created_at >= ? AND alert_type = 'STOCKOUT' AND is_acknowledged = 0
    """, (cutoff,)).fetchone()['count'] or 0

    if total_item_days == 0:
        return 0.0

    return stockout_items / total_item_days


def calculate_kpi_days_of_inventory(db, company_id=None, warehouse_id=None):
    """Calculate average days of inventory across items."""
    query = """
        SELECT SUM(ib.quantity) as total_stock,
               SUM(pd.avg_demand / 30) as total_daily_demand
        FROM wms_inventory_balances ib
        JOIN wms_items i ON ib.item_id = i.id
        LEFT JOIN (
            SELECT item_id, AVG(sales_quantity + consumption_quantity) / 30 as avg_demand
            FROM planning_demand_history
            WHERE period_start >= DATE('now', '-12 months')
            GROUP BY item_id
        ) pd ON ib.item_id = pd.item_id
        WHERE 1=1
    """
    params = []
    if company_id:
        query += " AND ib.company_id = ?"
        params.append(company_id)
    if warehouse_id:
        query += " AND ib.warehouse_id = ?"
        params.append(warehouse_id)

    row = db.execute(query, params).fetchone()
    stock = row['total_stock'] or 0
    daily = row['total_daily_demand'] or 0

    if daily == 0:
        return float('inf') if stock > 0 else 0

    return stock / daily


def snapshot_kpis(db, period_type='DAILY', company_id=None, warehouse_id=None):
    """Take a snapshot of current KPIs."""
    from datetime import datetime, timedelta

    today = datetime.now().date().strftime('%Y-%m-%d')

    kpis = [
        ('FILL_RATE', calculate_kpi_fill_rate(db, company_id, warehouse_id)),
        ('SERVICE_LEVEL', calculate_kpi_service_level(db, company_id)),
        ('STOCKOUT_RATE', calculate_kpi_stockout_rate(db)),
        ('AVG_DAYS_OF_INVENTORY', calculate_kpi_days_of_inventory(db, company_id, warehouse_id)),
    ]

    for kpi_name, value in kpis:
        db.execute("""
            INSERT INTO planning_kpi_records
            (kpi_name, period_type, period_start, company_id, warehouse_id, value)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(kpi_name, period_type, period_start, company_id, warehouse_id, item_id)
            DO UPDATE SET value = excluded.value
        """, (kpi_name, period_type, today, company_id, warehouse_id, value))

    db.commit()


# ============================================================
# ENTERPRISE STATISTICAL FORECASTING ENGINE
# ============================================================

def calculate_exponential_smoothing(demand_values, alpha=0.3):
    """
    Simple exponential smoothing.
    S_t = alpha * Y_t + (1 - alpha) * S_{t-1}
    """
    if not demand_values:
        return 0
    forecast = demand_values[0]
    for value in demand_values[1:]:
        forecast = alpha * value + (1 - alpha) * forecast
    return forecast


def calculate_double_exponential_smoothing(demand_values, alpha=0.3, beta=0.1):
    """
    Double exponential smoothing (Holt's method) for trend data.
    Level: S_t = alpha * Y_t + (1 - alpha) * (S_{t-1} + b_{t-1})
    Trend: b_t = beta * (S_t - S_{t-1}) + (1 - beta) * b_{t-1}
    Forecast: F_t+h = S_t + h * b_t
    """
    if not demand_values:
        return 0, 0
    if len(demand_values) < 2:
        return demand_values[0], 0

    n = len(demand_values)
    s = [0] * n
    b = [0] * n

    s[0] = demand_values[0]
    b[0] = demand_values[1] - demand_values[0] if n > 1 else 0

    for t in range(1, n):
        s[t] = alpha * demand_values[t] + (1 - alpha) * (s[t-1] + b[t-1])
        b[t] = beta * (s[t] - s[t-1]) + (1 - beta) * b[t-1]

    final_level = s[-1]
    final_trend = b[-1]
    return final_level, final_trend


def calculate_triple_exponential_smoothing(demand_values, alpha=0.3, beta=0.1, gamma=0.1, period=12):
    """
    Triple exponential smoothing (Holt-Winters) for seasonal data.
    Requires at least 2 complete seasonal periods.
    Returns (forecast, seasonal_indices)
    """
    if not demand_values or len(demand_values) < period * 2:
        return calculate_exponential_smoothing(demand_values, alpha), None

    n = len(demand_values)
    s = [0] * n
    b = [0] * n
    c = [0] * n

    avg_period = sum(demand_values[:period]) / period
    for j in range(period):
        c[j] = demand_values[j] / avg_period if avg_period > 0 else 1

    b[0] = sum([demand_values[period + i] - demand_values[i] for i in range(period)]) / (period * period)
    s[0] = demand_values[0] / c[0] if c[0] != 0 else demand_values[0]

    for t in range(1, n):
        s[t] = alpha * (demand_values[t] / c[t - period]) + (1 - alpha) * (s[t-1] + b[t-1])
        b[t] = beta * (s[t] - s[t-1]) + (1 - beta) * b[t-1]
        c[t] = gamma * (demand_values[t] / s[t]) + (1 - gamma) * c[t - period] if t >= period else c[t % period]

    final_level = s[-1]
    final_trend = b[-1]
    seasonal_indices = c[-(period):]

    forecast = final_level + final_trend
    avg_seasonal = sum(seasonal_indices) / len(seasonal_indices) if seasonal_indices else 1
    forecast = forecast * (avg_seasonal if avg_seasonal > 0 else 1)

    return forecast, seasonal_indices


def calculate_forecast_with_seasonality(demand_values, seasonal_indices, horizon=30):
    """
    Generate forecasts incorporating seasonal indices.
    """
    if not demand_values or not seasonal_indices:
        return [calculate_moving_average(demand_values) for _ in range(horizon)]

    forecasts = []
    base_forecast, trend = calculate_double_exponential_smoothing(demand_values)

    for h in range(horizon):
        period_idx = h % len(seasonal_indices)
        seasonal_factor = seasonal_indices[period_idx]
        forecasts.append(base_forecast + trend * h * seasonal_factor)

    return forecasts


def calculate_weighted_moving_average_v2(demand_values, weights):
    """
    Weighted moving average with configurable weights.
    Weights should sum to 1.0.
    """
    if not demand_values:
        return 0
    n = min(len(demand_values), len(weights))
    if n == 0:
        return 0
    relevant_demand = demand_values[-n:]
    relevant_weights = weights[-n:]
    total_weight = sum(relevant_weights)
    if total_weight == 0:
        return 0
    return sum(v * w for v, w in zip(relevant_demand, relevant_weights)) / total_weight


def calculate_regression_forecast(demand_values):
    """
    Simple linear regression forecast.
    Returns (slope, intercept, forecast_value).
    """
    if len(demand_values) < 2:
        return 0, sum(demand_values) / len(demand_values) if demand_values else 0, sum(demand_values) / len(demand_values) if demand_values else 0

    n = len(demand_values)
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(demand_values) / n

    numerator = sum((x[i] - x_mean) * (demand_values[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

    slope = numerator / denominator if denominator != 0 else 0
    intercept = y_mean - slope * x_mean

    next_x = n
    forecast = slope * next_x + intercept

    return slope, intercept, forecast


def auto_select_forecast_method(demand_values):
    """
    Automatically select the best forecasting method based on data characteristics.
    Returns the method name and parameters.
    """
    if not demand_values or len(demand_values) < 3:
        return 'MOVING_AVERAGE', {'window': 3}

    pattern = classify_demand_pattern(demand_values)

    if pattern == 'INTERMITTENT' or pattern == 'SPORADIC':
        return 'MOVING_AVERAGE', {'window': min(6, len(demand_values))}

    if pattern == 'SEASONAL':
        return 'HOLT_WINTERS', {'period': 12}

    if pattern == 'TREND_UP' or pattern == 'TREND_DOWN':
        return 'DOUBLE_EXPONENTIAL', {'alpha': 0.3, 'beta': 0.1}

    if pattern == 'VOLATILE':
        return 'WEIGHTED_MOVING_AVERAGE', {'weights': [0.5, 0.3, 0.2]}

    cv = 0
    mean = sum(demand_values) / len(demand_values)
    if mean > 0:
        variance = sum((x - mean) ** 2 for x in demand_values) / len(demand_values)
        std_dev = math.sqrt(variance)
        cv = std_dev / mean

    if cv < 0.2:
        return 'EXPONENTIAL_SMOOTHING', {'alpha': 0.3}

    return 'MOVING_AVERAGE', {'window': min(3, len(demand_values))}


# ============================================================
# ENTERPRISE FORECAST ACCURACY CALCULATION ENGINE
# ============================================================

def calculate_mape(actual, forecast):
    """Mean Absolute Percentage Error."""
    if not actual or actual == 0:
        return None
    return abs((actual - forecast) / actual) * 100


def calculate_wape(actual_values, forecast_values):
    """
    Weighted Absolute Percentage Error.
    WAPE = sum(|actual - forecast|) / sum(|actual|)
    """
    total_actual = sum(abs(a) for a in actual_values)
    if total_actual == 0:
        return None
    total_error = sum(abs(a - f) for a, f in zip(actual_values, forecast_values))
    return (total_error / total_actual) * 100


def calculate_mae(actual_values, forecast_values):
    """Mean Absolute Error."""
    if not actual_values:
        return None
    return sum(abs(a - f) for a, f in zip(actual_values, forecast_values)) / len(actual_values)


def calculate_rmse(actual_values, forecast_values):
    """Root Mean Square Error."""
    if not actual_values:
        return None
    mse = sum((a - f) ** 2 for a, f in zip(actual_values, forecast_values)) / len(actual_values)
    return math.sqrt(mse)


def calculate_bias(actual_values, forecast_values):
    """
    Forecast bias: positive = over-forecast, negative = under-forecast.
    Bias = sum(forecast - actual) / sum(actual) * 100
    """
    total_actual = sum(actual_values)
    if total_actual == 0:
        return None
    total_bias = sum(f - a for a, f in zip(actual_values, forecast_values))
    return (total_bias / total_actual) * 100


def calculate_tracking_signal(actual_values, forecast_values):
    """
    Tracking Signal = sum(forecast - actual) / MAD
    where MAD = Mean Absolute Deviation.
    """
    if not actual_values:
        return None

    errors = [f - a for a, f in zip(actual_values, forecast_values)]
    cumulative_error = sum(errors)
    mad = sum(abs(e) for e in errors) / len(errors)

    if mad == 0:
        return None

    return cumulative_error / mad


def calculate_theil_u(actual_values, forecast_values):
    """
    Theil's U statistic for forecast accuracy comparison.
    U < 1: Forecast is better than naive.
    U = 1: Forecast is equal to naive.
    U > 1: Forecast is worse than naive.
    """
    if not actual_values or len(actual_values) < 2:
        return None

    n = len(actual_values)
    forecast_error_sum = sum((actual_values[t] - forecast_values[t]) ** 2 for t in range(n))
    naive_error_sum = sum((actual_values[t] - actual_values[t-1]) ** 2 for t in range(1, n))

    if naive_error_sum == 0:
        return None

    return math.sqrt(forecast_error_sum / naive_error_sum)


def calculate_forecast_accuracy_metrics(db, item_id, version_id=None, warehouse_id=None,
                                         start_date=None, end_date=None):
    """
    Calculate comprehensive accuracy metrics for an item's forecast vs actual.
    Returns dict with MAPE, WAPE, MAE, RMSE, Bias, Tracking Signal, Theil U.
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')

    query = """
        SELECT
            fl.period_start,
            fl.final_quantity as forecast_qty,
            COALESCE(dh.sales_quantity + dh.consumption_quantity, 0) as actual_qty
        FROM planning_forecast_lines fl
        LEFT JOIN planning_demand_history dh
            ON fl.item_id = dh.item_id
            AND fl.period_start = dh.period_start
            AND fl.warehouse_id = dh.warehouse_id
        WHERE fl.item_id = ?
          AND fl.period_start BETWEEN ? AND ?
    """
    params = [item_id, start_date, end_date]

    if version_id:
        query += " AND fl.run_id = ?"
        params.append(version_id)

    if warehouse_id:
        query += " AND fl.warehouse_id = ?"
        params.append(warehouse_id)

    query += " ORDER BY fl.period_start"

    rows = db.execute(query, params).fetchall()

    if not rows:
        return None

    actual_values = [r['actual_qty'] for r in rows]
    forecast_values = [r['forecast_qty'] for r in rows]

    metrics = {
        'mape': calculate_mape(sum(actual_values), sum(forecast_values)),
        'wape': calculate_wape(actual_values, forecast_values),
        'mae': calculate_mae(actual_values, forecast_values),
        'rmse': calculate_rmse(actual_values, forecast_values),
        'bias': calculate_bias(actual_values, forecast_values),
        'tracking_signal': calculate_tracking_signal(actual_values, forecast_values),
        'theil_u': calculate_theil_u(actual_values, forecast_values),
        'data_points': len(rows)
    }

    return metrics


def calculate_item_forecast_accuracy(db, item_id, company_id=None, warehouse_id=None):
    """
    Calculate forecast accuracy for an item across all recent periods.
    Stores results in planning_forecast_accuracy table.
    """
    today = datetime.now().date()
    start_date = (today - timedelta(days=90)).strftime('%Y-%m-%d')

    rows = db.execute("""
        SELECT
            fl.period_start,
            fl.warehouse_id,
            fl.final_quantity as forecast_qty,
            COALESCE(dh.sales_quantity + dh.consumption_quantity, 0) as actual_qty
        FROM planning_forecast_lines fl
        LEFT JOIN planning_demand_history dh
            ON fl.item_id = dh.item_id
            AND fl.period_start = dh.period_start
            AND fl.warehouse_id = dh.warehouse_id
        WHERE fl.item_id = ?
          AND fl.period_start BETWEEN ? AND ?
          AND fl.is_frozen = 0
        ORDER BY fl.period_start
    """, (item_id, start_date, today.strftime('%Y-%m-%d'))).fetchall()

    for row in rows:
        actual = row['actual_qty']
        forecast = row['forecast_qty']
        error = forecast - actual
        abs_error = abs(error)

        mape = None
        if actual != 0:
            mape = (abs_error / actual) * 100

        db.execute("""
            INSERT INTO planning_forecast_accuracy
            (item_id, warehouse_id, company_id, period_start, period_type,
             forecast_quantity, actual_quantity, error_quantity, absolute_error,
             percent_error, absolute_percent_error, mape)
            VALUES (?, ?, ?, ?, 'daily', ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT DO NOTHING
        """, (item_id, row['warehouse_id'], company_id, row['period_start'],
              forecast, actual, error, abs_error, error/actual*100 if actual != 0 else None,
              mape, mape))


def calculate_forecast_bias_by_planner(db, planner_id=None, company_id=None, period_start=None):
    """
    Calculate forecast bias grouped by planner or overall.
    """
    if not period_start:
        period_start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    query = """
        SELECT
            fl.item_id,
            fl.warehouse_id,
            r.created_by as planner_id,
            SUM(fl.final_quantity) as total_forecast,
            COALESCE(SUM(dh.sales_quantity + dh.consumption_quantity), 0) as total_actual
        FROM planning_forecast_lines fl
        JOIN planning_forecast_runs r ON fl.run_id = r.id
        LEFT JOIN planning_demand_history dh
            ON fl.item_id = dh.item_id
            AND fl.period_start = dh.period_start
        WHERE fl.period_start >= ?
    """
    params = [period_start]

    if planner_id:
        query += " AND r.created_by = ?"
        params.append(planner_id)

    if company_id:
        query += " AND fl.company_id = ?"
        params.append(company_id)

    query += " GROUP BY fl.item_id, fl.warehouse_id, r.created_by"

    rows = db.execute(query, params).fetchall()

    for row in rows:
        forecast = row['total_forecast']
        actual = row['total_actual']
        bias_amount = forecast - actual
        bias_percent = (bias_amount / actual * 100) if actual != 0 else 0

        db.execute("""
            INSERT INTO planning_forecast_bias
            (item_id, warehouse_id, planner_id, period_type, period_start,
             total_forecast, total_actual, bias_amount, bias_percent)
            VALUES (?, ?, ?, 'monthly', ?, ?, ?, ?, ?)
        """, (row['item_id'], row['warehouse_id'], row['planner_id'],
              period_start, forecast, actual, bias_amount, bias_percent))

    db.commit()


# ============================================================
# ENTERPRISE FORECAST VERSION MANAGEMENT
# ============================================================

def create_forecast_version(db, version_name, forecast_run_id=None, created_by=None,
                            company_id=None, branch_id=None, description=None,
                            is_baseline=False, parent_version_id=None):
    """
    Create a new forecast version snapshot.
    """
    existing_count = db.execute("""
        SELECT COUNT(*) as cnt FROM planning_forecast_versions
        WHERE forecast_run_id = ?
    """, (forecast_run_id,)).fetchone()['cnt']

    version_number = existing_count + 1

    cursor = db.execute("""
        INSERT INTO planning_forecast_versions
        (version_name, version_number, description, status, forecast_run_id,
         is_baseline, parent_version_id, created_by, company_id, branch_id)
        VALUES (?, ?, ?, 'DRAFT', ?, ?, ?, ?, ?, ?)
    """, (version_name, version_number, description, forecast_run_id,
          1 if is_baseline else 0, parent_version_id, created_by, company_id, branch_id))

    version_id = cursor.lastrowid

    if forecast_run_id:
        db.execute("""
            INSERT INTO planning_forecast_version_lines
            (version_id, item_id, warehouse_id, company_id, branch_id,
             period_start, period_type, baseline_quantity, final_quantity)
            SELECT ?, item_id, warehouse_id, company_id, branch_id,
                   period_start, period_type, base_quantity, final_quantity
            FROM planning_forecast_lines
            WHERE run_id = ?
        """, (version_id, forecast_run_id))

        db.execute("""
            UPDATE planning_forecast_versions
            SET total_items = (SELECT COUNT(DISTINCT item_id) FROM planning_forecast_version_lines WHERE version_id = ?),
                total_quantity = (SELECT SUM(final_quantity) FROM planning_forecast_version_lines WHERE version_id = ?)
            WHERE id = ?
        """, (version_id, version_id, version_id))

    db.commit()
    return version_id


def clone_forecast_version(db, version_id, new_name, created_by=None):
    """
    Clone an existing forecast version.
    """
    original = db.execute("SELECT * FROM planning_forecast_versions WHERE id = ?",
                          (version_id,)).fetchone()
    if not original:
        return None

    new_version_id = create_forecast_version(
        db, new_name, original['forecast_run_id'], created_by,
        original['company_id'], original['branch_id'],
        f"Cloned from version {original['version_name']} (v{original['version_number']})",
        parent_version_id=version_id
    )

    return new_version_id


def freeze_forecast_version(db, version_id, user_id=None):
    """
    Freeze a forecast version (make it immutable).
    """
    db.execute("""
        UPDATE planning_forecast_versions
        SET status = 'FROZEN',
            is_frozen = 1,
            published_at = CURRENT_TIMESTAMP,
            published_by = ?
        WHERE id = ?
    """, (user_id, version_id))

    db.execute("""
        UPDATE planning_forecast_version_lines
        SET is_frozen = 1
        WHERE version_id = ?
    """, (version_id,))

    db.commit()


def publish_forecast_version(db, version_id, user_id=None):
    """
    Publish a forecast version for wider use.
    """
    db.execute("""
        UPDATE planning_forecast_versions
        SET status = 'PUBLISHED',
            published_at = CURRENT_TIMESTAMP,
            published_by = ?
        WHERE id = ?
    """, (user_id, version_id))
    db.commit()


def compare_forecast_versions(db, version_id_1, version_id_2):
    """
    Compare two forecast versions and return differences.
    """
    comparison = db.execute("""
        SELECT
            v1.item_id,
            i.item_code,
            i.name as item_name,
            v1.warehouse_id,
            v1.period_start,
            v1.final_quantity as quantity_v1,
            v2.final_quantity as quantity_v2,
            v2.final_quantity - v1.final_quantity as difference,
            CASE WHEN v1.final_quantity != 0
                 THEN ((v2.final_quantity - v1.final_quantity) / v1.final_quantity * 100)
                 ELSE NULL END as pct_difference
        FROM planning_forecast_version_lines v1
        JOIN planning_forecast_version_lines v2
            ON v1.item_id = v2.item_id
            AND v1.warehouse_id = v2.warehouse_id
            AND v1.period_start = v2.period_start
            AND v2.version_id = ?
        JOIN wms_items i ON v1.item_id = i.id
        WHERE v1.version_id = ?
        ORDER BY ABS(v2.final_quantity - v1.final_quantity) DESC
    """, (version_id_2, version_id_1)).fetchall()

    return comparison


# ============================================================
# ENTERPRISE CONSENSUS PLANNING
# ============================================================

def create_consensus_forecast(db, version_id, item_id, period_start,
                               sales_input=None, planner_input=None, marketing_input=None,
                               created_by=None, company_id=None, branch_id=None):
    """
    Create or update a consensus forecast entry with multiple inputs.
    """
    consensus_value = None
    disagreement_level = 'LOW'

    inputs = [sales_input, planner_input, marketing_input]
    valid_inputs = [i for i in inputs if i is not None]

    if valid_inputs:
        consensus_value = sum(valid_inputs) / len(valid_inputs)

        if len(valid_inputs) >= 2:
            max_diff = max(valid_inputs) - min(valid_inputs)
            avg_val = sum(valid_inputs) / len(valid_inputs)
            if avg_val > 0:
                diff_pct = max_diff / avg_val
                if diff_pct > 0.5:
                    disagreement_level = 'HIGH'
                elif diff_pct > 0.2:
                    disagreement_level = 'MEDIUM'

    cursor = db.execute("""
        INSERT INTO planning_consensus_forecasts
        (version_id, item_id, period_start, sales_input, planner_input, marketing_input,
         consensus_value, status, disagreement_level, created_by, company_id, branch_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'DRAFT', ?, ?, ?, ?)
    """, (version_id, item_id, period_start, sales_input, planner_input, marketing_input,
          consensus_value, disagreement_level, created_by, company_id, branch_id))

    db.commit()
    return cursor.lastrowid


def add_consensus_comment(db, consensus_id, user_id, comment_text,
                           user_role=None, is_internal=True, parent_comment_id=None):
    """
    Add a comment to a consensus forecast entry.
    """
    cursor = db.execute("""
        INSERT INTO planning_consensus_comments
        (consensus_id, user_id, user_role, comment_text, is_internal, parent_comment_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (consensus_id, user_id, user_role, comment_text, 1 if is_internal else 0, parent_comment_id))
    db.commit()
    return cursor.lastrowid


def resolve_consensus_disagreement(db, consensus_id, final_value, user_id):
    """
    Resolve a disagreement in consensus forecast by setting final approved value.
    """
    db.execute("""
        UPDATE planning_consensus_forecasts
        SET final_approved_value = ?,
            status = 'APPROVED'
        WHERE id = ?
    """, (final_value, consensus_id))

    add_consensus_comment(db, consensus_id, user_id,
                          f"Disagreement resolved. Final value set to {final_value}.",
                          user_role='SYSTEM', is_internal=False)

    db.commit()


# ============================================================
# ENTERPRISE DEMAND DRIVERS & CAUSAL FACTORS
# ============================================================

def create_demand_driver(db, driver_name, driver_type, impact_factor=1.0,
                         start_date=None, end_date=None, item_id=None,
                         brand_id=None, category_id=None, company_id=None,
                         created_by=None, description=None):
    """
    Register a demand driver (promotion, event, season, etc.).
    """
    cursor = db.execute("""
        INSERT INTO planning_demand_drivers
        (driver_name, driver_type, description, impact_factor, start_date, end_date,
         item_id, brand_id, category_id, company_id, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (driver_name, driver_type, description, impact_factor, start_date, end_date,
          item_id, brand_id, category_id, company_id, created_by))
    db.commit()
    return cursor.lastrowid


def create_promotion_record(db, promotion_name, promotion_type, start_date, end_date,
                             expected_uplift_percent=0, item_id=None, brand_id=None,
                             category_id=None, warehouse_id=None, company_id=None,
                             created_by=None, budget_allocated=None):
    """
    Create a promotion impact record.
    """
    cursor = db.execute("""
        INSERT INTO planning_promotion_impact
        (promotion_name, promotion_type, item_id, brand_id, category_id,
         warehouse_id, company_id, start_date, end_date,
         expected_uplift_percent, budget_allocated, status, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PLANNED', ?)
    """, (promotion_name, promotion_type, item_id, brand_id, category_id,
          warehouse_id, company_id, start_date, end_date,
          expected_uplift_percent, budget_allocated, created_by))
    db.commit()
    return cursor.lastrowid


def update_promotion_actual_impact(db, promotion_id, actual_uplift_percent,
                                    actual_additional_demand=None, budget_spent=None):
    """
    Update promotion record with actual measured impact.
    """
    db.execute("""
        UPDATE planning_promotion_impact
        SET actual_uplift_percent = ?,
            actual_additional_demand = ?,
            budget_spent = ?,
            status = 'COMPLETED',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (actual_uplift_percent, actual_additional_demand, budget_spent, promotion_id))
    db.commit()


def apply_promotion_impact_to_forecast(db, promotion_id, forecast_run_id):
    """
    Apply promotion uplift to forecast lines for the promotion period.
    """
    promotion = db.execute("SELECT * FROM planning_promotion_impact WHERE id = ?",
                           (promotion_id,)).fetchone()
    if not promotion:
        return

    uplift_factor = 1 + (promotion['expected_uplift_percent'] / 100)

    query = """
        UPDATE planning_forecast_lines
        SET override_quantity = final_quantity * ?,
            notes = COALESCE(notes, '') || ' [Promotion: {name}]'
        WHERE run_id = ?
          AND period_start BETWEEN ? AND ?
    """
    params = [uplift_factor, forecast_run_id, promotion['start_date'], promotion['end_date']]

    if promotion['item_id']:
        query += " AND item_id = ?"
        params.append(promotion['item_id'])
    if promotion['brand_id']:
        query += " AND item_id IN (SELECT id FROM wms_items WHERE brand_id = ?)"
        params.append(promotion['brand_id'])
    if promotion['category_id']:
        query += " AND item_id IN (SELECT id FROM wms_items WHERE category_id = ?)"
        params.append(promotion['category_id'])

    db.execute(query, params)
    db.commit()


def create_seasonality_profile(db, profile_name, item_id=None, brand_id=None,
                                 category_id=None, company_id=None,
                                 monthly_factors=None):
    """
    Create a seasonality profile with monthly factors.
    monthly_factors: dict with keys 'jan' through 'dec' (or list of 12 values).
    """
    if monthly_factors is None:
        monthly_factors = {m: 1.0 for m in ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                                              'jul', 'aug', 'sep', 'oct', 'nov', 'dec']}
    elif isinstance(monthly_factors, (list, tuple)) and len(monthly_factors) == 12:
        monthly_factors = {
            'jan': monthly_factors[0], 'feb': monthly_factors[1], 'mar': monthly_factors[2],
            'apr': monthly_factors[3], 'may': monthly_factors[4], 'jun': monthly_factors[5],
            'jul': monthly_factors[6], 'aug': monthly_factors[7], 'sep': monthly_factors[8],
            'oct': monthly_factors[9], 'nov': monthly_factors[10], 'dec': monthly_factors[11]
        }

    cursor = db.execute("""
        INSERT INTO planning_seasonality_profiles
        (profile_name, item_id, brand_id, category_id, company_id,
         jan_factor, feb_factor, mar_factor, apr_factor, may_factor, jun_factor,
         jul_factor, aug_factor, sep_factor, oct_factor, nov_factor, dec_factor)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (profile_name, item_id, brand_id, category_id, company_id,
          monthly_factors.get('jan', 1.0), monthly_factors.get('feb', 1.0),
          monthly_factors.get('mar', 1.0), monthly_factors.get('apr', 1.0),
          monthly_factors.get('may', 1.0), monthly_factors.get('jun', 1.0),
          monthly_factors.get('jul', 1.0), monthly_factors.get('aug', 1.0),
          monthly_factors.get('sep', 1.0), monthly_factors.get('oct', 1.0),
          monthly_factors.get('nov', 1.0), monthly_factors.get('dec', 1.0)))
    db.commit()
    return cursor.lastrowid


def calculate_seasonal_factors_from_history(demand_history, period_length=12):
    """
    Calculate seasonal factors from historical demand data.
    Returns a dict of month_index -> seasonal_factor.
    """
    if len(demand_history) < period_length * 2:
        return {i: 1.0 for i in range(12)}

    cycle_count = len(demand_history) // period_length
    if cycle_count == 0:
        return {i: 1.0 for i in range(len(demand_history))}

    period_totals = [0.0] * period_length
    period_counts = [0] * period_length

    for idx, demand in enumerate(demand_history):
        period_idx = idx % period_length
        period_totals[period_idx] += demand
        period_counts[period_idx] += 1

    avg_demand = sum(demand_history) / len(demand_history)
    factors = {}
    for i in range(period_length):
        if period_counts[i] > 0:
            factors[i] = (period_totals[i] / period_counts[i]) / avg_demand if avg_demand > 0 else 1.0
        else:
            factors[i] = 1.0

    return factors


# ============================================================
# ENTERPRISE DEMAND SENSING SCAFFOLD
# ============================================================

def record_demand_signal(db, item_id, signal_type, signal_value, signal_direction,
                          signal_date=None, warehouse_id=None, company_id=None,
                          volatility_score=None, anomaly_score=None,
                          signal_source=None, notes=None):
    """
    Record a demand signal for short-term demand sensing.
    """
    if signal_date is None:
        signal_date = datetime.now().date().strftime('%Y-%m-%d')

    cursor = db.execute("""
        INSERT INTO planning_demand_signals
        (item_id, warehouse_id, company_id, signal_type, signal_source,
         signal_value, signal_direction, volatility_score, anomaly_score,
         signal_date, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (item_id, warehouse_id, company_id, signal_type, signal_source,
          signal_value, signal_direction, volatility_score, anomaly_score,
          signal_date, notes))
    db.commit()
    return cursor.lastrowid


def detect_demand_volatility(db, item_id, warehouse_id=None, window=7, threshold_cv=0.5):
    """
    Detect high demand volatility for an item using coefficient of variation.
    Returns volatility alert if CV exceeds threshold.
    """
    start_date = (datetime.now() - timedelta(days=window)).strftime('%Y-%m-%d')

    rows = db.execute("""
        SELECT sales_quantity + consumption_quantity as demand
        FROM planning_demand_history
        WHERE item_id = ? AND period_start >= ?
    """, (item_id, start_date)).fetchall()

    if not rows or len(rows) < 3:
        return None

    demand_values = [r['demand'] for r in rows]
    mean = sum(demand_values) / len(demand_values)

    if mean == 0:
        return None

    variance = sum((x - mean) ** 2 for x in demand_values) / len(demand_values)
    std_dev = math.sqrt(variance)
    cv = std_dev / mean

    if cv > threshold_cv:
        z_score = (demand_values[-1] - mean) / std_dev if std_dev > 0 else 0

        cursor = db.execute("""
            INSERT INTO planning_volatility_alerts
            (item_id, warehouse_id, alert_type, severity, threshold_value,
             actual_value, cv_value, z_score)
            VALUES (?, ?, 'HIGH_VOLATILITY',
                    CASE WHEN ? > 1.0 THEN 'HIGH' ELSE 'MEDIUM' END,
                    ?, ?, ?, ?)
        """, (item_id, warehouse_id, cv, threshold_cv, cv, cv, z_score))
        db.commit()
        return cursor.lastrowid

    return None


def detect_demand_spike_or_drop(db, item_id, warehouse_id=None, window=7, z_threshold=2.0):
    """
    Detect sudden demand spikes or drops using Z-score analysis.
    """
    start_date = (datetime.now() - timedelta(days=window * 2)).strftime('%Y-%m-%d')

    rows = db.execute("""
        SELECT period_start, sales_quantity + consumption_quantity as demand
        FROM planning_demand_history
        WHERE item_id = ? AND period_start >= ?
        ORDER BY period_start
    """, (item_id, start_date)).fetchall()

    if not rows or len(rows) < window:
        return None

    recent_values = [r['demand'] for r in rows[-window:]]
    baseline_values = [r['demand'] for r in rows[:-window]]

    if not baseline_values:
        return None

    baseline_mean = sum(baseline_values) / len(baseline_values)
    if baseline_mean == 0:
        return None

    baseline_var = sum((x - baseline_mean) ** 2 for x in baseline_values) / len(baseline_values)
    baseline_std = math.sqrt(baseline_var)

    if baseline_std == 0:
        return None

    z_score = (recent_values[-1] - baseline_mean) / baseline_std

    if abs(z_score) > z_threshold:
        alert_type = 'DEMAND_SPIKE' if z_score > 0 else 'DEMAND_DROP'
        severity = 'HIGH' if abs(z_score) > 3 else 'MEDIUM' if abs(z_score) > 2.5 else 'LOW'

        cursor = db.execute("""
            INSERT INTO planning_volatility_alerts
            (item_id, warehouse_id, alert_type, severity, threshold_value, actual_value, z_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (item_id, warehouse_id, alert_type, severity, z_threshold, recent_values[-1], z_score))
        db.commit()
        return cursor.lastrowid

    return None


# ============================================================
# ENTERPRISE OVERRIDE APPROVAL WORKFLOW
# ============================================================

def create_override_approval(db, override_id, requested_by, approval_level=1):
    """
    Create an approval record for a forecast override.
    """
    db.execute("""
        INSERT INTO planning_override_approvals
        (override_id, requested_by, approval_level)
        VALUES (?, ?, ?)
    """, (override_id, requested_by, approval_level))
    db.commit()


def approve_override(db, approval_id, reviewed_by, review_notes=None):
    """
    Approve a forecast override.
    """
    db.execute("""
        UPDATE planning_override_approvals
        SET approval_status = 'APPROVED',
            reviewed_by = ?,
            reviewed_at = CURRENT_TIMESTAMP,
            review_notes = ?
        WHERE id = ?
    """, (reviewed_by, review_notes, approval_id))

    approval = db.execute("SELECT override_id FROM planning_override_approvals WHERE id = ?",
                           (approval_id,)).fetchone()
    if approval:
        db.execute("""
            UPDATE planning_forecast_overrides
            SET status = 'APPROVED',
                reviewed_by = ?,
                reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (reviewed_by, approval['override_id']))

    db.commit()


def reject_override(db, approval_id, reviewed_by, review_notes=None):
    """
    Reject a forecast override.
    """
    db.execute("""
        UPDATE planning_override_approvals
        SET approval_status = 'REJECTED',
            reviewed_by = ?,
            reviewed_at = CURRENT_TIMESTAMP,
            review_notes = ?
        WHERE id = ?
    """, (reviewed_by, review_notes, approval_id))

    approval = db.execute("SELECT override_id FROM planning_override_approvals WHERE id = ?",
                           (approval_id,)).fetchone()
    if approval:
        db.execute("""
            UPDATE planning_forecast_overrides
            SET status = 'REJECTED',
                reviewed_by = ?,
                reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (reviewed_by, approval['override_id']))

    db.commit()


# ============================================================
# ENTERPRISE FLOW INTEGRATION
# ============================================================

def create_flow_notification(db, notification_type, title, message,
                              entity_type=None, entity_id=None, priority='NORMAL',
                              action_url=None, created_by=None, company_id=None):
    """
    Create a Flow notification for demand planning events.
    """
    cursor = db.execute("""
        INSERT INTO planning_flow_notifications
        (notification_type, title, message, entity_type, entity_id,
         priority, action_url, created_by, company_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (notification_type, title, message, entity_type, entity_id,
          priority, action_url, created_by, company_id))
    db.commit()
    return cursor.lastrowid


def notify_forecast_alert(db, item_id, alert_type, severity, title, message,
                          company_id=None, action_url=None):
    """
    Create a Flow notification for forecast-related alerts.
    """
    notification_type = f'FORECAST_ALERT_{alert_type}'
    priority = 'HIGH' if severity in ('CRITICAL', 'HIGH') else 'NORMAL'

    create_flow_notification(
        db, notification_type, title, message,
        entity_type='forecast_alert', entity_id=item_id,
        priority=priority, action_url=action_url,
        company_id=company_id
    )


def notify_pending_approval(db, entity_type, entity_id, entity_name,
                            approver_role, company_id=None, created_by=None):
    """
    Notify approvers of pending forecast approvals.
    """
    title = f"Pending Approval: {entity_name}"
    message = f"A forecast {entity_type} requires your approval."

    create_flow_notification(
        db, 'PENDING_APPROVAL', title, message,
        entity_type=entity_type, entity_id=entity_id,
        priority='NORMAL', action_url=f'/{entity_type}/review/{entity_id}',
        created_by=created_by, company_id=company_id
    )


# ============================================================
# ENTERPRISE FORECAST GENERATION WITH ALL METHODS
# ============================================================

def generate_statistical_forecast(db, item_id, method='MOVING_AVERAGE',
                                   horizon_days=30, period_type='daily',
                                   warehouse_id=None, company_id=None,
                                   created_by=None, run_name=None):
    """
    Generate a comprehensive statistical forecast using specified method.
    Supports: MOVING_AVERAGE, WEIGHTED_MOVING_AVERAGE, EXPONENTIAL_SMOOTHING,
              DOUBLE_EXPONENTIAL, HOLT_WINTERS, AUTO
    """
    if run_name is None:
        run_name = f"{method} Forecast {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    history_months = 12
    if method in ('HOLT_WINTERS',):
        history_months = 24

    history = db.execute("""
        SELECT period_start,
               sales_quantity + consumption_quantity as demand
        FROM planning_demand_history
        WHERE item_id = ? AND period_start >= DATE('now', '-' || ? || ' months')
        ORDER BY period_start
    """, (item_id, history_months)).fetchall()

    if not history:
        return None

    demand_values = [h['demand'] for h in history]

    if method == 'AUTO':
        method, params = auto_select_forecast_method(demand_values)
    else:
        params = {}

    if method == 'MOVING_AVERAGE':
        window = params.get('window', 3)
        forecast_value = calculate_moving_average(demand_values, window)
    elif method == 'WEIGHTED_MOVING_AVERAGE':
        weights = params.get('weights', [0.5, 0.3, 0.2])
        forecast_value = calculate_weighted_moving_average_v2(demand_values, weights)
    elif method == 'EXPONENTIAL_SMOOTHING':
        alpha = params.get('alpha', 0.3)
        forecast_value = calculate_exponential_smoothing(demand_values, alpha)
    elif method == 'DOUBLE_EXPONENTIAL':
        alpha = params.get('alpha', 0.3)
        beta = params.get('beta', 0.1)
        level, trend = calculate_double_exponential_smoothing(demand_values, alpha, beta)
        forecast_value = level + trend * (horizon_days / 2)
    elif method == 'HOLT_WINTERS':
        alpha = params.get('alpha', 0.3)
        beta = params.get('beta', 0.1)
        gamma = params.get('gamma', 0.1)
        period = params.get('period', 12)
        forecast_value, _ = calculate_triple_exponential_smoothing(
            demand_values, alpha, beta, gamma, period
        )
    else:
        forecast_value = calculate_moving_average(demand_values, 3)

    cursor = db.execute("""
        INSERT INTO planning_forecast_runs
        (run_name, forecast_type, method, horizon_days, period_type,
         warehouse_id, company_id, status, created_by, total_items, total_demand)
        VALUES (?, 'DEMAND', ?, ?, ?, ?, ?, 'DRAFT', ?, 1, ?)
    """, (run_name, method, horizon_days, period_type, warehouse_id, company_id,
          created_by, forecast_value * horizon_days))

    run_id = cursor.lastrowid

    for day_offset in range(horizon_days):
        forecast_date = (datetime.now() + timedelta(days=day_offset)).strftime('%Y-%m-%d')

        seasonal_factor = 1.0
        seasonal_profile = db.execute("""
            SELECT * FROM planning_seasonality_profiles
            WHERE item_id = ? OR (brand_id = (SELECT brand_id FROM wms_items WHERE id = ?))
                   OR (category_id = (SELECT category_id FROM wms_items WHERE id = ?))
            LIMIT 1
        """, (item_id, item_id, item_id)).fetchone()

        if seasonal_profile:
            month = (datetime.strptime(forecast_date, '%Y-%m-%d').month)
            month_col = {1: 'jan_factor', 2: 'feb_factor', 3: 'mar_factor', 4: 'apr_factor',
                         5: 'may_factor', 6: 'jun_factor', 7: 'jul_factor', 8: 'aug_factor',
                         9: 'sep_factor', 10: 'oct_factor', 11: 'nov_factor', 12: 'dec_factor'}
            seasonal_factor = seasonal_profile.get(month_col.get(month), 1.0)

        final_value = forecast_value * seasonal_factor

        db.execute("""
            INSERT INTO planning_forecast_lines
            (run_id, item_id, warehouse_id, company_id, period_start, period_type,
             base_quantity, seasonal_factor, final_quantity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (run_id, item_id, warehouse_id, company_id, forecast_date, period_type,
              forecast_value, seasonal_factor, final_value))

    db.execute("""
        UPDATE planning_item_profiles
        SET last_forecast_run_id = ?, last_calculated_at = CURRENT_TIMESTAMP
        WHERE item_id = ?
    """, (run_id, item_id))

    db.commit()
    return run_id


# ============================================================
# ENTERPRISE MODEL PERFORMANCE TRACKING
# ============================================================

def record_model_performance(db, item_id, model_name, period_start, period_end,
                              mape, wape=None, mae=None, bias=None, rmse=None,
                              theil_u=None, is_best_fit=False, parameters=None):
    """
    Record forecast model performance metrics for model comparison.
    """
    params_json = json.dumps(parameters) if parameters else None

    db.execute("""
        INSERT INTO planning_model_performance
        (item_id, model_name, period_start, period_end, mape, wape, mae, bias,
         rmse, theil_u, is_best_fit, parameters_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (item_id, model_name, period_start, period_end, mape, wape, mae, bias,
          rmse, theil_u, 1 if is_best_fit else 0, params_json))
    db.commit()


def get_best_forecast_model(db, item_id):
    """
    Get the best performing forecast model for an item based on historical MAPE.
    """
    row = db.execute("""
        SELECT model_name, parameters_json
        FROM planning_model_performance
        WHERE item_id = ? AND mape IS NOT NULL
        ORDER BY mape ASC
        LIMIT 1
    """, (item_id,)).fetchone()

    if row:
        params = json.loads(row['parameters_json']) if row['parameters_json'] else {}
        return row['model_name'], params
    return None, None


# ============================================================
# ENTERPRISE SCENARIO PLANNING ENHANCEMENTS
# ============================================================

def create_scenario_from_forecast(db, scenario_name, scenario_type, forecast_run_id=None,
                                   parameters=None, created_by=None, company_id=None,
                                   description=None):
    """
    Create a new planning scenario based on an existing forecast.
    """
    cursor = db.execute("""
        INSERT INTO planning_scenarios
        (name, description, scenario_type, parameters_json, created_by, company_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (scenario_name, description, scenario_type,
          json.dumps(parameters) if parameters else None, created_by, company_id))

    scenario_id = cursor.lastrowid

    if forecast_run_id:
        db.execute("""
            INSERT INTO planning_scenario_lines
            (scenario_id, item_id, warehouse_id, company_id, metric_name,
             base_value)
            SELECT ?, item_id, warehouse_id, company_id, 'FORECAST', final_quantity
            FROM planning_forecast_lines
            WHERE run_id = ?
        """, (scenario_id, forecast_run_id))

        total_items = db.execute("""
            SELECT COUNT(DISTINCT item_id) as cnt FROM planning_forecast_lines WHERE run_id = ?
        """, (forecast_run_id,)).fetchone()['cnt']

        total_impact = db.execute("""
            SELECT SUM(base_value) as total FROM planning_scenario_lines WHERE scenario_id = ?
        """, (scenario_id,)).fetchone()['total'] or 0

        db.execute("""
            UPDATE planning_scenarios
            SET total_impact_items = ?, total_shortage_impact = ?
            WHERE id = ?
        """, (total_items, total_impact, scenario_id))

    db.commit()
    return scenario_id


def apply_scenario_assumptions(db, scenario_id):
    """
    Apply scenario parameters to forecast lines and calculate impacts.
    """
    scenario = db.execute("SELECT * FROM planning_scenarios WHERE id = ?",
                          (scenario_id,)).fetchone()
    if not scenario:
        return

    params = json.loads(scenario['parameters_json']) if scenario['parameters_json'] else {}

    uplift_percent = params.get('uplift_percent', 0)
    demand_shift = params.get('demand_shift', 0)
    price_factor = params.get('price_factor', 1.0)

    scenario_type = scenario['scenario_type']

    if scenario_type == 'PROMOTION':
        factor = 1 + (uplift_percent / 100)
    elif scenario_type == 'DEMAND_SPIKE':
        factor = 1 + (demand_shift / 100)
    elif scenario_type == 'DEMAND_DROP':
        factor = 1 - (abs(demand_shift) / 100)
    elif scenario_type == 'PRICE_CHANGE':
        factor = price_factor
    else:
        factor = 1 + (uplift_percent / 100)

    db.execute("""
        UPDATE planning_scenario_lines
        SET scenario_value = base_value * ?,
            impact_value = (base_value * ?) - base_value,
            impact_percent = ((base_value * ?) - base_value) / NULLIF(base_value, 0) * 100
        WHERE scenario_id = ?
    """, (factor, factor, factor, scenario_id))

    total_impact = db.execute("""
        SELECT SUM(impact_value) as total, SUM(impact_percent) as pct
        FROM planning_scenario_lines
        WHERE scenario_id = ?
    """, (scenario_id,)).fetchone()

    db.execute("""
        UPDATE planning_scenarios
        SET total_cost_impact = ?
        WHERE id = ?
    """, (total_impact['total'] if total_impact else 0, scenario_id))

    db.commit()
