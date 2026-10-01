

'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Scale,
  Sparkles,
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
      const res = await fetch('http://localhost:8000/api/qa/documents');
      if (res.ok) {
        const data = await res.json();
        const docs: DocumentItem[] = data.documents || [];
        setDocuments(docs);
        // By default select all indexed documents if none selected
        if (docs.length > 0 && selectedDocIds.length === 0) {
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
      const res = await fetch(`http://localhost:8000/api/qa/documents/${targetId}`, {
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
      const res = await fetch('http://localhost:8000/api/qa/ask', {
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

      const res = await fetch('http://localhost:8000/api/qa/documents/upload', {
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

  // Render clickable citation markers inside the answer text
  const renderAnswerText = (text: string, citations: CitationItem[]) => {
    const parts = text.split(/(\[S\d+\])/g);
    return parts.map((part, index) => {
      const match = part.match(/\[(S\d+)\]/);
      if (match) {
        const sourceId = match[1];
        const cit = citations.find(c => c.source_id.toUpperCase() === sourceId.toUpperCase());
        const isSelected = activeCitation?.source_id.toUpperCase() === sourceId.toUpperCase();

        return (
          <button
            key={index}
            type="button"
            onClick={() => cit && selectCitation(cit)}
            className={`inline-flex items-center gap-1 mx-1 px-1.5 py-0.5 rounded text-xs font-semibold tracking-wider transition-all duration-200 ${
              isSelected
                ? 'bg-[#B59A68] text-[#151716] shadow-[0_0_12px_rgba(181,154,104,0.5)] scale-105'
                : 'bg-[#B59A68]/20 text-[#B59A68] border border-[#B59A68]/40 hover:bg-[#B59A68]/35 hover:scale-105'
            }`}
            title={cit ? `${cit.document_title} (Page ${cit.page_number})` : 'Citation marker'}
          >
            <span>[{sourceId}]</span>
          </button>
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  return (
    <div className="min-h-screen bg-[#151716] text-[#F4EFE5] flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 pt-28 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        {/* Header Banner */}
        <div className="mb-8 border-b border-[#3B3A33]/70 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-[#B59A68]/30 bg-[#1D211F]/80 px-3 py-1 text-xs font-medium text-[#B59A68] mb-3">
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>Evidence-Grounded Legal Research Workspace</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-display font-semibold text-[#F4EFE5] tracking-tight">
              AI Legal Research & Citations
            </h1>
            <p className="mt-2 text-sm text-[#A9A49A] max-w-2xl">
              Query your indexed judicial records, orders, and contracts with mathematically grounded hybrid retrieval.
              Every statement is tethered directly to authentic paragraph and page coordinates.
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
                    <Sparkles className="h-3 w-3 text-[#B59A68]" /> Suggested:
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

            {/* Answer Display Card */}
            {result && (
              <div className="rounded-xl border border-[#3B3A33] bg-[#1D211F] p-6 shadow-xl flex flex-col gap-5">
                
                {/* Answer Meta Bar */}
                <div className="flex items-center justify-between pb-4 border-b border-[#3B3A33]/60">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-[#B59A68]" />
                    <span className="text-xs font-semibold uppercase tracking-wider text-[#A9A49A]">
                      Grounded Answer
                    </span>
                    <span className="text-[11px] rounded bg-[#151716] px-2 py-0.5 text-[#B59A68] border border-[#3B3A33]">
                      {result.provider} · {result.model}
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={handleCopyAnswer}
                    className="inline-flex items-center gap-1.5 text-xs text-[#A9A49A] hover:text-[#F4EFE5] transition-colors"
                  >
                    {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                    <span>{copied ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>

                {/* Insufficient Evidence Warning Banner */}
                {result.insufficient_evidence && (
                  <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-3 text-xs text-amber-200 flex items-start gap-2.5">
                    <Info className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold">Insufficient Document Evidence Detected:</span>
                      <p className="mt-0.5 text-amber-200/80">
                        The retrieved corpus does not contain unambiguous factual evidence to fully answer your question. The model has refrained from guessing.
                      </p>
                    </div>
                  </div>
                )}

                {/* Body of the Answer with Interactive Citation Tags */}
                <div className="text-sm leading-relaxed text-[#F4EFE5]/90 space-y-3 font-sans">
                  {renderAnswerText(result.answer, result.citations)}
                </div>

                {/* Citation Cards Strip */}
                {result.citations && result.citations.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-[#3B3A33]/70">
                    <div className="text-xs font-semibold uppercase tracking-wider text-[#A9A49A] mb-3 flex items-center justify-between">
                      <span>Verifiable Supporting Citations ({result.citations.length})</span>
                      <span className="text-[11px] text-[#A9A49A]/60">click to inspect source passage</span>
                    </div>

                    <div className="flex flex-col gap-2">
                      {result.citations.map((cit) => {
                        const isSelected = activeCitation?.source_id === cit.source_id;
                        return (
                          <div
                            key={cit.source_id}
                            onClick={() => selectCitation(cit)}
                            className={`cursor-pointer rounded-lg border p-3 transition-all ${
                              isSelected
                                ? 'border-[#B59A68] bg-[#B59A68]/10 shadow-md'
                                : 'border-[#3B3A33]/70 bg-[#151716]/60 hover:border-[#B59A68]/50 hover:bg-[#151716]'
                            }`}
                          >
                            <div className="flex items-center justify-between mb-1">
                              <div className="flex items-center gap-2">
                                <span className="rounded bg-[#B59A68] text-[#151716] font-bold text-xs px-2 py-0.5">
                                  [{cit.source_id}]
                                </span>
                                <span className="font-medium text-xs text-[#F4EFE5]">
                                  {cit.document_title}
                                </span>
                              </div>
                              <span className="text-[11px] text-[#A9A49A] font-mono">
                                Page {cit.page_number} · Para {cit.paragraph_number}
                              </span>
                            </div>

                            <p className="text-xs text-[#A9A49A] line-clamp-2 italic font-serif pl-2 border-l-2 border-[#B59A68]/40 mt-1.5">
                              "{cit.excerpt}"
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* RIGHT PANEL: Source Document & Exact Paragraph Inspector (Col 8-12) */}
          <div className={`lg:col-span-5 flex flex-col gap-4 ${activeTab === 'answer' ? 'hidden md:flex' : 'flex'}`}>
            <div className="rounded-xl border border-[#3B3A33] bg-[#1D211F] p-5 shadow-xl min-h-[500px] flex flex-col sticky top-28">
              
              {/* Header Bar */}
              <div className="flex items-center justify-between pb-3 border-b border-[#3B3A33]/70">
                <div className="flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-[#B59A68]" />
                  <span className="text-xs font-semibold uppercase tracking-wider text-[#A9A49A]">
                    Source Evidence Inspector
                  </span>
                </div>

                {activeCitation && (
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={() => setViewMode('excerpt')}
                      className={`text-[11px] px-2.5 py-1 rounded transition-colors ${
                        viewMode === 'excerpt'
                          ? 'bg-[#B59A68] text-[#151716] font-semibold'
                          : 'text-[#A9A49A] hover:text-[#F4EFE5]'
                      }`}
                    >
                      Excerpt
                    </button>
                    <button
                      type="button"
                      onClick={() => setViewMode('pdf')}
                      className={`text-[11px] px-2.5 py-1 rounded transition-colors ${
                        viewMode === 'pdf'
                          ? 'bg-[#B59A68] text-[#151716] font-semibold'
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
                  <p className="text-xs text-[#A9A49A] mt-1 max-w-xs">
                    Ask a legal question and click any <span className="text-[#B59A68] font-semibold">[S1]</span> citation marker in the answer to inspect authentic source text.
                  </p>
                </div>
              ) : viewMode === 'excerpt' ? (
                <div className="flex-1 flex flex-col gap-4 pt-4">
                  {/* Active Source Title & Meta */}
                  <div className="rounded-lg bg-[#151716] p-3 border border-[#3B3A33]/70">
                    <div className="flex items-center justify-between mb-1">
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
                    <div className="flex items-center gap-3 text-xs text-[#A9A49A] mt-1">
                      <span>Page {activeCitation.page_number}</span>
                      <span>·</span>
                      <span>Paragraph {activeCitation.paragraph_number}</span>
                      {activeCitation.section_title && (
                        <>
                          <span>·</span>
                          <span className="text-[#B59A68]">{activeCitation.section_title}</span>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Verbatim Excerpt Reader */}
                  <div className="flex-1 rounded-lg bg-[#151716] p-4 border border-[#3B3A33]/70 overflow-y-auto max-h-[460px]">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-[#A9A49A]/70 mb-2 block">
                      Authentic Stored Paragraph Extract:
                    </span>
                    <p className="text-sm font-serif leading-relaxed text-[#F2EBDD] bg-[#B59A68]/10 p-3.5 rounded border-l-4 border-[#B59A68]">
                      "{activeCitation.excerpt}"
                    </p>
                  </div>

                  {/* Source Navigation Controls */}
                  {result && result.citations.length > 1 && (
                    <div className="flex items-center justify-between pt-2 border-t border-[#3B3A33]/50">
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
                          className="p-1 rounded border border-[#3B3A33] hover:border-[#B59A68] text-[#A9A49A] hover:text-[#F4EFE5] transition-colors"
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
                          className="p-1 rounded border border-[#3B3A33] hover:border-[#B59A68] text-[#A9A49A] hover:text-[#F4EFE5] transition-colors"
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
                <div className="flex-1 flex flex-col pt-3 min-h-[440px]">
                  <div className="flex items-center justify-between text-xs text-[#A9A49A] mb-2">
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
                        href={`http://localhost:8000/api/qa/documents/${activeCitation.document_id}/file`}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-[#B59A68] hover:underline"
                      >
                        <ExternalLink className="h-3 w-3" /> Full Screen
                      </a>
                    </div>
                  </div>
                  <iframe
                    src={`http://localhost:8000/api/qa/documents/${activeCitation.document_id}/file#page=${activeCitation.page_number}`}
                    className="w-full flex-1 min-h-[420px] rounded border border-[#3B3A33] bg-[#151716]"
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
