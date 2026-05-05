"""
WMS Schema - Database table definitions and initialization for Warehouse Management System.
This module contains all WMS table CREATE statements extracted from wms_routes.py.
Use initialize_wms_schema(get_db_func) to create all tables and seed default data.
"""

_wms_schema_initialized = False


def initialize_wms_schema(get_db_func):
    """
    Initialize all WMS database tables and seed default data.
    """
    global _wms_schema_initialized
    if _wms_schema_initialized:
        return

    db = get_db_func()

    # Create all WMS tables
    table_defs = [
        ('wms_settings', '''
            CREATE TABLE IF NOT EXISTS wms_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT, setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT, setting_type TEXT DEFAULT 'string',
                category TEXT DEFAULT 'general', description TEXT,
                is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_companies', '''
            CREATE TABLE IF NOT EXISTS wms_companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER NOT NULL,
                code TEXT UNIQUE NOT NULL, name TEXT NOT NULL, name_local TEXT,
                country TEXT, currency TEXT DEFAULT 'USD', language TEXT DEFAULT 'en',
                timezone TEXT DEFAULT 'UTC', address TEXT, phone TEXT, email TEXT,
                tax_id TEXT, is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id))'''),

        ('wms_warehouses', '''
            CREATE TABLE IF NOT EXISTS wms_warehouses (
                id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER NOT NULL,
                code TEXT UNIQUE NOT NULL, name TEXT NOT NULL, name_local TEXT,
                type TEXT DEFAULT 'main', address TEXT, city TEXT, country TEXT,
                phone TEXT, email TEXT, manager_id INTEGER, is_active INTEGER DEFAULT 1,
                allow_receiving INTEGER DEFAULT 1, allow_shipping INTEGER DEFAULT 1,
                allow_storage INTEGER DEFAULT 1, default_rotation_policy TEXT DEFAULT 'FIFO',
                min_temp REAL, max_temp REAL, notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES wms_companies(id))'''),

        ('wms_zones', '''
            CREATE TABLE IF NOT EXISTS wms_zones (
                id INTEGER PRIMARY KEY AUTOINCREMENT, warehouse_id INTEGER NOT NULL,
                code TEXT NOT NULL, name TEXT NOT NULL, zone_type TEXT NOT NULL,
                description TEXT, picking_enabled INTEGER DEFAULT 1,
                putaway_enabled INTEGER DEFAULT 1, replenishment_enabled INTEGER DEFAULT 1,
                is_active INTEGER DEFAULT 1, sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                UNIQUE(warehouse_id, code))'''),

        ('wms_locations', '''
            CREATE TABLE IF NOT EXISTS wms_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT, warehouse_id INTEGER NOT NULL,
                zone_id INTEGER, parent_location_id INTEGER, code TEXT NOT NULL,
                barcode TEXT, name TEXT, location_type TEXT NOT NULL, level INTEGER DEFAULT 0,
                coordinates_rack TEXT, coordinates_bay TEXT, coordinates_level TEXT,
                coordinates_position TEXT, coordinates_bin TEXT,
                capacity_pallets INTEGER, capacity_weight_kg REAL, capacity_volume_m3 REAL,
                capacity_cartons INTEGER, current_pallets INTEGER DEFAULT 0,
                current_weight_kg REAL DEFAULT 0, current_volume_m3 REAL DEFAULT 0,
                current_cartons INTEGER DEFAULT 0, picking_enabled INTEGER DEFAULT 1,
                putaway_enabled INTEGER DEFAULT 1, replenishment_enabled INTEGER DEFAULT 1,
                is_locked INTEGER DEFAULT 0, lock_reason TEXT, is_active INTEGER DEFAULT 1,
                is_empty INTEGER DEFAULT 1, temperature_min REAL, temperature_max REAL,
                humidity_min REAL, humidity_max REAL, preferred_item_class TEXT,
                cycle_count_class TEXT, last_count_date TEXT, last_count_by INTEGER,
                notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (zone_id) REFERENCES wms_zones(id),
                FOREIGN KEY (parent_location_id) REFERENCES wms_locations(id),
                UNIQUE(warehouse_id, code))'''),

        ('wms_item_categories', '''
            CREATE TABLE IF NOT EXISTS wms_item_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT, parent_id INTEGER,
                code TEXT UNIQUE NOT NULL, name TEXT NOT NULL, name_local TEXT,
                description TEXT, level INTEGER DEFAULT 0, path TEXT,
                is_active INTEGER DEFAULT 1, sort_order INTEGER DEFAULT 0, metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES wms_item_categories(id))'''),

        ('wms_item_brands', '''
            CREATE TABLE IF NOT EXISTS wms_item_brands (
                id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL, name_local TEXT, manufacturer TEXT, country TEXT,
                website TEXT, logo_url TEXT, description TEXT, is_active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_item_groups', '''
            CREATE TABLE IF NOT EXISTS wms_item_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL, name_local TEXT, description TEXT,
                is_active INTEGER DEFAULT 1, sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_items', '''
            CREATE TABLE IF NOT EXISTS wms_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT, item_code TEXT UNIQUE NOT NULL,
                sku TEXT, barcode TEXT, qr_code TEXT, part_number TEXT, oem_number TEXT,
                alternate_part_numbers TEXT, supplier_code TEXT, name TEXT NOT NULL,
                name_local TEXT, short_name TEXT, long_description TEXT, brand_id INTEGER,
                category_id INTEGER, group_id INTEGER, item_type TEXT DEFAULT 'finished_goods',
                unit_of_measure TEXT DEFAULT 'PCS', secondary_uom TEXT,
                conversion_rate REAL DEFAULT 1.0, weight_kg REAL, volume_m3 REAL,
                length_cm REAL, width_cm REAL, height_cm REAL, color TEXT, size TEXT,
                material TEXT, country_of_origin TEXT, hazard_class TEXT,
                temperature_requirement TEXT, shelf_life_days INTEGER,
                expiry_tracking INTEGER DEFAULT 0, batch_tracking INTEGER DEFAULT 0,
                lot_tracking INTEGER DEFAULT 0, serial_tracking INTEGER DEFAULT 0,
                quality_inspection_required INTEGER DEFAULT 0,
                min_stock_level REAL DEFAULT 0, max_stock_level REAL,
                reorder_point REAL DEFAULT 0, reorder_quantity REAL,
                safety_stock REAL DEFAULT 0, economic_order_quantity REAL,
                preferred_warehouse_id INTEGER, preferred_location_id INTEGER,
                rotation_policy TEXT DEFAULT 'FIFO', picking_strategy TEXT,
                packing_instruction TEXT, handling_instruction TEXT,
                selling_status TEXT DEFAULT 'active',
                procurement_status TEXT DEFAULT 'active', abc_class TEXT, image_url TEXT,
                is_active INTEGER DEFAULT 1, is_kit INTEGER DEFAULT 0,
                is_bundle INTEGER DEFAULT 0, kit_components TEXT, metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP, created_by INTEGER)'''),

        ('wms_item_suppliers', '''
            CREATE TABLE IF NOT EXISTS wms_item_suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL,
                supplier_id INTEGER NOT NULL, supplier_code TEXT,
                supplier_part_number TEXT, lead_time_days INTEGER, moq REAL DEFAULT 1,
                unit_cost REAL, currency TEXT DEFAULT 'USD',
                is_preferred INTEGER DEFAULT 0, is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_item_relations', '''
            CREATE TABLE IF NOT EXISTS wms_item_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL,
                related_item_id INTEGER NOT NULL, relation_type TEXT NOT NULL,
                is_bidirectional INTEGER DEFAULT 0, is_approved INTEGER DEFAULT 1,
                priority INTEGER DEFAULT 0, notes TEXT, valid_from TEXT, valid_to TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_lots', '''
            CREATE TABLE IF NOT EXISTS wms_lots (
                id INTEGER PRIMARY KEY AUTOINCREMENT, lot_number TEXT UNIQUE NOT NULL,
                item_id INTEGER NOT NULL, warehouse_id INTEGER NOT NULL,
                location_id INTEGER, quantity REAL DEFAULT 0,
                reserved_quantity REAL DEFAULT 0, blocked_quantity REAL DEFAULT 0,
                manufacturing_date TEXT, expiry_date TEXT, received_date TEXT,
                supplier_batch_number TEXT, production_line TEXT, status TEXT DEFAULT 'ACTIVE',
                notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_serial_numbers', '''
            CREATE TABLE IF NOT EXISTS wms_serial_numbers (
                id INTEGER PRIMARY KEY AUTOINCREMENT, serial_number TEXT UNIQUE NOT NULL,
                item_id INTEGER NOT NULL, lot_id INTEGER, warehouse_id INTEGER NOT NULL,
                location_id INTEGER, status TEXT DEFAULT 'AVAILABLE', assigned_to TEXT,
                assigned_date TEXT, warranty_expiry_date TEXT, notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_inventory_balances', '''
            CREATE TABLE IF NOT EXISTS wms_inventory_balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL,
                lot_id INTEGER, serial_number_id INTEGER, warehouse_id INTEGER NOT NULL,
                location_id INTEGER, company_id INTEGER, quantity REAL DEFAULT 0,
                reserved_quantity REAL DEFAULT 0, allocated_quantity REAL DEFAULT 0,
                blocked_quantity REAL DEFAULT 0, status TEXT DEFAULT 'AVAILABLE',
                last_movement_date TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(item_id, lot_id, serial_number_id, warehouse_id, location_id, company_id, status))'''),

        ('wms_inventory_ledger', '''
            CREATE TABLE IF NOT EXISTS wms_inventory_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT, transaction_type TEXT NOT NULL,
                transaction_number TEXT, reference_type TEXT, reference_number TEXT,
                item_id INTEGER NOT NULL, lot_id INTEGER, serial_number_id INTEGER,
                warehouse_id INTEGER NOT NULL, location_id INTEGER, company_id INTEGER,
                quantity_before REAL, quantity_moved REAL, quantity_after REAL,
                status_before TEXT, status_after TEXT, reason_code TEXT, notes TEXT,
                user_id INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_inbound_receipts', '''
            CREATE TABLE IF NOT EXISTS wms_inbound_receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT, receipt_number TEXT UNIQUE NOT NULL,
                receipt_type TEXT NOT NULL, warehouse_id INTEGER NOT NULL, company_id INTEGER,
                supplier_id INTEGER, po_reference TEXT, asn_reference TEXT,
                expected_date TEXT, actual_arrival_date TEXT, received_by INTEGER,
                quality_status TEXT DEFAULT 'PENDING', status TEXT DEFAULT 'EXPECTED',
                notes TEXT, attachments TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP, created_by INTEGER)'''),

        ('wms_inbound_receipt_lines', '''
            CREATE TABLE IF NOT EXISTS wms_inbound_receipt_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT, receipt_id INTEGER NOT NULL,
                line_number INTEGER, item_id INTEGER NOT NULL,
                expected_quantity REAL, received_quantity REAL DEFAULT 0,
                accepted_quantity REAL DEFAULT 0, rejected_quantity REAL DEFAULT 0,
                damaged_quantity REAL DEFAULT 0, short_quantity REAL DEFAULT 0,
                over_quantity REAL DEFAULT 0, lot_number TEXT, expiry_date TEXT,
                serial_numbers TEXT, location_id INTEGER, unit_cost REAL,
                currency TEXT DEFAULT 'USD', quality_status TEXT DEFAULT 'PENDING',
                status TEXT DEFAULT 'PENDING', notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_asn', '''
            CREATE TABLE IF NOT EXISTS wms_asn (
                id INTEGER PRIMARY KEY AUTOINCREMENT, asn_number TEXT UNIQUE NOT NULL,
                partner_id INTEGER, warehouse_id INTEGER, expected_date TEXT,
                actual_date TEXT, status TEXT DEFAULT 'EXPECTED', po_number TEXT,
                notes TEXT, created_by INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_asn_lines', '''
            CREATE TABLE IF NOT EXISTS wms_asn_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT, asn_id INTEGER NOT NULL,
                line_number INTEGER, item_id INTEGER NOT NULL,
                expected_quantity REAL NOT NULL, received_quantity REAL DEFAULT 0,
                unit_cost REAL, lot_number TEXT, expiry_date TEXT,
                status TEXT DEFAULT 'PENDING', notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_cross_dock', '''
            CREATE TABLE IF NOT EXISTS wms_cross_dock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cross_dock_number TEXT UNIQUE NOT NULL, receipt_id INTEGER,
                warehouse_id INTEGER, dock_door_id INTEGER,
                status TEXT DEFAULT 'PENDING', priority INTEGER DEFAULT 5,
                scheduled_arrival TEXT, actual_arrival TEXT,
                scheduled_departure TEXT, actual_departure TEXT, notes TEXT,
                created_by INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_putaway_tasks', '''
            CREATE TABLE IF NOT EXISTS wms_putaway_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT, task_number TEXT UNIQUE NOT NULL,
                receipt_line_id INTEGER, item_id INTEGER NOT NULL, lot_id INTEGER,
                source_location_id INTEGER, destination_location_id INTEGER,
                suggested_location_id INTEGER, quantity REAL NOT NULL,
                priority INTEGER DEFAULT 5, status TEXT DEFAULT 'PENDING',
                assigned_to INTEGER, started_at TEXT, completed_at TEXT,
                completed_by INTEGER, notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP, created_by INTEGER)'''),

        ('wms_putaway_rules', '''
            CREATE TABLE IF NOT EXISTS wms_putaway_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT, rule_name TEXT NOT NULL,
                rule_type TEXT NOT NULL, description TEXT, priority INTEGER DEFAULT 5,
                is_active INTEGER DEFAULT 1, conditions_json TEXT,
                action_type TEXT NOT NULL, target_zone_id INTEGER,
                target_location_type TEXT, target_warehouse_id INTEGER,
                min_capacity_weight REAL, max_capacity_weight REAL,
                min_capacity_volume REAL, max_capacity_volume REAL,
                velocity_class TEXT, hazmat_class TEXT,
                temperature_required INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP, created_by INTEGER)'''),

        ('wms_putaway_rule_log', '''
            CREATE TABLE IF NOT EXISTS wms_putaway_rule_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT, rule_id INTEGER,
                receipt_line_id INTEGER, item_id INTEGER, suggested_location_id INTEGER,
                actual_location_id INTEGER, is_accepted INTEGER DEFAULT 0,
                is_overridden INTEGER DEFAULT 0, override_reason TEXT,
                decision_time_ms INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_internal_movements', '''
            CREATE TABLE IF NOT EXISTS wms_internal_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movement_number TEXT UNIQUE NOT NULL, movement_type TEXT NOT NULL,
                item_id INTEGER NOT NULL, lot_id INTEGER, serial_number_id INTEGER,
                source_location_id INTEGER, destination_location_id INTEGER,
                quantity REAL NOT NULL, reason_code TEXT,
                status TEXT DEFAULT 'COMPLETED', reference_type TEXT,
                reference_number TEXT, notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, created_by INTEGER)'''),

        ('wms_replenishment_tasks', '''
            CREATE TABLE IF NOT EXISTS wms_replenishment_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_number TEXT UNIQUE NOT NULL, item_id INTEGER NOT NULL,
                lot_id INTEGER, source_location_id INTEGER,
                destination_location_id INTEGER, quantity REAL NOT NULL,
                priority INTEGER DEFAULT 5, replenishment_type TEXT DEFAULT 'PICKING_AREA',
                status TEXT DEFAULT 'PENDING', assigned_to INTEGER,
                started_at TEXT, completed_at TEXT, completed_by INTEGER,
                notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP, created_by INTEGER)'''),

        ('wms_replenishment_config', '''
            CREATE TABLE IF NOT EXISTS wms_replenishment_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL, min_quantity REAL DEFAULT 0,
                max_quantity REAL DEFAULT 0, reorder_point REAL DEFAULT 0,
                reorder_quantity REAL DEFAULT 0, safety_stock REAL DEFAULT 0,
                lead_time_days INTEGER DEFAULT 7, abc_class TEXT,
                velocity_class TEXT, replenishment_method TEXT DEFAULT 'MIN_MAX',
                is_active INTEGER DEFAULT 1, last_calculated_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_demand_forecast', '''
            CREATE TABLE IF NOT EXISTS wms_demand_forecast (
                id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL,
                forecast_date DATE NOT NULL, predicted_quantity REAL NOT NULL,
                confidence_level REAL DEFAULT 0.95,
                forecast_method TEXT DEFAULT 'MOVING_AVG', actual_quantity REAL,
                variance REAL, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(item_id, forecast_date))'''),

        ('wms_kanban_config', '''
            CREATE TABLE IF NOT EXISTS wms_kanban_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL,
                source_location_id INTEGER NOT NULL,
                destination_location_id INTEGER NOT NULL, kanban_size INTEGER DEFAULT 1,
                current_cards INTEGER DEFAULT 0, max_cards INTEGER DEFAULT 5,
                signal_point INTEGER DEFAULT 2, is_active INTEGER DEFAULT 1,
                last_refill_at TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_replenishment_suggestions', '''
            CREATE TABLE IF NOT EXISTS wms_replenishment_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL, suggested_quantity REAL NOT NULL,
                reason_code TEXT, urgency TEXT DEFAULT 'NORMAL',
                status TEXT DEFAULT 'PENDING', reviewed_by INTEGER,
                reviewed_at TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_outbound_orders', '''
            CREATE TABLE IF NOT EXISTS wms_outbound_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE NOT NULL, order_type TEXT NOT NULL,
                warehouse_id INTEGER NOT NULL, company_id INTEGER, customer_id INTEGER,
                so_reference TEXT, order_date TEXT, required_date TEXT,
                shipped_date TEXT, status TEXT DEFAULT 'DRAFT',
                priority INTEGER DEFAULT 5, picking_strategy TEXT, notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP, created_by INTEGER)'''),

        ('wms_outbound_order_lines', '''
            CREATE TABLE IF NOT EXISTS wms_outbound_order_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL,
                line_number INTEGER, item_id INTEGER NOT NULL,
                ordered_quantity REAL, allocated_quantity REAL DEFAULT 0,
                picked_quantity REAL DEFAULT 0, packed_quantity REAL DEFAULT 0,
                shipped_quantity REAL DEFAULT 0, reserved_lot_id INTEGER,
                reserved_serial_numbers TEXT, status TEXT DEFAULT 'PENDING',
                notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_pick_tasks', '''
            CREATE TABLE IF NOT EXISTS wms_pick_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT, task_number TEXT UNIQUE NOT NULL,
                order_line_id INTEGER, order_id INTEGER, item_id INTEGER NOT NULL,
                lot_id INTEGER, serial_number_id INTEGER,
                source_location_id INTEGER NOT NULL, quantity REAL NOT NULL,
                picked_quantity REAL DEFAULT 0, priority INTEGER DEFAULT 5,
                pick_sequence INTEGER, status TEXT DEFAULT 'PENDING',
                assigned_to INTEGER, started_at TEXT, completed_at TEXT,
                completed_by INTEGER, short_pick_reason TEXT, notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP, created_by INTEGER)'''),

        ('wms_pack_tasks', '''
            CREATE TABLE IF NOT EXISTS wms_pack_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT, task_number TEXT UNIQUE NOT NULL,
                order_id INTEGER NOT NULL, pack_station TEXT,
                carton_count INTEGER DEFAULT 1, packed_weight_kg REAL,
                packed_dimensions_l REAL, packed_dimensions_w REAL,
                packed_dimensions_h REAL, packing_material TEXT,
                status TEXT DEFAULT 'PENDING', assigned_to INTEGER,
                started_at TEXT, completed_at TEXT, completed_by INTEGER,
                notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP, created_by INTEGER)'''),

        ('wms_shipments', '''
            CREATE TABLE IF NOT EXISTS wms_shipments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shipment_number TEXT UNIQUE NOT NULL, order_id INTEGER,
                warehouse_id INTEGER NOT NULL, company_id INTEGER, carrier_id INTEGER,
                carrier_name TEXT, tracking_number TEXT, vehicle_id INTEGER,
                driver_name TEXT, departure_date TEXT, arrival_date TEXT,
                status TEXT DEFAULT 'PREPARING', notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP, created_by INTEGER)'''),

        ('wms_transfers', '''
            CREATE TABLE IF NOT EXISTS wms_transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transfer_number TEXT UNIQUE NOT NULL, transfer_type TEXT NOT NULL,
                source_warehouse_id INTEGER NOT NULL,
                destination_warehouse_id INTEGER NOT NULL, source_company_id INTEGER,
                destination_company_id INTEGER, status TEXT DEFAULT 'DRAFT',
                priority INTEGER DEFAULT 5, requested_by INTEGER, approved_by INTEGER,
                picked_by INTEGER, shipped_by INTEGER, received_by INTEGER,
                shipped_date TEXT, received_date TEXT, notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP, created_by INTEGER)'''),

        ('wms_transfer_lines', '''
            CREATE TABLE IF NOT EXISTS wms_transfer_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT, transfer_id INTEGER NOT NULL,
                line_number INTEGER, item_id INTEGER NOT NULL,
                requested_quantity REAL, picked_quantity REAL DEFAULT 0,
                shipped_quantity REAL DEFAULT 0, received_quantity REAL DEFAULT 0,
                discrepancy_quantity REAL DEFAULT 0, lot_id INTEGER,
                source_location_id INTEGER, destination_location_id INTEGER,
                status TEXT DEFAULT 'PENDING', notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_returns', '''
            CREATE TABLE IF NOT EXISTS wms_returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_number TEXT UNIQUE NOT NULL, return_type TEXT NOT NULL,
                warehouse_id INTEGER NOT NULL, company_id INTEGER, customer_id INTEGER,
                supplier_id INTEGER, original_order_number TEXT, rma_number TEXT,
                reason_code TEXT, status TEXT DEFAULT 'REQUESTED',
                authorization_status TEXT DEFAULT 'PENDING', inspected_by INTEGER,
                inspected_date TEXT, disposition TEXT, notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP, created_by INTEGER)'''),

        ('wms_return_lines', '''
            CREATE TABLE IF NOT EXISTS wms_return_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT, return_id INTEGER NOT NULL,
                line_number INTEGER, item_id INTEGER NOT NULL,
                original_order_line_id INTEGER, quantity_returned REAL,
                quantity_received REAL DEFAULT 0, quantity_accepted REAL DEFAULT 0,
                quantity_rejected REAL DEFAULT 0, quantity_damaged REAL DEFAULT 0,
                lot_id INTEGER, serial_number_id INTEGER, condition_grade TEXT,
                restock_decision TEXT, restock_location_id INTEGER,
                inspection_status TEXT DEFAULT 'PENDING', notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_stock_counts', '''
            CREATE TABLE IF NOT EXISTS wms_stock_counts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                count_number TEXT UNIQUE NOT NULL, count_type TEXT NOT NULL,
                warehouse_id INTEGER NOT NULL, company_id INTEGER, location_id INTEGER,
                category_id INTEGER, status TEXT DEFAULT 'DRAFT',
                count_method TEXT DEFAULT 'MANUAL', is_blind_count INTEGER DEFAULT 0,
                scheduled_date TEXT, started_date TEXT, completed_date TEXT,
                approved_by INTEGER, approved_date TEXT, total_lines INTEGER DEFAULT 0,
                counted_lines INTEGER DEFAULT 0, variance_lines INTEGER DEFAULT 0,
                freeze_stock INTEGER DEFAULT 0, notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP, created_by INTEGER)'''),

        ('wms_stock_count_lines', '''
            CREATE TABLE IF NOT EXISTS wms_stock_count_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT, count_id INTEGER NOT NULL,
                line_number INTEGER, item_id INTEGER NOT NULL, location_id INTEGER,
                lot_id INTEGER, serial_number_id INTEGER, system_quantity REAL,
                counted_quantity REAL, variance_quantity REAL, variance_value REAL,
                status TEXT DEFAULT 'PENDING', reason_code TEXT,
                investigation_notes TEXT, counted_by INTEGER, counted_at TEXT,
                verified_by INTEGER, verified_at TEXT, approved_by INTEGER,
                approved_at TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_stock_adjustments', '''
            CREATE TABLE IF NOT EXISTS wms_stock_adjustments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                adjustment_number TEXT UNIQUE NOT NULL,
                warehouse_id INTEGER NOT NULL, company_id INTEGER,
                adjustment_type TEXT NOT NULL, reason_code TEXT NOT NULL,
                status TEXT DEFAULT 'DRAFT', approved_by INTEGER,
                approved_date TEXT, applied_by INTEGER, applied_date TEXT,
                total_lines INTEGER DEFAULT 0, total_variance_value REAL DEFAULT 0,
                notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP, created_by INTEGER)'''),

        ('wms_stock_adjustment_lines', '''
            CREATE TABLE IF NOT EXISTS wms_stock_adjustment_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                adjustment_id INTEGER NOT NULL, line_number INTEGER,
                item_id INTEGER NOT NULL, location_id INTEGER, lot_id INTEGER,
                serial_number_id INTEGER, system_quantity REAL, counted_quantity REAL,
                adjusted_quantity REAL, unit_cost REAL, variance_value REAL,
                reason_code TEXT, notes TEXT, status TEXT DEFAULT 'PENDING',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_wave_templates', '''
            CREATE TABLE IF NOT EXISTS wms_wave_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT UNIQUE NOT NULL, description TEXT,
                picking_strategy TEXT DEFAULT 'WAVE', allocation_rule TEXT DEFAULT 'FIFO',
                max_picks_per_operator INTEGER DEFAULT 50,
                auto_assign_tasks INTEGER DEFAULT 1, release_type TEXT DEFAULT 'IMMEDIATE',
                is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP, created_by INTEGER)'''),

        ('wms_waves', '''
            CREATE TABLE IF NOT EXISTS wms_waves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wave_number TEXT UNIQUE NOT NULL, template_id INTEGER,
                warehouse_id INTEGER NOT NULL, company_id INTEGER, description TEXT,
                picking_strategy TEXT DEFAULT 'WAVE', allocation_rule TEXT DEFAULT 'FIFO',
                max_picks_per_operator INTEGER DEFAULT 50,
                auto_assign_tasks INTEGER DEFAULT 1, release_type TEXT DEFAULT 'IMMEDIATE',
                scheduled_release_time TEXT, status TEXT DEFAULT 'PLANNED',
                priority INTEGER DEFAULT 5, order_count INTEGER DEFAULT 0,
                total_lines INTEGER DEFAULT 0, total_picks INTEGER DEFAULT 0,
                picks_completed INTEGER DEFAULT 0, released_by INTEGER, released_at TEXT,
                completed_by INTEGER, completed_at TEXT, cancelled_by INTEGER,
                cancelled_at TEXT, cancel_reason TEXT, notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP, created_by INTEGER)'''),

        ('wms_wave_orders', '''
            CREATE TABLE IF NOT EXISTS wms_wave_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT, wave_id INTEGER NOT NULL,
                order_id INTEGER NOT NULL, added_by INTEGER,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_qc_inspections', '''
            CREATE TABLE IF NOT EXISTS wms_qc_inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inspection_number TEXT UNIQUE NOT NULL, inspection_type TEXT NOT NULL,
                warehouse_id INTEGER NOT NULL, source_receipt_line_id INTEGER,
                source_return_line_id INTEGER, item_id INTEGER NOT NULL, lot_id INTEGER,
                location_id INTEGER, sample_size INTEGER, inspected_quantity REAL,
                passed_quantity REAL DEFAULT 0, failed_quantity REAL DEFAULT 0,
                result TEXT DEFAULT 'PENDING', defect_codes TEXT, notes TEXT,
                inspected_by INTEGER, inspection_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_usage_decisions', '''
            CREATE TABLE IF NOT EXISTS wms_usage_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_number TEXT UNIQUE NOT NULL, inspection_id INTEGER,
                item_id INTEGER NOT NULL, lot_id INTEGER,
                decision_code TEXT NOT NULL, decision_text TEXT,
                quantity REAL NOT NULL, disposition TEXT, notes TEXT,
                decided_by INTEGER, decided_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_defect_codes', '''
            CREATE TABLE IF NOT EXISTS wms_defect_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL, description TEXT,
                severity TEXT DEFAULT 'MINOR', disposition TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_quality_certificates', '''
            CREATE TABLE IF NOT EXISTS wms_quality_certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                certificate_number TEXT UNIQUE NOT NULL, inspection_id INTEGER,
                lot_id INTEGER, item_id INTEGER NOT NULL, supplier_name TEXT,
                manufacture_date TEXT, expiry_date TEXT, parameters_json TEXT,
                result_summary TEXT, is_passed INTEGER DEFAULT 1,
                issued_by INTEGER, issued_at TEXT, pdf_path TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_aql_rules', '''
            CREATE TABLE IF NOT EXISTS wms_aql_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT, rule_name TEXT NOT NULL,
                inspection_level TEXT DEFAULT 'II', aql_level REAL DEFAULT 1.5,
                lot_size_min INTEGER DEFAULT 1, lot_size_max INTEGER DEFAULT 50000,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_quality_capa', '''
            CREATE TABLE IF NOT EXISTS wms_quality_capa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capa_number TEXT UNIQUE NOT NULL, defect_id INTEGER,
                root_cause TEXT, corrective_action TEXT, preventive_action TEXT,
                responsible_id INTEGER, status TEXT DEFAULT 'OPEN',
                priority TEXT DEFAULT 'MEDIUM', due_date TEXT, completed_at TEXT,
                effectiveness_check TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_quality_holds', '''
            CREATE TABLE IF NOT EXISTS wms_quality_holds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hold_number TEXT UNIQUE NOT NULL, warehouse_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL, lot_id INTEGER, serial_number_id INTEGER,
                location_id INTEGER, quantity_held REAL DEFAULT 0,
                hold_reason TEXT NOT NULL, hold_type TEXT DEFAULT 'INSPECTION',
                source_receipt_line_id INTEGER, source_return_line_id INTEGER,
                source_inspection_id INTEGER, status TEXT DEFAULT 'ACTIVE',
                hold_notes TEXT, held_by INTEGER, held_at TEXT DEFAULT CURRENT_TIMESTAMP,
                released_by INTEGER, released_at TEXT, release_reason TEXT,
                expected_clear_date TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_saved_reports', '''
            CREATE TABLE IF NOT EXISTS wms_saved_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT, report_name TEXT NOT NULL,
                fields_json TEXT, filters_json TEXT, sort_json TEXT,
                created_by INTEGER, is_shared INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_documents', '''
            CREATE TABLE IF NOT EXISTS wms_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_number TEXT UNIQUE NOT NULL, document_type TEXT NOT NULL,
                warehouse_id INTEGER, related_entity_type TEXT,
                related_entity_id INTEGER, reference_number TEXT, issue_date TEXT,
                status TEXT DEFAULT 'DRAFT', prepared_by INTEGER, checked_by INTEGER,
                approved_by INTEGER, content_json TEXT, file_path TEXT, notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_rf_scan_log', '''
            CREATE TABLE IF NOT EXISTS wms_rf_scan_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT, operator_id INTEGER,
                scan_type TEXT NOT NULL, barcode TEXT, item_id INTEGER,
                quantity REAL, location_id INTEGER,
                operation_status TEXT DEFAULT 'SUCCESS', error_message TEXT,
                response_time_ms INTEGER,
                scan_time TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_voice_config', '''
            CREATE TABLE IF NOT EXISTS wms_voice_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE NOT NULL, config_value TEXT,
                config_type TEXT DEFAULT 'string', language TEXT DEFAULT 'en',
                description TEXT, is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_voice_pick_log', '''
            CREATE TABLE IF NOT EXISTS wms_voice_pick_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER,
                operator_id INTEGER, instruction_text TEXT,
                recognized_command TEXT, is_correct INTEGER DEFAULT 0,
                response_time_ms INTEGER, error_type TEXT,
                retry_count INTEGER DEFAULT 0,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_yard_vehicles', '''
            CREATE TABLE IF NOT EXISTS wms_yard_vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT, plate_number TEXT NOT NULL,
                driver_name TEXT, driver_phone TEXT, carrier_name TEXT,
                vehicle_type TEXT DEFAULT 'INBOUND', warehouse_id INTEGER NOT NULL,
                dock_id INTEGER, status TEXT DEFAULT 'WAITING',
                arrival_time TEXT, departure_time TEXT,
                expected_duration_minutes INTEGER DEFAULT 60,
                is_active INTEGER DEFAULT 1, notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_dock_doors', '''
            CREATE TABLE IF NOT EXISTS wms_dock_doors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                door_number TEXT NOT NULL, warehouse_id INTEGER NOT NULL,
                door_type TEXT DEFAULT 'BOTH', status TEXT DEFAULT 'AVAILABLE',
                current_vehicle_id INTEGER, height_limit_cm INTEGER,
                width_limit_cm INTEGER, weight_limit_kg INTEGER,
                is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_dock_schedule', '''
            CREATE TABLE IF NOT EXISTS wms_dock_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scheduled_date TEXT NOT NULL, scheduled_time TEXT,
                warehouse_id INTEGER NOT NULL, dock_id INTEGER, vehicle_type TEXT,
                carrier_name TEXT, plate_number TEXT, driver_name TEXT,
                driver_phone TEXT, reference_number TEXT,
                estimated_duration_minutes INTEGER,
                status TEXT DEFAULT 'SCHEDULED', notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_yard_activity_log', '''
            CREATE TABLE IF NOT EXISTS wms_yard_activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER,
                event TEXT NOT NULL, plate_number TEXT, driver_name TEXT,
                dock_number TEXT, user_id INTEGER,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_work_tasks', '''
            CREATE TABLE IF NOT EXISTS wms_work_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_number TEXT UNIQUE NOT NULL, task_type TEXT NOT NULL,
                warehouse_id INTEGER NOT NULL, location_id INTEGER,
                priority INTEGER DEFAULT 5, status TEXT DEFAULT 'PENDING',
                assigned_to INTEGER, estimated_minutes INTEGER, actual_minutes INTEGER,
                started_at TEXT, completed_at TEXT, completed_by INTEGER,
                reference_type TEXT, reference_number TEXT, notes TEXT,
                exceptions TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP, created_by INTEGER)'''),

        ('wms_alerts', '''
            CREATE TABLE IF NOT EXISTS wms_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT, alert_type TEXT NOT NULL,
                alert_code TEXT, warehouse_id INTEGER, item_id INTEGER,
                location_id INTEGER, severity TEXT DEFAULT 'MEDIUM',
                title TEXT NOT NULL, message TEXT, is_active INTEGER DEFAULT 1,
                is_acknowledged INTEGER DEFAULT 0, acknowledged_by INTEGER,
                acknowledged_at TEXT, resolved_at TEXT, resolved_by INTEGER,
                action_url TEXT, metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_edi_partners', '''
            CREATE TABLE IF NOT EXISTS wms_edi_partners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_name TEXT NOT NULL, partner_type TEXT NOT NULL,
                edi_protocol TEXT DEFAULT 'AS2', endpoint_url TEXT, username TEXT,
                password_encrypted TEXT, certificate_blob TEXT,
                is_active INTEGER DEFAULT 1, is_test_mode INTEGER DEFAULT 1,
                partner_code TEXT UNIQUE, contact_email TEXT, contact_phone TEXT,
                notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_outbound_idocs', '''
            CREATE TABLE IF NOT EXISTS wms_outbound_idocs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idoc_number TEXT UNIQUE NOT NULL, message_type TEXT NOT NULL,
                partner_id INTEGER NOT NULL, status TEXT DEFAULT 'PENDING',
                content_xml TEXT, content_json TEXT, sent_at TEXT,
                acknowledged_at TEXT, error_message TEXT,
                retry_count INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER)'''),

        ('wms_inbound_idocs', '''
            CREATE TABLE IF NOT EXISTS wms_inbound_idocs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idoc_number TEXT UNIQUE NOT NULL, message_type TEXT NOT NULL,
                partner_id INTEGER NOT NULL, status TEXT DEFAULT 'RECEIVED',
                content_xml TEXT, content_json TEXT, processed_at TEXT,
                error_message TEXT, reference_number TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_edi_mappings', '''
            CREATE TABLE IF NOT EXISTS wms_edi_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mapping_name TEXT NOT NULL, message_type TEXT NOT NULL,
                direction TEXT NOT NULL, field_mappings_json TEXT,
                transformation_rules_json TEXT, validation_rules_json TEXT,
                is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP, created_by INTEGER)'''),

        ('wms_edi_audit_log', '''
            CREATE TABLE IF NOT EXISTS wms_edi_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT, idoc_id INTEGER,
                action_type TEXT NOT NULL, old_status TEXT, new_status TEXT,
                details TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER)'''),

        ('wms_notifications', '''
            CREATE TABLE IF NOT EXISTS wms_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                title TEXT NOT NULL, message TEXT,
                notification_type TEXT DEFAULT 'info',
                related_entity_type TEXT, related_entity_id INTEGER,
                is_read INTEGER DEFAULT 0, read_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_audit_log', '''
            CREATE TABLE IF NOT EXISTS wms_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL, entity_type TEXT NOT NULL,
                entity_id INTEGER, details TEXT, user_id INTEGER,
                ip_address TEXT, user_agent TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_user_permissions', '''
            CREATE TABLE IF NOT EXISTS wms_user_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
                permission_key TEXT NOT NULL, granted_by INTEGER,
                granted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, permission_key))'''),

        ('wms_user_companies', '''
            CREATE TABLE IF NOT EXISTS wms_user_companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
                company_id INTEGER NOT NULL,
                UNIQUE(user_id, company_id))'''),

        ('wms_user_warehouses', '''
            CREATE TABLE IF NOT EXISTS wms_user_warehouses (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL,
                UNIQUE(user_id, warehouse_id))'''),

        ('wms_code_sequences', '''
            CREATE TABLE IF NOT EXISTS wms_code_sequences (
                id INTEGER PRIMARY KEY AUTOINCREMENT, code_type TEXT NOT NULL,
                year INTEGER NOT NULL, company_id INTEGER,
                last_seq INTEGER NOT NULL DEFAULT 0,
                UNIQUE(code_type, year, company_id))'''),

        ('wms_stock_status_history', '''
            CREATE TABLE IF NOT EXISTS wms_stock_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL,
                lot_id INTEGER, serial_number_id INTEGER,
                warehouse_id INTEGER NOT NULL, location_id INTEGER, old_status TEXT,
                new_status TEXT NOT NULL, reason_code TEXT, reference_type TEXT,
                reference_number TEXT, changed_by INTEGER,
                changed_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_location_types', '''
            CREATE TABLE IF NOT EXISTS wms_location_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL, name_local TEXT, description TEXT,
                is_picking INTEGER DEFAULT 1, is_putaway INTEGER DEFAULT 1,
                is_storage INTEGER DEFAULT 1, is_staging INTEGER DEFAULT 0,
                is_receiving INTEGER DEFAULT 0, is_dispatch INTEGER DEFAULT 0,
                is_quarantine INTEGER DEFAULT 0, is_damaged INTEGER DEFAULT 0,
                is_return INTEGER DEFAULT 0, is_inspection INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),

        ('wms_reason_codes', '''
            CREATE TABLE IF NOT EXISTS wms_reason_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL,
                description TEXT NOT NULL, reason_type TEXT NOT NULL,
                is_active INTEGER DEFAULT 1, requires_approval INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)'''),
    ]

    for name, sql in table_defs:
        try:
            db.execute(sql)
        except Exception as e:
            print(f"Error creating {name}: {e}")

    db.commit()
    _wms_schema_initialized = True