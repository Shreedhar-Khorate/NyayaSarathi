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
    iconColor: 'text-[#B59A68]',
  },
  {
    icon: FileText,
    title: 'Judgment Summarizer',
    detail: 'Multi-page orders condensed into facts, issues, holding, and ratio — each line traceable to its paragraph.',
    span: 'md:col-span-3',
    iconColor: 'text-[#71877A]',
  },
  {
    icon: Users2,
    title: 'Legal Entity Extraction',
    detail: 'Judges, counsel, acts, sections, and dates auto-tagged across every document you upload.',
    span: 'md:col-span-3',
    iconColor: 'text-[#71877A]',
  },
  {
    icon: ScrollText,
    title: 'BNS ⇄ IPC Code Mapping',
    detail: 'Cross-reference old Penal Code sections against the Bharatiya Nyaya Sanhita instantly, with mapping confidence shown inline.',
    span: 'md:col-span-3',
    iconColor: 'text-[#B59A68]',
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
    const rotateX = ((y - rect.height / 2) / rect.height) * -5;
    const rotateY = ((x - rect.width / 2) / rect.width) * 5;
    el.style.transform = `perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
    el.style.setProperty('--mx', `${x}px`);
    el.style.setProperty('--my', `${y}px`);
  };

  const handleMouseLeave = () => {
    const el = ref.current;
    if (!el) return;
    el.style.transform = 'perspective(800px) rotateX(0deg) rotateY(0deg)';
  };

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`group relative overflow-hidden rounded border border-[#3B3A33] bg-[#242925] p-8 transition-[transform,border-color] duration-300 ease-out hover:border-[#B59A68]/30 ${card.span}`}
      style={{ transformStyle: 'preserve-3d', willChange: 'transform' }}
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: 0.5 }}
    >
      {/* Very subtle brass radial on hover — not a glow, just a warmth */}
      <div
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-400 group-hover:opacity-100"
        style={{
          background: `radial-gradient(260px circle at var(--mx) var(--my), rgba(181, 154, 104, 0.05), transparent 70%)`,
        }}
      />
      <card.icon className={`mb-7 h-6 w-6 ${card.iconColor}`} strokeWidth={1.4} />
      <h3 className="font-display text-2xl font-semibold text-ivory">{card.title}</h3>
      <p className="mt-3 max-w-md font-sans text-sm leading-relaxed text-stone">{card.detail}</p>
    </motion.div>
  );
}

import { useLanguage } from '@/context/LanguageContext';

export default function CapabilitiesBento() {
  const { t } = useLanguage();

  const dynamicCards = [
    {
      icon: Search,
      title: t('capabilities.card1Title'),
      detail: t('capabilities.card1Desc'),
      span: 'md:col-span-1',
      iconColor: 'text-[#B59A68]',
    },
    {
      icon: FileText,
      title: t('capabilities.card2Title'),
      detail: t('capabilities.card2Desc'),
      span: 'md:col-span-1',
      iconColor: 'text-[#71877A]',
    },
    {
      icon: Users2,
      title: t('capabilities.card3Title'),
      detail: t('capabilities.card3Desc'),
      span: 'md:col-span-1',
      iconColor: 'text-[#71877A]',
    },
    {
      icon: ScrollText,
      title: t('capabilities.card4Title'),
      detail: t('capabilities.card4Desc'),
      span: 'md:col-span-1',
      iconColor: 'text-[#B59A68]',
    },
  ];

  return (
    <section id="capabilities" className="relative py-28 md:py-36 bg-[#151716]">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-14 max-w-2xl">
          <div className="mb-4">
            <span className="section-label">{t('capabilities.label')}</span>
          </div>
          <h2 className="font-display text-3xl font-semibold leading-tight text-ivory sm:text-4xl md:text-5xl">
            {t('capabilities.title')}
          </h2>
        </div>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {dynamicCards.map((card) => (
            <BentoCard key={card.title} card={card} />
          ))}
        </div>
      </div>
    </section>
  );
}
