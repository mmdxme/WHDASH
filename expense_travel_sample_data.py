"""
Expense / Travel Management - Sample Data Seeder
================================================
Seeds realistic demo data for the Expense/Travel module.

Usage:
    python expense_travel_sample_data.py
"""

import sqlite3
import random
from datetime import datetime, timedelta
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'warehouse.db')

def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def seed_sample_data():
    """Seed sample expense/travel data."""
    db = get_db()
    cursor = db.cursor()

    # Get some existing employees from HR module
    employees = cursor.execute("""
        SELECT id, employee_code, first_name, last_name, '' as department_id, '' as department_name, '' as branch_id, '' as branch_name, 1 as company_id
        FROM hr_employees
        LIMIT 10
    """).fetchall()

    if not employees:
        # Create sample employees if none exist
        employees = [
            (1, 'EMP001', 'Ahmed', 'Al-Mansouri', 1, 'Finance', 1, 'Dubai HQ', 1),
            (2, 'EMP002', 'Fatima', 'Al-Hassan', 1, 'Finance', 1, 'Dubai HQ', 1),
            (3, 'EMP003', 'Mohammed', 'Al-Rashid', 2, 'Operations', 1, 'Dubai HQ', 1),
            (4, 'EMP004', 'Sara', 'Khan', 3, 'Sales', 1, 'Dubai HQ', 1),
            (5, 'EMP005', 'Ali', 'Ahmed', 2, 'Operations', 2, 'Abu Dhabi Branch', 1),
        ]

    # Get expense categories
    categories = cursor.execute("SELECT id, code, name FROM expense_categories LIMIT 10").fetchall()

    # Sample purposes
    purposes = [
        'Client meeting in Dubai',
        'Project kickoff presentation',
        'Supplier negotiation in Abu Dhabi',
        'Training workshop attendance',
        'Conference participation',
        'Site inspection visit',
        'Customer on-site support',
        'Sales presentation to prospective client',
        'Technical review meeting',
        'Annual review committee'
    ]

    # Sample vendors
    vendors = [
        'Emirates Hotel LLC',
        'Dubai Airlines',
        'Etihad Airways',
        'Rotana Hotels',
        'Marriott Dubai',
        'Car Rental Dubai',
        'Abu Dhabi Taxis',
        'Emirates Catering',
        'Business Bay Restaurant',
        'Dubai Convention Center'
    ]

    print("Seeding expense claims...")

    # Create expense claims
    claim_ids = []
    for i in range(25):
        emp = random.choice(employees if isinstance(employees[0], tuple) else [(e['id'], e['employee_code'], f"{e['first_name']} {e['last_name']}", e['department_id'], e['department_name'], e['branch_id'], e['branch_name'], e['company_id']) for e in employees])

        claim_date = (datetime.now() - timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d')
        submission_date = (datetime.strptime(claim_date, '%Y-%m-%d') + timedelta(days=random.randint(0, 2))).strftime('%Y-%m-%d') if random.random() > 0.3 else None

        statuses = ['draft', 'submitted', 'under_review', 'approved', 'rejected', 'paid', 'returned']
        status_weights = [0.1, 0.15, 0.1, 0.2, 0.1, 0.25, 0.1]
        status = random.choices(statuses, weights=status_weights)[0]

        claim_number = f"EXP{10001 + i:05d}"
        total_amount = round(random.uniform(50, 5000), 2)

        cursor.execute("""
            INSERT INTO expense_claims (
                claim_number, status, employee_id, employee_code, employee_name,
                department_id, department_name, branch_id, branch_name, company_id,
                claim_date, submission_date, currency, total_amount, total_amount_base,
                business_purpose, cost_center_name, cost_center_code,
                submitted_by, submitted_by_name, approved_by_name, rejection_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            claim_number, status, emp[0], emp[1], f"{emp[2]} {emp[3] if len(emp) > 3 else emp[2]}",
            emp[4], emp[5], emp[6], emp[7], emp[8] if len(emp) > 8 else 1,
            claim_date, submission_date, 'AED', total_amount, total_amount,
            random.choice(purposes),
            f"CC-{random.randint(100, 999)}", f"CC{random.randint(100, 999)}",
            emp[0], f"{emp[2]} {emp[3] if len(emp) > 3 else emp[2]}",
            random.choice([None, 'Manager User', 'Finance Approver']) if status == 'approved' else None,
            'Policy exceeded without justification' if status == 'rejected' else None
        ))

        claim_id = cursor.lastrowid
        claim_ids.append(claim_id)

        # Add expense lines
        num_lines = random.randint(1, 5)
        for j in range(num_lines):
            cat = random.choice(categories) if categories else (1, 'TRAVEL', 'Travel')
            line_amount = round(total_amount / num_lines, 2)

            cursor.execute("""
                INSERT INTO expense_claim_lines (
                    claim_id, line_number, category_id, category_code, category_name,
                    expense_date, expense_description, amount, amount_currency,
                    amount_base, vendor_name, has_receipt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                claim_id, j + 1, cat[0], cat[1], cat[2],
                claim_date, f"{random.choice(['Business expense', 'Travel cost', 'Client entertainment'])} - {random.choice(vendors)}",
                line_amount, 'AED', line_amount,
                random.choice(vendors), random.choice([0, 1])
            ))

    db.commit()
    print(f"Created {len(claim_ids)} expense claims")

    print("Seeding travel requests...")

    # Create travel requests
    travel_ids = []
    for i in range(15):
        emp = random.choice(employees if isinstance(employees[0], tuple) else [(e['id'], e['employee_code'], f"{e['first_name']} {e['last_name']}", e['department_id'], e['department_name'], e['branch_id'], e['branch_name'], e['company_id']) for e in employees])

        start_date = (datetime.now() + timedelta(days=random.randint(-30, 60))).strftime('%Y-%m-%d')
        end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=random.randint(1, 7))).strftime('%Y-%m-%d')

        statuses = ['draft', 'submitted', 'approved', 'rejected', 'completed', 'cancelled']
        status = random.choice(statuses)

        countries = ['UAE', 'Saudi Arabia', 'United Kingdom', 'USA', 'Germany', 'India', 'Singapore']
        cities = ['Dubai', 'Riyadh', 'London', 'New York', 'Berlin', 'Mumbai', 'Singapore']
        country = random.choice(countries)
        city = cities[countries.index(country)]

        travel_number = f"TRV{10001 + i:05d}"
        est_cost = round(random.uniform(500, 15000), 2)
        advance = round(est_cost * random.uniform(0.3, 0.8), 2) if random.random() > 0.5 else 0

        cursor.execute("""
            INSERT INTO travel_requests (
                travel_number, status, employee_id, employee_code, employee_name,
                department_id, department_name, branch_id, branch_name, company_id,
                trip_purpose, trip_type, destination_country, destination_city,
                travel_start_date, travel_end_date, total_trip_days,
                request_date, estimated_total_cost, estimated_total_cost_currency,
                advance_requested, advance_requested_currency,
                submitted_by, submitted_by_name, approved_by_name, rejection_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            travel_number, status, emp[0], emp[1], f"{emp[2]} {emp[3] if len(emp) > 3 else emp[2]}",
            emp[4], emp[5], emp[6], emp[7], emp[8] if len(emp) > 8 else 1,
            random.choice(purposes), random.choice(['business', 'training', 'conference']),
            country, city,
            start_date, end_date, (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days + 1,
            (datetime.now() - timedelta(days=random.randint(1, 45))).strftime('%Y-%m-%d'),
            est_cost, 'AED', advance, 'AED',
            emp[0], f"{emp[2]} {emp[3] if len(emp) > 3 else emp[2]}",
            random.choice([None, 'Manager User']) if status == 'approved' else None,
            'Budget constraints' if status == 'rejected' else None
        ))

        travel_id = cursor.lastrowid
        travel_ids.append(travel_id)

        # Add itinerary items
        if status in ['approved', 'completed']:
            num_segments = random.randint(2, 5)
            for seg in range(num_segments):
                cursor.execute("""
                    INSERT INTO travel_itineraries (
                        travel_request_id, itinerary_type, sequence_order, segment_name,
                        segment_date, estimated_cost, is_confirmed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    travel_id,
                    random.choice(['flight', 'hotel', 'transport', 'meal']),
                    seg + 1,
                    random.choice(['Flight to ' + city, 'Hotel Stay', 'Airport Transfer', 'Client Dinner']),
                    start_date if seg == 0 else (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=seg)).strftime('%Y-%m-%d'),
                    round(est_cost / num_segments, 2),
                    1
                ))

    db.commit()
    print(f"Created {len(travel_ids)} travel requests")

    print("Seeding cash advances...")

    # Create cash advances
    advance_ids = []
    for i in range(12):
        emp = random.choice(employees if isinstance(employees[0], tuple) else [(e['id'], e['employee_code'], f"{e['first_name']} {e['last_name']}", e['department_id'], e['department_name'], e['branch_id'], e['branch_name'], e['company_id']) for e in employees])

        request_date = (datetime.now() - timedelta(days=random.randint(1, 60))).strftime('%Y-%m-%d')

        statuses = ['draft', 'submitted', 'approved', 'issued', 'settled', 'partially_settled', 'rejected']
        status = random.choice(statuses)

        requested_amount = round(random.uniform(200, 5000), 2)
        approved_amount = requested_amount if status in ['approved', 'issued', 'settled', 'partially_settled'] else 0
        outstanding = requested_amount - random.uniform(0, requested_amount) if status in ['partially_settled', 'settled'] else approved_amount

        advance_number = f"ADV{10001 + i:05d}"

        cursor.execute("""
            INSERT INTO cash_advances (
                advance_number, status, employee_id, employee_code, employee_name,
                department_id, department_name, branch_id, branch_name, company_id,
                request_date, requested_amount, requested_currency,
                requested_amount_base, approval_date, approved_amount, approved_amount_currency,
                issuance_date, is_issued, purpose, outstanding_balance,
                submitted_by, submitted_by_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            advance_number, status, emp[0], emp[1], f"{emp[2]} {emp[3] if len(emp) > 3 else emp[2]}",
            emp[4], emp[5], emp[6], emp[7], emp[8] if len(emp) > 8 else 1,
            request_date, requested_amount, 'AED', requested_amount,
            (datetime.strptime(request_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d') if status != 'draft' else None,
            approved_amount, 'AED',
            (datetime.strptime(request_date, '%Y-%m-%d') + timedelta(days=2)).strftime('%Y-%m-%d') if status in ['issued', 'settled', 'partially_settled'] else None,
            1 if status in ['issued', 'settled', 'partially_settled'] else 0,
            random.choice(['Business travel to ' + random.choice(['Dubai', 'Abu Dhabi', 'Riyadh', 'London']), 'Conference attendance', 'Client meeting advance']),
            round(outstanding, 2),
            emp[0], f"{emp[2]} {emp[3] if len(emp) > 3 else emp[2]}"
        ))

        advance_id = cursor.lastrowid
        advance_ids.append(advance_id)

    db.commit()
    print(f"Created {len(advance_ids)} cash advances")

    print("Seeding reimbursements...")

    # Create reimbursements
    for i in range(10):
        # Link to some paid claims
        paid_claims = cursor.execute("SELECT id, claim_number, employee_id, employee_name, total_amount, department_name FROM expense_claims WHERE status = 'paid' LIMIT 5").fetchall()

        if paid_claims:
            claim = random.choice(paid_claims)

            statuses = ['pending', 'approved', 'paid']
            status = random.choice(statuses)

            reim_number = f"REIM{10001 + i:05d}"
            advance_deduct = round(random.uniform(0, claim['total_amount'] * 0.3), 2) if random.random() > 0.5 else 0
            net_reim = claim['total_amount'] - advance_deduct

            cursor.execute("""
                INSERT INTO expense_reimbursements (
                    reimbursement_number, status, claim_id, claim_number,
                    employee_id, employee_name, department_name,
                    reimbursement_amount, currency, net_reimbursement,
                    advance_deduction, approved_by_name, approved_date,
                    payment_date, payment_reference
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                reim_number, status, claim['id'], claim['claim_number'],
                claim['employee_id'], claim['employee_name'], claim['department_name'],
                claim['total_amount'], 'AED', net_reim,
                advance_deduct,
                'Finance User' if status in ['approved', 'paid'] else None,
                datetime.now().strftime('%Y-%m-%d') if status in ['approved', 'paid'] else None,
                (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d') if status == 'paid' else None,
                f"PAY-{random.randint(100000, 999999)}" if status == 'paid' else None
            ))

    db.commit()
    print("Created 10 reimbursements")

    print("Seeding expense policies...")

    # Create expense policies
    policies = [
        ('POL-EXP-001', 'Standard Expense Policy', 'Standard expense policy for all employees', 'expense', 5000, 10000, 500),
        ('POL-EXP-002', 'Travel Expense Policy', 'Policy for travel-related expenses', 'travel', 10000, 20000, 1000),
        ('POL-EXP-003', 'Client Entertainment Policy', 'Policy for client entertainment expenses', 'expense', 2000, 5000, 500),
    ]

    for code, name, desc, ptype, max_trans, max_month, approval_above in policies:
        cursor.execute("""
            INSERT OR IGNORE INTO expense_policies (
                policy_code, policy_name, policy_type, description,
                max_per_transaction, max_per_month, approval_required_above,
                is_active, requires_receipt
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1)
        """, (code, name, desc, ptype, max_trans, max_month, approval_above))

    db.commit()
    print("Created expense policies")

    print("Seeding receipts...")

    # Create some receipts
    for i in range(20):
        claim = random.choice(claim_ids) if claim_ids else 1
        receipt_date = (datetime.now() - timedelta(days=random.randint(1, 60))).strftime('%Y-%m-%d')

        cursor.execute("""
            INSERT INTO expense_receipts (
                receipt_number, claim_id, file_name, file_path,
                receipt_date, merchant_name, total_amount, currency,
                uploaded_by, uploaded_by_name, status, is_linked, is_valid
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"RCP{20001 + i:05d}",
            claim,
            f"receipt_{i+1}.pdf",
            f"/static/uploads/expense_receipts/receipt_{i+1}.pdf",
            receipt_date,
            random.choice(vendors),
            round(random.uniform(20, 1000), 2),
            'AED',
            1, 'Demo User',
            random.choice(['pending', 'valid', 'valid', 'valid']),
            random.choice([0, 1]),
            random.choice([0, 1, 1, 1])
        ))

    db.commit()
    print("Created 20 receipts")

    print("\n=== Expense/Travel Sample Data Seeding Complete ===")
    print(f"  - Expense Claims: {len(claim_ids)}")
    print(f"  - Travel Requests: {len(travel_ids)}")
    print(f"  - Cash Advances: {len(advance_ids)}")
    print(f"  - Reimbursements: 10")
    print(f"  - Expense Policies: 3")
    print(f"  - Receipts: 20")

    db.close()

if __name__ == '__main__':
    print("Starting Expense/Travel sample data seeding...")
    seed_sample_data()
    print("Done!")