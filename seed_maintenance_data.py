"""
Seed Maintenance Management Demo Data
==================================
Seeds realistic maintenance data for testing and demonstration.
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


def seed_maintenance_data():
    """Seed comprehensive maintenance demo data."""
    conn = get_db()
    cursor = conn.cursor()

    print("Seeding maintenance management demo data...")

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) as cnt FROM maintenance_facilities")
    if cursor.fetchone()['cnt'] > 0:
        print("Maintenance data already exists, skipping...")
        conn.close()
        return

    # Seed Maintenance Facilities
    print("  Creating facilities...")
    facilities = [
        ('FAC-001', 'Main Office Building', 'Headquarters office building', 'Building', 'Corporate', 'Dubai', 'UAE', 'John Smith', '+971-4-123-4567', 'john.smith@company.com', 1, 1),
        ('FAC-002', 'Warehouse A', 'Primary storage warehouse', 'Warehouse', 'Storage', 'Dubai', 'UAE', 'Ahmed Al Mansouri', '+971-4-234-5678', 'ahmed.mansouri@company.com', 1, 1),
        ('FAC-003', 'Factory Floor 1', 'Main manufacturing floor', 'Factory', 'Manufacturing', 'Sharjah', 'UAE', 'Khalid Hassan', '+971-6-345-6789', 'khalid.hassan@company.com', 1, 1),
        ('FAC-004', 'Data Center', 'IT data center facility', 'Data Center', 'IT', 'Dubai', 'UAE', 'Fatima Al Zahra', '+971-4-456-7890', 'fatima.zahra@company.com', 1, 1),
        ('FAC-005', 'Service Center', 'Customer service building', 'Building', 'Service', 'Abu Dhabi', 'UAE', 'Mohammed Al Kaabi', '+971-2-567-8901', 'mohammed.kaabi@company.com', 1, 0),
    ]

    for code, name, desc, ftype, cat, city, country, contact, phone, email, is_crit, active in facilities:
        cursor.execute(
            "INSERT INTO maintenance_facilities (facility_code, name, description, facility_type, category, city, country, contact_person, contact_phone, contact_email, is_critical, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (code, name, desc, ftype, cat, city, country, contact, phone, email, is_crit, active)
        )

    # Seed Maintenance Teams
    print("  Creating teams...")
    teams = [
        ('MT-001', 'Electrical Team', 'Handles all electrical maintenance', 1, 'Electrical, PLC, Wiring'),
        ('MT-002', 'HVAC Team', 'Heating, ventilation, and air conditioning', 2, 'HVAC, Refrigeration, Ventilation'),
        ('MT-003', 'Mechanical Team', 'Mechanical equipment maintenance', 3, 'Motors, Pumps, Bearings'),
        ('MT-004', 'General Maintenance', 'General facility maintenance', 4, 'Plumbing, Carpentry, Painting'),
        ('MT-005', 'IT Support Team', 'IT equipment and infrastructure', 5, 'Servers, Networks, Computers'),
    ]

    for code, name, desc, lead_id, skills in teams:
        cursor.execute(
            "INSERT INTO maintenance_teams (team_code, team_name, description, team_lead_id, skill_specializations, is_active) VALUES (?, ?, ?, ?, ?, 1)",
            (code, name, desc, lead_id, skills)
        )

    # Get some employees for team members
    cursor.execute("SELECT id FROM hr_employees LIMIT 10")
    employees = [row['id'] for row in cursor.fetchall()]

    # Add team members
    for team_id in range(1, 6):
        for i, emp_id in enumerate(employees[:random.randint(3, 5)]):
            role = 'Team Lead' if i == 0 else 'Technician'
            cursor.execute(
                "INSERT INTO maintenance_team_members (team_id, employee_id, role, is_active, joined_date) VALUES (?, ?, ?, 1, date('now', '-' || ? || ' days'))",
                (team_id, emp_id, role, random.randint(30, 365))
            )

    # Seed some PM Schedules
    print("  Creating PM schedules...")
    cursor.execute("SELECT id FROM assets WHERE status NOT IN ('Disposed', 'Retired') LIMIT 15")
    assets = [row['id'] for row in cursor.fetchall()]

    cursor.execute("SELECT id FROM maintenance_types")
    maint_types = [row['id'] for row in cursor.fetchall()]

    cursor.execute("SELECT id FROM hr_employees LIMIT 5")
    techs = [row['id'] for row in cursor.fetchall()]

    frequencies = ['Daily', 'Weekly', 'Monthly', 'Quarterly', 'Semi-Annual', 'Annual']
    priorities = ['Low', 'Medium', 'High', 'Critical']

    for i, asset_id in enumerate(assets[:12]):
        maint_type = random.choice(maint_types)
        freq = random.choice(frequencies)
        priority = random.choice(priorities)
        tech = random.choice(techs) if techs else None

        days_until_due = random.randint(-10, 45)
        next_due = (datetime.now() + timedelta(days=days_until_due)).strftime('%Y-%m-%d')

        interval = 30 if freq == 'Monthly' else (7 if freq == 'Weekly' else (90 if freq == 'Quarterly' else 365))

        cursor.execute(
            "INSERT INTO maintenance_schedules (asset_id, maintenance_type_id, schedule_name, frequency, interval_days, next_due_date, priority, assigned_technician_id, estimated_duration_hours, estimated_cost, is_active, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1)",
            (asset_id, maint_type, f"PM Schedule {i+1}", freq, interval, next_due, priority, tech, random.uniform(1, 8), random.uniform(50, 500))
        )

    # Seed Work Orders
    print("  Creating work orders...")
    wo_statuses = ['Open', 'In Progress', 'Completed', 'On Hold', 'Waiting Parts']
    wo_types = ['Preventive', 'Corrective', 'Emergency']

    for i in range(25):
        asset_id = random.choice(assets)
        maint_type = random.choice(maint_types)
        tech = random.choice(techs) if techs else None
        status = random.choice(wo_statuses)
        wo_type = random.choice(wo_types)
        priority = random.choice(priorities)

        issue_date = (datetime.now() - timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d')
        wo_number = f"WO-{datetime.now().strftime('%Y%m')}-{i+1:04d}"
        scheduled_end = (datetime.strptime(issue_date, '%Y-%m-%d') + timedelta(days=random.randint(1, 7))).strftime('%Y-%m-%d')

        actual_cost = random.uniform(50, 800) if status == 'Completed' else 0
        downtime = random.uniform(0, 4) if status == 'Completed' else 0
        completed_at = (datetime.strptime(issue_date, '%Y-%m-%d') + timedelta(days=random.randint(1, 14))).strftime('%Y-%m-%d') if status == 'Completed' else None

        cursor.execute(
            "INSERT INTO maintenance_work_orders (work_order_number, asset_id, maintenance_type_id, work_order_type, priority, status, issue_date, issue_description, assigned_technician_id, scheduled_start_date, scheduled_end_date, estimated_cost, actual_cost, downtime_hours, completed_by, completed_at, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)",
            (wo_number, asset_id, maint_type, wo_type, priority, status, issue_date,
             f"Maintenance work order {i+1} - {wo_type} maintenance",
             tech, issue_date, scheduled_end,
             random.uniform(100, 1000), actual_cost, downtime,
             tech if status == 'Completed' else None, completed_at)
        )

    # Seed Work Logs for completed work orders
    print("  Creating work logs...")
    cursor.execute("SELECT id FROM maintenance_work_orders WHERE status = 'Completed' LIMIT 15")
    completed_wos = [row['id'] for row in cursor.fetchall()]

    for wo_id in completed_wos:
        cursor.execute("SELECT asset_id, maintenance_type_id FROM maintenance_work_orders WHERE id = ?", (wo_id,))
        wo = cursor.fetchone()
        work_date = (datetime.now() - timedelta(days=random.randint(1, 60))).strftime('%Y-%m-%d')

        cursor.execute(
            "INSERT INTO maintenance_work_logs (work_order_id, asset_id, maintenance_type_id, work_date, technician_id, work_performed, action_taken, labor_hours, labor_cost, parts_cost, total_cost, downtime_hours, notes, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)",
            (wo_id, wo['asset_id'], wo['maintenance_type_id'], work_date,
             random.choice(techs) if techs else None,
             "Routine maintenance work performed", "Completed standard maintenance procedures",
             random.uniform(1, 6), random.uniform(50, 300), random.uniform(20, 200),
             random.uniform(70, 500), random.uniform(0, 3), 'Work completed successfully')
        )

    # Seed Cost Entries
    print("  Creating cost entries...")
    cursor.execute("SELECT id, asset_id FROM maintenance_work_orders LIMIT 20")
    for wo_id, asset_id in cursor.fetchall():
        cost_date = (datetime.now() - timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d')
        cursor.execute(
            "INSERT INTO maintenance_cost_entries (asset_id, work_order_id, cost_type, cost_date, description, amount, created_by) VALUES (?, ?, ?, ?, ?, ?, 1)",
            (asset_id, wo_id, random.choice(['Labor', 'Parts', 'Maintenance', 'External Service']),
            cost_date, "Maintenance cost entry", random.uniform(20, 500))
        )

    # Seed Facility Requests
    print("  Creating facility requests...")
    cursor.execute("SELECT id FROM maintenance_facilities LIMIT 5")
    fac_ids = [row['id'] for row in cursor.fetchall()]

    categories = ['Electrical', 'HVAC', 'Plumbing', 'Structural', 'Safety', 'Cleaning', 'Landscaping']
    req_statuses = ['Open', 'In Progress', 'Completed', 'On Hold']

    for i in range(15):
        fac_id = random.choice(fac_ids)
        req_number = f"FMR-{datetime.now().strftime('%Y%m')}-{i+1:04d}"
        reported_date = (datetime.now() - timedelta(days=random.randint(1, 45))).strftime('%Y-%m-%d')
        is_emergency = 1 if random.random() < 0.2 else 0
        actual_cost_val = random.uniform(50, 1500) if random.random() < 0.5 else 0
        downtime_val = random.uniform(0, 8) if random.random() < 0.5 else 0

        cursor.execute(
            "INSERT INTO maintenance_facility_requests (request_number, facility_id, request_type, category, priority, severity, status, reported_by, reported_date, description, is_emergency, estimated_cost, actual_cost, downtime_hours, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, 1)",
            (req_number, fac_id, random.choice(['Corrective', 'Preventive', 'Emergency']),
            random.choice(categories), random.choice(priorities), random.choice(['Low', 'Medium', 'High']),
            random.choice(req_statuses), reported_date,
            f"Facility maintenance request {i+1} - {random.choice(categories)} issue reported",
            is_emergency, random.uniform(100, 2000), actual_cost_val, downtime_val)
        )

    # Seed Technician Skills
    print("  Creating technician skills...")
    skills_list = [
        ('Electrical Systems', 'Certified Electrician', 'CERT-2024-001', None, 'Advanced', 5),
        ('HVAC Systems', 'EPA 608 Certified', 'EPA-2024-015', None, 'Advanced', 7),
        ('PLC Programming', 'Siemens S7 Certified', 'S7-2024-003', None, 'Intermediate', 3),
        ('Welding', 'AWS Certified Welder', 'AWS-2024-007', None, 'Advanced', 6),
        ('Forklift Operation', 'OSHA Certified', 'OSHA-2024-012', None, 'Intermediate', 2),
        ('Data Center Operations', 'CDCP Certified', 'CDCP-2024-002', None, 'Advanced', 4),
        ('Generator Maintenance', 'Cummins Certified', 'CM-2024-008', None, 'Intermediate', 5),
        ('Fire Safety', 'NFPA Certified', 'NFPA-2024-004', None, 'Advanced', 3),
    ]

    for emp_id in employees[:8]:
        skill = random.choice(skills_list)
        cursor.execute(
            "INSERT INTO maintenance_technician_skills (employee_id, skill_name, certification_name, certification_number, certification_expiry, proficiency_level, years_experience, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, 1)",
            (emp_id, skill[0], skill[1], skill[2], skill[3], skill[4], skill[5])
        )

    # Seed Downtime Logs
    print("  Creating downtime logs...")
    cursor.execute("SELECT id FROM assets WHERE status NOT IN ('Disposed', 'Retired') LIMIT 10")
    dt_assets = [row['id'] for row in cursor.fetchall()]

    reasons = ['Equipment Failure', 'Planned Maintenance', 'Power Outage', 'Bearing Wear', 'Motor Failure', 'Scheduled Inspection']

    for i in range(12):
        asset_id = random.choice(dt_assets)
        log_number = f"DT-{datetime.now().strftime('%Y%m')}-{i+1:04d}"
        start = datetime.now() - timedelta(days=random.randint(1, 60), hours=random.randint(0, 12))
        end = start + timedelta(hours=random.uniform(0.5, 12))
        planned = 1 if random.random() < 0.3 else 0
        total_hours = (end - start).total_seconds() / 3600

        cursor.execute(
            "INSERT INTO maintenance_downtime_logs (log_number, asset_id, downtime_reason, downtime_start, downtime_end, planned_downtime, total_hours, impact_level, root_cause, corrective_action, is_resolved, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1)",
            (log_number, asset_id, random.choice(reasons),
             start.strftime('%Y-%m-%d %H:%M'), end.strftime('%Y-%m-%d %H:%M'),
             planned, total_hours, random.choice(['Low', 'Medium', 'High', 'Critical']),
             f"Root cause: {random.choice(['wear and tear', 'ageing component', 'operating conditions'])}",
             f"Action taken: {random.choice(['replaced part', 'adjusted settings', 'performed calibration'])}")
        )

    # Seed Parts Usage
    print("  Creating parts usage records...")
    cursor.execute("SELECT id FROM maintenance_work_orders LIMIT 15")
    wo_ids = [row['id'] for row in cursor.fetchall()]

    parts = [
        ('Bearing Assembly', 'BRG-001', 'Unit'),
        ('Motor Controller', 'MCT-002', 'Unit'),
        ('Hydraulic Seal', 'HDS-003', 'Unit'),
        ('Filter Cartridge', 'FLC-004', 'Unit'),
        ('Drive Belt', 'DRB-005', 'Unit'),
        ('Sensor Module', 'SNS-006', 'Unit'),
        ('Coolant Fluid', 'CLF-007', 'Liter'),
        ('Lubricant Oil', 'LBO-008', 'Liter'),
    ]

    for i, wo_id in enumerate(wo_ids[:10]):
        part = random.choice(parts)
        qty = random.randint(1, 5)
        usage_number = f"MPU-{datetime.now().strftime('%Y%m')}-{i+1:04d}"
        issue_date = (datetime.now() - timedelta(days=random.randint(1, 45))).strftime('%Y-%m-%d')
        unit_cost = random.uniform(10, 200)
        total_cost = qty * unit_cost

        cursor.execute(
            "INSERT INTO maintenance_parts_usage (usage_number, work_order_id, part_number, part_name, quantity_requested, quantity_issued, quantity_used, unit_of_measure, issue_date, unit_cost, total_cost, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)",
            (usage_number, wo_id, part[1], part[0], qty, qty, qty, part[2], issue_date, unit_cost, total_cost)
        )

    # Seed Labor Logs
    print("  Creating labor logs...")
    for i, wo_id in enumerate(wo_ids[:10]):
        tech = random.choice(techs) if techs else None
        log_number = f"MLL-{datetime.now().strftime('%Y%m')}-{i+1:04d}"
        hours = random.uniform(1, 8)
        work_date = (datetime.now() - timedelta(days=random.randint(1, 45))).strftime('%Y-%m-%d')
        hourly_rate = random.uniform(25, 75)
        labor_cost = hours * hourly_rate

        cursor.execute(
            "INSERT INTO maintenance_labor_logs (log_number, work_order_id, technician_id, work_date, total_hours, regular_hours, overtime_hours, hourly_rate, labor_cost, work_description, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (log_number, wo_id, tech, work_date, hours, hours, 0, hourly_rate, labor_cost,
             "Routine maintenance work", 'Work completed as scheduled')
        )

    conn.commit()
    print("Maintenance data seeded successfully!")
    conn.close()


if __name__ == '__main__':
    seed_maintenance_data()
