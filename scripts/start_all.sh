#!/usr/bin/env bash
# ==============================================================================
# KanoAI Suite - One-Click Launcher
# Starts the Unified Backend API Server (OCR + TTS), Standalone Local Engines
# (IndicPhotoOCR on port 7860, Gujarati TrOCR on port 7862), and Local Web Studio,
# verifies health checks, and opens the suite in your default web browser.
# ==============================================================================

set -e

# Resolve repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/docs/index.html" ]; then
  REPO_ROOT="${SCRIPT_DIR}"
elif [ -f "${SCRIPT_DIR}/../docs/index.html" ]; then
  REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
else
  REPO_ROOT="${SCRIPT_DIR}"
fi
DOCS_DIR="${REPO_ROOT}/docs"

# Default Ports
API_PORT=8000
WEB_PORT=8085
INDIC_PORT=7860
TROCR_PORT=7862
TTS_PORT=7861
F5_PORT=7865
TARGET_TAB=""
OPEN_BROWSER=true
ENABLE_ENGINES=true

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-browser)
      OPEN_BROWSER=false
      shift
      ;;
    --no-engines)
      ENABLE_ENGINES=false
      shift
      ;;
    --api-port)
      API_PORT="$2"
      shift 2
      ;;
    --web-port)
      WEB_PORT="$2"
      shift 2
      ;;
    --indic-port)
      INDIC_PORT="$2"
      shift 2
      ;;
    --trocr-port)
      TROCR_PORT="$2"
      shift 2
      ;;
    --tts-port)
      TTS_PORT="$2"
      shift 2
      ;;
    --f5-port)
      F5_PORT="$2"
      shift 2
      ;;
    --tab)
      TARGET_TAB="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: ./start_all.sh [options]"
      echo ""
      echo "Options:"
      echo "  --no-browser         Start servers without opening web browser"
      echo "  --no-engines         Skip dedicated standalone OCR engines (ports 7860, 7862)"
      echo "  --api-port <port>    Port for Python Backend API Server (default: 8000)"
      echo "  --indic-port <port>  Port for Local IndicPhotoOCR Engine (default: 7860)"
      echo "  --trocr-port <port>  Port for Local Gujarati TrOCR Engine (default: 7862)"
      echo "  --tts-port <port>    Port for Local Indic-TTS Engine (default: 7861)"
      echo "  --f5-port <port>     Port for Local IndicF5 Engine (default: 7865)"
      echo "  --web-port <port>    Port for Local Web Studio (default: 8085)"
      echo "  --tab <name>         Open directly to tab: animator, handwriting, tts, ocr"
      echo "  -h, --help           Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1 (run with --help for options)"
      shift
      ;;
  esac
done

# Color styling
BOLD='\033[1m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo -e "${BOLD}${CYAN}=================================================================${NC}"
echo -e "${BOLD}${CYAN}   🚀 KanoAI (ગુજરાતી Language & Intelligence Suite)   ${NC}"
echo -e "${BOLD}${CYAN}=================================================================${NC}"
echo ""

# 1. Locate Python executables
PYTHON_BIN=""
if [ -x "${REPO_ROOT}/.venv/bin/python3" ]; then
  PYTHON_BIN="${REPO_ROOT}/.venv/bin/python3"
elif [ -x "${REPO_ROOT}/.venv/bin/python" ]; then
  PYTHON_BIN="${REPO_ROOT}/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
else
  echo -e "${RED}❌ Error: Python 3 not found. Please install Python 3 or create a virtual environment (.venv).${NC}"
  exit 1
fi

TROCR_PYTHON_BIN="${PYTHON_BIN}"
if [ -x "${REPO_ROOT}/.venv_trocr/bin/python" ]; then
  TROCR_PYTHON_BIN="${REPO_ROOT}/.venv_trocr/bin/python"
elif [ -x "${REPO_ROOT}/.venv_trocr/bin/python3" ]; then
  TROCR_PYTHON_BIN="${REPO_ROOT}/.venv_trocr/bin/python3"
fi

echo -e "🐍 Primary Python: ${GREEN}${PYTHON_BIN}${NC}"
if [ "${TROCR_PYTHON_BIN}" != "${PYTHON_BIN}" ]; then
  echo -e "🧠 TrOCR Neural Python: ${GREEN}${TROCR_PYTHON_BIN}${NC}"
fi

# 2. Check and cleanup stale processes on target ports if needed
clean_port() {
  local port="$1"
  local name="$2"
  local pid
  pid=$(lsof -ti :"$port" 2>/dev/null || true)
  if [ -n "$pid" ]; then
    echo -e "${YELLOW}⚠️  Port ${port} (${name}) is already in use by PID ${pid}.${NC}"
    echo -e "   Stopping old process to avoid port conflicts..."
    kill -9 "$pid" 2>/dev/null || true
    sleep 1
  fi
}

clean_port "${API_PORT}" "Backend API"
clean_port "${WEB_PORT}" "Web Studio"
if [ "$ENABLE_ENGINES" = true ]; then
  clean_port "${INDIC_PORT}" "IndicPhotoOCR Engine"
  clean_port "${TROCR_PORT}" "TrOCR Engine"
  clean_port "${TTS_PORT}" "Indic-TTS Engine"
  clean_port "${F5_PORT}" "IndicF5 Engine"
fi

# Variables to track background PIDs
API_PID=""
WEB_PID=""
INDIC_PID=""
TROCR_PID=""
TTS_PID=""
F5_PID=""

# Cleanup trap on exit / Ctrl+C
cleanup() {
  echo ""
  echo -e "${YELLOW}🛑 Shutting down KanoAI servers...${NC}"
  for pid in "${INDIC_PID}" "${TROCR_PID}" "${TTS_PID}" "${F5_PID}" "${API_PID}" "${WEB_PID}"; do
    if [ -n "${pid}" ]; then
      kill "${pid}" 2>/dev/null || true
    fi
  done
  echo -e "${GREEN}✓ All servers stopped cleanly.${NC}"
  exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 3. Start Local Standalone OCR & TTS Engines (if enabled)
if [ "$ENABLE_ENGINES" = true ]; then
  echo -e "🤖 Starting Local TrOCR Engine Server on port ${TROCR_PORT}..."
  "${TROCR_PYTHON_BIN}" "${REPO_ROOT}/python/ocr/run_local_trocr.py" --port "${TROCR_PORT}" > /tmp/kano_trocr_server.log 2>&1 &
  TROCR_PID=$!

  echo -e "🔬 Starting Local IndicPhotoOCR Engine Server on port ${INDIC_PORT}..."
  "${PYTHON_BIN}" "${REPO_ROOT}/python/ocr/run_local_indic.py" --port "${INDIC_PORT}" --trocr-url "http://localhost:${TROCR_PORT}/api/recognize" > /tmp/kano_indic_server.log 2>&1 &
  INDIC_PID=$!

  echo -e "🎙️ Starting Local Indic-TTS Engine Server on port ${TTS_PORT}..."
  "${PYTHON_BIN}" "${REPO_ROOT}/python/tts/run_local_indic_tts.py" --port "${TTS_PORT}" > /tmp/kano_indic_tts_server.log 2>&1 &
  TTS_PID=$!

  echo -e "🌊 Starting Local IndicF5 Engine Server on port ${F5_PORT}..."
  "${PYTHON_BIN}" "${REPO_ROOT}/python/tts/run_local_indic_f5.py" --port "${F5_PORT}" > /tmp/kano_indic_f5_server.log 2>&1 &
  F5_PID=$!
fi

# 4. Start Backend API Server (python/ocr/server.py on port 8000)
echo -e "⚡ Starting Unified Backend API Server (OCR & TTS) on port ${API_PORT}..."
"${PYTHON_BIN}" "${REPO_ROOT}/python/ocr/server.py" --port "${API_PORT}" > /tmp/kano_api_server.log 2>&1 &
API_PID=$!

# 5. Start Web Studio Server (docs/ directory on port 8085)
echo -e "🌐 Starting Web Studio HTTP Server on port ${WEB_PORT}..."
"${PYTHON_BIN}" -m http.server "${WEB_PORT}" --directory "${DOCS_DIR}" > /tmp/kano_web_server.log 2>&1 &
WEB_PID=$!

# 6. Wait for servers to be healthy
echo -e "⏳ Waiting for servers to initialize..."

wait_for_url() {
  local url="$1"
  local max_attempts=20
  local attempt=1
  while [ $attempt -le $max_attempts ]; do
    if curl -s -f -o /dev/null "$url" 2>/dev/null; then
      return 0
    fi
    sleep 0.5
    attempt=$((attempt + 1))
  done
  return 1
}

if [ "$ENABLE_ENGINES" = true ]; then
  if wait_for_url "http://localhost:${INDIC_PORT}/api/health"; then
    echo -e "${GREEN}✓ Local IndicPhotoOCR Engine ready: http://localhost:${INDIC_PORT}/api/health${NC}"
  fi
  if wait_for_url "http://localhost:${TROCR_PORT}/health"; then
    echo -e "${GREEN}✓ Local Gujarati TrOCR Engine ready: http://localhost:${TROCR_PORT}/health${NC}"
  fi
  if wait_for_url "http://localhost:${TTS_PORT}/"; then
    echo -e "${GREEN}✓ Local Indic-TTS Engine ready: http://localhost:${TTS_PORT}/${NC}"
  fi
  if wait_for_url "http://localhost:${F5_PORT}/"; then
    echo -e "${GREEN}✓ Local IndicF5 Engine ready: http://localhost:${F5_PORT}/${NC}"
  fi
fi

if wait_for_url "http://localhost:${API_PORT}/api/health"; then
  echo -e "${GREEN}✓ Backend API is ready: http://localhost:${API_PORT}/api/health${NC}"
else
  echo -e "${RED}⚠️  Warning: Backend API did not respond within 10 seconds. Check /tmp/kano_api_server.log${NC}"
fi

if wait_for_url "http://localhost:${WEB_PORT}/"; then
  echo -e "${GREEN}✓ Web Studio is ready: http://localhost:${WEB_PORT}/${NC}"
else
  echo -e "${RED}⚠️  Warning: Web Studio did not respond within 10 seconds. Check /tmp/kano_web_server.log${NC}"
fi

# Determine target URL
URL="http://localhost:${WEB_PORT}/"
if [ -n "${TARGET_TAB}" ]; then
  case "${TARGET_TAB}" in
    handwriting)
      URL="http://localhost:${WEB_PORT}/handwriting/"
      ;;
    tts)
      URL="http://localhost:${WEB_PORT}/#tts"
      ;;
    ocr)
      URL="http://localhost:${WEB_PORT}/#ocr"
      ;;
    animator)
      URL="http://localhost:${WEB_PORT}/#animator"
      ;;
    *)
      URL="http://localhost:${WEB_PORT}/"
      ;;
  esac
fi

echo ""
echo -e "${BOLD}${GREEN}=================================================================${NC}"
echo -e "${BOLD}${GREEN}   🎉 KanoAI Suite is Live!${NC}"
echo -e "${BOLD}${GREEN}=================================================================${NC}"
echo -e "   🖋️  Stroke Animator & Audio:   ${CYAN}http://localhost:${WEB_PORT}/${NC}"
echo -e "   ✍️  Handwriting Practice Suite: ${CYAN}http://localhost:${WEB_PORT}/handwriting/${NC}"
echo -e "   🗣️  Text-to-Speech (TTS) Studio:${CYAN}http://localhost:${WEB_PORT}/#tts${NC}"
echo -e "   📸  OCR & Vision Studio:        ${CYAN}http://localhost:${WEB_PORT}/#ocr${NC}"
echo -e "   ⚡  Unified Backend API:        ${CYAN}http://localhost:${API_PORT}/api/health${NC}"
if [ "$ENABLE_ENGINES" = true ]; then
  echo -e "   🔬  IndicPhotoOCR (Port 7860):  ${CYAN}http://localhost:${INDIC_PORT}/api/health${NC}"
  echo -e "   🤖  Gujarati TrOCR (Port 7862): ${CYAN}http://localhost:${TROCR_PORT}/health${NC}"
  echo -e "   🎙️  Indic-TTS (Port 7861):      ${CYAN}http://localhost:${TTS_PORT}/${NC}"
  echo -e "   🌊  IndicF5 (Port 7865):        ${CYAN}http://localhost:${F5_PORT}/${NC}"
fi
echo -e "${BOLD}${GREEN}=================================================================${NC}"
echo -e "   Press ${BOLD}Ctrl+C${NC} anytime to stop all servers."
echo ""

# 7. Open Webpage in default browser
if [ "$OPEN_BROWSER" = true ]; then
  echo -e "🚀 Opening ${CYAN}${URL}${NC} in your browser..."
  if [[ "$OSTYPE" == "darwin"* ]]; then
    open "${URL}"
  elif [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "freebsd"* ]]; then
    if command -v xdg-open >/dev/null 2>&1; then
      xdg-open "${URL}" >/dev/null 2>&1 &
    elif command -v gnome-open >/dev/null 2>&1; then
      gnome-open "${URL}" >/dev/null 2>&1 &
    fi
  elif [[ "$OSTYPE" == "msys"* ]] || [[ "$OSTYPE" == "cygwin"* ]] || [[ "$OSTYPE" == "win32"* ]]; then
    start "${URL}"
  fi
fi

# Keep script running to maintain servers until user hits Ctrl+C
wait "${API_PID}" "${WEB_PID}" "${INDIC_PID}" "${TROCR_PID}" "${TTS_PID}" "${F5_PID}" 2>/dev/null || true
