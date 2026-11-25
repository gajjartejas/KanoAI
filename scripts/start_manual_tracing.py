#!/usr/bin/env python3
"""Launch the local manual tracing studio without loading OCR/TTS models."""
import runpy
import sys
from pathlib import Path

studio = Path(__file__).resolve().parents[1] / 'python/manual_tracing'
sys.path.insert(0, str(studio))
runpy.run_path(str(studio / 'server.py'), run_name='__main__')
