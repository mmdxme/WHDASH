"""
Seed Data for Legal / Tax Reporting Module
========================================
Generates realistic sample data for testing and demonstration.

Author: Legal/Tax Module Implementation
"""

from database import get_db_context, table_exists
from legal_tax_models import (
    initialize_legal_tax_schema,
    create_tax_jurisdiction,
    create_tax_authority,
    create_legal_entity,
    create_tax_group,
    create_tax_code,
    create_tax_rate,
    create_tax_rule,
    create_filing_period,
    create_return,
    create_return_line,
    create_return_adjustment,
    create_obligations,
    create_compliance_task,
    create_tax_review_item,
    create_notice,
    create_penalty,
    create_dispute,
    create_reconciliation,
    create_reconciliation_line,
    create_audit_pack,
    get_next_return_number,
    get_next_obligation_number,
    get_next_task_number,
    get_next_review_number,
    get_next_notice_number,
    get_next_penalty_number,
    get_next_dispute_number,
    get_next_reconciliation_number,
    get_next_pack_number,
)


def seed_legal_tax_data():
    """Generate seed data for legal/tax module."""

    # Initialize schema first
    initialize_legal_tax_schema()

    with get_db_context() as db:
        # Check if data already exists
        cursor = db.execute("SELECT COUNT(*) as cnt FROM tax_jurisdictions")
        row = cursor.fetchone()
        if row and row['cnt'] > 0:
            print("- Tax jurisdictions already have data, skipping")
            return

    company_id = 1  # Default company
    user_id = 1  # Default user

    print("Seeding Legal/Tax data...")

    # =================================================================
    # TAX JURISDICTIONS
    # =================================================================
    jurisdictions = [
        {
            'code': 'UAE-FED', 'name': 'UAE Federal', 'name_ar': 'المركز المالي للاتحاد',
            'country': 'UAE', 'tax_type': 'federal', 'company_id': company_id, 'created_by': user_id
        },
        {
            'code': 'UAE-DXB', 'name': 'Dubai', 'name_ar': 'دبي',
            'country': 'UAE', 'region': 'Dubai', 'tax_type': 'vat', 'company_id': company_id, 'created_by': user_id
        },
        {
            'code': 'UAE-AUH', 'name': 'Abu Dhabi', 'name_ar': 'أبوظبي',
            'country': 'UAE', 'region': 'Abu Dhabi', 'tax_type': 'vat', 'company_id': company_id, 'created_by': user_id
        },
        {
            'code': 'SAU', 'name': 'Saudi Arabia', 'name_ar': 'المملكة العربية السعودية',
            'country': 'Saudi Arabia', 'tax_type': 'vat', 'company_id': company_id, 'created_by': user_id
        },
        {
            'code': 'EGY', 'name': 'Egypt', 'name_ar': 'مصر',
            'country': 'Egypt', 'tax_type': 'sales_tax', 'company_id': company_id, 'created_by': user_id
        },
        {
            'code': 'IND', 'name': 'India', 'name_ar': 'الهند',
            'country': 'India', 'tax_type': 'gst', 'company_id': company_id, 'created_by': user_id
        },
    ]

    jurisdiction_ids = {}
    for j in jurisdictions:
        j_id = create_tax_jurisdiction(j)
        jurisdiction_ids[j['code']] = j_id
    print(f"- Created {len(jurisdictions)} tax jurisdictions")

    # =================================================================
    # TAX AUTHORITIES
    # =================================================================
    authorities = [
        {
            'code': 'FTA', 'name': 'Federal Tax Authority', 'name_ar': 'الهيئة الاتحادية للضرائب',
            'jurisdiction_id': jurisdiction_ids['UAE-FED'], 'country': 'UAE',
            'email': 'info@fta.gov.ae', 'phone': '+971 4 300 5000',
            'company_id': company_id, 'created_by': user_id
        },
        {
            'code': 'DMCC', 'name': 'Dubai Customs', 'name_ar': 'جمارك دبي',
            'jurisdiction_id': jurisdiction_ids['UAE-DXB'], 'country': 'UAE',
            'email': 'info@dmcc.ae', 'phone': '+971 4 555 5555',
            'company_id': company_id, 'created_by': user_id
        },
        {
            'code': 'GAZT', 'name': 'General Authority for Zakat and Tax', 'name_ar': 'الهيئة العامة للزكاة والدخل',
            'jurisdiction_id': jurisdiction_ids['SAU'], 'country': 'Saudi Arabia',
            'email': 'info@gazt.gov.sa', 'phone': '+966 11 500 0000',
            'company_id': company_id, 'created_by': user_id
        },
        {
            'code': 'ETA', 'name': 'Egyptian Tax Authority', 'name_ar': 'مصلحة الضرائب المصرية',
            'jurisdiction_id': jurisdiction_ids['EGY'], 'country': 'Egypt',
            'email': 'info@eta.gov.eg', 'phone': '+202 16328',
            'company_id': company_id, 'created_by': user_id
        },
        {
            'code': 'CBIC', 'name': 'Central Board of Indirect Taxes', 'name_ar': 'المجلس المركزي للضرائب غير المباشرة',
            'jurisdiction_id': jurisdiction_ids['IND'], 'country': 'India',
            'email': 'gst@cbic.gov.in', 'phone': '+91 11 2300 0000',
            'company_id': company_id, 'created_by': user_id
        },
    ]

    authority_ids = {}
    for a in authorities:
        a_id = create_tax_authority(a)
        authority_ids[a['code']] = a_id
    print(f"- Created {len(authorities)} tax authorities")

    # =================================================================
    # LEGAL ENTITIES
    # =================================================================
    entities = [
        {
            'code': 'ENT-001', 'name': 'Global Trading LLC', 'name_ar': 'شركة التجارة العالمية',
            'registration_number': 'CL-123456', 'tax_identification_number': 'TIN-789456',
            'vat_number': 'VAT-123456789', 'jurisdiction_id': jurisdiction_ids['UAE-DXB'],
            'city': 'Dubai', 'country': 'UAE', 'email': 'info@globaltrading.ae',
            'company_id': company_id, 'created_by': user_id
        },
        {
            'code': 'ENT-002', 'name': 'Gulf Services FZE', 'name_ar': 'خدمات الخليج',
            'registration_number': 'CL-654321', 'tax_identification_number': 'TIN-456789',
            'vat_number': 'VAT-987654321', 'jurisdiction_id': jurisdiction_ids['UAE-AUH'],
            'city': 'Abu Dhabi', 'country': 'UAE', 'email': 'contact@gulfservices.ae',
            'company_id': company_id, 'created_by': user_id
        },
        {
            'code': 'ENT-003', 'name': 'Riyadh Retail Co', 'name_ar': 'شركة رياض للتجزئة',
            'registration_number': 'CR-101010', 'tax_identification_number': 'TIN-101010',
            'vat_number': 'VAT-3101234567', 'jurisdiction_id': jurisdiction_ids['SAU'],
            'city': 'Riyadh', 'country': 'Saudi Arabia', 'email': 'info@riyadhretail.sa',
            'company_id': company_id, 'created_by': user_id
        },
    ]

    entity_ids = {}
    for e in entities:
        e_id = create_legal_entity(e)
        entity_ids[e['code']] = e_id
    print(f"- Created {len(entities)} legal entities")

    # =================================================================
    # TAX GROUPS
    # =================================================================
    groups = [
        {'code': 'GRP-STD', 'name': 'Standard Rate', 'name_ar': 'السعر القياسي',
         'company_id': company_id, 'created_by': user_id},
        {'code': 'GRP-ZERO', 'name': 'Zero Rate', 'name_ar': 'معدل الصفر',
         'company_id': company_id, 'created_by': user_id},
        {'code': 'GRP-EXEMPT', 'name': 'Exempt', 'name_ar': 'معفى',
         'company_id': company_id, 'created_by': user_id},
        {'code': 'GRP-OUT', 'name': 'Out of Scope', 'name_ar': 'خارج النطاق',
         'company_id': company_id, 'created_by': user_id},
    ]

    group_ids = {}
    for g in groups:
        g_id = create_tax_group(g)
        group_ids[g['code']] = g_id
    print(f"- Created {len(groups)} tax groups")

    # =================================================================
    # TAX RATES
    # =================================================================
    rates = [
        {'code': 'RATE-5', 'name': '5% Standard', 'rate': 5, 'rate_type': 'percentage',
         'company_id': company_id, 'created_by': user_id},
        {'code': 'RATE-0', 'name': '0% Zero', 'rate': 0, 'rate_type': 'percentage',
         'company_id': company_id, 'created_by': user_id},
        {'code': 'RATE-15', 'name': '15% Standard', 'rate': 15, 'rate_type': 'percentage',
         'company_id': company_id, 'created_by': user_id},
        {'code': 'RATE-18', 'name': '18% GST', 'rate': 18, 'rate_type': 'percentage',
         'company_id': company_id, 'created_by': user_id},
    ]

    rate_ids = {}
    for r in rates:
        r_id = create_tax_rate(r)
        rate_ids[r['code']] = r_id
    print(f"- Created {len(rates)} tax rates")

    # =================================================================
    # TAX CODES
    # =================================================================
    tax_codes = [
        {'code': 'TC-VAT-5', 'name': 'VAT 5%', 'tax_group_id': group_ids['GRP-STD'],
         'jurisdiction_id': jurisdiction_ids['UAE-FED'], 'tax_rate_id': rate_ids['RATE-5'],
         'company_id': company_id, 'created_by': user_id},
        {'code': 'TC-VAT-0', 'name': 'VAT 0%', 'tax_group_id': group_ids['GRP-ZERO'],
         'jurisdiction_id': jurisdiction_ids['UAE-FED'], 'tax_rate_id': rate_ids['RATE-0'],
         'company_id': company_id, 'created_by': user_id},
        {'code': 'TC-VAT-EX', 'name': 'VAT Exempt', 'tax_group_id': group_ids['GRP-EXEMPT'],
         'jurisdiction_id': jurisdiction_ids['UAE-FED'],
         'company_id': company_id, 'created_by': user_id},
        {'code': 'TC-SA-15', 'name': 'KSA VAT 15%', 'tax_group_id': group_ids['GRP-STD'],
         'jurisdiction_id': jurisdiction_ids['SAU'], 'tax_rate_id': rate_ids['RATE-15'],
         'company_id': company_id, 'created_by': user_id},
        {'code': 'TC-IN-18', 'name': 'India GST 18%', 'tax_group_id': group_ids['GRP-STD'],
         'jurisdiction_id': jurisdiction_ids['IND'], 'tax_rate_id': rate_ids['RATE-18'],
         'company_id': company_id, 'created_by': user_id},
    ]

    tax_code_ids = {}
    for tc in tax_codes:
        tc_id = create_tax_code(tc)
        tax_code_ids[tc['code']] = tc_id
    print(f"- Created {len(tax_codes)} tax codes")

    # =================================================================
    # TAX RULES
    # =================================================================
    tax_rules = [
        {'code': 'RUL-001', 'name': 'Standard Output VAT', 'rule_type': 'output_vat',
         'tax_code_id': tax_code_ids['TC-VAT-5'], 'jurisdiction_id': jurisdiction_ids['UAE-FED'],
         'priority': 10, 'company_id': company_id, 'created_by': user_id},
        {'code': 'RUL-002', 'name': 'Zero Rated Supplies', 'rule_type': 'zero_rated',
         'tax_code_id': tax_code_ids['TC-VAT-0'], 'jurisdiction_id': jurisdiction_ids['UAE-FED'],
         'priority': 5, 'company_id': company_id, 'created_by': user_id},
        {'code': 'RUL-003', 'name': 'Exempt Supplies', 'rule_type': 'exempt',
         'tax_code_id': tax_code_ids['TC-VAT-EX'], 'jurisdiction_id': jurisdiction_ids['UAE-FED'],
         'priority': 1, 'company_id': company_id, 'created_by': user_id},
    ]

    for tr in tax_rules:
        create_tax_rule(tr)
    print(f"- Created {len(tax_rules)} tax rules")

    # =================================================================
    # FILING PERIODS
    # =================================================================
    from datetime import date, timedelta
    periods = [
        {'code': 'FP-2026-Q1', 'name': 'Q1 2026', 'period_type': 'quarterly',
         'jurisdiction_id': jurisdiction_ids['UAE-FED'], 'authority_id': authority_ids['FTA'],
         'start_date': '2026-01-01', 'end_date': '2026-03-31', 'due_date': '2026-04-28',
         'filing_frequency': 'quarterly', 'company_id': company_id, 'created_by': user_id},
        {'code': 'FP-2026-Q4-2025', 'name': 'Q4 2025', 'period_type': 'quarterly',
         'jurisdiction_id': jurisdiction_ids['UAE-FED'], 'authority_id': authority_ids['FTA'],
         'start_date': '2025-10-01', 'end_date': '2025-12-31', 'due_date': '2026-01-28',
         'filing_frequency': 'quarterly', 'status': 'filed', 'company_id': company_id, 'created_by': user_id},
        {'code': 'FP-2026-M03', 'name': 'March 2026', 'period_type': 'monthly',
         'jurisdiction_id': jurisdiction_ids['UAE-FED'], 'authority_id': authority_ids['FTA'],
         'start_date': '2026-03-01', 'end_date': '2026-03-31', 'due_date': '2026-04-28',
         'filing_frequency': 'monthly', 'company_id': company_id, 'created_by': user_id},
        {'code': 'FP-2026-M02', 'name': 'February 2026', 'period_type': 'monthly',
         'jurisdiction_id': jurisdiction_ids['UAE-FED'], 'authority_id': authority_ids['FTA'],
         'start_date': '2026-02-01', 'end_date': '2026-02-28', 'due_date': '2026-03-28',
         'filing_frequency': 'monthly', 'status': 'filed', 'company_id': company_id, 'created_by': user_id},
    ]

    period_ids = {}
    for p in periods:
        p_id = create_filing_period(p)
        period_ids[p['code']] = p_id
    print(f"- Created {len(periods)} filing periods")

    # =================================================================
    # RETURNS
    # =================================================================
    returns_data = [
        {
            'return_type': 'vat', 'filing_period_id': period_ids['FP-2026-Q4-2025'],
            'jurisdiction_id': jurisdiction_ids['UAE-FED'], 'authority_id': authority_ids['FTA'],
            'entity_id': entity_ids['ENT-001'], 'status': 'approved', 'filing_status': 'filed',
            'total_output_tax': 52500, 'total_input_tax': 31200, 'total_tax_due': 21300,
            'company_id': company_id, 'created_by': user_id
        },
        {
            'return_type': 'vat', 'filing_period_id': period_ids['FP-2026-M02'],
            'jurisdiction_id': jurisdiction_ids['UAE-FED'], 'authority_id': authority_ids['FTA'],
            'entity_id': entity_ids['ENT-001'], 'status': 'approved', 'filing_status': 'filed',
            'total_output_tax': 17500, 'total_input_tax': 10400, 'total_tax_due': 7100,
            'company_id': company_id, 'created_by': user_id
        },
        {
            'return_type': 'vat', 'filing_period_id': period_ids['FP-2026-M03'],
            'jurisdiction_id': jurisdiction_ids['UAE-FED'], 'authority_id': authority_ids['FTA'],
            'entity_id': entity_ids['ENT-001'], 'status': 'draft', 'filing_status': 'pending',
            'total_output_tax': 21300, 'total_input_tax': 12800, 'total_tax_due': 8500,
            'company_id': company_id, 'created_by': user_id
        },
    ]

    return_ids = []
    for i, r in enumerate(returns_data):
        r['return_number'] = get_next_return_number(r['return_type'], company_id)
        r_id = create_return(r)
        return_ids.append(r_id)

        # Add return lines
        lines = [
            {'return_id': r_id, 'box_code': '1', 'box_label': 'Total Sales (Excl. VAT)',
             'base_amount': 420000, 'tax_amount': 21000, 'tax_rate': 5, 'line_type': 'auto',
             'company_id': company_id},
            {'return_id': r_id, 'box_code': '2', 'box_label': 'Total Zero-Rated Sales',
             'base_amount': 150000, 'tax_amount': 0, 'tax_rate': 0, 'line_type': 'auto',
             'company_id': company_id},
            {'return_id': r_id, 'box_code': '3', 'box_label': 'Total Exempt Sales',
             'base_amount': 80000, 'tax_amount': 0, 'tax_rate': 0, 'line_type': 'auto',
             'company_id': company_id},
            {'return_id': r_id, 'box_code': '4', 'box_label': 'Total Output Tax Due',
             'base_amount': 0, 'tax_amount': 21000, 'tax_rate': 5, 'line_type': 'auto',
             'company_id': company_id},
            {'return_id': r_id, 'box_code': '5', 'box_label': 'Total Input Tax (Recoverable)',
             'base_amount': 0, 'tax_amount': 12800, 'tax_rate': 5, 'line_type': 'auto',
             'company_id': company_id},
            {'return_id': r_id, 'box_code': '6', 'box_label': 'Net Tax Due',
             'base_amount': 0, 'tax_amount': 8200, 'tax_rate': 5, 'line_type': 'auto',
             'company_id': company_id},
        ]
        for j, line in enumerate(lines):
            line['line_number'] = j + 1
            create_return_line(line)
    print(f"- Created {len(returns_data)} returns with lines")

    # =================================================================
    # OBLIGATIONS
    # =================================================================
    obligations_data = [
        {
            'obligation_type': 'vat_return', 'description': 'Q1 2026 VAT Return Filing',
            'jurisdiction_id': jurisdiction_ids['UAE-FED'], 'authority_id': authority_ids['FTA'],
            'entity_id': entity_ids['ENT-001'], 'filing_period_id': period_ids['FP-2026-Q1'],
            'due_date': '2026-04-28', 'filing_frequency': 'quarterly',
            'status': 'pending', 'priority': 'high', 'risk_score': 75,
            'company_id': company_id, 'created_by': user_id
        },
        {
            'obligation_type': 'vat_return', 'description': 'March 2026 VAT Return',
            'jurisdiction_id': jurisdiction_ids['UAE-FED'], 'authority_id': authority_ids['FTA'],
            'entity_id': entity_ids['ENT-002'], 'filing_period_id': period_ids['FP-2026-M03'],
            'due_date': '2026-04-28', 'filing_frequency': 'monthly',
            'status': 'pending', 'priority': 'high', 'risk_score': 80,
            'company_id': company_id, 'created_by': user_id
        },
        {
            'obligation_type': 'vat_return', 'description': 'Q4 2025 KSA VAT Return',
            'jurisdiction_id': jurisdiction_ids['SAU'], 'authority_id': authority_ids['GAZT'],
            'entity_id': entity_ids['ENT-003'], 'due_date': '2026-02-28',
            'filing_frequency': 'quarterly', 'status': 'completed', 'priority': 'high',
            'company_id': company_id, 'created_by': user_id
        },
        {
            'obligation_type': 'tax_filing', 'description': 'Annual Tax Report 2025',
            'jurisdiction_id': jurisdiction_ids['UAE-FED'], 'authority_id': authority_ids['FTA'],
            'entity_id': entity_ids['ENT-001'], 'due_date': '2026-03-31',
            'filing_frequency': 'annually', 'status': 'pending', 'priority': 'medium',
            'risk_score': 50, 'company_id': company_id, 'created_by': user_id
        },
    ]

    for o in obligations_data:
        o['obligation_number'] = get_next_obligation_number(o['obligation_type'], company_id)
        create_obligations(o)
    print(f"- Created {len(obligations_data)} obligations")

    # =================================================================
    # COMPLIANCE TASKS
    # =================================================================
    tasks_data = [
        {
            'task_type': 'filing', 'title': 'Prepare Q1 2026 VAT Return',
            'obligation_id': None, 'return_id': return_ids[2] if len(return_ids) > 2 else None,
            'priority': 'high', 'status': 'pending', 'due_date': '2026-04-20',
            'company_id': company_id, 'created_by': user_id
        },
        {
            'task_type': 'review', 'title': 'Review March 2026 Transactions',
            'priority': 'medium', 'status': 'pending', 'due_date': '2026-04-15',
            'company_id': company_id, 'created_by': user_id
        },
        {
            'task_type': 'reconciliation', 'title': 'Reconcile Q1 Tax Accounts',
            'priority': 'high', 'status': 'in_progress', 'due_date': '2026-04-25',
            'company_id': company_id, 'created_by': user_id
        },
    ]

    for t in tasks_data:
        t['task_number'] = get_next_task_number(t['task_type'], company_id)
        create_compliance_task(t)
    print(f"- Created {len(tasks_data)} compliance tasks")

    # =================================================================
    # TAX REVIEW ITEMS
    # =================================================================
    review_items_data = [
        {
            'item_type': 'invoice', 'source_transaction': 'Customer Invoice',
            'source_transaction_id': 1001, 'tax_code_id': tax_code_ids['TC-VAT-5'],
            'transaction_date': '2026-03-15', 'transaction_amount': 52500,
            'tax_amount': 2625, 'exception_type': 'rate_mismatch',
            'exception_reason': 'Invoice shows 5% but should be 0% for this category',
            'severity': 'high', 'status': 'pending',
            'company_id': company_id, 'created_by': user_id
        },
        {
            'item_type': 'bill', 'source_transaction': 'Supplier Bill',
            'source_transaction_id': 2001, 'tax_code_id': tax_code_ids['TC-VAT-5'],
            'transaction_date': '2026-03-10', 'transaction_amount': 31500,
            'tax_amount': 1575, 'exception_type': 'missing_tax_code',
            'exception_reason': 'Supplier bill missing tax code',
            'severity': 'medium', 'status': 'pending',
            'company_id': company_id, 'created_by': user_id
        },
        {
            'item_type': 'credit_note', 'source_transaction': 'Credit Note',
            'source_transaction_id': 3001, 'tax_code_id': tax_code_ids['TC-VAT-0'],
            'transaction_date': '2026-03-20', 'transaction_amount': 10500,
            'tax_amount': 0, 'exception_type': 'duplicate_risk',
            'exception_reason': 'Possible duplicate credit note detected',
            'severity': 'low', 'status': 'approved',
            'company_id': company_id, 'created_by': user_id
        },
    ]

    for r in review_items_data:
        r['review_number'] = get_next_review_number(r['item_type'], company_id)
        create_tax_review_item(r)
    print(f"- Created {len(review_items_data)} tax review items")

    # =================================================================
    # NOTICES
    # =================================================================
    notices_data = [
        {
            'notice_type': 'inquiry', 'authority_id': authority_ids['FTA'],
            'entity_id': entity_ids['ENT-001'], 'subject': 'VAT Return Inquiry - Q4 2025',
            'content': 'We require additional documentation for some transactions in your Q4 2025 VAT return.',
            'severity': 'medium', 'issue_date': '2026-03-15', 'due_date': '2026-04-15',
            'status': 'received', 'company_id': company_id, 'created_by': user_id
        },
        {
            'notice_type': 'assessment', 'authority_id': authority_ids['GAZT'],
            'entity_id': entity_ids['ENT-003'], 'subject': 'VAT Assessment Notice - Q3 2025',
            'content': 'Additional tax assessed based on review of your Q3 2025 return.',
            'severity': 'high', 'issue_date': '2026-02-20', 'due_date': '2026-03-20',
            'status': 'responded', 'company_id': company_id, 'created_by': user_id
        },
    ]

    for n in notices_data:
        n['notice_number'] = get_next_notice_number(n['notice_type'], company_id)
        create_notice(n)
    print(f"- Created {len(notices_data)} notices")

    # =================================================================
    # PENALTIES
    # =================================================================
    penalties_data = [
        {
            'penalty_type': 'late_filing', 'authority_id': authority_ids['FTA'],
            'entity_id': entity_ids['ENT-001'],
            'description': 'Late filing penalty for February 2026 VAT return',
            'amount': 1000, 'penalty_date': '2026-03-29', 'due_date': '2026-04-15',
            'status': 'pending', 'company_id': company_id, 'created_by': user_id
        },
        {
            'penalty_type': 'late_payment', 'authority_id': authority_ids['GAZT'],
            'entity_id': entity_ids['ENT-003'],
            'description': 'Late payment penalty for Q3 2025 VAT',
            'amount': 2500, 'penalty_date': '2026-01-29', 'due_date': '2026-03-15',
            'status': 'partial', 'paid_amount': 1000,
            'company_id': company_id, 'created_by': user_id
        },
    ]

    for p in penalties_data:
        p['penalty_number'] = get_next_penalty_number(p['penalty_type'], company_id)
        create_penalty(p)
    print(f"- Created {len(penalties_data)} penalties")

    # =================================================================
    # DISPUTES
    # =================================================================
    disputes_data = [
        {
            'dispute_type': 'tax_assessment', 'authority_id': authority_ids['GAZT'],
            'entity_id': entity_ids['ENT-003'],
            'subject': 'Dispute: Q3 2025 VAT Assessment',
            'description': 'We dispute the additional tax assessed for Q3 2025. Our return was correct.',
            'amount': 15000, 'filing_date': '2026-02-25', 'status': 'open',
            'company_id': company_id, 'created_by': user_id
        },
    ]

    for d in disputes_data:
        d['dispute_number'] = get_next_dispute_number(d['dispute_type'], company_id)
        create_dispute(d)
    print(f"- Created {len(disputes_data)} disputes")

    # =================================================================
    # RECONCILIATIONS
    # =================================================================
    reconciliations_data = [
        {
            'reconciliation_type': 'gl_tax', 'period_id': period_ids['FP-2026-M02'],
            'jurisdiction_id': jurisdiction_ids['UAE-FED'], 'entity_id': entity_ids['ENT-001'],
            'status': 'completed', 'total_source_amount': 7100, 'total_target_amount': 7100,
            'variance_amount': 0, 'matched_count': 6, 'unmatched_count': 0,
            'company_id': company_id, 'created_by': user_id
        },
        {
            'reconciliation_type': 'gl_tax', 'period_id': period_ids['FP-2026-M03'],
            'jurisdiction_id': jurisdiction_ids['UAE-FED'], 'entity_id': entity_ids['ENT-001'],
            'status': 'draft', 'total_source_amount': 8500, 'total_target_amount': 8200,
            'variance_amount': 300, 'matched_count': 4, 'unmatched_count': 2,
            'company_id': company_id, 'created_by': user_id
        },
    ]

    recon_ids = []
    for r in reconciliations_data:
        r['reconciliation_number'] = get_next_reconciliation_number(r['reconciliation_type'], company_id)
        recon_id = create_reconciliation(r)
        recon_ids.append(recon_id)

        # Add reconciliation lines
        lines = [
            {'reconciliation_id': recon_id, 'line_type': 'source', 'source_amount': 8500,
             'target_amount': 8200, 'variance_amount': 300, 'match_status': 'matched',
             'match_explanation': 'Minor rounding difference', 'company_id': company_id},
        ]
        for line in lines:
            create_reconciliation_line(line)
    print(f"- Created {len(reconciliations_data)} reconciliations")

    # =================================================================
    # AUDIT PACKS
    # =================================================================
    audit_packs_data = [
        {
            'pack_name': 'Q4 2025 VAT Audit Pack', 'pack_type': 'tax_audit',
            'period_id': period_ids['FP-2026-Q4-2025'], 'jurisdiction_id': jurisdiction_ids['UAE-FED'],
            'entity_id': entity_ids['ENT-001'],
            'status': 'completed', 'completeness_score': 95,
            'generated_by': user_id, 'company_id': company_id, 'created_by': user_id
        },
        {
            'pack_name': 'Q1 2026 Tax Audit Pack', 'pack_type': 'tax_audit',
            'period_id': period_ids['FP-2026-Q1'], 'jurisdiction_id': jurisdiction_ids['UAE-FED'],
            'entity_id': entity_ids['ENT-001'],
            'status': 'draft', 'completeness_score': 45,
            'company_id': company_id, 'created_by': user_id
        },
    ]

    for ap in audit_packs_data:
        ap['pack_number'] = get_next_pack_number(ap['pack_type'], company_id)
        create_audit_pack(ap)
    print(f"- Created {len(audit_packs_data)} audit packs")

    print("\nLegal/Tax sample data seeding completed successfully!")
    print(f"  - {len(jurisdictions)} jurisdictions")
    print(f"  - {len(authorities)} authorities")
    print(f"  - {len(entities)} entities")
    print(f"  - {len(groups)} tax groups")
    print(f"  - {len(rates)} tax rates")
    print(f"  - {len(tax_codes)} tax codes")
    print(f"  - {len(tax_rules)} tax rules")
    print(f"  - {len(periods)} filing periods")
    print(f"  - {len(returns_data)} returns")
    print(f"  - {len(obligations_data)} obligations")
    print(f"  - {len(tasks_data)} compliance tasks")
    print(f"  - {len(review_items_data)} tax review items")
    print(f"  - {len(notices_data)} notices")
    print(f"  - {len(penalties_data)} penalties")
    print(f"  - {len(disputes_data)} disputes")
    print(f"  - {len(reconciliations_data)} reconciliations")
    print(f"  - {len(audit_packs_data)} audit packs")


if __name__ == '__main__':
    seed_legal_tax_data()
