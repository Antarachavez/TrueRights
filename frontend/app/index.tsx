import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Dimensions, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Animated, { FadeIn, FadeInUp, FadeInDown } from 'react-native-reanimated';

const { width, height } = Dimensions.get('window');

export default function WelcomeScreen() {
  const router = useRouter();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    checkOnboarding();
  }, []);

  const checkOnboarding = async () => {
    try {
      const completed = await AsyncStorage.getItem('onboarding_completed');
      if (completed === 'true') {
        router.replace('/(tabs)/home');
      } else {
        setChecking(false);
      }
    } catch (e) {
      setChecking(false);
    }
  };

  const handleGetStarted = async () => {
    await AsyncStorage.setItem('onboarding_completed', 'true');
    router.replace('/(tabs)/home');
  };

  if (checking) {
    return (
      <View style={styles.container}>
        <View style={styles.loadingContainer}>
          <Ionicons name="shield-checkmark" size={60} color="#3B82F6" />
        </View>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Animated.View entering={FadeInUp.duration(800).delay(200)} style={styles.logoContainer}>
          <View style={styles.logoCircle}>
            <Ionicons name="shield-checkmark" size={60} color="#FFFFFF" />
          </View>
        </Animated.View>

        <Animated.View entering={FadeInUp.duration(800).delay(400)} style={styles.textContainer}>
          <Text style={styles.title}>Know Your Rights</Text>
          <Text style={styles.subtitle}>Quick, clear guidance for real-life situations</Text>
        </Animated.View>

        <Animated.View entering={FadeIn.duration(800).delay(600)} style={styles.featuresContainer}>
          <View style={styles.featureRow}>
            <View style={[styles.featureIcon, { backgroundColor: '#3B82F620' }]}>
              <Ionicons name="flash" size={24} color="#3B82F6" />
            </View>
            <View style={styles.featureText}>
              <Text style={styles.featureTitle}>Fast Answers</Text>
              <Text style={styles.featureDesc}>Get quick guidance when you need it most</Text>
            </View>
          </View>

          <View style={styles.featureRow}>
            <View style={[styles.featureIcon, { backgroundColor: '#10B98120' }]}>
              <Ionicons name="document-text" size={24} color="#10B981" />
            </View>
            <View style={styles.featureText}>
              <Text style={styles.featureTitle}>Ready Scripts</Text>
              <Text style={styles.featureDesc}>Words you can say in stressful moments</Text>
            </View>
          </View>

          <View style={styles.featureRow}>
            <View style={[styles.featureIcon, { backgroundColor: '#EF444420' }]}>
              <Ionicons name="alert-circle" size={24} color="#EF4444" />
            </View>
            <View style={styles.featureText}>
              <Text style={styles.featureTitle}>Emergency Mode</Text>
              <Text style={styles.featureDesc}>Stay calm and document what happens</Text>
            </View>
          </View>
        </Animated.View>

        <Animated.View entering={FadeInDown.duration(800).delay(800)} style={styles.bottomContainer}>
          <TouchableOpacity style={styles.startButton} onPress={handleGetStarted}>
            <Text style={styles.startButtonText}>Get Started</Text>
            <Ionicons name="arrow-forward" size={20} color="#FFFFFF" />
          </TouchableOpacity>

          <Text style={styles.disclaimer}>
            This app provides educational information only.{"\n"}It is not legal advice.
          </Text>
        </Animated.View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0F0F0F',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: 40,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 32,
  },
  logoCircle: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: '#3B82F6',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#3B82F6',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.4,
    shadowRadius: 16,
    elevation: 10,
  },
  textContainer: {
    alignItems: 'center',
    marginBottom: 40,
  },
  title: {
    fontSize: 32,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#9CA3AF',
    textAlign: 'center',
  },
  featuresContainer: {
    flex: 1,
    justifyContent: 'center',
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
    paddingHorizontal: 8,
  },
  featureIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  featureText: {
    flex: 1,
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  featureDesc: {
    fontSize: 14,
    color: '#9CA3AF',
  },
  bottomContainer: {
    paddingBottom: 20,
  },
  startButton: {
    backgroundColor: '#3B82F6',
    paddingVertical: 16,
    borderRadius: 16,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  startButtonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '600',
    marginRight: 8,
  },
  disclaimer: {
    fontSize: 12,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 18,
  },
});
