from app import app

# Add a test route to see if we can reproduce the issue
@app.route('/test_url_for/<export_type>')
def test_url_for(export_type):
    from flask import url_for
    return url_for('dashboard.api_export', export_type=export_type)

# Now test it
with app.test_client() as client:
    resp = client.get('/test_url_for/csv')
    print(f'Test result: {resp.status_code}')
    print(f'Data: {resp.data}')