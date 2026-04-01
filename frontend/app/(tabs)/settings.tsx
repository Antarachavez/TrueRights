import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, Alert, Switch, Platform, Modal, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Location from 'expo-location';
import axios from 'axios';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function SettingsScreen() {
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
      // Get device ID
      let storedDeviceId = await AsyncStorage.getItem('device_id');
      if (!storedDeviceId) {
        storedDeviceId = `device_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        await AsyncStorage.setItem('device_id', storedDeviceId);
      }
      setDeviceId(storedDeviceId);

      // Load saved settings
      const savedState = await AsyncStorage.getItem('user_state');
      const savedName = await AsyncStorage.getItem('emergency_name');
      const savedPhone = await AsyncStorage.getItem('emergency_phone');
      
      if (savedState) setSelectedState(savedState);
      if (savedName) setEmergencyName(savedName);
      if (savedPhone) setEmergencyPhone(savedPhone);

      // Fetch states list
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
      // Save locally
      if (selectedState) await AsyncStorage.setItem('user_state', selectedState);
      if (emergencyName) await AsyncStorage.setItem('emergency_name', emergencyName);
      if (emergencyPhone) await AsyncStorage.setItem('emergency_phone', emergencyPhone);

      // Save to backend
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
        <Text style={styles.headerTitle}>Settings</Text>
        <Text style={styles.headerSubtitle}>Customize your experience</Text>
      </View>

      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Location Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Your Location</Text>
          <Text style={styles.sectionDescription}>
            Laws vary by state. Setting your location helps us give more accurate information.
          </Text>
          
          <TouchableOpacity 
            style={styles.stateSelector}
            onPress={() => setShowStateModal(true)}
          >
            <View style={styles.stateSelectorContent}>
              <Ionicons name="location" size={20} color="#3B82F6" />
              <Text style={styles.stateSelectorText}>
                {selectedState || 'Select your state'}
              </Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#6B7280" />
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.detectButton}
            onPress={detectLocation}
            disabled={detectingLocation}
          >
            {detectingLocation ? (
              <ActivityIndicator size="small" color="#3B82F6" />
            ) : (
              <>
                <Ionicons name="navigate" size={18} color="#3B82F6" />
                <Text style={styles.detectButtonText}>Detect my location</Text>
              </>
            )}
          </TouchableOpacity>
        </View>

        {/* Emergency Contact Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Emergency Contact</Text>
          <Text style={styles.sectionDescription}>
            This contact can be quickly notified in Emergency Mode.
          </Text>
          
          <View style={styles.inputContainer}>
            <Text style={styles.inputLabel}>Contact Name</Text>
            <TextInput
              style={styles.textInput}
              placeholder="e.g., Mom, Dad, Trusted Adult"
              placeholderTextColor="#6B7280"
              value={emergencyName}
              onChangeText={setEmergencyName}
            />
          </View>

          <View style={styles.inputContainer}>
            <Text style={styles.inputLabel}>Phone Number</Text>
            <TextInput
              style={styles.textInput}
              placeholder="e.g., 555-123-4567"
              placeholderTextColor="#6B7280"
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
            <Text style={styles.saveButtonText}>Save Settings</Text>
          )}
        </TouchableOpacity>

        {/* Data & Privacy Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Data & Privacy</Text>
          
          <TouchableOpacity style={styles.dangerButton} onPress={clearAllData}>
            <Ionicons name="trash-outline" size={20} color="#EF4444" />
            <Text style={styles.dangerButtonText}>Clear All Data</Text>
          </TouchableOpacity>
        </View>

        {/* About Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>About</Text>
          <View style={styles.aboutItem}>
            <Text style={styles.aboutLabel}>Version</Text>
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
                <Ionicons name="close" size={24} color="#FFFFFF" />
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
                    <Ionicons name="checkmark" size={20} color="#3B82F6" />
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
    backgroundColor: '#0F0F0F',
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 16,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#9CA3AF',
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
    color: '#FFFFFF',
    marginBottom: 8,
  },
  sectionDescription: {
    fontSize: 13,
    color: '#9CA3AF',
    marginBottom: 16,
    lineHeight: 18,
  },
  stateSelector: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#1A1A1A',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#2D2D2D',
  },
  stateSelectorContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  stateSelectorText: {
    fontSize: 15,
    color: '#FFFFFF',
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
    color: '#3B82F6',
    marginLeft: 8,
  },
  inputContainer: {
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 13,
    color: '#9CA3AF',
    marginBottom: 8,
  },
  textInput: {
    backgroundColor: '#1A1A1A',
    borderRadius: 12,
    padding: 16,
    color: '#FFFFFF',
    fontSize: 15,
    borderWidth: 1,
    borderColor: '#2D2D2D',
  },
  saveButton: {
    backgroundColor: '#3B82F6',
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
    backgroundColor: '#1A1A1A',
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
    backgroundColor: '#1A1A1A',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2D2D2D',
  },
  aboutLabel: {
    fontSize: 15,
    color: '#9CA3AF',
  },
  aboutValue: {
    fontSize: 15,
    color: '#FFFFFF',
  },
  disclaimerBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#1A1A1A',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#F59E0B30',
  },
  disclaimerText: {
    flex: 1,
    fontSize: 13,
    color: '#9CA3AF',
    marginLeft: 12,
    lineHeight: 18,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1A1A1A',
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
    borderBottomColor: '#2D2D2D',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
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
    backgroundColor: '#3B82F620',
  },
  stateItemText: {
    fontSize: 15,
    color: '#FFFFFF',
  },
  stateItemTextSelected: {
    color: '#3B82F6',
    fontWeight: '600',
  },
});
