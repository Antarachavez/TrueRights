import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import axios from 'axios';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface Category {
  id: string;
  name: string;
  icon: string;
  color: string;
  description: string;
}

const ICON_MAP: { [key: string]: keyof typeof Ionicons.glyphMap } = {
  'school': 'school', 'briefcase': 'briefcase', 'home': 'home', 'shield': 'shield',
  'lock': 'lock-closed', 'map-pin': 'location', 'globe': 'globe', 'cart': 'cart',
};

export default function HomeScreen() {
  const router = useRouter();
  const [categories, setCategories] = useState<Category[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => { fetchCategories(); }, []);

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/categories`);
      setCategories(response.data);
    } catch (error) { console.error('Error:', error); }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchCategories();
    setRefreshing(false);
  };

  const getIconName = (icon: string): keyof typeof Ionicons.glyphMap => ICON_MAP[icon] || 'help-circle';

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#C45C5C" />}
      >
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>True Rights</Text>
            <Text style={styles.subGreeting}>What do you need help with?</Text>
          </View>
          <TouchableOpacity style={styles.emergencyBtn} onPress={() => router.push('/emergency')} activeOpacity={0.8}>
            <LinearGradient colors={['#FB7185', '#F43F5E']} style={styles.emergencyBtnGrad} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
              <Ionicons name="warning" size={18} color="#FFFFFF" />
            </LinearGradient>
          </TouchableOpacity>
        </View>

        {/* Emergency Banner */}
        <TouchableOpacity style={styles.emergencyBanner} onPress={() => router.push('/emergency')} activeOpacity={0.85}>
          <LinearGradient colors={['#FB7185', '#EC4899']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.emergencyBannerGrad}>
            <View style={styles.emergencyBannerContent}>
              <Ionicons name="alert-circle" size={22} color="#FFFFFF" />
              <View style={styles.emergencyBannerText}>
                <Text style={styles.emergencyBannerTitle}>Emergency Mode</Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={20} color="rgba(255,255,255,0.7)" />
          </LinearGradient>
        </TouchableOpacity>

        {/* Categories */}
        <Text style={styles.sectionTitle}>Choose a Situation</Text>
        {Array.from({ length: Math.ceil(categories.length / 2) }).map((_, rowIndex) => (
          <View key={rowIndex} style={styles.categoryRow}>
            {categories.slice(rowIndex * 2, rowIndex * 2 + 2).map((cat) => (
              <View key={cat.id} style={styles.categoryCardOuter}>
                <TouchableOpacity style={styles.categoryCard} onPress={() => router.push(`/category/${cat.id}`)} activeOpacity={0.7}>
                  <View style={[styles.categoryIcon, { backgroundColor: `${cat.color}10` }]}>
                    <Ionicons name={getIconName(cat.icon)} size={22} color={cat.color} />
                  </View>
                  <Text style={styles.categoryName}>{cat.name}</Text>
                  <Text style={styles.categoryDesc} numberOfLines={2}>{cat.description}</Text>
                </TouchableOpacity>
              </View>
            ))}
            {categories.slice(rowIndex * 2, rowIndex * 2 + 2).length === 1 && <View style={styles.categoryCardOuter} />}
          </View>
        ))}

        {/* Disclaimer */}
        <View style={styles.disclaimer}>
          <Ionicons name="information-circle" size={14} color="#94A3B8" />
          <Text style={styles.disclaimerText}>Educational information only. Laws vary by state. Not legal advice.</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FAF8F5' },
  scrollView: { flex: 1 },
  scrollContent: { paddingHorizontal: 20, paddingBottom: 24 },
  header: { marginTop: 12, marginBottom: 14, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  greeting: { fontSize: 22, fontWeight: '700', color: '#1B2A4A', letterSpacing: -0.5 },
  subGreeting: { fontSize: 13, color: '#5E6E7D', marginTop: 2 },
  emergencyBtn: { borderRadius: 18, overflow: 'hidden' },
  emergencyBtnGrad: { width: 36, height: 36, borderRadius: 18, justifyContent: 'center', alignItems: 'center' },
  emergencyBanner: { borderRadius: 14, overflow: 'hidden', marginBottom: 16 },
  emergencyBannerGrad: { padding: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  emergencyBannerContent: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  emergencyBannerText: { marginLeft: 12 },
  emergencyBannerTitle: { fontSize: 16, fontWeight: '600', color: '#FFFFFF' },
  emergencyBannerDesc: { fontSize: 13, color: 'rgba(255,255,255,0.8)', marginTop: 1 },
  sectionTitle: { fontSize: 15, fontWeight: '600', color: '#1B2A4A', marginBottom: 12 },
  categoryRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 10 },
  categoryCardOuter: { width: '48%' },
  categoryCard: { backgroundColor: '#FFFDF9', borderRadius: 14, padding: 14, minHeight: 110, borderWidth: 1, borderColor: '#EDE9E3' },
  categoryIcon: { width: 42, height: 42, borderRadius: 12, justifyContent: 'center', alignItems: 'center', marginBottom: 10 },
  categoryName: { fontSize: 14, fontWeight: '600', color: '#1B2A4A', marginBottom: 3 },
  categoryDesc: { fontSize: 12, color: '#94A3B8', lineHeight: 16 },
  disclaimer: { flexDirection: 'row', alignItems: 'flex-start', backgroundColor: '#FFFDF9', borderRadius: 12, padding: 12, marginTop: 12, borderWidth: 1, borderColor: '#EDE9E3' },
  disclaimerText: { flex: 1, fontSize: 12, color: '#94A3B8', marginLeft: 8, lineHeight: 18 },
});
