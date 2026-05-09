"""
Integration / Middleware Module - Seed Data
==========================================
Realistic sample data for the Integration module.
This provides operational-looking data across all integration entities.

Author: Enterprise Architecture Team
Version: 1.0.0
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
import random


def get_integration_db():
    """Get database connection."""
    from database import get_db
    return get_db()


def seed_integration_data():
    """Seed all integration tables with realistic sample data."""
    conn = get_integration_db()
    cursor = conn.cursor()
    
    seed_connectors(cursor)
    seed_flows(cursor)
    seed_endpoints(cursor)
    seed_webhooks(cursor)
    seed_events(cursor)
    seed_queue_items(cursor)
    seed_dlq_items(cursor)
    seed_schedules(cursor)
    seed_job_runs(cursor)
    seed_credentials(cursor)
    seed_mappings(cursor)
    seed_transformations(cursor)
    seed_alert_rules(cursor)
    seed_reconciliation_batches(cursor)
    seed_file_exchange(cursor)
    seed_usage_metrics(cursor)
    
    conn.commit()
    print("[Integration Module] Sample data seeded successfully")


def seed_connectors(cursor):
    """Seed sample connectors."""
    connectors = [
        ('SHOPIFY_PROD', 'Shopify Production', 'shopify', 'ecommerce', 'bidirectional', 'oauth2',
         'Active Shopify store connection for order sync and inventory updates', 'active', 'healthy', 'success',
         datetime.now() - timedelta(hours=2), None, datetime.now() - timedelta(days=1)),
        
        ('QUICKBOOKS_API', 'QuickBooks Online', 'accounting', 'finance', 'bidirectional', 'oauth2',
         'Accounting system integration for GL entries and invoice sync', 'active', 'healthy', 'success',
         datetime.now() - timedelta(hours=1), None, datetime.now() - timedelta(hours=4)),
        
        ('SFTP_SUPPLIERS', 'Supplier SFTP Portal', 'sftp', 'procurement', 'outbound', 'ssh_key',
         'SFTP connection to supplier portal for PO and ASN exchange', 'active', 'healthy', 'success',
         datetime.now() - timedelta(minutes=30), None, datetime.now() - timedelta(days=2)),
        
        ('WMS_REST', 'Warehouse Management API', 'rest_api', 'warehouse', 'bidirectional', 'api_key',
         'WMS REST API for inventory levels and shipment status', 'active', 'unhealthy', 'failed',
         datetime.now() - timedelta(days=1), datetime.now() - timedelta(hours=6), datetime.now() - timedelta(hours=6)),
        
        ('DHL_CARRIER', 'DHL Express API', 'logistics', 'logistics', 'outbound', 'api_key',
         'DHL shipping rates and label generation API', 'active', 'healthy', 'success',
         datetime.now() - timedelta(minutes=15), None, datetime.now() - timedelta(days=3)),
        
        ('HR_WORKDAY', 'Workday HR System', 'rest_api', 'hr', 'inbound', 'oauth2',
         'Employee master data sync from Workday', 'active', 'healthy', 'success',
         datetime.now() - timedelta(hours=4), None, datetime.now() - timedelta(days=5)),
        
        ('CRM_SALESFORCE', 'Salesforce CRM', 'crm', 'sales', 'bidirectional', 'oauth2',
         'Salesforce opportunity and account sync', 'active', 'healthy', 'success',
         datetime.now() - timedelta(hours=3), None, datetime.now() - timedelta(hours=12)),
        
        ('MARKETING_MAILCHIMP', 'Mailchimp Email', 'email_outbound', 'marketing', 'outbound', 'api_key',
         'Email campaign subscriber sync and engagement events', 'active', 'healthy', 'success',
         datetime.now() - timedelta(hours=6), None, datetime.now() - timedelta(days=1)),
        
        ('INTERNAL_SAP', 'SAP ERP (Internal)', 'internal_module', 'finance', 'bidirectional', 'internal',
         'Internal SAP integration for financial documents', 'active', 'healthy', 'success',
         datetime.now() - timedelta(minutes=5), None, datetime.now() - timedelta(hours=2)),
        
        ('SHOPIFY_STAGING', 'Shopify Staging', 'shopify', 'ecommerce', 'bidirectional', 'oauth2',
         'Staging Shopify store for testing', 'inactive', 'unknown', 'untested',
         None, None, None),
    ]
    
    for conn_data in connectors:
        cursor.execute("""
            INSERT OR IGNORE INTO integration_connectors 
            (code, name, connector_type, owner_module, direction, auth_method, description,
             active_status, health_status, test_status, last_success_at, last_failure_at, last_tested_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, conn_data)


def seed_flows(cursor):
    """Seed sample integration flows."""
    flows = [
        ('FLOW-ORD-001', 'Shopify Order to Sales Order', 'shopify', 'sales', 'webhook', 'inbound', 'orders',
         'Syncs incoming Shopify orders to internal sales order system', 'published', 1),
        
        ('FLOW-INV-001', 'Inventory Level Sync', 'wms', 'ecommerce', 'scheduled', 'outbound', 'inventory',
         'Pushes warehouse inventory levels to e-commerce platforms', 'published', 2),
        
        ('FLOW-GL-001', 'GL Entry Creation', 'ecommerce', 'finance', 'event', 'outbound', 'transactions',
         'Creates GL entries from e-commerce transactions', 'published', 1),
        
        ('FLOW-SHIP-001', 'Shipment Status Update', 'logistics', 'ecommerce', 'api_polling', 'inbound', 'shipments',
         'Polls carrier APIs for shipment status updates', 'published', 3),
        
        ('FLOW-EMP-001', 'Employee Master Sync', 'hr', 'hr', 'scheduled', 'inbound', 'employees',
         'Syncs employee data from Workday to internal systems', 'draft', 1),
        
        ('FLOW-PO-001', 'PO Export to Supplier', 'procurement', 'supplier', 'scheduled', 'outbound', 'purchase_orders',
         'Exports approved POs to supplier SFTP portal', 'published', 1),
        
        ('FLOW-CUST-001', 'Customer Credit Sync', 'finance', 'crm', 'scheduled', 'bidirectional', 'customers',
         'Syncs customer credit limits between Finance and CRM', 'archived', 1),
        
        ('FLOW-MARKET-001', 'Email Subscriber Sync', 'ecommerce', 'marketing', 'event', 'outbound', 'customers',
         'Syncs new customers to Mailchimp for email marketing', 'published', 2),
        
        ('FLOW-RATES-001', 'Shipping Rates Calculation', 'logistics', 'ecommerce', 'api', 'outbound', 'shipping',
         'Fetches real-time shipping rates from carriers', 'published', 1),
        
        ('FLOW-ASN-001', 'ASN Import from Suppliers', 'supplier', 'warehouse', 'file', 'inbound', 'shipments',
         'Imports ASN files from supplier SFTP for receiving', 'draft', 1),
    ]
    
    for flow_data in flows:
        cursor.execute("""
            INSERT OR IGNORE INTO integration_flows 
            (code, name, source_system, destination_system, trigger_type, direction, data_entity,
             description, flow_status, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, flow_data)


def seed_endpoints(cursor):
    """Seed sample API endpoints."""
    endpoints = [
        ('EP-ORD-001', 'Get Orders', 'inbound', 'GET', '/api/v1/orders', 'bearer_token',
         'sales', 'Retrieve orders by status or date range', 'active', 1500, 5, 'healthy', datetime.now() - timedelta(hours=1)),
        
        ('EP-ORD-002', 'Create Order', 'inbound', 'POST', '/api/v1/orders', 'bearer_token',
         'sales', 'Create a new sales order', 'active', 800, 3, 'healthy', datetime.now() - timedelta(hours=2)),
        
        ('EP-INV-001', 'Get Inventory Levels', 'inbound', 'GET', '/api/v1/inventory', 'api_key',
         'warehouse', 'Get current inventory by SKU', 'active', 3000, 10, 'healthy', datetime.now() - timedelta(minutes=30)),
        
        ('EP-SHIP-001', 'Get Shipping Rates', 'outbound', 'POST', '/api/v1/shipping/rates', 'bearer_token',
         'logistics', 'Request shipping rate quotes', 'active', 1200, 8, 'healthy', datetime.now() - timedelta(hours=3)),
        
        ('EP-SHIP-002', 'Create Shipment Label', 'outbound', 'POST', '/api/v1/shipping/labels', 'bearer_token',
         'logistics', 'Generate shipping label', 'active', 600, 2, 'healthy', datetime.now() - timedelta(hours=1)),
        
        ('EP-CUST-001', 'Get Customers', 'inbound', 'GET', '/api/v1/customers', 'bearer_token',
         'crm', 'Retrieve customer records', 'active', 900, 4, 'healthy', datetime.now() - timedelta(hours=4)),
        
        ('EP-GL-001', 'Post GL Entry', 'outbound', 'POST', '/api/v1/gl/entries', 'oauth2',
         'finance', 'Create general ledger entry', 'active', 450, 1, 'healthy', datetime.now() - timedelta(hours=2)),
        
        ('EP-PO-001', 'Get Purchase Orders', 'inbound', 'GET', '/api/v1/purchase-orders', 'api_key',
         'procurement', 'Retrieve purchase orders', 'active', 300, 2, 'unhealthy', datetime.now() - timedelta(days=1)),
    ]
    
    for ep_data in endpoints:
        cursor.execute("""
            INSERT OR IGNORE INTO integration_endpoints 
            (code, name, endpoint_type, http_method, url_path, auth_type, endpoint_group,
             description, active_status, usage_count, error_count, health_check_result, last_health_check)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ep_data)


def seed_webhooks(cursor):
    """Seed sample webhooks."""
    webhooks = [
        ('WH-ORD-001', 'Shopify Order Created', 'order.created', 'ecommerce', 'https://internal.api/webhook/shopify/order',
         'POST', 'hmac_sha256', 'Webhook for new Shopify orders', 'active', 'healthy', 1, 4500, 4450, 50,
         datetime.now() - timedelta(hours=1), None),
        
        ('WH-ORD-002', 'Shopify Order Paid', 'order.paid', 'ecommerce', 'https://internal.api/webhook/shopify/paid',
         'POST', 'hmac_sha256', 'Webhook for paid orders', 'active', 'healthy', 1, 3200, 3180, 20,
         datetime.now() - timedelta(hours=2), None),
        
        ('WH-INV-001', 'Inventory Updated', 'inventory.updated', 'warehouse', 'https://internal.api/webhook/wms/inventory',
         'POST', 'api_key', 'Webhook for inventory level changes', 'active', 'healthy', 1, 8500, 8450, 50,
         datetime.now() - timedelta(minutes=30), None),
        
        ('WH-SHIP-001', 'Shipment Delivered', 'shipment.delivered', 'logistics', 'https://internal.api/webhook/carrier/delivered',
         'POST', 'hmac_sha256', 'Webhook for delivery confirmations', 'active', 'healthy', 1, 2100, 2080, 20,
         datetime.now() - timedelta(hours=3), None),
        
        ('WH-CUST-001', 'Customer Created', 'customer.created', 'crm', 'https://internal.api/webhook/crm/customer',
         'POST', 'bearer_token', 'Webhook for new customer creation', 'active', 'unhealthy', 1, 500, 480, 20,
         datetime.now() - timedelta(hours=6), datetime.now() - timedelta(hours=6)),
    ]
    
    for wh_data in webhooks:
        cursor.execute("""
            INSERT OR IGNORE INTO integration_webhooks 
            (code, name, event_type, source_system, target_url, http_method, auth_type, description,
             active_status, health_status, is_outbound, usage_count, success_count, failure_count,
             last_success_at, last_failure_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, wh_data)


def seed_events(cursor):
    """Seed sample events."""
    event_types = ['order.created', 'order.updated', 'order.shipped', 'order.delivered',
                   'inventory.low', 'inventory.updated', 'customer.created', 'shipment.status']
    sources = ['shopify', 'wms', 'crm', 'logistics', 'ecommerce']
    
    for i in range(50):
        event_type = random.choice(event_types)
        source = random.choice(sources)
        priority = random.choice(['high', 'normal', 'low'])
        status = random.choice(['published', 'processed', 'published', 'published'])
        
        cursor.execute("""
            INSERT INTO integration_events 
            (event_id, event_type, source_system, payload, priority, event_status, 
             correlation_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f'EVT-{datetime.now().strftime("%Y%m%d")}-{i:04d}',
            event_type,
            source,
            json.dumps({'id': i, 'data': f'Sample event data {i}'}),
            priority,
            status,
            f'CORR-{i:06d}',
            datetime.now() - timedelta(minutes=random.randint(1, 1440))
        ))


def seed_queue_items(cursor):
    """Seed sample queue items."""
    queues = ['order_sync', 'inventory_sync', 'shipment_update', 'customer_sync', 'gl_entry']
    
    for i in range(100):
        queue = random.choice(queues)
        status = random.choice(['pending', 'queued', 'processing', 'completed', 'failed'])
        retry = random.randint(0, 3) if status in ['failed', 'pending'] else 0
        
        cursor.execute("""
            INSERT INTO integration_queue_items 
            (queue_item_id, queue_name, source_system, destination_system, message_type,
             payload_preview, priority, message_status, retry_count, max_retries, last_error,
             correlation_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f'MSG-{datetime.now().strftime("%Y%m%d")}-{i:05d}',
            queue,
            random.choice(['ecommerce', 'warehouse', 'procurement']),
            random.choice(['sales', 'finance', 'logistics']),
            'json',
            f'{{"id": {i}, "type": "{queue}"}}',
            random.choice(['high', 'normal', 'low']),
            status,
            retry,
            5,
            'Connection timeout' if retry > 0 else None,
            f'CORR-Q{i:06d}',
            datetime.now() - timedelta(minutes=random.randint(1, 720))
        ))


def seed_dlq_items(cursor):
    """Seed sample DLQ items."""
    queues = ['order_sync', 'inventory_sync', 'shipment_update']
    
    for i in range(15):
        queue = random.choice(queues)
        review = random.choice(['pending', 'pending', 'pending', 'resolved'])
        
        cursor.execute("""
            INSERT INTO integration_dlq_items 
            (dlq_item_id, original_message_id, queue_name, message_type, payload, error_message,
             error_code, failure_count, last_failure_at, source_system, destination_system,
             review_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f'DLQ-{datetime.now().strftime("%Y%m%d")}-{i:04d}',
            f'MSG-ORIG-{i:05d}',
            queue,
            'json',
            json.dumps({'id': i, 'failed': True, 'reason': 'Max retries exceeded'}),
            'Connection refused after 5 retries',
            'ERR-CONN-REFUSED',
            random.randint(1, 5),
            datetime.now() - timedelta(hours=random.randint(1, 48)),
            random.choice(['ecommerce', 'warehouse']),
            random.choice(['sales', 'finance']),
            review,
            datetime.now() - timedelta(hours=random.randint(1, 72))
        ))


def seed_schedules(cursor):
    """Seed sample schedules."""
    cursor.execute("SELECT id, code FROM integration_flows LIMIT 10")
    flows = cursor.fetchall()
    
    schedules = [
        ('*/5 * * * *', 'Every 5 minutes', 5, '08:00', 'active'),
        ('*/15 * * * *', 'Every 15 minutes', 15, '00:00', 'active'),
        ('0 * * * *', 'Every hour', 60, '00:00', 'active'),
        ('0 0 * * *', 'Daily at midnight', None, '00:00', 'active'),
        ('0 6 * * *', 'Daily at 6 AM', None, '06:00', 'active'),
        ('0 */4 * * *', 'Every 4 hours', 240, '00:00', 'inactive'),
    ]
    
    for idx, (cron, freq, interval, time, status) in enumerate(schedules):
        if idx < len(flows):
            flow_id, flow_code = flows[idx]
            cursor.execute("""
                INSERT OR IGNORE INTO integration_schedules 
                (flow_id, schedule_name, cron_expression, frequency, interval_minutes, time_of_day,
                 is_active, next_run_at, run_count, error_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                flow_id,
                f'Schedule for {flow_code}',
                cron,
                freq,
                interval,
                time,
                1 if status == 'active' else 0,
                datetime.now() + timedelta(minutes=random.randint(5, 120)),
                random.randint(10, 500),
                random.randint(0, 5)
            ))


def seed_job_runs(cursor):
    """Seed sample job runs."""
    cursor.execute("SELECT id FROM integration_flows LIMIT 10")
    flows = cursor.fetchall()
    
    for i in range(50):
        flow_id = flows[i % len(flows)][0] if flows else 1
        status = random.choice(['success', 'success', 'success', 'failed', 'running'])
        start = datetime.now() - timedelta(hours=random.randint(1, 168))
        duration = random.randint(1000, 60000)
        processed = random.randint(10, 1000)
        succeeded = random.randint(5, processed)
        failed = processed - succeeded
        
        cursor.execute("""
            INSERT INTO integration_job_runs
            (job_run_id, flow_id, job_type, trigger_type, start_time, end_time, duration_ms,
             job_status, records_processed, records_succeeded, records_failed, records_skipped,
             warning_count, info_count, execution_mode, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f'RUN-{datetime.now().strftime("%Y%m%d%H%M")}-{i:04d}',
            flow_id,
            'flow_execution',
            random.choice(['scheduled', 'manual', 'webhook']),
            start,
            start + timedelta(milliseconds=duration) if status != 'running' else None,
            duration,
            status,
            processed,
            succeeded,
            failed,
            random.randint(0, 10),
            random.randint(0, 10),
            random.randint(0, 20),
            random.choice(['production', 'test']),
            start
        ))


def seed_credentials(cursor):
    """Seed sample credentials."""
    cursor.execute("SELECT id FROM integration_connectors LIMIT 5")
    connectors = [r[0] for r in cursor.fetchall()]
    
    creds = [
        ('shopify_oauth', 'Shopify OAuth Token', 'oauth2', 'bearer_token', connectors[0] if len(connectors) > 0 else None),
        ('quickbooks_oauth', 'QuickBooks OAuth', 'oauth2', 'oauth2', connectors[1] if len(connectors) > 1 else None),
        ('wms_api_key', 'WMS API Key', 'api_key', 'api_key', connectors[3] if len(connectors) > 3 else None),
        ('dhl_api_key', 'DHL API Key', 'api_key', 'api_key', connectors[4] if len(connectors) > 4 else None),
        ('sftp_ssh_key', 'SFTP SSH Key', 'ssh_key', 'ssh_key', connectors[2] if len(connectors) > 2 else None),
    ]
    
    for cred_data in creds:
        cursor.execute("""
            INSERT OR IGNORE INTO integration_credentials 
            (credential_id, code, name, credential_type, auth_method, connector_id,
             is_active, test_status, expiry_warning_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            f'CRED-{cred_data[0]}',
            cred_data[1],
            cred_data[2],
            cred_data[3],
            cred_data[4],
            1,
            'success',
            30
        ))


def seed_mappings(cursor):
    """Seed sample field mappings."""
    mappings = [
        ('order_id', 'Order ID', 'shopify', 'internal_sales', 'orders',
         '[{"source_field": "id", "target_field": "order_number"}, {"source_field": "total_price", "target_field": "amount"}]'),
        
        ('customer_map', 'Customer Mapping', 'shopify', 'internal_crm', 'customers',
         '[{"source_field": "email", "target_field": "email_address"}, {"source_field": "first_name", "target_field": "firstname"}]'),
        
        ('inventory_map', 'Inventory Mapping', 'wms', 'ecommerce', 'inventory',
         '[{"source_field": "sku", "target_field": "product_sku"}, {"source_field": "quantity", "target_field": "stock_qty"}]'),
    ]
    
    for map_data in mappings:
        cursor.execute("""
            INSERT OR IGNORE INTO integration_field_mappings 
            (mapping_id, code, name, source_system, target_system, entity_type,
             mappings_json, is_active, usage_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            f'MAP-{map_data[0]}',
            map_data[1],
            map_data[2],
            map_data[3],
            map_data[4],
            map_data[5],
            1,
            random.randint(5, 100)
        ))


def seed_transformations(cursor):
    """Seed sample transformation rules."""
    rules = [
        ('date_norm', 'Date Normalization', 'date_formatting', 'normalization',
         'Transform dates to ISO 8601 format', 'input.date.toISOString()'),
        
        ('price_mult', 'Price Multiplier', 'formula', 'enrichment',
         'Apply currency conversion multiplier', 'input.price * config.multiplier'),
        
        ('status_map', 'Status Code Mapping', 'enum_mapping', 'mapping',
         'Map external status to internal codes', 'statusMapping[input.status]'),
        
        ('upper_email', 'Email Uppercase', 'string_transform', 'normalization',
         'Normalize email to uppercase', 'input.email.toUpperCase()'),
    ]
    
    for rule_data in rules:
        cursor.execute("""
            INSERT OR IGNORE INTO integration_transformation_rules 
            (rule_id, code, name, rule_type, category, transformation_logic,
             expression, is_active, usage_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            f'RULE-{rule_data[0]}',
            rule_data[1],
            rule_data[2],
            rule_data[3],
            rule_data[4],
            rule_data[5],
            1,
            random.randint(10, 200)
        ))


def seed_alert_rules(cursor):
    """Seed sample alert rules."""
    rules = [
        ('connector_down', 'Connector Down Alert', 'connector_health', 'critical',
         "connector.health_status == 'unhealthy'", 0, 15),
        
        ('dlq_threshold', 'DLQ Threshold Alert', 'queue_depth', 'high',
         'dlq.count > 10', 0, 30),
        
        ('high_failure_rate', 'High Failure Rate', 'flow_failure_rate', 'high',
         'flow.failure_rate > 0.1', 5, 15),
        
        ('queue_backlog', 'Queue Backlog', 'queue_depth', 'medium',
         'queue.depth > 1000', 10, 30),
    ]
    
    for rule_data in rules:
        cursor.execute("""
            INSERT OR IGNORE INTO integration_alert_rules 
            (rule_id, code, name, alert_type, severity, condition_expression,
             cooldown_minutes, is_active, trigger_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            f'ALR-{rule_data[0]}',
            rule_data[1],
            rule_data[2],
            rule_data[3],
            rule_data[4],
            rule_data[5],
            1,
            random.randint(0, 20)
        ))


def seed_reconciliation_batches(cursor):
    """Seed sample reconciliation batches."""
    batches = [
        ('Daily Sales Recon', 'count_match', 'ecommerce', 'finance', 'transactions',
         datetime.now() - timedelta(days=1), datetime.now() - timedelta(hours=12),
         1500, 1500, 1495, 5, 0, 0, 'completed', 'exact', 0.0),
        
        ('Inventory Count Recon', 'count_match', 'wms', 'ecommerce', 'inventory',
         datetime.now() - timedelta(hours=6), datetime.now() - timedelta(hours=2),
         500, 498, 490, 8, 2, 0, 'completed', 'exact', 0.0),
        
        ('Customer Sync Check', 'status_match', 'crm', 'ecommerce', 'customers',
         datetime.now() - timedelta(hours=4), datetime.now() - timedelta(hours=1),
         200, 200, 195, 5, 0, 0, 'completed', 'exact', 0.0),
    ]
    
    for batch_data in batches:
        cursor.execute("""
            INSERT OR IGNORE INTO integration_reconciliation_batches
            (batch_id, batch_name, reconciliation_type, source_system, destination_system,
             entity_type, period_start, period_end, source_count, destination_count,
             matched_count, mismatch_count, missing_in_source_count, missing_in_destination_count,
             duplicate_count, batch_status, run_start_time, run_end_time, run_duration_ms,
             comparison_method, tolerance_percentage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            batch_data[0],
            batch_data[1],
            batch_data[2],
            batch_data[3],
            batch_data[4],
            batch_data[5],
            batch_data[6],
            batch_data[7],
            batch_data[8],
            batch_data[9],
            batch_data[10],
            batch_data[11],
            batch_data[12],
            0,
            batch_data[13],
            batch_data[5],
            batch_data[6],
            random.randint(1000, 30000),
            batch_data[14],
            batch_data[15]
        ))


def seed_file_exchange(cursor):
    """Seed sample file exchange records."""
    files = [
        ('orders_20240115.csv', 'csv', 'outbound', 'ecommerce', 'procurement', 1500, 1450, 50),
        ('inventory_snapshot.xlsx', 'excel', 'inbound', 'wms', 'ecommerce', 500, 498, 2),
        ('shipment_manifest_001.xml', 'xml', 'outbound', 'logistics', 'warehouse', 75, 75, 0),
        ('customer_export.json', 'json', 'outbound', 'crm', 'marketing', 300, 295, 5),
    ]
    
    for idx, file_data in enumerate(files):
        cursor.execute("""
            INSERT OR IGNORE INTO integration_file_exchange 
            (file_id, file_name, file_type, direction, source_system, destination_system,
             row_count, success_count, error_count, file_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            file_data[0],
            file_data[1],
            file_data[2],
            file_data[3],
            file_data[4],
            file_data[5],
            file_data[6],
            file_data[7],
            'completed' if file_data[7] == file_data[6] else 'failed',
            datetime.now() - timedelta(days=idx, hours=random.randint(1, 12))
        ))


def seed_usage_metrics(cursor):
    """Seed sample usage metrics."""
    cursor.execute("SELECT id FROM integration_connectors LIMIT 5")
    connectors = [r[0] for r in cursor.fetchall()]
    
    for days_ago in range(30):
        date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        for hour in range(24):
            for conn_id in connectors:
                metric_value = random.randint(10, 500)
                
                cursor.execute("""
                    INSERT INTO integration_usage_metrics 
                    (metric_id, metric_date, metric_hour, connector_id, metric_type,
                     metric_value, unit, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    date,
                    hour,
                    conn_id,
                    random.choice(['api_calls', 'data_volume', 'processing_time']),
                    metric_value,
                    random.choice(['calls', 'MB', 'ms']),
                    datetime.now() - timedelta(days=days_ago, hours=24-hour)
                ))


if __name__ == '__main__':
    from database import get_db
    conn = get_db()
    cursor = conn.cursor()
    seed_integration_data()
    print("Integration seed data complete!")
