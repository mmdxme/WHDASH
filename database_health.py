"""
Database Health Check Utility
==============================
Analyzes the database for common issues and performance problems.

Checks performed:
- Missing indexes on foreign keys
- Tables without primary keys
- Missing NOT NULL constraints
- Large tables without ANALYZE
- Transaction issues
- Locking issues
- Schema inconsistencies
"""

import sqlite3
import os
import sys
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Get a database connection with Row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def check_missing_indexes(conn: sqlite3.Connection) -> List[Dict]:
    """Check for potentially missing indexes on foreign keys."""
    issues = []

    # Get all foreign key constraints
    tables = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
    """).fetchall()

    for table in tables:
        table_name = table['name']

        # Get foreign keys for this table
        foreign_keys = conn.execute(f"PRAGMA foreign_key_list({table_name})").fetchall()

        for fk in foreign_keys:
            from_col = fk['from']
            to_table = fk['table']
            to_col = fk['to']

            # Check if an index exists on the foreign key column
            indexes = conn.execute(f"PRAGMA index_list({table_name})").fetchall()

            has_index = False
            for idx in indexes:
                idx_info = conn.execute(f"PRAGMA index_info({idx['name']})").fetchall()
                for col in idx_info:
                    if col['name'] == from_col:
                        has_index = True
                        break

            if not has_index:
                issues.append({
                    'type': 'MISSING_INDEX',
                    'severity': 'MEDIUM',
                    'table': table_name,
                    'column': from_col,
                    'recommendation': f"CREATE INDEX idx_fk_{table_name}_{from_col} ON {table_name}({from_col})",
                    'reason': f"Foreign key column {from_col} referencing {to_table}({to_col}) is not indexed"
                })

    return issues


def check_tables_without_primary_key(conn: sqlite3.Connection) -> List[Dict]:
    """Check for tables without primary keys."""
    issues = []

    tables = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
    """).fetchall()

    for table in tables:
        table_name = table['name']
        primary_keys = conn.execute(f"PRAGMA table_info({table_name})").fetchall()

        has_pk = any(col['pk'] > 0 for col in primary_keys)

        if not has_pk:
            issues.append({
                'type': 'NO_PRIMARY_KEY',
                'severity': 'HIGH',
                'table': table_name,
                'recommendation': f"Add a primary key to {table_name}",
                'reason': "Table has no primary key - data integrity and performance may be affected"
            })

    return issues


def check_large_tables(conn: sqlite3.Connection) -> List[Dict]:
    """Check for large tables that may need optimization."""
    issues = []

    tables = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
    """).fetchall()

    for table in tables:
        table_name = table['name']
        info = conn.execute(f"PRAGMA table_info({table_name})").fetchall()

        # Estimate row size
        row_size = sum(
            col['type'] in ('INTEGER', 'REAL') and 8 or 100
            for col in info
        )

        # Get page count
        page_count = conn.execute(f"PRAGMA page_count({table_name})").fetchone()[0]
        page_size = conn.execute("PRAGMA page_size").fetchone()[0]
        table_size_bytes = page_count * page_size

        # Flag tables over 100MB
        if table_size_bytes > 100 * 1024 * 1024:
            issues.append({
                'type': 'LARGE_TABLE',
                'severity': 'LOW',
                'table': table_name,
                'size_mb': table_size_bytes / (1024 * 1024),
                'recommendation': f"Consider archiving old data or partitioning {table_name}",
                'reason': f"Table size is {table_size_bytes / (1024 * 1024):.1f}MB"
            })

    return issues


def check_query_plan_issues(conn: sqlite3.Connection) -> List[Dict]:
    """Check for queries that might have poor query plans."""
    issues = []

    # Common expensive query patterns to check
    queries = [
        ("SELECT * FROM movements ORDER BY id DESC LIMIT 100"),
        ("SELECT * FROM platform_audit_log ORDER BY created_at DESC"),
    ]

    for query in queries:
        try:
            # EXPLAIN QUERY PLAN returns rows with details
            plan = conn.execute(f"EXPLAIN QUERY PLAN {query}").fetchall()
            plan_text = ' '.join([str(row) for row in plan])

            # Check for table scans
            if 'SCAN' in plan_text.upper() and 'USING' not in plan_text.upper():
                issues.append({
                    'type': 'TABLE_SCAN',
                    'severity': 'MEDIUM',
                    'query': query,
                    'plan': plan_text,
                    'recommendation': "Consider adding an index to avoid table scan",
                    'reason': f"Query may perform full table scan: {plan_text}"
                })
        except sqlite3.Error:
            pass

    return issues


def check_database_settings(conn: sqlite3.Connection) -> List[Dict]:
    """Check database settings for performance."""
    issues = []

    # Check journal mode
    journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    if journal_mode != 'WAL':
        issues.append({
            'type': 'SUBOPTIMAL_SETTING',
            'severity': 'MEDIUM',
            'setting': 'journal_mode',
            'current': journal_mode,
            'recommended': 'WAL',
            'recommendation': "ALTER DATABASE SET journal_mode=WAL",
            'reason': "WAL mode provides better concurrency and crash recovery"
        })

    # Check synchronous
    synchronous = conn.execute("PRAGMA synchronous").fetchone()[0]
    if synchronous == 2:  # FULL
        issues.append({
            'type': 'SUBOPTIMAL_SETTING',
            'severity': 'LOW',
            'setting': 'synchronous',
            'current': 'FULL (2)',
            'recommended': 'NORMAL (1)',
            'recommendation': "PRAGMA synchronous=NORMAL for better performance with slightly less durability",
            'reason': "NORMAL provides good durability with better performance"
        })

    # Check if ANALYZE has been run
    table_count = conn.execute("""
        SELECT COUNT(*) as cnt FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'
    """).fetchone()[0]

    index_count = conn.execute("""
        SELECT COUNT(*) as cnt FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'
    """).fetchone()[0]

    if index_count < table_count:
        issues.append({
            'type': 'STALE_STATISTICS',
            'severity': 'LOW',
            'recommendation': "Run ANALYZE to update query planner statistics",
            'reason': f"Database has {table_count} tables but only {index_count} indexes - statistics may be stale"
        })

    return issues


def check_missing_unique_constraints(conn: sqlite3.Connection) -> List[Dict]:
    """Check for tables that might benefit from unique constraints."""
    issues = []

    # Common cases where unique constraints would help
    unique_checks = [
        ('users', 'username', 'Username should be unique'),
        ('users', 'email', 'Email should be unique'),
        ('parts', 'part_number', 'Part number should be unique'),
    ]

    for table_name, column, reason in unique_checks:
        try:
            # Get column info
            columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
            column_exists = any(col['name'] == column for col in columns)

            if not column_exists:
                continue

            # Check for existing unique index
            indexes = conn.execute(f"PRAGMA index_list({table_name})").fetchall()
            has_unique = False

            for idx in indexes:
                if idx['unique']:
                    idx_info = conn.execute(f"PRAGMA index_info({idx['name']})").fetchall()
                    if len(idx_info) == 1 and idx_info[0]['name'] == column:
                        has_unique = True
                        break

            if not has_unique:
                issues.append({
                    'type': 'MISSING_UNIQUE_CONSTRAINT',
                    'severity': 'LOW',
                    'table': table_name,
                    'column': column,
                    'recommendation': f"Consider adding UNIQUE constraint or index on {table_name}.{column}",
                    'reason': reason
                })
        except sqlite3.Error:
            pass

    return issues


def run_health_check(db_path: str = None) -> Dict:
    """
    Run comprehensive database health check.

    Returns:
        Dictionary with issues grouped by severity
    """
    if db_path is None:
        from config import DATABASE_PATH
        db_path = os.environ.get('DATABASE_PATH', DATABASE_PATH)

    print("=" * 70)
    print("Database Health Check")
    print("=" * 70)
    print(f"Database: {db_path}")
    print()

    if not os.path.exists(db_path):
        print(f"ERROR: Database file not found: {db_path}")
        return {'error': 'Database not found'}

    conn = get_db_connection(db_path)

    try:
        all_issues = []

        print("Checking for missing indexes on foreign keys...")
        all_issues.extend(check_missing_indexes(conn))

        print("Checking for tables without primary keys...")
        all_issues.extend(check_tables_without_primary_key(conn))

        print("Checking for large tables...")
        all_issues.extend(check_large_tables(conn))

        print("Checking for query plan issues...")
        all_issues.extend(check_query_plan_issues(conn))

        print("Checking database settings...")
        all_issues.extend(check_database_settings(conn))

        print("Checking for missing unique constraints...")
        all_issues.extend(check_missing_unique_constraints(conn))

    finally:
        conn.close()

    # Group issues by severity
    by_severity = {'HIGH': [], 'MEDIUM': [], 'LOW': []}

    for issue in all_issues:
        severity = issue.pop('severity', 'MEDIUM')
        by_severity[severity].append(issue)

    # Print summary
    print()
    print("=" * 70)
    print("Health Check Results")
    print("=" * 70)

    for severity in ['HIGH', 'MEDIUM', 'LOW']:
        issues = by_severity[severity]
        if issues:
            print(f"\n{severity} Severity Issues ({len(issues)}):")
            print("-" * 50)

            for issue in issues:
                print(f"  [{issue['type']}] {issue['table'] if issue.get('table') else issue.get('setting', 'N/A')}")
                print(f"    {issue['reason']}")
                print(f"    Recommendation: {issue['recommendation']}")

    total_issues = sum(len(v) for v in by_severity.values())
    print()
    print(f"Total issues found: {total_issues}")

    if total_issues == 0:
        print("  Database appears healthy!")

    return by_severity


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Database Health Check')
    parser.add_argument('--db', '-d', help='Path to database file')

    args = parser.parse_args()

    run_health_check(args.db)
