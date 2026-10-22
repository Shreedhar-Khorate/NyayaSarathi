'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Scale,
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
  ExternalLink,
  BookOpen,
  CheckCircle2,
  XCircle,
  HelpCircle,
  FileText,
  RotateCcw
} from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext';
import { Navbar, Footer } from '@/components/layout/NavAndFooter';
import { API_BASE_URL } from '@/lib/config';
import { CaseTypeSelect, ALL_KNOWN_CASE_TYPES } from '@/components/ui/CaseTypeSelect';

interface Precedent {
  case_name: string;
  court: string;
  year: number;
  similarity: number;
  outcome: string;
  citation: string;
  source_url: string;
  cnr?: string;
  verbatim_excerpt?: string;
  excerpt?: string;
}

interface AnalyzeResponseData {
  status?: string;
  success_probability: number;
  confidence: string;
  predicted_outcome?: string;
  outcome?: string;
  precedents: Precedent[];
  supporting_factors: string[];
  opposing_factors: string[];
  takeaway: string;
  disclaimer?: string;
  probability?: string;
}

const SAMPLE_CASES = [
  {
    title: '498A Anticipatory Bail (Procedural Non-Compliance)',
    type: 'Bail',
    court: 'Supreme Court of India',
    sections: 'Section 41 CrPC, Section 498A IPC',
    description: 'Anticipatory bail application in a Section 498A IPC case. The investigating officer failed to issue or serve a mandatory notice under Section 41 and Section 41A CrPC before initiating arrest procedures. Offense carries a maximum sentence of under 7 years.'
  },
  {
    title: 'Speedy Trial Bail (Prolonged Incarceration)',
    type: 'Bail',
    court: 'Supreme Court of India',
    sections: 'Article 21, Section 439 CrPC',
    description: 'Regular bail application based on prolonged detention. The accused has been in judicial custody for over 3 years without trial commencement or charge framing. Article 21 fundamental right to speedy trial is invoked.'
  },
  {
    title: 'Bail Rejection (Witness Tampering Risk)',
    type: 'Bail',
    court: 'Supreme Court of India',
    sections: 'Section 302 IPC, Section 439 CrPC',
    description: 'Bail application in a murder case under Section 302 IPC. The prosecution has submitted witness affidavits indicating serious threats to prime eyewitnesses and past criminal antecedents of the applicant.'
  }
];

export default function PredictorPage() {
  const { language, t } = useLanguage();
  const [caseType, setCaseType] = useState('Bail');
  const [court, setCourt] = useState('');
  const [sections, setSections] = useState('');
  const [description, setDescription] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponseData | null>(null);

  const handleAnalyze = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!description.trim()) {
      setError('Please provide a case description or brief facts before predicting.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const parsedSections = sections.trim()
        ? sections.split(/[,;\n]+/).map((s) => s.trim()).filter(Boolean)
        : [];

      const res = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          case_type: caseType,
          description: description.trim(),
          court: court.trim() || undefined,
          sections: parsedSections,
          target_language: language,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        let message = 'Failed to calculate prediction from backend server.';
        if (typeof errData.detail === 'string') {
          message = errData.detail;
        } else if (Array.isArray(errData.detail)) {
          message = errData.detail.map((e: any) => `${e.loc?.join('.') || ''}: ${e.msg || 'Invalid field'}`).join(' | ');
        }
        throw new Error(message);
      }

      const data: AnalyzeResponseData = await res.json();
      setResult(data);
    } catch (err: any) {
      console.error('Prediction API Error:', err);
      setError(err.message || `Could not connect to NyayaSarathi API backend. Ensure the backend server is running at ${API_BASE_URL}.`);
    } finally {
      setLoading(false);
    }
  };

  // Automatically re-fetch prediction in selected target language when user toggles language
  useEffect(() => {
    if (result && description.trim() && !loading) {
      handleAnalyze();
    }
  }, [language]);

  const loadSample = (sample: typeof SAMPLE_CASES[0]) => {
    setCaseType(sample.type);
    setCourt(sample.court);
    setSections(sample.sections);
    setDescription(sample.description);
    setError(null);
  };

  const resetForm = () => {
    setCaseType('Bail');
    setCourt('');
    setSections('');
    setDescription('');
    setResult(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-[#151716] text-[#F4EFE5] selection:bg-[#6E2634]/40 flex flex-col font-sans">
      <Navbar />

      {/* Main Content Surface */}
      <main className="flex-1 pt-28 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        
        {/* Page Header */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center max-w-3xl mx-auto mb-10"
        >
          <h1 className="font-display text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight text-[#F4EFE5] mb-3">
            {t('predictor.title')}
          </h1>
          <p className="text-stone/80 text-sm sm:text-base leading-relaxed">
            {t('predictor.subtitle')}
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* LEFT COLUMN: Input Form */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="lg:col-span-5 ink-panel rounded-xl p-6 sm:p-7 border border-[#3B3A33] shadow-2xl relative"
          >
            <div className="flex items-center justify-between pb-4 mb-6 border-b border-[#3B3A33]">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-[#B59A68]" />
                <h2 className="font-display text-lg font-semibold text-[#F4EFE5]">{t('predictor.formTitle')}</h2>
              </div>
              <button
                type="button"
                onClick={resetForm}
                className="flex items-center gap-1 text-xs text-stone/70 hover:text-[#B59A68] transition-colors"
                title={t('predictor.resetBtn')}
              >
                <RotateCcw className="w-3.5 h-3.5" />
                {t('predictor.resetBtn')}
              </button>
            </div>

            {/* Quick Sample Selector */}
            <div className="mb-6">
              <label className="block text-xs font-semibold uppercase tracking-wider text-stone/70 mb-2">
                {t('predictor.quickSamples')}
              </label>
              <div className="flex flex-col gap-2">
                {SAMPLE_CASES.map((sample, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => loadSample(sample)}
                    className="text-left text-xs p-2.5 rounded border border-[#3B3A33] bg-[#242925]/60 hover:bg-[#242925] hover:border-[#B59A68]/50 text-stone hover:text-[#F4EFE5] transition-all flex items-center justify-between group"
                  >
                    <span className="truncate pr-2 font-medium">{sample.title}</span>
                    <ArrowRight className="w-3.5 h-3.5 shrink-0 text-[#B59A68] opacity-0 group-hover:opacity-100 transition-opacity" />
                  </button>
                ))}
              </div>
            </div>

            <form onSubmit={handleAnalyze} className="space-y-4">
              {/* Case Type */}
              <div>
                <label htmlFor="case_type" className="block text-xs font-medium text-stone/90 mb-1">
                  {t('predictor.categoryLabel')} <span className="text-[#8A3545]">*</span>
                </label>
                <CaseTypeSelect
                  value={caseType}
                  onChange={(val) => setCaseType(val)}
                  required
                />

                {/* Custom Category Input field if Custom is chosen or typed */}
                {(!caseType || !ALL_KNOWN_CASE_TYPES.includes(caseType)) && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="mt-2"
                  >
                    <input
                      type="text"
                      placeholder="Specify custom filing type or specific statute..."
                      value={caseType}
                      onChange={(e) => setCaseType(e.target.value)}
                      className="w-full rounded bg-[#151716] border border-[#B59A68] px-3.5 py-2 text-sm text-[#F4EFE5] placeholder:text-stone/40 focus:outline-none transition-colors"
                      required
                    />
                  </motion.div>
                )}
              </div>


              {/* Court (Optional) */}
              <div>
                <label htmlFor="court" className="block text-xs font-medium text-stone/90 mb-1">
                  {t('predictor.courtLabel')}
                </label>
                <input
                  id="court"
                  type="text"
                  placeholder="e.g. Supreme Court of India"
                  value={court}
                  onChange={(e) => setCourt(e.target.value)}
                  className="w-full rounded bg-[#151716] border border-[#3B3A33] px-3.5 py-2 text-sm text-[#F4EFE5] placeholder:text-stone/40 focus:outline-none focus:border-[#B59A68] transition-colors"
                />
              </div>

              {/* Relevant Sections (Optional) */}
              <div>
                <label htmlFor="sections" className="block text-xs font-medium text-stone/90 mb-1">
                  {t('predictor.sectionsLabel')}
                </label>
                <input
                  id="sections"
                  type="text"
                  placeholder="e.g. Section 41 CrPC, Section 498A IPC"
                  value={sections}
                  onChange={(e) => setSections(e.target.value)}
                  className="w-full rounded bg-[#151716] border border-[#3B3A33] px-3.5 py-2 text-sm text-[#F4EFE5] placeholder:text-stone/40 focus:outline-none focus:border-[#B59A68] transition-colors"
                />
              </div>

              {/* Description */}
              <div>
                <label htmlFor="description" className="block text-xs font-medium text-stone/90 mb-1">
                  {t('predictor.factsLabel')} <span className="text-[#8A3545]">*</span>
                </label>
                <textarea
                  id="description"
                  rows={5}
                  placeholder="Enter detailed facts, procedural history, or specific statutory grounds..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full rounded bg-[#151716] border border-[#3B3A33] p-3 text-sm text-[#F4EFE5] placeholder:text-stone/40 focus:outline-none focus:border-[#B59A68] transition-colors doc-scroll resize-none"
                  required
                />
              </div>

              {error && (
                <div className="p-3 rounded bg-[#6E2634]/20 border border-[#8A3545]/50 flex items-start gap-2.5 text-xs text-[#F4EFE5]">
                  <AlertTriangle className="w-4 h-4 text-[#8A3545] shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full btn-oxblood rounded py-3 font-semibold text-sm tracking-wide flex items-center justify-center gap-2 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all mt-2"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-ivory/30 border-t-ivory rounded-full animate-spin" />
                    <span>{t('predictor.analyzingBtn')}</span>
                  </>
                ) : (
                  <>
                    <span>{t('predictor.computeBtn')}</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          </motion.div>

          {/* RIGHT COLUMN: Output Results */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="lg:col-span-7 space-y-6"
          >
            {loading && (
              <div className="ink-panel rounded-xl p-12 border border-[#3B3A33] text-center flex flex-col items-center justify-center space-y-4 min-h-[420px]">
                <div className="relative">
                  <div className="w-16 h-16 border-2 border-[#3B3A33] border-t-[#B59A68] rounded-full animate-spin" />
                  <Scale className="w-6 h-6 text-[#B59A68] absolute inset-0 m-auto" />
                </div>
                <div className="space-y-1">
                  <h3 className="font-display text-lg font-semibold text-[#F4EFE5]">{t('predictor.analyzingBtn')}</h3>
                </div>
              </div>
            )}

            {!loading && !result && !error && (
              <div className="ink-panel rounded-xl p-10 border border-[#3B3A33] text-center flex flex-col items-center justify-center min-h-[420px] space-y-4">
                <div className="w-14 h-14 rounded-full bg-[#242925] border border-[#3B3A33] flex items-center justify-center text-[#B59A68]">
                  <BookOpen className="w-7 h-7" />
                </div>
                <div className="max-w-md space-y-2">
                  <h3 className="font-display text-xl font-semibold text-[#F4EFE5]">{t('predictor.awaitingTitle')}</h3>
                  <p className="text-xs text-stone/70 leading-relaxed">
                    {t('predictor.awaitingDesc')}
                  </p>
                </div>
              </div>
            )}

            <AnimatePresence mode="wait">
              {!loading && result && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  transition={{ duration: 0.4 }}
                  className="space-y-6"
                >
                  {/* Probability & Confidence Card */}
                  <div className="ink-panel rounded-xl p-6 border border-[#3B3A33] relative overflow-hidden">
                    {(() => {
                      const isInsufficient =
                        result.status === 'insufficient_data' ||
                        result.success_probability === null ||
                        result.success_probability === undefined;

                      const rawOutcome = isInsufficient
                        ? 'INSUFFICIENT DATA / ABSTAINED'
                        : (result.predicted_outcome || result.outcome || (
                            result.success_probability >= 65 ? 'Favorable' :
                            result.success_probability <= 35 ? 'Unfavorable' :
                            'Balanced / Discretionary'
                          )).toUpperCase();

                      const isFav = !isInsufficient && rawOutcome.includes('FAVORABLE') && !rawOutcome.includes('UNFAVORABLE');
                      const isBal = !isInsufficient && (rawOutcome.includes('BALANCED') || rawOutcome.includes('DISCRETIONARY'));

                      const displayOutcome = isInsufficient
                        ? 'INSUFFICIENT DATA / ABSTAINED'
                        : language === 'mr'
                        ? (isFav ? 'अनुकूल (FAVORABLE)' : isBal ? 'संतुलित (BALANCED)' : 'प्रतिकूल (UNFAVORABLE)')
                        : language === 'hi'
                        ? (isFav ? 'अनुकूल (FAVORABLE)' : isBal ? 'संतुलित (BALANCED)' : 'प्रतिकूल (UNFAVORABLE)')
                        : rawOutcome;

                      const displayConfidence = language === 'mr'
                        ? (result.confidence?.toLowerCase() === 'high' ? 'उच्च (HIGH)' : result.confidence?.toLowerCase() === 'medium' ? 'मध्यम (MEDIUM)' : 'कमी (LOW)')
                        : language === 'hi'
                        ? (result.confidence?.toLowerCase() === 'high' ? 'उच्च (HIGH)' : result.confidence?.toLowerCase() === 'medium' ? 'मध्यम (MEDIUM)' : 'निम्न (LOW)')
                        : result.confidence;

                      return (
                        <>
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
                            <div className="space-y-2">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold tracking-wider uppercase ${
                                  isInsufficient
                                    ? 'bg-[#B59A68]/20 text-[#B59A68] border border-[#B59A68]/40'
                                    : isFav
                                    ? 'bg-[#71877A]/20 text-[#71877A] border border-[#71877A]/40'
                                    : isBal
                                    ? 'bg-[#B59A68]/20 text-[#B59A68] border border-[#B59A68]/40'
                                    : 'bg-[#6E2634]/30 text-[#8A3545] border border-[#8A3545]/40'
                                }`}>
                                  {isInsufficient ? (
                                    <HelpCircle className="w-3.5 h-3.5" />
                                  ) : isFav ? (
                                    <CheckCircle2 className="w-3.5 h-3.5" />
                                  ) : isBal ? (
                                    <Scale className="w-3.5 h-3.5" />
                                  ) : (
                                    <XCircle className="w-3.5 h-3.5" />
                                  )}
                                  {displayOutcome}
                                </span>
                                <span className="text-xs font-mono uppercase tracking-wider px-2.5 py-1 rounded bg-[#242925] border border-[#3B3A33] text-stone">
                                  {t('predictor.confidence')}: {displayConfidence}
                                </span>
                              </div>
                              <h3 className="font-display text-xl font-semibold text-[#F4EFE5]">
                                {isInsufficient ? 'Prediction Status' : t('predictor.favorableProbability')}
                              </h3>
                            </div>

                            {/* Percentage Badge */}
                            <div className="flex items-center gap-3">
                              <div className="text-right">
                                <div className={`font-display font-bold ${
                                  isInsufficient
                                    ? 'text-xl sm:text-2xl text-[#B59A68]'
                                    : isFav
                                    ? 'text-4xl sm:text-5xl text-[#71877A]'
                                    : isBal
                                    ? 'text-4xl sm:text-5xl text-[#B59A68]'
                                    : 'text-4xl sm:text-5xl text-[#8A3545]'
                                }`}>
                                  {isInsufficient ? 'N/A (Abstained)' : `${result.success_probability}%`}
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* Progress Bar */}
                          <div className="w-full bg-[#151716] h-2.5 rounded-full mt-5 overflow-hidden border border-[#3B3A33]">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: isInsufficient ? '0%' : `${result.success_probability}%` }}
                              transition={{ duration: 0.8, ease: 'easeOut' }}
                              className={`h-full ${
                                isInsufficient ? 'bg-[#3B3A33]' : isFav ? 'bg-[#71877A]' : isBal ? 'bg-[#B59A68]' : 'bg-[#8A3545]'
                              }`}
                            />
                          </div>
                        </>
                      );
                    })()}
                  </div>

                  {/* Grounded Plain-Language Takeaway */}
                  <div className="ink-raised rounded-xl p-5 border border-[#3B3A33] space-y-2">
                    <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#B59A68]">
                      <Scale className="w-4 h-4" />
                      {t('predictor.takeawayTitle')}
                    </div>
                    <p className="text-xs sm:text-sm text-[#F4EFE5]/90 leading-relaxed font-legal italic">
                      &ldquo;{result.takeaway}&rdquo;
                    </p>
                  </div>

                  {/* Supporting vs Opposing Factors */}
                  {result.supporting_factors.length > 0 || result.opposing_factors.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Supporting Factors */}
                      <div className="ink-panel rounded-xl p-5 border border-[#3B3A33] space-y-3">
                        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#71877A]">
                          <CheckCircle2 className="w-4 h-4" />
                          {t('predictor.supportingFactors')} ({result.supporting_factors.length})
                        </div>
                        <ul className="space-y-2 text-xs text-stone/90">
                          {result.supporting_factors.map((factor, i) => (
                            <li key={i} className="flex items-start gap-2 bg-[#151716]/60 p-2.5 rounded border border-[#3B3A33]/50">
                              <span className="w-1.5 h-1.5 rounded-full bg-[#71877A] mt-1.5 shrink-0" />
                              <span>{factor}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Opposing Factors */}
                      <div className="ink-panel rounded-xl p-5 border border-[#3B3A33] space-y-3">
                        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#8A3545]">
                          <XCircle className="w-4 h-4" />
                          {t('predictor.opposingFactors')} ({result.opposing_factors.length})
                        </div>
                        <ul className="space-y-2 text-xs text-stone/90">
                          {result.opposing_factors.map((factor, i) => (
                            <li key={i} className="flex items-start gap-2 bg-[#151716]/60 p-2.5 rounded border border-[#3B3A33]/50">
                              <span className="w-1.5 h-1.5 rounded-full bg-[#8A3545] mt-1.5 shrink-0" />
                              <span>{factor}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ) : (
                    <div className="p-4 rounded-lg bg-[#242925]/60 border border-[#3B3A33] text-xs text-stone/80 flex items-start gap-2.5">
                      <HelpCircle className="w-4 h-4 text-[#B59A68] shrink-0 mt-0.5" />
                      <span>
                        <strong>Guidance for Prediction:</strong> To generate empirical factor attributions and historical outcome probabilities, please specify applicable statutory Acts (e.g. <em>Information Technology Act, 2000</em>, <em>IPC</em>) or Section numbers (e.g. <em>Section 43, 66, 66C</em>).
                      </span>
                    </div>
                  )}

                  {/* Cited Historical Precedents */}
                  <div className="ink-panel rounded-xl p-6 border border-[#3B3A33] space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="font-display text-base font-semibold text-[#F4EFE5] flex items-center gap-2">
                        <BookOpen className="w-4 h-4 text-[#B59A68]" />
                        {t('predictor.matchedPrecedents')} ({result.precedents.length})
                      </h4>
                    </div>

                    <div className="space-y-3">
                      {result.precedents.map((precedent, i) => {
                        const outcomeUpper = (precedent.outcome || '').toUpperCase();
                        const isPrecAllowed = outcomeUpper.includes('ALLOWED') || outcomeUpper.includes('GRANTED') || outcomeUpper.includes('QUASHED') || outcomeUpper.includes('DECREED');
                        const isPrecPartial = outcomeUpper.includes('PARTLY') || outcomeUpper.includes('PARTIAL') || outcomeUpper.includes('DISPOSED') || outcomeUpper.includes('WITHDRAWN');

                        return (
                          <div
                            key={i}
                            className="document-card rounded-lg p-4 transition-all hover:shadow-lg relative group"
                          >
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                              <h5 className="font-display font-semibold text-sm text-[#151716] group-hover:text-[#6E2634] transition-colors">
                                {precedent.case_name} ({precedent.year})
                              </h5>
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-[#151716] text-[#B59A68]">
                                  {Math.round(precedent.similarity * 100)}% {t('predictor.similarity')}
                                </span>
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                                  isPrecAllowed
                                    ? 'bg-[#71877A]/20 text-[#1E3A2F] border border-[#71877A]/40'
                                    : isPrecPartial
                                    ? 'bg-[#B59A68]/20 text-[#614E2E] border border-[#B59A68]/40'
                                    : 'bg-[#6E2634]/20 text-[#6E2634] border border-[#8A3545]/40'
                                }`}>
                                  {precedent.outcome}
                                </span>
                              </div>
                            </div>

                            {(precedent.verbatim_excerpt || precedent.excerpt) && (
                              <p className="text-[11px] text-[#151716]/75 italic line-clamp-2 my-1.5 pl-2 border-l-2 border-[#B59A68]/60">
                                &ldquo;{precedent.verbatim_excerpt || precedent.excerpt}&rdquo;
                              </p>
                            )}

                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-[#151716]/80 pt-2 border-t border-[#DED5C4]">
                              <span className="font-medium truncate max-w-full sm:max-w-[72%]">
                                {precedent.court} &bull; <span className="font-mono">{precedent.citation}</span>
                              </span>
                              {(() => {
                                const isKanoon = precedent.source_url?.includes('indiankanoon.org') || precedent.cnr?.startsWith('WEB_');
                                const label = isKanoon ? 'Indian Kanoon' : 'Hugging Face Dataset';
                                const targetUrl = precedent.source_url || 'https://huggingface.co/datasets/overthelex/indian-court-decisions';

                                return (
                                  <a
                                    href={targetUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1 font-semibold text-[#6E2634] hover:underline"
                                    title={`Open source on ${label}`}
                                  >
                                    <span>{label}</span>
                                    <ExternalLink className="w-3 h-3" />
                                  </a>
                                );
                              })()}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Advisory Disclaimer */}
                  <div className="p-4 rounded-lg bg-[#242925]/80 border border-[#3B3A33] flex items-start gap-3 text-xs text-stone/70">
                    <ShieldCheck className="w-4 h-4 text-[#B59A68] shrink-0 mt-0.5" />
                    <span>
                      {result.disclaimer || t('predictor.disclaimer')}
                    </span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
