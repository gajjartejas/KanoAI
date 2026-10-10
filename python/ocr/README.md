# Gujarati OCR & Vision Engine (ગુજરાતી KanoAI OCR)

A high-performance, multi-engine Optical Character Recognition (OCR) and document intelligence toolkit specialized for the Gujarati script. Supports scene text, printed books, scanned official documents, handwritten notebook pages, and individual character/line recognition.

---

## 🌟 Supported Engines & Model Matrix

| Engine | Best For | Architecture | Reference / Weights | Accuracy / Benchmark |
| :--- | :--- | :--- | :--- | :--- |
| **Bhashini-IITJ IndicPhotoOCR** *(Recommended)* | Natural scene photos, signboards, complex layouts | DBNet Detection + CRNN / Seq2Seq Indic Text Recognizer | [Bhashini-IITJ/IndicPhotoOCR](https://github.com/Bhashini-IITJ/IndicPhotoOCR) | State-of-the-art for Indic multilingual scene text & bounding box extraction |
| **Gujarati TrOCR** | Printed books, clean scanned literature, conjuncts | Vision Transformer (TrOCR) encoder-decoder | [umangchaudhari/gujarati-ocr](https://huggingface.co/umangchaudhari/gujarati-ocr) | **96.2% exact word accuracy, 1.35% CER** on 10,090 scanned Gujarati words |
| **GujaratiHCR Pipeline** | Handwritten notes, ruled notebooks, custom glyphs | Otsu/Adaptive Threshold + Projection Line/Word Slicing + CNN/LSTM/Transformer | Hybrid research architecture inspired by IIIT-H ILOCR (116k+ handwritten images) | Effective segmentation and contour-based feature extraction for cursive handwriting |

---

## 🚀 Quick Start

### 1. Run Automated Unit Tests

```bash
# Verify OCR engines, sample generators, and segmenters
.venv/bin/python3 python/ocr/cli.py --test
```

### 2. Recognize an Image via CLI

```bash
# Recognize using default recommended Bhashini IndicPhotoOCR:
.venv/bin/python3 python/ocr/cli.py --image docs/assets/ocr_samples/sample_1_printed_book.png --engine indic_photo_ocr

# Recognize printed document with Gujarati TrOCR:
.venv/bin/python3 python/ocr/cli.py --image docs/assets/ocr_samples/sample_4_official_doc.png --engine gujarati_trocr

# Run Handwriting HCR segmentation on handwritten notes:
.venv/bin/python3 python/ocr/cli.py --image docs/assets/ocr_samples/sample_3_handwritten_note.png --engine gujarati_hcr

# Compare all engines side-by-side:
.venv/bin/python3 python/ocr/cli.py --image docs/assets/ocr_samples/sample_1_printed_book.png --compare
```

### 3. Generate Benchmark Sample Datasets

```bash
# Generates 5 benchmark images with authentic Gujarati texts into docs/assets/ocr_samples/
.venv/bin/python3 python/ocr/sample_generator.py
```

### 4. Start the Unified OCR & TTS Backend Server

```bash
# Launches REST API on port 8000
.venv/bin/python3 python/ocr/server.py --port 8000
```

---

## 📡 HTTP REST API Endpoints

### 1. `POST /api/ocr/recognize`
Performs OCR on an uploaded image.

**Request**:
```json
{
  "image": "data:image/png;base64,...",
  "engine": "indic_photo_ocr", // "indic_photo_ocr" | "gujarati_trocr" | "gujarati_hcr"
  "language": "gu"
}
```

**Response**:
```json
{
  "success": true,
  "engine": "indic_photo_ocr",
  "text": "એક વનમાં એક વડનું મોટું ઝાડ હતું...",
  "confidence": 0.94,
  "execution_time_ms": 320,
  "boxes": [
    { "box": [40, 30, 240, 75], "text": "એક વનમાં એક વડનું", "confidence": 0.95 }
  ],
  "annotated_image": "data:image/jpeg;base64,..."
}
```

### 2. `POST /api/ocr/compare`
Runs an image simultaneously against all 3 OCR engines and returns a comparative JSON response.

### 3. `GET /api/ocr/samples`
Returns metadata and paths of the 5 pre-generated Gujarati test images.

### 4. `GET /api/ocr/health`
Health check and engine availability status.

---

## 🎨 Interactive Web Studio

The OCR Studio is integrated directly into the KanoAI web interface at [`docs/index.html#ocr`](../../docs/index.html):
- **Image Upload & Whiteboard**: Drag-and-drop JPG/PNG/WEBP or draw live handwriting on the interactive canvas.
- **Bounding Box Overlay**: Interactive toggle to visualize detected lines and text bounding boxes with confidence tooltips.
- **Voice Bridge**: Click `🔊 Speak with Kano TTS` to seamlessly read extracted text aloud using AI4Bharat Indic-TTS or IndicF5 voice synthesis.
- **Export Options**: 1-click clipboard copy and `.txt` file download.
