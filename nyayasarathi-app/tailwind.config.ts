import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/app/**/*.{ts,tsx}', './src/components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // ── Neo-Classical Legal Palette ──────────────────────────────
        ink:       '#151716',   // Main background (replaces obsidian)
        charcoal:  '#1D211F',   // Secondary background
        olive:     '#242925',   // Cards & panel surfaces
        oxblood: {
          DEFAULT: '#6E2634',   // Primary accent (replaces amber)
          light:   '#8A3545',   // Hover states
        },
        verdigris: '#71877A',   // Verified / success states
        brass:     '#B59A68',   // Citations & decorative accents
        vellum: {
          DEFAULT: '#F2EBDD',   // Document viewer surface
          dark:    '#DED5C4',   // Borders & metadata on vellum
        },
        ivory:     '#F4EFE5',   // Primary text on dark
        stone:     '#A9A49A',   // Secondary text & descriptions
        border:    '#3B3A33',   // Dividers & card borders

        // Keep legacy names pointing to new values for any missed classnames
        obsidian:  '#151716',
        cream:     '#F4EFE5',
        ash:       '#A9A49A',
      },
      fontFamily: {
        display: ['var(--font-display)', 'Georgia', 'serif'],
        sans:    ['var(--font-body)', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        legal:   ['var(--font-legal)', 'Georgia', 'serif'],
      },
      boxShadow: {
        oxblood: '0 0 40px -8px rgba(110, 38, 52, 0.35)',
        brass:   '0 0 30px -10px rgba(181, 154, 104, 0.25)',
      },
      backgroundImage: {
        'grid-faint':
          'linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)',
      },
      backgroundSize: {
        grid: '48px 48px',
      },
    },
  },
  plugins: [],
};

export default config;
