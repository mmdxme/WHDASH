"""
Expense / Travel Management Module - Data Models
================================================
Comprehensive database models covering:
- Expense Claims (multi-line, multi-currency)
- Travel Requests (authorization workflow)
- Cash Advances (request, issuance, settlement)
- Receipts & Attachments (upload, linking, audit)
- Travel Itineraries (segments, accommodations, transport)
- Expense/Travel Policies (rules, thresholds, violations)
- Reimbursements (payment queue, settlement)
- Per Diem / Allowance Rules
- Finance Integration (cost centers, journal preview)
- HR Integration (employee, manager hierarchy)

Author: Expense/Travel Module Implementation
"""

from database import get_db_context, get_one, get_all, row_to_dict, rows_to_list, table_exists, log_audit

# ============================================================================
# EXPENSE / TRAVEL MODULE INITIALIZATION
# ============================================================================

def initialize_expense_travel_schema():
    """Initialize all expense/travel module tables."""
    _create_expense_categories()
    _create_expense_policies()
    _create_expense_policy_rules()
    _create_expense_claims()
    _create_expense_claim_lines()
    _create_expense_receipts()
    _create_travel_requests()
    _create_travel_itineraries()
    _create_travel_segments()
    _create_cash_advances()
    _create_advance_settlements()
    _create_reimbursements()
    _create_per_diem_rules()
    _create_expense_violations()
    _create_expense_approvals()
    _create_expense_delegations()
    _create_expense_settings()
    _create_expense_audit_log()


# ============================================================================
# EXPENSE CATEGORIES
# ============================================================================

def _create_expense_categories():
    """Create expense categories table."""
    if not table_exists('expense_categories'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE expense_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    name_ar TEXT,
                    name_fa TEXT,
                    name_ru TEXT,
                    name_hi TEXT,
                    name_es TEXT,
                    name_zh TEXT,
                    name_de TEXT,
                    category_type TEXT DEFAULT 'expense',
                    parent_id INTEGER,
                    is_active INTEGER DEFAULT 1,
                    requires_receipt INTEGER DEFAULT 1,
                    max_amount REAL,
                    max_amount_currency TEXT DEFAULT 'AED',
                    is_per_diem_eligible INTEGER DEFAULT 0,
                    is_mileage_eligible INTEGER DEFAULT 0,
                    is_travel_eligible INTEGER DEFAULT 0,
                    account_code TEXT,
                    vat_rate REAL DEFAULT 0,
                    display_order INTEGER DEFAULT 0,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_id) REFERENCES expense_categories(id)
                )
            """)
            db.execute("CREATE INDEX idx_exp_cat_code ON expense_categories(code)")
            db.execute("CREATE INDEX idx_exp_cat_type ON expense_categories(category_type)")
            db.execute("CREATE INDEX idx_exp_cat_parent ON expense_categories(parent_id)")
            db.commit()

            # Seed default expense categories
            default_categories = [
                # Travel Expenses
                ('TRAVEL', 'Travel', 'السفر', 'سفر', 'Путешествие', 'यात्रा', 'Viaje', '出差', 'Reise', 'travel', None, 1, 0, 0, 1, '6101', 0, 1),
                ('AIRFARE', 'Airfare', 'تذكرة الطيران', 'بلیط هواپیما', 'Авиабилет', 'हवाई जहाज', 'Billete de avión', '机票', 'Flugticket', 'travel', None, 1, 0, 0, 1, '6101-001', 0, 2),
                ('HOTEL', 'Hotel / Accommodation', 'الفندق / الإقامة', 'هتل / اقامت', 'Гостиница', 'होटल', 'Hotel', '酒店', 'Hotel', 'travel', None, 1, 500, 0, 0, 1, '6101-002', 0, 3),
                ('MEALS_TRAVEL', 'Meals - Travel', 'وجبات - السفر', 'غذا - سفر', 'Питание', 'भोजन', 'Comidas', '餐饮', 'Mahlzeiten', 'travel', None, 1, 100, 0, 0, 1, '6101-003', 0, 4),
                ('TRANSPORT_LOCAL', 'Local Transport', 'النقل المحلي', 'حمل و نقل محلی', 'Местный транспорт', 'स्थानीय परिवहन', 'Transporte local', '本地交通', 'Lokaler Transport', 'travel', None, 1, 100, 0, 0, 1, '6101-004', 0, 5),
                ('CAR_RENTAL', 'Car Rental', 'تأجير السيارات', 'اجاره خودرو', 'Аренда автомобиля', 'कार किराया', 'Alquiler de coche', '租车', 'Autovermietung', 'travel', None, 1, 0, 0, 0, 1, '6101-005', 0, 6),
                ('FUEL', 'Fuel / Gasoline', 'الوقود', 'سوخت', 'Топливо', 'ईंधन', 'Combustible', '燃料', 'Benzin', 'travel', None, 1, 200, 0, 0, 1, '6101-006', 0, 7),
                ('TRAIN', 'Train / Rail', 'القطار', 'قطار', 'Поезд', 'ट्रेन', 'Tren', '火车', 'Zug', 'travel', None, 1, 0, 0, 0, 1, '6101-007', 0, 8),
                ('TAXI', 'Taxi / Ride Share', 'التاكسي', 'تاکسی', 'Такси', 'टैक्सी', 'Taxi', '出租车', 'Taxi', 'travel', None, 1, 100, 0, 0, 1, '6101-008', 0, 9),
                ('PARKING', 'Parking / Tolls', 'مواقف / رسوم الطرق', 'پارکینگ / عوارض', 'Парковка', 'पार्किंग', 'Aparcamiento', '停车', 'Parken', 'travel', None, 1, 50, 0, 0, 1, '6101-009', 0, 10),
                
                # Office Expenses
                ('OFFICE', 'Office Supplies', 'اللوازم المكتبية', 'لوازم اداری', 'Канцтовары', 'कार्यालय आपूर्ति', 'Suministros de oficina', '办公用品', 'Bürobedarf', 'expense', None, 1, 0, 0, 0, 1, '6201', 0, 20),
                ('STATIONERY', 'Stationery', 'قرطاسية', 'نوشت‌افزار', 'Канцелярия', 'लेखन सामग्री', 'Papelería', '文具', 'Schreibwaren', 'expense', None, 1, 0, 0, 0, 1, '6201-001', 0, 21),
                ('PRINTING', 'Printing / Copying', 'طباعة / نسخ', 'چاپ / کپی', 'Печать', 'प्रिंटिंग', 'Impresión', '打印', 'Drucken', 'expense', None, 1, 0, 0, 0, 1, '6201-002', 0, 22),
                ('POSTAGE', 'Postage / Courier', 'بريد / شحن', 'پست / پیک', 'Почта', 'डाक', 'Correo', '邮费', 'Post', 'expense', None, 1, 0, 0, 0, 1, '6201-003', 0, 23),
                
                # Communication
                ('COMM', 'Communication', 'الاتصالات', 'ارتباطات', 'Связь', 'संचार', 'Comunicación', '通讯', 'Kommunikation', 'expense', None, 1, 0, 0, 0, 1, '6301', 0, 30),
                ('PHONE', 'Phone / Mobile', 'الهاتف / الجوال', 'تلفن / موبایل', 'Телефон', 'फोन', 'Teléfono', '电话', 'Telefon', 'expense', None, 1, 0, 0, 0, 1, '6301-001', 0, 31),
                ('INTERNET', 'Internet / Data', 'الإنترنت / البيانات', 'اینترنت / داده', 'Интернет', 'इंटरनेट', 'Internet', '互联网', 'Internet', 'expense', None, 1, 0, 0, 0, 1, '6301-002', 0, 32),
                
                # Professional Services
                ('PROF', 'Professional Services', 'الخدمات المهنية', 'خدمات حرفه‌ای', 'Профессиональные услуги', 'पेशेवर सेवाएं', 'Servicios profesionales', '专业服务', 'Professionelle Dienste', 'expense', None, 1, 0, 0, 0, 1, '6401', 0, 40),
                ('CONSULTING', 'Consulting Fees', 'رسوم الاستشارات', 'هزینه مشاوره', 'Консалтинг', 'परामर्श शुल्क', 'Honorarios de consultoría', '咨询费', 'Beratungsgebühren', 'expense', None, 1, 0, 0, 0, 1, '6401-001', 0, 41),
                ('LEGAL', 'Legal Fees', 'الرسوم القانونية', 'هزینه‌های حقوقی', 'Юридические расходы', 'वैधानिक शुल्क', 'Gastos legales', '法律费用', 'Anwaltskosten', 'expense', None, 1, 0, 0, 0, 1, '6401-002', 0, 42),
                
                # Entertainment
                ('ENTERTAIN', 'Entertainment', 'الترفيه', 'سرگرمی', 'Развлечения', 'मनोरंजन', 'Entretenimiento', '娱乐', 'Unterhaltung', 'expense', None, 1, 0, 0, 0, 1, '6501', 0, 50),
                ('CLIENT_MEALS', 'Client Meals', 'وجبات العملاء', 'غذای مشتری', 'Питание клиентов', 'ग्राहक भोजन', 'Comidas de clientes', '客户餐饮', 'Kundenbewirtung', 'expense', None, 1, 200, 0, 0, 1, '6501-001', 0, 51),
                ('CLIENT_GIFTS', 'Client Gifts', 'هدايا العملاء', 'هدایای مشتری', 'Подарки клиентам', 'ग्राहक उपहार', 'Regalos a clientes', '客户礼品', 'Kundengeschenke', 'expense', None, 1, 100, 0, 0, 1, '6501-002', 0, 52),
                
                # Other Expenses
                ('OTHER', 'Other Expenses', 'مصروفات أخرى', 'سایر هزینه‌ها', 'Прочие расходы', 'अन्य खर्च', 'Otros gastos', '其他费用', 'Sonstige Ausgaben', 'expense', None, 1, 0, 0, 0, 1, '6601', 0, 90),
                ('MISC', 'Miscellaneous', 'متفرقات', 'متفرقه', 'Разное', 'विविध', 'Varios', '杂项', 'Verschiedenes', 'expense', None, 1, 0, 0, 0, 1, '6601-001', 0, 91),
            ]
            
            for cat in default_categories:
                db.execute("""
                    INSERT OR IGNORE INTO expense_categories 
                    (code, name, name_ar, name_fa, name_ru, name_hi, name_es, name_zh, name_de, 
                     category_type, parent_id, is_active, max_amount, is_per_diem_eligible,
                     is_mileage_eligible, is_travel_eligible, account_code, vat_rate, display_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?)
                """, cat)
            db.commit()


def get_expense_categories(category_type=None, active_only=True):
    """Get all expense categories."""
    sql = "SELECT * FROM expense_categories WHERE 1=1"
    params = []
    
    if category_type:
        sql += " AND category_type = ?"
        params.append(category_type)
    
    if active_only:
        sql += " AND is_active = 1"
    
    sql += " ORDER BY display_order, code"
    return get_all(sql, params if params else None)


def get_expense_category_by_id(category_id):
    """Get expense category by ID."""
    return get_one("SELECT * FROM expense_categories WHERE id = ?", (category_id,))


# ============================================================================
# EXPENSE POLICIES
# ============================================================================

def _create_expense_policies():
    """Create expense policies table."""
    if not table_exists('expense_policies'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE expense_policies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    policy_code TEXT UNIQUE NOT NULL,
                    policy_name TEXT NOT NULL,
                    policy_name_ar TEXT,
                    policy_name_fa TEXT,
                    policy_type TEXT NOT NULL,
                    description TEXT,
                    applies_to_all INTEGER DEFAULT 1,
                    is_active INTEGER DEFAULT 1,
                    requires_pre_approval INTEGER DEFAULT 0,
                    requires_receipt INTEGER DEFAULT 1,
                    max_per_transaction REAL,
                    max_per_day REAL,
                    max_per_month REAL,
                    currency TEXT DEFAULT 'AED',
                    approval_required_above REAL,
                    approval_required_above_currency TEXT DEFAULT 'AED',
                    receipt_threshold REAL DEFAULT 0,
                    receipt_threshold_currency TEXT DEFAULT 'AED',
                    per_diem_enabled INTEGER DEFAULT 0,
                    per_diem_rate REAL,
                    per_diem_currency TEXT DEFAULT 'AED',
                    grace_period_hours INTEGER DEFAULT 0,
                    company_id INTEGER,
                    branch_id INTEGER,
                    department_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_pol_code ON expense_policies(policy_code)")
            db.execute("CREATE INDEX idx_pol_type ON expense_policies(policy_type)")
            db.commit()


def _create_expense_policy_rules():
    """Create expense policy rules table."""
    if not table_exists('expense_policy_rules'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE expense_policy_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    policy_id INTEGER NOT NULL,
                    rule_type TEXT NOT NULL,
                    category_id INTEGER,
                    condition_operator TEXT,
                    condition_value REAL,
                    condition_value_text TEXT,
                    max_amount REAL,
                    max_amount_currency TEXT DEFAULT 'AED',
                    allowed INTEGER DEFAULT 1,
                    exception_reason TEXT,
                    requires_approval INTEGER DEFAULT 0,
                    approver_role TEXT,
                    display_order INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (policy_id) REFERENCES expense_policies(id),
                    FOREIGN KEY (category_id) REFERENCES expense_categories(id)
                )
            """)
            db.execute("CREATE INDEX idx_rule_policy ON expense_policy_rules(policy_id)")
            db.commit()


def get_expense_policies(policy_type=None, active_only=True):
    """Get all expense policies."""
    sql = "SELECT * FROM expense_policies WHERE 1=1"
    params = []
    
    if policy_type:
        sql += " AND policy_type = ?"
        params.append(policy_type)
    
    if active_only:
        sql += " AND is_active = 1"
    
    return get_all(sql, params if params else None)


def get_policy_rules(policy_id):
    """Get rules for a specific policy."""
    return get_all("""
        SELECT r.*, c.name as category_name, c.code as category_code
        FROM expense_policy_rules r
        LEFT JOIN expense_categories c ON r.category_id = c.id
        WHERE r.policy_id = ? AND r.is_active = 1
        ORDER BY r.display_order
    """, (policy_id,))


# ============================================================================
# EXPENSE CLAIMS
# ============================================================================

def _create_expense_claims():
    """Create expense claims table."""
    if not table_exists('expense_claims'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE expense_claims (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    claim_number TEXT UNIQUE NOT NULL,
                    claim_type TEXT DEFAULT 'expense',
                    status TEXT DEFAULT 'draft',
                    
                    -- Employee Info (from HR)
                    employee_id INTEGER,
                    employee_code TEXT,
                    employee_name TEXT,
                    department_id INTEGER,
                    department_name TEXT,
                    branch_id INTEGER,
                    branch_name TEXT,
                    company_id INTEGER,
                    
                    -- Claim Details
                    claim_date TEXT,
                    submission_date TEXT,
                    fiscal_period_id INTEGER,
                    currency TEXT DEFAULT 'AED',
                    total_amount REAL DEFAULT 0,
                    total_amount_base REAL DEFAULT 0,
                    exchange_rate REAL DEFAULT 1,
                    base_currency TEXT DEFAULT 'AED',
                    
                    -- Purpose & Description
                    business_purpose TEXT,
                    project_code TEXT,
                    project_name TEXT,
                    
                    -- Cost Center Allocation
                    cost_center_id INTEGER,
                    cost_center_name TEXT,
                    cost_center_code TEXT,
                    
                    -- Travel Linkage
                    travel_request_id INTEGER,
                    trip_purpose TEXT,
                    
                    -- Policy & Approval
                    policy_id INTEGER,
                    policy_name TEXT,
                    is_policy_compliant INTEGER DEFAULT 1,
                    has_exceptions INTEGER DEFAULT 0,
                    
                    -- Approval Workflow
                    current_approver_id INTEGER,
                    current_approver_name TEXT,
                    approval_level INTEGER DEFAULT 0,
                    approval_deadline TEXT,
                    
                    -- Finance Integration
                    reimbursement_id INTEGER,
                    reimbursement_status TEXT,
                    payment_date TEXT,
                    payment_reference TEXT,
                    journal_entry_id INTEGER,
                    
                    -- Additional Info
                    notes TEXT,
                    internal_notes TEXT,
                    attachment_count INTEGER DEFAULT 0,
                    
                    -- Audit
                    submitted_by INTEGER,
                    submitted_by_name TEXT,
                    approved_by INTEGER,
                    approved_by_name TEXT,
                    rejected_by INTEGER,
                    rejected_by_name TEXT,
                    rejection_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_claim_number ON expense_claims(claim_number)")
            db.execute("CREATE INDEX idx_claim_status ON expense_claims(status)")
            db.execute("CREATE INDEX idx_claim_employee ON expense_claims(employee_id)")
            db.execute("CREATE INDEX idx_claim_dept ON expense_claims(department_id)")
            db.execute("CREATE INDEX idx_claim_branch ON expense_claims(branch_id)")
            db.execute("CREATE INDEX idx_claim_company ON expense_claims(company_id)")
            db.execute("CREATE INDEX idx_claim_date ON expense_claims(claim_date)")
            db.execute("CREATE INDEX idx_claim_travel ON expense_claims(travel_request_id)")
            db.commit()


def _create_expense_claim_lines():
    """Create expense claim lines table."""
    if not table_exists('expense_claim_lines'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE expense_claim_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    claim_id INTEGER NOT NULL,
                    line_number INTEGER NOT NULL,
                    
                    -- Expense Details
                    category_id INTEGER,
                    category_code TEXT,
                    category_name TEXT,
                    expense_date TEXT,
                    expense_description TEXT,
                    
                    -- Amount
                    amount REAL NOT NULL,
                    amount_currency TEXT DEFAULT 'AED',
                    amount_base REAL,
                    exchange_rate REAL DEFAULT 1,
                    base_currency TEXT DEFAULT 'AED',
                    vat_amount REAL DEFAULT 0,
                    vat_rate REAL DEFAULT 0,
                    total_with_vat REAL,
                    
                    -- Vendor/Supplier
                    vendor_name TEXT,
                    vendor_id INTEGER,
                    invoice_number TEXT,
                    invoice_date TEXT,
                    
                    -- Receipt
                    receipt_id INTEGER,
                    has_receipt INTEGER DEFAULT 0,
                    receipt_status TEXT,
                    
                    -- Cost Allocation
                    cost_center_id INTEGER,
                    cost_center_name TEXT,
                    cost_center_code TEXT,
                    department_id INTEGER,
                    department_name TEXT,
                    project_code TEXT,
                    project_name TEXT,
                    
                    -- Policy Compliance
                    is_compliant INTEGER DEFAULT 1,
                    policy_violation_id INTEGER,
                    exception_reason TEXT,
                    override_approved_by INTEGER,
                    override_approved_by_name TEXT,
                    
                    -- Mileage (if applicable)
                    is_mileage INTEGER DEFAULT 0,
                    mileage_km REAL,
                    mileage_rate REAL,
                    mileage_total REAL,
                    
                    -- Per Diem (if applicable)
                    is_per_diem INTEGER DEFAULT 0,
                    per_diem_days REAL,
                    per_diem_rate REAL,
                    per_diem_total REAL,
                    
                    -- Linked Travel
                    travel_segment_id INTEGER,
                    itinerary_day INTEGER,
                    
                    -- Notes
                    line_notes TEXT,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (claim_id) REFERENCES expense_claims(id)
                )
            """)
            db.execute("CREATE INDEX idx_line_claim ON expense_claim_lines(claim_id)")
            db.execute("CREATE INDEX idx_line_category ON expense_claim_lines(category_id)")
            db.execute("CREATE INDEX idx_line_date ON expense_claim_lines(expense_date)")
            db.commit()


# ============================================================================
# EXPENSE RECEIPTS
# ============================================================================

def _create_expense_receipts():
    """Create expense receipts table."""
    if not table_exists('expense_receipts'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE expense_receipts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_number TEXT UNIQUE NOT NULL,
                    claim_line_id INTEGER,
                    claim_id INTEGER,
                    
                    -- File Info
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    mime_type TEXT,
                    original_file_name TEXT,
                    
                    -- Receipt Details
                    receipt_date TEXT,
                    merchant_name TEXT,
                    merchant_category TEXT,
                    total_amount REAL,
                    currency TEXT DEFAULT 'AED',
                    exchange_rate REAL DEFAULT 1,
                    base_amount REAL,
                    base_currency TEXT DEFAULT 'AED',
                    
                    -- OCR Data (future-ready)
                    ocr_processed INTEGER DEFAULT 0,
                    ocr_data TEXT,
                    ocr_confidence REAL,
                    
                    -- Validation
                    is_valid INTEGER DEFAULT 1,
                    validation_status TEXT,
                    validation_notes TEXT,
                    is_matching INTEGER DEFAULT 0,
                    match_confidence REAL,
                    
                    -- Link Status
                    is_linked INTEGER DEFAULT 0,
                    linked_by INTEGER,
                    linked_at TEXT,
                    
                    -- Status
                    status TEXT DEFAULT 'pending',
                    
                    -- Audit
                    uploaded_by INTEGER,
                    uploaded_by_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_receipt_number ON expense_receipts(receipt_number)")
            db.execute("CREATE INDEX idx_receipt_claim ON expense_receipts(claim_id)")
            db.execute("CREATE INDEX idx_receipt_line ON expense_receipts(claim_line_id)")
            db.execute("CREATE INDEX idx_receipt_status ON expense_receipts(status)")
            db.execute("CREATE INDEX idx_receipt_uploaded ON expense_receipts(uploaded_by)")
            db.commit()


# ============================================================================
# TRAVEL REQUESTS
# ============================================================================

def _create_travel_requests():
    """Create travel requests table."""
    if not table_exists('travel_requests'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE travel_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    travel_number TEXT UNIQUE NOT NULL,
                    status TEXT DEFAULT 'draft',
                    
                    -- Employee Info
                    employee_id INTEGER,
                    employee_code TEXT,
                    employee_name TEXT,
                    department_id INTEGER,
                    department_name TEXT,
                    branch_id INTEGER,
                    branch_name TEXT,
                    company_id INTEGER,
                    
                    -- Trip Details
                    trip_purpose TEXT NOT NULL,
                    trip_type TEXT,
                    destination_country TEXT,
                    destination_city TEXT,
                    travel_start_date TEXT,
                    travel_end_date TEXT,
                    total_trip_days INTEGER,
                    
                    -- Dates
                    request_date TEXT,
                    submission_date TEXT,
                    approval_date TEXT,
                    
                    -- Financial
                    estimated_total_cost REAL DEFAULT 0,
                    estimated_total_cost_currency TEXT DEFAULT 'AED',
                    pre_approved_budget REAL,
                    pre_approved_budget_currency TEXT DEFAULT 'AED',
                    
                    -- Cash Advance
                    advance_requested REAL DEFAULT 0,
                    advance_requested_currency TEXT DEFAULT 'AED',
                    advance_id INTEGER,
                    advance_status TEXT,
                    
                    -- Policy
                    policy_id INTEGER,
                    policy_name TEXT,
                    is_policy_compliant INTEGER DEFAULT 1,
                    
                    -- Approval
                    current_approver_id INTEGER,
                    current_approver_name TEXT,
                    approval_level INTEGER DEFAULT 0,
                    approval_deadline TEXT,
                    
                    -- Travel Status
                    is_booked INTEGER DEFAULT 0,
                    booking_reference TEXT,
                    booking_notes TEXT,
                    
                    -- Expense Linkage
                    has_expense_claim INTEGER DEFAULT 0,
                    expense_claim_id INTEGER,
                    post_trip_submitted INTEGER DEFAULT 0,
                    
                    -- Additional
                    justification TEXT,
                    notes TEXT,
                    attachment_count INTEGER DEFAULT 0,
                    
                    -- Audit
                    submitted_by INTEGER,
                    submitted_by_name TEXT,
                    approved_by INTEGER,
                    approved_by_name TEXT,
                    rejected_by INTEGER,
                    rejected_by_name TEXT,
                    rejection_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_travel_number ON travel_requests(travel_number)")
            db.execute("CREATE INDEX idx_travel_status ON travel_requests(status)")
            db.execute("CREATE INDEX idx_travel_employee ON travel_requests(employee_id)")
            db.execute("CREATE INDEX idx_travel_dates ON travel_requests(travel_start_date, travel_end_date)")
            db.execute("CREATE INDEX idx_travel_approval ON travel_requests(current_approver_id)")
            db.commit()


def _create_travel_itineraries():
    """Create travel itineraries table."""
    if not table_exists('travel_itineraries'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE travel_itineraries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    travel_request_id INTEGER NOT NULL,
                    itinerary_type TEXT NOT NULL,
                    sequence_order INTEGER DEFAULT 1,
                    
                    -- Segment Details
                    segment_name TEXT,
                    segment_date TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    
                    -- Location
                    origin_country TEXT,
                    origin_city TEXT,
                    origin_location TEXT,
                    destination_country TEXT,
                    destination_city TEXT,
                    destination_location TEXT,
                    
                    -- Booking Info
                    booking_reference TEXT,
                    booking_provider TEXT,
                    ticket_number TEXT,
                    confirmation_number TEXT,
                    
                    -- Vendor
                    vendor_name TEXT,
                    vendor_id INTEGER,
                    
                    -- Cost
                    estimated_cost REAL,
                    estimated_cost_currency TEXT DEFAULT 'AED',
                    actual_cost REAL,
                    actual_cost_currency TEXT DEFAULT 'AED',
                    
                    -- Status
                    is_confirmed INTEGER DEFAULT 0,
                    is_cancelled INTEGER DEFAULT 0,
                    cancellation_reason TEXT,
                    
                    -- Notes
                    notes TEXT,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (travel_request_id) REFERENCES travel_requests(id)
                )
            """)
            db.execute("CREATE INDEX idx_itin_travel ON travel_itineraries(travel_request_id)")
            db.commit()


def _create_travel_segments():
    """Create travel segments table (detailed breakdown)."""
    if not table_exists('travel_segments'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE travel_segments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    itinerary_id INTEGER NOT NULL,
                    segment_type TEXT NOT NULL,
                    sequence_order INTEGER DEFAULT 1,
                    
                    -- Timing
                    departure_date TEXT,
                    departure_time TEXT,
                    arrival_date TEXT,
                    arrival_time TEXT,
                    
                    -- Location
                    departure_city TEXT,
                    departure_location TEXT,
                    arrival_city TEXT,
                    arrival_location TEXT,
                    
                    -- Transport Details
                    carrier_code TEXT,
                    carrier_name TEXT,
                    flight_number TEXT,
                    train_number TEXT,
                    bus_number TEXT,
                    vehicle_rental_company TEXT,
                    vehicle_type TEXT,
                    
                    -- Booking
                    booking_reference TEXT,
                    ticket_class TEXT,
                    seat_number TEXT,
                    confirmation_number TEXT,
                    
                    -- Cost
                    base_fare REAL,
                    taxes REAL,
                    fees REAL,
                    total_cost REAL,
                    currency TEXT DEFAULT 'AED',
                    
                    -- Accommodation
                    hotel_name TEXT,
                    hotel_address TEXT,
                    check_in_date TEXT,
                    check_in_time TEXT,
                    check_out_date TEXT,
                    check_out_time TEXT,
                    room_type TEXT,
                    hotel_confirmation_number TEXT,

                    -- Status
                    status TEXT DEFAULT 'planned',
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (itinerary_id) REFERENCES travel_itineraries(id)
                )
            """)
            db.execute("CREATE INDEX idx_segment_itin ON travel_segments(itinerary_id)")
            db.commit()


# ============================================================================
# CASH ADVANCES
# ============================================================================

def _create_cash_advances():
    """Create cash advances table."""
    if not table_exists('cash_advances'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE cash_advances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    advance_number TEXT UNIQUE NOT NULL,
                    status TEXT DEFAULT 'draft',
                    
                    -- Employee Info
                    employee_id INTEGER,
                    employee_code TEXT,
                    employee_name TEXT,
                    department_id INTEGER,
                    department_name TEXT,
                    branch_id INTEGER,
                    branch_name TEXT,
                    company_id INTEGER,
                    
                    -- Request Details
                    request_date TEXT,
                    submission_date TEXT,
                    requested_amount REAL NOT NULL,
                    requested_currency TEXT DEFAULT 'AED',
                    requested_amount_base REAL,
                    base_currency TEXT DEFAULT 'AED',
                    exchange_rate REAL DEFAULT 1,
                    
                    -- Purpose
                    purpose TEXT,
                    travel_request_id INTEGER,
                    trip_purpose TEXT,
                    expected_expense_type TEXT,
                    expected_destination TEXT,
                    
                    -- Approval
                    current_approver_id INTEGER,
                    current_approver_name TEXT,
                    approval_date TEXT,
                    approved_amount REAL,
                    approved_amount_currency TEXT DEFAULT 'AED',
                    
                    -- Issuance
                    issuance_date TEXT,
                    payment_method TEXT,
                    payment_reference TEXT,
                    bank_account TEXT,
                    is_issued INTEGER DEFAULT 0,
                    issued_by INTEGER,
                    issued_by_name TEXT,
                    
                    -- Settlement
                    settlement_claim_id INTEGER,
                    settlement_date TEXT,
                    settlement_amount REAL,
                    settlement_amount_currency TEXT DEFAULT 'AED',
                    unused_amount REAL,
                    unused_amount_currency TEXT DEFAULT 'AED',
                    recovery_required INTEGER DEFAULT 0,
                    recovery_status TEXT,
                    recovery_date TEXT,
                    
                    -- Outstanding
                    outstanding_balance REAL,
                    outstanding_balance_currency TEXT DEFAULT 'AED',
                    overdue_days INTEGER DEFAULT 0,
                    
                    -- Policy
                    policy_id INTEGER,
                    policy_name TEXT,
                    
                    -- Additional
                    notes TEXT,
                    rejection_reason TEXT,
                    rejection_by INTEGER,
                    rejection_by_name TEXT,
                    
                    -- Audit
                    submitted_by INTEGER,
                    submitted_by_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_adv_number ON cash_advances(advance_number)")
            db.execute("CREATE INDEX idx_adv_status ON cash_advances(status)")
            db.execute("CREATE INDEX idx_adv_employee ON cash_advances(employee_id)")
            db.execute("CREATE INDEX idx_adv_travel ON cash_advances(travel_request_id)")
            db.commit()


def _create_advance_settlements():
    """Create advance settlement records table."""
    if not table_exists('advance_settlements'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE advance_settlements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    advance_id INTEGER NOT NULL,
                    claim_id INTEGER NOT NULL,
                    settlement_type TEXT DEFAULT 'full',
                    
                    -- Amounts
                    advance_amount REAL,
                    applied_amount REAL,
                    unused_amount REAL,
                    excess_amount REAL,
                    currency TEXT DEFAULT 'AED',
                    
                    -- Status
                    status TEXT DEFAULT 'pending',
                    processed_by INTEGER,
                    processed_by_name TEXT,
                    processed_date TEXT,
                    
                    -- Recovery
                    recovery_required INTEGER DEFAULT 0,
                    recovery_amount REAL,
                    recovery_date TEXT,
                    
                    -- Notes
                    notes TEXT,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (advance_id) REFERENCES cash_advances(id),
                    FOREIGN KEY (claim_id) REFERENCES expense_claims(id)
                )
            """)
            db.execute("CREATE INDEX idx_settle_advance ON advance_settlements(advance_id)")
            db.execute("CREATE INDEX idx_settle_claim ON advance_settlements(claim_id)")
            db.commit()


# ============================================================================
# REIMBURSEMENTS
# ============================================================================

def _create_reimbursements():
    """Create reimbursements table."""
    if not table_exists('expense_reimbursements'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE expense_reimbursements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reimbursement_number TEXT UNIQUE NOT NULL,
                    status TEXT DEFAULT 'pending',
                    
                    -- Link to Claim
                    claim_id INTEGER NOT NULL,
                    claim_number TEXT,
                    employee_id INTEGER,
                    employee_name TEXT,
                    department_name TEXT,
                    
                    -- Amount
                    reimbursement_amount REAL NOT NULL,
                    currency TEXT DEFAULT 'AED',
                    reimbursement_amount_base REAL,
                    base_currency TEXT DEFAULT 'AED',
                    exchange_rate REAL DEFAULT 1,
                    
                    -- Advance Deduction
                    advance_id INTEGER,
                    advance_number TEXT,
                    advance_deduction REAL DEFAULT 0,
                    net_reimbursement REAL,
                    
                    -- Payment
                    payment_date TEXT,
                    payment_method TEXT,
                    payment_reference TEXT,
                    bank_name TEXT,
                    bank_account TEXT,
                    is_paid INTEGER DEFAULT 0,
                    
                    -- Finance Integration
                    journal_entry_id INTEGER,
                    journal_number TEXT,
                    posting_date TEXT,
                    posted_by INTEGER,
                    
                    -- Batch
                    batch_id INTEGER,
                    batch_number TEXT,
                    batch_date TEXT,
                    
                    -- Additional
                    notes TEXT,
                    rejection_reason TEXT,
                    payment_proof TEXT,
                    
                    -- Audit
                    approved_by INTEGER,
                    approved_by_name TEXT,
                    approved_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_reim_number ON expense_reimbursements(reimbursement_number)")
            db.execute("CREATE INDEX idx_reim_status ON expense_reimbursements(status)")
            db.execute("CREATE INDEX idx_reim_claim ON expense_reimbursements(claim_id)")
            db.execute("CREATE INDEX idx_reim_employee ON expense_reimbursements(employee_id)")
            db.execute("CREATE INDEX idx_reim_batch ON expense_reimbursements(batch_id)")
            db.commit()


# ============================================================================
# PER DIEM RULES
# ============================================================================

def _create_per_diem_rules():
    """Create per diem rules table."""
    if not table_exists('per_diem_rules'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE per_diem_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_code TEXT UNIQUE NOT NULL,
                    rule_name TEXT NOT NULL,
                    rule_name_ar TEXT,
                    country_code TEXT,
                    country_name TEXT,
                    city TEXT,
                    zone TEXT,
                    
                    -- Rates
                    lodging_rate REAL,
                    lodging_rate_currency TEXT DEFAULT 'AED',
                    meals_rate REAL,
                    meals_rate_currency TEXT DEFAULT 'AED',
                    incidentals_rate REAL,
                    incidentals_rate_currency TEXT DEFAULT 'AED',
                    total_daily_rate REAL,
                    total_daily_rate_currency TEXT DEFAULT 'AED',
                    
                    -- Rules
                    max_lodging_days INTEGER DEFAULT 30,
                    max_meals_days INTEGER DEFAULT 30,
                    first_day_rule TEXT,
                    last_day_rule TEXT,
                    partial_day_rule TEXT,
                    
                    -- Applicability
                    applies_to_all INTEGER DEFAULT 1,
                    employee_grade TEXT,
                    travel_type TEXT,
                    
                    -- Status
                    is_active INTEGER DEFAULT 1,
                    effective_from TEXT,
                    effective_to TEXT,
                    
                    -- Additional
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_perdiem_country ON per_diem_rules(country_code)")
            db.execute("CREATE INDEX idx_perdiem_city ON per_diem_rules(city)")
            db.commit()


# ============================================================================
# EXPENSE VIOLATIONS
# ============================================================================

def _create_expense_violations():
    """Create expense policy violations table."""
    if not table_exists('expense_violations'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE expense_violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    violation_code TEXT UNIQUE NOT NULL,
                    claim_id INTEGER,
                    claim_line_id INTEGER,
                    
                    -- Type
                    violation_type TEXT,
                    severity TEXT DEFAULT 'medium',
                    
                    -- Rule Details
                    policy_id INTEGER,
                    policy_rule_id INTEGER,
                    rule_description TEXT,
                    
                    -- What was violated
                    category_id INTEGER,
                    category_name TEXT,
                    amount REAL,
                    amount_currency TEXT DEFAULT 'AED',
                    threshold_amount REAL,
                    threshold_amount_currency TEXT DEFAULT 'AED',
                    
                    -- Exception
                    exception_requested INTEGER DEFAULT 0,
                    exception_reason TEXT,
                    exception_status TEXT,
                    exception_approved_by INTEGER,
                    exception_approved_by_name TEXT,
                    exception_approval_date TEXT,
                    
                    -- Resolution
                    resolution TEXT,
                    resolved_by INTEGER,
                    resolved_by_name TEXT,
                    resolved_at TEXT,
                    
                    -- Status
                    status TEXT DEFAULT 'open',
                    is_overridden INTEGER DEFAULT 0,
                    
                    -- Audit
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (claim_id) REFERENCES expense_claims(id),
                    FOREIGN KEY (claim_line_id) REFERENCES expense_claim_lines(id)
                )
            """)
            db.execute("CREATE INDEX idx_viol_claim ON expense_violations(claim_id)")
            db.execute("CREATE INDEX idx_viol_status ON expense_violations(status)")
            db.commit()


# ============================================================================
# EXPENSE APPROVALS
# ============================================================================

def _create_expense_approvals():
    """Create expense approval workflow table."""
    if not table_exists('expense_approvals'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE expense_approvals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    approval_type TEXT NOT NULL,
                    reference_id INTEGER NOT NULL,
                    reference_type TEXT NOT NULL,
                    
                    -- Level
                    approval_level INTEGER DEFAULT 1,
                    is_final_approval INTEGER DEFAULT 0,
                    
                    -- Approver
                    approver_id INTEGER,
                    approver_name TEXT,
                    approver_role TEXT,
                    delegated_from_id INTEGER,
                    delegated_from_name TEXT,
                    
                    -- Status
                    status TEXT DEFAULT 'pending',
                    decision_date TEXT,
                    decision_notes TEXT,
                    
                    -- SLA
                    sla_deadline TEXT,
                    sla_breached INTEGER DEFAULT 0,
                    escalation_triggered INTEGER DEFAULT 0,
                    
                    -- Delegation
                    is_delegated INTEGER DEFAULT 0,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_appr_type ON expense_approvals(reference_type)")
            db.execute("CREATE INDEX idx_appr_approver ON expense_approvals(approver_id)")
            db.execute("CREATE INDEX idx_appr_status ON expense_approvals(status)")
            db.commit()


# ============================================================================
# EXPENSE DELEGATIONS
# ============================================================================

def _create_expense_delegations():
    """Create expense delegation rules table."""
    if not table_exists('expense_delegations'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE expense_delegations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    delegator_id INTEGER NOT NULL,
                    delegator_name TEXT,
                    delegate_id INTEGER NOT NULL,
                    delegate_name TEXT,
                    
                    -- Scope
                    delegation_type TEXT DEFAULT 'expense',
                    applies_to_claims INTEGER DEFAULT 1,
                    applies_to_travel INTEGER DEFAULT 1,
                    applies_to_advances INTEGER DEFAULT 1,
                    applies_to_approvals INTEGER DEFAULT 1,
                    
                    -- Validity
                    start_date TEXT,
                    end_date TEXT,
                    is_active INTEGER DEFAULT 1,
                    
                    -- Limits
                    max_amount REAL,
                    max_amount_currency TEXT DEFAULT 'AED',
                    max_approval_level INTEGER,
                    
                    -- Reason
                    reason TEXT,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_deleg_delegator ON expense_delegations(delegator_id)")
            db.execute("CREATE INDEX idx_deleg_delegate ON expense_delegations(delegate_id)")
            db.commit()


# ============================================================================
# EXPENSE SETTINGS
# ============================================================================

def _create_expense_settings():
    """Create expense/travel settings table."""
    if not table_exists('expense_settings'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE expense_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT,
                    setting_type TEXT DEFAULT 'string',
                    category TEXT DEFAULT 'general',
                    description TEXT,
                    is_active INTEGER DEFAULT 1,
                    company_id INTEGER,
                    branch_id INTEGER,
                    department_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.commit()
            
            # Seed default settings
            default_settings = [
                ('default_currency', 'AED', 'string', 'general', 'Default expense currency'),
                ('require_receipt_threshold', '25', 'number', 'policy', 'Minimum amount requiring receipt'),
                ('auto_approve_below', '50', 'number', 'policy', 'Auto-approve expenses below this amount'),
                ('reimbursement_cycle_days', '7', 'number', 'finance', 'Reimbursement payment cycle in days'),
                ('advance_recovery_threshold_days', '30', 'number', 'policy', 'Days before requiring advance settlement'),
                ('max_mileage_rate', '3', 'number', 'policy', 'Maximum mileage reimbursement rate per KM'),
                ('default_per_diem_enabled', '1', 'boolean', 'policy', 'Enable per diem by default'),
                ('receipt_upload_max_size', '10485760', 'number', 'general', 'Max receipt file size in bytes (10MB)'),
                ('allowed_receipt_types', '.jpg,.jpeg,.png,.pdf,.gif', 'string', 'general', 'Allowed receipt file types'),
                ('expense_claim_prefix', 'EXP', 'string', 'numbering', 'Expense claim number prefix'),
                ('expense_claim_next_number', '10001', 'number', 'numbering', 'Next expense claim number'),
                ('travel_request_prefix', 'TRV', 'string', 'numbering', 'Travel request number prefix'),
                ('travel_request_next_number', '10001', 'number', 'numbering', 'Next travel request number'),
                ('advance_prefix', 'ADV', 'string', 'numbering', 'Cash advance number prefix'),
                ('advance_next_number', '10001', 'number', 'numbering', 'Next cash advance number'),
                ('auto_post_journal', '0', 'boolean', 'finance', 'Auto-post reimbursement journals'),
                ('expense_journal_description', 'Expense Reimbursement', 'string', 'finance', 'Journal entry description'),
                ('require_project_code', '0', 'boolean', 'policy', 'Require project code on expenses'),
                ('require_cost_center', '1', 'boolean', 'policy', 'Require cost center on expenses'),
                ('default_approval_level', '1', 'number', 'workflow', 'Default approval level count'),
                ('escalation_hours', '24', 'number', 'workflow', 'Hours before escalation'),
                ('email_notifications_enabled', '1', 'boolean', 'notifications', 'Enable email notifications'),
                ('flow_notifications_enabled', '1', 'boolean', 'notifications', 'Enable Flow notifications'),
            ]
            
            for key, value, stype, cat, desc in default_settings:
                db.execute("""
                    INSERT OR IGNORE INTO expense_settings (setting_key, setting_value, setting_type, category, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (key, value, stype, cat, desc))
            db.commit()


# ============================================================================
# EXPENSE AUDIT LOG
# ============================================================================

def _create_expense_audit_log():
    """Create dedicated expense audit log table."""
    if not table_exists('expense_audit_log'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE expense_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,
                    entity_id INTEGER,
                    entity_number TEXT,
                    action TEXT NOT NULL,
                    
                    -- User
                    user_id INTEGER,
                    user_name TEXT,
                    user_role TEXT,
                    
                    -- Changes
                    field_name TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    
                    -- Context
                    ip_address TEXT,
                    user_agent TEXT,
                    session_id TEXT,
                    
                    -- Additional
                    notes TEXT,
                    related_entity_type TEXT,
                    related_entity_id INTEGER,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_exp_audit_entity ON expense_audit_log(entity_type, entity_id)")
            db.execute("CREATE INDEX idx_exp_audit_user ON expense_audit_log(user_id, created_at)")
            db.execute("CREATE INDEX idx_exp_audit_action ON expense_audit_log(action, created_at)")
            db.commit()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_expense_setting(setting_key, default=None):
    """Get an expense/travel setting value."""
    result = get_one("SELECT setting_value FROM expense_settings WHERE setting_key = ? AND is_active = 1", (setting_key,))
    return result['setting_value'] if result else default


def set_expense_setting(setting_key, value, category='general'):
    """Set an expense/travel setting value."""
    with get_db_context() as db:
        existing = db.execute("SELECT id FROM expense_settings WHERE setting_key = ?", (setting_key,)).fetchone()
        if existing:
            db.execute("UPDATE expense_settings SET setting_value = ?, category = ?, updated_at = CURRENT_TIMESTAMP WHERE setting_key = ?",
                       (str(value), category, setting_key))
        else:
            db.execute("INSERT INTO expense_settings (setting_key, setting_value, setting_type, category) VALUES (?, ?, 'string', ?)",
                       (setting_key, str(value), category))
        db.commit()


def get_next_claim_number():
    """Generate next expense claim number."""
    prefix = get_expense_setting('expense_claim_prefix', 'EXP')
    next_num = int(get_expense_setting('expense_claim_next_number', '10001'))
    number = f"{prefix}{next_num:05d}"
    set_expense_setting('expense_claim_next_number', str(next_num + 1))
    return number


def get_next_travel_number():
    """Generate next travel request number."""
    prefix = get_expense_setting('travel_request_prefix', 'TRV')
    next_num = int(get_expense_setting('travel_request_next_number', '10001'))
    number = f"{prefix}{next_num:05d}"
    set_expense_setting('travel_request_next_number', str(next_num + 1))
    return number


def get_next_advance_number():
    """Generate next cash advance number."""
    prefix = get_expense_setting('advance_prefix', 'ADV')
    next_num = int(get_expense_setting('advance_next_number', '10001'))
    number = f"{prefix}{next_num:05d}"
    set_expense_setting('advance_next_number', str(next_num + 1))
    return number


def log_expense_audit(entity_type, entity_id, action, user_id=None, user_name=None,
                       field_name=None, old_value=None, new_value=None, notes=None,
                       related_entity_type=None, related_entity_id=None, ip_address=None):
    """Log an expense module audit entry."""
    with get_db_context() as db:
        db.execute("""
            INSERT INTO expense_audit_log 
            (entity_type, entity_id, action, user_id, user_name, field_name, old_value, new_value,
             notes, related_entity_type, related_entity_id, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (entity_type, entity_id, action, user_id, user_name, field_name, old_value, new_value,
              notes, related_entity_type, related_entity_id, ip_address))
        db.commit()


# ============================================================================
# EXPENSE CLAIM CRUD OPERATIONS
# ============================================================================

def create_expense_claim(data):
    """Create a new expense claim."""
    claim_number = get_next_claim_number()
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO expense_claims (
                claim_number, claim_type, status, employee_id, employee_code, employee_name,
                department_id, department_name, branch_id, branch_name, company_id,
                claim_date, currency, business_purpose, project_code, project_name,
                cost_center_id, cost_center_name, cost_center_code,
                travel_request_id, trip_purpose, policy_id, policy_name,
                notes, submitted_by, submitted_by_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            claim_number, data.get('claim_type', 'expense'), 'draft',
            data.get('employee_id'), data.get('employee_code'), data.get('employee_name'),
            data.get('department_id'), data.get('department_name'),
            data.get('branch_id'), data.get('branch_name'), data.get('company_id'),
            data.get('claim_date'), data.get('currency', 'AED'), data.get('business_purpose'),
            data.get('project_code'), data.get('project_name'),
            data.get('cost_center_id'), data.get('cost_center_name'), data.get('cost_center_code'),
            data.get('travel_request_id'), data.get('trip_purpose'),
            data.get('policy_id'), data.get('policy_name'),
            data.get('notes'), data.get('submitted_by'), data.get('submitted_by_name')
        ))
        db.commit()
        return cursor.lastrowid, claim_number


def add_expense_claim_line(claim_id, data):
    """Add a line item to an expense claim."""
    with get_db_context() as db:
        # Get next line number
        result = db.execute("SELECT MAX(line_number) as max_line FROM expense_claim_lines WHERE claim_id = ?", (claim_id,)).fetchone()
        next_line = (result['max_line'] or 0) + 1
        
        cursor = db.execute("""
            INSERT INTO expense_claim_lines (
                claim_id, line_number, category_id, category_code, category_name,
                expense_date, expense_description, amount, amount_currency,
                amount_base, exchange_rate, base_currency, vat_amount, vat_rate, total_with_vat,
                vendor_name, vendor_id, invoice_number, invoice_date,
                receipt_id, has_receipt, cost_center_id, cost_center_name, cost_center_code,
                department_id, department_name, project_code, project_name,
                is_compliant, exception_reason, is_mileage, mileage_km, mileage_rate, mileage_total,
                is_per_diem, per_diem_days, per_diem_rate, per_diem_total,
                travel_segment_id, itinerary_day, line_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            claim_id, next_line, data.get('category_id'), data.get('category_code'), data.get('category_name'),
            data.get('expense_date'), data.get('expense_description'), data.get('amount'), data.get('amount_currency', 'AED'),
            data.get('amount_base'), data.get('exchange_rate', 1), data.get('base_currency', 'AED'),
            data.get('vat_amount', 0), data.get('vat_rate', 0), data.get('total_with_vat'),
            data.get('vendor_name'), data.get('vendor_id'), data.get('invoice_number'), data.get('invoice_date'),
            data.get('receipt_id'), data.get('has_receipt', 0), data.get('cost_center_id'), data.get('cost_center_name'),
            data.get('cost_center_code'), data.get('department_id'), data.get('department_name'),
            data.get('project_code'), data.get('project_name'),
            data.get('is_compliant', 1), data.get('exception_reason'),
            data.get('is_mileage', 0), data.get('mileage_km'), data.get('mileage_rate'), data.get('mileage_total'),
            data.get('is_per_diem', 0), data.get('per_diem_days'), data.get('per_diem_rate'), data.get('per_diem_total'),
            data.get('travel_segment_id'), data.get('itinerary_day'), data.get('line_notes')
        ))
        
        # Update claim total
        db.execute("""
            UPDATE expense_claims SET total_amount = (
                SELECT COALESCE(SUM(COALESCE(total_with_vat, amount)), 0) FROM expense_claim_lines WHERE claim_id = ?
            ), attachment_count = (
                SELECT COUNT(*) FROM expense_claim_lines WHERE claim_id = ? AND has_receipt = 1
            )
            WHERE id = ?
        """, (claim_id, claim_id, claim_id))
        
        db.commit()
        return cursor.lastrowid


def get_expense_claims(filters=None):
    """Get expense claims with optional filters."""
    sql = "SELECT c.*, p.policy_name as policy_name FROM expense_claims c LEFT JOIN expense_policies p ON c.policy_id = p.id WHERE 1=1"
    params = []
    
    if filters:
        if filters.get('employee_id'):
            sql += " AND c.employee_id = ?"
            params.append(filters['employee_id'])
        if filters.get('status'):
            sql += " AND c.status = ?"
            params.append(filters['status'])
        if filters.get('department_id'):
            sql += " AND c.department_id = ?"
            params.append(filters['department_id'])
        if filters.get('branch_id'):
            sql += " AND c.branch_id = ?"
            params.append(filters['branch_id'])
        if filters.get('company_id'):
            sql += " AND c.company_id = ?"
            params.append(filters['company_id'])
        if filters.get('date_from'):
            sql += " AND c.claim_date >= ?"
            params.append(filters['date_from'])
        if filters.get('date_to'):
            sql += " AND c.claim_date <= ?"
            params.append(filters['date_to'])
        if filters.get('search'):
            sql += " AND (c.claim_number LIKE ? OR c.employee_name LIKE ? OR c.business_purpose LIKE ?)"
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term, search_term])
    
    sql += " ORDER BY c.created_at DESC"
    
    if filters and filters.get('limit'):
        sql += f" LIMIT {filters['limit']}"
    
    return get_all(sql, params if params else None)


def get_expense_claim_by_id(claim_id):
    """Get a single expense claim by ID."""
    return get_one("SELECT * FROM expense_claims WHERE id = ?", (claim_id,))


def get_expense_claim_lines(claim_id):
    """Get all line items for an expense claim."""
    return get_all("SELECT * FROM expense_claim_lines WHERE claim_id = ? ORDER BY line_number", (claim_id,))


def update_expense_claim(claim_id, data):
    """Update an expense claim."""
    fields = []
    values = []
    
    updatable = [
        'status', 'claim_date', 'currency', 'business_purpose', 'project_code', 'project_name',
        'cost_center_id', 'cost_center_name', 'cost_center_code', 'travel_request_id', 'trip_purpose',
        'policy_id', 'policy_name', 'is_policy_compliant', 'has_exceptions',
        'current_approver_id', 'current_approver_name', 'approval_level', 'approval_deadline',
        'reimbursement_id', 'reimbursement_status', 'payment_date', 'payment_reference',
        'journal_entry_id', 'notes', 'internal_notes',
        'approved_by', 'approved_by_name', 'rejected_by', 'rejected_by_name', 'rejection_reason'
    ]
    
    for field in updatable:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    
    if not fields:
        return False
    
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(claim_id)
    
    with get_db_context() as db:
        db.execute(f"UPDATE expense_claims SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
    
    return True


# ============================================================================
# TRAVEL REQUEST CRUD OPERATIONS
# ============================================================================

def create_travel_request(data):
    """Create a new travel request."""
    travel_number = get_next_travel_number()
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO travel_requests (
                travel_number, status, employee_id, employee_code, employee_name,
                department_id, department_name, branch_id, branch_name, company_id,
                trip_purpose, trip_type, destination_country, destination_city,
                travel_start_date, travel_end_date, total_trip_days,
                request_date, estimated_total_cost, estimated_total_cost_currency,
                pre_approved_budget, pre_approved_budget_currency,
                advance_requested, advance_requested_currency,
                policy_id, policy_name, justification, notes,
                submitted_by, submitted_by_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            travel_number, 'draft', data.get('employee_id'), data.get('employee_code'), data.get('employee_name'),
            data.get('department_id'), data.get('department_name'), data.get('branch_id'), data.get('branch_name'),
            data.get('company_id'), data.get('trip_purpose'), data.get('trip_type'),
            data.get('destination_country'), data.get('destination_city'),
            data.get('travel_start_date'), data.get('travel_end_date'), data.get('total_trip_days'),
            data.get('request_date'), data.get('estimated_total_cost', 0), data.get('estimated_total_cost_currency', 'AED'),
            data.get('pre_approved_budget'), data.get('pre_approved_budget_currency', 'AED'),
            data.get('advance_requested', 0), data.get('advance_requested_currency', 'AED'),
            data.get('policy_id'), data.get('policy_name'), data.get('justification'), data.get('notes'),
            data.get('submitted_by'), data.get('submitted_by_name')
        ))
        db.commit()
        return cursor.lastrowid, travel_number


def get_travel_requests(filters=None):
    """Get travel requests with optional filters."""
    sql = "SELECT * FROM travel_requests WHERE 1=1"
    params = []
    
    if filters:
        if filters.get('employee_id'):
            sql += " AND employee_id = ?"
            params.append(filters['employee_id'])
        if filters.get('status'):
            sql += " AND status = ?"
            params.append(filters['status'])
        if filters.get('department_id'):
            sql += " AND department_id = ?"
            params.append(filters['department_id'])
        if filters.get('branch_id'):
            sql += " AND branch_id = ?"
            params.append(filters['branch_id'])
        if filters.get('date_from'):
            sql += " AND travel_start_date >= ?"
            params.append(filters['date_from'])
        if filters.get('date_to'):
            sql += " AND travel_end_date <= ?"
            params.append(filters['date_to'])
        if filters.get('search'):
            sql += " AND (travel_number LIKE ? OR employee_name LIKE ? OR trip_purpose LIKE ?)"
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term, search_term])
    
    sql += " ORDER BY created_at DESC"
    
    if filters and filters.get('limit'):
        sql += f" LIMIT {filters['limit']}"
    
    return get_all(sql, params if params else None)


def get_travel_request_by_id(request_id):
    """Get a single travel request by ID."""
    return get_one("SELECT * FROM travel_requests WHERE id = ?", (request_id,))


def get_travel_itineraries(travel_request_id):
    """Get all itinerary items for a travel request."""
    return get_all("SELECT * FROM travel_itineraries WHERE travel_request_id = ? ORDER BY sequence_order", (travel_request_id,))


def update_travel_request(request_id, data):
    """Update a travel request."""
    fields = []
    values = []

    updatable = [
        'status', 'trip_purpose', 'trip_type', 'destination_country', 'destination_city',
        'travel_start_date', 'travel_end_date', 'total_trip_days',
        'estimated_total_cost', 'estimated_total_cost_currency',
        'pre_approved_budget', 'pre_approved_budget_currency',
        'advance_requested', 'advance_requested_currency',
        'policy_id', 'policy_name', 'justification', 'notes',
        'current_approver_id', 'current_approver_name', 'approval_level', 'approval_deadline',
        'approved_by', 'approved_by_name', 'approval_date',
        'rejected_by', 'rejected_by_name', 'rejection_reason'
    ]

    for field in updatable:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])

    if not fields:
        return False

    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(request_id)

    with get_db_context() as db:
        db.execute(f"UPDATE travel_requests SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()

    return True


# ============================================================================
# CASH ADVANCE CRUD OPERATIONS
# ============================================================================

def create_cash_advance(data):
    """Create a new cash advance request."""
    advance_number = get_next_advance_number()
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO cash_advances (
                advance_number, status, employee_id, employee_code, employee_name,
                department_id, department_name, branch_id, branch_name, company_id,
                request_date, requested_amount, requested_currency,
                requested_amount_base, base_currency, exchange_rate,
                purpose, travel_request_id, trip_purpose, expected_expense_type, expected_destination,
                policy_id, policy_name, notes, submitted_by, submitted_by_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            advance_number, 'draft', data.get('employee_id'), data.get('employee_code'), data.get('employee_name'),
            data.get('department_id'), data.get('department_name'), data.get('branch_id'), data.get('branch_name'),
            data.get('company_id'), data.get('request_date'), data.get('requested_amount'), data.get('requested_currency', 'AED'),
            data.get('requested_amount_base'), data.get('base_currency', 'AED'), data.get('exchange_rate', 1),
            data.get('purpose'), data.get('travel_request_id'), data.get('trip_purpose'),
            data.get('expected_expense_type'), data.get('expected_destination'),
            data.get('policy_id'), data.get('policy_name'), data.get('notes'),
            data.get('submitted_by'), data.get('submitted_by_name')
        ))
        db.commit()
        return cursor.lastrowid, advance_number


def get_cash_advances(filters=None):
    """Get cash advances with optional filters."""
    sql = "SELECT * FROM cash_advances WHERE 1=1"
    params = []
    
    if filters:
        if filters.get('employee_id'):
            sql += " AND employee_id = ?"
            params.append(filters['employee_id'])
        if filters.get('status'):
            sql += " AND status = ?"
            params.append(filters['status'])
        if filters.get('overdue'):
            sql += " AND overdue_days > 0 AND status NOT IN ('settled', 'recovered')"
    
    sql += " ORDER BY created_at DESC"
    return get_all(sql, params if params else None)


def get_cash_advance_by_id(advance_id):
    """Get a single cash advance by ID."""
    return get_one("SELECT * FROM cash_advances WHERE id = ?", (advance_id,))


# ============================================================================
# RECEIPT OPERATIONS
# ============================================================================

def add_expense_receipt(data):
    """Add a receipt to an expense claim."""
    receipt_number = f"RCP{data.get('claim_id', '000'):05d}{data.get('uploaded_by', '000'):03d}"
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO expense_receipts (
                receipt_number, claim_id, claim_line_id, file_name, file_path, file_size,
                mime_type, original_file_name, receipt_date, merchant_name,
                total_amount, currency, exchange_rate, base_amount, base_currency,
                uploaded_by, uploaded_by_name, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            receipt_number, data.get('claim_id'), data.get('claim_line_id'),
            data.get('file_name'), data.get('file_path'), data.get('file_size'),
            data.get('mime_type'), data.get('original_file_name'), data.get('receipt_date'),
            data.get('merchant_name'), data.get('total_amount'), data.get('currency', 'AED'),
            data.get('exchange_rate', 1), data.get('base_amount'), data.get('base_currency', 'AED'),
            data.get('uploaded_by'), data.get('uploaded_by_name'), 'pending'
        ))
        
        # Update claim line if provided
        if data.get('claim_line_id'):
            db.execute("UPDATE expense_claim_lines SET has_receipt = 1, receipt_id = ? WHERE id = ?",
                       (cursor.lastrowid, data.get('claim_line_id')))
        
        db.commit()
        return cursor.lastrowid, receipt_number


def get_expense_receipts(filters=None):
    """Get expense receipts with optional filters."""
    sql = "SELECT * FROM expense_receipts WHERE 1=1"
    params = []
    
    if filters:
        if filters.get('claim_id'):
            sql += " AND claim_id = ?"
            params.append(filters['claim_id'])
        if filters.get('status'):
            sql += " AND status = ?"
            params.append(filters['status'])
        if filters.get('uploaded_by'):
            sql += " AND uploaded_by = ?"
            params.append(filters['uploaded_by'])
    
    sql += " ORDER BY created_at DESC"
    return get_all(sql, params if params else None)


# ============================================================================
# REIMBURSEMENT OPERATIONS
# ============================================================================

def create_reimbursement(data):
    """Create a new reimbursement record."""
    reim_number = f"REIM{data.get('claim_id', '000'):05d}{int(data.get('reimbursement_amount', 0)):05d}"
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO expense_reimbursements (
                reimbursement_number, status, claim_id, claim_number,
                employee_id, employee_name, department_name,
                reimbursement_amount, currency, reimbursement_amount_base, base_currency, exchange_rate,
                advance_id, advance_number, advance_deduction, net_reimbursement,
                notes, approved_by, approved_by_name, approved_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            reim_number, 'pending', data.get('claim_id'), data.get('claim_number'),
            data.get('employee_id'), data.get('employee_name'), data.get('department_name'),
            data.get('reimbursement_amount'), data.get('currency', 'AED'),
            data.get('reimbursement_amount_base'), data.get('base_currency', 'AED'), data.get('exchange_rate', 1),
            data.get('advance_id'), data.get('advance_number'), data.get('advance_deduction', 0),
            data.get('net_reimbursement'),
            data.get('notes'), data.get('approved_by'), data.get('approved_by_name'), data.get('approved_date')
        ))
        db.commit()
        return cursor.lastrowid, reim_number


def get_reimbursements(filters=None):
    """Get reimbursements with optional filters."""
    sql = "SELECT * FROM expense_reimbursements WHERE 1=1"
    params = []
    
    if filters:
        if filters.get('employee_id'):
            sql += " AND employee_id = ?"
            params.append(filters['employee_id'])
        if filters.get('status'):
            sql += " AND status = ?"
            params.append(filters['status'])
        if filters.get('claim_id'):
            sql += " AND claim_id = ?"
            params.append(filters['claim_id'])
    
    sql += " ORDER BY created_at DESC"
    return get_all(sql, params if params else None)


# ============================================================================
# DASHBOARD STATISTICS
# ============================================================================

def get_expense_dashboard_stats(company_id=None, department_id=None, branch_id=None, user_id=None, role=None):
    """Get expense dashboard statistics."""
    
    # Base filters
    dept_filter = f"AND department_id = {department_id}" if department_id else ""
    branch_filter = f"AND branch_id = {branch_id}" if branch_id else ""
    company_filter = f"AND company_id = {company_id}" if company_id else ""
    
    # Employee scope filter
    if role == 'employee' and user_id:
        scope_filter = f"AND employee_id = {user_id}"
    elif role == 'manager':
        scope_filter = ""  # Managers see their department
    else:
        scope_filter = ""
    
    base_where = f"WHERE 1=1 {company_filter} {dept_filter} {branch_filter} {scope_filter}"
    
    stats = {}
    
    # Expense Claims Stats
    claims_stats = get_one(f"""
        SELECT 
            COUNT(*) as total_claims,
            SUM(CASE WHEN status = 'draft' THEN 1 ELSE 0 END) as draft_claims,
            SUM(CASE WHEN status = 'submitted' THEN 1 ELSE 0 END) as submitted_claims,
            SUM(CASE WHEN status = 'under_review' THEN 1 ELSE 0 END) as under_review_claims,
            SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_claims,
            SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected_claims,
            SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid_claims,
            SUM(CASE WHEN status = 'returned' THEN 1 ELSE 0 END) as returned_claims,
            COALESCE(SUM(CASE WHEN status NOT IN ('draft', 'cancelled', 'rejected') THEN total_amount ELSE 0 END), 0) as total_submitted_amount,
            COALESCE(SUM(CASE WHEN status = 'paid' THEN total_amount ELSE 0 END), 0) as total_paid_amount,
            COALESCE(SUM(CASE WHEN has_exceptions = 1 THEN 1 ELSE 0 END), 0) as claims_with_violations
        FROM expense_claims {base_where}
    """)
    stats['claims'] = dict(claims_stats) if claims_stats else {}
    
    # Travel Requests Stats
    travel_stats = get_one(f"""
        SELECT 
            COUNT(*) as total_requests,
            SUM(CASE WHEN status = 'draft' THEN 1 ELSE 0 END) as draft_requests,
            SUM(CASE WHEN status = 'submitted' THEN 1 ELSE 0 END) as submitted_requests,
            SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_requests,
            SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected_requests,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_trips,
            SUM(CASE WHEN is_booked = 1 AND status = 'approved' THEN 1 ELSE 0 END) as booked_trips,
            COALESCE(SUM(estimated_total_cost), 0) as total_estimated_cost,
            COALESCE(SUM(advance_requested), 0) as total_advances_requested
        FROM travel_requests {base_where}
    """)
    stats['travel'] = dict(travel_stats) if travel_stats else {}
    
    # Cash Advances Stats
    advance_stats = get_one(f"""
        SELECT 
            COUNT(*) as total_advances,
            SUM(CASE WHEN status = 'draft' THEN 1 ELSE 0 END) as draft_advances,
            SUM(CASE WHEN status = 'submitted' THEN 1 ELSE 0 END) as submitted_advances,
            SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_advances,
            SUM(CASE WHEN status = 'issued' THEN 1 ELSE 0 END) as issued_advances,
            SUM(CASE WHEN status = 'settled' THEN 1 ELSE 0 END) as settled_advances,
            SUM(CASE WHEN status = 'partially_settled' THEN 1 ELSE 0 END) as partial_advances,
            SUM(CASE WHEN overdue_days > 0 AND status NOT IN ('settled', 'recovered') THEN 1 ELSE 0 END) as overdue_advances,
            COALESCE(SUM(requested_amount), 0) as total_requested,
            COALESCE(SUM(CASE WHEN is_issued = 1 THEN approved_amount ELSE 0 END), 0) as total_issued,
            COALESCE(SUM(outstanding_balance), 0) as total_outstanding
        FROM cash_advances {base_where}
    """)
    stats['advances'] = dict(advance_stats) if advance_stats else {}
    
    # Reimbursements Stats
    reim_stats = get_one(f"""
        SELECT 
            COUNT(*) as total_reimbursements,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_reimbursements,
            SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_reimbursements,
            SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid_reimbursements,
            COALESCE(SUM(reimbursement_amount), 0) as total_reimbursed,
            COALESCE(SUM(CASE WHEN status = 'paid' THEN net_reimbursement ELSE 0 END), 0) as total_paid
        FROM expense_reimbursements r
        LEFT JOIN expense_claims c ON r.claim_id = c.id
        {base_where.replace('expense_claims', 'c')}
    """)
    stats['reimbursements'] = dict(reim_stats) if reim_stats else {}
    
    # Policy Violations Stats
    violation_stats = get_one(f"""
        SELECT 
            COUNT(*) as total_violations,
            SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_violations,
            SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_violations,
            SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected_violations,
            SUM(CASE WHEN severity = 'high' AND status = 'open' THEN 1 ELSE 0 END) as high_severity_open,
            SUM(CASE WHEN severity = 'critical' AND status = 'open' THEN 1 ELSE 0 END) as critical_open
        FROM expense_violations v
        LEFT JOIN expense_claims c ON v.claim_id = c.id
        {base_where.replace('expense_claims', 'c')}
    """)
    stats['violations'] = dict(violation_stats) if violation_stats else {}
    
    # Missing Receipts
    missing_receipts = get_one(f"""
        SELECT COUNT(*) as missing_receipts
        FROM expense_claim_lines l
        JOIN expense_claims c ON l.claim_id = c.id
        WHERE l.has_receipt = 0 AND c.status NOT IN ('draft', 'cancelled')
        {scope_filter.replace('employee_id', 'c.employee_id') if scope_filter else ''}
    """)
    stats['missing_receipts'] = missing_receipts['missing_receipts'] if missing_receipts else 0
    
    # Pending Approvals (for managers/finance)
    pending_approvals = get_one(f"""
        SELECT 
            (SELECT COUNT(*) FROM expense_claims WHERE status IN ('submitted', 'under_review') {company_filter} {dept_filter} {branch_filter}) +
            (SELECT COUNT(*) FROM travel_requests WHERE status IN ('submitted', 'under_review') {company_filter} {dept_filter} {branch_filter}) +
            (SELECT COUNT(*) FROM cash_advances WHERE status IN ('submitted', 'under_review') {company_filter} {dept_filter} {branch_filter}) as total_pending
    """)
    stats['pending_approvals'] = pending_approvals['total_pending'] if pending_approvals else 0
    
    return stats


def get_expense_summary_by_department(date_from=None, date_to=None, company_id=None):
    """Get expense summary grouped by department."""
    sql = """
        SELECT 
            department_name,
            COUNT(*) as claim_count,
            SUM(total_amount) as total_amount,
            AVG(total_amount) as avg_amount,
            MIN(total_amount) as min_amount,
            MAX(total_amount) as max_amount
        FROM expense_claims
        WHERE status IN ('approved', 'paid')
    """
    params = []
    
    if date_from:
        sql += " AND claim_date >= ?"
        params.append(date_from)
    if date_to:
        sql += " AND claim_date <= ?"
        params.append(date_to)
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    
    sql += " GROUP BY department_name ORDER BY total_amount DESC"
    
    return get_all(sql, params)


def get_expense_summary_by_category(date_from=None, date_to=None, company_id=None):
    """Get expense summary grouped by category."""
    sql = """
        SELECT 
            l.category_name,
            l.category_code,
            COUNT(*) as line_count,
            SUM(l.amount) as total_amount,
            AVG(l.amount) as avg_amount
        FROM expense_claim_lines l
        JOIN expense_claims c ON l.claim_id = c.id
        WHERE c.status IN ('approved', 'paid')
    """
    params = []
    
    if date_from:
        sql += " AND c.claim_date >= ?"
        params.append(date_from)
    if date_to:
        sql += " AND c.claim_date <= ?"
        params.append(date_to)
    if company_id:
        sql += " AND c.company_id = ?"
        params.append(company_id)
    
    sql += " GROUP BY l.category_name, l.category_code ORDER BY total_amount DESC"
    
    return get_all(sql, params)


def get_travel_summary_by_destination(date_from=None, date_to=None, company_id=None):
    """Get travel summary grouped by destination."""
    sql = """
        SELECT 
            destination_country,
            destination_city,
            COUNT(*) as trip_count,
            SUM(total_trip_days) as total_days,
            SUM(estimated_total_cost) as total_cost,
            AVG(estimated_total_cost) as avg_cost
        FROM travel_requests
        WHERE status IN ('approved', 'completed')
    """
    params = []
    
    if date_from:
        sql += " AND travel_start_date >= ?"
        params.append(date_from)
    if date_to:
        sql += " AND travel_end_date <= ?"
        params.append(date_to)
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    
    sql += " GROUP BY destination_country, destination_city ORDER BY total_cost DESC"
    
    return get_all(sql, params)
