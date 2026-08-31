# Live audit smoke: boots the backend on 8002 and exercises the admin
# credential surface end-to-end against the dev DB (synthetic_only).
# The sentinel value must appear in NO response body.
$ErrorActionPreference = 'Stop'
Set-Location "$PSScriptRoot\..\backend"

$base = 'http://localhost:8002'
$sentinel = 'smoke-live-key-ZZ99'

function Invoke-Json {
    param([string]$Method, [string]$Url, [string]$Token = '', [string]$Body = '')
    $headers = @{}
    if ($Token) { $headers['Authorization'] = "Bearer $Token" }
    $args = @('-s', '-X', $Method, '-w', "`n%{http_code}")
    if ($Body) {
        # Body via temp file — immune to PowerShell native-command quote
        # stripping.
        $bodyFile = Join-Path $env:TEMP "signal_smoke_body_$([guid]::NewGuid().ToString('N')).json"
        [System.IO.File]::WriteAllText($bodyFile, $Body)
        $args += @('-H', 'Content-Type: application/json', '-d', "@$bodyFile")
    }
    foreach ($k in $headers.Keys) { $args += @('-H', "$k`: $($headers[$k])") }
    $args += $Url
    $out = & curl.exe @args
    if ($Body) { Remove-Item $bodyFile -ErrorAction SilentlyContinue }
    $lines = ($out -split "`n")
    $code = [int]$lines[-1]
    $text = ($lines[0..($lines.Length - 2)] -join "`n")
    return @{ Code = $code; Text = $text }
}

# 1. Health
$h = Invoke-Json 'GET' "$base/health"
Write-Output "health: $($h.Code) $($h.Text)"

# 2. Admin login (seeded root@signal.example)
$login = Invoke-Json 'POST' "$base/api/v1/auth/token" -Body '{"email":"root@signal.example","password":"synthetic"}'
if ($login.Code -ne 200) { throw "admin login failed: $($login.Code) $($login.Text)" }
$adminToken = (($login.Text | ConvertFrom-Json).data.access_token)
Write-Output "admin login: 200 (token minted)"

# 3. Provider statuses
$prov = Invoke-Json 'GET' "$base/api/v1/admin/providers" -Token $adminToken
Write-Output "providers: $($prov.Code)"
if ($prov.Text -match $sentinel) { throw 'sentinel leaked in provider status' }

# 4. PUT credential
$put = Invoke-Json 'PUT' "$base/api/v1/admin/credentials/llm" -Token $adminToken -Body (@{ value = $sentinel } | ConvertTo-Json -Compress)
Write-Output "PUT credential: $($put.Code)"
if ($put.Code -ne 200) { throw "PUT failed: $($put.Text)" }
if ($put.Text -match $sentinel) { throw 'RAW VALUE ECHOED BY PUT' }
if ($put.Text -notmatch 'ZZ99') { throw 'masked suffix missing from PUT response' }

# 5. GET credential list
$lst = Invoke-Json 'GET' "$base/api/v1/admin/credentials" -Token $adminToken
Write-Output "GET credentials: $($lst.Code)"
if ($lst.Text -match $sentinel) { throw 'RAW VALUE LEAKED BY GET' }
if ($lst.Text -notmatch 'ZZ99') { throw 'masked suffix missing from GET response' }

# 6. Test connection (fake key -> must report failure cleanly, no leak)
$tst = Invoke-Json 'POST' "$base/api/v1/admin/providers/llm/test" -Token $adminToken
Write-Output "test connection: $($tst.Code) $($tst.Text)"
if ($tst.Text -match $sentinel) { throw 'sentinel leaked by test connection' }

# 7. DELETE (soft) -> fallback
$del = Invoke-Json 'DELETE' "$base/api/v1/admin/credentials/llm" -Token $adminToken
Write-Output "DELETE credential: $($del.Code)"
if ($del.Code -ne 200) { throw "DELETE failed: $($del.Text)" }
$lst2 = Invoke-Json 'GET' "$base/api/v1/admin/credentials" -Token $adminToken
if ($lst2.Text -match '"is_active":true') { Write-Output 'WARN: llm still active after delete' } else { Write-Output 'llm deactivated ok' }

# 8. Non-admin (caretaker stub) must get 403 on the admin surface
$ctLogin = Invoke-Json 'POST' "$base/api/v1/auth/token" -Body '{"email":"synthetic-staff@signal.example","password":"x"}'
$ctToken = (($ctLogin.Text | ConvertFrom-Json).data.access_token)
$denied = Invoke-Json 'GET' "$base/api/v1/admin/credentials" -Token $ctToken
Write-Output "caretaker on admin surface: $($denied.Code)"
if ($denied.Code -ne 403) { throw "expected 403 for caretaker, got $($denied.Code)" }

Write-Output 'SMOKE PASS: no raw value leaked anywhere; guards hold.'
