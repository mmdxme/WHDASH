# ==============================================================================
# Migration Management CLI
# ==============================================================================
# Alembic migration commands for the MMDx database layer.
#
# Usage:
#   python migrate.py                              # Show help
#   python migrate.py init                        # Initialize migrations (already done)
#   python migrate.py revision -m "description"   # Create new revision
#   python migrate.py upgrade                     # Apply all pending migrations
#   python migrate.py downgrade                    # Roll back one revision
#   python migrate.py history                     # Show migration history
#   python migrate.py current                     # Show current revision
#
# Environment:
#   DB_ENGINE=sqlite    (default) - use SQLite
#   DB_ENGINE=postgresql             - use PostgreSQL
#   DATABASE_PATH=warehouse.db      - SQLite path override
# ==============================================================================

import os
import sys

# Add project root to path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from alembic.config import CommandLine
from alembic import config


def main():
    """Run Alembic CLI via Python."""
    os.chdir(BASE_DIR)

    alembic_cfg = config.Config(
        os.path.join(BASE_DIR, 'alembic.ini'),
        ini_section='alembic',
    )
    # script_location is already set in alembic.ini to 'migrations'
    # (relative to the alembic.ini location)

    cli = CommandLine()
    # Strip first arg (script name 'migrate.py') before passing to Alembic
    args = sys.argv[1:] if len(sys.argv) > 1 else ['--help']
    sys.exit(cli.main(argv=args))


if __name__ == '__main__':
    main()
