# Wait for the Docker daemon, then bring up the SIGNAL Postgres container.
$ok = $false
for ($i = 0; $i -lt 40; $i++) {
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { $ok = $true; break }
    Start-Sleep -Seconds 3
}
if (-not $ok) { Write-Output "docker NOT ready"; exit 1 }
Write-Output "docker ready"

Set-Location "s:\Projects\Hackthon Project\SIGNAL_dot_agent"
docker compose up -d db
if ($LASTEXITCODE -ne 0) { Write-Output "compose up FAILED"; exit 1 }

# Wait until Postgres accepts connections with the app credentials.
$ready = $false
for ($i = 0; $i -lt 40; $i++) {
    docker exec signal_dot_agent-db-1 pg_isready -U signal -d signal_dev 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { $ready = $true; break }
    Start-Sleep -Seconds 2
}
if ($ready) { Write-Output "postgres ready" } else { Write-Output "postgres NOT ready"; exit 1 }
