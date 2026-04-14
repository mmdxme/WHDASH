"""
Base Repository
===============
Base class for all data repositories providing common query patterns.

This provides:
- Standardized database access
- Query builder helpers
- Transaction management
- Error handling
"""

from typing import Optional, List, Dict, Any, Callable
from contextlib import contextmanager


class BaseRepository:
    """
    Base repository class with common database operations.
    All specific repositories should inherit from this class.
    """

    def __init__(self, get_db_func):
        """
        Initialize repository with database connection factory.

        Args:
            get_db_func: Function that returns a database connection
        """
        self.get_db = get_db_func

    @contextmanager
    def get_connection(self):
        """
        Get a database connection as a context manager.
        Automatically handles commit/rollback and cleanup.
        """
        db = self.get_db()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def get_one(self, sql: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """
        Execute a query and return a single row as dictionary.

        Args:
            sql: SQL query with placeholders
            params: Query parameters

        Returns:
            Dictionary of row data or None
        """
        with self.get_connection() as db:
            cursor = db.execute(sql, params) if params else db.execute(sql)
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        Execute a query and return all rows as list of dictionaries.

        Args:
            sql: SQL query with placeholders
            params: Query parameters

        Returns:
            List of row dictionaries
        """
        with self.get_connection() as db:
            cursor = db.execute(sql, params) if params else db.execute(sql)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def execute(self, sql: str, params: tuple = None) -> int:
        """
        Execute a SQL statement and return rows affected.

        Args:
            sql: SQL statement with placeholders
            params: Statement parameters

        Returns:
            Number of rows affected
        """
        with self.get_connection() as db:
            cursor = db.execute(sql, params) if params else db.execute(sql)
            return cursor.rowcount

    def execute_many(self, sql: str, params_list: List[tuple]) -> int:
        """
        Execute a SQL statement for multiple parameter sets.

        Args:
            sql: SQL statement with placeholders
            params_list: List of parameter tuples

        Returns:
            Number of rows affected
        """
        with self.get_connection() as db:
            cursor = db.executemany(sql, params_list)
            return cursor.rowcount

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        Insert a row into a table.

        Args:
            table: Table name
            data: Dictionary of column:value pairs

        Returns:
            ID of inserted row
        """
        columns = list(data.keys())
        placeholders = ','.join(['?' for _ in columns])
        sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
        params = tuple(data[c] for c in columns)

        with self.get_connection() as db:
            cursor = db.execute(sql, params)
            return cursor.lastrowid

    def update(self, table: str, data: Dict[str, Any], where: str, where_params: tuple) -> int:
        """
        Update rows in a table.

        Args:
            table: Table name
            data: Dictionary of column:value pairs to update
            where: WHERE clause string
            where_params: Parameters for WHERE clause

        Returns:
            Number of rows affected
        """
        set_clause = ','.join([f"{k} = ?" for k in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
        params = tuple(data.values()) + where_params

        with self.get_connection() as db:
            cursor = db.execute(sql, params)
            return cursor.rowcount

    def delete(self, table: str, where: str, where_params: tuple) -> int:
        """
        Delete rows from a table.

        Args:
            table: Table name
            where: WHERE clause string
            where_params: Parameters for WHERE clause

        Returns:
            Number of rows deleted
        """
        sql = f"DELETE FROM {table} WHERE {where}"

        with self.get_connection() as db:
            cursor = db.execute(sql, where_params)
            return cursor.rowcount

    def exists(self, table: str, where: str, where_params: tuple) -> bool:
        """
        Check if a row exists in a table.

        Args:
            table: Table name
            where: WHERE clause string
            where_params: Parameters for WHERE clause

        Returns:
            True if row exists
        """
        sql = f"SELECT 1 FROM {table} WHERE {where} LIMIT 1"
        result = self.get_one(sql, where_params)
        return result is not None

    def count(self, table: str, where: str = "1=1", where_params: tuple = None) -> int:
        """
        Count rows in a table.

        Args:
            table: Table name
            where: WHERE clause string
            where_params: Parameters for WHERE clause

        Returns:
            Count of matching rows
        """
        sql = f"SELECT COUNT(*) as cnt FROM {table} WHERE {where}"
        result = self.get_one(sql, where_params)
        return result['cnt'] if result else 0

    def paginate(self, sql: str, page: int = 1, per_page: int = 50,
                 params: tuple = None) -> Dict[str, Any]:
        """
        Execute a paginated query.

        Args:
            sql: SQL query (should include ORDER BY)
            page: Page number (1-indexed)
            per_page: Items per page
            params: Query parameters

        Returns:
            Dictionary with items, total, page, per_page, pages
        """
        # Get total count
        count_sql = sql.strip()
        if count_sql.upper().startswith('SELECT'):
            # Remove ORDER BY for count query
            count_sql = re.sub(r'ORDER BY.*$', '', count_sql, flags=re.IGNORECASE | re.DOTALL)
            count_sql = f"SELECT COUNT(*) as cnt FROM ({count_sql}) as subq"

        total = self.get_one(count_sql, params)
        total = total['cnt'] if total else 0

        # Get page items
        offset = (page - 1) * per_page
        paginated_sql = f"{sql} LIMIT {per_page} OFFSET {offset}"

        items = self.get_all(paginated_sql, params)

        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page if per_page > 0 else 0,
        }


# Need to import re for the paginate method
import re
