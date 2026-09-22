@echo off
REM ===========================================================================
REM  JARVIS OS - FULL ERROR CHECK  (double-click to run)
REM ===========================================================================
REM  Runs every automated check against the project and reports failures:
REM    1. ESLint        - undefined components/variables (the "blank screen" bugs)
REM    2. Health check  - imports, routes, API paths, preload bridge, python syntax
REM    3. API contract  - every UI call must match a real backend route
REM    4. Render smoke  - all 18 routes render + mount (no browser download needed)
REM    5. Build         - production bundle must compile
REM    6. Backend tests - 11 live test suites
REM    7. Endpoint sweep- boots the backend and probes every GET route for 5xx
REM    8. Browser smoke - loads all 18 routes in real Chromium (optional)
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
echo [1/12] ESLint (undefined vars / bad JSX) ...
call npm run lint
if errorlevel 1 goto :failed

echo.
echo [2/12] Static health check (imports, routes, API wiring) ...
"%PY%" scripts\health_check.py
if errorlevel 1 goto :failed

echo.
echo [3/12] API contract (UI calls ^<^-^> backend routes) ...
call npm run check:api
if errorlevel 1 goto :failed

echo.
echo [4/12] Route render smoke test (all 18 routes) ...
call npm run smoke
if errorlevel 1 goto :failed

echo.
echo [5/12] Production build ...
call npm run build
if errorlevel 1 goto :failed

echo.
echo [6/12] Backend test suites ...
pushd backend
"%PY%" test_all_endpoints.py
set BACKEND_RC=%errorlevel%
popd
if not "%BACKEND_RC%"=="0" goto :failed

echo.
echo [7/12] Google integration test (offline fake-Google suite) ...
pushd backend
"%PY%" test_google_integration.py
set GOOGLE_RC=%errorlevel%
popd
if not "%GOOGLE_RC%"=="0" goto :failed

echo.
echo [8/12] Mail + Calendar test (fake IMAP + iCal parser) ...
pushd backend
"%PY%" test_mail_calendar.py
set MAIL_RC=%errorlevel%
popd
if not "%MAIL_RC%"=="0" goto :failed

echo.
echo [9/12] Mail -^> memory ingestion test (fake IMAP + RAG proof) ...
pushd backend
"%PY%" test_mail_ingestion.py
set INGEST_RC=%errorlevel%
popd
if not "%INGEST_RC%"=="0" goto :failed

echo.
echo [10/12] Orb voice loop (mic re-arm, TTS watchdog, wake word) ...
call npm run test:orb
if errorlevel 1 goto :failed

echo.
echo [11/12] Backend endpoint sweep (every GET route) ...
"%PY%" backend\verify_backend_endpoints.py
if errorlevel 1 goto :failed

echo.
echo [12/12] Browser route smoke test ...
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
