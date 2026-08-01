'use client';

import { useRef, MouseEvent } from 'react';
import { motion } from 'framer-motion';
import { Search, FileText, Users2, ScrollText } from 'lucide-react';

const CARDS = [
  {
    icon: Search,
    title: 'Semantic Case Search',
    detail:
      'Ask in plain language — "cases where anticipatory bail was denied under Section 438" — and retrieve ranked judgments by meaning, not just keyword.',
    span: 'md:col-span-3 md:row-span-2',
    accent: 'amber',
  },
  {
    icon: FileText,
    title: 'Judgment Summarizer',
    detail: 'Multi-page orders condensed into facts, issues, holding, and ratio — each line traceable to its paragraph.',
    span: 'md:col-span-3',
    accent: 'indigo',
  },
  {
    icon: Users2,
    title: 'Legal Entity Extraction',
    detail: 'Judges, counsel, acts, sections, and dates auto-tagged across every document you upload.',
    span: 'md:col-span-3',
    accent: 'cobalt',
  },
  {
    icon: ScrollText,
    title: 'BNS ⇄ IPC Code Mapping',
    detail: 'Cross-reference old Penal Code sections against the Bharatiya Nyaya Sanhita instantly, with mapping confidence shown inline.',
    span: 'md:col-span-3',
    accent: 'amber',
  },
];

function BentoCard({ card }: { card: (typeof CARDS)[number] }) {
  const ref = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const rotateX = ((y - rect.height / 2) / rect.height) * -6;
    const rotateY = ((x - rect.width / 2) / rect.width) * 6;
    el.style.transform = `perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(0)`;
    el.style.setProperty('--mx', `${x}px`);
    el.style.setProperty('--my', `${y}px`);
  };

  const handleMouseLeave = () => {
    const el = ref.current;
    if (!el) return;
    el.style.transform = 'perspective(800px) rotateX(0deg) rotateY(0deg)';
  };

  const glow =
    card.accent === 'amber'
      ? 'rgba(245,158,11,0.14)'
      : card.accent === 'indigo'
      ? 'rgba(55,48,163,0.18)'
      : 'rgba(30,58,138,0.2)';

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`glass-panel group relative overflow-hidden rounded-3xl p-8 transition-[transform,border-color] duration-300 ease-out hover:border-white/20 ${card.span}`}
      style={{ transformStyle: 'preserve-3d', willChange: 'transform' }}
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: 0.5 }}
    >
      <div
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background: `radial-gradient(220px circle at var(--mx) var(--my), ${glow}, transparent 70%)`,
        }}
      />
      <card.icon className="mb-6 h-7 w-7 text-amber" strokeWidth={1.6} />
      <h3 className="font-display text-2xl font-semibold text-cream">{card.title}</h3>
      <p className="mt-3 max-w-md text-sm leading-relaxed text-ash">{card.detail}</p>
    </motion.div>
  );
}

export default function CapabilitiesBento() {
  return (
    <section id="capabilities" className="relative py-32 md:py-40">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-16 max-w-2xl">
          <span className="mb-4 inline-block font-sans text-xs font-semibold uppercase tracking-[0.25em] text-amber">
            System Capabilities
          </span>
          <h2 className="font-display text-4xl font-semibold leading-tight text-cream md:text-5xl">
            Built for how legal research actually happens.
          </h2>
        </div>
        <div className="grid grid-cols-1 gap-5 md:grid-cols-6">
          {CARDS.map((card) => (
            <BentoCard key={card.title} card={card} />
          ))}
        </div>
      </div>
    </section>
  );
}
