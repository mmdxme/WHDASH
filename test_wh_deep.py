import requests
from bs4 import BeautifulSoup

session = requests.Session()
login_data = {'username': 'admin', 'password': 'admin123'}
session.post('http://localhost:5000/login', data=login_data, allow_redirects=False)

resp = session.get('http://localhost:5000/admin/warehouses')
content = resp.text

soup = BeautifulSoup(content, 'html.parser')

# Check page title
title = soup.find('title')
print('Page title:', title.text if title else 'NO TITLE')

# Check for h1
h1 = soup.find('h1')
print('H1:', h1.text if h1 else 'NO H1')

# Check for flash messages
flash_errors = soup.find_all(class_=lambda x: x and 'error' in x.lower())
print('Flash errors found:', len(flash_errors))
for fe in flash_errors[:3]:
    print(' -', fe.text[:100])

# Check tables
tables = soup.find_all('table')
print('Tables found:', len(tables))

# Count rows in the main table
tbody = soup.find('tbody')
if tbody:
    rows = tbody.find_all('tr')
    print('Table rows:', len(rows))
    for row in rows[:3]:
        cells = row.find_all(['td', 'th'])
        print('  Row:', [c.text.strip()[:20] for c in cells])

# Check select dropdowns
selects = soup.find_all('select')
print('Select dropdowns:', len(selects))
for sel in selects:
    options = sel.find_all('option')
    print(f'  Select ({sel.get("name", "unnamed")}): {len(options)} options')

# Look for any visible error text
all_text = soup.get_text()
error_phrases = ['Access Denied', 'Permission', 'does not have permission', 'no warehouses']
for phrase in error_phrases:
    if phrase.lower() in all_text.lower():
        idx = all_text.lower().find(phrase.lower())
        print(f'Found "{phrase}" at {idx}: ...{all_text[max(0,idx-30):idx+80]}...')
