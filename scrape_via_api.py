"""
Complete Peyvast Stock Scraper using API (not HTML scraping)
Since the page is an Inertia SPA, we use the API directly with bearer token
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
from typing import List, Dict, Optional

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load .env file
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
    """Complete stock item with all features."""
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
    """Initialize database schema."""
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
    logger.info("Database schema initialized")


def save_items_to_db(items: List[StockItem]) -> Dict:
    """Save items to database with upsert logic."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    saved = 0
    updated = 0
    errors = 0

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
            logger.warning(f"Error saving item {item.part_number}: {e}")

    conn.commit()
    conn.close()
    return {'saved': saved, 'updated': updated, 'errors': errors}


def login_via_api() -> Optional[str]:
    """Login via API and return bearer token."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/html, */*',
    })

    # Step 1: Get CSRF cookie
    logger.info("1. Getting CSRF cookie...")
    session.get(f"{PEYVAST_BASE_URL}/sanctum/csrf-cookie", timeout=30)

    # Step 2: API login
    logger.info("2. Logging in via API...")
    resp = session.post(
        f"{PEYVAST_BASE_URL}/api/login",
        json={'email': USERNAME, 'password': PASSWORD},
        timeout=30
    )

    logger.info(f"   Login status: {resp.status_code}")

    if resp.status_code == 200:
        try:
            data = resp.json()
            if data.get('data', {}).get('token'):
                token = data['data']['token']
                logger.info(f"   Got token: {token[:30]}...")
                return token
        except Exception as e:
            logger.error(f"   Parse error: {e}")
    else:
        logger.error(f"   Login failed: {resp.text[:200]}")

    return None


def fetch_all_products(token: str) -> List[StockItem]:
    """Fetch all products from various API endpoints using bearer token."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    })

    all_items = []
    seen_part_numbers = set()

    # Try different API endpoints
    endpoints_to_try = [
        # Products search
        f"{PEYVAST_BASE_URL}/api/products/search?search=&page=1&per_page=500",
        f"{PEYVAST_BASE_URL}/dashboard/api/products/search?search=&page=1&per_page=500",
        # Inventory reports
        f"{PEYVAST_BASE_URL}/api/reports/inventory?page=1&per_page=500",
        f"{PEYVAST_BASE_URL}/dashboard/api/reports/inventory?page=1&per_page=500",
        # Stock management
        f"{PEYVAST_BASE_URL}/api/stock?page=1&per_page=500",
        f"{PEYVAST_BASE_URL}/api/warehouses/inventory?page=1&per_page=500",
        # Products list
        f"{PEYVAST_BASE_URL}/api/products?page=1&per_page=500",
        f"{PEYVAST_BASE_URL}/dashboard/api/products?page=1&per_page=500",
    ]

    for url in endpoints_to_try:
        logger.info(f"\n{'='*60}")
        logger.info(f"Trying: {url}")
        logger.info(f"{'='*60}")

        try:
            resp = session.get(url, timeout=60)
            logger.info(f"   Status: {resp.status_code}")

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    items = parse_api_response(data, seen_part_numbers)
                    if items:
                        logger.info(f"   Got {len(items)} items!")
                        all_items.extend(items)
                    else:
                        logger.info(f"   No items parsed from this endpoint")
                        # Log structure for debugging
                        if isinstance(data, dict):
                            logger.info(f"   Keys: {list(data.keys())}")
                        elif isinstance(data, list):
                            logger.info(f"   List with {len(data)} items")
                except Exception as e:
                    logger.error(f"   Parse error: {e}")
            elif resp.status_code == 401:
                logger.warning("   Unauthorized - token may have expired")
            else:
                logger.warning(f"   Status {resp.status_code}")

        except Exception as e:
            logger.error(f"   Request error: {e}")

        time.sleep(0.5)

    # Also try with pagination
    logger.info(f"\n{'='*60}")
    logger.info("Trying with pagination...")
    logger.info(f"{'='*60}")

    for page_num in range(1, 50):  # Try up to 50 pages
        url = f"{PEYVAST_BASE_URL}/api/products/search?search=&page={page_num}&per_page=500"
        logger.info(f"\nPage {page_num}: {url}")

        try:
            resp = session.get(url, timeout=60)

            if resp.status_code == 200:
                data = resp.json()
                items = parse_api_response(data, seen_part_numbers)

                if items:
                    logger.info(f"   Page {page_num}: Got {len(items)} items (total unique: {len(all_items)})")
                    all_items.extend(items)
                else:
                    # Check if there's pagination info
                    if isinstance(data, dict):
                        if 'data' in data and isinstance(data['data'], dict):
                            pagination = data['data'].get('pagination', {})
                            if pagination:
                                logger.info(f"   Pagination: {pagination}")
                                if page_num >= pagination.get('last_page', 1):
                                    logger.info("   Reached last page")
                                    break
                    # If no items and no pagination, we might be done
                    if not items and page_num > 1:
                        break
            else:
                logger.warning(f"   Status {resp.status_code}")
                if resp.status_code == 401:
                    break

        except Exception as e:
            logger.error(f"   Error: {e}")
            break

        time.sleep(0.3)

    return all_items


def parse_api_response(data, seen_part_numbers: set) -> List[StockItem]:
    """Parse API response and return list of StockItems."""
    items = []

    if not isinstance(data, dict):
        return items

    # Handle different response structures
    # Laravel pagination: {"data": {"data": [...], "pagination": {...}}}
    # Simple list: {"data": [...]}
    # Nested: {"data": [...], "products": [...]}

    products = None

    if 'data' in data:
        inner = data['data']
        if isinstance(inner, dict):
            # Check for nested data
            if 'data' in inner:
                products = inner['data']
            elif 'products' in inner:
                products = inner['products']
            # Check for pagination
            if 'pagination' in inner:
                logger.info(f"   Pagination: {inner['pagination']}")
        elif isinstance(inner, list):
            products = inner

    if not products and 'products' in data:
        products = data['products']

    if not products:
        return items

    if not isinstance(products, list):
        return items

    logger.info(f"   Processing {len(products)} products...")

    for p in products:
        if not isinstance(p, dict):
            continue

        try:
            # Extract part number/barcode
            part_number = str(p.get('barcode', '') or p.get('sku', '') or p.get('part_number', '') or '').strip()
            barcode = str(p.get('barcode', '') or p.get('sku', '')).strip()

            if not part_number and not barcode:
                continue

            if part_number in seen_part_numbers:
                continue
            seen_part_numbers.add(part_number)

            # Get other fields
            description = str(p.get('title', '') or p.get('description', '') or p.get('name', '') or '').strip()
            product_name = str(p.get('title', '') or p.get('name', '') or '').strip()
            category = str(p.get('category_name', '') or p.get('category', '') or '').strip()
            brand = str(p.get('brand_name', '') or p.get('brand', '') or '').strip()
            warehouse_name = str(p.get('warehouse_name', '') or p.get('warehouse', '') or 'Main').strip()

            # Stock values
            stock = int(p.get('total_stock', 0) or p.get('stock', 0) or p.get('quantity', 0) or 0)
            min_stock = int(p.get('min_stock', 0) or 0)
            max_stock = int(p.get('max_stock', 0) or 0)
            initial_stock = int(p.get('initial_stock', 0) or 0)

            # Price info
            last_purchase_price = float(p.get('last_purchase_price', 0) or 0)
            avg_unit_cost = float(p.get('avg_unit_cost', 0) or p.get('unit_cost', 0) or 0)
            last_purchase_qty = int(p.get('last_purchase_qty', 0) or 0)
            last_purchase_date = str(p.get('last_purchase_date', '') or '')

            item = StockItem(
                part_number=part_number,
                barcode=barcode,
                product_code=str(p.get('product_number', '') or barcode or '').strip(),
                description=description,
                product_name=product_name,
                category=category,
                brand=brand,
                warehouse_name=warehouse_name,
                stock_location=str(p.get('location', '') or '').strip(),
                current_stock=stock,
                initial_stock=initial_stock,
                min_stock=min_stock,
                max_stock=max_stock,
                last_purchase_price=last_purchase_price,
                last_purchase_qty=last_purchase_qty,
                last_purchase_date=last_purchase_date,
                avg_unit_cost=avg_unit_cost,
                seller_invoice_details=str(p.get('seller_invoice_details', '') or '').strip(),
                last_synced_at=datetime.now().isoformat()
            )
            items.append(item)

        except Exception as e:
            logger.warning(f"   Error parsing product: {e}")
            continue

    return items


def main():
    print("=" * 70)
    print("PEYVAST COMPLETE SCRAPER - Using API")
    print("=" * 70)

    if not USERNAME or not PASSWORD:
        print("\nERROR: PEYVAST_USERNAME and PEYVAST_PASSWORD not set in .env")
        return

    print(f"\nUsername: {USERNAME}")
    print()

    init_database()

    # Login via API
    token = login_via_api()
    if not token:
        print("\nERROR: Could not get authentication token!")
        return

    print("\nAuthenticated successfully!\n")

    # Fetch all products
    items = fetch_all_products(token)

    if not items:
        print("\nWARNING: No items scraped!")
        return

    print(f"\n{'='*70}")
    print(f"SCRAPING COMPLETE: {len(items)} items collected")
    print(f"{'='*70}\n")

    # Save to JSON
    output_file = "all_items_scraped.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump([item.to_dict() for item in items], f, ensure_ascii=False, indent=2)
    print(f"Saved JSON: {output_file}")

    # Save to database
    print("\nSaving to database...")
    result = save_items_to_db(items)
    print(f"Database: {result['saved']} saved, {result['updated']} updated, {result['errors']} errors")

    # Summary
    total_stock = sum(i.current_stock for i in items)
    brands = set(i.brand for i in items if i.brand)
    categories = set(i.category for i in items if i.category)
    warehouses = set(i.warehouse_name for i in items if i.warehouse_name)

    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"  Total Items: {len(items):,}")
    print(f"  Total Stock: {total_stock:,}")
    print(f"  Unique Brands: {len(brands)}")
    print(f"  Unique Categories: {len(categories)}")
    print(f"  Unique Warehouses: {len(warehouses)}")
    print(f"  Out of Stock: {sum(1 for i in items if i.current_stock == 0)}")
    print(f"  In Stock: {sum(1 for i in items if i.current_stock > 0)}")
    print(f"{'='*70}")

    print("\nFIRST 30 ITEMS (Preview):")
    print("-" * 70)
    for i, item in enumerate(items[:30], 1):
        print(f"{i}. {item.part_number} | {item.description[:40]} | Stock: {item.current_stock} | Brand: {item.brand}")
    print("-" * 70)


if __name__ == "__main__":
    main()