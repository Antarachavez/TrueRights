import React from 'react';
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { StyleSheet, Platform } from 'react-native';
import { useLanguage } from '../../utils/LanguageContext';

export default function TabLayout() {
  const { t } = useLanguage();

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: styles.tabBar,
        tabBarActiveTintColor: '#1B2A4A',
        tabBarInactiveTintColor: '#9BA5AD',
        tabBarLabelStyle: styles.tabBarLabel,
        tabBarIconStyle: styles.tabBarIcon,
      }}
    >
      <Tabs.Screen name="home" options={{ title: t('tab.home'), tabBarIcon: ({ color, size }) => <Ionicons name="home" size={size} color={color} /> }} />
      <Tabs.Screen name="scripts" options={{ title: t('tab.scripts'), tabBarIcon: ({ color, size }) => <Ionicons name="document-text" size={size} color={color} /> }} />
      <Tabs.Screen name="resources" options={{ title: t('tab.resources'), tabBarIcon: ({ color, size }) => <Ionicons name="help-buoy" size={size} color={color} /> }} />
      <Tabs.Screen name="chat" options={{ title: t('tab.askAi'), tabBarIcon: ({ color, size }) => <Ionicons name="chatbubbles" size={size} color={color} /> }} />
      <Tabs.Screen name="settings" options={{ title: t('tab.settings'), tabBarIcon: ({ color, size }) => <Ionicons name="settings-outline" size={size} color={color} /> }} />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: '#FFFDF9',
    borderTopColor: '#EDE9E3',
    borderTopWidth: 1,
    paddingTop: 6,
    paddingBottom: Platform.OS === 'ios' ? 24 : 8,
    height: Platform.OS === 'ios' ? 84 : 60,
    elevation: 0,
  },
  tabBarLabel: { fontSize: 11, fontWeight: '500' },
  tabBarIcon: { marginBottom: -2 },
});
