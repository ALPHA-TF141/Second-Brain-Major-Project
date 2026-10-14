@echo off
REM ============================================================================
REM  JARVIS SECOND BRAIN - FULL VERIFICATION PIPELINE (Windows batch)
REM ----------------------------------------------------------------------------
REM  Mirror of verify-jarvis.ps1 for plain cmd.exe:
REM    1. ESLint            2. Health check   3. API contract   4. Build
REM    5. Research tests    6. Bench repro    7. Multi-user bench
REM    8. Endpoint sweep    9. Browser smoke (optional)
REM ============================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

set PY=backend\.venv\Scripts\python.exe
if not exist "%PY%" set PY=python
set BPY=backend\.venv\Scripts\python.exe
if not exist "%BPY%" set BPY=python
set FAILED=0

echo.
echo === STEP 1 : ESLint ===
call npm run lint
if errorlevel 1 set FAILED=1

if %FAILED%==0 (
  echo.
  echo === STEP 2 : Static health check ===
  "%PY%" scripts\health_check.py
  if errorlevel 1 set FAILED=1
)

if %FAILED%==0 (
  echo.
  echo === STEP 3 : API contract ===
  call npm run check:api
  if errorlevel 1 set FAILED=1
)

if %FAILED%==0 (
  echo.
  echo === STEP 4 : Production build ===
  call npm run build
  if errorlevel 1 set FAILED=1
)

if %FAILED%==0 (
  echo.
  echo === STEP 5 : Research layer tests ===
  pushd backend
  "%BPY%" -m pytest tests\test_neural_research.py -q
  if errorlevel 1 ( popd & set FAILED=1 ) else ( popd )
)

if %FAILED%==0 (
  echo.
  echo === STEP 6 : PersonalBrain-Bench reproduction ===
  "%PY%" backend\scripts\run_bench.py
  if errorlevel 1 set FAILED=1
)

if %FAILED%==0 (
  echo.
  echo === STEP 7 : Multi-user benchmark ===
  "%PY%" backend\scripts\run_multi_user_bench.py
  if errorlevel 1 set FAILED=1
)

if %FAILED%==0 (
  echo.
  echo === STEP 8 : Backend endpoint sweep ===
  "%PY%" scripts\api_sweep.py
  if errorlevel 1 set FAILED=1
)

if %FAILED%==0 (
  echo.
  echo === STEP 9 : Browser route smoke test (optional) ===
  if exist node_modules\playwright (
    node scripts\smoke_test.mjs
    if errorlevel 1 set FAILED=1
  ) else (
    echo       skipped - playwright not installed. Enable once with: npm run smoke:setup
  )
)

echo.
if %FAILED%==1 (
  echo RESULT: FAILED - see above.
  exit /b 1
) else (
  echo RESULT: ALL STEPS PASSED.
  exit /b 0
)
