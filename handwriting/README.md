# ✍️ KanoAI: Real-Time Gujarati Handwriting Recognition Suite

An offline Gujarati handwriting prototype with guided stroke evaluation and freehand template matching. The current fallback compares rasterized drawings with template rasters; it does not run a trained CNN or TFLite model. Validate accuracy and latency on representative Android and iOS devices before using freehand results to award learning progress.

[![Handwriting Recognition & Practice Suite Preview](../docs/assets/preview-handwriting.png)](https://gajjartejas.github.io/KanoAI/handwriting/)

---

## 🌟 Interactive Features

1. **✍️ Guided Practice (`GuidedPracticeScreen`)**:
   - Step-by-step Gujarati character tracing with dynamic SVG overlays.
   - Real-time animated directional hints with sequence bubbles (①, ②, ③).
   - Instant stroke-by-stroke accuracy evaluation with granular feedback in both Gujarati and English.
   - Replay modal and printable SVG/HTML worksheet generator.

2. **🎬 Animated Player (`AnimatedDrawingScreen`)**:
   - Progressive stroke-by-stroke animated visualization of 521 unique SVG templates (567 learning entries include repeated forms).
   - Playback speed adjustment, step navigation, and stroke order verification.
   - High-fidelity Kano audio pronunciation integration.

3. **🎮 Quiz Game (`QuizGameScreen`)**:
   - Gamified vocabulary challenges associating characters with Gujarati words and illustrations.
   - Interactive drawing canvas requiring correct stroke formation to score points and build streaks.
   - Auditory reinforcement and celebratory feedback.

4. **🔍 Free Drawing & Recognition (`FreeDrawingScreen`)**:
   - Unconstrained handwriting canvas supporting multi-stroke characters.
   - DTW template matching with raster similarity fallback. The CNN utilities are experimental and are not wired into the recognizer.
   - Real-time top-3 predictions with confidence metrics and stroke diagnostics.

5. **⚡ Benchmark Suite (`BenchmarkScreen`)**:
   - Automated testing suite verifying inference latency and accuracy across character sets.
   - Local profiling tools for DTW and raster similarity. Their timings are not a device performance guarantee.

---

## 📁 Workspace Structure

```
handwriting/
├── src/
│   ├── components/       # UI Components (Canvas, Overlay, ScoreCard, Diagnostics, Replay, Worksheet)
│   ├── data/             # Character templates (521 SVG guides), word associations, catalog
│   ├── engine/           # Deterministic DTW, normalizer, direction matcher, scoring, feedback
│   ├── ml/               # Raster similarity fallback, experimental CNN utilities and weights
│   ├── screens/          # GuidedPractice, AnimatedDrawing, QuizGame, FreeDrawing, Benchmark
│   ├── types/            # TypeScript interfaces (Point, Stroke, CharacterTemplate, etc.)
│   └── utils/            # Audio & Web Speech synthesis integration
├── scripts/
│   ├── extract-templates.ts  # Extracts stroke templates from interpolate-svg/svgs
│   ├── generate_model.ts     # Generates Tiny CNN weights from character raster signatures
│   └── train_export_model.py # Optional Python PyTorch/TFLite export pipeline
├── __tests__/            # 7 Jest test suites (30 tests)
├── App.tsx               # Main 5-tab application controller
├── app.json              # Expo configuration with GitHub Pages baseUrl
├── package.json          # Dependencies, scripts, and build targets
└── tsconfig.json         # TypeScript configuration
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Run Automated Unit Tests
```bash
npm test
```
Runs the Jest suites covering normalization, DTW, direction vectors, scoring, guided tracing, CNN utility functions, quiz logic, and hybrid recognizer.

### 3. Launch Development Server
```bash
npm run web
```
Launches Metro bundler in web mode at `http://localhost:8081`.

### 4. Build for GitHub Pages
```bash
npm run build:web
```
Exports the optimized web bundle directly to `../docs/handwriting`.

### 5. Re-generate Templates & ML Weights
```bash
# Re-extract vector stroke templates from ../interpolate-svg/svgs
npm run extract-templates

# Re-generate Tiny CNN model weights
npm run generate-model
```
