$pythonProcs = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*pythoncore*" }
foreach ($p in $pythonProcs) {
    Write-Host "Python PID=$($p.Id) Path=$($p.Path) StartTime=$($p.StartTime)"
}

# Also check the modules loaded - can't easily do that but let me check the server startup
# Let me look at the actual app_factory.py from the disk
$afLines = Get-Content "C:\Users\sdads\WHDASH\app_factory.py" | Select-Object -First 5
Write-Host "`napp_factory.py first 5 lines:"
$afLines | ForEach-Object { Write-Host $_ }

# Check when app_factory.py was last modified
$afInfo = Get-Item "C:\Users\sdads\WHDASH\app_factory.py"
Write-Host "`napp_factory.py last modified: $($afInfo.LastWriteTime)"

# Check application/bootstrap.py
$bootInfo = Get-Item "C:\Users\sdads\WHDASH\application\bootstrap.py"
Write-Host "bootstrap.py last modified: $($bootInfo.LastWriteTime)"