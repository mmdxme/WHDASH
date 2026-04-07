"""Extract employees data from the SPA HTML page"""
import requests
import json
import re

BASE_URL = 'https://panel.sdadparts.com'

def login():
    """Login"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    })

    csrf_resp = session.get(f'{BASE_URL}/sanctum/csrf-cookie', timeout=30)
    xsrf_token = session.cookies.get('XSRF-TOKEN', '')
    from urllib.parse import unquote
    xsrf_token = unquote(xsrf_token)

    login_data = {'email': 'lab@sdadparts.com', 'password': 'Lab!1234'}
    resp = session.post(
        f'{BASE_URL}/login',
        data=login_data,
        headers={'X-XSRF-TOKEN': xsrf_token},
        allow_redirects=True,
        timeout=30
    )
    print(f"Login: {resp.status_code} - {resp.url}")
    return session

def extract_from_spa_page(session):
    """Extract employee data from SPA page"""
    print("\n=== /dashboard/employees ===")
    r = session.get(f'{BASE_URL}/dashboard/employees', timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Content-Type: {r.headers.get('Content-Type')}")
    print(f"HTML length: {len(r.text)}")

    if r.status_code == 200:
        html = r.text

        # Look for Inertia page component data
        # Inertia stores page data in a JSON payload
        patterns_to_try = [
            # Inertia v1 style
            r'window\.inertia\s*=\s*(\{[^;]+\})',
            r'inertia\.page\s*=\s*(\{[^;]+\})',
            # Script tag with JSON
            r'<script[^>]*>\s*(\{.*?"props".*?\})\s*</script>',
            r'page-data\s*=\s*"([^"]+)"',
        ]

        for pattern in patterns_to_try:
            matches = re.findall(pattern, html, re.DOTALL)
            if matches:
                print(f"Pattern '{pattern[:30]}...' matched {len(matches)} times")
                for m in matches[:2]:
                    print(f"  Match preview: {str(m)[:300]}...")

        # Look for __ INITIAL STATE __ or similar
        init_matches = re.findall(r'INITIAL_STATE["\s]*=[\s]*({.+?})', html, re.DOTALL)
        if init_matches:
            print(f"\nFound INITIAL_STATE!")
            try:
                data = json.loads(init_matches[0])
                print(f"Keys: {list(data.keys())}")
            except:
                print(f"Raw: {init_matches[0][:500]}")

        # Look for embedded JSON objects with employee data
        json嵌入式 = re.findall(r'\{[^{}]*"employees"[^{}]*\}', html)
        if json嵌入式:
            print(f"\nFound {len(json嵌入式)} embedded employee JSON objects")

        # Try to find any serialized PHP arrays or JSON
        all_json = re.findall(r'"\w+":\s*\[.*?\]\s*', html)
        print(f"\nFound {len(all_json)} JSON arrays")

        # Look for inertia version
        inertia_version = re.findall(r'X-Inertia-Version["\s]*:[\s]*"([^"]+)"', html)
        print(f"Inertia version: {inertia_version}")

        # Look for any API endpoint patterns
        api_patterns = re.findall(r'/api/[\w/-]+', html)
        unique_apis = list(set(api_patterns))
        print(f"\nUnique API patterns found ({len(unique_apis)}):")
        for api in unique_apis[:20]:
            print(f"  {api}")

        # Check if there's a specific page component for employees
        component_matches = re.findall(r'component["\s]*:[\s]*"([^"]+)"', html)
        unique_components = list(set(component_matches))
        print(f"\nComponents found ({len(unique_components)}):")
        for c in unique_components[:20]:
            print(f"  {c}")

        return html
    return None

def extract_data_from_html(html):
    """Try to extract employee data from the HTML"""
    if not html:
        return

    # Method 1: Look for page props
    print("\n=== Extracting from HTML ===")

    # Try to find serialized data
    # Laravel serializes to base64 or JSON
    serialized_patterns = [
        r'Laravel\S*?\s*=\s*({.+?});',
        r'data:[\s]*({.+?}),',
    ]

    for pattern in serialized_patterns:
        matches = re.findall(pattern, html, re.DOTALL)
        if matches:
            print(f"Pattern found: {len(matches)} matches")
            for m in matches[:2]:
                print(f"  {str(m)[:200]}...")

    # Check for any array that looks like employees
    # Look for patterns like "id", "name", "email" together
    if '"id":' in html and '"name":' in html:
        print("Found id+name pattern in HTML")

        # Find context around "employees"
        if 'employees' in html.lower():
            idx = html.lower().find('employees')
            context = html[max(0,idx-100):idx+200]
            print(f"Employees context: {context[:300]}")

if __name__ == '__main__':
    session = login()
    html = extract_from_spa_page(session)
    extract_data_from_html(html)
