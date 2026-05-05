"""Flow Messaging Service - Message handling with rate limiting."""
from services.base import BaseService
import time


class MessagingService(BaseService):
    """Service for messaging operations."""

    _rate_limit_cache = {}

    def send_message(self, sender_id, recipient_id, content, conversation_id=None, parent_id=None):
        """Send a message with rate limiting."""
        now = time.time()
        key = f'msg_{sender_id}'

        if key in self._rate_limit_cache:
            if now - self._rate_limit_cache[key] < 1:
                raise ValueError('Rate limit exceeded. Please wait before sending another message.')

        db = self.get_db()
        db.execute('''
            INSERT INTO flow_messages (conversation_id, sender_id, recipient_id, content, parent_id, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (conversation_id, sender_id, recipient_id, content, parent_id))
        db.commit()

        self._rate_limit_cache[key] = now
        return db.execute('SELECT last_insert_rowid()').fetchone()[0]

    def search_messages(self, user_id, query=None, recipient_id=None, start_date=None, end_date=None, limit=50):
        """Search messages with parameterized filters."""
        db = self.get_db()
        sql = '''
            SELECT m.*, u.username as sender_name, r.username as recipient_name
            FROM flow_messages m
            JOIN users u ON u.id = m.sender_id
            JOIN users r ON r.id = m.recipient_id
            WHERE (m.sender_id = ? OR m.recipient_id = ?)
        '''
        params = [user_id, user_id]

        if query:
            sql += " AND m.content LIKE ?"
            params.append(f'%{query}%')
        if recipient_id:
            sql += " AND m.recipient_id = ?"
            params.append(recipient_id)
        if start_date:
            sql += " AND m.created_at >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND m.created_at <= ?"
            params.append(end_date)

        sql += " ORDER BY m.created_at DESC LIMIT ?"
        params.append(limit)
        return db.execute(sql, params).fetchall()

    def get_conversation_messages(self, conversation_id, limit=100, offset=0):
        """Get messages in a conversation."""
        db = self.get_db()
        return db.execute('''
            SELECT m.*, u.username as sender_name
            FROM flow_messages m
            JOIN users u ON u.id = m.sender_id
            WHERE m.conversation_id = ?
            ORDER BY m.created_at DESC
            LIMIT ? OFFSET ?
        ''', (conversation_id, limit, offset)).fetchall()

    def delete_message(self, message_id, user_id):
        """Soft delete a message (only by sender)."""
        db = self.get_db()
        msg = db.execute('SELECT sender_id FROM flow_messages WHERE id = ?', (message_id,)).fetchone()
        if not msg or msg['sender_id'] != user_id:
            raise ValueError('Not authorized to delete this message.')
        db.execute('UPDATE flow_messages SET is_deleted = 1, deleted_at = CURRENT_TIMESTAMP WHERE id = ?', (message_id,))
        db.commit()