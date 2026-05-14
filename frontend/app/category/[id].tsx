import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Dimensions, TextInput, ActivityIndicator, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import axios from 'axios';
import Animated, { FadeInUp } from 'react-native-reanimated';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { fuzzySearch } from '../../utils/fuzzySearch';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;
const { width } = Dimensions.get('window');

interface Scenario {
  id: string;
  question: string;
  short_answer: string;
  category: string;
  subcategory: string;
}

interface Subcategory {
  id: string;
  name: string;
  icon: string;
  color: string;
}

interface Category {
  id: string;
  name: string;
  icon: string;
  color: string;
  description: string;
  subcategories: Subcategory[];
}

const ICON_MAP: { [key: string]: keyof typeof Ionicons.glyphMap } = {
  'school': 'school',
  'briefcase': 'briefcase',
  'home': 'home',
  'shield': 'shield',
  'lock': 'lock-closed',
  'map-pin': 'location',
  'search': 'search',
  'warning': 'warning',
  'time': 'time',
  'megaphone': 'megaphone',
  'people': 'people',
  'shirt': 'shirt',
  'cash': 'cash',
  'shield-checkmark': 'shield-checkmark',
  'alert-circle': 'alert-circle',
  'exit': 'exit',
  'eye-off': 'eye-off',
  'key': 'key',
  'construct': 'construct',
  'log-out': 'log-out',
  'document-text': 'document-text',
  'hand-left': 'hand-left',
  'lock-closed': 'lock-closed',
  'videocam': 'videocam',
  'share-social': 'share-social',
  'analytics': 'analytics',
  'images': 'images',
  'eye': 'eye',
  'camera': 'camera',
  'storefront': 'storefront',
  'bus': 'bus',
  'leaf': 'leaf',
  'moon': 'moon',
};

export default function CategoryScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [category, setCategory] = useState<Category | null>(null);
  const [allScenarios, setAllScenarios] = useState<Scenario[]>([]);
  const [scenarioCounts, setScenarioCounts] = useState<{ [key: string]: number }>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [generatedScenarios, setGeneratedScenarios] = useState<any[]>([]);
  const [deviceId, setDeviceId] = useState('');

  useEffect(() => {
    initAndFetch();
  }, [id]);

  const initAndFetch = async () => {
    let storedDeviceId = await AsyncStorage.getItem('device_id');
    if (!storedDeviceId) {
      storedDeviceId = `device_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      await AsyncStorage.setItem('device_id', storedDeviceId);
    }
    setDeviceId(storedDeviceId);
    await fetchData();
  };

  const fetchData = async () => {
    try {
      const [categoriesRes, scenariosRes, genRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/categories`),
        axios.get(`${BACKEND_URL}/api/scenarios/${id}`),
        axios.get(`${BACKEND_URL}/api/scenarios/generated/${id}`),
      ]);
      
      const foundCategory = categoriesRes.data.find((c: Category) => c.id === id);
      setCategory(foundCategory);
      setAllScenarios(scenariosRes.data);
      setGeneratedScenarios(genRes.data || []);
      
      const counts: { [key: string]: number } = {};
      scenariosRes.data.forEach((scenario: any) => {
        counts[scenario.subcategory] = (counts[scenario.subcategory] || 0) + 1;
      });
      setScenarioCounts(counts);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateWithAI = async () => {
    if (!searchQuery.trim()) return;
    setGenerating(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/api/scenarios/generate`, {
        question: searchQuery.trim(),
        category: id,
        device_id: deviceId,
      });
      const generated = response.data;
      // Navigate to the generated scenario detail
      router.push(`/scenario/generated/${generated.id}`);
      // Refresh generated scenarios list
      const genRes = await axios.get(`${BACKEND_URL}/api/scenarios/generated/${id}`);
      setGeneratedScenarios(genRes.data || []);
    } catch (error) {
      console.error('Error generating:', error);
      Alert.alert('Error', 'Could not generate answer. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  const getIconName = (icon: string): keyof typeof Ionicons.glyphMap => {
    return ICON_MAP[icon] || 'help-circle';
  };

  // Filter scenarios based on search - uses fuzzy matching for similar meanings
  const searchResults = searchQuery.trim() 
    ? fuzzySearch(searchQuery, allScenarios)
    : [];

  if (loading || !category) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={[styles.header, { borderBottomColor: `${category.color}30` }]}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color="#1B2A4A" />
        </TouchableOpacity>
        
        <View style={styles.headerContent}>
          <View style={[styles.categoryIcon, { backgroundColor: `${category.color}20` }]}>
            <Ionicons name={getIconName(category.icon)} size={28} color={category.color} />
          </View>
          <View style={styles.headerText}>
            <Text style={styles.categoryName}>{category.name}</Text>
            <Text style={styles.categoryDesc}>{category.description}</Text>
          </View>
        </View>
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <Ionicons name="search" size={20} color="#94A3B8" />
          <TextInput
            style={styles.searchInput}
            placeholder={`Search ${category.name.toLowerCase()} questions...`}
            placeholderTextColor="#94A3B8"
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Ionicons name="close-circle" size={20} color="#94A3B8" />
            </TouchableOpacity>
          )}
        </View>
      </View>

      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {/* Show search results if searching */}
        {searchQuery.trim() ? (
          <>
            <Text style={styles.sectionTitle}>
              {searchResults.length} result{searchResults.length !== 1 ? 's' : ''} found
            </Text>
            {searchResults.map((scenario, index) => (
              <TouchableOpacity
                key={scenario.id}
                style={[styles.searchResultCard, { borderLeftColor: category.color }]}
                onPress={() => router.push(`/scenario/${scenario.id}`)}
              >
                <View style={styles.searchResultContent}>
                  <Text style={styles.searchResultQuestion}>{scenario.question}</Text>
                  <Text style={styles.searchResultAnswer} numberOfLines={2}>{scenario.short_answer}</Text>
                </View>
                <Ionicons name="chevron-forward" size={18} color="#94A3B8" />
              </TouchableOpacity>
            ))}
            {searchResults.length === 0 && (
              <View style={styles.noResults}>
                <Ionicons name="search-outline" size={48} color="#5E6E7D" />
                <Text style={styles.noResultsText}>No pre-loaded answers found</Text>
                <Text style={styles.noResultsHint}>Want AI to research this for you?</Text>
                <TouchableOpacity
                  style={styles.generateButton}
                  onPress={generateWithAI}
                  disabled={generating}
                  activeOpacity={0.8}
                >
                  <LinearGradient
                    colors={['#E8A5A5', '#D4787A']}
                    style={styles.generateGradient}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 0 }}
                  >
                    {generating ? (
                      <>
                        <ActivityIndicator size="small" color="#FFFFFF" />
                        <Text style={styles.generateText}>AI is researching...</Text>
                      </>
                    ) : (
                      <>
                        <Ionicons name="sparkles" size={18} color="#FFFFFF" />
                        <Text style={styles.generateText}>Generate with AI</Text>
                      </>
                    )}
                  </LinearGradient>
                </TouchableOpacity>
              </View>
            )}
          </>
        ) : (
          <>
            {/* Subcategories Grid */}
            <Text style={styles.sectionTitle}>Choose a Topic</Text>
            <View style={styles.subcategoriesGrid}>
              {category.subcategories?.map((sub, index) => (
                <Animated.View 
                  key={sub.id}
                  entering={FadeInUp.duration(400).delay(index * 60)}
                  style={styles.subcategoryCardWrapper}
                >
                  <TouchableOpacity
                    style={[styles.subcategoryCard, { borderColor: `${sub.color}40` }]}
                    onPress={() => router.push(`/subcategory/${id}/${sub.id}`)}
                  >
                    <View style={[styles.subcategoryIcon, { backgroundColor: `${sub.color}20` }]}>
                      <Ionicons name={getIconName(sub.icon)} size={26} color={sub.color} />
                    </View>
                    <Text style={styles.subcategoryName}>{sub.name}</Text>
                    <Text style={styles.subcategoryCount}>
                      {scenarioCounts[sub.id] || 0} questions
                    </Text>
                    <View style={[styles.arrowCircle, { backgroundColor: `${sub.color}15` }]}>
                      <Ionicons name="chevron-forward" size={14} color={sub.color} />
                    </View>
                  </TouchableOpacity>
                </Animated.View>
              ))}
            </View>

            {/* Ask AI / Generate */}
            <TouchableOpacity 
              style={styles.askAiCard}
              onPress={() => {/* focus search */}}
            >
              <View style={styles.askAiIcon}>
                <Ionicons name="sparkles" size={22} color="#E8A5A5" />
              </View>
              <View style={styles.askAiText}>
                <Text style={styles.askAiTitle}>Can't find your question?</Text>
                <Text style={styles.askAiDesc}>Search above and AI will generate an answer</Text>
              </View>
              <Ionicons name="arrow-forward" size={18} color="#E8A5A5" />
            </TouchableOpacity>

            {/* Previously Generated by AI */}
            {generatedScenarios.length > 0 && (
              <>
                <View style={styles.generatedHeader}>
                  <Ionicons name="sparkles" size={16} color="#E8A5A5" />
                  <Text style={styles.generatedTitle}>AI Generated</Text>
                  <Text style={styles.generatedCount}>{generatedScenarios.length}</Text>
                </View>
                {generatedScenarios.map((scenario: any, index: number) => (
                  <Animated.View key={scenario.id} entering={FadeInUp.duration(300).delay(index * 50)}>
                    <TouchableOpacity
                      style={[styles.searchResultCard, { borderLeftColor: '#E8A5A5' }]}
                      onPress={() => router.push(`/scenario/generated/${scenario.id}`)}
                    >
                      <View style={styles.searchResultContent}>
                        <View style={styles.aiBadgeRow}>
                          <View style={styles.aiBadge}>
                            <Ionicons name="sparkles" size={10} color="#E8A5A5" />
                            <Text style={styles.aiBadgeText}>AI Generated</Text>
                          </View>
                        </View>
                        <Text style={styles.searchResultQuestion}>{scenario.question}</Text>
                        <Text style={styles.searchResultAnswer} numberOfLines={2}>{scenario.short_answer}</Text>
                      </View>
                      <Ionicons name="chevron-forward" size={18} color="#94A3B8" />
                    </TouchableOpacity>
                  </Animated.View>
                ))}
              </>
            )}
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAF8F5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#1B2A4A',
    fontSize: 16,
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 16,
    borderBottomWidth: 1,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#FFFDF9',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  categoryIcon: {
    width: 56,
    height: 56,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  headerText: {
    flex: 1,
  },
  categoryName: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1B2A4A',
  },
  categoryDesc: {
    fontSize: 13,
    color: '#5E6E7D',
    marginTop: 2,
  },
  searchContainer: {
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFDF9',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: '#EDE9E3',
  },
  searchInput: {
    flex: 1,
    fontSize: 15,
    color: "#1B2A4A",
    marginLeft: 10,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingTop: 8,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#5E6E7D',
    marginBottom: 14,
  },
  subcategoriesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  subcategoryCardWrapper: {
    width: (width - 52) / 2,
    marginBottom: 12,
  },
  subcategoryCard: {
    backgroundColor: '#FFFDF9',
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    minHeight: 130,
  },
  subcategoryIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 10,
  },
  subcategoryName: {
    fontSize: 14,
    fontWeight: '600',
    color: "#1B2A4A",
    marginBottom: 4,
  },
  subcategoryCount: {
    fontSize: 12,
    color: '#94A3B8',
  },
  arrowCircle: {
    position: 'absolute',
    top: 12,
    right: 12,
    width: 26,
    height: 26,
    borderRadius: 13,
    justifyContent: 'center',
    alignItems: 'center',
  },
  searchResultCard: {
    backgroundColor: '#FFFDF9',
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    borderLeftWidth: 3,
    flexDirection: 'row',
    alignItems: 'center',
  },
  searchResultContent: {
    flex: 1,
    marginRight: 10,
  },
  searchResultQuestion: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1B2A4A',
    marginBottom: 6,
  },
  searchResultAnswer: {
    fontSize: 13,
    color: '#5E6E7D',
    lineHeight: 18,
  },
  noResults: {
    alignItems: 'center',
    paddingTop: 40,
  },
  noResultsText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1B2A4A',
    marginTop: 12,
  },
  noResultsHint: {
    fontSize: 14,
    color: '#94A3B8',
    marginTop: 4,
  },
  askAiCard: {
    backgroundColor: '#FFFDF9',
    borderRadius: 14,
    padding: 14,
    marginTop: 8,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E8A5A525',
  },
  askAiIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: '#E8A5A515',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  askAiText: {
    flex: 1,
  },
  askAiTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: "#1B2A4A",
  },
  askAiDesc: {
    fontSize: 12,
    color: '#5E6E7D',
    marginTop: 2,
  },
  generateButton: {
    marginTop: 20,
    borderRadius: 14,
    overflow: 'hidden',
    width: '80%',
  },
  generateGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 14,
    gap: 8,
  },
  generateText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  generatedHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 24,
    marginBottom: 12,
    gap: 8,
  },
  generatedTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#E8A5A5',
    flex: 1,
  },
  generatedCount: {
    fontSize: 13,
    color: '#94A3B8',
    backgroundColor: '#FFFDF9',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
    overflow: 'hidden',
  },
  aiBadgeRow: {
    flexDirection: 'row',
    marginBottom: 6,
  },
  aiBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E8A5A515',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    gap: 4,
  },
  aiBadgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#E8A5A5',
  },
});
