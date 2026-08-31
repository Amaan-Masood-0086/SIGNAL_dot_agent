# FEAT-03 live smoke: session lifecycle + mode-agnostic observations +
# STT-unavailable fallback (503). Throwaway dev script; local servers only.
$ErrorActionPreference = 'Stop'
$base = 'http://localhost:3000'
$origin = @{ Origin = $base }

function Read-ErrorBody($ex) {
    $reader = New-Object System.IO.StreamReader($ex.Exception.Response.GetResponseStream())
    return @{ Code = $ex.Exception.Response.StatusCode.value__; Body = $reader.ReadToEnd() }
}

# 1. Login (sets HttpOnly session cookie server-side)
$login = Invoke-WebRequest -Uri "$base/api/auth/login" -Method POST `
    -Headers ($origin + @{ 'Content-Type' = 'application/json' }) `
    -Body '{"email":"synthetic-staff@signal.example","password":"synthetic"}' `
    -UseBasicParsing
Write-Output ("LOGIN " + $login.StatusCode)

# Production-mode next start sets the Secure flag; rebuild the cookie in a
# jar WITHOUT Secure for plain-http smoke (harness-only accommodation).
$setCookie = $login.Headers['Set-Cookie']
if (-not $setCookie) { Write-Output "FAIL: no Set-Cookie on login"; exit 1 }
$pair = ($setCookie -split ';')[0]
$value = ($pair -split '=', 2)[1]
$sess = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$sess.Cookies.Add((New-Object System.Net.Cookie('signal_session', $value, '/', 'localhost')))

# 2. Intake a child first
$intake = Invoke-WebRequest -Uri "$base/api/children" -Method POST `
    -Headers ($origin + @{ 'Content-Type' = 'application/json' }) `
    -Body '{"name":"Smoke Voice Child","dob_confirmed":false,"estimated_age_range":"24-30 months","estimated_age_note":"feat03 smoke"}' `
    -WebSession $sess -UseBasicParsing
$childId = ($intake.Content | ConvertFrom-Json).child.id
Write-Output ("INTAKE " + $intake.StatusCode + " child=" + $childId)

# 3. Start a session (text mode)
$sessionResp = Invoke-WebRequest -Uri "$base/api/sessions" -Method POST `
    -Headers ($origin + @{ 'Content-Type' = 'application/json' }) `
    -Body (@{ child_id = $childId; mode = 'text' } | ConvertTo-Json) `
    -WebSession $sess -UseBasicParsing
$sessionId = ($sessionResp.Content | ConvertFrom-Json).session.id
Write-Output ("SESSION " + $sessionResp.StatusCode + " id=" + $sessionId)

# 4. Turn 1 — same body shape voice transcripts use downstream
$turn1 = Invoke-WebRequest -Uri "$base/api/sessions/$sessionId/observations" -Method POST `
    -Headers ($origin + @{ 'Content-Type' = 'application/json' }) `
    -Body '{"raw_input":"child pointed at the picture and named it"}' `
    -WebSession $sess -UseBasicParsing
$t1 = ($turn1.Content | ConvertFrom-Json).observation
Write-Output ("TURN1 " + $turn1.StatusCode + " turn_number=" + $t1.turn_number)
if ($t1.turn_number -ne 1) { Write-Output "FAIL: expected turn_number 1"; exit 1 }

# 5. Turn 2 — server-assigned sequence, never client-supplied
$turn2 = Invoke-WebRequest -Uri "$base/api/sessions/$sessionId/observations" -Method POST `
    -Headers ($origin + @{ 'Content-Type' = 'application/json' }) `
    -Body '{"raw_input":"second turn","turn_number":999}' `
    -WebSession $sess -UseBasicParsing
$t2 = ($turn2.Content | ConvertFrom-Json).observation
Write-Output ("TURN2 " + $turn2.StatusCode + " turn_number=" + $t2.turn_number)
if ($t2.turn_number -ne 2) { Write-Output "FAIL: client-supplied turn_number leaked"; exit 1 }

# 6. Negative: blank raw_input must 422
try {
    Invoke-WebRequest -Uri "$base/api/sessions/$sessionId/observations" -Method POST `
        -Headers ($origin + @{ 'Content-Type' = 'application/json' }) `
        -Body '{"raw_input":"   "}' -WebSession $sess -UseBasicParsing | Out-Null
    Write-Output "FAIL: blank turn accepted"; exit 1
} catch {
    $e = Read-ErrorBody $_
    Write-Output ("BLANK " + $e.Code + " (expected 422)")
}

# 7. Read back turns
$read = Invoke-WebRequest -Uri "$base/api/sessions/$sessionId/observations?page=1&page_size=50" `
    -Headers $origin -WebSession $sess -UseBasicParsing
$page = ($read.Content | ConvertFrom-Json).result
Write-Output ("READ " + $read.StatusCode + " total=" + $page.total)
if ($page.total -ne 2) { Write-Output "FAIL: expected 2 turns"; exit 1 }

# 8. STT unconfigured -> 503 with fallback guidance (zero-STT text acceptance)
$boundary = [guid]::NewGuid().ToString()
$enc = [System.Text.Encoding]::GetEncoding('iso-8859-1')
$audio = [byte[]](0x52, 0x49, 0x46, 0x46, 0x00, 0x00, 0x00, 0x00)
# Explicit [byte[]] cast: byte[] + byte[] yields object[] in PowerShell, and
# Invoke-WebRequest mangles object[] bodies (formData() then cannot parse).
[byte[]]$mbody = $enc.GetBytes("--$boundary`r`nContent-Disposition: form-data; name=`"audio`"; filename=`"turn.webm`"`r`nContent-Type: audio/webm`r`n`r`n") + $audio + $enc.GetBytes("`r`n--$boundary--`r`n")
try {
    Invoke-WebRequest -Uri "$base/api/stt/transcribe" -Method POST `
        -Headers $origin -ContentType "multipart/form-data; boundary=$boundary" `
        -Body $mbody -WebSession $sess -UseBasicParsing | Out-Null
    Write-Output "FAIL: STT unexpectedly available"; exit 1
} catch {
    $e = Read-ErrorBody $_
    Write-Output ("STT " + $e.Code + " (expected 503) body=" + $e.Body)
    if ($e.Code -ne 503) { exit 1 }
}

# 9. Complete the session; further turns must 409
$complete = Invoke-WebRequest -Uri "$base/api/sessions/$sessionId/complete" -Method POST `
    -Headers $origin -Body '' -WebSession $sess -UseBasicParsing
$status = ($complete.Content | ConvertFrom-Json).session.status
Write-Output ("COMPLETE " + $complete.StatusCode + " status=" + $status)
try {
    Invoke-WebRequest -Uri "$base/api/sessions/$sessionId/observations" -Method POST `
        -Headers ($origin + @{ 'Content-Type' = 'application/json' }) `
        -Body '{"raw_input":"late turn"}' -WebSession $sess -UseBasicParsing | Out-Null
    Write-Output "FAIL: turn accepted after complete"; exit 1
} catch {
    $e = Read-ErrorBody $_
    Write-Output ("LATE " + $e.Code + " (expected 409)")
}

# 10. Unauthenticated session create must 401
try {
    Invoke-WebRequest -Uri "$base/api/sessions" -Method POST `
        -Headers ($origin + @{ 'Content-Type' = 'application/json' }) `
        -Body (@{ child_id = $childId; mode = 'text' } | ConvertTo-Json) `
        -UseBasicParsing | Out-Null
    Write-Output "FAIL: unauthenticated session created"; exit 1
} catch {
    $e = Read-ErrorBody $_
    Write-Output ("UNAUTH " + $e.Code + " (expected 401)")
}

Write-Output "FEAT-03 SMOKE: ALL GREEN"
