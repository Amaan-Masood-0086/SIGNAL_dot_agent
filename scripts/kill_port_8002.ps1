# Restart the backend on port 8002 (kill stale process only if it is python/uvicorn).
$ErrorActionPreference = 'Stop'
$conn = Get-NetTCPConnection -LocalPort 8002 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($conn) {
    $proc = Get-Process -Id $conn.OwningProcess
    if ($proc.ProcessName -eq 'python') {
        Write-Host "Killing stale backend PID $($proc.Id)"
        Stop-Process -Id $proc.Id -Force
        Start-Sleep -Seconds 2
    } else {
        Write-Host "Port 8002 held by $($proc.ProcessName) - not killing"
        exit 1
    }
} else {
    Write-Host "Port 8002 free"
}
