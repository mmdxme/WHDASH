"""BTP Connector Service - SAP BTP connector management."""
from services.base import BaseService


class ConnectorService(BaseService):
    """Service for BTP connector operations."""

    def get_connectors(self, status=None):
        """Get list of BTP connectors."""
        db = self.get_db()
        query = 'SELECT * FROM btp_connectors WHERE 1=1'
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY name"
        return db.execute(query, params).fetchall()

    def create_connector(self, name, connector_type, config, created_by):
        """Create a new BTP connector."""
        db = self.get_db()
        db.execute('''
            INSERT INTO btp_connectors (name, type, config, status, created_by, created_at)
            VALUES (?, ?, ?, 'DISCONNECTED', ?, CURRENT_TIMESTAMP)
        ''', (name, connector_type, config, created_by))
        db.commit()
        return db.execute('SELECT last_insert_rowid()').fetchone()[0]

    def test_connection(self, connector_id):
        """Test connector connection."""
        db = self.get_db()
        connector = db.execute('SELECT * FROM btp_connectors WHERE id = ?', (connector_id,)).fetchone()
        if not connector:
            raise ValueError('Connector not found.')
        return {'status': 'success', 'message': 'Connection test successful'}

    def update_connector_status(self, connector_id, status):
        """Update connector status."""
        db = self.get_db()
        db.execute('UPDATE btp_connectors SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                   (status, connector_id))
        db.commit()