"""
KanoAI Gujarati Text-to-Speech API Server
Lightweight HTTP microservice with CORS support.
"""

import os
import sys
import json
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    from .tts_service import TTSService
except (ImportError, ValueError):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(current_dir))
    from tts.tts_service import TTSService


class TTSRequestHandler(BaseHTTPRequestHandler):
    service = TTSService()

    def _set_cors_headers(self, status: int = 200, content_type: str = "application/json"):
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Type", content_type)
        self.end_headers()

    def do_OPTIONS(self):
        self._set_cors_headers(200)

    def do_GET(self):
        if self.path in ["/api/health", "/health"]:
            self._set_cors_headers(200)
            self.wfile.write(json.dumps({"status": "ok", "service": "kano_gujarati_tts"}).encode("utf-8"))
        elif self.path in ["/api/presets", "/presets", "/api/tts/presets"]:
            self._set_cors_headers(200)
            self.wfile.write(json.dumps(self.service.get_presets(), ensure_ascii=False).encode("utf-8"))
        elif self.path in ["/api/voices", "/voices", "/api/tts/voices"]:
            self._set_cors_headers(200)
            voices = self.service.get_presets().get("speakers", [])
            self.wfile.write(json.dumps(voices, ensure_ascii=False).encode("utf-8"))
        else:
            self._set_cors_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length)

        try:
            body = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception as e:
            self._set_cors_headers(400)
            self.wfile.write(json.dumps({"error": f"Invalid JSON payload: {str(e)}"}).encode("utf-8"))
            return

        if self.path in ["/api/synthesize", "/api/tts/synthesize"]:
            text = body.get("text", "").strip()
            engine = body.get("engine", "indic_f5").strip()
            speaker_id = body.get("speaker_id", "dhara")

            if not text:
                self._set_cors_headers(400)
                self.wfile.write(json.dumps({"error": "Missing 'text' in request"}).encode("utf-8"))
                return

            speed = float(body.get("speed", 0.75))
            try:
                result = self.service.synthesize(
                    engine=engine,
                    text=text,
                    speaker_id=speaker_id,
                    ref_text=body.get("ref_text"),
                    ref_audio_path=body.get("ref_audio_path"),
                    hf_token=body.get("hf_token"),
                    api_url=body.get("api_url"),
                    f5_api_url=body.get("f5_api_url"),
                    tts_api_url=body.get("tts_api_url"),
                    speed=speed,
                )
                self._set_cors_headers(200)
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"error": str(e), "engine": engine}).encode("utf-8"))

        elif self.path == "/api/compare":
            text = body.get("text", "").strip()
            speaker_id = body.get("speaker_id", "dhara")
            speed = float(body.get("speed", 0.75))

            if not text:
                self._set_cors_headers(400)
                self.wfile.write(json.dumps({"error": "Missing 'text' in request"}).encode("utf-8"))
                return

            try:
                result = self.service.compare(
                    text=text,
                    speaker_id=speaker_id,
                    hf_token=body.get("hf_token"),
                    f5_api_url=body.get("f5_api_url") or body.get("api_url"),
                    tts_api_url=body.get("tts_api_url"),
                    ref_text=body.get("ref_text"),
                    ref_audio_path=body.get("ref_audio_path"),
                    speed=speed,
                )
                self._set_cors_headers(200)
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"error": str(e), "engine": "compare"}).encode("utf-8"))
        else:
            self._set_cors_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def log_message(self, format, *args):
        # Clean logging
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")


def run_server(host: str = "127.0.0.1", port: int = 8000):
    server = HTTPServer((host, port), TTSRequestHandler)
    print(f"==================================================")
    print(f"🎙️  KanoAI Gujarati TTS API Server running!")
    print(f"🌐  Host: http://{host}:{port}")
    print(f"🔊  Engines: Meta MMS-TTS (Offline), IndicF5 & Indic-TTS")
    print(f"👉  Health: http://{host}:{port}/api/health")
    print(f"==================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KanoAI Gujarati TTS Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host binding (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port binding (default: 8000)")
    args = parser.parse_args()
    run_server(args.host, args.port)
