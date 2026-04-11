"""
Asset Management Seed Data
========================
Seeds realistic demo/test data for the Asset Management module.

Usage:
    python seed_asset_data.py
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random


def get_default_db_path():
    """Get the default database path matching app.py"""
    base = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base, 'warehouse.db')

DATABASE = os.environ.get('DATABASE_PATH', get_default_db_path())


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def seed_asset_data():
    """Seed comprehensive asset management data."""
    db = get_db()

    print("Seeding Asset Management data...")

    # Check if we already have data
    existing_assets = db.execute("SELECT COUNT(*) as cnt FROM assets").fetchone()['cnt']
    if existing_assets > 10:
        print(f"Assets already seeded ({existing_assets} found). Skipping...")
        db.close()
        return

    # Get reference data
    companies = db.execute("SELECT id, name FROM companies").fetchall()
    departments = db.execute("SELECT id, name FROM hr_departments LIMIT 10").fetchall()
    suppliers = db.execute("SELECT id, name FROM suppliers LIMIT 20").fetchall()
    employees = db.execute("SELECT id, first_name, last_name FROM hr_employees LIMIT 20").fetchall()
    categories = db.execute("SELECT id, name, code, default_useful_life_years, default_salvage_percent FROM asset_categories").fetchall()
    depreciation_methods = db.execute("SELECT id, code FROM depreciation_methods").fetchall()
    maintenance_types = db.execute("SELECT id, name FROM maintenance_types").fetchall()

    if not companies or len(companies) == 0:
        companies = [(1, 'Main Company')]

    if not categories:
        print("No asset categories found. Please run init first.")
        db.close()
        return

    # Get depreciation method IDs
    straight_line_id = None
    for dm in depreciation_methods:
        if dm['code'] == 'STRAIGHT_LINE':
            straight_line_id = dm['id']
            break
    if not straight_line_id:
        straight_line_id = depreciation_methods[0]['id'] if depreciation_methods else 1

    # Asset templates for realistic data
    asset_templates = [
        # IT Equipment
        {'name': 'Dell Latitude 5520 Laptop', 'category': 'IT-EQUIP', 'brand': 'Dell', 'model': 'Latitude 5520', 'cost': 4500, 'life': 3},
        {'name': 'Dell OptiPlex 7090 Desktop', 'category': 'IT-EQUIP', 'brand': 'Dell', 'model': 'OptiPlex 7090', 'cost': 3200, 'life': 3},
        {'name': 'HP EliteBook 840 G8', 'category': 'IT-EQUIP', 'brand': 'HP', 'model': 'EliteBook 840 G8', 'cost': 5200, 'life': 3},
        {'name': 'Lenovo ThinkPad X1 Carbon', 'category': 'IT-EQUIP', 'brand': 'Lenovo', 'model': 'X1 Carbon Gen 9', 'cost': 6800, 'life': 3},
        {'name': 'Apple MacBook Pro 14"', 'category': 'IT-EQUIP', 'brand': 'Apple', 'model': 'MacBook Pro 14"', 'cost': 12000, 'life': 4},
        {'name': 'Cisco IP Phone 8845', 'category': 'IT-EQUIP', 'brand': 'Cisco', 'model': 'IP Phone 8845', 'cost': 1800, 'life': 5},
        {'name': 'HP LaserJet Pro M404n', 'category': 'IT-EQUIP', 'brand': 'HP', 'model': 'LaserJet Pro M404n', 'cost': 2400, 'life': 5},
        {'name': 'Synology DS920+ NAS', 'category': 'IT-EQUIP', 'brand': 'Synology', 'model': 'DS920+', 'cost': 3500, 'life': 5},
        {'name': 'Ubiquiti UniFi Dream Machine', 'category': 'IT-EQUIP', 'brand': 'Ubiquiti', 'model': 'UDM-Pro', 'cost': 2800, 'life': 5},
        {'name': 'Samsung 27" Monitor', 'category': 'IT-EQUIP', 'brand': 'Samsung', 'model': 'S27R750Q', 'cost': 2200, 'life': 4},

        # Office Furniture
        {'name': 'Executive Desk - Mahogany', 'category': 'OFF-FURN', 'brand': 'Godrej', 'model': 'Executive Pro', 'cost': 4500, 'life': 10},
        {'name': 'Ergonomic Office Chair', 'category': 'OFF-FURN', 'brand': 'Herman Miller', 'model': 'Aeron', 'cost': 8500, 'life': 10},
        {'name': 'Conference Table - 10 Seater', 'category': 'OFF-FURN', 'brand': 'Spacewood', 'model': 'CT-10', 'cost': 12000, 'life': 10},
        {'name': 'Storage Cabinet - 4 Door', 'category': 'OFF-FURN', 'brand': 'Godrej', 'model': 'Steel Cabinet', 'cost': 3500, 'life': 10},
        {'name': 'Reception Desk', 'category': 'OFF-FURN', 'brand': 'Spacewood', 'model': 'Reception-L', 'cost': 18000, 'life': 10},
        {'name': 'Bookshelf - 5 Tier', 'category': 'OFF-FURN', 'brand': 'Godrej', 'model': 'Steel Shelf', 'cost': 2500, 'life': 10},

        # Office Equipment
        {'name': 'Canon imageRUNNER 2520', 'category': 'OFF-EQUIP', 'brand': 'Canon', 'model': 'imageRUNNER 2520', 'cost': 28000, 'life': 5},
        {'name': 'Ricoh MP 4055SP', 'category': 'OFF-EQUIP', 'brand': 'Ricoh', 'model': 'MP 4055SP', 'cost': 35000, 'life': 5},
        {'name': 'Paper Shredder - Heavy Duty', 'category': 'OFF-EQUIP', 'brand': 'Fellowes', 'model': 'Powershred 99Ci', 'cost': 1800, 'life': 5},
        {'name': 'Projector - Epson EB-2250U', 'category': 'OFF-EQUIP', 'brand': 'Epson', 'model': 'EB-2250U', 'cost': 8500, 'life': 5},
        {'name': 'Digital Whiteboard - 86"', 'category': 'OFF-EQUIP', 'brand': 'Samsung', 'model': 'Flip Pro', 'cost': 25000, 'life': 5},

        # Vehicles
        {'name': 'Toyota Camry 2.5L', 'category': 'VEHICLES', 'brand': 'Toyota', 'model': 'Camry', 'cost': 120000, 'life': 5, 'salvage': 20},
        {'name': 'Toyota Corolla 1.8L', 'category': 'VEHICLES', 'brand': 'Toyota', 'model': 'Corolla', 'cost': 95000, 'life': 5, 'salvage': 20},
        {'name': 'Ford Transit Van', 'category': 'VEHICLES', 'brand': 'Ford', 'model': 'Transit 350L', 'cost': 180000, 'life': 5, 'salvage': 15},
        {'name': 'Mitsubishi L200 Pickup', 'category': 'VEHICLES', 'brand': 'Mitsubishi', 'model': 'L200', 'cost': 85000, 'life': 5, 'salvage': 20},

        # Machinery
        {'name': 'CNC Milling Machine - 5 Axis', 'category': 'MACHINERY', 'brand': 'Haas', 'model': 'VF-5SS', 'cost': 450000, 'life': 10, 'salvage': 10},
        {'name': 'Industrial Lathe Machine', 'category': 'MACHINERY', 'brand': 'Mazak', 'model': 'QT-250', 'cost': 280000, 'life': 10, 'salvage': 10},
        {'name': 'Hydraulic Press - 200 Ton', 'category': 'MACHINERY', 'brand': 'Schuler', 'model': 'HP-200', 'cost': 180000, 'life': 10, 'salvage': 10},
        {'name': 'Welding Robot - 6 Axis', 'category': 'MACHINERY', 'brand': 'Fanuc', 'model': 'ArcMate 120iD', 'cost': 320000, 'life': 10, 'salvage': 10},

        # Warehouse Equipment
        {'name': 'Forklift - 3 Ton', 'category': 'WH-EQUIP', 'brand': 'Toyota', 'model': 'Core IC 3Ton', 'cost': 95000, 'life': 7},
        {'name': 'Electric Pallet Jack', 'category': 'WH-EQUIP', 'brand': 'Still', 'model': 'EXV-SF', 'cost': 25000, 'life': 7},
        {'name': 'Warehouse Racking System', 'category': 'WH-EQUIP', 'brand': 'Mecalux', 'model': 'Pallet Flow', 'cost': 180000, 'life': 10},
        {'name': 'Shipping Container - 40ft', 'category': 'WH-EQUIP', 'brand': 'SeaCan', 'model': '40HC', 'cost': 35000, 'life': 10},
        {'name': 'Platform Scale - 5 Ton', 'category': 'WH-EQUIP', 'brand': 'Mettler Toledo', 'model': 'PBD-655', 'cost': 15000, 'life': 7},

        # Communication Devices
        {'name': 'Cisco Unified IP Phone 9971', 'category': 'COMM-DEV', 'brand': 'Cisco', 'model': '9971', 'cost': 2200, 'life': 5},
        {'name': 'Polycom Conference Phone', 'category': 'COMM-DEV', 'brand': 'Polycom', 'model': 'SoundStation IP 7000', 'cost': 4500, 'life': 5},
        {'name': 'Motorola Radio - Handheld', 'category': 'COMM-DEV', 'brand': 'Motorola', 'model': 'DP4801e', 'cost': 1800, 'life': 5},

        # Leasehold Improvements
        {'name': 'Office Interior - Fitout Level 1', 'category': 'LEASEHOLD', 'brand': 'Various', 'model': 'Standard Fitout', 'cost': 450000, 'life': 10},
        {'name': 'AC Installation - Central', 'category': 'LEASEHOLD', 'brand': 'Daikin', 'model': 'VRV IV', 'cost': 180000, 'life': 10},
        {'name': 'Fire Suppression System', 'category': 'LEASEHOLD', 'brand': 'Tyco', 'model': 'JTL', 'cost': 85000, 'life': 10},
        {'name': 'Security System - CCTV', 'category': 'LEASEHOLD', 'brand': 'Hikvision', 'model': 'Pro Series', 'cost': 120000, 'life': 5},

        # Tools
        {'name': 'Power Drill Set - Industrial', 'category': 'TOOLS', 'brand': 'Makita', 'model': 'HP2071X', 'cost': 1800, 'life': 5},
        {'name': 'Angle Grinder - 9"', 'category': 'TOOLS', 'brand': 'Bosch', 'model': 'GWS 22-230', 'cost': 850, 'life': 5},
        {'name': 'Measuring Instrument Set', 'category': 'TOOLS', 'brand': 'Mitutoyo', 'model': '500 Series', 'cost': 12000, 'life': 5},
    ]

    # Depreciation method mapping
    depr_method_by_category = {
        'IT-EQUIP': 'STRAIGHT_LINE',
        'OFF-FURN': 'STRAIGHT_LINE',
        'OFF-EQUIP': 'STRAIGHT_LINE',
        'VEHICLES': 'STRAIGHT_LINE',
        'MACHINERY': 'STRAIGHT_LINE',
        'WH-EQUIP': 'STRAIGHT_LINE',
        'COMM-DEV': 'STRAIGHT_LINE',
        'LEASEHOLD': 'STRAIGHT_LINE',
        'TOOLS': 'STRAIGHT_LINE',
    }

    # Status distribution
    statuses = ['Active', 'Active', 'Active', 'Active', 'Active', 'Under Maintenance', 'Pending Disposal', 'Disposed']
    conditions = ['Excellent', 'Good', 'Good', 'Good', 'Fair']
    locations = ['Office - Floor 1', 'Office - Floor 2', 'Office - Floor 3', 'Warehouse A', 'Warehouse B', 'Storage Room', 'Server Room', 'Showroom']

    # Get category IDs
    category_ids = {cat['code']: cat['id'] for cat in categories}

    created_assets = []
    asset_counter = 10001

    for template in asset_templates:
        cat_code = template['category']
        if cat_code not in category_ids:
            continue

        cat_id = category_ids[cat_code]
        salvage = template.get('salvage', 0)
        life = template.get('life', 5)

        # Get company and department
        company_id = companies[0]['id'] if companies else 1
        dept_id = departments[random.randint(0, len(departments)-1)]['id'] if departments else None
        supplier_id = suppliers[random.randint(0, len(suppliers)-1)]['id'] if suppliers else None
        custodian_id = employees[random.randint(0, len(employees)-1)]['id'] if employees else None

        # Random dates
        days_ago = random.randint(30, 730)  # 1 month to 2 years ago
        acquisition_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')

        capitalization_date = (datetime.strptime(acquisition_date, '%Y-%m-%d') + timedelta(days=random.randint(1, 7))).strftime('%Y-%m-%d')

        in_service_date = capitalization_date

        depr_start_date = in_service_date

        # Calculate depreciation
        acquisition_cost = template['cost']
        salvage_value = acquisition_cost * (salvage / 100)

        # Status
        status = random.choice(statuses)

        # Serial number generation
        serial = f"SN-{template['brand'][:3].upper()}-{asset_counter}"

        # Asset code
        asset_code = f"AST-{asset_counter}"

        # Insert asset
        cursor = db.execute("""
            INSERT INTO assets (
                asset_code, name, description, category_id, asset_type,
                serial_number, brand, model, tag_number,
                acquisition_date, capitalization_date, in_service_date,
                acquisition_cost, supplier_id,
                depreciation_method_id, useful_life_years, salvage_value, salvage_percent,
                depreciation_start_date, company_id, department_id, custodian_id,
                location, status, condition_rating,
                accumulated_depreciation, net_book_value,
                depreciation_status, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            asset_code,
            template['name'],
            f"{template['brand']} {template['model']} - Purchased for {dept_id if dept_id else 'General'} use",
            cat_id,
            'Tangible',
            serial,
            template['brand'],
            template['model'],
            f"TAG-{asset_counter}",
            acquisition_date,
            capitalization_date,
            in_service_date,
            acquisition_cost,
            supplier_id,
            straight_line_id,
            life,
            salvage_value,
            salvage,
            depr_start_date,
            company_id,
            dept_id,
            custodian_id,
            random.choice(locations),
            status,
            random.choice(conditions),
            0,  # accumulated depreciation (will update)
            acquisition_cost,  # net book value initially
            'Active' if status in ['Active', 'Under Maintenance'] else 'Disposed',
            1  # admin user
        ))

        asset_id = cursor.lastrowid
        created_assets.append({
            'id': asset_id,
            'asset_code': asset_code,
            'name': template['name'],
            'acquisition_cost': acquisition_cost,
            'salvage_value': salvage_value,
            'life': life,
            'status': status,
            'in_service_date': in_service_date,
            'depr_start_date': depr_start_date
        })

        # Create depreciation profile
        depreciable = acquisition_cost - salvage_value
        monthly_depr = depreciable / (life * 12) if life > 0 else 0

        db.execute("""
            INSERT INTO asset_depreciation_profiles (
                asset_id, depreciation_method_id, acquisition_cost, salvage_value,
                useful_life_months, useful_life_years, monthly_depreciation,
                accumulated_depreciation, net_book_value, depreciation_start_date, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            asset_id, straight_line_id, acquisition_cost, salvage_value,
            life * 12, life, monthly_depr,
            0, acquisition_cost, depr_start_date
        ))

        # Create initial assignment
        db.execute("""
            INSERT INTO asset_assignments (
                asset_id, assignment_type, assigned_to_id, department_id,
                effective_date, status, condition_at_assignment
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            asset_id, 'Initial Assignment', custodian_id, dept_id,
            acquisition_date, 'Active' if status == 'Active' else 'Returned', 'Good'
        ))

        # Create acquisition record
        db.execute("""
            INSERT INTO asset_acquisitions (
                asset_id, acquisition_type, acquisition_date, capitalization_date,
                supplier_id, invoice_amount, total_capitalized_cost,
                approval_status, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            asset_id, 'Purchase', acquisition_date, capitalization_date,
            supplier_id, acquisition_cost, acquisition_cost,
            'Approved', 1
        ))

        # Add some maintenance schedules for active IT and machinery assets
        if status == 'Active' and cat_code in ['IT-EQUIP', 'MACHINERY', 'WH-EQUIP']:
            maint_type_id = maintenance_types[0]['id'] if maintenance_types else 1

            # Next due date
            next_due = (datetime.now() + timedelta(days=random.randint(7, 90))).strftime('%Y-%m-%d')

            db.execute("""
                INSERT INTO maintenance_schedules (
                    asset_id, maintenance_type_id, frequency, interval_days,
                    next_due_date, priority, estimated_cost, is_active, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1)
            """, (
                asset_id, maint_type_id, 'Monthly', 30,
                next_due, 'Medium', 500
            ))

        asset_counter += 1

    db.commit()
    print(f"Created {len(created_assets)} assets")

    # Create some depreciation runs for historical data
    print("Creating depreciation history...")

    # Get assets that need depreciation history
    active_assets = db.execute("""
        SELECT a.id, a.asset_code, a.name, a.acquisition_cost, a.salvage_value,
               a.in_service_date, a.accumulated_depreciation, a.net_book_value,
               adp.monthly_depreciation, adp.useful_life_months, adp.depreciation_start_date
        FROM assets a
        JOIN asset_depreciation_profiles adp ON a.id = adp.asset_id
        WHERE a.status IN ('Active', 'Under Maintenance')
        LIMIT 20
    """).fetchall()

    # Create depreciation runs for last 6 months
    for month_offset in range(6):
        run_date = datetime.now() - timedelta(days=30 * month_offset)
        period_month = run_date.month
        period_year = run_date.year

        # Check if run exists
        existing = db.execute("""
            SELECT id FROM depreciation_runs WHERE period_month = ? AND period_year = ?
        """, (period_month, period_year)).fetchone()

        if existing:
            continue

        run_number = f"DEP-{period_year}{period_month:02d}-001"

        cursor = db.execute("""
            INSERT INTO depreciation_runs (
                run_number, run_date, period_month, period_year,
                description, status, total_assets,
                total_depreciation, processed_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_number, run_date.strftime('%Y-%m-%d'), period_month, period_year,
            f'Depreciation run {period_month}/{period_year}', 'Posted',
            len(active_assets), 0, 1
        ))
        run_id = cursor.lastrowid

        total_depr = 0
        for asset in active_assets:
            # Calculate months since start
            start = datetime.strptime(asset['depreciation_start_date'], '%Y-%m-%d')
            months_elapsed = (run_date.year - start.year) * 12 + (run_date.month - start.month)

            if months_elapsed < 0:
                continue

            depr_amount = asset['monthly_depreciation']
            new_accumulated = asset['accumulated_depreciation'] + depr_amount
            new_nbv = asset['acquisition_cost'] - new_accumulated

            if new_nbv < asset['salvage_value']:
                depr_amount = asset['net_book_value'] - asset['salvage_value']
                new_accumulated = asset['accumulated_depreciation']
                new_nbv = asset['salvage_value']

            db.execute("""
                INSERT INTO depreciation_entries (
                    run_id, asset_id, asset_code, asset_name,
                    period_month, period_year, depreciation_amount,
                    accumulated_depreciation, net_book_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id, asset['id'], asset['asset_code'], asset['name'],
                period_month, period_year, depr_amount,
                new_accumulated, new_nbv
            ))

            # Update asset
            db.execute("""
                UPDATE assets SET
                    accumulated_depreciation = ?,
                    net_book_value = ?,
                    last_depreciation_date = ?
                WHERE id = ?
            """, (new_accumulated, new_nbv, f'{period_year}-{period_month:02d}-01', asset['id']))

            total_depr += depr_amount

        # Update run totals
        db.execute("""
            UPDATE depreciation_runs SET
                total_depreciation = ?,
                total_accumulated = (SELECT SUM(accumulated_depreciation) FROM depreciation_entries WHERE run_id = ?),
                total_net_book_value = (SELECT SUM(net_book_value) FROM depreciation_entries WHERE run_id = ?)
            WHERE id = ?
        """, (total_depr, run_id, run_id, run_id))

    db.commit()
    print("Depreciation history created")

    # Create some maintenance work orders and logs
    print("Creating maintenance records...")

    maint_assets = db.execute("""
        SELECT id FROM assets
        WHERE status IN ('Active', 'Under Maintenance')
        AND category_id IN (SELECT id FROM asset_categories WHERE code IN ('IT-EQUIP', 'MACHINERY', 'WH-EQUIP'))
        LIMIT 10
    """).fetchall()

    maint_type_id = maintenance_types[0]['id'] if maintenance_types else 1

    for i, asset_row in enumerate(maint_assets):
        asset_id = asset_row['id']

        # Create work order
        wo_number = f"WO-{1001 + i}"
        work_order_date = (datetime.now() - timedelta(days=random.randint(5, 60))).strftime('%Y-%m-%d')

        cursor = db.execute("""
            INSERT INTO maintenance_work_orders (
                work_order_number, asset_id, maintenance_type_id,
                work_order_type, priority, status, issue_date,
                issue_description, estimated_cost, actual_cost,
                completed_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            wo_number, asset_id, maint_type_id,
            random.choice(['Corrective', 'Preventive']),
            random.choice(['Low', 'Medium', 'High']),
            'Completed', work_order_date,
            f"Scheduled {random.choice(['inspection', 'maintenance', 'repair', 'calibration'])}",
            500, random.randint(300, 1500),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1
        ))
        wo_id = cursor.lastrowid

        # Create work log
        db.execute("""
            INSERT INTO maintenance_work_logs (
                work_order_id, asset_id, maintenance_type_id, work_date,
                work_performed, action_taken, parts_used,
                labor_hours, labor_cost, parts_cost, total_cost,
                notes, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            wo_id, asset_id, maint_type_id, work_order_date,
            'Routine maintenance performed',
            'Inspected and serviced as per schedule',
            'Oil, filters replaced',
            2, 200, random.randint(100, 500), random.randint(400, 1000),
            'Completed on schedule', 1
        ))

        # Create cost entry
        db.execute("""
            INSERT INTO maintenance_cost_entries (
                asset_id, work_order_id, cost_type, cost_date,
                description, amount, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            asset_id, wo_id, 'Maintenance',
            work_order_date, 'Work order completion',
            random.randint(400, 1500), 1
        ))

    db.commit()
    print("Maintenance records created")

    # Create a few disposal requests and disposals
    print("Creating disposal records...")

    disposed_assets = db.execute("""
        SELECT id, asset_code, name, net_book_value
        FROM assets WHERE status = 'Disposed'
        LIMIT 3
    """).fetchall()

    for i, asset in enumerate(disposed_assets):
        # Create request
        request_date = (datetime.now() - timedelta(days=30 + i * 10)).strftime('%Y-%m-%d')
        disposal_date = (datetime.now() - timedelta(days=20 + i * 10)).strftime('%Y-%m-%d')

        request_number = f"DR-{1001 + i}"
        disposal_number = f"DSP-{1001 + i}"

        proceeds = random.randint(500, 5000)
        nbv = asset['net_book_value'] or 0
        gain_loss = proceeds - nbv

        # Create request
        db.execute("""
            INSERT INTO disposal_requests (
                request_number, asset_id, request_date, disposal_type,
                reason_code, estimated_proceeds, net_book_value, gain_loss,
                status, approved_by, approved_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request_number, asset['id'], request_date, 'Sale',
            'Obsolete', proceeds, nbv, gain_loss,
            'Completed', 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1
        ))

        # Create disposal
        db.execute("""
            INSERT INTO asset_disposals (
                disposal_number, asset_id, disposal_date, disposal_type,
                proceeds, cost_of_disposal, net_proceeds, gain_loss,
                buyer_name, approval_status, approved_by, approved_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            disposal_number, asset['id'], disposal_date, 'Sale',
            proceeds, 200, proceeds - 200, gain_loss,
            f'Buyer {i+1}', 'Approved', 1,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1
        ))

    db.commit()
    print("Disposal records created")

    print("\nAsset Management seed data completed successfully!")
    print(f"Total assets created: {len(created_assets)}")

    db.close()


if __name__ == '__main__':
    seed_asset_data()
