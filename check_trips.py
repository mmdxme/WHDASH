from database import get_db

db = get_db()

# Check what logistics tables exist
result = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'logistics_%'").fetchall()
print("Logistics tables:")
for r in result:
    print(f"  - {r['name']}")

# Check if delivery_trips exists
result2 = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = 'delivery_trips'").fetchone()
print(f"\ndelivery_trips exists: {result2 is not None}")

# Check if trips table exists (different naming)
result3 = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = 'trips'").fetchone()
print(f"trips exists: {result3 is not None}")

db.close()
