import sqlite3

def test_queries():
    conn = sqlite3.connect('warehouse.db')
    conn.row_factory = sqlite3.Row
    db = conn.cursor()
    
    queries = [
        "SELECT c.name, SUM(i.quantity) as total FROM inventory i JOIN companies c ON i.company_id = c.id GROUP BY c.id",
        "SELECT (SELECT COUNT(*) FROM locations) as total_locs, (SELECT COUNT(DISTINCT zone) FROM inventory WHERE quantity > 0) as occupied_locs",
        "SELECT b.name, SUM(i.quantity) as total FROM inventory i JOIN parts p ON i.part_id = p.id JOIN brands b ON p.brand_id = b.id GROUP BY b.id ORDER BY total DESC LIMIT 10",
        "SELECT (SELECT COUNT(DISTINCT part_id) FROM inventory) as unique_parts, (SELECT COUNT(*) FROM brands) as total_brands, (SELECT COUNT(*) FROM categories) as total_categories",
        "SELECT cat.name, COUNT(DISTINCT p.id) as part_count, SUM(i.quantity) as total_qty FROM inventory i JOIN parts p ON i.part_id = p.id JOIN categories cat ON p.category_id = cat.id GROUP BY cat.id",
        "SELECT SUM(i.quantity * p.cost_price) as grand_total_value FROM inventory i JOIN parts p ON i.part_id = p.id",
        "SELECT b.name, SUM(i.quantity * p.cost_price) as total_val FROM inventory i JOIN parts p ON i.part_id = p.id JOIN brands b ON p.brand_id = b.id GROUP BY b.id ORDER BY total_val DESC LIMIT 10",
        "SELECT cat.name, SUM(i.quantity * p.cost_price) as total_val FROM inventory i JOIN parts p ON i.part_id = p.id JOIN categories cat ON p.category_id = cat.id GROUP BY cat.id",
        "SELECT c.name, SUM(i.quantity * p.cost_price) as total_val FROM inventory i JOIN parts p ON i.part_id = p.id JOIN companies c ON i.company_id = c.id GROUP BY c.id",
        "SELECT p.part_number, p.name, SUM(i.quantity) as total_qty, SUM(i.quantity * p.cost_price) as total_val, cat.name as category, b.name as brand FROM inventory i JOIN parts p ON i.part_id = p.id LEFT JOIN categories cat ON p.category_id = cat.id LEFT JOIN brands b ON p.brand_id = b.id GROUP BY p.id ORDER BY total_val DESC LIMIT 20",
        "SELECT p.part_number, p.name, SUM(i.quantity) as total_qty, SUM(i.quantity * p.cost_price) as total_val, cat.name as category, b.name as brand FROM inventory i JOIN parts p ON i.part_id = p.id LEFT JOIN categories cat ON p.category_id = cat.id LEFT JOIN brands b ON p.brand_id = b.id GROUP BY p.id ORDER BY total_qty DESC LIMIT 20"
    ]
    
    for i, q in enumerate(queries):
        try:
            db.execute(q)
            print(f"Query {i} OK")
        except Exception as e:
            print(f"Query {i} FAILED: {e}")

if __name__ == '__main__':
    test_queries()
