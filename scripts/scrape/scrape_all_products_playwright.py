"""
Complete Peyvast Stock Scraper using Playwright
Simple approach: Login via form fill like a real user
"""

import os
import sys
import json
import sqlite3
import logging
import time
import re
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict

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


def init_database():
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
    logger.info("Database initialized")


def save_items_to_db(items: List[StockItem]) -> Dict:
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    saved = updated = errors = 0

    for item in items:
        try:
            now = datetime.now().isoformat()
            part_num = item.part_number or item.barcode
            if not part_num:
                continue

            cursor.execute("SELECT id FROM peyvast_products WHERE part_number = ?", (part_num,))
            existing = cursor.fetchone()

            if existing:
                cursor.execute('''
                    UPDATE peyvast_products SET
                        barcode=?, product_code=?, description=?, product_name=?,
                        category=?, brand=?, warehouse_name=?, stock_location=?,
                        current_stock=?, initial_stock=?, min_stock=?, max_stock=?,
                        last_purchase_price=?, last_purchase_qty=?, last_purchase_date=?,
                        avg_unit_cost=?, seller_invoice_details=?,
                        last_synced_at=?, updated_at=?
                    WHERE part_number=?
                ''', (
                    item.barcode, item.product_code, item.description, item.product_name,
                    item.category, item.brand, item.warehouse_name, item.stock_location,
                    item.current_stock, item.initial_stock, item.min_stock, item.max_stock,
                    item.last_purchase_price, item.last_purchase_qty, item.last_purchase_date,
                    item.avg_unit_cost, item.seller_invoice_details,
                    now, now, part_num
                ))
                updated += 1
            else:
                cursor.execute('''
                    INSERT INTO peyvast_products
                    (part_number, barcode, product_code, description, product_name,
                     category, brand, warehouse_name, stock_location,
                     current_stock, initial_stock, min_stock, max_stock,
                     last_purchase_price, last_purchase_qty, last_purchase_date,
                     avg_unit_cost, seller_invoice_details, last_synced_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    part_num, item.barcode, item.product_code, item.description, item.product_name,
                    item.category, item.brand, item.warehouse_name, item.stock_location,
                    item.current_stock, item.initial_stock, item.min_stock, item.max_stock,
                    item.last_purchase_price, item.last_purchase_qty, item.last_purchase_date,
                    item.avg_unit_cost, item.seller_invoice_details, now
                ))
                saved += 1
        except Exception as e:
            errors += 1
            logger.warning(f"Error: {e}")

    conn.commit()
    conn.close()
    return {'saved': saved, 'updated': updated, 'errors': errors}


def scrape():
    """Main scrape function."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        os.system(f"{sys.executable} -m playwright install chromium")
        from playwright.sync_api import sync_playwright

    init_database()
    all_items = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        # Step 1: Go to login page
        logger.info("1. Loading login page...")
        page.goto(f"{PEYVAST_BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        logger.info(f"   URL: {page.url}")

        # Step 2: Fill login form
        logger.info("2. Filling login form...")
        try:
            page.fill('input[type="email"], input[name="email"]', USERNAME)
            page.fill('input[type="password"], input[name="password"]', PASSWORD)
            logger.info("   Filled email and password")
        except Exception as e:
            logger.error(f"   Could not fill form: {e}")
            browser.close()
            return []

        # Step 3: Submit
        logger.info("3. Clicking submit...")
        try:
            page.click('button[type="submit"]')
        except Exception as e:
            logger.error(f"   Could not click submit: {e}")
            browser.close()
            return []

        # Wait for redirect
        page.wait_for_timeout(5000)
        logger.info(f"   URL after submit: {page.url}")

        # Check if logged in
        if 'login' in page.url.lower():
            logger.warning("   Still on login page")
        else:
            logger.info("   Login successful!")

        # Step 4: Navigate to stock page
        logger.info("4. Navigating to stock page...")
        stock_url = f"{PEYVAST_BASE_URL}/dashboard/peyvast?page=database%2Fstock-management&role=admin"

        # Use direct navigation
        page.goto(stock_url, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(5000)
        logger.info(f"   URL: {page.url}")

        # Check what page we're on
        if 'login' in page.url.lower():
            logger.error("   Redirected to login!")
            browser.close()
            return []

        # Get page info
        page_info = page.evaluate("""
        () => {
            const app = document.querySelector('#app');
            if (app) {
                const dp = app.getAttribute('data-page');
                if (dp) {
                    try {
                        const p = JSON.parse(dp);
                        return {component: p.component, url: window.location.href};
                    } catch(e) {}
                }
            }
            return {url: window.location.href};
        }
        """)
        logger.info(f"   Page: {page_info}")

        # Find tables
        tables = page.evaluate("""
        () => {
            const ts = document.querySelectorAll('table');
            return Array.from(ts).map(t => ({
                headers: Array.from(t.querySelectorAll('th')).map(h => h.innerText.trim()),
                rows: Array.from(t.querySelectorAll('tbody tr')).length
            }));
        }
        """)
        logger.info(f"   Tables: {tables}")

        # Scrape pagination
        total_pages = 1
        current = 1
        max_pages = 500

        while current <= max_pages:
            logger.info(f"\n=== PAGE {current} ===")

            # Wait for table
            page.wait_for_timeout(2000)

            # Get rows
            rows = page.evaluate("""
            () => {
                const tbody = document.querySelector('table tbody');
                if (!tbody) return [];
                return Array.from(tbody.querySelectorAll('tr')).map(r =>
                    Array.from(r.querySelectorAll('td')).map(td => td.innerText.trim())
                );
            }
            """)

            if not rows:
                logger.warning("No rows found")
                break

            logger.info(f"Found {len(rows)} rows")

            # Get pagination on first page
            if current == 1:
                pagination = page.evaluate("""
                () => {
                    const el = document.querySelector('.dataTables_info, .pagination-info, [class*="info"]');
                    return el ? el.innerText : '';
                }
                """)
                if pagination:
                    logger.info(f"Pagination: {pagination}")
                    m = re.search(r'of\s+([\d,]+)', pagination)
                    if m:
                        total = int(m.group(1).replace(',', ''))
                        total_pages = max(1, (total + len(rows) - 1) // len(rows))
                        logger.info(f"Total pages: {total_pages}")

            # Extract items
            for row in rows:
                if len(row) < 5:
                    continue

                barcode = row[2] if len(row) > 2 else ""
                desc = row[3] if len(row) > 3 else ""
                stock_text = row[4] if len(row) > 4 else "0"
                try:
                    stock = int(''.join(filter(str.isdigit, stock_text))) or 0
                except:
                    stock = 0
                warehouse = row[5] if len(row) > 5 else "Main"
                brand = row[6] if len(row) > 6 else ""

                if barcode and barcode not in seen:
                    seen.add(barcode)
                    all_items.append(StockItem(
                        part_number=barcode,
                        barcode=barcode,
                        product_code=row[1] if len(row) > 1 else "",
                        description=desc,
                        product_name=desc,
                        brand=brand,
                        warehouse_name=warehouse,
                        current_stock=stock,
                        last_synced_at=datetime.now().isoformat()
                    ))

            if current >= total_pages:
                break

            current += 1

            # Click next
            next_clicked = False
            for sel in ['button[rel="next"]', 'a.paginate_button.next', 'a:has-text("»")', 'a:has-text("›")', 'button:has-text("Next")']:
                try:
                    btn = page.query_selector(sel)
                    if btn and btn.is_enabled():
                        btn.click()
                        page.wait_for_timeout(2000)
                        next_clicked = True
                        break
                except:
                    pass

            if not next_clicked:
                logger.warning("Could not click next")
                break

        logger.info(f"\n=== TOTAL: {len(all_items)} items ===")
        browser.close()

    return all_items


def main():
    print("=" * 70)
    print("PEYVAST STOCK SCRAPER")
    print("=" * 70)

    if not USERNAME or not PASSWORD:
        print("\nERROR: Set PEYVAST_USERNAME and PEYVAST_PASSWORD in .env")
        return

    print(f"Username: {USERNAME}\n")

    items = scrape()

    if not items:
        print("\nNo items scraped!")
        return

    print(f"\nCollected {len(items)} items\n")

    # Save JSON
    with open("all_items_scraped.json", 'w', encoding='utf-8') as f:
        json.dump([i.to_dict() for i in items], f, ensure_ascii=False, indent=2)

    # Save DB
    result = save_items_to_db(items)
    print(f"DB: {result['saved']} saved, {result['updated']} updated, {result['errors']} errors")

    # Stats
    total_stock = sum(i.current_stock for i in items)
    brands = set(i.brand for i in items if i.brand)

    print(f"\nSUMMARY:")
    print(f"  Total Items: {len(items)}")
    print(f"  Total Stock: {total_stock}")
    print(f"  Brands: {len(brands)}")
    print(f"  Out of Stock: {sum(1 for i in items if i.current_stock == 0)}")

    print("\nFIRST 10:")
    for i, item in enumerate(items[:10], 1):
        print(f"{i}. {item.part_number} | {item.description[:30]} | Stock: {item.current_stock}")


if __name__ == "__main__":
    main()