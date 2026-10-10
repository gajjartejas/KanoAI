"""
Unit tests for Meta MMS-TTS Engine (facebook/mms-tts-guj).
Tests:
- Numeral verbalization (૧ -> એક, ૧૦ -> દસ)
- Empty text validation
- In-process or mock synthesis output format
- Waveform audio serialization
- File writing (WAV and MP3 conversion fallback)
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tts.mms_tts import MMSTTSEngine, normalize_gujarati_text, array_to_wav


class TestMMSTTSEngine(unittest.TestCase):
    def setUp(self):
        self.engine = MMSTTSEngine()

    def test_empty_text_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.engine.synthesize("   ")

    def test_numeral_normalization_single_digit(self):
        self.assertEqual(normalize_gujarati_text("૧"), "એક")
        self.assertEqual(normalize_gujarati_text("૫"), "પાંચ")
        self.assertEqual(normalize_gujarati_text("૦"), "શૂન્ય")

    def test_numeral_normalization_composite_numbers(self):
        self.assertEqual(normalize_gujarati_text("૧૦"), "દસ")
        self.assertEqual(normalize_gujarati_text("૨૦"), "વીસ")
        self.assertEqual(normalize_gujarati_text("૧૦૦"), "સો")

    def test_text_normalization_with_consonants(self):
        self.assertEqual(normalize_gujarati_text("ક"), "ક")
        self.assertEqual(normalize_gujarati_text("નમસ્તે"), "નમસ્તે")
        self.assertEqual(normalize_gujarati_text("કા"), "કા")

    def test_mock_synthesis_structure(self):
        res = self.engine.synthesize("ક", mock=True)
        self.assertTrue(res.get("offline"))
        self.assertEqual(res.get("engine"), "mms_tts")
        self.assertEqual(res.get("model_name"), "facebook/mms-tts-guj")
        self.assertEqual(res.get("sample_rate"), 16000)
        self.assertGreater(res.get("duration", 0), 0)
        self.assertGreater(res.get("file_size", 0), 0)
        self.assertIn("audio_base64", res)

    def test_synthesize_to_file_wav(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "test_output.wav")
            saved = self.engine.synthesize_to_file("ખ", out_path, format="wav", mock=True)
            self.assertTrue(os.path.exists(saved))
            self.assertGreater(os.path.getsize(saved), 100)

    def test_synthesize_to_file_fallback_mp3(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "test_output.mp3")
            saved = self.engine.synthesize_to_file("ગ", out_path, format="mp3", mock=True)
            self.assertTrue(os.path.exists(saved))
            self.assertGreater(os.path.getsize(saved), 100)


if __name__ == "__main__":
    unittest.main()
