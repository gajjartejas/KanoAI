"""
Unit tests for KanoAI TTS API Server RequestHandler.
"""

import os
import sys
import json
import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tts.server import TTSRequestHandler


class DummySocket:
    def makefile(self, *args, **kwargs):
        return BytesIO()


class TestTTSServerHandler(unittest.TestCase):
    def _create_handler(self, method: str, path: str, body: bytes = b""):
        handler = TTSRequestHandler.__new__(TTSRequestHandler)
        handler.command = method
        handler.path = path
        handler.request_version = "HTTP/1.1"
        handler.requestline = f"{method} {path} HTTP/1.1"
        handler.log_request = lambda *args, **kwargs: None
        handler.log_message = lambda *args, **kwargs: None
        handler.headers = {"Content-Length": str(len(body)), "Content-Type": "application/json"}
        handler.rfile = BytesIO(body)
        handler.wfile = BytesIO()
        handler.connection = DummySocket()
        handler.client_address = ("127.0.0.1", 12345)
        handler.close_connection = False
        return handler

    def test_get_health_endpoint(self):
        handler = self._create_handler("GET", "/api/health")
        handler.do_GET()

        output = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("200 OK", output)
        self.assertIn('"status": "ok"', output)
        self.assertIn('"service": "kano_gujarati_tts"', output)

    def test_get_voices_endpoint(self):
        handler = self._create_handler("GET", "/api/tts/voices")
        handler.do_GET()

        output = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("200 OK", output)
        self.assertIn('"dhara"', output)
        self.assertIn('"parth"', output)

    def test_options_cors(self):
        handler = self._create_handler("OPTIONS", "/api/tts/synthesize")
        handler.do_OPTIONS()

        output = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("200 OK", output)
        self.assertIn("Access-Control-Allow-Origin: *", output)

    def test_post_synthesize_invalid_json(self):
        handler = self._create_handler("POST", "/api/tts/synthesize", b"invalid-payload{")
        handler.do_POST()

        output = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("400 Bad Request", output)
        self.assertIn("Invalid JSON payload", output)

    @patch("tts.tts_service.TTSService.synthesize")
    def test_post_synthesize_success(self, mock_synthesize):
        mock_synthesize.return_value = {
            "success": True,
            "engine": "indic_tts",
            "audio_base64": "dummy_b64_audio"
        }
        payload = json.dumps({"text": "નમસ્તે", "engine": "indic_tts", "speaker_id": "dhara"}).encode("utf-8")
        handler = self._create_handler("POST", "/api/tts/synthesize", payload)
        handler.do_POST()

        output = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("200 OK", output)
        self.assertIn('"audio_base64": "dummy_b64_audio"', output)


if __name__ == "__main__":
    unittest.main()
