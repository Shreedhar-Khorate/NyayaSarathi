import type { Metadata } from 'next';
import { Cormorant_Garamond, Manrope, Source_Serif_4, Noto_Sans_Devanagari } from 'next/font/google';
import './globals.css';

// ── Cormorant Garamond — display / editorial headings ─────────────────────
const cormorant = Cormorant_Garamond({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  style: ['normal', 'italic'],
  variable: '--font-display',
  display: 'swap',
});

// ── Manrope — UI, navigation, labels, body copy ───────────────────────────
const manrope = Manrope({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  variable: '--font-body',
  display: 'swap',
});

// ── Source Serif 4 — legal documents, quotations, excerpts ────────────────
const sourceSerif = Source_Serif_4({
  subsets: ['latin'],
  weight: ['400', '600'],
  style: ['normal', 'italic'],
  variable: '--font-legal',
  display: 'swap',
});

// ── Noto Sans Devanagari — Hindi & Marathi script ─────────────────────────
const notoDevanagari = Noto_Sans_Devanagari({
  subsets: ['devanagari'],
  weight: ['300', '400', '500', '600', '700'],
  variable: '--font-devanagari',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'NyayaSarathi — AI-Powered Judicial Case Intelligence',
  description:
    'NyayaSarathi is an AI-powered judicial case intelligence and decision support system — hybrid RAG search, judgment summarization, and verifiable legal citations.',
  icons: {
    icon: [
      { url: '/favicon.ico', sizes: 'any' },
      { url: '/icon.png', type: 'image/png', sizes: '512x512' },
    ],
    shortcut: '/favicon.ico',
    apple: '/apple-icon.png',
  },
};

import SmoothScroll from '@/components/layout/SmoothScroll';
import AppLoaderWrapper from '@/components/layout/AppLoaderWrapper';
import { LanguageProvider } from '@/context/LanguageContext';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      data-scroll-behavior="smooth"
      className={`${cormorant.variable} ${manrope.variable} ${sourceSerif.variable} ${notoDevanagari.variable}`}
    >
      <body className="bg-ink text-ivory antialiased" suppressHydrationWarning>
        <LanguageProvider>
          <AppLoaderWrapper>
            <SmoothScroll>{children}</SmoothScroll>
          </AppLoaderWrapper>
        </LanguageProvider>
      </body>
    </html>
  );
}
