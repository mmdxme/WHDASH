"""
SDAD Panel Synchronization Module
Fetches stock data from SDAD Panel and syncs with local warehouse database.
"""

import sqlite3
import os
import re
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'warehouse.db')

# SDAD Panel Configuration
SDAD_PANEL_BASE_URL = "https://panel.sdadparts.com"
SDAD_API_ENDPOINT = "/api/stock"  # Adjust based on actual API


@dataclass
class SDADStockItem:
    """Represents a stock item from SDAD Panel."""
    product_code: str
    name: str
    sku: str
    category: str
    brand: str
    warehouse: str
    stock_location: str
    quantity: int
    min_stock: int
    max_stock: int
    initial_stock: int = 0
    unit: str = "pcs"
    last_updated: str = ""


class SDADSyncManager:
    """
    Manages synchronization between SDAD Panel and local warehouse database.
    Handles authentication, data fetching, and database updates.
    """

    def __init__(self, db_path: str = DATABASE):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self._credentials = self._load_credentials()

    def _load_credentials(self) -> Dict[str, str]:
        """Load SDAD Panel credentials from environment or config."""
        return {
            'base_url': os.environ.get('SDAD_PANEL_URL', SDAD_PANEL_BASE_URL),
            'api_token': os.environ.get('SDAD_API_TOKEN', ''),
            'username': os.environ.get('SDAD_USERNAME', ''),
            'password': os.environ.get('SDAD_PASSWORD', '')
        }

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def get_db(self):
        """Context manager for database operations."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    # ─── Database Schema Migration ───────────────────────────────────────────

    def ensure_sync_schema(self) -> None:
        """Ensure all sync-related tables and columns exist."""
        with self.get_db() as db:
            # Sync metadata table
            db.execute('''
                CREATE TABLE IF NOT EXISTS sdad_sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sync_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    items_synced INTEGER DEFAULT 0,
                    errors TEXT,
                    started_at TEXT,
                    completed_at TEXT
                )
            ''')

            # SDAD Products table
            db.execute('''
                CREATE TABLE IF NOT EXISTS sdad_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_code TEXT NOT NULL UNIQUE,
                    name TEXT,
                    sku TEXT,
                    category TEXT,
                    brand TEXT,
                    warehouse_name TEXT,
                    stock_location TEXT,
                    quantity INTEGER DEFAULT 0,
                    initial_stock INTEGER DEFAULT 0,
                    min_stock INTEGER DEFAULT 0,
                    max_stock INTEGER DEFAULT 0,
                    unit TEXT DEFAULT 'pcs',
                    local_part_id INTEGER,
                    last_synced_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (local_part_id) REFERENCES parts(id)
                )
            ''')

            # SDAD Warehouses table
            db.execute('''
                CREATE TABLE IF NOT EXISTS sdad_warehouses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    code TEXT,
                    location TEXT,
                    is_active INTEGER DEFAULT 1,
                    local_warehouse_id INTEGER,
                    last_synced_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (local_warehouse_id) REFERENCES warehouses(id)
                )
            ''')

            # SDAD Categories table
            db.execute('''
                CREATE TABLE IF NOT EXISTS sdad_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    parent_id INTEGER,
                    local_category_id INTEGER,
                    last_synced_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Add sync_status column to inventory if not exists
            try:
                db.execute("ALTER TABLE inventory ADD COLUMN sync_status TEXT DEFAULT 'pending'")
            except:
                pass

            try:
                db.execute("ALTER TABLE inventory ADD COLUMN sdad_product_code TEXT")
            except:
                pass

            try:
                db.execute("ALTER TABLE parts ADD COLUMN sdad_product_id INTEGER")
            except:
                pass

    # ─── Authentication ───────────────────────────────────────────────────────

    def authenticate(self) -> bool:
        """
        Authenticate with SDAD Panel.
        Returns True if authentication successful, False otherwise.
        """
        if not self._credentials.get('username') or not self._credentials.get('password'):
            print("No SDAD credentials configured. Please set SDAD_USERNAME and SDAD_PASSWORD environment variables.")
            return False

        try:
            response = self.session.post(
                f"{self._credentials['base_url']}/api/auth/login",
                json={
                    'username': self._credentials['username'],
                    'password': self._credentials['password']
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                self.session.headers.update({
                    'Authorization': f"Bearer {data.get('token', '')}"
                })
                return True
            else:
                print(f"Authentication failed: {response.status_code} - {response.text}")
                return False

        except requests.RequestException as e:
            print(f"Authentication error: {str(e)}")
            return False

    # ─── Data Fetching ───────────────────────────────────────────────────────

    def fetch_stock_data(self) -> List[SDADStockItem]:
        """
        Fetch stock data from SDAD Panel.
        Returns list of SDADStockItem objects.
        """
        if not self._credentials.get('api_token') and not self._credentials.get('username'):
            return self._get_demo_stock_data()

        try:
            response = self.session.get(
                f"{self._credentials['base_url']}/api/stock-management/products",
                params={'role': 'admin'},
                timeout=60
            )

            if response.status_code == 200:
                return self._parse_stock_response(response.json())
            else:
                print(f"Failed to fetch stock data: {response.status_code}")
                return self._get_demo_stock_data()

        except requests.RequestException as e:
            print(f"Error fetching stock data: {str(e)}")
            return self._get_demo_stock_data()

    def _parse_stock_response(self, data: Dict) -> List[SDADStockItem]:
        """Parse SDAD Panel API response into SDADStockItem objects."""
        items = []

        if isinstance(data, dict) and 'products' in data:
            products = data['products']
        elif isinstance(data, list):
            products = data
        else:
            products = []

        for product in products:
            item = SDADStockItem(
                product_code=product.get('product_code', product.get('code', '')),
                name=product.get('name', product.get('product_name', '')),
                sku=product.get('sku', product.get('product_code', '')),
                category=product.get('category', product.get('cat_name', '')),
                brand=product.get('brand', ''),
                warehouse=product.get('warehouse', product.get('warehouse_name', 'Peyvast')),
                stock_location=product.get('stock_location', ''),
                quantity=int(product.get('quantity', product.get('qty', 0))),
                initial_stock=int(product.get('initial_stock', product.get('quantity', 0))),
                min_stock=int(product.get('min_stock', product.get('min', 0))),
                max_stock=int(product.get('max_stock', product.get('max', 0))),
                unit=product.get('unit', 'pcs'),
                last_updated=product.get('updated_at', datetime.now().isoformat())
            )
            items.append(item)

        return items

    def _get_demo_stock_data(self) -> List[SDADStockItem]:
        """
        Return demo stock data for testing when API is unavailable.
        This simulates the SDAD Panel stock data structure.
        """
        return [
            SDADStockItem(
                product_code="BRK-001",
                name="Brake Pad Set - Front",
                sku="BRK-PAD-FRT",
                category="Brakes",
                brand="Brembo",
                warehouse="Peyvast",
                stock_location="A-01-01",
                quantity=150,
                initial_stock=200,
                min_stock=20,
                max_stock=500
            ),
            SDADStockItem(
                product_code="FLT-001",
                name="Oil Filter - Standard",
                sku="FLT-OIL-STD",
                category="Filters",
                brand="Mann",
                warehouse="Peyvast",
                stock_location="A-01-02",
                quantity=320,
                initial_stock=400,
                min_stock=50,
                max_stock=1000
            ),
            SDADStockItem(
                product_code="IGN-001",
                name="Spark Plug - Iridium",
                sku="IGN-SPG-IRI",
                category="Ignition",
                brand="NGK",
                warehouse="Peyvast",
                stock_location="B-02-01",
                quantity=85,
                initial_stock=100,
                min_stock=30,
                max_stock=300
            ),
            SDADStockItem(
                product_code="FLT-002",
                name="Air Filter - Panel Type",
                sku="FLT-AIR-PNL",
                category="Filters",
                brand="Mann",
                warehouse="Peyvast",
                stock_location="A-02-01",
                quantity=210,
                initial_stock=250,
                min_stock=40,
                max_stock=600
            ),
            SDADStockItem(
                product_code="ENG-001",
                name="Timing Belt Kit",
                sku="ENG-TBK-001",
                category="Engine",
                brand="Gates",
                warehouse="Peyvast",
                stock_location="C-01-01",
                quantity=45,
                initial_stock=60,
                min_stock=15,
                max_stock=150
            ),
            SDADStockItem(
                product_code="TRN-001",
                name="Clutch Set - Single Plate",
                sku="TRN-CLT-SGL",
                category="Transmission",
                brand="LuK",
                warehouse="Peyvast",
                stock_location="C-02-01",
                quantity=28,
                initial_stock=40,
                min_stock=10,
                max_stock=100
            ),
            SDADStockItem(
                product_code="ELT-001",
                name="Alternator - 90A",
                sku="ELT-ALT-90A",
                category="Electrical",
                brand="Bosch",
                warehouse="Peyvast",
                stock_location="D-01-01",
                quantity=15,
                initial_stock=25,
                min_stock=5,
                max_stock=50
            ),
            SDADStockItem(
                product_code="ELT-002",
                name="Starter Motor - 1.8kW",
                sku="ELT-STR-18K",
                category="Electrical",
                brand="Bosch",
                warehouse="Peyvast",
                stock_location="D-01-02",
                quantity=12,
                initial_stock=20,
                min_stock=5,
                max_stock=40
            ),
            SDADStockItem(
                product_code="SUS-001",
                name="Shock Absorber - Front Pair",
                sku="SUS-SAF-FRT",
                category="Suspension",
                brand="Monroe",
                warehouse="Peyvast",
                stock_location="E-01-01",
                quantity=65,
                initial_stock=80,
                min_stock=20,
                max_stock=200
            ),
            SDADStockItem(
                product_code="SUS-002",
                name="Control Arm - Lower Left",
                sku="SUS-CAL-LOW",
                category="Suspension",
                brand="TRW",
                warehouse="Peyvast",
                stock_location="E-02-01",
                quantity=38,
                initial_stock=50,
                min_stock=10,
                max_stock=100
            ),
            SDADStockItem(
                product_code="COL-001",
                name="Radiator - Aluminum",
                sku="COL-RAD-ALU",
                category="Cooling",
                brand="Denso",
                warehouse="Peyvast",
                stock_location="F-01-01",
                quantity=22,
                initial_stock=30,
                min_stock=8,
                max_stock=60
            ),
            SDADStockItem(
                product_code="COL-002",
                name="Water Pump - with Gasket",
                sku="COL-WPM-GSK",
                category="Cooling",
                brand="Gates",
                warehouse="Peyvast",
                stock_location="F-01-02",
                quantity=55,
                initial_stock=70,
                min_stock=15,
                max_stock=150
            ),
            SDADStockItem(
                product_code="ENG-002",
                name="Drive Belt - Serpentine",
                sku="ENG-DRV-SRP",
                category="Engine",
                brand="Gates",
                warehouse="Peyvast",
                stock_location="C-01-02",
                quantity=95,
                initial_stock=120,
                min_stock=25,
                max_stock=300
            ),
            SDADStockItem(
                product_code="FLS-001",
                name="Fuel Filter - In-Line",
                sku="FLS-FLT-INL",
                category="Fuel System",
                brand="Mann",
                warehouse="Peyvast",
                stock_location="G-01-01",
                quantity=130,
                initial_stock=150,
                min_stock=30,
                max_stock=400
            ),
            SDADStockItem(
                product_code="BRK-002",
                name="Brake Disc - Front Ventilated",
                sku="BRK-DSC-FVT",
                category="Brakes",
                brand="Brembo",
                warehouse="Peyvast",
                stock_location="A-01-03",
                quantity=72,
                initial_stock=90,
                min_stock=20,
                max_stock=200
            )
        ]

    # ─── Data Synchronization ─────────────────────────────────────────────────

    def sync_all(self, authenticate_first: bool = True) -> Dict[str, Any]:
        """
        Perform full synchronization with SDAD Panel.
        Returns sync statistics and status.
        """
        sync_id = self._create_sync_log("full_sync", "running")

        result = {
            'sync_id': sync_id,
            'success': False,
            'items_synced': 0,
            'warehouses_synced': 0,
            'categories_synced': 0,
            'errors': []
        }

        start_time = datetime.now().isoformat()

        try:
            # Step 1: Authenticate if needed
            if authenticate_first:
                if not self.authenticate():
                    result['errors'].append("Authentication failed")

            # Step 2: Fetch stock data
            stock_items = self.fetch_stock_data()
            result['items_synced'] = len(stock_items)

            # Step 3: Sync warehouses
            warehouses = self._extract_warehouses(stock_items)
            self._sync_warehouses(warehouses)
            result['warehouses_synced'] = len(warehouses)

            # Step 4: Sync categories
            categories = self._extract_categories(stock_items)
            self._sync_categories(categories)
            result['categories_synced'] = len(categories)

            # Step 5: Sync products and update local inventory
            self._sync_products(stock_items)
            self._sync_inventory(stock_items)

            result['success'] = True

        except Exception as e:
            result['errors'].append(str(e))

        finally:
            self._complete_sync_log(sync_id, result)

        return result

    def _extract_warehouses(self, items: List[SDADStockItem]) -> List[str]:
        """Extract unique warehouse names from stock items."""
        return list(set(item.warehouse for item in items))

    def _extract_categories(self, items: List[SDADStockItem]) -> List[str]:
        """Extract unique category names from stock items."""
        return list(set(item.category for item in items))

    def _sync_warehouses(self, warehouse_names: List[str]) -> None:
        """Sync warehouses from SDAD Panel to local database."""
        with self.get_db() as db:
            for name in warehouse_names:
                existing = db.execute(
                    "SELECT id FROM sdad_warehouses WHERE name = ?", (name,)
                ).fetchone()

                if existing:
                    db.execute('''
                        UPDATE sdad_warehouses
                        SET last_synced_at = ?, is_active = 1
                        WHERE name = ?
                    ''', (datetime.now().isoformat(), name))
                else:
                    db.execute('''
                        INSERT INTO sdad_warehouses (name, last_synced_at)
                        VALUES (?, ?)
                    ''', (name, datetime.now().isoformat()))

                # Also create in local warehouses table if not exists
                local_wh = db.execute(
                    "SELECT id FROM warehouses WHERE name = ?", (name,)
                ).fetchone()

                if not local_wh:
                    # Get default company
                    company = db.execute("SELECT id FROM companies LIMIT 1").fetchone()
                    if company:
                        db.execute(
                            "INSERT INTO warehouses (name, company_id) VALUES (?, ?)",
                            (name, company['id'])
                        )

    def _sync_categories(self, category_names: List[str]) -> None:
        """Sync categories from SDAD Panel to local database."""
        with self.get_db() as db:
            for name in category_names:
                existing = db.execute(
                    "SELECT id FROM sdad_categories WHERE name = ?", (name,)
                ).fetchone()

                if existing:
                    db.execute('''
                        UPDATE sdad_categories
                        SET last_synced_at = ?
                        WHERE name = ?
                    ''', (datetime.now().isoformat(), name))
                else:
                    db.execute('''
                        INSERT INTO sdad_categories (name, last_synced_at)
                        VALUES (?, ?)
                    ''', (name, datetime.now().isoformat()))

                # Also create in local categories table if not exists
                local_cat = db.execute(
                    "SELECT id FROM categories WHERE name = ?", (name,)
                ).fetchone()

                if not local_cat:
                    db.execute("INSERT INTO categories (name) VALUES (?)", (name,))

    def _sync_products(self, items: List[SDADStockItem]) -> None:
        """Sync products from SDAD Panel to local database."""
        with self.get_db() as db:
            for item in items:
                existing = db.execute(
                    "SELECT id FROM sdad_products WHERE product_code = ?",
                    (item.product_code,)
                ).fetchone()

                now = datetime.now().isoformat()

                if existing:
                    db.execute('''
                        UPDATE sdad_products
                        SET name = ?, sku = ?, category = ?, brand = ?,
                            warehouse_name = ?, stock_location = ?,
                            quantity = ?, initial_stock = ?,
                            min_stock = ?, max_stock = ?,
                            unit = ?, last_synced_at = ?, updated_at = ?
                        WHERE product_code = ?
                    ''', (
                        item.name, item.sku, item.category, item.brand,
                        item.warehouse, item.stock_location,
                        item.quantity, item.initial_stock,
                        item.min_stock, item.max_stock,
                        item.unit, now, now, item.product_code
                    ))
                else:
                    db.execute('''
                        INSERT INTO sdad_products
                        (product_code, name, sku, category, brand,
                         warehouse_name, stock_location,
                         quantity, initial_stock, min_stock, max_stock,
                         unit, last_synced_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        item.product_code, item.name, item.sku, item.category, item.brand,
                        item.warehouse, item.stock_location,
                        item.quantity, item.initial_stock, item.min_stock, item.max_stock,
                        item.unit, now
                    ))

                # Create or update local part
                local_part = db.execute(
                    "SELECT id FROM parts WHERE part_number = ?",
                    (item.product_code,)
                ).fetchone()

                if not local_part:
                    # Get category id
                    cat_row = db.execute(
                        "SELECT id FROM categories WHERE name = ?",
                        (item.category,)
                    ).fetchone()
                    cat_id = cat_row['id'] if cat_row else None

                    db.execute('''
                        INSERT INTO parts (part_number, description, category_id, reorder_point, cost_price)
                        VALUES (?, ?, ?, ?, 0.00)
                    ''', (item.product_code, item.name, cat_id, item.min_stock))

                    # Get the inserted part id and link to sdad_product
                    part_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
                    db.execute('''
                        UPDATE sdad_products SET local_part_id = ?
                        WHERE product_code = ?
                    ''', (part_id, item.product_code))
                else:
                    # Update existing part
                    cat_row = db.execute(
                        "SELECT id FROM categories WHERE name = ?",
                        (item.category,)
                    ).fetchone()
                    cat_id = cat_row['id'] if cat_row else None

                    db.execute('''
                        UPDATE parts SET description = ?, category_id = ?, reorder_point = ?
                        WHERE part_number = ?
                    ''', (item.name, cat_id, item.min_stock, item.product_code))

    def _sync_inventory(self, items: List[SDADStockItem]) -> None:
        """Sync inventory quantities from SDAD Panel to local database."""
        with self.get_db() as db:
            # Get the Peyvast warehouse or first warehouse
            wh_row = db.execute(
                "SELECT id FROM warehouses WHERE name LIKE '%Peyvast%' LIMIT 1"
            ).fetchone()
            warehouse_id = wh_row['id'] if wh_row else 1

            # Get default company
            company_row = db.execute("SELECT id FROM companies LIMIT 1").fetchone()
            company_id = company_row['id'] if company_row else 1

            for item in items:
                part_row = db.execute(
                    "SELECT id FROM parts WHERE part_number = ?",
                    (item.product_code,)
                ).fetchone()

                if part_row:
                    part_id = part_row['id']

                    # Check if inventory record exists
                    inv_row = db.execute('''
                        SELECT id FROM inventory
                        WHERE part_id = ? AND company_id = ?
                    ''', (part_id, company_id)).fetchone()

                    if inv_row:
                        # Update quantity
                        db.execute('''
                            UPDATE inventory
                            SET quantity = ?, warehouse_id = ?, sync_status = 'synced',
                                sdad_product_code = ?, updated_at = ?
                            WHERE part_id = ? AND company_id = ?
                        ''', (
                            item.quantity, warehouse_id, item.product_code,
                            datetime.now().isoformat(), part_id, company_id
                        ))
                    else:
                        # Create new inventory record
                        db.execute('''
                            INSERT INTO inventory
                            (part_id, company_id, warehouse_id, quantity, sync_status, sdad_product_code)
                            VALUES (?, ?, ?, ?, 'synced', ?)
                        ''', (part_id, company_id, warehouse_id, item.quantity, item.product_code))

    # ─── Sync Log ────────────────────────────────────────────────────────────

    def _create_sync_log(self, sync_type: str, status: str) -> int:
        """Create a sync log entry and return its ID."""
        with self.get_db() as db:
            db.execute('''
                INSERT INTO sdad_sync_log (sync_type, status, started_at)
                VALUES (?, ?, ?)
            ''', (sync_type, status, datetime.now().isoformat()))
            return db.execute("SELECT last_insert_rowid()").fetchone()[0]

    def _complete_sync_log(self, sync_id: int, result: Dict) -> None:
        """Update sync log with completion status."""
        with self.get_db() as db:
            errors_json = json.dumps(result['errors']) if result['errors'] else None
            db.execute('''
                UPDATE sdad_sync_log
                SET status = ?, items_synced = ?, errors = ?, completed_at = ?
                WHERE id = ?
            ''', (
                'completed' if result['success'] else 'failed',
                result['items_synced'],
                errors_json,
                datetime.now().isoformat(),
                sync_id
            ))

    def get_sync_status(self) -> List[Dict]:
        """Get recent sync log entries."""
        with self.get_db() as db:
            rows = db.execute('''
                SELECT * FROM sdad_sync_log
                ORDER BY started_at DESC
                LIMIT 10
            ''').fetchall()
            return [dict(row) for row in rows]

    # ─── Data Retrieval ──────────────────────────────────────────────────────

    def get_all_products(self) -> List[Dict]:
        """Get all synced products with local inventory data."""
        with self.get_db() as db:
            rows = db.execute('''
                SELECT
                    sp.id, sp.product_code, sp.name, sp.sku, sp.category, sp.brand,
                    sp.warehouse_name, sp.stock_location,
                    sp.quantity, sp.initial_stock, sp.min_stock, sp.max_stock,
                    sp.unit, sp.last_synced_at,
                    p.id as part_id, p.part_number, p.description,
                    i.quantity as local_qty, i.warehouse_id
                FROM sdad_products sp
                LEFT JOIN parts p ON sp.local_part_id = p.id
                LEFT JOIN inventory i ON p.id = i.part_id
                ORDER BY sp.category, sp.name
            ''').fetchall()
            return [dict(row) for row in rows]

    def get_low_stock_items(self, threshold: int = None) -> List[Dict]:
        """Get items that are below minimum stock level."""
        with self.get_db() as db:
            if threshold is not None:
                rows = db.execute('''
                    SELECT * FROM sdad_products
                    WHERE quantity <= min_stock
                    AND quantity > 0
                    ORDER BY (min_stock - quantity) DESC
                ''').fetchall()
            else:
                rows = db.execute('''
                    SELECT * FROM sdad_products
                    WHERE quantity < min_stock
                    ORDER BY (min_stock - quantity) DESC
                ''').fetchall()
            return [dict(row) for row in rows]

    def get_out_of_stock_items(self) -> List[Dict]:
        """Get items that are out of stock."""
        with self.get_db() as db:
            rows = db.execute('''
                SELECT * FROM sdad_products
                WHERE quantity = 0
                ORDER BY category, name
            ''').fetchall()
            return [dict(row) for row in rows]

    def get_stock_by_warehouse(self, warehouse_name: str = None) -> List[Dict]:
        """Get stock items grouped by warehouse."""
        with self.get_db() as db:
            if warehouse_name:
                rows = db.execute('''
                    SELECT * FROM sdad_products
                    WHERE warehouse_name = ?
                    ORDER BY category, name
                ''', (warehouse_name,)).fetchall()
            else:
                rows = db.execute('''
                    SELECT * FROM sdad_products
                    ORDER BY warehouse_name, category, name
                ''').fetchall()
            return [dict(row) for row in rows]

    def get_warehouses(self) -> List[Dict]:
        """Get all synced warehouses."""
        with self.get_db() as db:
            rows = db.execute('''
                SELECT w.*, sw.local_warehouse_id
                FROM sdad_warehouses w
                LEFT JOIN warehouses sw ON w.name = sw.name
                WHERE w.is_active = 1
                ORDER BY w.name
            ''').fetchall()
            return [dict(row) for row in rows]

    def get_categories(self) -> List[Dict]:
        """Get all synced categories."""
        with self.get_db() as db:
            rows = db.execute('''
                SELECT * FROM sdad_categories
                ORDER BY name
            ''').fetchall()
            return [dict(row) for row in rows]

    def get_stock_summary(self) -> Dict:
        """Get stock summary statistics."""
        with self.get_db() as db:
            total = db.execute("SELECT COUNT(*) as cnt FROM sdad_products").fetchone()['cnt']
            total_qty = db.execute("SELECT COALESCE(SUM(quantity), 0) as total FROM sdad_products").fetchone()['total']
            low_stock = db.execute(
                "SELECT COUNT(*) as cnt FROM sdad_products WHERE quantity <= min_stock AND quantity > 0"
            ).fetchone()['cnt']
            out_of_stock = db.execute(
                "SELECT COUNT(*) as cnt FROM sdad_products WHERE quantity = 0"
            ).fetchone()['cnt']
            over_stock = db.execute(
                "SELECT COUNT(*) as cnt FROM sdad_products WHERE quantity >= max_stock"
            ).fetchone()['cnt']

            warehouses = db.execute(
                "SELECT COUNT(*) as cnt FROM sdad_warehouses WHERE is_active = 1"
            ).fetchone()['cnt']

            categories = db.execute(
                "SELECT COUNT(*) as cnt FROM sdad_categories"
            ).fetchone()['cnt']

            return {
                'total_products': total,
                'total_warehouse_quantity': total_qty,
                'low_stock': low_stock,
                'out_of_stock': out_of_stock,
                'over_stock': over_stock,
                'warehouses': warehouses,
                'categories': categories
            }


# ─── Standalone Functions ────────────────────────────────────────────────────

def run_sync() -> Dict[str, Any]:
    """Run full sync with SDAD Panel."""
    manager = SDADSyncManager()
    manager.ensure_sync_schema()
    return manager.sync_all()


if __name__ == "__main__":
    print("Starting SDAD Panel sync...")
    result = run_sync()
    print(f"Sync completed: {result}")
