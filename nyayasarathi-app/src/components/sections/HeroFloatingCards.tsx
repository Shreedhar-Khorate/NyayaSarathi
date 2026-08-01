'use client';

import { useRef } from 'react';
import { motion, useScroll, useTransform, type MotionValue } from 'framer-motion';
import { FileText, ShieldAlert, CheckCircle, Scale, Database, Search } from 'lucide-react';

interface FloatingCard {
  title: string;
  subtitle: string;
  content: string;
  icon: typeof FileText;
  iconColor: string;
  meta: string;
  status: string;
  statusColor: string;
  initialRotate: number;
}

const floatingCardsData: FloatingCard[] = [
  {
    title: 'Exhibit A-12',
    subtitle: 'Forensic PDF Scan',
    content: 'CRIMINAL BRIEF: Discrepancies noted in digital signature timestamps on page 42.',
    icon: FileText,
    iconColor: 'text-amber',
    meta: 'SECURED DEPOSIT',
    status: 'Ready to Map',
    statusColor: 'text-amber bg-amber/10 border-amber/20',
    initialRotate: -8,
  },
  {
    title: 'Precedent Match',
    subtitle: 'State of MH v. K. Shah (2022)',
    content: 'CRIMINAL LAW: Precedent governs admissibility of electronic records without certificate.',
    icon: Scale,
    iconColor: 'text-emerald-400',
    meta: 'BM25 INDEX',
    status: '98% Confident',
    statusColor: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
    initialRotate: 6,
  },
  {
    title: 'Verify Citation',
    subtitle: 'IPC Section 302',
    content: 'GROUND TRUTH: Verifying corpus mapping against Bharatiya Nyaya Sanhita equivalents.',
    icon: ShieldAlert,
    iconColor: 'text-rose-400',
    meta: 'CROSS-VERIFICATION',
    status: 'Warning Checked',
    statusColor: 'text-rose-400 bg-rose-400/10 border-rose-400/20',
    initialRotate: -5,
  },
  {
    title: 'Chunk Extraction',
    subtitle: 'Paragraph 14 Analysis',
    content: 'RAG CONTEXT: Sentence boundaries extracted. NER matches Judge name "A.K. Sen".',
    icon: Database,
    iconColor: 'text-indigo-400',
    meta: 'PARAGRAPH CLASSIFIER',
    status: 'Segmented',
    statusColor: 'text-indigo-400 bg-indigo-400/10 border-indigo-400/20',
    initialRotate: 7,
  },
  {
    title: 'Semantic Query',
    subtitle: 'Anticipatory Bail Scope',
    content: 'SEARCH: Filtered for offenses with jail terms below 7 years under Section 438.',
    icon: Search,
    iconColor: 'text-sky-400',
    meta: 'VECTOR NEIGHBORS',
    status: 'Fitted',
    statusColor: 'text-sky-400 bg-sky-400/10 border-sky-400/20',
    initialRotate: -6,
  },
  {
    title: 'Verified Answer',
    subtitle: 'Final Decision Support',
    content: 'RAG GEN: Answer compiled from 4 cited paragraphs. 100% source-grounded.',
    icon: CheckCircle,
    iconColor: 'text-teal-400',
    meta: 'DECISION PIPELINE',
    status: 'Verified',
    statusColor: 'text-teal-400 bg-teal-400/10 border-teal-400/20',
    initialRotate: 5,
  },
];

/* ─── Floating Card Item (Complies with Rules of Hooks) ─── */

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

  // Move only vertically and rotate to prevent horizontal card overlap/clashing
  const y = useTransform(scrollYProgress, [start, end], [100, 0], { clamp: true });
  const rotate = useTransform(scrollYProgress, [start, end], [card.initialRotate, 0], { clamp: true });
  const opacity = useTransform(scrollYProgress, [start, start + duration * 0.4], [0, 1], { clamp: true });
  const scale = useTransform(scrollYProgress, [start, end], [0.9, 1], { clamp: true });

  const Icon = card.icon;

  return (
    <motion.div style={{ y, rotate, opacity, scale }} className="relative">
      <motion.div
        whileHover={{
          y: -10,
        }}
        className="glass-panel-raised flex flex-col justify-between rounded-2xl border border-white/5 bg-[#161d2b]/70 p-5 md:p-6 backdrop-blur-md transition-[border-color,background-color,box-shadow] duration-300 hover:border-amber-500/40 hover:bg-[#161d2b]/95 hover:shadow-[0_20px_40px_-15px_rgba(245,158,11,0.2)] h-full"
      >
        <div>
          {/* Card Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-white/5">
                <Icon className={`h-5 w-5 ${card.iconColor}`} />
              </div>
              <div>
                <h4 className="font-semibold text-sm text-cream">{card.title}</h4>
                <span className="text-[10px] text-ash font-sans">{card.subtitle}</span>
              </div>
            </div>
            <span className="text-[9px] font-mono tracking-widest text-ash/80 bg-white/5 px-2 py-0.5 rounded">
              {card.meta}
            </span>
          </div>

          {/* Card Content */}
          <p className="text-xs text-ash leading-relaxed mb-6 font-mono bg-black/25 p-3 rounded-lg border border-white/5">
            {card.content}
          </p>
        </div>

        {/* Card Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-white/5 text-[11px] mt-auto">
          <span className="text-ash/60">INTELLIGENCE NODE</span>
          <span className={`px-2.5 py-0.5 rounded-full border text-[10px] font-medium ${card.statusColor}`}>
            {card.status}
          </span>
        </div>
      </motion.div>
    </motion.div>
  );
}

/* ─── Main Component ───────────────────────────────────────── */

export default function HeroFloatingCards() {
  const containerRef = useRef<HTMLDivElement>(null);

  // Track scroll progress across the parent's scrollable height
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end end'],
  });

  return (
    <section
      ref={containerRef}
      className="relative h-[220vh] bg-[#0b0f17] text-cream"
    >
      {/* Sticky container that keeps elements in screen for the duration of the scroll */}
      <div className="sticky top-0 h-screen w-full flex flex-col justify-center overflow-hidden px-6 md:px-12">
        {/* Background radial highlight */}
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_45%,rgba(30,58,138,0.12),transparent_70%)]" />

        {/* Grid overlay */}
        <div className="absolute inset-0 bg-grid-faint bg-grid opacity-[0.06] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,black,transparent)]" />

        <div className="relative mx-auto max-w-5xl text-center mb-16 z-10">
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="mb-4 inline-flex items-center gap-2 rounded-full border border-amber-500/20 bg-amber-500/5 px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-amber-400"
          >
            <Scale className="h-3.5 w-3.5" />
            Interactive Knowledge Graph
          </motion.div>

          <h2 className="font-display text-4xl font-semibold leading-tight text-cream md:text-5xl">
            Visualizing the Evidence Stack
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-ash text-sm md:text-base leading-relaxed">
            Scroll down to watch case files, index records, and semantic chunks lock into a verified, structured knowledge grid.
          </p>
        </div>

        {/* Cards container */}
        <div className="relative mx-auto max-w-5xl w-full flex items-center justify-center px-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full relative z-20">
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
