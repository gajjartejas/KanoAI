import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { RecognitionResult } from '../types/handwriting';

interface RecognitionScoreCardProps {
  result: RecognitionResult | null;
}

export const RecognitionScoreCard: React.FC<RecognitionScoreCardProps> = ({ result }) => {
  if (!result) {
    return (
      <View style={styles.card}>
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyIcon}>🎯</Text>
          <View style={styles.emptyContent}>
            <Text style={styles.emptyTitle}>Accuracy Evaluation</Text>
            <Text style={styles.emptyText}>Trace character on canvas to see real-time DTW score</Text>
          </View>
        </View>
        <View style={styles.formulaPill}>
          <Text style={styles.formulaText}>50% Shape • 30% Direction • 20% Strokes</Text>
        </View>
      </View>
    );
  }

  const {
    confidence,
    isCorrect,
    shapeScore,
    directionScore,
    strokeCountScore,
    method,
    character,
    errors,
  } = result;

  const scoreColor = isCorrect ? '#22c55e' : confidence >= 50 ? '#eab308' : '#ef4444';
  const hasErrors = errors && (errors.missingStrokes > 0 || errors.extraStrokes > 0 || errors.wrongDirection);

  return (
    <View style={styles.card}>
      {/* Header: Status and Character */}
      <View style={styles.header}>
        <View style={styles.titleGroup}>
          <Text style={styles.charBadge}>{character}</Text>
          <View style={styles.titleTextContainer}>
            <Text style={[styles.statusText, { color: scoreColor }]}>
              {isCorrect ? '✓ Excellent Drawing' : confidence >= 50 ? 'Needs Improvement' : 'Try Again'}
            </Text>
            <Text style={styles.methodText}>
              Engine: {method === 'dtw' ? '⚡ DTW Deterministic' : 'Raster Similarity Fallback'}
            </Text>
          </View>
        </View>

        {/* Confidence Gauge */}
        <View style={[styles.gaugeContainer, { borderColor: scoreColor }]}>
          <Text style={[styles.gaugeValue, { color: scoreColor }]}>{confidence}%</Text>
          <Text style={styles.gaugeLabel}>Accuracy</Text>
        </View>
      </View>

      {/* Metric Breakdown Bars (0.5 Shape, 0.3 Direction, 0.2 Stroke Count) */}
      <View style={styles.breakdownSection}>
        <Text style={styles.breakdownTitle}>Scoring Formula Breakdown</Text>

        {/* Shape (50%) */}
        <View style={styles.metricRow}>
          <View style={styles.metricLabelGroup}>
            <Text style={styles.metricName}>Shape Match (50%)</Text>
            <Text style={styles.metricPercent}>{Math.round(shapeScore * 100)}%</Text>
          </View>
          <View style={styles.progressTrack}>
            <View
              style={[
                styles.progressBar,
                { width: `${Math.min(100, Math.max(0, Math.round(shapeScore * 100)))}%`, backgroundColor: '#38bdf8' },
              ]}
            />
          </View>
        </View>

        {/* Direction (30%) */}
        <View style={styles.metricRow}>
          <View style={styles.metricLabelGroup}>
            <Text style={styles.metricName}>Direction (30%)</Text>
            <Text style={styles.metricPercent}>{Math.round(directionScore * 100)}%</Text>
          </View>
          <View style={styles.progressTrack}>
            <View
              style={[
                styles.progressBar,
                { width: `${Math.min(100, Math.max(0, Math.round(directionScore * 100)))}%`, backgroundColor: '#a855f7' },
              ]}
            />
          </View>
        </View>

        {/* Stroke Count (20%) */}
        <View style={styles.metricRow}>
          <View style={styles.metricLabelGroup}>
            <Text style={styles.metricName}>Stroke Count (20%)</Text>
            <Text style={styles.metricPercent}>{Math.round(strokeCountScore * 100)}%</Text>
          </View>
          <View style={styles.progressTrack}>
            <View
              style={[
                styles.progressBar,
                { width: `${Math.min(100, Math.max(0, Math.round(strokeCountScore * 100)))}%`, backgroundColor: '#ec4899' },
              ]}
            />
          </View>
        </View>
      </View>

      {/* Inline Diagnostic Alert */}
      {hasErrors && (
        <View style={styles.inlineAlert}>
          <Text style={styles.inlineAlertText}>
            {errors.wrongDirection
              ? '🔄 Reversed stroke direction'
              : errors.missingStrokes > 0
              ? `⚠️ Missing ${errors.missingStrokes} stroke(s)`
              : `➕ ${errors.extraStrokes} extra stroke(s)`}
          </Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#0d1117',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: '#30363d',
  },
  emptyContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 4,
  },
  emptyIcon: {
    fontSize: 22,
  },
  emptyContent: {
    flex: 1,
  },
  emptyTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#f0f6fc',
  },
  emptyText: {
    color: '#8b949e',
    fontSize: 11,
    marginTop: 2,
    lineHeight: 15,
  },
  formulaPill: {
    marginTop: 8,
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 6,
    backgroundColor: '#161b22',
    borderWidth: 1,
    borderColor: '#21262d',
    alignItems: 'center',
  },
  formulaText: {
    fontSize: 10,
    color: '#8b949e',
    fontWeight: '600',
    letterSpacing: 0.3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#21262d',
    paddingBottom: 10,
  },
  titleGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    minWidth: 0,
    marginRight: 8,
  },
  charBadge: {
    fontSize: 24,
    color: '#f0f6fc',
    marginRight: 8,
    backgroundColor: '#161b22',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#30363d',
    flexShrink: 0,
  },
  titleTextContainer: {
    flex: 1,
    minWidth: 0,
  },
  statusText: {
    fontSize: 13,
    fontWeight: '700',
  },
  methodText: {
    fontSize: 10,
    color: '#8b949e',
    marginTop: 2,
  },
  gaugeContainer: {
    width: 52,
    height: 52,
    borderRadius: 26,
    borderWidth: 2.5,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#161b22',
    flexShrink: 0,
  },
  gaugeValue: {
    fontSize: 14,
    fontWeight: '800',
  },
  gaugeLabel: {
    fontSize: 8,
    color: '#94a3b8',
    textTransform: 'uppercase',
  },
  breakdownSection: {
    marginTop: 10,
  },
  breakdownTitle: {
    fontSize: 10,
    fontWeight: '700',
    color: '#8b949e',
    textTransform: 'uppercase',
    marginBottom: 6,
    letterSpacing: 0.5,
  },
  metricRow: {
    marginBottom: 6,
  },
  metricLabelGroup: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 3,
  },
  metricName: {
    fontSize: 11,
    color: '#cbd5e1',
  },
  metricPercent: {
    fontSize: 11,
    fontWeight: '600',
    color: '#f1f5f9',
  },
  progressTrack: {
    height: 5,
    backgroundColor: '#161b22',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    borderRadius: 3,
  },
  inlineAlert: {
    marginTop: 8,
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 6,
    backgroundColor: 'rgba(239, 68, 68, 0.12)',
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.3)',
  },
  inlineAlertText: {
    color: '#f87171',
    fontSize: 11,
    fontWeight: '600',
  },
});

