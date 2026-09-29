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
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM Each step records WHERE it is before running, so a failure names itself
REM below instead of leaving "scroll up" with nothing to find. The exit code is
REM read with !errorlevel! (delayed expansion) - inside a parenthesised block
REM %errorlevel% would be expanded when the block is PARSED, which is always 0.
set "ERRCODE=0"
set "CRASHNOTE="
set PY=backend\.venv\Scripts\python.exe
if not exist "%PY%" set PY=python

echo.
echo ============================================================
echo   JARVIS OS - FULL ERROR CHECK
echo ============================================================

echo.
echo [1/15] ESLint (undefined vars / bad JSX) ...
set "STEPNO=1"
set "STEPNAME=ESLint (undefined vars / bad JSX)"
call npm run lint
if errorlevel 1 ( set "ERRCODE=!errorlevel!" & goto :failed )

echo.
echo [2/15] Static health check (imports, routes, API wiring) ...
set "STEPNO=2"
set "STEPNAME=Static health check"
"%PY%" scripts\health_check.py
if errorlevel 1 ( set "ERRCODE=!errorlevel!" & goto :failed )

echo.
echo [3/15] API contract (UI calls ^<^-^> backend routes) ...
set "STEPNO=3"
set "STEPNAME=API contract"
call npm run check:api
if errorlevel 1 ( set "ERRCODE=!errorlevel!" & goto :failed )

echo.
echo [4/15] Route render smoke test (all 18 routes) ...
set "STEPNO=4"
set "STEPNAME=Route render smoke test"
call npm run smoke
if errorlevel 1 ( set "ERRCODE=!errorlevel!" & goto :failed )

echo.
echo [5/15] Production build ...
set "STEPNO=5"
set "STEPNAME=Production build"
call npm run build
if errorlevel 1 ( set "ERRCODE=!errorlevel!" & goto :failed )

echo.
echo [6/15] Backend test suites ...
set "STEPNO=6"
set "STEPNAME=Backend test suites"
pushd backend
"%PY%" test_all_endpoints.py
set BACKEND_RC=!errorlevel!
popd
if not "!BACKEND_RC!"=="0" ( set "ERRCODE=!BACKEND_RC!" & goto :failed )

echo.
echo [7/15] Google integration test (offline fake-Google suite) ...
set "STEPNO=7"
set "STEPNAME=Google integration test"
pushd backend
"%PY%" test_google_integration.py
set GOOGLE_RC=!errorlevel!
popd
if not "!GOOGLE_RC!"=="0" ( set "ERRCODE=!GOOGLE_RC!" & goto :failed )

echo.
echo [8/15] Mail + Calendar test (fake IMAP + iCal parser) ...
set "STEPNO=8"
set "STEPNAME=Mail + Calendar test"
pushd backend
"%PY%" test_mail_calendar.py
set MAIL_RC=!errorlevel!
popd
if not "!MAIL_RC!"=="0" ( set "ERRCODE=!MAIL_RC!" & goto :failed )

echo.
echo [9/15] Mail -^> memory ingestion test (fake IMAP + RAG proof) ...
set "STEPNO=9"
set "STEPNAME=Mail ingestion test"
pushd backend
"%PY%" test_mail_ingestion.py
set INGEST_RC=!errorlevel!
popd
if not "!INGEST_RC!"=="0" ( set "ERRCODE=!INGEST_RC!" & goto :failed )

echo.
echo [10/15] Orb voice loop (mic re-arm, TTS watchdog, wake word) ...
set "STEPNO=10"
set "STEPNAME=Orb voice loop"
call npm run test:orb
if errorlevel 1 ( set "ERRCODE=!errorlevel!" & goto :failed )

echo.
echo [11/15] Wake word + proactive voice (policy + real model) ...
set "STEPNO=11"
set "STEPNAME=Wake word + proactive voice"
pushd backend
"%PY%" test_proactive_voice.py
set PV_RC=!errorlevel!
popd
if not "!PV_RC!"=="0" ( set "ERRCODE=!PV_RC!" & goto :failed )

echo.
echo [12/15] Hands-free UI wiring (wake -^> orb, speak -^> voice) ...
set "STEPNO=12"
set "STEPNAME=Hands-free UI wiring"
call npm run test:proactive
if errorlevel 1 ( set "ERRCODE=!errorlevel!" & goto :failed )

echo.
echo [13/15] Research layer (7 contributions + PersonalBrain-Bench) ...
set "STEPNO=13"
set "STEPNAME=Research layer"
pushd backend
"%PY%" test_research_layer.py
set RL_RC=!errorlevel!
popd
if not "!RL_RC!"=="0" ( set "ERRCODE=!RL_RC!" & goto :failed )

echo.
echo [14/15] Backend endpoint sweep (every GET route) ...
set "STEPNO=14"
set "STEPNAME=Backend endpoint sweep"
"%PY%" backend\verify_backend_endpoints.py
if errorlevel 1 ( set "ERRCODE=!errorlevel!" & goto :failed )

echo.
echo [15/15] Browser route smoke test ...
set "STEPNO=15"
set "STEPNAME=Browser route smoke test"
if not exist "node_modules\playwright" (
    echo       Playwright not installed - skipping.
    echo       To enable it run:  npm run smoke:setup
    echo                          npx playwright install chromium
) else (
    call node scripts\smoke_test.mjs
    if errorlevel 1 ( set "ERRCODE=!errorlevel!" & goto :failed )
)

echo.
echo ============================================================
echo   ALL CHECKS PASSED - PROJECT IS CLEAN
echo ============================================================
echo.
pause
exit /b 0

:failed
REM A step can print its own all-clear and still return non-zero: the process
REM died while shutting down (a native library unloaded under a live background
REM thread - sounddevice, onnxruntime, torch) after writing its verdict. Windows
REM reports those as large or negative codes, and they are named as such rather
REM than left looking like a failed check.
set "CRASHNOTE="
if !ERRCODE! LSS 0 set "CRASHNOTE=  (a crash during shutdown, not a failed check)"
if !ERRCODE! GTR 9000 set "CRASHNOTE=  (a crash during shutdown, not a failed check)"
echo.
echo ============================================================
echo   CHECK FAILED
echo ============================================================
echo   step !STEPNO! - !STEPNAME!
echo   exit code !ERRCODE!!CRASHNOTE!
echo.
echo   Scroll up for that step's own [FAIL] lines. If it shows none,
echo   it crashed during shutdown rather than failing a check.
echo ============================================================
echo.
pause
exit /b 1
