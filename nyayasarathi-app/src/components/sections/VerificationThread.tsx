'use client';

import { useRef, useState, type MouseEvent } from 'react';
import { motion, type Variants } from 'framer-motion';
import {
  FileUp,
  ScanText,
  Scissors,
  Network,
  Sparkles,
  ShieldCheck,
  type LucideIcon,
} from 'lucide-react';

interface Stage {
  icon: LucideIcon;
  step: string;
  title: string;
  description: string;
  badge: string;
}

const stages: Stage[] = [
  {
    icon: FileUp,
    step: 'STAGE 01',
    title: 'Document Upload',
    description:
      'Judgments, orders, and case files ingested as PDF, DOCX, or scanned image — no reformatting required.',
    badge: 'MULTI-FORMAT INGEST',
  },
  {
    icon: ScanText,
    step: 'STAGE 02',
    title: 'OCR & Text Extraction',
    description:
      'Layout-aware OCR reconstructs paragraphs, tables, and cause-title structure from scanned court records.',
    badge: 'LAYOUT RECONSTRUCTION',
  },
  {
    icon: Scissors,
    step: 'STAGE 03',
    title: 'Text Chunking & NER',
    description:
      'Passages are split at legal boundaries and tagged for judges, sections, acts, and dates.',
    badge: 'PARAGRAPH TAGGING',
  },
  {
    icon: Network,
    step: 'STAGE 04',
    title: 'Hybrid Indexing',
    description:
      'Vector embeddings and lexical (BM25) indexes are built side by side for meaning and exact statute matches.',
    badge: 'VECTOR + BM25',
  },
  {
    icon: Sparkles,
    step: 'STAGE 05',
    title: 'RAG AI Generation',
    description:
      'Retrieved passages ground every generated answer — the model argues from your corpus, not memory.',
    badge: 'GROUNDED RESPONSE',
  },
  {
    icon: ShieldCheck,
    step: 'STAGE 06',
    title: 'Citation Verification',
    description:
      'Each claim is traced back to its source paragraph before it ever reaches the researcher.',
    badge: 'PARAGRAPH TRACE',
  },
];

/* ─── Framer Motion Variants for Staggered Entrance ─── */

const containerVariants: Variants = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.08,
    },
  },
};

const cardVariants: Variants = {
  hidden: { opacity: 0, y: 35, scale: 0.96 },
  show: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      duration: 0.7,
      ease: [0.16, 1, 0.3, 1],
    },
  },
};

/* ─── Stage Card with Spotlight Interaction ─────────── */

function SpotlightStageCard({ stage, index }: { stage: Stage; index: number }) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [coords, setCoords] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const { left, top } = cardRef.current.getBoundingClientRect();
    setCoords({
      x: e.clientX - left,
      y: e.clientY - top,
    });
  };

  const Icon = stage.icon;

  return (
    <motion.div
      ref={cardRef}
      variants={cardVariants}
      onMouseMove={handleMouseMove}
      whileHover={{ y: -6, transition: { duration: 0.2 } }}
      className="group relative rounded-2xl p-[1px] bg-slate-800 shadow-xl overflow-hidden"
    >
      {/* Outer Border Spotlight Glow */}
      <div
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background: `radial-gradient(150px circle at ${coords.x}px ${coords.y}px, rgba(245, 158, 11, 0.4), transparent)`,
        }}
      />

      {/* Inner Card Body */}
      <div className="relative flex flex-col justify-between h-full rounded-[15px] bg-[#131924]/95 p-6 min-h-[260px] overflow-hidden">
        {/* Dynamic Cursor Spotlight Inner Background Glow */}
        <div
          className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
          style={{
            background: `radial-gradient(350px circle at ${coords.x}px ${coords.y}px, rgba(245, 158, 11, 0.04), transparent 80%)`,
          }}
        />

        <div>
          {/* Card Header */}
          <div className="relative mb-5 flex items-center justify-between z-10">
            <span className="flex items-center gap-2 rounded-md border border-amber-400/20 bg-amber-400/10 px-2.5 py-1 text-xs font-bold tracking-wider text-amber-400/90">
              <Icon className="h-3.5 w-3.5" strokeWidth={2} />
              {stage.step}
            </span>
            <span className="rounded border border-slate-700/50 bg-slate-800/80 px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest text-slate-400">
              {stage.badge}
            </span>
          </div>

          {/* Card Title & Description */}
          <h3 className="relative mb-3 font-display text-xl font-semibold text-slate-100 transition-colors duration-300 group-hover:text-amber-400 z-10">
            {stage.title}
          </h3>
          <p className="relative mb-6 text-sm leading-relaxed text-slate-400 z-10">
            {stage.description}
          </p>
        </div>

        {/* Card Footer */}
        <div className="relative flex items-center justify-between border-t border-slate-800/80 pt-4 text-xs text-slate-500 z-10 mt-auto">
          <span>STAGE {String(index + 1).padStart(2, '0')} OF 06</span>
          <span className="h-1.5 w-1.5 rounded-full bg-slate-700 transition-colors duration-300 group-hover:bg-amber-400 group-hover:shadow-[0_0_8px_2px_rgba(245, 158, 11, 0.4)]" />
        </div>
      </div>
    </motion.div>
  );
}

/* ─── Main Component ───────────────────────────────────────── */

export default function VerificationThread() {
  return (
    <section
      id="pipeline"
      className="relative min-h-screen bg-[#0b0f17] px-6 py-24 text-white md:px-12"
    >
      {/* Subtle background glow */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_60%_40%_at_50%_20%,rgba(245,158,11,0.04),transparent_70%)]" />

      {/* Header Section */}
      <div className="relative mx-auto mb-20 max-w-4xl text-center z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true }}
          className="mb-4 inline-flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-amber-400"
        >
          <span className="h-2 w-2 animate-pulse rounded-full bg-amber-400" />
          The Pipeline Architecture
        </motion.div>

        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          viewport={{ once: true }}
          className="font-display text-4xl font-semibold tracking-tight text-amber-50 md:text-5xl"
        >
          The Verification Thread
        </motion.h2>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          viewport={{ once: true }}
          className="mx-auto mt-4 max-w-2xl text-lg leading-relaxed text-slate-400"
        >
          Every answer is tethered to its source, start to finish. Raw filings
          become verifiable legal intelligence through six stages. Scroll to
          watch the thread trace the same path your evidence takes.
        </motion.p>
      </div>

      {/* 6-Stage Cards Grid */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, margin: '-100px' }}
        className="relative mx-auto grid max-w-6xl grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 z-10"
      >
        {stages.map((stage, index) => (
          <SpotlightStageCard key={stage.step} stage={stage} index={index} />
        ))}
      </motion.div>
    </section>
  );
}
