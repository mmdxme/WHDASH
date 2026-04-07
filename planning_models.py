"""
Planning Models - Demand Forecasting & Inventory Planning System

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
"""

import sqlite3
import json
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
