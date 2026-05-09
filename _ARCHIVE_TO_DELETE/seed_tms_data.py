"""
TMS Data Seeder for WHDASH
Populates the database with realistic TMS data for testing and demo purposes.
Must be idempotent - safe to run multiple times.
"""

import sqlite3
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class TMSSSeeder:
    def __init__(self, db_path: str = 'warehouse.db'):
        self.db_path = db_path
        self.vehicle_ids: List[int] = []
        self.driver_ids: List[int] = []
        self.route_ids: List[int] = []
        self.trip_ids: List[int] = []
        self.shipment_ids: List[int] = []
        self.pod_ids: List[int] = []
        self.cost_ids: List[int] = []
        self.incident_ids: List[int] = []
        self.schedule_ids: List[int] = []
        self.checkpoint_ids: List[int] = []
        self.kpi_ids: List[int] = []
        self.document_ids: List[int] = []

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def clear_existing_tms_data(self):
        """Remove existing TMS data to ensure idempotency."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        tables = [
            'logistics_transport_documents', 'logistics_fleet_kpis', 'logistics_stop_checkpoints',
            'logistics_delivery_schedules', 'logistics_incidents', 'logistics_cost_entries', 'logistics_pod_records',
            'logistics_shipments', 'logistics_trips', 'logistics_route_masters', 'logistics_drivers', 'logistics_vehicles'
        ]
        
        for table in tables:
            try:
                cursor.execute(f'DELETE FROM {table}')
            except sqlite3.OperationalError:
                pass
        
        conn.commit()
        conn.close()

    def seed_vehicles(self, count: int = 15) -> List[int]:
        """Create vehicles with realistic data."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        vehicle_types = ['Semi Truck', 'Box Truck', 'Van', 'Flatbed', 'Tanker']
        statuses = ['active', 'active', 'active', 'maintenance', 'inactive']
        fuel_types = ['Diesel', 'Gasoline', 'Electric', 'Hybrid']
        
        vehicles = []
        for i in range(1, count + 1):
            # Generate realistic plate numbers like ABC-1234
            letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            plate = f'{random.choice(letters)}{random.choice(letters)}{random.choice(letters)}-{random.randint(1000, 9999)}'
            vehicles.append((
                f'VH-{1000 + i:04d}',      # vehicle_code
                plate,                      # plate_number
                random.choice(vehicle_types),  # vehicle_type
                'Toyota',                   # brand
                f'Model-{random.randint(1, 9)}',  # model
                random.randint(2018, 2024),  # year
                f'VIN-{random.randint(100000000, 999999999)}',  # vin_number
                random.choice(statuses),     # status
                random.randint(50000, 500000),  # odometer_reading
                random.choice(fuel_types),    # fuel_type
                random.randint(5000, 20000),  # load_capacity_kg (kg not tons)
                1,                          # branch_id
                datetime.now().isoformat(),  # created_at
                datetime.now().isoformat()   # updated_at
            ))
        
        cursor.executemany('''
            INSERT OR REPLACE INTO logistics_vehicles 
            (vehicle_code, plate_number, vehicle_type, brand, model, year, 
             vin_number, status, odometer_reading, fuel_type, load_capacity_kg, 
             branch_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', vehicles)
        
        conn.commit()
        cursor.execute('SELECT id FROM logistics_vehicles ORDER BY id')
        self.vehicle_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        return self.vehicle_ids

    def seed_drivers(self, count: int = 20) -> List[int]:
        """Create drivers with realistic data."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        first_names = ['James', 'Michael', 'Robert', 'David', 'William', 
                       'Maria', 'Sarah', 'Jennifer', 'Linda', 'Patricia',
                       'Carlos', 'Miguel', 'Ahmed', 'Ali', 'Wei', 'Raj']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones',
                       'Garcia', 'Martinez', 'Chen', 'Patel', 'Singh']
        licenses = ['Class A CDL', 'Class B CDL', 'Class C CDL', 'Hazmat']
        statuses = ['available', 'available', 'available', 'on_trip', 'off_duty']
        
        drivers = []
        for i in range(1, count + 1):
            fname = random.choice(first_names)
            lname = random.choice(last_names)
            full_name = f'{fname} {lname}'
            drivers.append((
                f'DR-{1000 + i:04d}',           # driver_code
                full_name,                      # full_name
                f'+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}',  # mobile
                random.choice(licenses),         # license_class
                f'Lic-{random.randint(100000, 999999)}',  # license_number
                (datetime.now().date() + timedelta(days=random.randint(365, 1825))).isoformat(),  # license_expiry
                random.choice(statuses),         # status
                1,                              # branch_id
                datetime.now().isoformat(),      # created_at
                datetime.now().isoformat()       # updated_at
            ))
        
        cursor.executemany('''
            INSERT OR REPLACE INTO logistics_drivers
            (driver_code, full_name, mobile, license_class,
             license_number, license_expiry, status, branch_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', drivers)
        
        conn.commit()
        cursor.execute('SELECT id FROM logistics_drivers ORDER BY id')
        self.driver_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        return self.driver_ids

    def seed_routes(self, count: int = 10) -> List[int]:
        """Create routes with realistic data."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cities = ['Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia',
                  'San Antonio', 'San Diego', 'Dallas', 'San Jose', 'Austin']
        route_types = ['intercity', 'local', 'regional', 'long_haul']
        
        routes = []
        for i in range(1, count + 1):
            origin = random.choice(cities)
            dest = random.choice([c for c in cities if c != origin])
            routes.append((
                f'RT-{1000 + i:04d}',           # route_code
                f'{origin} to {dest}',         # route_name
                f'Route from {origin} to {dest}',  # description
                random.randint(100, 2000),      # distance_km
                random.randint(120, 2880),      # estimated_time_minutes (2-48 hours converted to minutes)
                random.uniform(1.5, 4.5),       # cost_per_km
                1,                              # is_active
                1,                              # branch_id
                datetime.now().isoformat(),      # created_at
                datetime.now().isoformat()       # updated_at
            ))
        
        cursor.executemany('''
            INSERT OR REPLACE INTO logistics_route_masters
            (route_code, route_name, description, distance_km, estimated_time_minutes,
             cost_per_km, is_active, branch_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', routes)
        
        conn.commit()
        cursor.execute('SELECT id FROM logistics_route_masters ORDER BY id')
        self.route_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        return self.route_ids

    def seed_trips(self, count: int = 30) -> List[int]:
        """Create trips with realistic data."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        statuses = ['scheduled', 'in_progress', 'completed', 'cancelled']
        priorities = ['low', 'medium', 'high', 'urgent']
        
        trips = []
        for i in range(1, count + 1):
            status = random.choice(statuses)
            start_date = datetime.now() - timedelta(days=random.randint(-10, 30))
            end_date = start_date + timedelta(hours=random.randint(4, 72))
            
            trips.append((
                f'TR-{1000 + i:04d}',           # trip_code
                f'Trip {i}',                    # trip_name
                status,                         # status
                random.choice(priorities),      # priority
                random.choice(self.route_ids) if self.route_ids else None,  # route_id
                random.choice(self.vehicle_ids) if self.vehicle_ids else None,  # vehicle_id
                random.choice(self.driver_ids) if self.driver_ids else None,  # driver_id
                None,                           # helper_id
                start_date.isoformat(),         # planned_departure
                end_date.isoformat(),           # planned_arrival
                start_date.isoformat() if status in ['in_progress', 'completed'] else None,  # actual_departure
                end_date.isoformat() if status == 'completed' else None,  # actual_arrival
                random.randint(100, 5000),     # total_weight_kg
                random.randint(1000, 10000),    # estimated_cost
                random.randint(1000, 10000),    # actual_cost
                random.randint(100, 1000),     # fuel_cost
                random.randint(50, 500),       # tolls_cost
                random.randint(50, 300),        # driver_allowance
                f'Trip notes for TR-{1000 + i:04d}',  # notes
                1,                              # branch_id
                datetime.now().isoformat(),      # created_at
                datetime.now().isoformat()       # updated_at
            ))
        
        cursor.executemany('''
            INSERT OR REPLACE INTO logistics_trips
            (trip_code, trip_name, status, priority, route_id, vehicle_id, driver_id, helper_id,
             planned_departure, planned_arrival, actual_departure, actual_arrival,
             total_weight_kg, estimated_cost, actual_cost, fuel_cost, tolls_cost, driver_allowance,
             notes, branch_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', trips)
        
        conn.commit()
        cursor.execute('SELECT id FROM logistics_trips ORDER BY id')
        self.trip_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        return self.trip_ids

    def seed_shipments(self, count: int = 40) -> List[int]:
        """Create shipments with realistic data."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        statuses = ['pending', 'picked_up', 'in_transit', 'delivered', 'returned']
        priorities = ['standard', 'express', 'overnight', 'economy']
        
        shipments = []
        for i in range(1, count + 1):
            shipments.append((
                f'SH-{1000 + i:04d}',
                random.choice(self.trip_ids) if self.trip_ids else None,
                f'Customer-{random.randint(1, 50)}',
                f'Sender-{random.randint(1, 50)}',
                random.choice(['Warehouse A', 'Warehouse B', 'Warehouse C']),
                random.choice(['Store 1', 'Store 2', 'Store 3', 'Customer Site']),
                random.choice(statuses),
                random.choice(priorities),
                datetime.now() + timedelta(days=random.randint(1, 14)),
                random.randint(1, 500),  # weight kg
                random.randint(1, 100),  # packages
                f'REF-{random.randint(100000, 999999)}',
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
        
        cursor.executemany('''
            INSERT OR REPLACE INTO logistics_shipments
            (tracking_number, trip_id, receiver_name, sender_name, pickup_location,
             delivery_location, status, priority, due_date, weight_kg, packages,
             reference, branch_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', shipments)
        
        conn.commit()
        cursor.execute('SELECT id FROM logistics_shipments ORDER BY id')
        self.shipment_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        return self.shipment_ids

    def seed_pod_records(self, count: int = 25) -> List[int]:
        """Create POD (Proof of Delivery) records."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        statuses = ['pending', 'signed', 'photo', 'partial', 'rejected']
        signees = ['John Smith', 'Jane Doe', 'Mike Johnson', 'Sarah Williams',
                   'Receiving Dock', 'Front Desk', 'Security Gate', 'Self-Service']
        
        pods = []
        for i in range(1, count + 1):
            status = random.choice(statuses)
            delivery_time = datetime.now() - timedelta(days=random.randint(0, 30))
            
            pods.append((
                f'POD-{1000 + i:04d}',
                random.choice(self.trip_ids) if self.trip_ids else None,
                random.choice(self.shipment_ids) if self.shipment_ids else None,
                status,
                delivery_time.isoformat() if status != 'pending' else None,
                random.choice(signees) if status in ['signed', 'partial'] else None,
                f'Signature data for {i}' if status == 'signed' else None,
                random.randint(1, 5),  # rating
                f'Notes for delivery {i}' if random.random() > 0.5 else None,
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
        
        cursor.executemany('''
            INSERT OR REPLACE INTO logistics_pod_records
            (pod_number, trip_id, shipment_id, status, delivery_time, signee_name,
             signature_data, rating, notes, branch_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', pods)
        
        conn.commit()
        cursor.execute('SELECT id FROM pod_records ORDER BY id')
        self.pod_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        return self.pod_ids

    def seed_cost_entries(self, count: int = 30) -> List[int]:
        """Create cost entries for trips."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cost_types = ['fuel', 'toll', 'parking', 'maintenance', 'driver_bonus', 'insurance', 'depreciation']
        
        costs = []
        for i in range(1, count + 1):
            costs.append((
                f'TR-{random.choice(self.trip_ids) if self.trip_ids else 1}',
                random.choice(cost_types),
                random.uniform(50, 2000),
                datetime.now() - timedelta(days=random.randint(0, 60)),
                f'Invoice-{random.randint(1000, 9999)}',
                f'Cost entry {i} notes',
                random.choice(['pending', 'approved', 'rejected']),
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
        
        cursor.executemany('''
            INSERT OR REPLACE INTO logistics_cost_entries
            (trip_id, cost_type, amount, date, invoice_number, notes, 
             status, branch_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', costs)
        
        conn.commit()
        cursor.execute('SELECT id FROM logistics_cost_entries ORDER BY id')
        self.cost_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        return self.cost_ids

    def seed_incidents(self, count: int = 15) -> List[int]:
        """Create incidents/delays."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        incident_types = ['delay', 'breakdown', 'accident', 'weather', 'traffic', 'mechanical']
        severities = ['low', 'medium', 'high', 'critical']
        statuses = ['open', 'investigating', 'resolved', 'closed']
        
        incidents = []
        for i in range(1, count + 1):
            incidents.append((
                f'INC-{1000 + i:04d}',
                random.choice(self.trip_ids) if self.trip_ids else None,
                random.choice(incident_types),
                random.choice(severities),
                random.choice(statuses),
                datetime.now() - timedelta(days=random.randint(0, 30)),
                datetime.now() + timedelta(days=random.randint(0, 7)) if random.random() > 0.5 else None,
                f'Description for incident {i}',
                f'Resolution notes {i}' if random.random() > 0.5 else None,
                random.randint(0, 5000),  # delay minutes
                random.randint(0, 10000),  # estimated cost
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
        
        cursor.executemany('''
            INSERT OR REPLACE INTO logistics_incidents
            (incident_code, trip_id, incident_type, severity, status, 
             reported_at, resolved_at, description, resolution, 
             delay_minutes, estimated_cost, branch_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', incidents)
        
        conn.commit()
        cursor.execute('SELECT id FROM logistics_incidents ORDER BY id')
        self.incident_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        return self.incident_ids

    def seed_delivery_schedules(self, count: int = 20) -> List[int]:
        """Create delivery schedules."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        statuses = ['scheduled', 'in_progress', 'completed', 'missed']
        
        schedules = []
        for i in range(1, count + 1):
            scheduled_date = datetime.now() + timedelta(days=random.randint(-5, 14))
            schedules.append((
                f'SCH-{1000 + i:04d}',
                random.choice(self.trip_ids) if self.trip_ids else None,
                random.choice(self.shipment_ids) if self.shipment_ids else None,
                f'Location-{random.randint(1, 30)}',
                scheduled_date.isoformat(),
                scheduled_date + timedelta(hours=random.randint(1, 4)),
                random.choice(statuses),
                f'Schedule {i} notes',
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
        
        cursor.executemany('''
            INSERT OR REPLACE INTO logistics_delivery_schedules
            (schedule_code, trip_id, shipment_id, location, scheduled_start,
             scheduled_end, status, notes, branch_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', schedules)
        
        conn.commit()
        cursor.execute('SELECT id FROM logistics_delivery_schedules ORDER BY id')
        self.schedule_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        return self.schedule_ids

    def seed_stop_checkpoints(self, count: int = 50) -> List[int]:
        """Create stop checkpoints for route tracking."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        checkpoint_types = ['pickup', 'delivery', 'rest_stop', 'fuel', 'checkpoint', 'customs']
        statuses = ['pending', 'arrived', 'completed', 'skipped']
        
        checkpoints = []
        for i in range(1, count + 1):
            status = random.choice(statuses)
            arrival = datetime.now() - timedelta(days=random.randint(0, 20)) if status != 'pending' else None
            
            checkpoints.append((
                f'CP-{1000 + i:04d}',
                random.choice(self.trip_ids) if self.trip_ids else None,
                f'Stop-{random.randint(1, 50)}',
                random.choice(checkpoint_types),
                f'Location {random.randint(1, 100)}',
                arrival,
                arrival + timedelta(minutes=random.randint(15, 120)) if status == 'completed' else None,
                status,
                f'Checkpoint {i} notes' if random.random() > 0.5 else None,
                random.randint(0, 100),  # odometer reading
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
        
        cursor.executemany('''
            INSERT OR REPLACE INTO logistics_stop_checkpoints
            (checkpoint_code, trip_id, stop_name, checkpoint_type, location,
             arrival_time, departure_time, status, notes, odometer_reading,
             branch_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', checkpoints)
        
        conn.commit()
        cursor.execute('SELECT id FROM logistics_stop_checkpoints ORDER BY id')
        self.checkpoint_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        return self.checkpoint_ids

    def seed_fleet_kpis(self, count: int = 30) -> List[int]:
        """Create fleet KPI records."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        kpi_types = [
            'on_time_delivery_rate', 'fuel_efficiency', 'vehicle_utilization',
            'driver_hours', 'trip_completion', 'avg_delivery_time', 'km_traveled',
            'incidents_count', 'maintenance_cost', 'fleet_availability'
        ]
        
        kpis = []
        for i in range(1, count + 1):
            record_date = datetime.now() - timedelta(days=random.randint(0, 30))
            kpis.append((
                random.choice(self.vehicle_ids) if self.vehicle_ids else None,
                random.choice(self.driver_ids) if self.driver_ids else None,
                random.choice(kpi_types),
                random.uniform(0, 100),  # value
                random.choice(['daily', 'weekly', 'monthly']),
                record_date.date().isoformat(),
                f'KPI notes {i}' if random.random() > 0.5 else None,
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
        
        cursor.executemany('''
            INSERT OR REPLACE INTO logistics_fleet_kpis
            (vehicle_id, driver_id, kpi_type, value, period, record_date,
             notes, branch_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', kpis)
        
        conn.commit()
        cursor.execute('SELECT id FROM logistics_fleet_kpis ORDER BY id')
        self.kpi_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        return self.kpi_ids

    def seed_transport_documents(self, count: int = 20) -> List[int]:
        """Create transport documents."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        doc_types = ['bill_of_lading', 'cmr', 'delivery_note', 'invoice', 
                      'customs_declaration', 'insurance', 'permit', 'inspection']
        statuses = ['valid', 'expired', 'pending', 'renewed']
        
        docs = []
        for i in range(1, count + 1):
            issue_date = datetime.now() - timedelta(days=random.randint(0, 180))
            expiry_date = issue_date + timedelta(days=random.randint(90, 365))
            
            docs.append((
                f'TD-{1000 + i:04d}',
                random.choice(self.trip_ids) if self.trip_ids else None,
                random.choice(self.vehicle_ids) if self.vehicle_ids else None,
                random.choice(doc_types),
                issue_date.date().isoformat(),
                expiry_date.date().isoformat(),
                random.choice(statuses),
                f'Doc-{random.randint(1000, 9999)}.pdf',
                f'Document {i} notes',
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
        
        cursor.executemany('''
            INSERT OR REPLACE INTO logistics_transport_documents
            (doc_number, trip_id, vehicle_id, doc_type, issue_date, expiry_date,
             status, file_path, notes, branch_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', docs)
        
        conn.commit()
        cursor.execute('SELECT id FROM logistics_transport_documents ORDER BY id')
        self.document_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        return self.document_ids

    def run(self):
        """Execute full seed operation."""
        print('Clearing existing TMS data...')
        self.clear_existing_tms_data()
        
        print('Seeding vehicles (15+)...')
        self.seed_vehicles(15)
        
        print('Seeding drivers (20+)...')
        self.seed_drivers(20)
        
        print('Seeding routes (10+)...')
        self.seed_routes(10)
        
        print('Seeding trips (30+)...')
        self.seed_trips(30)
        
        print('Seeding shipments (40+)...')
        self.seed_shipments(40)
        
        print('Seeding POD records (25+)...')
        self.seed_pod_records(25)
        
        print('Seeding cost entries (30+)...')
        self.seed_cost_entries(30)
        
        print('Seeding incidents (15+)...')
        self.seed_incidents(15)
        
        print('Seeding delivery schedules (20+)...')
        self.seed_delivery_schedules(20)
        
        print('Seeding stop checkpoints (50+)...')
        self.seed_stop_checkpoints(50)
        
        print('Seeding fleet KPIs (30+)...')
        self.seed_fleet_kpis(30)
        
        print('Seeding transport documents (20+)...')
        self.seed_transport_documents(20)
        
        print('\n=== TMS Data Seeding Complete ===')
        print(f'  Vehicles: {len(self.vehicle_ids)}')
        print(f'  Drivers: {len(self.driver_ids)}')
        print(f'  Routes: {len(self.route_ids)}')
        print(f'  Trips: {len(self.trip_ids)}')
        print(f'  Shipments: {len(self.shipment_ids)}')
        print(f'  POD Records: {len(self.pod_ids)}')
        print(f'  Cost Entries: {len(self.cost_ids)}')
        print(f'  Incidents: {len(self.incident_ids)}')
        print(f'  Delivery Schedules: {len(self.schedule_ids)}')
        print(f'  Stop Checkpoints: {len(self.checkpoint_ids)}')
        print(f'  Fleet KPIs: {len(self.kpi_ids)}')
        print(f'  Transport Documents: {len(self.document_ids)}')
        print('================================')


def seed_tms_data(db_path: str = 'warehouse.db'):
    """Main entry point for seeding TMS data."""
    seeder = TMSSSeeder(db_path)
    seeder.run()


if __name__ == '__main__':
    seed_tms_data()
