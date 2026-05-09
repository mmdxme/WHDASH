"""
BI Reporting Seed Data
====================
Seeds the Advanced Reporting / BI module with realistic demo data.

This module creates:
- Reporting datasets for all business domains
- Dataset fields with proper metadata
- KPI definitions across all categories
- Sample saved reports
- Sample ad-hoc queries
- Sample schedules
- Sample delivery logs
- Sample access logs

Run this script to populate the BI module with demo data.

Usage:
    python seed_bi_data.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from bi_reporting_models import (
    ReportingDataset, DatasetField, ReportingKPI, SavedReport,
    ReportSchedule, AdhocQuery, QueryLog, ReportAccessLog,
    ExportLog, DeliveryLog, ApprovalRequest, initialize_reporting_tables
)


def seed_datasets():
    """Create reporting datasets for all business domains."""
    print("Creating datasets...")
    
    datasets_data = [
        {
            'code': 'sales_orders',
            'name': 'Sales Orders',
            'description': 'Complete sales order transactions including header and line details',
            'module_domain': 'Sales',
            'base_table': 'sales_orders',
            'dataset_type': 'transactional'
        },
        {
            'code': 'sales_customers',
            'name': 'Customers',
            'description': 'Customer master data and financial summary',
            'module_domain': 'CRM',
            'base_table': 'sales_customers',
            'dataset_type': 'transactional'
        },
        {
            'code': 'inventory_balances',
            'name': 'Inventory Balances',
            'description': 'Current inventory positions by item and warehouse',
            'module_domain': 'Inventory',
            'base_table': 'wms_inventory_balances',
            'dataset_type': 'aggregated'
        },
        {
            'code': 'inventory_movements',
            'name': 'Stock Movements',
            'description': 'Inventory ledger transactions and movements',
            'module_domain': 'Inventory',
            'base_table': 'wms_inventory_ledger',
            'dataset_type': 'transactional'
        },
        {
            'code': 'purchase_orders',
            'name': 'Purchase Orders',
            'description': 'Purchase order transactions and receipts',
            'module_domain': 'Procurement',
            'base_table': 'purchase_orders',
            'dataset_type': 'transactional'
        },
        {
            'code': 'suppliers',
            'name': 'Suppliers',
            'description': 'Supplier master data and performance metrics',
            'module_domain': 'Procurement',
            'base_table': 'suppliers',
            'dataset_type': 'transactional'
        },
        {
            'code': 'delivery_trips',
            'name': 'Delivery Trips',
            'description': 'Delivery trip and stop records',
            'module_domain': 'Logistics',
            'base_table': 'delivery_trips',
            'dataset_type': 'transactional'
        },
        {
            'code': 'hr_employees',
            'name': 'HR Employees',
            'description': 'Employee master data and employment details',
            'module_domain': 'HR',
            'base_table': 'hr_employees',
            'dataset_type': 'transactional'
        },
        {
            'code': 'hr_attendance',
            'name': 'Attendance Records',
            'description': 'Employee attendance and time tracking',
            'module_domain': 'HR',
            'base_table': 'hr_attendance_records',
            'dataset_type': 'transactional'
        },
        {
            'code': 'finance_ar',
            'name': 'AR / Receivables',
            'description': 'Accounts receivable invoices and receipts',
            'module_domain': 'Finance',
            'base_table': 'ar_invoices',
            'dataset_type': 'transactional'
        },
        {
            'code': 'finance_ap',
            'name': 'AP / Payables',
            'description': 'Accounts payable bills and payments',
            'module_domain': 'Finance',
            'base_table': 'ap_bills',
            'dataset_type': 'transactional'
        },
        {
            'code': 'assets_register',
            'name': 'Fixed Assets',
            'description': 'Fixed asset register and depreciation',
            'module_domain': 'Assets',
            'base_table': 'assets',
            'dataset_type': 'transactional'
        },
        {
            'code': 'maintenance_work_orders',
            'name': 'Maintenance Work Orders',
            'description': 'Maintenance work orders and task tracking',
            'module_domain': 'Maintenance',
            'base_table': 'maintenance_work_orders',
            'dataset_type': 'transactional'
        },
        {
            'code': 'projects',
            'name': 'Projects',
            'description': 'Project tracking and task management',
            'module_domain': 'Projects',
            'base_table': 'projects',
            'dataset_type': 'transactional'
        },
        {
            'code': 'quality_inspections',
            'name': 'Quality Inspections',
            'description': 'Quality inspection results and NCR tracking',
            'module_domain': 'Quality',
            'base_table': 'quality_inspections',
            'dataset_type': 'transactional'
        },
        {
            'code': 'ecommerce_orders',
            'name': 'E-commerce Orders',
            'description': 'Online store orders and fulfillment',
            'module_domain': 'E-commerce',
            'base_table': 'ecommerce_orders',
            'dataset_type': 'transactional'
        },
    ]
    
    created_datasets = {}
    for ds_data in datasets_data:
        existing = ReportingDataset.get_by_code(ds_data['code'])
        if not existing:
            ds_id = ReportingDataset.create(**ds_data)
            created_datasets[ds_data['code']] = ds_id
            print(f"  Created dataset: {ds_data['name']} (ID: {ds_id})")
        else:
            created_datasets[ds_data['code']] = existing['id']
            print(f"  Dataset exists: {ds_data['name']} (ID: {existing['id']})")
    
    return created_datasets


def seed_dataset_fields(datasets):
    """Create fields for each dataset."""
    print("Creating dataset fields...")
    
    fields_data = {
        'sales_orders': [
            {'code': 'order_id', 'name': 'Order ID', 'data_type': 'number', 'field_category': 'identifier', 'is_groupable': True},
            {'code': 'order_number', 'name': 'Order Number', 'data_type': 'string', 'field_category': 'identifier', 'is_filterable': True, 'is_sortable': True},
            {'code': 'order_date', 'name': 'Order Date', 'data_type': 'date', 'field_category': 'date', 'is_filterable': True, 'is_sortable': True, 'is_groupable': True},
            {'code': 'customer_id', 'name': 'Customer ID', 'data_type': 'number', 'field_category': 'attribute'},
            {'code': 'customer_name', 'name': 'Customer Name', 'data_type': 'string', 'field_category': 'attribute', 'is_filterable': True, 'is_sortable': True, 'is_groupable': True},
            {'code': 'salesperson_id', 'name': 'Salesperson ID', 'data_type': 'number', 'field_category': 'attribute'},
            {'code': 'salesperson_name', 'name': 'Salesperson', 'data_type': 'string', 'field_category': 'attribute', 'is_filterable': True, 'is_groupable': True},
            {'code': 'status', 'name': 'Status', 'data_type': 'string', 'field_category': 'attribute', 'is_filterable': True, 'is_sortable': True, 'is_groupable': True},
            {'code': 'subtotal', 'name': 'Subtotal', 'data_type': 'number', 'field_category': 'measure', 'is_aggregatable': True, 'default_aggregation': 'SUM'},
            {'code': 'tax_amount', 'name': 'Tax Amount', 'data_type': 'number', 'field_category': 'measure', 'is_aggregatable': True, 'default_aggregation': 'SUM'},
            {'code': 'discount_amount', 'name': 'Discount', 'data_type': 'number', 'field_category': 'measure', 'is_aggregatable': True, 'default_aggregation': 'SUM'},
            {'code': 'total_amount', 'name': 'Total Amount', 'data_type': 'number', 'field_category': 'measure', 'is_aggregatable': True, 'default_aggregation': 'SUM'},
            {'code': 'company_id', 'name': 'Company ID', 'data_type': 'number', 'field_category': 'attribute', 'is_filterable': True},
            {'code': 'market', 'name': 'Market', 'data_type': 'string', 'field_category': 'attribute', 'is_filterable': True, 'is_groupable': True},
        ],
        'sales_customers': [
            {'code': 'customer_id', 'name': 'Customer ID', 'data_type': 'number', 'field_category': 'identifier'},
            {'code': 'name', 'name': 'Customer Name', 'data_type': 'string', 'field_category': 'attribute', 'is_filterable': True, 'is_sortable': True, 'is_groupable': True},
            {'code': 'phone', 'name': 'Phone', 'data_type': 'string', 'field_category': 'attribute'},
            {'code': 'location', 'name': 'Location', 'data_type': 'string', 'field_category': 'attribute', 'is_filterable': True, 'is_groupable': True},
            {'code': 'type', 'name': 'Customer Type', 'data_type': 'string', 'field_category': 'attribute', 'is_filterable': True, 'is_groupable': True},
            {'code': 'credit_limit', 'name': 'Credit Limit', 'data_type': 'number', 'field_category': 'measure', 'is_aggregatable': True},
            {'code': 'outstanding_balance', 'name': 'Outstanding Balance', 'data_type': 'number', 'field_category': 'measure', 'is_aggregatable': True, 'default_aggregation': 'SUM'},
            {'code': 'is_active', 'name': 'Is Active', 'data_type': 'boolean', 'field_category': 'attribute', 'is_filterable': True},
        ],
        'inventory_balances': [
            {'code': 'item_id', 'name': 'Item ID', 'data_type': 'number', 'field_category': 'identifier'},
            {'code': 'item_code', 'name': 'Item Code', 'data_type': 'string', 'field_category': 'identifier', 'is_filterable': True, 'is_sortable': True},
            {'code': 'item_name', 'name': 'Item Name', 'data_type': 'string', 'field_category': 'attribute', 'is_filterable': True, 'is_sortable': True},
            {'code': 'warehouse_id', 'name': 'Warehouse ID', 'data_type': 'number', 'field_category': 'attribute', 'is_filterable': True},
            {'code': 'warehouse_name', 'name': 'Warehouse', 'data_type': 'string', 'field_category': 'attribute', 'is_filterable': True, 'is_groupable': True},
            {'code': 'quantity', 'name': 'Quantity', 'data_type': 'number', 'field_category': 'measure', 'is_aggregatable': True, 'default_aggregation': 'SUM'},
            {'code': 'reserved', 'name': 'Reserved', 'data_type': 'number', 'field_category': 'measure', 'is_aggregatable': True, 'default_aggregation': 'SUM'},
            {'code': 'allocated', 'name': 'Allocated', 'data_type': 'number', 'field_category': 'measure', 'is_aggregatable': True, 'default_aggregation': 'SUM'},
            {'code': 'reorder_point', 'name': 'Reorder Point', 'data_type': 'number', 'field_category': 'measure'},
            {'code': 'unit_cost', 'name': 'Unit Cost', 'data_type': 'number', 'field_category': 'measure'},
            {'code': 'stock_value', 'name': 'Stock Value', 'data_type': 'number', 'field_category': 'measure', 'is_aggregatable': True, 'default_aggregation': 'SUM'},
        ],
        'purchase_orders': [
            {'code': 'po_id', 'name': 'PO ID', 'data_type': 'number', 'field_category': 'identifier'},
            {'code': 'po_number', 'name': 'PO Number', 'data_type': 'string', 'field_category': 'identifier', 'is_filterable': True},
            {'code': 'order_date', 'name': 'Order Date', 'data_type': 'date', 'field_category': 'date', 'is_filterable': True, 'is_sortable': True, 'is_groupable': True},
            {'code': 'supplier_id', 'name': 'Supplier ID', 'data_type': 'number', 'field_category': 'attribute'},
            {'code': 'supplier_name', 'name': 'Supplier', 'data_type': 'string', 'field_category': 'attribute', 'is_filterable': True, 'is_groupable': True},
            {'code': 'status', 'name': 'Status', 'data_type': 'string', 'field_category': 'attribute', 'is_filterable': True, 'is_groupable': True},
            {'code': 'total_amount', 'name': 'Total Amount', 'data_type': 'number', 'field_category': 'measure', 'is_aggregatable': True, 'default_aggregation': 'SUM'},
            {'code': 'purchase_type', 'name': 'Purchase Type', 'data_type': 'string', 'field_category': 'attribute', 'is_filterable': True, 'is_groupable': True},
        ],
        'delivery_trips': [
            {'code': 'trip_id', 'name': 'Trip ID', 'data_type': 'number', 'field_category': 'identifier'},
            {'code': 'trip_number', 'name': 'Trip Number', 'data_type': 'string', 'field_category': 'identifier', 'is_filterable': True},
            {'code': 'date', 'name': 'Date', 'data_type': 'date', 'field_category': 'date', 'is_filterable': True, 'is_sortable': True, 'is_groupable': True},
            {'code': 'status', 'name': 'Status', 'data_type': 'string', 'field_category': 'attribute', 'is_filterable': True, 'is_groupable': True},
            {'code': 'warehouse_name', 'name': 'Warehouse', 'data_type': 'string', 'field_category': 'attribute', 'is_filterable': True, 'is_groupable': True},
            {'code': 'driver_name', 'name': 'Driver', 'data_type': 'string', 'field_category': 'attribute', 'is_filterable': True, 'is_groupable': True},
            {'code': 'total_stops', 'name': 'Total Stops', 'data_type': 'number', 'field_category': 'measure', 'is_aggregatable': True, 'default_aggregation': 'COUNT'},
            {'code': 'completed_stops', 'name': 'Completed Stops', 'data_type': 'number', 'field_category': 'measure', 'is_aggregatable': True, 'default_aggregation': 'SUM'},
        ],
        'hr_employees': [
            {'code': 'employee_id', 'name': 'Employee ID', 'data_type': 'number', 'field_category': 'identifier'},
            {'code': 'employee_code', 'name': 'Employee Code', 'data_type': 'string', 'field_category': 'identifier'},
            {'code': 'first_name', 'name': 'First Name', 'data_type': 'string', 'field_category': 'attribute', 'is_sortable': True},
            {'code': 'last_name', 'name': 'Last Name', 'data_type': 'string', 'field_category': 'attribute', 'is_sortable': True},
            {'code': 'full_name', 'name': 'Full Name', 'data_type': 'string', 'field_category': 'attribute', 'is_filterable': True, 'is_groupable': True},
            {'code': 'department_name', 'name': 'Department', 'data_type': 'string', 'field_category': 'attribute', 'is_filterable': True, 'is_groupable': True},
            {'code': 'position_name', 'name': 'Position', 'data_type': 'string', 'field_category': 'attribute', 'is_filterable': True, 'is_groupable': True},
            {'code': 'status', 'name': 'Status', 'data_type': 'string', 'field_category': 'attribute', 'is_filterable': True, 'is_groupable': True},
            {'code': 'hire_date', 'name': 'Hire Date', 'data_type': 'date', 'field_category': 'date', 'is_filterable': True, 'is_groupable': True},
        ],
        'hr_attendance': [
            {'code': 'record_id', 'name': 'Record ID', 'data_type': 'number', 'field_category': 'identifier'},
            {'code': 'employee_name', 'name': 'Employee', 'data_type': 'string', 'field_category': 'attribute', 'is_filterable': True, 'is_groupable': True},
            {'code': 'date', 'name': 'Date', 'data_type': 'date', 'field_category': 'date', 'is_filterable': True, 'is_sortable': True, 'is_groupable': True},
            {'code': 'status', 'name': 'Status', 'data_type': 'string', 'field_category': 'attribute', 'is_filterable': True, 'is_groupable': True},
            {'code': 'check_in', 'name': 'Check In', 'data_type': 'time', 'field_category': 'attribute'},
            {'code': 'check_out', 'name': 'Check Out', 'data_type': 'time', 'field_category': 'attribute'},
            {'code': 'work_hours', 'name': 'Work Hours', 'data_type': 'number', 'field_category': 'measure'},
            {'code': 'overtime_hours', 'name': 'Overtime Hours', 'data_type': 'number', 'field_category': 'measure', 'is_aggregatable': True, 'default_aggregation': 'SUM'},
            {'code': 'late_minutes', 'name': 'Late Minutes', 'data_type': 'number', 'field_category': 'measure', 'is_aggregatable': True, 'default_aggregation': 'SUM'},
        ],
    }
    
    for ds_code, fields in fields_data.items():
        ds_id = datasets.get(ds_code)
        if not ds_id:
            continue
        
        existing_fields = DatasetField.get_by_dataset(ds_id)
        if existing_fields:
            continue
        
        for i, field in enumerate(fields):
            DatasetField.create(dataset_id=ds_id, display_order=i, **field)
        
        print(f"  Created {len(fields)} fields for {ds_code}")


def seed_kpis():
    """Create KPI definitions."""
    print("Creating KPI definitions...")
    
    kpis_data = [
        {
            'kpi_code': 'sales.total_revenue',
            'kpi_name': 'Total Revenue',
            'category': 'Sales',
            'description': 'Sum of all order amounts including tax',
            'business_definition': 'Total sales revenue from confirmed orders',
            'formula_description': 'SUM(sales_orders.total_amount) WHERE status NOT IN (Cancelled, Closed)',
            'dataset_code': 'sales_orders',
            'aggregation_type': 'SUM',
            'unit_of_measure': 'AED',
            'display_format': '#,##0',
            'target_direction': 'higher_is_better',
            'warning_threshold': 0.9,
            'critical_threshold': 0.8,
            'tags': ['sales', 'revenue', 'primary']
        },
        {
            'kpi_code': 'sales.order_count',
            'kpi_name': 'Order Count',
            'category': 'Sales',
            'description': 'Number of sales orders in period',
            'business_definition': 'Count of all sales orders',
            'formula_description': 'COUNT(sales_orders.id)',
            'dataset_code': 'sales_orders',
            'aggregation_type': 'COUNT',
            'unit_of_measure': 'count',
            'display_format': '#,##0',
            'target_direction': 'higher_is_better',
            'tags': ['sales', 'orders']
        },
        {
            'kpi_code': 'sales.avg_order_value',
            'kpi_name': 'Average Order Value',
            'category': 'Sales',
            'description': 'Average value per order',
            'business_definition': 'Total revenue divided by order count',
            'formula_description': 'SUM(total_amount) / COUNT(id)',
            'dataset_code': 'sales_orders',
            'aggregation_type': 'AVG',
            'unit_of_measure': 'AED',
            'display_format': '#,##0.00',
            'target_direction': 'higher_is_better',
            'tags': ['sales', 'revenue', 'efficiency']
        },
        {
            'kpi_code': 'inventory.total_value',
            'kpi_name': 'Total Inventory Value',
            'category': 'Inventory',
            'description': 'Total value of inventory on hand',
            'business_definition': 'Sum of quantity times unit cost for all items',
            'formula_description': 'SUM(wms_inventory_balances.quantity * items.unit_cost)',
            'dataset_code': 'inventory_balances',
            'aggregation_type': 'SUM',
            'unit_of_measure': 'AED',
            'display_format': '#,##0',
            'target_direction': 'range',
            'warning_threshold': 1.1,
            'critical_threshold': 1.2,
            'tags': ['inventory', 'value', 'balance']
        },
        {
            'kpi_code': 'inventory.stockout_count',
            'kpi_name': 'Stockout Items',
            'category': 'Inventory',
            'description': 'Number of items with zero stock',
            'business_definition': 'Count of items where quantity <= 0',
            'formula_description': 'COUNT(items WHERE quantity <= 0)',
            'dataset_code': 'inventory_balances',
            'aggregation_type': 'COUNT',
            'unit_of_measure': 'count',
            'display_format': '#,##0',
            'target_direction': 'lower_is_better',
            'warning_threshold': 5,
            'critical_threshold': 10,
            'tags': ['inventory', 'stockout', 'availability']
        },
        {
            'kpi_code': 'inventory.low_stock_count',
            'kpi_name': 'Low Stock Items',
            'category': 'Inventory',
            'description': 'Number of items below reorder point',
            'business_definition': 'Count of items where quantity < reorder_point AND quantity > 0',
            'formula_description': 'COUNT(items WHERE quantity < reorder_point AND quantity > 0)',
            'dataset_code': 'inventory_balances',
            'aggregation_type': 'COUNT',
            'unit_of_measure': 'count',
            'display_format': '#,##0',
            'target_direction': 'lower_is_better',
            'warning_threshold': 20,
            'critical_threshold': 50,
            'tags': ['inventory', 'low_stock', 'reorder']
        },
        {
            'kpi_code': 'procurement.total_spend',
            'kpi_name': 'Total Procurement Spend',
            'category': 'Procurement',
            'description': 'Total value of purchase orders',
            'business_definition': 'Sum of purchase order amounts',
            'formula_description': 'SUM(purchase_orders.total_amount)',
            'dataset_code': 'purchase_orders',
            'aggregation_type': 'SUM',
            'unit_of_measure': 'AED',
            'display_format': '#,##0',
            'target_direction': 'lower_is_better',
            'tags': ['procurement', 'spend', 'purchasing']
        },
        {
            'kpi_code': 'logistics.trips_completed',
            'kpi_name': 'Completed Trips',
            'category': 'Logistics',
            'description': 'Number of delivery trips completed',
            'business_definition': 'Count of trips with status Completed',
            'formula_description': 'COUNT(delivery_trips WHERE status = Completed)',
            'dataset_code': 'delivery_trips',
            'aggregation_type': 'COUNT',
            'unit_of_measure': 'count',
            'display_format': '#,##0',
            'target_direction': 'higher_is_better',
            'tags': ['logistics', 'delivery', 'trips']
        },
        {
            'kpi_code': 'logistics.on_time_rate',
            'kpi_name': 'On-Time Delivery Rate',
            'category': 'Logistics',
            'description': 'Percentage of deliveries on time',
            'business_definition': 'Deliveries on time divided by total deliveries',
            'formula_description': 'COUNT(deliveries WHERE arrival <= scheduled) / COUNT(deliveries) * 100',
            'dataset_code': 'delivery_trips',
            'aggregation_type': 'FORMULA',
            'unit_of_measure': 'percentage',
            'display_format': '0.0%',
            'target_direction': 'higher_is_better',
            'warning_threshold': 0.95,
            'critical_threshold': 0.9,
            'tags': ['logistics', 'delivery', 'performance']
        },
        {
            'kpi_code': 'hr.headcount',
            'kpi_name': 'Total Headcount',
            'category': 'HR',
            'description': 'Number of active employees',
            'business_definition': 'Count of employees with status Active',
            'formula_description': "COUNT(hr_employees WHERE status = 'Active')",
            'dataset_code': 'hr_employees',
            'aggregation_type': 'COUNT',
            'unit_of_measure': 'count',
            'display_format': '#,##0',
            'target_direction': 'higher_is_better',
            'tags': ['hr', 'headcount', 'workforce']
        },
        {
            'kpi_code': 'hr.attendance_rate',
            'kpi_name': 'Attendance Rate',
            'category': 'HR',
            'description': 'Percentage of employees present',
            'business_definition': 'Present employees divided by total employees',
            'formula_description': 'COUNT(present) / COUNT(total) * 100',
            'dataset_code': 'hr_attendance',
            'aggregation_type': 'FORMULA',
            'unit_of_measure': 'percentage',
            'display_format': '0.0%',
            'target_direction': 'higher_is_better',
            'warning_threshold': 0.95,
            'critical_threshold': 0.9,
            'tags': ['hr', 'attendance', 'performance']
        },
        {
            'kpi_code': 'finance.ar_balance',
            'kpi_name': 'Total Receivables',
            'category': 'Finance',
            'description': 'Outstanding customer balances',
            'business_definition': 'Sum of all customer outstanding balances',
            'formula_description': 'SUM(customers.outstanding_balance)',
            'dataset_code': 'sales_customers',
            'aggregation_type': 'SUM',
            'unit_of_measure': 'AED',
            'display_format': '#,##0',
            'target_direction': 'lower_is_better',
            'warning_threshold': 1.0,
            'critical_threshold': 1.2,
            'tags': ['finance', 'receivables', 'collections']
        },
    ]
    
    for kpi_data in kpis_data:
        existing = ReportingKPI.get_by_code(kpi_data['kpi_code'])
        if not existing:
            ReportingKPI.create(**kpi_data)
            print(f"  Created KPI: {kpi_data['kpi_name']}")
        else:
            print(f"  KPI exists: {kpi_data['kpi_name']}")


def seed_sample_reports(datasets):
    """Create sample saved reports."""
    print("Creating sample reports...")
    
    sales_ds = datasets.get('sales_orders')
    
    if not sales_ds:
        print("  Skipping reports - no sales dataset")
        return
    
    reports_data = [
        {
            'report_name': 'Monthly Sales Summary',
            'dataset_id': sales_ds,
            'report_type': 'tabular',
            'description': 'Monthly breakdown of sales by status and salesperson',
            'selected_fields': ['order_date', 'order_number', 'customer_name', 'salesperson_name', 'status', 'total_amount'],
            'filters_config': {},
            'grouping_config': [],
            'sorting_config': [{'field': 'order_date', 'direction': 'DESC'}],
            'status': 'active',
            'is_shared': True,
            'run_count': 45,
            'created_by_user_id': 1
        },
        {
            'report_name': 'Sales by Customer Type',
            'dataset_id': sales_ds,
            'report_type': 'summary',
            'description': 'Summary of sales grouped by customer type and market',
            'selected_fields': ['market', 'customer_name', 'total_amount'],
            'filters_config': {},
            'grouping_config': ['market', 'customer_name'],
            'sorting_config': [{'field': 'total_amount', 'direction': 'DESC'}],
            'status': 'active',
            'is_shared': True,
            'run_count': 23,
            'created_by_user_id': 1
        },
        {
            'report_name': 'Top Customers by Revenue',
            'dataset_id': sales_ds,
            'report_type': 'tabular',
            'description': 'Top 20 customers ranked by total revenue',
            'selected_fields': ['customer_name', 'order_number', 'order_date', 'total_amount'],
            'filters_config': {},
            'grouping_config': ['customer_name'],
            'sorting_config': [{'field': 'total_amount', 'direction': 'DESC'}],
            'row_limit': 20,
            'status': 'active',
            'is_shared': True,
            'run_count': 67,
            'created_by_user_id': 1
        },
    ]
    
    inv_ds = datasets.get('inventory_balances')
    if inv_ds:
        reports_data.append({
            'report_name': 'Inventory Stock Report',
            'dataset_id': inv_ds,
            'report_type': 'tabular',
            'description': 'Current inventory levels by warehouse',
            'selected_fields': ['item_code', 'item_name', 'warehouse_name', 'quantity', 'unit_cost', 'stock_value'],
            'filters_config': {},
            'grouping_config': ['warehouse_name'],
            'sorting_config': [{'field': 'stock_value', 'direction': 'DESC'}],
            'status': 'active',
            'is_shared': True,
            'run_count': 34,
            'created_by_user_id': 1
        })
    
    for report_data in reports_data:
        SavedReport.create(**report_data)
        print(f"  Created report: {report_data['report_name']}")


def seed_sample_queries(datasets):
    """Create sample ad-hoc queries."""
    print("Creating sample queries...")
    
    sales_ds = datasets.get('sales_orders')
    
    if sales_ds:
        AdhocQuery.create(
            query_name='All Orders This Month',
            dataset_id=sales_ds,
            sql_statement="SELECT * FROM sales_orders WHERE order_date >= date('now', 'start of month')",
            description='Quick view of all orders this month',
            is_shared=True,
            execution_count=15,
            created_by_user_id=1
        )
        print("  Created query: All Orders This Month")
        
        AdhocQuery.create(
            query_name='High Value Orders',
            dataset_id=sales_ds,
            sql_statement="SELECT order_number, customer_name, total_amount FROM sales_orders WHERE total_amount > 50000 ORDER BY total_amount DESC",
            description='Orders over 50,000 AED',
            is_shared=True,
            execution_count=8,
            created_by_user_id=1
        )
        print("  Created query: High Value Orders")
    
    hr_ds = datasets.get('hr_employees')
    if hr_ds:
        AdhocQuery.create(
            query_name='Active Employees by Department',
            dataset_id=hr_ds,
            sql_statement="SELECT department_name, COUNT(*) as emp_count FROM hr_employees WHERE status = 'Active' GROUP BY department_name ORDER BY emp_count DESC",
            description='Employee count by department',
            is_shared=True,
            execution_count=12,
            created_by_user_id=1
        )
        print("  Created query: Active Employees by Department")


def seed_sample_schedules(datasets):
    """Create sample report schedules."""
    print("Creating sample schedules...")
    
    reports = SavedReport.get_all(status='active')
    if not reports:
        print("  Skipping schedules - no active reports")
        return
    
    report_id = reports[0]['id'] if reports else None
    if not report_id:
        return
    
    ReportSchedule.create(
        schedule_name='Weekly Sales Report',
        report_id=report_id,
        frequency='weekly',
        run_time='09:00',
        day_of_week=1,
        output_formats=['excel'],
        delivery_method='email',
        recipient_emails=['manager@company.com', 'sales@company.com'],
        email_subject='Weekly Sales Report - {{ date }}',
        is_active=True,
        run_count=12,
        created_by_user_id=1
    )
    print("  Created schedule: Weekly Sales Report")
    
    ReportSchedule.create(
        schedule_name='Monthly Inventory Summary',
        report_id=report_id,
        frequency='monthly',
        run_time='08:00',
        day_of_month=1,
        output_formats=['excel', 'csv'],
        delivery_method='email',
        recipient_emails=['warehouse@company.com', 'manager@company.com'],
        email_subject='Monthly Inventory Summary',
        is_active=True,
        run_count=4,
        created_by_user_id=1
    )
    print("  Created schedule: Monthly Inventory Summary")


def seed_sample_logs():
    """Create sample access and query logs."""
    print("Creating sample logs...")
    
    for i in range(10):
        ReportAccessLog.create(
            report_id=1,
            report_name='Monthly Sales Summary',
            accessed_by_user_id=1,
            access_type='view',
            ip_address='192.168.1.100'
        )
    
    QueryLog.create(
        query_name='Quick Sales Query',
        executed_by_user_id=1,
        sql_statement='SELECT * FROM sales_orders LIMIT 100',
        result_row_count=100,
        execution_time_ms=45,
        status='completed',
        client_ip='192.168.1.100'
    )
    print("  Created sample access and query logs")


def main():
    """Main seed function."""
    print("=" * 60)
    print("Advanced Reporting / BI - Seed Data Generator")
    print("=" * 60)
    
    print("\nInitializing BI tables...")
    initialize_reporting_tables()
    
    print("\nSeeding datasets...")
    datasets = seed_datasets()
    
    print("\nSeeding dataset fields...")
    seed_dataset_fields(datasets)
    
    print("\nSeeding KPIs...")
    seed_kpis()
    
    print("\nSeeding sample reports...")
    seed_sample_reports(datasets)
    
    print("\nSeeding sample queries...")
    seed_sample_queries(datasets)
    
    print("\nSeeding sample schedules...")
    seed_sample_schedules(datasets)
    
    print("\nSeeding sample logs...")
    seed_sample_logs()
    
    print("\n" + "=" * 60)
    print("BI Seed Data Complete!")
    print("=" * 60)
    
    print(f"\nSummary:")
    print(f"  Datasets: {len(ReportingDataset.get_all())}")
    print(f"  KPIs: {len(ReportingKPI.get_all())}")
    print(f"  Reports: {len(SavedReport.get_all())}")
    print(f"  Schedules: {len(ReportSchedule.get_all())}")
    print(f"  Queries: {len(AdhocQuery.get_all(user_id=1))}")


if __name__ == '__main__':
    main()
