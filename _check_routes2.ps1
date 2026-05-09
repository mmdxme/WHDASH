$resp = Invoke-WebRequest -Uri "http://localhost:5000/health" -TimeoutSec 5 -UseBasicParsing
Write-Host "Health: $($resp.Content)"

$resp2 = Invoke-WebRequest -Uri "http://localhost:5000/login" -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue
if ($resp2) {
    Write-Host "Login page status: $($resp2.StatusCode)"
} else {
    Write-Host "Login page: ERROR or not found"
}

# Get all routes via the app's route info
$resp3 = Invoke-WebRequest -Uri "http://localhost:5000/customer-intelligence" -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue
if ($resp3) {
    Write-Host "Root CI: $($resp3.StatusCode)"
} else {
    Write-Host "Root CI: ERROR"
}

# Try without trailing slash
$resp4 = Invoke-WebRequest -Uri "http://localhost:5000/dashboard" -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue
if ($resp4) {
    Write-Host "Dashboard: $($resp4.StatusCode)"
} else {
    Write-Host "Dashboard: ERROR"
}