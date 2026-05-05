"""Debug seed scripts - check FK constraints"""
import sqlite3
conn = sqlite3.connect('warehouse.db')
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('PRAGMA foreign_keys=ON')
conn.row_factory = sqlite3.Row

# Check foreign keys on key tables
tables = ['projects', 'work_centers', 'tm_talent_profiles', 'spc_measurement_data',
          'project_tasks', 'project_milestones', 'project_phases']
for t in tables:
    fks = conn.execute(f"PRAGMA foreign_key_list([{t}])").fetchall()
    print(f"\n{t} foreign keys:")
    for fk in fks:
        print(f"  {fk[3]} -> {fk[2]}")

# Check project_types table
print("\nproject_types:")
try:
    rows = conn.execute("SELECT * FROM project_types LIMIT 5").fetchall()
    print(f"  Has {len(rows)} rows")
    if rows:
        print(f"  Columns: {rows[0].keys()}")
        print(f"  Sample: {dict(rows[0])}")
except Exception as e:
    print(f"  Error: {e}")

# Check hr_employees count
print("\nhr_employees:")
try:
    count = conn.execute("SELECT COUNT(*) FROM hr_employees").fetchone()[0]
    print(f"  Has {count} rows")
    if count > 0:
        row = conn.execute("SELECT id FROM hr_employees LIMIT 3").fetchall()
        print(f"  Sample IDs: {[r['id'] for r in row]}")
except Exception as e:
    print(f"  Error: {e}")

# Check spc_control_charts count
print("\nspc_control_charts:")
try:
    count = conn.execute("SELECT COUNT(*) FROM spc_control_charts").fetchone()[0]
    print(f"  Has {count} rows")
    if count > 0:
        row = conn.execute("SELECT id FROM spc_control_charts LIMIT 3").fetchall()
        print(f"  Sample IDs: {[r['id'] for r in row]}")
except Exception as e:
    print(f"  Error: {e}")

# Check spc_measurement_data columns
print("\nspc_measurement_data columns:")
try:
    cols = conn.execute("PRAGMA table_info([spc_measurement_data])").fetchall()
    for c in cols:
        print(f"  {c[1]}: {c[2]}")
except Exception as e:
    print(f"  Error: {e}")

conn.close()