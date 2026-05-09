# Quality Management Sample Data Guide

## Overview

The Quality Management module includes comprehensive sample data for demonstration, testing, and training purposes. This guide documents all sample data entities, their structure, and usage.

## Sample Data Seeding Script

The sample data is seeded via `seed_quality_data.py` which populates the database with realistic demo data across all quality entities.

## Quality Settings Data

### Quality Settings

| Field | Sample Value | Description |
|-------|-------------|-------------|
| `inspection_required` | `true` | Incoming inspection required |
| `auto_close_days` | `30` | Days to auto-close pending items |
| `default_severity` | `MEDIUM` | Default NCR severity |
| `enable_spc` | `true` | SPC module enabled |
| `enable_supplier_quality` | `true` | Supplier quality tracking enabled |
| `quality_alert_email` | `quality@whdash.com` | Alert email address |
| `default_inspector` | `inspector` | Default inspector role |
| `ncr_number_format` | `NCR-{YYYY}-{SEQ}` | NCR numbering format |
| `capa_number_format` | `CAPA-{YYYY}-{SEQ}` | CAPA numbering format |
| `audit_number_format` | `AUD-{YYYY}-{SEQ}` | Audit numbering format |

### Inspection Types

| Type Code | Type Name | Description |
|-----------|-----------|-------------|
| `INCOMING` | Incoming Inspection | Inspect items on receipt |
| `IN_PROCESS` | In-Process Inspection | Inspect during production |
| `FINAL` | Final Inspection | Inspect completed items |
| `WAREHOUSE` | Warehouse Inspection | Warehouse quality checks |
| `SUPPLIER` | Supplier Audit | Supplier site inspection |
| `CUSTOMER` | Customer Inspection | Customer site inspection |
| `RE_INSPECTION` | Re-Inspection | Re-inspect previously failed |

### Defect Categories

| Category Code | Category Name | Description |
|---------------|---------------|-------------|
| `DIMENSIONAL` | Dimensional | Size/measurement issues |
| `VISUAL` | Visual | Appearance defects |
| `FUNCTIONAL` | Functional | Function not working |
| `MATERIAL` | Material | Wrong/wrong quality material |
| `PACKAGING` | Packaging | Packaging issues |
| `LABELING` | Labeling | Label/ marking issues |
| `SAFETY` | Safety | Safety-related defects |
| `PERFORMANCE` | Performance | Performance below spec |
| `DOCUMENTATION` | Documentation | Documentation missing/incorrect |

### CAPA Categories

| Category Code | Category Name | Description |
|---------------|---------------|-------------|
| `CORRECTIVE` | Corrective Action | Fix existing problem |
| `PREVENTIVE` | Preventive Action | Prevent potential problem |
| `INVESTIGATION` | Investigation | Root cause investigation |
| `PROCESS_IMPROVEMENT` | Process Improvement | Process enhancement |
| `TRAINING` | Training | Staff training required |
| `DOCUMENT_UPDATE` | Document Update | Documentation revision |
| `EQUIPMENT` | Equipment | Equipment-related |
| `SUPPLIER` | Supplier | Supplier-related CAPA |

### Root Cause Categories

| Category Code | Category Name | Description |
|---------------|---------------|-------------|
| `MANUAL` | Human Error | Operator mistake |
| `MACHINE` | Machine | Equipment malfunction |
| `MATERIAL` | Material | Material defect |
| `METHOD` | Method | Procedure issue |
| `MEASUREMENT` | Measurement | Gauge/measurement issue |
| `ENVIRONMENT` | Environment | Environmental condition |
| `MANAGEMENT` | Management | Management/system issue |
| `DESIGN` | Design | Design deficiency |

## Quality Inspections Sample Data

### Sample Inspection 1: Incoming Inspection - Raw Materials

```json
{
  "inspection_number": "INS-2026-0001",
  "inspection_type": "INCOMING",
  "source_type": "PURCHASE_ORDER",
  "source_reference": "PO-2026-00150",
  "supplier_id": "SUPPLIER-001",
  "supplier_name": "ABC Materials Co.",
  "item_id": "ITEM-RAW-001",
  "item_code": "RAW-STL-001",
  "item_name": "Steel Sheet 4x8 16GA",
  "quantity_received": 500,
  "quantity_inspected": 50,
  "sample_size": 50,
  "inspection_date": "2026-04-15",
  "inspector_id": "USER-005",
  "inspector_name": "John Smith",
  "status": "PASSED",
  "result": "PASSED",
  "quantity_accepted": 500,
  "quantity_rejected": 0,
  "pass_rate": 100.0,
  "notes": "Material meets specification. Mill cert provided.",
  "disposition": "ACCEPT",
  "lot_number": "LOT-2026-0415-001"
}
```

### Sample Inspection 2: Incoming Inspection - Component with Failures

```json
{
  "inspection_number": "INS-2026-0002",
  "inspection_type": "INCOMING",
  "source_type": "PURCHASE_ORDER",
  "source_reference": "PO-2026-00155",
  "supplier_id": "SUPPLIER-002",
  "supplier_name": "XYZ Components Ltd.",
  "item_id": "ITEM-COMP-042",
  "item_code": "COMP-BRG-042",
  "item_name": "Ball Bearing 42mm",
  "quantity_received": 200,
  "quantity_inspected": 40,
  "sample_size": 40,
  "inspection_date": "2026-04-14",
  "inspector_id": "USER-005",
  "inspector_name": "John Smith",
  "status": "FAILED",
  "result": "FAILED",
  "quantity_accepted": 180,
  "quantity_rejected": 20,
  "pass_rate": 90.0,
  "notes": "10% of bearings show dimensional deviation. Reject lot pending supplier response.",
  "disposition": "CONDITIONAL",
  "lot_number": "LOT-2026-0414-002",
  "non_conformance_id": "NCR-2026-0002"
}
```

### Sample Inspection 3: In-Process Inspection - Manufacturing

```json
{
  "inspection_number": "INS-2026-0003",
  "inspection_type": "IN_PROCESS",
  "source_type": "WORK_ORDER",
  "source_reference": "WO-2026-0085",
  "production_line": "LINE-01",
  "item_id": "ITEM-FG-001",
  "item_code": "WIDGET-STD-01",
  "item_name": "Standard Widget Assembly",
  "quantity_produced": 100,
  "quantity_inspected": 20,
  "sample_size": 20,
  "inspection_date": "2026-04-16",
  "inspector_id": "USER-006",
  "inspector_name": "Maria Garcia",
  "status": "PASSED",
  "result": "PASSED",
  "quantity_accepted": 100,
  "quantity_rejected": 0,
  "pass_rate": 100.0,
  "first_pass_yield": 98.5,
  "notes": "First article inspection passed. Process is stable.",
  "disposition": "ACCEPT"
}
```

### Sample Inspection 4: Final Inspection - Pre-Shipment

```json
{
  "inspection_number": "INS-2026-0004",
  "inspection_type": "FINAL",
  "source_type": "SALES_ORDER",
  "source_reference": "SO-2026-0220",
  "customer_id": "CUST-015",
  "customer_name": "Acme Industries",
  "item_id": "ITEM-FG-001",
  "item_code": "WIDGET-STD-01",
  "item_name": "Standard Widget Assembly",
  "quantity_ordered": 50,
  "quantity_inspected": 50,
  "sample_size": 50,
  "inspection_date": "2026-04-17",
  "inspector_id": "USER-007",
  "inspector_name": "Ahmed Hassan",
  "status": "PASSED",
  "result": "PASSED",
  "quantity_accepted": 50,
  "quantity_rejected": 0,
  "pass_rate": 100.0,
  "notes": "Final inspection passed. Certificate of conformance attached.",
  "disposition": "RELEASE",
  "certificate_number": "COC-2026-0045"
}
```

## Non-Conformances Sample Data

### Sample NCR 1: Supplier Material Defect

```json
{
  "ncr_number": "NCR-2026-0001",
  "ncr_date": "2026-04-10",
  "ncr_type": "SUPPLIER",
  "severity": "MAJOR",
  "priority": "HIGH",
  "status": "OPEN",
  "source_type": "INSPECTION",
  "source_reference": "INS-2026-0002",
  "supplier_id": "SUPPLIER-002",
  "supplier_name": "XYZ Components Ltd.",
  "item_id": "ITEM-COMP-042",
  "item_code": "COMP-BRG-042",
  "item_name": "Ball Bearing 42mm",
  "lot_number": "LOT-2026-0414-002",
  "quantity_affected": 200,
  "quantity_defective": 20,
  "defect_category": "DIMENSIONAL",
  "defect_description": "Inner diameter out of tolerance. Spec: 42.00mm +/- 0.02mm. Actual: 42.08mm - 42.12mm",
  "immediate_action": "Lot placed on quarantine hold pending investigation.",
  "containment_action": "100% incoming inspection implemented for this supplier.",
  "root_cause_category": "SUPPLIER_PROCESS",
  "root_cause_description": "Supplier manufacturing process tolerance drift. No recent calibration of grinding equipment.",
  "corrective_action": "Supplier has been notified. Corrective action request sent.",
  "preventive_action": "Enhanced supplier quality agreement. Quarterly process audits.",
  "disposition": "RETURN_TO_SUPPLIER",
  "owner_id": "USER-010",
  "owner_name": "Sarah Johnson",
  "assigned_to_id": "USER-010",
  "assigned_to_name": "Sarah Johnson",
  "due_date": "2026-04-25",
  "capa_number": "CAPA-2026-0001",
  "cost_impact": 2500.00,
  "created_by": "USER-005",
  "created_date": "2026-04-10"
}
```

### Sample NCR 2: In-Process Quality Issue

```json
{
  "ncr_number": "NCR-2026-0002",
  "ncr_date": "2026-04-12",
  "ncr_type": "INTERNAL",
  "severity": "CRITICAL",
  "priority": "HIGH",
  "status": "IN_REVIEW",
  "source_type": "PRODUCTION",
  "source_reference": "WO-2026-0080",
  "production_line": "LINE-02",
  "item_id": "ITEM-FG-015",
  "item_code": "ASSY-CTRL-015",
  "item_name": "Control Panel Assembly",
  "quantity_affected": 25,
  "quantity_defective": 5,
  "defect_category": "FUNCTIONAL",
  "defect_description": "PCB assemblies showing intermittent connectivity. Suspected cold solder joints.",
  "immediate_action": "Production line halted for inspection of remaining 20 units.",
  "containment_action": "All assembled units held for full electrical testing.",
  "root_cause_category": "PROCESS",
  "root_cause_description": "Wave soldering equipment temperature calibration drift.",
  "corrective_action": "Equipment recalibrated. Solder paste storage procedures updated.",
  "preventive_action": "Preventive maintenance schedule enhanced. Daily calibration checks.",
  "disposition": "REWORK",
  "owner_id": "USER-011",
  "owner_name": "Michael Chen",
  "assigned_to_id": "USER-011",
  "assigned_to_name": "Michael Chen",
  "due_date": "2026-04-20",
  "capa_number": "CAPA-2026-0002",
  "cost_impact": 5000.00,
  "created_by": "USER-006"
}
```

### Sample NCR 3: Customer Complaint

```json
{
  "ncr_number": "NCR-2026-0003",
  "ncr_date": "2026-04-14",
  "ncr_type": "CUSTOMER",
  "severity": "MAJOR",
  "priority": "MEDIUM",
  "status": "DISPOSITION",
  "source_type": "CUSTOMER_COMPLAINT",
  "source_reference": "CC-2026-0045",
  "customer_id": "CUST-022",
  "customer_name": "TechCorp Solutions",
  "item_id": "ITEM-FG-008",
  "item_code": "SENSOR-TMP-008",
  "item_name": "Temperature Sensor Module",
  "invoice_number": "INV-2026-0890",
  "quantity_shipped": 100,
  "quantity_affected": 15,
  "quantity_defective": 15,
  "defect_category": "PERFORMANCE",
  "defect_description": "Customer reports 15% failure rate in field. Units showing drift beyond +/- 2C accuracy spec.",
  "immediate_action": "Technical support engaged with customer. Field units being returned for analysis.",
  "containment_action": "Same batch inventory quarantined. No further shipments of affected batch.",
  "root_cause_category": "MATERIAL",
  "root_cause_description": "Under investigation. Suspect thermal compound batch issue.",
  "corrective_action": "Under investigation.",
  "preventive_action": "Pending root cause analysis.",
  "disposition": "PENDING",
  "owner_id": "USER-012",
  "owner_name": "Emily Davis",
  "assigned_to_id": "USER-012",
  "assigned_to_name": "Emily Davis",
  "due_date": "2026-04-30",
  "cost_impact": 12000.00,
  "created_by": "USER-012"
}
```

## CAPA Sample Data

### Sample CAPA 1: Supplier Corrective Action

```json
{
  "capa_number": "CAPA-2026-0001",
  "capa_date": "2026-04-11",
  "capa_type": "CORRECTIVE",
  "category": "SUPPLIER",
  "severity": "MAJOR",
  "priority": "HIGH",
  "status": "IN_PROGRESS",
  "title": "XYZ Components - Bearing Dimensional Drift",
  "description": "Supplier bearing dimensional failures require corrective action to prevent recurrence.",
  "source_type": "NCR",
  "source_reference": "NCR-2026-0001",
  "affected_item": "Ball Bearing 42mm",
  "affected_supplier": "XYZ Components Ltd.",
  "root_cause": "Supplier grinding equipment calibration drift",
  "containment_actions": [
    "100% incoming inspection implemented",
    "Supplier notified with CAR-2026-001"
  ],
  "corrective_actions": [
    {
      "action": "Supplier to recalibrate all grinding equipment",
      "owner": "Supplier QA Manager",
      "due_date": "2026-04-18",
      "status": "VERIFIED"
    },
    {
      "action": "Third-party audit of supplier process",
      "owner": "Internal Supplier Quality",
      "due_date": "2026-04-25",
      "status": "IN_PROGRESS"
    }
  ],
  "preventive_actions": [
    {
      "action": "Update supplier quality agreement with calibration requirements",
      "owner": "Procurement",
      "due_date": "2026-05-01",
      "status": "PENDING"
    },
    {
      "action": "Implement quarterly supplier audits",
      "owner": "Supplier Quality",
      "due_date": "2026-05-15",
      "status": "PENDING"
    }
  ],
  "effectiveness_criteria": "Zero dimensional failures for 6 consecutive months",
  "effectiveness_review_date": "2026-10-15",
  "owner_id": "USER-010",
  "owner_name": "Sarah Johnson",
  "created_by": "USER-010",
  "created_date": "2026-04-11"
}
```

### Sample CAPA 2: Process Improvement Preventive Action

```json
{
  "capa_number": "CAPA-2026-0002",
  "capa_date": "2026-04-13",
  "capa_type": "PREVENTIVE",
  "category": "PROCESS_IMPROVEMENT",
  "severity": "MINOR",
  "priority": "MEDIUM",
  "status": "OPEN",
  "title": "Wave Soldering Equipment Enhancement",
  "description": "Proactive enhancement of wave soldering process based on equipment age and failure risk analysis.",
  "source_type": "RISK_ASSESSMENT",
  "source_reference": "RISK-2026-003",
  "root_cause": "Equipment approaching calibration drift threshold",
  "preventive_actions": [
    {
      "action": "Replace soldering equipment temperature controllers",
      "owner": "Maintenance Manager",
      "due_date": "2026-04-30",
      "status": "IN_PROGRESS"
    },
    {
      "action": "Update preventive maintenance schedule",
      "owner": "Maintenance Manager",
      "due_date": "2026-04-25",
      "status": "COMPLETED"
    },
    {
      "action": "Train operators on new calibration procedures",
      "owner": "Production Manager",
      "due_date": "2026-05-05",
      "status": "PENDING"
    }
  ],
  "effectiveness_criteria": "Zero soldering-related defects for 3 months post-implementation",
  "effectiveness_review_date": "2026-08-01",
  "owner_id": "USER-011",
  "owner_name": "Michael Chen",
  "created_by": "USER-011",
  "created_date": "2026-04-13"
}
```

## Audit Sample Data

### Sample Audit Plan 1: Internal Process Audit

```json
{
  "audit_number": "AUD-2026-0001",
  "audit_date": "2026-04-20",
  "audit_type": "INTERNAL",
  "audit_category": "PROCESS",
  "title": "Q2 2026 - Production Process Audit",
  "scope": "All production lines - Widget Assembly and Control Panel Assembly",
  "objectives": "Verify compliance with production procedures and quality management system requirements",
  "criteria": "ISO 9001:2015, Internal QMS procedures",
  "status": "SCHEDULED",
  "lead_auditor": "USER-015",
  "lead_auditor_name": "Robert Williams",
  "audit_team": ["USER-015", "USER-016"],
  "auditee_department": "Production",
  "scheduled_start": "2026-04-20 08:00",
  "scheduled_end": "2026-04-20 17:00",
  "location": "Main Production Facility",
  "checklist_id": "CHK-PROC-001",
  "findings_count": 3,
  "created_by": "USER-015",
  "created_date": "2026-04-01"
}
```

### Sample Audit Plan 2: Supplier Quality Audit

```json
{
  "audit_number": "AUD-2026-0002",
  "audit_date": "2026-04-25",
  "audit_type": "SUPPLIER",
  "audit_category": "QUALITY_SYSTEM",
  "title": "XYZ Components Ltd. - Quality System Audit",
  "scope": "Quality management system, manufacturing process, calibration system",
  "objectives": "Evaluate supplier QMS compliance and capability following NCR-2026-0001",
  "criteria": "ISO 9001:2015, Customer-specific requirements",
  "status": "SCHEDULED",
  "lead_auditor": "USER-014",
  "lead_auditor_name": "Lisa Anderson",
  "audit_team": ["USER-014", "USER-010"],
  "auditee_name": "XYZ Components Ltd.",
  "auditee_contact": "John Smith, QA Director",
  "scheduled_start": "2026-04-25 09:00",
  "scheduled_end": "2026-04-25 17:00",
  "location": "XYZ Components Ltd. - Facility",
  "checklist_id": "CHK-SUP-002",
  "findings_count": 0,
  "created_by": "USER-014",
  "created_date": "2026-04-10"
}
```

### Sample Audit Findings

```json
{
  "finding_number": "FIND-2026-0001",
  "audit_number": "AUD-2026-0001",
  "finding_date": "2026-04-20",
  "finding_title": "Incomplete Calibration Records",
  "finding_category": "NON_CONFORMANCE",
  "finding_severity": "MINOR",
  "finding_status": "OPEN",
  "description": "Wave soldering equipment calibration records for Q1 2026 are incomplete. Last calibration date recorded as 2026-01-15 but equipment use log shows operation through March.",
  "evidence": "calibration_log_q1_2026.pdf",
  "root_cause": "No formal calibration tracking system in place",
  "corrective_action": "Implement digital calibration tracking system",
  "preventive_action": "Add calibration dates to maintenance calendar with automated alerts",
  "auditee_department": "Maintenance",
  "auditee_name": "Maintenance Manager",
  "auditor_id": "USER-015",
  "auditor_name": "Robert Williams",
  "owner_id": "USER-013",
  "owner_name": "David Brown",
  "due_date": "2026-05-15",
  "actual_closure_date": null,
  "verified_by": null,
  "created_by": "USER-015",
  "created_date": "2026-04-20"
}
```

```json
{
  "finding_number": "FIND-2026-0002",
  "audit_number": "AUD-2026-0001",
  "finding_date": "2026-04-20",
  "finding_title": "Missing Operator Training Records",
  "finding_category": "TRAINING",
  "finding_severity": "MAJOR",
  "finding_status": "OPEN",
  "description": "3 of 12 operators on Line 02 lack documented training for new soldering procedures introduced in February 2026.",
  "evidence": "training_matrix_line02.xlsx",
  "root_cause": "Training matrix not updated when new procedures were introduced",
  "corrective_action": "Immediate training for 3 operators. Retraining to be completed by 2026-04-27.",
  "preventive_action": "Update training matrix procedure to require update within 5 days of any procedure change",
  "auditee_department": "Production",
  "auditee_name": "Production Manager",
  "auditor_id": "USER-015",
  "auditor_name": "Robert Williams",
  "owner_id": "USER-011",
  "owner_name": "Michael Chen",
  "due_date": "2026-04-27",
  "actual_closure_date": null,
  "verified_by": null,
  "created_by": "USER-015",
  "created_date": "2026-04-20"
}
```

## Supplier Quality Sample Data

### Supplier Scorecard Summary

| Supplier | Quality Score | On-Time Delivery | Defect Rate | NCR Count | Audit Status |
|----------|--------------|------------------|-------------|-----------|--------------|
| ABC Materials Co. | 95% | 98% | 0.5% | 0 | Approved |
| XYZ Components Ltd. | 78% | 85% | 8.5% | 2 | Conditional |
| Global Fasteners Inc. | 92% | 94% | 1.2% | 0 | Approved |
| Premier Plastics | 88% | 90% | 2.8% | 1 | Approved |
| Steel Works Ltd. | 82% | 88% | 4.5% | 1 | Conditional |

### Held Inventory Sample

| Lot Number | Item | Quantity Held | Hold Reason | Hold Date | Status |
|------------|------|---------------|-------------|-----------|--------|
| LOT-2026-0414-002 | Ball Bearing 42mm | 200 | NCR-2026-0001 - Dimensional Defect | 2026-04-14 | ON_HOLD |
| LOT-2026-0412-015 | PCB Assembly Rev 3 | 50 | NCR-2026-0002 - Solder Joint Issue | 2026-04-12 | REWORK_PENDING |
| LOT-2026-0416-008 | Temperature Sensor | 100 | NCR-2026-0003 - Field Performance | 2026-04-16 | ON_HOLD |

## Dashboard Metrics Sample

### Quality Executive Dashboard

```json
{
  "date_range": "2026-04-01 to 2026-04-18",
  "total_inspections": 156,
  "inspection_pass_rate": 94.2,
  "total_ncrs": 18,
  "ncr_open": 8,
  "ncr_closed": 10,
  "ncr_overdue": 2,
  "total_capas": 12,
  "capa_open": 5,
  "capa_closed": 7,
  "capa_overdue": 1,
  "total_audits": 8,
  "audits_completed": 3,
  "audits_scheduled": 5,
  "open_findings": 6,
  "overdue_findings": 1,
  "held_inventory_value": 45000.00,
  "quality_cost": 125000.00,
  "quality_index": 87.5
}
```

## Export Configuration Sample

### Default Inspection Export Columns

```
inspection_number, inspection_type, source_reference, supplier_name, item_code, 
item_name, quantity_received, quantity_inspected, result, pass_rate, inspector_name,
inspection_date, disposition, status
```

### Default NCR Export Columns

```
ncr_number, ncr_date, ncr_type, severity, priority, status, supplier_name,
item_code, item_name, quantity_affected, defect_category, root_cause_category,
owner_name, due_date, cost_impact
```

### Default CAPA Export Columns

```
capa_number, capa_date, capa_type, category, severity, priority, status,
title, source_reference, owner_name, corrective_actions_count,
preventive_actions_count, due_date, effectiveness_review_date
```

## Flow Notification Sample Data

### Quality Alert Notifications

| Type | Title | Message | Severity |
|------|-------|---------|----------|
| `INSPECTION_FAILED` | Inspection Failed | INS-2026-0002 - Ball Bearing 42mm failed inspection. Supplier: XYZ Components. 10% defect rate. | HIGH |
| `NCR_CREATED` | NCR Created | NCR-2026-0001 created for Ball Bearing defect. Severity: MAJOR. Owner: Sarah Johnson. | HIGH |
| `NCR_OVERDUE` | NCR Overdue | NCR-2026-0002 is 3 days overdue. Assigned to: Michael Chen. | MEDIUM |
| `CAPA_CREATED` | CAPA Created | CAPA-2026-0001 created from NCR-2026-0001. Owner: Sarah Johnson. Due: 2026-04-25. | MEDIUM |
| `CAPA_OVERDUE` | CAPA Overdue | CAPA-2026-0002 is 5 days overdue. | HIGH |
| `AUDIT_FINDING` | Audit Finding | FIND-2026-0002 created. Major finding in Production Line 02. Due: 2026-04-27. | HIGH |
| `QUALITY_HOLD` | Item On Hold | LOT-2026-0414-002 (Ball Bearing 42mm) placed on quality hold. Qty: 200. | MEDIUM |
| `SUPPLIER_BLOCKED` | Supplier Blocked | XYZ Components Ltd. status changed to BLOCKED due to quality issues. | CRITICAL |

## Testing Recommendations

1. **Inspection Lifecycle**: Create, inspect, pass/fail, dispose
2. **NCR Workflow**: Create NCR, assign, investigate, disposition, close
3. **CAPA Workflow**: Create from NCR, add actions, complete, effectiveness review, close
4. **Audit Execution**: Schedule audit, execute, record findings, follow up, close
5. **Hold/Release**: Place on hold, review, release or reject
6. **Supplier Quality**: Create NCR against supplier, verify scorecard updates
7. **Export**: Test all export formats with various column selections
8. **Permissions**: Test role-based access to all quality features
9. **Multilingual**: Verify all screens render correctly in all 8 languages
10. **Flow Integration**: Verify notifications fire for quality events