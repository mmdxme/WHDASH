# Dead Code Backup

These files were removed from production on 2026-05-02 during code quality improvements.

## Files Removed

| File | Purpose |
|------|---------|
| `analyze_all_tables.py` | Debug script for table analysis |
| `analyze_tables.py` | Debug script for table analysis |
| `check_db_state.py` | Debug script for database state |
| `check_seeded.py` | Debug script for checking seed data |
| `check_tables.py` | Debug script for table validation |
| `debug_fk.py` | Debug script for foreign key analysis |
| `debug_seed.py` | Debug script for seed debugging |
| `seed_aggressive.py` | Aggressive seeding script |
| `seed_final_master.py` | Master seed script |
| `wms_schema.py` | Duplicate schema definition |

## Review Instructions

1. Review each file to confirm no unique logic
2. Extract any useful functions or constants
3. Move to permanent archive (e.g., `archive/YYYY-MM/`)

## Restoration

If any file needs to be restored:
```bash
git checkout HEAD -- <filename>
```

## Permanent Deletion

After review, these files can be safely deleted:
```bash
rm -rf DEAD_CODE_BACKUP/
```