"""
Theme Engine - Jinja2 Template Helpers
=====================================
Provides helper functions for generating theme-aware HTML attributes,
CSS classes, and JavaScript theme switching code.

This module is imported by Flask app.py and exposed to templates
via the inject_globals context processor.

USAGE:
    In templates, use the theme_ attributes provided:
    {{ theme_attr('background', 'surface') }}
    {{ theme_class('card', 'glass-panel') }}
"""

from theme_system import (
    get_theme_config, get_theme_tokens,
    get_chart_palette, is_dark_theme,
    AVAILABLE_THEMES, THEME_TOKENS,
    THEME_TOKEN_CATEGORIES,
    get_available_themes
)


def theme_css_variables(theme_id: str) -> str:
    """
    Generate CSS custom property declarations for a theme.
    Returns a string like: --theme-bg: #0f172a; --theme-surface: #1e293b; ...
    """
    tokens = get_theme_tokens(theme_id)
    return '; '.join(f'{k}: {v}' for k, v in tokens.items())


def theme_inline_style(theme_id: str) -> str:
    """
    Generate a complete <style> block with CSS variables for a theme.
    """
    vars = theme_css_variables(theme_id)
    return f'<style>:root {{{vars}}}</style>'


def theme_data_attrs(theme_id: str) -> str:
    """
    Generate data attributes for theme application.
    Returns: data-theme="dark" data-theme-is-dark="true"
    """
    is_dark = 'true' if is_dark_theme(theme_id) else 'false'
    return f'data-theme="{theme_id}" data-theme-dark="{is_dark}"'


def chartjs_config(theme_id: str) -> dict:
    """
    Generate Chart.js configuration object for the current theme.
    Used to make charts theme-aware.
    """
    palette = get_chart_palette(theme_id)
    tokens = get_theme_tokens(theme_id)

    return {
        'palette': palette,
        'options': {
            'color': tokens.get('--theme-text-secondary', '#94a3b8'),
            'borderColor': tokens.get('--theme-border', 'rgba(255,255,255,0.08)'),
            'backgroundColor': tokens.get('--theme-surface', '#1e293b'),
        }
    }


def theme_preview_data() -> list:
    """
    Generate theme preview card data for the theme selector UI.
    """
    return [
        {
            'id': theme['id'],
            'name': theme['name'],
            'label': theme['label'],
            'description': theme['description'],
            'is_dark': theme['is_dark'],
            'preview': theme.get('preview', {}),
        }
        for theme in AVAILABLE_THEMES.values()
    ]


def get_status_color_classes(status: str) -> tuple:
    """
    Get Tailwind-compatible color classes for a status value.
    Returns (bg_class, text_class, border_class).
    """
    status_colors = {
        'Draft': ('bg-gray-500/20', 'text-gray-200', 'border-gray-500/30'),
        'Open': ('bg-blue-500/20', 'text-blue-200', 'border-blue-500/30'),
        'Active': ('bg-emerald-500/20', 'text-emerald-200', 'border-emerald-500/30'),
        'Pending': ('bg-yellow-500/20', 'text-yellow-200', 'border-yellow-500/30'),
        'In Progress': ('bg-blue-500/20', 'text-blue-200', 'border-blue-500/30'),
        'Review': ('bg-purple-500/20', 'text-purple-200', 'border-purple-500/30'),
        'Approved': ('bg-emerald-500/20', 'text-emerald-200', 'border-emerald-500/30'),
        'Completed': ('bg-emerald-500/20', 'text-emerald-200', 'border-emerald-500/30'),
        'Rejected': ('bg-red-500/20', 'text-red-200', 'border-red-500/30'),
        'Canceled': ('bg-gray-500/20', 'text-gray-200', 'border-gray-500/30'),
        'Inactive': ('bg-gray-500/20', 'text-gray-200', 'border-gray-500/30'),
        'Archived': ('bg-gray-500/20', 'text-gray-200', 'border-gray-500/30'),
        'Low': ('bg-gray-500/20', 'text-gray-200', 'border-gray-500/30'),
        'Medium': ('bg-yellow-500/20', 'text-yellow-200', 'border-yellow-500/30'),
        'High': ('bg-orange-500/20', 'text-orange-200', 'border-orange-500/30'),
        'Critical': ('bg-red-500/20', 'text-red-200', 'border-red-500/30'),
        'Delivered': ('bg-emerald-500/20', 'text-emerald-200', 'border-emerald-500/30'),
        'In Transit': ('bg-blue-500/20', 'text-blue-200', 'border-blue-500/30'),
        'Failed': ('bg-red-500/20', 'text-red-200', 'border-red-500/30'),
        'Returned': ('bg-yellow-500/20', 'text-yellow-200', 'border-yellow-500/30'),
        'Overdue': ('bg-red-500/20', 'text-red-200', 'border-red-500/30'),
        'Paid': ('bg-emerald-500/20', 'text-emerald-200', 'border-emerald-500/30'),
        'Sent': ('bg-blue-500/20', 'text-blue-200', 'border-blue-500/30'),
        'Locked': ('bg-gray-500/20', 'text-gray-200', 'border-gray-500/30'),
        'Present': ('bg-emerald-500/20', 'text-emerald-200', 'border-emerald-500/30'),
        'Absent': ('bg-red-500/20', 'text-red-200', 'border-red-500/30'),
        'Late': ('bg-yellow-500/20', 'text-yellow-200', 'border-yellow-500/30'),
        'On Leave': ('bg-blue-500/20', 'text-blue-200', 'border-blue-500/30'),
        'Holiday': ('bg-purple-500/20', 'text-purple-200', 'border-purple-500/30'),
    }
    return status_colors.get(status, ('bg-gray-500/20', 'text-gray-200', 'border-gray-500/30'))


def get_priority_classes(priority: str) -> tuple:
    """
    Get Tailwind-compatible color classes for a priority value.
    Returns (bg_class, text_class, border_class).
    """
    priority_colors = {
        'Low': ('bg-gray-500/20', 'text-gray-300', 'border-gray-500/30'),
        'Medium': ('bg-yellow-500/20', 'text-yellow-300', 'border-yellow-500/30'),
        'High': ('bg-orange-500/20', 'text-orange-300', 'border-orange-500/30'),
        'Critical': ('bg-red-500/20', 'text-red-300', 'border-red-500/30'),
    }
    return priority_colors.get(priority, ('bg-gray-500/20', 'text-gray-300', 'border-gray-500/30'))
