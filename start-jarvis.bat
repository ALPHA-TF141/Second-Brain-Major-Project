@echo off
setlocal
title JARVIS - Second Brain AI OS
color 0B

echo.
echo ==============================================
echo    JARVIS // PERSONAL AI OPERATING SYSTEM
echo ==============================================
echo.

cd /d "%~dp0"

REM ---- 1. Clear stale processes ----
echo [1/4] Clearing stale processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM electron.exe >nul 2>&1
timeout /t 1 /nobreak >nul
echo       Ports clear.

REM ---- 2. Verify venv exists ----
echo [2/4] Verifying backend environment...
if not exist "backend\.venv\Scripts\python.exe" (
    echo       [ERROR] Virtual environment missing.
    echo       Run setup_backend.bat first.
    pause
    exit /b 1
)
echo       Virtual environment found.

REM ---- 3. Check Ollama ----
echo [3/4] Checking local Ollama LLM...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel%==0 (
    echo       Ollama online.
) else (
    echo       Starting Ollama in background...
    start "" ollama serve
    timeout /t 3 /nobreak >nul
)

REM ---- 4. Launch ----
echo [4/4] Launching Jarvis OS...
echo.
echo ==============================================
echo   Backend  : http://127.0.0.1:8000
echo   Frontend : http://127.0.0.1:5173
echo   Desktop  : Electron window will open
echo   Orb      : Press Alt + J anytime
echo ==============================================
echo.
echo   Keep this window open. Press Ctrl+C to stop.
echo.

call npm run dev

pause
