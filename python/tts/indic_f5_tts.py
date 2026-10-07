"""
AI4Bharat IndicF5 Gujarati Text-to-Speech Engine
Reference-conditioned Flow-Matching Speech Synthesis
https://github.com/AI4Bharat/IndicF5
https://huggingface.co/ai4bharat/IndicF5
"""

import os
import io
import time
import base64
from typing import Optional, Dict, Any

import requests

try:
    import soundfile as sf
except ImportError:
    sf = None

try:
    from gradio_client import Client, handle_file
except ImportError:
    Client = None
    handle_file = None


class IndicF5Engine:
    def __init__(
        self,
        space_id: str = "ai4bharat/IndicF5",
        default_ref_path: Optional[str] = None,
        hf_token: Optional[str] = None,
    ):
        self.space_id = space_id
        self.hf_token = hf_token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        self._client = None
        
        # Locate project root and default reference audio
        current_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
        
        if default_ref_path and os.path.exists(default_ref_path):
            self.default_ref_path = default_ref_path
        else:
            # Look for existing Gujarati audio in repo assets
            candidate = os.path.join(repo_root, "docs", "assets", "audio", "kakko", "1_ka.mp3")
            if os.path.exists(candidate):
                self.default_ref_path = candidate
            else:
                self.default_ref_path = None

        self.default_ref_text = "ક"

    def _get_client(self, endpoint: Optional[str] = None, token: Optional[str] = None):
        target = (endpoint or self.space_id).strip()
        is_local = (
            target.startswith("http://")
            or target.startswith("https://127.0.0.1")
            or "localhost" in target
            or "127.0.0.1" in target
        )

        if self._client is not None and getattr(self, "_current_target", None) == target:
            if is_local or getattr(self, "_current_token", None) == token:
                return self._client

        if Client is None:
            raise RuntimeError("gradio_client is not installed. Run `pip install gradio_client`.")

        kwargs = {}
        if not is_local:
            use_token = token or self.hf_token
            if use_token and use_token.strip():
                kwargs["token"] = use_token.strip()

        self._client = Client(target, **kwargs)
        self._current_target = target
        self._current_token = token
        return self._client

    def synthesize(
        self,
        text: str,
        ref_audio_path: Optional[str] = None,
        ref_text: Optional[str] = None,
        hf_token: Optional[str] = None,
        api_url: Optional[str] = None,
        speed: float = 0.75,
    ) -> Dict[str, Any]:
        """
        Synthesize Gujarati speech using AI4Bharat IndicF5.
        
        Args:
            text: Gujarati text string to synthesize.
            ref_audio_path: Path to reference audio clip (WAV/MP3) for voice conditioning.
            ref_text: Transcript of the reference audio clip.
            hf_token: Optional Hugging Face token for higher ZeroGPU limits.
            api_url: Optional custom API endpoint (e.g. http://localhost:7860 or space name).
            speed: Speech rate multiplier (e.g. 0.75 for clear calm diction).
            
        Returns:
            Dict containing audio_bytes, base64, sample_rate, duration, format.
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty.")

        audio_file = ref_audio_path or self.default_ref_path
        transcript = ref_text or self.default_ref_text

        if not audio_file or not os.path.exists(audio_file):
            raise FileNotFoundError(f"Reference audio file not found: {audio_file}")

        target_endpoint = (api_url or self.space_id).strip()
        start_time = time.time()

        # Direct REST check for local standalone IndicF5 server (run_local_indic_f5.py)
        is_http = target_endpoint.startswith("http://") or target_endpoint.startswith("https://")
        if is_http:
            try:
                ep = f"{target_endpoint.rstrip('/')}/synthesize_speech"
                payload = {
                    "text": text.strip(),
                    "ref_audio": audio_file,
                    "ref_text": transcript.strip(),
                    "speed": speed,
                }
                resp = requests.post(ep, json=payload, timeout=90)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_bytes = None
                    if "audio_base64" in data and data["audio_base64"]:
                        raw_bytes = base64.b64decode(data["audio_base64"])
                    elif "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                        first_item = data["data"][0]
                        if isinstance(first_item, dict) and "path" in first_item and os.path.exists(first_item["path"]):
                            with open(first_item["path"], "rb") as f:
                                raw_bytes = f.read()
                        elif isinstance(first_item, str) and os.path.exists(first_item):
                            with open(first_item, "rb") as f:
                                raw_bytes = f.read()

                    if raw_bytes:
                        audio_b64 = base64.b64encode(raw_bytes).decode("utf-8")
                        sr = data.get("sample_rate", 24000)
                        dur = data.get("duration", round(len(raw_bytes) / (sr * 2), 2))
                        return {
                            "engine": "indic_f5",
                            "model_name": data.get("model_name", "AI4Bharat IndicF5 (Local Server)"),
                            "text": text,
                            "sample_rate": sr,
                            "duration": dur,
                            "elapsed_seconds": round(time.time() - start_time, 2),
                            "format": "wav",
                            "mime_type": "audio/wav",
                            "audio_base64": audio_b64,
                            "file_size": len(raw_bytes),
                        }
            except Exception:
                # Fall back to Gradio Client below
                pass

        client = self._get_client(endpoint=target_endpoint, token=hf_token)

        # Call IndicF5 synthesis endpoint
        try:
            result_path = client.predict(
                text=text.strip(),
                ref_audio=handle_file(audio_file),
                ref_text=transcript.strip(),
                api_name="/synthesize_speech",
            )
        except Exception as e:
            err_str = str(e)
            if "ZeroGPU" in err_str or "quota" in err_str.lower():
                raise RuntimeError(
                    "IndicF5 ZeroGPU limit reached on Hugging Face Spaces. "
                    "Options to run without limit:\n"
                    "1. Switch IndicF5 API to 'Local Server (http://localhost:7860)' and run `python python/tts/run_local_indic_f5.py`\n"
                    "2. Enter your personal Hugging Face Token (from https://huggingface.co/settings/tokens) in the IndicF5 settings panel."
                ) from e
            raise

        elapsed = time.time() - start_time

        if not os.path.exists(result_path):
            raise RuntimeError(f"IndicF5 generation failed. Output not found: {result_path}")

        with open(result_path, "rb") as f:
            audio_bytes = f.read()

        sample_rate = 24000
        duration = 0.0

        if sf is not None:
            try:
                data, sr = sf.read(io.BytesIO(audio_bytes))
                sample_rate = sr
                duration = round(len(data) / sr, 3)
            except Exception:
                pass

        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        return {
            "engine": "indic_f5",
            "model_name": "ai4bharat/IndicF5",
            "text": text,
            "sample_rate": sample_rate,
            "duration": duration,
            "elapsed_seconds": round(elapsed, 2),
            "format": "wav",
            "mime_type": "audio/wav",
            "audio_base64": audio_b64,
            "file_size": len(audio_bytes),
        }
