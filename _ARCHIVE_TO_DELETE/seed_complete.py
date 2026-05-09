"""
Aggressive Minimal Seeder - Fills ALL Empty Tables
================================================
Inserts rows even if some columns are NULL/DEFAULT.
"""

import os
import sys
import sqlite3
import random
from datetime import datetime, timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'warehouse.db')

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except:
    pass


def get_db():
    conn = sqlite3.connect(DATABASE, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=OFF")  # Disable FK for seeding
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def get_columns_info(db, table):
    """Get columns with types and defaults."""
    try:
        cursor = db.execute(f"PRAGMA table_info([{table}])")
        return [(row[1], row[2], row[4]) for row in cursor.fetchall()]  # name, type, dflt
    except:
        return []


def count_rows(db, table):
    try:
        return db.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
    except:
        return 0


def generate_row(db, table, columns_info):
    """Generate minimal row that works with actual schema."""
    data = {}
    
    for col_name, col_type, col_default in columns_info:
        # Skip id columns that are autoincrement
        if col_name == 'id':
            continue
        
        # Handle columns with defaults
        if col_default is not None:
            data[col_name] = col_default
            continue
        
        col_lower = col_name.lower()
        
        # Based on column name patterns
        if 'name' in col_lower:
            data[col_name] = f'Sample {col_name.title()}'
        elif 'code' in col_lower:
            data[col_name] = f'{col_name[:3].upper()}-{random.randint(100, 999)}'
        elif 'number' in col_lower or 'no' in col_lower:
            data[col_name] = str(random.randint(1000, 9999))
        elif 'status' in col_lower:
            data[col_name] = 'Active'
        elif 'type' in col_lower:
            data[col_name] = 'General'
        elif 'date' in col_lower or 'at' in col_lower or '_on' in col_lower:
            data[col_name] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        elif 'amount' in col_lower or 'price' in col_lower or 'cost' in col_lower or 'total' in col_lower:
            data[col_name] = round(random.uniform(100, 10000), 2)
        elif 'qty' in col_lower or 'quantity' in col_lower or 'count' in col_lower or 'stock' in col_lower:
            data[col_name] = random.randint(1, 100)
        elif 'rate' in col_lower or 'ratio' in col_lower or 'percent' in col_lower:
            data[col_name] = round(random.uniform(0.1, 10.0), 2)
        elif 'email' in col_lower:
            data[col_name] = f'sample{random.randint(1,999)}@example.com'
        elif 'phone' in col_lower or 'mobile' in col_lower:
            data[col_name] = f'+97150{random.randint(1000000, 9999999)}'
        elif 'address' in col_lower or 'location' in col_lower:
            data[col_name] = f'123 Sample St, Dubai, UAE'
        elif 'desc' in col_lower or 'notes' in col_lower or 'remark' in col_lower:
            data[col_name] = f'Sample {col_name} entry'
        elif 'token' in col_lower:
            data[col_name] = f'token_{random.randint(10000, 99999)}'
        elif 'url' in col_lower or 'link' in col_lower or 'website' in col_lower:
            data[col_name] = f'https://example.com/{random.randint(1,100)}'
        elif 'image' in col_lower or 'photo' in col_lower or 'avatar' in col_lower or 'file' in col_lower:
            data[col_name] = '/static/images/default.png'
        elif 'is_' in col_lower or 'has_' in col_lower or 'can_' in col_lower or 'enabled' in col_lower:
            data[col_name] = random.choice([0, 1, 'Yes', 'No', 'True', 'False'])
        elif 'flag' in col_lower:
            data[col_name] = 0
        elif 'color' in col_lower:
            data[col_name] = '#' + ''.join([random.choice('0123456789ABCDEF') for _ in range(6)])
        elif 'ip' in col_lower:
            data[col_name] = f'192.168.1.{random.randint(1,254)}'
        elif 'json' in col_lower or 'config' in col_lower or 'metadata' in col_lower:
            data[col_name] = '{}'
        elif 'foreign' in col_lower or '_id' in col_lower:
            # Foreign key - set to 1 or NULL
            data[col_name] = 1 if random.random() > 0.3 else None
        elif 'reference' in col_lower:
            data[col_name] = f'REF-{random.randint(1000, 9999)}'
        elif 'version' in col_lower:
            data[col_name] = '1.0'
        elif 'priority' in col_lower:
            data[col_name] = random.choice(['Low', 'Medium', 'High'])
        elif 'category' in col_lower:
            data[col_name] = 'General'
        elif 'company' in col_lower:
            data[col_name] = 1
        elif 'user' in col_lower or 'employee' in col_lower or 'staff' in col_lower:
            data[col_name] = 1
        elif 'customer' in col_lower or 'client' in col_lower:
            data[col_name] = 1
        elif 'supplier' in col_lower or 'vendor' in col_lower:
            data[col_name] = 1
        elif 'order' in col_lower or 'po' in col_lower or 'purchase' in col_lower:
            data[col_name] = 1
        elif 'invoice' in col_lower or 'receipt' in col_lower or 'payment' in col_lower:
            data[col_name] = 1
        elif 'part' in col_lower or 'item' in col_lower or 'product' in col_lower or 'sku' in col_lower:
            data[col_name] = 1
        elif 'warehouse' in col_lower or 'location' in col_lower or 'zone' in col_lower or 'bin' in col_lower:
            data[col_name] = 1
        elif 'document' in col_lower or 'file' in col_lower:
            data[col_name] = '/documents/sample.pdf'
        elif 'message' in col_lower or 'content' in col_lower or 'text' in col_lower:
            data[col_name] = f'Sample message content {random.randint(1,100)}'
        elif 'title' in col_lower or 'subject' in col_lower or 'head' in col_lower:
            data[col_name] = f'Sample {col_name} entry'
        elif 'action' in col_lower:
            data[col_name] = f'Action {random.randint(1,10)}'
        elif 'trigger' in col_lower:
            data[col_name] = 'on_create'
        elif 'event' in col_lower:
            data[col_name] = 'item.created'
        elif 'platform' in col_lower:
            data[col_name] = 'Web'
        elif 'channel' in col_lower:
            data[col_name] = 'Direct'
        elif 'gender' in col_lower:
            data[col_name] = random.choice(['Male', 'Female', 'Other'])
        elif 'nationality' in col_lower or 'country' in col_lower:
            data[col_name] = 'UAE'
        elif 'city' in col_lower or 'state' in col_lower or 'province' in col_lower:
            data[col_name] = 'Dubai'
        elif 'zip' in col_lower or 'postal' in col_lower:
            data[col_name] = '00000'
        elif 'fax' in col_lower:
            data[col_name] = f'+9714{random.randint(100000, 999999)}'
        elif 'lat' in col_lower or 'longitude' in col_lower or 'lng' in col_lower:
            data[col_name] = round(random.uniform(25.0, 25.5), 6)
        elif 'factor' in col_lower or 'multiplier' in col_lower:
            data[col_name] = round(random.uniform(0.8, 1.2), 2)
        elif 'length' in col_lower or 'width' in col_lower or 'height' in col_lower or 'size' in col_lower or 'dimension' in col_lower:
            data[col_name] = round(random.uniform(1, 100), 2)
        elif 'weight' in col_lower:
            data[col_name] = round(random.uniform(0.1, 50), 2)
        elif 'volume' in col_lower:
            data[col_name] = round(random.uniform(0.1, 100), 2)
        elif 'thresh' in col_lower or 'min' in col_lower or 'max' in col_lower:
            data[col_name] = round(random.uniform(1, 100), 2)
        elif 'budget' in col_lower:
            data[col_name] = round(random.uniform(10000, 100000), 2)
        elif 'spent' in col_lower or 'used' in col_lower or 'consumed' in col_lower:
            data[col_name] = round(random.uniform(100, 50000), 2)
        elif 'balance' in col_lower:
            data[col_name] = round(random.uniform(0, 10000), 2)
        elif 'interest' in col_lower:
            data[col_name] = round(random.uniform(0.1, 10.0), 2)
        elif 'penalty' in col_lower:
            data[col_name] = round(random.uniform(10, 500), 2)
        elif 'revenue' in col_lower or 'income' in col_lower or 'profit' in col_lower or 'sales' in col_lower:
            data[col_name] = round(random.uniform(1000, 100000), 2)
        elif 'expense' in col_lower or 'cost' in col_lower:
            data[col_name] = round(random.uniform(100, 50000), 2)
        elif 'margin' in col_lower:
            data[col_name] = round(random.uniform(5, 30), 2)
        elif 'tax' in col_lower:
            data[col_name] = round(random.uniform(5, 20), 2)
        elif 'discount' in col_lower:
            data[col_name] = round(random.uniform(0, 15), 2)
        elif 'commission' in col_lower:
            data[col_name] = round(random.uniform(1, 10), 2)
        elif 'ref' in col_lower or 'rel' in col_lower or 'link' in col_lower:
            data[col_name] = random.randint(1, 100)
        elif 'parent' in col_lower or 'root' in col_lower or 'group' in col_lower:
            data[col_name] = None
        elif 'level' in col_lower or 'tier' in col_lower or 'grade' in col_lower:
            data[col_name] = random.randint(1, 5)
        elif 'sort' in col_lower or 'order' in col_lower or 'seq' in col_lower or 'index' in col_lower:
            data[col_name] = random.randint(1, 100)
        elif 'position' in col_lower:
            data[col_name] = random.randint(1, 50)
        elif 'hours' in col_lower or 'days' in col_lower or 'time' in col_lower or 'duration' in col_lower:
            data[col_name] = random.randint(1, 24)
        elif 'minutes' in col_lower:
            data[col_name] = random.randint(1, 60)
        elif 'month' in col_lower:
            data[col_name] = random.randint(1, 12)
        elif 'year' in col_lower:
            data[col_name] = 2026
        elif 'quarter' in col_lower:
            data[col_name] = random.randint(1, 4)
        elif 'week' in col_lower:
            data[col_name] = random.randint(1, 52)
        elif 'period' in col_lower:
            data[col_name] = random.randint(1, 12)
        elif 'template' in col_lower or 'format' in col_lower or 'layout' in col_lower:
            data[col_name] = 'standard'
        elif 'currency' in col_lower:
            data[col_name] = 'AED'
        elif 'language' in col_lower or 'lang' in col_lower:
            data[col_name] = 'en'
        elif 'timezone' in col_lower:
            data[col_name] = 'Asia/Dubai'
        elif 'theme' in col_lower or 'skin' in col_lower:
            data[col_name] = 'default'
        elif 'icon' in col_lower:
            data[col_name] = 'fa-check'
        elif 'method' in col_lower or 'mode' in col_lower:
            data[col_name] = 'auto'
        elif 'source' in col_lower or 'origin' in col_lower:
            data[col_name] = 'manual'
        elif 'target' in col_lower or 'destination' in col_lower or 'dest' in col_lower:
            data[col_name] = 'default'
        elif 'direction' in col_lower:
            data[col_name] = 'inbound'
        elif 'condition' in col_lower or 'criteria' in col_lower or 'filter' in col_lower:
            data[col_name] = 'default'
        elif 'operator' in col_lower:
            data[col_name] = 'equals'
        elif 'expression' in col_lower or 'formula' in col_lower or 'logic' in col_lower:
            data[col_name] = 'true'
        elif 'query' in col_lower or 'sql' in col_lower or 'statement' in col_lower:
            data[col_name] = 'SELECT 1'
        elif 'schedule' in col_lower or 'cron' in col_lower:
            data[col_name] = '0 0 * * *'
        elif 'timezone' in col_lower:
            data[col_name] = 'Asia/Dubai'
        elif 'offset' in col_lower:
            data[col_name] = '+04:00'
        elif 'unit' in col_lower:
            data[col_name] = 'PCS'
        elif 'uom' in col_lower:
            data[col_name] = 'PCS'
        elif 'brand' in col_lower:
            data[col_name] = 'Generic'
        elif 'model' in col_lower or 'make' in col_lower:
            data[col_name] = 'Standard'
        elif 'serial' in col_lower or 'lot' in col_lower or 'batch' in col_lower:
            data[col_name] = f'LOT-{random.randint(1000, 9999)}'
        elif 'expiry' in col_lower or 'exp' in col_lower:
            data[col_name] = '2027-12-31'
        elif 'start' in col_lower or 'begin' in col_lower:
            data[col_name] = datetime.now().strftime('%Y-%m-%d')
        elif 'end' in col_lower or 'finish' in col_lower or 'close' in col_lower:
            data[col_name] = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        elif 'valid' in col_lower:
            data[col_name] = 'Active'
        elif 'active' in col_lower or 'enabled' in col_lower:
            data[col_name] = 1
        elif 'inactive' in col_lower or 'disabled' in col_lower:
            data[col_name] = 0
        elif 'deleted' in col_lower or 'removed' in col_lower or 'archived' in col_lower:
            data[col_name] = 0
        elif 'approved' in col_lower or 'confirmed' in col_lower or 'verified' in col_lower:
            data[col_name] = 1 if random.random() > 0.3 else 0
        elif 'sent' in col_lower or 'received' in col_lower or 'processed' in col_lower:
            data[col_name] = 0
        elif 'read' in col_lower or 'seen' in col_lower:
            data[col_name] = 0
        elif 'locked' in col_lower or 'encrypted' in col_lower or 'secure' in col_lower:
            data[col_name] = 0
        elif 'hidden' in col_lower or 'visible' in col_lower:
            data[col_name] = 0 if 'hidden' in col_lower else 1
        elif 'required' in col_lower or 'mandatory' in col_lower or ' compulsory' in col_lower:
            data[col_name] = 1
        elif 'optional' in col_lower:
            data[col_name] = 0
        elif 'internal' in col_lower or 'external' in col_lower:
            data[col_name] = 'internal'
        elif 'system' in col_lower or 'auto' in col_lower:
            data[col_name] = 0
        elif 'manual' in col_lower:
            data[col_name] = 1
        elif 'core' in col_lower:
            data[col_name] = 1
        elif 'custom' in col_lower:
            data[col_name] = 0
        elif 'report' in col_lower:
            data[col_name] = 'standard'
        elif 'log' in col_lower:
            data[col_name] = f'Log entry {random.randint(1,100)}'
        elif 'trace' in col_lower or 'debug' in col_lower:
            data[col_name] = 'info'
        elif 'error' in col_lower:
            data[col_name] = 0
        elif 'warning' in col_lower:
            data[col_name] = 0
        elif 'success' in col_lower:
            data[col_name] = 0
        elif 'info' in col_lower:
            data[col_name] = 0
        elif 'browser' in col_lower or 'user_agent' in col_lower:
            data[col_name] = 'Mozilla/5.0'
        elif 'os' in col_lower or 'system' in col_lower:
            data[col_name] = 'Windows'
        elif 'device' in col_lower or 'platform' in col_lower:
            data[col_name] = 'Web'
        elif 'browser' in col_lower:
            data[col_name] = 'Chrome'
        elif 'response' in col_lower or 'result' in col_lower or 'output' in col_lower:
            data[col_name] = 'success'
        elif 'error' in col_lower or 'fail' in col_lower or 'exception' in col_lower:
            data[col_name] = None
        elif 'message' in col_lower or 'msg' in col_lower:
            data[col_name] = f'Message {random.randint(1,100)}'
        elif 'body' in col_lower or 'payload' in col_lower or 'data' in col_lower:
            data[col_name] = '{}'
        elif 'header' in col_lower:
            data[col_name] = 'application/json'
        elif 'size' in col_lower or 'bytes' in col_lower or 'length' in col_lower:
            data[col_name] = random.randint(100, 10000)
        elif 'height' in col_lower or 'width' in col_lower:
            data[col_name] = random.randint(100, 1920)
        elif 'depth' in col_lower:
            data[col_name] = random.randint(1, 10)
        elif 'capacity' in col_lower or 'max' in col_lower or 'limit' in col_lower:
            data[col_name] = random.randint(10, 1000)
        elif 'used' in col_lower or 'current' in col_lower:
            data[col_name] = random.randint(0, 100)
        elif 'available' in col_lower or 'free' in col_lower or 'remaining' in col_lower:
            data[col_name] = random.randint(0, 100)
        elif 'over' in col_lower or 'exceeded' in col_lower or 'surplus' in col_lower:
            data[col_name] = 0
        elif 'warning' in col_lower or 'alert' in col_lower:
            data[col_name] = 0
        elif 'critical' in col_lower:
            data[col_name] = 0
        elif 'info' in col_lower or 'notice' in col_lower:
            data[col_name] = 1
        elif 'success' in col_lower or 'complete' in col_lower:
            data[col_name] = 1
        elif 'failed' in col_lower or 'failure' in col_lower:
            data[col_name] = 0
        elif 'pending' in col_lower:
            data[col_name] = 0
        elif 'cancelled' in col_lower or 'canceled' in col_lower:
            data[col_name] = 0
        elif 'rejected' in col_lower:
            data[col_name] = 0
        elif 'draft' in col_lower:
            data[col_name] = 1
        elif 'final' in col_lower or 'published' in col_lower or 'live' in col_lower:
            data[col_name] = 0
        elif 'test' in col_lower:
            data[col_name] = 0
        elif 'sample' in col_lower:
            data[col_name] = 1
        elif 'demo' in col_lower:
            data[col_name] = 1
        elif 'default' in col_lower:
            data[col_name] = 0 if 'non' in col_lower else 1
        elif 'override' in col_lower:
            data[col_name] = 0
        elif 'inherit' in col_lower:
            data[col_name] = 1
        elif 'null' in col_lower or 'none' in col_lower:
            data[col_name] = None
        elif 'empty' in col_lower or 'blank' in col_lower:
            data[col_name] = 0
        elif 'full' in col_lower:
            data[col_name] = 0
        elif 'partial' in col_lower or 'half' in col_lower:
            data[col_name] = 0
        elif 'complete' in col_lower or 'completed' in col_lower:
            data[col_name] = 0
        elif 'incomplete' in col_lower or 'unfinished' in col_lower:
            data[col_name] = 1
        elif 'processing' in col_lower or 'processing' in col_lower:
            data[col_name] = 0
        elif 'verified' in col_lower:
            data[col_name] = 0
        elif 'unverified' in col_lower:
            data[col_name] = 1
        elif 'locked' in col_lower:
            data[col_name] = 0
        elif 'unlocked' in col_lower:
            data[col_name] = 1
        elif 'expired' in col_lower:
            data[col_name] = 0
        elif 'valid' in col_lower:
            data[col_name] = 1
        elif 'invalid' in col_lower:
            data[col_name] = 0
        elif 'reviewed' in col_lower:
            data[col_name] = 0
        elif 'approved' in col_lower:
            data[col_name] = 0
        elif 'submitted' in col_lower:
            data[col_name] = 0
        elif 'confirmed' in col_lower:
            data[col_name] = 0
        elif 'paid' in col_lower:
            data[col_name] = 0
        elif 'unpaid' in col_lower:
            data[col_name] = 1
        elif 'delivered' in col_lower:
            data[col_name] = 0
        elif 'returned' in col_lower:
            data[col_name] = 0
        elif 'refunded' in col_lower:
            data[col_name] = 0
        elif 'resolved' in col_lower:
            data[col_name] = 0
        elif 'open' in col_lower:
            data[col_name] = 1
        elif 'closed' in col_lower:
            data[col_name] = 0
        elif 'solved' in col_lower:
            data[col_name] = 0
        elif 'unsolved' in col_lower:
            data[col_name] = 1
        else:
            # Generic fallback based on type
            if 'INT' in col_type.upper():
                data[col_name] = random.randint(1, 100)
            elif 'REAL' in col_type.upper() or 'FLOAT' in col_type.upper() or 'DECIMAL' in col_type.upper():
                data[col_name] = round(random.uniform(1, 100), 2)
            elif 'TEXT' in col_type.upper() or 'VARCHAR' in col_type.upper() or 'CHAR' in col_type.upper():
                data[col_name] = f'Sample {col_name}'
            elif 'BLOB' in col_type.upper():
                data[col_name] = None
            elif 'DATE' in col_type.upper() or 'TIME' in col_type.upper():
                data[col_name] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            else:
                data[col_name] = f'value_{random.randint(1,100)}'
    
    return data


def seed_table(db, table):
    """Seed a single empty table."""
    cols_info = get_columns_info(db, table)
    if not cols_info:
        return 0
    
    if count_rows(db, table) > 0:
        return 0
    
    data = generate_row(db, table, cols_info)
    if not data:
        return 0
    
    # Filter to only columns that exist
    valid_cols = [c[0] for c in cols_info]
    filtered_data = {k: v for k, v in data.items() if k in valid_cols}
    
    if not filtered_data:
        return 0
    
    placeholders = ', '.join(['?'] * len(filtered_data))
    col_names = ', '.join(filtered_data.keys())
    
    try:
        db.execute(f"INSERT INTO [{table}] ({col_names}) VALUES ({placeholders})",
                   list(filtered_data.values()))
        return 1
    except Exception as e:
        # Try with minimal columns only
        minimal = {k: v for k, v in filtered_data.items() 
                  if k == 'created_at' or 'name' in k.lower() or 'code' in k.lower()}
        if minimal:
            try:
                placeholders = ', '.join(['?'] * len(minimal))
                col_names = ', '.join(minimal.keys())
                db.execute(f"INSERT INTO [{table}] ({col_names}) VALUES ({placeholders})",
                           list(minimal.values()))
                return 1
            except:
                pass
        return 0


def main():
    print("=" * 70)
    print("  MMDx AGGRESSIVE MINIMAL SEEDER")
    print("  Filling ALL Empty Tables")
    print("=" * 70)
    print()
    
    db = get_db()
    
    cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    seeded = 0
    errors = []
    
    for table in all_tables:
        if count_rows(db, table) > 0:
            continue
        
        result = seed_table(db, table)
        if result > 0:
            print(f"  + {table}")
            seeded += 1
        else:
            errors.append(table)
    
    db.commit()
    db.close()
    
    print()
    if errors:
        print(f"  Could not seed ({len(errors)} tables):")
        for t in errors[:20]:
            print(f"    - {t}")
        if len(errors) > 20:
            print(f"    ... and {len(errors) - 20} more")
    print()
    print("=" * 70)
    print(f"  SEEDED: {seeded} tables")
    print("=" * 70)


if __name__ == '__main__':
    main()
