# Restart both SIGNAL servers with the latest code/build.
$ErrorActionPreference = 'SilentlyContinue'

# Backend (port 8002)
& "$PSScriptRoot\kill_port_8002.ps1"

# Frontend (port 3000)
$conn = Get-NetTCPConnection -LocalPort 3000 -State Listen | Select-Object -First 1
if ($conn) { Stop-Process -Id $conn.OwningProcess -Force; Write-Output 'frontend stopped' }
Start-Sleep -Seconds 2

$backendDir = Join-Path $PSScriptRoot '..\backend'
$frontendDir = Join-Path $PSScriptRoot '..\frontend'

Start-Process -FilePath (Join-Path $backendDir '.venv\Scripts\python.exe') `
  -ArgumentList '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8002' `
  -WorkingDirectory $backendDir -WindowStyle Hidden
Write-Output 'backend starting on 8002'

Start-Process -FilePath 'npm.cmd' -ArgumentList 'run', 'start' `
  -WorkingDirectory $frontendDir -WindowStyle Hidden
Write-Output 'frontend starting on 3000'

Start-Sleep -Seconds 10
$health = & curl.exe -s -m 5 http://127.0.0.1:8002/health
Write-Output "backend health: $health"
$front = & curl.exe -s -m 5 -o NUL -w '%{http_code}' http://localhost:3000/login
Write-Output "frontend login page: $front"
