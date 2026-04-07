"""
Social Media Management System - Database Models
================================================
This file contains all database table definitions for the Social Media Management System.
These tables are designed to extend the existing SQLite database without conflicts.

Social Media Tables:
1. social_accounts - Social media account/platform registration
2. social_content_production - Content production workflow items
3. social_content_calendar - Publishing calendar entries
4. social_content_archive - Published content archive
5. social_publish_queue - Publishing queue and scheduling
6. social_publish_history - Publishing history log
7. social_messages - Inbox messages and interactions
8. social_message_threads - Message conversation threads
9. social_leads - Social media leads
10. social_lead_followups - Lead follow-up history
11. social_campaigns - Social campaigns
12. social_ads - Social advertisements
13. social_audiences - Audience definitions
14. social_monitoring - Brand/market monitoring records
15. social_alerts - System alerts
16. social_kpis - KPI records and targets
17. social_roles - Role definitions
18. social_permissions - Permission definitions
19. social_audit_logs - Audit trail
20. social_settings - Configurable settings
21. social_captions - Caption bank
22. social_hashtags - Hashtag bank
23. social_ctas - CTA bank
24. social_templates - Content templates
25. social_audit - Audit/traceability records
"""

import sqlite3
import os
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
# SOCIAL MEDIA TABLE DEFINITIONS
# =============================================================================

SOCIAL_MEDIA_TABLES = [
    # -------------------------------------------------------------------------
    # 1. Social Accounts & Platforms
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT NOT NULL,
        account_name TEXT NOT NULL,
        username TEXT,
        account_link TEXT,
        company_id INTEGER,
        target_market TEXT,
        primary_language TEXT DEFAULT 'en',
        account_type TEXT DEFAULT 'Business',
        account_status TEXT DEFAULT 'Active',
        account_manager_id INTEGER,
        allowed_admins TEXT,
        connected_email TEXT,
        connected_mobile TEXT,
        two_factor_enabled INTEGER DEFAULT 0,
        business_manager_id TEXT,
        pixel_tracking_id TEXT,
        whatsapp_linked_number TEXT,
        website_linked_url TEXT,
        notes TEXT,
        last_activity_at DATETIME,
        security_status TEXT DEFAULT 'Secure',
        inactive_archive INTEGER DEFAULT 0,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id),
        FOREIGN KEY (account_manager_id) REFERENCES users(id),
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 2. Content Production Workflow
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_content_production (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content_code TEXT UNIQUE,
        internal_title TEXT NOT NULL,
        display_title TEXT,
        target_platform TEXT,
        content_type TEXT,
        content_format TEXT,
        content_pillar TEXT,
        topic TEXT,
        content_objective TEXT,
        target_audience TEXT,
        language TEXT DEFAULT 'en',
        caption TEXT,
        hook TEXT,
        cta_text TEXT,
        hashtags TEXT,
        keywords TEXT,
        related_brand TEXT,
        related_products TEXT,
        related_skus TEXT,
        location_tag TEXT,
        mentions TEXT,
        destination_link TEXT,
        cover_file TEXT,
        main_file TEXT,
        subtitle_file TEXT,
        content_versions TEXT,
        creator_id INTEGER,
        designer_id INTEGER,
        editor_id INTEGER,
        content_owner_id INTEGER,
        design_owner_id INTEGER,
        approval_owner_id INTEGER,
        publishing_owner_id INTEGER,
        production_status TEXT DEFAULT 'Idea',
        approval_status TEXT DEFAULT 'Pending',
        approved_by_id INTEGER,
        approved_at DATETIME,
        rejection_reason TEXT,
        priority INTEGER DEFAULT 3,
        related_campaign_id INTEGER,
        notes TEXT,
        attachments TEXT,
        tags TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (creator_id) REFERENCES users(id),
        FOREIGN KEY (designer_id) REFERENCES users(id),
        FOREIGN KEY (editor_id) REFERENCES users(id),
        FOREIGN KEY (content_owner_id) REFERENCES users(id),
        FOREIGN KEY (design_owner_id) REFERENCES users(id),
        FOREIGN KEY (approval_owner_id) REFERENCES users(id),
        FOREIGN KEY (publishing_owner_id) REFERENCES users(id),
        FOREIGN KEY (approved_by_id) REFERENCES users(id),
        FOREIGN KEY (related_campaign_id) REFERENCES social_campaigns(id),
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 3. Content Calendar
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_content_calendar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content_id INTEGER,
        publish_date DATE,
        publish_time TEXT,
        platform TEXT NOT NULL,
        content_type TEXT,
        content_topic TEXT,
        content_objective TEXT,
        target_audience TEXT,
        target_market TEXT,
        linked_campaign_id INTEGER,
        related_product TEXT,
        related_brand TEXT,
        related_sku TEXT,
        cta TEXT,
        content_owner_id INTEGER,
        design_owner_id INTEGER,
        approval_owner_id INTEGER,
        publishing_owner_id INTEGER,
        calendar_status TEXT DEFAULT 'Scheduled',
        priority INTEGER DEFAULT 3,
        timezone TEXT DEFAULT 'Asia/Dubai',
        utm_source TEXT,
        utm_medium TEXT,
        utm_campaign TEXT,
        notes TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (content_id) REFERENCES social_content_production(id) ON DELETE SET NULL,
        FOREIGN KEY (linked_campaign_id) REFERENCES social_campaigns(id),
        FOREIGN KEY (content_owner_id) REFERENCES users(id),
        FOREIGN KEY (design_owner_id) REFERENCES users(id),
        FOREIGN KEY (approval_owner_id) REFERENCES users(id),
        FOREIGN KEY (publishing_owner_id) REFERENCES users(id),
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 4. Content Archive
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_content_archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content_code TEXT UNIQUE,
        platform TEXT NOT NULL,
        content_type TEXT,
        display_title TEXT,
        internal_title TEXT,
        content_pillar TEXT,
        topic TEXT,
        content_objective TEXT,
        target_market TEXT,
        target_audience TEXT,
        language TEXT,
        caption TEXT,
        hook TEXT,
        cta TEXT,
        hashtags TEXT,
        related_brand TEXT,
        related_products TEXT,
        related_skus TEXT,
        destination_link TEXT,
        cover_file TEXT,
        main_file TEXT,
        published_at DATETIME,
        reach INTEGER DEFAULT 0,
        impressions INTEGER DEFAULT 0,
        engagement INTEGER DEFAULT 0,
        likes INTEGER DEFAULT 0,
        comments INTEGER DEFAULT 0,
        shares INTEGER DEFAULT 0,
        saves INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        ctr DECIMAL(5,2) DEFAULT 0,
        messages_generated INTEGER DEFAULT 0,
        leads_generated INTEGER DEFAULT 0,
        sales_generated DECIMAL(12,2) DEFAULT 0,
        linked_campaign_id INTEGER,
        linked_account_id INTEGER,
        performance_status TEXT DEFAULT 'Active',
        archived_reason TEXT,
        notes TEXT,
        tags TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (linked_campaign_id) REFERENCES social_campaigns(id),
        FOREIGN KEY (linked_account_id) REFERENCES social_accounts(id),
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 5. Publish Queue
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_publish_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content_id INTEGER,
        calendar_id INTEGER,
        account_id INTEGER,
        platform TEXT NOT NULL,
        publish_date DATE NOT NULL,
        publish_time TEXT NOT NULL,
        timezone TEXT DEFAULT 'Asia/Dubai',
        publish_type TEXT DEFAULT 'Scheduled',
        publishing_mode TEXT DEFAULT 'Manual',
        is_group_publish INTEGER DEFAULT 0,
        repeat_pattern TEXT,
        utm_source TEXT,
        utm_medium TEXT,
        utm_campaign TEXT,
        approval_status TEXT DEFAULT 'Approved',
        approved_by_id INTEGER,
        approved_at DATETIME,
        queue_status TEXT DEFAULT 'Queued',
        error_message TEXT,
        attempts INTEGER DEFAULT 0,
        last_attempt_at DATETIME,
        published_at DATETIME,
        notes TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (content_id) REFERENCES social_content_production(id) ON DELETE SET NULL,
        FOREIGN KEY (calendar_id) REFERENCES social_content_calendar(id) ON DELETE SET NULL,
        FOREIGN KEY (account_id) REFERENCES social_accounts(id),
        FOREIGN KEY (approved_by_id) REFERENCES users(id),
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 6. Publish History
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_publish_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        queue_id INTEGER,
        content_id INTEGER,
        account_id INTEGER,
        platform TEXT NOT NULL,
        publish_date DATETIME NOT NULL,
        publish_type TEXT,
        publishing_mode TEXT,
        status TEXT NOT NULL,
        error_code TEXT,
        error_message TEXT,
        reach INTEGER DEFAULT 0,
        impressions INTEGER DEFAULT 0,
        engagement INTEGER DEFAULT 0,
        link_clicks INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (queue_id) REFERENCES social_publish_queue(id),
        FOREIGN KEY (content_id) REFERENCES social_content_production(id),
        FOREIGN KEY (account_id) REFERENCES social_accounts(id)
    )""",

    # -------------------------------------------------------------------------
    # 7. Message Threads
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_message_threads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thread_platform TEXT NOT NULL,
        thread_external_id TEXT,
        sender_name TEXT,
        sender_username TEXT,
        sender_phone TEXT,
        sender_email TEXT,
        sender_country TEXT,
        sender_city TEXT,
        account_id INTEGER,
        platform TEXT NOT NULL,
        thread_type TEXT DEFAULT 'Direct',
        message_count INTEGER DEFAULT 0,
        is_unread INTEGER DEFAULT 1,
        is_starred INTEGER DEFAULT 0,
        is_archived INTEGER DEFAULT 0,
        is_blocked INTEGER DEFAULT 0,
        message_classification TEXT,
        assigned_responder_id INTEGER,
        thread_status TEXT DEFAULT 'Open',
        priority_level TEXT DEFAULT 'Normal',
        tags TEXT,
        last_message_at DATETIME,
        first_response_at DATETIME,
        last_response_at DATETIME,
        avg_response_time_minutes INTEGER,
        sla_breached INTEGER DEFAULT 0,
        notes TEXT,
        internal_notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (account_id) REFERENCES social_accounts(id),
        FOREIGN KEY (assigned_responder_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 8. Message Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thread_id INTEGER,
        message_platform TEXT NOT NULL,
        message_external_id TEXT,
        sender_type TEXT DEFAULT 'User',
        message_text TEXT,
        message_subject TEXT,
        message_type TEXT,
        has_media INTEGER DEFAULT 0,
        media_urls TEXT,
        is_incoming INTEGER DEFAULT 1,
        is_read INTEGER DEFAULT 0,
        read_at DATETIME,
        message_status TEXT DEFAULT 'Received',
        priority_level TEXT DEFAULT 'Normal',
        requires_reply INTEGER DEFAULT 1,
        convert_to_lead INTEGER DEFAULT 0,
        lead_id INTEGER,
        assigned_salesperson_id INTEGER,
        replied_by_id INTEGER,
        replied_at DATETIME,
        reply_text TEXT,
        response_result TEXT,
        sent_via_api INTEGER DEFAULT 0,
        api_message_id TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (thread_id) REFERENCES social_message_threads(id) ON DELETE CASCADE,
        FOREIGN KEY (lead_id) REFERENCES social_leads(id),
        FOREIGN KEY (assigned_salesperson_id) REFERENCES users(id),
        FOREIGN KEY (replied_by_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 9. Social Leads
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_name TEXT NOT NULL,
        phone TEXT,
        whatsapp TEXT,
        email TEXT,
        country TEXT,
        city TEXT,
        customer_type TEXT,
        is_wholesale INTEGER DEFAULT 0,
        is_retail INTEGER DEFAULT 0,
        is_local INTEGER DEFAULT 0,
        is_export INTEGER DEFAULT 0,
        source_platform TEXT,
        source_content_id INTEGER,
        source_campaign_id INTEGER,
        source_post_id TEXT,
        source_ad_id INTEGER,
        brand_interest TEXT,
        product_group_interest TEXT,
        product_interest TEXT,
        part_number_interest TEXT,
        estimated_value DECIMAL(12,2) DEFAULT 0,
        urgency_level TEXT DEFAULT 'Medium',
        funnel_stage TEXT DEFAULT 'Message',
        assigned_salesperson_id INTEGER,
        lead_status TEXT DEFAULT 'New',
        entry_date DATE,
        last_followup_at DATETIME,
        followup_count INTEGER DEFAULT 0,
        next_followup_date DATE,
        final_result TEXT,
        lost_reason TEXT,
        converted_to_customer_id INTEGER,
        converted_to_inquiry_id INTEGER,
        converted_at DATETIME,
        notes TEXT,
        tags TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (source_content_id) REFERENCES social_content_production(id),
        FOREIGN KEY (source_campaign_id) REFERENCES social_campaigns(id),
        FOREIGN KEY (source_ad_id) REFERENCES social_ads(id),
        FOREIGN KEY (assigned_salesperson_id) REFERENCES users(id),
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 10. Lead Follow-ups
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_lead_followups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER NOT NULL,
        followup_date DATETIME NOT NULL,
        followup_type TEXT,
        followup_method TEXT,
        followup_notes TEXT,
        followup_result TEXT,
        next_followup_date DATE,
        next_followup_notes TEXT,
        assigned_to_id INTEGER,
        is_completed INTEGER DEFAULT 0,
        completed_at DATETIME,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (lead_id) REFERENCES social_leads(id) ON DELETE CASCADE,
        FOREIGN KEY (assigned_to_id) REFERENCES users(id),
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 11. Social Campaigns
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_campaigns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_name TEXT NOT NULL,
        campaign_code TEXT UNIQUE,
        campaign_type TEXT,
        campaign_objective TEXT,
        platform TEXT,
        target_market TEXT,
        target_audience TEXT,
        customer_type TEXT,
        target_brand TEXT,
        target_products TEXT,
        target_product_group TEXT,
        start_date DATE,
        end_date DATE,
        approved_budget DECIMAL(12,2) DEFAULT 0,
        actual_budget DECIMAL(12,2) DEFAULT 0,
        campaign_manager_id INTEGER,
        main_message TEXT,
        cta_text TEXT,
        target_landing_url TEXT,
        target_whatsapp TEXT,
        utm_source TEXT,
        utm_medium TEXT,
        utm_campaign TEXT,
        target_kpi TEXT,
        campaign_status TEXT DEFAULT 'Draft',
        approval_state TEXT DEFAULT 'Pending',
        approved_by_id INTEGER,
        approved_at DATETIME,
        total_reach INTEGER DEFAULT 0,
        total_impressions INTEGER DEFAULT 0,
        total_engagement INTEGER DEFAULT 0,
        total_leads INTEGER DEFAULT 0,
        total_inquiries INTEGER DEFAULT 0,
        total_sales DECIMAL(12,2) DEFAULT 0,
        total_conversions INTEGER DEFAULT 0,
        roas DECIMAL(5,2) DEFAULT 0,
        cac DECIMAL(12,2) DEFAULT 0,
        notes TEXT,
        attachments TEXT,
        tags TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (campaign_manager_id) REFERENCES users(id),
        FOREIGN KEY (approved_by_id) REFERENCES users(id),
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 12. Social Ads
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_ads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_campaign_id INTEGER,
        ad_set_name TEXT,
        ad_name TEXT NOT NULL,
        ad_objective TEXT,
        platform TEXT NOT NULL,
        audience_definition TEXT,
        age_min INTEGER DEFAULT 18,
        age_max INTEGER DEFAULT 65,
        gender TEXT,
        locations TEXT,
        languages TEXT,
        customer_type TEXT,
        creative_file TEXT,
        ad_copy TEXT,
        cta_text TEXT,
        daily_budget DECIMAL(12,2) DEFAULT 0,
        total_budget DECIMAL(12,2) DEFAULT 0,
        bid_strategy TEXT,
        start_time DATETIME,
        end_time DATETIME,
        ad_status TEXT DEFAULT 'Draft',
        pixel_event TEXT,
        pixel_ids TEXT,
        reach_estimate INTEGER,
        impressions_count INTEGER DEFAULT 0,
        clicks_count INTEGER DEFAULT 0,
        ctr DECIMAL(5,2) DEFAULT 0,
        engagement_count INTEGER DEFAULT 0,
        messages_count INTEGER DEFAULT 0,
        leads_count INTEGER DEFAULT 0,
        inquiries_count INTEGER DEFAULT 0,
        sales_count INTEGER DEFAULT 0,
        sales_revenue DECIMAL(12,2) DEFAULT 0,
        cost_per_result DECIMAL(12,2) DEFAULT 0,
        amount_spent DECIMAL(12,2) DEFAULT 0,
        results_description TEXT,
        notes TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_campaign_id) REFERENCES social_campaigns(id),
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 13. Audience Definitions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_audiences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        audience_name TEXT NOT NULL,
        audience_code TEXT UNIQUE,
        platform TEXT NOT NULL,
        audience_type TEXT,
        age_min INTEGER DEFAULT 18,
        age_max INTEGER DEFAULT 65,
        genders TEXT,
        locations TEXT,
        languages TEXT,
        interests TEXT,
        behaviors TEXT,
        customer_types TEXT,
        estimated_size INTEGER,
        saved_audience_json TEXT,
        notes TEXT,
        usage_count INTEGER DEFAULT 0,
        last_used_at DATETIME,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 14. Brand & Market Monitoring
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_monitoring (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        monitoring_type TEXT NOT NULL,
        monitored_entity TEXT NOT NULL,
        platform TEXT,
        source_link TEXT,
        observed_text TEXT,
        category TEXT,
        sentiment TEXT,
        importance_level TEXT DEFAULT 'Medium',
        requires_action INTEGER DEFAULT 0,
        assigned_owner_id INTEGER,
        action_taken TEXT,
        action_result TEXT,
        alert_triggered INTEGER DEFAULT 0,
        record_date DATE,
        notes TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (assigned_owner_id) REFERENCES users(id),
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 15. Social Alerts
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_type TEXT NOT NULL,
        alert_title TEXT NOT NULL,
        alert_message TEXT,
        severity TEXT DEFAULT 'Info',
        entity_type TEXT,
        entity_id INTEGER,
        entity_name TEXT,
        linked_platform TEXT,
        linked_account_id INTEGER,
        linked_campaign_id INTEGER,
        linked_content_id INTEGER,
        is_resolved INTEGER DEFAULT 0,
        resolved_at DATETIME,
        resolved_by_user_id INTEGER,
        resolution_notes TEXT,
        alert_data TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (linked_account_id) REFERENCES social_accounts(id),
        FOREIGN KEY (linked_campaign_id) REFERENCES social_campaigns(id),
        FOREIGN KEY (linked_content_id) REFERENCES social_content_production(id),
        FOREIGN KEY (resolved_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 16. Social KPIs
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_kpis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kpi_name TEXT NOT NULL,
        kpi_code TEXT UNIQUE,
        kpi_category TEXT,
        description TEXT,
        metric_unit TEXT,
        target_value DECIMAL(12,4),
        warning_threshold DECIMAL(12,4),
        critical_threshold DECIMAL(12,4),
        higher_is_better INTEGER DEFAULT 1,
        display_order INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 17. KPI Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_kpi_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kpi_id INTEGER NOT NULL,
        record_date DATE NOT NULL,
        record_value DECIMAL(12,4) DEFAULT 0,
        platform TEXT,
        account_id INTEGER,
        campaign_id INTEGER,
        content_id INTEGER,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (kpi_id) REFERENCES social_kpis(id),
        FOREIGN KEY (account_id) REFERENCES social_accounts(id),
        FOREIGN KEY (campaign_id) REFERENCES social_campaigns(id),
        FOREIGN KEY (content_id) REFERENCES social_content_production(id)
    )""",

    # -------------------------------------------------------------------------
    # 18. Social Roles
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_roles (
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
        can_view_all_accounts INTEGER DEFAULT 0,
        status TEXT DEFAULT 'Active',
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 19. Social User Assignments
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_user_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        social_role_id INTEGER NOT NULL,
        assigned_by_id INTEGER,
        assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (social_role_id) REFERENCES social_roles(id),
        FOREIGN KEY (assigned_by_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 20. Saved Replies
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_saved_replies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reply_title TEXT NOT NULL,
        reply_category TEXT,
        reply_text TEXT NOT NULL,
        shortcut_code TEXT,
        platform TEXT,
        message_type TEXT,
        usage_count INTEGER DEFAULT 0,
        last_used_at DATETIME,
        is_active INTEGER DEFAULT 1,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 21. Caption Bank
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_caption_bank (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        caption_text TEXT NOT NULL,
        caption_title TEXT,
        platform TEXT,
        content_type TEXT,
        content_pillar TEXT,
        tone_of_voice TEXT,
        language TEXT DEFAULT 'en',
        usage_count INTEGER DEFAULT 0,
        last_used_at DATETIME,
        tags TEXT,
        is_favorite INTEGER DEFAULT 0,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 22. Hashtag Bank
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_hashtag_bank (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hashtag_text TEXT NOT NULL,
        hashtag_group TEXT,
        platform TEXT,
        usage_count INTEGER DEFAULT 0,
        last_used_at DATETIME,
        avg_performance DECIMAL(5,2) DEFAULT 0,
        is_trending INTEGER DEFAULT 0,
        is_blocked INTEGER DEFAULT 0,
        blocked_reason TEXT,
        tags TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 23. CTA Bank
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_cta_bank (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cta_text TEXT NOT NULL,
        cta_description TEXT,
        cta_type TEXT,
        cta_url TEXT,
        platform TEXT,
        usage_count INTEGER DEFAULT 0,
        last_used_at DATETIME,
        conversion_rate DECIMAL(5,2) DEFAULT 0,
        tags TEXT,
        is_active INTEGER DEFAULT 1,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 24. Content Templates
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_content_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_name TEXT NOT NULL,
        template_code TEXT UNIQUE,
        template_type TEXT,
        platform TEXT,
        content_format TEXT,
        template_structure TEXT,
        default_caption TEXT,
        default_hashtags TEXT,
        default_cta TEXT,
        usage_count INTEGER DEFAULT 0,
        last_used_at DATETIME,
        tags TEXT,
        is_favorite INTEGER DEFAULT 0,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 25. Audit Logs
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_audit_logs (
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
    # 26. Social Settings
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_settings (
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
    # 27. Automations
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_automations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        automation_name TEXT NOT NULL,
        automation_code TEXT UNIQUE,
        automation_type TEXT NOT NULL,
        trigger_event TEXT,
        trigger_conditions TEXT,
        automation_actions TEXT,
        is_active INTEGER DEFAULT 1,
        run_count INTEGER DEFAULT 0,
        last_run_at DATETIME,
        next_run_at DATETIME,
        schedule_pattern TEXT,
        notes TEXT,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )""",

    # -------------------------------------------------------------------------
    # 28. Automation Logs
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS social_automation_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        automation_id INTEGER,
        run_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        trigger_event TEXT,
        actions_executed TEXT,
        records_affected INTEGER DEFAULT 0,
        status TEXT DEFAULT 'Success',
        error_message TEXT,
        execution_time_ms INTEGER,
        FOREIGN KEY (automation_id) REFERENCES social_automations(id) ON DELETE CASCADE
    )""",
]


# =============================================================================
# MIGRATION RUNNER
# =============================================================================

def run_social_media_migrations():
    """Run all social media table migrations."""
    conn = get_db()
    try:
        for table_sql in SOCIAL_MEDIA_TABLES:
            conn.executescript(table_sql)
        conn.commit()
        
        # Seed default data
        seed_social_roles(conn)
        seed_social_kpis(conn)
        seed_social_settings(conn)
        seed_social_platforms(conn)
        seed_content_pillars(conn)
        seed_content_types(conn)
        seed_message_types(conn)
        seed_lead_sources(conn)
        
    finally:
        conn.close()


def seed_social_roles(conn):
    """Seed default social media roles if not exist."""
    existing = conn.execute("SELECT COUNT(*) FROM social_roles").fetchone()[0]
    if existing > 0:
        return
    
    default_roles = [
        ('Super Admin', 'SM-SUPER-ADMIN', 'Full access to all social media features', 1, 1, 1, 1, 1),
        ('COO / Management', 'SM-COO', 'Executive management access', 1, 1, 1, 1, 1),
        ('Marketing Manager', 'SM-MKT-MANAGER', 'Marketing team leadership', 1, 1, 1, 1, 0),
        ('Social Media Manager', 'SM-SMM', 'Social media team management', 1, 1, 1, 1, 0),
        ('Content Creator', 'SM-CREATOR', 'Content creation and drafting', 0, 0, 0, 0, 0),
        ('Designer', 'SM-DESIGNER', 'Design and visual content', 0, 0, 0, 0, 0),
        ('Video Editor', 'SM-VIDEO', 'Video content editing', 0, 0, 0, 0, 0),
        ('Publisher', 'SM-PUBLISHER', 'Publishing and scheduling', 0, 1, 1, 0, 0),
        ('Community Manager', 'SM-CM', 'Community and message management', 0, 0, 0, 0, 0),
        ('Sales User', 'SM-SALES', 'Social leads and sales access', 0, 0, 0, 0, 0),
        ('Analyst', 'SM-ANALYST', 'Analytics and reporting', 0, 0, 0, 0, 0),
        ('Viewer', 'SM-VIEWER', 'Read-only access', 0, 0, 0, 0, 0),
    ]
    
    for name, code, desc, sys, approve, publish, manage, view_all in default_roles:
        conn.execute("""
            INSERT OR IGNORE INTO social_roles 
            (role_name, role_code, description, is_system_role, can_approve, can_publish, can_manage_team, can_view_all_accounts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, code, desc, sys, approve, publish, manage, view_all))


def seed_social_kpis(conn):
    """Seed default social media KPIs if not exist."""
    existing = conn.execute("SELECT COUNT(*) FROM social_kpis").fetchone()[0]
    if existing > 0:
        return
    
    default_kpis = [
        ('Followers Growth', 'FOLLOWERS_GROWTH', 'Growth', 'Monthly follower growth rate', '%', 5, 2, 0, 1, 1),
        ('Reach', 'REACH', 'Reach', 'Total content reach', 'users', 10000, 5000, 1000, 1, 2),
        ('Engagement Rate', 'ENGAGEMENT_RATE', 'Engagement', 'Engagement divided by reach', '%', 5, 3, 1, 1, 3),
        ('Save Rate', 'SAVE_RATE', 'Engagement', 'Saves divided by reach', '%', 3, 1.5, 0.5, 1, 4),
        ('Share Rate', 'SHARE_RATE', 'Engagement', 'Shares divided by reach', '%', 2, 1, 0.25, 1, 5),
        ('Click Rate (CTR)', 'CTR', 'Conversion', 'Clicks divided by reach', '%', 3, 1.5, 0.5, 1, 6),
        ('DM Rate', 'DM_RATE', 'Conversion', 'Messages divided by reach', '%', 2, 1, 0.25, 1, 7),
        ('Lead Rate', 'LEAD_RATE', 'Conversion', 'Leads divided by reach', '%', 2, 1, 0.25, 1, 8),
        ('Conversion Rate', 'CONVERSION_RATE', 'Conversion', 'Purchases divided by leads', '%', 10, 5, 1, 1, 9),
        ('Cost per Lead', 'CPL', 'Financial', 'Amount spent per lead', 'AED', 50, 100, 200, 0, 10),
        ('Cost per Inquiry', 'CPI', 'Financial', 'Amount spent per inquiry', 'AED', 100, 200, 500, 0, 11),
        ('Cost per Order', 'CPO', 'Financial', 'Amount spent per order', 'AED', 500, 1000, 2000, 0, 12),
        ('Revenue from Social', 'REV_SOCIAL', 'Financial', 'Total revenue attributed to social', 'AED', 100000, 50000, 10000, 1, 13),
        ('ROAS', 'ROAS', 'Financial', 'Return on ad spend', 'ratio', 5, 3, 1, 1, 14),
        ('ROI', 'ROI', 'Financial', 'Return on investment', '%', 100, 50, 0, 1, 15),
        ('Response Time', 'RESPONSE_TIME', 'Service', 'Average response time', 'minutes', 30, 60, 120, 0, 16),
        ('Response SLA Compliance', 'SLA_COMPLIANCE', 'Service', 'Messages replied within SLA', '%', 90, 75, 50, 1, 17),
        ('Negative Comment Rate', 'NEG_RATE', 'Reputation', 'Negative comments divided by total', '%', 2, 5, 10, 0, 18),
        ('Content On-Time Rate', 'ONTIME_RATE', 'Operations', 'Content published on schedule', '%', 95, 85, 70, 1, 19),
    ]
    
    for name, code, cat, desc, unit, target, warn, crit, higher, order in default_kpis:
        conn.execute("""
            INSERT OR IGNORE INTO social_kpis 
            (kpi_name, kpi_code, kpi_category, description, metric_unit, target_value, warning_threshold, critical_threshold, higher_is_better, display_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, code, cat, desc, unit, target, warn, crit, higher, order))


def seed_social_settings(conn):
    """Seed default social media settings if not exist."""
    existing = conn.execute("SELECT COUNT(*) FROM social_settings").fetchone()[0]
    if existing > 0:
        return
    
    default_settings = [
        ('timezone', 'Asia/Dubai', 'string', 'general', 'Default timezone for publishing'),
        ('default_language', 'en', 'string', 'general', 'Default content language'),
        ('date_format', 'YYYY-MM-DD', 'string', 'general', 'Date display format'),
        ('time_format', '24h', 'string', 'general', 'Time display format'),
        ('currency', 'AED', 'string', 'general', 'Default currency for values'),
        ('response_sla_minutes', '30', 'number', 'messages', 'SLA for message response in minutes'),
        ('work_calendar_start', '08:00', 'string', 'general', 'Work day start time'),
        ('work_calendar_end', '18:00', 'string', 'general', 'Work day end time'),
        ('work_days', '1,2,3,4,5', 'string', 'general', 'Work days (1=Mon, 7=Sun)'),
        ('holidays', '', 'string', 'general', 'Public holidays (comma separated dates)'),
        ('auto_convert_sales_messages', '1', 'boolean', 'automations', 'Auto-convert sales messages to leads'),
        ('auto_assign_by_country', '1', 'boolean', 'automations', 'Auto-assign leads by country'),
        ('auto_lead_assignment', '0', 'boolean', 'automations', 'Auto-assign new leads'),
        ('alert_unanswered_message_minutes', '60', 'number', 'alerts', 'Alert after X minutes unanswered'),
        ('alert_reach_drop_percent', '25', 'number', 'alerts', 'Alert if reach drops more than X%'),
        ('alert_engagement_drop_percent', '30', 'number', 'alerts', 'Alert if engagement drops more than X%'),
        ('alert_budget_exceeded_percent', '90', 'number', 'alerts', 'Alert if budget exceeds X%'),
        ('alert_weak_ad_performance', '1', 'boolean', 'alerts', 'Alert for weak ad performance'),
        ('alert_low_stock_promotion', '1', 'boolean', 'alerts', 'Alert for promoting low stock items'),
        ('alert_repeated_negative', '3', 'number', 'alerts', 'Alert after X negative comments'),
        ('reminder_ready_unpublished_hours', '24', 'number', 'automations', 'Remind after X hours if content ready but not published'),
        ('daily_report_time', '09:00', 'string', 'automations', 'Time to send daily report'),
        ('weekly_report_day', '1', 'string', 'automations', 'Day of week for weekly report (1=Mon)'),
        ('brand_name', 'SDAD', 'string', 'brand', 'Primary brand name'),
        ('brand_tone', 'Professional', 'string', 'brand', 'Brand tone of voice'),
        ('allowed_ctas', 'Learn More,Shop Now,Contact Us,Get Quote,Call Now', 'string', 'brand', 'Allowed CTA texts'),
        ('part_number_format', 'XXX-XXXXX', 'string', 'brand', 'Part number format pattern'),
        ('instagram_handle', '@sdad_official', 'string', 'accounts', 'Instagram business handle'),
        ('facebook_page', 'SDADOfficial', 'string', 'accounts', 'Facebook page name'),
        ('linkedin_company', 'SDAD-Trading', 'string', 'accounts', 'LinkedIn company page'),
        ('default_caption_length', '2200', 'number', 'content', 'Maximum caption length'),
        ('max_hashtags', '30', 'number', 'content', 'Maximum number of hashtags'),
        ('require_approval_for', 'Campaign,Advertisement', 'string', 'approval', 'Content types requiring approval'),
        ('approval_workflow', 'Creator->Designer->Manager->Publisher', 'string', 'approval', 'Approval workflow steps'),
    ]
    
    for key, value, stype, cat, desc in default_settings:
        conn.execute("""
            INSERT OR IGNORE INTO social_settings 
            (setting_key, setting_value, setting_type, category, description)
            VALUES (?, ?, ?, ?, ?)
        """, (key, value, stype, cat, desc))


def seed_social_platforms(conn):
    """Seed default platforms if not exist."""
    existing = conn.execute("SELECT COUNT(*) FROM social_accounts").fetchone()[0]
    if existing > 0:
        return
    
    # Insert default accounts for demo
    default_accounts = [
        ('Instagram', 'SDAD Official', '@sdad_official', 'https://instagram.com/sdad_official', 'General', 'en', 'Business', 'Active'),
        ('Facebook', 'SDAD Official', '@SDADOfficial', 'https://facebook.com/SDADOfficial', 'General', 'en', 'Business', 'Active'),
        ('LinkedIn', 'SDAD Trading', '@SDAD-Trading', 'https://linkedin.com/company/sdad-trading', 'B2B', 'en', 'Business', 'Active'),
        ('YouTube', 'SDAD Channel', '@sdad_channel', 'https://youtube.com/@sdad_channel', 'General', 'en', 'Business', 'Active'),
        ('WhatsApp Business', 'SDAD Sales', '+971501234567', '', 'Sales', 'en', 'Business', 'Active'),
    ]
    
    for platform, name, username, link, market, lang, atype, status in default_accounts:
        conn.execute("""
            INSERT OR IGNORE INTO social_accounts 
            (platform, account_name, username, account_link, target_market, primary_language, account_type, account_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (platform, name, username, link, market, lang, atype, status))


def seed_content_pillars(conn):
    """Seed default content pillars."""
    existing = conn.execute("SELECT COUNT(*) FROM social_settings WHERE setting_key='content_pillars'").fetchone()[0]
    if existing > 0:
        return
    
    pillars = [
        ('Product Showcase', 'Displaying products and catalog'),
        ('Educational', 'Tips, how-tos, and informative content'),
        ('Entertaining', 'Fun and engaging content'),
        ('Inspirational', 'Aspirational and lifestyle content'),
        ('Promotional', 'Sales, offers, and advertisements'),
        ('Behind the Scenes', 'Company culture and team'),
        ('User Generated', 'Customer content and testimonials'),
        ('Seasonal', 'Holiday and event-based content'),
    ]
    
    for name, desc in pillars:
        conn.execute("""
            INSERT OR IGNORE INTO social_settings (setting_key, setting_value, setting_type, category, description)
            VALUES (?, ?, 'string', 'content', ?)
        """, (f'pillar_{name.lower().replace(" ", "_")}', name, desc))


def seed_content_types(conn):
    """Seed default content types."""
    existing = conn.execute("SELECT COUNT(*) FROM social_settings WHERE setting_key='content_types'").fetchone()[0]
    if existing > 0:
        return
    
    types = [
        ('Post', 'Standard feed post'),
        ('Carousel', 'Multi-image carousel post'),
        ('Story', '24-hour ephemeral story'),
        ('Reel', 'Short-form video'),
        ('Live', 'Live video broadcast'),
        ('Article', 'Long-form article or blog post'),
        ('Poll', 'Interactive poll post'),
        ('Quiz', 'Interactive quiz'),
        ('Question', 'Question/AMA post'),
        ('Video', 'Standard video post'),
        ('GIF', 'Animated GIF post'),
        ('Meme', 'Humor/meme content'),
    ]
    
    for name, desc in types:
        conn.execute("""
            INSERT OR IGNORE INTO social_settings (setting_key, setting_value, setting_type, category, description)
            VALUES (?, ?, 'string', 'content', ?)
        """, (f'type_{name.lower()}', name, desc))


def seed_message_types(conn):
    """Seed default message types."""
    existing = conn.execute("SELECT COUNT(*) FROM social_settings WHERE setting_key='message_types'").fetchone()[0]
    if existing > 0:
        return
    
    types = [
        ('Sales Inquiry', 'Product or pricing questions'),
        ('Stock Inquiry', 'Availability questions'),
        ('Order Follow-up', 'Existing order status'),
        ('Complaint', 'Customer complaint'),
        ('Partnership', 'Business partnership inquiries'),
        ('Hiring', 'Job opportunity questions'),
        ('General Question', 'Other questions'),
        ('Spam', 'Spam or junk messages'),
        ('Support', 'Customer support requests'),
        ('Feedback', 'Suggestions or feedback'),
    ]
    
    for name, desc in types:
        conn.execute("""
            INSERT OR IGNORE INTO social_settings (setting_key, setting_value, setting_type, category, description)
            VALUES (?, ?, 'string', 'messages', ?)
        """, (f'msg_{name.lower().replace(" ", "_")}', name, desc))


def seed_lead_sources(conn):
    """Seed default social lead sources."""
    existing = conn.execute("SELECT COUNT(*) FROM social_settings WHERE setting_key='social_lead_sources'").fetchone()[0]
    if existing > 0:
        return
    
    sources = [
        ('Instagram Post', 'Organic Instagram content'),
        ('Instagram Story', 'Instagram story engagement'),
        ('Instagram Reel', 'Instagram reel views'),
        ('Instagram Ad', 'Instagram advertising'),
        ('Facebook Post', 'Organic Facebook content'),
        ('Facebook Ad', 'Facebook advertising'),
        ('LinkedIn Post', 'Organic LinkedIn content'),
        ('LinkedIn Ad', 'LinkedIn advertising'),
        ('YouTube Video', 'YouTube content'),
        ('YouTube Ad', 'YouTube advertising'),
        ('WhatsApp', 'WhatsApp Business'),
        ('TikTok', 'TikTok content'),
        ('Campaign', 'Marketing campaign'),
        ('Bio Link', 'Link in bio'),
        ('Direct Message', 'Social messaging'),
    ]
    
    for name, desc in sources:
        conn.execute("""
            INSERT OR IGNORE INTO social_settings (setting_key, setting_value, setting_type, category, description)
            VALUES (?, ?, 'string', 'leads', ?)
        """, (f'src_{name.lower().replace(" ", "_")}', name, desc))


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_social_setting(conn, key, default=None):
    """Get a social media setting value."""
    row = conn.execute(
        "SELECT setting_value FROM social_settings WHERE setting_key = ? AND is_active = 1",
        (key,)
    ).fetchone()
    return row['setting_value'] if row else default


def update_social_setting(conn, key, value, user_id=None):
    """Update a social media setting value."""
    conn.execute("""
        UPDATE social_settings SET setting_value = ?, updated_by_user_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE setting_key = ?
    """, (value, user_id, key))
    conn.commit()


def log_social_audit(conn, entity_type, entity_id, action_type, field_name=None, old_value=None, new_value=None, reason=None, user_id=None):
    """Log an audit entry for social media activities."""
    conn.execute("""
        INSERT INTO social_audit_logs (entity_type, entity_id, action_type, field_name, old_value, new_value, change_reason, actor_user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (entity_type, entity_id, action_type, field_name, old_value, new_value, reason, user_id))
    conn.commit()


def get_social_dashboard_data(conn, date_from=None, date_to=None, platform=None, account_id=None):
    """Get dashboard statistics for social media."""
    if date_from is None:
        date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if date_to is None:
        date_to = datetime.now().strftime('%Y-%m-%d')
    
    stats = {}
    
    # Today's posts
    today = datetime.now().strftime('%Y-%m-%d')
    stats['posts_today'] = conn.execute("""
        SELECT COUNT(*) FROM social_publish_history
        WHERE date(publish_date) = ? AND status = 'Published'
    """, (today,)).fetchone()[0]
    
    # Total messages
    stats['total_messages'] = conn.execute("""
        SELECT COUNT(*) FROM social_messages WHERE date(created_at) BETWEEN ? AND ?
    """, (date_from, date_to)).fetchone()[0]
    
    # Unread messages
    stats['unread_messages'] = conn.execute("""
        SELECT COUNT(*) FROM social_message_threads WHERE is_unread = 1 AND is_archived = 0
    """).fetchone()[0]
    
    # Unanswered messages (no response within SLA)
    sla_minutes = int(get_social_setting(conn, 'response_sla_minutes', '30'))
    stats['unanswered_messages'] = conn.execute("""
        SELECT COUNT(*) FROM social_message_threads 
        WHERE thread_status = 'Open' 
        AND is_unread = 1 
        AND message_count > 0
        AND (last_message_at IS NULL OR 
             (strftime('%s', 'now') - strftime('%s', last_message_at)) > ?)
    """, (sla_minutes * 60,)).fetchone()[0]
    
    # New leads
    stats['new_leads'] = conn.execute("""
        SELECT COUNT(*) FROM social_leads WHERE date(created_at) BETWEEN ? AND ?
    """, (date_from, date_to)).fetchone()[0]
    
    # Active campaigns
    stats['active_campaigns'] = conn.execute("""
        SELECT COUNT(*) FROM social_campaigns WHERE campaign_status = 'Active'
    """).fetchone()[0]
    
    # Total accounts
    stats['total_accounts'] = conn.execute("""
        SELECT COUNT(*) FROM social_accounts WHERE inactive_archive = 0
    """).fetchone()[0]
    
    # Platform breakdown
    stats['platforms'] = conn.execute("""
        SELECT platform, COUNT(*) as count FROM social_accounts 
        WHERE inactive_archive = 0 GROUP BY platform
    """).fetchall()
    
    # Recent leads
    stats['recent_leads'] = conn.execute("""
        SELECT l.*, u.username as assigned_to_name
        FROM social_leads l
        LEFT JOIN users u ON l.assigned_salesperson_id = u.id
        ORDER BY l.created_at DESC LIMIT 10
    """).fetchall()
    
    # Top performing content
    stats['top_content'] = conn.execute("""
        SELECT a.*, c.display_title, c.internal_title
        FROM social_content_archive a
        LEFT JOIN social_content_production c ON a.content_code = c.content_code
        ORDER BY a.engagement DESC LIMIT 5
    """).fetchall()
    
    # Alerts count
    stats['open_alerts'] = conn.execute("""
        SELECT COUNT(*) FROM social_alerts WHERE is_resolved = 0
    """).fetchone()[0]
    
    # Content by status
    stats['content_by_status'] = conn.execute("""
        SELECT production_status, COUNT(*) as count
        FROM social_content_production GROUP BY production_status
    """).fetchall()
    
    return stats


def get_campaign_summary_stats(conn, campaign_id=None):
    """Get summary statistics for campaigns."""
    query = """
        SELECT 
            COUNT(*) as total_campaigns,
            SUM(CASE WHEN campaign_status = 'Active' THEN 1 ELSE 0 END) as active,
            SUM(CASE WHEN campaign_status = 'Completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN campaign_status = 'Draft' THEN 1 ELSE 0 END) as draft,
            SUM(actual_budget) as total_spent,
            SUM(total_leads) as total_leads,
            SUM(total_sales) as total_revenue,
            AVG(roas) as avg_roas
        FROM social_campaigns
    """
    if campaign_id:
        query += " WHERE id = ?"
        return dict(conn.execute(query, (campaign_id,)).fetchone())
    return dict(conn.execute(query).fetchone())


def get_content_performance(conn, date_from=None, date_to=None, platform=None):
    """Get content performance metrics."""
    if date_from is None:
        date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if date_to is None:
        date_to = datetime.now().strftime('%Y-%m-%d')
    
    query = """
        SELECT * FROM social_content_archive
        WHERE date(published_at) BETWEEN ? AND ?
    """
    params = [date_from, date_to]
    
    if platform:
        query += " AND platform = ?"
        params.append(platform)
    
    query += " ORDER BY engagement DESC"
    return conn.execute(query, params).fetchall()


if __name__ == '__main__':
    print("Running Social Media migrations...")
    run_social_media_migrations()
    print("Social Media tables created successfully!")
