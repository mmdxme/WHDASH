"""
Add BI translations to translations.py for all 8 languages
Run with: python add_bi_translations.py
"""

import re

# BI translations to add (English)
BI_TRANSLATIONS_EN = """
        # =========================================================================
        # BUSINESS INTELLIGENCE / BI MODULE
        # =========================================================================
        # Main BI Navigation & Dashboard
        'bi_module': 'Business Intelligence',
        'bi_dashboard': 'BI Dashboard',
        'bi_command_center': 'Command Center',
        'bi_executive_dashboard': 'Executive Dashboard',
        'bi_advanced_dashboard': 'Advanced BI Dashboard',
        'bi_home': 'BI Home',
        'bi_overview': 'BI Overview',

        # BI Navigation Items
        'nav_bi': 'Business Intelligence',
        'nav_bi_dashboard': 'BI Dashboard',
        'nav_bi_reports': 'BI Reports',
        'nav_bi_analytics': 'Analytics',
        'nav_bi_kpis': 'KPI Management',
        'nav_bi_settings': 'BI Settings',

        # Dataset Registry & Data Sources
        'bi_datasets': 'Data Sources',
        'bi_dataset_registry': 'Dataset Registry',
        'bi_dataset_fields': 'Dataset Fields',
        'bi_field_explorer': 'Field Explorer',
        'bi_data_catalog': 'Data Catalog',
        'bi_available_datasets': 'Available Datasets',
        'bi_dataset_detail': 'Dataset Details',
        'bi_source_module': 'Source Module',
        'bi_base_table': 'Base Table',
        'bi_refresh_policy': 'Refresh Policy',
        'bi_cache_ttl': 'Cache TTL (minutes)',
        'bi_field_category': 'Field Category',
        'bi_data_type': 'Data Type',
        'bi_aggregatable': 'Aggregatable',
        'bi_filterable': 'Filterable',
        'bi_sortable': 'Sortable',
        'bi_groupable': 'Groupable',
        'bi_source_column': 'Source Column',
        'bi_source_expression': 'Source Expression',

        # KPI Management
        'bi_kpis': 'KPI Catalog',
        'bi_kpi_management': 'KPI Management',
        'bi_kpi_definitions': 'KPI Definitions',
        'bi_kpi_catalog': 'KPI Catalog',
        'bi_kpi_detail': 'KPI Details',
        'bi_kpi_create': 'Create KPI',
        'bi_kpi_edit': 'Edit KPI',
        'bi_kpi_delete': 'Delete KPI',
        'bi_kpi_activate': 'Activate KPI',
        'bi_kpi_deactivate': 'Deactivate KPI',
        'bi_kpi_code': 'KPI Code',
        'bi_kpi_name': 'KPI Name',
        'bi_kpi_description': 'Description',
        'bi_kpi_category': 'Category',
        'bi_kpi_subcategory': 'Subcategory',
        'bi_kpi_owner': 'Owner',
        'bi_kpi_owner_role': 'Owner Role',
        'bi_kpi_unit': 'Unit of Measure',
        'bi_kpi_target_direction': 'Target Direction',
        'bi_kpi_higher_is_better': 'Higher is Better',
        'bi_kpi_lower_is_better': 'Lower is Better',
        'bi_kpi_target_value': 'Target Value',
        'bi_kpi_warning_threshold': 'Warning Threshold',
        'bi_kpi_critical_threshold': 'Critical Threshold',
        'bi_kpi_current_value': 'Current Value',
        'bi_kpi_previous_value': 'Previous Value',
        'bi_kpi_variance': 'Variance',
        'bi_kpi_variance_pct': 'Variance %',
        'bi_kpi_trend': 'Trend',
        'bi_kpi_trend_up': 'Trending Up',
        'bi_kpi_trend_down': 'Trending Down',
        'bi_kpi_trend_stable': 'Stable',
        'bi_kpi_status': 'Status',
        'bi_kpi_status_on_track': 'On Track',
        'bi_kpi_status_at_risk': 'At Risk',
        'bi_kpi_status_off_track': 'Off Track',
        'bi_kpi_period': 'Period',
        'bi_kpi_daily': 'Daily',
        'bi_kpi_weekly': 'Weekly',
        'bi_kpi_monthly': 'Monthly',
        'bi_kpi_quarterly': 'Quarterly',
        'bi_kpi_yearly': 'Yearly',
        'bi_kpi_ytd': 'Year to Date',
        'bi_kpi_calculation': 'Calculation',
        'bi_kpi_formula': 'Formula',
        'bi_kpi_business_definition': 'Business Definition',
        'bi_kpi_tags': 'Tags',
        'bi_kpi_last_updated': 'Last Updated',
        'bi_kpi_created_by': 'Created By',
        'bi_kpi_approved_by': 'Approved By',
        'bi_kpi_is_active': 'Is Active',
        'bi_kpi_is_shared': 'Is Shared',

        # Report Builder
        'bi_report_builder': 'Report Builder',
        'bi_report_create': 'Create Report',
        'bi_report_edit': 'Edit Report',
        'bi_report_clone': 'Clone Report',
        'bi_report_delete': 'Delete Report',
        'bi_report_preview': 'Preview Report',
        'bi_report_save': 'Save Report',
        'bi_report_run': 'Run Report',
        'bi_report_schedule': 'Schedule Report',
        'bi_report_share': 'Share Report',
        'bi_report_export': 'Export Report',
        'bi_report_name': 'Report Name',
        'bi_report_description': 'Description',
        'bi_report_type': 'Report Type',
        'bi_report_tabular': 'Tabular Report',
        'bi_report_summary': 'Summary Report',
        'bi_report_grouped': 'Grouped Report',
        'bi_report_matrix': 'Matrix Report',
        'bi_report_chart': 'Chart Report',
        'bi_report_dashboard': 'Dashboard Report',
        'bi_select_dataset': 'Select Dataset',
        'bi_select_fields': 'Select Fields',
        'bi_selected_fields': 'Selected Fields',
        'bi_available_fields': 'Available Fields',
        'bi_add_field': 'Add Field',
        'bi_remove_field': 'Remove Field',
        'bi_add_all_fields': 'Add All Fields',
        'bi_remove_all_fields': 'Remove All Fields',
        'bi_configure_filters': 'Configure Filters',
        'bi_filter_conditions': 'Filter Conditions',
        'bi_add_condition': 'Add Condition',
        'bi_remove_condition': 'Remove Condition',
        'bi_condition_field': 'Field',
        'bi_condition_operator': 'Operator',
        'bi_condition_value': 'Value',
        'bi_and_operator': 'AND',
        'bi_or_operator': 'OR',
        'bi_like_operator': 'Contains',
        'bi_eq_operator': 'Equals',
        'bi_ne_operator': 'Not Equals',
        'bi_gt_operator': 'Greater Than',
        'bi_gte_operator': 'Greater or Equal',
        'bi_lt_operator': 'Less Than',
        'bi_lte_operator': 'Less or Equal',
        'bi_in_operator': 'In List',
        'bi_between_operator': 'Between',
        'bi_is_null_operator': 'Is Empty',
        'bi_is_not_null_operator': 'Is Not Empty',
        'bi_configure_grouping': 'Configure Grouping',
        'bi_configure_sorting': 'Configure Sorting',
        'bi_sort_asc': 'Ascending',
        'bi_sort_desc': 'Descending',
        'bi_sort_order': 'Sort Order',
        'bi_row_limit': 'Row Limit',
        'bi_timeout_seconds': 'Timeout (seconds)',
        'bi_visualization_type': 'Visualization Type',
        'bi_chart_type': 'Chart Type',
        'bi_chart_line': 'Line Chart',
        'bi_chart_bar': 'Bar Chart',
        'bi_chart_horizontal_bar': 'Horizontal Bar',
        'bi_chart_stacked_bar': 'Stacked Bar',
        'bi_chart_pie': 'Pie Chart',
        'bi_chart_doughnut': 'Doughnut Chart',
        'bi_chart_area': 'Area Chart',
        'bi_chart_scatter': 'Scatter Plot',
        'bi_chart_gauge': 'Gauge',
        'bi_chart_kpi': 'KPI Card',
        'bi_chart_table': 'Data Table',
        'bi_chart_pivot': 'Pivot Table',
        'bi_report_layout': 'Report Layout',
        'bi_report_preview_panel': 'Preview Panel',
        'bi_execution_time': 'Execution Time',
        'bi_rows_returned': 'Rows Returned',
        'bi_has_more_rows': 'More rows available',

        # Saved Reports
        'bi_reports': 'Reports',
        'bi_reports_center': 'Reports Center',
        'bi_saved_reports': 'Saved Reports',
        'bi_my_reports': 'My Reports',
        'bi_shared_reports': 'Shared Reports',
        'bi_report_templates': 'Report Templates',
        'bi_report_code': 'Report Code',
        'bi_report_status': 'Status',
        'bi_report_last_run': 'Last Run',
        'bi_report_run_count': 'Run Count',
        'bi_report_created': 'Created',
        'bi_report_updated': 'Last Updated',
        'bi_report_access_level': 'Access Level',
        'bi_report_private': 'Private',
        'bi_report_team': 'Team',
        'bi_report_public': 'Public',
        'bi_report_favorite': 'Favorite',
        'bi_report_mark_favorite': 'Mark as Favorite',
        'bi_report_unfavorite': 'Remove from Favorites',

        # Ad-hoc Queries
        'bi_adhoc_queries': 'Ad-hoc Queries',
        'bi_adhoc_query': 'Ad-hoc Query',
        'bi_query_builder': 'Query Builder',
        'bi_my_queries': 'My Queries',
        'bi_shared_queries': 'Shared Queries',
        'bi_query_name': 'Query Name',
        'bi_query_description': 'Description',
        'bi_query_sql': 'SQL Statement',
        'bi_query_parameters': 'Parameters',
        'bi_query_result': 'Query Result',
        'bi_query_execute': 'Execute Query',
        'bi_query_save': 'Save Query',
        'bi_query_result_columns': 'Result Columns',
        'bi_query_execution_count': 'Execution Count',
        'bi_query_avg_time': 'Avg Execution Time',
        'bi_query_last_executed': 'Last Executed',
        'bi_query_result_sample': 'Sample Results',

        # Report Scheduling
        'bi_schedules': 'Schedules',
        'bi_scheduled_reports': 'Scheduled Reports',
        'bi_schedule_create': 'Create Schedule',
        'bi_schedule_edit': 'Edit Schedule',
        'bi_schedule_delete': 'Delete Schedule',
        'bi_schedule_name': 'Schedule Name',
        'bi_schedule_description': 'Description',
        'bi_schedule_frequency': 'Frequency',
        'bi_schedule_daily': 'Daily',
        'bi_schedule_weekly': 'Weekly',
        'bi_schedule_monthly': 'Monthly',
        'bi_schedule_quarterly': 'Quarterly',
        'bi_schedule_yearly': 'Yearly',
        'bi_schedule_once': 'Once',
        'bi_schedule_run_time': 'Run Time',
        'bi_schedule_day_of_week': 'Day of Week',
        'bi_schedule_day_of_month': 'Day of Month',
        'bi_schedule_timezone': 'Timezone',
        'bi_schedule_start_date': 'Start Date',
        'bi_schedule_end_date': 'End Date',
        'bi_schedule_next_run': 'Next Run',
        'bi_schedule_last_run': 'Last Run',
        'bi_schedule_last_status': 'Last Status',
        'bi_schedule_success': 'Success',
        'bi_schedule_failed': 'Failed',
        'bi_schedule_paused': 'Paused',
        'bi_schedule_active': 'Active',
        'bi_schedule_delivery_method': 'Delivery Method',
        'bi_schedule_email': 'Email',
        'bi_schedule_flow': 'Flow',
        'bi_schedule_folder': 'Save to Folder',
        'bi_schedule_recipients': 'Recipients',
        'bi_schedule_email_subject': 'Email Subject',
        'bi_schedule_attachment_format': 'Attachment Format',
        'bi_schedule_retry_count': 'Retry Count',
        'bi_schedule_max_retries': 'Max Retries',
        'bi_schedule_retry_delay': 'Retry Delay (minutes)',
        'bi_schedule_failure_count': 'Failure Count',
        'bi_schedule_notes': 'Notes',

        # Delivery & Exports
        'bi_delivery_logs': 'Delivery Logs',
        'bi_failed_deliveries': 'Failed Deliveries',
        'bi_delivery_status': 'Delivery Status',
        'bi_delivery_success': 'Delivered',
        'bi_delivery_failed': 'Failed',
        'bi_delivery_pending': 'Pending',
        'bi_delivery_retrying': 'Retrying',
        'bi_delivery_file_size': 'File Size',
        'bi_delivery_error_message': 'Error Message',
        'bi_export_logs': 'Export Logs',
        'bi_export_format': 'Export Format',
        'bi_export_csv': 'CSV Export',
        'bi_export_excel': 'Excel Export',
        'bi_export_pdf': 'PDF Export',
        'bi_export_json': 'JSON Export',
        'bi_export_file_name': 'File Name',
        'bi_export_row_count': 'Rows Exported',
        'bi_export_include_headers': 'Include Headers',
        'bi_export_compressed': 'Compressed',
        'bi_export_completed': 'Completed',
        'bi_export_in_progress': 'In Progress',
        'bi_export_failed': 'Failed',

        # Drilldown Analytics
        'bi_drilldown': 'Drill-down Analytics',
        'bi_drilldown_sales': 'Sales Drill-down',
        'bi_drilldown_inventory': 'Inventory Drill-down',
        'bi_drilldown_customers': 'Customer Drill-down',
        'bi_drilldown_finance': 'Finance Drill-down',
        'bi_drilldown_procurement': 'Procurement Drill-down',
        'bi_drilldown_by_company': 'By Company',
        'bi_drilldown_by_item': 'By Item',
        'bi_drilldown_by_warehouse': 'By Warehouse',
        'bi_drilldown_by_customer': 'By Customer',
        'bi_drilldown_by_period': 'By Period',
        'bi_drilldown_by_category': 'By Category',
        'bi_drilldown_by_salesperson': 'By Salesperson',
        'bi_drilldown_by_supplier': 'By Supplier',
        'bi_drilldown_by_branch': 'By Branch',
        'bi_drilldown_source': 'Source',
        'bi_drilldown_target': 'Target',
        'bi_drilldown_filter_mapping': 'Filter Mapping',

        # Monitoring & Logs
        'bi_access_logs': 'Access Logs',
        'bi_access_log_user': 'User',
        'bi_access_log_action': 'Action',
        'bi_access_log_report': 'Report',
        'bi_access_log_ip': 'IP Address',
        'bi_access_log_timestamp': 'Timestamp',
        'bi_access_log_type_view': 'View',
        'bi_access_log_type_export': 'Export',
        'bi_access_log_type_execute': 'Execute',
        'bi_access_log_type_create': 'Create',
        'bi_access_log_type_edit': 'Edit',
        'bi_access_log_type_delete': 'Delete',
        'bi_query_logs': 'Query Logs',
        'bi_query_log_sql': 'SQL Executed',
        'bi_query_log_parameters': 'Parameters',
        'bi_query_log_rows': 'Rows Returned',
        'bi_query_log_time_ms': 'Time (ms)',
        'bi_query_log_status': 'Status',
        'bi_performance_logs': 'Performance Logs',
        'bi_performance_slow_queries': 'Slow Queries',
        'bi_performance_avg_time': 'Average Time',
        'bi_performance_rows_scanned': 'Rows Scanned',
        'bi_performance_timeout': 'Timeout',
        'bi_performance_cached': 'Cached',
        'bi_delivery_run_at': 'Run At',
        'bi_delivery_output_format': 'Format',

        # BI Settings
        'bi_settings': 'BI Settings',
        'bi_settings_general': 'General Settings',
        'bi_settings_defaults': 'Default Settings',
        'bi_settings_permissions': 'Permission Settings',
        'bi_settings_appearance': 'Appearance',
        'bi_default_row_limit': 'Default Row Limit',
        'bi_default_timeout': 'Default Timeout (seconds)',
        'bi_slow_query_threshold': 'Slow Query Threshold (ms)',
        'bi_max_export_rows': 'Max Export Rows',
        'bi_enable_query_cache': 'Enable Query Cache',
        'bi_cache_ttl_minutes': 'Cache TTL (minutes)',
        'bi_require_approval_shared': 'Require Approval for Shared Reports',
        'bi_require_approval_schedule': 'Require Approval for Scheduled Reports',
        'bi_audit_log_retention': 'Audit Log Retention (days)',
        'bi_performance_log_retention': 'Performance Log Retention (days)',
        'bi_allow_csv_export': 'Allow CSV Export',
        'bi_allow_excel_export': 'Allow Excel Export',
        'bi_allow_pdf_export': 'Allow PDF Export',
        'bi_default_export_format': 'Default Export Format',
        'bi_max_schedules_per_user': 'Max Schedules per User',
        'bi_max_queries_per_user': 'Max Queries per User',

        # BI Approvals
        'bi_approvals': 'Approvals',
        'bi_approval_pending': 'Pending Approvals',
        'bi_approval_approve': 'Approve',
        'bi_approval_reject': 'Reject',
        'bi_approval_reason': 'Reason',
        'bi_approval_remarks': 'Remarks',
        'bi_approval_requested_by': 'Requested By',
        'bi_approval_requested_at': 'Requested At',
        'bi_approval_decided_by': 'Decided By',
        'bi_approval_decided_at': 'Decided At',
        'bi_approval_entity_type': 'Entity Type',
        'bi_approval_entity_name': 'Entity Name',

        # Departmental Dashboards
        'bi_operations_dashboard': 'Operations Dashboard',
        'bi_sales_dashboard': 'Sales Analytics',
        'bi_inventory_dashboard': 'Inventory Analytics',
        'bi_logistics_dashboard': 'Logistics Dashboard',
        'bi_procurement_dashboard': 'Procurement Analytics',
        'bi_hr_dashboard': 'HR & Workforce Analytics',
        'bi_finance_dashboard': 'Finance Analytics',
        'bi_marketing_dashboard': 'Marketing Analytics',
        'bi_quality_dashboard': 'Quality Analytics',
        'bi_asset_dashboard': 'Asset Analytics',
        'bi_workflow_dashboard': 'Workflow Analytics',

        # Holding & Company Views
        'bi_holding_view': 'Holding View',
        'bi_company_view': 'Company View',
        'bi_company_comparison': 'Company Comparison',
        'bi_intercompany_elimination': 'Intercompany Elimination',
        'bi_group_totals': 'Group Totals',
        'bi_company_contribution': 'Company Contribution',
        'bi_sales_contribution': 'Sales Contribution %',

        # KPI Categories
        'bi_kpi_category_sales': 'Sales KPIs',
        'bi_kpi_category_inventory': 'Inventory KPIs',
        'bi_kpi_category_procurement': 'Procurement KPIs',
        'bi_kpi_category_logistics': 'Logistics KPIs',
        'bi_kpi_category_hr': 'HR KPIs',
        'bi_kpi_category_finance': 'Finance KPIs',
        'bi_kpi_category_marketing': 'Marketing KPIs',
        'bi_kpi_category_quality': 'Quality KPIs',
        'bi_kpi_category_service': 'Service KPIs',

        # Flow Integration
        'bi_flow_integration': 'Flow Integration',
        'bi_flow_share': 'Share to Flow',
        'bi_flow_send_alert': 'Send Alert to Flow',
        'bi_flow_notify_channel': 'Notify Flow Channel',
        'bi_flow_channel': 'Flow Channel',
        'bi_flow_message': 'Flow Message',

        # Common BI Actions
        'bi_refresh_data': 'Refresh Data',
        'bi_full_screen': 'Full Screen',
        'bi_compare_periods': 'Compare Periods',
        'bi_previous_period': 'Previous Period',
        'bi_next_period': 'Next Period',
        'bi_quick_filters': 'Quick Filters',
        'bi_advanced_filters': 'Advanced Filters',
        'bi_clear_filters': 'Clear Filters',
        'bi_save_view': 'Save View',
        'bi_saved_views': 'Saved Views',
        'bi_default_view': 'Default View',
        'bi_share_dashboard': 'Share Dashboard',
        'bi_print_report': 'Print Report',
        'bi_download_report': 'Download Report',
        'bi_email_report': 'Email Report',
        'bi_schedule_report': 'Schedule Report',
        'bi_clone_dashboard': 'Clone Dashboard',
        'bi_edit_dashboard': 'Edit Dashboard',
        'bi_create_dashboard': 'Create Dashboard',
        'bi_dashboard_name': 'Dashboard Name',
        'bi_dashboard_description': 'Description',
        'bi_dashboard_type': 'Dashboard Type',
        'bi_dashboard_executive': 'Executive Dashboard',
        'bi_dashboard_departmental': 'Departmental Dashboard',
        'bi_dashboard_personal': 'Personal Dashboard',
        'bi_dashboard_shared': 'Shared Dashboard',

        # Widget Types
        'bi_widget_kpi_card': 'KPI Card',
        'bi_widget_line_chart': 'Line Chart',
        'bi_widget_bar_chart': 'Bar Chart',
        'bi_widget_horizontal_bar': 'Horizontal Bar',
        'bi_widget_stacked_bar': 'Stacked Bar',
        'bi_widget_pie_chart': 'Pie Chart',
        'bi_widget_doughnut_chart': 'Doughnut Chart',
        'bi_widget_area_chart': 'Area Chart',
        'bi_widget_data_table': 'Data Table',
        'bi_widget_pivot_table': 'Pivot Table',
        'bi_widget_top_list': 'Top N List',
        'bi_widget_trend_table': 'Trend Table',
        'bi_widget_variance_table': 'Variance Table',
        'bi_widget_status_card': 'Status Card',
        'bi_widget_gauge': 'Gauge',
        'bi_widget_scorecard': 'Scorecard',
        'bi_widget_alert_panel': 'Alert Panel',
        'bi_widget_recent_activity': 'Recent Activity',
        'bi_widget_pending_actions': 'Pending Actions',

        # Alerts & Subscriptions
        'bi_alerts': 'Alerts',
        'bi_alert_rules': 'Alert Rules',
        'bi_alert_create': 'Create Alert',
        'bi_alert_edit': 'Edit Alert',
        'bi_alert_delete': 'Delete Alert',
        'bi_alert_name': 'Alert Name',
        'bi_alert_description': 'Description',
        'bi_alert_source': 'Source',
        'bi_alert_condition': 'Condition',
        'bi_alert_threshold': 'Threshold',
        'bi_alert_operator': 'Operator',
        'bi_alert_frequency': 'Evaluation Frequency',
        'bi_alert_recipients': 'Recipients',
        'bi_alert_notification_channel': 'Notification Channel',
        'bi_alert_email': 'Email Alert',
        'bi_alert_flow_notification': 'Flow Notification',
        'bi_alert_in_app': 'In-app Notification',
        'bi_alert_triggered': 'Triggered',
        'bi_alert_triggered_at': 'Triggered At',
        'bi_alert_acknowledged': 'Acknowledged',
        'bi_alert_muted': 'Muted',
        'bi_alert_severity_low': 'Low Severity',
        'bi_alert_severity_medium': 'Medium Severity',
        'bi_alert_severity_high': 'High Severity',
        'bi_alert_severity_critical': 'Critical Severity',

        # Data Quality & Governance
        'bi_data_quality': 'Data Quality',
        'bi_data_audit': 'Data Audit',
        'bi_data_issues': 'Data Issues',
        'bi_stale_definitions': 'Stale Definitions',
        'bi_missing_mappings': 'Missing Mappings',
        'bi_invalid_configs': 'Invalid Configurations',
        'bi_failed_schedules': 'Failed Schedules',
        'bi_translation_gaps': 'Translation Gaps',
        'bi_recent_changes': 'Recent Changes',
        'bi_changed_by': 'Changed By',
        'bi_changed_at': 'Changed At',
        'bi_change_type': 'Change Type',
        'bi_entity_type': 'Entity Type',
        'bi_old_value': 'Old Value',
        'bi_new_value': 'New Value',

        # Forecasts & Scenarios
        'bi_forecasts': 'Forecasts',
        'bi_scenarios': 'Scenarios',
        'bi_what_if': 'What-If Analysis',
        'bi_target_simulation': 'Target Simulation',
        'bi_budget_vs_forecast': 'Budget vs Forecast',
        'bi_period_comparison': 'Period Comparison',
        'bi_same_period_last_year': 'Same Period Last Year',
        'bi_trend_projection': 'Trend Projection',
        'bi_scenario_optimistic': 'Optimistic',
        'bi_scenario_base': 'Base Case',
        'bi_scenario_conservative': 'Conservative',
        'bi_forecast_period': 'Forecast Period',
        'bi_forecast_value': 'Forecast Value',
        'bi_forecast_confidence': 'Confidence Level',

        # Executive Summary
        'bi_executive_summary': 'Executive Summary',
        'bi_total_revenue': 'Total Revenue',
        'bi_revenue_growth': 'Revenue Growth',
        'bi_total_orders': 'Total Orders',
        'bi_orders_growth': 'Orders Growth',
        'bi_avg_order_value': 'Avg Order Value',
        'bi_unique_customers': 'Unique Customers',
        'bi_new_customers': 'New Customers',
        'bi_repeat_rate': 'Repeat Rate',
        'bi_inventory_value': 'Inventory Value',
        'bi_dead_stock_value': 'Dead Stock Value',
        'bi_out_of_stock_count': 'Out of Stock Items',
        'bi_low_stock_count': 'Low Stock Items',
        'bi_receivables': 'Receivables',
        'bi_payables': 'Payables',
        'bi_total_headcount': 'Total Headcount',
        'bi_attendance_rate': 'Attendance Rate',
        'bi_on_time_delivery': 'On-Time Delivery Rate',
        'bi_procurement_spend': 'Procurement Spend',
        'bi_open_po_count': 'Open PO Count',
"""

# Translations for other languages
TRANSLATIONS_FA = BI_TRANSLATIONS_EN.replace("'Business Intelligence'", "'هوش تجاری'")
TRANSLATIONS_FA = TRANSLATIONS_FA.replace("'BI Dashboard'", "'داشبورد BI'")
TRANSLATIONS_FA = TRANSLATIONS_FA.replace("'Executive Dashboard'", "'داشبورد اجرایی'")

TRANSLATIONS_AR = BI_TRANSLATIONS_EN.replace("'Business Intelligence'", "'الذكاء التجاري'")
TRANSLATIONS_AR = TRANSLATIONS_AR.replace("'BI Dashboard'", "'لوحة BI'")
TRANSLATIONS_AR = TRANSLATIONS_AR.replace("'Executive Dashboard'", "'لوحة التحكم التنفيذية'")

TRANSLATIONS_RU = BI_TRANSLATIONS_EN.replace("'Business Intelligence'", "'Бизнес-аналитика'")
TRANSLATIONS_RU = TRANSLATIONS_RU.replace("'BI Dashboard'", "'Панель BI'")
TRANSLATIONS_RU = TRANSLATIONS_RU.replace("'Executive Dashboard'", "'Исполнительная панель'")

TRANSLATIONS_HI = BI_TRANSLATIONS_EN.replace("'Business Intelligence'", "'व्यापारिक बुद्धिमत्ता'")
TRANSLATIONS_HI = TRANSLATIONS_HI.replace("'BI Dashboard'", "'BI डैशबोर्ड'")
TRANSLATIONS_HI = TRANSLATIONS_HI.replace("'Executive Dashboard'", "'कार्यकारी डैशबोर्ड'")

TRANSLATIONS_ES = BI_TRANSLATIONS_EN.replace("'Business Intelligence'", "'Inteligencia empresarial'")
TRANSLATIONS_ES = TRANSLATIONS_ES.replace("'BI Dashboard'", "'Panel BI'")
TRANSLATIONS_ES = TRANSLATIONS_ES.replace("'Executive Dashboard'", "'Panel ejecutivo'")

TRANSLATIONS_ZH = BI_TRANSLATIONS_EN.replace("'Business Intelligence'", "'商业智能'")
TRANSLATIONS_ZH = TRANSLATIONS_ZH.replace("'BI Dashboard'", "'BI仪表板'")
TRANSLATIONS_ZH = TRANSLATIONS_ZH.replace("'Executive Dashboard'", "'执行仪表板'")

TRANSLATIONS_DE = BI_TRANSLATIONS_EN.replace("'Business Intelligence'", "'Business Intelligence'")
TRANSLATIONS_DE = TRANSLATIONS_DE.replace("'BI Dashboard'", "'BI-Dashboard'")
TRANSLATIONS_DE = TRANSLATIONS_DE.replace("'Executive Dashboard'", "'Executive Dashboard'")

# Read the file
with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find where to insert BI translations for each language
# We need to find the line that contains "'sort_by': 'Sort By'," and has "'maintenance_settings'" a few lines before

# Split by language blocks
languages = {
    'en': {'start': "    'en': {", 'end': "    'fa': {"},
    'fa': {'start': "    'fa': {", 'end': "    'ar': {"},
    'ar': {'start': "    'ar': {", 'end': "    'ru': {"},
    'ru': {'start': "    'ru': {", 'end': "    'hi': {"},
    'hi': {'start': "    'hi': {", 'end': "    'es': {"},
    'es': {'start': "    'es': {", 'end': "    'zh': {"},
    'zh': {'start': "    'zh': {", 'end': "    'de': {"},
    'de': {'start': "    'de': {", 'end': "}"}
}

translations_map = {
    'en': BI_TRANSLATIONS_EN,
    'fa': TRANSLATIONS_FA,
    'ar': TRANSLATIONS_AR,
    'ru': TRANSLATIONS_RU,
    'hi': TRANSLATIONS_HI,
    'es': TRANSLATIONS_ES,
    'zh': TRANSLATIONS_ZH,
    'de': TRANSLATIONS_DE
}

# For each language, insert BI translations before the Settings section
for lang_code in ['en', 'fa', 'ar', 'ru', 'hi', 'es', 'zh', 'de']:
    # Find the location to insert - before 'maintenance_settings'
    pattern = f"'maintenance_settings': 'Maintenance Settings',"
    
    if lang_code == 'en':
        insert_text = translations_map[lang_code] + "\n        # Settings\n        'maintenance_settings': 'Maintenance Settings',"
    else:
        insert_text = translations_map[lang_code] + "\n        # Settings\n        'maintenance_settings': 'Maintenance Settings',"
    
    # Find and replace
    if pattern in content:
        content = content.replace(pattern, insert_text)
        print(f"Added BI translations for {lang_code}")
    else:
        print(f"Pattern not found for {lang_code}")

# Write back
with open('C:/Users/sdads/WHDASH/translations.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done! BI translations added to all 8 languages.")