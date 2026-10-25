import { Point, Stroke, Strokes, BoundingBox } from '../types/handwriting';

export const POINTS_PER_STROKE = 32;

/**
 * Calculates bounding box for a collection of strokes.
 */
export function getStrokesBoundingBox(strokes: Strokes): BoundingBox {
  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;

  let hasPoints = false;
  for (const stroke of strokes) {
    for (const p of stroke) {
      hasPoints = true;
      if (p.x < minX) minX = p.x;
      if (p.x > maxX) maxX = p.x;
      if (p.y < minY) minY = p.y;
      if (p.y > maxY) maxY = p.y;
    }
  }

  if (!hasPoints) {
    return { minX: 0, maxX: 0, minY: 0, maxY: 0, width: 0, height: 0 };
  }

  return {
    minX,
    maxX,
    minY,
    maxY,
    width: Math.max(1e-5, maxX - minX),
    height: Math.max(1e-5, maxY - minY),
  };
}

/**
 * Filters consecutive duplicate points or jitter within a stroke.
 */
export function filterStrokeJitter(stroke: Stroke, minDistance = 0.5): Stroke {
  if (stroke.length <= 1) return [...stroke];
  const cleaned: Stroke = [stroke[0]];

  for (let i = 1; i < stroke.length; i++) {
    const prev = cleaned[cleaned.length - 1];
    const curr = stroke[i];
    const dist = Math.hypot(curr.x - prev.x, curr.y - prev.y);
    if (dist >= minDistance || i === stroke.length - 1) {
      cleaned.push(curr);
    }
  }

  return cleaned;
}

/**
 * Calculates total cumulative path length of a stroke.
 */
export function getStrokePathLength(stroke: Stroke): number {
  let length = 0;
  for (let i = 1; i < stroke.length; i++) {
    length += Math.hypot(stroke[i].x - stroke[i - 1].x, stroke[i].y - stroke[i - 1].y);
  }
  return length;
}

/**
 * Resamples a single stroke to exactly `targetPoints` (default 32)
 * using linear interpolation along cumulative arc length.
 */
export function resampleStroke(stroke: Stroke, targetPoints = POINTS_PER_STROKE): Stroke {
  if (stroke.length === 0) return [];
  if (stroke.length === 1) {
    return Array.from({ length: targetPoints }, () => ({ ...stroke[0] }));
  }

  const totalLength = getStrokePathLength(stroke);
  if (totalLength < 1e-5) {
    // Zero length stroke (single tap)
    return Array.from({ length: targetPoints }, () => ({ ...stroke[0] }));
  }

  const interval = totalLength / (targetPoints - 1);
  const resampled: Stroke = [{ ...stroke[0] }];

  let currentDist = 0;
  let segIndex = 0;
  let segStartDist = 0;

  for (let i = 1; i < targetPoints - 1; i++) {
    const targetDist = i * interval;

    while (segIndex < stroke.length - 1) {
      const p1 = stroke[segIndex];
      const p2 = stroke[segIndex + 1];
      const segLen = Math.hypot(p2.x - p1.x, p2.y - p1.y);

      if (segStartDist + segLen >= targetDist) {
        const segProgress = segLen === 0 ? 0 : (targetDist - segStartDist) / segLen;
        resampled.push({
          x: p1.x + (p2.x - p1.x) * segProgress,
          y: p1.y + (p2.y - p1.y) * segProgress,
          t: p1.t !== undefined && p2.t !== undefined
            ? p1.t + (p2.t - p1.t) * segProgress
            : undefined,
        });
        break;
      }

      segStartDist += segLen;
      segIndex++;
    }
  }

  // Ensure last point matches exactly
  resampled.push({ ...stroke[stroke.length - 1] });
  return resampled;
}

/**
 * Full Normalization Pipeline:
 * 1. Removes empty strokes & jitter
 * 2. Translates to origin (0, 0)
 * 3. Scales uniformly to [0, 1] bounding box with aspect-ratio preservation
 * 4. Resamples each stroke to exactly 32 points
 */
export function normalizeStrokes(rawStrokes: Strokes, targetPoints = POINTS_PER_STROKE): Strokes {
  const rawBox = getStrokesBoundingBox(rawStrokes);
  const jitterDistance = Math.min(0.5, Math.max(rawBox.width, rawBox.height) * 0.005);
  const filteredStrokes = rawStrokes
    .map(s => filterStrokeJitter(s, jitterDistance))
    .filter(s => s.length > 0);

  if (filteredStrokes.length === 0) return [];

  const bbox = getStrokesBoundingBox(filteredStrokes);
  const maxDim = Math.max(bbox.width, bbox.height, 1e-4);

  // Center offset to place shape symmetrically in [0, 1]
  const offsetX = (maxDim - bbox.width) / 2;
  const offsetY = (maxDim - bbox.height) / 2;

  const normalized: Strokes = [];

  for (const stroke of filteredStrokes) {
    // Translate and scale
    const transformed: Stroke = stroke.map(p => ({
      x: (p.x - bbox.minX + offsetX) / maxDim,
      y: (p.y - bbox.minY + offsetY) / maxDim,
      t: p.t,
    }));

    // Resample to 32 points
    const resampled = resampleStroke(transformed, targetPoints);
    normalized.push(resampled);
  }

  return normalized;
}
