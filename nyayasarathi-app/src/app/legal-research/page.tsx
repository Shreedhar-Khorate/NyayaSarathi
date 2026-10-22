

'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Scale,
  BookOpen,
  UploadCloud,
  FileText,
  Search,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  ChevronRight,
  ChevronLeft,
  Copy,
  Check,
  RotateCcw,
  ShieldCheck,
  Layers,
  ArrowRight,
  FileCheck,
  X,
  Eye,
  Info,
  Trash2
} from 'lucide-react';
import { Navbar, Footer } from '@/components/layout/NavAndFooter';
import { API_BASE_URL } from '@/lib/config';

interface DocumentItem {
  id: string;
  title: string;
  filename: string;
  file_type: string;
  file_size: number;
  total_pages: number;
  total_chunks: number;
  status: string;
  created_at: string;
}

interface CitationItem {
  source_id: string;
  document_id: string;
  document_title: string;
  page_number: number;
  paragraph_number: number;
  section_title?: string;
  excerpt: string;
  chunk_id: string;
}

interface QAResponseData {
  answer: string;
  citations: CitationItem[];
  insufficient_evidence: boolean;
  provider: string;
  model: string;
}

const SAMPLE_QUESTIONS = [
  "What are the core legal holdings or rulings in this document?",
  "What statutory provisions and sections are cited or relied upon?",
  "What factual background and primary contentions are recorded?",
  "What conditions, directions, or relief did the court order?"
];

export default function LegalResearchPage() {
  // State
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<QAResponseData | null>(null);

  // Inspector State
  const [activeCitation, setActiveCitation] = useState<CitationItem | null>(null);
  const [activeTab, setActiveTab] = useState<'answer' | 'document'>('answer'); // Mobile switch
  const [viewMode, setViewMode] = useState<'excerpt' | 'pdf'>('excerpt');
  const [copied, setCopied] = useState(false);
  const [copiedExcerptId, setCopiedExcerptId] = useState<string | null>(null);

  // Upload modal state
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Delete modal state
  const [docToDelete, setDocToDelete] = useState<DocumentItem | null>(null);
  const [deletingDoc, setDeletingDoc] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch document catalog on mount
  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/qa/documents`);
      if (res.ok) {
        const data = await res.json();
        const docs: DocumentItem[] = data.documents || [];
        setDocuments(docs);
        
        // Check if docId was passed from OCR or link
        let selectedFromUrl = false;
        if (typeof window !== 'undefined') {
          const urlParams = new URLSearchParams(window.location.search);
          const targetDocId = urlParams.get('docId');
          if (targetDocId && docs.some(d => d.id === targetDocId)) {
            setSelectedDocIds([targetDocId]);
            selectedFromUrl = true;
          }
        }

        // By default select all indexed documents if none selected from URL
        if (!selectedFromUrl && docs.length > 0 && selectedDocIds.length === 0) {
          setSelectedDocIds(docs.filter(d => d.status === 'indexed').map(d => d.id));
        }
      }
    } catch (err) {
      console.warn('Could not fetch document catalog:', err);
    }
  };

  const handleToggleDoc = (docId: string) => {
    setSelectedDocIds(prev =>
      prev.includes(docId) ? prev.filter(id => id !== docId) : [...prev, docId]
    );
  };

  const handleSelectAllDocs = () => {
    if (selectedDocIds.length === documents.length) {
      setSelectedDocIds([]);
    } else {
      setSelectedDocIds(documents.map(d => d.id));
    }
  };

  const handleDeleteDocClick = (doc: DocumentItem, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setDocToDelete(doc);
  };

  const confirmDeleteDoc = async () => {
    if (!docToDelete) return;
    const targetId = docToDelete.id;
    setDeletingDoc(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/qa/documents/${targetId}`, {
        method: 'DELETE',
      });
      if (!res.ok && res.status !== 204 && res.status !== 404) {
        throw new Error('Failed to delete document from server.');
      }

      setDocuments(prev => prev.filter(d => d.id !== targetId));
      setSelectedDocIds(prev => prev.filter(id => id !== targetId));
      if (activeCitation?.document_id === targetId) {
        setActiveCitation(null);
      }
      setDocToDelete(null);
    } catch (err: any) {
      setError(err?.message || 'Failed to delete document.');
    } finally {
      setDeletingDoc(false);
    }
  };

  const handleAsk = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${API_BASE_URL}/api/qa/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: question.trim(),
          document_ids: selectedDocIds,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        throw new Error(errData?.detail || `API error ${res.status}`);
      }

      const data: QAResponseData = await res.json();
      setResult(data);

      // Automatically select first citation if available
      if (data.citations && data.citations.length > 0) {
        setActiveCitation(data.citations[0]);
      } else {
        setActiveCitation(null);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to complete legal research query.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    setUploading(true);
    setUploadError(null);

    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      if (uploadTitle.trim()) {
        formData.append('title', uploadTitle.trim());
      }

      const res = await fetch(`${API_BASE_URL}/api/qa/documents/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        throw new Error(errData?.detail || 'Failed to upload document.');
      }

      const newDoc: DocumentItem = await res.json();
      setDocuments(prev => [newDoc, ...prev]);
      setSelectedDocIds(prev => [newDoc.id, ...prev]);
      setUploadOpen(false);
      setUploadFile(null);
      setUploadTitle('');
    } catch (err: any) {
      setUploadError(err?.message || 'Failed to process and index document.');
    } finally {
      setUploading(false);
    }
  };

  const handleCopyAnswer = () => {
    if (!result?.answer) return;
    navigator.clipboard.writeText(result.answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const selectCitation = (citation: CitationItem) => {
    setActiveCitation(citation);
    setActiveTab('document'); // Jump to viewer on mobile
  };

  const handleCopyExcerpt = (text: string, id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    navigator.clipboard.writeText(text);
    setCopiedExcerptId(id);
    setTimeout(() => setCopiedExcerptId(null), 2000);
  };

  // Scroll to a specific source passage card when a citation pill is clicked
  const scrollToSourcePassage = (sourceId: string) => {
    const el = document.getElementById(`source-passage-${sourceId.toLowerCase()}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  };

  // Render clickable citation markers and bold styling with proper text baseline alignment
  const renderInlineWithCitations = (line: string, citations: CitationItem[]) => {
    // Normalize full-width/unicode brackets like 【S1】 -> [S1]
    const normalizedLine = line.replace(/【/g, '[').replace(/】/g, ']');

    // Matches **bold**, *italic*, and [S1] / [S1, S2] / [S1][S2] style citations
    const tokenRegex = /(\*\*[^*]+\*\*|\*[^*]+\*|\[S\d+(?:,\s*S\d+)*\]|\[S\d+\])/g;
    const parts = normalizedLine.split(tokenRegex);

    return parts.map((part, idx) => {
      if (!part) return null;

      // Bold formatting
      if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
        return (
          <strong key={idx} className="font-semibold text-[#F4EFE5]">
            {part.slice(2, -2)}
          </strong>
        );
      }

      // Italic formatting
      if (part.startsWith('*') && part.endsWith('*') && part.length > 2) {
        return (
          <em key={idx} className="italic text-[#E2DACB]">
            {part.slice(1, -1)}
          </em>
        );
      }

      // Citation matching (handles [S1], [S1, S2], etc.)
      const citeMatches = part.match(/\[(S\d+(?:,\s*S\d+)*)\]/i);
      if (citeMatches) {
        const sids = citeMatches[1].split(',').map(s => s.trim().toUpperCase());
        return (
          <span key={idx} className="inline-flex items-center gap-1 mx-1 align-baseline">
            {sids.map((sourceId) => {
              const cit = citations.find(c => c.source_id.toUpperCase() === sourceId);
              const isSelected = activeCitation?.source_id.toUpperCase() === sourceId;

              return (
                <button
                  key={sourceId}
                  type="button"
                  onClick={() => {
                    if (cit) {
                      selectCitation(cit);
                      scrollToSourcePassage(sourceId);
                    }
                  }}
                  className={`inline-flex items-center justify-center px-1.5 py-0.5 rounded text-[11px] font-mono font-bold tracking-tight transition-all duration-200 cursor-pointer select-none leading-none ${
                    isSelected
                      ? 'bg-[#B59A68] text-[#151716] shadow-[0_0_12px_rgba(181,154,104,0.6)] ring-2 ring-[#B59A68] scale-105'
                      : 'bg-[#B59A68]/15 text-[#B59A68] border border-[#B59A68]/40 hover:bg-[#B59A68] hover:text-[#151716] hover:border-[#B59A68] hover:scale-105'
                  }`}
                  title={cit ? `${cit.document_title} (Page ${cit.page_number}, Para ${cit.paragraph_number}) - Click to view excerpt` : `Citation ${sourceId}`}
                >
                  [{sourceId}]
                </button>
              );
            })}
          </span>
        );
      }

      return <span key={idx}>{part}</span>;
    });
  };

  // Render paragraphs, headings, lists, and formatted answer body
  const renderFormattedAnswer = (rawText: string, citations: CitationItem[]) => {
    if (!rawText) return null;

    const sections = rawText.split(/\n\s*\n/);

    return sections.map((sec, sIdx) => {
      const lines = sec.split(/\n/).map(l => l.trim()).filter(Boolean);
      if (lines.length === 0) return null;

      // Check if whole block is bullet list
      const isBulletList = lines.every(l => /^([•\-\*]|\d+\.)\s+/.test(l));

      if (isBulletList) {
        return (
          <ul key={sIdx} className="space-y-2 my-3 pl-1">
            {lines.map((line, lIdx) => {
              const cleanLine = line.replace(/^([•\-\*]|\d+\.)\s+/, '');
              return (
                <li key={lIdx} className="flex items-start gap-2.5 text-sm leading-relaxed text-[#F4EFE5]/90">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#B59A68] mt-2 shrink-0" />
                  <span className="flex-1">{renderInlineWithCitations(cleanLine, citations)}</span>
                </li>
              );
            })}
          </ul>
        );
      }

      return (
        <div key={sIdx} className="space-y-2 my-2.5">
          {lines.map((line, lIdx) => {
            // Markdown header detection
            if (/^###\s+/.test(line)) {
              return (
                <h4 key={lIdx} className="text-sm font-semibold text-[#B59A68] pt-2 pb-0.5 tracking-wide">
                  {renderInlineWithCitations(line.replace(/^###\s+/, ''), citations)}
                </h4>
              );
            }
            if (/^##\s+/.test(line)) {
              return (
                <h3 key={lIdx} className="text-base font-semibold text-[#F4EFE5] pt-3 pb-1 border-b border-[#3B3A33]/50 tracking-tight">
                  {renderInlineWithCitations(line.replace(/^##\s+/, ''), citations)}
                </h3>
              );
            }
            if (/^#\s+/.test(line)) {
              return (
                <h2 key={lIdx} className="text-lg font-bold text-[#F4EFE5] pt-3 pb-1 tracking-tight">
                  {renderInlineWithCitations(line.replace(/^#\s+/, ''), citations)}
                </h2>
              );
            }

            // Standalone bullet line in mixed paragraph
            if (/^([•\-\*]|\d+\.)\s+/.test(line)) {
              const clean = line.replace(/^([•\-\*]|\d+\.)\s+/, '');
              return (
                <div key={lIdx} className="flex items-start gap-2.5 text-sm leading-relaxed text-[#F4EFE5]/90 pl-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#B59A68] mt-2 shrink-0" />
                  <span className="flex-1">{renderInlineWithCitations(clean, citations)}</span>
                </div>
              );
            }

            return (
              <p key={lIdx} className="text-sm leading-relaxed text-[#F4EFE5]/90">
                {renderInlineWithCitations(line, citations)}
              </p>
            );
          })}
        </div>
      );
    });
  };

  return (
    <div className="min-h-screen bg-[#151716] text-[#F4EFE5] flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 pt-28 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        {/* Header Banner */}
        <div className="mb-8 border-b border-[#3B3A33]/70 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h1 className="text-3xl sm:text-4xl font-display font-semibold text-[#F4EFE5] tracking-tight">
              Legal Research & Citations
            </h1>
            <p className="mt-2 text-sm text-[#A9A49A] max-w-2xl">
              Query indexed judicial records, orders, and contracts with paragraph-level verified citations.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setUploadOpen(true)}
              className="inline-flex items-center gap-2 rounded-lg bg-[#B59A68] hover:bg-[#a08552] text-[#151716] px-4 py-2 text-sm font-semibold transition-all shadow-md active:scale-95"
            >
              <UploadCloud className="h-4 w-4" />
              <span>Upload Document</span>
            </button>
          </div>
        </div>

        {/* Document Selection Strip */}
        <div className="mb-6 rounded-xl border border-[#3B3A33] bg-[#1D211F]/60 p-4 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-[#B59A68]" />
              <span className="text-xs font-semibold uppercase tracking-wider text-[#A9A49A]">
                Scope Research Corpus ({selectedDocIds.length} of {documents.length} selected)
              </span>
            </div>
            {documents.length > 0 && (
              <button
                type="button"
                onClick={handleSelectAllDocs}
                className="text-xs text-[#B59A68] hover:underline transition-colors"
              >
                {selectedDocIds.length === documents.length ? 'Deselect All' : 'Select All'}
              </button>
            )}
          </div>

          {documents.length === 0 ? (
            <div className="flex items-center justify-between text-xs text-[#A9A49A] py-3 px-4 rounded-lg bg-[#151716]/60 border border-[#3B3A33]/50">
              <span>No user documents indexed yet. Upload a PDF, DOCX, or TXT legal record to begin research.</span>
              <button
                type="button"
                onClick={() => setUploadOpen(true)}
                className="text-[#B59A68] font-semibold hover:underline flex items-center gap-1"
              >
                <UploadCloud className="h-3.5 w-3.5" />
                <span>Upload First File</span>
              </button>
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {documents.map((doc) => {
                const isSelected = selectedDocIds.includes(doc.id);
                return (
                  <div
                    key={doc.id}
                    onClick={() => handleToggleDoc(doc.id)}
                    className={`group cursor-pointer flex items-center gap-2 rounded-lg pl-3 pr-2 py-1.5 text-xs font-medium border transition-all select-none ${
                      isSelected
                        ? 'border-[#B59A68] bg-[#B59A68]/15 text-[#F4EFE5] shadow-sm'
                        : 'border-[#3B3A33] bg-[#151716]/60 text-[#A9A49A] hover:border-[#B59A68]/40'
                    }`}
                  >
                    <FileText className={`h-3.5 w-3.5 shrink-0 ${isSelected ? 'text-[#B59A68]' : 'text-[#A9A49A]'}`} />
                    <span className="max-w-[180px] truncate">{doc.title}</span>
                    <span className="text-[10px] text-[#A9A49A]/80 font-mono">
                      {doc.total_pages}p
                    </span>
                    <button
                      type="button"
                      onClick={(e) => handleDeleteDocClick(doc, e)}
                      className="ml-1 p-1 rounded hover:bg-rose-500/20 text-[#A9A49A] hover:text-rose-400 transition-colors opacity-70 group-hover:opacity-100"
                      title={`Delete "${doc.title}"`}
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Mobile Tab Switcher */}
        <div className="flex md:hidden mb-4 border border-[#3B3A33] rounded-lg p-1 bg-[#1D211F]">
          <button
            type="button"
            onClick={() => setActiveTab('answer')}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-colors ${
              activeTab === 'answer' ? 'bg-[#B59A68] text-[#151716]' : 'text-[#A9A49A]'
            }`}
          >
            AI Grounded Answer
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('document')}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-colors ${
              activeTab === 'document' ? 'bg-[#B59A68] text-[#151716]' : 'text-[#A9A49A]'
            }`}
          >
            Source Document {activeCitation ? `[${activeCitation.source_id}]` : ''}
          </button>
        </div>

        {/* Main Split-Screen Workspace */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* LEFT PANEL: Q&A + Answer + Citation Cards (Col 1-7) */}
          <div className={`lg:col-span-7 flex flex-col gap-6 ${activeTab === 'document' ? 'hidden md:flex' : 'flex'}`}>
            
            {/* Question Input Card */}
            <div className="rounded-xl border border-[#3B3A33] bg-[#1D211F] p-5 shadow-lg">
              <form onSubmit={handleAsk} className="flex flex-col gap-3">
                <label htmlFor="rag-question" className="text-xs font-semibold uppercase tracking-wider text-[#A9A49A] flex items-center justify-between">
                  <span>Inquire into Selected Legal Records</span>
                  <span className="text-[11px] text-[#A9A49A]/60 lowercase">ctrl + enter to execute</span>
                </label>

                <div className="relative">
                  <textarea
                    id="rag-question"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                        handleAsk();
                      }
                    }}
                    placeholder="e.g. What precedent or legal basis did the court rely upon regarding Section 420 IPC and anticipatory bail conditions?"
                    rows={3}
                    className="w-full rounded-lg border border-[#3B3A33] bg-[#151716] p-3 text-sm text-[#F4EFE5] placeholder-[#A9A49A]/50 focus:border-[#B59A68] focus:outline-none focus:ring-1 focus:ring-[#B59A68] transition-all resize-none font-sans"
                  />
                </div>

                {/* Sample Prompt Chips */}
                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                  <span className="text-[11px] text-[#A9A49A]/70 flex items-center gap-1">
                    <Search className="h-3 w-3 text-[#B59A68]" /> Suggested:
                  </span>
                  {SAMPLE_QUESTIONS.map((sq, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => setQuestion(sq)}
                      className="rounded border border-[#3B3A33]/70 bg-[#151716]/60 px-2 py-0.5 text-[11px] text-[#A9A49A] hover:text-[#F4EFE5] hover:border-[#B59A68]/50 transition-colors"
                    >
                      {sq.slice(0, 38)}...
                    </button>
                  ))}
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-[#3B3A33]/50">
                  <button
                    type="button"
                    onClick={() => {
                      setQuestion('');
                      setResult(null);
                      setActiveCitation(null);
                    }}
                    className="inline-flex items-center gap-1 text-xs text-[#A9A49A] hover:text-[#F4EFE5] transition-colors"
                  >
                    <RotateCcw className="h-3.5 w-3.5" />
                    <span>Reset</span>
                  </button>

                  <button
                    type="submit"
                    disabled={loading || !question.trim()}
                    className="inline-flex items-center gap-2 rounded-lg bg-[#B59A68] hover:bg-[#a08552] disabled:opacity-40 disabled:hover:bg-[#B59A68] text-[#151716] px-5 py-2 text-sm font-semibold transition-all shadow-md active:scale-95"
                  >
                    {loading ? (
                      <>
                        <div className="h-4 w-4 animate-spin rounded-full border-2 border-[#151716] border-t-transparent" />
                        <span>Retrieving & Reasoning...</span>
                      </>
                    ) : (
                      <>
                        <Search className="h-4 w-4" />
                        <span>Search & Synthesize</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>

            {/* Error Message */}
            {error && (
              <div className="rounded-lg border border-[#8A3545] bg-[#6E2634]/20 p-4 text-xs text-[#F4EFE5] flex items-center gap-3">
                <AlertTriangle className="h-4 w-4 text-[#8A3545] shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Grounded Answer Card */}
            {result && (
              <div className="rounded-xl border border-[#3B3A33] bg-[#1D211F] p-6 shadow-xl flex flex-col gap-4">
                
                {/* Answer Meta Bar */}
                <div className="flex flex-wrap items-center justify-between gap-3 pb-3.5 border-b border-[#3B3A33]/70">
                  <div className="flex items-center gap-2.5">
                    <div className="h-8 w-8 rounded-lg bg-[#B59A68]/15 border border-[#B59A68]/30 flex items-center justify-center text-[#B59A68] shrink-0">
                      <FileText className="h-4 w-4" />
                    </div>
                    <div>
                      <h2 className="text-sm font-semibold text-[#F4EFE5] tracking-tight">
                        Research Findings
                      </h2>
                      <span className="text-[11px] text-[#A9A49A]">
                        Verified citations from document corpus
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-[11px] rounded-md bg-[#151716] px-2.5 py-1 text-[#B59A68] border border-[#3B3A33] font-mono">
                      {result.provider} · {result.model}
                    </span>
                    <button
                      type="button"
                      onClick={handleCopyAnswer}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-[#3B3A33] bg-[#151716] px-3 py-1.5 text-xs text-[#A9A49A] hover:text-[#F4EFE5] hover:border-[#B59A68]/50 transition-colors"
                    >
                      {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                      <span>{copied ? 'Copied' : 'Copy Answer'}</span>
                    </button>
                  </div>
                </div>

                {/* Insufficient Evidence Warning Banner */}
                {result.insufficient_evidence && (
                  <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-3 text-xs text-amber-200 flex items-start gap-2.5">
                    <Info className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold">Insufficient Document Evidence Detected:</span>
                      <p className="mt-0.5 text-amber-200/80">
                        The retrieved corpus does not contain unambiguous factual evidence to fully answer your question. The system has refrained from guessing.
                      </p>
                    </div>
                  </div>
                )}

                {/* Body of the Answer */}
                <div className="py-1">
                  {renderFormattedAnswer(result.answer, result.citations)}
                </div>

                <div className="pt-3 border-t border-[#3B3A33]/50 flex items-center justify-between text-[11px] text-[#A9A49A]/70">
                  <span className="flex items-center gap-1.5">
                    <ShieldCheck className="h-3.5 w-3.5 text-[#B59A68]" />
                    Every statement above is tethered directly to the source citations below.
                  </span>
                  <span>{result.citations.length} cited source{result.citations.length === 1 ? '' : 's'}</span>
                </div>
              </div>
            )}

            {/* Separate Card: Relevant Source Passages */}
            {result && result.citations && result.citations.length > 0 && (
              <div className="rounded-xl border border-[#3B3A33] bg-[#1D211F] p-6 shadow-xl flex flex-col gap-4">
                
                <div className="flex items-center justify-between pb-3.5 border-b border-[#3B3A33]/70">
                  <div className="flex items-center gap-2.5">
                    <div className="h-8 w-8 rounded-lg bg-[#B59A68]/15 border border-[#B59A68]/30 flex items-center justify-center text-[#B59A68] shrink-0">
                      <BookOpen className="h-4 w-4" />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-[#F4EFE5] tracking-tight">
                        Relevant Source Passages
                      </h3>
                      <span className="text-[11px] text-[#A9A49A]">
                        Verbatim evidentiary paragraphs extracted directly from your selected documents
                      </span>
                    </div>
                  </div>

                  <span className="text-xs text-[#B59A68] bg-[#B59A68]/10 border border-[#B59A68]/30 px-2.5 py-0.5 rounded-full font-medium">
                    {result.citations.length} passage{result.citations.length === 1 ? '' : 's'}
                  </span>
                </div>

                <div className="flex flex-col gap-3.5">
                  {result.citations.map((cit) => {
                    const isSelected = activeCitation?.source_id.toUpperCase() === cit.source_id.toUpperCase();
                    const isCopiedExcerpt = copiedExcerptId === cit.source_id;

                    return (
                      <div
                        key={cit.source_id}
                        id={`source-passage-${cit.source_id.toLowerCase()}`}
                        onClick={() => selectCitation(cit)}
                        className={`group cursor-pointer rounded-xl border p-4.5 transition-all duration-200 ${
                          isSelected
                            ? 'border-[#B59A68] bg-[#B59A68]/15 shadow-[0_0_20px_rgba(181,154,104,0.18)] ring-1 ring-[#B59A68]/60'
                            : 'border-[#3B3A33]/80 bg-[#151716]/80 hover:border-[#B59A68]/50 hover:bg-[#151716]'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2 mb-3">
                          <div className="flex items-center gap-2.5">
                            <span className="rounded bg-[#B59A68] text-[#151716] font-mono font-bold text-xs px-2.5 py-0.5 tracking-tight shadow-sm">
                              [{cit.source_id}]
                            </span>
                            <span className="font-semibold text-xs text-[#F4EFE5] truncate max-w-[280px] flex items-center gap-1.5">
                              <FileText className="h-3.5 w-3.5 text-[#B59A68] shrink-0" />
                              <span className="truncate">{cit.document_title}</span>
                            </span>
                          </div>

                          <div className="flex items-center gap-2">
                            <span className="text-[11px] text-[#A9A49A] font-mono bg-[#1D211F] px-2.5 py-0.5 rounded-md border border-[#3B3A33]/70 shadow-inner">
                              Page {cit.page_number} · Para {cit.paragraph_number}
                            </span>
                            {isSelected && (
                              <span className="text-[10px] text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30 flex items-center gap-1">
                                <CheckCircle2 className="h-3 w-3" /> Active Excerpt
                              </span>
                            )}
                          </div>
                        </div>

                        {cit.section_title && (
                          <div className="mb-2.5 text-[11px] text-[#B59A68] font-medium flex items-center gap-1 bg-[#B59A68]/10 px-2.5 py-1 rounded border border-[#B59A68]/20">
                            <span className="font-semibold">Section:</span>
                            <span className="text-[#F4EFE5]/90">{cit.section_title}</span>
                          </div>
                        )}

                        <blockquote className="text-xs text-[#F4EFE5]/95 font-serif leading-relaxed pl-3.5 border-l-2 border-[#B59A68] bg-[#151716]/80 p-3 rounded-r-lg shadow-inner">
                          "{cit.excerpt}"
                        </blockquote>

                        <div className="mt-3.5 flex items-center justify-between pt-2.5 border-t border-[#3B3A33]/40">
                          <span className="text-[11px] text-[#A9A49A] group-hover:text-[#B59A68] transition-colors flex items-center gap-1.5">
                            <Eye className="h-3.5 w-3.5" />
                            <span>{isSelected ? 'Currently Loaded in Right Inspector' : 'Click to inspect in document viewer'}</span>
                          </span>

                          <button
                            type="button"
                            onClick={(e) => handleCopyExcerpt(cit.excerpt, cit.source_id, e)}
                            className="inline-flex items-center gap-1 text-[11px] text-[#A9A49A] hover:text-[#F4EFE5] px-2 py-1 rounded bg-[#1D211F]/80 border border-[#3B3A33]/50 hover:border-[#B59A68]/50 transition-colors"
                            title="Copy this excerpt"
                          >
                            {isCopiedExcerpt ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                            <span>{isCopiedExcerpt ? 'Copied' : 'Copy Excerpt'}</span>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* RIGHT PANEL: Source Document & Exact Paragraph Inspector (Col 8-12) */}
          <div className={`lg:col-span-5 flex flex-col gap-4 ${activeTab === 'answer' ? 'hidden md:flex' : 'flex'}`}>
            <div className="rounded-xl border border-[#3B3A33] bg-[#1D211F] p-5 shadow-xl sticky top-24 max-h-[calc(100vh-7rem)] flex flex-col">
              
              {/* Header Bar */}
              <div className="flex items-center justify-between pb-3.5 border-b border-[#3B3A33]/70 shrink-0">
                <div className="flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-[#B59A68]" />
                  <span className="text-xs font-semibold uppercase tracking-wider text-[#A9A49A]">
                    Source Evidence Inspector
                  </span>
                </div>

                {activeCitation && (
                  <div className="flex items-center gap-1 bg-[#151716] p-0.5 rounded-lg border border-[#3B3A33]">
                    <button
                      type="button"
                      onClick={() => setViewMode('excerpt')}
                      className={`text-[11px] px-2.5 py-1 rounded-md transition-colors ${
                        viewMode === 'excerpt'
                          ? 'bg-[#B59A68] text-[#151716] font-semibold shadow-sm'
                          : 'text-[#A9A49A] hover:text-[#F4EFE5]'
                      }`}
                    >
                      Verbatim Excerpt
                    </button>
                    <button
                      type="button"
                      onClick={() => setViewMode('pdf')}
                      className={`text-[11px] px-2.5 py-1 rounded-md transition-colors ${
                        viewMode === 'pdf'
                          ? 'bg-[#B59A68] text-[#151716] font-semibold shadow-sm'
                          : 'text-[#A9A49A] hover:text-[#F4EFE5]'
                      }`}
                    >
                      Document File
                    </button>
                  </div>
                )}
              </div>

              {/* Inspector Content */}
              {!activeCitation ? (
                <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-[#A9A49A]">
                  <FileCheck className="h-12 w-12 text-[#3B3A33] mb-3 stroke-[1]" />
                  <h4 className="text-sm font-semibold text-[#F4EFE5]">No Citation Selected</h4>
                  <p className="text-xs text-[#A9A49A] mt-1.5 max-w-xs leading-relaxed">
                    Execute a research query and click any <span className="text-[#B59A68] font-semibold">[S#]</span> marker or source passage to inspect the authentic excerpt here.
                  </p>
                </div>
              ) : viewMode === 'excerpt' ? (
                <div className="flex-1 flex flex-col gap-3 pt-3 overflow-hidden">
                  {/* Active Source Title & Meta */}
                  <div className="rounded-lg bg-[#151716] p-3.5 border border-[#3B3A33]/70 shrink-0">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="rounded bg-[#B59A68] text-[#151716] text-xs font-bold px-2 py-0.5">
                        [{activeCitation.source_id}]
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] text-emerald-400 flex items-center gap-1 font-medium">
                          <CheckCircle2 className="h-3 w-3" /> Verifiable Stored Passage
                        </span>
                        <button
                          type="button"
                          onClick={() => {
                            const doc = documents.find(d => d.id === activeCitation.document_id) || {
                              id: activeCitation.document_id,
                              title: activeCitation.document_title,
                              filename: activeCitation.document_title,
                              file_type: '.pdf',
                              file_size: 0,
                              total_pages: activeCitation.page_number,
                              total_chunks: 1,
                              status: 'indexed',
                              created_at: '',
                            };
                            handleDeleteDocClick(doc);
                          }}
                          className="p-1 rounded hover:bg-rose-500/20 text-[#A9A49A] hover:text-rose-400 transition-colors"
                          title="Delete this document"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                    <h3 className="text-sm font-semibold text-[#F4EFE5] truncate">
                      {activeCitation.document_title}
                    </h3>
                    <div className="flex items-center gap-2.5 text-xs text-[#A9A49A] mt-1.5 font-mono">
                      <span>Page {activeCitation.page_number}</span>
                      <span>·</span>
                      <span>Paragraph {activeCitation.paragraph_number}</span>
                      {activeCitation.section_title && (
                        <>
                          <span>·</span>
                          <span className="text-[#B59A68] font-sans truncate">{activeCitation.section_title}</span>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Verbatim Excerpt Reader */}
                  <div className="flex-1 rounded-lg bg-[#151716] p-4 border border-[#3B3A33]/70 overflow-y-auto min-h-[180px] flex flex-col justify-between gap-3">
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-mono uppercase tracking-wider text-[#A9A49A]/80">
                          Authentic Stored Paragraph Extract:
                        </span>
                        <button
                          type="button"
                          onClick={() => handleCopyExcerpt(activeCitation.excerpt, activeCitation.source_id)}
                          className="inline-flex items-center gap-1 text-[11px] text-[#A9A49A] hover:text-[#F4EFE5] transition-colors"
                        >
                          {copiedExcerptId === activeCitation.source_id ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                          <span>{copiedExcerptId === activeCitation.source_id ? 'Copied' : 'Copy'}</span>
                        </button>
                      </div>
                      <p className="text-sm font-serif leading-relaxed text-[#F2EBDD] bg-[#B59A68]/10 p-3.5 rounded-lg border-l-4 border-[#B59A68]">
                        "{activeCitation.excerpt}"
                      </p>
                    </div>

                    <div className="text-[11px] text-[#A9A49A]/60 flex items-center justify-between pt-2 border-t border-[#3B3A33]/40">
                      <span>Verified against indexed chunk record</span>
                      <span>{activeCitation.excerpt.length} characters</span>
                    </div>
                  </div>

                  {/* Source Navigation Controls */}
                  {result && result.citations.length > 1 && (
                    <div className="flex items-center justify-between pt-2 border-t border-[#3B3A33]/50 shrink-0">
                      <span className="text-xs text-[#A9A49A]">
                        Citation {result.citations.findIndex(c => c.source_id === activeCitation.source_id) + 1} of {result.citations.length}
                      </span>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => {
                            const idx = result.citations.findIndex(c => c.source_id === activeCitation.source_id);
                            if (idx > 0) setActiveCitation(result.citations[idx - 1]);
                          }}
                          className="p-1.5 rounded-lg border border-[#3B3A33] hover:border-[#B59A68] text-[#A9A49A] hover:text-[#F4EFE5] transition-colors"
                          title="Previous Citation"
                        >
                          <ChevronLeft className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            const idx = result.citations.findIndex(c => c.source_id === activeCitation.source_id);
                            if (idx < result.citations.length - 1) setActiveCitation(result.citations[idx + 1]);
                          }}
                          className="p-1.5 rounded-lg border border-[#3B3A33] hover:border-[#B59A68] text-[#A9A49A] hover:text-[#F4EFE5] transition-colors"
                          title="Next Citation"
                        >
                          <ChevronRight className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                /* PDF / Raw File Viewer Mode */
                <div className="flex-1 flex flex-col pt-3 min-h-[440px] overflow-hidden">
                  <div className="flex items-center justify-between text-xs text-[#A9A49A] mb-2 shrink-0">
                    <span className="truncate max-w-[200px]">{activeCitation.document_title}</span>
                    <div className="flex items-center gap-3">
                      <button
                        type="button"
                        onClick={() => {
                          const doc = documents.find(d => d.id === activeCitation.document_id) || {
                            id: activeCitation.document_id,
                            title: activeCitation.document_title,
                            filename: activeCitation.document_title,
                            file_type: '.pdf',
                            file_size: 0,
                            total_pages: activeCitation.page_number,
                            total_chunks: 1,
                            status: 'indexed',
                            created_at: '',
                          };
                          handleDeleteDocClick(doc);
                        }}
                        className="inline-flex items-center gap-1 text-rose-400/80 hover:text-rose-400 hover:underline"
                        title="Delete this document"
                      >
                        <Trash2 className="h-3 w-3" /> Delete
                      </button>
                      <a
                        href={`${API_BASE_URL}/api/qa/documents/${activeCitation.document_id}/file`}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-[#B59A68] hover:underline"
                      >
                        <ExternalLink className="h-3 w-3" /> Full Screen
                      </a>
                    </div>
                  </div>
                  <iframe
                    src={`${API_BASE_URL}/api/qa/documents/${activeCitation.document_id}/file#page=${activeCitation.page_number}`}
                    className="w-full flex-1 min-h-[380px] rounded-lg border border-[#3B3A33] bg-[#151716]"
                    title="Source Document Viewer"
                  />
                </div>
              )}
            </div>
          </div>

        </div>
      </main>

      {/* Upload Document Modal */}
      <AnimatePresence>
        {uploadOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-md rounded-xl border border-[#3B3A33] bg-[#1D211F] p-6 shadow-2xl"
            >
              <div className="flex items-center justify-between pb-3 border-b border-[#3B3A33]/70">
                <div className="flex items-center gap-2">
                  <UploadCloud className="h-5 w-5 text-[#B59A68]" />
                  <h3 className="text-base font-display font-semibold text-[#F4EFE5]">
                    Ingest Legal Document
                  </h3>
                </div>
                <button
                  type="button"
                  onClick={() => setUploadOpen(false)}
                  className="text-[#A9A49A] hover:text-[#F4EFE5] transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <form onSubmit={handleUpload} className="mt-4 flex flex-col gap-4">
                <div>
                  <label className="text-xs font-semibold uppercase tracking-wider text-[#A9A49A] block mb-1.5">
                    Custom Title (Optional)
                  </label>
                  <input
                    type="text"
                    value={uploadTitle}
                    onChange={(e) => setUploadTitle(e.target.value)}
                    placeholder="e.g. State of Maharashtra vs XYZ (Bail Order)"
                    className="w-full rounded-lg border border-[#3B3A33] bg-[#151716] p-2.5 text-xs text-[#F4EFE5] placeholder-[#A9A49A]/50 focus:border-[#B59A68] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold uppercase tracking-wider text-[#A9A49A] block mb-1.5">
                    Select File (PDF, DOCX, TXT)
                  </label>
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    className="cursor-pointer border-2 border-dashed border-[#3B3A33] hover:border-[#B59A68]/60 rounded-lg p-6 text-center bg-[#151716]/60 transition-colors"
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,.docx,.doc,.txt"
                      onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                      className="hidden"
                    />
                    <FileText className="h-8 w-8 text-[#B59A68] mx-auto mb-2 opacity-80" />
                    {uploadFile ? (
                      <div className="text-xs text-[#F4EFE5] font-medium truncate">
                        {uploadFile.name} ({(uploadFile.size / 1024).toFixed(1)} KB)
                      </div>
                    ) : (
                      <>
                        <span className="text-xs text-[#F4EFE5] font-medium block">
                          Click to browse or drag file here
                        </span>
                        <span className="text-[11px] text-[#A9A49A] block mt-1">
                          PyMuPDF page-aware chunking & text indexing
                        </span>
                      </>
                    )}
                  </div>
                </div>

                {uploadError && (
                  <div className="rounded border border-[#8A3545] bg-[#6E2634]/20 p-2.5 text-xs text-[#F4EFE5] flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-[#8A3545] shrink-0" />
                    <span>{uploadError}</span>
                  </div>
                )}

                <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#3B3A33]/50">
                  <button
                    type="button"
                    onClick={() => setUploadOpen(false)}
                    className="px-4 py-2 text-xs font-medium text-[#A9A49A] hover:text-[#F4EFE5]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={uploading || !uploadFile}
                    className="inline-flex items-center gap-2 rounded-lg bg-[#B59A68] hover:bg-[#a08552] disabled:opacity-40 text-[#151716] px-4 py-2 text-xs font-semibold transition-all shadow-md"
                  >
                    {uploading ? (
                      <>
                        <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-[#151716] border-t-transparent" />
                        <span>Processing Chunks...</span>
                      </>
                    ) : (
                      <>
                        <UploadCloud className="h-3.5 w-3.5" />
                        <span>Upload & Index</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
        {/* Delete Confirmation Modal */}
        {docToDelete && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="w-full max-w-md rounded-xl border border-rose-500/30 bg-[#1D211F] p-6 shadow-2xl"
            >
              <div className="flex items-center justify-between pb-3 border-b border-[#3B3A33]/70">
                <div className="flex items-center gap-2 text-rose-400">
                  <Trash2 className="h-5 w-5" />
                  <h3 className="text-base font-display font-semibold text-[#F4EFE5]">
                    Delete Document
                  </h3>
                </div>
                <button
                  type="button"
                  onClick={() => setDocToDelete(null)}
                  className="text-[#A9A49A] hover:text-[#F4EFE5] transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="mt-4 flex flex-col gap-3">
                <p className="text-xs text-[#F4EFE5]/90 leading-relaxed">
                  Are you sure you want to permanently delete this document and all its indexed chunks?
                </p>

                <div className="rounded-lg bg-[#151716] p-3 border border-[#3B3A33]/70">
                  <div className="flex items-center gap-2 mb-1">
                    <FileText className="h-4 w-4 text-[#B59A68]" />
                    <span className="text-xs font-semibold text-[#F4EFE5] truncate">
                      {docToDelete.title}
                    </span>
                  </div>
                  <div className="text-[11px] text-[#A9A49A] flex items-center gap-2">
                    <span>{docToDelete.filename}</span>
                    <span>·</span>
                    <span>{docToDelete.total_pages} page(s)</span>
                  </div>
                </div>

                <div className="rounded border border-amber-500/30 bg-amber-500/10 p-2.5 text-[11px] text-amber-200/90 flex items-center gap-2">
                  <AlertTriangle className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                  <span>This action will remove the file from your workspace and citation database.</span>
                </div>

                <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#3B3A33]/50">
                  <button
                    type="button"
                    onClick={() => setDocToDelete(null)}
                    className="px-4 py-2 text-xs font-medium text-[#A9A49A] hover:text-[#F4EFE5]"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={confirmDeleteDoc}
                    disabled={deletingDoc}
                    className="inline-flex items-center gap-2 rounded-lg bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white px-4 py-2 text-xs font-semibold transition-all shadow-md active:scale-95"
                  >
                    {deletingDoc ? (
                      <>
                        <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                        <span>Deleting...</span>
                      </>
                    ) : (
                      <>
                        <Trash2 className="h-3.5 w-3.5" />
                        <span>Delete Permanently</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <Footer />
    </div>
  );
}
