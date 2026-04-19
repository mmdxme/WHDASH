"""
SAP ERP Integration Adapter for WMS
Supports SAP RFC/BAPI and IDoc communication
"""

import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# SAP Connection Configuration
SAP_CONFIG = {
    'ashost': 'sap.example.com',
    'sysnr': '00',
    'client': '100',
    'user': 'WMS_USER',
    'passwd': '',
    'lang': 'EN'
}


class SAPAdapter:
    """
    SAP ERP Adapter for WMS integration.
    Handles RFC/BAPI calls and IDoc processing.
    """

    def __init__(self, config: Dict = None):
        """Initialize SAP adapter with configuration."""
        self.config = config or SAP_CONFIG
        self.connected = False
        self.client = None

    def connect(self) -> bool:
        """
        Establish connection to SAP system.
        In production, this uses pyrfc or sapnwrfc.
        """
        try:
            # In production, uncomment below:
            # from pyrfc import Connection
            # self.client = Connection(**self.config)
            # self.connected = True

            # Simulation for development
            logger.info("SAP connection established (simulation mode)")
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"SAP connection failed: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Close SAP connection."""
        if self.client:
            try:
                self.client.close()
            except:
                pass
        self.connected = False

    def test_connection(self) -> Dict:
        """Test SAP connection and return status."""
        try:
            if self.connect():
                # In production: self.client.ping()
                return {
                    'success': True,
                    'message': 'SAP connection successful',
                    'system': self.config.get('ashost'),
                    'client': self.config.get('client')
                }
            return {'success': False, 'message': 'Connection failed'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    # =====================================================================
    # IDOC CREATION - WMS to SAP
    # =====================================================================

    def create_despatch_advice(self, receipt_data: Dict) -> Optional[str]:
        """
        Create DESADV IDoc for goods receipt.
        Maps WMS receipt to SAP Goods Receipt IDoc.

        Args:
            receipt_data: {
                'receipt_number': str,
                'po_number': str,
                'delivery_date': str,
                'items': [
                    {'item_code': str, 'quantity': float, 'unit': str, 'lot': str}
                ]
            }

        Returns:
            IDoc number if successful, None otherwise
        """
        if not self.connected:
            self.connect()

        try:
            idoc_data = {
                'IDOCHDR': {
                    'DOCNUM': '',  # System generates
                    'DIRECT': 2,  # Outbound
                    'IDOCTYP': 'DESADV01',
                    'MESTYP': 'DESADV',
                    'SNDPOR': 'WMS',
                    'SNDPRT': 'LS',
                    'SNDPRN': 'WMS001',
                    'RCVPOR': 'SAP',
                    'RCVPRT': 'LS',
                    'RCVPRN': self.config.get('client'),
                },
                'IDOCCTRL': {
                    'SEGNAM': 'E1EDK01',
                    'DOCNUM': '',
                },
                'E1EDK01': {
                    'ACTION': '000',  # New
                    'BSART': 'EL',  # Delivery
                    'LIFEX': receipt_data.get('receipt_number'),  # External ID
                    'BEDAT': receipt_data.get('delivery_date', datetime.now().strftime('%Y%m%d')),
                },
                'E1EDK02': [{
                    'QUALF': '001',  # Purchase Order
                    'BELNR': receipt_data.get('po_number'),
                    'DATUM': datetime.now().strftime('%Y%m%d'),
                }],
                'E1EDP01': []
            }

            # Add line items
            for idx, item in enumerate(receipt_data.get('items', [])):
                line = {
                    'POSEX': str(idx + 1).zfill(6),
                    'MENGE': str(item.get('quantity', 0)),
                    'MENEE': item.get('unit', 'EA'),
                    'ARTIK': item.get('item_code'),
                    'MATNR': item.get('item_code'),
                }
                if item.get('lot'):
                    line['CHARG'] = item.get('lot')  # Batch/Lot
                idoc_data['E1EDP01'].append(line)

            # In production: result = self.client.call('IDOC_INBOUND_ASYNCHRONOUS', idoc_data)
            idoc_number = f"D{datetime.now().strftime('%Y%m%d%H%M%S')}"

            logger.info(f"DESADV IDoc created: {idoc_number}")
            return idoc_number

        except Exception as e:
            logger.error(f"DESADV creation failed: {e}")
            return None

    def create_receiving_advice(self, receipt_data: Dict) -> Optional[str]:
        """
        Create RECADV IDoc for receiving confirmation.
        """
        if not self.connected:
            self.connect()

        try:
            idoc_data = {
                'IDOCHDR': {
                    'IDOCTYP': 'RECADV01',
                    'MESTYP': 'RECADV',
                },
                'E1EDK01': {
                    'LIFEX': receipt_data.get('receipt_number'),
                    'ACTION': '000',
                },
                'E1EDP01': []
            }

            for idx, item in enumerate(receipt_data.get('items', [])):
                line = {
                    'POSEX': str(idx + 1).zfill(6),
                    'MENGE': str(item.get('received_quantity', item.get('quantity', 0))),
                    'MENEE': item.get('unit', 'EA'),
                    'MATNR': item.get('item_code'),
                }
                if item.get('lot'):
                    line['CHARG'] = item.get('lot')
                idoc_data['E1EDP01'].append(line)

            # In production: result = self.client.call('IDOC_INBOUND_ASYNCHRONOUS', idoc_data)
            idoc_number = f"R{datetime.now().strftime('%Y%m%d%H%M%S')}"

            logger.info(f"RECADV IDoc created: {idoc_number}")
            return idoc_number

        except Exception as e:
            logger.error(f"RECADV creation failed: {e}")
            return None

    def create_invoice_idoc(self, invoice_data: Dict) -> Optional[str]:
        """
        Create INVOIC IDoc for billing.
        """
        if not self.connected:
            self.connect()

        try:
            idoc_data = {
                'IDOCHDR': {
                    'IDOCTYP': 'INVOIC01',
                    'MESTYP': 'INVOIC',
                },
                'E1EDK01': {
                    'ACTION': '000',
                    'WRBTR': str(invoice_data.get('amount', 0)),
                    'WAERS': invoice_data.get('currency', 'USD'),
                    'LIFEX': invoice_data.get('invoice_number'),
                },
                'E1EDK02': [{
                    'QUALF': '001',
                    'BELNR': invoice_data.get('po_number'),
                }],
                'E1EDP01': []
            }

            for idx, item in enumerate(invoice_data.get('items', [])):
                line = {
                    'POSEX': str(idx + 1).zfill(6),
                    'MATNR': item.get('item_code'),
                    'MENGE': str(item.get('quantity', 0)),
                    'TBTWR': str(item.get('amount', 0)),
                }
                idoc_data['E1EDP01'].append(line)

            # In production: result = self.client.call('IDOC_INBOUND_ASYNCHRONOUS', idoc_data)
            idoc_number = f"I{datetime.now().strftime('%Y%m%d%H%M%S')}"

            logger.info(f"INVOIC IDoc created: {idoc_number}")
            return idoc_number

        except Exception as e:
            logger.error(f"INVOIC creation failed: {e}")
            return None

    # =====================================================================
    # IDOC PROCESSING - SAP to WMS
    # =====================================================================

    def process_inbound_idoc(self, idoc_content: Dict) -> Dict:
        """
        Process inbound IDoc from SAP and convert to WMS transaction.

        Args:
            idoc_content: Parsed IDoc data from SAP

        Returns:
            Dict with processed transaction data for WMS
        """
        try:
            message_type = idoc_content.get('MESTYP', '')

            if message_type == 'ORDERS':
                return self._process_purchase_order(idoc_content)
            elif message_type == 'DELVRY':
                return self._process_delivery(idoc_content)
            elif message_type == 'ORDSP':
                return self._process_order_response(idoc_content)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                return {'error': f'Unknown message type: {message_type}'}

        except Exception as e:
            logger.error(f"IDoc processing failed: {e}")
            return {'error': str(e)}

    def _process_purchase_order(self, idoc_content: Dict) -> Dict:
        """Process ORDERS (Purchase Order) IDoc."""
        header = idoc_content.get('E1EDK01', {})
        lines = idoc_content.get('E1EDP01', [])

        po_data = {
            'po_number': '',
            'vendor_id': '',
            'vendor_name': '',
            'items': []
        }

        # Extract PO number
        for edi_k02 in idoc_content.get('E1EDK02', []):
            if edi_k02.get('QUALF') == '001':
                po_data['po_number'] = edi_k02.get('BELNR', '')

        # Extract vendor
        po_data['vendor_id'] = idoc_content.get('E1EDKA1', {}).get('LIFNR', '')
        po_data['vendor_name'] = idoc_content.get('E1EDKA1', {}).get('NAME1', '')

        # Extract items
        for line in lines:
            item = {
                'item_code': line.get('MATNR', ''),
                'description': line.get('ARKTX', ''),
                'quantity': float(line.get('MENGE', 0)),
                'unit': line.get('MENEE', 'EA'),
                'unit_price': float(line.get('CMPRE', 0)),
            }
            po_data['items'].append(item)

        logger.info(f"Processed PO {po_data['po_number']} with {len(po_data['items'])} items")
        return {'type': 'PURCHASE_ORDER', 'data': po_data}

    def _process_delivery(self, idoc_content: Dict) -> Dict:
        """Process DELVRY (Delivery) IDoc."""
        header = idoc_content.get('E1EDK01', {})
        lines = idoc_content.get('E1EDP01', [])

        delivery_data = {
            'delivery_number': '',
            'po_number': '',
            'items': []
        }

        delivery_data['delivery_number'] = header.get('LIFEX', '')

        # Extract references
        for edi_k02 in idoc_content.get('E1EDK02', []):
            if edi_k02.get('QUALF') == '001':
                delivery_data['po_number'] = edi_k02.get('BELNR', '')

        # Extract items
        for line in lines:
            item = {
                'item_code': line.get('MATNR', ''),
                'quantity': float(line.get('MENGE', 0)),
                'unit': line.get('MENEE', 'EA'),
                'batch': line.get('CHARG', ''),
            }
            delivery_data['items'].append(item)

        logger.info(f"Processed Delivery {delivery_data['delivery_number']}")
        return {'type': 'DELIVERY', 'data': delivery_data}

    def _process_order_response(self, idoc_content: Dict) -> Dict:
        """Process ORDRSP (Order Response) IDoc."""
        header = idoc_content.get('E1EDK01', {})
        lines = idoc_content.get('E1EDP01', [])

        response_data = {
            'po_number': '',
            'confirmation_number': '',
            'items': []
        }

        response_data['confirmation_number'] = header.get('LIFEX', '')

        for edi_k02 in idoc_content.get('E1EDK02', []):
            if edi_k02.get('QUALF') == '001':
                response_data['po_number'] = edi_k02.get('BELNR', '')

        for line in lines:
            item = {
                'item_code': line.get('MATNR', ''),
                'confirmed_quantity': float(line.get('MENGE', 0)),
                'confirmed_date': line.get('LFDAT', ''),
            }
            response_data['items'].append(item)

        return {'type': 'ORDER_RESPONSE', 'data': response_data}

    # =====================================================================
    # BAPI CALLS
    # =====================================================================

    def call_bapi_goods_receipt(self, receipt_data: Dict) -> Dict:
        """
        Call SAP BAPI for goods receipt posting.
        Uses BAPI_GOODS_RECEIPT_CREATE.
        """
        if not self.connected:
            self.connect()

        try:
            # In production:
            # result = self.client.call('BAPI_GOODS_RECEIPT_CREATE', receipt_data)

            # Simulation
            return {
                'success': True,
                'document_number': f'GR{datetime.now().strftime("%Y%m%d%H%M%S")}',
                'message': 'Goods receipt posted successfully'
            }

        except Exception as e:
            logger.error(f"BAPI Goods Receipt failed: {e}")
            return {'success': False, 'error': str(e)}

    def call_bapi_inventory_posting(self, posting_data: Dict) -> Dict:
        """
        Call SAP BAPI for inventory posting.
        Uses BAPI_GOODS_STOCK_POSTING_RECIPE or MB1C.
        """
        if not self.connected:
            self.connect()

        try:
            # In production:
            # result = self.client.call('BAPI_GOODS_STOCK_POSTING_RECIPE', posting_data)

            return {
                'success': True,
                'document_number': f'INV{datetime.now().strftime("%Y%m%d%H%M%S")}',
                'message': 'Inventory posting successful'
            }

        except Exception as e:
            logger.error(f"BAPI Inventory Posting failed: {e}")
            return {'success': False, 'error': str(e)}

    # =====================================================================
    # SYNCHRONIZATION
    # =====================================================================

    def sync_material_master(self, item_code: str) -> Optional[Dict]:
        """
        Fetch material master data from SAP for WMS item.
        """
        if not self.connected:
            self.connect()

        try:
            # In production:
            # result = self.client.call('BAPI_MATERIAL_GET_DETAIL', {'MATNR': item_code})

            # Simulation
            return {
                'item_code': item_code,
                'description': 'Material from SAP',
                'unit': 'EA',
                'material_type': 'FERT',
                'valuation_class': '9200',
            }

        except Exception as e:
            logger.error(f"Material sync failed for {item_code}: {e}")
            return None

    def sync_vendor_master(self, vendor_id: str) -> Optional[Dict]:
        """
        Fetch vendor master data from SAP.
        """
        if not self.connected:
            self.connect()

        try:
            # In production:
            # result = self.client.call('BAPI_VENDOR_GETDETAIL', {'VENDORNO': vendor_id})

            return {
                'vendor_id': vendor_id,
                'name': 'Vendor from SAP',
                'address': 'SAP Address',
            }

        except Exception as e:
            logger.error(f"Vendor sync failed for {vendor_id}: {e}")
            return None

    # =====================================================================
    # ERROR HANDLING
    # =====================================================================

    def get_idoc_status(self, idoc_number: str) -> Optional[Dict]:
        """
        Get status of an IDoc in SAP.
        """
        if not self.connected:
            self.connect()

        try:
            # In production:
            # result = self.client.call('STATUS_READ', {'IDOCNUMBER': idoc_number})

            return {
                'idoc_number': idoc_number,
                'status': 'Sent',
                'timestamp': datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Status check failed for {idoc_number}: {e}")
            return None

    def resend_idoc(self, idoc_number: str) -> bool:
        """
        Resend a failed IDoc to SAP.
        """
        if not self.connected:
            self.connect()

        try:
            # In production:
            # result = self.client.call('IDOC_RESEND', {'IDOC_NUMBER': idoc_number})

            logger.info(f"IDoc {idoc_number} resent successfully")
            return True

        except Exception as e:
            logger.error(f"IDoc resend failed for {idoc_number}: {e}")
            return False


# Singleton instance
_sap_adapter = None


def get_sap_adapter(config: Dict = None) -> SAPAdapter:
    """Get singleton SAP adapter instance."""
    global _sap_adapter
    if _sap_adapter is None:
        _sap_adapter = SAPAdapter(config)
    return _sap_adapter
