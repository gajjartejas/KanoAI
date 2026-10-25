import {
  normalizeStrokes,
  resampleStroke,
  getStrokesBoundingBox,
  filterStrokeJitter,
  POINTS_PER_STROKE,
} from '../src/engine/normalizer';
import { Strokes, Stroke } from '../src/types/handwriting';

describe('Vector Normalization Pipeline', () => {
  test('POINTS_PER_STROKE is exactly 32 as per PRD spec', () => {
    expect(POINTS_PER_STROKE).toBe(32);
  });

  test('resampleStroke resamples arbitrary stroke into exactly 32 points', () => {
    // 5-point raw stroke
    const raw: Stroke = [
      { x: 0, y: 0 },
      { x: 10, y: 10 },
      { x: 20, y: 30 },
      { x: 40, y: 50 },
      { x: 100, y: 100 },
    ];

    const resampled = resampleStroke(raw, 32);
    expect(resampled.length).toBe(32);
    // Start and end points must match
    expect(resampled[0].x).toBeCloseTo(0);
    expect(resampled[0].y).toBeCloseTo(0);
    expect(resampled[31].x).toBeCloseTo(100);
    expect(resampled[31].y).toBeCloseTo(100);
  });

  test('getStrokesBoundingBox computes correct bounding coordinates', () => {
    const strokes: Strokes = [
      [
        { x: 10, y: 20 },
        { x: 50, y: 80 },
      ],
      [
        { x: 5, y: 30 },
        { x: 60, y: 90 },
      ],
    ];

    const bbox = getStrokesBoundingBox(strokes);
    expect(bbox.minX).toBe(5);
    expect(bbox.maxX).toBe(60);
    expect(bbox.minY).toBe(20);
    expect(bbox.maxY).toBe(90);
    expect(bbox.width).toBe(55);
    expect(bbox.height).toBe(70);
  });

  test('filterStrokeJitter removes consecutive points closer than minDistance', () => {
    const noisy: Stroke = [
      { x: 0, y: 0 },
      { x: 0.1, y: 0.1 }, // jitter
      { x: 0.2, y: 0.1 }, // jitter
      { x: 10, y: 10 },
    ];

    const filtered = filterStrokeJitter(noisy, 0.5);
    expect(filtered.length).toBe(2);
    expect(filtered[0]).toEqual({ x: 0, y: 0 });
    expect(filtered[1]).toEqual({ x: 10, y: 10 });
  });

  test('normalizeStrokes scales and translates strokes to [0, 1] unit square', () => {
    const raw: Strokes = [
      [
        { x: 100, y: 200 },
        { x: 200, y: 200 },
        { x: 300, y: 400 },
      ],
    ];

    const norm = normalizeStrokes(raw);
    expect(norm.length).toBe(1);
    expect(norm[0].length).toBe(32);

    for (const pt of norm[0]) {
      expect(pt.x).toBeGreaterThanOrEqual(0);
      expect(pt.x).toBeLessThanOrEqual(1.0001);
      expect(pt.y).toBeGreaterThanOrEqual(0);
      expect(pt.y).toBeLessThanOrEqual(1.0001);
    }
  });

  test('normalizing an already unit-scaled drawing preserves its curve', () => {
    const unitStroke: Stroke = Array.from({ length: 32 }, (_, index) => ({
      x: index / 31,
      y: Math.sin(index / 31 * Math.PI) * 0.4,
    }));
    const normalized = normalizeStrokes([unitStroke])[0];
    expect(normalized[16].y).toBeGreaterThan(0.35);
    expect(normalized[16].x).toBeGreaterThan(0.45);
    expect(normalized[16].x).toBeLessThan(0.6);
  });
});
