"""
Marketing Module Database Models and Migrations
================================================
This file contains all marketing-related database table definitions and migration functions.
Tables are designed to be added to the existing SQLite database without conflicts.

Marketing Tables:
1. marketing_brands: Brand profiles and identity
2. marketing_market_intelligence: Market and competitor tracking
3. marketing_customer_segments: Customer segmentation for marketing
4. marketing_channels: Marketing channel definitions
5. marketing_campaigns: Campaign management
6. marketing_campaign_channels: Campaign-channel junction
7. marketing_advertisements: Advertisement management
8. marketing_content: Content and asset management
9. marketing_content_calendar: Content publishing calendar
10. marketing_leads: Lead management
11. marketing_lead_sources: Lead source definitions
12. marketing_funnel_stages: Funnel stage definitions
13. marketing_funnel_records: Funnel tracking records
14. marketing_offers: Offer/promotion management
15. marketing_budgets: Marketing budget plans
16. marketing_costs: Actual marketing costs
17. marketing_performance_metrics: KPI tracking
18. marketing_alerts: Alert definitions
19. marketing_recommendations: AI recommendations
20. marketing_attribution: Attribution tracking
21. marketing_audit_logs: Audit trail
22. marketing_settings: Configurable settings
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'warehouse.db'))


def get_db():
    """Get database connection with Row factory for dict-like access."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# =============================================================================
# MARKETING TABLE DEFINITIONS
# =============================================================================

MARKETING_TABLES = [
    # -------------------------------------------------------------------------
    # 1. Brand Profiles
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_brands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        trade_name TEXT,
        code TEXT UNIQUE,
        identity TEXT,
        positioning TEXT,
        tone_of_voice TEXT,
        brand_values TEXT,
        competitive_advantage TEXT,
        core_message TEXT,
        slogan TEXT,
        color_system TEXT,
        allowed_messaging TEXT,
        target_market TEXT,
        target_segments TEXT,
        brand_performance_notes TEXT,
        visual_identity_refs TEXT,
        logo_assets TEXT,
        approved_content_assets TEXT,
        linked_product_groups TEXT,
        linked_markets TEXT,
        status TEXT DEFAULT 'Active',
        notes TEXT,
        attachments TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 2. Market & Competitor Intelligence
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_market_intelligence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        market_name TEXT NOT NULL,
        market_type TEXT,
        region TEXT,
        country TEXT,
        city TEXT,
        is_local INTEGER DEFAULT 1,
        is_export INTEGER DEFAULT 0,
        is_retail INTEGER DEFAULT 0,
        is_wholesale INTEGER DEFAULT 0,
        is_b2b INTEGER DEFAULT 0,
        is_b2c INTEGER DEFAULT 0,
        competitor_name TEXT,
        competitor_scope TEXT,
        competitor_brands TEXT,
        competitor_pricing TEXT,
        competitor_ad_style TEXT,
        competitor_channels TEXT,
        competitor_strengths TEXT,
        competitor_weaknesses TEXT,
        estimated_market_share TEXT,
        market_gaps TEXT,
        market_threats TEXT,
        recommended_strategy TEXT,
        price_comparison TEXT,
        service_comparison TEXT,
        assortment_comparison TEXT,
        opportunity_areas TEXT,
        threats_requiring_response TEXT,
        status TEXT DEFAULT 'Active',
        notes TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 3. Customer Segments
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_customer_segments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE,
        description TEXT,
        segment_type TEXT,
        customer_type TEXT,
        is_retail INTEGER DEFAULT 0,
        is_wholesale INTEGER DEFAULT 0,
        is_local INTEGER DEFAULT 0,
        is_export INTEGER DEFAULT 0,
        country TEXT,
        city TEXT,
        industry TEXT,
        trade_type TEXT,
        purchase_volume_min REAL,
        purchase_volume_max REAL,
        purchase_frequency TEXT,
        loyalty_level TEXT,
        buying_power TEXT,
        price_sensitivity TEXT,
        brand_sensitivity TEXT,
        speed_sensitivity TEXT,
        persona_description TEXT,
        acquisition_channel TEXT,
        preferred_products TEXT,
        preferred_brands TEXT,
        typical_buying_time TEXT,
        typical_inquiry_time TEXT,
        content_type_preference TEXT,
        offer_type_preference TEXT,
        is_dynamic INTEGER DEFAULT 0,
        segment_rules TEXT,
        saved_audience_filters TEXT,
        campaign_ready_list TEXT,
        status TEXT DEFAULT 'Active',
        notes TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 4. Marketing Channels
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE,
        channel_type TEXT NOT NULL,
        description TEXT,
        owner_user_id INTEGER,
        budget DECIMAL(12,2) DEFAULT 0,
        target_audience TEXT,
        expected_kpi TEXT,
        actual_kpi TEXT,
        efficiency_score INTEGER,
        status TEXT DEFAULT 'Active',
        notes TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (owner_user_id) REFERENCES users(id),
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 5. Campaigns
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_campaigns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE,
        campaign_type TEXT NOT NULL,
        goal TEXT,
        start_date DATE,
        end_date DATE,
        target_market TEXT,
        target_segment_id INTEGER,
        target_brand_id INTEGER,
        target_products TEXT,
        budget DECIMAL(12,2) DEFAULT 0,
        actual_cost DECIMAL(12,2) DEFAULT 0,
        owner_user_id INTEGER,
        main_message TEXT,
        sales_offer TEXT,
        ad_copy TEXT,
        media_assets TEXT,
        landing_page_url TEXT,
        posting_frequency TEXT,
        budget_per_channel TEXT,
        target_kpi TEXT,
        final_results TEXT,
        status TEXT DEFAULT 'Draft',
        approval_state TEXT DEFAULT 'Pending',
        approved_by_user_id INTEGER,
        approved_at DATETIME,
        linked_lead_source TEXT,
        leads_generated INTEGER DEFAULT 0,
        inquiries_generated INTEGER DEFAULT 0,
        calls_generated INTEGER DEFAULT 0,
        whatsapp_generated INTEGER DEFAULT 0,
        quotations_generated INTEGER DEFAULT 0,
        purchases_generated INTEGER DEFAULT 0,
        repeat_purchases INTEGER DEFAULT 0,
        sales_generated DECIMAL(12,2) DEFAULT 0,
        profit_generated DECIMAL(12,2) DEFAULT 0,
        new_customers_acquired INTEGER DEFAULT 0,
        reactivated_customers INTEGER DEFAULT 0,
        notes TEXT,
        attachments TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (target_segment_id) REFERENCES marketing_customer_segments(id),
        FOREIGN KEY (target_brand_id) REFERENCES marketing_brands(id),
        FOREIGN KEY (owner_user_id) REFERENCES users(id),
        FOREIGN KEY (approved_by_user_id) REFERENCES users(id),
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 6. Campaign-Channel Junction
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_campaign_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id INTEGER NOT NULL,
        channel_id INTEGER NOT NULL,
        budget_allocated DECIMAL(12,2) DEFAULT 0,
        actual_spend DECIMAL(12,2) DEFAULT 0,
        posts_planned INTEGER DEFAULT 0,
        posts_published INTEGER DEFAULT 0,
        leads_generated INTEGER DEFAULT 0,
        inquiries_generated INTEGER DEFAULT 0,
        sales_generated DECIMAL(12,2) DEFAULT 0,
        status TEXT DEFAULT 'Active',
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (campaign_id) REFERENCES marketing_campaigns(id) ON DELETE CASCADE,
        FOREIGN KEY (channel_id) REFERENCES marketing_channels(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 7. Advertisements
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_advertisements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        advertisement_type TEXT NOT NULL,
        objective TEXT,
        channel_id INTEGER,
        publish_date DATE,
        placement TEXT,
        content_text TEXT,
        cta_text TEXT,
        cta_url TEXT,
        budget DECIMAL(12,2) DEFAULT 0,
        actual_cost DECIMAL(12,2) DEFAULT 0,
        audience TEXT,
        approving_manager_id INTEGER,
        status TEXT DEFAULT 'Draft',
        linked_campaign_id INTEGER,
        linked_brand_id INTEGER,
        linked_products TEXT,
        validity_date DATE,
        reach INTEGER DEFAULT 0,
        impressions INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        ctr DECIMAL(5,2) DEFAULT 0,
        calls_generated INTEGER DEFAULT 0,
        whatsapp_generated INTEGER DEFAULT 0,
        inquiries_generated INTEGER DEFAULT 0,
        attributed_leads INTEGER DEFAULT 0,
        attributed_inquiries INTEGER DEFAULT 0,
        attributed_sales DECIMAL(12,2) DEFAULT 0,
        attributed_profit DECIMAL(12,2) DEFAULT 0,
        notes TEXT,
        attachments TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (channel_id) REFERENCES marketing_channels(id),
        FOREIGN KEY (approving_manager_id) REFERENCES users(id),
        FOREIGN KEY (linked_campaign_id) REFERENCES marketing_campaigns(id),
        FOREIGN KEY (linked_brand_id) REFERENCES marketing_brands(id),
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 8. Content Management
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_content (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT NOT NULL,
        title TEXT,
        content_objective TEXT,
        target_audience TEXT,
        channel_id INTEGER,
        content_format TEXT,
        content_text TEXT,
        publish_date DATE,
        content_creator_id INTEGER,
        approver_id INTEGER,
        linked_campaign_id INTEGER,
        linked_brand_id INTEGER,
        linked_products TEXT,
        linked_market TEXT,
        status TEXT DEFAULT 'Draft',
        reach INTEGER DEFAULT 0,
        impressions INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        ctr DECIMAL(5,2) DEFAULT 0,
        engagement INTEGER DEFAULT 0,
        shares INTEGER DEFAULT 0,
        saves INTEGER DEFAULT 0,
        comments INTEGER DEFAULT 0,
        watch_time INTEGER DEFAULT 0,
        messages_generated INTEGER DEFAULT 0,
        purchases_generated INTEGER DEFAULT 0,
        notes TEXT,
        attachments TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (channel_id) REFERENCES marketing_channels(id),
        FOREIGN KEY (content_creator_id) REFERENCES users(id),
        FOREIGN KEY (approver_id) REFERENCES users(id),
        FOREIGN KEY (linked_campaign_id) REFERENCES marketing_campaigns(id),
        FOREIGN KEY (linked_brand_id) REFERENCES marketing_brands(id),
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 9. Content Calendar
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_content_calendar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content_id INTEGER,
        planned_date DATE,
        planned_time TEXT,
        actual_publish_date DATETIME,
        channel_id INTEGER,
        content_topic TEXT,
        content_format TEXT,
        content_title TEXT,
        linked_campaign_id INTEGER,
        linked_brand_id INTEGER,
        linked_products TEXT,
        assigned_to_user_id INTEGER,
        approver_id INTEGER,
        status TEXT DEFAULT 'Planned',
        notes TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (content_id) REFERENCES marketing_content(id) ON DELETE SET NULL,
        FOREIGN KEY (channel_id) REFERENCES marketing_channels(id),
        FOREIGN KEY (linked_campaign_id) REFERENCES marketing_campaigns(id),
        FOREIGN KEY (linked_brand_id) REFERENCES marketing_brands(id),
        FOREIGN KEY (assigned_to_user_id) REFERENCES users(id),
        FOREIGN KEY (approver_id) REFERENCES users(id),
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 10. Lead Sources
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_lead_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE,
        source_type TEXT,
        channel_id INTEGER,
        description TEXT,
        cost_per_lead DECIMAL(10,2) DEFAULT 0,
        leads_count INTEGER DEFAULT 0,
        conversion_rate DECIMAL(5,2) DEFAULT 0,
        status TEXT DEFAULT 'Active',
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (channel_id) REFERENCES marketing_channels(id),
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 11. Leads
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_name TEXT NOT NULL,
        phone TEXT,
        whatsapp TEXT,
        email TEXT,
        city TEXT,
        country TEXT,
        industry TEXT,
        trade_type TEXT,
        source_id INTEGER,
        product_interest TEXT,
        brand_interest TEXT,
        customer_type TEXT,
        importance_level TEXT DEFAULT 'Medium',
        lead_status TEXT DEFAULT 'New',
        assigned_salesperson_id INTEGER,
        follow_up_date DATE,
        follow_up_notes TEXT,
        related_campaign_id INTEGER,
        related_advertisement_id INTEGER,
        related_content_id INTEGER,
        related_market TEXT,
        estimated_value DECIMAL(12,2) DEFAULT 0,
        conversion_probability INTEGER DEFAULT 0,
        lost_reason TEXT,
        converted_to_customer_id INTEGER,
        converted_to_inquiry_id INTEGER,
        converted_at DATETIME,
        notes TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (source_id) REFERENCES marketing_lead_sources(id),
        FOREIGN KEY (assigned_salesperson_id) REFERENCES users(id),
        FOREIGN KEY (related_campaign_id) REFERENCES marketing_campaigns(id),
        FOREIGN KEY (related_advertisement_id) REFERENCES marketing_advertisements(id),
        FOREIGN KEY (related_content_id) REFERENCES marketing_content(id),
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 12. Funnel Stages
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_funnel_stages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE,
        stage_order INTEGER NOT NULL,
        stage_type TEXT,
        description TEXT,
        conversion_target_days INTEGER,
        status TEXT DEFAULT 'Active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 13. Funnel Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_funnel_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER,
        stage_id INTEGER NOT NULL,
        entering_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        exiting_date DATETIME,
        time_spent_hours INTEGER DEFAULT 0,
        drop_off_reason TEXT,
        follow_up_owner_id INTEGER,
        potential_value DECIMAL(12,2) DEFAULT 0,
        acquisition_cost DECIMAL(10,2) DEFAULT 0,
        attributed_campaign_id INTEGER,
        attributed_channel_id INTEGER,
        attributed_content_id INTEGER,
        attributed_ad_id INTEGER,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (lead_id) REFERENCES marketing_leads(id) ON DELETE CASCADE,
        FOREIGN KEY (stage_id) REFERENCES marketing_funnel_stages(id),
        FOREIGN KEY (follow_up_owner_id) REFERENCES users(id),
        FOREIGN KEY (attributed_campaign_id) REFERENCES marketing_campaigns(id),
        FOREIGN KEY (attributed_channel_id) REFERENCES marketing_channels(id),
        FOREIGN KEY (attributed_content_id) REFERENCES marketing_content(id),
        FOREIGN KEY (attributed_ad_id) REFERENCES marketing_advertisements(id)
    )""",

    # -------------------------------------------------------------------------
    # 14. Offers & Promotions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_offers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        offer_number TEXT UNIQUE,
        offer_date DATE,
        target_customer TEXT,
        customer_type TEXT,
        products_included TEXT,
        brands_included TEXT,
        discount_percentage DECIMAL(5,2) DEFAULT 0,
        validity_period DATE,
        responsible_salesperson_id INTEGER,
        offer_result TEXT,
        linked_campaign_id INTEGER,
        linked_channel_id INTEGER,
        linked_lead_id INTEGER,
        is_opened INTEGER DEFAULT 0,
        opened_at DATETIME,
        call_generated INTEGER DEFAULT 0,
        purchase_generated INTEGER DEFAULT 0,
        sales_value_generated DECIMAL(12,2) DEFAULT 0,
        profit_value_generated DECIMAL(12,2) DEFAULT 0,
        status TEXT DEFAULT 'Sent',
        notes TEXT,
        attachments TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (responsible_salesperson_id) REFERENCES users(id),
        FOREIGN KEY (linked_campaign_id) REFERENCES marketing_campaigns(id),
        FOREIGN KEY (linked_channel_id) REFERENCES marketing_channels(id),
        FOREIGN KEY (linked_lead_id) REFERENCES marketing_leads(id),
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 15. Budget Plans
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        budget_type TEXT NOT NULL,
        period_type TEXT NOT NULL,
        period_start DATE,
        period_end DATE,
        total_budget DECIMAL(12,2) DEFAULT 0,
        branding_budget DECIMAL(12,2) DEFAULT 0,
        digital_budget DECIMAL(12,2) DEFAULT 0,
        print_budget DECIMAL(12,2) DEFAULT 0,
        exhibition_budget DECIMAL(12,2) DEFAULT 0,
        content_budget DECIMAL(12,2) DEFAULT 0,
        approved_budget DECIMAL(12,2) DEFAULT 0,
        actual_spent DECIMAL(12,2) DEFAULT 0,
        variance DECIMAL(12,2) DEFAULT 0,
        approved_by_user_id INTEGER,
        approved_at DATETIME,
        status TEXT DEFAULT 'Draft',
        notes TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (approved_by_user_id) REFERENCES users(id),
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 16. Cost Entries
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_costs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cost_date DATE NOT NULL,
        cost_type TEXT NOT NULL,
        description TEXT,
        amount DECIMAL(12,2) NOT NULL,
        currency TEXT DEFAULT 'AED',
        linked_campaign_id INTEGER,
        linked_channel_id INTEGER,
        linked_brand_id INTEGER,
        linked_market TEXT,
        linked_segment_id INTEGER,
        invoice_reference TEXT,
        vendor_name TEXT,
        receipt_path TEXT,
        status TEXT DEFAULT 'Pending',
        approved_by_user_id INTEGER,
        approved_at DATETIME,
        notes TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (linked_campaign_id) REFERENCES marketing_campaigns(id),
        FOREIGN KEY (linked_channel_id) REFERENCES marketing_channels(id),
        FOREIGN KEY (linked_brand_id) REFERENCES marketing_brands(id),
        FOREIGN KEY (linked_segment_id) REFERENCES marketing_customer_segments(id),
        FOREIGN KEY (approved_by_user_id) REFERENCES users(id),
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 17. Performance Metrics
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_performance_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        metric_date DATE NOT NULL,
        metric_type TEXT NOT NULL,
        entity_type TEXT,
        entity_id INTEGER,
        entity_name TEXT,
        metric_name TEXT NOT NULL,
        metric_value DECIMAL(12,4) DEFAULT 0,
        metric_unit TEXT,
        target_value DECIMAL(12,4),
        achievement_rate DECIMAL(5,2),
        period_start DATE,
        period_end DATE,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (entity_id) REFERENCES marketing_campaigns(id)
    )""",

    # -------------------------------------------------------------------------
    # 18. Marketing Alerts
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_type TEXT NOT NULL,
        alert_title TEXT NOT NULL,
        alert_message TEXT,
        severity TEXT DEFAULT 'Info',
        entity_type TEXT,
        entity_id INTEGER,
        entity_name TEXT,
        linked_campaign_id INTEGER,
        linked_channel_id INTEGER,
        linked_lead_id INTEGER,
        is_resolved INTEGER DEFAULT 0,
        resolved_at DATETIME,
        resolved_by_user_id INTEGER,
        resolution_notes TEXT,
        alert_data TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (linked_campaign_id) REFERENCES marketing_campaigns(id),
        FOREIGN KEY (linked_channel_id) REFERENCES marketing_channels(id),
        FOREIGN KEY (linked_lead_id) REFERENCES marketing_leads(id),
        FOREIGN KEY (resolved_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 19. Recommendations
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recommendation_type TEXT NOT NULL,
        recommendation_title TEXT NOT NULL,
        recommendation_text TEXT,
        priority TEXT DEFAULT 'Medium',
        target_entity_type TEXT,
        target_entity_id INTEGER,
        target_entity_name TEXT,
        expected_impact TEXT,
        confidence_score DECIMAL(5,2),
        action_items TEXT,
        status TEXT DEFAULT 'Open',
        implemented_at DATETIME,
        implemented_by_user_id INTEGER,
        rejected_reason TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (implemented_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 20. Attribution Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_attribution (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        lead_id INTEGER,
        campaign_id INTEGER,
        channel_id INTEGER,
        content_id INTEGER,
        advertisement_id INTEGER,
        offer_id INTEGER,
        attribution_model TEXT,
        touchpoint_type TEXT,
        touchpoint_date DATETIME,
        revenue_generated DECIMAL(12,2) DEFAULT 0,
        profit_generated DECIMAL(12,2) DEFAULT 0,
        weight_percentage DECIMAL(5,2) DEFAULT 100,
        is_conversion INTEGER DEFAULT 0,
        conversion_value DECIMAL(12,2) DEFAULT 0,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(id),
        FOREIGN KEY (lead_id) REFERENCES marketing_leads(id),
        FOREIGN KEY (campaign_id) REFERENCES marketing_campaigns(id),
        FOREIGN KEY (channel_id) REFERENCES marketing_channels(id),
        FOREIGN KEY (content_id) REFERENCES marketing_content(id),
        FOREIGN KEY (advertisement_id) REFERENCES marketing_advertisements(id),
        FOREIGN KEY (offer_id) REFERENCES marketing_offers(id)
    )""",

    # -------------------------------------------------------------------------
    # 21. Audit Logs
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,
        entity_id INTEGER,
        action_type TEXT NOT NULL,
        field_name TEXT,
        old_value TEXT,
        new_value TEXT,
        change_reason TEXT,
        actor_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (actor_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 22. Marketing Settings
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_key TEXT NOT NULL UNIQUE,
        setting_value TEXT,
        setting_type TEXT,
        category TEXT,
        description TEXT,
        is_active INTEGER DEFAULT 1,
        updated_by_user_id INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (updated_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 23. Seasonality & Timing
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_seasonality (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        season_type TEXT,
        start_month INTEGER,
        end_month INTEGER,
        start_day INTEGER DEFAULT 1,
        end_day INTEGER DEFAULT 31,
        is_peak INTEGER DEFAULT 0,
        best_for_campaign_type TEXT,
        best_for_content_type TEXT,
        best_for_channel TEXT,
        notes TEXT,
        status TEXT DEFAULT 'Active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 24. Marketing Roles
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role_name TEXT NOT NULL,
        role_code TEXT UNIQUE,
        description TEXT,
        is_system_role INTEGER DEFAULT 0,
        permissions_json TEXT,
        menu_access_json TEXT,
        can_view_financials INTEGER DEFAULT 0,
        can_approve INTEGER DEFAULT 0,
        can_publish INTEGER DEFAULT 0,
        can_manage_team INTEGER DEFAULT 0,
        can_view_all_data INTEGER DEFAULT 0,
        status TEXT DEFAULT 'Active',
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 25. Marketing User Role Assignments
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS marketing_user_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        marketing_role_id INTEGER NOT NULL,
        assigned_by_id INTEGER,
        assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (marketing_role_id) REFERENCES marketing_roles(id),
        FOREIGN KEY (assigned_by_id) REFERENCES users(id)
    )""",
]


# =============================================================================
# DEFAULT MARKETING PERMISSIONS
# =============================================================================

MARKETING_DEFAULT_PERMISSIONS = {
    'all_marketing': 'Full access to all marketing modules and functions',
    'view_dashboard': 'View marketing dashboard and KPIs',
    'view_brands': 'View brand profiles',
    'manage_brands': 'Create, edit, and delete brand profiles',
    'view_market_intel': 'View market intelligence data',
    'manage_market_intel': 'Create, edit, and delete market intelligence entries',
    'view_segments': 'View customer segments',
    'manage_segments': 'Create, edit, and delete customer segments',
    'view_channels': 'View marketing channels',
    'manage_channels': 'Create, edit, and delete marketing channels',
    'view_campaigns': 'View marketing campaigns',
    'manage_campaigns': 'Create, edit, and delete marketing campaigns',
    'approve_campaigns': 'Approve marketing campaigns',
    'view_advertisements': 'View advertisements',
    'manage_advertisements': 'Create, edit, and delete advertisements',
    'view_content': 'View content library',
    'manage_content': 'Create, edit, and delete content',
    'publish_content': 'Publish content to channels',
    'view_leads': 'View leads',
    'manage_leads': 'Create, edit, and delete leads',
    'assign_leads': 'Assign leads to team members',
    'view_funnel': 'View funnel analytics',
    'manage_funnel': 'Manage funnel stages and tracking',
    'view_offers': 'View offers and promotions',
    'manage_offers': 'Create, edit, and delete offers',
    'view_budgets': 'View marketing budgets',
    'manage_budgets': 'Create, edit, and delete marketing budgets',
    'view_costs': 'View marketing costs',
    'manage_costs': 'Create, edit, and delete marketing costs',
    'view_analytics': 'View analytics and reports',
    'manage_alerts': 'Manage marketing alerts',
    'manage_recommendations': 'Manage AI recommendations',
    'manage_settings': 'Manage marketing settings',
    'view_reports': 'View and export reports',
}

MARKETING_DEFAULT_ROLES = [
    {
        'role_name': 'Marketing Admin',
        'role_code': 'MKT_ADMIN',
        'description': 'Full access to all marketing functions',
        'is_system_role': 1,
        'permissions_json': json.dumps(['all_marketing']),
        'can_view_financials': 1,
        'can_approve': 1,
        'can_publish': 1,
        'can_manage_team': 1,
        'can_view_all_data': 1,
    },
    {
        'role_name': 'Marketing Manager',
        'role_code': 'MKT_MANAGER',
        'description': 'Can manage campaigns, content, and leads',
        'is_system_role': 1,
        'permissions_json': json.dumps([
            'view_dashboard', 'view_brands', 'manage_brands',
            'view_market_intel', 'manage_market_intel',
            'view_segments', 'manage_segments',
            'view_channels', 'manage_channels',
            'view_campaigns', 'manage_campaigns',
            'view_advertisements', 'manage_advertisements',
            'view_content', 'manage_content', 'publish_content',
            'view_leads', 'manage_leads', 'assign_leads',
            'view_funnel', 'manage_funnel',
            'view_offers', 'manage_offers',
            'view_budgets', 'manage_budgets',
            'view_costs', 'manage_costs',
            'view_analytics', 'manage_alerts',
            'manage_recommendations',
            'view_reports',
        ]),
        'can_view_financials': 1,
        'can_approve': 1,
        'can_publish': 1,
        'can_manage_team': 1,
        'can_view_all_data': 1,
    },
    {
        'role_name': 'Marketing Specialist',
        'role_code': 'MKT_SPECIALIST',
        'description': 'Can create and manage campaigns and content',
        'is_system_role': 1,
        'permissions_json': json.dumps([
            'view_dashboard',
            'view_brands',
            'view_market_intel',
            'view_segments',
            'view_channels',
            'view_campaigns', 'manage_campaigns',
            'view_advertisements', 'manage_advertisements',
            'view_content', 'manage_content', 'publish_content',
            'view_leads', 'manage_leads',
            'view_funnel',
            'view_offers', 'manage_offers',
            'view_analytics',
            'view_reports',
        ]),
        'can_view_financials': 0,
        'can_approve': 0,
        'can_publish': 1,
        'can_manage_team': 0,
        'can_view_all_data': 0,
    },
    {
        'role_name': 'Lead Manager',
        'role_code': 'MKT_LEAD_MGR',
        'description': 'Focused on lead management and conversion',
        'is_system_role': 1,
        'permissions_json': json.dumps([
            'view_dashboard',
            'view_brands',
            'view_segments',
            'view_channels',
            'view_campaigns',
            'view_leads', 'manage_leads', 'assign_leads',
            'view_funnel', 'manage_funnel',
            'view_offers',
            'view_analytics',
        ]),
        'can_view_financials': 0,
        'can_approve': 0,
        'can_publish': 0,
        'can_manage_team': 0,
        'can_view_all_data': 0,
    },
    {
        'role_name': 'Marketing Viewer',
        'role_code': 'MKT_VIEWER',
        'description': 'Read-only access to marketing data',
        'is_system_role': 1,
        'permissions_json': json.dumps([
            'view_dashboard',
            'view_brands',
            'view_market_intel',
            'view_segments',
            'view_channels',
            'view_campaigns',
            'view_advertisements',
            'view_content',
            'view_leads',
            'view_funnel',
            'view_offers',
            'view_budgets',
            'view_costs',
            'view_analytics',
            'view_reports',
        ]),
        'can_view_financials': 0,
        'can_approve': 0,
        'can_publish': 0,
        'can_manage_team': 0,
        'can_view_all_data': 0,
    },
]


# =============================================================================
# MIGRATION RUNNER
# =============================================================================

def run_marketing_migrations():
    """Run all marketing table migrations."""
    conn = get_db()
    try:
        for table_sql in MARKETING_TABLES:
            conn.executescript(table_sql)
        conn.commit()

        # Seed default funnel stages
        seed_funnel_stages(conn)

        # Seed default lead sources
        seed_lead_sources(conn)

        # Seed default marketing channels
        seed_marketing_channels(conn)

        # Seed default marketing settings
        seed_marketing_settings(conn)

        # Seed default seasonality
        seed_seasonality(conn)

        # Seed default marketing roles
        seed_marketing_roles(conn)

    finally:
        conn.close()


def seed_funnel_stages(conn):
    """Seed default funnel stages if not exist."""
    existing = conn.execute("SELECT COUNT(*) FROM marketing_funnel_stages").fetchone()[0]
    if existing > 0:
        return
    
    stages = [
        ('Reach', 'REACH', 1, 'Awareness', 'Number of people who saw the brand/content', 24),
        ('Awareness', 'AWARENESS', 2, 'Interest', 'People who engaged with content', 48),
        ('Interest', 'INTEREST', 3, 'Inquiry', 'People who asked questions or inquired', 72),
        ('Inquiry', 'INQUIRY', 4, 'Lead', 'Formal inquiry or contact request', 96),
        ('Lead', 'LEAD', 5, 'Quotation', 'Qualified lead with contact details', 120),
        ('Quotation', 'QUOTATION', 6, 'Negotiation', 'Quotation sent to customer', 168),
        ('Negotiation', 'NEGOTIATION', 7, 'Purchase', 'Active negotiation phase', 240),
        ('Purchase', 'PURCHASE', 8, 'RepeatPurchase', 'Purchase completed', 0),
        ('Repeat Purchase', 'REPEAT_PURCHASE', 9, 'Loyalty', 'Customer made repeat purchase', 720),
        ('Loyalty', 'LOYALTY', 10, 'Advocacy', 'Loyal customer who refers others', 2160),
    ]
    
    for name, code, order, stype, desc, days in stages:
        conn.execute(
            "INSERT OR IGNORE INTO marketing_funnel_stages (name, code, stage_order, stage_type, description, conversion_target_days) VALUES (?, ?, ?, ?, ?, ?)",
            (name, code, order, stype, desc, days)
        )


def seed_lead_sources(conn):
    """Seed default lead sources if not exist."""
    existing = conn.execute("SELECT COUNT(*) FROM marketing_lead_sources").fetchone()[0]
    if existing > 0:
        return
    
    sources = [
        ('Google Search', 'SRC-GOOGLE', 'Search Engine', None, 'Leads from Google search ads'),
        ('Instagram', 'SRC-INSTAGRAM', 'Social Media', None, 'Leads from Instagram posts/ads'),
        ('WhatsApp', 'SRC-WHATSAPP', 'Direct Messaging', None, 'Leads via WhatsApp'),
        ('Direct Call', 'SRC-CALL', 'Direct', None, 'Incoming phone calls'),
        ('Exhibition', 'SRC-EXHIBITION', 'Event', None, 'Leads from trade exhibitions'),
        ('Customer Referral', 'SRC-REFERRAL', 'Referral', None, 'Referrals from existing customers'),
        ('Website', 'SRC-WEBSITE', 'Digital', None, 'Website contact form inquiries'),
        ('Paid Ad', 'SRC-PAID-AD', 'Advertising', None, 'Paid advertisement clicks'),
        ('Field Marketer', 'SRC-FIELD', 'Field', None, 'Field marketing activities'),
        ('Email Marketing', 'SRC-EMAIL', 'Digital', None, 'Email campaign responses'),
        ('Offer List', 'SRC-OFFER', 'Direct', None, 'Responses to offer lists'),
        ('Facebook', 'SRC-FACEBOOK', 'Social Media', None, 'Leads from Facebook'),
        ('LinkedIn', 'SRC-LINKEDIN', 'Social Media', None, 'B2B leads from LinkedIn'),
        ('YouTube', 'SRC-YOUTUBE', 'Video', None, 'Leads from YouTube content'),
        ('TikTok', 'SRC-TIKTOK', 'Social Media', None, 'Leads from TikTok'),
        ('SMS', 'SRC-SMS', 'Direct', None, 'SMS marketing responses'),
        ('Brochure', 'SRC-BROCHURE', 'Print', None, 'Brochure/catalog responses'),
        ('Campaign', 'SRC-CAMPAIGN', 'Campaign', None, 'Linked to specific campaign'),
    ]
    
    for name, code, stype, chan, desc in sources:
        conn.execute(
            "INSERT OR IGNORE INTO marketing_lead_sources (name, code, source_type, channel_id, description) VALUES (?, ?, ?, ?, ?)",
            (name, code, stype, chan, desc)
        )


def seed_marketing_channels(conn):
    """Seed default marketing channels if not exist."""
    existing = conn.execute("SELECT COUNT(*) FROM marketing_channels").fetchone()[0]
    if existing > 0:
        return
    
    channels = [
        ('Website', 'CH-WEBSITE', 'Digital', 'Company website with contact forms'),
        ('Google Search', 'CH-GOOGLE-SEARCH', 'Digital', 'Google search engine marketing'),
        ('Google Maps', 'CH-GOOGLE-MAPS', 'Digital', 'Google Maps presence and ads'),
        ('Google Ads', 'CH-GOOGLE-ADS', 'Digital', 'Paid Google advertising'),
        ('SEO', 'CH-SEO', 'Digital', 'Search engine optimization'),
        ('Instagram', 'CH-INSTAGRAM', 'Social Media', 'Instagram posts and stories'),
        ('Facebook', 'CH-FACEBOOK', 'Social Media', 'Facebook page and ads'),
        ('LinkedIn', 'CH-LINKEDIN', 'Social Media', 'LinkedIn professional network'),
        ('YouTube', 'CH-YOUTUBE', 'Video', 'YouTube channel and ads'),
        ('TikTok', 'CH-TIKTOK', 'Social Media', 'TikTok short video content'),
        ('Email Marketing', 'CH-EMAIL', 'Digital', 'Email campaigns and newsletters'),
        ('WhatsApp Marketing', 'CH-WHATSAPP', 'Messaging', 'WhatsApp business marketing'),
        ('Telegram', 'CH-TELEGRAM', 'Messaging', 'Telegram channel and groups'),
        ('SMS Marketing', 'CH-SMS', 'Direct', 'SMS text message marketing'),
        ('Field Visits', 'CH-FIELD', 'Offline', 'In-person field marketing visits'),
        ('Direct Calls', 'CH-CALLS', 'Direct', 'Outbound and inbound call campaigns'),
        ('Exhibitions', 'CH-EXHIBITIONS', 'Event', 'Trade shows and exhibitions'),
        ('Brochures', 'CH-BROCHURES', 'Print', 'Printed promotional materials'),
        ('Catalogs', 'CH-CATALOGS', 'Print', 'Product catalogs'),
        ('Business Cards', 'CH-BIZCARDS', 'Print', 'Business card distribution'),
        ('Banners', 'CH-BANNERS', 'Print', 'Outdoor banners and signage'),
        ('Stands', 'CH-STANDS', 'Event', 'Promotional stands at events'),
        ('Outdoor Advertising', 'CH-OUTDOOR', 'Print', 'Billboard and outdoor ads'),
        ('Packaging Print', 'CH-PACKAGING', 'Print', 'Printed packaging materials'),
        ('Market Partner', 'CH-PARTNER', 'Partnership', 'Partner channel marketing'),
        ('Referral Program', 'CH-REFERRAL', 'Direct', 'Customer referral program'),
    ]
    
    for name, code, ctype, desc in channels:
        conn.execute(
            "INSERT OR IGNORE INTO marketing_channels (name, code, channel_type, description) VALUES (?, ?, ?, ?)",
            (name, code, ctype, desc)
        )


def seed_marketing_settings(conn):
    """Seed default marketing settings if not exist."""
    existing = conn.execute("SELECT COUNT(*) FROM marketing_settings").fetchone()[0]
    if existing > 0:
        return
    
    settings = [
        # Campaign Types
        ('campaign_type_sales_growth', 'Sales Growth Campaign', 'string', 'campaign_types', 'Campaign focused on increasing sales'),
        ('campaign_type_brand_awareness', 'Brand Awareness Campaign', 'string', 'campaign_types', 'Campaign to build brand visibility'),
        ('campaign_type_discount', 'Discount Campaign', 'string', 'campaign_types', 'Price discount promotional campaign'),
        ('campaign_type_seasonal', 'Seasonal/Occasion Campaign', 'string', 'campaign_types', 'Ramadan, Eid, summer, etc.'),
        ('campaign_type_reactivation', 'Customer Reactivation Campaign', 'string', 'campaign_types', 'Target inactive customers'),
        ('campaign_type_new_customer', 'New Customer Acquisition', 'string', 'campaign_types', 'Target new customer segments'),
        ('campaign_type_new_product', 'New Product Introduction', 'string', 'campaign_types', 'Launch new product/brand'),
        ('campaign_type_liquidation', 'Stock Liquidation Campaign', 'string', 'campaign_types', 'Clear slow/dead stock'),
        ('campaign_type_contact_gen', 'Contact Generation Campaign', 'string', 'campaign_types', 'Generate calls, WhatsApp, inquiries'),
        
        # Advertisement Types
        ('ad_type_branding', 'Branding Ad', 'string', 'ad_types', 'Brand image and awareness ad'),
        ('ad_type_direct_sales', 'Direct Sales Ad', 'string', 'ad_types', 'Direct response sales ad'),
        ('ad_type_discount', 'Discount Ad', 'string', 'ad_types', 'Discount/promotion ad'),
        ('ad_type_product', 'Product-Specific Ad', 'string', 'ad_types', 'Single product highlight'),
        ('ad_type_service', 'Service Ad', 'string', 'ad_types', 'Service offering ad'),
        ('ad_type_speed_delivery', 'Speed/Delivery Ad', 'string', 'ad_types', 'Warehouse and delivery speed'),
        ('ad_type_trust', 'Trust-Building Ad', 'string', 'ad_types', 'Customer testimonials, reliability'),
        ('ad_type_special_offer', 'Special Offer Ad', 'string', 'ad_types', 'Limited time special offer'),
        
        # Content Types
        ('content_type_product_intro', 'Product Introduction', 'string', 'content_types', 'New product announcement'),
        ('content_type_brand_intro', 'Brand Introduction', 'string', 'content_types', 'Brand story and values'),
        ('content_type_technical', 'Technical Education', 'string', 'content_types', 'Technical tips and guides'),
        ('content_type_comparison', 'Brand Comparison', 'string', 'content_types', 'Comparison with competitors'),
        ('content_type_service_intro', 'Services Introduction', 'string', 'content_types', 'Service capabilities'),
        ('content_type_company_intro', 'Company Introduction', 'string', 'content_types', 'About the company'),
        ('content_type_behind_scenes', 'Behind the Scenes', 'string', 'content_types', 'Warehouse, team, operations'),
        ('content_type_testimonial', 'Customer Testimonial', 'string', 'content_types', 'Customer satisfaction stories'),
        ('content_type_faq', 'FAQ Content', 'string', 'content_types', 'Frequently asked questions'),
        ('content_type_seasonal', 'Seasonal Content', 'string', 'content_types', 'Seasonal greetings and tips'),
        ('content_type_warning', 'Technical Warning', 'string', 'content_types', 'Product warnings and recalls'),
        ('content_type_buying_tips', 'Buying Tips', 'string', 'content_types', 'Tips for buyers'),
        
        # Content Formats
        ('format_image_post', 'Image Post', 'string', 'content_formats', 'Static image for social'),
        ('format_story', 'Story', 'string', 'content_formats', '24h temporary content'),
        ('format_reels', 'Reels/Shorts', 'string', 'content_formats', 'Short video content'),
        ('format_video', 'Video', 'string', 'content_formats', 'Longer video content'),
        ('format_article', 'Article', 'string', 'content_formats', 'Blog or website article'),
        ('format_pdf', 'PDF', 'string', 'content_formats', 'Downloadable PDF'),
        ('format_brochure', 'Digital Brochure', 'string', 'content_formats', 'Interactive brochure'),
        ('format_banner', 'Banner', 'string', 'content_formats', 'Web banner'),
        ('format_catalog', 'Digital Catalog', 'string', 'content_formats', 'Online product catalog'),
        ('format_email', 'Email', 'string', 'content_formats', 'Email newsletter'),
        ('format_whatsapp', 'WhatsApp Message', 'string', 'content_formats', 'WhatsApp promotional message'),
        ('format_sms', 'SMS', 'string', 'content_formats', 'Text message'),
        
        # Lead Statuses
        ('lead_status_new', 'New', 'string', 'lead_statuses', 'Newly captured lead'),
        ('lead_status_follow_up', 'In Follow-up', 'string', 'lead_statuses', 'Currently being followed up'),
        ('lead_status_converted_inquiry', 'Converted to Inquiry', 'string', 'lead_statuses', 'Became formal inquiry'),
        ('lead_status_converted_customer', 'Converted to Customer', 'string', 'lead_statuses', 'Became paying customer'),
        ('lead_status_lost', 'Lost', 'string', 'lead_statuses', 'Lead was lost'),
        ('lead_status_inactive', 'Inactive', 'string', 'lead_statuses', 'No response, inactive'),
        ('lead_status_needs_follow_up', 'Needs Follow-up Again', 'string', 'lead_statuses', 'Ready for another attempt'),
        
        # Importance Levels
        ('importance_high', 'High', 'string', 'importance_levels', 'High priority lead'),
        ('importance_medium', 'Medium', 'string', 'importance_levels', 'Medium priority lead'),
        ('importance_low', 'Low', 'string', 'importance_levels', 'Low priority lead'),
        
        # Alert Thresholds
        ('alert_threshold_cpl_max', '50', 'number', 'alert_thresholds', 'Maximum cost per lead'),
        ('alert_threshold_cpi_max', '200', 'number', 'alert_thresholds', 'Maximum cost per inquiry'),
        ('alert_threshold_cpa_max', '1000', 'number', 'alert_thresholds', 'Maximum cost per acquisition'),
        ('alert_threshold_lead_conv_min', '10', 'number', 'alert_thresholds', 'Minimum lead conversion rate %'),
        ('alert_threshold_budget_usage', '90', 'number', 'alert_thresholds', 'Budget exhaustion warning %'),
        ('alert_threshold_ctr_min', '1', 'number', 'alert_thresholds', 'Minimum click-through rate %'),
        
        # Attribution Models
        ('attribution_first_touch', 'First Touch', 'string', 'attribution_models', '100% credit to first touchpoint'),
        ('attribution_last_touch', 'Last Touch', 'string', 'attribution_models', '100% credit to last touchpoint'),
        ('attribution_linear', 'Linear', 'string', 'attribution_models', 'Equal credit to all touchpoints'),
        ('attribution_time_decay', 'Time Decay', 'string', 'attribution_models', 'More credit to recent touchpoints'),
        ('attribution_position', 'Position Based', 'string', 'attribution_models', '40% first, 40% last, 20% middle'),
        
        # Default Currency
        ('default_currency', 'AED', 'string', 'general', 'Default marketing currency'),
        
        # Budget Rules
        ('budget_approval_required_above', '10000', 'number', 'budget_rules', 'Budget amount requiring approval'),
        ('high_budget_threshold', '50000', 'number', 'budget_rules', 'High budget campaign threshold'),
    ]
    
    for key, val, vtype, cat, desc in settings:
        conn.execute(
            "INSERT OR IGNORE INTO marketing_settings (setting_key, setting_value, setting_type, category, description) VALUES (?, ?, ?, ?, ?)",
            (key, val, vtype, cat, desc)
        )


def seed_marketing_roles(conn):
    """Seed default marketing roles if not exist."""
    existing = conn.execute("SELECT COUNT(*) FROM marketing_roles WHERE is_system_role = 1").fetchone()[0]
    if existing > 0:
        return

    for role_data in MARKETING_DEFAULT_ROLES:
        conn.execute(
            """INSERT OR IGNORE INTO marketing_roles
               (role_name, role_code, description, is_system_role, permissions_json,
                can_view_financials, can_approve, can_publish, can_manage_team, can_view_all_data, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Active')""",
            (
                role_data['role_name'],
                role_data['role_code'],
                role_data['description'],
                role_data['is_system_role'],
                role_data['permissions_json'],
                role_data.get('can_view_financials', 0),
                role_data.get('can_approve', 0),
                role_data.get('can_publish', 0),
                role_data.get('can_manage_team', 0),
                role_data.get('can_view_all_data', 0),
            )
        )


def get_user_marketing_permissions(user_id: int) -> List[str]:
    """Get all marketing permissions for a user based on their role assignments."""
    conn = get_db()
    try:
        permissions = set()

        # Get Global Admin bypass
        user = conn.execute(
            "SELECT r.role_name FROM users u JOIN roles r ON u.role_id = r.id WHERE u.id = ?",
            (user_id,)
        ).fetchone()

        if user and user['role_name'] == 'Global Admin':
            permissions.add('all_marketing')
            return list(permissions)

        # Get permissions from marketing role assignments
        rows = conn.execute("""
            SELECT mr.permissions_json
            FROM marketing_user_roles mur
            JOIN marketing_roles mr ON mur.marketing_role_id = mr.id
            WHERE mur.user_id = ? AND mur.is_active = 1 AND mr.status = 'Active'
        """, (user_id,)).fetchall()

        for row in rows:
            if row['permissions_json']:
                perms = json.loads(row['permissions_json'])
                permissions.update(perms)

        return list(permissions)
    finally:
        conn.close()


def get_marketing_role_users(role_id: int) -> List[Dict]:
    """Get all users assigned to a specific marketing role."""
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT u.id, u.username, u.email, mur.assigned_at
            FROM marketing_user_roles mur
            JOIN users u ON mur.user_id = u.id
            WHERE mur.marketing_role_id = ? AND mur.is_active = 1
        """, (role_id,)).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def seed_seasonality(conn):
    """Seed default seasonality data if not exist."""
    existing = conn.execute("SELECT COUNT(*) FROM marketing_seasonality").fetchone()[0]
    if existing > 0:
        return
    
    seasons = [
        ('Peak Sales Season', 'peak', 1, 3, 1, 31, 1, 'Sales Growth,Discount', 'Product Introduction,Buying Tips', 'Instagram,WhatsApp,Email', 'Highest sales period'),
        ('Ramadan Pre-Season', 'pre_ramadan', 1, 2, 1, 28, 0, 'Brand Awareness,Product Intro', 'Seasonal Content,FAQ', 'Social Media,Email', 'Build momentum before Ramadan'),
        ('Ramadan Season', 'ramadan', 3, 3, 1, 30, 1, 'Brand Awareness,Discount', 'Behind the Scenes,Testimonial', 'WhatsApp,Instagram,Facebook', 'Holy month campaign'),
        ('Post-Ramadan/Eid', 'eid', 4, 4, 1, 15, 1, 'Sales Growth,Reactivation', 'Special Offer,Discount', 'All Channels', 'Eid celebration and sales'),
        ('Summer Season', 'summer', 6, 8, 1, 31, 0, 'Seasonal Content,Brand Awareness', 'Behind the Scenes,Buying Tips', 'Instagram,TikTok,YouTube', 'Summer campaign period'),
        ('Back to School', 'back_to_school', 8, 9, 1, 30, 0, 'Product Introduction,Discount', 'Product Introduction,FAQ', 'Email,WhatsApp,Social Media', 'Education sector push'),
        ('Year End', 'year_end', 11, 12, 1, 31, 0, 'Stock Liquidation,Reactivation', 'Special Offer,Discount', 'All Channels', 'Year-end clearance'),
        ('Low Season', 'low', 5, 5, 1, 31, 0, 'Brand Awareness,Content', 'Technical Education,FAQ', 'Website,SEO,LinkedIn', 'Maintain presence during slow period'),
    ]
    
    for name, stype, smonth, emonth, sday, eday, ipeak, ctype, ftype, channels, notes in seasons:
        conn.execute(
            "INSERT OR IGNORE INTO marketing_seasonality (name, season_type, start_month, end_month, start_day, end_day, is_peak, best_for_campaign_type, best_for_content_type, best_for_channel, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (name, stype, smonth, emonth, sday, eday, ipeak, ctype, ftype, channels, notes)
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def log_marketing_audit(conn, entity_type, entity_id, action_type, field_name=None, old_value=None, new_value=None, change_reason=None, actor_user_id=None):
    """Log an audit record for marketing changes."""
    conn.execute(
        """INSERT INTO marketing_audit_logs 
           (entity_type, entity_id, action_type, field_name, old_value, new_value, change_reason, actor_user_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (entity_type, entity_id, action_type, field_name, old_value, new_value, change_reason, actor_user_id)
    )


def get_marketing_setting(conn, key, default=None):
    """Get a marketing setting value."""
    row = conn.execute(
        "SELECT setting_value FROM marketing_settings WHERE setting_key = ? AND is_active = 1",
        (key,)
    ).fetchone()
    return row['setting_value'] if row else default


def update_marketing_setting(conn, key, value, updated_by_user_id=None):
    """Update a marketing setting value."""
    conn.execute(
        "UPDATE marketing_settings SET setting_value = ?, updated_by_user_id = ?, updated_at = CURRENT_TIMESTAMP WHERE setting_key = ?",
        (value, updated_by_user_id, key)
    )


def get_marketing_permissions(user_id):
    """Get marketing permissions for a user from session/role."""
    # This would be populated from session in routes
    return []


# =============================================================================
# ANALYTICS HELPERS
# =============================================================================

def get_campaign_summary_stats(conn, campaign_id=None, date_from=None, date_to=None):
    """Get campaign summary statistics."""
    query = """
        SELECT 
            COUNT(*) as total_campaigns,
            SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active_campaigns,
            SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_campaigns,
            SUM(CASE WHEN status = 'Paused' THEN 1 ELSE 0 END) as paused_campaigns,
            SUM(leads_generated) as total_leads,
            SUM(inquiries_generated) as total_inquiries,
            SUM(quotations_generated) as total_quotations,
            SUM(purchases_generated) as total_purchases,
            SUM(sales_generated) as total_sales,
            SUM(actual_cost) as total_cost,
            SUM(new_customers_acquired) as new_customers,
            SUM(reactivated_customers) as reactivated_customers
        FROM marketing_campaigns
        WHERE 1=1
    """
    params = []
    
    if campaign_id:
        query += " AND id = ?"
        params.append(campaign_id)
    
    if date_from:
        query += " AND start_date >= ?"
        params.append(date_from)
    
    if date_to:
        query += " AND end_date <= ?"
        params.append(date_to)
    
    return dict(conn.execute(query, params).fetchone())


def get_lead_stats(conn, date_from=None, date_to=None, source_id=None):
    """Get lead statistics."""
    query = """
        SELECT 
            COUNT(*) as total_leads,
            SUM(CASE WHEN lead_status = 'New' THEN 1 ELSE 0 END) as new_leads,
            SUM(CASE WHEN lead_status = 'In Follow-up' THEN 1 ELSE 0 END) as in_follow_up,
            SUM(CASE WHEN lead_status = 'Converted to Customer' THEN 1 ELSE 0 END) as converted,
            SUM(CASE WHEN lead_status = 'Lost' THEN 1 ELSE 0 END) as lost_leads,
            SUM(estimated_value) as total_estimated_value,
            SUM(CASE WHEN converted_to_customer_id IS NOT NULL THEN 1 ELSE 0 END) as converted_to_customer
        FROM marketing_leads
        WHERE 1=1
    """
    params = []
    
    if date_from:
        query += " AND created_at >= ?"
        params.append(date_from)
    
    if date_to:
        query += " AND created_at <= ?"
        params.append(date_to)
    
    if source_id:
        query += " AND source_id = ?"
        params.append(source_id)
    
    return dict(conn.execute(query, params).fetchone())


def get_channel_performance(conn, date_from=None, date_to=None):
    """Get channel performance metrics."""
    query = """
        SELECT 
            c.id,
            c.name,
            c.channel_type,
            c.budget,
            COALESCE(cc.actual_spend, 0) as actual_spend,
            COALESCE(cc.leads_generated, 0) as leads_generated,
            COALESCE(cc.inquiries_generated, 0) as inquiries_generated,
            COALESCE(cc.sales_generated, 0) as sales_generated,
            CASE WHEN COALESCE(cc.leads_generated, 0) > 0 
                 THEN ROUND(COALESCE(cc.actual_spend, 0) / cc.leads_generated, 2) 
                 ELSE 0 END as cost_per_lead,
            CASE WHEN COALESCE(cc.inquiries_generated, 0) > 0 
                 THEN ROUND(COALESCE(cc.actual_spend, 0) / cc.inquiries_generated, 2) 
                 ELSE 0 END as cost_per_inquiry
        FROM marketing_channels c
        LEFT JOIN marketing_campaign_channels cc ON c.id = cc.channel_id
        LEFT JOIN marketing_campaigns cmp ON cc.campaign_id = cmp.id
        WHERE c.status = 'Active'
    """
    params = []
    
    if date_from:
        query += " AND (cmp.start_date >= ? OR cmp.start_date IS NULL)"
        params.append(date_from)
    
    if date_to:
        query += " AND (cmp.end_date <= ? OR cmp.end_date IS NULL)"
        params.append(date_to)
    
    query += " GROUP BY c.id ORDER BY c.channel_type, c.name"
    
    return [dict(r) for r in conn.execute(query, params).fetchall()]


def get_marketing_dashboard_data(conn, date_from=None, date_to=None):
    """Get comprehensive dashboard data for marketing."""
    campaign_stats = get_campaign_summary_stats(conn, date_from=date_from, date_to=date_to)
    lead_stats = get_lead_stats(conn, date_from=date_from, date_to=date_to)
    channel_perf = get_channel_performance(conn, date_from=date_from, date_to=date_to)
    
    # Funnel data
    funnel_data = conn.execute("""
        SELECT 
            fs.name,
            fs.stage_order,
            fs.stage_type,
            COUNT(fr.id) as records,
            AVG(ROUND((julianday(COALESCE(fr.exiting_date, CURRENT_TIMESTAMP)) - julianday(fr.entering_date)) * 24)) as avg_hours
        FROM marketing_funnel_stages fs
        LEFT JOIN marketing_funnel_records fr ON fs.id = fr.stage_id
        GROUP BY fs.id
        ORDER BY fs.stage_order
    """).fetchall()
    
    # Top campaigns by ROI
    top_campaigns = conn.execute("""
        SELECT 
            id,
            name,
            campaign_type,
            status,
            budget,
            actual_cost,
            sales_generated,
            CASE WHEN actual_cost > 0 THEN ROUND((sales_generated - actual_cost) / actual_cost * 100, 2) ELSE 0 END as roi,
            leads_generated,
            new_customers_acquired
        FROM marketing_campaigns
        WHERE actual_cost > 0 AND sales_generated > 0
        ORDER BY roi DESC
        LIMIT 10
    """).fetchall()
    
    # Recent alerts
    recent_alerts = conn.execute("""
        SELECT 
            id,
            alert_type,
            alert_title,
            severity,
            entity_name,
            is_resolved,
            created_at
        FROM marketing_alerts
        WHERE is_resolved = 0
        ORDER BY created_at DESC
        LIMIT 10
    """).fetchall()
    
    return {
        'campaign_stats': dict(campaign_stats) if campaign_stats else {},
        'lead_stats': dict(lead_stats) if lead_stats else {},
        'channel_performance': [dict(r) for r in channel_perf],
        'funnel_data': [dict(r) for r in funnel_data],
        'top_campaigns': [dict(r) for r in top_campaigns],
        'recent_alerts': [dict(r) for r in recent_alerts],
    }


# =============================================================================
# CROSS-MODULE INTEGRATION FUNCTIONS
# =============================================================================

def get_marketing_customer_insights(conn, lead_id: int = None, customer_id: int = None):
    """
    Get cross-module insights linking marketing leads/customers to sales and inventory data.
    Used for connecting marketing campaigns to actual sales and warehouse data.
    """
    insights = {
        'customer_profile': None,
        'purchase_history': [],
        'related_campaigns': [],
        'related_inventory': [],
        'cross_sell_opportunities': [],
    }

    if lead_id:
        # Get lead info and find related customer
        lead = conn.execute("SELECT * FROM marketing_leads WHERE id = ?", (lead_id,)).fetchone()
        if lead:
            insights['lead_info'] = dict(lead)

            # Try to find matching customer by phone/email
            if lead.get('phone'):
                customer = conn.execute(
                    "SELECT * FROM sdad_customers WHERE phone LIKE ? LIMIT 1",
                    (f"%{lead['phone']}%",)
                ).fetchone()
                if customer:
                    insights['customer_profile'] = dict(customer)
                    customer_id = customer['id']

    if customer_id:
        # Get customer profile
        customer = conn.execute("SELECT * FROM sdad_customers WHERE id = ?", (customer_id,)).fetchone()
        if customer:
            insights['customer_profile'] = dict(customer)

            # Get recent purchases
            purchases = conn.execute("""
                SELECT * FROM sdad_sales_transactions
                WHERE customer_id = ?
                ORDER BY transaction_date DESC
                LIMIT 10
            """, (customer_id,)).fetchall()
            insights['purchase_history'] = [dict(p) for p in purchases]

    return insights


def get_campaign_sales_impact(conn, campaign_id: int = None, date_from: str = None, date_to: str = None):
    """
    Calculate the impact of marketing campaigns on actual sales.
    Links marketing campaigns to sales transactions.
    """
    params = []
    where_clause = ""

    if campaign_id:
        where_clause += " AND c.id = ?"
        params.append(campaign_id)

    if date_from:
        where_clause += " AND st.transaction_date >= ?"
        params.append(date_from)

    if date_to:
        where_clause += " AND st.transaction_date <= ?"
        params.append(date_to)

    # Get sales linked to marketing campaigns
    sales_data = conn.execute(f"""
        SELECT
            c.id as campaign_id,
            c.name as campaign_name,
            c.campaign_type,
            c.status,
            COUNT(DISTINCT st.id) as transaction_count,
            SUM(st.total_amount) as total_sales,
            AVG(st.total_amount) as avg_transaction
        FROM marketing_campaigns c
        LEFT JOIN marketing_attribution ma ON c.id = ma.campaign_id
        LEFT JOIN sdad_customers cust ON ma.customer_id = cust.id
        LEFT JOIN sdad_sales_transactions st ON cust.id = st.customer_id
            AND st.transaction_date BETWEEN c.start_date AND COALESCE(c.end_date, CURRENT_DATE)
        WHERE 1=1 {where_clause}
        GROUP BY c.id
        ORDER BY total_sales DESC NULLS LAST
    """, params).fetchall()

    return [dict(r) for r in sales_data]


def get_inventory_marketing_alignment(conn, brand_id: int = None, category_id: int = None):
    """
    Get inventory data aligned with marketing brands and campaigns.
    Helps marketing team understand stock availability for promoted products.
    """
    params = []
    where_clause = ""

    if brand_id:
        where_clause += " AND b.id = ?"
        params.append(brand_id)

    if category_id:
        where_clause += " AND cat.id = ?"
        params.append(category_id)

    inventory_data = conn.execute(f"""
        SELECT
            p.id as part_id,
            p.part_number,
            p.name as part_name,
            b.name as brand_name,
            cat.name as category_name,
            i.quantity_in_stock,
            i.location,
            i.min_stock_level,
            CASE WHEN i.quantity_in_stock <= i.min_stock_level THEN 'Low Stock'
                 WHEN i.quantity_in_stock <= i.min_stock_level * 2 THEN 'Medium'
                 ELSE 'Good' END as stock_status
        FROM parts p
        LEFT JOIN brands b ON p.brand_id = b.id
        LEFT JOIN categories cat ON p.category_id = cat.id
        LEFT JOIN inventory i ON p.id = i.part_id
        WHERE 1=1 {where_clause}
        ORDER BY i.quantity_in_stock ASC NULLS LAST
        LIMIT 50
    """, params).fetchall()

    return [dict(r) for r in inventory_data]


def link_lead_to_customer(conn, lead_id: int, customer_id: int, user_id: int):
    """
    Link a marketing lead to an existing CRM customer.
    Used when a lead is converted to a customer.
    """
    conn.execute("""
        UPDATE marketing_leads
        SET converted_to_customer_id = ?,
            conversion_date = CURRENT_TIMESTAMP,
            status = 'Converted'
        WHERE id = ?
    """, (customer_id, lead_id))

    # Log the conversion
    log_marketing_audit(conn, 'marketing_leads', lead_id, 'CONVERT',
                        f'Lead converted to customer ID: {customer_id}', user_id)

    conn.commit()


def create_campaign_attribution(conn, campaign_id: int, customer_id: int, touchpoints: str, user_id: int):
    """
    Create attribution record linking a customer/purchase to a marketing campaign.
    """
    cursor = conn.execute("""
        INSERT INTO marketing_attribution
        (campaign_id, customer_id, touchpoints, attributed_at, created_by_user_id)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
    """, (campaign_id, customer_id, touchpoints, user_id))
    conn.commit()
    return cursor.lastrowid


def get_segment_customer_overlap(conn, segment_id: int):
    """
    Get overlap between marketing segments and CI customer segments.
    Helps identify which marketing segments map to actual customers.
    """
    # Get marketing segment criteria
    segment = conn.execute(
        "SELECT * FROM marketing_customer_segments WHERE id = ?",
        (segment_id,)
    ).fetchone()

    if not segment:
        return {'segment': None, 'matched_customers': [], 'total_count': 0}

    # Build query based on segment criteria
    query_conditions = []
    params = []

    if segment.get('country'):
        query_conditions.append("country = ?")
        params.append(segment['country'])

    if segment.get('city'):
        query_conditions.append("city = ?")
        params.append(segment['city'])

    if segment.get('is_retail'):
        query_conditions.append("customer_type = 'Retail'")

    if segment.get('is_wholesale'):
        query_conditions.append("customer_type = 'Wholesale'")

    where_clause = " AND ".join(query_conditions) if query_conditions else "1=1"

    matched = conn.execute(f"""
        SELECT id, name, phone, city, country, customer_type, total_sales
        FROM sdad_customers
        WHERE {where_clause}
        ORDER BY total_sales DESC
        LIMIT 100
    """, params).fetchall()

    return {
        'segment': dict(segment),
        'matched_customers': [dict(r) for r in matched],
        'total_count': len(matched),
    }


# =============================================================================
# ALERTS AND RECOMMENDATIONS ENGINE
# =============================================================================

ALERT_SEVERITY_MAP = {
    'critical': 3,
    'high': 2,
    'medium': 1,
    'low': 0,
}


def generate_marketing_alerts(conn, user_id: int = None):
    """
    Generate marketing alerts based on current data.
    Called periodically or on demand to create alert records.
    """
    alerts_created = 0

    # 1. Campaign Budget Alerts
    campaigns_over_budget = conn.execute("""
        SELECT id, name, budget, actual_cost
        FROM marketing_campaigns
        WHERE status = 'Active'
        AND actual_cost > budget
        AND budget > 0
    """).fetchall()

    for camp in campaigns_over_budget:
        alert_title = f"Budget Exceeded: {camp['name']}"
        existing = conn.execute("""
            SELECT id FROM marketing_alerts
            WHERE alert_title = ? AND is_resolved = 0
        """, (alert_title,)).fetchone()

        if not existing:
            conn.execute("""
                INSERT INTO marketing_alerts
                (alert_type, alert_title, description, severity, entity_type, entity_id, entity_name, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'budget',
                alert_title,
                f"Campaign '{camp['name']}' has exceeded its budget. Budget: ${camp['budget']}, Actual: ${camp['actual_cost']}",
                'high',
                'campaign',
                camp['id'],
                camp['name'],
                user_id
            ))
            alerts_created += 1

    # 2. Lead Response Time Alerts
    old_unresponsive_leads = conn.execute("""
        SELECT id, name, created_at, assigned_to
        FROM marketing_leads
        WHERE status = 'New'
        AND julianday('now') - julianday(created_at) > 7
    """).fetchall()

    for lead in old_unresponsive_leads:
        alert_title = f"Stale Lead: {lead['name']}"
        existing = conn.execute("""
            SELECT id FROM marketing_alerts
            WHERE alert_title = ? AND is_resolved = 0
        """, (alert_title,)).fetchone()

        if not existing:
            conn.execute("""
                INSERT INTO marketing_alerts
                (alert_type, alert_title, description, severity, entity_type, entity_id, entity_name, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'lead',
                alert_title,
                f"Lead '{lead['name']}' has been unaddressed for over 7 days.",
                'medium',
                'lead',
                lead['id'],
                lead['name'],
                user_id
            ))
            alerts_created += 1

    # 3. Low Stock Campaign Products Alert
    low_stock_parts = conn.execute("""
        SELECT p.id, p.name, p.part_number, i.quantity_in_stock, i.min_stock_level
        FROM parts p
        JOIN inventory i ON p.id = i.part_id
        JOIN marketing_campaigns mc ON mc.target_products LIKE '%' || p.part_number || '%'
            OR mc.messaging LIKE '%' || p.name || '%'
        WHERE mc.status = 'Active'
        AND i.quantity_in_stock <= i.min_stock_level
        LIMIT 10
    """).fetchall()

    for part in low_stock_parts:
        alert_title = f"Low Stock for Campaign: {part['name']}"
        existing = conn.execute("""
            SELECT id FROM marketing_alerts
            WHERE alert_title = ? AND is_resolved = 0
        """, (alert_title,)).fetchone()

        if not existing:
            conn.execute("""
                INSERT INTO marketing_alerts
                (alert_type, alert_title, description, severity, entity_type, entity_id, entity_name, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'inventory',
                alert_title,
                f"Part '{part['name']}' (Stock: {part['quantity_in_stock']}) is low while linked to an active campaign.",
                'high',
                'part',
                part['id'],
                part['name'],
                user_id
            ))
            alerts_created += 1

    # 4. Campaign ROI Decline Alert
    campaigns_with_roi_drop = conn.execute("""
        WITH previous_roi AS (
            SELECT campaign_id,
                   AVG(CASE WHEN actual_cost > 0 THEN (sales_generated - actual_cost) / actual_cost * 100 ELSE 0 END) as prev_roi
            FROM marketing_campaigns
            WHERE status = 'Completed'
            GROUP BY campaign_id
        )
        SELECT mc.id, mc.name, mc.roi,
               COALESCE(p.roi, 0) as previous_roi
        FROM marketing_campaigns mc
        LEFT JOIN previous_roi p ON mc.id = p.campaign_id
        WHERE mc.status = 'Active'
        AND mc.roi < COALESCE(p.roi, 0) * 0.5
        AND mc.actual_cost > 1000
    """).fetchall()

    for camp in campaigns_with_roi_drop:
        alert_title = f"Declining ROI: {camp['name']}"
        existing = conn.execute("""
            SELECT id FROM marketing_alerts
            WHERE alert_title = ? AND is_resolved = 0
        """, (alert_title,)).fetchone()

        if not existing:
            conn.execute("""
                INSERT INTO marketing_alerts
                (alert_type, alert_title, description, severity, entity_type, entity_id, entity_name, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'performance',
                alert_title,
                f"Campaign '{camp['name']}' ROI has dropped significantly from {camp['previous_roi']:.1f}% to {camp['roi']:.1f}%.",
                'medium',
                'campaign',
                camp['id'],
                camp['name'],
                user_id
            ))
            alerts_created += 1

    # 5. Content Calendar Gaps Alert
    # Check if there's upcoming content scheduled
    upcoming_content = conn.execute("""
        SELECT COUNT(*) as cnt
        FROM marketing_content
        WHERE scheduled_date BETWEEN date('now') AND date('now', '+7 days')
    """).fetchone()

    if upcoming_content['cnt'] == 0:
        alert_title = "Content Calendar Gap"
        existing = conn.execute("""
            SELECT id FROM marketing_alerts
            WHERE alert_title = ? AND is_resolved = 0
        """, (alert_title,)).fetchone()

        if not existing:
            conn.execute("""
                INSERT INTO marketing_alerts
                (alert_type, alert_title, description, severity, entity_type, entity_name, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                'content',
                alert_title,
                "No content is scheduled for the next 7 days. Consider planning upcoming content.",
                'low',
                'content',
                'Content Calendar',
                user_id
            ))
            alerts_created += 1

    conn.commit()
    return alerts_created


def generate_marketing_recommendations(conn, user_id: int = None):
    """
    Generate AI-powered marketing recommendations based on data patterns.
    """
    recommendations_created = 0

    # 1. Best Performing Channel Recommendation
    top_channel = conn.execute("""
        SELECT channel_id, channel_name, AVG(roi) as avg_roi, SUM(actual_cost) as total_spend
        FROM marketing_campaign_channels mcc
        JOIN marketing_campaigns mc ON mcc.campaign_id = mc.id
        WHERE mc.status IN ('Active', 'Completed')
        AND mc.actual_cost > 0
        GROUP BY channel_id, channel_name
        ORDER BY avg_roi DESC
        LIMIT 1
    """).fetchone()

    if top_channel and top_channel['avg_roi'] > 0:
        rec_title = f"Increase investment in {top_channel['channel_name']}"
        existing = conn.execute("""
            SELECT id FROM marketing_recommendations
            WHERE recommendation_title = ? AND is_implemented = 0
        """, (rec_title,)).fetchone()

        if not existing:
            conn.execute("""
                INSERT INTO marketing_recommendations
                (recommendation_type, recommendation_title, description, potential_impact,
                 difficulty, priority_score, target_entities, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'channel_investment',
                rec_title,
                f"{top_channel['channel_name']} channel has shown the highest ROI ({top_channel['avg_roi']:.1f}%). "
                f"Consider shifting more budget to this channel.",
                f"{top_channel['avg_roi']:.1f}% avg ROI",
                'low',
                8,
                json.dumps([{'type': 'channel', 'id': top_channel['channel_id']}]),
                user_id
            ))
            recommendations_created += 1

    # 2. Lead Conversion Optimization
    lead_conversion_rates = conn.execute("""
        SELECT source, COUNT(*) as total,
               SUM(CASE WHEN status = 'Converted' THEN 1 ELSE 0 END) as converted
        FROM marketing_leads
        WHERE source IS NOT NULL AND source != ''
        GROUP BY source
        HAVING total > 5
        ORDER BY (CAST(SUM(CASE WHEN status = 'Converted' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*)) DESC
        LIMIT 1
    """).fetchone()

    if lead_conversion_rates:
        rate = (lead_conversion_rates['converted'] / lead_conversion_rates['total']) * 100
        rec_title = f"Focus on {lead_conversion_rates['source']} lead source"
        existing = conn.execute("""
            SELECT id FROM marketing_recommendations
            WHERE recommendation_title = ? AND is_implemented = 0
        """, (rec_title,)).fetchone()

        if not existing:
            conn.execute("""
                INSERT INTO marketing_recommendations
                (recommendation_type, recommendation_title, description, potential_impact,
                 difficulty, priority_score, target_entities, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'lead_source',
                rec_title,
                f"'{lead_conversion_rates['source']}' leads have a {rate:.1f}% conversion rate. "
                f"Consider investing more in this source.",
                f"{rate:.1f}% conversion rate",
                'medium',
                7,
                json.dumps([{'type': 'lead_source', 'name': lead_conversion_rates['source']}]),
                user_id
            ))
            recommendations_created += 1

    # 3. Budget Reallocation Recommendation
    underperforming_campaigns = conn.execute("""
        SELECT id, name, budget, actual_cost, sales_generated,
               CASE WHEN actual_cost > 0 THEN (sales_generated - actual_cost) / actual_cost * 100 ELSE -100 END as roi
        FROM marketing_campaigns
        WHERE status = 'Active'
        AND actual_cost > 0
        AND (sales_generated - actual_cost) / actual_cost * 100 < 0
    """).fetchall()

    if len(underperforming_campaigns) > 1:
        total_waste = sum(c['actual_cost'] - (c['sales_generated'] or 0) for c in underperforming_campaigns if c['sales_generated'] < c['actual_cost'])

        rec_title = "Reallocate budget from underperforming campaigns"
        existing = conn.execute("""
            SELECT id FROM marketing_recommendations
            WHERE recommendation_title = ? AND is_implemented = 0
        """, (rec_title,)).fetchone()

        if not existing:
            campaign_names = ', '.join([c['name'] for c in underperforming_campaigns[:3]])
            conn.execute("""
                INSERT INTO marketing_recommendations
                (recommendation_type, recommendation_title, description, potential_impact,
                 difficulty, priority_score, target_entities, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'budget_allocation',
                rec_title,
                f"{len(underperforming_campaigns)} campaigns are ROI-negative. "
                f"Consider reallocating ~${total_waste:.0f} from: {campaign_names}",
                f"${total_waste:.0f} potential savings",
                'high',
                9,
                json.dumps([{'type': 'campaign', 'id': c['id']} for c in underperforming_campaigns]),
                user_id
            ))
            recommendations_created += 1

    # 4. Seasonality Timing Recommendation
    peak_season = conn.execute("""
        SELECT * FROM marketing_seasonality
        WHERE is_peak = 1
        AND start_month <= strftime('%m', 'now', '+30 days')
        AND end_month >= strftime('%m', 'now', '+30 days')
        LIMIT 1
    """).fetchone()

    if peak_season:
        rec_title = f"Prepare for {peak_season['name']}"
        existing = conn.execute("""
            SELECT id FROM marketing_recommendations
            WHERE recommendation_title = ? AND is_implemented = 0
        """, (rec_title,)).fetchone()

        if not existing:
            conn.execute("""
                INSERT INTO marketing_recommendations
                (recommendation_type, recommendation_title, description, potential_impact,
                 difficulty, priority_score, target_entities, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'seasonality',
                rec_title,
                f"{peak_season['name']} is approaching. "
                f"Best channels: {peak_season.get('best_for_channel', 'All')}. "
                f"Best content: {peak_season.get('best_for_content_type', 'General')}",
                'High seasonal sales potential',
                'medium',
                8,
                json.dumps([{'type': 'seasonality', 'id': peak_season['id']}]),
                user_id
            ))
            recommendations_created += 1

    # 5. Cross-Sell Opportunity
    high_value_customers_no_recent_campaign = conn.execute("""
        SELECT c.id, c.name, c.total_sales, c.last_purchase_date
        FROM sdad_customers c
        WHERE c.total_sales > 10000
        AND c.last_purchase_date < date('now', '-90 days')
        AND NOT EXISTS (
            SELECT 1 FROM marketing_attribution ma
            JOIN marketing_campaigns mc ON ma.campaign_id = mc.id
            WHERE ma.customer_id = c.id
            AND mc.end_date > date('now', '-90 days')
        )
        LIMIT 10
    """).fetchall()

    if high_value_customers_no_recent_campaign:
        rec_title = "Re-engage dormant high-value customers"
        existing = conn.execute("""
            SELECT id FROM marketing_recommendations
            WHERE recommendation_title = ? AND is_implemented = 0
        """, (rec_title,)).fetchone()

        if not existing:
            customer_names = ', '.join([c['name'] for c in high_value_customers_no_recent_campaign[:3]])
            conn.execute("""
                INSERT INTO marketing_recommendations
                (recommendation_type, recommendation_title, description, potential_impact,
                 difficulty, priority_score, target_entities, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'customer_reengagement',
                rec_title,
                f"{len(high_value_customers_no_recent_campaign)} high-value customers haven't been reached by recent campaigns. "
                f"Consider a re-engagement campaign for: {customer_names}",
                'High customer lifetime value recovery',
                'low',
                7,
                json.dumps([{'type': 'customer', 'id': c['id']} for c in high_value_customers_no_recent_campaign]),
                user_id
            ))
            recommendations_created += 1

    conn.commit()
    return recommendations_created


def run_marketing_insights(user_id: int = None):
    """
    Run the full marketing intelligence engine.
    Generates alerts and recommendations.
    """
    conn = get_db()
    try:
        alerts_count = generate_marketing_alerts(conn, user_id)
        recommendations_count = generate_marketing_recommendations(conn, user_id)
        return {
            'alerts_created': alerts_count,
            'recommendations_created': recommendations_count
        }
    finally:
        conn.close()


# Run migrations when this module is imported
if __name__ != '__main__':
    try:
        run_marketing_migrations()
    except Exception as e:
        print(f"Marketing migrations note: {e}")
