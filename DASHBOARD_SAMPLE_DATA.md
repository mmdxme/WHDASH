# Dashboard Sample Data Guide

## Overview

This document describes the sample/demo data used in the WHDASH Enterprise Dashboard for demonstration purposes.

---

## Sample Data Structure

The dashboard uses realistic sample data to demonstrate functionality when actual database data is limited.

---

## Greeting Messages

### English (en)
```python
greetings = {
    'en': "Good {morning/afternoon/evening}, {username}",
    'fa': "سلام {username}",
    'ar': "أهلاً {username}",
    'ru': "Добрый {день/вечер}, {username}",
    'hi': "नमस्ते {username}",
    'es': "Buenos {días/tardes}, {username}",
    'zh': "你好，{username}",
    'de': "Guten {Morgen/Tag/Abend}, {username}"
}
```

---

## Sample KPI Data

### Default KPIs
```python
{
    'id': 'pending_approvals',
    'label': 'Pending Approvals',
    'value': 12,
    'formatted_value': '12',
    'icon': 'clipboard-check',
    'severity': 'warning',
    'trend': '+3 today',
    'trend_direction': 'up',
    'subtext': 'Requires attention',
    'link': '/workflow/my-approvals'
}
```

### Finance KPIs (Sample)
```python
{
    'id': 'cash_position',
    'label': 'Cash Position',
    'value': 2450000,
    'formatted_value': 'AED 2.45M',
    'icon': 'wallet',
    'severity': 'success',
    'trend': '+2.3%',
    'trend_direction': 'up',
    'subtext': 'Total available',
    'link': '/finance/treasury/cash-position'
}
```

---

## Sample Module Data

### Module Tile Example
```python
{
    'id': 'treasury',
    'label': 'Treasury',
    'icon': 'wallet',
    'url': '/finance/treasury/dashboard',
    'description': 'Cash & liquidity management',
    'permission': 'finance.treasury',
    'has_access': True,
    'is_favorite': True
}
```

---

## Sample Alert Data

### Critical Alert
```python
{
    'id': 'alert_001',
    'type': 'sla_breach',
    'severity': 'critical',
    'icon': 'exclamation-circle',
    'title': 'Invoice Approval SLA Breached',
    'message': 'INV-2026-0890 is 3 days past the SLA deadline. Immediate approval required.',
    'time_ago': '2 hours ago',
    'action_label': 'Review',
    'action_url': '/finance/ar/invoices/890',
    'dismissible': False
}
```

### Warning Alert
```python
{
    'id': 'alert_003',
    'type': 'stock_low',
    'severity': 'warning',
    'icon': 'boxes-stacked',
    'title': 'Low Stock Alert',
    'message': 'Spare parts category "Brake Pads" is below reorder point in Dubai warehouse.',
    'time_ago': '5 hours ago',
    'action_label': 'Reorder',
    'action_url': '/inventory/reorder',
    'dismissible': True
}
```

---

## Sample Operational Widgets

```python
{
    'type': 'kpi',
    'title': 'WMS Health',
    'icon': 'boxes',
    'value': '94%',
    'subtitle': '+1.2% vs last week',
    'badge': '3 Critical',
    'badge_type': 'danger',
    'link': '/inventory/dashboard'
}
```

---

## Sample Financial Widgets

```python
{
    'title': 'Revenue MTD',
    'icon': 'chart-line',
    'value': 'AED 8.75M',
    'comparison': {
        'label': 'vs Budget',
        'value': '+12.3%',
        'direction': 'up'
    }
}
```

---

## Sample Workflow Data

### Pending Approval
```python
{
    'id': 'wf_001',
    'icon': 'file-invoice',
    'title': 'Invoice Approval - AED 85,000',
    'requester': 'Sarah Johnson',
    'time_ago': '2 hours ago'
}
```

### SLA Metrics
```python
{
    'compliance': 87,
    'compliance_color': 'yellow',  # green/yellow/red
    'breaches': 3
}
```

---

## Sample Flow Announcements

```python
{
    'id': 'ann_001',
    'author': 'CEO Office',
    'author_avatar': None,
    'message': 'Q1 Town Hall meeting scheduled for April 25th at 2:00 PM. All employees are encouraged to attend.',
    'time_ago': '3 hours ago',
    'pinned': True
}
```

---

## Sample Personal Tasks

```python
{
    'id': 'task_001',
    'title': 'Review Q1 financial report',
    'due_date': 'Today',
    'completed': False
}
```

---

## Sample AI Insights

```python
{
    'id': 'ins_001',
    'type': 'attention',
    'type_label': 'Attention Needed',
    'icon': 'exclamation-circle',
    'confidence': 92,
    'title': 'Cash Flow Risk Detected',
    'description': 'Based on current payables and receivables patterns, there is a 78% probability of cash flow shortfall in the next 15 days.',
    'affected_items': 'AED 2.4M in receivables overdue >30 days',
    'source_module': 'Treasury',
    'time_ago': '1 hour ago',
    'actions': [
        {'label': 'View Details', 'icon': 'eye', 'type': 'secondary', 'url': '/finance/treasury/cash-flow-risk'},
        {'label': 'Take Action', 'icon': 'bolt', 'type': 'primary', 'url': '/finance/treasury/actions#collections'}
    ]
}
```

---

## Sample Activity Timeline

```python
{
    'category': 'approvals',  # approvals, documents, system, critical
    'event': 'Invoice Approved',
    'details': 'INV-2026-0891 for AED 45,000 approved by CFO',
    'user': 'Mohammed Hassan',
    'time_ago': '15 minutes ago'
}
```

---

## Sample Reports

```python
{
    'title': 'CFO Executive Report',
    'description': 'Comprehensive financial overview for leadership',
    'icon': 'file-invoice-dollar',
    'url': '/reports/cfo',
    'last_run': '2 hours ago',
    'frequency': 'Daily'
}
```

---

## Quick Actions

```python
[
    {'label': 'Create Invoice', 'icon': 'file-invoice', 'url': '/finance/ar/create'},
    {'label': 'New Task', 'icon': 'tasks', 'url': '/tasks/create'},
    {'label': 'Upload Document', 'icon': 'upload', 'url': '/documents/upload'},
    {'label': 'Submit Expense', 'icon': 'receipt', 'url': '/expenses/create'},
    {'label': 'Start Workflow', 'icon': 'project-diagram', 'url': '/workflow/start'},
    {'label': 'Schedule Report', 'icon': 'calendar', 'url': '/reports/schedule'},
]
```

---

## Currency Formatting

Dashboard uses AED (UAE Dirham) as default currency:
```python
'formatted_value': 'AED 2.45M'  # Millions
'formatted_value': 'AED 185K'    # Thousands
'formatted_value': 'AED 425,000'   # Full amount
```

---

## Date/Time Formatting

Based on user language preference:
- **en**: `%A, %B %d, %Y` → "Thursday, April 16, 2026"
- **fa**: `%Y/%m/%d` → "2026/04/16"
- **ar**: `%d %B %Y` → "16 أبريل 2026"

---

## RTL Support

All sample data is designed to work with RTL languages:
- Icons that imply direction (arrows) are mirrored
- Text alignment uses CSS logical properties
- Numbers and dates remain LTR

---

*Document Version: 1.0*
*Last Updated: 2026-04-16*
