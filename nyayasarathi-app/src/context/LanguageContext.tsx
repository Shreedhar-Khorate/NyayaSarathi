'use client';

import React, { createContext, useContext, useEffect, ReactNode, useCallback } from 'react';
import { DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES, Language } from '../i18n/config';
import { useTranslationHelper } from '../i18n/useTranslation';

interface LanguageContextType {
  language: string;
  setLanguage: (code: string) => void;
  currentLanguageObj: Language;
  t: (key: string, fallback?: string) => any;
  translateText: (text: string) => Promise<string>;
  isTranslating: boolean;
}

const defaultLangObj: Language = SUPPORTED_LANGUAGES[0] || {
  code: 'en',
  name: 'English',
  nativeName: 'English',
  flag: '🇬🇧',
  script: 'Latin',
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const language = DEFAULT_LANGUAGE;
  const currentLanguageObj = defaultLangObj;
  const { t: staticT } = useTranslationHelper('en');

  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem('nyayasarathi_lang');
        localStorage.removeItem('nyaya_gemini_tr_hi');
        localStorage.removeItem('nyaya_gemini_tr_mr');
      } catch {
        // ignore
      }
      if (typeof document !== 'undefined') {
        document.documentElement.setAttribute('lang', 'en');
        document.documentElement.setAttribute('data-script', 'latin');
      }
    }
  }, []);

  const setLanguage = useCallback((_code: string) => {
    // English-only application default
  }, []);

  const translateText = useCallback(async (text: string): Promise<string> => {
    return text;
  }, []);

  const t = useCallback(
    (key: string, fallback?: string): any => {
      const res = staticT(key);
      if (res && res !== key) {
        return res;
      }
      return fallback || res || key;
    },
    [staticT]
  );

  return (
    <LanguageContext.Provider
      value={{
        language,
        setLanguage,
        currentLanguageObj,
        t,
        translateText,
        isTranslating: false,
      }}
    >
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
