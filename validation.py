"""
Centralized Validation Framework for MMDx
==========================================
Provides consistent validation across all modules.

Usage:
    from validation import Validator, validate_email, validate_required
    
    # Define a validator
    validator = Validator(data)
    validator.required('email', 'Email is required')
    validator.email('email', 'Invalid email format')
    validator.min_length('password', 8, 'Password must be at least 8 characters')
    
    if not validator.is_valid():
        return jsonify({'errors': validator.errors}), 400
    
    # Or use predefined validators
    errors = validate_email(data.get('email'))
    errors = validate_required(data, ['name', 'email', 'password'])
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable


class ValidationError(Exception):
    """Custom validation error with field information."""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class Validator:
    """
    Fluent validation builder.
    
    Usage:
        validator = Validator(data)
        validator.required('email').email('email').min_length('password', 8)
        
        if not validator.is_valid():
            print(validator.errors)
    """
    
    def __init__(self, data: Dict[str, Any]):
        self.data = data or {}
        self.errors: Dict[str, List[str]] = {}
        self._validators: List[Tuple[str, Callable, str]] = []
    
    def _add_error(self, field: str, message: str):
        if field not in self.errors:
            self.errors[field] = []
        if message not in self.errors[field]:
            self.errors[field].append(message)
    
    def _get_value(self, field: str) -> Any:
        """Get field value, supporting dot notation for nested data."""
        if '.' in field:
            parts = field.split('.')
            value = self.data
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return None
            return value
        return self.data.get(field)
    
    def required(self, field: str, message: str = None) -> 'Validator':
        """Field is required and not empty."""
        msg = message or f"{field} is required"
        value = self._get_value(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            self._add_error(field, msg)
        return self
    
    def email(self, field: str, message: str = None) -> 'Validator':
        """Field must be a valid email address."""
        msg = message or "Invalid email format"
        value = self._get_value(field)
        if value and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', str(value)):
            self._add_error(field, msg)
        return self
    
    def phone(self, field: str, message: str = None) -> 'Validator':
        """Field must be a valid phone number."""
        msg = message or "Invalid phone number format"
        value = self._get_value(field)
        if value:
            phone_pattern = r'^[\d\s\-\+\(\)]+$'
            if not re.match(phone_pattern, str(value)) or len(re.sub(r'\D', '', str(value))) < 10:
                self._add_error(field, msg)
        return self
    
    def min_length(self, field: str, length: int, message: str = None) -> 'Validator':
        """Field must have minimum length."""
        msg = message or f"Minimum length is {length} characters"
        value = self._get_value(field)
        if value and len(str(value)) < length:
            self._add_error(field, msg)
        return self
    
    def max_length(self, field: str, length: int, message: str = None) -> 'Validator':
        """Field must have maximum length."""
        msg = message or f"Maximum length is {length} characters"
        value = self._get_value(field)
        if value and len(str(value)) > length:
            self._add_error(field, msg)
        return self
    
    def min_value(self, field: str, min_val: float, message: str = None) -> 'Validator':
        """Field must be at least minimum value."""
        msg = message or f"Minimum value is {min_val}"
        value = self._get_value(field)
        if value is not None:
            try:
                if float(value) < min_val:
                    self._add_error(field, msg)
            except (ValueError, TypeError):
                self._add_error(field, "Invalid numeric value")
        return self
    
    def max_value(self, field: str, max_val: float, message: str = None) -> 'Validator':
        """Field must be at most maximum value."""
        msg = message or f"Maximum value is {max_val}"
        value = self._get_value(field)
        if value is not None:
            try:
                if float(value) > max_val:
                    self._add_error(field, msg)
            except (ValueError, TypeError):
                self._add_error(field, "Invalid numeric value")
        return self
    
    def numeric(self, field: str, message: str = None) -> 'Validator':
        """Field must be a number."""
        msg = message or "Must be a number"
        value = self._get_value(field)
        if value:
            try:
                float(value)
            except (ValueError, TypeError):
                self._add_error(field, msg)
        return self
    
    def integer(self, field: str, message: str = None) -> 'Validator':
        """Field must be an integer."""
        msg = message or "Must be an integer"
        value = self._get_value(field)
        if value:
            try:
                int(value)
            except (ValueError, TypeError):
                self._add_error(field, msg)
        return self
    
    def positive(self, field: str, message: str = None) -> 'Validator':
        """Field must be a positive number."""
        msg = message or "Must be a positive number"
        value = self._get_value(field)
        if value:
            try:
                if float(value) <= 0:
                    self._add_error(field, msg)
            except (ValueError, TypeError):
                self._add_error(field, "Invalid numeric value")
        return self
    
    def in_list(self, field: str, choices: List[Any], message: str = None) -> 'Validator':
        """Field must be one of the choices."""
        msg = message or f"Must be one of: {', '.join(str(c) for c in choices)}"
        value = self._get_value(field)
        if value and value not in choices:
            self._add_error(field, msg)
        return self
    
    def date(self, field: str, message: str = None) -> 'Validator':
        """Field must be a valid date."""
        msg = message or "Invalid date format"
        value = self._get_value(field)
        if value:
            try:
                datetime.strptime(str(value), '%Y-%m-%d')
            except ValueError:
                self._add_error(field, msg)
        return self
    
    def datetime_format(self, field: str, format: str = '%Y-%m-%d %H:%M:%S', message: str = None) -> 'Validator':
        """Field must be a valid datetime in specified format."""
        msg = message or f"Invalid datetime format (expected: {format})"
        value = self._get_value(field)
        if value:
            try:
                datetime.strptime(str(value), format)
            except ValueError:
                self._add_error(field, msg)
        return self
    
    def regex(self, field: str, pattern: str, message: str = None) -> 'Validator':
        """Field must match regex pattern."""
        msg = message or "Invalid format"
        value = self._get_value(field)
        if value and not re.match(pattern, str(value)):
            self._add_error(field, msg)
        return self
    
    def url(self, field: str, message: str = None) -> 'Validator':
        """Field must be a valid URL."""
        msg = message or "Invalid URL format"
        value = self._get_value(field)
        if value:
            url_pattern = r'^https?://[\w\.-]+(?:/[\w\.-]*)*/?$'
            if not re.match(url_pattern, str(value)):
                self._add_error(field, msg)
        return self
    
    def custom(self, field: str, validator_func: Callable[['Validator', Any], bool], message: str) -> 'Validator':
        """Add a custom validation function."""
        value = self._get_value(field)
        if value and not validator_func(self, value):
            self._add_error(field, message)
        return self
    
    def is_valid(self) -> bool:
        """Check if validation passed."""
        return len(self.errors) == 0
    
    def get_errors(self) -> Dict[str, List[str]]:
        """Get all validation errors."""
        return self.errors
    
    def get_first_error(self) -> Optional[str]:
        """Get the first error message."""
        for field, errors in self.errors.items():
            if errors:
                return f"{field}: {errors[0]}"
        return None


# =============================================================================
# PREDEFINED VALIDATORS
# =============================================================================

def validate_email(value: Any) -> Optional[str]:
    """Validate email and return error message if invalid."""
    if not value:
        return None  # Use required() for empty check
    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', str(value)):
        return "Invalid email format"
    return None


def validate_phone(value: Any) -> Optional[str]:
    """Validate phone number and return error message if invalid."""
    if not value:
        return None
    phone_digits = re.sub(r'\D', '', str(value))
    if len(phone_digits) < 10:
        return "Phone number must have at least 10 digits"
    return None


def validate_required(data: Dict, fields: List[str]) -> Dict[str, str]:
    """Validate multiple required fields. Returns dict of field -> error message."""
    errors = {}
    for field in fields:
        if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            errors[field] = f"{field} is required"
    return errors


def validate_customer(data: Dict) -> Validator:
    """Validate customer form data."""
    return (Validator(data)
            .required('name', 'Customer name is required')
            .min_length('name', 2, 'Name must be at least 2 characters')
            .email('email', 'Invalid email format')
            .phone('phone', 'Invalid phone number')
            .max_length('address', 500, 'Address too long'))


def validate_supplier(data: Dict) -> Validator:
    """Validate supplier form data."""
    return (Validator(data)
            .required('name', 'Supplier name is required')
            .min_length('name', 2, 'Name must be at least 2 characters')
            .email('email', 'Invalid email format')
            .phone('phone', 'Invalid phone number')
            .required('contact_person', 'Contact person is required'))


def validate_item(data: Dict) -> Validator:
    """Validate item/product form data."""
    return (Validator(data)
            .required('name', 'Item name is required')
            .min_length('name', 2, 'Name must be at least 2 characters')
            .required('sku', 'SKU is required')
            .max_length('sku', 50, 'SKU too long')
            .numeric('unit_price', 'Unit price must be a number')
            .min_value('unit_price', 0, 'Unit price cannot be negative')
            .positive('quantity', 'Quantity must be positive'))


def validate_sales_order(data: Dict) -> Validator:
    """Validate sales order form data."""
    return (Validator(data)
            .required('customer_id', 'Customer is required')
            .integer('customer_id', 'Invalid customer')
            .required('order_date', 'Order date is required')
            .date('order_date', 'Invalid date format')
            .in_list('status', ['Draft', 'Confirmed', 'Processing', 'Shipped', 'Delivered', 'Canceled'],
                     'Invalid status'))


def validate_purchase_order(data: Dict) -> Validator:
    """Validate purchase order form data."""
    return (Validator(data)
            .required('supplier_id', 'Supplier is required')
            .integer('supplier_id', 'Invalid supplier')
            .required('order_date', 'Order date is required')
            .date('order_date', 'Invalid date format')
            .in_list('status', ['Draft', 'Sent', 'Confirmed', 'Received', 'Canceled'],
                     'Invalid status'))


def validate_asset(data: Dict) -> Validator:
    """Validate asset form data."""
    return (Validator(data)
            .required('name', 'Asset name is required')
            .min_length('name', 2, 'Name must be at least 2 characters')
            .required('asset_code', 'Asset code is required')
            .max_length('asset_code', 50, 'Asset code too long')
            .numeric('acquisition_cost', 'Acquisition cost must be a number')
            .min_value('acquisition_cost', 0, 'Cost cannot be negative'))


def validate_inspection(data: Dict) -> Validator:
    """Validate quality inspection form data."""
    return (Validator(data)
            .required('inspection_type', 'Inspection type is required')
            .in_list('result', ['Pass', 'Fail', 'Conditional'],
                     'Invalid result')
            .required('quantity_inspected', 'Quantity inspected is required')
            .positive('quantity_inspected', 'Quantity must be positive')
            .numeric('quantity_passed', 'Quantity passed must be a number')
            .numeric('quantity_failed', 'Quantity failed must be a number'))


def validate_user(data: Dict) -> Validator:
    """Validate user form data."""
    return (Validator(data)
            .required('username', 'Username is required')
            .min_length('username', 3, 'Username must be at least 3 characters')
            .max_length('username', 50, 'Username too long')
            .regex('username', r'^[\w_]+$', 'Username can only contain letters, numbers, and underscores')
            .required('email', 'Email is required')
            .email('email', 'Invalid email format')
            .required('password', 'Password is required')
            .min_length('password', 8, 'Password must be at least 8 characters'))


def validate_password_reset(data: Dict) -> Validator:
    """Validate password reset form data."""
    return (Validator(data)
            .required('password', 'New password is required')
            .min_length('password', 8, 'Password must be at least 8 characters')
            .required('confirm_password', 'Please confirm your password')
            .custom('confirm_password',
                    lambda v, val: val == data.get('password'),
                    'Passwords do not match'))


def validate_api_key_request(data: Dict) -> Validator:
    """Validate API key creation request."""
    return (Validator(data)
            .required('client_name', 'Client name is required')
            .min_length('client_name', 3, 'Client name too short')
            .required('scopes', 'At least one scope is required'))


def sanitize_html(value: str) -> str:
    """Remove potentially dangerous HTML from input."""
    if not value:
        return value
    # Remove script tags
    value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
    # Remove event handlers
    value = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', value, flags=re.IGNORECASE)
    # Remove javascript: URLs
    value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
    return value


def sanitize_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize all string values in input data."""
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_html(value.strip())
        elif isinstance(value, dict):
            sanitized[key] = sanitize_input(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_html(str(v)) if isinstance(v, str) else v for v in value]
        else:
            sanitized[key] = value
    return sanitized


# =============================================================================
# VALIDATION HELPERS FOR ROUTES
# =============================================================================

def validate_form_fields(data: Dict, rules: List[Dict]) -> Tuple[bool, Dict[str, List[str]]]:
    """
    Validate form data against a list of rules.
    
    Args:
        data: Form data dictionary
        rules: List of rule dicts with keys:
            - field: field name (required)
            - rules: list of rule names (required, email, phone, etc.)
            - message: custom error message (optional)
            - params: additional rule parameters (optional)
    
    Returns:
        Tuple of (is_valid, errors_dict)
    
    Example:
        rules = [
            {'field': 'email', 'rules': ['required', 'email']},
            {'field': 'password', 'rules': ['required', 'min_length'], 'params': {'length': 8}},
        ]
        is_valid, errors = validate_form_fields(request.form, rules)
    """
    validator = Validator(data)
    
    for rule in rules:
        field = rule.get('field')
        rule_list = rule.get('rules', [])
        custom_msg = rule.get('message')
        params = rule.get('params', {})
        
        for r in rule_list:
            if r == 'required':
                validator.required(field, custom_msg)
            elif r == 'email':
                validator.email(field, custom_msg)
            elif r == 'phone':
                validator.phone(field, custom_msg)
            elif r == 'min_length' and 'length' in params:
                validator.min_length(field, params['length'], custom_msg)
            elif r == 'max_length' and 'length' in params:
                validator.max_length(field, params['length'], custom_msg)
            elif r == 'min_value' and 'value' in params:
                validator.min_value(field, params['value'], custom_msg)
            elif r == 'max_value' and 'value' in params:
                validator.max_value(field, params['value'], custom_msg)
            elif r == 'numeric':
                validator.numeric(field, custom_msg)
            elif r == 'integer':
                validator.integer(field, custom_msg)
            elif r == 'positive':
                validator.positive(field, custom_msg)
            elif r == 'date':
                validator.date(field, custom_msg)
            elif r == 'url':
                validator.url(field, custom_msg)
    
    return validator.is_valid(), validator.get_errors()
