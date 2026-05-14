import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, Alert, Platform, Modal, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Location from 'expo-location';
import axios from 'axios';
import { useLanguage } from '../../utils/LanguageContext';
import { LANGUAGES, Language } from '../../utils/i18n';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function SettingsScreen() {
  const { lang, setLanguage, t } = useLanguage();
  const [deviceId, setDeviceId] = useState('');
  const [selectedState, setSelectedState] = useState<string | null>(null);
  const [emergencyName, setEmergencyName] = useState('');
  const [emergencyPhone, setEmergencyPhone] = useState('');
  const [states, setStates] = useState<string[]>([]);
  const [showStateModal, setShowStateModal] = useState(false);
  const [detectingLocation, setDetectingLocation] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    initializeSettings();
  }, []);

  const initializeSettings = async () => {
    try {
      let storedDeviceId = await AsyncStorage.getItem('device_id');
      if (!storedDeviceId) {
        storedDeviceId = `device_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        await AsyncStorage.setItem('device_id', storedDeviceId);
      }
      setDeviceId(storedDeviceId);

      const savedState = await AsyncStorage.getItem('user_state');
      const savedName = await AsyncStorage.getItem('emergency_name');
      const savedPhone = await AsyncStorage.getItem('emergency_phone');
      
      if (savedState) setSelectedState(savedState);
      if (savedName) setEmergencyName(savedName);
      if (savedPhone) setEmergencyPhone(savedPhone);

      const response = await axios.get(`${BACKEND_URL}/api/states`);
      setStates(response.data);
    } catch (error) {
      console.error('Error initializing settings:', error);
    }
  };

  const detectLocation = async () => {
    setDetectingLocation(true);
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Denied', 'Location permission is needed to detect your state.');
        setDetectingLocation(false);
        return;
      }

      const location = await Location.getCurrentPositionAsync({});
      const [address] = await Location.reverseGeocodeAsync({
        latitude: location.coords.latitude,
        longitude: location.coords.longitude,
      });

      if (address?.region) {
        setSelectedState(address.region);
        await AsyncStorage.setItem('user_state', address.region);
        Alert.alert('Location Detected', `Your state has been set to ${address.region}`);
      } else {
        Alert.alert('Could Not Detect', 'Unable to determine your state. Please select manually.');
      }
    } catch (error) {
      console.error('Location error:', error);
      Alert.alert('Error', 'Could not detect your location. Please select your state manually.');
    }
    setDetectingLocation(false);
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      if (selectedState) await AsyncStorage.setItem('user_state', selectedState);
      if (emergencyName) await AsyncStorage.setItem('emergency_name', emergencyName);
      if (emergencyPhone) await AsyncStorage.setItem('emergency_phone', emergencyPhone);

      await axios.post(`${BACKEND_URL}/api/preferences`, {
        device_id: deviceId,
        state: selectedState,
        emergency_contact_name: emergencyName,
        emergency_contact_phone: emergencyPhone,
        onboarding_completed: true
      });

      Alert.alert('Saved', 'Your settings have been saved.');
    } catch (error) {
      console.error('Save error:', error);
      Alert.alert('Error', 'Could not save settings. Please try again.');
    }
    setSaving(false);
  };

  const clearAllData = () => {
    Alert.alert(
      'Clear All Data',
      'This will reset all your settings, saved scripts, and chat history. Are you sure?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            try {
              await AsyncStorage.clear();
              await axios.delete(`${BACKEND_URL}/api/chat/history/${deviceId}`);
              setSelectedState(null);
              setEmergencyName('');
              setEmergencyPhone('');
              Alert.alert('Cleared', 'All data has been cleared.');
            } catch (error) {
              console.error('Clear error:', error);
            }
          }
        }
      ]
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>{t('settings.title')}</Text>
        <Text style={styles.headerSubtitle}>{t('settings.subtitle')}</Text>
      </View>

      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Language Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('settings.language')}</Text>
          <View style={{ gap: 8 }}>
            {LANGUAGES.map((language) => (
              <TouchableOpacity
                key={language.code}
                style={[styles.stateSelector, lang === language.code && { borderColor: '#1B2A4A', borderWidth: 1.5 }]}
                onPress={() => setLanguage(language.code)}
              >
                <View style={styles.stateSelectorContent}>
                  <Text style={{ fontSize: 22, marginRight: 4 }}>{language.flag}</Text>
                  <Text style={styles.stateSelectorText}>{language.nativeName}</Text>
                </View>
                {lang === language.code && <Ionicons name="checkmark-circle" size={22} color="#1B2A4A" />}
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Location Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('settings.yourLocation')}</Text>
          <Text style={styles.sectionDescription}>
            {t('settings.locationDesc')}
          </Text>
          
          <TouchableOpacity 
            style={styles.stateSelector}
            onPress={() => setShowStateModal(true)}
          >
            <View style={styles.stateSelectorContent}>
              <Ionicons name="location" size={20} color="#1B2A4A" />
              <Text style={styles.stateSelectorText}>
                {selectedState || 'Select your state'}
              </Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#94A3B8" />
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.detectButton}
            onPress={detectLocation}
            disabled={detectingLocation}
          >
            {detectingLocation ? (
              <ActivityIndicator size="small" color="#1B2A4A" />
            ) : (
              <>
                <Ionicons name="navigate" size={18} color="#1B2A4A" />
                <Text style={styles.detectButtonText}>Detect my location</Text>
              </>
            )}
          </TouchableOpacity>
        </View>

        {/* Emergency Contact Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('settings.emergencyContact')}</Text>
          <Text style={styles.sectionDescription}>
            This contact can be quickly notified in Emergency Mode.
          </Text>
          
          <View style={styles.inputContainer}>
            <Text style={styles.inputLabel}>Contact Name</Text>
            <TextInput
              style={styles.textInput}
              placeholder="e.g., Mom, Dad, Trusted Adult"
              placeholderTextColor="#94A3B8"
              value={emergencyName}
              onChangeText={setEmergencyName}
            />
          </View>

          <View style={styles.inputContainer}>
            <Text style={styles.inputLabel}>Phone Number</Text>
            <TextInput
              style={styles.textInput}
              placeholder="e.g., 555-123-4567"
              placeholderTextColor="#94A3B8"
              value={emergencyPhone}
              onChangeText={setEmergencyPhone}
              keyboardType="phone-pad"
            />
          </View>
        </View>

        {/* Save Button */}
        <TouchableOpacity 
          style={styles.saveButton}
          onPress={saveSettings}
          disabled={saving}
        >
          {saving ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <Text style={styles.saveButtonText}>{t('settings.saveSettings')}</Text>
          )}
        </TouchableOpacity>

        {/* Data & Privacy Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('settings.dataPrivacy')}</Text>
          
          <TouchableOpacity style={styles.dangerButton} onPress={clearAllData}>
            <Ionicons name="trash-outline" size={20} color="#EF4444" />
            <Text style={styles.dangerButtonText}>{t('settings.clearAll')}</Text>
          </TouchableOpacity>
        </View>

        {/* About Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('settings.about')}</Text>
          <View style={styles.aboutItem}>
            <Text style={styles.aboutLabel}>{t('settings.version')}</Text>
            <Text style={styles.aboutValue}>1.0.0</Text>
          </View>
          <View style={styles.disclaimerBox}>
            <Ionicons name="alert-circle" size={20} color="#F59E0B" />
            <Text style={styles.disclaimerText}>
              This app provides educational information only. It is not legal advice and should not be relied upon as such. Always consult a qualified attorney for legal matters.
            </Text>
          </View>
        </View>
      </ScrollView>

      {/* State Selection Modal */}
      <Modal
        visible={showStateModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowStateModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Select Your State</Text>
              <TouchableOpacity onPress={() => setShowStateModal(false)}>
                <Ionicons name="close" size={24} color="#374151" />
              </TouchableOpacity>
            </View>
            <ScrollView style={styles.statesList}>
              {states.map((state) => (
                <TouchableOpacity
                  key={state}
                  style={[
                    styles.stateItem,
                    selectedState === state && styles.stateItemSelected
                  ]}
                  onPress={() => {
                    setSelectedState(state);
                    setShowStateModal(false);
                  }}
                >
                  <Text style={[
                    styles.stateItemText,
                    selectedState === state && styles.stateItemTextSelected
                  ]}>{state}</Text>
                  {selectedState === state && (
                    <Ionicons name="checkmark" size={20} color="#1B2A4A" />
                  )}
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
  container: {
    flex: 1,
    backgroundColor: '#F5F0EB',
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 16,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1B2A4A',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#5E6E7D',
    marginTop: 4,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingTop: 4,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1B2A4A',
    marginBottom: 8,
  },
  sectionDescription: {
    fontSize: 13,
    color: '#5E6E7D',
    marginBottom: 16,
    lineHeight: 18,
  },
  stateSelector: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#FFFDF9',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#EDE9E3',
  },
  stateSelectorContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  stateSelectorText: {
    fontSize: 15,
    color: '#1B2A4A',
    marginLeft: 12,
  },
  detectButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 12,
    padding: 12,
  },
  detectButtonText: {
    fontSize: 14,
    color: '#1B2A4A',
    marginLeft: 8,
  },
  inputContainer: {
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 13,
    color: '#5E6E7D',
    marginBottom: 8,
  },
  textInput: {
    backgroundColor: '#FFFDF9',
    borderRadius: 12,
    padding: 16,
    color: '#1B2A4A',
    fontSize: 15,
    borderWidth: 1,
    borderColor: '#EDE9E3',
  },
  saveButton: {
    backgroundColor: '#C45C5C',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginBottom: 24,
  },
  saveButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  dangerButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFDF9',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#EF444430',
  },
  dangerButtonText: {
    fontSize: 15,
    color: '#EF4444',
    marginLeft: 8,
  },
  aboutItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#FFFDF9',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#EDE9E3',
  },
  aboutLabel: {
    fontSize: 15,
    color: '#5E6E7D',
  },
  aboutValue: {
    fontSize: 15,
    color: '#1B2A4A',
    fontWeight: '500',
  },
  disclaimerBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#FFFDF9',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#EDE9E3',
  },
  disclaimerText: {
    flex: 1,
    fontSize: 13,
    color: '#5E6E7D',
    marginLeft: 12,
    lineHeight: 18,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#FFFDF9',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '70%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#EDE9E3',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1B2A4A',
  },
  statesList: {
    padding: 8,
  },
  stateItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
  },
  stateItemSelected: {
    backgroundColor: '#1B2A4A10',
  },
  stateItemText: {
    fontSize: 15,
    color: '#374151',
  },
  stateItemTextSelected: {
    color: '#1B2A4A',
    fontWeight: '600',
  },
});
