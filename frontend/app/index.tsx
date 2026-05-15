import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, TextInput, ScrollView, Modal, KeyboardAvoidingView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LinearGradient } from 'expo-linear-gradient';
import axios from 'axios';
import { useLanguage } from '../utils/LanguageContext';
import { LANGUAGES, Language } from '../utils/i18n';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function OnboardingScreen() {
  const router = useRouter();
  const { lang, setLanguage, t } = useLanguage();
  const [checking, setChecking] = useState(true);
  const [step, setStep] = useState<'language' | 'info'>('language');
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

  const selectLanguage = async (code: Language) => {
    await setLanguage(code);
    setStep('info');
  };

  const handleContinue = async () => {
    try {
      await AsyncStorage.setItem('onboarding_completed', 'true');
      if (selectedState) await AsyncStorage.setItem('user_state', selectedState);
      if (contactName) await AsyncStorage.setItem('emergency_name', contactName);
      if (contactPhone) await AsyncStorage.setItem('emergency_phone', contactPhone);
      let deviceId = await AsyncStorage.getItem('device_id');
      if (!deviceId) {
        deviceId = `device_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        await AsyncStorage.setItem('device_id', deviceId);
      }
      try {
        await axios.post(`${BACKEND_URL}/api/preferences`, {
          device_id: deviceId, state: selectedState || null,
          emergency_contact_name: contactName || null,
          emergency_contact_phone: contactPhone || null,
          language: lang, onboarding_completed: true,
        });
      } catch (e) {}
    } catch (e) { console.error('Error saving onboarding:', e); }
    router.replace('/(tabs)/home');
  };

  if (checking) return (
    <View style={styles.container}>
      <View style={styles.loadingContainer}>
        <Ionicons name="shield-checkmark" size={48} color="#C45C5C" />
      </View>
    </View>
  );

  // STEP 1: Language Selection
  if (step === 'language') {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.langPage}>
          <View style={styles.langHeader}>
            <LinearGradient colors={['#1B2A4A', '#2A3F6A']} style={styles.logoCircle} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
              <Ionicons name="shield-checkmark" size={32} color="#FFFFFF" />
            </LinearGradient>
            <Text style={styles.title}>True Rights</Text>
            <Text style={styles.langSubtitle}>{t('onboarding.chooseLanguage')}</Text>
            <Text style={styles.langSubtitleSmall}>{t('onboarding.languageSub')}</Text>
          </View>

          <View style={styles.langOptions}>
            {LANGUAGES.map((language) => (
              <TouchableOpacity
                key={language.code}
                style={[styles.langCard, lang === language.code && styles.langCardSelected]}
                onPress={() => selectLanguage(language.code)}
                activeOpacity={0.7}
              >
                <Text style={styles.langFlag}>{language.flag}</Text>
                <View style={styles.langTextContainer}>
                  <Text style={[styles.langName, lang === language.code && styles.langNameSelected]}>{language.nativeName}</Text>
                  <Text style={styles.langNameEn}>{language.name}</Text>
                </View>
                {lang === language.code && (
                  <Ionicons name="checkmark-circle" size={24} color="#1B2A4A" />
                )}
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </SafeAreaView>
    );
  }

  // STEP 2: Info Gathering
  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
          <View style={styles.headerSection}>
            <TouchableOpacity style={styles.backToLang} onPress={() => setStep('language')}>
              <Ionicons name="chevron-back" size={20} color="#5E6E7D" />
              <Text style={styles.backToLangText}>{LANGUAGES.find(l => l.code === lang)?.flag} {LANGUAGES.find(l => l.code === lang)?.nativeName}</Text>
            </TouchableOpacity>
            <Text style={styles.title}>{t('app.name')}</Text>
            <Text style={styles.subtitle}>{t('onboarding.subtitle')}</Text>
          </View>

          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Ionicons name="location" size={18} color="#1B2A4A" />
              <Text style={styles.sectionTitle}>{t('onboarding.yourState')}</Text>
            </View>
            <Text style={styles.sectionDesc}>{t('onboarding.stateDesc')}</Text>
            <TouchableOpacity style={styles.selector} onPress={() => setShowStatePicker(true)} activeOpacity={0.7}>
              <Text style={selectedState ? styles.selectorText : styles.selectorPlaceholder}>
                {selectedState || t('onboarding.selectState')}
              </Text>
              <Ionicons name="chevron-down" size={20} color="#9BA5AD" />
            </TouchableOpacity>
          </View>

          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Ionicons name="call" size={18} color="#C45C5C" />
              <Text style={styles.sectionTitle}>{t('onboarding.emergencyContact')}</Text>
            </View>
            <Text style={styles.sectionDesc}>{t('onboarding.emergencyDesc')}</Text>
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>{t('onboarding.contactName')}</Text>
              <TextInput style={styles.textInput} placeholder={t('onboarding.contactNamePlaceholder')} placeholderTextColor="#9BA5AD" value={contactName} onChangeText={setContactName} />
            </View>
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>{t('onboarding.phoneNumber')}</Text>
              <TextInput style={styles.textInput} placeholder={t('onboarding.phonePlaceholder')} placeholderTextColor="#9BA5AD" value={contactPhone} onChangeText={setContactPhone} keyboardType="phone-pad" />
            </View>
          </View>

          <View style={styles.infoBox}>
            <Ionicons name="information-circle" size={18} color="#5E6E7D" />
            <Text style={styles.infoText}>{t('onboarding.infoNote')}</Text>
          </View>
        </ScrollView>

        <View style={styles.bottomContainer}>
          <TouchableOpacity style={styles.continueButton} onPress={handleContinue} activeOpacity={0.85}>
            <LinearGradient colors={['#1B2A4A', '#2A3F6A']} style={styles.continueGradient} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}>
              <Text style={styles.continueText}>{t('onboarding.continue')}</Text>
              <Ionicons name="arrow-forward" size={18} color="#FFFFFF" />
            </LinearGradient>
          </TouchableOpacity>
          <Text style={styles.disclaimer}>{t('onboarding.disclaimer')}</Text>
        </View>
      </KeyboardAvoidingView>

      <Modal visible={showStatePicker} animationType="slide" transparent={true} onRequestClose={() => setShowStatePicker(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>{t('onboarding.selectStateTitle')}</Text>
              <TouchableOpacity onPress={() => { setShowStatePicker(false); setStateSearch(''); }}>
                <Ionicons name="close" size={24} color="#374151" />
              </TouchableOpacity>
            </View>
            <View style={styles.modalSearch}>
              <Ionicons name="search" size={18} color="#9BA5AD" />
              <TextInput style={styles.modalSearchInput} placeholder={t('onboarding.searchStates')} placeholderTextColor="#9BA5AD" value={stateSearch} onChangeText={setStateSearch} autoFocus />
            </View>
            <ScrollView style={styles.statesList} keyboardShouldPersistTaps="handled">
              {filteredStates.map((state) => (
                <TouchableOpacity key={state} style={[styles.stateItem, selectedState === state && styles.stateItemSelected]} onPress={() => { setSelectedState(state); setShowStatePicker(false); setStateSearch(''); }}>
                  <Text style={[styles.stateItemText, selectedState === state && styles.stateItemTextSelected]}>{state}</Text>
                  {selectedState === state && <Ionicons name="checkmark" size={20} color="#1B2A4A" />}
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
  container: { flex: 1, backgroundColor: '#F5F0EB' },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },

  // Language page
  langPage: { flex: 1, paddingHorizontal: 24, justifyContent: 'center' },
  langHeader: { alignItems: 'center', marginBottom: 36 },
  logoCircle: { width: 64, height: 64, borderRadius: 32, justifyContent: 'center', alignItems: 'center', marginBottom: 16 },
  langSubtitle: { fontSize: 18, fontWeight: '500', color: '#1B2A4A', marginTop: 8 },
  langSubtitleSmall: { fontSize: 12, color: '#9BA5AD', marginTop: 6, textAlign: 'center' },
  langOptions: { gap: 10 },
  langCard: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFFDF9',
    borderRadius: 14, padding: 16, borderWidth: 1.5, borderColor: '#EDE9E3',
  },
  langCardSelected: { borderColor: '#1B2A4A', backgroundColor: '#F0EDE8' },
  langFlag: { fontSize: 28, marginRight: 14 },
  langTextContainer: { flex: 1 },
  langName: { fontSize: 17, fontWeight: '600', color: '#1B2A4A' },
  langNameSelected: { color: '#1B2A4A' },
  langNameEn: { fontSize: 13, color: '#9BA5AD', marginTop: 1 },

  // Info page
  scrollView: { flex: 1 },
  scrollContent: { paddingHorizontal: 24, paddingTop: 16, paddingBottom: 16 },
  headerSection: { marginBottom: 24 },
  backToLang: { flexDirection: 'row', alignItems: 'center', marginBottom: 16 },
  backToLangText: { fontSize: 14, color: '#5E6E7D', marginLeft: 4 },
  title: { fontSize: 26, fontWeight: '700', color: '#1B2A4A', textAlign: 'center' },
  subtitle: { fontSize: 14, color: '#5E6E7D', textAlign: 'center', lineHeight: 20, marginTop: 6 },
  section: { marginBottom: 24 },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 6 },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: '#1B2A4A', marginLeft: 8 },
  sectionDesc: { fontSize: 13, color: '#5E6E7D', marginBottom: 12, lineHeight: 18 },
  selector: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#FFFDF9', borderRadius: 12, padding: 16, borderWidth: 1, borderColor: '#EDE9E3' },
  selectorText: { fontSize: 15, color: '#1B2A4A' },
  selectorPlaceholder: { fontSize: 15, color: '#9BA5AD' },
  inputGroup: { marginBottom: 14 },
  inputLabel: { fontSize: 13, color: '#5E6E7D', marginBottom: 6 },
  textInput: { backgroundColor: '#FFFDF9', borderRadius: 12, padding: 14, fontSize: 15, color: '#1B2A4A', borderWidth: 1, borderColor: '#EDE9E3' },
  infoBox: { flexDirection: 'row', alignItems: 'flex-start', backgroundColor: '#FFFDF9', borderRadius: 12, padding: 14, borderWidth: 1, borderColor: '#EDE9E3' },
  infoText: { flex: 1, fontSize: 12, color: '#5E6E7D', marginLeft: 10, lineHeight: 17 },
  bottomContainer: { paddingHorizontal: 24, paddingBottom: 16, paddingTop: 8 },
  continueButton: { borderRadius: 14, overflow: 'hidden', marginBottom: 12 },
  continueGradient: { paddingVertical: 16, borderRadius: 14, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8 },
  continueText: { color: '#FFFFFF', fontSize: 17, fontWeight: '600' },
  disclaimer: { fontSize: 11, color: '#9BA5AD', textAlign: 'center' },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
  modalContent: { backgroundColor: '#FFFFFF', borderTopLeftRadius: 24, borderTopRightRadius: 24, maxHeight: '70%' },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 20, borderBottomWidth: 1, borderBottomColor: '#EDE9E3' },
  modalTitle: { fontSize: 18, fontWeight: '600', color: '#1B2A4A' },
  modalSearch: { flexDirection: 'row', alignItems: 'center', margin: 16, marginBottom: 8, padding: 12, backgroundColor: '#F5F0EB', borderRadius: 10 },
  modalSearchInput: { flex: 1, fontSize: 15, color: '#1B2A4A', marginLeft: 8 },
  statesList: { paddingHorizontal: 8, paddingBottom: 20 },
  stateItem: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 14, borderRadius: 10 },
  stateItemSelected: { backgroundColor: '#F5F0EB' },
  stateItemText: { fontSize: 15, color: '#374151' },
  stateItemTextSelected: { color: '#1B2A4A', fontWeight: '600' },
});
