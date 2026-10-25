import React, { useState, useRef, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Platform,
  useWindowDimensions,
} from 'react-native';
import { CharacterTemplate, Strokes, RecognitionCandidate } from '../types/handwriting';
import { HandwritingCanvas, HandwritingCanvasRef } from '../components/HandwritingCanvas';
import { recognizeHandwriting } from '../engine/recognizer';
import { ModeSelector, ActiveTab } from '../components/ModeSelector';

interface FreeDrawingScreenProps {
  templates: CharacterTemplate[];
  onSelectCandidate?: (template: CharacterTemplate) => void;
  activeTab?: ActiveTab;
  onSelectTab?: (tab: ActiveTab) => void;
}

export const FreeDrawingScreen: React.FC<FreeDrawingScreenProps> = ({
  templates,
  onSelectCandidate,
  activeTab,
  onSelectTab,
}) => {
  const [candidates, setCandidates] = useState<RecognitionCandidate[]>([]);
  const [isRecognizing, setIsRecognizing] = useState<boolean>(false);
  const [activeCategory, setActiveCategory] = useState<string>('all');

  const canvasRef = useRef<HandwritingCanvasRef>(null);

  const { width: windowWidth } = useWindowDimensions();
  const isWide = windowWidth >= 880;
  const canvasSize = isWide ? 330 : Math.min(windowWidth - 64, 330);

  const runRecognition = useCallback(
    (strokes: Strokes) => {
      if (strokes.length === 0) {
        setCandidates([]);
        return;
      }

      setIsRecognizing(true);
      setTimeout(() => {
        const results = recognizeHandwriting(strokes, templates, {
          enableMlFallback: true,
          maxCandidates: 6,
          categoryFilter: activeCategory === 'all' ? undefined : (activeCategory as any),
        });
        setCandidates(results);
        setIsRecognizing(false);
      }, 20);
    },
    [templates, activeCategory]
  );

  const handleStrokesEnd = (strokes: Strokes) => {
    runRecognition(strokes);
  };

  const handleClear = () => {
    canvasRef.current?.clear();
    setCandidates([]);
  };

  const handleUndo = () => {
    canvasRef.current?.undo();
    if (canvasRef.current) {
      const remaining = canvasRef.current.getStrokes();
      runRecognition(remaining);
    }
  };

  return (
    <ScrollView
      style={[
        styles.screen,
        Platform.OS === 'web' && ({ overflowY: 'visible', flex: 'none', height: 'auto' } as any),
      ]}
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
      scrollEnabled={Platform.OS !== 'web'}
    >
      {/* 2-Column Workspace Layout */}
      <View style={[styles.workspaceLayout, isWide ? styles.workspaceLayoutRow : styles.workspaceLayoutCol]}>
        {/* Left Column: Header Banner + Freehand Canvas Stage */}
        <View style={[styles.stagesColumn, isWide && styles.stagesColumnWide]}>
          {/* Header Banner */}
          <View style={styles.headerBanner}>
            <View style={styles.bannerInfo}>
              <Text style={styles.bannerTitle}>🔍 Free Drawing & Recognition</Text>
              <Text style={styles.bannerSubtitle}>
                Draw a Gujarati letter or number. DTW and raster similarity suggest possible matches.
              </Text>
            </View>
            <View style={styles.badgeOffline}>
              <Text style={styles.badgeOfflineText}>100% OFFLINE</Text>
            </View>
          </View>

          {/* Stage Card */}
          <View style={styles.stageCard}>
            <View style={styles.stageCardHeader}>
              <Text style={styles.stageCardTitle}>✍️ Freehand Canvas</Text>
              <View style={styles.badgeHeaderDtw}>
                <Text style={styles.badgeHeaderDtwText}>Live Stroke Capture</Text>
              </View>
            </View>

            {/* Canvas Stage */}
            <View style={styles.svgStage}>
              <HandwritingCanvas
                ref={canvasRef}
                size={canvasSize}
                strokeColor="#38bdf8"
                strokeWidth={5}
                onStrokeEnd={handleStrokesEnd}
              />
            </View>

            {/* Canvas Quick Actions Bar */}
            <View style={styles.controlsRow}>
              <TouchableOpacity style={styles.actionBtn} onPress={handleClear} activeOpacity={0.7}>
                <Text style={styles.actionBtnText}>🗑 Clear</Text>
              </TouchableOpacity>

              <TouchableOpacity style={styles.actionBtn} onPress={handleUndo} activeOpacity={0.7}>
                <Text style={styles.actionBtnText}>↩ Undo</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.actionBtn, styles.recognizeBtn]}
                onPress={() => {
                  if (canvasRef.current) {
                    runRecognition(canvasRef.current.getStrokes());
                  }
                }}
                activeOpacity={0.7}
              >
                {isRecognizing ? (
                  <ActivityIndicator size="small" color="#ffffff" />
                ) : (
                  <Text style={styles.recognizeBtnText}>⚡ Recognize</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>

        {/* Right Column: Settings & Predictions Panel */}
        <View style={[styles.settingsPanel, isWide && styles.settingsPanelWide]}>
          <View style={styles.panelHeader}>
            <Text style={styles.panelHeaderTitle}>⚙️ Filter & Predictions</Text>
          </View>

          {/* Practice Mode Switcher */}
          <ModeSelector activeTab={activeTab} onSelectTab={onSelectTab} />

          {/* Category Filter */}
          <View style={styles.panelGroup}>
            <Text style={styles.panelLabel}>CATEGORY FILTER</Text>
            <View style={styles.filterRow}>
              {[
                { id: 'all', label: 'All' },
                { id: 'consonant', label: 'Consonants' },
                { id: 'vowel', label: 'Vowels' },
                { id: 'number', label: 'Numbers' },
              ].map(cat => (
                <TouchableOpacity
                  key={cat.id}
                  style={[
                    styles.filterPill,
                    activeCategory === cat.id && styles.activeFilterPill,
                  ]}
                  onPress={() => setActiveCategory(cat.id)}
                  activeOpacity={0.7}
                >
                  <Text
                    style={[
                      styles.filterText,
                      activeCategory === cat.id && styles.activeFilterText,
                    ]}
                  >
                    {cat.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Recognition Candidates List */}
          <View style={styles.panelGroup}>
            <View style={styles.resultsHeader}>
              <Text style={styles.panelLabel}>TOP PREDICTIONS</Text>
              {isRecognizing && <ActivityIndicator size="small" color="#38bdf8" />}
            </View>

            {candidates.length === 0 ? (
              <View style={styles.emptyResultsBox}>
                <Text style={styles.emptyResultsEmoji}>✍️</Text>
                <Text style={styles.emptyResultsText}>
                  Draw any Gujarati letter or number on the canvas to see predictions
                </Text>
              </View>
            ) : (
              <View style={styles.candidateGrid}>
                {candidates.map((cand, idx) => (
                  <TouchableOpacity
                    key={`cand-${cand.template.id}-${idx}`}
                    style={[
                      styles.candidateCard,
                      idx === 0 && styles.topCandidateCard,
                    ]}
                    onPress={() => onSelectCandidate?.(cand.template)}
                    activeOpacity={0.7}
                  >
                    <View style={styles.cardHeader}>
                      <Text style={[styles.rankBadge, idx === 0 && styles.rankBadgeTop]}>
                        #{idx + 1}
                      </Text>
                      <Text style={[styles.confidenceText, idx === 0 && styles.confidenceTextTop]}>
                        {cand.confidence}%
                      </Text>
                    </View>

                    <Text style={styles.candidateGujarati}>
                      {cand.template.gujarati}
                    </Text>

                    <Text style={styles.candidateName} numberOfLines={1}>
                      {cand.template.name}
                    </Text>
                    <Text style={styles.candidateMethod}>
                      {cand.method === 'dtw' ? 'DTW Match' : 'Raster Match'}
                    </Text>
                    <Text style={styles.practiceHint}>Practice ➔</Text>
                  </TouchableOpacity>
                ))}
              </View>
            )}
          </View>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  screen: {
    backgroundColor: '#0a0e14',
    width: '100%',
  },
  scrollContent: {
    paddingHorizontal: 0,
    paddingVertical: 0,
    width: '100%',
    maxWidth: 1140,
    alignSelf: 'center',
  },

  /* Workspace Layout */
  workspaceLayout: {
    width: '100%',
    marginBottom: 24,
  },
  workspaceLayoutRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 20,
  },
  workspaceLayoutCol: {
    flexDirection: 'column',
    gap: 20,
  },

  /* Left Column */
  stagesColumn: {
    width: '100%',
    gap: 16,
  },
  stagesColumnWide: {
    flex: 1,
    minWidth: 0,
  },

  headerBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(22, 29, 39, 0.85)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 16,
    paddingHorizontal: 20,
    paddingVertical: 12,
    flexWrap: 'wrap',
    gap: 12,
  },
  bannerInfo: {
    flex: 1,
    minWidth: 200,
  },
  bannerTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#f0f6fc',
  },
  bannerSubtitle: {
    fontSize: 12,
    color: '#8b949e',
    marginTop: 2,
  },
  badgeOffline: {
    backgroundColor: 'rgba(34, 197, 94, 0.12)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 9999,
    borderWidth: 1,
    borderColor: 'rgba(34, 197, 94, 0.3)',
  },
  badgeOfflineText: {
    color: '#4ade80',
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.3,
  },

  stageCard: {
    backgroundColor: 'rgba(22, 29, 39, 0.85)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
  },
  stageCardHeader: {
    width: '100%',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  stageCardTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#8b949e',
  },
  badgeHeaderDtw: {
    backgroundColor: 'rgba(56, 189, 248, 0.15)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 9999,
  },
  badgeHeaderDtwText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#38bdf8',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  svgStage: {
    backgroundColor: '#0a0e14',
    borderWidth: 1,
    borderStyle: 'dashed',
    borderColor: 'rgba(255, 255, 255, 0.12)',
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  controlsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 10,
    marginTop: 12,
    width: '100%',
  },
  actionBtn: {
    flex: 1,
    backgroundColor: '#21262d',
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionBtnText: {
    color: '#c9d1d9',
    fontSize: 12,
    fontWeight: '600',
  },
  recognizeBtn: {
    backgroundColor: '#0284c7',
    borderColor: '#38bdf8',
  },
  recognizeBtnText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '700',
  },

  /* Right Settings & Predictions Panel */
  settingsPanel: {
    backgroundColor: 'rgba(22, 29, 39, 0.85)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 16,
    padding: 20,
    gap: 16,
    width: '100%',
  },
  settingsPanelWide: {
    width: 320,
    flexShrink: 0,
  },
  panelHeader: {
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.08)',
  },
  panelHeaderTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#f0f6fc',
  },
  panelGroup: {
    gap: 8,
  },
  panelLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#8b949e',
    letterSpacing: 0.5,
  },

  filterRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  filterPill: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 9999,
    backgroundColor: '#21262d',
    borderWidth: 1,
    borderColor: '#30363d',
  },
  activeFilterPill: {
    backgroundColor: '#0284c7',
    borderColor: '#38bdf8',
  },
  filterText: {
    color: '#8b949e',
    fontSize: 11,
    fontWeight: '600',
  },
  activeFilterText: {
    color: '#ffffff',
    fontWeight: '700',
  },

  resultsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  emptyResultsBox: {
    backgroundColor: '#0d1117',
    borderRadius: 10,
    padding: 20,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#30363d',
  },
  emptyResultsEmoji: {
    fontSize: 28,
    marginBottom: 6,
  },
  emptyResultsText: {
    color: '#6e7681',
    textAlign: 'center',
    fontSize: 12,
    lineHeight: 16,
  },

  candidateGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    justifyContent: 'space-between',
  },
  candidateCard: {
    width: '48%',
    backgroundColor: '#0d1117',
    borderRadius: 10,
    padding: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#30363d',
  },
  topCandidateCard: {
    borderColor: '#22c55e',
    backgroundColor: 'rgba(34, 197, 94, 0.08)',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
  },
  rankBadge: {
    fontSize: 10,
    color: '#8b949e',
    fontWeight: '700',
  },
  rankBadgeTop: {
    color: '#4ade80',
  },
  confidenceText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#38bdf8',
  },
  confidenceTextTop: {
    color: '#4ade80',
  },
  candidateGujarati: {
    fontSize: 30,
    color: '#f0f6fc',
    marginVertical: 4,
    fontWeight: '700',
  },
  candidateName: {
    fontSize: 11,
    color: '#cbd5e1',
    fontWeight: '600',
  },
  candidateMethod: {
    fontSize: 9,
    color: '#6e7681',
    marginTop: 2,
  },
  practiceHint: {
    fontSize: 10,
    color: '#38bdf8',
    marginTop: 6,
    fontWeight: '600',
  },
});

