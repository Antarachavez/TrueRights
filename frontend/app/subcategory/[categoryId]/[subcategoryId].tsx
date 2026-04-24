import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import Animated, { FadeInUp } from 'react-native-reanimated';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

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
  'school': 'school', 'briefcase': 'briefcase', 'home': 'home', 'shield': 'shield',
  'lock': 'lock-closed', 'map-pin': 'location', 'search': 'search', 'warning': 'warning',
  'time': 'time', 'megaphone': 'megaphone', 'people': 'people', 'shirt': 'shirt',
  'cash': 'cash', 'shield-checkmark': 'shield-checkmark', 'alert-circle': 'alert-circle',
  'exit': 'exit', 'eye-off': 'eye-off', 'key': 'key', 'construct': 'construct',
  'log-out': 'log-out', 'document-text': 'document-text', 'hand-left': 'hand-left',
  'lock-closed': 'lock-closed', 'videocam': 'videocam', 'share-social': 'share-social',
  'analytics': 'analytics', 'images': 'images', 'eye': 'eye', 'camera': 'camera',
  'storefront': 'storefront', 'bus': 'bus', 'leaf': 'leaf', 'moon': 'moon',
};

export default function SubcategoryScreen() {
  const { categoryId, subcategoryId } = useLocalSearchParams<{ categoryId: string; subcategoryId: string }>();
  const router = useRouter();
  const [category, setCategory] = useState<Category | null>(null);
  const [subcategory, setSubcategory] = useState<Subcategory | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [categoryId, subcategoryId]);

  const fetchData = async () => {
    try {
      const [categoriesRes, scenariosRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/categories`),
        axios.get(`${BACKEND_URL}/api/scenarios/${categoryId}/${subcategoryId}`)
      ]);
      
      const foundCategory = categoriesRes.data.find((c: Category) => c.id === categoryId);
      setCategory(foundCategory);
      
      if (foundCategory) {
        const foundSubcategory = foundCategory.subcategories?.find((s: Subcategory) => s.id === subcategoryId);
        setSubcategory(foundSubcategory);
      }
      
      setScenarios(scenariosRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getIconName = (icon: string): keyof typeof Ionicons.glyphMap => {
    return ICON_MAP[icon] || 'help-circle';
  };

  const filteredScenarios = searchQuery.trim()
    ? scenarios.filter(s =>
        s.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.short_answer.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : scenarios;

  if (loading || !category || !subcategory) {
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
      <View style={[styles.header, { borderBottomColor: `${subcategory.color}30` }]}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color="#1E1B4B" />
        </TouchableOpacity>
        
        <View style={styles.headerContent}>
          <View style={[styles.subcategoryIcon, { backgroundColor: `${subcategory.color}20` }]}>
            <Ionicons name={getIconName(subcategory.icon)} size={26} color={subcategory.color} />
          </View>
          <View style={styles.headerText}>
            <Text style={styles.breadcrumb}>{category.name}</Text>
            <Text style={[styles.subcategoryName, { color: subcategory.color }]}>{subcategory.name}</Text>
          </View>
        </View>
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <View style={[styles.searchBar, { borderColor: `${subcategory.color}30` }]}>
          <Ionicons name="search" size={18} color="#94A3B8" />
          <TextInput
            style={styles.searchInput}
            placeholder="Search questions..."
            placeholderTextColor="#94A3B8"
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Ionicons name="close-circle" size={18} color="#94A3B8" />
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Questions List */}
      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={styles.sectionTitle}>
          {filteredScenarios.length} question{filteredScenarios.length !== 1 ? 's' : ''}
        </Text>
        
        {filteredScenarios.map((scenario, index) => (
          <Animated.View 
            key={scenario.id}
            entering={FadeInUp.duration(300).delay(index * 40)}
          >
            <TouchableOpacity
              style={[styles.scenarioCard, { borderLeftColor: subcategory.color }]}
              onPress={() => router.push(`/scenario/${scenario.id}`)}
            >
              <View style={styles.scenarioContent}>
                <Text style={styles.scenarioQuestion}>{scenario.question}</Text>
                <Text style={styles.scenarioAnswer} numberOfLines={2}>{scenario.short_answer}</Text>
              </View>
              <View style={[styles.arrowCircle, { backgroundColor: `${subcategory.color}12` }]}>
                <Ionicons name="chevron-forward" size={16} color={subcategory.color} />
              </View>
            </TouchableOpacity>
          </Animated.View>
        ))}

        {filteredScenarios.length === 0 && searchQuery.trim() && (
          <View style={styles.noResults}>
            <Ionicons name="search-outline" size={40} color="#64748B" />
            <Text style={styles.noResultsText}>No matches found</Text>
          </View>
        )}

        {/* Ask AI */}
        <TouchableOpacity 
          style={styles.askAiCard}
          onPress={() => router.push('/(tabs)/chat')}
        >
          <View style={styles.askAiIcon}>
            <Ionicons name="chatbubbles" size={20} color="#3B82F6" />
          </View>
          <View style={styles.askAiText}>
            <Text style={styles.askAiTitle}>Don't see your question?</Text>
            <Text style={styles.askAiDesc}>Ask AI for help</Text>
          </View>
          <Ionicons name="arrow-forward" size={16} color="#3B82F6" />
        </TouchableOpacity>

        <View style={styles.disclaimer}>
          <Text style={styles.disclaimerText}>
            Laws vary by state. This is educational info, not legal advice.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FAFAFE' },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { color: '#1E1B4B', fontSize: 16 },
  header: { paddingHorizontal: 20, paddingTop: 8, paddingBottom: 14, borderBottomWidth: 1 },
  backButton: { width: 38, height: 38, borderRadius: 19, backgroundColor: '#FFFFFF', justifyContent: 'center', alignItems: 'center', marginBottom: 12 },
  headerContent: { flexDirection: 'row', alignItems: 'center' },
  subcategoryIcon: { width: 52, height: 52, borderRadius: 14, justifyContent: 'center', alignItems: 'center', marginRight: 14 },
  headerText: { flex: 1 },
  breadcrumb: { fontSize: 12, color: '#94A3B8', marginBottom: 2 },
  subcategoryName: { fontSize: 20, fontWeight: '700' },
  searchContainer: { paddingHorizontal: 20, paddingVertical: 10 },
  searchBar: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFFFFF', borderRadius: 10, paddingHorizontal: 12, paddingVertical: 10, borderWidth: 1 },
  searchInput: { flex: 1, fontSize: 14, color: "#1E1B4B", marginLeft: 8 },
  scrollView: { flex: 1 },
  scrollContent: { padding: 20, paddingTop: 6 },
  sectionTitle: { fontSize: 13, fontWeight: '500', color: '#94A3B8', marginBottom: 12 },
  scenarioCard: { backgroundColor: '#FFFFFF', borderRadius: 14, padding: 14, marginBottom: 10, borderLeftWidth: 3, flexDirection: 'row', alignItems: 'center' },
  scenarioContent: { flex: 1, marginRight: 10 },
  scenarioQuestion: { fontSize: 15, fontWeight: '600', color: "#1E1B4B", marginBottom: 6, lineHeight: 20 },
  scenarioAnswer: { fontSize: 13, color: '#64748B', lineHeight: 18 },
  arrowCircle: { width: 32, height: 32, borderRadius: 16, justifyContent: 'center', alignItems: 'center' },
  noResults: { alignItems: 'center', paddingTop: 30 },
  noResultsText: { fontSize: 15, color: '#94A3B8', marginTop: 10 },
  askAiCard: { backgroundColor: '#FFFFFF', borderRadius: 12, padding: 12, marginTop: 10, flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderColor: '#3B82F620' },
  askAiIcon: { width: 38, height: 38, borderRadius: 10, backgroundColor: '#3B82F612', justifyContent: 'center', alignItems: 'center', marginRight: 10 },
  askAiText: { flex: 1 },
  askAiTitle: { fontSize: 13, fontWeight: '600', color: '#1E1B4B' },
  askAiDesc: { fontSize: 11, color: '#64748B', marginTop: 1 },
  disclaimer: { paddingTop: 16, paddingBottom: 8 },
  disclaimerText: { fontSize: 11, color: '#64748B', textAlign: 'center' },
});
