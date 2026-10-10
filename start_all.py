#!/usr/bin/env python3
"""
KanoAI Suite - One-Click Server & Web Launcher (Cross-Platform Python)
Delegates to scripts/start_all.py
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(SCRIPT_DIR, "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from start_all import main

if __name__ == "__main__":
    main()
