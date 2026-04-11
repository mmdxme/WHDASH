"""
Fix Employee Codes Migration
============================
Reassigns all employee codes to the standardized format: EMP{YYYY}{####}
- EMP: fixed prefix
- YYYY: 4-digit year (using hire_date year or current year)
- ####: zero-padded sequential number within the year

This ensures all employee codes follow a consistent, predictable pattern.
"""

import sqlite3
import os
from datetime import datetime

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'warehouse.db'))


def get_db():
    """Get database connection with Row factory for dict-like access."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def fix_employee_codes():
    """Reassign all employee codes to standardized format EMP{YYYY}{####}."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get all employees ordered by hire_date (or created_at if no hire_date)
    employees = conn.execute("""
        SELECT id, first_name, last_name, employee_code, hire_date, created_at
        FROM hr_employees
        ORDER BY COALESCE(hire_date, created_at) ASC
    """).fetchall()
    
    if not employees:
        print("No employees found in the database.")
        return
    
    print(f"Found {len(employees)} employees to process.")
    print("-" * 80)
    
    # Group employees by year based on hire_date or created_at
    year_groups = {}
    for emp in employees:
        hire_date = emp['hire_date']
        created_at = emp['created_at']
        
        # Use hire_date if available, otherwise use created_at
        if hire_date:
            try:
                year = int(hire_date[:4])
            except (ValueError, TypeError):
                year = datetime.now().year
        else:
            try:
                year = int(created_at[:4])
            except (ValueError, TypeError):
                year = datetime.now().year
        
        if year not in year_groups:
            year_groups[year] = []
        year_groups[year].append(emp)
    
    # Generate new codes for each year group
    updates = []
    for year in sorted(year_groups.keys()):
        year_employees = year_groups[year]
        print(f"\nYear {year}: {len(year_employees)} employees")
        
        for seq, emp in enumerate(year_employees, start=1):
            new_code = f"EMP{year}{seq:04d}"
            old_code = emp['employee_code']
            updates.append((new_code, emp['id']))
            
            print(f"  {old_code} -> {new_code} ({emp['first_name']} {emp['last_name']})")
    
    # Perform the updates in a single transaction
    print("\n" + "-" * 80)
    print("Updating database...")
    
    cursor.executemany("UPDATE hr_employees SET employee_code = ? WHERE id = ?", updates)
    conn.commit()
    
    # Verify the update
    print(f"Updated {cursor.rowcount} employee codes.")
    
    # Show final result
    print("\n" + "-" * 80)
    print("Final employee codes:")
    final = conn.execute("""
        SELECT employee_code, first_name, last_name
        FROM hr_employees
        ORDER BY id
    """).fetchall()
    
    for emp in final:
        print(f"  {emp['employee_code']} - {emp['first_name']} {emp['last_name']}")
    
    conn.close()
    print("\nEmployee code standardization complete!")


if __name__ == '__main__':
    fix_employee_codes()
