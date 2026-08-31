$conn = Get-NetTCPConnection -LocalPort 8002 -State Listen -ErrorAction SilentlyContinue
if ($conn) {
    foreach ($c in $conn) {
        $proc = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
        Write-Host "PID $($c.OwningProcess) ($($proc.ProcessName))"
    }
} else {
    Write-Host "nothing listening on 8002"
}
try {
    $r = Invoke-WebRequest -Uri http://localhost:8002/health -UseBasicParsing -TimeoutSec 5
    Write-Host "health: $($r.StatusCode) $($r.Content)"
} catch {
    Write-Host "health failed: $($_.Exception.Message)"
}
