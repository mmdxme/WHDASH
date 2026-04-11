"""Seed workflow_instances table"""
import sqlite3
import os
import random
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'warehouse.db')

conn = sqlite3.connect(DATABASE)
conn.execute("PRAGMA foreign_keys=OFF")

def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# workflow_instances needs workflow_definition_id, source_entity_type, source_entity_id
wf_ids = [r[0] for r in conn.execute("SELECT id FROM workflow_definitions LIMIT 5").fetchall()]
if wf_ids:
    for i, wf_id in enumerate(wf_ids[:3]):
        try:
            conn.execute("""INSERT INTO workflow_instances
                (workflow_definition_id, instance_code, source_module, source_entity_type, source_entity_id,
                 current_state, priority, company_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (wf_id, f'WFI-{random.randint(10000,99999)}', 'general', 'request', 1,
                 'draft', 'medium', 1, now()))
            print(f"+ workflow_instances: inserted")
        except Exception as e:
            print(f"  workflow_instances error: {e}")

conn.commit()
conn.close()
print("Done!")
