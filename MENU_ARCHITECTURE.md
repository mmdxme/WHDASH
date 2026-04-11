# MMDx Menu Architecture
## 3-Level Hierarchical Navigation Structure

---

## Overview

This document defines the complete 3-level menu architecture for the MMDx enterprise ERP system. The structure follows consistent design patterns across all modules, ensuring scalability, business-logical organization, and enterprise-grade usability.

### Design Principles

1. **Level 1 (Main Menu)**: Top-level module grouping (e.g., Workflow, WMS, Finance)
2. **Level 2 (Submenu)**: Functional area within a module (e.g., Dashboard, Transactions, Reports)
3. **Level 3 (Child Menu)**: Specific operational views, statuses, reports, or settings

### Design Patterns Applied

| Submenu Type | Level-3 Children Pattern |
|-------------|-------------------------|
| Dashboard | Overview, KPI Summary, Alerts, Quick Actions, Recent Activity |
| Master Data | All Records, Create New, Categories, Import, Export, Archive, Audit History |
| Transactional | New, Drafts, Pending, Approved, In Progress, Completed, Cancelled, Documents, Reports |
| Approval/Review | Pending Review, Approved, Rejected, Returned, Escalated, History |
| Report-based | Summary, Detailed, Trend Analysis, By Status, By User, Export Center, Saved Views |
| Settings | General, Numbering Rules, Workflow Rules, Permissions, Notifications, Integrations, Audit Log |

---

## Complete Menu Tree

### 1. Dashboard
- **Dashboard**
  - Overview
  - KPI Summary
  - Alerts
  - Shortcuts
  - Recent Activity

### 2. Workflow
- **Dashboard**
  - Overview
  - KPI Summary
  - Delayed Items
  - SLA Alerts
- **My Work**
  - Assigned to Me
  - Due Today
  - Overdue
  - Completed by Me
- **My Approvals**
  - Pending Approvals
  - Approved by Me
  - Rejected by Me
  - Returned by Me
- **Workflow Designer**
  - Canvas
  - Nodes
  - Transitions
  - Publish / Versioning
- **Definitions**
  - All Definitions
  - Create Definition
  - Active
  - Archived
- **Templates**
  - All Templates
  - Create Template
  - Draft Templates
  - Published Templates
- **Process Modeling**
  - Flow Maps
  - Swimlanes
  - Conditions
  - Simulation
- **Automation Rules**
  - Active Rules
  - Failed Rules
  - Create Rule
  - Execution Logs
- **Performance Report**
  - Summary
  - By Workflow
  - By User
  - Trend
- **Settings**
  - General
  - SLA Rules
  - Notifications
  - Audit Log

### 3. Reports & Analytics
- **Command Center**
  - Executive View
  - Operational View
  - Exceptions
  - Saved Views
- **BI Dashboard**
  - KPI Boards
  - Trends
  - Comparisons
  - Drilldowns
- **BI Reports**
  - Summary Reports
  - Detailed Reports
  - Scheduled Reports
  - Export Center

### 4. WMS (Warehouse Management)
- **Dashboard**
  - Stock KPIs
  - Alerts
  - Fast Moving
  - Dead Stock
- **Inventory**
  - Current Stock
  - By Warehouse
  - By Location
  - Reserved Stock
- **Stock Movements**
  - Inbound
  - Outbound
  - Internal Moves
  - Movement History
- **Items**
  - Item Master
  - Create Item
  - Categories
  - Brands
  - UOM
  - Barcode / Labels
- **Locations**
  - Warehouse Zones
  - Bins
  - Capacity
  - Location Mapping
- **Stock Count**
  - Count Plans
  - Open Counts
  - Variances
  - Count History
- **Receipts**
  - New Receipt
  - Pending Putaway
  - Received Today
  - Receipt History
- **Shipments**
  - New Shipment
  - Picking
  - Packed
  - Dispatched
  - Shipment History
- **Returns**
  - Customer Returns
  - Supplier Returns
  - Pending Inspection
  - Closed Returns
- **Transfers**
  - New Transfer
  - Pending Approval
  - In Transit
  - Completed Transfers
- **Adjustments**
  - Positive Adjustments
  - Negative Adjustments
  - Pending Approval
  - History
- **Putaway**
  - Pending
  - Assigned
  - Completed
  - Putaway Rules
- **Pickup**
  - Picking Queue
  - Assigned Picks
  - Completed Picks
  - Short Picks
- **Reports**
  - Stock Balance
  - Movement Report
  - Ageing
  - Valuation
  - By Location
- **Settings**
  - Warehouse Settings
  - Location Rules
  - Numbering
  - Notifications

### 5. Maintenance
- **Dashboard**
  - Overview
  - KPI Summary
  - Open Work Orders
  - Overdue
- **Equipment**
  - Register
  - Categories
  - Status
  - History
- **PM Plans**
  - All Plans
  - Create Plan
  - Active Plans
  - Archived Plans
- **Work Orders**
  - New
  - Open
  - In Progress
  - Completed
  - Closed
- **Technicians**
  - Team List
  - Skills
  - Workload
  - Performance
- **Reports**
  - PM Compliance
  - Downtime
  - Labor
  - Parts Usage
- **Settings**
  - General
  - SLA Rules
  - Notifications
  - Audit Log

### 6. Logistics
- **Dashboard**
  - Overview
  - KPI Summary
  - Active Trips
  - Exceptions
- **Trips**
  - Planned
  - Active
  - Completed
  - Cancelled
- **Routes**
  - Route Master
  - Route Plans
  - Route Optimization
  - Route History
- **Dispatch**
  - Dispatch Queue
  - Assigned
  - In Transit
  - Delivered
- **Vehicles**
  - Fleet List
  - Maintenance Status
  - Documents
  - Utilization
- **Drivers**
  - Driver List
  - License Tracking
  - Assignments
  - Performance
- **Reports**
  - Trip Summary
  - Delivery Performance
  - Utilization
  - Cost Analysis
- **Settings**
  - General
  - Route Rules
  - Driver Policies
  - Notifications

### 7. Finance
- **Dashboard**
  - Overview
  - KPI Summary
  - Cash Position
  - Alerts
- **Accounts**
  - Chart of Accounts
  - Create Account
  - Account Groups
  - Inactive Accounts
- **Journals**
  - Draft Entries
  - Posted Entries
  - Recurring Entries
  - Approval Queue
- **AR Invoices**
  - Draft Invoices
  - Posted Invoices
  - Overdue
  - Credit Notes
- **AR Receipts**
  - New Receipt
  - Applied
  - Unapplied
  - Reconciliation
- **AP Bills**
  - Draft Bills
  - Posted Bills
  - Due Soon
  - Overdue
- **AP Payments**
  - Payment Queue
  - Paid
  - Scheduled
  - Reconciliation
- **Budgets**
  - Annual
  - Departmental
  - Revisions
  - Variance Analysis
- **Balance Sheet**
  - Current Period
  - Comparative
  - Monthly Trend
  - Export
- **Tax**
  - Tax Codes
  - VAT Transactions
  - Tax Reports
  - Settings
- **Reports**
  - Trial Balance
  - General Ledger
  - Accounts Receivable Aging
  - Accounts Payable Aging
  - Cash Flow
  - Profit & Loss
  - Export Center
- **Settings**
  - Fiscal Years
  - Cost Centers
  - Numbering Rules
  - Currency Settings
  - Audit Log

### 8. Procurement
- **Dashboard**
  - Overview
  - KPI Summary
  - Open POs
  - Expiring Contracts
- **Suppliers**
  - Supplier Master
  - New Supplier
  - Approved Suppliers
  - Inactive Suppliers
- **Requisitions**
  - New PR
  - Draft PR
  - Pending Approval
  - Approved PR
- **RFQs**
  - New RFQ
  - Open RFQs
  - Closed RFQs
  - Comparison Sheet
- **Quotations**
  - Received Quotes
  - Comparison
  - Selected
  - Rejected
- **Orders**
  - Draft POs
  - Approved POs
  - Open POs
  - Closed POs
- **Receiving**
  - Pending Receipt
  - Partial Receipt
  - Completed Receipt
  - GRN History
- **Shipment Tracking**
  - Incoming
  - In Transit
  - Delivered
  - Exceptions
- **Claims & Returns**
  - Open Claims
  - Under Review
  - Resolved
  - Supplier Returns
- **Contracts**
  - Active Contracts
  - Draft Contracts
  - Expiring Soon
  - Archived
- **Reports**
  - Supplier Performance
  - PO Status
  - Lead Time
  - Claims Analysis
  - Spend Analysis
- **Settings**
  - General
  - Numbering Rules
  - Approval Workflow
  - Notifications
  - Audit Log

### 9. Sales
- **Dashboard**
  - Overview
  - KPI Summary
  - Pipeline Summary
  - Alerts
- **Customers**
  - Customer Master
  - New Customer
  - Segments
  - Inactive Customers
- **Inquiries**
  - New Inquiry
  - Open Inquiries
  - Follow-up
  - Closed
- **Opportunities**
  - Pipeline
  - By Stage
  - Won
  - Lost
- **Quotations**
  - Draft Quotes
  - Sent Quotes
  - Approved Quotes
  - Expired Quotes
- **Orders**
  - Draft Orders
  - Confirmed
  - Pending Delivery
  - Closed
- **Reservations**
  - Active Reservations
  - Expired
  - Converted to Order
  - Cancelled
- **Deliveries**
  - Pending
  - In Transit
  - Delivered
  - Exceptions
- **Returns**
  - Customer Returns
  - Pending Inspection
  - Closed Returns
- **Reports**
  - Sales Summary
  - By Customer
  - By Item
  - By Salesperson
  - Pipeline Report
  - Conversion Analysis
- **Settings**
  - General
  - Numbering Rules
  - Pricing Rules
  - Notifications
  - Audit Log

### 10. HR
- **Dashboard**
  - Overview
  - KPI Summary
  - Headcount
  - Alerts
- **Employees**
  - Employee List
  - Active Employees
  - Inactive Employees
  - Employee Profiles
  - Documents
- **Add Employee**
  - New Hire
  - Bulk Import
  - Onboarding Checklist
  - Approval
- **Departments**
  - Department List
  - Create Department
  - Hierarchy
  - Inactive
- **Positions**
  - Position Master
  - Create Position
  - Active
  - Inactive
- **Attendance**
  - Daily Attendance
  - Monthly Summary
  - Exceptions
  - Corrections
- **Leave**
  - Leave Requests
  - Leave Balance
  - Pending Approval
  - Leave Calendar
- **Payroll**
  - Payroll Run
  - Adjustments
  - Payslips
  - Payroll History
- **Overtime**
  - Overtime Requests
  - Pending Approval
  - Approved
  - History
- **Training**
  - Training Sessions
  - Participants
  - Schedules
  - Certificates
- **Documents**
  - Document Types
  - Employee Documents
  - Expiry Alerts
  - Archives
- **Announcements**
  - Active Announcements
  - Draft
  - Scheduled
  - Archive
- **Recruitment**
  - Open Positions
  - Candidates
  - Interviews
  - Offers
- **Performance**
  - Reviews
  - Goals
  - Appraisal Cycles
  - History
- **Reports**
  - Headcount Report
  - Attendance Summary
  - Leave Balance
  - Payroll Summary
  - Turnover Analysis
- **Settings**
  - General
  - Leave Policies
  - Payroll Rules
  - Approval Workflows
  - Notifications
  - Audit Log

### 11. Quality
- **Dashboard**
  - Overview
  - KPI Summary
  - Open NCRs
  - CAPA Status
- **Inspections**
  - Incoming
  - In-Process
  - Outgoing
  - Failed Inspections
  - Inspection History
- **Non-Conformance (NCR)**
  - Open NCRs
  - Under Review
  - Closed NCRs
  - Root Cause
  - Overdue NCRs
- **CAPA**
  - Open CAPAs
  - In Progress
  - Effectiveness Review
  - Closed CAPAs
  - Overdue CAPAs
- **Audits**
  - Audit Plan
  - Active Audits
  - Findings
  - Closed Audits
- **Reports**
  - Inspection Summary
  - NCR Analysis
  - CAPA Effectiveness
  - Audit Findings
- **Settings**
  - General
  - Inspection Types
  - NCR Categories
  - CAPA Workflows
  - Notifications
  - Audit Log

### 12. Documents
- **Dashboard**
  - Overview
  - Recent
  - Pending Signature
  - Expiring Soon
- **All Documents**
  - Active
  - Draft
  - Expired
  - Restricted
- **My Documents**
  - Created by Me
  - Shared with Me
  - Pending Signature
  - Recent
- **Categories**
  - Category Master
  - Access Rules
  - Retention Rules
  - Archive Rules
- **Tags**
  - Tag Master
  - Usage Report
- **Links**
  - Document Links
  - External References
- **Versions**
  - Version History
  - Compare Versions
- **Templates**
  - Document Templates
  - Create Template
- **Signatures**
  - Pending Signatures
  - Completed Signatures
  - Signature Requests
- **Reports**
  - Document Usage
  - Access Log
  - Storage Report
  - Expiry Report
- **Settings**
  - Numbering
  - Access Control
  - Retention Policy
  - Audit Log

### 13. Assets
- **Dashboard**
  - Overview
  - KPI Summary
  - Depreciation Status
  - Alerts
- **Asset Register**
  - Active Assets
  - Inactive Assets
  - By Category
  - By Location
- **Categories**
  - Category Master
  - Depreciation Rules
  - Inactive
- **Depreciation**
  - Depreciation Runs
  - Asset Depreciation
  - Depreciation Schedule
  - History
- **Maintenance**
  - Maintenance Requests
  - Work Orders
  - Schedules
  - Work Logs
  - Costs
- **Disposal**
  - Draft Disposal
  - Pending Approval
  - Approved
  - Completed
- **Transfers**
  - New Transfer
  - Pending
  - Completed
  - History
- **Reports**
  - Asset Register
  - Depreciation
  - Movement
  - Disposal
  - Maintenance Cost
- **Settings**
  - General
  - Numbering Rules
  - Depreciation Methods
  - Categories
  - Notifications
  - Audit Log

### 14. API Gateway
- **Dashboard**
  - Overview
  - API Health
  - Traffic Summary
  - Errors
- **REST API**
  - Routes
  - Versions
  - Request Logs
  - API Explorer
- **Auth**
  - API Clients
  - Scopes
  - Access Policies
- **Integrations**
  - Profiles
  - Sync Jobs
  - Exceptions
- **Webhooks**
  - Event Catalog
  - Subscriptions
  - Delivery Logs
  - Failed Deliveries
- **Documentation**
  - Guides
  - OpenAPI / Swagger
  - Error Codes
- **Monitoring**
  - Usage Metrics
  - Error Metrics
  - Rate Limits
  - Health Status
- **Settings**
  - General
  - Rate Limiting
  - Security Rules
  - Notifications
- **Audit Logs**
  - All Logs
  - By Client
  - By Event Type

### 15. Email Management
- **Inbox**
  - Unread
  - Flagged
  - Archived
  - Spam Review
- **All Emails**
  - Sent
  - Received
  - Drafts
  - Deleted
- **Compose**
  - New Email
  - Templates
  - Scheduled
  - Signatures
- **Account Settings**
  - SMTP/IMAP
  - Aliases
  - Signatures
  - Sync

### 16. Issue Tracker
- **Dashboard**
  - Overview
  - KPI Summary
  - Open Issues
  - SLA Breaches
- **All Issues**
  - By Status
  - By Priority
  - By Category
  - By Assignee
- **My Issues**
  - Reported by Me
  - Assigned to Me
  - Shared with Me
- **Backlog**
  - Backlog Items
  - Prioritized
  - Unprioritized
- **In Progress**
  - Active
  - Paused
  - Blocked
- **Pending Review**
  - Awaiting Review
  - Feedback
- **Resolved**
  - Recently Resolved
  - Verification Pending
- **Closed**
  - Closed This Week
  - Closed This Month
  - Archive
- **Priorities**
  - Priority Master
  - SLA Settings
- **Categories**
  - Category Master
  - Subcategories
- **SLA Breaches**
  - Breached
  - At Risk
- **Reports**
  - Issue Summary
  - Resolution Time
  - By Priority
  - By Category
  - Trend Analysis
- **Settings**
  - General
  - Workflow
  - Notifications
  - SLA Rules
  - Audit Log

### 17. Task Center
- **Dashboard**
  - Overview
  - KPI Summary
  - My Tasks
  - Team Tasks
- **Task List**
  - My Tasks
  - Team Tasks
  - Overdue
  - Completed
- **Task Command Center**
  - Queue
  - Priority Board
  - SLA View
  - Escalations
- **Sub Tasks**
  - Open
  - In Progress
  - Completed
  - Linked Tasks
- **Transactions**
  - Task Logs
  - Time Logs
  - Status History
  - Assignment History
- **Reports**
  - Productivity
  - Completion Rate
  - By User
  - By Department
- **Settings**
  - General
  - Task Types
  - Workflow
  - Notifications

### 18. Planning
- **Forecast Center**
  - Overview
  - By Period
  - By Product
  - By Region
- **Demand Analysis**
  - Demand Forecasts
  - Historical Analysis
  - Seasonal Patterns
- **Inventory Health**
  - Stock Level
  - Reorder Points
  - Dead Stock
  - Excess Inventory
- **Replenishment**
  - Suggestions
  - Approved
  - In Progress
  - History
- **Purchase Suggestions**
  - Pending
  - Approved
  - Rejected
  - Converted to PO
- **Scenarios**
  - What-If Analysis
  - Saved Scenarios
- **Alerts**
  - Active Alerts
  - Acknowledged
  - Settings
- **Reports**
  - Forecast Accuracy
  - Stock Coverage
  - Replenishment Summary
- **Settings**
  - General
  - Forecasting Methods
  - Alert Thresholds

### 19. Marketing
- **Dashboard**
  - Overview
  - KPI Summary
  - Campaign Performance
  - Budget Utilization
- **Campaigns**
  - All Campaigns
  - Active
  - Draft
  - Completed
  - Archived
- **Leads**
  - New Leads
  - Qualified
  - Converted
  - Lost
- **Channels**
  - Channel Master
  - Performance
- **Content**
  - Content Library
  - Create Content
  - Scheduled
  - Published
- **Advertisements**
  - Ad Campaigns
  - Ad Groups
  - Performance
- **Offers**
  - Active Offers
  - Scheduled
  - Expired
- **Budgets**
  - Budget Overview
  - Allocations
  - Revisions
- **Reports**
  - Campaign ROI
  - Lead Conversion
  - Channel Performance
  - Budget Analysis
- **Settings**
  - General
  - Campaign Types
  - Budget Rules
  - Notifications

### 20. Customer Intelligence
- **Dashboard**
  - Overview
  - Risk Score
  - Churn Alerts
  - Recommendations
- **Customer Profiles**
  - All Profiles
  - By Segment
  - At Risk
  - High Value
- **Segments**
  - Segment Master
  - Segment Rules
  - Dynamic Segments
- **Forecasts**
  - Churn Prediction
  - Lifetime Value
  - Demand Forecast
- **Risk Alerts**
  - Active Alerts
  - Acknowledged
  - Risk Level
- **Recommendations**
  - Actionable Insights
  - Personalization
- **Reports**
  - Customer Health Score
  - Segment Analysis
  - Churn Analysis
  - Lifetime Value Report
- **Settings**
  - General
  - Risk Rules
  - Scoring Model
  - Notifications

### 21. E-commerce Integration
- **Dashboard**
  - Overview
  - Order Sync
  - Inventory Sync
  - Error Summary
- **Channels**
  - Channel Master
  - Active Channels
  - Settings
- **Products**
  - Product Catalog
  - Sync Status
  - Variations
  - Pricing
- **Orders**
  - Imported Orders
  - Synced Orders
  - Failed Sync
- **Inventory**
  - Stock Sync
  - Reserved Stock
  - Sync History
- **Mappings**
  - Category Mapping
  - Attribute Mapping
  - Price Rules
- **Reports**
  - Sync Log
  - Order Performance
  - Error Analysis
- **Settings**
  - General
  - Sync Rules
  - Webhook Settings
  - Notifications

### 22. Social Media
- **Dashboard**
  - Overview
  - Engagement
  - Publishing Queue
- **Accounts**
  - Connected Accounts
  - Account Settings
- **Content**
  - Content Library
  - Create Post
  - Scheduled
  - Published
- **Calendar**
  - Monthly View
  - Weekly View
  - Content Queue
- **Publishing**
  - Queue
  - Published
  - Failed
- **Engagement**
  - Incoming Messages
  - Responses
  - Automation Rules
- **Leads**
  - Captured Leads
  - By Campaign
  - By Source
- **Campaigns**
  - Campaign Master
  - Performance
- **Reports**
  - Engagement Report
  - Growth Report
  - Content Performance
- **Settings**
  - General
  - Platform Settings
  - Notification Rules

### 23. Admin / Platform Settings
- **Dashboard**
  - System Overview
  - Active Users
  - System Health
- **Users**
  - User List
  - Active Users
  - Inactive Users
  - Pending Approval
- **Roles**
  - Role Master
  - Permissions
  - Inactive Roles
- **Modules**
  - Module List
  - Enable/Disable
  - Module Settings
- **Company**
  - Company Profile
  - Branches
  - Departments
- **Numbering**
  - Numbering Rules
  - Format Templates
- **Localization**
  - Languages
  - Translations
  - Date/Time Format
  - Currency Settings
- **Notifications**
  - Templates
  - Channels
  - History
- **Audit Logs**
  - All Logs
  - By User
  - By Module
  - By Action Type
- **Integrations**
  - API Keys
  - Webhooks
  - Connected Apps
- **System**
  - General Settings
  - Security Settings
  - Backup Settings
  - Cache Management

---

## Module Ordering

| Order | Module |
|------|--------|
| 0 | Dashboard |
| 0.4 | Form Builder |
| 0.5 | Workflow |
| 1 | Warehouse (WMS) |
| 2 | Procurement |
| 3 | Sales |
| 3.5 | Asset Management |
| 3.6 | Maintenance |
| 4 | Logistics |
| 5 | Finance |
| 6 | Planning |
| 7 | HR |
| 8 | Marketing |
| 9 | Customer Intelligence |
| 10 | Quality |
| 11 | E-commerce Integration |
| 12 | Social Media |
| 13 | API Gateway |
| 13.5 | Reports & Analytics |
| 14 | Admin / Platform Settings |

---

## Design Standards Summary

### Level-3 Naming Conventions

| Pattern | Usage |
|---------|-------|
| New / Create | First-level action, creating new records |
| All / List | Complete collection view |
| By [Dimension] | Grouped/sliced views (By Status, By User, etc.) |
| Active / Open | Currently active operational items |
| Draft / Pending | Items in preliminary or awaiting states |
| Approved / Confirmed | Items that have been approved |
| Completed / Closed | Finished items |
| Cancelled / Rejected | Discarded items |
| In Progress | Items being processed |
| History / Archive | Historical or archived records |
| Reports / Analytics | Reporting-related views |
| Settings / Configuration | Configuration and settings |
| Audit / Logs | Audit trails and logs |

### Icon Standards (FontAwesome)

| Category | Icon Prefix |
|----------|-------------|
| Dashboards | fa-th-large |
| Master Data | fa-database, fa-boxes, fa-file-alt |
| Transactions | fa-shopping-cart, fa-file-invoice |
| Reports | fa-chart-bar, fa-chart-line, fa-chart-pie |
| Settings | fa-cog, fa-sliders-h |
| Alerts/Warnings | fa-exclamation-circle, fa-bell |
| History/Audit | fa-history, fa-clipboard-list |
| Users | fa-users, fa-user-check |
| Approvals | fa-check-circle, fa-file-signature |

---

## Implementation Notes

1. **Scalability**: Each module can expand its Level-3 children without affecting other modules
2. **Consistency**: Same patterns applied across all modules ensures user familiarity
3. **Business Logic**: Structure mirrors real business workflows and organizational structures
4. **Permission-Based**: Each Level-3 item supports granular permission control
5. **Internationalization**: All labels support Arabic (ar) and Farsi (fa) translations
6. **Future-Proof**: Structure allows adding new modules or Level-3 items without redesign
