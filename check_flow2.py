import sqlite3
from datetime import datetime

db = sqlite3.connect('warehouse.db')
db.row_factory = sqlite3.Row

# Simulate get_conversation_id_for_users(1, 6)
user1, user2 = sorted([1, 6])
result = db.execute('''
    SELECT fc.id
    FROM flow_conversations fc
    JOIN flow_conversation_members fcm1 ON fc.id = fcm1.conversation_id AND fcm1.user_id = ?
    JOIN flow_conversation_members fcm2 ON fc.id = fcm2.conversation_id AND fcm2.user_id = ?
    WHERE fc.conversation_type = 'private'
    AND (SELECT COUNT(*) FROM flow_conversation_members WHERE conversation_id = fc.id) = 2
''', (user1, user2)).fetchone()
print('Existing conv:', dict(result) if result else None)

# Check flow_conversations schema
cols = db.execute("PRAGMA table_info(flow_conversations)").fetchall()
print('Conversations columns:', [c['name'] for c in cols])

# Test a simple insert
import uuid
conv_id = str(uuid.uuid4()).replace('-', '')[:32]
now = datetime.now().isoformat()
try:
    db.execute("INSERT INTO flow_conversations (id, conversation_type, created_by, last_message_at) VALUES (?, 'private', ?, ?)", (conv_id, 1, now))
    db.execute("INSERT INTO flow_conversation_members (conversation_id, user_id, role, last_read_at) VALUES (?, ?, 'member', ?)", (conv_id, 1, now))
    db.execute("INSERT INTO flow_conversation_members (conversation_id, user_id, role, last_read_at) VALUES (?, ?, 'member', ?)", (conv_id, 6, now))
    db.rollback()
    print('Create test: OK (rolled back)')
except Exception as e:
    print('Create error:', e)
    import traceback
    traceback.print_exc()

db.close()
