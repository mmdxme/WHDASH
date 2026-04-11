"""
API Gateway Demo Data Seeder
Seeds realistic demo data for testing the API Gateway module.
"""

import sqlite3
import random
import hashlib
from datetime import datetime, timedelta
import secrets

DATABASE = 'warehouse.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_api_key(api_key):
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()

def seed():
    """Seed API Gateway demo data."""
    print("Seeding API Gateway demo data...")
    
    conn = get_db()
    c = conn.cursor()
    
    # Ensure tables exist first
    try:
        from api_gateway_models import init_api_gateway_tables
        init_api_gateway_tables()
        print("API Gateway tables initialized.")
    except Exception as e:
        print(f"Note: Tables may already exist - {e}")
    
    # Seed Integration Profiles
    integrations = [
        {
            'integration_code': 'INT-ECOM-001',
            'integration_name': 'E-Commerce Sync',
            'integration_type': 'ecommerce',
            'module': 'sales',
            'direction': 'bidirectional',
            'module_scope': 'sales, inventory',
            'description': 'Sync orders and inventory with Shopify store',
            'connection_config': '{"shop_url": "https://example.myshopify.com", "api_version": "2024-01"}',
            'sync_schedule': '*/15 * * * *',
            'is_active': 1,
            'last_run_status': 'success',
        },
        {
            'integration_code': 'INT-ACC-001',
            'integration_name': 'Accounting System Integration',
            'integration_type': 'accounting',
            'module': 'finance',
            'direction': 'outbound',
            'module_scope': 'finance',
            'description': 'Push journal entries to QuickBooks Online',
            'connection_config': '{"company_id": "qb-12345", "environment": "production"}',
            'sync_schedule': '0 */2 * * *',
            'is_active': 1,
            'last_run_status': 'success',
        },
        {
            'integration_code': 'INT-SHIP-001',
            'integration_name': 'Shipping Provider Integration',
            'integration_type': 'shipping',
            'module': 'logistics',
            'direction': 'outbound',
            'module_scope': 'logistics',
            'description': 'FedEx shipping label generation and tracking',
            'connection_config': '{"account_number": "FEDEX123", "environment": "production"}',
            'sync_schedule': '0 * * * *',
            'is_active': 0,
            'last_run_status': 'failed',
        },
    ]
    
    int_count = 0
    for integration in integrations:
        existing = c.execute("""
            SELECT id FROM integration_profiles WHERE integration_code = ?
        """, (integration['integration_code'],)).fetchone()
        
        if existing:
            continue
            
        c.execute("""
            INSERT INTO integration_profiles (integration_code, integration_name, integration_type,
                                              module, direction, module_scope, description,
                                              connection_config, sync_schedule, is_active,
                                              last_run_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (integration['integration_code'], integration['integration_name'], integration['integration_type'],
              integration['module'], integration['direction'], integration['module_scope'], integration['description'],
              integration['connection_config'], integration['sync_schedule'], integration['is_active'],
              integration['last_run_status'], datetime.now().isoformat()))
        int_count += 1
    
    print(f"Seeded {int_count} integration profiles")
    
    # Seed Integration Runs
    integration_run_count = 0
    base_time = datetime.now() - timedelta(days=7)
    
    for integration in integrations:
        profile_rec = c.execute("""
            SELECT id, integration_code, direction FROM integration_profiles WHERE integration_code = ?
        """, (integration['integration_code'],)).fetchone()
        
        if not profile_rec:
            continue
        
        for i in range(20):
            status = random.choices(
                ['success', 'failed', 'running'],
                weights=[15, 3, 2]
            )[0]
            started_at = base_time + timedelta(hours=random.randint(0, 168))
            duration = random.uniform(1.5, 120.0)
            
            c.execute("""
                INSERT INTO integration_runs (run_id, integration_id, integration_code,
                                            run_type, direction, status,
                                            records_processed, records_success, records_failed,
                                            execution_time_ms, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (secrets.token_hex(16), profile_rec['id'], profile_rec['integration_code'],
                  'scheduled', profile_rec['direction'], status,
                  random.randint(10, 500) if status == 'success' else 0,
                  random.randint(10, 500) if status == 'success' else 0,
                  random.randint(1, 10) if status == 'failed' else 0,
                  int(duration * 1000),
                  started_at.isoformat(),
                  (started_at + timedelta(seconds=duration)).isoformat() if status != 'running' else None))
            integration_run_count += 1
    
    print(f"Seeded {integration_run_count} integration runs")
    
    # Seed Webhook Deliveries
    events = [
        'order.created', 'order.updated', 'inventory.updated',
        'customer.created', 'invoice.posted', 'payment.received',
    ]
    
    sub_ids = [row['id'] for row in c.execute("SELECT id FROM webhook_subscriptions").fetchall()]
    
    delivery_count = 0
    for sub_id in sub_ids:
        for i in range(30):
            event_code = random.choice(events)
            delivery_status = random.choices(
                ['delivered', 'failed', 'pending', 'retrying'],
                weights=[25, 3, 1, 1]
            )[0]
            attempt = 1 if delivery_status == 'delivered' else random.randint(1, 4)
            created_at = base_time + timedelta(hours=random.randint(0, 168))
            
            c.execute("""
                INSERT INTO webhook_deliveries (delivery_id, event_code, subscription_id,
                                               delivery_status, attempt_number,
                                               http_status_code, response_body_preview,
                                               response_time_ms, created_at, delivered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (secrets.token_hex(16), event_code, sub_id,
                  delivery_status, attempt, 200 if delivery_status == 'delivered' else random.choice([500, 502, 503, 408]),
                  'OK' if delivery_status == 'delivered' else 'Internal Server Error',
                  random.randint(50, 5000),
                  created_at.isoformat(),
                  created_at.isoformat() if delivery_status == 'delivered' else None))
            delivery_count += 1
    
    print(f"Seeded {delivery_count} webhook deliveries")
    
    conn.commit()
    conn.close()
    
    print("API Gateway demo data seeding complete!")
    print("\nTest API Keys (use these with the /api/v1/* endpoints):")
    print("  POS System:   sk_live_pos_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6")
    print("  E-Commerce:  sk_live_ecom_k1l2m3n4o5p6q7r8s9t0u1v2w3x4")
    print("  Partner:      sk_live_part_x1y2z3a4b5c6d7e8f9g0h1i2j3")
    print("  BI Suite:     sk_live_bi_d1e2f3g4h5i6j7k8l9m0n1o2p3q4")
    print("  Mobile App:   sk_live_mob_r1s2t3u4v5w6x7y8z9a0b1c2d3e4")

if __name__ == '__main__':
    seed()
