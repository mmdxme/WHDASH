import requests

session = requests.Session()
login_data = {'username': 'admin', 'password': 'admin123'}
session.post('http://localhost:5000/login', data=login_data, allow_redirects=False)

resp = session.get('http://localhost:5000/admin/warehouses')
print('Status:', resp.status_code)
print('Content-Type:', resp.headers.get('Content-Type', ''))

content = resp.text

# Find visible text content
lines = content.split('\n')
visible_lines = [l.strip() for l in lines if l.strip() and len(l.strip()) > 0]
print(f'Total lines: {len(lines)}, Non-empty: {len(visible_lines)}')

# Check for specific warehouse names in visible content
check_names = ['JAFZA', 'Main Warehouse', 'Export Warehouse', 'Central Warehouse']
for name in check_names:
    if name in content:
        idx = content.find(name)
        # Show context around the name
        start = max(0, idx - 50)
        end = min(len(content), idx + 100)
        print(f'\n{name} found at {idx}:')
        print(content[start:end].replace('\n', ' '))

# Try to extract actual warehouse names from text
import re
# Find text between value=" and " pattern for warehouse names
matches = re.findall(r'<td[^>]*>\s*<input[^>]*value="([^"]*)"', content)
print(f'\nWarehouse names found: {matches[:10]}')

# Check for any error in the response
if 'Traceback' in content:
    print('\n!!! TRACEBACK FOUND IN RESPONSE !!!')
    idx = content.find('Traceback')
    print(content[idx:idx+500])
