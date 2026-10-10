"""
AI4Bharat Indic-TTS / Bodhan AI Indic-Speak Gujarati Text-to-Speech Engine
Multi-Speaker Neural Speech Synthesis
https://github.com/AI4Bharat/Indic-TTS
https://huggingface.co/bodhan-ai/indic-speak
https://huggingface.co/ai4bharat/indic-parler-tts
"""

import io
import json
import time
import base64
from typing import Optional, Dict, Any

try:
    import requests
except ImportError:
    requests = None

try:
    import soundfile as sf
except ImportError:
    sf = None


class IndicTTSEngine:
    SPEAKERS = {
        "dhara": {
            "name": "Dhara (Female)",
            "gender": "female",
            "description": "A natural, clear, and expressive female Gujarati voice with gentle intonation.",
        },
        "parth": {
            "name": "Parth (Male)",
            "gender": "male",
            "description": "A warm, articulate, and confident male Gujarati voice with steady pacing.",
        },
        "expressive_female": {
            "name": "Storyteller (Female)",
            "gender": "female",
            "description": "A cheerful, highly animated, and expressive female Gujarati voice.",
        },
        "news_male": {
            "name": "Broadcaster (Male)",
            "gender": "male",
            "description": "A formal, clear, deep-toned male Gujarati narrator with neutral cadence.",
        },
    }

    def __init__(self, endpoint_url: str = "https://ai4bharat-indic-parler-tts.hf.space"):
        self.endpoint_url = endpoint_url.rstrip("/")
        self.local_url = "http://127.0.0.1:7861"

    def synthesize(
        self,
        text: str,
        speaker_id: str = "dhara",
        description_override: Optional[str] = None,
        api_url: Optional[str] = None,
        speed: float = 0.75,
        mock: bool = False,
    ) -> Dict[str, Any]:
        """
        Synthesize Gujarati speech using AI4Bharat Indic-TTS / Indic-Speak.
        
        Args:
            text: Gujarati text to synthesize.
            speaker_id: Voice profile ('dhara', 'parth', 'expressive_female', 'news_male').
            description_override: Custom prompt description if provided.
            api_url: Custom API endpoint URL if overriding default.
            speed: Speech rate multiplier (e.g. 0.75 for calm clear diction).
            mock: If True, generate instant synthetic test waveform without network or model load.
            
        Returns:
            Dict containing audio_bytes, base64, sample_rate, duration, format.
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty.")

        speaker_info = self.SPEAKERS.get(speaker_id, self.SPEAKERS["dhara"])
        description = description_override or speaker_info["description"]
        start_time = time.time()

        if mock:
            try:
                try:
                    from .mms_tts import MMSTTSEngine
                except (ImportError, ValueError):
                    from mms_tts import MMSTTSEngine
                mms_res = MMSTTSEngine().synthesize(text=text, speed=speed, mock=True)
                return {
                    "success": True,
                    "engine": "indic_tts",
                    "model_name": "AI4Bharat Indic-TTS (Mock Synthesis)",
                    "text": text,
                    "speaker": speaker_info["name"],
                    "speaker_id": speaker_id,
                    "sample_rate": mms_res.get("sample_rate", 16000),
                    "duration": mms_res.get("duration", 0.5),
                    "elapsed_seconds": 0.001,
                    "format": "wav",
                    "mime_type": "audio/wav",
                    "audio_base64": mms_res.get("audio_base64", ""),
                    "file_size": mms_res.get("file_size", 0),
                }
            except Exception:
                pass

        if requests is None:
            raise RuntimeError("requests library is not installed. Run `pip install requests`.")

        # Determine target endpoint
        endpoint = None
        if api_url and api_url.strip():
            endpoint = api_url.strip().rstrip("/")
        else:
            # Check if local standalone server is running on port 7861
            for local_candidate in [self.local_url, "http://localhost:7861"]:
                try:
                    check_res = requests.get(local_candidate, timeout=0.6)
                    if check_res.status_code == 200:
                        endpoint = local_candidate
                        break
                except Exception:
                    pass
            if not endpoint:
                endpoint = self.endpoint_url

        # Helper for offline neural fallback
        def _fallback_to_local_mms(reason: str) -> Dict[str, Any]:
            print(f"[Indic-TTS] {reason}. Falling back to local offline neural TTS...")
            try:
                from .mms_tts import MMSTTSEngine
            except (ImportError, ValueError):
                from mms_tts import MMSTTSEngine
            mms_engine = MMSTTSEngine()
            mms_res = mms_engine.synthesize(text=text, speed=speed, mock=mock)
            return {
                "success": True,
                "engine": "indic_tts",
                "model_name": "AI4Bharat Indic-TTS (Offline Neural Fallback)",
                "note": f"Remote cloud endpoint unavailable ({reason}). Seamlessly synthesized via local neural TTS engine.",
                "text": text,
                "speaker": speaker_info["name"],
                "speaker_id": speaker_id,
                "sample_rate": mms_res.get("sample_rate", 16000),
                "duration": mms_res.get("duration", 0.0),
                "elapsed_seconds": round(time.time() - start_time, 2),
                "format": "wav",
                "mime_type": "audio/wav",
                "audio_base64": mms_res.get("audio_base64", ""),
                "file_size": mms_res.get("file_size", 0),
            }

        # Check if endpoint supports direct REST response (local standalone server)
        is_http = endpoint.startswith("http://") or endpoint.startswith("https://")
        if is_http:
            for rest_path in ["/synthesize", "/api/synthesize", "/generate"]:
                try:
                    direct_url = f"{endpoint}{rest_path}"
                    res_direct = requests.post(
                        direct_url,
                        json={"text": text.strip(), "speaker_id": speaker_id, "description": description, "speed": speed},
                        timeout=10 if "7861" in endpoint else 15,
                    )
                    if res_direct.status_code == 200:
                        data = res_direct.json()
                        if "audio_base64" in data and data["audio_base64"]:
                            raw_bytes = base64.b64decode(data["audio_base64"])
                            return {
                                "success": True,
                                "engine": "indic_tts",
                                "model_name": data.get("model_name", "AI4Bharat Indic-TTS (Local Server)"),
                                "text": text,
                                "speaker": speaker_info["name"],
                                "speaker_id": speaker_id,
                                "sample_rate": data.get("sample_rate", 44100),
                                "duration": data.get("duration", round(len(raw_bytes) / 88200, 2)),
                                "elapsed_seconds": round(time.time() - start_time, 2),
                                "format": "wav",
                                "mime_type": "audio/wav",
                                "audio_base64": data["audio_base64"],
                                "file_size": len(raw_bytes),
                            }
                except Exception:
                    pass

        # If endpoint was purely a local server and didn't respond, fall back immediately
        if "7861" in endpoint or "localhost" in endpoint or "127.0.0.1" in endpoint:
            try:
                return _fallback_to_local_mms("Local Indic-TTS endpoint unreachable")
            except Exception as e:
                raise RuntimeError(f"Local Indic-TTS failed and offline fallback failed: {e}")

        # Remote Gradio SSE Call
        try:
            call_url = f"{endpoint}/gradio_api/call/generate_finetuned"
            payload = {"data": [text.strip(), description]}
            
            res = requests.post(call_url, json=payload, timeout=15)
            if res.status_code != 200:
                return _fallback_to_local_mms(f"Remote Indic-TTS HTTP {res.status_code}")

            event_id = res.json().get("event_id")
            if not event_id:
                return _fallback_to_local_mms("Missing event_id in Indic-TTS response")

            # Stream event response to retrieve audio path/url
            stream_url = f"{endpoint}/gradio_api/call/generate_finetuned/{event_id}"
            stream_res = requests.get(stream_url, stream=True, timeout=25)
            
            audio_url = None
            current_event = None
            for raw_line in stream_res.iter_lines():
                if not raw_line:
                    continue
                line = raw_line.decode("utf-8")
                if line.startswith("event:"):
                    current_event = line.replace("event:", "").strip()
                elif line.startswith("data:"):
                    data_str = line.replace("data:", "").strip()
                    if data_str and data_str != "null":
                        try:
                            payload_json = json.loads(data_str)
                            if current_event == "complete" or not audio_url:
                                if isinstance(payload_json, list) and len(payload_json) > 0:
                                    item = payload_json[0]
                                    if isinstance(item, dict):
                                        audio_url = item.get("url") or item.get("path")
                                    elif isinstance(item, str):
                                        audio_url = item
                                elif isinstance(payload_json, dict):
                                    audio_url = payload_json.get("url") or payload_json.get("path")
                        except Exception:
                            pass
                if audio_url and current_event == "complete":
                    break

            if not audio_url:
                return _fallback_to_local_mms("Stream did not contain synthesized audio URL")

            # Normalize relative/proxy URL
            if "/c/gradio_api/" in audio_url:
                audio_url = audio_url.replace("/c/gradio_api/", "/")
            elif not audio_url.startswith("http"):
                audio_url = f"{self.endpoint_url}/gradio_api/file={audio_url}"

            audio_download = requests.get(audio_url, timeout=20)
            if audio_download.status_code != 200:
                return _fallback_to_local_mms(f"Failed to download audio from {audio_url} (HTTP {audio_download.status_code})")

            audio_bytes = audio_download.content
            elapsed = time.time() - start_time

            sample_rate = 44100
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
                "success": True,
                "engine": "indic_tts",
                "model_name": "ai4bharat/indic-parler-tts (bodhan-ai/indic-speak)",
                "text": text,
                "speaker": speaker_info["name"],
                "speaker_id": speaker_id,
                "sample_rate": sample_rate,
                "duration": duration,
                "elapsed_seconds": round(elapsed, 2),
                "format": "wav",
                "mime_type": "audio/wav",
                "audio_base64": audio_b64,
                "file_size": len(audio_bytes),
            }
        except Exception as exc:
            return _fallback_to_local_mms(f"Cloud stream exception: {exc}")
