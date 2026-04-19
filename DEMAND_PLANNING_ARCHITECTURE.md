# WHDASH Demand Planning Architecture

## Overview

The WHDASH Enterprise Demand Planning module provides comprehensive demand forecasting, collaborative planning, and inventory optimization capabilities. It is built as an integral part of the WHDASH ERP system, fully integrated with SCM, Procurement, WMS, Sales, Marketing, Finance, Workflow, and Flow modules.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │  Control    │ │  Forecast   │ │ Statistical │ │  Accuracy   │       │
│  │  Tower      │ │  Center     │ │ Forecasting │ │  Dashboard  │       │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │  Demand     │ │  Scenario   │ │ Consensus   │ │  Exception  │       │
│  │  Sensing    │ │  Planning   │ │  Planning   │ │  Management │       │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          BUSINESS LOGIC LAYER                            │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                   PLANNING_MODELS.PY                              │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │   │
│  │  │ Statistical │ │  Accuracy   │ │  Demand     │               │   │
│  │  │ Forecasting │ │  Engine     │ │  Sensing    │               │   │
│  │  │ Engine     │ │             │ │  Engine    │               │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘               │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │   │
│  │  │  Version    │ │  Override   │ │ Consensus   │               │   │
│  │  │  Management│ │  Workflow   │ │  Planning   │               │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘               │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │   │
│  │  │  Scenario   │ │  Alert     │ │   Flow     │               │   │
│  │  │  Planning   │ │  Generation│ │ Integration│               │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            DATA LAYER                                   │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    PLANNING_TABLES_SQL                            │   │
│  │  Core Tables           │ Enterprise Tables                       │   │
│  │  ─────────────────────┼─────────────────────────────────────    │   │
│  │  demand_history       │ forecast_versions                       │   │
│  │  sales_history        │ forecast_version_lines                  │   │
│  │  item_profiles        │ consensus_forecasts                    │   │
│  │  policies             │ consensus_comments                      │   │
│  │  policy_assignments   │ demand_drivers                         │   │
│  │  forecast_runs        │ promotion_impact                       │   │
│  │  forecast_lines       │ seasonality_profiles                    │   │
│  │  forecast_overrides   │ holiday_calendar                       │   │
│  │  replenishment_rec    │ forecast_accuracy                      │   │
│  │  purchase_rec         │ forecast_bias                          │   │
│  │  transfer_rec         │ model_performance                      │   │
│  │  scenarios            │ demand_signals                         │   │
│  │  scenario_lines       │ volatility_alerts                      │   │
│  │  alerts               │ override_approvals                     │   │
│  │  kpi_records          │ sla_policies                           │   │
│  │  audit_log            │ approval_matrix                        │   │
│  │  settings             │ flow_notifications                    │   │
│  │  lost_sales           │ forecast_attributes                    │   │
│  │  customer_patterns     │                                        │   │
│  │  supplier_performance  │                                        │   │
│  │  user_permissions     │                                        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Statistical Forecasting Engine

**Location:** `planning_models.py` - lines 1872-2100+

**Methods Supported:**
- `calculate_moving_average()` - Simple N-period moving average
- `calculate_weighted_moving_average()` - Linear weight decay
- `calculate_exponential_smoothing()` - Single exponential smoothing (SES)
- `calculate_double_exponential_smoothing()` - Holt's method for trends
- `calculate_triple_exponential_smoothing()` - Holt-Winters for seasonality
- `calculate_regression_forecast()` - Linear regression
- `auto_select_forecast_method()` - Automatic best-fit selection

**Configuration:**
```python
FORECAST_METHODS = [
    'MOVING_AVERAGE',
    'WEIGHTED_MOVING_AVERAGE',
    'EXPONENTIAL_SMOOTHING',
    'DOUBLE_EXPONENTIAL',
    'HOLT_WINTERS',
    'AUTO'
]
```

### 2. Forecast Accuracy Engine

**Location:** `planning_models.py` - lines 2101-2300+

**Metrics Calculated:**
- MAPE (Mean Absolute Percentage Error)
- WAPE (Weighted Absolute Percentage Error)
- MAE (Mean Absolute Error)
- RMSE (Root Mean Square Error)
- Bias (Forecast - Actual / Actual)
- Tracking Signal (Cumulative Error / MAD)
- Theil's U Statistic

**Functions:**
- `calculate_mape()` - Per-item or aggregate MAPE
- `calculate_wape()` - Weighted aggregate accuracy
- `calculate_mae()` - Mean absolute error
- `calculate_rmse()` - Root mean square error
- `calculate_bias()` - Forecast bias direction and magnitude
- `calculate_tracking_signal()` - Cumulative bias monitoring
- `calculate_theil_u()` - Naive forecast comparison
- `calculate_forecast_accuracy_metrics()` - Comprehensive metrics
- `calculate_item_forecast_accuracy()` - Per-item accuracy storage
- `calculate_forecast_bias_by_planner()` - Attribution tracking

### 3. Version Management

**Location:** `planning_models.py` - lines 2301-2450+

**Version Lifecycle:**
1. DRAFT - Initial working version
2. FROZEN - Immutable, locked for reference
3. PUBLISHED - Available for replenishment
4. APPROVED - Final approved version

**Functions:**
- `create_forecast_version()` - Snapshot from forecast run
- `clone_forecast_version()` - Copy existing version
- `freeze_forecast_version()` - Lock version
- `publish_forecast_version()` - Release for use
- `compare_forecast_versions()` - Diff analysis

### 4. Override Workflow

**Location:** `planning_models.py` - lines 2451-2550+

**Override Types:**
- MANUAL - Individual planner adjustment
- BULK - Mass override by criteria
- SALES_INPUT - Sales team adjustment
- MARKETING - Marketing adjustment
- PROMOTION - Promotional override
- EVENT - Event-based override

**Approval States:**
- PENDING - Awaiting approval
- APPROVED - Accepted
- REJECTED - Not accepted

### 5. Consensus Planning

**Location:** `planning_models.py` - lines 2551-2700+

**Collaborative Inputs:**
- Sales forecast input
- Planner baseline input
- Marketing projection
- Automatic consensus calculation
- Disagreement detection and escalation

**Disagreement Levels:**
- LOW - < 20% variance
- MEDIUM - 20-50% variance
- HIGH - > 50% variance

### 6. Demand Sensing

**Location:** `planning_models.py` - lines 2701-2850+

**Detection Methods:**
- Volatility Analysis (Coefficient of Variation)
- Z-Score Anomaly Detection
- Spike/Drop Detection
- Short-term Signal Recording

**Alert Types:**
- HIGH_VOLATILITY - CV > threshold
- DEMAND_SPIKE - Sudden increase
- DEMAND_DROP - Sudden decrease

### 7. Scenario Planning

**Location:** `planning_models.py` - lines 2851-2950+

**Scenario Types:**
- PROMOTION - Uplift scenario
- DEMAND_SPIKE - Increase scenario
- DEMAND_DROP - Decrease scenario
- PRICE_CHANGE - Elasticity scenario
- SUPPLY_CONSTRAINT - Limitation scenario
- SEASON_SHIFT - Pattern change scenario

## Data Flow

```
                    ┌──────────────────┐
                    │  WMS Inventory  │
                    │     Ledger       │
                    └────────┬─────────┘
                             │
                             ▼
              ┌──────────────────────────┐
              │  Demand Aggregation     │
              │  (aggregate_demand_    │
              │   from_ledger)        │
              └────────┬───────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Statistical │ │   Demand     │ │  Sales      │
│ Forecasting  │ │   Sensing    │ │  History    │
└──────┬───────┘ └──────────────┘ └──────────────┘
       │
       ▼
┌──────────────────┐
│ Forecast Runs    │
│ (planning_       │
│ forecast_runs)   │
└──────┬───────────┘
       │
       ├────────────────────────┬─────────────────────┐
       │                        │                     │
       ▼                        ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Override   │      │   Version    │      │  Consensus   │
│  Workflow   │      │  Management  │      │  Planning   │
└──────┬──────┘      └──────┬───────┘      └──────┬──────┘
       │                     │                      │
       └────────────────────┼──────────────────────┘
                            │
                            ▼
              ┌──────────────────────────┐
              │   Approved Forecast      │
              │   (FROZEN/PUBLISHED)     │
              └─────────────┬─────────────┘
                            │
        ┌──────────────────┼──────────────────┐
        │                  │                   │
        ▼                  ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Replenishment│   │  Procurement  │   │  SCM / MRP  │
│  Planning    │   │  Suggestions │   │   Engine    │
└──────────────┘   └──────────────┘   └──────────────┘
```

## Integration Points

### WMS Integration
- Demand aggregation from inventory ledger
- Current stock context for replenishment
- Warehouse-specific forecasting

### Procurement Integration
- Forecast-driven purchase recommendations
- Supplier lead time consideration
- Budget impact assessment

### SCM/Replenishment Integration
- Forecast-to-replenishment handoff
- Coverage impact analysis
- Branch refill risk assessment

### Sales Integration
- Sales history for forecasting input
- Sales forecast collaboration
- Campaign impact tracking

### Marketing Integration
- Promotion planning and impact
- Marketing campaign demand signals
- Seasonal calendar integration

### Flow Integration
- Alert notifications
- Approval routing
- Escalation management
- Collaboration threads

## Route Structure

**Main Routes (scm_routes.py):**
- `/scm/demand` - Demand planning overview
- `/scm/demand/control-tower` - Command center
- `/scm/demand/forecast-center` - Forecast generation
- `/scm/demand/statistical` - Statistical methods
- `/scm/demand/versions/list` - Version management
- `/scm/demand/versions/<id>` - Version detail
- `/scm/demand/overrides/list` - Override management
- `/scm/demand/accuracy/dashboard` - Accuracy metrics
- `/scm/demand/sensing` - Demand sensing
- `/scm/demand/scenarios` - What-if planning
- `/scm/demand/exceptions` - Exception queue
- `/scm/demand/consensus` - Collaborative planning
- `/scm/demand/drivers` - Demand drivers
- `/scm/demand/approvals` - Approval workflow
- `/scm/demand/settings` - Configuration

## Permission Model

**Roles Defined:**
- DEMAND_PLANNING_ADMIN - Full system access
- DEMAND_PLANNING_MANAGER - Management functions
- DEMAND_PLANNER - Forecast creation/modification
- SALES_CONTRIBUTOR - Sales forecast input
- MARKETING_CONTRIBUTOR - Marketing forecast input
- BRANCH_PLANNER - Branch-specific access
- EXECUTIVE_VIEWER - Read-only dashboards
- AUDITOR - Audit trail access

**Resource Actions:**
```
planning.forecasts:        view, create, edit, delete, approve, override
planning.statistical:      view, create, edit, delete, run
planning.versions:        view, create, edit, delete, freeze, publish, clone, compare
planning.overrides:       view, create, edit, delete, approve, reject, bulk_override
planning.demand_drivers:  view, create, edit, delete
planning.consensus:       view, create, edit, delete, approve, input
planning.accuracy:         view, create, calculate
planning.sensing:         view, create, detect, acknowledge
planning.scenarios:       view, create, edit, delete, run, compare
planning.alerts:          view, create, edit, delete, resolve, acknowledge, escalate
planning.workflow:         view, create, edit, delete, approve, reject
planning.reports:         view, export, create, edit, delete
planning.settings:        view, edit
```

## Performance Considerations

### Forecasting Optimization
- Demand history limited to 12-24 months
- Indexing on item_id, period_start for fast lookup
- Batch processing for bulk forecast generation
- Lazy loading for large forecast datasets

### Accuracy Calculation
- Rolling window calculation (configurable 30/60/90 days)
- Periodic batch calculation vs. real-time
- Aggregation for portfolio-level metrics

### Scalability
- Database indexes on all foreign keys
- Pagination for large datasets (200 items per page)
- Efficient SQL queries with proper JOINs
- Connection pooling via Flask g object

## Future Enhancements

1. **ML-Based Forecasting**
   - Integration with scikit-learn for advanced models
   - LSTM/Neural Network for complex patterns
   - External factor integration (weather, economic)

2. **Demand Sensing Advanced**
   - Real-time point-of-sale integration
   - IoT sensor data incorporation
   - Social media signal mining

3. **S&OP Integration**
   - Executive review meeting workflows
   - Financial integration hooks
   - Capacity planning linkage

4. **Collaborative Features**
   - Real-time co-editing
   - Mobile planner app
   - Chat/inline comments on forecasts

## Technical Stack

- **Backend:** Flask, SQLite
- **Frontend:** Jinja2 templates, Tailwind CSS
- **Database:** SQLite with foreign key constraints
- **Authentication:** Session-based with role checks
- **Caching:** None (real-time calculations)
- **Logging:** planning_audit_log table

## File Locations

- Models: `planning_models.py`
- Routes: `scm_routes.py`
- Templates: `templates/scm/demand/*.html`
- Navigation: `navigation.py`
- Permissions: `permissions.py`
- Translations: `translations.py`
