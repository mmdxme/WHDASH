# SCM Sample Data

## Overview

This document describes the sample data available for testing and demonstration of the SCM module.

## Sample Data Categories

### 1. Items and Products

```sql
-- Active items with various categories
INSERT INTO wms_items (item_code, name, category_id, unit_cost, is_active)
VALUES
  ('SKU-001', 'Widget A (Standard)', 1, 25.00, 1),
  ('SKU-002', 'Widget B (Premium)', 1, 45.00, 1),
  ('SKU-003', 'Gadget X (Basic)', 2, 35.00, 1),
  ('SKU-004', 'Gadget Y (Advanced)', 2, 75.00, 1),
  ('SKU-005', 'Component Z-100', 3, 12.50, 1);
```

### 2. Demand History

```sql
-- 12 months of daily demand data
INSERT INTO planning_demand_history 
(item_id, warehouse_id, company_id, period_type, period_start, sales_quantity, consumption_quantity, order_count)
VALUES
  (1, 1, 1, 'daily', DATE('now', '-30 days'), 45, 5, 12),
  (1, 1, 1, 'daily', DATE('now', '-29 days'), 52, 3, 15),
  -- ... continues for all items
```

### 3. Forecast Runs

```sql
-- Sample forecast runs
INSERT INTO planning_forecast_runs 
(run_name, forecast_type, method, horizon_days, status, total_items, created_by)
VALUES
  ('Q2 Forecast - Moving Average', 'DEMAND', 'MOVING_AVERAGE', 90, 'APPROVED', 150, 1),
  ('Q2 Forecast - Exponential', 'DEMAND', 'EXPONENTIAL_SMOOTHING', 90, 'DRAFT', 150, 1),
  ('Spring Seasonality Forecast', 'DEMAND', 'MOVING_AVERAGE', 60, 'DRAFT', 75, 2);
```

### 4. Replenishment Recommendations

```sql
-- Sample replenishment recommendations
INSERT INTO planning_replenishment_recommendations
(item_id, warehouse_id, recommendation_type, action, priority, current_stock, 
 forecasted_demand, recommended_quantity, recommended_date, status)
VALUES
  (1, 1, 'STOCK_REPLENISHMENT', 'PURCHASE', 85, 150, 1200, 500, DATE('now', '+7 days'), 'OPEN'),
  (3, 1, 'STOCK_REPLENISHMENT', 'TRANSFER', 70, 80, 600, 200, DATE('now', '+3 days'), 'APPROVED');
```

### 5. MRP Purchase Suggestions

```sql
-- Sample purchase recommendations
INSERT INTO planning_purchase_recommendations
(item_id, supplier_id, recommendation_type, action, priority, current_stock,
 forecasted_demand, recommended_quantity, suggested_order_date, estimated_total_cost, status)
VALUES
  (2, 1, 'NORMAL', 'PURCHASE', 90, 50, 1800, 750, DATE('now', '+5 days'), 33750.00, 'OPEN'),
  (4, 2, 'EMERGENCY', 'PURCHASE', 100, 10, 600, 300, DATE('now', '+1 days'), 22500.00, 'OPEN');
```

### 6. Planning Alerts

```sql
-- Sample alerts
INSERT INTO planning_alerts
(alert_type, severity, title, message, item_id, warehouse_id)
VALUES
  ('STOCKOUT', 'CRITICAL', 'Stockout: SKU-003', 'Item SKU-003 has zero stock', 3, 1),
  ('SAFETY_STOCK_BREACH', 'HIGH', 'Below Safety: SKU-001', 'Stock below safety level', 1, 1),
  ('REORDER_POINT_BREACH', 'MEDIUM', 'Below ROP: SKU-004', 'Stock below reorder point', 4, 1),
  ('FORECAST_DEVIATION', 'LOW', 'High Forecast Variance: SKU-002', 'Actual 30% below forecast', 2, NULL);
```

### 7. Planning Scenarios

```sql
-- Sample scenarios
INSERT INTO planning_scenarios
(name, description, scenario_type, parameters_json, is_active, total_impact_items)
VALUES
  ('Demand Spike +20%', 'What if demand increases by 20%?', 'DEMAND_SPIKE',
   '{"demand_increase_pct": 20}', 1, 45),
  ('Supplier Delay 2 Weeks', 'Impact of major supplier delay', 'SUPPLIER_DELAY',
   '{"supplier_id": 1, "delay_days": 14}', 1, 30),
  ('Lead Time Increase', 'Impact of lead time increase', 'LEAD_TIME_INCREASE',
   '{"lead_time_increase_pct": 50}', 1, 25);
```

### 8. Supplier Performance

```sql
-- Sample supplier performance data
INSERT INTO planning_supplier_performance
(supplier_id, period_type, period_start, total_orders, on_time_count, fill_rate, avg_lead_time_days)
VALUES
  (1, 'MONTHLY', DATE('now', '-1 month'), 25, 22, 0.88, 8.5),
  (2, 'MONTHLY', DATE('now', '-1 month'), 18, 17, 0.94, 6.2),
  (1, 'MONTHLY', DATE('now', '-2 months'), 22, 20, 0.91, 9.0);
```

### 9. Inventory Balances

```sql
-- Sample inventory balances
INSERT INTO wms_inventory_balances
(item_id, warehouse_id, company_id, quantity, reserved, allocated)
VALUES
  (1, 1, 1, 500, 50, 25),
  (2, 1, 1, 200, 20, 10),
  (3, 1, 1, 0, 0, 5),    -- Stockout example
  (4, 1, 1, 800, 30, 15),  -- Overstock example
  (5, 2, 1, 300, 10, 5);
```

### 10. Customer Demand Patterns

```sql
-- Sample customer patterns
INSERT INTO planning_customer_demand_patterns
(customer_id, item_id, total_orders, total_quantity, avg_order_quantity, demand_trend, is_key_customer)
VALUES
  (1, 1, 45, 2250, 50, 'STABLE', 1),
  (2, 1, 30, 1200, 40, 'TREND_UP', 1),
  (3, 2, 15, 450, 30, 'STABLE', 0);
```

### 11. Lost Sales

```sql
-- Sample lost sales data
INSERT INTO planning_lost_sales
(item_id, customer_id, lost_date, requested_quantity, fulfilled_quantity, lost_quantity, lost_value, lost_reason)
VALUES
  (3, 1, DATE('now', '-5 days'), 100, 0, 100, 3500.00, 'STOCKOUT'),
  (1, 2, DATE('now', '-10 days'), 50, 30, 20, 500.00, 'PARTIAL_STOCKOUT');
```

### 12. Inbound Receipts (Supply Pipeline)

```sql
-- Sample inbound receipts
INSERT INTO wms_inbound_receipts
(item_id, supplier_id, warehouse_id, quantity, status, expected_arrival_date)
VALUES
  (1, 1, 1, 500, 'IN_TRANSIT', DATE('now', '+3 days')),
  (2, 1, 1, 200, 'APPROVED', DATE('now', '+7 days')),
  (4, 2, 1, 100, 'SENT', DATE('now', '+2 days'));
```

## Demo Scenarios

### Scenario 1: Active Stockout Response
1. SKU-003 has zero stock
2. System generates shortage alert
3. Planner reviews MRP suggestions
4. Emergency PO created and approved
5. Stock replenished

### Scenario 2: Demand Spike Planning
1. Marketing plans 20% promotion
2. Demand planner creates what-if scenario
3. System calculates required stock
4. Replenishment recommendations generated
5. Purchase orders approved

### Scenario 3: Supplier Delay Mitigation
1. Key supplier reports 2-week delay
2. Planner runs supplier delay scenario
3. System identifies affected items
4. Alternative sourcing recommendations
5. Transfer suggestions between warehouses

## Test Users

| User | Role | Branches |
|------|------|----------|
| admin | SCM Admin | All |
| planner1 | Demand Planner | Branch 1 |
| planner2 | Supply Planner | Branch 1, 2 |
| executor | Replenishment Executor | All |
| viewer | Executive Viewer | All |

## Data Volume Guidelines

| Table | Recommended Test Size |
|-------|---------------------|
| planning_demand_history | 5,000+ rows |
| planning_forecast_lines | 2,000+ rows |
| planning_alerts | 100+ rows |
| planning_replenishment_recommendations | 50+ rows |
| planning_purchase_recommendations | 100+ rows |
