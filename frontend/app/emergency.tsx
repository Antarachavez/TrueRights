import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, Alert, Dimensions, Vibration } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import Animated, { FadeIn, FadeInUp, useAnimatedStyle, useSharedValue, withRepeat, withTiming } from 'react-native-reanimated';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;
const { width } = Dimensions.get('window');

const EMERGENCY_SCRIPTS = [
  {
    id: '1',
    title: 'Stay Calm',
    content: "I want to remain calm. I am documenting this situation."
  },
  {
    id: '2',
    title: 'Ask If Detained',
    content: "Am I free to go, or am I being detained?"
  },
  {
    id: '3',
    title: 'Decline Search',
    content: "I do not consent to a search."
  },
  {
    id: '4',
    title: 'Request Support',
    content: "I would like to contact a parent, guardian, or lawyer."
  },
  {
    id: '5',
    title: 'Remain Silent',
    content: "I am exercising my right to remain silent."
  }
];

export default function EmergencyScreen() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'scripts' | 'notes' | 'timer'>('scripts');
  const [notes, setNotes] = useState('');
  const [timerSeconds, setTimerSeconds] = useState(0);
  const [timerRunning, setTimerRunning] = useState(false);
  const [events, setEvents] = useState<{time: string, note: string}[]>([]);
  const [emergencyContact, setEmergencyContact] = useState<{name: string, phone: string} | null>(null);
  const [deviceId, setDeviceId] = useState('');
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const pulseValue = useSharedValue(1);

  useEffect(() => {
    initializeEmergency();
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  useEffect(() => {
    if (timerRunning) {
      pulseValue.value = withRepeat(
        withTiming(1.05, { duration: 1000 }),
        -1,
        true
      );
    } else {
      pulseValue.value = withTiming(1);
    }
  }, [timerRunning]);

  const pulseStyle = useAnimatedStyle(() => ({
    transform: [{ scale: pulseValue.value }],
  }));

  const initializeEmergency = async () => {
    try {
      let storedDeviceId = await AsyncStorage.getItem('device_id');
      if (!storedDeviceId) {
        storedDeviceId = `device_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        await AsyncStorage.setItem('device_id', storedDeviceId);
      }
      setDeviceId(storedDeviceId);

      const name = await AsyncStorage.getItem('emergency_name');
      const phone = await AsyncStorage.getItem('emergency_phone');
      
      if (name && phone) {
        setEmergencyContact({ name, phone });
      }

      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
    } catch (error) {
      console.error('Error initializing:', error);
    }
  };

  const formatTime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const startTimer = () => {
    setTimerRunning(true);
    timerRef.current = setInterval(() => {
      setTimerSeconds(prev => prev + 1);
    }, 1000);
    logEvent('Timer started');
  };

  const stopTimer = () => {
    setTimerRunning(false);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    logEvent('Timer stopped');
  };

  const logEvent = (note: string) => {
    const now = new Date();
    const timeStr = now.toLocaleTimeString();
    setEvents(prev => [...prev, { time: timeStr, note }]);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  };

  const addNote = async () => {
    if (!notes.trim()) return;
    
    logEvent(notes.trim());
    
    try {
      await axios.post(`${BACKEND_URL}/api/emergency/notes`, {
        device_id: deviceId,
        content: notes.trim(),
        event_time: new Date().toISOString()
      });
    } catch (error) {
      console.error('Error saving note:', error);
    }
    
    setNotes('');
    Alert.alert('Note Saved', 'Your note has been recorded.');
  };

  const sendEmergencyAlert = async () => {
    if (!emergencyContact) {
      Alert.alert(
        'No Emergency Contact',
        'Please set up an emergency contact in Settings first.',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Go to Settings', onPress: () => router.push('/(tabs)/settings') }
        ]
      );
      return;
    }

    Alert.alert(
      'Send Alert',
      `Send emergency alert to ${emergencyContact.name}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Send',
          style: 'destructive',
          onPress: async () => {
            try {
              await axios.post(`${BACKEND_URL}/api/sms/send`, {
                to_phone: emergencyContact.phone,
                message: "EMERGENCY ALERT: I may need help. Please check on me or call me. This message was sent from the True Rights app.",
                from_name: "True Rights App"
              });
              Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
              logEvent(`Alert sent to ${emergencyContact.name}`);
              Alert.alert('Alert Sent', `Emergency alert sent to ${emergencyContact.name}. (Note: This is a demo - actual SMS requires Twilio setup)`);
            } catch (error) {
              console.error('Error sending alert:', error);
              Alert.alert('Demo Mode', 'SMS would be sent in production with Twilio integration.');
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
        <TouchableOpacity 
          style={styles.closeButton}
          onPress={() => router.back()}
        >
          <Ionicons name="close" size={24} color="#374151" />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle}>Emergency Mode</Text>
          <Text style={styles.headerSubtitle}>Stay calm. You've got this.</Text>
        </View>
        <TouchableOpacity 
          style={styles.alertButton}
          onPress={sendEmergencyAlert}
        >
          <Ionicons name="notifications" size={20} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      {/* Timer Display */}
      <Animated.View style={[styles.timerContainer, pulseStyle]}>
        <Text style={styles.timerText}>{formatTime(timerSeconds)}</Text>
        <View style={styles.timerControls}>
          {!timerRunning ? (
            <TouchableOpacity style={styles.timerButton} onPress={startTimer}>
              <Ionicons name="play" size={20} color="#FFFFFF" />
              <Text style={styles.timerButtonText}>Start Recording</Text>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity style={[styles.timerButton, styles.timerButtonStop]} onPress={stopTimer}>
              <Ionicons name="stop" size={20} color="#FFFFFF" />
              <Text style={styles.timerButtonText}>Stop</Text>
            </TouchableOpacity>
          )}
        </View>
      </Animated.View>

      {/* Tabs */}
      <View style={styles.tabContainer}>
        <TouchableOpacity 
          style={[styles.tab, activeTab === 'scripts' && styles.activeTab]}
          onPress={() => setActiveTab('scripts')}
        >
          <Ionicons name="document-text" size={18} color={activeTab === 'scripts' ? '#FFFFFF' : '#94A3B8'} />
          <Text style={[styles.tabText, activeTab === 'scripts' && styles.activeTabText]}>Scripts</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.tab, activeTab === 'notes' && styles.activeTab]}
          onPress={() => setActiveTab('notes')}
        >
          <Ionicons name="create" size={18} color={activeTab === 'notes' ? '#FFFFFF' : '#94A3B8'} />
          <Text style={[styles.tabText, activeTab === 'notes' && styles.activeTabText]}>Notes</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.tab, activeTab === 'timer' && styles.activeTab]}
          onPress={() => setActiveTab('timer')}
        >
          <Ionicons name="time" size={18} color={activeTab === 'timer' ? '#FFFFFF' : '#94A3B8'} />
          <Text style={[styles.tabText, activeTab === 'timer' && styles.activeTabText]}>Log</Text>
        </TouchableOpacity>
      </View>

      {/* Content */}
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {activeTab === 'scripts' && (
          <Animated.View entering={FadeIn.duration(300)}>
            <Text style={styles.sectionTitle}>Say This Out Loud</Text>
            <Text style={styles.sectionDesc}>Tap any script to read it calmly</Text>
            
            {EMERGENCY_SCRIPTS.map((script, index) => (
              <Animated.View key={script.id} entering={FadeInUp.duration(300).delay(index * 50)}>
                <TouchableOpacity 
                  style={styles.scriptCard}
                  onPress={() => {
                    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
                    Alert.alert(script.title, `\n"${script.content}"\n\nSay this clearly and calmly.`);
                  }}
                >
                  <View style={styles.scriptNumber}>
                    <Text style={styles.scriptNumberText}>{index + 1}</Text>
                  </View>
                  <View style={styles.scriptContentView}>
                    <Text style={styles.scriptTitle}>{script.title}</Text>
                    <Text style={styles.scriptText}>"{script.content}"</Text>
                  </View>
                </TouchableOpacity>
              </Animated.View>
            ))}
          </Animated.View>
        )}

        {activeTab === 'notes' && (
          <Animated.View entering={FadeIn.duration(300)}>
            <Text style={styles.sectionTitle}>Document What's Happening</Text>
            <Text style={styles.sectionDesc}>Write down details while they're fresh</Text>
            
            <View style={styles.noteInputContainer}>
              <TextInput
                style={styles.noteInput}
                placeholder="What's happening? Who's involved? What time is it?"
                placeholderTextColor="#94A3B8"
                value={notes}
                onChangeText={setNotes}
                multiline
                numberOfLines={4}
              />
              <TouchableOpacity 
                style={[styles.addNoteButton, !notes.trim() && styles.addNoteButtonDisabled]}
                onPress={addNote}
                disabled={!notes.trim()}
              >
                <Ionicons name="add" size={20} color="#FFFFFF" />
                <Text style={styles.addNoteButtonText}>Save Note</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.tipBox}>
              <Ionicons name="bulb" size={18} color="#F59E0B" />
              <Text style={styles.tipText}>Include: names, badge numbers, time, location, witnesses</Text>
            </View>
          </Animated.View>
        )}

        {activeTab === 'timer' && (
          <Animated.View entering={FadeIn.duration(300)}>
            <Text style={styles.sectionTitle}>Event Log</Text>
            <Text style={styles.sectionDesc}>Timestamped record of events</Text>
            
            <TouchableOpacity 
              style={styles.logEventButton}
              onPress={() => logEvent('Event marked')}
            >
              <Ionicons name="flag" size={18} color="#FFFFFF" />
              <Text style={styles.logEventButtonText}>Mark Event</Text>
            </TouchableOpacity>

            {events.length > 0 ? (
              <View style={styles.eventsList}>
                {events.map((event, index) => (
                  <View key={index} style={styles.eventItem}>
                    <Text style={styles.eventTime}>{event.time}</Text>
                    <Text style={styles.eventNote}>{event.note}</Text>
                  </View>
                ))}
              </View>
            ) : (
              <View style={styles.emptyLog}>
                <Ionicons name="time-outline" size={32} color="#94A3B8" />
                <Text style={styles.emptyLogText}>No events logged yet</Text>
              </View>
            )}
          </Animated.View>
        )}
      </ScrollView>

      {/* Emergency Contact Bar */}
      <View style={styles.emergencyBar}>
        {emergencyContact ? (
          <TouchableOpacity style={styles.emergencyBarContent} onPress={sendEmergencyAlert}>
            <Ionicons name="call" size={20} color="#EF4444" />
            <Text style={styles.emergencyBarText}>Alert {emergencyContact.name}</Text>
            <Ionicons name="chevron-forward" size={18} color="#94A3B8" />
          </TouchableOpacity>
        ) : (
          <TouchableOpacity style={styles.emergencyBarContent} onPress={() => router.push('/(tabs)/settings')}>
            <Ionicons name="person-add" size={20} color="#64748B" />
            <Text style={styles.emergencyBarText}>Set up emergency contact</Text>
            <Ionicons name="chevron-forward" size={18} color="#94A3B8" />
          </TouchableOpacity>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAFAFE',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  closeButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#FFFFFF',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#F1F1F5',
  },
  headerCenter: {
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1E1B4B',
  },
  headerSubtitle: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 2,
  },
  alertButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#EF4444',
    justifyContent: 'center',
    alignItems: 'center',
  },
  timerContainer: {
    alignItems: 'center',
    paddingVertical: 24,
    marginHorizontal: 20,
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#F1F1F5',
  },
  timerText: {
    fontSize: 48,
    fontWeight: '300',
    color: '#1E1B4B',
    fontVariant: ['tabular-nums'],
  },
  timerControls: {
    marginTop: 16,
  },
  timerButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#10B981',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
  },
  timerButtonStop: {
    backgroundColor: '#EF4444',
  },
  timerButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
    marginLeft: 8,
  },
  tabContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 8,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: 12,
    marginHorizontal: 4,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#F1F1F5',
  },
  activeTab: {
    backgroundColor: '#8B5CF6',
    borderColor: '#8B5CF6',
  },
  tabText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#94A3B8',
    marginLeft: 6,
  },
  activeTabText: {
    color: '#FFFFFF',
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1E1B4B',
    marginBottom: 4,
  },
  sectionDesc: {
    fontSize: 13,
    color: '#64748B',
    marginBottom: 16,
  },
  scriptCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#F1F1F5',
  },
  scriptNumber: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#EF444420',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  scriptNumberText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#EF4444',
  },
  scriptContentView: {
    flex: 1,
  },
  scriptTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1E1B4B',
    marginBottom: 4,
  },
  scriptText: {
    fontSize: 13,
    color: '#64748B',
    fontStyle: 'italic',
  },
  noteInputContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 14,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#F1F1F5',
  },
  noteInput: {
    fontSize: 15,
    color: '#1E1B4B',
    minHeight: 100,
    textAlignVertical: 'top',
  },
  addNoteButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#3B82F6',
    borderRadius: 10,
    paddingVertical: 12,
    marginTop: 12,
  },
  addNoteButtonDisabled: {
    backgroundColor: '#E2E8F0',
  },
  addNoteButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
    marginLeft: 6,
  },
  tipBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: '#F1F1F5',
  },
  tipText: {
    flex: 1,
    fontSize: 13,
    color: '#64748B',
    marginLeft: 10,
    lineHeight: 18,
  },
  logEventButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#3B82F6',
    borderRadius: 12,
    paddingVertical: 14,
    marginBottom: 16,
  },
  logEventButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
    marginLeft: 8,
  },
  eventsList: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 4,
    borderWidth: 1,
    borderColor: '#F1F1F5',
  },
  eventItem: {
    flexDirection: 'row',
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F1F5',
  },
  eventTime: {
    fontSize: 13,
    fontWeight: '600',
    color: '#3B82F6',
    width: 80,
  },
  eventNote: {
    flex: 1,
    fontSize: 14,
    color: '#374151',
  },
  emptyLog: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyLogText: {
    fontSize: 14,
    color: '#94A3B8',
    marginTop: 12,
  },
  emergencyBar: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#F1F1F5',
  },
  emergencyBarContent: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: '#F1F1F5',
  },
  emergencyBarText: {
    flex: 1,
    fontSize: 14,
    color: '#1E1B4B',
    marginLeft: 12,
  },
});
