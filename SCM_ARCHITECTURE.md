# SCM Architecture Document

## Overview

The Supply Chain Management (SCM) module is an enterprise-grade supply chain operating platform that extends the existing Planning module. It provides comprehensive demand planning, supply planning, replenishment, MRP, inventory optimization, multi-echelon planning, service level management, scenario planning, and executive dashboards.

## Architecture Principles

1. **Planning-Driven**: All SCM decisions are based on demand forecasts and supply visibility
2. **Exception-Aware**: The system highlights problems requiring planner attention
3. **Inventory-Intelligent**: Stock levels are continuously monitored and optimized
4. **Integrated**: Deep integration with Procurement, WMS, Logistics, Finance, and Flow

## Module Structure

### Core Modules

#### 1. Supply Chain Control Tower
- **Purpose**: Central command center for supply chain visibility
- **Features**:
  - Global supply visibility
  - Stock health summary
  - Demand vs supply summary
  - Critical shortages view
  - Overstock risks
  - Service level breaches
  - In-transit supply pipeline
  - Planner action queue

#### 2. Demand Planning
- **Purpose**: Forecast and analyze customer demand
- **Features**:
  - Forecast Center (generate/manage forecasts)
  - Forecast by Item/Warehouse/Category
  - Forecast versions and comparison
  - Manual forecast overrides
  - Forecast accuracy tracking
  - Demand trend analysis
  - Seasonal adjustment support

#### 3. Supply Planning
- **Purpose**: Plan and monitor incoming supply
- **Features**:
  - Incoming supply pipeline
  - Open PO impact analysis
  - Supply risk identification
  - Coverage analysis
  - Lead time management
  - Supplier performance tracking

#### 4. Replenishment Planning
- **Purpose**: Ensure optimal stock levels across locations
- **Features**:
  - Automatic replenishment recommendations
  - Min/Max planning rules
  - Safety stock rules
  - Branch and warehouse refill planning
  - Priority-based approval workflow
  - Transfer suggestions

#### 5. MRP (Material Requirements Planning)
- **Purpose**: Calculate net requirements and generate purchase suggestions
- **Features**:
  - MRP run with configurable horizon
  - Net requirement calculation
  - Purchase suggestions
  - Reschedule suggestions
  - Shortage detection
  - Excess stock proposals
  - Planner review queue

#### 6. Inventory Optimization
- **Purpose**: Maintain optimal inventory levels
- **Features**:
  - Stock health monitoring
  - ABC/XYZ analysis
  - Safety stock optimization
  - Excess/slow/dead stock identification
  - Stock risk heatmap
  - Days of supply analysis
  - Service level target management

#### 7. Multi-Echelon Planning (MEIO)
- **Purpose**: Optimize inventory across supply network
- **Features**:
  - Network visibility
  - Source-to-destination planning
  - Cross-warehouse balancing
  - Inter-branch reallocation
  - Transfer recommendations
  - Forward/reserve stock planning

#### 8. Service Level & Fulfillment
- **Purpose**: Monitor and improve customer service
- **Features**:
  - Fill rate analysis
  - OTIF (On Time In Full) tracking
  - Backorder impact view
  - Lost demand analysis
  - Supply reliability metrics

#### 9. Scenario Planning
- **Purpose**: What-if analysis for strategic decisions
- **Features**:
  - Demand spike scenarios
  - Supplier delay scenarios
  - Lead time change scenarios
  - Stock rebalancing scenarios
  - Scenario comparison
  - Impact analysis

#### 10. Alerts & Exceptions
- **Purpose**: Proactive exception management
- **Features**:
  - Shortage alerts
  - Overstock alerts
  - Forecast deviation alerts
  - Delayed supply alerts
  - Low coverage alerts
  - Critical item watchlist
  - Escalation queue

## Database Schema

### Core Tables

```sql
-- Demand history aggregation
planning_demand_history
- item_id, warehouse_id, company_id
- period_type, period_start
- quantity, sales_quantity, consumption_quantity
- customer_count, order_count

-- Forecast runs
planning_forecast_runs
- run_name, forecast_type, method
- horizon_days, status
- total_items, total_demand

-- Forecast lines
planning_forecast_lines
- run_id, item_id, period_start
- base_quantity, final_quantity
- override_quantity, is_frozen

-- Replenishment recommendations
planning_replenishment_recommendations
- item_id, recommendation_type, action
- priority, recommended_quantity
- status, approved_by

-- Purchase recommendations (MRP)
planning_purchase_recommendations
- item_id, supplier_id
- recommended_quantity
- suggested_order_date
- status

-- Transfer recommendations (MEIO)
planning_transfer_recommendations
- item_id, source/destination warehouse
- recommended_quantity
- urgency, status

-- Planning alerts
planning_alerts
- alert_type, severity
- item_id, warehouse_id
- is_acknowledged

-- Scenarios
planning_scenarios
- name, scenario_type
- parameters_json
- total_impact_items

-- Item planning profiles
planning_item_profiles
- item_id, abc_class, xyz_class
- planning_method, forecast_method
- lead_time_days, safety_stock_days
- service_level_target
```

## Integration Points

### WMS Integration
- Inventory balances drive stock health
- Inbound receipts feed supply pipeline
- Warehouse assignments enable multi-location planning

### Procurement Integration
- Purchase orders link to supply plan
- Supplier lead times inform replenishment
- PO receipts update inventory

### Logistics Integration
- Dispatch plans affect fulfillment metrics
- In-transit inventory visible in supply view
- Route constraints considered in planning

### Finance Integration
- Budget constraints affect replenishment limits
- Cost data in purchase recommendations
- Inventory value in executive dashboards

### Flow Integration
- Alerts surface in Flow
- Approval workflows use Flow
- Planner notifications via Flow

## Security Model

### Permission Structure
```python
'scm': {
    'dashboard': ['view'],
    'demand': ['view', 'create', 'edit', 'delete', 'approve', 'override'],
    'supply': ['view', 'create', 'edit', 'delete'],
    'replenishment': ['view', 'create', 'edit', 'delete', 'approve', 'execute'],
    'mrp': ['view', 'create', 'edit', 'delete', 'approve', 'execute'],
    'inventory': ['view', 'create', 'edit', 'delete'],
    'network': ['view', 'create', 'edit', 'delete'],
    'service': ['view', 'create', 'edit', 'delete'],
    'scenarios': ['view', 'create', 'edit', 'delete', 'approve', 'run'],
    'alerts': ['view', 'create', 'edit', 'delete', 'resolve', 'acknowledge'],
    'supplier': ['view', 'create', 'edit', 'delete'],
    'warehouse': ['view', 'create', 'edit', 'delete'],
    'workflow': ['view', 'create', 'edit', 'delete', 'approve'],
    'reports': ['view', 'export', 'create', 'edit', 'delete'],
    'settings': ['view', 'edit'],
}
```

### Role-Based Access
- **SCM Admin**: Full access to all SCM functions
- **Supply Chain Manager**: Access to all planning functions
- **Demand Planner**: Focus on demand planning
- **Supply Planner**: Focus on supply and procurement
- **Replenishment Planner**: Focus on replenishment
- **Branch Planner**: Access to assigned branches only
- **Executive Viewer**: Read-only dashboard access

## Performance Considerations

### Optimization Strategies
1. **Indexed Queries**: All frequently filtered columns are indexed
2. **Batch Processing**: Forecast generation and MRP runs process in batches
3. **Caching**: Dashboard summaries cached for 5 minutes
4. **Lazy Loading**: Large datasets paginated

### Scalability
- Horizontal scaling supported via multiple app instances
- Database partitioning for large demand history tables
- Async processing for long-running MRP runs

## Future Enhancements

1. **ML-Based Forecasting**: Integration with ML models for better predictions
2. **Constraint Optimization**: Mathematical optimization for multi-echelon planning
3. **Supplier Collaboration Portal**: External supplier access
4. **Real-Time Supply Chain**: Event-driven updates
5. **Advanced Analytics**: Predictive maintenance for inventory

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite (expandable to PostgreSQL)
- **Frontend**: HTML5, CSS3, JavaScript, Tailwind CSS
- **Icons**: Font Awesome 6
- **Charts**: Chart.js
- **Real-time**: WebSocket for live updates (future)
