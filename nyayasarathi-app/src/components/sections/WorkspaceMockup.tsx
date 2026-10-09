'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, CheckCircle2, Search, ShieldCheck } from 'lucide-react';

import { useLanguage } from '@/context/LanguageContext';

const FILTER_TAGS = ['#BNS', '#IPC', '#SupremeCourt', '#Section420'];

const CITATIONS = [
  { id: 'c1', label: 'Para 14', page: 'Page 14' },
  { id: 'c2', label: 'Para 21', page: 'Page 21' },
];

export default function WorkspaceMockup() {
  const [activeCite, setActiveCite] = useState<string | null>(null);
  const [activeFilters, setActiveFilters] = useState<string[]>(['#Section420']);
  const { t } = useLanguage();

  // Build answer lines dynamically from translations
  const ANSWER_LINES = [
    { text: t('workspace.answerLine1'), citeId: null },
    { text: t('workspace.answerLine2'), citeId: 'c1' },
    { text: t('workspace.answerLine3'), citeId: null },
    { text: t('workspace.answerLine4'), citeId: 'c2' },
    { text: t('workspace.answerLine5'), citeId: null },
  ];

  const toggleFilter = (tag: string) => {
    setActiveFilters((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  return (
    <section id="workspace" className="relative py-32 md:py-40 bg-[#1D211F]">
      {/* Top hairline */}
      <div className="absolute inset-x-0 top-0 h-px bg-[#3B3A33]" />

      <div className="mx-auto max-w-7xl px-6">
        {/* Section header */}
        <div className="mb-14 max-w-2xl">
          <div className="mb-5">
            <span className="section-label">{t('workspace.label')}</span>
          </div>
          <h2 className="font-display text-4xl font-semibold leading-tight text-ivory md:text-5xl">
            {t('workspace.title')}
          </h2>
          <p className="mt-5 font-sans text-base leading-relaxed text-stone">
            {t('workspace.desc')}
          </p>
        </div>

        {/* ── Search Bar ─────────────────────────────────────────────────── */}
        <div className="mb-5 flex flex-col gap-4 rounded border border-[#3B3A33] bg-[#151716] p-4 sm:flex-row sm:items-center">
          <div className="flex flex-1 items-center gap-3 rounded-sm border border-[#3B3A33] bg-[#1D211F] px-4 py-3">
            <Search className="h-4 w-4 shrink-0 text-[#B59A68]" strokeWidth={1.5} />
            <input
              readOnly
              value={t('workspace.searchPlaceholder')}
              className="w-full bg-transparent font-sans text-sm text-ivory outline-none placeholder:text-stone"
            />
            <span className="shrink-0 font-mono text-[10px] tracking-widest text-[#B59A68] font-semibold whitespace-nowrap">
              {t('workspace.hybridSearch')}
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {FILTER_TAGS.map((tag) => {
              const active = activeFilters.includes(tag);
              return (
                <button
                  key={tag}
                  onClick={() => toggleFilter(tag)}
                  className={`rounded-sm border px-3 py-1.5 font-sans text-xs font-medium transition-colors duration-200 ${
                    active
                      ? 'border-[#B59A68]/50 bg-[#B59A68]/15 text-[#B59A68]'
                      : 'border-[#3B3A33] text-stone hover:border-[#3B3A33] hover:text-ivory'
                  }`}
                >
                  {tag}
                </button>
              );
            })}
          </div>
        </div>

        {/* ── Split View ─────────────────────────────────────────────────── */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 items-stretch">

          {/* ── LEFT: Legal Document (Warm Vellum) ──────────────────────── */}
          <div className="flex flex-col h-full rounded border border-[#DED5C4]/40 overflow-hidden bg-[#F2EBDD]">
            {/* Document header bar */}
            <div className="flex items-center justify-between border-b border-[#DED5C4]/50 px-5 py-4 bg-[#DED5C4] shrink-0">
              <div>
                <p className="font-display text-sm font-semibold text-[#151716]">
                  {t('workspace.docCaseName')}
                </p>
                <p className="font-sans text-xs text-[#5A554C] mt-0.5">
                  {t('workspace.docCourt')}
                </p>
              </div>
              <span className="verdigris-badge flex items-center gap-1.5 rounded-sm px-2.5 py-1 font-sans text-[10px] font-semibold tracking-wide">
                <ShieldCheck className="h-3 w-3" strokeWidth={2} />
                {t('workspace.docOcrBadge')}
              </span>
            </div>

            {/* Vellum document body */}
            <div className="doc-scroll flex-1 min-h-[460px] max-h-[560px] overflow-y-auto px-7 py-6">
              {/* Document label */}
              <div className="flex items-center justify-between mb-5 pb-3 border-b border-[#DED5C4]">
                <span className="font-mono text-[9px] tracking-[0.2em] text-[#A9A49A] uppercase">
                  {t('workspace.docLabel')}
                </span>
                <span className="font-mono text-[9px] tracking-[0.2em] text-[#A9A49A]">
                  {t('workspace.docPages')}
                </span>
              </div>

              <div className="font-legal text-sm leading-8 text-[#1D211F]">
                <p className="mb-5">
                  <span className="float-right ml-3 font-mono text-[10px] text-[#B59A68] tracking-wide">14.</span>
                  {t('workspace.docPara14')}
                </p>

                <motion.p
                  className="mb-5 rounded-sm px-3 py-2 -mx-3 transition-colors duration-500"
                  animate={{
                    backgroundColor: activeCite === 'c1' ? 'rgba(110, 38, 52, 0.12)' : 'rgba(110, 38, 52, 0)',
                  }}
                >
                  <span className="float-right ml-3 font-mono text-[10px] text-[#B59A68] tracking-wide">15.</span>
                  {t('workspace.docPara15')}
                </motion.p>

                <p className="mb-5">
                  <span className="float-right ml-3 font-mono text-[10px] text-[#B59A68] tracking-wide">18.</span>
                  {t('workspace.docPara18')}
                </p>

                <motion.p
                  className="mb-5 rounded-sm px-3 py-2 -mx-3 transition-colors duration-500"
                  animate={{
                    backgroundColor: activeCite === 'c2' ? 'rgba(110, 38, 52, 0.12)' : 'rgba(110, 38, 52, 0)',
                  }}
                >
                  <span className="float-right ml-3 font-mono text-[10px] text-[#B59A68] tracking-wide">21.</span>
                  {t('workspace.docPara21')}
                </motion.p>

                <p>
                  <span className="float-right ml-3 font-mono text-[10px] text-[#B59A68] tracking-wide">24.</span>
                  {t('workspace.docPara24')}
                </p>
              </div>

              {/* Document footer */}
              <div className="mt-8 pt-4 border-t border-[#DED5C4] flex items-center justify-between">
                <span className="font-mono text-[9px] tracking-[0.15em] text-[#A9A49A] uppercase">
                  {t('workspace.docSourceVerified')}
                </span>
                <span className="font-mono text-[9px] tracking-[0.15em] text-[#A9A49A]">
                  {t('workspace.docJudgmentNo')}
                </span>
              </div>
            </div>
          </div>

          {/* ── RIGHT: Research Note (AI Response) ─────────────────────── */}
          <div className="flex flex-col h-full rounded border border-[#3B3A33] bg-[#151716] overflow-hidden">
            {/* Note header */}
            <div className="flex items-center justify-between border-b border-[#3B3A33] px-5 py-4 shrink-0">
              <div className="flex items-center gap-2.5">
                <BookOpen className="h-4 w-4 text-[#B59A68]" strokeWidth={1.4} />
                <p className="font-sans text-xs font-semibold tracking-[0.2em] uppercase text-stone">
                  {t('workspace.researchNote')}
                </p>
              </div>
              <span className="verdigris-badge flex items-center gap-1.5 rounded-sm px-2.5 py-1 font-sans text-[10px] font-semibold">
                <CheckCircle2 className="h-3 w-3" strokeWidth={2} />
                {t('workspace.verifiedSources')}
              </span>
            </div>

            {/* Note body */}
            <div className="flex-1 px-6 py-6">
              {/* Answer text */}
              <div className="font-legal text-sm leading-8 text-ivory/90">
                {ANSWER_LINES.map((line, i) => {
                  if (!line.citeId) {
                    return <span key={i}>{line.text}</span>;
                  }
                  const citation = CITATIONS.find((c) => c.id === line.citeId)!;
                  return (
                    <span key={i}>
                      {line.text}
                      <button
                        onMouseEnter={() => setActiveCite(line.citeId)}
                        onMouseLeave={() => setActiveCite(null)}
                        onClick={() => setActiveCite(line.citeId)}
                        className="mx-1 inline-flex items-center rounded-sm border border-[#B59A68]/35 bg-[#B59A68]/10 px-1.5 py-0.5 align-middle font-sans text-[11px] font-semibold text-[#B59A68] transition-colors hover:bg-[#B59A68]/20"
                      >
                        {citation.label}
                      </button>
                    </span>
                  );
                })}
              </div>

              {/* Divider */}
              <div className="my-6 border-t border-[#3B3A33]" />

              {/* Basis of Answer */}
              <div className="mb-5">
                <p className="font-sans text-[10px] tracking-[0.2em] uppercase text-stone mb-3">
                  {t('workspace.basisTitle')}
                </p>
                <div className="flex flex-col gap-1.5">
                  <div className="flex items-center gap-2 font-sans text-xs text-stone">
                    <span className="h-1 w-1 rounded-full bg-[#71877A]" />
                    {t('workspace.passagesRetrieved')}
                  </div>
                  <div className="flex items-center gap-2 font-sans text-xs text-stone">
                    <span className="h-1 w-1 rounded-full bg-[#71877A]" />
                    {t('workspace.judgmentsReferenced')}
                  </div>
                  <div className="flex items-center gap-2 font-sans text-xs text-stone">
                    <span className="h-1 w-1 rounded-full bg-[#B59A68]" />
                    {t('workspace.docPageRefs')}
                  </div>
                </div>
              </div>

              {/* Source panel — shown on citation hover */}
              <AnimatePresence>
                {activeCite && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="border border-[#3B3A33] bg-[#1D211F] rounded-sm p-4">
                      <div className="border-b border-[#3B3A33] pb-3 mb-3">
                        <p className="font-sans text-[10px] tracking-[0.2em] uppercase text-stone mb-1">
                          {t('workspace.sourceLabel')}
                        </p>
                        <p className="font-display text-sm font-semibold text-[#B59A68]">
                          {t('workspace.docJudgmentNo')} · {CITATIONS.find((c) => c.id === activeCite)?.page}
                        </p>
                        <p className="font-sans text-xs text-stone mt-0.5">
                          {CITATIONS.find((c) => c.id === activeCite)?.label} — {t('workspace.sourceHighlighted')}
                        </p>
                      </div>
                      <button className="font-sans text-[11px] font-semibold text-[#B59A68] hover:text-[#D4AF37] tracking-wide transition-colors">
                        {t('workspace.viewSource')}
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Follow-up input */}
            <div className="border-t border-[#3B3A33] px-5 py-4 shrink-0">
              <div className="flex items-center gap-3 rounded-sm border border-[#3B3A33] bg-[#1D211F] px-4 py-3">
                <input
                  readOnly
                  placeholder={t('workspace.askFollowUp')}
                  className="w-full bg-transparent font-sans text-sm text-stone outline-none placeholder:text-stone/50"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
