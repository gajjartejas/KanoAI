"""
Unit tests for Piper TTS and eSpeak-NG Engines in KanoAI Gujarati Suite.
Tests:
- PiperTTSEngine voice resolution, numeral verbalization, and synthesis
- ESpeakTTSEngine phoneme extraction, character classification, and formant synthesis
- TTSService preset discovery, multi-engine dispatch, and compare function
"""

import os
import sys
import unittest
import base64

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tts.piper_tts import PiperTTSEngine, normalize_gujarati_for_piper
from tts.espeak_tts import ESpeakTTSEngine
from tts.tts_service import TTSService


class TestPiperTTSEngine(unittest.TestCase):
    def setUp(self):
        self.engine = PiperTTSEngine()

    def test_numeral_verbalization(self):
        self.assertEqual(normalize_gujarati_for_piper("૧"), "એક")
        self.assertEqual(normalize_gujarati_for_piper("૧૦"), "દસ")
        self.assertEqual(normalize_gujarati_for_piper("૧૦૦"), "સો")
        self.assertEqual(normalize_gujarati_for_piper("નમસ્તે ૧"), "નમસ્તે એક")

    def test_voice_info_resolution(self):
        rohan = self.engine.get_voice_info("rohan")
        self.assertEqual(rohan["id"], "rohan")
        self.assertEqual(rohan["sample_rate"], 22050)

        pratham = self.engine.get_voice_info("pratham")
        self.assertEqual(pratham["id"], "pratham")

        gujarati = self.engine.get_voice_info("gujarati_male")
        self.assertEqual(gujarati["language"], "gu")

    def test_mock_synthesis(self):
        res = self.engine.synthesize("નમસ્તે", voice_id="rohan", mock=True)
        self.assertEqual(res["engine"], "piper_tts")
        self.assertEqual(res["sample_rate"], 22050)
        self.assertEqual(res["format"], "wav")
        self.assertTrue(res["is_mock"])
        self.assertGreater(len(res["audio_base64"]), 100)
        self.assertGreater(res["duration_seconds"], 0)

    def test_real_or_cross_venv_synthesis(self):
        res = self.engine.synthesize("ક", voice_id="rohan")
        self.assertEqual(res["engine"], "piper_tts")
        self.assertIn("audio_base64", res)
        self.assertGreater(len(res["audio_base64"]), 1000)
        # Check that base64 decodes cleanly to WAV header
        raw_wav = base64.b64decode(res["audio_base64"])
        self.assertTrue(raw_wav.startswith(b"RIFF"))


class TestESpeakTTSEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ESpeakTTSEngine()

    def test_supported_languages(self):
        langs = self.engine.get_supported_languages()
        codes = [item["code"] for item in langs]
        self.assertIn("gu", codes)
        self.assertIn("hi", codes)

    def test_extract_phonemes_gujarati(self):
        info = self.engine.extract_phonemes("નમસ્તે", lang="gu")
        self.assertEqual(info["text"], "નમસ્તે")
        self.assertEqual(info["lang"], "gu")
        self.assertGreater(len(info["tokens"]), 0)
        self.assertTrue(len(info["ipa"]) > 0 or len(info["raw_phonemes"]) > 0)

    def test_extract_phonemes_consonants_and_matras(self):
        info = self.engine.extract_phonemes("કા", lang="gu")
        types = [t["type"] for t in info["tokens"]]
        self.assertIn("velar", types)
        self.assertIn("matra", types)

    def test_formant_synthesis_wav_generation(self):
        res = self.engine.synthesize("ગુજરાતી", lang="gu")
        self.assertEqual(res["engine"], "espeak_ng")
        self.assertEqual(res["lang"], "gu")
        self.assertIn("debug", res)
        self.assertIn("ipa", res["debug"])
        self.assertGreater(len(res["audio_base64"]), 1000)

        raw_wav = base64.b64decode(res["audio_base64"])
        self.assertTrue(raw_wav.startswith(b"RIFF"))

    def test_mock_synthesis(self):
        res = self.engine.synthesize("ક", mock=True)
        self.assertTrue(res["is_mock"])
        self.assertEqual(res["engine"], "espeak_ng")


class TestTTSServiceIntegration(unittest.TestCase):
    def setUp(self):
        self.service = TTSService()

    def test_presets_include_all_engines(self):
        presets = self.service.get_presets()
        engine_ids = [e["id"] for e in presets["engines"]]
        self.assertIn("mms_tts", engine_ids)
        self.assertIn("piper_tts", engine_ids)
        self.assertIn("espeak_ng", engine_ids)
        self.assertIn("indic_tts", engine_ids)
        self.assertIn("indic_f5", engine_ids)
        self.assertIn("piper_voices", presets)

    def test_synthesize_piper(self):
        res = self.service.synthesize(engine="piper_tts", text="નમસ્તે", mock=True)
        self.assertEqual(res["engine"], "piper_tts")

    def test_synthesize_espeak(self):
        res = self.service.synthesize(engine="espeak_ng", text="નમસ્તે", mock=True)
        self.assertEqual(res["engine"], "espeak_ng")

    def test_compare_all_engines(self):
        comp = self.service.compare("ક", mock=True)
        self.assertTrue(comp["has_mms"])
        self.assertTrue(comp["has_piper"])
        self.assertTrue(comp["has_espeak"])
        self.assertTrue(comp["has_f5"])
        self.assertTrue(comp["has_tts"])


if __name__ == "__main__":
    unittest.main()
