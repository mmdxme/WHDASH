# WHDASH Enterprise Dashboard Architecture

## Overview

This document describes the comprehensive architecture of the WHDASH Enterprise Dashboard - the primary landing page and command center of the entire platform.

---

## 1. Design Philosophy

The WHDASH Enterprise Dashboard is designed to be:

- **Executive Command Center** - A unified entry point providing at-a-glance visibility across all ERP modules
- **Operations Nerve Center** - Real-time operational metrics, alerts, and workflow status
- **Personalized Home Page** - Role-based content tailored to the logged-in user's responsibilities
- **Module Discovery Hub** - Quick access to all 35+ ERP modules with intuitive navigation
- **Intelligence Platform** - AI-ready insights and recommendations for proactive management

### 1.1 Design Principles

1. **Clarity over Density** - Information hierarchy guides attention to what matters most
2. **Action-Oriented** - Every widget provides actionable insights and drill-down capabilities
3. **Role-Aware** - Content adapts to user role (Executive, Manager, Analyst, Operator)
4. **Multilingual-First** - Full support for 8 languages with proper RTL/LTR handling
5. **Performance-Optimized** - Fast loading with lazy loading and caching strategies
6. **Accessibility** - WCAG 2.1 AA compliance with keyboard navigation support

---

## 2. Dashboard Zones Architecture

### 2.1 Zone Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ZONE 1: GLOBAL HEADER / WELCOME BAR (height: 80px)                     │
│  - Personalized greeting, date/time, company context, quick search      │
├─────────────────────────────────────────────────────────────────────────┤
│  ZONE 2: EXECUTIVE KPI STRIP (height: 140px)                           │
│  - High-value KPIs with trend indicators and drill-down                │
├─────────────────────────────────────────────────────────────────────────┤
│  ZONE 3: SMART QUICK ACCESS / MODULE LAUNCHER (height: 280px)         │
│  - 35+ module shortcuts organized by category                          │
├───────────────────────────────┬─────────────────────────────────────────┤
│  ZONE 4: ALERTS / EXCEPTIONS  │  ZONE 5: OPERATIONAL OVERVIEW          │
│  (width: 35%, height: 320px)  │  (width: 65%, height: 320px)           │
│  - Critical actions, SLA      │  - WMS, logistics, inventory          │
│    breaches, warnings          │    alerts, workflow status            │
├───────────────────────────────┼─────────────────────────────────────────┤
│  ZONE 6: FINANCIAL SNAPSHOT   │  ZONE 7: WORKFLOW / APPROVAL           │
│  (width: 50%, height: 300px)  │  (width: 50%, height: 300px)          │
│  - Finance summary, AP/AR     │  - Pending approvals, SLA             │
│    treasury snapshot           │    compliance, escalations            │
├───────────────────────────────┼─────────────────────────────────────────┤
│  ZONE 8: FLOW / COMMUNICATION │  ZONE 9: PERSONAL PRODUCTIVITY         │
│  (width: 50%, height: 280px)  │  (width: 50%, height: 280px)          │
│  - Announcements, mentions,   │  - My tasks, issues, recent          │
│    team alerts                 │    documents, shortcuts               │
├─────────────────────────────────────────────────────────────────────────┤
│  ZONE 10: REPORTS & ANALYTICS (height: 260px)                           │
│  - Executive reports, scheduled reports, analytics shortcuts            │
├─────────────────────────────────────────────────────────────────────────┤
│  ZONE 11: AI INSIGHTS / RECOMMENDATIONS (height: 220px)                │
│  - Attention-needed areas, predicted bottlenecks, recommendations      │
├─────────────────────────────────────────────────────────────────────────┤
│  ZONE 12: ACTIVITY TIMELINE / AUDIT HIGHLIGHTS (height: 200px)         │
│  - Recent critical actions, approvals, record changes                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Zone Specifications

### 3.1 Zone 1: Global Header / Welcome Bar

**Purpose**: First impression, personalization, and global context

**Components**:
- Personalized greeting (time-based: Good morning/afternoon/evening)
- Current date/time with timezone
- Company/entity/branch context selector
- Global quick search input
- Notification bell with unread count
- User avatar with dropdown menu
- Role badge

**Data Source**: `session`, `user_preferences`

**Behavior**:
- Company context persists across session
- Search uses global search API
- Notifications update in real-time via polling

---

### 3.2 Zone 2: Executive KPI Strip

**Purpose**: At-a-glance executive metrics

**Default KPIs** (role-adaptive):

| KPI | Icon | Trend | Color | Default Role |
|-----|------|-------|-------|--------------|
| Pending Approvals | fa-clipboard-check | up/down | amber | All |
| Critical Alerts | fa-exclamation-triangle | count | red | All |
| Overdue Tasks | fa-clock | count | red | All |
| Open Issues | fa-exclamation-circle | count | orange | All |
| Treasury Cash Position | fa-wallet | up/down | green | Finance |
| Today's Collections | fa-hand-holding-dollar | vs target | blue | Finance |
| Due Payments | fa-credit-card | vs target | orange | Finance |
| Active Workflows | fa-project-diagram | count | purple | Manager |
| Stock Health | fa-boxes-stacked | trend | green | Operations |
| Late Deliveries | fa-truck-fast | count | red | Logistics |
| Headcount Summary | fa-users | vs budget | blue | HR |
| Revenue Snapshot | fa-chart-line | vs target | green | Executive |
| Budget Variance | fa-chart-column | variance | amber/red | CFO |
| Open Maintenance Orders | fa-wrench | count | orange | Maintenance |
| Quality Exceptions | fa-check-double | count | red | Quality |
| Unread Flow Alerts | fa-bell | count | blue | All |

**Drill-down Behavior**: Click on any KPI card navigates to relevant detail page

**Visual Design**:
- Horizontal scrollable on smaller screens
- Gradient accent on left border indicating severity
- Sparkline trend indicator
- Percentage change badge

---

### 3.3 Zone 3: Smart Quick Access / Module Launcher

**Purpose**: One-click access to all 35+ ERP modules

**Module Categories**:

#### Core Operations
1. Organizational Planning / BPM
2. Financial Management / Accounting
3. Treasury & Cash Flow Management
4. Fixed Asset Accounting
5. Controlling / Cost Accounting
6. Inventory / Warehouse Management (WMS)
7. Logistics / Transportation (TMS)
8. Supply Chain Management (SCM)
9. Demand Planning / Forecasting
10. Manufacturing (MES/PP)
11. Quality Management (QA/QC)
12. Maintenance Management (EAM/PM)

#### People & Organization
13. Human Resources Management (HR)
14. Payroll
15. Talent Management
16. Expense Management / Travel

#### Customers & Commerce
17. CRM / Customer Relationship
18. Marketing Automation
19. E-commerce / Online Store
20. Project Management

#### Technology & Governance
21. Investment Management
22. Business Intelligence / Dashboards
23. Artificial Intelligence / AI Copilot
24. Business Technology Platform (BTP)
25. Integration / Middleware
26. Security / SSO / MFA
27. Governance & Compliance / GRC
28. Document Management / DMS
29. Legal / Tax Reporting
30. Multi-company / Intercompany

#### Services
31. Service Management / Field Service
32. Supplier Collaboration
33. Contingent Workforce Management
34. Sustainability / ESG
35. Research & Development (R&D)

**Visual Design**:
- 6-column grid on desktop, 4 on tablet, 2 on mobile
- Icon + label + optional subtitle
- Hover: scale(1.02) with shadow elevation
- Category headers with collapsible sections
- Recently used modules pinned at top
- Favorites/starred modules highlighted

**Behavior**:
- Role-based visibility (modules hidden if no permission)
- Click navigates to module's default page
- Long-press/right-click opens module settings (if admin)
- Drag to reorder favorites (persisted to user preferences)

---

### 3.4 Zone 4: Alerts / Exceptions / Critical Actions

**Purpose**: Surface urgent items requiring immediate attention

**Alert Types**:
- Pending approvals (actionable)
- SLA breaches (time-critical)
- Critical treasury issues (financial risk)
- Overdue collections (cash flow risk)
- Overdue payables (compliance risk)
- Stock shortages (operational risk)
- Delayed deliveries (customer impact)
- Unassigned tasks (productivity risk)
- Unresolved issues (quality risk)
- Failed integrations (system risk)
- Expired/expiring documents (compliance risk)
- Maintenance critical alerts (asset risk)
- Quality exceptions (compliance risk)
- Compliance warnings (regulatory risk)
- Period-close reminders (finance risk)
- Audit-related exceptions (governance risk)

**Visual Design**:
- Severity-coded left border (Critical: red, Warning: amber, Info: blue)
- Icon indicating alert type
- Title + brief description
- Timestamp
- Action button (Approve, View, Dismiss)
- Filter pills (All, Critical, Warnings, Mine)

**Behavior**:
- Acknowledge/dismiss supported for non-critical alerts
- Click navigates to source module
- Real-time polling for new alerts (30s interval)
- Batch actions for multiple selections

---

### 3.5 Zone 5: Operational Overview

**Purpose**: Real-time operational status across modules

**Widgets**:

1. **WMS Health Widget**
   - Total inventory value
   - Stock-out count (critical low)
   - Low stock warnings
   - Reorder suggestions
   - Chart: Stock level trend (7 days)

2. **Logistics Status Widget**
   - Active shipments
   - On-time delivery rate
   - Delayed shipments
   - Pending pickups
   - Chart: Delivery performance (7 days)

3. **Production Watchlist** (if Manufacturing enabled)
   - Active work orders
   - Completed today
   - Bottleneck operations
   - Quality holds

4. **Service Calls Widget** (if Service enabled)
   - Open tickets
   - Avg response time
   - SLA compliance
   - Unassigned tickets

**Behavior**:
- Auto-refresh every 60 seconds
- Click any widget to drill down
- Expand/collapse for detail view

---

### 3.6 Zone 6: Financial & Business Snapshot

**Purpose**: CFO and financial manager overview

**Widgets**:

1. **Finance Summary**
   - Revenue (MTD/YTD)
   - Expenses (MTD/YTD)
   - Net Profit
   - vs Budget variance

2. **AP/AR Snapshot**
   - AR outstanding
   - AP outstanding
   - Due this week
   - Overdue amount

3. **Treasury Snapshot**
   - Cash position
   - 7-day forecast
   - Upcoming payments
   - Pending transfers

4. **Budget vs Actual**
   - Horizontal bar chart
   - By department/category
   - Variance percentage

**Visual Design**:
- CFO-grade styling
- Currency formatting based on company setting
- Sparklines for trend
- Drill-down on click

---

### 3.7 Zone 7: Workflow / Approval / SLA Zone

**Purpose**: Workflow status and approval queue

**Widgets**:

1. **My Approvals**
   - Count badge
   - List of pending items
   - Priority indicator
   - Due time
   - Quick approve/reject buttons

2. **Workflow Performance**
   - Avg completion time
   - SLA compliance rate
   - Pending instance count
   - Bottleneck indicators

3. **Escalations**
   - Escalated items count
   - By priority breakdown
   - Time since escalation

**Behavior**:
- Inline approve/reject with comment
- Bulk actions supported
- Filter by workflow type
- Sort by priority/due date

---

### 3.8 Zone 8: Flow / Communication / Notices

**Purpose**: Enterprise communication integration

**Widgets**:

1. **Recent Announcements**
   - Company-wide notices
   - Department announcements
   - Pin/unpin support

2. **Mentions & Alerts**
   - @mentions of current user
   - Action-required items
   - Due date reminders

3. **Team Activity**
   - Recent posts from followed channels
   - Collaborative project updates

4. **Quick Post**
   - Create announcement shortcut
   - Post to channel option

**Visual Design**:
- Modern feed style
- Avatar + name + timestamp
- Like/comment counts
- Priority pin indicator

---

### 3.9 Zone 9: Personal Productivity Zone

**Purpose**: Personalized to-do and shortcuts

**Widgets**:

1. **My Tasks**
   - Today's tasks
   - Overdue count
   - Upcoming deadlines
   - Check-off support

2. **My Issues**
   - Assigned to me
   - Priority breakdown
   - Status summary

3. **Recent Documents**
   - Last 5 accessed
   - Quick open
   - Share option

4. **Saved Filters**
   - Favorite saved searches
   - Quick apply

**Behavior**:
- Drag to reorder widgets
- Widget visibility toggles
- Compact/expanded mode

---

### 3.10 Zone 10: Reports & Analytics

**Purpose**: Quick access to reporting

**Widgets**:

1. **Executive Reports**
   - CFO Report
   - Operations Report
   - HR Report
   - Custom favorites

2. **Scheduled Reports**
   - My subscriptions
   - Next run time
   - Download latest

3. **Quick Analytics**
   - Top 5 most accessed
   - Recent exports
   - Scheduled exports

4. **BI Dashboard Shortcuts**
   - Link to Power BI / Tableau
   - Embedded analytics (if configured)

**Visual Design**:
- Card grid layout
- Report icon + title + description
- Last run/status indicator

---

### 3.11 Zone 11: AI Insights / Recommendations

**Purpose**: Intelligent recommendations (AI-ready architecture)

**Insight Categories**:

1. **Attention Needed**
   - Items requiring review
   - Anomaly detections
   - Risk indicators

2. **Predicted Bottlenecks**
   - Capacity constraints
   - Resource conflicts
   - Timeline risks

3. **Recommended Actions**
   - Prioritized action list
   - Impact estimation
   - One-click execute (where applicable)

**Insight Sources** (rule-based today, AI-ready tomorrow):
- Inventory: Stockout risk, overstocking, slow-moving items
- Finance: Budget variance, cash flow anomalies, payment delays
- Operations: Delivery delays, quality issues, capacity utilization
- HR: Attendance anomalies, overtime trends, turnover risk
- Workflow: Bottleneck detection, SLA risk, rejection patterns

**Visual Design**:
- Insight cards with confidence indicator
- Category icons
- Action buttons
- "Why this insight?" tooltip

---

### 3.12 Zone 12: Activity Timeline / Audit Highlights

**Purpose**: Recent activity audit trail

**Activity Types**:
- Record creations
- Approvals granted/denied
- Status transitions
- Document uploads
- Critical field changes
- User sessions
- System events

**Visual Design**:
- Vertical timeline
- Color-coded by category
- Expandable details
- Filter by date range
- Export capability

---

## 4. Role-Based Dashboard Behavior

### 4.1 Role Definitions

| Role | Primary KPIs | Visible Zones | Module Access |
|------|-------------|---------------|---------------|
| Global Admin | All | All (full) | All |
| Executive/CEO | Revenue, Profit, Growth | All (executive view) | Strategic modules |
| CFO | Financial metrics | Finance-focused | Finance, Reports |
| COO | Operations metrics | Operations-focused | Ops modules |
| Department Manager | Department KPIs | Department + personal | Department scope |
| Finance Manager | Treasury, AP/AR | Finance zone | Finance module |
| Treasury Manager | Cash, liquidity | Treasury zone | Treasury module |
| HR Manager | Headcount, attendance | HR zone | HR module |
| Warehouse Manager | Stock, movements | WMS zone | WMS module |
| Logistics Manager | Shipments, delivery | Logistics zone | TMS module |
| Quality Manager | Exceptions, compliance | Quality zone | QA module |
| Maintenance Manager | Work orders, downtime | Maintenance zone | EAM module |
| Auditor | Audit trail, compliance | Audit-focused | Read-only |
| Standard User | Personal tasks | Personal zone | Assigned modules |

### 4.2 Permission Matrix

| Zone | View | Edit | Dismiss | Export |
|------|------|------|---------|--------|
| Global Header | All | Context only | N/A | N/A |
| KPI Strip | All | N/A | N/A | N/A |
| Module Launcher | Based on permissions | Admin only | N/A | N/A |
| Alerts | Based on module permissions | N/A | Acknowledgable | N/A |
| Operational | Based on module permissions | N/A | N/A | N/A |
| Financial | Finance role + permissions | N/A | N/A | Finance role |
| Workflow | All | Approve/Reject | N/A | Manager |
| Flow | All | Based on permissions | N/A | N/A |
| Personal | Self only | Self only | N/A | Self |
| Reports | Based on report permissions | N/A | N/A | Report permission |
| AI Insights | All | N/A | N/A | Admin |
| Timeline | Based on audit permissions | N/A | N/A | Auditor |

---

## 5. Multilingual Support

### 5.1 Supported Languages

| Code | Language | Direction | Font Stack |
|------|----------|-----------|------------|
| en | English | LTR | Outfit |
| fa | Persian/Farsi | RTL | Vazirmatn |
| ar | Arabic | RTL | Tajawal |
| ru | Russian | LTR | Noto Sans |
| hi | Hindi | LTR | Noto Sans |
| es | Spanish | LTR | Outfit |
| zh | Chinese | LTR | Noto Sans |
| de | German | LTR | Outfit |

### 5.2 RTL Implementation

- `dir="auto"` on dynamic content
- CSS logical properties (margin-inline-start, padding-inline-end)
- Flexbox direction awareness
- Icon mirroring for directional icons (arrows, navigation)
- Number and date formatting per locale
- Currency formatting per locale

### 5.3 Translation Requirements

All dashboard elements must use translation keys:
- Zone titles and headers
- Widget titles and descriptions
- KPI labels and units
- Button labels
- Tooltip text
- Empty state messages
- Error messages
- Placeholder text
- Status labels

---

## 6. Technical Architecture

### 6.1 Route Structure

```
GET /                         → Main dashboard (index)
GET /dashboard/api/kpis      → KPI data endpoint
GET /dashboard/api/alerts    → Alerts endpoint
GET /dashboard/api/activities → Timeline endpoint
GET /dashboard/api/modules    → Module visibility endpoint
POST /dashboard/api/dismiss   → Dismiss alert
POST /dashboard/api/preferences → Save dashboard preferences
```

### 6.2 Data Loading Strategy

1. **Initial Load**: Server-rendered HTML with embedded data
2. **Lazy Load**: Zones load independently via AJAX
3. **Polling**: Real-time zones poll every 30-60 seconds
4. **Caching**: KPI data cached 60 seconds, alerts 30 seconds

### 6.3 Component Structure

```
templates/
  dashboard/
    index.html           ← Main dashboard (replaces index.html)
    widgets/
      kpi_card.html
      module_tile.html
      alert_item.html
      activity_item.html
      workflow_item.html
      insight_card.html
    partials/
      header.html
      footer.html
```

### 6.4 State Management

- **User Preferences**: Stored in `user_preferences` table
- **Dashboard Layout**: JSON in user preferences
- **Widget Visibility**: Boolean flags per widget
- **Favorites**: Array of module IDs

---

## 7. API Specifications

### 7.1 KPI Endpoint

```
GET /dashboard/api/kpis
Response: {
  "kpis": [
    {
      "id": "pending_approvals",
      "label": "Pending Approvals",
      "value": 12,
      "trend": "up",
      "trend_value": "+3",
      "severity": "warning",
      "link": "/workflow/my-approvals",
      "icon": "clipboard-check"
    }
  ],
  "generated_at": "2026-04-16T10:30:00Z"
}
```

### 7.2 Alerts Endpoint

```
GET /dashboard/api/alerts?severity=critical&limit=10
Response: {
  "alerts": [
    {
      "id": "alert_123",
      "type": "sla_breach",
      "severity": "critical",
      "title": "Invoice Approval Overdue",
      "message": "INV-2024-0890 is 3 days past SLA",
      "source_module": "finance",
      "source_link": "/finance/invoices/123",
      "created_at": "2026-04-14T08:00:00Z",
      "actions": ["view", "approve", "dismiss"]
    }
  ],
  "total_count": 45,
  "unread_count": 12
}
```

### 7.3 Module Visibility Endpoint

```
GET /dashboard/api/modules
Response: {
  "modules": [
    {
      "id": "treasury",
      "label": "Treasury & Cash Flow",
      "icon": "fa-wallet",
      "category": "finance",
      "url": "/finance/treasury/dashboard",
      "is_favorite": true,
      "is_recent": true,
      "permission": "view"
    }
  ],
  "categories": ["core_operations", "finance", "people", "commerce", "technology", "services"]
}
```

---

## 8. Responsive Breakpoints

| Breakpoint | Width | Columns | Zones |
|------------|-------|---------|-------|
| Desktop XL | > 1920px | 12 | All zones, 3-column layouts |
| Desktop | 1280-1919px | 12 | All zones, 2-column layouts |
| Laptop | 1024-1279px | 10 | All zones, stacked where needed |
| Tablet | 768-1023px | 6 | Collapsed zones, horizontal scroll KPIs |
| Mobile | < 768px | 4 | Single column, tabbed navigation |

---

## 9. Performance Requirements

- **Initial Load**: < 2 seconds (First Contentful Paint)
- **Time to Interactive**: < 3 seconds
- **Largest Contentful Paint**: < 2.5 seconds
- **Cumulative Layout Shift**: < 0.1
- **Zone Lazy Load**: < 500ms per zone
- **Polling Overhead**: < 100KB per minute

---

## 10. Accessibility Requirements

- **Keyboard Navigation**: Full tab navigation through all zones
- **Focus Indicators**: Visible focus rings on all interactive elements
- **ARIA Labels**: Proper labels on all icons, buttons, and regions
- **Screen Reader**: Semantic HTML with proper heading hierarchy
- **Color Contrast**: 4.5:1 minimum for text, 3:1 for large text
- **Reduced Motion**: Respect `prefers-reduced-motion` media query

---

## 11. Future Enhancements

1. **Custom Widget Builder** - Drag-and-drop custom widgets
2. **Dashboard Templates** - Pre-built dashboards per role
3. **Embedded Analytics** - Direct Power BI/Tableau embedding
4. **AI Copilot Integration** - Natural language dashboard queries
5. **Mobile Native App** - Dedicated iOS/Android dashboard
6. **Notification Center** - Unified notification management
7. **Collaboration Features** - Share dashboard views with team
8. **Audit Dashboard** - Dedicated audit and compliance view

---

*Document Version: 1.0*
*Last Updated: 2026-04-16*
*Author: Enterprise Dashboard Architecture*
