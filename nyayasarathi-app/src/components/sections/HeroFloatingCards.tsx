'use client';

import { useRef } from 'react';
import { motion, useScroll, useTransform, type MotionValue } from 'framer-motion';
import { FileText, ShieldAlert, CheckCircle, Scale, Database, Search } from 'lucide-react';

interface FloatingCard {
  title: string;
  subtitle: string;
  content: string;
  icon: typeof FileText;
  meta: string;
  status: string;
  statusClass: string;
  iconClass: string;
  initialRotate: number;
}

const floatingCardsData: FloatingCard[] = [
  {
    title: 'Exhibit A-12',
    subtitle: 'Forensic PDF Scan',
    content: 'CRIMINAL BRIEF: Discrepancies noted in digital signature timestamps on page 42.',
    icon: FileText,
    iconClass: 'text-[#B59A68]',
    meta: 'SECURED DEPOSIT',
    status: 'Ready to Map',
    statusClass: 'text-[#B59A68] bg-[#B59A68]/8 border-[#B59A68]/30',
    initialRotate: -8,
  },
  {
    title: 'Precedent Match',
    subtitle: 'State of MH v. K. Shah (2022)',
    content: 'CRIMINAL LAW: Precedent governs admissibility of electronic records without certificate.',
    icon: Scale,
    iconClass: 'text-[#71877A]',
    meta: 'BM25 INDEX',
    status: '98% Confident',
    statusClass: 'text-[#71877A] bg-[#71877A]/8 border-[#71877A]/30',
    initialRotate: 6,
  },
  {
    title: 'Verify Citation',
    subtitle: 'IPC Section 302',
    content: 'GROUND TRUTH: Verifying corpus mapping against Bharatiya Nyaya Sanhita equivalents.',
    icon: ShieldAlert,
    iconClass: 'text-[#8A3545]',
    meta: 'CROSS-VERIFICATION',
    status: 'Warning Checked',
    statusClass: 'text-[#8A3545] bg-[#6E2634]/10 border-[#6E2634]/30',
    initialRotate: -5,
  },
  {
    title: 'Chunk Extraction',
    subtitle: 'Paragraph 14 Analysis',
    content: 'RAG CONTEXT: Sentence boundaries extracted. NER matches Judge name "A.K. Sen".',
    icon: Database,
    iconClass: 'text-stone',
    meta: 'PARAGRAPH CLASSIFIER',
    status: 'Segmented',
    statusClass: 'text-[#A9A49A] bg-[#A9A49A]/8 border-[#A9A49A]/25',
    initialRotate: 7,
  },
  {
    title: 'Semantic Query',
    subtitle: 'Anticipatory Bail Scope',
    content: 'SEARCH: Filtered for offenses with jail terms below 7 years under Section 438.',
    icon: Search,
    iconClass: 'text-[#B59A68]',
    meta: 'VECTOR NEIGHBORS',
    status: 'Fitted',
    statusClass: 'text-[#B59A68] bg-[#B59A68]/8 border-[#B59A68]/30',
    initialRotate: -6,
  },
  {
    title: 'Verified Answer',
    subtitle: 'Final Decision Support',
    content: 'RAG GEN: Answer compiled from 4 cited paragraphs. 100% source-grounded.',
    icon: CheckCircle,
    iconClass: 'text-[#71877A]',
    meta: 'DECISION PIPELINE',
    status: 'Verified',
    statusClass: 'text-[#71877A] bg-[#71877A]/8 border-[#71877A]/30',
    initialRotate: 5,
  },
];

function FloatingCardItem({
  card,
  index,
  scrollYProgress,
}: {
  card: FloatingCard;
  index: number;
  scrollYProgress: MotionValue<number>;
}) {
  const duration = 0.12;
  const start = 0.05 + index * 0.08;
  const end = start + duration;

  const y       = useTransform(scrollYProgress, [start, end], [100, 0],  { clamp: true });
  const rotate  = useTransform(scrollYProgress, [start, end], [card.initialRotate, 0], { clamp: true });
  const opacity = useTransform(scrollYProgress, [start, start + duration * 0.4], [0, 1], { clamp: true });
  const scale   = useTransform(scrollYProgress, [start, end], [0.92, 1], { clamp: true });

  const Icon = card.icon;

  return (
    <motion.div style={{ y, rotate, opacity, scale }} className="relative">
      <motion.div
        whileHover={{ y: -8 }}
        className="flex flex-col justify-between h-full rounded border border-[#3B3A33] bg-[#1D211F] p-5 md:p-6 transition-[border-color,background-color] duration-300 hover:border-[#8A3545]/40 hover:bg-[#242925]"
      >
        <div>
          {/* Card header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-sm bg-[#151716]">
                <Icon className={`h-4 w-4 ${card.iconClass}`} strokeWidth={1.5} />
              </div>
              <div>
                <h4 className="font-display text-sm font-semibold text-ivory">{card.title}</h4>
                <span className="text-[10px] font-sans text-stone">{card.subtitle}</span>
              </div>
            </div>
            <span className="text-[9px] font-mono tracking-widest text-stone/60 bg-[#151716] border border-[#3B3A33] px-1.5 py-0.5 rounded-sm">
              {card.meta}
            </span>
          </div>

          {/* Card content — legal document style */}
          <p className="font-legal text-xs text-stone leading-relaxed mb-5 bg-[#151716]/60 p-3 rounded-sm border border-[#3B3A33]/50 italic">
            {card.content}
          </p>
        </div>

        {/* Card footer */}
        <div className="flex items-center justify-between pt-3 border-t border-[#3B3A33] text-[10px] mt-auto">
          <span className="font-mono text-stone/40 tracking-widest">INTELLIGENCE NODE</span>
          <span className={`px-2 py-0.5 rounded-sm border font-sans text-[9px] font-semibold tracking-wide ${card.statusClass}`}>
            {card.status}
          </span>
        </div>
      </motion.div>
    </motion.div>
  );
}

export default function HeroFloatingCards() {
  const containerRef = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end end'],
  });

  return (
    <section
      ref={containerRef}
      className="relative h-[220vh] bg-[#151716] text-ivory"
    >
      <div className="sticky top-0 h-screen w-full flex flex-col justify-center overflow-hidden px-6 md:px-12">
        {/* Very subtle top-lit ambient — no radial blobs */}
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-[#3B3A33]" />

        {/* Section header */}
        <div className="relative mx-auto max-w-5xl text-center mb-14 z-10">
          <div className="mb-5 flex justify-center">
            <span className="section-label">
              <Scale className="h-3 w-3 text-[#B59A68]" strokeWidth={1.5} />
              Interactive Knowledge Graph
            </span>
          </div>

          <h2 className="font-display text-4xl font-semibold leading-tight text-ivory md:text-5xl">
            Visualizing the Evidence Stack
          </h2>
          <p className="mx-auto mt-4 max-w-xl font-sans text-sm text-stone leading-relaxed">
            Scroll down to watch case files, index records, and semantic chunks lock
            into a verified, structured knowledge grid.
          </p>
        </div>

        {/* Cards */}
        <div className="relative mx-auto max-w-5xl w-full flex items-center justify-center px-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 w-full relative z-20">
            {floatingCardsData.map((card, index) => (
              <FloatingCardItem
                key={index}
                card={card}
                index={index}
                scrollYProgress={scrollYProgress}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
