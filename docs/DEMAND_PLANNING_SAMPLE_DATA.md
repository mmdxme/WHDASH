# Demand Planning Sample Data Guide

## Overview

This document describes the sample/demo data for the WHDASH Demand Planning module, including data structure, generation scripts, and intended scenarios.

## Sample Data Structure

### 1. Demand History

```sql
-- 12 months of daily demand data for 50 items
INSERT INTO planning_demand_history
(item_id, warehouse_id, company_id, period_type, period_start, 
 sales_quantity, consumption_quantity, customer_count, order_count)
VALUES 
(1, 1, 1, 'daily', '2025-04-17', 150.5, 10.0, 12, 8),
(1, 1, 1, 'daily', '2025-04-18', 142.0, 8.5, 10, 7),
-- ... continuing for 365 days per item
```

### 2. Items Profile

Sample items with varying characteristics:

| Item Code | Category | Brand | ABC | XYZ | Planning Method | Seasonal |
|-----------|----------|-------|-----|-----|----------------|----------|
| ELEC-001 | Electronics | TechPro | A | X | AUTO | Yes |
| ELEC-002 | Electronics | TechPro | A | Y | MOVING_AVERAGE | No |
| ELEC-003 | Electronics | PowerMax | B | Z | WEIGHTED_MA | No |
| FURN-001 | Furniture | ComfortLiving | A | X | AUTO | Yes |
| FURN-002 | Furniture | ComfortLiving | B | Y | EXPONENTIAL | Yes |
| PACK-001 | Packaging | PackPro | C | Z | MOVING_AVERAGE | No |
| CHEM-001 | Chemicals | ChemCo | B | Y | AUTO | No |

### 3. Forecast Runs

Sample forecast runs demonstrating various methods:

| Run Name | Method | Horizon | Items | Status |
|----------|--------|---------|-------|--------|
| Q1 2026 Baseline | MOVING_AVERAGE | 30 | 50 | APPROVED |
| Q1 2026 Weighted | WEIGHTED_MOVING_AVERAGE | 30 | 50 | PUBLISHED |
| Q1 2026 Exponential | EXPONENTIAL_SMOOTHING | 60 | 50 | DRAFT |
| Q1 2026 Seasonal | HOLT_WINTERS | 90 | 25 | APPROVED |
| Q1 2026 Auto | AUTO | 30 | 50 | DRAFT |

### 4. Forecast Versions

| Version Name | Number | Status | Items | Total Qty |
|-------------|--------|---------|-------|-----------|
| Q1 2026 Initial | 1 | APPROVED | 50 | 1,250,000 |
| Q1 2026 Sales Adjusted | 2 | PUBLISHED | 50 | 1,275,000 |
| Q1 2026 Final | 3 | FROZEN | 50 | 1,260,000 |
| Q2 2026 Draft | 1 | DRAFT | 50 | 1,300,000 |

### 5. Override Examples

| Item | Period | Original | Override | Reason | Status |
|------|--------|----------|----------|--------|--------|
| ELEC-001 | 2026-02-15 | 200 | 250 | PROMOTION | APPROVED |
| FURN-001 | 2026-03-01 | 180 | 220 | MARKETING | APPROVED |
| ELEC-002 | 2026-02-20 | 150 | 130 | SALES_INPUT | PENDING |
| PACK-001 | 2026-03-15 | 500 | 450 | STOCKOUT_CORRECTION | APPROVED |

### 6. Demand Drivers

| Driver Name | Type | Impact Factor | Start Date | End Date |
|------------|------|---------------|------------|----------|
| Summer Sale 2026 | PROMOTION | 1.25 | 2026-06-01 | 2026-06-30 |
| Eid Festival | HOLIDAY | 1.40 | 2026-06-15 | 2026-06-20 |
| Back to School | CAMPAIGN | 1.15 | 2026-08-01 | 2026-09-15 |
| New Product Launch | EVENT | 1.30 | 2026-05-01 | 2026-05-31 |
| Price Increase | PRICE_CHANGE | 0.85 | 2026-04-01 | 2026-04-30 |

### 7. Seasonality Profiles

**Electronics Category Monthly Factors:**
| Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| 0.80 | 0.85 | 0.90 | 1.00 | 1.10 | 1.30 | 1.25 | 1.35 | 1.15 | 1.00 | 1.20 | 1.50 |

**Furniture Category Monthly Factors:**
| Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| 0.70 | 0.75 | 0.85 | 0.95 | 1.05 | 1.20 | 1.15 | 1.10 | 0.95 | 0.90 | 1.30 | 1.60 |

### 8. Forecast Accuracy Records

Sample accuracy data for demonstration:

| Item | Period | Forecast | Actual | MAPE | Bias |
|------|--------|----------|--------|------|------|
| ELEC-001 | 2026-01 | 6,000 | 5,800 | 3.4% | -3.3% |
| ELEC-001 | 2026-02 | 6,200 | 6,500 | 4.8% | +4.8% |
| ELEC-002 | 2026-01 | 4,500 | 4,200 | 6.7% | -6.7% |
| FURN-001 | 2026-01 | 5,400 | 5,600 | 3.7% | +3.7% |
| PACK-001 | 2026-01 | 15,000 | 14,200 | 5.3% | -5.3% |

### 9. Volatility Alerts

| Item | Alert Type | Severity | Z-Score | CV | Date |
|------|------------|----------|---------|-----|------|
| ELEC-003 | DEMAND_SPIKE | HIGH | 3.2 | 0.75 | 2026-04-10 |
| FURN-002 | DEMAND_DROP | MEDIUM | -2.4 | 0.55 | 2026-04-12 |
| CHEM-001 | HIGH_VOLATILITY | HIGH | - | 0.85 | 2026-04-08 |
| PACK-001 | DEMAND_SPIKE | LOW | 2.1 | 0.45 | 2026-04-15 |

### 10. Scenarios

| Scenario Name | Type | Uplift % | Items | Total Impact |
|---------------|------|----------|-------|--------------|
| Summer Promo 15% | PROMOTION | 15 | 50 | +187,500 |
| Summer Promo 20% | PROMOTION | 20 | 50 | +250,000 |
| Demand Drop 10% | DEMAND_DROP | -10 | 50 | -125,000 |
| New Customer | DEMAND_SPIKE | 25 | 10 | +62,500 |
| Price Increase | PRICE_CHANGE | -5 | 30 | -45,000 |

### 11. Consensus Forecasts

| Item | Sales Input | Planner Input | Marketing Input | Consensus | Disagreement |
|------|-------------|---------------|-----------------|-----------|--------------|
| ELEC-001 | 6,500 | 6,200 | 6,000 | 6,233 | LOW |
| FURN-001 | 5,800 | 5,400 | 5,600 | 5,600 | LOW |
| ELEC-002 | 4,800 | 4,200 | 5,000 | 4,667 | MEDIUM |
| CHEM-001 | 3,200 | 3,800 | 3,000 | 3,333 | HIGH |

## Data Generation Script

```python
"""
Seed script for Demand Planning sample data.
Run with: python seed_demand_planning.py
"""

import random
from datetime import datetime, timedelta
from database import get_db

def seed_demand_planning():
    db = get_db()
    
    # Seed demand history (12 months)
    print("Seeding demand history...")
    items = db.execute("SELECT id FROM wms_items LIMIT 50").fetchall()
    warehouses = db.execute("SELECT id FROM wms_warehouses").fetchall()
    
    start_date = datetime.now() - timedelta(days=365)
    
    for item in items:
        base_demand = random.randint(100, 500)
        for day_offset in range(365):
            date = start_date + timedelta(days=day_offset)
            # Add seasonality
            month_factor = get_seasonality_factor(item.id, date.month)
            # Add randomness
            qty = base_demand * month_factor * random.uniform(0.8, 1.2)
            
            db.execute("""
                INSERT INTO planning_demand_history
                (item_id, warehouse_id, period_type, period_start,
                 sales_quantity, consumption_quantity, order_count, customer_count)
                VALUES (?, ?, 'daily', ?, ?, ?, ?, ?)
            """, (item.id, warehouses[0].id, date.strftime('%Y-%m-%d'),
                  qty * 0.9, qty * 0.1, random.randint(5, 20), random.randint(3, 15)))
    
    db.commit()
    print("Demand history seeded.")

def get_seasonality_factor(item_id, month):
    # Simplified seasonality
    electronics_factors = {
        1: 0.80, 2: 0.85, 3: 0.90, 4: 1.00, 5: 1.10, 6: 1.30,
        7: 1.25, 8: 1.35, 9: 1.15, 10: 1.00, 11: 1.20, 12: 1.50
    }
    return electronics_factors.get(month, 1.0)

if __name__ == '__main__':
    seed_demand_planning()
```

## Scenarios for Demo

### 1. Basic Forecasting Demo
- Generate moving average forecast for ELEC-001
- Compare with weighted moving average
- Show forecast vs actuals

### 2. Override Workflow Demo
- Create manual override for promotion
- Route for approval
- Approve and verify

### 3. Version Management Demo
- Create draft version
- Freeze version
- Compare with previous approved version

### 4. Accuracy Analysis Demo
- Calculate MAPE for all items
- Identify high-error items
- Show bias analysis by planner

### 5. Demand Sensing Demo
- Run volatility detection
- Review spike/drop alerts
- Acknowledge and document

### 6. Scenario Planning Demo
- Create promotion scenario
- Apply 15% uplift
- Compare impacts

### 7. Consensus Planning Demo
- Enter sales input
- Enter planner input
- Resolve disagreement

## Test Users

| Username | Role | Permissions |
|----------|------|-------------|
| admin | ADMIN | Full access |
| dp_manager | DEMAND_PLANNING_MANAGER | All planning + approval |
| dp_planner1 | DEMAND_PLANNER | Create/edit forecasts |
| dp_planner2 | DEMAND_PLANNER | Create/edit forecasts |
| sales_user | SALES_CONTRIBUTOR | Sales forecast input |
| mkt_user | MARKETING_CONTRIBUTOR | Marketing forecast input |
| branch_user | BRANCH_PLANNER | Branch-restricted access |
| exec_user | EXECUTIVE_VIEWER | Read-only dashboards |
| auditor | AUDITOR | Audit trail access |

## Expected Outcomes

With full sample data loaded:

1. **Control Tower**: Shows 5 active forecasts, 12 pending overrides, 8 high-error items
2. **Forecast Center**: 5 forecast runs with various methods
3. **Accuracy Dashboard**: Average MAPE ~8.5%, 15 items > 20% MAPE
4. **Exceptions**: 25 total exceptions, 5 critical
5. **Versions**: 4 versions with clear lifecycle
6. **Scenarios**: 5 what-if scenarios demonstrating impact
