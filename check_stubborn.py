"""Check stubborn tables"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'warehouse.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

stubborn_tables = [
    'wms_stock_adjustment_lines',
    'workflow_instances',
    'bi_approval_requests',
    'form_submission_rows'
]

for table in stubborn_tables:
    print(f"\n{'='*60}")
    print(f"TABLE: {table}")
    print('='*60)
    
    # Get columns
    cursor.execute(f"PRAGMA table_info([{table}])")
    cols = cursor.fetchall()
    print(f"Columns ({len(cols)}):")
    for col in cols:
        print(f"  {col[1]} ({col[2]}) default={col[4]}")
    
    # Check foreign keys
    cursor.execute(f"PRAGMA foreign_key_list([{table}])")
    fks = cursor.fetchall()
    if fks:
        print(f"Foreign Keys:")
        for fk in fks:
            print(f"  {fk}")
    else:
        print("Foreign Keys: None")
    
    # Try insert with NULLs
    col_names = [c[1] for c in cols]
    null_data = {c: None for c in col_names if c != 'id'}
    if null_data:
        placeholders = ', '.join(['?'] * len(null_data))
        col_names_str = ', '.join(null_data.keys())
        try:
            cursor.execute(f"INSERT INTO [{table}] ({col_names_str}) VALUES ({placeholders})",
                         list(null_data.values()))
            conn.commit()
            print(f"Inserted with NULLs: SUCCESS")
        except Exception as e:
            print(f"Inserted with NULLs: FAILED - {e}")
    
    # Count
    count = cursor.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
    print(f"Row count: {count}")

conn.close()
