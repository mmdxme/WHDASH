"""Jinja2 Template Filters - Custom filters for Flask templates."""
from flask import Flask
import datetime
import json


def register_jinja_filters(app: Flask):
    """Register all custom Jinja2 filters."""

    @app.template_filter('currency')
    def currency_filter(value, symbol='$'):
        """Format number as currency."""
        try:
            return f"{symbol}{float(value):,.2f}"
        except (ValueError, TypeError):
            return value

    @app.template_filter('percentage')
    def percentage_filter(value, decimals=1):
        """Format number as percentage."""
        try:
            return f"{float(value):.{decimals}f}%"
        except (ValueError, TypeError):
            return value

    @app.template_filter('relative_time')
    def relative_time(value):
        """Format datetime as relative time (e.g., '2 hours ago')."""
        if isinstance(value, str):
            try:
                value = datetime.datetime.fromisoformat(value)
            except ValueError:
                return value

        if not isinstance(value, datetime.datetime):
            return value

        now = datetime.datetime.now()
        delta = now - value

        if delta.days > 365:
            return f"{delta.days // 365}y ago"
        elif delta.days > 30:
            return f"{delta.days // 30}mo ago"
        elif delta.days > 0:
            return f"{delta.days}d ago"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600}h ago"
        elif delta.seconds > 60:
            return f"{delta.seconds // 60}m ago"
        else:
            return "just now"

    @app.template_filter('pluralize')
    def pluralize_filter(count, singular='', plural='s'):
        """Add plural suffix if count != 1."""
        return singular if count == 1 else plural

    @app.template_filter('truncate_chars')
    def truncate_chars(value, length=50):
        """Truncate string to specified length."""
        if not isinstance(value, str):
            value = str(value)
        return value[:length] + '...' if len(value) > length else value

    @app.template_filter('json_loads')
    def json_loads_filter(value):
        """Parse JSON string to Python object."""
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return {}

    @app.template_filter('file_size')
    def file_size_filter(bytes_value):
        """Format bytes as human-readable file size."""
        try:
            bytes_value = int(bytes_value)
        except (ValueError, TypeError):
            return bytes_value

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024
        return f"{bytes_value:.1f} PB"

    @app.template_filter('date_format')
    def date_format_filter(value, format='%Y-%m-%d'):
        """Format date with custom format."""
        if isinstance(value, str):
            try:
                value = datetime.datetime.fromisoformat(value)
            except ValueError:
                return value

        if isinstance(value, (datetime.datetime, datetime.date)):
            return value.strftime(format)
        return value

    @app.template_filter('date')
    def date_filter(value, format='%Y-%m-%d'):
        """Format date or datetime object, or the string 'now' to current date/time."""
        if value == 'now' or value is None:
            return datetime.datetime.now().strftime(format)

        if isinstance(value, str):
            try:
                value = datetime.datetime.fromisoformat(value)
            except ValueError:
                try:
                    value = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return value

        if isinstance(value, (datetime.datetime, datetime.date)):
            return value.strftime(format)
        return value

    @app.template_filter('initials')
    def initials_filter(name):
        """Get initials from a name."""
        if not name:
            return ''
        parts = name.split()
        return ''.join(p[0].upper() for p in parts[:2])

    return app