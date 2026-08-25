export interface Language {
  code: string;
  name: string;
  nativeName: string;
  flag: string;
  script: string;
}

export const SUPPORTED_LANGUAGES: Language[] = [
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇬🇧', script: 'Latin' },
  { code: 'hi', name: 'Hindi', nativeName: 'हिंदी', flag: '🇮🇳', script: 'Devanagari' },
  { code: 'mr', name: 'Marathi', nativeName: 'मराठी', flag: '🇮🇳', script: 'Devanagari' },
];

export const DEFAULT_LANGUAGE = 'en';
