"""
Form Builder Helper Functions
============================
Template helper functions for the Form Builder.
"""

# Field type icons mapping
FIELD_TYPE_ICONS = {
    'text': 'fa-font',
    'textarea': 'fa-align-left',
    'number': 'fa-hashtag',
    'decimal': 'fa-calculator',
    'currency': 'fa-dollar-sign',
    'percentage': 'fa-percent',
    'date': 'fa-calendar',
    'time': 'fa-clock',
    'datetime': 'fa-calendar-alt',
    'dropdown': 'fa-chevron-down',
    'multi_select': 'fa-check-double',
    'radio': 'fa-dot-circle',
    'checkbox': 'fa-check-square',
    'toggle': 'fa-toggle-on',
    'file': 'fa-file',
    'image': 'fa-image',
    'signature': 'fa-signature',
    'user_picker': 'fa-user',
    'role_picker': 'fa-users-cog',
    'department_picker': 'fa-building',
    'branch_picker': 'fa-sitemap',
    'warehouse_picker': 'fa-warehouse',
    'email': 'fa-envelope',
    'phone': 'fa-phone',
    'url': 'fa-link',
    'barcode': 'fa-barcode',
    'reference': 'fa-id-badge',
    'formula': 'fa-function',
    'status': 'fa-flag',
    'rich_text': 'fa-edit',
    'table': 'fa-table',
    'item_selector': 'fa-box',
    'supplier_selector': 'fa-truck',
    'customer_selector': 'fa-user-tie',
    'related_form': 'fa-external-link-square-alt',
    'approval_decision': 'fa-clipboard-check',
    'comment': 'fa-comment',
}


# Field type labels
FIELD_TYPE_LABELS = {
    'text': 'Single Line Text',
    'textarea': 'Multi-Line Text',
    'number': 'Integer Number',
    'decimal': 'Decimal Number',
    'currency': 'Currency',
    'percentage': 'Percentage',
    'date': 'Date',
    'time': 'Time',
    'datetime': 'Date & Time',
    'dropdown': 'Dropdown',
    'multi_select': 'Multi-Select',
    'radio': 'Radio Buttons',
    'checkbox': 'Checkboxes',
    'toggle': 'Toggle/Switch',
    'file': 'File Upload',
    'image': 'Image Upload',
    'signature': 'Signature',
    'user_picker': 'User Picker',
    'role_picker': 'Role Picker',
    'department_picker': 'Department Picker',
    'branch_picker': 'Branch Picker',
    'warehouse_picker': 'Warehouse Picker',
    'email': 'Email Address',
    'phone': 'Phone Number',
    'url': 'URL/Website',
    'barcode': 'Barcode/QR',
    'reference': 'Reference Field',
    'formula': 'Calculated Formula',
    'status': 'Status Display',
    'rich_text': 'Rich Text Editor',
    'table': 'Data Table/Rows',
    'item_selector': 'Item/Product Selector',
    'supplier_selector': 'Supplier Selector',
    'customer_selector': 'Customer Selector',
    'related_form': 'Related Form Link',
    'approval_decision': 'Approval Decision',
    'comment': 'Comment/Notes',
}


def get_field_icon(field_type):
    """Get the Font Awesome icon class for a field type."""
    return FIELD_TYPE_ICONS.get(field_type, 'fa-square')


def get_field_label(field_type):
    """Get the human-readable label for a field type."""
    return FIELD_TYPE_LABELS.get(field_type, field_type.replace('_', ' ').title())


# Register these as Jinja2 globals
def register_form_helpers(app):
    """Register form builder helpers with Flask app."""
    @app.context_processor
    def inject_form_helpers():
        return {
            'get_field_icon': get_field_icon,
            'get_field_label': get_field_label,
        }
