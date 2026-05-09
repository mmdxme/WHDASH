"""
Form Builder & Form Workflow Engine Models
===========================================
Comprehensive database models for the enterprise Form Builder system.
Supports templates, sections, fields, workflows, approvals, signatures, attachments, and more.
"""

import sqlite3
from database import get_db_context, table_exists, log_audit

# ============================================================================
# FORM BUILDER CONSTANTS
# ============================================================================

# Form Template Status
TEMPLATE_STATUS_DRAFT = 'draft'
TEMPLATE_STATUS_PUBLISHED = 'published'
TEMPLATE_STATUS_ARCHIVED = 'archived'

TEMPLATE_STATUSES = [TEMPLATE_STATUS_DRAFT, TEMPLATE_STATUS_PUBLISHED, TEMPLATE_STATUS_ARCHIVED]

# Form Submission Status
SUBMISSION_STATUS_DRAFT = 'draft'
SUBMISSION_STATUS_SUBMITTED = 'submitted'
SUBMISSION_STATUS_UNDER_REVIEW = 'under_review'
SUBMISSION_STATUS_PENDING_SUPERVISOR = 'pending_supervisor'
SUBMISSION_STATUS_PENDING_MANAGER = 'pending_manager'
SUBMISSION_STATUS_PENDING_DEPARTMENT = 'pending_department'
SUBMISSION_STATUS_PENDING_FINANCE = 'pending_finance'
SUBMISSION_STATUS_PENDING_FINAL = 'pending_final'
SUBMISSION_STATUS_APPROVED = 'approved'
SUBMISSION_STATUS_PARTIALLY_APPROVED = 'partially_approved'
SUBMISSION_STATUS_REJECTED = 'rejected'
SUBMISSION_STATUS_RETURNED = 'returned'
SUBMISSION_STATUS_REVISED = 'revised'
SUBMISSION_STATUS_CANCELLED = 'cancelled'
SUBMISSION_STATUS_CLOSED = 'closed'

SUBMISSION_STATUSES = [
    SUBMISSION_STATUS_DRAFT, SUBMISSION_STATUS_SUBMITTED, SUBMISSION_STATUS_UNDER_REVIEW,
    SUBMISSION_STATUS_PENDING_SUPERVISOR, SUBMISSION_STATUS_PENDING_MANAGER,
    SUBMISSION_STATUS_PENDING_DEPARTMENT, SUBMISSION_STATUS_PENDING_FINANCE,
    SUBMISSION_STATUS_PENDING_FINAL, SUBMISSION_STATUS_APPROVED,
    SUBMISSION_STATUS_PARTIALLY_APPROVED, SUBMISSION_STATUS_REJECTED,
    SUBMISSION_STATUS_RETURNED, SUBMISSION_STATUS_REVISED, SUBMISSION_STATUS_CANCELLED,
    SUBMISSION_STATUS_CLOSED
]

# Status colors for UI
STATUS_COLORS = {
    SUBMISSION_STATUS_DRAFT: 'gray',
    SUBMISSION_STATUS_SUBMITTED: 'blue',
    SUBMISSION_STATUS_UNDER_REVIEW: 'purple',
    SUBMISSION_STATUS_PENDING_SUPERVISOR: 'yellow',
    SUBMISSION_STATUS_PENDING_MANAGER: 'yellow',
    SUBMISSION_STATUS_PENDING_DEPARTMENT: 'yellow',
    SUBMISSION_STATUS_PENDING_FINANCE: 'yellow',
    SUBMISSION_STATUS_PENDING_FINAL: 'yellow',
    SUBMISSION_STATUS_APPROVED: 'green',
    SUBMISSION_STATUS_PARTIALLY_APPROVED: 'teal',
    SUBMISSION_STATUS_REJECTED: 'red',
    SUBMISSION_STATUS_RETURNED: 'orange',
    SUBMISSION_STATUS_REVISED: 'blue',
    SUBMISSION_STATUS_CANCELLED: 'gray',
    SUBMISSION_STATUS_CLOSED: 'green',
}

# Field Types
FIELD_TYPE_TEXT = 'text'
FIELD_TYPE_TEXTAREA = 'textarea'
FIELD_TYPE_NUMBER = 'number'
FIELD_TYPE_DECIMAL = 'decimal'
FIELD_TYPE_CURRENCY = 'currency'
FIELD_TYPE_PERCENTAGE = 'percentage'
FIELD_TYPE_DATE = 'date'
FIELD_TYPE_TIME = 'time'
FIELD_TYPE_DATETIME = 'datetime'
FIELD_TYPE_DROPDOWN = 'dropdown'
FIELD_TYPE_MULTI_SELECT = 'multi_select'
FIELD_TYPE_RADIO = 'radio'
FIELD_TYPE_CHECKBOX = 'checkbox'
FIELD_TYPE_TOGGLE = 'toggle'
FIELD_TYPE_FILE = 'file'
FIELD_TYPE_IMAGE = 'image'
FIELD_TYPE_SIGNATURE = 'signature'
FIELD_TYPE_USER_PICKER = 'user_picker'
FIELD_TYPE_ROLE_PICKER = 'role_picker'
FIELD_TYPE_DEPARTMENT_PICKER = 'department_picker'
FIELD_TYPE_BRANCH_PICKER = 'branch_picker'
FIELD_TYPE_WAREHOUSE_PICKER = 'warehouse_picker'
FIELD_TYPE_EMAIL = 'email'
FIELD_TYPE_PHONE = 'phone'
FIELD_TYPE_URL = 'url'
FIELD_TYPE_BARCODE = 'barcode'
FIELD_TYPE_REFERENCE = 'reference'
FIELD_TYPE_FORMULA = 'formula'
FIELD_TYPE_STATUS = 'status'
FIELD_TYPE_RICH_TEXT = 'rich_text'
FIELD_TYPE_TABLE = 'table'
FIELD_TYPE_ITEM_SELECTOR = 'item_selector'
FIELD_TYPE_SUPPLIER_SELECTOR = 'supplier_selector'
FIELD_TYPE_CUSTOMER_SELECTOR = 'customer_selector'
FIELD_TYPE_RELATED_FORM = 'related_form'
FIELD_TYPE_APPROVAL_DECISION = 'approval_decision'
FIELD_TYPE_COMMENT = 'comment'

FIELD_TYPES = [
    FIELD_TYPE_TEXT, FIELD_TYPE_TEXTAREA, FIELD_TYPE_NUMBER, FIELD_TYPE_DECIMAL,
    FIELD_TYPE_CURRENCY, FIELD_TYPE_PERCENTAGE, FIELD_TYPE_DATE, FIELD_TYPE_TIME,
    FIELD_TYPE_DATETIME, FIELD_TYPE_DROPDOWN, FIELD_TYPE_MULTI_SELECT, FIELD_TYPE_RADIO,
    FIELD_TYPE_CHECKBOX, FIELD_TYPE_TOGGLE, FIELD_TYPE_FILE, FIELD_TYPE_IMAGE,
    FIELD_TYPE_SIGNATURE, FIELD_TYPE_USER_PICKER, FIELD_TYPE_ROLE_PICKER,
    FIELD_TYPE_DEPARTMENT_PICKER, FIELD_TYPE_BRANCH_PICKER, FIELD_TYPE_WAREHOUSE_PICKER,
    FIELD_TYPE_EMAIL, FIELD_TYPE_PHONE, FIELD_TYPE_URL, FIELD_TYPE_BARCODE,
    FIELD_TYPE_REFERENCE, FIELD_TYPE_FORMULA, FIELD_TYPE_STATUS, FIELD_TYPE_RICH_TEXT,
    FIELD_TYPE_TABLE, FIELD_TYPE_ITEM_SELECTOR, FIELD_TYPE_SUPPLIER_SELECTOR,
    FIELD_TYPE_CUSTOMER_SELECTOR, FIELD_TYPE_RELATED_FORM, FIELD_TYPE_APPROVAL_DECISION,
    FIELD_TYPE_COMMENT
]

# Field Type Categories
FIELD_TYPE_CATEGORIES = {
    'Basic Input': [FIELD_TYPE_TEXT, FIELD_TYPE_TEXTAREA, FIELD_TYPE_NUMBER, FIELD_TYPE_DECIMAL, FIELD_TYPE_CURRENCY, FIELD_TYPE_PERCENTAGE],
    'Date & Time': [FIELD_TYPE_DATE, FIELD_TYPE_TIME, FIELD_TYPE_DATETIME],
    'Selection': [FIELD_TYPE_DROPDOWN, FIELD_TYPE_MULTI_SELECT, FIELD_TYPE_RADIO, FIELD_TYPE_CHECKBOX, FIELD_TYPE_TOGGLE],
    'File & Media': [FIELD_TYPE_FILE, FIELD_TYPE_IMAGE],
    'Signature': [FIELD_TYPE_SIGNATURE],
    'Entity Selection': [FIELD_TYPE_USER_PICKER, FIELD_TYPE_ROLE_PICKER, FIELD_TYPE_DEPARTMENT_PICKER, FIELD_TYPE_BRANCH_PICKER, FIELD_TYPE_WAREHOUSE_PICKER, FIELD_TYPE_ITEM_SELECTOR, FIELD_TYPE_SUPPLIER_SELECTOR, FIELD_TYPE_CUSTOMER_SELECTOR],
    'Contact': [FIELD_TYPE_EMAIL, FIELD_TYPE_PHONE, FIELD_TYPE_URL],
    'Advanced': [FIELD_TYPE_BARCODE, FIELD_TYPE_REFERENCE, FIELD_TYPE_FORMULA, FIELD_TYPE_STATUS, FIELD_TYPE_RICH_TEXT],
    'Structured': [FIELD_TYPE_TABLE, FIELD_TYPE_RELATED_FORM],
    'Workflow': [FIELD_TYPE_APPROVAL_DECISION, FIELD_TYPE_COMMENT],
}

# Workflow Step Types
WORKFLOW_STEP_APPROVAL = 'approval'
WORKFLOW_STEP_REVIEW = 'review'
WORKFLOW_STEP_VERIFICATION = 'verification'
WORKFLOW_STEP_NOTIFICATION = 'notification'
WORKFLOW_STEP_AUTOMATED = 'automated'

WORKFLOW_STEP_TYPES = [
    WORKFLOW_STEP_APPROVAL, WORKFLOW_STEP_REVIEW, WORKFLOW_STEP_VERIFICATION,
    WORKFLOW_STEP_NOTIFICATION, WORKFLOW_STEP_AUTOMATED
]

# Workflow Action Types
WORKFLOW_ACTION_SUBMIT = 'submit'
WORKFLOW_ACTION_ASSIGN = 'assign'
WORKFLOW_ACTION_REVIEW = 'review'
WORKFLOW_ACTION_APPROVE = 'approve'
WORKFLOW_ACTION_REJECT = 'reject'
WORKFLOW_ACTION_RETURN = 'return'
WORKFLOW_ACTION_ESCALATE = 'escalate'
WORKFLOW_ACTION_FORWARD = 'forward'
WORKFLOW_ACTION_REASSIGN = 'reassign'
WORKFLOW_ACTION_CLOSE = 'close'
WORKFLOW_ACTION_REOPEN = 'reopen'

WORKFLOW_ACTIONS = [
    WORKFLOW_ACTION_SUBMIT, WORKFLOW_ACTION_ASSIGN, WORKFLOW_ACTION_REVIEW,
    WORKFLOW_ACTION_APPROVE, WORKFLOW_ACTION_REJECT, WORKFLOW_ACTION_RETURN,
    WORKFLOW_ACTION_ESCALATE, WORKFLOW_ACTION_FORWARD, WORKFLOW_ACTION_REASSIGN,
    WORKFLOW_ACTION_CLOSE, WORKFLOW_ACTION_REOPEN
]

# Routing Types
ROUTING_TYPE_SERIAL = 'serial'
ROUTING_TYPE_PARALLEL = 'parallel'
ROUTING_TYPE_CONDITIONAL = 'conditional'

ROUTING_TYPES = [ROUTING_TYPE_SERIAL, ROUTING_TYPE_PARALLEL, ROUTING_TYPE_CONDITIONAL]

# Signature Types
SIGNATURE_TYPE_TYPED = 'typed'
SIGNATURE_TYPE_DRAWN = 'drawn'
SIGNATURE_TYPE_IMAGE = 'image'
SIGNATURE_TYPE_APPROVAL = 'approval'
SIGNATURE_TYPE_AUTHORIZATION = 'authorization'

SIGNATURE_TYPES = [
    SIGNATURE_TYPE_TYPED, SIGNATURE_TYPE_DRAWN, SIGNATURE_TYPE_IMAGE,
    SIGNATURE_TYPE_APPROVAL, SIGNATURE_TYPE_AUTHORIZATION
]

# Attachment Types
ATTACHMENT_TYPE_GENERAL = 'general'
ATTACHMENT_TYPE_PER_SECTION = 'per_section'
ATTACHMENT_TYPE_PER_ROW = 'per_row'
ATTACHMENT_TYPE_APPROVAL_STAGE = 'approval_stage'

ATTACHMENT_TYPES = [
    ATTACHMENT_TYPE_GENERAL, ATTACHMENT_TYPE_PER_SECTION,
    ATTACHMENT_TYPE_PER_ROW, ATTACHMENT_TYPE_APPROVAL_STAGE
]


# ============================================================================
# FORM BUILDER TABLE DEFINITIONS
# ============================================================================

FORM_BUILDER_TABLES = [

    # --------------------------------------------------------------------------
    # 1. FORM TEMPLATES
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS form_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_code TEXT UNIQUE NOT NULL,
        form_title TEXT NOT NULL,
        form_title_ar TEXT,
        description TEXT,
        purpose TEXT,
        department TEXT,
        category TEXT,
        subcategory TEXT,
        owner_id INTEGER,
        version INTEGER DEFAULT 1,
        parent_version_id INTEGER,
        status TEXT DEFAULT 'draft',
        effective_from DATE,
        effective_to DATE,
        language TEXT DEFAULT 'en',
        instructions TEXT,
        default_workflow_id INTEGER,
        allow_draft INTEGER DEFAULT 1,
        allow_save INTEGER DEFAULT 1,
        allow_cancel INTEGER DEFAULT 1,
        allow_withdraw INTEGER DEFAULT 0,
        require_attachment INTEGER DEFAULT 0,
        require_signature INTEGER DEFAULT 0,
        numbering_prefix TEXT,
        numbering_suffix TEXT,
        numbering_sequence INTEGER DEFAULT 1,
        numbering_date_format TEXT DEFAULT 'YYYY',
        visibility TEXT DEFAULT 'internal',
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        published_at TIMESTAMP,
        archived_at TIMESTAMP,
        is_archived INTEGER DEFAULT 0,
        metadata TEXT
    )""",

    # --------------------------------------------------------------------------
    # 2. FORM TEMPLATE VERSIONS
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS form_template_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_id INTEGER NOT NULL,
        version_number INTEGER NOT NULL,
        change_summary TEXT,
        changed_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (template_id) REFERENCES form_templates(id) ON DELETE CASCADE
    )""",

    # --------------------------------------------------------------------------
    # 3. FORM SECTIONS
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS form_sections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_id INTEGER NOT NULL,
        section_code TEXT,
        title TEXT NOT NULL,
        title_ar TEXT,
        description TEXT,
        section_order INTEGER DEFAULT 0,
        is_collapsible INTEGER DEFAULT 1,
        is_repeatable INTEGER DEFAULT 0,
        max_repeat_count INTEGER,
        layout_type TEXT DEFAULT 'vertical',
        column_count INTEGER DEFAULT 1,
        is_visible INTEGER DEFAULT 1,
        is_required INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (template_id) REFERENCES form_templates(id) ON DELETE CASCADE
    )""",

    # --------------------------------------------------------------------------
    # 4. FORM FIELDS
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS form_fields (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        section_id INTEGER NOT NULL,
        field_code TEXT NOT NULL,
        field_type TEXT NOT NULL,
        label TEXT NOT NULL,
        label_ar TEXT,
        placeholder TEXT,
        help_text TEXT,
        default_value TEXT,
        validation_rules TEXT,
        field_order INTEGER DEFAULT 0,
        field_width INTEGER DEFAULT 12,
        is_required INTEGER DEFAULT 0,
        is_readonly INTEGER DEFAULT 0,
        is_hidden INTEGER DEFAULT 0,
        is_unique INTEGER DEFAULT 0,
        min_value TEXT,
        max_value TEXT,
        min_length INTEGER,
        max_length INTEGER,
        accepted_file_types TEXT,
        max_file_size_mb INTEGER,
        data_source TEXT,
        data_source_config TEXT,
        calculation_formula TEXT,
        conditional_logic TEXT,
        metadata TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (section_id) REFERENCES form_sections(id) ON DELETE CASCADE
    )""",

    # --------------------------------------------------------------------------
    # 5. FIELD OPTIONS (for dropdown, radio, multi-select)
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS field_options (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        field_id INTEGER NOT NULL,
        option_value TEXT NOT NULL,
        option_label TEXT NOT NULL,
        option_label_ar TEXT,
        option_order INTEGER DEFAULT 0,
        is_default INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        metadata TEXT,
        FOREIGN KEY (field_id) REFERENCES form_fields(id) ON DELETE CASCADE
    )""",

    # --------------------------------------------------------------------------
    # 6. FIELD RULES (conditional visibility, requiredness, etc.)
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS field_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        field_id INTEGER NOT NULL,
        rule_type TEXT NOT NULL,
        trigger_field_id INTEGER,
        trigger_condition TEXT,
        trigger_value TEXT,
        action TEXT NOT NULL,
        action_value TEXT,
        priority INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (field_id) REFERENCES form_fields(id) ON DELETE CASCADE
    )""",

    # --------------------------------------------------------------------------
    # 7. TABLE FIELD COLUMNS (for table/grid fields)
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS table_columns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        field_id INTEGER NOT NULL,
        column_code TEXT NOT NULL,
        column_label TEXT NOT NULL,
        column_label_ar TEXT,
        column_type TEXT NOT NULL,
        column_order INTEGER DEFAULT 0,
        column_width INTEGER,
        is_required INTEGER DEFAULT 0,
        is_readonly INTEGER DEFAULT 0,
        default_value TEXT,
        min_value TEXT,
        max_value TEXT,
        accepted_file_types TEXT,
        data_source TEXT,
        data_source_config TEXT,
        calculation_formula TEXT,
        metadata TEXT,
        FOREIGN KEY (field_id) REFERENCES form_fields(id) ON DELETE CASCADE
    )""",

    # --------------------------------------------------------------------------
    # 8. FORM WORKFLOWS
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS form_workflows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_id INTEGER NOT NULL,
        workflow_name TEXT NOT NULL,
        workflow_name_ar TEXT,
        description TEXT,
        workflow_type TEXT DEFAULT 'serial',
        is_default INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        requires_all_approvals INTEGER DEFAULT 0,
        allow_partial_approval INTEGER DEFAULT 0,
        return_to_originator INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (template_id) REFERENCES form_templates(id) ON DELETE CASCADE
    )""",

    # --------------------------------------------------------------------------
    # 9. WORKFLOW STEPS
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS workflow_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workflow_id INTEGER NOT NULL,
        step_order INTEGER NOT NULL,
        step_name TEXT NOT NULL,
        step_name_ar TEXT,
        step_type TEXT NOT NULL,
        approver_type TEXT NOT NULL,
        approver_id INTEGER,
        approver_role_id INTEGER,
        approver_department_id INTEGER,
        routing_condition TEXT,
        is_parallel_step INTEGER DEFAULT 0,
        parallel_approvers TEXT,
        sla_hours INTEGER,
        escalation_step_id INTEGER,
        step_status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workflow_id) REFERENCES form_workflows(id) ON DELETE CASCADE
    )""",

    # --------------------------------------------------------------------------
    # 10. WORKFLOW TRANSITIONS
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS workflow_transitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workflow_id INTEGER NOT NULL,
        from_step_id INTEGER NOT NULL,
        to_step_id INTEGER,
        action TEXT NOT NULL,
        condition TEXT,
        transition_order INTEGER DEFAULT 0,
        is_default INTEGER DEFAULT 0,
        notification_template TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workflow_id) REFERENCES form_workflows(id) ON DELETE CASCADE,
        FOREIGN KEY (from_step_id) REFERENCES workflow_steps(id) ON DELETE CASCADE,
        FOREIGN KEY (to_step_id) REFERENCES workflow_steps(id) ON DELETE SET NULL
    )""",

    # --------------------------------------------------------------------------
    # 11. FORM SUBMISSIONS
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS form_submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_id INTEGER NOT NULL,
        submission_number TEXT UNIQUE NOT NULL,
        title TEXT,
        status TEXT DEFAULT 'draft',
        priority TEXT DEFAULT 'medium',
        submitted_by INTEGER,
        submitted_at TIMESTAMP,
        current_step_id INTEGER,
        workflow_id INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        department_id INTEGER,
        warehouse_id INTEGER,
        parent_submission_id INTEGER,
        related_form_id INTEGER,
        due_date DATE,
        completed_at TIMESTAMP,
        cancelled_at TIMESTAMP,
        cancelled_by INTEGER,
        cancellation_reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        metadata TEXT,
        FOREIGN KEY (template_id) REFERENCES form_templates(id),
        FOREIGN KEY (submitted_by) REFERENCES users(id),
        FOREIGN KEY (workflow_id) REFERENCES form_workflows(id),
        FOREIGN KEY (parent_submission_id) REFERENCES form_submissions(id)
    )""",

    # --------------------------------------------------------------------------
    # 12. FORM SUBMISSION VALUES
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS form_submission_values (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id INTEGER NOT NULL,
        field_id INTEGER NOT NULL,
        field_code TEXT NOT NULL,
        field_type TEXT NOT NULL,
        field_value TEXT,
        field_value_text TEXT,
        previous_value TEXT,
        changed_by INTEGER,
        changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (submission_id) REFERENCES form_submissions(id) ON DELETE CASCADE,
        FOREIGN KEY (field_id) REFERENCES form_fields(id),
        FOREIGN KEY (changed_by) REFERENCES users(id)
    )""",

    # --------------------------------------------------------------------------
    # 13. FORM SUBMISSION ROWS (for table fields)
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS form_submission_rows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id INTEGER NOT NULL,
        field_id INTEGER NOT NULL,
        row_index INTEGER NOT NULL,
        row_data TEXT,
        row_status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (submission_id) REFERENCES form_submissions(id) ON DELETE CASCADE,
        FOREIGN KEY (field_id) REFERENCES form_fields(id)
    )""",

    # --------------------------------------------------------------------------
    # 14. FORM SUBMISSION ROW VALUES (for table field cells)
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS form_submission_row_values (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        row_id INTEGER NOT NULL,
        column_id INTEGER NOT NULL,
        column_code TEXT NOT NULL,
        cell_value TEXT,
        cell_value_text TEXT,
        FOREIGN KEY (row_id) REFERENCES form_submission_rows(id) ON DELETE CASCADE
    )""",

    # --------------------------------------------------------------------------
    # 15. FORM SUBMISSION ATTACHMENTS
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS form_submission_attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id INTEGER NOT NULL,
        section_id INTEGER,
        field_id INTEGER,
        row_id INTEGER,
        attachment_type TEXT DEFAULT 'general',
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_type TEXT,
        file_size INTEGER,
        uploaded_by INTEGER,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_required INTEGER DEFAULT 0,
        is_verified INTEGER DEFAULT 0,
        verified_by INTEGER,
        verified_at TIMESTAMP,
        metadata TEXT,
        FOREIGN KEY (submission_id) REFERENCES form_submissions(id) ON DELETE CASCADE
    )""",

    # --------------------------------------------------------------------------
    # 16. FORM STATUS HISTORY
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS form_status_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id INTEGER NOT NULL,
        from_status TEXT,
        to_status TEXT NOT NULL,
        changed_by INTEGER,
        changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        reason TEXT,
        workflow_step_id INTEGER,
        FOREIGN KEY (submission_id) REFERENCES form_submissions(id) ON DELETE CASCADE,
        FOREIGN KEY (changed_by) REFERENCES users(id)
    )""",

    # --------------------------------------------------------------------------
    # 17. FORM COMMENTS
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS form_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id INTEGER NOT NULL,
        parent_comment_id INTEGER,
        comment_type TEXT DEFAULT 'general',
        comment_text TEXT NOT NULL,
        is_internal INTEGER DEFAULT 0,
        mentioned_users TEXT,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (submission_id) REFERENCES form_submissions(id) ON DELETE CASCADE,
        FOREIGN KEY (parent_comment_id) REFERENCES form_comments(id)
    )""",

    # --------------------------------------------------------------------------
    # 18. FORM SIGNATURES
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS form_signatures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id INTEGER NOT NULL,
        signature_type TEXT NOT NULL,
        signed_by INTEGER NOT NULL,
        signed_by_name TEXT,
        signed_by_role TEXT,
        signature_data TEXT,
        signature_image_path TEXT,
        signed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        workflow_step_id INTEGER,
        ip_address TEXT,
        user_agent TEXT,
        is_valid INTEGER DEFAULT 1,
        metadata TEXT,
        FOREIGN KEY (submission_id) REFERENCES form_submissions(id) ON DELETE CASCADE,
        FOREIGN KEY (signed_by) REFERENCES users(id)
    )""",

    # --------------------------------------------------------------------------
    # 19. FORM ASSIGNMENTS
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS form_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id INTEGER NOT NULL,
        workflow_step_id INTEGER,
        assigned_to INTEGER NOT NULL,
        assigned_by INTEGER,
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        due_date DATE,
        status TEXT DEFAULT 'pending',
        completed_at TIMESTAMP,
        delegation_from INTEGER,
        delegation_reason TEXT,
        reassigned_to INTEGER,
        reassigned_at TIMESTAMP,
        is_active INTEGER DEFAULT 1,
        priority TEXT DEFAULT 'medium',
        notes TEXT,
        FOREIGN KEY (submission_id) REFERENCES form_submissions(id) ON DELETE CASCADE,
        FOREIGN KEY (assigned_to) REFERENCES users(id),
        FOREIGN KEY (workflow_step_id) REFERENCES workflow_steps(id)
    )""",

    # --------------------------------------------------------------------------
    # 20. FORM APPROVALS
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS form_approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id INTEGER NOT NULL,
        workflow_step_id INTEGER NOT NULL,
        approval_number INTEGER DEFAULT 1,
        approved_by INTEGER NOT NULL,
        approved_by_name TEXT,
        approval_action TEXT NOT NULL,
        approval_comment TEXT,
        decision_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_delegated INTEGER DEFAULT 0,
        delegated_from INTEGER,
        delegation_approved INTEGER DEFAULT 0,
        sla_breached INTEGER DEFAULT 0,
        sla_breach_at TIMESTAMP,
        is_valid INTEGER DEFAULT 1,
        metadata TEXT,
        FOREIGN KEY (submission_id) REFERENCES form_submissions(id) ON DELETE CASCADE,
        FOREIGN KEY (workflow_step_id) REFERENCES workflow_steps(id),
        FOREIGN KEY (approved_by) REFERENCES users(id)
    )""",

    # --------------------------------------------------------------------------
    # 21. FORM NOTIFICATIONS
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS form_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id INTEGER,
        notification_type TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT,
        recipient_id INTEGER,
        recipient_role_id INTEGER,
        is_read INTEGER DEFAULT 0,
        read_at TIMESTAMP,
        link_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP,
        FOREIGN KEY (submission_id) REFERENCES form_submissions(id) ON DELETE SET NULL
    )""",

    # --------------------------------------------------------------------------
    # 22. NUMBERING RULES
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS form_numbering_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_id INTEGER NOT NULL,
        prefix TEXT,
        suffix TEXT,
        sequence_name TEXT,
        sequence_start INTEGER DEFAULT 1,
        current_sequence INTEGER DEFAULT 0,
        date_format TEXT DEFAULT 'YYYY',
        include_year INTEGER DEFAULT 1,
        include_month INTEGER DEFAULT 0,
        include_day INTEGER DEFAULT 0,
        include_department_code INTEGER DEFAULT 0,
        department_id INTEGER,
        padding_length INTEGER DEFAULT 5,
        separator TEXT DEFAULT '-',
        is_active INTEGER DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (template_id) REFERENCES form_templates(id) ON DELETE CASCADE
    )""",

    # --------------------------------------------------------------------------
    # 23. FORM LINKS / RELATED FORMS
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS form_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_submission_id INTEGER NOT NULL,
        target_submission_id INTEGER NOT NULL,
        link_type TEXT NOT NULL,
        link_label TEXT,
        linked_by INTEGER,
        linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (source_submission_id) REFERENCES form_submissions(id) ON DELETE CASCADE,
        FOREIGN KEY (target_submission_id) REFERENCES form_submissions(id) ON DELETE CASCADE
    )""",

    # --------------------------------------------------------------------------
    # 24. FORM TEMPLATE ACCESS RULES
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS form_template_access (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_id INTEGER NOT NULL,
        access_type TEXT NOT NULL,
        role_id INTEGER,
        department_id INTEGER,
        user_id INTEGER,
        permission TEXT DEFAULT 'view',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (template_id) REFERENCES form_templates(id) ON DELETE CASCADE
    )""",

    # --------------------------------------------------------------------------
    # 25. FORM SUBMISSION ACCESS LOG
    # --------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS form_access_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id INTEGER NOT NULL,
        accessed_by INTEGER NOT NULL,
        access_type TEXT NOT NULL,
        accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT,
        FOREIGN KEY (submission_id) REFERENCES form_submissions(id) ON DELETE CASCADE,
        FOREIGN KEY (accessed_by) REFERENCES users(id)
    )""",
]


# ============================================================================
# INDEX DEFINITIONS
# ============================================================================

FORM_BUILDER_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_form_templates_code ON form_templates(template_code)",
    "CREATE INDEX IF NOT EXISTS idx_form_templates_status ON form_templates(status)",
    "CREATE INDEX IF NOT EXISTS idx_form_templates_department ON form_templates(department)",
    "CREATE INDEX IF NOT EXISTS idx_form_templates_category ON form_templates(category)",
    "CREATE INDEX IF NOT EXISTS idx_form_templates_owner ON form_templates(owner_id)",

    "CREATE INDEX IF NOT EXISTS idx_form_sections_template ON form_sections(template_id)",
    "CREATE INDEX IF NOT EXISTS idx_form_sections_order ON form_sections(template_id, section_order)",

    "CREATE INDEX IF NOT EXISTS idx_form_fields_section ON form_fields(section_id)",
    "CREATE INDEX IF NOT EXISTS idx_form_fields_code ON form_fields(field_code)",
    "CREATE INDEX IF NOT EXISTS idx_form_fields_type ON form_fields(field_type)",

    "CREATE INDEX IF NOT EXISTS idx_field_options_field ON field_options(field_id)",

    "CREATE INDEX IF NOT EXISTS idx_table_columns_field ON table_columns(field_id)",

    "CREATE INDEX IF NOT EXISTS idx_form_workflows_template ON form_workflows(template_id)",

    "CREATE INDEX IF NOT EXISTS idx_workflow_steps_workflow ON workflow_steps(workflow_id)",
    "CREATE INDEX IF NOT EXISTS idx_workflow_steps_order ON workflow_steps(workflow_id, step_order)",

    "CREATE INDEX IF NOT EXISTS idx_workflow_transitions_workflow ON workflow_transitions(workflow_id)",
    "CREATE INDEX IF NOT EXISTS idx_workflow_transitions_from ON workflow_transitions(from_step_id)",

    "CREATE INDEX IF NOT EXISTS idx_form_submissions_template ON form_submissions(template_id)",
    "CREATE INDEX IF NOT EXISTS idx_form_submissions_number ON form_submissions(submission_number)",
    "CREATE INDEX IF NOT EXISTS idx_form_submissions_status ON form_submissions(status)",
    "CREATE INDEX IF NOT EXISTS idx_form_submissions_submitter ON form_submissions(submitted_by)",
    "CREATE INDEX IF NOT EXISTS idx_form_submissions_workflow ON form_submissions(workflow_id)",
    "CREATE INDEX IF NOT EXISTS idx_form_submissions_company ON form_submissions(company_id)",
    "CREATE INDEX IF NOT EXISTS idx_form_submissions_dept ON form_submissions(department_id)",
    "CREATE INDEX IF NOT EXISTS idx_form_submissions_due ON form_submissions(due_date)",

    "CREATE INDEX IF NOT EXISTS idx_form_submission_values_submission ON form_submission_values(submission_id)",
    "CREATE INDEX IF NOT EXISTS idx_form_submission_values_field ON form_submission_values(field_id)",

    "CREATE INDEX IF NOT EXISTS idx_form_submission_rows_submission ON form_submission_rows(submission_id)",
    "CREATE INDEX IF NOT EXISTS idx_form_submission_rows_field ON form_submission_rows(field_id)",

    "CREATE INDEX IF NOT EXISTS idx_form_submission_attachments_submission ON form_submission_attachments(submission_id)",
    "CREATE INDEX IF NOT EXISTS idx_form_submission_attachments_section ON form_submission_attachments(section_id)",
    "CREATE INDEX IF NOT EXISTS idx_form_submission_attachments_field ON form_submission_attachments(field_id)",

    "CREATE INDEX IF NOT EXISTS idx_form_status_history_submission ON form_status_history(submission_id)",
    "CREATE INDEX IF NOT EXISTS idx_form_status_history_date ON form_status_history(changed_at)",

    "CREATE INDEX IF NOT EXISTS idx_form_comments_submission ON form_comments(submission_id)",
    "CREATE INDEX IF NOT EXISTS idx_form_comments_parent ON form_comments(parent_comment_id)",

    "CREATE INDEX IF NOT EXISTS idx_form_signatures_submission ON form_signatures(submission_id)",
    "CREATE INDEX IF NOT EXISTS idx_form_signatures_signer ON form_signatures(signed_by)",

    "CREATE INDEX IF NOT EXISTS idx_form_assignments_submission ON form_assignments(submission_id)",
    "CREATE INDEX IF NOT EXISTS idx_form_assignments_assignee ON form_assignments(assigned_to)",
    "CREATE INDEX IF NOT EXISTS idx_form_assignments_status ON form_assignments(status)",

    "CREATE INDEX IF NOT EXISTS idx_form_approvals_submission ON form_approvals(submission_id)",
    "CREATE INDEX IF NOT EXISTS idx_form_approvals_step ON form_approvals(workflow_step_id)",
    "CREATE INDEX IF NOT EXISTS idx_form_approvals_approver ON form_approvals(approved_by)",

    "CREATE INDEX IF NOT EXISTS idx_form_notifications_recipient ON form_notifications(recipient_id)",
    "CREATE INDEX IF NOT EXISTS idx_form_notifications_type ON form_notifications(notification_type)",
    "CREATE INDEX IF NOT EXISTS idx_form_notifications_submission ON form_notifications(submission_id)",

    "CREATE INDEX IF NOT EXISTS idx_form_numbering_template ON form_numbering_rules(template_id)",

    "CREATE INDEX IF NOT EXISTS idx_form_links_source ON form_links(source_submission_id)",
    "CREATE INDEX IF NOT EXISTS idx_form_links_target ON form_links(target_submission_id)",

    "CREATE INDEX IF NOT EXISTS idx_form_access_template ON form_template_access(template_id)",

    "CREATE INDEX IF NOT EXISTS idx_form_access_log_submission ON form_access_log(submission_id)",
]


# ============================================================================
# FORM BUILDER MODEL FUNCTIONS
# ============================================================================

def initialize_form_builder_tables():
    """
    Initialize all Form Builder tables.
    Called during app startup to ensure all tables exist.
    """
    with get_db_context() as db:
        # Create tables
        for table_sql in FORM_BUILDER_TABLES:
            db.execute(table_sql)
        
        # Create indexes - skip any that fail due to missing columns
        for index_sql in FORM_BUILDER_INDEXES:
            try:
                db.execute(index_sql)
            except sqlite3.OperationalError:
                pass  # Skip indexes on missing columns
        
        db.commit()


def get_form_template(template_id):
    """Get a single form template by ID."""
    from database import get_one
    return get_one("SELECT * FROM form_templates WHERE id = ?", (template_id,))


def get_form_template_by_code(template_code):
    """Get a form template by its code."""
    from database import get_one
    return get_one("SELECT * FROM form_templates WHERE template_code = ?", (template_code,))


def get_form_templates(status=None, department=None, category=None, include_archived=False):
    """
    Get list of form templates with optional filters.
    """
    from database import get_all
    
    sql = "SELECT * FROM form_templates WHERE 1=1"
    params = []
    
    if status:
        sql += " AND status = ?"
        params.append(status)
    
    if department:
        sql += " AND department = ?"
        params.append(department)
    
    if category:
        sql += " AND category = ?"
        params.append(category)
    
    if not include_archived:
        sql += " AND is_archived = 0"
    
    sql += " ORDER BY form_title"
    
    return get_all(sql, params)


def get_template_sections(template_id):
    """Get all sections for a template, ordered."""
    from database import get_all
    return get_all(
        "SELECT * FROM form_sections WHERE template_id = ? ORDER BY section_order",
        (template_id,)
    )


def get_section_fields(section_id):
    """Get all fields for a section, ordered."""
    from database import get_all
    return get_all(
        "SELECT * FROM form_fields WHERE section_id = ? ORDER BY field_order",
        (section_id,)
    )


def get_field_options(field_id):
    """Get all options for a field (dropdown, radio, etc.)."""
    from database import get_all
    return get_all(
        "SELECT * FROM field_options WHERE field_id = ? AND is_active = 1 ORDER BY option_order",
        (field_id,)
    )


def get_table_columns(field_id):
    """Get all columns for a table field."""
    from database import get_all
    return get_all(
        "SELECT * FROM table_columns WHERE field_id = ? ORDER BY column_order",
        (field_id,)
    )


def get_field_rules(field_id):
    """Get all rules for a field."""
    from database import get_all
    return get_all(
        "SELECT * FROM field_rules WHERE field_id = ? AND is_active = 1 ORDER BY priority",
        (field_id,)
    )


def get_template_workflow(template_id):
    """Get the default workflow for a template."""
    from database import get_one
    return get_one(
        "SELECT * FROM form_workflows WHERE template_id = ? AND is_default = 1 AND is_active = 1",
        (template_id,)
    )


def get_workflow_steps(workflow_id):
    """Get all steps for a workflow, ordered."""
    from database import get_all
    return get_all(
        "SELECT * FROM workflow_steps WHERE workflow_id = ? AND step_status = 'active' ORDER BY step_order",
        (workflow_id,)
    )


def get_workflow_transitions(workflow_id):
    """Get all transitions for a workflow."""
    from database import get_all
    return get_all(
        "SELECT * FROM workflow_transitions WHERE workflow_id = ?",
        (workflow_id,)
    )


def get_step_transitions(step_id):
    """Get all transitions from a workflow step."""
    from database import get_all
    return get_all(
        "SELECT * FROM workflow_transitions WHERE from_step_id = ?",
        (step_id,)
    )


def get_current_workflow_step(submission_id):
    """Get the current workflow step ID for a submission."""
    from database import get_one
    result = get_one(
        "SELECT current_step_id FROM form_submissions WHERE id = ?",
        (submission_id,)
    )
    return result['current_step_id'] if result else None


def get_submission(submission_id):
    """Get a single form submission."""
    from database import get_one
    return get_one("SELECT * FROM form_submissions WHERE id = ?", (submission_id,))


def get_submission_values(submission_id):
    """Get all field values for a submission."""
    from database import get_all
    return get_all(
        "SELECT * FROM form_submission_values WHERE submission_id = ?",
        (submission_id,)
    )


def get_submission_rows(submission_id, field_id):
    """Get all rows for a table field in a submission."""
    from database import get_all
    return get_all(
        "SELECT * FROM form_submission_rows WHERE submission_id = ? AND field_id = ? AND row_status = 'active' ORDER BY row_index",
        (submission_id, field_id)
    )


def get_row_values(row_id):
    """Get all cell values for a table row."""
    from database import get_all
    return get_all(
        "SELECT * FROM form_submission_row_values WHERE row_id = ?",
        (row_id,)
    )


def get_submission_attachments(submission_id, section_id=None, field_id=None):
    """Get attachments for a submission."""
    from database import get_all
    
    sql = "SELECT * FROM form_submission_attachments WHERE submission_id = ?"
    params = [submission_id]
    
    if section_id:
        sql += " AND section_id = ?"
        params.append(section_id)
    
    if field_id:
        sql += " AND field_id = ?"
        params.append(field_id)
    
    sql += " ORDER BY uploaded_at"
    
    return get_all(sql, params)


def get_submission_signatures(submission_id):
    """Get all signatures for a submission."""
    from database import get_all
    return get_all(
        "SELECT * FROM form_signatures WHERE submission_id = ? ORDER BY signed_at",
        (submission_id,)
    )


def get_submission_comments(submission_id, include_internal=False):
    """Get all comments for a submission."""
    from database import get_all
    
    sql = "SELECT * FROM form_comments WHERE submission_id = ?"
    if not include_internal:
        sql += " AND is_internal = 0"
    sql += " ORDER BY created_at"
    
    return get_all(sql, (submission_id,))


def get_submission_history(submission_id):
    """Get status history for a submission."""
    from database import get_all
    return get_all(
        "SELECT * FROM form_status_history WHERE submission_id = ? ORDER BY changed_at DESC",
        (submission_id,)
    )


def get_pending_approvals(user_id):
    """Get all submissions pending approval by a user."""
    from database import get_all
    
    sql = """
        SELECT fs.*, ft.form_title, ft.template_code, fa.workflow_step_id, fa.id as approval_id,
               ws.step_name, u.username as submitted_by_name
        FROM form_assignments fa
        JOIN form_submissions fs ON fa.submission_id = fs.id
        JOIN form_templates ft ON fs.template_id = ft.id
        LEFT JOIN workflow_steps ws ON fa.workflow_step_id = ws.id
        LEFT JOIN users u ON fs.submitted_by = u.id
        WHERE fa.assigned_to = ? AND fa.status = 'pending' AND fa.is_active = 1
        ORDER BY fa.due_date ASC, fa.assigned_at ASC
    """
    return get_all(sql, (user_id,))


def get_user_drafts(user_id):
    """Get all draft submissions for a user."""
    from database import get_all
    return get_all(
        """SELECT fs.*, ft.form_title, ft.template_code
           FROM form_submissions fs
           JOIN form_templates ft ON fs.template_id = ft.id
           WHERE fs.submitted_by = ? AND fs.status = 'draft'
           ORDER BY fs.updated_at DESC""",
        (user_id,)
    )


def get_user_submissions(user_id, status=None, limit=50):
    """Get recent submissions by a user."""
    from database import get_all
    
    sql = """
        SELECT fs.*, ft.form_title, ft.template_code
        FROM form_submissions fs
        JOIN form_templates ft ON fs.template_id = ft.id
        WHERE fs.submitted_by = ?
    """
    params = [user_id]
    
    if status:
        sql += " AND fs.status = ?"
        params.append(status)
    
    sql += " ORDER BY fs.created_at DESC LIMIT ?"
    params.append(limit)
    
    return get_all(sql, params)


def get_submission_assignments(submission_id):
    """Get all assignments for a submission."""
    from database import get_all
    return get_all(
        """SELECT fa.*, u.username as assigned_to_name, ws.step_name
           FROM form_assignments fa
           LEFT JOIN users u ON fa.assigned_to = u.id
           LEFT JOIN workflow_steps ws ON fa.workflow_step_id = ws.id
           WHERE fa.submission_id = ?
           ORDER BY fa.assigned_at DESC""",
        (submission_id,)
    )


def get_numbering_rule(template_id):
    """Get the numbering rule for a template."""
    from database import get_one
    return get_one(
        "SELECT * FROM form_numbering_rules WHERE template_id = ? AND is_active = 1",
        (template_id,)
    )


def generate_submission_number(template_id):
    """
    Generate a unique submission number based on the template's numbering rule.
    Returns the generated number string.
    """
    from database import get_db_context
    from datetime import datetime
    
    rule = get_numbering_rule(template_id)
    if not rule:
        # Default numbering if no rule exists
        template = get_form_template(template_id)
        prefix = template.get('numbering_prefix', 'FORM') if template else 'FORM'
        return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    with get_db_context() as db:
        # Get next sequence number
        current = rule['current_sequence'] or 0
        next_seq = current + 1
        
        # Update sequence
        db.execute(
            "UPDATE form_numbering_rules SET current_sequence = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (next_seq, rule['id'])
        )
        db.commit()
    
    # Build the number
    parts = []
    
    if rule['prefix']:
        parts.append(rule['prefix'])
    
    # Year
    if rule['include_year']:
        year_format = rule['date_format'].replace('YYYY', '%Y').replace('YY', '%y')
        parts.append(datetime.now().strftime(year_format))
    
    # Month
    if rule['include_month']:
        parts.append(datetime.now().strftime('%m'))
    
    # Day
    if rule['include_day']:
        parts.append(datetime.now().strftime('%d'))
    
    # Sequence with padding
    seq_str = str(next_seq).zfill(rule['padding_length'])
    parts.append(seq_str)
    
    if rule['suffix']:
        parts.append(rule['suffix'])
    
    separator = rule['separator'] or '-'
    return separator.join(parts)


# ============================================================================
# FORM TEMPLATE CRUD OPERATIONS
# ============================================================================

def create_form_template(data):
    """Create a new form template."""
    from database import get_db_context
    from datetime import datetime
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO form_templates (
                template_code, form_title, form_title_ar, description, purpose,
                department, category, subcategory, owner_id, version, status,
                effective_from, effective_to, language, instructions,
                allow_draft, allow_save, allow_cancel, allow_withdraw,
                require_attachment, require_signature, numbering_prefix,
                numbering_suffix, numbering_date_format, visibility,
                created_by, created_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('template_code'),
            data.get('form_title'),
            data.get('form_title_ar'),
            data.get('description'),
            data.get('purpose'),
            data.get('department'),
            data.get('category'),
            data.get('subcategory'),
            data.get('owner_id'),
            1,  # version
            data.get('status', TEMPLATE_STATUS_DRAFT),
            data.get('effective_from'),
            data.get('effective_to'),
            data.get('language', 'en'),
            data.get('instructions'),
            data.get('allow_draft', 1),
            data.get('allow_save', 1),
            data.get('allow_cancel', 1),
            data.get('allow_withdraw', 0),
            data.get('require_attachment', 0),
            data.get('require_signature', 0),
            data.get('numbering_prefix'),
            data.get('numbering_suffix'),
            data.get('numbering_date_format', 'YYYY'),
            data.get('visibility', 'internal'),
            data.get('created_by'),
            datetime.now().isoformat(),
            data.get('metadata')
        ))
        db.commit()
        return cursor.lastrowid


def update_form_template(template_id, data):
    """Update an existing form template."""
    from database import get_db_context
    from datetime import datetime
    
    fields = []
    values = []
    
    for key in ['form_title', 'form_title_ar', 'description', 'purpose',
                'department', 'category', 'subcategory', 'owner_id',
                'status', 'effective_from', 'effective_to', 'language',
                'instructions', 'allow_draft', 'allow_save', 'allow_cancel',
                'allow_withdraw', 'require_attachment', 'require_signature',
                'numbering_prefix', 'numbering_suffix', 'numbering_date_format',
                'visibility', 'is_archived', 'metadata']:
        if key in data:
            fields.append(f"{key} = ?")
            values.append(data[key])
    
    fields.append("updated_at = ?")
    values.append(datetime.now().isoformat())
    values.append(template_id)
    
    with get_db_context() as db:
        db.execute(
            f"UPDATE form_templates SET {', '.join(fields)} WHERE id = ?",
            values
        )
        db.commit()


def create_form_section(data):
    """Create a new form section."""
    from database import get_db_context
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO form_sections (
                template_id, section_code, title, title_ar, description,
                section_order, is_collapsible, is_repeatable, max_repeat_count,
                layout_type, column_count, is_visible, is_required
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('template_id'),
            data.get('section_code'),
            data.get('title'),
            data.get('title_ar'),
            data.get('description'),
            data.get('section_order', 0),
            data.get('is_collapsible', 1),
            data.get('is_repeatable', 0),
            data.get('max_repeat_count'),
            data.get('layout_type', 'vertical'),
            data.get('column_count', 1),
            data.get('is_visible', 1),
            data.get('is_required', 1)
        ))
        db.commit()
        return cursor.lastrowid


def create_form_field(data):
    """Create a new form field."""
    from database import get_db_context
    import json
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO form_fields (
                section_id, field_code, field_type, label, label_ar,
                placeholder, help_text, default_value, validation_rules,
                field_order, field_width, is_required, is_readonly, is_hidden,
                is_unique, min_value, max_value, min_length, max_length,
                accepted_file_types, max_file_size_mb, data_source,
                data_source_config, calculation_formula, conditional_logic, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('section_id'),
            data.get('field_code'),
            data.get('field_type'),
            data.get('label'),
            data.get('label_ar'),
            data.get('placeholder'),
            data.get('help_text'),
            data.get('default_value'),
            data.get('validation_rules'),
            data.get('field_order', 0),
            data.get('field_width', 12),
            data.get('is_required', 0),
            data.get('is_readonly', 0),
            data.get('is_hidden', 0),
            data.get('is_unique', 0),
            data.get('min_value'),
            data.get('max_value'),
            data.get('min_length'),
            data.get('max_length'),
            data.get('accepted_file_types'),
            data.get('max_file_size_mb'),
            data.get('data_source'),
            json.dumps(data.get('data_source_config')) if data.get('data_source_config') else None,
            data.get('calculation_formula'),
            json.dumps(data.get('conditional_logic')) if data.get('conditional_logic') else None,
            json.dumps(data.get('metadata')) if data.get('metadata') else None
        ))
        db.commit()
        return cursor.lastrowid


def create_field_option(data):
    """Create an option for a dropdown/radio/multi-select field."""
    from database import get_db_context
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO field_options (
                field_id, option_value, option_label, option_label_ar,
                option_order, is_default, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('field_id'),
            data.get('option_value'),
            data.get('option_label'),
            data.get('option_label_ar'),
            data.get('option_order', 0),
            data.get('is_default', 0),
            data.get('is_active', 1)
        ))
        db.commit()
        return cursor.lastrowid


def create_table_column(data):
    """Create a column for a table field."""
    from database import get_db_context
    import json
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO table_columns (
                field_id, column_code, column_label, column_label_ar,
                column_type, column_order, column_width, is_required, is_readonly,
                default_value, min_value, max_value, accepted_file_types,
                data_source, data_source_config, calculation_formula, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('field_id'),
            data.get('column_code'),
            data.get('column_label'),
            data.get('column_label_ar'),
            data.get('column_type'),
            data.get('column_order', 0),
            data.get('column_width'),
            data.get('is_required', 0),
            data.get('is_readonly', 0),
            data.get('default_value'),
            data.get('min_value'),
            data.get('max_value'),
            data.get('accepted_file_types'),
            data.get('data_source'),
            json.dumps(data.get('data_source_config')) if data.get('data_source_config') else None,
            data.get('calculation_formula'),
            json.dumps(data.get('metadata')) if data.get('metadata') else None
        ))
        db.commit()
        return cursor.lastrowid


def create_field_rule(data):
    """Create a rule for a field."""
    from database import get_db_context
    import json
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO field_rules (
                field_id, rule_type, trigger_field_id, trigger_condition,
                trigger_value, action, action_value, priority, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('field_id'),
            data.get('rule_type'),
            data.get('trigger_field_id'),
            data.get('trigger_condition'),
            data.get('trigger_value'),
            data.get('action'),
            data.get('action_value'),
            data.get('priority', 0),
            data.get('is_active', 1)
        ))
        db.commit()
        return cursor.lastrowid


# ============================================================================
# FORM WORKFLOW OPERATIONS
# ============================================================================

def create_form_workflow(data):
    """Create a workflow for a form template."""
    from database import get_db_context
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO form_workflows (
                template_id, workflow_name, workflow_name_ar, description,
                workflow_type, is_default, is_active, requires_all_approvals,
                allow_partial_approval, return_to_originator
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('template_id'),
            data.get('workflow_name'),
            data.get('workflow_name_ar'),
            data.get('description'),
            data.get('workflow_type', ROUTING_TYPE_SERIAL),
            data.get('is_default', 1),
            data.get('is_active', 1),
            data.get('requires_all_approvals', 0),
            data.get('allow_partial_approval', 0),
            data.get('return_to_originator', 0)
        ))
        db.commit()
        return cursor.lastrowid


def create_workflow_step(data):
    """Create a step in a workflow."""
    from database import get_db_context
    import json
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO workflow_steps (
                workflow_id, step_order, step_name, step_name_ar, step_type,
                approver_type, approver_id, approver_role_id, approver_department_id,
                routing_condition, is_parallel_step, parallel_approvers, sla_hours,
                escalation_step_id, step_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('workflow_id'),
            data.get('step_order'),
            data.get('step_name'),
            data.get('step_name_ar'),
            data.get('step_type'),
            data.get('approver_type'),
            data.get('approver_id'),
            data.get('approver_role_id'),
            data.get('approver_department_id'),
            data.get('routing_condition'),
            data.get('is_parallel_step', 0),
            json.dumps(data.get('parallel_approvers')) if data.get('parallel_approvers') else None,
            data.get('sla_hours'),
            data.get('escalation_step_id'),
            data.get('step_status', 'active')
        ))
        db.commit()
        return cursor.lastrowid


def create_workflow_transition(data):
    """Create a transition between workflow steps."""
    from database import get_db_context
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO workflow_transitions (
                workflow_id, from_step_id, to_step_id, action, condition,
                transition_order, is_default, notification_template
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('workflow_id'),
            data.get('from_step_id'),
            data.get('to_step_id'),
            data.get('action'),
            data.get('condition'),
            data.get('transition_order', 0),
            data.get('is_default', 0),
            data.get('notification_template')
        ))
        db.commit()
        return cursor.lastrowid


# ============================================================================
# FORM SUBMISSION OPERATIONS
# ============================================================================

def create_form_submission(data):
    """Create a new form submission."""
    from database import get_db_context
    from datetime import datetime
    
    submission_number = generate_submission_number(data.get('template_id'))
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO form_submissions (
                template_id, submission_number, title, status, priority,
                submitted_by, submitted_at, workflow_id, company_id,
                branch_id, department_id, warehouse_id, parent_submission_id,
                related_form_id, due_date, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('template_id'),
            submission_number,
            data.get('title'),
            data.get('status', SUBMISSION_STATUS_DRAFT),
            data.get('priority', 'medium'),
            data.get('submitted_by'),
            data.get('submitted_at'),
            data.get('workflow_id'),
            data.get('company_id'),
            data.get('branch_id'),
            data.get('department_id'),
            data.get('warehouse_id'),
            data.get('parent_submission_id'),
            data.get('related_form_id'),
            data.get('due_date'),
            data.get('metadata')
        ))
        db.commit()
        return cursor.lastrowid


def save_submission_value(submission_id, field_id, field_code, field_type, field_value, user_id=None):
    """Save or update a field value for a submission."""
    from database import get_db_context
    
    with get_db_context() as db:
        # Check if value already exists
        existing = db.execute(
            "SELECT id, field_value FROM form_submission_values WHERE submission_id = ? AND field_id = ?",
            (submission_id, field_id)
        ).fetchone()
        
        if existing:
            # Update
            db.execute("""
                UPDATE form_submission_values
                SET field_value = ?, field_value_text = ?, previous_value = ?,
                    changed_by = ?, changed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (field_value, str(field_value), existing['field_value'], user_id, existing['id']))
        else:
            # Insert
            db.execute("""
                INSERT INTO form_submission_values (
                    submission_id, field_id, field_code, field_type,
                    field_value, field_value_text, changed_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (submission_id, field_id, field_code, field_type, field_value, str(field_value), user_id))
        
        db.commit()


def add_submission_row(submission_id, field_id, row_index, row_data=None):
    """Add a row to a table field."""
    from database import get_db_context
    import json
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO form_submission_rows (submission_id, field_id, row_index, row_data)
            VALUES (?, ?, ?, ?)
        """, (submission_id, field_id, row_index, json.dumps(row_data) if row_data else None))
        db.commit()
        return cursor.lastrowid


def save_row_value(row_id, column_id, column_code, cell_value):
    """Save a cell value for a table row."""
    from database import get_db_context
    
    with get_db_context() as db:
        # Check if exists
        existing = db.execute(
            "SELECT id FROM form_submission_row_values WHERE row_id = ? AND column_id = ?",
            (row_id, column_id)
        ).fetchone()
        
        if existing:
            db.execute("""
                UPDATE form_submission_row_values SET cell_value = ?, cell_value_text = ?
                WHERE id = ?
            """, (cell_value, str(cell_value), existing['id']))
        else:
            db.execute("""
                INSERT INTO form_submission_row_values (row_id, column_id, column_code, cell_value, cell_value_text)
                VALUES (?, ?, ?, ?, ?)
            """, (row_id, column_id, column_code, cell_value, str(cell_value)))
        
        db.commit()


def update_submission_status(submission_id, new_status, user_id=None, reason=None, workflow_step_id=None):
    """Update the status of a submission and log the change."""
    from database import get_db_context
    from datetime import datetime
    
    with get_db_context() as db:
        # Get current status
        current = db.execute(
            "SELECT status FROM form_submissions WHERE id = ?", (submission_id,)
        ).fetchone()
        
        current_status = current['status'] if current else None
        
        # Update submission status
        db.execute(
            "UPDATE form_submissions SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, datetime.now().isoformat(), submission_id)
        )
        
        # Log status change
        db.execute("""
            INSERT INTO form_status_history (submission_id, from_status, to_status, changed_by, reason, workflow_step_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (submission_id, current_status, new_status, user_id, reason, workflow_step_id))
        
        db.commit()


def assign_submission(submission_id, assigned_to, assigned_by, workflow_step_id=None, due_date=None, priority='medium', notes=None):
    """Assign a submission to a user."""
    from database import get_db_context
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO form_assignments (
                submission_id, workflow_step_id, assigned_to, assigned_by,
                due_date, status, priority, notes
            ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
        """, (submission_id, workflow_step_id, assigned_to, assigned_by, due_date, priority, notes))
        db.commit()
        return cursor.lastrowid


def complete_assignment(assignment_id, user_id):
    """Mark an assignment as completed."""
    from database import get_db_context
    from datetime import datetime
    
    with get_db_context() as db:
        db.execute("""
            UPDATE form_assignments SET status = 'completed', completed_at = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), assignment_id))
        db.commit()


def add_approval(submission_id, workflow_step_id, approved_by, approval_action, approval_comment=None, is_delegated=False, delegated_from=None):
    """Record an approval/rejection/return action."""
    from database import get_db_context
    
    # Get approval number
    with get_db_context() as db:
        count = db.execute(
            "SELECT COUNT(*) as cnt FROM form_approvals WHERE submission_id = ? AND workflow_step_id = ?",
            (submission_id, workflow_step_id)
        ).fetchone()
        approval_number = (count['cnt'] if count else 0) + 1
        
        cursor = db.execute("""
            INSERT INTO form_approvals (
                submission_id, workflow_step_id, approval_number, approved_by,
                approval_action, approval_comment, is_delegated, delegated_from
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (submission_id, workflow_step_id, approval_number, approved_by,
              approval_action, approval_comment, 1 if is_delegated else 0, delegated_from))
        db.commit()
        return cursor.lastrowid


def add_signature(submission_id, signature_type, signed_by, signed_by_name, signature_data=None, signature_image_path=None, workflow_step_id=None, ip_address=None, user_agent=None):
    """Add a signature to a submission."""
    from database import get_db_context
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO form_signatures (
                submission_id, signature_type, signed_by, signed_by_name,
                signature_data, signature_image_path, workflow_step_id,
                ip_address, user_agent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (submission_id, signature_type, signed_by, signed_by_name,
              signature_data, signature_image_path, workflow_step_id, ip_address, user_agent))
        db.commit()
        return cursor.lastrowid


def add_attachment(submission_id, file_name, file_path, file_type, file_size, uploaded_by, section_id=None, field_id=None, row_id=None, attachment_type='general', is_required=0):
    """Add an attachment to a submission."""
    from database import get_db_context
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO form_submission_attachments (
                submission_id, section_id, field_id, row_id, attachment_type,
                file_name, file_path, file_type, file_size, uploaded_by, is_required
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (submission_id, section_id, field_id, row_id, attachment_type,
              file_name, file_path, file_type, file_size, uploaded_by, is_required))
        db.commit()
        return cursor.lastrowid


def add_comment(submission_id, comment_text, created_by, comment_type='general', is_internal=0, parent_comment_id=None, mentioned_users=None):
    """Add a comment to a submission."""
    from database import get_db_context
    import json
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO form_comments (
                submission_id, parent_comment_id, comment_type, comment_text,
                is_internal, mentioned_users, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (submission_id, parent_comment_id, comment_type, comment_text,
              is_internal, json.dumps(mentioned_users) if mentioned_users else None, created_by))
        db.commit()
        return cursor.lastrowid


def create_form_notification(submission_id, notification_type, title, message, recipient_id=None, recipient_role_id=None, link_url=None, expires_at=None):
    """Create a notification for form events."""
    from database import get_db_context
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO form_notifications (
                submission_id, notification_type, title, message,
                recipient_id, recipient_role_id, link_url, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (submission_id, notification_type, title, message,
              recipient_id, recipient_role_id, link_url, expires_at))
        db.commit()
        return cursor.lastrowid


def link_forms(source_submission_id, target_submission_id, link_type, linked_by, link_label=None):
    """Link two form submissions."""
    from database import get_db_context
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO form_links (source_submission_id, target_submission_id, link_type, link_label, linked_by)
            VALUES (?, ?, ?, ?, ?)
        """, (source_submission_id, target_submission_id, link_type, link_label, linked_by))
        db.commit()
        return cursor.lastrowid


def log_form_access(submission_id, accessed_by, access_type, ip_address=None):
    """Log access to a form submission."""
    from database import get_db_context
    
    with get_db_context() as db:
        db.execute("""
            INSERT INTO form_access_log (submission_id, accessed_by, access_type, ip_address)
            VALUES (?, ?, ?, ?)
        """, (submission_id, accessed_by, access_type, ip_address))
        db.commit()


def create_numbering_rule(template_id, prefix, suffix='', sequence_start=1, date_format='YYYY', include_year=1, include_month=0, include_day=0, padding_length=5, separator='-'):
    """Create a numbering rule for a template."""
    from database import get_db_context
    
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO form_numbering_rules (
                template_id, prefix, suffix, sequence_start, current_sequence,
                date_format, include_year, include_month, include_day,
                padding_length, separator, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (template_id, prefix, suffix, sequence_start, sequence_start - 1,
              date_format, include_year, include_month, include_day, padding_length, separator))
        db.commit()
        return cursor.lastrowid


# ============================================================================
# QUERY AND REPORTING FUNCTIONS
# ============================================================================

def search_submissions(template_id=None, status=None, department_id=None, submitted_by=None,
                       date_from=None, date_to=None, search_text=None, assignee_id=None,
                       priority=None, overdue=None, limit=100, offset=0):
    """Search form submissions with filters."""
    from database import get_all
    
    sql = """
        SELECT fs.*, ft.form_title, ft.template_code, u.username as submitted_by_name,
               dept.name as department_name
        FROM form_submissions fs
        JOIN form_templates ft ON fs.template_id = ft.id
        LEFT JOIN users u ON fs.submitted_by = u.id
        LEFT JOIN departments dept ON fs.department_id = dept.id
        WHERE 1=1
    """
    params = []
    
    if template_id:
        sql += " AND fs.template_id = ?"
        params.append(template_id)
    
    if status:
        sql += " AND fs.status = ?"
        params.append(status)
    
    if department_id:
        sql += " AND fs.department_id = ?"
        params.append(department_id)
    
    if submitted_by:
        sql += " AND fs.submitted_by = ?"
        params.append(submitted_by)
    
    if assignee_id:
        sql += " AND EXISTS (SELECT 1 FROM form_assignments fa WHERE fa.submission_id = fs.id AND fa.assigned_to = ? AND fa.is_active = 1)"
        params.append(assignee_id)
    
    if date_from:
        sql += " AND fs.created_at >= ?"
        params.append(date_from)
    
    if date_to:
        sql += " AND fs.created_at <= ?"
        params.append(date_to)
    
    if search_text:
        sql += " AND (fs.submission_number LIKE ? OR ft.form_title LIKE ? OR fs.title LIKE ?)"
        search_pattern = f"%{search_text}%"
        params.extend([search_pattern, search_pattern, search_pattern])
    
    if priority:
        sql += " AND fs.priority = ?"
        params.append(priority)
    
    if overdue:
        sql += " AND fs.due_date < date('now') AND fs.status NOT IN ('approved', 'rejected', 'cancelled', 'closed')"
    
    sql += " ORDER BY fs.created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    return get_all(sql, params)


def get_submission_stats(template_id=None, department_id=None, date_from=None, date_to=None):
    """Get submission statistics."""
    from database import get_all
    
    sql = """
        SELECT 
            fs.status,
            COUNT(*) as count
        FROM form_submissions fs
        JOIN form_templates ft ON fs.template_id = ft.id
        WHERE 1=1
    """
    params = []
    
    if template_id:
        sql += " AND fs.template_id = ?"
        params.append(template_id)
    
    if department_id:
        sql += " AND fs.department_id = ?"
        params.append(department_id)
    
    if date_from:
        sql += " AND fs.created_at >= ?"
        params.append(date_from)
    
    if date_to:
        sql += " AND fs.created_at <= ?"
        params.append(date_to)
    
    sql += " GROUP BY fs.status"
    
    return get_all(sql, params)


def get_template_usage_stats():
    """Get usage statistics for form templates."""
    from database import get_all
    
    sql = """
        SELECT 
            ft.id, ft.form_title, ft.template_code, ft.status,
            COUNT(fs.id) as submission_count,
            SUM(CASE WHEN fs.status = 'approved' THEN 1 ELSE 0 END) as approved_count,
            SUM(CASE WHEN fs.status = 'rejected' THEN 1 ELSE 0 END) as rejected_count,
            SUM(CASE WHEN fs.status = 'pending' THEN 1 ELSE 0 END) as pending_count
        FROM form_templates ft
        LEFT JOIN form_submissions fs ON ft.id = fs.template_id
        GROUP BY ft.id
        ORDER BY submission_count DESC
    """
    return get_all(sql)


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_form_builder():
    """
    Initialize the Form Builder system.
    Called during app startup.
    """
    initialize_form_builder_tables()
