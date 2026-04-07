import sqlite3

# Test the index query directly
conn = sqlite3.connect('warehouse.db')
conn.row_factory = sqlite3.Row

tables = ['companies', 'categories', 'brands', 'statuses', 'vitalities']
for table in tables:
    rows = conn.execute(f"SELECT * FROM {table} ORDER BY name").fetchall()
    print(f"{table}: {len(rows)} rows")
    if len(rows) > 0:
        print(f"  First row: {dict(rows[0]).keys()}")

conn.close()
print("\nDatabase queries work fine.")