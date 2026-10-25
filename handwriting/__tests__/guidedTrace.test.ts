import { evaluateGuidedTrace } from '../src/engine/guidedTrace';
import { TemplateStroke } from '../src/types/handwriting';

const guide: TemplateStroke = {
  points: Array.from({ length: 32 }, (_, index) => ({ x: index / 31, y: 0.5 })),
  startPoint: { x: 0, y: 0.5 },
  endPoint: { x: 1, y: 0.5 },
  length: 1,
};
const stroke = guide.points.map(point => ({ x: 24 + point.x * 272, y: 24 + point.y * 272 }));

test('requires correct position, direction and coverage in guided mode', () => {
  expect(evaluateGuidedTrace(stroke, guide, 320)).toBe(true);
  expect(evaluateGuidedTrace(stroke.map(point => ({ ...point, y: point.y + 70 })), guide, 320)).toBe(false);
  expect(evaluateGuidedTrace([...stroke].reverse(), guide, 320)).toBe(false);
  expect(evaluateGuidedTrace(stroke.slice(0, 8), guide, 320)).toBe(false);
});
