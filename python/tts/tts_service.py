"""
Unified Gujarati TTS Service
Coordinates MMS-TTS, Piper TTS, eSpeak-NG, IndicF5, and Indic-TTS engines.
"""

from typing import Dict, Any, List, Optional
from .indic_f5_tts import IndicF5Engine
from .indic_tts import IndicTTSEngine
from .mms_tts import MMSTTSEngine
from .piper_tts import PiperTTSEngine
from .espeak_tts import ESpeakTTSEngine
from .parler_tts import ParlerTTSEngine
from .bhashini_tts import BhashiniTTSEngine
from .google_tts import GoogleCloudTTSEngine

DEFAULT_GUJARATI_SAMPLES = [
    {
        "id": "greeting",
        "title": "નમસ્તે (Greetings)",
        "text": "નમસ્તે! ગુજરાતી ભાષા KanoAI માં આપનું હાર્દિક સ્વાગત છે.",
        "category": "Basic",
    },
    {
        "id": "rich_language",
        "title": "ગુજરાતી ભાષા (Rich Language)",
        "text": "ગુજરાતી ભાષા ખૂબ જ સમૃદ્ધ, મીઠી અને પ્રાચીન સાહિત્યિક પરંપરા ધરાવતી ભાષા છે.",
        "category": "Literature",
    },
    {
        "id": "daily_dialogue",
        "title": "રોજિંદી વાતચીત (Daily Life)",
        "text": "કેમ છો? આજે હવામાન ખૂબ જ સરસ છે અને અમે બહાર ફરવા જઈ રહ્યા છીએ.",
        "category": "Conversational",
    },
    {
        "id": "numbers",
        "title": "આંકડા (Numbers 1-10)",
        "text": "એક, બે, ત્રણ, ચાર, પાંચ, છ, સાત, આઠ, નવ, દસ.",
        "category": "Education",
    },
    {
        "id": "alphabet",
        "title": "કક્કો વ્યંજન (Consonants)",
        "text": "ક ખ ગ ઘ ચ છ જ ઝ ટ ઠ ડ ઢ ણ ત થ દ ધ ન પ ફ બ ભ મ ય ર લ વ શ ષ સ હ ળ ક્ષ જ્ઞ.",
        "category": "Kakko",
    },
]


class TTSService:
    def __init__(self):
        self.indic_f5 = IndicF5Engine()
        self.indic_tts = IndicTTSEngine()
        self.mms_tts = MMSTTSEngine()
        self.piper_tts = PiperTTSEngine()
        self.espeak_tts = ESpeakTTSEngine()
        self.parler_tts = ParlerTTSEngine()
        self.bhashini_tts = BhashiniTTSEngine()
        self.google_tts = GoogleCloudTTSEngine()

    def get_presets(self) -> Dict[str, Any]:
        """Return available sample texts, speaker profiles, and engine capabilities."""
        return {
            "samples": DEFAULT_GUJARATI_SAMPLES,
            "speakers": [
                {"id": k, "name": v["name"], "gender": v["gender"], "description": v["description"]}
                for k, v in self.indic_tts.SPEAKERS.items()
            ],
            "piper_voices": [
                {
                    "id": k,
                    "name": v["name"],
                    "language": v["language"],
                    "gender": v["gender"],
                    "description": v["description"],
                }
                for k, v in self.piper_tts.VOICES.items()
            ],
            "parler_presets": [
                {"id": k, "name": v["name"], "prompt": v["prompt"]}
                for k, v in self.parler_tts.PROMPT_PRESETS.items()
            ],
            "bhashini_voices": self.bhashini_tts.get_supported_voices(),
            "google_voices": self.google_tts.get_supported_voices(),
            "engines": [
                {
                    "id": "mms_tts",
                    "name": "Meta MMS-TTS (Offline VITS)",
                    "type": "End-to-End Variational Inference TTS",
                    "features": ["100% Offline & Local", "Zero Cloud Dependency", "Accurate Gujarati Phonetics"],
                    "sample_rate": 16000,
                    "url": "https://huggingface.co/facebook/mms-tts-guj",
                },
                {
                    "id": "piper_tts",
                    "name": "Piper TTS (Ultra-Fast ONNX)",
                    "type": "Neural ONNX Runtime Inference",
                    "features": ["Sub-100ms Inference", "Lightweight CPU Execution", "Native Hindi & Gujarati Models"],
                    "sample_rate": 22050,
                    "url": "https://github.com/rhasspy/piper",
                },
                {
                    "id": "parler_tts",
                    "name": "Parler-TTS Indic (Prompt-Guided)",
                    "type": "Natural Language Audio Codec Synthesis",
                    "features": ["Controllable Emotion & Style", "Prompt Description Guided", "Near-Human Prosody"],
                    "sample_rate": 24000,
                    "url": "https://huggingface.co/ai4bharat/indic-parler-tts",
                },
                {
                    "id": "web_speech",
                    "name": "Browser Native Web Speech API (Client-Side)",
                    "type": "Device Hardware Native SpeechSynthesis",
                    "features": ["Zero Server Latency", "100% Client-Side", "Native OS gu-IN Neural Voices"],
                    "sample_rate": 44100,
                    "url": "https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API",
                },
                {
                    "id": "bhashini_tts",
                    "name": "Bhashini Official Neural TTS",
                    "type": "Digital India Bhashini Mission / IIT Madras",
                    "features": ["National Benchmark Standard", "Formal Academic Diction", "Female & Male Profiles"],
                    "sample_rate": 22050,
                    "url": "https://bhashini.gov.in/",
                },
                {
                    "id": "google_cloud_tts",
                    "name": "Google Cloud Neural2 / Wavenet (gu-IN)",
                    "type": "Commercial Neural Synthesis",
                    "features": ["Standard, Wavenet & Neural2", "Studio Broadcast Clarity", "Dual Gender Profiles"],
                    "sample_rate": 24000,
                    "url": "https://cloud.google.com/text-to-speech",
                },
                {
                    "id": "espeak_ng",
                    "name": "eSpeak-NG (Formant & Phoneme Debugger)",
                    "type": "Formant Synthesis & Phoneme Analysis",
                    "features": ["Zero Neural Weights (<10 MB)", "Native Gujarati (gu) & Hindi (hi)", "IPA & Consonant Debugging"],
                    "sample_rate": 22050,
                    "url": "https://github.com/espeak-ng/espeak-ng",
                },
                {
                    "id": "indic_f5",
                    "name": "AI4Bharat IndicF5",
                    "type": "Flow-Matching Neural TTS",
                    "features": ["Voice Conditioning", "Reference Mimicking", "Near-Human Prosody"],
                    "sample_rate": 24000,
                    "url": "https://huggingface.co/ai4bharat/IndicF5",
                },
                {
                    "id": "indic_tts",
                    "name": "AI4Bharat Indic-TTS / Bodhan Indic-Speak",
                    "type": "Multi-Speaker Neural TTS",
                    "features": ["Preset Speakers (Dhara, Parth)", "High Clarity", "Instant Synthesis"],
                    "sample_rate": 44100,
                    "url": "https://huggingface.co/bodhan-ai/indic-speak",
                },
            ],
        }

    def synthesize(self, engine: str, text: str, **kwargs) -> Dict[str, Any]:
        """Synthesize speech using selected engine."""
        engine_normalized = engine.lower().replace("-", "_")

        speed = kwargs.get("speed", 1.0 if engine_normalized in ["mms_tts", "mms", "meta_mms", "vits", "piper_tts", "piper", "onnx", "espeak_ng", "espeak", "web_speech"] else 0.75)

        if engine_normalized in ["mms_tts", "mms", "meta_mms", "vits"]:
            return self.mms_tts.synthesize(
                text=text,
                speed=speed,
                model_id=kwargs.get("model_id") or kwargs.get("model") or "facebook/mms-tts-guj",
                mock=kwargs.get("mock", False),
            )
        elif engine_normalized in ["piper_tts", "piper", "onnx"]:
            return self.piper_tts.synthesize(
                text=text,
                voice_id=kwargs.get("voice_id") or kwargs.get("voice", "rohan"),
                speed=speed,
                mock=kwargs.get("mock", False),
                hf_token=kwargs.get("hf_token"),
            )
        elif engine_normalized in ["parler_tts", "parler", "indic_parler"]:
            prompt_str = kwargs.get("prompt") or kwargs.get("description") or ""
            preset_str = kwargs.get("preset", "warm_female")
            gender_kw = kwargs.get("gender")
            if not gender_kw:
                is_fem = any(w in (prompt_str + " " + preset_str).lower() for w in ["female", "woman", "girl", "dhara", "warm_female", "expressive_story", "gentle_whisper"])
                gender_kw = "female" if is_fem else "male"
            return self.parler_tts.synthesize(
                text=text,
                prompt=prompt_str,
                preset=preset_str,
                gender=gender_kw,
                api_url=kwargs.get("parler_api_url") or kwargs.get("api_url"),
                speed=speed,
                pitch_factor=kwargs.get("pitch_factor"),
                mock=kwargs.get("mock", False),
            )
        elif engine_normalized in ["web_speech", "browser_speech", "browser", "webspeech"]:
            return {
                "success": True,
                "engine": "web_speech",
                "client_side": True,
                "client_side_only": True,
                "text": text,
                "message": "Synthesized directly via Client-Side Web Speech API (window.speechSynthesis).",
            }
        elif engine_normalized in ["bhashini_tts", "bhashini", "ulca"]:
            return self.bhashini_tts.synthesize(
                text=text,
                voice_id=kwargs.get("voice_id") or kwargs.get("voice", "gu_female"),
                api_key=kwargs.get("bhashini_key") or kwargs.get("api_key"),
                api_url=kwargs.get("bhashini_url") or kwargs.get("api_url"),
                mode=kwargs.get("bhashini_mode") or kwargs.get("mode"),
                speed=speed,
                mock=kwargs.get("mock", False),
            )
        elif engine_normalized in ["google_cloud_tts", "google_tts", "google", "wavenet", "neural2"]:
            return self.google_tts.synthesize(
                text=text,
                voice_id=kwargs.get("voice_id") or kwargs.get("voice", "gu-IN-Wavenet-A"),
                api_key=kwargs.get("google_key") or kwargs.get("api_key"),
                api_url=kwargs.get("google_url") or kwargs.get("api_url"),
                mode=kwargs.get("google_mode") or kwargs.get("mode"),
                speed=speed,
                pitch=float(kwargs.get("pitch", 0.0)),
                mock=kwargs.get("mock", False),
            )
        elif engine_normalized in ["espeak_ng", "espeak", "espeakng"]:
            return self.espeak_tts.synthesize(
                text=text,
                lang=kwargs.get("lang", "gu"),
                speed=speed,
                variant=kwargs.get("variant") or kwargs.get("voice_variant") or kwargs.get("voice"),
                pitch=kwargs.get("pitch", 50),
                mock=kwargs.get("mock", False),
            )
        elif engine_normalized in ["indic_f5", "indicf5", "f5"]:
            return self.indic_f5.synthesize(
                text=text,
                ref_audio_path=kwargs.get("ref_audio_path"),
                ref_text=kwargs.get("ref_text"),
                hf_token=kwargs.get("hf_token"),
                api_url=kwargs.get("f5_api_url") or kwargs.get("api_url"),
                speed=speed,
                mock=kwargs.get("mock", False),
            )
        elif engine_normalized in ["indic_tts", "indictts", "indic_speak", "indicspeak"]:
            return self.indic_tts.synthesize(
                text=text,
                speaker_id=kwargs.get("speaker_id", "dhara"),
                description_override=kwargs.get("description"),
                api_url=kwargs.get("tts_api_url") or kwargs.get("api_url"),
                speed=speed,
                mock=kwargs.get("mock", False),
            )
        else:
            raise ValueError(f"Unknown TTS engine '{engine}'. Choose 'mms_tts', 'piper_tts', 'parler_tts', 'web_speech', 'bhashini_tts', 'google_cloud_tts', 'espeak_ng', 'indic_f5', or 'indic_tts'.")

    def compare(self, text: str, **kwargs) -> Dict[str, Any]:
        """Synthesize speech with ALL engines for side-by-side evaluation."""
        results = {}
        errors = {}
        speed = kwargs.get("speed", 1.0)
        mock = kwargs.get("mock", False)

        try:
            results["mms_tts"] = self.mms_tts.synthesize(text=text, speed=1.0, mock=mock)
        except Exception as e:
            errors["mms_tts"] = str(e)

        try:
            results["piper_tts"] = self.piper_tts.synthesize(
                text=text,
                voice_id=kwargs.get("voice_id", "rohan"),
                speed=1.0,
                mock=mock,
            )
        except Exception as e:
            errors["piper_tts"] = str(e)

        try:
            results["espeak_ng"] = self.espeak_tts.synthesize(
                text=text,
                lang=kwargs.get("lang", "gu"),
                speed=1.0,
                mock=mock,
            )
        except Exception as e:
            errors["espeak_ng"] = str(e)

        try:
            results["indic_f5"] = self.indic_f5.synthesize(
                text=text,
                ref_audio_path=kwargs.get("ref_audio_path"),
                ref_text=kwargs.get("ref_text"),
                hf_token=kwargs.get("hf_token"),
                api_url=kwargs.get("f5_api_url") or kwargs.get("api_url"),
                speed=0.75,
                mock=mock,
            )
        except Exception as e:
            errors["indic_f5"] = str(e)

        try:
            results["indic_tts"] = self.indic_tts.synthesize(
                text=text,
                speaker_id=kwargs.get("speaker_id", "dhara"),
                description_override=kwargs.get("description"),
                api_url=kwargs.get("tts_api_url") or kwargs.get("api_url"),
                speed=0.75,
                mock=mock,
            )
        except Exception as e:
            errors["indic_tts"] = str(e)

        try:
            results["parler_tts"] = self.parler_tts.synthesize(
                text=text,
                prompt=kwargs.get("prompt"),
                speed=1.0,
                mock=mock,
            )
        except Exception as e:
            errors["parler_tts"] = str(e)

        try:
            results["bhashini_tts"] = self.bhashini_tts.synthesize(
                text=text,
                voice_id=kwargs.get("voice_id", "gu_female"),
                api_key=kwargs.get("bhashini_key"),
                speed=1.0,
                mock=mock,
            )
        except Exception as e:
            errors["bhashini_tts"] = str(e)

        try:
            results["google_cloud_tts"] = self.google_tts.synthesize(
                text=text,
                voice_id=kwargs.get("google_voice_id", "gu-IN-Wavenet-A"),
                api_key=kwargs.get("google_key"),
                speed=1.0,
                mock=mock,
            )
        except Exception as e:
            errors["google_cloud_tts"] = str(e)

        return {
            "text": text,
            "mms_tts": results.get("mms_tts"),
            "piper_tts": results.get("piper_tts"),
            "parler_tts": results.get("parler_tts"),
            "bhashini_tts": results.get("bhashini_tts"),
            "google_cloud_tts": results.get("google_cloud_tts"),
            "espeak_ng": results.get("espeak_ng"),
            "indic_f5": results.get("indic_f5"),
            "indic_tts": results.get("indic_tts"),
            "results": results,
            "errors": errors,
            "has_mms": "mms_tts" in results,
            "has_piper": "piper_tts" in results,
            "has_parler": "parler_tts" in results,
            "has_bhashini": "bhashini_tts" in results,
            "has_google": "google_cloud_tts" in results,
            "has_espeak": "espeak_ng" in results,
            "has_f5": "indic_f5" in results,
            "has_tts": "indic_tts" in results,
        }
