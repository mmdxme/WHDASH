"""
Customer Demand Intelligence System - Database Models
======================================================
Enterprise-grade customer analytics, behavior forecasting, and demand intelligence.

Tables:
- ci_customer_profiles: Enriched customer master with intelligence-ready fields
- ci_customer_segments: Flexible segment definitions (manual, rule-based, dynamic)
- ci_segment_members: Customer-to-segment membership mapping
- ci_retail_behavior: Retail-specific customer behavior metrics
- ci_wholesale_behavior: Wholesale-specific customer behavior metrics
- ci_customer_demand_history: Demand/Order/Inquiry history per customer
- ci_lost_sales: Lost sales and unmet demand records
- ci_customer_seasonality: Seasonality patterns per customer
- ci_basket_profiles: Favorite items/brands/categories per customer
- ci_dependency_profiles: Brand/item/salesperson dependency per customer
- ci_financial_profiles: Financial and credit behavior per customer
- ci_logistics_profiles: Logistics and service burden per customer
- ci_forecast_runs: Forecast generation runs
- ci_forecast_lines: Per-customer, per-item forecast lines
- ci_forecast_versions: Versioning for forecast overrides
- ci_risk_alerts: Churn, risk, and opportunity alerts
- ci_recommendations: Actionable recommendations per customer
- ci_kpi_records: KPI snapshots per customer
- ci_audit_logs: Audit trail for all critical changes
- ci_settings: Configurable business rules and thresholds
"""

import sqlite3
import os
from datetime import datetime, timedelta
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
# CUSTOMER INTELLIGENCE TABLE DEFINITIONS
# =============================================================================

CI_TABLES = [

    # -------------------------------------------------------------------------
    # 1. CI Customer Profiles - Enriched customer master
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS ci_customer_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        sdad_customer_id INTEGER,
        company_id INTEGER,
        salesperson_id INTEGER,
        customer_type TEXT DEFAULT 'retail',
        customer_subtype TEXT,
        customer_code TEXT,
        customer_name TEXT NOT NULL,
        contact_person TEXT,
        phone TEXT,
        email TEXT,
        city TEXT,
        country TEXT,
        market TEXT DEFAULT 'local',
        sales_channel TEXT,
        related_company TEXT,
        is_active INTEGER DEFAULT 1,
        is_new INTEGER DEFAULT 0,
        is_key INTEGER DEFAULT 0,
        is_profitable INTEGER DEFAULT 1,
        is_good_payer INTEGER DEFAULT 1,
        is_recurring INTEGER DEFAULT 0,
        is_seasonal INTEGER DEFAULT 0,
        price_sensitivity REAL DEFAULT 0.5,
        speed_sensitivity REAL DEFAULT 0.5,
        brand_sensitivity REAL DEFAULT 0.5,
        credit_limit REAL DEFAULT 0,
        outstanding_balance REAL DEFAULT 0,
        avg_payment_delay_days REAL DEFAULT 0,
        returned_cheque_count INTEGER DEFAULT 0,
        debt_status TEXT DEFAULT 'Good',
        payment_terms TEXT DEFAULT 'Net 30',
        transaction_currency TEXT DEFAULT 'AED',
        agreed_discount REAL DEFAULT 0,
        target_margin REAL DEFAULT 0,
        loyalty_score REAL DEFAULT 0,
        churn_risk_score REAL DEFAULT 0,
        growth_score REAL DEFAULT 0,
        lifetime_value REAL DEFAULT 0,
        service_burden_score REAL DEFAULT 0,
        operational_pressure_score REAL DEFAULT 0,
        notes TEXT,
        tags TEXT,
        custom_attributes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
        FOREIGN KEY (sdad_customer_id) REFERENCES sdad_customers(id) ON DELETE SET NULL,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL,
        FOREIGN KEY (salesperson_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 2. CI Customer Segments
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS ci_customer_segments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        segment_name TEXT NOT NULL,
        segment_code TEXT UNIQUE NOT NULL,
        segment_type TEXT NOT NULL,
        description TEXT,
        rules_definition TEXT,
        is_dynamic INTEGER DEFAULT 0,
        is_system INTEGER DEFAULT 0,
        company_id INTEGER,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 3. CI Segment Members
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS ci_segment_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        segment_id INTEGER NOT NULL,
        customer_id INTEGER NOT NULL,
        company_id INTEGER,
        added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        added_by INTEGER,
        FOREIGN KEY (segment_id) REFERENCES ci_customer_segments(id) ON DELETE CASCADE,
        FOREIGN KEY (customer_id) REFERENCES sdad_customers(id) ON DELETE CASCADE,
        FOREIGN KEY (added_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 4. CI Retail Behavior
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS ci_retail_behavior (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        company_id INTEGER,
        visits_per_month REAL DEFAULT 0,
        avg_basket_value REAL DEFAULT 0,
        avg_sku_count REAL DEFAULT 0,
        avg_time_between_purchases_days REAL DEFAULT 0,
        urgent_purchase_ratio REAL DEFAULT 0,
        substitute_purchase_ratio REAL DEFAULT 0,
        repeat_purchase_rate REAL DEFAULT 0,
        cancellation_rate REAL DEFAULT 0,
        inquiry_to_purchase_rate REAL DEFAULT 0,
        loyalty_score REAL DEFAULT 0,
        price_sensitivity_score REAL DEFAULT 0,
        brand_loyalty_score REAL DEFAULT 0,
        demand_volatility REAL DEFAULT 0,
        last_purchase_date TEXT,
        avg_purchase_amount REAL DEFAULT 0,
        preferred_payment_method TEXT,
        preferred_brand TEXT,
        preferred_category TEXT,
        accepts_substitutes INTEGER DEFAULT 0,
        prefers_immediate_stock INTEGER DEFAULT 0,
        sensitivity_to_delivery_time REAL DEFAULT 0,
        sensitivity_to_final_price REAL DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES sdad_customers(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 5. CI Wholesale Behavior
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS ci_wholesale_behavior (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        company_id INTEGER,
        avg_order_volume REAL DEFAULT 0,
        order_frequency_per_month REAL DEFAULT 0,
        order_cycle_days REAL DEFAULT 0,
        order_regularity_score REAL DEFAULT 0,
        payment_discipline_score REAL DEFAULT 0,
        order_fulfillment_rate REAL DEFAULT 0,
        critical_shortage_ratio REAL DEFAULT 0,
        reserved_stock_share REAL DEFAULT 0,
        purchase_growth_rate REAL DEFAULT 0,
        brand_stability_score REAL DEFAULT 0,
        basket_stability_score REAL DEFAULT 0,
        customer_lifetime_value REAL DEFAULT 0,
        avg_sku_count_per_order REAL DEFAULT 0,
        share_of_top_item REAL DEFAULT 0,
        discount_sensitivity REAL DEFAULT 0,
        lead_time_sensitivity REAL DEFAULT 0,
        quality_sensitivity REAL DEFAULT 0,
        supply_stability_sensitivity REAL DEFAULT 0,
        payment_terms_sensitivity REAL DEFAULT 0,
        reserved_stock_sensitivity REAL DEFAULT 0,
        delivery_commitment_sensitivity REAL DEFAULT 0,
        volume_demand_score REAL DEFAULT 0,
        export_demand_share REAL DEFAULT 0,
        project_driven_demand_score REAL DEFAULT 0,
        contract_demand_share REAL DEFAULT 0,
        seasonal_demand_share REAL DEFAULT 0,
        last_order_date TEXT,
        last_contact_date TEXT,
        top_brand_1 TEXT,
        top_brand_2 TEXT,
        top_item_group TEXT,
        has_contract INTEGER DEFAULT 0,
        has_reserved_stock INTEGER DEFAULT 0,
        prefers_single_brand INTEGER DEFAULT 0,
        prefers_single_item INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES sdad_customers(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 6. CI Customer Demand History
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS ci_customer_demand_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        company_id INTEGER,
        record_date DATE NOT NULL,
        period_type TEXT NOT NULL,
        request_count INTEGER DEFAULT 0,
        confirmed_order_count INTEGER DEFAULT 0,
        preorder_count INTEGER DEFAULT 0,
        open_orders INTEGER DEFAULT 0,
        delayed_orders INTEGER DEFAULT 0,
        partial_orders INTEGER DEFAULT 0,
        cancelled_orders INTEGER DEFAULT 0,
        inquiry_count INTEGER DEFAULT 0,
        purchase_count INTEGER DEFAULT 0,
        purchase_amount REAL DEFAULT 0,
        purchase_quantity INTEGER DEFAULT 0,
        sku_count INTEGER DEFAULT 0,
        item_groups TEXT,
        brands TEXT,
        conversion_rate REAL DEFAULT 0,
        avg_order_value REAL DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES sdad_customers(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 7. CI Lost Sales
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS ci_lost_sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        company_id INTEGER,
        lost_date DATE NOT NULL,
        reason TEXT NOT NULL,
        reason_category TEXT,
        requested_item_id INTEGER,
        requested_item_name TEXT,
        requested_quantity INTEGER DEFAULT 0,
        lost_amount REAL DEFAULT 0,
        lost_profit REAL DEFAULT 0,
        competitor_name TEXT,
        customer_reaction TEXT,
        alternative_item_id INTEGER,
        alternative_item_name TEXT,
        was_substituted INTEGER DEFAULT 0,
        follow_up_action TEXT,
        follow_up_date TEXT,
        follow_up_notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES sdad_customers(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 8. CI Customer Seasonality
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS ci_customer_seasonality (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        company_id INTEGER,
        month_1 REAL DEFAULT 0, month_2 REAL DEFAULT 0, month_3 REAL DEFAULT 0,
        month_4 REAL DEFAULT 0, month_5 REAL DEFAULT 0, month_6 REAL DEFAULT 0,
        month_7 REAL DEFAULT 0, month_8 REAL DEFAULT 0, month_9 REAL DEFAULT 0,
        month_10 REAL DEFAULT 0, month_11 REAL DEFAULT 0, month_12 REAL DEFAULT 0,
        peak_month_1 INTEGER, peak_month_2 INTEGER, peak_month_3 INTEGER,
        low_month_1 INTEGER, low_month_2 INTEGER,
        seasonality_type TEXT DEFAULT 'stable',
        ramadan_effect REAL DEFAULT 0,
        eid_effect REAL DEFAULT 0,
        summer_effect REAL DEFAULT 0, winter_effect REAL DEFAULT 0,
        promotional_response_score REAL DEFAULT 0,
        pre_holiday_spike_score REAL DEFAULT 0,
        post_holiday_dip_score REAL DEFAULT 0,
        weather_sensitivity REAL DEFAULT 0,
        annual_growth_rate REAL DEFAULT 0,
        annual_volatility REAL DEFAULT 0,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES sdad_customers(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 9. CI Basket Profiles
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS ci_basket_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        company_id INTEGER,
        frequent_items TEXT,
        frequent_brands TEXT,
        frequent_categories TEXT,
        frequent_item_groups TEXT,
        acceptable_substitutes TEXT,
        complementary_items TEXT,
        critical_items TEXT,
        basket_diversity_score REAL DEFAULT 0,
        repeat_item_ratio REAL DEFAULT 0,
        cross_sell_opportunities TEXT,
        upsell_opportunities TEXT,
        loyalty_by_brand TEXT,
        loyalty_by_sku TEXT,
        acceptable_alternatives TEXT,
        top_5_items TEXT,
        top_3_brands TEXT,
        basket_size_avg REAL DEFAULT 0,
        basket_size_min INTEGER DEFAULT 0,
        basket_size_max INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES sdad_customers(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 10. CI Dependency Profiles
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS ci_dependency_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        company_id INTEGER,
        brand_dependency_score REAL DEFAULT 0,
        primary_brand TEXT,
        brand_1_share REAL DEFAULT 0, brand_2_share REAL DEFAULT 0, brand_3_share REAL DEFAULT 0,
        item_dependency_score REAL DEFAULT 0,
        primary_item_id INTEGER,
        primary_item_name TEXT,
        top_item_share REAL DEFAULT 0,
        warehouse_dependency_score REAL DEFAULT 0,
        primary_warehouse_id INTEGER,
        immediate_delivery_dependency_score REAL DEFAULT 0,
        salesperson_dependency_score REAL DEFAULT 0,
        assigned_salesperson_id INTEGER,
        salesperson_share REAL DEFAULT 0,
        discount_dependency_score REAL DEFAULT 0,
        customer_share_concentration REAL DEFAULT 0,
        business_concentration_risk REAL DEFAULT 0,
        strategic_dependency_alert TEXT,
        dependency_alert_level TEXT DEFAULT 'Low',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES sdad_customers(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 11. CI Financial Profiles
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS ci_financial_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        company_id INTEGER,
        avg_purchase_amount REAL DEFAULT 0,
        total_monthly_purchase REAL DEFAULT 0,
        total_yearly_purchase REAL DEFAULT 0,
        customer_margin REAL DEFAULT 0,
        discount_percentage_received REAL DEFAULT 0,
        service_cost REAL DEFAULT 0,
        delivery_cost REAL DEFAULT 0,
        net_customer_profit REAL DEFAULT 0,
        share_of_total_sales REAL DEFAULT 0,
        cash_vs_credit_ratio REAL DEFAULT 0,
        settlement_period_days INTEGER DEFAULT 0,
        avg_payment_delay_days REAL DEFAULT 0,
        open_invoice_count INTEGER DEFAULT 0,
        collection_risk_score REAL DEFAULT 0,
        payment_discipline_score REAL DEFAULT 0,
        credit_utilization REAL DEFAULT 0,
        credit_limit_breach_count INTEGER DEFAULT 0,
        profitability_after_logistics REAL DEFAULT 0,
        profitability_after_discount REAL DEFAULT 0,
        profitability_after_service REAL DEFAULT 0,
        total_revenue_generated REAL DEFAULT 0,
        total_profit_generated REAL DEFAULT 0,
        avg_monthly_revenue REAL DEFAULT 0,
        avg_monthly_profit REAL DEFAULT 0,
        last_financial_review_date TEXT,
        financial_rating INTEGER DEFAULT 3,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES sdad_customers(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 12. CI Logistics Profiles
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS ci_logistics_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        company_id INTEGER,
        is_self_pickup INTEGER DEFAULT 0,
        delivery_service_type TEXT DEFAULT 'standard',
        daily_delivery_count INTEGER DEFAULT 0,
        multiple_deliveries_per_day INTEGER DEFAULT 0,
        consolidated_delivery INTEGER DEFAULT 1,
        urgent_delivery_ratio REAL DEFAULT 0,
        fixed_vs_changing_location TEXT DEFAULT 'fixed',
        delivery_location_count INTEGER DEFAULT 1,
        delivery_time_sensitivity REAL DEFAULT 0,
        total_deliveries INTEGER DEFAULT 0,
        cost_per_delivery REAL DEFAULT 0,
        avg_preparation_time_minutes REAL DEFAULT 0,
        urgent_order_ratio REAL DEFAULT 0,
        small_order_ratio REAL DEFAULT 0,
        bulk_order_ratio REAL DEFAULT 0,
        operational_pressure_score REAL DEFAULT 0,
        route_complexity_score REAL DEFAULT 0,
        service_burden_score REAL DEFAULT 0,
        customer_logistics_profitability REAL DEFAULT 0,
        avg_delivery_lead_time_hours REAL DEFAULT 0,
        delivery_success_rate REAL DEFAULT 0,
        delivery_change_frequency REAL DEFAULT 0,
        preferred_delivery_window TEXT,
        special_handling_requirements TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES sdad_customers(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 13. CI Forecast Runs
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS ci_forecast_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_name TEXT NOT NULL,
        forecast_type TEXT NOT NULL,
        customer_scope TEXT DEFAULT 'all',
        period_start DATE NOT NULL,
        period_end DATE NOT NULL,
        granularity TEXT DEFAULT 'monthly',
        model_version TEXT,
        status TEXT DEFAULT 'pending',
        total_customers_forecasted INTEGER DEFAULT 0,
        total_demand_forecasted REAL DEFAULT 0,
        notes TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME
    )""",

    # -------------------------------------------------------------------------
    # 14. CI Forecast Lines
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS ci_forecast_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER NOT NULL,
        customer_id INTEGER NOT NULL,
        company_id INTEGER,
        forecast_date DATE NOT NULL,
        period_type TEXT NOT NULL,
        predicted_demand REAL DEFAULT 0,
        predicted_order_count REAL DEFAULT 0,
        predicted_revenue REAL DEFAULT 0,
        confidence_level REAL DEFAULT 0,
        prediction_interval_low REAL DEFAULT 0,
        prediction_interval_high REAL DEFAULT 0,
        is_override INTEGER DEFAULT 0,
        override_reason TEXT,
        approved INTEGER DEFAULT 0,
        approved_by INTEGER,
        approved_at DATETIME,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (run_id) REFERENCES ci_forecast_runs(id) ON DELETE CASCADE,
        FOREIGN KEY (customer_id) REFERENCES sdad_customers(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 15. CI Forecast Versions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS ci_forecast_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER NOT NULL,
        version_number INTEGER NOT NULL,
        version_label TEXT,
        changes_summary TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (run_id) REFERENCES ci_forecast_runs(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 16. CI Risk Alerts
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS ci_risk_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        company_id INTEGER,
        alert_type TEXT NOT NULL,
        alert_category TEXT NOT NULL,
        alert_level TEXT DEFAULT 'Medium',
        title TEXT NOT NULL,
        description TEXT,
        metric_name TEXT,
        metric_value REAL,
        threshold_value REAL,
        churn_risk_score REAL,
        growth_opportunity_score REAL,
        recommended_action TEXT,
        is_resolved INTEGER DEFAULT 0,
        resolved_by INTEGER,
        resolved_at DATETIME,
        resolution_notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES sdad_customers(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 17. CI Recommendations
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS ci_recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        company_id INTEGER,
        recommendation_type TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        priority TEXT DEFAULT 'Medium',
        action_category TEXT,
        suggested_items TEXT,
        suggested_campaign TEXT,
        target_date TEXT,
        estimated_impact REAL,
        effort_level TEXT,
        is_approved INTEGER DEFAULT 0,
        approved_by INTEGER,
        approved_at DATETIME,
        is_implemented INTEGER DEFAULT 0,
        implemented_at DATETIME,
        implementation_notes TEXT,
        status TEXT DEFAULT 'Open',
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES sdad_customers(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 18. CI KPI Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS ci_kpi_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        company_id INTEGER,
        kpi_name TEXT NOT NULL,
        kpi_category TEXT,
        kpi_value REAL DEFAULT 0,
        kpi_unit TEXT,
        period_start DATE,
        period_end DATE,
        comparison_value REAL,
        trend_direction TEXT,
        is_anomaly INTEGER DEFAULT 0,
        anomaly_score REAL DEFAULT 0,
        notes TEXT,
        recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES sdad_customers(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 19. CI Audit Logs
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS ci_audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,
        entity_id INTEGER,
        customer_id INTEGER,
        action_type TEXT NOT NULL,
        field_name TEXT,
        old_value TEXT,
        new_value TEXT,
        reason TEXT,
        notes TEXT,
        company_id INTEGER,
        user_id INTEGER,
        ip_address TEXT,
        user_agent TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 20. CI Settings
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS ci_settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        churn_risk_threshold_high REAL DEFAULT 0.75,
        churn_risk_threshold_medium REAL DEFAULT 0.50,
        growth_threshold_high REAL DEFAULT 0.30,
        growth_threshold_low REAL DEFAULT -0.20,
        inactive_days_threshold INTEGER DEFAULT 90,
        payment_delay_threshold_days INTEGER DEFAULT 30,
        credit_utilization_threshold REAL DEFAULT 0.90,
        min_order_frequency_wholesale INTEGER DEFAULT 2,
        min_order_volume_wholesale REAL DEFAULT 1000,
        forecast_confidence_threshold REAL DEFAULT 0.70,
        seasonality_spike_threshold REAL DEFAULT 1.5,
        service_burden_threshold_high REAL DEFAULT 0.80,
        operational_pressure_threshold REAL DEFAULT 0.70,
        profit_margin_threshold_low REAL DEFAULT 0.10,
        lost_sales_alert_threshold REAL DEFAULT 0.15,
        customer_lifetime_months INTEGER DEFAULT 36,
        key_customer_revenue_threshold REAL DEFAULT 50000,
        high_value_customer_threshold REAL DEFAULT 100000,
        currency TEXT DEFAULT 'AED',
        date_format TEXT DEFAULT 'DD/MM/YYYY',
        timezone TEXT DEFAULT 'Asia/Dubai',
        forecast_granularity_default TEXT DEFAULT 'monthly',
        auto_alert_generation INTEGER DEFAULT 1,
        auto_forecast_generation INTEGER DEFAULT 1,
        forecast_horizon_months INTEGER DEFAULT 6,
        min_data_points_for_forecast INTEGER DEFAULT 3,
        seasonality_detection_enabled INTEGER DEFAULT 1,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
]


def init_ci_tables():
    """Initialize all Customer Intelligence tables."""
    conn = get_db()
    try:
        for table_sql in CI_TABLES:
            conn.executescript(table_sql)
        conn.commit()
        
        # Seed default settings if not exists
        existing = conn.execute("SELECT COUNT(*) FROM ci_settings").fetchone()[0]
        if existing == 0:
            conn.execute("INSERT INTO ci_settings (id) VALUES (1)")
            conn.commit()
        
        # Seed default segment types if not exist
        default_segments = [
            ('Active', 'active', 'Active customers with recent purchases', 0, 1),
            ('Inactive', 'inactive', 'Customers with no recent activity', 0, 1),
            ('New', 'new', 'Recently acquired customers', 0, 1),
            ('Key', 'key', 'High-value strategic customers', 0, 1),
            ('Profitable', 'profitable', 'Customers with strong margins', 0, 1),
            ('Low-Profit', 'low_profit', 'Customers with thin margins', 0, 1),
            ('Good Payer', 'good_payer', 'Customers with excellent payment history', 0, 1),
            ('Risky', 'risky', 'Customers with payment or credit concerns', 0, 1),
            ('Recurring', 'recurring', 'Customers with regular purchase patterns', 0, 1),
            ('Occasional', 'occasional', 'Sporadic purchasing customers', 0, 1),
            ('Seasonal', 'seasonal', 'Customers with strong seasonal patterns', 0, 1),
            ('Stable', 'stable', 'Customers with consistent year-round demand', 0, 1),
            ('Local', 'local', 'Domestic market customers', 0, 1),
            ('Export', 'export', 'Export market customers', 0, 1),
            ('Wholesale', 'wholesale', 'Wholesale business customers', 0, 1),
            ('Retail', 'retail', 'Retail customers', 0, 1),
            ('High-Growth', 'high_growth', 'Customers showing strong growth', 0, 1),
            ('Declining', 'declining', 'Customers showing declining activity', 0, 1),
            ('High-Service-Cost', 'high_service_cost', 'Customers with high operational burden', 0, 1),
            ('High-Churn-Risk', 'high_churn_risk', 'Customers at risk of churning', 0, 1),
            ('Stock-Dependent', 'stock_dependent', 'Customers highly dependent on stock availability', 0, 1),
            ('Salesperson-Dependent', 'salesperson_dependent', 'Customers tied to specific salesperson', 0, 1),
        ]
        for name, code, desc, is_dynamic, is_system in default_segments:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO ci_customer_segments 
                    (segment_name, segment_code, segment_type, description, is_dynamic, is_system)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, code, 'behavioral', desc, is_dynamic, is_system))
            except:
                pass
        conn.commit()
    finally:
        conn.close()


def log_ci_audit(entity_type, entity_id, action_type, field_name=None, old_value=None,
                  new_value=None, reason=None, notes=None, company_id=None, customer_id=None):
    """Log an audit entry for customer intelligence actions."""
    conn = get_db()
    try:
        user_id = None
        try:
            from flask import session
            user_id = session.get('user_id')
        except:
            pass
        
        conn.execute("""
            INSERT INTO ci_audit_logs 
            (entity_type, entity_id, action_type, field_name, old_value, new_value, reason, notes, company_id, customer_id, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (entity_type, entity_id, action_type, field_name, old_value, new_value, reason, notes, company_id, customer_id, user_id))
        conn.commit()
    finally:
        conn.close()


def get_ci_settings():
    """Get Customer Intelligence settings."""
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM ci_settings WHERE id = 1").fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


def update_ci_settings(settings_dict):
    """Update Customer Intelligence settings."""
    conn = get_db()
    try:
        allowed_fields = [
            'churn_risk_threshold_high', 'churn_risk_threshold_medium',
            'growth_threshold_high', 'growth_threshold_low',
            'inactive_days_threshold', 'payment_delay_threshold_days',
            'credit_utilization_threshold', 'min_order_frequency_wholesale',
            'min_order_volume_wholesale', 'forecast_confidence_threshold',
            'seasonality_spike_threshold', 'service_burden_threshold_high',
            'operational_pressure_threshold', 'profit_margin_threshold_low',
            'lost_sales_alert_threshold', 'customer_lifetime_months',
            'key_customer_revenue_threshold', 'high_value_customer_threshold',
            'currency', 'date_format', 'timezone',
            'forecast_granularity_default', 'auto_alert_generation',
            'auto_forecast_generation', 'forecast_horizon_months',
            'min_data_points_for_forecast', 'seasonality_detection_enabled'
        ]
        
        for key, value in settings_dict.items():
            if key in allowed_fields:
                conn.execute(f"UPDATE ci_settings SET {key} = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (value,))
        conn.commit()
        return True
    finally:
        conn.close()


if __name__ == '__main__':
    init_ci_tables()
    print("Customer Intelligence tables initialized successfully.")
