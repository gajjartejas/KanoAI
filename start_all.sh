#!/usr/bin/env bash
# ==============================================================================
# KanoAI Suite - One-Click Launcher
# Delegates to scripts/start_all.sh
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "${SCRIPT_DIR}/scripts/start_all.sh" "$@"
