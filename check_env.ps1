# Check if there's any environment variable or config that affects DATABASE_PATH
Write-Host "Checking current environment..."
Write-Host "PWD: $(Get-Location)"

# Check .env file
$envPath = Join-Path (Get-Location) ".env"
if (Test-Path $envPath) {
    Write-Host ".env file exists"
    Get-Content $envPath | Select-Object -First 10
} else {
    Write-Host ".env file does NOT exist"
}

# Check if there's a separate database
$dbFiles = Get-ChildItem -Filter "*.db"
Write-Host "`nDatabase files:"
$dbFiles | Format-Table Name, Length, LastWriteTime

# Check which database is actually being used by checking its users table
$warehouseDb = "warehouse.db"
if (Test-Path $warehouseDb) {
    Write-Host "`nChecking warehouse.db admin user..."
    $hash = sqlite3 $warehouseDb "SELECT password FROM users WHERE username='admin';"
    Write-Host "Hash: $hash"
}