import type { Metadata } from 'next';
import { Playfair_Display, Plus_Jakarta_Sans } from 'next/font/google';
import './globals.css';

const playfair = Playfair_Display({
  subsets: ['latin'],
  weight: ['500', '600', '700'],
  style: ['normal', 'italic'],
  variable: '--font-playfair',
  display: 'swap',
});

const jakarta = Plus_Jakarta_Sans({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
  variable: '--font-jakarta',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'NyayaSarathi — AI-Powered Judicial Case Intelligence',
  description:
    'NyayaSarathi is an AI-powered judicial case intelligence and decision support system — hybrid RAG search, judgment summarization, and verifiable legal citations.',
};

import SmoothScroll from '@/components/layout/SmoothScroll';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`dark ${playfair.variable} ${jakarta.variable}`}>
      <body className="bg-obsidian text-cream antialiased">
        <SmoothScroll>{children}</SmoothScroll>
      </body>
    </html>
  );
}
