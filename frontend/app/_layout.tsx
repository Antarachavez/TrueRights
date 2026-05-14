import React from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { LanguageProvider } from '../utils/LanguageContext';

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <LanguageProvider>
        <StatusBar style="dark" />
        <Stack
          screenOptions={{
            headerShown: false,
            contentStyle: { backgroundColor: '#F5F0EB' },
            animation: 'slide_from_right',
          }}
        >
          <Stack.Screen name="index" />
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="category/[id]" />
          <Stack.Screen name="subcategory/[categoryId]/[subcategoryId]" />
          <Stack.Screen name="scenario/[id]" />
          <Stack.Screen name="scenario/generated/[id]" />
          <Stack.Screen 
            name="emergency" 
            options={{ 
              animation: 'fade',
              presentation: 'fullScreenModal' 
            }} 
          />
        </Stack>
      </LanguageProvider>
    </SafeAreaProvider>
  );
}
