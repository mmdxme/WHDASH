"""
Delete customers with Persian/Farsi names from sdad_customers table.
Persian characters range: \u0600-\u06FF (Arabic block) including Persian-specific chars
"""
import re
import sqlite3
import os

# Persian/Farsi character pattern
PERSIAN_PATTERN = re.compile(r'[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]+')

def has_persian(text):
    """Check if text contains any Persian/Arabic characters."""
    if not text:
        return False
    return bool(PERSIAN_PATTERN.search(text))

def safe_str(s):
    """Convert string to ascii-safe representation."""
    if s is None:
        return ''
    return str(s).encode('ascii', 'backslashreplace').decode('ascii')

def main():
    db_path = os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'warehouse.db'))
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Find all customers with Persian names
    cursor.execute("SELECT id, customer_id, name FROM sdad_customers")
    all_customers = cursor.fetchall()

    persian_customers = []
    for cust_id, customer_code, name in all_customers:
        if has_persian(name):
            persian_customers.append((cust_id, customer_code, name))

    print(f"Found {len(persian_customers)} customers with Persian names:")
    for cust_id, customer_code, name in persian_customers:
        print(f"  ID: {cust_id}, Code: {safe_str(customer_code)}, Name: {safe_str(name)}")

    if not persian_customers:
        print("No Persian customers found.")
        conn.close()
        return

    confirm = input(f"\nDelete {len(persian_customers)} customers? (yes/no): ")
    if confirm.lower() == 'yes':
        customer_ids = [c[0] for c in persian_customers]
        placeholders = ','.join('?' * len(customer_ids))
        cursor.execute(f"DELETE FROM sdad_customers WHERE id IN ({placeholders})", customer_ids)
        conn.commit()
        print(f"Deleted {cursor.rowcount} customers.")
    else:
        print("Aborted.")

    conn.close()

if __name__ == '__main__':
    main()
