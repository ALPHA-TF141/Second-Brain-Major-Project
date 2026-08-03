@echo off
setlocal enabledelayedexpansion
title Second Brain - Backend Setup
color 0B

echo ==============================================
echo   SECOND BRAIN - BACKEND SETUP
echo   This creates a venv and installs deps.
echo ==============================================
echo.

REM ---- Detect Python (prefer `py`, fall back to `python`) ----
set PY=python
py --version >nul 2>&1
if !errorlevel!==0 (
    set PY=py -3
    echo [OK] Using launcher: py
) else (
    python --version >nul 2>&1
    if !errorlevel!==0 (
        echo [FAIL] Python not found. Install Python 3.11/3.12 from python.org and check "Add to PATH".
        pause & exit /b 1
    ) else (
        echo [OK] Using: python
    )
)

REM ---- Create venv if missing ----
if exist "backend\.venv\Scripts\python.exe" (
    echo [OK] venv already exists
) else (
    echo [..] Creating virtual env...
    %PY% -m venv backend\.venv
    if not exist "backend\.venv\Scripts\python.exe" (
        echo [FAIL] Could not create venv. Check Python install.
        pause & exit /b 1
    )
    echo [OK] venv created
)
echo.

REM ---- Upgrade pip ----
echo [..] Upgrading pip...
backend\.venv\Scripts\python.exe -m pip install --upgrade pip
echo.

REM ---- Install base requirements ----
echo [..] Installing base requirements.txt (this may take a few minutes)...
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
echo.

REM ---- Optional staged requirements (ignore failures for heavy AI deps) ----
for %%r in (requirements-rag requirements-semantic requirements-voice requirements-ocr-optional) do (
    if exist "backend\%%r.txt" (
        echo [..] Installing %%r.txt...
        backend\.venv\Scripts\python.exe -m pip install -r backend\%%r.txt
        if !errorlevel!==0 echo [WARN] %%r.txt had errors - run it separately later.
    )
)
echo.

REM ---- Create .env from example if missing ----
if not exist "backend\.env" (
    if exist "backend\.env.example" (
        copy /Y "backend\.env.example" "backend\.env" >nul
        echo [OK] Created backend\.env from .env.example
        echo     ^>^> OPEN backend\.env NOW and fill in real values (LLM key, Neo4j creds, etc.)
    ) else (
        echo [WARN] No .env.example found - create backend\.env manually.
    )
) else (
    echo [OK] backend\.env already exists
)
echo.

echo ==============================================
echo   SETUP COMPLETE - next steps:
echo   1) Edit backend\.env with real values
echo   2) Start backend:   backend\.venv\Scripts\activate  ^&^&  uvicorn app.main:app --host 0.0.0.0 --port 8000
echo   3) Start frontend:  npm run dev
echo ==============================================
pause
