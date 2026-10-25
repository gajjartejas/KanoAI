import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Switch,
  Platform,
  useWindowDimensions,
} from 'react-native';
import { CharacterTemplate, Strokes, RecognitionResult } from '../types/handwriting';
import { HandwritingCanvas, HandwritingCanvasRef } from '../components/HandwritingCanvas';
import { GuidedOverlay } from '../components/GuidedOverlay';
import { CharacterSelector } from '../components/CharacterSelector';
import { DrawingReplayModal } from '../components/DrawingReplayModal';
import { WorksheetModal } from '../components/WorksheetModal';
import { RecognitionScoreCard } from '../components/RecognitionScoreCard';
import { StrokeDiagnostics } from '../components/StrokeDiagnostics';
import { evaluateGuidedDrawing } from '../engine/recognizer';
import { evaluateGuidedTrace } from '../engine/guidedTrace';
import { speakGujarati } from '../utils/speech';
import { ModeSelector, ActiveTab } from '../components/ModeSelector';

interface GuidedPracticeScreenProps {
  templates: CharacterTemplate[];
  initialTemplate?: CharacterTemplate;
  isEmbedded?: boolean;
  activeTab?: ActiveTab;
  onSelectTab?: (tab: ActiveTab) => void;
}

export const GuidedPracticeScreen: React.FC<GuidedPracticeScreenProps> = ({
  templates,
  initialTemplate,
  isEmbedded = false,
  activeTab = 'guided',
  onSelectTab,
}) => {
  const canvasRef = useRef<HandwritingCanvasRef>(null);
  const validatedCountRef = useRef(0);

  const [selectedTemplate, setSelectedTemplate] = useState<CharacterTemplate>(
    initialTemplate || templates.find(t => t.id === '1_k' || t.gujarati === 'ક') || templates[0] || ({} as CharacterTemplate)
  );

  useEffect(() => {
    if (initialTemplate) {
      setSelectedTemplate(initialTemplate);
      canvasRef.current?.clear();
      setUserStrokes([]);
      setResult(null);
      validatedCountRef.current = 0;
    }
  }, [initialTemplate]);

  const [showOverlay, setShowOverlay] = useState<boolean>(true);
  const [showStrokeOrder, setShowStrokeOrder] = useState<boolean>(true);
  const [strokeColor, setStrokeColor] = useState<string>('#38bdf8');
  const [result, setResult] = useState<RecognitionResult | null>(null);
  const [userStrokes, setUserStrokes] = useState<Strokes>([]);

  // Feature Modals
  const [isReplayOpen, setIsReplayOpen] = useState(false);
  const [isWorksheetOpen, setIsWorksheetOpen] = useState(false);

  const { width: windowWidth } = useWindowDimensions();
  const isDesktop = windowWidth >= 960;
  const isTabletOrDesktop = windowWidth >= 680;
  const canvasSize = isTabletOrDesktop ? 330 : Math.max(260, Math.min(windowWidth - 64, 320));

  const handleStrokesEnd = useCallback(
    (strokes: Strokes) => {
      if (strokes.length <= validatedCountRef.current) {
        validatedCountRef.current = strokes.length;
        setUserStrokes(strokes);
        setResult(null);
        return;
      }
      const nextIndex = validatedCountRef.current;
      const guide = selectedTemplate.strokes[nextIndex];
      if (!guide || !evaluateGuidedTrace(strokes[nextIndex], guide, canvasSize)) {
        canvasRef.current?.undo();
        return;
      }
      validatedCountRef.current = strokes.length;
      setUserStrokes(strokes);
      setResult(strokes.length === selectedTemplate.strokeCount ? evaluateGuidedDrawing(strokes, selectedTemplate) : null);
    },
    [canvasSize, selectedTemplate]
  );

  const handleSelectTemplate = (t: CharacterTemplate) => {
    setSelectedTemplate(t);
    canvasRef.current?.clear();
    setUserStrokes([]);
    setResult(null);
    validatedCountRef.current = 0;
  };

  const handleClear = () => {
    canvasRef.current?.clear();
    setUserStrokes([]);
    setResult(null);
    validatedCountRef.current = 0;
  };

  const handleUndo = () => {
    canvasRef.current?.undo();
  };

  // Real-time Next-Stroke Hint
  const strokeCount = selectedTemplate.strokeCount || 1;
  const drawnCount = userStrokes.length;
  const activeStrokeIndex = drawnCount;

  let nextStrokeHint = '';
  if (drawnCount === 0) {
    nextStrokeHint = `💡 Stroke 1: Start at bubble ① and follow the arrow`;
  } else if (drawnCount < strokeCount) {
    nextStrokeHint = `💡 Next: Start at bubble ${drawnCount + 1} of ${strokeCount} (blue glowing stroke)`;
  } else {
    nextStrokeHint = result
      ? `✓ All ${strokeCount} strokes drawn! Accuracy: ${result.confidence}% (${result.isCorrect ? 'Excellent' : 'Needs Practice'}).`
      : `✓ All ${strokeCount} strokes drawn!`;
  }

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
      {/* Top Workspace: Stages (Left) + Settings Panel (Right) */}
      <View style={[styles.workspaceLayout, isDesktop ? styles.workspaceLayoutRow : styles.workspaceLayoutCol]}>
        {/* Left Column: Character Banner + Handwriting Canvas Stage */}
        <View style={[styles.stagesColumn, isDesktop && styles.stagesColumnWide]}>
          {/* Active Character Summary Banner */}
          <View style={styles.charHeaderBanner}>
            <View style={styles.charMainInfo}>
              <Text style={styles.charGlyphLarge}>{selectedTemplate.gujarati}</Text>
              <View style={styles.charNames}>
                <Text style={styles.charTitle}>
                  {selectedTemplate.gujarati} ({selectedTemplate.name})
                </Text>
                <Text style={styles.charSubtitle}>
                  {selectedTemplate.category === 'vowel'
                    ? 'Swar Vowel (સ્વર)'
                    : selectedTemplate.category === 'number'
                    ? 'Ank Number (અંક)'
                    : 'Kakko Consonant (વ્યંજન)'}
                </Text>
              </View>
            </View>

            <View style={styles.charMetaTags}>
              <View style={styles.tagAccent}>
                <Text style={styles.tagAccentText}>
                  {selectedTemplate.category?.toUpperCase() || 'KAKKO'}
                </Text>
              </View>
              <View style={styles.tag}>
                <Text style={styles.tagText}>
                  {strokeCount} Stroke{strokeCount > 1 ? 's' : ''}
                </Text>
              </View>
              <TouchableOpacity
                style={styles.listenBtn}
                onPress={() => speakGujarati(selectedTemplate.gujarati, selectedTemplate.transliteration)}
                activeOpacity={0.7}
              >
                <Text style={styles.listenBtnText}>🔊 Listen</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Drawing Canvas Stage Card (Handwriting Square + Accuracy Evaluation Next to It) */}
          <View style={styles.stageCard}>
            <View style={styles.stageCardHeader}>
              <View style={styles.stageCardHeaderLeft}>
                <Text style={styles.stageCardTitle}>✍️ Tracing Stage & Evaluation</Text>
              </View>
              <View style={styles.stageHeaderRight}>
                {result && (
                  <View
                    style={[
                      styles.liveAccuracyBadge,
                      {
                        backgroundColor: result.isCorrect
                          ? 'rgba(34, 197, 94, 0.15)'
                          : result.confidence >= 50
                          ? 'rgba(234, 179, 8, 0.15)'
                          : 'rgba(239, 68, 68, 0.15)',
                        borderColor: result.isCorrect
                          ? '#22c55e'
                          : result.confidence >= 50
                          ? '#eab308'
                          : '#ef4444',
                      },
                    ]}
                  >
                    <Text
                      style={[
                        styles.liveAccuracyText,
                        {
                          color: result.isCorrect
                            ? '#4ade80'
                            : result.confidence >= 50
                            ? '#facc15'
                            : '#f87171',
                        },
                      ]}
                    >
                      🎯 {result.confidence}% Accuracy
                    </Text>
                  </View>
                )}
                <View style={styles.badgeHeaderDtw}>
                  <Text style={styles.badgeHeaderDtwText}>Guided stroke check</Text>
                </View>
              </View>
            </View>

            {/* Stage Body: Canvas (Left) + Accuracy Evaluation (Right) on Tablet & Desktop */}
            <View style={[styles.stageBodyRow, !isTabletOrDesktop && styles.stageBodyCol]}>
              {/* Canvas Container */}
              <View style={[styles.canvasContainer, { width: isTabletOrDesktop ? 330 : canvasSize }]}>
                <View style={[styles.svgStage, { width: canvasSize, height: canvasSize }]}>
                  <HandwritingCanvas
                    ref={canvasRef}
                    size={canvasSize}
                    strokeColor={strokeColor}
                    strokeWidth={5}
                    onStrokeEnd={handleStrokesEnd}
                  >
                    {showOverlay && (
                      <GuidedOverlay
                        template={selectedTemplate}
                        size={canvasSize}
                        activeStrokeIndex={activeStrokeIndex}
                        showStrokes={true}
                        showStrokeOrder={showStrokeOrder}
                        showDirectionArrows={true}
                      />
                    )}
                  </HandwritingCanvas>
                </View>

                {/* Hint Banner below canvas */}
                <View
                  style={[
                    styles.hintBanner,
                    drawnCount >= strokeCount && styles.hintBannerComplete,
                  ]}
                >
                  <Text style={styles.hintText}>{nextStrokeHint}</Text>
                </View>
              </View>

              {/* Accuracy Evaluation Next to Canvas */}
              <View style={styles.accuracyEvaluationPane}>
                <View style={styles.accuracyPaneHeader}>
                  <Text style={styles.accuracyCardTitle}>📊 Accuracy Evaluation</Text>
                  {result && (
                    <View
                      style={[
                        styles.scorePill,
                        {
                          backgroundColor: result.isCorrect
                            ? 'rgba(34, 197, 94, 0.15)'
                            : result.confidence >= 50
                            ? 'rgba(234, 179, 8, 0.15)'
                            : 'rgba(239, 68, 68, 0.15)',
                          borderColor: result.isCorrect
                            ? '#22c55e'
                            : result.confidence >= 50
                            ? '#eab308'
                            : '#ef4444',
                        },
                      ]}
                    >
                      <Text
                        style={[
                          styles.scorePillText,
                          {
                            color: result.isCorrect
                              ? '#4ade80'
                              : result.confidence >= 50
                              ? '#facc15'
                              : '#f87171',
                          },
                        ]}
                      >
                        {result.confidence}% {result.isCorrect ? 'PASS' : 'RETRY'}
                      </Text>
                    </View>
                  )}
                </View>
                <RecognitionScoreCard result={result} />
                {result && <StrokeDiagnostics result={result} />}
              </View>
            </View>
          </View>
        </View>

        {/* Right Column: Settings & Controls Panel */}
        <View style={[styles.settingsPanel, isDesktop && styles.settingsPanelWide]}>
          <View style={styles.panelHeader}>
            <Text style={styles.panelHeaderTitle}>⚙️ Settings & Controls</Text>
          </View>

          {/* Practice Mode Switcher */}
          <ModeSelector activeTab={activeTab} onSelectTab={onSelectTab} />

          {/* Quick Playback & Drawing Actions */}
          <View style={styles.panelGroup}>
            <Text style={styles.panelLabel}>ACTIONS</Text>
            <View style={styles.panelBtnGrid}>
              <TouchableOpacity style={styles.btnActionSecondary} onPress={handleClear} activeOpacity={0.7}>
                <Text style={styles.btnActionSecondaryText}>🗑 Clear</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.btnActionSecondary} onPress={handleUndo} activeOpacity={0.7}>
                <Text style={styles.btnActionSecondaryText}>↩ Undo</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.btnActionPrimary, userStrokes.length === 0 && styles.btnDisabled]}
                onPress={() => setIsReplayOpen(true)}
                disabled={userStrokes.length === 0}
                activeOpacity={0.7}
              >
                <Text style={styles.btnActionPrimaryText}>▶ Replay</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.btnActionWorksheet}
                onPress={() => setIsWorksheetOpen(true)}
                activeOpacity={0.7}
              >
                <Text style={styles.btnActionWorksheetText}>📄 Worksheet</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Display Layers (Toggles) */}
          <View style={styles.panelGroup}>
            <Text style={styles.panelLabel}>DISPLAY LAYERS</Text>
            <View style={styles.toggleRow}>
              <Text style={styles.toggleLabel}>Ghost Guide & Glow</Text>
              <Switch
                value={showOverlay}
                onValueChange={setShowOverlay}
                trackColor={{ false: '#21262d', true: '#0369a1' }}
                thumbColor={showOverlay ? '#38bdf8' : '#6e7681'}
              />
            </View>
            <View style={styles.toggleRow}>
              <Text style={styles.toggleLabel}>Stroke Numbers (1, 2, 3)</Text>
              <Switch
                value={showStrokeOrder}
                onValueChange={setShowStrokeOrder}
                trackColor={{ false: '#21262d', true: '#0369a1' }}
                thumbColor={showStrokeOrder ? '#38bdf8' : '#6e7681'}
              />
            </View>
          </View>

          {/* Ink Color Picker */}
          <View style={styles.panelGroup}>
            <Text style={styles.panelLabel}>INK COLOR</Text>
            <View style={styles.colorPalette}>
              {['#38bdf8', '#4ade80', '#f472b6', '#fbbf24', '#a855f7'].map(color => (
                <TouchableOpacity
                  key={color}
                  style={[
                    styles.colorDot,
                    { backgroundColor: color },
                    strokeColor === color && styles.activeColorDot,
                  ]}
                  onPress={() => setStrokeColor(color)}
                  activeOpacity={0.7}
                />
              ))}
            </View>
          </View>
        </View>
      </View>

      {/* Bottom Section: Character Catalog Browser (Hidden when embedded in unified suite) */}
      {!isEmbedded && (
        <View style={styles.catalogSection}>
          <CharacterSelector
            templates={templates}
            selectedTemplate={selectedTemplate}
            onSelect={handleSelectTemplate}
          />
        </View>
      )}

      {/* Feature Modals */}
      <DrawingReplayModal
        visible={isReplayOpen}
        onClose={() => setIsReplayOpen(false)}
        userStrokes={userStrokes}
        template={selectedTemplate}
      />
      <WorksheetModal
        visible={isWorksheetOpen}
        onClose={() => setIsWorksheetOpen(false)}
        template={selectedTemplate}
      />
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

  /* Workspace Layout (Stages Left + Controls Right) */
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

  /* Left Column: Stages */
  stagesColumn: {
    width: '100%',
    gap: 16,
  },
  stagesColumnWide: {
    flex: 1,
    minWidth: 0,
  },

  /* Character Summary Banner */
  charHeaderBanner: {
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
  charMainInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  charGlyphLarge: {
    fontSize: 38,
    fontWeight: '700',
    color: '#ff6b35',
    lineHeight: 40,
  },
  charNames: {
    flexDirection: 'column',
  },
  charTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#f0f6fc',
  },
  charSubtitle: {
    fontSize: 12,
    color: '#8b949e',
  },
  charMetaTags: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  tag: {
    backgroundColor: '#21262d',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 9999,
  },
  tagText: {
    fontSize: 11,
    color: '#8b949e',
    fontWeight: '600',
  },
  tagAccent: {
    backgroundColor: 'rgba(255, 107, 53, 0.15)',
    borderWidth: 1,
    borderColor: '#ff6b35',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 9999,
  },
  tagAccentText: {
    fontSize: 11,
    color: '#ff6b35',
    fontWeight: '700',
  },
  listenBtn: {
    backgroundColor: 'rgba(56, 189, 248, 0.15)',
    borderWidth: 1,
    borderColor: '#38bdf8',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 9999,
  },
  listenBtnText: {
    fontSize: 11,
    color: '#38bdf8',
    fontWeight: '700',
  },

  /* Stage Card */
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
  stageCardHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  stageCardTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#8b949e',
  },
  stageHeaderRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  liveAccuracyBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 9999,
    borderWidth: 1,
  },
  liveAccuracyText: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.3,
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
  hintBanner: {
    backgroundColor: 'rgba(56, 189, 248, 0.12)',
    borderWidth: 1,
    borderColor: 'rgba(56, 189, 248, 0.3)',
    borderRadius: 10,
    paddingVertical: 8,
    paddingHorizontal: 14,
    marginTop: 10,
    width: '100%',
    alignItems: 'center',
  },
  hintBannerComplete: {
    backgroundColor: 'rgba(34, 197, 94, 0.15)',
    borderColor: 'rgba(34, 197, 94, 0.3)',
  },
  hintText: {
    color: '#f0f6fc',
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
  },

  /* Stage Body Layout & Accuracy Evaluation Pane */
  stageBodyRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 16,
    width: '100%',
  },
  stageBodyCol: {
    flexDirection: 'column',
    alignItems: 'center',
    gap: 14,
  },
  canvasContainer: {
    alignItems: 'center',
    maxWidth: '100%',
    flexShrink: 0,
  },
  accuracyEvaluationPane: {
    flex: 1,
    minWidth: 0,
    width: '100%',
    gap: 8,
  },
  accuracyPaneHeader: {
    width: '100%',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  accuracyCardTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#f0f6fc',
    letterSpacing: 0.3,
  },

  /* Right Settings Panel */
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
  panelLabelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  scorePill: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 9999,
    borderWidth: 1,
  },
  scorePillText: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  panelBtnGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  btnActionPrimary: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: '#0284c7',
    borderWidth: 1,
    borderColor: '#38bdf8',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  btnActionPrimaryText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '700',
  },
  btnActionSecondary: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: '#21262d',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  btnActionSecondaryText: {
    color: '#c9d1d9',
    fontSize: 12,
    fontWeight: '600',
  },
  btnActionWorksheet: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: 'rgba(34, 197, 94, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(34, 197, 94, 0.4)',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  btnActionWorksheetText: {
    color: '#4ade80',
    fontSize: 12,
    fontWeight: '700',
  },
  btnDisabled: {
    opacity: 0.4,
  },
  toggleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 2,
  },
  toggleLabel: {
    color: '#c9d1d9',
    fontSize: 12,
  },
  colorPalette: {
    flexDirection: 'row',
    gap: 8,
  },
  colorDot: {
    width: 22,
    height: 22,
    borderRadius: 11,
  },
  activeColorDot: {
    borderWidth: 2,
    borderColor: '#ffffff',
  },

  /* Bottom Section: Character Catalog */
  catalogSection: {
    width: '100%',
    backgroundColor: 'rgba(22, 29, 39, 0.85)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 16,
    padding: 16,
  },
  catalogHeader: {
    marginBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.08)',
    paddingBottom: 6,
  },
  catalogTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#f0f6fc',
  },
  catalogSubtitle: {
    fontSize: 11,
    color: '#8b949e',
    marginTop: 2,
  },
});

