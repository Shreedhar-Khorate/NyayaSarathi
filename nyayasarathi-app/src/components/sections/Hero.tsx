'use client';

import { useRef } from 'react';
import { motion, type Variants } from 'framer-motion';
import { ArrowUpRight, Upload, Scale } from 'lucide-react';
import dynamic from 'next/dynamic';

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
  'Decision',
  'Support',
  'System',
];

export default function Hero() {
  const sectionRef = useRef<HTMLElement>(null);

  return (
    <section
      ref={sectionRef}
      className="relative flex min-h-screen items-center overflow-hidden pt-28"
    >
      {/* Ink-toned scroll-parallax background video */}
      <BackgroundVideo targetRef={sectionRef} />

      <div className="relative z-10 mx-auto w-full max-w-6xl px-6">
        <motion.div variants={container} initial="hidden" animate="show" className="max-w-4xl">

          {/* Editorial eyebrow label */}
          <motion.div variants={item} className="mb-8">
            <span className="section-label">
              <Scale className="h-3 w-3 text-[#B59A68]" strokeWidth={1.5} />
              Your Guide Through the Court of Evidence
            </span>
          </motion.div>

          {/* Headline — Cormorant Garamond */}
          <h1 className="font-display flex flex-wrap gap-x-3 gap-y-1 text-5xl font-semibold leading-[1.1] text-ivory sm:text-6xl md:text-7xl">
            {HEADLINE_WORDS.map((word, i) => (
              <motion.span
                key={i}
                variants={item}
                className={
                  word === 'Judicial' || word === 'Intelligence'
                    ? 'text-[#B59A68]'
                    : ''
                }
              >
                {word}
              </motion.span>
            ))}
          </h1>

          {/* Sub-copy */}
          <motion.p
            variants={item}
            className="mt-7 max-w-xl font-sans text-base leading-relaxed text-stone"
          >
            NyayaSarathi reads, indexes, and cross-verifies case law at the speed
            of a query &mdash; every generated answer traced back to the paragraph
            that supports it.
          </motion.p>

          {/* CTAs */}
          <motion.div variants={item} className="mt-10 flex flex-col gap-4 sm:flex-row">
            <button className="btn-oxblood group flex items-center justify-center gap-2 rounded px-7 py-3.5 font-sans text-sm font-semibold tracking-wide">
              Launch Research Hub
              <ArrowUpRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </button>
            <button className="group flex items-center justify-center gap-2 rounded border border-[#3B3A33] bg-transparent px-7 py-3.5 font-sans text-sm font-semibold text-ivory transition-colors duration-300 hover:border-[#8A3545]/50 hover:bg-[#6E2634]/8">
              <Upload className="h-4 w-4 text-stone transition-colors group-hover:text-ivory" />
              Upload Document
            </button>
          </motion.div>

          {/* Stats row */}
          <motion.div variants={item} className="mt-16 flex flex-wrap items-stretch gap-0">
            {[
              ['12,400+', 'Judgments indexed'],
              ['85%',     'Research time saved'],
              ['100%',    'Citation-verifiable'],
            ].map(([value, label], i) => (
              <div
                key={label}
                className={`pr-10 ${i > 0 ? 'pl-10 border-l border-[#3B3A33]' : ''}`}
              >
                <p className="font-display text-3xl font-semibold text-[#B59A68]">{value}</p>
                <p className="mt-1 font-sans text-xs tracking-wide text-stone">{label}</p>
              </div>
            ))}
          </motion.div>
        </motion.div>
      </div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 h-40 w-full bg-gradient-to-t from-[#151716] to-transparent" />
    </section>
  );
}
