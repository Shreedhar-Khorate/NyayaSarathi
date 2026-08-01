import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/app/**/*.{ts,tsx}', './src/components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        obsidian: '#0B0F17',
        slate: {
          DEFAULT: '#111827',
          raised: '#161D2B',
        },
        amber: {
          DEFAULT: '#F59E0B',
          deep: '#D97706',
        },
        indigo: {
          deep: '#3730A3',
        },
        cobalt: '#1E3A8A',
        cream: '#F9FAFB',
        ash: '#9CA3AF',
      },
      fontFamily: {
        display: ['var(--font-playfair)', 'serif'],
        sans: ['var(--font-jakarta)', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        gold: '0 0 40px -8px rgba(245, 158, 11, 0.35)',
        cobalt: '0 0 40px -8px rgba(30, 58, 138, 0.45)',
      },
      backgroundImage: {
        'grid-faint':
          'linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px)',
      },
      backgroundSize: {
        grid: '48px 48px',
      },
    },
  },
  plugins: [],
};

export default config;
