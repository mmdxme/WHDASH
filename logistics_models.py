"""
Logistics Management System - Database Models
==============================================
This file contains all Logistics/TMS-related database table definitions.

Logistics Tables:
- logistics_shipments: Main shipment records
- logistics_shipment_lines: Line items per shipment
- logistics_delivery_orders: Delivery order management
- logistics_pickup_orders: Pickup order management
- logistics_trips: Trip management (extends existing delivery_trips)
- logistics_route_masters: Route definitions
- logistics_route_stops: Route stop sequences
- logistics_drivers: Driver master data
- logistics_driver_documents: Driver license/documents
- logistics_vehicles: Vehicle/fleet master
- logistics_vehicle_documents: Vehicle registration/insurance docs
- logistics_carriers: Third-party carrier management
- logistics_carrier_rates: Carrier pricing agreements
- logistics_dispatch_plans: Dispatch planning
- logistics_pod_records: Proof of delivery
- logistics_cost_entries: Cost tracking per shipment
- logistics_expense_entries: Expense entries per trip
- logistics_incidents: Incident/exception tracking
- logistics_alerts: System alerts and notifications
- logistics_settings: Configurable settings
- logistics_audit_logs: Audit trail for critical changes
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'warehouse.db'))


def get_db():
    """Get database connection with Row factory for dict-like access."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# =============================================================================
# LOGISTICS TABLE DEFINITIONS
# =============================================================================

LOGISTICS_TABLES = [
    # -------------------------------------------------------------------------
    # 1. Logistics Shipments - Main shipment records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_shipments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shipment_code TEXT UNIQUE NOT NULL,
        shipment_type TEXT NOT NULL DEFAULT 'outbound',
        status TEXT NOT NULL DEFAULT 'draft',
        priority TEXT DEFAULT 'Normal',
        company_id INTEGER,
        branch_id INTEGER,
        warehouse_id INTEGER,
        customer_id INTEGER,
        consignee_name TEXT,
        consignee_phone TEXT,
        consignee_address TEXT,
        pickup_address TEXT,
        delivery_address TEXT,
        billing_party TEXT,
        transport_mode TEXT,
        requested_date DATE,
        planned_date DATE,
        dispatch_date DATE,
        estimated_delivery DATE,
        actual_delivery DATETIME,
        sla_target DATETIME,
        carrier_id INTEGER,
        driver_id INTEGER,
        vehicle_id INTEGER,
        route_id INTEGER,
        trip_id INTEGER,
        shipment_reference TEXT,
        notes TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL,
        FOREIGN KEY (warehouse_id) REFERENCES warehouses(id) ON DELETE SET NULL,
        FOREIGN KEY (customer_id) REFERENCES sdad_customers(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 2. Logistics Shipment Lines - Items/Cargo per shipment
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_shipment_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shipment_id INTEGER NOT NULL,
        part_id INTEGER,
        description TEXT,
        quantity INTEGER DEFAULT 1,
        unit TEXT DEFAULT 'pcs',
        weight REAL DEFAULT 0,
        volume REAL DEFAULT 0,
        cartons INTEGER DEFAULT 0,
        pallets INTEGER DEFAULT 0,
        special_handling TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (shipment_id) REFERENCES logistics_shipments(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 3. Logistics Delivery Orders - Delivery order management
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_delivery_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        do_number TEXT UNIQUE NOT NULL,
        shipment_id INTEGER,
        customer_id INTEGER,
        contact_person TEXT,
        contact_phone TEXT,
        shipping_address TEXT,
        billing_address TEXT,
        scheduled_date DATE,
        promised_date DATE,
        priority TEXT DEFAULT 'Normal',
        required_vehicle_type TEXT,
        required_handling TEXT,
        temperature_control INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending',
        picked_status TEXT DEFAULT 'pending',
        packed_status TEXT DEFAULT 'pending',
        loaded_status TEXT DEFAULT 'pending',
        out_for_delivery INTEGER DEFAULT 0,
        delivered_status TEXT DEFAULT 'pending',
        delivery_completed_at DATETIME,
        receiver_name TEXT,
        receiver_phone TEXT,
        signature_path TEXT,
        photo_path TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (shipment_id) REFERENCES logistics_shipments(id) ON DELETE SET NULL,
        FOREIGN KEY (customer_id) REFERENCES sdad_customers(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 4. Logistics Pickup Orders - Pickup management
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_pickup_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pickup_number TEXT UNIQUE NOT NULL,
        shipment_id INTEGER,
        pickup_type TEXT DEFAULT 'supplier',
        customer_id INTEGER,
        supplier_name TEXT,
        contact_person TEXT,
        contact_phone TEXT,
        pickup_address TEXT,
        scheduled_date DATE,
        priority TEXT DEFAULT 'Normal',
        status TEXT DEFAULT 'pending',
        picked_up INTEGER DEFAULT 0,
        picked_up_at DATETIME,
        proof_of_pickup TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (shipment_id) REFERENCES logistics_shipments(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 5. Logistics Route Masters - Route definitions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_route_masters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        route_code TEXT UNIQUE NOT NULL,
        route_name TEXT NOT NULL,
        description TEXT,
        origin_id INTEGER,
        destination_id INTEGER,
        distance_km REAL DEFAULT 0,
        estimated_time_minutes INTEGER DEFAULT 0,
        cost_per_km REAL DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 6. Logistics Route Stops - Stop sequence per route
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_route_stops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        route_id INTEGER NOT NULL,
        stop_order INTEGER NOT NULL,
        stop_name TEXT NOT NULL,
        address TEXT,
        latitude REAL,
        longitude REAL,
        estimated_arrival TIME,
        estimated_departure TIME,
        service_time_minutes INTEGER DEFAULT 15,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (route_id) REFERENCES logistics_route_masters(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 7. Logistics Drivers - Driver master (linked to HR)
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        driver_code TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        employee_type TEXT DEFAULT 'internal',
        company_id INTEGER,
        branch_id INTEGER,
        mobile TEXT,
        emergency_contact TEXT,
        license_number TEXT,
        license_class TEXT,
        license_expiry DATE,
        nationality TEXT,
        status TEXT DEFAULT 'active',
        availability TEXT DEFAULT 'available',
        assigned_vehicle_id INTEGER,
        backup_vehicle_id INTEGER,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 8. Logistics Driver Documents - Driver documents tracking
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_driver_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_id INTEGER NOT NULL,
        document_type TEXT NOT NULL,
        document_number TEXT,
        issue_date DATE,
        expiry_date DATE,
        file_path TEXT,
        is_verified INTEGER DEFAULT 0,
        verified_by INTEGER,
        verified_at DATETIME,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (driver_id) REFERENCES logistics_drivers(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 9. Logistics Vehicles - Vehicle/fleet master
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_code TEXT UNIQUE NOT NULL,
        plate_number TEXT UNIQUE NOT NULL,
        fleet_number TEXT,
        vehicle_type TEXT NOT NULL,
        vehicle_category TEXT,
        company_id INTEGER,
        branch_id INTEGER,
        brand TEXT,
        model TEXT,
        year INTEGER,
        vin_number TEXT,
        fuel_type TEXT DEFAULT 'diesel',
        load_capacity_kg REAL DEFAULT 0,
        load_capacity_volume REAL DEFAULT 0,
        pallet_capacity INTEGER DEFAULT 0,
        carton_capacity INTEGER DEFAULT 0,
        odometer_reading REAL DEFAULT 0,
        fuel_tank_capacity REAL DEFAULT 0,
        status TEXT DEFAULT 'active',
        availability TEXT DEFAULT 'available',
        gps_tracker_ref TEXT,
        assigned_driver_id INTEGER,
        backup_driver_id INTEGER,
        cost_center TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (assigned_driver_id) REFERENCES logistics_drivers(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 10. Logistics Vehicle Documents - Vehicle docs (registration, insurance)
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_vehicle_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER NOT NULL,
        document_type TEXT NOT NULL,
        document_number TEXT,
        issue_date DATE,
        expiry_date DATE,
        file_path TEXT,
        is_verified INTEGER DEFAULT 0,
        verified_by INTEGER,
        verified_at DATETIME,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vehicle_id) REFERENCES logistics_vehicles(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 11. Logistics Vehicles Maintenance - Vehicle maintenance tracking
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_vehicle_maintenance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER NOT NULL,
        maintenance_type TEXT NOT NULL,
        description TEXT,
        scheduled_date DATE,
        completed_date DATE,
        odometer_reading REAL,
        cost REAL DEFAULT 0,
        service_provider TEXT,
        next_service_date DATE,
        next_service_km REAL,
        status TEXT DEFAULT 'pending',
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vehicle_id) REFERENCES logistics_vehicles(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 12. Logistics Carriers - Third-party carrier management
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_carriers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        carrier_code TEXT UNIQUE NOT NULL,
        carrier_name TEXT NOT NULL,
        contact_person TEXT,
        phone TEXT,
        email TEXT,
        address TEXT,
        service_areas TEXT,
        vehicle_types TEXT,
        service_levels TEXT,
        credit_terms TEXT,
        rating REAL DEFAULT 0,
        status TEXT DEFAULT 'active',
        contract_start DATE,
        contract_end DATE,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 13. Logistics Carrier Rates - Carrier pricing agreements
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_carrier_rates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        carrier_id INTEGER NOT NULL,
        rate_name TEXT NOT NULL,
        origin TEXT,
        destination TEXT,
        vehicle_type TEXT,
        rate_per_km REAL DEFAULT 0,
        minimum_charge REAL DEFAULT 0,
        flat_rate REAL DEFAULT 0,
        fuel_surcharge_percent REAL DEFAULT 0,
        effective_from DATE,
        effective_to DATE,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (carrier_id) REFERENCES logistics_carriers(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 14. Logistics Dispatch Plans - Dispatch wave planning
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_dispatch_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_code TEXT UNIQUE NOT NULL,
        plan_date DATE NOT NULL,
        branch_id INTEGER,
        warehouse_id INTEGER,
        total_shipments INTEGER DEFAULT 0,
        total_weight REAL DEFAULT 0,
        total_volume REAL DEFAULT 0,
        total_vehicles INTEGER DEFAULT 0,
        status TEXT DEFAULT 'planned',
        approved_by INTEGER,
        approved_at DATETIME,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 15. Logistics Dispatch Wave Details - Wave-to-shipment linkage
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_dispatch_wave_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dispatch_plan_id INTEGER NOT NULL,
        shipment_id INTEGER NOT NULL,
        vehicle_id INTEGER,
        driver_id INTEGER,
        route_id INTEGER,
        sequence_order INTEGER,
        loading_sequence INTEGER,
        status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (dispatch_plan_id) REFERENCES logistics_dispatch_plans(id) ON DELETE CASCADE,
        FOREIGN KEY (shipment_id) REFERENCES logistics_shipments(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 16. Logistics POD Records - Proof of Delivery
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_pod_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shipment_id INTEGER NOT NULL,
        delivery_order_id INTEGER,
        trip_id INTEGER,
        driver_id INTEGER,
        customer_id INTEGER,
        receiver_name TEXT,
        receiver_phone TEXT,
        delivery_timestamp DATETIME NOT NULL,
        latitude REAL,
        longitude REAL,
        signature_data TEXT,
        photo_paths TEXT,
        notes TEXT,
        delivery_status TEXT DEFAULT 'completed',
        shortage_confirmed INTEGER DEFAULT 0,
        damage_confirmed INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (shipment_id) REFERENCES logistics_shipments(id) ON DELETE CASCADE,
        FOREIGN KEY (delivery_order_id) REFERENCES logistics_delivery_orders(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 17. Logistics Cost Entries - Cost tracking per shipment
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_cost_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shipment_id INTEGER NOT NULL,
        trip_id INTEGER,
        cost_type TEXT NOT NULL,
        description TEXT,
        amount REAL NOT NULL DEFAULT 0,
        currency TEXT DEFAULT 'AED',
        cost_category TEXT,
        vendor_id INTEGER,
        invoice_reference TEXT,
        is_approved INTEGER DEFAULT 0,
        approved_by INTEGER,
        approved_at DATETIME,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (shipment_id) REFERENCES logistics_shipments(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 18. Logistics Expense Entries - Trip-level expenses
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_expense_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trip_id INTEGER NOT NULL,
        expense_type TEXT NOT NULL,
        description TEXT,
        amount REAL NOT NULL DEFAULT 0,
        currency TEXT DEFAULT 'AED',
        receipt_path TEXT,
        is_approved INTEGER DEFAULT 0,
        approved_by INTEGER,
        approved_at DATETIME,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (trip_id) REFERENCES delivery_trips(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 19. Logistics Incidents - Incident/exception tracking
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_number TEXT UNIQUE NOT NULL,
        shipment_id INTEGER,
        trip_id INTEGER,
        driver_id INTEGER,
        vehicle_id INTEGER,
        customer_id INTEGER,
        incident_type TEXT NOT NULL,
        severity TEXT DEFAULT 'medium',
        incident_date DATETIME NOT NULL,
        description TEXT,
        responsible_party TEXT,
        action_taken TEXT,
        status TEXT DEFAULT 'open',
        cost_impact REAL DEFAULT 0,
        sla_impact TEXT,
        closed_by INTEGER,
        closed_at DATETIME,
        closure_notes TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (shipment_id) REFERENCES logistics_shipments(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 20. Logistics Alert Rules - Configurable alert definitions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_code TEXT UNIQUE NOT NULL,
        alert_name TEXT NOT NULL,
        alert_type TEXT NOT NULL,
        trigger_condition TEXT NOT NULL,
        notification_channels TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 21. Logistics Notifications - Alert notification records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        notification_code TEXT UNIQUE,
        alert_id INTEGER,
        shipment_id INTEGER,
        trip_id INTEGER,
        driver_id INTEGER,
        vehicle_id INTEGER,
        title TEXT NOT NULL,
        message TEXT,
        notification_type TEXT,
        is_read INTEGER DEFAULT 0,
        read_at DATETIME,
        read_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (alert_id) REFERENCES logistics_alerts(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 22. Logistics Settings - Configurable settings
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_key TEXT UNIQUE NOT NULL,
        setting_value TEXT,
        setting_type TEXT DEFAULT 'Text',
        category TEXT,
        description TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 23. Logistics Audit Logs - Audit trail for critical changes
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,
        entity_id INTEGER,
        action TEXT NOT NULL,
        field_name TEXT,
        old_value TEXT,
        new_value TEXT,
        user_id INTEGER,
        ip_address TEXT,
        user_agent TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 24. Logistics Shipment Status History - Status change tracking
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_shipment_status_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shipment_id INTEGER NOT NULL,
        from_status TEXT,
        to_status TEXT NOT NULL,
        changed_by INTEGER,
        changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        reason TEXT,
        notes TEXT,
        FOREIGN KEY (shipment_id) REFERENCES logistics_shipments(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 25. Logistics Document Templates - Transport form templates
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_document_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_code TEXT UNIQUE NOT NULL,
        template_name TEXT NOT NULL,
        document_type TEXT NOT NULL,
        template_content TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 26. Logistics Generated Documents - Generated transport documents
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_generated_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_number TEXT UNIQUE NOT NULL,
        shipment_id INTEGER,
        trip_id INTEGER,
        document_type TEXT NOT NULL,
        file_path TEXT,
        generated_by INTEGER,
        generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (shipment_id) REFERENCES logistics_shipments(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 27. Logistics Trip Expenses - Extended trip cost tracking
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_trip_expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trip_id INTEGER NOT NULL,
        expense_category TEXT NOT NULL,
        expense_type TEXT NOT NULL,
        amount REAL NOT NULL DEFAULT 0,
        currency TEXT DEFAULT 'AED',
        description TEXT,
        receipt_path TEXT,
        is_approved INTEGER DEFAULT 0,
        approved_by INTEGER,
        approved_at DATETIME,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (trip_id) REFERENCES delivery_trips(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 28. Logistics Delivery Schedules - Appointment/schedule management
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_delivery_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        schedule_code TEXT UNIQUE NOT NULL,
        shipment_id INTEGER,
        delivery_order_id INTEGER,
        customer_id INTEGER,
        scheduled_date DATE NOT NULL,
        scheduled_time_from TIME,
        scheduled_time_to TIME,
        actual_time_from TIME,
        actual_time_to TIME,
        dock_door_id INTEGER,
        gate_id INTEGER,
        vehicle_id INTEGER,
        driver_id INTEGER,
        status TEXT DEFAULT 'scheduled',
        appointment_type TEXT DEFAULT 'delivery',
        customer_preference TEXT,
        is_rescheduled INTEGER DEFAULT 0,
        original_schedule_id INTEGER,
        scheduling_notes TEXT,
        checked_in_at DATETIME,
        checked_out_at DATETIME,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (shipment_id) REFERENCES logistics_shipments(id) ON DELETE SET NULL,
        FOREIGN KEY (delivery_order_id) REFERENCES logistics_delivery_orders(id) ON DELETE SET NULL,
        FOREIGN KEY (customer_id) REFERENCES sdad_customers(id) ON DELETE SET NULL,
        FOREIGN KEY (dock_door_id) REFERENCES logistics_dock_doors(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 29. Logistics Load Plans - Load planning and consolidation
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_load_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        load_code TEXT UNIQUE NOT NULL,
        load_name TEXT,
        load_date DATE NOT NULL,
        vehicle_id INTEGER,
        driver_id INTEGER,
        route_id INTEGER,
        total_weight REAL DEFAULT 0,
        total_volume REAL DEFAULT 0,
        total_pallets INTEGER DEFAULT 0,
        total_cartons INTEGER DEFAULT 0,
        total_shipments INTEGER DEFAULT 0,
        total_stops INTEGER DEFAULT 0,
        status TEXT DEFAULT 'planned',
        load_type TEXT DEFAULT 'standard',
        priority TEXT DEFAULT 'Normal',
        dispatch_time TIME,
        estimated_completion TIME,
        actual_departure DATETIME,
        actual_return DATETIME,
        notes TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vehicle_id) REFERENCES logistics_vehicles(id) ON DELETE SET NULL,
        FOREIGN KEY (driver_id) REFERENCES logistics_drivers(id) ON DELETE SET NULL,
        FOREIGN KEY (route_id) REFERENCES logistics_route_masters(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 30. Logistics Load Plan Shipments - Shipments assigned to loads
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_load_plan_shipments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        load_plan_id INTEGER NOT NULL,
        shipment_id INTEGER NOT NULL,
        sequence_order INTEGER DEFAULT 1,
        stop_number INTEGER DEFAULT 1,
        estimated_arrival TIME,
        actual_arrival TIME,
        status TEXT DEFAULT 'assigned',
        loading_sequence INTEGER,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (load_plan_id) REFERENCES logistics_load_plans(id) ON DELETE CASCADE,
        FOREIGN KEY (shipment_id) REFERENCES logistics_shipments(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 31. Logistics Dock Doors - Dock/gate scheduling
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_dock_doors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dock_code TEXT UNIQUE NOT NULL,
        dock_name TEXT NOT NULL,
        location TEXT,
        dock_type TEXT DEFAULT 'receiving',
        capacity REAL DEFAULT 0,
        capacity_unit TEXT DEFAULT 'kg',
        status TEXT DEFAULT 'available',
        operating_hours_from TIME,
        operating_hours_to TIME,
        is_active INTEGER DEFAULT 1,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 32. Logistics Delivery Slots - Time slot definitions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_delivery_slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slot_date DATE NOT NULL,
        slot_time_from TIME NOT NULL,
        slot_time_to TIME NOT NULL,
        zone TEXT,
        slot_type TEXT DEFAULT 'delivery',
        capacity INTEGER DEFAULT 0,
        booked INTEGER DEFAULT 0,
        available INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 33. Logistics Schedule Exceptions - Schedule conflicts/exceptions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_schedule_exceptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exception_code TEXT UNIQUE NOT NULL,
        exception_type TEXT NOT NULL,
        schedule_id INTEGER,
        shipment_id INTEGER,
        exception_date DATE NOT NULL,
        exception_time_from TIME,
        exception_time_to TIME,
        reason TEXT,
        status TEXT DEFAULT 'open',
        resolved_by INTEGER,
        resolved_at DATETIME,
        resolution_notes TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (schedule_id) REFERENCES logistics_delivery_schedules(id) ON DELETE SET NULL,
        FOREIGN KEY (shipment_id) REFERENCES logistics_shipments(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 30. Logistics Trips - Full trip lifecycle management
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_trips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trip_code TEXT UNIQUE NOT NULL,
        trip_name TEXT,
        status TEXT NOT NULL DEFAULT 'draft',
        priority TEXT DEFAULT 'Normal',
        route_id INTEGER,
        vehicle_id INTEGER,
        driver_id INTEGER,
        helper_id INTEGER,
        planned_departure DATETIME,
        planned_arrival DATETIME,
        actual_departure DATETIME,
        actual_arrival DATETIME,
        origin_location TEXT,
        destination_location TEXT,
        distance_km REAL DEFAULT 0,
        total_stops INTEGER DEFAULT 0,
        completed_stops INTEGER DEFAULT 0,
        failed_stops INTEGER DEFAULT 0,
        total_weight_kg REAL DEFAULT 0,
        total_volume_m3 REAL DEFAULT 0,
        estimated_cost REAL DEFAULT 0,
        actual_cost REAL DEFAULT 0,
        fuel_cost REAL DEFAULT 0,
        tolls_cost REAL DEFAULT 0,
        driver_allowance REAL DEFAULT 0,
        notes TEXT,
        cancellation_reason TEXT,
        closed_by INTEGER,
        closed_at DATETIME,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 31. Logistics Trip Stops - Stop sequence for each trip
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_trip_stops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trip_id INTEGER NOT NULL,
        stop_sequence INTEGER NOT NULL,
        route_stop_id INTEGER,
        shipment_id INTEGER,
        customer_id INTEGER,
        stop_name TEXT NOT NULL,
        address TEXT,
        latitude REAL,
        longitude REAL,
        contact_person TEXT,
        contact_phone TEXT,
        planned_arrival DATETIME,
        planned_departure DATETIME,
        actual_arrival DATETIME,
        actual_departure DATETIME,
        service_time_minutes INTEGER DEFAULT 15,
        sequence_order INTEGER DEFAULT 1,
        status TEXT DEFAULT 'pending',
        failure_reason TEXT,
        proof_of_delivery TEXT,
        receiver_name TEXT,
        receiver_signature TEXT,
        photo_path TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (trip_id) REFERENCES logistics_trips(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 32. Logistics Route Templates - Reusable route templates
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_route_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_code TEXT UNIQUE NOT NULL,
        template_name TEXT NOT NULL,
        description TEXT,
        route_type TEXT DEFAULT 'delivery',
        service_zone TEXT,
        vehicle_type_required TEXT,
        distance_km REAL DEFAULT 0,
        estimated_time_minutes INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        usage_count INTEGER DEFAULT 0,
        last_used_at DATETIME,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 33. Logistics Service Zones - Geographic service zones
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_service_zones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        zone_code TEXT UNIQUE NOT NULL,
        zone_name TEXT NOT NULL,
        zone_type TEXT DEFAULT 'service',
        description TEXT,
        city TEXT,
        state TEXT,
        country TEXT,
        postal_code TEXT,
        boundary_coords TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 34. Logistics Route Optimization Rules
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_route_optimization_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_name TEXT NOT NULL,
        rule_code TEXT UNIQUE NOT NULL,
        rule_type TEXT NOT NULL,
        priority INTEGER DEFAULT 0,
        condition_json TEXT,
        action_json TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 35. Logistics Stop Checkpoints - Real-time stop tracking
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_stop_checkpoints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        checkpoint_code TEXT UNIQUE NOT NULL,
        trip_id INTEGER NOT NULL,
        stop_id INTEGER,
        shipment_id INTEGER,
        checkpoint_time DATETIME NOT NULL,
        checkpoint_type TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        geofence_status TEXT DEFAULT 'inside',
        eta_minutes INTEGER,
        actual_arrival DATETIME,
        actual_departure DATETIME,
        dwell_time_minutes INTEGER,
        status TEXT DEFAULT 'pending',
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (trip_id) REFERENCES logistics_trips(id) ON DELETE CASCADE,
        FOREIGN KEY (stop_id) REFERENCES logistics_trip_stops(id) ON DELETE SET NULL,
        FOREIGN KEY (shipment_id) REFERENCES logistics_shipments(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 36. Logistics Freight Costs - Detailed freight cost tracking
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_freight_costs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cost_code TEXT UNIQUE NOT NULL,
        trip_id INTEGER,
        shipment_id INTEGER,
        cost_category TEXT NOT NULL,
        cost_type TEXT NOT NULL,
        amount REAL NOT NULL DEFAULT 0,
        currency TEXT DEFAULT 'AED',
        vendor_id INTEGER,
        vendor_name TEXT,
        invoice_number TEXT,
        invoice_date DATE,
        notes TEXT,
        is_approved INTEGER DEFAULT 0,
        approved_by INTEGER,
        approved_at DATETIME,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (trip_id) REFERENCES logistics_trips(id) ON DELETE SET NULL,
        FOREIGN KEY (shipment_id) REFERENCES logistics_shipments(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 37. Logistics Fleet KPIs - Vehicle/Driver performance metrics
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_fleet_kpis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kpi_date DATE NOT NULL,
        vehicle_id INTEGER,
        driver_id INTEGER,
        total_km REAL DEFAULT 0,
        fuel_liters REAL DEFAULT 0,
        fuel_cost REAL DEFAULT 0,
        trips_completed INTEGER DEFAULT 0,
        deliveries_completed INTEGER DEFAULT 0,
        on_time_count INTEGER DEFAULT 0,
        late_count INTEGER DEFAULT 0,
        failed_count INTEGER DEFAULT 0,
        on_time_rate REAL DEFAULT 0,
        idle_time_minutes INTEGER DEFAULT 0,
        driving_time_minutes INTEGER DEFAULT 0,
        exception_count INTEGER DEFAULT 0,
        carbon_kg REAL DEFAULT 0,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vehicle_id) REFERENCES logistics_vehicles(id) ON DELETE SET NULL,
        FOREIGN KEY (driver_id) REFERENCES logistics_drivers(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 38. Logistics Transport Documents - Document management
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS logistics_transport_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_code TEXT UNIQUE NOT NULL,
        doc_type TEXT NOT NULL,
        trip_id INTEGER,
        shipment_id INTEGER,
        vehicle_id INTEGER,
        driver_id INTEGER,
        file_path TEXT,
        file_name TEXT,
        file_size INTEGER,
        mime_type TEXT,
        uploaded_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (trip_id) REFERENCES logistics_trips(id) ON DELETE SET NULL,
        FOREIGN KEY (shipment_id) REFERENCES logistics_shipments(id) ON DELETE SET NULL,
        FOREIGN KEY (vehicle_id) REFERENCES logistics_vehicles(id) ON DELETE SET NULL,
        FOREIGN KEY (driver_id) REFERENCES logistics_drivers(id) ON DELETE SET NULL
    )""",
]


def run_logistics_migrations():
    """
    Run all Logistics table migrations.
    Creates all Logistics tables if they don't exist.
    Seeds default data for essential lookups.
    """
    conn = get_db()
    try:
        # Create all Logistics tables
        for table_sql in LOGISTICS_TABLES:
            conn.executescript(table_sql)

        conn.commit()

        # Seed default data
        seed_logistics_defaults(conn)

        return True, "Logistics migrations completed successfully"
    except Exception as e:
        conn.rollback()
        return False, f"Logistics migration error: {str(e)}"
    finally:
        conn.close()


# =============================================================================
# TMS TABLE MIGRATIONS
# =============================================================================

TMS_TABLES = [
    # Stop Checkpoints
    """CREATE TABLE IF NOT EXISTS logistics_stop_checkpoints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        checkpoint_code TEXT UNIQUE NOT NULL,
        trip_id INTEGER NOT NULL,
        stop_id INTEGER,
        shipment_id INTEGER,
        checkpoint_time DATETIME NOT NULL,
        checkpoint_type TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        geofence_status TEXT DEFAULT 'inside',
        eta_minutes INTEGER,
        actual_arrival DATETIME,
        actual_departure DATETIME,
        dwell_time_minutes INTEGER,
        status TEXT DEFAULT 'pending',
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (trip_id) REFERENCES logistics_trips(id) ON DELETE CASCADE,
        FOREIGN KEY (stop_id) REFERENCES logistics_trip_stops(id) ON DELETE SET NULL,
        FOREIGN KEY (shipment_id) REFERENCES logistics_shipments(id) ON DELETE SET NULL
    )""",

    # Freight Costs
    """CREATE TABLE IF NOT EXISTS logistics_freight_costs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cost_code TEXT UNIQUE NOT NULL,
        trip_id INTEGER,
        shipment_id INTEGER,
        cost_category TEXT NOT NULL,
        cost_type TEXT NOT NULL,
        amount REAL NOT NULL DEFAULT 0,
        currency TEXT DEFAULT 'AED',
        vendor_id INTEGER,
        vendor_name TEXT,
        invoice_number TEXT,
        invoice_date DATE,
        notes TEXT,
        is_approved INTEGER DEFAULT 0,
        approved_by INTEGER,
        approved_at DATETIME,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (trip_id) REFERENCES logistics_trips(id) ON DELETE SET NULL,
        FOREIGN KEY (shipment_id) REFERENCES logistics_shipments(id) ON DELETE SET NULL
    )""",

    # Fleet KPIs
    """CREATE TABLE IF NOT EXISTS logistics_fleet_kpis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kpi_date DATE NOT NULL,
        vehicle_id INTEGER,
        driver_id INTEGER,
        total_km REAL DEFAULT 0,
        fuel_liters REAL DEFAULT 0,
        fuel_cost REAL DEFAULT 0,
        trips_completed INTEGER DEFAULT 0,
        deliveries_completed INTEGER DEFAULT 0,
        on_time_count INTEGER DEFAULT 0,
        late_count INTEGER DEFAULT 0,
        failed_count INTEGER DEFAULT 0,
        on_time_rate REAL DEFAULT 0,
        idle_time_minutes INTEGER DEFAULT 0,
        driving_time_minutes INTEGER DEFAULT 0,
        exception_count INTEGER DEFAULT 0,
        carbon_kg REAL DEFAULT 0,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vehicle_id) REFERENCES logistics_vehicles(id) ON DELETE SET NULL,
        FOREIGN KEY (driver_id) REFERENCES logistics_drivers(id) ON DELETE SET NULL
    )""",

    # Transport Documents
    """CREATE TABLE IF NOT EXISTS logistics_transport_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_code TEXT UNIQUE NOT NULL,
        doc_type TEXT NOT NULL,
        trip_id INTEGER,
        shipment_id INTEGER,
        vehicle_id INTEGER,
        driver_id INTEGER,
        file_path TEXT,
        file_name TEXT,
        file_size INTEGER,
        mime_type TEXT,
        uploaded_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (trip_id) REFERENCES logistics_trips(id) ON DELETE SET NULL,
        FOREIGN KEY (shipment_id) REFERENCES logistics_shipments(id) ON DELETE SET NULL,
        FOREIGN KEY (vehicle_id) REFERENCES logistics_vehicles(id) ON DELETE SET NULL,
        FOREIGN KEY (driver_id) REFERENCES logistics_drivers(id) ON DELETE SET NULL
    )""",
]


def ensure_tms_tables():
    """
    Run TMS table migrations.
    Creates TMS-specific tables if they don't exist.
    These include: stop_checkpoints, freight_costs, fleet_kpis, transport_documents.
    """
    conn = get_db()
    try:
        for table_sql in TMS_TABLES:
            conn.executescript(table_sql)

        conn.commit()
        return True, "TMS tables created successfully"
    except Exception as e:
        conn.rollback()
        return False, f"TMS table migration error: {str(e)}"
    finally:
        conn.close()


def seed_logistics_defaults(conn):
    """Seed default Logistics data for essential lookups."""

    # Seed default logistics settings
    default_settings = [
        ('shipment_type_outbound', 'Outbound', 'Text', 'Shipment Types', 'Outbound shipment type'),
        ('shipment_type_inbound', 'Inbound', 'Text', 'Shipment Types', 'Inbound shipment type'),
        ('shipment_type_transfer', 'Transfer', 'Text', 'Shipment Types', 'Transfer shipment type'),
        ('shipment_type_return', 'Return', 'Text', 'Shipment Types', 'Return shipment type'),
        ('shipment_type_pickup', 'Pickup', 'Text', 'Shipment Types', 'Pickup shipment type'),
        ('shipment_type_intercompany', 'Inter-Company', 'Text', 'Shipment Types', 'Inter-company shipment type'),
        ('status_draft', 'Draft', 'Text', 'Shipment Status', 'Draft status'),
        ('status_created', 'Created', 'Text', 'Shipment Status', 'Created status'),
        ('status_planned', 'Planned', 'Text', 'Shipment Status', 'Planned status'),
        ('status_scheduled', 'Scheduled', 'Text', 'Shipment Status', 'Scheduled status'),
        ('status_ready_dispatch', 'Ready to Dispatch', 'Text', 'Shipment Status', 'Ready to dispatch status'),
        ('status_assigned', 'Assigned', 'Text', 'Shipment Status', 'Assigned status'),
        ('status_loaded', 'Loaded', 'Text', 'Shipment Status', 'Loaded status'),
        ('status_departed', 'Departed', 'Text', 'Shipment Status', 'Departed status'),
        ('status_in_transit', 'In Transit', 'Text', 'Shipment Status', 'In transit status'),
        ('status_at_stop', 'At Stop', 'Text', 'Shipment Status', 'At stop status'),
        ('status_delivered', 'Delivered', 'Text', 'Shipment Status', 'Delivered status'),
        ('status_partially_delivered', 'Partially Delivered', 'Text', 'Shipment Status', 'Partially delivered status'),
        ('status_delivery_attempted', 'Delivery Attempted', 'Text', 'Shipment Status', 'Delivery attempted status'),
        ('status_failed_delivery', 'Failed Delivery', 'Text', 'Shipment Status', 'Failed delivery status'),
        ('status_customer_unavailable', 'Customer Unavailable', 'Text', 'Shipment Status', 'Customer unavailable status'),
        ('status_address_issue', 'Address Issue', 'Text', 'Shipment Status', 'Address issue status'),
        ('status_rescheduled', 'Rescheduled', 'Text', 'Shipment Status', 'Rescheduled status'),
        ('status_returned', 'Returned', 'Text', 'Shipment Status', 'Returned status'),
        ('status_cancelled', 'Cancelled', 'Text', 'Shipment Status', 'Cancelled status'),
        ('status_closed', 'Closed', 'Text', 'Shipment Status', 'Closed status'),
        ('priority_low', 'Low', 'Text', 'Priority', 'Low priority'),
        ('priority_normal', 'Normal', 'Text', 'Priority', 'Normal priority'),
        ('priority_high', 'High', 'Text', 'Priority', 'High priority'),
        ('priority_urgent', 'Urgent', 'Text', 'Priority', 'Urgent priority'),
        ('transport_mode_road', 'Road', 'Text', 'Transport Mode', 'Road transport'),
        ('transport_mode_sea', 'Sea', 'Text', 'Transport Mode', 'Sea transport'),
        ('transport_mode_air', 'Air', 'Text', 'Transport Mode', 'Air transport'),
        ('transport_mode_rail', 'Rail', 'Text', 'Transport Mode', 'Rail transport'),
        ('transport_mode_multimodal', 'Multimodal', 'Text', 'Transport Mode', 'Multimodal transport'),
        ('cost_type_freight', 'Freight', 'Text', 'Cost Types', 'Freight cost'),
        ('cost_type_fuel', 'Fuel', 'Text', 'Cost Types', 'Fuel cost'),
        ('cost_type_tolls', 'Tolls', 'Text', 'Cost Types', 'Tolls cost'),
        ('cost_type_parking', 'Parking', 'Text', 'Cost Types', 'Parking cost'),
        ('cost_type_loading', 'Loading/Unloading', 'Text', 'Cost Types', 'Loading/unloading cost'),
        ('cost_type_driver_allowance', 'Driver Allowance', 'Text', 'Cost Types', 'Driver allowance'),
        ('cost_type_overtime', 'Overtime', 'Text', 'Cost Types', 'Overtime cost'),
        ('cost_type_helper', 'Helper Cost', 'Text', 'Cost Types', 'Helper cost'),
        ('cost_type_maintenance', 'Maintenance', 'Text', 'Cost Types', 'Maintenance cost'),
        ('cost_type_carrier', 'Carrier Charges', 'Text', 'Cost Types', 'Carrier charges'),
        ('cost_type_customs', 'Customs/Clearance', 'Text', 'Cost Types', 'Customs clearance cost'),
        ('cost_type_insurance', 'Insurance', 'Text', 'Cost Types', 'Insurance cost'),
        ('cost_type_surcharge', 'Surcharge', 'Text', 'Cost Types', 'Surcharge'),
        ('cost_type_redelivery', 'Redelivery', 'Text', 'Cost Types', 'Redelivery cost'),
        ('cost_type_failed_delivery', 'Failed Delivery', 'Text', 'Cost Types', 'Failed delivery cost'),
        ('cost_type_return', 'Return Cost', 'Text', 'Cost Types', 'Return cost'),
        ('cost_type_demurrage', 'Demurrage', 'Text', 'Cost Types', 'Demurrage cost'),
        ('cost_type_misc', 'Miscellaneous', 'Text', 'Cost Types', 'Miscellaneous cost'),
        ('expense_type_fuel', 'Fuel', 'Text', 'Expense Types', 'Fuel expense'),
        ('expense_type_tolls', 'Tolls', 'Text', 'Expense Types', 'Tolls expense'),
        ('expense_type_parking', 'Parking', 'Text', 'Expense Types', 'Parking expense'),
        ('expense_type_meal', 'Meal', 'Text', 'Expense Types', 'Meal expense'),
        ('expense_type_accommodation', 'Accommodation', 'Text', 'Expense Types', 'Accommodation expense'),
        ('expense_type_misc', 'Miscellaneous', 'Text', 'Expense Types', 'Miscellaneous expense'),
        ('incident_type_delay', 'Delivery Delay', 'Text', 'Incident Types', 'Delivery delay incident'),
        ('incident_type_breakdown', 'Vehicle Breakdown', 'Text', 'Incident Types', 'Vehicle breakdown incident'),
        ('incident_type_driver_absence', 'Driver Absence', 'Text', 'Incident Types', 'Driver absence incident'),
        ('incident_type_customer_unavailable', 'Customer Unavailable', 'Text', 'Incident Types', 'Customer unavailable incident'),
        ('incident_type_wrong_address', 'Wrong Address', 'Text', 'Incident Types', 'Wrong address incident'),
        ('incident_type_damage', 'Shipment Damage', 'Text', 'Incident Types', 'Shipment damage incident'),
        ('incident_type_missing_item', 'Missing Item', 'Text', 'Incident Types', 'Missing item incident'),
        ('incident_type_shortage', 'Shortage', 'Text', 'Incident Types', 'Shortage incident'),
        ('incident_type_excess', 'Excess Delivery', 'Text', 'Incident Types', 'Excess delivery incident'),
        ('incident_type_accident', 'Accident', 'Text', 'Incident Types', 'Accident incident'),
        ('incident_type_traffic_fine', 'Traffic Fine', 'Text', 'Incident Types', 'Traffic fine incident'),
        ('incident_type_route_deviation', 'Route Deviation', 'Text', 'Incident Types', 'Route deviation incident'),
        ('incident_type_document_missing', 'Document Missing', 'Text', 'Incident Types', 'Document missing incident'),
        ('incident_type_failed_pickup', 'Failed Pickup', 'Text', 'Incident Types', 'Failed pickup incident'),
        ('incident_type_failed_delivery', 'Failed Delivery', 'Text', 'Incident Types', 'Failed delivery incident'),
        ('incident_type_quality_issue', 'Quality Issue in Transit', 'Text', 'Incident Types', 'Quality issue in transit'),
        ('incident_type_cold_chain', 'Cold Chain Violation', 'Text', 'Incident Types', 'Cold chain violation'),
        ('vehicle_type_van', 'Van', 'Text', 'Vehicle Types', 'Van'),
        ('vehicle_type_truck', 'Truck', 'Text', 'Vehicle Types', 'Truck'),
        ('vehicle_type_pickup', 'Pickup', 'Text', 'Vehicle Types', 'Pickup truck'),
        ('vehicle_type_trailer', 'Trailer', 'Text', 'Vehicle Types', 'Trailer'),
        ('vehicle_type_refrigerated', 'Refrigerated', 'Text', 'Vehicle Types', 'Refrigerated vehicle'),
        ('vehicle_type_tanker', 'Tanker', 'Text', 'Vehicle Types', 'Tanker'),
        ('vehicle_type_container', 'Container', 'Text', 'Vehicle Types', 'Container'),
        ('document_type_delivery_order', 'Delivery Order', 'Text', 'Document Types', 'Delivery order document'),
        ('document_type_dispatch_note', 'Dispatch Note', 'Text', 'Document Types', 'Dispatch note document'),
        ('document_type_shipment_manifest', 'Shipment Manifest', 'Text', 'Document Types', 'Shipment manifest document'),
        ('document_type_trip_sheet', 'Trip Sheet', 'Text', 'Document Types', 'Trip sheet document'),
        ('document_type_route_sheet', 'Route Sheet', 'Text', 'Document Types', 'Route sheet document'),
        ('document_type_pickup_form', 'Pickup Form', 'Text', 'Document Types', 'Pickup form document'),
        ('document_type_pod', 'Proof of Delivery', 'Text', 'Document Types', 'Proof of delivery document'),
        ('document_type_return_receipt', 'Return Receipt', 'Text', 'Document Types', 'Return receipt document'),
        ('document_type_incident_report', 'Incident Report', 'Text', 'Document Types', 'Incident report document'),
        ('default_currency', 'AED', 'Text', 'General', 'Default currency'),
        ('default_timezone', 'Asia/Dubai', 'Text', 'General', 'Default timezone'),
        ('date_format', 'DD/MM/YYYY', 'Text', 'General', 'Date format'),
        ('sla_same_day_hours', '8', 'Number', 'SLA', 'Same-day delivery SLA in hours'),
        ('sla_next_day_hours', '24', 'Number', 'SLA', 'Next-day delivery SLA in hours'),
        ('sla_standard_days', '3', 'Number', 'SLA', 'Standard delivery SLA in days'),
    ]

    for setting in default_settings:
        conn.execute("""
            INSERT OR IGNORE INTO logistics_settings
            (setting_key, setting_value, setting_type, category, description)
            VALUES (?, ?, ?, ?, ?)
        """, setting)

    conn.commit()


def get_logistics_setting(setting_key: str, default: str = None) -> str:
    """Get a specific logistics setting value."""
    conn = get_db()
    try:
        result = conn.execute(
            "SELECT setting_value FROM logistics_settings WHERE setting_key = ? AND is_active = 1",
            (setting_key,)
        ).fetchone()
        return result['setting_value'] if result else default
    finally:
        conn.close()


def update_logistics_setting(setting_key: str, value: str) -> bool:
    """Update a specific logistics setting value."""
    conn = get_db()
    try:
        conn.execute(
            "UPDATE logistics_settings SET setting_value = ?, updated_at = CURRENT_TIMESTAMP WHERE setting_key = ?",
            (value, setting_key)
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def log_logistics_audit(entity_type: str, entity_id: int, action: str, user_id: int,
                         field_name: str = None, old_value: str = None,
                         new_value: str = None, ip_address: str = None,
                         user_agent: str = None) -> int:
    """Log a logistics audit entry."""
    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO logistics_audit_logs
            (entity_type, entity_id, action, field_name, old_value, new_value,
             user_id, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (entity_type, entity_id, action, field_name, old_value, new_value,
              user_id, ip_address, user_agent))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


# =============================================================================
# HELPER FUNCTIONS FOR COMMON LOGISTICS OPERATIONS
# =============================================================================

def get_next_shipment_code():
    """Generate next shipment code."""
    conn = get_db()
    try:
        today = datetime.now().strftime('%Y%m%d')
        result = conn.execute(
            "SELECT shipment_code FROM logistics_shipments WHERE shipment_code LIKE ? ORDER BY id DESC LIMIT 1",
            (f'SHP{today}%',)
        ).fetchone()
        if result:
            last_num = int(result['shipment_code'].replace(f'SHP{today}', ''))
            return f"SHP{today}{(last_num + 1):04d}"
        return f"SHP{today}0001"
    finally:
        conn.close()


def get_next_do_number():
    """Generate next delivery order number."""
    conn = get_db()
    try:
        today = datetime.now().strftime('%Y%m%d')
        result = conn.execute(
            "SELECT do_number FROM logistics_delivery_orders WHERE do_number LIKE ? ORDER BY id DESC LIMIT 1",
            (f'DO{today}%',)
        ).fetchone()
        if result:
            last_num = int(result['do_number'].replace(f'DO{today}', ''))
            return f"DO{today}{(last_num + 1):04d}"
        return f"DO{today}0001"
    finally:
        conn.close()


def get_next_pickup_number():
    """Generate next pickup order number."""
    conn = get_db()
    try:
        today = datetime.now().strftime('%Y%m%d')
        result = conn.execute(
            "SELECT pickup_number FROM logistics_pickup_orders WHERE pickup_number LIKE ? ORDER BY id DESC LIMIT 1",
            (f'PU{today}%',)
        ).fetchone()
        if result:
            last_num = int(result['pickup_number'].replace(f'PU{today}', ''))
            return f"PU{today}{(last_num + 1):04d}"
        return f"PU{today}0001"
    finally:
        conn.close()


def get_next_incident_number():
    """Generate next incident number."""
    conn = get_db()
    try:
        year = datetime.now().year
        result = conn.execute(
            "SELECT incident_number FROM logistics_incidents WHERE incident_number LIKE ? ORDER BY id DESC LIMIT 1",
            (f'INC{year}%',)
        ).fetchone()
        if result:
            last_num = int(result['incident_number'].replace(f'INC{year}', ''))
            return f"INC{year}{(last_num + 1):04d}"
        return f"INC{year}0001"
    finally:
        conn.close()


def get_next_trip_code():
    """Generate next trip code."""
    conn = get_db()
    try:
        today = datetime.now().strftime('%Y%m%d')
        result = conn.execute(
            "SELECT trip_code FROM logistics_trips WHERE trip_code LIKE ? ORDER BY id DESC LIMIT 1",
            (f'TRP{today}%',)
        ).fetchone()
        if result:
            last_num = int(result['trip_code'].replace(f'TRP{today}', ''))
            return f"TRP{today}{(last_num + 1):04d}"
        return f"TRP{today}0001"
    finally:
        conn.close()


def get_next_route_code():
    """Generate next route code."""
    conn = get_db()
    try:
        today = datetime.now().strftime('%Y%m%d')
        result = conn.execute(
            "SELECT route_code FROM logistics_route_masters WHERE route_code LIKE ? ORDER BY id DESC LIMIT 1",
            (f'RTE{today}%',)
        ).fetchone()
        if result:
            last_num = int(result['route_code'].replace(f'RTE{today}', ''))
            return f"RTE{today}{(last_num + 1):04d}"
        return f"RTE{today}0001"
    finally:
        conn.close()


def get_trip_stats(status=None, date_from=None, date_to=None):
    """Get trip statistics."""
    conn = get_db()
    try:
        where = ["1=1"]
        params = []

        if status:
            where.append("status = ?")
            params.append(status)
        if date_from:
            where.append("date(planned_departure) >= ?")
            params.append(date_from)
        if date_to:
            where.append("date(planned_departure) <= ?")
            params.append(date_to)

        where_clause = " AND ".join(where)

        stats = {
            'total': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_trips WHERE {where_clause}", params).fetchone()['cnt'],
            'draft': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_trips WHERE {where_clause} AND status = 'draft'", params).fetchone()['cnt'],
            'planned': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_trips WHERE {where_clause} AND status = 'planned'", params).fetchone()['cnt'],
            'ready_for_dispatch': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_trips WHERE {where_clause} AND status = 'ready_for_dispatch'", params).fetchone()['cnt'],
            'dispatched': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_trips WHERE {where_clause} AND status = 'dispatched'", params).fetchone()['cnt'],
            'en_route': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_trips WHERE {where_clause} AND status = 'en_route'", params).fetchone()['cnt'],
            'arrived': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_trips WHERE {where_clause} AND status = 'arrived'", params).fetchone()['cnt'],
            'completed': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_trips WHERE {where_clause} AND status = 'completed'", params).fetchone()['cnt'],
            'partially_completed': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_trips WHERE {where_clause} AND status = 'partially_completed'", params).fetchone()['cnt'],
            'failed': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_trips WHERE {where_clause} AND status = 'failed'", params).fetchone()['cnt'],
            'cancelled': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_trips WHERE {where_clause} AND status = 'cancelled'", params).fetchone()['cnt'],
            'closed': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_trips WHERE {where_clause} AND status = 'closed'", params).fetchone()['cnt'],
        }
        return stats
    finally:
        conn.close()


def get_route_stats():
    """Get route statistics."""
    conn = get_db()
    try:
        return {
            'total': conn.execute("SELECT COUNT(*) as cnt FROM logistics_route_masters WHERE is_active = 1").fetchone()['cnt'],
            'delivery': conn.execute("SELECT COUNT(*) as cnt FROM logistics_route_masters WHERE is_active = 1 AND route_type = 'delivery'").fetchone()['cnt'],
            'pickup': conn.execute("SELECT COUNT(*) as cnt FROM logistics_route_masters WHERE is_active = 1 AND route_type = 'pickup'").fetchone()['cnt'],
            'transfer': conn.execute("SELECT COUNT(*) as cnt FROM logistics_route_masters WHERE is_active = 1 AND route_type = 'transfer'").fetchone()['cnt'],
            'return': conn.execute("SELECT COUNT(*) as cnt FROM logistics_route_masters WHERE is_active = 1 AND route_type = 'return'").fetchone()['cnt'],
        }
    finally:
        conn.close()


def get_stop_stats(status=None):
    """Get stop statistics."""
    conn = get_db()
    try:
        where = ["1=1"]
        params = []

        if status:
            where.append("status = ?")
            params.append(status)

        where_clause = " AND ".join(where)

        stats = {
            'total': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_trip_stops WHERE {where_clause}", params).fetchone()['cnt'],
            'pending': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_trip_stops WHERE {where_clause} AND status = 'pending'", params).fetchone()['cnt'],
            'arrived': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_trip_stops WHERE {where_clause} AND status = 'arrived'", params).fetchone()['cnt'],
            'completed': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_trip_stops WHERE {where_clause} AND status = 'completed'", params).fetchone()['cnt'],
            'failed': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_trip_stops WHERE {where_clause} AND status = 'failed'", params).fetchone()['cnt'],
            'skipped': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_trip_stops WHERE {where_clause} AND status = 'skipped'", params).fetchone()['cnt'],
        }
        return stats
    finally:
        conn.close()


def get_shipment_stats(company_id=None, date_from=None, date_to=None):
    """Get shipment statistics for dashboard."""
    conn = get_db()
    try:
        where = ["1=1"]
        params = []

        if company_id:
            where.append("s.company_id = ?")
            params.append(company_id)
        if date_from:
            where.append("date(s.created_at) >= ?")
            params.append(date_from)
        if date_to:
            where.append("date(s.created_at) <= ?")
            params.append(date_to)

        where_clause = " AND ".join(where)

        stats = {
            'total': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_shipments s WHERE {where_clause}", params).fetchone()['cnt'],
            'draft': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_shipments s WHERE {where_clause} AND s.status = 'draft'", params).fetchone()['cnt'],
            'created': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_shipments s WHERE {where_clause} AND s.status = 'created'", params).fetchone()['cnt'],
            'planned': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_shipments s WHERE {where_clause} AND s.status = 'planned'", params).fetchone()['cnt'],
            'scheduled': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_shipments s WHERE {where_clause} AND s.status = 'scheduled'", params).fetchone()['cnt'],
            'ready_dispatch': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_shipments s WHERE {where_clause} AND s.status = 'ready_dispatch'", params).fetchone()['cnt'],
            'assigned': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_shipments s WHERE {where_clause} AND s.status = 'assigned'", params).fetchone()['cnt'],
            'in_transit': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_shipments s WHERE {where_clause} AND s.status = 'in_transit'", params).fetchone()['cnt'],
            'delivered': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_shipments s WHERE {where_clause} AND s.status = 'delivered'", params).fetchone()['cnt'],
            'failed_delivery': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_shipments s WHERE {where_clause} AND s.status = 'failed_delivery'", params).fetchone()['cnt'],
            'returned': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_shipments s WHERE {where_clause} AND s.status = 'returned'", params).fetchone()['cnt'],
            'cancelled': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_shipments s WHERE {where_clause} AND s.status = 'cancelled'", params).fetchone()['cnt'],
        }

        # Calculate rates
        total_complete = stats['delivered'] + stats['failed_delivery'] + stats['returned']
        stats['delivery_success_rate'] = round((stats['delivered'] / total_complete * 100) if total_complete > 0 else 0, 1)
        stats['on_time_rate'] = round((stats['delivered'] / stats['total'] * 100) if stats['total'] > 0 else 0, 1)

        return stats
    finally:
        conn.close()


def get_driver_availability_stats():
    """Get driver availability statistics."""
    conn = get_db()
    try:
        return {
            'total': conn.execute("SELECT COUNT(*) as cnt FROM logistics_drivers WHERE status = 'active'").fetchone()['cnt'],
            'available': conn.execute("SELECT COUNT(*) as cnt FROM logistics_drivers WHERE status = 'active' AND availability = 'available'").fetchone()['cnt'],
            'on_trip': conn.execute("SELECT COUNT(*) as cnt FROM logistics_drivers WHERE status = 'active' AND availability = 'on_trip'").fetchone()['cnt'],
            'on_leave': conn.execute("SELECT COUNT(*) as cnt FROM logistics_drivers WHERE status = 'active' AND availability = 'on_leave'").fetchone()['cnt'],
            'unavailable': conn.execute("SELECT COUNT(*) as cnt FROM logistics_drivers WHERE status = 'active' AND availability = 'unavailable'").fetchone()['cnt'],
        }
    finally:
        conn.close()


def get_vehicle_availability_stats():
    """Get vehicle availability statistics."""
    conn = get_db()
    try:
        return {
            'total': conn.execute("SELECT COUNT(*) as cnt FROM logistics_vehicles WHERE status = 'active'").fetchone()['cnt'],
            'available': conn.execute("SELECT COUNT(*) as cnt FROM logistics_vehicles WHERE status = 'active' AND availability = 'available'").fetchone()['cnt'],
            'on_trip': conn.execute("SELECT COUNT(*) as cnt FROM logistics_vehicles WHERE status = 'active' AND availability = 'on_trip'").fetchone()['cnt'],
            'maintenance': conn.execute("SELECT COUNT(*) as cnt FROM logistics_vehicles WHERE status = 'active' AND availability = 'maintenance'").fetchone()['cnt'],
            'unavailable': conn.execute("SELECT COUNT(*) as cnt FROM logistics_vehicles WHERE status = 'active' AND availability = 'unavailable'").fetchone()['cnt'],
        }
    finally:
        conn.close()


def get_active_shipments_for_dispatch(warehouse_id=None, company_id=None):
    """Get shipments ready for dispatch planning."""
    conn = get_db()
    try:
        query = """
            SELECT s.*, c.name as customer_name
            FROM logistics_shipments s
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            WHERE s.status IN ('ready_dispatch', 'assigned')
        """
        params = []

        if warehouse_id:
            query += " AND s.warehouse_id = ?"
            params.append(warehouse_id)
        if company_id:
            query += " AND s.company_id = ?"
            params.append(company_id)

        query += " ORDER BY s.priority DESC, s.planned_date ASC"

        return [dict(r) for r in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def get_open_incidents_count():
    """Get count of open logistics incidents."""
    conn = get_db()
    try:
        return conn.execute("SELECT COUNT(*) as cnt FROM logistics_incidents WHERE status = 'open'").fetchone()['cnt']
    finally:
        conn.close()


def get_pod_pending_count():
    """Get count of PODs pending upload."""
    conn = get_db()
    try:
        return conn.execute("""
            SELECT COUNT(*) as cnt FROM logistics_shipments
            WHERE status IN ('delivered', 'partially_delivered')
            AND id NOT IN (SELECT shipment_id FROM logistics_pod_records WHERE shipment_id IS NOT NULL)
        """).fetchone()['cnt']
    finally:
        conn.close()


def get_next_schedule_code():
    """Generate next schedule code."""
    conn = get_db()
    try:
        today = datetime.now().strftime('%Y%m%d')
        result = conn.execute(
            "SELECT schedule_code FROM logistics_delivery_schedules WHERE schedule_code LIKE ? ORDER BY id DESC LIMIT 1",
            (f'SCH{today}%',)
        ).fetchone()
        if result:
            last_num = int(result['schedule_code'].replace(f'SCH{today}', ''))
            return f"SCH{today}{(last_num + 1):04d}"
        return f"SCH{today}0001"
    finally:
        conn.close()


def get_next_load_code():
    """Generate next load plan code."""
    conn = get_db()
    try:
        today = datetime.now().strftime('%Y%m%d')
        result = conn.execute(
            "SELECT load_code FROM logistics_load_plans WHERE load_code LIKE ? ORDER BY id DESC LIMIT 1",
            (f'LOAD{today}%',)
        ).fetchone()
        if result:
            last_num = int(result['load_code'].replace(f'LOAD{today}', ''))
            return f"LOAD{today}{(last_num + 1):04d}"
        return f"LOAD{today}0001"
    finally:
        conn.close()


def get_next_exception_code():
    """Generate next exception code."""
    conn = get_db()
    try:
        year = datetime.now().year
        result = conn.execute(
            "SELECT exception_code FROM logistics_schedule_exceptions WHERE exception_code LIKE ? ORDER BY id DESC LIMIT 1",
            (f'EXC{year}%',)
        ).fetchone()
        if result:
            last_num = int(result['exception_code'].replace(f'EXC{year}', ''))
            return f"EXC{year}{(last_num + 1):04d}"
        return f"EXC{year}0001"
    finally:
        conn.close()


def get_scheduling_stats(date_from=None, date_to=None):
    """Get scheduling statistics."""
    conn = get_db()
    try:
        where = ["1=1"]
        params = []

        if date_from:
            where.append("date(scheduled_date) >= ?")
            params.append(date_from)
        if date_to:
            where.append("date(scheduled_date) <= ?")
            params.append(date_to)

        where_clause = " AND ".join(where)

        stats = {
            'total': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_delivery_schedules s WHERE {where_clause}", params).fetchone()['cnt'],
            'scheduled': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_delivery_schedules s WHERE {where_clause} AND s.status = 'scheduled'", params).fetchone()['cnt'],
            'checked_in': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_delivery_schedules s WHERE {where_clause} AND s.status = 'checked_in'", params).fetchone()['cnt'],
            'completed': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_delivery_schedules s WHERE {where_clause} AND s.status = 'completed'", params).fetchone()['cnt'],
            'cancelled': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_delivery_schedules s WHERE {where_clause} AND s.status = 'cancelled'", params).fetchone()['cnt'],
            'rescheduled': conn.execute(f"SELECT COUNT(*) as cnt FROM logistics_delivery_schedules s WHERE {where_clause} AND s.is_rescheduled = 1", params).fetchone()['cnt'],
        }

        return stats
    finally:
        conn.close()


def get_load_planning_stats():
    """Get load planning statistics."""
    conn = get_db()
    try:
        today = datetime.now().date().strftime('%Y-%m-%d')
        return {
            'total_loads': conn.execute("SELECT COUNT(*) as cnt FROM logistics_load_plans").fetchone()['cnt'],
            'planned': conn.execute("SELECT COUNT(*) as cnt FROM logistics_load_plans WHERE status = 'planned'").fetchone()['cnt'],
            'assigned': conn.execute("SELECT COUNT(*) as cnt FROM logistics_load_plans WHERE status = 'assigned'").fetchone()['cnt'],
            'ready': conn.execute("SELECT COUNT(*) as cnt FROM logistics_load_plans WHERE status = 'ready'").fetchone()['cnt'],
            'dispatched': conn.execute("SELECT COUNT(*) as cnt FROM logistics_load_plans WHERE status = 'dispatched'").fetchone()['cnt'],
            'today_loads': conn.execute("SELECT COUNT(*) as cnt FROM logistics_load_plans WHERE load_date = ?", (today,)).fetchone()['cnt'],
        }
    finally:
        conn.close()


def check_load_capacity(load_plan_id):
    """Check vehicle capacity against load plan."""
    conn = get_db()
    try:
        # Get load plan details
        load = conn.execute("SELECT * FROM logistics_load_plans WHERE id = ?", (load_plan_id,)).fetchone()
        if not load:
            return {'error': 'Load plan not found'}

        # Get vehicle capacity
        vehicle = conn.execute("SELECT * FROM logistics_vehicles WHERE id = ?", (load['vehicle_id'],)).fetchone()
        if not vehicle:
            return {'error': 'Vehicle not assigned'}

        # Get load plan shipments totals
        totals = conn.execute("""
            SELECT 
                COALESCE(SUM(sl.weight), 0) as total_weight,
                COALESCE(SUM(sl.volume), 0) as total_volume,
                COALESCE(SUM(sl.pallets), 0) as total_pallets,
                COALESCE(SUM(sl.cartons), 0) as total_cartons,
                COUNT(*) as shipment_count
            FROM logistics_load_plan_shipments lps
            JOIN logistics_shipments s ON lps.shipment_id = s.id
            LEFT JOIN logistics_shipment_lines sl ON s.id = sl.shipment_id
            WHERE lps.load_plan_id = ?
        """, (load_plan_id,)).fetchone()

        weight_ok = totals['total_weight'] <= vehicle['load_capacity_kg'] if vehicle['load_capacity_kg'] else True
        volume_ok = totals['total_volume'] <= vehicle['load_capacity_volume'] if vehicle['load_capacity_volume'] else True
        pallets_ok = totals['total_pallets'] <= vehicle['pallet_capacity'] if vehicle['pallet_capacity'] else True

        return {
            'load_plan_id': load_plan_id,
            'vehicle_id': vehicle['id'],
            'vehicle_code': vehicle['vehicle_code'],
            'max_weight_kg': vehicle['load_capacity_kg'],
            'max_volume': vehicle['load_capacity_volume'],
            'max_pallets': vehicle['pallet_capacity'],
            'max_cartons': vehicle['carton_capacity'],
            'total_weight_kg': totals['total_weight'],
            'total_volume': totals['total_volume'],
            'total_pallets': totals['total_pallets'],
            'total_cartons': totals['total_cartons'],
            'shipment_count': totals['shipment_count'],
            'weight_ok': weight_ok,
            'volume_ok': volume_ok,
            'pallets_ok': pallets_ok,
            'capacity_ok': weight_ok and volume_ok and pallets_ok,
            'weight_utilization': round((totals['total_weight'] / vehicle['load_capacity_kg'] * 100) if vehicle['load_capacity_kg'] else 0, 1),
            'volume_utilization': round((totals['total_volume'] / vehicle['load_capacity_volume'] * 100) if vehicle['load_capacity_volume'] else 0, 1),
        }
    finally:
        conn.close()


if __name__ == '__main__':
    # Run migrations when executed directly
    success, message = run_logistics_migrations()
    print(message)
