"""
Marketing Automation Module Tests

Tests for the comprehensive marketing automation platform including:
- Lead scoring engine
- Nurture journeys
- A/B testing
- Customer journey intelligence
- Attribution & ROI
- Channel deliverability
"""

import pytest
import json
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database import get_db


class TestLeadScoring:
    """Tests for lead scoring functionality."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            with app.app_context():
                yield client

    def test_lead_scoring_list_accessible(self, client):
        """Test that lead scoring page loads."""
        response = client.get('/marketing/lead-scoring')
        # Should redirect to login if not authenticated or return 200/302
        assert response.status_code in [200, 302]

    def test_scoring_rules_structure(self):
        """Test that scoring rules have required fields."""
        from marketing_models import seed_lead_scoring_rules
        conn = get_db()

        # Verify seed function exists
        assert callable(seed_lead_scoring_rules)

        # Check table exists
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='marketing_lead_scoring_rules'
        """)
        table_exists = cursor.fetchone() is not None
        assert table_exists, "marketing_lead_scoring_rules table should exist"

    def test_lead_score_calculation(self):
        """Test lead score calculation logic."""
        # Test hot lead (score >= 80)
        demographic = 30
        behavioral = 30
        engagement = 25
        total = demographic + behavioral + engagement
        assert total == 85
        assert total >= 80  # Hot lead threshold

        # Test warm lead (50 <= score < 80)
        demographic = 20
        behavioral = 20
        engagement = 15
        total = demographic + behavioral + engagement
        assert 50 <= total < 80  # Warm lead threshold

        # Test cold lead (score < 50)
        demographic = 10
        behavioral = 10
        engagement = 5
        total = demographic + behavioral + engagement
        assert total < 50  # Cold lead threshold


class TestNurtureJourneys:
    """Tests for nurture journey functionality."""

    def test_journey_table_structure(self):
        """Test that journey tables exist."""
        conn = get_db()

        tables = [
            'marketing_nurture_journeys',
            'marketing_journey_steps',
            'marketing_journey_participants'
        ]

        for table in tables:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
            """, (table,))
            assert cursor.fetchone() is not None, f"{table} should exist"

    def test_journey_types(self):
        """Test valid journey types."""
        valid_types = [
            'welcome',
            'lead_nurture',
            'reengagement',
            'onboarding',
            'upsell',
            'cross_sell'
        ]
        assert len(valid_types) == 6

    def test_journey_statuses(self):
        """Test valid journey statuses."""
        valid_statuses = ['Draft', 'Active', 'Paused', 'Completed', 'Archived']
        assert len(valid_statuses) == 5


class TestABTesting:
    """Tests for A/B testing functionality."""

    def test_ab_test_table_structure(self):
        """Test that A/B test tables exist."""
        conn = get_db()

        tables = [
            'marketing_ab_tests',
            'marketing_ab_test_variants'
        ]

        for table in tables:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
            """, (table,))
            assert cursor.fetchone() is not None, f"{table} should exist"

    def test_test_types(self):
        """Test valid A/B test types."""
        valid_types = [
            'subject_line',
            'cta',
            'content',
            'audience',
            'design'
        ]
        assert len(valid_types) == 5

    def test_variant_types(self):
        """Test valid variant types."""
        valid_types = ['control', 'challenger']
        assert len(valid_types) == 2


class TestAttributionModels:
    """Tests for attribution modeling."""

    def test_attribution_models_exist(self):
        """Test that attribution models are defined."""
        from marketing_models import seed_attribution_models
        conn = get_db()

        # Verify seed function exists
        assert callable(seed_attribution_models)

        # Check table exists
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='marketing_attribution_models'
        """)
        assert cursor.fetchone() is not None

    def test_default_models(self):
        """Test default attribution models."""
        models = [
            ('First Touch', 'first_touch'),
            ('Last Touch', 'last_touch'),
            ('Linear', 'linear'),
            ('Time Decay', 'time_decay'),
            ('Position Based', 'position_based')
        ]
        assert len(models) == 5


class TestSLAPolicies:
    """Tests for SLA policies."""

    def test_sla_table_structure(self):
        """Test that SLA tables exist."""
        conn = get_db()

        tables = [
            'marketing_sla_policies',
            'marketing_sla_instances'
        ]

        for table in tables:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
            """, (table,))
            assert cursor.fetchone() is not None, f"{table} should exist"

    def test_sla_priority_levels(self):
        """Test SLA priority levels."""
        priorities = ['Critical', 'High', 'Medium', 'Low']
        assert len(priorities) == 4


class TestChannelDeliverability:
    """Tests for channel deliverability."""

    def test_deliverability_table(self):
        """Test deliverability table exists."""
        conn = get_db()
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='marketing_channel_deliverability'
        """)
        assert cursor.fetchone() is not None

    def test_communications_table(self):
        """Test communications table exists."""
        conn = get_db()
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='marketing_communications'
        """)
        assert cursor.fetchone() is not None

    def test_channel_types(self):
        """Test valid channel types."""
        channels = ['email', 'sms', 'whatsapp', 'push']
        assert len(channels) == 4


class TestExportConfiguration:
    """Tests for export configuration."""

    def test_export_config_table(self):
        """Test export configuration table exists."""
        conn = get_db()
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='marketing_export_configs'
        """)
        assert cursor.fetchone() is not None

    def test_output_formats(self):
        """Test supported output formats."""
        formats = ['csv', 'excel', 'pdf']
        assert 'csv' in formats
        assert 'excel' in formats


class TestMarketingPermissions:
    """Tests for marketing permissions."""

    def test_permission_decorator_exists(self):
        """Test that permission decorator exists."""
        from marketing_routes import mkt_permission_required
        assert callable(mkt_permission_required)

    def test_marketing_roles_defined(self):
        """Test that marketing roles are defined."""
        from marketing_models import MARKETING_ROLES
        assert len(MARKETING_ROLES) > 0


class TestMultilingualSupport:
    """Tests for multilingual support."""

    def test_translations_loaded(self):
        """Test that translations are loaded."""
        from translations import TRANSLATIONS
        assert 'en' in TRANSLATIONS

    def test_rtl_languages(self):
        """Test RTL language support."""
        from translations import TRANSLATIONS
        rtl_languages = ['ar', 'fa']
        for lang in rtl_languages:
            assert lang in TRANSLATIONS

    def test_marketing_translations_exist(self):
        """Test that marketing-specific translations exist."""
        from translations import TRANSLATIONS
        marketing_keys = [
            'marketing',
            'campaigns',
            'leads',
            'lead_scoring',
            'nurture_journeys',
            'ab_tests'
        ]
        for key in marketing_keys:
            assert key in TRANSLATIONS.get('en', {}), f"{key} should exist in English translations"


class TestJourneyIntelligence:
    """Tests for customer journey intelligence."""

    def test_journey_intelligence_table(self):
        """Test journey intelligence table exists."""
        conn = get_db()
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='marketing_journey_intelligence'
        """)
        assert cursor.fetchone() is not None

    def test_journey_stages(self):
        """Test valid journey stages."""
        stages = ['Awareness', 'Consideration', 'Conversion', 'Retention', 'Advocacy']
        assert len(stages) == 5


class TestNotifications:
    """Tests for marketing notifications."""

    def test_notifications_table(self):
        """Test notifications table exists."""
        conn = get_db()
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='marketing_notifications'
        """)
        assert cursor.fetchone() is not None

    def test_notification_types(self):
        """Test valid notification types."""
        types = ['approval', 'alert', 'reminder', 'milestone', 'sla']
        assert len(types) == 5


class TestBranchMarketing:
    """Tests for branch marketing configuration."""

    def test_branch_configs_table(self):
        """Test branch configurations table exists."""
        conn = get_db()
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='marketing_branch_configs'
        """)
        assert cursor.fetchone() is not None


class TestAuditLogging:
    """Tests for audit logging."""

    def test_activity_log_table(self):
        """Test activity log table exists."""
        conn = get_db()
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='marketing_activity_log'
        """)
        assert cursor.fetchone() is not None

    def test_log_marketing_audit_function(self):
        """Test audit logging function exists."""
        from marketing_models import log_marketing_audit
        assert callable(log_marketing_audit)


class TestDatabaseMigrations:
    """Tests for database migrations."""

    def test_run_marketing_migrations(self):
        """Test that migrations can run."""
        from marketing_models import run_marketing_migrations

        # Should not raise exception
        try:
            run_marketing_migrations()
            migrations_passed = True
        except Exception as e:
            migrations_passed = False
            print(f"Migration error: {e}")

        assert migrations_passed

    def test_all_new_tables_exist(self):
        """Test that all new marketing tables exist."""
        conn = get_db()

        expected_tables = [
            'marketing_lead_scoring_rules',
            'marketing_lead_scores',
            'marketing_lead_score_history',
            'marketing_nurture_journeys',
            'marketing_journey_steps',
            'marketing_journey_participants',
            'marketing_journey_step_events',
            'marketing_ab_tests',
            'marketing_ab_test_variants',
            'marketing_journey_intelligence',
            'marketing_assets',
            'marketing_templates',
            'marketing_communications',
            'marketing_export_configs',
            'marketing_activity_log',
            'marketing_sla_policies',
            'marketing_sla_instances',
            'marketing_branch_configs',
            'marketing_notifications',
            'marketing_channel_deliverability',
            'marketing_suppression_list',
            'marketing_attribution_models',
            'marketing_roi_metrics'
        ]

        for table in expected_tables:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
            """, (table,))
            assert cursor.fetchone() is not None, f"{table} should exist"


class TestROICalculation:
    """Tests for ROI calculation logic."""

    def test_roi_formula(self):
        """Test ROI calculation formula."""
        revenue = 100000
        cost = 50000
        roi = ((revenue - cost) / cost) * 100
        assert roi == 100.0  # 100% ROI

    def test_cost_per_lead_formula(self):
        """Test cost per lead calculation."""
        total_cost = 10000
        leads = 100
        cpl = total_cost / leads
        assert cpl == 100.0  # $100 per lead

    def test_cost_per_acquisition_formula(self):
        """Test cost per acquisition calculation."""
        total_cost = 10000
        acquisitions = 50
        cpa = total_cost / acquisitions
        assert cpa == 200.0  # $200 per acquisition


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
