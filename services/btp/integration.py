"""BTP Integration Service - Integration flow management."""
from services.base import BaseService


class IntegrationService(BaseService):
    """Service for BTP integration operations."""

    def get_integrations(self, connector_id=None, status=None):
        """Get list of integrations."""
        db = self.get_db()
        query = 'SELECT * FROM btp_integrations WHERE 1=1'
        params = []
        if connector_id:
            query += " AND connector_id = ?"
            params.append(connector_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY name"
        return db.execute(query, params).fetchall()

    def create_integration(self, name, connector_id, flow_config, created_by):
        """Create a new integration."""
        db = self.get_db()
        db.execute('''
            INSERT INTO btp_integrations (name, connector_id, flow_config, status, created_by, created_at)
            VALUES (?, ?, ?, 'DRAFT', ?, CURRENT_TIMESTAMP)
        ''', (name, connector_id, flow_config, created_by))
        db.commit()
        return db.execute('SELECT last_insert_rowid()').fetchone()[0]

    def get_integration_metrics(self, integration_id):
        """Get integration execution metrics."""
        db = self.get_db()
        return db.execute('''
            SELECT COUNT(*) as total_runs,
                   SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful,
                   SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
                   AVG(execution_time_ms) as avg_time
            FROM btp_integration_runs
            WHERE integration_id = ?
        ''', (integration_id,)).fetchone()

    def execute_integration(self, integration_id):
        """Trigger integration execution."""
        db = self.get_db()
        integration = db.execute('SELECT * FROM btp_integrations WHERE id = ?', (integration_id,)).fetchone()
        if not integration:
            raise ValueError('Integration not found.')

        db.execute('''
            INSERT INTO btp_integration_runs (integration_id, status, started_at)
            VALUES (?, 'RUNNING', CURRENT_TIMESTAMP)
        ''', (integration_id,))
        db.commit()
        return db.execute('SELECT last_insert_rowid()').fetchone()[0]