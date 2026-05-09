# MMDx Local Setup Guide

## Overview

MMDx (Warehouse Dashboard) is a Flask-based enterprise management platform running on SQLite.

## Prerequisites

- Python 3.8+ (64-bit)
- Windows 10/11 or Windows Server
- pip package manager

## Quick Start

### Option 1: PowerShell (Recommended)

```powershell
.\run_local.ps1
```

### Option 2: Batch File

```cmd
run_local.bat
```

### Option 3: Manual

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
$env:FLASK_ENV = "development"
$env:SECRET_KEY = "dev-secret-key-change-in-production-12345"
$env:ADMIN_PASSWORD = "admin"
$env:DATABASE_PATH = "warehouse.db"

# Run the app
python app.py
```

## Access

- **URL**: http://127.0.0.1:5000
- **Default Admin Login**:
  - Username: `admin`
  - Password: `password` (or value of ADMIN_PASSWORD env var)

## First-Time Setup

1. The app will automatically create the SQLite database (`warehouse.db`) on first run
2. The database schema will be initialized from `sqlite_schema.sql`
3. Default admin user is seeded automatically

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| FLASK_ENV | production | Set to `development` for debug mode |
| SECRET_KEY | (required in prod) | Session encryption key |
| ADMIN_PASSWORD | (none) | Set to seed admin password on startup |
| DATABASE_PATH | warehouse.db | Path to SQLite database file |
| FLASK_DEBUG | 0 | Set to 1 for debug mode |
| PORT | 5000 | Server port |

## Project Structure

```
MMDx/
├── app.py              # Main Flask application
├── database.py        # Database connection utilities
├── config.py          # Configuration module
├── settings.py        # Settings management
├── sqlite_schema.sql  # Database schema
├── requirements.txt   # Python dependencies
├── .env              # Local environment (create from .env.example)
├── run_local.bat     # Windows batch launcher
├── run_local.ps1     # PowerShell launcher
└── templates/        # Jinja2 templates
```

## Database

The app uses SQLite with WAL mode for better concurrency. Database file is created automatically at `warehouse.db` in the project root.

### Key Tables

- `companies` - Subsidiaries/warehouses
- `users` - User accounts
- `roles` - Role-based access control
- `parts` - Master parts catalog
- `inventory` - Stock levels per company
- `movements` - Stock movement history
- `vitalities` - Part classification (Fast Moving, Slow Moving, etc.)

## Troubleshooting

### Server Won't Start

1. Check Python version: `python --version`
2. Install dependencies: `pip install -r requirements.txt`
3. Check port availability: `netstat -ano | findstr :5000`
4. Check database file permissions

### Login Fails

1. Set admin password via environment: `$env:ADMIN_PASSWORD = "yourpassword"`
2. Or check database directly for seeded admin user
3. Default seeded password is `password`

### Template Errors

1. Ensure all required tables exist in database
2. Check that `sqlite_schema.sql` hasn't been modified incorrectly
3. Try deleting the database and letting it reinitialize

### Import Errors

If you see missing module errors, install all dependencies:

```bash
pip install Flask==3.1.3 pandas==3.0.1 openpyxl==3.1.5 gunicorn requests==2.31.0 playwright==1.50.0
```

## Development Notes

- App runs in debug mode when `FLASK_ENV=development`
- Debug mode enables auto-reload and detailed error pages
- SQLite database is stored at `warehouse.db`
- Upload folder is `static/uploads/avatars`
- Session type is filesystem-based
