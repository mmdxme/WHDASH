"""
Unified Reporting Framework
========================
Centralized reporting and analytics for the MMDx platform.

This module provides:
- Standardized KPI calculations
- Cross-module report builders
- Common filters and date range handling
- Export functionality (Excel, CSV, PDF)
- Dashboard widget framework
- Saved views

USAGE:
    from reporting import (
        get_dashboard_stats,
        build_sales_report,
        build_inventory_report,
        export_to_excel
    )
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from database import get_db_context, get_one, get_all, row_to_dict
from functools import reduce

# ============================================================================
# COMMON FILTER BUILDERS
# ============================================================================

def build_date_filter(date_from: str, date_to: str, date_field: str = 'created_at') -> tuple:
    """
    Build SQL date filter clause and parameters.
    
    Args:
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        date_field: Date column name
    
    Returns:
        (where_clause, params)
    """
    clauses = []
    params = []
    
    if date_from:
        clauses.append(f"{date_field} >= ?")
        params.append(date_from)
    
    if date_to:
        clauses.append(f"{date_field} <= ?")
        params.append(f"{date_to} 23:59:59")
    
    if clauses:
        return (" AND ".join(clauses), params)
    return ("", [])


def build_company_filter(company_id: int, tables_alias: str = '') -> tuple:
    """Build company filter if applicable."""
    if not company_id:
        return ("", [])
    
    prefix = f"{tables_alias}." if tables_alias else ""
    return (f"{prefix}company_id = ?", [company_id])


def build_status_filter(status: str, status_field: str = 'status') -> tuple:
    """Build status filter."""
    if not status:
        return ("", [])
    return (f"{status_field} = ?", [status])


def build_search_filter(search: str, fields: List[str], prefix: str = '') -> tuple:
    """Build search filter across multiple fields."""
    if not search:
        return ("", [])
    
    prefix = f"{prefix}." if prefix else ""
    clauses = [f"{prefix}{f} LIKE ?" for f in fields]
    search_param = f"%{search}%"
    return (f"({' OR '.join(clauses)})", [search_param] * len(fields))


# ============================================================================
# DASHBOARD STATISTICS
# ============================================================================

def get_dashboard_stats(user_id: int = None, company_id: int = None) -> Dict[str, Any]:
    """
    Get unified dashboard statistics for the platform.
    
    This replaces module-specific dashboard queries with a single,
    authoritative source of truth for KPIs.
    
    Returns:
        Dict with all dashboard metrics
    """
    stats = {
        'timestamp': datetime.now().isoformat(),
        'date_range': {
            'today': datetime.now().strftime('%Y-%m-%d'),
            'month_start': datetime.now().replace(day=1).strftime('%Y-%m-%d'),
            'year_start': datetime.now().replace(month=1, day=1).strftime('%Y-%m-%d'),
        },
        'hr': {},
        'inventory': {},
        'sales': {},
        'logistics': {},
        'planning': {},
        'marketing': {},
        'tasks': {},
    }
    
    with get_db_context() as db:
        # HR Stats
        stats['hr'] = {
            'total_employees': _safe_int(db.execute(
                "SELECT COUNT(*) FROM hr_employees WHERE status = 'Active'"
            ).fetchone()[0]),
            'present_today': _safe_int(db.execute(
                """SELECT COUNT(*) FROM hr_attendance_records 
                   WHERE date = ? AND status = 'Present'""",
                (datetime.now().strftime('%Y-%m-%d'),)
            ).fetchone()[0]),
            'on_leave_today': _safe_int(db.execute(
                """SELECT COUNT(*) FROM hr_leave_requests 
                   WHERE status = 'Approved' 
                   AND start_date <= ? AND end_date >= ?""",
                (datetime.now().strftime('%Y-%m-%d'),) * 2
            ).fetchone()[0]),
            'pending_leave_requests': _safe_int(db.execute(
                "SELECT COUNT(*) FROM hr_leave_requests WHERE status = 'Pending'"
            ).fetchone()[0]),
        }
        
        # Inventory Stats
        inv_stats = db.execute("""
            SELECT 
                COUNT(DISTINCT item_id) as total_items,
                SUM(quantity) as total_stock,
                SUM(CASE WHEN quantity <= 0 THEN 1 ELSE 0 END) as out_of_stock,
                SUM(CASE WHEN quantity < reorder_point THEN 1 ELSE 0 END) as low_stock
            FROM wms_inventory_balances ib
            JOIN wms_items i ON ib.item_id = i.id
            WHERE i.is_active = 1
        """).fetchone()
        
        stats['inventory'] = {
            'total_items': _safe_int(inv_stats['total_items']),
            'total_stock_value': _safe_float(inv_stats['total_stock']),
            'out_of_stock_items': _safe_int(inv_stats['out_of_stock']),
            'low_stock_items': _safe_int(inv_stats['low_stock']),
        }
        
        # Sales Stats (from customer_transactions)
        sales_stats = db.execute("""
            SELECT 
                COUNT(*) as total_transactions,
                SUM(CASE WHEN type = 'Invoice' THEN amount ELSE 0 END) as total_sales,
                SUM(CASE WHEN type = 'Payment' THEN amount ELSE 0 END) as total_payments
            FROM customer_transactions
            WHERE transaction_date >= ?
        """, (datetime.now().replace(day=1).strftime('%Y-%m-%d'),)).fetchone()
        
        stats['sales'] = {
            'month_transactions': _safe_int(sales_stats['total_transactions']),
            'month_sales': _safe_float(sales_stats['total_sales']),
            'month_payments': _safe_float(sales_stats['total_payments']),
            'outstanding': _safe_float(db.execute(
                "SELECT COALESCE(SUM(total_debt), 0) FROM sdad_customers"
            ).fetchone()[0]),
        }
        
        # Logistics Stats
        trip_stats = db.execute("""
            SELECT 
                COUNT(*) as total_trips,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'In Transit' THEN 1 ELSE 0 END) as in_transit
            FROM delivery_trips
            WHERE date = ?
        """, (datetime.now().strftime('%Y-%m-%d'),)).fetchone()
        
        stats['logistics'] = {
            'trips_today': _safe_int(trip_stats['total_trips']),
            'completed_today': _safe_int(trip_stats['completed']),
            'in_transit': _safe_int(trip_stats['in_transit']),
            'total_deliveries': _safe_int(db.execute(
                """SELECT COUNT(*) FROM delivery_stops ds
                   JOIN delivery_trips dt ON ds.trip_id = dt.id
                   WHERE DATE(dt.date) = ? AND ds.status = 'Completed'""",
                (datetime.now().strftime('%Y-%m-%d'),)
            ).fetchone()[0]),
        }
        
        # Task Stats
        task_stats = db.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) as open_tasks,
                SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN due_at < ? AND status NOT IN ('Completed', 'Canceled') THEN 1 ELSE 0 END) as overdue
            FROM task_items
        """, (datetime.now().strftime('%Y-%m-%d'),)).fetchone()
        
        stats['tasks'] = {
            'total_tasks': _safe_int(task_stats['total']),
            'open_tasks': _safe_int(task_stats['open_tasks']),
            'in_progress_tasks': _safe_int(task_stats['in_progress']),
            'completed_tasks': _safe_int(task_stats['completed']),
            'overdue_tasks': _safe_int(task_stats['overdue']),
        }
        
        # Marketing Stats
        campaign_stats = db.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed
            FROM marketing_campaigns
        """).fetchone()
        
        lead_stats = db.execute("""
            SELECT COUNT(*) FROM marketing_leads WHERE lead_status = 'New'
        """).fetchone()
        
        stats['marketing'] = {
            'total_campaigns': _safe_int(campaign_stats['total']),
            'active_campaigns': _safe_int(campaign_stats['active']),
            'new_leads': _safe_int(lead_stats[0]),
        }
        
        # Planning Stats
        alert_stats = db.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical,
                SUM(CASE WHEN severity = 'HIGH' THEN 1 ELSE 0 END) as high
            FROM planning_alerts
            WHERE is_acknowledged = 0
        """).fetchone()
        
        stats['planning'] = {
            'active_alerts': _safe_int(alert_stats['total']),
            'critical_alerts': _safe_int(alert_stats['critical']),
            'high_alerts': _safe_int(alert_stats['high']),
        }
    
    return stats


def _safe_int(value) -> int:
    """Safely convert to int."""
    try:
        return int(value) if value is not None else 0
    except (ValueError, TypeError):
        return 0


def _safe_float(value) -> float:
    """Safely convert to float."""
    try:
        return float(value) if value is not None else 0.0
    except (ValueError, TypeError):
        return 0.0


# ============================================================================
# INVENTORY REPORTS
# ============================================================================

def build_inventory_report(filters: Dict = None) -> Dict[str, Any]:
    """
    Build a comprehensive inventory report.
    
    Args:
        filters: Dict with optional keys:
            - warehouse_id: Filter by warehouse
            - category_id: Filter by category
            - brand_id: Filter by brand
            - stock_status: 'all', 'low', 'out', 'normal'
            - date_from, date_to: Date range
    
    Returns:
        Dict with report data and metadata
    """
    filters = filters or {}
    
    where_clauses = ["i.is_active = 1"]
    params = []
    
    if filters.get('warehouse_id'):
        where_clauses.append("ib.warehouse_id = ?")
        params.append(filters['warehouse_id'])
    
    if filters.get('category_id'):
        where_clauses.append("i.category_id = ?")
        params.append(filters['category_id'])
    
    if filters.get('brand_id'):
        where_clauses.append("i.brand_id = ?")
        params.append(filters['brand_id'])
    
    stock_status = filters.get('stock_status', 'all')
    if stock_status == 'low':
        where_clauses.append("ib.quantity < ib.reorder_point AND ib.quantity > 0")
    elif stock_status == 'out':
        where_clauses.append("ib.quantity <= 0")
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    with get_db_context() as db:
        items = db.execute(f"""
            SELECT 
                i.id, i.item_code, i.name,
                c.name as category_name,
                b.name as brand_name,
                ib.quantity,
                ib.reserved,
                ib.allocated,
                ib.reorder_point,
                ib.safety_stock,
                (ib.quantity - ib.reserved - ib.allocated) as available_stock,
                CASE 
                    WHEN ib.quantity <= 0 THEN 'Out of Stock'
                    WHEN ib.quantity < ib.reorder_point THEN 'Low Stock'
                    ELSE 'In Stock'
                END as stock_status,
                COALESCE(i.unit_cost, 0) as unit_cost,
                COALESCE(i.unit_cost, 0) * ib.quantity as total_value
            FROM wms_items i
            LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
            LEFT JOIN wms_item_categories c ON i.category_id = c.id
            LEFT JOIN wms_item_brands b ON i.brand_id = b.id
            WHERE {where_sql}
            ORDER BY i.name
        """, params).fetchall()
        
        # Calculate summary
        summary = {
            'total_items': len(items),
            'in_stock': sum(1 for i in items if i['quantity'] > 0),
            'low_stock': sum(1 for i in items if 0 < i['quantity'] < i['reorder_point']),
            'out_of_stock': sum(1 for i in items if i['quantity'] <= 0),
            'total_value': sum(i['total_value'] or 0 for i in items),
            'total_quantity': sum(i['quantity'] or 0 for i in items),
        }
        
        return {
            'report_type': 'inventory',
            'generated_at': datetime.now().isoformat(),
            'filters': filters,
            'summary': summary,
            'items': [dict(i) for i in items],
        }


def build_stock_movement_report(filters: Dict = None) -> Dict[str, Any]:
    """Build a stock movement report."""
    filters = filters or {}
    
    date_filter, date_params = build_date_filter(
        filters.get('date_from'),
        filters.get('date_to'),
        'ml.created_at'
    )
    
    with get_db_context() as db:
        movements = db.execute(f"""
            SELECT 
                ml.id, ml.transaction_type, ml.quantity_moved,
                ml.reference, ml.notes, ml.created_at,
                i.item_code, i.name as item_name,
                w.name as warehouse_name,
                u.username as performed_by
            FROM wms_inventory_ledger ml
            JOIN wms_items i ON ml.item_id = i.id
            LEFT JOIN wms_warehouses w ON ml.warehouse_id = w.id
            LEFT JOIN users u ON ml.performed_by_user_id = u.id
            WHERE 1=1 {date_filter}
            ORDER BY ml.created_at DESC
            LIMIT 1000
        """, date_params).fetchall()
        
        return {
            'report_type': 'stock_movements',
            'generated_at': datetime.now().isoformat(),
            'filters': filters,
            'movements': [dict(m) for m in movements],
        }


# ============================================================================
# SALES REPORTS
# ============================================================================

def build_sales_report(filters: Dict = None) -> Dict[str, Any]:
    """
    Build a sales performance report.
    
    Args:
        filters: Dict with optional keys:
            - date_from, date_to: Date range
            - customer_id: Filter by customer
            - salesperson_id: Filter by salesperson
            - company_id: Filter by company
    """
    filters = filters or {}
    
    where_clauses = ["1=1"]
    params = []
    
    if filters.get('date_from'):
        where_clauses.append("ct.transaction_date >= ?")
        params.append(filters['date_from'])
    
    if filters.get('date_to'):
        where_clauses.append("ct.transaction_date <= ?")
        params.append(filters['date_to'])
    
    if filters.get('customer_id'):
        where_clauses.append("ct.customer_id = ?")
        params.append(filters['customer_id'])
    
    where_sql = " AND ".join(where_clauses)
    
    with get_db_context() as db:
        transactions = db.execute(f"""
            SELECT 
                ct.id, ct.transaction_date, ct.type, ct.amount,
                ct.reference, ct.notes,
                c.name as customer_name,
                u.username as salesperson_name
            FROM customer_transactions ct
            LEFT JOIN customers c ON ct.customer_id = c.id
            LEFT JOIN users u ON c.salesperson_id = u.id
            WHERE {where_sql}
            ORDER BY ct.transaction_date DESC
        """, params).fetchall()
        
        # Summary by type
        by_type = {}
        for tx in transactions:
            tx_type = tx['type']
            if tx_type not in by_type:
                by_type[tx_type] = {'count': 0, 'total': 0}
            by_type[tx_type]['count'] += 1
            by_type[tx_type]['total'] += tx['amount'] or 0
        
        return {
            'report_type': 'sales',
            'generated_at': datetime.now().isoformat(),
            'filters': filters,
            'summary': {
                'total_transactions': len(transactions),
                'total_amount': sum(t['amount'] or 0 for t in transactions),
                'by_type': by_type,
            },
            'transactions': [dict(t) for t in transactions],
        }


def build_customer_summary_report() -> Dict[str, Any]:
    """Build a summary report of all customers."""
    with get_db_context() as db:
        customers = db.execute("""
            SELECT 
                c.id, c.name, c.phone, c.location, c.type,
                c.credit_limit, c.balance,
                sc.total_orders, sc.total_debt, sc.total_payments,
                sc.last_purchase_date, sc.salesperson_name
            FROM customers c
            LEFT JOIN sdad_customers sc ON c.id = sc.id
            ORDER BY sc.total_orders DESC
            LIMIT 1000
        """).fetchall()
        
        return {
            'report_type': 'customer_summary',
            'generated_at': datetime.now().isoformat(),
            'total_customers': len(customers),
            'total_outstanding': sum(c['total_debt'] or 0 for c in customers),
            'total_credit_limit': sum(c['credit_limit'] or 0 for c in customers),
            'customers': [dict(c) for c in customers],
        }


# ============================================================================
# HR REPORTS
# ============================================================================

def build_hr_attendance_report(month: int, year: int) -> Dict[str, Any]:
    """Build HR attendance report for a month."""
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"
    
    with get_db_context() as db:
        records = db.execute("""
            SELECT 
                e.id, e.employee_code, e.first_name, e.last_name,
                d.name as department_name,
                ar.date, ar.check_in, ar.check_out, ar.status,
                ar.work_hours, ar.overtime_hours, ar.late_minutes
            FROM hr_attendance_records ar
            JOIN hr_employees e ON ar.employee_id = e.id
            LEFT JOIN hr_departments d ON e.department_id = d.id
            WHERE ar.date >= ? AND ar.date < ?
            ORDER BY e.last_name, ar.date
        """, (start_date, end_date)).fetchall()
        
        # Summary by employee
        by_employee = {}
        for r in records:
            emp_id = r['id']
            if emp_id not in by_employee:
                by_employee[emp_id] = {
                    'name': f"{r['first_name']} {r['last_name']}",
                    'code': r['employee_code'],
                    'department': r['department_name'],
                    'present': 0, 'absent': 0, 'late': 0,
                    'total_hours': 0, 'total_overtime': 0
                }
            
            by_employee[emp_id][r['status'].lower().replace(' ', '_')] = by_employee[emp_id].get(r['status'].lower().replace(' ', '_'), 0) + 1
            by_employee[emp_id]['total_hours'] += r['work_hours'] or 0
            by_employee[emp_id]['total_overtime'] += r['overtime_hours'] or 0
        
        return {
            'report_type': 'hr_attendance',
            'generated_at': datetime.now().isoformat(),
            'period': {'month': month, 'year': year},
            'summary': {
                'total_records': len(records),
                'employees': len(by_employee),
            },
            'records': [dict(r) for r in records],
            'by_employee': by_employee,
        }


def build_hr_leave_report(year: int) -> Dict[str, Any]:
    """Build HR leave summary report for a year."""
    with get_db_context() as db:
        leaves = db.execute("""
            SELECT 
                lr.id, lr.start_date, lr.end_date, lr.total_days,
                lr.status, lr.reason,
                e.first_name, e.last_name, e.employee_code,
                lt.name as leave_type_name, lt.is_paid
            FROM hr_leave_requests lr
            JOIN hr_employees e ON lr.employee_id = e.id
            JOIN hr_leave_types lt ON lr.leave_type_id = lt.id
            WHERE strftime('%Y', lr.start_date) = ?
            ORDER BY lr.start_date DESC
        """, (str(year),)).fetchall()
        
        return {
            'report_type': 'hr_leave',
            'generated_at': datetime.now().isoformat(),
            'year': year,
            'total_requests': len(leaves),
            'approved': sum(1 for l in leaves if l['status'] == 'Approved'),
            'pending': sum(1 for l in leaves if l['status'] == 'Pending'),
            'leaves': [dict(l) for l in leaves],
        }


# ============================================================================
# LOGISTICS REPORTS
# ============================================================================

def build_delivery_report(date_from: str = None, date_to: str = None) -> Dict[str, Any]:
    """Build delivery performance report."""
    if not date_from:
        date_from = datetime.now().strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.now().strftime('%Y-%m-%d')
    
    with get_db_context() as db:
        trips = db.execute("""
            SELECT 
                dt.id, dt.date, dt.status, dt.driver_id,
                u.username as driver_name,
                v.name as vehicle_name, v.plate_number,
                COUNT(ds.id) as total_stops,
                SUM(CASE WHEN ds.status = 'Completed' THEN 1 ELSE 0 END) as completed_stops,
                SUM(CASE WHEN ds.status = 'Pending' THEN 1 ELSE 0 END) as pending_stops,
                MIN(ds.arrival_time) as first_arrival,
                MAX(ds.departure_time) as last_departure
            FROM delivery_trips dt
            LEFT JOIN users u ON dt.driver_id = u.id
            LEFT JOIN vehicles v ON dt.vehicle_id = v.id
            LEFT JOIN delivery_stops ds ON dt.id = ds.trip_id
            WHERE dt.date BETWEEN ? AND ?
            GROUP BY dt.id
            ORDER BY dt.date DESC
        """, (date_from, date_to)).fetchall()
        
        return {
            'report_type': 'delivery',
            'generated_at': datetime.now().isoformat(),
            'period': {'from': date_from, 'to': date_to},
            'summary': {
                'total_trips': len(trips),
                'completed': sum(1 for t in trips if t['status'] == 'Completed'),
                'in_transit': sum(1 for t in trips if t['status'] == 'In Transit'),
            },
            'trips': [dict(t) for t in trips],
        }


# ============================================================================
# PLANNING REPORTS
# ============================================================================

def build_planning_alerts_report() -> Dict[str, Any]:
    """Build planning alerts summary."""
    with get_db_context() as db:
        alerts = db.execute("""
            SELECT 
                pa.*, i.item_code, i.name as item_name,
                w.name as warehouse_name
            FROM planning_alerts pa
            LEFT JOIN wms_items i ON pa.item_id = i.id
            LEFT JOIN wms_warehouses w ON pa.warehouse_id = w.id
            WHERE pa.is_acknowledged = 0
            ORDER BY 
                CASE pa.severity 
                    WHEN 'CRITICAL' THEN 1 
                    WHEN 'HIGH' THEN 2 
                    WHEN 'MEDIUM' THEN 3 
                    ELSE 4 
                END,
                pa.created_at DESC
        """).fetchall()
        
        by_severity = {}
        by_type = {}
        for a in alerts:
            sev = a['severity']
            atype = a['alert_type']
            by_severity[sev] = by_severity.get(sev, 0) + 1
            by_type[atype] = by_type.get(atype, 0) + 1
        
        return {
            'report_type': 'planning_alerts',
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_alerts': len(alerts),
                'by_severity': by_severity,
                'by_type': by_type,
            },
            'alerts': [dict(a) for a in alerts],
        }


# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

def export_to_excel(data: List[Dict], columns: List[str], filename: str) -> bytes:
    """
    Export data to Excel format.
    
    Args:
        data: List of dictionaries
        columns: List of column keys to include
        filename: Output filename
    
    Returns:
        Excel file bytes
    """
    from openpyxl import Workbook
    from io import BytesIO
    
    wb = Workbook()
    ws = wb.active
    ws.title = filename[:31]  # Sheet name max 31 chars
    
    # Header row
    ws.append(columns)
    
    # Data rows
    for row in data:
        ws.append([row.get(col) for col in columns])
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()


def export_to_csv(data: List[Dict], columns: List[str]) -> str:
    """
    Export data to CSV format.
    
    Args:
        data: List of dictionaries
        columns: List of column keys to include
    
    Returns:
        CSV string
    """
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    
    for row in data:
        writer.writerow({col: row.get(col) for col in columns})
    
    return output.getvalue()


# ============================================================================
# REPORT SCHEDULING (for future implementation)
# ============================================================================

def save_report_snapshot(name: str, report_type: str, filters: Dict, data: List[Dict]):
    """Save a report snapshot for later retrieval."""
    import json
    
    with get_db_context() as db:
        db.execute("""
            INSERT INTO report_snapshots (name, report_type, filters_json, data_json, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (name, report_type, json.dumps(filters), json.dumps(data)))
        db.commit()


def get_report_snapshots(report_type: str = None) -> List[Dict]:
    """Get saved report snapshots."""
    sql = "SELECT * FROM report_snapshots"
    params = []
    
    if report_type:
        sql += " WHERE report_type = ?"
        params.append(report_type)
    
    sql += " ORDER BY created_at DESC"
    return get_all(sql, params)


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_reporting():
    """Initialize reporting tables."""
    with get_db_context() as db:
        # Report snapshots table
        db.execute("""
            CREATE TABLE IF NOT EXISTS report_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                report_type TEXT NOT NULL,
                filters_json TEXT,
                data_json TEXT,
                created_by_user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Saved reports table
        db.execute("""
            CREATE TABLE IF NOT EXISTS saved_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                report_type TEXT NOT NULL,
                filters_json TEXT,
                columns_json TEXT,
                is_shared INTEGER DEFAULT 0,
                created_by_user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        db.commit()
