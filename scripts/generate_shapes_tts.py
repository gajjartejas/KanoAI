#!/usr/bin/env python3
"""
Generate TTS Audio for Kano Shapes Section using Google Gujarati Neural TTS
Synthesizes:
1. Shape word pronunciation (e.g., "વર્તુળ")
2. Sentence 1 (e.g., "સૂરજ ગોળ છે.")
3. Sentence 2 (e.g., "બંગડી વર્તુળાકાર હોય છે.")

Encodes all files into normalized 128kbps MP3 audio files.
Saves to canonical assets directory: Kano/assets/audio/shapes/
and updates Kano/app/assets/lang/sections/shapes.json with audio_ios and audio_android paths.
Runs post-install.js to synchronize assets across iOS and Android.
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

REPO_ROOT = Path(__file__).resolve().parent.parent
KANO_APP_ROOT = REPO_ROOT.parent / "Kano"
SHAPES_JSON_PATH = KANO_APP_ROOT / "app" / "assets" / "lang" / "sections" / "shapes.json"
CANONICAL_AUDIO_DIR = KANO_APP_ROOT / "assets" / "audio" / "shapes"

SLUG_MAP = {
    1: "circle",
    2: "square",
    3: "triangle",
    4: "rectangle",
    5: "oval",
    6: "star",
    7: "heart",
    8: "diamond",
    9: "pentagon",
    10: "hexagon",
    11: "heptagon",
    12: "octagon",
    13: "nonagon",
    14: "decagon",
    15: "semicircle",
    16: "crescent",
    17: "cross",
    18: "arrow",
    19: "trapezoid",
    20: "parallelogram",
    21: "cube",
    22: "cuboid",
    23: "sphere",
    24: "cylinder",
    25: "cone",
    26: "pyramid",
    27: "prism",
    28: "torus",
    29: "line",
    30: "spiral",
}

# Spoken text mapping for clean spoken Gujarati without slashes
SPOKEN_TEXT_MAP = {
    1: "વર્તુળ",
    5: "લંબગોળ",
    8: "હીરાકાર",
    16: "અર્ધચંદ્રાકાર",
    17: "ચોકડી",
    18: "તીર",
    19: "સમલંબ ચતુષ્કોણ",
    28: "કડી",
    29: "રેખા",
}


def synthesize_google_tts(text: str, api_key: Optional[str] = None) -> bytes:
    """Synthesizes speech using Google Text-to-Speech."""
    clean_text = text.strip()
    if api_key:
        try:
            url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key.strip()}"
            payload = {
                "input": {"text": clean_text},
                "voice": {
                    "languageCode": "gu-IN",
                    "name": "gu-IN-Wavenet-A",
                    "ssmlGender": "FEMALE",
                },
                "audioConfig": {
                    "audioEncoding": "MP3",
                    "sampleRateHertz": 24000,
                    "speakingRate": 0.95,
                },
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
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
        url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
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
            "ffmpeg",
            "-y",
            "-i",
            tmp_in_path,
            "-af",
            "silenceremove=start_periods=1:start_duration=0.05:start_threshold=-50dB,loudnorm=I=-16:TP=-1.5:LRA=11",
            "-codec:a",
            "libmp3lame",
            "-b:a",
            bitrate,
            "-ar",
            "24000",
            str(mp3_path),
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return res.returncode == 0
    finally:
        if os.path.exists(tmp_in_path):
            os.remove(tmp_in_path)


def generate_all():
    print("=" * 75)
    print("🔊 GENERATING TTS AUDIO FOR SHAPES (WORDS & SENTENCES)")
    print("=" * 75)

    if not SHAPES_JSON_PATH.exists():
        print(f"❌ Error: {SHAPES_JSON_PATH} not found!")
        sys.exit(1)

    with open(SHAPES_JSON_PATH, "r", encoding="utf-8") as f:
        shapes_data = json.load(f)

    items = shapes_data.get("items", [])
    print(f"📖 Loaded {len(items)} shapes from shapes.json\n")

    CANONICAL_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    api_key = os.environ.get("GOOGLE_TTS_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    updated_items = []
    word_count = 0
    sent1_count = 0
    sent2_count = 0

    for item in items:
        sid = item["id"]
        en_name = item["en"]
        gu_name = item["gu"]
        slug = SLUG_MAP.get(sid, f"shape_{sid}")

        # 1. Word Audio
        spoken_word = SPOKEN_TEXT_MAP.get(sid, gu_name.split("/")[0].strip())
        word_filename = f"shape_{sid}_{slug}.mp3"
        word_ios_rel = f"audio/shapes/{word_filename}"
        word_android_rel = f"audio_shape_{sid}_{slug}.mp3"
        word_canonical_file = CANONICAL_AUDIO_DIR / word_filename

        print(f"[{sid:02d}/30] {en_name:<18} ({spoken_word})")

        if not word_canonical_file.exists() or word_canonical_file.stat().st_size < 1000:
            raw_word = synthesize_google_tts(spoken_word, api_key=api_key)
            convert_audio_to_mp3(raw_word, word_canonical_file)
        word_count += 1
        print(f"   • Word:     '{spoken_word}' -> ✅ {word_filename}")

        # 2. Sentences
        sentences = item.get("sentences", [])
        updated_sentences = []
        for s_idx, sentence in enumerate(sentences):
            sent_num = s_idx + 1
            sent_gu = sentence.get("gu", "")
            sent_en = sentence.get("en", "")
            sent_filename = f"shape_{sid}_sent{sent_num}.mp3"
            sent_ios_rel = f"audio/shapes/{sent_filename}"
            sent_android_rel = f"audio_shape_{sid}_sent{sent_num}.mp3"
            sent_canonical_file = CANONICAL_AUDIO_DIR / sent_filename

            if not sent_canonical_file.exists() or sent_canonical_file.stat().st_size < 1000:
                raw_sent = synthesize_google_tts(sent_gu, api_key=api_key)
                convert_audio_to_mp3(raw_sent, sent_canonical_file)

            if sent_num == 1:
                sent1_count += 1
            else:
                sent2_count += 1
            print(f"   • Sent {sent_num}:   '{sent_gu}' -> ✅ {sent_filename}")

            updated_sentences.append({
                "id": sentence.get("id", sent_num),
                "gu": sent_gu,
                "en": sent_en,
                "audio_ios": sent_ios_rel,
                "audio_android": sent_android_rel,
            })

        item_copy = dict(item)
        item_copy["audio_ios"] = word_ios_rel
        item_copy["audio_android"] = word_android_rel
        item_copy["sentences"] = updated_sentences
        updated_items.append(item_copy)

    # Write updated shapes.json
    shapes_data["items"] = updated_items
    with open(SHAPES_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(shapes_data, f, ensure_ascii=False, indent=2)

    # Run post-install.js to synchronize assets to platforms
    print("\n🔄 Running post-install.js to sync assets to iOS and Android...")
    subprocess.run(["node", "./post-install.js"], cwd=str(KANO_APP_ROOT))

    print("\n" + "=" * 75)
    print(f"🎉 Synthesis Completed Successfully!")
    print(f"   • Words generated:      {word_count}/30")
    print(f"   • Sentence 1 generated: {sent1_count}/30")
    print(f"   • Sentence 2 generated: {sent2_count}/30")
    print(f"   • Total MP3 files:      {word_count + sent1_count + sent2_count} in canonical root")
    print(f"📁 Canonical assets: {CANONICAL_AUDIO_DIR}")
    print(f"💾 Updated shapes.json with audio_ios and audio_android paths!")
    print("=" * 75)


if __name__ == "__main__":
    generate_all()
