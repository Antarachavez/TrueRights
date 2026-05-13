import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, TextInput, ScrollView, Modal, KeyboardAvoidingView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LinearGradient } from 'expo-linear-gradient';
import axios from 'axios';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function OnboardingScreen() {
  const router = useRouter();
  const [checking, setChecking] = useState(true);
  const [selectedState, setSelectedState] = useState('');
  const [contactName, setContactName] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [showStatePicker, setShowStatePicker] = useState(false);
  const [states, setStates] = useState<string[]>([]);
  const [stateSearch, setStateSearch] = useState('');

  useEffect(() => {
    checkOnboarding();
    fetchStates();
  }, []);

  const checkOnboarding = async () => {
    try {
      const completed = await AsyncStorage.getItem('onboarding_completed');
      if (completed === 'true') router.replace('/(tabs)/home');
      else setChecking(false);
    } catch (e) { setChecking(false); }
  };

  const fetchStates = async () => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/states`);
      setStates(res.data);
    } catch (e) {
      setStates(['Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut','Delaware','Florida','Georgia','Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Kentucky','Louisiana','Maine','Maryland','Massachusetts','Michigan','Minnesota','Mississippi','Missouri','Montana','Nebraska','Nevada','New Hampshire','New Jersey','New Mexico','New York','North Carolina','North Dakota','Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island','South Carolina','South Dakota','Tennessee','Texas','Utah','Vermont','Virginia','Washington','West Virginia','Wisconsin','Wyoming','District of Columbia']);
    }
  };

  const filteredStates = stateSearch.trim()
    ? states.filter(s => s.toLowerCase().includes(stateSearch.toLowerCase()))
    : states;

  const handleContinue = async () => {
    try {
      await AsyncStorage.setItem('onboarding_completed', 'true');
      if (selectedState) await AsyncStorage.setItem('user_state', selectedState);
      if (contactName) await AsyncStorage.setItem('emergency_name', contactName);
      if (contactPhone) await AsyncStorage.setItem('emergency_phone', contactPhone);

      // Save device ID
      let deviceId = await AsyncStorage.getItem('device_id');
      if (!deviceId) {
        deviceId = `device_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        await AsyncStorage.setItem('device_id', deviceId);
      }

      // Save to backend
      try {
        await axios.post(`${BACKEND_URL}/api/preferences`, {
          device_id: deviceId,
          state: selectedState || null,
          emergency_contact_name: contactName || null,
          emergency_contact_phone: contactPhone || null,
          onboarding_completed: true,
        });
      } catch (e) { /* non-critical */ }
    } catch (e) {
      console.error('Error saving onboarding:', e);
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
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
      >
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Header */}
          <View style={styles.headerSection}>
            <View style={styles.logoRow}>
              <LinearGradient colors={['#8B5CF6', '#A78BFA']} style={styles.logoCircle} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
                <Ionicons name="shield-checkmark" size={32} color="#FFFFFF" />
              </LinearGradient>
            </View>
            <Text style={styles.title}>Know Your Rights</Text>
            <Text style={styles.subtitle}>Let's set up a few things so the app works best for you</Text>
          </View>

          {/* State Selection */}
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Ionicons name="location" size={18} color="#3B82F6" />
              <Text style={styles.sectionTitle}>Your State</Text>
            </View>
            <Text style={styles.sectionDesc}>Laws vary by state. This helps us give accurate info.</Text>
            <TouchableOpacity
              style={styles.selector}
              onPress={() => setShowStatePicker(true)}
              activeOpacity={0.7}
            >
              <Text style={selectedState ? styles.selectorText : styles.selectorPlaceholder}>
                {selectedState || 'Tap to select your state'}
              </Text>
              <Ionicons name="chevron-down" size={20} color="#94A3B8" />
            </TouchableOpacity>
          </View>

          {/* Emergency Contact */}
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Ionicons name="call" size={18} color="#EF4444" />
              <Text style={styles.sectionTitle}>Emergency Contact</Text>
            </View>
            <Text style={styles.sectionDesc}>Someone who can be quickly notified in Emergency Mode.</Text>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Contact Name</Text>
              <TextInput
                style={styles.textInput}
                placeholder="e.g., Mom, Dad, Trusted Adult"
                placeholderTextColor="#94A3B8"
                value={contactName}
                onChangeText={setContactName}
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Phone Number</Text>
              <TextInput
                style={styles.textInput}
                placeholder="e.g., (555) 123-4567"
                placeholderTextColor="#94A3B8"
                value={contactPhone}
                onChangeText={setContactPhone}
                keyboardType="phone-pad"
              />
            </View>
          </View>

          {/* Info Note */}
          <View style={styles.infoBox}>
            <Ionicons name="information-circle" size={18} color="#64748B" />
            <Text style={styles.infoText}>You can always change these later in Settings. All fields are optional.</Text>
          </View>
        </ScrollView>

        {/* Continue Button */}
        <View style={styles.bottomContainer}>
          <TouchableOpacity style={styles.continueButton} onPress={handleContinue} activeOpacity={0.85}>
            <LinearGradient colors={['#8B5CF6', '#7C3AED']} style={styles.continueGradient} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}>
              <Text style={styles.continueText}>Continue</Text>
              <Ionicons name="arrow-forward" size={18} color="#FFFFFF" />
            </LinearGradient>
          </TouchableOpacity>
          <Text style={styles.disclaimer}>Educational information only. Not legal advice.</Text>
        </View>
      </KeyboardAvoidingView>

      {/* State Picker Modal */}
      <Modal
        visible={showStatePicker}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowStatePicker(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Select Your State</Text>
              <TouchableOpacity onPress={() => { setShowStatePicker(false); setStateSearch(''); }}>
                <Ionicons name="close" size={24} color="#374151" />
              </TouchableOpacity>
            </View>
            <View style={styles.modalSearch}>
              <Ionicons name="search" size={18} color="#94A3B8" />
              <TextInput
                style={styles.modalSearchInput}
                placeholder="Search states..."
                placeholderTextColor="#94A3B8"
                value={stateSearch}
                onChangeText={setStateSearch}
                autoFocus
              />
            </View>
            <ScrollView style={styles.statesList} keyboardShouldPersistTaps="handled">
              {filteredStates.map((state) => (
                <TouchableOpacity
                  key={state}
                  style={[styles.stateItem, selectedState === state && styles.stateItemSelected]}
                  onPress={() => {
                    setSelectedState(state);
                    setShowStatePicker(false);
                    setStateSearch('');
                  }}
                >
                  <Text style={[styles.stateItemText, selectedState === state && styles.stateItemTextSelected]}>{state}</Text>
                  {selectedState === state && <Ionicons name="checkmark" size={20} color="#3B82F6" />}
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FAFAFE' },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  scrollView: { flex: 1 },
  scrollContent: { paddingHorizontal: 24, paddingTop: 24, paddingBottom: 16 },

  headerSection: { alignItems: 'center', marginBottom: 28 },
  logoRow: { marginBottom: 16 },
  logoCircle: { width: 64, height: 64, borderRadius: 32, justifyContent: 'center', alignItems: 'center' },
  title: { fontSize: 26, fontWeight: '700', color: '#1E1B4B', marginBottom: 8, textAlign: 'center' },
  subtitle: { fontSize: 14, color: '#64748B', textAlign: 'center', lineHeight: 20 },

  section: { marginBottom: 24 },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 6 },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: '#1E1B4B', marginLeft: 8 },
  sectionDesc: { fontSize: 13, color: '#64748B', marginBottom: 12, lineHeight: 18 },

  selector: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    backgroundColor: '#FFFFFF', borderRadius: 12, padding: 16,
    borderWidth: 1, borderColor: '#F1F1F5',
  },
  selectorText: { fontSize: 15, color: '#1E1B4B' },
  selectorPlaceholder: { fontSize: 15, color: '#94A3B8' },

  inputGroup: { marginBottom: 14 },
  inputLabel: { fontSize: 13, color: '#64748B', marginBottom: 6 },
  textInput: {
    backgroundColor: '#FFFFFF', borderRadius: 12, padding: 14,
    fontSize: 15, color: '#1E1B4B',
    borderWidth: 1, borderColor: '#F1F1F5',
  },

  infoBox: {
    flexDirection: 'row', alignItems: 'flex-start',
    backgroundColor: '#FFFFFF', borderRadius: 12, padding: 14,
    borderWidth: 1, borderColor: '#F1F1F5',
  },
  infoText: { flex: 1, fontSize: 12, color: '#64748B', marginLeft: 10, lineHeight: 17 },

  bottomContainer: { paddingHorizontal: 24, paddingBottom: 16, paddingTop: 8 },
  continueButton: { borderRadius: 14, overflow: 'hidden', marginBottom: 12 },
  continueGradient: {
    paddingVertical: 16, borderRadius: 14, flexDirection: 'row',
    justifyContent: 'center', alignItems: 'center', gap: 8,
  },
  continueText: { color: '#FFFFFF', fontSize: 17, fontWeight: '600' },
  disclaimer: { fontSize: 11, color: '#94A3B8', textAlign: 'center' },

  // Modal
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
  modalContent: { backgroundColor: '#FFFFFF', borderTopLeftRadius: 24, borderTopRightRadius: 24, maxHeight: '70%' },
  modalHeader: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    padding: 20, borderBottomWidth: 1, borderBottomColor: '#F1F1F5',
  },
  modalTitle: { fontSize: 18, fontWeight: '600', color: '#1E1B4B' },
  modalSearch: {
    flexDirection: 'row', alignItems: 'center',
    margin: 16, marginBottom: 8, padding: 12,
    backgroundColor: '#F8F9FA', borderRadius: 10,
  },
  modalSearchInput: { flex: 1, fontSize: 15, color: '#1E1B4B', marginLeft: 8 },
  statesList: { paddingHorizontal: 8, paddingBottom: 20 },
  stateItem: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    padding: 14, borderRadius: 10,
  },
  stateItemSelected: { backgroundColor: '#3B82F610' },
  stateItemText: { fontSize: 15, color: '#374151' },
  stateItemTextSelected: { color: '#3B82F6', fontWeight: '600' },
});
