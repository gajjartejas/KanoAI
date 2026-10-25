import { Point, Stroke, TemplateStroke } from '../types/handwriting';
import { resampleStroke } from './normalizer';

const GUIDE_PADDING = 24;
const SAMPLE_COUNT = 32;

const distance = (a: Point, b: Point) => Math.hypot(a.x - b.x, a.y - b.y);

const length = (points: Stroke) => points.reduce(
  (total, point, index) => index ? total + distance(points[index - 1], point) : total,
  0,
);

/** Validate against the guide in canvas coordinates before advancing its stroke hint. */
export const evaluateGuidedTrace = (
  drawn: Stroke,
  guide: TemplateStroke,
  canvasSize: number,
): boolean => {
  if (drawn.length < 2 || !guide.points.length) return false;
  const drawable = canvasSize - GUIDE_PADDING * 2;
  const expected = guide.points.map(point => ({
    x: GUIDE_PADDING + point.x * drawable,
    y: GUIDE_PADDING + point.y * drawable,
  }));
  const user = resampleStroke(drawn, SAMPLE_COUNT);
  const expectedLength = length(expected);
  if (expectedLength <= 0 || length(drawn) < expectedLength * 0.42 || length(drawn) > expectedLength * 1.7) return false;
  if (distance(user[0], expected[0]) > canvasSize * 0.1) return false;
  if (distance(user[user.length - 1], expected[expected.length - 1]) > canvasSize * 0.12) return false;
  let forward = 0;
  let reverse = 0;
  let covered = 0;
  let nearGuide = 0;
  let totalError = 0;
  let directionAgreement = 0;
  let directionSamples = 0;
  for (let index = 0; index < expected.length; index++) {
    forward += distance(user[index], expected[index]);
    reverse += distance(user[index], expected[expected.length - 1 - index]);
    const guideDistance = Math.min(...user.map(point => distance(point, expected[index])));
    const userDistance = Math.min(...expected.map(point => distance(point, user[index])));
    if (guideDistance <= canvasSize * 0.105) covered++;
    if (userDistance <= canvasSize * 0.105) nearGuide++;
    totalError += (guideDistance + userDistance) / 2;
    if (index > 0) {
      const ux = user[index].x - user[index - 1].x;
      const uy = user[index].y - user[index - 1].y;
      const ex = expected[index].x - expected[index - 1].x;
      const ey = expected[index].y - expected[index - 1].y;
      const magnitude = Math.hypot(ux, uy) * Math.hypot(ex, ey);
      if (magnitude > 0.0001) {
        directionAgreement += (ux * ex + uy * ey) / magnitude;
        directionSamples++;
      }
    }
  }
  return reverse + canvasSize * 0.02 >= forward &&
    (directionSamples === 0 || directionAgreement / directionSamples >= -0.15) &&
    Math.min(covered, nearGuide) / expected.length >= 0.78 &&
    totalError / expected.length / canvasSize <= 0.065;
};
