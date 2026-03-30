import sqlite3
import os

dbs = ['database.db', 'warehouse.db', 'MMD_DASH.db', 'MMD_Dashboard.db']
for db_name in dbs:
    if os.path.exists(db_name):
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='suppliers';")
        sup = c.fetchone()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vehicles';")
        veh = c.fetchone()
        print(f"{db_name} -> suppliers: {sup}, vehicles: {veh}")
