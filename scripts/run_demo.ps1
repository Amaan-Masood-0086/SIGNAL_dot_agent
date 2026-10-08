# One command to bring SIGNAL up for a demo, from a cold start.
#
#   .\scripts\run_demo.ps1            # start (keeps existing data)
#   .\scripts\run_demo.ps1 -Reset     # wipe the dev database first -> clean demo data
#   .\scripts\run_demo.ps1 -Rebuild   # also rebuild the frontend
#
# Local synthetic data only. Reads no secrets: it never prints or edits .env. The
# only values it sets are the documented dev-only database URLs, as process
# environment variables for the two servers it starts (they win over .env).
param(
    [switch]$Reset,
    [switch]$Rebuild
)
# Continue, not Stop: Windows PowerShell 5.1 turns any native-command stderr line
# (alembic logs to stderr) into a terminating error. Exit codes are checked by hand.
$ErrorActionPreference = 'Continue'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
$py = Join-Path $backend '.venv\Scripts\python.exe'

function Step($text) { Write-Host "`n== $text" -ForegroundColor Green }
function Fail($text) { Write-Host "FAILED: $text" -ForegroundColor Red; exit 1 }

if (-not (Test-Path $py)) { Fail "backend venv missing. See README: python -m venv .venv; pip install -r requirements.lock.txt" }
if (-not (Test-Path (Join-Path $frontend 'node_modules'))) { Fail "frontend dependencies missing. Run: cd frontend; npm ci" }
if (-not (Test-Path (Join-Path $backend '.env'))) { Fail "backend\.env missing. Run: cd backend; python scripts\write_dev_env.py" }

# ---- 1. Docker + database ---------------------------------------------------
Step "Docker"
$ok = $false
for ($i = 0; $i -lt 40; $i++) {
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { $ok = $true; break }
    if ($i -eq 0) { Write-Host "waiting for Docker Desktop..." }
    Start-Sleep -Seconds 3
}
if (-not $ok) { Fail "Docker is not running. Start Docker Desktop and try again." }

# 5432 is often taken by another project's Postgres; fall back to 5433.
$dbPort = 5432
if (Get-NetTCPConnection -LocalPort 5432 -State Listen -ErrorAction SilentlyContinue) {
    $mine = docker ps --filter "name=signal_dot_agent-db-1" --format "{{.Ports}}" 2>$null
    if ($mine -notmatch '5432->5432') { $dbPort = 5433 }
}
$env:SIGNAL_DB_PORT = "$dbPort"
Step "Database on port $dbPort"
Push-Location $root
docker compose up -d db 2>&1 | ForEach-Object { "$_" }
if ($LASTEXITCODE -ne 0) { Pop-Location; Fail "docker compose up failed" }
Pop-Location

$ready = $false
for ($i = 0; $i -lt 40; $i++) {
    docker exec signal_dot_agent-db-1 pg_isready -U signal -d signal_dev 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { $ready = $true; break }
    Start-Sleep -Seconds 2
}
if (-not $ready) { Fail "Postgres did not become ready" }

# Dev-only credentials, documented in the README and the migration. Not secrets.
$env:DATABASE_URL = "postgresql+psycopg://signal:signal_dev_only@localhost:$dbPort/signal_dev"
$env:TENANT_DATABASE_URL = "postgresql+psycopg://signal_app:signal_app@localhost:$dbPort/signal_dev"

# ---- 2. Stop old servers first (they hold DB connections) --------------------
foreach ($p in 8002, 3000) {
    $c = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($c) {
        $proc = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
        if ($proc -and $proc.ProcessName -in 'python', 'node') { Stop-Process -Id $proc.Id -Force; Start-Sleep -Seconds 1 }
        elseif ($proc) { Fail "port $p is held by $($proc.ProcessName); not killing it" }
    }
}

# ---- 3. Schema + data --------------------------------------------------------
if ($Reset) {
    Step "Reset dev database (synthetic data only)"
    docker exec signal_dot_agent-db-1 psql -U signal -d postgres -c "DROP DATABASE IF EXISTS signal_dev WITH (FORCE)" | Out-Null
    docker exec signal_dot_agent-db-1 psql -U signal -d postgres -c "CREATE DATABASE signal_dev" | Out-Null
    # Cluster-wide role from a previous run; migration 0001 recreates it.
    docker exec signal_dot_agent-db-1 psql -U signal -d postgres -c "DROP ROLE IF EXISTS signal_app" 2>&1 | Out-Null
}

Step "Migrations, knowledge base, synthetic data"
Push-Location $backend
& $py -m alembic upgrade head 2>&1 | Select-Object -Last 2
if ($LASTEXITCODE -ne 0) { Pop-Location; Fail "alembic upgrade failed" }
& $py scripts\ingest_knowledge_base.py
& $py scripts\seed_synthetic_tenant.py
& $py scripts\seed_admin.py --email root@signal.example
& $py scripts\seed_demo_children.py
Pop-Location

# ---- 4. Servers --------------------------------------------------------------
Step "Backend on 8002"
Start-Process -FilePath $py -ArgumentList '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8002', '--no-server-header' `
    -WorkingDirectory $backend -WindowStyle Hidden

if ($Rebuild -or -not (Test-Path (Join-Path $frontend '.next\BUILD_ID'))) {
    Step "Frontend build (about a minute)"
    Push-Location $frontend
    npm.cmd run build
    $code = $LASTEXITCODE
    Pop-Location
    if ($code -ne 0) { Fail "frontend build failed" }
}
Step "Frontend on 3000"
Start-Process -FilePath 'npm.cmd' -ArgumentList 'run', 'start' -WorkingDirectory $frontend -WindowStyle Hidden

# ---- 5. Verify ---------------------------------------------------------------
Step "Checks"
$health = $null
for ($i = 0; $i -lt 20; $i++) {
    $health = & curl.exe -s -m 3 http://127.0.0.1:8002/health
    if ($health) { break }
    Start-Sleep -Seconds 1
}
$page = $null
for ($i = 0; $i -lt 30; $i++) {
    $page = & curl.exe -s -m 3 -o NUL -w '%{http_code}' http://localhost:3000/login
    if ($page -eq '200') { break }
    Start-Sleep -Seconds 1
}
if (-not $health) { Fail "backend did not answer on 8002" }
if ($page -ne '200') { Fail "frontend login page returned '$page'" }

Write-Host "`nSIGNAL is up." -ForegroundColor Green
Write-Host "  App:      http://localhost:3000"
Write-Host "  Caretaker synthetic-staff@signal.example  (any password, synthetic mode)"
Write-Host "  Admin     root@signal.example             (any password, synthetic mode)"
Write-Host "  Sign-in is throttled to 5 per 5 minutes per account, and a session lasts 15 minutes."
Write-Host "  Database: localhost:$dbPort"
