import sqlite3
conn = sqlite3.connect('warehouse.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cur.fetchall() if 'marketing' in t[0].lower() or 'campaign' in t[0].lower()]
print('Marketing-related tables:', tables)
cur.execute("PRAGMA table_info(marketing_campaigns)")
cols = [c[1] for c in cur.fetchall()]
print('marketing_campaigns columns:', cols)
conn.close()
print('DB check done')