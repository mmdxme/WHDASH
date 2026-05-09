"""
Baseline Marker: Current Production Schema
==========================================
Revision ID: 002_current_schema_marker
Revises: 001_initial_schema
Create Date: 2026-05-06

IMPORTANT: This migration exists for correctness tracking only.

This is a "baseline marker" migration. It does NOT make any schema changes.
Its purpose is to record that the Alembic version table is now the system of
record, even though tables already exist in the database from previous
scattered init_* calls.

Why this migration exists:
  The production database already contains all tables created by the
  scattered init_*() functions in various route files and model modules.
  Alembic needs to know the current state BEFORE it can safely manage
  future schema changes.

After this marker, ALL schema changes must go through new Alembic migrations.

Future developers MUST NOT use the old scattered init_* patterns.
All schema evolution must use:
  python migrate.py revision -m "description"
  python migrate.py upgrade

No CREATE TABLE in route files, model files, or app startup.
"""

from alembic import op

revision = '002_current_schema_marker'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This is a marker-only migration.
    # No schema changes - the baseline is already in place.
    pass


def downgrade() -> None:
    # No reverse - this marker must not be removed.
    pass