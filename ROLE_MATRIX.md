# MMDx Role Matrix
## Enterprise Multi-Layer Role-Based Access Control

---

## 1. GLOBAL / CROSS-SYSTEM ROLES

| Role | Code | Description | Scope |
|------|------|-------------|-------|
| **Super Admin** | `super_admin` | Full system control, all modules, all companies. Cannot be edited/deleted. | Global |
| **Global Admin** | `global_admin` | Platform administration, user/role management, settings | Global |
| **Executive / CEO View** | `executive_viewer` | Read-only dashboards, executive summaries, reports | Global |
| **Internal Auditor** | `internal_auditor` | Read-only access to audit logs, compliance reports, financial summaries | Global |
| **Compliance Reviewer** | `compliance_reviewer` | Read-only access to audit logs, NCR, CAPA, quality records | Global |

---

## 2. WAREHOUSE / WMS ROLES

| Role | Code | Description | Scope |
|------|------|-------------|-------|
| **Warehouse Manager** | `warehouse_manager` | Full warehouse visibility, approve transfers/adjustments, export reports, manage team | Own Business Unit |
| **Warehouse Supervisor** | `warehouse_supervisor` | Manage daily operations, assign tasks, validate counts, confirm receipts/shipments | Own Warehouse |
| **Warehouse Assistant** | `warehouse_assistant` | Prepare documents, update statuses, support transactions, upload attachments | Own Warehouse |
| **Warehouse Operator** | `warehouse_operator` | Receive, pick, pack, move, count, update assigned operational records | Assigned Location |
| **Warehouse Viewer** | `warehouse_viewer` | Read-only access to inventory, reports and logs | Own Warehouse |

---

## 3. LOGISTICS / DELIVERY ROLES

| Role | Code | Description | Scope |
|------|------|-------------|-------|
| **Logistics Manager** | `logistics_manager` | Full logistics visibility, approve shipments, driver management, reports | Own Business Unit |
| **Logistics Supervisor** | `logistics_supervisor` | Dispatch operations, trip management, route optimization, driver coordination | Own Region |
| **Logistics Assistant** | `logistics_assistant` | Prepare shipment documents, update follow-ups, documentation support | Own Region |
| **Logistics Coordinator** | `logistics_coordinator` | Coordinate deliveries, track shipments, handle exceptions | Assigned Routes |
| **Logistics Driver** | `logistics_driver` | View assigned trips, update delivery status, check-in at stops | Assigned Vehicle |
| **Logistics Viewer** | `logistics_viewer` | Read-only access to trips, routes, delivery reports | Own Region |

---

## 4. PROCUREMENT / PURCHASING ROLES

| Role | Code | Description | Scope |
|------|------|-------------|-------|
| **Procurement Manager** | `procurement_manager` | Approve PR/RFQ/PO, supplier performance, contracts, final approval | Global/Own Company |
| **Procurement Supervisor** | `procurement_supervisor` | Review drafts, assign buyers, monitor due dates, second-level approval | Own Company |
| **Procurement Assistant** | `procurement_assistant` | Prepare RFQ/PO drafts, upload quotations, update follow-ups | Own Company |
| **Procurement Buyer** | `procurement_buyer` | Create requisitions, request quotes, work assigned purchase orders | Own Company |
| **Procurement Viewer** | `procurement_viewer` | Read-only access to suppliers, contracts, procurement reports | Own Company |

---

## 5. FINANCE / ACCOUNTING ROLES

| Role | Code | Description | Scope |
|------|------|-------------|-------|
| **Finance Manager** | `finance_manager` | Broad visibility, approvals, posting, closing, financial reporting | Global/Own Company |
| **Finance Supervisor** | `finance_supervisor` | Review entries, supervise billing/payment workflow, reconcile | Own Company |
| **Finance Assistant** | `finance_assistant` | Prepare bills/invoices/receipts, reconciliation support, data entry | Own Company |
| **Finance Accountant** | `finance_accountant` | Daily operational accounting by assigned scope, journal entries | Own Company |
| **Finance AP Clerk** | `finance_ap_clerk` | Process payables, payments, vendor invoices | Own Company |
| **Finance AR Clerk** | `finance_ar_clerk` | Process receivables, receipts, customer invoices | Own Company |
| **Finance Viewer** | `finance_viewer` | Read-only financial review, reports, dashboards | Own Company |
| **Finance Auditor** | `finance_auditor` | Read-only access to journals, audit logs, financial records | Global |

---

## 6. HR / HUMAN RESOURCES ROLES

| Role | Code | Description | Scope |
|------|------|-------------|-------|
| **HR Manager** | `hr_manager` | Full HR visibility, employee management, leave/attendance approval, payroll final | Global/Own Company |
| **HR Supervisor** | `hr_supervisor` | Attendance/leave review, team administration, recruitment screening | Own Company |
| **HR Assistant** | `hr_assistant` | Employee document updates, onboarding support, leave processing, data entry | Own Company |
| **HR Officer** | `hr_officer` | Day-to-day HR operations, attendance management, leave tracking | Own Company |
| **Payroll Manager** | `payroll_manager` | Full payroll access, salary processing, tax calculations, disbursements | Own Company |
| **Payroll Officer** | `payroll_officer` | Prepare payroll, calculate overtime, benefits administration | Own Company |
| **HR Viewer** | `hr_viewer` | Read-only access to employee lists, leave balances, reports | Own Company |
| **Employee Self-Service** | `employee_self_service` | View own profile, submit leave requests, view own attendance | Self Only |

---

## 7. ASSET MANAGEMENT ROLES

| Role | Code | Description | Scope |
|------|------|-------------|-------|
| **Asset Manager** | `asset_manager` | Full asset visibility, acquisitions, disposals, depreciation, team oversight | Global/Own Company |
| **Asset Supervisor** | `asset_supervisor` | Asset maintenance tracking, depreciation run review, transfers approval | Own Company |
| **Asset Accountant** | `asset_accountant` | Depreciation calculations, asset valuations, financial reporting | Own Company |
| **Asset Assistant** | `asset_assistant` | Prepare acquisition documents, update asset records, maintenance logs | Own Company |
| **Asset Operator** | `asset_operator` | Record asset usage, submit maintenance requests, physical counts | Own Company |
| **Asset Viewer** | `asset_viewer` | Read-only access to asset register, depreciation schedules | Own Company |

---

## 8. MAINTENANCE MANAGEMENT ROLES

| Role | Code | Description | Scope |
|------|------|-------------|-------|
| **Maintenance Manager** | `maintenance_manager` | Full maintenance visibility, approve work orders, PM schedules, costs | Global/Own Company |
| **Maintenance Supervisor** | `maintenance_supervisor` | Manage technicians, assign work orders, review completion | Own Facility |
| **Maintenance Technician** | `maintenance_technician` | Execute work orders, update task completion, log parts usage | Assigned Facility |
| **Maintenance Planner** | `maintenance_planner` | Schedule PM plans, create work orders, parts planning | Own Facility |
| **Maintenance Viewer** | `maintenance_viewer` | Read-only access to work orders, equipment, maintenance reports | Own Facility |

---

## 9. QUALITY MANAGEMENT ROLES

| Role | Code | Description | Scope |
|------|------|-------------|-------|
| **Quality Manager** | `quality_manager` | Full quality visibility, NCR/CAPA approval, audit scheduling, reports | Global/Own Company |
| **Quality Supervisor** | `quality_supervisor` | Inspections oversight, NCR review, CAPA tracking | Own Company |
| **Quality Inspector** | `quality_inspector` | Execute inspections, create NCRs, verify quality standards | Assigned Area |
| **Quality Auditor** | `quality_auditor` | Conduct audits, document findings, track CAPA effectiveness | Own Company |
| **Quality Assistant** | `quality_assistant` | Prepare inspection documents, update records, support audits | Own Company |
| **Quality Viewer** | `quality_viewer` | Read-only access to inspections, NCR, CAPA, audit logs | Own Company |

---

## 10. SALES & CRM ROLES

| Role | Code | Description | Scope |
|------|------|-------------|-------|
| **Sales Manager** | `sales_manager` | Sales dashboards, customer approvals, quotation oversight, team management | Global/Own Company |
| **Sales Supervisor** | `sales_supervisor` | Team pipeline supervision, quotation review, order follow-up | Own Company |
| **Sales Assistant** | `sales_assistant` | Data entry, quote preparation, documentation, follow-up | Own Company |
| **Sales Executive** | `sales_executive` | Customer operations, quotations, orders within scope | Own Company |
| **CRM Manager** | `crm_manager` | Customer data, segments, customer intelligence oversight | Global/Own Company |
| **CRM Specialist** | `crm_specialist` | Customer profiling, segmentation, activity tracking | Own Company |
| **Sales Viewer** | `sales_viewer` | Read-only access to customers, quotations, orders, reports | Own Company |

---

## 11. MARKETING ROLES

| Role | Code | Description | Scope |
|------|------|-------------|-------|
| **Marketing Manager** | `marketing_manager` | Full marketing visibility, campaign approvals, budget control, team oversight | Global/Own Company |
| **Marketing Supervisor** | `marketing_supervisor` | Campaign coordination, lead management, content approval | Own Company |
| **Marketing Assistant** | `marketing_assistant` | Prepare campaign content, manage leads, social media posts | Own Company |
| **Marketing Specialist** | `marketing_specialist` | Execute campaigns, track leads, manage channels | Own Company |
| **Content Manager** | `content_manager` | Approve/publish content, manage templates, brand consistency | Own Company |
| **Marketing Viewer** | `marketing_viewer` | Read-only access to campaigns, leads, reports, analytics | Own Company |

---

## 12. PLANNING / DEMAND PLANNING ROLES

| Role | Code | Description | Scope |
|------|------|-------------|-------|
| **Planning Manager** | `planning_manager` | Full planning visibility, forecast approval, replenishment decisions | Global/Own Company |
| **Planning Analyst** | `planning_analyst` | Create forecasts, analyze demand, run replenishment scenarios | Own Company |
| **Planning Assistant** | `planning_assistant` | Prepare planning data, update parameters, support analysis | Own Company |
| **Planning Viewer** | `planning_viewer` | Read-only access to forecasts, demand plans, replenishment | Own Company |

---

## 13. WORKFLOW / BPM ROLES

| Role | Code | Description | Scope |
|------|------|-------------|-------|
| **Workflow Admin** | `workflow_admin` | Full workflow visibility, designer access, process modeling | Global |
| **Workflow Supervisor** | `workflow_supervisor` | Monitor instances, handle escalations, approve/reject | Own Company |
| **Workflow User** | `workflow_user` | Access assigned work items, complete tasks, submit for approval | Assigned |
| **Workflow Viewer** | `workflow_viewer` | Read-only access to workflow dashboard, monitoring | Own Company |

---

## 14. DOCUMENTS / DMS ROLES

| Role | Code | Description | Scope |
|------|------|-------------|-------|
| **Documents Manager** | `documents_manager` | Full document visibility, access control, retention policies | Global |
| **Documents Controller** | `documents_controller` | Manage document categories, templates, signature workflows | Own Company |
| **Documents Assistant** | `documents_assistant` | Upload documents, update versions, manage links | Own Company |
| **Documents User** | `documents_user` | View/upload own documents, request signatures | Assigned |
| **Documents Viewer** | `documents_viewer` | Read-only access to documents library | Own Company |

---

## 15. E-COMMERCE ROLES

| Role | Code | Description | Scope |
|------|------|-------------|-------|
| **E-commerce Manager** | `ecommerce_manager` | Full e-commerce visibility, channel management, order approvals | Global |
| **E-commerce Coordinator** | `ecommerce_coordinator` | Manage orders, sync inventory, handle exceptions | Own Company |
| **E-commerce Assistant** | `ecommerce_assistant` | Process orders, update status, customer communication | Own Company |
| **E-commerce Viewer** | `ecommerce_viewer` | Read-only access to orders, channels, reports | Own Company |

---

## 16. API GATEWAY ROLES

| Role | Code | Description | Scope |
|------|------|-------------|-------|
| **API Gateway Admin** | `api_gateway_admin` | Full API visibility, client management, rate limits, monitoring | Global |
| **API Manager** | `api_manager` | Manage API routes, versions, documentation | Global |
| **API Support User** | `api_support_user` | View logs, monitor health, manage webhooks | Global |
| **API Viewer** | `api_viewer` | Read-only access to API routes, logs, monitoring | Global |

---

## 17. BUSINESS INTELLIGENCE / REPORTS ROLES

| Role | Code | Description | Scope |
|------|------|-------------|-------|
| **BI Manager** | `bi_manager` | Full BI visibility, dataset management, scheduled reports | Global |
| **BI Analyst** | `bi_analyst` | Create reports, run adhoc queries, manage KPIs | Own Company |
| **BI Viewer** | `bi_viewer` | View dashboards, executive reports, standard reports | Own Company |
| **BI Data Steward** | `bi_data_steward` | Manage datasets, data quality, import/export | Global |

---

## 18. SOCIAL MEDIA ROLES

| Role | Code | Description | Scope |
|------|------|-------------|-------|
| **Social Media Manager** | `social_media_manager` | Full social media visibility, approve content, manage accounts | Global |
| **Social Media Specialist** | `social_media_specialist` | Create content, manage calendar, publish posts | Own Company |
| **Social Media Viewer** | `social_media_viewer` | Read-only access to content, engagement reports | Own Company |

---

## 19. ADMIN / PLATFORM SETTINGS ROLES

| Role | Code | Description | Scope |
|------|------|-------------|-------|
| **Platform Admin** | `platform_admin` | System settings, localization, numbering, notifications | Global |
| **User & Role Admin** | `user_role_admin` | Manage users, roles, permissions, access scopes | Global |
| **Audit Viewer** | `audit_viewer` | View audit logs, system logs | Global |

---

## 20. COMPANY / ORGANIZATION ROLES

| Role | Code | Description | Scope |
|------|------|-------------|-------|
| **Company Admin** | `company_admin` | Manage company, branches, departments | Own Company |
| **Branch Manager** | `branch_manager` | Full branch visibility, branch operations | Own Branch |
| **Department Manager** | `department_manager` | Department oversight, team management | Own Department |

---

## Role Hierarchy Summary

```
GLOBAL ROLES
├── Super Admin
├── Global Admin
├── Executive Viewer
├── Internal Auditor
└── Compliance Reviewer

MODULE-SPECIFIC ROLES (per module)
├── [Module] Manager        → Highest operational authority
├── [Module] Supervisor     → Team oversight, review
├── [Module] Assistant       → Administrative support
├── [Module] User/Operator   → Day-to-day operations
└── [Module] Viewer         → Read-only access
```

---

## Sensitive Data Access Restrictions

| Module | Sensitive Data | Restricted To |
|--------|---------------|---------------|
| Finance | Journal posting | Finance Manager, Finance Supervisor with posting rights |
| Finance | Salary/Payroll data | Payroll Manager, HR Manager with payroll rights |
| Finance | Audit logs | Finance Auditor, Internal Auditor, Compliance Reviewer |
| HR | Salary/Payroll | Payroll Manager, HR Manager (payroll authorized) |
| HR | Performance reviews | Employee's manager and HR Manager only |
| Admin | Role/Permission editing | User & Role Admin, Global Admin only |
| Admin | Audit logs | Audit Viewer, Internal Auditor, Compliance Reviewer |
| API | API credentials/tokens | API Gateway Admin, API Manager only |
| Documents | Classified documents | Explicit role-based access per classification |
