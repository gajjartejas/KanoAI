"""
KanoAI Gujarati OCR Command Line Interface (CLI)
Usage:
    python python/ocr/cli.py --image path/to/doc.png
    python python/ocr/cli.py --image path/to/note.jpg --engine gujarati_hcr
    python python/ocr/cli.py --compare --image path/to/sample.png
    python python/ocr/cli.py --samples
    python python/ocr/cli.py --test
"""

import os
import sys
import json
import argparse
import time

current_dir = os.path.dirname(os.path.abspath(__file__))  # python/ocr
parent_dir = os.path.dirname(current_dir)  # python
repo_root = os.path.dirname(parent_dir)  # repo root

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from ocr.ocr_service import OCRService


def main():
    parser = argparse.ArgumentParser(description="KanoAI Gujarati OCR CLI")
    parser.add_argument("--image", help="Path to input image (JPG, PNG, WEBP)")
    parser.add_argument("--engine", default="indic_photo_ocr", choices=["indic_photo_ocr", "gujarati_trocr", "gujarati_hcr"], help="OCR engine")
    parser.add_argument("--lang", default="gujarati", help="Language code (gujarati, hindi, auto)")
    parser.add_argument("--compare", action="store_true", help="Compare IndicPhotoOCR vs GujaratiHCR side-by-side")
    parser.add_argument("--samples", action="store_true", help="Run benchmark across all 5 built-in sample images")
    parser.add_argument("--test", action="store_true", help="Run quick self-test of the OCR pipeline")
    parser.add_argument("--output", help="Optional output filepath to save extracted text")
    parser.add_argument("--json", action="store_true", help="Output full result as JSON")
    parser.add_argument("--hf-token", help="Hugging Face personal token")

    args = parser.parse_args()
    service = OCRService()

    if args.test:
        print("🧪 Running KanoAI OCR self-test...")
        sample_path = os.path.join(repo_root, "docs", "assets", "ocr_samples", "sample_5_conjuncts.png")
        if not os.path.exists(sample_path):
            from ocr.sample_generator import generate_sample_5_conjuncts
            generate_sample_5_conjuncts()

        print(f"Testing GujaratiHCR on {sample_path}...")
        t0 = time.time()
        res_hcr = service.recognize(sample_path, engine="gujarati_hcr")
        print(f"✓ GujaratiHCR: {res_hcr.get('lines_count', 0)} lines, {res_hcr.get('words_count', 0)} word boxes ({round(time.time() - t0, 2)}s)")

        print("Testing IndicPhotoOCR connectivity...")
        t0 = time.time()
        res_photo = service.recognize(sample_path, engine="indic_photo_ocr")
        print(f"✓ IndicPhotoOCR success: {res_photo.get('success')}, length: {len(res_photo.get('text', ''))} chars ({round(time.time() - t0, 2)}s)")
        print("✨ Self-test completed successfully!")
        return

    if args.samples:
        print("📊 Running OCR on all benchmark samples...")
        samples = service.get_sample_catalogs()
        for s in samples:
            abs_path = os.path.join(repo_root, "docs", s["image_url"])
            if os.path.exists(abs_path):
                print("-" * 60)
                print(f"Testing {s['title']} with {s['recommended_engine']}...")
                res = service.recognize(abs_path, engine=s["recommended_engine"], lang=args.lang, hf_token=args.hf_token)
                print(f"Result (in {res.get('elapsed_seconds')}s):")
                print(res.get("text", "")[:300])
        return

    if not args.image:
        parser.print_help()
        sys.exit(1)

    if not os.path.exists(args.image):
        print(f"❌ Error: Image file not found: {args.image}")
        sys.exit(1)

    if args.compare:
        print(f"⚖️ Comparing engines on {args.image}...")
        res = service.compare(args.image, lang=args.lang, hf_token=args.hf_token)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            p_res = res["results"]["indic_photo_ocr"]
            h_res = res["results"]["gujarati_hcr"]
            print("\n1️⃣ IndicPhotoOCR:")
            print(f"   Text: {p_res.get('text', '')}")
            print(f"   Elapsed: {p_res.get('elapsed_seconds')}s | Boxes: {p_res.get('box_count', 0)}")
            print("\n2️⃣ GujaratiHCR:")
            print(f"   Text: {h_res.get('text', '')}")
            print(f"   Elapsed: {h_res.get('elapsed_seconds')}s | Boxes: {h_res.get('box_count', 0)}")
        return

    print(f"🔍 Running {args.engine} on {args.image}...")
    res = service.recognize(args.image, engine=args.engine, lang=args.lang, hf_token=args.hf_token)

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        if res.get("success"):
            print("\n" + "=" * 50)
            print("📝 RECOGNIZED GUJARATI TEXT:")
            print("=" * 50)
            print(res.get("text", ""))
            print("=" * 50)
            print(f"⚡ Latency: {res.get('elapsed_seconds')}s | 📦 Boxes: {res.get('box_count', 0)} | 🎯 Confidence: {res.get('confidence', 0)}")
        else:
            print(f"❌ Error: {res.get('error')}")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            if args.output.endswith(".json"):
                json.dump(res, f, indent=2, ensure_ascii=False)
            else:
                f.write(res.get("text", ""))
        print(f"💾 Output saved to {args.output}")


if __name__ == "__main__":
    main()
