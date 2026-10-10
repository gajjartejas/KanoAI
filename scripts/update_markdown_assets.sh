#!/usr/bin/env bash
set -e

# update_markdown_assets.sh
# Captures high-resolution, pixel-perfect screenshots of KanoAI web suites using headless Chrome,
# then compresses them with pngquant and optipng.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCS_DIR="${REPO_ROOT}/docs"
ASSETS_DIR="${DOCS_DIR}/assets"
PORT=8899
SERVER_PID=""

echo "🚀 Starting KanoAI Markdown & Screenshot Asset Updater..."

# 1. Ensure output assets directory exists
mkdir -p "${ASSETS_DIR}"

# 2. Check if server is already running on PORT, else spin up background http-server
if curl -s "http://localhost:${PORT}/" >/dev/null 2>&1; then
  echo "✓ Local web server already active on port ${PORT}."
else
  echo "🌐 Launching local http-server on port ${PORT}..."
  npx http-server "${DOCS_DIR}" -p ${PORT} -c-1 > /tmp/kano_server.log 2>&1 &
  SERVER_PID=$!
  sleep 2
fi

# Cleanup handler if server was launched by this script
cleanup() {
  if [ -n "${SERVER_PID}" ]; then
    echo "🛑 Shutting down temporary local server (PID: ${SERVER_PID})..."
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

# 3. Locate Google Chrome
CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if [ ! -x "${CHROME_BIN}" ]; then
  CHROME_BIN="$(which google-chrome || which chromium || true)"
fi

if [ -z "${CHROME_BIN}" ] || [ ! -x "${CHROME_BIN}" ]; then
  echo "❌ Error: Google Chrome / Chromium not found."
  exit 1
fi

echo "📸 Capturing screenshots via ${CHROME_BIN}..."

# 3.1 Stroke Animator & Audio (Dark Theme - Default)
"${CHROME_BIN}" --headless --disable-gpu --screenshot="${ASSETS_DIR}/preview.png" --window-size=1280,820 "http://localhost:${PORT}/" >/dev/null 2>&1 || true

# 3.2 Stroke Animator & Audio (Light Theme)
"${CHROME_BIN}" --headless --disable-gpu --screenshot="${ASSETS_DIR}/preview-light.png" --window-size=1280,820 "http://localhost:${PORT}/?theme=light" >/dev/null 2>&1 || true

# 3.3 Handwriting Recognition & Practice Suite
"${CHROME_BIN}" --headless --disable-gpu --screenshot="${ASSETS_DIR}/preview-handwriting.png" --window-size=1280,820 "http://localhost:${PORT}/handwriting/" >/dev/null 2>&1 || true

# 3.4 Gujarati Text-to-Speech (TTS) Studio
"${CHROME_BIN}" --headless --disable-gpu --screenshot="${ASSETS_DIR}/preview-tts.png" --window-size=1280,820 "http://localhost:${PORT}/#tts" >/dev/null 2>&1 || true

# 3.5 Gujarati OCR & Vision Studio
"${CHROME_BIN}" --headless --disable-gpu --screenshot="${ASSETS_DIR}/preview-ocr.png" --window-size=1280,820 "http://localhost:${PORT}/#ocr" >/dev/null 2>&1 || true

echo "✓ Raw screenshots captured."

# 4. Compress PNGs using pngquant and optipng
echo "🗜️ Compressing screenshots..."

if command -v pngquant >/dev/null 2>&1; then
  pngquant --quality=75-90 --skip-if-larger --force --ext .png "${ASSETS_DIR}"/preview*.png || true
  echo "✓ pngquant compression applied."
else
  echo "⚠️ pngquant not installed, skipping."
fi

if command -v optipng >/dev/null 2>&1; then
  optipng -o5 -strip all "${ASSETS_DIR}"/preview*.png || true
  echo "✓ optipng optimization applied."
else
  echo "⚠️ optipng not installed, skipping."
fi

# Print final file sizes
echo "📊 Final asset sizes:"
ls -lh "${ASSETS_DIR}"/preview*.png

echo "✨ Markdown and screenshot assets successfully updated!"
