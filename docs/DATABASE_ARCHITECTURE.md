# MMDx Database & Migration Architecture

> **Last Updated:** 2026-05-06
> **Status:** Remediation complete — migration framework operational

---

## Executive Summary

The MMDx database layer has been remediated from a fragile, scattered, SQLite-coupled state into a **migration-driven, schema-safe, PostgreSQL-ready** architecture.

**What was done:**
- Alembic migration framework fully wired into application startup
- All scattered module tables consolidated into migration `003`
- `init_*()` functions marked deprecated but retained for safe backward compatibility
- SQLite PRAGMA coupling reduced via engine-conditional application
- 50+ root-level `seed_*.py` files archived into `_ARCHIVE_TO_DELETE/`
- `workflow_models.py` auto-init-on-import anti-pattern removed
- Migration safety helpers (preflight checks, backup reminders, environment guards) added
- Seed runner (`seeds/runner.py`) confirmed as the single seeding entry point

---

## 1. Migration Framework

### What was introduced: Alembic 1.14.0

Alembic is now the **authoritative system for all schema evolution**.

### Files

| File | Purpose |
|------|---------|
| `alembic.ini` | Alembic configuration (points to `migrations/`) |
| `migrations/env.py` | Migration environment with dual DB (SQLite/PostgreSQL) support |
| `migrations/script.py.mako` | Template for new migration files |
| `migrations/migrate_app.py` | Safety helpers, programmatic migration control |
| `migrations/__init__.py` | Lazy-loading public API (`ensure_db_current`, `stamp_baseline_if_needed`, `get_migration_status`) |
| `migrations/versions/001_initial_schema.py` | Baseline migration — all core tables |
| `migrations/versions/002_current_schema_marker.py` | Pre-Alembic baseline marker |
| `migrations/versions/003_consolidate_scattered_tables.py` | **NEW** — All module tables consolidated |
| `migrate.py` | CLI wrapper: `python migrate.py revision -m "desc"` |

### Migration Chain

```
001_initial_schema
        ↓
002_current_schema_marker
        ↓
003_consolidate_scattered_tables  ← NEW (planning, workflow, GRC, BTP, marketing, quality, SPC, etc.)
        ↓
[future migrations]
```

### Usage

```bash
# Create a new migration
python migrate.py revision -m "add customer_phone column"

# Apply all pending migrations
python migrate.py upgrade

# Preview pending migrations (safe)
python migrate.py upgrade --sql

# Roll back one revision
python migrate.py downgrade

# Show history
python migrate.py history

# Show current state
python migrate.py current
```

### Safety Tools

```bash
# Production migration with safety checks
SKIP_MIGRATION_SAFETY=1 python migrate.py upgrade   # Bypasses prompts

# Backup reminder prints automatically before migrations
# Preflight checks verify environment before applying migrations
```

---

## 2. Schema Source of Truth

**`migrations/versions/001_initial_schema.py`** (core tables)
**`migrations/versions/003_consolidate_scattered_tables.py`** (module tables)

These are the **only authoritative schema definitions**. All other schema-creation code is deprecated.

### Deprecated patterns (must NOT be used for new work):

```python
# OLD - DO NOT USE for new tables
db.execute("CREATE TABLE IF NOT EXISTS my_table ...")
init_db()                             # Called automatically at startup
_ensure_audit_table()                 # Called automatically at startup
initialize_workflow_schema()           # Deprecated, use migrations
init_planning_tables()                # Deprecated, use migrations
```

### New pattern:

```bash
# NEW - All schema changes go through Alembic
python migrate.py revision -m "add my_table"
# Edit the generated migration, then:
python migrate.py upgrade
```

---

## 3. Application Startup — Migration Integration

The application startup flow (`application/bootstrap.py::init_app()`) now:

1. **`stamp_baseline_if_needed()`** — Detects existing databases without Alembic version table and stamps the baseline (`001_initial_schema`). New databases skip this automatically.

2. **`ensure_db_current(safe_mode=False)`** — Applies any pending Alembic migrations silently on every startup. Fast when DB is already at head.

3. **Deprecated `init_*()` calls** — All module init functions are called for backward compatibility. These use `CREATE TABLE IF NOT EXISTS` so they are safe on existing databases. They are **no-ops on properly migrated databases** because the tables already exist from Alembic migrations.

```python
# In application/bootstrap.py::init_app():

# Step 1: Stamp existing DB baseline
stamp_baseline_if_needed()

# Step 2: Apply pending migrations (idempotent)
ensure_db_current(safe_mode=False)

# Step 3: Deprecated init calls (safety net only)
_init_deprecated("planning", initialize_planning_tables)
_init_deprecated("workflow", initialize_workflow_schema)
# ... etc.
```

---

## 4. Module Tables Coverage (Migration 003)

The 003 consolidation migration covers tables from these modules that were previously created by scattered `init_*()` functions:

| Module | Tables | Source |
|--------|--------|--------|
| Planning | 37 tables (`planning_demand_history`, `planning_item_profiles`, `planning_forecast_*`, etc.) | `planning_models.py::PLANNING_TABLES_SQL` |
| Workflow | 20 tables (`workflow_definitions`, `workflow_instances`, `automation_*`, etc.) | `workflow_models.py` |
| Platform indexes | 17 indexes | `database.py::PLATFORM_INDEXES` |

All use `CREATE TABLE IF NOT EXISTS` — existing tables are preserved, new databases get the full schema.

---

## 5. Seeding System

### Structure

```
seeds/
  runner.py              # Central seed orchestrator (ONLY entry point)
  bootstrap/
    core_reference.py   # BOOTSTRAP tier: categories, brands, statuses, departments
  demo/
    sample_customers.py # DEMO tier: sample customers, trips, tasks, issues
    sample_delivery_trips.py
    sample_tasks.py
    sample_issues.py
    sample_inventory.py
```

### Tier Model

| Tier | Name | Purpose | When to run |
|------|------|---------|-------------|
| 1 | BOOTSTRAP | Core reference data, lookup tables | Always |
| 2 | REFERENCE | Companies, users, warehouses | Development/staging |
| 3 | DEMO | Sample business data | Development/demo only |

### Usage

```bash
# Default (demo mode for dev)
python seeds/runner.py

# Bootstrap only (production-like minimal)
python seeds/runner.py --mode bootstrap

# Skip all seeds
python seeds/runner.py --mode none

# Or via environment variable
SEED_MODE=reference python seeds/runner.py
```

### Root-level seed_*.py files

All 50+ `seed_*.py` files at the project root have been moved to `_ARCHIVE_TO_DELETE/`. They are archived, not deleted, to preserve history. They should NOT be used — use `seeds/runner.py` instead.

---

## 6. SQLite Coupling — What Changed

### `database.py` — PRAGMA isolation

Before: `STANDARD_PRAGMAS` (WAL mode, busy_timeout, etc.) were applied unconditionally on every `get_db()` call, even for PostgreSQL connections.

After: Pragmas are only applied when `DB_ENGINE=sqlite` (the default). For PostgreSQL (`DB_ENGINE=postgresql`), pragmas list is empty.

```python
# In database.py
_DB_ENGINE = os.environ.get('DB_ENGINE', 'sqlite').lower()
_is_sqlite = _DB_ENGINE != 'postgresql'

STANDARD_PRAGMAS = [...] if _is_sqlite else []

def get_db():
    if _is_sqlite:
        # Apply pragmas
    else:
        # Return psycopg2 connection directly
```

### `models/base.py` — SQLAlchemy engine factory

Provides DB-agnostic engine creation:
- SQLite: Uses `sqlite:///` URL with WAL pragma event listener
- PostgreSQL: Uses `postgresql://` URL with `NullPool`

### `migrations/env.py` — Dual DB support

```python
# Resolves dynamically from environment
if db_engine == 'postgresql':
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"
else:
    return f"sqlite:///{db_path}"
```

### PostgreSQL readiness — Remaining blockers

1. `database.py` uses raw `sqlite3` (row factory, type handling) throughout — not PostgreSQL compatible
2. Some raw SQL uses SQLite-specific functions (`IFNULL`, `julianday()`, `strftime()`)
3. `database.py::add_column_if_safe` uses SQLite `ALTER TABLE ADD COLUMN` nuances
4. Per-model `get_db()` functions in `grc_models.py`, `btp_models.py`, etc. duplicate connection logic

A full PostgreSQL migration requires replacing raw `sqlite3` usage with SQLAlchemy across the query layer. This is a larger effort scoped for a future iteration.

---

## 7. Anti-Patterns Removed

### 1. `workflow_models.py` auto-init on import

**Before:** `workflow_models.py` called `initialize_workflow_schema()` at module import time, creating tables and seeding demo data on import. This caused:
- Schema creation during normal imports (e.g., during testing, route imports)
- Duplicate seeding on every import

**After:** The auto-init call at end of file has been **removed**. Tables are created through Alembic migrations. Manual initialization requires explicit call: `initialize_workflow_schema()`.

### 2. `seed_grc_comprehensive_data()` called at startup

**Before:** `bootstrap.py` called `seed_grc_comprehensive_data()` from `seed_grc_data.py` at every app startup.

**After:** This call has been **removed**. GRC data seeding is handled through the organized `seeds/` framework.

---

## 8. Project Structure

```
WHDASH/
  # Migration Framework
  alembic.ini                           # Alembic configuration
  migrate.py                            # CLI: python migrate.py ...
  migrations/
    __init__.py                        # Lazy public API
    env.py                             # Dual-DB migration environment
    migrate_app.py                     # Safety helpers, ensure_db_current, stamp_baseline
    script.py.mako                     # Migration template
    versions/
      001_initial_schema.py            # Core tables (companies, users, roles, etc.)
      002_current_schema_marker.py     # Baseline marker
      003_consolidate_scattered_tables.py  # Module tables (planning, workflow, GRC, BTP...)

  # Database Layer
  database.py                          # Runtime queries (raw sqlite3, SQLite-conditional pragmas)
  models/
    __init__.py                        # Package marker
    base.py                           # SQLAlchemy Base + engine factory (dual-DB)
  config.py                           # DB config (DB_ENGINE, PostgreSQL settings)

  # Seeding
  seeds/
    runner.py                          # ONLY seed entry point
    bootstrap/core_reference.py        # Bootstrap tier
    demo/                             # Demo tier

  # DEPRECATED (phasing out):
  schema.sql                          # Legacy schema reference
  sqlite_schema.sql                   # Legacy SQLite schema (used by bootstrap for base schema only)
  application/database_init.py        # Being replaced by migrations
  _ARCHIVE_TO_DELETE/                # Archived: 50+ old seed_*.py files
```

---

## 9. Compatibility & Data Safety

### Existing databases (pre-Alembic)

- **Safe**: `stamp_baseline_if_needed()` detects missing `alembic_version` table and stamps the baseline
- No destructive changes — `CREATE TABLE IF NOT EXISTS` preserves existing tables
- Pre-Alembic tables are marked as present and migrations build on top normally

### New deployments

- Fresh databases get full schema via `ensure_db_current()` at first startup
- All schema created through Alembic, no scattered init functions needed

### Production migrations

```bash
# Required before production migration:
# 1. Take a full backup of the database

# 2. Preview changes safely:
python migrate.py upgrade --sql

# 3. Apply with safety bypass (after backup confirmed):
SKIP_MIGRATION_SAFETY=1 python migrate.py upgrade
```

---

## 10. Remaining Future Improvements

1. **Full per-module migrations**: Build dedicated Alembic migrations for each module's tables (`planning_models`, `finance_models`, `hr_models`, `wms_schema`, etc.) instead of the catch-all 003 consolidation
2. **SQLAlchemy ORM migration**: Replace raw `sqlite3` in `database.py` with SQLAlchemy sessions for full PostgreSQL compatibility
3. **Remove init_*() safety net**: After all modules have proper migrations, remove the deprecated `init_*()` calls from `bootstrap.py`
4. **PostgreSQL connection pooling**: Configure SQLAlchemy `QueuePool` when `DB_ENGINE=postgresql`
5. **CI migration tests**: Add automated tests that verify migrations apply cleanly on both SQLite and PostgreSQL
6. **Seed coverage**: Migrate remaining archived seed functions into `seeds/bootstrap/` or `seeds/demo/`

---

## 11. Manual QA Checklist

After deploying this remediation:

- [ ] `python migrate.py current` shows current migration revision
- [ ] `python migrate.py history` shows at least 3 revisions
- [ ] `python migrate.py upgrade` runs without errors on fresh DB
- [ ] Application starts without `CREATE TABLE` errors
- [ ] `python seeds/runner.py --mode bootstrap` runs without errors
- [ ] `python seeds/runner.py --mode demo` runs without errors
- [ ] `python app.py` starts the Flask app
- [ ] `alembic_version` table exists and has `002_current_schema_marker` stamped
- [ ] `SEED_MODE=none python seeds/runner.py` runs silently
- [ ] No `CREATE TABLE` errors in application logs during startup
- [ ] Importing `workflow_models.py` does NOT create tables automatically
- [ ] `python migrate.py current` after fresh `python app.py` startup shows current head
