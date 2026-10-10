#!/usr/bin/env python3
"""
KanoAI Test Runner (Cross-Platform Python)
Runs unit tests across OCR, TTS, and core services.
"""

import os
import sys
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(SCRIPT_DIR, "docs", "index.html")):
    REPO_ROOT = SCRIPT_DIR
elif os.path.exists(os.path.join(SCRIPT_DIR, "..", "docs", "index.html")):
    REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
else:
    REPO_ROOT = SCRIPT_DIR

sys.path.insert(0, os.path.join(REPO_ROOT, "python"))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))


def main():
    print("=" * 65)
    print("  🧪 Running KanoAI Test Suite (OCR, TTS, System Utilities)")
    print("=" * 65)
    print(f"🐍 Python: {sys.executable}")
    print(f"📁 Root:   {REPO_ROOT}\n")

    test_dir = os.path.join(REPO_ROOT, "python", "tests")
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=test_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 65)
    if result.wasSuccessful():
        print(f"  ✓ All {result.testsRun} tests passed successfully!")
        print("=" * 65)
        sys.exit(0)
    else:
        print(f"  ❌ {len(result.failures)} failures, {len(result.errors)} errors out of {result.testsRun} tests.")
        print("=" * 65)
        sys.exit(1)


if __name__ == "__main__":
    main()
