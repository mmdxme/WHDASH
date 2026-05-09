"""
Logistics Service Layer
======================
Business logic extracted from the monolithic logistics_routes.py (426 KB).

Sub-services:
- fleet_service: Vehicle management, maintenance, fuel
- driver_service: Driver records, licensing, availability
- trip_service: Trip planning, scheduling, routing
- dispatch_service: Dispatching, tracking, delivery
- cost_service: Fuel costs, maintenance expenses, toll/salik
"""

from services.logistics.fleet_service import LogisticsFleetService
from services.logistics.driver_service import LogisticsDriverService
from services.logistics.trip_service import LogisticsTripService
from services.logistics.dispatch_service import LogisticsDispatchService
from services.logistics.cost_service import LogisticsCostService

__all__ = [
    'LogisticsFleetService',
    'LogisticsDriverService',
    'LogisticsTripService',
    'LogisticsDispatchService',
    'LogisticsCostService',
]
