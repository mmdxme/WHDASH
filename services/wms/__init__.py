"""
WMS Service Layer
=================
Business logic extracted from the monolithic wms_routes.py (7838 lines).

Sub-services:
- dashboard: Dashboard statistics & KPIs
- inventory: Stock management, movements, adjustments
- receiving: Inbound receipts, putaway
- picking: Picking, packing, dispatch
- transfers: Inter-warehouse/company transfers
- items: Item master CRUD
- warehouses: Warehouse & location management
- quality: Quality holds, inspections
- reports: Analytics, export
"""

from services.wms.dashboard_service import WMSDashboardService
from services.wms.inventory_service import WMSInventoryService
from services.wms.receiving_service import WMSReceivingService
from services.wms.picking_service import WMSPickingService
from services.wms.transfer_service import WMSTransferService
from services.wms.item_service import WMSItemService
from services.wms.warehouse_service import WMSWarehouseService
from services.wms.quality_service import WMSQualityService
from services.wms.helpers import (
    get_wms_permissions,
    scoped_warehouse_ids,
    ensure_warehouse_allowed,
    get_warehouse_filter,
    get_company_filter,
    generate_wms_code,
    log_wms_audit,
    create_wms_notification,
    validate_item_payload,
    get_stock_status_name,
    get_rotation_policy_name,
)

__all__ = [
    'WMSDashboardService',
    'WMSInventoryService',
    'WMSReceivingService',
    'WMSPickingService',
    'WMSTransferService',
    'WMSItemService',
    'WMSWarehouseService',
    'WMSQualityService',
]