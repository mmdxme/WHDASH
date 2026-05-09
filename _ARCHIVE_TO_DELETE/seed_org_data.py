"""
Organization Structure Setup & Seeder
=====================================
Creates and populates: branches, departments, divisions, teams
Enhances: companies, warehouses, company_branches, company_facilities
With comprehensive SAP-style sample data.
"""

from database import get_db_context, get_all, get_one

def create_org_tables():
    """Create missing organization tables."""
    with get_db_context() as db:
        # branches table
        db.execute("""
            CREATE TABLE IF NOT EXISTS branches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                company_id INTEGER,
                branch_type TEXT,
                description TEXT,
                address TEXT,
                city TEXT,
                region TEXT,
                country TEXT,
                postal_code TEXT,
                phone TEXT,
                email TEXT,
                manager_name TEXT,
                manager_phone TEXT,
                manager_email TEXT,
                is_active INTEGER DEFAULT 1,
                is_operational INTEGER DEFAULT 1,
                opened_date TEXT,
                area_sqm REAL,
                employee_count INTEGER,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
        """)

        # departments table
        db.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                name_ar TEXT,
                name_fa TEXT,
                company_id INTEGER,
                branch_id INTEGER,
                division_id INTEGER,
                department_type TEXT,
                description TEXT,
                cost_center TEXT,
                head_employee_id INTEGER,
                parent_department_id INTEGER,
                is_active INTEGER DEFAULT 1,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY (company_id) REFERENCES companies(id),
                FOREIGN KEY (branch_id) REFERENCES branches(id)
            )
        """)

        # divisions table
        db.execute("""
            CREATE TABLE IF NOT EXISTS divisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                name_ar TEXT,
                company_id INTEGER,
                division_type TEXT,
                description TEXT,
                head_employee_id INTEGER,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
        """)

        # teams table
        db.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                company_id INTEGER,
                department_id INTEGER,
                team_lead_id INTEGER,
                team_type TEXT,
                description TEXT,
                shift_pattern TEXT,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY (company_id) REFERENCES companies(id),
                FOREIGN KEY (department_id) REFERENCES departments(id)
            )
        """)

        db.commit()
        print("Organization tables created successfully.")

def seed_organization_data():
    """Seed comprehensive sample data for all organization entities."""

    # Get company IDs
    companies = get_all("SELECT id, name FROM companies")
    company_map = {c['name']: c['id'] for c in companies}
    print(f"Found {len(companies)} companies: {list(company_map.keys())}")

    with get_db_context() as db:

        # ============================================================
        # SEED BRANCHES (for each company)
        # ============================================================
        branch_data = [
            # WHDASH Trading LLC branches
            {'code': 'WHD-DXB-01', 'name': 'Dubai Main Branch', 'company_id': company_map.get('WHDASH Trading LLC'),
             'branch_type': 'Headquarters', 'city': 'Dubai', 'region': 'Dubai', 'country': 'UAE',
             'address': 'Plot 123, Al Quoz Industrial Area 3', 'phone': '+971-4-333-1111', 'email': 'dxb-hq@whdash.com',
             'manager_name': 'Ahmed Al Maktoum', 'manager_phone': '+971-50-123-4567', 'manager_email': 'ahmed.m@whdash.com',
             'opened_date': '2018-01-15', 'area_sqm': 2500, 'employee_count': 45},
            {'code': 'WHD-ABU-01', 'name': 'Abu Dhabi Branch', 'company_id': company_map.get('WHDASH Trading LLC'),
             'branch_type': 'Regional Office', 'city': 'Abu Dhabi', 'region': 'Abu Dhabi', 'country': 'UAE',
             'address': 'Khalifa City A, Street 12', 'phone': '+971-2-555-2222', 'email': 'abu-office@whdash.com',
             'manager_name': 'Khalid Hassan', 'manager_phone': '+971-50-987-6543', 'manager_email': 'khalid.h@whdash.com',
             'opened_date': '2019-06-01', 'area_sqm': 1200, 'employee_count': 22},

            # SDAD branches
            {'code': 'SDD-DXB-01', 'name': 'SDAD Dubai HQ', 'company_id': company_map.get('SDAD'),
             'branch_type': 'Headquarters', 'city': 'Dubai', 'region': 'Dubai', 'country': 'UAE',
             'address': 'Business Bay, Tower 3, Floor 12', 'phone': '+971-4-444-1000', 'email': 'info@sdad.ae',
             'manager_name': 'Mohammed Al Rashidi', 'manager_phone': '+971-50-555-1234', 'manager_email': 'm.alrashidi@sdad.ae',
             'opened_date': '2015-03-20', 'area_sqm': 3500, 'employee_count': 85},
            {'code': 'SDD-SHJ-01', 'name': 'Sharjah Branch', 'company_id': company_map.get('SDAD'),
             'branch_type': 'Sales Office', 'city': 'Sharjah', 'region': 'Sharjah', 'country': 'UAE',
             'address': 'Al Khan Area, Near City Center', 'phone': '+971-6-555-3300', 'email': 'shj@sdad.ae',
             'manager_name': 'Salim Al Qasimi', 'manager_phone': '+971-50-444-9876', 'manager_email': 's.alqasimi@sdad.ae',
             'opened_date': '2017-09-10', 'area_sqm': 600, 'employee_count': 12},
            {'code': 'SDD-AJM-01', 'name': 'Ajman Branch', 'company_id': company_map.get('SDAD'),
             'branch_type': 'Sales Office', 'city': 'Ajman', 'region': 'Ajman', 'country': 'UAE',
             'address': 'Al Swaidi Street, Near Chamzar Metro', 'phone': '+971-6-744-5500', 'email': 'ajm@sdad.ae',
             'manager_name': 'Rashid Al Zahmi', 'manager_phone': '+971-50-333-7654', 'manager_email': 'r.alzahmi@sdad.ae',
             'opened_date': '2020-02-15', 'area_sqm': 400, 'employee_count': 8},

            # AFRA branches
            {'code': 'AFR-JLT-01', 'name': 'AFRA JLT Office', 'company_id': company_map.get('AFRA'),
             'branch_type': 'Headquarters', 'city': 'Dubai', 'region': 'JLT', 'country': 'UAE',
             'address': 'JLT Cluster T, Tiffany Tower, Floor 18', 'phone': '+971-4-555-8800', 'email': 'dubai@afra.ae',
             'manager_name': 'Fatima Al Hashimi', 'manager_phone': '+971-50-777-4321', 'manager_email': 'f.hashimi@afra.ae',
             'opened_date': '2016-08-01', 'area_sqm': 800, 'employee_count': 18},
            {'code': 'AFR-DIC-01', 'name': 'AFRA DIC Branch', 'company_id': company_map.get('AFRA'),
             'branch_type': 'Operations Center', 'city': 'Dubai', 'region': 'DIC', 'country': 'UAE',
             'address': 'Dubai Internet City, Building 14', 'phone': '+971-4-555-9900', 'email': 'ops@afra.ae',
             'manager_name': 'Omar Al Batin', 'manager_phone': '+971-50-888-1234', 'manager_email': 'o.albatin@afra.ae',
             'opened_date': '2019-11-20', 'area_sqm': 500, 'employee_count': 10},

            # Carmania branches
            {'code': 'CAR-DXB-01', 'name': 'Carmania Showroom', 'company_id': company_map.get('Carmania'),
             'branch_type': 'Showroom', 'city': 'Dubai', 'region': 'Deira', 'country': 'UAE',
             'address': 'Al Muraqqabat Street, Deira', 'phone': '+971-4-222-7700', 'email': 'showroom@carmania.ae',
             'manager_name': 'Jamal Al Bastaki', 'manager_phone': '+971-50-999-2468', 'manager_email': 'j.albastaki@carmania.ae',
             'opened_date': '2012-05-10', 'area_sqm': 1500, 'employee_count': 30},
            {'code': 'CAR-ABU-01', 'name': 'Carmania Abu Dhabi', 'company_id': company_map.get('Carmania'),
             'branch_type': 'Service Center', 'city': 'Abu Dhabi', 'region': 'Al Ain', 'country': 'UAE',
             'address': 'Khalifa Street, Near Al Ain Rotana', 'phone': '+971-3-777-5500', 'email': 'abudhabi@carmania.ae',
             'manager_name': 'Hassan Al Kaabi', 'manager_phone': '+971-50-111-3579', 'manager_email': 'h.alkaabi@carmania.ae',
             'opened_date': '2018-07-22', 'area_sqm': 900, 'employee_count': 20},

            # General branches
            {'code': 'GEN-DXB-01', 'name': 'General Trading Dubai', 'company_id': company_map.get('General'),
             'branch_type': 'Warehouse & Office', 'city': 'Dubai', 'region': 'Al Aweer', 'country': 'UAE',
             'address': 'Al Aweer Vegetable Market Area', 'phone': '+971-4-888-1100', 'email': 'trade@general.ae',
             'manager_name': 'Ali Al Marzouqi', 'manager_phone': '+971-50-222-1593', 'manager_email': 'a.almarzouqi@general.ae',
             'opened_date': '2010-01-05', 'area_sqm': 5000, 'employee_count': 55},
        ]

        for branch in branch_data:
            try:
                db.execute("""
                    INSERT OR IGNORE INTO branches (code, name, company_id, branch_type, description, address, city, region, country, postal_code, phone, email, manager_name, manager_phone, manager_email, is_active, is_operational, opened_date, area_sqm, employee_count, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    branch['code'], branch['name'], branch['company_id'], branch['branch_type'],
                    '', branch['address'], branch['city'], branch['region'],
                    branch['country'], branch.get('postal_code', ''), branch['phone'], branch['email'],
                    branch['manager_name'], branch['manager_phone'], branch['manager_email'],
                    branch['opened_date'], branch['area_sqm'], branch['employee_count']
                ))
            except Exception as e:
                print(f"Branch {branch['code']} error: {e}")

        print(f"Seeded {len(branch_data)} branches.")

        # ============================================================
        # SEED DIVISIONS
        # ============================================================
        division_data = [
            {'code': 'DIV-CORP', 'name': 'Corporate', 'company_id': None, 'division_type': 'Corporate',
             'description': 'Executive management and corporate functions'},
            {'code': 'DIV-SALES', 'name': 'Sales & Marketing', 'company_id': None, 'division_type': 'Business',
             'description': 'Sales operations, marketing, and customer management'},
            {'code': 'DIV-OPS', 'name': 'Operations', 'company_id': None, 'division_type': 'Business',
             'description': 'Warehouse, logistics, and supply chain operations'},
            {'code': 'DIV-FIN', 'name': 'Finance & Accounting', 'company_id': None, 'division_type': 'Support',
             'description': 'Financial management, accounting, and treasury'},
            {'code': 'DIV-HR', 'name': 'Human Resources', 'company_id': None, 'division_type': 'Support',
             'description': 'HR management, recruitment, and employee development'},
            {'code': 'DIV-IT', 'name': 'Information Technology', 'company_id': None, 'division_type': 'Support',
             'description': 'IT infrastructure, systems, and digital transformation'},
            {'code': 'DIV-PROC', 'name': 'Procurement', 'company_id': None, 'division_type': 'Business',
             'description': 'Purchasing, supplier management, and sourcing'},
            {'code': 'DIV-QA', 'name': 'Quality Assurance', 'company_id': None, 'division_type': 'Support',
             'description': 'Quality control, compliance, and process improvement'},
        ]

        for div in division_data:
            try:
                db.execute("""
                    INSERT OR IGNORE INTO divisions (code, name, company_id, division_type, description, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                """, (div['code'], div['name'], div['company_id'], div['division_type'], div['description']))
            except Exception as e:
                print(f"Division {div['code']} error: {e}")

        print(f"Seeded {len(division_data)} divisions.")

        # ============================================================
        # SEED DEPARTMENTS
        # ============================================================
        department_data = [
            # Corporate
            {'code': 'DEPT-EXE', 'name': 'Executive Management', 'company_id': None, 'department_type': 'Executive',
             'description': 'CEO, CFO, COO and other C-level executives', 'cost_center': 'CC-1001'},
            {'code': 'DEPT-CS', 'name': 'Company Secretariat', 'company_id': None, 'department_type': 'Corporate',
             'description': 'Legal, compliance, and company secretarial duties', 'cost_center': 'CC-1002'},
            {'code': 'DEPT-COMM', 'name': 'Communications', 'company_id': None, 'department_type': 'Corporate',
             'description': 'Internal and external communications, PR', 'cost_center': 'CC-1003'},

            # Sales & Marketing
            {'code': 'DEPT-SMO', 'name': 'Sales Management', 'company_id': None, 'department_type': 'Commercial',
             'description': 'Overall sales strategy and management', 'cost_center': 'CC-2001'},
            {'code': 'DEPT-BDO', 'name': 'Business Development', 'company_id': None, 'department_type': 'Commercial',
             'description': 'New market expansion and partnership development', 'cost_center': 'CC-2002'},
            {'code': 'DEPT-MKT', 'name': 'Marketing', 'company_id': None, 'department_type': 'Commercial',
             'description': 'Marketing campaigns, digital marketing, brand management', 'cost_center': 'CC-2003'},
            {'code': 'DEPT-CRM', 'name': 'Customer Relationship Management', 'company_id': None, 'department_type': 'Commercial',
             'description': 'Customer service, retention, and account management', 'cost_center': 'CC-2004'},
            {'code': 'DEPT-EXP', 'name': 'Export & International Sales', 'company_id': None, 'department_type': 'Commercial',
             'description': 'Export documentation, international logistics', 'cost_center': 'CC-2005'},

            # Operations
            {'code': 'DEPT-WMS', 'name': 'Warehouse Management', 'company_id': None, 'department_type': 'Operations',
             'description': 'Inbound, storage, picking, packing, outbound operations', 'cost_center': 'CC-3001'},
            {'code': 'DEPT-LOG', 'name': 'Logistics & Transportation', 'company_id': None, 'department_type': 'Operations',
             'description': 'Fleet management, delivery, route optimization', 'cost_center': 'CC-3002'},
            {'code': 'DEPT-IMP', 'name': 'Import & Customs', 'company_id': None, 'department_type': 'Operations',
             'description': 'Import clearance, customs documentation, duties', 'cost_center': 'CC-3003'},
            {'code': 'DEPT-QC', 'name': 'Quality Control', 'company_id': None, 'department_type': 'Operations',
             'description': 'Incoming inspection, stock quality, returns handling', 'cost_center': 'CC-3004'},
            {'code': 'DEPT-PLN', 'name': 'Planning & Forecasting', 'company_id': None, 'department_type': 'Operations',
             'description': 'Demand planning, inventory optimization, replenishment', 'cost_center': 'CC-3005'},

            # Finance
            {'code': 'DEPT-FIN', 'name': 'Finance', 'company_id': None, 'department_type': 'Finance',
             'description': 'Financial reporting, management accounting, budgeting', 'cost_center': 'CC-4001'},
            {'code': 'DEPT-ACC', 'name': 'Accounting', 'company_id': None, 'department_type': 'Finance',
             'description': 'AP/AR, general ledger, month-end close', 'cost_center': 'CC-4002'},
            {'code': 'DEPT-TRE', 'name': 'Treasury', 'company_id': None, 'department_type': 'Finance',
             'description': 'Cash management, banking, forex, working capital', 'cost_center': 'CC-4003'},
            {'code': 'DEPT-AUD', 'name': 'Internal Audit', 'company_id': None, 'department_type': 'Finance',
             'description': 'Internal controls, audit, risk management', 'cost_center': 'CC-4004'},
            {'code': 'DEPT-TAX', 'name': 'Tax & Compliance', 'company_id': None, 'department_type': 'Finance',
             'description': 'VAT, corporate tax, transfer pricing', 'cost_center': 'CC-4005'},

            # HR
            {'code': 'DEPT-HRS', 'name': 'HR Strategy', 'company_id': None, 'department_type': 'HR',
             'description': 'HR strategy, talent management, HRBP', 'cost_center': 'CC-5001'},
            {'code': 'DEPT-REC', 'name': 'Recruitment', 'company_id': None, 'department_type': 'HR',
             'description': 'Talent acquisition, onboarding, employer branding', 'cost_center': 'CC-5002'},
            {'code': 'DEPT-PAY', 'name': 'Payroll & Benefits', 'company_id': None, 'department_type': 'HR',
             'description': 'Payroll processing, benefits administration', 'cost_center': 'CC-5003'},
            {'code': 'DEPT-TRN', 'name': 'Training & Development', 'company_id': None, 'department_type': 'HR',
             'description': 'L&D, skills development, succession planning', 'cost_center': 'CC-5004'},
            {'code': 'DEPT-SAF', 'name': 'Health & Safety', 'company_id': None, 'department_type': 'HR',
             'description': 'OSHA compliance, workplace safety, wellness', 'cost_center': 'CC-5005'},

            # IT
            {'code': 'DEPT-INF', 'name': 'Infrastructure', 'company_id': None, 'department_type': 'IT',
             'description': 'Networks, servers, cloud, IT operations', 'cost_center': 'CC-6001'},
            {'code': 'DEPT-APP', 'name': 'Applications', 'company_id': None, 'department_type': 'IT',
             'description': 'ERP, CRM, WMS, business applications', 'cost_center': 'CC-6002'},
            {'code': 'DEPT-CYB', 'name': 'Cybersecurity', 'company_id': None, 'department_type': 'IT',
             'description': 'Security operations, SOC, incident response', 'cost_center': 'CC-6003'},
            {'code': 'DEPT-BI', 'name': 'Business Intelligence', 'company_id': None, 'department_type': 'IT',
             'description': 'Data analytics, dashboards, BI tools', 'cost_center': 'CC-6004'},

            # Procurement
            {'code': 'DEPT-PUR', 'name': 'Purchasing', 'company_id': None, 'department_type': 'Procurement',
             'description': 'Purchase orders, procurement operations', 'cost_center': 'CC-7001'},
            {'code': 'DEPT-SUP', 'name': 'Supplier Management', 'company_id': None, 'department_type': 'Procurement',
             'description': 'Supplier evaluation, contracts, performance', 'cost_center': 'CC-7002'},
            {'code': 'DEPT-CON', 'name': 'Contract Management', 'company_id': None, 'department_type': 'Procurement',
             'description': 'Vendor contracts, SLA management', 'cost_center': 'CC-7003'},

            # QA/Compliance
            {'code': 'DEPT-QLT', 'name': 'Quality Management', 'company_id': None, 'department_type': 'Quality',
             'description': 'ISO compliance, process improvement, Six Sigma', 'cost_center': 'CC-8001'},
            {'code': 'DEPT-ENV', 'name': 'Environment & Sustainability', 'company_id': None, 'department_type': 'Quality',
             'description': 'Environmental compliance, sustainability initiatives', 'cost_center': 'CC-8002'},
        ]

        for dept in department_data:
            try:
                db.execute("""
                    INSERT OR IGNORE INTO departments (code, name, company_id, department_type, description, cost_center, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                """, (dept['code'], dept['name'], dept['company_id'], dept['department_type'],
                      dept['description'], dept['cost_center']))
            except Exception as e:
                print(f"Department {dept['code']} error: {e}")

        print(f"Seeded {len(department_data)} departments.")

        # ============================================================
        # SEED TEAMS
        # ============================================================
        team_data = [
            {'code': 'TEAM-WMS-01', 'name': 'Receiving Team', 'department_id': None, 'team_type': 'Operational',
             'description': 'Inbound goods receiving, inspection, putaway'},
            {'code': 'TEAM-WMS-02', 'name': 'Picking Team', 'department_id': None, 'team_type': 'Operational',
             'description': 'Order picking, packing, labeling'},
            {'code': 'TEAM-WMS-03', 'name': 'Dispatch Team', 'department_id': None, 'team_type': 'Operational',
             'description': 'Outbound loading, vehicle dispatch, POD collection'},
            {'code': 'TEAM-WMS-04', 'name': 'Inventory Control Team', 'department_id': None, 'team_type': 'Analytical',
             'description': 'Cycle counts, stock adjustments, reconciliation'},
            {'code': 'TEAM-WMS-05', 'name': 'Returns Processing Team', 'department_id': None, 'team_type': 'Operational',
             'description': 'Returns intake, inspection, credit processing'},

            {'code': 'TEAM-LOG-01', 'name': 'Delivery Fleet Team A', 'department_id': None, 'team_type': 'Field',
             'description': 'Same-day delivery routes Dubai South'},
            {'code': 'TEAM-LOG-02', 'name': 'Delivery Fleet Team B', 'department_id': None, 'team_type': 'Field',
             'description': 'Next-day delivery routes Northern Emirates'},
            {'code': 'TEAM-LOG-03', 'name': 'Transport Planning Team', 'department_id': None, 'team_type': 'Planning',
             'description': 'Route optimization, carrier management'},

            {'code': 'TEAM-SAL-01', 'name': 'Inside Sales Team', 'department_id': None, 'team_type': 'Sales',
             'description': 'Inbound inquiries, quotation generation'},
            {'code': 'TEAM-SAL-02', 'name': 'Field Sales Team Dubai', 'department_id': None, 'team_type': 'Sales',
             'description': 'Direct sales Dubai and Northern Emirates'},
            {'code': 'TEAM-SAL-03', 'name': 'Key Accounts Team', 'department_id': None, 'team_type': 'Sales',
             'description': 'Strategic accounts, contract negotiations'},
            {'code': 'TEAM-SAL-04', 'name': 'Pre-Sales Engineering', 'department_id': None, 'team_type': 'Technical',
             'description': 'Technical support for complex quotations'},

            {'code': 'TEAM-FIN-01', 'name': 'Accounts Payable Team', 'department_id': None, 'team_type': 'Finance',
             'description': 'Supplier invoices, payment processing'},
            {'code': 'TEAM-FIN-02', 'name': 'Accounts Receivable Team', 'department_id': None, 'team_type': 'Finance',
             'description': 'Customer invoicing, collections, credit control'},
            {'code': 'TEAM-FIN-03', 'name': 'Financial Reporting Team', 'department_id': None, 'team_type': 'Finance',
             'description': 'Month-end close, management accounts, statutory reporting'},

            {'code': 'TEAM-IT-01', 'name': 'Help Desk Team', 'department_id': None, 'team_type': 'Support',
             'description': 'User support, incident management, ticket resolution'},
            {'code': 'TEAM-IT-02', 'name': 'Development Team', 'department_id': None, 'team_type': 'Technical',
             'description': 'Custom development, integrations, automation'},

            {'code': 'TEAM-QC-01', 'name': 'Inbound QC Team', 'department_id': None, 'team_type': 'Quality',
             'description': 'Supplier delivery inspection, compliance checks'},
            {'code': 'TEAM-QC-02', 'name': 'Outbound QC Team', 'department_id': None, 'team_type': 'Quality',
             'description': 'Picked order verification, packaging checks'},
        ]

        for team in team_data:
            try:
                db.execute("""
                    INSERT OR IGNORE INTO teams (code, name, company_id, department_id, team_type, description, is_active, created_at)
                    VALUES (?, ?, NULL, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                """, (team['code'], team['name'], team['department_id'], team['team_type'], team['description']))
            except Exception as e:
                print(f"Team {team['code']} error: {e}")

        print(f"Seeded {len(team_data)} teams.")

        db.commit()
        print("\n=== Organization data seeding complete ===")

def enhance_companies():
    """Add extra fields to companies if missing."""
    with get_db_context() as db:
        # Check and add missing columns to companies
        existing_cols = [c[1] for c in db.execute("PRAGMA table_info(companies)").fetchall()]
        new_cols = {
            'code': 'TEXT',
            'registration_number': 'TEXT',
            'tax_number': 'TEXT',
            'website': 'TEXT',
            'founded_year': 'INTEGER',
            'employee_count': 'INTEGER',
            'annual_revenue': 'REAL',
            'description': 'TEXT',
            'address': 'TEXT',
            'city': 'TEXT',
            'country': 'TEXT',
            'phone': 'TEXT',
            'email': 'TEXT',
            'logo_url': 'TEXT',
            'industry': 'TEXT',
            'company_type': 'TEXT',
        }
        for col, col_type in new_cols.items():
            if col not in existing_cols:
                try:
                    db.execute(f"ALTER TABLE companies ADD COLUMN {col} {col_type}")
                    print(f"Added column: companies.{col}")
                except:
                    pass

        # Update existing companies with sample data
        companies = get_all("SELECT id, name FROM companies")
        for company in companies:
            try:
                db.execute("""
                    UPDATE companies SET
                        code = ?,
                        registration_number = ?,
                        tax_number = ?,
                        website = ?,
                        founded_year = ?,
                        employee_count = ?,
                        description = ?,
                        address = ?,
                        city = ?,
                        country = 'UAE',
                        phone = ?,
                        email = ?
                    WHERE id = ?
                """, (
                    f"CO-{company['id']:04d}",
                    f"CR-{company['id'] * 12345}",
                    f"TAX-{company['id'] * 11111}",
                    f"https://www.{company['name'].lower().replace(' ', '')}.ae",
                    2010 + company['id'],
                    50 + company['id'] * 20,
                    f"{company['name']} - Trading & Distribution Company",
                    f"Plot {company['id'] * 10}, Industrial Area",
                    'Dubai',
                    f"+971-4-{company['id']*111:04d}",
                    f"info@{company['name'].lower().replace(' ', '')}.ae",
                    company['id']
                ))
            except Exception as e:
                pass  # May fail for duplicate key or other

        db.commit()
        print("Companies enhanced with additional fields.")

def enhance_warehouses():
    """Add extra fields to warehouses if missing."""
    with get_db_context() as db:
        existing_cols = [c[1] for c in db.execute("PRAGMA table_info(warehouses)").fetchall()]
        new_cols = {
            'code': 'TEXT',
            'address': 'TEXT',
            'city': 'TEXT',
            'country': 'TEXT',
            'phone': 'TEXT',
            'email': 'TEXT',
            'manager_name': 'TEXT',
            'manager_contact': 'TEXT',
            'storage_type': 'TEXT',
            'temperature_control': 'INTEGER',
            'is_active': 'INTEGER',
        }
        for col, col_type in new_cols.items():
            if col not in existing_cols:
                try:
                    db.execute(f"ALTER TABLE warehouses ADD COLUMN {col} {col_type}")
                    print(f"Added column: warehouses.{col}")
                except:
                    pass

        # Update warehouses with sample data
        warehouses = get_all("SELECT id, company_id FROM warehouses")
        for wh in warehouses:
            try:
                db.execute("""
                    UPDATE warehouses SET
                        code = ?,
                        address = ?,
                        city = ?,
                        country = 'UAE',
                        phone = ?,
                        email = ?,
                        manager_name = ?,
                        storage_type = ?,
                        is_active = 1
                    WHERE id = ?
                """, (
                    f"WH-{wh['id']:03d}",
                    f"Warehouse {wh['id']}, JAFZA",
                    'Dubai',
                    f"+971-4-555-{wh['id']*11:04d}",
                    f"warehouse{wh['id']}@whdash.com",
                    'Warehouse Manager',
                    'Racked',
                    wh['id']
                ))
            except:
                pass

        db.commit()
        print("Warehouses enhanced with additional fields.")

# Run everything
create_org_tables()
seed_organization_data()
enhance_companies()
enhance_warehouses()

print("\n=== All done! ===")