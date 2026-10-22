'use client';

import dynamic from 'next/dynamic';
import Hero from '@/components/sections/Hero';
import { Navbar, Footer } from '@/components/layout/NavAndFooter';

const JudicialDiarySketchbook = dynamic(
  () => import('@/components/sections/JudicialDiarySketchbook'),
  {
    ssr: false,
    loading: () => (
      <section className="relative w-full min-h-[640px] bg-[#101211] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rounded-full border-2 border-[#B59A68] border-t-transparent animate-spin" />
          <span className="font-mono text-xs uppercase tracking-widest text-[#B59A68]/70">
            Loading Judicial Folio...
          </span>
        </div>
      </section>
    ),
  }
);

export default function Home() {
  return (
    <main className="relative min-h-screen bg-obsidian">
      <div className="grain-overlay" />
      <Navbar />
      <Hero />
      <JudicialDiarySketchbook />
      <Footer />
    </main>
  );
}
