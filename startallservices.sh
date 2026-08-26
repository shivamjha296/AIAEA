#!/usr/bin/env bash
# ==============================================================================
# Autonomous Regulatory & Compliance Radar — Shell Launcher v2
#
# Launches all 4 services in separate terminal tabs/windows:
#   1. Ollama         http://localhost:11434  (LLM inference)
#   2. FastAPI        http://localhost:8000   (REST API backend)
#   3. Next.js        http://localhost:3000   (Web frontend)
#   4. Pipeline CLI   (manual scans, idle window)
#
# Usage: bash startallservices.sh
#        chmod +x startallservices.sh && ./startallservices.sh
# ==============================================================================

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "======================================================================"
echo "  REGULATORY COMPLIANCE RADAR — Starting All Services"
echo "======================================================================"
echo ""

# ── Dependency checks ─────────────────────────────────────────
if ! command -v ollama &>/dev/null; then
  echo "[WARNING] Ollama is NOT installed. LLM extraction unavailable."
  echo "  Install: curl -fsSL https://ollama.com/install.sh | sh"
  echo ""
fi

if ! command -v node &>/dev/null; then
  echo "[WARNING] Node.js not found. Frontend will not start."
  echo "  Install: https://nodejs.org/"
fi

if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
  echo "[ERROR] Python not found. Cannot continue."
  exit 1
fi

PYTHON=$(command -v python3 || command -v python)
echo "[OK] Python: $PYTHON"
echo ""

# ── Helper: open a new terminal window ───────────────────────
open_terminal() {
  local TITLE="$1"
  local CMD="$2"
  if command -v gnome-terminal &>/dev/null; then
    gnome-terminal --title="$TITLE" -- bash -c "$CMD; exec bash" &
  elif command -v xterm &>/dev/null; then
    xterm -title "$TITLE" -e "bash -c '$CMD; exec bash'" &
  elif command -v konsole &>/dev/null; then
    konsole --title "$TITLE" -e bash -c "$CMD; exec bash" &
  elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e "tell application \"Terminal\" to do script \"cd '$ROOT' && $CMD\""
  else
    # Fallback: run in background in current terminal
    bash -c "$CMD" &
  fi
}

# ── 1. Ollama Server ──────────────────────────────────────────
echo "[1/4] Starting Ollama LLM Server..."
open_terminal "Ollama Server :11434" \
  "echo '=== OLLAMA LLM SERVER ===' && echo 'Port: 11434' && echo '' && ollama serve"
sleep 2

# ── 2. FastAPI Backend ────────────────────────────────────────
echo "[2/4] Starting FastAPI Backend API..."
open_terminal "FastAPI Backend :8000" \
  "cd '$ROOT' && echo '=== FASTAPI BACKEND ===' && echo 'URL:  http://localhost:8000' && echo 'Docs: http://localhost:8000/docs' && sleep 3 && $PYTHON -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"
sleep 3

# ── 3. Next.js Frontend ───────────────────────────────────────
echo "[3/4] Starting Next.js Frontend..."
open_terminal "Next.js Frontend :3000" \
  "cd '$ROOT/frontend' && echo '=== NEXT.JS FRONTEND ===' && echo 'URL: http://localhost:3000' && sleep 5 && npm run dev"

# ── 4. Pipeline CLI (idle) ────────────────────────────────────
echo "[4/4] Opening Pipeline CLI window..."
open_terminal "Compliance Pipeline CLI" \
  "cd '$ROOT' && echo '=== COMPLIANCE RADAR PIPELINE CLI ===' && echo '' && echo 'Run a manual scan:' && echo '  python main.py' && echo '  python main.py --queries 2 --max-sources 3' && echo '' && echo 'Or trigger via the web UI at http://localhost:3000' && echo '' && exec bash"

echo ""
echo "======================================================================"
echo "  All 4 services launching in separate terminals:"
echo ""
echo "   Terminal 1:  Ollama LLM Server    http://localhost:11434"
echo "   Terminal 2:  FastAPI REST API     http://localhost:8000"
echo "                API Docs             http://localhost:8000/docs"
echo "   Terminal 3:  Next.js Frontend     http://localhost:3000"
echo "   Terminal 4:  Pipeline CLI         (manual scans)"
echo ""
echo "  Frontend ready in ~15 seconds."
echo "======================================================================"
echo ""
