# Organizational Planning & BPM - Sample Data Guide

This document describes the sample data created for the Organizational Planning & BPM module.

## Running the Sample Data Seeder

To populate the database with sample data, run:

```bash
python seed_org_planning.py
```

This script will:
1. Run all migrations to ensure tables exist
2. Create demo companies, org units, positions
3. Create sample workflow definitions
4. Create sample SLA policies
5. Create sample automation rules
6. Create sample process instances

## Sample Data Overview

### Companies
| Company Name | Code | Type | Country |
|-------------|------|------|---------|
| GlobalTech Industries | GTI001 | corporation | USA |
| Asia Pacific Holdings | APH001 | holding | Singapore |
| EuroTech GmbH | ETG001 | subsidiary | Germany |
| MENA Operations | MOP001 | subsidiary | UAE |

### Organizational Units
| Unit Name | Type | Level | Company |
|-----------|------|-------|---------|
| Executive Division | division | L1 | GlobalTech Industries |
| Technology Group | business_unit | L2 | GlobalTech Industries |
| Finance & Accounting | department | L3 | GlobalTech Industries |
| Human Resources | department | L3 | GlobalTech Industries |
| Sales & Marketing | department | L3 | GlobalTech Industries |
| Engineering | department | L3 | GlobalTech Industries |
| Product Development | section | L4 | GlobalTech Industries |
| Quality Assurance | section | L4 | GlobalTech Industries |
| Customer Support | section | L4 | GlobalTech Industries |
| IT Infrastructure | department | L3 | GlobalTech Industries |
| Operations | division | L1 | GlobalTech Industries |
| Logistics | department | L3 | GlobalTech Industries |
| Warehouse Management | section | L4 | GlobalTech Industries |

### Positions
| Position Title | Code | Level | Unit |
|---------------|------|-------|------|
| Chief Executive Officer | CEO001 | C-Level | Executive Division |
| Chief Financial Officer | CFO001 | C-Level | Finance & Accounting |
| Chief Technology Officer | CTO001 | C-Level | Technology Group |
| VP of Engineering | VPE001 | VP | Engineering |
| Director of HR | DHR001 | Director | Human Resources |
| Sales Director | DSR001 | Director | Sales & Marketing |
| Finance Manager | FNM001 | Manager | Finance & Accounting |
| HR Manager | HRM001 | Manager | Human Resources |
| Engineering Manager | EGM001 | Manager | Engineering |
| Product Manager | PMG001 | Manager | Product Development |
| QA Manager | QAM001 | Manager | Quality Assurance |
| IT Manager | ITM001 | Manager | IT Infrastructure |
| Logistics Manager | LGM001 | Manager | Logistics |
| Senior Engineer | SENG01 | Senior | Engineering |
| Software Engineer | SWE001 | Mid | Engineering |
| Junior Engineer | JENG01 | Junior | Engineering |
| QA Engineer | QAE001 | Mid | Quality Assurance |
| HR Specialist | HRS001 | Mid | Human Resources |
| Account Manager | ACM001 | Mid | Sales & Marketing |
| Sales Representative | SREP01 | Junior | Sales & Marketing |

### Workflow Definitions
| Workflow Name | Category | Steps | Status |
|--------------|----------|-------|--------|
| Purchase Request | procurement | 4 | published |
| Leave Approval | hr | 3 | published |
| Expense Report | finance | 3 | published |
| New Hire Onboarding | hr | 5 | published |
| Document Approval | general | 3 | draft |
| IT Service Request | it | 4 | published |
| Customer Complaint | customer | 4 | published |

### SLA Policies
| Policy Name | Priority | Response (hrs) | Resolution (hrs) |
|-------------|----------|----------------|------------------|
| Critical Issues | critical | 1 | 4 |
| High Priority | high | 4 | 24 |
| Medium Priority | medium | 8 | 48 |
| Low Priority | low | 24 | 120 |

### Automation Rules
| Rule Name | Trigger | Action | Status |
|----------|---------|--------|--------|
| Auto-assign IT Requests | on_create | assign_to_group | active |
| Remind Overdue Tasks | scheduled | send_notification | active |
| Escalate Critical SLA | on_breach | escalate | active |

### Process Instances (Sample)
| Process Title | Workflow | Status | Assignee |
|--------------|----------|--------|----------|
| Q1 Budget Review | Expense Report | in_progress | CFO001 |
| New Marketing Campaign | Purchase Request | completed | DSR001 |
| Office Supplies Request | Purchase Request | in_progress | HRM001 |
| Annual Leave - John | Leave Approval | approved | SREP01 |
| Server Upgrade | IT Service Request | in_progress | ITM001 |

## Creating Additional Sample Data

### Via the UI
1. Navigate to the relevant module (e.g., `/org-planning/companies`)
2. Click "Create" button
3. Fill in the form
4. Submit

### Via Database
You can insert data directly into the SQLite database:

```sql
-- Create a new company
INSERT INTO op_companies (name, code, country, is_active)
VALUES ('New Company', 'NC001', 'USA', 1);

-- Create org unit
INSERT INTO op_org_units (company_id, unit_type, name, code, is_active)
VALUES (1, 'department', 'New Department', 'ND001', 1);

-- Create position
INSERT INTO op_positions (org_unit_id, title, position_code, level, is_active)
VALUES (1, 'New Position', 'NP001', 'mid', 1);
```

## Resetting Sample Data

To reset all sample data and start fresh:

1. Backup your database
2. Delete the database file or specific tables
3. Restart the application (migrations will recreate tables)
4. Run `python seed_org_planning.py`

## Sample Data for Different Scenarios

### Test RTL Languages
Switch the website language to Arabic or Persian to test RTL rendering of:
- Organizational structure tree
- Form labels and inputs
- Navigation menus
- Status badges and buttons

### Test Permission Scenarios
Create users with different roles to test:
- `org_admin`: Full access to all org planning features
- `department_manager`: Access to own department's units and positions
- `approver`: Can approve/reject but cannot edit structures
- `viewer`: Read-only access to reports and dashboards

### Test Workflow Scenarios
1. Create a new workflow definition
2. Start a process instance
3. Approve/reject at each step
4. Verify SLA timers
5. Check escalation triggers
