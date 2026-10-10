"""
Unit tests for python/audio_generation/generate_tts_local.py.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from audio_generation.generate_tts_local import (
    BENCHMARK_ITEMS,
    run_benchmark,
    batch_generate_kakko,
    batch_generate_numerals,
)
from tts.mms_tts import MMSTTSEngine


class TestAudioGeneration(unittest.TestCase):
    def setUp(self):
        self.engine = MMSTTSEngine()

    def test_benchmark_items_contain_issue_7_requirements(self):
        chars = [item["char"] for item in BENCHMARK_ITEMS]
        # Consonants
        for c in ["ક", "ખ", "ગ", "ઘ"]:
            self.assertIn(c, chars)
        # Barakhadi
        for b in ["ક", "કા", "કિ", "કી", "કુ", "કે", "કો"]:
            self.assertIn(b, chars)
        # Numerals
        for n in ["૧", "૧૦"]:
            self.assertIn(n, chars)

    def test_run_benchmark_mock(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            results = run_benchmark(self.engine, tmpdir, audio_format="wav", mock=True)
            self.assertEqual(len(results), len(BENCHMARK_ITEMS))
            for res in results:
                self.assertTrue(os.path.exists(os.path.join(tmpdir, res["file"])))
                self.assertGreater(res["file_size"], 0)

    def test_batch_generate_kakko_limit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_generate_kakko(self.engine, tmpdir, audio_format="wav", limit=3, mock=True)
            files = os.listdir(tmpdir)
            self.assertEqual(len(files), 3)

    def test_batch_generate_numerals_limit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_generate_numerals(self.engine, tmpdir, audio_format="wav", limit=3, mock=True)
            files = os.listdir(tmpdir)
            self.assertEqual(len(files), 3)


if __name__ == "__main__":
    unittest.main()
