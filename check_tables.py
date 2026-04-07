import sqlite3
db = sqlite3.connect('warehouse.db')
cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print("Tables count:", len(tables))

# Marketing tables
mkt_tables = [t for t in tables if t.startswith('marketing_')]
print(f"\nMarketing tables ({len(mkt_tables)}):")
for t in sorted(mkt_tables):
    print(f"  {t}")

# Check for marketing_roles and marketing_user_roles
if 'marketing_roles' in tables:
    print("\nmarketing_roles table found")
    cursor = db.execute("PRAGMA table_info(marketing_roles)")
    for col in cursor.fetchall():
        print(f"  {col}")
else:
    print("\nNo 'marketing_roles' table found")

if 'marketing_user_roles' in tables:
    print("\nmarketing_user_roles table found")
    cursor = db.execute("PRAGMA table_info(marketing_user_roles)")
    for col in cursor.fetchall():
        print(f"  {col}")
else:
    print("\nNo 'marketing_user_roles' table found")

# Check data in marketing_roles
if 'marketing_roles' in tables:
    print("\nMarketing roles data:")
    cursor = db.execute("SELECT id, role_name, role_code, is_system_role FROM marketing_roles")
    for row in cursor.fetchall():
        print(f"  {row}")

db.close()