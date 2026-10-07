"""
CLI Runner and Automated Test Suite for KanoAI Gujarati TTS
Usage:
    .venv/bin/python python/tts/cli.py --test
    .venv/bin/python python/tts/cli.py --engine indic_f5 --text "નમસ્તે" --output out_f5.wav
    .venv/bin/python python/tts/cli.py --engine indic_tts --text "નમસ્તે" --output out_tts.wav
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

    # Test 1: IndicF5
    print("▶ 1. Testing AI4Bharat IndicF5 (Flow-Matching Neural TTS)...")
    try:
        f5_res = service.synthesize(engine="indic_f5", text=test_phrase)
        print(f"   ✅ IndicF5 Success!")
        print(f"      • Model: {f5_res['model_name']}")
        print(f"      • Sample Rate: {f5_res['sample_rate']} Hz")
        print(f"      • Duration: {f5_res['duration']}s")
        print(f"      • Time Elapsed: {f5_res['elapsed_seconds']}s")
        print(f"      • File Size: {f5_res['file_size']} bytes")

        # Save test output
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output", "tts"))
        os.makedirs(output_dir, exist_ok=True)
        out_f5 = os.path.join(output_dir, "test_indic_f5.wav")
        with open(out_f5, "wb") as f:
            f.write(base64.b64decode(f5_res["audio_base64"]))
        print(f"      • Saved: {out_f5}\n")
    except Exception as e:
        print(f"   ❌ IndicF5 Failed: {e}\n")

    # Test 2: Indic-TTS / Indic-Speak
    print("▶ 2. Testing AI4Bharat Indic-TTS / Indic-Speak (Dhara - Female)...")
    try:
        tts_res = service.synthesize(engine="indic_tts", text=test_phrase, speaker_id="dhara")
        print(f"   ✅ Indic-TTS Success!")
        print(f"      • Model: {tts_res['model_name']}")
        print(f"      • Speaker: {tts_res['speaker']}")
        print(f"      • Sample Rate: {tts_res['sample_rate']} Hz")
        print(f"      • Duration: {tts_res['duration']}s")
        print(f"      • Time Elapsed: {tts_res['elapsed_seconds']}s")
        print(f"      • File Size: {tts_res['file_size']} bytes")

        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output", "tts"))
        os.makedirs(output_dir, exist_ok=True)
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
    parser.add_argument("--test", action="store_true", help="Run automated test suite for both engines")
    parser.add_argument("--engine", choices=["indic_f5", "indic_tts"], default="indic_f5", help="TTS Engine")
    parser.add_argument("--text", type=str, help="Gujarati text to synthesize")
    parser.add_argument("--speaker", type=str, default="dhara", help="Speaker for Indic-TTS (dhara, parth)")
    parser.add_argument("--output", type=str, default="output.wav", help="Output audio file path")
    parser.add_argument("--compare", action="store_true", help="Synthesize with both engines")
    parser.add_argument("--api-url", type=str, help="Custom API or server URL (e.g. http://localhost:7860)")
    parser.add_argument("--f5-api-url", type=str, help="Custom IndicF5 server URL")
    parser.add_argument("--tts-api-url", type=str, help="Custom Indic-TTS server URL")
    parser.add_argument("--token", type=str, help="Hugging Face User Token for ZeroGPU")
    parser.add_argument("--speed", type=float, default=0.75, help="Speech rate multiplier (default: 0.75)")

    args = parser.parse_args()

    if args.test:
        run_test()
        return

    if not args.text:
        parser.print_help()
        sys.exit(1)

    service = TTSService()

    if args.compare:
        print(f"Comparing both engines for: '{args.text}' (speed: {args.speed}x)")
        comp = service.compare(
            text=args.text,
            speaker_id=args.speaker,
            f5_api_url=args.f5_api_url or args.api_url,
            tts_api_url=args.tts_api_url or args.api_url,
            hf_token=args.token,
            speed=args.speed,
        )
        os.makedirs("output/tts", exist_ok=True)
        if comp["has_f5"]:
            with open("output/tts/compare_f5.wav", "wb") as f:
                f.write(base64.b64decode(comp["results"]["indic_f5"]["audio_base64"]))
            print("Saved IndicF5: output/tts/compare_f5.wav")
        if comp["has_tts"]:
            with open("output/tts/compare_tts.wav", "wb") as f:
                f.write(base64.b64decode(comp["results"]["indic_tts"]["audio_base64"]))
            print("Saved Indic-TTS: output/tts/compare_tts.wav")
    else:
        print(f"Synthesizing with {args.engine}: '{args.text}' (speed: {args.speed}x)")
        res = service.synthesize(
            engine=args.engine,
            text=args.text,
            speaker_id=args.speaker,
            f5_api_url=args.f5_api_url or args.api_url,
            tts_api_url=args.tts_api_url or args.api_url,
            api_url=args.api_url,
            hf_token=args.token,
            speed=args.speed,
        )
        with open(args.output, "wb") as f:
            f.write(base64.b64decode(res["audio_base64"]))
        print(f"Saved: {args.output} (Duration: {res['duration']}s, Time: {res['elapsed_seconds']}s)")


if __name__ == "__main__":
    main()
