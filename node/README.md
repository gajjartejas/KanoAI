# Gujarati Language Resource Generator (Node.js)

A Node.js tool to generate static SVG glyphs, interpolated Jodakshar stroke SVGs, CSV tables, and synthesized audio pronunciations for Gujarati **Kakko** (consonants), **Barakhadi** (syllables), **Jodakshar** (conjuncts), and **Numerals** (0–9).

---

## 📁 Directory Layout

```
node/
├── package.json            # Dependencies (harfbuzzjs, text-to-svg, svg-path-properties, node-fetch)
├── package-lock.json       # Locked dependency versions
├── index.js                # Generation entrypoint
├── harfbuzzSvg.js          # HarfBuzz OpenType shaping + SVG path renderer
├── jodaksharInterpolate.js # Interpolate stroke matching/transfer for conjuncts
├── svgGeometry.js          # Affine transform, Bézier path transform, polygon containment
├── jodakshar.test.js       # Node unit & asset validation tests (`npm test`)
└── README.md               # Documentation and usage instructions
```

---

## ⚙️ Installation

Navigate to the `node/` directory and install dependencies:

```bash
cd node
npm install
```

---

## 🚀 Usage

Run the generator to produce SVGs and CSVs in `resources/`:

```bash
# Run directly with Node.js
node index.js

# Or from repository root
node node/index.js

# Run validation tests
npm test
```

### Outputs Generated in `resources/`:
- **Kakko (Consonants)**:
  - `resources/kakko/svgs/`: 45 vector SVGs (e.g. `1_ka.svg`, `2_kha.svg`)
  - `resources/kakko/kakko.csv`: Gujarati characters mapped to English transliteration
- **Barakhadi (Syllables)**:
  - `resources/barakhdi/svgs/`: Complete 500+ syllable SVGs across all consonant classes
  - `resources/barakhdi/barakhdi.csv`: Grid matrix of all consonant + vowel combinations
- **Jodakshar (Conjuncts)**:
  - `resources/jodakshar/svgs/`: 62 HarfBuzz-shaped combined vector SVGs (e.g. `1_kra.svg`, `4_sva.svg`)
  - `resources/jodakshar/svgs-interpolate/`: Shaped outlines (`g0p0`) paired with matching interpolated `g0sN` strokes from `interpolate-svg`
  - `resources/jodakshar/jodakshar.csv`: Conjunct metadata, components, patterns, and example words/sentences
- **Numerals (0–100)**:
  - `resources/numerals/svgs/`: Standard numeral SVGs (`0.svg`, `1.svg`, ..., `100.svg`)
  - `resources/numerals/numerals.csv`: Transliteration and English/Gujarati numeral names

---

## 🎙️ Audio Generation (Optional)

`index.js` includes functions to fetch synthesized Gujarati speech (Wavenet) from Google Text-to-Speech:
- `generateBarakhadiAudio()`: Generates MP3 audio for each syllable
- `generateKakkoAudio()`: Generates MP3 audio for consonants
- `generateJodaksharAudio()`: Generates MP3 audio for conjuncts
- `generateNumeralsAudio()`: Generates MP3 audio for numbers

To generate audio files, invoke `generateAudio()` inside `index.js`.
