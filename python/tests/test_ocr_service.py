"""
Unit tests for KanoAI OCRService.
Verifies sample catalog retrieval, engine routing, fallback mechanisms, and comparison mode.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ocr.ocr_service import OCRService


class TestOCRService(unittest.TestCase):
    def setUp(self):
        self.service = OCRService()

    def test_sample_catalogs_structure(self):
        samples = self.service.get_sample_catalogs()
        self.assertIsInstance(samples, list)
        self.assertGreaterEqual(len(samples), 5)

        for s in samples:
            self.assertIn("id", s)
            self.assertIn("title", s)
            self.assertIn("category", s)
            self.assertIn("recommended_engine", s)
            self.assertIn("image_url", s)
            self.assertIn("ground_truth", s)
            self.assertTrue(len(s["ground_truth"]) > 0)

    @patch.object(OCRService, "recognize")
    def test_compare_mode(self, mock_recognize):
        self.service.indic_photo.recognize = MagicMock(return_value={
            "success": True,
            "engine": "indic_photo_ocr",
            "text": "ગુજરાતી ટેક્સ્ટ ૧",
            "boxes": []
        })
        self.service.hcr.recognize = MagicMock(return_value={
            "success": True,
            "engine": "gujarati_hcr",
            "text": "ગુજરાતી ટેક્સ્ટ ૨",
            "boxes": []
        })

        res = self.service.compare("dummy_base64_data")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("mode"), "comparison")
        self.assertIn("indic_photo_ocr", res.get("results", {}))
        self.assertIn("gujarati_hcr", res.get("results", {}))

    def test_engine_routing_trocr(self):
        self.service.trocr.recognize = MagicMock(return_value={
            "success": True,
            "engine": "gujarati_trocr",
            "text": "પંચતંત્ર"
        })
        res = self.service.recognize("dummy_image", engine="gujarati_trocr")
        self.assertTrue(res.get("success"))
        self.service.trocr.recognize.assert_called_once()

    def test_engine_routing_hcr(self):
        self.service.hcr.recognize = MagicMock(return_value={
            "success": True,
            "engine": "gujarati_hcr",
            "text": "ગાંધીજીના સુવિચારો"
        })
        res = self.service.recognize("dummy_image", engine="gujarati_hcr")
        self.assertTrue(res.get("success"))
        self.service.hcr.recognize.assert_called_once()

    def test_engine_routing_indic_photo(self):
        self.service.indic_photo.recognize = MagicMock(return_value={
            "success": True,
            "engine": "indic_photo_ocr",
            "text": "અમદાવાદ જંકશન"
        })
        res = self.service.recognize("dummy_image", engine="indic_photo_ocr")
        self.assertTrue(res.get("success"))
        self.service.indic_photo.recognize.assert_called_once()

    def test_indic_photo_fallback_to_trocr_when_unreachable(self):
        self.service.indic_photo.recognize = MagicMock(return_value={
            "success": False,
            "error": "Connection refused"
        })
        self.service.trocr.recognize = MagicMock(return_value={
            "success": True,
            "engine": "gujarati_trocr",
            "text": "Fallback text from TrOCR"
        })

        res = self.service.recognize("dummy_image", engine="indic_photo_ocr")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("text"), "Fallback text from TrOCR")
        self.assertIn("auto-transcribed", res.get("note", ""))


if __name__ == "__main__":
    unittest.main()
