"""
Unit tests for KanoAI OCR API Server RequestHandler.
"""

import os
import sys
import json
import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ocr.server import OCRRequestHandler


class DummySocket:
    def makefile(self, *args, **kwargs):
        return BytesIO()


class TestOCRServerHandler(unittest.TestCase):
    def _create_handler(self, method: str, path: str, body: bytes = b""):
        handler = OCRRequestHandler.__new__(OCRRequestHandler)
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
        self.assertIn('KanoAI Gujarati OCR', output)

    def test_get_samples_endpoint(self):
        handler = self._create_handler("GET", "/api/ocr/samples")
        handler.do_GET()

        output = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("200 OK", output)
        self.assertIn('"sample_1_printed_book"', output)

    def test_options_cors(self):
        handler = self._create_handler("OPTIONS", "/api/ocr/recognize")
        handler.do_OPTIONS()

        output = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("200 OK", output)
        self.assertIn("Access-Control-Allow-Origin: *", output)

    def test_post_recognize_invalid_json(self):
        handler = self._create_handler("POST", "/api/ocr/recognize", b"invalid-json{")
        handler.do_POST()

        output = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("400 Bad Request", output)
        self.assertIn("Invalid JSON payload", output)

    @patch("ocr.ocr_service.OCRService.recognize")
    def test_post_recognize_success(self, mock_recognize):
        mock_recognize.return_value = {
            "success": True,
            "engine": "gujarati_hcr",
            "text": "નમસ્તે"
        }
        payload = json.dumps({"image": "data:image/png;base64,dummy", "engine": "gujarati_hcr"}).encode("utf-8")
        handler = self._create_handler("POST", "/api/ocr/recognize", payload)
        handler.do_POST()

        output = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("200 OK", output)
        self.assertIn('"text": "નમસ્તે"', output)


if __name__ == "__main__":
    unittest.main()
