# ============================================================================
#  JARVIS SECOND BRAIN - FULL VERIFICATION PIPELINE (Windows PowerShell)
# ----------------------------------------------------------------------------
#  Runs every check that matters for the paper-aligned codebase:
#    1. ESLint                - undefined vars / bad JSX
#    2. Static health check   - imports resolve, API wiring, python syntax
#    3. API contract          - UI /api/ calls <-> backend route table
#    4. Production build      - vite build
#    5. Research layer tests  - neural NLI / temporal extraction (pytest)
#    6. PersonalBrain-Bench   - reproduces Table I of the IEEE paper
#    7. Multi-user benchmark  - five personas + paired statistics
#    8. Endpoint sweep        - boots backend, probes every GET route for 5xx
#    9. Browser route smoke   - optional, loads all routes in real Chromium
#
#  Usage:  powershell -ExecutionPolicy Bypass -File verify-jarvis.ps1
# ============================================================================

$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

$failed = $false
$script:currentStep = ""

function Step([int]$n, [string]$title) {
  $script:currentStep = "$n ($title)"
  Write-Host ""
  Write-Host "=== STEP $n : $title ===" -ForegroundColor Cyan
}

function RecordFailure([int]$code, [string]$what) {
  $script:failed = $true
  $label = if ($what) { $what } else { $script:currentStep }
  Write-Host "      FAILED ($code) in $label" -ForegroundColor Red
}

$py = "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

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
  Step 4 "Production build"
  npm run build
  if ($LASTEXITCODE -ne 0) { RecordFailure $LASTEXITCODE "" }
}

if (-not $failed) {
  Step 5 "Research layer tests (neural NLI, temporal extraction, multi-user pipeline)"
  Push-Location backend
  $backendPy = ".venv\Scripts\python.exe"
  if (-not (Test-Path $backendPy)) { $backendPy = "python" }
  & $backendPy -m pytest tests\test_neural_research.py -q
  $rc = $LASTEXITCODE
  Pop-Location
  if ($rc -ne 0) { RecordFailure $rc "5 (Research layer tests)" }
}

if (-not $failed) {
  Step 6 "PersonalBrain-Bench reproduction (Table I of the IEEE paper)"
  & $py backend\scripts\run_bench.py
  if ($LASTEXITCODE -ne 0) { RecordFailure $LASTEXITCODE "" }
}

if (-not $failed) {
  Step 7 "Multi-user benchmark (five personas, paired Wilcoxon statistics)"
  & $py backend\scripts\run_multi_user_bench.py
  if ($LASTEXITCODE -ne 0) { RecordFailure $LASTEXITCODE "" }
}

if (-not $failed) {
  Step 8 "Backend endpoint sweep (boots backend, probes every GET route for 5xx)"
  & $py scripts\api_sweep.py
  if ($LASTEXITCODE -ne 0) { RecordFailure $LASTEXITCODE "" }
}

if (-not $failed) {
  Step 9 "Browser route smoke test (real Chromium, optional)"
  if (Test-Path "node_modules\playwright") {
    node scripts\smoke_test.mjs
    if ($LASTEXITCODE -ne 0) { RecordFailure $LASTEXITCODE "" }
  } else {
    Write-Host "      skipped - playwright not installed." -ForegroundColor DarkGray
    Write-Host "      Enable it once with:  npm run smoke:setup" -ForegroundColor DarkGray
  }
}

Write-Host ""
if ($failed) {
  Write-Host "RESULT: FAILED - see red lines above." -ForegroundColor Red
  exit 1
} else {
  Write-Host "RESULT: ALL STEPS PASSED." -ForegroundColor Green
  exit 0
}
