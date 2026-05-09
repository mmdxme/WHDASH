"""
Treasury Module - Unit Tests
============================
Unit tests for treasury module functionality including:
- Cash position calculations
- Cash flow forecasting
- Bank statement reconciliation
- Payment runs
- FX contracts
- Cash pooling
- Collection scoring
- Liquidity analysis
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestTreasuryModels(unittest.TestCase):
    """Test treasury model functions."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        from database import initialize_database
        initialize_database()

    def test_treasury_schema_initialization(self):
        """Test treasury schema initialization creates all tables."""
        from treasury_models import initialize_treasury_schema
        from database import table_exists

        initialize_treasury_schema()

        tables = [
            'treasury_settings',
            'treasury_cash_position_snapshots',
            'treasury_petty_cash_accounts',
            'treasury_cash_boxes',
            'treasury_cash_movements',
            'treasury_forecasts',
            'treasury_forecast_scenarios',
            'treasury_forecast_items',
            'treasury_liquidity_plans',
            'treasury_liquidity_thresholds',
            'treasury_collections_plan',
            'treasury_payments_plan',
            'treasury_transfer_requests',
            'treasury_transfer_approvals',
            'treasury_controls',
            'treasury_alerts',
            'treasury_audit_log',
            'treasury_bank_signatories',
            'treasury_account_groups',
            'treasury_workflow_rules',
            'treasury_reconciliation_rules',
            'treasury_bank_statements',
            'treasury_bank_statement_lines',
            'treasury_payment_runs',
            'treasury_payment_run_items',
            'treasury_fx_contracts',
            'treasury_counterparties',
            'treasury_bank_connections',
            'treasury_bank_charges',
            'treasury_cash_pools',
            'treasury_cash_pool_members',
            'treasury_notional_pooling',
            'treasury_collection_scores',
            'treasury_dunning_settings',
            'treasury_notification_preferences'
        ]

        for table in tables:
            self.assertTrue(table_exists(table), f"Table {table} should exist")

    def test_calculate_daily_cash_position(self):
        """Test daily cash position calculation."""
        from treasury_models import calculate_daily_cash_position

        result = calculate_daily_cash_position(company_id=1)

        self.assertIn('total_position', result)
        self.assertIn('by_currency', result)
        self.assertIn('by_bank', result)
        self.assertIn('by_entity', result)

    def test_get_cash_flow_forecast_data(self):
        """Test cash flow forecast data generation."""
        from treasury_models import get_cash_flow_forecast_data

        result = get_cash_flow_forecast_data(company_id=1, days=7)

        self.assertIn('forecast', result)
        self.assertIn('start_date', result)
        self.assertIn('end_date', result)
        self.assertEqual(result['days'], 7)

    def test_analyze_liquidity_position(self):
        """Test liquidity position analysis."""
        from treasury_models import analyze_liquidity_position

        result = analyze_liquidity_position(company_id=1)

        self.assertIn('liquidity_status', result)
        self.assertIn('current_position', result)
        self.assertIn('minimum_required', result)
        self.assertIn('issues', result)

    def test_treasury_settings_crud(self):
        """Test treasury settings CRUD operations."""
        from treasury_models import set_treasury_setting, get_treasury_setting

        set_treasury_setting('test_key', 'test_value', category='test')

        value = get_treasury_setting('test_key', default=None)
        self.assertEqual(value, 'test_value')

    def test_create_bank_statement(self):
        """Test bank statement creation."""
        from treasury_models import create_bank_statement, get_bank_statements

        stmt_id = create_bank_statement({
            'bank_account_id': 1,
            'statement_date': '2026-04-16',
            'statement_number': 'TEST-001',
            'opening_balance': 10000,
            'closing_balance': 15000,
            'total_credits': 6000,
            'total_debits': 1000,
            'company_id': 1
        })

        self.assertIsNotNone(stmt_id)

        statements = get_bank_statements(company_id=1)
        self.assertGreater(len(statements), 0)

    def test_create_payment_run(self):
        """Test payment run creation."""
        from treasury_models import create_payment_run, get_payment_runs

        run_id = create_payment_run({
            'run_name': 'Test Payment Run',
            'run_date': '2026-04-16',
            'bank_account_id': 1,
            'payment_type': 'standard',
            'currency': 'AED',
            'company_id': 1
        })

        self.assertIsNotNone(run_id)

        runs = get_payment_runs(company_id=1)
        self.assertGreater(len(runs), 0)

    def test_create_fx_contract(self):
        """Test FX contract creation."""
        from treasury_models import create_fx_contract, get_fx_contracts

        contract_id = create_fx_contract({
            'contract_type': 'spot',
            'buy_sell': 'buy',
            'base_currency': 'USD',
            'quote_currency': 'AED',
            'base_amount': 100000,
            'quote_amount': 367000,
            'exchange_rate': 3.67,
            'contract_date': '2026-04-16',
            'value_date': '2026-04-18',
            'company_id': 1,
            'created_by': 1
        })

        self.assertIsNotNone(contract_id)

        contracts = get_fx_contracts(company_id=1)
        self.assertGreater(len(contracts), 0)

    def test_fx_position_calculation(self):
        """Test FX position calculation."""
        from treasury_models import get_fx_position

        position = get_fx_position(company_id=1)

        self.assertIsInstance(position, dict)

    def test_create_counterparty(self):
        """Test counterparty creation."""
        from treasury_models import create_counterparty, get_counterparties

        cp_id = create_counterparty({
            'counterparty_name': 'Test Bank',
            'counterparty_type': 'bank',
            'bank_name': 'Emirates NBD',
            'account_number': '123456789',
            'swift_code': 'EBIL',
            'company_id': 1
        })

        self.assertIsNotNone(cp_id)

        counterparties = get_counterparties(company_id=1)
        self.assertGreater(len(counterparties), 0)

    def test_create_cash_pool(self):
        """Test cash pool creation."""
        from treasury_models import create_cash_pool, get_cash_pools

        pool_id = create_cash_pool({
            'pool_name': 'Test Cash Pool',
            'pool_type': 'physical',
            'pooling_method': 'zero_balance',
            'currency': 'AED',
            'company_id': 1
        })

        self.assertIsNotNone(pool_id)

        pools = get_cash_pools(company_id=1)
        self.assertGreater(len(pools), 0)

    def test_collection_score_calculation(self):
        """Test collection risk score calculation."""
        from treasury_models import calculate_collection_score

        score = calculate_collection_score(customer_id=1, company_id=1)

        if score:
            self.assertIn('collection_probability', score)
            self.assertIn('risk_classification', score)
            self.assertIn('total_exposure', score)
            self.assertIn('overdue_exposure', score)

    def test_treasury_alert_creation(self):
        """Test treasury alert creation."""
        from treasury_models import create_treasury_alert, get_treasury_alerts

        alert_id = create_treasury_alert({
            'alert_type': 'low_balance',
            'alert_category': 'liquidity',
            'severity': 'high',
            'title': 'Test Alert',
            'message': 'This is a test alert',
            'amount': 50000,
            'currency': 'AED',
            'company_id': 1
        })

        self.assertIsNotNone(alert_id)

        alerts = get_treasury_alerts(company_id=1)
        self.assertGreater(len(alerts), 0)

    def test_treasury_control_creation(self):
        """Test treasury control creation."""
        from treasury_models import create_treasury_control, get_treasury_controls

        control_id = create_treasury_control({
            'control_name': 'test_control',
            'control_type': 'transfer_limit',
            'control_category': 'approval',
            'description': 'Test control',
            'threshold_value': 100000,
            'threshold_operator': 'greater_equal',
            'affected_operations': 'bank_transfer',
            'severity': 'high',
            'company_id': 1
        })

        self.assertIsNotNone(control_id)

        controls = get_treasury_controls(company_id=1)
        self.assertGreater(len(controls), 0)


class TestTreasuryRoutes(unittest.TestCase):
    """Test treasury route handlers."""

    def setUp(self):
        """Set up test client."""
        from flask import Flask
        from treasury_routes import treasury_bp

        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.register_blueprint(treasury_bp)
        self.client = self.app.test_client()

    def test_treasury_dashboard_route(self):
        """Test treasury dashboard route."""
        response = self.client.get('/finance/treasury/dashboard')
        self.assertIn(response.status_code, [200, 302])

    def test_cash_position_route(self):
        """Test cash position route."""
        response = self.client.get('/finance/treasury/cash-position')
        self.assertIn(response.status_code, [200, 302])

    def test_cash_position_by_currency_route(self):
        """Test cash position by currency route."""
        response = self.client.get('/finance/treasury/cash-position/by-currency')
        self.assertIn(response.status_code, [200, 302])

    def test_cash_position_by_bank_route(self):
        """Test cash position by bank route."""
        response = self.client.get('/finance/treasury/cash-position/by-bank')
        self.assertIn(response.status_code, [200, 302])

    def test_forecast_routes(self):
        """Test forecast routes."""
        routes = [
            '/finance/treasury/forecast',
            '/finance/treasury/forecast/7-day',
            '/finance/treasury/forecast/30-day',
            '/finance/treasury/forecast/90-day',
            '/finance/treasury/forecast/vs-actual'
        ]

        for route in routes:
            response = self.client.get(route)
            self.assertIn(response.status_code, [200, 302])

    def test_collections_routes(self):
        """Test collections routes."""
        routes = [
            '/finance/treasury/collections',
            '/finance/treasury/collections/calendar',
            '/finance/treasury/collections/overdue'
        ]

        for route in routes:
            response = self.client.get(route)
            self.assertIn(response.status_code, [200, 302])

    def test_payments_routes(self):
        """Test payments routes."""
        routes = [
            '/finance/treasury/payments',
            '/finance/treasury/payments/calendar',
            '/finance/treasury/payments/cash-requirement'
        ]

        for route in routes:
            response = self.client.get(route)
            self.assertIn(response.status_code, [200, 302])

    def test_bank_statement_routes(self):
        """Test bank statement routes."""
        routes = [
            '/finance/treasury/bank-statements',
            '/finance/treasury/bank-statements/import'
        ]

        for route in routes:
            response = self.client.get(route)
            self.assertIn(response.status_code, [200, 302])

    def test_payment_run_routes(self):
        """Test payment run routes."""
        routes = [
            '/finance/treasury/payment-runs',
            '/finance/treasury/payment-runs/create'
        ]

        for route in routes:
            response = self.client.get(route)
            self.assertIn(response.status_code, [200, 302])

    def test_fx_routes(self):
        """Test FX routes."""
        routes = [
            '/finance/treasury/fx-contracts',
            '/finance/treasury/fx-contracts/create',
            '/finance/treasury/fx-position'
        ]

        for route in routes:
            response = self.client.get(route)
            self.assertIn(response.status_code, [200, 302])

    def test_cash_pool_routes(self):
        """Test cash pool routes."""
        routes = [
            '/finance/treasury/cash-pools',
            '/finance/treasury/cash-pools/create'
        ]

        for route in routes:
            response = self.client.get(route)
            self.assertIn(response.status_code, [200, 302])


class TestTreasuryTranslations(unittest.TestCase):
    """Test treasury translations."""

    def test_get_treasury_translation(self):
        """Test getting treasury translation."""
        from treasury_translations import get_treasury_translation

        result = get_treasury_translation('treasury_dashboard', 'en')
        self.assertEqual(result, 'Treasury Dashboard')

    def test_get_all_treasury_translations(self):
        """Test getting all treasury translations."""
        from treasury_translations import get_all_treasury_translations

        translations = get_all_treasury_translations('en')

        self.assertIsInstance(translations, dict)
        self.assertIn('treasury_dashboard', translations)
        self.assertIn('cash_position', translations)
        self.assertIn('liquidity', translations)

    def test_all_languages_supported(self):
        """Test all 8 languages are supported."""
        from treasury_translations import TREASURY_TRANSLATIONS

        languages = ['en', 'fa', 'ar', 'ru', 'hi', 'es', 'zh', 'de']

        for lang in languages:
            self.assertIn(lang, TREASURY_TRANSLATIONS)

    def test_critical_translations_exist(self):
        """Test critical translation keys exist in all languages."""
        from treasury_translations import TREASURY_TRANSLATIONS

        critical_keys = [
            'treasury_dashboard',
            'cash_position',
            'cash_flow_forecast',
            'collections',
            'payments',
            'transfers',
            'reconciliation',
            'liquidity',
            'alerts',
            'bank_accounts'
        ]

        languages = ['en', 'fa', 'ar', 'ru', 'hi', 'es', 'zh', 'de']

        for lang in languages:
            for key in critical_keys:
                self.assertIn(key, TREASURY_TRANSLATIONS[lang],
                           f"Key {key} should exist in {lang}")


class TestTreasuryPermissions(unittest.TestCase):
    """Test treasury permissions."""

    def test_treasury_permissions_defined(self):
        """Test treasury permissions are defined in MODULE_PERMISSIONS."""
        from permissions import MODULE_PERMISSIONS

        self.assertIn('finance', MODULE_PERMISSIONS)
        finance_perms = MODULE_PERMISSIONS['finance']

        treasury_perms = [
            'treasury',
            'treasury_dashboard',
            'cash_position',
            'cash_forecast',
            'collections',
            'payments',
            'transfers',
            'petty_cash',
            'cash_boxes',
            'liquidity',
            'treasury_controls',
            'treasury_alerts',
            'treasury_reports',
            'treasury_settings',
            'treasury_audit',
            'bank_statements',
            'payment_runs',
            'fx_contracts',
            'cash_pools',
            'collection_scores',
            'counterparties'
        ]

        for perm in treasury_perms:
            self.assertIn(perm, finance_perms.get('resources', {}),
                         f"Permission {perm} should exist in finance resources")


if __name__ == '__main__':
    unittest.main()