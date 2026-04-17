"""
Report Background Tasks
======================
Background task processing for scheduled report generation and delivery.

Tasks:
- generate_treasury_report: Daily treasury status report
- generate_cash_position_snapshot: Cash position snapshot
- generate_weekly_kpi_report: Weekly KPI summary
- generate_financial_report: Periodic financial statements
- generate_asset_report: Asset status report
- deliver_report: Email delivery of generated reports
"""

from celery import Task
from datetime import datetime, timedelta
import logging
import io
import csv

logger = logging.getLogger(__name__)


class ReportTask(Task):
    """Base class for report generation tasks."""
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 2}
    retry_backoff = True
    retry_backoff_max = 300


# =============================================================================
# TREASURY REPORTS
# =============================================================================

@ReportTask.bind(name='tasks.report_tasks.generate_treasury_report')
def generate_treasury_report(self):
    """
    Generate daily treasury status report.

    Runs at 6 AM daily. Generates:
    - Cash position summary by bank
    - Liquidity gaps analysis
    - Upcoming payments/collections
    - Treasury alerts summary
    """
    logger.info("Generating treasury report...")

    with get_db_for_reporting() as db:
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'cash_position': [],
            'liquidity_gaps': [],
            'upcoming_payments': [],
            'upcoming_collections': [],
            'active_alerts': [],
            'summary': {}
        }

        # Cash position by bank account
        cash_position = db.execute("""
            SELECT ba.bank_name, ba.account_number, c.currency,
                   SUM(cp.current_balance) as total_balance
            FROM treasury_cash_position cp
            JOIN treasury_bank_accounts ba ON cp.bank_account_id = ba.id
            JOIN currencies c ON ba.currency_id = c.id
            WHERE cp.as_of_date >= date('now', '-1 day')
            GROUP BY ba.bank_name, c.currency
        """).fetchall()

        for pos in cash_position:
            report_data['cash_position'].append({
                'bank': pos['bank_name'],
                'account': pos['account_number'],
                'currency': pos['currency'],
                'balance': float(pos['total_balance']) if pos['total_balance'] else 0
            })

        # Calculate summary totals
        total_by_currency = {}
        for pos in report_data['cash_position']:
            curr = pos['currency']
            if curr not in total_by_currency:
                total_by_currency[curr] = 0
            total_by_currency[curr] += pos['balance']

        report_data['summary']['total_by_currency'] = total_by_currency
        report_data['summary']['total_accounts'] = len(cash_position)

        # Active alerts
        alerts = db.execute("""
            SELECT id, title, severity, status
            FROM treasury_alerts
            WHERE status = 'active'
            AND created_at >= date('now', '-7 days')
            ORDER BY severity DESC, created_at DESC
        """).fetchall()

        report_data['active_alerts'] = [
            {'id': a['id'], 'title': a['title'], 'severity': a['severity']}
            for a in alerts
        ]

        # Store report in database
        report_id = _store_report(
            db=db,
            report_type='treasury_daily',
            title='Treasury Daily Report',
            data=report_data
        )

        logger.info(f"Treasury report generated: {report_id}")
        return {'status': 'completed', 'report_id': report_id}


@ReportTask.bind(name='tasks.report_tasks.generate_cash_position_snapshot')
def generate_cash_position_snapshot(self):
    """
    Generate cash position snapshot for the current date.

    Runs at 6:30 AM daily. Captures:
    - All bank account balances
    - Petty cash balances
    - Cash pool positions
    - FX position summary
    """
    logger.info("Generating cash position snapshot...")

    with get_db_for_reporting() as db:
        snapshot_data = {
            'snapshot_date': datetime.now().date().isoformat(),
            'generated_at': datetime.now().isoformat(),
            'bank_accounts': [],
            'petty_cash': [],
            'cash_pools': [],
            'fx_positions': [],
            'total_by_currency': {}
        }

        # Bank account balances
        bank_accounts = db.execute("""
            SELECT ba.id, ba.bank_name, ba.account_number, c.currency,
                   ba.current_balance, ba.last_reconciled_date
            FROM treasury_bank_accounts ba
            JOIN currencies c ON ba.currency_id = c.id
            WHERE ba.is_active = 1
        """).fetchall()

        for ba in bank_accounts:
            snapshot_data['bank_accounts'].append({
                'id': ba['id'],
                'bank': ba['bank_name'],
                'account': ba['account_number'],
                'currency': ba['currency'],
                'balance': float(ba['current_balance']) if ba['current_balance'] else 0,
                'last_reconciled': ba['last_reconciled_date']
            })

        # Petty cash
        petty_cash = db.execute("""
            SELECT pc.id, pc.account_name, c.currency,
                   pc.current_balance, pc.minimum_balance
            FROM treasury_petty_cash pc
            JOIN currencies c ON pc.currency_id = c.id
            WHERE pc.is_active = 1
        """).fetchall()

        for pc in petty_cash:
            snapshot_data['petty_cash'].append({
                'id': pc['id'],
                'name': pc['account_name'],
                'currency': pc['currency'],
                'balance': float(pc['current_balance']) if pc['current_balance'] else 0,
                'minimum': float(pc['minimum_balance']) if pc['minimum_balance'] else 0
            })

        # Cash pools
        pools = db.execute("""
            SELECT cp.id, cp.pool_name, c.currency,
                   cp.total_balance, cp.member_count
            FROM treasury_cash_pools cp
            JOIN currencies c ON cp.currency_id = c.id
            WHERE cp.is_active = 1
        """).fetchall()

        for pool in pools:
            snapshot_data['cash_pools'].append({
                'id': pool['id'],
                'name': pool['pool_name'],
                'currency': pool['currency'],
                'balance': float(pool['total_balance']) if pool['total_balance'] else 0,
                'members': pool['member_count']
            })

        # Calculate totals
        all_items = (
            snapshot_data['bank_accounts'] +
            snapshot_data['petty_cash'] +
            snapshot_data['cash_pools']
        )
        for item in all_items:
            curr = item['currency']
            if curr not in snapshot_data['total_by_currency']:
                snapshot_data['total_by_currency'][curr] = 0
            snapshot_data['total_by_currency'][curr] += item['balance']

        # Store snapshot
        _store_snapshot(
            db=db,
            snapshot_type='cash_position',
            data=snapshot_data
        )

        logger.info("Cash position snapshot generated")
        return {'status': 'completed', 'snapshot_date': snapshot_data['snapshot_date']}


@ReportTask.bind(name='tasks.report_tasks.generate_weekly_kpi_report')
def generate_weekly_kpi_report(self):
    """
    Generate weekly KPI summary report.

    Runs Monday at 7 AM. Covers:
    - Sales performance
    - Cash flow metrics
    - Inventory turnover
    - HR metrics
    - Exception counts
    """
    logger.info("Generating weekly KPI report...")

    with get_db_for_reporting() as db:
        week_start = (datetime.now() - timedelta(days=7)).date().isoformat()
        week_end = datetime.now().date().isoformat()

        kpi_data = {
            'period': {'start': week_start, 'end': week_end},
            'generated_at': datetime.now().isoformat(),
            'finance': {},
            'operations': {},
            'hr': {},
            'exceptions': {}
        }

        # Finance KPIs
        finance_kpis = db.execute("""
            SELECT
                (SELECT SUM(current_balance) FROM treasury_bank_accounts WHERE is_active = 1) as total_cash,
                (SELECT COUNT(*) FROM treasury_alerts WHERE status = 'active') as active_alerts,
                (SELECT SUM(amount) FROM treasury_payments WHERE due_date BETWEEN ? AND ? AND status = 'approved') as pending_payments
        """, (week_start, week_end)).fetchone()

        kpi_data['finance'] = {
            'total_cash': float(finance_kpis['total_cash']) if finance_kpis['total_cash'] else 0,
            'active_alerts': finance_kpis['active_alerts'],
            'pending_payments': float(finance_kpis['pending_payments']) if finance_kpis['pending_payments'] else 0
        }

        # Operations KPIs
        ops_kpis = db.execute("""
            SELECT
                (SELECT COUNT(*) FROM wms_stock WHERE quantity_on_hand < reorder_point) as low_stock_items,
                (SELECT COUNT(*) FROM logistics_deliveries WHERE status = 'delivered' AND delivery_date BETWEEN ? AND ?) as deliveries_completed,
                (SELECT COUNT(*) FROM tasks WHERE status = 'completed' AND completed_at BETWEEN ? AND ?) as tasks_completed
        """, (week_start, week_end, week_start, week_end)).fetchone()

        kpi_data['operations'] = {
            'low_stock_items': ops_kpis['low_stock_items'],
            'deliveries_completed': ops_kpis['deliveries_completed'],
            'tasks_completed': ops_kpis['tasks_completed']
        }

        # Store report
        report_id = _store_report(
            db=db,
            report_type='weekly_kpi',
            title='Weekly KPI Report',
            data=kpi_data
        )

        logger.info(f"Weekly KPI report generated: {report_id}")
        return {'status': 'completed', 'report_id': report_id}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_db_for_reporting():
    """Get database connection for reporting tasks."""
    from database import get_db_context
    return get_db_context()


def _store_report(db, report_type, title, data):
    """Store generated report in database."""
    import json
    cursor = db.execute("""
        INSERT INTO report_history
        (report_type, title, generated_at, generated_by, data, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        report_type,
        title,
        datetime.now().isoformat(),
        1,  # System user
        json.dumps(data),
        'completed'
    ))
    db.commit()
    return cursor.lastrowid


def _store_snapshot(db, snapshot_type, data):
    """Store snapshot data in database."""
    import json
    cursor = db.execute("""
        INSERT INTO treasury_cash_position_snapshots
        (snapshot_date, data, created_at)
        VALUES (?, ?, ?)
    """, (
        data.get('snapshot_date', datetime.now().date().isoformat()),
        json.dumps(data),
        datetime.now().isoformat()
    ))
    db.commit()
    return cursor.lastrowid
