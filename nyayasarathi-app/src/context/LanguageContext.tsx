'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES, Language } from '../i18n/config';
import { useTranslationHelper } from '../i18n/useTranslation';

interface LanguageContextType {
  language: string;
  setLanguage: (code: string) => void;
  currentLanguageObj: Language;
  t: (key: string) => any;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<string>(DEFAULT_LANGUAGE);

  const DEVANAGARI_CODES = ['hi', 'mr'];

  const applyScriptAttribute = (code: string) => {
    if (typeof document !== 'undefined') {
      const isDevanagari = DEVANAGARI_CODES.includes(code);
      document.documentElement.setAttribute('data-script', isDevanagari ? 'devanagari' : 'latin');
      document.documentElement.setAttribute('lang', code);
    }
  };

  useEffect(() => {
    const saved = localStorage.getItem('nyayasarathi_lang');
    const activeCode = saved && SUPPORTED_LANGUAGES.some((l) => l.code === saved) ? saved : DEFAULT_LANGUAGE;
    setLanguageState(activeCode);
    applyScriptAttribute(activeCode);
  }, []);

  const setLanguage = (code: string) => {
    if (SUPPORTED_LANGUAGES.some((l) => l.code === code)) {
      setLanguageState(code);
      localStorage.setItem('nyayasarathi_lang', code);
      applyScriptAttribute(code);
    }
  };

  const currentLanguageObj =
    SUPPORTED_LANGUAGES.find((l) => l.code === language) || SUPPORTED_LANGUAGES[0];

  const { t } = useTranslationHelper(language);

  return (
    <LanguageContext.Provider value={{ language, setLanguage, currentLanguageObj, t }}>
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
