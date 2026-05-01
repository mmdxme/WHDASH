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
        raise RuntimeError(
            "SECRET_KEY environment variable must be set in production. "
            "Generate a secure key with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    # Development-only weak key - NEVER used in production
    SECRET_KEY = os.environ.get('DEV_SECRET_KEY', 'dev-only-insecure-key-do-not-use-in-prod')

# Ensure SECRET_KEY is sufficiently long for security
if len(SECRET_KEY) < 32 and ENV == 'production':
    raise RuntimeError("SECRET_KEY must be at least 32 characters (64 hex digits) for adequate security")

# VAPID keys for Web Push - MUST come from environment in production
_VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY')
_VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY')
if not _VAPID_PUBLIC_KEY or not _VAPID_PRIVATE_KEY:
    if ENV == 'production':
        raise RuntimeError(
            "VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY environment variables must be set in production. "
            "Generate keys with: python -c \"from webpush import vapid; v = vapid.VAPID(); print('PUBLIC:', v.public_key); print('PRIVATE:', v.private_key)\""
        )
    # Development fallback - use insecure defaults
    _VAPID_PUBLIC_KEY = 'MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEY-hwQ6_Hdk7VJ4fTNt1P1S0qX63wxwwtrfbnfPDPGwpckcjeTF337se9o6Ncgn5lp6rHPSzoJq_rwDUAqlI_oQ'
    _VAPID_PRIVATE_KEY = 'MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgIrq9m4IxBGkkkOX315urB7sbbkE7_GIvRGD0csfA6hehRANCAARj6HBDr8d2TtUnh9M23U_VLSpfrfDHDC2t9ud88M8bClyRyN5MXffux72jo1yCfmWnqsc9LOgmr-vANQCqUj+h'

VAPID_PUBLIC_KEY = _VAPID_PUBLIC_KEY
VAPID_PRIVATE_KEY = _VAPID_PRIVATE_KEY
VAPID_SUBJECT = os.environ.get('VAPID_SUBJECT', 'mailto:notifications@example.com')


# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'warehouse.db'))

# =============================================================================
# DATABASE ENGINE SELECTION (PostgreSQL-ready Architecture)
# =============================================================================
# Set DB_ENGINE to 'postgresql' to switch from SQLite to PostgreSQL

DB_ENGINE = os.environ.get('DB_ENGINE', 'sqlite').lower()

# PostgreSQL Configuration (used when DB_ENGINE='postgresql')
POSTGRESQL_HOST = os.environ.get('POSTGRESQL_HOST', 'localhost')
POSTGRESQL_PORT = int(os.environ.get('POSTGRESQL_PORT', '5432'))
POSTGRESQL_DATABASE = os.environ.get('POSTGRESQL_DATABASE', 'whdash')
POSTGRESQL_USER = os.environ.get('POSTGRESQL_USER', 'whdash_user')
POSTGRESQL_PASSWORD = os.environ.get('POSTGRESQL_PASSWORD', '')
POSTGRESQL_SCHEMA = os.environ.get('POSTGRESQL_SCHEMA', 'public')

# PostgreSQL Connection Pooling
POSTGRESQL_POOL_SIZE = int(os.environ.get('POSTGRESQL_POOL_SIZE', '20'))
POSTGRESQL_MAX_OVERFLOW = int(os.environ.get('POSTGRESQL_MAX_OVERFLOW', '40'))
POSTGRESQL_POOL_TIMEOUT = int(os.environ.get('POSTGRESQL_POOL_TIMEOUT', '30'))
POSTGRESQL_POOL_RECYCLE = int(os.environ.get('POSTGRESQL_POOL_RECYCLE', '3600'))  # Recycle after 1 hour

# Build PostgreSQL connection URL
if DB_ENGINE == 'postgresql' and POSTGRESQL_PASSWORD:
    POSTGRESQL_URL = f"postgresql://{POSTGRESQL_USER}:{POSTGRESQL_PASSWORD}@{POSTGRESQL_HOST}:{POSTGRESQL_PORT}/{POSTGRESQL_DATABASE}"
elif DB_ENGINE == 'postgresql':
    POSTGRESQL_URL = f"postgresql://{POSTGRESQL_USER}@{POSTGRESQL_HOST}:{POSTGRESQL_PORT}/{POSTGRESQL_DATABASE}"
else:
    POSTGRESQL_URL = None

# SQLite Connection Pool Settings (for app-level pooling)
DB_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', '5'))
DB_MAX_OVERFLOW = int(os.environ.get('DB_MAX_OVERFLOW', '10'))

# =============================================================================
# REDIS CONFIGURATION (Session & Cache)
# =============================================================================

REDIS_URL = os.environ.get('REDIS_URL', '')
REDIS_CACHE_URL = os.environ.get('REDIS_CACHE_URL', '')

# If REDIS_URL is not set but we're in production, try default local Redis
if not REDIS_URL and ENV == 'production':
    REDIS_URL = 'redis://localhost:6379/0'
if not REDIS_CACHE_URL and not REDIS_URL:
    REDIS_CACHE_URL = 'redis://localhost:6379/1'

# Use Redis for sessions if REDIS_URL is configured
SESSION_TYPE = 'redis' if REDIS_URL else 'filesystem'

# Cache configuration
CACHE_TYPE = 'redis' if REDIS_CACHE_URL or REDIS_URL else 'simple'
CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', '300'))

# Redis Cache TTL Settings (in seconds)
REDIS_CACHE_TTL = {
    'user_permissions': int(os.environ.get('CACHE_TTL_USER_PERMS', '300')),      # 5 minutes
    'dashboard_kpis': int(os.environ.get('CACHE_TTL_KPIS', '300')),              # 5 minutes
    'navigation': int(os.environ.get('CACHE_TTL_NAV', '900')),                   # 15 minutes
    'settings': int(os.environ.get('CACHE_TTL_SETTINGS', '1800')),              # 30 minutes
    'category_list': int(os.environ.get('CACHE_TTL_CATEGORIES', '3600')),        # 1 hour
    'report_data': int(os.environ.get('CACHE_TTL_REPORTS', '600')),             # 10 minutes
    'query_result': int(os.environ.get('CACHE_TTL_QUERY', '300')),              # 5 minutes
    'master_data': int(os.environ.get('CACHE_TTL_MASTER', '1800')),             # 30 minutes
    'notification_count': int(os.environ.get('CACHE_TTL_NOTIF_COUNT', '60')),    # 1 minute
}

# Query Cache Settings
QUERY_CACHE_SIZE = int(os.environ.get('QUERY_CACHE_SIZE', '1000'))
QUERY_CACHE_TTL = int(os.environ.get('QUERY_CACHE_TTL', '300'))


# =============================================================================
# CELERY BACKGROUND JOB CONFIGURATION
# =============================================================================

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', '')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', '')

# If Redis is configured, use it as Celery broker by default
if not CELERY_BROKER_URL and REDIS_URL:
    CELERY_BROKER_URL = REDIS_URL.replace('/0/', '/2/') if '/0/' in REDIS_URL else f"{REDIS_URL}/2"
if not CELERY_RESULT_BACKEND and REDIS_URL:
    CELERY_RESULT_BACKEND = REDIS_URL.replace('/0/', '/3/') if '/0/' in REDIS_URL else f"{REDIS_URL}/3"

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = os.environ.get('CELERY_TIMEZONE', 'UTC')
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes max per task
CELERY_RESULT_EXTENDED = True


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

SESSION_PERMANENT = True
PERMANENT_SESSION_LIFETIME = 120  # minutes
# Session file directory - use a persistent location
SESSION_FILE_DIR = os.path.join(BASE_DIR, 'flask_session')


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
DEFAULT_SALVAGE_VALUE_PERCENT = 10


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
