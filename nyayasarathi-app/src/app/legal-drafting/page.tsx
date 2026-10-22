'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Scale,
  Sparkles,
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
  AlertCircle
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

export default function LegalDraftingPage() {
  // Client mount state to prevent hydration errors from browser autofill extensions (e.g. fdprocessedid)
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

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
  const [activeLanguageView, setActiveLanguageView] = useState<'original' | 'translated'>('original');

  // Editor State for Single Unified Legal Draft
  const [editedFullText, setEditedFullText] = useState<string>('');
  const [isDirty, setIsDirty] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);

  // Translation in-place
  const [isTranslating, setIsTranslating] = useState(false);

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
      setActiveLanguageView('original');

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

  // Regional Translation
  const handleTranslateDraft = async (langCode: string) => {
    if (!currentResult) return;
    if (langCode === 'en') {
      if (originalDraft) {
        setCurrentResult({
          ...currentResult,
          draft: originalDraft,
          language: 'en',
        });
        const origText = originalDraft.full_text || originalDraft.sections?.[0]?.content || '';
        setEditedFullText(origText);
        setActiveLanguageView('original');
        setIsDirty(false);
      }
      return;
    }

    setIsTranslating(true);
    try {
      const textToTranslate = editedFullText || currentResult.draft.full_text || currentResult.draft.sections?.[0]?.content || '';
      const draftPayload = {
        title: currentResult.draft.title,
        full_text: textToTranslate,
        sections: [
          {
            id: 'final_draft',
            title: currentResult.draft.title,
            content: textToTranslate,
            order: 1,
          },
        ],
      };

      const res = await fetch(`${API_BASE_URL}/api/drafts/translate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify({
          draft_id: currentResult.draft_id,
          document_type: currentResult.document_type,
          draft: draftPayload,
          source_language: 'en',
          target_language: langCode,
        }),
      });

      if (!res.ok) throw new Error('Translation service failed.');
      const translatedDraft: DraftContent = await res.json();

      setCurrentResult({
        ...currentResult,
        draft: translatedDraft,
        language: langCode,
      });

      const tText = translatedDraft.full_text || translatedDraft.sections?.[0]?.content || '';
      setEditedFullText(tText);
      setActiveLanguageView('translated');
      setIsDirty(false);
    } catch (err: any) {
      alert(`Translation Error: ${err.message}`);
    } finally {
      setIsTranslating(false);
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
      <div className="min-h-screen bg-[#151716] text-[#F4EFE5] flex flex-col font-sans selection:bg-[#B59A68]/30" suppressHydrationWarning>
        <Navbar />

        <main className="flex-1 pt-24 pb-20 px-4 md:px-8 max-w-7xl mx-auto w-full" suppressHydrationWarning>
          <div className="mb-8 border-b border-[#3B3A33]/70 pb-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#B59A68]/40 bg-[#B59A68]/10 text-[#B59A68] text-xs font-semibold mb-2">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Feature 3.8 • AI Legal Drafting & Regional Translation</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-display font-bold tracking-tight text-[#F4EFE5]">
              Legal Drafting & Regional Translation Hub
            </h1>
            <p className="text-sm text-stone-400 mt-1 max-w-3xl leading-relaxed">
              Generate production-quality, court-grounded first drafts of legal documents from facts,
              cross-referenced against authentic Indian statutes, transitional era rules (IPC vs BNS),
              and regional Indic languages.
            </p>

            <div className="mt-4 p-3.5 rounded-xl border border-[#B59A68]/30 bg-[#B59A68]/5 flex items-start gap-3">
              <ShieldAlert className="w-4 h-4 text-[#B59A68] shrink-0 mt-0.5" />
              <div className="text-xs text-stone-300 leading-relaxed">
                <strong className="text-[#B59A68] font-semibold">Important Legal Notice: </strong>
                The drafts generated by NyayaSarathi are preliminary working drafts for assistance to advocates and legal professionals.
                Prior to execution or court filing, a qualified advocate must thoroughly review all factual averments and statutory provisions.
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            <div className="lg:col-span-5 space-y-6">
              <div className="p-6 rounded-2xl border border-[#3B3A33] bg-[#1D211F] shadow-lg animate-pulse space-y-4">
                <div className="h-4 bg-stone-800 rounded w-1/3"></div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="h-20 bg-stone-800/60 rounded-xl"></div>
                  <div className="h-20 bg-stone-800/60 rounded-xl"></div>
                  <div className="h-20 bg-stone-800/60 rounded-xl"></div>
                  <div className="h-20 bg-stone-800/60 rounded-xl"></div>
                </div>
                <div className="h-10 bg-stone-800/50 rounded-lg"></div>
              </div>
              <div className="p-6 rounded-2xl border border-[#3B3A33] bg-[#1D211F] shadow-lg animate-pulse space-y-4">
                <div className="h-4 bg-stone-800 rounded w-1/2"></div>
                <div className="h-10 bg-stone-800/50 rounded-lg"></div>
                <div className="h-32 bg-stone-800/50 rounded-xl"></div>
              </div>
            </div>

            <div className="lg:col-span-7">
              <div className="p-8 rounded-2xl border border-[#3B3A33] bg-[#1D211F] shadow-lg animate-pulse flex flex-col items-center justify-center min-h-[460px] text-center space-y-3">
                <div className="w-12 h-12 rounded-full bg-stone-800/80"></div>
                <div className="h-4 bg-stone-800 rounded w-1/3"></div>
                <div className="h-3 bg-stone-800/60 rounded w-1/2"></div>
              </div>
            </div>
          </div>
        </main>

        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#151716] text-[#F4EFE5] flex flex-col font-sans selection:bg-[#B59A68]/30" suppressHydrationWarning>
      <Navbar />

      <main className="flex-1 pt-24 pb-20 px-4 md:px-8 max-w-7xl mx-auto w-full" suppressHydrationWarning>
        {/* Header & Notice Banner */}
        <div className="mb-8 border-b border-[#3B3A33]/70 pb-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#B59A68]/40 bg-[#B59A68]/10 text-[#B59A68] text-xs font-semibold mb-2">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Feature 3.8 • AI Legal Drafting & Regional Translation</span>
              </div>
              <h1 className="text-2xl md:text-3xl font-display font-bold tracking-tight text-[#F4EFE5]">
                Legal Drafting & Regional Translation Hub
              </h1>
              <p className="text-sm text-stone-400 mt-1 max-w-3xl leading-relaxed">
                Generate production-quality, court-grounded first drafts of legal documents from facts,
                cross-referenced against authentic Indian statutes, transitional era rules (IPC vs BNS),
                and regional Indic languages.
              </p>
            </div>

            {currentResult && (
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleReset}
                  className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-[#3B3A33] bg-[#1D211F] text-xs font-medium text-stone-300 hover:text-white hover:border-stone-500 transition-colors"
                >
                  <RotateCcw className="w-3.5 h-3.5 text-stone-400" />
                  <span>New Draft</span>
                </button>
              </div>
            )}
          </div>

          {/* Statutory Review Disclaimer Banner */}
          <div className="mt-4 p-3.5 rounded-xl border border-[#B59A68]/30 bg-[#B59A68]/5 flex items-start gap-3">
            <ShieldAlert className="w-4 h-4 text-[#B59A68] shrink-0 mt-0.5" />
            <div className="text-xs text-stone-300 leading-relaxed">
              <strong className="text-[#B59A68] font-semibold">Important Legal Notice: </strong>
              The drafts generated by NyayaSarathi are preliminary working drafts for assistance to advocates and legal professionals.
              They do not constitute formal legal certification or certified pleadings. Prior to execution, dispatch, or court filing,
              a qualified advocate must thoroughly review all factual averments, jurisdiction clauses, and applicable statutory provisions.
            </div>
          </div>
        </div>

        {/* Main Workspace Layout: Side-by-side on desktop, stacked on mobile */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* LEFT COLUMN: Configuration & Case Facts Form */}
          <div className={`lg:col-span-5 space-y-6 ${currentResult ? 'hidden lg:block' : 'block'}`}>
            
            {/* Step 1: Document Configuration Card */}
            <div className="p-5 rounded-2xl border border-[#3B3A33] bg-[#1D211F] shadow-lg">
              <div className="flex items-center gap-2 pb-3 mb-4 border-b border-[#3B3A33]">
                <div className="w-6 h-6 rounded-full bg-[#B59A68]/20 flex items-center justify-center text-xs font-bold text-[#B59A68]">
                  1
                </div>
                <h2 className="text-sm font-bold uppercase tracking-wider text-stone-200">
                  Document Configuration
                </h2>
              </div>

              {/* Document Type Selector Grid */}
              <div className="space-y-2 mb-4">
                <label className="text-xs font-semibold text-stone-300">Select Document Type</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {DOCUMENT_TYPES.map((t) => {
                    const isSelected = docType === t.id;
                    const Icon = t.icon;
                    return (
                      <button
                        key={t.id}
                        type="button"
                        onClick={() => setDocType(t.id)}
                        className={`p-3 rounded-xl border text-left transition-all ${
                          isSelected
                            ? 'border-[#B59A68] bg-[#B59A68]/15 shadow-sm ring-1 ring-[#B59A68]/50'
                            : 'border-[#3B3A33] bg-[#151716] hover:border-stone-500 hover:bg-white/[0.02]'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <Icon className={`w-4 h-4 ${isSelected ? 'text-[#B59A68]' : 'text-stone-400'}`} />
                          <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${isSelected ? 'bg-[#B59A68]/20 text-[#B59A68]' : 'bg-[#242926] text-stone-400'}`}>
                            {t.badge}
                          </span>
                        </div>
                        <div className={`text-xs font-bold ${isSelected ? 'text-[#F4EFE5]' : 'text-stone-300'}`}>
                          {t.name}
                        </div>
                        <p className="text-[10px] text-stone-400 mt-1 line-clamp-2 leading-tight">
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
                  <label className="block text-xs font-semibold text-stone-300 mb-1">
                    Case Category
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full bg-[#151716] border border-[#3B3A33] rounded-lg px-3 py-2 text-xs text-stone-200 focus:outline-none focus:border-[#B59A68]"
                  >
                    {CASE_CATEGORIES.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-stone-300 mb-1">
                    Court / Jurisdiction
                  </label>
                  <input
                    type="text"
                    value={jurisdiction}
                    onChange={(e) => setJurisdiction(e.target.value)}
                    placeholder="e.g. Bombay High Court, Sessions Delhi"
                    className="w-full bg-[#151716] border border-[#3B3A33] rounded-lg px-3 py-2 text-xs text-stone-200 focus:outline-none focus:border-[#B59A68]"
                  />
                </div>
              </div>

              {/* Language Preference */}
              <div className="pt-2 border-t border-[#3B3A33]/50">
                <label className="block text-xs font-semibold text-stone-300 mb-1">
                  Output Language
                </label>
                <select
                  value={targetLanguage}
                  onChange={(e) => setTargetLanguage(e.target.value)}
                  className="w-full bg-[#151716] border border-[#3B3A33] rounded-lg px-3 py-2 text-xs text-stone-200 focus:outline-none focus:border-[#B59A68]"
                >
                  {SUPPORTED_LANGUAGES.map((lang) => (
                    <option key={lang.code} value={lang.code}>
                      {lang.flag} {lang.label} ({lang.native})
                    </option>
                  ))}
                </select>
              </div>

              {/* Citations Control */}
              <div className="pt-3 border-t border-[#3B3A33]/50">
                <label className="flex items-start gap-2.5 cursor-pointer">
                  <input
                    type="checkbox"
                    id="include-citations-toggle"
                    checked={includeCitations}
                    onChange={(e) => setIncludeCitations(e.target.checked)}
                    className="mt-0.5 w-4 h-4 accent-[#B59A68] rounded cursor-pointer"
                  />
                  <div>
                    <span className="text-xs font-semibold text-stone-200 block">
                      Include Verified Legal Citations & Precedents
                    </span>
                    <span className="text-[10px] text-stone-400 block leading-tight mt-0.5">
                      Embeds certified Supreme Court / High Court precedents without fabricated citations.
                    </span>
                  </div>
                </label>
              </div>
            </div>

            {/* Step 2: Case Information Card */}
            <div className="p-5 rounded-2xl border border-[#3B3A33] bg-[#1D211F] shadow-lg space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b border-[#3B3A33]">
                <div className="w-6 h-6 rounded-full bg-[#B59A68]/20 flex items-center justify-center text-xs font-bold text-[#B59A68]">
                  2
                </div>
                <h2 className="text-sm font-bold uppercase tracking-wider text-stone-200">
                  Case Information & Facts
                </h2>
              </div>

              {/* Case Title */}
              <div>
                <label className="block text-xs font-semibold text-stone-300 mb-1">
                  Case Title or Matter Caption (Optional)
                </label>
                <input
                  type="text"
                  value={caseTitle}
                  onChange={(e) => setCaseTitle(e.target.value)}
                  placeholder="e.g. Ramesh Kumar v. State of Maharashtra"
                  className="w-full bg-[#151716] border border-[#3B3A33] rounded-lg px-3 py-2 text-xs text-stone-200 focus:outline-none focus:border-[#B59A68]"
                />
              </div>

              {/* Parties Details */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-stone-300 mb-1">
                    {docType === 'legal_notice' ? 'Client / Sender' : 'Applicant / Petitioner'}
                  </label>
                  <input
                    type="text"
                    value={senderName}
                    onChange={(e) => setSenderName(e.target.value)}
                    placeholder="Full legal name"
                    className="w-full bg-[#151716] border border-[#3B3A33] rounded-lg px-3 py-2 text-xs text-stone-200 focus:outline-none focus:border-[#B59A68] mb-1.5"
                  />
                  <input
                    type="text"
                    value={senderDetails}
                    onChange={(e) => setSenderDetails(e.target.value)}
                    placeholder="Address / Designation / Age"
                    className="w-full bg-[#151716] border border-[#3B3A33] rounded-lg px-3 py-1.5 text-[11px] text-stone-300 focus:outline-none focus:border-[#B59A68]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-stone-300 mb-1">
                    {docType === 'legal_notice' ? 'Recipient / Addressee' : 'Opposing Party / Respondent'}
                  </label>
                  <input
                    type="text"
                    value={recipientName}
                    onChange={(e) => setRecipientName(e.target.value)}
                    placeholder="Full name or Authority"
                    className="w-full bg-[#151716] border border-[#3B3A33] rounded-lg px-3 py-2 text-xs text-stone-200 focus:outline-none focus:border-[#B59A68] mb-1.5"
                  />
                  <input
                    type="text"
                    value={recipientDetails}
                    onChange={(e) => setRecipientDetails(e.target.value)}
                    placeholder="Address / Jurisdiction"
                    className="w-full bg-[#151716] border border-[#3B3A33] rounded-lg px-3 py-1.5 text-[11px] text-stone-300 focus:outline-none focus:border-[#B59A68]"
                  />
                </div>
              </div>

              {/* Statutory Notice Period & Date of Cause of Action */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-stone-300 mb-1">
                    Statutory Notice / Cure Period
                  </label>
                  <select
                    value={noticePeriod}
                    onChange={(e) => setNoticePeriod(e.target.value)}
                    className="w-full bg-[#151716] border border-[#3B3A33] rounded-lg px-3 py-2 text-xs text-stone-200 focus:outline-none focus:border-[#B59A68]"
                  >
                    <option value="15 Days">15 Days (Section 138 NI Act / Standard Notice)</option>
                    <option value="30 Days">30 Days (Standard Commercial / Contractual)</option>
                    <option value="60 Days">60 Days (Section 80 CPC - Govt / Public Officer)</option>
                    <option value="7 Days">7 Days (Urgent Default / Injunction Pre-demand)</option>
                    <option value="Immediate">Immediate / 24 Hours (Urgent Criminal / Cease & Desist)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-stone-300 mb-1">
                    Date of Contract / Default / Cause of Action
                  </label>
                  <input
                    type="text"
                    value={causeOfActionDate}
                    onChange={(e) => setCauseOfActionDate(e.target.value)}
                    placeholder="e.g. 15 March 2024 (Cheque dishonour / Default date)"
                    className="w-full bg-[#151716] border border-[#3B3A33] rounded-lg px-3 py-2 text-xs text-stone-200 focus:outline-none focus:border-[#B59A68]"
                  />
                </div>
              </div>

              {/* Issuing Advocate / Counsel Coordinates */}
              <div className="p-3.5 rounded-xl border border-[#3B3A33] bg-[#151716]/60 space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-stone-300 flex items-center gap-1.5">
                    <Scale className="w-3.5 h-3.5 text-[#B59A68]" />
                    <span>Issuing Advocate / Counsel Details</span>
                  </label>
                  <span className="text-[10px] text-stone-400">Header & Signature Block</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  <div>
                    <label className="block text-[11px] text-stone-400 mb-1">Advocate / Counsel Name</label>
                    <input
                      type="text"
                      value={advocateName}
                      onChange={(e) => setAdvocateName(e.target.value)}
                      placeholder="e.g. Adv. Rajesh Sharma"
                      className="w-full bg-[#151716] border border-[#3B3A33] rounded-lg px-3 py-1.5 text-xs text-stone-200 focus:outline-none focus:border-[#B59A68]"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] text-stone-400 mb-1">Bar Council Enrollment No.</label>
                    <input
                      type="text"
                      value={advocateEnrollment}
                      onChange={(e) => setAdvocateEnrollment(e.target.value)}
                      placeholder="e.g. MAH/2456/2014"
                      className="w-full bg-[#151716] border border-[#3B3A33] rounded-lg px-3 py-1.5 text-xs text-stone-200 focus:outline-none focus:border-[#B59A68]"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] text-stone-400 mb-1">Chambers / Office Address</label>
                    <input
                      type="text"
                      value={advocateChambers}
                      onChange={(e) => setAdvocateChambers(e.target.value)}
                      placeholder="e.g. Chamber No. 42, High Court premises"
                      className="w-full bg-[#151716] border border-[#3B3A33] rounded-lg px-3 py-1.5 text-xs text-stone-200 focus:outline-none focus:border-[#B59A68]"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] text-stone-400 mb-1">Contact Phone / Email</label>
                    <input
                      type="text"
                      value={advocateContact}
                      onChange={(e) => setAdvocateContact(e.target.value)}
                      placeholder="e.g. +91 9876543210 | adv.sharma@law.in"
                      className="w-full bg-[#151716] border border-[#3B3A33] rounded-lg px-3 py-1.5 text-xs text-stone-200 focus:outline-none focus:border-[#B59A68]"
                    />
                  </div>
                </div>
              </div>

              {/* Important Dates */}
              <div>
                <label className="block text-xs font-semibold text-stone-300 mb-1">
                  Important Dates & Chronology
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={newDateInput}
                    onChange={(e) => setNewDateInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddDate())}
                    placeholder="e.g. 15.01.2024 - Agreement signed"
                    className="flex-1 bg-[#151716] border border-[#3B3A33] rounded-lg px-3 py-1.5 text-xs text-stone-200 focus:outline-none focus:border-[#B59A68]"
                  />
                  <button
                    type="button"
                    onClick={handleAddDate}
                    className="px-3 py-1.5 bg-[#242926] hover:bg-[#3B3A33] border border-[#3B3A33] rounded-lg text-xs font-medium text-stone-200 flex items-center gap-1"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add</span>
                  </button>
                </div>

                {datesList.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {datesList.map((dt, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1 text-[11px] bg-[#151716] border border-[#3B3A33] text-stone-300 px-2 py-0.5 rounded-md"
                      >
                        <Calendar className="w-3 h-3 text-[#B59A68]" />
                        <span>{dt}</span>
                        <button
                          type="button"
                          onClick={() => handleRemoveDate(idx)}
                          className="text-stone-500 hover:text-red-400 ml-0.5"
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
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-semibold text-stone-300">
                    Chronological Facts & Grievance <span className="text-[#E25C6F]">*</span>
                  </label>
                  <span className={`text-[10px] font-mono ${facts.length < 10 ? 'text-[#E25C6F]' : 'text-stone-400'}`}>
                    {facts.length} / 50000 chars
                  </span>
                </div>
                <textarea
                  rows={6}
                  value={facts}
                  onChange={(e) => setFacts(e.target.value)}
                  placeholder="Set out the chronological sequence of material facts, transactions, contract terms, breach or FIR details, custody duration, and specific grievances..."
                  className="w-full bg-[#151716] border border-[#3B3A33] rounded-xl p-3 text-xs text-stone-200 focus:outline-none focus:border-[#B59A68] leading-relaxed resize-y"
                />
              </div>

              {/* Relief & Applicable Sections */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-stone-300 mb-1">
                    Relief / Demands Requested
                  </label>
                  <input
                    type="text"
                    value={requestedRelief}
                    onChange={(e) => setRequestedRelief(e.target.value)}
                    placeholder="e.g. Regular bail on surety, Pay Rs. 5,00,000"
                    className="w-full bg-[#151716] border border-[#3B3A33] rounded-lg px-3 py-2 text-xs text-stone-200 focus:outline-none focus:border-[#B59A68]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-stone-300 mb-1">
                    Applicable Sections (Optional)
                  </label>
                  <input
                    type="text"
                    value={applicableSections}
                    onChange={(e) => setApplicableSections(e.target.value)}
                    placeholder="e.g. S. 138 NI Act, S. 439 CrPC"
                    className="w-full bg-[#151716] border border-[#3B3A33] rounded-lg px-3 py-2 text-xs text-stone-200 focus:outline-none focus:border-[#B59A68]"
                  />
                </div>
              </div>

              {/* Generation Button & Inline Validation Error */}
              {genError && (
                <div className="p-3 rounded-lg bg-red-950/40 border border-red-800/60 text-xs text-red-200 flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                  <span>{genError}</span>
                </div>
              )}

              <button
                type="button"
                id="generate-draft-btn"
                disabled={isGenerating || facts.trim().length < 10}
                onClick={handleGenerateDraft}
                className="w-full py-3 px-4 rounded-xl font-sans text-xs md:text-sm font-bold tracking-wide uppercase flex items-center justify-center gap-2 transition-all shadow-md bg-[#6E2634] hover:bg-[#8A3545] text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isGenerating ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>{progressMsg || 'Generating Structured Draft...'}</span>
                  </>
                ) : (
                  <>
                    <Scale className="w-4 h-4 text-[#B59A68]" />
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
              <div className="p-12 rounded-2xl border border-dashed border-[#3B3A33] bg-[#1D211F]/50 text-center flex flex-col items-center justify-center min-h-[500px]">
                <div className="w-16 h-16 rounded-full bg-[#242926] border border-[#3B3A33] flex items-center justify-center mb-4">
                  <Scale className="w-8 h-8 text-[#B59A68]/80" strokeWidth={1.5} />
                </div>
                <h3 className="text-lg font-display font-semibold text-stone-200 mb-2">
                  No Legal Draft Generated Yet
                </h3>
                <p className="text-xs text-stone-400 max-w-md leading-relaxed mb-6">
                  Configure your document type on the left, input the chronological case facts,
                  and click &ldquo;Generate Structured Legal Draft&rdquo; to begin.
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-left w-full max-w-lg">
                  {DOCUMENT_TYPES.map((t) => (
                    <div key={t.id} className="p-2.5 rounded-lg border border-[#3B3A33] bg-[#151716] text-[11px]">
                      <span className="font-bold text-[#B59A68] block">{t.name}</span>
                      <span className="text-[10px] text-stone-400">{t.badge}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              // Active Draft Review & Editor Workspace
              <div className="space-y-6">
                
                {/* Action Bar: Export PDF, DOCX, Copy, Language Switcher */}
                <div className="p-4 rounded-2xl border border-[#3B3A33] bg-[#1D211F] shadow-lg flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-md bg-[#6E2634]/40 border border-[#6E2634] text-red-200 uppercase">
                      {currentResult.document_type.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-[#B59A68] font-medium bg-[#B59A68]/10 border border-[#B59A68]/30 px-2 py-0.5 rounded">
                      Single Output Document
                    </span>
                    {isDirty && (
                      <div className="flex items-center gap-1.5">
                        <span className="text-[11px] font-semibold text-amber-400 bg-amber-950/30 border border-amber-800 px-2 py-0.5 rounded">
                          Unsaved Edits
                        </span>
                        <button
                          type="button"
                          onClick={handleResetToOriginal}
                          className="text-[11px] text-stone-400 hover:text-white underline ml-1"
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
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#3B3A33] bg-[#151716] text-xs font-medium text-stone-200 hover:text-white hover:border-[#B59A68] transition-colors"
                      title="Copy full draft text"
                    >
                      {copySuccess ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                          <span className="text-emerald-400">Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5 text-stone-400" />
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
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#B59A68]/40 bg-[#B59A68]/10 text-xs font-semibold text-[#B59A68] hover:bg-[#B59A68]/20 transition-all disabled:opacity-50"
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
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#3B3A33] bg-[#242926] text-xs font-semibold text-stone-200 hover:border-stone-400 transition-all disabled:opacity-50"
                    >
                      {isExportingDocx ? (
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Download className="w-3.5 h-3.5" />
                      )}
                      <span>DOCX</span>
                    </button>

                    {/* Regional Translation Quick Switcher */}
                    <div className="relative inline-flex items-center rounded-lg border border-[#3B3A33] bg-[#151716] p-0.5">
                      <button
                        type="button"
                        onClick={() => handleTranslateDraft('en')}
                        disabled={isTranslating}
                        className={`px-2.5 py-1 text-xs font-medium rounded transition-colors ${
                          currentResult.language === 'en'
                            ? 'bg-[#B59A68]/20 text-[#B59A68] font-bold'
                            : 'text-stone-400 hover:text-stone-200'
                        }`}
                      >
                        EN
                      </button>
                      <button
                        type="button"
                        onClick={() => handleTranslateDraft('hi')}
                        disabled={isTranslating}
                        className={`px-2.5 py-1 text-xs font-medium rounded transition-colors ${
                          currentResult.language === 'hi'
                            ? 'bg-[#B59A68]/20 text-[#B59A68] font-bold'
                            : 'text-stone-400 hover:text-stone-200'
                        }`}
                      >
                        {isTranslating && currentResult.language !== 'hi' ? '...' : 'हिंदी'}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleTranslateDraft('mr')}
                        disabled={isTranslating}
                        className={`px-2.5 py-1 text-xs font-medium rounded transition-colors ${
                          currentResult.language === 'mr'
                            ? 'bg-[#B59A68]/20 text-[#B59A68] font-bold'
                            : 'text-stone-400 hover:text-stone-200'
                        }`}
                      >
                        {isTranslating && currentResult.language !== 'mr' ? '...' : 'मराठी'}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Warnings & Contradiction Notices */}
                {currentResult.warnings && currentResult.warnings.length > 0 && (
                  <div className="p-4 rounded-2xl border border-amber-600/40 bg-amber-950/20 space-y-2">
                    <div className="flex items-center gap-2 text-xs font-bold text-amber-400">
                      <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
                      <span>Legal Review & Chronology Notices ({currentResult.warnings.length})</span>
                    </div>
                    <ul className="text-xs text-amber-200/90 list-disc list-inside space-y-1 pl-1 font-sans">
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
                  <div className="p-4 rounded-2xl border border-sky-600/40 bg-sky-950/20 space-y-2">
                    <div className="flex items-center gap-2 text-xs font-bold text-sky-400">
                      <Info className="w-4 h-4 shrink-0 text-sky-400" />
                      <span>Missing Case Data Flagged with [INFORMATION REQUIRED] ({currentResult.missing_information.length})</span>
                    </div>
                    <p className="text-[11px] text-stone-300">
                      To prevent factual hallucinations, the generator has not invented these details. Placeholders have been inserted in the draft for counsel confirmation:
                    </p>
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {currentResult.missing_information.map((item, mIdx) => (
                        <span
                          key={mIdx}
                          className="px-2 py-0.5 rounded-md bg-sky-900/40 border border-sky-700/60 text-sky-200 text-[11px] font-mono"
                        >
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                )}



                {/* Single Continuous Legal Draft Document Editor */}
                <div className="p-5 md:p-6 rounded-2xl border border-[#3B3A33] bg-[#1D211F] shadow-xl space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#3B3A33]">
                    <div>
                      <span className="text-[10px] font-mono uppercase tracking-wider text-[#B59A68] block font-semibold">
                        {currentResult.language === 'hi' ? 'विधिक प्रारूप (हिंदी)' : currentResult.language === 'mr' ? 'कायदेशीर मसुदा (मराठी)' : 'OFFICIAL LEGAL DRAFT'}
                      </span>
                      <h3 className="text-sm md:text-base font-display font-bold text-stone-100">
                        {currentResult.draft.title}
                      </h3>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-stone-400 font-mono">
                      <span>{editedFullText.trim() ? editedFullText.trim().split(/\s+/).filter(Boolean).length : 0} words</span>
                      <span>•</span>
                      <span>{editedFullText.length} chars</span>
                    </div>
                  </div>

                  {/* Editable Full Draft Textarea */}
                  <textarea
                    rows={22}
                    value={editedFullText}
                    onChange={(e) => handleFullTextChange(e.target.value)}
                    placeholder="Legal draft will appear here..."
                    className="w-full bg-[#151716] border border-[#3B3A33] rounded-xl p-4 md:p-5 text-xs md:text-sm text-stone-100 focus:outline-none focus:border-[#B59A68] leading-relaxed resize-y font-mono whitespace-pre-wrap selection:bg-[#B59A68]/30"
                  />

                  <div className="flex flex-wrap items-center justify-between text-[11px] text-stone-400 pt-1 border-t border-[#3B3A33]/50">
                    <div className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                      <span>Single Output Section • Complete Draft Ready for Review</span>
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
