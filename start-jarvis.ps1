# ============================================================
#   JARVIS SECOND BRAIN - CLEAN LAUNCHER
#   Runs the full stack in an isolated process, immune to
#   VS Code terminal injection or Ctrl+C interruptions.
# ============================================================

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "   JARVIS // PERSONAL AI OPERATING SYSTEM      " -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

# ---- 1. Free up ports if stale processes are lingering ----
Write-Host "[1/4] Clearing stale processes..." -ForegroundColor Yellow
Get-Process -Name python,node,electron -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 700

$portInUse = netstat -ano | Select-String ":8000\s+.*LISTENING"
if ($portInUse) {
    Write-Host "      Port 8000 still occupied. Forcing release..." -ForegroundColor DarkYellow
    foreach ($line in $portInUse) {
        $parts = ($line -split '\s+') | Where-Object { $_ -ne '' }
        $procId = $parts[-1]
        if ($procId -match '^\d+$') {
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Milliseconds 500
}
Write-Host "      Ports clear." -ForegroundColor Green

# ---- 2. Verify Python virtual environment exists ----
Write-Host "[2/4] Verifying backend environment..." -ForegroundColor Yellow
$VenvPython = Join-Path $ProjectRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "      [ERROR] Virtual environment missing at:" -ForegroundColor Red
    Write-Host "      $VenvPython" -ForegroundColor Red
    Write-Host "      Run setup_backend.bat first to create it." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "      Virtual environment found." -ForegroundColor Green

# ---- 3. Verify Ollama local LLM is serving ----
Write-Host "[3/4] Checking local Ollama LLM..." -ForegroundColor Yellow
try {
    $ollamaCheck = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "      Ollama online. Models available: $($ollamaCheck.models.Count)" -ForegroundColor Green
} catch {
    Write-Host "      Ollama not responding. Attempting to start it..." -ForegroundColor DarkYellow
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    Write-Host "      Ollama start attempted." -ForegroundColor Green
}

# ---- 4. Launch the full stack ----
Write-Host "[4/4] Launching Jarvis OS..." -ForegroundColor Yellow
Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Backend  : http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  Frontend : http://127.0.0.1:5173" -ForegroundColor White
Write-Host "  Desktop  : Electron window will open" -ForegroundColor White
Write-Host "  Orb      : Press Alt + J anytime" -ForegroundColor White
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Keep this window open. Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host ""

npm run dev
