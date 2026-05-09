# Dashboard Widget Matrix

## Overview

This document details every widget, zone, and interactive element in the WHDASH Enterprise Dashboard.

---

## Zone Structure

| Zone ID | Zone Name | Priority | Refresh Interval | Height |
|---------|-----------|----------|-----------------|--------|
| Z1 | Global Header / Welcome Bar | Critical | Static | 80px |
| Z2 | Executive KPI Strip | Critical | 60s | 140px |
| Z3 | Module Launcher | High | Static | 280px |
| Z4 | Alerts / Exceptions | High | 30s | 320px |
| Z5 | Operational Overview | Medium | 60s | 320px |
| Z6 | Financial Snapshot | High | 60s | 300px |
| Z7 | Workflow / Approvals | High | 30s | 300px |
| Z8 | Flow / Communication | Medium | 60s | 280px |
| Z9 | Personal Productivity | Medium | 60s | 280px |
| Z10 | Reports & Analytics | Medium | Static | 260px |
| Z11 | AI Insights | Medium | 300s | 220px |
| Z12 | Activity Timeline | Low | 60s | 200px |

---

## Widget Specifications

### Zone 1: Global Header

#### 1.1 Greeting Block
- **Type**: Static display
- **Data Source**: Session (username, language)
- **Content**: Time-based greeting (morning/afternoon/evening) + username
- **Languages**: All 8 supported

#### 1.2 Date/Time Display
- **Type**: Dynamic (updates every second)
- **Data Source**: Browser time (with timezone preference)
- **Format**: Localized based on user preference

#### 1.3 Company Context
- **Type**: Dropdown selector
- **Data Source**: `session.company_id`
- **Options**: All companies user has access to

#### 1.4 Global Search
- **Type**: Input field
- **Endpoint**: `/search?q={query}`
- **Keyboard Shortcut**: ⌘K / Ctrl+K
- **Placeholder**: Translation key `dashboard_search_placeholder`

#### 1.5 Quick Actions Dropdown
- **Type**: Dropdown menu
- **Items**: 6 configurable quick actions
- **Default Items**:
  - Create Invoice → `/finance/ar/create`
  - New Task → `/tasks/create`
  - Upload Document → `/documents/upload`
  - Submit Expense → `/expenses/create`
  - Start Workflow → `/workflow/start`
  - Schedule Report → `/reports/schedule`

#### 1.6 Notifications Bell
- **Type**: Icon button with badge
- **Badge**: Unread count (red badge)
- **Endpoint**: `/dashboard/api/notifications`

#### 1.7 User Profile Dropdown
- **Type**: Avatar + dropdown
- **Items**:
  - My Profile → `/profile`
  - Preferences → `/preferences`
  - Logout → `/logout`

---

### Zone 2: Executive KPI Strip

#### KPI Card Structure
Each KPI card contains:
- Icon (left)
- Label (top)
- Value (large, center)
- Subtext (bottom)
- Trend indicator (optional)
- Drill-down link

#### Default KPIs (All Users)

| ID | Label Key | Icon | Severity | Link |
|----|-----------|------|----------|------|
| pending_approvals | pending_approvals | clipboard-check | warning | /workflow/my-approvals |
| critical_alerts | critical_alerts | exclamation-triangle | critical | /alerts?severity=critical |
| overdue_tasks | overdue_tasks | clock | warning | /tasks?filter=overdue |
| open_issues | open_issues | exclamation-circle | info | /issues |

#### Finance KPIs (CFO, Finance Mgr, Treasury Mgr, Admin)

| ID | Label Key | Icon | Severity | Link |
|----|-----------|------|----------|------|
| cash_position | cash_position | wallet | success | /finance/treasury/cash-position |
| todays_collections | todays_collections | hand-holding-dollar | info | /finance/treasury/collections |
| due_payments | due_payments | credit-card | warning | /finance/treasury/payments |
| active_workflows | active_workflows | project-diagram | info | /workflow/dashboard |

#### Operations KPIs (COO, Warehouse Mgr, Operations Mgr, Admin)

| ID | Label Key | Icon | Severity | Link |
|----|-----------|------|----------|------|
| stock_health | stock_health | boxes-stacked | success | /inventory/dashboard |
| late_deliveries | late_deliveries | truck-fast | critical | /logistics/deliveries?status=delayed |

#### HR KPIs (HR Manager, Admin)

| ID | Label Key | Icon | Severity | Link |
|----|-----------|------|----------|------|
| headcount | headcount | users | info | /hr/employees |

#### Executive KPIs (CEO, COO, CFO, Admin)

| ID | Label Key | Icon | Severity | Link |
|----|-----------|------|----------|------|
| revenue_snapshot | revenue_snapshot | chart-line | success | /reports/revenue |
| budget_variance | budget_variance | chart-column | warning | /reports/budget |

---

### Zone 3: Module Launcher

#### Module Categories

| Category ID | Category Label | Modules |
|------------|----------------|--------|
| core_operations | Core Operations | org_planning, finance, treasury, assets, controlling, inventory, logistics, supply_chain, demand_planning, manufacturing, quality, maintenance |
| people_organization | People & Organization | hr, payroll, talent, expense |
| customers_commerce | Customers & Commerce | crm, marketing, ecommerce, project |
| technology_governance | Technology & Governance | investment, bi, ai, btp, integration, security, compliance, documents, legal, multi_company |
| services | Services | service, supplier, contingent, sustainability, rd |

#### Module Tile Structure
- Icon (48x48 gradient background)
- Label (centered)
- Description (optional, below label)
- Favorite star (top-right corner)

#### Module Tile States
- Default: Gray border
- Hover: Primary border + elevation
- Favorite: Gold star icon
- Disabled: Reduced opacity (if no permission)

---

### Zone 4: Alerts / Exceptions

#### Alert Item Structure
- Severity indicator (left border)
- Icon (severity-colored)
- Title (bold)
- Message (secondary text)
- Time ago (muted)
- Action button(s)

#### Alert Severity Levels

| Severity | Color | Border | Icon Background |
|----------|-------|--------|----------------|
| critical | Red (#ef4444) | Left 4px red | Red transparent |
| warning | Amber (#f59e0b) | Left 4px amber | Amber transparent |
| info | Blue (#3b82f6) | Left 4px blue | Blue transparent |

#### Alert Filter Pills
- All (default)
- Critical
- Warning

#### Default Alerts (Sample Data)

| ID | Type | Severity | Title | Action |
|----|------|----------|-------|--------|
| alert_001 | sla_breach | critical | Invoice Approval SLA Breached | Review |
| alert_002 | payment_overdue | critical | Payment Overdue | View |
| alert_003 | stock_low | warning | Low Stock Alert | Reorder |
| alert_004 | transfer_pending | warning | Transfer Approval Pending | Approve |
| alert_005 | document_expired | warning | Document Expiring | Renew |

---

### Zone 5: Operational Overview

#### Widget Types

| Type | Description | Content |
|------|-------------|---------|
| kpi | Single metric | Value + subtitle + badge + link |
| list | Item list | Label + value pairs |
| mini-chart | Small chart | Canvas with chart.js |

#### Default Operational Widgets

| Widget | Type | Value | Badge | Link |
|--------|------|-------|-------|------|
| WMS Health | kpi | 94% | 3 Critical | /inventory/dashboard |
| Active Shipments | kpi | 24 | 4 Delayed | /logistics/shipments |
| Quality Holds | kpi | 7 | 2 Urgent | /quality/holds |
| Open Work Orders | kpi | 31 | 5 Overdue | /maintenance/work-orders |

---

### Zone 6: Financial Snapshot

#### Default Financial Widgets

| Widget | Value | Comparison |
|--------|-------|-----------|
| Revenue MTD | AED 8.75M | vs Budget: +12.3% |
| Expenses MTD | AED 5.2M | vs Budget: -3.1% |
| AR Outstanding | AED 12.4M | vs Last Month: +8.5% |
| AP Outstanding | AED 4.8M | Due This Week: AED 1.2M |

---

### Zone 7: Workflow / Approvals

#### Approval Item Structure
- Icon
- Title (document type + amount)
- Requester + Time ago
- Quick approve/reject buttons

#### SLA Metrics
- Compliance percentage (with progress bar)
- Breaches count

---

### Zone 8: Flow / Communication

#### Tab: Announcements
- Avatar + author
- Message text
- Time ago
- Pinned indicator

#### Tab: Mentions
- @ icon
- Message text
- Context (channel name)

---

### Zone 9: Personal Productivity

#### My Tasks Widget
- Summary stats (overdue, today, upcoming)
- Task list (max 5)
- Checkbox for completion
- Due date display

#### My Issues Widget
- Priority breakdown (critical, high, medium, low)
- Color-coded bars

---

### Zone 10: Reports & Analytics

#### Default Report Cards

| Report | Icon | Last Run | Frequency |
|--------|------|----------|-----------|
| CFO Executive Report | file-invoice-dollar | 2 hours ago | Daily |
| Operations Dashboard | chart-pie | 1 hour ago | Real-time |
| HR Analytics | users | 1 day ago | Weekly |
| Treasury Report | wallet | 4 hours ago | Daily |
| Inventory Status | boxes | 3 hours ago | Daily |
| Sales Performance | chart-line | 1 day ago | Weekly |

---

### Zone 11: AI Insights

#### Insight Card Structure
- Type icon (attention/recommendation/prediction)
- Type label
- Confidence bar (if applicable)
- Title
- Description
- Affected items (if applicable)
- Action buttons
- Source module + time ago

#### Default Insights

| ID | Type | Title | Confidence |
|----|------|-------|------------|
| ins_001 | attention | Cash Flow Risk Detected | 92% |
| ins_002 | recommendation | Reorder Point Adjustment | 85% |
| ins_003 | prediction | SLA Breach Risk | 76% |
| ins_004 | attention | Expense Variance Alert | 88% |

---

### Zone 12: Activity Timeline

#### Timeline Item Structure
- Category marker (colored dot)
- Event title
- Details text
- User (if applicable)
- Time ago

#### Category Colors

| Category | Color |
|----------|-------|
| approvals | Green |
| documents | Blue |
| system | Amber |
| critical | Red |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/dashboard/api/kpis` | GET | Get KPI data |
| `/dashboard/api/alerts` | GET | Get alerts (supports `?severity=` and `?limit=`) |
| `/dashboard/api/alerts/dismiss` | POST | Dismiss an alert |
| `/dashboard/api/modules/favorite` | POST | Toggle module favorite |
| `/dashboard/api/workflow/approve` | POST | Quick approve |
| `/dashboard/api/workflow/reject` | POST | Quick reject |
| `/dashboard/api/tasks/toggle` | POST | Toggle task completion |

---

## Interaction Behaviors

| Element | Hover | Click | Long Press |
|---------|-------|-------|------------|
| KPI Card | Elevate + show drill-down icon | Navigate to link | N/A |
| Module Tile | Elevate + show star | Navigate to module | Open settings (admin) |
| Alert Item | N/A | Navigate to source | N/A |
| Approval Button | Color change | Process action | N/A |
| Task Checkbox | N/A | Toggle completion | N/A |

---

*Document Version: 1.0*
*Last Updated: 2026-04-16*
