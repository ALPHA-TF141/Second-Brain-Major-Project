<#
  JARVIS OS - FULL ERROR CHECK (PowerShell)
  =========================================
  Usage:  .\verify-jarvis.ps1

  Runs every automated check and stops at the first failure:

    1. ESLint                  - undefined vars / unimported JSX components (the
                                 "blank screen / red diagnostic" crash class)
    2. Static health check     - imports resolve, API wiring, python syntax
    3. API contract            - every URL the UI calls must exist on the backend
    4. Route render smoke      - renders AND mounts all 18 routes (no browser needed)
    5. Production build        - the bundle must compile
    6. Backend test suites     - 11 live functional suites
    7. Backend endpoint sweep  - boots the backend and calls every GET route
    8. Browser smoke test      - optional, loads all 18 routes in real Chromium
#>
$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot

$py = "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

function Step($n, $title) {
  Write-Host ""
  Write-Host "[$n/15] $title" -ForegroundColor Cyan
  $script:currentStep = "$n ($title)"
}

$failed = $false
$failedSteps = @()

# A step that prints an all-clear and STILL returns a non-zero code is the
# confusing case: the process died while shutting down (a native library being
# unloaded under a live background thread - sounddevice, onnxruntime, torch),
# after its verdict was written. Windows reports those as large or negative
# codes, so they are named here instead of leaving "scroll up for the [FAIL]
# lines" with no [FAIL] line to find.
function ExplainExit($code) {
  if ($code -lt 0 -or $code -gt 9000) {
    return "  <- this is a crash during shutdown, not a failed check"
  }
  return ""
}

function RecordFailure($code, $what) {
  $script:failed = $true
  $label = if ($what) { $what } else { $script:currentStep }
  $script:failedSteps += "  - step $label  (exit code $code)$(ExplainExit $code)"
}

Step 1 "ESLint (undefined vars / bad JSX)"
npm run lint
if ($LASTEXITCODE -ne 0) { RecordFailure $LASTEXITCODE "" }

if (-not $failed) {
  Step 2 "Static health check (imports, routes, API wiring, python syntax)"
  & $py scripts\health_check.py
  if ($LASTEXITCODE -ne 0) { RecordFailure $LASTEXITCODE "" }
}

if (-not $failed) {
  Step 3 "API contract (UI calls <-> backend routes)"
  npm run check:api
  if ($LASTEXITCODE -ne 0) { RecordFailure $LASTEXITCODE "" }
}

if (-not $failed) {
  Step 4 "Route render smoke test (all 18 routes render + mount)"
  npm run smoke
  if ($LASTEXITCODE -ne 0) { RecordFailure $LASTEXITCODE "" }
}

if (-not $failed) {
  Step 5 "Production build"
  npm run build
  if ($LASTEXITCODE -ne 0) { RecordFailure $LASTEXITCODE "" }
}

if (-not $failed) {
  Step 6 "Backend test suites"
  Push-Location backend
  $backendPy = ".venv\Scripts\python.exe"
  if (-not (Test-Path $backendPy)) { $backendPy = "python" }
  & $backendPy test_all_endpoints.py
  $rc = $LASTEXITCODE
  Pop-Location
  if ($rc -ne 0) { RecordFailure $rc "6 (Backend test suites)" }
}

if (-not $failed) {
  Step 7 "Google integration test (offline fake-Google suite)"
  Push-Location backend
  & $backendPy test_google_integration.py
  $grc = $LASTEXITCODE
  Pop-Location
  if ($grc -ne 0) { RecordFailure $grc "7 (Google integration test)" }
}

if (-not $failed) {
  Step 8 "Mail + Calendar test (fake IMAP server + iCal parser)"
  Push-Location backend
  & $backendPy test_mail_calendar.py
  $mrc = $LASTEXITCODE
  Pop-Location
  if ($mrc -ne 0) { RecordFailure $mrc "8 (Mail + Calendar test)" }
}

if (-not $failed) {
  Step 9 "Mail -> memory ingestion test (fake IMAP, RAG retrieval proof)"
  Push-Location backend
  & $backendPy test_mail_ingestion.py
  $ingestRc = $LASTEXITCODE
  Pop-Location
  if ($ingestRc -ne 0) { RecordFailure $ingestRc "9 (Mail ingestion test)" }
}

if (-not $failed) {
  Step 10 "Orb voice loop (mic re-arm, TTS watchdog, wake word)"
  npm run test:orb
  if ($LASTEXITCODE -ne 0) { RecordFailure $LASTEXITCODE "" }
}

if (-not $failed) {
  Step 11 "Wake word + proactive voice (policy, quiet hours, dedupe, real model)"
  Push-Location backend
  & $backendPy test_proactive_voice.py
  $pvRc = $LASTEXITCODE
  Pop-Location
  if ($pvRc -ne 0) { RecordFailure $pvRc "11 (Wake word + proactive voice)" }
}

if (-not $failed) {
  Step 12 "Hands-free UI wiring (wake -> orb, speak -> voice)"
  npm run test:proactive
  if ($LASTEXITCODE -ne 0) { RecordFailure $LASTEXITCODE "" }
}

if (-not $failed) {
  Step 13 "Research layer (7 paper contributions + PersonalBrain-Bench)"
  Push-Location backend
  & $backendPy test_research_layer.py
  $rlRc = $LASTEXITCODE
  Pop-Location
  if ($rlRc -ne 0) { RecordFailure $rlRc "13 (Research layer)" }
}

if (-not $failed) {
  Step 14 "Backend endpoint sweep (boots backend, probes every GET route for 5xx)"
  & $py backend\verify_backend_endpoints.py
  if ($LASTEXITCODE -ne 0) { RecordFailure $LASTEXITCODE "" }
}

if (-not $failed) {
  Step 15 "Browser route smoke test (real Chromium)"
  if (Test-Path "node_modules\playwright") {
    node scripts\smoke_test.mjs
    if ($LASTEXITCODE -ne 0) { RecordFailure $LASTEXITCODE "" }
  } else {
    Write-Host "      Playwright not installed - skipping." -ForegroundColor DarkGray
    Write-Host "      Enable it once with:  npm run smoke:setup" -ForegroundColor DarkGray
  }
}

Write-Host ""
if ($failed) {
  Write-Host "============================================================" -ForegroundColor Red
  Write-Host "  CHECK FAILED" -ForegroundColor Red
  Write-Host "============================================================" -ForegroundColor Red
  foreach ($line in $failedSteps) { Write-Host $line -ForegroundColor Red }
  Write-Host ""
  Write-Host "  Scroll up for the check's own [FAIL] lines. If a step above shows" -ForegroundColor DarkGray
  Write-Host "  no [FAIL] line, it crashed during shutdown rather than failing." -ForegroundColor DarkGray
  Write-Host "============================================================" -ForegroundColor Red
  exit 1
}
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  ALL CHECKS PASSED - PROJECT IS CLEAN" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
exit 0
