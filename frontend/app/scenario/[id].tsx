import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Clipboard from 'expo-clipboard';
import * as Haptics from 'expo-haptics';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LinearGradient } from 'expo-linear-gradient';
import axios from 'axios';
import Animated, { FadeInUp, FadeIn } from 'react-native-reanimated';

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

const CATEGORY_COLORS: { [key: string]: string } = {
  school: '#7DD3FC',
  work: '#FCA5A5',
  housing: '#86EFAC',
  police: '#FDA4AF',
  online: '#C4B5FD',
  public: '#6EE7B7',
  immigration: '#67E8F9',
  consumer: '#FDBA74',
};

const QUOTE_TYPE_CONFIG: { [key: string]: { icon: string; gradient: string[] } } = {
  'Constitution': { icon: 'shield-checkmark', gradient: ['#C4B5FD', '#DDD6FE'] },
  'Supreme Court': { icon: 'hammer', gradient: ['#FDA4AF', '#FCA5A5'] },
  'Federal Law': { icon: 'document-text', gradient: ['#7DD3FC', '#93C5FD'] },
  'Federal Court': { icon: 'business', gradient: ['#86EFAC', '#6EE7B7'] },
  'State Law': { icon: 'flag', gradient: ['#FDBA74', '#FCD34D'] },
  'Common Law': { icon: 'book', gradient: ['#67E8F9', '#7DD3FC'] },
};

export default function ScenarioScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [scenario, setScenario] = useState<ScenarioDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [copiedScript, setCopiedScript] = useState(false);
  const [savedScript, setSavedScript] = useState(false);
  const [deviceId, setDeviceId] = useState('');

  useEffect(() => {
    initializeAndFetch();
  }, [id]);

  const initializeAndFetch = async () => {
    try {
      let storedDeviceId = await AsyncStorage.getItem('device_id');
      if (!storedDeviceId) {
        storedDeviceId = `device_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        await AsyncStorage.setItem('device_id', storedDeviceId);
      }
      setDeviceId(storedDeviceId);

      const response = await axios.get(`${BACKEND_URL}/api/scenario/${id}`);
      setScenario(response.data);
    } catch (error) {
      console.error('Error fetching scenario:', error);
    } finally {
      setLoading(false);
    }
  };

  const copyScript = async () => {
    if (!scenario) return;
    await Clipboard.setStringAsync(scenario.script);
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    setCopiedScript(true);
    setTimeout(() => setCopiedScript(false), 2000);
  };

  const saveScript = async () => {
    if (!scenario || !deviceId) return;
    try {
      await axios.post(`${BACKEND_URL}/api/scripts/saved`, {
        device_id: deviceId,
        title: scenario.question,
        content: scenario.script,
        category: scenario.category
      });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setSavedScript(true);
      Alert.alert('Saved!', 'Script added to your saved collection.');
    } catch (error) {
      console.error('Error saving script:', error);
      Alert.alert('Error', 'Could not save script.');
    }
  };

  if (loading || !scenario) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading...</Text>
        </View>
      </SafeAreaView>
    );
  }

  const color = CATEGORY_COLORS[scenario.category] || '#3B82F6';

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Ionicons name="arrow-back" size={24} color="#FFFFFF" />
        </TouchableOpacity>
        
        <View style={[styles.categoryBadge, { backgroundColor: `${color}20` }]}>
          <Text style={[styles.categoryText, { color }]}>{scenario.category}</Text>
        </View>
      </View>

      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Question */}
        <Animated.View entering={FadeInUp.duration(400)}>
          <Text style={styles.question}>{scenario.question}</Text>
        </Animated.View>

        {/* Short Answer */}
        <Animated.View entering={FadeInUp.duration(400).delay(100)} style={[styles.section, styles.answerSection, { borderLeftColor: color }]}>
          <Text style={styles.sectionLabel}>Quick Answer</Text>
          <Text style={styles.shortAnswer}>{scenario.short_answer}</Text>
        </Animated.View>

        {/* Explanation */}
        <Animated.View entering={FadeInUp.duration(400).delay(200)} style={styles.section}>
          <View style={styles.sectionHeader}>
            <Ionicons name="information-circle" size={20} color="#9CA3AF" />
            <Text style={styles.sectionTitle}>What This Usually Means</Text>
          </View>
          <Text style={styles.explanation}>{scenario.explanation}</Text>
        </Animated.View>

        {/* Next Steps */}
        <Animated.View entering={FadeInUp.duration(400).delay(400)} style={styles.section}>
          <View style={styles.sectionHeader}>
            <Ionicons name="footsteps" size={20} color="#9CA3AF" />
            <Text style={styles.sectionTitle}>Next Steps</Text>
          </View>
          <View style={styles.stepsList}>
            {scenario.next_steps.map((step, index) => (
              <View key={index} style={styles.stepItem}>
                <View style={[styles.stepNumber, { backgroundColor: `${color}20` }]}>
                  <Text style={[styles.stepNumberText, { color }]}>{index + 1}</Text>
                </View>
                <Text style={styles.stepText}>{step}</Text>
              </View>
            ))}
          </View>
        </Animated.View>

        {/* Legal Quotes */}
        {scenario.legal_quotes && scenario.legal_quotes.length > 0 && (
          <Animated.View entering={FadeInUp.duration(400).delay(450)} style={styles.section}>
            <View style={styles.sectionHeader}>
              <Ionicons name="book" size={20} color="#C4B5FD" />
              <Text style={styles.sectionTitle}>What the Law Says</Text>
            </View>
            {scenario.legal_quotes.map((quote, index) => {
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
                      <Ionicons name="link" size={12} color="#6B7280" />
                      <Text style={styles.legalSourceText}>{quote.source}</Text>
                    </View>
                  </LinearGradient>
                </View>
              );
            })}
          </Animated.View>
        )}

        {/* Disclaimer */}
        <Animated.View entering={FadeIn.duration(400).delay(500)} style={styles.disclaimerBox}>
          <Ionicons name="warning" size={20} color="#F59E0B" />
          <View style={styles.disclaimerContent}>
            <Text style={styles.disclaimerTitle}>Remember</Text>
            <Text style={styles.disclaimerText}>
              Laws vary by location. This is educational information, not legal advice. For serious legal issues, please consult a qualified attorney.
            </Text>
          </View>
        </Animated.View>

        {/* Ask AI */}
        <TouchableOpacity 
          style={styles.askAiButton}
          onPress={() => router.push('/(tabs)/chat')}
        >
          <Ionicons name="chatbubbles" size={20} color="#3B82F6" />
          <Text style={styles.askAiText}>Have more questions? Ask AI</Text>
          <Ionicons name="arrow-forward" size={18} color="#C4B5FD" />
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0D0D14',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#FFFFFF',
    fontSize: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#14141E',
    justifyContent: 'center',
    alignItems: 'center',
  },
  categoryBadge: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 12,
  },
  categoryText: {
    fontSize: 13,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingTop: 8,
  },
  question: {
    fontSize: 26,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 24,
    lineHeight: 34,
  },
  section: {
    marginBottom: 24,
  },
  answerSection: {
    backgroundColor: '#14141E',
    borderRadius: 16,
    padding: 16,
    borderLeftWidth: 4,
  },
  sectionLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#9CA3AF',
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  shortAnswer: {
    fontSize: 17,
    fontWeight: '600',
    color: '#FFFFFF',
    lineHeight: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginLeft: 10,
  },
  explanation: {
    fontSize: 15,
    color: '#D1D5DB',
    lineHeight: 24,
  },
  scriptContainer: {
    backgroundColor: '#14141E',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1E1E2E',
  },
  scriptQuote: {
    fontSize: 17,
    color: '#FFFFFF',
    fontStyle: 'italic',
    lineHeight: 26,
    marginBottom: 16,
  },
  scriptActions: {
    flexDirection: 'row',
  },
  scriptButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1E1E2E',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 10,
    marginRight: 10,
  },
  scriptButtonActive: {
    backgroundColor: '#14141E',
    borderWidth: 1,
    borderColor: '#1E1E2E',
  },
  scriptButtonText: {
    fontSize: 14,
    color: '#FFFFFF',
    marginLeft: 6,
    fontWeight: '500',
  },
  scriptButtonTextActive: {
    color: '#10B981',
  },
  stepsList: {
    backgroundColor: '#14141E',
    borderRadius: 16,
    padding: 4,
  },
  stepItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 12,
  },
  stepNumber: {
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  stepNumberText: {
    fontSize: 14,
    fontWeight: '700',
  },
  stepText: {
    flex: 1,
    fontSize: 15,
    color: '#D1D5DB',
    lineHeight: 22,
  },
  disclaimerBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#14141E',
    borderRadius: 16,
    padding: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#F59E0B30',
  },
  disclaimerContent: {
    flex: 1,
    marginLeft: 12,
  },
  disclaimerTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#F59E0B',
    marginBottom: 4,
  },
  disclaimerText: {
    fontSize: 13,
    color: '#9CA3AF',
    lineHeight: 18,
  },
  askAiButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#14141E',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#C4B5FD30',
    marginBottom: 20,
  },
  askAiText: {
    fontSize: 15,
    color: '#C4B5FD',
    fontWeight: '500',
    marginHorizontal: 8,
  },
  // Legal Quotes
  legalQuoteCard: {
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#1E1E2E',
  },
  legalQuoteGradient: {
    padding: 16,
  },
  legalQuoteHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  legalTypeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  legalTypeText: {
    fontSize: 11,
    fontWeight: '600',
    marginLeft: 5,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  legalQuoteText: {
    fontSize: 15,
    color: '#E5E7EB',
    lineHeight: 24,
    fontStyle: 'italic',
    marginBottom: 10,
  },
  legalSourceRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  legalSourceText: {
    fontSize: 12,
    color: '#6B7280',
    marginLeft: 6,
    flex: 1,
    fontWeight: '500',
  },
});
