"""
Form Builder Sample Templates Seeder
===================================
Creates sample form templates for the Form Builder system.
Run this script to seed starter templates.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db_context
from form_models import (
    initialize_form_builder_tables, create_form_template, create_form_section,
    create_form_field, create_field_option, create_table_column, create_numbering_rule,
    get_form_templates
)


def seed_warehouse_request_form():
    """Seed Warehouse Request Form template."""
    # Check if already exists
    existing = get_form_templates(status=None)
    for t in existing:
        if t.get('template_code') == 'WH-REQ':
            return t['id']
    
    # Create template
    template_id = create_form_template({
        'template_code': 'WH-REQ',
        'form_title': 'Warehouse Request Form',
        'form_title_ar': 'نموذج طلب المستودع',
        'description': 'Standard form for warehouse requests including item requests, transfers, and adjustments.',
        'purpose': 'Request items, materials, or equipment from the warehouse',
        'department': 'warehouse',
        'category': 'Request',
        'subcategory': 'Inventory',
        'status': 'published',
        'allow_draft': 1,
        'allow_cancel': 1,
        'require_attachment': 1,
        'numbering_prefix': 'WH-REQ',
        'numbering_date_format': 'YYYY',
        'visibility': 'internal'
    })
    
    # Create numbering rule
    create_numbering_rule(
        template_id=template_id,
        prefix='WH-REQ',
        date_format='YYYY',
        include_year=1,
        padding_length=5
    )
    
    # Section 1: Request Details
    section1_id = create_form_section({
        'template_id': template_id,
        'section_code': 'REQ_DETAILS',
        'title': 'Request Details',
        'title_ar': 'تفاصيل الطلب',
        'description': 'Basic information about this request',
        'section_order': 0,
        'is_collapsible': 1,
        'is_required': 1
    })
    
    # Request Type
    create_form_field({
        'section_id': section1_id,
        'field_code': 'request_type',
        'field_type': 'dropdown',
        'label': 'Request Type',
        'label_ar': 'نوع الطلب',
        'field_order': 0,
        'is_required': 1
    })
    # Add options for request type
    with get_db_context() as db:
        field = db.execute("SELECT id FROM form_fields WHERE section_id = ? AND field_code = 'request_type'", (section1_id,)).fetchone()
        if field:
            for idx, (val, lbl, lbl_ar) in enumerate([
                ('item_request', 'Item Request', 'طلب أصناف'),
                ('stock_transfer', 'Stock Transfer', 'نقل مخزون'),
                ('equipment_request', 'Equipment Request', 'طلب معدات'),
                ('material_request', 'Material Request', 'طلب مواد'),
            ]):
                db.execute("""
                    INSERT INTO field_options (field_id, option_value, option_label, option_label_ar, option_order, is_default)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (field['id'], val, lbl, lbl_ar, idx, 1 if idx == 0 else 0))
            db.commit()
    
    # Requested By (auto-filled)
    create_form_field({
        'section_id': section1_id,
        'field_code': 'requested_by',
        'field_type': 'user_picker',
        'label': 'Requested By',
        'label_ar': 'مطلوب من',
        'field_order': 1,
        'is_required': 1
    })
    
    # Department
    create_form_field({
        'section_id': section1_id,
        'field_code': 'department',
        'field_type': 'department_picker',
        'label': 'Department',
        'label_ar': 'القسم',
        'field_order': 2,
        'is_required': 1
    })
    
    # Requested Date
    create_form_field({
        'section_id': section1_id,
        'field_code': 'request_date',
        'field_type': 'date',
        'label': 'Request Date',
        'label_ar': 'تاريخ الطلب',
        'field_order': 3,
        'is_required': 1
    })
    
    # Priority
    create_form_field({
        'section_id': section1_id,
        'field_code': 'priority',
        'field_type': 'radio',
        'label': 'Priority',
        'label_ar': 'الأولوية',
        'field_order': 4
    })
    with get_db_context() as db:
        field = db.execute("SELECT id FROM form_fields WHERE section_id = ? AND field_code = 'priority'", (section1_id,)).fetchone()
        if field:
            for idx, (val, lbl) in enumerate([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')]):
                db.execute("""
                    INSERT INTO field_options (field_id, option_value, option_label, option_order, is_default)
                    VALUES (?, ?, ?, ?, ?)
                """, (field['id'], val, lbl.title(), idx, 1 if val == 'medium' else 0))
            db.commit()
    
    # Section 2: Items Requested (Table)
    section2_id = create_form_section({
        'template_id': template_id,
        'section_code': 'ITEMS',
        'title': 'Items Requested',
        'title_ar': 'الأصناف المطلوبة',
        'description': 'List of items being requested',
        'section_order': 1,
        'is_collapsible': 1,
        'is_required': 1
    })
    
    # Items Table
    items_table_id = create_form_field({
        'section_id': section2_id,
        'field_code': 'requested_items',
        'field_type': 'table',
        'label': 'Requested Items',
        'label_ar': 'الأصناف المطلوبة',
        'field_order': 0,
        'is_required': 1
    })
    
    # Table columns
    with get_db_context() as db:
        field = db.execute("SELECT id FROM form_fields WHERE section_id = ? AND field_code = 'requested_items'", (section2_id,)).fetchone()
        if field:
            columns = [
                ('item_code', 'Item Code', 'كود الصنف', 'text', 50, 1),
                ('item_name', 'Item Name', 'اسم الصنف', 'text', 150, 1),
                ('quantity', 'Quantity', 'الكمية', 'number', 80, 1),
                ('unit', 'Unit', 'الوحدة', 'text', 60, 1),
                ('notes', 'Notes', 'ملاحظات', 'text', 100, 0),
            ]
            for idx, (code, lbl, lbl_ar, typ, width, req) in enumerate(columns):
                db.execute("""
                    INSERT INTO table_columns (field_id, column_code, column_label, column_label_ar, column_type, column_order, column_width, is_required)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (field['id'], code, lbl, lbl_ar, typ, idx, width, req))
            db.commit()
    
    # Section 3: Justification
    section3_id = create_form_section({
        'template_id': template_id,
        'section_code': 'JUSTIFICATION',
        'title': 'Justification & Notes',
        'title_ar': 'المبررات والملاحظات',
        'section_order': 2,
        'is_collapsible': 1
    })
    
    create_form_field({
        'section_id': section3_id,
        'field_code': 'reason',
        'field_type': 'textarea',
        'label': 'Reason for Request',
        'label_ar': 'سبب الطلب',
        'field_order': 0,
        'is_required': 1
    })
    
    create_form_field({
        'section_id': section3_id,
        'field_code': 'additional_notes',
        'field_type': 'textarea',
        'label': 'Additional Notes',
        'label_ar': 'ملاحظات إضافية',
        'field_order': 1
    })
    
    print(f"Created Warehouse Request Form template (ID: {template_id})")
    return template_id


def seed_leave_request_form():
    """Seed Leave Request Form template."""
    existing = get_form_templates(status=None)
    for t in existing:
        if t.get('template_code') == 'HR-LEAVE':
            return t['id']
    
    template_id = create_form_template({
        'template_code': 'HR-LEAVE',
        'form_title': 'Leave Request Form',
        'form_title_ar': 'نموذج طلب إجازة',
        'description': 'Standard form for employee leave requests',
        'purpose': 'Request various types of leave',
        'department': 'hr',
        'category': 'Leave',
        'status': 'published',
        'allow_draft': 1,
        'allow_cancel': 1,
        'numbering_prefix': 'HR-LEAVE',
        'numbering_date_format': 'YYYY',
        'visibility': 'internal'
    })
    
    create_numbering_rule(
        template_id=template_id,
        prefix='HR-LEAVE',
        date_format='YYYY',
        include_year=1,
        padding_length=5
    )
    
    # Section 1: Employee Info
    section1_id = create_form_section({
        'template_id': template_id,
        'section_code': 'EMP_INFO',
        'title': 'Employee Information',
        'title_ar': 'معلومات الموظف',
        'section_order': 0
    })
    
    create_form_field({
        'section_id': section1_id,
        'field_code': 'employee_name',
        'field_type': 'text',
        'label': 'Employee Name',
        'label_ar': 'اسم الموظف',
        'field_order': 0,
        'is_required': 1
    })
    
    create_form_field({
        'section_id': section1_id,
        'field_code': 'employee_id',
        'field_type': 'text',
        'label': 'Employee ID',
        'label_ar': 'رقم الموظف',
        'field_order': 1,
        'is_required': 1
    })
    
    create_form_field({
        'section_id': section1_id,
        'field_code': 'department',
        'field_type': 'department_picker',
        'label': 'Department',
        'label_ar': 'القسم',
        'field_order': 2,
        'is_required': 1
    })
    
    # Section 2: Leave Details
    section2_id = create_form_section({
        'template_id': template_id,
        'section_code': 'LEAVE_DETAILS',
        'title': 'Leave Details',
        'title_ar': 'تفاصيل الإجازة',
        'section_order': 1
    })
    
    create_form_field({
        'section_id': section2_id,
        'field_code': 'leave_type',
        'field_type': 'dropdown',
        'label': 'Leave Type',
        'label_ar': 'نوع الإجازة',
        'field_order': 0,
        'is_required': 1
    })
    with get_db_context() as db:
        field = db.execute("SELECT id FROM form_fields WHERE section_id = ? AND field_code = 'leave_type'", (section2_id,)).fetchone()
        if field:
            for idx, (val, lbl, lbl_ar) in enumerate([
                ('annual', 'Annual Leave', 'إجازة سنوية'),
                ('sick', 'Sick Leave', 'إجازة مرضية'),
                ('personal', 'Personal Leave', 'إجازة شخصية'),
                ('emergency', 'Emergency Leave', 'إجازة طارئة'),
                ('unpaid', 'Unpaid Leave', 'إجازة بدون أجر'),
            ]):
                db.execute("""
                    INSERT INTO field_options (field_id, option_value, option_label, option_label_ar, option_order, is_default)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (field['id'], val, lbl, lbl_ar, idx, 1 if idx == 0 else 0))
            db.commit()
    
    create_form_field({
        'section_id': section2_id,
        'field_code': 'start_date',
        'field_type': 'date',
        'label': 'Start Date',
        'label_ar': 'تاريخ البداية',
        'field_order': 1,
        'is_required': 1
    })
    
    create_form_field({
        'section_id': section2_id,
        'field_code': 'end_date',
        'field_type': 'date',
        'label': 'End Date',
        'label_ar': 'تاريخ النهاية',
        'field_order': 2,
        'is_required': 1
    })
    
    create_form_field({
        'section_id': section2_id,
        'field_code': 'total_days',
        'field_type': 'number',
        'label': 'Total Days',
        'label_ar': 'إجمالي الأيام',
        'field_order': 3,
        'is_required': 1
    })
    
    create_form_field({
        'section_id': section2_id,
        'field_code': 'reason',
        'field_type': 'textarea',
        'label': 'Reason for Leave',
        'label_ar': 'سبب الإجازة',
        'field_order': 4,
        'is_required': 1
    })
    
    # Section 3: Coverage
    section3_id = create_form_section({
        'template_id': template_id,
        'section_code': 'COVERAGE',
        'title': 'Work Coverage',
        'title_ar': 'تغطية العمل',
        'section_order': 2
    })
    
    create_form_field({
        'section_id': section3_id,
        'field_code': 'coverage_assigned_to',
        'field_type': 'user_picker',
        'label': 'Coverage Assigned To',
        'label_ar': 'تغطية العمل بواسطة',
        'field_order': 0,
        'is_required': 1
    })
    
    create_form_field({
        'section_id': section3_id,
        'field_code': 'handover_notes',
        'field_type': 'textarea',
        'label': 'Handover Notes',
        'label_ar': 'ملاحظات التسليم',
        'field_order': 1
    })
    
    print(f"Created Leave Request Form template (ID: {template_id})")
    return template_id


def seed_maintenance_request_form():
    """Seed Maintenance Request Form template."""
    existing = get_form_templates(status=None)
    for t in existing:
        if t.get('template_code') == 'MAINT-REQ':
            return t['id']
    
    template_id = create_form_template({
        'template_code': 'MAINT-REQ',
        'form_title': 'Maintenance Request Form',
        'form_title_ar': 'نموذج طلب صيانة',
        'description': 'Request maintenance or repair work for equipment, facilities, or infrastructure.',
        'purpose': 'Submit maintenance and repair requests',
        'department': 'maintenance',
        'category': 'Request',
        'subcategory': 'Maintenance',
        'status': 'published',
        'allow_draft': 1,
        'allow_cancel': 1,
        'numbering_prefix': 'MAINT',
        'numbering_date_format': 'YYYY',
        'visibility': 'internal'
    })
    
    create_numbering_rule(
        template_id=template_id,
        prefix='MAINT',
        date_format='YYYY',
        include_year=1,
        padding_length=5
    )
    
    # Section 1: Request Info
    section1_id = create_form_section({
        'template_id': template_id,
        'section_code': 'REQ_INFO',
        'title': 'Request Information',
        'title_ar': 'معلومات الطلب',
        'section_order': 0
    })
    
    create_form_field({
        'section_id': section1_id,
        'field_code': 'request_type',
        'field_type': 'dropdown',
        'label': 'Request Type',
        'label_ar': 'نوع الطلب',
        'field_order': 0,
        'is_required': 1
    })
    with get_db_context() as db:
        field = db.execute("SELECT id FROM form_fields WHERE section_id = ? AND field_code = 'request_type'", (section1_id,)).fetchone()
        if field:
            for idx, (val, lbl) in enumerate([
                ('repair', 'Repair'), ('preventive', 'Preventive Maintenance'),
                ('emergency', 'Emergency'), ('inspection', 'Inspection')
            ]):
                db.execute("""
                    INSERT INTO field_options (field_id, option_value, option_label, option_order, is_default)
                    VALUES (?, ?, ?, ?, ?)
                """, (field['id'], val, lbl, idx, 1 if idx == 0 else 0))
            db.commit()
    
    create_form_field({
        'section_id': section1_id,
        'field_code': 'location',
        'field_type': 'text',
        'label': 'Location / Equipment ID',
        'label_ar': 'الموقع / رقم المعدة',
        'field_order': 1,
        'is_required': 1
    })
    
    create_form_field({
        'section_id': section1_id,
        'field_code': 'priority',
        'field_type': 'radio',
        'label': 'Priority',
        'label_ar': 'الأولوية',
        'field_order': 2
    })
    with get_db_context() as db:
        field = db.execute("SELECT id FROM form_fields WHERE section_id = ? AND field_code = 'priority'", (section1_id,)).fetchone()
        if field:
            for idx, (val, lbl) in enumerate([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')]):
                db.execute("""
                    INSERT INTO field_options (field_id, option_value, option_label, option_order, is_default)
                    VALUES (?, ?, ?, ?, ?)
                """, (field['id'], val, lbl.title(), idx, 1 if val == 'medium' else 0))
            db.commit()
    
    # Section 2: Description
    section2_id = create_form_section({
        'template_id': template_id,
        'section_code': 'DESCRIPTION',
        'title': 'Problem Description',
        'title_ar': 'وصف المشكلة',
        'section_order': 1
    })
    
    create_form_field({
        'section_id': section2_id,
        'field_code': 'problem_description',
        'field_type': 'textarea',
        'label': 'Problem Description',
        'label_ar': 'وصف المشكلة',
        'field_order': 0,
        'is_required': 1
    })
    
    create_form_field({
        'section_id': section2_id,
        'field_code': 'photos',
        'field_type': 'image',
        'label': 'Photos (if applicable)',
        'label_ar': 'صور (إن وجدت)',
        'field_order': 1
    })
    
    create_form_field({
        'section_id': section2_id,
        'field_code': 'desired_date',
        'field_type': 'date',
        'label': 'Desired Completion Date',
        'label_ar': 'تاريخ الإنجاز المطلوب',
        'field_order': 2
    })
    
    print(f"Created Maintenance Request Form template (ID: {template_id})")
    return template_id


def seed_purchase_request_form():
    """Seed Purchase Request Form template."""
    existing = get_form_templates(status=None)
    for t in existing:
        if t.get('template_code') == 'PUR-REQ':
            return t['id']
    
    template_id = create_form_template({
        'template_code': 'PUR-REQ',
        'form_title': 'Purchase Request Form',
        'form_title_ar': 'نموذج طلب شراء',
        'description': 'Request purchase of items, materials, or services.',
        'purpose': 'Submit purchase requests for approval',
        'department': 'procurement',
        'category': 'Request',
        'subcategory': 'Purchase',
        'status': 'published',
        'allow_draft': 1,
        'allow_cancel': 1,
        'require_attachment': 1,
        'numbering_prefix': 'PUR',
        'numbering_date_format': 'YYYY',
        'visibility': 'internal'
    })
    
    create_numbering_rule(
        template_id=template_id,
        prefix='PUR',
        date_format='YYYY',
        include_year=1,
        padding_length=5
    )
    
    # Section 1: Request Info
    section1_id = create_form_section({
        'template_id': template_id,
        'section_code': 'REQ_INFO',
        'title': 'Request Information',
        'title_ar': 'معلومات الطلب',
        'section_order': 0
    })
    
    create_form_field({
        'section_id': section1_id,
        'field_code': 'requested_by',
        'field_type': 'user_picker',
        'label': 'Requested By',
        'label_ar': 'مطلوب من',
        'field_order': 0,
        'is_required': 1
    })
    
    create_form_field({
        'section_id': section1_id,
        'field_code': 'department',
        'field_type': 'department_picker',
        'label': 'Department',
        'label_ar': 'القسم',
        'field_order': 1,
        'is_required': 1
    })
    
    create_form_field({
        'section_id': section1_id,
        'field_code': 'request_date',
        'field_type': 'date',
        'label': 'Request Date',
        'label_ar': 'تاريخ الطلب',
        'field_order': 2,
        'is_required': 1
    })
    
    create_form_field({
        'section_id': section1_id,
        'field_code': 'need_by_date',
        'field_type': 'date',
        'label': 'Need By Date',
        'label_ar': 'تاريخ الحاجة',
        'field_order': 3,
        'is_required': 1
    })
    
    # Section 2: Items
    section2_id = create_form_section({
        'template_id': template_id,
        'section_code': 'ITEMS',
        'title': 'Items to Purchase',
        'title_ar': 'الأصناف المراد شراؤها',
        'section_order': 1
    })
    
    items_table_id = create_form_field({
        'section_id': section2_id,
        'field_code': 'purchase_items',
        'field_type': 'table',
        'label': 'Purchase Items',
        'label_ar': 'أصناف الشراء',
        'field_order': 0,
        'is_required': 1
    })
    
    with get_db_context() as db:
        field = db.execute("SELECT id FROM form_fields WHERE section_id = ? AND field_code = 'purchase_items'", (section2_id,)).fetchone()
        if field:
            columns = [
                ('item_description', 'Description', 'الوصف', 'text', 200, 1),
                ('quantity', 'Qty', 'الكمية', 'number', 60, 1),
                ('unit', 'Unit', 'الوحدة', 'text', 60, 1),
                ('estimated_cost', 'Est. Cost', 'التكلفة المقدرة', 'decimal', 80, 1),
                ('supplier', 'Supplier', 'المورد', 'text', 100, 0),
            ]
            for idx, (code, lbl, lbl_ar, typ, width, req) in enumerate(columns):
                db.execute("""
                    INSERT INTO table_columns (field_id, column_code, column_label, column_label_ar, column_type, column_order, column_width, is_required)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (field['id'], code, lbl, lbl_ar, typ, idx, width, req))
            db.commit()
    
    # Section 3: Justification
    section3_id = create_form_section({
        'template_id': template_id,
        'section_code': 'JUST',
        'title': 'Justification',
        'title_ar': 'المبررات',
        'section_order': 2
    })
    
    create_form_field({
        'section_id': section3_id,
        'field_code': 'justification',
        'field_type': 'textarea',
        'label': 'Business Justification',
        'label_ar': 'المبرر التجاري',
        'field_order': 0,
        'is_required': 1
    })
    
    create_form_field({
        'section_id': section3_id,
        'field_code': 'budget_code',
        'field_type': 'text',
        'label': 'Budget Code / Cost Center',
        'label_ar': 'رمز الميزانية',
        'field_order': 1,
        'is_required': 1
    })
    
    create_form_field({
        'section_id': section3_id,
        'field_code': 'attachment',
        'field_type': 'file',
        'label': 'Supporting Documents',
        'label_ar': 'المستندات الداعمة',
        'field_order': 2
    })
    
    print(f"Created Purchase Request Form template (ID: {template_id})")
    return template_id


def seed_expense_approval_form():
    """Seed Expense Approval Form template."""
    existing = get_form_templates(status=None)
    for t in existing:
        if t.get('template_code') == 'EXP-APP':
            return t['id']

    template_id = create_form_template({
        'template_code': 'EXP-APP',
        'form_title': 'Expense Approval Form',
        'form_title_ar': 'نموذج اعتماد المصروفات',
        'description': 'Submit expense reports for reimbursement approval.',
        'purpose': 'Submit expense reports for reimbursement',
        'department': 'finance',
        'category': 'Finance',
        'subcategory': 'Expenses',
        'status': 'published',
        'allow_draft': 1,
        'allow_cancel': 1,
        'require_attachment': 1,
        'numbering_prefix': 'EXP',
        'visibility': 'internal'
    })

    create_numbering_rule(template_id, prefix='EXP', date_format='YYYY', include_year=1, padding_length=5)

    # Section 1: Employee Info
    section1_id = create_form_section({
        'template_id': template_id, 'section_code': 'EMP', 'title': 'Employee Information',
        'section_order': 0
    })

    create_form_field({
        'section_id': section1_id, 'field_code': 'employee_name', 'field_type': 'text',
        'label': 'Employee Name', 'field_order': 0, 'is_required': 1
    })
    create_form_field({
        'section_id': section1_id, 'field_code': 'department', 'field_type': 'department_picker',
        'label': 'Department', 'field_order': 1, 'is_required': 1
    })
    create_form_field({
        'section_id': section1_id, 'field_code': 'expense_date', 'field_type': 'date',
        'label': 'Expense Date', 'field_order': 2, 'is_required': 1
    })

    # Section 2: Expense Lines
    section2_id = create_form_section({
        'template_id': template_id, 'section_code': 'EXPENSES', 'title': 'Expense Details',
        'section_order': 1
    })

    expense_table_id = create_form_field({
        'section_id': section2_id, 'field_code': 'expense_lines', 'field_type': 'table',
        'label': 'Expense Items', 'field_order': 0, 'is_required': 1
    })

    with get_db_context() as db:
        field = db.execute("SELECT id FROM form_fields WHERE section_id = ? AND field_code = 'expense_lines'", (section2_id,)).fetchone()
        if field:
            columns = [
                ('date', 'Date', 'التاريخ', 'date', 100, 1),
                ('category', 'Category', 'الفئة', 'dropdown', 100, 1),
                ('description', 'Description', 'الوصف', 'text', 150, 1),
                ('amount', 'Amount', 'المبلغ', 'decimal', 80, 1),
                ('receipt', 'Receipt #', 'الإيصال', 'text', 80, 0),
            ]
            for idx, (code, lbl, lbl_ar, typ, width, req) in enumerate(columns):
                db.execute("""
                    INSERT INTO table_columns (field_id, column_code, column_label, column_label_ar, column_type, column_order, column_width, is_required)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (field['id'], code, lbl, lbl_ar, typ, idx, width, req))
            db.commit()

    # Section 3: Justification
    section3_id = create_form_section({
        'template_id': template_id, 'section_code': 'JUST', 'title': 'Justification',
        'section_order': 2
    })

    create_form_field({
        'section_id': section3_id, 'field_code': 'total_amount', 'field_type': 'decimal',
        'label': 'Total Amount', 'field_order': 0, 'is_required': 1
    })
    create_form_field({
        'section_id': section3_id, 'field_code': 'justification', 'field_type': 'textarea',
        'label': 'Business Justification', 'field_order': 1, 'is_required': 1
    })
    create_form_field({
        'section_id': section3_id, 'field_code': 'attachment', 'field_type': 'file',
        'label': 'Receipts', 'field_order': 2, 'is_required': 1
    })

    print(f"Created Expense Approval Form template (ID: {template_id})")
    return template_id


def seed_incident_report_form():
    """Seed Incident Report Form template."""
    existing = get_form_templates(status=None)
    for t in existing:
        if t.get('template_code') == 'INC-RPT':
            return t['id']

    template_id = create_form_template({
        'template_code': 'INC-RPT',
        'form_title': 'Incident Report Form',
        'form_title_ar': 'نموذج تقريرincident',
        'description': 'Report workplace incidents, accidents, or safety concerns.',
        'purpose': 'Report workplace incidents',
        'department': 'safety',
        'category': 'Safety',
        'subcategory': 'Incidents',
        'status': 'published',
        'allow_draft': 1,
        'allow_cancel': 0,
        'require_attachment': 1,
        'numbering_prefix': 'INC',
        'visibility': 'internal'
    })

    create_numbering_rule(template_id, prefix='INC', date_format='YYYY', include_year=1, padding_length=5)

    # Section 1: Incident Details
    section1_id = create_form_section({
        'template_id': template_id, 'section_code': 'INCIDENT', 'title': 'Incident Details',
        'section_order': 0
    })

    create_form_field({
        'section_id': section1_id, 'field_code': 'incident_date', 'field_type': 'datetime',
        'label': 'Date & Time of Incident', 'field_order': 0, 'is_required': 1
    })
    create_form_field({
        'section_id': section1_id, 'field_code': 'location', 'field_type': 'text',
        'label': 'Location', 'field_order': 1, 'is_required': 1
    })
    create_form_field({
        'section_id': section1_id, 'field_code': 'incident_type', 'field_type': 'dropdown',
        'label': 'Incident Type', 'field_order': 2, 'is_required': 1
    })
    with get_db_context() as db:
        field = db.execute("SELECT id FROM form_fields WHERE section_id = ? AND field_code = 'incident_type'", (section1_id,)).fetchone()
        if field:
            for idx, (val, lbl) in enumerate([
                ('accident', 'Accident'), ('near_miss', 'Near Miss'),
                ('safety_concern', 'Safety Concern'), ('property_damage', 'Property Damage'),
                ('environmental', 'Environmental Incident')
            ]):
                db.execute("""
                    INSERT INTO field_options (field_id, option_value, option_label, option_order, is_default)
                    VALUES (?, ?, ?, ?, ?)
                """, (field['id'], val, lbl, idx, 1 if idx == 0 else 0))
            db.commit()

    create_form_field({
        'section_id': section1_id, 'field_code': 'severity', 'field_type': 'radio',
        'label': 'Severity', 'field_order': 3
    })
    with get_db_context() as db:
        field = db.execute("SELECT id FROM form_fields WHERE section_id = ? AND field_code = 'severity'", (section1_id,)).fetchone()
        if field:
            for idx, (val, lbl) in enumerate([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')]):
                db.execute("""
                    INSERT INTO field_options (field_id, option_value, option_label, option_order, is_default)
                    VALUES (?, ?, ?, ?, ?)
                """, (field['id'], val, lbl, idx, 1 if val == 'medium' else 0))
            db.commit()

    # Section 2: Description
    section2_id = create_form_section({
        'template_id': template_id, 'section_code': 'DESC', 'title': 'Incident Description',
        'section_order': 1
    })

    create_form_field({
        'section_id': section2_id, 'field_code': 'description', 'field_type': 'textarea',
        'label': 'What Happened?', 'field_order': 0, 'is_required': 1
    })
    create_form_field({
        'section_id': section2_id, 'field_code': 'photos', 'field_type': 'image',
        'label': 'Photos', 'field_order': 1
    })

    # Section 3: People Involved
    section3_id = create_form_section({
        'template_id': template_id, 'section_code': 'PEOPLE', 'title': 'People Involved',
        'section_order': 2
    })

    create_form_field({
        'section_id': section3_id, 'field_code': 'injured_persons', 'field_type': 'number',
        'label': 'Number of Injured Persons', 'field_order': 0
    })
    create_form_field({
        'section_id': section3_id, 'field_code': 'witnesses', 'field_type': 'user_picker',
        'label': 'Witnesses', 'field_order': 1
    })

    print(f"Created Incident Report Form template (ID: {template_id})")
    return template_id


def seed_document_request_form():
    """Seed Document Request Form template."""
    existing = get_form_templates(status=None)
    for t in existing:
        if t.get('template_code') == 'DOC-REQ':
            return t['id']

    template_id = create_form_template({
        'template_code': 'DOC-REQ',
        'form_title': 'Document Request Form',
        'form_title_ar': 'نموذج طلب مستند',
        'description': 'Request official documents, certificates, or records.',
        'purpose': 'Request official documents',
        'department': 'general',
        'category': 'Request',
        'subcategory': 'Documents',
        'status': 'published',
        'allow_draft': 1,
        'allow_cancel': 1,
        'numbering_prefix': 'DOC',
        'visibility': 'internal'
    })

    create_numbering_rule(template_id, prefix='DOC', date_format='YYYY', include_year=1, padding_length=5)

    # Section 1: Requester Info
    section1_id = create_form_section({
        'template_id': template_id, 'section_code': 'REQ', 'title': 'Requester Information',
        'section_order': 0
    })

    create_form_field({
        'section_id': section1_id, 'field_code': 'requester_name', 'field_type': 'text',
        'label': 'Full Name', 'field_order': 0, 'is_required': 1
    })
    create_form_field({
        'section_id': section1_id, 'field_code': 'employee_id', 'field_type': 'text',
        'label': 'Employee ID', 'field_order': 1, 'is_required': 1
    })
    create_form_field({
        'section_id': section1_id, 'field_code': 'department', 'field_type': 'department_picker',
        'label': 'Department', 'field_order': 2, 'is_required': 1
    })

    # Section 2: Document Details
    section2_id = create_form_section({
        'template_id': template_id, 'section_code': 'DOC', 'title': 'Document Details',
        'section_order': 1
    })

    create_form_field({
        'section_id': section2_id, 'field_code': 'document_type', 'field_type': 'dropdown',
        'label': 'Document Type', 'field_order': 0, 'is_required': 1
    })
    with get_db_context() as db:
        field = db.execute("SELECT id FROM form_fields WHERE section_id = ? AND field_code = 'document_type'", (section2_id,)).fetchone()
        if field:
            for idx, (val, lbl) in enumerate([
                ('certificate', 'Certificate'), ('employment_letter', 'Employment Letter'),
                ('salary_statement', 'Salary Statement'), ('experience_letter', 'Experience Letter'),
                ('noc', 'No Objection Certificate'), ('other', 'Other')
            ]):
                db.execute("""
                    INSERT INTO field_options (field_id, option_value, option_label, option_order, is_default)
                    VALUES (?, ?, ?, ?, ?)
                """, (field['id'], val, lbl, idx, 1 if idx == 0 else 0))
            db.commit()

    create_form_field({
        'section_id': section2_id, 'field_code': 'purpose', 'field_type': 'textarea',
        'label': 'Purpose / Reason for Request', 'field_order': 1, 'is_required': 1
    })
    create_form_field({
        'section_id': section2_id, 'field_code': 'need_by_date', 'field_type': 'date',
        'label': 'Needed By Date', 'field_order': 2
    })
    create_form_field({
        'section_id': section2_id, 'field_code': 'additional_notes', 'field_type': 'textarea',
        'label': 'Additional Notes', 'field_order': 3
    })

    print(f"Created Document Request Form template (ID: {template_id})")
    return template_id


def seed_overtime_request_form():
    """Seed Overtime Request Form template."""
    existing = get_form_templates(status=None)
    for t in existing:
        if t.get('template_code') == 'OT-REQ':
            return t['id']

    template_id = create_form_template({
        'template_code': 'OT-REQ',
        'form_title': 'Overtime Request Form',
        'form_title_ar': 'نموذج طلب overtime',
        'description': 'Request approval for overtime work.',
        'purpose': 'Request overtime work approval',
        'department': 'hr',
        'category': 'Leave',
        'subcategory': 'Overtime',
        'status': 'published',
        'allow_draft': 1,
        'allow_cancel': 1,
        'numbering_prefix': 'OT',
        'visibility': 'internal'
    })

    create_numbering_rule(template_id, prefix='OT', date_format='YYYY', include_year=1, padding_length=5)

    # Section 1: Employee Info
    section1_id = create_form_section({
        'template_id': template_id, 'section_code': 'EMP', 'title': 'Employee Information',
        'section_order': 0
    })

    create_form_field({
        'section_id': section1_id, 'field_code': 'employee_name', 'field_type': 'text',
        'label': 'Employee Name', 'field_order': 0, 'is_required': 1
    })
    create_form_field({
        'section_id': section1_id, 'field_code': 'employee_id', 'field_type': 'text',
        'label': 'Employee ID', 'field_order': 1, 'is_required': 1
    })
    create_form_field({
        'section_id': section1_id, 'field_code': 'department', 'field_type': 'department_picker',
        'label': 'Department', 'field_order': 2, 'is_required': 1
    })

    # Section 2: Overtime Details
    section2_id = create_form_section({
        'template_id': template_id, 'section_code': 'OT', 'title': 'Overtime Details',
        'section_order': 1
    })

    create_form_field({
        'section_id': section2_id, 'field_code': 'ot_date', 'field_type': 'date',
        'label': 'Date', 'field_order': 0, 'is_required': 1
    })
    create_form_field({
        'section_id': section2_id, 'field_code': 'start_time', 'field_type': 'time',
        'label': 'Start Time', 'field_order': 1, 'is_required': 1
    })
    create_form_field({
        'section_id': section2_id, 'field_code': 'end_time', 'field_type': 'time',
        'label': 'End Time', 'field_order': 2, 'is_required': 1
    })
    create_form_field({
        'section_id': section2_id, 'field_code': 'total_hours', 'field_type': 'decimal',
        'label': 'Total Hours', 'field_order': 3, 'is_required': 1
    })
    create_form_field({
        'section_id': section2_id, 'field_code': 'reason', 'field_type': 'textarea',
        'label': 'Reason for Overtime', 'field_order': 4, 'is_required': 1
    })

    print(f"Created Overtime Request Form template (ID: {template_id})")
    return template_id


def seed_all_form_templates():
    """Seed all sample form templates."""
    print("Initializing Form Builder tables...")
    initialize_form_builder_tables()

    print("Seeding sample form templates...")
    seed_warehouse_request_form()
    seed_leave_request_form()
    seed_maintenance_request_form()
    seed_purchase_request_form()
    seed_expense_approval_form()
    seed_incident_report_form()
    seed_document_request_form()
    seed_overtime_request_form()

    print("All form templates seeded successfully!")


if __name__ == '__main__':
    seed_all_form_templates()
