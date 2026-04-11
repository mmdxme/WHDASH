"""
Cross-Module Integration Framework
===================================
Provides integration points between modules.

This framework ensures:
- Inventory reservations when sales orders are created
- Finance entries traceable to source transactions
- Maintenance parts reduce inventory
- Quality holds block inventory movement
- Asset depreciation links to finance

Usage:
    from integration import (
        reserve_inventory_for_order,
        create_finance_entry,
        link_document_to_transaction
    )
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from database import get_db_context, log_audit


# =============================================================================
# INVENTORY-SALES INTEGRATION
# =============================================================================

def reserve_inventory_for_order(order_id: int, order_type: str = 'sales',
                                 created_by: int = None) -> Dict[str, Any]:
    """
    Reserve inventory when a sales order is confirmed.
    
    Args:
        order_id: The sales order ID
        order_type: Type of order (sales, transfer, etc.)
        created_by: User ID making the reservation
    
    Returns:
        Dict with reservation results
    """
    with get_db_context() as db:
        # Get order lines
        lines = db.execute("""
            SELECT id, item_id, quantity_ordered, warehouse_id
            FROM sales_order_lines
            WHERE order_id = ?
        """, (order_id,)).fetchall()
        
        if not lines:
            return {'success': False, 'message': 'No order lines found', 'reservations': []}
        
        reservations = []
        errors = []
        
        for line in lines:
            item_id = line['item_id']
            qty = line['quantity_ordered']
            warehouse_id = line['warehouse_id'] or 1
            
            # Check available stock
            available = db.execute("""
                SELECT COALESCE(SUM(quantity), 0) as available
                FROM wms_inventory_balances
                WHERE item_id = ? AND warehouse_id = ?
            """, (item_id, warehouse_id)).fetchone()['available']
            
            if available >= qty:
                # Create reservation
                db.execute("""
                    INSERT INTO inventory_reservations (
                        item_id, warehouse_id, reference_type, reference_id,
                        quantity, status, created_by, created_at
                    ) VALUES (?, ?, ?, ?, ?, 'confirmed', ?, ?)
                """, (item_id, warehouse_id, order_type, order_id, qty, created_by, datetime.now().isoformat()))
                
                # Reduce available inventory
                db.execute("""
                    UPDATE wms_inventory_balances
                    SET quantity = quantity - ?
                    WHERE item_id = ? AND warehouse_id = ?
                """, (qty, item_id, warehouse_id))
                
                reservations.append({
                    'item_id': item_id,
                    'quantity': qty,
                    'warehouse_id': warehouse_id
                })
            else:
                errors.append({
                    'item_id': item_id,
                    'requested': qty,
                    'available': available
                })
        
        db.commit()
        
        # Log the reservation
        log_audit('inventory_reservation', order_id, 'CREATE', created_by,
                  notes=f"Reserved inventory for {order_type} order {order_id}")
        
        return {
            'success': len(errors) == 0,
            'message': f"Reserved {len(reservations)} items" if not errors else f"Partial reservation: {len(errors)} items unavailable",
            'reservations': reservations,
            'errors': errors
        }


def release_inventory_reservation(reservation_id: int, released_by: int = None) -> bool:
    """
    Release an inventory reservation (e.g., when order is canceled).
    """
    with get_db_context() as db:
        # Get reservation details
        res = db.execute("""
            SELECT item_id, warehouse_id, quantity, status
            FROM inventory_reservations
            WHERE id = ?
        """, (reservation_id,)).fetchone()
        
        if not res:
            return False
        
        if res['status'] != 'confirmed':
            return False
        
        # Restore inventory
        db.execute("""
            UPDATE wms_inventory_balances
            SET quantity = quantity + ?
            WHERE item_id = ? AND warehouse_id = ?
        """, (res['quantity'], res['item_id'], res['warehouse_id']))
        
        # Update reservation status
        db.execute("""
            UPDATE inventory_reservations
            SET status = 'released', released_at = ?, released_by = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), released_by, reservation_id))
        
        db.commit()
        
        log_audit('inventory_reservation', reservation_id, 'RELEASE', released_by,
                   notes=f"Released reservation {reservation_id}")
        
        return True


def get_item_inventory_summary(item_id: int) -> Dict[str, Any]:
    """
    Get complete inventory summary for an item across all warehouses.
    Includes available, reserved, and on-order quantities.
    """
    with get_db_context() as db:
        # Physical stock
        physical = db.execute("""
            SELECT warehouse_id, SUM(quantity) as qty
            FROM wms_inventory_balances
            WHERE item_id = ?
            GROUP BY warehouse_id
        """, (item_id,)).fetchall()
        
        # Reserved
        reserved = db.execute("""
            SELECT warehouse_id, SUM(quantity) as qty
            FROM inventory_reservations
            WHERE item_id = ? AND status = 'confirmed'
            GROUP BY warehouse_id
        """, (item_id,)).fetchall()
        
        # On order (purchase orders)
        on_order = db.execute("""
            SELECT pol.expected_stock, pol.warehouse_id, pol.quantity_ordered
            FROM purchase_order_lines pol
            JOIN purchase_orders po ON pol.order_id = po.id
            WHERE pol.item_id = ? AND po.status IN ('Sent', 'Confirmed', 'Partially Received')
        """, (item_id,)).fetchall()
        
        return {
            'item_id': item_id,
            'by_warehouse': {
                row['warehouse_id']: {
                    'physical': row['qty'],
                    'reserved': next((r['qty'] for r in reserved if r['warehouse_id'] == row['warehouse_id']), 0),
                    'on_order': next((o['quantity_ordered'] for o in on_order if o['warehouse_id'] == row['warehouse_id']), 0)
                }
                for row in physical
            }
        }


# =============================================================================
# FINANCE-SOURCE TRANSACTION INTEGRATION
# =============================================================================

def create_finance_entry(entry_type: str, entry_data: Dict[str, Any],
                         source_module: str, source_id: int,
                         created_by: int = None) -> Optional[int]:
    """
    Create a finance journal entry with source transaction tracking.
    
    Args:
        entry_type: 'ar_invoice', 'ap_bill', 'payment', 'journal', etc.
        entry_data: Dict with entry details (amount, account_id, description, etc.)
        source_module: Module that created this entry (sales, procurement, maintenance, etc.)
        source_id: ID of the source transaction
        created_by: User creating the entry
    
    Returns:
        Journal entry ID if successful, None otherwise
    """
    with get_db_context() as db:
        # Generate entry number
        entry_num = db.execute("""
            SELECT COALESCE(MAX(CAST(journal_number AS INTEGER)), 0) + 1 as next_num
            FROM finance_journals
        """).fetchone()['next_num']
        
        journal_number = f"JRN-{entry_num:06d}"
        
        # Create journal header
        cursor = db.execute("""
            INSERT INTO finance_journals (
                journal_number, journal_type, reference, description,
                journal_date, period_id, company_id,
                is_posted, is_reversed, source_module, source_id,
                created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?, ?, ?)
        """, (
            journal_number,
            entry_data.get('journal_type', 'Standard'),
            entry_data.get('reference', f"{source_module}.{source_id}"),
            entry_data.get('description', ''),
            entry_data.get('journal_date', datetime.now().strftime('%Y-%m-%d')),
            entry_data.get('period_id'),
            entry_data.get('company_id'),
            source_module,
            source_id,
            created_by,
            datetime.now().isoformat()
        ))
        
        journal_id = cursor.lastrowid
        
        # Create journal lines
        lines = entry_data.get('lines', [])
        for i, line in enumerate(lines):
            db.execute("""
                INSERT INTO finance_journal_lines (
                    journal_id, line_number, account_id, description,
                    debit_amount, credit_amount, cost_center_id,
                    created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                journal_id,
                i + 1,
                line['account_id'],
                line.get('description', ''),
                line.get('debit', 0),
                line.get('credit', 0),
                line.get('cost_center_id'),
                created_by,
                datetime.now().isoformat()
            ))
        
        db.commit()
        
        # Audit log
        log_audit('finance_journal', journal_id, 'CREATE', created_by,
                  notes=f"Created from {source_module}:{source_id}")
        
        return journal_id


def get_source_transaction(module: str, transaction_id: int) -> Optional[Dict[str, Any]]:
    """
    Get the source transaction details for any module.
    Used to trace where finance entries came from.
    """
    with get_db_context() as db:
        if module == 'sales':
            return db.execute("SELECT * FROM sales_orders WHERE id = ?",
                             (transaction_id,)).fetchone()
        elif module == 'procurement':
            return db.execute("SELECT * FROM purchase_orders WHERE id = ?",
                             (transaction_id,)).fetchone()
        elif module == 'maintenance':
            return db.execute("SELECT * FROM maintenance_work_orders WHERE id = ?",
                             (transaction_id,)).fetchone()
        elif module == 'asset':
            return db.execute("SELECT * FROM assets WHERE id = ?",
                             (transaction_id,)).fetchone()
        return None


# =============================================================================
# MAINTENANCE-INVENTORY INTEGRATION
# =============================================================================

def consume_inventory_for_maintenance(work_order_id: int, work_log_id: int = None,
                                       consumed_by: int = None) -> Dict[str, Any]:
    """
    Create inventory consumption record when maintenance uses parts.
    This reduces actual inventory and records the cost.
    """
    with get_db_context() as db:
        # Get parts usage records
        parts = db.execute("""
            SELECT mu.*, mu.quantity_used as qty
            FROM maintenance_parts_usage mu
            WHERE mu.work_order_id = ? AND mu.status = 'Issued'
        """, (work_order_id,)).fetchall()
        
        if not parts:
            return {'success': True, 'message': 'No parts to consume', 'consumptions': []}
        
        consumptions = []
        
        for part in parts:
            part_id = part['part_id']
            qty = part['quantity_used']
            warehouse_id = part['warehouse_id']
            unit_cost = part['unit_cost']
            
            # Reduce inventory
            rows = db.execute("""
                UPDATE wms_inventory_balances
                SET quantity = quantity - ?
                WHERE item_id = ? AND warehouse_id = ?
                RETURNING id
            """, (qty, part_id, warehouse_id)).fetchall()
            
            if rows:
                # Record consumption transaction
                db.execute("""
                    INSERT INTO inventory_transactions (
                        item_id, warehouse_id, transaction_type, reference_type,
                        reference_id, quantity, unit_cost, total_cost,
                        notes, created_by, created_at
                    ) VALUES (?, ?, 'Maintenance Issue', 'work_order', ?, ?, ?, ?, ?, ?, ?)
                """, (
                    part_id, warehouse_id, work_order_id,
                    qty, unit_cost, qty * unit_cost,
                    f"Used in work order {work_order_id}",
                    consumed_by, datetime.now().isoformat()
                ))
                
                consumptions.append({
                    'part_id': part_id,
                    'quantity': qty,
                    'warehouse_id': warehouse_id,
                    'cost': qty * unit_cost
                })
        
        # Update parts usage status
        db.execute("""
            UPDATE maintenance_parts_usage
            SET status = 'Consumed'
            WHERE work_order_id = ?
        """, (work_order_id,))
        
        db.commit()
        
        return {
            'success': True,
            'message': f"Consumed {len(consumptions)} parts",
            'consumptions': consumptions
        }


# =============================================================================
# QUALITY-INVENTORY INTEGRATION
# =============================================================================

def check_quality_hold(item_id: int, warehouse_id: int, quantity: int = None) -> bool:
    """
    Check if an item is on quality hold and cannot be used/shipped.
    Returns True if item is blocked by quality hold.
    """
    with get_db_context() as db:
        # Check for active quality holds on this item
        hold = db.execute("""
            SELECT id FROM quality_non_conformances
            WHERE item_id = ?
            AND status IN ('Open', 'In Review')
            LIMIT 1
        """, (item_id,)).fetchone()
        
        if hold:
            return True
        
        # Check if item is in quarantine zone
        if quantity:
            quarantine = db.execute("""
                SELECT COALESCE(SUM(quarantine_quantity), 0) as qty
                FROM quality_quarantine
                WHERE item_id = ? AND warehouse_id = ?
            """, (item_id, warehouse_id)).fetchone()['qty']
            
            return quarantine >= quantity
        
        return False


def place_item_on_quarantine(item_id: int, warehouse_id: int,
                               quantity: int, reason: str,
                               placed_by: int = None) -> int:
    """
    Place an item into quarantine (quality hold).
    Returns the quarantine record ID.
    """
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO quality_quarantine (
                item_id, warehouse_id, quarantine_quantity, reason,
                status, placed_by, placed_at
            ) VALUES (?, ?, ?, ?, 'On Hold', ?, ?)
        """, (item_id, warehouse_id, quantity, reason, placed_by, datetime.now().isoformat()))
        
        db.commit()
        
        log_audit('quality_quarantine', cursor.lastrowid, 'CREATE', placed_by,
                  notes=f"Item {item_id} placed on quarantine: {reason}")
        
        return cursor.lastrowid


# =============================================================================
# ASSET-FINANCE INTEGRATION
# =============================================================================

def create_asset_depreciation_entry(asset_id: int, depreciation_run_id: int,
                                    period_id: int, created_by: int = None) -> Optional[int]:
    """
    Create finance journal entries for asset depreciation.
    Links the depreciation entry to the asset and run.
    """
    with get_db_context() as db:
        # Get asset and depreciation details
        asset = db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if not asset:
            return None
        
        run = db.execute("""
            SELECT * FROM depreciation_runs WHERE id = ?
        """, (depreciation_run_id,)).fetchone()
        
        if not run:
            return None
        
        # Get depreciation expense account from asset category
        category = db.execute("""
            SELECT depreciation_expense_account FROM asset_categories WHERE id = ?
        """, (asset['category_id'],)).fetchone()
        
        expense_account = category['depreciation_expense_account'] if category else '6100'
        asset_account = asset.get('asset_account', '1500')  # Fixed asset account
        
        # Create journal entry
        return create_finance_entry('depreciation', {
            'journal_type': 'Depreciation',
            'reference': f"DEP-{asset['asset_code']}-{run['run_date'][:7]}",
            'description': f"Depreciation for {asset['name']}",
            'journal_date': run['run_date'],
            'period_id': period_id,
            'company_id': asset['company_id'],
            'lines': [
                {
                    'account_id': expense_account,
                    'description': f"Depreciation expense - {asset['name']}",
                    'debit': run['depreciation_amount'],
                    'credit': 0
                },
                {
                    'account_id': asset_account,
                    'description': f"Accumulated depreciation - {asset['name']}",
                    'debit': 0,
                    'credit': run['depreciation_amount']
                }
            ]
        }, source_module='asset', source_id=asset_id, created_by=created_by)


# =============================================================================
# DOCUMENT LINKING
# =============================================================================

def link_document_to_transaction(document_id: int, module: str, record_id: int,
                                  link_type: str = 'Related', created_by: int = None) -> int:
    """
    Link a document to any business transaction across modules.
    """
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO document_links (
                document_id, linked_module, linked_record_id, link_type,
                is_primary, created_by_user_id, created_at
            ) VALUES (?, ?, ?, ?, 0, ?, ?)
        """, (document_id, module, record_id, link_type, created_by, datetime.now().isoformat()))
        
        db.commit()
        
        log_audit('document_link', cursor.lastrowid, 'CREATE', created_by,
                  notes=f"Linked document {document_id} to {module}:{record_id}")
        
        return cursor.lastrowid


def get_linked_transactions(document_id: int) -> List[Dict[str, Any]]:
    """
    Get all transactions linked to a document.
    """
    with get_db_context() as db:
        links = db.execute("""
            SELECT dl.*, dl.link_type as connection_type,
                   dl.linked_module as module, dl.linked_record_id as record_id
            FROM document_links dl
            WHERE dl.document_id = ?
        """, (document_id,)).fetchall()
        
        transactions = []
        for link in links:
            source = get_source_transaction(link['module'], link['record_id'])
            if source:
                transactions.append({
                    'link_id': link['id'],
                    'module': link['module'],
                    'record_id': link['record_id'],
                    'record': dict(source)
                })
        
        return transactions


# =============================================================================
# STATUS SYNCHRONIZATION
# =============================================================================

def sync_order_status_to_inventory(order_id: int, new_status: str) -> None:
    """
    Update inventory reservations when sales order status changes.
    """
    with get_db_context() as db:
        if new_status in ('Canceled', 'Returned'):
            # Release all reservations
            reservations = db.execute("""
                SELECT id, item_id, warehouse_id, quantity
                FROM inventory_reservations
                WHERE reference_type = 'sales' AND reference_id = ?
                AND status = 'confirmed'
            """, (order_id,)).fetchall()
            
            for res in reservations:
                db.execute("""
                    UPDATE wms_inventory_balances
                    SET quantity = quantity + ?
                    WHERE item_id = ? AND warehouse_id = ?
                """, (res['quantity'], res['item_id'], res['warehouse_id']))
                
                db.execute("""
                    UPDATE inventory_reservations
                    SET status = 'released', released_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), res['id']))
            
            db.commit()
            
        elif new_status in ('Shipped', 'Delivered'):
            # Convert reservations to actual consumption
            db.execute("""
                UPDATE inventory_reservations
                SET status = 'fulfilled'
                WHERE reference_type = 'sales' AND reference_id = ?
                AND status = 'confirmed'
            """, (order_id,))
            
            db.commit()


# =============================================================================
# AUDIT TRAIL HELPERS
# =============================================================================

def get_transaction_audit_trail(module: str, record_id: int) -> List[Dict[str, Any]]:
    """
    Get complete audit trail for a transaction across all modules.
    """
    with get_db_context() as db:
        # Get document links
        docs = db.execute("""
            SELECT document_id FROM document_links
            WHERE linked_module = ? AND linked_record_id = ?
        """, (module, record_id)).fetchall()
        
        trail = []
        
        # Add document audit
        for doc in docs:
            doc_logs = db.execute("""
                SELECT dal.*, d.title as document_title
                FROM document_access_logs dal
                JOIN documents d ON dal.document_id = d.id
                WHERE dal.document_id = ?
                ORDER BY dal.created_at DESC
            """, (doc['document_id'],)).fetchall()
            
            for log in doc_logs:
                trail.append({
                    'timestamp': log['created_at'],
                    'action': log['access_action'],
                    'module': 'document',
                    'record_id': doc['document_id'],
                    'user_id': log['user_id'],
                    'details': log
                })
        
        # Add finance audit
        finance = db.execute("""
            SELECT * FROM finance_journals
            WHERE source_module = ? AND source_id = ?
        """, (module, record_id)).fetchall()
        
        for entry in finance:
            trail.append({
                'timestamp': entry['created_at'],
                'action': 'finance_entry',
                'module': 'finance',
                'record_id': entry['id'],
                'details': entry
            })
        
        # Sort by timestamp
        trail.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return trail
