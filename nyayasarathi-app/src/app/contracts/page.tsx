'use client';

import { useState, useRef, useEffect, useMemo } from 'react';
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
  BookOpen,
  Info,
  SlidersHorizontal,
  Eye,
  EyeOff,
  Download,
  Flame,
  FileSignature,
} from 'lucide-react';
import { Navbar, Footer } from '@/components/layout/NavAndFooter';
import {
  analyzeContract,
  getToken,
  removeAuth,
  type ContractAnalysisResult,
  type ContractRedFlag,
} from '@/lib/auth';

// ── Realistic Preloaded Indian Legal Sample Contracts ─────────────────────────
const SAMPLE_CONTRACTS = [
  {
    id: 'sample-msa',
    title: 'Unilateral Master Services Agreement',
    badge: 'High Risk Archetype',
    badgeColor: 'text-[#E25C6F] bg-[#6E2634]/30 border-[#8A3545]/60',
    description: 'Contains uncapped indemnities, 3-year non-compete restraint (Sec 27 ICA), and asymmetric 24-hr unilateral termination.',
    fileName: 'sample_unilateral_msa.txt',
    content: `MASTER SERVICES AGREEMENT (MSA)
This Agreement is entered into on this 15th day of January, 2026 by and between:
Client Corporation India Pvt. Ltd. ("Client") and Vendor Technical Solutions LLP ("Service Provider").

1. SCOPE OF SERVICES
The Service Provider agrees to provide specialized cloud development, deployment, and ongoing legal compliance support as detailed in subsequent Statements of Work.

2. UNILATERAL TERMINATION & LOCK-IN
The Client reserves the absolute and unilateral right to terminate this Agreement or any Statement of Work at any time, with or without cause, upon twenty-four (24) hours prior written notice. The Service Provider shall be subject to a strict mandatory five (5) year lock-in period and shall possess no right to terminate this Agreement for convenience or cause prior to the expiration of said term.

3. UNLIMITED INDEMNIFICATION & CONSEQUENTIAL DAMAGES
The Service Provider shall defend, indemnify, and hold harmless the Client, its parent companies, affiliates, directors, officers, employees, and agents from and against any and all claims, demands, liabilities, penalties, forfeitures, damages (including indirect, special, punitive, exemplary, and consequential damages), and reasonable legal fees arising directly or indirectly from any act, omission, delay, or alleged breach of this Agreement. This indemnity obligation shall be completely uncapped and shall not be subject to any aggregate limitation of liability.

4. EXCLUSION OF CLIENT LIABILITY
To the fullest extent permissible by law, the Client's total aggregate liability arising out of or related to this Agreement, whether in contract, tort, or otherwise, shall be strictly capped at INR 1,000 (Indian Rupees One Thousand only).

5. COVENANT IN RESTRAINT OF TRADE (POST-TERMINATION NON-COMPETE)
The Service Provider and its key personnel agree that during the term of this Agreement and for a mandatory period of three (3) years following the termination or expiration hereof, they shall not directly or indirectly establish, advise, invest in, or provide similar software consultancy services to any competing business entity within the territory of India.

6. RESTRICTION ON LEGAL PROCEEDINGS & FORUM EXCLUSION
Any dispute or controversy arising under this Agreement shall not be submitted to Indian civil courts. The parties agree that no suit or legal proceeding may be filed by the Service Provider after ninety (90) days from the date the cause of action first arose, after which all rights and remedies shall be deemed permanently extinguished.

7. GOVERNING LAW
This Agreement shall be governed by and construed in accordance with the substantive laws of India, subject to the exclusive venue provisions herein.`,
  },
  {
    id: 'sample-nda',
    title: 'Vendor Non-Disclosure Agreement',
    badge: 'Moderate Risk Archetype',
    badgeColor: 'text-[#D4AF37] bg-[#B59A68]/20 border-[#B59A68]/40',
    description: 'Perpetual confidentiality, unilateral injunctive relief with bond waiver, and unilateral IP assignment.',
    fileName: 'sample_vendor_nda.txt',
    content: `NON-DISCLOSURE AND CONFIDENTIALITY AGREEMENT
This Non-Disclosure Agreement ("Agreement") is executed on 10th February, 2026.

1. DEFINITION OF CONFIDENTIAL INFORMATION
Confidential Information includes all non-public technical, commercial, financial, customer, and marketing data disclosed by Disclosing Party to Receiving Party, whether orally or in writing.

2. PERPETUAL CONFIDENTIALITY OBLIGATION
The obligations of confidentiality, non-use, and non-disclosure set forth herein shall survive indefinitely and shall remain binding upon Receiving Party perpetually, without any limitation of time.

3. WAIVER OF DEFENSES & AUTOMATIC INJUNCTION
In the event of any breach or threatened breach by Receiving Party, Disclosing Party shall be entitled to an immediate ex-parte injunction without the necessity of posting any bond, demonstrating irreparable injury, or proving actual monetary damages. Receiving Party irrevocably waives all rights to oppose such emergency relief.

4. IP FORFEITURE & ASSIGNMENT
All ideas, modifications, improvements, or derivative works conceived by Receiving Party during discussions or evaluation of Confidential Information shall immediately become the sole and exclusive property of Disclosing Party.`,
  },
  {
    id: 'sample-commercial-lease',
    title: 'Standard Commercial Property Lease',
    badge: 'Standard Risk Archetype',
    badgeColor: 'text-emerald-400 bg-emerald-950/40 border-emerald-800/40',
    description: '36-month lock-in, escalation clause, forfeiture of security deposit upon early exit, and arbitration clause.',
    fileName: 'sample_commercial_lease.txt',
    content: `COMMERCIAL LEASE DEED
This Lease Deed is executed on 1st March 2026 between Landlord Properties Pvt. Ltd. (Lessor) and Tech Innovations Ltd. (Lessee).

1. PREMISES & LEASE TERM
The Lessor grants on lease Office Unit No. 402, Cyber City, Bangalore for a period of five (5) years commencing April 1, 2026.

2. LOCK-IN PERIOD & SECURITY DEPOSIT FORFEITURE
Both parties agree to a mandatory lock-in period of thirty-six (36) months. In the event the Lessee vacates the premises prior to completion of the lock-in term, the entire interest-free Security Deposit equivalent to six (6) months rent shall stand absolutely forfeited to the Lessor as liquidated damages.

3. RENT ESCALATION
The monthly rent shall automatically escalate by fifteen percent (15%) upon completion of every twelve (12) months of occupancy.

4. ARBITRATION & JURISDICTION
Any dispute arising from this Deed shall be referred to a sole arbitrator appointed mutually under the Arbitration and Conciliation Act, 1996. The seat and venue of arbitration shall be Bengaluru.`,
  },
];

export default function ContractsPage() {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ContractAnalysisResult | null>(null);
  const [isAuth, setIsAuth] = useState<boolean>(true);

  // Filters, Search & View Controls
  const [riskFilter, setRiskFilter] = useState<'ALL' | 'HIGH' | 'MEDIUM' | 'LOW'>('ALL');
  const [classificationFilter, setClassificationFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedCards, setExpandedCards] = useState<Record<number, boolean>>({});
  const [allExpanded, setAllExpanded] = useState<boolean>(true);
  const [copiedClauseIdx, setCopiedClauseIdx] = useState<number | null>(null);
  const [copiedSummary, setCopiedSummary] = useState(false);
  const [copiedReport, setCopiedReport] = useState(false);
  const [activeTab, setActiveTab] = useState<'findings' | 'scorecard' | 'limitations'>('findings');

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

  const loadSampleContract = (sample: typeof SAMPLE_CONTRACTS[0]) => {
    const blob = new Blob([sample.content], { type: 'text/plain' });
    const sampleFile = new File([blob], sample.fileName, { type: 'text/plain' });
    validateAndSetFile(sampleFile);
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

    // Progress simulation stages
    const stage1 = setTimeout(() => {
      setLoadingStage('Parsing document text & performing OCR layout analysis...');
    }, 1200);

    const stage2 = setTimeout(() => {
      setLoadingStage('Auditing statutory risks against Indian Contract Act & High Court doctrines...');
    }, 3200);

    const stage3 = setTimeout(() => {
      setLoadingStage('Calculating weighted severity score & grounding clause citations...');
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
      setAllExpanded(true);
    } catch (err: any) {
      console.error('Contract analysis error:', err);
      const isAuthError =
        err.message?.toLowerCase().includes('token') ||
        err.message?.toLowerCase().includes('authentication') ||
        err.message?.toLowerCase().includes('unauthorized');
      if (isAuthError) {
        removeAuth();
        setIsAuth(false);
        setError('Your session has expired or is invalid. Please sign in to analyze contracts.');
      } else {
        setError(
          err.message || 'An error occurred while analyzing the contract. Please verify your document and retry.'
        );
      }
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
    setClassificationFilter('ALL');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const toggleExpand = (idx: number) => {
    setExpandedCards((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const toggleExpandAll = () => {
    if (!result) return;
    const newState = !allExpanded;
    setAllExpanded(newState);
    const updated: Record<number, boolean> = {};
    result.red_flags.forEach((_, idx) => {
      updated[idx] = newState;
    });
    setExpandedCards(updated);
  };

  const copyClause = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedClauseIdx(idx);
    setTimeout(() => setCopiedClauseIdx(null), 2200);
  };

  const copySummaryText = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedSummary(true);
    setTimeout(() => setCopiedSummary(false), 2200);
  };

  const copyFullReport = () => {
    if (!result) return;
    const highCount = result.red_flags.filter((rf) => rf.risk_level.toLowerCase() === 'high').length;
    const medCount = result.red_flags.filter((rf) => rf.risk_level.toLowerCase() === 'medium').length;
    const lowCount = result.red_flags.filter((rf) => rf.risk_level.toLowerCase() === 'low').length;

    const lines: string[] = [
      `# NYAYASARATHI CONTRACT RED-FLAG AUDIT REPORT`,
      `Document: ${result.filename || file?.name || 'Contract Agreement'}`,
      `Document Classification: ${result.document_type_label || result.document_type || 'Commercial Contract'}`,
      `Audit Status: ${result.audit_status || 'COMPLETED'}`,
      `Overall Risk Level: ${result.overall_risk_score.toUpperCase()}`,
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

  // Severity Counts
  const highCount = useMemo(() => {
    return result?.red_flags.filter((rf) => rf.risk_level.toLowerCase() === 'high').length ?? 0;
  }, [result]);

  const medCount = useMemo(() => {
    return result?.red_flags.filter((rf) => rf.risk_level.toLowerCase() === 'medium').length ?? 0;
  }, [result]);

  const lowCount = useMemo(() => {
    return result?.red_flags.filter((rf) => rf.risk_level.toLowerCase() === 'low').length ?? 0;
  }, [result]);

  // Filtered Flags with live search
  const filteredFlags = useMemo(() => {
    if (!result) return [];
    return result.red_flags.filter((flag) => {
      // Severity Filter
      if (riskFilter !== 'ALL' && flag.risk_level.toUpperCase() !== riskFilter) {
        return false;
      }
      // Classification Filter
      if (classificationFilter !== 'ALL' && flag.risk_classification !== classificationFilter) {
        return false;
      }
      // Search Filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const inTitle = (flag.title || '').toLowerCase().includes(q);
        const inClause = (flag.verbatim_clause || flag.clause_text || '').toLowerCase().includes(q);
        const inCat = (flag.risk_category || '').toLowerCase().includes(q);
        const inStatute = (flag.statutory_provision || '').toLowerCase().includes(q);
        const inExpl = (flag.legal_explanation || flag.explanation || '').toLowerCase().includes(q);
        const inAction = (flag.recommended_action || flag.recommendation || '').toLowerCase().includes(q);
        return inTitle || inClause || inCat || inStatute || inExpl || inAction;
      }
      return true;
    });
  }, [result, riskFilter, classificationFilter, searchQuery]);

  return (
    <div className="min-h-screen bg-[#151716] text-[#F4EFE5] flex flex-col font-sans selection:bg-[#6E2634]/40">
      <Navbar />

      {/* Main Content Area */}
      <main className="flex-1 pt-24 sm:pt-28 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        {/* Header Hero */}
        <div className="text-center max-w-3xl mx-auto mb-10">
          <h1 className="font-display text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight text-[#F4EFE5] mb-3">
            Contract Red-Flag Analyzer
          </h1>

          <p className="text-stone text-sm sm:text-base leading-relaxed">
            Audit commercial agreements, tenders, and NDAs for high-risk clauses, indemnities, and statutory compliance under the{' '}
            <span className="text-[#B59A68] font-medium">Indian Contract Act, 1872</span>.
          </p>
        </div>

        {/* Authentication Warning Banner if guest */}
        {!isAuth && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8 rounded-xl border border-[#B59A68]/40 bg-[#B59A68]/10 p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-lg backdrop-blur-sm"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#B59A68]/20 border border-[#B59A68]/40 flex items-center justify-center shrink-0">
                <Lock className="w-5 h-5 text-[#B59A68]" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-[#F4EFE5]">Authentication Required</h4>
                <p className="text-xs text-stone/90 leading-relaxed mt-0.5">
                  Contract document ingestion and clause audit are protected features. Sign in to analyze your documents or test with demo credentials.
                </p>
              </div>
            </div>
            <Link
              href="/login"
              className="shrink-0 rounded-lg px-4 py-2 text-xs font-semibold text-[#151716] bg-[#B59A68] hover:bg-[#c9af7e] transition-all shadow-md flex items-center gap-1.5"
            >
              <span>Sign In with Demo</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </motion.div>
        )}

        {/* Workspace: Upload vs Results */}
        {!result ? (
          /* Upload State */
          <div className="max-w-3xl mx-auto space-y-8">
            <div className="ink-panel rounded-2xl p-6 sm:p-8 border border-[#3B3A33] shadow-2xl relative overflow-hidden bg-gradient-to-b from-[#1E2320]/80 via-[#1A1C1B] to-[#151716]">
              {/* Subtle Ambient Radial Highlight */}
              <div className="pointer-events-none absolute -top-24 -left-24 w-72 h-72 bg-[#B59A68]/10 rounded-full blur-3xl" />
              <div className="pointer-events-none absolute -bottom-24 -right-24 w-72 h-72 bg-[#6E2634]/15 rounded-full blur-3xl" />

              <div className="flex items-center justify-between pb-4 mb-5 border-b border-[#3B3A33]">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-[#B59A68]/15 border border-[#B59A68]/30 flex items-center justify-center text-[#B59A68]">
                    <Upload className="w-4 h-4" />
                  </div>
                  <div>
                    <h2 className="font-display text-base sm:text-lg font-semibold text-[#F4EFE5]">
                      Upload Contract Document
                    </h2>
                    <p className="text-xs text-stone/80">
                      Supports digital PDF, scanned PDF (PaddleOCR), DOCX, or TXT agreements up to 25 MB.
                    </p>
                  </div>
                </div>
                {file && (
                  <span className="hidden sm:inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-mono bg-emerald-950/40 text-emerald-400 border border-emerald-800/50">
                    <CheckCircle2 className="w-3 h-3" /> Ready
                  </span>
                )}
              </div>

              {/* Drag & Drop Zone */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`relative border-2 border-dashed rounded-xl p-8 sm:p-10 text-center cursor-pointer transition-all duration-300 ${
                  isDragging
                    ? 'border-[#B59A68] bg-[#B59A68]/15 scale-[1.01]'
                    : file
                    ? 'border-[#B59A68]/70 bg-[#1D211F]/90 shadow-inner'
                    : 'border-[#3B3A33] hover:border-[#B59A68]/50 bg-[#151716]/80 hover:bg-[#1A1C1B]'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.doc,.txt"
                  onChange={handleFileChange}
                  className="hidden"
                />

                <div className="mx-auto w-14 h-14 rounded-2xl bg-[#1D211F] border border-[#3B3A33] flex items-center justify-center mb-4 text-[#B59A68] shadow-md group-hover:scale-105 transition-transform">
                  <FileText className="w-7 h-7" />
                </div>

                {file ? (
                  <div className="space-y-1">
                    <p className="text-sm font-semibold text-[#F4EFE5] truncate max-w-md mx-auto">
                      {file.name}
                    </p>
                    <p className="text-xs text-stone font-mono">
                      {(file.size / (1024 * 1024)).toFixed(2)} MB &bull; {file.name.split('.').pop()?.toUpperCase()} Document
                    </p>
                    <p className="text-xs text-[#B59A68] font-medium pt-2">
                      Click or drag a new file to replace
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-[#F4EFE5]">
                      Drag and drop your contract here, or{' '}
                      <span className="text-[#B59A68] underline decoration-[#B59A68]/40 hover:decoration-[#B59A68] font-semibold">
                        browse local files
                      </span>
                    </p>
                    <p className="text-xs text-stone/70">
                      PDF, DOCX, TXT &bull; Max 25 MB &bull; Scanned PDFs processed via high-accuracy OCR
                    </p>
                  </div>
                )}
              </div>

              {/* Error Message Banner */}
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-5 p-4 rounded-xl bg-[#6E2634]/25 border border-[#8A3545]/60 flex items-start gap-3 text-xs text-[#E25C6F]"
                >
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  <div className="flex-1 leading-relaxed">
                    <strong>Audit Notice:</strong> {error}
                    {!isAuth && (
                      <div className="mt-2">
                        <Link
                          href="/login"
                          className="inline-flex items-center gap-1 font-semibold text-[#F4EFE5] underline hover:text-[#B59A68]"
                        >
                          Sign in with a demo account &rarr;
                        </Link>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}

              {/* Action Buttons */}
              <div className="mt-6 flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-[#3B3A33]/70">
                {file ? (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setFile(null);
                      if (fileInputRef.current) fileInputRef.current.value = '';
                    }}
                    disabled={loading}
                    className="text-xs text-stone/80 hover:text-stone font-medium px-3 py-2 rounded-lg hover:bg-white/[0.04] transition-colors"
                  >
                    Clear Selected File
                  </button>
                ) : (
                  <div className="text-xs text-stone/60 italic flex items-center gap-1.5">
                    <Info className="w-3.5 h-3.5" /> No document selected yet
                  </div>
                )}

                <button
                  type="button"
                  id="analyze-contract-btn"
                  onClick={handleAnalyze}
                  disabled={!file || loading}
                  className={`flex items-center justify-center gap-2 rounded-lg px-6 py-2.5 font-sans text-sm font-semibold tracking-wide transition-all shadow-lg ${
                    !file || loading
                      ? 'bg-[#3B3A33]/40 text-stone/50 cursor-not-allowed border border-transparent'
                      : 'bg-[#6E2634] hover:bg-[#8A3545] text-[#F4EFE5] border border-[#8A3545]/80 hover:shadow-oxblood active:scale-[0.99]'
                  }`}
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-[#F4EFE5]/30 border-t-[#F4EFE5] rounded-full animate-spin" />
                      <span>Auditing Contract...</span>
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="w-4 h-4 text-[#B59A68]" />
                      <span>Analyze Red Flags</span>
                      <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
                    </>
                  )}
                </button>
              </div>

              {/* Loading progress banner */}
              {loading && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="mt-5 p-4 rounded-xl bg-[#151716] border border-[#3B3A33]"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-[#B59A68]/20 flex items-center justify-center">
                      <Scale className="w-3.5 h-3.5 text-[#B59A68] animate-bounce" />
                    </div>
                    <span className="text-xs font-mono text-[#B59A68] font-medium">{loadingStage}</span>
                  </div>
                  <div className="w-full bg-[#1D211F] rounded-full h-1.5 mt-3 overflow-hidden">
                    <div className="bg-[#B59A68] h-1.5 rounded-full w-2/3 animate-[pulse_1.5s_infinite]" />
                  </div>
                </motion.div>
              )}
            </div>

            {/* Quick Test Preloaded Sample Contracts Section */}
            <div className="ink-panel rounded-2xl p-6 border border-[#3B3A33] bg-[#1A1C1B]">
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#3B3A33]">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-[#B59A68]" />
                  <h3 className="font-display text-sm font-semibold text-[#F4EFE5]">
                    Quick Test with Preloaded Indian Contract Samples
                  </h3>
                </div>
                <span className="text-[11px] font-mono text-stone/70">1-Click Demonstration</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {SAMPLE_CONTRACTS.map((sample) => (
                  <div
                    key={sample.id}
                    onClick={() => loadSampleContract(sample)}
                    className="group rounded-xl p-4 bg-[#151716] border border-[#3B3A33] hover:border-[#B59A68]/70 hover:bg-[#1D211F] cursor-pointer transition-all duration-200 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold border ${sample.badgeColor}`}>
                          {sample.badge}
                        </span>
                        <ArrowRight className="w-3.5 h-3.5 text-stone/50 group-hover:text-[#B59A68] group-hover:translate-x-0.5 transition-all" />
                      </div>
                      <h4 className="text-xs font-semibold text-[#F4EFE5] group-hover:text-[#B59A68] transition-colors line-clamp-1">
                        {sample.title}
                      </h4>
                      <p className="text-[11px] text-stone/70 mt-1 line-clamp-3 leading-relaxed">
                        {sample.description}
                      </p>
                    </div>

                    <div className="mt-3.5 pt-2.5 border-t border-[#3B3A33]/60 flex items-center justify-between gap-2 min-w-0">
                      <div className="flex items-center gap-1.5 text-[10px] font-mono text-stone/50 truncate min-w-0">
                        <FileText className="w-3 h-3 shrink-0 text-stone/40" />
                        <span className="truncate">{sample.fileName}</span>
                      </div>
                      <span className="shrink-0 whitespace-nowrap inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-semibold text-[#151716] bg-[#B59A68] group-hover:bg-[#c9af7e] transition-all shadow-sm">
                        Load
                        <ArrowRight className="w-2.5 h-2.5" />
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* Results View Dashboard */
          <div className="space-y-6 animate-fadeIn">
            {/* Top Toolbar / Quick Actions */}
            <div className="flex flex-wrap items-center justify-between gap-4 p-4 sm:p-5 rounded-2xl bg-[#1A1C1B] border border-[#3B3A33] shadow-xl">
              <div className="flex items-center gap-3.5">
                <div className="w-10 h-10 rounded-xl bg-[#B59A68]/15 border border-[#B59A68]/30 flex items-center justify-center text-[#B59A68] shrink-0">
                  <FileCheck2 className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-sm sm:text-base font-semibold text-[#F4EFE5]">
                      {result.filename || file?.name || 'Contract Audit Brief'}
                    </h3>
                    {result.document_type_label && (
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono uppercase bg-[#B59A68]/15 text-[#D4AF37] border border-[#B59A68]/40">
                        {result.document_type_label}
                      </span>
                    )}
                    {result.classification_confidence !== undefined &&
                      result.classification_confidence !== null && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-[#151716] text-[#B59A68] border border-[#3B3A33]">
                          {Math.round(result.classification_confidence * 100)}% Conf
                        </span>
                      )}
                    {result.audit_status && (
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono uppercase border ${
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
                  <p className="text-xs text-stone/70 mt-1">
                    Processed via <span className="text-[#EDE8DC] font-medium">{result.extraction_method || 'Digital Parser'}</span> &bull;{' '}
                    {result.total_pages ? `${result.total_pages} pages audited` : 'Extracted clauses verified'}
                    {result.classification_reason ? ` &bull; ${result.classification_reason}` : ''}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 flex-wrap">
                <button
                  type="button"
                  onClick={copyFullReport}
                  className="flex items-center gap-1.5 rounded-lg border border-[#3B3A33] bg-[#151716] px-3.5 py-2 text-xs font-medium text-stone hover:text-ivory hover:border-[#B59A68]/60 transition-colors shadow-sm"
                  title="Copy formatted markdown report"
                >
                  {copiedReport ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedReport ? 'Report Copied' : 'Copy Brief'}</span>
                </button>

                <button
                  type="button"
                  onClick={handlePrint}
                  className="flex items-center gap-1.5 rounded-lg border border-[#3B3A33] bg-[#151716] px-3.5 py-2 text-xs font-medium text-stone hover:text-ivory hover:border-[#B59A68]/60 transition-colors shadow-sm"
                  title="Print or export as PDF"
                >
                  <Printer className="w-3.5 h-3.5" />
                  <span>Print / PDF</span>
                </button>

                <button
                  type="button"
                  onClick={handleReset}
                  className="flex items-center gap-1.5 rounded-lg border border-[#6E2634]/70 bg-[#6E2634]/30 px-3.5 py-2 text-xs font-semibold text-[#E25C6F] hover:bg-[#6E2634]/50 transition-colors shadow-sm"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Audit Another</span>
                </button>
              </div>
            </div>

            {/* Document Mismatch Dedicated Notification Banner */}
            {result.audit_status === 'DOCUMENT_TYPE_MISMATCH' && (
              <div className="rounded-2xl border border-[#B59A68]/50 bg-[#B59A68]/10 p-6 space-y-4">
                <div className="flex items-start gap-3.5">
                  <div className="w-10 h-10 rounded-xl bg-[#B59A68]/20 flex items-center justify-center shrink-0 text-[#D4AF37]">
                    <AlertCircle className="w-5 h-5" />
                  </div>
                  <div className="flex-1 space-y-1">
                    <h4 className="text-sm font-semibold text-[#F4EFE5]">
                      Document Type Mismatch: {result.document_type_label || 'Non-Contract Document'}
                    </h4>
                    <p className="text-xs text-stone/90 leading-relaxed">
                      {result.summary}
                    </p>
                    {result.recommended_action && (
                      <p className="text-xs text-[#D4AF37] font-medium pt-1">
                        <strong>Recommended Next Step:</strong> {result.recommended_action}
                      </p>
                    )}
                  </div>
                </div>
                <div className="pt-3 flex flex-wrap gap-2.5 border-t border-[#B59A68]/20">
                  <Link
                    href="/legal-research"
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium bg-[#1A1C1B] text-[#D4AF37] border border-[#B59A68]/40 hover:bg-[#B59A68]/20 transition-colors"
                  >
                    <Scale className="w-3.5 h-3.5" />
                    <span>Search Precedents in Legal Research</span>
                  </Link>
                  <Link
                    href="/predictor"
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium bg-[#1A1C1B] text-[#D4AF37] border border-[#B59A68]/40 hover:bg-[#B59A68]/20 transition-colors"
                  >
                    <Scale className="w-3.5 h-3.5" />
                    <span>Open Case Predictor</span>
                  </Link>
                  <button
                    type="button"
                    onClick={handleReset}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium bg-[#6E2634]/30 text-[#E25C6F] border border-[#8A3545]/50 hover:bg-[#6E2634]/50 transition-colors"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Upload a Commercial Contract</span>
                  </button>
                </div>
              </div>
            )}

            {/* Risk Assessment Summary Cards */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
              {/* Overall Risk Profile Card */}
              {result.audit_status === 'DOCUMENT_TYPE_MISMATCH' || result.overall_risk_score.toLowerCase() === 'not assessed' ? (
                <div className="lg:col-span-4 rounded-2xl p-6 border bg-[#6E2634]/15 border-[#8A3545]/50 flex flex-col justify-between">
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
                      Document is identified as a {result.document_type_label || 'non-contract legal instrument'}. Commercial contract risk profiling is not applicable to court rulings or judgments.
                    </p>
                  </div>
                  <div className="mt-6 pt-4 border-t border-white/[0.08] text-center">
                    <span className="inline-block text-[11px] font-mono text-[#D4AF37] bg-[#B59A68]/15 px-3 py-1 rounded-full border border-[#B59A68]/30">
                      0 Contract Findings Evaluated
                    </span>
                  </div>
                </div>
              ) : (
                <div
                  className={`lg:col-span-4 rounded-2xl p-6 border flex flex-col justify-between shadow-xl ${
                    result.overall_risk_score.toLowerCase() === 'high'
                      ? 'bg-gradient-to-b from-[#6E2634]/25 to-[#1A1C1B] border-[#6E2634]/80 shadow-oxblood'
                      : result.overall_risk_score.toLowerCase() === 'medium'
                      ? 'bg-gradient-to-b from-[#B59A68]/20 to-[#1A1C1B] border-[#B59A68]/70 shadow-brass'
                      : 'bg-gradient-to-b from-emerald-950/30 to-[#1A1C1B] border-emerald-800/70'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs uppercase font-mono tracking-wider text-stone font-bold">
                        Overall Risk Profile
                      </span>
                      {result.overall_risk_score.toLowerCase() === 'high' ? (
                        <ShieldAlert className="w-6 h-6 text-[#E25C6F]" />
                      ) : result.overall_risk_score.toLowerCase() === 'medium' ? (
                        <AlertTriangle className="w-6 h-6 text-[#D4AF37]" />
                      ) : (
                        <ShieldCheck className="w-6 h-6 text-emerald-400" />
                      )}
                    </div>

                    <div className="flex items-baseline gap-2.5 mt-1">
                      <div
                        className={`font-display text-3xl sm:text-4xl font-bold tracking-tight ${
                          result.overall_risk_score.toLowerCase() === 'high'
                            ? 'text-[#E25C6F]'
                            : result.overall_risk_score.toLowerCase() === 'medium'
                            ? 'text-[#D4AF37]'
                            : 'text-emerald-400'
                        }`}
                      >
                        {result.overall_risk_score.toUpperCase()}
                      </div>
                      {result.score_breakdown && (
                        <span className="text-xs font-mono font-semibold px-2.5 py-1 rounded-lg bg-white/[0.08] border border-white/10 text-[#F4EFE5]">
                          {result.score_breakdown.numerical_score} pts
                        </span>
                      )}
                    </div>

                    <p className="mt-3 text-xs text-stone/90 leading-relaxed">
                      {result.overall_risk_score.toLowerCase() === 'high'
                        ? 'Critical contractual imbalances detected. Significant indemnification, uncapped liability, or unilateral covenants require formal legal redlining.'
                        : result.overall_risk_score.toLowerCase() === 'medium'
                        ? 'Moderate exposure identified. Terms contain ambiguous payment, renewal, or dispute resolution mechanisms warranting review.'
                        : 'Standard contractual terms identified with low statutory exposure.'}
                    </p>
                  </div>

                  {/* Severity Breakdown Bar */}
                  <div className="mt-6 pt-4 border-t border-white/[0.08] grid grid-cols-3 gap-2.5 text-center">
                    <div className="bg-[#6E2634]/30 rounded-xl p-2.5 border border-[#6E2634]/50">
                      <span className="block text-sm font-mono text-[#E25C6F] font-bold">{highCount}</span>
                      <span className="text-[10px] text-stone/80 uppercase font-medium">High (5pt)</span>
                    </div>
                    <div className="bg-[#B59A68]/20 rounded-xl p-2.5 border border-[#B59A68]/40">
                      <span className="block text-sm font-mono text-[#D4AF37] font-bold">{medCount}</span>
                      <span className="text-[10px] text-stone/80 uppercase font-medium">Med (3pt)</span>
                    </div>
                    <div className="bg-emerald-950/35 rounded-xl p-2.5 border border-emerald-800/40">
                      <span className="block text-sm font-mono text-emerald-400 font-bold">{lowCount}</span>
                      <span className="text-[10px] text-stone/80 uppercase font-medium">Low (1pt)</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Executive Summary Card */}
              <div className="lg:col-span-8 rounded-2xl p-6 bg-[#1A1C1B] border border-[#3B3A33] flex flex-col justify-between shadow-xl">
                <div>
                  <div className="flex items-center justify-between mb-3 pb-2 border-b border-[#3B3A33]/70">
                    <h3 className="font-display text-base font-semibold text-[#F4EFE5] flex items-center gap-2">
                      <FileText className="w-4 h-4 text-[#B59A68]" />
                      Executive Legal Summary
                    </h3>
                    <button
                      type="button"
                      onClick={() => copySummaryText(result.summary || '')}
                      className="text-xs text-stone/80 hover:text-stone flex items-center gap-1.5 transition-colors px-2 py-1 rounded bg-[#151716] border border-[#3B3A33]"
                    >
                      {copiedSummary ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copiedSummary ? 'Copied' : 'Copy Summary'}</span>
                    </button>
                  </div>
                  <p className="text-xs sm:text-sm text-[#EDE8DC] leading-relaxed">
                    {result.summary || 'Statutory analysis completed across all extracted clauses.'}
                  </p>
                </div>

                {/* Audit Limitations Banner if any */}
                {result.limitations && result.limitations.length > 0 && (
                  <div className="mt-5 pt-3 border-t border-[#3B3A33]/80">
                    <span className="text-[11px] font-mono font-bold text-[#B59A68] uppercase block mb-1">
                      Audit Notes & Verification Limitations:
                    </span>
                    <ul className="text-xs text-stone/70 space-y-1 list-disc list-inside">
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
              <div className="rounded-2xl p-5 sm:p-6 bg-[#1A1C1B] border border-[#3B3A33] space-y-3.5 shadow-xl">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#3B3A33]/70 pb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-[#B59A68]/15 border border-[#B59A68]/30 flex items-center justify-center text-[#B59A68]">
                      <Scale className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-xs sm:text-sm font-semibold text-[#F4EFE5] flex items-center gap-2">
                        <span>Deterministic Risk Scoring Calculation</span>
                        <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-[#B59A68]/15 text-[#D4AF37] border border-[#B59A68]/30">
                          {result.score_breakdown.numerical_score} Points Total
                        </span>
                      </h4>
                      <p className="text-[11px] font-mono text-stone/60 mt-0.5">
                        Weighted Severity Model: {result.score_breakdown.scoring_method}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-xs font-mono flex-wrap">
                    <span className="text-[#E25C6F] bg-[#6E2634]/20 border border-[#6E2634]/40 px-2.5 py-1 rounded-lg">
                      High: {result.score_breakdown.high_count} &times; 5 = {result.score_breakdown.high_count * 5} pts
                    </span>
                    <span className="text-[#D4AF37] bg-[#B59A68]/20 border border-[#B59A68]/40 px-2.5 py-1 rounded-lg">
                      Med: {result.score_breakdown.medium_count} &times; 3 = {result.score_breakdown.medium_count * 3} pts
                    </span>
                    <span className="text-emerald-400 bg-emerald-950/30 border border-emerald-800/40 px-2.5 py-1 rounded-lg">
                      Low: {result.score_breakdown.low_count} &times; 1 = {result.score_breakdown.low_count * 1} pts
                    </span>
                  </div>
                </div>

                <p className="text-xs text-stone/90 leading-relaxed">
                  <strong className="text-[#F4EFE5]">Score Rationale: </strong>
                  {result.score_breakdown.risk_rationale}
                </p>

                {result.score_breakdown.scoring_limitations && (
                  <p className="text-[11px] text-stone/60 italic border-t border-[#3B3A33]/50 pt-2">
                    <strong>Statutory Scope: </strong>
                    {result.score_breakdown.scoring_limitations}
                  </p>
                )}
              </div>
            )}

            {/* Findings Explorer Workspace */}
            <div className="space-y-4 pt-2">
              {/* Filter and Search Bar */}
              <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3 p-4 rounded-2xl bg-[#1A1C1B] border border-[#3B3A33]">
                {/* Severity Tabs */}
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="text-xs text-stone/60 font-mono mr-1 hidden sm:inline">Severity:</span>
                  <button
                    type="button"
                    onClick={() => setRiskFilter('ALL')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      riskFilter === 'ALL'
                        ? 'bg-[#B59A68] text-[#151716] shadow-sm'
                        : 'bg-[#151716] text-stone/80 hover:text-ivory border border-[#3B3A33]'
                    }`}
                  >
                    All ({result.red_flags.length})
                  </button>
                  <button
                    type="button"
                    onClick={() => setRiskFilter('HIGH')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      riskFilter === 'HIGH'
                        ? 'bg-[#6E2634] text-[#F4EFE5] shadow-sm'
                        : 'bg-[#151716] text-[#E25C6F]/80 hover:text-[#E25C6F] border border-[#3B3A33]'
                    }`}
                  >
                    High ({highCount})
                  </button>
                  <button
                    type="button"
                    onClick={() => setRiskFilter('MEDIUM')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      riskFilter === 'MEDIUM'
                        ? 'bg-[#B59A68]/35 text-[#D4AF37] border border-[#B59A68]/60 shadow-sm'
                        : 'bg-[#151716] text-[#D4AF37]/80 hover:text-[#D4AF37] border border-[#3B3A33]'
                    }`}
                  >
                    Medium ({medCount})
                  </button>
                  <button
                    type="button"
                    onClick={() => setRiskFilter('LOW')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      riskFilter === 'LOW'
                        ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800 shadow-sm'
                        : 'bg-[#151716] text-emerald-400/80 hover:text-emerald-400 border border-[#3B3A33]'
                    }`}
                  >
                    Low ({lowCount})
                  </button>
                </div>

                {/* Search & View Controls */}
                <div className="flex items-center gap-2 flex-1 sm:flex-initial">
                  {/* Keyword Search */}
                  <div className="relative flex-1 sm:w-64">
                    <Search className="w-3.5 h-3.5 text-stone/50 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Filter clauses or statutes..."
                      className="w-full bg-[#151716] border border-[#3B3A33] rounded-lg pl-8 pr-7 py-1.5 text-xs text-[#F4EFE5] placeholder:text-stone/50 focus:outline-none focus:border-[#B59A68]"
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

                  {/* Expand/Collapse All */}
                  <button
                    type="button"
                    onClick={toggleExpandAll}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#151716] border border-[#3B3A33] text-xs font-medium text-stone hover:text-ivory transition-colors whitespace-nowrap"
                    title={allExpanded ? 'Collapse All Cards' : 'Expand All Cards'}
                  >
                    {allExpanded ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    <span className="hidden sm:inline">{allExpanded ? 'Collapse All' : 'Expand All'}</span>
                  </button>
                </div>
              </div>

              {/* Red Flags List Cards */}
              {result.audit_status === 'DOCUMENT_TYPE_MISMATCH' ? (
                <div className="text-center py-12 px-4 rounded-2xl border border-[#3B3A33] bg-[#1A1C1B]">
                  <AlertCircle className="w-9 h-9 text-[#D4AF37] mx-auto mb-2.5" />
                  <h4 className="text-sm font-semibold text-[#F4EFE5]">Contract Red-Flag Audit Not Applicable</h4>
                  <p className="text-xs text-stone/70 mt-1 max-w-md mx-auto leading-relaxed">
                    This document was classified as a judicial decision or non-contract instrument. To evaluate contractual risks such as unilateral indemnities, non-compete covenants, or liability caps, please upload a commercial contract.
                  </p>
                </div>
              ) : filteredFlags.length === 0 ? (
                <div className="text-center py-14 px-4 rounded-2xl border border-[#3B3A33] bg-[#1A1C1B]">
                  <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto mb-3" />
                  <h4 className="text-sm font-semibold text-[#F4EFE5]">
                    {searchQuery ? 'No Red Flags Found in this View' : 'No Supported Red Flags Detected in Analyzed Content'}
                  </h4>
                  <p className="text-xs text-stone/70 mt-2 max-w-lg mx-auto leading-relaxed">
                    {searchQuery
                      ? `No flagged clauses matched your search query "${searchQuery}".`
                      : 'No statutory red flags were identified by the automated analysis. The absence of findings does not guarantee full statutory compliance; formal review by a qualified Indian advocate is recommended prior to contract execution.'}
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
                      : 'Document-wide';

                    return (
                      <div
                        key={idx}
                        className={`rounded-2xl border transition-all duration-200 overflow-hidden shadow-lg ${
                          isHigh
                            ? 'bg-[#1C1517] border-[#6E2634]/70 hover:border-[#8A3545]'
                            : isMed
                            ? 'bg-[#1B1916] border-[#B59A68]/50 hover:border-[#B59A68]'
                            : 'bg-[#161917] border-emerald-900/50 hover:border-emerald-700'
                        }`}
                      >
                        {/* Header Bar */}
                        <div
                          onClick={() => toggleExpand(idx)}
                          className="p-4 sm:p-5 flex items-center justify-between gap-3 cursor-pointer select-none hover:bg-white/[0.02] transition-colors"
                        >
                          <div className="flex items-center gap-2 sm:gap-2.5 flex-wrap">
                            {/* Severity Pill */}
                            <span
                              className={`px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold uppercase tracking-wider ${
                                isHigh
                                  ? 'bg-[#6E2634] text-[#F4EFE5] shadow-sm'
                                  : isMed
                                  ? 'bg-[#B59A68]/25 text-[#D4AF37] border border-[#B59A68]/50'
                                  : 'bg-emerald-950/50 text-emerald-400 border border-emerald-800'
                              }`}
                            >
                              {flag.risk_level} Risk
                            </span>

                            {/* Risk Classification Badge */}
                            <span
                              className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-medium border ${
                                classification === 'potential_commercial_risk'
                                  ? 'bg-amber-950/40 text-amber-300 border-amber-800/40'
                                  : classification === 'possible_legal_concern'
                                  ? 'bg-sky-950/40 text-sky-300 border-sky-800/40'
                                  : 'bg-[#6E2634]/35 text-[#E25C6F] border-[#8A3545]/60'
                              }`}
                            >
                              {classification === 'potential_commercial_risk'
                                ? 'Potential Commercial Risk'
                                : classification === 'possible_legal_concern'
                                ? 'Possible Legal Concern'
                                : 'Legal Conclusion Requiring Review'}
                            </span>

                            {/* Title / Category */}
                            <span className="text-xs sm:text-sm font-semibold text-[#F4EFE5]">
                              {flag.title || (flag.risk_category ? flag.risk_category.replace(/_/g, ' ') : 'Contract Finding')}
                            </span>

                            {/* Finding ID chip */}
                            {flag.finding_id && (
                              <span className="px-1.5 py-0.5 rounded text-[10px] font-mono text-stone/60 bg-[#151716] border border-[#3B3A33]">
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
                              <span className="text-[10px] font-mono text-stone/50 hidden sm:inline">
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
                              className="text-stone/60 hover:text-[#B59A68] p-1.5 rounded-lg hover:bg-white/[0.04] transition-colors"
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
                              className="border-t border-[#3B3A33]/50 px-4 sm:px-6 pb-6 pt-4 space-y-4 bg-[#151716]/60"
                            >
                              {/* Verbatim Clause Excerpt */}
                              <div>
                                <div className="flex items-center justify-between mb-2">
                                  <span className="text-[11px] font-mono uppercase tracking-wider text-stone/70 font-semibold flex items-center gap-1.5">
                                    <FileSignature className="w-3.5 h-3.5 text-[#B59A68]" />
                                    Verbatim Contract Clause
                                  </span>
                                  <button
                                    type="button"
                                    onClick={() => copyClause(verbatim, idx)}
                                    className="text-[11px] text-[#B59A68] hover:underline flex items-center gap-1 font-medium"
                                  >
                                    {copiedClauseIdx === idx ? 'Copied' : 'Copy Excerpt'}
                                  </button>
                                </div>
                                <div className="p-4 rounded-xl bg-[#0D0F0E] border border-[#3B3A33] font-mono text-xs text-[#EDE8DC] leading-relaxed italic select-text shadow-inner">
                                  &ldquo;{verbatim}&rdquo;
                                </div>
                              </div>

                              {/* Statutory Reference & Verification Status */}
                              {flag.statutory_provision && (
                                <div className="p-4 rounded-xl bg-[#1A1C1B] border border-[#3B3A33]/80 space-y-2">
                                  <div className="flex items-center justify-between flex-wrap gap-2">
                                    <div className="flex items-center gap-2">
                                      <Scale className="w-4 h-4 text-[#B59A68]" />
                                      <span className="text-xs sm:text-sm font-semibold text-[#EDE8DC]">
                                        {flag.statutory_provision}
                                      </span>
                                      {flag.applicable_law && (
                                        <span className="text-xs text-stone/70 font-mono">
                                          ({flag.applicable_law})
                                        </span>
                                      )}
                                    </div>
                                    <span
                                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono border ${
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
                                    <p className="text-xs text-stone/90 leading-relaxed">
                                      <strong className="text-[#F4EFE5]">Statutory Application: </strong>
                                      {flag.application_to_clause}
                                    </p>
                                  )}

                                  {flag.uncertainty_or_limitation && (
                                    <p className="text-[11px] text-stone/70 italic border-t border-[#3B3A33]/50 pt-2">
                                      <strong>Limitations & Context: </strong>
                                      {flag.uncertainty_or_limitation}
                                    </p>
                                  )}
                                </div>
                              )}

                              {/* Legal Exposure Reasoning & Actionable Recommendation */}
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="rounded-xl p-4 bg-[#1A1C1B] border border-[#6E2634]/40">
                                  <div className="flex items-center gap-2 text-xs font-semibold text-[#E25C6F] mb-2">
                                    <AlertCircle className="w-4 h-4 shrink-0" />
                                    <span>Statutory Risk & Legal Exposure</span>
                                  </div>
                                  <p className="text-xs text-stone/90 leading-relaxed">
                                    {flag.legal_explanation || flag.explanation}
                                  </p>
                                </div>

                                {/* Actionable Recommendation */}
                                {(flag.recommended_action || flag.recommendation) && (
                                  <div className="rounded-xl p-4 bg-[#1A1C1B] border border-[#B59A68]/50">
                                    <div className="flex items-center gap-2 text-xs font-semibold text-[#B59A68] mb-2">
                                      <CheckCircle2 className="w-4 h-4 shrink-0 text-[#B59A68]" />
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
