import { Strokes, CharacterTemplate, RecognitionCandidate, IMLModelRunner } from '../types/handwriting';
import { rasterizeStrokes, BITMAP_SIZE } from './rasterizer';
import { calculateCosineEmbedding } from './tiny_cnn';

/**
 * Default embedded raster-template classifier (legacy class name).
 * Compares user rasterized strokes against precomputed/cached character templates.
 * Provides fallback when user draws multi-stroke character as a single stroke
 * or in non-standard sequence.
 */
export class EmbeddedTinyClassifier implements IMLModelRunner {
  private templateRasters: Map<string, Float32Array> = new Map();

  constructor(templates?: CharacterTemplate[]) {
    if (templates) {
      this.initTemplates(templates);
    }
  }

  public initTemplates(templates: CharacterTemplate[]) {
    for (const t of templates) {
      if (!this.templateRasters.has(t.id)) {
        const rawStrokes = t.strokes.map(s => s.points);
        const raster = rasterizeStrokes(rawStrokes, BITMAP_SIZE);
        this.templateRasters.set(t.id, raster);
      }
    }
  }

  public getRaster(templateId: string): Float32Array | undefined {
    return this.templateRasters.get(templateId);
  }

  /**
   * Implements IMLModelRunner.predict
   */
  public async predict(raster64x64: Float32Array): Promise<Array<{ classIndex: number; probability: number }>> {
    // Computes similarity against all template rasters
    const results: Array<{ classIndex: number; probability: number }> = [];
    let idx = 0;
    for (const [, refRaster] of this.templateRasters) {
      const sim = calculateCosineEmbedding(raster64x64, refRaster);
      results.push({ classIndex: idx++, probability: Math.max(0, sim) });
    }
    return results.sort((a, b) => b.probability - a.probability);
  }

  /**
   * Classifies user strokes against candidate templates.
   */
  public classify(
    strokes: Strokes,
    templates: CharacterTemplate[],
    topK = 5
  ): RecognitionCandidate[] {
    if (strokes.length === 0 || templates.length === 0) return [];

    const userRaster = rasterizeStrokes(strokes, BITMAP_SIZE);
    const scored: Array<{ template: CharacterTemplate; similarity: number }> = [];

    for (const template of templates) {
      let refRaster = this.templateRasters.get(template.id);
      if (!refRaster) {
        const rawStrokes = template.strokes.map(s => s.points);
        refRaster = rasterizeStrokes(rawStrokes, BITMAP_SIZE);
        this.templateRasters.set(template.id, refRaster);
      }

      const similarity = calculateCosineEmbedding(userRaster, refRaster);
      scored.push({ template, similarity });
    }

    scored.sort((a, b) => b.similarity - a.similarity);

    return scored.slice(0, topK).map(item => {
      const confidence = Math.round(Math.max(0, Math.min(100, item.similarity * 100)));
      const isCorrect = confidence >= 70;
      return {
        template: item.template,
        score: item.similarity,
        shapeScore: item.similarity,
        directionScore: 0.8,
        strokeCountScore: 0.8,
        confidence,
        feedback: {
          confidence,
          isCorrect,
          shapeScore: item.similarity,
          strokeCountScore: 0.8,
          directionScore: 0.8,
          finalScore: item.similarity,
          errors: {
            missingStrokes: 0,
            extraStrokes: 0,
            wrongDirection: false,
            strokeDetails: [],
          },
        },
        method: 'ml-fallback',
      };
    });
  }
}

// Global default classifier singleton
let defaultClassifierInstance: EmbeddedTinyClassifier | null = null;

export function getClassifier(templates?: CharacterTemplate[]): EmbeddedTinyClassifier {
  if (!defaultClassifierInstance) {
    defaultClassifierInstance = new EmbeddedTinyClassifier(templates);
  } else if (templates) {
    defaultClassifierInstance.initTemplates(templates);
  }
  return defaultClassifierInstance;
}
