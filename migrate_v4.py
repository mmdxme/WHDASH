import sqlite3
import os

def run_migration():
    db_path = 'C:/Users/2g/AG/MMD DASH/warehouse.db'
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    # Return rows as dict-like objects
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check current columns in roles
    cursor.execute("PRAGMA table_info(roles)")
    columns = [row['name'] for row in cursor.fetchall()]
    print(f"Current columns in roles: {columns}")
    
    # New columns to add
    new_cols = [
        ('can_view_reports', 'TINYINT(1) DEFAULT 0'),
        ('can_view_valuation', 'TINYINT(1) DEFAULT 0'),
        ('can_manage_parts', 'TINYINT(1) DEFAULT 0'),
        ('can_manage_locations', 'TINYINT(1) DEFAULT 0'),
        ('can_manage_taxonomies', 'TINYINT(1) DEFAULT 0')
    ]
    
    for col_name, col_type in new_cols:
        if col_name not in columns:
            print(f"Adding column {col_name} to roles...")
            try:
                cursor.execute(f"ALTER TABLE roles ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")
            
    # Predefined groups
    # Sales: View Reports
    # Accounting: View Reports, View Valuation
    # Procurement: View Reports, View Valuation, Edit Stock, Manage Parts
    # Delivery: Edit Stock (Picking)
    # Warehouse: Edit Stock, Manage Parts, Manage Locations, Manage Taxonomies
    # Manager: Full access
    
    groups = [
        # role_name, can_edit_stock, can_manage_users, can_view_reports, can_view_val, can_manage_parts, can_manage_locs, can_manage_tax
        ('Sales', 0, 0, 1, 0, 0, 0, 0),
        ('Accounting', 0, 0, 1, 1, 0, 0, 0),
        ('Procurement', 1, 0, 1, 1, 1, 0, 0),
        ('Delivery', 1, 0, 0, 0, 0, 0, 0),
        ('Warehouse', 1, 0, 0, 0, 1, 1, 1),
        ('Manager', 1, 0, 1, 1, 1, 1, 1)
    ]
    
    for g_name, edit_stock, manage_users, view_reports, view_val, manage_parts, manage_locs, manage_tax in groups:
        cursor.execute("SELECT id FROM roles WHERE role_name = ?", (g_name,))
        if not cursor.fetchone():
            print(f"Seeding role {g_name}...")
            cursor.execute("""
                INSERT INTO roles (role_name, can_edit_stock, can_manage_users, can_view_reports, 
                                 can_view_valuation, can_manage_parts, can_manage_locations, can_manage_taxonomies)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (g_name, edit_stock, manage_users, view_reports, view_val, manage_parts, manage_locs, manage_tax))
        else:
            print(f"Role {g_name} already exists.")
            
    conn.commit()
    conn.close()
    print("Migration v4 completed.")

if __name__ == '__main__':
    run_migration()
