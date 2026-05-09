$proc = Get-Process -Id 32652 -ErrorAction SilentlyContinue
if ($proc) {
    Write-Host "Process on port 5000: PID=$($proc.Id) $($proc.ProcessName)"
    Write-Host "    Started: $($proc.StartTime)"
    Write-Host "    Path: $($proc.Path)"
}
$pythonFiles = Get-ChildItem -Path . -Filter "*.py" | Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-1) } | Select-Object Name, LastWriteTime
if ($pythonFiles) {
    Write-Host "`nRecently modified Python files:"
    $pythonFiles | ForEach-Object { Write-Host "  $($_.Name) - $($_.LastWriteTime)" }
}