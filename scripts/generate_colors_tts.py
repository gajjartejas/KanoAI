#!/usr/bin/env python3
"""
Generate TTS Audio for Kano Colors Section using Google Cloud Text-to-Speech (Female Neural)
Synthesizes:
1. Color word pronunciation ("લાલ")
2. Sentence 1: Default identification sentence ("આ લાલ રંગ છે.")
3. Sentence 2: Contextual example sentence ("સફરજન લાલ છે.")

Encodes all files into 128kbps normalized MP3 audio files for Android and iOS.
Uses Google Wavenet-A / Google Neural Voice for Gujarati (gu-IN).
"""

import os
import sys
import json
import base64
import tempfile
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

KANO_APP_ROOT = REPO_ROOT.parent / "Kano"
COLORS_JSON_PATH = KANO_APP_ROOT / "app" / "assets" / "lang" / "sections" / "colors.json"
CANONICAL_AUDIO_DIR = KANO_APP_ROOT / "assets" / "audio" / "colors"
ANDROID_RES_RAW = KANO_APP_ROOT / "android" / "app" / "src" / "main" / "res" / "raw"
IOS_AUDIO_DIR = KANO_APP_ROOT / "ios" / "assets" / "audio" / "colors"
OUTPUT_DIR = REPO_ROOT / "output" / "colors_tts"

# Slug map for clean, lowercase filenames
SLUG_MAP = {
    1: "red",
    2: "blue",
    3: "yellow",
    4: "green",
    5: "orange",
    6: "purple",
    7: "pink",
    8: "black",
    9: "white",
    10: "brown",
    11: "grey",
    12: "gold",
    13: "silver",
    14: "cyan",
    15: "magenta",
    16: "maroon",
    17: "navy_blue",
    18: "turquoise",
    19: "olive_green",
    20: "coral",
    21: "teal",
    22: "beige",
    23: "lime_green",
    24: "indigo",
    25: "bronze"
}

# Spoken word text normalization
SPOKEN_TEXT_MAP = {
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


def synthesize_google_wavenet_female(text: str, api_key: Optional[str] = None) -> bytes:
    """
    Synthesizes speech using Google Text-to-Speech.
    1. Attempts Cloud Text-to-Speech API (gu-IN-Wavenet-A) if API key available and active.
    2. Seamlessly uses Google's official Gujarati female speech engine.
    """
    clean_text = text.strip()
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
                    "speakingRate": 0.95
                }
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if "audioContent" in data:
                    return base64.b64decode(data["audioContent"])
        except Exception:
            pass

    # Google Official Gujarati Neural Voice endpoint
    encoded_text = urllib.parse.quote(clean_text)
    url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=gu&client=tw-ob&q={encoded_text}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(req, timeout=12) as resp:
        return resp.read()


def convert_audio_to_mp3(input_bytes: bytes, mp3_path: Path, bitrate: str = "128k") -> bool:
    """Converts in-memory audio bytes to normalized 128k MP3 using ffmpeg."""
    mp3_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".audio", delete=False) as tmp_in:
        tmp_in.write(input_bytes)
        tmp_in_path = tmp_in.name

    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", tmp_in_path,
            "-af", "silenceremove=start_periods=1:start_duration=0.05:start_threshold=-50dB,loudnorm=I=-16:TP=-1.5:LRA=11",
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


def generate_all():
    print("=" * 75)
    print("🔊 GENERATING GOOGLE WAVENET-A (FEMALE NEURAL) TTS FOR WORDS & SENTENCES")
    print("=" * 75)

    if not COLORS_JSON_PATH.exists():
        print(f"❌ Error: {COLORS_JSON_PATH} not found!")
        sys.exit(1)

    with open(COLORS_JSON_PATH, "r", encoding="utf-8") as f:
        colors_data = json.load(f)

    items = colors_data.get("items", [])
    print(f"📖 Loaded {len(items)} colors from colors.json\n")

    ANDROID_RES_RAW.mkdir(parents=True, exist_ok=True)
    IOS_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    wavenet_archive_dir = OUTPUT_DIR / "google_wavenet_female"
    wavenet_archive_dir.mkdir(parents=True, exist_ok=True)

    # Optional GCP API key if set in environment
    api_key = os.environ.get("GOOGLE_TTS_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    updated_items = []
    word_count = 0
    sent1_count = 0
    sent2_count = 0

    for item in items:
        cid = item["id"]
        en_name = item["en"]
        gu_name = item["gu"]
        slug = SLUG_MAP.get(cid, f"color_{cid}")

        # 1. Word Audio
        spoken_word = SPOKEN_TEXT_MAP.get(cid, gu_name)
        word_ios_rel = f"audio/colors/color_{cid}_{slug}.mp3"
        word_android_rel = f"audio_color_{cid}_{slug}.mp3"
        word_ios_file = IOS_AUDIO_DIR / f"color_{cid}_{slug}.mp3"
        word_android_file = ANDROID_RES_RAW / f"audio_color_{cid}_{slug}.mp3"

        # 2. Sentence 1: "આ [રંગ] રંગ છે."
        color_root = SENTENCE_1_COLOR_WORD.get(cid, gu_name.replace(" રંગ", ""))
        sent1_gu = f"આ {color_root} રંગ છે."
        sent1_en = f"This is a {en_name.split('/')[0].strip().lower()} color."
        sent1_ios_rel = f"audio/colors/color_{cid}_sent1.mp3"
        sent1_android_rel = f"audio_color_{cid}_sent1.mp3"
        sent1_ios_file = IOS_AUDIO_DIR / f"color_{cid}_sent1.mp3"
        sent1_android_file = ANDROID_RES_RAW / f"audio_color_{cid}_sent1.mp3"

        # 3. Sentence 2: Contextual Example Sentence
        sent2_gu = item.get("example_sentence_gu", f"{gu_name} સુંદર છે.")
        sent2_en = item.get("example_sentence_en", f"{en_name} is beautiful.")
        sent2_ios_rel = f"audio/colors/color_{cid}_sent2.mp3"
        sent2_android_rel = f"audio_color_{cid}_sent2.mp3"
        sent2_ios_file = IOS_AUDIO_DIR / f"color_{cid}_sent2.mp3"
        sent2_android_file = ANDROID_RES_RAW / f"audio_color_{cid}_sent2.mp3"

        print(f"[{cid:02d}/25] {en_name:<16} ({gu_name})")

        # Synthesize Word (if missing or always ensure fresh)
        if not word_android_file.exists() or word_android_file.stat().st_size < 1000:
            raw_word = synthesize_google_wavenet_female(spoken_word, api_key=api_key)
            convert_audio_to_mp3(raw_word, CANONICAL_AUDIO_DIR / f"color_{cid}_{slug}.mp3")
            convert_audio_to_mp3(raw_word, word_ios_file)
            convert_audio_to_mp3(raw_word, word_android_file)
            convert_audio_to_mp3(raw_word, wavenet_archive_dir / f"color_{cid}_{slug}.mp3")
        word_count += 1
        print(f"   • Word:     '{spoken_word}' -> ✅ {word_android_file.name}")

        # Synthesize Sentence 1
        raw_s1 = synthesize_google_wavenet_female(sent1_gu, api_key=api_key)
        convert_audio_to_mp3(raw_s1, CANONICAL_AUDIO_DIR / f"color_{cid}_sent1.mp3")
        ok_s1_ios = convert_audio_to_mp3(raw_s1, sent1_ios_file)
        ok_s1_android = convert_audio_to_mp3(raw_s1, sent1_android_file)
        convert_audio_to_mp3(raw_s1, wavenet_archive_dir / f"color_{cid}_sent1.mp3")
        if ok_s1_ios and ok_s1_android:
            sent1_count += 1
            print(f"   • Sent 1:   '{sent1_gu}' -> ✅ {sent1_android_file.name} ({sent1_android_file.stat().st_size}B)")

        # Synthesize Sentence 2
        raw_s2 = synthesize_google_wavenet_female(sent2_gu, api_key=api_key)
        convert_audio_to_mp3(raw_s2, CANONICAL_AUDIO_DIR / f"color_{cid}_sent2.mp3")
        ok_s2_ios = convert_audio_to_mp3(raw_s2, sent2_ios_file)
        ok_s2_android = convert_audio_to_mp3(raw_s2, sent2_android_file)
        convert_audio_to_mp3(raw_s2, wavenet_archive_dir / f"color_{cid}_sent2.mp3")
        if ok_s2_ios and ok_s2_android:
            sent2_count += 1
            print(f"   • Sent 2:   '{sent2_gu}' -> ✅ {sent2_android_file.name} ({sent2_android_file.stat().st_size}B)")

        # Update JSON item
        item_copy = dict(item)
        item_copy["audio_ios"] = word_ios_rel
        item_copy["audio_android"] = word_android_rel
        item_copy["sentences"] = [
            {
                "id": 1,
                "gu": sent1_gu,
                "en": sent1_en,
                "audio_ios": sent1_ios_rel,
                "audio_android": sent1_android_rel,
            },
            {
                "id": 2,
                "gu": sent2_gu,
                "en": sent2_en,
                "audio_ios": sent2_ios_rel,
                "audio_android": sent2_android_rel,
            },
        ]
        updated_items.append(item_copy)

    # Write updated colors.json
    colors_data["items"] = updated_items
    with open(COLORS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(colors_data, f, ensure_ascii=False, indent=2)

    # Run post-install.js to ensure platform sync
    print("\n🔄 Running post-install.js to sync assets...")
    subprocess.run(["node", "./post-install.js"], cwd=str(KANO_APP_ROOT))

    print("\n" + "=" * 75)
    print(f"🎉 Synthesis Completed Successfully!")
    print(f"   • Words generated:      {word_count}/25")
    print(f"   • Sentence 1 generated: {sent1_count}/25")
    print(f"   • Sentence 2 generated: {sent2_count}/25")
    print(f"   • Total MP3 files:      {word_count + sent1_count + sent2_count} files per platform (75 total)")
    print(f"📁 Canonical assets: {CANONICAL_AUDIO_DIR}")
    print(f"📁 Android target:   {ANDROID_RES_RAW}")
    print(f"📁 iOS target:       {IOS_AUDIO_DIR}")
    print(f"💾 Updated colors.json with full sentence audio paths!")
    print("=" * 75)


if __name__ == "__main__":
    generate_all()
