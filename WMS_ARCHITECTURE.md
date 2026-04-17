# WMS Architecture Document
## Enterprise Warehouse Management System

---

## 1. System Overview

The WMS module provides end-to-end warehouse management capabilities for the enterprise ERP system. It integrates with procurement, sales, quality, and logistics operations.

### 1.1 Design Philosophy
- **Operational Speed**: Minimize clicks for daily warehouse tasks
- **Stock Accuracy**: Real-time inventory with full traceability
- **Exception Awareness**: Proactive alerting for discrepancies
- **Role-Based Execution**: Supports warehouse workers through executives
- **Multilingual**: Full support for 8 languages with RTL compatibility

---

## 2. Core Data Models

### 2.1 Warehouse Structure Hierarchy
```
Company (wms_companies)
└── Warehouse (wms_warehouses)
    ├── Zone (wms_zones)
    │   ├── Aisle (implicit in location codes)
    │   ├── Rack (implicit in location codes)
    │   └── Location (wms_locations)
    │       └── Bin Types, Capacity Rules
    └── Dock Doors (wms_dock_doors)
```

### 2.2 Item Master (wms_items)
- Part Number / SKU
- Barcode / Alternate Barcodes
- Batch / Serial / Expiry Tracking Flags
- Putaway Class / Picking Class
- Min/Max/Reorder Point Rules
- UOM / Packing Quantities
- ABC Velocity Classification
- Cycle Count Class

### 2.3 Inventory (wms_inventory_balances)
- Quantity by Status: Available, Reserved, Allocated, Blocked, Quarantine, Damaged
- Lot tracking with expiry
- Serial number tracking
- Location binding
- Full movement ledger

---

## 3. Key Processes

### 3.1 Receiving/Inbound
1. Expected Receipt created (manual or PO-linked)
2. Vehicle arrival registered (Yard Management)
3. Dock assignment
4. Physical receiving against receipt
5. QC Hold if quality check required
6. Putaway task generation
7. Putaway completion

### 3.2 Putaway
- Rule-based suggested location
- Zone-directed putaway
- Capacity-aware bin selection
- Override capability
- Confirmation workflow

### 3.3 Picking
- Single Order / Batch / Zone / Wave picking
- Pick task generation from outbound orders
- Short pick handling
- Pick confirmation with scan hook

### 3.4 Wave Management
- Wave templates with pre-configured strategies
- Order assignment to waves
- Wave release and execution monitoring
- Pick task generation from wave
- Progress tracking

### 3.5 Packing & Dispatch
- Packing queue from picked orders
- Station assignment
- Carton building with content validation
- Label generation
- Dispatch confirmation

### 3.6 Returns
- Customer Returns / Supplier Returns / Internal Returns
- RMA processing
- Inspection and quality decision
- Disposition: Return to Stock / Scrap / Hold / Vendor Return

### 3.7 Stock Count
- Cycle Count (ABC-based scheduling)
- Full Stock Count
- Blind Count option
- Variance review and approval
- Adjustment workflow

---

## 4. Supporting Modules

### 4.1 Yard/Gate/Dock Management
- Vehicle arrival/departure tracking
- Dock door assignment
- Waiting vehicle queue
- Dock scheduling calendar
- Activity logging

### 4.2 Labor/Task Management
- Task creation and assignment
- Priority-based work queue
- Operator workload visibility
- Productivity tracking
- Completion time analytics

### 4.3 RF/Scan Infrastructure
- Scan workbench for all operations
- Barcode rules management
- Scan audit log
- Mobile-ready UI architecture

---

## 5. Reporting & Analytics

### 5.1 Dashboards
- WMS Dashboard (operational overview)
- Executive Warehouse Dashboard (KPIs, trends)
- Inventory Dashboard
- Inbound/Outbound Dashboards
- Labor Productivity Dashboard

### 5.2 Standard Reports
- Inventory Summary
- Stock Movement
- Expiry Report
- Space Utilization
- Receiving/Putaway/Picking Reports
- Wave Performance
- Transfer Report
- Return Report
- Count Variance
- Quality Hold Inventory

---

## 6. Permissions & Security

### 6.1 Role Definitions
- **WMS Admin**: Full system access
- **Warehouse Manager**: Operations management
- **Warehouse Supervisor**: Floor supervision
- **Receiver**: Receiving operations
- **Picker/Packer**: Picking and packing tasks
- **Inventory Controller**: Stock management and counts
- **Auditor**: Read-only with audit trail access

### 6.2 Permission Matrix
- Module-level access control
- Warehouse scope filtering
- Action-level permissions (view/create/edit/delete/approve)
- Special permissions for sensitive operations

### 6.3 Audit Trail
- All stock changes logged with before/after values
- Operator identity captured
- Approval chain documented
- Full change history

---

## 7. Multilingual Support

### 7.1 Languages
- English (en)
- Persian/Farsi (fa)
- Arabic (ar)
- Russian (ru)
- Hindi (hi)
- Spanish (es)
- Chinese (zh)
- German (de)

### 7.2 RTL Support
- Full bidirectional layout support
- Proper text alignment
- Chart and table RTL adaptation
- Mixed content safe rendering

---

## 8. Integration Points

### 8.1 Flow Integration
- WMS alerts publish to Flow channels
- Escalation notifications
- Operator mentions
- Real-time warehouse activity

### 8.2 Other Modules
- Procurement (PO-linked receipts)
- Sales (outbound order fulfillment)
- Quality (QC holds, NCR integration)
- Finance (inventory valuation)
- Logistics (shipment tracking)

---

## 9. Database Schema

### 9.1 Core Tables
- wms_settings
- wms_companies, wms_warehouses, wms_zones, wms_locations
- wms_item_categories, wms_item_brands, wms_item_groups, wms_items
- wms_lots, wms_serial_numbers
- wms_inventory_balances, wms_inventory_ledger
- wms_inbound_receipts, wms_inbound_receipt_lines
- wms_putaway_tasks
- wms_pick_tasks, wms_pack_tasks, wms_shipments
- wms_wave_templates, wms_waves, wms_wave_orders
- wms_replenishment_tasks
- wms_transfers, wms_transfer_lines
- wms_returns, wms_return_lines
- wms_stock_counts, wms_stock_count_lines
- wms_stock_adjustments, wms_stock_adjustment_lines
- wms_qc_inspections
- wms_work_tasks
- wms_alerts
- wms_notifications
- wms_audit_log
- wms_rf_scan_log
- wms_yard_vehicles, wms_dock_doors, wms_dock_schedule, wms_yard_activity_log

---

## 10. Menu Structure

```
Warehouse (wms)
├── WMS Dashboard
├── Executive Warehouse Dashboard
├── Inventory
│   ├── Current Stock
│   ├── By Warehouse / By Location / Reserved
│   └── Stock Movements
├── Item Master
│   ├── All Items / Create Item
│   ├── Categories / Brands
│   └── Barcode / Labels
├── Locations
│   ├── Warehouse Zones
│   ├── Bins / Capacity
│   └── Location Mapping
├── Stock Count
│   ├── Count Plans / Open Counts
│   ├── Variances / History
│   └── New Stock Count
├── Receipts
│   ├── All Receipts / New Receipt
│   ├── Pending Putaway
│   └── Received Today / History
├── Shipments
│   ├── All Shipments / New Shipment
│   ├── Picking / Packed / Dispatched
│   └── Shipment History
├── Wave Management
│   ├── Wave List / Create Wave
│   └── Wave Templates
├── Yard Management
│   ├── Yard Overview
│   ├── Dock Doors
│   └── Dock Schedule
├── Labor Management
│   ├── Task Queue
│   └── Productivity
├── RF Scan Workbench
├── Returns
│   ├── Customer Returns
│   ├── Supplier Returns
│   └── Return History
└── Reports
    ├── Inventory / Movement / Expiry
    ├── Space Utilization
    ├── Receiving / Putaway / Picking
    └── Count Variance
```

---

*Document Version: 1.0*
*Last Updated: April 2026*