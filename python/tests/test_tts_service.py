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

        engine_ids = [e["id"] for e in presets["engines"]]
        self.assertIn("mms_tts", engine_ids)
        self.assertIn("piper_tts", engine_ids)
        self.assertIn("espeak_ng", engine_ids)
        self.assertIn("indic_f5", engine_ids)
        self.assertIn("indic_tts", engine_ids)
        self.assertIn("piper_voices", presets)

    def test_synthesize_routing_mms_tts(self):
        self.service.mms_tts.synthesize = MagicMock(return_value={
            "offline": True,
            "engine": "mms_tts",
            "audio_base64": "mms_dummy_b64"
        })
        res = self.service.synthesize("mms_tts", "ક")
        self.assertTrue(res.get("offline"))
        self.assertEqual(res.get("engine"), "mms_tts")
        self.service.mms_tts.synthesize.assert_called_once()

    def test_synthesize_routing_piper_tts(self):
        self.service.piper_tts.synthesize = MagicMock(return_value={
            "engine": "piper_tts",
            "audio_base64": "piper_dummy_b64",
            "sample_rate": 22050,
        })
        res = self.service.synthesize("piper_tts", "નમસ્તે", voice_id="rohan")
        self.assertEqual(res.get("engine"), "piper_tts")
        self.service.piper_tts.synthesize.assert_called_once()

    def test_synthesize_routing_espeak_ng(self):
        self.service.espeak_tts.synthesize = MagicMock(return_value={
            "engine": "espeak_ng",
            "audio_base64": "espeak_dummy_b64",
            "lang": "gu",
        })
        res = self.service.synthesize("espeak_ng", "નમસ્તે", lang="gu")
        self.assertEqual(res.get("engine"), "espeak_ng")
        self.service.espeak_tts.synthesize.assert_called_once()

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

    def test_compare_synthesizes_all_engines(self):
        self.service.mms_tts.synthesize = MagicMock(return_value={
            "offline": True,
            "engine": "mms_tts",
            "audio_base64": "mms_audio"
        })
        self.service.piper_tts.synthesize = MagicMock(return_value={
            "engine": "piper_tts",
            "audio_base64": "piper_audio"
        })
        self.service.espeak_tts.synthesize = MagicMock(return_value={
            "engine": "espeak_ng",
            "audio_base64": "espeak_audio"
        })
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
        self.assertTrue(res.get("has_mms"))
        self.assertTrue(res.get("has_piper"))
        self.assertTrue(res.get("has_espeak"))
        self.assertTrue(res.get("has_f5"))
        self.assertTrue(res.get("has_tts"))
        self.assertEqual(res.get("mms_tts", {}).get("audio_base64"), "mms_audio")
        self.assertEqual(res.get("piper_tts", {}).get("audio_base64"), "piper_audio")
        self.assertEqual(res.get("espeak_ng", {}).get("audio_base64"), "espeak_audio")
        self.assertEqual(res.get("indic_f5", {}).get("audio_base64"), "f5_audio")
        self.assertEqual(res.get("indic_tts", {}).get("audio_base64"), "tts_audio")


if __name__ == "__main__":
    unittest.main()
