from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, has_request_context
import base64
import html
import io
import json
import mimetypes
import os
import re
import secrets
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timedelta
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

bp = Blueprint('google_workspace', __name__)
_db_factory = None

GOOGLE_WORKSPACE_SCOPES = [
    'openid',
    'email',
    'profile',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly'
]
GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'
GOOGLE_GMAIL_API = 'https://gmail.googleapis.com/gmail/v1/users/me'
GOOGLE_DRIVE_API = 'https://www.googleapis.com/drive/v3'
GOOGLE_SHEETS_API = 'https://sheets.googleapis.com/v4/spreadsheets'
GOOGLE_CLIENT_ID_PATTERN = re.compile(r'^\d{6,}-[a-z0-9._-]+\.apps\.googleusercontent\.com$', re.IGNORECASE)
GOOGLE_PLACEHOLDER_VALUES = {
    '',
    'admin',
    '123456',
    'test',
    'google_client_id',
    'google_client_secret',
    'your-client-id',
    'your-client-secret',
    'client-id',
    'client-secret',
}
GOOGLE_EXPORT_MAP = {
    'application/vnd.google-apps.document': ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.docx'),
    'application/vnd.google-apps.spreadsheet': ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.xlsx'),
    'application/vnd.google-apps.presentation': ('application/vnd.openxmlformats-officedocument.presentationml.presentation', '.pptx'),
    'application/vnd.google-apps.drawing': ('application/pdf', '.pdf'),
}


def register_google_workspace(app, get_db_factory):
    global _db_factory
    _db_factory = get_db_factory
    app.register_blueprint(bp)


def _get_db():
    if _db_factory is None:
        raise RuntimeError('Google Workspace database factory is not registered.')
    return _db_factory()


def _utcnow():
    return datetime.utcnow()


def _format_dt(value):
    return value.strftime('%Y-%m-%d %H:%M:%S') if value else ''


def _parse_dt(value):
    if not value:
        return None
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S'):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def validate_google_workspace_config(config):
    errors = []
    client_id = (config.get('client_id') or '').strip()
    client_secret = (config.get('client_secret') or '').strip()
    redirect_uri = (config.get('redirect_uri') or '').strip()

    if not client_id:
        errors.append('Google Client ID is missing.')
    elif client_id.lower() in GOOGLE_PLACEHOLDER_VALUES or not GOOGLE_CLIENT_ID_PATTERN.match(client_id):
        errors.append('Google Client ID is not a valid Google OAuth Web Client ID.')

    if not client_secret:
        errors.append('Google Client Secret is missing.')
    elif client_secret.lower() in GOOGLE_PLACEHOLDER_VALUES or len(client_secret) < 8:
        errors.append('Google Client Secret looks like a placeholder and must be replaced with the real Google secret.')

    if redirect_uri:
        parsed = urllib.parse.urlparse(redirect_uri)
        if parsed.scheme not in ('http', 'https'):
            errors.append('Redirect URI must start with http:// or https://.')
        if not parsed.path.endswith('/workspace/oauth/callback'):
            errors.append('Redirect URI must end with /workspace/oauth/callback to match the Google Workspace callback route.')
    elif has_request_context():
        generated = url_for('google_workspace.workspace_callback', _external=True)
        parsed = urllib.parse.urlparse(generated)
        if not parsed.scheme:
            errors.append('Redirect URI could not be generated for the current server.')

    return errors


def get_google_workspace_settings(db=None):
    database = db or _get_db()
    row = database.execute(
        'SELECT * FROM google_workspace_settings WHERE id = 1'
    ).fetchone()
    if not row:
        return {
            'client_id': '',
            'client_secret': '',
            'redirect_uri': '',
            'updated_at': ''
        }
    return dict(row)


def save_google_workspace_settings(db, client_id, client_secret, redirect_uri):
    existing = get_google_workspace_settings(db)
    resolved_secret = client_secret.strip() or existing.get('client_secret', '')
    db.execute(
        '''
        INSERT INTO google_workspace_settings (
            id, client_id, client_secret, redirect_uri, updated_at
        ) VALUES (1, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            client_id = excluded.client_id,
            client_secret = CASE
                WHEN COALESCE(excluded.client_secret, '') != '' THEN excluded.client_secret
                ELSE google_workspace_settings.client_secret
            END,
            redirect_uri = excluded.redirect_uri,
            updated_at = CURRENT_TIMESTAMP
        ''',
        (
            client_id.strip(),
            resolved_secret,
            redirect_uri.strip(),
        )
    )
    db.commit()
    return get_google_workspace_settings(db)


def resolved_google_workspace_config(db=None):
    settings = get_google_workspace_settings(db)
    client_id = (os.environ.get('GOOGLE_CLIENT_ID', '') or settings.get('client_id', '')).strip()
    client_secret = (os.environ.get('GOOGLE_CLIENT_SECRET', '') or settings.get('client_secret', '')).strip()
    redirect_uri = (os.environ.get('GOOGLE_OAUTH_REDIRECT_URI', '') or settings.get('redirect_uri', '')).strip()
    if not redirect_uri and has_request_context():
        redirect_uri = url_for('google_workspace.workspace_callback', _external=True)
    return {
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'settings_updated_at': settings.get('updated_at', ''),
        'source': (
            'environment'
            if os.environ.get('GOOGLE_CLIENT_ID') and os.environ.get('GOOGLE_CLIENT_SECRET')
            else ('database' if settings.get('client_id') and settings.get('client_secret') else 'missing')
        )
    }


def google_workspace_is_configured(db=None):
    config = resolved_google_workspace_config(db)
    return bool(config['client_id'] and config['client_secret'] and not validate_google_workspace_config(config))


def google_workspace_redirect_uri(db=None):
    config = resolved_google_workspace_config(db)
    if config['redirect_uri']:
        return config['redirect_uri']
    if has_request_context():
        return url_for('google_workspace.workspace_callback', _external=True)
    return ''


def get_google_connection(db=None, user_id=None):
    resolved_user_id = user_id or session.get('user_id')
    if not resolved_user_id:
        return None
    database = db or _get_db()
    return database.execute(
        'SELECT * FROM google_workspace_tokens WHERE user_id = ?',
        (resolved_user_id,)
    ).fetchone()


def save_google_connection(db, user_id, token_payload, email_address=''):
    expires_in = int(token_payload.get('expires_in') or 3600)
    expires_at = _utcnow() + timedelta(seconds=max(expires_in - 60, 60))
    db.execute(
        '''
        INSERT INTO google_workspace_tokens (
            user_id, access_token, refresh_token, token_type, scope, expires_at, email_address, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            access_token = excluded.access_token,
            refresh_token = CASE
                WHEN COALESCE(excluded.refresh_token, '') != '' THEN excluded.refresh_token
                ELSE google_workspace_tokens.refresh_token
            END,
            token_type = excluded.token_type,
            scope = excluded.scope,
            expires_at = excluded.expires_at,
            email_address = excluded.email_address,
            updated_at = CURRENT_TIMESTAMP
        ''',
        (
            user_id,
            token_payload.get('access_token', ''),
            token_payload.get('refresh_token', ''),
            token_payload.get('token_type', 'Bearer'),
            token_payload.get('scope', ' '.join(GOOGLE_WORKSPACE_SCOPES)),
            _format_dt(expires_at),
            email_address,
        )
    )
    db.commit()
    return get_google_connection(db, user_id)


def delete_google_connection(db, user_id):
    db.execute('DELETE FROM google_workspace_tokens WHERE user_id = ?', (user_id,))
    db.commit()


def workspace_connection_summary(db=None):
    db = db or _get_db()
    token_row = get_google_connection(db)
    config = resolved_google_workspace_config(db)
    config_errors = validate_google_workspace_config(config)
    summary = {
        'configured': google_workspace_is_configured(db),
        'connected': bool(token_row),
        'email_address': token_row['email_address'] if token_row else '',
        'expires_at': token_row['expires_at'] if token_row else '',
        'scopes': (token_row['scope'] or '').split() if token_row and token_row['scope'] else GOOGLE_WORKSPACE_SCOPES,
        'redirect_uri': config['redirect_uri'],
        'recommended_redirect_uri': url_for('google_workspace.workspace_callback', _external=True) if has_request_context() else '',
        'settings_updated_at': config['settings_updated_at'],
        'configuration_source': config['source'],
        'can_manage_settings': bool(session.get('can_manage_users')),
        'config_errors': config_errors,
        'config_valid': not config_errors,
    }
    return summary


def _token_request_payload(payload):
    encoded = urllib.parse.urlencode(payload).encode('utf-8')
    request_obj = urllib.request.Request(
        GOOGLE_TOKEN_URL,
        data=encoded,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST'
    )
    return _load_json(request_obj)


def _load_json(request_obj):
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


def _load_bytes(request_obj):
    try:
        with urllib.request.urlopen(request_obj, timeout=60) as response:
            return response.read(), response.headers.get_content_type()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='ignore')
        raise RuntimeError(body or str(exc))
    except urllib.error.URLError as exc:
        raise RuntimeError(str(exc.reason or exc))


def exchange_google_code(code, db=None):
    config = resolved_google_workspace_config(db)
    return _token_request_payload({
        'code': code,
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'redirect_uri': google_workspace_redirect_uri(db),
        'grant_type': 'authorization_code'
    })


def refresh_google_access_token(refresh_token, db=None):
    config = resolved_google_workspace_config(db)
    return _token_request_payload({
        'refresh_token': refresh_token,
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'grant_type': 'refresh_token'
    })


def valid_google_access_token(db=None):
    db = db or _get_db()
    connection = get_google_connection(db)
    if not connection:
        raise RuntimeError('Google Workspace is not connected for this user.')

    expires_at = _parse_dt(connection['expires_at'])
    if expires_at and expires_at > _utcnow() + timedelta(seconds=30):
        return connection['access_token']

    refresh_token = connection['refresh_token']
    if not refresh_token:
        raise RuntimeError('Google Workspace token expired and no refresh token is available.')

    refreshed = refresh_google_access_token(refresh_token, db)
    refreshed['refresh_token'] = refresh_token
    save_google_connection(db, session.get('user_id'), refreshed, connection['email_address'])
    return get_google_connection(db)['access_token']


def google_json_api(path_or_url, access_token, params=None, method='GET', payload=None, extra_headers=None):
    url = path_or_url if path_or_url.startswith('http') else path_or_url
    if params:
        url = f"{url}{'&' if '?' in url else '?'}{urllib.parse.urlencode(params, doseq=True)}"
    headers = {'Authorization': f'Bearer {access_token}'}
    if extra_headers:
        headers.update(extra_headers)
    data = None
    if payload is not None:
        data = json.dumps(payload).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    request_obj = urllib.request.Request(url, data=data, headers=headers, method=method)
    return _load_json(request_obj)


def google_bytes_api(url, access_token, params=None):
    if params:
        url = f"{url}{'&' if '?' in url else '?'}{urllib.parse.urlencode(params, doseq=True)}"
    request_obj = urllib.request.Request(url, headers={'Authorization': f'Bearer {access_token}'})
    return _load_bytes(request_obj)


def google_user_profile(access_token):
    return google_json_api(GOOGLE_USERINFO_URL, access_token)


def build_google_auth_url(db=None):
    state = secrets.token_urlsafe(24)
    session['google_workspace_oauth_state'] = state
    config = resolved_google_workspace_config(db)
    params = {
        'client_id': config['client_id'],
        'redirect_uri': google_workspace_redirect_uri(db),
        'response_type': 'code',
        'scope': ' '.join(GOOGLE_WORKSPACE_SCOPES),
        'access_type': 'offline',
        'prompt': 'consent',
        'include_granted_scopes': 'true',
        'state': state,
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


def gmail_list_messages(access_token, search_query=''):
    payload = google_json_api(
        f'{GOOGLE_GMAIL_API}/messages',
        access_token,
        params={'maxResults': 25, 'labelIds': 'INBOX', 'q': search_query or ''}
    )
    messages = []
    for item in payload.get('messages', []):
        detail = google_json_api(
            f"{GOOGLE_GMAIL_API}/messages/{item['id']}",
            access_token,
            params={
                'format': 'metadata',
                'metadataHeaders': ['From', 'Subject', 'Date', 'To']
            }
        )
        headers = {header['name'].lower(): header['value'] for header in detail.get('payload', {}).get('headers', [])}
        messages.append({
            'id': detail.get('id'),
            'thread_id': detail.get('threadId'),
            'snippet': detail.get('snippet', ''),
            'subject': headers.get('subject', '(No subject)'),
            'from': headers.get('from', '--'),
            'to': headers.get('to', '--'),
            'date': headers.get('date', '--'),
            'label_ids': detail.get('labelIds', []),
        })
    return messages


def _decode_b64_url(value):
    if not value:
        return ''
    padding = '=' * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode('utf-8')).decode('utf-8', errors='ignore')


def _strip_html(value):
    if not value:
        return ''
    value = re.sub(r'(?i)<br\s*/?>', '\n', value)
    value = re.sub(r'(?i)</p>', '\n\n', value)
    value = re.sub(r'<[^>]+>', '', value)
    return html.unescape(value).strip()


def _extract_message_part(parts, mime_type):
    for part in parts:
        if part.get('mimeType') == mime_type and part.get('body', {}).get('data'):
            return _decode_b64_url(part['body']['data'])
        if part.get('parts'):
            nested = _extract_message_part(part['parts'], mime_type)
            if nested:
                return nested
    return ''


def _collect_attachments(parts, attachments=None):
    attachments = attachments or []
    for part in parts:
        filename = part.get('filename') or ''
        body = part.get('body', {})
        if filename and body.get('attachmentId'):
            attachments.append({
                'filename': filename,
                'mime_type': part.get('mimeType', 'application/octet-stream'),
                'attachment_id': body.get('attachmentId'),
                'size': body.get('size', 0),
            })
        if part.get('parts'):
            _collect_attachments(part['parts'], attachments)
    return attachments


def gmail_get_message(access_token, message_id):
    detail = google_json_api(
        f'{GOOGLE_GMAIL_API}/messages/{message_id}',
        access_token,
        params={'format': 'full'}
    )
    payload = detail.get('payload', {})
    headers = {header['name'].lower(): header['value'] for header in payload.get('headers', [])}
    parts = payload.get('parts', [])
    plain_body = _extract_message_part(parts, 'text/plain')
    html_body = _extract_message_part(parts, 'text/html')
    fallback_body = _decode_b64_url(payload.get('body', {}).get('data', ''))
    body = plain_body or _strip_html(html_body) or fallback_body or detail.get('snippet', '')
    return {
        'id': detail.get('id'),
        'thread_id': detail.get('threadId'),
        'subject': headers.get('subject', '(No subject)'),
        'from': headers.get('from', '--'),
        'to': headers.get('to', '--'),
        'cc': headers.get('cc', ''),
        'date': headers.get('date', '--'),
        'body': body,
        'snippet': detail.get('snippet', ''),
        'attachments': _collect_attachments(parts),
        'label_ids': detail.get('labelIds', []),
    }


def gmail_send_message(access_token, form, uploaded_files):
    message = MIMEMultipart()
    message['To'] = form.get('to', '').strip()
    if form.get('cc', '').strip():
        message['Cc'] = form.get('cc', '').strip()
    if form.get('bcc', '').strip():
        message['Bcc'] = form.get('bcc', '').strip()
    message['Subject'] = form.get('subject', '').strip() or '(No subject)'
    body = form.get('body', '').strip()
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
    return google_json_api(
        f'{GOOGLE_GMAIL_API}/messages/send',
        access_token,
        method='POST',
        payload={'raw': raw}
    )


def drive_get_item(access_token, file_id):
    return google_json_api(
        f'{GOOGLE_DRIVE_API}/files/{file_id}',
        access_token,
        params={'fields': 'id,name,mimeType,size,parents,modifiedTime,webViewLink'}
    )


def drive_list_items(access_token, parent_id='root', search_query=''):
    query_parts = [f"'{parent_id or 'root'}' in parents", 'trashed = false']
    if search_query:
        safe_query = search_query.replace("'", "\\'")
        query_parts.append(f"name contains '{safe_query}'")
    payload = google_json_api(
        f'{GOOGLE_DRIVE_API}/files',
        access_token,
        params={
            'q': ' and '.join(query_parts),
            'orderBy': 'folder,name',
            'pageSize': 100,
            'fields': 'files(id,name,mimeType,size,modifiedTime,parents,webViewLink)'
        }
    )
    files = []
    for item in payload.get('files', []):
        files.append({
            'id': item.get('id'),
            'name': item.get('name', '--'),
            'mime_type': item.get('mimeType', ''),
            'size': int(item.get('size') or 0),
            'modified_time': item.get('modifiedTime', ''),
            'parents': item.get('parents', []),
            'is_folder': item.get('mimeType') == 'application/vnd.google-apps.folder',
            'is_google_file': str(item.get('mimeType', '')).startswith('application/vnd.google-apps.'),
            'web_view_link': item.get('webViewLink', ''),
        })
    return files


def drive_build_breadcrumbs(access_token, parent_id):
    breadcrumbs = [{'id': 'root', 'name': 'My Drive'}]
    if not parent_id or parent_id == 'root':
        return breadcrumbs

    chain = []
    current_id = parent_id
    while current_id and current_id != 'root':
        item = drive_get_item(access_token, current_id)
        chain.append({'id': item.get('id'), 'name': item.get('name', '--')})
        parents = item.get('parents') or []
        current_id = parents[0] if parents else 'root'
    breadcrumbs.extend(reversed(chain))
    return breadcrumbs


def drive_download_item_bytes(access_token, item):
    mime_type = item.get('mimeType', '')
    name = item.get('name', 'download')
    if mime_type in GOOGLE_EXPORT_MAP:
        export_mime, extension = GOOGLE_EXPORT_MAP[mime_type]
        content, resolved_type = google_bytes_api(
            f"{GOOGLE_DRIVE_API}/files/{item['id']}/export",
            access_token,
            params={'mimeType': export_mime}
        )
        return content, resolved_type or export_mime, name + extension
    content, resolved_type = google_bytes_api(
        f"{GOOGLE_DRIVE_API}/files/{item['id']}",
        access_token,
        params={'alt': 'media'}
    )
    return content, resolved_type or 'application/octet-stream', name


def drive_write_folder_to_zip(access_token, folder_id, archive, prefix=''):
    for child in drive_list_items(access_token, folder_id):
        child_path = f"{prefix}{child['name']}"
        if child['is_folder']:
            drive_write_folder_to_zip(access_token, child['id'], archive, child_path + '/')
            continue
        content, _, filename = drive_download_item_bytes(access_token, {
            'id': child['id'],
            'name': child['name'],
            'mimeType': child['mime_type']
        })
        final_name = child_path
        if filename != child['name'] and not final_name.endswith(os.path.splitext(filename)[1]):
            final_name += os.path.splitext(filename)[1]
        archive.writestr(final_name, content)


def sheets_list_spreadsheets(access_token, search_query=''):
    query_parts = ["mimeType = 'application/vnd.google-apps.spreadsheet'", 'trashed = false']
    if search_query:
        safe_query = search_query.replace("'", "\\'")
        query_parts.append(f"name contains '{safe_query}'")
    payload = google_json_api(
        f'{GOOGLE_DRIVE_API}/files',
        access_token,
        params={
            'q': ' and '.join(query_parts),
            'orderBy': 'modifiedTime desc',
            'pageSize': 50,
            'fields': 'files(id,name,modifiedTime,owners(displayName),webViewLink)'
        }
    )
    return payload.get('files', [])


def sheets_get_preview(access_token, spreadsheet_id):
    metadata = google_json_api(
        f'{GOOGLE_SHEETS_API}/{spreadsheet_id}',
        access_token,
        params={'fields': 'spreadsheetId,properties(title),sheets(properties(title,sheetId,gridProperties(rowCount,columnCount)))'}
    )
    sheets = metadata.get('sheets', [])
    if not sheets:
        return {'metadata': metadata, 'sheet_title': '', 'headers': [], 'rows': []}
    sheet_title = sheets[0].get('properties', {}).get('title', 'Sheet1')
    preview_range = urllib.parse.quote(f"'{sheet_title}'!A1:Z30", safe="!:'")
    values_payload = google_json_api(
        f'{GOOGLE_SHEETS_API}/{spreadsheet_id}/values/{preview_range}',
        access_token
    )
    values = values_payload.get('values', [])
    headers = values[0] if values else []
    rows = values[1:] if len(values) > 1 else []
    max_columns = max([len(headers)] + [len(row) for row in rows], default=0)
    if max_columns and len(headers) < max_columns:
        headers = headers + [f'Column {idx}' for idx in range(len(headers) + 1, max_columns + 1)]
    normalized_rows = [row + [''] * (len(headers) - len(row)) for row in rows]
    return {
        'metadata': metadata,
        'sheet_title': sheet_title,
        'headers': headers,
        'rows': normalized_rows,
    }


def _workspace_context(title):
    db = _get_db()
    summary = workspace_connection_summary(db)
    settings = get_google_workspace_settings(db)
    return db, summary, {
        'title': title,
        'workspace_connection': summary,
        'workspace_settings': settings,
    }


def google_workspace_report_snapshot(db, current_user_id=None):
    config = resolved_google_workspace_config(db)
    config_errors = validate_google_workspace_config(config)
    token_rows = db.execute(
        '''
        SELECT gwt.*, u.username, u.email
        FROM google_workspace_tokens gwt
        LEFT JOIN users u ON gwt.user_id = u.id
        ORDER BY COALESCE(gwt.updated_at, gwt.expires_at) DESC, gwt.user_id DESC
        '''
    ).fetchall()
    total_users_row = db.execute('SELECT COUNT(*) AS total FROM users').fetchone()
    total_users = int((total_users_row['total'] if total_users_row else 0) or 0)
    now_value = _utcnow()
    soon_threshold = now_value + timedelta(hours=24)
    expiring_soon = 0
    connected_accounts = []

    for row in token_rows:
        expires_at = _parse_dt(row['expires_at'])
        token_health = 'Healthy'
        if expires_at and expires_at <= soon_threshold:
            expiring_soon += 1
            token_health = 'Expiring Soon'
        connected_accounts.append({
            'username': row['username'] or f"User {row['user_id']}",
            'email': row['email_address'] or row['email'] or '--',
            'updated_at': row['updated_at'] or '',
            'expires_at': row['expires_at'] or '--',
            'token_health': token_health,
        })

    current_connection = get_google_connection(db, current_user_id) if current_user_id else None
    connected_total = len(connected_accounts)
    unlinked_users = max(total_users - connected_total, 0)

    return {
        'summary': {
            'configured': not config_errors,
            'configuration_source': config['source'],
            'connected_accounts': connected_total,
            'total_users': total_users,
            'unlinked_users': unlinked_users,
            'expiring_soon': expiring_soon,
            'current_user_connected': bool(current_connection),
            'current_user_email': current_connection['email_address'] if current_connection else '',
            'redirect_uri': config['redirect_uri'],
            'config_errors': config_errors,
        },
        'health_chart': [
            {'label': 'Connected Accounts', 'total': connected_total},
            {'label': 'Unlinked Users', 'total': unlinked_users},
            {'label': 'Expiring Soon', 'total': expiring_soon},
        ],
        'connected_accounts': connected_accounts[:12],
    }


def _settings_button_context():
    if not session.get('can_manage_users'):
        return {
            'workspace_setup_label': 'Admin Setup Required',
            'workspace_setup_url': url_for('google_workspace.workspace_home')
        }
    return {
        'workspace_setup_label': 'Configure Google OAuth',
        'workspace_setup_url': url_for('google_workspace.workspace_settings')
    }


@bp.route('/workspace')
def workspace_home():
    db, summary, context = _workspace_context('Google Workspace')
    metrics = {'gmail': 0, 'drive': 0, 'sheets': 0}
    if summary['connected'] and summary['configured']:
        try:
            access_token = valid_google_access_token(db)
            metrics['gmail'] = len(gmail_list_messages(access_token))
            metrics['drive'] = len(drive_list_items(access_token))
            metrics['sheets'] = len(sheets_list_spreadsheets(access_token))
        except Exception as exc:
            flash(f'Google Workspace connection needs attention: {exc}', 'error')
    context['workspace_metrics'] = metrics
    context.update(_settings_button_context())
    return render_template('workspace_hub.html', **context)


@bp.route('/workspace/settings', methods=['GET', 'POST'])
def workspace_settings():
    if not session.get('can_manage_users'):
        flash('Only administrators can manage Google Workspace OAuth settings.', 'error')
        return redirect(url_for('google_workspace.workspace_home'))

    db, summary, context = _workspace_context('Google Workspace Settings')
    existing_settings = get_google_workspace_settings(db)
    recommended_redirect = url_for('google_workspace.workspace_callback', _external=True)

    if request.method == 'POST':
        client_id = request.form.get('client_id', '').strip()
        client_secret = request.form.get('client_secret', '').strip()
        redirect_uri = request.form.get('redirect_uri', '').strip() or recommended_redirect
        preview_settings = {
            'client_id': client_id,
            'client_secret': client_secret or existing_settings.get('client_secret', ''),
            'redirect_uri': redirect_uri,
        }
        validation_errors = validate_google_workspace_config(preview_settings)

        if not client_id:
            flash('Google Client ID is required.', 'error')
        elif not (client_secret or existing_settings.get('client_secret', '').strip()):
            flash('Google Client Secret is required the first time you save Google Workspace settings.', 'error')
        elif validation_errors:
            for error_message in validation_errors:
                flash(error_message, 'error')
        else:
            save_google_workspace_settings(db, client_id, client_secret, redirect_uri)
            flash('Google Workspace OAuth settings saved successfully.', 'success')
            return redirect(url_for('google_workspace.workspace_settings'))

    refreshed_settings = get_google_workspace_settings(db)
    context.update({
        'workspace_settings': refreshed_settings,
        'workspace_recommended_redirect_uri': recommended_redirect,
        'workspace_has_saved_secret': bool(refreshed_settings.get('client_secret', '').strip()),
        'workspace_uses_env_override': summary['configuration_source'] == 'environment',
    })
    return render_template('workspace_settings.html', **context)


@bp.route('/workspace/connect')
def workspace_connect():
    db = _get_db()
    if not google_workspace_is_configured(db):
        config_errors = validate_google_workspace_config(resolved_google_workspace_config(db))
        error_message = config_errors[0] if config_errors else 'Google Workspace OAuth is not configured yet.'
        if session.get('can_manage_users'):
            flash(f'{error_message} Update Google Workspace Settings first.', 'error')
            return redirect(url_for('google_workspace.workspace_settings'))
        flash(f'{error_message} Please ask an administrator to complete Google Workspace Settings first.', 'error')
        return redirect(url_for('google_workspace.workspace_home'))
    return redirect(build_google_auth_url(db))


@bp.route('/workspace/oauth/callback')
def workspace_callback():
    expected_state = session.get('google_workspace_oauth_state')
    received_state = request.args.get('state', '')
    code = request.args.get('code', '')
    if not code or not expected_state or expected_state != received_state:
        flash('Google Workspace authorization could not be verified.', 'error')
        return redirect(url_for('google_workspace.workspace_home'))

    db = _get_db()
    try:
        tokens = exchange_google_code(code, db)
        profile = google_user_profile(tokens.get('access_token', ''))
        save_google_connection(db, session.get('user_id'), tokens, profile.get('email', ''))
        flash('Google Workspace connected successfully.', 'success')
    except Exception as exc:
        flash(f'Google Workspace connection failed: {exc}', 'error')
    finally:
        session.pop('google_workspace_oauth_state', None)
    return redirect(url_for('google_workspace.workspace_home'))


@bp.route('/workspace/disconnect', methods=['POST'])
def workspace_disconnect():
    db = _get_db()
    delete_google_connection(db, session.get('user_id'))
    flash('Google Workspace connection removed.', 'success')
    return redirect(url_for('google_workspace.workspace_home'))


@bp.route('/workspace/gmail')
def workspace_gmail():
    db, summary, context = _workspace_context('Workspace Gmail')
    messages = []
    selected_message = None
    query = request.args.get('q', '').strip()
    if summary['connected'] and summary['configured']:
        try:
            access_token = valid_google_access_token(db)
            messages = gmail_list_messages(access_token, query)
            message_id = request.args.get('message_id', '').strip()
            if message_id:
                selected_message = gmail_get_message(access_token, message_id)
        except Exception as exc:
            flash(f'Gmail could not be loaded: {exc}', 'error')
    context.update({
        'gmail_messages': messages,
        'gmail_selected_message': selected_message,
        'gmail_query': query,
        **_settings_button_context(),
    })
    return render_template('workspace_gmail.html', **context)


@bp.route('/workspace/gmail/send', methods=['POST'])
def workspace_gmail_send():
    db = _get_db()
    try:
        access_token = valid_google_access_token(db)
        if not request.form.get('to', '').strip():
            raise RuntimeError('Recipient email address is required.')
        gmail_send_message(access_token, request.form, request.files.getlist('attachments'))
        flash('Email sent successfully.', 'success')
    except Exception as exc:
        flash(f'Email could not be sent: {exc}', 'error')
    return redirect(url_for('google_workspace.workspace_gmail'))


@bp.route('/workspace/drive')
def workspace_drive():
    db, summary, context = _workspace_context('Workspace Drive')
    items = []
    breadcrumbs = [{'id': 'root', 'name': 'My Drive'}]
    current_folder = {'id': 'root', 'name': 'My Drive'}
    query = request.args.get('q', '').strip()
    parent_id = request.args.get('parent_id', 'root').strip() or 'root'
    if summary['connected'] and summary['configured']:
        try:
            access_token = valid_google_access_token(db)
            items = drive_list_items(access_token, parent_id, query)
            breadcrumbs = drive_build_breadcrumbs(access_token, parent_id)
            current_folder = breadcrumbs[-1]
        except Exception as exc:
            flash(f'Google Drive could not be loaded: {exc}', 'error')
    context.update({
        'drive_items': items,
        'drive_breadcrumbs': breadcrumbs,
        'drive_current_folder': current_folder,
        'drive_query': query,
        'drive_parent_id': parent_id,
        **_settings_button_context(),
    })
    return render_template('workspace_drive.html', **context)


@bp.route('/workspace/drive/download/<file_id>')
def workspace_drive_download(file_id):
    db = _get_db()
    try:
        access_token = valid_google_access_token(db)
        item = drive_get_item(access_token, file_id)
        if item.get('mimeType') == 'application/vnd.google-apps.folder':
            return redirect(url_for('google_workspace.workspace_drive_folder_download', file_id=file_id))
        content, mime_type, filename = drive_download_item_bytes(access_token, item)
        return send_file(io.BytesIO(content), as_attachment=True, download_name=filename, mimetype=mime_type)
    except Exception as exc:
        flash(f'File download failed: {exc}', 'error')
        return redirect(url_for('google_workspace.workspace_drive'))


@bp.route('/workspace/drive/folder/<file_id>/download')
def workspace_drive_folder_download(file_id):
    db = _get_db()
    try:
        access_token = valid_google_access_token(db)
        folder = drive_get_item(access_token, file_id)
        if folder.get('mimeType') != 'application/vnd.google-apps.folder':
            raise RuntimeError('The selected item is not a Google Drive folder.')
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            drive_write_folder_to_zip(access_token, file_id, archive, folder.get('name', 'Folder') + '/')
        output.seek(0)
        return send_file(output, as_attachment=True, download_name=f"{folder.get('name', 'drive-folder')}.zip", mimetype='application/zip')
    except Exception as exc:
        flash(f'Folder download failed: {exc}', 'error')
        return redirect(url_for('google_workspace.workspace_drive'))


@bp.route('/workspace/sheets')
def workspace_sheets():
    db, summary, context = _workspace_context('Workspace Sheets')
    spreadsheets = []
    preview = None
    query = request.args.get('q', '').strip()
    spreadsheet_id = request.args.get('spreadsheet_id', '').strip()
    if summary['connected'] and summary['configured']:
        try:
            access_token = valid_google_access_token(db)
            spreadsheets = sheets_list_spreadsheets(access_token, query)
            if spreadsheet_id:
                preview = sheets_get_preview(access_token, spreadsheet_id)
        except Exception as exc:
            flash(f'Google Sheets could not be loaded: {exc}', 'error')
    context.update({
        'sheets_files': spreadsheets,
        'sheets_preview': preview,
        'sheets_query': query,
        **_settings_button_context(),
    })
    return render_template('workspace_sheets.html', **context)
