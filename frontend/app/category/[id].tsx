import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Dimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import Animated, { FadeInUp, FadeIn } from 'react-native-reanimated';

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
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedSubcategory, setSelectedSubcategory] = useState<string | null>(null);
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
      setScenarios(scenariosRes.data);
      
      // Select first subcategory by default
      if (foundCategory?.subcategories?.length > 0) {
        setSelectedSubcategory(foundCategory.subcategories[0].id);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getIconName = (icon: string): keyof typeof Ionicons.glyphMap => {
    return ICON_MAP[icon] || 'help-circle';
  };

  const filteredScenarios = selectedSubcategory 
    ? scenarios.filter(s => s.subcategory === selectedSubcategory)
    : scenarios;

  const getSelectedSubcategoryInfo = () => {
    if (!category || !selectedSubcategory) return null;
    return category.subcategories.find(s => s.id === selectedSubcategory);
  };

  if (loading || !category) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading...</Text>
        </View>
      </SafeAreaView>
    );
  }

  const subcategoryInfo = getSelectedSubcategoryInfo();

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

      {/* Subcategory Pills */}
      <View style={styles.subcategoryContainer}>
        <ScrollView 
          horizontal 
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.subcategoryScroll}
        >
          {category.subcategories?.map((sub, index) => (
            <Animated.View key={sub.id} entering={FadeIn.duration(300).delay(index * 50)}>
              <TouchableOpacity
                style={[
                  styles.subcategoryPill,
                  selectedSubcategory === sub.id && { backgroundColor: sub.color }
                ]}
                onPress={() => setSelectedSubcategory(sub.id)}
              >
                <Ionicons 
                  name={getIconName(sub.icon)} 
                  size={16} 
                  color={selectedSubcategory === sub.id ? '#FFFFFF' : sub.color} 
                />
                <Text style={[
                  styles.subcategoryText,
                  selectedSubcategory === sub.id && styles.subcategoryTextActive
                ]}>
                  {sub.name}
                </Text>
              </TouchableOpacity>
            </Animated.View>
          ))}
        </ScrollView>
      </View>

      {/* Subcategory Title */}
      {subcategoryInfo && (
        <View style={styles.subcategoryHeader}>
          <Text style={[styles.subcategoryTitle, { color: subcategoryInfo.color }]}>
            {subcategoryInfo.name}
          </Text>
          <Text style={styles.scenarioCount}>{filteredScenarios.length} questions</Text>
        </View>
      )}

      {/* Scenarios List */}
      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {filteredScenarios.map((scenario, index) => (
          <Animated.View 
            key={scenario.id}
            entering={FadeInUp.duration(400).delay(index * 80)}
          >
            <TouchableOpacity
              style={[styles.scenarioCard, { borderLeftColor: subcategoryInfo?.color || category.color }]}
              onPress={() => router.push(`/scenario/${scenario.id}`)}
            >
              <View style={styles.scenarioContent}>
                <Text style={styles.scenarioQuestion}>{scenario.question}</Text>
                <Text style={styles.scenarioAnswer} numberOfLines={2}>
                  {scenario.short_answer}
                </Text>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#6B7280" />
            </TouchableOpacity>
          </Animated.View>
        ))}

        {/* Ask AI Card */}
        <TouchableOpacity 
          style={styles.askAiCard}
          onPress={() => router.push('/(tabs)/chat')}
        >
          <View style={styles.askAiContent}>
            <View style={styles.askAiIcon}>
              <Ionicons name="chatbubbles" size={24} color="#3B82F6" />
            </View>
            <View style={styles.askAiText}>
              <Text style={styles.askAiTitle}>Have a different question?</Text>
              <Text style={styles.askAiDesc}>Ask our AI assistant for help</Text>
            </View>
          </View>
          <Ionicons name="arrow-forward" size={20} color="#3B82F6" />
        </TouchableOpacity>

        {/* Disclaimer */}
        <View style={styles.disclaimer}>
          <Ionicons name="information-circle" size={16} color="#6B7280" />
          <Text style={styles.disclaimerText}>
            Laws vary by state. This is educational information, not legal advice.
          </Text>
        </View>
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
    marginBottom: 16,
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
    marginRight: 16,
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
    fontSize: 14,
    color: '#9CA3AF',
    marginTop: 4,
  },
  subcategoryContainer: {
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1A1A1A',
  },
  subcategoryScroll: {
    paddingHorizontal: 20,
  },
  subcategoryPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1A1A1A',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 20,
    marginRight: 10,
    borderWidth: 1,
    borderColor: '#2D2D2D',
  },
  subcategoryText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#9CA3AF',
    marginLeft: 6,
  },
  subcategoryTextActive: {
    color: '#FFFFFF',
  },
  subcategoryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 8,
  },
  subcategoryTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  scenarioCount: {
    fontSize: 13,
    color: '#6B7280',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingTop: 8,
  },
  scenarioCard: {
    backgroundColor: '#1A1A1A',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 4,
    flexDirection: 'row',
    alignItems: 'center',
  },
  scenarioContent: {
    flex: 1,
    marginRight: 12,
  },
  scenarioQuestion: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  scenarioAnswer: {
    fontSize: 14,
    color: '#9CA3AF',
    lineHeight: 20,
  },
  askAiCard: {
    backgroundColor: '#1A1A1A',
    borderRadius: 16,
    padding: 16,
    marginTop: 8,
    marginBottom: 20,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#3B82F630',
  },
  askAiContent: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  askAiIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: '#3B82F620',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  askAiText: {
    flex: 1,
  },
  askAiTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  askAiDesc: {
    fontSize: 13,
    color: '#9CA3AF',
    marginTop: 2,
  },
  disclaimer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 12,
  },
  disclaimerText: {
    flex: 1,
    fontSize: 12,
    color: '#6B7280',
    marginLeft: 8,
    lineHeight: 16,
  },
});
