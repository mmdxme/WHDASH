# Read the raw file bytes
with open('dashboard_routes.py', 'rb') as f:
    content = f.read()

# Find the api_export function definition
idx = content.find(b'@dashboard_bp.route("/api/export/<export_type>")')
if idx >= 0:
    print(f'Found decorator at byte {idx}')
    print(f'Bytes around it: {content[idx:idx+100].hex()}')

    # Find the function name
    next_newline = content.find(b'\n', idx)
    next_line = content[idx:next_newline+1]
    print(f'Line: {next_line}')

    # Check if there's anything between decorator and def
    between = content[next_newline:next_newline+100]
    print(f'After decorator: {between[:50]}')

# Also find the api_alerts function for comparison
idx2 = content.find(b'@dashboard_bp.route("/api/alerts")')
if idx2 >= 0:
    print(f'\nFound api_alerts decorator at byte {idx2}')
    next_newline = content.find(b'\n', idx2)
    between = content[next_newline:next_newline+50]
    print(f'After api_alerts decorator: {between[:50]}')