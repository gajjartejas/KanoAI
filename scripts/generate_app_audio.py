#!/usr/bin/env python3
"""
Generate TTS Audio for all Kano App Audio Sections:
- Colors (25 color words + 25 Sentence 1 + 25 Sentence 2 = 75 MP3 files)
- Numbers (0 to 100 = 101 MP3 files)
- Barakhadi (35 series x 12 forms = 420 MP3 files)
Total: 596 MP3 audio files.

Voice: Google Neural Voice / Wavenet for Gujarati (gu-IN)
Format: 128kbps normalized MP3 (24kHz, mono, loudnorm)
Target: Kano/assets/audio/<section>/ and synced via Kano/post-install.js
"""

import os
import sys
import json
import time
import base64
import tempfile
import argparse
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional, Tuple

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
KANO_APP_ROOT = REPO_ROOT.parent / "Kano"

CANONICAL_AUDIO_DIR = KANO_APP_ROOT / "assets" / "audio"
COLORS_JSON_PATH = KANO_APP_ROOT / "app" / "assets" / "lang" / "sections" / "colors.json"
NUMERALS_JSON_PATH = KANO_APP_ROOT / "app" / "assets" / "lang" / "numerals" / "numerals.json"
BARAKHADI_JSON_PATH = KANO_APP_ROOT / "app" / "assets" / "lang" / "barakhadi" / "barakhadi.json"
JODAKSHAR_JSON_PATH = KANO_APP_ROOT / "app" / "assets" / "lang" / "sections" / "jodakshar.json"

# Slug map for colors
COLOR_SLUG_MAP = {
    1: "red", 2: "blue", 3: "yellow", 4: "green", 5: "orange",
    6: "purple", 7: "pink", 8: "black", 9: "white", 10: "brown",
    11: "grey", 12: "gold", 13: "silver", 14: "cyan", 15: "magenta",
    16: "maroon", 17: "navy_blue", 18: "turquoise", 19: "olive_green",
    20: "coral", 21: "teal", 22: "beige", 23: "lime_green", 24: "indigo",
    25: "bronze"
}

# Spoken text normalization for colors
COLOR_SPOKEN_TEXT_MAP = {
    5: "નારંગી, કેસરી",
    10: "કથ્થઈ, બદામી"
}

# Natural Gujarati primary color descriptor for Sentence 1
SENTENCE_1_COLOR_WORD = {
    5: "કેસરી",
    10: "કથ્થઈ",
    20: "પરવાળા",
    21: "તીલ વાદળી",
    22: "ક્રીમ",
    24: "ગળી",
    25: "કાંસા"
}


def synthesize_google_neural(text: str, api_key: Optional[str] = None, speed: float = 0.90, max_retries: int = 4) -> bytes:
    """Synthesizes speech using Google Gujarati Neural Voice with retry and backoff."""
    clean_text = text.strip()
    if not clean_text:
        raise ValueError("Cannot synthesize empty text")

    # 1. Attempt Cloud Text-to-Speech API if API key available
    if api_key:
        try:
            url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key.strip()}"
            payload = {
                "input": {"text": clean_text},
                "voice": {
                    "languageCode": "gu-IN",
                    "name": "gu-IN-Wavenet-A",
                    "ssmlGender": "FEMALE"
                },
                "audioConfig": {
                    "audioEncoding": "MP3",
                    "sampleRateHertz": 24000,
                    "speakingRate": speed
                }
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if "audioContent" in data:
                    return base64.b64decode(data["audioContent"])
        except Exception:
            pass

    # 2. Google Gujarati Neural Voice endpoint with exponential backoff
    encoded_text = urllib.parse.quote(clean_text)
    url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=gu&client=tw-ob&q={encoded_text}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"}
    )

    last_error = None
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
                if len(data) > 200:
                    return data
        except Exception as e:
            last_error = e
            time.sleep(1.0 * (attempt + 1))

    raise RuntimeError(f"Failed to synthesize '{clean_text}' after {max_retries} attempts: {last_error}")


def convert_audio_to_mp3(input_bytes: bytes, mp3_path: Path, bitrate: str = "96k", speed: float = 0.90) -> bool:
    """Converts in-memory audio bytes to compressed 96k MP3 with clear vocal presence at requested speed using ffmpeg."""
    mp3_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".audio", delete=False) as tmp_in:
        tmp_in.write(input_bytes)
        tmp_in_path = tmp_in.name

    try:
        # Build audio filter: apply atempo for speed, silenceremove, loudnorm, and subtle treble clarity boost
        if abs(speed - 1.0) > 0.01:
            af_filter = f"atempo={speed:.2f},silenceremove=start_periods=1:start_duration=0.04:start_threshold=-50dB,loudnorm=I=-16:TP=-1.5:LRA=11,treble=g=1.2"
        else:
            af_filter = "silenceremove=start_periods=1:start_duration=0.04:start_threshold=-50dB,loudnorm=I=-16:TP=-1.5:LRA=11,treble=g=1.2"

        cmd = [
            "ffmpeg", "-y",
            "-i", tmp_in_path,
            "-af", af_filter,
            "-codec:a", "libmp3lame",
            "-b:a", bitrate,
            "-ar", "24000",
            str(mp3_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return res.returncode == 0
    finally:
        if os.path.exists(tmp_in_path):
            os.remove(tmp_in_path)


def process_audio_task(item: Tuple[str, str, Path], api_key: Optional[str], speed: float = 0.90) -> Tuple[str, bool, str]:
    """Worker task: synthesizes text and converts to MP3 at specified speed."""
    label, text, dest_path = item
    try:
        raw_audio = synthesize_google_neural(text, api_key=api_key, speed=speed)
        ok = convert_audio_to_mp3(raw_audio, dest_path, speed=speed)
        if ok and dest_path.exists() and dest_path.stat().st_size > 500:
            return (label, True, f"{dest_path.name} ({dest_path.stat().st_size}B)")
        return (label, False, f"FFmpeg conversion failed for {dest_path.name}")
    except Exception as e:
        return (label, False, str(e))


def prepare_colors_tasks(force: bool = True) -> List[Tuple[str, str, Path]]:
    with open(COLORS_JSON_PATH, "r", encoding="utf-8") as f:
        colors_data = json.load(f)

    tasks = []
    items = colors_data.get("items", [])
    colors_dir = CANONICAL_AUDIO_DIR / "colors"
    colors_dir.mkdir(parents=True, exist_ok=True)

    for item in items:
        cid = item["id"]
        en_name = item["en"]
        gu_name = item["gu"]
        slug = COLOR_SLUG_MAP.get(cid, f"color_{cid}")

        # 1. Word
        spoken_word = COLOR_SPOKEN_TEXT_MAP.get(cid, gu_name)
        word_dest = colors_dir / f"color_{cid}_{slug}.mp3"
        if force or not word_dest.exists() or word_dest.stat().st_size < 1000:
            tasks.append((f"Color {cid} Word [{spoken_word}]", spoken_word, word_dest))

        # 2. Sentence 1
        color_root = SENTENCE_1_COLOR_WORD.get(cid, gu_name.replace(" રંગ", ""))
        sent1_gu = f"આ {color_root} રંગ છે."
        sent1_dest = colors_dir / f"color_{cid}_sent1.mp3"
        if force or not sent1_dest.exists() or sent1_dest.stat().st_size < 1000:
            tasks.append((f"Color {cid} Sent1 [{sent1_gu}]", sent1_gu, sent1_dest))

        # 3. Sentence 2
        sent2_gu = item.get("example_sentence_gu", f"{gu_name} સુંદર છે.")
        sent2_dest = colors_dir / f"color_{cid}_sent2.mp3"
        if force or not sent2_dest.exists() or sent2_dest.stat().st_size < 1000:
            tasks.append((f"Color {cid} Sent2 [{sent2_gu}]", sent2_gu, sent2_dest))

    return tasks


def prepare_numerals_tasks(force: bool = True) -> List[Tuple[str, str, Path]]:
    with open(NUMERALS_JSON_PATH, "r", encoding="utf-8") as f:
        numerals_data = json.load(f)

    tasks = []
    numbers_dir = CANONICAL_AUDIO_DIR / "numbers"
    numbers_dir.mkdir(parents=True, exist_ok=True)

    for item in numerals_data:
        nid = item["id"]
        name_gu = item.get("name_gu", "")
        dest = numbers_dir / f"{nid}_num.mp3"
        if force or not dest.exists() or dest.stat().st_size < 1000:
            tasks.append((f"Number {nid} [{name_gu}]", name_gu, dest))

    return tasks


def prepare_barakhadi_tasks(force: bool = True) -> List[Tuple[str, str, Path]]:
    with open(BARAKHADI_JSON_PATH, "r", encoding="utf-8") as f:
        barakhadi_data = json.load(f)

    tasks = []
    for sec in barakhadi_data:
        for c in sec.get("chars", []):
            gu_char = c.get("gu", "")
            audio_rel = c.get("audio_ios", "").replace("audio/", "")
            dest = CANONICAL_AUDIO_DIR / audio_rel
            if force or not dest.exists() or dest.stat().st_size < 1000:
                tasks.append((f"Barakhadi [{gu_char}] -> {audio_rel}", gu_char, dest))

    return tasks


def prepare_jodakshar_tasks(force: bool = True) -> List[Tuple[str, str, Path]]:
    with open(JODAKSHAR_JSON_PATH, "r", encoding="utf-8") as f:
        jodakshar_data = json.load(f)

    tasks = []
    jodakshar_dir = CANONICAL_AUDIO_DIR / "jodakshar"
    jodakshar_dir.mkdir(parents=True, exist_ok=True)

    for item in jodakshar_data.get("items", []):
        iid = item["id"]
        cluster = item["cluster"]

        letter_dest = jodakshar_dir / f"jodakshar_{iid}_letter.mp3"
        if force or not letter_dest.exists() or letter_dest.stat().st_size < 1000:
            tasks.append((f"Jodakshar [{cluster}] Letter", cluster, letter_dest))

        for e_idx, ex in enumerate(item.get("examples", [])):
            word = ex.get("word", "")
            suffix = "" if e_idx == 0 else f"_{e_idx + 1}"
            word_dest = jodakshar_dir / f"jodakshar_{iid}_word{suffix}.mp3"
            if force or not word_dest.exists() or word_dest.stat().st_size < 1000:
                tasks.append((f"Jodakshar [{cluster}] Word '{word}'", word, word_dest))

            sent_gu = ex.get("sentence_gu", "")
            if sent_gu:
                sent_dest = jodakshar_dir / f"jodakshar_{iid}_sentence{suffix}.mp3"
                if force or not sent_dest.exists() or sent_dest.stat().st_size < 1000:
                    tasks.append((f"Jodakshar [{cluster}] Sentence '{sent_gu}'", sent_gu, sent_dest))

    return tasks


def run_generation(section: str = "all", workers: int = 6, force: bool = True, speed: float = 0.90):
    print("=" * 80)
    print("🔊 KANO APP AUDIO SYNTHESIS: GOOGLE NEURAL / WAVENET GUJARATI (gu-IN)")
    print("=" * 80)
    print(f"🎯 Target Scope:   {section.upper()}")
    print(f"📁 Canonical Dir:  {CANONICAL_AUDIO_DIR}")
    print(f"⚡ Concurrency:    {workers} worker threads")
    print(f"⏱️ Speech Tempo:   {speed:.2f}x (slower, clear pronunciation)")
    print(f"🔄 Force Fresh:    {force}")
    print("=" * 80)

    api_key = os.environ.get("GOOGLE_TTS_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    tasks: List[Tuple[str, str, Path]] = []
    if section in ("all", "colors"):
        colors_tasks = prepare_colors_tasks(force=force)
        print(f"📋 Queued {len(colors_tasks)} Colors tasks (Words + Sentences)")
        tasks.extend(colors_tasks)

    if section in ("all", "numbers"):
        numbers_tasks = prepare_numerals_tasks(force=force)
        print(f"📋 Queued {len(numbers_tasks)} Numbers tasks (0-100)")
        tasks.extend(numbers_tasks)

    if section in ("all", "barakhadi"):
        barakhadi_tasks = prepare_barakhadi_tasks(force=force)
        print(f"📋 Queued {len(barakhadi_tasks)} Barakhadi tasks (35 series x 12)")
        tasks.extend(barakhadi_tasks)

    if section in ("all", "jodakshar"):
        jodakshar_tasks = prepare_jodakshar_tasks(force=force)
        print(f"📋 Queued {len(jodakshar_tasks)} Jodakshar tasks (30 clusters x letter/word/sentence)")
        tasks.extend(jodakshar_tasks)

    total_tasks = len(tasks)
    print(f"\n🚀 Starting batch synthesis of {total_tasks} audio files at {speed:.2f}x speed...\n")

    t_start = time.time()
    success_count = 0
    fail_count = 0
    failures = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {executor.submit(process_audio_task, task, api_key, speed): task for task in tasks}

        for i, future in enumerate(as_completed(future_map), 1):
            task = future_map[future]
            try:
                label, ok, msg = future.result()
                if ok:
                    success_count += 1
                    if i % 10 == 0 or i == total_tasks:
                        elapsed = time.time() - t_start
                        rate = i / elapsed if elapsed > 0 else 0
                        print(f"[{i:03d}/{total_tasks:03d}] ({rate:.1f} files/s) ✅ {label} -> {msg}")
                else:
                    fail_count += 1
                    failures.append((label, msg))
                    print(f"[{i:03d}/{total_tasks:03d}] ❌ {label} -> {msg}")
            except Exception as exc:
                fail_count += 1
                failures.append((task[0], str(exc)))
                print(f"[{i:03d}/{total_tasks:03d}] ❌ {task[0]} -> {exc}")

    elapsed_total = time.time() - t_start
    print("\n" + "=" * 80)
    print(f"🏁 Synthesis Finished in {elapsed_total:.1f}s!")
    print(f"   • Success: {success_count}/{total_tasks}")
    print(f"   • Failed:  {fail_count}/{total_tasks}")

    if failures:
        print("\n⚠️ Failed items:")
        for f_label, f_msg in failures[:10]:
            print(f"   - {f_label}: {f_msg}")
        if len(failures) > 10:
            print(f"   ... and {len(failures) - 10} more.")

    # Platform Synchronization via post-install.js
    print("\n🔄 Running post-install.js to synchronize to Android and iOS...")
    res = subprocess.run(["node", "./post-install.js"], cwd=str(KANO_APP_ROOT))
    if res.returncode == 0:
        print("✅ Platform asset synchronization succeeded!")
    else:
        print(f"❌ post-install.js returned exit code {res.returncode}")

    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Generate TTS audio for Kano app")
    parser.add_argument("--section", choices=["all", "colors", "numbers", "barakhadi", "jodakshar"], default="all")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--speed", type=float, default=0.90, help="Speech tempo multiplier (default: 0.90 for natural clarity)")
    parser.add_argument("--no-force", action="store_true", help="Do not overwrite existing valid files")
    args = parser.parse_args()

    run_generation(section=args.section, workers=args.workers, force=not args.no_force, speed=args.speed)


if __name__ == "__main__":
    main()
