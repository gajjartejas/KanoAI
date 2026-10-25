import {
  Strokes,
  CharacterTemplate,
  RecognitionResult,
  RecognitionCandidate,
} from '../types/handwriting';
import { normalizeStrokes, resampleStroke } from './normalizer';
import { calculateDtwDistance, dtwDistanceToShapeScore } from './dtw';
import { generateFeedback } from './feedback';
import { evaluateStrokesAgainstTemplate } from './scoring';
import { getClassifier } from '../ml/classifier';

export interface RecognizerOptions {
  enableMlFallback?: boolean;
  maxCandidates?: number;
  categoryFilter?: 'vowel' | 'consonant' | 'barakhadi' | 'number';
}

/**
 * Compares user handwritten strokes against a specific expected character template (Guided Practice).
 * Uses DTW plus raster-template similarity on stroke mismatch.
 */
export function evaluateGuidedDrawing(rawStrokes: Strokes, targetTemplate: CharacterTemplate): RecognitionResult {
  const feedback = generateFeedback(normalizeStrokes(rawStrokes), targetTemplate);
  return {
    character: targetTemplate.gujarati,
    id: targetTemplate.id,
    confidence: feedback.confidence,
    isCorrect: feedback.isCorrect,
    overallScore: feedback.finalScore,
    shapeScore: feedback.shapeScore,
    directionScore: feedback.directionScore,
    strokeCountScore: feedback.strokeCountScore,
    errors: feedback.errors,
    method: 'dtw',
  };
}

export function evaluateUserDrawing(
  rawStrokes: Strokes,
  targetTemplate: CharacterTemplate
): RecognitionResult {
  const normalizedUserStrokes = normalizeStrokes(rawStrokes);

  if (normalizedUserStrokes.length === 0) {
    return {
      character: targetTemplate.gujarati,
      id: targetTemplate.id,
      confidence: 0,
      isCorrect: false,
      overallScore: 0,
      shapeScore: 0,
      directionScore: 0,
      strokeCountScore: 0,
      errors: {
        missingStrokes: targetTemplate.strokeCount,
        extraStrokes: 0,
        wrongDirection: false,
        strokeDetails: [],
      },
      method: 'dtw',
    };
  }

  // 1. Standard stroke-by-stroke DTW evaluation
  const feedback = generateFeedback(normalizedUserStrokes, targetTemplate);

  // 2. Continuous stroke and raster similarity fallback:
  // Triggered when user draws in continuous stroke (e.g. 1 stroke for a 2-or-3 stroke char like 'અ' or 'ક'),
  // or when stroke counts mismatch or DTW confidence is low.
  const isContinuous =
    normalizedUserStrokes.length === 1 && targetTemplate.strokeCount > 1;

  if (isContinuous || feedback.confidence < 70) {
    // Check continuous DTW against concatenated template
    let contScore = 0;
    if (isContinuous) {
      const tmplMerged = resampleStroke(
        targetTemplate.strokes.flatMap(s => s.points),
        32
      );
      const contDist = calculateDtwDistance(normalizedUserStrokes[0], tmplMerged);
      contScore = dtwDistanceToShapeScore(contDist);
    }

    // Compare 64x64 rasters; this does not run trained model inference.
    const classifier = getClassifier([targetTemplate]);
    const mlCandidates = classifier.classify(rawStrokes, [targetTemplate], 1);
    const mlResult = mlCandidates[0];
    const mlConfidence = mlResult ? mlResult.confidence : 0;
    const mlScore = mlResult ? mlResult.score : 0;

    const bestAlternativeScore = Math.max(contScore, mlScore);
    const bestAlternativeConf = Math.round(bestAlternativeScore * 100);

    if (bestAlternativeConf > feedback.confidence) {
      const isCorrect = bestAlternativeConf >= 65;
      return {
        character: targetTemplate.gujarati,
        id: targetTemplate.id,
        confidence: bestAlternativeConf,
        isCorrect,
        overallScore: bestAlternativeScore,
        shapeScore: bestAlternativeScore,
        directionScore: feedback.directionScore,
        strokeCountScore: feedback.strokeCountScore,
        errors: {
          missingStrokes: feedback.errors.missingStrokes,
          extraStrokes: feedback.errors.extraStrokes,
          wrongDirection: feedback.errors.wrongDirection,
          strokeDetails: feedback.errors.strokeDetails,
        },
        method: 'ml-fallback',
      };
    }
  }

  return {
    character: targetTemplate.gujarati,
    id: targetTemplate.id,
    confidence: feedback.confidence,
    isCorrect: feedback.isCorrect,
    overallScore: feedback.finalScore,
    shapeScore: feedback.shapeScore,
    directionScore: feedback.directionScore,
    strokeCountScore: feedback.strokeCountScore,
    errors: feedback.errors,
    method: 'dtw',
  };
}

/**
 * Searches template library to classify unguided / free drawing strokes.
 * Evaluates both the Lightweight ML 64x64 Classifier (stroke-order and stroke-count invariant)
 * and Sakoe-Chiba DTW, fusing them for maximum accuracy on continuous or multi-stroke writing.
 */
export function recognizeHandwriting(
  rawStrokes: Strokes,
  templates: CharacterTemplate[],
  options: RecognizerOptions = {}
): RecognitionCandidate[] {
  const {
    enableMlFallback = true,
    maxCandidates = 6,
    categoryFilter,
  } = options;

  if (rawStrokes.length === 0 || templates.length === 0) return [];

  const normalized = normalizeStrokes(rawStrokes);
  if (normalized.length === 0) return [];

  let pool = templates;
  if (categoryFilter) {
    pool = pool.filter(t => t.category === categoryFilter);
  }

  const userStrokeCount = normalized.length;

  // 1. Run Lightweight ML Classification across candidate pool (stroke-count and stroke-order invariant)
  const classifier = getClassifier(pool);
  const mlResults = enableMlFallback ? classifier.classify(rawStrokes, pool, 35) : [];
  const mlScoreMap = new Map<string, RecognitionCandidate>();
  mlResults.forEach(c => mlScoreMap.set(c.template.id, c));

  // 2. Select candidates to score: Top ML predictions + stroke-count compatible templates
  const candidateMap = new Map<string, CharacterTemplate>();
  mlResults.slice(0, 25).forEach(c => candidateMap.set(c.template.id, c.template));
  pool
    .filter(t => Math.abs(t.strokeCount - userStrokeCount) <= 1)
    .slice(0, 25)
    .forEach(t => {
      if (!candidateMap.has(t.id)) candidateMap.set(t.id, t);
    });

  // Precompute concatenated user stroke for single-stroke continuous input
  const userMerged =
    userStrokeCount === 1 ? normalized[0] : resampleStroke(normalized.flat(), 32);

  interface ScoredCandidate extends RecognitionCandidate {
    sortScore: number;
  }

  const scoredCandidates: ScoredCandidate[] = [];

  for (const template of candidateMap.values()) {
    const mlCand = mlScoreMap.get(template.id);
    const mlConfidence = mlCand ? mlCand.confidence : 0;
    const mlScore = mlCand ? mlCand.score : 0;

    // Standard DTW evaluation
    const dtwFeedback = generateFeedback(normalized, template);
    let dtwConfidence = dtwFeedback.confidence;
    let finalScore = dtwFeedback.finalScore;
    let method: 'dtw' | 'ml-fallback' = 'dtw';

    // Continuous-stroke DTW evaluation for multi-stroke characters drawn in 1 stroke
    if (userStrokeCount === 1 && template.strokeCount > 1) {
      const tmplMerged = resampleStroke(
        template.strokes.flatMap(s => s.points),
        32
      );
      const contDist = calculateDtwDistance(userMerged, tmplMerged);
      const contShape = dtwDistanceToShapeScore(contDist);
      const contConf = Math.round(contShape * 100);

      if (contConf > dtwConfidence) {
        dtwConfidence = contConf;
        finalScore = contShape;
      }
    }

    // Hybrid selection:
    // If user drew continuous stroke, or ML visual similarity is higher than DTW
    if (
      mlConfidence > dtwConfidence &&
      (userStrokeCount !== template.strokeCount || mlConfidence >= 70)
    ) {
      finalScore = mlScore;
      dtwConfidence = mlConfidence;
      method = 'ml-fallback';
    } else if (userStrokeCount === template.strokeCount && dtwConfidence >= 70 && mlConfidence >= 60) {
      // Both DTW and ML agree
      finalScore = 0.5 * dtwFeedback.finalScore + 0.5 * mlScore;
      dtwConfidence = Math.round(finalScore * 100);
    }

    // Give base characters (vowels, consonants, numbers) a slight natural preference over complex barakhadi compounds
    const isBaseChar =
      template.category === 'vowel' ||
      template.category === 'consonant' ||
      template.category === 'number';
    const sortScore = dtwConfidence + (isBaseChar ? 4 : 0);

    scoredCandidates.push({
      template,
      score: finalScore,
      shapeScore:
        method === 'ml-fallback'
          ? mlCand?.shapeScore || finalScore
          : dtwFeedback.shapeScore,
      directionScore: dtwFeedback.directionScore,
      strokeCountScore: dtwFeedback.strokeCountScore,
      confidence: Math.min(100, dtwConfidence),
      feedback: dtwFeedback,
      method,
      sortScore,
    });
  }

  // Sort descending by sortScore
  scoredCandidates.sort((a, b) => b.sortScore - a.sortScore);

  // De-duplicate by Gujarati character symbol so diverse characters are returned
  const seenGujarati = new Set<string>();
  const deduped: RecognitionCandidate[] = [];

  for (const c of scoredCandidates) {
    if (!seenGujarati.has(c.template.gujarati)) {
      seenGujarati.add(c.template.gujarati);
      deduped.push(c);
      if (deduped.length >= maxCandidates) break;
    }
  }

  return deduped;
}
