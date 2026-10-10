"""
Unit tests for GujaratiTrOCR integration.
"""

import os
import sys
import unittest
import numpy as np
import cv2
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ocr.trocr_service import GujaratiTrOCR


class TestGujaratiTrOCR(unittest.TestCase):
    def setUp(self):
        self.trocr = GujaratiTrOCR()

    def _create_multi_line_image(self):
        img = np.ones((300, 400, 3), dtype=np.uint8) * 255
        # Line 1: dark text bar
        cv2.rectangle(img, (30, 40), (320, 80), (0, 0, 0), -1)
        # Line 2: dark text bar
        cv2.rectangle(img, (30, 140), (280, 180), (0, 0, 0), -1)
        return img

    def test_slice_lines(self):
        img = self._create_multi_line_image()
        line_crops = self.trocr._slice_lines(img)

        self.assertGreaterEqual(len(line_crops), 2)
        for lc in line_crops:
            self.assertIn("crop", lc)
            self.assertIn("bbox", lc)
            bbox = lc["bbox"]
            self.assertIn("norm_x", bbox)
            self.assertIn("norm_y", bbox)
            self.assertIn("norm_width", bbox)
            self.assertIn("norm_height", bbox)

    @patch("requests.post")
    def test_recognize_mock_local(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "text": "પંચતંત્રની બોધકથા\nચતુર સસલું",
            "lines": [{"text": "પંચતંત્રની બોધકથા"}, {"text": "ચતુર સસલું"}],
            "boxes": [
                {"norm_x": 0.1, "norm_y": 0.1, "norm_width": 0.5, "norm_height": 0.2},
                {"norm_x": 0.1, "norm_y": 0.4, "norm_width": 0.5, "norm_height": 0.2}
            ]
        }
        mock_post.return_value = mock_response

        img = self._create_multi_line_image()
        res = self.trocr.recognize(img, api_url="http://localhost:7862/api/recognize", mode="offline")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("engine"), "gujarati_trocr")
        self.assertIn("પંચતંત્રની બોધકથા", res.get("text", ""))
        self.assertEqual(len(res.get("lines", [])), 2)
        self.assertEqual(len(res.get("boxes", [])), 2)

    @patch("requests.post")
    def test_recognize_mock_online(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"generated_text": "ગુજરાતી ભાષા"}]
        mock_post.return_value = mock_response

        img = self._create_multi_line_image()
        res = self.trocr.recognize(img, mode="online", hf_token="hf_mock_token")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("engine"), "gujarati_trocr")
        self.assertIn("ગુજરાતી ભાષા", res.get("text", ""))


if __name__ == "__main__":
    unittest.main()
