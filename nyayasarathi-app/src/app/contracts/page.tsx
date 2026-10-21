'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import {
  Scale,
  FileText,
  Upload,
  AlertTriangle,
  AlertCircle,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  Copy,
  Check,
  Sparkles,
  Filter,
  Search,
  Printer,
  RotateCcw,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  FileCheck2,
  Lock,
  Layers,
  ArrowRight,
} from 'lucide-react';
import { Navbar, Footer } from '@/components/layout/NavAndFooter';
import {
  analyzeContract,
  getToken,
  type ContractAnalysisResult,
  type ContractRedFlag,
} from '@/lib/auth';

export default function ContractsPage() {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ContractAnalysisResult | null>(null);
  const [isAuth, setIsAuth] = useState<boolean>(true);

  // Filters & Interactivity
  const [riskFilter, setRiskFilter] = useState<'ALL' | 'HIGH' | 'MEDIUM' | 'LOW'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedCards, setExpandedCards] = useState<Record<number, boolean>>({});
  const [copiedClauseIdx, setCopiedClauseIdx] = useState<number | null>(null);
  const [copiedSummary, setCopiedSummary] = useState(false);
  const [copiedReport, setCopiedReport] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setIsAuth(Boolean(getToken()));
  }, []);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const dropped = e.dataTransfer.files[0];
      validateAndSetFile(dropped);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (f: File) => {
    setError(null);
    setResult(null);
    const validExtensions = ['.pdf', '.docx', '.doc', '.txt'];
    const ext = '.' + f.name.split('.').pop()?.toLowerCase();
    if (!validExtensions.includes(ext)) {
      setError(`Unsupported format (${ext}). Please provide a PDF, DOCX, or TXT contract.`);
      return;
    }
    if (f.size > 25 * 1024 * 1024) {
      setError('File exceeds 25 MB limit. Please optimize or compress the document.');
      return;
    }
    setFile(f);
  };

  const handleAnalyze = async () => {
    if (!file) return;

    if (!isAuth) {
      setError('Authentication required. Please sign in to analyze contracts.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setLoadingStage('Validating contract document structure...');

    // Progress simulation for user engagement
    const stage1 = setTimeout(() => {
      setLoadingStage('Extracting clauses, paragraphs, and page layout...');
    }, 1200);

    const stage2 = setTimeout(() => {
      setLoadingStage('Auditing statutory risks against Indian Contract Act & High Court doctrines...');
    }, 3200);

    const stage3 = setTimeout(() => {
      setLoadingStage('Verifying clause citations and grounding quotes...');
    }, 5500);

    try {
      const data = await analyzeContract(file);
      setResult(data);
      // Auto-expand all high-risk cards by default
      const initialExpanded: Record<number, boolean> = {};
      data.red_flags.forEach((_, idx) => {
        initialExpanded[idx] = true;
      });
      setExpandedCards(initialExpanded);
    } catch (err: any) {
      console.error('Contract analysis error:', err);
      setError(
        err.message || 'An error occurred while analyzing the contract. Please verify your document and retry.'
      );
    } finally {
      clearTimeout(stage1);
      clearTimeout(stage2);
      clearTimeout(stage3);
      setLoading(false);
      setLoadingStage('');
    }
  };

  const handleReset = () => {
    setFile(null);
    setResult(null);
    setError(null);
    setSearchQuery('');
    setRiskFilter('ALL');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const toggleExpand = (idx: number) => {
    setExpandedCards((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const copyClause = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedClauseIdx(idx);
    setTimeout(() => setCopiedClauseIdx(null), 2000);
  };

  const copySummaryText = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedSummary(true);
    setTimeout(() => setCopiedSummary(false), 2000);
  };

  const copyFullReport = () => {
    if (!result) return;
    const lines = [
      `# NYAYASARATHI CONTRACT RED-FLAG AUDIT REPORT`,
      `Document: ${result.filename || file?.name || 'Contract'}`,
      `Document Classification: ${result.document_type_label || result.document_type || 'Unknown'}`,
      ...(result.classification_reason ? [`Classification Reason: ${result.classification_reason}`] : []),
      `Audit Status: ${result.audit_status || 'COMPLETED'}`,
      `Overall Risk Level: ${result.overall_risk_score}`,
      ...(result.score_breakdown
        ? [
            `Risk Score: ${result.score_breakdown.numerical_score} pts`,
            `Scoring Methodology: ${result.score_breakdown.scoring_method}`,
            `Risk Rationale: ${result.score_breakdown.risk_rationale}`,
          ]
        : []),
      `Total Flagged Clauses: ${result.red_flags.length} (High: ${highCount}, Medium: ${medCount}, Low: ${lowCount})`,
      `\n## EXECUTIVE SUMMARY`,
      result.summary || 'N/A',
      `\n## IDENTIFIED RED FLAGS`,
    ];

    result.red_flags.forEach((rf, i) => {
      const heading = rf.title
        ? `${i + 1}. [${rf.risk_level.toUpperCase()}] ${rf.title}`
        : `${i + 1}. [${rf.risk_level.toUpperCase()}] ${rf.risk_category || 'Contract Risk'}`;
      lines.push(`\n### ${heading}`);
      if (rf.finding_id) lines.push(`Finding ID: ${rf.finding_id}`);
      if (rf.risk_classification) {
        const classLabel =
          rf.risk_classification === 'potential_commercial_risk'
            ? 'Potential Commercial Risk'
            : rf.risk_classification === 'possible_legal_concern'
            ? 'Possible Legal Concern'
            : 'Legal Conclusion Requiring Review';
        lines.push(`Risk Classification: ${classLabel}`);
      }
      const pageLoc = rf.source_page
        ? `Page ${rf.source_page}`
        : rf.page_ref
        ? `Page ${rf.page_ref}`
        : 'Document-wide / Unspecified';
      lines.push(`Location: ${pageLoc}${rf.clause_location ? ` (${rf.clause_location})` : ''}`);
      lines.push(`\nVERBATIM CLAUSE:\n"${rf.verbatim_clause || rf.clause_text}"`);
      if (rf.statutory_provision) {
        lines.push(
          `\nAPPLICABLE STATUTE: ${rf.statutory_provision} (${rf.applicable_law || 'Indian Law'}) [${
            rf.statutory_verification_status === 'verified' ? 'Verified' : 'Unverified'
          }]`
        );
      }
      lines.push(`\nLEGAL EXPOSURE EXPLANATION:\n${rf.legal_explanation || rf.explanation}`);
      if (rf.application_to_clause) {
        lines.push(`\nAPPLICABILITY TO CLAUSE:\n${rf.application_to_clause}`);
      }
      if (rf.uncertainty_or_limitation) {
        lines.push(`\nMATERIAL LIMITATIONS & CONTEXT:\n${rf.uncertainty_or_limitation}`);
      }
      const action = rf.recommended_action || rf.recommendation;
      if (action) {
        lines.push(`\nRECOMMENDED REDLINE / ACTION:\n${action}`);
      }
    });

    if (result.limitations && result.limitations.length > 0) {
      lines.push(`\n## AUDIT LIMITATIONS & NOTES`);
      result.limitations.forEach((lim) => lines.push(`- ${lim}`));
    }

    lines.push(`\n## STATUTORY DISCLAIMER`);
    lines.push(
      `This red-flag audit is generated automatically for assistive legal research and risk triage. It does not constitute formal legal advice or create an attorney-client relationship. All findings, statutory interpretations, and redlines must be reviewed by a qualified Indian advocate prior to contract execution.`
    );

    navigator.clipboard.writeText(lines.join('\n'));
    setCopiedReport(true);
    setTimeout(() => setCopiedReport(false), 2500);
  };

  const handlePrint = () => {
    window.print();
  };

  // Filtered red flags
  const filteredFlags = (result?.red_flags || []).filter((flag) => {
    const matchesFilter =
      riskFilter === 'ALL' || flag.risk_level.toUpperCase() === riskFilter;
    const q = searchQuery.toLowerCase().trim();
    const matchesSearch =
      !q ||
      (flag.clause_text && flag.clause_text.toLowerCase().includes(q)) ||
      (flag.verbatim_clause && flag.verbatim_clause.toLowerCase().includes(q)) ||
      (flag.title && flag.title.toLowerCase().includes(q)) ||
      (flag.explanation && flag.explanation.toLowerCase().includes(q)) ||
      (flag.legal_explanation && flag.legal_explanation.toLowerCase().includes(q)) ||
      (flag.risk_category && flag.risk_category.toLowerCase().includes(q)) ||
      (flag.statutory_provision && flag.statutory_provision.toLowerCase().includes(q)) ||
      (flag.applicable_law && flag.applicable_law.toLowerCase().includes(q)) ||
      (flag.risk_classification && flag.risk_classification.toLowerCase().includes(q)) ||
      (flag.recommendation && flag.recommendation.toLowerCase().includes(q)) ||
      (flag.recommended_action && flag.recommended_action.toLowerCase().includes(q));
    return matchesFilter && matchesSearch;
  });

  const highCount =
    result?.risk_counts?.high ??
    (result?.red_flags || []).filter((f) => f.risk_level.toLowerCase() === 'high').length;
  const medCount =
    result?.risk_counts?.medium ??
    (result?.red_flags || []).filter((f) => f.risk_level.toLowerCase() === 'medium').length;
  const lowCount =
    result?.risk_counts?.low ??
    (result?.red_flags || []).filter((f) => f.risk_level.toLowerCase() === 'low').length;

  return (
    <div className="min-h-screen bg-[#151716] text-[#F4EFE5] flex flex-col selection:bg-[#6E2634]/40 font-sans">
      <Navbar />

      <main className="flex-1 pt-28 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        {/* Page Header */}
        <div className="text-center max-w-3xl mx-auto mb-10">
          <div className="inline-flex items-center gap-2 rounded-full border border-[#B59A68]/30 bg-[#B59A68]/10 px-3.5 py-1 text-xs font-semibold text-[#B59A68] mb-3">
            <Scale className="w-3.5 h-3.5 text-[#B59A68]" />
            <span>Statutory Contract Intelligence</span>
          </div>
          <h1 className="font-display text-3xl sm:text-4xl md:text-5xl font-semibold tracking-tight text-[#F4EFE5]">
            Contract Red-Flag Analyzer
          </h1>
          <p className="mt-3 text-stone/80 font-sans text-sm sm:text-base leading-relaxed">
            Audit commercial and legal contracts against Indian statutory doctrine — identifying
            unilateral termination, unlimited liability, unconscionable restraints of trade,
            and jurisdiction traps with grounded clause citations.
          </p>
          <div className="mt-3 inline-flex items-center gap-2 text-xs text-stone/60 italic border border-[#3B3A33]/60 rounded-full px-3 py-1 bg-[#1A1C1B]">
            <span>Note: Findings provide assistive statutory intelligence; final negotiation remains subject to advocate review.</span>
          </div>
        </div>

        {/* Authentication Warning Banner if guest */}
        {!isAuth && (
          <div className="mb-8 rounded-xl border border-[#B59A68]/40 bg-[#B59A68]/10 p-4 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <Lock className="w-5 h-5 text-[#B59A68] shrink-0" />
              <p className="text-xs sm:text-sm text-[#EDE8DC]">
                <strong className="text-[#B59A68]">Session Required:</strong> Contract document analysis is protected. Please sign in to upload and audit contracts.
              </p>
            </div>
            <Link
              href="/login"
              className="shrink-0 rounded px-3.5 py-1.5 text-xs font-semibold text-[#151716] bg-[#B59A68] hover:bg-[#c9af7e] transition-colors"
            >
              Sign In
            </Link>
          </div>
        )}

        {/* Workspace: Upload vs Results */}
        {!result ? (
          /* Upload State */
          <div className="max-w-2xl mx-auto">
            <div className="ink-panel border border-[#3B3A33] rounded-xl p-6 sm:p-8 shadow-xl bg-[#1A1C1B]">
              <h2 className="font-display text-lg font-semibold text-[#F4EFE5] mb-2 flex items-center gap-2">
                <Upload className="w-4 h-4 text-[#B59A68]" />
                Upload Contract Agreement
              </h2>
              <p className="text-xs text-stone/80 mb-5">
                Ingest digital PDF, scanned PDF (auto-OCR), DOCX, or TXT agreements up to 25 MB.
              </p>

              {/* Drag & Drop Zone */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
                  isDragging
                    ? 'border-[#B59A68] bg-[#B59A68]/10'
                    : 'border-[#3B3A33] hover:border-[#B59A68]/50 bg-[#151716]'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.doc,.txt"
                  onChange={handleFileChange}
                  className="hidden"
                />

                <div className="mx-auto w-12 h-12 rounded-full bg-[#1A1C1B] border border-[#3B3A33] flex items-center justify-center mb-3 text-[#B59A68]">
                  <FileText className="w-6 h-6" />
                </div>

                {file ? (
                  <div>
                    <p className="text-sm font-semibold text-[#F4EFE5] truncate max-w-sm mx-auto">
                      {file.name}
                    </p>
                    <p className="text-xs text-stone/70 mt-1 font-mono">
                      {(file.size / (1024 * 1024)).toFixed(2)} MB &bull; {file.name.split('.').pop()?.toUpperCase()}
                    </p>
                    <p className="text-xs text-[#B59A68] mt-2 font-medium">
                      Click or drag a new file to replace
                    </p>
                  </div>
                ) : (
                  <div>
                    <p className="text-sm font-medium text-stone/90">
                      Drag and drop your contract here, or{' '}
                      <span className="text-[#B59A68] underline decoration-stone/50 hover:decoration-[#B59A68]">
                        browse files
                      </span>
                    </p>
                    <p className="text-xs text-stone/60 mt-1.5">
                      PDF, DOCX, TXT &bull; Max 25 MB &bull; Scanned PDFs processed via OCR
                    </p>
                  </div>
                )}
              </div>

              {/* Error Message */}
              {error && (
                <div className="mt-4 p-3.5 rounded-lg bg-[#6E2634]/25 border border-[#8A3545]/60 flex items-start gap-2.5 text-xs text-[#E25C6F]">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  <div className="flex-1 leading-relaxed">{error}</div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="mt-6 flex items-center justify-between gap-3 pt-4 border-t border-[#3B3A33]/70">
                {file ? (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setFile(null);
                      if (fileInputRef.current) fileInputRef.current.value = '';
                    }}
                    disabled={loading}
                    className="text-xs text-stone/70 hover:text-stone font-medium px-3 py-2 rounded hover:bg-white/[0.04] transition-colors"
                  >
                    Remove File
                  </button>
                ) : (
                  <div />
                )}

                <button
                  type="button"
                  id="analyze-contract-btn"
                  onClick={handleAnalyze}
                  disabled={!file || loading}
                  className={`btn-oxblood group flex items-center justify-center gap-2 rounded px-5 py-2.5 font-sans text-sm font-semibold tracking-wide transition-all ${
                    !file || loading ? 'opacity-50 cursor-not-allowed' : 'hover:shadow-lg'
                  }`}
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-[#F4EFE5]/30 border-t-[#F4EFE5] rounded-full animate-spin" />
                      <span>Auditing Contract...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 text-[#B59A68]" />
                      <span>Analyze Red Flags</span>
                      <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
                    </>
                  )}
                </button>
              </div>

              {/* Loading progress banner */}
              {loading && (
                <div className="mt-5 p-4 rounded-xl bg-[#151716] border border-[#3B3A33] animate-pulse">
                  <div className="flex items-center gap-3">
                    <div className="w-5 h-5 rounded-full bg-[#B59A68]/20 flex items-center justify-center">
                      <Scale className="w-3 h-3 text-[#B59A68] animate-bounce" />
                    </div>
                    <span className="text-xs font-mono text-[#B59A68]">{loadingStage}</span>
                  </div>
                  <div className="w-full bg-[#1D211F] rounded-full h-1.5 mt-3 overflow-hidden">
                    <div className="bg-[#B59A68] h-1.5 rounded-full w-2/3 animate-[shimmer_2s_infinite]" />
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Results View */
          <div className="space-y-8 animate-fadeIn">
            {/* Top Toolbar / Quick Actions */}
            <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-[#1A1C1B] border border-[#3B3A33]">
              <div className="flex items-center gap-3">
                <FileCheck2 className="w-5 h-5 text-[#B59A68]" />
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-sm font-semibold text-[#F4EFE5]">
                      {result.filename || file?.name || 'Contract Audit'}
                    </h3>
                    {result.document_type_label && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-[#B59A68]/20 text-[#D4AF37] border border-[#B59A68]/40">
                        {result.document_type_label}
                      </span>
                    )}
                    {result.classification_confidence !== undefined &&
                      result.classification_confidence !== null && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#151716] text-[#B59A68] border border-[#3B3A33]">
                          {Math.round(result.classification_confidence * 100)}% Conf
                        </span>
                      )}
                    {result.audit_status && (
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase border ${
                          result.audit_status === 'COMPLETED'
                            ? 'bg-emerald-950/40 text-emerald-400 border-emerald-800/50'
                            : result.audit_status === 'DOCUMENT_TYPE_MISMATCH'
                            ? 'bg-[#6E2634]/40 text-[#E25C6F] border-[#8A3545]/60'
                            : 'bg-amber-950/40 text-amber-400 border-amber-800/50'
                        }`}
                      >
                        {result.audit_status.replace(/_/g, ' ')}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-stone/70 mt-0.5">
                    Extracted via {result.extraction_method || 'PyMuPDF'} &bull;{' '}
                    {result.total_pages ? `${result.total_pages} pages inspected` : 'Document text processed'}
                    {result.classification_reason ? ` &bull; ${result.classification_reason}` : ''}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 flex-wrap">
                <button
                  type="button"
                  onClick={copyFullReport}
                  className="flex items-center gap-1.5 rounded border border-[#3B3A33] bg-[#151716] px-3 py-1.5 text-xs font-medium text-stone hover:text-ivory hover:border-[#B59A68]/60 transition-colors"
                >
                  {copiedReport ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedReport ? 'Report Copied' : 'Copy Full Report'}</span>
                </button>

                <button
                  type="button"
                  onClick={handlePrint}
                  className="flex items-center gap-1.5 rounded border border-[#3B3A33] bg-[#151716] px-3 py-1.5 text-xs font-medium text-stone hover:text-ivory hover:border-[#B59A68]/60 transition-colors"
                >
                  <Printer className="w-3.5 h-3.5" />
                  <span>Print Report</span>
                </button>

                <button
                  type="button"
                  onClick={handleReset}
                  className="flex items-center gap-1.5 rounded border border-[#6E2634]/70 bg-[#6E2634]/30 px-3 py-1.5 text-xs font-semibold text-[#E25C6F] hover:bg-[#6E2634]/50 transition-colors"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Analyze Another</span>
                </button>
              </div>
            </div>

            {/* Document Mismatch Dedicated Notification Banner */}
            {result.audit_status === 'DOCUMENT_TYPE_MISMATCH' && (
              <div className="rounded-xl border border-[#B59A68]/50 bg-[#B59A68]/10 p-5 space-y-3">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-[#D4AF37] shrink-0 mt-0.5" />
                  <div className="flex-1 space-y-1">
                    <h4 className="text-sm font-semibold text-[#F4EFE5]">
                      Document Type Mismatch: {result.document_type_label || 'Non-Contract Document'}
                    </h4>
                    <p className="text-xs text-stone/80 leading-relaxed">
                      {result.summary}
                    </p>
                    {result.recommended_action && (
                      <p className="text-xs text-[#D4AF37] font-medium pt-1">
                        <strong>Recommended Action:</strong> {result.recommended_action}
                      </p>
                    )}
                  </div>
                </div>
                <div className="pt-2 flex flex-wrap gap-2 border-t border-[#B59A68]/20">
                  <Link
                    href="/legal-research"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-[#1A1C1B] text-[#D4AF37] border border-[#B59A68]/40 hover:bg-[#B59A68]/20 transition-colors"
                  >
                    <Scale className="w-3.5 h-3.5" />
                    <span>Search Precedents in Legal Research</span>
                  </Link>
                  <Link
                    href="/predictor"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-[#1A1C1B] text-[#D4AF37] border border-[#B59A68]/40 hover:bg-[#B59A68]/20 transition-colors"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Open Case Predictor</span>
                  </Link>
                  <button
                    type="button"
                    onClick={handleReset}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-[#6E2634]/30 text-[#E25C6F] border border-[#8A3545]/50 hover:bg-[#6E2634]/50 transition-colors"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Upload a Commercial Contract</span>
                  </button>
                </div>
              </div>
            )}

            {/* Risk Assessment Summary Banner */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
              {/* Overall Risk Card */}
              {result.audit_status === 'DOCUMENT_TYPE_MISMATCH' || result.overall_risk_score.toLowerCase() === 'not assessed' ? (
                <div className="lg:col-span-4 rounded-xl p-6 border bg-[#6E2634]/15 border-[#8A3545]/50 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs uppercase font-mono tracking-wider text-stone/80 font-bold">
                        Audit Status
                      </span>
                      <AlertCircle className="w-5 h-5 text-[#E25C6F]" />
                    </div>
                    <div className="font-display text-2xl font-bold tracking-tight text-[#E25C6F]">
                      NOT ASSESSED
                    </div>
                    <p className="mt-2 text-xs text-stone/80 leading-relaxed">
                      Document is identified as a {result.document_type_label || 'non-contract legal document'}. Commercial contract risk profiling is not applicable to judicial decisions or legal notices.
                    </p>
                  </div>
                  <div className="mt-6 pt-4 border-t border-white/[0.08] text-center">
                    <span className="inline-block text-[11px] font-mono text-[#D4AF37] bg-[#B59A68]/15 px-2.5 py-1 rounded border border-[#B59A68]/30">
                      0 Contract Findings Evaluated
                    </span>
                  </div>
                </div>
              ) : (
                <div
                  className={`lg:col-span-4 rounded-xl p-6 border flex flex-col justify-between ${
                    result.overall_risk_score.toLowerCase() === 'high'
                      ? 'bg-[#6E2634]/20 border-[#6E2634]/70'
                      : result.overall_risk_score.toLowerCase() === 'medium'
                      ? 'bg-[#B59A68]/15 border-[#B59A68]/60'
                      : 'bg-emerald-950/25 border-emerald-800/60'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs uppercase font-mono tracking-wider text-stone/80 font-bold">
                        Overall Risk Profile
                      </span>
                      {result.overall_risk_score.toLowerCase() === 'high' ? (
                        <ShieldAlert className="w-5 h-5 text-[#E25C6F]" />
                      ) : result.overall_risk_score.toLowerCase() === 'medium' ? (
                        <AlertTriangle className="w-5 h-5 text-[#D4AF37]" />
                      ) : (
                        <ShieldCheck className="w-5 h-5 text-emerald-400" />
                      )}
                    </div>
                    <div className="flex items-baseline gap-2 mt-1">
                      <div
                        className={`font-display text-3xl font-bold tracking-tight ${
                          result.overall_risk_score.toLowerCase() === 'high'
                            ? 'text-[#E25C6F]'
                            : result.overall_risk_score.toLowerCase() === 'medium'
                            ? 'text-[#D4AF37]'
                            : 'text-emerald-400'
                        }`}
                      >
                        {result.overall_risk_score.toUpperCase()} RISK
                      </div>
                      {result.score_breakdown && (
                        <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-white/[0.06] border border-white/10 text-stone">
                          {result.score_breakdown.numerical_score} pts
                        </span>
                      )}
                    </div>
                    <p className="mt-2 text-xs text-stone/80 leading-relaxed">
                      {result.overall_risk_score.toLowerCase() === 'high'
                        ? 'Severe contractual imbalances detected. Significant indemnification, liability, or unilateral clauses require legal intervention.'
                        : result.overall_risk_score.toLowerCase() === 'medium'
                        ? 'Moderate risk exposure identified. Terms contain ambiguous payment, renewal, or dispute resolutions warranting redlines.'
                        : 'Standard contractual terms identified with low statutory exposure.'}
                    </p>
                  </div>

                  {/* Severity Breakdown Bar */}
                  <div className="mt-6 pt-4 border-t border-white/[0.08] grid grid-cols-3 gap-2 text-center">
                    <div className="bg-[#6E2634]/30 rounded-lg p-2 border border-[#6E2634]/40">
                      <span className="block text-xs font-mono text-[#E25C6F] font-bold">{highCount}</span>
                      <span className="text-[10px] text-stone/70 uppercase">High</span>
                    </div>
                    <div className="bg-[#B59A68]/20 rounded-lg p-2 border border-[#B59A68]/30">
                      <span className="block text-xs font-mono text-[#D4AF37] font-bold">{medCount}</span>
                      <span className="text-[10px] text-stone/70 uppercase">Med</span>
                    </div>
                    <div className="bg-emerald-950/30 rounded-lg p-2 border border-emerald-800/30">
                      <span className="block text-xs font-mono text-emerald-400 font-bold">{lowCount}</span>
                      <span className="text-[10px] text-stone/70 uppercase">Low</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Executive Summary Box */}
              <div className="lg:col-span-8 rounded-xl p-6 bg-[#1A1C1B] border border-[#3B3A33] flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-display text-base font-semibold text-[#F4EFE5] flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-[#B59A68]" />
                      Executive Legal Summary
                    </h3>
                    <button
                      type="button"
                      onClick={() => copySummaryText(result.summary || '')}
                      className="text-xs text-stone/70 hover:text-stone flex items-center gap-1 transition-colors"
                    >
                      {copiedSummary ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      <span>{copiedSummary ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>
                  <p className="text-xs sm:text-sm text-[#EDE8DC] leading-relaxed">
                    {result.summary || 'Statutory analysis completed across all extracted clauses.'}
                  </p>
                </div>

                {/* Audit Limitations Banner if any */}
                {result.limitations && result.limitations.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-[#3B3A33]/80">
                    <span className="text-[11px] font-mono font-bold text-[#B59A68] uppercase block mb-1">
                      Audit Notes & Verification Limitations:
                    </span>
                    <ul className="text-xs text-stone/70 space-y-0.5 list-disc list-inside">
                      {result.limitations.map((lim, i) => (
                        <li key={i}>{lim}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            {/* Score Breakdown & Methodology Card */}
            {result.score_breakdown && (
              <div className="rounded-xl p-5 bg-[#1A1C1B] border border-[#3B3A33] space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#3B3A33]/70 pb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-[#B59A68]/20 flex items-center justify-center text-[#B59A68]">
                      <Scale className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-xs sm:text-sm font-semibold text-[#F4EFE5] flex items-center gap-2">
                        <span>Risk Scoring Methodology & Calculation</span>
                        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#B59A68]/15 text-[#D4AF37] border border-[#B59A68]/30">
                          {result.score_breakdown.numerical_score} Points Total
                        </span>
                      </h4>
                      <p className="text-[11px] font-mono text-stone/60 mt-0.5">
                        Model: {result.score_breakdown.scoring_method}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-xs font-mono">
                    <span className="text-[#E25C6F] bg-[#6E2634]/20 border border-[#6E2634]/40 px-2 py-1 rounded">
                      High: {result.score_breakdown.high_count} &times; 5 = {result.score_breakdown.high_count * 5} pts
                    </span>
                    <span className="text-[#D4AF37] bg-[#B59A68]/20 border border-[#B59A68]/40 px-2 py-1 rounded">
                      Med: {result.score_breakdown.medium_count} &times; 3 = {result.score_breakdown.medium_count * 3} pts
                    </span>
                    <span className="text-emerald-400 bg-emerald-950/30 border border-emerald-800/40 px-2 py-1 rounded">
                      Low: {result.score_breakdown.low_count} &times; 1 = {result.score_breakdown.low_count * 1} pts
                    </span>
                  </div>
                </div>

                <p className="text-xs text-stone/80 leading-relaxed">
                  <strong className="text-[#F4EFE5]">Score Rationale: </strong>
                  {result.score_breakdown.risk_rationale}
                </p>

                {result.score_breakdown.scoring_limitations && (
                  <p className="text-[11px] text-stone/60 italic border-t border-[#3B3A33]/50 pt-2">
                    <strong>Limitations: </strong>
                    {result.score_breakdown.scoring_limitations}
                  </p>
                )}
              </div>
            )}

            {/* Findings Explorer */}
            <div className="space-y-4">
              {/* Filter and Search Bar */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pb-2">
                {/* Severity Tabs */}
                <div className="inline-flex rounded-lg border border-[#3B3A33] bg-[#151716] p-1 gap-1">
                  <button
                    type="button"
                    onClick={() => setRiskFilter('ALL')}
                    className={`px-3 py-1 rounded text-xs font-semibold transition-all ${
                      riskFilter === 'ALL'
                        ? 'bg-[#B59A68] text-[#151716]'
                        : 'text-stone/70 hover:text-ivory'
                    }`}
                  >
                    All ({result.red_flags.length})
                  </button>
                  <button
                    type="button"
                    onClick={() => setRiskFilter('HIGH')}
                    className={`px-3 py-1 rounded text-xs font-semibold transition-all ${
                      riskFilter === 'HIGH'
                        ? 'bg-[#6E2634] text-[#F4EFE5]'
                        : 'text-[#E25C6F]/80 hover:text-[#E25C6F]'
                    }`}
                  >
                    High ({highCount})
                  </button>
                  <button
                    type="button"
                    onClick={() => setRiskFilter('MEDIUM')}
                    className={`px-3 py-1 rounded text-xs font-semibold transition-all ${
                      riskFilter === 'MEDIUM'
                        ? 'bg-[#B59A68]/40 text-[#D4AF37] border border-[#B59A68]/60'
                        : 'text-[#D4AF37]/80 hover:text-[#D4AF37]'
                    }`}
                  >
                    Medium ({medCount})
                  </button>
                  <button
                    type="button"
                    onClick={() => setRiskFilter('LOW')}
                    className={`px-3 py-1 rounded text-xs font-semibold transition-all ${
                      riskFilter === 'LOW'
                        ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800'
                        : 'text-emerald-400/80 hover:text-emerald-400'
                    }`}
                  >
                    Low ({lowCount})
                  </button>
                </div>

                {/* Keyword Search */}
                <div className="relative flex-1 sm:max-w-xs">
                  <Search className="w-3.5 h-3.5 text-stone/50 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search flagged clauses or laws..."
                    className="w-full bg-[#1A1C1B] border border-[#3B3A33] rounded-lg pl-8 pr-3 py-1.5 text-xs text-[#F4EFE5] placeholder:text-stone/50 focus:outline-none focus:border-[#B59A68]"
                  />
                  {searchQuery && (
                    <button
                      type="button"
                      onClick={() => setSearchQuery('')}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-xs text-stone/50 hover:text-stone"
                    >
                      &times;
                    </button>
                  )}
                </div>
              </div>

              {/* Red Flags List */}
              {result.audit_status === 'DOCUMENT_TYPE_MISMATCH' ? (
                <div className="text-center py-10 px-4 rounded-xl border border-[#3B3A33] bg-[#1A1C1B]">
                  <AlertCircle className="w-8 h-8 text-[#D4AF37] mx-auto mb-2" />
                  <h4 className="text-sm font-semibold text-[#F4EFE5]">Contract Red-Flag Audit Not Applicable</h4>
                  <p className="text-xs text-stone/70 mt-1 max-w-md mx-auto leading-relaxed">
                    This document was classified as a judicial decision or non-contract instrument. To evaluate contractual risks such as unilateral indemnities, non-compete covenants, or liability caps, please upload a commercial contract.
                  </p>
                </div>
              ) : filteredFlags.length === 0 ? (
                <div className="text-center py-12 px-4 rounded-xl border border-[#3B3A33] bg-[#1A1C1B]">
                  <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
                  <h4 className="text-sm font-semibold text-[#F4EFE5]">
                    {searchQuery ? 'No Red Flags Found in this View' : 'No Red Flags Detected in Analyzed Content'}
                  </h4>
                  <p className="text-xs text-stone/70 mt-2 max-w-lg mx-auto leading-relaxed">
                    {searchQuery
                      ? `No flagged clauses matched your search query "${searchQuery}".`
                      : 'No supported red flags were identified by the current automated analysis. The absence of findings does not establish the absence of contractual risk or guarantee statutory compliance. Formal review by a qualified Indian advocate is recommended prior to signing.'}
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredFlags.map((flag, idx) => {
                    const isExpanded = expandedCards[idx] ?? true;
                    const isHigh = flag.risk_level.toLowerCase() === 'high';
                    const isMed = flag.risk_level.toLowerCase() === 'medium';
                    const classification = flag.risk_classification || 'potential_commercial_risk';
                    const verbatim = flag.verbatim_clause || flag.clause_text;
                    const pageLocation = flag.source_page
                      ? `Page ${flag.source_page}`
                      : flag.page_ref
                      ? `Page ${flag.page_ref}`
                      : 'Document-wide / Unspecified';

                    return (
                      <div
                        key={idx}
                        className={`rounded-xl border transition-all ${
                          isHigh
                            ? 'bg-[#1C1416]/90 border-[#6E2634]/60'
                            : isMed
                            ? 'bg-[#1C1A16]/90 border-[#B59A68]/40'
                            : 'bg-[#171A18]/90 border-emerald-900/40'
                        }`}
                      >
                        {/* Header Bar */}
                        <div
                          onClick={() => toggleExpand(idx)}
                          className="p-4 sm:p-5 flex items-center justify-between gap-3 cursor-pointer select-none"
                        >
                          <div className="flex items-center gap-2.5 flex-wrap">
                            {/* Severity Pill */}
                            <span
                              className={`px-2.5 py-0.5 rounded text-[11px] font-mono font-bold uppercase tracking-wider ${
                                isHigh
                                  ? 'bg-[#6E2634] text-[#F4EFE5]'
                                  : isMed
                                  ? 'bg-[#B59A68]/30 text-[#D4AF37] border border-[#B59A68]/50'
                                  : 'bg-emerald-950/40 text-emerald-400 border border-emerald-800'
                              }`}
                            >
                              {flag.risk_level} Risk
                            </span>

                            {/* Risk Classification Badge */}
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-mono font-medium border ${
                                classification === 'potential_commercial_risk'
                                  ? 'bg-amber-950/40 text-amber-300 border-amber-800/40'
                                  : classification === 'possible_legal_concern'
                                  ? 'bg-sky-950/40 text-sky-300 border-sky-800/40'
                                  : 'bg-[#6E2634]/40 text-[#E25C6F] border-[#8A3545]/60'
                              }`}
                            >
                              {classification === 'potential_commercial_risk'
                                ? 'Potential Commercial Risk'
                                : classification === 'possible_legal_concern'
                                ? 'Possible Legal Concern'
                                : 'Legal Conclusion Requiring Review'}
                            </span>

                            {/* Title / Category */}
                            <span className="text-xs font-semibold text-[#F4EFE5]">
                              {flag.title || (flag.risk_category ? flag.risk_category.replace(/_/g, ' ') : 'Contract Finding')}
                            </span>

                            {/* Finding ID chip */}
                            {flag.finding_id && (
                              <span className="px-1.5 py-0.5 rounded text-[10px] font-mono text-stone/50 bg-[#151716] border border-[#3B3A33]">
                                {flag.finding_id}
                              </span>
                            )}

                            {/* Page Indicator */}
                            <span className="text-xs font-mono text-stone/60">
                              {pageLocation}
                              {flag.clause_location ? ` (${flag.clause_location})` : ''}
                            </span>

                            {/* Confidence Pill */}
                            {(flag.evidence_confidence !== undefined && flag.evidence_confidence !== null) ||
                            (flag.confidence !== undefined && flag.confidence !== null) ? (
                              <span className="text-[10px] font-mono text-stone/50">
                                {Math.round(((flag.evidence_confidence ?? flag.confidence) || 0) * 100)}% match
                              </span>
                            ) : null}
                          </div>

                          <div className="flex items-center gap-2">
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                copyClause(verbatim, idx);
                              }}
                              className="text-stone/60 hover:text-stone p-1 rounded hover:bg-white/[0.04] transition-colors"
                              title="Copy verbatim clause"
                            >
                              {copiedClauseIdx === idx ? (
                                <Check className="w-3.5 h-3.5 text-emerald-400" />
                              ) : (
                                <Copy className="w-3.5 h-3.5" />
                              )}
                            </button>
                            {isExpanded ? (
                              <ChevronUp className="w-4 h-4 text-stone/60" />
                            ) : (
                              <ChevronDown className="w-4 h-4 text-stone/60" />
                            )}
                          </div>
                        </div>

                        {/* Collapsible Content */}
                        <AnimatePresence>
                          {isExpanded && (
                            <motion.div
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: 'auto' }}
                              exit={{ opacity: 0, height: 0 }}
                              transition={{ duration: 0.2 }}
                              className="border-t border-[#3B3A33]/50 px-4 sm:px-5 pb-5 pt-4 space-y-4"
                            >
                              {/* Verbatim Clause Excerpt */}
                              <div>
                                <div className="flex items-center justify-between mb-1.5">
                                  <span className="text-[11px] font-mono uppercase tracking-wider text-stone/60 font-semibold">
                                    Verbatim Contract Clause
                                  </span>
                                  <button
                                    type="button"
                                    onClick={() => copyClause(verbatim, idx)}
                                    className="text-[11px] text-[#B59A68] hover:underline flex items-center gap-1"
                                  >
                                    {copiedClauseIdx === idx ? 'Copied' : 'Copy Excerpt'}
                                  </button>
                                </div>
                                <div className="p-3.5 rounded-lg bg-[#0E100F] border border-[#3B3A33] font-mono text-xs text-[#EDE8DC] leading-relaxed italic select-text">
                                  &ldquo;{verbatim}&rdquo;
                                </div>
                              </div>

                              {/* Statutory Reference & Verification Status */}
                              {flag.statutory_provision && (
                                <div className="p-3 rounded-lg bg-[#151716] border border-[#3B3A33]/80 space-y-2">
                                  <div className="flex items-center justify-between flex-wrap gap-2">
                                    <div className="flex items-center gap-2">
                                      <Scale className="w-3.5 h-3.5 text-[#B59A68]" />
                                      <span className="text-xs font-semibold text-[#EDE8DC]">
                                        {flag.statutory_provision}
                                      </span>
                                      {flag.applicable_law && (
                                        <span className="text-xs text-stone/60 font-mono">
                                          ({flag.applicable_law})
                                        </span>
                                      )}
                                    </div>
                                    <span
                                      className={`px-2 py-0.5 rounded text-[10px] font-mono border ${
                                        flag.statutory_verification_status === 'verified'
                                          ? 'bg-emerald-950/40 text-emerald-400 border-emerald-800/40'
                                          : 'bg-amber-950/40 text-amber-400 border-amber-800/40'
                                      }`}
                                    >
                                      {flag.statutory_verification_status === 'verified'
                                        ? 'Statute Verified'
                                        : 'Statute Unverified / Pending Legal Validation'}
                                    </span>
                                  </div>

                                  {flag.application_to_clause && (
                                    <p className="text-xs text-stone/80 leading-relaxed">
                                      <strong className="text-stone">Application: </strong>
                                      {flag.application_to_clause}
                                    </p>
                                  )}

                                  {flag.uncertainty_or_limitation && (
                                    <p className="text-[11px] text-stone/60 italic border-t border-[#3B3A33]/50 pt-1.5">
                                      <strong>Limitations & Context: </strong>
                                      {flag.uncertainty_or_limitation}
                                    </p>
                                  )}
                                </div>
                              )}

                              {/* Legal Exposure Reasoning & Recommendation */}
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="rounded-lg p-3.5 bg-[#151716] border border-[#3B3A33]/70">
                                  <div className="flex items-center gap-1.5 text-xs font-semibold text-[#E25C6F] mb-1.5">
                                    <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                                    <span>Statutory Risk & Legal Exposure</span>
                                  </div>
                                  <p className="text-xs text-stone/90 leading-relaxed">
                                    {flag.legal_explanation || flag.explanation}
                                  </p>
                                </div>

                                {/* Actionable Recommendation */}
                                {(flag.recommended_action || flag.recommendation) && (
                                  <div className="rounded-lg p-3.5 bg-[#151716] border border-[#B59A68]/40">
                                    <div className="flex items-center gap-1.5 text-xs font-semibold text-[#B59A68] mb-1.5">
                                      <Sparkles className="w-3.5 h-3.5 shrink-0" />
                                      <span>Recommended Action / Redline</span>
                                    </div>
                                    <p className="text-xs text-[#EDE8DC] leading-relaxed">
                                      {flag.recommended_action || flag.recommendation}
                                    </p>
                                  </div>
                                )}
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
