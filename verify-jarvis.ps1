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
  Write-Host "[$n/8] $title" -ForegroundColor Cyan
}

$failed = $false

Step 1 "ESLint (undefined vars / bad JSX)"
npm run lint
if ($LASTEXITCODE -ne 0) { $failed = $true }

if (-not $failed) {
  Step 2 "Static health check (imports, routes, API wiring, python syntax)"
  & $py scripts\health_check.py
  if ($LASTEXITCODE -ne 0) { $failed = $true }
}

if (-not $failed) {
  Step 3 "API contract (UI calls <-> backend routes)"
  npm run check:api
  if ($LASTEXITCODE -ne 0) { $failed = $true }
}

if (-not $failed) {
  Step 4 "Route render smoke test (all 18 routes render + mount)"
  npm run smoke
  if ($LASTEXITCODE -ne 0) { $failed = $true }
}

if (-not $failed) {
  Step 5 "Production build"
  npm run build
  if ($LASTEXITCODE -ne 0) { $failed = $true }
}

if (-not $failed) {
  Step 6 "Backend test suites"
  Push-Location backend
  $backendPy = ".venv\Scripts\python.exe"
  if (-not (Test-Path $backendPy)) { $backendPy = "python" }
  & $backendPy test_all_endpoints.py
  $rc = $LASTEXITCODE
  Pop-Location
  if ($rc -ne 0) { $failed = $true }
}

if (-not $failed) {
  Step 7 "Google integration test (offline fake-Google suite)"
  Push-Location backend
  & $backendPy test_google_integration.py
  $grc = $LASTEXITCODE
  Pop-Location
  if ($grc -ne 0) { $failed = $true }
}

if (-not $failed) {
  Step 8 "Backend endpoint sweep (boots backend, probes every GET route for 5xx)"
  & $py backend\verify_backend_endpoints.py
  if ($LASTEXITCODE -ne 0) { $failed = $true }
}

if (-not $failed) {
  Step 9 "Browser route smoke test (real Chromium)"
  if (Test-Path "node_modules\playwright") {
    node scripts\smoke_test.mjs
    if ($LASTEXITCODE -ne 0) { $failed = $true }
  } else {
    Write-Host "      Playwright not installed - skipping." -ForegroundColor DarkGray
    Write-Host "      Enable it once with:  npm run smoke:setup" -ForegroundColor DarkGray
  }
}

Write-Host ""
if ($failed) {
  Write-Host "============================================================" -ForegroundColor Red
  Write-Host "  CHECK FAILED - scroll up for the [FAIL] lines" -ForegroundColor Red
  Write-Host "============================================================" -ForegroundColor Red
  exit 1
}
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  ALL CHECKS PASSED - PROJECT IS CLEAN" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
exit 0
