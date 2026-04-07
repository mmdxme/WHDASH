import os
os.environ['PEYVAST_USERNAME'] = 'lab@sdadparts.com'
os.environ['PEYVAST_PASSWORD'] = 'Lab!1234'
from peyvast_sync import PeyvastSyncManager
mgr = PeyvastSyncManager()
if mgr.authenticate():
    # Try the export endpoint
    resp = mgr.session.get('https://panel.sdadparts.com/dashboard/products/export', timeout=30)
    print(f'Export status: {resp.status_code}')
    print(f'Content type: {resp.headers.get("content-type", "")}')
    print(f'Content length: {len(resp.content)}')
    print(f'URL: {resp.url}')

    # Save the content if it's something useful
    if resp.status_code == 200:
        with open('export_output.bin', 'wb') as f:
            f.write(resp.content)
        print("Saved to export_output.bin")
