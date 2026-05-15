import { useLanguage } from '../utils/LanguageContext';
import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, Alert, Dimensions, Vibration, Linking } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Animated, { FadeIn, FadeInUp, useAnimatedStyle, useSharedValue, withRepeat, withTiming } from 'react-native-reanimated';

const { width } = Dimensions.get('window');

const EMERGENCY_SCRIPTS_KEYS = [
  { id: '1', titleKey: 'emergency.script1Title', contentKey: 'emergency.script1Content' },
  { id: '2', titleKey: 'emergency.script2Title', contentKey: 'emergency.script2Content' },
  { id: '3', titleKey: 'emergency.script3Title', contentKey: 'emergency.script3Content' },
  { id: '4', titleKey: 'emergency.script4Title', contentKey: 'emergency.script4Content' },
  { id: '5', titleKey: 'emergency.script5Title', contentKey: 'emergency.script5Content' },
];

export default function EmergencyScreen() {
  const router = useRouter();
  const { t } = useLanguage();
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

  const EMERGENCY_SCRIPTS = EMERGENCY_SCRIPTS_KEYS.map(s => ({
    id: s.id,
    title: t(s.titleKey),
    content: t(s.contentKey),
  }));

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
    logEvent(t('emergency.timerStarted'));
  };

  const stopTimer = () => {
    setTimerRunning(false);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    logEvent(t('emergency.timerStopped'));
  };

  const logEvent = (note: string) => {
    const now = new Date();
    const timeStr = now.toLocaleTimeString();
    setEvents(prev => [...prev, { time: timeStr, note }]);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  };

  const addNote = () => {
    if (!notes.trim()) return;
    
    logEvent(notes.trim());
    setNotes('');
    Alert.alert(t('emergency.noteSaved'), t('emergency.noteRecorded'));
  };

  const callEmergencyContact = () => {
    if (!emergencyContact) {
      Alert.alert(
        t('emergency.noContact'),
        t('emergency.noContactDesc'),
        [
          { text: t('emergency.cancel'), style: 'cancel' },
          { text: t('emergency.goSettings'), onPress: () => router.push('/(tabs)/settings') }
        ]
      );
      return;
    }

    Alert.alert(
      t('emergency.callContactTitle'),
      `${t('emergency.callContactQ')} ${emergencyContact.name}?`,
      [
        { text: t('emergency.cancel'), style: 'cancel' },
        {
          text: t('emergency.callContactCall'),
          onPress: () => {
            Linking.openURL(`tel:${emergencyContact.phone}`);
            Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
            logEvent(`${t('emergency.calledLog')} ${emergencyContact.name}`);
          }
        }
      ]
    );
  };

  const call911 = () => {
    Alert.alert(
      t('emergency.call911'),
      t('emergency.callConfirm'),
      [
        { text: t('emergency.cancel'), style: 'cancel' },
        {
          text: t('emergency.call911'),
          style: 'destructive',
          onPress: () => {
            Linking.openURL('tel:911');
            logEvent(`${t('emergency.calledLog')} 911`);
          }
        }
      ]
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      {/* Extra spacing for notch/Dynamic Island */}
      <View style={{ height: 12 }} />
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.closeButton}
          onPress={() => router.back()}
        >
          <Ionicons name="close" size={24} color="#374151" />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle}>{t('emergency.title')}</Text>
          <Text style={styles.headerSubtitle}>{t('emergency.subtitle')}</Text>
        </View>
        <TouchableOpacity 
          style={styles.alertButton}
          onPress={call911}
        >
          <Ionicons name="call" size={20} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      {/* Timer Display */}
      <Animated.View style={[styles.timerContainer, pulseStyle]}>
        <Text style={styles.timerText}>{formatTime(timerSeconds)}</Text>
        <View style={styles.timerControls}>
          {!timerRunning ? (
            <TouchableOpacity style={styles.timerButton} onPress={startTimer}>
              <Ionicons name="play" size={20} color="#FFFFFF" />
              <Text style={styles.timerButtonText}>{t('emergency.startRecording')}</Text>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity style={[styles.timerButton, styles.timerButtonStop]} onPress={stopTimer}>
              <Ionicons name="stop" size={20} color="#FFFFFF" />
              <Text style={styles.timerButtonText}>{t('emergency.stop')}</Text>
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
          <Text style={[styles.tabText, activeTab === 'scripts' && styles.activeTabText]}>{t('emergency.scripts')}</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.tab, activeTab === 'notes' && styles.activeTab]}
          onPress={() => setActiveTab('notes')}
        >
          <Ionicons name="create" size={18} color={activeTab === 'notes' ? '#FFFFFF' : '#94A3B8'} />
          <Text style={[styles.tabText, activeTab === 'notes' && styles.activeTabText]}>{t('emergency.notes')}</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.tab, activeTab === 'timer' && styles.activeTab]}
          onPress={() => setActiveTab('timer')}
        >
          <Ionicons name="time" size={18} color={activeTab === 'timer' ? '#FFFFFF' : '#94A3B8'} />
          <Text style={[styles.tabText, activeTab === 'timer' && styles.activeTabText]}>{t('emergency.log')}</Text>
        </TouchableOpacity>
      </View>

      {/* Content */}
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {activeTab === 'scripts' && (
          <Animated.View entering={FadeIn.duration(300)}>
            <Text style={styles.sectionTitle}>{t('emergency.sayThis')}</Text>
            <Text style={styles.sectionDesc}>{t('emergency.sayThisDesc')}</Text>
            
            {EMERGENCY_SCRIPTS.map((script, index) => (
              <Animated.View key={script.id} entering={FadeInUp.duration(300).delay(index * 50)}>
                <TouchableOpacity 
                  style={styles.scriptCard}
                  onPress={() => {
                    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
                    Alert.alert(script.title, `\n"${script.content}"\n\n${t('emergency.sayClearly')}`);
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
            <Text style={styles.sectionTitle}>{t('emergency.documentTitle')}</Text>
            <Text style={styles.sectionDesc}>{t('emergency.documentDesc')}</Text>
            
            <View style={styles.noteInputContainer}>
              <TextInput
                style={styles.noteInput}
                placeholder={t('emergency.notePlaceholderShort')}
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
                <Text style={styles.addNoteButtonText}>{t('emergency.saveNote')}</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.tipBox}>
              <Ionicons name="bulb" size={18} color="#F59E0B" />
              <Text style={styles.tipText}>{t('emergency.tipText')}</Text>
            </View>
          </Animated.View>
        )}

        {activeTab === 'timer' && (
          <Animated.View entering={FadeIn.duration(300)}>
            <Text style={styles.sectionTitle}>{t('emergency.eventLog')}</Text>
            <Text style={styles.sectionDesc}>{t('emergency.eventLogDesc')}</Text>
            
            <TouchableOpacity 
              style={styles.logEventButton}
              onPress={() => logEvent(t('emergency.eventMarked'))}
            >
              <Ionicons name="flag" size={18} color="#FFFFFF" />
              <Text style={styles.logEventButtonText}>{t('emergency.markEvent')}</Text>
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
                <Text style={styles.emptyLogText}>{t('emergency.noEvents')}</Text>
              </View>
            )}
          </Animated.View>
        )}
      </ScrollView>

      {/* Emergency Call Bar */}
      <View style={styles.emergencyBar}>
        <TouchableOpacity style={styles.call911Button} onPress={call911}>
          <Ionicons name="call" size={20} color="#FFFFFF" />
          <Text style={styles.call911Text}>{t('emergency.call911')}</Text>
        </TouchableOpacity>
        {emergencyContact ? (
          <TouchableOpacity style={styles.callContactButton} onPress={callEmergencyContact}>
            <Ionicons name="person" size={18} color="#1B2A4A" />
            <Text style={styles.callContactText}>{t('emergency.callBtnLabel')} {emergencyContact.name}</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity style={styles.callContactButton} onPress={() => router.push('/(tabs)/settings')}>
            <Ionicons name="person-add" size={18} color="#5E6E7D" />
            <Text style={styles.callContactText}>{t('emergency.setupContact')}</Text>
          </TouchableOpacity>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F0EB',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  closeButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#FFFDF9',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#EDE9E3',
  },
  headerCenter: {
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1B2A4A',
  },
  headerSubtitle: {
    fontSize: 13,
    color: '#5E6E7D',
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
    backgroundColor: '#FFFDF9',
    borderRadius: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#EDE9E3',
  },
  timerText: {
    fontSize: 48,
    fontWeight: '300',
    color: '#1B2A4A',
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
    backgroundColor: '#FFFDF9',
    borderWidth: 1,
    borderColor: '#EDE9E3',
  },
  activeTab: {
    backgroundColor: '#C45C5C',
    borderColor: '#C45C5C',
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
    color: '#1B2A4A',
    marginBottom: 4,
  },
  sectionDesc: {
    fontSize: 13,
    color: '#5E6E7D',
    marginBottom: 16,
  },
  scriptCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFDF9',
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#EDE9E3',
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
    color: '#1B2A4A',
    marginBottom: 4,
  },
  scriptText: {
    fontSize: 13,
    color: '#5E6E7D',
    fontStyle: 'italic',
  },
  noteInputContainer: {
    backgroundColor: '#FFFDF9',
    borderRadius: 14,
    padding: 14,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#EDE9E3',
  },
  noteInput: {
    fontSize: 15,
    color: '#1B2A4A',
    minHeight: 100,
    textAlignVertical: 'top',
  },
  addNoteButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#C45C5C',
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
    backgroundColor: '#FFFDF9',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: '#EDE9E3',
  },
  tipText: {
    flex: 1,
    fontSize: 13,
    color: '#5E6E7D',
    marginLeft: 10,
    lineHeight: 18,
  },
  logEventButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#C45C5C',
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
    backgroundColor: '#FFFDF9',
    borderRadius: 14,
    padding: 4,
    borderWidth: 1,
    borderColor: '#EDE9E3',
  },
  eventItem: {
    flexDirection: 'row',
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#EDE9E3',
  },
  eventTime: {
    fontSize: 13,
    fontWeight: '600',
    color: '#1B2A4A',
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
    borderTopColor: '#EDE9E3',
    gap: 8,
  },
  call911Button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#C45C5C',
    borderRadius: 12,
    padding: 14,
  },
  call911Text: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
    marginLeft: 8,
  },
  callContactButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFDF9',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: '#EDE9E3',
  },
  callContactText: {
    fontSize: 14,
    color: '#1B2A4A',
    marginLeft: 8,
  },
});
