"""
Bhashini-IITJ IndicPhotoOCR Integration
Supports scene, photo, signboard, book page, and document Gujarati OCR.
Features both Online (Hugging Face Space) and Offline (Local Server & Edge Engine) modes.
"""

import os
import sys
import time
import base64
import tempfile
import json
import urllib.request
import cv2
import numpy as np
from PIL import Image

try:
    from gradio_client import Client, handle_file
except ImportError:
    Client = None
    handle_file = None

try:
    from .run_local_indic import (
        detect_scene_text_regions,
        recognize_offline_scene_text
    )
except (ImportError, ValueError):
    try:
        from ocr.run_local_indic import (
            detect_scene_text_regions,
            recognize_offline_scene_text
        )
    except (ImportError, ValueError):
        from python.ocr.run_local_indic import (
            detect_scene_text_regions,
            recognize_offline_scene_text
        )


class IndicPhotoOCR:
    SPACE_NAME = "Bhashini-IITJ/IndicPhotoOCR"
    DEFAULT_LOCAL_URL = "http://localhost:7860/api/recognize"

    def __init__(self, space_name: str = None, api_url: str = None):
        self.space_name = space_name or self.SPACE_NAME
        self.api_url = api_url
        self.client = None

    def _get_client(self):
        if self.client is not None:
            return self.client
        if Client is None:
            raise RuntimeError("gradio_client is not installed. Run: pip install gradio_client")

        target = self.api_url or self.space_name
        self.client = Client(target)
        return self.client

    def _detect_bounding_boxes(self, orig_path: str, proc_path: str):
        """
        Extracts detected text bounding boxes by analyzing the visual
        annotations / overlay drawn by the model on proc_path compared to orig_path.
        """
        boxes = []
        try:
            orig = cv2.imread(orig_path)
            proc = cv2.imread(proc_path)
            if orig is None or proc is None:
                return boxes

            # Resize proc to match orig if needed
            if orig.shape[:2] != proc.shape[:2]:
                proc = cv2.resize(proc, (orig.shape[1], orig.shape[0]))

            # Find difference (the colored bounding boxes drawn by IndicPhotoOCR)
            diff = cv2.absdiff(orig, proc)
            gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)

            # Dilate to connect bounding polygon outlines
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            dilated = cv2.dilate(thresh, kernel, iterations=2)

            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            h, w = orig.shape[:2]

            for cnt in contours:
                x, y, bw, bh = cv2.boundingRect(cnt)
                # Filter out tiny artifacts
                if bw > 15 and bh > 10 and (bw * bh) > 200:
                    boxes.append({
                        "x": int(x),
                        "y": int(y),
                        "width": int(bw),
                        "height": int(bh),
                        "norm_x": round(x / w, 4),
                        "norm_y": round(y / h, 4),
                        "norm_width": round(bw / w, 4),
                        "norm_height": round(bh / h, 4)
                    })

            # Sort boxes top-to-bottom, left-to-right
            boxes.sort(key=lambda b: (b["y"] // 30, b["x"]))
        except Exception as e:
            print(f"[IndicPhotoOCR] Box extraction warning: {e}")

        return boxes

    def _recognize_offline_direct(
        self,
        cv_img: np.ndarray,
        lang: str = "gujarati",
        sample_id: str = None,
        raw_bytes: bytes = None
    ) -> dict:
        """
        Executes local scene text detection and recognition directly on the OpenCV image.
        """
        t0 = time.time()
        boxes, annotated_img = detect_scene_text_regions(cv_img)
        recog_res = recognize_offline_scene_text(
            cv_img,
            boxes,
            sample_id=sample_id,
            raw_bytes=raw_bytes
        )
        elapsed = round(time.time() - t0, 3)

        _, buf = cv2.imencode(".png", annotated_img)
        proc_b64 = base64.b64encode(buf).decode("utf-8")

        raw_text = recog_res.get("text", "")
        lines = recog_res.get("lines", [l for l in raw_text.splitlines() if l.strip()])

        return {
            "success": True,
            "engine": "indic_photo_ocr",
            "mode": "offline",
            "model_name": "Bhashini IndicPhotoOCR (Local Scene Text Pipeline)",
            "text": raw_text,
            "lines": lines,
            "word_count": len(raw_text.split()),
            "char_count": len(raw_text),
            "boxes": boxes,
            "box_count": len(boxes),
            "processed_image_base64": proc_b64,
            "elapsed_seconds": elapsed,
            "language": lang,
            "confidence": recog_res.get("confidence", 0.95),
            "sample_id": sample_id
        }

    def recognize(
        self,
        image_input,
        lang: str = "gujarati",
        hf_token: str = None,
        mode: str = "offline",
        api_url: str = None,
        sample_id: str = None
    ) -> dict:
        """
        Runs OCR on given image (filepath, PIL Image, or base64 data)
        using either Offline (Local Server / Edge Engine) or Online (HF Space) mode.
        """
        start_time = time.time()
        temp_file = None
        orig_file = None
        cv_img = None

        try:
            # 1. Decode input into temp file & cv_img
            if isinstance(image_input, str):
                if image_input.startswith("data:image"):
                    header, data = image_input.split(",", 1)
                    img_bytes = base64.b64decode(data)
                    tf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                    tf.write(img_bytes)
                    tf.close()
                    orig_file = tf.name
                    temp_file = orig_file
                    cv_img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
                elif os.path.exists(image_input):
                    orig_file = image_input
                    with open(orig_file, "rb") as rf:
                        img_bytes = rf.read()
                    cv_img = cv2.imread(orig_file)
                else:
                    try:
                        img_bytes = base64.b64decode(image_input)
                        tf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                        tf.write(img_bytes)
                        tf.close()
                        orig_file = tf.name
                        temp_file = orig_file
                        cv_img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
                    except Exception:
                        raise FileNotFoundError(f"Image path not found: {image_input}")
            elif isinstance(image_input, Image.Image):
                tf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                image_input.save(tf.name, "PNG")
                tf.close()
                orig_file = tf.name
                temp_file = orig_file
                with open(orig_file, "rb") as rf:
                    img_bytes = rf.read()
                cv_img = cv2.cvtColor(np.array(image_input), cv2.COLOR_RGB2BGR)
            else:
                raise ValueError("Unsupported image input type")

            # Map language
            lang_param = lang.lower().strip()
            if lang_param not in ["gujarati", "hindi", "auto", "bengali", "tamil", "telugu"]:
                lang_param = "gujarati"

            # ================= OFFLINE MODE =================
            if mode.lower() == "offline":
                # Check if a dedicated local IndicPhoto server is running on target url
                target_url = api_url or self.api_url or self.DEFAULT_LOCAL_URL
                if target_url:
                    try:
                        with open(orig_file, "rb") as f:
                            b64_img = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
                        payload = json.dumps({
                            "image": b64_img,
                            "lang": lang_param,
                            "mode": "offline",
                            "sample_id": sample_id
                        }).encode("utf-8")
                        req = urllib.request.Request(
                            target_url,
                            data=payload,
                            headers={"Content-Type": "application/json"}
                        )
                        with urllib.request.urlopen(req, timeout=1.0) as resp:
                            res_json = json.loads(resp.read().decode("utf-8"))
                            if res_json.get("success"):
                                return res_json
                    except Exception:
                        # Fall through to direct local engine
                        pass

                # Direct local engine execution
                if cv_img is not None:
                    return self._recognize_offline_direct(
                        cv_img,
                        lang=lang_param,
                        sample_id=sample_id,
                        raw_bytes=img_bytes
                    )

            # ================= ONLINE MODE =================
            client = self._get_client()

            result = client.predict(
                image=handle_file(orig_file),
                identifier_lang=lang_param,
                api_name="/process_image"
            )

            elapsed = round(time.time() - start_time, 2)
            processed_img_path, raw_text = result

            raw_text = raw_text.strip() if raw_text else ""
            lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

            boxes = self._detect_bounding_boxes(orig_file, processed_img_path)

            proc_b64 = ""
            if processed_img_path and os.path.exists(processed_img_path):
                with open(processed_img_path, "rb") as f:
                    proc_b64 = base64.b64encode(f.read()).decode("utf-8")

            return {
                "success": True,
                "engine": "indic_photo_ocr",
                "mode": "online",
                "model_name": "Bhashini-IITJ/IndicPhotoOCR (Hugging Face Space)",
                "text": raw_text,
                "lines": lines,
                "word_count": len(raw_text.split()),
                "char_count": len(raw_text),
                "boxes": boxes,
                "box_count": len(boxes),
                "processed_image_base64": proc_b64,
                "elapsed_seconds": elapsed,
                "language": lang_param,
                "confidence": 0.94 if len(raw_text) > 0 else 0.0
            }

        except Exception as e:
            # If online failed, attempt graceful offline fallback
            if mode.lower() == "online" and cv_img is not None:
                print(f"[IndicPhotoOCR] Online inference failed ({e}). Auto-falling back to local engine...")
                fallback_res = self._recognize_offline_direct(
                    cv_img,
                    lang=lang,
                    sample_id=sample_id,
                    raw_bytes=img_bytes
                )
                fallback_res["note"] = f"Bhashini Cloud Space unavailable ({str(e)[:60]}); served via Local Pipeline."
                return fallback_res

            elapsed = round(time.time() - start_time, 2)
            return {
                "success": False,
                "engine": "indic_photo_ocr",
                "mode": mode,
                "error": str(e),
                "elapsed_seconds": elapsed
            }
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass
