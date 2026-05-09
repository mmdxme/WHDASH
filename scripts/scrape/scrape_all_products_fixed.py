"""
Peyvast Stock Scraper - Complete with Retry Logic
Fetches ALL 41,888+ products from /dashboard/reports/inventory/list
"""

import os
import json
import sqlite3
import logging
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from urllib.parse import unquote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load .env
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key.strip(), value.strip())

load_env()

PEYVAST_BASE_URL = os.environ.get('PEYVAST_BASE_URL', 'https://panel.sdadparts.com')
USERNAME = os.environ.get('PEYVAST_USERNAME', '')
PASSWORD = os.environ.get('PEYVAST_PASSWORD', '')
DATABASE = os.path.join(os.path.dirname(__file__), 'warehouse.db')


@dataclass
class StockItem:
    part_number: str = ""
    barcode: str = ""
    product_code: str = ""
    description: str = ""
    product_name: str = ""
    category: str = ""
    brand: str = ""
    warehouse_name: str = ""
    stock_location: str = ""
    current_stock: int = 0
    initial_stock: int = 0
    min_stock: int = 0
    max_stock: int = 0
    last_purchase_price: float = 0.0
    last_purchase_qty: int = 0
    last_purchase_date: str = ""
    avg_unit_cost: float = 0.0
    seller_invoice_details: str = ""
    source_system: str = "peyvast"
    last_synced_at: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute('''
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
    conn.execute('CREATE INDEX IF NOT EXISTS idx_peyvast_part_number ON peyvast_products(part_number)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_peyvast_barcode ON peyvast_products(barcode)')
    conn.commit()
    conn.close()


def save_to_db(items: List[StockItem]) -> Dict:
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    saved = updated = errors = 0

    for item in items:
        try:
            now = datetime.now().isoformat()
            pn = item.part_number or item.barcode
            if not pn:
                continue

            c.execute("SELECT id FROM peyvast_products WHERE part_number = ?", (pn,))
            if c.fetchone():
                c.execute('''
                    UPDATE peyvast_products SET
                        barcode=?, product_code=?, description=?, product_name=?,
                        category=?, brand=?, warehouse_name=?, stock_location=?,
                        current_stock=?, initial_stock=?, min_stock=?, max_stock=?,
                        last_purchase_price=?, last_purchase_qty=?, last_purchase_date=?,
                        avg_unit_cost=?, seller_invoice_details=?, last_synced_at=?, updated_at=?
                    WHERE part_number=?
                ''', (
                    item.barcode, item.product_code, item.description, item.product_name,
                    item.category, item.brand, item.warehouse_name, item.stock_location,
                    item.current_stock, item.initial_stock, item.min_stock, item.max_stock,
                    item.last_purchase_price, item.last_purchase_qty, item.last_purchase_date,
                    item.avg_unit_cost, item.seller_invoice_details, now, now, pn
                ))
                updated += 1
            else:
                c.execute('''
                    INSERT INTO peyvast_products
                    (part_number, barcode, product_code, description, product_name,
                     category, brand, warehouse_name, stock_location,
                     current_stock, initial_stock, min_stock, max_stock,
                     last_purchase_price, last_purchase_qty, last_purchase_date,
                     avg_unit_cost, seller_invoice_details, last_synced_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    pn, item.barcode, item.product_code, item.description, item.product_name,
                    item.category, item.brand, item.warehouse_name, item.stock_location,
                    item.current_stock, item.initial_stock, item.min_stock, item.max_stock,
                    item.last_purchase_price, item.last_purchase_qty, item.last_purchase_date,
                    item.avg_unit_cost, item.seller_invoice_details, now
                ))
                saved += 1
        except Exception as e:
            errors += 1

    conn.commit()
    conn.close()
    return {'saved': saved, 'updated': updated, 'errors': errors}


def create_session() -> requests.Session:
    """Create a requests session with retry logic."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })

    # Add retry adapter
    adapter = HTTPAdapter(
        max_retries=Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )
    )
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    return session


def authenticate(session: requests.Session) -> bool:
    session.get(f"{PEYVAST_BASE_URL}/", timeout=30)
    session.get(f"{PEYVAST_BASE_URL}/sanctum/csrf-cookie", timeout=30)

    xsrf = unquote(session.cookies.get('XSRF-TOKEN', ''))
    if not xsrf:
        return False

    resp = session.post(
        f"{PEYVAST_BASE_URL}/login",
        data={'email': USERNAME, 'password': PASSWORD},
        headers={'X-XSRF-TOKEN': xsrf, 'Content-Type': 'application/x-www-form-urlencoded'},
        allow_redirects=True, timeout=30
    )

    return 'dashboard' in resp.url.lower()


def fetch_page_with_retry(session: requests.Session, url: str, params: dict, max_retries: int = 3) -> Optional[dict]:
    """Fetch a page with retry logic."""
    for attempt in range(max_retries):
        try:
            resp = session.get(url, params=params, timeout=60)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:  # Too many requests
                logger.warning(f"Rate limited, waiting 5 seconds...")
                time.sleep(5)
            else:
                logger.warning(f"Status {resp.status_code}")
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(3 + attempt * 2)  # Increasing delay
        except Exception as e:
            logger.error(f"Error (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(2)

    return None


def fetch_reports_inventory(session: requests.Session) -> List[StockItem]:
    """Fetch from /dashboard/reports/inventory/list with proper pagination and retry."""
    all_items = []
    seen = set()
    page = 1
    per_page = 100
    total_pages = 999
    consecutive_errors = 0
    max_consecutive_errors = 10

    while page <= total_pages and consecutive_errors < max_consecutive_errors:
        url = f"{PEYVAST_BASE_URL}/dashboard/reports/inventory/list"
        params = {'page': page, 'per_page': per_page}

        data = fetch_page_with_retry(session, url, params)

        if data is None:
            consecutive_errors += 1
            logger.warning(f"Failed to fetch page {page} ({consecutive_errors}/{max_consecutive_errors})")
            time.sleep(5)
            continue

        consecutive_errors = 0  # Reset on success

        try:
            # Parse response structure
            products_data = data.get('data', {}).get('products', {})

            if not isinstance(products_data, dict):
                logger.warning(f"Page {page}: products is not dict")
                break

            # Get pagination info
            current_page = products_data.get('current_page', 1)
            last_page = products_data.get('last_page', 1)
            total = products_data.get('total', 0)

            if page == 1:
                logger.info(f"Pagination: page {current_page}/{last_page}, total {total}")
                total_pages = last_page

            # Get products array
            products = products_data.get('data', [])

            if not products:
                logger.info("No more products")
                break

            logger.info(f"Page {page}: {len(products)} products (total: {len(all_items)})")

            # Parse each product
            for p in products:
                item = parse_product(p)
                if item:
                    key = item.part_number or item.barcode
                    if key and key not in seen:
                        seen.add(key)
                        all_items.append(item)

            # Check if we've reached the last page
            if current_page >= last_page:
                logger.info(f"Reached last page ({last_page})")
                break

            page += 1
            time.sleep(1)  # 1 second delay between pages

        except Exception as e:
            logger.error(f"Page {page}: error - {e}")
            consecutive_errors += 1
            time.sleep(2)

    return all_items


def parse_product(p: Dict) -> Optional[StockItem]:
    """Parse a product dict into StockItem."""
    try:
        pn = str(p.get('barcode', '') or p.get('sku', '') or p.get('part_number', '')).strip()

        if not pn:
            product = p.get('product', {})
            if product:
                pn = str(product.get('barcode', '') or product.get('sku', '')).strip()

        if not pn:
            return None

        return StockItem(
            part_number=pn,
            barcode=str(p.get('barcode', '') or p.get('sku', '') or pn).strip(),
            product_code=str(p.get('product_number', '') or p.get('sku', '') or pn).strip(),
            description=str(p.get('title', '') or p.get('description', '') or '').strip(),
            product_name=str(p.get('title', '') or '').strip(),
            category=str(p.get('category_name', '') or p.get('category', '') or '').strip(),
            brand=str(p.get('brand_name', '') or p.get('brand', '') or '').strip(),
            warehouse_name=str(p.get('warehouse_name', '') or 'Main').strip(),
            stock_location=str(p.get('location', '') or p.get('stock_location', '') or '').strip(),
            current_stock=int(p.get('total_stock', 0) or p.get('stock', 0) or p.get('quantity', 0) or 0),
            initial_stock=int(p.get('initial_stock', 0) or 0),
            min_stock=int(p.get('min_stock', 0) or 0),
            max_stock=int(p.get('max_stock', 0) or 0),
            last_purchase_price=float(p.get('last_purchase_price', 0) or 0),
            avg_unit_cost=float(p.get('avg_unit_cost', 0) or 0),
            last_purchase_qty=int(p.get('last_purchase_qty', 0) or 0),
            last_purchase_date=str(p.get('last_purchase_date', '') or '').strip(),
            last_synced_at=datetime.now().isoformat()
        )
    except Exception as e:
        logger.warning(f"Parse error: {e}")
        return None


def main():
    print("=" * 70)
    print("PEYVAST STOCK SCRAPER - COMPLETE WITH RETRY")
    print("=" * 70)

    if not USERNAME or not PASSWORD:
        print("\nERROR: Set PEYVAST_USERNAME and PEYVAST_PASSWORD in .env")
        return

    print(f"\nUsername: {USERNAME}")
    print(f"Target: {PEYVAST_BASE_URL}/dashboard/reports/inventory/list")
    print(f"Expected: ~41,888 products (419 pages)\n")

    init_db()

    session = create_session()

    if not authenticate(session):
        print("\nERROR: Authentication failed!")
        return

    print("\nAuthenticated!\n")

    items = fetch_reports_inventory(session)

    print(f"\n{'=' * 60}")
    print(f"TOTAL: {len(items)} items")
    print(f"{'=' * 60}")

    if not items:
        print("\nWARNING: No items scraped!")
        return

    # Save JSON
    with open("all_items_scraped.json", 'w', encoding='utf-8') as f:
        json.dump([i.to_dict() for i in items], f, ensure_ascii=False, indent=2)

    # Save DB
    result = save_to_db(items)
    print(f"DB: {result['saved']} saved, {result['updated']} updated")

    # Stats
    total_stock = sum(i.current_stock for i in items)
    brands = set(i.brand for i in items if i.brand)

    print(f"\nSUMMARY:")
    print(f"  Total Items: {len(items):,}")
    print(f"  Total Stock: {total_stock:,}")
    print(f"  Unique Brands: {len(brands)}")
    print(f"  Out of Stock: {sum(1 for i in items if i.current_stock == 0)}")
    print(f"  In Stock: {sum(1 for i in items if i.current_stock > 0)}")

    print("\nFIRST 30:")
    for i, item in enumerate(items[:30], 1):
        print(f"{i}. {item.part_number} | {item.description[:35]} | Stock: {item.current_stock} | {item.brand}")


if __name__ == "__main__":
    main()