"""
CLI Runner and Automated Test Suite for KanoAI Gujarati TTS
Usage:
    .venv/bin/python python/tts/cli.py --test
    .venv/bin/python python/tts/cli.py --engine mms_tts --text "નમસ્તે" --output out_mms.wav
    .venv/bin/python python/tts/cli.py --engine piper_tts --voice rohan --text "નમસ્તે" --output out_piper.wav
    .venv/bin/python python/tts/cli.py --engine espeak_ng --lang gu --text "નમસ્તે" --output out_espeak.wav
    .venv/bin/python python/tts/cli.py --compare --text "ગુજરાતી ભાષા સુંદર છે."
"""

import os
import sys
import argparse
import base64

try:
    from .tts_service import TTSService
except (ImportError, ValueError):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(current_dir))
    from tts.tts_service import TTSService


def run_test():
    print("=" * 60)
    print("🧪 Running KanoAI Gujarati TTS Engine Automated Tests")
    print("=" * 60)

    service = TTSService()
    test_phrase = "નમસ્તે, ગુજરાતી ભાષા શીખવી ખૂબ જ સરળ અને આનંદદાયક છે."
    print(f"Test Phrase: {test_phrase}\n")

    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output", "tts"))
    os.makedirs(output_dir, exist_ok=True)

    # Test 1: Meta MMS-TTS (Offline VITS)
    print("▶ 1. Testing Meta MMS-TTS (100% Offline VITS facebook/mms-tts-guj)...")
    try:
        mms_res = service.synthesize(engine="mms_tts", text=test_phrase)
        print(f"   ✅ MMS-TTS Success!")
        print(f"      • Model: {mms_res.get('model_name', 'facebook/mms-tts-guj')}")
        print(f"      • Sample Rate: {mms_res['sample_rate']} Hz")
        print(f"      • Duration: {mms_res.get('duration') or mms_res.get('duration_seconds')}s")
        print(f"      • Time Elapsed: {mms_res.get('elapsed_seconds') or mms_res.get('inference_time_ms', 0) / 1000}s")

        out_mms = os.path.join(output_dir, "test_mms_tts.wav")
        with open(out_mms, "wb") as f:
            f.write(base64.b64decode(mms_res["audio_base64"]))
        print(f"      • Saved: {out_mms}\n")
    except Exception as e:
        print(f"   ❌ MMS-TTS Failed: {e}\n")

    # Test 2: Piper TTS (Ultra-Fast ONNX)
    print("▶ 2. Testing Piper TTS (Neural ONNX Inference - Rohan Voice)...")
    try:
        piper_res = service.synthesize(engine="piper_tts", text=test_phrase, voice="rohan")
        print(f"   ✅ Piper TTS Success!")
        print(f"      • Voice: {piper_res.get('voice_name', 'Rohan')}")
        print(f"      • Sample Rate: {piper_res['sample_rate']} Hz")
        print(f"      • Duration: {piper_res['duration_seconds']}s")
        print(f"      • Inference Time: {piper_res['inference_time_ms']} ms")
        print(f"      • Is Mock: {piper_res.get('is_mock', False)}")

        out_piper = os.path.join(output_dir, "test_piper_tts.wav")
        with open(out_piper, "wb") as f:
            f.write(base64.b64decode(piper_res["audio_base64"]))
        print(f"      • Saved: {out_piper}\n")
    except Exception as e:
        print(f"   ❌ Piper TTS Failed: {e}\n")

    # Test 3: eSpeak-NG (Formant & Phoneme Debugger)
    print("▶ 3. Testing eSpeak-NG (Formant Synthesis & Phoneme Analysis - Gujarati)...")
    try:
        espeak_res = service.synthesize(engine="espeak_ng", text=test_phrase, lang="gu")
        print(f"   ✅ eSpeak-NG Success!")
        print(f"      • Language: {espeak_res.get('lang', 'gu')}")
        print(f"      • Method: {espeak_res.get('method')}")
        print(f"      • IPA: {espeak_res.get('debug', {}).get('ipa', 'N/A')}")
        print(f"      • Phonemes: {espeak_res.get('debug', {}).get('phonemes', [])[:8]}...")
        print(f"      • Duration: {espeak_res['duration_seconds']}s")
        print(f"      • Inference Time: {espeak_res['inference_time_ms']} ms")

        out_espeak = os.path.join(output_dir, "test_espeak_ng.wav")
        with open(out_espeak, "wb") as f:
            f.write(base64.b64decode(espeak_res["audio_base64"]))
        print(f"      • Saved: {out_espeak}\n")
    except Exception as e:
        print(f"   ❌ eSpeak-NG Failed: {e}\n")

    # Test 4: IndicF5
    print("▶ 4. Testing AI4Bharat IndicF5 (Flow-Matching Neural TTS)...")
    try:
        f5_res = service.synthesize(engine="indic_f5", text=test_phrase)
        print(f"   ✅ IndicF5 Success!")
        print(f"      • Model: {f5_res['model_name']}")
        print(f"      • Sample Rate: {f5_res['sample_rate']} Hz")
        print(f"      • Duration: {f5_res['duration']}s")
        print(f"      • Time Elapsed: {f5_res['elapsed_seconds']}s")

        out_f5 = os.path.join(output_dir, "test_indic_f5.wav")
        with open(out_f5, "wb") as f:
            f.write(base64.b64decode(f5_res["audio_base64"]))
        print(f"      • Saved: {out_f5}\n")
    except Exception as e:
        print(f"   ❌ IndicF5 Failed: {e}\n")

    # Test 5: Indic-TTS
    print("▶ 5. Testing AI4Bharat Indic-TTS / Indic-Speak (Dhara - Female)...")
    try:
        tts_res = service.synthesize(engine="indic_tts", text=test_phrase, speaker_id="dhara")
        print(f"   ✅ Indic-TTS Success!")
        print(f"      • Model: {tts_res['model_name']}")
        print(f"      • Speaker: {tts_res['speaker']}")
        print(f"      • Sample Rate: {tts_res['sample_rate']} Hz")
        print(f"      • Duration: {tts_res['duration']}s")
        print(f"      • Time Elapsed: {tts_res['elapsed_seconds']}s")

        out_tts = os.path.join(output_dir, "test_indic_tts.wav")
        with open(out_tts, "wb") as f:
            f.write(base64.b64decode(tts_res["audio_base64"]))
        print(f"      • Saved: {out_tts}\n")
    except Exception as e:
        print(f"   ❌ Indic-TTS Failed: {e}\n")

    print("=" * 60)
    print("🎉 Testing completed!")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="KanoAI Gujarati TTS CLI")
    parser.add_argument("--test", action="store_true", help="Run automated test suite for all engines")
    parser.add_argument(
        "--engine",
        choices=["mms_tts", "piper_tts", "espeak_ng", "indic_f5", "indic_tts"],
        default="mms_tts",
        help="TTS Engine",
    )
    parser.add_argument("--text", type=str, help="Gujarati text to synthesize")
    parser.add_argument("--speaker", type=str, default="dhara", help="Speaker for Indic-TTS (dhara, parth)")
    parser.add_argument("--voice", type=str, default="rohan", help="Voice for Piper TTS (rohan, pratham, priyamvada, gujarati_male)")
    parser.add_argument("--lang", type=str, default="gu", help="Language code for eSpeak-NG (gu, hi)")
    parser.add_argument("--output", type=str, default="output.wav", help="Output audio file path")
    parser.add_argument("--compare", action="store_true", help="Synthesize with all engines")
    parser.add_argument("--api-url", type=str, help="Custom API or server URL (e.g. http://localhost:7860)")
    parser.add_argument("--f5-api-url", type=str, help="Custom IndicF5 server URL")
    parser.add_argument("--tts-api-url", type=str, help="Custom Indic-TTS server URL")
    parser.add_argument("--token", type=str, help="Hugging Face User Token for ZeroGPU / gated models")
    parser.add_argument("--speed", type=float, default=1.0, help="Speech rate multiplier (default: 1.0)")

    args = parser.parse_args()

    if args.test:
        run_test()
        return

    if not args.text:
        parser.print_help()
        sys.exit(1)

    service = TTSService()

    if args.compare:
        print(f"Comparing all engines for: '{args.text}' (speed: {args.speed}x)")
        comp = service.compare(
            text=args.text,
            speaker_id=args.speaker,
            voice_id=args.voice,
            lang=args.lang,
            f5_api_url=args.f5_api_url or args.api_url,
            tts_api_url=args.tts_api_url or args.api_url,
            hf_token=args.token,
            speed=args.speed,
        )
        os.makedirs("output/tts", exist_ok=True)
        if comp.get("has_mms"):
            with open("output/tts/compare_mms.wav", "wb") as f:
                f.write(base64.b64decode(comp["results"]["mms_tts"]["audio_base64"]))
            print("Saved MMS-TTS: output/tts/compare_mms.wav")
        if comp.get("has_piper"):
            with open("output/tts/compare_piper.wav", "wb") as f:
                f.write(base64.b64decode(comp["results"]["piper_tts"]["audio_base64"]))
            print("Saved Piper TTS: output/tts/compare_piper.wav")
        if comp.get("has_espeak"):
            with open("output/tts/compare_espeak.wav", "wb") as f:
                f.write(base64.b64decode(comp["results"]["espeak_ng"]["audio_base64"]))
            print("Saved eSpeak-NG: output/tts/compare_espeak.wav")
        if comp.get("has_f5"):
            with open("output/tts/compare_f5.wav", "wb") as f:
                f.write(base64.b64decode(comp["results"]["indic_f5"]["audio_base64"]))
            print("Saved IndicF5: output/tts/compare_f5.wav")
        if comp.get("has_tts"):
            with open("output/tts/compare_tts.wav", "wb") as f:
                f.write(base64.b64decode(comp["results"]["indic_tts"]["audio_base64"]))
            print("Saved Indic-TTS: output/tts/compare_tts.wav")
    else:
        print(f"Synthesizing with {args.engine}: '{args.text}' (speed: {args.speed}x)")
        res = service.synthesize(
            engine=args.engine,
            text=args.text,
            speaker_id=args.speaker,
            voice=args.voice,
            voice_id=args.voice,
            lang=args.lang,
            f5_api_url=args.f5_api_url or args.api_url,
            tts_api_url=args.tts_api_url or args.api_url,
            api_url=args.api_url,
            hf_token=args.token,
            speed=args.speed,
        )
        with open(args.output, "wb") as f:
            f.write(base64.b64decode(res["audio_base64"]))
        dur = res.get("duration") or res.get("duration_seconds")
        print(f"Saved: {args.output} (Duration: {dur}s)")
        if "debug" in res:
            print(f"IPA Phonemes: {res['debug']['ipa']}")


if __name__ == "__main__":
    main()
