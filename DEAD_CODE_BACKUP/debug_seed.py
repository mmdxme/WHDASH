"""Debug seeding - check if tables exist and try a direct insert"""
import sqlite3
conn = sqlite3.connect('warehouse.db')
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('PRAGMA foreign_keys=ON')
conn.row_factory = sqlite3.Row

# Check if tables exist
tables_to_check = ['projects', 'work_centers', 'tm_talent_profiles', 'spc_measurement_data', 'service_agreements']
for t in tables_to_check:
    result = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (t,)
    ).fetchone()
    print(f"Table '{t}' exists: {result is not None}")
    if result:
        # Check columns
        cols = conn.execute(f"PRAGMA table_info([{t}])").fetchall()
        print(f"  Columns: {[c[1] for c in cols][:5]}...")
        # Try a direct insert
        try:
            if 'id' in [c[1] for c in cols]:
                all_cols = [c[1] for c in cols]
                placeholders = ','.join(['?'] * len(all_cols))
                # Use default values for all non-id columns
                vals = []
                for c in all_cols:
                    if c == 'id':
                        vals.append(None)
                    elif 'date' in c.lower() or 'at' in c.lower():
                        vals.append('2025-01-01 00:00:00')
                    elif 'amount' in c.lower() or 'price' in c.lower() or 'cost' in c.lower():
                        vals.append(100.0)
                    elif 'qty' in c.lower() or 'quantity' in c.lower():
                        vals.append(10)
                    elif 'is_' in c.lower() or 'status' in c.lower():
                        vals.append('Active')
                    else:
                        vals.append(f'test_{c}')
                conn.execute(f"INSERT INTO {t} ({','.join(all_cols)}) VALUES ({placeholders})", vals)
                conn.commit()
                count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                print(f"  Direct insert succeeded, count now: {count}")
        except Exception as e:
            print(f"  Direct insert failed: {e}")

conn.close()