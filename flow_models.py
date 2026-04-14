"""
FLOW - Enterprise Internal Communication Platform
Database Models Module

This module defines all database tables and helper functions for the FLOW
internal communication platform including private chats, groups, channels,
messages, calls, meetings, notifications, and more.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from contextlib import contextmanager
import uuid
import json

# Import the database helper from the main app
try:
    from database import get_db, get_db_context, get_one, get_all, log_audit
except ImportError:
    # Fallback if database.py is not available
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'warehouse.db')
    
    def get_db():
        conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA foreign_keys=ON')
        return conn
    
    @contextmanager
    def get_db_context():
        db = get_db()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    
    def get_one(sql, params=None):
        with get_db_context() as db:
            cur = db.execute(sql, params or ())
            row = cur.fetchone()
            return dict(row) if row else None
    
    def get_all(sql, params=None):
        with get_db_context() as db:
            cur = db.execute(sql, params or ())
            return [dict(row) for row in cur.fetchall()]
    
    def log_audit(user_id, action, details, module='flow'):
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'warehouse.db')


# ============================================================================
# FLOW TABLES INITIALIZATION
# ============================================================================

def initialize_flow_tables():
    """Initialize all FLOW tables in the database."""
    
    with get_db_context() as db:
        # Enable WAL mode for better concurrency
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('PRAGMA foreign_keys=ON')
        
        # Flow user profiles (extends main app users)
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_user_profiles (
                user_id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                avatar_url TEXT,
                bio TEXT,
                department TEXT,
                job_title TEXT,
                phone TEXT,
                email TEXT,
                is_bot INTEGER DEFAULT 0,
                last_seen_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # User presence and status
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_user_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                status_type TEXT DEFAULT 'online',
                status_text TEXT,
                status_expires_at DATETIME,
                is_custom INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Conversations (private, group, channel base)
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_conversations (
                id TEXT PRIMARY KEY,
                conversation_type TEXT NOT NULL,
                name TEXT,
                description TEXT,
                avatar_url TEXT,
                created_by INTEGER NOT NULL,
                is_archived INTEGER DEFAULT 0,
                is_pinned INTEGER DEFAULT 0,
                last_message_at DATETIME,
                last_message_preview TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')
        
        # Conversation members
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_conversation_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT DEFAULT 'member',
                nickname TEXT,
                is_muted INTEGER DEFAULT 0,
                is_pinned INTEGER DEFAULT 0,
                is_archived INTEGER DEFAULT 0,
                unread_count INTEGER DEFAULT 0,
                last_read_at DATETIME,
                notifications_enabled INTEGER DEFAULT 1,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES flow_conversations(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(conversation_id, user_id)
            )
        ''')
        
        # Messages
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                sender_id INTEGER,
                message_type TEXT DEFAULT 'text',
                content TEXT,
                content_html TEXT,
                metadata TEXT,
                reply_to_id TEXT,
                forwarded_from_id TEXT,
                is_edited INTEGER DEFAULT 0,
                edited_at DATETIME,
                is_deleted INTEGER DEFAULT 0,
                deleted_at DATETIME,
                delete_scope TEXT DEFAULT 'me',
                is_pinned INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES flow_conversations(id) ON DELETE CASCADE,
                FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE SET NULL,
                FOREIGN KEY (reply_to_id) REFERENCES flow_messages(id) ON DELETE SET NULL
            )
        ''')
        
        # Message attachments
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_message_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT,
                file_size INTEGER,
                mime_type TEXT,
                thumbnail_path TEXT,
                duration_seconds INTEGER,
                width INTEGER,
                height INTEGER,
                download_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES flow_messages(id) ON DELETE CASCADE
            )
        ''')
        
        # Message reactions
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_message_reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                emoji TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES flow_messages(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(message_id, user_id, emoji)
            )
        ''')
        
        # Message mentions
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_message_mentions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES flow_messages(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(message_id, user_id)
            )
        ''')
        
        # Saved messages (user's personal save)
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_saved_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message_id TEXT NOT NULL,
                saved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (message_id) REFERENCES flow_messages(id) ON DELETE CASCADE,
                UNIQUE(user_id, message_id)
            )
        ''')
        
        # Message reminders
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_message_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message_id TEXT NOT NULL,
                reminder_text TEXT,
                remind_at DATETIME NOT NULL,
                is_completed INTEGER DEFAULT 0,
                is_dismissed INTEGER DEFAULT 0,
                completed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (message_id) REFERENCES flow_messages(id) ON DELETE CASCADE
            )
        ''')
        
        # Channels (extends conversations)
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_channels (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                channel_id TEXT UNIQUE,
                description TEXT,
                avatar_url TEXT,
                channel_type TEXT DEFAULT 'public',
                category TEXT,
                invite_code TEXT,
                is_archived INTEGER DEFAULT 0,
                created_by INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                settings TEXT,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        # Add channel_id column if missing (for existing tables created before this column was added)
        cur = db.execute("PRAGMA table_info(flow_channels)")
        existing_cols = [col[1] for col in cur.fetchall()]
        if 'channel_id' not in existing_cols:
            db.execute("ALTER TABLE flow_channels ADD COLUMN channel_id TEXT")
        
        # Channel members
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_channel_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT DEFAULT 'member',
                notifications_enabled INTEGER DEFAULT 1,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (channel_id) REFERENCES flow_channels(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(channel_id, user_id)
            )
        ''')
        
        # Channel categories
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_channel_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                sort_order INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Groups (extends conversations)
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_groups (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                avatar_url TEXT,
                group_type TEXT DEFAULT 'private',
                created_by INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                settings TEXT,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')
        
        # Group members
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_group_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT DEFAULT 'member',
                nickname TEXT,
                notifications_enabled INTEGER DEFAULT 1,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES flow_groups(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(group_id, user_id)
            )
        ''')
        
        # Shared media/files
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_shared_media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT,
                channel_id TEXT,
                uploaded_by INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT,
                file_size INTEGER,
                mime_type TEXT,
                thumbnail_path TEXT,
                duration_seconds INTEGER,
                width INTEGER,
                height INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (uploaded_by) REFERENCES users(id)
            )
        ''')
        
        # Notifications
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                notification_type TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT,
                data TEXT,
                is_read INTEGER DEFAULT 0,
                read_at DATETIME,
                action_url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Call sessions
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_call_sessions (
                id TEXT PRIMARY KEY,
                call_type TEXT NOT NULL,
                initiated_by INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                started_at DATETIME,
                ended_at DATETIME,
                duration_seconds INTEGER,
                recording_url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (initiated_by) REFERENCES users(id)
            )
        ''')
        
        # Call participants
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_call_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                call_status TEXT DEFAULT 'pending',
                joined_at DATETIME,
                left_at DATETIME,
                is_muted INTEGER DEFAULT 0,
                is_video_enabled INTEGER DEFAULT 0,
                FOREIGN KEY (call_id) REFERENCES flow_call_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(call_id, user_id)
            )
        ''')
        
        # Meeting sessions
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_meeting_sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                meeting_type TEXT DEFAULT 'scheduled',
                host_id INTEGER NOT NULL,
                start_time DATETIME,
                end_time DATETIME,
                status TEXT DEFAULT 'scheduled',
                meeting_url TEXT,
                recording_url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (host_id) REFERENCES users(id)
            )
        ''')
        
        # Meeting participants
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_meeting_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT DEFAULT 'participant',
                joined_at DATETIME,
                left_at DATETIME,
                is_muted INTEGER DEFAULT 0,
                is_video_enabled INTEGER DEFAULT 0,
                is_screen_sharing INTEGER DEFAULT 0,
                FOREIGN KEY (meeting_id) REFERENCES flow_meeting_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(meeting_id, user_id)
            )
        ''')
        
        # Meeting chat messages
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_meeting_chat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id TEXT NOT NULL,
                sender_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (meeting_id) REFERENCES flow_meeting_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Typing indicators (temporary tracking)
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_typing_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                is_typing INTEGER DEFAULT 1,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(conversation_id, user_id),
                FOREIGN KEY (conversation_id) REFERENCES flow_conversations(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # User settings
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                language TEXT DEFAULT 'en',
                theme TEXT DEFAULT 'light',
                notification_sound INTEGER DEFAULT 1,
                notification_desktop INTEGER DEFAULT 1,
                notification_mobile INTEGER DEFAULT 1,
                message_preview INTEGER DEFAULT 1,
                show_online_status INTEGER DEFAULT 1,
                show_read_receipts INTEGER DEFAULT 1,
                show_last_seen INTEGER DEFAULT 1,
                auto_download_wifi INTEGER DEFAULT 1,
                auto_download_cellular INTEGER DEFAULT 0,
                compact_mode INTEGER DEFAULT 0,
                emoji_style TEXT DEFAULT 'native',
                gif_provider TEXT DEFAULT 'giphy',
                giphy_api_key TEXT,
                chat_background TEXT DEFAULT 'default',
                chat_background_custom TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Blocked users
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_blocked_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                blocked_user_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (blocked_user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, blocked_user_id)
            )
        ''')
        
        # Push notification subscriptions
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_push_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                endpoint TEXT NOT NULL,
                p256dh TEXT NOT NULL,
                auth TEXT NOT NULL,
                device_info TEXT,
                browser TEXT,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_used_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(endpoint)
            )
        ''')
        
        # Push notification logs
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_push_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                notification_type TEXT NOT NULL,
                title TEXT,
                body TEXT,
                status TEXT DEFAULT 'sent',
                error_message TEXT,
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Scheduled push notifications
        db.execute('''
            CREATE TABLE IF NOT EXISTS flow_push_scheduled (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                reminder_id INTEGER,
                title TEXT NOT NULL,
                body TEXT,
                data TEXT,
                scheduled_for DATETIME NOT NULL,
                is_sent INTEGER DEFAULT 0,
                sent_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Create indexes for performance
        db.execute('CREATE INDEX IF NOT EXISTS idx_messages_conversation ON flow_messages(conversation_id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_messages_sender ON flow_messages(sender_id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_messages_created ON flow_messages(created_at)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_conversation_members_user ON flow_conversation_members(user_id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_notifications_user ON flow_notifications(user_id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_notifications_read ON flow_notifications(is_read)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_reminders_user ON flow_message_reminders(user_id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_reminders_at ON flow_message_reminders(remind_at)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_presence_user ON flow_user_status(user_id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_channel_members ON flow_channel_members(channel_id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_group_members ON flow_group_members(group_id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user ON flow_push_subscriptions(user_id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_push_scheduled_user ON flow_push_scheduled(user_id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_push_scheduled_due ON flow_push_scheduled(is_sent, scheduled_for)')

        # Migration: Add chat_background columns if they don't exist
        try:
            db.execute("ALTER TABLE flow_user_settings ADD COLUMN chat_background TEXT DEFAULT 'default'")
        except:
            pass
        try:
            db.execute("ALTER TABLE flow_user_settings ADD COLUMN chat_background_custom TEXT")
        except:
            pass

        # Migration: Add channel_id and invite_code to flow_channels if they don't exist
        try:
            db.execute("ALTER TABLE flow_channels ADD COLUMN channel_id TEXT UNIQUE")
        except:
            pass
        try:
            db.execute("ALTER TABLE flow_channels ADD COLUMN invite_code TEXT")
        except:
            pass

        db.commit()
        
        import sys
        print("[FLOW] Tables initialized successfully", file=sys.stderr)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_id():
    """Generate a unique ID for Flow entities."""
    return str(uuid.uuid4())


def validate_channel_id(channel_id):
    """
    Validate a channel ID format.
    Channel ID must:
    - Be at least 3 characters
    - Contain only: English letters (a-z, A-Z), numbers (0-9), hyphens (-), and dots (.)
    - Start with a letter or number (not hyphen or dot)
    """
    import re
    if not channel_id or len(channel_id) < 3:
        return False
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9.-]*$', channel_id):
        return False
    return True


def generate_invite_code(length=8):
    """Generate a random invite code for private channels."""
    import random
    import string
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def is_channel_id_available(channel_id):
    """Check if a channel ID is already taken."""
    result = get_one('SELECT 1 FROM flow_channels WHERE channel_id = ?', (channel_id,))
    return result is None


def get_channel_by_channel_id(channel_id):
    """Get a channel by its URL-friendly channel_id (username)."""
    return get_one('SELECT * FROM flow_channels WHERE channel_id = ?', (channel_id,))


def get_channel_by_invite_code(invite_code):
    """Get a private channel by its invite code."""
    return get_one('SELECT * FROM flow_channels WHERE invite_code = ? AND channel_type = ?', (invite_code, 'private'))


def regenerate_invite_code(channel_id, user_id):
    """Regenerate the invite code for a private channel."""
    channel = get_one('SELECT * FROM flow_channels WHERE id = ?', (channel_id,))
    if not channel or channel['channel_type'] != 'private':
        return None

    new_code = generate_invite_code()
    with get_db_context() as db:
        db.execute('UPDATE flow_channels SET invite_code = ? WHERE id = ?', (new_code, channel_id))

    log_audit(user_id, 'channel_regenerate_invite', {'channel_id': channel_id}, 'flow')
    return new_code


def send_channel_message(channel_identifier, sender_id, content, message_type='text', reply_to_id=None, metadata=None):
    """
    Send a message to a channel using either the channel ID or channel_id (username).
    This allows accessing channels via their URL-friendly ID.
    """
    # Try to find channel by channel_id first (username), then by internal id
    channel = get_channel_by_channel_id(channel_identifier)
    if not channel:
        channel = get_one('SELECT * FROM flow_channels WHERE id = ?', (channel_identifier,))

    if not channel:
        return None

    # Get the conversation for this channel
    conv = get_one('''
        SELECT * FROM flow_conversations
        WHERE name = ? AND conversation_type = 'channel'
    ''', (channel['name'],))

    if not conv:
        return None

    return send_message(conv['id'], sender_id, content, message_type, reply_to_id, metadata)


def get_flow_profile(user_id):
    """Get or create a FLOW user profile for a user."""
    profile = get_one('''
        SELECT * FROM flow_user_profiles WHERE user_id = ?
    ''', (user_id,))
    
    if not profile:
        # Get basic info from main users table
        user = get_one('SELECT id, username, email FROM users WHERE id = ?', (user_id,))
        if user:
            with get_db_context() as db:
                db.execute('''
                    INSERT INTO flow_user_profiles (user_id, username, display_name, email)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, user['username'], user['username'].title(), user.get('email', '')))
            profile = get_one('SELECT * FROM flow_user_profiles WHERE user_id = ?', (user_id,))
    
    return profile


def ensure_flow_profile(user_id, display_name=None, username=None):
    """Ensure a FLOW profile exists for a user."""
    profile = get_flow_profile(user_id)
    if not profile:
        user = get_one('SELECT id, username, email FROM users WHERE id = ?', (user_id,))
        if user:
            with get_db_context() as db:
                db.execute('''
                    INSERT INTO flow_user_profiles (user_id, username, display_name, email)
                    VALUES (?, ?, ?, ?)
                ''', (
                    user_id,
                    username or user['username'],
                    display_name or user['username'].title(),
                    user.get('email', '')
                ))
            profile = get_one('SELECT * FROM flow_user_profiles WHERE user_id = ?', (user_id,))
    return profile


def get_conversation_id_for_users(user_ids):
    """Get existing private conversation ID for a set of users, or None."""
    if len(user_ids) != 2:
        return None
    
    user1, user2 = sorted(user_ids)
    
    # Find a private conversation with exactly these 2 members
    result = get_one('''
        SELECT fc.id 
        FROM flow_conversations fc
        JOIN flow_conversation_members fcm1 ON fc.id = fcm1.conversation_id AND fcm1.user_id = ?
        JOIN flow_conversation_members fcm2 ON fc.id = fcm2.conversation_id AND fcm2.user_id = ?
        WHERE fc.conversation_type = 'private'
        AND (SELECT COUNT(*) FROM flow_conversation_members WHERE conversation_id = fc.id) = 2
    ''', (user1, user2))
    
    return result['id'] if result else None


def get_or_create_private_conversation(user1_id, user2_id):
    """Get or create a private conversation between two users."""
    conv_id = get_conversation_id_for_users([user1_id, user2_id])
    
    if conv_id:
        return conv_id
    
    # Create new conversation
    conv_id = generate_id()
    now = datetime.now().isoformat()
    
    with get_db_context() as db:
        db.execute('''
            INSERT INTO flow_conversations (id, conversation_type, created_by, last_message_at)
            VALUES (?, 'private', ?, ?)
        ''', (conv_id, user1_id, now))
        
        # Add both users as members
        db.execute('''
            INSERT INTO flow_conversation_members (conversation_id, user_id, role, last_read_at)
            VALUES (?, ?, 'member', ?)
        ''', (conv_id, user1_id, now))
        
        db.execute('''
            INSERT INTO flow_conversation_members (conversation_id, user_id, role, last_read_at)
            VALUES (?, ?, 'member', ?)
        ''', (conv_id, user2_id, now))
    
    return conv_id


def get_user_saved_messages_conversation(user_id):
    """Get or create the 'Save Messages' conversation for a user."""
    # Save Messages is always a private conversation with self
    conv_id = get_conversation_id_for_users([user_id, user_id])
    
    if conv_id:
        return conv_id
    
    conv_id = generate_id()
    now = datetime.now().isoformat()
    
    with get_db_context() as db:
        db.execute('''
            INSERT INTO flow_conversations (id, conversation_type, name, created_by, last_message_at)
            VALUES (?, 'private', 'Save Messages', ?, ?)
        ''', (conv_id, user_id, now))
        
        db.execute('''
            INSERT INTO flow_conversation_members (conversation_id, user_id, role, last_read_at)
            VALUES (?, ?, 'owner', ?)
        ''', (conv_id, user_id, now))
    
    return conv_id


def send_message(conversation_id, sender_id, content, message_type='text', reply_to_id=None, metadata=None):
    """Send a message to a conversation."""
    import sys
    msg_id = generate_id()
    now = datetime.now().isoformat()
    
    print(f'[FLOW send_message] INSERTING: msg_id={msg_id}, conv={conversation_id}, sender={sender_id}, content={content[:50] if content else "empty"}', file=sys.stderr)
    
    with get_db_context() as db:
        db.execute('''
            INSERT INTO flow_messages (id, conversation_id, sender_id, message_type, content, reply_to_id, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (msg_id, conversation_id, sender_id, message_type, content, reply_to_id, json.dumps(metadata) if metadata else None, now))
        db.commit()

        # Update conversation last message
        preview = content[:100] if content else '[Media]'
        db.execute('''
            UPDATE flow_conversations 
            SET last_message_at = ?, last_message_preview = ?
            WHERE id = ?
        ''', (now, preview, conversation_id))
        db.commit()

        # Update unread counts for other members
        db.execute('''
            UPDATE flow_conversation_members
            SET unread_count = unread_count + 1
            WHERE conversation_id = ? AND user_id != ?
        ''', (conversation_id, sender_id))
        db.commit()
    
    print(f'[FLOW send_message] COMPLETED: msg_id={msg_id}', file=sys.stderr)
    
    # Extract and save mentions
    if content:
        import re
        mentions = re.findall(r'@(\w+)', content)
        for username in mentions:
            mentioned_user = get_one('SELECT user_id FROM flow_user_profiles WHERE username = ?', (username,))
            if mentioned_user:
                with get_db_context() as db:
                    db.execute('''
                        INSERT OR IGNORE INTO flow_message_mentions (message_id, user_id)
                        VALUES (?, ?)
                    ''', (msg_id, mentioned_user['user_id']))
                
                # Create notification for mention
                create_notification(
                    mentioned_user['user_id'],
                    'mention',
                    f'@{username} mentioned you',
                    content[:100],
                    f'/flow/chat/{conversation_id}',
                    sender_id
                )
    
    return msg_id


def add_reaction(message_id, user_id, emoji):
    """Add a reaction to a message."""
    with get_db_context() as db:
        db.execute('''
            INSERT OR REPLACE INTO flow_message_reactions (message_id, user_id, emoji)
            VALUES (?, ?, ?)
        ''', (message_id, user_id, emoji))
        db.commit()
    
    # Notify message sender
    msg = get_one('SELECT sender_id, content FROM flow_messages WHERE id = ?', (message_id,))
    if msg and msg['sender_id'] != user_id:
        reactor = get_one('SELECT display_name FROM flow_user_profiles WHERE user_id = ?', (user_id,))
        create_notification(
            msg['sender_id'],
            'reaction',
            f'{reactor["display_name"]} reacted to your message',
            msg['content'][:50] if msg['content'] else '',
            f'/flow/chat/{message_id}'
        )


def remove_reaction(message_id, user_id, emoji):
    """Remove a reaction from a message."""
    with get_db_context() as db:
        db.execute('''
            DELETE FROM flow_message_reactions
            WHERE message_id = ? AND user_id = ? AND emoji = ?
        ''', (message_id, user_id, emoji))
        db.commit()


def set_reminder(user_id, message_id, remind_at, reminder_text=None):
    """Set a reminder on a message."""
    with get_db_context() as db:
        db.execute('''
            INSERT INTO flow_message_reminders (user_id, message_id, reminder_text, remind_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, message_id, reminder_text, remind_at))
        db.commit()
    
    # Notify the user when reminder is set
    msg = get_one('SELECT sender_id, content FROM flow_messages WHERE id = ?', (message_id,))
    if msg:
        create_notification(
            user_id,
            'reminder_set',
            'Reminder set',
            f'Reminder for: {msg["content"][:50] if msg["content"] else "message"}',
            f'/flow/chat/{message_id}'
        )


def get_due_reminders():
    """Get all reminders that are due now."""
    now = datetime.now().isoformat()
    return get_all('''
        SELECT mr.*, fm.content, fm.conversation_id, fup.display_name as sender_name
        FROM flow_message_reminders mr
        JOIN flow_messages fm ON mr.message_id = fm.id
        LEFT JOIN flow_user_profiles fup ON fm.sender_id = fup.user_id
        WHERE mr.is_completed = 0 
        AND mr.is_dismissed = 0
        AND mr.remind_at <= ?
    ''', (now,))


def complete_reminder(reminder_id):
    """Mark a reminder as completed."""
    with get_db_context() as db:
        db.execute('''
            UPDATE flow_message_reminders 
            SET is_completed = 1, completed_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), reminder_id))


def create_notification(user_id, notification_type, title, body, action_url=None, from_user_id=None):
    """Create a notification for a user."""
    with get_db_context() as db:
        db.execute('''
            INSERT INTO flow_notifications (user_id, notification_type, title, body, action_url)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, notification_type, title, body, action_url))
        db.commit()
    
    # Also add to main app notifications if available
    try:
        from database import create_notification as main_create_notification
        main_create_notification(
            user_id=user_id,
            title=f"FLOW: {title}",
            message=body,
            notification_type='info',
            created_by=from_user_id
        )
    except:
        pass


def get_user_conversations(user_id, includeArchived=False):
    """Get all conversations for a user."""
    archived_cond = "" if includeArchived else "AND fc.is_archived = 0"
    
    return get_all('''
        SELECT fc.*,
               fcm.role, fcm.is_pinned, fcm.unread_count, fcm.is_muted,
               (SELECT display_name FROM flow_user_profiles WHERE user_id =
                   (SELECT user_id FROM flow_conversation_members WHERE conversation_id = fc.id AND user_id != ? LIMIT 1)
               ) as other_user_name,
               (SELECT avatar_url FROM flow_user_profiles WHERE user_id =
                   (SELECT user_id FROM flow_conversation_members WHERE conversation_id = fc.id AND user_id != ? LIMIT 1)
               ) as other_user_avatar,
               (SELECT COUNT(*) FROM flow_message_mentions fmm
                JOIN flow_messages fm ON fmm.message_id = fm.id
                WHERE fm.conversation_id = fc.id AND fmm.user_id = ? AND fm.is_deleted = 0) as mention_count
        FROM flow_conversations fc
        JOIN flow_conversation_members fcm ON fc.id = fcm.conversation_id
        WHERE fcm.user_id = ? {} AND fcm.is_archived = 0
        ORDER BY
            CASE WHEN fcm.is_pinned = 1 THEN 0 ELSE 1 END,
            fc.last_message_at DESC
    '''.format(archived_cond), (user_id, user_id, user_id, user_id))


def get_conversation_messages(conversation_id, user_id, limit=50, before=None):
    """Get messages for a conversation."""
    before_cond = f"AND m.created_at < '{before}'" if before else ""
    
    # Mark as read
    with get_db_context() as db:
        db.execute('''
            UPDATE flow_conversation_members
            SET unread_count = 0, last_read_at = ?
            WHERE conversation_id = ? AND user_id = ?
        ''', (datetime.now().isoformat(), conversation_id, user_id))
    
    return get_all(f'''
        SELECT m.*, 
               fup.display_name as sender_name,
               fup.avatar_url as sender_avatar,
               fup.username as sender_username,
               (SELECT COUNT(*) FROM flow_message_reactions WHERE message_id = m.id) as reaction_count,
               (SELECT GROUP_CONCAT(emoji || ':' || user_id) FROM flow_message_reactions WHERE message_id = m.id) as reactions
        FROM flow_messages m
        LEFT JOIN flow_user_profiles fup ON m.sender_id = fup.user_id
        WHERE m.conversation_id = ? AND m.is_deleted = 0 {before_cond}
        ORDER BY m.created_at DESC
        LIMIT ?
    ''', (conversation_id, limit))


def search_messages(user_id, query, search_type='all', limit=50):
    """Search messages across all accessible conversations."""
    base_query = '''
        SELECT m.*, fc.name as conversation_name, fc.conversation_type,
               fup.display_name as sender_name
        FROM flow_messages m
        JOIN flow_conversations fc ON m.conversation_id = fc.id
        JOIN flow_conversation_members fcm ON fc.id = fcm.conversation_id
        LEFT JOIN flow_user_profiles fup ON m.sender_id = fup.user_id
        WHERE fcm.user_id = ?
        AND m.is_deleted = 0
        AND m.content LIKE ?
    '''
    
    params = [user_id, f'%{query}%']
    
    if search_type == 'files':
        base_query += " AND m.message_type = 'file'"
    elif search_type == 'images':
        base_query += " AND m.message_type IN ('image', 'video')"
    elif search_type == 'links':
        base_query += " AND m.content LIKE '%http%'"
    
    base_query += ' ORDER BY m.created_at DESC LIMIT ?'
    params.append(limit)
    
    return get_all(base_query, params)


def get_unread_notification_count(user_id):
    """Get count of unread notifications."""
    result = get_one('''
        SELECT COUNT(*) as count FROM flow_notifications
        WHERE user_id = ? AND is_read = 0
    ''', (user_id,))
    return result['count'] if result else 0


def get_user_status(user_id):
    """Get current user status."""
    status = get_one('''
        SELECT * FROM flow_user_status
        WHERE user_id = ? AND (status_expires_at IS NULL OR status_expires_at > ?)
        ORDER BY created_at DESC LIMIT 1
    ''', (user_id, datetime.now().isoformat()))
    
    if not status:
        # Check last seen
        profile = get_one('SELECT last_seen_at FROM flow_user_profiles WHERE user_id = ?', (user_id,))
        if profile and profile['last_seen_at']:
            return {'status_type': 'offline', 'status_text': None}
        return {'status_type': 'offline', 'status_text': None}
    
    return status


def set_user_status(user_id, status_type, status_text=None, expires_in_hours=None):
    """Set user status."""
    expires_at = None
    if expires_in_hours:
        expires_at = (datetime.now() + timedelta(hours=expires_in_hours)).isoformat()
    
    with get_db_context() as db:
        # Clear existing status
        db.execute('DELETE FROM flow_user_status WHERE user_id = ?', (user_id,))
        
        db.execute('''
            INSERT INTO flow_user_status (user_id, status_type, status_text, status_expires_at, is_custom)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, status_type, status_text, expires_at, 1 if status_text else 0))
    
    log_audit(user_id, 'status_change', {'status_type': status_type, 'status_text': status_text}, 'flow')


def update_presence(user_id, status_type='online'):
    """Update user presence."""
    with get_db_context() as db:
        db.execute('''
            UPDATE flow_user_profiles
            SET last_seen_at = ?
            WHERE user_id = ?
        ''', (datetime.now().isoformat(), user_id))
    
    # Also update/set status
    current = get_user_status(user_id)
    if not current or current.get('is_custom') != 1:
        set_user_status(user_id, status_type)


def create_channel(name, description, created_by, channel_type='public', category=None, channel_id=None, invite_code=None):
    """Create a new channel.

    Args:
        name: Channel display name
        description: Channel description
        created_by: User ID of creator
        channel_type: 'public' or 'private'
        category: Channel category
        channel_id: Custom URL-friendly ID for public channels (e.g., 'general', 'engineering.team')
        invite_code: Optional invite code for private channels
    """
    db_channel_id = generate_id()
    conv_id = generate_id()
    now = datetime.now().isoformat()

    # For public channels, use the provided channel_id or generate from name
    final_channel_id = None
    if channel_type == 'public':
        if channel_id:
            # Clean and validate the provided channel_id
            final_channel_id = channel_id.lower().strip()
        else:
            # Generate from name
            final_channel_id = name.lower().replace(' ', '-').replace('_', '-')

    # For private channels, generate invite code if not provided
    final_invite_code = invite_code
    if channel_type == 'private' and not final_invite_code:
        final_invite_code = generate_invite_code()

    with get_db_context() as db:
        # Create channel
        db.execute('''
            INSERT INTO flow_channels (id, name, channel_id, description, channel_type, category, invite_code, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (db_channel_id, name, final_channel_id, description, channel_type, category, final_invite_code, created_by))

        # Create corresponding conversation
        db.execute('''
            INSERT INTO flow_conversations (id, conversation_type, name, created_by, last_message_at)
            VALUES (?, 'channel', ?, ?, ?)
        ''', (conv_id, name, created_by, now))

        # Add creator as admin
        db.execute('''
            INSERT INTO flow_channel_members (channel_id, user_id, role)
            VALUES (?, ?, 'admin')
        ''', (db_channel_id, created_by))

        db.execute('''
            INSERT INTO flow_conversation_members (conversation_id, user_id, role)
            VALUES (?, ?, 'admin')
        ''', (conv_id, created_by))

    log_audit(created_by, 'channel_create', {'channel_id': db_channel_id, 'name': name, 'channel_id_value': final_channel_id}, 'flow')
    return db_channel_id


def create_group(name, description, created_by, group_type='private', member_ids=None):
    """Create a new group."""
    group_id = generate_id()
    conv_id = generate_id()
    now = datetime.now().isoformat()
    
    with get_db_context() as db:
        db.execute('''
            INSERT INTO flow_groups (id, name, description, group_type, created_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (group_id, name, description, group_type, created_by))
        
        db.execute('''
            INSERT INTO flow_conversations (id, conversation_type, name, created_by, last_message_at)
            VALUES (?, 'group', ?, ?, ?)
        ''', (conv_id, name, created_by, now))
        
        # Add creator as owner
        db.execute('''
            INSERT INTO flow_group_members (group_id, user_id, role)
            VALUES (?, ?, 'owner')
        ''', (group_id, created_by))
        
        db.execute('''
            INSERT INTO flow_conversation_members (conversation_id, user_id, role)
            VALUES (?, ?, 'owner')
        ''', (conv_id, created_by))
        
        # Add other members
        if member_ids:
            for mid in member_ids:
                if mid != created_by:
                    db.execute('''
                        INSERT INTO flow_group_members (group_id, user_id, role)
                        VALUES (?, ?, 'member')
                    ''', (group_id, mid))
                    
                    db.execute('''
                        INSERT INTO flow_conversation_members (conversation_id, user_id, role)
                        VALUES (?, ?, 'member')
                    ''', (conv_id, mid))
    
    log_audit(created_by, 'group_create', {'group_id': group_id, 'name': name, 'members': len(member_ids) if member_ids else 0}, 'flow')
    return group_id


def start_call(call_type, initiated_by, participant_ids):
    """Start a call session."""
    call_id = generate_id()
    now = datetime.now().isoformat()
    
    with get_db_context() as db:
        db.execute('''
            INSERT INTO flow_call_sessions (id, call_type, initiated_by, status, started_at)
            VALUES (?, ?, ?, 'active', ?)
        ''', (call_id, call_type, initiated_by, now))
        
        # Add initiator
        db.execute('''
            INSERT INTO flow_call_participants (call_id, user_id, call_status, joined_at)
            VALUES (?, ?, 'joined', ?)
        ''', (call_id, initiated_by, now))
        
        # Add other participants
        for pid in participant_ids:
            if pid != initiated_by:
                db.execute('''
                    INSERT INTO flow_call_participants (call_id, user_id, call_status)
                    VALUES (?, ?, 'pending')
                ''', (call_id, pid))
                
                # Send notification
                caller = get_one('SELECT display_name FROM flow_user_profiles WHERE user_id = ?', (initiated_by,))
                create_notification(
                    pid,
                    'call_incoming',
                    f'Incoming {call_type}',
                    f'{caller["display_name"]} is calling you',
                    f'/flow/call/{call_id}'
                )
    
    return call_id


def start_meeting(title, description, host_id, start_time=None, meeting_type='instant'):
    """Start or schedule a meeting."""
    meeting_id = generate_id()
    now = datetime.now().isoformat()
    
    with get_db_context() as db:
        db.execute('''
            INSERT INTO flow_meeting_sessions (id, title, description, meeting_type, host_id, start_time, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            meeting_id, title, description, meeting_type, host_id,
            start_time or now,
            'active' if meeting_type == 'instant' else 'scheduled'
        ))
        
        db.execute('''
            INSERT INTO flow_meeting_participants (meeting_id, user_id, role, joined_at)
            VALUES (?, ?, 'host', ?)
        ''', (meeting_id, host_id, now))
    
    log_audit(host_id, 'meeting_start', {'meeting_id': meeting_id, 'title': title}, 'flow')
    return meeting_id


def get_shared_media(conversation_id=None, channel_id=None, limit=100):
    """Get shared media for a conversation or channel."""
    if conversation_id:
        return get_all('''
            SELECT m.*, fma.file_name, fma.file_path, fma.file_type, fma.file_size,
                   fma.thumbnail_path, fma.duration_seconds, fma.width, fma.height,
                   fup.display_name as uploader_name
            FROM flow_messages m
            JOIN flow_message_attachments fma ON m.id = fma.message_id
            LEFT JOIN flow_user_profiles fup ON m.sender_id = fup.user_id
            WHERE m.conversation_id = ? AND m.is_deleted = 0
            AND fma.file_type IN ('image', 'video', 'audio', 'document')
            ORDER BY m.created_at DESC
            LIMIT ?
        ''', (conversation_id, limit))
    
    if channel_id:
        return get_all('''
            SELECT sm.*, fup.display_name as uploader_name
            FROM flow_shared_media sm
            LEFT JOIN flow_user_profiles fup ON sm.uploaded_by = fup.user_id
            WHERE sm.channel_id = ?
            ORDER BY sm.created_at DESC
            LIMIT ?
        ''', (channel_id, limit))
    
    return []


def get_user_settings(user_id):
    """Get user settings with defaults."""
    settings = get_one('''
        SELECT * FROM flow_user_settings WHERE user_id = ?
    ''', (user_id,))
    
    if not settings:
        defaults = {
            'user_id': user_id,
            'language': 'en',
            'theme': 'light',
            'notification_sound': 1,
            'notification_desktop': 1,
            'notification_mobile': 1,
            'message_preview': 1,
            'show_online_status': 1,
            'show_read_receipts': 1,
            'show_last_seen': 1,
            'auto_download_wifi': 1,
            'auto_download_cellular': 0,
            'compact_mode': 0,
            'emoji_style': 'native',
            'gif_provider': 'giphy',
            'chat_background': 'default',
            'chat_background_custom': None
        }
        with get_db_context() as db:
            db.execute('''
                INSERT INTO flow_user_settings (user_id, language, theme, notification_sound,
                    notification_desktop, notification_mobile, message_preview, show_online_status,
                    show_read_receipts, show_last_seen, auto_download_wifi, auto_download_cellular,
                    compact_mode, emoji_style, gif_provider, chat_background, chat_background_custom)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, defaults['language'], defaults['theme'], defaults['notification_sound'],
                defaults['notification_desktop'], defaults['notification_mobile'], defaults['message_preview'],
                defaults['show_online_status'], defaults['show_read_receipts'], defaults['show_last_seen'],
                defaults['auto_download_wifi'], defaults['auto_download_cellular'], defaults['compact_mode'],
                defaults['emoji_style'], defaults['gif_provider'], defaults['chat_background'], defaults['chat_background_custom']
            ))
        settings = get_one('SELECT * FROM flow_user_settings WHERE user_id = ?', (user_id,))
    
    return settings


def update_channel(channel_id, data):
    """Update a channel's settings. Returns True on success."""
    valid_fields = ['name', 'description', 'avatar_url', 'category']
    updates = []
    values = []
    for key, value in data.items():
        if key in valid_fields:
            updates.append(f'{key} = ?')
            values.append(value)

    if not updates:
        return False

    now = datetime.now().isoformat()
    values.extend([now, channel_id])
    with get_db_context() as db:
        db.execute(f'''
            UPDATE flow_channels
            SET {', '.join(updates)}, updated_at = ?
            WHERE id = ?
        ''', values)

    if 'name' in data or 'avatar_url' in data:
        conv = get_one('SELECT id FROM flow_conversations WHERE name = (SELECT name FROM flow_channels WHERE id = ?) AND conversation_type = ?', (channel_id, 'channel'))
        if conv:
            if 'avatar_url' in data:
                db.execute('UPDATE flow_conversations SET avatar_url = ? WHERE id = ?', (data['avatar_url'], conv['id']))
            if 'name' in data:
                db.execute('UPDATE flow_conversations SET name = ? WHERE id = ?', (data['name'], conv['id']))

    return True


def update_group(group_id, data):
    """Update a group's settings. Returns True on success."""
    valid_fields = ['name', 'description', 'avatar_url']
    updates = []
    values = []
    for key, value in data.items():
        if key in valid_fields:
            updates.append(f'{key} = ?')
            values.append(value)

    if not updates:
        return False

    now = datetime.now().isoformat()
    values.extend([now, group_id])
    with get_db_context() as db:
        db.execute(f'''
            UPDATE flow_groups
            SET {', '.join(updates)}, updated_at = ?
            WHERE id = ?
        ''', values)

    if 'name' in data or 'avatar_url' in data:
        conv = get_one('SELECT id FROM flow_conversations WHERE name = (SELECT name FROM flow_groups WHERE id = ?) AND conversation_type = ?', (group_id, 'group'))
        if conv:
            if 'avatar_url' in data:
                db.execute('UPDATE flow_conversations SET avatar_url = ? WHERE id = ?', (data['avatar_url'], conv['id']))
            if 'name' in data:
                db.execute('UPDATE flow_conversations SET name = ? WHERE id = ?', (data['name'], conv['id']))

    return True


def update_user_settings(user_id, settings_dict):
    """Update user settings."""
    valid_fields = [
        'language', 'theme', 'notification_sound', 'notification_desktop',
        'notification_mobile', 'message_preview', 'show_online_status',
        'show_read_receipts', 'show_last_seen', 'auto_download_wifi',
        'auto_download_cellular', 'compact_mode', 'emoji_style', 'gif_provider', 'giphy_api_key',
        'chat_background', 'chat_background_custom'
    ]

    updates = []
    values = []
    for key, value in settings_dict.items():
        if key in valid_fields:
            updates.append(f'{key} = ?')
            values.append(value)

    if updates:
        values.append(user_id)
        with get_db_context() as db:
            db.execute(f'''
                UPDATE flow_user_settings
                SET {', '.join(updates)}, updated_at = ?
                WHERE user_id = ?
            ''', values)


def update_flow_profile(user_id, profile_data):
    """Update user profile data."""
    valid_fields = ['display_name', 'username', 'bio', 'department', 'job_title', 'phone', 'avatar_url']

    updates = []
    values = []
    for key, value in profile_data.items():
        if key in valid_fields:
            updates.append(f'{key} = ?')
            values.append(value)

    if updates:
        updates.append('updated_at = ?')
        values.append(datetime.now().isoformat())
        values.append(user_id)
        with get_db_context() as db:
            db.execute(f'''
                UPDATE flow_user_profiles
                SET {', '.join(updates)}
                WHERE user_id = ?
            ''', values)


def block_user(user_id, blocked_user_id):
    """Block a user."""
    with get_db_context() as db:
        db.execute('''
            INSERT OR IGNORE INTO flow_blocked_users (user_id, blocked_user_id)
            VALUES (?, ?)
        ''', (user_id, blocked_user_id))


def unblock_user(user_id, blocked_user_id):
    """Unblock a user."""
    with get_db_context() as db:
        db.execute('''
            DELETE FROM flow_blocked_users WHERE user_id = ? AND blocked_user_id = ?
        ''', (user_id, blocked_user_id))


def is_user_blocked(user_id, other_user_id):
    """Check if a user is blocked."""
    result = get_one('''
        SELECT 1 FROM flow_blocked_users
        WHERE user_id = ? AND blocked_user_id = ?
    ''', (user_id, other_user_id))
    return result is not None


# ============================================================================
# PUSH NOTIFICATIONS
# ============================================================================

def save_push_subscription(user_id, endpoint, p256dh, auth, device_info=None, browser=None):
    """Save a push notification subscription."""
    with get_db_context() as db:
        db.execute('''
            INSERT OR REPLACE INTO flow_push_subscriptions
            (user_id, endpoint, p256dh, auth, device_info, browser, is_active, updated_at, last_used_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
        ''', (user_id, endpoint, p256dh, auth, json.dumps(device_info) if device_info else None, browser, datetime.now().isoformat(), datetime.now().isoformat()))
    
    log_audit(user_id, 'push_subscribe', {'browser': browser}, 'flow')


def remove_push_subscription(user_id, endpoint=None):
    """Remove a push notification subscription."""
    if endpoint:
        with get_db_context() as db:
            db.execute('''
                UPDATE flow_push_subscriptions SET is_active = 0, updated_at = ?
                WHERE user_id = ? AND endpoint = ?
            ''', (datetime.now().isoformat(), user_id, endpoint))
    else:
        # Remove all subscriptions for user
        with get_db_context() as db:
            db.execute('''
                UPDATE flow_push_subscriptions SET is_active = 0, updated_at = ?
                WHERE user_id = ?
            ''', (datetime.now().isoformat(), user_id))
    
    log_audit(user_id, 'push_unsubscribe', {'endpoint': endpoint}, 'flow')


def get_active_push_subscription(user_id):
    """Get the active push subscription for a user."""
    return get_one('''
        SELECT * FROM flow_push_subscriptions
        WHERE user_id = ? AND is_active = 1
        ORDER BY last_used_at DESC LIMIT 1
    ''', (user_id,))


def get_all_active_push_subscriptions(user_id):
    """Get all active push subscriptions for a user (for multi-device)."""
    return get_all('''
        SELECT * FROM flow_push_subscriptions
        WHERE user_id = ? AND is_active = 1
        ORDER BY last_used_at DESC
    ''', (user_id,))


def update_push_subscription_usage(endpoint):
    """Update last_used_at for a subscription."""
    with get_db_context() as db:
        db.execute('''
            UPDATE flow_push_subscriptions SET last_used_at = ?
            WHERE endpoint = ?
        ''', (datetime.now().isoformat(), endpoint))


def log_push_notification(user_id, notification_type, title, body, status='sent', error_message=None):
    """Log a push notification for audit."""
    with get_db_context() as db:
        db.execute('''
            INSERT INTO flow_push_logs
            (user_id, notification_type, title, body, status, error_message, sent_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, notification_type, title, body, status, error_message, datetime.now().isoformat()))


def get_push_notification_logs(user_id, limit=100):
    """Get push notification logs for a user."""
    return get_all('''
        SELECT * FROM flow_push_logs
        WHERE user_id = ?
        ORDER BY sent_at DESC
        LIMIT ?
    ''', (user_id, limit))


def has_push_subscription(user_id):
    """Check if user has any active push subscription."""
    result = get_one('''
        SELECT 1 FROM flow_push_subscriptions
        WHERE user_id = ? AND is_active = 1 LIMIT 1
    ''', (user_id,))
    return result is not None


def send_push_notification(user_id, notification_type, title, body, data=None):
    """
    Send a push notification to a user using webpush.
    Returns True if sent successfully, False otherwise.
    """
    subscriptions = get_all_active_push_subscriptions(user_id)
    if not subscriptions:
        return False
    
    try:
        from webpush import WebPush, WebPushException
        
        # Get VAPID keys from config
        try:
            from config import VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_SUBJECT
        except ImportError:
            # Fallback if config not available
            VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', 'MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEY-hwQ6_Hdk7VJ4fTNt1P1S0qX63wxwwtrfbnfPDPGwpckcjeTF337se9o6Ncgn5lp6rHPSzoJq_rwDUAqlI_oQ')
            VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', 'MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgIrq9m4IxBGkkkOX315urB7sbbkE7_GIvRGD0csfA6hehRANCAARj6HBDr8d2TtUnh9M23U_VLSpfrfDHDC2t9ud88M8bClyRyN5MXffux72jo1yCfmWnqsc9LOgmr-vANQCqUj-h')
            VAPID_SUBJECT = os.environ.get('VAPID_SUBJECT', 'mailto:notifications@example.com')
        
        # Build notification payload
        payload = {
            'title': title,
            'body': body,
            'notification_type': notification_type,
            'url': data.get('url', '/flow/') if data else '/flow/',
            'conversation_id': data.get('conversation_id') if data else None,
            'message_id': data.get('message_id') if data else None,
            'notification_id': data.get('notification_id') if data else None,
            'tag': f'flow-{notification_type}',
            'icon': '/static/flow-icon.png',
            'requireInteraction': notification_type in ['flow_call', 'flow_meeting']
        }
        
        success_count = 0
        
        for sub in subscriptions:
            try:
                # Build subscription object
                push_subscription = {
                    'endpoint': sub['endpoint'],
                    'keys': {
                        'p256dh': sub['p256dh'],
                        'auth': sub['auth']
                    }
                }
                
                # Create WebPush instance
                push = WebPush(
                    subscription=push_subscription,
                    data=json.dumps(payload),
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims={
                        'sub': VAPID_SUBJECT,
                        'aud': '/'.join(push_subscription['endpoint'].split('/')[:3])
                    }
                )
                
                # Send the push notification
                push.send()
                
                log_push_notification(user_id, notification_type, title, body, 'sent')
                success_count += 1
                
            except WebPushException as e:
                log_push_notification(user_id, notification_type, title, body, 'failed', str(e))
                
                # If subscription is expired or invalid, deactivate it
                if e.response and e.response.status_code in [404, 410]:
                    with get_db_context() as db:
                        db.execute('''
                            UPDATE flow_push_subscriptions 
                            SET is_active = 0, updated_at = ?
                            WHERE endpoint = ?
                        ''', (datetime.now().isoformat(), sub['endpoint']))
                continue
                
            except Exception as e:
                log_push_notification(user_id, notification_type, title, body, 'failed', str(e))
                continue
        
        return success_count > 0
        
    except ImportError:
        # webpush not installed, log and return
        log_push_notification(user_id, notification_type, title, body, 'failed', 'webpush not installed')
        return False
    except Exception as e:
        log_push_notification(user_id, notification_type, title, body, 'failed', str(e))
        return False


def get_vapid_public_key():
    """Get the VAPID public key for frontend subscription."""
    try:
        from config import VAPID_PUBLIC_KEY
        return VAPID_PUBLIC_KEY
    except ImportError:
        return os.environ.get('VAPID_PUBLIC_KEY', 'MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEY-hwQ6_Hdk7VJ4fTNt1P1S0qX63wxwwtrfbnfPDPGwpckcjeTF337se9o6Ncgn5lp6rHPSzoJq_rwDUAqlI_oQ')


def schedule_push_reminder(user_id, reminder_id, title, body, remind_at, data=None):
    """
    Schedule a push notification for a future time.
    This would typically use a task queue like Celery or Redis.
    For now, we store the scheduled notification.
    """
    with get_db_context() as db:
        # Store scheduled notification
        db.execute('''
            INSERT INTO flow_push_scheduled (user_id, reminder_id, title, body, data, scheduled_for, is_sent)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        ''', (user_id, reminder_id, title, body, json.dumps(data) if data else None, remind_at))
    
    return True


def get_due_scheduled_notifications():
    """Get all scheduled notifications that are due."""
    now = datetime.now().isoformat()
    return get_all('''
        SELECT * FROM flow_push_scheduled
        WHERE is_sent = 0 AND scheduled_for <= ?
    ''', (now,))


def mark_scheduled_notification_sent(scheduled_id):
    """Mark a scheduled notification as sent."""
    with get_db_context() as db:
        db.execute('''
            UPDATE flow_push_scheduled SET is_sent = 1, sent_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), scheduled_id))


# ============================================================================
# PERMISSIONS
# ============================================================================

FLOW_PERMISSIONS = {
    'flow': {
        'resources': {
            'channels': ['view', 'create', 'join', 'leave', 'manage', 'admin'],
            'groups': ['view', 'create', 'join', 'leave', 'manage', 'admin'],
            'messages': ['view', 'send', 'edit', 'delete', 'pin'],
            'files': ['upload', 'download', 'delete'],
            'calls': ['initiate', 'join', 'manage'],
            'meetings': ['create', 'join', 'host', 'manage'],
            'notifications': ['view', 'manage'],
            'settings': ['view', 'edit'],
            'users': ['view', 'block']
        }
    }
}


# ============================================================================
# SEED DATA
# ============================================================================

def seed_flow_data():
    """Seed FLOW with demo data."""
    import random
    from datetime import timedelta
    
    import sys
    print("[FLOW] Seeding demo data...", file=sys.stderr)
    
    # Get existing users
    users = get_all('SELECT id, username FROM users LIMIT 20')
    if not users:
        print("[FLOW] No users found. Please create users first.", file=sys.stderr)
        return
    
    user_ids = [u['id'] for u in users]
    
    with get_db_context() as db:
        # Ensure profiles exist for all users
        for user in users:
            profile = get_one('SELECT 1 FROM flow_user_profiles WHERE user_id = ?', (user['id'],))
            if not profile:
                db.execute('''
                    INSERT INTO flow_user_profiles (user_id, username, display_name, department, job_title)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    user['id'],
                    user['username'],
                    user['username'].title(),
                    random.choice(['Engineering', 'Sales', 'Marketing', 'HR', 'Operations', 'Warehouse']),
                    random.choice(['Manager', 'Specialist', 'Coordinator', 'Director', 'Associate'])
                ))
        
        # Ensure user settings exist
        for user in users:
            settings = get_one('SELECT 1 FROM flow_user_settings WHERE user_id = ?', (user['id'],))
            if not settings:
                db.execute('''
                    INSERT INTO flow_user_settings (user_id) VALUES (?)
                ''', (user['id'],))
        
        # Set random statuses for users
        statuses = ['online', 'away', 'busy', 'in_meeting', 'offline']
        for user in users:
            if random.random() > 0.3:  # 70% have a status
                status = random.choice(statuses)
                status_text = None
                if status == 'busy':
                    status_text = random.choice(['In a call', 'Focus mode', 'Do not disturb'])
                elif status == 'away':
                    status_text = random.choice(['Away from desk', 'Back soon', 'BRB'])
                
                db.execute('''
                    INSERT INTO flow_user_status (user_id, status_type, status_text, is_custom)
                    VALUES (?, ?, ?, ?)
                ''', (user['id'], status, status_text, 1 if status_text else 0))
        
        # Create channels
        channel_data = [
            {'name': 'general', 'description': 'General discussions and announcements', 'category': 'Company'},
            {'name': 'announcements', 'description': 'Official company announcements', 'category': 'Company'},
            {'name': 'engineering', 'description': 'Engineering team discussions', 'category': 'Departments'},
            {'name': 'sales', 'description': 'Sales team updates and leads', 'category': 'Departments'},
            {'name': 'marketing', 'description': 'Marketing campaigns and social media', 'category': 'Departments'},
            {'name': 'hr', 'description': 'HR policies and employee resources', 'category': 'Departments'},
            {'name': 'warehouse', 'description': 'Warehouse operations and logistics', 'category': 'Operations'},
            {'name': 'logistics', 'description': 'Shipping and delivery updates', 'category': 'Operations'},
            {'name': 'random', 'description': 'Random conversations and water cooler chat', 'category': 'Social'},
            {'name': 'introductions', 'description': 'Introduce yourself to the team', 'category': 'Social'},
        ]
        
        channel_ids = []
        for ch in channel_data:
            channel_id = generate_id()
            conv_id = generate_id()
            now = datetime.now().isoformat()
            
            db.execute('''
                INSERT INTO flow_channels (id, name, description, channel_type, category, created_by)
                VALUES (?, ?, ?, 'public', ?, ?)
            ''', (channel_id, ch['name'], ch['description'], ch['category'], user_ids[0]))
            
            db.execute('''
                INSERT INTO flow_conversations (id, conversation_type, name, created_by, last_message_at)
                VALUES (?, 'channel', ?, ?, ?)
            ''', (conv_id, ch['name'], user_ids[0], now))
            
            # Add all users to channels
            for uid in user_ids[:random.randint(5, len(user_ids))]:
                db.execute('''
                    INSERT INTO flow_channel_members (channel_id, user_id, role)
                    VALUES (?, ?, 'member')
                ''', (channel_id, uid))
                
                db.execute('''
                    INSERT INTO flow_conversation_members (conversation_id, user_id, role)
                    VALUES (?, ?, 'member')
                ''', (conv_id, uid))
            
            channel_ids.append(channel_id)
        
        # Create groups
        group_data = [
            {'name': 'Project Alpha Team', 'description': 'Core team for Project Alpha', 'type': 'private'},
            {'name': 'Q4 Marketing Campaign', 'description': 'Marketing push for Q4', 'type': 'private'},
            {'name': 'New Employee Onboarding', 'description': 'Onboarding committee', 'type': 'private'},
            {'name': 'Friday Social Club', 'description': 'Friday activities and events', 'type': 'public'},
            {'name': 'Book Club', 'description': 'Monthly book discussions', 'type': 'public'},
        ]
        
        group_ids = []
        for grp in group_data:
            group_id = generate_id()
            conv_id = generate_id()
            now = datetime.now().isoformat()
            
            db.execute('''
                INSERT INTO flow_groups (id, name, description, group_type, created_by)
                VALUES (?, ?, ?, ?, ?)
            ''', (group_id, grp['name'], grp['description'], grp['type'], user_ids[0]))
            
            db.execute('''
                INSERT INTO flow_conversations (id, conversation_type, name, created_by, last_message_at)
                VALUES (?, 'group', ?, ?, ?)
            ''', (conv_id, grp['name'], user_ids[0], now))
            
            # Add random members
            members = random.sample(user_ids, random.randint(3, min(8, len(user_ids))))
            for uid in members:
                role = 'owner' if uid == user_ids[0] else 'admin' if members.index(uid) < 2 else 'member'
                db.execute('''
                    INSERT INTO flow_group_members (group_id, user_id, role)
                    VALUES (?, ?, ?)
                ''', (group_id, uid, role))
                
                db.execute('''
                    INSERT INTO flow_conversation_members (conversation_id, user_id, role)
                    VALUES (?, ?, ?)
                ''', (conv_id, uid, role))
            
            group_ids.append(group_id)
        
        # Create private conversations between random user pairs
        private_conv_ids = []
        for i in range(min(10, len(user_ids) // 2)):
            u1, u2 = random.sample(user_ids, 2)
            
            # Check if private chat already exists
            existing = get_one('''
                SELECT fc.id FROM flow_conversations fc
                JOIN flow_conversation_members fcm1 ON fc.id = fcm1.conversation_id AND fcm1.user_id = ?
                JOIN flow_conversation_members fcm2 ON fc.id = fcm2.conversation_id AND fcm2.user_id = ?
                WHERE fc.conversation_type = 'private'
            ''', (u1, u2))
            
            if not existing:
                conv_id = generate_id()
                now = datetime.now().isoformat()
                
                db.execute('''
                    INSERT INTO flow_conversations (id, conversation_type, created_by, last_message_at)
                    VALUES (?, 'private', ?, ?)
                ''', (conv_id, u1, now))
                
                db.execute('''
                    INSERT INTO flow_conversation_members (conversation_id, user_id, role)
                    VALUES (?, ?, 'member'), (?, ?, 'member')
                ''', (conv_id, u1, conv_id, u2))
                
                private_conv_ids.append(conv_id)
            else:
                private_conv_ids.append(existing['id'])
        
        # Create "Save Messages" for each user
        for user in users:
            existing = get_one('''
                SELECT fc.id FROM flow_conversations fc
                JOIN flow_conversation_members fcm ON fc.id = fcm.conversation_id
                WHERE fc.conversation_type = 'private' AND fcm.user_id = ? AND fcm.role = 'owner'
                AND (SELECT COUNT(*) FROM flow_conversation_members WHERE conversation_id = fc.id) = 1
            ''', (user['id'],))
            
            if not existing:
                conv_id = generate_id()
                now = datetime.now().isoformat()
                
                db.execute('''
                    INSERT INTO flow_conversations (id, conversation_type, name, created_by, last_message_at)
                    VALUES (?, 'private', 'Save Messages', ?, ?)
                ''', (conv_id, user['id'], now))
                
                db.execute('''
                    INSERT INTO flow_conversation_members (conversation_id, user_id, role)
                    VALUES (?, ?, 'owner')
                ''', (conv_id, user['id']))
        
        # Create sample messages in channels
        sample_messages = [
            "Good morning everyone! 👋",
            "Has anyone seen the latest quarterly report?",
            "The new server deployment is scheduled for tonight.",
            "Great job team on closing that deal! 🎉",
            "Reminder: All hands meeting at 3 PM today.",
            "Can someone review my pull request?",
            "The warehouse inventory has been updated.",
            "Welcome to the team, @{}!".format(random.choice(users)['username'] if users else 'newbie'),
            "Lunch is on me today! 🍕",
            "Please remember to update your status.",
            "The new marketing materials are ready for review.",
            "Has anyone tested the new workflow automation?",
            "Excellent work on the presentation!",
            "The client meeting went really well.",
            "Don't forget to submit your timesheets.",
        ]
        
        all_conv_ids = private_conv_ids.copy()
        
        # Add messages to channels
        for ch_idx, channel_id in enumerate(channel_ids[:5]):
            conv = get_one('''
                SELECT id FROM flow_conversations 
                WHERE name = (SELECT name FROM flow_channels WHERE id = ?)
                AND conversation_type = 'channel'
            ''', (channel_id,))
            
            if conv:
                all_conv_ids.append(conv['id'])
                
                for j in range(random.randint(5, 15)):
                    msg_id = generate_id()
                    sender = random.choice(user_ids[:5])
                    content = random.choice(sample_messages)
                    minutes_ago = random.randint(1, 1440)
                    msg_time = (datetime.now() - timedelta(minutes=minutes_ago)).isoformat()
                    
                    db.execute('''
                        INSERT INTO flow_messages (id, conversation_id, sender_id, message_type, content, created_at)
                        VALUES (?, ?, ?, 'text', ?, ?)
                    ''', (msg_id, conv['id'], sender, content, msg_time))
                    
                    # Update conversation
                    db.execute('''
                        UPDATE flow_conversations 
                        SET last_message_at = ?, last_message_preview = ?
                        WHERE id = ?
                    ''', (msg_time, content[:50], conv['id']))
        
        # Add messages to groups
        for grp_idx, group_id in enumerate(group_ids[:3]):
            conv = get_one('''
                SELECT id FROM flow_conversations WHERE name = (SELECT name FROM flow_groups WHERE id = ?)
                AND conversation_type = 'group'
            ''', (group_id,))
            
            if conv:
                all_conv_ids.append(conv['id'])
                
                for j in range(random.randint(3, 10)):
                    msg_id = generate_id()
                    sender = random.choice(user_ids[:5])
                    content = random.choice(sample_messages)
                    minutes_ago = random.randint(1, 2880)
                    msg_time = (datetime.now() - timedelta(minutes=minutes_ago)).isoformat()
                    
                    db.execute('''
                        INSERT INTO flow_messages (id, conversation_id, sender_id, message_type, content, created_at)
                        VALUES (?, ?, ?, 'text', ?, ?)
                    ''', (msg_id, conv['id'], sender, content, msg_time))
        
        # Add messages to private chats
        for conv_id in private_conv_ids[:5]:
            for j in range(random.randint(3, 8)):
                msg_id = generate_id()
                sender = random.choice(user_ids[:2])
                content = random.choice([
                    "Hey, how are you?",
                    "Did you see the email about the meeting?",
                    "I'll send you the files shortly.",
                    "Thanks for your help!",
                    "Can we schedule a call?",
                    "The report looks great!",
                    "I'll review it tomorrow.",
                    "Let me know when you're free.",
                ])
                minutes_ago = random.randint(1, 720)
                msg_time = (datetime.now() - timedelta(minutes=minutes_ago)).isoformat()
                
                db.execute('''
                    INSERT INTO flow_messages (id, conversation_id, sender_id, message_type, content, created_at)
                    VALUES (?, ?, ?, 'text', ?, ?)
                ''', (msg_id, conv_id, sender, content, msg_time))
                
                db.execute('''
                    UPDATE flow_conversations 
                    SET last_message_at = ?, last_message_preview = ?
                    WHERE id = ?
                ''', (msg_time, content[:50], conv_id))
        
        # Create some sample notifications
        for user in users[:5]:
            for i in range(random.randint(1, 5)):
                notif_types = ['message', 'mention', 'reaction', 'call_missed', 'reminder']
                notif_type = random.choice(notif_types)
                
                titles = {
                    'message': 'New message',
                    'mention': 'You were mentioned',
                    'reaction': 'Someone reacted to your message',
                    'call_missed': 'Missed call',
                    'reminder': 'Reminder'
                }
                
                db.execute('''
                    INSERT INTO flow_notifications (user_id, notification_type, title, body, is_read, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user['id'],
                    notif_type,
                    titles[notif_type],
                    f'Sample notification body for {notif_type}',
                    1 if random.random() > 0.5 else 0,
                    (datetime.now() - timedelta(minutes=random.randint(1, 1440))).isoformat()
                ))
        
        # Create sample call history
        call_types = ['audio', 'video']
        call_statuses = ['completed', 'completed', 'completed', 'missed', 'declined']
        call_durations = [120, 300, 480, 600, 900, 1800]  # 2min to 30min in seconds
        
        for _ in range(random.randint(5, 15)):
            caller_idx = random.randint(0, min(len(user_ids) - 1, 9))
            callee_idx = random.randint(0, min(len(user_ids) - 1, 9))
            
            if caller_idx == callee_idx:
                callee_idx = (callee_idx + 1) % min(len(user_ids), 10)
            
            call_id = generate_id()
            call_type = random.choice(call_types)
            status = random.choice(call_statuses)
            started_at = datetime.now() - timedelta(minutes=random.randint(1, 4320))  # up to 3 days ago
            
            if status == 'completed':
                duration = random.choice(call_durations)
                ended_at = started_at + timedelta(seconds=duration)
            else:
                duration = 0
                ended_at = None
            
            db.execute('''
                INSERT INTO flow_call_sessions (id, call_type, initiated_by, status, started_at, ended_at, duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (call_id, call_type, user_ids[caller_idx], status, started_at.isoformat(), ended_at.isoformat() if ended_at else None, duration))
            
            # Add caller as participant
            db.execute('''
                INSERT INTO flow_call_participants (call_id, user_id, call_status, joined_at, left_at)
                VALUES (?, ?, 'joined', ?, ?)
            ''', (call_id, user_ids[caller_idx], started_at.isoformat(), ended_at.isoformat() if ended_at else None))
            
            # Add callee as participant
            db.execute('''
                INSERT INTO flow_call_participants (call_id, user_id, call_status, joined_at, left_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (call_id, user_ids[callee_idx], 'joined' if status == 'completed' else status, started_at.isoformat(), ended_at.isoformat() if ended_at else None))
        
        db.commit()
    
    import sys
    print("[FLOW] Demo data seeded successfully", file=sys.stderr)
    return True


# ============================================================================
# SAMPLE CHANNELS WITH IDs AND MEDIA
# ============================================================================

def seed_sample_channels():
    """
    Create sample channels with proper IDs (usernames for public, invite codes for private)
    and sample messages including text, images, and videos.
    """
    import random
    from datetime import timedelta
    import sys

    print("[FLOW] Creating sample channels with IDs and demo data...", file=sys.stderr)

    # Get existing users
    users = get_all('SELECT id, username FROM users LIMIT 20')
    if not users:
        print("[FLOW] No users found. Please create users first.", file=sys.stderr)
        return False

    user_ids = [u['id'] for u in users]
    creator_id = user_ids[0]  # Use first user as creator

    # Sample channels data with unique IDs
    # Format: (name, channel_id, description, type, category)
    sample_channels = [
        # Public channels with custom IDs
        ('General', 'general', 'General discussions and announcements for everyone', 'public', 'Company'),
        ('Engineering', 'engineering', 'Engineering team discussions, code reviews, and technical updates', 'public', 'Departments'),
        ('Sales Team', 'sales-team', 'Sales leads, customer meetings, and revenue updates', 'public', 'Departments'),
        ('Marketing', 'marketing', 'Marketing campaigns, social media, and brand updates', 'public', 'Departments'),
        ('HR & People', 'hr-people', 'Human resources policies, benefits, and employee resources', 'public', 'Departments'),
        ('Warehouse Ops', 'warehouse-ops', 'Warehouse operations, inventory, and logistics', 'public', 'Operations'),
        ('IT Support', 'it-support', 'Technical support, IT requests, and infrastructure', 'public', 'Operations'),
        ('Random', 'random', 'Random conversations, jokes, and water cooler chat', 'public', 'Social'),
        ('Introductions', 'introductions', 'Introduce yourself to the team!', 'public', 'Social'),
        ('Announcements', 'announcements', 'Official company announcements and updates', 'public', 'Company'),

        # Private channels (require invite code)
        ('Leadership', 'leadership', 'Executive team discussions', 'private', 'Leadership'),
        ('Project Alpha', 'project-alpha', 'Core team for Project Alpha - confidential', 'private', 'Projects'),
        ('M&A Discussions', 'ma-discussions', 'Mergers and acquisitions planning', 'private', 'Leadership'),
        ('Q4 Planning', 'q4-planning', 'Q4 strategic planning and goals', 'private', 'Planning'),
        ('Board Communications', 'board-comms', 'Board of directors communications', 'private', 'Leadership'),
    ]

    # Sample messages with different types
    text_messages = {
        'general': [
            "Good morning everyone! Hope you all had a great weekend! 👋",
            "Reminder: All-hands meeting is scheduled for tomorrow at 3 PM.",
            "Can someone help me with the quarterly report?",
            "The new coffee machine in the break room is amazing! ☕",
            "Welcome to our newest team member, @admin! Please introduce yourself.",
            "Don't forget to submit your timesheets by Friday.",
            "Great job on closing that deal! 🎉",
            "Has anyone seen the updated company policy document?",
            "The office will be closed next Friday for the holiday.",
            "Who's joining for lunch today?",
        ],
        'engineering': [
            "Just pushed the new deployment to production. Please monitor for any issues.",
            "The API documentation has been updated with new endpoints.",
            "Can I get a code review on PR #342?",
            "Found and fixed a critical bug in the payment processing module.",
            "The new caching layer has improved response times by 40%!",
            "Meeting to discuss the architecture review at 2 PM today.",
            "Updated the test suite - all tests passing now ✓",
            "The CI/CD pipeline has been optimized. Build times down 50%.",
            "Who's working on the authentication module? Need some input.",
            "Documentation for the new microservice is ready for review.",
        ],
        'sales-team': [
            "Just closed a huge deal with SDAD Corporation! 🎉",
            "The new CRM system is live. Please update your client records.",
            "Sales targets for Q4 have been updated - check your emails.",
            "Anyone available for a client call at 4 PM?",
            "Great presentation today to the prospective client!",
            "The proposal for the new project is ready for review.",
            "Q3 revenue is up 25% compared to last year!",
            "Reminder: Sales training session tomorrow morning.",
            "The marketing materials have arrived - pick them up from reception.",
            "Client feedback survey results are in - 92% satisfaction!",
        ],
        'marketing': [
            "The new social media campaign launches next week!",
            "Check out our latest blog post on industry trends.",
            "The email newsletter has a 45% open rate this month!",
            "Updated brand guidelines have been uploaded to the shared drive.",
            "Who's attending the marketing conference next month?",
            "The new product brochure designs look amazing!",
            "Website traffic is up 30% this quarter! 📈",
            "We hit 10K followers on LinkedIn! Thanks team!",
            "The video ad campaign results are in - exceeded expectations.",
            "Content calendar for next month is ready for review.",
        ],
        'hr-people': [
            "Open enrollment for benefits starts next Monday.",
            "Reminder: Performance reviews are due by end of month.",
            "New employee onboarding sessions are every Monday at 9 AM.",
            "The company picnic is scheduled for next month - details coming soon!",
            "Updated PTO policy has been posted - please review.",
            "We are hiring! Please refer qualified candidates.",
            "The wellness program launch is next week.",
            "Reminder to update your emergency contact information.",
            "New learning & development courses are available.",
            "Town hall meeting scheduled for Friday at noon.",
        ],
        'warehouse-ops': [
            "Inventory count for Q3 is complete.",
            "The new forklift training session is tomorrow morning.",
            "Shipping delays expected due to weather - plan accordingly.",
            "We processed 500 orders today - new record! 🚀",
            "Updated safety protocols are now in effect.",
            "The new racking system installation is complete.",
            "Quality control flagged 3 shipments for review.",
            "Warehouse temperature monitoring system is now operational.",
            "Loading dock 3 will be closed for maintenance on Friday.",
            "Excellent work by the night shift team!",
        ],
        'it-support': [
            "System maintenance scheduled for Saturday 2 AM - 6 AM.",
            "Password reset requests - please use the self-service portal.",
            "New software licenses have been provisioned.",
            "The VPN issue has been resolved. Please reconnect.",
            "Reminder: Backup verification is every Friday.",
            "IT security training must be completed by end of month.",
            "The new workstations are ready for pickup.",
            "Printer ink cartridges need replacement in Building A.",
            "Multi-factor authentication is now mandatory.",
            "Please report any suspicious emails to IT immediately.",
        ],
        'random': [
            "Anyone up for Friday happy hour? 🍺",
            "This is hilarious - had to share!",
            "Who won the office football pool?",
            "Book recommendations for the weekend?",
            "The new restaurant across the street is amazing!",
            "Anyone else watching the game tonight?",
            "Pet photos thread! Share your furry friends! 🐕",
            "Coffee recommendations for cold brew lovers?",
            "The weather is finally cooling down!",
            "Who's coming to the game night this weekend?",
        ],
        'introductions': [
            "Hi everyone! I'm new to the team and excited to be here!",
            "Welcome aboard! Feel free to ask any questions.",
            "Introduce yourself here so we can all get to know each other!",
            "Just transferred from the Dubai office. Hello everyone!",
            "Looking forward to meeting all of you in person!",
            "4 years at the company and still learning every day!",
            "Fresh graduate joining the team this week!",
            "Remote worker here - based in a different timezone!",
            "Celebrating my 1-year anniversary with the company! 🎂",
            "Former competitor employee - happy to be here!",
        ],
        'announcements': [
            "📢 IMPORTANT: New company policy updates effective immediately.",
            "Q3 financial results exceeded expectations!",
            "Office hours during Ramadan have been updated.",
            "New parking regulations will be enforced starting next week.",
            "Company town hall recording is now available.",
            "Annual performance review cycle begins next month.",
            "We are proud to announce a new partnership with Microsoft.",
            "Updated expense reimbursement policy - effective immediately.",
            "Congratulations to the Q3 award winners!",
            "Holiday schedule for next year has been posted.",
        ],
        'leadership': [
            "Confidential: Q4 strategic planning review.",
            "Board meeting notes from last week attached.",
            "Key performance indicators are on track.",
            "Budget review scheduled for next Tuesday.",
            "Confidential: Potential acquisition discussions.",
            "Leadership development program nominations open.",
            "Quarterly business review preparation starts Monday.",
            "Strategic initiatives update - restricted audience.",
        ],
        'project-alpha': [
            "Phase 1 completion celebrated - team lunch on Friday!",
            "Milestone 2 deliverables due next week.",
            "Client feedback on demo was overwhelmingly positive.",
            "Resource allocation for Phase 2 needs review.",
            "Risk assessment updated - new mitigation strategies added.",
            "The prototype exceeded performance expectations!",
            "Integration testing scheduled for next sprint.",
            "Stakeholder presentation preparation starts tomorrow.",
        ],
        'ma-discussions': [
            "Confidential: Due diligence documents uploaded.",
            "Legal review in progress with external counsel.",
            "Valuation models updated with latest projections.",
            "Board presentation preparation timeline attached.",
            "NDA signed - moving to next phase of discussions.",
            "Target company financial health looks promising.",
            "Regulatory approval process mapped out.",
        ],
        'q4-planning': [
            "Q4 targets distribution meeting tomorrow.",
            "Resource planning spreadsheet updated.",
            "Marketing budget allocation needs approval.",
            "Sales pipeline review scheduled for Monday.",
            "Operational capacity planning in progress.",
            "Cross-functional alignment session this Thursday.",
            "Final Q4 goals due to leadership by Friday.",
        ],
        'board-comms': [
            "Board meeting scheduled for end of month.",
            "Quarterly investor relations update attached.",
            "Executive compensation review documentation.",
            "Strategic presentation for board review.",
            "Governance committee recommendations.",
            "Confidential financial projections for board eyes only.",
        ],
    }

    # Image URLs (using placeholder services)
    image_messages = {
        'general': [
            ("Check out our new office layout! 🏢", "https://picsum.photos/seed/office1/800/600"),
            ("Team lunch photo from last week!", "https://picsum.photos/seed/team1/800/600"),
            ("The renovated meeting room looks amazing!", "https://picsum.photos/seed/room1/800/600"),
            ("New company swag arrived! 👕", "https://picsum.photos/seed/swag1/800/600"),
        ],
        'engineering': [
            ("Architecture diagram for the new system", "https://picsum.photos/seed/arch1/800/600"),
            ("Code review feedback visualization", "https://picsum.photos/seed/code1/800/600"),
            ("Server room upgrade completed!", "https://picsum.photos/seed/server1/800/600"),
            ("New monitoring dashboard sneak peek", "https://picsum.photos/seed/monitor1/800/600"),
        ],
        'sales-team': [
            ("Celebrating with our latest signed client!", "https://picsum.photos/seed/client1/800/600"),
            ("The new office in Dubai looks great", "https://picsum.photos/seed/dubai1/800/600"),
            ("Q3 sales board - incredible results!", "https://picsum.photos/seed/sales1/800/600"),
            ("Product demo setup for upcoming presentation", "https://picsum.photos/seed/demo1/800/600"),
        ],
        'marketing': [
            ("Social media campaign mockup - draft v2", "https://picsum.photos/seed/social1/800/600"),
            ("New brand guidelines cover design", "https://picsum.photos/seed/brand1/800/600"),
            ("Website redesign preview", "https://picsum.photos/seed/web1/800/600"),
            ("Event booth setup at trade show", "https://picsum.photos/seed/event1/800/600"),
        ],
        'warehouse-ops': [
            ("New inventory management system dashboard", "https://picsum.photos/seed/inventory1/800/600"),
            ("Loading dock during peak hours", "https://picsum.photos/seed/dock1/800/600"),
            ("Safety equipment inspection day", "https://picsum.photos/seed/safety1/800/600"),
            ("Organized warehouse shelves after reorganization", "https://picsum.photos/seed/shelves1/800/600"),
        ],
        'random': [
            ("Caturday is here! 🐱", "https://picsum.photos/seed/cat1/800/600"),
            ("Office dog meeting day! 🐕", "https://picsum.photos/seed/dog1/800/600"),
            ("Lunch at the new place nearby", "https://picsum.photos/seed/lunch1/800/600"),
            ("Sunset view from our office terrace", "https://picsum.photos/seed/sunset1/800/600"),
        ],
    }

    # Video placeholder messages
    video_messages = {
        'general': [
            ("Watch: Company year-in-review highlights!", "https://www.w3schools.com/html/mov_bbb.mp4"),
            ("Training video: New employee onboarding process", "https://www.w3schools.com/html/movie.mp4"),
        ],
        'engineering': [
            ("Demo: New feature showcase recording", "https://www.w3schools.com/html/mov_bbb.mp4"),
            ("Tutorial: How to use the new CI/CD pipeline", "https://www.w3schools.com/html/movie.mp4"),
        ],
        'marketing': [
            ("New commercial - final cut for review", "https://www.w3schools.com/html/mov_bbb.mp4"),
            ("Social media content creation behind the scenes", "https://www.w3schools.com/html/movie.mp4"),
        ],
        'sales-team': [
            ("Product demo recording for client presentation", "https://www.w3schools.com/html/mov_bbb.mp4"),
            ("Sales pitch rehearsal - feedback welcome!", "https://www.w3schools.com/html/movie.mp4"),
        ],
    }

    # Create channels and messages
    now = datetime.now()

    for idx, (name, channel_id_val, description, ch_type, category) in enumerate(sample_channels):
        # Check if channel already exists
        existing = get_one('SELECT 1 FROM flow_channels WHERE channel_id = ?', (channel_id_val,))
        if existing:
            print(f"[FLOW] Channel {channel_id_val} already exists, skipping...", file=sys.stderr)
            continue

        # Create the channel
        db_channel_id = generate_id()
        conv_id = generate_id()
        invite_code = None if ch_type == 'public' else generate_invite_code()

        with get_db_context() as db:
            # Create channel
            db.execute('''
                INSERT INTO flow_channels (id, name, channel_id, description, channel_type, category, invite_code, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (db_channel_id, name, channel_id_val, description, ch_type, category, invite_code, creator_id))

            # Create corresponding conversation
            db.execute('''
                INSERT INTO flow_conversations (id, conversation_type, name, created_by, last_message_at)
                VALUES (?, 'channel', ?, ?, ?)
            ''', (conv_id, name, creator_id, now.isoformat()))

            # Add creator as admin
            db.execute('''
                INSERT INTO flow_channel_members (channel_id, user_id, role)
                VALUES (?, ?, 'admin')
            ''', (db_channel_id, creator_id))

            db.execute('''
                INSERT INTO flow_conversation_members (conversation_id, user_id, role)
                VALUES (?, ?, 'admin')
            ''', (conv_id, creator_id))

            # Add some random members (for public channels)
            if ch_type == 'public':
                member_count = random.randint(3, min(8, len(user_ids)))
                for uid in random.sample(user_ids[1:], member_count):
                    db.execute('''
                        INSERT OR IGNORE INTO flow_channel_members (channel_id, user_id, role)
                        VALUES (?, ?, 'member')
                    ''', (db_channel_id, uid))

                    db.execute('''
                        INSERT OR IGNORE INTO flow_conversation_members (conversation_id, user_id, role)
                        VALUES (?, ?, 'member')
                    ''', (conv_id, uid))

        # Add text messages
        text_key = channel_id_val if channel_id_val in text_messages else 'general'
        msg_templates = text_messages.get(text_key, text_messages['general'])

        for i, content in enumerate(msg_templates):
            msg_id = generate_id()
            sender_id = random.choice(user_ids)
            minutes_ago = random.randint(1, 14400)  # Up to 10 days ago
            msg_time = (now - timedelta(minutes=minutes_ago)).isoformat()

            with get_db_context() as db:
                db.execute('''
                    INSERT INTO flow_messages (id, conversation_id, sender_id, message_type, content, created_at)
                    VALUES (?, ?, ?, 'text', ?, ?)
                ''', (msg_id, conv_id, sender_id, content, msg_time))

                # Update conversation last message
                db.execute('''
                    UPDATE flow_conversations
                    SET last_message_at = ?, last_message_preview = ?
                    WHERE id = ?
                ''', (msg_time, content[:80], conv_id))

        # Add image messages
        img_key = channel_id_val if channel_id_val in image_messages else None
        if img_key and img_key in image_messages:
            for content, image_url in image_messages[img_key]:
                msg_id = generate_id()
                sender_id = random.choice(user_ids)
                minutes_ago = random.randint(1, 7200)  # Up to 5 days ago
                msg_time = (now - timedelta(minutes=minutes_ago)).isoformat()

                metadata = json.dumps({
                    'attachments': [{
                        'type': 'image',
                        'url': image_url,
                        'thumbnail': image_url,
                    }]
                })

                with get_db_context() as db:
                    db.execute('''
                        INSERT INTO flow_messages (id, conversation_id, sender_id, message_type, content, metadata, created_at)
                        VALUES (?, ?, ?, 'image', ?, ?, ?)
                    ''', (msg_id, conv_id, sender_id, content, metadata, msg_time))

                    db.execute('''
                        UPDATE flow_conversations
                        SET last_message_at = ?, last_message_preview = ?
                        WHERE id = ?
                    ''', (msg_time, content[:80], conv_id))

        # Add video messages
        vid_key = channel_id_val if channel_id_val in video_messages else None
        if vid_key and vid_key in video_messages:
            for content, video_url in video_messages[vid_key]:
                msg_id = generate_id()
                sender_id = random.choice(user_ids)
                minutes_ago = random.randint(1, 3600)  # Up to 2.5 days ago
                msg_time = (now - timedelta(minutes=minutes_ago)).isoformat()

                metadata = json.dumps({
                    'attachments': [{
                        'type': 'video',
                        'url': video_url,
                        'thumbnail': 'https://picsum.photos/seed/video/320/180',
                    }]
                })

                with get_db_context() as db:
                    db.execute('''
                        INSERT INTO flow_messages (id, conversation_id, sender_id, message_type, content, metadata, created_at)
                        VALUES (?, ?, ?, 'video', ?, ?, ?)
                    ''', (msg_id, conv_id, sender_id, content, metadata, msg_time))

                    db.execute('''
                        UPDATE flow_conversations
                        SET last_message_at = ?, last_message_preview = ?
                        WHERE id = ?
                    ''', (msg_time, content[:80], conv_id))

        print(f"[FLOW] Created channel: {name} (ID: {channel_id_val}, Type: {ch_type})", file=sys.stderr)

    print("[FLOW] Sample channels created successfully!", file=sys.stderr)
    return True


# ============================================================================
# TEST MESSAGES SEEDER
# ============================================================================

def seed_test_messages():
    """
    Add additional test messages to existing conversations.
    This is called separately to add more realistic conversation data.
    """
    import random
    from datetime import timedelta
    import sys

    print("[FLOW] Adding test messages to conversations...", file=sys.stderr)

    # Get all conversations with members
    conversations = get_all('''
        SELECT fc.*,
               (SELECT user_id FROM flow_conversation_members WHERE conversation_id = fc.id LIMIT 1) as first_member
        FROM flow_conversations fc
        WHERE fc.conversation_type IN ('private', 'group', 'channel')
    ''')

    if not conversations:
        print("[FLOW] No conversations found to add messages to", file=sys.stderr)
        return False

    # Get users for message sending
    users = get_all('SELECT id, username FROM users LIMIT 20')
    if not users:
        print("[FLOW] No users found", file=sys.stderr)
        return False

    user_ids = [u['id'] for u in users]

    # Different message templates for different conversation types
    channel_messages = {
        'general': [
            "سلام به همه! صبح بخیر ☀️",
            "کسی میدونه جلسه امروز ساعت چنده؟",
            "گزارش هفتگی رو ارسال کردم",
            "در مورد پروژه جدید چطور فکر می‌کنید؟",
            "تبریک میگم به تیم فروش! عالی بودید! 🎉",
            "یک لحظه وقت دارید برای یه سوال؟",
            "فایل‌های جدید آپلود شد",
            "فردا تعطیل هستیم",
            "لطفا status خودتون رو آپدیت کنید",
            "کسی میتونه pull request من رو review کنه؟",
        ],
        'engineering': [
            "deployment جدید برای امشب برنامه‌ریزی شده",
            "کسی تجربه با این library داره؟",
            "مشکل رو پیدا کردم! باگ ساده‌ای بود",
            "code review لطفا 🙏",
            "تست‌ها pass شدن ✓",
            "ممنون از کمکت!",
            "این feature جدید عالیه!",
            "لطفا قبل از merge تست کنید",
            "نسخه جدید آماده است",
            "documentation رو آپدیت کردم",
        ],
        'random': [
            "کسی غذا پیشنهاد داره؟ 🍕",
            "امشب کسی وقت استراحت داره؟",
            "لینک جالب: https://example.com",
            "این عکس رو دیدید؟ 😍",
            "جمعه‌بازار چطور بود؟",
            "کتاب جدید推荐 می‌کنید؟",
            "ساعت چند می‌رید خونه؟",
            "پیتزا order می‌دیم؟",
            "فکر کنم باید یه تیم building داشته باشیم!",
            "کسی می‌خواد کافه بریم؟",
        ],
        'default': [
            "سلام! 👋",
            "خوبین؟",
            "چطور میتونم کمک کنم؟",
            "لطفا اطلاعات بیشتر بدید",
            "باشه، در جریان هستم",
            "ممنون از پیامتون",
            "این موضوع مهم هست",
            "لطفا فایل رو چک کنید",
            "جلسه بعدی کی هست؟",
            "همه چیز آماده است",
        ]
    }

    group_messages = [
        "سلام گروه! 🙋",
        "پروژه پیشرفت خوبی داشته",
        "deadline نزدیک هست، تمرکز کنیم",
        "کسی سوالی داره؟",
        "آپدیت: کارها انجام شد ✓",
        "عالی! تیم عالی هستید",
        "فردا جلسه داریم",
        "document رو آپلود کردم",
        "لطفا نظرتون رو بگید",
        "این ایده رو چطور فکر می‌کنید؟",
        "منابع بیشتری نیاز داریم",
        "مشکلی نیست، حلش می‌کنیم",
        "ممنون از همکاری همه",
        "进展顺利！",
        "会议提前到3点",
    ]

    private_messages = [
        "سلام! خوبی؟",
        "بله، ممنون",
        "در مورد پروژه صحبت می‌کردیم",
        "文件已发送",
        "会议定在明天下午3点",
        "好的，我明白了",
        "谢谢你告诉我",
        "我处理一下",
        "请稍等",
        "好的！",
        "کارها رو چک کردم",
        "ایمیل رو فرستادم",
        "سوالی داشتم",
        "میتونی کمکم کنی؟",
        "باشه، بعدا صحبت می‌کنیم",
    ]

    now = datetime.now()
    message_count = 0

    with get_db_context() as db:
        for conv in conversations:
            conv_type = conv['conversation_type']
            conv_id = conv['id']
            conv_name = (conv.get('name') or '').lower()

            # Determine message template based on conversation type and name
            if conv_type == 'channel':
                # Find matching template
                template_key = 'default'
                for key in channel_messages.keys():
                    if key in conv_name:
                        template_key = key
                        break
                msg_template = channel_messages[template_key]
            elif conv_type == 'group':
                msg_template = group_messages
            else:  # private
                msg_template = private_messages

            # Add 5-15 messages per conversation
            num_messages = random.randint(5, 15)

            for i in range(num_messages):
                msg_id = generate_id()
                sender_id = random.choice(user_ids)
                content = random.choice(msg_template)

                # Stagger messages over the past week
                minutes_ago = random.randint(1, 10080)  # up to 7 days
                msg_time = (now - timedelta(minutes=minutes_ago)).isoformat()

                db.execute('''
                    INSERT INTO flow_messages (id, conversation_id, sender_id, message_type, content, created_at)
                    VALUES (?, ?, ?, 'text', ?, ?)
                ''', (msg_id, conv_id, sender_id, content, msg_time))

                # Update conversation
                preview = content[:50] if content else '[Media]'
                db.execute('''
                    UPDATE flow_conversations
                    SET last_message_at = ?, last_message_preview = ?
                    WHERE id = ?
                ''', (msg_time, preview, conv_id))

                message_count += 1

        db.commit()

    print(f"[FLOW] Added {message_count} test messages", file=sys.stderr)
    return True


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_flow():
    """Initialize FLOW platform - call this on app startup."""
    try:
        initialize_flow_tables()
        
        # Check if we need to seed data
        users = get_all('SELECT id FROM users')
        profiles = get_all('SELECT user_id FROM flow_user_profiles')
        
        if len(users) > 0 and len(profiles) < len(users):
            seed_flow_data()
        
        return True
    except Exception as e:
        import sys
        print(f"[FLOW] Initialization error: {e}", file=sys.stderr)
        return False


# Auto-initialize when module is imported
if __name__ != '__main__':
    try:
        initialize_flow()
    except:
        pass
