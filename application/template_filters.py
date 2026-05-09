"""
Template Filters Module
=======================

Jinja2 template filters that can be used in Flask templates.
This module centralizes filter definitions that were previously in app.py.

Usage:
    from application.template_filters import register_template_filters

    app = create_app()
    register_template_filters(app)
"""

from flask import Flask
from datetime import datetime, date
import html
import json


def register_template_filters(app: Flask) -> None:
    """
    Register all template filters with the Flask application.

    Args:
        app: Flask application instance
    """

    @app.template_filter('escape_html')
    def escape_html_filter(text):
        """Escape HTML entities in text."""
        return html.escape(text) if text else ''

    @app.template_filter('date')
    def date_filter(value, format='%Y-%m-%d'):
        """
        Format a date value.

        Usage: {{ some_date | date }}
              {{ some_date | date('%d/%m/%Y') }}
        """
        if value == 'now' or value is None:
            return datetime.now().strftime(format)
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                try:
                    value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return value
        if isinstance(value, (datetime, date)):
            return value.strftime(format)
        return value

    @app.template_filter('from_json')
    def from_json_filter(text):
        """Parse JSON string to list/dict."""
        if not text:
            return []
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return []

    @app.template_filter('to_json')
    def to_json_filter(value):
        """Convert value to JSON string."""
        return json.dumps(value)

    @app.template_filter('truncate_words')
    def truncate_words_filter(text, num_words=50):
        """Truncate text to a certain number of words."""
        if not text:
            return ''
        words = str(text).split()
        if len(words) <= num_words:
            return text
        return ' '.join(words[:num_words]) + '...'

    @app.template_filter('filesizeformat')
    def filesizeformat_filter(bytes_value):
        """Format bytes as human-readable file size."""
        try:
            bytes_value = int(bytes_value)
        except (ValueError, TypeError):
            return '0 B'
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"

    @app.template_filter('percentage')
    def percentage_filter(value, decimals=1):
        """Format a decimal as percentage."""
        try:
            value = float(value) * 100
            return f"{value:.{decimals}f}%"
        except (ValueError, TypeError):
            return '0%'

    @app.template_filter('dict_get')
    def dict_get_filter(d, key, default=''):
        """Get value from dictionary with default."""
        if isinstance(d, dict):
            return d.get(key, default)
        return default