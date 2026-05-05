"""BTP API Management Service - API analytics and management."""
from services.base import BaseService


class APIManagementService(BaseService):
    """Service for BTP API management."""

    def get_api_usage_stats(self, api_id=None, start_date=None, end_date=None):
        """Get API usage statistics."""
        db = self.get_db()
        query = '''
            SELECT api_id, method, endpoint,
                   COUNT(*) as call_count,
                   AVG(response_time_ms) as avg_response_time,
                   SUM(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 ELSE 0 END) as success_count,
                   SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_count
            FROM btp_api_logs
            WHERE 1=1
        '''
        params = []
        if api_id:
            query += " AND api_id = ?"
            params.append(api_id)
        if start_date:
            query += " AND created_at >= ?"
            params.append(start_date)
        if end_date:
            query += " AND created_at <= ?"
            params.append(end_date)
        query += " GROUP BY api_id, method, endpoint ORDER BY call_count DESC"
        return db.execute(query, params).fetchall()

    def log_api_call(self, api_id, method, endpoint, status_code, response_time_ms, user_id=None):
        """Log an API call."""
        db = self.get_db()
        db.execute('''
            INSERT INTO btp_api_logs (api_id, method, endpoint, status_code, response_time_ms, user_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (api_id, method, endpoint, status_code, response_time_ms, user_id))
        db.commit()

    def get_top_apis(self, limit=10):
        """Get top APIs by call volume."""
        db = self.get_db()
        return db.execute('''
            SELECT api_id, endpoint, COUNT(*) as call_count
            FROM btp_api_logs
            GROUP BY api_id
            ORDER BY call_count DESC
            LIMIT ?
        ''', (limit,)).fetchall()

    def get_error_summary(self, start_date=None, end_date=None):
        """Get API error summary."""
        db = self.get_db()
        query = '''
            SELECT api_id, endpoint, status_code, COUNT(*) as count
            FROM btp_api_logs
            WHERE status_code >= 400
        '''
        params = []
        if start_date:
            query += " AND created_at >= ?"
            params.append(start_date)
        if end_date:
            query += " AND created_at <= ?"
            params.append(end_date)
        query += " GROUP BY api_id, endpoint, status_code ORDER BY count DESC"
        return db.execute(query, params).fetchall()