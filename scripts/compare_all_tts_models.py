#!/usr/bin/env python3
"""
Model Comparison & Benchmarking Tool for Gujarati TTS
Compares all offline and online Text-to-Speech models across all flavors and configurations.

Outputs:
  - Model-wise dedicated folders: output/{output_dir}/{model_name}/
  - Flavor-appended audio files:  output/{output_dir}/{model_name}/{sample_id}_{flavor}.wav
  - Comparison Manifest (JSON):   output/{output_dir}/manifest.json
  - Comparison Report (Markdown): output/{output_dir}/report.md
  - Interactive Audio Player (HTML): output/{output_dir}/index.html
"""

import os
import sys
import json
import time
import base64
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure project root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from python.tts.tts_service import TTSService

# Definition of all engines, categories, and flavor configurations
TTS_MODELS_REGISTRY = {
    "mms_tts": {
        "engine": "mms_tts",
        "name": "Meta MMS-TTS (VITS)",
        "category": "offline",
        "description": "100% Offline end-to-end VITS neural synthesis from Meta AI",
        "flavors": [
            {
                "flavor": "mms_guj",
                "name": "MMS Gujarati (facebook/mms-tts-guj)",
                "params": {"model_id": "facebook/mms-tts-guj"}
            },
            {
                "flavor": "mms_hin",
                "name": "MMS Hindi (facebook/mms-tts-hin)",
                "params": {"model_id": "facebook/mms-tts-hin"}
            }
        ]
    },
    "piper_tts": {
        "engine": "piper_tts",
        "name": "Piper TTS (Fast ONNX)",
        "category": "offline",
        "description": "Ultra-fast local neural synthesis running on ONNX Runtime",
        "flavors": [
            {
                "flavor": "rohan",
                "name": "Rohan (Hindi / Indic Male)",
                "params": {"voice_id": "rohan"}
            },
            {
                "flavor": "pratham",
                "name": "Pratham (Hindi / Indic Male)",
                "params": {"voice_id": "pratham"}
            },
            {
                "flavor": "priyamvada",
                "name": "Priyamvada (Hindi / Indic Female)",
                "params": {"voice_id": "priyamvada"}
            },
            {
                "flavor": "gujarati_male",
                "name": "Gujarati Male (Arjun4707 ONNX)",
                "params": {"voice_id": "gujarati_male"}
            }
        ]
    },
    "espeak_ng": {
        "engine": "espeak_ng",
        "name": "eSpeak-NG (Formant)",
        "category": "offline",
        "description": "Ultra-lightweight (<10 MB) formant acoustic speech synthesizer",
        "flavors": [
            {
                "flavor": "gu",
                "name": "Gujarati Default (gu)",
                "params": {"lang": "gu", "variant": "default"}
            },
            {
                "flavor": "gu_female",
                "name": "Gujarati Female Voice (gu+f2)",
                "params": {"lang": "gu", "variant": "f2"}
            },
            {
                "flavor": "gu_male_deep",
                "name": "Gujarati Deep Male Voice (gu+m3)",
                "params": {"lang": "gu", "variant": "m3"}
            },
            {
                "flavor": "hi",
                "name": "Hindi Voice (hi)",
                "params": {"lang": "hi", "variant": "default"}
            }
        ]
    },
    "indic_tts": {
        "engine": "indic_tts",
        "name": "AI4Bharat Indic-TTS / Bodhan Indic-Speak",
        "category": "online",
        "description": "High-quality neural multi-speaker synthesis from AI4Bharat",
        "flavors": [
            {
                "flavor": "dhara",
                "name": "Dhara (Female)",
                "params": {"speaker_id": "dhara"}
            },
            {
                "flavor": "parth",
                "name": "Parth (Male)",
                "params": {"speaker_id": "parth"}
            },
            {
                "flavor": "expressive_female",
                "name": "Storyteller Expressive (Female)",
                "params": {"speaker_id": "expressive_female"}
            },
            {
                "flavor": "news_male",
                "name": "News Broadcaster (Male)",
                "params": {"speaker_id": "news_male"}
            }
        ]
    },
    "indic_f5": {
        "engine": "indic_f5",
        "name": "AI4Bharat IndicF5",
        "category": "online",
        "description": "Flow-Matching non-autoregressive speech synthesis",
        "flavors": [
            {
                "flavor": "default",
                "name": "IndicF5 Flow-Matching",
                "params": {}
            }
        ]
    },
    "parler_tts": {
        "engine": "parler_tts",
        "name": "AI4Bharat Indic Parler-TTS",
        "category": "online",
        "description": "Natural language prompt-guided expressive neural speech synthesis",
        "flavors": [
            {
                "flavor": "warm_female",
                "name": "Warm & Gentle (Female)",
                "params": {"preset": "warm_female"}
            },
            {
                "flavor": "expressive_story",
                "name": "Expressive Storyteller (Female)",
                "params": {"preset": "expressive_story"}
            },
            {
                "flavor": "news_broadcast",
                "name": "Authoritative Broadcaster (Male)",
                "params": {"preset": "news_broadcast"}
            },
            {
                "flavor": "gentle_whisper",
                "name": "Intimate Whisper (Female)",
                "params": {"preset": "gentle_whisper"}
            }
        ]
    },
    "google_cloud_tts": {
        "engine": "google_cloud_tts",
        "name": "Google Cloud Text-to-Speech",
        "category": "online",
        "description": "Commercial cloud synthesis for gu-IN (Standard, Wavenet, Neural2)",
        "flavors": [
            {
                "flavor": "wavenet_a",
                "name": "Google Wavenet-A (Female Neural)",
                "params": {"voice_id": "gu-IN-Wavenet-A"}
            },
            {
                "flavor": "wavenet_b",
                "name": "Google Wavenet-B (Male Neural)",
                "params": {"voice_id": "gu-IN-Wavenet-B"}
            },
            {
                "flavor": "neural2_a",
                "name": "Google Neural2-A (Female Premium)",
                "params": {"voice_id": "gu-IN-Neural2-A"}
            },
            {
                "flavor": "standard_a",
                "name": "Google Standard-A (Female Standard)",
                "params": {"voice_id": "gu-IN-Standard-A"}
            }
        ]
    },
    "bhashini_tts": {
        "engine": "bhashini_tts",
        "name": "Bhashini Official Neural TTS",
        "category": "online",
        "description": "National Language Translation Mission official Gujarati voices",
        "flavors": [
            {
                "flavor": "gu_female",
                "name": "Bhashini Official (Female)",
                "params": {"voice_id": "gu_female"}
            },
            {
                "flavor": "gu_male",
                "name": "Bhashini Official (Male)",
                "params": {"voice_id": "gu_male"}
            }
        ]
    }
}


def load_input_samples(input_path: Path) -> List[Dict[str, Any]]:
    """Loads text samples from various JSON formats."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input JSON file not found at: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    samples = []
    if isinstance(data, list):
        for idx, item in enumerate(data):
            if isinstance(item, dict):
                sample_id = item.get("id") or f"line_{idx + 1}"
                text = item.get("text") or item.get("content") or ""
                category = item.get("category", "")
                samples.append({"id": sample_id, "text": text, "category": category})
            elif isinstance(item, str):
                samples.append({"id": f"line_{idx + 1}", "text": item, "category": ""})
    elif isinstance(data, dict):
        if "samples" in data and isinstance(data["samples"], list):
            return load_input_samples_from_list(data["samples"])
        for k, v in data.items():
            if isinstance(v, dict):
                samples.append({
                    "id": k,
                    "text": v.get("text", ""),
                    "category": v.get("category", "")
                })
            elif isinstance(v, str):
                samples.append({"id": k, "text": v, "category": ""})

    valid_samples = [s for s in samples if s["text"].strip()]
    if not valid_samples:
        raise ValueError("No valid text entries found in input JSON.")
    return valid_samples


def load_input_samples_from_list(items: list) -> List[Dict[str, Any]]:
    samples = []
    for idx, item in enumerate(items):
        if isinstance(item, dict):
            sample_id = item.get("id") or f"line_{idx + 1}"
            text = item.get("text") or item.get("content") or ""
            category = item.get("category", "")
            samples.append({"id": sample_id, "text": text, "category": category})
        elif isinstance(item, str):
            samples.append({"id": f"line_{idx + 1}", "text": item, "category": ""})
    return samples


def generate_html_player(manifest: Dict[str, Any], output_dir: Path) -> Path:
    """Generates a responsive, sleek HTML dashboard to play and compare all audio outputs."""
    html_path = output_dir / "index.html"

    samples_data = manifest.get("samples", [])
    results_data = manifest.get("results", [])

    # Group results by sample_id
    grouped_by_sample: Dict[str, List[Dict[str, Any]]] = {}
    for res in results_data:
        sid = res["sample_id"]
        if sid not in grouped_by_sample:
            grouped_by_sample[sid] = []
        grouped_by_sample[sid].append(res)

    # Group results by (model, flavor) for 3-column side-by-side matrix
    flavor_rows: Dict[tuple, Dict[str, Any]] = {}
    for res in results_data:
        key = (res["model"], res["flavor"])
        if key not in flavor_rows:
            flavor_rows[key] = {
                "model": res["model"],
                "model_name": res["model_name"],
                "flavor": res["flavor"],
                "flavor_name": res["flavor_name"],
                "category": res["category"],
                "samples": {}
            }
        flavor_rows[key]["samples"][res["sample_id"]] = res

    html_content = f"""<!DOCTYPE html>
<html lang="gu">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Gujarati TTS 3-Column Side-by-Side Comparison | KanoAI</title>
  <style>
    :root {{
      --bg: #0b1120;
      --card-bg: #1e293b;
      --card-border: #334155;
      --card-hover-border: #6366f1;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #6366f1;
      --accent-hover: #4f46e5;
      --badge-offline: #10b981;
      --badge-online: #3b82f6;
      --success: #22c55e;
      --error: #ef4444;
      --table-header-bg: #1e293b;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }}
    body {{
      background-color: var(--bg);
      color: var(--text);
      padding: 2rem 1.5rem;
      min-height: 100vh;
    }}
    .container {{
      max-width: 1560px;
      margin: 0 auto;
    }}
    header {{
      margin-bottom: 2rem;
      border-bottom: 1px solid var(--card-border);
      padding-bottom: 1.5rem;
    }}
    h1 {{
      font-size: 2.2rem;
      font-weight: 700;
      background: linear-gradient(135deg, #818cf8 0%, #c084fc 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 0.5rem;
    }}
    p.subtitle {{
      color: var(--text-muted);
      font-size: 1.05rem;
    }}
    .toolbar {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
      margin-top: 1.5rem;
    }}
    .stats-bar {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
    }}
    .stat-pill {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      padding: 0.4rem 0.9rem;
      border-radius: 9999px;
      font-size: 0.85rem;
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }}
    .stat-pill span.num {{
      font-weight: 700;
      color: #38bdf8;
    }}
    .controls-bar {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      align-items: center;
    }}
    .filter-btn, .view-btn {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      color: var(--text);
      padding: 0.45rem 1rem;
      border-radius: 0.5rem;
      cursor: pointer;
      font-size: 0.85rem;
      font-weight: 500;
      transition: all 0.2s ease;
    }}
    .filter-btn:hover, .view-btn:hover {{
      border-color: var(--accent);
      color: #fff;
    }}
    .filter-btn.active, .view-btn.active {{
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
      font-weight: 600;
    }}
    .search-input {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      color: #fff;
      padding: 0.45rem 0.9rem;
      border-radius: 0.5rem;
      font-size: 0.85rem;
      outline: none;
      min-width: 220px;
    }}
    .search-input:focus {{
      border-color: var(--accent);
    }}

    /* 3-Column Side-by-Side Matrix Styles */
    .matrix-wrapper {{
      overflow-x: auto;
      border: 1px solid var(--card-border);
      border-radius: 0.75rem;
      background: var(--card-bg);
      margin-bottom: 2.5rem;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }}
    .matrix-table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 1200px;
      text-align: left;
    }}
    .matrix-table thead th {{
      background: #1e293b;
      padding: 1.1rem 1rem;
      border-bottom: 2px solid var(--card-border);
      border-right: 1px solid var(--card-border);
      position: sticky;
      top: 0;
      z-index: 20;
    }}
    .matrix-table thead th:last-child {{
      border-right: none;
    }}
    .matrix-table tbody td {{
      padding: 1rem;
      border-bottom: 1px solid var(--card-border);
      border-right: 1px solid var(--card-border);
      vertical-align: top;
      background: rgba(30, 41, 59, 0.4);
    }}
    .matrix-table tbody td:last-child {{
      border-right: none;
    }}
    .matrix-table tbody tr:hover td {{
      background: rgba(99, 102, 241, 0.08);
    }}
    .col-model-header {{
      width: 260px;
      min-width: 240px;
    }}
    .col-sentence-header {{
      width: calc((100% - 260px) / 3);
      min-width: 320px;
    }}
    .sentence-header-card {{
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 0.5rem;
      padding: 0.75rem;
    }}
    .sentence-badge-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.4rem;
    }}
    .sentence-id {{
      font-family: monospace;
      font-size: 0.8rem;
      font-weight: 700;
      color: #38bdf8;
      background: rgba(56, 189, 248, 0.15);
      padding: 0.15rem 0.5rem;
      border-radius: 0.3rem;
    }}
    .sentence-cat {{
      font-size: 0.75rem;
      color: var(--text-muted);
    }}
    .sentence-text-preview {{
      font-size: 0.95rem;
      line-height: 1.4;
      color: #f1f5f9;
      font-weight: 500;
    }}
    .model-info-cell {{
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }}
    .model-badge-row {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .model-name {{
      font-size: 1rem;
      font-weight: 700;
      color: #f8fafc;
    }}
    .flavor-name {{
      font-size: 0.85rem;
      color: #cbd5e1;
    }}
    .audio-cell {{
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }}
    .meta-metrics {{
      display: flex;
      justify-content: space-between;
      font-size: 0.75rem;
      color: var(--text-muted);
    }}
    .meta-metrics strong {{
      color: #38bdf8;
    }}
    audio {{
      width: 100%;
      height: 36px;
      border-radius: 18px;
      outline: none;
    }}
    .file-ref {{
      font-family: monospace;
      font-size: 0.7rem;
      color: #64748b;
      word-break: break-all;
    }}
    .badge {{
      padding: 0.2rem 0.5rem;
      border-radius: 9999px;
      font-size: 0.7rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .badge.offline {{
      background: rgba(16, 185, 129, 0.2);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.4);
    }}
    .badge.online {{
      background: rgba(59, 130, 246, 0.2);
      color: #60a5fa;
      border: 1px solid rgba(59, 130, 246, 0.4);
    }}
    .error-box {{
      background: rgba(239, 68, 68, 0.1);
      border: 1px solid rgba(239, 68, 68, 0.3);
      color: #fca5a5;
      padding: 0.5rem;
      border-radius: 0.4rem;
      font-size: 0.8rem;
    }}

    /* Card Grid View Styles */
    .sample-section {{
      background: rgba(30, 41, 59, 0.6);
      border: 1px solid var(--card-border);
      border-radius: 1rem;
      padding: 1.75rem;
      margin-bottom: 2.5rem;
      backdrop-filter: blur(8px);
    }}
    .sample-header {{
      margin-bottom: 1.25rem;
    }}
    .sample-title {{
      font-size: 1.25rem;
      font-weight: 600;
      color: #e2e8f0;
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }}
    .sample-id-badge {{
      background: #475569;
      color: #fff;
      font-size: 0.8rem;
      padding: 0.2rem 0.6rem;
      border-radius: 0.4rem;
      text-transform: uppercase;
      font-family: monospace;
    }}
    .sample-text-box {{
      background: #0f172a;
      border: 1px solid #334155;
      padding: 1rem 1.25rem;
      border-radius: 0.6rem;
      margin-top: 0.75rem;
      font-size: 1.2rem;
      line-height: 1.6;
      color: #f1f5f9;
      font-weight: 500;
    }}
    .cards-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 1.25rem;
      margin-top: 1.5rem;
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 0.75rem;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: transform 0.2s ease, border-color 0.2s ease;
    }}
    .card:hover {{
      transform: translateY(-2px);
      border-color: #6366f1;
    }}
    .card-top {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 0.75rem;
    }}
    .model-title {{
      font-size: 1.05rem;
      font-weight: 600;
      color: #f8fafc;
    }}
    .meta-row {{
      display: flex;
      gap: 1rem;
      margin: 0.75rem 0;
      font-size: 0.8rem;
      color: var(--text-muted);
    }}
    .audio-wrapper {{
      margin-top: 0.75rem;
    }}
    .hidden {{
      display: none !important;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Gujarati TTS 3-Column Side-by-Side Model Comparison</h1>
      <p class="subtitle">Direct sentence-by-sentence evaluation across all offline and online Text-to-Speech models & flavours for KanoAI</p>
      
      <div class="toolbar">
        <div class="stats-bar">
          <div class="stat-pill">Total Audio Files: <span class="num">{len(results_data)}</span></div>
          <div class="stat-pill">Models / Flavors: <span class="num">{len(flavor_rows)}</span></div>
          <div class="stat-pill">Sentences: <span class="num">{len(samples_data)}</span></div>
          <div class="stat-pill">Date: <span class="num">{manifest.get("generated_at", "")[:10]}</span></div>
        </div>

        <div class="controls-bar">
          <input type="text" id="modelSearch" class="search-input" placeholder="🔍 Search model or flavor..." oninput="filterModels()">
          <button class="filter-btn active" data-filter="all" onclick="setCategoryFilter('all')">All ({len(flavor_rows)})</button>
          <button class="filter-btn" data-filter="offline" onclick="setCategoryFilter('offline')">Offline Only</button>
          <button class="filter-btn" data-filter="online" onclick="setCategoryFilter('online')">Online Only</button>
          <button class="view-btn active" id="btnMatrixView" onclick="switchView('matrix')">📊 3-Column Matrix</button>
          <button class="view-btn" id="btnGridView" onclick="switchView('grid')">🃏 Cards View</button>
        </div>
      </div>
    </header>

    <!-- 3-COLUMN SIDE-BY-SIDE MATRIX VIEW -->
    <div id="viewMatrix" class="matrix-wrapper">
      <table class="matrix-table">
        <thead>
          <tr>
            <th class="col-model-header">
              <div style="font-size: 1.05rem; font-weight: 700; color: #f8fafc;">Model & Flavor</div>
              <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.3rem;">25 Configurations</div>
            </th>
"""

    for s in samples_data:
        sid = s["id"]
        stext = s["text"]
        scat = s.get("category", "")
        html_content += f"""
            <th class="col-sentence-header">
              <div class="sentence-header-card">
                <div class="sentence-badge-row">
                  <span class="sentence-id">{sid}</span>
                  <span class="sentence-cat">{scat[:35]}</span>
                </div>
                <div class="sentence-text-preview">{stext}</div>
              </div>
            </th>
"""

    html_content += """
          </tr>
        </thead>
        <tbody>
"""

    for (m_id, f_id), row in flavor_rows.items():
        cat_badge_class = "offline" if row["category"] == "offline" else "online"
        html_content += f"""
          <tr class="matrix-row" data-category="{row['category']}" data-model="{row['model']}" data-flavor="{row['flavor']}" data-title="{row['model_name']} {row['flavor_name']}">
            <td class="model-info-cell">
              <div class="model-badge-row">
                <span class="badge {cat_badge_class}">{row['category']}</span>
              </div>
              <div class="model-name">{row['model_name']}</div>
              <div class="flavor-name">{row['flavor_name']}</div>
            </td>
"""
        for s in samples_data:
            sid = s["id"]
            it = row["samples"].get(sid)
            if it and it.get("success") and it.get("relative_audio_path"):
                dur_str = f"{it.get('duration_seconds', 0.0):.2f}s" if it.get("duration_seconds") else "N/A"
                inf_str = f"{it.get('inference_time_ms', 0):.0f}ms" if it.get("inference_time_ms") else "-"
                audio_mime = "audio/mpeg" if it['relative_audio_path'].endswith(".mp3") else "audio/wav"
                html_content += f"""
            <td>
              <div class="audio-cell">
                <div class="meta-metrics">
                  <span>⏱ Duration: <strong>{dur_str}</strong></span>
                  <span>⚡ Latency: <strong>{inf_str}</strong></span>
                </div>
                <audio controls preload="none">
                  <source src="{it['relative_audio_path']}" type="{audio_mime}">
                  Your browser does not support the audio element.
                </audio>
                <div class="file-ref">{it['relative_audio_path']}</div>
              </div>
            </td>
"""
            elif it:
                err_msg = it.get("error") or "Failed"
                html_content += f"""
            <td>
              <div class="error-box">{err_msg}</div>
            </td>
"""
            else:
                html_content += """
            <td>
              <div class="file-ref">Not synthesized</div>
            </td>
"""
        html_content += """
          </tr>
"""

    html_content += """
        </tbody>
      </table>
    </div>

    <!-- CARDS PER-SENTENCE VIEW -->
    <div id="viewGrid" class="hidden">
"""

    for s in samples_data:
        sid = s["id"]
        stext = s["text"]
        scat = s.get("category", "")
        items = grouped_by_sample.get(sid, [])

        html_content += f"""
      <section class="sample-section">
        <div class="sample-header">
          <div class="sample-title">
            <span class="sample-id-badge">{sid}</span>
            <span>{scat or "Sample Text"}</span>
          </div>
          <div class="sample-text-box">{stext}</div>
        </div>

        <div class="cards-grid">
"""
        for it in items:
            cat_badge_class = "offline" if it["category"] == "offline" else "online"
            rel_audio_path = it.get("relative_audio_path", "")
            duration_str = f"{it.get('duration_seconds', 0.0):.2f}s" if it.get('duration_seconds') else "N/A"
            inf_time_str = f"{it.get('inference_time_ms', 0):.0f}ms" if it.get('inference_time_ms') else "N/A"
            fallback_label = " (Fallback/Local)" if it.get("is_fallback") or it.get("is_mock") else ""

            html_content += f"""
          <div class="card" data-category="{it['category']}" data-title="{it['model_name']} {it['flavor_name']}">
            <div>
              <div class="card-top">
                <div>
                  <div class="model-title">{it['model_name']}</div>
                  <div class="flavor-title">{it['flavor_name']}{fallback_label}</div>
                </div>
                <span class="badge {cat_badge_class}">{it['category']}</span>
              </div>
              <div class="meta-row">
                <div>⏱ Duration: <strong>{duration_str}</strong></div>
                <div>⚡ Latency: <strong>{inf_time_str}</strong></div>
                <div>Rate: <strong>{it.get('sample_rate', 'N/A')}Hz</strong></div>
              </div>
            </div>
            <div class="audio-wrapper">
"""
            if it.get("success") and rel_audio_path:
                card_audio_mime = "audio/mpeg" if rel_audio_path.endswith(".mp3") else "audio/wav"
                html_content += f"""
              <audio controls preload="none">
                <source src="{rel_audio_path}" type="{card_audio_mime}">
                Your browser does not support the audio element.
              </audio>
              <div class="file-ref">{rel_audio_path}</div>
"""
            else:
                err_msg = it.get("error") or "Generation failed"
                html_content += f"""
              <div class="error-box">{err_msg}</div>
"""
            html_content += """
            </div>
          </div>
"""
        html_content += """
        </div>
      </section>
"""

    html_content += """
    </div>
  </div>

  <script>
    let currentCategory = 'all';

    function switchView(viewName) {
      const matrix = document.getElementById('viewMatrix');
      const grid = document.getElementById('viewGrid');
      const btnMatrix = document.getElementById('btnMatrixView');
      const btnGrid = document.getElementById('btnGridView');

      if (viewName === 'matrix') {
        matrix.classList.remove('hidden');
        grid.classList.add('hidden');
        btnMatrix.classList.add('active');
        btnGrid.classList.remove('active');
      } else {
        matrix.classList.add('hidden');
        grid.classList.remove('hidden');
        btnMatrix.classList.remove('active');
        btnGrid.classList.add('active');
      }
    }

    function setCategoryFilter(category) {
      currentCategory = category;
      document.querySelectorAll('.filter-btn').forEach(btn => {
        if (btn.getAttribute('data-filter') === category) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
      filterModels();
    }

    function filterModels() {
      const query = document.getElementById('modelSearch').value.toLowerCase().trim();

      // Filter Matrix Rows
      document.querySelectorAll('.matrix-row').forEach(row => {
        const cat = row.getAttribute('data-category');
        const title = row.getAttribute('data-title').toLowerCase();
        const matchesCategory = (currentCategory === 'all' || cat === currentCategory);
        const matchesQuery = (!query || title.includes(query));
        if (matchesCategory && matchesQuery) {
          row.style.display = '';
        } else {
          row.style.display = 'none';
        }
      });

      // Filter Cards
      document.querySelectorAll('.card').forEach(card => {
        const cat = card.getAttribute('data-category');
        const title = card.getAttribute('data-title').toLowerCase();
        const matchesCategory = (currentCategory === 'all' || cat === currentCategory);
        const matchesQuery = (!query || title.includes(query));
        if (matchesCategory && matchesQuery) {
          card.style.display = '';
        } else {
          card.style.display = 'none';
        }
      });
    }

    // Auto-pause previous audio when a new audio starts playing
    document.addEventListener('play', function(e) {
      const audios = document.querySelectorAll('audio');
      for (let i = 0; i < audios.length; i++) {
        if (audios[i] !== e.target) {
          audios[i].pause();
        }
      }
    }, true);
  </script>
</body>
</html>
"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return html_path


def generate_markdown_report(manifest: Dict[str, Any], output_dir: Path) -> Path:
    """Generates a clean Markdown report with a side-by-side comparison matrix."""
    md_path = output_dir / "report.md"

    samples = manifest.get("samples", [])
    results = manifest.get("results", [])

    lines = [
        "# Gujarati TTS Model Comparison Report",
        "",
        f"**Generated:** {manifest.get('generated_at')}",
        f"**Total Audio Files Generated:** {len(results)}",
        f"**Models Tested:** {len(TTS_MODELS_REGISTRY)}",
        "",
        "## Evaluated Test Samples",
        "",
    ]

    for s in samples:
        lines.append(f"- **ID:** `{s['id']}`")
        if s.get("category"):
            lines.append(f"  - **Description:** {s['category']}")
        lines.append(f"  - **Text:** `{s['text']}`")
        lines.append("")

    lines.extend([
        "## Model & Flavor Summary Matrix",
        "",
        "| Sample | Model | Flavor / Config | Type | Duration | Latency | Audio File | Status |",
        "| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :---: |",
    ])

    for r in results:
        sample_id = r["sample_id"]
        model = r["model"]
        flavor = r["flavor"]
        category = r["category"].capitalize()
        dur = f"{r.get('duration_seconds', 0.0):.2f}s" if r.get('duration_seconds') else "-"
        lat = f"{r.get('inference_time_ms', 0):.0f}ms" if r.get('inference_time_ms') else "-"
        rel_path = f"[`{r.get('relative_audio_path')}`]({r.get('relative_audio_path')})" if r.get("relative_audio_path") else "-"
        status = "✅ Success" if r.get("success") else f"❌ {r.get('error', 'Failed')}"
        lines.append(f"| `{sample_id}` | {model} | {flavor} | {category} | {dur} | {lat} | {rel_path} | {status} |")

    lines.extend([
        "",
        "## Output Folder Structure",
        "",
        "```",
        f"{output_dir.name}/",
    ])

    for model_id in TTS_MODELS_REGISTRY:
        lines.append(f"├── {model_id}/")
        sample_files = [r for r in results if r["model"] == model_id]
        for sf in sample_files[:4]:
            fn = Path(sf.get("relative_audio_path", "")).name
            if fn:
                lines.append(f"│     ├── {fn}")
        if len(sample_files) > 4:
            lines.append(f"│     └── ... ({len(sample_files)} total files)")

    lines.extend([
        "├── manifest.json",
        "├── report.md",
        "└── index.html",
        "```",
        "",
        "Open `index.html` in your web browser to listen to all audio files interactively.",
        "",
    ])

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return md_path


def run_comparison(
    input_path: Path,
    output_dir: Path,
    selected_models: Optional[List[str]] = None,
    offline_only: bool = False,
    online_only: bool = False,
    speed: float = 1.0,
    hf_token: Optional[str] = None,
    skip_existing: bool = False,
) -> Dict[str, Any]:
    """Runs the full model comparison workflow."""
    print("=" * 70)
    print("🚀 GUJARATI TTS FULL MODEL COMPARISON WORKFLOW")
    print("=" * 70)

    # 1. Load samples
    samples = load_input_samples(input_path)
    print(f"📖 Loaded {len(samples)} input sample(s) from {input_path}")
    for idx, s in enumerate(samples, 1):
        print(f"   [{idx}] ({s['id']}): {s['text']}")

    # 2. Initialize TTS Service
    print("\n📦 Initializing Unified TTS Service...")
    tts_service = TTSService()

    # 3. Filter models
    target_registry = {}
    for model_id, model_cfg in TTS_MODELS_REGISTRY.items():
        if selected_models and model_id not in selected_models:
            continue
        if offline_only and model_cfg["category"] != "offline":
            continue
        if online_only and model_cfg["category"] != "online":
            continue
        target_registry[model_id] = model_cfg

    print(f"🔍 Evaluated models ({len(target_registry)}): {list(target_registry.keys())}\n")

    # 4. Create base output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []

    # 5. Process each sample
    for sample in samples:
        sample_id = sample["id"]
        sample_text = sample["text"]
        print(f"\n▶️ Processing Sample: '{sample_id}'")
        print(f"   Text: {sample_text}")

        for model_id, model_info in target_registry.items():
            model_engine = model_info["engine"]
            model_name = model_info["name"]
            category = model_info["category"]
            flavors = model_info["flavors"]

            # Model dedicated directory: output/{output_dir}/{model_id}/
            model_dir = output_dir / model_id
            model_dir.mkdir(parents=True, exist_ok=True)

            print(f"\n   ⚙️  Model: [{model_id}] ({category.upper()}) - {len(flavors)} flavor(s)")

            for flavor_info in flavors:
                flavor_id = flavor_info["flavor"]
                flavor_name = flavor_info["name"]
                flavor_params = flavor_info.get("params", {})

                # Filename pattern: {sample_id}_{flavor_id}.wav
                filename = f"{sample_id}_{flavor_id}.wav"
                audio_file_path = model_dir / filename
                rel_audio_path = f"{model_id}/{filename}"

                print(f"      • Flavor: '{flavor_id}' ({flavor_name})...", end=" ", flush=True)

                start_t = time.time()
                result_entry = {
                    "sample_id": sample_id,
                    "sample_text": sample_text,
                    "model": model_id,
                    "model_name": model_name,
                    "flavor": flavor_id,
                    "flavor_name": flavor_name,
                    "category": category,
                    "relative_audio_path": rel_audio_path,
                    "absolute_audio_path": str(audio_file_path),
                    "success": False,
                    "error": None,
                    "duration_seconds": None,
                    "inference_time_ms": None,
                    "sample_rate": None,
                    "is_mock": False,
                    "is_fallback": False,
                }

                if skip_existing and audio_file_path.exists() and audio_file_path.stat().st_size > 100:
                    dur_val = None
                    sr_val = None
                    try:
                        import wave
                        with wave.open(str(audio_file_path), "rb") as wf:
                            dur_val = round(wf.getnframes() / float(wf.getframerate()), 2)
                            sr_val = wf.getframerate()
                    except Exception:
                        pass
                    result_entry["success"] = True
                    result_entry["duration_seconds"] = dur_val
                    result_entry["sample_rate"] = sr_val
                    result_entry["inference_time_ms"] = 0.0
                    print(f"SKIPPED (Already exists: {dur_val or 'WAV'}s) -> {rel_audio_path}")
                    results.append(result_entry)
                    continue

                try:
                    kwargs = dict(flavor_params)
                    kwargs["speed"] = speed
                    if hf_token:
                        kwargs["hf_token"] = hf_token

                    res = tts_service.synthesize(
                        engine=model_engine,
                        text=sample_text,
                        **kwargs
                    )

                    elapsed_ms = round((time.time() - start_t) * 1000, 2)
                    result_entry["inference_time_ms"] = elapsed_ms

                    if res and res.get("audio_base64"):
                        wav_bytes = base64.b64decode(res["audio_base64"])
                        with open(audio_file_path, "wb") as af:
                            af.write(wav_bytes)

                        result_entry["success"] = True
                        result_entry["duration_seconds"] = res.get("duration_seconds")
                        result_entry["sample_rate"] = res.get("sample_rate")
                        result_entry["is_mock"] = bool(res.get("is_mock"))
                        result_entry["is_fallback"] = bool(res.get("method") in ["local_neural_fallback", "formant_synthesis", "local_fallback"])

                        dur_disp = f"{res.get('duration_seconds')}s" if res.get('duration_seconds') else "WAV"
                        print(f"DONE ({dur_disp}, {elapsed_ms}ms) -> {rel_audio_path}")
                    else:
                        err_msg = res.get("error") or res.get("message") or "No audio returned"
                        result_entry["error"] = err_msg
                        print(f"FAILED: {err_msg}")

                except Exception as e:
                    elapsed_ms = round((time.time() - start_t) * 1000, 2)
                    result_entry["inference_time_ms"] = elapsed_ms
                    result_entry["error"] = str(e)
                    print(f"ERROR: {str(e)[:80]}")

                results.append(result_entry)

    # 6. Build Manifest
    manifest = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "input_path": str(input_path),
        "output_dir": str(output_dir),
        "samples": samples,
        "results": results,
    }

    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"\n📄 Saved JSON Manifest: {manifest_path}")

    # 7. Build Markdown Report
    report_path = generate_markdown_report(manifest, output_dir)
    print(f"📊 Saved Markdown Report: {report_path}")

    # 8. Build Interactive HTML Dashboard
    html_path = generate_html_player(manifest, output_dir)
    print(f"🎧 Saved Interactive HTML Player: {html_path}")

    print("\n" + "=" * 70)
    print("✅ COMPARISON RUN COMPLETE!")
    print(f"📁 Output Folder: {output_dir}")
    print("=" * 70)

    return manifest


def main():
    parser = argparse.ArgumentParser(
        description="Compare all offline and online TTS models and flavors for Gujarati text."
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=str(REPO_ROOT / "resources" / "tts_samples" / "sample_test.json"),
        help="Path to JSON file with Gujarati input texts.",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default=str(REPO_ROOT / "output" / "tts_comparison"),
        help="Directory to save model-wise audio folders and reports.",
    )
    parser.add_argument(
        "--models", "-m",
        type=str,
        default=None,
        help="Comma-separated list of models to evaluate (e.g. mms_tts,piper_tts,espeak_ng).",
    )
    parser.add_argument(
        "--offline-only",
        action="store_true",
        help="Run only offline models (MMS, Piper, eSpeak-NG).",
    )
    parser.add_argument(
        "--online-only",
        action="store_true",
        help="Run only online models (Indic-TTS, IndicF5, Parler-TTS, Google, Bhashini).",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Speech speed factor (default: 1.0).",
    )
    parser.add_argument(
        "--hf-token",
        type=str,
        default=os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN"),
        help="HuggingFace token for gated spaces/models.",
    )

    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip re-synthesizing if the target audio file already exists on disk.",
    )

    args = parser.parse_args()

    selected_models = None
    if args.models:
        selected_models = [m.strip() for m in args.models.split(",") if m.strip()]

    run_comparison(
        input_path=Path(args.input),
        output_dir=Path(args.output_dir),
        selected_models=selected_models,
        offline_only=args.offline_only,
        online_only=args.online_only,
        speed=args.speed,
        hf_token=args.hf_token,
        skip_existing=args.skip_existing,
    )


if __name__ == "__main__":
    main()
