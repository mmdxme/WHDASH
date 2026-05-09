"""
Minimal Data Seeder - Fills ALL Empty Tables with Minimal Data
============================================================
This script adds just 1-3 rows to each empty table to eliminate empty states.
It is completely safe and only inserts if table is empty.

Usage:
    python seed_minimal.py
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
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def get_columns(db, table):
    try:
        cursor = db.execute(f"PRAGMA table_info([{table}])")
        return {row[1]: row[2] for row in cursor.fetchall()}  # name: type
    except:
        return {}


def count_rows(db, table):
    try:
        return db.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
    except:
        return 0


def get_any_value(db, table, column):
    try:
        result = db.execute(f"SELECT {column} FROM [{table}] LIMIT 1").fetchone()
        return result[0] if result else None
    except:
        return None


def get_first_id(db, table):
    try:
        result = db.execute(f"SELECT id FROM [{table}] LIMIT 1").fetchone()
        return result['id'] if result and 'id' in result.keys() else 1
    except:
        try:
            result = db.execute(f"SELECT id FROM [{table}] LIMIT 1").fetchone()
            return result[0] if result else 1
        except:
            return 1


def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def days_ago(n):
    return (datetime.now() - timedelta(days=n)).strftime('%Y-%m-%d')


def generate_minimal_row(db, table, columns):
    """Generate minimal row data based on actual columns."""
    data = {}
    
    for col, col_type in columns.items():
        if col in ['id', 'created_at', 'updated_at', 'timestamp']:
            continue
        
        # Handle common column patterns
        col_lower = col.lower()
        
        if 'name' in col_lower:
            data[col] = f'{table.replace("_", " ").title()} Sample'
        elif 'code' in col_lower:
            data[col] = f'{col[:3].upper()}-{random.randint(1000, 9999)}'
        elif 'number' in col_lower:
            data[col] = f'NUM-{random.randint(10000, 99999)}'
        elif 'status' in col_lower:
            data[col] = 'Active'
        elif 'type' in col_lower:
            data[col] = 'General'
        elif 'date' in col_lower:
            data[col] = days_ago(random.randint(1, 30))
        elif 'amount' in col_lower or 'price' in col_lower or 'total' in col_lower:
            data[col] = random.uniform(100, 10000)
        elif 'quantity' in col_lower or 'qty' in col_lower:
            data[col] = random.randint(1, 100)
        elif 'rate' in col_lower or 'percentage' in col_lower or 'ratio' in col_lower:
            data[col] = random.uniform(0.1, 10.0)
        elif 'email' in col_lower:
            data[col] = f'sample{random.randint(1, 100)}@example.com'
        elif 'phone' in col_lower or 'mobile' in col_lower:
            data[col] = f'+97150{random.randint(1000000, 9999999)}'
        elif 'address' in col_lower or 'location' in col_lower:
            data[col] = f'Address {random.randint(1, 999)}, Dubai, UAE'
        elif 'description' in col_lower or 'notes' in col_lower or 'remark' in col_lower:
            data[col] = f'Sample {col} for testing'
        elif 'password' in col_lower or 'hash' in col_lower:
            data[col] = 'placeholder_hash'
        elif 'token' in col_lower:
            data[col] = f'token_{random.randint(100000, 999999)}'
        elif 'url' in col_lower or 'link' in col_lower:
            data[col] = f'https://example.com/{random.randint(1, 100)}'
        elif 'image' in col_lower or 'photo' in col_lower or 'avatar' in col_lower:
            data[col] = '/static/uploads/avatar.png'
        elif 'is_' in col_lower or 'has_' in col_lower or 'can_' in col_lower:
            data[col] = random.choice([0, 1, 'Yes', 'No'])
        elif 'flag' in col_lower:
            data[col] = 0
        elif 'color' in col_lower:
            data[col] = '#' + ''.join([random.choice('0123456789ABCDEF') for _ in range(6)])
        elif 'ip' in col_lower:
            data[col] = f'192.168.1.{random.randint(1, 255)}'
        elif col_type == 'INTEGER' or col_type == 'REAL':
            if 'id' not in col_lower:
                data[col] = random.randint(1, 100)
        elif col_type == 'TEXT':
            data[col] = f'Sample text {random.randint(1, 100)}'
        else:
            # Try to make it a string
            data[col] = f'Value_{random.randint(1, 100)}'
    
    # Add created_at if exists
    if 'created_at' in columns:
        data['created_at'] = now()
    
    return data


def seed_table(db, table):
    """Seed a single empty table with minimal data."""
    cols = get_columns(db, table)
    if not cols:
        return 0
    
    if count_rows(db, table) > 0:
        return 0
    
    data = generate_minimal_row(db, table, cols)
    if not data:
        return 0
    
    placeholders = ', '.join(['?'] * len(data))
    col_names = ', '.join(data.keys())
    
    try:
        db.execute(f"INSERT INTO [{table}] ({col_names}) VALUES ({placeholders})",
                   list(data.values()))
        return 1
    except Exception as e:
        # Try with fewer columns
        essential = {k: v for k, v in data.items() 
                    if 'id' not in k.lower() and 'foreign' not in k.lower()}
        if essential:
            try:
                placeholders = ', '.join(['?'] * len(essential))
                col_names = ', '.join(essential.keys())
                db.execute(f"INSERT INTO [{table}] ({col_names}) VALUES ({placeholders})",
                           list(essential.values()))
                return 1
            except:
                pass
        return 0


def main():
    print("=" * 70)
    print("  MMDx MINIMAL DATA SEEDER")
    print("  Filling ALL Empty Tables with Minimal Sample Data")
    print("=" * 70)
    print()
    
    db = get_db()
    
    # Get all tables
    cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    seeded = 0
    total = 0
    
    for table in all_tables:
        count_before = count_rows(db, table)
        if count_before > 0:
            continue
        
        inserted = seed_table(db, table)
        if inserted > 0:
            print(f"  + {table}")
            seeded += 1
            total += inserted
    
    db.commit()
    db.close()
    
    print()
    print("=" * 70)
    print(f"  SEEDED: {seeded} tables with minimal data")
    print("=" * 70)


if __name__ == '__main__':
    main()
