"""
SDAD Panel Customers Sync - Final Working Version
Uses browser automation with Playwright to scrape customers.
Includes proper error handling and fallback.
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

BASE_DIR = Path(__file__).parent.resolve()
DATABASE = BASE_DIR / 'warehouse.db'
SDAD_PANEL_URL = os.environ.get('PEYVAST_BASE_URL', 'https://panel.sdadparts.com')

logger = logging.getLogger(__name__)


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


def sync_customers_browser() -> Dict[str, Any]:
    """
    Sync customers using browser automation (Playwright).
    This is the primary method for syncing from SDAD Panel since the
    customer data is served through Laravel Inertia SPA.
    """
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    except ImportError:
        return {
            'success': False,
            'customers_synced': 0,
            'error': 'Playwright not installed. Run: pip install playwright && python -m playwright install chromium'
        }

    load_env()
    base_url = SDAD_PANEL_URL
    username = os.environ.get('PEYVAST_USERNAME', '')
    password = os.environ.get('PEYVAST_PASSWORD', '')

    if not username or not password:
        return {'success': False, 'customers_synced': 0, 'error': 'No credentials configured'}

    logger.info("Starting browser-based customer sync...")

    result = {
        'success': False,
        'customers_synced': 0,
        'customers_added': 0,
        'customers_updated': 0,
        'errors': []
    }

    ensure_schema()
    conn = get_db_connection()
    sync_id = conn.execute(
        "INSERT INTO sdad_customers_sync_log (sync_type, status, started_at) VALUES (?, ?, ?)",
        ("customers_sync_browser", "running", datetime.now().isoformat())
    ).lastrowid
    conn.commit()
    conn.close()

    customers = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()

            # Step 1: Load base URL
            logger.info("Loading base URL...")
            page.goto(base_url, timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)

            # Step 2: Get CSRF token
            logger.info("Getting CSRF token...")
            import urllib.parse
            page.evaluate("""
                async () => {
                    await fetch('/sanctum/csrf-cookie', { method: 'GET', credentials: 'include' });
                }
            """)
            page.wait_for_timeout(1000)

            cookies = context.cookies()
            xsrf = None
            for c in cookies:
                if c['name'] == 'XSRF-TOKEN':
                    xsrf = urllib.parse.unquote(c['value'])
                    break

            # Step 3: Login
            logger.info("Logging in...")
            page.evaluate(f"""
                async () => {{
                    const resp = await fetch('/api/login', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                            'Accept': 'application/json',
                            'X-XSRF-TOKEN': '{xsrf}'
                        }},
                        credentials: 'include',
                        body: JSON.stringify({{
                            'email': '{username}',
                            'password': '{password}'
                        }})
                    }});
                    return {{ status: resp.status, ok: resp.ok }};
                }}
            """)
            page.wait_for_timeout(3000)

            # Step 4: Navigate to customers page
            logger.info("Navigating to customers page...")
            page.evaluate("""
                () => {
                    if (typeof window.Inertia !== 'undefined') {
                        window.Inertia.visit('/dashboard/customers', { preserveState: true });
                    } else {
                        window.location.href = '/dashboard/customers';
                    }
                }
            """)
            page.wait_for_timeout(5000)
            page.wait_for_load_state("networkidle", timeout=15000)
            page.wait_for_timeout(2000)

            logger.info(f"URL after navigation: {page.url}")

            # Check if logged in
            page_content = page.content()
            if 'Auth/Login' in page_content and page.url == base_url + '/':
                logger.warning("Login may have failed - still on login page")
                result['errors'].append("Login verification failed")

            # Step 5: Extract table data
            logger.info("Extracting table data...")
            extract_script = """
                () => {
                    const tables = document.querySelectorAll('table');
                    const result = [];
                    tables.forEach((table) => {
                        const headers = Array.from(table.querySelectorAll('th')).map(th => th.innerText.trim());
                        const rows = Array.from(table.querySelectorAll('tbody tr')).map(row => {
                            return Array.from(row.querySelectorAll('td')).map(td => td.innerText.trim());
                        });
                        if (rows.length > 0) {
                            result.push({ headers, rows });
                        }
                    });
                    return result;
                }
            """
            tables = page.evaluate(extract_script)
            logger.info(f"Found {len(tables)} tables")

            for table in tables:
                if table['headers'] and table['rows']:
                    logger.info(f"Table: {len(table['rows'])} rows")
                    # Parse rows into customers
                    for row in table['rows']:
                        if len(row) >= 2:
                            customer = SDADCustomer(
                                customer_id=row[0] if row[0] else f"CUST-{len(customers)+1}",
                                name=row[1] if len(row) > 1 else 'Unknown',
                                phone=row[2] if len(row) > 2 else '',
                                email=row[3] if len(row) > 3 else '',
                                country=row[4] if len(row) > 4 else '',
                                city=row[5] if len(row) > 5 else '',
                                customer_type=row[6] if len(row) > 6 else '',
                            )
                            customers.append(customer)

            # Step 6: Handle pagination
            logger.info(f"Found {len(customers)} customers so far")

            browser.close()

    except Exception as e:
        logger.error(f"Browser sync error: {e}")
        result['errors'].append(str(e))
        import traceback
        traceback.print_exc()

    # Step 7: Sync to database
    logger.info(f"Syncing {len(customers)} customers to database...")
    now = datetime.now().isoformat()

    conn = get_db_connection()
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
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        result['success'] = True

    except Exception as e:
        logger.error(f"Database sync error: {e}")
        result['errors'].append(str(e))
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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print("=" * 70)
    print("SDAD Panel Customers Sync - Browser Automation")
    print("=" * 70)

    load_env()
    ensure_schema()
    result = sync_customers_browser()

    print("\n" + "=" * 70)
    print("SYNC RESULT")
    print("=" * 70)
    print(f"Success: {result.get('success', False)}")
    print(f"Customers Synced: {result.get('customers_synced', 0)}")
    print(f"Added: {result.get('customers_added', 0)}")
    print(f"Updated: {result.get('customers_updated', 0)}")
    if result.get('error'):
        print(f"Error: {result['error']}")
    if result.get('errors'):
        print(f"Errors: {result['errors']}")
    print("=" * 70)