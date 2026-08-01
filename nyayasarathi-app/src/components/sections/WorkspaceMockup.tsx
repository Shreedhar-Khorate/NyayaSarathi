'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, CheckCircle2, Search, SlidersHorizontal } from 'lucide-react';

const FILTER_TAGS = ['#BNS', '#IPC', '#SupremeCourt', '#Section420'];

const CITATIONS = [
  {
    id: 'c1',
    label: 'Para 14',
    text: 'In the matter of ',
  },
  {
    id: 'c2',
    label: 'Para 21',
    text: 'the Court, relying on the settled position under ',
  },
];

const ANSWER_LINES = [
  { text: 'The Court held that mere delay in lodging an FIR, by itself,', citeId: null },
  { text: 'does not vitiate the prosecution\u2019s case ', citeId: 'c1' },
  { text: 'where the delay stands satisfactorily explained on record.', citeId: null },
  { text: 'This finds direct support in the reasoning applied by the bench ', citeId: 'c2' },
  { text: 'in its interpretation of Section 154, CrPC.', citeId: null },
];

export default function WorkspaceMockup() {
  const [activeCite, setActiveCite] = useState<string | null>(null);
  const [activeFilters, setActiveFilters] = useState<string[]>(['#Section420']);

  const toggleFilter = (tag: string) => {
    setActiveFilters((prev) => (prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]));
  };

  return (
    <section id="workspace" className="relative py-32 md:py-40">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mb-14 max-w-2xl">
          <span className="mb-4 inline-block font-sans text-xs font-semibold uppercase tracking-[0.25em] text-amber">
            The NyayaSarathi Workspace
          </span>
          <h2 className="font-display text-4xl font-semibold leading-tight text-cream md:text-5xl">
            Read the judgment. Verify the answer. Same screen.
          </h2>
          <p className="mt-5 text-base leading-relaxed text-ash">
            Click any highlighted citation in the AI response to jump straight to its source paragraph
            in the document pane.
          </p>
        </div>

        {/* Unified search bar */}
        <div className="glass-panel-raised mb-6 flex flex-col gap-4 rounded-2xl p-4 sm:flex-row sm:items-center">
          <div className="flex flex-1 items-center gap-3 rounded-xl border border-white/10 bg-black/20 px-4 py-3">
            <Search className="h-4 w-4 shrink-0 text-ash" strokeWidth={2} />
            <input
              readOnly
              value="What did the Court hold about delay in FIR filing under Section 420?"
              className="w-full bg-transparent font-sans text-sm text-cream outline-none placeholder:text-ash"
            />
            <SlidersHorizontal className="h-4 w-4 shrink-0 text-ash" strokeWidth={2} />
          </div>
          <div className="flex flex-wrap gap-2">
            {FILTER_TAGS.map((tag) => {
              const active = activeFilters.includes(tag);
              return (
                <button
                  key={tag}
                  onClick={() => toggleFilter(tag)}
                  className={`rounded-full border px-3 py-1.5 font-sans text-xs font-medium transition-colors duration-200 ${
                    active
                      ? 'border-amber/40 bg-amber/15 text-amber'
                      : 'border-white/10 text-ash hover:border-white/20 hover:text-cream'
                  }`}
                >
                  {tag}
                </button>
              );
            })}
          </div>
        </div>

        {/* Split view */}
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          {/* Left: Document Reader */}
          <div className="glass-panel-raised flex flex-col rounded-2xl">
            <div className="flex items-center justify-between border-b hairline px-5 py-4">
              <div>
                <p className="font-display text-sm font-semibold text-cream">State v. Sharma, 2019</p>
                <p className="text-xs text-ash">Supreme Court of India · Criminal Appeal 1142/2019</p>
              </div>
              <span className="rounded-full border border-white/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-ash">
                OCR verified
              </span>
            </div>
            <div className="doc-scroll h-[420px] overflow-y-auto px-6 py-6 font-sans text-sm leading-7 text-ash">
              <p className="mb-4">
                14. In the matter of{' '}
                <span className="entity-underline entity-section">Section 420</span>, this Court has
                consistently held that mere delay in lodging the First Information Report does not, by
                itself, vitiate the prosecution&rsquo;s case, provided the delay is satisfactorily
                explained by the complainant on record.
              </p>
              <motion.p
                className="mb-4 rounded-lg px-2 py-1 -mx-2 transition-colors duration-500"
                animate={{
                  backgroundColor: activeCite === 'c1' ? 'rgba(245, 158, 11, 0.16)' : 'rgba(245, 158, 11, 0)',
                }}
              >
                Justice <span className="entity-underline entity-judge">A.K. Rao</span>, delivering the
                opinion of the bench, observed that the trial court correctly appreciated the testimony
                of PW-3 in light of the surrounding circumstances dated{' '}
                <span className="entity-underline entity-date">14 March 2018</span>.
              </motion.p>
              <p className="mb-4">
                18. The appellant&rsquo;s counsel contended that the delay of eleven days was fatal to
                the case, relying on precedent under the{' '}
                <span className="entity-underline entity-act">Bharatiya Nyaya Sanhita, 2023</span>.
              </p>
              <motion.p
                className="mb-4 rounded-lg px-2 py-1 -mx-2 transition-colors duration-500"
                animate={{
                  backgroundColor: activeCite === 'c2' ? 'rgba(245, 158, 11, 0.16)' : 'rgba(245, 158, 11, 0)',
                }}
              >
                21. This Court, relying on the settled position under{' '}
                <span className="entity-underline entity-section">Section 154, CrPC</span>, finds that
                the explanation tendered was consistent and credible, and accordingly affirms the
                conviction recorded by the courts below.
              </motion.p>
              <p>
                24. For the foregoing reasons, the appeal fails and is dismissed, with the sentence
                awarded by the Trial Court, as affirmed by the High Court, standing undisturbed.
              </p>
            </div>
          </div>

          {/* Right: AI Assistant Drawer */}
          <div className="glass-panel-raised flex flex-col rounded-2xl">
            <div className="flex items-center gap-2.5 border-b hairline px-5 py-4">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-amber/15">
                <Sparkles className="h-3.5 w-3.5 text-amber" strokeWidth={2} />
              </div>
              <p className="font-display text-sm font-semibold text-cream">RAG Assistant</p>
              <span className="ml-auto flex items-center gap-1.5 text-[11px] font-medium text-emerald-400/90">
                <CheckCircle2 className="h-3.5 w-3.5" strokeWidth={2} /> 2 sources verified
              </span>
            </div>
            <div className="flex-1 px-6 py-6 font-sans text-sm leading-8 text-cream">
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
                      className="mx-1 inline-flex items-center rounded-md border border-amber/30 bg-amber/10 px-1.5 py-0.5 align-middle font-sans text-[11px] font-semibold text-amber transition-colors hover:bg-amber/20"
                    >
                      {citation.label}
                    </button>
                  </span>
                );
              })}

              <AnimatePresence>
                {activeCite && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-5 overflow-hidden rounded-xl border border-amber/20 bg-amber/5 px-4 py-3"
                  >
                    <p className="text-xs font-semibold uppercase tracking-wider text-amber">
                      Source · {CITATIONS.find((c) => c.id === activeCite)?.label}
                    </p>
                    <p className="mt-1 text-xs leading-relaxed text-ash">
                      Highlighted in the document pane on the left — click any citation chip to verify.
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
            <div className="border-t hairline px-5 py-4">
              <div className="flex items-center gap-3 rounded-xl border border-white/10 bg-black/20 px-4 py-3">
                <input
                  readOnly
                  placeholder="Ask a follow-up question…"
                  className="w-full bg-transparent font-sans text-sm text-ash outline-none"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
