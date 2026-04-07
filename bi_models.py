"""
Business Intelligence Models - Management Dashboard Data Layer
============================================================
Centralized data access for all executive dashboards and management reports.

This module provides:
- Single source of truth for all KPIs
- Cross-module data consolidation
- Company/branch/warehouse rollups
- Holding-level consolidated views
- Time intelligence (MoM, QoQ, YoY, YTD)
- Alert and exception detection
- Drill-down support

KEY PRINCIPLES:
- All metrics traceable to source
- No duplicate KPI calculations
- Centralized aggregation logic
- Configurable intercompany elimination
- Role-based data visibility

Usage:
    from bi_models import (
        get_executive_dashboard_data,
        get_company_performance,
        get_inventory_kpis,
        get_sales_performance,
        get_logistics_metrics,
        get_procurement_summary,
        get_hr_workforce,
        get_marketing_kpis,
        get_alerts_and_exceptions,
        get_consolidated_holding_view
    )

IMPORTANT:
- All amounts in system currency (AED) unless specified
- All quantities as integers
- Dates in ISO format (YYYY-MM-DD)
- Percentages as decimals (0.15 = 15%)
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager

# Database path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'warehouse.db'))


# =============================================================================
# DATABASE CONNECTION HELPERS
# =============================================================================

def get_bi_db():
    """Get a database connection with Row factory for BI queries."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


@contextmanager
def bi_db_context():
    """Context manager for BI database operations."""
    db = get_bi_db()
    try:
        yield db
    finally:
        db.close()


def row_to_dict(row):
    """Convert sqlite3.Row to dictionary."""
    return dict(row) if row else None


def rows_to_list(rows):
    """Convert list of sqlite3.Row to list of dictionaries."""
    return [dict(row) for row in rows] if rows else []


# =============================================================================
# DATE/TIME INTELLIGENCE HELPERS
# =============================================================================

def get_date_range(period: str) -> Tuple[str, str]:
    """
    Get date range for common time periods.
    
    Args:
        period: 'today', 'yesterday', 'this_week', 'last_week', 
                'this_month', 'last_month', 'this_quarter', 'last_quarter',
                'this_year', 'ytd', 'last_ytd', 'last_12_months'
    
    Returns:
        (date_from, date_to) in YYYY-MM-DD format
    """
    today = datetime.now().date()
    
    if period == 'today':
        return (today.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
    elif period == 'yesterday':
        yesterday = today - timedelta(days=1)
        return (yesterday.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d'))
    elif period == 'this_week':
        start = today - timedelta(days=today.weekday())
        return (start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
    elif period == 'last_week':
        start = today - timedelta(days=today.weekday() + 7)
        end = start + timedelta(days=6)
        return (start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
    elif period == 'this_month':
        start = today.replace(day=1)
        return (start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
    elif period == 'last_month':
        first_this_month = today.replace(day=1)
        end = first_this_month - timedelta(days=1)
        start = end.replace(day=1)
        return (start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
    elif period == 'this_quarter':
        quarter = (today.month - 1) // 3
        start_month = quarter * 3 + 1
        start = today.replace(month=start_month, day=1)
        return (start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
    elif period == 'last_quarter':
        quarter = (today.month - 1) // 3
        if quarter == 0:
            start = today.replace(year=today.year - 1, month=10, day=1)
            end = start.replace(month=12, day=31)
        else:
            prev_quarter = quarter - 1
            start_month = prev_quarter * 3 + 1
            start = today.replace(month=start_month, day=1)
            end = start.replace(month=start_month + 2, day=1) + timedelta(days=31)
            end = end.replace(day=1) - timedelta(days=1)
        return (start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
    elif period == 'this_year':
        start = today.replace(month=1, day=1)
        return (start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
    elif period == 'ytd':
        start = today.replace(month=1, day=1)
        return (start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
    elif period == 'last_ytd':
        start = today.replace(month=1, day=1, year=today.year - 1)
        end = today.replace(month=1, day=1) - timedelta(days=1)
        return (start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
    elif period == 'last_12_months':
        start = today - timedelta(days=365)
        return (start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
    else:
        # Default to this month
        start = today.replace(day=1)
        return (start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))


def get_previous_period_dates(date_from: str, date_to: str) -> Tuple[str, str]:
    """
    Get equivalent previous period dates for comparison.
    Maintains same day count and day-of-week pattern.
    """
    from_dt = datetime.strptime(date_from, '%Y-%m-%d')
    to_dt = datetime.strptime(date_to, '%Y-%m-%d')
    
    days_diff = (to_dt - from_dt).days + 1
    
    prev_to = from_dt - timedelta(days=1)
    prev_from = prev_to - timedelta(days=days_diff - 1)
    
    return (prev_from.strftime('%Y-%m-%d'), prev_to.strftime('%Y-%m-%d'))


# =============================================================================
# MASTER DATA HELPERS
# =============================================================================

def get_all_companies_for_bi(include_inactive: bool = False) -> List[Dict]:
    """Get all companies for BI queries."""
    with bi_db_context() as db:
        rows = db.execute("""
            SELECT c.*, cp.company_type, cp.short_name
            FROM companies c
            LEFT JOIN company_profiles cp ON c.id = cp.company_id
            ORDER BY c.name
        """).fetchall()
        return rows_to_list(rows)


def get_all_warehouses_for_bi(company_id: int = None) -> List[Dict]:
    """Get all warehouses, optionally filtered by company."""
    with bi_db_context() as db:
        if company_id:
            rows = db.execute("""
                SELECT w.*, c.name as company_name
                FROM warehouses w
                JOIN companies c ON w.company_id = c.id
                WHERE w.company_id = ?
                ORDER BY c.name, w.name
            """, (company_id,)).fetchall()
        else:
            rows = db.execute("""
                SELECT w.*, c.name as company_name
                FROM warehouses w
                JOIN companies c ON w.company_id = c.id
                ORDER BY c.name, w.name
            """).fetchall()
        return rows_to_list(rows)


def get_all_salespersons() -> List[Dict]:
    """Get all users with sales permissions."""
    with bi_db_context() as db:
        rows = db.execute("""
            SELECT DISTINCT u.id, u.username, u.email
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE r.role_name LIKE '%Sales%' OR r.role_name LIKE '%sales%'
               OR r.role_name LIKE '%Account%'
            ORDER BY u.username
        """).fetchall()
        return rows_to_list(rows)


# =============================================================================
# SALES KPIs
# =============================================================================

def get_sales_kpis(company_id: int = None, date_from: str = None, date_to: str = None,
                   include_intercompany: bool = False) -> Dict[str, Any]:
    """
    Get comprehensive sales KPIs.
    
    Args:
        company_id: Filter by specific company (None = all companies)
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        include_intercompany: Whether to include intercompany transactions
    
    Returns:
        Dictionary with all sales KPIs and breakdowns
    """
    if not date_from or not date_to:
        date_from, date_to = get_date_range('this_month')
    
    with bi_db_context() as db:
        # Build WHERE clause
        where_clauses = ["so.order_date >= ?", "so.order_date <= ?"]
        params = [date_from, date_to]
        
        if company_id:
            where_clauses.append("so.company_id = ?")
            params.append(company_id)
        
        # Exclude intercompany if requested
        if not include_intercompany:
            where_clauses.append("""
                so.customer_id NOT IN (
                    SELECT related_company_id FROM company_relationships 
                    WHERE company_id = so.company_id AND relationship_type = 'intercompany'
                )
            """)
        
        where_sql = " AND ".join(where_clauses)
        
        # Total sales
        total_result = db.execute(f"""
            SELECT 
                COUNT(DISTINCT so.id) as order_count,
                COALESCE(SUM(so.total_amount), 0) as total_sales,
                COALESCE(SUM(so.subtotal), 0) as net_sales,
                COALESCE(SUM(so.discount_amount), 0) as total_discounts,
                COALESCE(AVG(so.total_amount), 0) as avg_order_value,
                COUNT(DISTINCT so.customer_id) as customer_count
            FROM sales_orders so
            WHERE {where_sql}
        """, params).fetchone()
        
        # Sales by status
        by_status = db.execute(f"""
            SELECT 
                so.status,
                COUNT(*) as count,
                COALESCE(SUM(so.total_amount), 0) as amount
            FROM sales_orders so
            WHERE {where_sql}
            GROUP BY so.status
        """, params).fetchall()
        
        # Sales by market (local/export)
        by_market = db.execute(f"""
            SELECT 
                COALESCE(so.market, 'Local') as market,
                COUNT(*) as order_count,
                COALESCE(SUM(so.total_amount), 0) as amount
            FROM sales_orders so
            WHERE {where_sql}
            GROUP BY so.market
        """, params).fetchall()
        
        # Sales by salesperson (top 10)
        by_salesperson = db.execute(f"""
            SELECT 
                u.username as salesperson,
                COUNT(DISTINCT so.id) as order_count,
                COALESCE(SUM(so.total_amount), 0) as amount,
                COUNT(DISTINCT so.customer_id) as customers
            FROM sales_orders so
            LEFT JOIN users u ON so.assigned_salesperson_id = u.id
            WHERE {where_sql}
            GROUP BY so.assigned_salesperson_id
            ORDER BY amount DESC
            LIMIT 10
        """, params).fetchall()
        
        # Top customers
        top_customers = db.execute(f"""
            SELECT 
                sc.name as customer,
                sc.location,
                COUNT(DISTINCT so.id) as order_count,
                COALESCE(SUM(so.total_amount), 0) as amount
            FROM sales_orders so
            JOIN sales_customers sc ON so.customer_id = sc.id
            WHERE {where_sql}
            GROUP BY so.customer_id
            ORDER BY amount DESC
            LIMIT 10
        """, params).fetchall()
        
        # Comparison period
        prev_from, prev_to = get_previous_period_dates(date_from, date_to)
        prev_params = [prev_from, prev_to] + params[2:]
        
        prev_result = db.execute(f"""
            SELECT 
                COUNT(DISTINCT so.id) as order_count,
                COALESCE(SUM(so.total_amount), 0) as total_sales
            FROM sales_orders so
            WHERE so.order_date >= ? AND so.order_date <= ?
            {'AND so.company_id = ?' if company_id else ''}
        """, prev_params).fetchone()
        
        # Calculate trends
        current_sales = float(total_result['total_sales'] or 0)
        prev_sales = float(prev_result['total_sales'] or 0) if prev_result else 0
        sales_change = ((current_sales - prev_sales) / prev_sales * 100) if prev_sales > 0 else 0
        
        current_orders = int(total_result['order_count'] or 0)
        prev_orders = int(prev_result['order_count'] or 0) if prev_result else 0
        orders_change = ((current_orders - prev_orders) / prev_orders * 100) if prev_orders > 0 else 0
        
        return {
            'period': {'from': date_from, 'to': date_to},
            'previous_period': {'from': prev_from, 'to': prev_to},
            'total_orders': current_orders,
            'total_sales': current_sales,
            'net_sales': float(total_result['net_sales'] or 0),
            'total_discounts': float(total_result['total_discounts'] or 0),
            'avg_order_value': float(total_result['avg_order_value'] or 0),
            'unique_customers': int(total_result['customer_count'] or 0),
            'sales_change_pct': round(sales_change, 1),
            'orders_change_pct': round(orders_change, 1),
            'by_status': {r['status']: {'count': r['count'], 'amount': r['amount']} for r in by_status},
            'by_market': {r['market']: {'count': r['order_count'], 'amount': r['amount']} for r in by_market},
            'by_salesperson': rows_to_list(by_salesperson),
            'top_customers': rows_to_list(top_customers),
            'currency': 'AED'
        }


def get_inquiry_to_order_funnel(date_from: str = None, date_to: str = None,
                                 company_id: int = None) -> Dict[str, Any]:
    """
    Get inquiry-to-order conversion funnel.
    Shows: Inquiries -> Quotations -> Orders -> Deliveries
    """
    if not date_from or not date_to:
        date_from, date_to = get_date_range('this_month')
    
    with bi_db_context() as db:
        where_clauses = ["si.inquiry_date >= ?", "si.inquiry_date <= ?"]
        params = [date_from, date_to]
        
        if company_id:
            where_clauses.append("si.company_id = ?")
            params.append(company_id)
        
        where_sql = " AND ".join(where_clauses)
        
        # Inquiries
        inquiries = db.execute(f"""
            SELECT COUNT(*) as count
            FROM sales_inquiries si
            WHERE {where_sql}
        """, params).fetchone()
        
        # Quotations created from inquiries
        quotations = db.execute(f"""
            SELECT COUNT(DISTINCT sq.id) as count,
                   COALESCE(SUM(sq.total_amount), 0) as value
            FROM sales_quotations sq
            WHERE {where_sql.replace('si.', 'sq.')}
        """, params).fetchone()
        
        # Orders
        orders = db.execute(f"""
            SELECT COUNT(*) as count,
                   COALESCE(SUM(so.total_amount), 0) as value
            FROM sales_orders so
            WHERE so.order_date >= ? AND so.order_date <= ?
            {'AND so.company_id = ?' if company_id else ''}
        """, params[1:] if company_id else [date_from, date_to]).fetchone()
        
        inquiry_count = int(inquiries['count'] or 0) if inquiries else 0
        quote_count = int(quotations['count'] or 0) if quotations else 0
        order_count = int(orders['count'] or 0) if orders else 0
        
        return {
            'period': {'from': date_from, 'to': date_to},
            'inquiries': inquiry_count,
            'quotations': quote_count,
            'inquiry_to_quote_rate': round(quote_count / inquiry_count * 100, 1) if inquiry_count > 0 else 0,
            'orders': order_count,
            'quote_to_order_rate': round(order_count / quote_count * 100, 1) if quote_count > 0 else 0,
            'overall_conversion_rate': round(order_count / inquiry_count * 100, 1) if inquiry_count > 0 else 0,
            'quotation_value': float(quotations['value'] or 0) if quotations else 0,
            'order_value': float(orders['value'] or 0) if orders else 0,
        }


def get_customer_metrics(date_from: str = None, date_to: str = None,
                          company_id: int = None) -> Dict[str, Any]:
    """Get customer-related KPIs."""
    if not date_from or not date_to:
        date_from, date_to = get_date_range('this_month')
    
    with bi_db_context() as db:
        # Active customers (with orders in period)
        active_customers = db.execute("""
            SELECT COUNT(DISTINCT customer_id) as count
            FROM sales_orders
            WHERE order_date >= ? AND order_date <= ?
            {'AND company_id = ?' if company_id else ''}
        """, [date_from, date_to] + ([company_id] if company_id else [])).fetchone()
        
        # New customers (first order in period)
        new_customers = db.execute("""
            SELECT COUNT(*) as count FROM (
                SELECT customer_id, MIN(order_date) as first_order
                FROM sales_orders
                WHERE order_date >= ? AND order_date <= ?
                {'AND company_id = ?' if company_id else ''}
                GROUP BY customer_id
                HAVING first_order >= ? AND first_order <= ?
            )
        """, [date_from, date_to] + ([company_id] if company_id else []) + [date_from, date_to]).fetchone()
        
        # Repeat customers (more than one order)
        repeat_customers = db.execute("""
            SELECT COUNT(*) as count FROM (
                SELECT customer_id
                FROM sales_orders
                WHERE order_date >= ? AND order_date <= ?
                {'AND company_id = ?' if company_id else ''}
                GROUP BY customer_id
                HAVING COUNT(*) > 1
            )
        """, [date_from, date_to] + ([company_id] if company_id else [])).fetchone()
        
        # Inactive customers (no orders in last 90 days)
        cutoff_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        inactive_customers = db.execute("""
            SELECT COUNT(*) as count
            FROM sales_customers sc
            WHERE is_active = 1
            AND NOT EXISTS (
                SELECT 1 FROM sales_orders so
                WHERE so.customer_id = sc.id
                AND so.order_date >= ?
            )
        """, (cutoff_date,)).fetchone()
        
        # Total customers
        total_customers = db.execute("""
            SELECT COUNT(*) as count FROM sales_customers WHERE is_active = 1
        """).fetchone()
        
        active = int(active_customers['count'] or 0) if active_customers else 0
        new = int(new_customers['count'] or 0) if new_customers else 0
        repeat = int(repeat_customers['count'] or 0) if repeat_customers else 0
        inactive = int(inactive_customers['count'] or 0) if inactive_customers else 0
        total = int(total_customers['count'] or 0) if total_customers else 0
        
        return {
            'period': {'from': date_from, 'to': date_to},
            'active_customers': active,
            'new_customers': new,
            'repeat_customers': repeat,
            'inactive_customers_90d': inactive,
            'total_customers': total,
            'repeat_rate': round(repeat / active * 100, 1) if active > 0 else 0,
            'new_customer_rate': round(new / active * 100, 1) if active > 0 else 0,
            'inactive_rate': round(inactive / total * 100, 1) if total > 0 else 0,
        }


# =============================================================================
# INVENTORY KPIs
# =============================================================================

def get_inventory_kpis(company_id: int = None, warehouse_id: int = None) -> Dict[str, Any]:
    """
    Get comprehensive inventory KPIs.
    
    Args:
        company_id: Filter by company
        warehouse_id: Filter by specific warehouse
    
    Returns:
        Dictionary with inventory KPIs
    """
    with bi_db_context() as db:
        # Build WHERE clause
        where_clauses = ["wib.quantity > 0"]
        params = []
        
        if company_id:
            where_clauses.append("w.company_id = ?")
            params.append(company_id)
        
        if warehouse_id:
            where_clauses.append("wib.warehouse_id = ?")
            params.append(warehouse_id)
        
        where_sql = " AND ".join(where_clauses)
        
        # Overall inventory value
        total_result = db.execute(f"""
            SELECT 
                COUNT(DISTINCT wi.id) as total_items,
                COUNT(DISTINCT wib.item_id) as items_with_stock,
                COALESCE(SUM(wib.quantity), 0) as total_quantity,
                COALESCE(SUM(wib.quantity * COALESCE(wi.unit_cost, 0)), 0) as total_value,
                COALESCE(AVG(wib.quantity * COALESCE(wi.unit_cost, 0)), 0) as avg_item_value
            FROM wms_inventory_balances wib
            JOIN wms_items wi ON wib.item_id = wi.id
            JOIN wms_warehouses w ON wib.warehouse_id = w.id
            WHERE {where_sql}
        """, params).fetchone()
        
        # Stock status breakdown
        stock_status = db.execute(f"""
            SELECT 
                CASE 
                    WHEN wib.quantity <= 0 THEN 'out_of_stock'
                    WHEN wib.quantity < wib.reorder_point THEN 'low_stock'
                    WHEN wib.quantity > wib.reorder_point * 3 THEN 'overstock'
                    ELSE 'normal'
                END as status,
                COUNT(*) as item_count,
                COALESCE(SUM(wib.quantity), 0) as quantity,
                COALESCE(SUM(wib.quantity * COALESCE(wi.unit_cost, 0)), 0) as value
            FROM wms_inventory_balances wib
            JOIN wms_items wi ON wib.item_id = wi.id
            JOIN wms_warehouses w ON wib.warehouse_id = w.id
            WHERE wi.is_active = 1
            GROUP BY status
        """, params).fetchall()
        
        # Dead stock (no movement in 180 days)
        cutoff_180 = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        dead_stock = db.execute(f"""
            SELECT 
                COUNT(DISTINCT wi.id) as dead_items,
                COALESCE(SUM(wib.quantity * COALESCE(wi.unit_cost, 0)), 0) as dead_value
            FROM wms_inventory_balances wib
            JOIN wms_items wi ON wib.item_id = wi.id
            JOIN wms_warehouses w ON wib.warehouse_id = w.id
            LEFT JOIN wms_inventory_ledger wil ON wi.id = wil.item_id 
                AND wil.created_at >= ?
            WHERE {where_sql}
            AND wi.is_active = 1
            AND wib.quantity > 0
            AND wil.id IS NULL
        """, [cutoff_180] + params).fetchone()
        
        # Top stock items
        top_items = db.execute(f"""
            SELECT 
                wi.item_code,
                wi.name as item_name,
                w.name as warehouse,
                wib.quantity,
                COALESCE(wi.unit_cost, 0) as unit_cost,
                COALESCE(wib.quantity * wi.unit_cost, 0) as total_value,
                wib.reorder_point
            FROM wms_inventory_balances wib
            JOIN wms_items wi ON wib.item_id = wi.id
            JOIN wms_warehouses w ON wib.warehouse_id = w.id
            WHERE {where_sql}
            AND wi.is_active = 1
            ORDER BY wib.quantity * COALESCE(wi.unit_cost, 0) DESC
            LIMIT 10
        """, params).fetchall()
        
        # Items below reorder point
        reorder_alerts = db.execute(f"""
            SELECT 
                wi.item_code,
                wi.name as item_name,
                w.name as warehouse,
                wib.quantity,
                wib.reorder_point,
                wib.reorder_point - wib.quantity as shortage
            FROM wms_inventory_balances wib
            JOIN wms_items wi ON wib.item_id = wi.id
            JOIN wms_warehouses w ON wib.warehouse_id = w.id
            WHERE {where_sql}
            AND wi.is_active = 1
            AND wib.quantity < wib.reorder_point
            AND wib.quantity > 0
            ORDER BY (wib.reorder_point - wib.quantity) DESC
            LIMIT 10
        """, params).fetchall()
        
        # Zero stock items
        zero_stock = db.execute(f"""
            SELECT COUNT(*) as count
            FROM wms_inventory_balances wib
            JOIN wms_items wi ON wib.item_id = wi.id
            JOIN wms_warehouses w ON wib.warehouse_id = w.id
            WHERE {where_sql}
            AND wi.is_active = 1
            AND wib.quantity <= 0
        """, params).fetchone()
        
        status_breakdown = {}
        for row in stock_status:
            status_breakdown[row['status']] = {
                'item_count': row['item_count'],
                'quantity': row['quantity'],
                'value': row['value']
            }
        
        return {
            'total_items': int(total_result['total_items'] or 0),
            'items_with_stock': int(total_result['items_with_stock'] or 0),
            'total_quantity': int(total_result['total_quantity'] or 0),
            'total_value': float(total_result['total_value'] or 0),
            'avg_item_value': float(total_result['avg_item_value'] or 0),
            'dead_stock_items': int(dead_stock['dead_items'] or 0) if dead_stock else 0,
            'dead_stock_value': float(dead_stock['dead_value'] or 0) if dead_stock else 0,
            'out_of_stock_count': int(zero_stock['count'] or 0) if zero_stock else 0,
            'status_breakdown': status_breakdown,
            'top_items': rows_to_list(top_items),
            'reorder_alerts': rows_to_list(reorder_alerts),
            'currency': 'AED'
        }


def get_inventory_turnover(days: int = 90) -> Dict[str, Any]:
    """
    Calculate inventory turnover metrics.
    
    Args:
        days: Number of days to look back for sales
    """
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    with bi_db_context() as db:
        # Total sales value in period
        sales_result = db.execute("""
            SELECT COALESCE(SUM(ol.final_price * ol.ordered_quantity), 0) as total_sales
            FROM sales_order_lines ol
            JOIN sales_orders o ON ol.order_id = o.id
            WHERE o.order_date >= ?
            AND o.status NOT IN ('Cancelled', 'Closed')
        """, (cutoff_date,)).fetchone()
        
        # Average inventory value
        avg_inventory = db.execute("""
            SELECT COALESCE(AVG(daily_value), 0) as avg_value
            FROM (
                SELECT SUM(wib.quantity * COALESCE(wi.unit_cost, 0)) as daily_value
                FROM wms_inventory_balances wib
                JOIN wms_items wi ON wib.item_id = wi.id
                WHERE wi.is_active = 1
                GROUP BY wib.warehouse_id
            )
        """).fetchone()
        
        sales = float(sales_result['total_sales'] or 0) if sales_result else 0
        avg_inv = float(avg_inventory['avg_value'] or 0) if avg_inventory else 0
        
        turnover = sales / avg_inv if avg_inv > 0 else 0
        days_of_inventory = (avg_inv / (sales / days)) if sales > 0 else 0
        
        return {
            'period_days': days,
            'cost_of_goods_sold': sales,
            'average_inventory_value': avg_inv,
            'inventory_turnover_ratio': round(turnover, 2),
            'days_of_inventory': round(days_of_inventory, 1),
            'currency': 'AED'
        }


# =============================================================================
# LOGISTICS KPIs
# =============================================================================

def get_logistics_kpis(date_from: str = None, date_to: str = None,
                       company_id: int = None) -> Dict[str, Any]:
    """Get comprehensive logistics and delivery KPIs."""
    if not date_from or not date_to:
        date_from, date_to = get_date_range('this_month')
    
    with bi_db_context() as db:
        # Build WHERE clause
        where_clauses = ["dt.date >= ?", "dt.date <= ?"]
        params = [date_from, date_to]
        
        if company_id:
            where_clauses.append("dt.company_id = ?")
            params.append(company_id)
        
        where_sql = " AND ".join(where_clauses)
        
        # Trip summary
        trips = db.execute(f"""
            SELECT 
                COUNT(DISTINCT dt.id) as total_trips,
                COUNT(DISTINCT CASE WHEN dt.status = 'Completed' THEN dt.id END) as completed_trips,
                COUNT(DISTINCT CASE WHEN dt.status = 'In Transit' THEN dt.id END) as in_transit,
                COUNT(DISTINCT CASE WHEN dt.status = 'Delayed' THEN dt.id END) as delayed
            FROM delivery_trips dt
            WHERE {where_sql}
        """, params).fetchone()
        
        # Delivery stops
        stops = db.execute(f"""
            SELECT 
                COUNT(DISTINCT ds.id) as total_stops,
                COUNT(DISTINCT CASE WHEN ds.status = 'Completed' THEN ds.id END) as completed,
                COUNT(DISTINCT CASE WHEN ds.status = 'Pending' THEN ds.id END) as pending,
                COUNT(DISTINCT CASE WHEN ds.status = 'Failed' THEN ds.id END) as failed
            FROM delivery_stops ds
            JOIN delivery_trips dt ON ds.trip_id = dt.id
            WHERE {where_sql.replace('dt.', 'dt.')}
        """, params).fetchone()
        
        # On-time delivery rate
        on_time = db.execute(f"""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN ds.arrival_time <= ds.scheduled_time THEN 1 ELSE 0 END) as on_time
            FROM delivery_stops ds
            JOIN delivery_trips dt ON ds.trip_id = dt.id
            WHERE {where_sql.replace('dt.', 'dt.')}
            AND ds.scheduled_time IS NOT NULL
            AND ds.status = 'Completed'
        """, params).fetchone()
        
        # By warehouse
        by_warehouse = db.execute(f"""
            SELECT 
                w.name as warehouse,
                COUNT(DISTINCT dt.id) as trips,
                COUNT(DISTINCT ds.id) as stops,
                COUNT(DISTINCT CASE WHEN ds.status = 'Completed' THEN ds.id END) as completed
            FROM delivery_trips dt
            JOIN delivery_stops ds ON dt.id = ds.trip_id
            JOIN warehouses w ON dt.warehouse_id = w.id
            WHERE {where_sql}
            GROUP BY w.id
        """, params).fetchall()
        
        trips_total = int(trips['total_trips'] or 0) if trips else 0
        trips_completed = int(trips['completed_trips'] or 0) if trips else 0
        stops_total = int(stops['total_stops'] or 0) if stops else 0
        stops_completed = int(stops['completed'] or 0) if stops else 0
        stops_failed = int(stops['failed'] or 0) if stops else 0
        
        on_time_total = int(on_time['total'] or 0) if on_time else 0
        on_time_count = int(on_time['on_time'] or 0) if on_time else 0
        
        return {
            'period': {'from': date_from, 'to': date_to},
            'total_trips': trips_total,
            'completed_trips': trips_completed,
            'in_transit_trips': int(trips['in_transit'] or 0) if trips else 0,
            'delayed_trips': int(trips['delayed'] or 0) if trips else 0,
            'trip_completion_rate': round(trips_completed / trips_total * 100, 1) if trips_total > 0 else 0,
            'total_stops': stops_total,
            'completed_stops': stops_completed,
            'pending_stops': int(stops['pending'] or 0) if stops else 0,
            'failed_stops': stops_failed,
            'stop_completion_rate': round(stops_completed / stops_total * 100, 1) if stops_total > 0 else 0,
            'on_time_delivery_rate': round(on_time_count / on_time_total * 100, 1) if on_time_total > 0 else 0,
            'failed_delivery_rate': round(stops_failed / stops_total * 100, 1) if stops_total > 0 else 0,
            'by_warehouse': rows_to_list(by_warehouse)
        }


# =============================================================================
# PROCUREMENT KPIs
# =============================================================================

def get_procurement_kpis(date_from: str = None, date_to: str = None,
                          company_id: int = None) -> Dict[str, Any]:
    """Get comprehensive procurement KPIs."""
    if not date_from or not date_to:
        date_from, date_to = get_date_range('this_month')
    
    with bi_db_context() as db:
        # Build WHERE clause
        where_clauses = ["po.order_date >= ?", "po.order_date <= ?"]
        params = [date_from, date_to]
        
        if company_id:
            where_clauses.append("po.company_id = ?")
            params.append(company_id)
        
        where_sql = " AND ".join(where_clauses)
        
        # PO summary
        po_summary = db.execute(f"""
            SELECT 
                COUNT(DISTINCT po.id) as po_count,
                COALESCE(SUM(po.total_amount), 0) as total_spend,
                COUNT(DISTINCT po.supplier_id) as supplier_count
            FROM purchase_orders po
            WHERE {where_sql}
            AND po.status NOT IN ('Cancelled', 'Rejected')
        """, params).fetchone()
        
        # By status
        by_status = db.execute(f"""
            SELECT 
                po.status,
                COUNT(*) as count,
                COALESCE(SUM(po.total_amount), 0) as amount
            FROM purchase_orders po
            WHERE {where_sql}
            GROUP BY po.status
        """, params).fetchall()
        
        # Delayed POs
        delayed = db.execute(f"""
            SELECT COUNT(*) as count,
                   COALESCE(SUM(po.total_amount), 0) as amount
            FROM purchase_orders po
            WHERE {where_sql}
            AND po.status = 'Delayed'
        """, params).fetchone()
        
        # Open POs (not delivered/completed)
        open_pos = db.execute(f"""
            SELECT COUNT(*) as count,
                   COALESCE(SUM(po.total_amount), 0) as amount
            FROM purchase_orders po
            WHERE {where_sql}
            AND po.status IN ('Confirmed', 'In Progress', 'Partial', 'Pending Receipt')
        """, params).fetchone()
        
        # Emergency purchases
        emergency = db.execute(f"""
            SELECT COUNT(*) as count,
                   COALESCE(SUM(po.total_amount), 0) as amount
            FROM purchase_orders po
            WHERE {where_sql}
            AND po.purchase_type = 'Emergency'
        """, params).fetchone()
        
        # Top suppliers
        top_suppliers = db.execute(f"""
            SELECT 
                s.name as supplier,
                COUNT(DISTINCT po.id) as po_count,
                COALESCE(SUM(po.total_amount), 0) as spend
            FROM purchase_orders po
            JOIN suppliers s ON po.supplier_id = s.id
            WHERE {where_sql}
            GROUP BY po.supplier_id
            ORDER BY spend DESC
            LIMIT 10
        """, params).fetchall()
        
        return {
            'period': {'from': date_from, 'to': date_to},
            'po_count': int(po_summary['po_count'] or 0) if po_summary else 0,
            'total_spend': float(po_summary['total_spend'] or 0) if po_summary else 0,
            'active_suppliers': int(po_summary['supplier_count'] or 0) if po_summary else 0,
            'delayed_count': int(delayed['count'] or 0) if delayed else 0,
            'delayed_amount': float(delayed['amount'] or 0) if delayed else 0,
            'open_po_count': int(open_pos['count'] or 0) if open_pos else 0,
            'open_po_amount': float(open_pos['amount'] or 0) if open_pos else 0,
            'emergency_count': int(emergency['count'] or 0) if emergency else 0,
            'emergency_amount': float(emergency['amount'] or 0) if emergency else 0,
            'emergency_rate': round(
                (int(emergency['count'] or 0) / int(po_summary['po_count'] or 1)) * 100, 1
            ) if po_summary and int(po_summary['po_count'] or 0) > 0 else 0,
            'by_status': {r['status']: {'count': r['count'], 'amount': r['amount']} for r in by_status},
            'top_suppliers': rows_to_list(top_suppliers),
            'currency': 'AED'
        }


# =============================================================================
# HR KPIs
# =============================================================================

def get_hr_kpis(date_from: str = None, date_to: str = None,
                 company_id: int = None) -> Dict[str, Any]:
    """Get comprehensive HR/workforce KPIs."""
    if not date_from or not date_to:
        date_from, date_to = get_date_range('this_month')
    
    with bi_db_context() as db:
        # Build WHERE clause for employees
        emp_where = "he.status = 'Active'"
        emp_params = []
        
        if company_id:
            emp_where += " AND he.company_id = ?"
            emp_params.append(company_id)
        
        # Headcount
        headcount = db.execute(f"""
            SELECT COUNT(*) as total
            FROM hr_employees he
            WHERE {emp_where}
        """, emp_params).fetchone()
        
        # Attendance today
        today = datetime.now().strftime('%Y-%m-%d')
        attendance_today = db.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN har.status = 'Present' THEN 1 ELSE 0 END) as present,
                SUM(CASE WHEN har.status = 'Absent' THEN 1 ELSE 0 END) as absent,
                SUM(CASE WHEN har.status = 'Late' THEN 1 ELSE 0 END) as late
            FROM hr_attendance_records har
            WHERE har.date = ?
        """, (today,)).fetchone()
        
        # On leave today
        on_leave = db.execute("""
            SELECT COUNT(*) as count
            FROM hr_leave_requests hlr
            WHERE hlr.status = 'Approved'
            AND hlr.start_date <= ?
            AND hlr.end_date >= ?
        """, (today, today)).fetchone()
        
        # Pending leave requests
        pending_leave = db.execute("""
            SELECT COUNT(*) as count
            FROM hr_leave_requests hlr
            WHERE hlr.status = 'Pending'
        """).fetchone()
        
        # Overtime summary (this month)
        overtime = db.execute("""
            SELECT 
                COALESCE(SUM(har.overtime_hours), 0) as total_hours,
                COUNT(DISTINCT har.employee_id) as employees_with_overtime
            FROM hr_attendance_records har
            WHERE har.date >= ? AND har.date <= ?
            AND har.overtime_hours > 0
        """, (date_from, date_to)).fetchone()
        
        # By department
        by_department = db.execute(f"""
            SELECT 
                hd.name as department,
                COUNT(DISTINCT he.id) as headcount
            FROM hr_departments hd
            LEFT JOIN hr_employees he ON hd.id = he.department_id AND he.status = 'Active'
            GROUP BY hd.id
            ORDER BY headcount DESC
        """).fetchall()
        
        # Open positions (if recruitment table exists)
        try:
            open_positions = db.execute("""
                SELECT COUNT(*) as count
                FROM hr_recruitment
                WHERE status IN ('Open', 'Published', 'Active')
            """).fetchone()
            open_pos_count = int(open_positions['count'] or 0) if open_positions else 0
        except:
            open_pos_count = 0
        
        present = int(attendance_today['present'] or 0) if attendance_today else 0
        total_att = int(attendance_today['total'] or 0) if attendance_today else 0
        late = int(attendance_today['late'] or 0) if attendance_today else 0
        
        return {
            'period': {'from': date_from, 'to': date_to},
            'total_headcount': int(headcount['total'] or 0) if headcount else 0,
            'attendance_today': {
                'total': total_att,
                'present': present,
                'absent': int(attendance_today['absent'] or 0) if attendance_today else 0,
                'late': late,
                'attendance_rate': round(present / total_att * 100, 1) if total_att > 0 else 0,
                'late_rate': round(late / total_att * 100, 1) if total_att > 0 else 0,
            },
            'on_leave_today': int(on_leave['count'] or 0) if on_leave else 0,
            'pending_leave_requests': int(pending_leave['count'] or 0) if pending_leave else 0,
            'overtime': {
                'total_hours': float(overtime['total_hours'] or 0) if overtime else 0,
                'employees': int(overtime['employees_with_overtime'] or 0) if overtime else 0,
            },
            'open_positions': open_pos_count,
            'by_department': rows_to_list(by_department)
        }


# =============================================================================
# MARKETING KPIs
# =============================================================================

def get_marketing_kpis(date_from: str = None, date_to: str = None,
                       company_id: int = None) -> Dict[str, Any]:
    """Get comprehensive marketing KPIs."""
    if not date_from or not date_to:
        date_from, date_to = get_date_range('this_month')
    
    with bi_db_context() as db:
        # Campaigns
        campaigns = db.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed
            FROM marketing_campaigns
            WHERE start_date >= ? AND start_date <= ?
        """, (date_from, date_to)).fetchone()
        
        # Leads
        leads = db.execute("""
            SELECT 
                COUNT(*) as total_leads,
                SUM(CASE WHEN lead_status = 'New' THEN 1 ELSE 0 END) as new,
                SUM(CASE WHEN lead_status = 'Contacted' THEN 1 ELSE 0 END) as contacted,
                SUM(CASE WHEN lead_status = 'Qualified' THEN 1 ELSE 0 END) as qualified,
                SUM(CASE WHEN lead_status = 'Converted' THEN 1 ELSE 0 END) as converted
            FROM marketing_leads
            WHERE created_at >= ? AND created_at <= ?
        """, (date_from, date_to)).fetchone()
        
        # Lead sources
        by_source = db.execute("""
            SELECT 
                COALESCE(lead_source, 'Unknown') as source,
                COUNT(*) as count
            FROM marketing_leads
            WHERE created_at >= ? AND created_at <= ?
            GROUP BY lead_source
            ORDER BY count DESC
        """, (date_from, date_to)).fetchall()
        
        # Converted leads value (from sales orders)
        converted_value = db.execute("""
            SELECT COALESCE(SUM(so.total_amount), 0) as value
            FROM sales_orders so
            JOIN marketing_leads ml ON so.lead_id = ml.id
            WHERE so.order_date >= ? AND so.order_date <= ?
        """, (date_from, date_to)).fetchone()
        
        total_leads = int(leads['total_leads'] or 0) if leads else 0
        converted_leads = int(leads['converted'] or 0) if leads else 0
        qualified_leads = int(leads['qualified'] or 0) if leads else 0
        
        return {
            'period': {'from': date_from, 'to': date_to},
            'campaigns': {
                'total': int(campaigns['total'] or 0) if campaigns else 0,
                'active': int(campaigns['active'] or 0) if campaigns else 0,
                'completed': int(campaigns['completed'] or 0) if campaigns else 0,
            },
            'leads': {
                'total': total_leads,
                'new': int(leads['new'] or 0) if leads else 0,
                'contacted': int(leads['contacted'] or 0) if leads else 0,
                'qualified': qualified_leads,
                'converted': converted_leads,
            },
            'conversion_rate': round(converted_leads / total_leads * 100, 1) if total_leads > 0 else 0,
            'qualification_rate': round(qualified_leads / total_leads * 100, 1) if total_leads > 0 else 0,
            'by_source': {r['source']: r['count'] for r in by_source},
            'converted_revenue': float(converted_value['value'] or 0) if converted_value else 0,
            'currency': 'AED'
        }


# =============================================================================
# FINANCIAL KPIs (Basic - requires accounting data)
# =============================================================================

def get_financial_kpis(date_from: str = None, date_to: str = None,
                       company_id: int = None) -> Dict[str, Any]:
    """
    Get basic financial KPIs.
    Note: Full financial data requires accounting module integration.
    """
    if not date_from or not date_to:
        date_from, date_to = get_date_range('this_month')
    
    with bi_db_context() as db:
        # Get sales revenue
        sales_where = "so.order_date >= ? AND so.order_date <= ?"
        sales_params = [date_from, date_to]
        
        if company_id:
            sales_where += " AND so.company_id = ?"
            sales_params.append(company_id)
        
        revenue_result = db.execute(f"""
            SELECT COALESCE(SUM(so.total_amount), 0) as revenue,
                   COALESCE(SUM(so.subtotal), 0) as net_revenue,
                   COALESCE(SUM(so.discount_amount), 0) as discounts
            FROM sales_orders so
            WHERE {sales_where}
            AND so.status NOT IN ('Cancelled', 'Closed')
        """, sales_params).fetchone()
        
        revenue = float(revenue_result['revenue'] or 0) if revenue_result else 0
        net_revenue = float(revenue_result['net_revenue'] or 0) if revenue_result else 0
        discounts = float(revenue_result['discounts'] or 0) if revenue_result else 0
        
        # Get customer receivables (outstanding balances)
        receivables = db.execute("""
            SELECT 
                COALESCE(SUM(sc.outstanding_balance), 0) as total_receivables,
                COUNT(*) as customers_with_balance
            FROM sales_customers sc
            WHERE sc.outstanding_balance > 0
        """).fetchone()
        
        # Aged receivables (simplified)
        aged_receivables = db.execute("""
            SELECT 
                CASE 
                    WHEN DATEDIFF(CURRENT_DATE, 
                        (SELECT MAX(so.order_date) FROM sales_orders so WHERE so.customer_id = sc.id)
                    ) <= 30 THEN 'current'
                    WHEN DATEDIFF(CURRENT_DATE,
                        (SELECT MAX(so.order_date) FROM sales_orders so WHERE so.customer_id = sc.id)
                    ) <= 60 THEN 'days_31_60'
                    WHEN DATEDIFF(CURRENT_DATE,
                        (SELECT MAX(so.order_date) FROM sales_orders so WHERE so.customer_id = sc.id)
                    ) <= 90 THEN 'days_61_90'
                    ELSE 'over_90'
                END as age_bucket,
                COUNT(*) as count,
                COALESCE(SUM(sc.outstanding_balance), 0) as amount
            FROM sales_customers sc
            WHERE sc.outstanding_balance > 0
            GROUP BY age_bucket
        """).fetchall()
        
        # Top debtors
        top_debtors = db.execute("""
            SELECT 
                sc.name as customer,
                sc.outstanding_balance as balance
            FROM sales_customers sc
            WHERE sc.outstanding_balance > 0
            ORDER BY sc.outstanding_balance DESC
            LIMIT 10
        """).fetchall()
        
        total_receivables = float(receivables['total_receivables'] or 0) if receivables else 0
        customers_with_balance = int(receivables['customers_with_balance'] or 0) if receivables else 0
        
        return {
            'period': {'from': date_from, 'to': date_to},
            'revenue': revenue,
            'net_revenue': net_revenue,
            'discounts_given': discounts,
            'gross_margin_estimate': net_revenue * 0.3,  # Estimate if no cost data
            'total_receivables': total_receivables,
            'receivable_customers': customers_with_balance,
            'aged_receivables': {r['age_bucket']: {'count': r['count'], 'amount': r['amount']} for r in aged_receivables},
            'top_debtors': rows_to_list(top_debtors),
            'currency': 'AED',
            'note': 'Gross margin is estimated. Actual margin requires cost data integration.'
        }


# =============================================================================
# ALERTS AND EXCEPTIONS
# =============================================================================

def get_alerts_and_exceptions(company_id: int = None, severity_threshold: str = 'MEDIUM') -> List[Dict]:
    """
    Get current alerts and exceptions requiring management attention.
    
    Args:
        company_id: Filter by company
        severity_threshold: Minimum severity to include (LOW, MEDIUM, HIGH, CRITICAL)
    
    Returns:
        List of alert/exception dictionaries
    """
    alerts = []
    today = datetime.now().strftime('%Y-%m-%d')
    
    severity_order = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
    min_severity = severity_order.get(severity_threshold, 2)
    
    with bi_db_context() as db:
        # Low stock alerts
        low_stock = db.execute("""
            SELECT 
                wi.item_code,
                wi.name as item_name,
                w.name as warehouse,
                wib.quantity,
                wib.reorder_point,
                (wib.reorder_point - wib.quantity) as shortage,
                'HIGH' as severity,
                'low_stock' as alert_type,
                'Low Stock Alert' as title,
                wi.id as item_id
            FROM wms_inventory_balances wib
            JOIN wms_items wi ON wib.item_id = wi.id
            JOIN wms_warehouses w ON wib.warehouse_id = w.id
            WHERE wib.quantity < wib.reorder_point
            AND wib.quantity > 0
            AND wi.is_active = 1
            ORDER BY shortage DESC
            LIMIT 10
        """).fetchall()
        
        for item in low_stock:
            if severity_order.get('HIGH', 3) >= min_severity:
                alerts.append({
                    'severity': item['severity'],
                    'type': item['alert_type'],
                    'title': f"Low Stock: {item['item_name']}",
                    'description': f"Current: {item['quantity']}, Reorder Point: {item['reorder_point']}, Shortage: {item['shortage']}",
                    'warehouse': item['warehouse'],
                    'item_code': item['item_code'],
                    'item_id': item['item_id'],
                    'action_url': f'/wms/inventory?item={item["item_id"]}'
                })
        
        # Out of stock items
        out_stock = db.execute("""
            SELECT 
                wi.item_code,
                wi.name as item_name,
                w.name as warehouse,
                'CRITICAL' as severity,
                'out_of_stock' as alert_type,
                wi.id as item_id
            FROM wms_inventory_balances wib
            JOIN wms_items wi ON wib.item_id = wi.id
            JOIN wms_warehouses w ON wib.warehouse_id = w.id
            WHERE wib.quantity <= 0
            AND wi.is_active = 1
            ORDER BY wi.name
            LIMIT 10
        """).fetchall()
        
        for item in out_stock:
            if severity_order.get('CRITICAL', 4) >= min_severity:
                alerts.append({
                    'severity': item['severity'],
                    'type': item['alert_type'],
                    'title': f"OUT OF STOCK: {item['item_name']}",
                    'description': 'Immediate procurement action required',
                    'warehouse': item['warehouse'],
                    'item_code': item['item_code'],
                    'item_id': item['item_id'],
                    'action_url': f'/procurement/requisitions?item={item["item_id"]}'
                })
        
        # Delayed orders
        delayed_orders = db.execute("""
            SELECT 
                so.order_number,
                so.order_date,
                so.total_amount,
                sc.name as customer,
                so.promised_delivery_date,
                DATEDIFF(?, so.promised_delivery_date) as delay_days,
                'HIGH' as severity,
                'delayed_order' as alert_type
            FROM sales_orders so
            JOIN sales_customers sc ON so.customer_id = sc.id
            WHERE so.status = 'Delayed'
            ORDER BY delay_days DESC
            LIMIT 10
        """, (today,)).fetchall()
        
        for order in delayed_orders:
            if severity_order.get('HIGH', 3) >= min_severity:
                alerts.append({
                    'severity': order['severity'],
                    'type': order['alert_type'],
                    'title': f"Delayed Order: {order['order_number']}",
                    'description': f"Customer: {order['customer']}, Amount: {order['total_amount']:,.2f}, Delayed by: {order['delay_days']} days",
                    'customer': order['customer'],
                    'order_number': order['order_number'],
                    'amount': order['total_amount'],
                    'delay_days': order['delay_days'],
                    'action_url': f'/sales/orders/{order["order_number"]}'
                })
        
        # Overdue receivables
        overdue_receivables = db.execute("""
            SELECT 
                sc.name as customer,
                sc.outstanding_balance as balance,
                DATEDIFF(?, 
                    (SELECT MAX(so.order_date) FROM sales_orders so WHERE so.customer_id = sc.id)
                ) as days_overdue,
                'HIGH' as severity,
                'overdue_receivable' as alert_type
            FROM sales_customers sc
            WHERE sc.outstanding_balance > 0
            AND DATEDIFF(?, 
                (SELECT MAX(so.order_date) FROM sales_orders so WHERE so.customer_id = sc.id)
            ) > 60
            ORDER BY days_overdue DESC
            LIMIT 10
        """, (today, today)).fetchall()
        
        for rec in overdue_receivables:
            if severity_order.get('HIGH', 3) >= min_severity:
                alerts.append({
                    'severity': rec['severity'],
                    'type': rec['alert_type'],
                    'title': f"Overdue Receivable: {rec['customer']}",
                    'description': f"Balance: {rec['balance']:,.2f}, Days Overdue: {rec['days_overdue']}",
                    'customer': rec['customer'],
                    'balance': rec['balance'],
                    'days_overdue': rec['days_overdue'],
                    'action_url': f'/sales/customers/{rec["customer"]}'
                })
        
        # Pending approvals (tasks)
        pending_approvals = db.execute("""
            SELECT 
                ti.task_name,
                ti.id,
                ti.priority,
                ti.due_at,
                u.username as assignee,
                'MEDIUM' as severity,
                'pending_approval' as alert_type
            FROM task_items ti
            LEFT JOIN users u ON ti.assigned_to_user_id = u.id
            WHERE ti.status IN ('Open', 'In Progress')
            AND ti.due_at < ?
            ORDER BY ti.due_at
            LIMIT 10
        """, (today,)).fetchall()
        
        for task in pending_approvals:
            if severity_order.get('MEDIUM', 2) >= min_severity:
                alerts.append({
                    'severity': task['severity'],
                    'type': task['alert_type'],
                    'title': f"Overdue Task: {task['task_name']}",
                    'description': f"Assignee: {task['assignee']}, Was due: {task['due_at']}",
                    'assignee': task['assignee'],
                    'task_id': task['id'],
                    'action_url': f'/tasks/{task["id"]}'
                })
        
        # High-value customers at credit limit
        credit_risk = db.execute("""
            SELECT 
                sc.name as customer,
                sc.credit_limit,
                sc.outstanding_balance,
                (sc.outstanding_balance / sc.credit_limit * 100) as utilization_pct,
                'MEDIUM' as severity,
                'credit_risk' as alert_type
            FROM sales_customers sc
            WHERE sc.credit_limit > 0
            AND (sc.outstanding_balance / sc.credit_limit * 100) > 90
            ORDER BY utilization_pct DESC
            LIMIT 10
        """).fetchall()
        
        for cust in credit_risk:
            if severity_order.get('MEDIUM', 2) >= min_severity:
                alerts.append({
                    'severity': cust['severity'],
                    'type': cust['alert_type'],
                    'title': f"Credit Risk: {cust['customer']}",
                    'description': f"Balance: {cust['outstanding_balance']:,.2f}, Limit: {cust['credit_limit']:,.2f}, Utilization: {cust['utilization_pct']:.1f}%",
                    'customer': cust['customer'],
                    'balance': cust['outstanding_balance'],
                    'credit_limit': cust['credit_limit'],
                    'utilization': cust['utilization_pct'],
                    'action_url': f'/sales/customers/{cust["customer"]}'
                })
    
    # Sort by severity
    severity_sort = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    alerts.sort(key=lambda x: severity_sort.get(x['severity'], 4))
    
    return alerts


# =============================================================================
# HOLDING/CONSOLIDATED VIEW
# =============================================================================

def get_consolidated_holding_view(date_from: str = None, date_to: str = None,
                                  eliminate_intercompany: bool = False) -> Dict[str, Any]:
    """
    Get holding-level consolidated view across all companies.
    
    This is critical for multi-company holdings:
    - Shows group-wide KPIs
    - Per-company contribution
    - Company ranking
    - Consolidated trends
    
    Args:
        date_from: Start date
        date_to: End date
        eliminate_intercompany: Whether to eliminate intercompany transactions
    
    Returns:
        Consolidated holding metrics
    """
    if not date_from or not date_to:
        date_from, date_to = get_date_range('this_month')
    
    companies = get_all_companies_for_bi()
    
    with bi_db_context() as db:
        company_metrics = []
        
        for company in companies:
            company_id = company['id']
            
            # Sales for company
            sales_result = db.execute("""
                SELECT 
                    COUNT(DISTINCT so.id) as order_count,
                    COALESCE(SUM(so.total_amount), 0) as total_sales,
                    COUNT(DISTINCT so.customer_id) as customer_count
                FROM sales_orders so
                WHERE so.company_id = ?
                AND so.order_date >= ? AND so.order_date <= ?
                AND so.status NOT IN ('Cancelled', 'Closed')
            """, (company_id, date_from, date_to)).fetchone()
            
            # Inventory value
            inv_result = db.execute("""
                SELECT COALESCE(SUM(wib.quantity * COALESCE(wi.unit_cost, 0)), 0) as inventory_value
                FROM wms_inventory_balances wib
                JOIN wms_items wi ON wib.item_id = wi.id
                JOIN wms_warehouses w ON wib.warehouse_id = w.id
                WHERE w.company_id = ?
                AND wi.is_active = 1
            """, (company_id,)).fetchone()
            
            # Receivables
            ar_result = db.execute("""
                SELECT COALESCE(SUM(outstanding_balance), 0) as receivables
                FROM sales_customers
                WHERE company_id = ?
                AND outstanding_balance > 0
            """, (company_id,)).fetchone()
            
            # Headcount
            hc_result = db.execute("""
                SELECT COUNT(*) as headcount
                FROM hr_employees
                WHERE company_id = ?
                AND status = 'Active'
            """, (company_id,)).fetchone()
            
            metrics = {
                'company_id': company_id,
                'company_name': company['name'],
                'company_type': company.get('company_type', 'Unknown'),
                'order_count': int(sales_result['order_count'] or 0) if sales_result else 0,
                'total_sales': float(sales_result['total_sales'] or 0) if sales_result else 0,
                'customer_count': int(sales_result['customer_count'] or 0) if sales_result else 0,
                'inventory_value': float(inv_result['inventory_value'] or 0) if inv_result else 0,
                'receivables': float(ar_result['receivables'] or 0) if ar_result else 0,
                'headcount': int(hc_result['headcount'] or 0) if hc_result else 0,
            }
            
            # Calculate per-capita metrics
            if metrics['headcount'] > 0:
                metrics['sales_per_employee'] = round(metrics['total_sales'] / metrics['headcount'], 2)
            else:
                metrics['sales_per_employee'] = 0
            
            company_metrics.append(metrics)
        
        # Calculate group totals
        group_total_sales = sum(c['total_sales'] for c in company_metrics)
        group_total_orders = sum(c['order_count'] for c in company_metrics)
        group_total_customers = sum(c['customer_count'] for c in company_metrics)
        group_total_inventory = sum(c['inventory_value'] for c in company_metrics)
        group_total_receivables = sum(c['receivables'] for c in company_metrics)
        group_total_headcount = sum(c['headcount'] for c in company_metrics)
        
        # Add contribution percentages
        for cm in company_metrics:
            cm['sales_contribution_pct'] = round(cm['total_sales'] / group_total_sales * 100, 1) if group_total_sales > 0 else 0
            cm['orders_contribution_pct'] = round(cm['order_count'] / group_total_orders * 100, 1) if group_total_orders > 0 else 0
        
        # Sort by sales
        company_metrics.sort(key=lambda x: x['total_sales'], reverse=True)
        
        # Add rank
        for i, cm in enumerate(company_metrics):
            cm['rank'] = i + 1
        
        return {
            'period': {'from': date_from, 'to': date_to},
            'eliminate_intercompany': eliminate_intercompany,
            'group_totals': {
                'total_sales': group_total_sales,
                'total_orders': group_total_orders,
                'total_customers': group_total_customers,
                'total_inventory': group_total_inventory,
                'total_receivables': group_total_receivables,
                'total_headcount': group_total_headcount,
                'avg_sales_per_employee': round(group_total_sales / group_total_headcount, 2) if group_total_headcount > 0 else 0,
                'company_count': len(company_metrics),
            },
            'by_company': company_metrics,
            'currency': 'AED',
            'generated_at': datetime.now().isoformat()
        }


def get_company_comparison(company_ids: List[int] = None, date_from: str = None, 
                           date_to: str = None) -> Dict[str, Any]:
    """
    Compare performance across companies.
    
    Args:
        company_ids: List of company IDs to compare (None = all)
        date_from: Start date
        date_to: End date
    
    Returns:
        Company comparison data
    """
    if not date_from or not date_to:
        date_from, date_to = get_date_range('this_month')
    
    companies = get_all_companies_for_bi()
    if company_ids:
        companies = [c for c in companies if c['id'] in company_ids]
    
    comparison = []
    
    with bi_db_context() as db:
        for company in companies:
            company_id = company['id']
            
            # Current period
            current = db.execute("""
                SELECT 
                    COUNT(DISTINCT so.id) as orders,
                    COALESCE(SUM(so.total_amount), 0) as sales,
                    COUNT(DISTINCT so.customer_id) as customers
                FROM sales_orders so
                WHERE so.company_id = ?
                AND so.order_date >= ? AND so.order_date <= ?
                AND so.status NOT IN ('Cancelled', 'Closed')
            """, (company_id, date_from, date_to)).fetchone()
            
            # Previous period
            prev_from, prev_to = get_previous_period_dates(date_from, date_to)
            previous = db.execute("""
                SELECT 
                    COUNT(DISTINCT so.id) as orders,
                    COALESCE(SUM(so.total_amount), 0) as sales
                FROM sales_orders so
                WHERE so.company_id = ?
                AND so.order_date >= ? AND so.order_date <= ?
                AND so.status NOT IN ('Cancelled', 'Closed')
            """, (company_id, prev_from, prev_to)).fetchone()
            
            # Inventory
            inventory = db.execute("""
                SELECT 
                    COUNT(DISTINCT wi.id) as items,
                    COALESCE(SUM(wib.quantity * COALESCE(wi.unit_cost, 0)), 0) as value
                FROM wms_inventory_balances wib
                JOIN wms_items wi ON wib.item_id = wi.id
                JOIN wms_warehouses w ON wib.warehouse_id = w.id
                WHERE w.company_id = ?
                AND wi.is_active = 1
            """, (company_id,)).fetchone()
            
            current_sales = float(current['sales'] or 0) if current else 0
            prev_sales = float(previous['sales'] or 0) if previous else 0
            sales_change = ((current_sales - prev_sales) / prev_sales * 100) if prev_sales > 0 else 0
            
            comparison.append({
                'company_id': company_id,
                'company_name': company['name'],
                'company_type': company.get('company_type', 'Unknown'),
                'period': {
                    'from': date_from,
                    'to': date_to
                },
                'previous_period': {
                    'from': prev_from,
                    'to': prev_to
                },
                'sales': {
                    'current': current_sales,
                    'previous': prev_sales,
                    'change_pct': round(sales_change, 1)
                },
                'orders': {
                    'current': int(current['orders'] or 0) if current else 0,
                    'previous': int(previous['orders'] or 0) if previous else 0
                },
                'customers': {
                    'current': int(current['customers'] or 0) if current else 0
                },
                'inventory': {
                    'items': int(inventory['items'] or 0) if inventory else 0,
                    'value': float(inventory['value'] or 0) if inventory else 0
                }
            })
    
    # Sort by current sales
    comparison.sort(key=lambda x: x['sales']['current'], reverse=True)
    
    return {
        'companies': comparison,
        'date_range': {'from': date_from, 'to': date_to},
        'currency': 'AED'
    }


# =============================================================================
# EXECUTIVE DASHBOARD MASTER FUNCTION
# =============================================================================

def get_executive_dashboard_data(user_id: int = None, company_id: int = None,
                                  date_from: str = None, date_to: str = None) -> Dict[str, Any]:
    """
    Get comprehensive executive dashboard data.
    
    This is the main entry point for the executive dashboard.
    It aggregates all KPIs into a single structure.
    
    Args:
        user_id: Current user ID (for permission filtering)
        company_id: Company filter (None = all accessible)
        date_from: Period start
        date_to: Period end
    
    Returns:
        Complete executive dashboard data structure
    """
    if not date_from or not date_to:
        date_from, date_to = get_date_range('this_month')
    
    # Get all KPIs
    sales = get_sales_kpis(company_id=company_id, date_from=date_from, date_to=date_to)
    customers = get_customer_metrics(date_from=date_from, date_to=date_to, company_id=company_id)
    inventory = get_inventory_kpis(company_id=company_id)
    logistics = get_logistics_kpis(date_from=date_from, date_to=date_to, company_id=company_id)
    procurement = get_procurement_kpis(date_from=date_from, date_to=date_to, company_id=company_id)
    hr = get_hr_kpis(date_from=date_from, date_to=date_to, company_id=company_id)
    marketing = get_marketing_kpis(date_from=date_from, date_to=date_to, company_id=company_id)
    financial = get_financial_kpis(date_from=date_from, date_to=date_to, company_id=company_id)
    alerts = get_alerts_and_exceptions(company_id=company_id, severity_threshold='MEDIUM')
    holding = get_consolidated_holding_view(date_from=date_from, date_to=date_to)
    funnel = get_inquiry_to_order_funnel(date_from=date_from, date_to=date_to, company_id=company_id)
    turnover = get_inventory_turnover(days=90)
    
    # Get critical alerts count
    critical_alerts = [a for a in alerts if a['severity'] == 'CRITICAL']
    high_alerts = [a for a in alerts if a['severity'] == 'HIGH']
    
    return {
        'timestamp': datetime.now().isoformat(),
        'period': {'from': date_from, 'to': date_to},
        'company_filter': company_id,
        
        # Executive Summary KPIs
        'executive_summary': {
            'total_revenue': sales['total_sales'],
            'revenue_change_pct': sales['sales_change_pct'],
            'total_orders': sales['total_orders'],
            'orders_change_pct': sales['orders_change_pct'],
            'avg_order_value': sales['avg_order_value'],
            'unique_customers': sales['unique_customers'],
            'new_customers': customers['new_customers'],
            'repeat_rate': customers['repeat_rate'],
            'inventory_value': inventory['total_value'],
            'dead_stock_value': inventory['dead_stock_value'],
            'out_of_stock_count': inventory['out_of_stock_count'],
            'receivables': financial['total_receivables'],
            'total_headcount': hr['total_headcount'],
            'attendance_rate': hr['attendance_today']['attendance_rate'],
        },
        
        # Detail sections
        'sales': sales,
        'customers': customers,
        'funnel': funnel,
        'inventory': inventory,
        'inventory_turnover': turnover,
        'logistics': logistics,
        'procurement': procurement,
        'hr': hr,
        'marketing': marketing,
        'financial': financial,
        'holding': holding,
        'alerts': alerts,
        
        # Alert summary
        'alert_summary': {
            'total': len(alerts),
            'critical': len(critical_alerts),
            'high': len(high_alerts),
            'top_alerts': alerts[:5]  # Top 5 most critical
        },
        
        # Trend summary
        'trend_summary': {
            'revenue_trend': 'up' if sales['sales_change_pct'] > 0 else 'down',
            'order_trend': 'up' if sales['orders_change_pct'] > 0 else 'down',
            'inventory_trend': 'normal',
            'delivery_trend': 'on_track' if logistics['on_time_delivery_rate'] > 90 else 'delayed'
        },
        
        # Metadata
        'meta': {
            'currency': 'AED',
            'timezone': 'Asia/Dubai',
            'date_format': 'DD/MM/YYYY',
            'generated_at': datetime.now().isoformat(),
            'version': '1.0'
        }
    }


# =============================================================================
# DRILL-DOWN FUNCTIONS
# =============================================================================

def drill_down_sales_by_company(date_from: str, date_to: str, company_id: int = None) -> List[Dict]:
    """Get sales breakdown by company for drill-down."""
    with bi_db_context() as db:
        where_clauses = ["so.order_date >= ?", "so.order_date <= ?"]
        params = [date_from, date_to]
        
        if company_id:
            where_clauses.append("so.company_id = ?")
            params.append(company_id)
        
        where_sql = " AND ".join(where_clauses)
        
        results = db.execute(f"""
            SELECT 
                c.id as company_id,
                c.name as company,
                COUNT(DISTINCT so.id) as order_count,
                COALESCE(SUM(so.total_amount), 0) as total_sales,
                COALESCE(AVG(so.total_amount), 0) as avg_order,
                COUNT(DISTINCT so.customer_id) as customer_count
            FROM sales_orders so
            JOIN companies c ON so.company_id = c.id
            WHERE {where_sql}
            GROUP BY c.id
            ORDER BY total_sales DESC
        """, params).fetchall()
        
        return rows_to_list(results)


def drill_down_sales_by_item(date_from: str, date_to: str, company_id: int = None,
                              limit: int = 50) -> List[Dict]:
    """Get sales breakdown by item/part for drill-down."""
    with bi_db_context() as db:
        where_clauses = ["so.order_date >= ?", "so.order_date <= ?"]
        params = [date_from, date_to]
        
        if company_id:
            where_clauses.append("so.company_id = ?")
            params.append(company_id)
        
        where_sql = " AND ".join(where_clauses)
        
        results = db.execute(f"""
            SELECT 
                sol.part_number,
                sol.brand,
                sol.description,
                COUNT(DISTINCT so.id) as order_count,
                SUM(sol.ordered_quantity) as total_qty,
                SUM(sol.final_price * sol.ordered_quantity) as total_sales
            FROM sales_orders so
            JOIN sales_order_lines sol ON so.id = sol.order_id
            WHERE {where_sql}
            AND so.status NOT IN ('Cancelled', 'Closed')
            GROUP BY sol.part_number, sol.brand
            ORDER BY total_sales DESC
            LIMIT ?
        """, params + [limit]).fetchall()
        
        return rows_to_list(results)


def drill_down_inventory_by_warehouse(company_id: int = None) -> List[Dict]:
    """Get inventory breakdown by warehouse for drill-down."""
    with bi_db_context() as db:
        if company_id:
            rows = db.execute("""
                SELECT 
                    w.id as warehouse_id,
                    w.name as warehouse,
                    c.name as company,
                    COUNT(DISTINCT wi.id) as item_count,
                    SUM(wib.quantity) as total_quantity,
                    SUM(wib.quantity * COALESCE(wi.unit_cost, 0)) as total_value,
                    SUM(CASE WHEN wib.quantity <= 0 THEN 1 ELSE 0 END) as out_of_stock_count,
                    SUM(CASE WHEN wib.quantity < wib.reorder_point AND wib.quantity > 0 THEN 1 ELSE 0 END) as low_stock_count
                FROM wms_warehouses w
                JOIN companies c ON w.company_id = c.id
                LEFT JOIN wms_inventory_balances wib ON w.id = wib.warehouse_id
                LEFT JOIN wms_items wi ON wib.item_id = wi.id AND wi.is_active = 1
                WHERE w.company_id = ?
                GROUP BY w.id
                ORDER BY total_value DESC
            """, (company_id,)).fetchall()
        else:
            rows = db.execute("""
                SELECT 
                    w.id as warehouse_id,
                    w.name as warehouse,
                    c.name as company,
                    COUNT(DISTINCT wi.id) as item_count,
                    SUM(wib.quantity) as total_quantity,
                    SUM(wib.quantity * COALESCE(wi.unit_cost, 0)) as total_value,
                    SUM(CASE WHEN wib.quantity <= 0 THEN 1 ELSE 0 END) as out_of_stock_count,
                    SUM(CASE WHEN wib.quantity < wib.reorder_point AND wib.quantity > 0 THEN 1 ELSE 0 END) as low_stock_count
                FROM wms_warehouses w
                JOIN companies c ON w.company_id = c.id
                LEFT JOIN wms_inventory_balances wib ON w.id = wib.warehouse_id
                LEFT JOIN wms_items wi ON wib.item_id = wi.id AND wi.is_active = 1
                GROUP BY w.id
                ORDER BY total_value DESC
            """).fetchall()
        
        return rows_to_list(rows)
