"""
Peyvast Stock Management Synchronization Module
Fetches stock data from Peyvast/SDAD Panel and syncs with local warehouse database.

Source: https://panel.sdadparts.com/dashboard/peyvast?page=database%2Fstock-management&role=admin

Business Mapping Rules:
- Barcode = Part Number (canonical key for all inventory/reporting logic)
- Product Name = Description
- Current Stock = current stock available in warehouse
- Warehouse = warehouse name
- Brand = item brand
"""

import sqlite3
import os
import re
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from contextlib import contextmanager
import time
import logging

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'warehouse.db')

# Configuration - loaded from environment variables
PEYVAST_BASE_URL = os.environ.get('PEYVAST_BASE_URL', 'https://panel.sdadparts.com')
PEYVAST_USERNAME = os.environ.get('PEYVAST_USERNAME', '')
PEYVAST_PASSWORD = os.environ.get('PEYVAST_PASSWORD', '')

# Request timeout
REQUEST_TIMEOUT = 60
MAX_RETRIES = 3
RETRY_DELAY = 5

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PeyvastStockItem:
    """
    Represents a stock item from Peyvast/SDAD Panel.
    All fields are mapped according to business rules:
    - Barcode = Part Number (canonical key)
    - Product Name = Description
    """
    # Primary key (Barcode = Part Number)
    part_number: str = ""
    barcode: str = ""

    # Product identification
    product_code: str = ""
    description: str = ""
    product_name: str = ""

    # Categorization
    category: str = ""
    brand: str = ""
    warehouse_name: str = ""

    # Stock information
    current_stock: int = 0
    initial_stock: int = 0
    min_stock: int = 0
    max_stock: int = 0
    stock_location: str = ""

    # Purchase information
    last_purchase_price: float = 0.0
    last_purchase_qty: int = 0
    last_purchase_date: str = ""
    avg_unit_cost: float = 0.0
    seller_invoice_details: str = ""

    # Metadata
    source_system: str = "peyvast"
    source_record_id: str = ""
    last_synced_at: str = ""
    raw_payload: str = ""

    def __post_init__(self):
        """Normalize part_number and barcode to be the same (canonical key)."""
        if self.part_number and not self.barcode:
            self.barcode = self.part_number
        elif self.barcode and not self.part_number:
            self.part_number = self.barcode
        elif self.part_number and self.barcode:
            # Both provided - use part_number as canonical, keep barcode in sync
            pass

    def to_dict(self) -> Dict:
        """Convert to dictionary for database operations."""
        return asdict(self)

    @classmethod
    def from_api_response(cls, data: Dict) -> 'PeyvastStockItem':
        """Parse API response into PeyvastStockItem."""
        # Map source columns to our normalized schema
        # Source: #, Product Code, Barcode, Product Name, Current Stock, Warehouse, Brand,
        #         Last Purchase Price, Last Purchase Qty, Last Purchase Date, Avg Unit Cost, Seller & Invoice Details

        part_number = data.get('part_number', '') or data.get('barcode', '') or data.get('Product Code', '') or ''
        barcode = data.get('barcode', '') or data.get('Barcode', '') or part_number

        return cls(
            part_number=str(part_number).strip(),
            barcode=str(barcode).strip(),
            product_code=str(data.get('product_code', '') or data.get('Product Code', '') or '').strip(),
            description=str(data.get('description', '') or data.get('Product Name', '') or data.get('name', '') or '').strip(),
            product_name=str(data.get('product_name', '') or data.get('Product Name', '') or data.get('name', '') or '').strip(),

            category=str(data.get('category', '') or data.get('Category', '') or '').strip(),
            brand=str(data.get('brand', '') or data.get('Brand', '') or '').strip(),
            warehouse_name=str(data.get('warehouse_name', '') or data.get('Warehouse', '') or data.get('warehouse', '') or 'Peyvast').strip(),

            current_stock=int(data.get('current_stock', 0) or data.get('Current Stock', 0) or data.get('quantity', 0) or 0),
            initial_stock=int(data.get('initial_stock', 0) or data.get('Initial Stock', 0) or 0),
            min_stock=int(data.get('min_stock', 0) or data.get('Min Stock', 0) or data.get('min', 0) or 0),
            max_stock=int(data.get('max_stock', 0) or data.get('Max Stock', 0) or data.get('max', 0) or 0),
            stock_location=str(data.get('stock_location', '') or data.get('Stock Location', '') or data.get('location', '') or '').strip(),

            last_purchase_price=float(data.get('last_purchase_price', 0) or data.get('Last Purchase Price', 0) or 0),
            last_purchase_qty=int(data.get('last_purchase_qty', 0) or data.get('Last Purchase Qty', 0) or 0),
            last_purchase_date=str(data.get('last_purchase_date', '') or data.get('Last Purchase Date', '') or '').strip(),
            avg_unit_cost=float(data.get('avg_unit_cost', 0) or data.get('Avg Unit Cost', 0) or 0),
            seller_invoice_details=str(data.get('seller_invoice_details', '') or data.get('Seller & Invoice Details', '') or '').strip(),

            source_system='peyvast',
            source_record_id=str(data.get('id', '') or data.get('record_id', '') or '').strip(),
            last_synced_at=datetime.now().isoformat(),
            raw_payload=json.dumps(data, ensure_ascii=False)
        )


class PeyvastSyncManager:
    """
    Manages synchronization between Peyvast/SDAD Panel and local warehouse database.
    Handles authentication, data fetching, and database updates.

    Uses Part Number (Barcode) as the canonical key for all inventory and reporting logic.
    """

    def __init__(self, db_path: str = DATABASE):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        self._auth_token = None
        self._csrf_token = None
        self._last_sync_time = None
        self._sync_stats = {
            'total': 0,
            'synced': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0
        }

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def get_db(self):
        """Context manager for database operations with automatic commit/rollback."""
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
        """
        Ensure all sync-related tables and columns exist.
        Creates the normalized stock data schema based on Part Number as canonical key.
        """
        with self.get_db() as db:
            # Peyvast Products table - normalized schema
            db.execute('''
                CREATE TABLE IF NOT EXISTS peyvast_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    part_number TEXT NOT NULL UNIQUE,
                    barcode TEXT NOT NULL,
                    product_code TEXT,
                    description TEXT,
                    product_name TEXT,
                    category TEXT,
                    brand TEXT,
                    warehouse_name TEXT,
                    stock_location TEXT,
                    current_stock INTEGER DEFAULT 0,
                    initial_stock INTEGER DEFAULT 0,
                    min_stock INTEGER DEFAULT 0,
                    max_stock INTEGER DEFAULT 0,
                    last_purchase_price REAL DEFAULT 0,
                    last_purchase_qty INTEGER DEFAULT 0,
                    last_purchase_date TEXT,
                    avg_unit_cost REAL DEFAULT 0,
                    seller_invoice_details TEXT,
                    source_system TEXT DEFAULT 'peyvast',
                    source_record_id TEXT,
                    last_synced_at TEXT,
                    raw_payload TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create index on part_number for fast lookups
            db.execute('CREATE INDEX IF NOT EXISTS idx_peyvast_part_number ON peyvast_products(part_number)')
            db.execute('CREATE INDEX IF NOT EXISTS idx_peyvast_barcode ON peyvast_products(barcode)')
            db.execute('CREATE INDEX IF NOT EXISTS idx_peyvast_warehouse ON peyvast_products(warehouse_name)')
            db.execute('CREATE INDEX IF NOT EXISTS idx_peyvast_brand ON peyvast_products(brand)')

            # Sync metadata table
            db.execute('''
                CREATE TABLE IF NOT EXISTS peyvast_sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sync_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    items_total INTEGER DEFAULT 0,
                    items_synced INTEGER DEFAULT 0,
                    items_updated INTEGER DEFAULT 0,
                    items_failed INTEGER DEFAULT 0,
                    errors TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    duration_seconds REAL
                )
            ''')

            # Create index on sync log
            db.execute('CREATE INDEX IF NOT EXISTS idx_sync_log_started ON peyvast_sync_log(started_at DESC)')

            # Warehouses table for sync
            db.execute('''
                CREATE TABLE IF NOT EXISTS peyvast_warehouses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    code TEXT,
                    location TEXT,
                    is_active INTEGER DEFAULT 1,
                    last_synced_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Categories table for sync
            db.execute('''
                CREATE TABLE IF NOT EXISTS peyvast_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    parent_id INTEGER,
                    last_synced_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Sync settings table for background sync configuration
            db.execute('''
                CREATE TABLE IF NOT EXISTS peyvast_sync_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL UNIQUE,
                    value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Add columns to local inventory table if not exists
            for col, default in [
                ('peyvast_part_number', 'TEXT'),
                ('last_purchase_price', 'REAL DEFAULT 0'),
                ('last_purchase_qty', 'INTEGER DEFAULT 0'),
                ('last_purchase_date', 'TEXT'),
                ('avg_unit_cost', 'REAL DEFAULT 0'),
                ('seller_invoice_details', 'TEXT')
            ]:
                try:
                    db.execute(f"ALTER TABLE inventory ADD COLUMN {col} {default}")
                except:
                    pass

            # Add peyvast_part_number to parts table if not exists
            try:
                db.execute("ALTER TABLE parts ADD COLUMN peyvast_part_number TEXT")
            except:
                pass

    # ─── Authentication ───────────────────────────────────────────────────────

    def authenticate(self) -> bool:
        """
        Authenticate with Peyvast/SDAD Panel.
        Returns True if authentication successful, False otherwise.

        Uses Laravel Sanctum CSRF token flow:
        1. Load main page to set initial cookies
        2. Get CSRF token from /sanctum/csrf-cookie
        3. POST login data with X-XSRF-TOKEN header
        """
        if not PEYVAST_USERNAME or not PEYVAST_PASSWORD:
            logger.error("PEYVAST_USERNAME and PEYVAST_PASSWORD environment variables are not set")
            return False

        try:
            # Step 1: Load main page to set initial cookies
            logger.info("Loading main page for initial cookies...")
            self.session.get(f"{PEYVAST_BASE_URL}/", timeout=REQUEST_TIMEOUT)

            # Step 2: Get CSRF token from Sanctum
            logger.info("Getting CSRF token from Sanctum...")
            csrf_response = self.session.get(
                f"{PEYVAST_BASE_URL}/sanctum/csrf-cookie",
                timeout=REQUEST_TIMEOUT
            )
            xsrf_token = self.session.cookies.get('XSRF-TOKEN', '')
            if not xsrf_token:
                logger.error("Failed to get XSRF-TOKEN cookie")
                return False

            # URL decode the token
            from urllib.parse import unquote
            xsrf_token = unquote(xsrf_token)
            logger.info(f"Got CSRF token: {xsrf_token[:30]}...")

            # Step 3: POST login with CSRF token
            logger.info("Posting login credentials...")
            login_data = {
                'email': PEYVAST_USERNAME,
                'password': PEYVAST_PASSWORD
            }

            response = self.session.post(
                f"{PEYVAST_BASE_URL}/login",
                data=login_data,
                headers={
                    'X-XSRF-TOKEN': xsrf_token,  # Already URL decoded above
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                allow_redirects=True,
                timeout=REQUEST_TIMEOUT
            )

            logger.info(f"Login response: {response.status_code} - {response.url}")

            if response.status_code == 200:
                if 'dashboard' in response.url.lower() or 'peyvast' in response.url.lower():
                    logger.info("Successfully authenticated with Peyvast Panel!")
                    return True
                elif 'login' in response.url:
                    logger.error("Login failed - still on login page")
                    return False

            logger.warning(f"Authentication returned status {response.status_code}")
            return False

        except requests.RequestException as e:
            logger.error(f"Authentication error: {str(e)}")
            return False

    def _try_alternative_login(self) -> bool:
        """Try alternative authentication methods."""
        try:
            # Try form-based login
            login_url = f"{PEYVAST_BASE_URL}/login"

            form_data = {
                'email': PEYVAST_USERNAME,
                'password': PEYVAST_PASSWORD,
                '_token': self._csrf_token or ''
            }

            response = self.session.post(
                login_url,
                data=form_data,
                allow_redirects=True,
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code in [200, 302]:
                # Check if we're now on a logged-in page
                if 'dashboard' in response.url.lower() or 'peyvast' in response.url.lower():
                    logger.info("Successfully authenticated via form login")
                    return True

            return False

        except requests.RequestException as e:
            logger.error(f"Alternative login error: {str(e)}")
            return False

    def is_authenticated(self) -> bool:
        """Check if session is authenticated."""
        return bool(self._auth_token)

    # ─── Data Fetching ────────────────────────────────────────────────────────

    def fetch_stock_data(self, page: int = 1, per_page: int = 100) -> Tuple[List[PeyvastStockItem], Dict]:
        """
        Fetch stock data from Peyvast Panel.
        Returns tuple of (list of items, pagination info).

        Uses the actual working API endpoints discovered from reverse engineering:
        - /dashboard/products/search - product catalog with pagination
        - /dashboard/reports/inventory/list - inventory with stock levels
        - /dashboard/warehouses/api/inventory-list - per-location inventory
        """
        if not self.is_authenticated():
            if not self.authenticate():
                logger.error("Not authenticated, cannot fetch stock data")
                return [], {'error': 'Authentication failed'}

        try:
            all_items = []
            pagination = {'current_page': 1, 'total_pages': 1, 'total': 0}

            # Method 1: Get all products from /dashboard/products/search with pagination
            logger.info("Fetching products from /dashboard/products/search...")
            search_url = f"{PEYVAST_BASE_URL}/dashboard/products/search"
            params = {'search': '', 'page': page, 'per_page': per_page}

            response = self.session.get(search_url, params=params, timeout=REQUEST_TIMEOUT)

            if response.status_code == 200:
                try:
                    products = response.json()
                    if isinstance(products, list):
                        logger.info(f"Got {len(products)} products from search endpoint")

                        # Now get inventory data for these products
                        for product in products:
                            item = self._create_item_from_product_search(product)
                            if item:
                                all_items.append(item)

                        pagination = {
                            'current_page': page,
                            'per_page': per_page,
                            'total': len(all_items),
                            'total_pages': 1
                        }
                except Exception as e:
                    logger.warning(f"Error parsing search response: {e}")

            # Method 2: Get inventory from /dashboard/warehouses/api/inventory-list
            logger.info("Fetching inventory from /dashboard/warehouses/api/inventory-list...")
            inv_response = self.session.get(
                f"{PEYVAST_BASE_URL}/dashboard/warehouses/api/inventory-list",
                timeout=REQUEST_TIMEOUT
            )

            if inv_response.status_code == 200:
                try:
                    inv_data = inv_response.json()
                    if isinstance(inv_data, dict) and 'inventory' in inv_data:
                        inventory = inv_data['inventory']
                        logger.info(f"Got {len(inventory)} inventory records")

                        # Merge inventory data with products
                        for inv in inventory:
                            product = inv.get('product', {})
                            item = self._create_item_from_inventory(inv, product)
                            if item:
                                # Check if we already have this item
                                existing = next((i for i in all_items if i.barcode == item.barcode), None)
                                if existing:
                                    existing.current_stock = item.current_stock
                                else:
                                    all_items.append(item)
                except Exception as e:
                    logger.warning(f"Error parsing inventory response: {e}")

            # Method 3: Also get from /dashboard/reports/inventory/list for complete data
            logger.info("Fetching from /dashboard/reports/inventory/list...")
            reports_response = self.session.get(
                f"{PEYVAST_BASE_URL}/dashboard/reports/inventory/list",
                params={'page': page, 'per_page': per_page},
                timeout=REQUEST_TIMEOUT
            )

            if reports_response.status_code == 200:
                try:
                    reports_data = reports_response.json()
                    if isinstance(reports_data, dict) and 'data' in reports_data:
                        data = reports_data['data']
                        if isinstance(data, dict) and 'products' in data:
                            products_data = data['products']
                            if isinstance(products_data, dict) and 'data' in products_data:
                                products_list = products_data['data']
                                logger.info(f"Got {len(products_list)} products from reports")

                                for p in products_list:
                                    item = self._create_item_from_report(p)
                                    if item:
                                        existing = next((i for i in all_items if i.barcode == item.barcode), None)
                                        if existing:
                                            existing.current_stock = item.current_stock
                                        else:
                                            all_items.append(item)

                            elif isinstance(products_data, list):
                                for p in products_data:
                                    item = self._create_item_from_report(p)
                                    if item:
                                        existing = next((i for i in all_items if i.barcode == item.barcode), None)
                                        if existing:
                                            existing.current_stock = item.current_stock
                                        else:
                                            all_items.append(item)
                except Exception as e:
                    logger.warning(f"Error parsing reports response: {e}")

            logger.info(f"Total items fetched: {len(all_items)}")
            return all_items, pagination

        except requests.RequestException as e:
            logger.error(f"Error fetching stock data: {str(e)}")
            return [], {'error': str(e)}

    def _fetch_stock_via_webpage(self, page: int = 1, per_page: int = 100) -> Tuple[List[PeyvastStockItem], Dict]:
        """Fetch stock data by scraping the web page."""
        try:
            stock_url = f"{PEYVAST_BASE_URL}/dashboard/peyvast?page=database%2Fstock-management&role=admin"
            response = self.session.get(stock_url, timeout=REQUEST_TIMEOUT)

            if response.status_code != 200:
                return [], {'error': f'Page load failed with status {response.status_code}'}

            # Parse HTML to extract data
            items, total = self._parse_html_table(response.text)

            pagination = {
                'current_page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page if total > 0 else 1
            }

            return items, pagination

        except requests.RequestException as e:
            logger.error(f"Error fetching via webpage: {str(e)}")
            return [], {'error': str(e)}

    def _parse_stock_response(self, data: Dict) -> Tuple[List[PeyvastStockItem], Dict]:
        """Parse API response into PeyvastStockItem objects."""
        items = []

        # Handle different response formats
        if isinstance(data, dict):
            products = data.get('products', []) or data.get('data', []) or data.get('items', []) or []
            pagination = data.get('pagination', {}) or data.get('meta', {}) or {}
        elif isinstance(data, list):
            products = data
            pagination = {}
        else:
            products = []
            pagination = {}

        for product in products:
            try:
                item = PeyvastStockItem.from_api_response(product)
                if item.part_number or item.barcode:
                    items.append(item)
            except Exception as e:
                logger.warning(f"Failed to parse product: {e}")
                continue

        return items, pagination

    def _parse_html_table(self, html: str) -> Tuple[List[PeyvastStockItem], int]:
        """Parse HTML response to extract stock table data."""
        items = []
        total = 0

        # Simple regex-based parsing for the table
        # This is a fallback when API is not available
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)

        for row in rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
            if len(cells) >= 6:
                try:
                    # Clean HTML tags from cell content
                    def clean_cell(cell):
                        return re.sub(r'<[^>]+>', '', cell).strip()

                    item = PeyvastStockItem(
                        part_number=clean_cell(cells[2] if len(cells) > 2 else ''),  # Barcode/Part Number
                        barcode=clean_cell(cells[2] if len(cells) > 2 else ''),
                        product_code=clean_cell(cells[1] if len(cells) > 1 else ''),
                        description=clean_cell(cells[3] if len(cells) > 3 else ''),
                        product_name=clean_cell(cells[3] if len(cells) > 3 else ''),
                        current_stock=int(re.sub(r'[^\d]', '', clean_cell(cells[4] if len(cells) > 4 else '0')) or 0),
                        warehouse_name=clean_cell(cells[5] if len(cells) > 5 else 'Peyvast'),
                        brand=clean_cell(cells[6] if len(cells) > 6 else ''),
                        last_synced_at=datetime.now().isoformat()
                    )
                    if item.part_number:
                        items.append(item)
                except Exception as e:
                    continue

        # Try to find total count
        total_match = re.search(r'total["\']?\s*:\s*(\d+)', html)
        if total_match:
            total = int(total_match.group(1))

        return items, total

    def _create_item_from_product_search(self, product: Dict) -> Optional[PeyvastStockItem]:
        """Create PeyvastStockItem from /dashboard/products/search response."""
        try:
            return PeyvastStockItem(
                part_number=str(product.get('barcode', '') or product.get('sku', '')).strip(),
                barcode=str(product.get('barcode', '') or product.get('sku', '')).strip(),
                product_code=str(product.get('product_number', '') or product.get('sku', '')).strip(),
                description=str(product.get('title', '')).strip(),
                product_name=str(product.get('title', '')).strip(),
                brand=str(product.get('brand_name', '')).strip(),
                last_synced_at=datetime.now().isoformat()
            )
        except Exception as e:
            logger.warning(f"Error creating item from product search: {e}")
            return None

    def _create_item_from_inventory(self, inventory: Dict, product: Dict) -> Optional[PeyvastStockItem]:
        """Create PeyvastStockItem from /dashboard/warehouses/api/inventory-list response."""
        try:
            warehouse = inventory.get('warehouse', {})
            location = inventory.get('location', {})

            return PeyvastStockItem(
                part_number=str(product.get('barcode', '') or product.get('sku', '')).strip(),
                barcode=str(product.get('barcode', '') or product.get('sku', '')).strip(),
                product_code=str(product.get('number', '') or product.get('barcode', '')).strip(),
                description=str(product.get('title', '')).strip(),
                product_name=str(product.get('title', '')).strip(),
                warehouse_name=str(warehouse.get('name', 'Peyvast')).strip(),
                stock_location=str(location.get('code', '')).strip(),
                current_stock=int(inventory.get('quantity', 0) or 0),
                min_stock=int(inventory.get('min_stock_level', 0) or 0),
                last_synced_at=datetime.now().isoformat()
            )
        except Exception as e:
            logger.warning(f"Error creating item from inventory: {e}")
            return None

    def _create_item_from_report(self, product: Dict) -> Optional[PeyvastStockItem]:
        """Create PeyvastStockItem from /dashboard/reports/inventory/list response."""
        try:
            return PeyvastStockItem(
                part_number=str(product.get('barcode', '') or product.get('sku', '')).strip(),
                barcode=str(product.get('barcode', '') or product.get('sku', '')).strip(),
                product_code=str(product.get('barcode', '') or product.get('sku', '')).strip(),
                description=str(product.get('title', '')).strip(),
                product_name=str(product.get('title', '')).strip(),
                brand=str(product.get('brand_name', '')).strip(),
                current_stock=int(product.get('total_stock', 0) or 0),
                last_synced_at=datetime.now().isoformat()
            )
        except Exception as e:
            logger.warning(f"Error creating item from report: {e}")
            return None

    def fetch_all_stock_data(self, max_items: int = None) -> List[PeyvastStockItem]:
        """
        Fetch all stock data with pagination.
        Returns list of all PeyvastStockItem objects.
        """
        all_items = []
        page = 1
        per_page = 100
        total_pages = 1

        while page <= total_pages:
            items, pagination = self.fetch_stock_data(page=page, per_page=per_page)

            if not items:
                break

            all_items.extend(items)

            # Update pagination info
            total_pages = pagination.get('total_pages', 1)
            total = pagination.get('total', 0)

            logger.info(f"Fetched page {page}/{total_pages} - {len(items)} items (total: {total})")

            # Check if we've reached max items limit
            if max_items and len(all_items) >= max_items:
                all_items = all_items[:max_items]
                break

            page += 1

            # Small delay to avoid rate limiting
            time.sleep(0.5)

        logger.info(f"Total items fetched: {len(all_items)}")
        return all_items

    # ─── Data Synchronization ─────────────────────────────────────────────────

    def sync_all(self, force_full: bool = False) -> Dict[str, Any]:
        """
        Perform full synchronization with Peyvast Panel.
        Returns sync statistics and status.
        """
        sync_id = self._create_sync_log("full_sync", "running")
        start_time = datetime.now()

        result = {
            'sync_id': sync_id,
            'success': False,
            'items_total': 0,
            'items_synced': 0,
            'items_updated': 0,
            'items_failed': 0,
            'warehouses_synced': 0,
            'categories_synced': 0,
            'errors': [],
            'warnings': [],
            'duration_seconds': 0
        }

        try:
            # Reset stats
            self._sync_stats = {'total': 0, 'synced': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

            # Step 1: Authenticate
            if not self.authenticate():
                result['errors'].append("Authentication failed - check PEYVAST_USERNAME and PEYVAST_PASSWORD")
                return result

            # Step 2: Fetch all stock data
            stock_items = self.fetch_all_stock_data()
            result['items_total'] = len(stock_items)

            if not stock_items:
                result['warnings'].append("No stock items fetched from source")
                logger.warning("No stock items fetched from Peyvast Panel")

            # Step 3: Sync warehouses
            warehouses = list(set(item.warehouse_name for item in stock_items if item.warehouse_name))
            self._sync_warehouses(warehouses)
            result['warehouses_synced'] = len(warehouses)

            # Step 4: Sync categories
            categories = list(set(item.category for item in stock_items if item.category))
            self._sync_categories(categories)
            result['categories_synced'] = len(categories)

            # Step 5: Sync products (upsert)
            for item in stock_items:
                try:
                    success = self._upsert_product(item)
                    if success:
                        result['items_synced'] += 1
                    else:
                        result['items_skipped'] += 1
                except Exception as e:
                    result['items_failed'] += 1
                    result['errors'].append(f"Failed to sync {item.part_number}: {str(e)}")
                    logger.error(f"Failed to sync {item.part_number}: {e}")

            # Step 6: Update local inventory tables
            self._sync_local_inventory(stock_items)

            result['success'] = True
            result['duration_seconds'] = (datetime.now() - start_time).total_seconds()

        except Exception as e:
            result['errors'].append(str(e))
            logger.error(f"Sync error: {e}")

        finally:
            self._complete_sync_log(sync_id, result)
            self._last_sync_time = datetime.now()

        return result

    def _upsert_product(self, item: PeyvastStockItem) -> bool:
        """
        Insert or update a product in the peyvast_products table.
        Uses part_number as the canonical key.
        """
        if not item.part_number and not item.barcode:
            return False

        part_number = item.part_number or item.barcode

        with self.get_db() as db:
            now = datetime.now().isoformat()

            # Check if exists
            existing = db.execute(
                "SELECT id FROM peyvast_products WHERE part_number = ?",
                (part_number,)
            ).fetchone()

            if existing:
                # Update existing
                db.execute('''
                    UPDATE peyvast_products SET
                        barcode = ?, product_code = ?, description = ?, product_name = ?,
                        category = ?, brand = ?, warehouse_name = ?, stock_location = ?,
                        current_stock = ?, initial_stock = ?, min_stock = ?, max_stock = ?,
                        last_purchase_price = ?, last_purchase_qty = ?, last_purchase_date = ?,
                        avg_unit_cost = ?, seller_invoice_details = ?,
                        last_synced_at = ?, updated_at = ?
                    WHERE part_number = ?
                ''', (
                    item.barcode, item.product_code, item.description, item.product_name,
                    item.category, item.brand, item.warehouse_name, item.stock_location,
                    item.current_stock, item.initial_stock, item.min_stock, item.max_stock,
                    item.last_purchase_price, item.last_purchase_qty, item.last_purchase_date,
                    item.avg_unit_cost, item.seller_invoice_details,
                    now, now, part_number
                ))
                return True
            else:
                # Insert new
                db.execute('''
                    INSERT INTO peyvast_products
                    (part_number, barcode, product_code, description, product_name,
                     category, brand, warehouse_name, stock_location,
                     current_stock, initial_stock, min_stock, max_stock,
                     last_purchase_price, last_purchase_qty, last_purchase_date,
                     avg_unit_cost, seller_invoice_details, last_synced_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    part_number, item.barcode, item.product_code, item.description, item.product_name,
                    item.category, item.brand, item.warehouse_name, item.stock_location,
                    item.current_stock, item.initial_stock, item.min_stock, item.max_stock,
                    item.last_purchase_price, item.last_purchase_qty, item.last_purchase_date,
                    item.avg_unit_cost, item.seller_invoice_details, now
                ))
                return True

    def _sync_warehouses(self, warehouse_names: List[str]) -> None:
        """Sync warehouses from Peyvast Panel to local database."""
        with self.get_db() as db:
            for name in warehouse_names:
                if not name:
                    continue

                now = datetime.now().isoformat()
                existing = db.execute(
                    "SELECT id FROM peyvast_warehouses WHERE name = ?", (name,)
                ).fetchone()

                if existing:
                    db.execute('''
                        UPDATE peyvast_warehouses
                        SET last_synced_at = ?, is_active = 1
                        WHERE name = ?
                    ''', (now, name))
                else:
                    db.execute('''
                        INSERT INTO peyvast_warehouses (name, last_synced_at)
                        VALUES (?, ?)
                    ''', (name, now))

    def _sync_categories(self, category_names: List[str]) -> None:
        """Sync categories from Peyvast Panel to local database."""
        with self.get_db() as db:
            for name in category_names:
                if not name:
                    continue

                now = datetime.now().isoformat()
                existing = db.execute(
                    "SELECT id FROM peyvast_categories WHERE name = ?", (name,)
                ).fetchone()

                if existing:
                    db.execute('''
                        UPDATE peyvast_categories
                        SET last_synced_at = ?
                        WHERE name = ?
                    ''', (now, name))
                else:
                    db.execute('''
                        INSERT INTO peyvast_categories (name, last_synced_at)
                        VALUES (?, ?)
                    ''', (name, now))

    def _sync_local_inventory(self, items: List[PeyvastStockItem]) -> None:
        """
        Sync inventory quantities from Peyvast Panel to local database.
        Links with local parts table using part_number as canonical key.
        """
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
                part_number = item.part_number or item.barcode
                if not part_number:
                    continue

                # Find or create local part
                part_row = db.execute(
                    "SELECT id FROM parts WHERE part_number = ?",
                    (part_number,)
                ).fetchone()

                if not part_row:
                    # Get category id
                    cat_id = None
                    if item.category:
                        cat_row = db.execute(
                            "SELECT id FROM categories WHERE name = ?",
                            (item.category,)
                        ).fetchone()
                        cat_id = cat_row['id'] if cat_row else None

                    # Get brand id
                    brand_id = None
                    if item.brand:
                        brand_row = db.execute(
                            "SELECT id FROM brands WHERE name = ?",
                            (item.brand,)
                        ).fetchone()
                        brand_id = brand_row['id'] if brand_row else None

                    # Create new part
                    db.execute('''
                        INSERT INTO parts (part_number, description, category_id, brand_id,
                                          reorder_point, cost_price, peyvast_part_number)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        part_number,
                        item.description or item.product_name,
                        cat_id,
                        brand_id,
                        item.min_stock,
                        item.avg_unit_cost,
                        part_number
                    ))
                    part_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
                else:
                    part_id = part_row['id']
                    # Update existing part info
                    db.execute('''
                        UPDATE parts SET
                            description = ?,
                            reorder_point = ?,
                            cost_price = ?,
                            peyvast_part_number = ?
                        WHERE id = ?
                    ''', (
                        item.description or item.product_name,
                        item.min_stock,
                        item.avg_unit_cost,
                        part_number,
                        part_id
                    ))

                # Check if inventory record exists
                inv_row = db.execute('''
                    SELECT id FROM inventory
                    WHERE part_id = ? AND company_id = ?
                ''', (part_id, company_id)).fetchone()

                now = datetime.now().isoformat()

                if inv_row:
                    # Update quantity and cost info
                    db.execute('''
                        UPDATE inventory SET
                            quantity = ?,
                            warehouse_id = ?,
                            last_purchase_price = ?,
                            last_purchase_qty = ?,
                            last_purchase_date = ?,
                            avg_unit_cost = ?,
                            seller_invoice_details = ?,
                            updated_at = ?
                        WHERE part_id = ? AND company_id = ?
                    ''', (
                        item.current_stock,
                        warehouse_id,
                        item.last_purchase_price,
                        item.last_purchase_qty,
                        item.last_purchase_date,
                        item.avg_unit_cost,
                        item.seller_invoice_details,
                        now,
                        part_id,
                        company_id
                    ))
                else:
                    # Create new inventory record
                    db.execute('''
                        INSERT INTO inventory
                        (part_id, company_id, warehouse_id, quantity,
                         last_purchase_price, last_purchase_qty, last_purchase_date,
                         avg_unit_cost, seller_invoice_details, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        part_id,
                        company_id,
                        warehouse_id,
                        item.current_stock,
                        item.last_purchase_price,
                        item.last_purchase_qty,
                        item.last_purchase_date,
                        item.avg_unit_cost,
                        item.seller_invoice_details,
                        now
                    ))

    # ─── Sync Log Management ──────────────────────────────────────────────────

    def _create_sync_log(self, sync_type: str, status: str) -> int:
        """Create a sync log entry and return its ID."""
        with self.get_db() as db:
            db.execute('''
                INSERT INTO peyvast_sync_log (sync_type, status, started_at)
                VALUES (?, ?, ?)
            ''', (sync_type, status, datetime.now().isoformat()))
            return db.execute("SELECT last_insert_rowid()").fetchone()[0]

    def _complete_sync_log(self, sync_id: int, result: Dict) -> None:
        """Update sync log with completion status."""
        with self.get_db() as db:
            errors_json = json.dumps(result['errors'], ensure_ascii=False) if result['errors'] else None
            warnings_json = json.dumps(result['warnings'], ensure_ascii=False) if result.get('warnings') else None

            db.execute('''
                UPDATE peyvast_sync_log SET
                    status = ?,
                    items_total = ?,
                    items_synced = ?,
                    items_updated = ?,
                    items_failed = ?,
                    errors = ?,
                    completed_at = ?,
                    duration_seconds = ?
                WHERE id = ?
            ''', (
                'completed' if result['success'] else 'failed',
                result['items_total'],
                result['items_synced'],
                result.get('items_updated', 0),
                result.get('items_failed', 0),
                errors_json or warnings_json,
                datetime.now().isoformat(),
                result.get('duration_seconds', 0),
                sync_id
            ))

    def get_sync_status(self, limit: int = 10) -> List[Dict]:
        """Get recent sync log entries."""
        with self.get_db() as db:
            rows = db.execute('''
                SELECT * FROM peyvast_sync_log
                ORDER BY started_at DESC
                LIMIT ?
            ''', (limit,)).fetchall()
            return [dict(row) for row in rows]

    def get_last_successful_sync(self) -> Optional[Dict]:
        """Get the most recent successful sync."""
        with self.get_db() as db:
            row = db.execute('''
                SELECT * FROM peyvast_sync_log
                WHERE status = 'completed'
                ORDER BY started_at DESC
                LIMIT 1
            ''').fetchone()
            return dict(row) if row else None

    # ─── Data Retrieval ───────────────────────────────────────────────────────

    def get_all_products(self, filters: Dict = None) -> List[Dict]:
        """
        Get all synced products with optional filters.
        Filter keys: warehouse, category, brand, search, min_stock, max_stock,
                      exclude_out_of_stock
        """
        with self.get_db() as db:
            query = '''
                SELECT * FROM peyvast_products
                WHERE 1=1
            '''
            params = []

            if filters:
                if filters.get('warehouse'):
                    query += " AND warehouse_name = ?"
                    params.append(filters['warehouse'])
                if filters.get('category'):
                    query += " AND category = ?"
                    params.append(filters['category'])
                if filters.get('brand'):
                    query += " AND brand = ?"
                    params.append(filters['brand'])
                if filters.get('search'):
                    query += " AND (part_number LIKE ? OR barcode LIKE ? OR description LIKE ?)"
                    search_term = f"%{filters['search']}%"
                    params.extend([search_term, search_term, search_term])
                if filters.get('min_stock') is not None:
                    query += " AND current_stock >= ?"
                    params.append(filters['min_stock'])
                if filters.get('max_stock') is not None:
                    query += " AND current_stock <= ?"
                    params.append(filters['max_stock'])
                if filters.get('exclude_out_of_stock'):
                    query += " AND current_stock > 0"

            query += " ORDER BY current_stock DESC"

            rows = db.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_all_products_count(self) -> int:
        """Get total count of all products."""
        with self.get_db() as db:
            row = db.execute('SELECT COUNT(*) as cnt FROM peyvast_products').fetchone()
            return row['cnt'] if row else 0

    def get_low_stock_items(self, threshold: int = None) -> List[Dict]:
        """Get items that are below minimum stock level."""
        with self.get_db() as db:
            if threshold is not None:
                rows = db.execute('''
                    SELECT * FROM peyvast_products
                    WHERE current_stock <= min_stock AND current_stock > 0
                    ORDER BY (min_stock - current_stock) DESC
                ''').fetchall()
            else:
                rows = db.execute('''
                    SELECT * FROM peyvast_products
                    WHERE current_stock < min_stock
                    ORDER BY (min_stock - current_stock) DESC
                ''').fetchall()
            return [dict(row) for row in rows]

    def get_out_of_stock_items(self) -> List[Dict]:
        """Get items that are out of stock."""
        with self.get_db() as db:
            rows = db.execute('''
                SELECT * FROM peyvast_products
                WHERE current_stock = 0
                ORDER BY category, part_number
            ''').fetchall()
            return [dict(row) for row in rows]

    def get_stock_by_warehouse(self, warehouse_name: str = None) -> List[Dict]:
        """Get stock items grouped by warehouse."""
        with self.get_db() as db:
            if warehouse_name:
                rows = db.execute('''
                    SELECT * FROM peyvast_products
                    WHERE warehouse_name = ?
                    ORDER BY category, part_number
                ''', (warehouse_name,)).fetchall()
            else:
                rows = db.execute('''
                    SELECT * FROM peyvast_products
                    ORDER BY warehouse_name, category, part_number
                ''').fetchall()
            return [dict(row) for row in rows]

    def get_stock_by_brand(self, brand: str = None) -> List[Dict]:
        """Get stock items grouped by brand."""
        with self.get_db() as db:
            if brand:
                rows = db.execute('''
                    SELECT * FROM peyvast_products
                    WHERE brand = ?
                    ORDER BY category, part_number
                ''', (brand,)).fetchall()
            else:
                rows = db.execute('''
                    SELECT * FROM peyvast_products
                    ORDER BY brand, category, part_number
                ''').fetchall()
            return [dict(row) for row in rows]

    def get_warehouses(self) -> List[Dict]:
        """Get all synced warehouses."""
        with self.get_db() as db:
            rows = db.execute('''
                SELECT * FROM peyvast_warehouses
                WHERE is_active = 1
                ORDER BY name
            ''').fetchall()
            return [dict(row) for row in rows]

    def get_categories(self) -> List[Dict]:
        """Get all synced categories."""
        with self.get_db() as db:
            rows = db.execute('''
                SELECT * FROM peyvast_categories
                ORDER BY name
            ''').fetchall()
            return [dict(row) for row in rows]

    def get_brands(self) -> List[str]:
        """Get all unique brands."""
        with self.get_db() as db:
            rows = db.execute('''
                SELECT DISTINCT brand FROM peyvast_products
                WHERE brand IS NOT NULL AND brand != ''
                ORDER BY brand
            ''').fetchall()
            return [row['brand'] for row in rows]

    def get_stock_summary(self) -> Dict:
        """Get stock summary statistics."""
        with self.get_db() as db:
            total = db.execute("SELECT COUNT(*) as cnt FROM peyvast_products").fetchone()['cnt']
            total_qty = db.execute("SELECT COALESCE(SUM(current_stock), 0) as total FROM peyvast_products").fetchone()['total']
            low_stock = db.execute(
                "SELECT COUNT(*) as cnt FROM peyvast_products WHERE current_stock <= min_stock AND current_stock > 0"
            ).fetchone()['cnt']
            out_of_stock = db.execute(
                "SELECT COUNT(*) as cnt FROM peyvast_products WHERE current_stock = 0"
            ).fetchone()['cnt']
            over_stock = db.execute(
                "SELECT COUNT(*) as cnt FROM peyvast_products WHERE current_stock >= max_stock"
            ).fetchone()['cnt']

            warehouses = db.execute(
                "SELECT COUNT(*) as cnt FROM peyvast_warehouses WHERE is_active = 1"
            ).fetchone()['cnt']

            categories = db.execute(
                "SELECT COUNT(*) as cnt FROM peyvast_categories"
            ).fetchone()['cnt']

            brands = db.execute(
                "SELECT COUNT(DISTINCT brand) as cnt FROM peyvast_products WHERE brand IS NOT NULL AND brand != ''"
            ).fetchone()['cnt']

            # Get total value
            total_value = db.execute(
                "SELECT COALESCE(SUM(current_stock * avg_unit_cost), 0) as total FROM peyvast_products"
            ).fetchone()['total']

            # Get last sync time
            last_sync = self.get_last_successful_sync()
            last_sync_time = last_sync['started_at'] if last_sync else None

            return {
                'total_products': total,
                'total_warehouse_quantity': total_qty,
                'low_stock': low_stock,
                'out_of_stock': out_of_stock,
                'over_stock': over_stock,
                'warehouses': warehouses,
                'categories': categories,
                'brands': brands,
                'total_stock_value': total_value,
                'last_sync_at': last_sync_time
            }

    def get_stock_by_part_number(self, part_number: str) -> Optional[Dict]:
        """Get detailed stock info for a specific part number."""
        with self.get_db() as db:
            row = db.execute(
                'SELECT * FROM peyvast_products WHERE part_number = ?',
                (part_number,)
            ).fetchone()
            return dict(row) if row else None

    # ─── CSV/Excel Import ──────────────────────────────────────────────────────

    def import_from_csv(self, csv_file_path: str) -> Dict[str, Any]:
        """
        Import stock data from a CSV file.
        Expected columns: part_number, barcode, product_code, description, product_name,
                         category, brand, warehouse_name, stock_location, current_stock,
                         initial_stock, min_stock, max_stock, last_purchase_price,
                         last_purchase_qty, last_purchase_date, avg_unit_cost,
                         seller_invoice_details

        Returns dict with success status and import statistics.
        """
        import csv

        result = {
            'success': False,
            'total_rows': 0,
            'imported': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }

        sync_id = self._create_sync_log("csv_import", "running")
        start_time = datetime.now()

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Normalize column names
                fieldnames = [fn.lower().strip().replace(' ', '_') for fn in reader.fieldnames or []]
                reader.fieldnames = fieldnames

                # Map common column variations
                column_map = {
                    'part_number': ['part_number', 'partnumber', 'part#', 'pn'],
                    'barcode': ['barcode', 'bar_code', 'bar'],
                    'product_code': ['product_code', 'productcode', 'code', 'prod_code'],
                    'description': ['description', 'desc', 'product_name', 'productname', 'name'],
                    'product_name': ['product_name', 'productname', 'name'],
                    'category': ['category', 'cat', 'cat_name'],
                    'brand': ['brand', 'make', 'manufacturer'],
                    'warehouse_name': ['warehouse_name', 'warehouse', 'wh', 'location'],
                    'stock_location': ['stock_location', 'location', 'bin', 'slot'],
                    'current_stock': ['current_stock', 'stock', 'qty', 'quantity', 'currentstock'],
                    'initial_stock': ['initial_stock', 'initialstock', 'initial'],
                    'min_stock': ['min_stock', 'minstock', 'min', 'reorder_point'],
                    'max_stock': ['max_stock', 'maxstock', 'max'],
                    'last_purchase_price': ['last_purchase_price', 'lastpurchaseprice', 'purchase_price', 'price'],
                    'last_purchase_qty': ['last_purchase_qty', 'lastpurchaseqty', 'purchase_qty', 'qty_purchased'],
                    'last_purchase_date': ['last_purchase_date', 'lastpurchasedate', 'purchase_date', 'date'],
                    'avg_unit_cost': ['avg_unit_cost', 'avgunitcost', 'unit_cost', 'cost', 'avg_cost'],
                    'seller_invoice_details': ['seller_invoice_details', 'seller', 'invoice', 'supplier']
                }

                # Build effective reader
                rows = list(reader)
                result['total_rows'] = len(rows)

                for idx, row in enumerate(rows):
                    try:
                        # Map columns
                        item_data = {}
                        for std_name, variations in column_map.items():
                            for var in variations:
                                if var in row:
                                    val = row[var]
                                    if std_name in ['current_stock', 'initial_stock', 'min_stock', 'max_stock',
                                                   'last_purchase_qty']:
                                        item_data[std_name] = int(float(val)) if val else 0
                                    elif std_name in ['last_purchase_price', 'avg_unit_cost']:
                                        item_data[std_name] = float(val) if val else 0.0
                                    else:
                                        item_data[std_name] = str(val).strip() if val else ''
                                    break

                        # Create PeyvastStockItem
                        item = PeyvastStockItem(
                            part_number=item_data.get('part_number', ''),
                            barcode=item_data.get('barcode', ''),
                            product_code=item_data.get('product_code', ''),
                            description=item_data.get('description', ''),
                            product_name=item_data.get('product_name', ''),
                            category=item_data.get('category', ''),
                            brand=item_data.get('brand', ''),
                            warehouse_name=item_data.get('warehouse_name', 'Peyvast'),
                            stock_location=item_data.get('stock_location', ''),
                            current_stock=item_data.get('current_stock', 0),
                            initial_stock=item_data.get('initial_stock', 0),
                            min_stock=item_data.get('min_stock', 0),
                            max_stock=item_data.get('max_stock', 0),
                            last_purchase_price=item_data.get('last_purchase_price', 0),
                            last_purchase_qty=item_data.get('last_purchase_qty', 0),
                            last_purchase_date=item_data.get('last_purchase_date', ''),
                            avg_unit_cost=item_data.get('avg_unit_cost', 0),
                            seller_invoice_details=item_data.get('seller_invoice_details', ''),
                            last_synced_at=datetime.now().isoformat()
                        )

                        if self._upsert_product(item):
                            result['imported'] += 1
                        else:
                            result['skipped'] += 1

                    except Exception as e:
                        result['errors'].append(f"Row {idx + 2}: {str(e)}")

            # Sync warehouses and categories
            products = self.get_all_products()
            warehouses = list(set(p.get('warehouse_name') for p in products if p.get('warehouse_name')))
            categories = list(set(p.get('category') for p in products if p.get('category')))
            self._sync_warehouses(warehouses)
            self._sync_categories(categories)

            result['success'] = True

        except Exception as e:
            result['errors'].append(f"Import failed: {str(e)}")

        finally:
            result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
            self._complete_sync_log(sync_id, {
                'success': result['success'],
                'items_total': result['total_rows'],
                'items_synced': result['imported'],
                'items_updated': result['updated'],
                'items_failed': len(result['errors']),
                'errors': result['errors'],
                'duration_seconds': result.get('duration_seconds', 0)
            })

        return result

    def import_from_excel(self, excel_file_path: str, sheet_name: str = None) -> Dict[str, Any]:
        """
        Import stock data from an Excel file.
        Uses pandas and openpyxl for reading.
        """
        try:
            import pandas as pd
        except ImportError:
            return {
                'success': False,
                'errors': ['pandas library is required for Excel import. Install with: pip install pandas openpyxl']
            }

        result = {
            'success': False,
            'total_rows': 0,
            'imported': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }

        sync_id = self._create_sync_log("excel_import", "running")
        start_time = datetime.now()

        try:
            # Read Excel file
            if sheet_name:
                df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(excel_file_path, sheet_name=0)

            # Normalize column names
            df.columns = [str(col).lower().strip().replace(' ', '_') for col in df.columns]

            result['total_rows'] = len(df)

            # Convert to list of dicts and process
            for idx, row in df.iterrows():
                try:
                    item = PeyvastStockItem(
                        part_number=str(row.get('part_number', row.get('barcode', ''))).strip(),
                        barcode=str(row.get('barcode', row.get('part_number', ''))).strip(),
                        product_code=str(row.get('product_code', '')).strip(),
                        description=str(row.get('description', row.get('product_name', ''))).strip(),
                        product_name=str(row.get('product_name', row.get('description', ''))).strip(),
                        category=str(row.get('category', '')).strip(),
                        brand=str(row.get('brand', '')).strip(),
                        warehouse_name=str(row.get('warehouse_name', row.get('warehouse', 'Peyvast'))).strip(),
                        stock_location=str(row.get('stock_location', '')).strip(),
                        current_stock=int(row.get('current_stock', row.get('stock', row.get('quantity', 0)))),
                        initial_stock=int(row.get('initial_stock', 0)),
                        min_stock=int(row.get('min_stock', 0)),
                        max_stock=int(row.get('max_stock', 0)),
                        last_purchase_price=float(row.get('last_purchase_price', 0)),
                        last_purchase_qty=int(row.get('last_purchase_qty', 0)),
                        last_purchase_date=str(row.get('last_purchase_date', '')).strip(),
                        avg_unit_cost=float(row.get('avg_unit_cost', 0)),
                        seller_invoice_details=str(row.get('seller_invoice_details', '')).strip(),
                        last_synced_at=datetime.now().isoformat()
                    )

                    if item.part_number and self._upsert_product(item):
                        result['imported'] += 1
                    else:
                        result['skipped'] += 1

                except Exception as e:
                    result['errors'].append(f"Row {idx + 2}: {str(e)}")

            # Sync warehouses and categories
            products = self.get_all_products()
            warehouses = list(set(p.get('warehouse_name') for p in products if p.get('warehouse_name')))
            categories = list(set(p.get('category') for p in products if p.get('category')))
            self._sync_warehouses(warehouses)
            self._sync_categories(categories)

            result['success'] = True

        except Exception as e:
            result['errors'].append(f"Excel import failed: {str(e)}")

        finally:
            result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
            self._complete_sync_log(sync_id, {
                'success': result['success'],
                'items_total': result['total_rows'],
                'items_synced': result['imported'],
                'items_updated': result['updated'],
                'items_failed': len(result['errors']),
                'errors': result['errors'],
                'duration_seconds': result.get('duration_seconds', 0)
            })

        return result

    # ─── Settings Management ──────────────────────────────────────────────────

    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get a sync setting value."""
        with self.get_db() as db:
            row = db.execute(
                "SELECT value FROM peyvast_sync_settings WHERE key = ?",
                (key,)
            ).fetchone()
            return row['value'] if row else default

    def set_setting(self, key: str, value: str) -> None:
        """Set a sync setting value."""
        with self.get_db() as db:
            db.execute('''
                INSERT OR REPLACE INTO peyvast_sync_settings (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, value, datetime.now().isoformat()))


# ─── Standalone Functions ────────────────────────────────────────────────────

def run_sync() -> Dict[str, Any]:
    """Run full sync with Peyvast Panel."""
    manager = PeyvastSyncManager()
    manager.ensure_sync_schema()
    return manager.sync_all()


def get_sync_manager() -> PeyvastSyncManager:
    """Get a configured PeyvastSyncManager instance."""
    return PeyvastSyncManager()


if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("Peyvast Stock Sync - Starting synchronization...")
    print("=" * 60)

    # Check credentials
    if not PEYVAST_USERNAME or not PEYVAST_PASSWORD:
        print("\nERROR: PEYVAST_USERNAME and PEYVAST_PASSWORD environment variables are required.")
        print("\nPlease set them before running:")
        print("  Windows (PowerShell):")
        print('    $env:PEYVAST_USERNAME = "lab@sdadparts.com"')
        print('    $env:PEYVAST_PASSWORD = "Lab!1234"')
        print("\n  Linux/Mac:")
        print('    export PEYVAST_USERNAME="lab@sdadparts.com"')
        print('    export PEYVAST_PASSWORD="Lab!1234"')
        print("\n  Or create a .env file in the project root:")
        print("    PEYVAST_USERNAME=lab@sdadparts.com")
        print("    PEYVAST_PASSWORD=Lab!1234")
        sys.exit(1)

    result = run_sync()

    print("\n" + "=" * 60)
    print("Sync Results:")
    print("=" * 60)
    print(f"Success: {result['success']}")
    print(f"Total Items: {result['items_total']}")
    print(f"Synced: {result['items_synced']}")
    print(f"Failed: {result['items_failed']}")
    print(f"Warehouses: {result['warehouses_synced']}")
    print(f"Categories: {result['categories_synced']}")
    print(f"Duration: {result.get('duration_seconds', 0):.2f} seconds")

    if result['errors']:
        print("\nErrors:")
        for err in result['errors'][:5]:
            print(f"  - {err}")

    print("=" * 60)
