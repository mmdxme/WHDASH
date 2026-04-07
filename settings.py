"""
Unified Settings Management System
================================
Centralized settings management for the entire WHDASH platform.

This module provides:
- Single settings table for all platform settings
- Categories for organizing settings
- Validation and type conversion
- Settings groups for module-specific configs
- Migration helpers for legacy settings tables

USAGE:
    from settings import (
        get_setting, set_setting,
        get_settings_by_category,
        initialize_settings,
        SETTINGS_CATEGORIES
    )
"""

from typing import Any, Optional, Dict, List
from database import get_db_context, get_one, get_all

# ============================================================================
# SETTINGS CATEGORIES
# ============================================================================

SETTINGS_CATEGORIES = {
    'GENERAL': {
        'label': 'General',
        'description': 'Basic platform configuration',
        'order': 1,
    },
    'COMPANY': {
        'label': 'Company',
        'description': 'Company information and branding',
        'order': 2,
    },
    'LOCALIZATION': {
        'label': 'Localization',
        'description': 'Language, timezone, date format settings',
        'order': 3,
    },
    'SECURITY': {
        'label': 'Security',
        'description': 'Authentication and security settings',
        'order': 4,
    },
    'NOTIFICATIONS': {
        'label': 'Notifications',
        'description': 'Email, SMS, and in-app notification settings',
        'order': 5,
    },
    'INTEGRATIONS': {
        'label': 'Integrations',
        'description': 'Third-party integrations',
        'order': 6,
    },
    'UI': {
        'label': 'User Interface',
        'description': 'Theme, layout, and display settings',
        'order': 7,
    },
    'HR': {
        'label': 'HR Settings',
        'description': 'Human Resources module configuration',
        'order': 10,
    },
    'WMS': {
        'label': 'Warehouse Settings',
        'description': 'WMS and inventory configuration',
        'order': 11,
    },
    'LOGISTICS': {
        'label': 'Logistics Settings',
        'description': 'Delivery and transport configuration',
        'order': 12,
    },
    'PLANNING': {
        'label': 'Planning Settings',
        'description': 'Forecasting and replenishment settings',
        'order': 13,
    },
    'CRM': {
        'label': 'CRM Settings',
        'description': 'Customer relationship settings',
        'order': 14,
    },
    'MARKETING': {
        'label': 'Marketing Settings',
        'description': 'Marketing and campaign configuration',
        'order': 15,
    },
}

# Default settings with their metadata
DEFAULT_SETTINGS = {
    # General
    'platform_name': {'value': 'MMDx', 'type': 'string', 'category': 'GENERAL', 'description': 'Platform display name'},
    'platform_version': {'value': '2.0', 'type': 'string', 'category': 'GENERAL', 'description': 'Current platform version'},
    
    # Company
    'company_name': {'value': 'Warehouse Dashboard', 'type': 'string', 'category': 'COMPANY', 'description': 'Primary company name'},
    'company_address': {'value': '', 'type': 'string', 'category': 'COMPANY', 'description': 'Company address'},
    'company_phone': {'value': '', 'type': 'string', 'category': 'COMPANY', 'description': 'Company phone number'},
    'company_email': {'value': '', 'type': 'string', 'category': 'COMPANY', 'description': 'Company email'},
    'company_website': {'value': '', 'type': 'string', 'category': 'COMPANY', 'description': 'Company website'},
    'company_logo_url': {'value': '', 'type': 'string', 'category': 'COMPANY', 'description': 'Company logo URL'},
    
    # Localization
    'default_language': {'value': 'en', 'type': 'string', 'category': 'LOCALIZATION', 'description': 'Default system language'},
    'available_languages': {'value': 'en,ar,fa', 'type': 'string', 'category': 'LOCALIZATION', 'description': 'Available languages (comma-separated)'},
    'default_timezone': {'value': 'Asia/Dubai', 'type': 'string', 'category': 'LOCALIZATION', 'description': 'Default timezone'},
    'date_format': {'value': 'DD/MM/YYYY', 'type': 'string', 'category': 'LOCALIZATION', 'description': 'Date format'},
    'time_format': {'value': '24h', 'type': 'string', 'category': 'LOCALIZATION', 'description': 'Time format (12h or 24h)'},
    'default_currency': {'value': 'AED', 'type': 'string', 'category': 'LOCALIZATION', 'description': 'Default currency code'},
    'currency_symbol': {'value': 'AED', 'type': 'string', 'category': 'LOCALIZATION', 'description': 'Currency symbol'},
    'enable_rtl': {'value': '1', 'type': 'boolean', 'category': 'LOCALIZATION', 'description': 'Enable RTL language support'},
    
    # Security
    'session_timeout_minutes': {'value': '120', 'type': 'integer', 'category': 'SECURITY', 'description': 'Session timeout in minutes'},
    'max_login_attempts': {'value': '5', 'type': 'integer', 'category': 'SECURITY', 'description': 'Maximum failed login attempts before lockout'},
    'password_min_length': {'value': '8', 'type': 'integer', 'category': 'SECURITY', 'description': 'Minimum password length'},
    'require_special_char_password': {'value': '1', 'type': 'boolean', 'category': 'SECURITY', 'description': 'Require special characters in password'},
    'require_email_verification': {'value': '0', 'type': 'boolean', 'category': 'SECURITY', 'description': 'Require email verification on signup'},
    'enable_2fa': {'value': '0', 'type': 'boolean', 'category': 'SECURITY', 'description': 'Enable two-factor authentication'},
    'allowed_file_extensions': {'value': 'png,jpg,jpeg,gif,pdf,doc,docx,xls,xlsx', 'type': 'string', 'category': 'SECURITY', 'description': 'Allowed file upload extensions'},
    'max_file_size_mb': {'value': '10', 'type': 'integer', 'category': 'SECURITY', 'description': 'Maximum file upload size in MB'},
    
    # Notifications
    'email_notifications_enabled': {'value': '1', 'type': 'boolean', 'category': 'NOTIFICATIONS', 'description': 'Enable email notifications'},
    'smtp_host': {'value': '', 'type': 'string', 'category': 'NOTIFICATIONS', 'description': 'SMTP server host'},
    'smtp_port': {'value': '587', 'type': 'integer', 'category': 'NOTIFICATIONS', 'description': 'SMTP server port'},
    'smtp_user': {'value': '', 'type': 'string', 'category': 'NOTIFICATIONS', 'description': 'SMTP username'},
    'smtp_password': {'value': '', 'type': 'password', 'category': 'NOTIFICATIONS', 'description': 'SMTP password'},
    'smtp_from_email': {'value': '', 'type': 'string', 'category': 'NOTIFICATIONS', 'description': 'From email address'},
    'smtp_from_name': {'value': 'MMDx', 'type': 'string', 'category': 'NOTIFICATIONS', 'description': 'From name for emails'},
    'enable_sms_notifications': {'value': '0', 'type': 'boolean', 'category': 'NOTIFICATIONS', 'description': 'Enable SMS notifications'},
    'in_app_notification_limit': {'value': '50', 'type': 'integer', 'category': 'NOTIFICATIONS', 'description': 'Max notifications to show'},
    
    # Integrations
    'peyvast_api_url': {'value': '', 'type': 'string', 'category': 'INTEGRATIONS', 'description': 'Peyvast API URL'},
    'peyvast_api_key': {'value': '', 'type': 'password', 'category': 'INTEGRATIONS', 'description': 'Peyvast API key'},
    'google_client_id': {'value': '', 'type': 'string', 'category': 'INTEGRATIONS', 'description': 'Google OAuth client ID'},
    'google_client_secret': {'value': '', 'type': 'password', 'category': 'INTEGRATIONS', 'description': 'Google OAuth client secret'},
    
    # UI
    'default_theme': {'value': 'dark', 'type': 'string', 'category': 'UI', 'description': 'Default UI theme'},
    'items_per_page': {'value': '50', 'type': 'integer', 'category': 'UI', 'description': 'Default pagination size'},
    'show_welcome_tour': {'value': '1', 'type': 'boolean', 'category': 'UI', 'description': 'Show welcome tour for new users'},
    'compact_sidebar': {'value': '0', 'type': 'boolean', 'category': 'UI', 'description': 'Use compact sidebar'},
    'default_font_size': {'value': 'medium', 'type': 'string', 'category': 'UI', 'description': 'Default font size'},
    
    # HR Defaults
    'hr_default_probation_months': {'value': '3', 'type': 'integer', 'category': 'HR', 'description': 'Default probation period in months'},
    'hr_default_annual_leave_days': {'value': '21', 'type': 'integer', 'category': 'HR', 'description': 'Default annual leave days'},
    'hr_work_week_days': {'value': '5', 'type': 'integer', 'category': 'HR', 'description': 'Working days per week'},
    'hr_overtime_rate_weekday': {'value': '1.5', 'type': 'float', 'category': 'HR', 'description': 'Overtime multiplier for weekdays'},
    'hr_overtime_rate_weekend': {'value': '2.0', 'type': 'float', 'category': 'HR', 'description': 'Overtime multiplier for weekends'},
    'hr_overtime_rate_holiday': {'value': '2.5', 'type': 'float', 'category': 'HR', 'description': 'Overtime multiplier for holidays'},
    
    # WMS Defaults
    'wms_default_warehouse_id': {'value': '', 'type': 'integer', 'category': 'WMS', 'description': 'Default warehouse ID'},
    'wms_enable_serial_tracking': {'value': '1', 'type': 'boolean', 'category': 'WMS', 'description': 'Enable serial number tracking'},
    'wms_enable_batch_tracking': {'value': '1', 'type': 'boolean', 'category': 'WMS', 'description': 'Enable batch tracking'},
    'wms_auto_assign_location': {'value': '1', 'type': 'boolean', 'category': 'WMS', 'description': 'Auto-assign storage location'},
    'wms_low_stock_threshold_percent': {'value': '20', 'type': 'integer', 'category': 'WMS', 'description': 'Low stock alert threshold %'},
    'wms_auto_receive': {'value': '0', 'type': 'boolean', 'category': 'WMS', 'description': 'Enable automatic receiving'},
    
    # Logistics Defaults
    'logistics_default_vehicle_id': {'value': '', 'type': 'integer', 'category': 'LOGISTICS', 'description': 'Default vehicle ID'},
    'logistics_enable_gps_tracking': {'value': '1', 'type': 'boolean', 'category': 'LOGISTICS', 'description': 'Enable GPS tracking'},
    'logistics_default_delivery_window_hours': {'value': '4', 'type': 'integer', 'category': 'LOGISTICS', 'description': 'Default delivery time window in hours'},
    
    # Planning Defaults
    'planning_default_forecast_method': {'value': 'MOVING_AVERAGE', 'type': 'string', 'category': 'PLANNING', 'description': 'Default forecast method'},
    'planning_forecast_horizon_days': {'value': '30', 'type': 'integer', 'category': 'PLANNING', 'description': 'Forecast horizon in days'},
    'planning_demand_history_months': {'value': '12', 'type': 'integer', 'category': 'PLANNING', 'description': 'Demand history months for forecasting'},
    'planning_enable_auto_replenishment': {'value': '0', 'type': 'boolean', 'category': 'PLANNING', 'description': 'Enable automatic replenishment'},
    
    # CRM Defaults
    'crm_lead_followup_days': {'value': '7', 'type': 'integer', 'category': 'CRM', 'description': 'Default lead follow-up reminder days'},
    'crm_enable_auto_assignment': {'value': '0', 'type': 'boolean', 'category': 'CRM', 'description': 'Enable automatic lead assignment'},
    
    # Marketing Defaults
    'marketing_default_campaign_budget': {'value': '1000', 'type': 'float', 'category': 'MARKETING', 'description': 'Default campaign budget'},
    'marketing_enable_attribution': {'value': '1', 'type': 'boolean', 'category': 'MARKETING', 'description': 'Enable marketing attribution tracking'},
}


# ============================================================================
# SETTINGS GET/SET FUNCTIONS
# ============================================================================

def get_setting(key: str, default: Any = None, use_cache: bool = True) -> Any:
    """
    Get a setting value with type conversion.
    
    Args:
        key: Setting key
        default: Default value if not found
        use_cache: Whether to use cached values
    
    Returns:
        The setting value, converted to the appropriate type
    """
    # Check if key has metadata for type
    setting_meta = DEFAULT_SETTINGS.get(key, {})
    value_type = setting_meta.get('type', 'string')
    
    result = get_one(
        "SELECT setting_value FROM platform_settings WHERE setting_key = ? AND is_active = 1",
        (key,)
    )
    
    if result is None:
        return default
    
    value = result['setting_value']
    
    # Convert to appropriate type
    if value is None:
        return default
    
    if value_type == 'boolean':
        return value in ('1', 'true', 'True', 'yes', 'Yes')
    elif value_type == 'integer':
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    elif value_type == 'float':
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    else:
        return value


def set_setting(key: str, value: Any, category: str = 'GENERAL', 
                description: str = None, setting_type: str = 'string') -> bool:
    """
    Set a setting value.
    
    Args:
        key: Setting key
        value: Setting value (will be converted to string)
        category: Settings category
        description: Optional description
        setting_type: Type hint for the setting
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with get_db_context() as db:
            # Check if exists
            existing = db.execute(
                "SELECT id FROM platform_settings WHERE setting_key = ?",
                (key,)
            ).fetchone()
            
            str_value = str(value) if value is not None else ''
            
            if existing:
                db.execute("""
                    UPDATE platform_settings 
                    SET setting_value = ?, category = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE setting_key = ?
                """, (str_value, category, description, key))
            else:
                db.execute("""
                    INSERT INTO platform_settings (setting_key, setting_value, category, description)
                    VALUES (?, ?, ?, ?)
                """, (key, str_value, category, description))
            
            db.commit()
            return True
    except Exception:
        return False


def delete_setting(key: str) -> bool:
    """Delete a setting (soft delete by deactivating)."""
    try:
        with get_db_context() as db:
            db.execute(
                "UPDATE platform_settings SET is_active = 0 WHERE setting_key = ?",
                (key,)
            )
            db.commit()
            return True
    except Exception:
        return False


def get_settings_by_category(category: str) -> Dict[str, Any]:
    """
    Get all settings in a category.
    
    Args:
        category: Category name
    
    Returns:
        Dictionary of {key: value}
    """
    rows = get_all(
        "SELECT setting_key, setting_value FROM platform_settings WHERE category = ? AND is_active = 1",
        (category,)
    )
    return {row['setting_key']: row['setting_value'] for row in rows}


def get_all_settings() -> Dict[str, Dict[str, Any]]:
    """
    Get all settings with their metadata.
    
    Returns:
        Dictionary of {key: {'value': ..., 'category': ..., 'description': ...}}
    """
    settings = {}
    rows = get_all("SELECT * FROM platform_settings WHERE is_active = 1")
    
    for row in rows:
        key = row['setting_key']
        meta = DEFAULT_SETTINGS.get(key, {})
        settings[key] = {
            'value': row['setting_value'],
            'category': row['category'],
            'description': row['description'] or meta.get('description', ''),
            'type': meta.get('type', 'string'),
        }
    
    return settings


def reset_setting_to_default(key: str) -> bool:
    """Reset a setting to its default value from DEFAULT_SETTINGS."""
    if key in DEFAULT_SETTINGS:
        meta = DEFAULT_SETTINGS[key]
        return set_setting(key, meta['value'], meta['category'], meta['description'], meta['type'])
    return False


def reset_all_settings() -> bool:
    """Reset all settings to defaults."""
    try:
        for key, meta in DEFAULT_SETTINGS.items():
            set_setting(key, meta['value'], meta['category'], meta['description'], meta['type'])
        return True
    except Exception:
        return False


# ============================================================================
# BULK SETTINGS OPERATIONS
# ============================================================================

def import_settings(settings_dict: Dict[str, Any]) -> Dict[str, bool]:
    """
    Import multiple settings at once.
    
    Args:
        settings_dict: Dictionary of {key: value}
    
    Returns:
        Dictionary of {key: success}
    """
    results = {}
    for key, value in settings_dict.items():
        results[key] = set_setting(key, value)
    return results


def export_settings(keys: List[str] = None) -> Dict[str, Any]:
    """
    Export settings values.
    
    Args:
        keys: List of keys to export (None = all)
    
    Returns:
        Dictionary of {key: value}
    """
    if keys:
        placeholders = ','.join(['?' for _ in keys])
        sql = f"SELECT setting_key, setting_value FROM platform_settings WHERE setting_key IN ({placeholders}) AND is_active = 1"
        rows = get_all(sql, keys)
    else:
        rows = get_all("SELECT setting_key, setting_value FROM platform_settings WHERE is_active = 1")
    
    return {row['setting_key']: row['setting_value'] for row in rows}


# ============================================================================
# VALIDATION
# ============================================================================

def validate_setting_value(key: str, value: Any) -> tuple:
    """
    Validate a setting value against its type.
    
    Args:
        key: Setting key
        value: Value to validate
    
    Returns:
        (is_valid: bool, error_message: str)
    """
    if key not in DEFAULT_SETTINGS:
        return True, None  # Unknown settings are valid
    
    meta = DEFAULT_SETTINGS[key]
    value_type = meta.get('type', 'string')
    
    if value is None:
        return False, "Value cannot be None"
    
    if value_type == 'boolean':
        if value not in (0, 1, '0', '1', True, False, 'true', 'false', 'yes', 'no'):
            return False, "Value must be a boolean (0/1, true/false, yes/no)"
    
    elif value_type == 'integer':
        try:
            int(value)
        except (ValueError, TypeError):
            return False, "Value must be an integer"
    
    elif value_type == 'float':
        try:
            float(value)
        except (ValueError, TypeError):
            return False, "Value must be a number"
    
    elif value_type == 'password':
        if len(str(value)) < 0:
            return False, "Password cannot be empty"
    
    return True, None


# ============================================================================
# SETTINGS GROUPS (for UI organization)
# ============================================================================

SETTINGS_GROUPS = {
    'platform_info': {
        'label': 'Platform Information',
        'icon': 'fa-info-circle',
        'settings': ['platform_name', 'platform_version']
    },
    'company_info': {
        'label': 'Company Information',
        'icon': 'fa-building',
        'settings': ['company_name', 'company_address', 'company_phone', 'company_email', 'company_website', 'company_logo_url']
    },
    'localization': {
        'label': 'Language & Region',
        'icon': 'fa-globe',
        'settings': ['default_language', 'available_languages', 'default_timezone', 'date_format', 'time_format', 'default_currency', 'currency_symbol', 'enable_rtl']
    },
    'security': {
        'label': 'Security & Authentication',
        'icon': 'fa-shield-alt',
        'settings': ['session_timeout_minutes', 'max_login_attempts', 'password_min_length', 'require_special_char_password', 'require_email_verification', 'enable_2fa', 'allowed_file_extensions', 'max_file_size_mb']
    },
    'notifications': {
        'label': 'Email & Notifications',
        'icon': 'fa-envelope',
        'settings': ['email_notifications_enabled', 'smtp_host', 'smtp_port', 'smtp_user', 'smtp_password', 'smtp_from_email', 'smtp_from_name', 'enable_sms_notifications', 'in_app_notification_limit']
    },
    'integrations': {
        'label': 'Third-Party Integrations',
        'icon': 'fa-plug',
        'settings': ['peyvast_api_url', 'peyvast_api_key', 'google_client_id', 'google_client_secret']
    },
    'ui_preferences': {
        'label': 'User Interface',
        'icon': 'fa-desktop',
        'settings': ['default_theme', 'items_per_page', 'show_welcome_tour', 'compact_sidebar', 'default_font_size']
    },
}


def get_settings_group(group_key: str) -> Dict[str, Any]:
    """Get a settings group with its values."""
    if group_key not in SETTINGS_GROUPS:
        return None
    
    group = SETTINGS_GROUPS[group_key].copy()
    group['settings_data'] = []
    
    for key in group['settings']:
        meta = DEFAULT_SETTINGS.get(key, {})
        value = get_setting(key, meta.get('value'))
        group['settings_data'].append({
            'key': key,
            'value': value,
            'type': meta.get('type', 'string'),
            'category': meta.get('category', 'GENERAL'),
            'description': meta.get('description', ''),
        })
    
    return group


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_settings():
    """Initialize the settings system with default values."""
    # Ensure table exists
    from database import table_exists
    if not table_exists('platform_settings'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE platform_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT,
                    category TEXT DEFAULT 'GENERAL',
                    description TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.commit()
    
    # Seed default settings
    for key, meta in DEFAULT_SETTINGS.items():
        existing = get_setting(key, use_cache=False)
        if existing is None:
            set_setting(key, meta['value'], meta['category'], meta['description'], meta['type'])


# Initialize when module is imported
initialize_settings()
