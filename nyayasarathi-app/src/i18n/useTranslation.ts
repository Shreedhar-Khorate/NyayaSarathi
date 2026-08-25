import { useCallback } from 'react';
import en from './locales/en.json';
import hi from './locales/hi.json';
import mr from './locales/mr.json';

const dictionaries: Record<string, any> = {
  en,
  hi,
  mr,
};

export function useTranslationHelper(language: string) {
  const t = useCallback(
    (key: string): any => {
      const parts = key.split('.');
      let dict = dictionaries[language] || dictionaries['en'];
      
      for (const part of parts) {
        if (dict && dict[part] !== undefined) {
          dict = dict[part];
        } else {
          // Fallback to English dictionary if key is missing in target language
          let fallback = dictionaries['en'];
          for (const fbPart of parts) {
            if (fallback && fallback[fbPart] !== undefined) {
              fallback = fallback[fbPart];
            } else {
              return key;
            }
          }
          return typeof fallback === 'string' || Array.isArray(fallback) ? fallback : key;
        }
      }
      
      return typeof dict === 'string' || Array.isArray(dict) ? dict : key;
    },
    [language]
  );

  return { t };
}
