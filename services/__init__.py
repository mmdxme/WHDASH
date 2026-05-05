"""Services Package
================
Centralized service layer for business logic and security.

Services:
- auth_service: Authentication and session management
- security_service: CSRF, headers, input validation
- logging_service: Centralized logging configuration
- base: BaseService class for all services
- wms: WMS (Warehouse Management) services - inventory, item, transfer
- scm: SCM (Supply Chain) services - demand, supply, replenishment, alerts
- flow: Flow/messaging services - messaging, channel, notification
- btp: BTP integration services - connector, integration, api_management
"""

from .auth_service import (
    AuthenticationService,
    LoginRateLimiter,
    get_rate_limiter,
    require_login,
    require_admin,
    require_stock_admin,
)

from .security_service import (
    CSRFProtectionService,
    SecurityHeadersService,
    InputSanitizer,
    PasswordValidator,
    FileUploadValidator,
)

from .logging_service import (
    setup_logging,
    log_request,
    log_response,
    log_error,
    log_audit_action,
    log_function_call,
    log_api_call,
    get_default_logger,
)

# WMS Services
from .wms import InventoryService, ItemService, TransferService

# SCM Services
from .scm import DemandService, SupplyService, ReplenishmentService, AlertsService

# Flow Services
from .flow import MessagingService, ChannelService, NotificationService

# BTP Services
from .btp import ConnectorService, IntegrationService, APIManagementService

__all__ = [
    # Auth service
    'AuthenticationService',
    'LoginRateLimiter',
    'get_rate_limiter',
    'require_login',
    'require_admin',
    'require_stock_admin',
    # Security service
    'CSRFProtectionService',
    'SecurityHeadersService',
    'InputSanitizer',
    'PasswordValidator',
    'FileUploadValidator',
    # Logging service
    'setup_logging',
    'log_request',
    'log_response',
    'log_error',
    'log_audit_action',
    'log_function_call',
    'log_api_call',
    'get_default_logger',
    # WMS services
    'InventoryService',
    'ItemService',
    'TransferService',
    # SCM services
    'DemandService',
    'SupplyService',
    'ReplenishmentService',
    'AlertsService',
    # Flow services
    'MessagingService',
    'ChannelService',
    'NotificationService',
    # BTP services
    'ConnectorService',
    'IntegrationService',
    'APIManagementService',
]