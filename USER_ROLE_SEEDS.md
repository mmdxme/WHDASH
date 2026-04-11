# MMDx User Role Seeds
## Demo Users for All Roles

This document lists all demo/test users to be created for testing the multi-layer role and permission system.

---

## Naming Convention

```
username: {module}.{role_level}
password: Default: Welcome123!
example: warehouse.manager / Welcome123!
```

---

## Global / Cross-System Users

| Username | Display Name | Email | Role | Company | Active |
|----------|--------------|-------|------|---------|--------|
| `super.admin` | Super Administrator | super@warehouse.local | Super Admin | System | Yes |
| `global.admin` | Global Administrator | admin@warehouse.local | Global Admin | System | Yes |
| `executive.viewer` | Executive Viewer | exec@warehouse.local | Executive Viewer | Main Company | Yes |
| `auditor.internal` | Internal Auditor | auditor@warehouse.local | Internal Auditor | Main Company | Yes |
| `compliance.viewer` | Compliance Reviewer | compliance@warehouse.local | Compliance Reviewer | Main Company | Yes |

---

## Warehouse / WMS Users

| Username | Display Name | Email | Role | Warehouse | Active |
|----------|--------------|-------|------|-----------|--------|
| `warehouse.manager` | Warehouse Manager | warehouse.mgr@warehouse.local | Warehouse Manager | Main Warehouse | Yes |
| `warehouse.supervisor` | Warehouse Supervisor | warehouse.sv@warehouse.local | Warehouse Supervisor | Main Warehouse | Yes |
| `warehouse.assistant` | Warehouse Assistant | warehouse.asst@warehouse.local | Warehouse Assistant | Main Warehouse | Yes |
| `warehouse.operator` | Warehouse Operator | warehouse.op@warehouse.local | Warehouse Operator | Main Warehouse | Yes |
| `warehouse.operator2` | Warehouse Operator 2 | warehouse.op2@warehouse.local | Warehouse Operator | Secondary Warehouse | Yes |
| `warehouse.viewer` | Warehouse Viewer | warehouse.view@warehouse.local | Warehouse Viewer | Main Warehouse | Yes |

---

## Logistics / Delivery Users

| Username | Display Name | Email | Role | Region | Active |
|----------|--------------|-------|------|--------|--------|
| `logistics.manager` | Logistics Manager | logistics.mgr@warehouse.local | Logistics Manager | Dubai | Yes |
| `logistics.supervisor` | Logistics Supervisor | logistics.sv@warehouse.local | Logistics Supervisor | Dubai | Yes |
| `logistics.assistant` | Logistics Assistant | logistics.asst@warehouse.local | Logistics Assistant | Dubai | Yes |
| `logistics.coordinator` | Logistics Coordinator | logistics.coord@warehouse.local | Logistics Coordinator | Dubai | Yes |
| `logistics.driver` | Logistics Driver | logistics.driver@warehouse.local | Logistics Driver | Dubai | Yes |
| `logistics.driver2` | Logistics Driver 2 | logistics.driver2@warehouse.local | Logistics Driver | Abu Dhabi | Yes |
| `logistics.viewer` | Logistics Viewer | logistics.view@warehouse.local | Logistics Viewer | Dubai | Yes |

---

## Procurement / Purchasing Users

| Username | Display Name | Email | Role | Company | Active |
|----------|--------------|-------|------|---------|--------|
| `procurement.manager` | Procurement Manager | procurement.mgr@warehouse.local | Procurement Manager | Main Company | Yes |
| `procurement.supervisor` | Procurement Supervisor | procurement.sv@warehouse.local | Procurement Supervisor | Main Company | Yes |
| `procurement.assistant` | Procurement Assistant | procurement.asst@warehouse.local | Procurement Assistant | Main Company | Yes |
| `procurement.buyer` | Procurement Buyer | procurement.buyer@warehouse.local | Procurement Buyer | Main Company | Yes |
| `procurement.buyer2` | Procurement Buyer 2 | procurement.buyer2@warehouse.local | Procurement Buyer | Main Company | Yes |
| `procurement.viewer` | Procurement Viewer | procurement.view@warehouse.local | Procurement Viewer | Main Company | Yes |

---

## Finance / Accounting Users

| Username | Display Name | Email | Role | Company | Active |
|----------|--------------|-------|------|---------|--------|
| `finance.manager` | Finance Manager | finance.mgr@warehouse.local | Finance Manager | Main Company | Yes |
| `finance.supervisor` | Finance Supervisor | finance.sv@warehouse.local | Finance Supervisor | Main Company | Yes |
| `finance.assistant` | Finance Assistant | finance.asst@warehouse.local | Finance Assistant | Main Company | Yes |
| `finance.accountant` | Finance Accountant | finance.acct@warehouse.local | Finance Accountant | Main Company | Yes |
| `finance.ap.clerk` | Finance AP Clerk | finance.ap@warehouse.local | Finance AP Clerk | Main Company | Yes |
| `finance.ar.clerk` | Finance AR Clerk | finance.ar@warehouse.local | Finance AR Clerk | Main Company | Yes |
| `finance.viewer` | Finance Viewer | finance.view@warehouse.local | Finance Viewer | Main Company | Yes |
| `finance.auditor` | Finance Auditor | finance.auditor@warehouse.local | Finance Auditor | Main Company | Yes |

---

## HR / Human Resources Users

| Username | Display Name | Email | Role | Company | Department | Active |
|----------|--------------|-------|------|---------|------------|--------|
| `hr.manager` | HR Manager | hr.mgr@warehouse.local | HR Manager | Main Company | HR | Yes |
| `hr.supervisor` | HR Supervisor | hr.sv@warehouse.local | HR Supervisor | Main Company | HR | Yes |
| `hr.assistant` | HR Assistant | hr.asst@warehouse.local | HR Assistant | Main Company | HR | Yes |
| `hr.officer` | HR Officer | hr.officer@warehouse.local | HR Officer | Main Company | HR | Yes |
| `payroll.manager` | Payroll Manager | payroll.mgr@warehouse.local | Payroll Manager | Main Company | HR | Yes |
| `payroll.officer` | Payroll Officer | payroll.officer@warehouse.local | Payroll Officer | Main Company | HR | Yes |
| `hr.viewer` | HR Viewer | hr.view@warehouse.local | HR Viewer | Main Company | HR | Yes |
| `employee.demo` | Demo Employee | employee@warehouse.local | Employee Self-Service | Main Company | Sales | Yes |

---

## Asset Management Users

| Username | Display Name | Email | Role | Company | Active |
|----------|--------------|-------|------|---------|--------|
| `asset.manager` | Asset Manager | asset.mgr@warehouse.local | Asset Manager | Main Company | Yes |
| `asset.supervisor` | Asset Supervisor | asset.sv@warehouse.local | Asset Supervisor | Main Company | Yes |
| `asset.accountant` | Asset Accountant | asset.acct@warehouse.local | Asset Accountant | Main Company | Yes |
| `asset.assistant` | Asset Assistant | asset.asst@warehouse.local | Asset Assistant | Main Company | Yes |
| `asset.operator` | Asset Operator | asset.op@warehouse.local | Asset Operator | Main Company | Yes |
| `asset.viewer` | Asset Viewer | asset.view@warehouse.local | Asset Viewer | Main Company | Yes |

---

## Maintenance Management Users

| Username | Display Name | Email | Role | Facility | Active |
|----------|--------------|-------|------|----------|--------|
| `maintenance.manager` | Maintenance Manager | maint.mgr@warehouse.local | Maintenance Manager | Main Facility | Yes |
| `maintenance.supervisor` | Maintenance Supervisor | maint.sv@warehouse.local | Maintenance Supervisor | Main Facility | Yes |
| `maintenance.technician` | Maintenance Technician | maint.tech@warehouse.local | Maintenance Technician | Main Facility | Yes |
| `maintenance.technician2` | Maintenance Technician 2 | maint.tech2@warehouse.local | Maintenance Technician | Secondary Facility | Yes |
| `maintenance.planner` | Maintenance Planner | maint.planner@warehouse.local | Maintenance Planner | Main Facility | Yes |
| `maintenance.viewer` | Maintenance Viewer | maint.view@warehouse.local | Maintenance Viewer | Main Facility | Yes |

---

## Quality Management Users

| Username | Display Name | Email | Role | Company | Active |
|----------|--------------|-------|------|---------|--------|
| `quality.manager` | Quality Manager | quality.mgr@warehouse.local | Quality Manager | Main Company | Yes |
| `quality.supervisor` | Quality Supervisor | quality.sv@warehouse.local | Quality Supervisor | Main Company | Yes |
| `quality.inspector` | Quality Inspector | quality.insp@warehouse.local | Quality Inspector | Main Company | Yes |
| `quality.inspector2` | Quality Inspector 2 | quality.insp2@warehouse.local | Quality Inspector | Main Company | Yes |
| `quality.auditor` | Quality Auditor | quality.auditor@warehouse.local | Quality Auditor | Main Company | Yes |
| `quality.assistant` | Quality Assistant | quality.asst@warehouse.local | Quality Assistant | Main Company | Yes |
| `quality.viewer` | Quality Viewer | quality.view@warehouse.local | Quality Viewer | Main Company | Yes |

---

## Sales / CRM Users

| Username | Display Name | Email | Role | Company | Active |
|----------|--------------|-------|------|---------|--------|
| `sales.manager` | Sales Manager | sales.mgr@warehouse.local | Sales Manager | Main Company | Yes |
| `sales.supervisor` | Sales Supervisor | sales.sv@warehouse.local | Sales Supervisor | Main Company | Yes |
| `sales.assistant` | Sales Assistant | sales.asst@warehouse.local | Sales Assistant | Main Company | Yes |
| `sales.executive` | Sales Executive | sales.exec@warehouse.local | Sales Executive | Main Company | Yes |
| `sales.executive2` | Sales Executive 2 | sales.exec2@warehouse.local | Sales Executive | Main Company | Yes |
| `crm.manager` | CRM Manager | crm.mgr@warehouse.local | CRM Manager | Main Company | Yes |
| `crm.specialist` | CRM Specialist | crm.spec@warehouse.local | CRM Specialist | Main Company | Yes |
| `sales.viewer` | Sales Viewer | sales.view@warehouse.local | Sales Viewer | Main Company | Yes |

---

## Marketing Users

| Username | Display Name | Email | Role | Company | Active |
|----------|--------------|-------|------|---------|--------|
| `marketing.manager` | Marketing Manager | marketing.mgr@warehouse.local | Marketing Manager | Main Company | Yes |
| `marketing.supervisor` | Marketing Supervisor | marketing.sv@warehouse.local | Marketing Supervisor | Main Company | Yes |
| `marketing.assistant` | Marketing Assistant | marketing.asst@warehouse.local | Marketing Assistant | Main Company | Yes |
| `marketing.specialist` | Marketing Specialist | marketing.spec@warehouse.local | Marketing Specialist | Main Company | Yes |
| `content.manager` | Content Manager | content.mgr@warehouse.local | Content Manager | Main Company | Yes |
| `marketing.viewer` | Marketing Viewer | marketing.view@warehouse.local | Marketing Viewer | Main Company | Yes |

---

## Planning / Demand Planning Users

| Username | Display Name | Email | Role | Company | Active |
|----------|--------------|-------|------|---------|--------|
| `planning.manager` | Planning Manager | planning.mgr@warehouse.local | Planning Manager | Main Company | Yes |
| `planning.analyst` | Planning Analyst | planning.analyst@warehouse.local | Planning Analyst | Main Company | Yes |
| `planning.assistant` | Planning Assistant | planning.asst@warehouse.local | Planning Assistant | Main Company | Yes |
| `planning.viewer` | Planning Viewer | planning.view@warehouse.local | Planning Viewer | Main Company | Yes |

---

## Workflow / BPM Users

| Username | Display Name | Email | Role | Company | Active |
|----------|--------------|-------|------|---------|--------|
| `workflow.admin` | Workflow Administrator | workflow.admin@warehouse.local | Workflow Admin | Main Company | Yes |
| `workflow.supervisor` | Workflow Supervisor | workflow.sv@warehouse.local | Workflow Supervisor | Main Company | Yes |
| `workflow.user` | Workflow User | workflow.user@warehouse.local | Workflow User | Main Company | Yes |
| `workflow.viewer` | Workflow Viewer | workflow.view@warehouse.local | Workflow Viewer | Main Company | Yes |

---

## Documents / DMS Users

| Username | Display Name | Email | Role | Company | Active |
|----------|--------------|-------|------|---------|--------|
| `documents.manager` | Documents Manager | docs.mgr@warehouse.local | Documents Manager | Main Company | Yes |
| `documents.controller` | Documents Controller | docs.ctrl@warehouse.local | Documents Controller | Main Company | Yes |
| `documents.assistant` | Documents Assistant | docs.asst@warehouse.local | Documents Assistant | Main Company | Yes |
| `documents.user` | Documents User | docs.user@warehouse.local | Documents User | Main Company | Yes |
| `documents.viewer` | Documents Viewer | docs.view@warehouse.local | Documents Viewer | Main Company | Yes |

---

## E-commerce Users

| Username | Display Name | Email | Role | Company | Active |
|----------|--------------|-------|------|---------|--------|
| `ecommerce.manager` | E-commerce Manager | ecommerce.mgr@warehouse.local | E-commerce Manager | Main Company | Yes |
| `ecommerce.coordinator` | E-commerce Coordinator | ecommerce.coord@warehouse.local | E-commerce Coordinator | Main Company | Yes |
| `ecommerce.assistant` | E-commerce Assistant | ecommerce.asst@warehouse.local | E-commerce Assistant | Main Company | Yes |
| `ecommerce.viewer` | E-commerce Viewer | ecommerce.view@warehouse.local | E-commerce Viewer | Main Company | Yes |

---

## API Gateway Users

| Username | Display Name | Email | Role | Active |
|----------|--------------|-------|------|--------|
| `api.admin` | API Gateway Admin | api.admin@warehouse.local | API Gateway Admin | Yes |
| `api.manager` | API Manager | api.mgr@warehouse.local | API Manager | Yes |
| `api.support` | API Support User | api.support@warehouse.local | API Support User | Yes |
| `api.viewer` | API Viewer | api.view@warehouse.local | API Viewer | Yes |

---

## BI / Reports Users

| Username | Display Name | Email | Role | Company | Active |
|----------|--------------|-------|------|---------|--------|
| `bi.manager` | BI Manager | bi.mgr@warehouse.local | BI Manager | Main Company | Yes |
| `bi.analyst` | BI Analyst | bi.analyst@warehouse.local | BI Analyst | Main Company | Yes |
| `bi.viewer` | BI Viewer | bi.view@warehouse.local | BI Viewer | Main Company | Yes |
| `bi.steward` | BI Data Steward | bi.steward@warehouse.local | BI Data Steward | Main Company | Yes |

---

## Social Media Users

| Username | Display Name | Email | Role | Company | Active |
|----------|--------------|-------|------|---------|--------|
| `social.manager` | Social Media Manager | social.mgr@warehouse.local | Social Media Manager | Main Company | Yes |
| `social.specialist` | Social Media Specialist | social.spec@warehouse.local | Social Media Specialist | Main Company | Yes |
| `social.viewer` | Social Media Viewer | social.view@warehouse.local | Social Media Viewer | Main Company | Yes |

---

## Admin / Platform Users

| Username | Display Name | Email | Role | Active |
|----------|--------------|-------|------|--------|
| `platform.admin` | Platform Administrator | platform.admin@warehouse.local | Platform Admin | Yes |
| `user.admin` | User & Role Administrator | user.admin@warehouse.local | User & Role Admin | Yes |
| `audit.viewer` | Audit Viewer | audit.view@warehouse.local | Audit Viewer | Yes |

---

## User Creation SQL Template

```sql
-- Create user
INSERT INTO users (username, email, password_hash, full_name, role_id, company_id, department, job_title, is_active, created_at, updated_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- Assign company access (if applicable)
INSERT INTO user_company_access (user_id, company_id, access_level)
VALUES (?, ?, 'read');

-- Assign warehouse access (if applicable)
INSERT INTO user_warehouse_access (user_id, warehouse_id, access_level)
VALUES (?, ?, 'read');
```

---

## Default Password Policy

All demo users use the default password: `Welcome123!`

This password should be changed after first login in production environments.

---

## Demo User Quick Reference

| Category | Usernames |
|----------|-----------|
| **Admins** | `super.admin`, `global.admin`, `platform.admin`, `user.admin` |
| **Warehouse** | `warehouse.manager`, `warehouse.supervisor`, `warehouse.assistant`, `warehouse.operator` |
| **Logistics** | `logistics.manager`, `logistics.supervisor`, `logistics.coordinator`, `logistics.driver` |
| **Finance** | `finance.manager`, `finance.supervisor`, `finance.accountant`, `finance.ap.clerk`, `finance.ar.clerk` |
| **HR** | `hr.manager`, `hr.supervisor`, `hr.officer`, `payroll.manager`, `employee.demo` |
| **Sales** | `sales.manager`, `sales.supervisor`, `sales.executive`, `crm.manager` |
| **Procurement** | `procurement.manager`, `procurement.supervisor`, `procurement.buyer` |
| **Quality** | `quality.manager`, `quality.inspector`, `quality.auditor` |
| **Maintenance** | `maintenance.manager`, `maintenance.technician`, `maintenance.planner` |
| **Assets** | `asset.manager`, `asset.accountant`, `asset.operator` |
| **Marketing** | `marketing.manager`, `marketing.specialist`, `content.manager` |
| **BI/Reports** | `bi.manager`, `bi.analyst`, `bi.viewer` |
| **Executive** | `executive.viewer`, `auditor.internal`, `compliance.viewer` |
