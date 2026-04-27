import sqlite3
import os

# Use exact path
DATABASE = r'C:\Users\sdads\WHDASH\warehouse.db'

conn = sqlite3.connect(DATABASE)
conn.row_factory = sqlite3.Row

# Check if investment_requests table exists
cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='investment_requests'")
if cur.fetchone():
    print("investment_requests table EXISTS")
else:
    print("investment_requests table DOES NOT EXIST")

# Check if departments table exists
cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='departments'")
if cur.fetchone():
    print("departments table EXISTS")
else:
    print("departments table DOES NOT EXIST")

# Try to query investment_requests
try:
    count = conn.execute("SELECT COUNT(*) FROM investment_requests").fetchone()[0]
    print(f"investment_requests has {count} rows")
except Exception as e:
    print(f"Error querying investment_requests: {e}")

conn.close()
