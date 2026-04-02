import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Dimensions, TextInput } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import Animated, { FadeInUp } from 'react-native-reanimated';

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

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    try {
      const [categoriesRes, scenariosRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/categories`),
        axios.get(`${BACKEND_URL}/api/scenarios/${id}`)
      ]);
      
      const foundCategory = categoriesRes.data.find((c: Category) => c.id === id);
      setCategory(foundCategory);
      setAllScenarios(scenariosRes.data);
      
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

  const getIconName = (icon: string): keyof typeof Ionicons.glyphMap => {
    return ICON_MAP[icon] || 'help-circle';
  };

  // Filter scenarios based on search
  const searchResults = searchQuery.trim() 
    ? allScenarios.filter(s => 
        s.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.short_answer.toLowerCase().includes(searchQuery.toLowerCase())
      )
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
          <Ionicons name="arrow-back" size={24} color="#FFFFFF" />
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
          <Ionicons name="search" size={20} color="#6B7280" />
          <TextInput
            style={styles.searchInput}
            placeholder={`Search ${category.name.toLowerCase()} questions...`}
            placeholderTextColor="#6B7280"
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Ionicons name="close-circle" size={20} color="#6B7280" />
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
              <Animated.View key={scenario.id} entering={FadeInUp.duration(300).delay(index * 50)}>
                <TouchableOpacity
                  style={[styles.searchResultCard, { borderLeftColor: category.color }]}
                  onPress={() => router.push(`/scenario/${scenario.id}`)}
                >
                  <View style={styles.searchResultContent}>
                    <Text style={styles.searchResultQuestion}>{scenario.question}</Text>
                    <Text style={styles.searchResultAnswer} numberOfLines={2}>{scenario.short_answer}</Text>
                  </View>
                  <Ionicons name="chevron-forward" size={18} color="#6B7280" />
                </TouchableOpacity>
              </Animated.View>
            ))}
            {searchResults.length === 0 && (
              <View style={styles.noResults}>
                <Ionicons name="search-outline" size={48} color="#4B5563" />
                <Text style={styles.noResultsText}>No questions found</Text>
                <Text style={styles.noResultsHint}>Try different keywords</Text>
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

            {/* Ask AI */}
            <TouchableOpacity 
              style={styles.askAiCard}
              onPress={() => router.push('/(tabs)/chat')}
            >
              <View style={styles.askAiIcon}>
                <Ionicons name="chatbubbles" size={22} color="#3B82F6" />
              </View>
              <View style={styles.askAiText}>
                <Text style={styles.askAiTitle}>Can't find your question?</Text>
                <Text style={styles.askAiDesc}>Ask our AI for help</Text>
              </View>
              <Ionicons name="arrow-forward" size={18} color="#3B82F6" />
            </TouchableOpacity>
          </>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#FFFFFF',
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
    backgroundColor: '#1A1A1A',
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
    color: '#FFFFFF',
  },
  categoryDesc: {
    fontSize: 13,
    color: '#9CA3AF',
    marginTop: 2,
  },
  searchContainer: {
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1A1A1A',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: '#2D2D2D',
  },
  searchInput: {
    flex: 1,
    fontSize: 15,
    color: '#FFFFFF',
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
    color: '#9CA3AF',
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
    backgroundColor: '#1A1A1A',
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
    color: '#FFFFFF',
    marginBottom: 4,
  },
  subcategoryCount: {
    fontSize: 12,
    color: '#6B7280',
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
    backgroundColor: '#1A1A1A',
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
    color: '#FFFFFF',
    marginBottom: 6,
  },
  searchResultAnswer: {
    fontSize: 13,
    color: '#9CA3AF',
    lineHeight: 18,
  },
  noResults: {
    alignItems: 'center',
    paddingTop: 40,
  },
  noResultsText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginTop: 12,
  },
  noResultsHint: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
  },
  askAiCard: {
    backgroundColor: '#1A1A1A',
    borderRadius: 14,
    padding: 14,
    marginTop: 8,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#3B82F625',
  },
  askAiIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: '#3B82F615',
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
    color: '#FFFFFF',
  },
  askAiDesc: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 2,
  },
});
