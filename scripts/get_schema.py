import sqlite3

def get_schema():
    conn = sqlite3.connect('warehouse.db')
    c = conn.cursor()
    c.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()
    for table_name, sql in tables:
        print(f"Table: {table_name}")
        print(sql)
        print("-" * 20)
    conn.close()

if __name__ == "__main__":
    get_schema()
