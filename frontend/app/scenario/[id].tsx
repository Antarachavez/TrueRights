import { useLanguage } from '../../utils/LanguageContext';
import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  ActivityIndicator, Share
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import * as Clipboard from 'expo-clipboard';
import * as Haptics from 'expo-haptics';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface LegalQuote {
  source: string;
  text: string;
  type: string;
}

interface ScenarioDetail {
  id: string;
  category: string;
  question: string;
  short_answer: string;
  explanation: string;
  script: string;
  next_steps: string[];
  legal_quotes?: LegalQuote[];
}

const CATEGORY_COLORS: Record<string, string> = {
  school: '#7DD3FC', work: '#FCA5A5', housing: '#86EFAC', police: '#FDA4AF',
  online: '#E8A5A5', public: '#6EE7B7', immigration: '#67E8F9', consumer: '#FDBA74',
};

const QUOTE_TYPE_CONFIG: Record<string, { icon: string; color: string }> = {
  'Constitution': { icon: 'shield-checkmark', color: '#C45C5C' },
  'Supreme Court': { icon: 'hammer', color: '#EC4899' },
  'Federal Law': { icon: 'document-text', color: '#1B2A4A' },
  'Federal Court': { icon: 'business', color: '#10B981' },
  'State Law': { icon: 'flag', color: '#F59E0B' },
  'Common Law': { icon: 'book', color: '#06B6D4' },
};

export default function ScenarioScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { lang } = useLanguage();
  const [scenario, setScenario] = useState<ScenarioDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchScenario(); }, [id, lang]);

  const fetchScenario = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/scenario/${id}?lang=${lang}`);
      setScenario(response.data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const shareScenario = async () => {
    if (!scenario) return;
    await Share.share({
      message: `${scenario.question}\n\n${scenario.short_answer}\n\n${scenario.explanation}`,
    });
  };

  if (loading || !scenario) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#C45C5C" />
        </View>
      </SafeAreaView>
    );
  }

  const color = CATEGORY_COLORS[scenario.category] || '#C45C5C';

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={22} color="#374151" />
        </TouchableOpacity>
        <View style={[styles.badge, { backgroundColor: `${color}15` }]}>
          <Text style={[styles.badgeText, { color }]}>{scenario.category}</Text>
        </View>
        <TouchableOpacity style={styles.shareBtn} onPress={shareScenario}>
          <Ionicons name="share-outline" size={20} color="#374151" />
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Question */}
        <Text style={[styles.question, { color: '#333333' }]}>{scenario.question}</Text>

        {/* Quick Answer */}
        <View style={[styles.card, { borderLeftWidth: 4, borderLeftColor: color }]}>
          <Text style={styles.cardLabel}>QUICK ANSWER</Text>
          <Text style={[styles.answer, { color: '#333333' }]}>{scenario.short_answer}</Text>
        </View>

        {/* Explanation */}
        <View style={styles.section}>
          <View style={styles.sectionRow}>
            <Ionicons name="information-circle" size={18} color="#5E6E7D" />
            <Text style={[styles.sectionTitle, { color: '#333333' }]}>What This Means</Text>
          </View>
          <Text style={[styles.body, { color: '#555555' }]}>{scenario.explanation}</Text>
        </View>

        {/* Next Steps */}
        <View style={styles.section}>
          <View style={styles.sectionRow}>
            <Ionicons name="footsteps" size={18} color="#5E6E7D" />
            <Text style={[styles.sectionTitle, { color: '#333333' }]}>Next Steps</Text>
          </View>
          {scenario.next_steps.map((step, i) => (
            <View key={i} style={styles.stepRow}>
              <View style={[styles.stepNum, { backgroundColor: `${color}15` }]}>
                <Text style={[styles.stepNumText, { color }]}>{i + 1}</Text>
              </View>
              <Text style={[styles.stepText, { color: '#555555' }]}>{step}</Text>
            </View>
          ))}
        </View>

        {/* Legal Quotes */}
        {scenario.legal_quotes && scenario.legal_quotes.length > 0 && (
          <View style={styles.section}>
            <View style={styles.sectionRow}>
              <Ionicons name="book" size={18} color="#C45C5C" />
              <Text style={styles.sectionTitle}>What the Law Says</Text>
            </View>
            {scenario.legal_quotes.map((quote, i) => {
              const cfg = QUOTE_TYPE_CONFIG[quote.type] || QUOTE_TYPE_CONFIG['Federal Law'];
              return (
                <View key={i} style={styles.quoteCard}>
                  <View style={[styles.quoteBadge, { backgroundColor: `${cfg.color}10` }]}>
                    <Ionicons name={cfg.icon as any} size={12} color={cfg.color} />
                    <Text style={[styles.quoteBadgeText, { color: cfg.color }]}>{quote.type}</Text>
                  </View>
                  <Text style={styles.quoteText}>{"\u201C"}{quote.text}{"\u201D"}</Text>
                  <View style={styles.sourceRow}>
                    <Ionicons name="link" size={11} color="#94A3B8" />
                    <Text style={styles.sourceText}>{quote.source}</Text>
                  </View>
                </View>
              );
            })}
          </View>
        )}

        {/* Disclaimer */}
        <View style={styles.disclaimer}>
          <Ionicons name="information-circle" size={14} color="#94A3B8" />
          <Text style={styles.disclaimerText}>Educational information only. Laws vary by state. Not legal advice.</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F0EB' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 16, paddingVertical: 10,
  },
  backBtn: {
    width: 40, height: 40, borderRadius: 20,
    backgroundColor: '#FFFDF9', justifyContent: 'center', alignItems: 'center',
    borderWidth: 1, borderColor: '#EDE9E3',
  },
  badge: { paddingHorizontal: 14, paddingVertical: 6, borderRadius: 12 },
  badgeText: { fontSize: 13, fontWeight: '600', textTransform: 'capitalize' },
  shareBtn: {
    width: 40, height: 40, borderRadius: 20,
    backgroundColor: '#FFFDF9', justifyContent: 'center', alignItems: 'center',
    borderWidth: 1, borderColor: '#EDE9E3',
  },
  scroll: { flex: 1 },
  scrollContent: { padding: 20, paddingTop: 8, paddingBottom: 40 },
  question: { fontSize: 24, fontWeight: '700', color: '#111827', lineHeight: 32, marginBottom: 20 },
  card: {
    backgroundColor: '#FFFDF9', borderRadius: 14, padding: 16, marginBottom: 24,
    borderWidth: 1, borderColor: '#EDE9E3',
  },
  cardLabel: { fontSize: 11, fontWeight: '700', color: '#94A3B8', letterSpacing: 0.5, marginBottom: 8 },
  answer: { fontSize: 16, fontWeight: '600', color: '#111827', lineHeight: 24 },
  section: { marginBottom: 24 },
  sectionRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: '#111827', marginLeft: 8 },
  body: { fontSize: 15, color: '#4B5563', lineHeight: 24 },
  stepRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 10 },
  stepNum: { width: 28, height: 28, borderRadius: 14, justifyContent: 'center', alignItems: 'center', marginRight: 12 },
  stepNumText: { fontSize: 13, fontWeight: '600' },
  stepText: { flex: 1, fontSize: 14, color: '#374151', lineHeight: 20 },
  quoteCard: {
    backgroundColor: '#FFFDF9', borderRadius: 14, padding: 16, marginBottom: 12,
    borderWidth: 1, borderColor: '#EDE9E3',
  },
  quoteBadge: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8, alignSelf: 'flex-start', marginBottom: 10 },
  quoteBadgeText: { fontSize: 11, fontWeight: '600', marginLeft: 5, textTransform: 'uppercase', letterSpacing: 0.3 },
  quoteText: { fontSize: 14, color: '#374151', lineHeight: 22, fontStyle: 'italic', marginBottom: 10 },
  sourceRow: { flexDirection: 'row', alignItems: 'center' },
  sourceText: { fontSize: 12, color: '#94A3B8', marginLeft: 6, flex: 1 },
  disclaimer: {
    flexDirection: 'row', alignItems: 'flex-start',
    backgroundColor: '#FFFDF9', borderRadius: 12, padding: 12,
    borderWidth: 1, borderColor: '#EDE9E3',
  },
  disclaimerText: { flex: 1, fontSize: 12, color: '#94A3B8', marginLeft: 8, lineHeight: 18 },
});
