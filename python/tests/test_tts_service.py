"""
Unit tests for KanoAI TTSService.
Verifies preset catalogs, engine routing, and comparison synthesis.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tts.tts_service import TTSService, DEFAULT_GUJARATI_SAMPLES


class TestTTSService(unittest.TestCase):
    def setUp(self):
        self.service = TTSService()

    def test_presets_structure(self):
        presets = self.service.get_presets()
        self.assertIn("samples", presets)
        self.assertIn("speakers", presets)
        self.assertIn("engines", presets)

        self.assertGreaterEqual(len(presets["samples"]), 5)
        for sample in presets["samples"]:
            self.assertIn("id", sample)
            self.assertIn("text", sample)
            self.assertIn("title", sample)

        speakers = presets["speakers"]
        speaker_ids = [s["id"] for s in speakers]
        self.assertIn("dhara", speaker_ids)
        self.assertIn("parth", speaker_ids)

    def test_synthesize_routing_indic_f5(self):
        self.service.indic_f5.synthesize = MagicMock(return_value={
            "success": True,
            "engine": "indic_f5",
            "audio_base64": "dummy_b64"
        })
        res = self.service.synthesize("indic_f5", "નમસ્તે")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("engine"), "indic_f5")
        self.service.indic_f5.synthesize.assert_called_once()

    def test_synthesize_routing_indic_tts(self):
        self.service.indic_tts.synthesize = MagicMock(return_value={
            "success": True,
            "engine": "indic_tts",
            "audio_base64": "dummy_b64"
        })
        res = self.service.synthesize("indic_tts", "નમસ્તે", speaker_id="parth")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("engine"), "indic_tts")
        self.service.indic_tts.synthesize.assert_called_once()

    def test_synthesize_unknown_engine_raises_error(self):
        with self.assertRaises(ValueError):
            self.service.synthesize("unknown_engine_xyz", "નમસ્તે")

    def test_compare_synthesizes_both_engines(self):
        self.service.indic_f5.synthesize = MagicMock(return_value={
            "success": True,
            "engine": "indic_f5",
            "audio_base64": "f5_audio"
        })
        self.service.indic_tts.synthesize = MagicMock(return_value={
            "success": True,
            "engine": "indic_tts",
            "audio_base64": "tts_audio"
        })

        res = self.service.compare("ગુજરાતી ભાષા")
        self.assertEqual(res.get("text"), "ગુજરાતી ભાષા")
        self.assertTrue(res.get("has_f5"))
        self.assertTrue(res.get("has_tts"))
        self.assertEqual(res.get("indic_f5", {}).get("audio_base64"), "f5_audio")
        self.assertEqual(res.get("indic_tts", {}).get("audio_base64"), "tts_audio")


if __name__ == "__main__":
    unittest.main()
