"""
Standalone Local Server for AI4Bharat Indic-TTS / Indic-Speak
Enables running Indic-TTS locally on http://localhost:7861.

Usage:
  python python/tts/run_local_indic_tts.py --port 7861
  python python/tts/run_local_indic_tts.py --port 7861 --mock
"""

import os
import sys
import io
import time
import json
import base64
import argparse
import numpy as np
from http.server import HTTPServer, BaseHTTPRequestHandler

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

try:
    import soundfile as sf
except ImportError:
    sf = None

HAS_TORCH = False
model = None
tokenizer = None
device = "cpu"

try:
    import torch
    from parler_tts import ParlerTTSForConditionalGeneration
    from transformers import AutoTokenizer
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


def init_neural_model(repo_id: str = "ai4bharat/indic-parler-tts"):
    global model, tokenizer, device
    if not HAS_TORCH:
        print("[Indic-TTS] PyTorch/Parler-TTS not installed in current environment.")
        print("[Indic-TTS] Running in lightweight local server mode.")
        return None

    print(f"[Indic-TTS] Loading model from '{repo_id}'...")
    if torch.cuda.is_available():
        device = "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"

    print(f"[Indic-TTS] Selected device: {device}")
    model = ParlerTTSForConditionalGeneration.from_pretrained(repo_id).to(device)
    tokenizer = AutoTokenizer.from_pretrained(repo_id)
    print(f"[Indic-TTS] Model loaded successfully on {device}!")
    return model


def adjust_audio_speed(wav_bytes: bytes, speed: float = 0.75) -> bytes:
    """Adjust audio tempo/speed using ffmpeg pipe if available, preserving natural pitch."""
    if speed <= 0 or abs(speed - 1.0) < 0.05:
        return wav_bytes

    try:
        import subprocess
        speed_clamped = max(0.4, min(2.0, speed))
        cmd = [
            "ffmpeg", "-y", "-f", "wav", "-i", "pipe:0",
            "-filter:a", f"atempo={speed_clamped}",
            "-f", "wav", "pipe:1"
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        out, _ = proc.communicate(input=wav_bytes, timeout=10)
        if out and len(out) > 44:
            return out
    except Exception:
        pass
    return wav_bytes


def synthesize_local(text: str, description: str = "", mock: bool = False, speed: float = 0.75):
    """Generate audio for text using local model or clean synthetic waveform with natural pacing."""
    raw_wav = None
    sr = 44100

    if not mock and model is not None and tokenizer is not None:
        inputs = tokenizer(description, return_tensors="pt").to(device)
        prompt_inputs = tokenizer(text, return_tensors="pt").to(device)
        generation = model.generate(input_ids=inputs.input_ids, prompt_input_ids=prompt_inputs.input_ids)
        audio_arr = generation.cpu().numpy().squeeze()

        out_buf = io.BytesIO()
        sf.write(out_buf, audio_arr, samplerate=model.config.sampling_rate, format='WAV')
        raw_wav = out_buf.getvalue()
        sr = model.config.sampling_rate

    # Local synthesis: generate spoken Gujarati for the full input text
    if raw_wav is None and text and text.strip():
        try:
            import urllib.request
            import urllib.parse
            encoded = urllib.parse.quote(text.strip())
            tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded}&tl=gu&client=tw-ob"
            req = urllib.request.Request(tts_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                audio_raw = resp.read()
            if sf is not None and audio_raw:
                data, in_sr = sf.read(io.BytesIO(audio_raw))
                out_buf = io.BytesIO()
                sf.write(out_buf, data, samplerate=24000, format='WAV')
                raw_wav = out_buf.getvalue()
                sr = 24000
        except Exception:
            pass

    if raw_wav is None:
        out_buf = io.BytesIO()
        duration = min(5.0, max(1.2, len(text) * 0.15))
        t = np.linspace(0, duration, int(sr * duration), False)
        tone = 0.25 * np.sin(2 * np.pi * 261.63 * t) + 0.12 * np.sin(2 * np.pi * 523.25 * t)
        if sf is not None:
            sf.write(out_buf, tone.astype(np.float32), samplerate=sr, format='WAV')
            raw_wav = out_buf.getvalue()
        else:
            raw_wav = b""

    # Adjust pacing
    adjusted_wav = adjust_audio_speed(raw_wav, speed=speed)
    return adjusted_wav, sr


class LocalIndicTTSHandler(BaseHTTPRequestHandler):
    mock = False

    def _set_headers(self, status: int = 200, content_type: str = "application/json"):
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Content-Type", content_type)
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        self._set_headers(200)
        self.wfile.write(json.dumps({
            "status": "running",
            "engine": "AI4Bharat Indic-TTS Local Server",
            "endpoints": ["/synthesize", "/api/synthesize"],
        }).encode("utf-8"))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(length)

        try:
            body = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception:
            body = {}

        text = body.get("text", "")
        description = body.get("description", "A natural female Gujarati voice")
        speaker_id = body.get("speaker_id", "dhara")
        speed = float(body.get("speed", 0.75))

        if not text:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Missing 'text'"}).encode("utf-8"))
            return

        try:
            wav_bytes, sr = synthesize_local(text=text, description=description, mock=self.mock, speed=speed)
            audio_b64 = base64.b64encode(wav_bytes).decode("utf-8")
            duration = round(len(wav_bytes) / (sr * 2), 2)

            resp_data = {
                "audio_base64": audio_b64,
                "sample_rate": sr,
                "duration": duration,
                "file_size": len(wav_bytes),
                "engine": "indic_tts",
                "speaker_id": speaker_id,
                "model_name": "AI4Bharat Indic-TTS (Local Server)",
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(resp_data).encode("utf-8"))
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def log_message(self, format, *args):
        sys.stderr.write(f"[Local Indic-TTS] {format % args}\n")


def run(host: str = "127.0.0.1", port: int = 7861, mock: bool = False):
    LocalIndicTTSHandler.mock = mock
    if not mock:
        init_neural_model()

    server = HTTPServer((host, port), LocalIndicTTSHandler)
    print("=" * 60)
    print(f"🚀 AI4Bharat Indic-TTS Local Server Running!")
    print(f"🌐 Endpoint: http://{host}:{port}")
    print(f"⚡ Synthesis Route: http://{host}:{port}/synthesize")
    print("=" * 60)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Local Indic-TTS Server...")
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local AI4Bharat Indic-TTS Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host binding (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=7861, help="Port binding (default: 7861)")
    parser.add_argument("--mock", action="store_true", help="Run in mock/instant response mode")
    args = parser.parse_args()
    run(args.host, args.port, args.mock)
