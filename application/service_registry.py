"""
Service Registry
================
Centralized management of service instances for dependency injection.
This allows controllers to access business logic without direct SQL coupling.
"""

from database import get_db

# WMS Services
from services.wms.dashboard_service import WMSDashboardService
from services.wms.inventory_service import WMSInventoryService
from services.wms.receiving_service import WMSReceivingService
from services.wms.picking_service import WMSPickingService
from services.wms.transfer_service import WMSTransferService
from services.wms.item_service import WMSItemService
from services.wms.warehouse_service import WMSWarehouseService
from services.wms.quality_service import WMSQualityService

# HR Services
from services.hr.employee_service import HREmployeeService
from services.hr.attendance_service import HRAttendanceService
from services.hr.leave_service import HRLeaveService
from services.hr.recruitment_service import HRRecruitmentService
from services.hr.training_service import HRTrainingService
from services.hr.reports_service import HRReportsService

# Logistics Services
from services.logistics.fleet_service import LogisticsFleetService
from services.logistics.driver_service import LogisticsDriverService
from services.logistics.trip_service import LogisticsTripService
from services.logistics.dispatch_service import LogisticsDispatchService
from services.logistics.cost_service import LogisticsCostService

# Document Services
from services.document.document_service import DocumentService

class ServiceRegistry:
    """Registry for all business services."""
    
    def __init__(self, get_db_func):
        self.get_db = get_db_func
        
        # Initialize WMS Services
        self.wms_dashboard = WMSDashboardService(self.get_db)
        self.wms_inventory = WMSInventoryService(self.get_db)
        self.wms_receiving = WMSReceivingService(self.get_db)
        self.wms_picking = WMSPickingService(self.get_db)
        self.wms_transfer = WMSTransferService(self.get_db)
        self.wms_item = WMSItemService(self.get_db)
        self.wms_warehouse = WMSWarehouseService(self.get_db)
        self.wms_quality = WMSQualityService(self.get_db)
        
        # Initialize HR Services
        self.hr_employee = HREmployeeService(self.get_db)
        self.hr_attendance = HRAttendanceService(self.get_db)
        self.hr_leave = HRLeaveService(self.get_db)
        self.hr_recruitment = HRRecruitmentService(self.get_db)
        self.hr_training = HRTrainingService(self.get_db)
        self.hr_reports = HRReportsService(self.get_db)
        
        # Initialize Logistics Services
        self.logistics_fleet = LogisticsFleetService(self.get_db)
        self.logistics_driver = LogisticsDriverService(self.get_db)
        self.logistics_trip = LogisticsTripService(self.get_db)
        self.logistics_dispatch = LogisticsDispatchService(self.get_db)
        self.logistics_cost = LogisticsCostService(self.get_db)
        
        # Initialize Document Services
        self.document = DocumentService(self.get_db)

# Global registry instance
services = ServiceRegistry(get_db)
