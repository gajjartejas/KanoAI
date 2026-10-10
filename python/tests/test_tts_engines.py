"""
Unit tests for IndicF5 and IndicTTS engines.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tts.indic_f5_tts import IndicF5Engine
from tts.indic_tts import IndicTTSEngine


class TestTTSEngines(unittest.TestCase):
    def test_indic_f5_empty_text_raises_value_error(self):
        engine = IndicF5Engine()
        with self.assertRaises(ValueError):
            engine.synthesize(text="   ")

    def test_indic_tts_empty_text_raises_value_error(self):
        engine = IndicTTSEngine()
        with self.assertRaises(ValueError):
            engine.synthesize(text="")

    def test_indic_tts_speakers_registry(self):
        engine = IndicTTSEngine()
        self.assertIn("dhara", engine.SPEAKERS)
        self.assertIn("parth", engine.SPEAKERS)
        self.assertEqual(engine.SPEAKERS["dhara"]["gender"], "female")
        self.assertEqual(engine.SPEAKERS["parth"]["gender"], "male")

    @patch("requests.post")
    def test_indic_tts_mock_synthesis(self, mock_post):
        engine = IndicTTSEngine()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "audio_base64": "UklGRi4AAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=",
            "sample_rate": 22050,
            "duration": 1.5
        }
        mock_post.return_value = mock_resp

        res = engine.synthesize(
            text="નમસ્તે",
            speaker_id="dhara",
            api_url="http://mock-tts-api"
        )
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("engine"), "indic_tts")
        self.assertEqual(res.get("speaker_id"), "dhara")
        self.assertIn("audio_base64", res)

    def test_indic_tts_mock_flag(self):
        engine = IndicTTSEngine()
        res = engine.synthesize(text="નમસ્તે", mock=True)
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("engine"), "indic_tts")
        self.assertIn("audio_base64", res)

    @patch("requests.post")
    def test_indic_tts_remote_failure_fallback(self, mock_post):
        mock_post.side_effect = Exception("Remote HF connection timed out")
        engine = IndicTTSEngine()
        # Should gracefully fallback to local neural synthesis instead of raising 500
        res = engine.synthesize(
            text="નમસ્તે",
            speaker_id="dhara",
            api_url="https://broken-space.hf.space",
            mock=True,
        )
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("engine"), "indic_tts")
        self.assertIn("audio_base64", res)


if __name__ == "__main__":
    unittest.main()
