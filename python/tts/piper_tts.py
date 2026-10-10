"""
Piper TTS Engine for Gujarati and Indic Languages (piper-tts)
Ultra-fast, lightweight neural text-to-speech running locally on ONNX Runtime.

Supports:
- Sub-100ms inference on CPU
- Native Hindi voices: Rohan, Pratham, Priyamvada (rhasspy/piper-voices)
- Community Gujarati model: Arjun4707/piper-gujarati-male
- In-process execution (Python <=3.11 with piper-tts installed)
- Seamless cross-venv worker fallback (executing via .venv_trocr)
- Gujarati numeral verbalization (૧ -> એક, ૧૦ -> દસ)
"""

import os
import sys
import io
import time
import json
import base64
import wave
import subprocess
import urllib.request
from typing import Dict, Any, Optional, Tuple, List

try:
    import numpy as np
except ImportError:
    np = None

# Check for Piper in active runtime
HAS_PIPER = False
try:
    from piper.voice import PiperVoice
    HAS_PIPER = True
except ImportError:
    HAS_PIPER = False

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODELS_DIR = os.path.join(REPO_ROOT, "resources", "models", "piper")

# Available Piper Voices
PIPER_VOICES = {
    "rohan": {
        "id": "rohan",
        "name": "Rohan (Hindi / Indic)",
        "language": "hi",
        "gender": "male",
        "sample_rate": 22050,
        "onnx_name": "hi_IN-rohan-medium.onnx",
        "repo": "rhasspy/piper-voices",
        "remote_path": "hi/hi_IN/rohan/medium/hi_IN-rohan-medium",
        "description": "Ultra-fast neural Indic male voice running on ONNX Runtime.",
    },
    "pratham": {
        "id": "pratham",
        "name": "Pratham (Hindi / Indic)",
        "language": "hi",
        "gender": "male",
        "sample_rate": 22050,
        "onnx_name": "hi_IN-pratham-medium.onnx",
        "repo": "rhasspy/piper-voices",
        "remote_path": "hi/hi_IN/pratham/medium/hi_IN-pratham-medium",
        "description": "Natural neural Indic male voice for conversational speech.",
    },
    "priyamvada": {
        "id": "priyamvada",
        "name": "Priyamvada (Hindi / Indic)",
        "language": "hi",
        "gender": "female",
        "sample_rate": 22050,
        "onnx_name": "hi_IN-priyamvada-medium.onnx",
        "repo": "rhasspy/piper-voices",
        "remote_path": "hi/hi_IN/priyamvada/medium/hi_IN-priyamvada-medium",
        "description": "Clear neural Indic female voice running on ONNX Runtime.",
    },
    "gujarati_male": {
        "id": "gujarati_male",
        "name": "Gujarati Male (Arjun4707)",
        "language": "gu",
        "gender": "male",
        "sample_rate": 22050,
        "onnx_name": "gu_epoch229.onnx",
        "repo": "Arjun4707/piper-gujarati-male",
        "remote_path": "gu_epoch229",
        "description": "Community Gujarati model trained on AI4Bharat dataset.",
    },
}

# Gujarati Numerals mapping
GUJARATI_DIGITS = {
    "૦": "શૂન્ય", "૧": "એક", "૨": "બે", "૩": "ત્રણ", "૪": "ચાર",
    "૫": "પાંચ", "૬": "છ", "૭": "સાત", "૮": "આઠ", "૯": "નવ",
    "0": "શૂન્ય", "1": "એક", "2": "બે", "3": "ત્રણ", "4": "ચાર",
    "5": "પાંચ", "6": "છ", "7": "સાત", "8": "આઠ", "9": "નવ",
}

GUJARATI_NUMBERS_SPECIAL = {
    "૧૦": "દસ", "૧૧": "અગિયાર", "૧૨": "બાર", "૧૩": "તેર", "૧૪": "ચૌદ",
    "૧૫": "પંદર", "૧૬": "સોળ", "૧૭": "સત્તર", "૧૮": "અઢાર", "૧૯": "ઓગણીસ",
    "૨૦": "વીસ", "૨૧": "એકવીસ", "૨૨": "બાવીસ", "૨૩": "ત્રેવીસ", "૨૪": "ચોવીસ",
    "૨૫": "પચ્ચીસ", "૨૬": "છવ્વીસ", "૨૭": "સત્તાવીસ", "૨૮": "અઠ્ઠાવીસ", "૨૯": "ઓગણત્રીસ",
    "૩૦": "ત્રીસ", "૪૦": "ચાલીસ", "૫૦": "પચાસ", "૬૦": "સાઈઠ", "૭૦": "સિત્તેર",
    "૮૦": "એંસી", "૯૦": "નેવું", "૧૦૦": "સો",
    "10": "દસ", "11": "અગિયાર", "12": "બાર", "13": "તેર", "14": "ચૌદ",
    "15": "પંદર", "16": "સોળ", "17": "સત્તર", "18": "અઢાર", "19": "ઓગણીસ",
    "20": "વીસ", "30": "ત્રીસ", "40": "ચાલીસ", "50": "પચાસ", "60": "સાઈઠ",
    "70": "સિત્તેર", "80": "એંસી", "90": "નેવું", "100": "સો"
}


def normalize_gujarati_for_piper(text: str) -> str:
    """Verbalize numerals and clean text for Piper ONNX synthesis."""
    if not text:
        return ""
    text = text.strip()
    if text in GUJARATI_NUMBERS_SPECIAL:
        return GUJARATI_NUMBERS_SPECIAL[text]

    words = []
    for chunk in text.split():
        if chunk in GUJARATI_NUMBERS_SPECIAL:
            words.append(GUJARATI_NUMBERS_SPECIAL[chunk])
        else:
            chars = []
            for ch in chunk:
                if ch in GUJARATI_DIGITS:
                    chars.append(GUJARATI_DIGITS[ch])
                else:
                    chars.append(ch)
            words.append("".join(chars))
    return " ".join(words)


class PiperTTSEngine:
    """Piper ONNX Neural Text-to-Speech Engine."""

    VOICES = PIPER_VOICES

    def __init__(self, models_dir: Optional[str] = None):
        self.models_dir = models_dir or MODELS_DIR
        os.makedirs(self.models_dir, exist_ok=True)
        self._loaded_voices: Dict[str, Any] = {}

    def get_voice_info(self, voice_id: str) -> Dict[str, Any]:
        """Returns metadata for the requested voice."""
        norm_id = voice_id.lower().replace("-", "_")
        return self.VOICES.get(norm_id, self.VOICES["rohan"])

    def resolve_model_files(self, voice_id: str, hf_token: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Locates or downloads .onnx and .onnx.json files for the voice.
        Returns (onnx_path, config_path) or (None, None) if unavailable.
        """
        info = self.get_voice_info(voice_id)
        onnx_name = info["onnx_name"]
        json_name = f"{onnx_name}.json"

        local_onnx = os.path.join(self.models_dir, onnx_name)
        local_json = os.path.join(self.models_dir, json_name)

        if os.path.isfile(local_onnx) and os.path.isfile(local_json):
            return local_onnx, local_json

        # Attempt downloading if not present locally
        repo = info["repo"]
        remote_path = info["remote_path"]

        token = hf_token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        headers = {"User-Agent": "Mozilla/5.0 (KanoAI PiperTTS Client)"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        base_url = f"https://huggingface.co/{repo}/resolve/main"
        if repo == "rhasspy/piper-voices":
            json_url = f"{base_url}/{remote_path}.onnx.json"
            onnx_url = f"{base_url}/{remote_path}.onnx"
        else:
            json_url = f"{base_url}/{remote_path}.onnx.json"
            onnx_url = f"{base_url}/{remote_path}.onnx"

        try:
            # Download JSON config
            req = urllib.request.Request(json_url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                with open(local_json, "wb") as f:
                    f.write(resp.read())

            # Download ONNX weights
            req = urllib.request.Request(onnx_url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                with open(local_onnx, "wb") as f:
                    f.write(resp.read())

            if os.path.isfile(local_onnx) and os.path.isfile(local_json):
                return local_onnx, local_json
        except Exception as e:
            # Clean up partial downloads on error
            for path in [local_onnx, local_json]:
                if os.path.isfile(path) and os.path.getsize(path) == 0:
                    try:
                        os.remove(path)
                    except OSError:
                        pass
            return None, None

        return None, None

    def synthesize(
        self,
        text: str,
        voice_id: str = "rohan",
        speed: float = 1.0,
        mock: bool = False,
        hf_token: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Synthesizes speech from Gujarati/Indic text using Piper TTS.
        """
        start_time = time.time()
        norm_text = normalize_gujarati_for_piper(text)
        if not norm_text:
            norm_text = "નમસ્તે"

        info = self.get_voice_info(voice_id)
        selected_voice = info["id"]
        sample_rate = info["sample_rate"]

        if mock:
            wav_bytes = self._generate_mock_wav(norm_text, sample_rate=sample_rate)
            duration_s = max(0.4, len(norm_text) * 0.12)
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "audio_base64": base64.b64encode(wav_bytes).decode("ascii"),
                "audio_url": f"data:audio/wav;base64,{base64.b64encode(wav_bytes).decode('ascii')}",
                "format": "wav",
                "sample_rate": sample_rate,
                "text": text,
                "engine": "piper_tts",
                "voice_id": selected_voice,
                "voice_name": info["name"],
                "duration_seconds": round(duration_s, 2),
                "inference_time_ms": elapsed_ms,
                "is_mock": True,
            }

        # Resolve model weights
        onnx_path, config_path = self.resolve_model_files(selected_voice, hf_token=hf_token)

        # Fallback to Rohan (default bundled/public voice) if selected voice is unavailable
        if not onnx_path or not config_path:
            onnx_path, config_path = self.resolve_model_files("rohan", hf_token=hf_token)
            if onnx_path:
                selected_voice = "rohan"
                info = self.get_voice_info("rohan")
                sample_rate = info["sample_rate"]

        wav_bytes = None
        is_mock = False

        if onnx_path and config_path:
            try:
                if HAS_PIPER:
                    wav_bytes = self._synthesize_in_process(norm_text, onnx_path, config_path, speed=speed)
                else:
                    wav_bytes = self._synthesize_cross_venv(norm_text, onnx_path, config_path, speed=speed)
            except Exception as e:
                # If ONNX fails at runtime, fallback to synthetic audio
                wav_bytes = self._generate_mock_wav(norm_text, sample_rate=sample_rate)
                is_mock = True
        else:
            wav_bytes = self._generate_mock_wav(norm_text, sample_rate=sample_rate)
            is_mock = True

        duration_s = self._calculate_wav_duration(wav_bytes, sample_rate=sample_rate)
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        b64_audio = base64.b64encode(wav_bytes).decode("ascii")

        return {
            "audio_base64": b64_audio,
            "audio_url": f"data:audio/wav;base64,{b64_audio}",
            "format": "wav",
            "sample_rate": sample_rate,
            "text": text,
            "engine": "piper_tts",
            "voice_id": selected_voice,
            "voice_name": info["name"],
            "duration_seconds": round(duration_s, 2),
            "inference_time_ms": elapsed_ms,
            "is_mock": is_mock,
        }

    def _synthesize_in_process(self, text: str, onnx_path: str, config_path: str, speed: float = 1.0) -> bytes:
        """In-process Piper synthesis via PiperVoice."""
        if onnx_path not in self._loaded_voices:
            self._loaded_voices[onnx_path] = PiperVoice.load(onnx_path, config_path=config_path)

        voice = self._loaded_voices[onnx_path]
        bio = io.BytesIO()
        with wave.open(bio, "wb") as wf:
            voice.synthesize_wav(text, wf)
        return bio.getvalue()

    def _synthesize_cross_venv(self, text: str, onnx_path: str, config_path: str, speed: float = 1.0) -> bytes:
        """Invokes .venv_trocr python runner where piper-tts is installed."""
        trocr_py = os.path.join(REPO_ROOT, ".venv_trocr", "bin", "python")
        if not os.path.isfile(trocr_py):
            raise FileNotFoundError(f"Cross-venv Python executable not found at {trocr_py}")

        script = """
import sys
import io
import wave
import base64
from piper.voice import PiperVoice

onnx_path = sys.argv[1]
config_path = sys.argv[2]
text = sys.argv[3]

voice = PiperVoice.load(onnx_path, config_path=config_path)
bio = io.BytesIO()
with wave.open(bio, "wb") as wf:
    voice.synthesize_wav(text, wf)

sys.stdout.write(base64.b64encode(bio.getvalue()).decode("ascii"))
"""
        cmd = [trocr_py, "-c", script, onnx_path, config_path, text]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
        if proc.returncode != 0:
            raise RuntimeError(f"Subprocess Piper-TTS synthesis failed: {proc.stderr}")

        return base64.b64decode(proc.stdout.strip())

    def _calculate_wav_duration(self, wav_bytes: bytes, sample_rate: int = 22050) -> float:
        """Calculates audio duration in seconds from WAV header."""
        try:
            with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / float(rate)
        except Exception:
            return len(wav_bytes) / (sample_rate * 2.0)

    def _generate_mock_wav(self, text: str, sample_rate: int = 22050) -> bytes:
        """Generates synthetic audio for unit testing or fallback."""
        sr = sample_rate
        duration = min(4.0, max(0.4, len(text) * 0.12))
        if np is not None:
            t = np.linspace(0, duration, int(sr * duration), False)
            # Pleasant melodic harmonic tone
            tone = 0.3 * np.sin(2 * np.pi * 329.63 * t) + 0.15 * np.sin(2 * np.pi * 659.25 * t)
            fade_len = int(sr * 0.04)
            if len(tone) > fade_len * 2:
                fade_in = np.linspace(0, 1, fade_len)
                fade_out = np.linspace(1, 0, fade_len)
                tone[:fade_len] *= fade_in
                tone[-fade_len:] *= fade_out

            audio_int16 = (tone * 32767.0).astype(np.int16)
            bio = io.BytesIO()
            with wave.open(bio, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes(audio_int16.tobytes())
            return bio.getvalue()
        else:
            bio = io.BytesIO()
            with wave.open(bio, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes(b"\x00\x00" * int(sr * duration))
            return bio.getvalue()
