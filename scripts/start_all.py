#!/usr/bin/env python3
"""
KanoAI Suite - One-Click Server & Web Launcher (Cross-Platform Python)
Starts the Unified Backend API Server (OCR + TTS) on port 8000,
Standalone IndicPhotoOCR Server on port 7860,
Standalone Gujarati TrOCR Server on port 7862,
Local Web Studio HTTP Server on port 8085,
verifies health checks, and opens the suite in your default web browser.
"""

import os
import sys
import time
import signal
import socket
import argparse
import subprocess
import webbrowser
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(SCRIPT_DIR, "docs", "index.html")):
    REPO_ROOT = SCRIPT_DIR
elif os.path.exists(os.path.join(SCRIPT_DIR, "..", "docs", "index.html")):
    REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
else:
    REPO_ROOT = SCRIPT_DIR
DOCS_DIR = os.path.join(REPO_ROOT, "docs")


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def wait_for_url(url: str, timeout: float = 10.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "KanoAI-HealthCheck"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.4)
    return False


def get_python_executable() -> str:
    venv_py = os.path.join(REPO_ROOT, ".venv", "bin", "python3")
    if os.path.isfile(venv_py) and os.access(venv_py, os.X_OK):
        return venv_py

    venv_py_win = os.path.join(REPO_ROOT, ".venv", "Scripts", "python.exe")
    if os.path.isfile(venv_py_win):
        return venv_py_win

    return sys.executable


def get_trocr_python_executable() -> str:
    venv_trocr = os.path.join(REPO_ROOT, ".venv_trocr", "bin", "python")
    if os.path.isfile(venv_trocr) and os.access(venv_trocr, os.X_OK):
        return venv_trocr
    return get_python_executable()


def main():
    parser = argparse.ArgumentParser(description="KanoAI Suite Server Launcher")
    parser.add_argument("--api-port", type=int, default=8000, help="Port for Backend API (default: 8000)")
    parser.add_argument("--indic-port", type=int, default=7860, help="Port for IndicPhotoOCR (default: 7860)")
    parser.add_argument("--trocr-port", type=int, default=7862, help="Port for Gujarati TrOCR (default: 7862)")
    parser.add_argument("--tts-port", type=int, default=7861, help="Port for Indic-TTS (default: 7861)")
    parser.add_argument("--f5-port", type=int, default=7865, help="Port for IndicF5 (default: 7865)")
    parser.add_argument("--web-port", type=int, default=8085, help="Port for Web Studio (default: 8085)")
    parser.add_argument("--no-engines", action="store_true", help="Skip dedicated standalone OCR/TTS engines (ports 7860, 7861, 7862, 7865)")
    parser.add_argument("--tab", type=str, default="", choices=["", "animator", "handwriting", "tts", "ocr"], help="Tab to open")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    args = parser.parse_args()

    python_bin = get_python_executable()
    trocr_python_bin = get_trocr_python_executable()

    print("=" * 65)
    print("   🚀 KanoAI (ગુજરાતી Language & Intelligence Suite)")
    print("=" * 65)
    print(f"🐍 Python Runtime:       {python_bin}")
    if trocr_python_bin != python_bin:
        print(f"🧠 TrOCR Neural Runtime: {trocr_python_bin}")

    # Check port conflicts
    port_targets = [
        (args.api_port, "Backend API"),
        (args.web_port, "Web Studio")
    ]
    if not args.no_engines:
        port_targets.extend([
            (args.indic_port, "IndicPhotoOCR Engine"),
            (args.trocr_port, "TrOCR Engine"),
            (args.tts_port, "Indic-TTS Engine"),
            (args.f5_port, "IndicF5 Engine"),
        ])

    for port, label in port_targets:
        if is_port_in_use(port):
            print(f"⚠️  Port {port} ({label}) is already in use!")

    processes = []

    # 1. Start Local Standalone OCR & TTS Engines (if enabled)
    if not args.no_engines:
        trocr_script = os.path.join(REPO_ROOT, "python", "ocr", "run_local_trocr.py")
        print(f"🤖 Starting Local TrOCR Engine Server on port {args.trocr_port}...")
        trocr_proc = subprocess.Popen(
            [trocr_python_bin, trocr_script, "--port", str(args.trocr_port)],
            cwd=REPO_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        processes.append(("TrOCR", trocr_proc))

        indic_script = os.path.join(REPO_ROOT, "python", "ocr", "run_local_indic.py")
        print(f"🔬 Starting Local IndicPhotoOCR Engine Server on port {args.indic_port}...")
        indic_proc = subprocess.Popen(
            [
                python_bin,
                indic_script,
                "--port",
                str(args.indic_port),
                "--trocr-url",
                f"http://localhost:{args.trocr_port}/api/recognize",
            ],
            cwd=REPO_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        processes.append(("IndicPhotoOCR", indic_proc))

        tts_script = os.path.join(REPO_ROOT, "python", "tts", "run_local_indic_tts.py")
        print(f"🎙️ Starting Local Indic-TTS Engine Server on port {args.tts_port}...")
        tts_proc = subprocess.Popen(
            [python_bin, tts_script, "--port", str(args.tts_port)],
            cwd=REPO_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        processes.append(("Indic-TTS", tts_proc))

        f5_script = os.path.join(REPO_ROOT, "python", "tts", "run_local_indic_f5.py")
        print(f"🌊 Starting Local IndicF5 Engine Server on port {args.f5_port}...")
        f5_proc = subprocess.Popen(
            [python_bin, f5_script, "--port", str(args.f5_port)],
            cwd=REPO_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        processes.append(("IndicF5", f5_proc))

    # 2. Start Backend API Server
    ocr_server_script = os.path.join(REPO_ROOT, "python", "ocr", "server.py")
    print(f"⚡ Starting Unified Backend API Server (OCR & TTS) on port {args.api_port}...")
    api_proc = subprocess.Popen(
        [python_bin, ocr_server_script, "--port", str(args.api_port)],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    processes.append(("Backend API", api_proc))

    # 3. Start Web Studio Server
    print(f"🌐 Starting Web Studio HTTP Server on port {args.web_port}...")
    web_proc = subprocess.Popen(
        [python_bin, "-m", "http.server", str(args.web_port), "--directory", DOCS_DIR],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    processes.append(("Web Studio", web_proc))

    def shutdown(signum=None, frame=None):
        print("\n🛑 Shutting down KanoAI servers...")
        for name, proc in processes:
            try:
                proc.terminate()
            except Exception:
                pass
        for name, proc in processes:
            try:
                proc.wait(timeout=2)
            except Exception:
                proc.kill()
        print("✓ All servers stopped cleanly.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # 4. Wait for health checks
    print("⏳ Waiting for servers to initialize...")
    if not args.no_engines:
        if wait_for_url(f"http://localhost:{args.indic_port}/api/health", timeout=6.0):
            print(f"✓ IndicPhotoOCR ready: http://localhost:{args.indic_port}/api/health")
        if wait_for_url(f"http://localhost:{args.trocr_port}/health", timeout=6.0):
            print(f"✓ TrOCR Engine ready:   http://localhost:{args.trocr_port}/health")
        if wait_for_url(f"http://localhost:{args.tts_port}/", timeout=6.0):
            print(f"✓ Indic-TTS ready:     http://localhost:{args.tts_port}/")
        if wait_for_url(f"http://localhost:{args.f5_port}/", timeout=6.0):
            print(f"✓ IndicF5 Engine ready: http://localhost:{args.f5_port}/")

    if wait_for_url(f"http://localhost:{args.api_port}/api/health", timeout=8.0):
        print(f"✓ Backend API ready:    http://localhost:{args.api_port}/api/health")
    else:
        print("⚠️  Warning: Backend API did not respond within timeout.")

    if wait_for_url(f"http://localhost:{args.web_port}/", timeout=8.0):
        print(f"✓ Web Studio ready:     http://localhost:{args.web_port}/")
    else:
        print("⚠️  Warning: Web Studio did not respond within timeout.")

    tab_map = {
        "handwriting": "handwriting/",
        "tts": "#tts",
        "ocr": "#ocr",
        "animator": "#animator",
    }
    path_suffix = tab_map.get(args.tab, "")
    url = f"http://localhost:{args.web_port}/{path_suffix}"

    print("")
    print("=" * 65)
    print("   🎉 KanoAI Suite is Live!")
    print("=" * 65)
    print(f"   🖋️  Stroke Animator & Audio:   http://localhost:{args.web_port}/")
    print(f"   ✍️  Handwriting Practice Suite: http://localhost:{args.web_port}/handwriting/")
    print(f"   🗣️  Text-to-Speech (TTS) Studio:http://localhost:{args.web_port}/#tts")
    print(f"   📸  OCR & Vision Studio:        http://localhost:{args.web_port}/#ocr")
    print(f"   ⚡  Unified Backend API:        http://localhost:{args.api_port}/api/health")
    if not args.no_engines:
        print(f"   🔬  IndicPhotoOCR (Port 7860):  http://localhost:{args.indic_port}/api/health")
        print(f"   🤖  Gujarati TrOCR (Port 7862): http://localhost:{args.trocr_port}/health")
        print(f"   🎙️  Indic-TTS (Port 7861):     http://localhost:{args.tts_port}/")
        print(f"   🌊  IndicF5 (Port 7865):        http://localhost:{args.f5_port}/")
    print(f"   🧠  Offline Neural TTS:         Meta MMS-TTS, Piper TTS, eSpeak-NG")
    print("=" * 65)
    print("   Press Ctrl+C anytime to stop all servers.")
    print("")

    if not args.no_browser:
        print(f"🚀 Opening {url} in your default browser...")
        webbrowser.open(url)

    # Keep alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
