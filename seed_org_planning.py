"""
Organizational Planning & BPM - Demo Data Seeder
================================================
Run this script to seed demo data for the Organizational Planning module.

Usage:
    python seed_org_planning.py

This will create:
- 2 companies (MMDx Global Corporation + MMDx MENA Operations)
- 8 divisions under the main company
- 32 departments under the divisions
- 30 positions at various levels
- Headcount plans for all departments
- 8 workflow definitions with steps
- 8 SLA policies
- 7 approval matrices
- 4 automation rules
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from org_planning_models import (
    run_org_planning_migrations,
    seed_org_planning_demo_data
)

def main():
    print("=" * 60)
    print("Organizational Planning & BPM - Demo Data Seeder")
    print("=" * 60)
    print()
    
    # Run migrations first
    print("[1/2] Running database migrations...")
    print("-" * 40)
    run_org_planning_migrations()
    print()
    
    # Seed demo data
    print("[2/2] Seeding demo data...")
    print("-" * 40)
    seed_org_planning_demo_data()
    print()
    
    print("=" * 60)
    print("Demo data seeding completed successfully!")
    print("=" * 60)
    print()
    print("You can now access the Organizational Planning module at:")
    print("  /org-planning/dashboard")
    print()

if __name__ == '__main__':
    main()
