"""Flow Channel Service - Channel management."""
from services.base import BaseService


class ChannelService(BaseService):
    """Service for channel operations."""

    def create_channel(self, name, created_by, channel_type='TEAM', description=None, is_private=False):
        """Create a new channel."""
        db = self.get_db()
        db.execute('''
            INSERT INTO flow_channels (name, type, description, is_private, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (name, channel_type, description, 1 if is_private else 0, created_by))
        db.commit()
        channel_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

        db.execute('''
            INSERT INTO flow_channel_members (channel_id, user_id, role, joined_at)
            VALUES (?, ?, 'ADMIN', CURRENT_TIMESTAMP)
        ''', (channel_id, created_by))
        db.commit()
        return channel_id

    def get_channel_members(self, channel_id):
        """Get members of a channel."""
        db = self.get_db()
        return db.execute('''
            SELECT u.id, u.username, u.email, cm.role, cm.joined_at
            FROM flow_channel_members cm
            JOIN users u ON u.id = cm.user_id
            WHERE cm.channel_id = ?
            ORDER BY cm.joined_at
        ''', (channel_id,)).fetchall()

    def add_member(self, channel_id, user_id, role='MEMBER'):
        """Add a member to a channel."""
        db = self.get_db()
        existing = db.execute(
            'SELECT id FROM flow_channel_members WHERE channel_id = ? AND user_id = ?',
            (channel_id, user_id)
        ).fetchone()
        if existing:
            raise ValueError('User is already a member.')

        db.execute('''
            INSERT INTO flow_channel_members (channel_id, user_id, role, joined_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (channel_id, user_id, role))
        db.commit()

    def remove_member(self, channel_id, user_id):
        """Remove a member from a channel."""
        db = self.get_db()
        db.execute(
            'DELETE FROM flow_channel_members WHERE channel_id = ? AND user_id = ?',
            (channel_id, user_id)
        )
        db.commit()

    def list_channels(self, user_id=None, channel_type=None):
        """List channels."""
        db = self.get_db()
        query = '''
            SELECT c.*, u.username as created_by_name
            FROM flow_channels c
            JOIN users u ON u.id = c.created_by
            WHERE 1=1
        '''
        params = []
        if user_id:
            query += " AND c.id IN (SELECT channel_id FROM flow_channel_members WHERE user_id = ?)"
            params.append(user_id)
        if channel_type:
            query += " AND c.type = ?"
            params.append(channel_type)
        query += " ORDER BY c.name"
        return db.execute(query, params).fetchall()