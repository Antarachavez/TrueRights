import { useLanguage } from '../../../utils/LanguageContext';
import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  ActivityIndicator, Share
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import Animated, { FadeInUp } from 'react-native-reanimated';
import axios from 'axios';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

const QUOTE_TYPE_CONFIG: { [key: string]: { icon: string; gradient: string[] } } = {
  'Constitution': { icon: 'shield-checkmark', gradient: ['#E8A5A5', '#DDD6FE'] },
  'Supreme Court': { icon: 'hammer', gradient: ['#FDA4AF', '#FCA5A5'] },
  'Federal Law': { icon: 'document-text', gradient: ['#7DD3FC', '#93C5FD'] },
  'Federal Court': { icon: 'business', gradient: ['#86EFAC', '#6EE7B7'] },
  'State Law': { icon: 'flag', gradient: ['#FDBA74', '#FCD34D'] },
  'Common Law': { icon: 'book', gradient: ['#67E8F9', '#7DD3FC'] },
};

export default function GeneratedScenarioScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { t } = useLanguage();
  const [scenario, setScenario] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchScenario();
  }, [id]);

  const fetchScenario = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/scenario/generated/${id}`);
      setScenario(response.data);
    } catch (error) {
      console.error('Error fetching generated scenario:', error);
    } finally {
      setLoading(false);
    }
  };

  const shareScenario = async () => {
    if (!scenario) return;
    try {
      await Share.share({
        message: `${scenario.question}\n\n${scenario.short_answer}\n\n${scenario.explanation}`,
      });
    } catch (error) {
      console.error('Error sharing:', error);
    }
  };

  if (loading || !scenario) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#E8A5A5" />
          <Text style={styles.loadingText}>Loading...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color="#1B2A4A" />
        </TouchableOpacity>
        <View style={styles.headerActions}>
          <TouchableOpacity style={styles.actionBtn} onPress={shareScenario}>
            <Ionicons name="share-outline" size={20} color="#1B2A4A" />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* AI Generated Badge */}
        <View>
          <View style={styles.aiBadge}>
            <LinearGradient
              colors={['#E8A5A5', '#D4787A']}
              style={styles.aiBadgeGradient}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
            >
              <Ionicons name="sparkles" size={14} color="#FFFFFF" />
              <Text style={styles.aiBadgeText}>AI Generated</Text>
            </LinearGradient>
            {scenario.category_name && (
              <View style={styles.categoryBadge}>
                <Text style={styles.categoryBadgeText}>{scenario.category_name}</Text>
              </View>
            )}
          </View>
        </View>

        {/* Question */}
        <View>
          <Text style={styles.question}>{scenario.question}</Text>
        </View>

        {/* Quick Answer */}
        <View>
          <View style={styles.sectionHeader}>
            <Ionicons name="flash" size={20} color="#FDBA74" />
            <Text style={styles.sectionTitle}>{t('scenario.quickAnswer')}</Text>
          </View>
          <View style={[styles.answerCard, { borderLeftColor: '#E8A5A5' }]}>
            <Text style={styles.shortAnswer}>{scenario.short_answer}</Text>
          </View>
        </View>

        {/* Explanation */}
        <View>
          <View style={styles.sectionHeader}>
            <Ionicons name="information-circle" size={20} color="#5E6E7D" />
            <Text style={styles.sectionTitle}>What This Usually Means</Text>
          </View>
          <Text style={styles.explanation}>{scenario.explanation}</Text>
        </View>

        {/* Next Steps */}
        {scenario.next_steps && scenario.next_steps.length > 0 && (
          <View>
            <View style={styles.sectionHeader}>
              <Ionicons name="footsteps" size={20} color="#5E6E7D" />
              <Text style={styles.sectionTitle}>{t('scenario.nextSteps')}</Text>
            </View>
            <View style={styles.stepsList}>
              {scenario.next_steps.map((step: string, index: number) => (
                <View key={index} style={styles.stepItem}>
                  <View style={styles.stepNumber}>
                    <Text style={styles.stepNumberText}>{index + 1}</Text>
                  </View>
                  <Text style={styles.stepText}>{step}</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Legal Quotes */}
        {scenario.legal_quotes && scenario.legal_quotes.length > 0 && (
          <View>
            <View style={styles.sectionHeader}>
              <Ionicons name="book" size={20} color="#E8A5A5" />
              <Text style={styles.sectionTitle}>{t('scenario.whatLawSays')}</Text>
            </View>
            {scenario.legal_quotes.map((quote: any, index: number) => {
              const config = QUOTE_TYPE_CONFIG[quote.type] || QUOTE_TYPE_CONFIG['Federal Law'];
              return (
                <View key={index} style={styles.legalQuoteCard}>
                  <LinearGradient
                    colors={[`${config.gradient[0]}15`, `${config.gradient[1]}08`]}
                    style={styles.legalQuoteGradient}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 1 }}
                  >
                    <View style={styles.legalQuoteHeader}>
                      <View style={[styles.legalTypeBadge, { backgroundColor: `${config.gradient[0]}25` }]}>
                        <Ionicons name={config.icon as any} size={12} color={config.gradient[0]} />
                        <Text style={[styles.legalTypeText, { color: config.gradient[0] }]}>{quote.type}</Text>
                      </View>
                    </View>
                    <Text style={styles.legalQuoteText}>{"\u201C"}{quote.text}{"\u201D"}</Text>
                    <View style={styles.legalSourceRow}>
                      <Ionicons name="link" size={12} color="#94A3B8" />
                      <Text style={styles.legalSourceText}>{quote.source}</Text>
                    </View>
                  </LinearGradient>
                </View>
              );
            })}
          </View>
        )}

        {/* Disclaimer */}
        <View style={styles.disclaimer}>
          <Ionicons name="information-circle" size={14} color="#94A3B8" />
          <Text style={styles.disclaimerText}>
            AI-generated content. This is educational info, not legal advice. Laws vary by state.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F0EB' },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { color: '#5E6E7D', fontSize: 14, marginTop: 12 },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 12,
  },
  backButton: {
    width: 40, height: 40, borderRadius: 20,
    backgroundColor: '#FFFDF9',
    justifyContent: 'center', alignItems: 'center',
  },
  headerActions: { flexDirection: 'row', gap: 8 },
  actionBtn: {
    width: 40, height: 40, borderRadius: 20,
    backgroundColor: '#FFFDF9',
    justifyContent: 'center', alignItems: 'center',
  },
  scrollView: { flex: 1 },
  scrollContent: { padding: 20, paddingTop: 4, paddingBottom: 40 },
  aiBadge: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  aiBadgeGradient: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8,
  },
  aiBadgeText: { color: '#FFFFFF', fontSize: 12, fontWeight: '600' },
  categoryBadge: {
    backgroundColor: '#EDE9E3', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 8,
  },
  categoryBadgeText: { color: '#5E6E7D', fontSize: 12, fontWeight: '500' },
  question: { fontSize: 22, fontWeight: '700', color: '#1B2A4A', lineHeight: 30, marginBottom: 20 },
  section: { marginBottom: 20 },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: '#374151' },
  answerCard: {
    backgroundColor: '#FFFDF9', borderRadius: 14, padding: 16,
    borderLeftWidth: 3, borderWidth: 1, borderColor: '#EDE9E3',
  },
  shortAnswer: { fontSize: 16, color: '#1B2A4A', lineHeight: 24, fontWeight: '500' },
  explanation: { fontSize: 15, color: '#5E6E7D', lineHeight: 24 },
  stepsList: { gap: 10 },
  stepItem: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  stepNumber: {
    width: 28, height: 28, borderRadius: 14,
    backgroundColor: '#E8A5A520',
    justifyContent: 'center', alignItems: 'center',
  },
  stepNumberText: { color: '#E8A5A5', fontSize: 13, fontWeight: '600' },
  stepText: { flex: 1, fontSize: 14, color: '#5E6E7D', lineHeight: 20 },
  legalQuoteCard: { borderRadius: 16, overflow: 'hidden', marginBottom: 12, borderWidth: 1, borderColor: '#EDE9E3' },
  legalQuoteGradient: { padding: 16 },
  legalQuoteHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 10 },
  legalTypeBadge: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8,
  },
  legalTypeText: { fontSize: 11, fontWeight: '600', marginLeft: 5, textTransform: 'uppercase', letterSpacing: 0.5 },
  legalQuoteText: { fontSize: 15, color: '#374151', lineHeight: 24, fontStyle: 'italic', marginBottom: 10 },
  legalSourceRow: { flexDirection: 'row', alignItems: 'center' },
  legalSourceText: { fontSize: 12, color: '#94A3B8', marginLeft: 6, flex: 1, fontWeight: '500' },
  disclaimer: {
    flexDirection: 'row', alignItems: 'flex-start',
    backgroundColor: '#FFFDF9', borderRadius: 12, padding: 12,
    borderWidth: 1, borderColor: '#EDE9E3', marginTop: 8,
  },
  disclaimerText: { flex: 1, fontSize: 12, color: '#94A3B8', marginLeft: 8, lineHeight: 18 },
});
