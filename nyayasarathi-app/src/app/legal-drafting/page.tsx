'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Scale,
  FileText,
  Copy,
  Check,
  RotateCcw,
  Download,
  Globe,
  Languages,
  AlertTriangle,
  ShieldAlert,
  Info,
  Calendar,
  Layers,
  Edit3,
  RefreshCw,
  Plus,
  X,
  AlertCircle,
  Sparkles,
  ArrowRight,
  ShieldCheck
} from 'lucide-react';
import { Navbar, Footer } from '@/components/layout/NavAndFooter';
import { API_BASE_URL } from '@/lib/config';
import { getAuthHeaders } from '@/lib/auth';

interface DraftSection {
  id: string;
  title: string;
  content: string;
  order: number;
}

interface CitationInfo {
  source_id?: string;
  title: string;
  citation: string;
  court?: string;
  decision_date?: string;
  source_url?: string;
  excerpt: string;
  is_verified: boolean;
  verification_status: string;
  authority_type: string;
  relevant_statement?: string;
}

interface DraftContent {
  title: string;
  sections: DraftSection[];
  full_text: string;
}

interface DraftResponseData {
  draft_id: string;
  document_type: string;
  language: string;
  status: string;
  draft: DraftContent;
  citations: CitationInfo[];
  warnings: string[];
  missing_information: string[];
  created_at: string;
  draft_text?: string;
  translated_text?: string;
  citations_used?: string[];
}

const DOCUMENT_TYPES = [
  {
    id: 'legal_notice',
    name: 'Legal Notice',
    badge: 'Pre-Litigation',
    desc: 'Formal demand notice under Section 138 NI Act, Section 80 CPC, or breach of contract.',
    icon: FileText
  },
  {
    id: 'bail_application',
    name: 'Bail Application',
    badge: 'Criminal Defense',
    desc: 'Regular or anticipatory bail under S. 437/439 CrPC or S. 480/483 BNSS with personal liberty grounds.',
    icon: Scale
  },
  {
    id: 'petition',
    name: 'Writ / Petition',
    badge: 'Constitutional / Civil',
    desc: 'High Court Article 226 or Section 482 CrPC / 528 BNSS petition with chronology, grounds, and prayer.',
    icon: Layers
  },
  {
    id: 'reply',
    name: 'Reply / Written Statement',
    badge: 'Responsive Pleading',
    desc: 'Defense reply to legal notice or written statement with preliminary objections and para-wise denials.',
    icon: Edit3
  }
];

const CASE_CATEGORIES = [
  'Civil & Property',
  'Commercial & Contracts',
  'Criminal & Bail',
  'Constitutional & Writs',
  'Matrimonial & Family',
  'Labor & Employment',
  'Banking & Debt Recovery',
  'Consumer Protection'
];

const SUPPORTED_LANGUAGES = [
  { code: 'en', label: 'English', native: 'English', flag: '🇬🇧' },
  { code: 'hi', label: 'Hindi', native: 'हिंदी', flag: '🇮🇳' },
  { code: 'mr', label: 'Marathi', native: 'मराठी', flag: '🇮🇳' }
];

const DRAFTING_SAMPLES = [
  {
    title: 'S. 138 NI Act Cheque Dishonour Notice',
    docType: 'legal_notice',
    category: 'Commercial & Contracts',
    jurisdiction: 'Chief Judicial Magistrate, Mumbai',
    senderName: 'Apex Logistics Pvt. Ltd.',
    senderDetails: 'Regd. Office: Nariman Point, Mumbai',
    recipientName: 'Vikas Trading Corporation',
    recipientDetails: 'Proprietor Mr. Vikas Mehta, Andheri East, Mumbai',
    noticePeriod: '15 Days',
    causeOfActionDate: '10 October 2024',
    applicableSections: 'Section 138 of Negotiable Instruments Act, 1881',
    requestedRelief: 'Demand payment of Rs. 18,50,000 within 15 days failing which criminal proceedings will be initiated.',
    facts: 'The client supplied commercial cargo goods worth Rs. 18,50,000 under Invoice No. AL/2024/889 dated 15.08.2024. In discharge of this legally enforceable debt, the addressee issued Cheque No. 441029 dated 01.10.2024 drawn on HDFC Bank. Upon presentation on 10.10.2024, the cheque was returned dishonoured with the remark "Funds Insufficient" as evidenced by the bank return memo dated 11.10.2024. Despite repeated oral requests, the outstanding amount remains unpaid.',
    dates: ['15.08.2024 - Goods delivered under invoice AL/2024/889', '01.10.2024 - Cheque No. 441029 issued', '10.10.2024 - Cheque presented for clearing', '11.10.2024 - Bank return memo: Funds Insufficient']
  },
  {
    title: 'Anticipatory Bail Application (S. 438 CrPC / 482 BNSS)',
    docType: 'bail_application',
    category: 'Criminal & Bail',
    jurisdiction: 'Sessions Court, Greater Mumbai',
    senderName: 'Sanjay Deshmukh',
    senderDetails: 'Age 42 years, Resident of Dadar, Mumbai',
    recipientName: 'State of Maharashtra',
    recipientDetails: 'Through Dadar Police Station',
    noticePeriod: 'Immediate',
    causeOfActionDate: '05 October 2024',
    applicableSections: 'Section 438 CrPC / Section 482 BNSS, Section 420, 406 IPC / BNS',
    requestedRelief: 'Grant of anticipatory bail in the event of arrest on reasonable bail bonds.',
    facts: 'The applicant is an IT consultant with clean antecedents and a reputed family background. An FIR No. 340/2024 was registered on 05.10.2024 alleging offenses under Sections 406 and 420 of IPC arising out of a purely civil contractual disagreement over software development deliverables. The applicant has cooperated fully with the investigating agency and there is no risk of flight, tampering with evidence, or influencing witnesses.',
    dates: ['01.03.2024 - Service agreement executed', '05.10.2024 - FIR registered at Dadar Police Station', '12.10.2024 - Notice under Section 41A received']
  },
  {
    title: 'Section 80 CPC Notice to Government Authority',
    docType: 'legal_notice',
    category: 'Civil & Property',
    jurisdiction: 'Civil Judge Senior Division, Pune',
    senderName: 'Sunita Patil & Others',
    senderDetails: 'Landowners, Survey No. 45/2, Haveli, Pune',
    recipientName: 'State of Maharashtra & District Collector',
    recipientDetails: 'Collector Office, Pune District',
    noticePeriod: '60 Days',
    causeOfActionDate: '01 September 2024',
    applicableSections: 'Section 80 Code of Civil Procedure, 1908, Right to Fair Compensation in Land Acquisition Act',
    requestedRelief: 'Immediate disbursement of statutory compensation with 12% interest as per statutory award.',
    facts: 'The noticees acquired land belonging to the clients measuring 2.5 Hectares at Village Haveli for public road widening project without passing a final compensation award under the 2013 Act or releasing mandatory solatium. Continuous representations since January 2024 have remained unaddressed by the revenue authorities.',
    dates: ['14.01.2024 - Preliminary acquisition notification', '01.09.2024 - Physical possession taken without compensation disbursement']
  }
];

export default function LegalDraftingPage() {
  // Client mount state to prevent hydration errors from browser autofill extensions (e.g. fdprocessedid)
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const loadSample = (sample: typeof DRAFTING_SAMPLES[0]) => {
    setDocType(sample.docType);
    setCategory(sample.category);
    setJurisdiction(sample.jurisdiction);
    setCaseTitle(sample.title);
    setSenderName(sample.senderName);
    setSenderDetails(sample.senderDetails);
    setRecipientName(sample.recipientName);
    setRecipientDetails(sample.recipientDetails);
    setNoticePeriod(sample.noticePeriod);
    setCauseOfActionDate(sample.causeOfActionDate);
    setApplicableSections(sample.applicableSections);
    setRequestedRelief(sample.requestedRelief);
    setFacts(sample.facts);
    setDatesList(sample.dates);
    setGenError(null);
  };

  // Step 1: Configuration
  const [docType, setDocType] = useState('legal_notice');
  const [category, setCategory] = useState('Commercial & Contracts');
  const [jurisdiction, setJurisdiction] = useState('');
  const [targetLanguage, setTargetLanguage] = useState('en');

  // Step 2: Case Information
  const [caseTitle, setCaseTitle] = useState('');
  const [senderName, setSenderName] = useState('');
  const [senderDetails, setSenderDetails] = useState('');
  const [recipientName, setRecipientName] = useState('');
  const [recipientDetails, setRecipientDetails] = useState('');
  const [facts, setFacts] = useState('');
  const [requestedRelief, setRequestedRelief] = useState('');
  const [applicableSections, setApplicableSections] = useState('');

  // Statutory Notice Period & Cause of Action Date
  const [noticePeriod, setNoticePeriod] = useState('15 Days');
  const [causeOfActionDate, setCauseOfActionDate] = useState('');

  // Issuing Advocate / Counsel Details
  const [advocateName, setAdvocateName] = useState('');
  const [advocateEnrollment, setAdvocateEnrollment] = useState('');
  const [advocateChambers, setAdvocateChambers] = useState('');
  const [advocateContact, setAdvocateContact] = useState('');
  
  // Important Dates list
  const [datesList, setDatesList] = useState<string[]>([]);
  const [newDateInput, setNewDateInput] = useState('');

  // Citation control
  const [includeCitations, setIncludeCitations] = useState(true);

  // Generation State
  const [isGenerating, setIsGenerating] = useState(false);
  const [progressMsg, setProgressMsg] = useState('');
  const [genError, setGenError] = useState<string | null>(null);

  // Draft Result & Versions
  const [currentResult, setCurrentResult] = useState<DraftResponseData | null>(null);
  const [originalDraft, setOriginalDraft] = useState<DraftContent | null>(null);

  // Editor State for Single Unified Legal Draft
  const [editedFullText, setEditedFullText] = useState<string>('');
  const [isDirty, setIsDirty] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);

  // Export State
  const [isExportingPdf, setIsExportingPdf] = useState(false);
  const [isExportingDocx, setIsExportingDocx] = useState(false);

  // Handle unsaved changes warning before unload
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
        e.returnValue = 'You have unsaved changes in your legal draft. Are you sure you want to exit?';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isDirty]);

  // Date management
  const handleAddDate = () => {
    if (newDateInput.trim() && !datesList.includes(newDateInput.trim())) {
      setDatesList([...datesList, newDateInput.trim()]);
      setNewDateInput('');
    }
  };

  const handleRemoveDate = (index: number) => {
    setDatesList(datesList.filter((_, i) => i !== index));
  };

  // ── GENERATE DRAFT ──────────────────────────────────────────────────────────
  const handleGenerateDraft = async () => {
    if (!facts.trim() || facts.trim().length < 10) {
      setGenError('Please provide case facts of at least 10 characters.');
      return;
    }

    // Pre-submission date validation
    if (causeOfActionDate) {
      const coaDate = new Date(causeOfActionDate);
      const today = new Date();
      if (!isNaN(coaDate.getTime()) && coaDate > today) {
        setGenError('Contradictory Date: Cause of action or incident date cannot be set in the future.');
        return;
      }
    }

    setGenError(null);
    setIsGenerating(true);
    setProgressMsg('Analyzing case chronology and temporal era (IPC vs BNS)...');

    const progressTimer = setTimeout(() => {
      setProgressMsg('Retrieving verified statutory authorities & court judgments...');
    }, 1400);

    const progressTimer2 = setTimeout(() => {
      setProgressMsg('Synthesizing structured legal sections & applying citation tags...');
    }, 2800);

    const parsedSections = applicableSections
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);

    const payload = {
      document_type: docType,
      case_category: category,
      jurisdiction: jurisdiction.trim() || undefined,
      target_language: targetLanguage,
      include_citations: includeCitations,
      case_title: caseTitle.trim() || undefined,
      parties: {
        applicant: senderName.trim()
          ? `${senderName.trim()}${senderDetails ? ` (${senderDetails.trim()})` : ''}`
          : undefined,
        respondent: recipientName.trim()
          ? `${recipientName.trim()}${recipientDetails ? ` (${recipientDetails.trim()})` : ''}`
          : undefined,
      },
      advocate_details: advocateName.trim() ? {
        name: advocateName.trim(),
        enrollment_number: advocateEnrollment.trim() || undefined,
        chambers_address: advocateChambers.trim() || undefined,
        contact: advocateContact.trim() || undefined,
      } : undefined,
      notice_period_days: noticePeriod.trim() || undefined,
      cause_of_action_date: causeOfActionDate.trim() || undefined,
      important_dates: datesList,
      facts: facts.trim(),
      requested_relief: requestedRelief.trim() || undefined,
      applicable_sections: parsedSections.length > 0 ? parsedSections : undefined,
    };

    try {
      const res = await fetch(`${API_BASE_URL}/api/drafts/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || data.detail || 'Draft generation failed.');
      }

      setCurrentResult(data);
      setOriginalDraft(data.draft);

      const fullText = data.draft.full_text || data.draft.sections?.[0]?.content || '';
      setEditedFullText(fullText);
      setIsDirty(false);
    } catch (err: any) {
      setGenError(err.message || 'An unexpected error occurred while generating the draft.');
    } finally {
      clearTimeout(progressTimer);
      clearTimeout(progressTimer2);
      setIsGenerating(false);
      setProgressMsg('');
    }
  };

  // Full Draft Content Edit
  const handleFullTextChange = (newText: string) => {
    setEditedFullText(newText);
    setIsDirty(true);
  };

  const handleResetToOriginal = () => {
    if (originalDraft) {
      setEditedFullText(originalDraft.full_text || originalDraft.sections?.[0]?.content || '');
      setIsDirty(false);
    }
  };

  // Copy Draft
  const handleCopyDraft = async () => {
    if (!currentResult) return;
    const textToCopy = editedFullText || currentResult.draft.full_text || currentResult.draft.sections?.[0]?.content || '';
    if (!textToCopy) return;

    try {
      await navigator.clipboard.writeText(
        `NYAYASARATHI LEGAL DRAFT: ${currentResult.draft.title}\n\n${textToCopy}\n\n[CONFIDENTIAL & PRIVILEGED — DRAFT GENERATED FOR ADVOCATE REVIEW]`
      );
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2500);
    } catch (err) {
      console.error('Failed to copy', err);
    }
  };

  // PDF Export
  const handleExportPdf = async () => {
    if (!currentResult) return;
    setIsExportingPdf(true);
    try {
      const textToExport = editedFullText || currentResult.draft.full_text || currentResult.draft.sections?.[0]?.content || '';
      const exportSections = [
        {
          id: 'final_draft',
          title: currentResult.draft.title,
          content: textToExport,
          order: 1,
        },
      ];

      const res = await fetch(`${API_BASE_URL}/api/drafts/export/pdf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify({
          title: currentResult.draft.title,
          document_type: currentResult.document_type,
          sections: exportSections,
          citations: currentResult.citations,
          language: currentResult.language || targetLanguage,
        }),
      });

      if (!res.ok) throw new Error('PDF export failed on backend.');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${currentResult.document_type}_draft.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      alert(`Export PDF Error: ${err.message}`);
    } finally {
      setIsExportingPdf(false);
    }
  };

  // DOCX Export
  const handleExportDocx = async () => {
    if (!currentResult) return;
    setIsExportingDocx(true);
    try {
      const textToExport = editedFullText || currentResult.draft.full_text || currentResult.draft.sections?.[0]?.content || '';
      const exportSections = [
        {
          id: 'final_draft',
          title: currentResult.draft.title,
          content: textToExport,
          order: 1,
        },
      ];

      const res = await fetch(`${API_BASE_URL}/api/drafts/export/docx`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify({
          title: currentResult.draft.title,
          document_type: currentResult.document_type,
          sections: exportSections,
          citations: currentResult.citations,
          language: currentResult.language || targetLanguage,
        }),
      });

      if (!res.ok) throw new Error('DOCX export failed on backend.');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${currentResult.document_type}_draft.docx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      alert(`Export DOCX Error: ${err.message}`);
    } finally {
      setIsExportingDocx(false);
    }
  };

  // Reset Draft / Form
  const handleReset = () => {
    if (isDirty && !window.confirm('You have unsaved edits in your legal draft. Are you sure you want to discard them?')) {
      return;
    }
    setCurrentResult(null);
    setOriginalDraft(null);
    setEditedFullText('');
    setIsDirty(false);
  };

  if (!isMounted) {
    return (
      <div className="min-h-screen bg-ink text-ivory flex flex-col font-sans selection:bg-oxblood selection:text-ivory" suppressHydrationWarning>
        <Navbar />

        <main className="flex-1 pt-28 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full" suppressHydrationWarning>
          <div className="mb-8 border-b border-border pb-6">
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-display font-bold tracking-tight text-ivory">
              Legal Drafting & Notice Generator
            </h1>
            <p className="text-xs sm:text-sm text-stone mt-1.5 max-w-3xl leading-relaxed">
              Generate court-ready first drafts of legal petitions, bail applications, affidavits, and notices formatted to standard court practice.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            <div className="lg:col-span-5 space-y-6">
              <div className="p-6 rounded-2xl border border-border bg-charcoal shadow-lg animate-pulse space-y-4">
                <div className="h-4 bg-olive rounded w-1/3"></div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="h-20 bg-olive/60 rounded-xl"></div>
                  <div className="h-20 bg-olive/60 rounded-xl"></div>
                  <div className="h-20 bg-olive/60 rounded-xl"></div>
                  <div className="h-20 bg-olive/60 rounded-xl"></div>
                </div>
                <div className="h-10 bg-olive/50 rounded-lg"></div>
              </div>
            </div>

            <div className="lg:col-span-7">
              <div className="p-8 rounded-2xl border border-border bg-charcoal shadow-lg animate-pulse flex flex-col items-center justify-center min-h-[460px] text-center space-y-3">
                <div className="w-12 h-12 rounded-full bg-olive/80"></div>
                <div className="h-4 bg-olive rounded w-1/3"></div>
                <div className="h-3 bg-olive/60 rounded w-1/2"></div>
              </div>
            </div>
          </div>
        </main>

        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-ink text-ivory flex flex-col font-sans selection:bg-oxblood selection:text-ivory relative" suppressHydrationWarning>
      {/* Ambient background glows */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[900px] h-[500px] bg-[radial-gradient(ellipse_at_center,rgba(110,38,52,0.12),transparent_70%)]" />
        <div className="absolute top-1/3 -right-48 w-[600px] h-[600px] bg-[radial-gradient(ellipse_at_center,rgba(181,154,104,0.06),transparent_70%)]" />
      </div>

      <Navbar />

      <main className="relative z-10 flex-1 pt-28 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full" suppressHydrationWarning>
        {/* Header & Notice Banner */}
        <div className="mb-8 border-b border-border pb-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-xs font-mono font-semibold tracking-wider text-brass uppercase">
                  Judicial Drafting Studio
                </span>
                <span className="text-xs text-stone/70">· Court-Ready Pleading Generator</span>
              </div>
              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-display font-bold tracking-tight text-ivory">
                Legal Drafting & Notice Generator
              </h1>
              <p className="text-xs sm:text-sm text-stone mt-1.5 max-w-3xl leading-relaxed">
                Generate court-ready first drafts of legal notices, bail applications, civil petitions, and written statements formatted to Indian procedural standards.
              </p>
            </div>

            {currentResult && (
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleReset}
                  className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-border bg-charcoal text-xs font-medium text-stone hover:text-ivory hover:border-brass/40 transition-colors shadow-sm"
                >
                  <RotateCcw className="w-3.5 h-3.5 text-brass" />
                  <span>New Draft</span>
                </button>
              </div>
            )}
          </div>

          {/* Statutory Review Disclaimer Banner */}
          <div className="mt-5 p-4 rounded-xl border border-brass/35 bg-brass/10 flex items-start gap-3 shadow-sm">
            <ShieldAlert className="w-4 h-4 text-brass shrink-0 mt-0.5" />
            <div className="text-xs text-ivory/90 leading-relaxed font-sans">
              <strong className="text-brass font-semibold font-mono uppercase text-[11px] block sm:inline mr-1.5">
                Statutory Notice:
              </strong>
              Drafts generated by NyayaSarathi are preliminary working drafts for legal research and advocate drafting assistance.
              Prior to dispatch or filing before any court, forum, or tribunal, a qualified practicing advocate must independently examine all averments, party names, limitation dates, and applicable statutory provisions.
            </div>
          </div>
        </div>

        {/* Main Workspace Layout: Side-by-side on desktop, stacked on mobile */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* LEFT COLUMN: Configuration & Case Facts Form */}
          <div className={`lg:col-span-5 space-y-6 ${currentResult ? 'hidden lg:block' : 'block'}`}>

            {/* Quick Judicial Presets Card */}
            <div className="p-4 sm:p-5 rounded-2xl border border-border bg-charcoal shadow-md space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-brass" />
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-brass">
                    One-Click Case Presets
                  </span>
                </div>
                <span className="text-[11px] text-stone/70">Click to instantly populate realistic facts</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                {DRAFTING_SAMPLES.map((sample, sIdx) => (
                  <button
                    key={sIdx}
                    type="button"
                    onClick={() => loadSample(sample)}
                    className="p-3 rounded-xl border border-border bg-ink hover:bg-olive/60 hover:border-brass/50 text-left transition-all group flex flex-col justify-between"
                  >
                    <div>
                      <div className="text-xs font-medium text-ivory group-hover:text-brass transition-colors line-clamp-1">
                        {sample.title}
                      </div>
                      <div className="text-[10px] font-mono text-stone/70 mt-1 uppercase">
                        {sample.category}
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-stone/60 pt-2 mt-2 border-t border-border/50">
                      <span>{sample.noticePeriod}</span>
                      <ArrowRight className="w-3 h-3 text-brass opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  </button>
                ))}
              </div>
            </div>
            
            {/* Step 1: Document Configuration Card */}
            <div className="p-5 sm:p-6 rounded-2xl border border-border bg-charcoal shadow-md">
              <div className="flex items-center gap-2.5 pb-3.5 mb-4 border-b border-border">
                <div className="w-6 h-6 rounded-full bg-brass/20 border border-brass/40 flex items-center justify-center text-xs font-bold text-brass">
                  1
                </div>
                <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-brass">
                  Document Configuration
                </h2>
              </div>

              {/* Document Type Selector Grid */}
              <div className="space-y-2 mb-4">
                <label className="text-xs font-mono text-brass uppercase block font-medium">Select Document Type</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {DOCUMENT_TYPES.map((t) => {
                    const isSelected = docType === t.id;
                    const Icon = t.icon;
                    return (
                      <button
                        key={t.id}
                        type="button"
                        onClick={() => setDocType(t.id)}
                        className={`p-3.5 rounded-xl border text-left transition-all duration-200 cursor-pointer ${
                          isSelected
                            ? 'border-brass bg-brass/15 shadow-brass ring-1 ring-brass/40'
                            : 'border-border bg-ink hover:border-brass/30 hover:bg-olive/40'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <Icon className={`w-4 h-4 ${isSelected ? 'text-brass' : 'text-stone'}`} />
                          <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold border ${
                            isSelected
                              ? 'bg-brass/20 text-brass border-brass/40'
                              : 'bg-olive text-stone border-border'
                          }`}>
                            {t.badge}
                          </span>
                        </div>
                        <div className={`text-xs font-bold font-display ${isSelected ? 'text-ivory' : 'text-ivory/80'}`}>
                          {t.name}
                        </div>
                        <p className="text-[10px] text-stone mt-1 line-clamp-2 leading-relaxed font-sans">
                          {t.desc}
                        </p>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Case Category & Jurisdiction */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                <div>
                  <label className="block text-xs font-mono text-brass uppercase mb-1.5 font-medium">
                    Case Category
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full bg-ink border border-border rounded-lg px-3.5 py-2.5 text-xs text-ivory focus:outline-none focus:border-brass focus:ring-1 focus:ring-brass/40 transition-colors"
                  >
                    {CASE_CATEGORIES.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-mono text-brass uppercase mb-1.5 font-medium">
                    Court / Jurisdiction
                  </label>
                  <input
                    type="text"
                    value={jurisdiction}
                    onChange={(e) => setJurisdiction(e.target.value)}
                    placeholder="e.g. Bombay High Court, Sessions Delhi"
                    className="w-full bg-ink border border-border rounded-lg px-3.5 py-2.5 text-xs text-ivory focus:outline-none focus:border-brass focus:ring-1 focus:ring-brass/40 transition-colors placeholder:text-stone/40"
                  />
                </div>
              </div>

              {/* Language Preference */}
              <div className="pt-3 border-t border-border/70">
                <label className="block text-xs font-mono text-brass uppercase mb-1.5 font-medium">
                  Output Language
                </label>
                <select
                  value={targetLanguage}
                  onChange={(e) => setTargetLanguage(e.target.value)}
                  className="w-full bg-ink border border-border rounded-lg px-3.5 py-2.5 text-xs text-ivory focus:outline-none focus:border-brass focus:ring-1 focus:ring-brass/40 transition-colors"
                >
                  {SUPPORTED_LANGUAGES.map((lang) => (
                    <option key={lang.code} value={lang.code}>
                      {lang.flag} {lang.label} ({lang.native})
                    </option>
                  ))}
                </select>
              </div>

              {/* Citations Control */}
              <div className="pt-3.5 border-t border-border/70">
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    id="include-citations-toggle"
                    checked={includeCitations}
                    onChange={(e) => setIncludeCitations(e.target.checked)}
                    className="mt-0.5 w-4 h-4 accent-brass rounded cursor-pointer"
                  />
                  <div>
                    <span className="text-xs font-semibold text-ivory block">
                      Include Verified Legal Citations & Precedents
                    </span>
                    <span className="text-[11px] text-stone block leading-tight mt-0.5">
                      Embeds certified Supreme Court / High Court precedents without fabricated citations.
                    </span>
                  </div>
                </label>
              </div>
            </div>

            {/* Step 2: Case Information Card */}
            <div className="p-5 sm:p-6 rounded-2xl border border-border bg-charcoal shadow-md space-y-4">
              <div className="flex items-center gap-2.5 pb-3.5 border-b border-border">
                <div className="w-6 h-6 rounded-full bg-brass/20 border border-brass/40 flex items-center justify-center text-xs font-bold text-brass">
                  2
                </div>
                <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-brass">
                  Case Information & Facts
                </h2>
              </div>

              {/* Case Title */}
              <div>
                <label className="block text-xs font-mono text-brass uppercase mb-1.5 font-medium">
                  Case Title or Matter Caption (Optional)
                </label>
                <input
                  type="text"
                  value={caseTitle}
                  onChange={(e) => setCaseTitle(e.target.value)}
                  placeholder="e.g. Ramesh Kumar v. State of Maharashtra"
                  className="w-full bg-ink border border-border rounded-lg px-3.5 py-2.5 text-xs text-ivory focus:outline-none focus:border-brass focus:ring-1 focus:ring-brass/40 transition-colors placeholder:text-stone/40"
                />
              </div>

              {/* Parties Details */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-mono text-brass uppercase mb-1.5 font-medium">
                    {docType === 'legal_notice' ? 'Client / Sender' : 'Applicant / Petitioner'}
                  </label>
                  <input
                    type="text"
                    value={senderName}
                    onChange={(e) => setSenderName(e.target.value)}
                    placeholder="Full legal name"
                    className="w-full bg-ink border border-border rounded-lg px-3.5 py-2.5 text-xs text-ivory focus:outline-none focus:border-brass focus:ring-1 focus:ring-brass/40 transition-colors placeholder:text-stone/40 mb-2"
                  />
                  <input
                    type="text"
                    value={senderDetails}
                    onChange={(e) => setSenderDetails(e.target.value)}
                    placeholder="Address / Designation / Age"
                    className="w-full bg-ink border border-border rounded-lg px-3.5 py-2 text-[11px] text-stone focus:outline-none focus:border-brass transition-colors placeholder:text-stone/40"
                  />
                </div>

                <div>
                  <label className="block text-xs font-mono text-brass uppercase mb-1.5 font-medium">
                    {docType === 'legal_notice' ? 'Recipient / Addressee' : 'Opposing Party / Respondent'}
                  </label>
                  <input
                    type="text"
                    value={recipientName}
                    onChange={(e) => setRecipientName(e.target.value)}
                    placeholder="Full name or Authority"
                    className="w-full bg-ink border border-border rounded-lg px-3.5 py-2.5 text-xs text-ivory focus:outline-none focus:border-brass focus:ring-1 focus:ring-brass/40 transition-colors placeholder:text-stone/40 mb-2"
                  />
                  <input
                    type="text"
                    value={recipientDetails}
                    onChange={(e) => setRecipientDetails(e.target.value)}
                    placeholder="Address / Jurisdiction"
                    className="w-full bg-ink border border-border rounded-lg px-3.5 py-2 text-[11px] text-stone focus:outline-none focus:border-brass transition-colors placeholder:text-stone/40"
                  />
                </div>
              </div>

              {/* Statutory Notice Period & Date of Cause of Action */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-mono text-brass uppercase mb-1.5 font-medium">
                    Statutory Notice / Cure Period
                  </label>
                  <select
                    value={noticePeriod}
                    onChange={(e) => setNoticePeriod(e.target.value)}
                    className="w-full bg-ink border border-border rounded-lg px-3.5 py-2.5 text-xs text-ivory focus:outline-none focus:border-brass focus:ring-1 focus:ring-brass/40 transition-colors"
                  >
                    <option value="15 Days">15 Days (Section 138 NI Act / Standard Notice)</option>
                    <option value="30 Days">30 Days (Standard Commercial / Contractual)</option>
                    <option value="60 Days">60 Days (Section 80 CPC - Govt / Public Officer)</option>
                    <option value="7 Days">7 Days (Urgent Default / Injunction Pre-demand)</option>
                    <option value="Immediate">Immediate / 24 Hours (Urgent Criminal / Cease & Desist)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-mono text-brass uppercase mb-1.5 font-medium">
                    Cause of Action Date
                  </label>
                  <input
                    type="text"
                    value={causeOfActionDate}
                    onChange={(e) => setCauseOfActionDate(e.target.value)}
                    placeholder="e.g. 15 March 2024"
                    className="w-full bg-ink border border-border rounded-lg px-3.5 py-2.5 text-xs text-ivory focus:outline-none focus:border-brass focus:ring-1 focus:ring-brass/40 transition-colors placeholder:text-stone/40"
                  />
                </div>
              </div>

              {/* Issuing Advocate / Counsel Coordinates */}
              <div className="p-4 rounded-xl border border-border bg-olive/50 space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-mono font-semibold text-brass flex items-center gap-1.5 uppercase">
                    <Scale className="w-3.5 h-3.5 text-brass" />
                    <span>Issuing Advocate / Counsel Details</span>
                  </label>
                  <span className="text-[10px] font-mono text-stone">Header & Signature Block</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  <div>
                    <label className="block text-[11px] text-stone mb-1 font-mono uppercase">Counsel Name</label>
                    <input
                      type="text"
                      value={advocateName}
                      onChange={(e) => setAdvocateName(e.target.value)}
                      placeholder="e.g. Adv. Rajesh Sharma"
                      className="w-full bg-ink border border-border rounded-lg px-3 py-2 text-xs text-ivory focus:outline-none focus:border-brass transition-colors placeholder:text-stone/40"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] text-stone mb-1 font-mono uppercase">Enrollment No.</label>
                    <input
                      type="text"
                      value={advocateEnrollment}
                      onChange={(e) => setAdvocateEnrollment(e.target.value)}
                      placeholder="e.g. MAH/2456/2014"
                      className="w-full bg-ink border border-border rounded-lg px-3 py-2 text-xs text-ivory focus:outline-none focus:border-brass transition-colors placeholder:text-stone/40"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] text-stone mb-1 font-mono uppercase">Chambers Address</label>
                    <input
                      type="text"
                      value={advocateChambers}
                      onChange={(e) => setAdvocateChambers(e.target.value)}
                      placeholder="e.g. Chamber No. 42, High Court"
                      className="w-full bg-ink border border-border rounded-lg px-3 py-2 text-xs text-ivory focus:outline-none focus:border-brass transition-colors placeholder:text-stone/40"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] text-stone mb-1 font-mono uppercase">Contact Phone / Email</label>
                    <input
                      type="text"
                      value={advocateContact}
                      onChange={(e) => setAdvocateContact(e.target.value)}
                      placeholder="e.g. +91 9876543210"
                      className="w-full bg-ink border border-border rounded-lg px-3 py-2 text-xs text-ivory focus:outline-none focus:border-brass transition-colors placeholder:text-stone/40"
                    />
                  </div>
                </div>
              </div>

              {/* Important Dates */}
              <div>
                <label className="block text-xs font-mono text-brass uppercase mb-1.5 font-medium">
                  Chronology Dates & Milestones
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={newDateInput}
                    onChange={(e) => setNewDateInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddDate())}
                    placeholder="e.g. 15.01.2024 - Agreement signed"
                    className="flex-1 bg-ink border border-border rounded-lg px-3.5 py-2 text-xs text-ivory focus:outline-none focus:border-brass transition-colors placeholder:text-stone/40"
                  />
                  <button
                    type="button"
                    onClick={handleAddDate}
                    className="px-3.5 py-2 bg-olive hover:bg-olive/80 border border-border hover:border-brass/40 rounded-lg text-xs font-medium text-ivory flex items-center gap-1 transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5 text-brass" />
                    <span>Add</span>
                  </button>
                </div>

                {datesList.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {datesList.map((dt, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1.5 text-[11px] bg-olive border border-border text-ivory px-2.5 py-1 rounded-md"
                      >
                        <Calendar className="w-3 h-3 text-brass" />
                        <span>{dt}</span>
                        <button
                          type="button"
                          onClick={() => handleRemoveDate(idx)}
                          className="text-stone hover:text-oxblood-light ml-0.5 transition-colors"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Core Case Facts (Required) */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-mono text-brass uppercase font-medium">
                    Chronological Facts & Grievance <span className="text-oxblood-light">*</span>
                  </label>
                  <span className={`text-[10px] font-mono ${facts.length < 10 ? 'text-oxblood-light' : 'text-stone'}`}>
                    {facts.length} / 50000 chars
                  </span>
                </div>
                <textarea
                  rows={6}
                  value={facts}
                  onChange={(e) => setFacts(e.target.value)}
                  placeholder="Set out the chronological sequence of material facts, transactions, contract terms, breach or FIR details, custody duration, and specific grievances..."
                  className="w-full bg-ink border border-border rounded-xl p-3.5 text-xs md:text-sm text-ivory focus:outline-none focus:border-brass focus:ring-1 focus:ring-brass/40 leading-relaxed resize-y font-sans placeholder:text-stone/40 transition-colors"
                />
              </div>

              {/* Relief & Applicable Sections */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-mono text-brass uppercase mb-1.5 font-medium">
                    Relief / Demands Requested
                  </label>
                  <input
                    type="text"
                    value={requestedRelief}
                    onChange={(e) => setRequestedRelief(e.target.value)}
                    placeholder="e.g. Regular bail on surety, Pay Rs. 5,00,000"
                    className="w-full bg-ink border border-border rounded-lg px-3.5 py-2.5 text-xs text-ivory focus:outline-none focus:border-brass focus:ring-1 focus:ring-brass/40 transition-colors placeholder:text-stone/40"
                  />
                </div>

                <div>
                  <label className="block text-xs font-mono text-brass uppercase mb-1.5 font-medium">
                    Applicable Sections (Optional)
                  </label>
                  <input
                    type="text"
                    value={applicableSections}
                    onChange={(e) => setApplicableSections(e.target.value)}
                    placeholder="e.g. S. 138 NI Act, S. 439 CrPC"
                    className="w-full bg-ink border border-border rounded-lg px-3.5 py-2.5 text-xs text-ivory focus:outline-none focus:border-brass focus:ring-1 focus:ring-brass/40 transition-colors placeholder:text-stone/40"
                  />
                </div>
              </div>

              {/* Generation Button & Inline Validation Error */}
              {genError && (
                <div className="p-3.5 rounded-xl bg-oxblood/20 border border-oxblood-light/60 text-xs text-ivory flex items-start gap-2 shadow-md">
                  <AlertCircle className="w-4 h-4 text-oxblood-light shrink-0 mt-0.5" />
                  <span>{genError}</span>
                </div>
              )}

              <button
                type="button"
                id="generate-draft-btn"
                disabled={isGenerating || facts.trim().length < 10}
                onClick={handleGenerateDraft}
                className="btn-oxblood w-full py-3.5 px-5 rounded-xl font-sans text-xs md:text-sm font-bold tracking-wider uppercase flex items-center justify-center gap-2 transition-all shadow-oxblood disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                {isGenerating ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin text-brass" />
                    <span>{progressMsg || 'Generating Structured Draft...'}</span>
                  </>
                ) : (
                  <>
                    <Scale className="w-4 h-4 text-brass" />
                    <span>Generate Structured Legal Draft</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* RIGHT COLUMN: Review, Editor & Export Actions */}
          <div className="lg:col-span-7 space-y-6">
            {!currentResult ? (
              // Empty State
              <div className="p-10 sm:p-14 rounded-2xl border border-dashed border-border bg-charcoal/40 text-center flex flex-col items-center justify-center min-h-[520px] shadow-lg">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-olive to-charcoal border border-brass/30 flex items-center justify-center mb-4 text-brass shadow-brass">
                  <Scale className="w-8 h-8 text-brass" strokeWidth={1.5} />
                </div>
                <h3 className="text-xl font-display font-semibold text-ivory mb-2">
                  No Legal Draft Generated Yet
                </h3>
                <p className="text-xs sm:text-sm text-stone max-w-md leading-relaxed mb-6 font-sans">
                  Configure your document type on the left, input the chronological case facts, or choose one of the one-click presets above to generate a court-ready draft.
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-left w-full max-w-lg">
                  {DOCUMENT_TYPES.map((t) => (
                    <div key={t.id} className="p-3 rounded-xl border border-border bg-ink text-[11px] shadow-sm">
                      <span className="font-bold font-display text-brass block">{t.name}</span>
                      <span className="text-[10px] text-stone/80 font-mono mt-0.5 block">{t.badge}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              // Active Draft Review & Editor Workspace
              <div className="space-y-6">
                
                {/* Action Bar: Export PDF, DOCX, Copy */}
                <div className="p-4 sm:p-5 rounded-2xl border border-border bg-charcoal shadow-md flex flex-wrap items-center justify-between gap-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-mono font-bold px-3 py-1 rounded-md bg-oxblood/25 border border-oxblood-light/60 text-ivory uppercase">
                      {currentResult.document_type.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-brass font-medium bg-brass/15 border border-brass/35 px-2.5 py-1 rounded-md font-mono">
                      Single Output Document
                    </span>
                    {isDirty && (
                      <div className="flex items-center gap-1.5">
                        <span className="text-[11px] font-semibold text-brass bg-brass/20 border border-brass/40 px-2 py-0.5 rounded font-mono">
                          Unsaved Edits
                        </span>
                        <button
                          type="button"
                          onClick={handleResetToOriginal}
                          className="text-[11px] text-stone hover:text-ivory underline ml-1 transition-colors"
                        >
                          Reset
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Actions buttons */}
                  <div className="flex items-center gap-2">
                    {/* Copy Button */}
                    <button
                      type="button"
                      id="copy-draft-btn"
                      onClick={handleCopyDraft}
                      className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-border bg-ink text-xs font-medium text-stone hover:text-ivory hover:border-brass/50 transition-colors shadow-sm"
                      title="Copy full draft text"
                    >
                      {copySuccess ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-verdigris" />
                          <span className="text-verdigris font-semibold">Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5 text-brass" />
                          <span>Copy Letter</span>
                        </>
                      )}
                    </button>

                    {/* PDF Export */}
                    <button
                      type="button"
                      id="export-pdf-btn"
                      disabled={isExportingPdf}
                      onClick={handleExportPdf}
                      className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-brass/40 bg-brass/15 text-xs font-semibold text-brass hover:bg-brass/25 transition-all shadow-sm disabled:opacity-50"
                    >
                      {isExportingPdf ? (
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Download className="w-3.5 h-3.5" />
                      )}
                      <span>PDF</span>
                    </button>

                    {/* DOCX Export */}
                    <button
                      type="button"
                      id="export-docx-btn"
                      disabled={isExportingDocx}
                      onClick={handleExportDocx}
                      className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-border bg-olive text-xs font-semibold text-ivory hover:border-brass/40 transition-all shadow-sm disabled:opacity-50"
                    >
                      {isExportingDocx ? (
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Download className="w-3.5 h-3.5" />
                      )}
                      <span>DOCX</span>
                    </button>
                  </div>
                </div>

                {/* Warnings & Contradiction Notices */}
                {currentResult.warnings && currentResult.warnings.length > 0 && (
                  <div className="p-4 sm:p-5 rounded-2xl border border-oxblood/40 bg-oxblood/10 space-y-2 shadow-md">
                    <div className="flex items-center gap-2 text-xs font-bold text-oxblood-light font-mono uppercase tracking-wider">
                      <AlertTriangle className="w-4 h-4 shrink-0 text-oxblood-light" />
                      <span>Legal Review & Chronology Notices ({currentResult.warnings.length})</span>
                    </div>
                    <ul className="text-xs text-ivory/90 list-disc list-inside space-y-1 pl-1 font-sans">
                      {currentResult.warnings.map((warn, wIdx) => (
                        <li key={wIdx} className="leading-relaxed">
                          {warn}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Missing Information / Required Advocate Fill-ins */}
                {currentResult.missing_information && currentResult.missing_information.length > 0 && (
                  <div className="p-4 sm:p-5 rounded-2xl border border-brass/35 bg-brass/10 space-y-2 shadow-md">
                    <div className="flex items-center gap-2 text-xs font-bold text-brass font-mono uppercase tracking-wider">
                      <Info className="w-4 h-4 shrink-0 text-brass" />
                      <span>Missing Case Data Flagged with [INFORMATION REQUIRED] ({currentResult.missing_information.length})</span>
                    </div>
                    <p className="text-[11px] text-stone">
                      To prevent factual hallucinations, the generator has not invented these details. Placeholders have been inserted in the draft for counsel confirmation:
                    </p>
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {currentResult.missing_information.map((item, mIdx) => (
                        <span
                          key={mIdx}
                          className="px-2.5 py-1 rounded-md bg-olive border border-brass/30 text-brass text-[11px] font-mono"
                        >
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Single Continuous Legal Draft Document Editor */}
                <div className="p-6 sm:p-8 rounded-2xl border border-border bg-charcoal shadow-2xl space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-border">
                    <div>
                      <span className="text-[10px] font-mono uppercase tracking-widest text-brass block font-semibold">
                        {currentResult.language === 'hi' ? 'विधिक प्रारूप (हिंदी)' : currentResult.language === 'mr' ? 'कायदेशीर मसुदा (मराठी)' : 'OFFICIAL LEGAL DRAFT'}
                      </span>
                      <h3 className="text-base sm:text-lg font-display font-bold text-ivory mt-0.5">
                        {currentResult.draft.title}
                      </h3>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-stone font-mono">
                      <span className="bg-ink px-2.5 py-1 rounded border border-border">
                        {editedFullText.trim() ? editedFullText.trim().split(/\s+/).filter(Boolean).length : 0} words
                      </span>
                      <span>•</span>
                      <span className="bg-ink px-2.5 py-1 rounded border border-border">
                        {editedFullText.length} chars
                      </span>
                    </div>
                  </div>

                  {/* Editable Full Draft Textarea */}
                  <textarea
                    rows={22}
                    value={editedFullText}
                    onChange={(e) => handleFullTextChange(e.target.value)}
                    placeholder="Legal draft will appear here..."
                    className="w-full bg-ink border border-border rounded-xl p-5 text-xs md:text-sm text-ivory/95 focus:outline-none focus:border-brass focus:ring-1 focus:ring-brass/40 leading-relaxed resize-y font-legal whitespace-pre-wrap selection:bg-oxblood selection:text-ivory shadow-inner transition-colors"
                  />

                  <div className="flex flex-wrap items-center justify-between text-[11px] text-stone pt-2 border-t border-border">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-verdigris animate-pulse"></span>
                      <span className="text-ivory font-medium">Single Output Section • Complete Draft Ready for Review</span>
                    </div>
                    <span>Placeholders marked as [MISSING: ...] can be edited directly before export.</span>
                  </div>
                </div>

              </div>
            )}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
