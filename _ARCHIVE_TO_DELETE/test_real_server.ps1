# Test with authentication via cookie
$baseUrl = "http://localhost:5000"

# First, get the login page to get any initial cookies
$loginPage = Invoke-WebRequest -Uri "$baseUrl/login" -UseBasicParsing -SessionVariable session
Write-Host "Login page status: $($loginPage.StatusCode)"

# Login with credentials
$loginResult = Invoke-WebRequest -Uri "$baseUrl/login" -UseBasicParsing -SessionVariable session -Method POST -Body @{
    username = "admin"
    password = "admin123"
} -Maximum_redirection 0 -ErrorAction SilentlyContinue

Write-Host "Login status: $($loginResult.StatusCode)"

# Now access the notifications page with the session cookie
$notifications = Invoke-WebRequest -Uri "$baseUrl/admin/notifications" -UseBasicParsing -WebSession $session
Write-Host "Notifications status: $($notifications.StatusCode)"
Write-Host "Content length: $($notifications.Content.Length)"

# Show first 500 chars
Write-Host "`n=== First 500 chars ==="
Write-Host $notifications.Content.Substring(0, [Math]::Min(500, $notifications.Content.Length))

# Show error if any
if ($notifications.Content -match "Error|Traceback|Exception") {
    Write-Host "`n=== Error detected ==="
    $notifications.Content -match ".{0,200}Error.{0,200}" | ForEach-Object { Write-Host $_ }
}