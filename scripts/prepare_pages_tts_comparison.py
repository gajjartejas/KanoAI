#!/usr/bin/env python3
"""
Compress TTS comparison WAV files to 128kbps MP3 and publish to docs/tts-comparison/
for hosting on GitHub Pages.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.compare_all_tts_models import (
    TTS_MODELS_REGISTRY,
    generate_html_player,
    generate_markdown_report,
)

SRC_OUTPUT_DIR = REPO_ROOT / "output" / "tts_comparison"
DEST_PAGES_DIR = REPO_ROOT / "docs" / "tts-comparison"


def compress_wav_to_mp3(src_wav: Path, dest_mp3: Path, bitrate: str = "128k") -> bool:
    """Compresses WAV audio file to MP3 with specified bitrate using ffmpeg."""
    dest_mp3.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(src_wav),
        "-codec:a", "libmp3lame",
        "-b:a", bitrate,
        str(dest_mp3)
    ]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        return proc.returncode == 0 and dest_mp3.exists() and dest_mp3.stat().st_size > 0
    except Exception as e:
        print(f"Error compressing {src_wav.name}: {e}")
        return False


def get_audio_duration(file_path: Path) -> float:
    """Calculates duration of audio file using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        if proc.returncode == 0 and proc.stdout.strip():
            return round(float(proc.stdout.strip()), 2)
    except Exception:
        pass
    return 0.0


def main():
    print("=" * 70)
    print("🚀 PUBLISHING GUJARATI TTS COMPARISON TO GITHUB PAGES (MP3 128K)")
    print("=" * 70)

    manifest_src = SRC_OUTPUT_DIR / "manifest.json"
    if not manifest_src.exists():
        raise FileNotFoundError(f"Source manifest not found at: {manifest_src}")

    with open(manifest_src, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    samples = manifest.get("samples", [])
    raw_results = manifest.get("results", [])

    print(f"📖 Loaded {len(samples)} sample(s) and {len(raw_results)} result items.")
    print(f"📁 Destination Directory: {DEST_PAGES_DIR}")
    DEST_PAGES_DIR.mkdir(parents=True, exist_ok=True)

    updated_results = []
    converted_count = 0
    skipped_count = 0

    for idx, item in enumerate(raw_results, 1):
        rel_wav = item.get("relative_audio_path")
        if not rel_wav:
            continue

        model_id = item["model"]
        flavor_id = item["flavor"]
        sample_id = item["sample_id"]

        src_wav_path = SRC_OUTPUT_DIR / rel_wav
        rel_mp3 = f"{model_id}/{Path(rel_wav).stem}.mp3"
        dest_mp3_path = DEST_PAGES_DIR / rel_mp3

        item_copy = dict(item)
        item_copy["relative_audio_path"] = rel_mp3
        item_copy["absolute_audio_path"] = str(dest_mp3_path)

        if dest_mp3_path.exists() and dest_mp3_path.stat().st_size > 500:
            skipped_count += 1
            dur = get_audio_duration(dest_mp3_path)
            if dur > 0:
                item_copy["duration_seconds"] = dur
            print(f"[{idx}/{len(raw_results)}] (Existing MP3) -> {rel_mp3}")
        elif src_wav_path.exists():
            success = compress_wav_to_mp3(src_wav_path, dest_mp3_path, bitrate="128k")
            if success:
                converted_count += 1
                dur = get_audio_duration(dest_mp3_path)
                if dur > 0:
                    item_copy["duration_seconds"] = dur
                size_kb = round(dest_mp3_path.stat().st_size / 1024, 1)
                print(f"[{idx}/{len(raw_results)}] Converted ({size_kb} KB, {dur}s) -> {rel_mp3}")
            else:
                print(f"[{idx}/{len(raw_results)}] FAILED conversion for {rel_wav}")
        else:
            print(f"[{idx}/{len(raw_results)}] Warning: Source WAV not found: {src_wav_path}")

        updated_results.append(item_copy)

    # Build updated GitHub Pages manifest
    pages_manifest = {
        "generated_at": manifest.get("generated_at"),
        "audio_format": "mp3",
        "audio_bitrate": "128k",
        "samples": samples,
        "results": updated_results,
    }

    manifest_dest = DEST_PAGES_DIR / "manifest.json"
    with open(manifest_dest, "w", encoding="utf-8") as f:
        json.dump(pages_manifest, f, indent=2, ensure_ascii=False)
    print(f"\n📄 Saved GitHub Pages JSON Manifest: {manifest_dest}")

    # Generate Markdown Report
    report_dest = generate_markdown_report(pages_manifest, DEST_PAGES_DIR)
    print(f"📊 Saved GitHub Pages Markdown Report: {report_dest}")

    # Generate 3-Column HTML Player
    html_dest = generate_html_player(pages_manifest, DEST_PAGES_DIR)
    print(f"🎧 Saved GitHub Pages Interactive 3-Column HTML Player: {html_dest}")

    print("\n" + "=" * 70)
    print(f"✅ GITHUB PAGES PUBLISHING READY!")
    print(f"   Converted: {converted_count} files to 128k MP3")
    print(f"   Reused:    {skipped_count} existing files")
    print(f"   Total:     {len(updated_results)} audio files in {DEST_PAGES_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
