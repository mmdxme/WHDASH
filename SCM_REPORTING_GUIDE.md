# SCM Reporting Guide

## Overview

The SCM module provides comprehensive reporting and analytics capabilities across all supply chain planning functions.

## Report Categories

### 1. Demand Reports

#### Demand Summary Report
- Total demand by period
- Demand by item/category/warehouse
- Trend analysis
- Forecast accuracy metrics

#### Forecast Report
- Forecast vs actual comparison
- Bias analysis
- Seasonal patterns
- Forecast versions comparison

#### Forecast Accuracy Report
- MAPE (Mean Absolute Percentage Error)
- Bias tracking
- Item-level accuracy
- Trend accuracy

### 2. Supply Reports

#### Supply Coverage Report
- Days of supply by item
- Coverage gaps identification
- In-transit supply status
- PO impact analysis

#### Supplier Performance Report
- On-time delivery rate
- Fill rate by supplier
- Lead time variance
- Quality metrics

### 3. Replenishment Reports

#### Replenishment Activity Report
- Recommendations generated
- Approval rates
- Execution status
- Cost impact

#### Purchase Suggestions Report
- Suggested quantities
- Estimated costs
- Priority classification
- Supplier assignment

### 4. Inventory Reports

#### Stock Health Report
- ABC/XYZ classification
- Stockout frequency
- Overstock identification
- Days of inventory

#### Slow/Dead Stock Report
- Items with no movement
- Obsolescence risk
- Disposition recommendations
- Value at risk

### 5. Service Level Reports

#### Fill Rate Report
- Line fill rate
- Order fill rate
- Warehouse comparison
- Category analysis

#### OTIF Report
- On-time delivery percentage
- In-full delivery percentage
- Root cause analysis
- Improvement trends

### 6. Exception Reports

#### Alert Summary Report
- Alert count by type
- Severity distribution
- Resolution time
- Trend analysis

#### Shortage Impact Report
- Items at risk
- Quantity shortfall
- Customer impact
- Mitigation actions

### 7. Branch/Entity Reports

#### Branch SCM Summary
- Stock value by branch
- Demand fulfillment
- Service levels
- Cost analysis

## Report Parameters

### Common Filters
- **Date Range**: Start/end dates
- **Branch/Entity**: Single or multiple selection
- **Warehouse**: Single or multiple selection
- **Item Category**: Product category filter
- **Item**: Specific items
- **Status**: Active/inactive/all

### Export Options
- **Format**: PDF, Excel, CSV
- **Columns**: User-selectable
- **Grouping**: Optional subtotals
- **Sorting**: Multiple column sort

## Custom Report Builder

### Available Fields

#### Demand Fields
- Item code, name, category
- Period (daily/weekly/monthly)
- Sales quantity
- Consumption quantity
- Total demand
- Forecast quantity
- Variance

#### Supply Fields
- Item code, name
- Current stock
- In-transit quantity
- Open PO quantity
- Projected stock
- Days of supply

#### Financial Fields
- Unit cost
- Total inventory value
- Carrying cost
- Stockout cost

## Scheduling Reports

### Automated Reports
- Daily demand summary
- Weekly stock health
- Monthly service level
- Quarterly planning review

### Distribution Lists
- Email distribution
- Role-based recipients
- Conditional recipients

## Key Performance Indicators (KPIs)

### Demand Planning KPIs
| KPI | Formula | Target |
|-----|---------|--------|
| Forecast Accuracy | 1 - (|Actual - Forecast| / Actual) | >85% |
| Forecast Bias | Sum(Actual - Forecast) / Sum(Actual) | ±5% |
| Demand Variability | Std Dev / Mean | Monitor |

### Supply Planning KPIs
| KPI | Formula | Target |
|-----|---------|--------|
| Supply Reliability | On-time Receipts / Total Receipts | >95% |
| Fill Rate | Shipped Qty / Ordered Qty | >98% |
| OTIF | On-time AND In-full / Total Orders | >90% |

### Inventory KPIs
| KPI | Formula | Target |
|-----|---------|--------|
| Days of Inventory | Stock / Avg Daily Demand | 30-45 days |
| Stockout Rate | Stockout Events / Total Items | <2% |
| Inventory Turnover | COGS / Avg Inventory | >8x |

### Replenishment KPIs
| KPI | Formula | Target |
|-----|---------|--------|
| Recommendation Rate | Recommendations Executed / Total | >80% |
| Approval Cycle | Time from create to approve | <4 hours |
| Auto-release Rate | Auto-replenishment / Total | >60% |

## Report Access

### Dashboard Widgets
- KPI summary cards
- Trend charts
- Exception highlights
- Quick links to detailed reports

### Export Capabilities
- Real-time export from any report
- Scheduled automated delivery
- User-configurable column selection
- Customizable date ranges

## Best Practices

1. **Run reports during off-peak hours** for large date ranges
2. **Use filters** to reduce data volume
3. **Schedule recurring reports** for regular monitoring
4. **Save favorite configurations** for quick access
5. **Review exceptions daily** for proactive management
