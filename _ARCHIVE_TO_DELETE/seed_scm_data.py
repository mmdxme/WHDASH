"""
Seed SCM Data - Sample data for Supply Chain Management module.
Run this script to populate the database with realistic SCM sample data.
"""

import sqlite3
import random
from datetime import datetime, timedelta


def seed_scm_data(db_path='warehouse.db'):
    """Seed the database with SCM sample data."""
    conn = sqlite3.connect(db_path)
    db = conn.cursor()
    
    print("Seeding SCM data...")
    
    # Seed planning_demand_history
    print("  - Creating demand history...")
    items = db.execute("SELECT id FROM wms_items WHERE is_active = 1 LIMIT 20").fetchall()
    if items:
        for item in items:
            item_id = item[0]
            for days_ago in range(90, 0, -3):
                date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
                sales_qty = random.randint(10, 200)
                consumption_qty = random.randint(5, 50)
                db.execute("""
                    INSERT INTO planning_demand_history 
                    (item_id, period_start, sales_quantity, consumption_quantity, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (item_id, date, sales_qty, consumption_qty, datetime.now().isoformat()))
    
    # Seed planning_forecast_runs
    print("  - Creating forecast runs...")
    forecast_methods = ['MOVING_AVERAGE', 'WEIGHTED_MA', 'EXP_SMOOTHING']
    for i in range(5):
        db.execute("""
            INSERT INTO planning_forecast_runs
            (run_name, method, horizon_days, status, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            f"Forecast Run {i+1}",
            random.choice(forecast_methods),
            30,
            'COMPLETED' if i < 3 else 'DRAFT',
            1,
            datetime.now().isoformat()
        ))
    
    # Seed planning_replenishment_recommendations
    print("  - Creating replenishment recommendations...")
    warehouses = db.execute("SELECT id FROM warehouses LIMIT 5").fetchall()
    if items and warehouses:
        for item in items[:10]:
            item_id = item[0]
            warehouse_id = random.choice(warehouses)[0]
            db.execute("""
                INSERT INTO planning_replenishment_recommendations
                (item_id, warehouse_id, recommended_quantity, recommended_date, 
                 priority, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id,
                warehouse_id,
                random.randint(50, 500),
                (datetime.now() + timedelta(days=random.randint(1, 14))).strftime('%Y-%m-%d'),
                random.choice(['HIGH', 'MEDIUM', 'LOW']),
                'OPEN',
                datetime.now().isoformat()
            ))
    
    # Seed planning_purchase_recommendations
    print("  - Creating purchase recommendations...")
    suppliers = db.execute("SELECT id FROM suppliers LIMIT 5").fetchall()
    if items and suppliers:
        for item in items[:10]:
            item_id = item[0]
            supplier_id = random.choice(suppliers)[0]
            db.execute("""
                INSERT INTO planning_purchase_recommendations
                (item_id, supplier_id, recommended_quantity, recommended_date,
                 priority, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id,
                supplier_id,
                random.randint(100, 1000),
                (datetime.now() + timedelta(days=random.randint(7, 30))).strftime('%Y-%m-%d'),
                random.choice(['HIGH', 'MEDIUM', 'LOW']),
                'OPEN',
                datetime.now().isoformat()
            ))
    
    # Seed planning_transfer_recommendations
    print("  - Creating transfer recommendations...")
    if len(warehouses) >= 2:
        for item in items[:5]:
            item_id = item[0]
            from_wh = random.choice(warehouses)[0]
            to_wh = random.choice([w for w in warehouses if w[0] != from_wh])[0]
            db.execute("""
                INSERT INTO planning_transfer_recommendations
                (item_id, from_warehouse_id, to_warehouse_id, recommended_quantity,
                 priority, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id,
                from_wh,
                to_wh,
                random.randint(20, 100),
                'MEDIUM',
                'OPEN',
                datetime.now().isoformat()
            ))
    
    # Seed planning_scenarios
    print("  - Creating scenarios...")
    scenario_types = ['DEMAND_INCREASE', 'DEMAND_DECREASE', 'SUPPLIER_DELAY', 'LEAD_TIME_INCREASE']
    for i, s_type in enumerate(scenario_types):
        db.execute("""
            INSERT INTO planning_scenarios
            (scenario_name, scenario_type, assumptions, is_active, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            f"Scenario {i+1}: {s_type.replace('_', ' ').title()}",
            s_type,
            f"Test assumptions for {s_type}",
            1,
            1,
            datetime.now().isoformat()
        ))
    
    # Seed planning_alerts
    print("  - Creating alerts...")
    alert_types = ['STOCKOUT', 'LOW_COVERAGE', 'OVERSTOCK', 'SUPPLIER_DELAY', 'FORECAST_DEVIATION']
    for i in range(15):
        db.execute("""
            INSERT INTO planning_alerts
            (alert_type, severity, item_id, message, is_acknowledged, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            random.choice(alert_types),
            random.choice(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']),
            random.choice(items)[0] if items else None,
            f"Alert message {i+1}",
            0,
            datetime.now().isoformat()
        ))
    
    # Seed planning_kpi_records
    print("  - Creating KPI records...")
    kpi_types = ['FILL_RATE', 'STOCKOUT_RATE', 'FORECAST_ACCURACY', 'AVG_DOI', 'INVENTORY_TURNOVER']
    for i in range(30):
        db.execute("""
            INSERT INTO planning_kpi_records
            (kpi_type, value, period_start, entity_type, entity_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            random.choice(kpi_types),
            round(random.uniform(0.7, 0.99), 2),
            (datetime.now() - timedelta(days=i*7)).strftime('%Y-%m-%d'),
            'COMPANY',
            1,
            datetime.now().isoformat()
        ))
    
    # Seed planning_item_profiles (if not exists)
    print("  - Creating item profiles...")
    if items:
        for item in items:
            item_id = item[0]
            existing = db.execute(
                "SELECT id FROM planning_item_profiles WHERE item_id = ?", (item_id,)
            ).fetchone()
            if not existing:
                db.execute("""
                    INSERT INTO planning_item_profiles
                    (item_id, reorder_point, reorder_quantity, safety_stock,
                     min_stock, max_stock, lead_time_days, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item_id,
                    random.randint(20, 50),
                    random.randint(50, 200),
                    random.randint(10, 30),
                    random.randint(5, 20),
                    random.randint(200, 500),
                    random.randint(3, 14),
                    1,
                    datetime.now().isoformat()
                ))
    
    conn.commit()
    conn.close()
    
    print("SCM data seeded successfully!")


if __name__ == "__main__":
    seed_scm_data()
