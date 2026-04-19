# Maintenance (EAM/PM) Sample Data Guide

## Overview

This document describes the sample/demo data available for the Maintenance module. The sample data is designed to demonstrate all features and provide realistic scenarios for testing and training.

## Seed Data Categories

### 1. Equipment & Facilities

#### Sample Facilities
| Code | Name | Type | Location |
|------|------|------|----------|
| FAC-0001 | Main Assembly Plant | Factory | Building A |
| FAC-0002 | Warehouse North | Warehouse | Building B |
| FAC-0003 | Office Complex | Office | Building C |
| FAC-0004 | Data Center | Data Center | Building D |
| FAC-0005 | Maintenance Shop | Factory | Building A |

#### Sample Equipment
| Code | Name | Category | Criticality |
|------|------|----------|-------------|
| EQ-ASSY-001 | CNC Milling Machine A1 | Production Equipment | High |
| EQ-ASSY-002 | CNC Milling Machine A2 | Production Equipment | High |
| EQ-PKG-001 | Packaging Line B1 | Packaging | Medium |
| EQ-HVAC-001 | HVAC Unit Central | HVAC | Critical |
| EQ-HVAC-002 | HVAC Unit Wing A | HVAC | High |
| EQ-COMP-001 | Compressor C1 | Compressors | Critical |
| EQ-COMP-002 | Compressor C2 | Compressors | High |
| EQ-FORK-001 | Forklift F1 | Vehicles | Medium |
| EQ-FORK-002 | Forklift F2 | Vehicles | Low |
| EQ-PUMP-001 | Coolant Pump P1 | Pumps | High |

### 2. Preventive Maintenance Schedules

#### Sample PM Plans
| Equipment | Schedule Name | Frequency | Interval | Next Due |
|----------|-------------|-----------|-----------|-----------|
| CNC Milling Machine A1 | Weekly Lubrication | Weekly | 7 days | 2026-04-25 |
| CNC Milling Machine A1 | Monthly Calibration | Monthly | 30 days | 2026-05-15 |
| CNC Milling Machine A2 | Weekly Lubrication | Weekly | 7 days | 2026-04-24 |
| Packaging Line B1 | Daily Inspection | Daily | 1 day | 2026-04-19 |
| HVAC Unit Central | Quarterly Service | Quarterly | 90 days | 2026-06-30 |
| HVAC Unit Wing A | Bi-Weekly Filter | Bi-Weekly | 14 days | 2026-04-28 |
| Compressor C1 | Monthly Inspection | Monthly | 30 days | 2026-05-10 |
| Forklift F1 | Weekly Safety Check | Weekly | 7 days | 2026-04-25 |
| Coolant Pump P1 | Daily Check | Daily | 1 day | 2026-04-19 |

### 3. Work Orders

#### Sample Work Order Statuses
| Status | Count | Description |
|--------|-------|-------------|
| Open | 5 | Newly created, not yet assigned |
| In Progress | 8 | Being worked on |
| On Hold | 3 | Waiting for parts or approval |
| Completed | 25 | Successfully completed |
| Closed | 42 | Verified and closed |

#### Sample Work Order Types
| Type | Priority Mix |
|------|-------------|
| Preventive | 45% |
| Corrective | 30% |
| Emergency | 8% |
| Inspection | 12% |
| Calibration | 5% |

### 4. Technicians & Teams

#### Sample Teams
| Team Code | Team Name | Lead | Members |
|-----------|-----------|------|--------|
| TEAM-MECH | Mechanical Team | John Smith | 4 |
| TEAM-ELEC | Electrical Team | Jane Doe | 3 |
| TEAM-HVAC | HVAC Team | Bob Johnson | 2 |
| TEAM-GEN | General Maintenance | Mike Brown | 3 |

#### Sample Technicians
| Employee Code | Name | Specialization | Skills |
|-------------|------|----------------|--------|
| TECH-001 | John Smith | Mechanical | Welding, Hydraulics, Pumps |
| TECH-002 | Jane Doe | Electrical | PLC, Motors, Wiring |
| TECH-003 | Bob Johnson | HVAC | Refrigeration, Air Systems |
| TECH-004 | Mike Brown | General | Multi-trade |
| TECH-005 | Sarah Wilson | Instrumentation | Calibrations, Sensors |

### 5. Labor & Time Tracking

#### Sample Labor Logs
| Date | Technician | Work Order | Hours | Type |
|------|------------|-----------|-------|------|
| 2026-04-15 | John Smith | WO-2026-0042 | 4.5 | Regular |
| 2026-04-15 | Jane Doe | WO-2026-0043 | 3.0 | Regular |
| 2026-04-16 | John Smith | WO-2026-0042 | 6.0 | Regular |
| 2026-04-16 | Mike Brown | WO-2026-0044 | 5.5 | Regular |
| 2026-04-17 | Bob Johnson | WO-2026-0045 | 4.0 | Regular |

### 6. Parts Usage

#### Sample Spare Parts
| Part Number | Name | Unit Cost | Stock |
|------------|------|-----------|-------|
| PART-001 | Bearing 6205-2RS | $12.50 | 50 |
| PART-002 | V-Belt B48 | $8.75 | 30 |
| PART-003 | Hydraulic Filter | $45.00 | 15 |
| PART-004 | PLC Battery | $28.00 | 20 |
| PART-005 | Drive Belt | $35.00 | 25 |

### 7. Downtime Records

#### Sample Downtime Incidents
| Date | Equipment | Reason | Duration | Impact | Type |
|------|----------|--------|----------|--------|------|
| 2026-04-10 | CNC Milling A1 | Bearing Failure | 8.5 hrs | High | Unplanned |
| 2026-04-12 | Compressor C1 | Planned Maintenance | 4.0 hrs | Medium | Planned |
| 2026-04-14 | Packaging B1 | Conveyor Belt | 3.0 hrs | High | Unplanned |
| 2026-04-15 | HVAC Central | Filter Replacement | 2.0 hrs | Low | Planned |

### 8. Checklists & Inspections

#### Sample Inspection Templates
| Template Code | Name | Type | Items |
|---------------|------|------|-------|
| EQUIP-INSP-001 | Standard Equipment Inspection | Safety | 8 |
| HVAC-INSP-001 | HVAC System Inspection | Inspection | 10 |
| SAFE-INSP-001 | Facility Safety Inspection | Safety | 8 |
| FORKLIFT-001 | Forklift Safety Check | Safety | 12 |

### 9. SLA Rules

| Priority | Response Time | Resolution Time | Escalation 1 | Escalation 2 |
|----------|---------------|-----------------|---------------|---------------|
| Critical | 1 hour | 4 hours | 1 hour | 2 hours |
| High | 2 hours | 8 hours | 2 hours | 4 hours |
| Medium | 4 hours | 24 hours | 4 hours | 8 hours |
| Low | 8 hours | 72 hours | 8 hours | 24 hours |

### 10. Dashboard Metrics

#### Sample Dashboard KPIs
| Metric | Value | Description |
|--------|-------|-------------|
| Open Work Orders | 15 | Currently active WOs |
| Overdue WOs | 3 | Past due date |
| PM Compliance Rate | 87% | On-time PM completion |
| Active Technicians | 8 | Available today |
| This Month Cost | $24,500 | MTD maintenance cost |
| Total Downtime (MTD) | 42 hrs | Month to date downtime |
| Missed PMs | 5 | Overdue PMs |
| Critical Alerts | 2 | Immediate attention needed |

## Test Scenarios

### Scenario 1: Emergency Breakdown
1. Equipment: CNC Milling Machine A1
2. Issue: Unexpected bearing failure
3. Actions: Create emergency work order → Assign technician → Log parts usage → Complete work order → Record downtime

### Scenario 2: Preventive Maintenance
1. Equipment: HVAC Unit Central
2. Task: Quarterly service
3. Actions: View PM schedule → Generate work order → Complete inspection checklist → Record labor → Close work order

### Scenario 3: Planner Board Assignment
1. Review unscheduled work orders
2. Check technician capacity
3. Assign work orders to technicians
4. Schedule dates
5. Monitor in-progress

### Scenario 4: Root Cause Analysis
1. Review recurring failure on Compressor C1
2. Identify failure pattern
3. Document root cause
4. Create corrective action plan
5. Schedule improvement work

## Generating Sample Data

The sample data is generated by the `seed_maintenance_data.py` script which creates:

1. 5 facilities
2. 10 equipment records
3. 15 PM schedules
4. 50 work orders (various statuses)
5. 8 technicians in 4 teams
6. 30 labor log entries
7. 20 parts usage records
8. 15 downtime incidents
9. 5 inspection templates
10. 4 SLA rules

To regenerate sample data:
```bash
python seed_maintenance_data.py
```
