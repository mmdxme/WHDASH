from database import get_db

db = get_db()
tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for t in tables:
    count = db.execute(f"SELECT COUNT(*) as cnt FROM {t['name']}").fetchone()
    print(f"{t['name']}: {count['cnt']} rows")
db.close()