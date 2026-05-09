"""
SDAD Panel Customers Sync - Browser Automation Version
Uses Playwright to scrape customers from Laravel Inertia SPA.
"""

import os
import sys
import json
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

import requests

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("ERROR: playwright not installed. Run: pip install playwright && python -m playwright install chromium")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.resolve()
DATABASE = BASE_DIR / 'warehouse.db'
SDAD_PANEL_URL = os.environ.get('PEYVAST_BASE_URL', 'https://panel.sdadparts.com')
USERNAME = os.environ.get('PEYVAST_USERNAME', '')
PASSWORD = os.environ.get('PEYVAST_PASSWORD', '')


@dataclass
class SDADCustomer:
    """Represents a customer from SDAD Panel."""
    customer_id: str = ""
    name: str = ""
    phone: str = ""
    phone2: str = ""
    email: str = ""
    website: str = ""
    country: str = ""
    city: str = ""
    state: str = ""
    address: str = ""
    locale: str = ""
    postal_code: str = ""
    customer_type: str = ""
    business_type: str = ""
    is_export: bool = False
    is_active: bool = True
    is_verified: bool = False
    balance: float = 0.0
    credit_limit: float = 5000.0
    total_purchases: float = 0.0
    total_paid: float = 0.0
    outstanding: float = 0.0
    last_purchase_date: str = ""
    last_purchase_amount: float = 0.0
    first_purchase_date: str = ""
    purchase_count: int = 0
    average_purchase: float = 0.0
    salesperson_id: str = ""
    salesperson_name: str = ""
    sales_team: str = ""
    created_at: str = ""
    updated_at: str = ""
    notes: str = ""
    tags: str = ""
    local_customer_id: int = 0
    last_synced_at: str = ""


def load_env():
    """Load .env file if exists."""
    env_path = BASE_DIR / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key.strip(), value.strip())


def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema():
    """Ensure sdad_customers table exists."""
    conn = get_db_connection()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sdad_customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                phone TEXT DEFAULT '',
                phone2 TEXT DEFAULT '',
                email TEXT DEFAULT '',
                website TEXT DEFAULT '',
                country TEXT DEFAULT '',
                city TEXT DEFAULT '',
                state TEXT DEFAULT '',
                address TEXT DEFAULT '',
                locale TEXT DEFAULT '',
                postal_code TEXT DEFAULT '',
                customer_type TEXT DEFAULT '',
                business_type TEXT DEFAULT '',
                is_export INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                is_verified INTEGER DEFAULT 0,
                balance REAL DEFAULT 0.0,
                credit_limit REAL DEFAULT 5000.0,
                total_purchases REAL DEFAULT 0.0,
                total_paid REAL DEFAULT 0.0,
                outstanding REAL DEFAULT 0.0,
                last_purchase_date TEXT DEFAULT '',
                last_purchase_amount REAL DEFAULT 0.0,
                first_purchase_date TEXT DEFAULT '',
                purchase_count INTEGER DEFAULT 0,
                average_purchase REAL DEFAULT 0.0,
                salesperson_id TEXT DEFAULT '',
                salesperson_name TEXT DEFAULT '',
                sales_team TEXT DEFAULT '',
                created_at TEXT DEFAULT '',
                updated_at TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                tags TEXT DEFAULT '',
                local_customer_id INTEGER DEFAULT 0,
                last_synced_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at_ts TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at_ts TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sdad_customers_sync_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_type TEXT NOT NULL,
                status TEXT NOT NULL,
                customers_synced INTEGER DEFAULT 0,
                errors TEXT,
                started_at TEXT,
                completed_at TEXT
            )
        ''')
        conn.commit()
    finally:
        conn.close()


class SDADBrowserSync:
    """Sync customers using browser automation."""

    def __init__(self):
        self.base_url = SDAD_PANEL_URL
        self.username = USERNAME
        self.password = PASSWORD
        self.customers: List[SDADCustomer] = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        })

    def login_via_requests(self) -> bool:
        """Login using requests session, then use cookies with browser."""
        logger.info("Logging in via requests session...")

        try:
            # Step 1: Get initial cookies
            self.session.get(self.base_url, timeout=30)
            logger.info("Got initial cookies")

            # Step 2: Get CSRF token
            self.session.get(f"{self.base_url}/sanctum/csrf-cookie", timeout=30)
            xsrf_token = self.session.cookies.get('XSRF-TOKEN', '')

            from urllib.parse import unquote
            xsrf_token = unquote(xsrf_token)
            logger.info(f"XSRF Token: {xsrf_token[:50]}...")

            # Step 3: API login
            resp = self.session.post(
                f"{self.base_url}/api/login",
                json={'email': self.username, 'password': self.password},
                timeout=30
            )
            logger.info(f"API Login status: {resp.status_code}")
            logger.info(f"API Login response: {resp.text[:200]}")

            if resp.status_code == 200:
                logger.info("Login successful via API!")
                return True
            else:
                logger.warning(f"Login may have failed: {resp.status_code}")
                return False

        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    def login(self, page) -> bool:
        """Login using playwright with proper SPA authentication."""
        logger.info("Starting playwright-based login...")

        try:
            from urllib.parse import unquote

            # Step 1: Get initial cookies
            logger.info("Step 1: Getting initial cookies...")
            page.goto(self.base_url, timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)

            # Get XSRF token from cookies
            csrf_cookie = page.context.cookies(f"{self.base_url}/sanctum/csrf-cookie")
            xsrf_token = None
            for c in csrf_cookie:
                if c['name'] == 'XSRF-TOKEN':
                    xsrf_token = unquote(c['value'])
                    break

            if not xsrf_token:
                logger.warning("No XSRF token found in cookies")

            logger.info(f"XSRF Token obtained: {xsrf_token[:30] if xsrf_token else 'None'}...")

            # Step 2: Execute login via JavaScript with proper headers
            logger.info("Step 2: Executing login...")

            login_script = f"""
            async () => {{
                const response = await fetch('{self.base_url}/api/login', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-XSRF-TOKEN': '{xsrf_token}'
                    }},
                    body: JSON.stringify({{
                        'email': '{self.username}',
                        'password': '{self.password}'
                    }})
                }});
                const data = await response.json();
                return {{ status: response.status, ok: response.ok, data: data }};
            }}
            """

            result = page.evaluate(login_script)
            logger.info(f"Login result: {result}")

            page.wait_for_timeout(2000)

            # Step 3: Check if logged in by visiting dashboard
            logger.info("Step 3: Verifying login...")
            page.goto(f"{self.base_url}/dashboard", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)
            page.wait_for_timeout(2000)

            logger.info(f"Current URL: {page.url}")

            # Check for Inertia page component
            page_content = page.content()
            if 'Auth/Login' in page_content or 'login' in page.url.lower():
                logger.warning("Login verification failed - still on login page")

                # Debug: check cookies
                all_cookies = page.context.cookies()
                logger.info(f"Browser cookies after login: {[c['name'] for c in all_cookies]}")

                return False

            logger.info(f"Login successful! Current URL: {page.url}")
            return True

        except Exception as e:
            logger.error(f"Login error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def navigate_to_customers(self, page) -> bool:
        """Navigate to customers page."""
        logger.info("Navigating to customers page...")

        # Try different URLs
        customer_urls = [
            f"{self.base_url}/dashboard/customers",
            f"{self.base_url}/dashboard/peyvast?page=customers",
            f"{self.base_url}/dashboard/peyvast?page=database%2Fcustomers",
        ]

        for url in customer_urls:
            try:
                logger.info(f"Trying URL: {url}")
                page.goto(url, timeout=45000)
                page.wait_for_load_state("networkidle", timeout=20000)
                page.wait_for_timeout(3000)

                if page.url and "login" not in page.url.lower():
                    logger.info(f"Successfully loaded: {page.url}")
                    return True
            except Exception as e:
                logger.warning(f"Failed to load {url}: {e}")
                continue

        return False

    def scrape_customers_table(self, page) -> List[Dict]:
        """Scrape customers from the table."""
        customers_data = []

        logger.info("Looking for customers table...")

        # Wait for table to load
        try:
            page.wait_for_selector("table", timeout=10000)
            logger.info("Found table element")
        except PlaywrightTimeout:
            logger.warning("No table found, looking for other elements...")
            # Save page for debugging
            with open(BASE_DIR / "debug_customers.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            logger.info("Saved page content to debug_customers.html")
            return []

        # Try multiple table selectors
        table_selectors = [
            "table",
            ".table",
            "table.table-hover",
            "table.customers",
            "[class*='table']",
        ]

        table = None
        for selector in table_selectors:
            try:
                table = page.wait_for_selector(selector, timeout=3000)
                if table:
                    logger.info(f"Found table with selector: {selector}")
                    break
            except PlaywrightTimeout:
                continue

        if not table:
            logger.warning("Could not find customers table!")
            return []

        # Get table rows
        rows = page.query_selector_all("tbody tr")
        if not rows:
            rows = page.query_selector_all("tr")
        logger.info(f"Found {len(rows)} table rows")

        for idx, row in enumerate(rows):
            try:
                cells = row.query_selector_all("td")
                if len(cells) < 2:
                    continue

                # Extract cell text
                cell_texts = [cell.inner_text().strip() for cell in cells]

                # Try to extract customer info
                customer = self._parse_table_row(cell_texts, idx)
                if customer:
                    customers_data.append(customer)

            except Exception as e:
                logger.warning(f"Error parsing row {idx}: {e}")
                continue

        # If table scraping didn't work, try JavaScript data extraction
        if not customers_data:
            logger.info("Table scraping didn't work, trying JavaScript extraction...")
            customers_data = self._scrape_via_javascript(page)

        return customers_data

    def _parse_table_row(self, cells: List[str], idx: int) -> Optional[Dict]:
        """Parse a table row into customer data."""
        if len(cells) < 2:
            return None

        try:
            # Basic customer from table
            customer = {
                'customer_id': cells[0] if len(cells) > 0 else f"CUST-{idx+1}",
                'name': cells[1] if len(cells) > 1 else 'Unknown',
                'phone': cells[2] if len(cells) > 2 else '',
                'email': cells[3] if len(cells) > 3 else '',
                'country': cells[4] if len(cells) > 4 else '',
                'city': cells[5] if len(cells) > 5 else '',
                'customer_type': cells[6] if len(cells) > 6 else '',
                'total_purchases': 0,
                'outstanding': 0,
            }

            return customer
        except Exception as e:
            logger.warning(f"Error parsing row: {e}")
            return None

    def _scrape_via_javascript(self, page) -> List[Dict]:
        """Try to extract data via JavaScript (Inertia SPA data)."""
        customers = []

        # Try to get Laravel/Inertia page props
        js_code = """
        () => {
            // Try window.data or window.page
            if (window.data) return window.data;
            if (window.page) return window.page;
            if (window.Inertia) return window.Inertia;

            // Try to find Vue/React app data
            const app = document.querySelector('#app');
            if (app && app.__vue__) return app.__vue__.$data;

            // Try to get from meta tags
            const meta = document.querySelector('meta[name="data"]');
            if (meta) return JSON.parse(meta.content);

            return null;
        }
        """

        try:
            result = page.evaluate(js_code)
            if result:
                logger.info(f"Found JavaScript data: {type(result)}")
        except Exception as e:
            logger.warning(f"JS extraction failed: {e}")

        # Try to get table data directly via JS
        js_table = """
        () => {
            const table = document.querySelector('table');
            if (!table) return [];

            const rows = table.querySelectorAll('tbody tr');
            const data = [];

            rows.forEach((row, idx) => {
                const cells = row.querySelectorAll('td');
                const rowData = [];
                cells.forEach(cell => {
                    rowData.push(cell.innerText.trim());
                });
                if (rowData.length > 0) {
                    data.push(rowData);
                }
            });

            return data;
        }
        """

        try:
            table_data = page.evaluate(js_table)
            if table_data and len(table_data) > 0:
                logger.info(f"Extracted {len(table_data)} rows via JS")

                for idx, row in enumerate(table_data):
                    customer = self._parse_table_row(row, idx)
                    if customer:
                        customers.append(customer)

        except Exception as e:
            logger.warning(f"JS table extraction failed: {e}")

        return customers

    def scrape_all_pages(self, page) -> List[SDADCustomer]:
        """Navigate through all pages and scrape customers."""
        all_customers = []
        page_num = 1
        seen_ids = set()

        logger.info("Starting to scrape all customer pages...")

        while True:
            logger.info(f"=== Scraping page {page_num} ===")

            # Scrape current page
            customers_data = self.scrape_customers_table(page)
            logger.info(f"Found {len(customers_data)} customers on page {page_num}")

            for cust_data in customers_data:
                cust_id = cust_data.get('customer_id', '')
                if cust_id and cust_id not in seen_ids:
                    seen_ids.add(cust_id)
                    customer = SDADCustomer(**{k: v for k, v in cust_data.items() if hasattr(SDADCustomer, k)})
                    # Set any missing fields
                    customer.customer_id = cust_id
                    all_customers.append(customer)

            # Try to go to next page
            next_button_selectors = [
                'button:has-text("Next")',
                'button:has-text("بعدی")',
                'button:has-text(">")',
                'a:has-text("Next")',
                'a:has-text(">")',
                '.page-item.next',
                '.pagination-next',
                'button[aria-label="Next"]',
                'a[rel="next"]',
            ]

            next_clicked = False
            for selector in next_button_selectors:
                try:
                    next_btn = page.wait_for_selector(selector, timeout=2000)
                    if next_btn and next_btn.is_enabled():
                        next_btn.click()
                        logger.info(f"Clicked next button: {selector}")
                        page.wait_for_timeout(2000)
                        next_clicked = True
                        page_num += 1
                        break
                except PlaywrightTimeout:
                    continue

            if not next_clicked:
                logger.info("No more pages or could not find next button")
                break

            # Safety limit
            if page_num > 100:
                logger.warning("Reached page limit (100), stopping")
                break

        logger.info(f"Total unique customers scraped: {len(all_customers)}")
        return all_customers

    def sync_to_database(self, customers: List[SDADCustomer]) -> Dict[str, Any]:
        """Sync customers to local database."""
        ensure_schema()

        conn = get_db_connection()
        now = datetime.now().isoformat()

        result = {
            'success': True,
            'customers_synced': 0,
            'customers_updated': 0,
            'customers_added': 0,
            'errors': []
        }

        sync_id = conn.execute(
            "INSERT INTO sdad_customers_sync_log (sync_type, status, started_at) VALUES (?, ?, ?)",
            ("customers_sync", "running", now)
        ).lastrowid

        try:
            for customer in customers:
                existing = conn.execute(
                    "SELECT id FROM sdad_customers WHERE customer_id = ?",
                    (customer.customer_id,)
                ).fetchone()

                if existing:
                    conn.execute('''
                        UPDATE sdad_customers SET
                            name = ?, phone = ?, phone2 = ?, email = ?, website = ?,
                            country = ?, city = ?, state = ?, address = ?, locale = ?, postal_code = ?,
                            customer_type = ?, business_type = ?, is_export = ?, is_active = ?, is_verified = ?,
                            balance = ?, credit_limit = ?, total_purchases = ?, total_paid = ?, outstanding = ?,
                            last_purchase_date = ?, last_purchase_amount = ?, first_purchase_date = ?,
                            purchase_count = ?, average_purchase = ?,
                            salesperson_id = ?, salesperson_name = ?, sales_team = ?,
                            created_at = ?, updated_at = ?, notes = ?, tags = ?,
                            last_synced_at = ?, updated_at_ts = ?
                        WHERE customer_id = ?
                    ''', (
                        customer.name, customer.phone, customer.phone2, customer.email, customer.website,
                        customer.country, customer.city, customer.state, customer.address, customer.locale, customer.postal_code,
                        customer.customer_type, customer.business_type, int(customer.is_export), int(customer.is_active), int(customer.is_verified),
                        customer.balance, customer.credit_limit, customer.total_purchases, customer.total_paid, customer.outstanding,
                        customer.last_purchase_date, customer.last_purchase_amount, customer.first_purchase_date,
                        customer.purchase_count, customer.average_purchase,
                        customer.salesperson_id, customer.salesperson_name, customer.sales_team,
                        customer.created_at, customer.updated_at, customer.notes, customer.tags,
                        now, now,
                        customer.customer_id
                    ))
                    result['customers_updated'] += 1
                else:
                    conn.execute('''
                        INSERT INTO sdad_customers (
                            customer_id, name, phone, phone2, email, website,
                            country, city, state, address, locale, postal_code,
                            customer_type, business_type, is_export, is_active, is_verified,
                            balance, credit_limit, total_purchases, total_paid, outstanding,
                            last_purchase_date, last_purchase_amount, first_purchase_date,
                            purchase_count, average_purchase,
                            salesperson_id, salesperson_name, sales_team,
                            created_at, updated_at, notes, tags, last_synced_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        customer.customer_id, customer.name, customer.phone, customer.phone2, customer.email, customer.website,
                        customer.country, customer.city, customer.state, customer.address, customer.locale, customer.postal_code,
                        customer.customer_type, customer.business_type, int(customer.is_export), int(customer.is_active), int(customer.is_verified),
                        customer.balance, customer.credit_limit, customer.total_purchases, customer.total_paid, customer.outstanding,
                        customer.last_purchase_date, customer.last_purchase_amount, customer.first_purchase_date,
                        customer.purchase_count, customer.average_purchase,
                        customer.salesperson_id, customer.salesperson_name, customer.sales_team,
                        customer.created_at, customer.updated_at, customer.notes, customer.tags, now
                    ))
                    result['customers_added'] += 1

                result['customers_synced'] += 1

            conn.commit()

        except Exception as e:
            result['errors'].append(str(e))
            result['success'] = False
            conn.rollback()
        finally:
            conn.close()

        # Update sync log
        conn = get_db_connection()
        conn.execute('''
            UPDATE sdad_customers_sync_log
            SET status = ?, customers_synced = ?, errors = ?, completed_at = ?
            WHERE id = ?
        ''', (
            'completed' if result['success'] else 'failed',
            result['customers_synced'],
            json.dumps(result['errors']) if result['errors'] else None,
            datetime.now().isoformat(),
            sync_id
        ))
        conn.commit()
        conn.close()

        return result

    def run_sync(self) -> Dict[str, Any]:
        """Run full sync operation."""
        load_env()

        logger.info("=" * 60)
        logger.info("SDAD CUSTOMERS SYNC - Browser Automation")
        logger.info("=" * 60)

        result = {
            'success': False,
            'customers_synced': 0,
            'error': ''
        }

        with sync_playwright() as p:
            browser = None
            try:
                logger.info("Starting browser...")
                browser = p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = context.new_page()

                # Enable request logging
                page.on("response", lambda response: logger.debug(f"{response.status} {response.url}"))

                # Login
                if not self.login(page):
                    result['error'] = "Login failed"
                    return result

                # Navigate to customers
                if not self.navigate_to_customers(page):
                    result['error'] = "Could not navigate to customers page"
                    return result

                # Wait for content to load
                page.wait_for_timeout(3000)

                # Scrape all pages
                customers = self.scrape_all_pages(page)
                logger.info(f"Total customers scraped: {len(customers)}")

                # Sync to database
                if customers:
                    result = self.sync_to_database(customers)
                    logger.info(f"Sync result: {result}")
                else:
                    result['error'] = "No customers scraped"
                    logger.warning("No customers were scraped from the page!")

            except Exception as e:
                logger.error(f"Error during sync: {e}")
                result['error'] = str(e)
                import traceback
                traceback.print_exc()

            finally:
                if browser:
                    browser.close()

        return result


def run_customer_sync() -> Dict[str, Any]:
    """Entry point for syncing customers."""
    load_env()
    ensure_schema()

    sync = SDADBrowserSync()
    return sync.run_sync()


if __name__ == "__main__":
    print("=" * 70)
    print("SDAD Panel Customers Sync - Browser Automation Version")
    print("=" * 70)

    result = run_customer_sync()

    print("\n" + "=" * 70)
    print("SYNC RESULT")
    print("=" * 70)
    print(f"Success: {result.get('success', False)}")
    print(f"Customers Synced: {result.get('customers_synced', 0)}")
    print(f"Added: {result.get('customers_added', 0)}")
    print(f"Updated: {result.get('customers_updated', 0)}")
    if result.get('error'):
        print(f"Error: {result['error']}")
    print("=" * 70)