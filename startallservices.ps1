# ==============================================================================
# Autonomous Regulatory & Compliance Radar -- PowerShell Launcher v2
#
# Launches services in separate PowerShell windows:
#   1. Ollama         -> http://localhost:11434  (LLM inference)
#   2. FastAPI        -> http://localhost:8000   (REST API backend)
#   3. Next.js        -> http://localhost:3000   (Web frontend)
#   4. Pipeline CLI   (manual scans)
#
# Usage: powershell -ExecutionPolicy Bypass -File startallservices.ps1
# ==============================================================================

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  REGULATORY COMPLIANCE RADAR -- Starting All Services" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# -- Check Ollama -------------------------------------------------------------
$ollamaRunning = $false
try {
    $resp = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($resp.StatusCode -eq 200) {
        $ollamaRunning = $true
    }
} catch {
    $ollamaRunning = $false
}

if ($ollamaRunning) {
    Write-Host "[OK] Ollama is already active on http://localhost:11434" -ForegroundColor Green
} elseif (Get-Command "ollama" -ErrorAction SilentlyContinue) {
    Write-Host "[OK] Ollama found in PATH. Will start server..." -ForegroundColor Green
} else {
    Write-Host "[WARNING] Ollama is NOT installed or not in PATH." -ForegroundColor Yellow
    Write-Host "  Install: winget install Ollama.Ollama" -ForegroundColor Gray
    Write-Host "  Or:      https://ollama.com/download" -ForegroundColor Gray
}

# -- Check Node.js ------------------------------------------------------------
if (-not (Get-Command "node" -ErrorAction SilentlyContinue)) {
    Write-Host "[WARNING] Node.js is NOT installed." -ForegroundColor Yellow
    Write-Host "  Install: https://nodejs.org/" -ForegroundColor Gray
} else {
    Write-Host "[OK] Node.js found: $(node --version)" -ForegroundColor Green
}

# -- Check Python -------------------------------------------------------------
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python is NOT installed." -ForegroundColor Red
    exit 1
} else {
    Write-Host "[OK] Python found." -ForegroundColor Green
}

Write-Host ""

# -- 1. Ollama Server ---------------------------------------------------------
Write-Host "[1/4] Checking Ollama LLM Service..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
`$Host.UI.RawUI.WindowTitle = 'Ollama LLM Status :11434'
Write-Host '=== OLLAMA LLM SERVICE ===' -ForegroundColor Yellow
Write-Host 'Port: 11434' -ForegroundColor Gray
Write-Host ''

`$ollamaProc = Get-Process -Name '*ollama*' -ErrorAction SilentlyContinue
if (`$ollamaProc) {
    Write-Host '[OK] Ollama is already RUNNING in background (PID: ' + (`$ollamaProc.Id -join ', ') + ')' -ForegroundColor Green
    Write-Host ''
    Write-Host 'Current downloaded models:' -ForegroundColor Cyan
    ollama list
    Write-Host ''
    Write-Host 'If list is empty, download a model by running:' -ForegroundColor Yellow
    Write-Host '  ollama pull llama3.1' -ForegroundColor White
    Write-Host '  ollama pull mistral' -ForegroundColor White
} else {
    Write-Host 'Starting ollama serve...' -ForegroundColor Yellow
    ollama serve
}
"@

Start-Sleep -Seconds 2

# -- 2. FastAPI Backend -------------------------------------------------------
Write-Host "[2/4] Starting FastAPI Backend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
`$Host.UI.RawUI.WindowTitle = 'FastAPI Backend :8000'
Set-Location '$ROOT'
Write-Host '=== FASTAPI BACKEND ===' -ForegroundColor Magenta
Write-Host 'URL:  http://localhost:8000' -ForegroundColor Gray
Write-Host 'Docs: http://localhost:8000/docs' -ForegroundColor Gray
Write-Host ''
Write-Host 'Starting server...' -ForegroundColor Gray
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
"@

Start-Sleep -Seconds 3

# -- 3. Next.js Frontend ------------------------------------------------------
Write-Host "[3/4] Starting Next.js Frontend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
`$Host.UI.RawUI.WindowTitle = 'Next.js Frontend :3000'
Set-Location '$ROOT\frontend'
Write-Host '=== NEXT.JS FRONTEND ===' -ForegroundColor Blue
Write-Host 'URL: http://localhost:3000' -ForegroundColor Gray
Write-Host ''
Write-Host 'Starting Next.js development server...' -ForegroundColor Gray
npm run dev
"@

# -- 4. Pipeline CLI Window ---------------------------------------------------
Write-Host "[4/4] Opening Pipeline CLI window..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
`$Host.UI.RawUI.WindowTitle = 'Compliance Pipeline CLI'
Set-Location '$ROOT'
Write-Host '=== COMPLIANCE RADAR PIPELINE CLI ===' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Run a manual pipeline scan:' -ForegroundColor Gray
Write-Host '  python main.py' -ForegroundColor White
Write-Host '  python main.py --queries 2 --max-sources 3' -ForegroundColor White
Write-Host ''
Write-Host 'Or trigger a live scan directly from the web UI at http://localhost:3000' -ForegroundColor Gray
Write-Host ''
"@

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  All services initiated in separate windows:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Window 1:  Ollama LLM Server    http://localhost:11434" -ForegroundColor White
Write-Host "   Window 2:  FastAPI REST API     http://localhost:8000" -ForegroundColor White
Write-Host "              API Docs             http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "   Window 3:  Next.js Frontend     http://localhost:3000" -ForegroundColor White
Write-Host "   Window 4:  Pipeline CLI         (manual scans)" -ForegroundColor White
Write-Host ""
Write-Host "  Open your browser at http://localhost:3000" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
