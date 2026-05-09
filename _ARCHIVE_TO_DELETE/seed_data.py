import sqlite3
import random

DATABASE = 'warehouse.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

def seed():
    conn = get_db()
    c = conn.cursor()

    print("Generating comprehensive test data...")
    
    # 1. Categories
    categories = ['Filters', 'Brakes', 'Suspension', 'Electrical', 'Engine Components', 'Body Parts']
    for cat in categories:
        c.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))
    
    # 2. Brands
    brands = [
        ('Toyota Genuine', 'Genuine'), 
        ('Bosch', 'Aftermarket'), 
        ('Denso', 'Aftermarket'), 
        ('ACDelco', 'Aftermarket'), 
        ('Hyundai Mobis', 'Genuine'),
        ('Brembo', 'Aftermarket')
    ]
    for b in brands:
        c.execute("INSERT OR IGNORE INTO brands (name, type) VALUES (?, ?)", b)
        
    # 3. Statuses
    statuses = ['Active', 'Discontinued', 'Recalled', 'Backordered']
    for st in statuses:
        c.execute("INSERT OR IGNORE INTO statuses (name) VALUES (?)", (st,))

    # 4. Master Parts (50 items)
    for i in range(1, 41):
        part_number = f"OEM-{random.randint(10000, 99999)}-{random.choice(['A', 'B', 'C'])}"
        desc = f"Premium Auto Part Level {i} Assembly"
        cat_id = random.randint(1, len(categories))
        brand_id = random.randint(1, len(brands))
        status_id = random.choice([1, 1, 1, 4]) # Mostly active
        cost = float(random.randint(1599, 45000)) / 100.0
        reorder = random.randint(5, 20)
        
        try:
            c.execute("""
                INSERT INTO parts (part_number, description, weight, category_id, brand_id, status_id, reorder_point, cost_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (part_number, desc, random.uniform(0.5, 12.0), cat_id, brand_id, status_id, reorder, cost))
        except sqlite3.IntegrityError:
            pass # Skip duplicate part numbers

    # 5. Inventory Items (Sub-locations array logic)
    part_ids = [row[0] for row in c.execute("SELECT id FROM parts").fetchall()]
    company_ids = [1, 2, 3, 4] # Holding, SDAD, AFRA, Carmania

    for pid in part_ids:
        num_subs = random.randint(1, 3)
        subs = random.sample(company_ids, num_subs)
        for cid in subs:
            qty = random.randint(0, 150)
            # Rack(01-99)-Bay(01-99)-Level(01-99)-Position(01-99)-Bin(A-Z)
            zone = f"{random.randint(1,20):02d}-{random.randint(1,50):02d}-{random.randint(1,10):02d}-{random.randint(1,99):02d}-{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"
            try:
                c.execute("""
                    INSERT INTO inventory (part_id, company_id, zone, quantity)
                    VALUES (?, ?, ?, ?)
                """, (pid, cid, zone, qty))
            except sqlite3.IntegrityError:
                pass

    conn.commit()
    conn.close()
    print("Database successfully seeded with colorful test data!")

if __name__ == '__main__':
    seed()
