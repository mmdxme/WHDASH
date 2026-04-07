"""Fetch all employees from /dashboard/employees/json and see full data"""
import requests
import json
from urllib.parse import unquote

BASE_URL = 'https://panel.sdadparts.com'

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
})

# Login
csrf_resp = session.get(f'{BASE_URL}/sanctum/csrf-cookie', timeout=30)
xsrf_token = session.cookies.get('XSRF-TOKEN', '')
xsrf_token = unquote(xsrf_token)

login_data = {'email': 'lab@sdadparts.com', 'password': 'Lab!1234'}
resp = session.post(
    f'{BASE_URL}/login',
    data=login_data,
    headers={'X-XSRF-TOKEN': xsrf_token, 'Accept': 'application/json'},
    timeout=30
)
print(f"Login: {resp.status_code}")

# Fetch all employees
r = session.get(f'{BASE_URL}/dashboard/employees/json', timeout=30)
print(f"Employees: {r.status_code}")

if r.status_code == 200:
    employees = r.json()
    print(f"Total employees: {len(employees)}")

    # Show first 3 complete records
    print("\n=== First 3 employees (complete data) ===")
    for i, emp in enumerate(employees[:3]):
        print(f"\n--- Employee {i+1} ---")
        print(json.dumps(emp, indent=2))

    # Show all keys from first employee
    print("\n=== Keys in employee record ===")
    if employees:
        emp = employees[0]
        print(f"Top-level keys: {list(emp.keys())}")

        # Check if there are nested objects
        for k, v in emp.items():
            if isinstance(v, dict):
                print(f"  {k} (dict): {list(v.keys())}")
            elif isinstance(v, list):
                print(f"  {k} (list): length {len(v)}")
                if v and isinstance(v[0], dict):
                    print(f"    First item keys: {list(v[0].keys())}")

    # Check for more detailed endpoint
    # Try to get employee details for first employee
    if employees:
        emp_id = employees[0]['id']
        print(f"\n=== Trying employee details for {emp_id} ===")

        # Try the details endpoint
        r2 = session.get(f'{BASE_URL}/dashboard/employees/{emp_id}/details', timeout=30)
        print(f"Details status: {r2.status_code}")
        if r2.status_code == 200:
            try:
                details = r2.json()
                print(f"Details keys: {list(details.keys())}")
                print(json.dumps(details, indent=2)[:1000])
            except:
                print(f"Raw: {r2.text[:500]}")

# Save all to file
if r.status_code == 200:
    with open('employees_raw.json', 'w') as f:
        json.dump(r.json(), f, indent=2)
    print(f"\nSaved {len(r.json())} employees to employees_raw.json")
