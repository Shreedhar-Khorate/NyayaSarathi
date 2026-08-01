'use client';

import { useRef } from 'react';
import { motion, type Variants } from 'framer-motion';
import { ArrowUpRight, Upload, Scale } from 'lucide-react';
import dynamic from 'next/dynamic';

const AmbientCanvas = dynamic(() => import('@/components/ui/AmbientCanvas'), { ssr: false });
const BackgroundVideo = dynamic(() => import('@/components/ui/BackgroundVideo'), { ssr: false });

const container: Variants = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.09, delayChildren: 0.15 },
  },
};

const item: Variants = {
  hidden: { opacity: 0, y: 22 },
  show: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] } },
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
      {/* Scroll-parallax background video, smoothed with a spring so it glides rather than snaps */}
      <BackgroundVideo targetRef={sectionRef} />

      {/* Ambient radial glow + faint grid sit above the video for depth, below the citation mesh */}
      <div className="ambient-field opacity-70 mix-blend-screen" />
      <div className="absolute inset-0 bg-grid-faint bg-grid opacity-[0.1] [mask-image:radial-gradient(ellipse_65%_55%_at_50%_35%,black,transparent)]" />
      <div className="absolute inset-0 opacity-60">
        <AmbientCanvas />
      </div>

      <div className="relative z-10 mx-auto w-full max-w-6xl px-6">
        <motion.div variants={container} initial="hidden" animate="show" className="max-w-4xl">
          <motion.div
            variants={item}
            className="mb-7 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 backdrop-blur-sm"
          >
            <Scale className="h-3.5 w-3.5 text-amber" strokeWidth={2} />
            <span className="font-sans text-xs font-medium tracking-wide text-ash">
              NyayaSarathi &mdash; Your Guide Through the Court of Evidence
            </span>
          </motion.div>

          <h1 className="font-display flex flex-wrap gap-x-3 gap-y-1 text-5xl font-semibold leading-[1.08] text-cream sm:text-6xl md:text-7xl">
            {HEADLINE_WORDS.map((word, i) => (
              <motion.span
                key={i}
                variants={item}
                className={word === 'Judicial' || word === 'Intelligence' ? 'text-gradient-gold' : ''}
              >
                {word}
              </motion.span>
            ))}
          </h1>

          <motion.p
            variants={item}
            className="mt-7 max-w-xl text-lg leading-relaxed text-ash"
          >
            NyayaSarathi reads, indexes, and cross-verifies case law at the speed of a query &mdash;
            every generated answer traced back to the paragraph that supports it.
          </motion.p>

          <motion.div variants={item} className="mt-10 flex flex-col gap-4 sm:flex-row">
            <button className="shimmer-btn group flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-amber-deep to-amber px-7 py-4 font-sans text-sm font-semibold text-obsidian shadow-gold transition-transform duration-300 hover:-translate-y-0.5">
              Launch Research Hub
              <ArrowUpRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </button>
            <button className="group flex items-center justify-center gap-2 rounded-xl border border-white/15 bg-white/5 px-7 py-4 font-sans text-sm font-semibold text-cream backdrop-blur-sm transition-colors duration-300 hover:border-white/30 hover:bg-white/10">
              <Upload className="h-4 w-4 text-ash transition-colors group-hover:text-cream" />
              Upload Document
            </button>
          </motion.div>

          <motion.div variants={item} className="mt-16 flex flex-wrap items-center gap-x-10 gap-y-4">
            {[
              ['12,400+', 'Judgments indexed'],
              ['85%', 'Research time saved'],
              ['100%', 'Citation-verifiable'],
            ].map(([value, label]) => (
              <div key={label}>
                <p className="font-display text-2xl font-semibold text-cream">{value}</p>
                <p className="text-xs text-ash">{label}</p>
              </div>
            ))}
          </motion.div>
        </motion.div>
      </div>

      <div className="absolute bottom-0 left-0 h-40 w-full bg-gradient-to-t from-obsidian to-transparent" />
    </section>
  );
}
