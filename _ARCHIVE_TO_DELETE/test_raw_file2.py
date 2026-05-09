# Read the raw file bytes
with open('dashboard_routes.py', 'rb') as f:
    content = f.read()

# Find the api_export function definition
search = b'api/export/<export_type>'
idx = content.find(search)
if idx >= 0:
    print(f'Found at byte {idx}')
    # Show surrounding bytes
    start = max(0, idx - 50)
    end = min(len(content), idx + len(search) + 50)
    print(f'Around it: {content[start:end]}')
    print()
    # Show hex
    print(f'Hex: {content[start:end].hex()}')