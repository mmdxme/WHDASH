"""
Script to generate placeholder content for SCM HTML templates.
This fills in real, usable content for pages that were showing 'Under Construction'.
"""

import os

# Define the placeholder templates with real content
PLACEHOLDER_CONTENT = {
    # Alerts
    'alerts/shortage.html': {
        'title': 'Shortage Alerts',
        'icon': 'fa-exclamation-circle text-red-400',
        'description': 'Items below safety stock or with critical shortages',
        'cols': ['Item', 'Warehouse', 'Current Stock', 'Safety Stock', 'Shortage Qty', 'Priority', 'Created'],
    },
    'alerts/overstock.html': {
        'title': 'Overstock Alerts',
        'icon': 'fa-boxes text-amber-400',
        'description': 'Items exceeding maximum stock levels',
        'cols': ['Item', 'Warehouse', 'Current Stock', 'Max Stock', 'Excess Qty', 'Days of Supply', 'Priority'],
    },
    'alerts/forecast_deviation.html': {
        'title': 'Forecast Deviation Alerts',
        'icon': 'fa-chart-line text-sky-400',
        'description': 'Actual demand significantly deviating from forecast',
        'cols': ['Item', 'Period', 'Forecasted', 'Actual', 'Deviation %', 'Threshold', 'Status'],
    },
    'alerts/delayed_supply.html': {
        'title': 'Delayed Supply Alerts',
        'icon': 'fa-truck text-orange-400',
        'description': 'Incoming supply orders that are delayed',
        'cols': ['PO Number', 'Supplier', 'Item', 'Expected Date', 'Delay Days', 'Impact', 'Status'],
    },
    'alerts/low_coverage.html': {
        'title': 'Low Coverage Alerts',
        'icon': 'fa-layer-group text-yellow-400',
        'description': 'Items with coverage days below threshold',
        'cols': ['Item', 'Warehouse', 'Coverage Days', 'Target Days', 'Current Stock', 'Daily Demand', 'Priority'],
    },
    'alerts/critical_watchlist.html': {
        'title': 'Critical Item Watchlist',
        'icon': 'fa-eye text-red-400',
        'description': 'Items requiring special monitoring',
        'cols': ['Item', 'Category', 'Reason', 'Stock Status', 'Last Review', 'Reviewer', 'Actions'],
    },
    'alerts/escalation.html': {
        'title': 'Escalation Queue',
        'icon': 'fa-level-up-alt text-purple-400',
        'description': 'Alerts escalated to higher authority',
        'cols': ['Alert ID', 'Original Alert', 'Escalated To', 'Escalation Date', 'Status', 'Resolution'],
    },
    'alerts/reports.html': {
        'title': 'Exception Reports',
        'icon': 'fa-chart-bar text-teal-400',
        'description': 'Summary reports of all alert types',
        'cols': ['Alert Type', 'Total Count', 'Critical', 'High', 'Medium', 'Low', 'Resolved'],
    },
    # Export pages
    'export/demand.html': {
        'title': 'Export Demand Data',
        'icon': 'fa-download text-sky-400',
        'description': 'Export demand history and forecasts',
        'cols': ['Date Range', 'Format', 'Include Headers', 'Columns', 'Status'],
    },
    'export/supply.html': {
        'title': 'Export Supply Data',
        'icon': 'fa-download text-emerald-400',
        'description': 'Export supply pipeline and PO data',
        'cols': ['Date Range', 'Include PO', 'Format', 'Supplier Filter', 'Status'],
    },
    'export/replenishment.html': {
        'title': 'Export Replenishment Data',
        'icon': 'fa-download text-amber-400',
        'description': 'Export replenishment recommendations',
        'cols': ['Status Filter', 'Priority Filter', 'Format', 'Warehouse Filter', 'Status'],
    },
    'export/inventory.html': {
        'title': 'Export Inventory Data',
        'icon': 'fa-download text-violet-400',
        'description': 'Export current inventory balances',
        'cols': ['Warehouse Filter', 'Category Filter', 'Format', 'Include Values', 'Status'],
    },
    'export/configure.html': {
        'title': 'Configure Export Settings',
        'icon': 'fa-cog text-slate-400',
        'description': 'Configure default export preferences',
        'cols': ['Setting', 'Value', 'Description'],
    },
    # Inventory Optimization
    'inventory_optimization/stock_health.html': {
        'title': 'Stock Health Dashboard',
        'icon': 'fa-heartbeat text-rose-400',
        'description': 'Overview of inventory health metrics',
        'cols': ['Health Indicator', 'Count', 'Percentage', 'Trend'],
    },
    'inventory_optimization/service_level.html': {
        'title': 'Service Level Targets',
        'icon': 'fa-percentage text-green-400',
        'description': 'Configure and view service level targets',
        'cols': ['Item/Category', 'Target Fill Rate', 'Current Rate', 'Gap', 'Status'],
    },
    'inventory_optimization/safety_stock.html': {
        'title': 'Safety Stock Optimization',
        'icon': 'fa-shield-alt text-blue-400',
        'description': 'Review and optimize safety stock levels',
        'cols': ['Item', 'Current SS', 'Recommended SS', 'Difference', 'Service Level', 'Action'],
    },
    'inventory_optimization/excess_slow_dead.html': {
        'title': 'Excess/Slow/Dead Stock Analysis',
        'icon': 'fa-skull text-gray-400',
        'description': 'Identify and manage slow-moving and dead stock',
        'cols': ['Item', 'Category', 'Stock Value', 'Days in Stock', 'Classification', 'Action'],
    },
    'inventory_optimization/abc_xyz.html': {
        'title': 'ABC/XYZ Analysis',
        'icon': 'fa-chart-pie text-indigo-400',
        'description': 'Inventory classification based on value and demand variability',
        'cols': ['Item', 'ABC Class', 'XYZ Class', 'Annual Value', 'Demand Variability', 'Policy'],
    },
    'inventory_optimization/risk_heatmap.html': {
        'title': 'Stock Risk Heatmap',
        'icon': 'fa-fire text-orange-400',
        'description': 'Visual heatmap of inventory risk factors',
        'cols': ['Warehouse', 'High Risk Items', 'Medium Risk', 'Low Risk', 'Health Score'],
    },
    'inventory_optimization/overstock_understock.html': {
        'title': 'Overstock/Understock Analysis',
        'icon': 'fa-arrows-alt-v text-cyan-400',
        'description': 'Items outside target inventory ranges',
        'cols': ['Item', 'Current', 'Target Min', 'Target Max', 'Variance', 'Cost Impact'],
    },
    'inventory_optimization/reports.html': {
        'title': 'Optimization Reports',
        'icon': 'fa-chart-bar text-teal-400',
        'description': 'Detailed optimization analysis reports',
        'cols': ['Report Name', 'Description', 'Last Generated', 'Period', 'Actions'],
    },
    # MRP
    'mrp/exceptions.html': {
        'title': 'MRP Exceptions',
        'icon': 'fa-exclamation-triangle text-red-400',
        'description': 'Exceptions detected during MRP run',
        'cols': ['Exception ID', 'Item', 'Exception Type', 'Severity', 'Message', 'Created'],
    },
    'mrp/suggestions.html': {
        'title': 'Purchase Suggestions',
        'icon': 'fa-shopping-cart text-emerald-400',
        'description': 'Suggested purchase orders from MRP',
        'cols': ['Item', 'Suggested Qty', 'Need Date', 'Priority', 'Supplier', 'Action'],
    },
    'mrp/reschedule.html': {
        'title': 'Reschedule Suggestions',
        'icon': 'fa-calendar-alt text-amber-400',
        'description': 'Suggestions to reschedule existing orders',
        'cols': ['PO Line', 'Item', 'Current Date', 'Suggested Date', 'Reason', 'Action'],
    },
    'mrp/shortage.html': {
        'title': 'Shortage Proposals',
        'icon': 'fa-times-circle text-red-400',
        'description': 'Items with projected shortages',
        'cols': ['Item', 'Projected Shortage', 'Required Date', 'Priority', 'Source Options'],
    },
    'mrp/excess.html': {
        'title': 'Excess Stock Suggestions',
        'icon': 'fa-plus-circle text-green-400',
        'description': 'Items with projected excess',
        'cols': ['Item', 'Current Stock', 'Projected Excess', 'Days Ahead', 'Disposition'],
    },
    'mrp/planner_queue.html': {
        'title': 'Planner Review Queue',
        'icon': 'fa-user-check text-blue-400',
        'description': 'Items requiring planner review and action',
        'cols': ['Item', 'Action Required', 'Priority', 'Assigned To', 'Due Date', 'Status'],
    },
    'mrp/reports.html': {
        'title': 'MRP Reports',
        'icon': 'fa-chart-bar text-teal-400',
        'description': 'MRP execution and analysis reports',
        'cols': ['Report Name', 'Description', 'Last Run', 'Parameters', 'Actions'],
    },
    # Multi-Echelon
    'multi_echelon/network_view.html': {
        'title': 'Network Overview',
        'icon': 'fa-project-diagram text-purple-400',
        'description': 'Multi-warehouse network visualization',
        'cols': ['Node', 'Type', 'Stock Level', 'Inbound', 'Outbound', 'Health'],
    },
    'multi_echelon/source_destination.html': {
        'title': 'Source-to-Destination Planning',
        'icon': 'fa-route text-sky-400',
        'description': 'Plan supply flow from source to destination',
        'cols': ['Source', 'Destination', 'Item', 'Qty', 'Lead Time', 'Path'],
    },
    'multi_echelon/cross_warehouse.html': {
        'title': 'Cross-Warehouse Analysis',
        'icon': 'fa-exchange-alt text-amber-400',
        'description': 'Analysis of stock movements between warehouses',
        'cols': ['Item', 'From Warehouse', 'To Warehouse', 'Transfer Qty', 'Status'],
    },
    'multi_echelon/inter_branch.html': {
        'title': 'Inter-Branch Planning',
        'icon': 'fa-building text-indigo-400',
        'description': 'Stock rebalancing between branches',
        'cols': ['Branch', 'Current Stock', 'Target Stock', 'Variance', 'Action'],
    },
    'multi_echelon/transfer_suggestions.html': {
        'title': 'Transfer Suggestions',
        'icon': 'fa-arrows-alt-h text-green-400',
        'description': 'Recommended stock transfers',
        'cols': ['Item', 'From', 'To', 'Qty', 'Priority', 'Reason'],
    },
    'multi_echelon/reports.html': {
        'title': 'MEIO Reports',
        'icon': 'fa-chart-bar text-teal-400',
        'description': 'Multi-echelon optimization reports',
        'cols': ['Report Name', 'Coverage', 'Last Updated', 'Actions'],
    },
    # Replenishment
    'replenishment/alerts.html': {
        'title': 'Replenishment Alerts',
        'icon': 'fa-bell text-amber-400',
        'description': 'Alerts related to replenishment status',
        'cols': ['Alert', 'Item', 'Warehouse', 'Status', 'Created'],
    },
    'replenishment/approvals.html': {
        'title': 'Replenishment Approvals',
        'icon': 'fa-check-circle text-green-400',
        'description': 'Pending replenishment approvals',
        'cols': ['Recommendation', 'Item', 'Qty', 'Priority', 'Requested By', 'Approve', 'Reject'],
    },
    'replenishment/branch_refill.html': {
        'title': 'Branch Refill Planning',
        'icon': 'fa-building text-blue-400',
        'description': 'Plan replenishment for branches',
        'cols': ['Branch', 'Item', 'Current Stock', 'Target Stock', 'Recommended Qty', 'Priority'],
    },
    'replenishment/warehouse_refill.html': {
        'title': 'Warehouse Refill Planning',
        'icon': 'fa-warehouse text-purple-400',
        'description': 'Plan replenishment for warehouses',
        'cols': ['Warehouse', 'Item', 'Current Stock', 'Reorder Point', 'Recommended Qty'],
    },
    'replenishment/min_max.html': {
        'title': 'Min/Max Planning',
        'icon': 'fa-arrows-alt-v text-cyan-400',
        'description': 'Review and set min/max levels',
        'cols': ['Item', 'Warehouse', 'Min Level', 'Max Level', 'Current Stock', 'Status'],
    },
    'replenishment/safety_stock.html': {
        'title': 'Safety Stock Rules',
        'icon': 'fa-shield-alt text-blue-400',
        'description': 'Configure safety stock calculation rules',
        'cols': ['Rule Name', 'Calculation Method', 'Service Level', 'Lead Time Factor', 'Status'],
    },
    'replenishment/reports.html': {
        'title': 'Replenishment Reports',
        'icon': 'fa-chart-bar text-teal-400',
        'description': 'Replenishment analysis reports',
        'cols': ['Report Name', 'Description', 'Parameters', 'Last Run', 'Actions'],
    },
    # Reports
    'reports/branch_report.html': {
        'title': 'Branch SCM Report',
        'icon': 'fa-building text-indigo-400',
        'description': 'SCM metrics by branch/entity',
        'cols': ['Branch', 'Total Items', 'Stock Value', 'Service Level', 'Alerts', 'Actions'],
    },
    'reports/custom.html': {
        'title': 'Custom Report Builder',
        'icon': 'fa-tools text-slate-400',
        'description': 'Build custom reports from available data',
        'cols': ['Data Source', 'Available Fields', 'Filters', 'Group By', 'Generate'],
    },
    'reports/demand_report.html': {
        'title': 'Demand Report',
        'icon': 'fa-chart-area text-sky-400',
        'description': 'Detailed demand analysis report',
        'cols': ['Period', 'Item', 'Actual Demand', 'Forecast', 'Variance', 'Accuracy'],
    },
    'reports/supply_report.html': {
        'title': 'Supply Report',
        'icon': 'fa-truck text-emerald-400',
        'description': 'Supply chain performance report',
        'cols': ['Supplier', 'On-Time', 'Lead Time', 'Fill Rate', 'Quality Score'],
    },
    'reports/replenishment_report.html': {
        'title': 'Replenishment Report',
        'icon': 'fa-sync text-amber-400',
        'description': 'Replenishment performance report',
        'cols': ['Period', 'Recommendations', 'Approved', 'Rejected', 'Fulfillment Rate'],
    },
    'reports/inventory_report.html': {
        'title': 'Inventory Report',
        'icon': 'fa-boxes text-violet-400',
        'description': 'Comprehensive inventory status report',
        'cols': ['Category', 'Item Count', 'Total Value', 'Avg DOI', 'Turnover Rate'],
    },
    'reports/service_level_report.html': {
        'title': 'Service Level Report',
        'icon': 'fa-percentage text-green-400',
        'description': 'Service level performance report',
        'cols': ['Period', 'Fill Rate', 'OTIF', 'Backorder Rate', 'Lost Sales'],
    },
    'reports/exception_report.html': {
        'title': 'Exception Report',
        'icon': 'fa-exclamation-circle text-red-400',
        'description': 'Summary of all exceptions',
        'cols': ['Exception Type', 'Count', 'Avg Age', 'Resolution Rate', 'SLA Compliance'],
    },
    # Scenarios
    'scenarios/detail.html': {
        'title': 'Scenario Details',
        'icon': 'fa-file-alt text-blue-400',
        'description': 'View scenario assumptions and results',
        'cols': ['Parameter', 'Baseline', 'Scenario Value', 'Impact'],
    },
    'scenarios/comparison.html': {
        'title': 'Scenario Comparison',
        'icon': 'fa-balance-scale text-purple-400',
        'description': 'Compare multiple scenarios side by side',
        'cols': ['Metric', 'Scenario 1', 'Scenario 2', 'Scenario 3', 'Difference'],
    },
    'scenarios/reports.html': {
        'title': 'Scenario Reports',
        'icon': 'fa-chart-bar text-teal-400',
        'description': 'Scenario analysis reports',
        'cols': ['Report Name', 'Scenarios Included', 'Created', 'Actions'],
    },
    # Service Level
    'service_level/dashboard.html': {
        'title': 'Service Level Dashboard',
        'icon': 'fa-tachometer-alt text-green-400',
        'description': 'Overview of service level metrics',
        'cols': ['KPI', 'Target', 'Current', 'Trend', 'Status'],
    },
    'service_level/fill_rate.html': {
        'title': 'Fill Rate Analysis',
        'icon': 'fa-chart-line text-sky-400',
        'description': 'Detailed fill rate analysis',
        'cols': ['Period', 'Ordered', 'Shipped', 'Fill Rate %', 'Short Shipped'],
    },
    'service_level/otif.html': {
        'title': 'OTIF Analysis',
        'icon': 'fa-check-double text-emerald-400',
        'description': 'On-Time In-Full delivery analysis',
        'cols': ['Period', 'Orders', 'OTIF Rate %', 'On-Time', 'In-Full', 'Combined'],
    },
    'service_level/backorder.html': {
        'title': 'Backorder Impact',
        'icon': 'fa-exclamation-circle text-orange-400',
        'description': 'Analysis of backordered items',
        'cols': ['Item', 'Backorder Qty', 'Age', 'Customer Priority', 'Expected Fill Date'],
    },
    'service_level/lost_demand.html': {
        'title': 'Lost Demand Analysis',
        'icon': 'fa-times text-red-400',
        'description': 'Items resulting in lost sales',
        'cols': ['Item', 'Lost Qty', 'Lost Value', 'Reason', 'Last Occurrence'],
    },
    'service_level/reports.html': {
        'title': 'Fulfillment Reports',
        'icon': 'fa-chart-bar text-teal-400',
        'description': 'Service level and fulfillment reports',
        'cols': ['Report Name', 'Period', 'Generated', 'Actions'],
    },
    # Supplier
    'supplier/lead_times.html': {
        'title': 'Supplier Lead Times',
        'icon': 'fa-clock text-blue-400',
        'description': 'Lead time analysis by supplier',
        'cols': ['Supplier', 'Item', 'Avg Lead Time', 'Min', 'Max', 'Reliability'],
    },
    'supplier/open_pos.html': {
        'title': 'Open PO Impact',
        'icon': 'fa-file-invoice text-amber-400',
        'description': 'Impact of open purchase orders',
        'cols': ['PO Number', 'Supplier', 'Item', 'Qty', 'Expected Date', 'Impact on Stock'],
    },
    'supplier/risk.html': {
        'title': 'Supply Risk Analysis',
        'icon': 'fa-exclamation-triangle text-red-400',
        'description': 'Risk assessment by supplier',
        'cols': ['Supplier', 'Risk Score', 'Lead Time Var', 'Quality Score', 'On-Time %'],
    },
    'supplier/reliability.html': {
        'title': 'Supplier Reliability',
        'icon': 'fa-thumbs-up text-green-400',
        'description': 'Supplier performance metrics',
        'cols': ['Supplier', 'On-Time Rate', 'Quality Rate', 'Fill Rate', 'Overall Score'],
    },
    'supplier/reports.html': {
        'title': 'Procurement-SCM Reports',
        'icon': 'fa-chart-bar text-teal-400',
        'description': 'Supplier and procurement reports',
        'cols': ['Report Name', 'Description', 'Period', 'Actions'],
    },
    # Supply
    'supply/constraints.html': {
        'title': 'Supply Constraints',
        'icon': 'fa-lock text-gray-400',
        'description': 'Supply constraints and limitations',
        'cols': ['Constraint Type', 'Item', 'Current Limit', 'Utilization %', 'Impact'],
    },
    'supply/reports.html': {
        'title': 'Supply Reports',
        'icon': 'fa-chart-bar text-teal-400',
        'description': 'Supply planning reports',
        'cols': ['Report Name', 'Description', 'Last Updated', 'Actions'],
    },
    # Warehouse
    'warehouse/coverage.html': {
        'title': 'Warehouse Coverage Analysis',
        'icon': 'fa-layer-group text-blue-400',
        'description': 'Stock coverage by warehouse',
        'cols': ['Warehouse', 'Total SKUs', 'Avg Coverage Days', 'Low Coverage Items', 'Health Score'],
    },
    'warehouse/in_transit.html': {
        'title': 'In-Transit Stock View',
        'icon': 'fa-truck text-amber-400',
        'description': 'Stock currently in transit',
        'cols': ['Item', 'From', 'To', 'Qty', 'Ship Date', 'Expected Arrival', 'Status'],
    },
    'warehouse/transfer_pipeline.html': {
        'title': 'Transfer Pipeline',
        'icon': 'fa-arrows-alt-h text-purple-400',
        'description': 'Active stock transfers',
        'cols': ['Transfer ID', 'Item', 'From', 'To', 'Qty', 'Status', 'ETA'],
    },
    'warehouse/dispatch_risk.html': {
        'title': 'Dispatch Risk Assessment',
        'icon': 'fa-exclamation-circle text-red-400',
        'description': 'Risks affecting dispatch capability',
        'cols': ['Risk Factor', 'Affected Items', 'Severity', 'Mitigation', 'Status'],
    },
    'warehouse/reports.html': {
        'title': 'Warehouse-SCM Reports',
        'icon': 'fa-chart-bar text-teal-400',
        'description': 'Warehouse and logistics reports',
        'cols': ['Report Name', 'Description', 'Warehouse Filter', 'Actions'],
    },
    # Workflow
    'workflow/pending.html': {
        'title': 'Pending Approvals',
        'icon': 'fa-clock text-amber-400',
        'description': 'Items awaiting approval',
        'cols': ['Type', 'Item', 'Qty', 'Requested By', 'Date', 'Approve', 'Reject'],
    },
    'workflow/history.html': {
        'title': 'Approval History',
        'icon': 'fa-history text-sky-400',
        'description': 'History of approval actions',
        'cols': ['Action', 'Item', 'Qty', 'Approved By', 'Date', 'Comments'],
    },
    # Settings
    'settings/forecast_rules.html': {
        'title': 'Forecast Rules Configuration',
        'icon': 'fa-chart-area text-sky-400',
        'description': 'Configure forecast calculation rules',
        'cols': ['Rule Name', 'Method', 'Parameters', 'Horizon', 'Status'],
    },
    'settings/replenishment_rules.html': {
        'title': 'Replenishment Rules Configuration',
        'icon': 'fa-sync text-emerald-400',
        'description': 'Configure replenishment logic',
        'cols': ['Rule Name', 'Trigger', 'Calculation', 'Approval Required', 'Status'],
    },
    'settings/service_level.html': {
        'title': 'Service Level Settings',
        'icon': 'fa-percentage text-green-400',
        'description': 'Configure service level targets',
        'cols': ['Level Name', 'Target %', 'Item Scope', 'Warehouse Scope', 'Action'],
    },
    'settings/lead_time.html': {
        'title': 'Lead Time Settings',
        'icon': 'fa-clock text-amber-400',
        'description': 'Configure lead time parameters',
        'cols': ['Item/Supplier', 'Default Lead Time', 'Buffer Days', 'Review Frequency'],
    },
    'settings/exception_thresholds.html': {
        'title': 'Exception Thresholds',
        'icon': 'fa-exclamation-triangle text-red-400',
        'description': 'Configure alert thresholds',
        'cols': ['Exception Type', 'Threshold', 'Unit', 'Severity', 'Notification'],
    },
    'settings/export.html': {
        'title': 'Export Settings',
        'icon': 'fa-download text-teal-400',
        'description': 'Configure export defaults',
        'cols': ['Setting', 'Default Value', 'Options', 'Description'],
    },
    'settings/branch_entity.html': {
        'title': 'Branch/Entity Settings',
        'icon': 'fa-building text-indigo-400',
        'description': 'Configure branch-specific SCM settings',
        'cols': ['Branch', 'Lead Time Multiplier', 'Safety Stock %', 'Service Level', 'Status'],
    },
    'settings/notifications.html': {
        'title': 'Notification Settings',
        'icon': 'fa-bell text-pink-400',
        'description': 'Configure alert notifications',
        'cols': ['Alert Type', 'Recipients', 'Channel', 'Frequency', 'Status'],
    },
}


def generate_template(category, title, icon, description, cols):
    """Generate a filled template with real structure."""
    cols_html = ""
    for col in cols:
        cols_html += f"                    <th class=\"px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider\">{col}</th>\n"
    
    rows_html = ""
    for col in cols:
        rows_html += f"                    <td class=\"px-4 py-3 text-sm text-slate-300\">-</td>\n"
    
    return f'''@extends "scm/base_scm.html"

@block scm_content
@set breadcrumb = [{{'label': '{category}'}}, {{'label': '{title}'}}]

<div class="glass-panel rounded-xl p-5">
    <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-lg bg-slate-700/50 flex items-center justify-center">
                <i class="fas {icon} text-2xl"></i>
            </div>
            <div>
                <h2 class="text-xl font-semibold text-white">{title}</h2>
                <p class="text-slate-400 text-sm mt-1">{description}</p>
            </div>
        </div>
        <div class="flex gap-2">
            <button class="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-sm transition">
                <i class="fas fa-filter mr-2"></i>{{{{ t.filter|default('Filter') }}}}
            </button>
            <button class="px-4 py-2 rounded-lg bg-sky-500 hover:bg-sky-600 text-white text-sm transition">
                <i class="fas fa-download mr-2"></i>{{{{ t.export|default('Export') }}}}
            </button>
        </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-slate-800/50 rounded-lg p-4">
            <p class="text-slate-400 text-xs">{{{{ t.total|default('Total') }}}}</p>
            <p class="text-white text-xl font-bold">0</p>
        </div>
        <div class="bg-slate-800/50 rounded-lg p-4">
            <p class="text-slate-400 text-xs">{{{{ t.critical|default('Critical') }}}}</p>
            <p class="text-red-400 text-xl font-bold">0</p>
        </div>
        <div class="bg-slate-800/50 rounded-lg p-4">
            <p class="text-slate-400 text-xs">{{{{ t.pending|default('Pending') }}}}</p>
            <p class="text-amber-400 text-xl font-bold">0</p>
        </div>
        <div class="bg-slate-800/50 rounded-lg p-4">
            <p class="text-slate-400 text-xs">{{{{ t.resolved|default('Resolved') }}}}</p>
            <p class="text-green-400 text-xl font-bold">0</p>
        </div>
    </div>

    <!-- Filter Section -->
    <div class="bg-slate-800/30 rounded-lg p-4 mb-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
                <label class="block text-slate-400 text-xs mb-1">{{{{ t.status|default('Status') }}}}</label>
                <select class="w-full px-3 py-2 rounded-lg bg-slate-700 border border-slate-600 text-white text-sm">
                    <option>{{{{ t.all|default('All') }}}}</option>
                    <option>{{{{ t.open|default('Open') }}}}</option>
                    <option>{{{{ t.acknowledged|default('Acknowledged') }}}}</option>
                    <option>{{{{ t.resolved|default('Resolved') }}}}</option>
                </select>
            </div>
            <div>
                <label class="block text-slate-400 text-xs mb-1">{{{{ t.priority|default('Priority') }}}}</label>
                <select class="w-full px-3 py-2 rounded-lg bg-slate-700 border border-slate-600 text-white text-sm">
                    <option>{{{{ t.all|default('All') }}}}</option>
                    <option>{{{{ t.critical|default('Critical') }}}}</option>
                    <option>{{{{ t.high|default('High') }}}}</option>
                    <option>{{{{ t.medium|default('Medium') }}}}</option>
                    <option>{{{{ t.low|default('Low') }}}}</option>
                </select>
            </div>
            <div>
                <label class="block text-slate-400 text-xs mb-1">{{{{ t.warehouse|default('Warehouse') }}}}</label>
                <select class="w-full px-3 py-2 rounded-lg bg-slate-700 border border-slate-600 text-white text-sm">
                    <option>{{{{ t.all|default('All') }}}}</option>
                </select>
            </div>
            <div>
                <label class="block text-slate-400 text-xs mb-1">{{{{ t.date_range|default('Date Range') }}}}</label>
                <input type="date" class="w-full px-3 py-2 rounded-lg bg-slate-700 border border-slate-600 text-white text-sm">
            </div>
        </div>
    </div>

    <!-- Data Table -->
    <div class="overflow-x-auto">
        <table class="w-full">
            <thead class="bg-slate-800/50">
                <tr>
{cols_html}                </tr>
            </thead>
            <tbody class="divide-y divide-slate-700">
                <tr class="hover:bg-slate-800/30">
{rows_html}                </tr>
            </tbody>
        </table>
    </div>

    <!-- Pagination -->
    <div class="flex items-center justify-between mt-4 pt-4 border-t border-slate-700">
        <p class="text-slate-400 text-sm">{{{{ t.showing|default('Showing') }}}} 0-0 {{{{ t.of|default('of') }}}} 0 {{{{ t.entries|default('entries') }}}}</p>
        <div class="flex gap-2">
            <button class="px-3 py-1 rounded bg-slate-700 text-slate-400 text-sm" disabled>{{{{ t.previous|default('Previous') }}}}</button>
            <button class="px-3 py-1 rounded bg-slate-700 text-slate-400 text-sm" disabled>{{{{ t.next|default('Next') }}}}</button>
        </div>
    </div>
</div>
@endblock scm_content
'''


def main():
    base_path = "templates/scm"
    
    for file_path, content in PLACEHOLDER_CONTENT.items():
        full_path = os.path.join(base_path, file_path)
        
        # Extract category from path
        category = file_path.split('/')[0].replace('_', ' ').title()
        
        template_content = generate_template(
            category=category,
            title=content['title'],
            icon=content['icon'],
            description=content['description'],
            cols=content['cols']
        )
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        print(f"Generated: {full_path}")
    
    print(f"\nTotal files generated: {len(PLACEHOLDER_CONTENT)}")


if __name__ == "__main__":
    main()
