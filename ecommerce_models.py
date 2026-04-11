"""
E-commerce Integration Models
============================
Data models for the E-commerce Integration module.
These models support:
- Channel / Website Connections
- Online Order Synchronization
- Inventory Synchronization
- Customer Synchronization
- Product / Catalog Mapping
- Sync Logs and Exceptions
"""

import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else ''
DATABASE = os.path.join(BASE_DIR, 'warehouse.db')


def get_db():
    """Get database connection."""
    import os
    db_path = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'warehouse.db'))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db_context():
    """Context manager for database operations."""
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    with get_db_context() as db:
        result = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        ).fetchone()
        return result is not None


# =============================================================================
# E-COMMERCE CHANNEL MODELS
# =============================================================================

@dataclass
class EcommerceChannel:
    """
    Represents an e-commerce channel / website connection.
    A channel can be an online store, marketplace, or any external sales platform.
    """
    id: int = 0
    channel_code: str = ""
    channel_name: str = ""
    channel_type: str = ""  # website, marketplace, social, etc.
    company_id: int = 0
    branch_id: int = 0
    warehouse_id: int = 0  # Default fulfillment warehouse
    api_endpoint: str = ""
    api_key: str = ""
    api_secret: str = ""
    webhook_url: str = ""
    is_active: bool = True
    is_connected: bool = False
    last_sync_at: str = ""
    last_sync_status: str = ""  # success, failed, pending
    last_error: str = ""
    sync_direction: str = "bidirectional"  # inbound, outbound, bidirectional
    created_at: str = ""
    created_by: int = 0
    updated_at: str = ""
    updated_by: int = 0
    notes: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class EcommerceChannelProfile:
    """
    Channel-specific profile containing mapping rules and settings.
    """
    id: int = 0
    channel_id: int = 0
    profile_name: str = ""
    # Product mapping
    auto_publish_products: bool = False
    product_sync_enabled: bool = False
    category_mapping_required: bool = True
    # Inventory sync settings
    inventory_sync_enabled: bool = False
    inventory_sync_interval: int = 15  # minutes
    inventory_source_type: str = "available"  # available, physical, reserved
    exclude_reserved_stock: bool = True
    safety_stock_buffer: int = 0
    # Order sync settings
    order_sync_enabled: bool = False
    order_auto_import: bool = True
    duplicate_detection_enabled: bool = True
    order_prefix: str = ""
    # Customer sync settings
    customer_sync_enabled: bool = False
    customer_auto_create: bool = True
    customer_matching_rule: str = "email"  # email, phone, name_email
    guest_customer_prefix: str = "GUEST"
    # Payment mapping
    payment_method_mapping: str = ""  # JSON string
    # Shipping mapping
    shipping_method_mapping: str = ""  # JSON string
    # Status mapping
    order_status_mapping: str = ""  # JSON string
    fulfillment_status_mapping: str = ""  # JSON string
    # Retry settings
    max_retry_attempts: int = 3
    retry_interval_minutes: int = 5
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class EcommerceProductMapping:
    """
    Maps internal products to external channel products.
    """
    id: int = 0
    channel_id: int = 0
    internal_item_id: int = 0
    internal_sku: str = ""
    internal_barcode: str = ""
    external_product_id: str = ""
    external_sku: str = ""
    external_barcode: str = ""
    external_url: str = ""
    is_active: bool = True
    last_synced_at: str = ""
    sync_status: str = "pending"  # pending, synced, failed, disabled
    created_at: str = ""
    updated_at: str = ""


@dataclass
class EcommerceCategoryMapping:
    """
    Maps internal categories to external channel categories.
    """
    id: int = 0
    channel_id: int = 0
    internal_category_id: int = 0
    internal_category_name: str = ""
    external_category_id: str = ""
    external_category_name: str = ""
    external_parent_id: str = ""
    is_active: bool = True
    created_at: str = ""


# =============================================================================
# E-COMMERCE ORDER MODELS
# =============================================================================

@dataclass
class EcommerceOrderImport:
    """
    Represents an imported online order from a channel.
    """
    id: int = 0
    external_order_id: str = ""
    external_order_number: str = ""
    channel_id: int = 0
    channel_name: str = ""
    company_id: int = 0
    branch_id: int = 0
    warehouse_id: int = 0

    # Customer info
    customer_id: int = 0  # Linked internal customer
    customer_email: str = ""
    customer_phone: str = ""
    customer_name: str = ""
    is_guest: bool = False

    # Billing
    billing_name: str = ""
    billing_company: str = ""
    billing_address: str = ""
    billing_city: str = ""
    billing_state: str = ""
    billing_country: str = ""
    billing_postal_code: str = ""
    billing_phone: str = ""

    # Shipping
    shipping_name: str = ""
    shipping_company: str = ""
    shipping_address: str = ""
    shipping_city: str = ""
    shipping_state: str = ""
    shipping_country: str = ""
    shipping_postal_code: str = ""
    shipping_phone: str = ""
    shipping_method: str = ""
    shipping_cost: float = 0.0

    # Order details
    order_date: str = ""
    order_datetime: str = ""
    currency: str = "USD"
    subtotal: float = 0.0
    discount_amount: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0

    # Payment
    payment_method: str = ""
    payment_method_display: str = ""
    payment_status: str = "pending"  # pending, paid, partially_refunded, refunded, failed
    payment_reference: str = ""

    # Fulfillment
    fulfillment_status: str = "unfulfilled"  # unfulfilled, processing, picked, packed, shipped, delivered, cancelled
    shipped_at: str = ""
    delivered_at: str = ""

    # Order status
    order_status: str = "pending"  # pending, confirmed, processing, completed, cancelled, returned
    status_reason: str = ""

    # Internal linkage
    internal_order_id: int = 0
    internal_order_number: str = ""
    internal_invoice_id: int = 0

    # Sync metadata
    sync_status: str = "pending"  # pending, importing, validating, importing_lines, creating_order, synced, failed, skipped
    sync_error: str = ""
    retry_count: int = 0
    last_retry_at: str = ""
    external_data: str = ""  # JSON string of original external data

    # Audit
    imported_at: str = ""
    imported_by: int = 0
    updated_at: str = ""
    notes: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class EcommerceOrderLine:
    """
    Line items from an imported e-commerce order.
    """
    id: int = 0
    order_import_id: int = 0
    line_number: int = 0

    # Product mapping
    internal_item_id: int = 0
    internal_sku: str = ""
    internal_barcode: str = ""
    product_mapping_id: int = 0

    # External product info
    external_product_id: str = ""
    external_product_name: str = ""
    external_sku: str = ""
    external_barcode: str = ""

    # Line details
    quantity: int = 1
    unit_price: float = 0.0
    discount_amount: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0
    tax_rate: float = 0.0

    # Fulfillment
    quantity_picked: int = 0
    quantity_packed: int = 0
    quantity_shipped: int = 0
    quantity_delivered: int = 0

    # Status
    fulfillment_status: str = "unfulfilled"

    # Notes
    notes: str = ""


@dataclass
class EcommerceOrderStatusSync:
    """
    Tracks order status synchronization history.
    """
    id: int = 0
    order_import_id: int = 0
    external_status: str = ""
    internal_status: str = ""
    channel_status: str = ""
    sync_action: str = ""  # pushed, pulled
    sync_result: str = ""  # success, failed, skipped
    error_message: str = ""
    synced_at: str = ""
    synced_by: int = 0


# =============================================================================
# E-COMMERCE INVENTORY MODELS
# =============================================================================

@dataclass
class EcommerceInventorySync:
    """
    Tracks inventory synchronization to channels.
    """
    id: int = 0
    channel_id: int = 0
    channel_name: str = ""
    company_id: int = 0
    warehouse_id: int = 0

    # Product
    internal_item_id: int = 0
    internal_sku: str = ""
    internal_barcode: str = ""
    product_mapping_id: int = 0
    external_product_id: str = ""

    # Stock values
    internal_stock: int = 0
    published_stock: int = 0
    reserved_stock: int = 0
    available_stock: int = 0
    safety_stock_buffer: int = 0

    # Sync result
    sync_status: str = "pending"  # pending, syncing, synced, failed, no_change
    sync_direction: str = "outbound"
    last_synced_at: str = ""
    error_message: str = ""
    retry_count: int = 0

    # Metadata
    sync_type: str = "full"  # full, incremental
    items_expected: int = 0
    items_synced: int = 0
    created_at: str = ""


@dataclass
class EcommerceWarehouseMapping:
    """
    Maps internal warehouses to channel-specific fulfillment centers.
    """
    id: int = 0
    channel_id: int = 0
    internal_warehouse_id: int = 0
    internal_warehouse_name: str = ""
    external_warehouse_id: str = ""
    external_warehouse_name: str = ""
    is_default: bool = False
    is_active: bool = True
    created_at: str = ""


@dataclass
class EcommerceInventoryRule:
    """
    Inventory synchronization rules per channel.
    """
    id: int = 0
    channel_id: int = 0
    rule_name: str = ""
    rule_type: str = ""  # availability, pricing, threshold
    stock_calculation: str = "available"  # available, physical, reserved
    exclude_reserved: bool = True
    safety_stock_qty: int = 0
    max_stock_override: int = 0
    out_of_stock_threshold: int = 0
    is_active: bool = True
    created_at: str = ""


# =============================================================================
# E-COMMERCE CUSTOMER MODELS
# =============================================================================

@dataclass
class EcommerceCustomerImport:
    """
    Represents an imported customer from a channel.
    """
    id: int = 0
    external_customer_id: str = ""
    channel_id: int = 0
    channel_name: str = ""
    company_id: int = 0

    # Basic info
    email: str = ""
    phone: str = ""
    mobile: str = ""
    first_name: str = ""
    last_name: str = ""
    full_name: str = ""
    is_guest: bool = False

    # Company (B2B)
    company_name: str = ""
    tax_id: str = ""
    vat_number: str = ""

    # Billing address
    billing_name: str = ""
    billing_address: str = ""
    billing_city: str = ""
    billing_state: str = ""
    billing_country: str = ""
    billing_postal_code: str = ""
    billing_phone: str = ""

    # Shipping address
    shipping_name: str = ""
    shipping_address: str = ""
    shipping_city: str = ""
    shipping_state: str = ""
    shipping_country: str = ""
    shipping_postal_code: str = ""
    shipping_phone: str = ""

    # Marketing
    accepts_marketing: bool = False
    customer_source: str = ""

    # Internal linkage
    internal_customer_id: int = 0
    customer_matched_by: str = ""  # email, phone, name, manual
    duplicate_review_status: str = "pending"  # pending, approved, rejected, merged
    duplicate_reviewed_by: int = 0
    duplicate_reviewed_at: str = ""

    # Sync metadata
    sync_status: str = "pending"  # pending, matching, creating, synced, failed, skipped, duplicate
    sync_error: str = ""
    retry_count: int = 0
    last_retry_at: str = ""
    external_data: str = ""

    # Audit
    imported_at: str = ""
    imported_by: int = 0
    updated_at: str = ""
    notes: str = ""


@dataclass
class EcommerceCustomerMatch:
    """
    Tracks customer matching decisions for duplicate review.
    """
    id: int = 0
    customer_import_id: int = 0
    internal_customer_id: int = 0
    match_confidence: float = 0.0  # 0.0 to 1.0
    match_criteria: str = ""  # JSON string of what matched
    decision: str = ""  # approved, rejected, pending
    decided_by: int = 0
    decided_at: str = ""
    notes: str = ""


# =============================================================================
# E-COMMERCE SYNC & EXCEPTION MODELS
# =============================================================================

@dataclass
class EcommerceSyncJob:
    """
    Represents a sync job execution.
    """
    id: int = 0
    job_type: str = ""  # order_import, inventory_sync, customer_sync, product_sync
    channel_id: int = 0
    channel_name: str = ""
    company_id: int = 0
    warehouse_id: int = 0
    status: str = "running"  # running, completed, failed, cancelled
    sync_mode: str = "manual"  # manual, scheduled, webhook
    started_at: str = ""
    completed_at: str = ""
    items_processed: int = 0
    items_successful: int = 0
    items_failed: int = 0
    error_message: str = ""
    created_by: int = 0
    created_at: str = ""


@dataclass
class EcommerceSyncQueue:
    """
    Queue for pending sync operations.
    """
    id: int = 0
    queue_type: str = ""  # order, inventory, customer, product
    channel_id: int = 0
    reference_id: str = ""  # External ID or internal ID depending on type
    priority: int = 0  # Lower = higher priority
    status: str = "queued"  # queued, processing, completed, failed, cancelled
    retry_count: int = 0
    max_retries: int = 3
    last_error: str = ""
    scheduled_for: str = ""
    processed_at: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass
class EcommerceException:
    """
    E-commerce exceptions requiring manual review.
    """
    id: int = 0
    exception_number: str = ""
    exception_type: str = ""  # unmapped_item, missing_customer, duplicate_order, stock_mismatch, etc.
    severity: str = "medium"  # low, medium, high, critical
    channel_id: int = 0
    channel_name: str = ""
    company_id: int = 0

    # References
    order_import_id: int = 0
    customer_import_id: int = 0
    inventory_sync_id: int = 0
    product_mapping_id: int = 0
    reference_type: str = ""  # order, customer, inventory, product
    external_reference: str = ""
    internal_reference: str = ""

    # Details
    title: str = ""
    description: str = ""
    source_data: str = ""  # JSON string
    internal_state: str = ""  # JSON string

    # Resolution
    status: str = "open"  # open, in_review, resolved, cancelled, escalated
    assigned_to: int = 0
    assigned_to_name: str = ""
    resolution_action: str = ""  # retry, skip, remap, create, approve, reject
    resolution_notes: str = ""
    resolved_by: int = 0
    resolved_at: str = ""

    # Audit
    created_at: str = ""
    created_by: int = 0
    updated_at: str = ""


@dataclass
class EcommerceAuditLog:
    """
    Audit log for e-commerce operations.
    """
    id: int = 0
    log_type: str = ""  # sync, mapping, exception, settings, auth
    action: str = ""  # created, updated, deleted, synced, retried, resolved
    channel_id: int = 0
    channel_name: str = ""
    company_id: int = 0
    user_id: int = 0
    user_name: str = ""
    entity_type: str = ""  # channel, order, customer, inventory, product, etc.
    entity_id: int = 0
    entity_reference: str = ""
    before_state: str = ""  # JSON string
    after_state: str = ""  # JSON string
    ip_address: str = ""
    user_agent: str = ""
    timestamp: str = ""


@dataclass
class EcommerceWebhookLog:
    """
    Logs incoming webhooks from channels.
    """
    id: int = 0
    channel_id: int = 0
    webhook_event: str = ""
    event_type: str = ""  # order_created, order_updated, payment_received, etc.
    payload: str = ""  # JSON string
    headers: str = ""  # JSON string
    signature: str = ""
    is_valid: bool = True
    validation_error: str = ""
    processed: bool = False
    processing_result: str = ""
    created_at: str = ""


@dataclass
class EcommerceApiLog:
    """
    Logs outgoing API calls to channels.
    """
    id: int = 0
    channel_id: int = 0
    channel_name: str = ""
    api_endpoint: str = ""
    http_method: str = ""
    request_headers: str = ""  # JSON (secret masked)
    request_body: str = ""  # JSON (sensitive data masked)
    response_status: int = 0
    response_headers: str = ""
    response_body: str = ""
    error_message: str = ""
    duration_ms: int = 0
    created_at: str = ""


# =============================================================================
# E-COMMERCE SETTINGS MODELS
# =============================================================================

@dataclass
class EcommerceStatusMapping:
    """
    Maps external channel statuses to internal statuses.
    """
    id: int = 0
    channel_id: int = 0
    mapping_type: str = ""  # order_status, payment_status, fulfillment_status
    external_value: str = ""
    external_display: str = ""
    internal_value: str = ""
    is_active: bool = True
    created_at: str = ""


@dataclass
class EcommerceSetting:
    """
    E-commerce module settings.
    """
    id: int = 0
    setting_key: str = ""
    setting_value: str = ""
    setting_type: str = "string"  # string, int, bool, json
    description: str = ""
    is_encrypted: bool = False
    company_id: int = 0
    channel_id: int = 0  # If set, channel-specific; if null, global
    updated_at: str = ""
    updated_by: int = 0


# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

ECOMMERCE_TABLES = [
    """
    CREATE TABLE IF NOT EXISTS ecommerce_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_code TEXT NOT NULL UNIQUE,
        channel_name TEXT NOT NULL,
        channel_type TEXT DEFAULT 'website',
        company_id INTEGER DEFAULT 0,
        branch_id INTEGER DEFAULT 0,
        warehouse_id INTEGER DEFAULT 0,
        api_endpoint TEXT DEFAULT '',
        api_key TEXT DEFAULT '',
        api_secret TEXT DEFAULT '',
        webhook_url TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        is_connected INTEGER DEFAULT 0,
        last_sync_at TEXT DEFAULT '',
        last_sync_status TEXT DEFAULT '',
        last_error TEXT DEFAULT '',
        sync_direction TEXT DEFAULT 'bidirectional',
        created_at TEXT DEFAULT (datetime('now')),
        created_by INTEGER DEFAULT 0,
        updated_at TEXT DEFAULT (datetime('now')),
        updated_by INTEGER DEFAULT 0,
        notes TEXT DEFAULT ''
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ecommerce_channel_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id INTEGER NOT NULL,
        profile_name TEXT NOT NULL,
        auto_publish_products INTEGER DEFAULT 0,
        product_sync_enabled INTEGER DEFAULT 0,
        category_mapping_required INTEGER DEFAULT 1,
        inventory_sync_enabled INTEGER DEFAULT 0,
        inventory_sync_interval INTEGER DEFAULT 15,
        inventory_source_type TEXT DEFAULT 'available',
        exclude_reserved_stock INTEGER DEFAULT 1,
        safety_stock_buffer INTEGER DEFAULT 0,
        order_sync_enabled INTEGER DEFAULT 0,
        order_auto_import INTEGER DEFAULT 1,
        duplicate_detection_enabled INTEGER DEFAULT 1,
        order_prefix TEXT DEFAULT '',
        customer_sync_enabled INTEGER DEFAULT 0,
        customer_auto_create INTEGER DEFAULT 1,
        customer_matching_rule TEXT DEFAULT 'email',
        guest_customer_prefix TEXT DEFAULT 'GUEST',
        payment_method_mapping TEXT DEFAULT '{}',
        shipping_method_mapping TEXT DEFAULT '{}',
        order_status_mapping TEXT DEFAULT '{}',
        fulfillment_status_mapping TEXT DEFAULT '{}',
        max_retry_attempts INTEGER DEFAULT 3,
        retry_interval_minutes INTEGER DEFAULT 5,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (channel_id) REFERENCES ecommerce_channels(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ecommerce_product_mappings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id INTEGER NOT NULL,
        internal_item_id INTEGER DEFAULT 0,
        internal_sku TEXT DEFAULT '',
        internal_barcode TEXT DEFAULT '',
        external_product_id TEXT DEFAULT '',
        external_sku TEXT DEFAULT '',
        external_barcode TEXT DEFAULT '',
        external_url TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        last_synced_at TEXT DEFAULT '',
        sync_status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (channel_id) REFERENCES ecommerce_channels(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ecommerce_category_mappings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id INTEGER NOT NULL,
        internal_category_id INTEGER DEFAULT 0,
        internal_category_name TEXT DEFAULT '',
        external_category_id TEXT DEFAULT '',
        external_category_name TEXT DEFAULT '',
        external_parent_id TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (channel_id) REFERENCES ecommerce_channels(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ecommerce_order_imports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        external_order_id TEXT DEFAULT '',
        external_order_number TEXT DEFAULT '',
        channel_id INTEGER DEFAULT 0,
        channel_name TEXT DEFAULT '',
        company_id INTEGER DEFAULT 0,
        branch_id INTEGER DEFAULT 0,
        warehouse_id INTEGER DEFAULT 0,
        customer_id INTEGER DEFAULT 0,
        customer_email TEXT DEFAULT '',
        customer_phone TEXT DEFAULT '',
        customer_name TEXT DEFAULT '',
        is_guest INTEGER DEFAULT 0,
        billing_name TEXT DEFAULT '',
        billing_company TEXT DEFAULT '',
        billing_address TEXT DEFAULT '',
        billing_city TEXT DEFAULT '',
        billing_state TEXT DEFAULT '',
        billing_country TEXT DEFAULT '',
        billing_postal_code TEXT DEFAULT '',
        billing_phone TEXT DEFAULT '',
        shipping_name TEXT DEFAULT '',
        shipping_company TEXT DEFAULT '',
        shipping_address TEXT DEFAULT '',
        shipping_city TEXT DEFAULT '',
        shipping_state TEXT DEFAULT '',
        shipping_country TEXT DEFAULT '',
        shipping_postal_code TEXT DEFAULT '',
        shipping_phone TEXT DEFAULT '',
        shipping_method TEXT DEFAULT '',
        shipping_cost REAL DEFAULT 0.0,
        order_date TEXT DEFAULT '',
        order_datetime TEXT DEFAULT '',
        currency TEXT DEFAULT 'USD',
        subtotal REAL DEFAULT 0.0,
        discount_amount REAL DEFAULT 0.0,
        tax_amount REAL DEFAULT 0.0,
        total_amount REAL DEFAULT 0.0,
        payment_method TEXT DEFAULT '',
        payment_method_display TEXT DEFAULT '',
        payment_status TEXT DEFAULT 'pending',
        payment_reference TEXT DEFAULT '',
        fulfillment_status TEXT DEFAULT 'unfulfilled',
        shipped_at TEXT DEFAULT '',
        delivered_at TEXT DEFAULT '',
        order_status TEXT DEFAULT 'pending',
        status_reason TEXT DEFAULT '',
        internal_order_id INTEGER DEFAULT 0,
        internal_order_number TEXT DEFAULT '',
        internal_invoice_id INTEGER DEFAULT 0,
        sync_status TEXT DEFAULT 'pending',
        sync_error TEXT DEFAULT '',
        retry_count INTEGER DEFAULT 0,
        last_retry_at TEXT DEFAULT '',
        external_data TEXT DEFAULT '',
        imported_at TEXT DEFAULT (datetime('now')),
        imported_by INTEGER DEFAULT 0,
        updated_at TEXT DEFAULT (datetime('now')),
        notes TEXT DEFAULT '',
        FOREIGN KEY (channel_id) REFERENCES ecommerce_channels(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ecommerce_order_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_import_id INTEGER NOT NULL,
        line_number INTEGER DEFAULT 1,
        internal_item_id INTEGER DEFAULT 0,
        internal_sku TEXT DEFAULT '',
        internal_barcode TEXT DEFAULT '',
        product_mapping_id INTEGER DEFAULT 0,
        external_product_id TEXT DEFAULT '',
        external_product_name TEXT DEFAULT '',
        external_sku TEXT DEFAULT '',
        external_barcode TEXT DEFAULT '',
        quantity INTEGER DEFAULT 1,
        unit_price REAL DEFAULT 0.0,
        discount_amount REAL DEFAULT 0.0,
        tax_amount REAL DEFAULT 0.0,
        total_amount REAL DEFAULT 0.0,
        tax_rate REAL DEFAULT 0.0,
        quantity_picked INTEGER DEFAULT 0,
        quantity_packed INTEGER DEFAULT 0,
        quantity_shipped INTEGER DEFAULT 0,
        quantity_delivered INTEGER DEFAULT 0,
        fulfillment_status TEXT DEFAULT 'unfulfilled',
        notes TEXT DEFAULT '',
        FOREIGN KEY (order_import_id) REFERENCES ecommerce_order_imports(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ecommerce_order_status_sync (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_import_id INTEGER NOT NULL,
        external_status TEXT DEFAULT '',
        internal_status TEXT DEFAULT '',
        channel_status TEXT DEFAULT '',
        sync_action TEXT DEFAULT '',
        sync_result TEXT DEFAULT '',
        error_message TEXT DEFAULT '',
        synced_at TEXT DEFAULT (datetime('now')),
        synced_by INTEGER DEFAULT 0,
        FOREIGN KEY (order_import_id) REFERENCES ecommerce_order_imports(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ecommerce_inventory_syncs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id INTEGER DEFAULT 0,
        channel_name TEXT DEFAULT '',
        company_id INTEGER DEFAULT 0,
        warehouse_id INTEGER DEFAULT 0,
        internal_item_id INTEGER DEFAULT 0,
        internal_sku TEXT DEFAULT '',
        internal_barcode TEXT DEFAULT '',
        product_mapping_id INTEGER DEFAULT 0,
        external_product_id TEXT DEFAULT '',
        internal_stock INTEGER DEFAULT 0,
        published_stock INTEGER DEFAULT 0,
        reserved_stock INTEGER DEFAULT 0,
        available_stock INTEGER DEFAULT 0,
        safety_stock_buffer INTEGER DEFAULT 0,
        sync_status TEXT DEFAULT 'pending',
        sync_direction TEXT DEFAULT 'outbound',
        last_synced_at TEXT DEFAULT '',
        error_message TEXT DEFAULT '',
        retry_count INTEGER DEFAULT 0,
        sync_type TEXT DEFAULT 'full',
        items_expected INTEGER DEFAULT 0,
        items_synced INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (channel_id) REFERENCES ecommerce_channels(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ecommerce_warehouse_mappings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id INTEGER NOT NULL,
        internal_warehouse_id INTEGER DEFAULT 0,
        internal_warehouse_name TEXT DEFAULT '',
        external_warehouse_id TEXT DEFAULT '',
        external_warehouse_name TEXT DEFAULT '',
        is_default INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (channel_id) REFERENCES ecommerce_channels(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ecommerce_inventory_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id INTEGER NOT NULL,
        rule_name TEXT NOT NULL,
        rule_type TEXT DEFAULT 'availability',
        stock_calculation TEXT DEFAULT 'available',
        exclude_reserved INTEGER DEFAULT 1,
        safety_stock_qty INTEGER DEFAULT 0,
        max_stock_override INTEGER DEFAULT 0,
        out_of_stock_threshold INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (channel_id) REFERENCES ecommerce_channels(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ecommerce_customer_imports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        external_customer_id TEXT DEFAULT '',
        channel_id INTEGER DEFAULT 0,
        channel_name TEXT DEFAULT '',
        company_id INTEGER DEFAULT 0,
        email TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        mobile TEXT DEFAULT '',
        first_name TEXT DEFAULT '',
        last_name TEXT DEFAULT '',
        full_name TEXT DEFAULT '',
        is_guest INTEGER DEFAULT 0,
        company_name TEXT DEFAULT '',
        tax_id TEXT DEFAULT '',
        vat_number TEXT DEFAULT '',
        billing_name TEXT DEFAULT '',
        billing_address TEXT DEFAULT '',
        billing_city TEXT DEFAULT '',
        billing_state TEXT DEFAULT '',
        billing_country TEXT DEFAULT '',
        billing_postal_code TEXT DEFAULT '',
        billing_phone TEXT DEFAULT '',
        shipping_name TEXT DEFAULT '',
        shipping_address TEXT DEFAULT '',
        shipping_city TEXT DEFAULT '',
        shipping_state TEXT DEFAULT '',
        shipping_country TEXT DEFAULT '',
        shipping_postal_code TEXT DEFAULT '',
        shipping_phone TEXT DEFAULT '',
        accepts_marketing INTEGER DEFAULT 0,
        customer_source TEXT DEFAULT '',
        internal_customer_id INTEGER DEFAULT 0,
        customer_matched_by TEXT DEFAULT '',
        duplicate_review_status TEXT DEFAULT 'pending',
        duplicate_reviewed_by INTEGER DEFAULT 0,
        duplicate_reviewed_at TEXT DEFAULT '',
        sync_status TEXT DEFAULT 'pending',
        sync_error TEXT DEFAULT '',
        retry_count INTEGER DEFAULT 0,
        last_retry_at TEXT DEFAULT '',
        external_data TEXT DEFAULT '',
        imported_at TEXT DEFAULT (datetime('now')),
        imported_by INTEGER DEFAULT 0,
        updated_at TEXT DEFAULT (datetime('now')),
        notes TEXT DEFAULT '',
        FOREIGN KEY (channel_id) REFERENCES ecommerce_channels(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ecommerce_customer_matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_import_id INTEGER NOT NULL,
        internal_customer_id INTEGER DEFAULT 0,
        match_confidence REAL DEFAULT 0.0,
        match_criteria TEXT DEFAULT '',
        decision TEXT DEFAULT 'pending',
        decided_by INTEGER DEFAULT 0,
        decided_at TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        FOREIGN KEY (customer_import_id) REFERENCES ecommerce_customer_imports(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ecommerce_sync_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_type TEXT NOT NULL,
        channel_id INTEGER DEFAULT 0,
        channel_name TEXT DEFAULT '',
        company_id INTEGER DEFAULT 0,
        warehouse_id INTEGER DEFAULT 0,
        status TEXT DEFAULT 'running',
        sync_mode TEXT DEFAULT 'manual',
        started_at TEXT DEFAULT (datetime('now')),
        completed_at TEXT DEFAULT '',
        items_processed INTEGER DEFAULT 0,
        items_successful INTEGER DEFAULT 0,
        items_failed INTEGER DEFAULT 0,
        error_message TEXT DEFAULT '',
        created_by INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ecommerce_sync_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        queue_type TEXT NOT NULL,
        channel_id INTEGER DEFAULT 0,
        reference_id TEXT DEFAULT '',
        priority INTEGER DEFAULT 5,
        status TEXT DEFAULT 'queued',
        retry_count INTEGER DEFAULT 0,
        max_retries INTEGER DEFAULT 3,
        last_error TEXT DEFAULT '',
        scheduled_for TEXT DEFAULT '',
        processed_at TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ecommerce_exceptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exception_number TEXT NOT NULL UNIQUE,
        exception_type TEXT NOT NULL,
        severity TEXT DEFAULT 'medium',
        channel_id INTEGER DEFAULT 0,
        channel_name TEXT DEFAULT '',
        company_id INTEGER DEFAULT 0,
        order_import_id INTEGER DEFAULT 0,
        customer_import_id INTEGER DEFAULT 0,
        inventory_sync_id INTEGER DEFAULT 0,
        product_mapping_id INTEGER DEFAULT 0,
        reference_type TEXT DEFAULT '',
        external_reference TEXT DEFAULT '',
        internal_reference TEXT DEFAULT '',
        title TEXT DEFAULT '',
        description TEXT DEFAULT '',
        source_data TEXT DEFAULT '',
        internal_state TEXT DEFAULT '',
        status TEXT DEFAULT 'open',
        assigned_to INTEGER DEFAULT 0,
        assigned_to_name TEXT DEFAULT '',
        resolution_action TEXT DEFAULT '',
        resolution_notes TEXT DEFAULT '',
        resolved_by INTEGER DEFAULT 0,
        resolved_at TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now')),
        created_by INTEGER DEFAULT 0,
        updated_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ecommerce_audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        log_type TEXT DEFAULT '',
        action TEXT DEFAULT '',
        channel_id INTEGER DEFAULT 0,
        channel_name TEXT DEFAULT '',
        company_id INTEGER DEFAULT 0,
        user_id INTEGER DEFAULT 0,
        user_name TEXT DEFAULT '',
        entity_type TEXT DEFAULT '',
        entity_id INTEGER DEFAULT 0,
        entity_reference TEXT DEFAULT '',
        before_state TEXT DEFAULT '',
        after_state TEXT DEFAULT '',
        ip_address TEXT DEFAULT '',
        user_agent TEXT DEFAULT '',
        timestamp TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ecommerce_webhook_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id INTEGER DEFAULT 0,
        webhook_event TEXT DEFAULT '',
        event_type TEXT DEFAULT '',
        payload TEXT DEFAULT '',
        headers TEXT DEFAULT '',
        signature TEXT DEFAULT '',
        is_valid INTEGER DEFAULT 1,
        validation_error TEXT DEFAULT '',
        processed INTEGER DEFAULT 0,
        processing_result TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ecommerce_api_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id INTEGER DEFAULT 0,
        channel_name TEXT DEFAULT '',
        api_endpoint TEXT DEFAULT '',
        http_method TEXT DEFAULT '',
        request_headers TEXT DEFAULT '',
        request_body TEXT DEFAULT '',
        response_status INTEGER DEFAULT 0,
        response_headers TEXT DEFAULT '',
        response_body TEXT DEFAULT '',
        error_message TEXT DEFAULT '',
        duration_ms INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ecommerce_status_mappings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id INTEGER NOT NULL,
        mapping_type TEXT NOT NULL,
        external_value TEXT DEFAULT '',
        external_display TEXT DEFAULT '',
        internal_value TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (channel_id) REFERENCES ecommerce_channels(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ecommerce_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_key TEXT NOT NULL UNIQUE,
        setting_value TEXT DEFAULT '',
        setting_type TEXT DEFAULT 'string',
        description TEXT DEFAULT '',
        is_encrypted INTEGER DEFAULT 0,
        company_id INTEGER DEFAULT 0,
        channel_id INTEGER DEFAULT 0,
        updated_at TEXT DEFAULT (datetime('now')),
        updated_by INTEGER DEFAULT 0
    )
    """,
]

ECOMMERCE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_ec_channel_code ON ecommerce_channels(channel_code)",
    "CREATE INDEX IF NOT EXISTS idx_ec_channel_active ON ecommerce_channels(is_active)",
    "CREATE INDEX IF NOT EXISTS idx_ec_order_external ON ecommerce_order_imports(external_order_id)",
    "CREATE INDEX IF NOT EXISTS idx_ec_order_channel ON ecommerce_order_imports(channel_id)",
    "CREATE INDEX IF NOT EXISTS idx_ec_order_sync_status ON ecommerce_order_imports(sync_status)",
    "CREATE INDEX IF NOT EXISTS idx_ec_order_status ON ecommerce_order_imports(order_status)",
    "CREATE INDEX IF NOT EXISTS idx_ec_order_date ON ecommerce_order_imports(order_date)",
    "CREATE INDEX IF NOT EXISTS idx_ec_order_customer ON ecommerce_order_imports(customer_email)",
    "CREATE INDEX IF NOT EXISTS idx_ec_inv_sync_channel ON ecommerce_inventory_syncs(channel_id)",
    "CREATE INDEX IF NOT EXISTS idx_ec_inv_sync_item ON ecommerce_inventory_syncs(internal_item_id)",
    "CREATE INDEX IF NOT EXISTS idx_ec_inv_sync_status ON ecommerce_inventory_syncs(sync_status)",
    "CREATE INDEX IF NOT EXISTS idx_ec_cust_external ON ecommerce_customer_imports(external_customer_id)",
    "CREATE INDEX IF NOT EXISTS idx_ec_cust_channel ON ecommerce_customer_imports(channel_id)",
    "CREATE INDEX IF NOT EXISTS idx_ec_cust_sync_status ON ecommerce_customer_imports(sync_status)",
    "CREATE INDEX IF NOT EXISTS idx_ec_cust_email ON ecommerce_customer_imports(email)",
    "CREATE INDEX IF NOT EXISTS idx_ec_cust_duplicate ON ecommerce_customer_imports(duplicate_review_status)",
    "CREATE INDEX IF NOT EXISTS idx_ec_exception_channel ON ecommerce_exceptions(channel_id)",
    "CREATE INDEX IF NOT EXISTS idx_ec_exception_type ON ecommerce_exceptions(exception_type)",
    "CREATE INDEX IF NOT EXISTS idx_ec_exception_status ON ecommerce_exceptions(status)",
    "CREATE INDEX IF NOT EXISTS idx_ec_exception_severity ON ecommerce_exceptions(severity)",
    "CREATE INDEX IF NOT EXISTS idx_ec_prod_map_channel ON ecommerce_product_mappings(channel_id)",
    "CREATE INDEX IF NOT EXISTS idx_ec_prod_map_internal ON ecommerce_product_mappings(internal_item_id)",
    "CREATE INDEX IF NOT EXISTS idx_ec_prod_map_external ON ecommerce_product_mappings(external_product_id)",
    "CREATE INDEX IF NOT EXISTS idx_ec_audit_channel ON ecommerce_audit_logs(channel_id)",
    "CREATE INDEX IF NOT EXISTS idx_ec_audit_entity ON ecommerce_audit_logs(entity_type, entity_id)",
    "CREATE INDEX IF NOT EXISTS idx_ec_audit_timestamp ON ecommerce_audit_logs(timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_ec_queue_type ON ecommerce_sync_queue(queue_type)",
    "CREATE INDEX IF NOT EXISTS idx_ec_queue_status ON ecommerce_sync_queue(status)",
    "CREATE INDEX IF NOT EXISTS idx_ec_webhook_channel ON ecommerce_webhook_logs(channel_id)",
    "CREATE INDEX IF NOT EXISTS idx_ec_api_channel ON ecommerce_api_logs(channel_id)",
]


def init_ecommerce_tables():
    """Initialize all e-commerce tables and indexes."""
    with get_db_context() as db:
        for table_sql in ECOMMERCE_TABLES:
            db.execute(table_sql)
        
        for index_sql in ECOMMERCE_INDEXES:
            db.execute(index_sql)
        
        db.commit()
    
    # Initialize default settings
    _init_default_settings()


def _init_default_settings():
    """Initialize default e-commerce settings."""
    default_settings = [
        ('ecommerce_default_currency', 'USD', 'string', 'Default currency for e-commerce transactions'),
        ('ecommerce_default_payment_status', 'pending', 'string', 'Default payment status for new orders'),
        ('ecommerce_default_fulfillment_status', 'unfulfilled', 'string', 'Default fulfillment status'),
        ('ecommerce_max_retry_attempts', '3', 'int', 'Maximum retry attempts for failed syncs'),
        ('ecommerce_retry_interval_minutes', '5', 'int', 'Minutes between retry attempts'),
        ('ecommerce_order_prefix', 'ECO', 'string', 'Prefix for manually created e-commerce orders'),
        ('ecommerce_customer_prefix', 'EC', 'string', 'Prefix for imported customer codes'),
        ('ecommerce_enable_audit_log', '1', 'bool', 'Enable detailed audit logging'),
        ('ecommerce_enable_webhook_log', '1', 'bool', 'Enable webhook logging'),
        ('ecommerce_enable_api_log', '1', 'bool', 'Enable API call logging'),
    ]
    
    with get_db_context() as db:
        for key, value, stype, desc in default_settings:
            existing = db.execute(
                "SELECT id FROM ecommerce_settings WHERE setting_key = ?",
                (key,)
            ).fetchone()
            
            if not existing:
                db.execute("""
                    INSERT INTO ecommerce_settings (setting_key, setting_value, setting_type, description)
                    VALUES (?, ?, ?, ?)
                """, (key, value, stype, desc))
        
        db.commit()
