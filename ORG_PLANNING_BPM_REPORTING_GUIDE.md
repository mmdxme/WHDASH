# Organizational Planning & BPM Reporting Guide

## Overview

This guide describes the reporting and analytics capabilities of the Organizational Planning & BPM module.

## Report Types

### 1. Organization Structure Report

**Access**: `/org-planning/reports/structure`

**Contents**:
- Complete org hierarchy tree
- Company, division, department, team listings
- Unit status (active/inactive)
- Employee counts per unit
- Cost center assignments

**Filters**:
- Company
- Unit type
- Status

**Export**: Excel, PDF

---

### 2. Headcount Report

**Access**: `/org-planning/reports/headcount`

**Contents**:
- Headcount by organization unit
- Approved vs current vs planned
- Vacancy tracking
- Utilization percentages
- Year-over-year comparisons

**Filters**:
- Year (2024, 2025, 2026)
- Organization unit
- Department

**Export**: Excel, PDF

---

### 3. Process Performance Report

**Access**: `/org-planning/reports/process-performance`

**Contents**:
- Total instances by workflow
- Completion rates
- Average cycle time
- Rejection rates
- SLA breach counts

**Filters**:
- Date range (7, 30, 90 days)
- Workflow category
- Priority level

**Export**: Excel, PDF

---

### 4. SLA Compliance Report

**Access**: `/org-planning/reports/sla-compliance`

**Contents**:
- SLA policy compliance rates
- Breach counts by policy
- Average resolution time
- Priority breakdown
- Trend analysis

**Filters**:
- Date range
- SLA policy
- Priority

**Export**: Excel, PDF

---

## Dashboard Widgets

### Key Metrics

| Widget | Description | Refresh |
|--------|-------------|---------|
| Total Organizations | Count of active org units | Real-time |
| Headcount vs Plan | Current vs approved headcount | Daily |
| SLA Compliance % | Overall SLA compliance rate | Real-time |
| Pending Approvals | Count of items awaiting action | Real-time |
| Active Workflows | Published workflow count | Real-time |

### Trend Charts

| Chart | Metrics | Period |
|-------|---------|---------|
| Headcount Trend | Monthly headcount | 12 months |
| Process Volume | Instances started/completed | 30 days |
| SLA Compliance | Compliance % over time | 30 days |
| Approval Cycle Time | Average approval hours | 30 days |

---

## Process Intelligence

### Bottleneck Analysis

**Access**: `/org-planning/monitoring/bottlenecks`

**Metrics**:
- Step average completion time
- Pending items per step
- Overdue items count
- Execution frequency

**Use Cases**:
- Identify which steps take longest
- Find steps with high pending counts
- Detect overdue items
- Optimize workflow design

---

### SLA Compliance Dashboard

**Access**: `/org-planning/monitoring`

**Metrics**:
- Overall compliance percentage
- Breach count by priority
- Average resolution time
- Policy comparison

**Alerts**:
- Warning at 75% threshold
- Critical at 50% threshold
- Breach notifications

---

## Custom Report Builder

### Available Fields

#### Organization
- Company name
- Unit name
- Unit type
- Unit status
- Employee count
- Budget

#### Positions
- Position title
- Level
- Grade
- Headcount (approved/current/vacant)
- Critical flag
- Authority level

#### Workflows
- Workflow name
- Category
- Total instances
- Completion rate
- Average cycle time
- SLA breach rate

#### Delegations
- Delegator name
- Delegate name
- Delegation type
- Status
- Date range
- Scope

---

## Export Formats

| Format | Use Case |
|--------|----------|
| Excel (.xlsx) | Detailed analysis, pivot tables |
| PDF | Executive summaries, printing |
| CSV | Data integration, external tools |

---

## Scheduled Reports

### Weekly Reports
- Headcount summary
- SLA compliance status
- Pending approvals

### Monthly Reports
- Full headcount report
- Process performance analysis
- SLA compliance trend

### Quarterly Reports
- Executive dashboard
- Budget vs actual
- Year-over-year comparison
