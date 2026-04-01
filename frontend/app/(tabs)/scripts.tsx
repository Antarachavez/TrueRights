import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, RefreshControl, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Clipboard from 'expo-clipboard';
import * as Haptics from 'expo-haptics';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import Animated, { FadeInUp } from 'react-native-reanimated';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface Script {
  id: string;
  title: string;
  content: string;
  category: string;
}

interface SavedScript {
  id: string;
  device_id: string;
  title: string;
  content: string;
  category: string;
  saved_at: string;
}

export default function ScriptsScreen() {
  const [defaultScripts, setDefaultScripts] = useState<Script[]>([]);
  const [savedScripts, setSavedScripts] = useState<SavedScript[]>([]);
  const [activeTab, setActiveTab] = useState<'default' | 'saved'>('default');
  const [refreshing, setRefreshing] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [deviceId, setDeviceId] = useState('');

  useEffect(() => {
    initializeAndFetch();
  }, []);

  const initializeAndFetch = async () => {
    try {
      let storedDeviceId = await AsyncStorage.getItem('device_id');
      if (!storedDeviceId) {
        storedDeviceId = `device_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        await AsyncStorage.setItem('device_id', storedDeviceId);
      }
      setDeviceId(storedDeviceId);
      await fetchScripts(storedDeviceId);
    } catch (error) {
      console.error('Error initializing:', error);
    }
  };

  const fetchScripts = async (devId?: string) => {
    try {
      const [defaultRes, savedRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/scripts/default`),
        axios.get(`${BACKEND_URL}/api/scripts/saved/${devId || deviceId}`)
      ]);
      setDefaultScripts(defaultRes.data);
      setSavedScripts(savedRes.data);
    } catch (error) {
      console.error('Error fetching scripts:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchScripts();
    setRefreshing(false);
  };

  const copyToClipboard = async (content: string, id: string) => {
    await Clipboard.setStringAsync(content);
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const saveScript = async (script: Script) => {
    try {
      await axios.post(`${BACKEND_URL}/api/scripts/saved`, {
        device_id: deviceId,
        title: script.title,
        content: script.content,
        category: script.category
      });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      await fetchScripts();
      Alert.alert('Saved!', 'Script added to your saved collection.');
    } catch (error) {
      console.error('Error saving script:', error);
      Alert.alert('Error', 'Could not save script.');
    }
  };

  const deleteScript = async (scriptId: string) => {
    Alert.alert(
      'Delete Script',
      'Are you sure you want to remove this saved script?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await axios.delete(`${BACKEND_URL}/api/scripts/saved/${scriptId}`);
              Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
              await fetchScripts();
            } catch (error) {
              console.error('Error deleting script:', error);
            }
          }
        }
      ]
    );
  };

  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: string } = {
      general: '#3B82F6',
      police: '#EF4444',
      school: '#3B82F6',
      work: '#F97316',
      housing: '#10B981',
      online: '#8B5CF6',
      public: '#14B8A6'
    };
    return colors[category] || '#3B82F6';
  };

  const ScriptCard = ({ script, isSaved = false }: { script: Script | SavedScript; isSaved?: boolean }) => {
    const color = getCategoryColor(script.category);
    const isCopied = copiedId === script.id;

    return (
      <Animated.View entering={FadeInUp.duration(400)} style={styles.scriptCard}>
        <View style={styles.scriptHeader}>
          <View style={[styles.categoryBadge, { backgroundColor: `${color}20` }]}>
            <Text style={[styles.categoryText, { color }]}>{script.category}</Text>
          </View>
          <View style={styles.scriptActions}>
            <TouchableOpacity 
              style={styles.actionButton}
              onPress={() => copyToClipboard(script.content, script.id)}
            >
              <Ionicons 
                name={isCopied ? "checkmark" : "copy-outline"} 
                size={20} 
                color={isCopied ? "#10B981" : "#9CA3AF"} 
              />
            </TouchableOpacity>
            {!isSaved ? (
              <TouchableOpacity 
                style={styles.actionButton}
                onPress={() => saveScript(script as Script)}
              >
                <Ionicons name="bookmark-outline" size={20} color="#9CA3AF" />
              </TouchableOpacity>
            ) : (
              <TouchableOpacity 
                style={styles.actionButton}
                onPress={() => deleteScript(script.id)}
              >
                <Ionicons name="trash-outline" size={20} color="#EF4444" />
              </TouchableOpacity>
            )}
          </View>
        </View>
        <Text style={styles.scriptTitle}>{script.title}</Text>
        <View style={styles.scriptContentContainer}>
          <Text style={styles.quoteIcon}>"</Text>
          <Text style={styles.scriptContent}>{script.content}</Text>
          <Text style={styles.quoteIconEnd}>"</Text>
        </View>
      </Animated.View>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Scripts</Text>
        <Text style={styles.headerSubtitle}>Ready-to-use phrases for any situation</Text>
      </View>

      {/* Tabs */}
      <View style={styles.tabContainer}>
        <TouchableOpacity 
          style={[styles.tab, activeTab === 'default' && styles.activeTab]}
          onPress={() => setActiveTab('default')}
        >
          <Text style={[styles.tabText, activeTab === 'default' && styles.activeTabText]}>Default</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.tab, activeTab === 'saved' && styles.activeTab]}
          onPress={() => setActiveTab('saved')}
        >
          <Text style={[styles.tabText, activeTab === 'saved' && styles.activeTabText]}>
            Saved ({savedScripts.length})
          </Text>
        </TouchableOpacity>
      </View>

      {/* Scripts List */}
      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#3B82F6" />
        }
      >
        {activeTab === 'default' ? (
          defaultScripts.map(script => (
            <ScriptCard key={script.id} script={script} />
          ))
        ) : savedScripts.length > 0 ? (
          savedScripts.map(script => (
            <ScriptCard key={script.id} script={script} isSaved />
          ))
        ) : (
          <View style={styles.emptyState}>
            <Ionicons name="bookmark-outline" size={48} color="#4B5563" />
            <Text style={styles.emptyTitle}>No saved scripts yet</Text>
            <Text style={styles.emptyText}>Tap the bookmark icon on any script to save it here</Text>
          </View>
        )}
      </ScrollView>
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
    paddingBottom: 8,
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
  tabContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginTop: 16,
    marginBottom: 8,
  },
  tab: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 20,
    marginRight: 12,
    backgroundColor: '#1A1A1A',
  },
  activeTab: {
    backgroundColor: '#3B82F6',
  },
  tabText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#9CA3AF',
  },
  activeTabText: {
    color: '#FFFFFF',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingTop: 12,
  },
  scriptCard: {
    backgroundColor: '#1A1A1A',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2D2D2D',
  },
  scriptHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  categoryBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  categoryText: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  scriptActions: {
    flexDirection: 'row',
  },
  actionButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#252525',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
  scriptTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 12,
  },
  scriptContentContainer: {
    backgroundColor: '#0F0F0F',
    borderRadius: 12,
    padding: 14,
    position: 'relative',
  },
  quoteIcon: {
    fontSize: 24,
    color: '#4B5563',
    position: 'absolute',
    top: 4,
    left: 8,
  },
  quoteIconEnd: {
    fontSize: 24,
    color: '#4B5563',
    position: 'absolute',
    bottom: -4,
    right: 8,
  },
  scriptContent: {
    fontSize: 15,
    color: '#E5E7EB',
    lineHeight: 22,
    paddingHorizontal: 16,
    fontStyle: 'italic',
  },
  emptyState: {
    alignItems: 'center',
    paddingTop: 60,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
    marginTop: 16,
  },
  emptyText: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    marginTop: 8,
    paddingHorizontal: 40,
  },
});
