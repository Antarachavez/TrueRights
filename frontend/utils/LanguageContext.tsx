import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Language } from './i18n';
import { t as translate } from './i18n';

interface LanguageContextType {
  lang: Language;
  setLanguage: (lang: Language) => Promise<void>;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextType>({
  lang: 'en',
  setLanguage: async () => {},
  t: (key: string) => key,
});

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLang] = useState<Language>('en');
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem('app_language').then((stored) => {
      if (stored && ['en', 'es', 'fr', 'zh'].includes(stored)) {
        setLang(stored as Language);
      }
      setLoaded(true);
    });
  }, []);

  const setLanguage = async (newLang: Language) => {
    setLang(newLang);
    await AsyncStorage.setItem('app_language', newLang);
  };

  const t = (key: string) => translate(key, lang);

  if (!loaded) return null;

  return (
    <LanguageContext.Provider value={{ lang, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}
