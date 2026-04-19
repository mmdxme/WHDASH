"""
Seed script for Demand Planning sample data.
Run with: python seed_demand_planning.py

This script creates comprehensive sample data for the WHDASH Demand Planning module
including demand history, forecast runs, versions, overrides, demand drivers, accuracy
records, volatility alerts, scenarios, and consensus forecasts.
"""

import sqlite3
import random
import math
from datetime import datetime, timedelta
from contextlib import contextmanager

# Configuration
DB_PATH = 'whdash.db'
NUM_ITEMS = 50
NUM_WAREHOUSES = 3
MONTHS_HISTORY = 12
SEED = 42

random.seed(SEED)

# Seasonality factors by month (Electronics example)
ELECTRONICS_SEASONALITY = {
    1: 0.80, 2: 0.85, 3: 0.90, 4: 1.00, 5: 1.10, 6: 1.30,
    7: 1.25, 8: 1.35, 9: 1.15, 10: 1.00, 11: 1.20, 12: 1.50
}

# Furniture seasonality
FURNITURE_SEASONALITY = {
    1: 0.70, 2: 0.75, 3: 0.85, 4: 0.95, 5: 1.05, 6: 1.20,
    7: 1.15, 8: 1.10, 9: 0.95, 10: 0.90, 11: 1.30, 12: 1.60
}

# Categories and their base demand ranges
CATEGORIES = {
    'Electronics': {'base_range': (200, 600), 'seasonality': ELECTRONICS_SEASONALITY, 'cv_range': (0.15, 0.35)},
    'Furniture': {'base_range': (100, 400), 'seasonality': FURNITURE_SEASONALITY, 'cv_range': (0.20, 0.45)},
    'Packaging': {'base_range': (500, 1500), 'seasonality': {m: 1.0 for m in range(1, 13)}, 'cv_range': (0.10, 0.25)},
    'Chemicals': {'base_range': (150, 500), 'seasonality': {m: 1.0 for m in range(1, 13)}, 'cv_range': (0.25, 0.50)},
}


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_or_create_item(db, item_code, name, category, brand, unit_cost=100):
    """Get existing item or create new one."""
    item = db.execute("SELECT id FROM wms_items WHERE item_code = ?", (item_code,)).fetchone()
    if item:
        return item['id']

    cursor = db.execute("""
        INSERT INTO wms_items (item_code, name, category_id, unit_cost, is_active, created_at)
        VALUES (?, ?, NULL, ?, 1, CURRENT_TIMESTAMP)
    """, (item_code, name, unit_cost))
    return cursor.lastrowid


def get_or_create_warehouse(db, code, name):
    """Get existing warehouse or create new one."""
    wh = db.execute("SELECT id FROM wms_warehouses WHERE code = ?", (code,)).fetchone()
    if wh:
        return wh['id']

    cursor = db.execute("""
        INSERT INTO wms_warehouses (code, name, is_active, created_at)
        VALUES (?, ?, 1, CURRENT_TIMESTAMP)
    """, (code, name))
    return cursor.lastrowid


def seed_demand_history(db):
    """Seed demand history for the past 12 months."""
    print("Seeding demand history...")

    items_data = [
        ('ELEC-001', '4K Smart TV 55 inch', 'Electronics', 'TechPro', 599.99),
        ('ELEC-002', 'Wireless Headphones Pro', 'Electronics', 'TechPro', 149.99),
        ('ELEC-003', 'Laptop Stand Premium', 'Electronics', 'PowerMax', 79.99),
        ('ELEC-004', 'USB-C Hub 7-in-1', 'Electronics', 'PowerMax', 49.99),
        ('ELEC-005', 'Mechanical Keyboard RGB', 'Electronics', 'TechPro', 129.99),
        ('FURN-001', 'Ergonomic Office Chair', 'Furniture', 'ComfortLiving', 399.99),
        ('FURN-002', 'Standing Desk Electric', 'Furniture', 'ComfortLiving', 599.99),
        ('FURN-003', 'Monitor Arm Dual', 'Furniture', 'FlexiMount', 89.99),
        ('FURN-004', 'LED Desk Lamp', 'Furniture', 'BrightWork', 45.99),
        ('PACK-001', 'Corrugated Boxes 12x12x12', 'Packaging', 'PackPro', 2.99),
        ('PACK-002', 'Bubble Wrap Roll 100m', 'Packaging', 'PackPro', 34.99),
        ('PACK-003', 'Packing Tape 6 Pack', 'Packaging', 'PackPro', 14.99),
        ('CHEM-001', 'Industrial Cleaner 5L', 'Chemicals', 'ChemCo', 24.99),
        ('CHEM-002', 'Lubricant Spray 400ml', 'Chemicals', 'ChemCo', 8.99),
    ]

    warehouses = [
        ('WH-MAIN', 'Main Warehouse'),
        ('WH-EAST', 'East Distribution'),
        ('WH-WEST', 'West Distribution'),
    ]

    # Create warehouses
    wh_ids = []
    for code, name in warehouses:
        wh_ids.append(get_or_create_warehouse(db, code, name))

    # Create items
    item_ids = []
    item_info = {}
    for item_code, name, category, brand, unit_cost in items_data:
        item_id = get_or_create_item(db, item_code, name, category, brand, unit_cost)
        item_ids.append(item_id)
        cat_data = CATEGORIES.get(category, CATEGORIES['Electronics'])
        item_info[item_id] = {
            'category': category,
            'base_demand': random.uniform(*cat_data['base_range']),
            'seasonality': cat_data['seasonality'],
            'cv': random.uniform(*cat_data['cv_range'])
        }

    # Generate demand history
    start_date = datetime.now() - timedelta(days=MONTHS_HISTORY * 30)

    for item_id in item_ids:
        info = item_info[item_id]
        base_demand = info['base_demand']
        seasonality = info['seasonality']
        cv = info['cv']

        for day_offset in range(MONTHS_HISTORY * 30):
            date = start_date + timedelta(days=day_offset)
            month = date.month

            # Apply seasonality
            seasonal_factor = seasonality.get(month, 1.0)

            # Add randomness based on CV
            random_factor = random.gauss(1.0, cv)

            # Calculate daily demand
            daily_demand = max(0, base_demand * seasonal_factor * random_factor / 30)

            # Split into sales and consumption
            sales_qty = daily_demand * random.uniform(0.85, 0.95)
            consumption_qty = daily_demand * random.uniform(0.05, 0.15)

            # Random warehouse assignment
            warehouse_id = random.choice(wh_ids)

            # Customer and order counts
            customer_count = random.randint(1, max(1, int(sales_qty / 10)))
            order_count = random.randint(1, max(1, int(customer_count / 2)))

            try:
                db.execute("""
                    INSERT INTO planning_demand_history
                    (item_id, warehouse_id, company_id, period_type, period_start,
                     sales_quantity, consumption_quantity, customer_count, order_count)
                    VALUES (?, ?, 1, 'daily', ?, ?, ?, ?, ?)
                """, (item_id, warehouse_id, date.strftime('%Y-%m-%d'),
                      sales_qty, consumption_qty, customer_count, order_count))
            except sqlite3.IntegrityError:
                # Skip duplicates
                pass

    db.commit()
    print(f"  Created demand history for {len(item_ids)} items over {MONTHS_HISTORY} months")
    return item_ids, wh_ids


def seed_forecast_runs(db, item_ids):
    """Seed forecast runs with different methods."""
    print("Seeding forecast runs...")

    methods = ['MOVING_AVERAGE', 'WEIGHTED_MOVING_AVERAGE', 'EXPONENTIAL_SMOOTHING', 'DOUBLE_EXPONENTIAL', 'HOLT_WINTERS']

    runs = [
        ('Q1 2026 Baseline MA', 'MOVING_AVERAGE', 30, 'APPROVED'),
        ('Q1 2026 Weighted MA', 'WEIGHTED_MOVING_AVERAGE', 30, 'PUBLISHED'),
        ('Q1 2026 Exponential', 'EXPONENTIAL_SMOOTHING', 60, 'DRAFT'),
        ('Q1 2026 Seasonal', 'HOLT_WINTERS', 90, 'APPROVED'),
        ('Q2 2026 Auto Select', 'MOVING_AVERAGE', 30, 'DRAFT'),
    ]

    run_ids = []
    for run_name, method, horizon, status in runs:
        cursor = db.execute("""
            INSERT INTO planning_forecast_runs
            (run_name, forecast_type, method, horizon_days, period_type,
             status, created_by, total_items, total_demand)
            VALUES (?, 'DEMAND', ?, ?, 'daily', ?, 1, ?, ?)
        """, (run_name, method, horizon, status, len(item_ids), random.randint(10000, 100000) * horizon))
        run_id = cursor.lastrowid
        run_ids.append(run_id)

        # Create forecast lines for each item
        for item_id in item_ids[:20]:  # Only first 20 items for demo
            base_qty = random.uniform(100, 500)

            for day_offset in range(horizon):
                date = datetime.now() + timedelta(days=day_offset)
                seasonal_factor = ELECTRONICS_SEASONALITY.get(date.month, 1.0)
                final_qty = base_qty * seasonal_factor

                db.execute("""
                    INSERT INTO planning_forecast_lines
                    (run_id, item_id, warehouse_id, company_id, period_start, period_type,
                     base_quantity, seasonal_factor, final_quantity)
                    VALUES (?, ?, 1, 1, ?, 'daily', ?, ?, ?)
                """, (run_id, item_id, date.strftime('%Y-%m-%d'), base_qty, seasonal_factor, final_qty))

    db.commit()
    print(f"  Created {len(run_ids)} forecast runs")
    return run_ids


def seed_forecast_versions(db, run_ids):
    """Seed forecast versions."""
    print("Seeding forecast versions...")

    versions = [
        ('Q1 2026 Initial', 1, 'APPROVED', run_ids[0] if len(run_ids) > 0 else None, True),
        ('Q1 2026 Sales Adjusted', 2, 'PUBLISHED', run_ids[0] if len(run_ids) > 0 else None, False),
        ('Q1 2026 Final', 3, 'FROZEN', run_ids[0] if len(run_ids) > 0 else None, True),
        ('Q2 2026 Draft', 1, 'DRAFT', run_ids[4] if len(run_ids) > 4 else None, False),
    ]

    version_ids = []
    for name, number, status, run_id, is_baseline in versions:
        cursor = db.execute("""
            INSERT INTO planning_forecast_versions
            (version_name, version_number, status, forecast_run_id, is_baseline,
             total_items, total_quantity, created_by, published_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1)
        """, (name, number, status, run_id, 1 if is_baseline else 0,
              random.randint(10, 50), random.randint(100000, 500000)))
        version_ids.append(cursor.lastrowid)

    db.commit()
    print(f"  Created {len(version_ids)} forecast versions")
    return version_ids


def seed_overrides(db, item_ids):
    """Seed forecast overrides."""
    print("Seeding forecast overrides...")

    reasons = ['PROMOTION', 'MARKETING', 'SALES_INPUT', 'EVENT', 'SEASONALITY', 'STOCKOUT']
    types = ['MANUAL', 'BULK', 'MANUAL', 'MANUAL', 'MANUAL']

    overrides = []
    for i in range(15):
        item_id = random.choice(item_ids)
        period_date = datetime.now() + timedelta(days=random.randint(1, 30))
        original_qty = random.uniform(100, 500)
        override_pct = random.uniform(-0.25, 0.35)
        override_qty = original_qty * (1 + override_pct)

        status = random.choice(['APPROVED', 'APPROVED', 'APPROVED', 'PENDING', 'REJECTED'])

        cursor = db.execute("""
            INSERT INTO planning_forecast_overrides
            (item_id, warehouse_id, company_id, period_start, period_type,
             original_quantity, override_quantity, override_reason, override_type,
             status, created_by, reviewed_by, reviewed_at)
            VALUES (?, 1, 1, ?, 'daily', ?, ?, ?, ?, ?, 1,
                    2 if ? = 'APPROVED' else NULL, CURRENT_TIMESTAMP if ? = 'APPROVED' else NULL)
        """, (item_id, period_date.strftime('%Y-%m-%d'), original_qty, override_qty,
              random.choice(reasons), random.choice(types), status, status))

        override_id = cursor.lastrowid()

        # Create approval record
        if status in ['APPROVED', 'REJECTED']:
            db.execute("""
                INSERT INTO planning_override_approvals
                (override_id, approval_status, requested_by, requested_at, reviewed_by, reviewed_at)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP, 2, CURRENT_TIMESTAMP)
            """, (override_id, status))

        overrides.append(override_id)

    db.commit()
    print(f"  Created {len(overrides)} forecast overrides")
    return overrides


def seed_demand_drivers(db):
    """Seed demand drivers and promotions."""
    print("Seeding demand drivers...")

    drivers = [
        ('Summer Sale 2026', 'PROMOTION', 1.25, '2026-06-01', '2026-06-30'),
        ('Eid Festival', 'HOLIDAY', 1.40, '2026-06-15', '2026-06-20'),
        ('Back to School', 'CAMPAIGN', 1.15, '2026-08-01', '2026-09-15'),
        ('New Product Launch', 'EVENT', 1.30, '2026-05-01', '2026-05-31'),
        ('Price Increase Effect', 'PRICE_CHANGE', 0.85, '2026-04-01', '2026-04-30'),
    ]

    driver_ids = []
    for name, dtype, factor, start, end in drivers:
        cursor = db.execute("""
            INSERT INTO planning_demand_drivers
            (driver_name, driver_type, impact_factor, start_date, end_date,
             is_active, created_by)
            VALUES (?, ?, ?, ?, ?, 1, 1)
        """, (name, dtype, factor, start, end))
        driver_ids.append(cursor.lastrowid)

    db.commit()
    print(f"  Created {len(driver_ids)} demand drivers")
    return driver_ids


def seed_promotions(db):
    """Seed promotion impact records."""
    print("Seeding promotions...")

    promotions = [
        ('Summer Flash Sale', 'FLASH_SALE', '2026-06-15', '2026-06-25', 20, 5000),
        ('Eid Special Offer', 'SPECIAL_OFFER', '2026-06-15', '2026-06-20', 25, 8000),
        ('Back to School Bundle', 'BUNDLE', '2026-08-01', '2026-09-05', 15, 12000),
    ]

    promo_ids = []
    for name, ptype, start, end, uplift, budget in promotions:
        cursor = db.execute("""
            INSERT INTO planning_promotion_impact
            (promotion_name, promotion_type, start_date, end_date,
             expected_uplift_percent, budget_allocated, status, created_by)
            VALUES (?, ?, ?, ?, ?, ?, 'PLANNED', 1)
        """, (name, ptype, start, end, uplift, budget))
        promo_ids.append(cursor.lastrowid)

    db.commit()
    print(f"  Created {len(promo_ids)} promotions")
    return promo_ids


def seed_forecast_accuracy(db, item_ids):
    """Seed forecast accuracy records."""
    print("Seeding forecast accuracy...")

    accuracy_records = 0
    for item_id in item_ids[:20]:
        for month_offset in range(6):
            period_date = datetime.now() - timedelta(days=30 * month_offset)
            forecast_qty = random.uniform(4000, 8000)
            actual_qty = forecast_qty * random.uniform(0.85, 1.15)
            error = actual_qty - forecast_qty
            mape = abs(error / forecast_qty * 100) if forecast_qty != 0 else 0
            bias = error / forecast_qty * 100 if forecast_qty != 0 else 0

            try:
                db.execute("""
                    INSERT INTO planning_forecast_accuracy
                    (item_id, warehouse_id, company_id, period_start, period_type,
                     forecast_quantity, actual_quantity, error_quantity, absolute_error,
                     mape, bias)
                    VALUES (?, 1, 1, ?, 'monthly', ?, ?, ?, ?, ?, ?)
                """, (item_id, period_date.strftime('%Y-%m-%d'), forecast_qty,
                      actual_qty, error, abs(error), mape, bias))
                accuracy_records += 1
            except sqlite3.IntegrityError:
                pass

    db.commit()
    print(f"  Created {accuracy_records} accuracy records")
    return accuracy_records


def seed_volatility_alerts(db, item_ids):
    """Seed volatility alerts."""
    print("Seeding volatility alerts...")

    alerts = [
        ('DEMAND_SPIKE', 'HIGH', 3.2, 0.78),
        ('DEMAND_DROP', 'MEDIUM', -2.4, 0.55),
        ('HIGH_VOLATILITY', 'HIGH', None, 0.85),
        ('DEMAND_SPIKE', 'LOW', 2.1, 0.45),
    ]

    alert_ids = []
    for item_id in item_ids[:4]:
        alert_type, severity, z_score, cv = alerts[len(alert_ids) % len(alerts)]

        cursor = db.execute("""
            INSERT INTO planning_volatility_alerts
            (item_id, warehouse_id, alert_type, severity, threshold_value,
             actual_value, cv_value, z_score)
            VALUES (?, 1, ?, ?, 2.0, ?, ?, ?)
        """, (item_id, alert_type, severity,
              random.uniform(500, 1000) if z_score else None, cv, z_score))
        alert_ids.append(cursor.lastrowid)

    db.commit()
    print(f"  Created {len(alert_ids)} volatility alerts")
    return alert_ids


def seed_scenarios(db, item_ids):
    """Seed scenario planning records."""
    print("Seeding scenarios...")

    scenarios = [
        ('Summer Promo 15%', 'PROMOTION', 15, 50),
        ('Summer Promo 20%', 'PROMOTION', 20, 50),
        ('Demand Drop 10%', 'DEMAND_DROP', -10, 50),
        ('New Customer Win', 'DEMAND_SPIKE', 25, 10),
        ('Price Increase Effect', 'PRICE_CHANGE', -5, 30),
    ]

    scenario_ids = []
    for name, stype, uplift, items_count in scenarios:
        cursor = db.execute("""
            INSERT INTO planning_scenarios
            (name, description, scenario_type, parameters_json, is_active,
             total_impact_items, total_cost_impact, created_by)
            VALUES (?, ?, ?, ?, 1, ?, ?, 1)
        """, (name, f"What-if scenario: {uplift}% change", stype,
              f'{{"uplift_percent": {uplift}}}', items_count,
              random.randint(50000, 200000)))
        scenario_id = cursor.lastrowid
        scenario_ids.append(scenario_id)

        # Create scenario lines
        for item_id in item_ids[:items_count]:
            base_value = random.uniform(1000, 5000)
            impact_value = base_value * uplift / 100
            scenario_value = base_value + impact_value

            db.execute("""
                INSERT INTO planning_scenario_lines
                (scenario_id, item_id, warehouse_id, company_id, metric_name,
                 base_value, scenario_value, impact_value, impact_percent)
                VALUES (?, ?, 1, 1, 'DEMAND', ?, ?, ?, ?)
            """, (scenario_id, item_id, base_value, scenario_value,
                  impact_value, uplift))

    db.commit()
    print(f"  Created {len(scenario_ids)} scenarios")
    return scenario_ids


def seed_consensus_forecasts(db, item_ids):
    """Seed consensus planning records."""
    print("Seeding consensus forecasts...")

    consensus_ids = []
    for item_id in item_ids[:10]:
        sales_input = random.uniform(4000, 6000)
        planner_input = random.uniform(3800, 5800)
        marketing_input = random.uniform(4200, 6500)

        inputs = [sales_input, planner_input, marketing_input]
        consensus_value = sum(inputs) / len(inputs)
        max_diff = max(inputs) - min(inputs)
        avg_val = sum(inputs) / len(inputs)
        diff_pct = max_diff / avg_val if avg_val != 0 else 0

        if diff_pct > 0.5:
            disagreement = 'HIGH'
        elif diff_pct > 0.2:
            disagreement = 'MEDIUM'
        else:
            disagreement = 'LOW'

        cursor = db.execute("""
            INSERT INTO planning_consensus_forecasts
            (version_id, item_id, period_start, sales_input, planner_input,
             marketing_input, consensus_value, status, disagreement_level,
             created_by, company_id)
            VALUES (1, ?, ?, ?, ?, ?, ?, 'DRAFT', ?, 1, 1)
        """, (item_id, datetime.now().strftime('%Y-%m-%d'),
              sales_input, planner_input, marketing_input, consensus_value, disagreement))
        consensus_ids.append(cursor.lastrowid)

    db.commit()
    print(f"  Created {len(consensus_ids)} consensus forecasts")
    return consensus_ids


def seed_flow_notifications(db):
    """Seed Flow integration notifications."""
    print("Seeding Flow notifications...")

    notifications = [
        ('FORECAST_ALERT_HIGH_VOLATILITY', 'High Volatility Detected', 'Item ELEC-001 showing unusual demand pattern', 'volatility_alert', None, 'HIGH'),
        ('PENDING_APPROVAL', 'Override Pending Approval', 'Forecast override for ELEC-002 requires approval', 'override', None, 'NORMAL'),
        ('EXCEPTION_ESCALATION', 'Exception Escalated', 'Critical forecast deviation alert for FURN-001', 'exception', None, 'HIGH'),
    ]

    notif_ids = []
    for ntype, title, message, entity_type, entity_id, priority in notifications:
        cursor = db.execute("""
            INSERT INTO planning_flow_notifications
            (notification_type, title, message, entity_type, entity_id,
             priority, created_by, company_id)
            VALUES (?, ?, ?, ?, ?, ?, 1, 1)
        """, (ntype, title, message, entity_type, entity_id, priority))
        notif_ids.append(cursor.lastrowid)

    db.commit()
    print(f"  Created {len(notif_ids)} Flow notifications")
    return notif_ids


def main():
    """Main seeding function."""
    print("=" * 60)
    print("WHDASH Demand Planning Sample Data Seeder")
    print("=" * 60)

    with get_db_connection() as db:
        print("\nStarting seed process...")

        # Seed all data
        item_ids, wh_ids = seed_demand_history(db)
        run_ids = seed_forecast_runs(db, item_ids)
        version_ids = seed_forecast_versions(db, run_ids)
        override_ids = seed_overrides(db, item_ids)
        driver_ids = seed_demand_drivers(db)
        promo_ids = seed_promotions(db)
        accuracy_count = seed_forecast_accuracy(db, item_ids)
        alert_ids = seed_volatility_alerts(db, item_ids)
        scenario_ids = seed_scenarios(db, item_ids)
        consensus_ids = seed_consensus_forecasts(db, item_ids)
        notif_ids = seed_flow_notifications(db)

        print("\n" + "=" * 60)
        print("Seeding Complete!")
        print("=" * 60)
        print(f"""
Summary:
  - Items with demand history: {len(item_ids)}
  - Warehouses: {len(wh_ids)}
  - Forecast runs: {len(run_ids)}
  - Forecast versions: {len(version_ids)}
  - Forecast overrides: {len(override_ids)}
  - Demand drivers: {len(driver_ids)}
  - Promotions: {len(promo_ids)}
  - Accuracy records: {accuracy_count}
  - Volatility alerts: {len(alert_ids)}
  - Scenarios: {len(scenario_ids)}
  - Consensus forecasts: {len(consensus_ids)}
  - Flow notifications: {len(notif_ids)}
        """)


if __name__ == '__main__':
    main()
