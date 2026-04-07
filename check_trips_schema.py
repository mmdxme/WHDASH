from database import get_db

db = get_db()

# Check delivery_trips schema
print("=== delivery_trips schema ===")
result = db.execute("PRAGMA table_info(delivery_trips)").fetchall()
for r in result:
    print(f"  {r['name']}: {r['type']}")

# Check logistics_drivers schema
print("\n=== logistics_drivers schema ===")
result = db.execute("PRAGMA table_info(logistics_drivers)").fetchall()
for r in result:
    print(f"  {r['name']}: {r['type']}")

# Check logistics_vehicles schema
print("\n=== logistics_vehicles schema ===")
result = db.execute("PRAGMA table_info(logistics_vehicles)").fetchall()
for r in result:
    print(f"  {r['name']}: {r['type']}")

# Try the exact query from trips_list
print("\n=== Testing trips query ===")
try:
    query = """
        SELECT t.*, d.full_name as driver_name, v.plate_number, v.vehicle_type
        FROM delivery_trips t
        LEFT JOIN logistics_drivers d ON t.driver_id = d.id
        LEFT JOIN logistics_vehicles v ON t.vehicle_id = v.id
        WHERE 1=1
        ORDER BY t.date DESC, t.id DESC
        LIMIT 20
    """
    trips = db.execute(query).fetchall()
    print(f"Success! Found {len(trips)} trips")
    if trips:
        print(f"Columns: {trips[0].keys()}")
except Exception as e:
    print(f"Error: {e}")

db.close()
