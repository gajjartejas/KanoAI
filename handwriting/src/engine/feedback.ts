import { Strokes, CharacterTemplate, RecognitionFeedback } from '../types/handwriting';
import { evaluateStrokesAgainstTemplate } from './scoring';

export const PASSING_CONFIDENCE_THRESHOLD = 70;

/**
 * Generates user feedback and diagnostic errors for handwriting evaluation.
 * Conforms to PRD Section 9.
 */
export function generateFeedback(
  normalizedUserStrokes: Strokes,
  template: CharacterTemplate
): RecognitionFeedback {
  const evalResult = evaluateStrokesAgainstTemplate(normalizedUserStrokes, template);

  const actualCount = normalizedUserStrokes.length;
  const expectedCount = template.strokeCount;

  const missingStrokes = Math.max(0, expectedCount - actualCount);
  const extraStrokes = Math.max(0, actualCount - expectedCount);
  const wrongDirection = evalResult.wrongDirection;

  // Guided stroke scoring requires the exact count, not merely a count penalty.
  const isCorrect =
    evalResult.confidence >= PASSING_CONFIDENCE_THRESHOLD &&
    missingStrokes === 0 &&
    extraStrokes === 0 &&
    evalResult.strokeDetails.every(stroke => stroke.passed) &&
    !wrongDirection;

  return {
    confidence: evalResult.confidence,
    isCorrect,
    shapeScore: evalResult.shapeScore,
    strokeCountScore: evalResult.strokeCountScore,
    directionScore: evalResult.directionScore,
    finalScore: evalResult.finalScore,
    errors: {
      missingStrokes,
      extraStrokes,
      wrongDirection,
      strokeDetails: evalResult.strokeDetails,
    },
  };
}
