import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Dimensions, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
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
  'globe': 'globe',
  'cart': 'cart',
};

// Pastel gradient pairs for each category
const GRADIENT_MAP: { [key: string]: string[] } = {
  school: ['#7DD3FC', '#93C5FD'],
  work: ['#FCA5A5', '#FDBA74'],
  housing: ['#86EFAC', '#6EE7B7'],
  police: ['#FDA4AF', '#FCA5A5'],
  online: ['#C4B5FD', '#DDD6FE'],
  public: ['#6EE7B7', '#86EFAC'],
  immigration: ['#67E8F9', '#7DD3FC'],
  consumer: ['#FDBA74', '#FCD34D'],
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

  const getGradient = (id: string): string[] => {
    return GRADIENT_MAP[id] || ['#C4B5FD', '#DDD6FE'];
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#C4B5FD" />
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
              style={styles.emergencyButtonOuter}
              onPress={() => router.push('/emergency')}
            >
              <LinearGradient
                colors={['#FDA4AF', '#FB7185']}
                style={styles.emergencyButton}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <Ionicons name="warning" size={20} color="#FFFFFF" />
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </Animated.View>

        {/* Emergency Banner */}
        <Animated.View entering={FadeIn.duration(600).delay(200)}>
          <TouchableOpacity 
            style={styles.emergencyBannerTouch}
            onPress={() => router.push('/emergency')}
            activeOpacity={0.85}
          >
            <LinearGradient
              colors={['#FB7185', '#F472B6', '#C084FC']}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.emergencyBanner}
            >
              <View style={styles.emergencyBannerContent}>
                <Ionicons name="alert-circle" size={24} color="#FFFFFF" />
                <View style={styles.emergencyBannerText}>
                  <Text style={styles.emergencyBannerTitle}>Emergency Mode</Text>
                  <Text style={styles.emergencyBannerDesc}>Stay calm, get scripts, document events</Text>
                </View>
              </View>
              <Ionicons name="chevron-forward" size={24} color="#FFFFFF" />
            </LinearGradient>
          </TouchableOpacity>
        </Animated.View>

        {/* Categories Grid */}
        <View style={styles.categoriesSection}>
          <Text style={styles.sectionTitle}>Choose a Situation</Text>
          {Array.from({ length: Math.ceil(categories.length / 2) }).map((_, rowIndex) => (
            <View key={rowIndex} style={styles.categoryRow}>
              {categories.slice(rowIndex * 2, rowIndex * 2 + 2).map((category) => {
                const gradColors = getGradient(category.id);
                return (
                  <View key={category.id} style={styles.categoryCardOuter}>
                    <TouchableOpacity
                      style={styles.categoryCard}
                      onPress={() => router.push(`/category/${category.id}`)}
                      activeOpacity={0.8}
                    >
                      <LinearGradient
                        colors={[`${gradColors[0]}18`, `${gradColors[1]}08`]}
                        style={styles.categoryCardGradient}
                        start={{ x: 0, y: 0 }}
                        end={{ x: 1, y: 1 }}
                      >
                        <View style={[styles.categoryIcon, { backgroundColor: `${category.color}25` }]}>
                          <Ionicons name={getIconName(category.icon)} size={28} color={category.color} />
                        </View>
                        <Text style={styles.categoryName}>{category.name}</Text>
                        <Text style={styles.categoryDesc} numberOfLines={2}>{category.description}</Text>
                      </LinearGradient>
                    </TouchableOpacity>
                  </View>
                );
              })}
              {categories.slice(rowIndex * 2, rowIndex * 2 + 2).length === 1 && (
                <View style={styles.categoryCard} />
              )}
            </View>
          ))}
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
            {[
              { text: '"I do not consent to a search."', colors: ['#FDA4AF', '#FCA5A5'] },
              { text: '"Am I free to go?"', colors: ['#C4B5FD', '#DDD6FE'] },
              { text: '"I\'d like to contact a parent."', colors: ['#7DD3FC', '#93C5FD'] },
            ].map((script, i) => (
              <TouchableOpacity key={i} style={styles.quickScriptCardTouch} activeOpacity={0.8}>
                <LinearGradient
                  colors={[`${script.colors[0]}15`, `${script.colors[1]}08`]}
                  style={styles.quickScriptCard}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                >
                  <Text style={styles.quickScriptText}>{script.text}</Text>
                </LinearGradient>
              </TouchableOpacity>
            ))}
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
    backgroundColor: '#0D0D14',
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
    color: '#F0F0F8',
  },
  subGreeting: {
    fontSize: 15,
    color: '#9CA3AF',
    marginTop: 4,
  },
  emergencyButtonOuter: {
    borderRadius: 22,
    overflow: 'hidden',
  },
  emergencyButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emergencyBannerTouch: {
    borderRadius: 18,
    overflow: 'hidden',
    marginBottom: 24,
  },
  emergencyBanner: {
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderRadius: 18,
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
    color: 'rgba(255,255,255,0.8)',
    marginTop: 2,
  },
  categoriesSection: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#E5E7EB',
    marginBottom: 16,
  },
  categoryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  categoryCardOuter: {
    width: '48%',
  },
  categoryCard: {
    borderRadius: 18,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#1E1E2E',
  },
  categoryCardGradient: {
    padding: 16,
    minHeight: 130,
  },
  categoryIcon: {
    width: 52,
    height: 52,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  categoryName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#F0F0F8',
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
    color: '#C4B5FD',
    fontWeight: '500',
  },
  quickScriptsScroll: {
    marginHorizontal: -20,
    paddingHorizontal: 20,
  },
  quickScriptCardTouch: {
    marginRight: 12,
    borderRadius: 14,
    overflow: 'hidden',
  },
  quickScriptCard: {
    borderRadius: 14,
    padding: 16,
    minWidth: 200,
    borderWidth: 1,
    borderColor: '#1E1E2E',
  },
  quickScriptText: {
    fontSize: 14,
    color: '#E5E7EB',
    fontStyle: 'italic',
  },
  disclaimerContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#14141E',
    borderRadius: 14,
    padding: 12,
    borderWidth: 1,
    borderColor: '#1E1E2E',
  },
  disclaimerText: {
    flex: 1,
    fontSize: 12,
    color: '#6B7280',
    marginLeft: 8,
    lineHeight: 18,
  },
});
