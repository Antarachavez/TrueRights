import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Dimensions, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import Animated, { FadeInUp, FadeIn } from 'react-native-reanimated';
import axios from 'axios';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;
const { width } = Dimensions.get('window');

interface Category {
  id: string;
  name: string;
  icon: string;
  color: string;
  description: string;
}

const ICON_MAP: { [key: string]: keyof typeof Ionicons.glyphMap } = {
  'school': 'school',
  'briefcase': 'briefcase',
  'home': 'home',
  'shield': 'shield',
  'lock': 'lock-closed',
  'map-pin': 'location',
};

export default function HomeScreen() {
  const router = useRouter();
  const [categories, setCategories] = useState<Category[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/categories`);
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchCategories();
    setRefreshing(false);
  };

  const getIconName = (icon: string): keyof typeof Ionicons.glyphMap => {
    return ICON_MAP[icon] || 'help-circle';
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#3B82F6" />
        }
      >
        {/* Header */}
        <Animated.View entering={FadeInUp.duration(600)} style={styles.header}>
          <View style={styles.headerTop}>
            <View>
              <Text style={styles.greeting}>Know Your Rights</Text>
              <Text style={styles.subGreeting}>What do you need help with?</Text>
            </View>
            <TouchableOpacity 
              style={styles.emergencyButton}
              onPress={() => router.push('/emergency')}
            >
              <Ionicons name="warning" size={20} color="#FFFFFF" />
            </TouchableOpacity>
          </View>
        </Animated.View>

        {/* Emergency Banner */}
        <Animated.View entering={FadeIn.duration(600).delay(200)}>
          <TouchableOpacity 
            style={styles.emergencyBanner}
            onPress={() => router.push('/emergency')}
          >
            <View style={styles.emergencyBannerContent}>
              <Ionicons name="alert-circle" size={24} color="#FFFFFF" />
              <View style={styles.emergencyBannerText}>
                <Text style={styles.emergencyBannerTitle}>Emergency Mode</Text>
                <Text style={styles.emergencyBannerDesc}>Stay calm, get scripts, document events</Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={24} color="#FFFFFF" />
          </TouchableOpacity>
        </Animated.View>

        {/* Categories Grid */}
        <View style={styles.categoriesSection}>
          <Text style={styles.sectionTitle}>Choose a Situation</Text>
          <View style={styles.categoriesGrid}>
            {categories.map((category, index) => (
              <Animated.View 
                key={category.id}
                entering={FadeInUp.duration(500).delay(300 + index * 100)}
                style={styles.categoryCardWrapper}
              >
                <TouchableOpacity
                  style={[styles.categoryCard, { borderColor: category.color }]}
                  onPress={() => router.push(`/category/${category.id}`)}
                >
                  <View style={[styles.categoryIcon, { backgroundColor: `${category.color}20` }]}>
                    <Ionicons name={getIconName(category.icon)} size={28} color={category.color} />
                  </View>
                  <Text style={styles.categoryName}>{category.name}</Text>
                  <Text style={styles.categoryDesc} numberOfLines={2}>{category.description}</Text>
                </TouchableOpacity>
              </Animated.View>
            ))}
          </View>
        </View>

        {/* Quick Scripts */}
        <Animated.View entering={FadeIn.duration(600).delay(800)} style={styles.quickScriptsSection}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Quick Scripts</Text>
            <TouchableOpacity onPress={() => router.push('/(tabs)/scripts')}>
              <Text style={styles.seeAllText}>See All</Text>
            </TouchableOpacity>
          </View>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.quickScriptsScroll}>
            <TouchableOpacity style={styles.quickScriptCard}>
              <Text style={styles.quickScriptText}>"I do not consent to a search."</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.quickScriptCard}>
              <Text style={styles.quickScriptText}>"Am I free to go?"</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.quickScriptCard}>
              <Text style={styles.quickScriptText}>"I'd like to contact a parent."</Text>
            </TouchableOpacity>
          </ScrollView>
        </Animated.View>

        {/* Disclaimer */}
        <View style={styles.disclaimerContainer}>
          <Ionicons name="information-circle" size={16} color="#6B7280" />
          <Text style={styles.disclaimerText}>
            This app provides educational information only. Laws vary by state. This is not legal advice.
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
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingBottom: 24,
  },
  header: {
    marginTop: 16,
    marginBottom: 20,
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  greeting: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  subGreeting: {
    fontSize: 15,
    color: '#9CA3AF',
    marginTop: 4,
  },
  emergencyButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#EF4444',
    justifyContent: 'center',
    alignItems: 'center',
  },
  emergencyBanner: {
    backgroundColor: '#DC2626',
    borderRadius: 16,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  emergencyBannerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  emergencyBannerText: {
    marginLeft: 12,
  },
  emergencyBannerTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  emergencyBannerDesc: {
    fontSize: 13,
    color: '#FCA5A5',
    marginTop: 2,
  },
  categoriesSection: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 16,
  },
  categoriesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  categoryCardWrapper: {
    width: (width - 52) / 2,
    marginBottom: 12,
  },
  categoryCard: {
    backgroundColor: '#1A1A1A',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#2D2D2D',
  },
  categoryIcon: {
    width: 52,
    height: 52,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  categoryName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  categoryDesc: {
    fontSize: 12,
    color: '#9CA3AF',
    lineHeight: 16,
  },
  quickScriptsSection: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  seeAllText: {
    fontSize: 14,
    color: '#3B82F6',
    fontWeight: '500',
  },
  quickScriptsScroll: {
    marginHorizontal: -20,
    paddingHorizontal: 20,
  },
  quickScriptCard: {
    backgroundColor: '#1A1A1A',
    borderRadius: 12,
    padding: 16,
    marginRight: 12,
    minWidth: 200,
    borderWidth: 1,
    borderColor: '#2D2D2D',
  },
  quickScriptText: {
    fontSize: 14,
    color: '#FFFFFF',
    fontStyle: 'italic',
  },
  disclaimerContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#1A1A1A',
    borderRadius: 12,
    padding: 12,
  },
  disclaimerText: {
    flex: 1,
    fontSize: 12,
    color: '#6B7280',
    marginLeft: 8,
    lineHeight: 18,
  },
});
