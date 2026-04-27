"""
Legal / Tax Reporting Module - Data Models
==========================================
Comprehensive legal and tax reporting models covering:
- Tax Jurisdictions & Authorities
- Tax Registrations & Groups
- Tax Codes, Rates & Rules
- Filing Periods & Returns
- Transaction Review & Exceptions
- Obligations & Compliance Tasks
- Reconciliations
- Notices, Penalties & Disputes
- Filing Submissions & Payments
- Audit Packs & Report Templates
- Export Profiles & Settings
- Flow & Document Links

Author: Legal/Tax Module Implementation
"""

from database import get_db_context, get_one, get_all, row_to_dict, rows_to_list, table_exists, log_audit

# ============================================================================
# LEGAL/TAX MODULE INITIALIZATION
# ============================================================================

def initialize_legal_tax_schema():
    """Initialize all legal/tax module tables."""
    _create_tax_jurisdictions()
    _create_tax_authorities()
    _create_legal_entities()
    _create_tax_groups()
    _create_tax_codes()
    _create_tax_rates()
    _create_tax_rules()
    _create_filing_periods()
    _create_returns()
    _create_return_lines()
    _create_return_adjustments()
    _create_return_approvals()
    _create_obligations()
    _create_compliance_tasks()
    _create_tax_review_items()
    _create_tax_review_comments()
    _create_reconciliations()
    _create_reconciliation_lines()
    _create_notices()
    _create_penalties()
    _create_disputes()
    _create_filing_submissions()
    _create_filing_payments()
    _create_audit_packs()
    _create_report_templates()
    _create_export_profiles()
    _create_settings()
    _create_flow_links()
    _create_document_links()
    _create_legal_tax_settings()


# ============================================================================
# TAX JURISDICTIONS
# ============================================================================

def _create_tax_jurisdictions():
    """Create tax jurisdictions table."""
    if not table_exists('tax_jurisdictions'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE tax_jurisdictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    name_ar TEXT,
                    name_fa TEXT,
                    country TEXT NOT NULL,
                    region TEXT,
                    tax_type TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_jur_code ON tax_jurisdictions(code)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_jur_country ON tax_jurisdictions(country)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_jur_company ON tax_jurisdictions(company_id)")
            db.commit()


def get_tax_jurisdictions(company_id=None, active_only=True):
    """Get all tax jurisdictions."""
    sql = "SELECT * FROM tax_jurisdictions WHERE is_deleted = 0"
    params = []
    if company_id:
        sql += " AND (company_id = ? OR company_id IS NULL)"
        params.append(company_id)
    if active_only:
        sql += " AND is_active = 1"
    sql += " ORDER BY name"
    return get_all(sql, params if params else None)


def get_tax_jurisdiction_by_id(jurisdiction_id):
    """Get a single jurisdiction by ID."""
    return get_one("SELECT * FROM tax_jurisdictions WHERE id = ? AND is_deleted = 0", (jurisdiction_id,))


def create_tax_jurisdiction(data):
    """Create a new tax jurisdiction."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO tax_jurisdictions (
                code, name, name_ar, name_fa, country, region, tax_type,
                is_active, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('code'),
            data.get('name'),
            data.get('name_ar'),
            data.get('name_fa'),
            data.get('country'),
            data.get('region'),
            data.get('tax_type'),
            data.get('is_active', 1),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def update_tax_jurisdiction(jurisdiction_id, data):
    """Update a tax jurisdiction."""
    fields = []
    values = []
    updatable = ['code', 'name', 'name_ar', 'name_fa', 'country', 'region', 'tax_type', 'is_active', 'company_id']
    for field in updatable:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return False
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(jurisdiction_id)
    with get_db_context() as db:
        db.execute(f"UPDATE tax_jurisdictions SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
        return True


def delete_tax_jurisdiction(jurisdiction_id):
    """Soft delete a tax jurisdiction."""
    with get_db_context() as db:
        db.execute("UPDATE tax_jurisdictions SET is_deleted = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (jurisdiction_id,))
        db.commit()
        return True


# ============================================================================
# TAX AUTHORITIES
# ============================================================================

def _create_tax_authorities():
    """Create tax authorities table."""
    if not table_exists('tax_authorities'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE tax_authorities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    name_ar TEXT,
                    name_fa TEXT,
                    jurisdiction_id INTEGER NOT NULL,
                    address TEXT,
                    city TEXT,
                    country TEXT,
                    postal_code TEXT,
                    phone TEXT,
                    email TEXT,
                    website TEXT,
                    contact_person TEXT,
                    is_active INTEGER DEFAULT 1,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (jurisdiction_id) REFERENCES tax_jurisdictions(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_auth_code ON tax_authorities(code)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_auth_jurisdiction ON tax_authorities(jurisdiction_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_auth_company ON tax_authorities(company_id)")
            db.commit()


def get_tax_authorities(jurisdiction_id=None, company_id=None, active_only=True):
    """Get all tax authorities."""
    sql = "SELECT * FROM tax_authorities WHERE is_deleted = 0"
    params = []
    if jurisdiction_id:
        sql += " AND jurisdiction_id = ?"
        params.append(jurisdiction_id)
    if company_id:
        sql += " AND (company_id = ? OR company_id IS NULL)"
        params.append(company_id)
    if active_only:
        sql += " AND is_active = 1"
    sql += " ORDER BY name"
    return get_all(sql, params if params else None)


def get_tax_authority_by_id(authority_id):
    """Get a single tax authority by ID."""
    return get_one("SELECT * FROM tax_authorities WHERE id = ? AND is_deleted = 0", (authority_id,))


def create_tax_authority(data):
    """Create a new tax authority."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO tax_authorities (
                code, name, name_ar, name_fa, jurisdiction_id, address, city,
                country, postal_code, phone, email, website, contact_person,
                is_active, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('code'),
            data.get('name'),
            data.get('name_ar'),
            data.get('name_fa'),
            data.get('jurisdiction_id'),
            data.get('address'),
            data.get('city'),
            data.get('country'),
            data.get('postal_code'),
            data.get('phone'),
            data.get('email'),
            data.get('website'),
            data.get('contact_person'),
            data.get('is_active', 1),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def update_tax_authority(authority_id, data):
    """Update a tax authority."""
    fields = []
    values = []
    updatable = ['code', 'name', 'name_ar', 'name_fa', 'jurisdiction_id', 'address', 'city',
                 'country', 'postal_code', 'phone', 'email', 'website', 'contact_person', 'is_active', 'company_id']
    for field in updatable:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return False
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(authority_id)
    with get_db_context() as db:
        db.execute(f"UPDATE tax_authorities SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
        return True


def delete_tax_authority(authority_id):
    """Soft delete a tax authority."""
    with get_db_context() as db:
        db.execute("UPDATE tax_authorities SET is_deleted = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (authority_id,))
        db.commit()
        return True


# ============================================================================
# LEGAL ENTITIES
# ============================================================================

def _create_legal_entities():
    """Create legal entities table."""
    if not table_exists('legal_entities'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE legal_entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    name_ar TEXT,
                    name_fa TEXT,
                    registration_number TEXT,
                    tax_identification_number TEXT,
                    vat_number TEXT,
                    jurisdiction_id INTEGER,
                    address TEXT,
                    city TEXT,
                    country TEXT,
                    postal_code TEXT,
                    phone TEXT,
                    email TEXT,
                    is_active INTEGER DEFAULT 1,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (jurisdiction_id) REFERENCES tax_jurisdictions(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_entity_code ON legal_entities(code)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_entity_jurisdiction ON legal_entities(jurisdiction_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_entity_company ON legal_entities(company_id)")
            db.commit()


def get_legal_entities(company_id=None, jurisdiction_id=None, active_only=True):
    """Get all legal entities."""
    sql = "SELECT * FROM legal_entities WHERE is_deleted = 0"
    params = []
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    if jurisdiction_id:
        sql += " AND jurisdiction_id = ?"
        params.append(jurisdiction_id)
    if active_only:
        sql += " AND is_active = 1"
    sql += " ORDER BY name"
    return get_all(sql, params if params else None)


def get_legal_entity_by_id(entity_id):
    """Get a single legal entity by ID."""
    return get_one("SELECT * FROM legal_entities WHERE id = ? AND is_deleted = 0", (entity_id,))


def create_legal_entity(data):
    """Create a new legal entity."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO legal_entities (
                code, name, name_ar, name_fa, registration_number,
                tax_identification_number, vat_number, jurisdiction_id,
                address, city, country, postal_code, phone, email,
                is_active, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('code'),
            data.get('name'),
            data.get('name_ar'),
            data.get('name_fa'),
            data.get('registration_number'),
            data.get('tax_identification_number'),
            data.get('vat_number'),
            data.get('jurisdiction_id'),
            data.get('address'),
            data.get('city'),
            data.get('country'),
            data.get('postal_code'),
            data.get('phone'),
            data.get('email'),
            data.get('is_active', 1),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def update_legal_entity(entity_id, data):
    """Update a legal entity."""
    fields = []
    values = []
    updatable = ['code', 'name', 'name_ar', 'name_fa', 'registration_number',
                 'tax_identification_number', 'vat_number', 'jurisdiction_id',
                 'address', 'city', 'country', 'postal_code', 'phone', 'email', 'is_active', 'company_id']
    for field in updatable:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return False
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(entity_id)
    with get_db_context() as db:
        db.execute(f"UPDATE legal_entities SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
        return True


# ============================================================================
# TAX GROUPS
# ============================================================================

def _create_tax_groups():
    """Create tax groups table."""
    if not table_exists('tax_groups'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE tax_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    name_ar TEXT,
                    name_fa TEXT,
                    description TEXT,
                    is_active INTEGER DEFAULT 1,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_group_code ON tax_groups(code)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_group_company ON tax_groups(company_id)")
            db.commit()


def get_tax_groups(company_id=None, active_only=True):
    """Get all tax groups."""
    sql = "SELECT * FROM tax_groups WHERE is_deleted = 0"
    params = []
    if company_id:
        sql += " AND (company_id = ? OR company_id IS NULL)"
        params.append(company_id)
    if active_only:
        sql += " AND is_active = 1"
    sql += " ORDER BY name"
    return get_all(sql, params if params else None)


def get_tax_group_by_id(group_id):
    """Get a single tax group by ID."""
    return get_one("SELECT * FROM tax_groups WHERE id = ? AND is_deleted = 0", (group_id,))


def create_tax_group(data):
    """Create a new tax group."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO tax_groups (code, name, name_ar, name_fa, description, is_active, company_id, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('code'),
            data.get('name'),
            data.get('name_ar'),
            data.get('name_fa'),
            data.get('description'),
            data.get('is_active', 1),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def update_tax_group(group_id, data):
    """Update a tax group."""
    fields = []
    values = []
    updatable = ['code', 'name', 'name_ar', 'name_fa', 'description', 'is_active', 'company_id']
    for field in updatable:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return False
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(group_id)
    with get_db_context() as db:
        db.execute(f"UPDATE tax_groups SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
        return True


# ============================================================================
# TAX CODES
# ============================================================================

def _create_tax_codes():
    """Create tax codes table."""
    if not table_exists('tax_codes'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE tax_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    name_ar TEXT,
                    name_fa TEXT,
                    description TEXT,
                    tax_group_id INTEGER,
                    jurisdiction_id INTEGER,
                    tax_rate_id INTEGER,
                    is_active INTEGER DEFAULT 1,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (tax_group_id) REFERENCES tax_groups(id),
                    FOREIGN KEY (jurisdiction_id) REFERENCES tax_jurisdictions(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_taxcode_code ON tax_codes(code)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_taxcode_group ON tax_codes(tax_group_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_taxcode_jurisdiction ON tax_codes(jurisdiction_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_taxcode_company ON tax_codes(company_id)")
            db.commit()


def get_tax_codes(company_id=None, jurisdiction_id=None, tax_group_id=None, active_only=True):
    """Get all tax codes."""
    sql = "SELECT * FROM tax_codes WHERE is_deleted = 0"
    params = []
    if company_id:
        sql += " AND (company_id = ? OR company_id IS NULL)"
        params.append(company_id)
    if jurisdiction_id:
        sql += " AND jurisdiction_id = ?"
        params.append(jurisdiction_id)
    if tax_group_id:
        sql += " AND tax_group_id = ?"
        params.append(tax_group_id)
    if active_only:
        sql += " AND is_active = 1"
    sql += " ORDER BY code"
    return get_all(sql, params if params else None)


def get_tax_code_by_id(tax_code_id):
    """Get a single tax code by ID."""
    return get_one("SELECT * FROM tax_codes WHERE id = ? AND is_deleted = 0", (tax_code_id,))


def create_tax_code(data):
    """Create a new tax code."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO tax_codes (
                code, name, name_ar, name_fa, description, tax_group_id,
                jurisdiction_id, tax_rate_id, is_active, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('code'),
            data.get('name'),
            data.get('name_ar'),
            data.get('name_fa'),
            data.get('description'),
            data.get('tax_group_id'),
            data.get('jurisdiction_id'),
            data.get('tax_rate_id'),
            data.get('is_active', 1),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def update_tax_code(tax_code_id, data):
    """Update a tax code."""
    fields = []
    values = []
    updatable = ['code', 'name', 'name_ar', 'name_fa', 'description', 'tax_group_id',
                 'jurisdiction_id', 'tax_rate_id', 'is_active', 'company_id']
    for field in updatable:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return False
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(tax_code_id)
    with get_db_context() as db:
        db.execute(f"UPDATE tax_codes SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
        return True


# ============================================================================
# TAX RATES
# ============================================================================

def _create_tax_rates():
    """Create tax rates table."""
    if not table_exists('tax_rates'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE tax_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    name_ar TEXT,
                    name_fa TEXT,
                    rate REAL NOT NULL,
                    rate_type TEXT DEFAULT 'percentage',
                    is_active INTEGER DEFAULT 1,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    effective_from DATE,
                    effective_to DATE,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_rate_code ON tax_rates(code)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_rate_company ON tax_rates(company_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_rate_effective ON tax_rates(effective_from, effective_to)")
            db.commit()


def get_tax_rates(company_id=None, active_only=True, effective_date=None):
    """Get all tax rates."""
    sql = "SELECT * FROM tax_rates WHERE is_deleted = 0"
    params = []
    if company_id:
        sql += " AND (company_id = ? OR company_id IS NULL)"
        params.append(company_id)
    if active_only:
        sql += " AND is_active = 1"
    if effective_date:
        sql += " AND (effective_from IS NULL OR effective_from <= ?) AND (effective_to IS NULL OR effective_to >= ?)"
        params.extend([effective_date, effective_date])
    sql += " ORDER BY rate"
    return get_all(sql, params if params else None)


def get_tax_rate_by_id(rate_id):
    """Get a single tax rate by ID."""
    return get_one("SELECT * FROM tax_rates WHERE id = ? AND is_deleted = 0", (rate_id,))


def create_tax_rate(data):
    """Create a new tax rate."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO tax_rates (
                code, name, name_ar, name_fa, rate, rate_type,
                is_active, company_id, created_by, effective_from, effective_to
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('code'),
            data.get('name'),
            data.get('name_ar'),
            data.get('name_fa'),
            data.get('rate'),
            data.get('rate_type', 'percentage'),
            data.get('is_active', 1),
            data.get('company_id'),
            data.get('created_by'),
            data.get('effective_from'),
            data.get('effective_to')
        ))
        db.commit()
        return cursor.lastrowid


def update_tax_rate(rate_id, data):
    """Update a tax rate."""
    fields = []
    values = []
    updatable = ['code', 'name', 'name_ar', 'name_fa', 'rate', 'rate_type', 'is_active', 'effective_from', 'effective_to']
    for field in updatable:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return False
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(rate_id)
    with get_db_context() as db:
        db.execute(f"UPDATE tax_rates SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
        return True


# ============================================================================
# TAX RULES
# ============================================================================

def _create_tax_rules():
    """Create tax rules table."""
    if not table_exists('tax_rules'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE tax_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    name_ar TEXT,
                    name_fa TEXT,
                    description TEXT,
                    tax_code_id INTEGER,
                    jurisdiction_id INTEGER,
                    rule_type TEXT NOT NULL,
                    condition_json TEXT,
                    action_json TEXT,
                    priority INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    is_system INTEGER DEFAULT 0,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (tax_code_id) REFERENCES tax_codes(id),
                    FOREIGN KEY (jurisdiction_id) REFERENCES tax_jurisdictions(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_ idx_rule_code ON tax_rules(code)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_ idx_rule_type ON tax_rules(rule_type)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_ idx_rule_jurisdiction ON tax_rules(jurisdiction_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_ idx_rule_company ON tax_rules(company_id)")
            db.commit()


def get_tax_rules(company_id=None, jurisdiction_id=None, rule_type=None, active_only=True):
    """Get all tax rules."""
    sql = "SELECT * FROM tax_rules WHERE is_deleted = 0"
    params = []
    if company_id:
        sql += " AND (company_id = ? OR company_id IS NULL)"
        params.append(company_id)
    if jurisdiction_id:
        sql += " AND jurisdiction_id = ?"
        params.append(jurisdiction_id)
    if rule_type:
        sql += " AND rule_type = ?"
        params.append(rule_type)
    if active_only:
        sql += " AND is_active = 1"
    sql += " ORDER BY priority DESC, name"
    return get_all(sql, params if params else None)


def get_tax_rule_by_id(rule_id):
    """Get a single tax rule by ID."""
    return get_one("SELECT * FROM tax_rules WHERE id = ? AND is_deleted = 0", (rule_id,))


def create_tax_rule(data):
    """Create a new tax rule."""
    import json
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO tax_rules (
                code, name, name_ar, name_fa, description, tax_code_id,
                jurisdiction_id, rule_type, condition_json, action_json,
                priority, is_active, is_system, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('code'),
            data.get('name'),
            data.get('name_ar'),
            data.get('name_fa'),
            data.get('description'),
            data.get('tax_code_id'),
            data.get('jurisdiction_id'),
            data.get('rule_type'),
            json.dumps(data.get('condition_json')) if data.get('condition_json') else None,
            json.dumps(data.get('action_json')) if data.get('action_json') else None,
            data.get('priority', 0),
            data.get('is_active', 1),
            data.get('is_system', 0),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def update_tax_rule(rule_id, data):
    """Update a tax rule."""
    import json
    fields = []
    values = []
    updatable = ['code', 'name', 'name_ar', 'name_fa', 'description', 'tax_code_id',
                 'jurisdiction_id', 'rule_type', 'condition_json', 'action_json',
                 'priority', 'is_active', 'is_system']
    for field in updatable:
        if field in data:
            if field in ['condition_json', 'action_json']:
                fields.append(f"{field} = ?")
                values.append(json.dumps(data[field]) if data[field] else None)
            else:
                fields.append(f"{field} = ?")
                values.append(data[field])
    if not fields:
        return False
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(rule_id)
    with get_db_context() as db:
        db.execute(f"UPDATE tax_rules SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
        return True


# ============================================================================
# FILING PERIODS
# ============================================================================

def _create_filing_periods():
    """Create filing periods table."""
    if not table_exists('filing_periods'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE filing_periods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    period_type TEXT NOT NULL,
                    jurisdiction_id INTEGER,
                    authority_id INTEGER,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    due_date DATE,
                    filing_frequency TEXT,
                    status TEXT DEFAULT 'open',
                    is_locked INTEGER DEFAULT 0,
                    locked_by INTEGER,
                    locked_at TIMESTAMP,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (jurisdiction_id) REFERENCES tax_jurisdictions(id),
                    FOREIGN KEY (authority_id) REFERENCES tax_authorities(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_period_code ON filing_periods(code)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_period_jurisdiction ON filing_periods(jurisdiction_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_period_status ON filing_periods(status)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_period_company ON filing_periods(company_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_period_dates ON filing_periods(start_date, end_date)")
            db.commit()


def get_filing_periods(company_id=None, jurisdiction_id=None, status=None, period_type=None):
    """Get all filing periods."""
    sql = "SELECT * FROM filing_periods WHERE is_deleted = 0"
    params = []
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    if jurisdiction_id:
        sql += " AND jurisdiction_id = ?"
        params.append(jurisdiction_id)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if period_type:
        sql += " AND period_type = ?"
        params.append(period_type)
    sql += " ORDER BY start_date DESC"
    return get_all(sql, params if params else None)


def get_filing_period_by_id(period_id):
    """Get a single filing period by ID."""
    return get_one("SELECT * FROM filing_periods WHERE id = ? AND is_deleted = 0", (period_id,))


def create_filing_period(data):
    """Create a new filing period."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO filing_periods (
                code, name, period_type, jurisdiction_id, authority_id,
                start_date, end_date, due_date, filing_frequency,
                status, is_locked, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('code'),
            data.get('name'),
            data.get('period_type'),
            data.get('jurisdiction_id'),
            data.get('authority_id'),
            data.get('start_date'),
            data.get('end_date'),
            data.get('due_date'),
            data.get('filing_frequency'),
            data.get('status', 'open'),
            data.get('is_locked', 0),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def update_filing_period(period_id, data):
    """Update a filing period."""
    fields = []
    values = []
    updatable = ['code', 'name', 'period_type', 'jurisdiction_id', 'authority_id',
                 'start_date', 'end_date', 'due_date', 'filing_frequency', 'status', 'is_locked', 'locked_by', 'locked_at']
    for field in updatable:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return False
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(period_id)
    with get_db_context() as db:
        db.execute(f"UPDATE filing_periods SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
        return True


def lock_filing_period(period_id, user_id):
    """Lock a filing period."""
    with get_db_context() as db:
        db.execute("""
            UPDATE filing_periods
            SET is_locked = 1, locked_by = ?, locked_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, period_id))
        db.commit()
        return True


def unlock_filing_period(period_id):
    """Unlock a filing period."""
    with get_db_context() as db:
        db.execute("""
            UPDATE filing_periods
            SET is_locked = 0, locked_by = NULL, locked_at = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (period_id,))
        db.commit()
        return True


# ============================================================================
# RETURNS
# ============================================================================

def _create_returns():
    """Create legal returns table."""
    if not table_exists('legal_returns'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE legal_returns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    return_number TEXT UNIQUE NOT NULL,
                    return_type TEXT NOT NULL,
                    filing_period_id INTEGER,
                    jurisdiction_id INTEGER,
                    authority_id INTEGER,
                    entity_id INTEGER,
                    tax_jurisdiction_id INTEGER,
                    status TEXT DEFAULT 'draft',
                    filing_status TEXT DEFAULT 'pending',
                    total_output_tax REAL DEFAULT 0,
                    total_input_tax REAL DEFAULT 0,
                    total_tax_due REAL DEFAULT 0,
                    total_adjustments REAL DEFAULT 0,
                    total_payment REAL DEFAULT 0,
                    payment_status TEXT DEFAULT 'unpaid',
                    filing_reference TEXT,
                    filed_by INTEGER,
                    filed_at TIMESTAMP,
                    approved_by INTEGER,
                    approved_at TIMESTAMP,
                    is_locked INTEGER DEFAULT 0,
                    locked_by INTEGER,
                    locked_at TIMESTAMP,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (filing_period_id) REFERENCES filing_periods(id),
                    FOREIGN KEY (jurisdiction_id) REFERENCES tax_jurisdictions(id),
                    FOREIGN KEY (authority_id) REFERENCES tax_authorities(id),
                    FOREIGN KEY (entity_id) REFERENCES legal_entities(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_return_number ON legal_returns(return_number)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_return_period ON legal_returns(filing_period_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_return_status ON legal_returns(status)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_return_company ON legal_returns(company_id)")
            db.commit()


def get_returns(company_id=None, jurisdiction_id=None, status=None, filing_status=None, period_id=None):
    """Get all returns."""
    sql = "SELECT * FROM legal_returns WHERE is_deleted = 0"
    params = []
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    if jurisdiction_id:
        sql += " AND jurisdiction_id = ?"
        params.append(jurisdiction_id)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if filing_status:
        sql += " AND filing_status = ?"
        params.append(filing_status)
    if period_id:
        sql += " AND filing_period_id = ?"
        params.append(period_id)
    sql += " ORDER BY created_at DESC"
    return get_all(sql, params if params else None)


def get_return_by_id(return_id):
    """Get a single return by ID."""
    return get_one("SELECT * FROM legal_returns WHERE id = ? AND is_deleted = 0", (return_id,))


def get_return_by_number(return_number):
    """Get a return by return number."""
    return get_one("SELECT * FROM legal_returns WHERE return_number = ? AND is_deleted = 0", (return_number,))


def create_return(data):
    """Create a new return."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO legal_returns (
                return_number, return_type, filing_period_id, jurisdiction_id,
                authority_id, entity_id, tax_jurisdiction_id, status, filing_status,
                company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('return_number'),
            data.get('return_type'),
            data.get('filing_period_id'),
            data.get('jurisdiction_id'),
            data.get('authority_id'),
            data.get('entity_id'),
            data.get('tax_jurisdiction_id'),
            data.get('status', 'draft'),
            data.get('filing_status', 'pending'),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def update_return(return_id, data):
    """Update a return."""
    fields = []
    values = []
    updatable = ['return_number', 'return_type', 'filing_period_id', 'jurisdiction_id',
                 'authority_id', 'entity_id', 'tax_jurisdiction_id', 'status', 'filing_status',
                 'total_output_tax', 'total_input_tax', 'total_tax_due', 'total_adjustments',
                 'total_payment', 'payment_status', 'filing_reference', 'filed_by', 'filed_at',
                 'approved_by', 'approved_at', 'is_locked', 'locked_by', 'locked_at']
    for field in updatable:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return False
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(return_id)
    with get_db_context() as db:
        db.execute(f"UPDATE legal_returns SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
        return True


def submit_return(return_id, user_id):
    """Submit a return for review."""
    with get_db_context() as db:
        db.execute("""
            UPDATE legal_returns
            SET status = 'submitted', filed_by = ?, filed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, return_id))
        db.commit()
        return True


def approve_return(return_id, user_id):
    """Approve a return."""
    with get_db_context() as db:
        db.execute("""
            UPDATE legal_returns
            SET status = 'approved', approved_by = ?, approved_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, return_id))
        db.commit()
        return True


def reject_return(return_id, user_id, reason):
    """Reject a return."""
    with get_db_context() as db:
        db.execute("""
            UPDATE legal_returns
            SET status = 'rejected', filed_by = ?, filed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, return_id))
        db.execute("""
            INSERT INTO tax_review_comments (return_id, user_id, comment, is_system)
            VALUES (?, ?, ?, 1)
        """, (return_id, user_id, f"Return rejected: {reason}"))
        db.commit()
        return True


def get_next_return_number(return_type, company_id):
    """Generate next return number."""
    prefix_map = {
        'vat': 'VAT',
        'gst': 'GST',
        'sales_tax': 'STX',
        'withholding': 'WHT',
        'excise': 'EXC',
        'customs': 'CUS',
        'payroll': 'PAY',
        'property': 'PRO',
        'other': 'OTH'
    }
    prefix = prefix_map.get(return_type, 'RET')
    with get_db_context() as db:
        cursor = db.execute("""
            SELECT COUNT(*) as cnt FROM legal_returns
            WHERE return_type = ? AND company_id = ?
        """, (return_type, company_id))
        row = cursor.fetchone()
        count = row['cnt'] + 1 if row else 1
        return f"{prefix}-{count:05d}"


# ============================================================================
# RETURN LINES
# ============================================================================

def _create_return_lines():
    """Create return lines table."""
    if not table_exists('legal_return_lines'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE legal_return_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    return_id INTEGER NOT NULL,
                    line_number INTEGER,
                    box_code TEXT,
                    box_label TEXT,
                    box_label_ar TEXT,
                    box_label_fa TEXT,
                    line_type TEXT DEFAULT 'auto',
                    tax_code_id INTEGER,
                    tax_rate REAL,
                    base_amount REAL DEFAULT 0,
                    tax_amount REAL DEFAULT 0,
                    notes TEXT,
                    source_transaction TEXT,
                    source_transaction_id INTEGER,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (return_id) REFERENCES legal_returns(id),
                    FOREIGN KEY (tax_code_id) REFERENCES tax_codes(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_line_return ON legal_return_lines(return_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_line_box ON legal_return_lines(box_code)")
            db.commit()


def get_return_lines(return_id):
    """Get all lines for a return."""
    return get_all("""
        SELECT l.*, tc.code as tax_code, tc.name as tax_code_name
        FROM legal_return_lines l
        LEFT JOIN tax_codes tc ON l.tax_code_id = tc.id
        WHERE l.return_id = ? AND l.is_deleted = 0
        ORDER BY l.line_number
    """, (return_id,))


def create_return_line(data):
    """Create a new return line."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO legal_return_lines (
                return_id, line_number, box_code, box_label, box_label_ar, box_label_fa,
                line_type, tax_code_id, tax_rate, base_amount, tax_amount,
                notes, source_transaction, source_transaction_id, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('return_id'),
            data.get('line_number'),
            data.get('box_code'),
            data.get('box_label'),
            data.get('box_label_ar'),
            data.get('box_label_fa'),
            data.get('line_type', 'auto'),
            data.get('tax_code_id'),
            data.get('tax_rate'),
            data.get('base_amount', 0),
            data.get('tax_amount', 0),
            data.get('notes'),
            data.get('source_transaction'),
            data.get('source_transaction_id'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def update_return_line(line_id, data):
    """Update a return line."""
    fields = []
    values = []
    updatable = ['line_number', 'box_code', 'box_label', 'box_label_ar', 'box_label_fa',
                 'line_type', 'tax_code_id', 'tax_rate', 'base_amount', 'tax_amount',
                 'notes', 'source_transaction', 'source_transaction_id']
    for field in updatable:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return False
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(line_id)
    with get_db_context() as db:
        db.execute(f"UPDATE legal_return_lines SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
        return True


def delete_return_line(line_id):
    """Delete a return line."""
    with get_db_context() as db:
        db.execute("UPDATE legal_return_lines SET is_deleted = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (line_id,))
        db.commit()
        return True


# ============================================================================
# RETURN ADJUSTMENTS
# ============================================================================

def _create_return_adjustments():
    """Create return adjustments table."""
    if not table_exists('legal_return_adjustments'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE legal_return_adjustments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    return_id INTEGER NOT NULL,
                    line_id INTEGER,
                    adjustment_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    adjustment_amount REAL NOT NULL,
                    reason TEXT NOT NULL,
                    supporting_document TEXT,
                    reviewed_by INTEGER,
                    reviewed_at TIMESTAMP,
                    is_approved INTEGER DEFAULT 0,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (return_id) REFERENCES legal_returns(id),
                    FOREIGN KEY (line_id) REFERENCES legal_return_lines(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_adj_return ON legal_return_adjustments(return_id)")
            db.commit()


def get_return_adjustments(return_id):
    """Get all adjustments for a return."""
    return get_all("""
        SELECT a.*, u.username as reviewed_by_name
        FROM legal_return_adjustments a
        LEFT JOIN users u ON a.reviewed_by = u.id
        WHERE a.return_id = ? AND a.is_deleted = 0
        ORDER BY a.created_at
    """, (return_id,))


def create_return_adjustment(data):
    """Create a new return adjustment."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO legal_return_adjustments (
                return_id, line_id, adjustment_type, description,
                adjustment_amount, reason, supporting_document,
                company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('return_id'),
            data.get('line_id'),
            data.get('adjustment_type'),
            data.get('description'),
            data.get('adjustment_amount'),
            data.get('reason'),
            data.get('supporting_document'),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def approve_adjustment(adjustment_id, user_id):
    """Approve an adjustment."""
    with get_db_context() as db:
        db.execute("""
            UPDATE legal_return_adjustments
            SET is_approved = 1, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, adjustment_id))
        db.commit()
        return True


# ============================================================================
# RETURN APPROVALS
# ============================================================================

def _create_return_approvals():
    """Create return approvals table."""
    if not table_exists('legal_return_approvals'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE legal_return_approvals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    return_id INTEGER NOT NULL,
                    approver_id INTEGER NOT NULL,
                    approval_level INTEGER DEFAULT 1,
                    action TEXT NOT NULL,
                    comments TEXT,
                    is_current INTEGER DEFAULT 1,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (return_id) REFERENCES legal_returns(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_appr_return ON legal_return_approvals(return_id)")
            db.commit()


def get_return_approvals(return_id):
    """Get all approvals for a return."""
    return get_all("""
        SELECT a.*, u.username as approver_name
        FROM legal_return_approvals a
        LEFT JOIN users u ON a.approver_id = u.id
        WHERE a.return_id = ?
        ORDER BY a.created_at
    """, (return_id,))


def create_return_approval(data):
    """Create a new return approval record."""
    with get_db_context() as db:
        db.execute("UPDATE legal_return_approvals SET is_current = 0 WHERE return_id = ?", (data.get('return_id'),))
        cursor = db.execute("""
            INSERT INTO legal_return_approvals (
                return_id, approver_id, approval_level, action, comments, is_current, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('return_id'),
            data.get('approver_id'),
            data.get('approval_level', 1),
            data.get('action'),
            data.get('comments'),
            1,
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


# ============================================================================
# OBLIGATIONS
# ============================================================================

def _create_obligations():
    """Create legal obligations table."""
    if not table_exists('legal_obligations'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE legal_obligations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    obligation_number TEXT UNIQUE NOT NULL,
                    obligation_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    description_ar TEXT,
                    description_fa TEXT,
                    jurisdiction_id INTEGER,
                    authority_id INTEGER,
                    entity_id INTEGER,
                    filing_period_id INTEGER,
                    due_date DATE NOT NULL,
                    filing_frequency TEXT,
                    status TEXT DEFAULT 'pending',
                    priority TEXT DEFAULT 'normal',
                    risk_score INTEGER DEFAULT 0,
                    assigned_to INTEGER,
                    reminder_date DATE,
                    completion_date DATE,
                    notes TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (jurisdiction_id) REFERENCES tax_jurisdictions(id),
                    FOREIGN KEY (authority_id) REFERENCES tax_authorities(id),
                    FOREIGN KEY (entity_id) REFERENCES legal_entities(id),
                    FOREIGN KEY (filing_period_id) REFERENCES filing_periods(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_obligation_number ON legal_obligations(obligation_number)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_obligation_status ON legal_obligations(status)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_obligation_due ON legal_obligations(due_date)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_obligation_company ON legal_obligations(company_id)")
            db.commit()


def get_obligations(company_id=None, jurisdiction_id=None, status=None, authority_id=None):
    """Get all obligations."""
    sql = "SELECT * FROM legal_obligations WHERE is_deleted = 0"
    params = []
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    if jurisdiction_id:
        sql += " AND jurisdiction_id = ?"
        params.append(jurisdiction_id)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if authority_id:
        sql += " AND authority_id = ?"
        params.append(authority_id)
    sql += " ORDER BY due_date"
    return get_all(sql, params if params else None)


def get_obligations_due_soon(days=7, company_id=None):
    """Get obligations due within specified days."""
    sql = """
        SELECT * FROM legal_obligations
        WHERE is_deleted = 0 AND status IN ('pending', 'in_progress')
        AND due_date BETWEEN date('now') AND date('now', ? || ' days')
    """
    params = [days]
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    sql += " ORDER BY due_date"
    return get_all(sql, params)


def get_overdue_obligations(company_id=None):
    """Get overdue obligations."""
    sql = """
        SELECT * FROM legal_obligations
        WHERE is_deleted = 0 AND status IN ('pending', 'in_progress')
        AND due_date < date('now')
    """
    if company_id:
        sql += " AND company_id = ?"
    sql += " ORDER BY due_date"
    return get_all(sql, [company_id] if company_id else None)


def get_obligation_by_id(obligation_id):
    """Get a single obligation by ID."""
    return get_one("SELECT * FROM legal_obligations WHERE id = ? AND is_deleted = 0", (obligation_id,))


def create_obligation(data):
    """Create a new obligation."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO legal_obligations (
                obligation_number, obligation_type, description, description_ar, description_fa,
                jurisdiction_id, authority_id, entity_id, filing_period_id,
                due_date, filing_frequency, status, priority, risk_score,
                assigned_to, reminder_date, notes, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('obligation_number'),
            data.get('obligation_type'),
            data.get('description'),
            data.get('description_ar'),
            data.get('description_fa'),
            data.get('jurisdiction_id'),
            data.get('authority_id'),
            data.get('entity_id'),
            data.get('filing_period_id'),
            data.get('due_date'),
            data.get('filing_frequency'),
            data.get('status', 'pending'),
            data.get('priority', 'normal'),
            data.get('risk_score', 0),
            data.get('assigned_to'),
            data.get('reminder_date'),
            data.get('notes'),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def update_obligation(obligation_id, data):
    """Update an obligation."""
    fields = []
    values = []
    updatable = ['obligation_number', 'obligation_type', 'description', 'description_ar', 'description_fa',
                 'jurisdiction_id', 'authority_id', 'entity_id', 'filing_period_id',
                 'due_date', 'filing_frequency', 'status', 'priority', 'risk_score',
                 'assigned_to', 'reminder_date', 'completion_date', 'notes']
    for field in updatable:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return False
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(obligation_id)
    with get_db_context() as db:
        db.execute(f"UPDATE legal_obligations SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
        return True


def complete_obligation(obligation_id):
    """Mark an obligation as completed."""
    with get_db_context() as db:
        db.execute("""
            UPDATE legal_obligations
            SET status = 'completed', completion_date = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (obligation_id,))
        db.commit()
        return True


def get_next_obligation_number(obligation_type, company_id):
    """Generate next obligation number."""
    prefix_map = {
        'vat_return': 'OB-VAT',
        'gst_return': 'OB-GST',
        'tax_filing': 'OB-TAX',
        'audit': 'OB-AUD',
        'report': 'OB-REP',
        'payment': 'OB-PAY',
        'other': 'OB-OTH'
    }
    prefix = prefix_map.get(obligation_type, 'OB-OTH')
    with get_db_context() as db:
        cursor = db.execute("SELECT COUNT(*) as cnt FROM legal_obligations WHERE company_id = ?", (company_id,))
        row = cursor.fetchone()
        count = row['cnt'] + 1 if row else 1
        return f"{prefix}-{count:05d}"


# ============================================================================
# COMPLIANCE TASKS
# ============================================================================

def _create_compliance_tasks():
    """Create compliance tasks table."""
    if not table_exists('legal_compliance_tasks'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE legal_compliance_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_number TEXT UNIQUE NOT NULL,
                    task_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    obligation_id INTEGER,
                    return_id INTEGER,
                    priority TEXT DEFAULT 'normal',
                    status TEXT DEFAULT 'pending',
                    due_date DATE,
                    assigned_to INTEGER,
                    completed_by INTEGER,
                    completed_at TIMESTAMP,
                    notes TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (obligation_id) REFERENCES legal_obligations(id),
                    FOREIGN KEY (return_id) REFERENCES legal_returns(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_task_number ON legal_compliance_tasks(task_number)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_task_status ON legal_compliance_tasks(status)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_task_company ON legal_compliance_tasks(company_id)")
            db.commit()


def get_compliance_tasks(company_id=None, status=None, assigned_to=None):
    """Get all compliance tasks."""
    sql = "SELECT * FROM legal_compliance_tasks WHERE is_deleted = 0"
    params = []
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if assigned_to:
        sql += " AND assigned_to = ?"
        params.append(assigned_to)
    sql += " ORDER BY due_date"
    return get_all(sql, params if params else None)


def get_compliance_task_by_id(task_id):
    """Get a single compliance task by ID."""
    return get_one("SELECT * FROM legal_compliance_tasks WHERE id = ? AND is_deleted = 0", (task_id,))


def create_compliance_task(data):
    """Create a new compliance task."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO legal_compliance_tasks (
                task_number, task_type, title, description, obligation_id, return_id,
                priority, status, due_date, assigned_to, notes, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('task_number'),
            data.get('task_type'),
            data.get('title'),
            data.get('description'),
            data.get('obligation_id'),
            data.get('return_id'),
            data.get('priority', 'normal'),
            data.get('status', 'pending'),
            data.get('due_date'),
            data.get('assigned_to'),
            data.get('notes'),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def update_compliance_task(task_id, data):
    """Update a compliance task."""
    fields = []
    values = []
    updatable = ['task_type', 'title', 'description', 'obligation_id', 'return_id',
                 'priority', 'status', 'due_date', 'assigned_to', 'completed_by', 'completed_at', 'notes']
    for field in updatable:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return False
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(task_id)
    with get_db_context() as db:
        db.execute(f"UPDATE legal_compliance_tasks SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
        return True


def complete_compliance_task(task_id, user_id):
    """Complete a compliance task."""
    with get_db_context() as db:
        db.execute("""
            UPDATE legal_compliance_tasks
            SET status = 'completed', completed_by = ?, completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, task_id))
        db.commit()
        return True


def get_next_task_number(task_type, company_id):
    """Generate next task number."""
    prefix_map = {
        'review': 'TASK-REV',
        'filing': 'TASK-FIL',
        'payment': 'TASK-PAY',
        'reconciliation': 'TASK-REC',
        'other': 'TASK-OTH'
    }
    prefix = prefix_map.get(task_type, 'TASK-OTH')
    with get_db_context() as db:
        cursor = db.execute("SELECT COUNT(*) as cnt FROM legal_compliance_tasks WHERE company_id = ?", (company_id,))
        row = cursor.fetchone()
        count = row['cnt'] + 1 if row else 1
        return f"{prefix}-{count:05d}"


# ============================================================================
# TAX REVIEW ITEMS
# ============================================================================

def _create_tax_review_items():
    """Create tax review items table."""
    if not table_exists('tax_review_items'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE tax_review_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    review_number TEXT UNIQUE NOT NULL,
                    item_type TEXT NOT NULL,
                    source_transaction TEXT NOT NULL,
                    source_transaction_id INTEGER,
                    source_document TEXT,
                    source_document_id INTEGER,
                    tax_code_id INTEGER,
                    tax_rate REAL,
                    transaction_date DATE,
                    transaction_amount REAL,
                    tax_amount REAL,
                    exception_type TEXT,
                    exception_reason TEXT,
                    severity TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'pending',
                    assigned_to INTEGER,
                    reviewed_by INTEGER,
                    reviewed_at TIMESTAMP,
                    resolution_notes TEXT,
                    override_reason TEXT,
                    is_manual_override INTEGER DEFAULT 0,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (tax_code_id) REFERENCES tax_codes(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_review_number ON tax_review_items(review_number)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_review_status ON tax_review_items(status)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_review_source ON tax_review_items(source_transaction, source_transaction_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_review_company ON tax_review_items(company_id)")
            db.commit()


def get_tax_review_items(company_id=None, status=None, severity=None, item_type=None):
    """Get all tax review items."""
    sql = "SELECT * FROM tax_review_items WHERE is_deleted = 0"
    params = []
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if severity:
        sql += " AND severity = ?"
        params.append(severity)
    if item_type:
        sql += " AND item_type = ?"
        params.append(item_type)
    sql += " ORDER BY created_at DESC"
    return get_all(sql, params if params else None)


def get_tax_review_item_by_id(item_id):
    """Get a single tax review item by ID."""
    return get_one("SELECT * FROM tax_review_items WHERE id = ? AND is_deleted = 0", (item_id,))


def create_tax_review_item(data):
    """Create a new tax review item."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO tax_review_items (
                review_number, item_type, source_transaction, source_transaction_id,
                source_document, source_document_id, tax_code_id, tax_rate,
                transaction_date, transaction_amount, tax_amount, exception_type,
                exception_reason, severity, status, assigned_to, is_manual_override,
                company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('review_number'),
            data.get('item_type'),
            data.get('source_transaction'),
            data.get('source_transaction_id'),
            data.get('source_document'),
            data.get('source_document_id'),
            data.get('tax_code_id'),
            data.get('tax_rate'),
            data.get('transaction_date'),
            data.get('transaction_amount'),
            data.get('tax_amount'),
            data.get('exception_type'),
            data.get('exception_reason'),
            data.get('severity', 'medium'),
            data.get('status', 'pending'),
            data.get('assigned_to'),
            data.get('is_manual_override', 0),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def update_tax_review_item(item_id, data):
    """Update a tax review item."""
    fields = []
    values = []
    updatable = ['item_type', 'source_transaction', 'source_transaction_id', 'source_document',
                 'source_document_id', 'tax_code_id', 'tax_rate', 'transaction_date',
                 'transaction_amount', 'tax_amount', 'exception_type', 'exception_reason',
                 'severity', 'status', 'assigned_to', 'reviewed_by', 'reviewed_at',
                 'resolution_notes', 'override_reason', 'is_manual_override']
    for field in updatable:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return False
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(item_id)
    with get_db_context() as db:
        db.execute(f"UPDATE tax_review_items SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
        return True


def approve_tax_review_item(item_id, user_id, notes=None):
    """Approve a tax review item."""
    with get_db_context() as db:
        db.execute("""
            UPDATE tax_review_items
            SET status = 'approved', reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP,
                resolution_notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, notes, item_id))
        db.commit()
        return True


def reject_tax_review_item(item_id, user_id, reason):
    """Reject a tax review item."""
    with get_db_context() as db:
        db.execute("""
            UPDATE tax_review_items
            SET status = 'rejected', reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP,
                resolution_notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, reason, item_id))
        db.commit()
        return True


def get_next_review_number(item_type, company_id):
    """Generate next review number."""
    prefix_map = {
        'invoice': 'REV-INV',
        'bill': 'REV-BIL',
        'credit_note': 'REV-CRN',
        'debit_note': 'REV-DBN',
        'journal': 'REV-JRN',
        'payment': 'REV-PAY',
        'other': 'REV-OTH'
    }
    prefix = prefix_map.get(item_type, 'REV-OTH')
    with get_db_context() as db:
        cursor = db.execute("SELECT COUNT(*) as cnt FROM tax_review_items WHERE company_id = ?", (company_id,))
        row = cursor.fetchone()
        count = row['cnt'] + 1 if row else 1
        return f"{prefix}-{count:05d}"


# ============================================================================
# TAX REVIEW COMMENTS
# ============================================================================

def _create_tax_review_comments():
    """Create tax review comments table."""
    if not table_exists('tax_review_comments'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE tax_review_comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    return_id INTEGER,
                    review_item_id INTEGER,
                    user_id INTEGER NOT NULL,
                    comment TEXT NOT NULL,
                    is_system INTEGER DEFAULT 0,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (return_id) REFERENCES legal_returns(id),
                    FOREIGN KEY (review_item_id) REFERENCES tax_review_items(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_comment_return ON tax_review_comments(return_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_comment_review ON tax_review_comments(review_item_id)")
            db.commit()


def get_return_comments(return_id):
    """Get all comments for a return."""
    return get_all("""
        SELECT c.*, u.username as user_name
        FROM tax_review_comments c
        LEFT JOIN users u ON c.user_id = u.id
        WHERE c.return_id = ?
        ORDER BY c.created_at
    """, (return_id,))


def get_review_item_comments(review_item_id):
    """Get all comments for a review item."""
    return get_all("""
        SELECT c.*, u.username as user_name
        FROM tax_review_comments c
        LEFT JOIN users u ON c.user_id = u.id
        WHERE c.review_item_id = ?
        ORDER BY c.created_at
    """, (review_item_id,))


def create_tax_comment(data):
    """Create a new tax comment."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO tax_review_comments (
                return_id, review_item_id, user_id, comment, is_system, company_id
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.get('return_id'),
            data.get('review_item_id'),
            data.get('user_id'),
            data.get('comment'),
            data.get('is_system', 0),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


# ============================================================================
# RECONCILIATIONS
# ============================================================================

def _create_reconciliations():
    """Create legal reconciliations table."""
    if not table_exists('legal_reconciliations'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE legal_reconciliations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reconciliation_number TEXT UNIQUE NOT NULL,
                    reconciliation_type TEXT NOT NULL,
                    period_id INTEGER,
                    jurisdiction_id INTEGER,
                    entity_id INTEGER,
                    status TEXT DEFAULT 'draft',
                    total_source_amount REAL DEFAULT 0,
                    total_target_amount REAL DEFAULT 0,
                    variance_amount REAL DEFAULT 0,
                    matched_count INTEGER DEFAULT 0,
                    unmatched_count INTEGER DEFAULT 0,
                    reviewed_by INTEGER,
                    reviewed_at TIMESTAMP,
                    notes TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (period_id) REFERENCES filing_periods(id),
                    FOREIGN KEY (jurisdiction_id) REFERENCES tax_jurisdictions(id),
                    FOREIGN KEY (entity_id) REFERENCES legal_entities(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_recon_number ON legal_reconciliations(reconciliation_number)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_recon_status ON legal_reconciliations(status)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_recon_company ON legal_reconciliations(company_id)")
            db.commit()


def get_reconciliations(company_id=None, status=None, reconciliation_type=None):
    """Get all reconciliations."""
    sql = "SELECT * FROM legal_reconciliations WHERE is_deleted = 0"
    params = []
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if reconciliation_type:
        sql += " AND reconciliation_type = ?"
        params.append(reconciliation_type)
    sql += " ORDER BY created_at DESC"
    return get_all(sql, params if params else None)


def get_reconciliation_by_id(recon_id):
    """Get a single reconciliation by ID."""
    return get_one("SELECT * FROM legal_reconciliations WHERE id = ? AND is_deleted = 0", (recon_id,))


def create_reconciliation(data):
    """Create a new reconciliation."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO legal_reconciliations (
                reconciliation_number, reconciliation_type, period_id, jurisdiction_id,
                entity_id, status, total_source_amount, total_target_amount,
                variance_amount, matched_count, unmatched_count, notes,
                company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('reconciliation_number'),
            data.get('reconciliation_type'),
            data.get('period_id'),
            data.get('jurisdiction_id'),
            data.get('entity_id'),
            data.get('status', 'draft'),
            data.get('total_source_amount', 0),
            data.get('total_target_amount', 0),
            data.get('variance_amount', 0),
            data.get('matched_count', 0),
            data.get('unmatched_count', 0),
            data.get('notes'),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def update_reconciliation(recon_id, data):
    """Update a reconciliation."""
    fields = []
    values = []
    updatable = ['reconciliation_type', 'period_id', 'jurisdiction_id', 'entity_id',
                 'status', 'total_source_amount', 'total_target_amount', 'variance_amount',
                 'matched_count', 'unmatched_count', 'reviewed_by', 'reviewed_at', 'notes']
    for field in updatable:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return False
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(recon_id)
    with get_db_context() as db:
        db.execute(f"UPDATE legal_reconciliations SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
        return True


def get_next_reconciliation_number(reconciliation_type, company_id):
    """Generate next reconciliation number."""
    prefix_map = {
        'gl_tax': 'REC-GLT',
        'ar_tax': 'REC-ART',
        'ap_tax': 'REC-APT',
        'return_payment': 'REC-RPM',
        'other': 'REC-OTH'
    }
    prefix = prefix_map.get(reconciliation_type, 'REC-OTH')
    with get_db_context() as db:
        cursor = db.execute("SELECT COUNT(*) as cnt FROM legal_reconciliations WHERE company_id = ?", (company_id,))
        row = cursor.fetchone()
        count = row['cnt'] + 1 if row else 1
        return f"{prefix}-{count:05d}"


# ============================================================================
# RECONCILIATION LINES
# ============================================================================

def _create_reconciliation_lines():
    """Create reconciliation lines table."""
    if not table_exists('legal_reconciliation_lines'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE legal_reconciliation_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reconciliation_id INTEGER NOT NULL,
                    line_type TEXT NOT NULL,
                    source_line_id INTEGER,
                    target_line_id INTEGER,
                    match_status TEXT DEFAULT 'unmatched',
                    source_amount REAL,
                    target_amount REAL,
                    variance_amount REAL,
                    match_explanation TEXT,
                    matched_by INTEGER,
                    matched_at TIMESTAMP,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (reconciliation_id) REFERENCES legal_reconciliations(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_reconline_recon ON legal_reconciliation_lines(reconciliation_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_reconline_status ON legal_reconciliation_lines(match_status)")
            db.commit()


def get_reconciliation_lines(reconciliation_id):
    """Get all lines for a reconciliation."""
    return get_all("""
        SELECT l.*, u.username as matched_by_name
        FROM legal_reconciliation_lines l
        LEFT JOIN users u ON l.matched_by = u.id
        WHERE l.reconciliation_id = ? AND l.is_deleted = 0
        ORDER BY l.line_type, l.id
    """, (reconciliation_id,))


def create_reconciliation_line(data):
    """Create a new reconciliation line."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO legal_reconciliation_lines (
                reconciliation_id, line_type, source_line_id, target_line_id,
                match_status, source_amount, target_amount, variance_amount,
                match_explanation, matched_by, matched_at, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('reconciliation_id'),
            data.get('line_type'),
            data.get('source_line_id'),
            data.get('target_line_id'),
            data.get('match_status', 'unmatched'),
            data.get('source_amount'),
            data.get('target_amount'),
            data.get('variance_amount'),
            data.get('match_explanation'),
            data.get('matched_by'),
            data.get('matched_at'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def match_reconciliation_line(line_id, user_id, explanation=None):
    """Match a reconciliation line."""
    with get_db_context() as db:
        db.execute("""
            UPDATE legal_reconciliation_lines
            SET match_status = 'matched', matched_by = ?, matched_at = CURRENT_TIMESTAMP,
                match_explanation = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, explanation, line_id))
        db.commit()
        return True


def unmatch_reconciliation_line(line_id):
    """Unmatch a reconciliation line."""
    with get_db_context() as db:
        db.execute("""
            UPDATE legal_reconciliation_lines
            SET match_status = 'unmatched', matched_by = NULL, matched_at = NULL,
                match_explanation = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (line_id,))
        db.commit()
        return True


# ============================================================================
# NOTICES
# ============================================================================

def _create_notices():
    """Create legal notices table."""
    if not table_exists('legal_notices'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE legal_notices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    notice_number TEXT UNIQUE NOT NULL,
                    notice_type TEXT NOT NULL,
                    authority_id INTEGER,
                    entity_id INTEGER,
                    subject TEXT NOT NULL,
                    content TEXT,
                    severity TEXT DEFAULT 'medium',
                    issue_date DATE,
                    due_date DATE,
                    response_deadline DATE,
                    status TEXT DEFAULT 'received',
                    assigned_to INTEGER,
                    resolved_by INTEGER,
                    resolved_at TIMESTAMP,
                    resolution_notes TEXT,
                    penalty_id INTEGER,
                    dispute_id INTEGER,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (authority_id) REFERENCES tax_authorities(id),
                    FOREIGN KEY (entity_id) REFERENCES legal_entities(id),
                    FOREIGN KEY (penalty_id) REFERENCES legal_penalties(id),
                    FOREIGN KEY (dispute_id) REFERENCES legal_disputes(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_notice_number ON legal_notices(notice_number)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_notice_status ON legal_notices(status)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_notice_company ON legal_notices(company_id)")
            db.commit()


def get_notices(company_id=None, status=None, severity=None, authority_id=None):
    """Get all notices."""
    sql = "SELECT * FROM legal_notices WHERE is_deleted = 0"
    params = []
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if severity:
        sql += " AND severity = ?"
        params.append(severity)
    if authority_id:
        sql += " AND authority_id = ?"
        params.append(authority_id)
    sql += " ORDER BY issue_date DESC"
    return get_all(sql, params if params else None)


def get_notice_by_id(notice_id):
    """Get a single notice by ID."""
    return get_one("SELECT * FROM legal_notices WHERE id = ? AND is_deleted = 0", (notice_id,))


def create_notice(data):
    """Create a new notice."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO legal_notices (
                notice_number, notice_type, authority_id, entity_id, subject,
                content, severity, issue_date, due_date, response_deadline,
                status, assigned_to, penalty_id, dispute_id, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('notice_number'),
            data.get('notice_type'),
            data.get('authority_id'),
            data.get('entity_id'),
            data.get('subject'),
            data.get('content'),
            data.get('severity', 'medium'),
            data.get('issue_date'),
            data.get('due_date'),
            data.get('response_deadline'),
            data.get('status', 'received'),
            data.get('assigned_to'),
            data.get('penalty_id'),
            data.get('dispute_id'),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def update_notice(notice_id, data):
    """Update a notice."""
    fields = []
    values = []
    updatable = ['notice_type', 'authority_id', 'entity_id', 'subject', 'content',
                 'severity', 'issue_date', 'due_date', 'response_deadline', 'status',
                 'assigned_to', 'resolved_by', 'resolved_at', 'resolution_notes']
    for field in updatable:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return False
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(notice_id)
    with get_db_context() as db:
        db.execute(f"UPDATE legal_notices SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
        return True


def resolve_notice(notice_id, user_id, notes):
    """Resolve a notice."""
    with get_db_context() as db:
        db.execute("""
            UPDATE legal_notices
            SET status = 'resolved', resolved_by = ?, resolved_at = CURRENT_TIMESTAMP,
                resolution_notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, notes, notice_id))
        db.commit()
        return True


def get_next_notice_number(notice_type, company_id):
    """Generate next notice number."""
    prefix_map = {
        'assessment': 'NOT-ASS',
        'inquiry': 'NOT-INQ',
        'audit': 'NOT-AUD',
        'demand': 'NOT-DEM',
        'other': 'NOT-OTH'
    }
    prefix = prefix_map.get(notice_type, 'NOT-OTH')
    with get_db_context() as db:
        cursor = db.execute("SELECT COUNT(*) as cnt FROM legal_notices WHERE company_id = ?", (company_id,))
        row = cursor.fetchone()
        count = row['cnt'] + 1 if row else 1
        return f"{prefix}-{count:05d}"


# ============================================================================
# PENALTIES
# ============================================================================

def _create_penalties():
    """Create legal penalties table."""
    if not table_exists('legal_penalties'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE legal_penalties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    penalty_number TEXT UNIQUE NOT NULL,
                    penalty_type TEXT NOT NULL,
                    notice_id INTEGER,
                    authority_id INTEGER,
                    entity_id INTEGER,
                    description TEXT NOT NULL,
                    amount REAL DEFAULT 0,
                    currency TEXT DEFAULT 'USD',
                    penalty_date DATE,
                    due_date DATE,
                    status TEXT DEFAULT 'pending',
                    paid_amount REAL DEFAULT 0,
                    paid_date DATE,
                    waiver_requested INTEGER DEFAULT 0,
                    waiver_reason TEXT,
                    dispute_id INTEGER,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (notice_id) REFERENCES legal_notices(id),
                    FOREIGN KEY (authority_id) REFERENCES tax_authorities(id),
                    FOREIGN KEY (entity_id) REFERENCES legal_entities(id),
                    FOREIGN KEY (dispute_id) REFERENCES legal_disputes(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_penalty_number ON legal_penalties(penalty_number)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_penalty_status ON legal_penalties(status)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_penalty_company ON legal_penalties(company_id)")
            db.commit()


def get_penalties(company_id=None, status=None, authority_id=None):
    """Get all penalties."""
    sql = "SELECT * FROM legal_penalties WHERE is_deleted = 0"
    params = []
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if authority_id:
        sql += " AND authority_id = ?"
        params.append(authority_id)
    sql += " ORDER BY penalty_date DESC"
    return get_all(sql, params if params else None)


def get_penalty_by_id(penalty_id):
    """Get a single penalty by ID."""
    return get_one("SELECT * FROM legal_penalties WHERE id = ? AND is_deleted = 0", (penalty_id,))


def create_penalty(data):
    """Create a new penalty."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO legal_penalties (
                penalty_number, penalty_type, notice_id, authority_id, entity_id,
                description, amount, currency, penalty_date, due_date, status,
                paid_amount, waiver_requested, waiver_reason, dispute_id,
                company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('penalty_number'),
            data.get('penalty_type'),
            data.get('notice_id'),
            data.get('authority_id'),
            data.get('entity_id'),
            data.get('description'),
            data.get('amount', 0),
            data.get('currency', 'USD'),
            data.get('penalty_date'),
            data.get('due_date'),
            data.get('status', 'pending'),
            data.get('paid_amount', 0),
            data.get('waiver_requested', 0),
            data.get('waiver_reason'),
            data.get('dispute_id'),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def update_penalty(penalty_id, data):
    """Update a penalty."""
    fields = []
    values = []
    updatable = ['penalty_type', 'notice_id', 'authority_id', 'entity_id', 'description',
                 'amount', 'currency', 'penalty_date', 'due_date', 'status',
                 'paid_amount', 'paid_date', 'waiver_requested', 'waiver_reason', 'dispute_id']
    for field in updatable:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return False
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(penalty_id)
    with get_db_context() as db:
        db.execute(f"UPDATE legal_penalties SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
        return True


def pay_penalty(penalty_id, amount, paid_date=None):
    """Record penalty payment."""
    with get_db_context() as db:
        db.execute("""
            UPDATE legal_penalties
            SET paid_amount = paid_amount + ?, paid_date = COALESCE(?, paid_date),
                status = CASE WHEN paid_amount + ? >= amount THEN 'paid' ELSE 'partial' END,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (amount, paid_date, amount, penalty_id))
        db.commit()
        return True


def get_next_penalty_number(penalty_type, company_id):
    """Generate next penalty number."""
    prefix_map = {
        'late_filing': 'PEN-LTF',
        'late_payment': 'PEN-LTP',
        'underpayment': 'PEN-UND',
        'assessment': 'PEN-ASS',
        'other': 'PEN-OTH'
    }
    prefix = prefix_map.get(penalty_type, 'PEN-OTH')
    with get_db_context() as db:
        cursor = db.execute("SELECT COUNT(*) as cnt FROM legal_penalties WHERE company_id = ?", (company_id,))
        row = cursor.fetchone()
        count = row['cnt'] + 1 if row else 1
        return f"{prefix}-{count:05d}"


# ============================================================================
# DISPUTES
# ============================================================================

def _create_disputes():
    """Create legal disputes table."""
    if not table_exists('legal_disputes'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE legal_disputes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dispute_number TEXT UNIQUE NOT NULL,
                    dispute_type TEXT NOT NULL,
                    authority_id INTEGER,
                    entity_id INTEGER,
                    notice_id INTEGER,
                    penalty_id INTEGER,
                    subject TEXT NOT NULL,
                    description TEXT,
                    amount REAL DEFAULT 0,
                    currency TEXT DEFAULT 'USD',
                    filing_date DATE,
                    hearing_date DATE,
                    decision_date DATE,
                    status TEXT DEFAULT 'open',
                    decision TEXT,
                    appeal_filed INTEGER DEFAULT 0,
                    appeal_date DATE,
                    appeal_decision TEXT,
                    resolved_by INTEGER,
                    resolved_at TIMESTAMP,
                    resolution_notes TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (authority_id) REFERENCES tax_authorities(id),
                    FOREIGN KEY (entity_id) REFERENCES legal_entities(id),
                    FOREIGN KEY (notice_id) REFERENCES legal_notices(id),
                    FOREIGN KEY (penalty_id) REFERENCES legal_penalties(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_dispute_number ON legal_disputes(dispute_number)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_dispute_status ON legal_disputes(status)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_dispute_company ON legal_disputes(company_id)")
            db.commit()


def get_disputes(company_id=None, status=None, dispute_type=None):
    """Get all disputes."""
    sql = "SELECT * FROM legal_disputes WHERE is_deleted = 0"
    params = []
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if dispute_type:
        sql += " AND dispute_type = ?"
        params.append(dispute_type)
    sql += " ORDER BY created_at DESC"
    return get_all(sql, params if params else None)


def get_dispute_by_id(dispute_id):
    """Get a single dispute by ID."""
    return get_one("SELECT * FROM legal_disputes WHERE id = ? AND is_deleted = 0", (dispute_id,))


def create_dispute(data):
    """Create a new dispute."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO legal_disputes (
                dispute_number, dispute_type, authority_id, entity_id, notice_id,
                penalty_id, subject, description, amount, currency, filing_date,
                hearing_date, decision_date, status, decision, appeal_filed,
                appeal_date, appeal_decision, resolved_by, resolved_at,
                resolution_notes, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('dispute_number'),
            data.get('dispute_type'),
            data.get('authority_id'),
            data.get('entity_id'),
            data.get('notice_id'),
            data.get('penalty_id'),
            data.get('subject'),
            data.get('description'),
            data.get('amount', 0),
            data.get('currency', 'USD'),
            data.get('filing_date'),
            data.get('hearing_date'),
            data.get('decision_date'),
            data.get('status', 'open'),
            data.get('decision'),
            data.get('appeal_filed', 0),
            data.get('appeal_date'),
            data.get('appeal_decision'),
            data.get('resolved_by'),
            data.get('resolved_at'),
            data.get('resolution_notes'),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def update_dispute(dispute_id, data):
    """Update a dispute."""
    fields = []
    values = []
    updatable = ['dispute_type', 'authority_id', 'entity_id', 'notice_id', 'penalty_id',
                 'subject', 'description', 'amount', 'currency', 'filing_date', 'hearing_date',
                 'decision_date', 'status', 'decision', 'appeal_filed', 'appeal_date',
                 'appeal_decision', 'resolved_by', 'resolved_at', 'resolution_notes']
    for field in updatable:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return False
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(dispute_id)
    with get_db_context() as db:
        db.execute(f"UPDATE legal_disputes SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
        return True


def resolve_dispute(dispute_id, user_id, decision, notes):
    """Resolve a dispute."""
    with get_db_context() as db:
        db.execute("""
            UPDATE legal_disputes
            SET status = 'resolved', decision = ?, resolved_by = ?,
                resolved_at = CURRENT_TIMESTAMP, resolution_notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (decision, user_id, notes, dispute_id))
        db.commit()
        return True


def get_next_dispute_number(dispute_type, company_id):
    """Generate next dispute number."""
    prefix_map = {
        'tax_assessment': 'DSP-TAX',
        'penalty': 'DSP-PEN',
        'refund': 'DSP-REF',
        'registration': 'DSP-REG',
        'other': 'DSP-OTH'
    }
    prefix = prefix_map.get(dispute_type, 'DSP-OTH')
    with get_db_context() as db:
        cursor = db.execute("SELECT COUNT(*) as cnt FROM legal_disputes WHERE company_id = ?", (company_id,))
        row = cursor.fetchone()
        count = row['cnt'] + 1 if row else 1
        return f"{prefix}-{count:05d}"


# ============================================================================
# FILING SUBMISSIONS
# ============================================================================

def _create_filing_submissions():
    """Create filing submissions table."""
    if not table_exists('legal_filing_submissions'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE legal_filing_submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    submission_number TEXT UNIQUE NOT NULL,
                    return_id INTEGER,
                    obligation_id INTEGER,
                    filing_type TEXT NOT NULL,
                    filing_method TEXT,
                    filing_date DATE,
                    acknowledgment_number TEXT,
                    acknowledgment_date DATE,
                    status TEXT DEFAULT 'submitted',
                    submitted_by INTEGER,
                    reviewed_by INTEGER,
                    reviewed_at TIMESTAMP,
                    rejection_reason TEXT,
                    attachment_path TEXT,
                    notes TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (return_id) REFERENCES legal_returns(id),
                    FOREIGN KEY (obligation_id) REFERENCES legal_obligations(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_submission_number ON legal_filing_submissions(submission_number)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_submission_return ON legal_filing_submissions(return_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_submission_status ON legal_filing_submissions(status)")
            db.commit()


def get_filing_submissions(return_id=None, company_id=None, status=None):
    """Get all filing submissions."""
    sql = "SELECT * FROM legal_filing_submissions WHERE is_deleted = 0"
    params = []
    if return_id:
        sql += " AND return_id = ?"
        params.append(return_id)
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY filing_date DESC"
    return get_all(sql, params if params else None)


def get_filing_submission_by_id(submission_id):
    """Get a single filing submission by ID."""
    return get_one("SELECT * FROM legal_filing_submissions WHERE id = ? AND is_deleted = 0", (submission_id,))


def create_filing_submission(data):
    """Create a new filing submission."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO legal_filing_submissions (
                submission_number, return_id, obligation_id, filing_type,
                filing_method, filing_date, acknowledgment_number, acknowledgment_date,
                status, submitted_by, reviewed_by, reviewed_at, rejection_reason,
                attachment_path, notes, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('submission_number'),
            data.get('return_id'),
            data.get('obligation_id'),
            data.get('filing_type'),
            data.get('filing_method'),
            data.get('filing_date'),
            data.get('acknowledgment_number'),
            data.get('acknowledgment_date'),
            data.get('status', 'submitted'),
            data.get('submitted_by'),
            data.get('reviewed_by'),
            data.get('reviewed_at'),
            data.get('rejection_reason'),
            data.get('attachment_path'),
            data.get('notes'),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def update_filing_submission(submission_id, data):
    """Update a filing submission."""
    fields = []
    values = []
    updatable = ['return_id', 'obligation_id', 'filing_type', 'filing_method', 'filing_date',
                 'acknowledgment_number', 'acknowledgment_date', 'status', 'submitted_by',
                 'reviewed_by', 'reviewed_at', 'rejection_reason', 'attachment_path', 'notes']
    for field in updatable:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return False
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(submission_id)
    with get_db_context() as db:
        db.execute(f"UPDATE legal_filing_submissions SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
        return True


def get_next_submission_number(filing_type, company_id):
    """Generate next submission number."""
    prefix_map = {
        'vat_return': 'SUB-VAT',
        'gst_return': 'SUB-GST',
        'tax_return': 'SUB-TAX',
        'amendment': 'SUB-AMN',
        'other': 'SUB-OTH'
    }
    prefix = prefix_map.get(filing_type, 'SUB-OTH')
    with get_db_context() as db:
        cursor = db.execute("SELECT COUNT(*) as cnt FROM legal_filing_submissions WHERE company_id = ?", (company_id,))
        row = cursor.fetchone()
        count = row['cnt'] + 1 if row else 1
        return f"{prefix}-{count:05d}"


# ============================================================================
# FILING PAYMENTS
# ============================================================================

def _create_filing_payments():
    """Create filing payments table."""
    if not table_exists('legal_filing_payments'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE legal_filing_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payment_number TEXT UNIQUE NOT NULL,
                    return_id INTEGER,
                    submission_id INTEGER,
                    payment_type TEXT NOT NULL,
                    payment_method TEXT,
                    payment_date DATE,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    reference_number TEXT,
                    bank_name TEXT,
                    attachment_path TEXT,
                    status TEXT DEFAULT 'pending',
                    confirmed_by INTEGER,
                    confirmed_at TIMESTAMP,
                    notes TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (return_id) REFERENCES legal_returns(id),
                    FOREIGN KEY (submission_id) REFERENCES legal_filing_submissions(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_payment_number ON legal_filing_payments(payment_number)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_payment_return ON legal_filing_payments(return_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_payment_status ON legal_filing_payments(status)")
            db.commit()


def get_filing_payments(return_id=None, company_id=None, status=None):
    """Get all filing payments."""
    sql = "SELECT * FROM legal_filing_payments WHERE is_deleted = 0"
    params = []
    if return_id:
        sql += " AND return_id = ?"
        params.append(return_id)
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY payment_date DESC"
    return get_all(sql, params if params else None)


def get_filing_payment_by_id(payment_id):
    """Get a single filing payment by ID."""
    return get_one("SELECT * FROM legal_filing_payments WHERE id = ? AND is_deleted = 0", (payment_id,))


def create_filing_payment(data):
    """Create a new filing payment."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO legal_filing_payments (
                payment_number, return_id, submission_id, payment_type,
                payment_method, payment_date, amount, currency, reference_number,
                bank_name, attachment_path, status, confirmed_by, confirmed_at,
                notes, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('payment_number'),
            data.get('return_id'),
            data.get('submission_id'),
            data.get('payment_type'),
            data.get('payment_method'),
            data.get('payment_date'),
            data.get('amount'),
            data.get('currency', 'USD'),
            data.get('reference_number'),
            data.get('bank_name'),
            data.get('attachment_path'),
            data.get('status', 'pending'),
            data.get('confirmed_by'),
            data.get('confirmed_at'),
            data.get('notes'),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def update_filing_payment(payment_id, data):
    """Update a filing payment."""
    fields = []
    values = []
    updatable = ['return_id', 'submission_id', 'payment_type', 'payment_method', 'payment_date',
                 'amount', 'currency', 'reference_number', 'bank_name', 'attachment_path',
                 'status', 'confirmed_by', 'confirmed_at', 'notes']
    for field in updatable:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return False
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(payment_id)
    with get_db_context() as db:
        db.execute(f"UPDATE legal_filing_payments SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
        return True


def confirm_filing_payment(payment_id, user_id):
    """Confirm a filing payment."""
    with get_db_context() as db:
        db.execute("""
            UPDATE legal_filing_payments
            SET status = 'confirmed', confirmed_by = ?, confirmed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, payment_id))
        db.commit()
        return True


def get_next_payment_number(payment_type, company_id):
    """Generate next payment number."""
    prefix_map = {
        'tax_payment': 'PAY-TAX',
        'penalty_payment': 'PAY-PEN',
        'refund': 'PAY-REF',
        'other': 'PAY-OTH'
    }
    prefix = prefix_map.get(payment_type, 'PAY-OTH')
    with get_db_context() as db:
        cursor = db.execute("SELECT COUNT(*) as cnt FROM legal_filing_payments WHERE company_id = ?", (company_id,))
        row = cursor.fetchone()
        count = row['cnt'] + 1 if row else 1
        return f"{prefix}-{count:05d}"


# ============================================================================
# AUDIT PACKS
# ============================================================================

def _create_audit_packs():
    """Create audit packs table."""
    if not table_exists('legal_audit_packs'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE legal_audit_packs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pack_number TEXT UNIQUE NOT NULL,
                    pack_name TEXT NOT NULL,
                    pack_type TEXT NOT NULL,
                    period_id INTEGER,
                    jurisdiction_id INTEGER,
                    entity_id INTEGER,
                    included_schedules TEXT,
                    included_documents TEXT,
                    included_approvals TEXT,
                    completeness_score REAL DEFAULT 0,
                    status TEXT DEFAULT 'draft',
                    generated_by INTEGER,
                    generated_at TIMESTAMP,
                    reviewed_by INTEGER,
                    reviewed_at TIMESTAMP,
                    notes TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (period_id) REFERENCES filing_periods(id),
                    FOREIGN KEY (jurisdiction_id) REFERENCES tax_jurisdictions(id),
                    FOREIGN KEY (entity_id) REFERENCES legal_entities(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_pack_number ON legal_audit_packs(pack_number)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_pack_status ON legal_audit_packs(status)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_pack_company ON legal_audit_packs(company_id)")
            db.commit()


def get_audit_packs(company_id=None, status=None, pack_type=None):
    """Get all audit packs."""
    sql = "SELECT * FROM legal_audit_packs WHERE is_deleted = 0"
    params = []
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if pack_type:
        sql += " AND pack_type = ?"
        params.append(pack_type)
    sql += " ORDER BY created_at DESC"
    return get_all(sql, params if params else None)


def get_audit_pack_by_id(pack_id):
    """Get a single audit pack by ID."""
    return get_one("SELECT * FROM legal_audit_packs WHERE id = ? AND is_deleted = 0", (pack_id,))


def create_audit_pack(data):
    """Create a new audit pack."""
    import json
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO legal_audit_packs (
                pack_number, pack_name, pack_type, period_id, jurisdiction_id,
                entity_id, included_schedules, included_documents, included_approvals,
                completeness_score, status, generated_by, generated_at,
                reviewed_by, reviewed_at, notes, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('pack_number'),
            data.get('pack_name'),
            data.get('pack_type'),
            data.get('period_id'),
            data.get('jurisdiction_id'),
            data.get('entity_id'),
            json.dumps(data.get('included_schedules')) if data.get('included_schedules') else None,
            json.dumps(data.get('included_documents')) if data.get('included_documents') else None,
            json.dumps(data.get('included_approvals')) if data.get('included_approvals') else None,
            data.get('completeness_score', 0),
            data.get('status', 'draft'),
            data.get('generated_by'),
            data.get('generated_at'),
            data.get('reviewed_by'),
            data.get('reviewed_at'),
            data.get('notes'),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def update_audit_pack(pack_id, data):
    """Update an audit pack."""
    import json
    fields = []
    values = []
    updatable = ['pack_name', 'pack_type', 'period_id', 'jurisdiction_id', 'entity_id',
                 'included_schedules', 'included_documents', 'included_approvals',
                 'completeness_score', 'status', 'generated_by', 'generated_at',
                 'reviewed_by', 'reviewed_at', 'notes']
    for field in updatable:
        if field in data:
            if field in ['included_schedules', 'included_documents', 'included_approvals']:
                fields.append(f"{field} = ?")
                values.append(json.dumps(data[field]) if data[field] else None)
            else:
                fields.append(f"{field} = ?")
                values.append(data[field])
    if not fields:
        return False
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(pack_id)
    with get_db_context() as db:
        db.execute(f"UPDATE legal_audit_packs SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
        return True


def get_next_pack_number(pack_type, company_id):
    """Generate next pack number."""
    prefix_map = {
        'tax_audit': 'AUD-TAX',
        'compliance': 'AUD-CMP',
        'internal': 'AUD-INT',
        'external': 'AUD-EXT',
        'other': 'AUD-OTH'
    }
    prefix = prefix_map.get(pack_type, 'AUD-OTH')
    with get_db_context() as db:
        cursor = db.execute("SELECT COUNT(*) as cnt FROM legal_audit_packs WHERE company_id = ?", (company_id,))
        row = cursor.fetchone()
        count = row['cnt'] + 1 if row else 1
        return f"{prefix}-{count:05d}"


# ============================================================================
# REPORT TEMPLATES
# ============================================================================

def _create_report_templates():
    """Create report templates table."""
    if not table_exists('legal_report_templates'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE legal_report_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_code TEXT UNIQUE NOT NULL,
                    template_name TEXT NOT NULL,
                    template_name_ar TEXT,
                    template_name_fa TEXT,
                    report_type TEXT NOT NULL,
                    description TEXT,
                    definition_json TEXT,
                    is_system INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_template_code ON legal_report_templates(template_code)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_template_type ON legal_report_templates(report_type)")
            db.commit()


def get_report_templates(company_id=None, report_type=None, active_only=True):
    """Get all report templates."""
    sql = "SELECT * FROM legal_report_templates WHERE is_deleted = 0"
    params = []
    if company_id:
        sql += " AND (company_id = ? OR company_id IS NULL)"
        params.append(company_id)
    if report_type:
        sql += " AND report_type = ?"
        params.append(report_type)
    if active_only:
        sql += " AND is_active = 1"
    sql += " ORDER BY template_name"
    return get_all(sql, params if params else None)


def get_report_template_by_id(template_id):
    """Get a single report template by ID."""
    return get_one("SELECT * FROM legal_report_templates WHERE id = ? AND is_deleted = 0", (template_id,))


def create_report_template(data):
    """Create a new report template."""
    import json
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO legal_report_templates (
                template_code, template_name, template_name_ar, template_name_fa,
                report_type, description, definition_json, is_system, is_active,
                company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('template_code'),
            data.get('template_name'),
            data.get('template_name_ar'),
            data.get('template_name_fa'),
            data.get('report_type'),
            data.get('description'),
            json.dumps(data.get('definition_json')) if data.get('definition_json') else None,
            data.get('is_system', 0),
            data.get('is_active', 1),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


# ============================================================================
# EXPORT PROFILES
# ============================================================================

def _create_export_profiles():
    """Create export profiles table."""
    if not table_exists('legal_export_profiles'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE legal_export_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_code TEXT UNIQUE NOT NULL,
                    profile_name TEXT NOT NULL,
                    export_type TEXT NOT NULL,
                    report_type TEXT,
                    columns_json TEXT,
                    filters_json TEXT,
                    sort_order TEXT,
                    is_default INTEGER DEFAULT 0,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_profile_code ON legal_export_profiles(profile_code)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_profile_type ON legal_export_profiles(export_type)")
            db.commit()


def get_export_profiles(company_id=None, export_type=None):
    """Get all export profiles."""
    sql = "SELECT * FROM legal_export_profiles WHERE is_deleted = 0"
    params = []
    if company_id:
        sql += " AND (company_id = ? OR company_id IS NULL)"
        params.append(company_id)
    if export_type:
        sql += " AND export_type = ?"
        params.append(export_type)
    sql += " ORDER BY profile_name"
    return get_all(sql, params if params else None)


def get_export_profile_by_id(profile_id):
    """Get a single export profile by ID."""
    return get_one("SELECT * FROM legal_export_profiles WHERE id = ? AND is_deleted = 0", (profile_id,))


def create_export_profile(data):
    """Create a new export profile."""
    import json
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO legal_export_profiles (
                profile_code, profile_name, export_type, report_type,
                columns_json, filters_json, sort_order, is_default, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('profile_code'),
            data.get('profile_name'),
            data.get('export_type'),
            data.get('report_type'),
            json.dumps(data.get('columns_json')) if data.get('columns_json') else None,
            json.dumps(data.get('filters_json')) if data.get('filters_json') else None,
            data.get('sort_order'),
            data.get('is_default', 0),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def update_export_profile(profile_id, data):
    """Update an export profile."""
    import json
    fields = []
    values = []
    updatable = ['profile_name', 'export_type', 'report_type', 'columns_json',
                 'filters_json', 'sort_order', 'is_default']
    for field in updatable:
        if field in data:
            if field in ['columns_json', 'filters_json']:
                fields.append(f"{field} = ?")
                values.append(json.dumps(data[field]) if data[field] else None)
            else:
                fields.append(f"{field} = ?")
                values.append(data[field])
    if not fields:
        return False
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(profile_id)
    with get_db_context() as db:
        db.execute(f"UPDATE legal_export_profiles SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
        return True


# ============================================================================
# SETTINGS
# ============================================================================

def _create_settings():
    """Create settings table."""
    if not table_exists('legal_settings'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE legal_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT,
                    setting_type TEXT DEFAULT 'text',
                    category TEXT DEFAULT 'general',
                    is_encrypted INTEGER DEFAULT 0,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_settings_key ON legal_settings(setting_key)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_settings_company ON legal_settings(company_id)")
            db.commit()


def get_legal_settings(company_id=None, category=None):
    """Get legal settings."""
    sql = "SELECT * FROM legal_settings WHERE 1=1"
    params = []
    if company_id:
        sql += " AND (company_id = ? OR company_id IS NULL)"
        params.append(company_id)
    if category:
        sql += " AND category = ?"
        params.append(category)
    return get_all(sql, params if params else None)


def get_legal_setting(key, company_id=None, default=None):
    """Get a specific setting value."""
    sql = "SELECT * FROM legal_settings WHERE setting_key = ? AND (company_id = ? OR company_id IS NULL)"
    result = get_one(sql, (key, company_id))
    if result:
        return result['setting_value']
    return default


def set_legal_setting(key, value, setting_type='text', category='general', company_id=None):
    """Set a legal setting."""
    with get_db_context() as db:
        existing = get_one("SELECT id FROM legal_settings WHERE setting_key = ? AND company_id = ?", (key, company_id))
        if existing:
            db.execute("""
                UPDATE legal_settings
                SET setting_value = ?, setting_type = ?, category = ?, updated_at = CURRENT_TIMESTAMP
                WHERE setting_key = ? AND company_id = ?
            """, (value, setting_type, category, key, company_id))
        else:
            db.execute("""
                INSERT INTO legal_settings (setting_key, setting_value, setting_type, category, company_id)
                VALUES (?, ?, ?, ?, ?)
            """, (key, value, setting_type, category, company_id))
        db.commit()
        return True


# ============================================================================
# FLOW LINKS
# ============================================================================

def _create_flow_links():
    """Create flow links table for Flow integration."""
    if not table_exists('legal_flow_links'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE legal_flow_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,
                    entity_id INTEGER NOT NULL,
                    flow_channel_id TEXT,
                    flow_thread_id TEXT,
                    flow_message_id TEXT,
                    is_active INTEGER DEFAULT 1,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_flowlink_entity ON legal_flow_links(entity_type, entity_id)")
            db.commit()


def get_flow_links(entity_type, entity_id):
    """Get flow links for an entity."""
    return get_all("""
        SELECT * FROM legal_flow_links
        WHERE entity_type = ? AND entity_id = ? AND is_deleted = 0 AND is_active = 1
    """, (entity_type, entity_id))


def create_flow_link(data):
    """Create a new flow link."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO legal_flow_links (
                entity_type, entity_id, flow_channel_id, flow_thread_id,
                flow_message_id, is_active, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('entity_type'),
            data.get('entity_id'),
            data.get('flow_channel_id'),
            data.get('flow_thread_id'),
            data.get('flow_message_id'),
            data.get('is_active', 1),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


# ============================================================================
# DOCUMENT LINKS
# ============================================================================

def _create_document_links():
    """Create document links table for document management integration."""
    if not table_exists('legal_document_links'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE legal_document_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,
                    entity_id INTEGER NOT NULL,
                    document_id INTEGER,
                    document_name TEXT,
                    document_type TEXT,
                    document_category TEXT,
                    file_path TEXT,
                    file_size INTEGER,
                    uploaded_by INTEGER,
                    is_primary INTEGER DEFAULT 0,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (document_id) REFERENCES documents(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_doclink_entity ON legal_document_links(entity_type, entity_id)")
            db.commit()


def get_document_links(entity_type, entity_id):
    """Get document links for an entity."""
    return get_all("""
        SELECT * FROM legal_document_links
        WHERE entity_type = ? AND entity_id = ? AND is_deleted = 0
        ORDER BY is_primary DESC, created_at DESC
    """, (entity_type, entity_id))


def create_document_link(data):
    """Create a new document link."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO legal_document_links (
                entity_type, entity_id, document_id, document_name,
                document_type, document_category, file_path, file_size,
                uploaded_by, is_primary, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('entity_type'),
            data.get('entity_id'),
            data.get('document_id'),
            data.get('document_name'),
            data.get('document_type'),
            data.get('document_category'),
            data.get('file_path'),
            data.get('file_size'),
            data.get('uploaded_by'),
            data.get('is_primary', 0),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def delete_document_link(link_id):
    """Delete a document link."""
    with get_db_context() as db:
        db.execute("UPDATE legal_document_links SET is_deleted = 1 WHERE id = ?", (link_id,))
        db.commit()
        return True


# ============================================================================
# LEGAL TAX SETTINGS (EXTENDED)
# ============================================================================

def _create_legal_tax_settings():
    """Create extended legal tax settings table."""
    if not table_exists('legal_tax_settings'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE legal_tax_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER,
                    jurisdiction_id INTEGER,
                    filing_frequency TEXT DEFAULT 'monthly',
                    default_approval_workflow TEXT,
                    auto_reminder_days INTEGER DEFAULT 7,
                    reminder_repeat_days INTEGER DEFAULT 3,
                    late_filing_penalty_rate REAL DEFAULT 0,
                    late_payment_penalty_rate REAL DEFAULT 0,
                    require_attachment_for_filing INTEGER DEFAULT 1,
                    allow_amendment_after_filing INTEGER DEFAULT 1,
                    lock_period_after_filing INTEGER DEFAULT 1,
                    risk_score_threshold INTEGER DEFAULT 70,
                    default_currency TEXT DEFAULT 'USD',
                    enable_auto_reconciliation INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id),
                    FOREIGN KEY (jurisdiction_id) REFERENCES tax_jurisdictions(id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_legal_settings_company ON legal_tax_settings(company_id)")
            db.commit()


def get_legal_tax_settings(company_id=None):
    """Get legal tax settings."""
    sql = "SELECT * FROM legal_tax_settings WHERE 1=1"
    params = []
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    results = get_all(sql, params if params else None)
    if results:
        return results[0]
    return None


def save_legal_tax_settings(data, company_id=None):
    """Save legal tax settings."""
    existing = get_legal_tax_settings(company_id)
    with get_db_context() as db:
        fields = []
        values = []
        updatable = ['jurisdiction_id', 'filing_frequency', 'default_approval_workflow',
                     'auto_reminder_days', 'reminder_repeat_days', 'late_filing_penalty_rate',
                     'late_payment_penalty_rate', 'require_attachment_for_filing',
                     'allow_amendment_after_filing', 'lock_period_after_filing',
                     'risk_score_threshold', 'default_currency', 'enable_auto_reconciliation']
        for field in updatable:
            if field in data:
                fields.append(f"{field} = ?")
                values.append(data[field])
        if not fields:
            return False
        fields.append("updated_at = CURRENT_TIMESTAMP")
        if existing:
            values.append(company_id)
            db.execute(f"UPDATE legal_tax_settings SET {', '.join(fields)} WHERE company_id = ?", values)
        else:
            fields.append("company_id")
            values.append(company_id)
            db.execute(f"INSERT INTO legal_tax_settings ({', '.join(fields)}) VALUES ({', '.join(['?'] * len(fields))})", values)
        db.commit()
        return True


# ============================================================================
# DASHBOARD / STATISTICS HELPERS
# ============================================================================

def get_legal_tax_dashboard_stats(company_id=None):
    """Get dashboard statistics for legal/tax module."""
    stats = {}

    with get_db_context() as db:
        base_sql = "WHERE is_deleted = 0"
        params = []
        if company_id:
            base_sql += " AND company_id = ?"
            params = [company_id]

        cursor = db.execute(f"SELECT COUNT(*) as cnt, status FROM legal_returns {base_sql} GROUP BY status", params)
        stats['returns_by_status'] = {row['status']: row['cnt'] for row in cursor.fetchall()}

        cursor = db.execute(f"SELECT COUNT(*) as cnt FROM legal_obligations {base_sql} AND status = 'pending' AND due_date < date('now')", params)
        row = cursor.fetchone()
        stats['overdue_obligations'] = row['cnt'] if row else 0

        cursor = db.execute(f"SELECT COUNT(*) as cnt FROM legal_obligations {base_sql} AND status = 'pending' AND due_date BETWEEN date('now') AND date('now', '+7 days')", params)
        row = cursor.fetchone()
        stats['upcoming_obligations_7d'] = row['cnt'] if row else 0

        cursor = db.execute(f"SELECT COUNT(*) as cnt FROM tax_review_items {base_sql} AND status = 'pending'", params)
        row = cursor.fetchone()
        stats['pending_review_items'] = row['cnt'] if row else 0

        cursor = db.execute(f"SELECT COUNT(*) as cnt FROM legal_notices {base_sql} AND status = 'received'", params)
        row = cursor.fetchone()
        stats['open_notices'] = row['cnt'] if row else 0

        cursor = db.execute(f"SELECT COUNT(*) as cnt FROM legal_penalties {base_sql} AND status = 'pending'", params)
        row = cursor.fetchone()
        stats['pending_penalties'] = row['cnt'] if row else 0

        cursor = db.execute(f"SELECT COUNT(*) as cnt FROM legal_disputes {base_sql} AND status = 'open'", params)
        row = cursor.fetchone()
        stats['open_disputes'] = row['cnt'] if row else 0

        cursor = db.execute(f"SELECT COUNT(*) as cnt FROM legal_reconciliations {base_sql} AND status = 'draft'", params)
        row = cursor.fetchone()
        stats['pending_reconciliations'] = row['cnt'] if row else 0

    return stats


def get_filing_calendar_events(company_id=None, start_date=None, end_date=None):
    """Get filing calendar events."""
    sql = """
        SELECT 'obligation' as event_type, id, obligation_number as reference,
               description as title, due_date as event_date, priority, status
        FROM legal_obligations
        WHERE is_deleted = 0 AND status IN ('pending', 'in_progress')
    """
    params = []
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    if start_date:
        sql += " AND due_date >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND due_date <= ?"
        params.append(end_date)

    sql += """
        UNION ALL
        SELECT 'return' as event_type, id, return_number as reference,
               return_type as title, fp.end_date as event_date, 'high' as priority, r.status
        FROM legal_returns r
        LEFT JOIN filing_periods fp ON r.filing_period_id = fp.id
        WHERE r.is_deleted = 0 AND r.status IN ('draft', 'submitted', 'approved')
    """
    if company_id:
        sql += " AND r.company_id = ?"
        params.append(company_id)

    return get_all(sql, params)
