import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Clipboard from 'expo-clipboard';
import * as Haptics from 'expo-haptics';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import Animated, { FadeInUp, FadeIn } from 'react-native-reanimated';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface ScenarioDetail {
  id: string;
  category: string;
  question: string;
  short_answer: string;
  explanation: string;
  script: string;
  next_steps: string[];
}

const CATEGORY_COLORS: { [key: string]: string } = {
  school: '#3B82F6',
  work: '#F97316',
  housing: '#10B981',
  police: '#EF4444',
  online: '#8B5CF6',
  public: '#14B8A6',
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

        {/* Script */}
        <Animated.View entering={FadeInUp.duration(400).delay(300)} style={styles.section}>
          <View style={styles.sectionHeader}>
            <Ionicons name="chatbubble-ellipses" size={20} color="#9CA3AF" />
            <Text style={styles.sectionTitle}>What You Can Say</Text>
          </View>
          <View style={styles.scriptContainer}>
            <Text style={styles.scriptQuote}>"{scenario.script}"</Text>
            <View style={styles.scriptActions}>
              <TouchableOpacity 
                style={[styles.scriptButton, copiedScript && styles.scriptButtonActive]}
                onPress={copyScript}
              >
                <Ionicons 
                  name={copiedScript ? "checkmark" : "copy-outline"} 
                  size={18} 
                  color={copiedScript ? "#10B981" : "#FFFFFF"} 
                />
                <Text style={[styles.scriptButtonText, copiedScript && styles.scriptButtonTextActive]}>
                  {copiedScript ? 'Copied!' : 'Copy'}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.scriptButton, savedScript && styles.scriptButtonActive]}
                onPress={saveScript}
                disabled={savedScript}
              >
                <Ionicons 
                  name={savedScript ? "bookmark" : "bookmark-outline"} 
                  size={18} 
                  color={savedScript ? "#3B82F6" : "#FFFFFF"} 
                />
                <Text style={[styles.scriptButtonText, savedScript && { color: '#3B82F6' }]}>
                  {savedScript ? 'Saved' : 'Save'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
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
          <Ionicons name="arrow-forward" size={18} color="#3B82F6" />
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
    borderColor: '#3B82F630',
    marginBottom: 20,
  },
  askAiText: {
    fontSize: 15,
    color: '#3B82F6',
    fontWeight: '500',
    marginHorizontal: 8,
  },
});
