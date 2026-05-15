import { useLanguage } from '../../utils/LanguageContext';
import React, { useState, useEffect, useMemo } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  RefreshControl, Alert, TextInput, FlatList, Platform
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Clipboard from 'expo-clipboard';
import * as Haptics from 'expo-haptics';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import Animated, { FadeInUp, FadeIn } from 'react-native-reanimated';
import { fuzzySearchScripts } from '../../utils/fuzzySearch';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface Script {
  id: string;
  title: string;
  content: string;
  category: string;
  category_name?: string;
  subcategory?: string;
  subcategory_name?: string;
}

interface SavedScript {
  id: string;
  device_id: string;
  title: string;
  content: string;
  category: string;
  saved_at: string;
}

interface CategoryData {
  name: string;
  icon: string;
  color: string;
  scripts: Script[];
  count: number;
}

type ViewMode = 'categories' | 'category-detail' | 'saved';

export default function ScriptsScreen() {
  const { lang, t } = useLanguage();
  const [categoriesData, setCategoriesData] = useState<Record<string, CategoryData>>({});
  const [savedScripts, setSavedScripts] = useState<SavedScript[]>([]);
  const [viewMode, setViewMode] = useState<ViewMode>('categories');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [deviceId, setDeviceId] = useState('');
  const [loading, setLoading] = useState(true);

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
      await fetchAll(storedDeviceId);
    } catch (error) {
      console.error('Error initializing:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAll = async (devId?: string) => {
    try {
      const [catRes, savedRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/scripts/by-category?lang=${lang}`),
        axios.get(`${BACKEND_URL}/api/scripts/saved/${devId || deviceId}`)
      ]);
      setCategoriesData(catRes.data);
      setSavedScripts(savedRes.data);
    } catch (error) {
      console.error('Error fetching:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchAll();
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
      await fetchAll();
      Alert.alert(t('scripts.scriptSavedTitle'), t('scripts.scriptSavedBody'));
    } catch (error) {
      console.error('Error saving script:', error);
      Alert.alert(t('scripts.errorTitle'), t('scripts.errorSave'));
    }
  };

  const deleteScript = async (scriptId: string) => {
    Alert.alert(
      t('scripts.deleteTitle'),
      t('scripts.deleteConfirm'),
      [
        { text: t('common.cancel'), style: 'cancel' },
        {
          text: t('common.delete'),
          style: 'destructive',
          onPress: async () => {
            try {
              await axios.delete(`${BACKEND_URL}/api/scripts/saved/${scriptId}`);
              Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
              await fetchAll();
            } catch (error) {
              console.error('Error deleting script:', error);
            }
          }
        }
      ]
    );
  };

  const getCategoryColor = (category: string) => {
    return categoriesData[category]?.color || '#1B2A4A';
  };

  // Filtered scripts for category detail view
  const filteredCategoryScripts = useMemo(() => {
    if (!selectedCategory || !categoriesData[selectedCategory]) return [];
    const scripts = categoriesData[selectedCategory].scripts;
    if (!searchQuery.trim()) return scripts;
    // Use fuzzy search for better matching
    return fuzzySearchScripts(searchQuery, scripts.map(s => ({...s, question: s.title})))
      .map(result => scripts.find(s => s.id === result.id)!)
      .filter(Boolean);
  }, [selectedCategory, categoriesData, searchQuery]);

  // Filtered saved scripts
  const filteredSavedScripts = useMemo(() => {
    if (!searchQuery.trim()) return savedScripts;
    return fuzzySearchScripts(searchQuery, savedScripts.map(s => ({...s, question: s.title})))
      .map(result => savedScripts.find(s => s.id === result.id)!)
      .filter(Boolean);
  }, [savedScripts, searchQuery]);

  // Filtered categories for category grid view
  const filteredCategories = useMemo(() => {
    const entries = Object.entries(categoriesData);
    if (!searchQuery.trim()) return entries;
    const q = searchQuery.toLowerCase();
    // Show category if its name matches OR any of its scripts match fuzzy search
    return entries.filter(([_, data]) =>
      data.name.toLowerCase().includes(q) ||
      fuzzySearchScripts(searchQuery, data.scripts.map(s => ({...s, question: s.title}))).length > 0
    );
  }, [categoriesData, searchQuery]);

  // Global search across ALL scripts (for categories view search)
  const globalSearchResults = useMemo(() => {
    if (!searchQuery.trim() || viewMode !== 'categories') return [];
    const allScripts: Script[] = [];
    Object.values(categoriesData).forEach(catData => {
      catData.scripts.forEach(script => allScripts.push(script));
    });
    return fuzzySearchScripts(searchQuery, allScripts.map(s => ({...s, question: s.title})))
      .map(result => allScripts.find(s => s.id === result.id)!)
      .filter(Boolean)
      .slice(0, 30);
  }, [categoriesData, searchQuery, viewMode]);

  const totalScripts = useMemo(() => {
    return Object.values(categoriesData).reduce((sum, cat) => sum + cat.count, 0);
  }, [categoriesData]);

  const openCategory = (catId: string) => {
    setSelectedCategory(catId);
    setSearchQuery('');
    setViewMode('category-detail');
  };

  const goBack = () => {
    setSearchQuery('');
    setViewMode('categories');
    setSelectedCategory(null);
  };

  const goToSaved = () => {
    setSearchQuery('');
    setViewMode('saved');
    setSelectedCategory(null);
  };

  const goToCategories = () => {
    setSearchQuery('');
    setViewMode('categories');
    setSelectedCategory(null);
  };

  // Script card component
  const ScriptCard = ({ script, isSaved = false, index = 0 }: { script: Script | SavedScript; isSaved?: boolean; index?: number }) => {
    const color = getCategoryColor(script.category);
    const isCopied = copiedId === script.id;
    const catData = categoriesData[script.category];

    return (
      <View style={styles.scriptCard} key={script.id}>
        <View style={styles.scriptHeader}>
          <View style={styles.scriptBadges}>
            <View style={[styles.categoryBadge, { backgroundColor: `${color}20` }]}>
              <Ionicons name={(catData?.icon || 'document') as any} size={12} color={color} />
              <Text style={[styles.categoryText, { color }]}>
                {catData?.name || script.category}
              </Text>
            </View>
            {'subcategory_name' in script && script.subcategory_name && (
              <View style={[styles.subBadge]}>
                <Text style={styles.subBadgeText}>{script.subcategory_name}</Text>
              </View>
            )}
          </View>
          <View style={styles.scriptActions}>
            <TouchableOpacity
              style={[styles.actionButton, isCopied && styles.actionButtonCopied]}
              onPress={() => copyToClipboard(script.content, script.id)}
              activeOpacity={0.7}
            >
              <Ionicons
                name={isCopied ? "checkmark" : "copy-outline"}
                size={18}
                color={isCopied ? "#10B981" : "#5E6E7D"}
              />
            </TouchableOpacity>
            {!isSaved ? (
              <TouchableOpacity
                style={styles.actionButton}
                onPress={() => saveScript(script as Script)}
                activeOpacity={0.7}
              >
                <Ionicons name="bookmark-outline" size={18} color="#5E6E7D" />
              </TouchableOpacity>
            ) : (
              <TouchableOpacity
                style={styles.actionButton}
                onPress={() => deleteScript(script.id)}
                activeOpacity={0.7}
              >
                <Ionicons name="trash-outline" size={18} color="#EF4444" />
              </TouchableOpacity>
            )}
          </View>
        </View>
        <Text style={styles.scriptTitle} numberOfLines={2}>{script.title}</Text>
        <View style={styles.scriptContentContainer}>
          <Text style={styles.quoteIcon}>{"\u201C"}</Text>
          <Text style={styles.scriptContent}>{script.content}</Text>
          <Text style={styles.quoteIconEnd}>{"\u201D"}</Text>
        </View>
      </View>
    );
  };

  // Search bar component
  const SearchBar = ({ placeholder }: { placeholder: string }) => (
    <View style={styles.searchContainer}>
      <View style={styles.searchBar}>
        <Ionicons name="search" size={18} color="#94A3B8" />
        <TextInput
          style={styles.searchInput}
          placeholder={placeholder}
          placeholderTextColor="#94A3B8"
          value={searchQuery}
          onChangeText={setSearchQuery}
          autoCorrect={false}
          returnKeyType="search"
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => setSearchQuery('')} activeOpacity={0.7}>
            <Ionicons name="close-circle" size={18} color="#94A3B8" />
          </TouchableOpacity>
        )}
      </View>
    </View>
  );

  // CATEGORY GRID VIEW (with global search results)
  const renderCategoriesView = () => (
    <ScrollView
      style={styles.scrollView}
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
      keyboardShouldPersistTaps="handled"
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#1B2A4A" />
      }
    >
      {/* Show global search results when searching */}
      {searchQuery.trim() && globalSearchResults.length > 0 ? (
        <>
          <Text style={styles.sectionLabel}>{globalSearchResults.length} {t('scripts.scriptsFound')}</Text>
          {globalSearchResults.map((script, index) => (
            <ScriptCard key={script.id} script={script} index={index} />
          ))}
        </>
      ) : searchQuery.trim() && globalSearchResults.length === 0 ? (
        <View style={styles.emptyState}>
          <Ionicons name="search-outline" size={44} color="#5E6E7D" />
          <Text style={styles.emptyTitle}>{t('scripts.noScriptsMatch')} "{searchQuery}"</Text>
          <Text style={styles.emptyText}>{t('scripts.tryDifferent')}</Text>
        </View>
      ) : (
        <>
          {/* Saved Scripts Quick Access */}
          <TouchableOpacity
            style={styles.savedBanner}
            onPress={goToSaved}
            activeOpacity={0.7}
          >
            <View style={styles.savedBannerLeft}>
              <View style={styles.savedIconContainer}>
                <Ionicons name="bookmark" size={20} color="#F59E0B" />
              </View>
              <View>
                <Text style={styles.savedBannerTitle}>{t('scripts.mySavedScripts')}</Text>
                <Text style={styles.savedBannerCount}>{savedScripts.length} {t('scripts.saved')}</Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#94A3B8" />
          </TouchableOpacity>

          {/* Category Grid */}
          <Text style={styles.sectionLabel}>{t('scripts.browseCategory')}</Text>
          <View style={styles.categoryGrid}>
            {filteredCategories.map(([catId, catData], index) => (
              <Animated.View
                key={catId}
                entering={FadeInUp.delay(index * 60).duration(400)}
                style={styles.categoryCardWrapper}
              >
                <TouchableOpacity
                  style={styles.categoryCard}
                  onPress={() => openCategory(catId)}
                  activeOpacity={0.7}
                >
                  <View style={[styles.categoryIconCircle, { backgroundColor: `${catData.color}20` }]}>
                    <Ionicons name={catData.icon as any} size={28} color={catData.color} />
                  </View>
                  <Text style={styles.categoryCardName}>{catData.name}</Text>
                  <Text style={styles.categoryCardCount}>{catData.count} scripts</Text>
                </TouchableOpacity>
              </Animated.View>
            ))}
          </View>
        </>
      )}
    </ScrollView>
  );

  // CATEGORY DETAIL VIEW
  const renderCategoryDetail = () => {
    const catData = selectedCategory ? categoriesData[selectedCategory] : null;
    if (!catData) return null;

    // Group scripts by subcategory
    const grouped: Record<string, Script[]> = {};
    filteredCategoryScripts.forEach(script => {
      const subName = script.subcategory_name || 'General';
      if (!grouped[subName]) grouped[subName] = [];
      grouped[subName].push(script);
    });

    return (
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={catData.color} />
        }
      >
        {Object.entries(grouped).map(([subName, scripts]) => (
          <View key={subName} style={styles.subcategorySection}>
            <View style={styles.subcategoryHeader}>
              <View style={[styles.subcategoryDot, { backgroundColor: catData.color }]} />
              <Text style={styles.subcategoryTitle}>{subName}</Text>
              <Text style={styles.subcategoryCount}>{scripts.length}</Text>
            </View>
            {scripts.map((script, index) => (
              <ScriptCard key={script.id} script={script} index={index} />
            ))}
          </View>
        ))}

        {filteredCategoryScripts.length === 0 && searchQuery.length > 0 && (
          <View style={styles.emptyState}>
            <Ionicons name="search-outline" size={44} color="#5E6E7D" />
            <Text style={styles.emptyTitle}>{t('scripts.noScriptsMatch')} "{searchQuery}"</Text>
            <Text style={styles.emptyText}>{t('scripts.trySearch')}</Text>
          </View>
        )}
      </ScrollView>
    );
  };

  // SAVED SCRIPTS VIEW
  const renderSavedView = () => (
    <ScrollView
      style={styles.scrollView}
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#F59E0B" />
      }
    >
      {filteredSavedScripts.length > 0 ? (
        filteredSavedScripts.map((script, index) => (
          <ScriptCard key={script.id} script={script} isSaved index={index} />
        ))
      ) : savedScripts.length === 0 ? (
        <View style={styles.emptyState}>
          <Ionicons name="bookmark-outline" size={48} color="#5E6E7D" />
          <Text style={styles.emptyTitle}>{t('scripts.noSaved')}</Text>
          <Text style={styles.emptyText}>{t('scripts.tapBookmark')}</Text>
        </View>
      ) : (
        <View style={styles.emptyState}>
          <Ionicons name="search-outline" size={44} color="#5E6E7D" />
          <Text style={styles.emptyTitle}>{t('scripts.noResultsFor')} "{searchQuery}"</Text>
          <Text style={styles.emptyText}>{t('scripts.trySearch')}</Text>
        </View>
      )}
    </ScrollView>
  );

  // Get header info based on view mode
  const getHeaderInfo = () => {
    if (viewMode === 'category-detail' && selectedCategory) {
      const catData = categoriesData[selectedCategory];
      return {
        title: catData?.name || t('scripts.title'),
        subtitle: `${catData?.count || 0} ${t('scripts.readyPhrases')}`,
        color: catData?.color || '#1B2A4A',
        searchPlaceholder: t('scripts.searchInCategory').replace('{cat}', catData?.name || '')
      };
    }
    if (viewMode === 'saved') {
      return {
        title: t('scripts.savedHeader'),
        subtitle: `${savedScripts.length} ${t('scripts.savedPhrases')}`,
        color: '#F59E0B',
        searchPlaceholder: t('scripts.searchSaved')
      };
    }
    return {
      title: t('scripts.title'),
      subtitle: `${totalScripts} ${t('scripts.readyPhrases')}`,
      color: '#1B2A4A',
      searchPlaceholder: t('scripts.searchAll')
    };
  };

  const headerInfo = getHeaderInfo();

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerRow}>
          {viewMode !== 'categories' && (
            <TouchableOpacity
              style={styles.backButton}
              onPress={goBack}
              activeOpacity={0.7}
            >
              <Ionicons name="arrow-back" size={24} color="#1B2A4A" />
            </TouchableOpacity>
          )}
          <View style={styles.headerTextContainer}>
            <Text style={styles.headerTitle}>{headerInfo.title}</Text>
            <Text style={styles.headerSubtitle}>{headerInfo.subtitle}</Text>
          </View>
          {viewMode === 'categories' && (
            <TouchableOpacity
              style={styles.savedButton}
              onPress={goToSaved}
              activeOpacity={0.7}
            >
              <Ionicons name="bookmark" size={20} color="#F59E0B" />
              {savedScripts.length > 0 && (
                <View style={styles.savedBadge}>
                  <Text style={styles.savedBadgeText}>{savedScripts.length}</Text>
                </View>
              )}
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Search */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <Ionicons name="search" size={18} color="#94A3B8" />
          <TextInput
            style={styles.searchInput}
            placeholder={headerInfo.searchPlaceholder}
            placeholderTextColor="#94A3B8"
            value={searchQuery}
            onChangeText={setSearchQuery}
            autoCorrect={false}
            returnKeyType="search"
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')} activeOpacity={0.7}>
              <Ionicons name="close-circle" size={18} color="#94A3B8" />
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Content */}
      {viewMode === 'categories' && renderCategoriesView()}
      {viewMode === 'category-detail' && renderCategoryDetail()}
      {viewMode === 'saved' && renderSavedView()}
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
    paddingTop: 12,
    paddingBottom: 8,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#FFFDF9',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  headerTextContainer: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 26,
    fontWeight: '700',
    color: "#1B2A4A",
  },
  headerSubtitle: {
    fontSize: 13,
    color: '#5E6E7D',
    marginTop: 2,
  },
  savedButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#FFFDF9',
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  savedBadge: {
    position: 'absolute',
    top: 4,
    right: 4,
    backgroundColor: '#EF4444',
    borderRadius: 8,
    minWidth: 16,
    height: 16,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 4,
  },
  savedBadgeText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '700',
  },
  // Search
  searchContainer: {
    paddingHorizontal: 20,
    paddingVertical: 8,
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFDF9',
    borderRadius: 12,
    paddingHorizontal: 14,
    height: 44,
    borderWidth: 1,
    borderColor: '#EDE9E3',
  },
  searchInput: {
    flex: 1,
    color: "#1B2A4A",
    fontSize: 15,
    marginLeft: 10,
    paddingVertical: 0,
  },
  // Scroll
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingTop: 8,
    paddingBottom: 40,
  },
  // Saved Banner
  savedBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FFFDF9',
    borderRadius: 16,
    padding: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#EDE9E3',
  },
  savedBannerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  savedIconContainer: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: '#F59E0B20',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  savedBannerTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: "#1B2A4A",
  },
  savedBannerCount: {
    fontSize: 13,
    color: '#5E6E7D',
    marginTop: 2,
  },
  // Section
  sectionLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#5E6E7D',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 14,
  },
  // Category Grid
  categoryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  categoryCardWrapper: {
    width: '48%',
    marginBottom: 12,
  },
  categoryCard: {
    backgroundColor: '#FFFDF9',
    borderRadius: 16,
    padding: 18,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#EDE9E3',
    minHeight: 140,
    justifyContent: 'center',
  },
  categoryIconCircle: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  categoryCardName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1B2A4A',
    textAlign: 'center',
  },
  categoryCardCount: {
    fontSize: 12,
    color: '#94A3B8',
    marginTop: 4,
  },
  // Subcategory sections
  subcategorySection: {
    marginBottom: 20,
  },
  subcategoryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#EDE9E3',
  },
  subcategoryDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 10,
  },
  subcategoryTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    flex: 1,
  },
  subcategoryCount: {
    fontSize: 13,
    color: '#94A3B8',
    backgroundColor: '#FFFDF9',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
    overflow: 'hidden',
  },
  // Script Card
  scriptCard: {
    backgroundColor: '#FFFDF9',
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#EDE9E3',
  },
  scriptHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  scriptBadges: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    flex: 1,
    gap: 6,
  },
  categoryBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    gap: 4,
  },
  categoryText: {
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  subBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    backgroundColor: '#EDE9E3',
  },
  subBadgeText: {
    fontSize: 11,
    fontWeight: '500',
    color: '#5E6E7D',
  },
  scriptActions: {
    flexDirection: 'row',
    gap: 6,
    marginLeft: 8,
  },
  actionButton: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: '#EDE9E3',
    justifyContent: 'center',
    alignItems: 'center',
  },
  actionButtonCopied: {
    backgroundColor: '#10B98120',
  },
  scriptTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#5E6E7D',
    marginBottom: 8,
  },
  scriptContentContainer: {
    backgroundColor: '#F5F0EB',
    borderRadius: 10,
    padding: 12,
    position: 'relative',
  },
  quoteIcon: {
    fontSize: 22,
    color: '#5E6E7D',
    position: 'absolute',
    top: 2,
    left: 6,
  },
  quoteIconEnd: {
    fontSize: 22,
    color: '#5E6E7D',
    position: 'absolute',
    bottom: -4,
    right: 6,
  },
  scriptContent: {
    fontSize: 15,
    color: '#374151',
    lineHeight: 22,
    paddingHorizontal: 14,
    fontStyle: 'italic',
    fontWeight: '500',
  },
  // Empty State
  emptyState: {
    alignItems: 'center',
    paddingTop: 60,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: "#1B2A4A",
    marginTop: 16,
  },
  emptyText: {
    fontSize: 14,
    color: '#94A3B8',
    textAlign: 'center',
    marginTop: 8,
    paddingHorizontal: 40,
  },
});
