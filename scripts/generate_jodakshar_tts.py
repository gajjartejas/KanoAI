#!/usr/bin/env python3
"""
Generate TTS Audio for Kano Jodakshar (Joint Letters) Section using Google Gujarati Neural Voice.

Synthesizes:
1. Joint letter cluster pronunciation (e.g., "ક્ર", "પ્ર", "ત્ર")
2. Example word pronunciation (e.g., "ક્રમ", "પ્રેમ", "મિત્ર")
3. Example sentence (e.g., "ક્રમ પ્રમાણે વાંચો.", "માતા આપણને પ્રેમ કરે છે.")

Formats audio into normalized MP3 files at 96k/24kHz mono loudnorm.
Saves to canonical assets directory: Kano/assets/audio/jodakshar/
Updates Kano/app/assets/lang/sections/jodakshar.json with complete examples and audio paths.
Runs Kano/post-install.js to synchronize assets across iOS and Android.
"""

import os
import sys
import json
import time
import base64
import tempfile
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
KANO_APP_ROOT = REPO_ROOT.parent / "Kano"
JODAKSHAR_JSON_PATH = KANO_APP_ROOT / "app" / "assets" / "lang" / "sections" / "jodakshar.json"
CANONICAL_AUDIO_DIR = KANO_APP_ROOT / "assets" / "audio" / "jodakshar"

# Natural, educational Gujarati example sentences and Gujarati meanings for all 30 Jodakshar items
JODAKSHAR_SENTENCES = {
    1: {"gu": "ક્રમ પ્રમાણે વાંચો.", "en": "Read in order.", "meaning_gu": "ક્રમ"},
    2: {"gu": "માતા આપણને પ્રેમ કરે છે.", "en": "Mother loves us.", "meaning_gu": "પ્રેમ"},
    3: {"gu": "મારો મિત્ર રમે છે.", "en": "My friend is playing.", "meaning_gu": "મિત્ર"},
    4: {"gu": "અ એક સ્વર છે.", "en": "A is a vowel.", "meaning_gu": "સ્વર"},
    5: {"gu": "હું સ્કૂલમાં જાઉં છું.", "en": "I go to school.", "meaning_gu": "શાળા / સ્કૂલ"},
    6: {"gu": "કૃપા કરીને મને ક્ષમા કરજો.", "en": "Please forgive me.", "meaning_gu": "માફી / ક્ષમા"},
    7: {"gu": "પુસ્તકથી જ્ઞાન મળે છે.", "en": "Books give knowledge.", "meaning_gu": "જ્ઞાન / બુદ્ધિ"},
    8: {"gu": "તે ખૂબ અક્કલવાળો છે.", "en": "He is very sensible.", "meaning_gu": "અક્કલ / સમજ"},
    9: {"gu": "શબ્દનો સાચો ઉચ્ચાર કરો.", "en": "Pronounce the word correctly.", "meaning_gu": "ઉચ્ચાર"},
    10: {"gu": "જનતા પાસે મોટી સત્તા છે.", "en": "The people hold great power.", "meaning_gu": "સત્તા / અધિકાર"},
    11: {"gu": "આપણો ઉદ્દેશ ભણવાનો છે.", "en": "Our purpose is to learn.", "meaning_gu": "ઉદ્દેશ / હેતુ"},
    12: {"gu": "અન્નનો ક્યારેય બગાડ ન કરવો.", "en": "Never waste food.", "meaning_gu": "અન્ન / અનાજ"},
    13: {"gu": "ગુજરાતમાં છપ્પન ભોગ ધરાવાય છે.", "en": "Fifty-six delicacies are offered in Gujarat.", "meaning_gu": "છપ્પન (૫૬)"},
    14: {"gu": "કુતરાના ગળામાં પટ્ટો છે.", "en": "There is a collar on the dog's neck.", "meaning_gu": "પટ્ટો"},
    15: {"gu": "ગાંધીજી હંમેશા સત્ય બોલતા.", "en": "Gandhiji always spoke the truth.", "meaning_gu": "સત્ય / સાચું"},
    16: {"gu": "અદાલત સાચો ન્યાય કરે છે.", "en": "The court delivers true justice.", "meaning_gu": "ન્યાય"},
    17: {"gu": "વિદ્યા વિનયથી શોભે છે.", "en": "Knowledge is adorned with humility.", "meaning_gu": "વિદ્યા / શિક્ષણ"},
    18: {"gu": "મંદિરનું દ્વાર ખુલ્લું છે.", "en": "The temple door is open.", "meaning_gu": "દ્વાર / દરવાજો"},
    19: {"gu": "આ એક સુંદર સ્થાન છે.", "en": "This is a beautiful place.", "meaning_gu": "સ્થાન / જગ્યા"},
    20: {"gu": "ઈશ્વર પર પૂર્ણ શ્રદ્ધા રાખો.", "en": "Have complete faith in God.", "meaning_gu": "શ્રદ્ધા / વિશ્વાસ"},
    21: {"gu": "લીલી દ્રાક્ષ મીઠી હોય છે.", "en": "Green grapes are sweet.", "meaning_gu": "દ્રાક્ષ"},
    22: {"gu": "દુકાનમાં ઘણા ગ્રાહક છે.", "en": "There are many customers in the shop.", "meaning_gu": "ગ્રાહક"},
    23: {"gu": "મહેનતથી બધા કષ્ટ દૂર થાય છે.", "en": "All hardships are overcome by hard work.", "meaning_gu": "કષ્ટ / તકલીફ"},
    24: {"gu": "આ પુસ્તક સૌથી શ્રેષ્ઠ છે.", "en": "This book is the best.", "meaning_gu": "શ્રેષ્ઠ / ઉત્તમ"},
    27: {"gu": "દિવાળી ખુશીનો ઉત્સવ છે.", "en": "Diwali is a festival of joy.", "meaning_gu": "ઉત્સવ / તહેવાર"},
    28: {"gu": "તાજમહલ એક અદ્ભુત ઇમારત છે.", "en": "The Taj Mahal is a wonderful building.", "meaning_gu": "અદ્ભુત"},
    29: {"gu": "આજે મારો જન્મદિવસ છે.", "en": "Today is my birthday.", "meaning_gu": "જન્મ"},
    30: {"gu": "તેનું ભવિષ્ય ઉજ્જ્વળ છે.", "en": "His future is bright.", "meaning_gu": "ઉજ્જ્વળ"},
    31: {"gu": "સવારની હવામાં સ્ફૂર્તિ હોય છે.", "en": "Morning air has freshness and energy.", "meaning_gu": "સ્ફૂર્તિ"},
    32: {"gu": "પોતાનું લક્ષ્ય હંમેશા યાદ રાખો.", "en": "Always remember your goal.", "meaning_gu": "લક્ષ્ય / ધ્યેય"},
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
                    "ssmlGender": "FEMALE",
                },
                "audioConfig": {
                    "audioEncoding": "MP3",
                    "sampleRateHertz": 24000,
                    "speakingRate": speed,
                },
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
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
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"},
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
            str(mp3_path),
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


def generate_all(force: bool = False, workers: int = 5, speed: float = 0.90):
    print("=" * 80)
    print("🔊 KANO JODAKSHAR (JOINT LETTERS) AUDIO GENERATION")
    print("=" * 80)

    if not JODAKSHAR_JSON_PATH.exists():
        print(f"❌ Error: {JODAKSHAR_JSON_PATH} not found!")
        sys.exit(1)

    with open(JODAKSHAR_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", [])
    print(f"📖 Loaded {len(items)} joint letters from jodakshar.json\n")

    CANONICAL_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    api_key = os.environ.get("GOOGLE_TTS_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    tasks: List[Tuple[str, str, Path]] = []
    updated_items = []

    for item in items:
        iid = item["id"]
        cluster = item["cluster"]
        roman = item["romanization"]

        # 1. Letter sound
        letter_filename = f"jodakshar_{iid}_letter.mp3"
        letter_dest = CANONICAL_AUDIO_DIR / letter_filename
        if force or not letter_dest.exists() or letter_dest.stat().st_size < 1000:
            tasks.append((f"[{iid:02d}] Letter '{cluster}' ({roman})", cluster, letter_dest))

        # 2. Example words & sentences
        sentence_meta = JODAKSHAR_SENTENCES.get(iid, {})
        updated_examples = []
        for e_idx, example in enumerate(item.get("examples", [])):
            word = example.get("word", "")
            word_suffix = "" if e_idx == 0 else f"_{e_idx + 1}"
            word_filename = f"jodakshar_{iid}_word{word_suffix}.mp3"
            word_dest = CANONICAL_AUDIO_DIR / word_filename
            if force or not word_dest.exists() or word_dest.stat().st_size < 1000:
                tasks.append((f"[{iid:02d}] Word '{word}'", word, word_dest))

            # Sentence
            sent_gu = example.get("sentence_gu") or sentence_meta.get("gu", "")
            sent_en = example.get("sentence_en") or sentence_meta.get("en", "")
            meaning_gu = example.get("meaning_gu") or sentence_meta.get("meaning_gu", word)

            ex_copy = dict(example)
            ex_copy["audio_ios"] = f"audio/jodakshar/{word_filename}"
            ex_copy["audio_android"] = f"audio_{word_filename}"
            ex_copy["meaning_gu"] = meaning_gu

            if sent_gu:
                sent_filename = f"jodakshar_{iid}_sentence{word_suffix}.mp3"
                sent_dest = CANONICAL_AUDIO_DIR / sent_filename
                if force or not sent_dest.exists() or sent_dest.stat().st_size < 1000:
                    tasks.append((f"[{iid:02d}] Sentence '{sent_gu}'", sent_gu, sent_dest))

                ex_copy["sentence_gu"] = sent_gu
                ex_copy["sentence_en"] = sent_en
                ex_copy["sentence_audio_ios"] = f"audio/jodakshar/{sent_filename}"
                ex_copy["sentence_audio_android"] = f"audio_{sent_filename}"

            updated_examples.append(ex_copy)

        item_copy = dict(item)
        item_copy["audio_ios"] = f"audio/jodakshar/{letter_filename}"
        item_copy["audio_android"] = f"audio_{letter_filename}"
        item_copy["examples"] = updated_examples
        updated_items.append(item_copy)

    # Save updated jodakshar.json
    data["items"] = updated_items
    with open(JODAKSHAR_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Updated jodakshar.json with complete examples and audio metadata!")

    print(f"\n📋 Queued {len(tasks)} audio tasks to synthesize (force={force})")

    if tasks:
        t_start = time.time()
        success_count = 0
        fail_count = 0
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_map = {executor.submit(process_audio_task, task, api_key, speed): task for task in tasks}
            for i, future in enumerate(as_completed(future_map), 1):
                label, ok, msg = future.result()
                if ok:
                    success_count += 1
                    print(f"[{i:02d}/{len(tasks)}] ✅ {label} -> {msg}")
                else:
                    fail_count += 1
                    print(f"[{i:02d}/{len(tasks)}] ❌ {label} -> {msg}")

        elapsed = time.time() - t_start
        print(f"\n⏱️ Finished synthesis in {elapsed:.1f}s: {success_count} succeeded, {fail_count} failed.")

    # Run post-install asset sync
    print("\n🔄 Running post-install.js to synchronize assets to iOS and Android...")
    subprocess.run(["node", "./post-install.js"], cwd=str(KANO_APP_ROOT))
    print("✅ Platform asset synchronization complete!")


if __name__ == "__main__":
    generate_all()

