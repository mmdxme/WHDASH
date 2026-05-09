"""
Seed E-commerce Demo Data
========================
Seeds realistic e-commerce integration demo data for testing and demonstration.
"""

import sqlite3
import os
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict

DATABASE = os.path.join(os.path.dirname(__file__), 'warehouse.db')

CHANNEL_NAMES = [
    ('SHOPIFY_US', 'Shopify USA Store', 'website'),
    ('SHOPIFY_EU', 'Shopify Europe', 'website'),
    ('AMAZON_MAIN', 'Amazon Marketplace', 'marketplace'),
    ('WOO_COMMERCE', 'WooCommerce Store', 'website'),
    ('ETSY_SHOP', 'Etsy Handmade Shop', 'marketplace'),
]

CUSTOMER_NAMES = [
    ('John', 'Smith', 'john.smith@email.com', '+1-555-0101'),
    ('Sarah', 'Johnson', 'sarah.j@email.com', '+1-555-0102'),
    ('Michael', 'Brown', 'mbrown@email.com', '+1-555-0103'),
    ('Emily', 'Davis', 'emily.d@email.com', '+1-555-0104'),
    ('David', 'Wilson', 'dwilson@email.com', '+1-555-0105'),
    ('Jennifer', 'Martinez', 'jmartinez@email.com', '+1-555-0106'),
    ('Robert', 'Anderson', 'randerson@email.com', '+1-555-0107'),
    ('Lisa', 'Taylor', 'ltaylor@email.com', '+1-555-0108'),
    ('James', 'Thomas', 'jthomas@email.com', '+1-555-0109'),
    ('Mary', 'Garcia', 'mgarcia@email.com', '+1-555-0110'),
]

PRODUCT_NAMES = [
    ('Wireless Bluetooth Headphones', 'WBH-001', '8901234567890'),
    ('USB-C Charging Cable 6ft', 'UCC-006', '8901234567891'),
    ('Portable Power Bank 10000mAh', 'PPB-010', '8901234567892'),
    ('Smartphone Screen Protector', 'SSP-001', '8901234567893'),
    ('Laptop Stand Aluminum', 'LSA-001', '8901234567894'),
    ('Wireless Mouse Ergonomic', 'WME-001', '8901234567895'),
    ('Mechanical Keyboard RGB', 'MKR-001', '8901234567896'),
    ('Webcam HD 1080p', 'WHD-108', '8901234567897'),
    ('Monitor Light Bar', 'MLB-001', '8901234567898'),
    ('Phone Car Mount Magnetic', 'PCM-001', '8901234567899'),
]

ORDER_STATUSES = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']
PAYMENT_STATUSES = ['pending', 'paid', 'partially_refunded', 'refunded', 'failed']
FULFILLMENT_STATUSES = ['unfulfilled', 'processing', 'picked', 'packed', 'shipped', 'delivered']
SYNC_STATUSES = ['pending', 'importing', 'synced', 'failed', 'skipped']

EXCEPTION_TYPES = [
    ('unmapped_item', 'medium', 'Product not found in internal catalog'),
    ('missing_customer', 'high', 'Customer email not found in system'),
    ('duplicate_order', 'low', 'Order already exists in system'),
    ('stock_mismatch', 'medium', 'Available stock differs from channel'),
    ('invalid_payment', 'high', 'Payment method not recognized'),
    ('price_mismatch', 'low', 'Channel price differs from catalog'),
    ('shipping_error', 'medium', 'Shipping address validation failed'),
]

CITIES = [
    ('New York', 'NY', 'US', '10001'),
    ('Los Angeles', 'CA', 'US', '90001'),
    ('Chicago', 'IL', 'US', '60601'),
    ('Houston', 'TX', 'US', '77001'),
    ('Phoenix', 'AZ', 'US', '85001'),
    ('Philadelphia', 'PA', 'US', '19101'),
    ('San Antonio', 'TX', 'US', '78201'),
    ('San Diego', 'CA', 'US', '92101'),
    ('Dallas', 'TX', 'US', '75201'),
    ('San Jose', 'CA', 'US', '95101'),
]


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def seed_channels():
    """Seed e-commerce channels."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if channels already exist
    existing = cursor.execute("SELECT COUNT(*) FROM ecommerce_channels").fetchone()[0]
    if existing > 0:
        print(f"  Channels already exist ({existing}), skipping...")
        conn.close()
        return
    
    print("  Seeding channels...")
    
    for code, name, ch_type in CHANNEL_NAMES:
        cursor.execute("""
            INSERT INTO ecommerce_channels
            (channel_code, channel_name, channel_type, company_id, warehouse_id,
             api_endpoint, api_key, is_active, is_connected, last_sync_at,
             last_sync_status, sync_direction, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            code, name, ch_type, 1, 1,
            f'https://api.{code.lower().replace("_", "")}.com/v1',
            f'key_{code.lower()}_demo123',
            1, 1,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'success', 'bidirectional'
        ))
    
    conn.commit()
    conn.close()
    print(f"  Created {len(CHANNEL_NAMES)} channels")


def seed_orders():
    """Seed e-commerce orders."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check existing
    existing = cursor.execute("SELECT COUNT(*) FROM ecommerce_order_imports").fetchone()[0]
    if existing > 0:
        print(f"  Orders already exist ({existing}), skipping...")
        conn.close()
        return
    
    print("  Seeding orders...")
    
    channels = cursor.execute("SELECT id, channel_name FROM ecommerce_channels").fetchall()
    if not channels:
        conn.close()
        return
    
    order_count = 0
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(50):
        channel = random.choice(channels)
        customer = random.choice(CUSTOMER_NAMES)
        city = random.choice(CITIES)
        
        order_num = f'ORD-{channel[1][:3].upper()}-{10000 + i}'
        order_date = base_date + timedelta(days=random.randint(0, 30), hours=random.randint(8, 20))
        
        # Calculate totals
        num_items = random.randint(1, 4)
        items_total = 0
        lines_data = []
        
        for j in range(num_items):
            product = random.choice(PRODUCT_NAMES)
            qty = random.randint(1, 3)
            price = round(random.uniform(19.99, 299.99), 2)
            discount = round(price * random.uniform(0, 0.15), 2)
            tax = round((price - discount) * 0.08, 2)
            line_total = (price - discount) * qty + tax
            items_total += line_total
            
            lines_data.append({
                'product': product,
                'qty': qty,
                'price': price,
                'discount': discount,
                'tax': tax,
                'total': line_total
            })
        
        shipping = round(random.uniform(5.99, 25.00), 2)
        total = items_total + shipping
        
        payment_status = random.choice(PAYMENT_STATUSES)
        fulfillment_status = random.choice(FULFILLMENT_STATUSES)
        sync_status = random.choice(SYNC_STATUSES)
        
        # Weight towards synced
        if random.random() < 0.7:
            sync_status = 'synced'
        
        first_name, last_name, email, phone = customer
        full_name = f"{first_name} {last_name}"
        
        # Insert order
        cursor.execute("""
            INSERT INTO ecommerce_order_imports
            (external_order_id, external_order_number, channel_id, channel_name,
             company_id, warehouse_id, customer_email, customer_phone, customer_name,
             billing_name, billing_city, billing_state, billing_country, billing_postal_code,
             billing_phone, shipping_name, shipping_city, shipping_state, shipping_country,
             shipping_postal_code, shipping_phone, shipping_method, shipping_cost,
             order_date, order_datetime, currency, subtotal, discount_amount, tax_amount,
             total_amount, payment_method, payment_method_display, payment_status,
             fulfillment_status, order_status, sync_status, imported_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            f'ext_{order_num}', order_num, channel[0], channel[1],
            1, 1, email, phone, full_name,
            full_name, city[0], city[1], city[2], city[3],
            phone, full_name, city[0], city[1], city[2], city[3],
            phone, random.choice(['standard', 'express', 'overnight']),
            shipping, order_date.strftime('%Y-%m-%d'), order_date.strftime('%Y-%m-%d %H:%M:%S'),
            'USD', round(items_total - sum(l['discount'] for l in lines_data), 2),
            round(sum(l['discount'] for l in lines_data), 2),
            round(sum(l['tax'] for l in lines_data), 2),
            round(total, 2),
            random.choice(['credit_card', 'paypal', 'apple_pay', 'bank_transfer']),
            random.choice(['Credit Card', 'PayPal', 'Apple Pay', 'Bank Transfer']),
            payment_status, fulfillment_status,
            'confirmed' if fulfillment_status != 'unfulfilled' else 'pending',
            sync_status
        ))
        
        order_id = cursor.lastrowid
        
        # Insert order lines
        for j, line in enumerate(lines_data):
            cursor.execute("""
                INSERT INTO ecommerce_order_lines
                (order_import_id, line_number, external_product_id, external_product_name,
                 external_sku, external_barcode, quantity, unit_price, discount_amount,
                 tax_amount, total_amount, fulfillment_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order_id, j + 1,
                f"prod_{line['product'][1]}",
                line['product'][0], line['product'][1], line['product'][2],
                line['qty'], line['price'], line['discount'],
                line['tax'], line['total'], fulfillment_status
            ))
        
        order_count += 1
    
    conn.commit()
    conn.close()
    print(f"  Created {order_count} orders")


def seed_customers():
    """Seed e-commerce customers."""
    conn = get_db()
    cursor = conn.cursor()
    
    existing = cursor.execute("SELECT COUNT(*) FROM ecommerce_customer_imports").fetchone()[0]
    if existing > 0:
        print(f"  Customers already exist ({existing}), skipping...")
        conn.close()
        return
    
    print("  Seeding customers...")
    
    channels = cursor.execute("SELECT id, channel_name FROM ecommerce_channels").fetchall()
    if not channels:
        conn.close()
        return
    
    customer_count = 0
    
    for i, customer in enumerate(CUSTOMER_NAMES):
        channel = random.choice(channels)
        city = random.choice(CITIES)
        first_name, last_name, email, phone = customer
        full_name = f"{first_name} {last_name}"
        
        sync_status = random.choice(['synced', 'synced', 'synced', 'pending', 'duplicate'])
        is_guest = 0
        duplicate_status = 'approved'
        
        if sync_status == 'duplicate':
            duplicate_status = 'pending'
        
        cursor.execute("""
            INSERT INTO ecommerce_customer_imports
            (external_customer_id, channel_id, channel_name, company_id,
             email, phone, first_name, last_name, full_name, is_guest,
             billing_name, billing_city, billing_state, billing_country,
             billing_postal_code, billing_phone, shipping_name, shipping_city,
             shipping_state, shipping_country, shipping_postal_code, shipping_phone,
             internal_customer_id, duplicate_review_status, sync_status, imported_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            f'ext_cust_{i+1}', channel[0], channel[1], 1,
            email, phone, first_name, last_name, full_name, is_guest,
            full_name, city[0], city[1], city[2], city[3], phone,
            full_name, city[0], city[1], city[2], city[3], phone,
            i + 100 if sync_status == 'synced' else 0,
            duplicate_status, sync_status
        ))
        
        customer_count += 1
    
    conn.commit()
    conn.close()
    print(f"  Created {customer_count} customers")


def seed_exceptions():
    """Seed e-commerce exceptions."""
    conn = get_db()
    cursor = conn.cursor()
    
    existing = cursor.execute("SELECT COUNT(*) FROM ecommerce_exceptions").fetchone()[0]
    if existing > 0:
        print(f"  Exceptions already exist ({existing}), skipping...")
        conn.close()
        return
    
    print("  Seeding exceptions...")
    
    channels = cursor.execute("SELECT id, channel_name FROM ecommerce_channels").fetchall()
    if not channels:
        conn.close()
        return
    
    exception_count = 0
    
    for i in range(15):
        channel = random.choice(channels)
        exc_type, severity, description = random.choice(EXCEPTION_TYPES)
        exc_date = datetime.now() - timedelta(days=random.randint(0, 7))
        
        exc_number = f"EXC-{exc_date.strftime('%Y%m%d')}{i+1:04d}"
        status = random.choice(['open', 'open', 'in_review', 'resolved'])
        
        cursor.execute("""
            INSERT INTO ecommerce_exceptions
            (exception_number, exception_type, severity, title, description,
             channel_id, channel_name, company_id, reference_type,
             external_reference, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', ?))
        """, (
            exc_number, exc_type, severity,
            f"{exc_type.replace('_', ' ').title()} Exception",
            description, channel[0], channel[1], 1, 'order',
            f"EXT-REF-{i+1}", status,
            f"-{random.randint(1, 7)} days"
        ))
        
        exception_count += 1
    
    conn.commit()
    conn.close()
    print(f"  Created {exception_count} exceptions")


def seed_inventory_syncs():
    """Seed inventory sync records."""
    conn = get_db()
    cursor = conn.cursor()
    
    existing = cursor.execute("SELECT COUNT(*) FROM ecommerce_inventory_syncs").fetchone()[0]
    if existing > 0:
        print(f"  Inventory syncs already exist ({existing}), skipping...")
        conn.close()
        return
    
    print("  Seeding inventory sync records...")
    
    channels = cursor.execute("SELECT id, channel_name FROM ecommerce_channels").fetchall()
    if not channels:
        conn.close()
        return
    
    sync_count = 0
    
    for channel in channels:
        for product in PRODUCT_NAMES[:5]:  # First 5 products
            internal_stock = random.randint(0, 500)
            published_stock = max(0, internal_stock - random.randint(0, 20))
            
            cursor.execute("""
                INSERT INTO ecommerce_inventory_syncs
                (channel_id, channel_name, company_id, warehouse_id,
                 internal_item_id, internal_sku, internal_barcode,
                 internal_stock, published_stock, available_stock,
                 sync_status, last_synced_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                channel[0], channel[1], 1, 1,
                random.randint(1, 100), product[1], product[2],
                internal_stock, published_stock, published_stock,
                random.choice(['synced', 'synced', 'pending', 'failed'])
            ))
            
            sync_count += 1
    
    conn.commit()
    conn.close()
    print(f"  Created {sync_count} inventory sync records")


def seed_product_mappings():
    """Seed product mappings."""
    conn = get_db()
    cursor = conn.cursor()
    
    existing = cursor.execute("SELECT COUNT(*) FROM ecommerce_product_mappings").fetchone()[0]
    if existing > 0:
        print(f"  Product mappings already exist ({existing}), skipping...")
        conn.close()
        return
    
    print("  Seeding product mappings...")
    
    channels = cursor.execute("SELECT id FROM ecommerce_channels").fetchall()
    if not channels:
        conn.close()
        return
    
    mapping_count = 0
    
    for channel in channels:
        for i, product in enumerate(PRODUCT_NAMES):
            cursor.execute("""
                INSERT INTO ecommerce_product_mappings
                (channel_id, internal_item_id, internal_sku, internal_barcode,
                 external_product_id, external_sku, external_barcode,
                 is_active, sync_status, last_synced_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                channel[0], 100 + i, product[1], product[2],
                f"ext_prod_{product[1]}", product[1], product[2],
                1, random.choice(['synced', 'synced', 'pending'])
            ))
            
            mapping_count += 1
    
    conn.commit()
    conn.close()
    print(f"  Created {mapping_count} product mappings")


def seed_sync_jobs():
    """Seed sync jobs."""
    conn = get_db()
    cursor = conn.cursor()
    
    existing = cursor.execute("SELECT COUNT(*) FROM ecommerce_sync_jobs").fetchone()[0]
    if existing > 0:
        print(f"  Sync jobs already exist ({existing}), skipping...")
        conn.close()
        return
    
    print("  Seeding sync jobs...")
    
    channels = cursor.execute("SELECT id, channel_name FROM ecommerce_channels").fetchall()
    if not channels:
        conn.close()
        return
    
    job_count = 0
    
    for i in range(20):
        channel = random.choice(channels)
        job_type = random.choice(['order_sync', 'inventory_sync', 'customer_sync'])
        status = random.choice(['completed', 'completed', 'completed', 'failed', 'running'])
        started = datetime.now() - timedelta(hours=random.randint(1, 72))
        
        processed = random.randint(5, 50)
        successful = int(processed * random.uniform(0.8, 1.0))
        failed = processed - successful
        
        cursor.execute("""
            INSERT INTO ecommerce_sync_jobs
            (job_type, channel_id, channel_name, company_id, warehouse_id,
             status, sync_mode, started_at, completed_at,
             items_processed, items_successful, items_failed,
             created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', ?))
        """, (
            job_type, channel[0], channel[1], 1, 1,
            status, random.choice(['manual', 'scheduled', 'webhook']),
            started.strftime('%Y-%m-%d %H:%M:%S'),
            (started + timedelta(minutes=random.randint(1, 30))).strftime('%Y-%m-%d %H:%M:%S') if status == 'completed' else '',
            processed, successful, failed,
            f"-{random.randint(1, 72)} hours"
        ))
        
        job_count += 1
    
    conn.commit()
    conn.close()
    print(f"  Created {job_count} sync jobs")


def seed_audit_logs():
    """Seed audit logs."""
    conn = get_db()
    cursor = conn.cursor()
    
    existing = cursor.execute("SELECT COUNT(*) FROM ecommerce_audit_logs").fetchone()[0]
    if existing > 0:
        print(f"  Audit logs already exist ({existing}), skipping...")
        conn.close()
        return
    
    print("  Seeding audit logs...")
    
    channels = cursor.execute("SELECT id, channel_name FROM ecommerce_channels").fetchall()
    if not channels:
        conn.close()
        return
    
    log_count = 0
    actions = ['created', 'updated', 'synced', 'retried', 'resolved', 'failed']
    entities = ['channel', 'order', 'customer', 'inventory', 'mapping']
    
    for i in range(30):
        channel = random.choice(channels)
        action = random.choice(actions)
        entity = random.choice(entities)
        
        cursor.execute("""
            INSERT INTO ecommerce_audit_logs
            (log_type, action, channel_id, channel_name, company_id,
             user_id, user_name, entity_type, entity_id, entity_reference,
             timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', ?))
        """, (
            'sync', action, channel[0], channel[1], 1,
            1, 'admin', entity, random.randint(1, 100), f'{entity.upper()}-{random.randint(1, 100)}',
            f"-{random.randint(1, 48)} hours"
        ))
        
        log_count += 1
    
    conn.commit()
    conn.close()
    print(f"  Created {log_count} audit logs")


def seed_settings():
    """Ensure default settings exist."""
    conn = get_db()
    cursor = conn.cursor()
    
    print("  Checking e-commerce settings...")
    
    defaults = [
        ('ecommerce_default_currency', 'USD', 'string', 'Default currency for e-commerce transactions'),
        ('ecommerce_default_payment_status', 'pending', 'string', 'Default payment status for new orders'),
        ('ecommerce_default_fulfillment_status', 'unfulfilled', 'string', 'Default fulfillment status'),
        ('ecommerce_max_retry_attempts', '3', 'int', 'Maximum retry attempts for failed syncs'),
        ('ecommerce_retry_interval_minutes', '5', 'int', 'Minutes between retry attempts'),
        ('ecommerce_order_prefix', 'ECO', 'string', 'Prefix for manually created e-commerce orders'),
        ('ecommerce_customer_prefix', 'EC', 'string', 'Prefix for imported customer codes'),
        ('ecommerce_enable_audit_log', '1', 'bool', 'Enable detailed audit logging'),
        ('ecommerce_enable_webhook_log', '1', 'bool', 'Enable webhook logging'),
        ('ecommerce_enable_api_log', '1', 'bool', 'Enable API call logging'),
    ]
    
    for key, value, stype, desc in defaults:
        existing = cursor.execute(
            "SELECT id FROM ecommerce_settings WHERE setting_key = ?", (key,)
        ).fetchone()
        
        if not existing:
            cursor.execute("""
                INSERT INTO ecommerce_settings (setting_key, setting_value, setting_type, description)
                VALUES (?, ?, ?, ?)
            """, (key, value, stype, desc))
    
    conn.commit()
    conn.close()
    print("  E-commerce settings initialized")


def main():
    """Main seeding function."""
    print("\n" + "="*60)
    print("SEEDING E-COMMERCE DATA")
    print("="*60 + "\n")
    
    # Initialize tables first
    from ecommerce_models import init_ecommerce_tables
    print("Initializing e-commerce tables...")
    init_ecommerce_tables()
    print("Tables initialized.\n")
    
    print("Seeding e-commerce data...")
    
    seed_settings()
    seed_channels()
    seed_product_mappings()
    seed_orders()
    seed_customers()
    seed_inventory_syncs()
    seed_exceptions()
    seed_sync_jobs()
    seed_audit_logs()
    
    print("\n" + "="*60)
    print("E-COMMERCE DATA SEEDING COMPLETE")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
