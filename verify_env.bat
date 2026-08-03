@echo off
setlocal enabledelayedexpansion
title Second Brain -> JARVIS - Env Diagnostic
color 0A

echo ==============================================
echo   SECOND BRAIN -^> JARVIS  ENV DIAGNOSTIC
echo   %date% %time%
echo ==============================================
echo.

REM ---------------- 1. Core tool versions ----------------
echo --- 1. Core tool versions ---
set FOUND=0

for /f "delims=" %%v in ('node --version 2^>nul') do set NODEVER=%%v
if defined NODEVER (echo [OK]    Node      -^> %NODEVER%) else (echo [FAIL]  Node not found / not on PATH)
if defined NODEVER set FOUND=1

for /f "delims=" %%v in ('npm --version 2^>nul') do set NPMVER=%%v
if defined NPMVER (echo [OK]    npm       -^> %NPMVER%) else (echo [FAIL]  npm not found)

for /f "delims=" %%v in ('python --version 2^>^&1') do set PYVER=%%v
if defined PYVER (echo [OK]    Python    -^> %PYVER%) else (echo [FAIL]  python not found / not on PATH)

for /f "delims=" %%v in ('git --version 2^>nul') do set GITVER=%%v
if defined GITVER (echo [OK]    Git       -^> %GITVER%) else (echo [CHECK] Git not found)

if "%FOUND%"=="0" (
  echo.
  echo [!] Node/Python not detected. Make sure they are installed and added to PATH.
)
echo.

REM ---------------- 2. Project folders ----------------
echo --- 2. Project folders (run this script from INSIDE the "Second Brain" folder) ---
if exist "backend\app" (echo [OK]    backend\app exists) else (echo [CHECK] backend\app NOT here - are you in the right folder?)
if exist "src"        (echo [OK]    frontend src exists) else (echo [CHECK] src NOT here - are you in the right folder?)
if exist "node_modules" (echo [OK]    node_modules present) else (echo [CHECK] node_modules missing - run: npm install)
if exist "backend\.env" (echo [OK]    backend\.env present) else (echo [CHECK] backend\.env missing - copy .env.example to .env and fill it)
if exist "backend\.env.example" (echo [OK]    backend\.env.example present) else (echo [CHECK] backend\.env.example missing)
if exist "backend\.venv\Scripts\python.exe" (
    echo [OK]    backend venv found
    set VENVPY=backend\.venv\Scripts\python.exe
) else (
    echo [CHECK] backend\.venv NOT found - create it:  python -m venv backend\.venv
    set VENVPY=python
)
echo.

REM ---------------- 3. Python packages ----------------
echo --- 3. Python packages (using backend venv if present) ---
for %%p in (fastapi uvicorn sqlalchemy chromadb neo4j openai whisper coqui-tts pyaudio sentence-transformers pillow pydantic pydantic-settings websockets) do (
    "%VENVPY%" -c "import importlib,sys; importlib.import_module(sys.argv[1])" %%p >nul 2>&1
    if !errorlevel!==0 (
        echo [OK]    %%p installed
    ) else (
        echo [FAIL]  %%p NOT installed
    )
)
echo.

REM ---------------- 4. Ports / services ----------------
echo --- 4. Services listening on ports ---
netstat -an | findstr /R /C:":8000 .*LISTEN" >nul 2>&1 && echo [OK]    Backend on :8000 LISTENING || echo [CHECK] Backend NOT on :8000 (OK if not started yet)
netstat -an | findstr /R /C:":5173 .*LISTEN" >nul 2>&1 && echo [OK]    Vite on :5173 LISTENING || echo [CHECK] Vite NOT on :5173 (OK if not started yet)
netstat -an | findstr /R /C:":7687 .*LISTEN" >nul 2>&1 && echo [OK]    Neo4j Bolt on :7687 LISTENING || echo [CHECK] Neo4j NOT on :7687 (needed for knowledge graph!)
netstat -an | findstr /R /C:":7474 .*LISTEN" >nul 2>&1 && echo [OK]    Neo4j HTTP on :7474 LISTENING || echo [CHECK] Neo4j HTTP NOT on :7474
echo.

REM ---------------- 5. Recent log tails ----------------
echo --- 5. Recent log tails (errors often hide here) ---
if exist "backend-dev.err.log"  (echo. & echo ### backend-dev.err.log & powershell -Command "Get-Content 'backend-dev.err.log' -Tail 20")
if exist "backend\backend-dev.err.log" (echo. & echo ### backend\backend-dev.err.log & powershell -Command "Get-Content 'backend\backend-dev.err.log' -Tail 20")
if exist "vite-dev.err.log"     (echo. & echo ### vite-dev.err.log & powershell -Command "Get-Content 'vite-dev.err.log' -Tail 20")
echo.

REM ---------------- Summary ----------------
echo --- Summary ---
echo Paste this output into the assistant chat. Also upload these files:
echo   backend\app\main.py  config.py  .env.example
echo   backend\requirements*.txt
echo   package.json  vite.config.js
echo   any Electron main file (main.js / electron/main.js) if you have one
echo.
pause
