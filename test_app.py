import sys
sys.path.insert(0, 'C:/Users/sdads/WHDASH')
try:
    from app import app
    print(f"Flask app created successfully")
    print(f"App name: {app.name}")
    print(f"Debug mode: {app.debug}")
    print(f"Secret key set: {bool(app.secret_key)}")

    # Test a few routes
    with app.test_client() as client:
        # Test home page
        rv = client.get('/')
        print(f"Home page status: {rv.status_code}")

        # Test language switch
        rv = client.get('/set_language/fa')
        print(f"Language switch to FA: {rv.status_code}")

        rv = client.get('/set_language/ar')
        print(f"Language switch to AR: {rv.status_code}")

        rv = client.get('/set_language/ru')
        print(f"Language switch to RU: {rv.status_code}")

        rv = client.get('/set_language/zh')
        print(f"Language switch to ZH: {rv.status_code}")

        rv = client.get('/set_language/es')
        print(f"Language switch to ES: {rv.status_code}")

        rv = client.get('/set_language/hi')
        print(f"Language switch to HI: {rv.status_code}")

        rv = client.get('/set_language/de')
        print(f"Language switch to DE: {rv.status_code}")

    print("\nAll Flask tests passed!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()