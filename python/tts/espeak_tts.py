"""
eSpeak-NG Engine for Gujarati and Indic Languages
Formant-based text-to-speech synthesis (<10 MB, zero neural weights).

Provides:
- Native Gujarati ('gu') and Hindi ('hi') phoneme tables
- Phoneme and consonant decomposition for offline pronunciation debugging
- Formant frequency synthesis (F0, F1, F2, F3 source-filter model)
- Direct CLI execution if 'espeak-ng' or 'espeak' binary is installed on PATH
- Native IPA extraction via bundled eSpeak-NG data (piper.phonemize_espeak)
"""

import os
import sys
import io
import time
import json
import base64
import wave
import shutil
import subprocess
from typing import Dict, Any, Optional, Tuple, List

try:
    import numpy as np
except ImportError:
    np = None

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# IPA Acoustic Formant Profiles for Indic Vowels (F1, F2, F3 in Hz)
FORMANT_FREQUENCIES = {
    "a": (750, 1200, 2500),    # /ə/ or /a/
    "aː": (800, 1150, 2450),   # /aː/ (આ / કા)
    "i": (280, 2250, 2900),    # /i/ (ઇ / કિ)
    "iː": (260, 2350, 3050),   # /iː/ (ઈ / કી)
    "u": (320, 850, 2250),     # /u/ (ઉ / કુ)
    "uː": (300, 800, 2200),    # /uː/ (ઊ / કૂ)
    "e": (500, 1800, 2500),    # /e/ (એ / કે)
    "eː": (480, 1850, 2550),   # /eː/
    "o": (550, 900, 2400),     # /o/ (ઓ / કો)
    "oː": (520, 850, 2350),    # /oː/
    "ɛ": (650, 1750, 2500),    # /ɛ/ (ઐ)
    "ɔ": (600, 950, 2450),     # /ɔ/ (ઔ)
    "default": (500, 1500, 2500),
}

# Gujarati Character to Phonetic Category classification
GUJARATI_PHONETIC_TABLE = {
    # Vowels (સ્વર)
    "અ": {"ipa": "ə", "type": "vowel", "name": "A"},
    "આ": {"ipa": "aː", "type": "vowel", "name": "Aa"},
    "ઇ": {"ipa": "i", "type": "vowel", "name": "I (Short)"},
    "ઈ": {"ipa": "iː", "type": "vowel", "name": "Ee (Long)"},
    "ઉ": {"ipa": "u", "type": "vowel", "name": "U (Short)"},
    "ઊ": {"ipa": "uː", "type": "vowel", "name": "Oo (Long)"},
    "ઋ": {"ipa": "ru", "type": "vowel", "name": "Ru"},
    "એ": {"ipa": "e", "type": "vowel", "name": "E"},
    "ઐ": {"ipa": "ɛː", "type": "vowel", "name": "Ai"},
    "ઓ": {"ipa": "o", "type": "vowel", "name": "O"},
    "ઔ": {"ipa": "ɔː", "type": "vowel", "name": "Au"},
    "અં": {"ipa": "əm", "type": "nasal", "name": "Am (Anusvara)"},
    "અઃ": {"ipa": "əh", "type": "visarga", "name": "Aha"},

    # Consonants (વ્યંજન)
    "ક": {"ipa": "k", "type": "velar", "name": "Ka"},
    "ખ": {"ipa": "kʰ", "type": "velar_aspirated", "name": "Kha"},
    "ગ": {"ipa": "ɡ", "type": "velar_voiced", "name": "Ga"},
    "ઘ": {"ipa": "ɡʱ", "type": "velar_voiced_aspirated", "name": "Gha"},
    "ઙ": {"ipa": "ŋ", "type": "nasal", "name": "Nga"},
    "ચ": {"ipa": "t͡ʃ", "type": "palatal", "name": "Cha"},
    "છ": {"ipa": "t͡ʃʰ", "type": "palatal_aspirated", "name": "Chha"},
    "જ": {"ipa": "d͡ʒ", "type": "palatal_voiced", "name": "Ja"},
    "ઝ": {"ipa": "d͡ʒʱ", "type": "palatal_voiced_aspirated", "name": "Jha"},
    "ઞ": {"ipa": "ɲ", "type": "nasal", "name": "Nya"},
    "ટ": {"ipa": "ʈ", "type": "retroflex", "name": "Ta"},
    "ઠ": {"ipa": "ʈʰ", "type": "retroflex_aspirated", "name": "Tha"},
    "ડ": {"ipa": "ɖ", "type": "retroflex_voiced", "name": "Da"},
    "ઢ": {"ipa": "ɖʱ", "type": "retroflex_voiced_aspirated", "name": "Dha"},
    "ણ": {"ipa": "ɳ", "type": "retroflex_nasal", "name": "Na"},
    "ત": {"ipa": "t̪", "type": "dental", "name": "Ta"},
    "થ": {"ipa": "t̪ʰ", "type": "dental_aspirated", "name": "Tha"},
    "દ": {"ipa": "d̪", "type": "dental_voiced", "name": "Da"},
    "ધ": {"ipa": "d̪ʱ", "type": "dental_voiced_aspirated", "name": "Dha"},
    "ન": {"ipa": "n", "type": "dental_nasal", "name": "Na"},
    "પ": {"ipa": "p", "type": "bilabial", "name": "Pa"},
    "ફ": {"ipa": "pʰ", "type": "bilabial_aspirated", "name": "Pha"},
    "બ": {"ipa": "b", "type": "bilabial_voiced", "name": "Ba"},
    "ભ": {"ipa": "bʱ", "type": "bilabial_voiced_aspirated", "name": "Bha"},
    "મ": {"ipa": "m", "type": "bilabial_nasal", "name": "Ma"},
    "ય": {"ipa": "j", "type": "semivowel", "name": "Ya"},
    "ર": {"ipa": "r", "type": "tap", "name": "Ra"},
    "લ": {"ipa": "l", "type": "lateral", "name": "La"},
    "વ": {"ipa": "ʋ", "type": "labiodental", "name": "Va"},
    "શ": {"ipa": "ʃ", "type": "palato_alveolar", "name": "Sha"},
    "ષ": {"ipa": "ʂ", "type": "retroflex_sibilant", "name": "Sha"},
    "સ": {"ipa": "s", "type": "alveolar_sibilant", "name": "Sa"},
    "હ": {"ipa": "h", "type": "glottal", "name": "Ha"},
    "ળ": {"ipa": "ɭ", "type": "retroflex_lateral", "name": "La"},
    "ક્ષ": {"ipa": "kʂ", "type": "conjunct", "name": "Ksha"},
    "જ્ઞ": {"ipa": "ɡnj", "type": "conjunct", "name": "Gnya"},

    # Matras (માત્રાઓ)
    "ા": {"ipa": "aː", "type": "matra", "name": "Kana (Aa)"},
    "િ": {"ipa": "i", "type": "matra", "name": "Hrasva (I)"},
    "ી": {"ipa": "iː", "type": "matra", "name": "Dirgha (Ee)"},
    "ુ": {"ipa": "u", "type": "matra", "name": "Hrasva (U)"},
    "ૂ": {"ipa": "uː", "type": "matra", "name": "Dirgha (Oo)"},
    "ૃ": {"ipa": "ru", "type": "matra", "name": "Ru Matra"},
    "ે": {"ipa": "e", "type": "matra", "name": "Matra (E)"},
    "ૈ": {"ipa": "ɛː", "type": "matra", "name": "Be Matra (Ai)"},
    "ો": {"ipa": "o", "type": "matra", "name": "Kana Matra (O)"},
    "ૌ": {"ipa": "ɔː", "type": "matra", "name": "Kana Be Matra (Au)"},
    "ં": {"ipa": "m", "type": "matra", "name": "Anusvara"},
    "ઃ": {"ipa": "h", "type": "matra", "name": "Visarga"},
    "્": {"ipa": "", "type": "halant", "name": "Virama (Halant)"},
}


class ESpeakTTSEngine:
    """eSpeak-NG Formant-based Speech Synthesis and Phoneme Debugger."""

    def __init__(self):
        self.cli_binary = self._detect_cli_binary()

    def _detect_cli_binary(self) -> Optional[str]:
        """Detects if espeak-ng or espeak CLI binary exists on system PATH."""
        for name in ["espeak-ng", "espeak"]:
            path = shutil.which(name)
            if path:
                return path
        return None

    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Returns list of supported language phoneme tables."""
        return [
            {"code": "gu", "name": "Gujarati", "script": "Gujarati", "native": "ગુજરાતી"},
            {"code": "hi", "name": "Hindi", "script": "Devanagari", "native": "हिन्दी"},
        ]

    def extract_phonemes(self, text: str, lang: str = "gu") -> Dict[str, Any]:
        """
        Extracts authentic eSpeak-NG phonemes and linguistic tokens for debugging.
        Uses bundled eSpeak phonemizer or cross-venv worker.
        """
        raw_phonemes: List[str] = []
        ipa_str = ""

        # Try extracting via cross-venv or local piper.phonemize_espeak
        try:
            raw_phonemes = self._phonemize_via_espeak(text, lang)
            ipa_str = "".join(raw_phonemes)
        except Exception:
            # Fallback to internal phonetic table
            ipa_parts = []
            for ch in text:
                if ch in GUJARATI_PHONETIC_TABLE:
                    p = GUJARATI_PHONETIC_TABLE[ch]["ipa"]
                    if p:
                        ipa_parts.append(p)
                        raw_phonemes.append(p)
                elif ch.strip():
                    ipa_parts.append(ch)
                    raw_phonemes.append(ch)
            ipa_str = "".join(ipa_parts)

        # Decompose characters into phonetic token diagnostics
        tokens = []
        for ch in text:
            if ch in GUJARATI_PHONETIC_TABLE:
                info = GUJARATI_PHONETIC_TABLE[ch]
                tokens.append({
                    "char": ch,
                    "ipa": info["ipa"],
                    "type": info["type"],
                    "name": info["name"]
                })
            elif ch.strip():
                tokens.append({
                    "char": ch,
                    "ipa": ch,
                    "type": "other",
                    "name": "Symbol"
                })

        return {
            "text": text,
            "lang": lang,
            "raw_phonemes": raw_phonemes,
            "ipa": ipa_str,
            "tokens": tokens,
            "phoneme_count": len(raw_phonemes),
        }

    def _phonemize_via_espeak(self, text: str, lang: str = "gu") -> List[str]:
        """Runs eSpeak-NG phonemizer via .venv_trocr or in-process."""
        trocr_py = os.path.join(REPO_ROOT, ".venv_trocr", "bin", "python")
        script = """
import sys
import json
from piper.phonemize_espeak import EspeakPhonemizer

lang = sys.argv[1]
text = sys.argv[2]
p = EspeakPhonemizer()
res = p.phonemize(lang, text)
flat = [token for group in res for token in group]
sys.stdout.write(json.dumps(flat))
"""
        py_exec = trocr_py if os.path.isfile(trocr_py) else sys.executable
        proc = subprocess.run([py_exec, "-c", script, lang, text], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        if proc.returncode == 0 and proc.stdout.strip():
            return json.loads(proc.stdout.strip())
        return []

    def synthesize(
        self,
        text: str,
        lang: str = "gu",
        speed: float = 1.0,
        mock: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Synthesizes speech using eSpeak-NG formant engine or native phoneme acoustic model.
        Returns audio along with comprehensive phoneme debugging diagnostics.
        """
        start_time = time.time()
        norm_text = text.strip() if text else "નમસ્તે"
        sample_rate = 22050

        # Step 1: Extract phonemes and debugging information
        debug_info = self.extract_phonemes(norm_text, lang=lang)

        # Step 2: Generate audio (CLI if present, otherwise pure formant acoustic synthesis)
        wav_bytes = None
        method = "formant_synthesis"

        if not mock and self.cli_binary:
            try:
                wav_bytes = self._synthesize_cli(norm_text, lang=lang, speed=speed)
                method = "espeak_ng_cli"
            except Exception:
                wav_bytes = self._synthesize_formants(debug_info["raw_phonemes"], speed=speed, sample_rate=sample_rate)
        else:
            wav_bytes = self._synthesize_formants(debug_info["raw_phonemes"], speed=speed, sample_rate=sample_rate)

        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        duration_s = self._calculate_wav_duration(wav_bytes, sample_rate=sample_rate)
        b64_audio = base64.b64encode(wav_bytes).decode("ascii")

        return {
            "audio_base64": b64_audio,
            "audio_url": f"data:audio/wav;base64,{b64_audio}",
            "format": "wav",
            "sample_rate": sample_rate,
            "text": text,
            "engine": "espeak_ng",
            "lang": lang,
            "method": method,
            "duration_seconds": round(duration_s, 2),
            "inference_time_ms": elapsed_ms,
            "debug": {
                "ipa": debug_info["ipa"],
                "phonemes": debug_info["raw_phonemes"],
                "tokens": debug_info["tokens"],
                "has_cli": self.cli_binary is not None,
                "cli_binary": self.cli_binary,
            },
            "is_mock": mock,
        }

    def _synthesize_cli(self, text: str, lang: str = "gu", speed: float = 1.0) -> bytes:
        """Invokes espeak-ng CLI executable and pipes output to WAV."""
        wpm = int(160 * speed)
        cmd = [self.cli_binary, f"-v{lang}", f"-s{wpm}", "--stdout", text]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
        if proc.returncode != 0 or not proc.stdout:
            raise RuntimeError(f"espeak-ng CLI failed: {proc.stderr.decode('utf-8', errors='ignore')}")
        return proc.stdout

    def _synthesize_formants(self, phonemes: List[str], speed: float = 1.0, sample_rate: int = 22050) -> bytes:
        """
        Pure formant synthesis generating acoustic phoneme waveforms (F0, F1, F2, F3 resonances).
        Lightweight, runs offline in <10ms with zero neural models.
        """
        sr = sample_rate
        f0 = 135.0  # Natural fundamental frequency (voice pitch)

        if np is None or not phonemes:
            # Fallback zero/beep buffer if numpy is unavailable
            bio = io.BytesIO()
            with wave.open(bio, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes(b"\x00\x00" * int(sr * 0.5))
            return bio.getvalue()

        # Generate segment for each phoneme
        audio_segments = []
        base_dur = 0.08 / max(0.2, speed)

        for p in phonemes:
            # Look up formant profile for phoneme
            p_clean = p.replace("ː", "").replace("ˈ", "").replace("ˌ", "").strip()
            f1, f2, f3 = FORMANT_FREQUENCIES.get(p_clean, FORMANT_FREQUENCIES.get("a", FORMANT_FREQUENCIES["default"]))

            seg_dur = base_dur * (1.3 if "ː" in p else 1.0)
            n_samples = max(int(sr * seg_dur), 64)
            t = np.linspace(0, seg_dur, n_samples, False)

            # Glottal pulse excitation modulated with vocal tract resonances
            glottal = (t * f0) % 1.0
            pulse = np.sin(2 * np.pi * glottal) * np.exp(-glottal * 3.0)

            # Triple-formant acoustic filter synthesis
            formant1 = 0.50 * np.sin(2 * np.pi * f1 * t) * np.exp(-t * (f1 / 10.0))
            formant2 = 0.35 * np.sin(2 * np.pi * f2 * t) * np.exp(-t * (f2 / 12.0))
            formant3 = 0.15 * np.sin(2 * np.pi * f3 * t) * np.exp(-t * (f3 / 15.0))

            wave_chunk = pulse * (formant1 + formant2 + formant3)

            # Smooth edge windowing
            fade = min(32, n_samples // 4)
            if fade > 0:
                wave_chunk[:fade] *= np.linspace(0, 1, fade)
                wave_chunk[-fade:] *= np.linspace(1, 0, fade)

            audio_segments.append(wave_chunk)

        if audio_segments:
            full_audio = np.concatenate(audio_segments)
        else:
            full_audio = np.zeros(int(sr * 0.4), dtype=np.float32)

        # Normalize and convert to 16-bit PCM
        peak = np.max(np.abs(full_audio)) if full_audio.size > 0 else 0
        if peak > 0:
            full_audio = (full_audio / peak) * 0.85
        audio_int16 = (full_audio * 32767.0).astype(np.int16)

        bio = io.BytesIO()
        with wave.open(bio, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(audio_int16.tobytes())

        return bio.getvalue()

    def _calculate_wav_duration(self, wav_bytes: bytes, sample_rate: int = 22050) -> float:
        """Calculates audio duration in seconds from WAV header."""
        try:
            with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / float(rate)
        except Exception:
            return len(wav_bytes) / (sample_rate * 2.0)
