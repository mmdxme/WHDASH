import sqlite3
conn = sqlite3.connect('warehouse.db')
cur = conn.cursor()

tables = ['companies', 'categories', 'brands', 'statuses', 'vitalities']
for table in tables:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = cur.fetchone()[0]
    print(f"{table}: {count} rows")

# Check if users exist
cur.execute("SELECT COUNT(*) FROM users")
print(f"users: {cur.fetchone()[0]} rows")

# Check if roles exist
cur.execute("SELECT COUNT(*) FROM roles")
print(f"roles: {cur.fetchone()[0]} rows")