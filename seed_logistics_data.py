"""
Seed Logistics/Delivery Demo Data
==================================
Seeds realistic logistics data for testing and demonstration.
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

DATABASE = os.path.join(os.path.dirname(__file__), 'warehouse.db')


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def seed_logistics_data():
    """Seed comprehensive logistics/delivery demo data."""
    conn = get_db()
    cursor = conn.cursor()

    print("Seeding logistics/delivery demo data...")

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) as cnt FROM logistics_vehicles")
    if cursor.fetchone()['cnt'] > 0:
        print("Logistics data already exists, skipping...")
        conn.close()
        return

    # Seed Vehicles
    print("  Creating vehicles...")
    vehicles = [
        ('VH-001', 'Toyota Hiace', 'White', 'ABC-1234', 2021, 15000, 'Active', 5000),
        ('VH-002', 'Mitsubishi Fuso', 'Silver', 'ABC-1235', 2020, 28000, 'Active', 8000),
        ('VH-003', 'Isuzu NPR', 'Blue', 'ABC-1236', 2022, 12000, 'Active', 6000),
        ('VH-004', 'Ford Transit', 'Black', 'ABC-1237', 2021, 35000, 'Active', 10000),
        ('VH-005', 'Nissan Urvan', 'Grey', 'ABC-1238', 2020, 45000, 'Active', 12000),
        ('VH-006', 'Hyundai H-1', 'White', 'ABC-1239', 2023, 8000, 'Active', 4000),
        ('VH-007', 'Mercedes Sprinter', 'Grey', 'ABC-1240', 2021, 55000, 'Active', 15000),
        ('VH-008', 'Toyota Dyna', 'Orange', 'ABC-1241', 2019, 70000, 'Maintenance', 0),
    ]

    for code, model, color, plate, year, mileage, status, capacity in vehicles:
        cursor.execute(
            """INSERT INTO logistics_vehicles (vehicle_code, vehicle_type, model_name, license_plate, 
                registration_expiry, insurance_expiry, status, current_mileage, fuel_type, 
                fuel_capacity, average_consumption, next_service_date, is_active) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (code, 'Van', model, plate, '2027-03-31', '2026-03-31', status, mileage, 
             random.choice(['Petrol', 'Diesel', 'Hybrid']), 80, random.uniform(8, 15), 
             (datetime.now() + timedelta(days=random.randint(30, 90))).strftime('%Y-%m-%d'), 1)
        )

    # Seed Drivers
    print("  Creating drivers...")
    drivers = [
        ('DR-001', 'Ahmed Al Rashid', 'UAE', 'DL-001234', '+971-50-123-4567', 5, 1),
        ('DR-002', 'Khalid Mohammed', 'UAE', 'DL-001235', '+971-50-234-5678', 8, 1),
        ('DR-003', 'Omar Hassan', 'UAE', 'DL-001236', '+971-50-345-6789', 3, 1),
        ('DR-004', 'Fahad Al Kaabi', 'UAE', 'DL-001237', '+971-50-456-7890', 12, 1),
        ('DR-005', 'Majid Al Sayed', 'UAE', 'DL-001238', '+971-50-567-8901', 6, 1),
        ('DR-006', 'Ali Hassan', 'UAE', 'DL-001239', '+971-50-678-9012', 4, 1),
        ('DR-007', 'Rashid Al Maktoum', 'UAE', 'DL-001240', '+971-50-789-0123', 7, 0),
        ('DR-008', 'Salem Al Qasimi', 'UAE', 'DL-001241', '+971-50-890-1234', 9, 1),
    ]

    for code, name, nationality, license, phone, exp_years, is_active in drivers:
        cursor.execute(
            """INSERT INTO logistics_drivers (driver_code, driver_name, nationality, 
                license_number, phone, years_experience, status, is_active,
                emergency_contact_name, emergency_contact_phone, date_of_birth, home_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (code, name, nationality, license, phone, exp_years, 
             'Active' if is_active else 'On Leave',
             is_active, 'Emergency Contact', '+971-50-000-0000',
             (datetime.now() - timedelta(days=random.randint(7300, 14000))).strftime('%Y-%m-%d'),
             'Dubai, UAE')
        )

    # Seed Routes
    print("  Creating routes...")
    routes = [
        ('RT-001', 'Dubai Central', 'Central Dubai Area', 45, 90),
        ('RT-002', 'Dubai Deira', 'Deira and Surrounds', 30, 60),
        ('RT-003', 'Dubai Marina', 'Marina and JBR', 55, 75),
        ('RT-004', 'Sharjah Route', 'Sharjah Industrial', 40, 70),
        ('RT-005', 'Abu Dhabi Express', 'Abu Dhabi City', 150, 180),
        ('RT-006', 'Al Ain Route', 'Al Ain Region', 120, 150),
        ('RT-007', 'Northern Emirates', 'RAK, Fujairah', 180, 240),
        ('RT-008', 'Dubai Silicon Oasis', 'DSO and Surrounds', 35, 55),
    ]

    for code, name, desc, distance, duration in routes:
        cursor.execute(
            """INSERT INTO logistics_route_masters (route_code, route_name, description, 
                distance_km, estimated_time_minutes, cost_per_km, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (code, name, desc, distance, duration, random.uniform(2.5, 5.0), 1)
        )

    # Seed Delivery Trips
    print("  Creating delivery trips...")
    today = datetime.now().date()
    
    # Get drivers and vehicles
    cursor.execute("SELECT id FROM logistics_drivers WHERE is_active = 1 LIMIT 8")
    driver_ids = [r['id'] for r in cursor.fetchall()]
    cursor.execute("SELECT id FROM logistics_vehicles WHERE status = 'Active' LIMIT 8")
    vehicle_ids = [r['id'] for r in cursor.fetchall()]

    statuses = ['At Warehouse', 'Loading', 'Active', 'Completed', 'Completed', 'Completed']
    trip_count = 0
    
    for day_offset in range(-7, 1):
        trip_date = today - timedelta(days=day_offset)
        num_trips = random.randint(3, 6)
        
        for t in range(num_trips):
            if not driver_ids or not vehicle_ids:
                break
            driver_id = random.choice(driver_ids)
            vehicle_id = random.choice(vehicle_ids)
            status = random.choice(statuses)
            
            warehouse_checkin = None
            warehouse_departure = None
            warehouse_arrival = None
            
            if status in ['At Warehouse', 'Loading']:
                warehouse_checkin = datetime.combine(trip_date, datetime.now().time().replace(hour=7, minute=0))
            elif status == 'Active':
                warehouse_checkin = datetime.combine(trip_date, datetime.strptime('07:00', '%H:%M'))
                warehouse_departure = datetime.combine(trip_date, datetime.strptime('08:30', '%H:%M'))
            elif status == 'Completed':
                warehouse_checkin = datetime.combine(trip_date, datetime.strptime('06:30', '%H:%M'))
                warehouse_departure = datetime.combine(trip_date, datetime.strptime('07:45', '%H:%M'))
                warehouse_arrival = datetime.combine(trip_date, datetime.strptime('17:00', '%H:%M'))
            
            cursor.execute(
                """INSERT INTO delivery_trips (driver_id, vehicle_id, date, status, 
                    warehouse_checkin, warehouse_departure, warehouse_arrival)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (driver_id, vehicle_id, trip_date.strftime('%Y-%m-%d'), status,
                 warehouse_checkin.isoformat() if warehouse_checkin else None,
                 warehouse_departure.isoformat() if warehouse_departure else None,
                 warehouse_arrival.isoformat() if warehouse_arrival else None)
            )
            trip_count += 1

    # Seed delivery stops for completed trips
    print("  Creating delivery stops...")
    cursor.execute("SELECT id FROM delivery_trips WHERE status = 'Completed' LIMIT 10")
    completed_trips = [r['id'] for r in cursor.fetchall()]
    
    cursor.execute("SELECT id, name FROM sdad_customers LIMIT 20")
    customers = list(cursor.fetchall())
    
    for trip_id in completed_trips:
        num_stops = random.randint(3, 7)
        for seq in range(num_stops):
            if not customers:
                break
            cust = random.choice(customers)
            arrival = datetime.now() - timedelta(hours=random.randint(1, 48))
            departure = arrival + timedelta(minutes=random.randint(10, 45))
            
            cursor.execute(
                """INSERT INTO delivery_stops (trip_id, customer_id, sequence_order, 
                    status, arrival_time, departure_time)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (trip_id, cust['id'], seq + 1, 'Departed',
                 arrival.isoformat(), departure.isoformat())
            )
            
            # Add activity log for each stop
            cursor.execute(
                """INSERT INTO delivery_activity_logs (trip_id, customer_id, activity_type, timestamp, notes)
                VALUES (?, ?, 'Arrival at Customer', ?, ?)""",
                (trip_id, cust['id'], arrival.isoformat(), f"Arrived at {cust['name']}")
            )
            cursor.execute(
                """INSERT INTO delivery_activity_logs (trip_id, customer_id, activity_type, timestamp, notes)
                VALUES (?, ?, 'Departure from Customer', ?, ?)""",
                (trip_id, cust['id'], departure.isoformat(), f"Left {cust['name']}")
            )

    conn.commit()
    print(f"Successfully seeded logistics data: {trip_count} trips, {len(vehicles)} vehicles, {len(drivers)} drivers, {len(routes)} routes")
    conn.close()


if __name__ == '__main__':
    seed_logistics_data()