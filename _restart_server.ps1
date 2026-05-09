# Kill old server process
$proc = Get-Process -Id 32652 -ErrorAction SilentlyContinue
if ($proc) {
    Write-Host "Stopping old server (PID $($proc.Id))..."
    $proc.Kill()
    Start-Sleep -Seconds 2
}

# Start new server
Write-Host "Starting new server..."
Set-Location "C:\Users\sdads\WHDASH"
Start-Process -FilePath "python" -ArgumentList "app.py" -WindowStyle Normal

Start-Sleep -Seconds 5

# Test
try {
    $resp = Invoke-WebRequest -Uri "http://localhost:5000/customer-intelligence/dashboard" -TimeoutSec 5 -MaximumRetryCount 1 -ErrorAction Stop
    Write-Host "Status: $($resp.StatusCode)"
} catch {
    Write-Host "Server may need more time to start, or check manually"
}