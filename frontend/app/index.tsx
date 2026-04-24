import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LinearGradient } from 'expo-linear-gradient';
import Animated, { FadeIn, FadeInUp } from 'react-native-reanimated';

export default function WelcomeScreen() {
  const router = useRouter();
  const [checking, setChecking] = useState(true);

  useEffect(() => { checkOnboarding(); }, []);

  const checkOnboarding = async () => {
    try {
      const completed = await AsyncStorage.getItem('onboarding_completed');
      if (completed === 'true') router.replace('/(tabs)/home');
      else setChecking(false);
    } catch (e) { setChecking(false); }
  };

  const handleGetStarted = async () => {
    try {
      await AsyncStorage.setItem('onboarding_completed', 'true');
    } catch (e) {
      console.error('Error saving onboarding state:', e);
    }
    router.replace('/(tabs)/home');
  };

  if (checking) return (
    <View style={styles.container}>
      <View style={styles.loadingContainer}>
        <Ionicons name="shield-checkmark" size={48} color="#8B5CF6" />
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Animated.View entering={FadeInUp.duration(800).delay(200)} style={styles.logoContainer}>
          <LinearGradient colors={['#8B5CF6', '#A78BFA']} style={styles.logoCircle} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
            <Ionicons name="shield-checkmark" size={48} color="#FFFFFF" />
          </LinearGradient>
        </Animated.View>

        <Animated.View entering={FadeInUp.duration(800).delay(400)} style={styles.textContainer}>
          <Text style={styles.title}>Know Your Rights</Text>
          <Text style={styles.subtitle}>Quick, clear guidance for real-life situations</Text>
        </Animated.View>

        <Animated.View entering={FadeIn.duration(800).delay(600)} style={styles.featuresContainer}>
          {[
            { icon: 'flash', color: '#8B5CF6', bg: '#8B5CF608', title: 'Fast Answers', desc: 'Get quick guidance when you need it most' },
            { icon: 'document-text', color: '#34D399', bg: '#34D39908', title: 'Ready Scripts', desc: 'Words you can say in stressful moments' },
            { icon: 'alert-circle', color: '#FB7185', bg: '#FB718508', title: 'Emergency Mode', desc: 'Stay calm and document what happens' },
          ].map((f, i) => (
            <View key={i} style={styles.featureRow}>
              <View style={[styles.featureIcon, { backgroundColor: f.bg }]}>
                <Ionicons name={f.icon as any} size={22} color={f.color} />
              </View>
              <View style={styles.featureText}>
                <Text style={styles.featureTitle}>{f.title}</Text>
                <Text style={styles.featureDesc}>{f.desc}</Text>
              </View>
            </View>
          ))}
        </Animated.View>

        <View style={styles.bottomContainer}>
          <TouchableOpacity style={styles.startButtonOuter} onPress={handleGetStarted} activeOpacity={0.85}>
            <LinearGradient colors={['#8B5CF6', '#7C3AED']} style={styles.startButton} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}>
              <Text style={styles.startButtonText}>Get Started</Text>
              <Ionicons name="arrow-forward" size={18} color="#FFFFFF" />
            </LinearGradient>
          </TouchableOpacity>
          <Text style={styles.disclaimer}>This app provides educational information only.{"\n"}It is not legal advice.</Text>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FAFAFE' },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  content: { flex: 1, paddingHorizontal: 28, paddingTop: 48 },
  logoContainer: { alignItems: 'center', marginBottom: 32 },
  logoCircle: { width: 96, height: 96, borderRadius: 48, justifyContent: 'center', alignItems: 'center' },
  textContainer: { alignItems: 'center', marginBottom: 40 },
  title: { fontSize: 30, fontWeight: '700', color: '#1E1B4B', marginBottom: 8, textAlign: 'center', letterSpacing: -0.5 },
  subtitle: { fontSize: 16, color: '#64748B', textAlign: 'center' },
  featuresContainer: { flex: 1, justifyContent: 'center' },
  featureRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 24, paddingHorizontal: 4 },
  featureIcon: { width: 44, height: 44, borderRadius: 12, justifyContent: 'center', alignItems: 'center', marginRight: 16 },
  featureText: { flex: 1 },
  featureTitle: { fontSize: 16, fontWeight: '600', color: '#1E1B4B', marginBottom: 2 },
  featureDesc: { fontSize: 14, color: '#94A3B8' },
  bottomContainer: { paddingBottom: 20 },
  startButtonOuter: { borderRadius: 16, overflow: 'hidden', marginBottom: 16 },
  startButton: { paddingVertical: 16, borderRadius: 16, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8 },
  startButtonText: { color: '#FFFFFF', fontSize: 17, fontWeight: '600' },
  disclaimer: { fontSize: 12, color: '#94A3B8', textAlign: 'center', lineHeight: 18 },
});
