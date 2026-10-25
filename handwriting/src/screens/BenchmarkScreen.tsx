import React from 'react';
import { View, Text, ScrollView, StyleSheet, Platform, useWindowDimensions } from 'react-native';
import { CharacterTemplate } from '../types/handwriting';
import { BenchmarkRunner } from '../components/BenchmarkRunner';
import { ModeSelector, ActiveTab } from '../components/ModeSelector';

interface BenchmarkScreenProps {
  templates: CharacterTemplate[];
  activeTab?: ActiveTab;
  onSelectTab?: (tab: ActiveTab) => void;
}

export const BenchmarkScreen: React.FC<BenchmarkScreenProps> = ({
  templates,
  activeTab,
  onSelectTab,
}) => {
  const { width: windowWidth } = useWindowDimensions();
  const isWide = windowWidth >= 880;

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
      <View style={[styles.workspaceLayout, isWide && styles.workspaceLayoutWide]}>
        {/* Left Column: Benchmark Runner & Specs */}
        <View style={[styles.leftColumn, isWide && styles.leftColumnWide]}>
          {/* Benchmark Harness */}
          <BenchmarkRunner templates={templates} />

          {/* Architecture Specs Card */}
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Engine Technical Specifications</Text>

            <View style={styles.specRow}>
              <Text style={styles.specLabel}>Architecture:</Text>
              <Text style={styles.specVal}>DTW + raster-template similarity</Text>
            </View>

            <View style={styles.specRow}>
              <Text style={styles.specLabel}>Normalization:</Text>
              <Text style={styles.specVal}>32 Points Arc-Length Resampling + Centered [0, 1] BBox</Text>
            </View>

            <View style={styles.specRow}>
              <Text style={styles.specLabel}>DTW Configuration:</Text>
              <Text style={styles.specVal}>Sakoe-Chiba Band (Window = 8)</Text>
            </View>

            <View style={styles.specRow}>
              <Text style={styles.specLabel}>Direction Analysis:</Text>
              <Text style={styles.specVal}>Tangent Unit Vectors + Cosine Reverse Detection</Text>
            </View>

            <View style={styles.specRow}>
              <Text style={styles.specLabel}>Scoring Weights:</Text>
              <Text style={styles.specVal}>0.5 Shape + 0.3 Direction + 0.2 Stroke Count</Text>
            </View>

            <View style={styles.specRow}>
              <Text style={styles.specLabel}>Fallback:</Text>
              <Text style={styles.specVal}>64x64 raster similarity (no trained model loaded)</Text>
            </View>

            <View style={styles.specRow}>
              <Text style={styles.specLabel}>App Footprint:</Text>
              <Text style={styles.specVal}>&lt; 1.5MB total (Strictly within &lt;10MB limit)</Text>
            </View>

            <View style={styles.specRow}>
              <Text style={styles.specLabel}>Hardware Target:</Text>
              <Text style={styles.specVal}>Low-end 4GB RAM devices (100% offline, &lt;35ms latency)</Text>
            </View>
          </View>
        </View>

        {/* Right Column: Settings Panel with Mode Selector & Dataset Stats */}
        <View style={[styles.settingsPanel, isWide && styles.settingsPanelWide]}>
          <View style={styles.panelHeader}>
            <Text style={styles.panelHeaderTitle}>⚙️ Settings & Benchmarks</Text>
          </View>

          {/* Practice Mode Switcher */}
          <ModeSelector activeTab={activeTab} onSelectTab={onSelectTab} />

          {/* Dataset Statistics */}
          <View style={styles.panelGroup}>
            <Text style={styles.panelLabel}>LOADED TEMPLATE DATASET</Text>
            <View style={styles.statsGrid}>
              <View style={styles.statBox}>
                <Text style={styles.statNum}>{templates.length}</Text>
                <Text style={styles.statLabel}>Total</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={styles.statNum}>
                  {templates.filter(t => t.category === 'consonant').length}
                </Text>
                <Text style={styles.statLabel}>Kakko</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={styles.statNum}>
                  {templates.filter(t => t.category === 'vowel').length}
                </Text>
                <Text style={styles.statLabel}>Vowels</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={styles.statNum}>
                  {templates.filter(t => t.category === 'number').length}
                </Text>
                <Text style={styles.statLabel}>Numbers</Text>
              </View>
            </View>
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
  workspaceLayout: {
    flexDirection: 'column',
    gap: 16,
    marginBottom: 20,
    width: '100%',
  },
  workspaceLayoutWide: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  leftColumn: {
    flex: 1,
    gap: 14,
    minWidth: 0,
  },
  leftColumnWide: {
    maxWidth: 740,
  },
  settingsPanel: {
    backgroundColor: '#161d27',
    borderRadius: 16,
    padding: 18,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    gap: 16,
    width: '100%',
  },
  settingsPanelWide: {
    width: 380,
    flexShrink: 0,
  },
  panelHeader: {
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.08)',
    paddingBottom: 10,
  },
  panelHeaderTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#f8fafc',
    letterSpacing: 0.3,
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
  card: {
    backgroundColor: 'rgba(22, 29, 39, 0.85)',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  cardTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#f8fafc',
    marginBottom: 14,
    textTransform: 'uppercase',
  },
  specRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.08)',
  },
  specLabel: {
    fontSize: 12,
    color: '#94a3b8',
    flex: 1,
  },
  specVal: {
    fontSize: 12,
    color: '#f1f5f9',
    fontWeight: '600',
    flex: 1.5,
    textAlign: 'right',
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 8,
  },
  statBox: {
    flex: 1,
    backgroundColor: '#0a0e14',
    padding: 10,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  statNum: {
    fontSize: 18,
    fontWeight: '700',
    color: '#38bdf8',
  },
  statLabel: {
    fontSize: 10,
    color: '#8b949e',
    marginTop: 2,
    textAlign: 'center',
  },
});
