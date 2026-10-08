'use client';

import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import {
  FileText,
  Upload,
  CheckCircle2,
  AlertTriangle,
  Copy,
  Check,
  Download,
  Layers,
  Sparkles,
  FileCheck,
  Eye,
  RefreshCw,
  Search,
  BookOpen,
  ArrowRight,
  ExternalLink,
} from 'lucide-react';
import { Navbar, Footer } from '@/components/layout/NavAndFooter';
import { API_BASE_URL } from '@/lib/config';

interface Block {
  text: string;
  confidence?: number | null;
  bbox: number[];
}

interface PageData {
  page_number: number;
  text: string;
  confidence?: number | null;
  blocks: Block[];
}

interface OCRResponse {
  document_id: string;
  filename: string;
  status: string;
  document_type: string;
  pages: number;
  extraction_method: string;
  text: string;
  pages_data: PageData[];
}

export default function OCRPage() {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<OCRResponse | null>(null);
  const [selectedPage, setSelectedPage] = useState<number>(1);
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState<'text' | 'blocks'>('text');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Legal Research Handoff States
  const [researchSending, setResearchSending] = useState(false);
  const [researchSent, setResearchSent] = useState(false);
  const [researchError, setResearchError] = useState<string | null>(null);
  const [researchDocId, setResearchDocId] = useState<string | null>(null);
  const [researchChunks, setResearchChunks] = useState<number>(0);

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
      setFile(e.dataTransfer.files[0]);
      setError(null);
      resetResearchState();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      resetResearchState();
    }
  };

  const resetResearchState = () => {
    setResearchSending(false);
    setResearchSent(false);
    setResearchError(null);
    setResearchDocId(null);
    setResearchChunks(0);
  };

  const handleProcessDocument = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    setResult(null);
    resetResearchState();

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/api/ocr/process`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        let errDetail = 'Failed to process document';
        try {
          const errData = await response.json();
          errDetail = errData.detail || errData.error || errDetail;
        } catch {
          // ignore json parse error
        }
        throw new Error(errDetail);
      }

      const data: OCRResponse = await response.json();
      setResult(data);
      setSelectedPage(1);
    } catch (err: any) {
      console.error('OCR processing error:', err);
      setError(err.message || 'An error occurred during OCR extraction.');
    } finally {
      setLoading(false);
    }
  };

  const handleSendToResearch = async () => {
    if (!result) return;

    setResearchSending(true);
    setResearchError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/ocr/send-to-research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: result.document_id,
          filename: result.filename,
          title: result.filename.replace(/\.[^/.]+$/, '').replace(/[_\\-]/g, ' '),
          document_type: result.document_type,
          pages: result.pages,
          extraction_method: result.extraction_method,
          text: result.text,
          pages_data: result.pages_data,
        }),
      });

      if (!response.ok) {
        let errDetail = 'Failed to index document in Legal Research';
        try {
          const errData = await response.json();
          errDetail = errData.detail || errData.error || errDetail;
        } catch {
          // ignore json error
        }
        throw new Error(errDetail);
      }

      const data = await response.json();
      setResearchSent(true);
      setResearchDocId(data.id || result.document_id);
      setResearchChunks(data.total_chunks || 1);
    } catch (err: any) {
      console.error('Send to Legal Research error:', err);
      setResearchError(
        err.message || 'Failed to send document to Legal Research. You can retry without re-running OCR.'
      );
    } finally {
      setResearchSending(false);
    }
  };

  const handleCopy = () => {
    if (!result) return;
    const textToCopy =
      viewMode === 'text' && result.pages_data.length > 0
        ? result.pages_data[selectedPage - 1]?.text || result.text
        : result.text;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!result) return;
    const blob = new Blob([result.text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${result.filename.replace(/\.[^/.]+$/, '')}_ocr_extracted.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const currentPageData =
    result?.pages_data && result.pages_data.length >= selectedPage
      ? result.pages_data[selectedPage - 1]
      : null;

  return (
    <div className="min-h-screen bg-[#0C0D0C] text-[#EDE8DC] flex flex-col selection:bg-[#B59A68]/30 selection:text-white">
      <Navbar />

      <main className="flex-1 pt-28 pb-20 px-6 max-w-7xl mx-auto w-full">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#3B3A33] bg-[#151716]/60 text-xs font-mono text-[#B59A68] uppercase tracking-wider mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            Legal Document Intelligence
          </div>
          <h1 className="font-display text-3xl sm:text-4xl md:text-5xl font-semibold tracking-tight text-[#EDE8DC]">
            Document OCR & Layout Analysis
          </h1>
          <p className="mt-3 text-stone-400 font-sans text-sm sm:text-base leading-relaxed">
            Extract text from court filings, judgments, affidavits, and scanned records with
            PaddleOCR, dual-column layout preservation, and reading-order reconstruction.
          </p>
        </div>

        {/* Upload & Workspace Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Upload, Controls and Handoff */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-[#151716] border border-[#3B3A33] rounded-2xl p-6 shadow-xl">
              <h2 className="font-display text-lg font-medium text-[#EDE8DC] mb-2 flex items-center gap-2">
                <Upload className="w-4 h-4 text-[#B59A68]" />
                Upload Court Document
              </h2>
              <p className="text-xs text-stone-400 mb-5">
                Supports PDF (digital, scanned, mixed), Word DOCX, and JPG/PNG documents up to 50MB.
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
                    : 'border-[#3B3A33] hover:border-[#B59A68]/50 bg-[#1A1C1B]'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.doc,.jpg,.jpeg,.png"
                  onChange={handleFileChange}
                  className="hidden"
                />

                <div className="mx-auto w-12 h-12 rounded-full bg-[#151716] border border-[#3B3A33] flex items-center justify-center mb-3 text-[#B59A68]">
                  <FileText className="w-6 h-6" />
                </div>

                {file ? (
                  <div>
                    <p className="text-sm font-medium text-[#EDE8DC] truncate max-w-xs mx-auto">
                      {file.name}
                    </p>
                    <p className="text-xs text-stone-400 mt-1">
                      {(file.size / (1024 * 1024)).toFixed(2)} MB • Ready for OCR
                    </p>
                  </div>
                ) : (
                  <div>
                    <p className="text-sm font-medium text-[#EDE8DC]">
                      Drag & drop your document here
                    </p>
                    <p className="text-xs text-stone-400 mt-1">or click to browse filesystem</p>
                  </div>
                )}
              </div>

              {/* Error Message */}
              {error && (
                <div className="mt-4 p-3 bg-red-950/40 border border-red-800/60 rounded-xl flex items-start gap-2 text-xs text-red-200">
                  <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              {/* Action Button */}
              <button
                onClick={handleProcessDocument}
                disabled={!file || loading}
                className={`w-full mt-6 py-3 px-4 rounded-xl font-medium text-sm transition-all duration-200 flex items-center justify-center gap-2 ${
                  !file || loading
                    ? 'bg-[#252826] text-stone-500 cursor-not-allowed'
                    : 'bg-[#B59A68] hover:bg-[#C8AD7B] text-[#0C0D0C] shadow-lg shadow-[#B59A68]/10 active:scale-[0.99]'
                }`}
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Running PaddleOCR Pipeline...</span>
                  </>
                ) : (
                  <>
                    <FileCheck className="w-4 h-4" />
                    <span>Process & Extract Legal Text</span>
                  </>
                )}
              </button>
            </div>

            {/* Document Metadata Summary Card */}
            {result && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-[#151716] border border-[#3B3A33] rounded-2xl p-6 shadow-xl space-y-4"
              >
                <div className="flex items-center justify-between pb-3 border-b border-[#3B3A33]">
                  <h3 className="font-display text-base font-medium text-[#EDE8DC] flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    Extraction Summary
                  </h3>
                  <span className="text-xs font-mono uppercase px-2.5 py-0.5 rounded-full bg-emerald-950/50 text-emerald-300 border border-emerald-800/50">
                    {result.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="bg-[#1A1C1B] p-3 rounded-xl border border-[#3B3A33]/50">
                    <span className="text-stone-400 block mb-1">Doc Classification</span>
                    <span className="font-mono text-[#EDE8DC] font-semibold uppercase">
                      {result.document_type}
                    </span>
                  </div>
                  <div className="bg-[#1A1C1B] p-3 rounded-xl border border-[#3B3A33]/50">
                    <span className="text-stone-400 block mb-1">Total Pages</span>
                    <span className="font-mono text-[#EDE8DC] font-semibold">{result.pages}</span>
                  </div>
                  <div className="bg-[#1A1C1B] p-3 rounded-xl border border-[#3B3A33]/50 col-span-2">
                    <span className="text-stone-400 block mb-1">OCR Method</span>
                    <span className="font-mono text-[#B59A68] font-semibold">
                      {result.extraction_method}
                    </span>
                  </div>
                </div>

                {/* Page Navigation */}
                {result.pages > 1 && (
                  <div className="pt-2">
                    <label className="text-xs text-stone-400 block mb-2">Select Page:</label>
                    <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto">
                      {Array.from({ length: result.pages }, (_, i) => i + 1).map((p) => (
                        <button
                          key={p}
                          onClick={() => setSelectedPage(p)}
                          className={`px-3 py-1 text-xs rounded-lg font-mono transition-colors ${
                            selectedPage === p
                              ? 'bg-[#B59A68] text-[#0C0D0C] font-bold'
                              : 'bg-[#1A1C1B] text-stone-300 hover:bg-[#252826] border border-[#3B3A33]/60'
                          }`}
                        >
                          P. {p}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            )}

            {/* Legal Research Handoff Box */}
            {result && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`border rounded-2xl p-6 shadow-xl transition-all duration-300 ${
                  researchSent
                    ? 'bg-[#151D18] border-emerald-800/60'
                    : 'bg-[#151716] border-[#3B3A33]'
                }`}
              >
                <div className="flex items-center justify-between pb-3 border-b border-[#3B3A33]/60">
                  <div className="flex items-center gap-2">
                    <BookOpen className={`w-4 h-4 ${researchSent ? 'text-emerald-400' : 'text-[#B59A68]'}`} />
                    <h3 className="font-display text-sm font-medium text-[#EDE8DC]">
                      Legal Research Integration
                    </h3>
                  </div>
                  {/* Status Indicator Badge */}
                  <span
                    className={`text-[11px] font-mono uppercase px-2.5 py-0.5 rounded-full border ${
                      researchSent
                        ? 'bg-emerald-950/60 text-emerald-300 border-emerald-700/60'
                        : researchSending
                        ? 'bg-[#B59A68]/20 text-[#B59A68] border-[#B59A68]/40 animate-pulse'
                        : researchError
                        ? 'bg-amber-950/50 text-amber-300 border-amber-800/50'
                        : 'bg-[#1A1C1B] text-stone-400 border-[#3B3A33]'
                    }`}
                  >
                    {researchSent
                      ? 'Ready for Legal Research'
                      : researchSending
                      ? 'Sending to Legal Research'
                      : researchError
                      ? 'Ingestion Error'
                      : 'OCR Complete'}
                  </span>
                </div>

                <div className="mt-4">
                  {researchSent ? (
                    <div className="space-y-4">
                      <div className="p-3 bg-emerald-950/30 border border-emerald-800/40 rounded-xl text-xs text-emerald-200">
                        <p className="font-medium flex items-center gap-1.5">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                          Document successfully indexed into 3-Level RAG!
                        </p>
                        <p className="mt-1 text-emerald-300/80">
                          {researchChunks} chunks created with page-level citations. You can now conduct citation-grounded research on this exact document without re-uploading.
                        </p>
                      </div>

                      <Link
                        href={`/legal-research?docId=${encodeURIComponent(researchDocId || result.document_id)}`}
                        className="w-full py-3 px-4 rounded-xl font-medium text-sm transition-all duration-200 flex items-center justify-center gap-2 bg-[#B59A68] hover:bg-[#C8AD7B] text-[#0C0D0C] shadow-lg shadow-[#B59A68]/20 active:scale-[0.99]"
                      >
                        <BookOpen className="w-4 h-4" />
                        <span>Open in Legal Research</span>
                        <ArrowRight className="w-4 h-4" />
                      </Link>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <p className="text-xs text-stone-400 leading-relaxed">
                        Handoff this extracted legal text directly to NyayaSarathi&apos;s Legal Research engine for citation-backed question answering and statutory analysis without uploading again.
                      </p>

                      {researchError && (
                        <div className="p-3 bg-amber-950/40 border border-amber-800/60 rounded-xl flex items-start gap-2 text-xs text-amber-200">
                          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                          <div>
                            <span className="font-semibold block">Handoff Failed:</span>
                            <span>{researchError}</span>
                          </div>
                        </div>
                      )}

                      <button
                        onClick={handleSendToResearch}
                        disabled={researchSending}
                        className={`w-full py-3 px-4 rounded-xl font-medium text-sm transition-all duration-200 flex items-center justify-center gap-2 ${
                          researchSending
                            ? 'bg-[#252826] text-stone-400 cursor-not-allowed'
                            : 'bg-[#B59A68] hover:bg-[#C8AD7B] text-[#0C0D0C] shadow-lg shadow-[#B59A68]/15 active:scale-[0.99]'
                        }`}
                      >
                        {researchSending ? (
                          <>
                            <RefreshCw className="w-4 h-4 animate-spin text-[#B59A68]" />
                            <span>Indexing in RAG Pipeline...</span>
                          </>
                        ) : researchError ? (
                          <>
                            <RefreshCw className="w-4 h-4" />
                            <span>Retry Send to Legal Research</span>
                          </>
                        ) : (
                          <>
                            <BookOpen className="w-4 h-4" />
                            <span>Send to Legal Research</span>
                            <ArrowRight className="w-4 h-4" />
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </div>

          {/* Right Column: Output Viewer */}
          <div className="lg:col-span-7">
            <div className="bg-[#151716] border border-[#3B3A33] rounded-2xl p-6 shadow-xl flex flex-col h-full min-h-[580px]">
              {/* Output Header */}
              <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#3B3A33]">
                <div className="flex items-center gap-3">
                  <span className="font-display text-lg font-medium text-[#EDE8DC]">
                    Extracted Text & Reading Order
                  </span>
                  {result && (
                    <span className="text-xs text-stone-400 font-mono">
                      (Page {selectedPage} of {result.pages})
                    </span>
                  )}
                </div>

                {result && (
                  <div className="flex items-center gap-2">
                    {/* View mode toggle */}
                    <div className="flex bg-[#1A1C1B] border border-[#3B3A33] rounded-lg p-0.5">
                      <button
                        onClick={() => setViewMode('text')}
                        className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors ${
                          viewMode === 'text'
                            ? 'bg-[#B59A68] text-[#0C0D0C]'
                            : 'text-stone-400 hover:text-[#EDE8DC]'
                        }`}
                      >
                        Reading Order
                      </button>
                      <button
                        onClick={() => setViewMode('blocks')}
                        className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors ${
                          viewMode === 'blocks'
                            ? 'bg-[#B59A68] text-[#0C0D0C]'
                            : 'text-stone-400 hover:text-[#EDE8DC]'
                        }`}
                      >
                        BBoxes ({currentPageData?.blocks?.length || 0})
                      </button>
                    </div>

                    <button
                      onClick={handleCopy}
                      className="p-1.5 rounded-lg border border-[#3B3A33] bg-[#1A1C1B] text-stone-300 hover:text-white hover:border-[#B59A68]/50 transition-colors"
                      title="Copy text"
                    >
                      {copied ? (
                        <Check className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </button>

                    <button
                      onClick={handleDownload}
                      className="p-1.5 rounded-lg border border-[#3B3A33] bg-[#1A1C1B] text-stone-300 hover:text-white hover:border-[#B59A68]/50 transition-colors"
                      title="Download as TXT"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>

              {/* Content Body */}
              <div className="flex-1 mt-4">
                {loading ? (
                  <div className="h-full flex flex-col items-center justify-center py-20 text-center">
                    <RefreshCw className="w-8 h-8 text-[#B59A68] animate-spin mb-4" />
                    <p className="text-sm font-medium text-[#EDE8DC]">
                      Extracting Document Text & Layout...
                    </p>
                    <p className="text-xs text-stone-400 max-w-sm mt-1">
                      Applying OpenCV preprocessing, PaddleOCR line detection, and column-aware
                      reading-order reconstruction.
                    </p>
                  </div>
                ) : result ? (
                  viewMode === 'text' ? (
                    <div className="relative">
                      {currentPageData?.confidence !== null &&
                        currentPageData?.confidence !== undefined && (
                          <div className="mb-3 px-3 py-1.5 rounded-lg bg-[#1A1C1B] border border-[#3B3A33] inline-flex items-center gap-2 text-xs font-mono text-[#B59A68]">
                            <span>Avg OCR Confidence:</span>
                            <span className="font-bold">
                              {(currentPageData.confidence * 100).toFixed(1)}%
                            </span>
                          </div>
                        )}
                      <textarea
                        readOnly
                        value={currentPageData?.text || result.text}
                        className="w-full h-[460px] p-4 bg-[#101211] border border-[#3B3A33]/70 rounded-xl text-stone-200 font-mono text-xs leading-relaxed resize-none focus:outline-none focus:border-[#B59A68]/40"
                      />
                    </div>
                  ) : (
                    <div className="h-[460px] overflow-y-auto space-y-2 pr-1">
                      {currentPageData?.blocks && currentPageData.blocks.length > 0 ? (
                        currentPageData.blocks.map((block, idx) => (
                          <div
                            key={idx}
                            className="p-3 bg-[#1A1C1B] border border-[#3B3A33]/50 rounded-xl flex flex-col gap-1.5 text-xs hover:border-[#B59A68]/40 transition-colors"
                          >
                            <div className="flex items-center justify-between text-[11px] font-mono text-stone-400">
                              <span className="text-[#B59A68]">Block #{idx + 1}</span>
                              <span className="bg-[#151716] px-2 py-0.5 rounded border border-[#3B3A33]">
                                bbox: [{block.bbox.join(', ')}]
                              </span>
                              {block.confidence !== undefined && block.confidence !== null && (
                                <span className="text-emerald-400">
                                  {(block.confidence * 100).toFixed(1)}%
                                </span>
                              )}
                            </div>
                            <p className="text-stone-200 font-mono text-xs mt-0.5 whitespace-pre-wrap">
                              {block.text}
                            </p>
                          </div>
                        ))
                      ) : (
                        <div className="text-center py-16 text-stone-500 text-xs">
                          No discrete bounding boxes recorded for this page.
                        </div>
                      )}
                    </div>
                  )
                ) : (
                  <div className="h-full flex flex-col items-center justify-center py-24 text-center">
                    <div className="w-12 h-12 rounded-full bg-[#1A1C1B] border border-[#3B3A33] flex items-center justify-center mb-3 text-stone-500">
                      <Layers className="w-5 h-5" />
                    </div>
                    <p className="text-sm font-medium text-stone-400">No Document Processed Yet</p>
                    <p className="text-xs text-stone-500 max-w-xs mt-1">
                      Upload a legal filing or scanned judgment on the left to inspect reconstructed
                      text and bounding boxes.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
