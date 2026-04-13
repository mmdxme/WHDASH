"""
Application Configuration
========================
Centralized configuration for MMDx.

This module provides:
- Environment-based configuration
- Secret key management
- Database path configuration
- Upload folder settings
- Session configuration
- Security settings
"""

import os


# =============================================================================
# BASE DIRECTORY
# =============================================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


# =============================================================================
# ENVIRONMENT CONFIGURATION
# =============================================================================

ENV = os.environ.get('FLASK_ENV', 'production')
DEBUG = ENV == 'development'


# =============================================================================
# SECURITY SETTINGS
# =============================================================================

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if ENV == 'production':
        raise RuntimeError("SECRET_KEY environment variable must be set in production")
    SECRET_KEY = 'change-me-in-development'


# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'warehouse.db'))


# =============================================================================
# UPLOAD SETTINGS
# =============================================================================

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_AVATAR_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg', 'gif', 'txt', 'csv', 'zip', 'rar'}
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB
MAX_DOCUMENT_SIZE = 50 * 1024 * 1024  # 50MB


# =============================================================================
# SESSION CONFIGURATION
# =============================================================================

SESSION_TYPE = 'filesystem'
SESSION_PERMANENT = True
PERMANENT_SESSION_LIFETIME = 120  # minutes


# =============================================================================
# APPLICATION SETTINGS
# =============================================================================

APP_NAME = 'MMDx'
APP_VERSION = '1.0.0'
DEFAULT_LANGUAGE = 'en'
DEFAULT_THEME = 'dark'
DEFAULT_CURRENCY = 'AED'
DEFAULT_TIMEZONE = 'Asia/Dubai'
DATE_FORMAT = 'DD/MM/YYYY'
ITEMS_PER_PAGE = 50


# =============================================================================
# SECURITY HEADERS
# =============================================================================

SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'SAMEORIGIN',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
}


# =============================================================================
# CORS SETTINGS (for API)
# =============================================================================

CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',') if os.environ.get('CORS_ORIGINS') else []
CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization', 'X-Requested-With']
CORS_EXPOSE_HEADERS = ['X-Request-ID', 'X-Response-Time']


# =============================================================================
# RATE LIMITING
# =============================================================================

RATELIMIT_ENABLED = True
RATELIMIT_DEFAULT = "200 per day"
RATELIMIT_LOGIN = "10 per minute"
RATELIMIT_API = "1000 per day"


# =============================================================================
# PAGINATION DEFAULTS
# =============================================================================

PAGINATION_PAGE_SIZES = [25, 50, 100, 200]
DEFAULT_PAGE_SIZE = 50


# =============================================================================
# CACHE SETTINGS (for future Redis integration)
# =============================================================================

CACHE_TYPE = 'simple'  # Can be 'redis' in production
CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FILE = os.environ.get('LOG_FILE', os.path.join(BASE_DIR, 'logs', 'app.log'))


# =============================================================================
# THIRD-PARTY SERVICE CONFIGURATION
# =============================================================================

# Google Workspace
GOOGLE_WORKSPACE_ENABLED = os.environ.get('GOOGLE_WORKSPACE_ENABLED', 'false').lower() == 'true'
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

# Peyvast Sync
PEYVAST_SYNC_ENABLED = os.environ.get('PEYVAST_SYNC_ENABLED', 'false').lower() == 'true'
PEYVAST_API_URL = os.environ.get('PEYVAST_API_URL', '')
PEYVAST_API_KEY = os.environ.get('PEYVAST_API_KEY', '')


# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================

EMAIL_ENABLED = os.environ.get('EMAIL_ENABLED', 'false').lower() == 'true'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.example.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'true').lower() == 'true'
EMAIL_USERNAME = os.environ.get('EMAIL_USERNAME', '')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')
EMAIL_FROM = os.environ.get('EMAIL_FROM', 'noreply@warehouse.local')


# =============================================================================
# EXPORT SETTINGS
# =============================================================================

EXPORT_CHUNK_SIZE = 1000
EXPORT_MAX_ROWS = 100000


# =============================================================================
# VALIDATION SETTINGS
# =============================================================================

PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGIT = True
PASSWORD_REQUIRE_SPECIAL = False

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 50
USERNAME_PATTERN = r'^[\w_]+$'

MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15


# =============================================================================
# ASSET DEPRECIATION SETTINGS
# =============================================================================

DEFAULT_DEPRECIATION_METHOD = 'straight_line'
DEFAULT_USEFUL_LIFE_YEARS = 5
DEFAULT Salvage_VALUE_PERCENT = 10


# =============================================================================
# INVENTORY SETTINGS
# =============================================================================

DEFAULT_LOW_STOCK_THRESHOLD = 10
DEFAULT_REORDER_POINT = 20
ENABLE_NEGATIVE_STOCK = False  # Prevent negative inventory


# =============================================================================
# QUALITY SETTINGS
# =============================================================================

QUALITY_AUTO_NCR_ON_FAIL = True
QUALITY_NCR_NUMBERING_PREFIX = 'NCR'
QUALITY_INSPECTION_NUMBERING_PREFIX = 'INS'
QUALITY_DEFAULT_SEVERITY = 'MINOR'


# =============================================================================
# FLOW PUSH NOTIFICATION SETTINGS (WebPush/VAPID)
# =============================================================================

# VAPID Keys for Web Push Notifications
# Generate new keys using:
#   python -c "from webpush import vapid; v = vapid.VAPID(); print(v.public_key, v.private_key)"
# Or use the generate_vapid_keys.py script

VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', 'MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEY-hwQ6_Hdk7VJ4fTNt1P1S0qX63wxwwtrfbnfPDPGwpckcjeTF337se9o6Ncgn5lp6rHPSzoJq_rwDUAqlI_oQ')
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', 'MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgIrq9m4IxBGkkkOX315urB7sbbkE7_GIvRGD0csfA6hehRANCAARj6HBDr8d2TtUnh9M23U_VLSpfrfDHDC2t9ud88M8bClyRyN5MXffux72jo1yCfmWnqsc9LOgmr-vANQCqUj-h')

# VAPID subject (mailto or URL for emergency contact)
VAPID_SUBJECT = os.environ.get('VAPID_SUBJECT', 'mailto:notifications@example.com')

# Flow notification settings
FLOW_PUSH_ENABLED = True
FLOW_NOTIFICATION_SOUND_ENABLED = True
FLOW_NOTIFICATION_VIBRATE = True


# =============================================================================
# EXPORT CONFIGURATION HELPERS
# =============================================================================

def get_config_dict():
    """Get configuration as dictionary (excluding secrets)."""
    return {
        'ENV': ENV,
        'DEBUG': DEBUG,
        'DATABASE_PATH': DATABASE_PATH,
        'APP_NAME': APP_NAME,
        'APP_VERSION': APP_VERSION,
        'DEFAULT_LANGUAGE': DEFAULT_LANGUAGE,
        'DEFAULT_THEME': DEFAULT_THEME,
        'DEFAULT_CURRENCY': DEFAULT_CURRENCY,
        'DATE_FORMAT': DATE_FORMAT,
        'ITEMS_PER_PAGE': ITEMS_PER_PAGE,
        'PAGINATION_PAGE_SIZES': PAGINATION_PAGE_SIZES,
        'DEFAULT_PAGE_SIZE': DEFAULT_PAGE_SIZE,
    }
