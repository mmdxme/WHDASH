"""
Theme Management System
========================
Centralized theme configuration, tokens, and helpers for the WHDASH platform.

This module provides:
- Theme definitions with semantic design tokens
- Theme validation and defaults
- Chart color palettes per theme
- Helper functions for theme-aware rendering

USAGE:
    from theme_system import get_available_themes, get_theme_config, CHART_PALETTES
"""

from typing import Dict, Any, List, Optional

# =============================================================================
# THEME DEFINITIONS
# =============================================================================
# Each theme has semantic tokens mapped to CSS variables.
# The actual CSS variable application is in base.html via the theme CSS engine.

AVAILABLE_THEMES: Dict[str, Dict[str, Any]] = {
    # -------------------------------------------------------------------------
    # 1. Dark / Night Theme - Default dark dashboard feel
    # -------------------------------------------------------------------------
    'dark': {
        'id': 'dark',
        'name': 'Dark Night',
        'label': 'Dark Night',
        'description': 'Modern dark dashboard with deep slate surfaces',
        'category': 'dark',  # 'dark' or 'light' base tone
        'preview': {
            'primary': '#0ea5e9',
            'secondary': '#6366f1',
            'background': '#0f172a',
            'surface': '#1e293b',
            'accent': '#38bdf8',
        },
        'is_dark': True,
        'order': 1,
    },

    # -------------------------------------------------------------------------
    # 2. Light / Day Theme - Clean bright business look
    # -------------------------------------------------------------------------
    'light': {
        'id': 'light',
        'name': 'Light Day',
        'label': 'Light Day',
        'description': 'Bright and clean business dashboard',
        'category': 'light',
        'preview': {
            'primary': '#0ea5e9',
            'secondary': '#6366f1',
            'background': '#eff5fb',
            'surface': '#ffffff',
            'accent': '#0284c7',
        },
        'is_dark': False,
        'order': 2,
    },

    # -------------------------------------------------------------------------
    # 3. Blue Theme - Corporate trustworthy blue
    # -------------------------------------------------------------------------
    'blue': {
        'id': 'blue',
        'name': 'Ocean Blue',
        'label': 'Ocean Blue',
        'description': 'Professional corporate blue with trustworthy feel',
        'category': 'dark',  # Uses dark base with blue accent
        'preview': {
            'primary': '#3b82f6',
            'secondary': '#1d4ed8',
            'background': '#0c1929',
            'surface': '#1e3a5f',
            'accent': '#60a5fa',
        },
        'is_dark': True,
        'order': 3,
    },

    # -------------------------------------------------------------------------
    # 4. Green Theme - Calm reliable operations
    # -------------------------------------------------------------------------
    'green': {
        'id': 'green',
        'name': 'Forest Green',
        'label': 'Forest Green',
        'description': 'Calm and reliable green for operations dashboards',
        'category': 'dark',
        'preview': {
            'primary': '#22c55e',
            'secondary': '#16a34a',
            'background': '#0f1f0f',
            'surface': '#1a2e1a',
            'accent': '#4ade80',
        },
        'is_dark': True,
        'order': 4,
    },

    # -------------------------------------------------------------------------
    # 5. Orange Theme - Energetic professional
    # -------------------------------------------------------------------------
    'orange': {
        'id': 'orange',
        'name': 'Sunset Orange',
        'label': 'Sunset Orange',
        'description': 'Warm energetic orange for dynamic business dashboards',
        'category': 'dark',
        'preview': {
            'primary': '#f97316',
            'secondary': '#ea580c',
            'background': '#1f1410',
            'surface': '#2d1f15',
            'accent': '#fb923c',
        },
        'is_dark': True,
        'order': 5,
    },

    # -------------------------------------------------------------------------
    # 6. Purple / Graphite Theme - Premium professional
    # -------------------------------------------------------------------------
    'purple': {
        'id': 'purple',
        'name': 'Royal Purple',
        'label': 'Royal Purple',
        'description': 'Premium refined purple for executive dashboards',
        'category': 'dark',
        'preview': {
            'primary': '#a855f7',
            'secondary': '#9333ea',
            'background': '#13101a',
            'surface': '#1f1830',
            'accent': '#c084fc',
        },
        'is_dark': True,
        'order': 6,
    },

    # -------------------------------------------------------------------------
    # 7. Light / Day Theme - Clean bright business look (renamed from original)
    # -------------------------------------------------------------------------
    'day': {
        'id': 'day',
        'name': 'Bright Day',
        'label': 'Bright Day',
        'description': 'Clean and crisp daylight dashboard with sky blue accents',
        'category': 'light',
        'preview': {
            'primary': '#0ea5e9',
            'secondary': '#6366f1',
            'background': '#f0f9ff',
            'surface': '#ffffff',
            'accent': '#0284c7',
        },
        'is_dark': False,
        'order': 7,
    },

    # -------------------------------------------------------------------------
    # 8. Warm Light Theme - Cozy professional warmth
    # -------------------------------------------------------------------------
    'warm': {
        'id': 'warm',
        'name': 'Warm Light',
        'label': 'Warm Light',
        'description': 'Cozy amber warmth for a welcoming dashboard feel',
        'category': 'light',
        'preview': {
            'primary': '#f59e0b',
            'secondary': '#d97706',
            'background': '#fffbeb',
            'surface': '#fef3c7',
            'accent': '#d97706',
        },
        'is_dark': False,
        'order': 8,
    },

    # -------------------------------------------------------------------------
    # 9. Forest Light Theme - Natural calm green
    # -------------------------------------------------------------------------
    'forest': {
        'id': 'forest',
        'name': 'Forest Light',
        'label': 'Forest Light',
        'description': 'Fresh natural green for a calm and balanced workspace',
        'category': 'light',
        'preview': {
            'primary': '#22c55e',
            'secondary': '#16a34a',
            'background': '#f0fdf4',
            'surface': '#dcfce7',
            'accent': '#16a34a',
        },
        'is_dark': False,
        'order': 9,
    },

    # -------------------------------------------------------------------------
    # 10. Ocean Light Theme - Clean coastal blue
    # -------------------------------------------------------------------------
    'ocean': {
        'id': 'ocean',
        'name': 'Ocean Light',
        'label': 'Ocean Light',
        'description': 'Fresh coastal blue for a clean professional look',
        'category': 'light',
        'preview': {
            'primary': '#3b82f6',
            'secondary': '#1d4ed8',
            'background': '#eff6ff',
            'surface': '#dbeafe',
            'accent': '#1d4ed8',
        },
        'is_dark': False,
        'order': 10,
    },

    # -------------------------------------------------------------------------
    # 11. Slate Light Theme - Neutral professional gray
    # -------------------------------------------------------------------------
    'slate': {
        'id': 'slate',
        'name': 'Slate Light',
        'label': 'Slate Light',
        'description': 'Neutral professional gray for focused work',
        'category': 'light',
        'preview': {
            'primary': '#64748b',
            'secondary': '#475569',
            'background': '#f8fafc',
            'surface': '#f1f5f9',
            'accent': '#334155',
        },
        'is_dark': False,
        'order': 11,
    },
}

# Default theme when none is selected
DEFAULT_THEME = 'dark'

# Themes that are considered "dark" (for body/html class)
DARK_THEMES = ['dark', 'blue', 'green', 'orange', 'purple']


# =============================================================================
# SEMANTIC DESIGN TOKEN DEFINITIONS
# =============================================================================
# These tokens map to CSS variables. Each theme fills these tokens
# with appropriate values for its color palette.

THEME_TOKEN_CATEGORIES = {
    # -------------------------------------------------------------------------
    # Backgrounds & Surfaces
    # -------------------------------------------------------------------------
    'background': {
        'name': 'Background',
        'description': 'Page/app background color',
        'token': '--theme-bg',
    },
    'surface': {
        'name': 'Surface',
        'description': 'Card and panel backgrounds',
        'token': '--theme-surface',
    },
    'surface-hover': {
        'name': 'Surface Hover',
        'description': 'Hover state for surfaces',
        'token': '--theme-surface-hover',
    },
    'surface-raised': {
        'name': 'Surface Raised',
        'description': 'Elevated elements like dropdowns',
        'token': '--theme-surface-raised',
    },

    # -------------------------------------------------------------------------
    # Text Colors
    # -------------------------------------------------------------------------
    'text-primary': {
        'name': 'Text Primary',
        'description': 'Main body text color',
        'token': '--theme-text-primary',
    },
    'text-secondary': {
        'name': 'Text Secondary',
        'description': 'Muted/supporting text',
        'token': '--theme-text-secondary',
    },
    'text-muted': {
        'name': 'Text Muted',
        'description': 'Disabled/placeholder text',
        'token': '--theme-text-muted',
    },
    'text-inverse': {
        'name': 'Text Inverse',
        'description': 'Text on dark/colored backgrounds',
        'token': '--theme-text-inverse',
    },

    # -------------------------------------------------------------------------
    # Brand / Primary Colors
    # -------------------------------------------------------------------------
    'primary': {
        'name': 'Primary',
        'description': 'Primary brand/action color',
        'token': '--theme-primary',
    },
    'primary-hover': {
        'name': 'Primary Hover',
        'description': 'Hover state for primary',
        'token': '--theme-primary-hover',
    },
    'primary-light': {
        'name': 'Primary Light',
        'description': 'Lighter primary for backgrounds',
        'token': '--theme-primary-light',
    },
    'primary-fg': {
        'name': 'Primary Foreground',
        'description': 'Text on primary color',
        'token': '--theme-primary-fg',
    },

    # -------------------------------------------------------------------------
    # Secondary Colors
    # -------------------------------------------------------------------------
    'secondary': {
        'name': 'Secondary',
        'description': 'Secondary accent color',
        'token': '--theme-secondary',
    },
    'secondary-hover': {
        'name': 'Secondary Hover',
        'description': 'Hover state for secondary',
        'token': '--theme-secondary-hover',
    },
    'secondary-fg': {
        'name': 'Secondary Foreground',
        'description': 'Text on secondary color',
        'token': '--theme-secondary-fg',
    },

    # -------------------------------------------------------------------------
    # Accent Colors
    # -------------------------------------------------------------------------
    'accent': {
        'name': 'Accent',
        'description': 'Highlight/accent color',
        'token': '--theme-accent',
    },
    'accent-hover': {
        'name': 'Accent Hover',
        'description': 'Hover state for accent',
        'token': '--theme-accent-hover',
    },

    # -------------------------------------------------------------------------
    # Status Colors
    # -------------------------------------------------------------------------
    'success': {
        'name': 'Success',
        'description': 'Success/positive states',
        'token': '--theme-success',
    },
    'success-bg': {
        'name': 'Success Background',
        'description': 'Success badge background',
        'token': '--theme-success-bg',
    },
    'warning': {
        'name': 'Warning',
        'description': 'Warning/caution states',
        'token': '--theme-warning',
    },
    'warning-bg': {
        'name': 'Warning Background',
        'description': 'Warning badge background',
        'token': '--theme-warning-bg',
    },
    'danger': {
        'name': 'Danger',
        'description': 'Error/danger states',
        'token': '--theme-danger',
    },
    'danger-bg': {
        'name': 'Danger Background',
        'description': 'Danger badge background',
        'token': '--theme-danger-bg',
    },
    'info': {
        'name': 'Info',
        'description': 'Informational states',
        'token': '--theme-info',
    },
    'info-bg': {
        'name': 'Info Background',
        'description': 'Info badge background',
        'token': '--theme-info-bg',
    },

    # -------------------------------------------------------------------------
    # Border Colors
    # -------------------------------------------------------------------------
    'border': {
        'name': 'Border',
        'description': 'Default border color',
        'token': '--theme-border',
    },
    'border-strong': {
        'name': 'Border Strong',
        'description': 'Emphasized borders',
        'token': '--theme-border-strong',
    },
    'border-focus': {
        'name': 'Border Focus',
        'description': 'Focus ring/border color',
        'token': '--theme-border-focus',
    },

    # -------------------------------------------------------------------------
    # Sidebar & Navigation
    # -------------------------------------------------------------------------
    'sidebar-bg': {
        'name': 'Sidebar Background',
        'description': 'Sidebar navigation background',
        'token': '--theme-sidebar-bg',
    },
    'sidebar-text': {
        'name': 'Sidebar Text',
        'description': 'Sidebar link text color',
        'token': '--theme-sidebar-text',
    },
    'sidebar-text-active': {
        'name': 'Sidebar Active Text',
        'description': 'Active sidebar link text',
        'token': '--theme-sidebar-text-active',
    },
    'sidebar-icon': {
        'name': 'Sidebar Icon',
        'description': 'Sidebar icon color',
        'token': '--theme-sidebar-icon',
    },
    'sidebar-hover-bg': {
        'name': 'Sidebar Hover Background',
        'description': 'Sidebar link hover background',
        'token': '--theme-sidebar-hover-bg',
    },
    'sidebar-active-bg': {
        'name': 'Sidebar Active Background',
        'description': 'Active sidebar link background',
        'token': '--theme-sidebar-active-bg',
    },

    # -------------------------------------------------------------------------
    # Input / Form Colors
    # -------------------------------------------------------------------------
    'input-bg': {
        'name': 'Input Background',
        'description': 'Form input background',
        'token': '--theme-input-bg',
    },
    'input-border': {
        'name': 'Input Border',
        'description': 'Form input border',
        'token': '--theme-input-border',
    },
    'input-text': {
        'name': 'Input Text',
        'description': 'Form input text color',
        'token': '--theme-input-text',
    },
    'input-placeholder': {
        'name': 'Input Placeholder',
        'description': 'Form input placeholder text',
        'token': '--theme-input-placeholder',
    },
    'input-focus-border': {
        'name': 'Input Focus Border',
        'description': 'Focused input border',
        'token': '--theme-input-focus-border',
    },
    'input-focus-ring': {
        'name': 'Input Focus Ring',
        'description': 'Focused input ring/shadow',
        'token': '--theme-input-focus-ring',
    },

    # -------------------------------------------------------------------------
    # Table Colors
    # -------------------------------------------------------------------------
    'table-header-bg': {
        'name': 'Table Header Background',
        'description': 'Table header cell background',
        'token': '--theme-table-header-bg',
    },
    'table-header-text': {
        'name': 'Table Header Text',
        'description': 'Table header text color',
        'token': '--theme-table-header-text',
    },
    'table-row-bg': {
        'name': 'Table Row Background',
        'description': 'Default table row background',
        'token': '--theme-table-row-bg',
    },
    'table-row-alt-bg': {
        'name': 'Table Row Alt Background',
        'description': 'Alternate/striped table row',
        'token': '--theme-table-row-alt-bg',
    },
    'table-row-hover': {
        'name': 'Table Row Hover',
        'description': 'Hovered table row',
        'token': '--theme-table-row-hover',
    },
    'table-border': {
        'name': 'Table Border',
        'description': 'Table cell borders',
        'token': '--theme-table-border',
    },

    # -------------------------------------------------------------------------
    # Overlay / Modal
    # -------------------------------------------------------------------------
    'overlay': {
        'name': 'Overlay',
        'description': 'Modal/drawer backdrop',
        'token': '--theme-overlay',
    },
    'modal-bg': {
        'name': 'Modal Background',
        'description': 'Modal dialog background',
        'token': '--theme-modal-bg',
    },
    'modal-border': {
        'name': 'Modal Border',
        'description': 'Modal dialog border',
        'token': '--theme-modal-border',
    },

    # -------------------------------------------------------------------------
    # Scrollbar
    # -------------------------------------------------------------------------
    'scrollbar-thumb': {
        'name': 'Scrollbar Thumb',
        'description': 'Scrollbar handle color',
        'token': '--theme-scrollbar-thumb',
    },
    'scrollbar-thumb-hover': {
        'name': 'Scrollbar Thumb Hover',
        'description': 'Scrollbar handle hover color',
        'token': '--theme-scrollbar-thumb-hover',
    },

    # -------------------------------------------------------------------------
    # Shadow
    # -------------------------------------------------------------------------
    'shadow': {
        'name': 'Shadow',
        'description': 'Default box shadow',
        'token': '--theme-shadow',
    },
    'shadow-lg': {
        'name': 'Shadow Large',
        'description': 'Large elevated shadow',
        'token': '--theme-shadow-lg',
    },
}


# =============================================================================
# CHART COLOR PALETTES
# =============================================================================
# Each theme has a curated color palette optimized for charts.
# These ensure good contrast and visual distinction.

CHART_PALETTES: Dict[str, List[str]] = {
    'dark': [
        '#38bdf8',  # Cyan - primary accent
        '#818cf8',  # Indigo
        '#34d399',  # Emerald
        '#fbbf24',  # Amber
        '#f87171',  # Red
        '#a78bfa',  # Violet
        '#2dd4bf',  # Teal
        '#fb923c',  # Orange
        '#e879f9',  # Fuchsia
        '#94a3b8',  # Slate
    ],
    'light': [
        '#0284c7',  # Sky 700
        '#6366f1',  # Indigo 500
        '#16a34a',  # Green 600
        '#d97706',  # Amber 600
        '#dc2626',  # Red 600
        '#9333ea',  # Purple 500
        '#0d9488',  # Teal 600
        '#ea580c',  # Orange 600
        '#c026d3',  # Fuchsia 500
        '#475569',  # Slate 600
    ],
    'blue': [
        '#3b82f6',  # Blue 500
        '#60a5fa',  # Blue 400
        '#1d4ed8',  # Blue 700
        '#93c5fd',  # Blue 300
        '#2563eb',  # Blue 600
        '#bfdbfe',  # Blue 200
        '#1e40af',  # Blue 800
        '#60a5fa',  # Blue 400 (alt)
        '#3b82f6',
        '#93c5fd',
    ],
    'green': [
        '#22c55e',  # Green 500
        '#4ade80',  # Green 400
        '#16a34a',  # Green 600
        '#86efac',  # Green 300
        '#15803d',  # Green 700
        '#bbf7d0',  # Green 200
        '#166534',  # Green 800
        '#4ade80',
        '#22c55e',
        '#86efac',
    ],
    'orange': [
        '#f97316',  # Orange 500
        '#fb923c',  # Orange 400
        '#ea580c',  # Orange 600
        '#fdba74',  # Orange 300
        '#c2410c',  # Orange 700
        '#fed7aa',  # Orange 200
        '#9a3412',  # Orange 800
        '#fb923c',
        '#f97316',
        '#fdba74',
    ],
    'purple': [
        '#a855f7',  # Purple 500
        '#c084fc',  # Purple 400
        '#9333ea',  # Purple 600
        '#d8b4fe',  # Purple 300
        '#7e22ce',  # Purple 700
        '#e9d5ff',  # Purple 200
        '#6b21a8',  # Purple 800
        '#c084fc',
        '#a855f7',
        '#d8b4fe',
    ],

    'day': [
        '#0ea5e9',  # Sky 500
        '#6366f1',  # Indigo 500
        '#22c55e',  # Green 500
        '#f59e0b',  # Amber 500
        '#dc2626',  # Red 600
        '#9333ea',  # Purple 500
        '#0d9488',  # Teal 600
        '#ea580c',  # Orange 600
        '#c026d3',  # Fuchsia 500
        '#475569',  # Slate 600
    ],

    'warm': [
        '#f59e0b',  # Amber 500
        '#d97706',  # Amber 600
        '#22c55e',  # Green 500
        '#0ea5e9',  # Sky 500
        '#dc2626',  # Red 600
        '#9333ea',  # Purple 500
        '#0d9488',  # Teal 600
        '#ea580c',  # Orange 600
        '#c026d3',  # Fuchsia 500
        '#475569',  # Slate 600
    ],

    'forest': [
        '#22c55e',  # Green 500
        '#16a34a',  # Green 600
        '#0ea5e9',  # Sky 500
        '#f59e0b',  # Amber 500
        '#dc2626',  # Red 600
        '#9333ea',  # Purple 500
        '#0d9488',  # Teal 600
        '#ea580c',  # Orange 600
        '#c026d3',  # Fuchsia 500
        '#475569',  # Slate 600
    ],

    'ocean': [
        '#3b82f6',  # Blue 500
        '#1d4ed8',  # Blue 700
        '#22c55e',  # Green 500
        '#f59e0b',  # Amber 500
        '#dc2626',  # Red 600
        '#9333ea',  # Purple 500
        '#0d9488',  # Teal 600
        '#ea580c',  # Orange 600
        '#c026d3',  # Fuchsia 500
        '#475569',  # Slate 600
    ],

    'slate': [
        '#64748b',  # Slate 500
        '#475569',  # Slate 600
        '#22c55e',  # Green 500
        '#f59e0b',  # Amber 500
        '#dc2626',  # Red 600
        '#9333ea',  # Purple 500
        '#0d9488',  # Teal 600
        '#ea580c',  # Orange 600
        '#c026d3',  # Fuchsia 500
        '#0ea5e9',  # Sky 500
    ],
}


# =============================================================================
# THEME TOKEN VALUES PER THEME
# =============================================================================
# Complete token mappings for each theme.

THEME_TOKENS: Dict[str, Dict[str, str]] = {
    'dark': {
        # Backgrounds
        '--theme-bg': '#0f172a',
        '--theme-surface': '#1e293b',
        '--theme-surface-hover': '#334155',
        '--theme-surface-raised': '#334155',

        # Text
        '--theme-text-primary': '#f8fafc',
        '--theme-text-secondary': '#94a3b8',
        '--theme-text-muted': '#64748b',
        '--theme-text-inverse': '#0f172a',

        # Primary
        '--theme-primary': '#0ea5e9',
        '--theme-primary-hover': '#38bdf8',
        '--theme-primary-light': 'rgba(14, 165, 233, 0.15)',
        '--theme-primary-fg': '#ffffff',

        # Secondary
        '--theme-secondary': '#6366f1',
        '--theme-secondary-hover': '#818cf8',
        '--theme-secondary-fg': '#ffffff',

        # Accent
        '--theme-accent': '#38bdf8',
        '--theme-accent-hover': '#7dd3fc',

        # Status
        '--theme-success': '#22c55e',
        '--theme-success-bg': 'rgba(34, 197, 94, 0.15)',
        '--theme-warning': '#f59e0b',
        '--theme-warning-bg': 'rgba(245, 158, 11, 0.15)',
        '--theme-danger': '#ef4444',
        '--theme-danger-bg': 'rgba(239, 68, 68, 0.15)',
        '--theme-info': '#38bdf8',
        '--theme-info-bg': 'rgba(56, 189, 248, 0.15)',

        # Borders
        '--theme-border': 'rgba(255, 255, 255, 0.08)',
        '--theme-border-strong': 'rgba(255, 255, 255, 0.15)',
        '--theme-border-focus': '#0ea5e9',

        # Sidebar
        '--theme-sidebar-bg': '#0c1425',
        '--theme-sidebar-text': '#94a3b8',
        '--theme-sidebar-text-active': '#f8fafc',
        '--theme-sidebar-icon': '#e2e8f0',
        '--theme-sidebar-hover-bg': 'rgba(255, 255, 255, 0.05)',
        '--theme-sidebar-active-bg': 'rgba(14, 165, 233, 0.12)',

        # Input
        '--theme-input-bg': 'rgba(30, 41, 59, 0.8)',
        '--theme-input-border': 'rgba(255, 255, 255, 0.1)',
        '--theme-input-text': '#f8fafc',
        '--theme-input-placeholder': '#64748b',
        '--theme-input-focus-border': '#0ea5e9',
        '--theme-input-focus-ring': 'rgba(14, 165, 233, 0.25)',

        # Table
        '--theme-table-header-bg': '#1e293b',
        '--theme-table-header-text': '#e2e8f0',
        '--theme-table-row-bg': 'transparent',
        '--theme-table-row-alt-bg': 'rgba(255, 255, 255, 0.02)',
        '--theme-table-row-hover': 'rgba(255, 255, 255, 0.05)',
        '--theme-table-border': 'rgba(255, 255, 255, 0.06)',

        # Overlay
        '--theme-overlay': 'rgba(0, 0, 0, 0.7)',
        '--theme-modal-bg': '#1e293b',
        '--theme-modal-border': 'rgba(255, 255, 255, 0.08)',

        # Scrollbar
        '--theme-scrollbar-thumb': '#334155',
        '--theme-scrollbar-thumb-hover': '#475569',

        # Shadow
        '--theme-shadow': '0 4px 6px -1px rgba(0, 0, 0, 0.3)',
        '--theme-shadow-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.4)',
    },

    'light': {
        # Backgrounds
        '--theme-bg': '#eff5fb',
        '--theme-surface': '#ffffff',
        '--theme-surface-hover': '#f1f5f9',
        '--theme-surface-raised': '#ffffff',

        # Text
        '--theme-text-primary': '#0f172a',
        '--theme-text-secondary': '#475569',
        '--theme-text-muted': '#94a3b8',
        '--theme-text-inverse': '#ffffff',

        # Primary
        '--theme-primary': '#0ea5e9',
        '--theme-primary-hover': '#0284c7',
        '--theme-primary-light': 'rgba(14, 165, 233, 0.1)',
        '--theme-primary-fg': '#ffffff',

        # Secondary
        '--theme-secondary': '#6366f1',
        '--theme-secondary-hover': '#4f46e5',
        '--theme-secondary-fg': '#ffffff',

        # Accent
        '--theme-accent': '#0284c7',
        '--theme-accent-hover': '#0369a1',

        # Status
        '--theme-success': '#16a34a',
        '--theme-success-bg': 'rgba(22, 163, 74, 0.1)',
        '--theme-warning': '#d97706',
        '--theme-warning-bg': 'rgba(217, 119, 6, 0.1)',
        '--theme-danger': '#dc2626',
        '--theme-danger-bg': 'rgba(220, 38, 38, 0.1)',
        '--theme-info': '#0284c7',
        '--theme-info-bg': 'rgba(2, 132, 199, 0.1)',

        # Borders
        '--theme-border': 'rgba(15, 23, 42, 0.08)',
        '--theme-border-strong': 'rgba(15, 23, 42, 0.15)',
        '--theme-border-focus': '#0ea5e9',

        # Sidebar
        '--theme-sidebar-bg': '#ffffff',
        '--theme-sidebar-text': '#475569',
        '--theme-sidebar-text-active': '#0f172a',
        '--theme-sidebar-icon': '#334155',
        '--theme-sidebar-hover-bg': 'rgba(15, 23, 42, 0.04)',
        '--theme-sidebar-active-bg': 'rgba(14, 165, 233, 0.08)',

        # Input
        '--theme-input-bg': 'rgba(255, 255, 255, 0.92)',
        '--theme-input-border': 'rgba(15, 23, 42, 0.12)',
        '--theme-input-text': '#0f172a',
        '--theme-input-placeholder': '#94a3b8',
        '--theme-input-focus-border': '#0ea5e9',
        '--theme-input-focus-ring': 'rgba(14, 165, 233, 0.2)',

        # Table
        '--theme-table-header-bg': '#f8fafc',
        '--theme-table-header-text': '#334155',
        '--theme-table-row-bg': 'transparent',
        '--theme-table-row-alt-bg': 'rgba(15, 23, 42, 0.02)',
        '--theme-table-row-hover': 'rgba(15, 23, 42, 0.04)',
        '--theme-table-border': 'rgba(15, 23, 42, 0.06)',

        # Overlay
        '--theme-overlay': 'rgba(15, 23, 42, 0.5)',
        '--theme-modal-bg': '#ffffff',
        '--theme-modal-border': 'rgba(15, 23, 42, 0.08)',

        # Scrollbar
        '--theme-scrollbar-thumb': '#cbd5e1',
        '--theme-scrollbar-thumb-hover': '#94a3b8',

        # Shadow
        '--theme-shadow': '0 1px 3px rgba(0, 0, 0, 0.08)',
        '--theme-shadow-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
    },

    'blue': {
        # Backgrounds
        '--theme-bg': '#0c1929',
        '--theme-surface': '#1e3a5f',
        '--theme-surface-hover': '#254d7a',
        '--theme-surface-raised': '#254d7a',

        # Text
        '--theme-text-primary': '#f8fafc',
        '--theme-text-secondary': '#93c5fd',
        '--theme-text-muted': '#60a5fa',
        '--theme-text-inverse': '#0c1929',

        # Primary
        '--theme-primary': '#3b82f6',
        '--theme-primary-hover': '#60a5fa',
        '--theme-primary-light': 'rgba(59, 130, 246, 0.15)',
        '--theme-primary-fg': '#ffffff',

        # Secondary
        '--theme-secondary': '#1d4ed8',
        '--theme-secondary-hover': '#3b82f6',
        '--theme-secondary-fg': '#ffffff',

        # Accent
        '--theme-accent': '#60a5fa',
        '--theme-accent-hover': '#93c5fd',

        # Status
        '--theme-success': '#22c55e',
        '--theme-success-bg': 'rgba(34, 197, 94, 0.15)',
        '--theme-warning': '#f59e0b',
        '--theme-warning-bg': 'rgba(245, 158, 11, 0.15)',
        '--theme-danger': '#ef4444',
        '--theme-danger-bg': 'rgba(239, 68, 68, 0.15)',
        '--theme-info': '#38bdf8',
        '--theme-info-bg': 'rgba(56, 189, 248, 0.15)',

        # Borders
        '--theme-border': 'rgba(59, 130, 246, 0.15)',
        '--theme-border-strong': 'rgba(59, 130, 246, 0.3)',
        '--theme-border-focus': '#3b82f6',

        # Sidebar
        '--theme-sidebar-bg': '#0a1520',
        '--theme-sidebar-text': '#93c5fd',
        '--theme-sidebar-text-active': '#f8fafc',
        '--theme-sidebar-icon': '#93c5fd',
        '--theme-sidebar-hover-bg': 'rgba(59, 130, 246, 0.08)',
        '--theme-sidebar-active-bg': 'rgba(59, 130, 246, 0.15)',

        # Input
        '--theme-input-bg': 'rgba(30, 58, 95, 0.6)',
        '--theme-input-border': 'rgba(59, 130, 246, 0.2)',
        '--theme-input-text': '#f8fafc',
        '--theme-input-placeholder': '#60a5fa',
        '--theme-input-focus-border': '#3b82f6',
        '--theme-input-focus-ring': 'rgba(59, 130, 246, 0.25)',

        # Table
        '--theme-table-header-bg': '#1e3a5f',
        '--theme-table-header-text': '#bfdbfe',
        '--theme-table-row-bg': 'transparent',
        '--theme-table-row-alt-bg': 'rgba(59, 130, 246, 0.04)',
        '--theme-table-row-hover': 'rgba(59, 130, 246, 0.08)',
        '--theme-table-border': 'rgba(59, 130, 246, 0.1)',

        # Overlay
        '--theme-overlay': 'rgba(0, 0, 0, 0.7)',
        '--theme-modal-bg': '#1e3a5f',
        '--theme-modal-border': 'rgba(59, 130, 246, 0.2)',

        # Scrollbar
        '--theme-scrollbar-thumb': '#254d7a',
        '--theme-scrollbar-thumb-hover': '#3b82f6',

        # Shadow
        '--theme-shadow': '0 4px 6px -1px rgba(0, 0, 0, 0.4)',
        '--theme-shadow-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.5)',
    },

    'green': {
        # Backgrounds
        '--theme-bg': '#0f1f0f',
        '--theme-surface': '#1a2e1a',
        '--theme-surface-hover': '#243524',
        '--theme-surface-raised': '#243524',

        # Text
        '--theme-text-primary': '#f0fdf4',
        '--theme-text-secondary': '#86efac',
        '--theme-text-muted': '#4ade80',
        '--theme-text-inverse': '#0f1f0f',

        # Primary
        '--theme-primary': '#22c55e',
        '--theme-primary-hover': '#4ade80',
        '--theme-primary-light': 'rgba(34, 197, 94, 0.15)',
        '--theme-primary-fg': '#ffffff',

        # Secondary
        '--theme-secondary': '#16a34a',
        '--theme-secondary-hover': '#22c55e',
        '--theme-secondary-fg': '#ffffff',

        # Accent
        '--theme-accent': '#4ade80',
        '--theme-accent-hover': '#86efac',

        # Status
        '--theme-success': '#22c55e',
        '--theme-success-bg': 'rgba(34, 197, 94, 0.15)',
        '--theme-warning': '#eab308',
        '--theme-warning-bg': 'rgba(234, 179, 8, 0.15)',
        '--theme-danger': '#ef4444',
        '--theme-danger-bg': 'rgba(239, 68, 68, 0.15)',
        '--theme-info': '#2dd4bf',
        '--theme-info-bg': 'rgba(45, 212, 191, 0.15)',

        # Borders
        '--theme-border': 'rgba(34, 197, 94, 0.15)',
        '--theme-border-strong': 'rgba(34, 197, 94, 0.3)',
        '--theme-border-focus': '#22c55e',

        # Sidebar
        '--theme-sidebar-bg': '#0a160a',
        '--theme-sidebar-text': '#86efac',
        '--theme-sidebar-text-active': '#f0fdf4',
        '--theme-sidebar-icon': '#86efac',
        '--theme-sidebar-hover-bg': 'rgba(34, 197, 94, 0.08)',
        '--theme-sidebar-active-bg': 'rgba(34, 197, 94, 0.15)',

        # Input
        '--theme-input-bg': 'rgba(26, 46, 26, 0.6)',
        '--theme-input-border': 'rgba(34, 197, 94, 0.2)',
        '--theme-input-text': '#f0fdf4',
        '--theme-input-placeholder': '#4ade80',
        '--theme-input-focus-border': '#22c55e',
        '--theme-input-focus-ring': 'rgba(34, 197, 94, 0.25)',

        # Table
        '--theme-table-header-bg': '#1a2e1a',
        '--theme-table-header-text': '#bbf7d0',
        '--theme-table-row-bg': 'transparent',
        '--theme-table-row-alt-bg': 'rgba(34, 197, 94, 0.04)',
        '--theme-table-row-hover': 'rgba(34, 197, 94, 0.08)',
        '--theme-table-border': 'rgba(34, 197, 94, 0.1)',

        # Overlay
        '--theme-overlay': 'rgba(0, 0, 0, 0.7)',
        '--theme-modal-bg': '#1a2e1a',
        '--theme-modal-border': 'rgba(34, 197, 94, 0.2)',

        # Scrollbar
        '--theme-scrollbar-thumb': '#243524',
        '--theme-scrollbar-thumb-hover': '#22c55e',

        # Shadow
        '--theme-shadow': '0 4px 6px -1px rgba(0, 0, 0, 0.4)',
        '--theme-shadow-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.5)',
    },

    'orange': {
        # Backgrounds
        '--theme-bg': '#1f1410',
        '--theme-surface': '#2d1f15',
        '--theme-surface-hover': '#3d2a1a',
        '--theme-surface-raised': '#3d2a1a',

        # Text
        '--theme-text-primary': '#fffbeb',
        '--theme-text-secondary': '#fdba74',
        '--theme-text-muted': '#fb923c',
        '--theme-text-inverse': '#1f1410',

        # Primary
        '--theme-primary': '#f97316',
        '--theme-primary-hover': '#fb923c',
        '--theme-primary-light': 'rgba(249, 115, 22, 0.15)',
        '--theme-primary-fg': '#ffffff',

        # Secondary
        '--theme-secondary': '#ea580c',
        '--theme-secondary-hover': '#f97316',
        '--theme-secondary-fg': '#ffffff',

        # Accent
        '--theme-accent': '#fb923c',
        '--theme-accent-hover': '#fdba74',

        # Status
        '--theme-success': '#22c55e',
        '--theme-success-bg': 'rgba(34, 197, 94, 0.15)',
        '--theme-warning': '#f59e0b',
        '--theme-warning-bg': 'rgba(245, 158, 11, 0.15)',
        '--theme-danger': '#ef4444',
        '--theme-danger-bg': 'rgba(239, 68, 68, 0.15)',
        '--theme-info': '#38bdf8',
        '--theme-info-bg': 'rgba(56, 189, 248, 0.15)',

        # Borders
        '--theme-border': 'rgba(249, 115, 22, 0.15)',
        '--theme-border-strong': 'rgba(249, 115, 22, 0.3)',
        '--theme-border-focus': '#f97316',

        # Sidebar
        '--theme-sidebar-bg': '#160f0a',
        '--theme-sidebar-text': '#fdba74',
        '--theme-sidebar-text-active': '#fffbeb',
        '--theme-sidebar-icon': '#fdba74',
        '--theme-sidebar-hover-bg': 'rgba(249, 115, 22, 0.08)',
        '--theme-sidebar-active-bg': 'rgba(249, 115, 22, 0.15)',

        # Input
        '--theme-input-bg': 'rgba(45, 31, 21, 0.6)',
        '--theme-input-border': 'rgba(249, 115, 22, 0.2)',
        '--theme-input-text': '#fffbeb',
        '--theme-input-placeholder': '#fb923c',
        '--theme-input-focus-border': '#f97316',
        '--theme-input-focus-ring': 'rgba(249, 115, 22, 0.25)',

        # Table
        '--theme-table-header-bg': '#2d1f15',
        '--theme-table-header-text': '#fed7aa',
        '--theme-table-row-bg': 'transparent',
        '--theme-table-row-alt-bg': 'rgba(249, 115, 22, 0.04)',
        '--theme-table-row-hover': 'rgba(249, 115, 22, 0.08)',
        '--theme-table-border': 'rgba(249, 115, 22, 0.1)',

        # Overlay
        '--theme-overlay': 'rgba(0, 0, 0, 0.7)',
        '--theme-modal-bg': '#2d1f15',
        '--theme-modal-border': 'rgba(249, 115, 22, 0.2)',

        # Scrollbar
        '--theme-scrollbar-thumb': '#3d2a1a',
        '--theme-scrollbar-thumb-hover': '#f97316',

        # Shadow
        '--theme-shadow': '0 4px 6px -1px rgba(0, 0, 0, 0.4)',
        '--theme-shadow-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.5)',
    },

    'purple': {
        # Backgrounds
        '--theme-bg': '#13101a',
        '--theme-surface': '#1f1830',
        '--theme-surface-hover': '#2a2040',
        '--theme-surface-raised': '#2a2040',

        # Text
        '--theme-text-primary': '#faf5ff',
        '--theme-text-secondary': '#d8b4fe',
        '--theme-text-muted': '#c084fc',
        '--theme-text-inverse': '#13101a',

        # Primary
        '--theme-primary': '#a855f7',
        '--theme-primary-hover': '#c084fc',
        '--theme-primary-light': 'rgba(168, 85, 247, 0.15)',
        '--theme-primary-fg': '#ffffff',

        # Secondary
        '--theme-secondary': '#9333ea',
        '--theme-secondary-hover': '#a855f7',
        '--theme-secondary-fg': '#ffffff',

        # Accent
        '--theme-accent': '#c084fc',
        '--theme-accent-hover': '#d8b4fe',

        # Status
        '--theme-success': '#22c55e',
        '--theme-success-bg': 'rgba(34, 197, 94, 0.15)',
        '--theme-warning': '#f59e0b',
        '--theme-warning-bg': 'rgba(245, 158, 11, 0.15)',
        '--theme-danger': '#ef4444',
        '--theme-danger-bg': 'rgba(239, 68, 68, 0.15)',
        '--theme-info': '#38bdf8',
        '--theme-info-bg': 'rgba(56, 189, 248, 0.15)',

        # Borders
        '--theme-border': 'rgba(168, 85, 247, 0.15)',
        '--theme-border-strong': 'rgba(168, 85, 247, 0.3)',
        '--theme-border-focus': '#a855f7',

        # Sidebar
        '--theme-sidebar-bg': '#0d0a12',
        '--theme-sidebar-text': '#d8b4fe',
        '--theme-sidebar-text-active': '#faf5ff',
        '--theme-sidebar-icon': '#d8b4fe',
        '--theme-sidebar-hover-bg': 'rgba(168, 85, 247, 0.08)',
        '--theme-sidebar-active-bg': 'rgba(168, 85, 247, 0.15)',

        # Input
        '--theme-input-bg': 'rgba(31, 24, 48, 0.6)',
        '--theme-input-border': 'rgba(168, 85, 247, 0.2)',
        '--theme-input-text': '#faf5ff',
        '--theme-input-placeholder': '#c084fc',
        '--theme-input-focus-border': '#a855f7',
        '--theme-input-focus-ring': 'rgba(168, 85, 247, 0.25)',

        # Table
        '--theme-table-header-bg': '#1f1830',
        '--theme-table-header-text': '#e9d5ff',
        '--theme-table-row-bg': 'transparent',
        '--theme-table-row-alt-bg': 'rgba(168, 85, 247, 0.04)',
        '--theme-table-row-hover': 'rgba(168, 85, 247, 0.08)',
        '--theme-table-border': 'rgba(168, 85, 247, 0.1)',

        # Overlay
        '--theme-overlay': 'rgba(0, 0, 0, 0.7)',
        '--theme-modal-bg': '#1f1830',
        '--theme-modal-border': 'rgba(168, 85, 247, 0.2)',

        # Scrollbar
        '--theme-scrollbar-thumb': '#2a2040',
        '--theme-scrollbar-thumb-hover': '#a855f7',

        # Shadow
        '--theme-shadow': '0 4px 6px -1px rgba(0, 0, 0, 0.4)',
        '--theme-shadow-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.5)',
    },

    'day': {
        # Backgrounds
        '--theme-bg': '#f0f9ff',
        '--theme-surface': '#ffffff',
        '--theme-surface-hover': '#e0f2fe',
        '--theme-surface-raised': '#ffffff',

        # Text
        '--theme-text-primary': '#0c4a6e',
        '--theme-text-secondary': '#0369a1',
        '--theme-text-muted': '#38bdf8',
        '--theme-text-inverse': '#ffffff',

        # Primary
        '--theme-primary': '#0ea5e9',
        '--theme-primary-hover': '#0284c7',
        '--theme-primary-light': 'rgba(14, 165, 233, 0.12)',
        '--theme-primary-fg': '#ffffff',

        # Secondary
        '--theme-secondary': '#6366f1',
        '--theme-secondary-hover': '#4f46e5',
        '--theme-secondary-fg': '#ffffff',

        # Accent
        '--theme-accent': '#0284c7',
        '--theme-accent-hover': '#0369a1',

        # Status
        '--theme-success': '#16a34a',
        '--theme-success-bg': 'rgba(22, 163, 74, 0.1)',
        '--theme-warning': '#d97706',
        '--theme-warning-bg': 'rgba(217, 119, 6, 0.1)',
        '--theme-danger': '#dc2626',
        '--theme-danger-bg': 'rgba(220, 38, 38, 0.1)',
        '--theme-info': '#0284c7',
        '--theme-info-bg': 'rgba(2, 132, 199, 0.1)',

        # Borders
        '--theme-border': 'rgba(14, 165, 233, 0.12)',
        '--theme-border-strong': 'rgba(14, 165, 233, 0.2)',
        '--theme-border-focus': '#0ea5e9',

        # Sidebar
        '--theme-sidebar-bg': '#ffffff',
        '--theme-sidebar-text': '#0369a1',
        '--theme-sidebar-text-active': '#0c4a6e',
        '--theme-sidebar-icon': '#0284c7',
        '--theme-sidebar-hover-bg': 'rgba(14, 165, 233, 0.06)',
        '--theme-sidebar-active-bg': 'rgba(14, 165, 233, 0.1)',

        # Input
        '--theme-input-bg': 'rgba(240, 249, 255, 0.9)',
        '--theme-input-border': 'rgba(14, 165, 233, 0.2)',
        '--theme-input-text': '#0c4a6e',
        '--theme-input-placeholder': '#38bdf8',
        '--theme-input-focus-border': '#0ea5e9',
        '--theme-input-focus-ring': 'rgba(14, 165, 233, 0.2)',

        # Table
        '--theme-table-header-bg': '#e0f2fe',
        '--theme-table-header-text': '#0369a1',
        '--theme-table-row-bg': 'transparent',
        '--theme-table-row-alt-bg': 'rgba(14, 165, 233, 0.03)',
        '--theme-table-row-hover': 'rgba(14, 165, 233, 0.06)',
        '--theme-table-border': 'rgba(14, 165, 233, 0.08)',

        # Overlay
        '--theme-overlay': 'rgba(12, 74, 110, 0.4)',
        '--theme-modal-bg': '#ffffff',
        '--theme-modal-border': 'rgba(14, 165, 233, 0.12)',

        # Scrollbar
        '--theme-scrollbar-thumb': '#bae6fd',
        '--theme-scrollbar-thumb-hover': '#7dd3fc',

        # Shadow
        '--theme-shadow': '0 1px 3px rgba(0, 0, 0, 0.06)',
        '--theme-shadow-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.08)',
    },

    'warm': {
        # Backgrounds
        '--theme-bg': '#fffbeb',
        '--theme-surface': '#fef3c7',
        '--theme-surface-hover': '#fde68a',
        '--theme-surface-raised': '#ffffff',

        # Text
        '--theme-text-primary': '#78350f',
        '--theme-text-secondary': '#92400e',
        '--theme-text-muted': '#d97706',
        '--theme-text-inverse': '#ffffff',

        # Primary
        '--theme-primary': '#f59e0b',
        '--theme-primary-hover': '#d97706',
        '--theme-primary-light': 'rgba(245, 158, 11, 0.12)',
        '--theme-primary-fg': '#ffffff',

        # Secondary
        '--theme-secondary': '#d97706',
        '--theme-secondary-hover': '#b45309',
        '--theme-secondary-fg': '#ffffff',

        # Accent
        '--theme-accent': '#d97706',
        '--theme-accent-hover': '#b45309',

        # Status
        '--theme-success': '#16a34a',
        '--theme-success-bg': 'rgba(22, 163, 74, 0.1)',
        '--theme-warning': '#f59e0b',
        '--theme-warning-bg': 'rgba(245, 158, 11, 0.1)',
        '--theme-danger': '#dc2626',
        '--theme-danger-bg': 'rgba(220, 38, 38, 0.1)',
        '--theme-info': '#0ea5e9',
        '--theme-info-bg': 'rgba(14, 165, 233, 0.1)',

        # Borders
        '--theme-border': 'rgba(217, 119, 6, 0.12)',
        '--theme-border-strong': 'rgba(217, 119, 6, 0.2)',
        '--theme-border-focus': '#f59e0b',

        # Sidebar
        '--theme-sidebar-bg': '#fef3c7',
        '--theme-sidebar-text': '#92400e',
        '--theme-sidebar-text-active': '#78350f',
        '--theme-sidebar-icon': '#d97706',
        '--theme-sidebar-hover-bg': 'rgba(217, 119, 6, 0.08)',
        '--theme-sidebar-active-bg': 'rgba(245, 158, 11, 0.12)',

        # Input
        '--theme-input-bg': 'rgba(255, 251, 235, 0.9)',
        '--theme-input-border': 'rgba(217, 119, 6, 0.2)',
        '--theme-input-text': '#78350f',
        '--theme-input-placeholder': '#d97706',
        '--theme-input-focus-border': '#f59e0b',
        '--theme-input-focus-ring': 'rgba(245, 158, 11, 0.2)',

        # Table
        '--theme-table-header-bg': '#fde68a',
        '--theme-table-header-text': '#78350f',
        '--theme-table-row-bg': 'transparent',
        '--theme-table-row-alt-bg': 'rgba(217, 119, 6, 0.03)',
        '--theme-table-row-hover': 'rgba(217, 119, 6, 0.06)',
        '--theme-table-border': 'rgba(217, 119, 6, 0.08)',

        # Overlay
        '--theme-overlay': 'rgba(120, 53, 15, 0.4)',
        '--theme-modal-bg': '#fef3c7',
        '--theme-modal-border': 'rgba(217, 119, 6, 0.12)',

        # Scrollbar
        '--theme-scrollbar-thumb': '#fcd34d',
        '--theme-scrollbar-thumb-hover': '#fbbf24',

        # Shadow
        '--theme-shadow': '0 1px 3px rgba(0, 0, 0, 0.06)',
        '--theme-shadow-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.08)',
    },

    'forest': {
        # Backgrounds
        '--theme-bg': '#f0fdf4',
        '--theme-surface': '#dcfce7',
        '--theme-surface-hover': '#bbf7d0',
        '--theme-surface-raised': '#ffffff',

        # Text
        '--theme-text-primary': '#14532d',
        '--theme-text-secondary': '#166534',
        '--theme-text-muted': '#22c55e',
        '--theme-text-inverse': '#ffffff',

        # Primary
        '--theme-primary': '#22c55e',
        '--theme-primary-hover': '#16a34a',
        '--theme-primary-light': 'rgba(34, 197, 94, 0.12)',
        '--theme-primary-fg': '#ffffff',

        # Secondary
        '--theme-secondary': '#16a34a',
        '--theme-secondary-hover': '#15803d',
        '--theme-secondary-fg': '#ffffff',

        # Accent
        '--theme-accent': '#16a34a',
        '--theme-accent-hover': '#15803d',

        # Status
        '--theme-success': '#22c55e',
        '--theme-success-bg': 'rgba(34, 197, 94, 0.1)',
        '--theme-warning': '#eab308',
        '--theme-warning-bg': 'rgba(234, 179, 8, 0.1)',
        '--theme-danger': '#dc2626',
        '--theme-danger-bg': 'rgba(220, 38, 38, 0.1)',
        '--theme-info': '#0ea5e9',
        '--theme-info-bg': 'rgba(14, 165, 233, 0.1)',

        # Borders
        '--theme-border': 'rgba(22, 163, 74, 0.12)',
        '--theme-border-strong': 'rgba(22, 163, 74, 0.2)',
        '--theme-border-focus': '#22c55e',

        # Sidebar
        '--theme-sidebar-bg': '#dcfce7',
        '--theme-sidebar-text': '#166534',
        '--theme-sidebar-text-active': '#14532d',
        '--theme-sidebar-icon': '#16a34a',
        '--theme-sidebar-hover-bg': 'rgba(22, 163, 74, 0.08)',
        '--theme-sidebar-active-bg': 'rgba(34, 197, 94, 0.12)',

        # Input
        '--theme-input-bg': 'rgba(240, 253, 244, 0.9)',
        '--theme-input-border': 'rgba(22, 163, 74, 0.2)',
        '--theme-input-text': '#14532d',
        '--theme-input-placeholder': '#22c55e',
        '--theme-input-focus-border': '#22c55e',
        '--theme-input-focus-ring': 'rgba(34, 197, 94, 0.2)',

        # Table
        '--theme-table-header-bg': '#bbf7d0',
        '--theme-table-header-text': '#14532d',
        '--theme-table-row-bg': 'transparent',
        '--theme-table-row-alt-bg': 'rgba(22, 163, 74, 0.03)',
        '--theme-table-row-hover': 'rgba(22, 163, 74, 0.06)',
        '--theme-table-border': 'rgba(22, 163, 74, 0.08)',

        # Overlay
        '--theme-overlay': 'rgba(20, 83, 45, 0.4)',
        '--theme-modal-bg': '#dcfce7',
        '--theme-modal-border': 'rgba(22, 163, 74, 0.12)',

        # Scrollbar
        '--theme-scrollbar-thumb': '#86efac',
        '--theme-scrollbar-thumb-hover': '#4ade80',

        # Shadow
        '--theme-shadow': '0 1px 3px rgba(0, 0, 0, 0.06)',
        '--theme-shadow-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.08)',
    },

    'ocean': {
        # Backgrounds
        '--theme-bg': '#eff6ff',
        '--theme-surface': '#dbeafe',
        '--theme-surface-hover': '#bfdbfe',
        '--theme-surface-raised': '#ffffff',

        # Text
        '--theme-text-primary': '#1e3a8a',
        '--theme-text-secondary': '#1e40af',
        '--theme-text-muted': '#3b82f6',
        '--theme-text-inverse': '#ffffff',

        # Primary
        '--theme-primary': '#3b82f6',
        '--theme-primary-hover': '#1d4ed8',
        '--theme-primary-light': 'rgba(59, 130, 246, 0.12)',
        '--theme-primary-fg': '#ffffff',

        # Secondary
        '--theme-secondary': '#1d4ed8',
        '--theme-secondary-hover': '#1e40af',
        '--theme-secondary-fg': '#ffffff',

        # Accent
        '--theme-accent': '#1d4ed8',
        '--theme-accent-hover': '#1e40af',

        # Status
        '--theme-success': '#22c55e',
        '--theme-success-bg': 'rgba(34, 197, 94, 0.1)',
        '--theme-warning': '#eab308',
        '--theme-warning-bg': 'rgba(234, 179, 8, 0.1)',
        '--theme-danger': '#dc2626',
        '--theme-danger-bg': 'rgba(220, 38, 38, 0.1)',
        '--theme-info': '#3b82f6',
        '--theme-info-bg': 'rgba(59, 130, 246, 0.1)',

        # Borders
        '--theme-border': 'rgba(59, 130, 246, 0.12)',
        '--theme-border-strong': 'rgba(59, 130, 246, 0.2)',
        '--theme-border-focus': '#3b82f6',

        # Sidebar
        '--theme-sidebar-bg': '#dbeafe',
        '--theme-sidebar-text': '#1e40af',
        '--theme-sidebar-text-active': '#1e3a8a',
        '--theme-sidebar-icon': '#1d4ed8',
        '--theme-sidebar-hover-bg': 'rgba(59, 130, 246, 0.08)',
        '--theme-sidebar-active-bg': 'rgba(59, 130, 246, 0.12)',

        # Input
        '--theme-input-bg': 'rgba(239, 246, 255, 0.9)',
        '--theme-input-border': 'rgba(59, 130, 246, 0.2)',
        '--theme-input-text': '#1e3a8a',
        '--theme-input-placeholder': '#3b82f6',
        '--theme-input-focus-border': '#3b82f6',
        '--theme-input-focus-ring': 'rgba(59, 130, 246, 0.2)',

        # Table
        '--theme-table-header-bg': '#bfdbfe',
        '--theme-table-header-text': '#1e3a8a',
        '--theme-table-row-bg': 'transparent',
        '--theme-table-row-alt-bg': 'rgba(59, 130, 246, 0.03)',
        '--theme-table-row-hover': 'rgba(59, 130, 246, 0.06)',
        '--theme-table-border': 'rgba(59, 130, 246, 0.08)',

        # Overlay
        '--theme-overlay': 'rgba(30, 58, 138, 0.4)',
        '--theme-modal-bg': '#dbeafe',
        '--theme-modal-border': 'rgba(59, 130, 246, 0.12)',

        # Scrollbar
        '--theme-scrollbar-thumb': '#93c5fd',
        '--theme-scrollbar-thumb-hover': '#60a5fa',

        # Shadow
        '--theme-shadow': '0 1px 3px rgba(0, 0, 0, 0.06)',
        '--theme-shadow-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.08)',
    },

    'slate': {
        # Backgrounds
        '--theme-bg': '#f8fafc',
        '--theme-surface': '#f1f5f9',
        '--theme-surface-hover': '#e2e8f0',
        '--theme-surface-raised': '#ffffff',

        # Text
        '--theme-text-primary': '#0f172a',
        '--theme-text-secondary': '#334155',
        '--theme-text-muted': '#64748b',
        '--theme-text-inverse': '#ffffff',

        # Primary
        '--theme-primary': '#64748b',
        '--theme-primary-hover': '#475569',
        '--theme-primary-light': 'rgba(100, 116, 139, 0.12)',
        '--theme-primary-fg': '#ffffff',

        # Secondary
        '--theme-secondary': '#475569',
        '--theme-secondary-hover': '#334155',
        '--theme-secondary-fg': '#ffffff',

        # Accent
        '--theme-accent': '#334155',
        '--theme-accent-hover': '#1e293b',

        # Status
        '--theme-success': '#22c55e',
        '--theme-success-bg': 'rgba(34, 197, 94, 0.1)',
        '--theme-warning': '#eab308',
        '--theme-warning-bg': 'rgba(234, 179, 8, 0.1)',
        '--theme-danger': '#dc2626',
        '--theme-danger-bg': 'rgba(220, 38, 38, 0.1)',
        '--theme-info': '#3b82f6',
        '--theme-info-bg': 'rgba(59, 130, 246, 0.1)',

        # Borders
        '--theme-border': 'rgba(100, 116, 139, 0.12)',
        '--theme-border-strong': 'rgba(100, 116, 139, 0.2)',
        '--theme-border-focus': '#64748b',

        # Sidebar
        '--theme-sidebar-bg': '#f1f5f9',
        '--theme-sidebar-text': '#475569',
        '--theme-sidebar-text-active': '#0f172a',
        '--theme-sidebar-icon': '#334155',
        '--theme-sidebar-hover-bg': 'rgba(100, 116, 139, 0.08)',
        '--theme-sidebar-active-bg': 'rgba(100, 116, 139, 0.12)',

        # Input
        '--theme-input-bg': 'rgba(248, 250, 252, 0.9)',
        '--theme-input-border': 'rgba(100, 116, 139, 0.2)',
        '--theme-input-text': '#0f172a',
        '--theme-input-placeholder': '#64748b',
        '--theme-input-focus-border': '#64748b',
        '--theme-input-focus-ring': 'rgba(100, 116, 139, 0.2)',

        # Table
        '--theme-table-header-bg': '#e2e8f0',
        '--theme-table-header-text': '#0f172a',
        '--theme-table-row-bg': 'transparent',
        '--theme-table-row-alt-bg': 'rgba(100, 116, 139, 0.03)',
        '--theme-table-row-hover': 'rgba(100, 116, 139, 0.06)',
        '--theme-table-border': 'rgba(100, 116, 139, 0.08)',

        # Overlay
        '--theme-overlay': 'rgba(15, 23, 42, 0.4)',
        '--theme-modal-bg': '#f1f5f9',
        '--theme-modal-border': 'rgba(100, 116, 139, 0.12)',

        # Scrollbar
        '--theme-scrollbar-thumb': '#cbd5e1',
        '--theme-scrollbar-thumb-hover': '#94a3b8',

        # Shadow
        '--theme-shadow': '0 1px 3px rgba(0, 0, 0, 0.06)',
        '--theme-shadow-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.08)',
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_available_themes() -> List[Dict[str, Any]]:
    """Return list of all available themes sorted by order."""
    return sorted(AVAILABLE_THEMES.values(), key=lambda t: t['order'])


def get_theme_config(theme_id: str) -> Optional[Dict[str, Any]]:
    """Get configuration for a specific theme."""
    return AVAILABLE_THEMES.get(theme_id)


def get_theme_tokens(theme_id: str) -> Dict[str, str]:
    """Get all CSS tokens for a specific theme."""
    return THEME_TOKENS.get(theme_id, THEME_TOKENS.get(DEFAULT_THEME))


def get_chart_palette(theme_id: str) -> List[str]:
    """Get chart color palette for a specific theme."""
    return CHART_PALETTES.get(theme_id, CHART_PALETTES.get(DEFAULT_THEME))


def is_dark_theme(theme_id: str) -> bool:
    """Check if a theme is a dark variant."""
    return theme_id in DARK_THEMES


def validate_theme(theme_id: str) -> bool:
    """Validate if a theme ID is valid."""
    return theme_id in AVAILABLE_THEMES


def get_default_theme() -> str:
    """Get the default theme ID."""
    return DEFAULT_THEME


def get_all_theme_ids() -> List[str]:
    """Get all theme IDs."""
    return list(AVAILABLE_THEMES.keys())
