"""Quick check of key tables after seeding"""
import sqlite3
conn = sqlite3.connect('warehouse.db')
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('PRAGMA foreign_keys=ON')
conn.row_factory = sqlite3.Row

checks = [
    'projects', 'project_tasks', 'project_milestones', 'project_phases',
    'work_centers', 'work_center_capacity', 'work_center_shifts',
    'work_order_operations', 'work_order_components',
    'tm_talent_profiles', 'tm_competencies', 'tm_succession_plans',
    'spc_measurement_data', 'spc_capability_studies', 'spc_sampling_plans',
    'service_agreements', 'warranty_records', 'technician_shifts',
    'crm_customer_contacts', 'crm_lead_contacts',
    'quality_inspections', 'quality_non_conformances', 'quality_capa_records',
    'btp_ai_chats', 'btp_event_subscriptions'
]

for t in checks:
    try:
        count = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        status = "OK" if count > 0 else "EMPTY"
        print(f'  {t}: {count} [{status}]')
    except Exception as e:
        print(f'  {t}: ERROR - {e}')

conn.close()
