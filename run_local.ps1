# MMDx Local Development Startup Script for Windows (PowerShell)
# ================================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Load .env file if it exists
$envFile = Join-Path $ScriptDir ".env"
if (Test-Path $envFile) {
    Write-Host "Loading environment from .env..."
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
        }
    }
}

# Check for virtual environment
if (Test-Path ".venv") {
    Write-Host "Activating virtual environment..."
    & ".venv\Scripts\Activate.ps1"
} else {
    Write-Host "Note: No .venv found, using system Python"
}

# Check dependencies
try {
    python -c "import flask" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing dependencies..."
        pip install -r requirements.txt
    }
} catch {
    Write-Host "Installing dependencies..."
    pip install -r requirements.txt
}

Write-Host ""
Write-Host "Starting MMDx on http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

# Set defaults if not set
if (-not $env:FLASK_ENV) { $env:FLASK_ENV = "development" }
if (-not $env:SECRET_KEY) { $env:SECRET_KEY = "dev-secret-key-change-in-production-12345" }
if (-not $env:ADMIN_PASSWORD) { $env:ADMIN_PASSWORD = "admin" }
if (-not $env:DATABASE_PATH) { $env:DATABASE_PATH = "warehouse.db" }
if (-not $env:FLASK_DEBUG) { $env:FLASK_DEBUG = "1" }
if (-not $env:FLASK_RUN_HOST) { $env:FLASK_RUN_HOST = "127.0.0.1" }
if (-not $env:PORT) { $env:PORT = "5000" }

# Run Flask app
python app.py
