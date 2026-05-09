"""Seed the 4 stubborn tables with proper FK references"""
import sqlite3
import os
import random
from datetime import datetime, timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'warehouse.db')

conn = sqlite3.connect(DATABASE)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys=OFF")

def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# wms_stock_adjustment_lines - needs adjustment_id from wms_stock_adjustments
adj_ids = [r['id'] for r in conn.execute("SELECT id FROM wms_stock_adjustments LIMIT 5").fetchall()]
if adj_ids:
    for i, adj_id in enumerate(adj_ids[:3]):
        try:
            conn.execute("""INSERT INTO wms_stock_adjustment_lines
                (adjustment_id, line_number, item_id, location_id, system_quantity, counted_quantity,
                 adjusted_quantity, unit_cost, variance_value, reason_code, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (adj_id, i+1, 1, 1, 100.0, 95.0, -5.0, 10.0, -50.0, 'DAMAGE', 'PENDING'))
            print(f"+ wms_stock_adjustment_lines: 1 row")
        except Exception as e:
            print(f"  wms_stock_adjustment_lines error: {e}")

# workflow_instances - needs workflow_definition_id from workflow_definitions
wf_ids = [r['id'] for r in conn.execute("SELECT id FROM workflow_definitions LIMIT 5").fetchall()]
if wf_ids:
    for i, wf_id in enumerate(wf_ids[:3]):
        try:
            conn.execute("""INSERT INTO workflow_instances
                (workflow_definition_id, instance_code, source_module, current_state,
                 priority, company_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (wf_id, f'WFI-{random.randint(1000,9999)}', 'general',
                 'draft', 'medium', 1, now()))
            print(f"+ workflow_instances: 1 row")
        except Exception as e:
            print(f"  workflow_instances error: {e}")

# bi_approval_requests - needs request_type
try:
    conn.execute("""INSERT INTO bi_approval_requests
        (request_code, request_type, entity_type, entity_id, entity_name,
         requested_by_user_id, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (f'BI-AR-{random.randint(1000,9999)}', 'dataset_access', 'dataset',
         1, 'Test Dataset', 1, 'pending'))
    print(f"+ bi_approval_requests: 1 row")
except Exception as e:
    print(f"  bi_approval_requests error: {e}")

# form_submission_rows - needs submission_id from form_submissions and field_id from form_fields
sub_ids = [r['id'] for r in conn.execute("SELECT id FROM form_submissions LIMIT 5").fetchall()]
field_ids = [r['id'] for r in conn.execute("SELECT id FROM form_fields LIMIT 5").fetchall()]
if sub_ids and field_ids:
    for i, (sub_id, field_id) in enumerate(zip(sub_ids[:3], field_ids[:3])):
        try:
            conn.execute("""INSERT INTO form_submission_rows
                (submission_id, field_id, row_index, row_data, row_status)
                VALUES (?, ?, ?, ?, ?)""",
                (sub_id, field_id, i+1, '{}', 'active'))
            print(f"+ form_submission_rows: 1 row")
        except Exception as e:
            print(f"  form_submission_rows error: {e}")

conn.commit()
conn.close()
print("\nDone!")
