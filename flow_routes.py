"""
FLOW - Enterprise Internal Communication Platform
Routes Module

This module defines all Flask routes for the FLOW platform including:
- Main dashboard and navigation
- Private chats, groups, and channels
- Messages and attachments
- Real-time updates via polling
- Calls and meetings
- Notifications
- User settings and profiles
- Search functionality
"""

import os
import json
import uuid
import base64
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, send_file, Response
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

try:
    from flow_models import (
        initialize_flow, get_flow_profile, ensure_flow_profile,
        get_or_create_private_conversation, get_user_saved_messages_conversation,
        send_message, add_reaction, remove_reaction, set_reminder,
        get_conversation_messages, get_user_conversations, search_messages,
        create_notification, get_unread_notification_count,
        get_user_status, set_user_status, update_presence,
        create_channel, create_group, start_call, start_meeting,
        get_shared_media, get_user_settings, update_user_settings,
        update_flow_profile,
        block_user, unblock_user, is_user_blocked,
        get_due_reminders, complete_reminder,
        generate_id, get_one, get_all, get_db_context, log_audit,
        FLOW_PERMISSIONS,
        # Push notifications
        save_push_subscription, remove_push_subscription, get_active_push_subscription,
        get_all_active_push_subscriptions, has_push_subscription, send_push_notification,
        get_push_notification_logs, update_push_subscription_usage,
        # Test messages
        seed_test_messages,
        # Channel ID validation
        validate_channel_id, is_channel_id_available,
        generate_invite_code, seed_sample_channels,
        # Updates
        update_channel, update_group
    )
    from permissions import user_has_permission
except ImportError:
    # Fallback if imports fail
    from database import get_one, get_all, get_db_context
    def user_has_permission(user_id, module, resource, action):
        return True

flow_bp = Blueprint('flow', __name__, url_prefix='/flow', template_folder='templates/flow')


def safe_is_json():
    """Safely check if request is JSON (handles OSError on Windows)."""
    try:
        return request.content_type and 'application/json' in request.content_type
    except OSError:
        return False


def safe_get_json():
    """Safely get JSON data from request (handles OSError on Windows)."""
    try:
        return request.get_json()
    except OSError:
        return None


# ============================================================================
# CSRF PROTECTION FOR FLOW API
# ============================================================================

def flow_csrf_protected(f):
    """Decorator to protect Flow JSON API endpoints with CSRF validation."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            # Check for CSRF token in headers or JSON body
            token = request.headers.get('X-CSRF-Token')
            if not token:
                # Try to get from JSON body
                try:
                    if safe_is_json() and safe_get_json():
                        token = safe_get_json().get('csrf_token')
                except OSError:
                    pass
            # Also allow cookie-based CSRF from browser
            if not token:
                token = request.cookies.get('csrf_token')

            if token:
                # Validate using app's validate function if available
                try:
                    from app import validate_csrf_token as app_validate
                    if not app_validate(token):
                        return jsonify({'error': 'CSRF validation failed'}), 403
                except ImportError:
                    pass
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# RATE LIMITING FOR MESSAGE SEND
# ============================================================================

import time
from threading import Lock

class RateLimiter:
    """Simple in-memory rate limiter for message sending."""

    def __init__(self, max_messages=10, window_seconds=60):
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        self.requests = {}
        self.lock = Lock()

    def is_allowed(self, user_id):
        """Check if user is allowed to send a message."""
        with self.lock:
            now = time.time()
            user_key = str(user_id)

            if user_key not in self.requests:
                self.requests[user_key] = []

            # Remove old entries outside the window
            self.requests[user_key] = [
                t for t in self.requests[user_key]
                if now - t < self.window_seconds
            ]

            # Check if under limit
            if len(self.requests[user_key]) >= self.max_messages:
                return False

            # Add this request
            self.requests[user_key].append(now)
            return True

    def get_remaining(self, user_id):
        """Get remaining messages allowed for user."""
        with self.lock:
            now = time.time()
            user_key = str(user_id)

            if user_key not in self.requests:
                return self.max_messages

            # Count recent requests
            recent = [t for t in self.requests[user_key] if now - t < self.window_seconds]
            return max(0, self.max_messages - len(recent))


# Global rate limiter instance
_message_rate_limiter = RateLimiter(max_messages=10, window_seconds=60)


def check_message_rate_limit(user_id):
    """Check if user can send message. Returns (allowed, remaining, retry_after)."""
    allowed = _message_rate_limiter.is_allowed(user_id)
    remaining = _message_rate_limiter.get_remaining(user_id)
    retry_after = 0 if allowed else 5  # Simple backoff
    return allowed, remaining, retry_after


# File upload configuration
FLOW_UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'flow_uploads')
FLOW_MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024  # 2GB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'webm', 'mov', 'mp3', 'wav', 'ogg', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv', 'zip', 'rar'}

os.makedirs(FLOW_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(FLOW_UPLOAD_FOLDER, 'images'), exist_ok=True)
os.makedirs(os.path.join(FLOW_UPLOAD_FOLDER, 'videos'), exist_ok=True)
os.makedirs(os.path.join(FLOW_UPLOAD_FOLDER, 'audio'), exist_ok=True)
os.makedirs(os.path.join(FLOW_UPLOAD_FOLDER, 'files'), exist_ok=True)
os.makedirs(os.path.join(FLOW_UPLOAD_FOLDER, 'thumbnails'), exist_ok=True)

# ============================================================================
# AUTH HELPERS
# ============================================================================

def get_current_user():
    """Get current logged in user from session."""
    try:
        user_id = session.get('user_id')
    except RuntimeError:
        # Session accessed outside request context
        return None
    if not user_id:
        return None
    return get_one('SELECT * FROM users WHERE id = ?', (user_id,))


def get_user_direction():
    """Get the text direction for the current user based on preferences."""
    try:
        from app import get_user_preferences
        prefs = get_user_preferences()
        interface_dir = prefs.get('interface_direction', 'auto')
        if interface_dir == 'auto':
            lang = prefs.get('language', 'en')
            return 'rtl' if lang in ['fa', 'ar', 'he', 'ur'] else 'ltr'
        return interface_dir
    except (ImportError, Exception):
        return 'ltr'  # Default to left-to-right


@flow_bp.context_processor
def inject_flow_context():
    """Inject common context variables into all flow templates."""
    from datetime import datetime

    def format_time(value):
        if value is None:
            return ''
        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return value
        elif isinstance(value, datetime):
            dt = value
        else:
            return str(value)

        now = datetime.now()
        diff = now - dt
        total_seconds = diff.total_seconds()

        if total_seconds < 0:
            return dt.strftime('%H:%M')
        if total_seconds < 60:
            return 'now'
        if total_seconds < 3600:
            minutes = int(total_seconds / 60)
            return f'{minutes}m'
        if total_seconds < 86400:
            hours = int(total_seconds / 3600)
            return f'{hours}h'
        if total_seconds < 604800:
            days = int(total_seconds / 86400)
            return f'{days}d'
        return dt.strftime('%Y-%m-%d')

    def safe_escape_html(text):
        """Safely escape HTML text, handling OSError on Windows."""
        if not text:
            return ''
        try:
            import html
            return html.escape(str(text))
        except Exception:
            return str(text)

    return {
        'direction': get_user_direction(),
        'format_time': format_time,
        'escape_html': safe_escape_html
    }


def require_login(f):
    """Decorator to require login for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            if safe_is_json():
                return jsonify({'error': 'Unauthorized'}), 401
            return redirect('/login')
        # Ensure flow profile exists (with error handling)
        try:
            ensure_flow_profile(user['id'])
        except Exception as e:
            import traceback
            logger.error(f'ensure_flow_profile error for user {user["id"]}: {str(e)}')
            traceback.print_exc()
            if safe_is_json():
                return jsonify({'error': 'Flow profile error', 'details': str(e)}), 500
        return f(*args, **kwargs)
    return decorated_function


def require_permission(resource, action):
    """Decorator to check Flow permissions."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({'error': 'Unauthorized'}), 401
            if not user_has_permission(user['id'], 'flow', resource, action):
                return jsonify({'error': 'Permission denied'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================================================
# MAIN ROUTES
# ============================================================================

@flow_bp.route('/')
@require_login
def index():
    """Main Flow dashboard/inbox."""
    user = get_current_user()
    conversations = get_user_conversations(user['id'])
    
    # Get channels
    channels = get_all('''
        SELECT fc.id, fc.name, fc.description, fc.avatar_url, fc.channel_type, fc.category,
               fc.is_archived, fc.created_by, fc.created_at, fc.updated_at, fc.settings, fc.invite_code, fc.channel_id,
               (SELECT COUNT(*) FROM flow_channel_members WHERE channel_id = fc.id) as member_count
        FROM flow_channels fc
        JOIN flow_channel_members fcm ON fc.id = fcm.channel_id
        WHERE fcm.user_id = ?
        ORDER BY fc.name
    ''', (user['id'],))
    
    # Get groups
    groups = get_all('''
        SELECT fg.id, fg.name, fg.description, fg.avatar_url, fg.group_type, fg.created_by,
               fg.created_at, fg.updated_at, fg.settings,
               (SELECT COUNT(*) FROM flow_group_members WHERE group_id = fg.id) as member_count
        FROM flow_groups fg
        JOIN flow_group_members fgm ON fg.id = fgm.group_id
        WHERE fgm.user_id = ?
        ORDER BY fg.name
    ''', (user['id'],))
    
    # Get unread count
    unread_count = sum(c.get('unread_count', 0) for c in conversations)
    
    # Get notifications
    notifications = get_all('''
        SELECT * FROM flow_notifications
        WHERE user_id = ? AND is_read = 0
        ORDER BY created_at DESC
        LIMIT 10
    ''', (user['id'],))
    
    # Get user status
    status = get_user_status(user['id'])
    
    # Get profile
    profile = get_flow_profile(user['id'])
    
    return render_template('flow/index.html',
        user=user,
        profile=profile,
        status=status,
        conversations=conversations,
        channels=channels,
        groups=groups,
        notifications=notifications,
        unread_count=unread_count,
        page_title='Flow',
        direction=get_user_direction()
    )


@flow_bp.route('/chat/<conversation_id>')
@require_login
def chat_view(conversation_id):
    """Open a specific conversation/chat."""
    user = get_current_user()
    
    # Get conversation details
    conversation = get_one('''
        SELECT * FROM flow_conversations WHERE id = ?
    ''', (conversation_id,))
    
    if not conversation:
        return render_template('flow/error.html', error='Conversation not found', user=user), 404
    
    # Check if user is a member
    membership = get_one('''
        SELECT * FROM flow_conversation_members
        WHERE conversation_id = ? AND user_id = ?
    ''', (conversation_id, user['id']))
    
    if not membership:
        return render_template('flow/error.html', error='Access denied', user=user), 403
    
    # Get messages
    messages = get_conversation_messages(conversation_id, user['id'], limit=100)
    
    # Mark as read and clear mentions
    with get_db_context() as db:
        db.execute('''
            UPDATE flow_conversation_members
            SET unread_count = 0, last_read_at = ?
            WHERE conversation_id = ? AND user_id = ?
        ''', (datetime.now().isoformat(), conversation_id, user['id']))

        # Clear mentions for this conversation
        db.execute('''
            DELETE FROM flow_message_mentions
            WHERE user_id = ? AND message_id IN (
                SELECT id FROM flow_messages WHERE conversation_id = ?
            )
        ''', (user['id'], conversation_id))
    
    # Get other members for private chat
    other_members = []
    if conversation['conversation_type'] == 'private':
        members = get_all('''
            SELECT fcm.*, fup.display_name, fup.avatar_url, fup.username,
                   fus.status_type as user_status
            FROM flow_conversation_members fcm
            LEFT JOIN flow_user_profiles fup ON fcm.user_id = fup.user_id
            LEFT JOIN flow_user_status fus ON fcm.user_id = fus.user_id
                AND (fus.status_expires_at IS NULL OR fus.status_expires_at > ?)
            WHERE fcm.conversation_id = ? AND fcm.user_id != ?
        ''', (datetime.now().isoformat(), conversation_id, user['id']))
        
        # If this is Save Messages (self-chat), show different info
        if conversation.get('name') == 'Save Messages':
            conversation['is_save_messages'] = True
            profile = get_flow_profile(user['id'])
            other_members = [{
                'user_id': user['id'],
                'display_name': profile['display_name'] if profile else user['username'],
                'avatar_url': profile['avatar_url'] if profile else None,
                'username': profile['username'] if profile else user['username']
            }]
        else:
            other_members = members
    elif conversation['conversation_type'] == 'group':
        members = get_all('''
            SELECT fgm.*, fup.display_name, fup.avatar_url, fup.username,
                   fus.status_type as user_status
            FROM flow_group_members fgm
            LEFT JOIN flow_user_profiles fup ON fgm.user_id = fup.user_id
            LEFT JOIN flow_user_status fus ON fgm.user_id = fus.user_id
                AND (fus.status_expires_at IS NULL OR fus.status_expires_at > ?)
            WHERE fgm.group_id = (
                SELECT id FROM flow_groups WHERE id = ? OR name = ?
            )
        ''', (datetime.now().isoformat(), conversation_id, conversation.get('name')))
        other_members = members
    else:  # channel
        members = get_all('''
            SELECT fcm.*, fup.display_name, fup.avatar_url, fup.username,
                   fus.status_type as user_status
            FROM flow_channel_members fcm
            LEFT JOIN flow_user_profiles fup ON fcm.user_id = fup.user_id
            LEFT JOIN flow_user_status fus ON fcm.user_id = fus.user_id
                AND (fus.status_expires_at IS NULL OR fus.status_expires_at > ?)
            WHERE fcm.channel_id = (
                SELECT id FROM flow_channels WHERE id = ? OR name = ?
            )
        ''', (datetime.now().isoformat(), conversation_id, conversation.get('name')))
        other_members = members
    
    # Get shared media
    shared_media = get_shared_media(conversation_id=conversation_id)[:20]
    
    profile = get_flow_profile(user['id'])
    status = get_user_status(user['id'])
    settings_data = get_user_settings(user['id'])
    
    return render_template('flow/chat.html',
        user=user,
        profile=profile,
        status=status,
        conversation=conversation,
        messages=messages,
        other_members=other_members,
        shared_media=shared_media,
        settings=settings_data,
        page_title=conversation.get('name', 'Chat'),
        direction=get_user_direction()
    )


@flow_bp.route('/api/conversations')
@require_login
def api_conversations():
    """Get all conversations for current user."""
    user = get_current_user()
    conversations = get_user_conversations(user['id'], includeArchived=True)
    return jsonify({'conversations': conversations})


@flow_bp.route('/api/conversations/<conversation_id>/messages')
@require_login
def api_messages(conversation_id):
    """Get messages for a conversation."""
    user = get_current_user()
    before = request.args.get('before')
    limit = int(request.args.get('limit', 50))

    messages = get_conversation_messages(conversation_id, user['id'], limit=limit, before=before)

    # Clear mentions for this conversation when user views it
    with get_db_context() as db:
        db.execute('''
            DELETE FROM flow_message_mentions
            WHERE user_id = ? AND message_id IN (
                SELECT id FROM flow_messages WHERE conversation_id = ?
            )
        ''', (user['id'], conversation_id))

    return jsonify({'messages': messages})


@flow_bp.route('/api/conversations/<conversation_id>/members')
@require_login
def api_conversation_members(conversation_id):
    """Get members of a conversation."""
    user = get_current_user()

    # Check if user is a member
    membership = get_one('''
        SELECT * FROM flow_conversation_members
        WHERE conversation_id = ? AND user_id = ?
    ''', (conversation_id, user['id']))

    if not membership:
        return jsonify({'error': 'Access denied'}), 403

    # Get conversation details
    conversation = get_one('SELECT * FROM flow_conversations WHERE id = ?', (conversation_id,))
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404

    # Get all members
    members = get_all('''
        SELECT fcm.*, fup.display_name, fup.avatar_url, fup.username, fup.job_title,
               fus.status_type as user_status
        FROM flow_conversation_members fcm
        LEFT JOIN flow_user_profiles fup ON fcm.user_id = fup.user_id
        LEFT JOIN flow_user_status fus ON fcm.user_id = fus.user_id
            AND (fus.status_expires_at IS NULL OR fus.status_expires_at > ?)
        WHERE fcm.conversation_id = ?
        ORDER BY fcm.role ASC, fup.display_name ASC
    ''', (datetime.now().isoformat(), conversation_id))

    return jsonify({
        'conversation': {
            'id': conversation['id'],
            'name': conversation['name'],
            'type': conversation['conversation_type']
        },
        'members': members,
        'current_user_role': membership['role']
    })


@flow_bp.route('/api/messages/send', methods=['POST'])
@require_login
def api_send_message():
    """Send a new message."""
    import traceback

    try:
        user = get_current_user()

        # Check rate limit
        allowed, remaining, retry_after = check_message_rate_limit(user['id'])
        if not allowed:
            return jsonify({
                'error': 'Too many messages. Please wait before sending again.',
                'retry_after': retry_after,
                'remaining': remaining
            }), 429

        data = safe_get_json()

        conversation_id = data.get('conversation_id')
        content = data.get('content', '')
        message_type = data.get('message_type', 'text')
        reply_to_id = data.get('reply_to_id')
        metadata = data.get('metadata')

        logger.debug(f'api_send_message called: user={user["id"]}, conv={conversation_id}, content={content[:50] if content else "empty"}...')

        if not conversation_id:
            return jsonify({'error': 'Conversation ID required'}), 400

        # Validate content length
        if len(content) > 10000:
            return jsonify({'error': 'Message too long (max 10000 characters)'}), 400

        # Check membership
        membership = get_one('''
            SELECT * FROM flow_conversation_members WHERE conversation_id = ? AND user_id = ?
        ''', (conversation_id, user['id']))

        if not membership:
            logger.warning(f'Access denied for user {user["id"]} to conversation {conversation_id}')
            user_convs = get_all('SELECT * FROM flow_conversation_members WHERE user_id = ?', (user['id'],))
            logger.debug(f'User conversations: {[c["conversation_id"] for c in user_convs]}')
            return jsonify({'error': 'Access denied'}), 403

        msg_id = send_message(conversation_id, user['id'], content, message_type, reply_to_id, metadata)
        logger.debug(f'send_message returned msg_id={msg_id}')

        # Get the created message
        message = get_one('''
            SELECT m.*, fup.display_name as sender_name, fup.avatar_url as sender_avatar
            FROM flow_messages m
            LEFT JOIN flow_user_profiles fup ON m.sender_id = fup.user_id
            WHERE m.id = ?
        ''', (msg_id,))

        logger.debug(f'get_one returned message={message}')

        return jsonify({'success': True, 'message': message, 'remaining': remaining - 1})
    except Exception as e:
        logger.exception(f'Exception in api_send_message: {e}')
        return jsonify({'error': str(e)}), 500


@flow_bp.route('/api/messages/<message_id>/react', methods=['POST'])
@require_login
def api_react_message(message_id):
    """Add reaction to a message."""
    user = get_current_user()
    data = safe_get_json()
    emoji = data.get('emoji')

    if not emoji:
        return jsonify({'error': 'Emoji required'}), 400

    add_reaction(message_id, user['id'], emoji)
    return jsonify({'success': True})


@flow_bp.route('/api/messages/<message_id>/unreact', methods=['POST'])
@require_login
def api_unreact_message(message_id):
    """Remove reaction from a message."""
    user = get_current_user()
    data = safe_get_json()
    emoji = data.get('emoji')

    if not emoji:
        return jsonify({'error': 'Emoji required'}), 400

    remove_reaction(message_id, user['id'], emoji)
    return jsonify({'success': True})


@flow_bp.route('/api/messages/<message_id>/react/toggle', methods=['POST'])
@require_login
def api_toggle_reaction(message_id):
    """Toggle a reaction on a message - adds if not present, removes if present."""
    user = get_current_user()
    data = safe_get_json()
    emoji = data.get('emoji', '👍')

    if not emoji:
        return jsonify({'error': 'Emoji required'}), 400

    # Check if user already reacted with this emoji
    existing = get_one('''
        SELECT id FROM flow_message_reactions
        WHERE message_id = ? AND user_id = ? AND emoji = ?
    ''', (message_id, user['id'], emoji))

    if existing:
        remove_reaction(message_id, user['id'], emoji)
        action = 'removed'
    else:
        add_reaction(message_id, user['id'], emoji)
        action = 'added'

    # Return updated reactions for this message
    reactions = get_all('''
        SELECT emoji, user_id FROM flow_message_reactions WHERE message_id = ?
    ''', (message_id,))

    reaction_dict = {}
    for r in reactions:
        if r['emoji'] not in reaction_dict:
            reaction_dict[r['emoji']] = []
        reaction_dict[r['emoji']].append(r['user_id'])

    return jsonify({
        'success': True,
        'action': action,
        'emoji': emoji,
        'reactions': reaction_dict,
        'user_reacted': action == 'added'
    })


@flow_bp.route('/api/messages/<message_id>/context-action', methods=['POST'])
@require_login
def api_message_context_action(message_id):
    """Handle context menu actions on a message: copy, edit, delete, forward, pin, save."""
    user = get_current_user()
    data = safe_get_json()
    action = data.get('action')
    content = data.get('content')  # For edit

    if not action:
        return jsonify({'error': 'Action required'}), 400

    # Get the message
    message = get_one('SELECT * FROM flow_messages WHERE id = ?', (message_id,))
    if not message:
        return jsonify({'error': 'Message not found'}), 404

    if message.get('is_deleted'):
        return jsonify({'error': 'Message has been deleted'}), 400

    # Check conversation membership for access
    membership = get_one('''
        SELECT * FROM flow_conversation_members
        WHERE conversation_id = ? AND user_id = ?
    ''', (message['conversation_id'], user['id']))
    if not membership:
        return jsonify({'error': 'Access denied'}), 403

    if action == 'copy':
        # Return message content for copying
        return jsonify({
            'success': True,
            'action': 'copy',
            'content': message.get('content', '')
        })

    elif action == 'edit':
        # Check ownership
        if message['sender_id'] != user['id']:
            return jsonify({'error': 'Cannot edit this message'}), 403
        # Check message age (24 hours)
        from datetime import datetime
        created_at = datetime.fromisoformat(message['created_at']) if message['created_at'] else None
        if created_at:
            age_hours = (datetime.now() - created_at).total_seconds() / 3600
            if age_hours > 24:
                return jsonify({'error': 'Message is too old to edit'}), 400

        if content is None:
            return jsonify({'error': 'Content required for edit'}), 400

        with get_db_context() as db:
            db.execute('''
                UPDATE flow_messages
                SET content = ?, is_edited = 1, edited_at = ?
                WHERE id = ?
            ''', (content, datetime.now().isoformat(), message_id))

        updated = get_one('''
            SELECT m.*, fup.display_name as sender_name, fup.avatar_url as sender_avatar
            FROM flow_messages m
            LEFT JOIN flow_user_profiles fup ON m.sender_id = fup.user_id
            WHERE m.id = ?
        ''', (message_id,))
        return jsonify({'success': True, 'action': 'edit', 'message': updated})

    elif action == 'delete':
        if message['sender_id'] != user['id']:
            return jsonify({'error': 'Cannot delete this message'}), 403

        delete_scope = data.get('scope', 'me')
        with get_db_context() as db:
            if delete_scope == 'everyone':
                db.execute('DELETE FROM flow_messages WHERE id = ?', (message_id,))
            else:
                db.execute('''
                    UPDATE flow_messages
                    SET is_deleted = 1, deleted_at = ?, delete_scope = 'me'
                    WHERE id = ?
                ''', (datetime.now().isoformat(), message_id))
        return jsonify({'success': True, 'action': 'delete', 'scope': delete_scope})

    elif action == 'forward':
        target_conversation_id = data.get('conversation_id')
        if not target_conversation_id:
            return jsonify({'error': 'Target conversation ID required'}), 400

        target_membership = get_one('''
            SELECT * FROM flow_conversation_members WHERE conversation_id = ? AND user_id = ?
        ''', (target_conversation_id, user['id']))
        if not target_membership:
            return jsonify({'error': 'Access denied to target conversation'}), 403

        new_msg_id = send_message(
            conversation_id=target_conversation_id,
            sender_id=user['id'],
            content=message['content'],
            message_type=message['message_type'],
            reply_to_id=None,
            metadata=json.dumps({
                'forwarded_from_id': message_id,
                'original_sender': message['sender_id'],
                'original_conversation': message['conversation_id']
            })
        )
        return jsonify({'success': True, 'action': 'forward', 'message_id': new_msg_id})

    elif action == 'pin':
        # Check if already pinned
        if message.get('is_pinned'):
            # Unpin
            with get_db_context() as db:
                db.execute('UPDATE flow_messages SET is_pinned = 0 WHERE id = ?', (message_id,))
            return jsonify({'success': True, 'action': 'unpin'})
        else:
            # Pin
            with get_db_context() as db:
                db.execute('UPDATE flow_messages SET is_pinned = 1 WHERE id = ?', (message_id,))
            return jsonify({'success': True, 'action': 'pin'})

    elif action == 'save':
        # Toggle save
        existing = get_one('''
            SELECT id FROM flow_saved_messages WHERE user_id = ? AND message_id = ?
        ''', (user['id'], message_id))
        if existing:
            with get_db_context() as db:
                db.execute('DELETE FROM flow_saved_messages WHERE id = ?', (existing['id'],))
            return jsonify({'success': True, 'action': 'unsave'})
        else:
            saved_id = generate_id()
            with get_db_context() as db:
                db.execute('''
                    INSERT INTO flow_saved_messages (id, user_id, message_id, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (saved_id, user['id'], message_id, datetime.now().isoformat()))
            return jsonify({'success': True, 'action': 'save'})

    else:
        return jsonify({'error': f'Unknown action: {action}'}), 400


@flow_bp.route('/api/messages/<message_id>/reminder', methods=['POST'])
@require_login
def api_set_reminder(message_id):
    """Set a reminder on a message."""
    user = get_current_user()
    data = safe_get_json()
    
    remind_at = data.get('remind_at')
    reminder_text = data.get('reminder_text')
    
    if not remind_at:
        return jsonify({'error': 'Reminder time required'}), 400
    
    set_reminder(user['id'], message_id, remind_at, reminder_text)
    return jsonify({'success': True})


@flow_bp.route('/api/messages/<message_id>/edit', methods=['POST'])
@require_login
def api_edit_message(message_id):
    """Edit a message."""
    user = get_current_user()
    data = safe_get_json()
    content = data.get('content')

    if content is None:
        return jsonify({'error': 'Content required'}), 400

    # Validate message_id from URL matches any in payload (defense in depth)
    payload_msg_id = data.get('message_id')
    if payload_msg_id and payload_msg_id != message_id:
        return jsonify({'error': 'Message ID mismatch'}), 400

    # Check ownership and that message exists
    message = get_one('SELECT * FROM flow_messages WHERE id = ?', (message_id,))
    if not message:
        return jsonify({'error': 'Message not found'}), 404
    if message['sender_id'] != user['id']:
        return jsonify({'error': 'Cannot edit this message'}), 403

    # Check if message is deleted
    if message.get('is_deleted'):
        return jsonify({'error': 'Cannot edit deleted message'}), 400

    # Check message was created within edit window (e.g., 24 hours)
    from datetime import datetime
    created_at = datetime.fromisoformat(message['created_at']) if message['created_at'] else None
    if created_at:
        age_hours = (datetime.now() - created_at).total_seconds() / 3600
        if age_hours > 24:
            return jsonify({'error': 'Message is too old to edit'}), 400

    with get_db_context() as db:
        db.execute('''
            UPDATE flow_messages
            SET content = ?, is_edited = 1, edited_at = ?
            WHERE id = ?
        ''', (content, datetime.now().isoformat(), message_id))

    # Return the updated message
    updated_message = get_one('''
        SELECT m.*, fup.display_name as sender_name, fup.avatar_url as sender_avatar
        FROM flow_messages m
        LEFT JOIN flow_user_profiles fup ON m.sender_id = fup.user_id
        WHERE m.id = ?
    ''', (message_id,))

    return jsonify({'success': True, 'message': updated_message})


@flow_bp.route('/api/messages/<message_id>/delete', methods=['POST'])
@require_login
def api_delete_message(message_id):
    """Delete a message."""
    user = get_current_user()
    data = safe_get_json() or {}
    delete_scope = data.get('scope', 'me')  # 'me' or 'everyone'

    # Check ownership
    message = get_one('SELECT * FROM flow_messages WHERE id = ?', (message_id,))
    if not message:
        return jsonify({'error': 'Message not found'}), 404

    if message['sender_id'] != user['id']:
        return jsonify({'error': 'Cannot delete this message'}), 403

    with get_db_context() as db:
        if delete_scope == 'everyone':
            # Delete the message completely for everyone
            db.execute('DELETE FROM flow_messages WHERE id = ?', (message_id,))
        else:
            # Soft delete - only for the current user
            db.execute('''
                UPDATE flow_messages
                SET is_deleted = 1, deleted_at = ?, delete_scope = 'me'
                WHERE id = ?
            ''', (datetime.now().isoformat(), message_id))

    return jsonify({'success': True})


@flow_bp.route('/api/messages/<message_id>/forward', methods=['POST'])
@require_login
def api_forward_message(message_id):
    """Forward a message to another conversation."""
    user = get_current_user()
    data = safe_get_json()

    target_conversation_id = data.get('conversation_id')
    if not target_conversation_id:
        return jsonify({'error': 'Target conversation ID required'}), 400

    # Check if user has access to target conversation
    membership = get_one('''
        SELECT * FROM flow_conversation_members WHERE conversation_id = ? AND user_id = ?
    ''', (target_conversation_id, user['id']))

    if not membership:
        return jsonify({'error': 'Access denied to target conversation'}), 403

    # Get the original message
    original_message = get_one('SELECT * FROM flow_messages WHERE id = ?', (message_id,))
    if not original_message:
        return jsonify({'error': 'Original message not found'}), 404

    # Create forwarded message
    from flow_models import send_message
    new_msg_id = send_message(
        conversation_id=target_conversation_id,
        sender_id=user['id'],
        content=original_message['content'],
        message_type=original_message['message_type'],
        reply_to_id=None,  # Don't carry over reply reference
        metadata=json.dumps({
            'forwarded_from_id': message_id,
            'original_sender': original_message['sender_id'],
            'original_conversation': original_message['conversation_id']
        })
    )

    return jsonify({'success': True, 'message_id': new_msg_id})


@flow_bp.route('/api/messages/<message_id>/pin', methods=['POST'])
@require_login
def api_pin_message(message_id):
    """Pin a message."""
    user = get_current_user()

    # Check message exists
    message = get_one('SELECT * FROM flow_messages WHERE id = ?', (message_id,))
    if not message:
        return jsonify({'error': 'Message not found'}), 404

    # Check user has access to this conversation
    membership = get_one('''
        SELECT * FROM flow_conversation_members
        WHERE conversation_id = ? AND user_id = ?
    ''', (message['conversation_id'], user['id']))
    if not membership:
        return jsonify({'error': 'Access denied'}), 403

    # Only message sender, channel admins, group admins/owners can pin
    conversation = get_one('SELECT * FROM flow_conversations WHERE id = ?', (message['conversation_id'],))
    can_pin = False

    if message['sender_id'] == user['id']:
        can_pin = True
    elif conversation['conversation_type'] == 'channel':
        channel = get_one('SELECT id FROM flow_channels WHERE name = ?', (conversation['name'],))
        if channel:
            member = get_one('SELECT role FROM flow_channel_members WHERE channel_id = ? AND user_id = ?', (channel['id'], user['id']))
            if member and member['role'] in ('admin', 'owner'):
                can_pin = True
    elif conversation['conversation_type'] == 'group':
        group = get_one('SELECT id FROM flow_groups WHERE name = ?', (conversation['name'],))
        if group:
            member = get_one('SELECT role FROM flow_group_members WHERE group_id = ? AND user_id = ?', (group['id'], user['id']))
            if member and member['role'] in ('admin', 'owner'):
                can_pin = True
    else:  # private chat - only sender can pin
        can_pin = message['sender_id'] == user['id']

    if not can_pin:
        return jsonify({'error': 'Permission denied'}), 403

    with get_db_context() as db:
        db.execute('UPDATE flow_messages SET is_pinned = 1 WHERE id = ?', (message_id,))

    return jsonify({'success': True})


@flow_bp.route('/api/messages/<message_id>/unpin', methods=['POST'])
@require_login
def api_unpin_message(message_id):
    """Unpin a message."""
    user = get_current_user()

    # Check message exists
    message = get_one('SELECT * FROM flow_messages WHERE id = ?', (message_id,))
    if not message:
        return jsonify({'error': 'Message not found'}), 404

    # Check user has access to this conversation
    membership = get_one('''
        SELECT * FROM flow_conversation_members
        WHERE conversation_id = ? AND user_id = ?
    ''', (message['conversation_id'], user['id']))
    if not membership:
        return jsonify({'error': 'Access denied'}), 403

    # Only message sender, channel admins, group admins/owners can unpin
    conversation = get_one('SELECT * FROM flow_conversations WHERE id = ?', (message['conversation_id'],))
    can_unpin = False

    if message['sender_id'] == user['id']:
        can_unpin = True
    elif conversation['conversation_type'] == 'channel':
        channel = get_one('SELECT id FROM flow_channels WHERE name = ?', (conversation['name'],))
        if channel:
            member = get_one('SELECT role FROM flow_channel_members WHERE channel_id = ? AND user_id = ?', (channel['id'], user['id']))
            if member and member['role'] in ('admin', 'owner'):
                can_unpin = True
    elif conversation['conversation_type'] == 'group':
        group = get_one('SELECT id FROM flow_groups WHERE name = ?', (conversation['name'],))
        if group:
            member = get_one('SELECT role FROM flow_group_members WHERE group_id = ? AND user_id = ?', (group['id'], user['id']))
            if member and member['role'] in ('admin', 'owner'):
                can_unpin = True
    else:  # private chat - only sender can unpin
        can_unpin = message['sender_id'] == user['id']

    if not can_unpin:
        return jsonify({'error': 'Permission denied'}), 403

    with get_db_context() as db:
        db.execute('UPDATE flow_messages SET is_pinned = 0 WHERE id = ?', (message_id,))

    return jsonify({'success': True})


@flow_bp.route('/api/conversations/<conversation_id>/pin', methods=['POST'])
@require_login
def api_pin_conversation(conversation_id):
    """Pin a conversation."""
    user = get_current_user()
    
    # Check if user is a member
    membership = get_one('''
        SELECT * FROM flow_conversation_members WHERE conversation_id = ? AND user_id = ?
    ''', (conversation_id, user['id']))
    
    if not membership:
        return jsonify({'error': 'Access denied'}), 403
    
    # Count current pinned conversations for this user
    pinned_count = get_one('''
        SELECT COUNT(*) as count FROM flow_conversation_members
        WHERE user_id = ? AND is_pinned = 1
    ''', (user['id']))
    
    if pinned_count and pinned_count['count'] >= 10:
        return jsonify({'error': 'Maximum 10 pinned conversations allowed'}), 400
    
    with get_db_context() as db:
        db.execute('''
            UPDATE flow_conversation_members
            SET is_pinned = 1
            WHERE conversation_id = ? AND user_id = ?
        ''', (conversation_id, user['id']))
    
    return jsonify({'success': True})


@flow_bp.route('/api/conversations/<conversation_id>/unpin', methods=['POST'])
@require_login
def api_unpin_conversation(conversation_id):
    """Unpin a conversation."""
    user = get_current_user()
    
    with get_db_context() as db:
        db.execute('''
            UPDATE flow_conversation_members
            SET is_pinned = 0
            WHERE conversation_id = ? AND user_id = ?
        ''', (conversation_id, user['id']))
    
    return jsonify({'success': True})


@flow_bp.route('/api/conversations/<conversation_id>/mute', methods=['POST'])
@require_login
def api_mute_conversation(conversation_id):
    """Mute/unmute a conversation."""
    user = get_current_user()
    data = safe_get_json()
    mute = data.get('mute', True)
    
    with get_db_context() as db:
        db.execute('''
            UPDATE flow_conversation_members
            SET is_muted = ?, notifications_enabled = ?
            WHERE conversation_id = ? AND user_id = ?
        ''', (1 if mute else 0, 0 if mute else 1, conversation_id, user['id']))
    
    return jsonify({'success': True})


@flow_bp.route('/api/conversations/<conversation_id>/archive', methods=['POST'])
@require_login
def api_archive_conversation(conversation_id):
    """Archive/unarchive a conversation."""
    user = get_current_user()
    
    # Toggle current state
    membership = get_one('''
        SELECT is_archived FROM flow_conversation_members
        WHERE conversation_id = ? AND user_id = ?
    ''', (conversation_id, user['id']))
    
    if not membership:
        return jsonify({'error': 'Access denied'}), 403
    
    new_state = 0 if membership['is_archived'] else 1
    
    with get_db_context() as db:
        db.execute('''
            UPDATE flow_conversation_members
            SET is_archived = ?
            WHERE conversation_id = ? AND user_id = ?
        ''', (new_state, conversation_id, user['id']))
        
        db.execute('''
            UPDATE flow_conversations
            SET is_archived = ?
            WHERE id = ?
        ''', (new_state, conversation_id))
    
    return jsonify({'success': True})


@flow_bp.route('/api/conversations/<conversation_id>/delete', methods=['POST'])
@require_login
def api_delete_conversation(conversation_id):
    """Delete a conversation permanently (both sides) - for private chats only."""
    user = get_current_user()
    data = safe_get_json()
    delete_scope = data.get('scope', 'me')

    membership = get_one('''
        SELECT * FROM flow_conversation_members
        WHERE conversation_id = ? AND user_id = ?
    ''', (conversation_id, user['id']))

    if not membership:
        return jsonify({'error': 'Access denied'}), 403

    conversation = get_one('SELECT * FROM flow_conversations WHERE id = ?', (conversation_id,))

    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404

    # Only allow 'everyone' delete for private chats
    if delete_scope == 'everyone' and conversation['conversation_type'] == 'private':
        with get_db_context() as db:
            # Delete all messages first (foreign key constraint)
            db.execute('DELETE FROM flow_messages WHERE conversation_id = ?', (conversation_id,))
            db.execute('DELETE FROM flow_conversation_members WHERE conversation_id = ?', (conversation_id,))
            db.execute('DELETE FROM flow_conversations WHERE id = ?', (conversation_id,))
    else:
        return jsonify({'error': 'Cannot delete permanently. Only private chats can be deleted by both parties.'}), 400

    return jsonify({'success': True})


@flow_bp.route('/api/conversations/<conversation_id>/remove', methods=['POST'])
@require_login
def api_remove_conversation(conversation_id):
    """Remove a conversation from user's list (one-sided hide)."""
    user = get_current_user()

    membership = get_one('''
        SELECT * FROM flow_conversation_members
        WHERE conversation_id = ? AND user_id = ?
    ''', (conversation_id, user['id']))

    if not membership:
        return jsonify({'error': 'Access denied'}), 403

    with get_db_context() as db:
        db.execute('''
            UPDATE flow_conversation_members
            SET is_archived = 1
            WHERE conversation_id = ? AND user_id = ?
        ''', (conversation_id, user['id']))

        db.execute('''
            UPDATE flow_conversations
            SET is_archived = 1
            WHERE id = ?
        ''', (conversation_id,))

    return jsonify({'success': True})


@flow_bp.route('/api/conversations/<conversation_id>/mark-unread', methods=['POST'])
@require_login
def api_mark_unread_conversation(conversation_id):
    """Mark a conversation as unread."""
    user = get_current_user()
    
    with get_db_context() as db:
        db.execute('''
            UPDATE flow_conversation_members
            SET unread_count = 1
            WHERE conversation_id = ? AND user_id = ?
        ''', (conversation_id, user['id']))
    
    return jsonify({'success': True})


# ============================================================================
# PRIVATE CHAT ROUTES
# ============================================================================

@flow_bp.route('/new-chat')
@require_login
def new_chat():
    """Start a new private chat."""
    user = get_current_user()
    
    # Get all users except current
    users = get_all('''
        SELECT u.id, u.username, fup.display_name, fup.avatar_url, fup.department
        FROM users u
        LEFT JOIN flow_user_profiles fup ON u.id = fup.user_id
        WHERE u.id != ?
        ORDER BY fup.display_name
    ''', (user['id'],))
    
    profile = get_flow_profile(user['id'])
    status = get_user_status(user['id'])
    
    return render_template('flow/new_chat.html',
        user=user,
        profile=profile,
        status=status,
        users=users,
        page_title='New Chat',
        direction=get_user_direction()
    )


@flow_bp.route('/api/chat/start', methods=['POST'])
@require_login
def api_start_chat():
    """Start or get existing private chat with a user."""
    user = get_current_user()
    data = safe_get_json() or {}
    other_user_id = data.get('user_id')
    
    if not other_user_id:
        return jsonify({'error': 'User ID required'}), 400
    
    try:
        other_user_id = int(other_user_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid user ID'}), 400

    try:
        conv_id = get_or_create_private_conversation(user['id'], other_user_id)
        if not conv_id:
            return jsonify({'error': 'Could not create conversation'}), 500
        return jsonify({'success': True, 'conversation_id': conv_id})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============================================================================
# CHANNEL ROUTES
# ============================================================================

@flow_bp.route('/channels')
@require_login
def channels():
    """List all channels."""
    user = get_current_user()
    
    # Get all channels
    all_channels = get_all('''
        SELECT fc.id, fc.name, fc.description, fc.avatar_url, fc.channel_type, fc.category,
               fc.is_archived, fc.created_by, fc.created_at, fc.updated_at, fc.settings, fc.invite_code, fc.channel_id,
               fcm.role,
               (SELECT COUNT(*) FROM flow_channel_members WHERE channel_id = fc.id) as member_count,
               (SELECT COUNT(*) FROM flow_messages m WHERE m.conversation_id = 
                   (SELECT id FROM flow_conversations WHERE name = fc.name AND conversation_type = 'channel')
               ) as message_count
        FROM flow_channels fc
        LEFT JOIN flow_channel_members fcm ON fc.id = fcm.channel_id AND fcm.user_id = ?
        ORDER BY fc.category, fc.name
    ''', (user['id'],))
    
    profile = get_flow_profile(user['id'])
    status = get_user_status(user['id'])
    
    # Group by category
    categories = {}
    for ch in all_channels:
        cat = ch.get('category', 'Other')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(ch)
    
    return render_template('flow/channels.html',
        user=user,
        profile=profile,
        status=status,
        channels=all_channels,
        categories=categories,
        page_title='Channels'
    )


@flow_bp.route('/channels/create')
@require_login
def create_channel_page():
    """Create a new channel."""
    user = get_current_user()
    
    profile = get_flow_profile(user['id'])
    status = get_user_status(user['id'])
    
    if not user_has_permission(user['id'], 'flow', 'channels', 'create'):
        # Build full context for error page (which extends flow/index.html)
        error_conversations = get_user_conversations(user['id'])
        error_channels = get_all('''
            SELECT fc.id, fc.name, fc.description, fc.avatar_url, fc.channel_type, fc.category,
                   fc.is_archived, fc.created_by, fc.created_at, fc.updated_at, fc.settings, fc.invite_code, fc.channel_id,
                   (SELECT COUNT(*) FROM flow_channel_members WHERE channel_id = fc.id) as member_count
            FROM flow_channels fc JOIN flow_channel_members fcm ON fc.id = fcm.channel_id
            WHERE fcm.user_id = ? ORDER BY fc.name
        ''', (user['id'],))
        error_groups = get_all('''
            SELECT fg.id, fg.name, fg.description, fg.avatar_url, fg.group_type, fg.created_by,
                   fg.created_at, fg.updated_at, fg.settings,
                   (SELECT COUNT(*) FROM flow_group_members WHERE group_id = fg.id) as member_count
            FROM flow_groups fg JOIN flow_group_members fgm ON fg.id = fgm.group_id
            WHERE fgm.user_id = ? ORDER BY fg.name
        ''', (user['id'],))
        error_notifications = get_all('''
            SELECT * FROM flow_notifications WHERE user_id = ? AND is_read = 0 ORDER BY created_at DESC LIMIT 10
        ''', (user['id'],))
        error_unread_count = sum(c.get('unread_count', 0) for c in error_conversations)
        return render_template('flow/error.html',
            error='Permission denied', user=user, profile=profile, status=status,
            conversations=error_conversations, channels=error_channels, groups=error_groups,
            notifications=error_notifications, unread_count=error_unread_count,
            page_title='Permission Denied', direction=get_user_direction()
        ), 403
    
    # Get categories
    categories = get_all('SELECT * FROM flow_channel_categories ORDER BY sort_order')
    
    # Get conversations for sidebar
    conversations = get_user_conversations(user['id'])
    
    # Get channels for sidebar
    channels = get_all('''
        SELECT fc.id, fc.name, fc.description, fc.avatar_url, fc.channel_type, fc.category,
               fc.is_archived, fc.created_by, fc.created_at, fc.updated_at, fc.settings, fc.invite_code, fc.channel_id,
               (SELECT COUNT(*) FROM flow_channel_members WHERE channel_id = fc.id) as member_count
        FROM flow_channels fc
        JOIN flow_channel_members fcm ON fc.id = fcm.channel_id
        WHERE fcm.user_id = ?
        ORDER BY fc.name
    ''', (user['id'],))
    
    # Get groups for sidebar
    groups = get_all('''
        SELECT fg.id, fg.name, fg.description, fg.avatar_url, fg.group_type, fg.created_by,
               fg.created_at, fg.updated_at, fg.settings,
               (SELECT COUNT(*) FROM flow_group_members WHERE group_id = fg.id) as member_count
        FROM flow_groups fg
        JOIN flow_group_members fgm ON fg.id = fgm.group_id
        WHERE fgm.user_id = ?
        ORDER BY fg.name
    ''', (user['id'],))
    
    # Get unread count
    unread_count = sum(c.get('unread_count', 0) for c in conversations)
    
    # Get notifications
    notifications = get_all('''
        SELECT * FROM flow_notifications
        WHERE user_id = ? AND is_read = 0
        ORDER BY created_at DESC
        LIMIT 10
    ''', (user['id'],))
    
    return render_template('flow/create_channel.html',
        user=user,
        profile=profile,
        status=status,
        categories=categories,
        conversations=conversations,
        channels=channels,
        groups=groups,
        notifications=notifications,
        unread_count=unread_count,
        page_title='Create Channel',
        direction=get_user_direction()
    )


@flow_bp.route('/api/channels/create', methods=['POST'])
@require_login
def api_create_channel():
    """Create a new channel."""
    user = get_current_user()
    data = safe_get_json()

    name = data.get('name')
    description = data.get('description', '')
    channel_type = data.get('channel_type', 'public')
    category = data.get('category')
    channel_id_val = data.get('channel_id')  # Custom URL-friendly ID
    invite_code = data.get('invite_code')  # For private channels

    if not name:
        return jsonify({'error': 'Channel name required'}), 400

    # For public channels, validate channel_id if provided
    if channel_type == 'public' and channel_id_val:
        if not validate_channel_id(channel_id_val):
            return jsonify({'error': 'Invalid Channel ID format. Use only lowercase letters, numbers, hyphens (-), and dots (.). Must be at least 3 characters.'}), 400

        if not is_channel_id_available(channel_id_val):
            return jsonify({'error': 'Channel ID is already taken. Please choose a different one.'}), 400

    # Create channel
    db_channel_id = create_channel(
        name=name,
        description=description,
        created_by=user['id'],
        channel_type=channel_type,
        category=category,
        channel_id=channel_id_val,
        invite_code=invite_code
    )

    return jsonify({'success': True, 'channel_db_id': db_channel_id})


@flow_bp.route('/api/channels/check-id')
@require_login
def api_check_channel_id():
    """Check if a channel ID is available."""
    channel_id = request.args.get('id', '').strip().lower()

    if not channel_id or len(channel_id) < 3:
        return jsonify({'available': False, 'message': 'ID too short'})

    if not validate_channel_id(channel_id):
        return jsonify({'available': False, 'message': 'Invalid format'})

    available = is_channel_id_available(channel_id)
    return jsonify({
        'available': available,
        'message': 'Available' if available else 'Already taken'
    })


@flow_bp.route('/api/channels/join-by-code', methods=['POST'])
@require_login
def api_join_by_code():
    """Join a private channel using an invite code."""
    user = get_current_user()
    data = safe_get_json()

    code = data.get('code', '').strip().upper()

    if not code:
        return jsonify({'error': 'Invite code required'}), 400

    if len(code) < 4:
        return jsonify({'error': 'Invalid invite code format'}), 400

    # Find channel by invite code
    channel = get_one('''
        SELECT id, name, description, avatar_url, channel_type, category,
               is_archived, created_by, created_at, updated_at, settings, invite_code, channel_id
        FROM flow_channels
        WHERE invite_code = ? AND channel_type = 'private'
    ''', (code,))

    if not channel:
        return jsonify({'error': 'Invalid or expired invite code'}), 404

    # Check if already a member
    existing = get_one('''
        SELECT * FROM flow_channel_members WHERE channel_id = ? AND user_id = ?
    ''', (channel['id'], user['id']))
    if existing:
        return jsonify({'error': 'You are already a member of this channel'}), 400

    # Add user as member
    with get_db_context() as db:
        db.execute('''
            INSERT OR IGNORE INTO flow_channel_members (channel_id, user_id, role)
            VALUES (?, ?, 'member')
        ''', (channel['id'], user['id']))

        # Also add to conversation
        conv = get_one('''
            SELECT id FROM flow_conversations
            WHERE name = ? AND conversation_type = 'channel'
        ''', (channel['name'],))

        if conv:
            db.execute('''
                INSERT OR IGNORE INTO flow_conversation_members (conversation_id, user_id, role)
                VALUES (?, ?, 'member')
            ''', (conv['id'], user['id']))

    log_audit(user['id'], 'channel_join_code', {'channel_id': channel['id'], 'channel_name': channel['name']}, 'flow')
    # Return channel_id (slug) for URL, preferring the friendly channel_id over UUID
    channel_url_id = channel['channel_id'] if channel['channel_id'] else channel['id']
    return jsonify({
        'success': True,
        'channel_id': channel_url_id,
        'channel_name': channel['name'],
        'redirect_url': f'/flow/channels/{channel_url_id}'
    })


@flow_bp.route('/api/channels/<channel_id>/regenerate-code', methods=['POST'])
@require_login
def api_regenerate_invite_code(channel_id):
    """Regenerate invite code for a private channel."""
    from flow_models import regenerate_invite_code

    user = get_current_user()

    channel = get_one('''
        SELECT id, name, description, avatar_url, channel_type, category,
               is_archived, created_by, created_at, updated_at, settings, invite_code, channel_id
        FROM flow_channels WHERE id = ?
    ''', (channel_id,))
    if not channel:
        return jsonify({'error': 'Channel not found'}), 404

    if channel['channel_type'] != 'private':
        return jsonify({'error': 'Only private channels have invite codes'}), 400

    # Check if user is admin
    membership = get_one('''
        SELECT role FROM flow_channel_members
        WHERE channel_id = ? AND user_id = ? AND role = 'admin'
    ''', (channel_id, user['id']))

    if not membership:
        return jsonify({'error': 'Permission denied'}), 403

    new_code = regenerate_invite_code(channel_id, user['id'])
    return jsonify({'success': True, 'invite_code': new_code})


@flow_bp.route('/api/seed/sample-channels', methods=['POST'])
@require_login
def api_seed_sample_channels():
    """Create sample channels with demo data."""
    user = get_current_user()

    # Only admin users can seed
    if not user_has_permission(user['id'], 'flow', 'channels', 'admin'):
        return jsonify({'error': 'Permission denied'}), 403

    result = seed_sample_channels()

    if result:
        return jsonify({'success': True, 'message': 'Sample channels created successfully'})
    else:
        return jsonify({'error': 'Failed to create sample channels'}), 500


# ============================================================================
# SHORT URL REDIRECTS FOR CHANNELS AND GROUPS
# ============================================================================

@flow_bp.route('/channel/<channel_id>')
@require_login
def channel_redirect(channel_id):
    """Redirect /flow/channel/<id> to /flow/channels/<id> for consistency."""
    from flask import redirect
    return redirect(f'/flow/channels/{channel_id}', code=301)


@flow_bp.route('/group/<group_id>')
@require_login
def group_redirect(group_id):
    """Redirect /flow/group/<id> to /flow/groups/<id> for consistency."""
    from flask import redirect
    return redirect(f'/flow/groups/{group_id}', code=301)


@flow_bp.route('/channels/<channel_id>')
@require_login
def channel_view(channel_id):
    """View a channel. Supports both internal UUID and URL-friendly channel_id (username)."""
    user = get_current_user()

    # Try to find channel by channel_id (username) first, then by internal UUID
    channel = get_one('''
        SELECT id, name, description, avatar_url, channel_type, category,
               is_archived, created_by, created_at, updated_at, settings, invite_code, channel_id
        FROM flow_channels WHERE channel_id = ?
    ''', (channel_id,))
    if not channel:
        channel = get_one('''
            SELECT id, name, description, avatar_url, channel_type, category,
                   is_archived, created_by, created_at, updated_at, settings, invite_code, channel_id
            FROM flow_channels WHERE id = ?
        ''', (channel_id,))

    if not channel:
        return render_template('flow/error.html', error='Channel not found', user=user, direction=get_user_direction()), 404

    # Check membership
    membership = get_one('''
        SELECT * FROM flow_channel_members WHERE channel_id = ? AND user_id = ?
    ''', (channel['id'], user['id']))
    
    if not membership and not user_has_permission(user['id'], 'flow', 'channels', 'admin'):
        return render_template('flow/error.html', error='Not a channel member', user=user, direction=get_user_direction()), 403
    
    # Get or create channel conversation
    conv = get_one('''
        SELECT * FROM flow_conversations
        WHERE name = ? AND conversation_type = 'channel'
    ''', (channel['name'],))

    if not conv:
        # Create a conversation for this channel
        conv_id = generate_id()
        now = datetime.now().isoformat()
        with get_db_context() as db:
            db.execute('''
                INSERT INTO flow_conversations (id, conversation_type, name, created_by, last_message_at)
                VALUES (?, 'channel', ?, ?, ?)
            ''', (conv_id, channel['name'], user['id'], now))
            db.execute('''
                INSERT INTO flow_conversation_members (conversation_id, user_id, role, last_read_at)
                VALUES (?, ?, 'owner', ?)
            ''', (conv_id, user['id'], now))
        conv = get_one('SELECT * FROM flow_conversations WHERE id = ?', (conv_id,))

    logger.debug(f'channel_view: channel_id={channel_id}, channel_name={channel["name"]}, conv={conv}')

    messages = []
    if conv:
        messages = get_conversation_messages(conv['id'], user['id'], limit=100)
    
    # Get members
    members = get_all('''
        SELECT fcm.*, fup.display_name, fup.avatar_url, fup.username, fup.department
        FROM flow_channel_members fcm
        LEFT JOIN flow_user_profiles fup ON fcm.user_id = fup.user_id
        WHERE fcm.channel_id = ?
    ''', (channel['id'],))
    
    profile = get_flow_profile(user['id'])
    status = get_user_status(user['id'])
    
    return render_template('flow/channel.html',
        user=user,
        profile=profile,
        status=status,
        channel=channel,
        conversation=conv,
        messages=messages,
        members=members,
        membership=membership,
        page_title=f'# {channel["name"]}',
        direction=get_user_direction()
    )


@flow_bp.route('/api/channels/<channel_id>/join', methods=['POST'])
@require_login
def api_join_channel(channel_id):
    """Join a channel."""
    user = get_current_user()

    channel = get_one('''
        SELECT id, name, description, avatar_url, channel_type, category,
               is_archived, created_by, created_at, updated_at, settings, invite_code, channel_id
        FROM flow_channels WHERE id = ?
    ''', (channel_id,))
    if not channel:
        return jsonify({'error': 'Channel not found'}), 404

    # Get the conversation - try to find it by channel name
    conv = get_one('''
        SELECT * FROM flow_conversations WHERE name = ? AND conversation_type = 'channel'
    ''', (channel['name'],))

    logger.debug(f'join_channel: channel_id={channel_id}, channel_name={channel["name"]}, conv={conv}')

    with get_db_context() as db:
        db.execute('''
            INSERT OR IGNORE INTO flow_channel_members (channel_id, user_id, role)
            VALUES (?, ?, 'member')
        ''', (channel_id, user['id']))

        if conv:
            db.execute('''
                INSERT OR IGNORE INTO flow_conversation_members (conversation_id, user_id, role)
                VALUES (?, ?, 'member')
            ''', (conv['id'], user['id']))
            logger.debug(f'join_channel: Added user {user["id"]} to conversation {conv["id"]}')
        else:
            logger.debug(f'join_channel: No conversation found for channel {channel["name"]}')

    log_audit(user['id'], 'channel_join', {'channel_id': channel_id}, 'flow')
    return jsonify({'success': True})


@flow_bp.route('/api/channels/<channel_id>/add-member', methods=['POST'])
@require_login
def api_add_channel_member(channel_id):
    """Add a member to a channel."""
    user = get_current_user()
    data = safe_get_json()
    new_user_id = data.get('user_id')
    
    if not new_user_id:
        return jsonify({'error': 'User ID required'}), 400
    
    channel = get_one('''
        SELECT id, name, description, avatar_url, channel_type, category,
               is_archived, created_by, created_at, updated_at, settings, invite_code, channel_id
        FROM flow_channels WHERE id = ?
    ''', (channel_id,))
    if not channel:
        return jsonify({'error': 'Channel not found'}), 404
    
    # Check if requester is admin
    membership = get_one('''
        SELECT * FROM flow_channel_members WHERE channel_id = ? AND user_id = ? AND role = 'admin'
    ''', (channel_id, user['id']))
    
    if not membership:
        return jsonify({'error': 'Permission denied'}), 403
    
    # Get the conversation
    conv = get_one('''
        SELECT * FROM flow_conversations WHERE name = ? AND conversation_type = 'channel'
    ''', (channel['name'],))
    
    with get_db_context() as db:
        db.execute('''
            INSERT OR IGNORE INTO flow_channel_members (channel_id, user_id, role)
            VALUES (?, ?, 'member')
        ''', (channel_id, new_user_id))
        
        if conv:
            db.execute('''
                INSERT OR IGNORE INTO flow_conversation_members (conversation_id, user_id, role)
                VALUES (?, ?, 'member')
            ''', (conv['id'], new_user_id))
    
    log_audit(user['id'], 'channel_add_member', {'channel_id': channel_id, 'new_user_id': new_user_id}, 'flow')
    return jsonify({'success': True})


@flow_bp.route('/api/channels/<channel_id>/leave', methods=['POST'])
@require_login
def api_leave_channel(channel_id):
    """Leave a channel. Supports both internal UUID and channel_id (username) format."""
    user = get_current_user()

    # Try to find channel by channel_id (username) first, then by internal UUID
    channel = get_one('''
        SELECT id, name, description, avatar_url, channel_type, category,
               is_archived, created_by, created_at, updated_at, settings, invite_code, channel_id
        FROM flow_channels WHERE channel_id = ?
    ''', (channel_id,))
    if not channel:
        channel = get_one('''
            SELECT id, name, description, avatar_url, channel_type, category,
                   is_archived, created_by, created_at, updated_at, settings, invite_code, channel_id
            FROM flow_channels WHERE id = ?
        ''', (channel_id,))

    if not channel:
        return jsonify({'error': 'Channel not found'}), 404

    # Check if user is the owner
    if channel['created_by'] == user['id']:
        return jsonify({'error': 'Channel owner cannot leave. Transfer ownership first.'}), 403

    # Check if user is a member
    membership = get_one('''
        SELECT * FROM flow_channel_members WHERE channel_id = ? AND user_id = ?
    ''', (channel['id'], user['id']))
    if not membership:
        return jsonify({'error': 'You are not a member of this channel'}), 400

    # Get the conversation
    conv = get_one('''
        SELECT * FROM flow_conversations WHERE name = ? AND conversation_type = 'channel'
    ''', (channel['name'],))

    with get_db_context() as db:
        db.execute('DELETE FROM flow_channel_members WHERE channel_id = ? AND user_id = ?', (channel['id'], user['id']))
        if conv:
            db.execute('DELETE FROM flow_conversation_members WHERE conversation_id = ? AND user_id = ?', (conv['id'], user['id']))

    log_audit(user['id'], 'channel_leave', {'channel_id': channel['id'], 'channel_name': channel['name']}, 'flow')
    return jsonify({'success': True, 'redirect_url': '/flow/channels'})


# ============================================================================
# GROUP ROUTES
# ============================================================================

@flow_bp.route('/groups')
@require_login
def groups():
    """List all groups."""
    user = get_current_user()
    
    groups = get_all('''
        SELECT fg.id, fg.name, fg.description, fg.avatar_url, fg.group_type, fg.created_by,
               fg.created_at, fg.updated_at, fg.settings,
               fgm.role,
               (SELECT COUNT(*) FROM flow_group_members WHERE group_id = fg.id) as member_count
        FROM flow_groups fg
        LEFT JOIN flow_group_members fgm ON fg.id = fgm.group_id AND fgm.user_id = ?
        ORDER BY fg.name
    ''', (user['id'],))
    
    profile = get_flow_profile(user['id'])
    status = get_user_status(user['id'])
    
    return render_template('flow/groups.html',
        user=user,
        profile=profile,
        status=status,
        groups=groups,
        page_title='Groups'
    )


@flow_bp.route('/groups/create')
@require_login
def create_group_page():
    """Create a new group."""
    user = get_current_user()
    
    if not user_has_permission(user['id'], 'flow', 'groups', 'create'):
        return render_template('flow/error.html', error='Permission denied', user=user), 403
    
    # Get all users
    users = get_all('''
        SELECT u.id, u.username, fup.display_name, fup.avatar_url, fup.department
        FROM users u
        LEFT JOIN flow_user_profiles fup ON u.id = fup.user_id
        ORDER BY fup.display_name
    ''')
    
    profile = get_flow_profile(user['id'])
    status = get_user_status(user['id'])
    
    return render_template('flow/create_group.html',
        user=user,
        profile=profile,
        status=status,
        users=users,
        page_title='Create Group'
    )


@flow_bp.route('/api/groups/create', methods=['POST'])
@require_login
def api_create_group():
    """Create a new group."""
    user = get_current_user()
    data = safe_get_json()
    
    name = data.get('name')
    description = data.get('description', '')
    group_type = data.get('group_type', 'private')
    member_ids = data.get('member_ids', [])
    
    if not name:
        return jsonify({'error': 'Group name required'}), 400
    
    group_id = create_group(name, description, user['id'], group_type, member_ids)
    
    return jsonify({'success': True, 'group_id': group_id})


@flow_bp.route('/groups/<group_id>')
@require_login
def group_view(group_id):
    """View a group."""
    user = get_current_user()
    
    group = get_one('''
        SELECT id, name, description, avatar_url, group_type, created_by,
               created_at, updated_at, settings
        FROM flow_groups WHERE id = ?
    ''', (group_id,))
    if not group:
        return render_template('flow/error.html', error='Group not found', user=user), 404

    # Check membership
    membership = get_one('''
        SELECT * FROM flow_group_members WHERE group_id = ? AND user_id = ?
    ''', (group_id, user['id']))

    if not membership:
        return render_template('flow/error.html', error='Not a group member', user=user), 403
    
    # Get or create group conversation
    conv = get_one('''
        SELECT * FROM flow_conversations WHERE name = ? AND conversation_type = 'group'
    ''', (group['name'],))
    
    if not conv:
        # Create a conversation for this group
        conv_id = generate_id()
        now = datetime.now().isoformat()
        with get_db_context() as db:
            db.execute('''
                INSERT INTO flow_conversations (id, conversation_type, name, created_by, last_message_at)
                VALUES (?, 'group', ?, ?, ?)
            ''', (conv_id, group['name'], user['id'], now))
            db.execute('''
                INSERT INTO flow_conversation_members (conversation_id, user_id, role, last_read_at)
                VALUES (?, ?, 'owner', ?)
            ''', (conv_id, user['id'], now))
        conv = get_one('SELECT * FROM flow_conversations WHERE id = ?', (conv_id,))
    
    messages = []
    if conv:
        messages = get_conversation_messages(conv['id'], user['id'], limit=100)
    
    # Get members
    members = get_all('''
        SELECT fgm.*, fup.display_name, fup.avatar_url, fup.username, fup.department, fup.job_title
        FROM flow_group_members fgm
        LEFT JOIN flow_user_profiles fup ON fgm.user_id = fup.user_id
        WHERE fgm.group_id = ?
    ''', (group_id,))
    
    profile = get_flow_profile(user['id'])
    status = get_user_status(user['id'])
    
    return render_template('flow/group.html',
        user=user,
        profile=profile,
        status=status,
        group=group,
        conversation=conv,
        messages=messages,
        members=members,
        membership=membership,
        page_title=group['name']
    )


@flow_bp.route('/api/groups/<group_id>/add-member', methods=['POST'])
@require_login
def api_add_group_member(group_id):
    """Add a member to a group."""
    user = get_current_user()
    data = safe_get_json()
    new_user_id = data.get('user_id')
    
    if not new_user_id:
        return jsonify({'error': 'User ID required'}), 400
    
    group = get_one('SELECT * FROM flow_groups WHERE id = ?', (group_id,))
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    
    # Check if requester is admin/owner
    membership = get_one('''
        SELECT * FROM flow_group_members WHERE group_id = ? AND user_id = ? AND role IN ('owner', 'admin')
    ''', (group_id, user['id']))
    
    if not membership:
        return jsonify({'error': 'Permission denied'}), 403
    
    # Get the conversation
    conv = get_one('''
        SELECT * FROM flow_conversations WHERE name = ? AND conversation_type = 'group'
    ''', (group['name'],))
    
    with get_db_context() as db:
        db.execute('''
            INSERT OR IGNORE INTO flow_group_members (group_id, user_id, role)
            VALUES (?, ?, 'member')
        ''', (group_id, new_user_id))
        
        if conv:
            db.execute('''
                INSERT OR IGNORE INTO flow_conversation_members (conversation_id, user_id, role)
                VALUES (?, ?, 'member')
            ''', (conv['id'], new_user_id))
    
    return jsonify({'success': True})


@flow_bp.route('/api/groups/<group_id>/remove-member', methods=['POST'])
@require_login
def api_remove_group_member(group_id):
    """Remove a member from a group."""
    user = get_current_user()
    data = safe_get_json()
    remove_user_id = data.get('user_id')
    
    if not remove_user_id:
        return jsonify({'error': 'User ID required'}), 400
    
    group = get_one('SELECT * FROM flow_groups WHERE id = ?', (group_id,))
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    
    # Check if requester is admin/owner or removing self
    membership = get_one('''
        SELECT * FROM flow_group_members WHERE group_id = ? AND user_id = ? AND role IN ('owner', 'admin')
    ''', (group_id, user['id']))
    
    if not membership and remove_user_id != user['id']:
        return jsonify({'error': 'Permission denied'}), 403
    
    # Get the conversation
    conv = get_one('''
        SELECT * FROM flow_conversations WHERE name = ? AND conversation_type = 'group'
    ''', (group['name'],))
    
    with get_db_context() as db:
        db.execute('DELETE FROM flow_group_members WHERE group_id = ? AND user_id = ?', (group_id, remove_user_id))
        if conv:
            db.execute('DELETE FROM flow_conversation_members WHERE conversation_id = ? AND user_id = ?', (conv['id'], remove_user_id))
    
    return jsonify({'success': True})


# ============================================================================
# SAVE MESSAGES
# ============================================================================

@flow_bp.route('/saved')
@require_login
def saved():
    """View saved messages."""
    user = get_current_user()
    
    # Get or create save messages conversation
    conv_id = get_user_saved_messages_conversation(user['id'])
    conversation = get_one('SELECT * FROM flow_conversations WHERE id = ?', (conv_id,))
    
    # Get saved messages
    saved = get_all('''
        SELECT sm.*, m.*, fup.display_name as sender_name, fc.name as conversation_name
        FROM flow_saved_messages sm
        JOIN flow_messages m ON sm.message_id = m.id
        LEFT JOIN flow_user_profiles fup ON m.sender_id = fup.user_id
        LEFT JOIN flow_conversations fc ON m.conversation_id = fc.id
        WHERE sm.user_id = ?
        ORDER BY sm.saved_at DESC
    ''', (user['id'],))
    
    profile = get_flow_profile(user['id'])
    status = get_user_status(user['id'])
    
    return render_template('flow/saved.html',
        user=user,
        profile=profile,
        status=status,
        conversation=conversation,
        saved_messages=saved,
        page_title='Saved Messages'
    )


@flow_bp.route('/api/messages/<message_id>/save', methods=['POST'])
@require_login
def api_save_message(message_id):
    """Save a message."""
    user = get_current_user()
    
    with get_db_context() as db:
        db.execute('''
            INSERT OR IGNORE INTO flow_saved_messages (user_id, message_id)
            VALUES (?, ?)
        ''', (user['id'], message_id))
    
    return jsonify({'success': True})


@flow_bp.route('/api/messages/<message_id>/unsave', methods=['POST'])
@require_login
def api_unsave_message(message_id):
    """Unsave a message."""
    user = get_current_user()
    
    with get_db_context() as db:
        db.execute('DELETE FROM flow_saved_messages WHERE user_id = ? AND message_id = ?', (user['id'], message_id))
    
    return jsonify({'success': True})


# ============================================================================
# CALLS & MEETINGS
# ============================================================================

@flow_bp.route('/calls')
@require_login
def calls():
    """View call history."""
    user = get_current_user()

    # Get recent calls
    calls = get_all('''
        SELECT fcs.*, fcp.call_status, fup.display_name as participant_name
        FROM flow_call_sessions fcs
        JOIN flow_call_participants fcp ON fcs.id = fcp.call_id AND fcp.user_id = ?
        LEFT JOIN flow_call_participants fcp2 ON fcs.id = fcp2.call_id AND fcp2.user_id != ?
        LEFT JOIN flow_user_profiles fup ON fcp2.user_id = fup.user_id
        ORDER BY fcs.created_at DESC
        LIMIT 50
    ''', (user['id'], user['id']))

    profile = get_flow_profile(user['id'])
    status = get_user_status(user['id'])

    # Get all users for initiating new calls
    all_users = get_all('''
        SELECT u.id, u.username, fup.display_name, fup.avatar_url, fup.department
        FROM users u
        LEFT JOIN flow_user_profiles fup ON u.id = fup.user_id
        WHERE u.id != ?
        ORDER BY fup.display_name OR u.username
    ''', (user['id'],))

    return render_template('flow/calls.html',
        user=user,
        profile=profile,
        status=status,
        calls=calls,
        all_users=all_users,
        page_title='Calls'
    )


@flow_bp.route('/call/<call_id>')
@require_login
def call_view(call_id):
    """View/start a call."""
    user = get_current_user()
    
    call = get_one('SELECT * FROM flow_call_sessions WHERE id = ?', (call_id,))
    if not call:
        return render_template('flow/error.html', error='Call not found', user=user), 404
    
    # Get participants
    participants = get_all('''
        SELECT fcp.*, fup.display_name, fup.avatar_url
        FROM flow_call_participants fcp
        LEFT JOIN flow_user_profiles fup ON fcp.user_id = fup.user_id
        WHERE fcp.call_id = ?
    ''', (call_id,))
    
    profile = get_flow_profile(user['id'])
    status = get_user_status(user['id'])
    
    return render_template('flow/call.html',
        user=user,
        profile=profile,
        status=status,
        call=call,
        participants=participants,
        page_title=f'Call'
    )


@flow_bp.route('/api/call/start', methods=['POST'])
@require_login
def api_start_call():
    """Start a new call."""
    user = get_current_user()
    data = safe_get_json()
    
    call_type = data.get('type', 'audio')  # audio or video
    participant_ids = data.get('participant_ids', [])
    
    if not participant_ids:
        return jsonify({'error': 'Participant IDs required'}), 400
    
    call_id = start_call(call_type, user['id'], participant_ids)
    
    return jsonify({'success': True, 'call_id': call_id})


@flow_bp.route('/api/call/<call_id>/join', methods=['POST'])
@require_login
def api_join_call(call_id):
    """Join a call."""
    user = get_current_user()
    
    with get_db_context() as db:
        db.execute('''
            UPDATE flow_call_participants
            SET call_status = 'joined', joined_at = ?
            WHERE call_id = ? AND user_id = ?
        ''', (datetime.now().isoformat(), call_id, user['id']))
    
    return jsonify({'success': True})


@flow_bp.route('/api/call/<call_id>/leave', methods=['POST'])
@require_login
def api_leave_call(call_id):
    """Leave a call."""
    user = get_current_user()

    with get_db_context() as db:
        db.execute('''
            UPDATE flow_call_participants
            SET call_status = 'left', left_at = ?
            WHERE call_id = ? AND user_id = ?
        ''', (datetime.now().isoformat(), call_id, user['id']))

    return jsonify({'success': True})


@flow_bp.route('/api/calls/delete', methods=['POST'])
@require_login
def api_delete_calls():
    """Delete selected call history for the current user."""
    user = get_current_user()
    data = safe_get_json()

    call_ids = data.get('call_ids', [])
    if not call_ids:
        return jsonify({'error': 'No call IDs provided'}), 400

    # Verify user is a participant in all calls and delete only their participation
    with get_db_context() as db:
        db.execute('''
            DELETE FROM flow_call_participants
            WHERE call_id IN ({}) AND user_id = ?
        '''.format(','.join('?' * len(call_ids))), call_ids + [user['id']])

        # Also delete call sessions that have no more participants
        db.execute('''
            DELETE FROM flow_call_sessions
            WHERE id IN ({}) AND initiated_by = ?
        '''.format(','.join('?' * len(call_ids))), call_ids + [user['id']])

    return jsonify({'success': True, 'deleted': len(call_ids)})


@flow_bp.route('/meetings')
@require_login
def meetings():
    """View meetings."""
    user = get_current_user()
    
    # Get upcoming meetings
    upcoming = get_all('''
        SELECT fms.*, fmp.role as participant_role,
               (SELECT COUNT(*) FROM flow_meeting_participants WHERE meeting_id = fms.id) as participant_count
        FROM flow_meeting_sessions fms
        JOIN flow_meeting_participants fmp ON fms.id = fmp.meeting_id AND fmp.user_id = ?
        WHERE fms.status IN ('scheduled', 'active')
        ORDER BY fms.start_time
    ''', (user['id'],))
    
    # Get past meetings
    past = get_all('''
        SELECT fms.*, fmp.role as participant_role,
               (SELECT COUNT(*) FROM flow_meeting_participants WHERE meeting_id = fms.id) as participant_count
        FROM flow_meeting_sessions fms
        JOIN flow_meeting_participants fmp ON fms.id = fmp.meeting_id AND fmp.user_id = ?
        WHERE fms.status = 'ended'
        ORDER BY fms.start_time DESC
        LIMIT 20
    ''', (user['id'],))
    
    profile = get_flow_profile(user['id'])
    status = get_user_status(user['id'])
    
    return render_template('flow/meetings.html',
        user=user,
        profile=profile,
        status=status,
        upcoming_meetings=upcoming,
        past_meetings=past,
        page_title='Meetings'
    )


@flow_bp.route('/meeting/<meeting_id>')
@require_login
def meeting_view(meeting_id):
    """View/start a meeting."""
    user = get_current_user()
    
    meeting = get_one('SELECT * FROM flow_meeting_sessions WHERE id = ?', (meeting_id,))
    if not meeting:
        return render_template('flow/error.html', error='Meeting not found', user=user), 404

    # Check participation
    participation = get_one('''
        SELECT * FROM flow_meeting_participants WHERE meeting_id = ? AND user_id = ?
    ''', (meeting_id, user['id']))

    if not participation:
        return render_template('flow/error.html', error='Not a participant', user=user), 403
    
    # Get participants
    participants = get_all('''
        SELECT fmp.*, fup.display_name, fup.avatar_url, fup.username
        FROM flow_meeting_participants fmp
        LEFT JOIN flow_user_profiles fup ON fmp.user_id = fup.user_id
        WHERE fmp.meeting_id = ?
    ''', (meeting_id,))
    
    # Get chat messages
    chat_messages = get_all('''
        SELECT fmc.*, fup.display_name, fup.avatar_url
        FROM flow_meeting_chat fmc
        LEFT JOIN flow_user_profiles fup ON fmc.sender_id = fup.user_id
        WHERE fmc.meeting_id = ?
        ORDER BY fmc.created_at
    ''', (meeting_id,))
    
    profile = get_flow_profile(user['id'])
    status = get_user_status(user['id'])
    
    return render_template('flow/meeting.html',
        user=user,
        profile=profile,
        status=status,
        meeting=meeting,
        participation=participation,
        participants=participants,
        chat_messages=chat_messages,
        page_title=meeting['title']
    )


@flow_bp.route('/api/meeting/start', methods=['POST'])
@require_login
def api_start_meeting():
    """Start a new instant meeting."""
    user = get_current_user()
    data = safe_get_json()
    
    title = data.get('title', 'Instant Meeting')
    description = data.get('description', '')
    
    meeting_id = start_meeting(title, description, user['id'], meeting_type='instant')
    
    return jsonify({'success': True, 'meeting_id': meeting_id})


@flow_bp.route('/api/meeting/<meeting_id>/chat', methods=['POST'])
@require_login
def api_meeting_chat(meeting_id):
    """Send a chat message in a meeting."""
    user = get_current_user()
    data = safe_get_json()
    content = data.get('content')
    
    if not content:
        return jsonify({'error': 'Content required'}), 400
    
    with get_db_context() as db:
        db.execute('''
            INSERT INTO flow_meeting_chat (meeting_id, sender_id, content)
            VALUES (?, ?, ?)
        ''', (meeting_id, user['id'], content))
    
    return jsonify({'success': True})


# ============================================================================
# NOTIFICATIONS
# ============================================================================

@flow_bp.route('/notifications')
@require_login
def notifications():
    """View all notifications."""
    user = get_current_user()
    
    notifications = get_all('''
        SELECT * FROM flow_notifications
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 100
    ''', (user['id'],))
    
    profile = get_flow_profile(user['id'])
    status = get_user_status(user['id'])
    
    return render_template('flow/notifications.html',
        user=user,
        profile=profile,
        status=status,
        notifications=notifications,
        page_title='Notifications'
    )


@flow_bp.route('/api/notifications/mark-read', methods=['POST'])
@require_login
def api_mark_notifications_read():
    """Mark notifications as read."""
    user = get_current_user()
    data = safe_get_json()
    notification_ids = data.get('notification_ids', [])
    
    if notification_ids:
        placeholders = ','.join(['?' for _ in notification_ids])
        with get_db_context() as db:
            db.execute(f'''
                UPDATE flow_notifications
                SET is_read = 1, read_at = ?
                WHERE id IN ({placeholders}) AND user_id = ?
            ''', [datetime.now().isoformat()] + notification_ids + [user['id']])
    else:
        # Mark all as read
        with get_db_context() as db:
            db.execute('''
                UPDATE flow_notifications
                SET is_read = 1, read_at = ?
                WHERE user_id = ? AND is_read = 0
            ''', (datetime.now().isoformat(), user['id']))
    
    return jsonify({'success': True})


@flow_bp.route('/api/notifications/unread-count')
@require_login
def api_unread_count():
    """Get unread notification count."""
    user = get_current_user()
    count = get_unread_notification_count(user['id'])
    return jsonify({'count': count})


# ============================================================================
# SEARCH
# ============================================================================

@flow_bp.route('/search')
@require_login
def search():
    """Search page."""
    user = get_current_user()
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'all')
    
    results = []
    if query:
        results = search_messages(user['id'], query, search_type)
    
    profile = get_flow_profile(user['id'])
    status = get_user_status(user['id'])
    
    return render_template('flow/search.html',
        user=user,
        profile=profile,
        status=status,
        query=query,
        search_type=search_type,
        results=results,
        page_title='Search'
    )


@flow_bp.route('/api/search')
@require_login
def api_search():
    """API search endpoint."""
    user = get_current_user()
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'all')
    limit = int(request.args.get('limit', 50))

    if not query:
        return jsonify({'results': []})

    results = search_messages(user['id'], query, search_type, limit)
    return jsonify({'results': results})


@flow_bp.route('/api/search/comprehensive')
@require_login
def api_search_comprehensive():
    """Comprehensive search across users, channels, groups, and messages."""
    user = get_current_user()
    query = request.args.get('q', '')
    search_scope = request.args.get('scope', 'all')  # all, users, channels, groups, messages
    limit = int(request.args.get('limit', 20))

    if not query or len(query) < 2:
        return jsonify({'error': 'Search query must be at least 2 characters'}), 400

    results = {
        'users': [],
        'channels': [],
        'groups': [],
        'messages': []
    }

    try:
        # Search users
        if search_scope in ['all', 'users']:
            users = get_all('''
                SELECT fup.user_id, fup.display_name, fup.username, fup.avatar_url,
                       fup.department, fup.job_title, u.email
                FROM flow_user_profiles fup
                JOIN users u ON fup.user_id = u.id
                WHERE (fup.display_name LIKE ? OR fup.username LIKE ? OR u.email LIKE ?)
                AND fup.user_id != ?
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', user['id'], limit))
            results['users'] = [{
                'id': u['user_id'],
                'display_name': u['display_name'] or u['username'] or 'Unknown',
                'username': u['username'],
                'avatar_url': u['avatar_url'],
                'department': u['department'],
                'job_title': u['job_title'],
                'type': 'user'
            } for u in users]

        # Search channels
        if search_scope in ['all', 'channels']:
            channels = get_all('''
                SELECT fc.id, fc.name, fc.description, fc.avatar_url, fc.channel_type,
                       fc.channel_id, fc.category,
                       (SELECT COUNT(*) FROM flow_channel_members WHERE channel_id = fc.id) as member_count
                FROM flow_channels fc
                WHERE (fc.name LIKE ? OR fc.description LIKE ? OR fc.channel_id LIKE ?)
                AND fc.is_archived = 0
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
            results['channels'] = [{
                'id': c['id'],
                'name': c['name'],
                'description': c['description'],
                'avatar_url': c['avatar_url'],
                'channel_type': c['channel_type'],
                'channel_id': c['channel_id'],
                'category': c['category'],
                'member_count': c['member_count'],
                'type': 'channel'
            } for c in channels]

        # Search groups
        if search_scope in ['all', 'groups']:
            groups = get_all('''
                SELECT fg.id, fg.name, fg.description, fg.avatar_url, fg.group_type,
                       (SELECT COUNT(*) FROM flow_group_members WHERE group_id = fg.id) as member_count
                FROM flow_groups fg
                WHERE (fg.name LIKE ? OR fg.description LIKE ?)
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', limit))
            results['groups'] = [{
                'id': g['id'],
                'name': g['name'],
                'description': g['description'],
                'avatar_url': g['avatar_url'],
                'group_type': g['group_type'],
                'member_count': g['member_count'],
                'type': 'group'
            } for g in groups]

        # Search messages
        if search_scope in ['all', 'messages']:
            messages = search_messages(user['id'], query, 'all', limit)
            results['messages'] = [{
                'id': m['id'],
                'content': m['content'][:200] if m['content'] else '',
                'conversation_id': m['conversation_id'],
                'conversation_name': m.get('conversation_name'),
                'conversation_type': m.get('conversation_type'),
                'sender_id': m['sender_id'],
                'sender_name': m.get('sender_name'),
                'message_type': m['message_type'],
                'created_at': m['created_at'].isoformat() if m.get('created_at') else None,
                'type': 'message'
            } for m in messages]

        return jsonify({'success': True, 'results': results, 'query': query})

    except Exception as e:
        logger.error(f'Search error: {str(e)}')
        return jsonify({'error': 'Search failed', 'details': str(e)}), 500


# ============================================================================
# FLOW FEED
# ============================================================================

@flow_bp.route('/api/flow/feed')
@require_login
def api_flow_feed():
    """Get Flow feed - posts from flow_posts table (native + published)."""
    import traceback
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Unauthorized', 'details': 'User not logged in'}), 401

        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        # Import the new function
        from flow_models import get_flow_feed_posts
        posts = get_flow_feed_posts(user['id'], limit=limit, offset=offset)
        return jsonify({'success': True, 'posts': posts})
    except Exception as e:
        logger.error(f'Flow feed error: {str(e)}')
        traceback.print_exc()
        return jsonify({'error': 'Failed to load Flow feed', 'details': str(e)}), 500


@flow_bp.route('/api/flow/posts', methods=['POST'])
@require_login
def api_create_flow_post():
    """Create a new native Flow post."""
    user = get_current_user()
    data = safe_get_json()

    content = data.get('content', '').strip()
    if not content:
        return jsonify({'error': 'Content is required'}), 400

    post_type = data.get('post_type', 'text')
    media_url = data.get('media_url')
    media_type = data.get('media_type')

    try:
        from flow_models import create_flow_post
        post_id = create_flow_post(
            author_id=user['id'],
            content=content,
            post_type=post_type,
            media_url=media_url,
            media_type=media_type
        )
        return jsonify({'success': True, 'post_id': post_id})
    except Exception as e:
        logger.error(f'Create post error: {str(e)}')
        return jsonify({'error': 'Failed to create post'}), 500


@flow_bp.route('/api/flow/posts/<post_id>/react', methods=['POST'])
@require_login
def api_flow_post_react(post_id):
    """Add or remove reaction on a Flow post. Returns updated reactions."""
    user = get_current_user()
    data = safe_get_json()
    emoji = data.get('emoji', '👍')
    action = data.get('action', 'add')  # 'add', 'remove', or 'toggle'

    try:
        from flow_models import (
            add_flow_post_reaction, remove_flow_post_reaction,
            get_one, get_all
        )

        # Toggle logic: if action is 'toggle', check existing reaction
        if action == 'toggle':
            existing = get_one('''
                SELECT id FROM flow_post_reactions
                WHERE post_id = ? AND user_id = ? AND emoji = ?
            ''', (post_id, user['id'], emoji))
            if existing:
                action = 'remove'
            else:
                action = 'add'

        if action == 'remove':
            remove_flow_post_reaction(post_id, user['id'], emoji)
            reaction_action = 'removed'
        else:
            add_flow_post_reaction(post_id, user['id'], emoji)
            reaction_action = 'added'

        # Return updated reactions
        reactions = get_all('''
            SELECT emoji, user_id FROM flow_post_reactions WHERE post_id = ?
        ''', (post_id,))

        reaction_dict = {}
        for r in reactions:
            if r['emoji'] not in reaction_dict:
                reaction_dict[r['emoji']] = []
            reaction_dict[r['emoji']].append(r['user_id'])

        # Get reaction counts
        reaction_count = sum(len(users) for users in reaction_dict.values())

        return jsonify({
            'success': True,
            'action': reaction_action,
            'emoji': emoji,
            'reactions': reaction_dict,
            'reaction_count': reaction_count,
            'user_reacted': reaction_action == 'added'
        })
    except Exception as e:
        logger.error(f'Reaction error: {str(e)}')
        return jsonify({'error': str(e)}), 500


@flow_bp.route('/api/flow/posts/<post_id>', methods=['GET'])
@require_login
def api_get_flow_post(post_id):
    """Get a single Flow post with comments."""
    user = get_current_user()

    try:
        from flow_models import get_one, get_all

        post = get_one('SELECT * FROM flow_posts WHERE id = ? AND is_deleted = 0', (post_id,))
        if not post:
            return jsonify({'error': 'Post not found'}), 404

        # Get reactions
        reactions = get_all('''
            SELECT emoji, user_id FROM flow_post_reactions WHERE post_id = ?
        ''', (post_id,))

        # Parse reactions into emoji groups
        reaction_dict = {}
        for r in reactions:
            if r['emoji'] not in reaction_dict:
                reaction_dict[r['emoji']] = []
            reaction_dict[r['emoji']].append(r['user_id'])

        # Get comments
        comments = get_all('''
            SELECT * FROM flow_post_comments
            WHERE post_id = ? AND is_deleted = 0
            ORDER BY created_at ASC
        ''', (post_id,))

        post['reactions'] = reaction_dict
        post['comments'] = comments

        # Check if current user has reacted
        post['user_reacted'] = user['id'] in [uid for uids in reaction_dict.values() for uid in uids]

        return jsonify({'success': True, 'post': post})
    except Exception as e:
        logger.error(f'Get post error: {str(e)}')
        return jsonify({'error': str(e)}), 500


@flow_bp.route('/post/<post_id>')
@require_login
def view_flow_post(post_id):
    """View a single Flow post page."""
    user = get_current_user()
    try:
        from flow_models import get_one, get_all

        post = get_one('SELECT * FROM flow_posts WHERE id = ? AND is_deleted = 0', (post_id,))
        if not post:
            return render_template('flow/post.html', error='Post not found'), 404

        # Get author info
        author = get_one('SELECT id, name, avatar FROM users WHERE id = ?', (post['author_id'],))
        post['author'] = author

        # Get reactions
        reactions = get_all('''
            SELECT emoji, user_id FROM flow_post_reactions WHERE post_id = ?
        ''', (post_id,))

        reaction_dict = {}
        for r in reactions:
            if r['emoji'] not in reaction_dict:
                reaction_dict[r['emoji']] = []
            reaction_dict[r['emoji']].append(r['user_id'])
        post['reactions'] = reaction_dict

        # Get comments with author info
        comments = get_all('''
            SELECT c.*, u.name as author_name, u.avatar as author_avatar
            FROM flow_post_comments c
            LEFT JOIN users u ON c.author_id = u.id
            WHERE c.post_id = ? AND c.is_deleted = 0
            ORDER BY c.created_at ASC
        ''', (post_id,))
        post['comments'] = comments

        # Get user info for current user
        current_user_info = get_one('SELECT id, name, avatar FROM users WHERE id = ?', (user['id'],))

        return render_template('flow/post.html', post=post, user=current_user_info)
    except Exception as e:
        logger.error(f'View post error: {str(e)}')
        import traceback
        traceback.print_exc()
        return render_template('flow/post.html', error=str(e)), 500


@flow_bp.route('/api/flow/posts/<post_id>/comment', methods=['POST'])
@require_login
def api_flow_post_comment(post_id):
    """Add a comment to a Flow post."""
    user = get_current_user()
    data = safe_get_json()
    content = data.get('content', '').strip()

    if not content:
        return jsonify({'error': 'Content is required'}), 400

    try:
        from flow_models import add_flow_post_comment
        comment_id = add_flow_post_comment(post_id, user['id'], content)
        return jsonify({'success': True, 'comment_id': comment_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@flow_bp.route('/api/flow/posts/<post_id>', methods=['DELETE'])
@require_login
def api_delete_flow_post(post_id):
    """Delete a Flow post."""
    user = get_current_user()

    try:
        from flow_models import delete_flow_post
        success = delete_flow_post(post_id, user['id'])
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Cannot delete this post'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@flow_bp.route('/api/flow/posts/<post_id>/pin', methods=['POST'])
@require_login
def api_pin_flow_post(post_id):
    """Pin or unpin a Flow post."""
    user = get_current_user()
    data = safe_get_json()
    is_pinned = data.get('is_pinned', True)

    try:
        from flow_models import pin_flow_post
        pin_flow_post(post_id, is_pinned)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@flow_bp.route('/api/flow/publish', methods=['POST'])
@require_login
def api_flow_publish():
    """Publish a message to Flow from a Stream."""
    user = get_current_user()
    data = safe_get_json()

    message_id = data.get('message_id')
    stream_id = data.get('stream_id')

    if not message_id and not stream_id:
        return jsonify({'error': 'Message ID or Stream ID required'}), 400

    try:
        from flow_models import publish_stream_to_flow

        if message_id and stream_id:
            # Publishing specific message from a stream
            post_id = publish_stream_to_flow(stream_id, message_id, user['id'])
            if post_id:
                return jsonify({'success': True, 'post_id': post_id})
            else:
                return jsonify({'error': 'Cannot publish: stream does not allow publishing or not a member'}), 403
        else:
            return jsonify({'error': 'Both message_id and stream_id are required'}), 400

    except Exception as e:
        logger.error(f'Publish error: {str(e)}')
        return jsonify({'error': 'Failed to publish'}), 500


@flow_bp.route('/api/flow/streams/<stream_id>/publish-allowed', methods=['GET'])
@require_login
def api_stream_publish_allowed(stream_id):
    """Check if current user can publish to Flow from a specific stream."""
    user = get_current_user()

    # Check if user is a member
    membership = get_one('''
        SELECT * FROM flow_channel_members WHERE channel_id = ? AND user_id = ?
    ''', (stream_id, user['id']))

    if not membership:
        return jsonify({'allowed': False, 'reason': 'Not a member'})

    # Check stream settings
    stream = get_one('SELECT settings FROM flow_channels WHERE id = ?', (stream_id,))
    if not stream:
        return jsonify({'allowed': False, 'reason': 'Stream not found'})

    settings = {}
    if stream.get('settings'):
        try:
            import json
            settings = json.loads(stream['settings']) if isinstance(stream['settings'], str) else stream['settings']
        except:
            settings = {}

    if settings.get('allow_publish_to_flow', False):
        return jsonify({'allowed': True})
    else:
        return jsonify({'allowed': False, 'reason': 'Stream does not allow publishing to Flow'})


# ============================================================================
# USER PROFILE & STATUS
# ============================================================================

@flow_bp.route('/profile/<int:user_id>')
@require_login
def user_profile(user_id):
    """View a user's profile."""
    user = get_current_user()
    
    profile = get_one('''
        SELECT fup.*, u.created_at as user_created_at
        FROM flow_user_profiles fup
        JOIN users u ON fup.user_id = u.id
        WHERE fup.user_id = ?
    ''', (user_id,))
    
    if not profile:
        return render_template('flow/error.html', error='User not found', user=user), 404
    
    status = get_user_status(user_id)
    
    # Get shared conversations
    shared_conversations = get_all('''
        SELECT fc.* FROM flow_conversations fc
        JOIN flow_conversation_members fcm1 ON fc.id = fcm1.conversation_id AND fcm1.user_id = ?
        JOIN flow_conversation_members fcm2 ON fc.id = fcm2.conversation_id AND fcm2.user_id = ?
        WHERE fc.conversation_type = 'private'
    ''', (user['id'], user_id))
    
    my_profile = get_flow_profile(user['id'])
    my_status = get_user_status(user['id'])
    
    return render_template('flow/user_profile.html',
        user=user,
        profile=profile,
        status=status,
        shared_conversations=shared_conversations,
        is_blocked=is_user_blocked(user['id'], user_id),
        page_title=profile['display_name']
    )


@flow_bp.route('/settings/profile')
@require_login
def settings_profile():
    """Edit profile settings."""
    user = get_current_user()
    profile = get_flow_profile(user['id'])
    
    return render_template('flow/settings_profile.html',
        user=user,
        profile=profile,
        status=get_user_status(user['id']),
        page_title='Profile Settings'
    )


@flow_bp.route('/settings')
@require_login
def settings():
    """User settings."""
    user = get_current_user()
    profile = get_flow_profile(user['id'])
    settings_data = get_user_settings(user['id'])
    
    return render_template('flow/settings.html',
        user=user,
        profile=profile,
        status=get_user_status(user['id']),
        settings=settings_data,
        page_title='Settings'
    )


@flow_bp.route('/api/settings/update', methods=['POST'])
@require_login
def api_update_settings():
    """Update user settings and profile."""
    user = get_current_user()
    data = safe_get_json()

    # Update user settings (flow_user_settings table)
    update_user_settings(user['id'], data)

    # Update profile data (flow_user_profiles table)
    profile_fields = ['display_name', 'username', 'bio', 'department', 'job_title', 'phone', 'avatar_url']
    profile_data = {k: v for k, v in data.items() if k in profile_fields}
    if profile_data:
        update_flow_profile(user['id'], profile_data)

    return jsonify({'success': True})


@flow_bp.route('/api/status/set', methods=['POST'])
@require_login
def api_set_status():
    """Set user status."""
    user = get_current_user()
    data = safe_get_json()
    
    status_type = data.get('status_type', 'online')
    status_text = data.get('status_text')
    expires_in_hours = data.get('expires_in_hours')
    
    set_user_status(user['id'], status_type, status_text, expires_in_hours)
    
    return jsonify({'success': True})


@flow_bp.route('/api/block/<int:user_id>', methods=['POST'])
@require_login
def api_block_user(user_id):
    """Block a user."""
    user = get_current_user()
    
    if user_id == user['id']:
        return jsonify({'error': 'Cannot block yourself'}), 400
    
    block_user(user['id'], user_id)
    return jsonify({'success': True})


@flow_bp.route('/api/unblock/<int:user_id>', methods=['POST'])
@require_login
def api_unblock_user(user_id):
    """Unblock a user."""
    user = get_current_user()
    
    unblock_user(user['id'], user_id)
    return jsonify({'success': True})


# ============================================================================
# PUSH NOTIFICATIONS
# ============================================================================

@flow_bp.route('/api/push/subscribe', methods=['POST'])
@require_login
def api_push_subscribe():
    """Subscribe to push notifications."""
    user = get_current_user()
    data = safe_get_json()
    
    if not data or 'subscription' not in data:
        return jsonify({'error': 'Subscription data required'}), 400
    
    subscription = data['subscription']
    endpoint = subscription.get('endpoint')
    keys = subscription.get('keys', {})
    p256dh = keys.get('p256dh', '')
    auth = keys.get('auth', '')
    
    if not endpoint or not p256dh or not auth:
        return jsonify({'error': 'Invalid subscription data'}), 400
    
    # Get device info
    device_info = {
        'user_agent': request.user_agent.string if request.user_agent else None,
        'platform': request.user_agent.platform if request.user_agent else None,
        'browser': request.user_agent.browser if request.user_agent else None
    }
    
    # Detect browser
    browser = 'unknown'
    if request.user_agent:
        if request.user_agent.browser == 'Mobile Safari':
            browser = 'safari-ios'
        elif request.user_agent.browser == 'Chrome':
            browser = 'chrome'
        elif request.user_agent.browser == 'Firefox':
            browser = 'firefox'
        elif request.user_agent.browser == 'Edge':
            browser = 'edge'
    
    # Save subscription
    save_push_subscription(
        user['id'],
        endpoint,
        p256dh,
        auth,
        device_info,
        browser
    )
    
    log_audit(user['id'], 'push_subscribe', {'browser': browser}, 'flow')
    
    return jsonify({'success': True, 'message': 'Push subscription saved'})


@flow_bp.route('/api/push/unsubscribe', methods=['POST'])
@require_login
def api_push_unsubscribe():
    """Unsubscribe from push notifications."""
    user = get_current_user()
    data = safe_get_json() or {}
    endpoint = data.get('endpoint')
    
    remove_push_subscription(user['id'], endpoint)
    
    return jsonify({'success': True, 'message': 'Push subscription removed'})


@flow_bp.route('/api/push/status')
@require_login
def api_push_status():
    """Get push notification status for current user."""
    user = get_current_user()
    
    has_subscription = has_push_subscription(user['id'])
    subscriptions = get_all_active_push_subscriptions(user['id'])
    
    return jsonify({
        'enabled': has_subscription,
        'subscription_count': len(subscriptions),
        'subscriptions': [{
            'browser': sub.get('browser'),
            'device_info': sub.get('device_info'),
            'created_at': sub.get('created_at'),
            'last_used_at': sub.get('last_used_at')
        } for sub in subscriptions]
    })


@flow_bp.route('/api/push/test', methods=['POST'])
@require_login
def api_push_test():
    """Send a test push notification."""
    user = get_current_user()
    
    # Check if user has subscription
    if not has_push_subscription(user['id']):
        return jsonify({'error': 'No push subscription found'}), 400
    
    # Send test notification
    success = send_push_notification(
        user['id'],
        'flow_reminder',
        '🔔 Test Notification',
        'Your push notifications are working!',
        {'url': '/flow/'}
    )
    
    if success:
        return jsonify({'success': True, 'message': 'Test notification sent'})
    else:
        return jsonify({'error': 'Failed to send notification'}), 500


@flow_bp.route('/api/push/logs')
@require_login
def api_push_logs():
    """Get push notification logs for current user."""
    user = get_current_user()
    limit = int(request.args.get('limit', 50))
    
    logs = get_push_notification_logs(user['id'], limit)

    return jsonify({'logs': logs})


@flow_bp.route('/api/push/vapid-key')
@require_login
def api_push_vapid_key():
    """Get the VAPID public key for push subscription."""
    from flow_models import get_vapid_public_key
    return jsonify({
        'vapidPublicKey': get_vapid_public_key()
    })


@flow_bp.route('/api/notifications/push-toggle', methods=['POST'])
@require_login
def api_toggle_push_notifications():
    """Toggle push notifications on/off for a user."""
    user = get_current_user()
    data = safe_get_json()
    enabled = data.get('enabled', True)
    
    if enabled:
        # Re-enable push - subscription should already exist
        pass
    else:
        # Disable push - remove subscriptions
        remove_push_subscription(user['id'])
    
    return jsonify({'success': True, 'enabled': enabled})


# ============================================================================
# FILE UPLOADS
# ============================================================================

@flow_bp.route('/api/upload', methods=['POST'])
@require_login
def api_upload_file():
    """Upload a file."""
    user = get_current_user()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check file size
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    
    if size > FLOW_MAX_CONTENT_LENGTH:
        return jsonify({'error': 'File too large (max 2GB)'}), 400
    
    # Get file type
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({'error': f'File type not allowed: {ext}'}), 400
    
    # Generate unique filename
    unique_id = generate_id()
    safe_filename = f"{unique_id}_{filename}"
    
    # Determine upload subfolder
    if ext in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
        subfolder = 'images'
    elif ext in {'mp4', 'webm', 'mov'}:
        subfolder = 'videos'
    elif ext in {'mp3', 'wav', 'ogg'}:
        subfolder = 'audio'
    else:
        subfolder = 'files'
    
    filepath = os.path.join(FLOW_UPLOAD_FOLDER, subfolder, safe_filename)
    file.save(filepath)
    
    # Return file info
    file_url = f'/static/flow_uploads/{subfolder}/{safe_filename}'
    
    return jsonify({
        'success': True,
        'file_id': unique_id,
        'file_name': filename,
        'file_url': file_url,
        'file_type': subfolder.rstrip('s'),
        'file_size': size,
        'mime_type': file.content_type
    })


@flow_bp.route('/files/<file_id>')
@require_login
def get_file(file_id):
    """Download/view a file."""
    user = get_current_user()
    
    # Find the file by ID prefix
    for subfolder in ['images', 'videos', 'audio', 'files']:
        folder_path = os.path.join(FLOW_UPLOAD_FOLDER, subfolder)
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                if filename.startswith(file_id):
                    filepath = os.path.join(folder_path, filename)
                    return send_file(filepath)
    
    return jsonify({'error': 'File not found'}), 404


@flow_bp.route('/api/upload/avatar', methods=['POST'])
@require_login
def api_upload_avatar():
    """Upload an avatar image (for user profile, group, or channel)."""
    user = get_current_user()

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    allowed_image = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    if ext not in allowed_image:
        return jsonify({'error': f'Only image files are allowed: {", ".join(allowed_image)}'}), 400

    # Limit to 5MB
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > 5 * 1024 * 1024:
        return jsonify({'error': 'Image too large (max 5MB)'}), 400

    unique_id = generate_id()
    safe_filename = f"avatar_{unique_id}.{ext}"
    avatars_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'flow_uploads', 'avatars')
    os.makedirs(avatars_folder, exist_ok=True)

    filepath = os.path.join(avatars_folder, safe_filename)
    file.save(filepath)

    avatar_url = f'/static/flow_uploads/avatars/{safe_filename}'

    # Optionally update the target entity
    target_type = request.form.get('target_type')  # 'user', 'group', 'channel'
    target_id = request.form.get('target_id')

    if target_type == 'user':
        from flow_models import get_db_context
        with get_db_context() as db:
            db.execute('UPDATE flow_user_profiles SET avatar_url = ? WHERE user_id = ?', (avatar_url, user['id']))
        # Also update the conversation avatar for all DM conversations with this user
        with get_db_context() as db:
            db.execute('''
                UPDATE flow_conversations SET avatar_url = ?
                WHERE conversation_type = 'direct'
                AND id IN (
                    SELECT conversation_id FROM flow_conversation_members
                    WHERE user_id = ? AND role = 'member'
                    AND conversation_id NOT IN (
                        SELECT conversation_id FROM flow_conversation_members
                        WHERE user_id != ? AND role = 'member'
                    )
                )
            ''', (avatar_url, user['id'], user['id']))

    elif target_type == 'group' and target_id:
        update_group(target_id, {'avatar_url': avatar_url})

    elif target_type == 'channel' and target_id:
        update_channel(target_id, {'avatar_url': avatar_url})

    return jsonify({'success': True, 'avatar_url': avatar_url})


# ============================================================================
# GROUP & CHANNEL SETTINGS
# ============================================================================

@flow_bp.route('/api/groups/<group_id>/update', methods=['POST'])
@require_login
def api_update_group(group_id):
    """Update group settings (name, description, avatar_url)."""
    user = get_current_user()
    data = safe_get_json() or {}

    group = get_one('SELECT * FROM flow_groups WHERE id = ?', (group_id,))
    if not group:
        return jsonify({'error': 'Group not found'}), 404

    membership = get_one('''
        SELECT * FROM flow_group_members WHERE group_id = ? AND user_id = ? AND role IN ('owner', 'admin')
    ''', (group_id, user['id']))

    if not membership:
        return jsonify({'error': 'Permission denied'}), 403

    update_fields = {}
    if 'name' in data:
        update_fields['name'] = data['name'].strip()
    if 'description' in data:
        update_fields['description'] = data['description'].strip()
    if 'avatar_url' in data:
        update_fields['avatar_url'] = data['avatar_url'].strip()

    if update_fields:
        update_group(group_id, update_fields)

    return jsonify({'success': True})


@flow_bp.route('/api/channels/<channel_id>/update', methods=['POST'])
@require_login
def api_update_channel(channel_id):
    """Update channel settings (name, description, category, avatar_url, settings)."""
    user = get_current_user()
    data = safe_get_json() or {}

    # Find by UUID or channel_id
    channel = get_one('''
        SELECT id, name, description, avatar_url, channel_type, category,
               is_archived, created_by, created_at, updated_at, settings, invite_code, channel_id
        FROM flow_channels WHERE id = ?
    ''', (channel_id,))
    if not channel:
        channel = get_one('''
            SELECT id, name, description, avatar_url, channel_type, category,
                   is_archived, created_by, created_at, updated_at, settings, invite_code, channel_id
            FROM flow_channels WHERE channel_id = ?
        ''', (channel_id,))
    if not channel:
        return jsonify({'error': 'Channel not found'}), 404

    membership = get_one('''
        SELECT * FROM flow_channel_members WHERE channel_id = ? AND user_id = ? AND role = 'admin'
    ''', (channel['id'], user['id']))

    if not membership and not user_has_permission(user['id'], 'flow', 'channels', 'admin'):
        return jsonify({'error': 'Permission denied'}), 403

    update_fields = {}
    if 'name' in data:
        update_fields['name'] = data['name'].strip()
    if 'description' in data:
        update_fields['description'] = data['description'].strip()
    if 'category' in data:
        update_fields['category'] = data['category'].strip()
    if 'avatar_url' in data:
        update_fields['avatar_url'] = data['avatar_url'].strip()
    if 'settings' in data:
        # Parse and merge settings
        import json
        current_settings = {}
        if channel.get('settings'):
            if isinstance(channel['settings'], str):
                current_settings = json.loads(channel['settings'])
            else:
                current_settings = channel['settings']

        new_settings = data['settings']
        if isinstance(new_settings, str):
            new_settings = json.loads(new_settings)

        # Merge settings
        current_settings.update(new_settings)
        update_fields['settings'] = json.dumps(current_settings)

    if update_fields:
        update_channel(channel['id'], update_fields)

    return jsonify({'success': True})


# ============================================================================
# TYPING INDICATORS & PRESENCE
# ============================================================================

@flow_bp.route('/api/typing', methods=['POST'])
@require_login
def api_set_typing():
    """Set typing indicator."""
    user = get_current_user()
    data = safe_get_json()
    
    conversation_id = data.get('conversation_id')
    is_typing = data.get('is_typing', True)
    
    if not conversation_id:
        return jsonify({'error': 'Conversation ID required'}), 400
    
    with get_db_context() as db:
        db.execute('''
            INSERT OR REPLACE INTO flow_typing_indicators (conversation_id, user_id, is_typing, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (conversation_id, user['id'], 1 if is_typing else 0, datetime.now().isoformat()))
    
    return jsonify({'success': True})


@flow_bp.route('/api/typing/<conversation_id>')
@require_login
def api_get_typing(conversation_id):
    """Get typing indicators for a conversation."""
    user = get_current_user()
    
    # Get users currently typing (excluding current user)
    typing_users = get_all('''
        SELECT fti.user_id, fup.display_name, fup.avatar_url
        FROM flow_typing_indicators fti
        LEFT JOIN flow_user_profiles fup ON fti.user_id = fup.user_id
        WHERE fti.conversation_id = ? 
        AND fti.user_id != ?
        AND fti.is_typing = 1
        AND fti.updated_at > ?
    ''', (conversation_id, user['id'], (datetime.now() - timedelta(minutes=1)).isoformat()))
    
    return jsonify({'typing': typing_users})


@flow_bp.route('/api/presence/update', methods=['POST'])
@require_login
def api_update_presence():
    """Update user presence."""
    user = get_current_user()
    data = safe_get_json()
    
    status_type = data.get('status', 'online')
    update_presence(user['id'], status_type)
    
    return jsonify({'success': True})


# ============================================================================
# REMINDERS
# ============================================================================

@flow_bp.route('/reminders')
@require_login
def reminders():
    """View active reminders."""
    user = get_current_user()
    
    reminders = get_all('''
        SELECT mr.*, m.content, m.conversation_id, fc.name as conversation_name,
               fup.display_name as sender_name
        FROM flow_message_reminders mr
        JOIN flow_messages m ON mr.message_id = m.id
        LEFT JOIN flow_conversations fc ON m.conversation_id = fc.id
        LEFT JOIN flow_user_profiles fup ON m.sender_id = fup.user_id
        WHERE mr.user_id = ? AND mr.is_completed = 0 AND mr.is_dismissed = 0
        ORDER BY mr.remind_at
    ''', (user['id'],))
    
    profile = get_flow_profile(user['id'])
    status = get_user_status(user['id'])
    
    return render_template('flow/reminders.html',
        user=user,
        profile=profile,
        status=status,
        reminders=reminders,
        page_title='Reminders'
    )


@flow_bp.route('/api/reminders/<int:reminder_id>/complete', methods=['POST'])
@require_login
def api_complete_reminder(reminder_id):
    """Mark a reminder as completed."""
    user = get_current_user()
    
    # Verify ownership
    reminder = get_one('SELECT * FROM flow_message_reminders WHERE id = ? AND user_id = ?', (reminder_id, user['id']))
    if not reminder:
        return jsonify({'error': 'Reminder not found'}), 404
    
    complete_reminder(reminder_id)
    return jsonify({'success': True})


@flow_bp.route('/api/reminders/<int:reminder_id>/dismiss', methods=['POST'])
@require_login
def api_dismiss_reminder(reminder_id):
    """Dismiss a reminder."""
    user = get_current_user()
    
    with get_db_context() as db:
        db.execute('''
            UPDATE flow_message_reminders SET is_dismissed = 1 WHERE id = ? AND user_id = ?
        ''', (reminder_id, user['id']))
    
    return jsonify({'success': True})


# ============================================================================
# SHARED MEDIA
# ============================================================================

@flow_bp.route('/shared-media')
@require_login
def shared_media():
    """View shared media across all conversations."""
    user = get_current_user()
    
    # Get user's accessible conversations
    conv_ids = get_all('''
        SELECT conversation_id FROM flow_conversation_members WHERE user_id = ?
    ''', (user['id'],))
    conv_ids = [c['conversation_id'] for c in conv_ids]
    
    if not conv_ids:
        media = []
    else:
        placeholders = ','.join(['?' for _ in conv_ids])
        media = get_all(f'''
            SELECT m.*, fma.file_name, fma.file_path, fma.file_type, fma.file_size,
                   fma.thumbnail_path, fma.duration_seconds, fma.width, fma.height,
                   fup.display_name as uploader_name, fc.name as conversation_name
            FROM flow_messages m
            JOIN flow_message_attachments fma ON m.id = fma.message_id
            LEFT JOIN flow_user_profiles fup ON m.sender_id = fup.user_id
            LEFT JOIN flow_conversations fc ON m.conversation_id = fc.id
            WHERE m.conversation_id IN ({placeholders})
            AND m.is_deleted = 0
            AND fma.file_type IN ('image', 'video', 'audio', 'document')
            ORDER BY m.created_at DESC
            LIMIT 200
        ''', conv_ids)
    
    profile = get_flow_profile(user['id'])
    status = get_user_status(user['id'])
    
    return render_template('flow/shared_media.html',
        user=user,
        profile=profile,
        status=status,
        media=media,
        page_title='Shared Media'
    )


# ============================================================================
# API HELPERS
# ============================================================================

@flow_bp.route('/api/seed/all', methods=['POST'])
@require_login
def api_seed_all():
    """Create sample channels, groups, private chats, and test messages."""
    user = get_current_user()

    # Only admin users can seed
    if not user_has_permission(user['id'], 'flow', 'channels', 'admin'):
        return jsonify({'error': 'Permission denied'}), 403

    from flow_models import (
        get_all, get_one, get_db_context, generate_id,
        create_channel, create_group, get_or_create_private_conversation, send_message
    )

    # Get users
    users = get_all('SELECT id, username FROM users LIMIT 20')
    if not users:
        return jsonify({'error': 'No users found'}), 400

    user_ids = [u['id'] for u in users]
    creator_id = user_ids[0]

    # 1. Create sample channels
    sample_channels = [
        ('General', 'general', 'General discussions and announcements', 'public', 'Company'),
        ('Engineering', 'engineering', 'Engineering team discussions', 'public', 'Departments'),
        ('Sales Team', 'sales-team', 'Sales discussions', 'public', 'Departments'),
        ('Marketing', 'marketing', 'Marketing campaigns', 'public', 'Departments'),
        ('HR & People', 'hr-people', 'Human resources', 'public', 'Departments'),
        ('Random', 'random', 'Random chat', 'public', 'Social'),
        ('Announcements', 'announcements', 'Company announcements', 'public', 'Company'),
    ]

    from flow_models import validate_channel_id, is_channel_id_available

    for name, channel_id, desc, ctype, cat in sample_channels:
        if validate_channel_id(channel_id) and is_channel_id_available(channel_id):
            db_id = create_channel(name, desc, creator_id, ctype, cat, channel_id)
            logger.info(f'Created channel: {name}')

            # Add members
            with get_db_context() as db:
                for uid in user_ids[:5]:
                    db.execute('INSERT OR IGNORE INTO flow_channel_members (channel_id, user_id, role) VALUES (?, ?, ?)',
                             (db_id, uid, 'member'))

                # Create conversation for channel
                conv_id = generate_id()
                db.execute('''INSERT INTO flow_conversations (id, name, conversation_type, created_by, created_at)
                             VALUES (?, ?, 'channel', ?, ?)''', (conv_id, name, creator_id, datetime.now().isoformat()))
                db.execute('INSERT INTO flow_conversation_members (conversation_id, user_id, role) VALUES (?, ?, ?)',
                          (conv_id, creator_id, 'admin'))
                for uid in user_ids[:5]:
                    db.execute('INSERT OR IGNORE INTO flow_conversation_members (conversation_id, user_id, role) VALUES (?, ?, ?)',
                              (conv_id, uid, 'member'))

                # Add sample messages
                messages = [
                    f"Welcome to #{name} channel! 👋",
                    f"This is the {name} channel for team discussions.",
                    "Feel free to share your thoughts and updates here.",
                    "Don't hesitate to ask questions!",
                ]
                for i, msg in enumerate(messages):
                    msg_id = generate_id()
                    db.execute('''INSERT INTO flow_messages (id, conversation_id, sender_id, content, message_type, created_at)
                                 VALUES (?, ?, ?, ?, 'text', ?)''',
                              (msg_id, conv_id, creator_id, msg, (datetime.now() - timedelta(hours=len(messages)-i)).isoformat()))

    # 2. Create sample groups
    sample_groups = [
        ('Project Alpha Team', 'Collaboration group for Project Alpha'),
        ('Weekend Plans', 'Planning weekend activities'),
        ('Book Club', 'Monthly book discussions'),
        ('Sports Fans', 'Sports enthusiasts group'),
        ('Foodies', 'Food and restaurant recommendations'),
    ]

    for i, (name, desc) in enumerate(sample_groups):
        member_ids = user_ids[i:i+4] if i+4 <= len(user_ids) else user_ids[:4]
        grp_id = create_group(name, desc, creator_id, 'private', member_ids)
        logger.info(f'Created group: {name}')

        # Add messages to group
        with get_db_context() as db:
            conv = get_one('SELECT id FROM flow_conversations WHERE name = ? AND conversation_type = ?', (name, 'group'))
            if conv:
                messages = [
                    f"Welcome to {name}! 🎉",
                    "Thanks for creating this group!",
                    "Looking forward to great discussions.",
                ]
                for j, msg in enumerate(messages):
                    msg_id = generate_id()
                    sender = member_ids[j % len(member_ids)]
                    db.execute('''INSERT INTO flow_messages (id, conversation_id, sender_id, content, message_type, created_at)
                                 VALUES (?, ?, ?, ?, 'text', ?)''',
                              (msg_id, conv['id'], sender, msg, (datetime.now() - timedelta(hours=len(messages)-j)).isoformat()))

    # 3. Create private chats between users
    private_messages = [
        "Hey! How are you?",
        "I'm good, thanks! Working on the new project.",
        "That sounds great! Let me know if you need any help.",
        "Will do! Talk later 👋",
    ]

    for i in range(min(5, len(user_ids)-1)):
        conv_id = get_or_create_private_conversation(user_ids[i], user_ids[i+1])
        with get_db_context() as db:
            for j, msg in enumerate(private_messages):
                msg_id = generate_id()
                sender = user_ids[i] if j % 2 == 0 else user_ids[i+1]
                db.execute('''INSERT INTO flow_messages (id, conversation_id, sender_id, content, message_type, created_at)
                             VALUES (?, ?, ?, ?, 'text', ?)''',
                          (msg_id, conv_id, sender, msg, (datetime.now() - timedelta(hours=len(private_messages)-j)).isoformat()))
        logger.info(f'Created private chat: user_{i} <-> user_{i+1}')

    return jsonify({'success': True, 'message': 'Sample data created successfully'})


@flow_bp.route('/api/test/messages', methods=['POST'])
@require_login
def api_seed_test_messages():
    """Add test messages to all conversations."""
    user = get_current_user()
    
    # Only admin users can seed test messages
    if not user_has_permission(user['id'], 'flow', 'channels', 'admin'):
        return jsonify({'error': 'Permission denied'}), 403
    
    result = seed_test_messages()
    
    if result:
        return jsonify({'success': True, 'message': 'Test messages added successfully'})
    else:
        return jsonify({'error': 'Failed to add test messages'}), 500


@flow_bp.route('/api/users')
@require_login
def api_get_users():
    """Get all users for mention autocomplete, etc."""
    user = get_current_user()
    query = request.args.get('q', '')
    
    users = get_all('''
        SELECT fup.user_id, fup.username, fup.display_name, fup.avatar_url, fup.department
        FROM flow_user_profiles fup
        JOIN users u ON fup.user_id = u.id
        WHERE (fup.display_name LIKE ? OR fup.username LIKE ?)
        ORDER BY fup.display_name
        LIMIT 20
    ''', (f'%{query}%', f'%{query}%'))
    
    return jsonify({'users': users})


@flow_bp.route('/api/user/<int:user_id>')
@require_login
def api_get_user(user_id):
    """Get a specific user's info."""
    profile = get_one('''
        SELECT fup.*
        FROM flow_user_profiles fup
        JOIN users u ON fup.user_id = u.id
        WHERE fup.user_id = ?
    ''', (user_id,))
    
    if not profile:
        return jsonify({'error': 'User not found'}), 404
    
    status = get_user_status(user_id)
    
    return jsonify({'profile': profile, 'status': status})


# ============================================================================
# POLLING ENDPOINT (for real-time-like updates)
# ============================================================================

@flow_bp.route('/api/updates')
@require_login
def api_get_updates():
    """Get updates for polling-based real-time."""
    user = get_current_user()

    # Get unread counts
    unread_data = get_all('''
        SELECT conversation_id, unread_count FROM flow_conversation_members
        WHERE user_id = ?
    ''', (user['id'],))

    # Get mention counts per conversation
    mention_data = get_all('''
        SELECT fm.conversation_id, COUNT(*) as mention_count
        FROM flow_message_mentions fmm
        JOIN flow_messages fm ON fmm.message_id = fm.id
        WHERE fmm.user_id = ? AND fm.is_deleted = 0
        GROUP BY fm.conversation_id
    ''', (user['id'],))

    # Get due reminders
    due_reminders = get_due_reminders()
    for reminder in due_reminders:
        complete_reminder(reminder['id'])
        create_notification(
            user['id'],
            'reminder',
            'Reminder',
            reminder.get('reminder_text') or f'Reminder: {reminder.get("content", "")[:50]}',
            f'/flow/chat/{reminder.get("conversation_id")}'
        )

    # Get unread notification count
    notif_count = get_unread_notification_count(user['id'])

    return jsonify({
        'unread': {item['conversation_id']: item['unread_count'] for item in unread_data},
        'mentions': {item['conversation_id']: item['mention_count'] for item in mention_data},
        'reminders_triggered': len(due_reminders),
        'notification_count': notif_count
    })


# ============================================================================
# REGISTER BLUEPRINT
# ============================================================================

def register_flow_routes(app):
    """Register FLOW routes with the Flask app."""
    app.register_blueprint(flow_bp)
    
    # Inject format_time function into templates for this blueprint
    from datetime import datetime
    @app.context_processor
    def inject_flow_format_time():
        def format_time(value):
            if value is None:
                return ''
            if isinstance(value, str):
                try:
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    return value
            elif isinstance(value, datetime):
                dt = value
            else:
                return str(value)
            
            now = datetime.now()
            diff = now - dt
            total_seconds = diff.total_seconds()
            
            if total_seconds < 0:
                return dt.strftime('%H:%M')
            if total_seconds < 60:
                return 'now'
            if total_seconds < 3600:
                minutes = int(total_seconds / 60)
                return f'{minutes}m'
            if total_seconds < 86400:
                hours = int(total_seconds / 3600)
                return f'{hours}h'
            if total_seconds < 604800:
                days = int(total_seconds / 86400)
                return f'{days}d'
            return dt.strftime('%Y-%m-%d')
        return {
            'format_time': format_time,
            'escape_html': lambda text: __import__('html').escape(text) if text else ''
        }
    
    # Initialize FLOW tables on first registration
    try:
        initialize_flow()
    except Exception as e:
        logger.warning(f'Initialization warning: {e}')
