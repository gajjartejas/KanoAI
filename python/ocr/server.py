"""
KanoAI Gujarati Optical Character Recognition (OCR) API Server
Lightweight HTTP microservice with CORS support.
Supports IndicPhotoOCR, Gujarati TrOCR, and GujaratiHCR.
"""

import os
import sys
import json
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from ocr.ocr_service import OCRService

try:
    from tts.tts_service import TTSService
    tts_service = TTSService()
except Exception:
    tts_service = None


class OCRRequestHandler(BaseHTTPRequestHandler):
    ocr_service = OCRService()

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
        clean_path = self.path.split("?")[0]
        if clean_path in ["/api/health", "/api/ocr/health", "/health"]:
            self._set_cors_headers(200)
            data = {
                "status": "ok",
                "service": "KanoAI Gujarati OCR & Vision Server",
                "engines": [
                    {
                        "id": "indic_photo_ocr",
                        "name": "Bhashini-IITJ IndicPhotoOCR",
                        "type": "Scene / Photo & Document Text",
                        "modes": ["offline", "online"],
                        "status": "active"
                    },
                    {
                        "id": "gujarati_trocr",
                        "name": "Gujarati TrOCR (umangchaudhari)",
                        "type": "Printed & Scanned OCR",
                        "status": "active"
                    },
                    {
                        "id": "gujarati_hcr",
                        "name": "GujaratiHCR Hybrid Pipeline",
                        "type": "Handwritten Character & Note OCR",
                        "status": "active"
                    }
                ],
                "has_tts": tts_service is not None
            }
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

        elif clean_path in ["/api/ocr/samples", "/api/samples"]:
            self._set_cors_headers(200)
            samples = self.ocr_service.get_sample_catalogs()
            self.wfile.write(json.dumps(samples, ensure_ascii=False).encode("utf-8"))

        elif clean_path in ["/api/presets", "/presets"] and tts_service:
            self._set_cors_headers(200)
            self.wfile.write(json.dumps(tts_service.get_presets(), ensure_ascii=False).encode("utf-8"))

        else:
            self._set_cors_headers(404)
            self.wfile.write(json.dumps({"error": f"Endpoint not found: {clean_path}"}).encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length)

        try:
            body = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception as e:
            self._set_cors_headers(400)
            self.wfile.write(json.dumps({"error": f"Invalid JSON payload: {str(e)}"}).encode("utf-8"))
            return

        clean_path = self.path.split("?")[0]

        # 1. OCR Recognize Endpoint
        if clean_path in ["/api/ocr/recognize", "/api/ocr/process", "/api/recognize"]:
            image_input = body.get("image") or body.get("image_base64")
            engine = body.get("engine", "indic_photo_ocr")
            lang = body.get("lang", "gujarati")
            hf_token = body.get("hf_token")
            api_url = body.get("api_url")
            mode = body.get("mode", "offline")
            sample_id = body.get("sample_id")

            if not image_input:
                self._set_cors_headers(400)
                self.wfile.write(json.dumps({"error": "Missing 'image' parameter in request"}).encode("utf-8"))
                return

            try:
                result = self.ocr_service.recognize(
                    image_input=image_input,
                    engine=engine,
                    lang=lang,
                    api_url=api_url,
                    hf_token=hf_token,
                    mode=mode
                )
                self._set_cors_headers(200)
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"error": str(e), "engine": engine}).encode("utf-8"))

        # 2. OCR Dual Comparison Endpoint
        elif clean_path in ["/api/ocr/compare"]:
            image_input = body.get("image") or body.get("image_base64")
            lang = body.get("lang", "gujarati")
            hf_token = body.get("hf_token")

            if not image_input:
                self._set_cors_headers(400)
                self.wfile.write(json.dumps({"error": "Missing 'image' parameter in request"}).encode("utf-8"))
                return

            try:
                result = self.ocr_service.compare(
                    image_input=image_input,
                    lang=lang,
                    hf_token=hf_token
                )
                self._set_cors_headers(200)
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

        # 3. TTS Speech Synthesis (if requested from OCR extracted text or TTS tab)
        elif clean_path in ["/api/synthesize"] and tts_service:
            text = body.get("text", "").strip()
            engine = body.get("engine", "indic_f5").strip()
            speaker_id = body.get("speaker_id", "dhara")
            speed = float(body.get("speed", 0.75))

            if not text:
                self._set_cors_headers(400)
                self.wfile.write(json.dumps({"error": "Missing 'text' in request"}).encode("utf-8"))
                return

            try:
                res = tts_service.synthesize(
                    engine=engine,
                    text=text,
                    speaker_id=speaker_id,
                    speed=speed,
                    hf_token=body.get("hf_token")
                )
                self._set_cors_headers(200)
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

        else:
            self._set_cors_headers(404)
            self.wfile.write(json.dumps({"error": f"Endpoint not found: {clean_path}"}).encode("utf-8"))


def run_server(host: str = "0.0.0.0", port: int = 8000):
    server_address = (host, port)
    httpd = HTTPServer(server_address, OCRRequestHandler)
    print("=" * 65)
    print(f"🚀 KanoAI Gujarati OCR & Vision Server running at:")
    print(f"   http://localhost:{port}")
    print(f"   Endpoints:")
    print(f"     • POST /api/ocr/recognize (Run OCR on image)")
    print(f"     • POST /api/ocr/compare   (Dual A/B OCR comparison)")
    print(f"     • GET  /api/ocr/samples   (List sample benchmark images)")
    print(f"     • GET  /api/ocr/health    (Service health & engine info)")
    if tts_service:
        print(f"     • POST /api/synthesize    (Voice playback bridge)")
    print("=" * 65)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down OCR server...")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KanoAI Gujarati OCR Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface (default 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default 8000)")
    args = parser.parse_args()
    run_server(args.host, args.port)
