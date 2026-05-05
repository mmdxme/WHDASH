"""
Logging configuration for WHDASH.

This module configures application-wide logging with:
- Daily rotating file handler (midnight rotation, 30 days retention)
- Console handler for development
- Structured formatting with timestamps, level, name, and location
- Reduced noise from third-party libraries

Usage:
    from utils.logging_config import configure_logging

    app = Flask(__name__)
    configure_logging(app)
"""

import logging
import logging.handlers
import os
from typing import Optional


def configure_logging(
    app,
    log_level: Optional[int] = None,
    log_dir: Optional[str] = None
) -> None:
    """
    Configure application logging with file and console handlers.

    Args:
        app: Flask application instance
        log_level: Log level (default: DEBUG if app.config.get('DEBUG'), else INFO)
        log_dir: Directory for log files (default: <app_root>/logs)
    """
    if log_level is None:
        log_level = logging.DEBUG if app.config.get('DEBUG') else logging.INFO

    # Determine log directory
    if log_dir is None:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')

    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Configure formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s [%(filename)s:%(lineno)d]'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s'
    )

    # File handler - rotate daily at midnight, keep 30 days
    file_handler = logging.handlers.TimedRotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    file_handler.setFormatter(detailed_formatter)
    file_handler.setLevel(log_level)

    # Console handler - for development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(simple_formatter)
    console_handler.setLevel(log_level)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(log_level)

    # Flask app logger
    app.logger.handlers.clear()
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)

    # Reduce noise from third-party libraries
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('flask_cors').setLevel(logging.WARNING)

    # Reduce noise from data processing libraries
    logging.getLogger('pandas').setLevel(logging.WARNING)
    logging.getLogger('openpyxl').setLevel(logging.WARNING)

    # Application-specific log level configuration
    if not app.config.get('DEBUG'):
        # In production, reduce verbosity from application modules
        logging.getLogger('werkzeug').setLevel(logging.ERROR)

    app.logger.info(f"Logging configured: level={logging.getLevelName(log_level)}, log_dir={log_dir}")