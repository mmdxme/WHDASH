"""
Complete Peyvast Stock Scraper v5
Uses /api/login for authentication.
"""

import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import time
import logging

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
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

load_env()

PEYVAST_BASE_URL = os.environ.get('PEYVAST_BASE_URL', 'https://panel.sdadparts.com')
USERNAME = os.environ.get('PEYVAST_USERNAME', '')
PASSWORD = os.environ.get('PEYVAST_PASSWORD', '')


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


class PeyvastScraper:
    """Complete scraper using API login."""

    def __init__(self):
        self.session = requests.Session()
        self.base_url = PEYVAST_BASE_URL
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'X-Requested-With': 'XMLHttpRequest',
        })

    def authenticate(self) -> bool:
        """Authenticate using /api/login."""
        try:
            # Step 1: Get initial cookies
            logger.info("Step 1: Getting initial cookies...")
            self.session.get(f"{self.base_url}/", timeout=30)

            # Step 2: Get CSRF token
            self.session.get(f"{self.base_url}/sanctum/csrf-cookie", timeout=30)

            # Step 3: API login
            logger.info("Step 2: API login...")
            resp = self.session.post(
                f"{self.base_url}/api/login",
                json={'email': USERNAME, 'password': PASSWORD},  # JSON body
                timeout=30
            )

            logger.info(f"API Login: {resp.status_code} - {resp.text[:200] if resp.text else 'empty'}")

            if resp.status_code == 200:
                # Try to access dashboard
                dash_resp = self.session.get(f"{self.base_url}/dashboard", timeout=30)
                logger.info(f"Dashboard: {dash_resp.status_code}")

                if 'login' not in dash_resp.url.lower():
                    logger.info("SUCCESS: Authenticated!")
                    return True

            return False

        except Exception as e:
            logger.error(f"Auth error: {e}")
            return False

    def scrape_all_items(self) -> List[StockItem]:
        """Scrape ALL items using proper pagination."""
        all_items = []
        seen = set()

        # Method 1: Try /dashboard/reports/inventory/list with pagination
        logger.info("=" * 50)
        logger.info("Method 1: /dashboard/reports/inventory/list")
        logger.info("=" * 50)

        items, total = self._fetch_inventory_list()
        logger.info(f"Got {len(items)} items from inventory list (total reported: {total})")

        for item in items:
            key = item.barcode or item.part_number
            if key and key not in seen:
                seen.add(key)
                all_items.append(item)

        # Method 2: Try /dashboard/warehouses/api/inventory-list
        logger.info("=" * 50)
        logger.info("Method 2: /dashboard/warehouses/api/inventory-list")
        logger.info("=" * 50)

        items2, _ = self._fetch_warehouse_inventory()
        logger.info(f"Got {len(items2)} items from warehouse inventory")

        for item in items2:
            key = item.barcode or item.part_number
            if key and key not in seen:
                seen.add(key)
                all_items.append(item)

        # Method 3: Try /dashboard/products/search with larger per_page
        logger.info("=" * 50)
        logger.info("Method 3: /dashboard/products/search")
        logger.info("=" * 50)

        items3, _ = self._fetch_products_search()
        logger.info(f"Got {len(items3)} items from products search")

        for item in items3:
            key = item.barcode or item.part_number
            if key and key not in seen:
                seen.add(key)
                all_items.append(item)

        # Method 4: Try /dashboard/warehouses/api/products/search
        logger.info("=" * 50)
        logger.info("Method 4: /dashboard/warehouses/api/products/search")
        logger.info("=" * 50)

        items4, _ = self._fetch_warehouse_products()
        logger.info(f"Got {len(items4)} items from warehouse products")

        for item in items4:
            key = item.barcode or item.part_number
            if key and key not in seen:
                seen.add(key)
                all_items.append(item)

        logger.info(f"=" * 50)
        logger.info(f"TOTAL UNIQUE ITEMS: {len(all_items)}")
        logger.info(f"=" * 50)

        return all_items

    def _fetch_inventory_list(self) -> tuple:
        """Fetch from /dashboard/reports/inventory/list with pagination."""
        all_items = []
        page = 1
        per_page = 500  # Maximum
        total = 0

        while True:
            logger.info(f"Fetching inventory list page {page}...")

            try:
                resp = self.session.get(
                    f"{self.base_url}/dashboard/reports/inventory/list",
                    params={'page': page, 'per_page': per_page},
                    timeout=30
                )

                if resp.status_code != 200:
                    logger.warning(f"Status {resp.status_code}")
                    break

                data = resp.json()
                logger.info(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")

                # Parse Laravel pagination format
                if isinstance(data, dict):
                    if 'data' in data:
                        inner = data['data']
                        if isinstance(inner, dict):
                            # Laravel default pagination
                            if 'products' in inner:
                                products_data = inner['products']
                                if isinstance(products_data, dict):
                                    total = products_data.get('total', 0)
                                    last_page = products_data.get('last_page', 1)
                                    current_page = products_data.get('current_page', 1)

                                    logger.info(f"Pagination: page {current_page}/{last_page}, total {total}")

                                    product_list = products_data.get('data', [])
                                    for p in product_list:
                                        item = self._parse_product(p)
                                        if item:
                                            all_items.append(item)

                                    if current_page >= last_page:
                                        break
                                    page += 1
                                elif isinstance(products_data, list):
                                    for p in products_data:
                                        item = self._parse_product(p)
                                        if item:
                                            all_items.append(item)
                            elif 'data' in inner:
                                # Another format
                                for p in inner['data']:
                                    item = self._parse_product(p)
                                    if item:
                                        all_items.append(item)
                        elif isinstance(inner, list):
                            for p in inner:
                                item = self._parse_product(p)
                                if item:
                                    all_items.append(item)
                    elif isinstance(data, list):
                        for p in data:
                            item = self._parse_product(p)
                            if item:
                                all_items.append(item)
                elif isinstance(data, list):
                    for p in data:
                        item = self._parse_product(p)
                        if item:
                            all_items.append(item)

            except Exception as e:
                logger.error(f"Error: {e}")
                break

            time.sleep(0.3)

        return all_items, total

    def _fetch_warehouse_inventory(self) -> tuple:
        """Fetch from /dashboard/warehouses/api/inventory-list."""
        all_items = []

        try:
            resp = self.session.get(
                f"{self.base_url}/dashboard/warehouses/api/inventory-list",
                params={'per_page': 500},
                timeout=30
            )

            if resp.status_code != 200:
                logger.warning(f"Warehouse inventory status: {resp.status_code}")
                return [], 0

            data = resp.json()
            logger.info(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")

            if isinstance(data, dict):
                inventory = data.get('inventory', data.get('data', []))
                if isinstance(inventory, list):
                    for inv in inventory:
                        product = inv.get('product', {})
                        item = self._parse_inventory(inv, product)
                        if item:
                            all_items.append(item)

            return all_items, len(all_items)

        except Exception as e:
            logger.error(f"Warehouse inventory error: {e}")
            return [], 0

    def _fetch_products_search(self) -> tuple:
        """Fetch from /dashboard/products/search."""
        all_items = []
        page = 1
        per_page = 500

        while True:
            try:
                resp = self.session.get(
                    f"{self.base_url}/dashboard/products/search",
                    params={'search': '', 'page': page, 'per_page': per_page},
                    timeout=30
                )

                if resp.status_code != 200:
                    break

                data = resp.json()
                items_data = []

                if isinstance(data, dict):
                    if 'data' in data:
                        inner = data['data']
                        if isinstance(inner, dict):
                            items_data = inner.get('data', [])
                            total = inner.get('total', len(items_data))
                            last_page = inner.get('last_page', 1)
                            if page >= last_page:
                                break
                        elif isinstance(inner, list):
                            items_data = inner
                            break
                    elif isinstance(data, list):
                        items_data = data
                        break
                elif isinstance(data, list):
                    items_data = data
                    break

                for p in items_data:
                    item = self._parse_product(p)
                    if item:
                        all_items.append(item)

                page += 1
                time.sleep(0.3)

            except Exception as e:
                logger.error(f"Products search error: {e}")
                break

        return all_items, len(all_items)

    def _fetch_warehouse_products(self) -> tuple:
        """Fetch from /dashboard/warehouses/api/products/search."""
        all_items = []

        try:
            resp = self.session.get(
                f"{self.base_url}/dashboard/warehouses/api/products/search",
                params={'search': '', 'per_page': 500},
                timeout=30
            )

            if resp.status_code != 200:
                return [], 0

            data = resp.json()

            if isinstance(data, dict):
                products = data.get('products', data.get('data', []))
                if isinstance(products, list):
                    for p in products:
                        item = self._parse_product(p)
                        if item:
                            all_items.append(item)

            return all_items, len(all_items)

        except Exception as e:
            logger.error(f"Warehouse products error: {e}")
            return [], 0

    def _parse_product(self, p: Dict) -> Optional[StockItem]:
        """Parse product dict into StockItem."""
        try:
            part_number = str(p.get('barcode', '') or p.get('sku', '') or p.get('part_number', '') or '').strip()
            barcode = str(p.get('barcode', '') or p.get('sku', '')).strip()

            if not part_number and not barcode:
                return None

            # Get nested product data if available
            product = p.get('product', {})

            # Get warehouse info
            warehouse = p.get('warehouse', {})
            location = p.get('location', {})

            # Determine stock values
            stock = p.get('total_stock', p.get('stock', p.get('quantity', 0)))
            min_s = p.get('min_stock', p.get('min_stock_level', 0))
            max_s = p.get('max_stock', p.get('max_stock_level', 0))

            # Get price info
            purchase_price = float(p.get('last_purchase_price', 0) or p.get('purchase_price', 0) or 0)
            avg_cost = float(p.get('avg_unit_cost', 0) or p.get('unit_cost', 0) or 0)
            purchase_qty = int(p.get('last_purchase_qty', 0) or 0)

            return StockItem(
                part_number=part_number,
                barcode=barcode,
                product_code=str(p.get('product_number', '') or p.get('barcode', '') or '').strip(),
                description=str(p.get('title', '') or p.get('description', '') or product.get('title', '') or '').strip(),
                product_name=str(p.get('title', '') or p.get('name', '') or product.get('title', '') or '').strip(),
                category=str(p.get('category_name', '') or p.get('category', '') or product.get('category_name', '') or '').strip(),
                brand=str(p.get('brand_name', '') or p.get('brand', '') or product.get('brand_name', '') or '').strip(),
                warehouse_name=str(warehouse.get('name', '') or p.get('warehouse_name', '') or 'Main').strip(),
                stock_location=str(location.get('code', '') or p.get('location', '') or '').strip(),
                current_stock=int(stock or 0),
                initial_stock=int(p.get('initial_stock', 0) or 0),
                min_stock=int(min_s or 0),
                max_stock=int(max_s or 0),
                last_purchase_price=purchase_price,
                last_purchase_qty=purchase_qty,
                last_purchase_date=str(p.get('last_purchase_date', '') or '').strip(),
                avg_unit_cost=avg_cost,
                seller_invoice_details=str(p.get('seller_invoice_details', '') or p.get('seller', '') or '').strip(),
                last_synced_at=datetime.now().isoformat()
            )
        except Exception as e:
            logger.warning(f"Parse error: {e}")
            return None

    def _parse_inventory(self, inv: Dict, product: Dict) -> Optional[StockItem]:
        """Parse inventory record."""
        try:
            part_number = str(product.get('barcode', '') or product.get('sku', '') or '').strip()
            if not part_number:
                return None

            warehouse = inv.get('warehouse', {})
            location = inv.get('location', {})

            return StockItem(
                part_number=part_number,
                barcode=str(product.get('barcode', '') or product.get('sku', '')).strip(),
                product_code=str(product.get('number', '') or product.get('barcode', '') or '').strip(),
                description=str(product.get('title', '') or '').strip(),
                product_name=str(product.get('title', '') or '').strip(),
                warehouse_name=str(warehouse.get('name', 'Peyvast')).strip(),
                stock_location=str(location.get('code', '') or '').strip(),
                current_stock=int(inv.get('quantity', 0) or 0),
                min_stock=int(inv.get('min_stock_level', 0) or 0),
                max_stock=int(inv.get('max_stock_level', 0) or 0),
                last_synced_at=datetime.now().isoformat()
            )
        except Exception as e:
            logger.warning(f"Inventory parse error: {e}")
            return None


def main():
    print("=" * 70)
    print("Peyvast Complete Scraper v5 - Fetching ALL items")
    print("=" * 70)

    scraper = PeyvastScraper()

    if not scraper.authenticate():
        print("ERROR: Authentication failed!")
        return

    print("\nAuthenticated successfully!\n")

    items = scraper.scrape_all_items()

    if not items:
        print("No items scraped!")
        return

    # Sort by current_stock descending
    items.sort(key=lambda x: x.current_stock, reverse=True)

    print(f"\n{'=' * 70}")
    print(f"SCRAPED {len(items)} ITEMS")
    print(f"SORTED BY HIGHEST STOCK QUANTITY")
    print(f"{'=' * 70}\n")

    # Display all items
    for idx, item in enumerate(items, 1):
        print(f"[{idx}] {item.part_number or item.barcode}")
        print(f"    Description: {item.description or item.product_name}")
        print(f"    Brand: {item.brand}")
        print(f"    Category: {item.category}")
        print(f"    Warehouse: {item.warehouse_name}")
        print(f"    Location: {item.stock_location}")
        print(f"    CURRENT STOCK: {item.current_stock}")
        print(f"    Min/Max: {item.min_stock}/{item.max_stock}")
        print(f"    Initial Stock: {item.initial_stock}")
        print(f"    Last Purchase: {item.last_purchase_qty} x ${item.last_purchase_price} on {item.last_purchase_date}")
        print(f"    Avg Unit Cost: ${item.avg_unit_cost}")
        print(f"    Seller/Invoice: {item.seller_invoice_details}")
        print()

    # Save to JSON
    output_file = "all_items_scraped.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump([item.to_dict() for item in items], f, ensure_ascii=False, indent=2)

    print(f"=" * 70)
    print(f"All data saved to: {output_file}")
    print(f"=" * 70)

    # Summary
    total_stock = sum(i.current_stock for i in items)
    print(f"\nSUMMARY:")
    print(f"  Total Items: {len(items)}")
    print(f"  Total Stock Quantity: {total_stock:,}")
    print(f"  Unique Brands: {len(set(i.brand for i in items if i.brand))}")
    print(f"  Unique Categories: {len(set(i.category for i in items if i.category))}")
    print(f"  Unique Warehouses: {len(set(i.warehouse_name for i in items if i.warehouse_name))}")
    print(f"  Out of Stock: {sum(1 for i in items if i.current_stock == 0)}")
    print(f"  Items with stock: {sum(1 for i in items if i.current_stock > 0)}")


if __name__ == "__main__":
    main()
