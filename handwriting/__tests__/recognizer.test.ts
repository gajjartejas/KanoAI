import { evaluateGuidedDrawing, evaluateUserDrawing, recognizeHandwriting } from '../src/engine/recognizer';
import { CharacterTemplate, Strokes } from '../src/types/handwriting';

describe('Hybrid Recognizer Engine (DTW + ML Fallback)', () => {
  const mockTemplateKa: CharacterTemplate = {
    id: 'consonant_1_k',
    name: 'Ka',
    gujarati: 'ક',
    transliteration: 'ka',
    category: 'consonant',
    strokeCount: 2,
    strokes: [
      {
        id: 's0',
        points: Array.from({ length: 32 }, (_, i) => ({
          x: i / 31,
          y: Math.sin((i / 31) * Math.PI) * 0.5 + 0.25,
        })),
        startPoint: { x: 0, y: 0.25 },
        endPoint: { x: 1, y: 0.25 },
        length: 1,
      },
      {
        id: 's1',
        points: Array.from({ length: 32 }, (_, i) => ({
          x: 0.8 - (i / 31) * 0.6,
          y: (i / 31) * 0.8 + 0.1,
        })),
        startPoint: { x: 0.8, y: 0.1 },
        endPoint: { x: 0.2, y: 0.9 },
        length: 0.8,
      },
    ],
  };

  test('evaluateUserDrawing scores perfect multi-stroke drawing with DTW method', () => {
    const rawStrokes: Strokes = mockTemplateKa.strokes.map(s => s.points);
    const result = evaluateUserDrawing(rawStrokes, mockTemplateKa);

    expect(result.character).toBe('ક');
    expect(result.confidence).toBeGreaterThanOrEqual(90);
    expect(result.isCorrect).toBe(true);
    expect(result.method).toBe('dtw');
    expect(result.errors.missingStrokes).toBe(0);
    expect(result.errors.wrongDirection).toBe(false);
  });

  test('evaluateUserDrawing falls back to ML when drawn as single stroke and shape matches', () => {
    // Merge the 2 strokes into a single continuous stroke (drawn without lifting finger)
    const singleStroke: Strokes = [
      [...mockTemplateKa.strokes[0].points, ...mockTemplateKa.strokes[1].points],
    ];

    const result = evaluateUserDrawing(singleStroke, mockTemplateKa);
    expect(result.character).toBe('ક');
    // ML fallback should rescue the match
    expect(result.confidence).toBeGreaterThan(60);
    expect(result.errors.missingStrokes).toBe(1);
    const guided = evaluateGuidedDrawing(singleStroke, mockTemplateKa);
    expect(guided.isCorrect).toBe(false);
    expect(guided.method).toBe('dtw');
  });

  test('recognizeHandwriting accurately recognizes character A (અ) when drawn as a single continuous stroke', () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const allTemplates: CharacterTemplate[] = require('../src/data/templates.json');
    const templateA = allTemplates.find(t => t.gujarati === 'અ');
    expect(templateA).toBeDefined();

    // User draws all points of A in 1 single continuous stroke
    const continuousA: Strokes = [templateA!.strokes.flatMap(s => s.points)];

    const candidates = recognizeHandwriting(continuousA, allTemplates, {
      maxCandidates: 5,
    });

    expect(candidates.length).toBeGreaterThan(0);
    // #1 candidate must be 'અ' (A)
    expect(candidates[0].template.gujarati).toBe('અ');
    expect(candidates[0].confidence).toBeGreaterThanOrEqual(85);
    expect(['dtw', 'ml-fallback']).toContain(candidates[0].method);
  });
});

