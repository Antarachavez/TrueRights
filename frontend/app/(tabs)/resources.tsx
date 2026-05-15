import { useLanguage } from '../../utils/LanguageContext';
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Linking, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import Animated, { FadeInUp } from 'react-native-reanimated';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface ResourceItem {
  name: string;
  contact: string;
  description: string;
}

interface ResourceCategory {
  category: string;
  items: ResourceItem[];
}

export default function ResourcesScreen() {
  const { t } = useLanguage();
  const [resources, setResources] = useState<ResourceCategory[]>([]);
  const [expandedCategories, setExpandedCategories] = useState<string[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchResources();
  }, []);

  const fetchResources = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/resources`);
      setResources(response.data);
      // Expand first category by default
      if (response.data.length > 0) {
        setExpandedCategories([response.data[0].category]);
      }
    } catch (error) {
      console.error('Error fetching resources:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchResources();
    setRefreshing(false);
  };

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => 
      prev.includes(category) 
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  const handleContact = (contact: string) => {
    if (contact.match(/^\d{3}$/)) {
      // 3-digit number like 911 or 988
      Linking.openURL(`tel:${contact}`);
    } else if (contact.match(/^1-\d{3}-\d{3}-\d{4}$/)) {
      // Phone number format
      Linking.openURL(`tel:${contact.replace(/-/g, '')}`);
    } else if (contact.includes('.')) {
      // Website
      const url = contact.startsWith('http') ? contact : `https://${contact}`;
      Linking.openURL(url);
    } else if (contact.toLowerCase().includes('text')) {
      // SMS
      const number = contact.match(/\d+/)?.[0];
      if (number) {
        Linking.openURL(`sms:${number}`);
      }
    }
  };

  const getCategoryIcon = (category: string): keyof typeof Ionicons.glyphMap => {
    const icons: { [key: string]: keyof typeof Ionicons.glyphMap } = {
      'Emergency Hotlines': 'call',
      'Emergency': 'call',
      'Legal Aid': 'briefcase',
      'Legal': 'briefcase',
      'Youth Support': 'heart',
      'Youth': 'heart',
      'Worker Rights': 'construct',
      'Immigration': 'globe',
      'Housing Help': 'home',
      'Consumer': 'cart',
    };
    return icons[category] || 'help-buoy';
  };

  const getCategoryColor = (category: string): string => {
    const colors: { [key: string]: string } = {
      'Emergency Hotlines': '#C45C5C',
      'Emergency': '#C45C5C',
      'Legal Aid': '#1B2A4A',
      'Legal': '#1B2A4A',
      'Youth Support': '#B87878',
      'Youth': '#B87878',
      'Worker Rights': '#B8977B',
      'Immigration': '#6B9E8A',
      'Housing Help': '#7BA37B',
      'Consumer': '#5B8DAF',
    };
    return colors[category] || '#8B9AAB';
  };

  const CAT_KEY_MAP: { [key: string]: string } = {
    'Emergency Hotlines': 'resources.cat.emergency',
    'Emergency': 'resources.cat.emergency',
    'Legal Aid': 'resources.cat.legal',
    'Legal': 'resources.cat.legal',
    'Youth Support': 'resources.cat.youth',
    'Youth': 'resources.cat.youth',
    'Worker Rights': 'resources.cat.worker',
    'Immigration': 'resources.cat.immigration',
    'Housing Help': 'resources.cat.housing',
    'Consumer': 'resources.cat.consumer',
  };

  const translateCategory = (cat: string) => {
    const key = CAT_KEY_MAP[cat];
    return key ? t(key) : cat;
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>{t('resources.title')}</Text>
        <Text style={styles.headerSubtitle}>{t('resources.subtitle')}</Text>
      </View>

      {/* Resources List */}
      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#1B2A4A" />
        }
      >
        {resources.map((resourceCategory, index) => {
          const isExpanded = expandedCategories.includes(resourceCategory.category);
          const color = getCategoryColor(resourceCategory.category);
          
          return (
            <Animated.View 
              key={resourceCategory.category}
              entering={FadeInUp.duration(400).delay(index * 100)}
              style={styles.categoryContainer}
            >
              <TouchableOpacity 
                style={styles.categoryHeader}
                onPress={() => toggleCategory(resourceCategory.category)}
              >
                <View style={styles.categoryHeaderLeft}>
                  <View style={[styles.categoryIcon, { backgroundColor: `${color}20` }]}>
                    <Ionicons name={getCategoryIcon(resourceCategory.category)} size={20} color={color} />
                  </View>
                  <Text style={styles.categoryTitle}>{translateCategory(resourceCategory.category)}</Text>
                </View>
                <Ionicons 
                  name={isExpanded ? "chevron-up" : "chevron-down"} 
                  size={20} 
                  color="#5E6E7D" 
                />
              </TouchableOpacity>

              {isExpanded && (
                <View style={styles.itemsContainer}>
                  {resourceCategory.items.map((item, itemIndex) => (
                    <TouchableOpacity 
                      key={itemIndex}
                      style={styles.resourceItem}
                      onPress={() => handleContact(item.contact)}
                    >
                      <View style={styles.resourceInfo}>
                        <Text style={styles.resourceName}>{item.name}</Text>
                        <Text style={styles.resourceDescription}>{item.description}</Text>
                      </View>
                      <View style={[styles.contactBadge, { backgroundColor: `${color}20` }]}>
                        <Text style={[styles.contactText, { color }]}>{item.contact}</Text>
                        <Ionicons 
                          name={item.contact.includes('.') ? "open-outline" : "call"} 
                          size={14} 
                          color={color} 
                          style={styles.contactIcon}
                        />
                      </View>
                    </TouchableOpacity>
                  ))}
                </View>
              )}
            </Animated.View>
          );
        })}

        {/* Help Tip */}
        <View style={styles.helpTip}>
          <Ionicons name="bulb" size={20} color="#B8977B" />
          <Text style={styles.helpTipText}>
            {t('resources.tapTip')}
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F0EB',
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 16,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1B2A4A',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#5E6E7D',
    marginTop: 4,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingTop: 4,
  },
  categoryContainer: {
    backgroundColor: '#FFFDF9',
    borderRadius: 16,
    marginBottom: 12,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#EDE9E3',
  },
  categoryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
  },
  categoryHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  categoryIcon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  categoryTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1B2A4A',
  },
  itemsContainer: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  resourceItem: {
    backgroundColor: '#F5F0EB',
    borderRadius: 12,
    padding: 14,
    marginBottom: 8,
  },
  resourceInfo: {
    marginBottom: 10,
  },
  resourceName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1B2A4A',
    marginBottom: 4,
  },
  resourceDescription: {
    fontSize: 13,
    color: '#5E6E7D',
  },
  contactBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  contactText: {
    fontSize: 13,
    fontWeight: '600',
  },
  contactIcon: {
    marginLeft: 6,
  },
  helpTip: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#FFFDF9',
    borderRadius: 12,
    padding: 14,
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#EDE9E3',
  },
  helpTipText: {
    flex: 1,
    fontSize: 13,
    color: '#5E6E7D',
    marginLeft: 10,
    lineHeight: 18,
  },
});
