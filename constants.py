"""
Central Constants for WHDASH - MMDx Platform

This module contains all magic numbers and configuration constants
used across the application. Import from this module instead of using
hardcoded values.

Usage:
    from constants import (
        DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE,
        SESSION_TIMEOUT_MINUTES,
        STATUS_ACTIVE, STATUS_DRAFT
    )

Constants are organized by category:
- Pagination
- Session & Security
- File Upload
- Cache
- Database
- Rate Limiting
- Flow Module
- SCM Planning
- Status Values
- Colors
"""

# =============================================================================
# PAGINATION
# =============================================================================

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 10
PAGINATION_PAGE_SIZES = [25, 50, 100, 200]

# =============================================================================
# SESSION & SECURITY
# =============================================================================

SESSION_TIMEOUT_MINUTES = 120
MAX_LOGIN_ATTEMPTS = 5
PASSWORD_MIN_LENGTH = 8
CSRF_TOKEN_LENGTH = 32

# =============================================================================
# FILE UPLOAD
# =============================================================================

MAX_UPLOAD_SIZE_MB = 50  # General files
MAX_VIDEO_UPLOAD_MB = 500  # Videos
MAX_IMAGE_UPLOAD_MB = 10  # Images
ALLOWED_IMAGE_TYPES = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_DOCUMENT_TYPES = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'csv'}
DANGEROUS_EXTENSIONS = {'exe', 'bat', 'cmd', 'sh', 'php', 'js', 'jar'}

# =============================================================================
# CACHE
# =============================================================================

DEFAULT_CACHE_TTL = 300  # 5 minutes in seconds
SHORT_CACHE_TTL = 60  # 1 minute in seconds
LONG_CACHE_TTL = 3600  # 1 hour in seconds

# =============================================================================
# DATABASE
# =============================================================================

DB_POOL_SIZE = 5
DB_MAX_OVERFLOW = 10
DB_BUSY_TIMEOUT = 5000  # milliseconds

# =============================================================================
# RATE LIMITING
# =============================================================================

RATE_LIMIT_MESSAGES_PER_MINUTE = 10
RATE_LIMIT_API_PER_MINUTE = 60
RATELIMIT_DEFAULT = "200 per day"
RATELIMIT_LOGIN = "10 per minute"
RATELIMIT_API_DAILY = "1000 per day"

# =============================================================================
# FLOW MODULE
# =============================================================================

MAX_MESSAGE_LENGTH = 10000
MAX_CONVERSATION_NAME_LENGTH = 100
MAX_CHANNEL_NAME_LENGTH = 50

# =============================================================================
# SCM PLANNING
# =============================================================================

DEFAULT_SAFETY_STOCK_DAYS = 10
DEFAULT_REORDER_POINT_DAYS = 5
DEMAND_HISTORY_AVG_PERIOD_DAYS = 30

# =============================================================================
# STATUS VALUES
# =============================================================================

STATUS_DRAFT = 'Draft'
STATUS_ACTIVE = 'Active'
STATUS_INACTIVE = 'Inactive'
STATUS_PENDING = 'Pending'
STATUS_APPROVED = 'Approved'
STATUS_REJECTED = 'Rejected'

# =============================================================================
# COLORS (for UI status indicators)
# =============================================================================

STATUS_COLOR_MAP = {
    'Draft': 'gray',
    'Active': 'green',
    'Pending': 'yellow',
    'Approved': 'green',
    'Rejected': 'red',
    'In Progress': 'blue',
    'Completed': 'green',
    'Canceled': 'gray',
    'Low': 'gray',
    'Medium': 'yellow',
    'High': 'orange',
    'Critical': 'red',
}

# =============================================================================
# EMAIL / GMAIL
# =============================================================================

GMAIL_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GMAIL_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GMAIL_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'
GMAIL_GMAIL_API = 'https://gmail.googleapis.com/gmail/v1/users/me'
GMAIL_SCOPES = [
    'openid', 'email', 'profile',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
]

# =============================================================================
# EXPORT SETTINGS
# =============================================================================

CHUNK_SIZE = 5000  # Rows per batch for streaming exports
STREAMING_THRESHOLD = 10000  # Auto-enable streaming above this row count

# =============================================================================
# LOGGING
# =============================================================================

LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/app.log'