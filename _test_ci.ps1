$resp = Invoke-WebRequest -Uri "http://localhost:5000/customer-intelligence/dashboard" -TimeoutSec 10 -UseBasicParsing -ErrorAction SilentlyContinue
if ($resp) {
    Write-Host "Status: $($resp.StatusCode)"
    if ($resp.StatusCode -eq 302 -or $resp.StatusCode -eq 301) {
        Write-Host "Redirect to: $($resp.Headers.Location)"
    }
} else {
    # Try with session/cookie to bypass auth redirect
    $session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
    $resp2 = Invoke-WebRequest -Uri "http://localhost:5000/login" -TimeoutSec 10 -UseBasicParsing -SessionVariable session
    Write-Host "Login page status: $($resp2.StatusCode)"
    $resp3 = Invoke-WebRequest -Uri "http://localhost:5000/customer-intelligence/dashboard" -WebSession $session -TimeoutSec 10 -UseBasicParsing
    Write-Host "After login attempt status: $($resp3.StatusCode)"
}

# Check if route exists
$allRoutes = Invoke-WebRequest -Uri "http://localhost:5000/health" -TimeoutSec 5 -UseBasicParsing
Write-Host "`nHealth check: $($allRoutes.Content)"
$routesResp = Invoke-WebRequest -Uri "http://localhost:5000/ready" -TimeoutSec 5 -UseBasicParsing
Write-Host "Ready check: $($routesResp.Content)"