'use client';

import { useRef, useState, type MouseEvent } from 'react';
import {
  motion,
  useInView,
  useScroll,
  useSpring,
  useTransform,
  useMotionValue,
  useReducedMotion,
  type Variants,
} from 'framer-motion';
import {
  FileUp,
  ScanText,
  Scissors,
  Network,
  BookOpen,
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
    icon: BookOpen,
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

/* ── Card reveal variants ───────────────────────────────────── */
const leftVariant: Variants = {
  hidden: { opacity: 0, x: -32, filter: 'blur(5px)' },
  visible: {
    opacity: 1,
    x: 0,
    filter: 'blur(0px)',
    transition: { duration: 0.65, ease: [0.16, 1, 0.3, 1] },
  },
};

const rightVariant: Variants = {
  hidden: { opacity: 0, x: 32, filter: 'blur(5px)' },
  visible: {
    opacity: 1,
    x: 0,
    filter: 'blur(0px)',
    transition: { duration: 0.65, ease: [0.16, 1, 0.3, 1] },
  },
};

/* ══════════════════════════════════════════════════════════════
   STAGE CARD
   ══════════════════════════════════════════════════════════════ */
function StageCard({
  stage,
  index,
  isLeft,
  isReduced,
}: {
  stage: Stage;
  index: number;
  isLeft: boolean;
  isReduced: boolean;
}) {
  const cardRef = useRef<HTMLDivElement>(null);
  const dividerRef = useRef<HTMLDivElement>(null);

  const cardInView = useInView(cardRef, { once: true, amount: 0.3 });
  const dividerInView = useInView(dividerRef, { once: true, margin: '-30px' });

  const [hovered, setHovered] = useState(false);

  /* Cursor spotlight */
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const springX = useSpring(mouseX, { stiffness: 130, damping: 22, mass: 0.4 });
  const springY = useSpring(mouseY, { stiffness: 130, damping: 22, mass: 0.4 });

  const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const { left, top } = cardRef.current.getBoundingClientRect();
    mouseX.set(e.clientX - left);
    mouseY.set(e.clientY - top);
  };

  const spotlightBg = useTransform(
    [springX, springY],
    ([x, y]) =>
      `radial-gradient(280px circle at ${x}px ${y}px, rgba(110,38,52,0.10), transparent 70%)`
  );

  const Icon = stage.icon;

  return (
    <motion.div
      variants={isReduced ? undefined : (isLeft ? leftVariant : rightVariant)}
      initial={isReduced ? {} : 'hidden'}
      whileInView={isReduced ? undefined : 'visible'}
      viewport={{ once: true, amount: 0.25 }}
      transition={isReduced ? {} : { delay: index * 0.08 }}
      className="relative"
    >
      {/* Ambient glow behind card */}
      <motion.div
        className="absolute -inset-3 rounded-xl pointer-events-none"
        animate={{ opacity: hovered && !isReduced ? 1 : 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        style={{
          background: isLeft
            ? 'radial-gradient(ellipse 60% 50% at 80% 15%, rgba(110,38,52,0.18) 0%, transparent 70%)'
            : 'radial-gradient(ellipse 60% 50% at 20% 15%, rgba(110,38,52,0.18) 0%, transparent 70%)',
        }}
      />

      {/* Card shell */}
      <motion.div
        ref={cardRef}
        onMouseMove={handleMouseMove}
        onMouseEnter={(e) => { handleMouseMove(e); setHovered(true); }}
        onMouseLeave={() => setHovered(false)}
        className="stage-card relative overflow-hidden border border-[#3B3A33] bg-[#151716] rounded transition-[border-color] duration-500"
        whileHover={
          isReduced
            ? {}
            : {
              y: -5,
              scale: 1.01,
              transition: { type: 'spring', stiffness: 220, damping: 24, mass: 0.6 },
            }
        }
      >
        {/* Border beam — activates when in view */}
        {!isReduced && (
          <div
            className="border-beam-track"
            style={{ opacity: cardInView ? 1 : 0, transition: 'opacity 0.6s ease' }}
            aria-hidden="true"
          />
        )}

        {/* Cursor spotlight */}
        {!isReduced && (
          <motion.div
            className="pointer-events-none absolute inset-0 rounded"
            style={{
              background: spotlightBg,
              opacity: hovered ? 1 : 0,
              transition: 'opacity 0.4s ease',
            }}
            aria-hidden="true"
          />
        )}

        {/* Card content */}
        <div className="relative flex flex-col justify-between min-h-[240px] p-6 z-10">
          {/* Badge row */}
          <div className="flex items-center justify-between mb-5">
            <motion.span
              className="inline-flex items-center gap-2 font-mono text-[10px] tracking-widest border px-2.5 py-1 rounded-sm"
              animate={{
                borderColor: hovered && !isReduced ? 'rgba(138,53,69,0.55)' : 'rgba(110,38,52,0.30)',
                backgroundColor: hovered && !isReduced ? 'rgba(110,38,52,0.16)' : 'rgba(110,38,52,0.08)',
                color: hovered && !isReduced ? '#A0475A' : '#8A3545',
              }}
              transition={{ duration: 0.3 }}
            >
              <Icon className="h-3 w-3" strokeWidth={2} />
              {stage.step}
            </motion.span>
            <motion.span
              className="font-mono text-[9px] tracking-widest border border-[#3B3A33] bg-[#1D211F] px-2 py-0.5 rounded-sm"
              animate={{ color: hovered && !isReduced ? '#A9A49A' : 'rgba(169,164,154,0.50)' }}
              transition={{ duration: 0.3 }}
            >
              {stage.badge}
            </motion.span>
          </div>

          {/* Title & description */}
          <div className="flex-1">
            <motion.h3
              className="font-display text-xl font-semibold mb-2"
              animate={{ color: hovered && !isReduced ? '#B59A68' : '#F4EFE5' }}
              transition={{ duration: 0.35 }}
            >
              {stage.title}
            </motion.h3>
            <p className="font-sans text-sm leading-relaxed text-stone">{stage.description}</p>
          </div>

          {/* Divider draw */}
          <div ref={dividerRef} className="mt-5 relative">
            <div className="h-px w-full bg-[#2A2924]" />
            <motion.div
              className="absolute top-0 left-0 h-px bg-[#3B3A33]"
              initial={{ width: '0%' }}
              animate={dividerInView ? { width: '100%' } : { width: '0%' }}
              transition={
                isReduced
                  ? { duration: 0 }
                  : { duration: 0.8, delay: index * 0.06, ease: [0.22, 1, 0.36, 1] }
              }
              aria-hidden="true"
            />
            <div className="flex items-center justify-between pt-3 text-[10px]">
              <span className="font-mono text-stone/40 tracking-widest">
                STAGE {String(index + 1).padStart(2, '0')} {stage.step.split(' ')[0]}
              </span>
              <motion.span
                className="h-1.5 w-1.5 rounded-full"
                animate={{ backgroundColor: hovered && !isReduced ? '#71877A' : '#3B3A33' }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}

/* ══════════════════════════════════════════════════════════════
   MAIN SECTION
   ══════════════════════════════════════════════════════════════ */
import { useLanguage } from '@/context/LanguageContext';

export default function VerificationThread() {
  const isReduced = useReducedMotion() ?? false;
  const sectionRef = useRef<HTMLElement>(null);
  const { t } = useLanguage();

  const dynamicStages: Stage[] = [
    {
      icon: FileUp,
      step: 'STAGE 01',
      title: t('pipeline.stage1Title'),
      description: t('pipeline.stage1Desc'),
      badge: t('pipeline.stage1Badge'),
    },
    {
      icon: ScanText,
      step: 'STAGE 02',
      title: t('pipeline.stage2Title'),
      description: t('pipeline.stage2Desc'),
      badge: t('pipeline.stage2Badge'),
    },
    {
      icon: Scissors,
      step: 'STAGE 03',
      title: t('pipeline.stage3Title'),
      description: t('pipeline.stage3Desc'),
      badge: t('pipeline.stage3Badge'),
    },
    {
      icon: Network,
      step: 'STAGE 04',
      title: t('pipeline.stage4Title'),
      description: t('pipeline.stage4Desc'),
      badge: t('pipeline.stage4Badge'),
    },
    {
      icon: BookOpen,
      step: 'STAGE 05',
      title: t('pipeline.stage5Title'),
      description: t('pipeline.stage5Desc'),
      badge: t('pipeline.stage5Badge'),
    },
    {
      icon: ShieldCheck,
      step: 'STAGE 06',
      title: t('pipeline.stage6Title'),
      description: t('pipeline.stage6Desc'),
      badge: t('pipeline.stage6Badge'),
    },
  ];

  /* Scroll progress for ambient glow + center line */
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ['start 80%', 'end 20%'],
  });

  const smoothProgress = useSpring(scrollYProgress, { stiffness: 60, damping: 20, mass: 0.5 });

  /* Section glow: 6% → 14% */
  const glowOpacity = useTransform(smoothProgress, [0, 1], [0.06, 0.14]);

  /* Center line: 0% → 100% */
  const lineHeight = useTransform(smoothProgress, [0, 1], ['0%', '100%']);

  return (
    <section
      id="pipeline"
      ref={sectionRef}
      className="relative bg-[#1D211F] px-6 py-24 text-ivory md:px-12 overflow-hidden"
    >
      {/* Section hairlines */}
      <div className="absolute inset-x-0 top-0 h-px bg-[#3B3A33]" />
      <div className="absolute inset-x-0 bottom-0 h-px bg-[#3B3A33]" />

      {/* Section ambient glow (scroll-driven) */}
      {!isReduced && (
        <motion.div
          className="pointer-events-none absolute inset-0"
          style={{
            opacity: glowOpacity,
            background: 'radial-gradient(ellipse 70% 55% at 50% 50%, rgba(110,38,52,1) 0%, transparent 70%)',
          }}
          aria-hidden="true"
        />
      )}

      <div className="relative mx-auto max-w-6xl">
        {/* Section header */}
        <div className="mb-20 text-center">
          <div className="mb-5 flex justify-center">
            <span className="section-label">{t('pipeline.label')}</span>
          </div>
          <motion.h2
            initial={isReduced ? {} : { opacity: 0, y: 18 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
            viewport={{ once: true }}
            className="font-display text-4xl font-semibold tracking-tight text-ivory md:text-5xl"
          >
            {t('pipeline.title')}
          </motion.h2>
          <motion.p
            initial={isReduced ? {} : { opacity: 0, y: 18 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.65, delay: 0.12, ease: [0.22, 1, 0.36, 1] }}
            viewport={{ once: true }}
            className="mt-5 mx-auto max-w-2xl font-sans text-base leading-relaxed text-stone"
          >
            {t('pipeline.desc')}
          </motion.p>
        </div>

        {/* ── Alternating Timeline Layout ──────────────────────────
            Desktop: card-LEFT | center-line | card-RIGHT alternating
            Mobile: single column with line on left
        ────────────────────────────────────────────────────────── */}
        <div className="relative">

          {/* ── CENTER vertical timeline line (desktop) ─────────── */}
          <div className="hidden md:block absolute left-1/2 top-0 bottom-0 w-px -translate-x-1/2 bg-[#2A2924]">
            {!isReduced && (
              <motion.div
                className="absolute top-0 left-0 w-full"
                style={{
                  height: lineHeight,
                  background: 'linear-gradient(to bottom, rgba(110,38,52,0.5), rgba(138,53,69,0.3))',
                  boxShadow: '0 0 8px 1px rgba(110,38,52,0.20)',
                }}
                aria-hidden="true"
              />
            )}
          </div>

          {/* ── LEFT vertical timeline line (mobile) ──────────────── */}
          <div className="md:hidden absolute left-4 top-0 bottom-0 w-px bg-[#2A2924]">
            {!isReduced && (
              <motion.div
                className="absolute top-0 left-0 w-full"
                style={{
                  height: lineHeight,
                  background: 'linear-gradient(to bottom, rgba(110,38,52,0.5), rgba(138,53,69,0.3))',
                }}
                aria-hidden="true"
              />
            )}
          </div>

          {/* ── Stage rows ─────────────────────────────────────────── */}
          <div className="flex flex-col gap-10">
            {dynamicStages.map((stage, index) => {
              const isLeft = index % 2 === 0; // even → left, odd → right

              return (
                <div key={stage.step} className="relative flex items-center gap-0 md:gap-0">

                  {/* ── LEFT CARD or empty ─────────────────────────── */}
                  <div className="hidden md:flex flex-1 justify-end pr-10">
                    {isLeft ? (
                      <div className="w-full max-w-[440px]">
                        <StageCard
                          stage={stage}
                          index={index}
                          isLeft={true}
                          isReduced={isReduced}
                        />
                      </div>
                    ) : (
                      <div className="w-full max-w-[440px]" />
                    )}
                  </div>

                  {/* ── CENTER NODE ────────────────────────────────── */}
                  <div className="hidden md:flex flex-col items-center z-10 shrink-0">
                    <motion.div
                      initial={isReduced ? {} : { scale: 0, opacity: 0 }}
                      whileInView={isReduced ? {} : { scale: 1, opacity: 1 }}
                      viewport={{ once: true, amount: 0.5 }}
                      transition={{ duration: 0.4, delay: index * 0.08, ease: [0.22, 1, 0.36, 1] }}
                      className="relative flex h-8 w-8 items-center justify-center"
                    >
                      {/* Outer ring */}
                      <div className="absolute inset-0 rounded-full border border-[#6E2634]/40 bg-[#1D211F]" />
                      {/* Inner dot */}
                      <div className="h-2 w-2 rounded-full bg-[#6E2634]/70" />
                      {/* Pulse ring — very subtle */}
                      {!isReduced && (
                        <motion.div
                          className="absolute inset-0 rounded-full border border-[#6E2634]/20"
                          animate={{ scale: [1, 1.6, 1], opacity: [0.4, 0, 0.4] }}
                          transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut', delay: index * 0.4 }}
                          aria-hidden="true"
                        />
                      )}
                    </motion.div>
                  </div>

                  {/* ── RIGHT CARD or empty ────────────────────────── */}
                  <div className="hidden md:flex flex-1 pl-10">
                    {!isLeft ? (
                      <div className="w-full max-w-[440px]">
                        <StageCard
                          stage={stage}
                          index={index}
                          isLeft={false}
                          isReduced={isReduced}
                        />
                      </div>
                    ) : (
                      <div className="w-full max-w-[440px]" />
                    )}
                  </div>

                  {/* ── MOBILE: single column with left dot ─────────── */}
                  <div className="flex md:hidden w-full items-start gap-5 pl-10">
                    <div className="absolute left-2 flex flex-col items-center">
                      <div className="relative flex h-5 w-5 items-center justify-center">
                        <div className="absolute inset-0 rounded-full border border-[#6E2634]/40 bg-[#1D211F]" />
                        <div className="h-1.5 w-1.5 rounded-full bg-[#6E2634]/60" />
                      </div>
                    </div>
                    <div className="flex-1">
                      <StageCard
                        stage={stage}
                        index={index}
                        isLeft={true}
                        isReduced={isReduced}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
