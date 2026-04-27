# Project Management Sample Data Guide

This guide provides sample data to populate the Project Management module with realistic test data for demonstration, training, and testing purposes.

---

## Portfolio Setup

### Portfolio 1: Strategic Projects Portfolio

```sql
-- Insert Strategic Projects Portfolio
INSERT INTO portfolios (portfolio_name, portfolio_code, description, portfolio_type, status, created_by_user_id, created_at)
VALUES ('Strategic Projects Portfolio', 'SPP', 'Long-term strategic initiatives that drive business transformation', 'Strategic', 'Active', 1, datetime('now'));
```

### Portfolio 2: Operations Portfolio

```sql
-- Insert Operations Portfolio
INSERT INTO portfolios (portfolio_name, portfolio_code, description, portfolio_type, status, created_by_user_id, created_at)
VALUES ('Operations Portfolio', 'OPS', 'Operational excellence and process improvement initiatives', 'Operational', 'Active', 1, datetime('now'));
```

---

## Program Setup

### Programs Under Strategic Projects

```sql
-- Program 1: Digital Transformation Program
INSERT INTO programs (program_name, program_code, portfolio_id, description, program_manager_id, status, start_date, end_date, created_by_user_id, created_at)
VALUES ('Digital Transformation Program', 'DTP', 1, 'Enterprise-wide digital transformation initiative', 2, 'Active', '2026-01-15', '2027-06-30', 1, datetime('now'));

-- Program 2: Innovation Initiative Program
INSERT INTO programs (program_name, program_code, portfolio_id, description, program_manager_id, status, start_date, end_date, created_by_user_id, created_at)
VALUES ('Innovation Initiative Program', 'IIP', 1, 'New product and service innovation initiatives', 2, 'Active', '2026-02-01', '2026-12-31', 1, datetime('now'));
```

### Program Under Operations

```sql
-- Program 3: Process Excellence Program
INSERT INTO programs (program_name, program_code, portfolio_id, description, program_manager_id, status, start_date, end_date, created_by_user_id, created_at)
VALUES ('Process Excellence Program', 'PEP', 2, 'Process improvement and efficiency programs', 3, 'Active', '2026-01-01', '2026-12-31', 1, datetime('now'));
```

---

## Project Setup

### Project 1: ERP Implementation

```sql
-- ERP Implementation Project
INSERT INTO projects (
    project_code, project_name, project_type_id, category_id, description,
    company_id, department_id, owner_user_id, manager_user_id, sponsor_user_id,
    planned_start_date, planned_end_date, actual_start_date, target_completion_date,
    priority, status, progress, baseline_start_date, baseline_end_date,
    cost_center, budget_code, created_by_user_id, created_at
) VALUES (
    'PRJ00001', 'ERP Implementation', 2, 1,
    'Enterprise Resource Planning system implementation covering finance, HR, supply chain, and operations modules. This multi-year initiative will modernize core business systems and replace legacy applications.',
    1, 1, 1, 2, 4,
    '2026-01-15', '2027-03-31', '2026-01-15', '2027-03-31',
    'Critical', 'Active', 25, '2026-01-15', '2027-03-31',
    'CC-FIN-001', 'BUD-ERP-2026', 1, datetime('now')
);
```

### Project 2: Mobile App Development

```sql
-- Mobile App Development Project
INSERT INTO projects (
    project_code, project_name, project_type_id, category_id, description,
    company_id, department_id, owner_user_id, manager_user_id, sponsor_user_id,
    planned_start_date, planned_end_date, actual_start_date, target_completion_date,
    priority, status, progress, baseline_start_date, baseline_end_date,
    cost_center, budget_code, created_by_user_id, created_at
) VALUES (
    'PRJ00002', 'Mobile App Development', 2, 1,
    'Native mobile application development for iOS and Android platforms. The app will provide customer self-service capabilities and improve engagement through push notifications and personalized content.',
    1, 2, 1, 3, 4,
    '2026-02-01', '2026-09-30', '2026-02-01', '2026-09-30',
    'High', 'Active', 45, '2026-02-01', '2026-09-30',
    'CC-IT-002', 'BUD-MOB-2026', 1, datetime('now')
);
```

### Project 3: Facility Renovation

```sql
-- Facility Renovation Project
INSERT INTO projects (
    project_code, project_name, project_type_id, category_id, description,
    company_id, department_id, owner_user_id, manager_user_id, sponsor_user_id,
    planned_start_date, planned_end_date, actual_start_date, target_completion_date,
    priority, status, progress, baseline_start_date, baseline_end_date,
    cost_center, budget_code, created_by_user_id, created_at
) VALUES (
    'PRJ00003', 'Headquarters Facility Renovation', 1, 1,
    'Complete renovation of headquarters building including new HVAC systems, LED lighting, space reconfiguration, and accessibility upgrades. Project includes 3 floors totaling 50,000 square feet.',
    1, 3, 1, 5, 4,
    '2026-03-01', '2026-11-30', '2026-03-01', '2026-11-30',
    'High', 'Active', 15, '2026-03-01', '2026-11-30',
    'CC-FAC-001', 'BUD-FAC-2026', 1, datetime('now')
);
```

### Project 4: Customer Portal

```sql
-- Customer Portal Project
INSERT INTO projects (
    project_code, project_name, project_type_id, category_id, description,
    company_id, department_id, owner_user_id, manager_user_id, sponsor_user_id,
    planned_start_date, planned_end_date, actual_start_date, target_completion_date,
    priority, status, progress, baseline_start_date, baseline_end_date,
    cost_center, budget_code, created_by_user_id, created_at
) VALUES (
    'PRJ00004', 'Customer Self-Service Portal', 2, 1,
    'Web-based customer portal enabling 24/7 self-service access to account information, order tracking, invoice payment, and support ticket management. Targets 10,000 registered customers.',
    1, 2, 1, 3, 4,
    '2026-01-20', '2026-08-15', '2026-01-20', '2026-08-15',
    'High', 'Active', 60, '2026-01-20', '2026-08-15',
    'CC-IT-003', 'BUD-CSP-2026', 1, datetime('now')
);
```

### Project 5: Data Warehouse

```sql
-- Data Warehouse Project
INSERT INTO projects (
    project_code, project_name, project_type_id, category_id, description,
    company_id, department_id, owner_user_id, manager_user_id, sponsor_user_id,
    planned_start_date, planned_end_date, actual_start_date, target_completion_date,
    priority, status, progress, baseline_start_date, baseline_end_date,
    cost_center, budget_code, created_by_user_id, created_at
) VALUES (
    'PRJ00005', 'Enterprise Data Warehouse', 2, 1,
    'Centralized data warehouse consolidating data from ERP, CRM, and operational systems. Includes data modeling, ETL pipelines, and executive dashboards for business intelligence.',
    1, 2, 1, 6, 4,
    '2026-04-01', '2027-01-31', '2026-04-01', '2027-01-31',
    'Critical', 'Active', 10, '2026-04-01', '2027-01-31',
    'CC-IT-004', 'BUD-DWH-2026', 1, datetime('now')
);
```

### Project 6: Process Automation

```sql
-- Process Automation Project
INSERT INTO projects (
    project_code, project_name, project_type_id, category_id, description,
    company_id, department_id, owner_user_id, manager_user_id, sponsor_user_id,
    planned_start_date, planned_end_date, actual_start_date, target_completion_date,
    priority, status, progress, baseline_start_date, baseline_end_date,
    cost_center, budget_code, created_by_user_id, created_at
) VALUES (
    'PRJ00006', 'Finance Process Automation', 5, 2,
    'Robotic Process Automation (RPA) implementation for finance department including invoice processing, reconciliation, and reporting automation. Expected to reduce manual effort by 60%.',
    1, 1, 1, 7, 4,
    '2026-02-15', '2026-10-31', '2026-02-15', '2026-10-31',
    'Medium', 'Active', 35, '2026-02-15', '2026-10-31',
    'CC-FIN-002', 'BUD-FPA-2026', 1, datetime('now')
);
```

---

## WBS Structure for ERP Implementation

```sql
-- WBS Level 1 - Project
INSERT INTO project_wbs (project_id, wbs_code, wbs_name, level, sort_order) VALUES (1, '1', 'ERP Implementation', 1, 1);

-- WBS Level 2 - Phases
INSERT INTO project_wbs (project_id, parent_wbs_id, wbs_code, wbs_name, level, sort_order)
VALUES (1, 1, '1.1', 'Project Initiation', 2, 1);

INSERT INTO project_wbs (project_id, parent_wbs_id, wbs_code, wbs_name, level, sort_order)
VALUES (1, 1, '1.2', 'Requirements Gathering', 2, 2);

INSERT INTO project_wbs (project_id, parent_wbs_id, wbs_code, wbs_name, level, sort_order)
VALUES (1, 1, '1.3', 'Solution Design', 2, 3);

INSERT INTO project_wbs (project_id, parent_wbs_id, wbs_code, wbs_name, level, sort_order)
VALUES (1, 1, '1.4', 'Build & Configuration', 2, 4);

INSERT INTO project_wbs (project_id, parent_wbs_id, wbs_code, wbs_name, level, sort_order)
VALUES (1, 1, '1.5', 'Testing', 2, 5);

INSERT INTO project_wbs (project_id, parent_wbs_id, wbs_code, wbs_name, level, sort_order)
VALUES (1, 1, '1.6', 'Training', 2, 6);

INSERT INTO project_wbs (project_id, parent_wbs_id, wbs_code, wbs_name, level, sort_order)
VALUES (1, 1, '1.7', 'Go-Live', 2, 7);

INSERT INTO project_wbs (project_id, parent_wbs_id, wbs_code, wbs_name, level, sort_order)
VALUES (1, 1, '1.8', 'Hypercare', 2, 8);

-- WBS Level 3 - Work Packages (example for Requirements Gathering)
INSERT INTO project_wbs (project_id, parent_wbs_id, wbs_code, wbs_name, level, sort_order)
VALUES (1, 2, '1.2.1', 'Stakeholder Interviews', 3, 1);

INSERT INTO project_wbs (project_id, parent_wbs_id, wbs_code, wbs_name, level, sort_order)
VALUES (1, 2, '1.2.2', 'Current State Analysis', 3, 2);

INSERT INTO project_wbs (project_id, parent_wbs_id, wbs_code, wbs_name, level, sort_order)
VALUES (1, 2, '1.2.3', 'Requirements Documentation', 3, 3);

INSERT INTO project_wbs (project_id, parent_wbs_id, wbs_code, wbs_name, level, sort_order)
VALUES (1, 2, '1.2.4', 'Requirements Workshop', 3, 4);

INSERT INTO project_wbs (project_id, parent_wbs_id, wbs_code, wbs_name, level, sort_order)
VALUES (1, 2, '1.2.5', 'Requirements Sign-off', 3, 5);
```

---

## Project Phases

### Phases for ERP Implementation

```sql
INSERT INTO project_phases (project_id, phase_name, phase_order, description, planned_start_date, planned_end_date, actual_start_date, status, progress)
VALUES (1, 'Initiation', 1, 'Project initiation and charter development', '2026-01-15', '2026-01-31', '2026-01-15', 'Completed', 100);

INSERT INTO project_phases (project_id, phase_name, phase_order, description, planned_start_date, planned_end_date, actual_start_date, status, progress)
VALUES (1, 'Requirements', 2, 'Requirements gathering and analysis', '2026-02-01', '2026-03-15', '2026-02-01', 'Completed', 100);

INSERT INTO project_phases (project_id, phase_name, phase_order, description, planned_start_date, planned_end_date, actual_start_date, status, progress)
VALUES (1, 'Design', 3, 'Solution design and architecture', '2026-03-16', '2026-05-15', '2026-03-16', 'In Progress', 65);

INSERT INTO project_phases (project_id, phase_name, phase_order, description, planned_start_date, planned_end_date, status, progress)
VALUES (1, 'Build', 4, 'System build and configuration', '2026-05-16', '2026-10-31', 'Pending', 0);

INSERT INTO project_phases (project_id, phase_name, phase_order, description, planned_start_date, planned_end_date, status, progress)
VALUES (1, 'Testing', 5, 'System integration testing', '2026-11-01', '2027-01-15', 'Pending', 0);

INSERT INTO project_phases (project_id, phase_name, phase_order, description, planned_start_date, planned_end_date, status, progress)
VALUES (1, 'Training', 6, 'User training and documentation', '2027-01-16', '2027-02-28', 'Pending', 0);

INSERT INTO project_phases (project_id, phase_name, phase_order, description, planned_start_date, planned_end_date, status, progress)
VALUES (1, 'Go-Live', 7, 'Production deployment', '2027-03-01', '2027-03-15', 'Pending', 0);

INSERT INTO project_phases (project_id, phase_name, phase_order, description, planned_start_date, planned_end_date, status, progress)
VALUES (1, 'Hypercare', 8, 'Post go-live support', '2027-03-16', '2027-03-31', 'Pending', 0);
```

---

## Milestones

### Milestones for ERP Implementation

```sql
INSERT INTO project_milestones (project_id, milestone_code, milestone_name, milestone_type, owner_user_id, planned_date, target_date, status, progress_contribution)
VALUES (1, 'MS0001', 'Project Charter Approved', 'Decision', 2, '2026-01-31', '2026-01-31', 'Completed', 5);

INSERT INTO project_milestones (project_id, milestone_code, milestone_name, milestone_type, owner_user_id, planned_date, target_date, actual_completion_date, status, progress_contribution)
VALUES (1, 'MS0002', 'Requirements Complete', 'Phase End', 2, '2026-03-15', '2026-03-15', '2026-03-14', 'Completed', 10);

INSERT INTO project_milestones (project_id, milestone_code, milestone_name, milestone_type, owner_user_id, planned_date, target_date, status, progress_contribution)
VALUES (1, 'MS0003', 'Design Sign-Off', 'Deliverable', 2, '2026-05-15', '2026-05-15', 'Pending', 10);

INSERT INTO project_milestones (project_id, milestone_code, milestone_name, milestone_type, owner_user_id, planned_date, target_date, status, progress_contribution)
VALUES (1, 'MS0004', 'System Integration Test Complete', 'Phase End', 2, '2026-11-30', '2026-11-30', 'Pending', 15);

INSERT INTO project_milestones (project_id, milestone_code, milestone_name, milestone_type, owner_user_id, planned_date, target_date, status, progress_contribution)
VALUES (1, 'MS0005', 'UAT Complete', 'Phase End', 2, '2027-01-15', '2027-01-15', 'Pending', 15);

INSERT INTO project_milestones (project_id, milestone_code, milestone_name, milestone_type, owner_user_id, planned_date, target_date, status, progress_contribution)
VALUES (1, 'MS0006', 'Training Complete', 'Phase End', 2, '2027-02-28', '2027-02-28', 'Pending', 10);

INSERT INTO project_milestones (project_id, milestone_code, milestone_name, milestone_type, owner_user_id, planned_date, target_date, status, progress_contribution)
VALUES (1, 'MS0007', 'Go-Live', 'External', 4, '2027-03-15', '2027-03-15', 'Pending', 20);

INSERT INTO project_milestones (project_id, milestone_code, milestone_name, milestone_type, owner_user_id, planned_date, target_date, status, progress_contribution)
VALUES (1, 'MS0008', 'Hypercare Complete', 'Phase End', 2, '2027-03-31', '2027-03-31', 'Pending', 15);
```

---

## Tasks with Assignees

### Tasks for Requirements Phase (ERP Project)

```sql
-- Task: Conduct stakeholder interviews
INSERT INTO project_tasks (
    project_id, phase_id, wbs_id, task_code, task_name, description, task_type_id,
    category, priority, status, owner_user_id, assigned_user_id,
    planned_start_date, planned_end_date, duration_days, estimated_hours,
    progress, milestone_id, deliverable
) VALUES (
    1, 2, NULL, 'TSK00001', 'Conduct Stakeholder Interviews', 'Interview key stakeholders across finance, HR, and operations to gather business requirements',
    1, 'Requirements', 'High', 'Completed', 2, 8, '2026-02-01', '2026-02-14', 10, 40, 100, 2,
    'Stakeholder interview notes and feedback summary'
);

-- Task: Document current state processes
INSERT INTO project_tasks (
    project_id, phase_id, wbs_id, task_code, task_name, description,
    category, priority, status, owner_user_id, assigned_user_id,
    planned_start_date, planned_end_date, duration_days, estimated_hours,
    progress, deliverable
) VALUES (
    1, 2, NULL, 'TSK00002', 'Document Current State Processes', 'Document AS-IS business processes for process improvement opportunities',
    'Requirements', 'High', 'Completed', 2, 9, '2026-02-15', '2026-02-28', 10, 60, 100,
    'Current state process documentation'
);

-- Task: Create requirements specification
INSERT INTO project_tasks (
    project_id, phase_id, wbs_id, task_code, task_name, description,
    category, priority, status, owner_user_id, assigned_user_id,
    planned_start_date, planned_end_date, duration_days, estimated_hours,
    progress, deliverable
) VALUES (
    1, 2, NULL, 'TSK00003', 'Create Requirements Specification', 'Develop detailed functional and non-functional requirements specification',
    'Requirements', 'Critical', 'In Progress', 2, 10, '2026-03-01', '2026-03-10', 8, 32, 75,
    'Requirements specification document'
);

-- Task: Requirements review workshop
INSERT INTO project_tasks (
    project_id, phase_id, wbs_id, task_code, task_name, description,
    category, priority, status, owner_user_id, assigned_user_id,
    planned_start_date, planned_end_date, duration_days, estimated_hours,
    progress, deliverable
) VALUES (
    1, 2, NULL, 'TSK00004', 'Requirements Review Workshop', 'Facilitate requirements review workshop with key stakeholders',
    'Requirements', 'High', 'Open', 2, 8, '2026-03-11', '2026-03-12', 2, 16, 0,
    'Requirements workshop sign-off'
);

-- Task: Requirements sign-off
INSERT INTO project_tasks (
    project_id, phase_id, wbs_id, task_code, task_name, description,
    category, priority, status, owner_user_id, assigned_user_id,
    planned_start_date, planned_end_date, duration_days, estimated_hours,
    progress, milestone_id, deliverable
) VALUES (
    1, 2, NULL, 'TSK00005', 'Requirements Sign-Off', 'Obtain formal sign-off from stakeholders on requirements specification',
    'Requirements', 'Critical', 'Open', 2, 4, '2026-03-13', '2026-03-15', 3, 24, 0, 2,
    'Signed requirements specification'
);
```

### Tasks for Design Phase (ERP Project)

```sql
-- Task: Solution architecture design
INSERT INTO project_tasks (
    project_id, phase_id, task_code, task_name, description,
    category, priority, status, owner_user_id, assigned_user_id,
    planned_start_date, planned_end_date, duration_days, estimated_hours,
    progress, deliverable
) VALUES (
    1, 3, 'TSK00006', 'Solution Architecture Design', 'Design solution architecture including integration patterns, security, and scalability',
    'Design', 'Critical', 'In Progress', 2, 11, '2026-03-16', '2026-04-05', 15, 80, 40,
    'Solution architecture document'
);

-- Task: Database design
INSERT INTO project_tasks (
    project_id, phase_id, task_code, task_name, description,
    category, priority, status, owner_user_id, assigned_user_id,
    planned_start_date, planned_end_date, duration_days, estimated_hours,
    progress, deliverable
) VALUES (
    1, 3, 'TSK00007', 'Database Design', 'Design database schema and data model for all ERP modules',
    'Design', 'Critical', 'In Progress', 2, 12, '2026-04-01', '2026-04-20', 15, 60, 30,
    'Database design document'
);

-- Task: UI/UX wireframes
INSERT INTO project_tasks (
    project_id, phase_id, task_code, task_name, description,
    category, priority, status, owner_user_id, assigned_user_id,
    planned_start_date, planned_end_date, duration_days, estimated_hours,
    progress, deliverable
) VALUES (
    1, 3, 'TSK00008', 'UI/UX Wireframes', 'Create wireframes and prototypes for key user interfaces',
    'Design', 'Medium', 'Open', 2, 13, '2026-04-15', '2026-04-30', 12, 48, 0,
    'UI/UX wireframes'
);

-- Task: Integration design
INSERT INTO project_tasks (
    project_id, phase_id, task_code, task_name, description,
    category, priority, status, owner_user_id, assigned_user_id,
    planned_start_date, planned_end_date, duration_days, estimated_hours,
    progress, deliverable
) VALUES (
    1, 3, 'TSK00009', 'Integration Design', 'Design integration architecture for connecting ERP with existing systems',
    'Design', 'High', 'Open', 2, 11, '2026-04-20', '2026-05-05', 12, 56, 0,
    'Integration design document'
);

-- Task: Design review and sign-off
INSERT INTO project_tasks (
    project_id, phase_id, task_code, task_name, description,
    category, priority, status, owner_user_id, assigned_user_id,
    planned_start_date, planned_end_date, duration_days, estimated_hours,
    progress, milestone_id, deliverable
) VALUES (
    1, 3, 'TSK00010', 'Design Review and Sign-Off', 'Conduct design review and obtain stakeholder sign-off',
    'Design', 'Critical', 'Open', 2, 4, '2026-05-10', '2026-05-15', 4, 24, 0, 3,
    'Design sign-off approval'
);
```

---

## Resource Allocations

### Resource Allocations for ERP Project

```sql
-- Project Manager allocation
INSERT INTO project_resource_allocations (
    project_id, resource_type, resource_id, role_on_project,
    allocation_percentage, planned_hours, planned_start_date, planned_end_date,
    allocation_status, availability_status
) VALUES (1, 'user', 2, 'Project Manager', 50, 800, '2026-01-15', '2027-03-31', 'Allocated', 'Available');

-- Business Analyst allocation
INSERT INTO project_resource_allocations (
    project_id, resource_type, resource_id, role_on_project,
    allocation_percentage, planned_hours, planned_start_date, planned_end_date,
    allocation_status, availability_status
) VALUES (1, 'user', 8, 'Business Analyst', 100, 600, '2026-02-01', '2026-05-15', 'Allocated', 'Available');

-- Solution Architect allocation
INSERT INTO project_resource_allocations (
    project_id, resource_type, resource_id, role_on_project,
    allocation_percentage, planned_hours, planned_start_date, planned_end_date,
    allocation_status, availability_status
) VALUES (1, 'user', 11, 'Solution Architect', 75, 500, '2026-03-16', '2026-12-31', 'Allocated', 'Available');

-- Database Admin allocation
INSERT INTO project_resource_allocations (
    project_id, resource_type, resource_id, role_on_project,
    allocation_percentage, planned_hours, planned_start_date, planned_end_date,
    allocation_status, availability_status
) VALUES (1, 'user', 12, 'Database Administrator', 80, 400, '2026-04-01', '2026-10-31', 'Allocated', 'Available');

-- Developer allocations
INSERT INTO project_resource_allocations (
    project_id, resource_type, resource_id, role_on_project,
    allocation_percentage, planned_hours, planned_start_date, planned_end_date,
    allocation_status, availability_status
) VALUES (1, 'user', 14, 'Lead Developer', 100, 1200, '2026-05-16', '2027-01-31', 'Allocated', 'Available');

INSERT INTO project_resource_allocations (
    project_id, resource_type, resource_id, role_on_project,
    allocation_percentage, planned_hours, planned_start_date, planned_end_date,
    allocation_status, availability_status
) VALUES (1, 'user', 15, 'Developer', 100, 1000, '2026-05-16', '2027-01-31', 'Allocated', 'Available');

INSERT INTO project_resource_allocations (
    project_id, resource_type, resource_id, role_on_project,
    allocation_percentage, planned_hours, planned_start_date, planned_end_date,
    allocation_status, availability_status
) VALUES (1, 'user', 16, 'Developer', 100, 1000, '2026-05-16', '2027-01-31', 'Allocated', 'Available');

-- QA Analyst allocation
INSERT INTO project_resource_allocations (
    project_id, resource_type, resource_id, role_on_project,
    allocation_percentage, planned_hours, planned_start_date, planned_end_date,
    allocation_status, availability_status
) VALUES (1, 'user', 17, 'QA Analyst', 80, 400, '2026-11-01', '2027-02-28', 'Allocated', 'Available');

-- Trainer allocation
INSERT INTO project_resource_allocations (
    project_id, resource_type, resource_id, role_on_project,
    allocation_percentage, planned_hours, planned_start_date, planned_end_date,
    allocation_status, availability_status
) VALUES (1, 'user', 18, 'Training Lead', 50, 200, '2027-01-16', '2027-02-28', 'Allocated', 'Available');
```

---

## Budget Data

### Budget for ERP Implementation

```sql
-- Main project budget
INSERT INTO project_budget_items (project_id, budget_code, category, description, budget_amount, approved_amount, committed_amount, spent_amount, period)
VALUES (1, 'BUD-ERP-2026', 'Labor', 'Internal labor costs', 450000.00, 450000.00, 120000.00, 95000.00, '2026');

INSERT INTO project_budget_items (project_id, budget_code, category, description, budget_amount, approved_amount, committed_amount, spent_amount, period)
VALUES (1, 'BUD-ERP-2026', 'Software', 'Software licenses and subscriptions', 200000.00, 200000.00, 180000.00, 45000.00, '2026');

INSERT INTO project_budget_items (project_id, budget_code, category, description, budget_amount, approved_amount, committed_amount, spent_amount, period)
VALUES (1, 'BUD-ERP-2026', 'Hardware', 'Hardware and infrastructure', 150000.00, 150000.00, 120000.00, 0.00, '2026');

INSERT INTO project_budget_items (project_id, budget_code, category, description, budget_amount, approved_amount, committed_amount, spent_amount, period)
VALUES (1, 'BUD-ERP-2026', 'Consulting', 'External consulting services', 300000.00, 300000.00, 200000.00, 75000.00, '2026');

INSERT INTO project_budget_items (project_id, budget_code, category, description, budget_amount, approved_amount, committed_amount, spent_amount, period)
VALUES (1, 'BUD-ERP-2026', 'Training', 'User training and enablement', 75000.00, 75000.00, 0.00, 0.00, '2026');

INSERT INTO project_budget_items (project_id, budget_code, category, description, budget_amount, approved_amount, committed_amount, spent_amount, period)
VALUES (1, 'BUD-ERP-2026', 'Contingency', 'Project contingency', 125000.00, 125000.00, 0.00, 0.00, '2026');
```

---

## Risks

### Risks for ERP Implementation

```sql
-- Risk 1: Key resource turnover
INSERT INTO project_risks (
    project_id, risk_number, risk_title, category, probability, impact, risk_score,
    owner_user_id, status, mitigation_plan, contingency_plan,
    identified_date, review_date, is_active
) VALUES (
    1, 'RSK-001', 'Key Technical Resource Turnover',
    'Resource', 'Medium', 'High', 'High',
    2, 'Mitigating',
    'Cross-train team members, document knowledge, maintain backup resources',
    'Engage consulting firm for knowledge transfer if key resources leave',
    '2026-01-20', '2026-06-20', 1
);

-- Risk 2: Integration complexity
INSERT INTO project_risks (
    project_id, risk_number, risk_title, category, probability, impact, risk_score,
    owner_user_id, status, mitigation_plan, contingency_plan,
    identified_date, review_date, is_active
) VALUES (
    1, 'RSK-002', 'Legacy System Integration Complexity',
    'Technical', 'High', 'High', 'Critical',
    11, 'Identified',
    'Conduct thorough integration assessment, prototype critical interfaces early',
    'Implement middleware for complex integrations, defer non-critical integrations',
    '2026-02-01', '2026-04-01', 1
);

-- Risk 3: Budget overrun
INSERT INTO project_risks (
    project_id, risk_number, risk_title, category, probability, impact, risk_score,
    owner_user_id, status, mitigation_plan, contingency_plan,
    identified_date, review_date, is_active
) VALUES (
    1, 'RSK-003', 'Budget Overrun Due to Scope Creep',
    'Budget', 'Medium', 'Medium', 'Medium',
    2, 'Mitigating',
    'Strict scope management, formal change control process, weekly budget monitoring',
    'Use contingency budget, reduce scope if necessary',
    '2026-01-15', '2026-12-15', 1
);

-- Risk 4: User adoption
INSERT INTO project_risks (
    project_id, risk_number, risk_title, category, probability, impact, risk_score,
    owner_user_id, status, mitigation_plan, contingency_plan,
    identified_date, review_date, is_active
) VALUES (
    1, 'RSK-004', 'Low User Adoption Rate',
    'Operational', 'Medium', 'High', 'High',
    2, 'Identified',
    'Comprehensive training program, change management activities, executive sponsorship',
    'Extended hypercare period, additional training sessions, super user network',
    '2026-03-01', '2026-08-01', 1
);
```

---

## Issues

### Issues for ERP Implementation

```sql
-- Issue 1: Data migration blocker
INSERT INTO project_issues (
    project_id, issue_number, issue_title, category, severity, impact,
    owner_user_id, reported_by_user_id, reported_date, due_date,
    is_blocker, status, mitigation_plan, escalation_level
) VALUES (
    1, 'ISS-00001', 'Legacy Data Migration Quality Issues',
    'Technical', 'High', 'Data quality issues identified in legacy system prevent migration planning',
    12, 8, '2026-03-15', '2026-04-10',
    1, 'In Progress',
    'Data cleansing project initiated, legacy vendor engaged for data export support',
    'Escalated to Steering Committee'
);

-- Issue 2: Resource availability
INSERT INTO project_issues (
    project_id, issue_number, issue_title, category, severity, impact,
    owner_user_id, reported_by_user_id, reported_date, due_date,
    is_blocker, status, mitigation_plan
) VALUES (
    1, 'ISS-00002', 'Business Analyst Full-Time Availability',
    'Resource', 'Medium', 'Business analyst has partial allocation causing requirement gathering delays',
    2, 2, '2026-02-20', '2026-03-15',
    0, 'In Progress',
    'Negotiated temporary increase to 80% allocation, backfill for current tasks'
);

-- Issue 3: Training environment delay
INSERT INTO project_issues (
    project_id, issue_number, issue_title, category, severity, impact,
    owner_user_id, reported_by_user_id, reported_date, due_date,
    is_blocker, status, mitigation_plan
) VALUES (
    1, 'ISS-00003', 'Training Environment Setup Delay',
    'Technical', 'Low', 'Training environment setup dependent on infrastructure team capacity',
    18, 2, '2026-03-25', '2026-04-20',
    0, 'Open',
    'Infrastructure team has committed timeline, backup plan is remote training option'
);
```

---

## Change Requests

### Change Requests for ERP Implementation

```sql
-- Change Request 1: Additional reporting module
INSERT INTO project_changes (
    project_id, change_number, change_title, description, change_type,
    requester_user_id, request_date, impact_analysis,
    schedule_impact_days, cost_impact, status,
    approver_user_id, decision_date, decision_reason
) VALUES (
    1, 'CR-001', 'Add Operational Reporting Module',
    'Add operational dashboards and self-service reporting capabilities beyond original scope',
    'Scope', 8, '2026-02-15',
    'Requires additional development time for reporting framework and dashboard design',
    15, 45000.00, 'Approved',
    4, '2026-02-28', 'Approved - high business value justified by moderate cost and schedule impact'
);

-- Change Request 2: Mobile access requirement
INSERT INTO project_changes (
    project_id, change_number, change_title, description, change_type,
    requester_user_id, request_date, impact_analysis,
    schedule_impact_days, cost_impact, status,
    approver_user_id, decision_date, decision_reason
) VALUES (
    1, 'CR-002', 'Mobile Access for Executives',
    'Add mobile-responsive interfaces for executive dashboard access on tablets and smartphones',
    'Scope', 4, '2026-03-10',
    'Leverages existing responsive design framework, minimal additional effort',
    5, 12000.00, 'Approved',
    4, '2026-03-20', 'Approved - small impact, high stakeholder value'
);
```

---

## Data Loading Instructions

### Quick Load Script

Save the following as `load_sample_data.sql` and execute against your database:

```bash
sqlite3 warehouse.db < load_sample_data.sql
```

### Verification Queries

After loading data, verify with these queries:

```sql
-- Check portfolio count
SELECT COUNT(*) as portfolio_count FROM portfolios;

-- Check program count
SELECT COUNT(*) as program_count FROM programs;

-- Check project count
SELECT COUNT(*) as project_count FROM projects;

-- Check milestone count
SELECT COUNT(*) as milestone_count FROM project_milestones;

-- Check task count
SELECT COUNT(*) as task_count FROM project_tasks;

-- Check risk count
SELECT COUNT(*) as risk_count FROM project_risks;

-- Check issue count
SELECT COUNT(*) as issue_count FROM project_issues;

-- Check resource allocation count
SELECT COUNT(*) as allocation_count FROM project_resource_allocations;

-- Check project list with status
SELECT project_code, project_name, status, progress FROM projects ORDER BY project_code;
```

### Expected Counts After Loading

| Entity | Expected Count |
|--------|----------------|
| Portfolios | 2 |
| Programs | 3 |
| Projects | 6 |
| Phases (per project) | 5-8 |
| WBS Nodes (per project) | 15-25 |
| Milestones (per project) | 4-8 |
| Tasks (per project) | 15-30 |
| Resource Allocations (per project) | 5-10 |
| Risks (per project) | 3-5 |
| Issues (per project) | 2-4 |
| Change Requests (per project) | 1-3 |

---

## Sample Users for Assignment

The following user IDs should exist in your system for task assignments:

| User ID | Role | Department |
|---------|------|------------|
| 1 | Global Admin | IT |
| 2 | PMO Manager | PMO |
| 3 | Project Manager | IT Development |
| 4 | Executive | C-Level |
| 5 | Project Manager | Facilities |
| 6 | Project Manager | IT Data |
| 7 | Project Coordinator | Finance |
| 8 | Business Analyst | PMO |
| 9 | Subject Matter Expert | Finance |
| 10 | Subject Matter Expert | HR |
| 11 | Solution Architect | IT Architecture |
| 12 | Database Administrator | IT Operations |
| 13 | UX Designer | IT Design |
| 14 | Lead Developer | IT Development |
| 15 | Developer | IT Development |
| 16 | Developer | IT Development |
| 17 | QA Analyst | IT Quality |
| 18 | Training Lead | HR Training |

---

*Document Version: 1.0*
*Last Updated: April 2026*
*Module: Project Management*
