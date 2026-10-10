"""
Unit tests for GujaratiHCR cursive handwriting segmentation and recognition.
"""

import os
import sys
import unittest
import numpy as np
import cv2
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ocr.handwriting_hcr import GujaratiHCR


class TestGujaratiHCR(unittest.TestCase):
    def setUp(self):
        self.hcr = GujaratiHCR()

    def _create_synthetic_text_image(self):
        """Creates a synthetic binary image with two white text bars on black background."""
        img = np.zeros((200, 300, 3), dtype=np.uint8)
        # Line 1: y from 30 to 60, x from 20 to 250
        cv2.rectangle(img, (20, 30), (250, 60), (255, 255, 255), -1)
        # Line 2: y from 100 to 130, x from 40 to 220
        cv2.rectangle(img, (40, 100), (220, 130), (255, 255, 255), -1)
        return img

    def test_preprocess(self):
        synthetic = self._create_synthetic_text_image()
        gray, binary, cleaned = self.hcr.preprocess(synthetic)

        self.assertEqual(gray.shape, (200, 300))
        self.assertEqual(binary.shape, (200, 300))
        self.assertEqual(cleaned.shape, (200, 300))
        self.assertEqual(len(np.unique(binary)), 2)

    def test_segment_lines_and_words(self):
        synthetic = self._create_synthetic_text_image()
        _, binary, _ = self.hcr.preprocess(synthetic)
        line_boxes, word_boxes = self.hcr.segment_lines_and_words(binary, synthetic.shape)

        self.assertGreaterEqual(len(line_boxes), 1)
        for b in line_boxes:
            self.assertIn("norm_x", b)
            self.assertIn("norm_y", b)
            self.assertIn("norm_width", b)
            self.assertIn("norm_height", b)
            self.assertGreaterEqual(b["norm_x"], 0.0)
            self.assertLessEqual(b["norm_x"] + b["norm_width"], 1.01)

    def test_draw_segmentation_overlay(self):
        synthetic = self._create_synthetic_text_image()
        _, binary, _ = self.hcr.preprocess(synthetic)
        line_boxes, word_boxes = self.hcr.segment_lines_and_words(binary, synthetic.shape)

        overlay = self.hcr.draw_segmentation_overlay(synthetic, line_boxes, word_boxes)
        self.assertEqual(overlay.shape, synthetic.shape)

    @patch("urllib.request.urlopen")
    def test_recognize_with_mocked_backend(self, mock_urlopen):
        synthetic = self._create_synthetic_text_image()
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"success": true, "text": "\\u0a97\\u0ac1\\u0a9c\\u0ab0\\u0abe\\u0aa4\\u0ac0", "lines": ["\\u0a97\\u0ac1\\u0a9c\\u0ab0\\u0abe\\u0aa4\\u0ac0"]}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = self.hcr.recognize(synthetic)
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("engine"), "gujarati_hcr")
        self.assertEqual(res.get("text"), "ગુજરાતી")
        self.assertEqual(res.get("lines"), ["ગુજરાતી"])
        self.assertIn("elapsed_seconds", res)
        self.assertIn("processed_image_base64", res)

    def test_recognize_neural_timeout_graceful_fallback(self):
        synthetic = self._create_synthetic_text_image()
        # Even if network calls fail/timeout, recognize must return valid schema with detected boxes
        with patch("urllib.request.urlopen", side_effect=Exception("Connection timed out")):
            res = self.hcr.recognize(synthetic)
            self.assertTrue(res.get("success"))
            self.assertEqual(res.get("engine"), "gujarati_hcr")
            self.assertIn("boxes", res)
            self.assertIn("metrics", res)


if __name__ == "__main__":
    unittest.main()
