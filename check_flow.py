import sqlite3

db = sqlite3.connect('warehouse.db')
db.row_factory = sqlite3.Row

tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
flow_tables = [t['name'] for t in tables if t['name'].startswith('flow')]
print('Flow tables:', flow_tables)

if 'flow_conversation_members' in flow_tables:
    cols = db.execute("PRAGMA table_info(flow_conversation_members)").fetchall()
    print('Members columns:', [c['name'] for c in cols])

if 'flow_conversations' in flow_tables:
    rows = db.execute("SELECT COUNT(*) as cnt FROM flow_conversations").fetchone()
    print('Conversations count:', rows['cnt'])

if 'flow_user_profiles' in flow_tables:
    rows = db.execute("SELECT COUNT(*) as cnt FROM flow_user_profiles").fetchone()
    print('Profiles count:', rows['cnt'])

users = db.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
print('Users count:', users['cnt'])

db.close()
