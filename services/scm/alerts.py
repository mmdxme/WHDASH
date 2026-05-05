"""SCM Alerts Service - Alert management."""
from services.base import BaseService


class AlertsService(BaseService):
    """Service for SCM alert operations."""

    def get_active_alerts(self, user_id=None, severity=None):
        """Get active alerts."""
        db = self.get_db()
        query = '''
            SELECT a.*, i.item_code, i.name as item_name, w.name as warehouse_name
            FROM scm_alerts a
            LEFT JOIN wms_items i ON i.id = a.item_id
            LEFT JOIN wms_warehouses w ON w.id = a.warehouse_id
            WHERE a.status = 'ACTIVE'
        '''
        params = []
        if user_id:
            query += " AND (a.user_id = ? OR a.user_id IS NULL)"
            params.append(user_id)
        if severity:
            query += " AND a.severity = ?"
            params.append(severity)
        query += " ORDER BY a.created_at DESC"
        return db.execute(query, params).fetchall()

    def acknowledge_alert(self, alert_id, user_id=None):
        """Acknowledge an alert."""
        db = self.get_db()
        db.execute('''
            UPDATE scm_alerts
            SET status = 'ACKNOWLEDGED', acknowledged_at = CURRENT_TIMESTAMP, acknowledged_by = ?
            WHERE id = ?
        ''', (user_id, alert_id))
        db.commit()

    def get_alert_summary(self):
        """Get alert summary counts by severity."""
        db = self.get_db()
        return db.execute('''
            SELECT severity, COUNT(*) as count
            FROM scm_alerts
            WHERE status = 'ACTIVE'
            GROUP BY severity
        ''').fetchall()