from sdad_customers_sync import run_customer_sync

result = run_customer_sync()
print(f"Success: {result['success']}")
print(f"Customers: {result.get('customers_synced', 0)}")
print(f"Added: {result.get('customers_added', 0)}")
print(f"Updated: {result.get('customers_updated', 0)}")
if result.get('errors'):
    print(f"Errors: {result['errors']}")