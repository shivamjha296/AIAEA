@echo off
REM ==============================================================================
REM Autonomous Regulatory & Compliance Radar -- Windows Batch Launcher v2
REM
REM Launches services in separate CMD windows:
REM   1. Ollama         http://localhost:11434  (LLM inference)
REM   2. FastAPI        http://localhost:8000   (REST API backend)
REM   3. Next.js        http://localhost:3000   (Web frontend)
REM   4. Pipeline CLI   (manual scans)
REM
REM Usage: Double-click startallservices.bat
REM ==============================================================================

echo.
echo ======================================================================
echo   REGULATORY COMPLIANCE RADAR - Starting All Services
echo ======================================================================
echo.

set ROOT=%~dp0

REM -- Check Ollama -----------------------------------------------------------
where ollama >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Ollama is NOT in PATH.
    echo   Install: winget install Ollama.Ollama
    echo.
) else (
    echo [OK] Ollama found.
)

REM -- Check Node -------------------------------------------------------------
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Node.js not found. Frontend will not start.
    echo   Install: https://nodejs.org/
) else (
    echo [OK] Node.js found.
)

echo.

REM -- 1. Ollama Server -------------------------------------------------------
echo [1/4] Checking Ollama LLM Service...
start "Ollama LLM Status :11434" cmd /k "title Ollama LLM Status :11434 && echo === OLLAMA LLM SERVICE === && echo Port: 11434 && echo. && tasklist | findstr /i "ollama.exe" >nul && (echo [OK] Ollama is already RUNNING in background. && echo Installed models: && ollama list && echo. && echo To download a model run: ollama pull llama3.1) || (ollama serve)"

timeout /t 2 /nobreak >nul

REM -- 2. FastAPI Backend ------------------------------------------------------
echo [2/4] Starting FastAPI Backend...
start "FastAPI Backend :8000" cmd /k "title FastAPI Backend :8000 && cd /d %ROOT% && echo === FASTAPI BACKEND === && echo URL:  http://localhost:8000 && echo Docs: http://localhost:8000/docs && echo. && python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak >nul

REM -- 3. Next.js Frontend -----------------------------------------------------
echo [3/4] Starting Next.js Frontend...
start "Next.js Frontend :3000" cmd /k "title Next.js Frontend :3000 && cd /d %ROOT%frontend && echo === NEXT.JS FRONTEND === && echo URL: http://localhost:3000 && echo. && npm run dev"

REM -- 4. Pipeline CLI Window --------------------------------------------------
echo [4/4] Opening Pipeline CLI window...
start "Compliance Pipeline CLI" cmd /k "title Compliance Pipeline CLI && cd /d %ROOT% && echo === COMPLIANCE RADAR PIPELINE CLI === && echo. && echo Run a manual scan: && echo   python main.py && echo   python main.py --queries 2 --max-sources 3 && echo. && echo Or trigger via the web UI at http://localhost:3000 && echo."

echo.
echo ======================================================================
echo   All services launched in separate windows:
echo.
echo    Window 1:  Ollama LLM Server    http://localhost:11434
echo    Window 2:  FastAPI REST API     http://localhost:8000
echo               API Docs             http://localhost:8000/docs
echo    Window 3:  Next.js Frontend     http://localhost:3000
echo    Window 4:  Pipeline CLI         (manual scans)
echo.
echo   Open http://localhost:3000 in your browser.
echo ======================================================================
echo.
