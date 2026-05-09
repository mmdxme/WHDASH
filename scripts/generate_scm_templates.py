#!/usr/bin/env python3
"""Generate SCM template stubs."""

templates = [
    ("supply", "reports"),
    ("replenishment", "queue"),
    ("replenishment", "min_max"),
    ("replenishment", "safety_stock"),
    ("replenishment", "branch_refill"),
    ("replenishment", "warehouse_refill"),
    ("replenishment", "alerts"),
    ("replenishment", "approvals"),
    ("replenishment", "reports"),
    ("mrp", "exceptions"),
    ("mrp", "suggestions"),
    ("mrp", "reschedule"),
    ("mrp", "shortage"),
    ("mrp", "excess"),
    ("mrp", "planner_queue"),
    ("mrp", "reports"),
    ("inventory_optimization", "stock_health"),
    ("inventory_optimization", "service_level"),
    ("inventory_optimization", "safety_stock"),
    ("inventory_optimization", "excess_slow_dead"),
    ("inventory_optimization", "abc_xyz"),
    ("inventory_optimization", "risk_heatmap"),
    ("inventory_optimization", "overstock_understock"),
    ("inventory_optimization", "reports"),
    ("multi_echelon", "network_view"),
    ("multi_echelon", "source_destination"),
    ("multi_echelon", "cross_warehouse"),
    ("multi_echelon", "inter_branch"),
    ("multi_echelon", "transfer_suggestions"),
    ("multi_echelon", "reports"),
    ("service_level", "dashboard"),
    ("service_level", "fill_rate"),
    ("service_level", "otif"),
    ("service_level", "backorder"),
    ("service_level", "lost_demand"),
    ("service_level", "reports"),
    ("scenarios", "detail"),
    ("scenarios", "comparison"),
    ("scenarios", "reports"),
    ("alerts", "shortage"),
    ("alerts", "overstock"),
    ("alerts", "forecast_deviation"),
    ("alerts", "delayed_supply"),
    ("alerts", "low_coverage"),
    ("alerts", "critical_watchlist"),
    ("alerts", "escalation"),
    ("alerts", "reports"),
    ("supplier", "lead_times"),
    ("supplier", "open_pos"),
    ("supplier", "risk"),
    ("supplier", "reliability"),
    ("supplier", "reports"),
    ("warehouse", "coverage"),
    ("warehouse", "in_transit"),
    ("warehouse", "transfer_pipeline"),
    ("warehouse", "dispatch_risk"),
    ("warehouse", "reports"),
    ("reports", "demand_report"),
    ("reports", "supply_report"),
    ("reports", "replenishment_report"),
    ("reports", "inventory_report"),
    ("reports", "service_level_report"),
    ("reports", "exception_report"),
    ("reports", "branch_report"),
    ("reports", "custom"),
    ("export", "demand"),
    ("export", "supply"),
    ("export", "replenishment"),
    ("export", "inventory"),
    ("export", "configure"),
    ("workflow", "pending"),
    ("workflow", "history"),
    ("settings", "forecast_rules"),
    ("settings", "replenishment_rules"),
    ("settings", "service_level"),
    ("settings", "lead_time"),
    ("settings", "exception_thresholds"),
    ("settings", "export"),
    ("settings", "branch_entity"),
    ("settings", "notifications"),
]

base_template = '''{% extends "scm/base_scm.html" %}
{% block scm_content %}
{% set breadcrumb = [{'label': '%category%', 'url': url_for('scm.%category_key%')}, {'label': '%title%'}] %}
<div class="glass-panel rounded-xl p-5">
    <h2 class="text-white font-semibold mb-4">{{ t.%title_key%|default('%title%') }}</h2>
    <p class="text-slate-400 text-center py-8">{{ t.page_under_construction|default('This page displays %title% content.') }}</p>
</div>
{% endblock %}
'''

import os

for category, title in templates:
    category_key = category.replace("_", "_")
    title_key = title.replace("_", "_")
    path = f"templates/scm/{category}/{title}.html"
    
    if not os.path.exists(path):
        content = base_template.replace("%category%", category.replace("_", " ").title())
        content = content.replace("%category_key%", f"{category.replace('_', '_')}")
        content = content.replace("%title%", title.replace("_", " ").title())
        content = content.replace("%title_key%", f"{category}_{title}".replace("_", "_"))
        
        with open(path, "w") as f:
            f.write(content)
        print(f"Created: {path}")

print("Done!")
