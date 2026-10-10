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

        speed = kwargs.get("speed", 1.0 if engine_normalized in ["mms_tts", "mms", "meta_mms", "vits", "piper_tts", "piper", "onnx", "espeak_ng", "espeak"] else 0.75)

        if engine_normalized in ["mms_tts", "mms", "meta_mms", "vits"]:
            return self.mms_tts.synthesize(
                text=text,
                speed=speed,
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
        elif engine_normalized in ["espeak_ng", "espeak", "espeakng"]:
            return self.espeak_tts.synthesize(
                text=text,
                lang=kwargs.get("lang", "gu"),
                speed=speed,
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
        elif engine_normalized in ["indic_tts", "indictts", "indic_speak", "indicspeak", "parler"]:
            return self.indic_tts.synthesize(
                text=text,
                speaker_id=kwargs.get("speaker_id", "dhara"),
                description_override=kwargs.get("description"),
                api_url=kwargs.get("tts_api_url") or kwargs.get("api_url"),
                speed=speed,
                mock=kwargs.get("mock", False),
            )
        else:
            raise ValueError(f"Unknown TTS engine '{engine}'. Choose 'mms_tts', 'piper_tts', 'espeak_ng', 'indic_f5', or 'indic_tts'.")

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

        return {
            "text": text,
            "mms_tts": results.get("mms_tts"),
            "piper_tts": results.get("piper_tts"),
            "espeak_ng": results.get("espeak_ng"),
            "indic_f5": results.get("indic_f5"),
            "indic_tts": results.get("indic_tts"),
            "results": results,
            "errors": errors,
            "has_mms": "mms_tts" in results,
            "has_piper": "piper_tts" in results,
            "has_espeak": "espeak_ng" in results,
            "has_f5": "indic_f5" in results,
            "has_tts": "indic_tts" in results,
        }
