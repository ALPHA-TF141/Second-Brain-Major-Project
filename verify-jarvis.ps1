<#
  JARVIS OS - FULL ERROR CHECK (PowerShell)
  =========================================
  Usage:  .\verify-jarvis.ps1
  Runs ESLint, static health check, production build, backend suites and the
  browser route smoke test. Stops at the first failure with a clear message.
#>
$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot

$py = "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

function Step($n, $title) {
  Write-Host ""
  Write-Host "[$n/5] $title" -ForegroundColor Cyan
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
  Step 3 "Production build"
  npm run build
  if ($LASTEXITCODE -ne 0) { $failed = $true }
}

if (-not $failed) {
  Step 4 "Backend test suites"
  Push-Location backend
  $backendPy = ".venv\Scripts\python.exe"
  if (-not (Test-Path $backendPy)) { $backendPy = "python" }
  & $backendPy test_all_endpoints.py
  $rc = $LASTEXITCODE
  Pop-Location
  if ($rc -ne 0) { $failed = $true }
}

if (-not $failed) {
  Step 5 "Browser route smoke test"
  if (Test-Path "node_modules\playwright") {
    node scripts\smoke_test.mjs
    if ($LASTEXITCODE -ne 0) { $failed = $true }
  } else {
    Write-Host "      Playwright not installed - skipping." -ForegroundColor DarkGray
    Write-Host "      Enable it with:  npm install --save-dev playwright ; npx playwright install chromium" -ForegroundColor DarkGray
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
