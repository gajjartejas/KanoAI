import * as fs from 'fs';
import * as path from 'path';
import { DOMParser } from '@xmldom/xmldom';
import { svgPathProperties } from 'svg-path-properties';

interface Point {
  x: number;
  y: number;
}

interface TemplateStroke {
  id: string;
  points: Point[];
  startPoint: Point;
  endPoint: Point;
  length: number;
}

interface CharacterTemplate {
  id: string;
  name: string;
  gujarati: string;
  transliteration: string;
  category: 'vowel' | 'consonant' | 'barakhadi' | 'number';
  strokeCount: number;
  strokes: TemplateStroke[];
  svgOutlinePath?: string;
  viewBox?: { width: number; height: number };
}

const KAKKO_GUJARATI_MAP: Record<string, { gujarati: string; name: string; trans: string }> = {
  // Vowels
  '0_aa': { gujarati: 'અ', name: 'A', trans: 'a' },
  '1_aa': { gujarati: 'આ', name: 'Aa', trans: 'aa' },
  '2_i': { gujarati: 'ઇ', name: 'I', trans: 'i' },
  '3_ee': { gujarati: 'ઈ', name: 'Ee', trans: 'ee' },
  '4_u': { gujarati: 'ઉ', name: 'U', trans: 'u' },
  '5_oo': { gujarati: 'ઊ', name: 'Oo', trans: 'oo' },
  '6_e': { gujarati: 'એ', name: 'E', trans: 'e' },
  '7_ai': { gujarati: 'ઐ', name: 'Ai', trans: 'ai' },
  '8_o': { gujarati: 'ઓ', name: 'O', trans: 'o' },
  '9_au': { gujarati: 'ઔ', name: 'Au', trans: 'au' },
  '10_am_or_an': { gujarati: 'અં', name: 'Am', trans: 'am' },
  '11_ah': { gujarati: 'અઃ', name: 'Ah', trans: 'ah' },

  // Consonants (Base 0_*.svg in each consonant folder)
  '1_k': { gujarati: 'ક', name: 'Ka', trans: 'ka' },
  '2_kh': { gujarati: 'ખ', name: 'Kha', trans: 'kha' },
  '3_g': { gujarati: 'ગ', name: 'Ga', trans: 'ga' },
  '4_gh': { gujarati: 'ઘ', name: 'Gha', trans: 'gha' },
  '5_ch': { gujarati: 'ચ', name: 'Cha', trans: 'cha' },
  '6_chha': { gujarati: 'છ', name: 'Chha', trans: 'chha' },
  '7_j': { gujarati: 'જ', name: 'Ja', trans: 'ja' },
  '8_jh': { gujarati: 'ઝ', name: 'Jha', trans: 'jha' },
  '9_t': { gujarati: 'ટ', name: 'Ta', trans: 'ta' },
  '10_th': { gujarati: 'ઠ', name: 'Tha', trans: 'tha' },
  '11_d': { gujarati: 'ડ', name: 'Da', trans: 'da' },
  '12_dh': { gujarati: 'ઢ', name: 'Dha', trans: 'dha' },
  '13_n': { gujarati: 'ણ', name: 'Ana', trans: 'na' },
  '14_t': { gujarati: 'ત', name: 'Ta', trans: 'ta' },
  '15_th': { gujarati: 'થ', name: 'Tha', trans: 'tha' },
  '16_d': { gujarati: 'દ', name: 'Da', trans: 'da' },
  '17_dh': { gujarati: 'ધ', name: 'Dha', trans: 'dha' },
  '18_n': { gujarati: 'ન', name: 'Na', trans: 'na' },
  '19_p': { gujarati: 'પ', name: 'Pa', trans: 'pa' },
  '20_f': { gujarati: 'ફ', name: 'Pha', trans: 'pha' },
  '21_b': { gujarati: 'બ', name: 'Ba', trans: 'ba' },
  '22_bh': { gujarati: 'ભ', name: 'Bha', trans: 'bha' },
  '23_m': { gujarati: 'મ', name: 'Ma', trans: 'ma' },
  '24_y': { gujarati: 'ય', name: 'Ya', trans: 'ya' },
  '25_r': { gujarati: 'ર', name: 'Ra', trans: 'ra' },
  '26_l': { gujarati: 'લ', name: 'La', trans: 'la' },
  '27_v': { gujarati: 'વ', name: 'Va', trans: 'va' },
  '28_sh': { gujarati: 'શ', name: 'Sha', trans: 'sha' },
  '29_sh': { gujarati: 'ષ', name: 'Ssha', trans: 'ssha' },
  '30_s': { gujarati: 'સ', name: 'Sa', trans: 'sa' },
  '31_h': { gujarati: 'હ', name: 'Ha', trans: 'ha' },
  '32_l': { gujarati: 'ળ', name: 'Ala', trans: 'la' },
  '33_x': { gujarati: 'ક્ષ', name: 'Ksha', trans: 'ksha' },
  '34_gy': { gujarati: 'જ્ઞ', name: 'Gnya', trans: 'gnya' },
};

const GUJARATI_NUMBERS = ['૦', '૧', '૨', '૩', '૪', '૫', '૬', '૭', '૮', '૯'];

const ASSETS_DIR = path.resolve(__dirname, '../../interpolate-svg/svgs');
const OUTPUT_DIR = path.resolve(__dirname, '../src/data');

function round4(val: number): number {
  return Math.round(val * 10000) / 10000;
}

type Matrix = [number, number, number, number, number, number];
const multiply = (a: Matrix, b: Matrix): Matrix => [
  a[0] * b[0] + a[2] * b[1], a[1] * b[0] + a[3] * b[1],
  a[0] * b[2] + a[2] * b[3], a[1] * b[2] + a[3] * b[3],
  a[0] * b[4] + a[2] * b[5] + a[4], a[1] * b[4] + a[3] * b[5] + a[5],
];

function transformPoint(point: Point, transform: string): Point {
  let matrix: Matrix = [1, 0, 0, 1, 0, 0];
  for (const operation of transform.matchAll(/(matrix|translate|scale|rotate)\s*\(([^)]*)\)/g)) {
    const values = operation[2].split(/[\s,]+/).filter(Boolean).map(Number);
    let next: Matrix;
    if (operation[1] === 'matrix') next = values as Matrix;
    else if (operation[1] === 'translate') next = [1, 0, 0, 1, values[0] || 0, values[1] || 0];
    else if (operation[1] === 'scale') next = [values[0], 0, 0, values[1] ?? values[0], 0, 0];
    else {
      const angle = values[0] * Math.PI / 180;
      const rotation: Matrix = [Math.cos(angle), Math.sin(angle), -Math.sin(angle), Math.cos(angle), 0, 0];
      const x = values[1] || 0;
      const y = values[2] || 0;
      next = multiply(multiply([1, 0, 0, 1, x, y], rotation), [1, 0, 0, 1, -x, -y]);
    }
    matrix = multiply(matrix, next);
  }
  return {
    x: matrix[0] * point.x + matrix[2] * point.y + matrix[4],
    y: matrix[1] * point.x + matrix[3] * point.y + matrix[5],
  };
}

function resamplePoints(rawPoints: Point[], targetCount = 32): Point[] {
  if (rawPoints.length === 0) return [];
  if (rawPoints.length === 1) {
    return Array.from({ length: targetCount }, () => ({ ...rawPoints[0] }));
  }

  // Calculate arc lengths
  const cumLengths: number[] = [0];
  for (let i = 1; i < rawPoints.length; i++) {
    const d = Math.hypot(rawPoints[i].x - rawPoints[i - 1].x, rawPoints[i].y - rawPoints[i - 1].y);
    cumLengths.push(cumLengths[i - 1] + d);
  }

  const totalLength = cumLengths[cumLengths.length - 1];
  if (totalLength < 1e-5) {
    return Array.from({ length: targetCount }, () => ({ ...rawPoints[0] }));
  }

  const interval = totalLength / (targetCount - 1);
  const resampled: Point[] = [{ ...rawPoints[0] }];

  let segIdx = 0;
  for (let i = 1; i < targetCount - 1; i++) {
    const targetDist = i * interval;
    while (segIdx < rawPoints.length - 1 && cumLengths[segIdx + 1] < targetDist) {
      segIdx++;
    }

    const segStartDist = cumLengths[segIdx];
    const segEndDist = cumLengths[segIdx + 1];
    const segLen = segEndDist - segStartDist;
    const progress = segLen === 0 ? 0 : (targetDist - segStartDist) / segLen;

    const p1 = rawPoints[segIdx];
    const p2 = rawPoints[segIdx + 1];
    resampled.push({
      x: p1.x + (p2.x - p1.x) * progress,
      y: p1.y + (p2.y - p1.y) * progress,
    });
  }

  resampled.push({ ...rawPoints[rawPoints.length - 1] });
  return resampled;
}

function parseSvgFile(filePath: string): {
  strokes: Array<{ id: string; rawPoints: Point[]; length: number }>;
  outlinePath?: string;
  width: number;
  height: number;
} | null {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    const doc = new DOMParser().parseFromString(content, 'text/xml');
    const svgEl = doc.getElementsByTagName('svg')[0];
    if (!svgEl) return null;

    const width = parseFloat(svgEl.getAttribute('width') || '100');
    const height = parseFloat(svgEl.getAttribute('height') || '100');

    const paths = doc.getElementsByTagName('path');
    const strokeList: Array<{ id: string; rawPoints: Point[]; length: number }> = [];
    let outlinePath: string | undefined;

    for (let i = 0; i < paths.length; i++) {
      const p = paths[i];
      const label = p.getAttribute('inkscape:label') || p.getAttribute('id') || '';
      const d = p.getAttribute('d') || '';

      if (!d) continue;

      if (label.includes('p0') || label.endsWith('p0') || (!label && !outlinePath)) {
        outlinePath = d;
      }

      if (label.includes('s') || label.startsWith('g0s')) {
        try {
          const props = new svgPathProperties(d);
          const totalLen = props.getTotalLength();
          if (totalLen <= 0) continue;

          // Sample 64 points along path
          const sampleCount = 64;
          const rawPts: Point[] = [];
          for (let s = 0; s < sampleCount; s++) {
            const pt = props.getPointAtLength((s / (sampleCount - 1)) * totalLen);
            let transformed: Point = { x: pt.x, y: pt.y };
            let ancestor = p.parentNode as Element | null;
            while (ancestor && ancestor.tagName !== 'svg') {
              const transform = ancestor.getAttribute?.('transform');
              if (transform) transformed = transformPoint(transformed, transform);
              ancestor = ancestor.parentNode as Element | null;
            }
            rawPts.push(transformed);
          }

          strokeList.push({
            id: label,
            rawPoints: rawPts,
            length: rawPts.reduce((sum, pt, index) =>
              index ? sum + Math.hypot(pt.x - rawPts[index - 1].x, pt.y - rawPts[index - 1].y) : sum, 0),
          });
        } catch {
          // ignore parsing error for invalid path
        }
      }
    }

    // Sort strokes by label (s0, s1, s2...) to preserve stroke order
    strokeList.sort((a, b) => a.id.localeCompare(b.id, undefined, { numeric: true }));

    return { strokes: strokeList, outlinePath, width, height };
  } catch {
    return null;
  }
}

function normalizeAndBuildTemplate(
  id: string,
  name: string,
  gujarati: string,
  transliteration: string,
  category: 'vowel' | 'consonant' | 'barakhadi' | 'number',
  parsed: ReturnType<typeof parseSvgFile>
): CharacterTemplate | null {
  if (!parsed || parsed.strokes.length === 0) return null;

  // Calculate bounding box over all raw strokes
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const s of parsed.strokes) {
    for (const p of s.rawPoints) {
      if (p.x < minX) minX = p.x;
      if (p.x > maxX) maxX = p.x;
      if (p.y < minY) minY = p.y;
      if (p.y > maxY) maxY = p.y;
    }
  }

  const width = Math.max(1e-4, maxX - minX);
  const height = Math.max(1e-4, maxY - minY);
  const maxDim = Math.max(width, height);
  const offsetX = (maxDim - width) / 2;
  const offsetY = (maxDim - height) / 2;

  const normalizedStrokes: TemplateStroke[] = parsed.strokes.map(s => {
    // 1. Scale & center to [0, 1]
    const scaled = s.rawPoints.map(p => ({
      x: (p.x - minX + offsetX) / maxDim,
      y: (p.y - minY + offsetY) / maxDim,
    }));

    // 2. Resample to 32 points
    const resampled = resampleStroke(scaled, 32);

    return {
      id: s.id,
      points: resampled.map(p => ({ x: round4(p.x), y: round4(p.y) })),
      startPoint: { x: round4(resampled[0].x), y: round4(resampled[0].y) },
      endPoint: { x: round4(resampled[resampled.length - 1].x), y: round4(resampled[resampled.length - 1].y) },
      length: round4(s.length / maxDim),
    };
  });

  return {
    id,
    name,
    gujarati,
    transliteration,
    category,
    strokeCount: normalizedStrokes.length,
    strokes: normalizedStrokes,
    svgOutlinePath: parsed.outlinePath,
    viewBox: { width: parsed.width, height: parsed.height },
  };
}

function resampleStroke(stroke: Point[], targetPoints = 32): Point[] {
  return resamplePoints(stroke, targetPoints);
}

async function extractAll() {
  console.log('Starting Gujarati Character Template Extraction...');
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  const templates: CharacterTemplate[] = [];

  // 1. Vowels from barakhadi/0_aa/
  const vowelsDir = path.join(ASSETS_DIR, 'barakhadi/0_aa');
  if (fs.existsSync(vowelsDir)) {
    const files = fs.readdirSync(vowelsDir).filter(f => f.endsWith('.svg'));
    for (const f of files) {
      const baseName = f.replace('.svg', '');
      const meta = KAKKO_GUJARATI_MAP[baseName] || {
        gujarati: baseName,
        name: baseName,
        trans: baseName,
      };

      const parsed = parseSvgFile(path.join(vowelsDir, f));
      const tmpl = normalizeAndBuildTemplate(
        `vowel_${baseName}`,
        meta.name,
        meta.gujarati,
        meta.trans,
        'vowel',
        parsed
      );
      if (tmpl) templates.push(tmpl);
    }
  }

  // 2. Consonants from barakhadi/1_k ... 34_gy
  for (let i = 1; i <= 34; i++) {
    const dirEntries = fs.readdirSync(path.join(ASSETS_DIR, 'barakhadi')).filter(d => d.startsWith(`${i}_`));
    for (const folderName of dirEntries) {
      const folderPath = path.join(ASSETS_DIR, 'barakhadi', folderName);
      if (!fs.statSync(folderPath).isDirectory()) continue;

      const meta = KAKKO_GUJARATI_MAP[folderName] || {
        gujarati: folderName,
        name: folderName,
        trans: folderName,
      };

      // Base consonant: 0_*.svg (e.g. 0_k.svg)
      const svgFiles = fs.readdirSync(folderPath).filter(f => f.endsWith('.svg'));
      const baseSvg = svgFiles.find(f => f.startsWith('0_'));
      if (baseSvg) {
        const parsed = parseSvgFile(path.join(folderPath, baseSvg));
        const tmpl = normalizeAndBuildTemplate(
          `consonant_${folderName}`,
          meta.name,
          meta.gujarati,
          meta.trans,
          'consonant',
          parsed
        );
        if (tmpl) templates.push(tmpl);
      }

      // Barakhadi forms (1_*.svg to 11_*.svg)
      for (const bSvg of svgFiles) {
        if (bSvg.startsWith('0_')) continue;
        const bBase = bSvg.replace('.svg', '');
        const parsed = parseSvgFile(path.join(folderPath, bSvg));
        const tmpl = normalizeAndBuildTemplate(
          `barakhadi_${folderName}_${bBase}`,
          `${meta.name}-${bBase}`,
          meta.gujarati,
          `${meta.trans}-${bBase}`,
          'barakhadi',
          parsed
        );
        if (tmpl) templates.push(tmpl);
      }
    }
  }

  // 3. Numbers from numbers/
  const numbersDir = path.join(ASSETS_DIR, 'numbers');
  if (fs.existsSync(numbersDir)) {
    // All numerals available to the mobile learning chart (0 through 100).
    for (let i = 0; i <= 100; i++) {
      const file = `${i}_num.svg`;
      const filePath = path.join(numbersDir, file);
      if (fs.existsSync(filePath)) {
        const parsed = parseSvgFile(filePath);
        const tmpl = normalizeAndBuildTemplate(
          `number_${i}`,
          `Number ${i}`,
          GUJARATI_NUMBERS[i] || `${i}`,
          `${i}`,
          'number',
          parsed
        );
        if (tmpl) templates.push(tmpl);
      }
    }

  }

  console.log(`Extracted ${templates.length} character templates.`);
  const outputPath = path.join(OUTPUT_DIR, 'templates.json');
  fs.writeFileSync(outputPath, JSON.stringify(templates));
  const fileSizeKb = (fs.statSync(outputPath).size / 1024).toFixed(1);
  console.log(`Saved templates to ${outputPath} (${fileSizeKb} KB).`);
}

extractAll().catch(err => {
  console.error('Extraction error:', err);
  process.exit(1);
});
