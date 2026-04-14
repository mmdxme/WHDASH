$response = Invoke-WebRequest -Uri "http://localhost:5000/tasks/dashboard" -TimeoutSec 5
$response.StatusCode
$response.BaseResponse.ResponseUri
