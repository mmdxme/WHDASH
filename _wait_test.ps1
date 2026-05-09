$proc = Get-Process -Id 48964 -ErrorAction SilentlyContinue
if ($proc) {
    Write-Host "Server PID: $($proc.Id) | Path: $($proc.Path)"
}

# Wait more for server to be fully ready
Start-Sleep -Seconds 5

# Now test
$test = Invoke-WebRequest -Uri "http://localhost:5000/health" -TimeoutSec 10 -UseBasicParsing
Write-Host "Health: $($test.Content)"

# Try CI
$test2 = Invoke-WebRequest -Uri "http://localhost:5000/customer-intelligence/dashboard" -TimeoutSec 10 -UseBasicParsing -ErrorAction SilentlyContinue
if ($test2) {
    Write-Host "CI Dashboard: $($test2.StatusCode)"
} else {
    Write-Host "CI Dashboard: FAILED"
    $failedResp = Invoke-WebRequest -Uri "http://localhost:5000/customer-intelligence/dashboard" -TimeoutSec 10 -UseBasicParsing
    Write-Host "Error: $($failedResp.StatusDescription)"
}