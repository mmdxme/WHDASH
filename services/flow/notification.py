"""Flow Notification Service - Push notifications and unread counts."""
from services.base import BaseService


class NotificationService(BaseService):
    """Service for notification operations."""

    def send_push_notification(self, user_id, title, message, notification_type='info', related_url=None):
        """Send a push notification to a user."""
        db = self.get_db()
        db.execute('''
            INSERT INTO flow_notifications (user_id, title, message, type, related_url, is_read, created_at)
            VALUES (?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
        ''', (user_id, title, message, notification_type, related_url))
        db.commit()

    def get_unread_count(self, user_id):
        """Get count of unread notifications."""
        db = self.get_db()
        result = db.execute(
            'SELECT COUNT(*) as count FROM flow_notifications WHERE user_id = ? AND is_read = 0',
            (user_id,)
        ).fetchone()
        return result['count'] if result else 0

    def get_recent_notifications(self, user_id, limit=20):
        """Get recent notifications for a user."""
        db = self.get_db()
        return db.execute('''
            SELECT * FROM flow_notifications
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit)).fetchall()

    def mark_as_read(self, notification_id, user_id):
        """Mark a notification as read."""
        db = self.get_db()
        db.execute(
            'UPDATE flow_notifications SET is_read = 1 WHERE id = ? AND user_id = ?',
            (notification_id, user_id)
        )
        db.commit()

    def mark_all_as_read(self, user_id):
        """Mark all notifications as read for a user."""
        db = self.get_db()
        db.execute('UPDATE flow_notifications SET is_read = 1 WHERE user_id = ?', (user_id,))
        db.commit()