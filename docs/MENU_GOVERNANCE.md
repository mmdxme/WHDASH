# Menu Governance Report
## MMDx Navigation Consistency Analysis

---

## Executive Summary

This document provides a comprehensive analysis of the MMDx menu system, identifying inconsistencies, duplicates, missing elements, and standardization opportunities. The goal is to ensure a consistent, scalable, and business-logical navigation structure across all modules.

---

## 1. Consistency Issues Identified

### 1.1 Duplicate Names Across Modules

| Item Name | Found In | Issue | Recommendation |
|-----------|----------|-------|-----------------|
| Dashboard | Multiple modules | Every module has a "Dashboard" - this is correct but some are labeled differently | Standardize as "Dashboard" with module-specific KPIs |
| Overview | Multiple modules | Used inconsistently | Use "Overview" for dashboard-type views |
| Settings | Almost every module | Good consistency | Ensure all Settings have same child structure |
| Reports | Multiple modules | Good consistency | Add sub-structure (Summary, Detailed, Export) |
| Active | Various modules | Sometimes means "Active Records", sometimes "Currently Running" | Clarify with context |
| History | Various modules | Good pattern | Maintain as "History" for audit trails |

### 1.2 Naming Inconsistencies

| Current Name | Should Be | Module | Reason |
|--------------|-----------|--------|--------|
| My Work | My Tasks / Assigned to Me | Workflow | Clarity on what "work" means |
| Command Center | Executive Dashboard | Reports & Analytics | More descriptive name |
| Holding Dashboard | Group Dashboard | Reports & Analytics | Industry-standard term |
| CI Dashboard | Customer Intel Dashboard | Customer Intelligence | Clearer identification |
| E-commerce Dashboard | E-commerce Dashboard | E-commerce | Consistent with others |
| TRIAL BALANCE | Trial Balance Report | Finance | It's a report, not an account |
| General Ledger | General Ledger Report | Finance | It's a report, not a transaction |
| All Instances | Active Workflows | Workflow | More user-friendly |
| Failed Automations | Failed Rules | Workflow | Actionable naming |
| Notification Templates | Notification Templates | Workflow | Correct but expand structure |
| Notification Logs | Notification History | Workflow | Consistent with other "History" items |

### 1.3 Unclear Sections

| Section | Module | Issue | Recommendation |
|---------|--------|-------|----------------|
| Items / Parts | WMS | Ambiguous - could mean inventory items or bill of materials | Split into "Item Master" and "Bill of Materials" |
| Facilities | Maintenance | Unclear if it means building facilities or equipment | Clarify scope |
| Facility Requests | Maintenance | Ambiguous - same as "Requests"? | Merge or differentiate clearly |
| Local Purchasing | Procurement | Missing Import Purchasing children | Add parity with Import Purchasing |
| Channels | Marketing, E-commerce | Used differently in each module | Define consistently |
| Content | Marketing, Social Media | Both have content but different types | Add module prefix if needed |

### 1.4 Missing Level-3 Child Menus

#### Workflow Module - Missing:
- **Workflow Designer** children: Templates, Version History, Published, Draft
- **Automation Rules** children: Triggers, Conditions, Actions (instead of generic "rules")
- **Escalation Rules** children: SLA Settings, Escalation Paths

#### WMS Module - Missing:
- **Items** children: Barcode/Labels, Import, Export, Inactive Items
- **Locations** children: Zone Mapping, Putaway Rules, Pick Logic
- **Adjustments** children: Approval Workflow, Adjustment Reasons
- **Reports** children: Age Analysis, Dead Stock, Fast Moving Items

#### Finance Module - Missing:
- **Reports** children: P&L Statement, Cash Flow Statement, Cost Center Report
- **Settings** children: Currency Settings, Exchange Rates, Bank Accounts

#### Procurement Module - Missing:
- **Contracts** children: Draft, Active, Expiring, Renewals
- **Claims & Returns** children: Inspection Results, Credit Notes
- **Settings** children: Numbering Rules, Approval Policies

#### Sales Module - Missing:
- **Deliveries** children: Pending, In Transit, Delivered, Failed
- **Settings** children: Numbering Rules, Invoice Templates, Payment Terms

#### HR Module - Missing:
- **Documents** children: Types, Employee Documents, Expiry Alerts
- **Announcements** children: Draft, Scheduled, Active, Archive
- **Settings** children: Leave Policies, Payroll Rules, Approval Workflows

#### Quality Module - Missing:
- **Inspections** children: Inspection Types, Calibration Records
- **NCR** children: NCR Types, Root Cause Analysis, Corrective Actions
- **Audits** children: Audit Types, Auditor Management, Schedule

#### Assets Module - Missing:
- **Categories** children: Depreciation Rules, Insurance Policies
- **Depreciation** children: Depreciation Methods, Asset Valuation
- **Settings** children: Numbering Rules, Asset Types, Insurance

#### API Gateway Module - Missing:
- **Auth** children: OAuth Settings, API Keys, Token Management
- **Integrations** children: Connected Apps, Sync History
- **Settings** children: Security Rules, IP Whitelist, CORS

#### Issue Tracker Module - Missing (Entirely):
- **Dashboard** children: Overview, KPI Summary, Open Issues, SLA Breaches
- **All Issues** children: By Status, By Priority, By Category, By Assignee
- **My Issues** children: Reported by Me, Assigned to Me, Shared with Me
- **Reports** children: Issue Summary, Resolution Time, By Priority, Trend
- **Settings** children: General, Workflow, Notifications, SLA Rules

#### Task Center Module - Missing (Entirely):
- **Dashboard** children: Overview, My Tasks, Team Tasks
- **Task List** children: My Tasks, Team Tasks, Overdue, Completed
- **Sub Tasks** children: Open, In Progress, Completed, Linked Tasks
- **Reports** children: Productivity, Completion Rate, By User
- **Settings** children: General, Task Types, Workflow

---

## 2. Module Standardization Matrix

| Module | Dashboard | Master Data | Transactions | Reports | Settings | Status-Driven Views |
|--------|-----------|-------------|--------------|---------|----------|---------------------|
| Workflow | Yes | No | Yes | Yes | Yes | Yes |
| WMS | Yes | Yes | Yes | Yes | Yes | Yes |
| Maintenance | Yes | Yes | Yes | Yes | Yes | Yes |
| Logistics | Yes | Yes | Yes | Yes | Yes | Partial |
| Finance | Yes | Yes | Yes | Yes | Yes | Partial |
| Procurement | Yes | Yes | Yes | Yes | Yes | Yes |
| Sales | Yes | Yes | Yes | Yes | Yes | Yes |
| HR | Yes | Yes | Yes | Yes | Yes | Partial |
| Quality | Yes | Yes | Yes | Yes | Yes | Yes |
| Documents | Yes | Yes | Yes | Yes | Yes | Yes |
| Assets | Yes | Yes | Yes | Yes | Yes | Yes |
| API Gateway | Yes | Yes | No | Yes | Yes | No |
| Marketing | Yes | Yes | Yes | Yes | Yes | Partial |
| Customer Intel | Yes | Yes | No | Yes | Yes | No |
| E-commerce | Yes | Yes | Yes | Yes | Yes | No |
| Social Media | Yes | Yes | Yes | Yes | Yes | No |
| Planning | Yes | Yes | Yes | Yes | Yes | No |
| Issue Tracker | No | No | No | No | No | No |
| Task Center | No | No | No | No | No | No |

### Legend:
- **Yes** = Fully implemented with proper child structure
- **Partial** = Partially implemented, needs completion
- **No** = Missing or not properly structured

---

## 3. Recommendations by Priority

### HIGH PRIORITY (Critical Issues)

1. **Issue Tracker** - Currently flat structure with `items: None`
   - Add full 3-level hierarchy as defined in Menu Architecture
   
2. **Task Center** - Currently flat structure with `items: None`
   - Add full 3-level hierarchy as defined in Menu Architecture

3. **WMS Adjustments** - Missing proper transactional children
   - Add: Positive, Negative, Pending Approval, History

4. **Finance Reports** - Missing standard financial reports
   - Add: P&L, Cash Flow, Cost Center reports

5. **Procurement Contracts** - No child structure
   - Add: Draft, Active, Expiring, Archived

### MEDIUM PRIORITY (Standardization)

6. **HR Documents** - No child structure
   - Add: Document Types, Employee Documents, Expiry Alerts

7. **Quality Inspections** - Missing inspection types
   - Add: Incoming, In-Process, Outgoing, Failed

8. **Assets Depreciation** - Missing methods and valuation
   - Add: Depreciation Methods, Asset Valuation

9. **API Gateway Auth** - Missing OAuth and token management
   - Add: OAuth Settings, API Keys, Token Management

### LOW PRIORITY (Consistency)

10. **Sales Deliveries** - Missing status-driven children
    - Add: Pending, In Transit, Delivered, Exceptions

11. **Marketing Channels** - Clarify if master data or transactions
    - Add appropriate children based on decision

12. **Social Media Accounts** - Missing account-specific settings
    - Add: Platform Settings, Connected Accounts

---

## 4. Structural Issues

### 4.1 Orphaned Items (Items with no children that should have children)

| Item | Module | Current State | Recommendation |
|------|--------|---------------|----------------|
| `items` | WMS | Points to `/settings` | Create proper Item Master with children |
| `locations` | WMS | Points to `/location_settings` | Create proper location management |
| `receipts` | WMS | Flat list | Add putaway workflow children |
| `shipments` | WMS | Flat list | Add fulfillment status children |

### 4.2 Inconsistent Dividers

Some modules use `divider_*` naming convention, others don't:
- Workflow: Consistent with dividers
- WMS: No dividers used
- Finance: No dividers used
- HR: No dividers used

**Recommendation**: Add consistent dividers between logical groups in all modules

### 4.3 Route Consistency Issues

| Module | Route Pattern | Issue |
|--------|---------------|-------|
| WMS | Mixed `/api/`, `/wms/`, `/stock-sync` | Should be `/wms/` |
| Procurement | Mixed `/procurement/`, `/po/` | Standardize |
| Assets | Consistent `/assets/` | OK |
| Quality | Consistent `/quality/` | OK |

---

## 5. Permission Structure Analysis

### 5.1 Permission Naming Convention

Current pattern: `('module', 'resource', 'action')`

| Module | Convention Status |
|--------|-------------------|
| Workflow | Consistent |
| WMS | Consistent |
| Finance | Consistent |
| Procurement | Consistent |
| HR | Consistent |
| Quality | Consistent |
| Assets | Consistent |
| API Gateway | Uses `('platform', ...)` instead of `('api_gateway', ...)` |

### 5.2 Modules with Non-Standard Permissions

| Module | Current | Should Be |
|--------|---------|-----------|
| API Gateway | `('platform', 'settings', 'view')` | `('api_gateway', ...)` |
| Management Dashboard | `('reports', 'executive', 'view')` | Consistent with other report modules |
| Advanced Reporting | `('reports', 'executive', 'view')` | Consistent |

---

## 6. Internationalization (i18n) Coverage

### 6.1 Modules Missing Translations

| Module | label_ar | label_fa |
|--------|----------|----------|
| Most modules | Present | Present |
| Issue Tracker | Missing | Missing |
| Task Center | Missing | Missing |
| E-commerce | Partial | Partial |

### 6.2 Translation Quality Issues

1. **Arithmetic operators in translations**: `label_ar: ' NCRs المفتوحة'` has leading space
2. **Inconsistent casing**: Some use Title Case, others use UPPERCASE
3. **Placeholder text**: `'---'` used as divider label instead of `None`

---

## 7. Action Items

### Immediate Actions

1. [ ] Add Level-3 children to Issue Tracker module
2. [ ] Add Level-3 children to Task Center module
3. [ ] Fix API Gateway permission tuple to use `api_gateway` prefix
4. [ ] Add dividers to WMS, Finance, HR modules for logical grouping
5. [ ] Fix translation spacing issues in Quality module

### Short-term Actions (Week 1-2)

6. [ ] Expand WMS Adjustments with proper transactional children
7. [ ] Add Finance Reports sub-structure (P&L, Cash Flow, etc.)
8. [ ] Add Procurement Contracts children (Draft, Active, Expiring)
9. [ ] Add HR Documents children (Types, Employee Documents, Expiry)
10. [ ] Standardize all routes to use module prefix

### Medium-term Actions (Week 3-4)

11. [ ] Add Quality Inspections children (Types, Calibration)
12. [ ] Add Assets Depreciation methods and valuation
13. [ ] Add API Gateway Auth children (OAuth, API Keys)
14. [ ] Complete translation coverage for Issue Tracker
15. [ ] Complete translation coverage for Task Center

### Long-term Actions (Month 2+)

16. [ ] Review and standardize all report children across modules
17. [ ] Implement consistent permission naming across all modules
18. [ ] Create menu governance documentation for new development
19. [ ] Establish menu review process for new features
20. [ ] Build automated menu validation tests

---

## 8. Best Practices Established

### 8.1 Menu Item Naming

1. **Use descriptive, action-oriented names**: "Pending Approval" not "Pending"
2. **Use consistent verb forms**: "Create", "View", "Edit", "Delete", "Archive"
3. **Avoid abbreviations**: "Dashboard" not "Dash", "Settings" not "Opts"
4. **Use noun phrases for master data**: "Customer Master", "Item Master"
5. **Use verb phrases for actions**: "Create New", "View All", "Export"

### 8.2 Menu Structure

1. **Always start with Dashboard** as the first item
2. **Use dividers to group related items**: Master Data, Transactions, Reports, Settings
3. **Order items logically**: Dashboard first, then operational items, then support items
4. **Keep similar items together**: All reports should be grouped, all settings together
5. **Limit top-level items to 7 ± 2**: Consider sub-grouping if more than 9 items

### 8.3 Permissions

1. **Always use tuple format**: `('module', 'resource', 'action')`
2. **Use consistent action names**: 'view', 'create', 'edit', 'delete', 'manage'
3. **Group related permissions**: Use consistent 'settings', 'reports', 'audit' resources
4. **Set `permission: None` for public items** like Profile

### 8.4 Internationalization

1. **Always provide all three labels**: `label`, `label_ar`, `label_fa`
2. **Use proper Arabic/Farsi typography**: Avoid ASCII art in translations
3. **Don't use placeholder text** like `'---'` for dividers
4. **Translate meaning, not words**: "Open" in Arabic should convey the business concept

---

## 9. Compliance Checklist

Use this checklist when adding new menus:

- [ ] Menu key follows `module_section_item` naming convention
- [ ] All three labels provided (en, ar, fa)
- [ ] Icon specified with proper FontAwesome class
- [ ] Route follows module-prefixed URL pattern
- [ ] Permission tuple uses correct module prefix
- [ ] Dividers used between logical groups
- [ ] Children added for transactional submenus (if applicable)
- [ ] Settings has appropriate child structure
- [ ] Reports has appropriate child structure (if applicable)
- [ ] Translations reviewed by native speaker (if possible)

---

## 10. Change Log

| Date | Change | Author | Version |
|------|--------|--------|---------|
| 2026-04-11 | Initial governance report | System | 1.0 |
| - | - | - | - |

---

## Appendix A: Current Module Inventory

| Module Key | Label | Order | Items Count | Has Children |
|------------|-------|-------|-------------|---------------|
| profile | My Profile | -1 | 16 | Yes |
| dashboard | Dashboard | 0 | 0 | No |
| workflow | Workflow | 0.5 | 30+ | Yes |
| forms | Form Builder | 0.4 | 10+ | Yes |
| warehouse | Warehouse | 3 | 11 | Yes |
| assets | Asset Management | 3.5 | 15+ | Yes |
| maintenance | Maintenance | 3.6 | 20+ | Yes |
| logistics | Logistics | 4 | 9 | Yes |
| finance | Finance | 5 | 20+ | Yes |
| procurement | Procurement | 5 | 15+ | Yes |
| planning | Planning | 6 | 9 | Yes |
| hr | HR | 7 | 15+ | Yes |
| marketing | Marketing | 8 | 10+ | Yes |
| customer_intelligence | Customer Intel | 9 | 7 | Yes |
| tasks | Tasks | 10 | 0 | No |
| issues | Issues | 11 | 0 | No |
| reports | Reports | 12 | 1 | Yes |
| advanced_reporting | Advanced Reporting / BI | 12.5 | 25+ | Yes |
| api_gateway | API Gateway | 13 | 30+ | Yes |
| management_dashboard | Management Dashboard | 13 | 10+ | Yes |
| quality | Quality Management | 13 | 20+ | Yes |
| ecommerce | E-commerce Integration | 13.5 | 15+ | Yes |
| social_media | Social Media | 13.7 | 9 | Yes |
| admin | Admin | 14 | 10+ | Yes |

---

## Appendix B: Issue Tracker Target Structure

```
Issue Tracker
├── Dashboard
│   ├── Overview
│   ├── KPI Summary
│   ├── Open Issues
│   └── SLA Breaches
├── All Issues
│   ├── By Status
│   ├── By Priority
│   ├── By Category
│   └── By Assignee
├── My Issues
│   ├── Reported by Me
│   ├── Assigned to Me
│   └── Shared with Me
├── Backlog
│   ├── Backlog Items
│   ├── Prioritized
│   └── Unprioritized
├── In Progress
│   ├── Active
│   ├── Paused
│   └── Blocked
├── Pending Review
│   ├── Awaiting Review
│   └── Feedback
├── Resolved
│   ├── Recently Resolved
│   └── Verification Pending
├── Closed
│   ├── Closed This Week
│   ├── Closed This Month
│   └── Archive
├── Priorities
│   ├── Priority Master
│   └── SLA Settings
├── Categories
│   ├── Category Master
│   └── Subcategories
├── SLA Breaches
│   ├── Breached
│   └── At Risk
├── Reports
│   ├── Issue Summary
│   ├── Resolution Time
│   ├── By Priority
│   ├── By Category
│   └── Trend Analysis
└── Settings
    ├── General
    ├── Workflow
    ├── Notifications
    ├── SLA Rules
    └── Audit Log
```

---

## Appendix C: Task Center Target Structure

```
Task Center
├── Dashboard
│   ├── Overview
│   ├── KPI Summary
│   ├── My Tasks
│   └── Team Tasks
├── Task List
│   ├── My Tasks
│   ├── Team Tasks
│   ├── Overdue
│   └── Completed
├── Task Command Center
│   ├── Queue
│   ├── Priority Board
│   ├── SLA View
│   └── Escalations
├── Sub Tasks
│   ├── Open
│   ├── In Progress
│   ├── Completed
│   └── Linked Tasks
├── Transactions
│   ├── Task Logs
│   ├── Time Logs
│   ├── Status History
│   └── Assignment History
├── Reports
│   ├── Productivity
│   ├── Completion Rate
│   ├── By User
│   └── By Department
└── Settings
    ├── General
    ├── Task Types
    ├── Workflow
    └── Notifications
```
