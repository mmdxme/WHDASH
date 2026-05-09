"""
Procurement Management Data Access Layer
========================================
Comprehensive data models for the Procurement & Purchasing Management System.

This module provides all data access for:
- Supplier Management
- Purchase Requisitions
- RFQ / Supplier Inquiries
- Supplier Quotations
- Vendor Selection & Approvals
- Purchase Orders
- Inbound Shipments
- Receiving Coordination
- Claims & Discrepancies
- Contracts & Price Agreements
- Procurement Budgets
- Supplier Performance
- Procurement Alerts
- Audit Logging

Usage:
    from procurement_models import (
        get_suppliers, get_supplier_by_id,
        get_requisitions, create_requisition,
        get_rfqs, create_rfq,
        # ... etc
    )
"""

from database import get_db_context, get_one, get_all, row_to_dict, rows_to_list, get_count, exists, table_exists
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any


# =============================================================================
# PROCUREMENT MODULE INITIALIZATION
# =============================================================================

def initialize_procurement_tables():
    """
    Initialize all procurement-related tables.
    Called during app startup via procurement_routes.py.
    """
    with get_db_context() as db:
        # ── Procurement Settings ──────────────────────────────────────────
        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT,
                category TEXT DEFAULT 'GENERAL',
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ── Supplier Extended Fields ────────────────────────────────────────
        # Extend the basic suppliers table with procurement-specific fields
        _ensure_supplier_columns(db)

        # ── Supplier Contacts ──────────────────────────────────────────────
        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_supplier_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER NOT NULL,
                contact_name TEXT NOT NULL,
                position TEXT,
                phone TEXT,
                mobile TEXT,
                email TEXT,
                is_primary INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
            )
        ''')

        # ── Supplier Brands / Item Groups ──────────────────────────────────
        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_supplier_brands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER NOT NULL,
                brand_name TEXT,
                item_group TEXT,
                is_preferred INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
            )
        ''')

        # ── Supplier Performance Metrics ────────────────────────────────────
        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_supplier_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER NOT NULL,
                metric_date DATE NOT NULL,
                on_time_delivery_rate REAL DEFAULT 0,
                avg_lead_time_days REAL DEFAULT 0,
                lead_time_variability REAL DEFAULT 0,
                fill_rate REAL DEFAULT 0,
                quantity_accuracy REAL DEFAULT 0,
                quality_acceptance_rate REAL DEFAULT 0,
                claim_rate REAL DEFAULT 0,
                return_rate REAL DEFAULT 0,
                responsiveness_score REAL DEFAULT 0,
                document_accuracy REAL DEFAULT 0,
                overall_score REAL DEFAULT 0,
                spend_amount REAL DEFAULT 0,
                total_orders INTEGER DEFAULT 0,
                total_receipts INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
            )
        ''')

        # ── Purchase Requisitions ──────────────────────────────────────────
        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_requisitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requisition_number TEXT UNIQUE NOT NULL,
                requisition_date DATE NOT NULL,
                requisition_time TEXT,
                requester_id INTEGER,
                requester_name TEXT,
                department TEXT,
                company_id INTEGER,
                branch_id INTEGER,
                warehouse_id INTEGER,
                source_type TEXT DEFAULT 'MANUAL',
                priority TEXT DEFAULT 'MEDIUM',
                urgency TEXT DEFAULT 'NORMAL',
                status TEXT DEFAULT 'DRAFT',
                approved_by INTEGER,
                approved_at TEXT,
                rejection_reason TEXT,
                total_estimated_amount REAL DEFAULT 0,
                currency TEXT DEFAULT 'AED',
                notes TEXT,
                internal_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (company_id) REFERENCES companies(id),
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
            )
        ''')

        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_requisition_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requisition_id INTEGER NOT NULL,
                line_number INTEGER,
                item_id INTEGER,
                item_code TEXT,
                item_name TEXT,
                description TEXT,
                brand TEXT,
                part_number TEXT,
                requested_qty REAL DEFAULT 0,
                unit_of_measure TEXT DEFAULT 'PCS',
                required_date DATE,
                preferred_supplier_id INTEGER,
                preferred_supplier_name TEXT,
                estimated_unit_price REAL DEFAULT 0,
                estimated_total_price REAL DEFAULT 0,
                current_stock REAL DEFAULT 0,
                reserved_stock REAL DEFAULT 0,
                open_demand REAL DEFAULT 0,
                open_purchase_qty REAL DEFAULT 0,
                purpose TEXT,
                remarks TEXT,
                status TEXT DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (requisition_id) REFERENCES procurement_requisitions(id) ON DELETE CASCADE,
                FOREIGN KEY (preferred_supplier_id) REFERENCES suppliers(id)
            )
        ''')

        # ── RFQ / Supplier Inquiries ───────────────────────────────────────
        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_rfqs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rfq_number TEXT UNIQUE NOT NULL,
                rfq_date DATE NOT NULL,
                buyer_id INTEGER,
                buyer_name TEXT,
                company_id INTEGER,
                warehouse_id INTEGER,
                source_requisition_id INTEGER,
                currency TEXT DEFAULT 'AED',
                status TEXT DEFAULT 'DRAFT',
                response_due_date DATE,
                requested_delivery_date DATE,
                incoterm TEXT,
                payment_terms TEXT,
                shipping_method TEXT,
                delivery_address TEXT,
                urgency TEXT DEFAULT 'NORMAL',
                notes TEXT,
                internal_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT,
                created_by INTEGER,
                FOREIGN KEY (company_id) REFERENCES companies(id),
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
                FOREIGN KEY (source_requisition_id) REFERENCES procurement_requisitions(id)
            )
        ''')

        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_rfq_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rfq_id INTEGER NOT NULL,
                line_number INTEGER,
                requisition_line_id INTEGER,
                item_id INTEGER,
                item_code TEXT,
                item_name TEXT,
                brand TEXT,
                part_number TEXT,
                requested_qty REAL DEFAULT 0,
                unit_of_measure TEXT DEFAULT 'PCS',
                specifications TEXT,
                target_price REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rfq_id) REFERENCES procurement_rfqs(id) ON DELETE CASCADE
            )
        ''')

        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_rfq_suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rfq_id INTEGER NOT NULL,
                supplier_id INTEGER NOT NULL,
                supplier_name TEXT,
                contact_person TEXT,
                contact_email TEXT,
                is_responded INTEGER DEFAULT 0,
                response_date DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rfq_id) REFERENCES procurement_rfqs(id) ON DELETE CASCADE,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        ''')

        # ── Supplier Quotations ─────────────────────────────────────────────
        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_quotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quotation_number TEXT UNIQUE NOT NULL,
                rfq_id INTEGER,
                supplier_id INTEGER NOT NULL,
                supplier_name TEXT,
                quotation_date DATE,
                validity_date DATE,
                status TEXT DEFAULT 'DRAFT',
                version INTEGER DEFAULT 1,
                currency TEXT DEFAULT 'AED',
                incoterm TEXT,
                payment_terms TEXT,
                lead_time_days INTEGER,
                moq REAL DEFAULT 1,
                order_multiple REAL DEFAULT 1,
                freight_cost REAL DEFAULT 0,
                other_charges REAL DEFAULT 0,
                total_amount REAL DEFAULT 0,
                is_accepted INTEGER DEFAULT 0,
                is_winner INTEGER DEFAULT 0,
                comparison_score REAL DEFAULT 0,
                notes TEXT,
                internal_notes TEXT,
                submitted_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT,
                created_by INTEGER,
                FOREIGN KEY (rfq_id) REFERENCES procurement_rfqs(id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        ''')

        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_quotation_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quotation_id INTEGER NOT NULL,
                line_number INTEGER,
                rfq_line_id INTEGER,
                item_id INTEGER,
                item_code TEXT,
                item_name TEXT,
                brand TEXT,
                part_number TEXT,
                quoted_qty REAL DEFAULT 0,
                unit_of_measure TEXT DEFAULT 'PCS',
                unit_price REAL DEFAULT 0,
                discount_percent REAL DEFAULT 0,
                final_unit_price REAL DEFAULT 0,
                line_total REAL DEFAULT 0,
                requested_qty REAL DEFAULT 0,
                is_matched INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (quotation_id) REFERENCES procurement_quotations(id) ON DELETE CASCADE
            )
        ''')

        # ── Vendor Selection ───────────────────────────────────────────────
        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_vendor_selections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                selection_number TEXT UNIQUE NOT NULL,
                requisition_id INTEGER,
                rfq_id INTEGER,
                selected_supplier_id INTEGER NOT NULL,
                selected_supplier_name TEXT,
                alternate_supplier_id INTEGER,
                alternate_supplier_name TEXT,
                selection_date DATE,
                status TEXT DEFAULT 'PENDING',
                selection_type TEXT DEFAULT 'LOWEST_PRICE',
                justification TEXT,
                estimated_total_amount REAL DEFAULT 0,
                currency TEXT DEFAULT 'AED',
                is_budget_approved INTEGER DEFAULT 0,
                budget_approver_id INTEGER,
                budget_approved_at TEXT,
                is_price_approved INTEGER DEFAULT 0,
                price_approver_id INTEGER,
                price_approved_at TEXT,
                approval_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT,
                created_by INTEGER,
                FOREIGN KEY (requisition_id) REFERENCES procurement_requisitions(id),
                FOREIGN KEY (rfq_id) REFERENCES procurement_rfqs(id),
                FOREIGN KEY (selected_supplier_id) REFERENCES suppliers(id)
            )
        ''')

        # ── Purchase Orders ────────────────────────────────────────────────
        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_purchase_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_number TEXT UNIQUE NOT NULL,
                po_date DATE NOT NULL,
                po_type TEXT DEFAULT 'STANDARD',
                supplier_id INTEGER NOT NULL,
                supplier_name TEXT,
                buyer_id INTEGER,
                buyer_name TEXT,
                company_id INTEGER,
                branch_id INTEGER,
                warehouse_id INTEGER,
                source_requisition_id INTEGER,
                source_rfq_id INTEGER,
                source_quotation_id INTEGER,
                source_vendor_selection_id INTEGER,
                currency TEXT DEFAULT 'AED',
                payment_terms TEXT,
                incoterm TEXT,
                shipment_method TEXT,
                delivery_address TEXT,
                expected_ship_date DATE,
                expected_delivery_date DATE,
                actual_delivery_date DATE,
                status TEXT DEFAULT 'DRAFT',
                approval_status TEXT DEFAULT 'PENDING',
                approved_by INTEGER,
                approved_at TEXT,
                subtotal REAL DEFAULT 0,
                discount_amount REAL DEFAULT 0,
                tax_amount REAL DEFAULT 0,
                freight_cost REAL DEFAULT 0,
                other_charges REAL DEFAULT 0,
                total_amount REAL DEFAULT 0,
                received_amount REAL DEFAULT 0,
                invoiced_amount REAL DEFAULT 0,
                paid_amount REAL DEFAULT 0,
                notes TEXT,
                internal_notes TEXT,
                terms_conditions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT,
                created_by INTEGER,
                FOREIGN KEY (company_id) REFERENCES companies(id),
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        ''')

        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_po_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_id INTEGER NOT NULL,
                line_number INTEGER,
                requisition_line_id INTEGER,
                rfq_line_id INTEGER,
                quotation_line_id INTEGER,
                item_id INTEGER,
                item_code TEXT,
                item_name TEXT,
                brand TEXT,
                part_number TEXT,
                ordered_qty REAL DEFAULT 0,
                unit_of_measure TEXT DEFAULT 'PCS',
                unit_price REAL DEFAULT 0,
                discount_percent REAL DEFAULT 0,
                final_unit_price REAL DEFAULT 0,
                line_total REAL DEFAULT 0,
                received_qty REAL DEFAULT 0,
                invoiced_qty REAL DEFAULT 0,
                rejected_qty REAL DEFAULT 0,
                pending_qty REAL DEFAULT 0,
                expected_delivery_date DATE,
                actual_delivery_date DATE,
                remarks TEXT,
                status TEXT DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (po_id) REFERENCES procurement_purchase_orders(id) ON DELETE CASCADE
            )
        ''')

        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_po_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                field_name TEXT,
                old_value TEXT,
                new_value TEXT,
                change_reason TEXT,
                changed_by INTEGER,
                changed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (po_id) REFERENCES procurement_purchase_orders(id) ON DELETE CASCADE
            )
        ''')

        # ── Inbound Shipments ──────────────────────────────────────────────
        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_shipments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shipment_number TEXT UNIQUE NOT NULL,
                po_id INTEGER,
                supplier_id INTEGER,
                supplier_name TEXT,
                shipment_date DATE,
                eta DATE,
                actual_arrival_date DATE,
                status TEXT DEFAULT 'PREPARING',
                shipping_method TEXT,
                carrier_name TEXT,
                vessel_name TEXT,
                voyage_number TEXT,
                container_number TEXT,
                bl_number TEXT,
                port_of_loading TEXT,
                port_of_discharge TEXT,
                country_of_origin TEXT,
                customs_status TEXT DEFAULT 'PENDING',
                document_status TEXT DEFAULT 'PENDING',
                freight_cost REAL DEFAULT 0,
                insurance_cost REAL DEFAULT 0,
                customs_duty REAL DEFAULT 0,
                other_cost REAL DEFAULT 0,
                total_landed_cost REAL DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT,
                created_by INTEGER,
                FOREIGN KEY (po_id) REFERENCES procurement_purchase_orders(id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        ''')

        # ── Expected Receipts ──────────────────────────────────────────────
        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_expected_receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_id INTEGER NOT NULL,
                po_line_id INTEGER,
                supplier_id INTEGER,
                supplier_name TEXT,
                warehouse_id INTEGER,
                expected_date DATE,
                expected_qty REAL DEFAULT 0,
                received_qty REAL DEFAULT 0,
                pending_qty REAL DEFAULT 0,
                status TEXT DEFAULT 'PENDING',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT,
                FOREIGN KEY (po_id) REFERENCES procurement_purchase_orders(id),
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
            )
        ''')

        # ── Receiving & Discrepancies ─────────────────────────────────────
        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_receiving (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_number TEXT UNIQUE NOT NULL,
                po_id INTEGER NOT NULL,
                po_number TEXT,
                supplier_id INTEGER,
                supplier_name TEXT,
                warehouse_id INTEGER,
                receipt_date DATE,
                received_by INTEGER,
                status TEXT DEFAULT 'RECEIVED',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (po_id) REFERENCES procurement_purchase_orders(id),
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
            )
        ''')

        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_receiving_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receiving_id INTEGER NOT NULL,
                po_line_id INTEGER,
                item_id INTEGER,
                item_code TEXT,
                item_name TEXT,
                expected_qty REAL DEFAULT 0,
                received_qty REAL DEFAULT 0,
                accepted_qty REAL DEFAULT 0,
                rejected_qty REAL DEFAULT 0,
                damaged_qty REAL DEFAULT 0,
                short_qty REAL DEFAULT 0,
                excess_qty REAL DEFAULT 0,
                unit_cost REAL DEFAULT 0,
                line_total REAL DEFAULT 0,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (receiving_id) REFERENCES procurement_receiving(id) ON DELETE CASCADE
            )
        ''')

        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_discrepancies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discrepancy_number TEXT UNIQUE NOT NULL,
                receiving_id INTEGER,
                po_id INTEGER,
                po_number TEXT,
                supplier_id INTEGER,
                supplier_name TEXT,
                item_id INTEGER,
                item_name TEXT,
                discrepancy_type TEXT NOT NULL,
                expected_qty REAL DEFAULT 0,
                actual_qty REAL DEFAULT 0,
                variance_qty REAL DEFAULT 0,
                unit_cost REAL DEFAULT 0,
                financial_impact REAL DEFAULT 0,
                description TEXT,
                responsibility TEXT,
                resolution TEXT,
                status TEXT DEFAULT 'OPEN',
                claim_id INTEGER,
                resolved_by INTEGER,
                resolved_at TEXT,
                resolution_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT,
                created_by INTEGER,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        ''')

        # ── Claims & Returns ────────────────────────────────────────────────
        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim_number TEXT UNIQUE NOT NULL,
                claim_date DATE NOT NULL,
                claim_type TEXT NOT NULL,
                po_id INTEGER,
                po_number TEXT,
                receiving_id INTEGER,
                discrepancy_id INTEGER,
                supplier_id INTEGER NOT NULL,
                supplier_name TEXT,
                item_id INTEGER,
                item_name TEXT,
                part_number TEXT,
                affected_qty REAL DEFAULT 0,
                unit_cost REAL DEFAULT 0,
                total_amount REAL DEFAULT 0,
                issue_type TEXT NOT NULL,
                issue_description TEXT,
                requested_resolution TEXT,
                financial_impact REAL DEFAULT 0,
                status TEXT DEFAULT 'OPEN',
                resolution TEXT,
                credit_note_number TEXT,
                replacement_po_id INTEGER,
                final_amount REAL DEFAULT 0,
                closed_by INTEGER,
                closed_at TEXT,
                closure_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT,
                created_by INTEGER,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        ''')

        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_number TEXT UNIQUE NOT NULL,
                return_date DATE NOT NULL,
                claim_id INTEGER,
                po_id INTEGER,
                supplier_id INTEGER,
                supplier_name TEXT,
                item_id INTEGER,
                item_name TEXT,
                part_number TEXT,
                return_qty REAL DEFAULT 0,
                return_reason TEXT,
                return_type TEXT DEFAULT 'RETURN',
                return_status TEXT DEFAULT 'PENDING',
                credit_received INTEGER DEFAULT 0,
                credit_amount REAL DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT,
                created_by INTEGER,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        ''')

        # ── Contracts & Price Agreements ───────────────────────────────────
        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_contracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_number TEXT UNIQUE NOT NULL,
                contract_name TEXT,
                supplier_id INTEGER NOT NULL,
                supplier_name TEXT,
                contract_type TEXT DEFAULT 'STANDARD',
                start_date DATE,
                end_date DATE,
                status TEXT DEFAULT 'ACTIVE',
                total_value REAL DEFAULT 0,
                currency TEXT DEFAULT 'AED',
                payment_terms TEXT,
                incoterm TEXT,
                moq REAL DEFAULT 1,
                lead_time_commitment INTEGER,
                sla_terms TEXT,
                rebate_percent REAL DEFAULT 0,
                special_conditions TEXT,
                auto_renewal INTEGER DEFAULT 0,
                renewal_notice_days INTEGER DEFAULT 30,
                covered_brands TEXT,
                covered_item_groups TEXT,
                owner_id INTEGER,
                owner_name TEXT,
                notes TEXT,
                attachments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT,
                created_by INTEGER,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        ''')

        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_contract_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_id INTEGER NOT NULL,
                item_id INTEGER,
                item_code TEXT,
                item_name TEXT,
                brand TEXT,
                part_number TEXT,
                negotiated_price REAL DEFAULT 0,
                unit_of_measure TEXT DEFAULT 'PCS',
                min_qty REAL DEFAULT 1,
                max_qty REAL,
                valid_from DATE,
                valid_to DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contract_id) REFERENCES procurement_contracts(id) ON DELETE CASCADE
            )
        ''')

        # ── Procurement Budgets ─────────────────────────────────────────────
        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                budget_number TEXT UNIQUE NOT NULL,
                budget_name TEXT,
                budget_year INTEGER,
                budget_period TEXT,
                company_id INTEGER,
                department TEXT,
                category TEXT,
                amount REAL DEFAULT 0,
                spent_amount REAL DEFAULT 0,
                currency TEXT DEFAULT 'AED',
                status TEXT DEFAULT 'ACTIVE',
                approved_by INTEGER,
                approved_at TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT,
                created_by INTEGER,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
        ''')

        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_budget_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                budget_id INTEGER NOT NULL,
                period_month INTEGER,
                period_year INTEGER,
                allocated_amount REAL DEFAULT 0,
                spent_amount REAL DEFAULT 0,
                committed_amount REAL DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (budget_id) REFERENCES procurement_budgets(id) ON DELETE CASCADE
            )
        ''')

        # ── Procurement Alerts ─────────────────────────────────────────────
        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                alert_code TEXT,
                title TEXT NOT NULL,
                message TEXT,
                priority TEXT DEFAULT 'MEDIUM',
                severity TEXT DEFAULT 'MEDIUM',
                entity_type TEXT,
                entity_id INTEGER,
                supplier_id INTEGER,
                po_id INTEGER,
                requisition_id INTEGER,
                rfq_id INTEGER,
                claim_id INTEGER,
                is_read INTEGER DEFAULT 0,
                is_resolved INTEGER DEFAULT 0,
                resolved_by INTEGER,
                resolved_at TEXT,
                resolution_notes TEXT,
                expires_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        ''')

        # ── Procurement Audit Log ───────────────────────────────────────────
        db.execute('''
            CREATE TABLE IF NOT EXISTS procurement_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id INTEGER,
                entity_code TEXT,
                action TEXT NOT NULL,
                field_name TEXT,
                old_value TEXT,
                new_value TEXT,
                user_id INTEGER,
                user_name TEXT,
                user_role TEXT,
                ip_address TEXT,
                change_reason TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ── Indexes for Performance ────────────────────────────────────────
        db.execute("CREATE INDEX IF NOT EXISTS idx_req_status ON procurement_requisitions(status)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_req_requester ON procurement_requisitions(requester_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_req_date ON procurement_requisitions(requisition_date)")

        db.execute("CREATE INDEX IF NOT EXISTS idx_rfq_status ON procurement_rfqs(status)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_rfq_buyer ON procurement_rfqs(buyer_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_rfq_date ON procurement_rfqs(rfq_date)")

        db.execute("CREATE INDEX IF NOT EXISTS idx_quot_status ON procurement_quotations(status)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_quot_supplier ON procurement_quotations(supplier_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_quot_rfq ON procurement_quotations(rfq_id)")

        db.execute("CREATE INDEX IF NOT EXISTS idx_po_status ON procurement_purchase_orders(status)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_po_supplier ON procurement_purchase_orders(supplier_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_po_date ON procurement_purchase_orders(po_date)")

        db.execute("CREATE INDEX IF NOT EXISTS idx_claim_status ON procurement_claims(status)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_claim_supplier ON procurement_claims(supplier_id)")

        db.execute("CREATE INDEX IF NOT EXISTS idx_contract_supplier ON procurement_contracts(supplier_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_contract_status ON procurement_contracts(status)")

        db.execute("CREATE INDEX IF NOT EXISTS idx_alert_type ON procurement_alerts(alert_type)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_alert_entity ON procurement_alerts(entity_type, entity_id)")

        db.execute("CREATE INDEX IF NOT EXISTS idx_shipment_status ON procurement_shipments(status)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_shipment_po ON procurement_shipments(po_id)")

        db.commit()

        # Seed default procurement settings
        _seed_procurement_settings(db)


def _ensure_supplier_columns(db):
    """Ensure all procurement-related columns exist in the suppliers table."""
    # Get existing columns
    existing_cols = [row['name'] for row in db.execute("PRAGMA table_info(suppliers)").fetchall()]

    # Define columns to add (column_name, column_definition)
    columns_to_add = [
        ('supplier_type', "TEXT DEFAULT 'LOCAL'"),
        ('trade_name', "TEXT"),
        ('whatsapp', "TEXT"),
        ('website', "TEXT"),
        ('tax_number', "TEXT"),
        ('vat_number', "TEXT"),
        ('bank_name', "TEXT"),
        ('bank_account', "TEXT"),
        ('swift_code', "TEXT"),
        ('iban', "TEXT"),
        ('moq', "REAL DEFAULT 1"),
        ('order_multiple', "REAL DEFAULT 1"),
        ('lead_time_standard', "INTEGER"),
        ('lead_time_actual', "REAL DEFAULT 0"),
        ('is_preferred', "INTEGER DEFAULT 0"),
        ('is_strategic', "INTEGER DEFAULT 0"),
        ('is_emergency', "INTEGER DEFAULT 0"),
        ('is_blacklisted', "INTEGER DEFAULT 0"),
        ('risk_level', "TEXT DEFAULT 'LOW'"),
        ('performance_score', "REAL DEFAULT 0"),
        ('spend_ytd', "REAL DEFAULT 0"),
        ('spend_last_year', "REAL DEFAULT 0"),
        ('category', "TEXT"),
        ('subcategory', "TEXT"),
        ('related_brands', "TEXT"),
        ('related_item_groups', "TEXT"),
        ('notes', "TEXT"),
        ('internal_rating', "INTEGER DEFAULT 3"),
        ('contract_count', "INTEGER DEFAULT 0"),
        ('po_count', "INTEGER DEFAULT 0"),
        ('last_po_date', "TEXT"),
        ('last_rfq_date', "TEXT"),
    ]

    for col_name, col_def in columns_to_add:
        if col_name not in existing_cols:
            try:
                db.execute(f"ALTER TABLE suppliers ADD COLUMN {col_name} {col_def}")
            except Exception:
                pass  # Column may already exist


def _seed_procurement_settings(db):
    """Seed default procurement settings."""
    default_settings = [
        ('proc_requisition_prefix', 'PR', 'NUMBERING', 'Prefix for requisition numbers'),
        ('proc_rfq_prefix', 'RFQ', 'NUMBERING', 'Prefix for RFQ numbers'),
        ('proc_quotation_prefix', 'QT', 'NUMBERING', 'Prefix for quotation numbers'),
        ('proc_po_prefix', 'PO', 'NUMBERING', 'Prefix for purchase order numbers'),
        ('proc_claim_prefix', 'CLM', 'NUMBERING', 'Prefix for claim numbers'),
        ('proc_contract_prefix', 'CON', 'NUMBERING', 'Prefix for contract numbers'),
        ('proc_return_prefix', 'RET', 'NUMBERING', 'Prefix for return numbers'),
        ('proc_shipment_prefix', 'SHP', 'NUMBERING', 'Prefix for shipment numbers'),
        ('default_currency', 'AED', 'GENERAL', 'Default procurement currency'),
        ('default_incoterm', 'DDP', 'GENERAL', 'Default Incoterm'),
        ('default_payment_terms', 'Net 30', 'GENERAL', 'Default payment terms'),
        ('emergency_purchase_requires_approval', '1', 'APPROVAL', 'Emergency purchases require approval'),
        ('po_below_moq_requires_approval', '1', 'APPROVAL', 'PO below MOQ requires approval'),
        ('single_source_requires_justification', '1', 'APPROVAL', 'Single source purchase requires justification'),
        ('budget_exceed_requires_approval', '1', 'APPROVAL', 'Exceeding budget requires approval'),
        ('auto_convert_approved_requisition', '1', 'WORKFLOW', 'Auto-convert approved requisitions'),
        ('auto_create_rfq_from_requisition', '0', 'WORKFLOW', 'Auto-create RFQ from requisition'),
        ('require_rfq_before_po', '0', 'WORKFLOW', 'Require RFQ before creating PO'),
        ('supplier_response_sla_days', '7', 'SLA', 'RFQ response SLA in days'),
        ('requisition_approval_sla_hours', '24', 'SLA', 'Requisition approval SLA in hours'),
        ('claim_resolution_sla_days', '14', 'SLA', 'Claim resolution SLA in days'),
        ('contract_expiry_alert_days', '30', 'ALERTS', 'Days before contract expiry to alert'),
        ('rfq_expiry_alert_days', '3', 'ALERTS', 'Days before RFQ expiry to alert'),
        ('low_stock_alert_enabled', '1', 'ALERTS', 'Enable low stock procurement alerts'),
        ('delay_alert_enabled', '1', 'ALERTS', 'Enable delivery delay alerts'),
        ('budget_alert_threshold', '80', 'ALERTS', 'Budget usage % to trigger alert'),
    ]

    for key, value, category, description in default_settings:
        existing = db.execute(
            "SELECT id FROM procurement_settings WHERE setting_key = ?", (key,)
        ).fetchone()
        if not existing:
            db.execute(
                "INSERT INTO procurement_settings (setting_key, setting_value, category, description) VALUES (?, ?, ?, ?)",
                (key, value, category, description)
            )
    db.commit()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_next_sequence_number(prefix, table_name, date_field=None):
    """
    Generate the next sequence number for procurement documents.

    Args:
        prefix: Document prefix (PR, RFQ, PO, etc.)
        table_name: Database table to query
        date_field: Optional date field to filter by current year/month

    Returns:
        String like 'PR-2026-00001'
    """
    now = datetime.now()
    year = now.year
    month = now.month

    if date_field:
        seq_sql = f"""
            SELECT MAX(CAST(SUBSTR({date_field}, -5) AS INTEGER)) as max_seq
            FROM {table_name}
            WHERE {date_field} LIKE ?
        """
        result = get_one(seq_sql, (f'%{year}%',))
    else:
        seq_sql = f"""
            SELECT MAX(CAST(SUBSTR(code, -5) AS INTEGER)) as max_seq
            FROM {table_name}
            WHERE code LIKE ?
        """
        # Determine which column to use for code
        code_col = 'requisition_number' if 'requisition' in table_name else \
                   'rfq_number' if 'rfq' in table_name else \
                   'quotation_number' if 'quotation' in table_name else \
                   'po_number' if 'po' in table_name else \
                   'claim_number' if 'claim' in table_name else \
                   'contract_number' if 'contract' in table_name else \
                   'return_number' if 'return' in table_name else \
                   'shipment_number' if 'shipment' in table_name else 'code'

        seq_sql = f"""
            SELECT MAX(CAST(SUBSTR({code_col}, -5) AS INTEGER)) as max_seq
            FROM {table_name}
            WHERE {code_col} LIKE ?
        """
        result = get_one(seq_sql, (f'{prefix}-{year}%',))

    next_seq = (result['max_seq'] or 0) + 1 if result else 1
    return f"{prefix}-{year}-{next_seq:05d}"


def log_procurement_audit(entity_type, entity_id, entity_code, action, user_id=None,
                          user_name=None, field_name=None, old_value=None,
                          new_value=None, change_reason=None, notes=None, ip_address=None):
    """Log a procurement audit entry."""
    with get_db_context() as db:
        db.execute("""
            INSERT INTO procurement_audit_log
            (entity_type, entity_id, entity_code, action, field_name, old_value, new_value,
             user_id, user_name, ip_address, change_reason, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (entity_type, entity_id, entity_code, action, field_name, old_value, new_value,
              user_id, user_name, ip_address, change_reason, notes))
        db.commit()


# =============================================================================
# SUPPLIER MANAGEMENT
# =============================================================================

def get_suppliers(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """
    Get paginated list of suppliers with filters.

    Args:
        filters: Dict with keys like search, status, type, country, is_preferred
        page: Page number (1-indexed)
        per_page: Items per page

    Returns:
        Dict with items, total, page, per_page, pages
    """
    where_clauses = ["1=1"]
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(s.name LIKE ? OR s.code LIKE ? OR s.trade_name LIKE ?)")
            search = f"%{filters['search']}%"
            params.extend([search, search, search])

        if filters.get('status'):
            where_clauses.append("s.status = ?")
            params.append(filters['status'])

        if filters.get('supplier_type'):
            where_clauses.append("s.supplier_type = ?")
            params.append(filters['supplier_type'])

        if filters.get('country'):
            where_clauses.append("s.country = ?")
            params.append(filters['country'])

        if filters.get('is_preferred'):
            where_clauses.append("s.is_preferred = 1")

        if filters.get('is_strategic'):
            where_clauses.append("s.is_strategic = 1")

        if filters.get('is_blacklisted'):
            where_clauses.append("s.is_blacklisted = 1")

        if filters.get('risk_level'):
            where_clauses.append("s.risk_level = ?")
            params.append(filters['risk_level'])

    where_sql = " AND ".join(where_clauses)

    # Count total
    count_sql = f"SELECT COUNT(*) as cnt FROM suppliers s WHERE {where_sql}"
    total = get_one(count_sql, params)['cnt']

    # Get paginated results
    offset = (page - 1) * per_page
    sql = f"""
        SELECT s.*,
               (SELECT COUNT(*) FROM procurement_contracts pc WHERE pc.supplier_id = s.id AND pc.status = 'ACTIVE') as active_contracts,
               (SELECT COUNT(*) FROM procurement_purchase_orders po WHERE po.supplier_id = s.id) as total_pos,
               (SELECT SUM(total_amount) FROM procurement_purchase_orders po WHERE po.supplier_id = s.id AND strftime('%Y', po.po_date) = strftime('%Y', 'now')) as spend_ytd
        FROM suppliers s
        WHERE {where_sql}
        ORDER BY s.name ASC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        items = [dict(row) for row in rows]

    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page if total > 0 else 1
    }


def get_supplier_by_id(supplier_id: int) -> Optional[Dict]:
    """Get a single supplier by ID with full details."""
    with get_db_context() as db:
        supplier = db.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,)).fetchone()
        if not supplier:
            return None

        result = dict(supplier)

        # Get contacts
        result['contacts'] = db.execute(
            "SELECT * FROM procurement_supplier_contacts WHERE supplier_id = ? ORDER BY is_primary DESC, contact_name",
            (supplier_id,)
        ).fetchall()

        # Get brands/item groups
        result['brands'] = db.execute(
            "SELECT * FROM procurement_supplier_brands WHERE supplier_id = ?",
            (supplier_id,)
        ).fetchall()

        # Get performance metrics (last 12 months)
        result['metrics'] = db.execute("""
            SELECT * FROM procurement_supplier_metrics
            WHERE supplier_id = ?
            ORDER BY metric_date DESC
            LIMIT 12
        """, (supplier_id,)).fetchall()

        # Get recent POs
        result['recent_pos'] = db.execute("""
            SELECT po_number, po_date, total_amount, status
            FROM procurement_purchase_orders
            WHERE supplier_id = ?
            ORDER BY created_at DESC
            LIMIT 5
        """, (supplier_id,)).fetchall()

        # Get active contracts
        result['active_contracts'] = db.execute("""
            SELECT contract_number, contract_name, end_date, total_value
            FROM procurement_contracts
            WHERE supplier_id = ? AND status = 'ACTIVE'
            ORDER BY end_date ASC
        """, (supplier_id,)).fetchall()

        return result


def create_supplier(data: Dict, user_id: int = None) -> int:
    """Create a new supplier."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO suppliers (
                name, code, supplier_type, trade_name, contact_person, email, phone,
                whatsapp, address, city, country, region, payment_terms, lead_time,
                currency, margin, rating, status, notes, website, tax_number, vat_number,
                bank_name, bank_account, swift_code, iban, moq, order_multiple,
                lead_time_standard, is_preferred, is_strategic, is_emergency, risk_level,
                category, subcategory, related_brands, related_item_groups,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            data.get('name'), data.get('code'), data.get('supplier_type', 'LOCAL'),
            data.get('trade_name'), data.get('contact_person'), data.get('email'),
            data.get('phone'), data.get('whatsapp'), data.get('address'),
            data.get('city'), data.get('country'), data.get('region'),
            data.get('payment_terms'), data.get('lead_time'), data.get('currency'),
            data.get('margin'), data.get('rating'), data.get('status', 'Active'),
            data.get('notes'), data.get('website'), data.get('tax_number'),
            data.get('vat_number'), data.get('bank_name'), data.get('bank_account'),
            data.get('swift_code'), data.get('iban'), data.get('moq', 1),
            data.get('order_multiple', 1), data.get('lead_time_standard'),
            data.get('is_preferred', 0), data.get('is_strategic', 0),
            data.get('is_emergency', 0), data.get('risk_level', 'LOW'),
            data.get('category'), data.get('subcategory'),
            data.get('related_brands'), data.get('related_item_groups')
        ))
        db.commit()
        supplier_id = cursor.lastrowid

        # Log audit
        log_procurement_audit('SUPPLIER', supplier_id, data.get('code'), 'CREATE',
                              user_id=user_id)

        return supplier_id


def update_supplier(supplier_id: int, data: Dict, user_id: int = None) -> bool:
    """Update an existing supplier."""
    # Build update query dynamically
    fields = []
    values = []

    allowed_fields = [
        'name', 'code', 'supplier_type', 'trade_name', 'contact_person', 'email',
        'phone', 'whatsapp', 'address', 'city', 'country', 'region', 'payment_terms',
        'lead_time', 'currency', 'margin', 'rating', 'status', 'notes', 'website',
        'tax_number', 'vat_number', 'bank_name', 'bank_account', 'swift_code', 'iban',
        'moq', 'order_multiple', 'lead_time_standard', 'is_preferred', 'is_strategic',
        'is_emergency', 'is_blacklisted', 'risk_level', 'category', 'subcategory',
        'related_brands', 'related_item_groups'
    ]

    for field in allowed_fields:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])

    if not fields:
        return False

    values.append(supplier_id)

    with get_db_context() as db:
        db.execute(f"""
            UPDATE suppliers SET {', '.join(fields)}, updated_at = datetime('now')
            WHERE id = ?
        """, values)
        db.commit()

        # Log audit
        supplier = db.execute("SELECT code FROM suppliers WHERE id = ?", (supplier_id,)).fetchone()
        log_procurement_audit('SUPPLIER', supplier_id, supplier['code'] if supplier else str(supplier_id),
                              'UPDATE', user_id=user_id)

    return True


# =============================================================================
# PURCHASE REQUISITIONS
# =============================================================================

def get_requisitions(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get paginated list of purchase requisitions."""
    where_clauses = ["1=1"]
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(pr.requisition_number LIKE ? OR pr.requester_name LIKE ?)")
            search = f"%{filters['search']}%"
            params.extend([search, search])

        if filters.get('status'):
            where_clauses.append("pr.status = ?")
            params.append(filters['status'])

        if filters.get('priority'):
            where_clauses.append("pr.priority = ?")
            params.append(filters['priority'])

        if filters.get('urgency'):
            where_clauses.append("pr.urgency = ?")
            params.append(filters['urgency'])

        if filters.get('requester_id'):
            where_clauses.append("pr.requester_id = ?")
            params.append(filters['requester_id'])

        if filters.get('department'):
            where_clauses.append("pr.department = ?")
            params.append(filters['department'])

        if filters.get('warehouse_id'):
            where_clauses.append("pr.warehouse_id = ?")
            params.append(filters['warehouse_id'])

        if filters.get('source_type'):
            where_clauses.append("pr.source_type = ?")
            params.append(filters['source_type'])

        if filters.get('date_from'):
            where_clauses.append("pr.requisition_date >= ?")
            params.append(filters['date_from'])

        if filters.get('date_to'):
            where_clauses.append("pr.requisition_date <= ?")
            params.append(filters['date_to'])

    where_sql = " AND ".join(where_clauses)

    count_sql = f"SELECT COUNT(*) as cnt FROM procurement_requisitions pr WHERE {where_sql}"
    total = get_one(count_sql, params)['cnt']

    offset = (page - 1) * per_page
    sql = f"""
        SELECT pr.*,
               (SELECT COUNT(*) FROM procurement_requisition_lines prl WHERE prl.requisition_id = pr.id) as line_count,
               u.username as creator_name
        FROM procurement_requisitions pr
        LEFT JOIN users u ON pr.created_by = u.id
        WHERE {where_sql}
        ORDER BY pr.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        items = [dict(row) for row in rows]

    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page if total > 0 else 1
    }


def get_requisition_by_id(requisition_id: int) -> Optional[Dict]:
    """Get a single requisition by ID with lines."""
    with get_db_context() as db:
        req = db.execute("SELECT * FROM procurement_requisitions WHERE id = ?", (requisition_id,)).fetchone()
        if not req:
            return None

        result = dict(req)

        # Get lines
        result['lines'] = db.execute("""
            SELECT * FROM procurement_requisition_lines
            WHERE requisition_id = ?
            ORDER BY line_number
        """, (requisition_id,)).fetchall()

        # Get history/audit trail
        result['history'] = db.execute("""
            SELECT * FROM procurement_audit_log
            WHERE entity_type = 'REQUISITION' AND entity_id = ?
            ORDER BY created_at DESC
        """, (requisition_id,)).fetchall()

        return result


def create_requisition(data: Dict, lines: List[Dict], user_id: int = None) -> int:
    """Create a new purchase requisition with lines."""
    requisition_number = get_next_sequence_number('PR', 'procurement_requisitions', 'requisition_date')

    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO procurement_requisitions (
                requisition_number, requisition_date, requisition_time, requester_id,
                requester_name, department, company_id, branch_id, warehouse_id,
                source_type, priority, urgency, status, total_estimated_amount,
                currency, notes, internal_notes, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            requisition_number,
            data.get('requisition_date', datetime.now().strftime('%Y-%m-%d')),
            data.get('requisition_time', datetime.now().strftime('%H:%M')),
            data.get('requester_id'),
            data.get('requester_name'),
            data.get('department'),
            data.get('company_id'),
            data.get('branch_id'),
            data.get('warehouse_id'),
            data.get('source_type', 'MANUAL'),
            data.get('priority', 'MEDIUM'),
            data.get('urgency', 'NORMAL'),
            'DRAFT',
            data.get('total_estimated_amount', 0),
            data.get('currency', 'AED'),
            data.get('notes'),
            data.get('internal_notes'),
            user_id
        ))
        db.commit()
        requisition_id = cursor.lastrowid

        # Insert lines
        total_amount = 0
        for i, line in enumerate(lines, 1):
            line_total = (line.get('requested_qty', 0) or 0) * (line.get('estimated_unit_price', 0) or 0)
            total_amount += line_total

            db.execute("""
                INSERT INTO procurement_requisition_lines (
                    requisition_id, line_number, item_id, item_code, item_name,
                    description, brand, part_number, requested_qty, unit_of_measure,
                    required_date, preferred_supplier_id, preferred_supplier_name,
                    estimated_unit_price, estimated_total_price, current_stock,
                    reserved_stock, open_demand, open_purchase_qty, purpose, remarks
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                requisition_id, i, line.get('item_id'), line.get('item_code'),
                line.get('item_name'), line.get('description'), line.get('brand'),
                line.get('part_number'), line.get('requested_qty', 0),
                line.get('unit_of_measure', 'PCS'), line.get('required_date'),
                line.get('preferred_supplier_id'), line.get('preferred_supplier_name'),
                line.get('estimated_unit_price', 0), line_total,
                line.get('current_stock', 0), line.get('reserved_stock', 0),
                line.get('open_demand', 0), line.get('open_purchase_qty', 0),
                line.get('purpose'), line.get('remarks')
            ))

        # Update total
        db.execute("""
            UPDATE procurement_requisitions
            SET total_estimated_amount = ?
            WHERE id = ?
        """, (total_amount, requisition_id))
        db.commit()

        log_procurement_audit('REQUISITION', requisition_id, requisition_number, 'CREATE',
                              user_id=user_id)

        return requisition_id


def update_requisition_status(requisition_id: int, new_status: str, user_id: int = None,
                               rejection_reason: str = None, approver_id: int = None) -> bool:
    """Update requisition status with proper workflow."""
    with get_db_context() as db:
        # Get current status
        req = db.execute("SELECT status, requisition_number FROM procurement_requisitions WHERE id = ?",
                        (requisition_id,)).fetchone()
        if not req:
            return False

        old_status = req['status']

        # Update status
        update_sql = "UPDATE procurement_requisitions SET status = ?, updated_at = datetime('now')"
        update_params = [new_status]

        if new_status == 'APPROVED' and approver_id:
            update_sql += ", approved_by = ?, approved_at = datetime('now')"
            update_params.append(approver_id)

        if new_status == 'REJECTED' and rejection_reason:
            update_sql += ", rejection_reason = ?"
            update_params.append(rejection_reason)

        update_sql += " WHERE id = ?"
        update_params.append(requisition_id)

        db.execute(update_sql, update_params)
        db.commit()

        log_procurement_audit('REQUISITION', requisition_id, req['requisition_number'],
                              f'STATUS_CHANGE: {old_status} -> {new_status}',
                              user_id=user_id,
                              old_value=old_status, new_value=new_value)

    return True


# =============================================================================
# RFQ MANAGEMENT
# =============================================================================

def get_rfqs(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get paginated list of RFQs."""
    where_clauses = ["1=1"]
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(prf.rfq_number LIKE ? OR prf.buyer_name LIKE ?)")
            search = f"%{filters['search']}%"
            params.extend([search, search])

        if filters.get('status'):
            where_clauses.append("prf.status = ?")
            params.append(filters['status'])

        if filters.get('buyer_id'):
            where_clauses.append("prf.buyer_id = ?")
            params.append(filters['buyer_id'])

        if filters.get('date_from'):
            where_clauses.append("prf.rfq_date >= ?")
            params.append(filters['date_from'])

        if filters.get('date_to'):
            where_clauses.append("prf.rfq_date <= ?")
            params.append(filters['date_to'])

    where_sql = " AND ".join(where_clauses)

    count_sql = f"SELECT COUNT(*) as cnt FROM procurement_rfqs prf WHERE {where_sql}"
    total = get_one(count_sql, params)['cnt']

    offset = (page - 1) * per_page
    sql = f"""
        SELECT prf.*,
               (SELECT COUNT(*) FROM procurement_rfq_suppliers prfs WHERE prfs.rfq_id = prf.id) as supplier_count,
               (SELECT COUNT(*) FROM procurement_rfq_suppliers prfs WHERE prfs.rfq_id = prf.id AND prfs.is_responded = 1) as response_count,
               u.username as creator_name
        FROM procurement_rfqs prf
        LEFT JOIN users u ON prf.created_by = u.id
        WHERE {where_sql}
        ORDER BY prf.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        items = [dict(row) for row in rows]

    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page if total > 0 else 1
    }


def get_rfq_by_id(rfq_id: int) -> Optional[Dict]:
    """Get a single RFQ by ID with lines and suppliers."""
    with get_db_context() as db:
        rfq = db.execute("SELECT * FROM procurement_rfqs WHERE id = ?", (rfq_id,)).fetchone()
        if not rfq:
            return None

        result = dict(rfq)

        # Get lines
        result['lines'] = db.execute("""
            SELECT * FROM procurement_rfq_lines WHERE rfq_id = ? ORDER BY line_number
        """, (rfq_id,)).fetchall()

        # Get suppliers
        result['suppliers'] = db.execute("""
            SELECT prfs.*, s.supplier_type, s.country, s.rating
            FROM procurement_rfq_suppliers prfs
            LEFT JOIN suppliers s ON prfs.supplier_id = s.id
            WHERE prfs.rfq_id = ?
        """, (rfq_id,)).fetchall()

        # Get quotations received
        result['quotations'] = db.execute("""
            SELECT pq.*, s.supplier_type, s.country
            FROM procurement_quotations pq
            LEFT JOIN suppliers s ON pq.supplier_id = s.id
            WHERE pq.rfq_id = ?
            ORDER BY pq.status, pq.total_amount
        """, (rfq_id,)).fetchall()

        return result


def create_rfq(data: Dict, lines: List[Dict], supplier_ids: List[int], user_id: int = None) -> int:
    """Create a new RFQ with lines and suppliers."""
    rfq_number = get_next_sequence_number('RFQ', 'procurement_rfqs', 'rfq_date')

    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO procurement_rfqs (
                rfq_number, rfq_date, buyer_id, buyer_name, company_id, warehouse_id,
                source_requisition_id, currency, status, response_due_date,
                requested_delivery_date, incoterm, payment_terms, shipping_method,
                delivery_address, urgency, notes, internal_notes, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rfq_number,
            data.get('rfq_date', datetime.now().strftime('%Y-%m-%d')),
            data.get('buyer_id'),
            data.get('buyer_name'),
            data.get('company_id'),
            data.get('warehouse_id'),
            data.get('source_requisition_id'),
            data.get('currency', 'AED'),
            'DRAFT',
            data.get('response_due_date'),
            data.get('requested_delivery_date'),
            data.get('incoterm'),
            data.get('payment_terms'),
            data.get('shipping_method'),
            data.get('delivery_address'),
            data.get('urgency', 'NORMAL'),
            data.get('notes'),
            data.get('internal_notes'),
            user_id
        ))
        db.commit()
        rfq_id = cursor.lastrowid

        # Insert lines
        for i, line in enumerate(lines, 1):
            db.execute("""
                INSERT INTO procurement_rfq_lines (
                    rfq_id, line_number, requisition_line_id, item_id, item_code,
                    item_name, brand, part_number, requested_qty, unit_of_measure,
                    specifications, target_price
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rfq_id, i, line.get('requisition_line_id'), line.get('item_id'),
                line.get('item_code'), line.get('item_name'), line.get('brand'),
                line.get('part_number'), line.get('requested_qty', 0),
                line.get('unit_of_measure', 'PCS'), line.get('specifications'),
                line.get('target_price')
            ))

        # Insert suppliers
        for supplier_id in supplier_ids:
            supplier = db.execute("SELECT name, contact_person, email FROM suppliers WHERE id = ?",
                                 (supplier_id,)).fetchone()
            if supplier:
                db.execute("""
                    INSERT INTO procurement_rfq_suppliers (
                        rfq_id, supplier_id, supplier_name, contact_person, contact_email
                    ) VALUES (?, ?, ?, ?, ?)
                """, (rfq_id, supplier_id, supplier['name'],
                      supplier['contact_person'], supplier['email']))

        db.commit()

        log_procurement_audit('RFQ', rfq_id, rfq_number, 'CREATE', user_id=user_id)

        return rfq_id


# =============================================================================
# QUOTATION MANAGEMENT
# =============================================================================

def get_quotations(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get paginated list of quotations."""
    where_clauses = ["1=1"]
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(pq.quotation_number LIKE ? OR pq.supplier_name LIKE ?)")
            search = f"%{filters['search']}%"
            params.extend([search, search])

        if filters.get('status'):
            where_clauses.append("pq.status = ?")
            params.append(filters['status'])

        if filters.get('supplier_id'):
            where_clauses.append("pq.supplier_id = ?")
            params.append(filters['supplier_id'])

        if filters.get('rfq_id'):
            where_clauses.append("pq.rfq_id = ?")
            params.append(filters['rfq_id'])

        if filters.get('is_winner'):
            where_clauses.append("pq.is_winner = 1")

    where_sql = " AND ".join(where_clauses)

    count_sql = f"SELECT COUNT(*) as cnt FROM procurement_quotations pq WHERE {where_sql}"
    total = get_one(count_sql, params)['cnt']

    offset = (page - 1) * per_page
    sql = f"""
        SELECT pq.*,
               prf.rfq_number,
               s.supplier_type, s.country as supplier_country, s.rating as supplier_rating
        FROM procurement_quotations pq
        LEFT JOIN procurement_rfqs prf ON pq.rfq_id = prf.id
        LEFT JOIN suppliers s ON pq.supplier_id = s.id
        WHERE {where_sql}
        ORDER BY pq.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        items = [dict(row) for row in rows]

    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page if total > 0 else 1
    }


def get_quotation_by_id(quotation_id: int) -> Optional[Dict]:
    """Get a single quotation by ID with lines."""
    with get_db_context() as db:
        quote = db.execute("SELECT * FROM procurement_quotations WHERE id = ?", (quotation_id,)).fetchone()
        if not quote:
            return None

        result = dict(quote)

        # Get lines
        result['lines'] = db.execute("""
            SELECT pql.*, pqrfl.requested_qty as rfq_requested_qty
            FROM procurement_quotation_lines pql
            LEFT JOIN procurement_rfq_lines pqrfl ON pql.rfq_line_id = pqrfl.id
            WHERE pql.quotation_id = ?
            ORDER BY pql.line_number
        """, (quotation_id,)).fetchall()

        # Get RFQ info
        if result['rfq_id']:
            result['rfq'] = db.execute("SELECT * FROM procurement_rfqs WHERE id = ?",
                                      (result['rfq_id'],)).fetchone()

        return result


def create_quotation(data: Dict, lines: List[Dict], user_id: int = None) -> int:
    """Create a new quotation with lines."""
    quotation_number = get_next_sequence_number('QT', 'procurement_quotations', 'quotation_date')

    with get_db_context() as db:
        # Calculate totals
        subtotal = 0
        for line in lines:
            line_total = (line.get('quoted_qty', 0) or 0) * (line.get('final_unit_price', 0) or 0)
            subtotal += line_total

        total_amount = subtotal + (data.get('freight_cost', 0) or 0) + (data.get('other_charges', 0) or 0)

        cursor = db.execute("""
            INSERT INTO procurement_quotations (
                quotation_number, rfq_id, supplier_id, supplier_name, quotation_date,
                validity_date, status, version, currency, incoterm, payment_terms,
                lead_time_days, moq, order_multiple, freight_cost, other_charges,
                total_amount, notes, internal_notes, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            quotation_number,
            data.get('rfq_id'),
            data.get('supplier_id'),
            data.get('supplier_name'),
            data.get('quotation_date', datetime.now().strftime('%Y-%m-%d')),
            data.get('validity_date'),
            'DRAFT',
            data.get('version', 1),
            data.get('currency', 'AED'),
            data.get('incoterm'),
            data.get('payment_terms'),
            data.get('lead_time_days'),
            data.get('moq', 1),
            data.get('order_multiple', 1),
            data.get('freight_cost', 0),
            data.get('other_charges', 0),
            total_amount,
            data.get('notes'),
            data.get('internal_notes'),
            user_id
        ))
        db.commit()
        quotation_id = cursor.lastrowid

        # Insert lines
        for i, line in enumerate(lines, 1):
            line_total = (line.get('quoted_qty', 0) or 0) * (line.get('final_unit_price', 0) or 0)

            db.execute("""
                INSERT INTO procurement_quotation_lines (
                    quotation_id, line_number, rfq_line_id, item_id, item_code,
                    item_name, brand, part_number, quoted_qty, unit_of_measure,
                    unit_price, discount_percent, final_unit_price, line_total,
                    requested_qty
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                quotation_id, i, line.get('rfq_line_id'), line.get('item_id'),
                line.get('item_code'), line.get('item_name'), line.get('brand'),
                line.get('part_number'), line.get('quoted_qty', 0),
                line.get('unit_of_measure', 'PCS'), line.get('unit_price', 0),
                line.get('discount_percent', 0),
                line.get('final_unit_price', line.get('unit_price', 0)),
                line_total, line.get('requested_qty', 0)
            ))

        # Mark supplier as responded in RFQ
        if data.get('rfq_id'):
            db.execute("""
                UPDATE procurement_rfq_suppliers
                SET is_responded = 1, response_date = ?
                WHERE rfq_id = ? AND supplier_id = ?
            """, (datetime.now().strftime('%Y-%m-%d'), data.get('rfq_id'), data.get('supplier_id')))

            # Check if all suppliers responded
            total_suppliers = db.execute("""
                SELECT COUNT(*) as cnt FROM procurement_rfq_suppliers WHERE rfq_id = ?
            """, (data.get('rfq_id'),)).fetchone()['cnt']

            responded_suppliers = db.execute("""
                SELECT COUNT(*) as cnt FROM procurement_rfq_suppliers
                WHERE rfq_id = ? AND is_responded = 1
            """, (data.get('rfq_id'),)).fetchone()['cnt']

            if responded_suppliers == total_suppliers:
                db.execute("UPDATE procurement_rfqs SET status = 'FULLY_RECEIVED' WHERE id = ?",
                          (data.get('rfq_id'),))
            else:
                db.execute("UPDATE procurement_rfqs SET status = 'PARTIALLY_RECEIVED' WHERE id = ?",
                          (data.get('rfq_id'),))

        db.commit()

        log_procurement_audit('QUOTATION', quotation_id, quotation_number, 'CREATE', user_id=user_id)

        return quotation_id


# =============================================================================
# PURCHASE ORDERS
# =============================================================================

def get_purchase_orders(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get paginated list of purchase orders."""
    where_clauses = ["1=1"]
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(ppo.po_number LIKE ? OR ppo.supplier_name LIKE ?)")
            search = f"%{filters['search']}%"
            params.extend([search, search])

        if filters.get('status'):
            where_clauses.append("ppo.status = ?")
            params.append(filters['status'])

        if filters.get('po_type'):
            where_clauses.append("ppo.po_type = ?")
            params.append(filters['po_type'])

        if filters.get('supplier_id'):
            where_clauses.append("ppo.supplier_id = ?")
            params.append(filters['supplier_id'])

        if filters.get('buyer_id'):
            where_clauses.append("ppo.buyer_id = ?")
            params.append(filters['buyer_id'])

        if filters.get('date_from'):
            where_clauses.append("ppo.po_date >= ?")
            params.append(filters['date_from'])

        if filters.get('date_to'):
            where_clauses.append("ppo.po_date <= ?")
            params.append(filters['date_to'])

        if filters.get('is_overdue'):
            where_clauses.append("ppo.expected_delivery_date < ? AND ppo.status NOT IN ('RECEIVED', 'CLOSED', 'CANCELLED')")
            params.append(datetime.now().strftime('%Y-%m-%d'))

    where_sql = " AND ".join(where_clauses)

    count_sql = f"SELECT COUNT(*) as cnt FROM procurement_purchase_orders ppo WHERE {where_sql}"
    total = get_one(count_sql, params)['cnt']

    offset = (page - 1) * per_page
    sql = f"""
        SELECT ppo.*,
               s.supplier_type, s.country as supplier_country,
               (SELECT SUM(received_qty * final_unit_price) FROM procurement_po_lines WHERE po_id = ppo.id) as received_value,
               u.username as creator_name
        FROM procurement_purchase_orders ppo
        LEFT JOIN suppliers s ON ppo.supplier_id = s.id
        LEFT JOIN users u ON ppo.created_by = u.id
        WHERE {where_sql}
        ORDER BY ppo.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        items = [dict(row) for row in rows]

    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page if total > 0 else 1
    }


def get_purchase_order_by_id(po_id: int) -> Optional[Dict]:
    """Get a single PO by ID with lines and history."""
    with get_db_context() as db:
        po = db.execute("SELECT * FROM procurement_purchase_orders WHERE id = ?", (po_id,)).fetchone()
        if not po:
            return None

        result = dict(po)

        # Get lines
        result['lines'] = db.execute("""
            SELECT ppl.*
            FROM procurement_po_lines ppl
            WHERE ppl.po_id = ?
            ORDER BY ppl.line_number
        """, (po_id,)).fetchall()

        # Get history
        result['history'] = db.execute("""
            SELECT * FROM procurement_po_history
            WHERE po_id = ?
            ORDER BY changed_at DESC
        """, (po_id,)).fetchall()

        # Get related shipments
        result['shipments'] = db.execute("""
            SELECT * FROM procurement_shipments
            WHERE po_id = ?
            ORDER BY created_at DESC
        """, (po_id,)).fetchall()

        # Get expected receipts
        result['expected_receipts'] = db.execute("""
            SELECT * FROM procurement_expected_receipts
            WHERE po_id = ?
            ORDER BY expected_date
        """, (po_id,)).fetchall()

        return result


def create_purchase_order(data: Dict, lines: List[Dict], user_id: int = None) -> int:
    """Create a new purchase order with lines."""
    po_number = get_next_sequence_number('PO', 'procurement_purchase_orders', 'po_date')

    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO procurement_purchase_orders (
                po_number, po_date, po_type, supplier_id, supplier_name, buyer_id,
                buyer_name, company_id, branch_id, warehouse_id, source_requisition_id,
                source_rfq_id, source_quotation_id, source_vendor_selection_id,
                currency, payment_terms, incoterm, shipment_method, delivery_address,
                expected_ship_date, expected_delivery_date, status, approval_status,
                subtotal, discount_amount, tax_amount, freight_cost, other_charges,
                total_amount, notes, internal_notes, terms_conditions, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            po_number,
            data.get('po_date', datetime.now().strftime('%Y-%m-%d')),
            data.get('po_type', 'STANDARD'),
            data.get('supplier_id'),
            data.get('supplier_name'),
            data.get('buyer_id'),
            data.get('buyer_name'),
            data.get('company_id'),
            data.get('branch_id'),
            data.get('warehouse_id'),
            data.get('source_requisition_id'),
            data.get('source_rfq_id'),
            data.get('source_quotation_id'),
            data.get('source_vendor_selection_id'),
            data.get('currency', 'AED'),
            data.get('payment_terms'),
            data.get('incoterm'),
            data.get('shipment_method'),
            data.get('delivery_address'),
            data.get('expected_ship_date'),
            data.get('expected_delivery_date'),
            'DRAFT',
            'PENDING',
            data.get('subtotal', 0),
            data.get('discount_amount', 0),
            data.get('tax_amount', 0),
            data.get('freight_cost', 0),
            data.get('other_charges', 0),
            data.get('total_amount', 0),
            data.get('notes'),
            data.get('internal_notes'),
            data.get('terms_conditions'),
            user_id
        ))
        db.commit()
        po_id = cursor.lastrowid

        # Insert lines and calculate totals
        subtotal = 0
        for i, line in enumerate(lines, 1):
            line_total = (line.get('ordered_qty', 0) or 0) * (line.get('final_unit_price', 0) or 0)
            subtotal += line_total

            db.execute("""
                INSERT INTO procurement_po_lines (
                    po_id, line_number, requisition_line_id, rfq_line_id, quotation_line_id,
                    item_id, item_code, item_name, brand, part_number, ordered_qty,
                    unit_of_measure, unit_price, discount_percent, final_unit_price,
                    line_total, expected_delivery_date, remarks, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                po_id, i, line.get('requisition_line_id'), line.get('rfq_line_id'),
                line.get('quotation_line_id'), line.get('item_id'), line.get('item_code'),
                line.get('item_name'), line.get('brand'), line.get('part_number'),
                line.get('ordered_qty', 0), line.get('unit_of_measure', 'PCS'),
                line.get('unit_price', 0), line.get('discount_percent', 0),
                line.get('final_unit_price', line.get('unit_price', 0)),
                line_total, line.get('expected_delivery_date'),
                line.get('remarks'), 'PENDING'
            ))

        # Update PO totals
        tax_amount = (subtotal - (data.get('discount_amount', 0) or 0)) * 0.05  # 5% VAT
        total_amount = subtotal - (data.get('discount_amount', 0) or 0) + tax_amount + \
                      (data.get('freight_cost', 0) or 0) + (data.get('other_charges', 0) or 0)

        db.execute("""
            UPDATE procurement_purchase_orders
            SET subtotal = ?, tax_amount = ?, total_amount = ?
            WHERE id = ?
        """, (subtotal, tax_amount, total_amount, po_id))

        # Create expected receipts
        for line in lines:
            if line.get('ordered_qty', 0) > 0:
                db.execute("""
                    INSERT INTO procurement_expected_receipts (
                        po_id, po_line_id, supplier_id, supplier_name, warehouse_id,
                        expected_date, expected_qty, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    po_id, line.get('po_line_id'), data.get('supplier_id'),
                    data.get('supplier_name'), data.get('warehouse_id'),
                    data.get('expected_delivery_date'), line.get('ordered_qty', 0),
                    'PENDING'
                ))

        # Update quotation as winner if applicable
        if data.get('source_quotation_id'):
            db.execute("""
                UPDATE procurement_quotations
                SET is_winner = 1, is_accepted = 1
                WHERE id = ?
            """, (data.get('source_quotation_id'),))

        # Update requisition status if linked
        if data.get('source_requisition_id'):
            db.execute("""
                UPDATE procurement_requisitions
                SET status = 'PARTIALLY_CONVERTED'
                WHERE id = ?
            """, (data.get('source_requisition_id'),))

        db.commit()

        log_procurement_audit('PO', po_id, po_number, 'CREATE', user_id=user_id)

        return po_id


# =============================================================================
# CLAIMS & RETURNS
# =============================================================================

def get_claims(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get paginated list of claims."""
    where_clauses = ["1=1"]
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(pc.claim_number LIKE ? OR pc.supplier_name LIKE ?)")
            search = f"%{filters['search']}%"
            params.extend([search, search])

        if filters.get('status'):
            where_clauses.append("pc.status = ?")
            params.append(filters['status'])

        if filters.get('claim_type'):
            where_clauses.append("pc.claim_type = ?")
            params.append(filters['claim_type'])

        if filters.get('supplier_id'):
            where_clauses.append("pc.supplier_id = ?")
            params.append(filters['supplier_id'])

    where_sql = " AND ".join(where_clauses)

    count_sql = f"SELECT COUNT(*) as cnt FROM procurement_claims pc WHERE {where_sql}"
    total = get_one(count_sql, params)['cnt']

    offset = (page - 1) * per_page
    sql = f"""
        SELECT pc.*, ppo.po_number, s.supplier_type, s.country as supplier_country
        FROM procurement_claims pc
        LEFT JOIN procurement_purchase_orders ppo ON pc.po_id = ppo.id
        LEFT JOIN suppliers s ON pc.supplier_id = s.id
        WHERE {where_sql}
        ORDER BY pc.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        items = [dict(row) for row in rows]

    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page if total > 0 else 1
    }


def create_claim(data: Dict, user_id: int = None) -> int:
    """Create a new claim."""
    claim_number = get_next_sequence_number('CLM', 'procurement_claims', 'claim_date')

    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO procurement_claims (
                claim_number, claim_date, claim_type, po_id, po_number,
                receiving_id, discrepancy_id, supplier_id, supplier_name,
                item_id, item_name, part_number, affected_qty, unit_cost,
                total_amount, issue_type, issue_description, requested_resolution,
                financial_impact, status, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            claim_number,
            data.get('claim_date', datetime.now().strftime('%Y-%m-%d')),
            data.get('claim_type', 'QUALITY'),
            data.get('po_id'),
            data.get('po_number'),
            data.get('receiving_id'),
            data.get('discrepancy_id'),
            data.get('supplier_id'),
            data.get('supplier_name'),
            data.get('item_id'),
            data.get('item_name'),
            data.get('part_number'),
            data.get('affected_qty', 0),
            data.get('unit_cost', 0),
            data.get('total_amount', 0),
            data.get('issue_type'),
            data.get('issue_description'),
            data.get('requested_resolution', 'CREDIT'),
            data.get('financial_impact', 0),
            'OPEN',
            user_id
        ))
        db.commit()

        log_procurement_audit('CLAIM', cursor.lastrowid, claim_number, 'CREATE', user_id=user_id)

        return cursor.lastrowid


def create_return(data: Dict, user_id: int = None) -> int:
    """Create a new return."""
    return_number = get_next_sequence_number('RET', 'procurement_returns', 'return_date')

    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO procurement_returns (
                return_number, return_date, claim_id, po_id, supplier_id,
                supplier_name, item_id, item_name, part_number, return_qty,
                return_reason, return_type, return_status, notes, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            return_number,
            data.get('return_date', datetime.now().strftime('%Y-%m-%d')),
            data.get('claim_id'),
            data.get('po_id'),
            data.get('supplier_id'),
            data.get('supplier_name'),
            data.get('item_id'),
            data.get('item_name'),
            data.get('part_number'),
            data.get('return_qty', 0),
            data.get('return_reason'),
            data.get('return_type', 'RETURN'),
            'PENDING',
            data.get('notes'),
            user_id
        ))
        db.commit()

        log_procurement_audit('RETURN', cursor.lastrowid, return_number, 'CREATE', user_id=user_id)

        return cursor.lastrowid


# =============================================================================
# CONTRACTS
# =============================================================================

def get_contracts(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get paginated list of contracts."""
    where_clauses = ["1=1"]
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(pc.contract_number LIKE ? OR pc.contract_name LIKE ? OR pc.supplier_name LIKE ?)")
            search = f"%{filters['search']}%"
            params.extend([search, search, search])

        if filters.get('status'):
            where_clauses.append("pc.status = ?")
            params.append(filters['status'])

        if filters.get('contract_type'):
            where_clauses.append("pc.contract_type = ?")
            params.append(filters['contract_type'])

        if filters.get('supplier_id'):
            where_clauses.append("pc.supplier_id = ?")
            params.append(filters['supplier_id'])

        if filters.get('expiring_within_days'):
            where_clauses.append("pc.end_date <= ? AND pc.end_date >= ? AND pc.status = 'ACTIVE'")
            future_date = (datetime.now() + timedelta(days=filters['expiring_within_days'])).strftime('%Y-%m-%d')
            params.extend([future_date, datetime.now().strftime('%Y-%m-%d')])

    where_sql = " AND ".join(where_clauses)

    count_sql = f"SELECT COUNT(*) as cnt FROM procurement_contracts pc WHERE {where_sql}"
    total = get_one(count_sql, params)['cnt']

    offset = (page - 1) * per_page
    sql = f"""
        SELECT pc.*, s.supplier_type, s.country as supplier_country,
               (SELECT COUNT(*) FROM procurement_contract_lines WHERE contract_id = pc.id) as line_count
        FROM procurement_contracts pc
        LEFT JOIN suppliers s ON pc.supplier_id = s.id
        WHERE {where_sql}
        ORDER BY pc.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        items = [dict(row) for row in rows]

    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page if total > 0 else 1
    }


def create_contract(data: Dict, lines: List[Dict] = None, user_id: int = None) -> int:
    """Create a new contract with optional price lines."""
    contract_number = get_next_sequence_number('CON', 'procurement_contracts', 'start_date')

    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO procurement_contracts (
                contract_number, contract_name, supplier_id, supplier_name,
                contract_type, start_date, end_date, status, total_value, currency,
                payment_terms, incoterm, moq, lead_time_commitment, sla_terms,
                rebate_percent, special_conditions, auto_renewal, renewal_notice_days,
                covered_brands, covered_item_groups, owner_id, owner_name,
                notes, attachments, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            contract_number,
            data.get('contract_name'),
            data.get('supplier_id'),
            data.get('supplier_name'),
            data.get('contract_type', 'STANDARD'),
            data.get('start_date'),
            data.get('end_date'),
            'ACTIVE',
            data.get('total_value', 0),
            data.get('currency', 'AED'),
            data.get('payment_terms'),
            data.get('incoterm'),
            data.get('moq', 1),
            data.get('lead_time_commitment'),
            data.get('sla_terms'),
            data.get('rebate_percent', 0),
            data.get('special_conditions'),
            data.get('auto_renewal', 0),
            data.get('renewal_notice_days', 30),
            data.get('covered_brands'),
            data.get('covered_item_groups'),
            data.get('owner_id'),
            data.get('owner_name'),
            data.get('notes'),
            data.get('attachments'),
            user_id
        ))
        db.commit()
        contract_id = cursor.lastrowid

        # Insert price lines if provided
        if lines:
            for line in lines:
                db.execute("""
                    INSERT INTO procurement_contract_lines (
                        contract_id, item_id, item_code, item_name, brand,
                        part_number, negotiated_price, unit_of_measure,
                        min_qty, max_qty, valid_from, valid_to, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    contract_id, line.get('item_id'), line.get('item_code'),
                    line.get('item_name'), line.get('brand'), line.get('part_number'),
                    line.get('negotiated_price', 0), line.get('unit_of_measure', 'PCS'),
                    line.get('min_qty', 1), line.get('max_qty'),
                    line.get('valid_from'), line.get('valid_to'), line.get('notes')
                ))

        db.commit()

        log_procurement_audit('CONTRACT', contract_id, contract_number, 'CREATE', user_id=user_id)

        return contract_id


# =============================================================================
# DASHBOARD & ANALYTICS
# =============================================================================

def get_procurement_dashboard_stats(user_id: int = None) -> Dict:
    """Get dashboard statistics for procurement module."""
    today = datetime.now().date()
    week_start = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
    month_start = today.replace(day=1).strftime('%Y-%m-%d')
    year_start = today.replace(month=1, day=1).strftime('%Y-%m-%d')

    stats = {}

    with get_db_context() as db:
        # Requisition stats
        stats['open_requisitions'] = db.execute("""
            SELECT COUNT(*) as cnt FROM procurement_requisitions
            WHERE status IN ('SUBMITTED', 'PENDING_APPROVAL', 'APPROVED')
        """).fetchone()['cnt']

        stats['pending_approval_requisitions'] = db.execute("""
            SELECT COUNT(*) as cnt FROM procurement_requisitions
            WHERE status = 'PENDING_APPROVAL'
        """).fetchone()['cnt']

        # RFQ stats
        stats['rfqs_in_progress'] = db.execute("""
            SELECT COUNT(*) as cnt FROM procurement_rfqs
            WHERE status IN ('DRAFT', 'SENT', 'AWAITING_RESPONSE', 'PARTIALLY_RECEIVED')
        """).fetchone()['cnt']

        stats['quotations_pending_comparison'] = db.execute("""
            SELECT COUNT(*) as cnt FROM procurement_quotations
            WHERE status = 'SUBMITTED' AND is_winner = 0
        """).fetchone()['cnt']

        # PO stats
        stats['open_pos'] = db.execute("""
            SELECT COUNT(*) as cnt FROM procurement_purchase_orders
            WHERE status NOT IN ('RECEIVED', 'CLOSED', 'CANCELLED')
        """).fetchone()['cnt']

        stats['pending_approval_pos'] = db.execute("""
            SELECT COUNT(*) as cnt FROM procurement_purchase_orders
            WHERE approval_status = 'PENDING'
        """).fetchone()['cnt']

        stats['delayed_pos'] = db.execute("""
            SELECT COUNT(*) as cnt FROM procurement_purchase_orders
            WHERE expected_delivery_date < ? AND status NOT IN ('RECEIVED', 'CLOSED', 'CANCELLED')
        """, (today.strftime('%Y-%m-%d'),)).fetchone()['cnt']

        stats['expected_receipts_this_week'] = db.execute("""
            SELECT COUNT(*) as cnt FROM procurement_expected_receipts
            WHERE expected_date >= ? AND expected_date <= ? AND status = 'PENDING'
        """, (today.strftime('%Y-%m-%d'), (today + timedelta(days=7)).strftime('%Y-%m-%d'))).fetchone()['cnt']

        stats['overdue_receipts'] = db.execute("""
            SELECT COUNT(*) as cnt FROM procurement_expected_receipts
            WHERE expected_date < ? AND status = 'PENDING'
        """, (today.strftime('%Y-%m-%d'),)).fetchone()['cnt']

        # Claim stats
        stats['open_claims'] = db.execute("""
            SELECT COUNT(*) as cnt FROM procurement_claims
            WHERE status NOT IN ('CLOSED', 'RESOLVED')
        """).fetchone()['cnt']

        stats['open_returns'] = db.execute("""
            SELECT COUNT(*) as cnt FROM procurement_returns
            WHERE return_status NOT IN ('COMPLETED', 'CANCELLED')
        """).fetchone()['cnt']

        # Contract stats
        stats['active_contracts'] = db.execute("""
            SELECT COUNT(*) as cnt FROM procurement_contracts
            WHERE status = 'ACTIVE'
        """).fetchone()['cnt']

        stats['expiring_contracts_30_days'] = db.execute("""
            SELECT COUNT(*) as cnt FROM procurement_contracts
            WHERE status = 'ACTIVE' AND end_date <= ? AND end_date >= ?
        """, ((today + timedelta(days=30)).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))).fetchone()['cnt']

        # Spend analytics
        stats['spend_today'] = db.execute("""
            SELECT COALESCE(SUM(total_amount), 0) as total FROM procurement_purchase_orders
            WHERE po_date = ?
        """, (today.strftime('%Y-%m-%d'),)).fetchone()['total']

        stats['spend_this_month'] = db.execute("""
            SELECT COALESCE(SUM(total_amount), 0) as total FROM procurement_purchase_orders
            WHERE po_date >= ?
        """, (month_start,)).fetchone()['total']

        stats['spend_this_year'] = db.execute("""
            SELECT COALESCE(SUM(total_amount), 0) as total FROM procurement_purchase_orders
            WHERE po_date >= ?
        """, (year_start,)).fetchone()['total']

        # Supplier stats
        stats['total_suppliers'] = db.execute("""
            SELECT COUNT(*) as cnt FROM suppliers WHERE status = 'Active'
        """).fetchone()['cnt']

        stats['preferred_suppliers'] = db.execute("""
            SELECT COUNT(*) as cnt FROM suppliers WHERE is_preferred = 1 AND status = 'Active'
        """).fetchone()['cnt']

        stats['blacklisted_suppliers'] = db.execute("""
            SELECT COUNT(*) as cnt FROM suppliers WHERE is_blacklisted = 1
        """).fetchone()['cnt']

        # Urgent/Emergency
        stats['urgent_requisitions'] = db.execute("""
            SELECT COUNT(*) as cnt FROM procurement_requisitions
            WHERE urgency = 'URGENT' AND status NOT IN ('CLOSED', 'CANCELLED')
        """).fetchone()['cnt']

        stats['emergency_pos'] = db.execute("""
            SELECT COUNT(*) as cnt FROM procurement_purchase_orders
            WHERE po_type = 'EMERGENCY' AND status NOT IN ('RECEIVED', 'CLOSED', 'CANCELLED')
        """).fetchone()['cnt']

    return stats


def get_supplier_performance_summary(supplier_id: int = None) -> List[Dict]:
    """Get supplier performance metrics."""
    sql = """
        SELECT
            s.id, s.name, s.code, s.supplier_type, s.country,
            s.rating, s.performance_score, s.spend_ytd,
            COALESCE(pom.on_time_delivery_rate, 0) as on_time_rate,
            COALESCE(pom.avg_lead_time_days, 0) as avg_lead_time,
            COALESCE(pom.fill_rate, 0) as fill_rate,
            COALESCE(pom.quality_acceptance_rate, 0) as quality_rate,
            COALESCE(pom.claim_rate, 0) as claim_rate,
            COUNT(DISTINCT po.id) as total_pos,
            SUM(po.total_amount) as total_spend
        FROM suppliers s
        LEFT JOIN procurement_supplier_metrics pom ON s.id = pom.supplier_id
        LEFT JOIN procurement_purchase_orders po ON s.id = po.supplier_id
        WHERE s.status = 'Active'
    """

    params = []
    if supplier_id:
        sql += " AND s.id = ?"
        params.append(supplier_id)

    sql += """
        GROUP BY s.id
        ORDER BY s.name
    """

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        return [dict(row) for row in rows]


# =============================================================================
# ALERTS
# =============================================================================

def create_procurement_alert(alert_type: str, title: str, message: str,
                              entity_type: str = None, entity_id: int = None,
                              supplier_id: int = None, priority: str = 'MEDIUM',
                              severity: str = 'MEDIUM', user_id: int = None) -> int:
    """Create a procurement alert."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO procurement_alerts (
                alert_type, title, message, priority, severity,
                entity_type, entity_id, supplier_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (alert_type, title, message, priority, severity,
              entity_type, entity_id, supplier_id, user_id))
        db.commit()
        return cursor.lastrowid


def get_procurement_alerts(filters: Dict = None, user_id: int = None) -> List[Dict]:
    """Get procurement alerts."""
    where_clauses = ["1=1"]
    params = []

    if filters:
        if filters.get('is_read') is not None:
            where_clauses.append("pa.is_read = ?")
            params.append(1 if filters['is_read'] else 0)

        if filters.get('is_resolved') is not None:
            where_clauses.append("pa.is_resolved = ?")
            params.append(1 if filters['is_resolved'] else 0)

        if filters.get('alert_type'):
            where_clauses.append("pa.alert_type = ?")
            params.append(filters['alert_type'])

        if filters.get('priority'):
            where_clauses.append("pa.priority = ?")
            params.append(filters['priority'])

        if filters.get('supplier_id'):
            where_clauses.append("pa.supplier_id = ?")
            params.append(filters['supplier_id'])

    where_sql = " AND ".join(where_clauses)

    sql = f"""
        SELECT pa.*, s.name as supplier_name
        FROM procurement_alerts pa
        LEFT JOIN suppliers s ON pa.supplier_id = s.id
        WHERE {where_sql}
        ORDER BY pa.created_at DESC
        LIMIT 100
    """

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        return [dict(row) for row in rows]


# =============================================================================
# SETTINGS
# =============================================================================

def get_procurement_setting(key: str, default: str = None) -> Optional[str]:
    """Get a procurement setting value."""
    result = get_one(
        "SELECT setting_value FROM procurement_settings WHERE setting_key = ? AND is_active = 1",
        (key,)
    )
    return result['setting_value'] if result else default


def set_procurement_setting(key: str, value: str, category: str = 'GENERAL',
                             description: str = None) -> bool:
    """Set a procurement setting value."""
    with get_db_context() as db:
        existing = db.execute(
            "SELECT id FROM procurement_settings WHERE setting_key = ?", (key,)
        ).fetchone()

        if existing:
            db.execute("""
                UPDATE procurement_settings
                SET setting_value = ?, category = ?, description = ?, updated_at = datetime('now')
                WHERE setting_key = ?
            """, (value, category, description, key))
        else:
            db.execute("""
                INSERT INTO procurement_settings (setting_key, setting_value, category, description)
                VALUES (?, ?, ?, ?)
            """, (key, value, category, description))
        db.commit()
    return True


def get_all_procurement_settings(category: str = None) -> Dict:
    """Get all procurement settings grouped by category."""
    sql = "SELECT * FROM procurement_settings WHERE is_active = 1"
    params = []

    if category:
        sql += " AND category = ?"
        params.append(category)

    sql += " ORDER BY category, setting_key"

    rows = get_all(sql, params)

    # Group by category
    grouped = {}
    for row in rows:
        cat = row['category']
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(row)

    return grouped
