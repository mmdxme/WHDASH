import sqlite3
import os

DATABASE = 'warehouse.db'

def migrate():
    if not os.path.exists(DATABASE):
        print(f"Database {DATABASE} not found.")
        return

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # 1. Create Customers Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            phone VARCHAR(50),
            location VARCHAR(255), -- City, Country
            type VARCHAR(50), -- Wholesale, Retail, Garage, Shop
            salesperson_id INTEGER,
            working_hours VARCHAR(100), -- e.g., 08:00 - 18:00
            working_days VARCHAR(100), -- e.g., Mon-Fri
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (salesperson_id) REFERENCES users(id)
        )
    ''')

    # 2. Create Delivery Trips Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS delivery_trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER NOT NULL,
            date DATE DEFAULT CURRENT_DATE,
            warehouse_departure TIMESTAMP,
            warehouse_arrival TIMESTAMP,
            status VARCHAR(20) DEFAULT 'At Warehouse', -- At Warehouse, In Transit, Completed
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (driver_id) REFERENCES users(id)
        )
    ''')

    # 3. Create Delivery Stops Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS delivery_stops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            arrival_time TIMESTAMP,
            departure_time TIMESTAMP,
            arrival_gps VARCHAR(100),
            departure_gps VARCHAR(100),
            status VARCHAR(20) DEFAULT 'Pending', -- Pending, Arrived, Departed
            sequence_order INTEGER,
            FOREIGN KEY (trip_id) REFERENCES delivery_trips(id) ON DELETE CASCADE,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')

    # 4. Insert Mock Data
    # 5 Mock Customers
    customers = [
        ('Speedy Garage', '050-1112223', 'Dubai, UAE', 'Garage', 1, '08:00 - 20:00', 'Sat-Thu'),
        ('Retail Parts Co', '055-3334445', 'Sharjah, UAE', 'Retail', 1, '09:00 - 21:00', 'Mon-Sat'),
        ('Elite Motors', '044-5556667', 'Abu Dhabi, UAE', 'Shop', 1, '08:30 - 17:30', 'Sun-Thu'),
        ('Reliable Auto', '052-7778889', 'Ajman, UAE', 'Garage', 1, '08:00 - 22:00', 'Daily'),
        ('Wholesale Hub', '056-9990001', 'Dubai, UAE', 'Wholesale', 1, '07:00 - 16:00', 'Sat-Wed')
    ]
    cursor.executemany('''
        INSERT INTO customers (name, phone, location, type, salesperson_id, working_hours, working_days)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', customers)

    # 2 Mock Drivers (if not exists, but we can just use existing users or add specifically)
    # Let's ensure we have a driver role name?
    # Actually, prompt says "2 drivers". I'll add them to users with a 'Staff' role or similar.
    # First, get a role ID for someone who isn't admin
    cursor.execute("SELECT id FROM roles WHERE role_name != 'Global Admin' LIMIT 1")
    row = cursor.fetchone()
    staff_role_id = row[0] if row else 1

    drivers = [
        ('driver1', 'driver1@holding.com', 'pbkdf2:sha256:260000$yR8xJz9Y$7f3f...', staff_role_id),
        ('driver2', 'driver2@holding.com', 'pbkdf2:sha256:260000$yR8xJz9Y$7f3f...', staff_role_id)
    ]
    # For simplicity, I'll just use generate_password_hash or assuming some password like 'driver123'
    # But since I'm in script, I'll use a dummy hash from werkzeug or just plain for now (bad but it's mock)
    # Better: Use the same format as admin if possible.
    
    for d_name, d_email, d_pass, d_role in drivers:
        cursor.execute("INSERT OR IGNORE INTO users (username, email, password, role_id) VALUES (?, ?, ?, ?)", 
                       (d_name, d_email, d_pass, d_role))

    conn.commit()
    conn.close()
    print("Migration v6 (Delivery) completed successfully.")

if __name__ == '__main__':
    migrate()
