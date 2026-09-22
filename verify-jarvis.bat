@echo off
REM ===========================================================================
REM  JARVIS OS - FULL ERROR CHECK  (double-click to run)
REM ===========================================================================
REM  Runs every automated check against the project and reports failures:
REM    1. ESLint        - undefined components/variables (the "blank screen" bugs)
REM    2. Health check  - imports, routes, API paths, preload bridge, python syntax
REM    3. Build         - production bundle must compile
REM    4. Backend tests - 11 live test suites
REM    5. Browser smoke - loads all 18 routes in a real Chromium (needs Playwright)
REM ===========================================================================
setlocal
cd /d "%~dp0"
set PY=backend\.venv\Scripts\python.exe
if not exist "%PY%" set PY=python

echo.
echo ============================================================
echo   JARVIS OS - FULL ERROR CHECK
echo ============================================================

echo.
echo [1/5] ESLint (undefined vars / bad JSX) ...
call npm run lint
if errorlevel 1 goto :failed

echo.
echo [2/5] Static health check (imports, routes, API wiring) ...
"%PY%" scripts\health_check.py
if errorlevel 1 goto :failed

echo.
echo [3/5] Production build ...
call npm run build
if errorlevel 1 goto :failed

echo.
echo [4/5] Backend test suites ...
pushd backend
"%PY%" test_all_endpoints.py
set BACKEND_RC=%errorlevel%
popd
if not "%BACKEND_RC%"=="0" goto :failed

echo.
echo [5/5] Browser route smoke test ...
if not exist "node_modules\playwright" (
    echo       Playwright not installed - skipping.
    echo       To enable it run:  npm run smoke:setup
    echo                          npx playwright install chromium
) else (
    call node scripts\smoke_test.mjs
    if errorlevel 1 goto :failed
)

echo.
echo ============================================================
echo   ALL CHECKS PASSED - PROJECT IS CLEAN
echo ============================================================
echo.
pause
exit /b 0

:failed
echo.
echo ============================================================
echo   CHECK FAILED - scroll up to see the [FAIL] lines
echo ============================================================
echo.
pause
exit /b 1
