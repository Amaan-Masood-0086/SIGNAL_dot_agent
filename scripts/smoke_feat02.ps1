# FEAT-02 live smoke test: login -> intake (estimated mode) -> profile read.
# Throwaway dev script; targets local servers only.
$ErrorActionPreference = 'Stop'
$base = 'http://localhost:3000'
$origin = @{ Origin = $base }

# 1. Login (sets HttpOnly session cookie server-side)
$login = Invoke-WebRequest -Uri "$base/api/auth/login" -Method POST `
    -Headers ($origin + @{ 'Content-Type' = 'application/json' }) `
    -Body '{"email":"synthetic-staff@signal.example","password":"synthetic"}' `
    -UseBasicParsing
Write-Output ("LOGIN " + $login.StatusCode + " " + $login.Content)

# Production-mode next start sets the Secure flag, so .NET's cookie jar
# drops it over plain http. Forward it manually — the app never sees the
# difference, and Secure-over-HTTPS is the correct production behavior.
$setCookie = $login.Headers['Set-Cookie']
if (-not $setCookie) { Write-Output "FAIL: no Set-Cookie on login"; exit 1 }
Write-Output ("COOKIE signal_session (Secure flag present: " + ($setCookie -match 'Secure') + ")")

# Rebuild the cookie manually in a jar WITHOUT the Secure flag (the browser
# and jar both drop Secure cookies over plain http). Harness-only accommodation
# for local smoke; production runs over HTTPS where Secure is enforced.
$pair = ($setCookie -split ';')[0]
$value = ($pair -split '=', 2)[1]
$sess = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$jarCookie = New-Object System.Net.Cookie('signal_session', $value, '/', 'localhost')
$sess.Cookies.Add($jarCookie)
$authHeaders = $origin

# 2. Intake — estimated-age mode (ADR-02)
try {
    $intake = Invoke-WebRequest -Uri "$base/api/children" -Method POST `
        -Headers ($authHeaders + @{ 'Content-Type' = 'application/json' }) `
        -Body '{"name":"Smoke Child","dob_confirmed":false,"estimated_age_range":"30-36 months","estimated_age_note":"smoke test"}' `
        -WebSession $sess -UseBasicParsing
} catch {
    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    Write-Output ("INTAKE FAIL " + $_.Exception.Response.StatusCode.value__ + " body=" + $reader.ReadToEnd())
    exit 1
}
Write-Output ("INTAKE " + $intake.StatusCode + " " + $intake.Content)

$childId = ($intake.Content | ConvertFrom-Json).child.id

# 3. Profile read
$profileRead = Invoke-WebRequest -Uri "$base/api/children/$childId" `
    -Headers $authHeaders -WebSession $sess -UseBasicParsing
Write-Output ("PROFILE " + $profileRead.StatusCode + " " + $profileRead.Content)

# 4. Negative: confirmed mode without dob must 422
try {
    Invoke-WebRequest -Uri "$base/api/children" -Method POST `
        -Headers ($authHeaders + @{ 'Content-Type' = 'application/json' }) `
        -Body '{"name":"Bad Child","dob_confirmed":true}' `
        -WebSession $sess -UseBasicParsing | Out-Null
    Write-Output "NEGATIVE FAIL: expected 422"
} catch {
    $code = $_.Exception.Response.StatusCode.value__
    Write-Output ("NEGATIVE " + $code + " (expected 422)")
}

# 5. Unauthenticated request must 401
try {
    Invoke-WebRequest -Uri "$base/api/children/$childId" -Headers $origin -UseBasicParsing | Out-Null
    Write-Output "AUTH FAIL: expected 401"
} catch {
    $code = $_.Exception.Response.StatusCode.value__
    Write-Output ("UNAUTH " + $code + " (expected 401)")
}
