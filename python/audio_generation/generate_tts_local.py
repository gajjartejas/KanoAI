"""
Local Neural TTS Audio Generator for Gujarati Characters & Numerals
Generates pronunciation audio for Kakko, Barakhadi, and Numerals using 100% offline Meta MMS-TTS.

Usage:
  # Benchmark sample isolated consonants, Barakhadi, and numerals:
  python python/audio_generation/generate_tts_local.py --benchmark

  # Synthesize custom text to MP3:
  python python/audio_generation/generate_tts_local.py --text "ક" --output out.mp3 --format mp3

  # Batch generate isolated Kakko consonants (WAV/MP3):
  python python/audio_generation/generate_tts_local.py --category kakko --output-dir output/tts/kakko --format mp3

  # Batch generate numerals:
  python python/audio_generation/generate_tts_local.py --category numerals --output-dir output/tts/numerals --format mp3

  # Batch generate Barakhadi series:
  python python/audio_generation/generate_tts_local.py --category barakhdi --limit 2 --output-dir output/tts/barakhdi --format mp3
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, Any, List, Optional

# Ensure repository root is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if os.path.join(REPO_ROOT, "python") not in sys.path:
    sys.path.insert(0, os.path.join(REPO_ROOT, "python"))

from python.tts.mms_tts import MMSTTSEngine

BENCHMARK_ITEMS = [
    # Isolated Consonants
    {"type": "consonant", "char": "ક", "en": "k", "desc": "Isolated consonant ka"},
    {"type": "consonant", "char": "ખ", "en": "kh", "desc": "Isolated consonant kha"},
    {"type": "consonant", "char": "ગ", "en": "g", "desc": "Isolated consonant ga"},
    {"type": "consonant", "char": "ઘ", "en": "gh", "desc": "Isolated consonant gha"},
    # Barakhadi Series for Ka
    {"type": "barakhadi", "char": "ક", "en": "ka", "desc": "Barakhadi ka"},
    {"type": "barakhadi", "char": "કા", "en": "kaa", "desc": "Barakhadi kaa"},
    {"type": "barakhadi", "char": "કિ", "en": "ki", "desc": "Barakhadi ki"},
    {"type": "barakhadi", "char": "કી", "en": "kee", "desc": "Barakhadi kee"},
    {"type": "barakhadi", "char": "કુ", "en": "ku", "desc": "Barakhadi ku"},
    {"type": "barakhadi", "char": "કે", "en": "ke", "desc": "Barakhadi ke"},
    {"type": "barakhadi", "char": "કો", "en": "ko", "desc": "Barakhadi ko"},
    # Numerals
    {"type": "numeral", "char": "૧", "en": "ek_1", "desc": "Numeral 1 (એક)"},
    {"type": "numeral", "char": "૧૦", "en": "das_10", "desc": "Numeral 10 (દસ)"},
]


def load_resource_json(rel_path: str) -> Any:
    full_path = os.path.join(REPO_ROOT, "resources", rel_path)
    if not os.path.exists(full_path):
        return None
    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_benchmark(engine: MMSTTSEngine, output_dir: str, audio_format: str = "wav", speed: float = 1.0, mock: bool = False):
    print("=" * 65)
    print("🎯 Benchmarking Pronunciation Quality (Meta MMS-TTS Offline)")
    print("=" * 65)
    os.makedirs(output_dir, exist_ok=True)

    results = []
    total_start = time.time()

    for idx, item in enumerate(BENCHMARK_ITEMS, 1):
        char = item["char"]
        desc = item["desc"]
        out_name = f"bench_{idx:02d}_{item['type']}_{item['en']}.{audio_format}"
        out_path = os.path.join(output_dir, out_name)

        t0 = time.time()
        res = engine.synthesize(char, speed=speed, mock=mock)
        t_synth = round(time.time() - t0, 3)

        # Save audio
        engine.synthesize_to_file(char, out_path, format=audio_format, speed=speed, mock=mock)
        file_sz = os.path.getsize(out_path) if os.path.exists(out_path) else 0

        print(f"[{idx:02d}/{len(BENCHMARK_ITEMS)}] {char:4s} | {desc:24s} | Dur: {res['duration']}s | Synth: {t_synth}s | Sz: {file_sz}B")
        results.append({
            "char": char,
            "type": item["type"],
            "desc": desc,
            "file": out_name,
            "duration": res["duration"],
            "synth_time": t_synth,
            "file_size": file_sz,
            "normalized": res.get("normalized_text"),
        })

    elapsed_total = round(time.time() - total_start, 2)
    print("=" * 65)
    print(f"✅ Benchmark finished in {elapsed_total}s! All {len(results)} audio files generated.")
    print(f"📁 Output directory: {output_dir}")
    print("=" * 65)
    return results


def batch_generate_kakko(engine: MMSTTSEngine, output_dir: str, audio_format: str = "mp3", limit: Optional[int] = None, mock: bool = False):
    kakko_data = load_resource_json("kakko/kakko.json")
    if not kakko_data:
        print("❌ Could not load kakko.json resource.")
        return

    os.makedirs(output_dir, exist_ok=True)
    items = kakko_data[:limit] if limit else kakko_data
    print(f"▶ Generating Kakko consonants ({len(items)} items) -> {output_dir}")

    for idx, char_info in enumerate(items, 1):
        char_gu = char_info.get("gu")
        char_id = char_info.get("id", idx)
        en_name = char_info.get("en", "").replace(" / ", "_or_").lower()
        filename = f"{char_id}_{en_name}.{audio_format}"
        out_path = os.path.join(output_dir, filename)

        engine.synthesize_to_file(char_gu, out_path, format=audio_format, mock=mock)
        print(f"  [{idx}/{len(items)}] Consonant: {char_gu} ({en_name}) -> {filename}")


def batch_generate_numerals(engine: MMSTTSEngine, output_dir: str, audio_format: str = "mp3", limit: Optional[int] = None, mock: bool = False):
    numerals_data = load_resource_json("numerals/numerals.json")
    if not numerals_data:
        print("❌ Could not load numerals.json resource.")
        return

    os.makedirs(output_dir, exist_ok=True)
    items = numerals_data[:limit] if limit else numerals_data
    print(f"▶ Generating Numerals ({len(items)} items) -> {output_dir}")

    for idx, num_info in enumerate(items, 1):
        char_gu = num_info.get("gu")
        en_name = str(num_info.get("en"))
        filename = f"{en_name}.{audio_format}"
        out_path = os.path.join(output_dir, filename)

        engine.synthesize_to_file(char_gu, out_path, format=audio_format, mock=mock)
        print(f"  [{idx}/{len(items)}] Numeral: {char_gu} ({num_info.get('name_gu')}) -> {filename}")


def batch_generate_barakhdi(engine: MMSTTSEngine, output_dir: str, audio_format: str = "mp3", limit: Optional[int] = None, mock: bool = False):
    barakhdi_data = load_resource_json("barakhdi/barakhdi.json")
    if not barakhdi_data:
        print("❌ Could not load barakhdi.json resource.")
        return

    sections = barakhdi_data[:limit] if limit else barakhdi_data
    print(f"▶ Generating Barakhadi Series ({len(sections)} sections) -> {output_dir}")

    for s_idx, sec in enumerate(sections):
        sec_en = sec.get("en", "").lower()
        sec_dir = os.path.join(output_dir, f"{s_idx}_{sec_en}")
        os.makedirs(sec_dir, exist_ok=True)

        chars = sec.get("chars", [])
        for c_idx, c_info in enumerate(chars):
            c_gu = c_info.get("gu")
            c_id = c_info.get("id", c_idx)
            c_en = c_info.get("en", "").replace(" / ", "_or_").lower()
            filename = f"{c_id}_{c_en}.{audio_format}"
            out_path = os.path.join(sec_dir, filename)

            engine.synthesize_to_file(c_gu, out_path, format=audio_format, mock=mock)
            print(f"  [Sec {s_idx}:{c_idx+1}/{len(chars)}] {c_gu} ({c_en}) -> {filename}")


def main():
    parser = argparse.ArgumentParser(description="KanoAI Local Neural TTS Generator (MMS-TTS)")
    parser.add_argument("--benchmark", action="store_true", help="Run standard quality benchmark on consonants, Barakhadi & numerals")
    parser.add_argument("--category", choices=["kakko", "barakhdi", "numerals", "all"], help="Category to batch synthesize")
    parser.add_argument("--text", type=str, help="Specific Gujarati text or character to synthesize")
    parser.add_argument("--output", type=str, help="Single output file path (e.g. out.wav or out.mp3)")
    parser.add_argument("--output-dir", type=str, default="output/tts", help="Output directory for generated files")
    parser.add_argument("--format", choices=["wav", "mp3"], default="wav", help="Audio output format (default: wav)")
    parser.add_argument("--speed", type=float, default=1.0, help="Speech rate multiplier (default: 1.0)")
    parser.add_argument("--limit", type=int, help="Limit number of items to generate (useful for testing)")
    parser.add_argument("--mock", action="store_true", help="Use lightweight mock synthesis for testing")
    parser.add_argument("--model", type=str, default="facebook/mms-tts-guj", help="Hugging Face model ID")

    args = parser.parse_args()

    engine = MMSTTSEngine(model_id=args.model)

    if args.benchmark:
        bench_dir = os.path.join(args.output_dir, "benchmark")
        run_benchmark(engine, bench_dir, audio_format=args.format, speed=args.speed, mock=args.mock)
        return

    if args.text:
        out_file = args.output or os.path.join(args.output_dir, f"synth.{args.format}")
        print(f"🎙️ Synthesizing: '{args.text}' -> {out_file} (format: {args.format})")
        saved = engine.synthesize_to_file(args.text, out_file, format=args.format, speed=args.speed, mock=args.mock)
        print(f"✅ Generated: {saved}")
        return

    if args.category == "kakko":
        kakko_dir = os.path.join(args.output_dir, "kakko")
        batch_generate_kakko(engine, kakko_dir, audio_format=args.format, limit=args.limit, mock=args.mock)
    elif args.category == "numerals":
        num_dir = os.path.join(args.output_dir, "numerals")
        batch_generate_numerals(engine, num_dir, audio_format=args.format, limit=args.limit, mock=args.mock)
    elif args.category == "barakhdi":
        barakhdi_dir = os.path.join(args.output_dir, "barakhdi")
        batch_generate_barakhdi(engine, barakhdi_dir, audio_format=args.format, limit=args.limit, mock=args.mock)
    elif args.category == "all":
        kakko_dir = os.path.join(args.output_dir, "kakko")
        num_dir = os.path.join(args.output_dir, "numerals")
        barakhdi_dir = os.path.join(args.output_dir, "barakhdi")
        batch_generate_kakko(engine, kakko_dir, audio_format=args.format, limit=args.limit, mock=args.mock)
        batch_generate_numerals(engine, num_dir, audio_format=args.format, limit=args.limit, mock=args.mock)
        batch_generate_barakhdi(engine, barakhdi_dir, audio_format=args.format, limit=args.limit, mock=args.mock)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
