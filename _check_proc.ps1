$proc = Get-Process -Id 32652 -ErrorAction SilentlyContinue
if ($proc) { Write-Host "PID 32652: $($proc.ProcessName)" }
$proc2 = Get-Process -Id 32788 -ErrorAction SilentlyContinue
if ($proc2) { Write-Host "PID 32788: $($proc2.ProcessName)" }