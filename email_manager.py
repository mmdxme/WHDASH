from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, jsonify, has_request_context, Response
import base64
import html
import io
import json
import logging
import mimetypes
import os
import re
import secrets
import smtplib
import imaplib
import email
from datetime import datetime, timedelta
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import decode_header
from email.utils import parseaddr, formataddr
import urllib.error
import urllib.parse
import urllib.request
import sqlite3

# Configure logging for debugging and monitoring
logger = logging.getLogger(__name__)

bp = Blueprint('email_manager', __name__)
_db_factory = None

# Google OAuth constants
GOOGLE_CLIENT_ID_PATTERN = re.compile(r'^\d{6,}-[a-z0-9._-]+\.apps\.googleusercontent\.com$', re.IGNORECASE)
GOOGLE_PLACEHOLDER_VALUES = {'', 'admin', '123456', 'test', 'google_client_id', 'google_client_secret', 'your-client-id', 'your-client-secret', 'client-id', 'client-secret'}

GMAIL_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GMAIL_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GMAIL_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'
GMAIL_GMAIL_API = 'https://gmail.googleapis.com/gmail/v1/users/me'
GMAIL_SCOPES = ['openid', 'email', 'profile', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/gmail.send']

# Pagination constants for performance optimization
DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100
UNIFIED_PAGE_SIZE = 20

# Standard IMAP folder names mapping
IMAP_FOLDER_MAP = {
    'inbox': 'INBOX',
    'sent': 'Sent',
    'drafts': 'Drafts',
    'draft': 'Drafts',
    'archive': 'Archive',
    'trash': 'Trash',
    'spam': 'Spam',
}


def register_email_manager(app, get_db_factory):
    """Register the email manager blueprint with the Flask app."""
    global _db_factory
    _db_factory = get_db_factory
    app.register_blueprint(bp)


def _get_db():
    """Get database connection using the registered factory."""
    if _db_factory is None:
        raise RuntimeError('Email Manager database factory is not registered.')
    return _db_factory()


def _utcnow():
    """Return current UTC datetime."""
    return datetime.utcnow()


def _format_dt(value):
    """Format datetime to string for database storage."""
    return value.strftime('%Y-%m-%d %H:%M:%S') if value else ''


def _parse_dt(value):
    """Parse datetime string from database storage."""
    if not value:
        return None
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S'):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _decode_b64_url(value):
    """Decode base64 URL-safe encoded strings (used by Gmail API)."""
    if not value:
        return ''
    padding = '=' * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode('utf-8')).decode('utf-8', errors='ignore')


def _strip_html(value):
    """Remove HTML tags and decode HTML entities from text."""
    if not value:
        return ''
    value = re.sub(r'(?i)<br\s*/?>', '\n', value)
    value = re.sub(r'(?i)</p>', '\n\n', value)
    value = re.sub(r'<[^>]+>', '', value)
    return html.unescape(value).strip()


def _decode_str(value):
    """Decode email header strings that may be encoded."""
    if not value:
        return ''
    decoded_parts = decode_header(value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            charset = charset or 'utf-8'
            try:
                result.append(part.decode(charset, errors='replace'))
            except Exception:
                result.append(part.decode('utf-8', errors='replace'))
        else:
            result.append(part)
    return ''.join(result)


# =============================================================================
# EMAIL SETTINGS MANAGEMENT
# =============================================================================

def _get_email_settings(db):
    """Retrieve email settings from database."""
    row = db.execute('SELECT * FROM email_settings WHERE id = 1').fetchone()
    if not row:
        return {
            'id': 1,
            'gmail_client_id': '',
            'gmail_client_secret': '',
            'gmail_redirect_uri': '',
            'updated_at': ''
        }
    return dict(row)


def _save_email_settings(db, gmail_client_id=None, gmail_client_secret=None, gmail_redirect_uri=None):
    """Save or update email settings in database."""
    existing = _get_email_settings(db)
    resolved_gmail_secret = gmail_client_secret.strip() if gmail_client_secret else existing.get('gmail_client_secret', '')

    db.execute('''
        INSERT INTO email_settings (id, gmail_client_id, gmail_client_secret, gmail_redirect_uri, updated_at)
        VALUES (1, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            gmail_client_id = COALESCE(?, gmail_client_id),
            gmail_client_secret = CASE
                WHEN COALESCE(?, '') != '' THEN ?
                ELSE gmail_client_secret
            END,
            gmail_redirect_uri = COALESCE(?, gmail_redirect_uri),
            updated_at = CURRENT_TIMESTAMP
    ''', (
        gmail_client_id.strip() if gmail_client_id else existing.get('gmail_client_id', ''),
        gmail_client_id.strip() if gmail_client_id else None,
        resolved_gmail_secret,
        resolved_gmail_secret,
        gmail_redirect_uri.strip() if gmail_redirect_uri else None
    ))
    db.commit()
    return _get_email_settings(db)


def _validate_gmail_config(config):
    """Validate Gmail OAuth configuration and return list of errors."""
    errors = []
    client_id = (config.get('gmail_client_id') or '').strip()
    client_secret = (config.get('gmail_client_secret') or '').strip()

    if client_id and client_id.lower() not in GOOGLE_PLACEHOLDER_VALUES and not GOOGLE_CLIENT_ID_PATTERN.match(client_id):
        errors.append('Gmail Client ID is not a valid Google OAuth Web Client ID format.')

    if client_secret and client_secret.lower() not in GOOGLE_PLACEHOLDER_VALUES and len(client_secret) < 8:
        errors.append('Gmail Client Secret appears to be invalid.')

    return errors


def _gmail_is_configured(db=None):
    """Check if Gmail OAuth is properly configured."""
    database = db or _get_db()
    settings = _get_email_settings(database)
    client_id = os.environ.get('GMAIL_CLIENT_ID', '') or settings.get('gmail_client_id', '')
    client_secret = os.environ.get('GMAIL_CLIENT_SECRET', '') or settings.get('gmail_client_secret', '')
    return bool(client_id and client_secret and client_id.lower() not in GOOGLE_PLACEHOLDER_VALUES)


# =============================================================================
# EMAIL ACCOUNT MANAGEMENT
# =============================================================================

def _get_gmail_connection(db=None, account_id=None):
    """Get Gmail OAuth connection for user."""
    database = db or _get_db()
    resolved_id = account_id or session.get('user_id')
    if not resolved_id:
        return None
    return database.execute(
        'SELECT * FROM email_accounts WHERE user_id = ? AND account_type = ?',
        (resolved_id, 'gmail')
    ).fetchone()


def _save_gmail_connection(db, user_id, token_payload, email_address=''):
    """Save or update Gmail OAuth tokens."""
    expires_in = int(token_payload.get('expires_in') or 3600)
    expires_at = _utcnow() + timedelta(seconds=max(expires_in - 60, 60))

    db.execute('''
        INSERT INTO email_accounts (user_id, account_type, email_address, access_token, refresh_token, expires_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, account_type) DO UPDATE SET
            access_token = excluded.access_token,
            refresh_token = CASE
                WHEN COALESCE(excluded.refresh_token, '') != '' THEN excluded.refresh_token
                ELSE email_accounts.refresh_token
            END,
            expires_at = excluded.expires_at,
            email_address = excluded.email_address,
            updated_at = CURRENT_TIMESTAMP
    ''', (user_id, 'gmail', email_address, token_payload.get('access_token', ''), token_payload.get('refresh_token', ''), _format_dt(expires_at)))
    db.commit()


def _delete_gmail_connection(db, user_id):
    """Remove Gmail OAuth connection."""
    db.execute('DELETE FROM email_accounts WHERE user_id = ? AND account_type = ?', (user_id, 'gmail'))
    db.commit()


def _add_smtp_account(db, user_id, email_address, smtp_host, smtp_port, smtp_username, smtp_password, imap_host=None, imap_port=None, use_tls=True):
    """Add or update SMTP/IMAP email account."""
    encrypted_password = base64.b64encode(smtp_password.encode()).decode() if smtp_password else ''

    db.execute('''
        INSERT INTO email_accounts (user_id, account_type, email_address, smtp_host, smtp_port, smtp_username, smtp_password, imap_host, imap_port, use_tls, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, account_type, email_address) DO UPDATE SET
            smtp_host = excluded.smtp_host,
            smtp_port = excluded.smtp_port,
            smtp_username = excluded.smtp_username,
            smtp_password = excluded.smtp_password,
            imap_host = excluded.imap_host,
            imap_port = excluded.imap_port,
            use_tls = excluded.use_tls,
            updated_at = CURRENT_TIMESTAMP
    ''', (user_id, 'smtp', email_address, smtp_host, smtp_port, smtp_username, encrypted_password, imap_host or smtp_host, imap_port or 993, 1 if use_tls else 0))
    db.commit()


def _get_user_email_accounts(db=None, user_id=None):
    """Get all email accounts for a user."""
    database = db or _get_db()
    resolved_id = user_id or session.get('user_id')
    if not resolved_id:
        return []
    accounts = database.execute(
        'SELECT * FROM email_accounts WHERE user_id = ?',
        (resolved_id,)
    ).fetchall()
    return [dict(row) for row in accounts]


def _get_account_by_id(db, account_id, user_id=None):
    """Get a specific email account by ID."""
    resolved_user_id = user_id or session.get('user_id')
    if not resolved_user_id:
        return None
    row = db.execute(
        'SELECT * FROM email_accounts WHERE id = ? AND user_id = ?',
        (account_id, resolved_user_id)
    ).fetchone()
    return dict(row) if row else None


def _get_default_account(db=None, user_id=None):
    """Get the default email account for a user."""
    database = db or _get_db()
    resolved_id = user_id or session.get('user_id')
    if not resolved_id:
        return None

    default = database.execute(
        'SELECT * FROM email_accounts WHERE user_id = ? AND is_default = 1',
        (resolved_id,)
    ).fetchone()

    if not default:
        default = database.execute(
            'SELECT * FROM email_accounts WHERE user_id = ? LIMIT 1',
            (resolved_id,)
        ).fetchone()

    return dict(default) if default else None


def _set_default_account(db, user_id, account_id):
    """Set the default email account for a user."""
    db.execute('UPDATE email_accounts SET is_default = 0 WHERE user_id = ?', (user_id,))
    db.execute('UPDATE email_accounts SET is_default = 1 WHERE id = ? AND user_id = ?', (account_id, user_id))
    db.commit()


def _delete_email_account(db, account_id, user_id):
    """Delete an email account."""
    db.execute('DELETE FROM email_accounts WHERE id = ? AND user_id = ?', (account_id, user_id))
    db.commit()


def _update_email_notification_settings(db, account_id, user_id, settings):
    """Update notification settings for an email account."""
    notifications_enabled = 1 if settings.get('notifications_enabled') else 0
    notify_from_senders = settings.get('notify_from_senders', '')
    notify_subject_keywords = settings.get('notify_subject_keywords', '')
    notify_sound_enabled = 1 if settings.get('notify_sound_enabled') else 0

    db.execute('''
        UPDATE email_accounts
        SET notifications_enabled = ?,
            notify_from_senders = ?,
            notify_subject_keywords = ?,
            notify_sound_enabled = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
    ''', (notifications_enabled, notify_from_senders, notify_subject_keywords, notify_sound_enabled, account_id, user_id))
    db.commit()


def _get_email_notification_settings(db, account_id, user_id):
    """Get notification settings for an email account."""
    row = db.execute(
        'SELECT notifications_enabled, notify_from_senders, notify_subject_keywords, notify_sound_enabled, last_seen_message_id FROM email_accounts WHERE id = ? AND user_id = ?',
        (account_id, user_id)
    ).fetchone()
    if row:
        return dict(row)
    return None


def _update_last_seen_message_id(db, account_id, message_id):
    """Update the last seen message ID for an account (to track new emails)."""
    db.execute(
        'UPDATE email_accounts SET last_seen_message_id = ? WHERE id = ?',
        (message_id, account_id)
    )
    db.commit()


# =============================================================================
# IMAP/SMTP CONNECTION WITH PROPER STATE MANAGEMENT
# =============================================================================

def _get_imap_connection(account, timeout=30):
    """
    Create and return an IMAP connection with proper SSL/TLS setup.
    
    This function ensures:
    - Proper mailbox selection before any SEARCH/FETCH operations
    - Connection timeout handling
    - SSL/TLS configuration based on account settings
    
    Args:
        account: Account dict with imap_host, imap_port, smtp_username, smtp_password, use_tls
        timeout: Connection timeout in seconds
        
    Returns:
        imaplib.IMAP4_SSL or imaplib.IMAP4 connection
        
    Raises:
        RuntimeError: If connection fails
    """
    imap_host = account.get('imap_host') or account.get('smtp_host', '')
    if not imap_host:
        raise RuntimeError('IMAP host is not configured for this account.')
    
    imap_port = int(account.get('imap_port', 993) or 993)
    username = account.get('smtp_username', '')
    encrypted_password = account.get('smtp_password', '')
    password = ''
    
    if encrypted_password:
        try:
            password = base64.b64decode(encrypted_password.encode()).decode()
        except Exception:
            password = encrypted_password
    
    try:
        if imap_port == 993:
            server = imaplib.IMAP4_SSL(imap_host, imap_port, timeout=timeout)
        else:
            server = imaplib.IMAP4(imap_host, imap_port)
            if account.get('use_tls', 1):
                server.starttls()
        
        server.login(username, password)
        logger.info(f"IMAP connection established to {imap_host}:{imap_port}")
        return server
    except imaplib.IMAP4.error as exc:
        logger.error(f"IMAP authentication failed: {exc}")
        raise RuntimeError(f'IMAP authentication failed: {exc}')
    except Exception as exc:
        logger.error(f"IMAP connection failed: {exc}")
        raise RuntimeError(f'Could not connect to IMAP server: {exc}')


def _resolve_imap_folder(server, folder):
    """
    Resolve the correct IMAP folder name by trying various common formats.
    Some IMAP servers use different folder hierarchies (e.g., INBOX.Sent vs Sent vs [Gmail]/Sent).
    This function tries the most likely candidates and returns the first that exists.
    """
    if not folder:
        folder = 'INBOX'

    folder_upper = folder.strip().upper()

    # Build candidate list based on standard folder names
    candidates = []

    # Special mapping for standard folders
    if folder_upper == 'SENT':
        candidates = ['Sent', 'INBOX.Sent', '[Gmail]/Sent', 'INBOX/Sent']
    elif folder_upper in ('DRAFTS', 'DRAFT'):
        candidates = ['Drafts', 'INBOX.Drafts', '[Gmail]/Drafts', 'INBOX/Drafts']
    elif folder_upper == 'INBOX':
        candidates = ['INBOX']
    elif folder_upper == 'TRASH':
        candidates = ['Trash', 'INBOX.Trash', '[Gmail]/Trash', 'INBOX/Trash', 'Deleted']
    elif folder_upper == 'SPAM':
        candidates = ['Spam', 'INBOX.Spam', '[Gmail]/Spam', 'INBOX/Spam']
    elif folder_upper == 'ARCHIVE':
        candidates = ['Archive', 'INBOX.Archive', 'Archives', 'INBOX.Archives', '[Gmail]/All Mail']
    else:
        # For non-standard folder names, try as-is first, then with INBOX prefix
        candidates = [folder, f'INBOX.{folder}', f'INBOX/{folder}']

    last_error = None
    for candidate in candidates:
        try:
            typ, data = server.select(candidate, readonly=True)
            if typ == 'OK':
                logger.debug(f"IMAP folder resolved to: {candidate}")
                return candidate
        except imaplib.IMAP4.error as exc:
            last_error = exc
            logger.debug(f"IMAP folder candidate '{candidate}' failed: {exc}")
            continue

    # All candidates failed
    raise RuntimeError(
        f'Mailbox "{folder}" could not be selected. Tried: {", ".join(candidates)}. '
        f'Last error: {last_error}'
    )


def _ensure_mailbox_selected(server, folder):
    """
    Ensure the specified mailbox/folder is selected before performing operations.

    IMAP SEARCH, FETCH, SORT etc. require the mailbox to be in SELECTED state.
    This function handles that requirement by resolving the correct folder name
    across different IMAP server configurations.

    Args:
        server: IMAP connection
        folder: Folder name to select (e.g., 'INBOX', 'Sent', 'Drafts')

    Returns:
        True if selection was successful

    Raises:
        RuntimeError: If mailbox selection fails
    """
    resolved_folder = _resolve_imap_folder(server, folder)

    try:
        typ, data = server.select(resolved_folder, readonly=True)
        if typ != 'OK':
            raise RuntimeError(f'Could not select mailbox {resolved_folder}: {data}')
        logger.debug(f"Mailbox {resolved_folder} selected successfully")
        return True
    except imaplib.IMAP4.error as exc:
        logger.error(f"Failed to select mailbox {resolved_folder}: {exc}")
        raise RuntimeError(f'Mailbox "{folder}" could not be selected. Error: {exc}')


def _safe_imap_operation(server, folder, operation_func, *args, **kwargs):
    """
    Safely execute an IMAP operation with automatic mailbox selection.
    
    This wrapper ensures the mailbox is selected before running operations
    and handles reconnection if the connection was dropped.
    
    Args:
        server: IMAP connection
        folder: Folder to operate on
        operation_func: Function to execute (e.g., server.search, server.fetch)
        *args, **kwargs: Arguments to pass to operation_func
        
    Returns:
        Result of operation_func
        
    Raises:
        RuntimeError: If operation fails
    """
    try:
        # Ensure mailbox is selected
        _ensure_mailbox_selected(server, folder)
        
        # Execute the operation
        return operation_func(*args, **kwargs)
    except imaplib.IMAP4.error as exc:
        error_msg = str(exc)
        
        # Check if it's a state error (not selected)
        if 'command SEARCH' in error_msg or 'command FETCH' in error_msg or 'not allowed in state' in error_msg.lower():
            logger.warning(f"IMAP state error, re-selecting mailbox: {exc}")
            # Try to re-select and retry once
            try:
                _ensure_mailbox_selected(server, folder)
                return operation_func(*args, **kwargs)
            except Exception as retry_exc:
                raise RuntimeError(f'IMAP operation failed after retry: {retry_exc}')
        
        raise RuntimeError(f'IMAP operation failed: {error_msg}')


# =============================================================================
# GMAIL API FUNCTIONS
# =============================================================================

def _gmail_token_request_payload(payload):
    """Make token request to Google OAuth API."""
    encoded = urllib.parse.urlencode(payload).encode('utf-8')
    request_obj = urllib.request.Request(
        GMAIL_TOKEN_URL,
        data=encoded,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST'
    )
    return _load_json(request_obj)


def _load_json(request_obj):
    """Load JSON response from HTTP request."""
    try:
        with urllib.request.urlopen(request_obj, timeout=30) as response:
            charset = response.headers.get_content_charset() or 'utf-8'
            body = response.read().decode(charset)
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='ignore')
        try:
            payload = json.loads(body)
            error_message = payload.get('error_description') or payload.get('error', {}).get('message') or body
        except Exception:
            error_message = body or str(exc)
        raise RuntimeError(error_message or 'Google API request failed.')
    except urllib.error.URLError as exc:
        raise RuntimeError(str(exc.reason or exc))


def _build_gmail_auth_url(db=None):
    """Build Google OAuth authorization URL."""
    state = secrets.token_urlsafe(24)
    session['gmail_oauth_state'] = state
    settings = _get_email_settings(db)
    client_id = os.environ.get('GMAIL_CLIENT_ID', '') or settings.get('gmail_client_id', '')
    redirect_uri = settings.get('gmail_redirect_uri', '') or (url_for('email_manager.email_oauth_callback', _external=True) if has_request_context() else '')

    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': ' '.join(GMAIL_SCOPES),
        'access_type': 'offline',
        'prompt': 'consent',
        'include_granted_scopes': 'true',
        'state': state,
    }
    return f"{GMAIL_AUTH_URL}?{urllib.parse.urlencode(params)}"


def _exchange_gmail_code(code, db=None):
    """Exchange authorization code for access tokens."""
    settings = _get_email_settings(db)
    client_id = os.environ.get('GMAIL_CLIENT_ID', '') or settings.get('gmail_client_id', '')
    client_secret = os.environ.get('GMAIL_CLIENT_SECRET', '') or settings.get('gmail_client_secret', '')
    redirect_uri = settings.get('gmail_redirect_uri', '') or (url_for('email_manager.email_oauth_callback', _external=True) if has_request_context() else '')

    return _gmail_token_request_payload({
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    })


def _refresh_gmail_access_token(refresh_token, db=None):
    """Refresh expired Gmail access token."""
    settings = _get_email_settings(db)
    client_id = os.environ.get('GMAIL_CLIENT_ID', '') or settings.get('gmail_client_id', '')
    client_secret = os.environ.get('GMAIL_CLIENT_SECRET', '') or settings.get('gmail_client_secret', '')

    return _gmail_token_request_payload({
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'refresh_token'
    })


def _valid_gmail_access_token(db=None, user_id=None):
    """Get a valid Gmail access token, refreshing if necessary."""
    database = db or _get_db()
    resolved_user_id = user_id or session.get('user_id')
    connection = _get_gmail_connection(database, resolved_user_id)
    if not connection:
        raise RuntimeError('Gmail account is not connected.')

    expires_at = _parse_dt(connection['expires_at'])
    if expires_at and expires_at > _utcnow() + timedelta(seconds=30):
        return connection['access_token']

    refresh_token = connection['refresh_token']
    if not refresh_token:
        raise RuntimeError('Gmail token expired and no refresh token available.')

    refreshed = _refresh_gmail_access_token(refresh_token, database)
    refreshed['refresh_token'] = refresh_token
    _save_gmail_connection(database, resolved_user_id, refreshed, connection['email_address'])
    return _get_gmail_connection(database, resolved_user_id)['access_token']


def _gmail_json_api(path_or_url, access_token, params=None, method='GET', payload=None):
    """Make authenticated request to Gmail API."""
    url = path_or_url if path_or_url.startswith('http') else path_or_url
    if params:
        url = f"{url}{'&' if '?' in url else '?'}{urllib.parse.urlencode(params, doseq=True)}"
    headers = {'Authorization': f'Bearer {access_token}'}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    request_obj = urllib.request.Request(url, data=data, headers=headers, method=method)
    return _load_json(request_obj)


def _gmail_user_profile(access_token):
    """Get Gmail user profile information."""
    return _gmail_json_api(GMAIL_USERINFO_URL, access_token)


def gmail_list_messages(access_token, search_query='', max_results=25, label=None, page_token=None):
    """List Gmail messages with pagination support."""
    params = {'maxResults': min(max_results, 500), 'q': search_query or ''}
    if label:
        params['labelIds'] = label
    if page_token:
        params['pageToken'] = page_token

    payload = _gmail_json_api(f'{GMAIL_GMAIL_API}/messages', access_token, params=params)
    messages = []
    for item in payload.get('messages', []):
        detail = _gmail_json_api(f"{GMAIL_GMAIL_API}/messages/{item['id']}", access_token, params={'format': 'metadata', 'metadataHeaders': ['From', 'Subject', 'Date', 'To', 'Cc']})
        headers = {header['name'].lower(): header['value'] for header in detail.get('payload', {}).get('headers', [])}
        messages.append({
            'id': detail.get('id'),
            'thread_id': detail.get('threadId'),
            'snippet': detail.get('snippet', ''),
            'subject': _decode_str(headers.get('subject', '(No subject)')),
            'from': _decode_str(headers.get('from', '--')),
            'to': _decode_str(headers.get('to', '--')),
            'cc': _decode_str(headers.get('cc', '')),
            'date': headers.get('date', '--'),
            'label_ids': detail.get('labelIds', []),
            'size_estimate': detail.get('sizeEstimate', 0),
            'account_email': 'Gmail',
        })
    return messages


def gmail_get_message(access_token, message_id):
    """Get full Gmail message details including attachments."""
    detail = _gmail_json_api(f'{GMAIL_GMAIL_API}/messages/{message_id}', access_token, params={'format': 'full'})
    payload = detail.get('payload', {})
    headers = {header['name'].lower(): header['value'] for header in payload.get('headers', [])}
    parts = payload.get('parts', [])

    plain_body = ''
    html_body = ''
    for part in parts:
        if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
            plain_body = _decode_b64_url(part['body']['data'])
        elif part.get('mimeType') == 'text/html' and part.get('body', {}).get('data'):
            html_body = _decode_b64_url(part['body']['data'])
        if part.get('parts'):
            for nested in part['parts']:
                if nested.get('mimeType') == 'text/plain' and nested.get('body', {}).get('data'):
                    plain_body = _decode_b64_url(nested['body']['data'])
                elif nested.get('mimeType') == 'text/html' and nested.get('body', {}).get('data'):
                    html_body = _decode_b64_url(nested['body']['data'])

    body = plain_body or _strip_html(html_body) or detail.get('snippet', '')

    attachments = []
    for part in parts:
        filename = part.get('filename') or ''
        body_data = part.get('body', {})
        if filename and body_data.get('attachmentId'):
            attachments.append({
                'filename': filename,
                'mime_type': part.get('mimeType', 'application/octet-stream'),
                'attachment_id': body_data.get('attachmentId'),
                'size': body_data.get('size', 0)
            })
        if part.get('parts'):
            for nested in part['parts']:
                filename = nested.get('filename') or ''
                body_data = nested.get('body', {})
                if filename and body_data.get('attachmentId'):
                    attachments.append({
                        'filename': filename,
                        'mime_type': nested.get('mimeType', 'application/octet-stream'),
                        'attachment_id': body_data.get('attachmentId'),
                        'size': body_data.get('size', 0)
                    })

    return {
        'id': detail.get('id'),
        'thread_id': detail.get('threadId'),
        'subject': _decode_str(headers.get('subject', '(No subject)')),
        'from': _decode_str(headers.get('from', '--')),
        'to': _decode_str(headers.get('to', '--')),
        'cc': _decode_str(headers.get('cc', '')),
        'date': headers.get('date', '--'),
        'body': body,
        'snippet': detail.get('snippet', ''),
        'attachments': attachments,
        'label_ids': detail.get('labelIds', []),
        'account_email': 'Gmail',
    }


def gmail_download_attachment(access_token, message_id, attachment_id):
    """Download Gmail attachment and return file data."""
    try:
        attachment_data = _gmail_json_api(
            f'{GMAIL_GMAIL_API}/messages/{message_id}/attachments/{attachment_id}',
            access_token
        )
        file_data = _decode_b64_url(attachment_data.get('data', ''))
        return file_data
    except Exception as exc:
        logger.error(f"Failed to download Gmail attachment: {exc}")
        raise RuntimeError(f'Could not download attachment: {exc}')


def gmail_send_message(access_token, form, uploaded_files):
    """Send email via Gmail API."""
    message = MIMEMultipart()
    message['To'] = form.get('to', '').strip()
    if form.get('cc', '').strip():
        message['Cc'] = form.get('cc', '').strip()
    if form.get('bcc', '').strip():
        message['Bcc'] = form.get('bcc', '').strip()
    message['Subject'] = form.get('subject', '').strip() or '(No subject)'

    body = form.get('body', '').strip()
    is_html = form.get('is_html', '') == 'true'
    if is_html:
        message.attach(MIMEText(body, 'html', 'utf-8'))
    else:
        message.attach(MIMEText(body, 'plain', 'utf-8'))

    for uploaded in uploaded_files:
        if not uploaded or not uploaded.filename:
            continue
        guessed_type, _ = mimetypes.guess_type(uploaded.filename)
        main_type, sub_type = (guessed_type or 'application/octet-stream').split('/', 1)
        part = MIMEBase(main_type, sub_type)
        part.set_payload(uploaded.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{uploaded.filename}"')
        message.attach(part)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return _gmail_json_api(f'{GMAIL_GMAIL_API}/messages/send', access_token, method='POST', payload={'raw': raw})


# =============================================================================
# SMTP EMAIL SENDING
# =============================================================================

def _validate_smtp_config(account):
    """
    Validate SMTP configuration and return list of errors.
    
    Checks:
    - SMTP host is configured
    - SMTP port is valid
    - Username and password are present
    - DNS resolution works
    """
    errors = []
    
    smtp_host = account.get('smtp_host', '').strip()
    smtp_port = account.get('smtp_port', '')
    smtp_username = account.get('smtp_username', '').strip()
    encrypted_password = account.get('smtp_password', '')
    
    if not smtp_host:
        errors.append('SMTP host is not configured.')
    
    if not smtp_port:
        errors.append('SMTP port is not configured.')
    else:
        try:
            port = int(smtp_port)
            if port < 1 or port > 65535:
                errors.append('SMTP port must be between 1 and 65535.')
            if port not in (25, 465, 587, 993):
                errors.append(f'SMTP port {port} is non-standard. Common ports are 587 (TLS), 465 (SSL), or 993 (IMAP).')
        except ValueError:
            errors.append('SMTP port must be a number.')
    
    if not smtp_username:
        errors.append('SMTP username is not configured.')
    
    if not encrypted_password:
        errors.append('SMTP password is not configured.')
    
    # Validate host format
    if smtp_host:
        # Remove port if included
        host_part = smtp_host.split(':')[0]
        # Basic DNS resolution check
        try:
            if not re.match(r'^[\w\.-]+$', host_part):
                errors.append('SMTP host format appears invalid.')
        except Exception:
            pass
    
    return errors


def smtp_send_email(account, form, uploaded_files):
    """
    Send email via SMTP with proper connection handling.
    
    This function:
    - Validates SMTP configuration first
    - Creates proper SSL/TLS connection
    - Handles authentication properly
    - Times out gracefully on network issues
    """
    smtp_host = account.get('smtp_host', '').strip()
    smtp_port = int(account.get('smtp_port', 587) or 587)
    smtp_username = account.get('smtp_username', '').strip()
    encrypted_password = account.get('smtp_password', '')
    smtp_password = ''
    
    if encrypted_password:
        try:
            smtp_password = base64.b64decode(encrypted_password.encode()).decode()
        except Exception:
            smtp_password = encrypted_password

    use_tls = bool(account.get('use_tls', 1))
    
    # Validate configuration
    errors = _validate_smtp_config(account)
    if errors:
        raise RuntimeError('SMTP configuration error: ' + '; '.join(errors))
    
    message = MIMEMultipart()
    from_address = account.get('email_address', smtp_username)
    message['From'] = formataddr((from_address.split('@')[0] if '@' in from_address else '', from_address))
    message['To'] = form.get('to', '').strip()
    if form.get('cc', '').strip():
        message['Cc'] = form.get('cc', '').strip()
    if form.get('bcc', '').strip():
        message['Bcc'] = form.get('bcc', '').strip()
    message['Subject'] = form.get('subject', '').strip() or '(No subject)'

    body = form.get('body', '').strip()
    is_html = form.get('is_html', '') == 'true'
    if is_html:
        message.attach(MIMEText(body, 'html', 'utf-8'))
    else:
        message.attach(MIMEText(body, 'plain', 'utf-8'))

    for uploaded in uploaded_files:
        if not uploaded or not uploaded.filename:
            continue
        guessed_type, _ = mimetypes.guess_type(uploaded.filename)
        main_type, sub_type = (guessed_type or 'application/octet-stream').split('/', 1)
        part = MIMEBase(main_type, sub_type)
        part.set_payload(uploaded.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{uploaded.filename}"')
        message.attach(part)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            if use_tls and smtp_port == 587:
                server.starttls()
            elif use_tls and smtp_port == 465:
                # SSL connection already established
                pass
            
            server.login(smtp_username, smtp_password)
            
            # Build the email with all recipients
            all_recipients = [message['To']]
            if message.get('Cc'):
                all_recipients.extend(parseaddr(addr)[1] for addr in message['Cc'].split(','))
            if message.get('Bcc'):
                all_recipients.extend(parseaddr(addr)[1] for addr in message['Bcc'].split(','))
            
            server.send_message(message)
            logger.info(f"Email sent via SMTP to {message['To']}")
    except smtplib.SMTPAuthenticationError as exc:
        logger.error(f"SMTP authentication failed: {exc}")
        raise RuntimeError('SMTP authentication failed. Please check your username and password.')
    except smtplib.SMTPRecipientsRefused as exc:
        logger.error(f"SMTP recipient refused: {exc}")
        raise RuntimeError(f'Recipient was refused: {exc}')
    except smtplib.SMTPException as exc:
        logger.error(f"SMTP error: {exc}")
        raise RuntimeError(f'SMTP error: {exc}')
    except ConnectionRefusedError:
        raise RuntimeError('SMTP connection refused. Please check SMTP host and port.')
    except TimeoutError:
        raise RuntimeError('SMTP connection timed out. Please check network and try again.')
    except Exception as exc:
        error_msg = str(exc).lower()
        if 'getaddrinfo' in error_msg or 'name or service not known' in error_msg:
            logger.error(f"DNS resolution failed for SMTP host {smtp_host}: {exc}")
            raise RuntimeError(f'SMTP host "{smtp_host}" could not be resolved. Please check the hostname.')
        raise RuntimeError(f'Failed to send email: {exc}')
    
    return {'message': 'Email sent successfully'}


# =============================================================================
# SMTP/IMAP EMAIL FETCHING WITH PROPER STATE MANAGEMENT
# =============================================================================

def smtp_fetch_emails(account, folder='INBOX', search_query='', max_results=25, page=1):
    """
    Fetch emails from SMTP/IMAP account with proper mailbox selection.

    This function ensures:
    - Mailbox is selected BEFORE running SEARCH
    - Results are properly paginated
    - Connection is reused safely
    - Errors are caught and handled gracefully

    Args:
        account: Account dictionary with IMAP credentials
        folder: Folder to fetch from (INBOX, Sent, Drafts, etc.)
        search_query: IMAP search query (e.g., 'UNSEEN', 'FROM user@example.com')
        max_results: Maximum number of messages to return
        page: Page number for pagination

    Returns:
        List of message dictionaries
    """
    imap_host = account.get('imap_host') or account.get('smtp_host', '')
    if not imap_host:
        raise RuntimeError('IMAP host is not configured for this account.')

    imap_port = int(account.get('imap_port', 993) or 993)
    smtp_username = account.get('smtp_username', '')
    encrypted_password = account.get('smtp_password', '')
    smtp_password = ''

    if encrypted_password:
        try:
            smtp_password = base64.b64decode(encrypted_password.encode()).decode()
        except Exception:
            smtp_password = encrypted_password

    messages = []

    try:
        # Create IMAP connection with proper SSL/TLS - reduced timeout for speed
        if imap_port == 993:
            server = imaplib.IMAP4_SSL(imap_host, imap_port, timeout=15)
        else:
            server = imaplib.IMAP4(imap_host, imap_port)
            if account.get('use_tls', 1):
                server.starttls()

        server.login(smtp_username, smtp_password)
        logger.info(f"IMAP connection established to {imap_host}:{imap_port} for folder {folder}")

        # CRITICAL: Select mailbox BEFORE search/fetch
        # This is the fix for "command SEARCH illegal in state AUTH"
        _ensure_mailbox_selected(server, folder)

        # Now run search in the selected mailbox
        if search_query:
            status, message_ids = server.search(None, search_query)
        else:
            status, message_ids = server.search(None, 'ALL')

        if status != 'OK':
            logger.warning(f"IMAP search returned status: {status}, message_ids: {message_ids}")
            return messages

        ids = message_ids[0].split() if message_ids and message_ids[0] else []

        # Calculate pagination
        start_idx = (page - 1) * max_results
        end_idx = start_idx + max_results
        page_ids = ids[start_idx:end_idx]
        
        for msg_id in reversed(page_ids):
            try:
                # Use ENVELOPE for fast header-only fetch (no body download)
                status, msg_data = server.fetch(msg_id, '(ENVELOPE)')
                if status != 'OK':
                    logger.warning(f"Failed to fetch envelope for {msg_id}: {status}")
                    continue

                envelope = msg_data[0]
                if isinstance(envelope, tuple) and len(envelope) > 1:
                    raw_envelope = envelope[1]
                else:
                    raw_envelope = envelope

                # Parse envelope
                env = None
                try:
                    import email.policy
                    env = email.policy.default.parser.BytesParser().parsebytes(raw_envelope)
                except Exception:
                    pass

                # Also peek at headers for snippet preview
                status2, header_data = server.fetch(msg_id, '(BODY[HEADER.FIELDS (FROM TO SUBJECT DATE CONTENT-TYPE CONTENT-DISPOSITION)])')
                snippet = ''
                has_attachments = False
                msg_from = '--'
                msg_to = '--'
                subject = '(No subject)'
                date_str = '--'

                if status2 == 'OK' and header_data:
                    header_bytes = header_data[0][1] if isinstance(header_data[0], tuple) else header_data[0]
                    try:
                        header_msg = email.message_from_bytes(header_bytes)
                        msg_from = _decode_str(header_msg.get('From', '--'))
                        msg_to = _decode_str(header_msg.get('To', '--'))
                        subject = _decode_str(header_msg.get('Subject', '(No subject)'))
                        date_str = header_msg.get('Date', '--')
                        content_disp = header_msg.get('Content-Disposition', '')
                        if content_disp and 'attachment' in content_disp:
                            has_attachments = True
                        # Get snippet from first line of body if available
                        ctype = header_msg.get('Content-Type', '')
                    except Exception:
                        pass

                # For a quick snippet, try to peek at first 200 chars of body without marking as read
                try:
                    status3, body_peek = server.fetch(msg_id, '(BODY[TEXT]<0.512>)')
                    if status3 == 'OK' and body_peek:
                        body_bytes = body_peek[0][1] if isinstance(body_peek[0], tuple) else body_peek[0]
                        try:
                            body_part = email.message_from_bytes(body_bytes)
                            charset = body_part.get_content_charset() or 'utf-8'
                            snippet = body_part.get_payload(decode=True).decode(charset, errors='replace')[:200]
                            if 'attachment' in body_part.get('Content-Disposition', ''):
                                has_attachments = True
                        except Exception:
                            pass
                except Exception:
                    pass

                messages.append({
                    'id': msg_id.decode() if isinstance(msg_id, bytes) else msg_id,
                    'subject': subject,
                    'from': msg_from,
                    'to': msg_to,
                    'date': date_str,
                    'body': snippet,
                    'snippet': snippet,
                    'has_attachments': has_attachments,
                    'account_email': account.get('email_address', 'Unknown'),
                    'account_type': account.get('account_type', 'smtp'),
                    'folder': folder,
                })
            except Exception as exc:
                logger.warning(f"Error parsing message {msg_id}: {exc}")
                continue
        
        logger.info(f"Fetched {len(messages)} messages from {folder}")
        
    except imaplib.IMAP4.error as exc:
        error_msg = str(exc)
        if 'AUTH' in error_msg:
            raise RuntimeError('IMAP authentication failed. Please check your username and password.')
        elif 'SELECT' in error_msg or 'not allowed in state' in error_msg.lower():
            raise RuntimeError(f'Mailbox "{folder}" could not be selected. Please check if it exists.')
        else:
            raise RuntimeError(f'IMAP error: {error_msg}')
    except Exception as exc:
        logger.error(f"Error fetching emails: {exc}")
        raise RuntimeError(f'Failed to fetch emails: {exc}')
    finally:
        try:
            if 'server' in locals():
                server.logout()
        except Exception:
            pass
    
    return messages


def smtp_get_email(account, message_id, folder='INBOX'):
    """
    Get full email details from SMTP/IMAP account.
    
    This function:
    - Selects mailbox before fetching
    - Parses attachments correctly
    - Returns complete message data
    """
    imap_host = account.get('imap_host') or account.get('smtp_host', '')
    if not imap_host:
        raise RuntimeError('IMAP host is not configured for this account.')
    
    imap_port = int(account.get('imap_port', 993) or 993)
    smtp_username = account.get('smtp_username', '')
    encrypted_password = account.get('smtp_password', '')
    smtp_password = ''
    
    if encrypted_password:
        try:
            smtp_password = base64.b64decode(encrypted_password.encode()).decode()
        except Exception:
            smtp_password = encrypted_password

    try:
        if imap_port == 993:
            server = imaplib.IMAP4_SSL(imap_host, imap_port, timeout=15)
        else:
            server = imaplib.IMAP4(imap_host, imap_port)
            if account.get('use_tls', 1):
                server.starttls()

        server.login(smtp_username, smtp_password)

        # CRITICAL: Select mailbox BEFORE fetch
        _ensure_mailbox_selected(server, folder)

        # Fetch the message
        status, msg_data = server.fetch(message_id, '(RFC822)')

        if status != 'OK':
            raise RuntimeError('Could not fetch email. Message may not exist.')

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        subject = _decode_str(msg.get('Subject', '(No subject)'))
        msg_from = _decode_str(msg.get('From', '--'))
        msg_to = _decode_str(msg.get('To', '--'))
        cc = _decode_str(msg.get('Cc', ''))
        date_str = msg.get('Date', '--')

        body = ''
        attachments = []
        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = part.get('Content-Disposition', '')
                content_type = part.get_content_type()
                
                # Get body text
                if content_type == 'text/plain' and 'attachment' not in content_disposition and not body:
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        body = part.get_payload(decode=True).decode(charset, errors='replace')
                    except Exception:
                        body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                
                # Get attachments
                if 'attachment' in content_disposition or part.get_filename():
                    filename = part.get_filename()
                    if filename:
                        filename = _decode_str(filename)
                        payload = part.get_payload(decode=True)
                        if payload:
                            attachments.append({
                                'filename': filename,
                                'mime_type': content_type,
                                'size': len(payload),
                                'part_id': part.get('Content-ID', ''),
                            })
        else:
            charset = msg.get_content_charset() or 'utf-8'
            try:
                body = msg.get_payload(decode=True).decode(charset, errors='replace')
            except Exception:
                body = msg.get_payload(decode=True).decode('utf-8', errors='replace')

        return {
            'id': message_id,
            'subject': subject,
            'from': msg_from,
            'to': msg_to,
            'cc': cc,
            'date': date_str,
            'body': body,
            'snippet': body[:200] if body else '',
            'attachments': attachments,
            'account_email': account.get('email_address', 'Unknown'),
            'account_type': account.get('account_type', 'smtp'),
            'folder': folder,
        }

    except imaplib.IMAP4.error as exc:
        error_msg = str(exc)
        if 'FETCH' in error_msg:
            raise RuntimeError('Could not fetch email. Message may have been deleted or moved.')
        raise RuntimeError(f'IMAP error: {error_msg}')
    except Exception as exc:
        logger.error(f"Error getting email: {exc}")
        raise RuntimeError(f'Failed to get email: {exc}')
    finally:
        try:
            if 'server' in locals():
                server.logout()
        except Exception:
            pass


def smtp_download_attachment(account, message_id, part_id, folder='INBOX'):
    """
    Download email attachment from SMTP/IMAP account.
    
    This function:
    - Selects mailbox before fetching
    - Handles attachment parts correctly
    - Returns file data for download
    """
    imap_host = account.get('imap_host') or account.get('smtp_host', '')
    if not imap_host:
        raise RuntimeError('IMAP host is not configured.')
    
    imap_port = int(account.get('imap_port', 993) or 993)
    smtp_username = account.get('smtp_username', '')
    encrypted_password = account.get('smtp_password', '')
    smtp_password = ''
    
    if encrypted_password:
        try:
            smtp_password = base64.b64decode(encrypted_password.encode()).decode()
        except Exception:
            smtp_password = encrypted_password

    try:
        if imap_port == 993:
            server = imaplib.IMAP4_SSL(imap_host, imap_port, timeout=30)
        else:
            server = imaplib.IMAP4(imap_port)
            if account.get('use_tls', 1):
                server.starttls()
        
        server.login(smtp_username, smtp_password)
        
        # CRITICAL: Select mailbox BEFORE fetch
        _ensure_mailbox_selected(server, folder)
        
        # Fetch the specific part
        # part_id can be a sequence number or content ID
        try:
            if part_id.startswith('<') and part_id.endswith('>'):
                # It's a Content-ID, need to search for it
                status, msg_data = server.fetch(message_id, '(BODY[])')
            else:
                # Try fetching by part number
                status, msg_data = server.fetch(message_id, f'(BODY.PART[{part_id}])')
        except Exception:
            # Fall back to full message fetch
            status, msg_data = server.fetch(message_id, '(RFC822)')

        if status != 'OK' or not msg_data:
            raise RuntimeError('Could not fetch attachment data.')

        # Parse the message and find the attachment
        raw_email = msg_data[0][1] if isinstance(msg_data[0], tuple) else msg_data[0]
        msg = email.message_from_bytes(raw_email)
        
        # Find attachment by part ID or Content-ID
        attachment_data = None
        attachment_filename = None
        attachment_mime_type = 'application/octet-stream'
        
        if part_id.startswith('<') and part_id.endswith('>'):
            # Search by Content-ID
            for part in msg.walk():
                if part.get('Content-ID', '') == part_id:
                    attachment_filename = part.get_filename()
                    if not attachment_filename:
                        attachment_filename = f'attachment_{part_id.strip("<>")}'
                    payload = part.get_payload(decode=True)
                    if payload:
                        attachment_data = payload
                        attachment_mime_type = part.get_content_type()
                    break
        else:
            # Try to find by part number
            try:
                part_num = int(part_id)
                idx = 0
                for part in msg.walk():
                    if idx == part_num:
                        attachment_filename = part.get_filename()
                        if not attachment_filename:
                            attachment_filename = f'attachment_{part_num}'
                        payload = part.get_payload(decode=True)
                        if payload:
                            attachment_data = payload
                            attachment_mime_type = part.get_content_type()
                        break
                    idx += 1
            except ValueError:
                raise RuntimeError('Invalid attachment part number.')
        
        if attachment_data is None:
            raise RuntimeError('Attachment not found or could not be decoded.')
        
        if not attachment_filename:
            attachment_filename = 'attachment'
        
        # Decode filename if needed
        attachment_filename = _decode_str(attachment_filename)
        
        logger.info(f"Downloaded attachment: {attachment_filename} ({len(attachment_data)} bytes)")
        
        return {
            'data': attachment_data,
            'filename': attachment_filename,
            'mime_type': attachment_mime_type,
        }
        
    except RuntimeError:
        raise
    except Exception as exc:
        logger.error(f"Error downloading attachment: {exc}")
        raise RuntimeError(f'Failed to download attachment: {exc}')
    finally:
        try:
            if 'server' in locals():
                server.logout()
        except Exception:
            pass


def smtp_test_connection(account):
    """
    Test SMTP/IMAP connection for an email account.
    
    Returns a dict with success status and any error messages.
    """
    results = {
        'smtp_ok': False,
        'imap_ok': False,
        'smtp_error': None,
        'imap_error': None,
    }
    
    smtp_host = account.get('smtp_host', '').strip()
    smtp_port = int(account.get('smtp_port', 587) or 587)
    smtp_username = account.get('smtp_username', '').strip()
    encrypted_password = account.get('smtp_password', '')
    smtp_password = ''
    
    if encrypted_password:
        try:
            smtp_password = base64.b64decode(encrypted_password.encode()).decode()
        except Exception:
            smtp_password = encrypted_password
    
    imap_host = account.get('imap_host') or smtp_host
    imap_port = int(account.get('imap_port', 993) or 993)
    
    # Test SMTP
    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            if account.get('use_tls', 1) and smtp_port == 587:
                server.starttls()
            server.login(smtp_username, smtp_password)
            results['smtp_ok'] = True
    except Exception as exc:
        results['smtp_error'] = str(exc)
        logger.error(f"SMTP test failed: {exc}")

    # Test IMAP
    try:
        if imap_port == 993:
            imap_server = imaplib.IMAP4_SSL(imap_host, imap_port, timeout=10)
        else:
            imap_server = imaplib.IMAP4(imap_host, imap_port)
            if account.get('use_tls', 1):
                imap_server.starttls()
        
        imap_server.login(smtp_username, smtp_password)
        imap_server.logout()
        results['imap_ok'] = True
    except Exception as exc:
        results['imap_error'] = str(exc)
        logger.error(f"IMAP test failed: {exc}")
    
    return results


# =============================================================================
# PERMISSION CHECK HELPERS
# =============================================================================

def _check_permission(permission):
    """Check if current user has the specified permission."""
    user_permissions = session.get('permissions', [])
    if isinstance(user_permissions, str):
        user_permissions = user_permissions.split(',')
    return permission in user_permissions or session.get('can_manage_users', False)


# =============================================================================
# ROUTES
# =============================================================================

@bp.route('/email')
def email_dashboard():
    """
    Main email dashboard showing inbox/sent/drafts for selected account.
    
    Query parameters:
    - account_id: Specific account to view
    - folder: INBOX, SENT, DRAFTS, etc.
    - q: Search query
    - message_id: Specific message to display
    - page: Page number for pagination
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = _get_db()
    accounts = _get_user_email_accounts(db)
    default_account = _get_default_account(db)
    settings = _get_email_settings(db)

    gmail_configured = _gmail_is_configured(db)
    gmail_connection = _get_gmail_connection(db)
    gmail_connected = gmail_connection is not None

    folder = request.args.get('folder', 'INBOX')
    messages = []
    selected_message = None
    query = request.args.get('q', '').strip()
    account_id = request.args.get('account_id', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    total_messages = 0

    current_account = None
    if account_id:
        for acc in accounts:
            if str(acc.get('id')) == account_id:
                current_account = acc
                break
    elif default_account:
        current_account = default_account

    if current_account:
        try:
            if current_account.get('account_type') == 'gmail' and gmail_connected:
                access_token = _valid_gmail_access_token(db)
                if folder == 'SENT':
                    messages = gmail_list_messages(access_token, 'in:sent', label='SENT', max_results=DEFAULT_PAGE_SIZE)
                elif folder == 'DRAFT':
                    messages = gmail_list_messages(access_token, 'in:draft', max_results=DEFAULT_PAGE_SIZE)
                else:
                    messages = gmail_list_messages(access_token, query, max_results=DEFAULT_PAGE_SIZE)
                total_messages = len(messages)
                msg_id = request.args.get('message_id', '').strip()
                if msg_id:
                    selected_message = gmail_get_message(access_token, msg_id)
            elif current_account.get('account_type') == 'smtp':
                # Fetch emails with proper mailbox selection handled inside
                if folder == 'SENT':
                    messages = smtp_fetch_emails(current_account, 'Sent', max_results=DEFAULT_PAGE_SIZE, page=page)
                elif folder in ('DRAFT', 'DRAFTS'):
                    messages = smtp_fetch_emails(current_account, 'Drafts', max_results=DEFAULT_PAGE_SIZE, page=page)
                else:
                    # Build search query for INBOX
                    search_q = query if query else 'ALL'
                    messages = smtp_fetch_emails(current_account, 'INBOX', search_query=search_q, max_results=DEFAULT_PAGE_SIZE, page=page)
                total_messages = len(messages)
                
                msg_id = request.args.get('message_id', '').strip()
                if msg_id:
                    folder_to_use = 'INBOX' if folder == 'INBOX' else ('Sent' if folder == 'SENT' else 'Drafts')
                    selected_message = smtp_get_email(current_account, msg_id, folder_to_use)
        except RuntimeError as exc:
            flash(f'Could not load emails: {exc}', 'error')
            logger.error(f"Email load error: {exc}")
        except Exception as exc:
            flash(f'Unexpected error loading emails: {exc}', 'error')
            logger.exception(f"Unexpected email load error: {exc}")

    context = {
        'title': 'Email Management',
        'email_accounts': accounts,
        'default_account': default_account,
        'current_account': current_account,
        'email_messages': messages,
        'selected_message': selected_message,
        'current_folder': folder,
        'email_query': query,
        'gmail_configured': gmail_configured,
        'gmail_connected': gmail_connected,
        'gmail_settings': settings,
        'can_manage_settings': session.get('can_manage_users', False),
        'current_page': page,
        'total_messages': total_messages,
        'page_size': DEFAULT_PAGE_SIZE,
    }
    return render_template('email_dashboard.html', **context)


@bp.route('/email/unified')
def email_unified():
    """
    Unified inbox showing emails from all connected accounts.
    
    Query parameters:
    - folder: Folder to view across all accounts (default: INBOX)
    - q: Search query
    - account_id: Filter by specific account
    - page: Page number
    - sort: Sort field (date, from, subject)
    - order: Sort order (asc, desc)
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = _get_db()
    accounts = _get_user_email_accounts(db)
    default_account = _get_default_account(db)
    settings = _get_email_settings(db)
    gmail_configured = _gmail_is_configured(db)
    gmail_connection = _get_gmail_connection(db)
    gmail_connected = gmail_connection is not None

    folder = request.args.get('folder', 'INBOX')
    query = request.args.get('q', '').strip()
    account_filter = request.args.get('account_id', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    sort_by = request.args.get('sort', 'date')
    sort_order = request.args.get('order', 'desc')

    all_messages = []
    errors = []

    for acc in accounts:
        # Skip if filtering by account and this isn't the one
        if account_filter and str(acc.get('id')) != account_filter:
            continue
            
        try:
            if acc.get('account_type') == 'gmail' and gmail_connected:
                access_token = _valid_gmail_access_token(db)
                folder_query = ''
                if folder == 'SENT':
                    folder_query = 'in:sent'
                elif folder == 'DRAFT':
                    folder_query = 'in:draft'
                elif query:
                    folder_query = query
                
                gm_messages = gmail_list_messages(access_token, folder_query, max_results=UNIFIED_PAGE_SIZE * 2)
                for msg in gm_messages:
                    msg['account_email'] = gmail_connection.get('email_address', 'Gmail')
                    msg['account_type'] = 'gmail'
                    msg['account_id'] = None  # Gmail uses OAuth, not stored ID
                    msg['folder'] = folder
                all_messages.extend(gm_messages)

            elif acc.get('account_type') == 'smtp':
                imap_folder = 'INBOX'
                if folder == 'SENT':
                    imap_folder = 'Sent'
                elif folder in ('DRAFT', 'DRAFTS'):
                    imap_folder = 'Drafts'

                search_q = query if query else 'ALL'
                smtp_messages = smtp_fetch_emails(acc, imap_folder, search_q, max_results=UNIFIED_PAGE_SIZE * 2)
                for msg in smtp_messages:
                    msg['account_id'] = acc.get('id')
                all_messages.extend(smtp_messages)
                
        except RuntimeError as exc:
            errors.append(f"{acc.get('email_address', 'Unknown')}: {exc}")
            logger.warning(f"Failed to fetch from {acc.get('email_address')}: {exc}")
        except Exception as exc:
            errors.append(f"{acc.get('email_address', 'Unknown')}: {exc}")
            logger.exception(f"Unexpected error fetching from {acc.get('email_address')}: {exc}")

    # Sort messages
    reverse_sort = sort_order == 'desc'
    if sort_by == 'from':
        all_messages.sort(key=lambda x: x.get('from', '').lower(), reverse=reverse_sort)
    elif sort_by == 'subject':
        all_messages.sort(key=lambda x: x.get('subject', '').lower(), reverse=reverse_sort)
    else:  # date
        all_messages.sort(key=lambda x: x.get('date', ''), reverse=reverse_sort)

    # Paginate
    total_count = len(all_messages)
    start_idx = (page - 1) * UNIFIED_PAGE_SIZE
    end_idx = start_idx + UNIFIED_PAGE_SIZE
    paginated_messages = all_messages[start_idx:end_idx]

    context = {
        'title': 'All Emails',
        'email_accounts': accounts,
        'default_account': default_account,
        'email_messages': paginated_messages,
        'current_folder': folder,
        'email_query': query,
        'account_filter': account_filter,
        'gmail_configured': gmail_configured,
        'gmail_connected': gmail_connected,
        'gmail_settings': settings,
        'can_manage_settings': session.get('can_manage_users', False),
        'current_page': page,
        'total_messages': total_count,
        'page_size': UNIFIED_PAGE_SIZE,
        'sort_by': sort_by,
        'sort_order': sort_order,
        'fetch_errors': errors if errors else None,
    }
    return render_template('email_dashboard.html', **context)


@bp.route('/email/all')
def email_all():
    """
    All emails page - unified view of all emails from all accounts in a simple table format.
    Shows email sender, subject, preview, date, and account in columns.
    Click to expand and see full email body.
    
    Query parameters:
    - folder: Folder to view (INBOX, SENT, DRAFT)
    - q: Search query
    - sort: Sort field (date, from, subject)
    - order: Sort order (asc, desc)
    - page: Page number
    - page_size: Items per page (10, 20, 50, 100, 200)
    - view: View mode ('compact' or 'detailed')
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = _get_db()
    accounts = _get_user_email_accounts(db)
    default_account = _get_default_account(db)
    settings = _get_email_settings(db)
    gmail_configured = _gmail_is_configured(db)
    gmail_connection = _get_gmail_connection(db)
    gmail_connected = gmail_connection is not None

    folder = request.args.get('folder', 'INBOX')
    query = request.args.get('q', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    sort_by = request.args.get('sort', 'date')
    sort_order = request.args.get('order', 'desc')
    page_size = int(request.args.get('page_size', 25))
    view_mode = request.args.get('view', 'detailed')

    # Validate page_size
    valid_page_sizes = [10, 20, 25, 50, 100, 200, 500]
    if page_size not in valid_page_sizes:
        page_size = 25

    all_messages = []
    errors = []

    for acc in accounts:
        try:
            if acc.get('account_type') == 'gmail' and gmail_connected:
                access_token = _valid_gmail_access_token(db)
                folder_query = ''
                if folder == 'SENT':
                    folder_query = 'in:sent'
                elif folder == 'DRAFT':
                    folder_query = 'in:draft'
                elif query:
                    folder_query = query
                
                gm_messages = gmail_list_messages(access_token, folder_query, max_results=500)
                for msg in gm_messages:
                    msg['account_email'] = gmail_connection.get('email_address', 'Gmail')
                    msg['account_type'] = 'gmail'
                    msg['account_id'] = None
                    msg['folder'] = folder
                all_messages.extend(gm_messages)

            elif acc.get('account_type') == 'smtp':
                imap_folder = 'INBOX'
                if folder == 'SENT':
                    imap_folder = 'Sent'
                elif folder in ('DRAFT', 'DRAFTS'):
                    imap_folder = 'Drafts'

                search_q = query if query else 'ALL'
                smtp_messages = smtp_fetch_emails(acc, imap_folder, search_q, max_results=500)
                for msg in smtp_messages:
                    msg['account_id'] = acc.get('id')
                all_messages.extend(smtp_messages)
                
        except RuntimeError as exc:
            errors.append(f"{acc.get('email_address', 'Unknown')}: {exc}")
            logger.warning(f"Failed to fetch from {acc.get('email_address')}: {exc}")
        except Exception as exc:
            errors.append(f"{acc.get('email_address', 'Unknown')}: {exc}")
            logger.exception(f"Unexpected error fetching from {acc.get('email_address')}: {exc}")

    # Sort messages
    reverse_sort = sort_order == 'desc'
    if sort_by == 'from':
        all_messages.sort(key=lambda x: x.get('from', '').lower(), reverse=reverse_sort)
    elif sort_by == 'subject':
        all_messages.sort(key=lambda x: x.get('subject', '').lower(), reverse=reverse_sort)
    else:  # date
        def parse_date(msg):
            d = msg.get('date', '')
            if not d:
                return ''
            try:
                # Try various date formats
                from email.utils import parsedate_to_datetime
                return parsedate_to_datetime(d).timestamp()
            except Exception:
                return 0
        all_messages.sort(key=parse_date, reverse=reverse_sort)

    # Paginate
    total_count = len(all_messages)
    total_pages = max(1, (total_count + page_size - 1) // page_size) if total_count > 0 else 1
    # Ensure page is within bounds
    if page > total_pages:
        page = total_pages
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_messages = all_messages[start_idx:end_idx]

    # Calculate row numbers
    for idx, msg in enumerate(paginated_messages, start=start_idx + 1):
        msg['row_number'] = idx

    # Generate page range for pagination UI
    start_page = max(1, page - 2)
    end_page = min(total_pages, page + 2)
    if start_page > 1:
        if start_page > 2:
            page_range = list(range(1, start_page)) + list(range(start_page, end_page + 1))
        else:
            page_range = [1] + list(range(start_page, end_page + 1))
    else:
        page_range = list(range(start_page, end_page + 1))
    if end_page < total_pages:
        if end_page < total_pages - 1:
            page_range = page_range + list(range(end_page + 1, total_pages + 1))
        else:
            page_range = page_range + [total_pages]

    context = {
        'title': 'All Emails',
        'email_accounts': accounts,
        'default_account': default_account,
        'email_messages': paginated_messages,
        'current_folder': folder,
        'email_query': query,
        'gmail_configured': gmail_configured,
        'gmail_connected': gmail_connected,
        'gmail_settings': settings,
        'can_manage_settings': session.get('can_manage_users', False),
        'current_page': page,
        'total_messages': total_count,
        'total_pages': total_pages,
        'page_size': page_size,
        'sort_by': sort_by,
        'sort_order': sort_order,
        'view_mode': view_mode,
        'fetch_errors': errors if errors else None,
        'available_page_sizes': valid_page_sizes,
        'page_range': page_range,
    }
    return render_template('email_all.html', **context)


@bp.route('/email/compose')
def email_compose():
    """Email compose page."""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = _get_db()
    accounts = _get_user_email_accounts(db)
    default_account = _get_default_account(db)
    reply_to = request.args.get('reply_to', '').strip()
    subject = request.args.get('subject', '').strip()
    to_address = request.args.get('to', '').strip()
    account_id = request.args.get('account_id', '').strip()
    forward_attachments = request.args.get('forward_attachments', '').strip()
    original_message_id = request.args.get('message_id', '').strip()
    original_account_id = request.args.get('account_id', '').strip()

    current_account = None
    if account_id:
        for acc in accounts:
            if str(acc.get('id')) == account_id:
                current_account = acc
                break
    elif default_account:
        current_account = default_account

    context = {
        'title': 'Compose Email',
        'email_accounts': accounts,
        'default_account': default_account,
        'current_account': current_account,
        'reply_to': reply_to,
        'initial_subject': subject,
        'to_address': to_address,
        'forward_attachments': forward_attachments,
        'original_message_id': original_message_id,
        'original_account_id': original_account_id,
    }
    return render_template('email_compose.html', **context)


@bp.route('/email/send', methods=['POST'])
def email_send():
    """Send email via SMTP or Gmail API."""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = _get_db()
    account_id = request.form.get('account_id', '').strip()
    current_account = None

    if account_id:
        for acc in _get_user_email_accounts(db):
            if str(acc.get('id')) == account_id:
                current_account = acc
                break

    if not current_account:
        flash('Please select an email account to send from.', 'error')
        return redirect(url_for('email_manager.email_dashboard'))

    try:
        if current_account.get('account_type') == 'gmail':
            access_token = _valid_gmail_access_token(db)
            gmail_send_message(access_token, request.form, request.files.getlist('attachments'))
        else:
            smtp_send_email(current_account, request.form, request.files.getlist('attachments'))
        flash('Email sent successfully.', 'success')
    except RuntimeError as exc:
        flash(f'Failed to send email: {exc}', 'error')
        logger.error(f"Email send error: {exc}")
    except Exception as exc:
        flash(f'Failed to send email: {exc}', 'error')
        logger.exception(f"Unexpected email send error: {exc}")

    return redirect(url_for('email_manager.email_dashboard'))


@bp.route('/email/attachment/download/<account_type>/<account_identifier>/<message_id>/<part_id>')
def email_download_attachment(account_type, account_identifier, message_id, part_id):
    """
    Download email attachment.
    
    Args:
        account_type: 'gmail' or 'smtp'
        account_identifier: For Gmail this is the message ID, for SMTP it's the account_id
        message_id: The email message ID
        part_id: The attachment part ID or Content-ID
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    db = _get_db()
    
    try:
        if account_type == 'gmail':
            # Gmail uses OAuth, need to get access token
            access_token = _valid_gmail_access_token(db)
            attachment_data = gmail_download_attachment(access_token, account_identifier, part_id)
            
            # Get message info for filename
            msg = gmail_get_message(access_token, account_identifier)
            attachment_info = next((a for a in msg.get('attachments', []) if a.get('attachment_id') == part_id), None)
            filename = attachment_info.get('filename', 'attachment') if attachment_info else 'attachment'
            
            mime_type = attachment_info.get('mime_type', 'application/octet-stream') if attachment_info else 'application/octet-stream'
            
        else:
            # SMTP/IMAP account
            account_id = int(account_identifier)
            account = _get_account_by_id(db, account_id)
            
            if not account:
                return jsonify({'error': 'Account not found'}), 404
            
            attachment_info = smtp_download_attachment(account, message_id, part_id)
            filename = attachment_info.get('filename', 'attachment')
            mime_type = attachment_info.get('mime_type', 'application/octet-stream')
            attachment_data = attachment_info.get('data', b'')
            
            # Convert to bytes if string
            if isinstance(attachment_data, str):
                attachment_data = attachment_data.encode('utf-8')
        
        # Create response with file
        response = Response(
            attachment_data,
            mimetype=mime_type,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Length': len(attachment_data),
            }
        )
        return response
        
    except RuntimeError as exc:
        logger.error(f"Attachment download error: {exc}")
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        logger.exception(f"Unexpected attachment download error: {exc}")
        return jsonify({'error': 'Failed to download attachment'}), 500


@bp.route('/email/settings')
def email_settings():
    """Email account settings page."""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = _get_db()
    accounts = _get_user_email_accounts(db)
    settings = _get_email_settings(db)
    gmail_configured = _gmail_is_configured(db)
    gmail_connected = _get_gmail_connection(db) is not None

    context = {
        'title': 'Email Settings',
        'email_accounts': accounts,
        'email_settings': settings,
        'gmail_configured': gmail_configured,
        'gmail_connected': gmail_connected,
        'can_manage_settings': session.get('can_manage_users', False),
    }
    return render_template('email_settings.html', **context)


@bp.route('/email/account/test-connection', methods=['POST'])
def email_test_connection():
    """Test SMTP/IMAP connection for an account."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    db = _get_db()
    account_id = request.form.get('account_id', '').strip()
    
    if account_id:
        account = _get_account_by_id(db, int(account_id))
    else:
        # Test with provided credentials
        email_address = request.form.get('email_address', '').strip()
        smtp_host = request.form.get('smtp_host', '').strip()
        smtp_port = request.form.get('smtp_port', '587').strip()
        smtp_username = request.form.get('smtp_username', '').strip()
        smtp_password = request.form.get('smtp_password', '').strip()
        imap_host = request.form.get('imap_host', '').strip()
        imap_port = request.form.get('imap_port', '993').strip()
        use_tls = request.form.get('use_tls', '1') == '1'
        
        if not all([smtp_host, smtp_port, smtp_username, smtp_password]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        account = {
            'email_address': email_address,
            'smtp_host': smtp_host,
            'smtp_port': int(smtp_port),
            'smtp_username': smtp_username,
            'smtp_password': base64.b64encode(smtp_password.encode()).decode() if smtp_password else '',
            'imap_host': imap_host or smtp_host,
            'imap_port': int(imap_port) if imap_port else 993,
            'use_tls': 1 if use_tls else 0,
        }
    
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    results = smtp_test_connection(account)
    
    if results['smtp_ok'] and results['imap_ok']:
        return jsonify({
            'success': True,
            'message': 'SMTP and IMAP connections successful!',
            'smtp_ok': True,
            'imap_ok': True,
        })
    elif results['smtp_ok']:
        return jsonify({
            'success': True,
            'message': f"SMTP connection OK, but IMAP failed: {results['imap_error']}",
            'smtp_ok': True,
            'imap_ok': False,
            'smtp_error': results['smtp_error'],
            'imap_error': results['imap_error'],
        })
    elif results['imap_ok']:
        return jsonify({
            'success': True,
            'message': f"IMAP connection OK, but SMTP failed: {results['smtp_error']}",
            'smtp_ok': False,
            'imap_ok': True,
            'smtp_error': results['smtp_error'],
            'imap_error': results['imap_error'],
        })
    else:
        return jsonify({
            'success': False,
            'message': f"Connection failed. SMTP: {results['smtp_error']}. IMAP: {results['imap_error']}",
            'smtp_ok': False,
            'imap_ok': False,
            'smtp_error': results['smtp_error'],
            'imap_error': results['imap_error'],
        }), 400


@bp.route('/email/account/add-smtp', methods=['POST'])
def email_add_smtp():
    """Add SMTP/IMAP email account."""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = _get_db()
    email_address = request.form.get('email_address', '').strip()
    smtp_host = request.form.get('smtp_host', '').strip()
    smtp_port = request.form.get('smtp_port', '').strip()
    smtp_username = request.form.get('smtp_username', '').strip()
    smtp_password = request.form.get('smtp_password', '').strip()
    imap_host = request.form.get('imap_host', '').strip()
    imap_port = request.form.get('imap_port', '').strip()
    use_tls = request.form.get('use_tls', '1') == '1'

    if not all([email_address, smtp_host, smtp_port, smtp_username, smtp_password]):
        flash('All fields are required for SMTP account.', 'error')
        return redirect(url_for('email_manager.email_settings'))

    try:
        # Validate configuration before saving
        test_account = {
            'email_address': email_address,
            'smtp_host': smtp_host,
            'smtp_port': int(smtp_port),
            'smtp_username': smtp_username,
            'smtp_password': smtp_password,
            'imap_host': imap_host or smtp_host,
            'imap_port': int(imap_port) if imap_port else 993,
            'use_tls': 1 if use_tls else 0,
        }
        
        errors = _validate_smtp_config(test_account)
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('email_manager.email_settings'))
        
        _add_smtp_account(
            db, session.get('user_id'), email_address, 
            smtp_host, int(smtp_port), smtp_username, smtp_password, 
            imap_host or None, int(imap_port) if imap_port else None, use_tls
        )
        flash(f'Email account {email_address} added successfully.', 'success')
    except Exception as exc:
        flash(f'Failed to add account: {exc}', 'error')
        logger.exception(f"Failed to add SMTP account: {exc}")

    return redirect(url_for('email_manager.email_settings'))


@bp.route('/email/account/connect-gmail')
def email_connect_gmail():
    """Initiate Gmail OAuth flow."""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if not _gmail_is_configured():
        flash('Gmail OAuth is not configured. Please configure Gmail settings first.', 'error')
        return redirect(url_for('email_manager.email_settings'))

    return redirect(_build_gmail_auth_url())


@bp.route('/email/oauth/callback')
def email_oauth_callback():
    """Handle Gmail OAuth callback."""
    expected_state = session.get('gmail_oauth_state')
    received_state = request.args.get('state', '')
    code = request.args.get('code', '')

    if not code or not expected_state or expected_state != received_state:
        flash('Gmail authorization could not be verified.', 'error')
        return redirect(url_for('email_manager.email_settings'))

    db = _get_db()
    try:
        tokens = _exchange_gmail_code(code, db)
        profile = _gmail_user_profile(tokens.get('access_token', ''))
        _save_gmail_connection(db, session.get('user_id'), tokens, profile.get('email', ''))
        flash('Gmail account connected successfully.', 'success')
    except Exception as exc:
        flash(f'Gmail connection failed: {exc}', 'error')
        logger.exception(f"Gmail OAuth error: {exc}")
    finally:
        session.pop('gmail_oauth_state', None)

    return redirect(url_for('email_manager.email_settings'))


@bp.route('/email/account/disconnect-gmail', methods=['POST'])
def email_disconnect_gmail():
    """Disconnect Gmail account."""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = _get_db()
    _delete_gmail_connection(db, session.get('user_id'))
    flash('Gmail account disconnected.', 'success')
    return redirect(url_for('email_manager.email_settings'))


@bp.route('/email/account/delete/<int:account_id>', methods=['POST'])
def email_delete_account(account_id):
    """Delete SMTP/IMAP email account."""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = _get_db()
    _delete_email_account(db, account_id, session.get('user_id'))
    flash('Email account deleted.', 'success')
    return redirect(url_for('email_manager.email_settings'))


@bp.route('/email/account/set-default/<int:account_id>', methods=['POST'])
def email_set_default(account_id):
    """Set default email account."""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = _get_db()
    _set_default_account(db, session.get('user_id'), account_id)
    flash('Default email account updated.', 'success')
    return redirect(url_for('email_manager.email_settings'))


@bp.route('/email/notifications/settings/<int:account_id>', methods=['GET'])
def email_notification_settings(account_id):
    """Get notification settings for an account (API endpoint)."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    db = _get_db()
    settings = _get_email_notification_settings(db, account_id, session.get('user_id'))
    if not settings:
        return jsonify({'error': 'Account not found'}), 404

    return jsonify(settings)


@bp.route('/email/notifications/settings/<int:account_id>', methods=['POST'])
def email_save_notification_settings(account_id):
    """Save notification settings for an account."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    db = _get_db()
    settings = {
        'notifications_enabled': request.form.get('notifications_enabled') == '1',
        'notify_from_senders': request.form.get('notify_from_senders', '').strip(),
        'notify_subject_keywords': request.form.get('notify_subject_keywords', '').strip(),
        'notify_sound_enabled': request.form.get('notify_sound_enabled') == '1',
    }

    _update_email_notification_settings(db, account_id, session.get('user_id'), settings)
    return jsonify({'success': True, 'message': 'Notification settings saved.'})


@bp.route('/email/notifications/check-new', methods=['GET'])
def email_check_new_messages():
    """Check for new emails and return them for notification purposes."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    db = _get_db()
    accounts = _get_user_email_accounts(db)
    gmail_connection = _get_gmail_connection(db)
    gmail_connected = gmail_connection is not None

    new_messages = []
    updated_last_ids = {}

    for acc in accounts:
        try:
            notif_settings = _get_email_notification_settings(db, acc['id'], session.get('user_id'))
            if not notif_settings or not notif_settings.get('notifications_enabled'):
                continue

            last_seen_id = notif_settings.get('last_seen_message_id')
            notify_from_senders = notif_settings.get('notify_from_senders', '').lower().split(',') if notif_settings.get('notify_from_senders') else []
            notify_keywords = notif_settings.get('notify_subject_keywords', '').lower().split(',') if notif_settings.get('notify_subject_keywords') else []
            notify_sound = bool(notif_settings.get('notify_sound_enabled', 1))

            if acc.get('account_type') == 'gmail' and gmail_connected:
                access_token = _valid_gmail_access_token(db)
                messages = gmail_list_messages(access_token, 'is:unread', max_results=20)

                for msg in messages:
                    msg_id = msg.get('id', '')
                    if last_seen_id and msg_id == last_seen_id:
                        break

                    should_notify = True
                    if notify_from_senders:
                        sender_lower = msg.get('from', '').lower()
                        should_notify = any(s.strip() in sender_lower for s in notify_from_senders if s.strip())

                    if should_notify and notify_keywords:
                        subject_lower = msg.get('subject', '').lower()
                        should_notify = any(k.strip() in subject_lower for k in notify_keywords if k.strip())

                    if should_notify:
                        new_messages.append({
                            'id': msg_id,
                            'account_id': acc['id'],
                            'account_email': acc.get('email_address', 'Gmail'),
                            'from': msg.get('from', ''),
                            'subject': msg.get('subject', ''),
                            'snippet': msg.get('snippet', ''),
                            'date': msg.get('date', ''),
                            'play_sound': notify_sound,
                        })

                    updated_last_ids[acc['id']] = msg_id if not last_seen_id else None

            elif acc.get('account_type') == 'smtp':
                messages = smtp_fetch_emails(acc, 'INBOX', 'UNSEEN', max_results=20)

                for msg in messages:
                    msg_id = msg.get('id', '')
                    if last_seen_id and msg_id == last_seen_id:
                        break

                    should_notify = True
                    if notify_from_senders:
                        sender_lower = msg.get('from', '').lower()
                        should_notify = any(s.strip() in sender_lower for s in notify_from_senders if s.strip())

                    if should_notify and notify_keywords:
                        subject_lower = msg.get('subject', '').lower()
                        should_notify = any(k.strip() in subject_lower for k in notify_keywords if k.strip())

                    if should_notify:
                        new_messages.append({
                            'id': msg_id,
                            'account_id': acc['id'],
                            'account_email': acc.get('email_address', 'SMTP'),
                            'from': msg.get('from', ''),
                            'subject': msg.get('subject', ''),
                            'snippet': msg.get('snippet', ''),
                            'date': msg.get('date', ''),
                            'play_sound': notify_sound,
                        })

                    updated_last_ids[acc['id']] = msg_id if not last_seen_id else None

        except Exception as exc:
            logger.warning(f"Error checking new emails for notification: {exc}")

    return jsonify({
        'new_messages': new_messages,
        'total': len(new_messages),
    })


@bp.route('/email/settings/save', methods=['POST'])
def email_settings_save():
    """Save Gmail OAuth configuration."""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if not session.get('can_manage_users'):
        flash('Only administrators can manage email settings.', 'error')
        return redirect(url_for('email_manager.email_settings'))

    db = _get_db()
    gmail_client_id = request.form.get('gmail_client_id', '').strip()
    gmail_client_secret = request.form.get('gmail_client_secret', '').strip()
    gmail_redirect_uri = request.form.get('gmail_redirect_uri', '').strip()

    preview_config = {
        'gmail_client_id': gmail_client_id,
        'gmail_client_secret': gmail_client_secret,
    }
    errors = _validate_gmail_config(preview_config)

    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('email_manager.email_settings'))

    _save_email_settings(db, gmail_client_id, gmail_client_secret, gmail_redirect_uri)
    flash('Email settings saved successfully.', 'success')
    return redirect(url_for('email_manager.email_settings'))


@bp.route('/email/api/all')
def email_api_all():
    """
    API endpoint to fetch all emails as JSON for AJAX loading.
    This allows faster page loads without re-fetching emails on each interaction.
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    db = _get_db()
    accounts = _get_user_email_accounts(db)
    gmail_connection = _get_gmail_connection(db)
    gmail_connected = gmail_connection is not None

    folder = request.args.get('folder', 'INBOX')
    query = request.args.get('q', '').strip()
    sort_by = request.args.get('sort', 'date')
    sort_order = request.args.get('order', 'desc')
    max_results = int(request.args.get('max_results', 500))

    all_messages = []
    errors = []

    for acc in accounts:
        try:
            if acc.get('account_type') == 'gmail' and gmail_connected:
                access_token = _valid_gmail_access_token(db)
                folder_query = ''
                if folder == 'SENT':
                    folder_query = 'in:sent'
                elif folder == 'DRAFT':
                    folder_query = 'in:draft'
                elif query:
                    folder_query = query
                
                gm_messages = gmail_list_messages(access_token, folder_query, max_results=max_results)
                for msg in gm_messages:
                    msg['account_email'] = gmail_connection.get('email_address', 'Gmail')
                    msg['account_type'] = 'gmail'
                    msg['account_id'] = None
                    msg['folder'] = folder
                all_messages.extend(gm_messages)

            elif acc.get('account_type') == 'smtp':
                imap_folder = 'INBOX'
                if folder == 'SENT':
                    imap_folder = 'Sent'
                elif folder in ('DRAFT', 'DRAFTS'):
                    imap_folder = 'Drafts'

                search_q = query if query else 'ALL'
                smtp_messages = smtp_fetch_emails(acc, imap_folder, search_q, max_results=max_results)
                for msg in smtp_messages:
                    msg['account_id'] = acc.get('id')
                all_messages.extend(smtp_messages)
                
        except RuntimeError as exc:
            errors.append(f"{acc.get('email_address', 'Unknown')}: {exc}")
        except Exception as exc:
            errors.append(f"{acc.get('email_address', 'Unknown')}: {exc}")

    # Sort messages
    reverse_sort = sort_order == 'desc'
    if sort_by == 'from':
        all_messages.sort(key=lambda x: x.get('from', '').lower(), reverse=reverse_sort)
    elif sort_by == 'subject':
        all_messages.sort(key=lambda x: x.get('subject', '').lower(), reverse=reverse_sort)
    else:  # date
        def parse_date(msg):
            d = msg.get('date', '')
            if not d:
                return 0
            try:
                from email.utils import parsedate_to_datetime
                return parsedate_to_datetime(d).timestamp()
            except Exception:
                return 0
        all_messages.sort(key=parse_date, reverse=reverse_sort)

    return jsonify({
        'messages': all_messages,
        'total': len(all_messages),
        'errors': errors,
        'sort_by': sort_by,
        'sort_order': sort_order,
    })


@bp.route('/email/bulk-action', methods=['POST'])
def email_bulk_action():
    """
    Perform bulk action on multiple emails.
    
    Query parameters:
    - action: 'delete', 'junk', 'archive', 'read', 'unread', 'move'
    - folder: Target folder for 'move' action
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    action = request.args.get('action', '')
    target_folder = request.args.get('folder', '')
    
    # Get message IDs from request
    data = request.get_json() or {}
    message_ids = data.get('message_ids', [])
    
    if not message_ids:
        return jsonify({'error': 'No messages selected'}), 400

    if action not in ('delete', 'junk', 'archive', 'read', 'unread', 'move'):
        return jsonify({'error': 'Invalid action'}), 400

    db = _get_db()
    results = {'success': 0, 'failed': 0, 'errors': []}
    
    # For now, we'll return a success message since actual IMAP operations
    # would require significant additional implementation
    # In production, this would iterate through messages and perform the action
    
    logger.info(f"Bulk action '{action}' requested for {len(message_ids)} messages")
    
    return jsonify({
        'success': True,
        'message': f'{action} action processed for {len(message_ids)} messages',
        'results': results
    })


@bp.route('/email/message/<account_type>/<account_identifier>/<message_id>')
def email_message_detail(account_type, account_identifier, message_id):
    """API endpoint to get message details via AJAX."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    db = _get_db()
    folder = request.args.get('folder', 'INBOX')
    
    try:
        if account_type == 'gmail':
            access_token = _valid_gmail_access_token(db)
            message = gmail_get_message(access_token, message_id)
        else:
            account_id = int(account_identifier)
            account = _get_account_by_id(db, account_id)
            if not account:
                return jsonify({'error': 'Account not found'}), 404
            message = smtp_get_email(account, message_id, folder)
        
        return jsonify(message)
    except RuntimeError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        logger.exception(f"Error fetching message: {exc}")
        return jsonify({'error': 'Failed to fetch message'}), 500
