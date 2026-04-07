"""
Unified Settings Reader API
==========================
This module provides a single API that all modules should use to read settings.
It replaces scattered hardcoded values throughout the codebase.

USAGE:
    from unified_settings import get_app_setting, get_module_setting
    
    # Get a global setting
    currency = get_app_setting('default_currency', 'AED')
    
    # Get a module-specific setting with fallback
    low_stock_threshold = get_module_setting('wms', 'low_stock_threshold_percent', 20)
    
    # Get setting with scoping
    company_discount = get_app_setting('max_discount_percent', scope_type='COMPANY', scope_id=1)

All modules should import from here instead of hardcoding values or creating their own settings tables.
"""

from typing import Any, Optional, Dict
from database import get_db_context, get_one, get_all

# ============================================================================
# UNIFIED SETTINGS READER
# ============================================================================

def get_app_setting(key: str, default: Any = None, 
                   scope_type: str = 'GLOBAL', 
                   scope_id: int = None,
                   category: str = None) -> Any:
    """
    Get an application setting with proper scoping and fallback.
    
    This is the PRIMARY interface for reading settings across ALL modules.
    
    Args:
        key: Setting key (e.g., 'default_currency', 'max_discount_percent')
        default: Default value if not found
        scope_type: GLOBAL, COMPANY, BRANCH, WAREHOUSE, ROLE, or USER
        scope_id: ID of the scope entity (company_id, branch_id, etc.)
        category: Optional category to filter by
    
    Returns:
        The setting value or the default
    """
    # Try scope-specific first if not global
    if scope_type != 'GLOBAL' and scope_id:
        result = _get_setting_from_db(key, scope_type, scope_id)
        if result is not None:
            return _convert_value(result)
    
    # Fall back to company-level if scope was branch/warehouse
    if scope_type in ('BRANCH', 'WAREHOUSE') and scope_id:
        # Try to get parent company_id
        company_id = _get_parent_company_id(scope_type, scope_id)
        if company_id:
            result = _get_setting_from_db(key, 'COMPANY', company_id)
            if result is not None:
                return _convert_value(result)
    
    # Fall back to global
    result = _get_setting_from_db(key, 'GLOBAL', None)
    if result is not None:
        return _convert_value(result)
    
    return default


def _get_setting_from_db(key: str, scope_type: str, scope_id: int) -> Optional[str]:
    """Query the database for a setting value."""
    if scope_type == 'GLOBAL':
        row = get_one("""
            SELECT setting_value FROM admin_settings 
            WHERE setting_key = ? AND scope_type = 'GLOBAL' AND is_active = 1
        """, (key,))
    else:
        row = get_one("""
            SELECT setting_value FROM admin_settings 
            WHERE setting_key = ? AND scope_type = ? AND scope_id = ? AND is_active = 1
        """, (key, scope_type.upper(), scope_id))
    
    return row['setting_value'] if row else None


def _convert_value(value: str) -> Any:
    """Convert string setting value to appropriate Python type."""
    if value is None:
        return None
    
    # Boolean
    if value in ('1', 'true', 'True', 'yes', 'Yes', 'on'):
        return True
    if value in ('0', 'false', 'False', 'no', 'No', 'off'):
        return False
    
    # Integer
    try:
        if '.' not in value and value.replace('-', '').isdigit():
            return int(value)
    except (ValueError, AttributeError):
        pass
    
    # Float
    try:
        return float(value)
    except (ValueError, TypeError):
        pass
    
    return value


def _get_parent_company_id(scope_type: str, scope_id: int) -> Optional[int]:
    """Get the parent company ID for a branch or warehouse."""
    if scope_type == 'BRANCH':
        row = get_one("SELECT company_id FROM branches WHERE id = ?", (scope_id,))
        return row['company_id'] if row else None
    elif scope_type == 'WAREHOUSE':
        row = get_one("SELECT company_id FROM warehouses WHERE id = ?", (scope_id,))
        return row['company_id'] if row else None
    return None


# ============================================================================
# MODULE-SPECIFIC SETTING GETTERS
# ============================================================================

def get_module_setting(module: str, key: str, default: Any = None,
                      scope_type: str = 'GLOBAL',
                      scope_id: int = None) -> Any:
    """
    Get a setting for a specific module with fallback to global default.
    
    Args:
        module: Module name (SALES, CRM, WMS, HR, etc.)
        key: Setting key (without module prefix)
        default: Default value
        scope_type: Scope type
        scope_id: Scope ID
    
    Returns:
        The setting value or default
    """
    # Try the full key first (e.g., 'wms_low_stock_threshold_percent')
    full_key = f"{module.lower()}_{key}"
    result = get_app_setting(full_key, default, scope_type, scope_id)
    
    # If not found and key doesn't have module prefix, try without prefix
    if result == default and not key.startswith(module.lower() + '_'):
        result = get_app_setting(key, default, scope_type, scope_id)
    
    return result


# ============================================================================
# SALES SETTINGS
# ============================================================================

def get_sales_setting(key: str, default: Any = None, **kwargs) -> Any:
    """Get a sales module setting."""
    return get_module_setting('SALES', key, default, **kwargs)


def get_sales_currency(scope_type: str = 'GLOBAL', scope_id: int = None) -> str:
    """Get the default sales currency."""
    return get_sales_setting('currency', 'AED', scope_type, scope_id)


def get_sales_tax_rate(scope_type: str = 'GLOBAL', scope_id: int = None) -> float:
    """Get the default sales tax rate."""
    return get_sales_setting('tax_rate', 5.0, scope_type, scope_id)


def get_max_discount_percent(scope_type: str = 'GLOBAL', scope_id: int = None) -> float:
    """Get the maximum allowed discount percentage."""
    return get_sales_setting('discount_percent', 20.0, scope_type, scope_id)


def get_quotation_validity_days(scope_type: str = 'GLOBAL', scope_id: int = None) -> int:
    """Get quotation validity period in days."""
    return get_sales_setting('validity_days', 30, scope_type, scope_id)


# ============================================================================
# CRM SETTINGS
# ============================================================================

def get_crm_setting(key: str, default: Any = None, **kwargs) -> Any:
    """Get a CRM module setting."""
    return get_module_setting('CRM', key, default, **kwargs)


def get_lead_followup_days(scope_type: str = 'GLOBAL', scope_id: int = None) -> int:
    """Get lead follow-up reminder days."""
    return get_crm_setting('followup_days', 7, scope_type, scope_id)


def get_credit_limit_default(scope_type: str = 'GLOBAL', scope_id: int = None) -> float:
    """Get default customer credit limit."""
    return get_crm_setting('credit_limit_default', 10000, scope_type, scope_id)


# ============================================================================
# WMS SETTINGS
# ============================================================================

def get_wms_setting(key: str, default: Any = None, **kwargs) -> Any:
    """Get a WMS/inventory module setting."""
    return get_module_setting('WMS', key, default, **kwargs)


def get_inventory_method(scope_type: str = 'GLOBAL', scope_id: int = None) -> str:
    """Get inventory valuation method (FIFO, LIFO, etc.)."""
    return get_wms_setting('inventory_method', 'FIFO', scope_type, scope_id)


def get_low_stock_threshold_percent(scope_type: str = 'GLOBAL', scope_id: int = None) -> int:
    """Get low stock alert threshold percentage."""
    return get_wms_setting('low_stock_threshold_percent', 20, scope_type, scope_id)


def get_reorder_threshold_percent(scope_type: str = 'GLOBAL', scope_id: int = None) -> int:
    """Get reorder threshold percentage."""
    return get_wms_setting('reorder_threshold_percent', 30, scope_type, scope_id)


def get_reservation_expiry_hours(scope_type: str = 'GLOBAL', scope_id: int = None) -> int:
    """Get stock reservation expiry in hours."""
    return get_wms_setting('reservation_expiry_hours', 48, scope_type, scope_id)


# ============================================================================
# LOGISTICS SETTINGS
# ============================================================================

def get_logistics_setting(key: str, default: Any = None, **kwargs) -> Any:
    """Get a logistics module setting."""
    return get_module_setting('LOGISTICS', key, default, **kwargs)


def get_delivery_window_hours(scope_type: str = 'GLOBAL', scope_id: int = None) -> int:
    """Get default delivery window in hours."""
    return get_logistics_setting('delivery_window_hours', 4, scope_type, scope_id)


def get_delivery_sla_hours(scope_type: str = 'GLOBAL', scope_id: int = None) -> int:
    """Get delivery SLA in hours."""
    return get_logistics_setting('sla_delivery_hours', 72, scope_type, scope_id)


# ============================================================================
# HR SETTINGS
# ============================================================================

def get_hr_setting(key: str, default: Any = None, **kwargs) -> Any:
    """Get an HR module setting."""
    return get_module_setting('HR', key, default, **kwargs)


def get_probation_months(scope_type: str = 'GLOBAL', scope_id: int = None) -> int:
    """Get default probation period in months."""
    return get_hr_setting('probation_months', 3, scope_type, scope_id)


def get_annual_leave_days(scope_type: str = 'GLOBAL', scope_id: int = None) -> int:
    """Get default annual leave days."""
    return get_hr_setting('annual_leave_days', 21, scope_type, scope_id)


def get_overtime_rate_weekday(scope_type: str = 'GLOBAL', scope_id: int = None) -> float:
    """Get weekday overtime rate multiplier."""
    return get_hr_setting('overtime_rate_weekday', 1.5, scope_type, scope_id)


# ============================================================================
# PLANNING SETTINGS
# ============================================================================

def get_planning_setting(key: str, default: Any = None, **kwargs) -> Any:
    """Get a planning module setting."""
    return get_module_setting('PLANNING', key, default, **kwargs)


def get_forecast_method(scope_type: str = 'GLOBAL', scope_id: int = None) -> str:
    """Get default forecast method."""
    return get_planning_setting('forecast_method', 'MOVING_AVERAGE', scope_type, scope_id)


def get_forecast_horizon_days(scope_type: str = 'GLOBAL', scope_id: int = None) -> int:
    """Get forecast horizon in days."""
    return get_planning_setting('forecast_horizon_days', 30, scope_type, scope_id)


def get_service_level_target(scope_type: str = 'GLOBAL', scope_id: int = None) -> int:
    """Get service level target percentage."""
    return get_planning_setting('service_level_target', 95, scope_type, scope_id)


# ============================================================================
# MARKETING SETTINGS
# ============================================================================

def get_marketing_setting(key: str, default: Any = None, **kwargs) -> Any:
    """Get a marketing module setting."""
    return get_module_setting('MARKETING', key, default, **kwargs)


def get_campaign_budget_default(scope_type: str = 'GLOBAL', scope_id: int = None) -> float:
    """Get default campaign budget."""
    return get_marketing_setting('campaign_budget_default', 1000, scope_type, scope_id)


def get_budget_alert_threshold(scope_type: str = 'GLOBAL', scope_id: int = None) -> int:
    """Get budget alert threshold percentage."""
    return get_marketing_setting('budget_alert_threshold', 80, scope_type, scope_id)


# ============================================================================
# GENERAL/PLATFORM SETTINGS
# ============================================================================

def get_platform_setting(key: str, default: Any = None, **kwargs) -> Any:
    """Get a general platform setting."""
    return get_app_setting(key, default, **kwargs)


def get_default_language() -> str:
    """Get the default system language."""
    return get_app_setting('default_language', 'en')


def get_default_currency() -> str:
    """Get the default currency code."""
    return get_app_setting('default_currency', 'AED')


def get_default_theme() -> str:
    """Get the default UI theme."""
    return get_app_setting('default_theme', 'dark')


def get_session_timeout() -> int:
    """Get session timeout in minutes."""
    return get_app_setting('session_timeout_minutes', 120)


def get_items_per_page() -> int:
    """Get default pagination size."""
    return get_app_setting('items_per_page', 50)


# ============================================================================
# BULK SETTINGS RETRIEVAL
# ============================================================================

def get_all_settings_for_module(module: str, scope_type: str = 'GLOBAL', 
                               scope_id: int = None) -> Dict[str, Any]:
    """
    Get all settings for a module as a dictionary.
    
    Useful for passing to templates or for module initialization.
    """
    # Get all settings that start with module prefix
    prefix = f"{module.lower()}_"
    
    settings = {}
    rows = get_all("""
        SELECT setting_key, setting_value FROM admin_settings 
        WHERE (setting_key LIKE ? OR setting_key LIKE ?)
        AND is_active = 1
        ORDER BY setting_key
    """, (f'{prefix}%', module.upper()))
    
    for row in rows:
        settings[row['setting_key']] = _convert_value(row['setting_value'])
    
    return settings


# ============================================================================
# SETTING EXISTS CHECK
# ============================================================================

def setting_exists(key: str, scope_type: str = 'GLOBAL', scope_id: int = None) -> bool:
    """Check if a setting exists in the database."""
    if scope_type == 'GLOBAL':
        row = get_one("""
            SELECT 1 FROM admin_settings 
            WHERE setting_key = ? AND scope_type = 'GLOBAL' AND is_active = 1
        """, (key,))
    else:
        row = get_one("""
            SELECT 1 FROM admin_settings 
            WHERE setting_key = ? AND scope_type = ? AND scope_id = ? AND is_active = 1
        """, (key, scope_type.upper(), scope_id))
    
    return row is not None
