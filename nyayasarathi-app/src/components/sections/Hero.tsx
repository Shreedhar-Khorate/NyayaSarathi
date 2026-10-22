'use client';

import { useRef } from 'react';
import { motion, type Variants } from 'framer-motion';
import { ArrowUpRight, Upload } from 'lucide-react';
import dynamic from 'next/dynamic';
import { useLanguage } from '@/context/LanguageContext';

import Link from 'next/link';

// AmbientCanvas removed per design spec (no animated blobs/particles)
const BackgroundVideo = dynamic(() => import('@/components/ui/BackgroundVideo'), { ssr: false });

const container: Variants = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.1, delayChildren: 0.2 },
  },
};

const item: Variants = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.22, 1, 0.36, 1] } },
};

const HEADLINE_WORDS = [
  'AI-Powered',
  'Judicial',
  'Case',
  'Intelligence',
  '&',
];

export default function Hero() {
  const sectionRef = useRef<HTMLElement>(null);
  const { t } = useLanguage();

  const headlineRaw = t('hero.headline');
  const headlineWords = Array.isArray(headlineRaw)
    ? headlineRaw
    : typeof headlineRaw === 'string'
    ? headlineRaw.split(' ')
    : HEADLINE_WORDS;

  return (
    <section
      ref={sectionRef}
      className="relative flex min-h-screen items-center overflow-hidden pt-28"
    >
      {/* Ink-toned scroll-parallax background video */}
      <BackgroundVideo targetRef={sectionRef} />

      <div className="relative z-10 mx-auto w-full max-w-6xl px-6">
        <motion.div variants={container} initial="hidden" animate="show" className="max-w-4xl">

          {/* Headline — Cormorant Garamond */}
          <h1 className="font-display flex flex-wrap gap-x-3 gap-y-1 text-5xl font-semibold leading-[1.1] text-ivory sm:text-6xl md:text-7xl">
            {headlineWords.map((word: string, i: number) => {
              const isHighlight =
                i === 1 ||
                i === 3 ||
                word === 'Judicial' ||
                word === 'Intelligence' ||
                word === 'न्यायालयीन' ||
                word === 'न्यायिक';
              return (
                <motion.span
                  key={i}
                  variants={item}
                  className={
                    isHighlight
                      ? 'bg-gradient-to-r from-[#F4EFE5] via-[#B59A68] to-[#997E4F] bg-clip-text text-transparent drop-shadow-[0_2px_14px_rgba(181,154,104,0.30)]'
                      : ''
                  }
                >
                  {word}
                </motion.span>
              );
            })}
          </h1>

          {/* Sub-copy */}
          <motion.p
            variants={item}
            className="mt-7 max-w-xl font-sans text-base leading-relaxed text-stone"
          >
            {t('hero.subtext')}
          </motion.p>

          {/* CTAs */}
          <motion.div variants={item} className="mt-10 flex flex-col gap-4 sm:flex-row">
            <Link
              href="/predictor"
              className="btn-oxblood group flex items-center justify-center gap-2 rounded px-7 py-3.5 font-sans text-sm font-semibold tracking-wide bg-gradient-to-r from-[#6E2634] via-[#7E2D3D] to-[#8A3545] border border-[#B59A68]/30 shadow-lg shadow-[#6E2634]/30"
            >
              <span>{t('hero.launchHub')}</span>
              <ArrowUpRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </Link>
            <Link
              href="/ocr"
              className="group flex items-center justify-center gap-2 rounded border border-[#3B3A33] bg-gradient-to-b from-[#1D211F]/90 to-[#151716]/90 px-7 py-3.5 font-sans text-sm font-semibold text-ivory transition-all duration-300 hover:border-[#B59A68]/50 hover:bg-gradient-to-b hover:from-[#242925] hover:to-[#181B1A]"
            >
              <Upload className="h-4 w-4 text-stone transition-colors group-hover:text-ivory" />
              <span>{t('hero.uploadDoc')}</span>
            </Link>
          </motion.div>
        </motion.div>
      </div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 h-40 w-full bg-gradient-to-t from-[#151716] to-transparent" />
    </section>
  );
}
