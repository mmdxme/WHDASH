# SCM Translation Keys

## Overview

The SCM module supports all 8 languages of the WHDASH platform with full RTL support for Persian and Arabic.

## Translation Structure

```python
TRANSLATIONS = {
    'en': {
        # SCM Module Labels
        'scm': 'Supply Chain Management',
        'scm_dashboard': 'SCM Dashboard',
        'scm_control_tower': 'SCM Control Tower',
        
        # Demand Planning
        'demand_planning': 'Demand Planning',
        'forecast_center': 'Forecast Center',
        'forecast_by_item': 'Forecast by Item',
        'forecast_by_warehouse': 'Forecast by Warehouse',
        'forecast_versions': 'Forecast Versions',
        'forecast_overrides': 'Forecast Overrides',
        'forecast_accuracy': 'Forecast Accuracy',
        
        # Supply Planning
        'supply_planning': 'Supply Planning',
        'supply_pipeline': 'Supply Pipeline',
        'supply_risks': 'Supply Risks',
        'supply_constraints': 'Supply Constraints',
        'coverage_analysis': 'Coverage Analysis',
        
        # Replenishment
        'replenishment': 'Replenishment',
        'replenishment_queue': 'Replenishment Queue',
        'min_max_planning': 'Min/Max Planning',
        'safety_stock_rules': 'Safety Stock Rules',
        'lead_time_rules': 'Lead Time Rules',
        'branch_refill': 'Branch Refill',
        'warehouse_refill': 'Warehouse Refill',
        
        # MRP
        'mrp': 'MRP',
        'mrp_run': 'MRP Run',
        'mrp_exceptions': 'MRP Exceptions',
        'purchase_suggestions': 'Purchase Suggestions',
        'reschedule_suggestions': 'Reschedule Suggestions',
        'shortage_proposals': 'Shortage Proposals',
        'excess_suggestions': 'Excess Suggestions',
        'planner_queue': 'Planner Queue',
        
        # Inventory Optimization
        'inventory_optimization': 'Inventory Optimization',
        'stock_health': 'Stock Health',
        'service_level_targets': 'Service Level Targets',
        'safety_stock_optimization': 'Safety Stock Optimization',
        'excess_slow_dead': 'Excess/Slow/Dead Stock',
        'abc_xyz_analysis': 'ABC/XYZ Analysis',
        'stock_risk_heatmap': 'Stock Risk Heatmap',
        'overstock_understock': 'Overstock/Understock',
        
        # Multi-Echelon
        'multi_echelon': 'Multi-Echelon',
        'network_view': 'Network View',
        'source_destination': 'Source-to-Destination',
        'cross_warehouse': 'Cross-Warehouse',
        'inter_branch': 'Inter-Branch',
        'transfer_suggestions': 'Transfer Suggestions',
        
        # Service Level
        'service_level': 'Service Level',
        'fill_rate_analysis': 'Fill Rate Analysis',
        'otif_analysis': 'OTIF Analysis',
        'backorder_impact': 'Backorder Impact',
        'lost_demand': 'Lost Demand',
        
        # Scenarios
        'scenarios': 'Scenarios',
        'scenario_comparison': 'Scenario Comparison',
        
        # Alerts
        'alerts_exceptions': 'Alerts & Exceptions',
        'shortage_alerts': 'Shortage Alerts',
        'overstock_alerts': 'Overstock Alerts',
        'forecast_deviation': 'Forecast Deviation',
        'delayed_supply': 'Delayed Supply',
        'low_coverage': 'Low Coverage',
        'critical_watchlist': 'Critical Watchlist',
        'escalation_queue': 'Escalation Queue',
        
        # Supplier & Procurement
        'supplier_linkage': 'Supplier Linkage',
        'supplier_lead_times': 'Supplier Lead Times',
        'open_pos_impact': 'Open POs Impact',
        'supply_risk': 'Supply Risk',
        'supplier_reliability': 'Supplier Reliability',
        
        # Warehouse & Logistics
        'warehouse_linkage': 'Warehouse Linkage',
        'warehouse_coverage': 'Warehouse Coverage',
        'in_transit_stock': 'In-Transit Stock',
        'transfer_pipeline': 'Transfer Pipeline',
        'dispatch_risk': 'Dispatch Risk',
        
        # Reports
        'reports_analytics': 'Reports & Analytics',
        'demand_report': 'Demand Report',
        'supply_report': 'Supply Report',
        'replenishment_report': 'Replenishment Report',
        'inventory_report': 'Inventory Report',
        'service_level_report': 'Service Level Report',
        'exception_report': 'Exception Report',
        'branch_scm_report': 'Branch SCM Report',
        'custom_report_builder': 'Custom Report Builder',
        
        # Export
        'export_center': 'Export Center',
        'export_demand': 'Export Demand Data',
        'export_supply': 'Export Supply Data',
        'export_replenishment': 'Export Replenishment',
        'export_inventory': 'Export Inventory',
        
        # Workflow
        'workflow_approvals': 'Workflow & Approvals',
        'pending_approvals': 'Pending Approvals',
        'approval_history': 'Approval History',
        
        # Settings
        'scm_settings': 'SCM Settings',
        'forecast_rules': 'Forecast Rules',
        'replenishment_rules': 'Replenishment Rules',
        'service_level_settings': 'Service Level Settings',
        'lead_time_settings': 'Lead Time Settings',
        'exception_thresholds': 'Exception Thresholds',
        'export_settings': 'Export Settings',
        'branch_entity_settings': 'Branch/Entity Settings',
        'notification_settings': 'Notification Settings',
        
        # Common Terms
        'active_items': 'Active Items',
        'active_alerts': 'Active Alerts',
        'below_safety': 'Below Safety',
        'below_rop': 'Below ROP',
        'zero_stock': 'Zero Stock',
        'excess_stock': 'Excess Stock',
        'open_recommendations': 'Open Recommendations',
        'purchase_suggestions': 'Purchase Suggestions',
        'transfers': 'Transfers',
        'dead_stock': 'Dead Stock Items',
        'demand_supply_summary': 'Demand & Supply Summary',
        'recent_demand_30d': 'Recent Demand (30d)',
        'in_transit_value': 'In-Transit Value',
        'fill_rate': 'Fill Rate',
        'pending_forecasts': 'Pending Forecasts',
        'active_scenarios': 'Active Scenarios',
        'delayed_supply': 'Delayed Supply',
        'stock_health_summary': 'Stock Health Summary',
        'stockout_risk': 'Stockout Risk',
        'healthy_stock': 'Healthy Stock',
        'top_shortage_items': 'Top Shortage Items',
        'top_overstock_items': 'Top Overstock Items',
        'recent_scm_alerts': 'Recent SCM Alerts',
        'severity': 'Severity',
        'type': 'Type',
        'alert': 'Alert',
        'item': 'Item',
        'created': 'Created',
        'actions': 'Actions',
        'priority': 'Priority',
        'action': 'Action',
        'current': 'Current',
        'forecast': 'Forecast',
        'open_demand': 'Open Demand',
        'in_transit': 'In-Transit',
        'rec_qty': 'Rec Qty',
        'suggested_date': 'Suggested Date',
        'supplier': 'Supplier',
        'status': 'Status',
        'view_all': 'View All',
        'refresh_alerts': 'Refresh Alerts',
        'ack': 'Ack',
        'no_alerts': 'No active alerts',
        
        # Arabic Translations (Sample)
        'ar': {
            'scm': 'إدارة سلسلة التوريد',
            'scm_dashboard': 'لوحة SCM',
            'demand_planning': 'تخطيط الطلب',
            'supply_planning': 'تخطيط التوريد',
            'replenishment': 'إعادة التعبئة',
            # ... etc
        },
        
        # Persian Translations (Sample)
        'fa': {
            'scm': 'مدیریت زنجیره تأمین',
            'scm_dashboard': 'داشبورد SCM',
            'demand_planning': 'برنامه‌ریزی تقاضا',
            'supply_planning': 'برنامه‌ریزی تأمین',
            'replenishment': 'تکمیل موجودی',
            # ... etc
        }
    }
}
```

## RTL Considerations

### Layout Direction
- All text uses `dir="auto"` for proper rendering
- Flex/Grid layouts use logical properties
- Icons positioned appropriately for RTL

### Text Alignment
- Headings: Center or end (RTL)
- Body: Start (LTR/RTL auto)
- Numbers: Always end-aligned

### List/Table Handling
- Tables maintain proper column order
- Lists use `margin-inline-start` for spacing

## Translation Best Practices

1. **Never hardcode strings** - Always use translation keys
2. **Context in keys** - Use descriptive names: `forecast_accuracy_rate`
3. **Plural handling** - Use ICU plural formats
4. **Date/number formatting** - Use locale-aware formatters
5. **Fallback** - English as ultimate fallback

## Implementation

### Template Usage
```html
{{ t.scm_dashboard }}
{{ t.demand_planning }}
{{ t.forecast_center }}
```

### JavaScript Usage
```javascript
const translations = {
    scm_dashboard: 'SCM Dashboard',
    // ...
};
```

## Testing

### RTL Testing
- Test in Arabic locale
- Test in Persian locale
- Verify icon positions
- Verify text alignment

### Translation Completeness
- All 8 languages should have same coverage
- No missing translation keys
- No untranslated strings visible
