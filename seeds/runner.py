"""
Seed Runner
===========
Centralized seed execution for the MMDx platform.

Seeds are organized into three tiers:

  1. BOOTSTRAP (core_reference_data) - Must run first
     -> Core lookup tables, roles, statuses, categories, brands,
        default platform settings, audit/nofification/settings tables.
        These are production-safe reference data that the app depends on.

  2. REFERENCE (reference_data) - Runs second
     -> Sample/reference companies, warehouses, users, suppliers.
        Can be used in production; contains real-ish reference entities.

  3. DEMO (demo_data) - Runs last / optional
     -> Demo customers, inventory, delivery trips, tasks, issues, etc.
        ONLY for development/demo environments. Marked clearly.

Environment Variables:
  SEED_MODE=none       - Skip all seeds (production)
  SEED_MODE=bootstrap  - Bootstrap only
  SEED_MODE=reference  - Bootstrap + reference
  SEED_MODE=demo       - Bootstrap + reference + demo (default for dev)

Usage:
  python seeds/runner.py                    # Run based on SEED_MODE env
  python seeds/runner.py --mode bootstrap   # Explicit bootstrap only
  python seeds/runner.py --mode none        # Skip all seeds

Module-level seed functions are imported on-demand so that seeds/
directory can be reorganized without breaking this runner.
"""

import os
import sys
import importlib
from pathlib import Path

# ==============================================================================
# Seed Tier Definitions
# ==============================================================================

BOOTSTRAP_SEEDS = [
    ('seeds.bootstrap.core_reference', 'seed_core_reference'),
]

REFERENCE_SEEDS = [
    ('seeds.bootstrap.core_reference', 'seed_reference_companies'),
    ('seeds.bootstrap.core_reference', 'seed_reference_users'),
    ('seeds.bootstrap.core_reference', 'seed_reference_warehouses'),
]

DEMO_SEEDS = [
    ('seeds.demo.sample_customers', 'seed_demo_customers'),
    ('seeds.demo.sample_delivery_trips', 'seed_demo_delivery_trips'),
    ('seeds.demo.sample_tasks', 'seed_demo_tasks'),
    ('seeds.demo.sample_issues', 'seed_demo_issues'),
    ('seeds.demo.sample_inventory', 'seed_demo_inventory'),
    # Customer Intelligence seeds
    ('seeds.demo.sample_customer_intelligence', 'seed_ci_settings'),
    ('seeds.demo.sample_customer_intelligence', 'seed_ci_customers'),
    ('seeds.demo.sample_customer_intelligence', 'seed_ci_risk_alerts'),
    ('seeds.demo.sample_customer_intelligence', 'seed_ci_recommendations'),
    ('seeds.demo.sample_customer_intelligence', 'seed_ci_lost_sales'),
    ('seeds.demo.sample_customer_intelligence', 'seed_ci_forecasts'),
    ('seeds.demo.sample_customer_intelligence', 'seed_ci_financial_profiles'),
    ('seeds.demo.sample_customer_intelligence', 'seed_ci_retail_behavior'),
    ('seeds.demo.sample_customer_intelligence', 'seed_ci_wholesale_behavior'),
    ('seeds.demo.sample_customer_intelligence', 'seed_ci_seasonality'),
    ('seeds.demo.sample_customer_intelligence', 'seed_ci_logistics_profiles'),
    ('seeds.demo.sample_customer_intelligence', 'seed_ci_demand_history'),
    ('seeds.demo.sample_customer_intelligence', 'seed_ci_kpi_records'),
]

# ==============================================================================
# Seed Runner
# ==============================================================================

class SeedRunner:
    """Orchestrates seed execution with proper ordering."""

    def __init__(self, db_getter=None):
        self.db_getter = db_getter or self._default_db_getter
        self.executed = []
        self.errors = []

    def _default_db_getter(self):
        """Default DB getter using database.py"""
        from database import get_db
        return get_db()

    def run_seed(self, module_path, function_name):
        """Import and call a single seed function."""
        try:
            module = importlib.import_module(module_path)
            fn = getattr(module, function_name, None)
            if fn is None:
                print(f"  [WARN] {module_path}.{function_name} not found - skipping")
                return True

            if callable(fn):
                print(f"  Running {module_path}::{function_name}...")
                fn(self.db_getter)
                self.executed.append(f"{module_path}.{function_name}")
                return True
            else:
                print(f"  [WARN] {function_name} in {module_path} is not callable - skipping")
                return True
        except Exception as e:
            print(f"  [ERROR] {module_path}.{function_name} failed: {e}")
            self.errors.append((module_path, function_name, str(e)))
            return False

    def run_tier(self, tier_name, seeds):
        """Run all seeds in a tier."""
        print(f"\n{'='*60}")
        print(f"  SEED TIER: {tier_name}")
        print(f"{'='*60}")
        for module_path, function_name in seeds:
            self.run_seed(module_path, function_name)

    def run(self, mode=None):
        """
        Run seeds based on mode.

        Modes:
          none       - Skip all seeds
          bootstrap  - Core reference data only
          reference  - Bootstrap + reference data
          demo       - All tiers (default in dev)
        """
        mode = mode or os.environ.get('SEED_MODE', 'demo')

        print(f"\n{'#'*60}")
        print(f"# MMDx Seed Runner")
        print(f"# Mode: {mode}")
        print(f"# Time: {__import__('datetime').datetime.now().isoformat()}")
        print(f"{'#'*60}")

        if mode == 'none':
            print("\n[SEED MODE: none] Skipping all seeds.")
            return

        self.run_tier("BOOTSTRAP (core reference)", BOOTSTRAP_SEEDS)

        if mode in ('reference', 'demo'):
            self.run_tier("REFERENCE (reference data)", REFERENCE_SEEDS)

        if mode == 'demo':
            self.run_tier("DEMO (sample data)", DEMO_SEEDS)

        # Summary
        print(f"\n{'='*60}")
        print(f"  SEED SUMMARY")
        print(f"{'='*60}")
        print(f"  Executed : {len(self.executed)}")
        if self.errors:
            print(f"  Errors   : {len(self.errors)}")
            for mod, fn, err in self.errors:
                print(f"    - {mod}.{fn}: {err}")
        else:
            print(f"  Errors   : 0")
        print(f"{'='*60}\n")

        return len(self.errors) == 0


# ==============================================================================
# CLI Entry Point
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run MMDx seed scripts')
    parser.add_argument(
        '--mode',
        choices=['none', 'bootstrap', 'reference', 'demo'],
        default=None,
        help='Seed mode (default from SEED_MODE env var, fallback: demo)'
    )
    args = parser.parse_args()

    runner = SeedRunner()
    success = runner.run(mode=args.mode)
    sys.exit(0 if success else 1)