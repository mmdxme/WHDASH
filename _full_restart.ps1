# Kill all Flask server processes
$pids = @(32652, 50548, 8752, 37992, 32492, 16236)
foreach ($p in $pids) {
    $proc = Get-Process -Id $p -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Host "Killing PID $p..."
        $proc.Kill()
    }
}

Start-Sleep -Seconds 3

# Verify port is free
$listeners = Get-NetTCPConnection -LocalAddress 5000 -ErrorAction SilentlyContinue
if ($listeners) {
    Write-Host "Port 5000 still in use by PID $($listeners[0].OwningProcess)"
} else {
    Write-Host "Port 5000 is FREE"
    Write-Host "Starting fresh server..."
    Start-Process -FilePath "python" -ArgumentList "app.py" -WorkingDirectory "C:\Users\sdads\WHDASH" -WindowStyle Normal -PassThru
    Start-Sleep -Seconds 8
    $test = Invoke-WebRequest -Uri "http://localhost:5000/customer-intelligence/dashboard" -TimeoutSec 10 -UseBasicParsing -ErrorAction SilentlyContinue
    if ($test) {
        Write-Host "CI Dashboard Status: $($test.StatusCode)"
    } else {
        Write-Host "Server may still be starting..."
    }
}