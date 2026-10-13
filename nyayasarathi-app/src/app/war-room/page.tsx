'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Scale,
  Shield,
  Swords,
  FileText,
  AlertTriangle,
  BookOpen,
  Search,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Download,
  Plus,
  Trash2,
  Edit3,
  RefreshCw,
  FolderOpen,
  Check,
  Zap,
  ChevronDown,
  Layers,
  ArrowRight,
  Sparkles,
  Info,
  Clock,
  Eye,
  FileCheck,
  AlertOctagon,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import { Navbar, Footer } from '@/components/layout/NavAndFooter';
import { API_BASE_URL } from '@/lib/config';
import { getAuthHeaders } from '@/lib/auth';

interface WarRoomSession {
  id: string;
  title: string;
  description: string;
  case_type: string;
  jurisdiction: string;
  court: string;
  user_position: string;
  opposing_party: string;
  relevant_dates: Array<{ event_date: string; description: string; source_reference?: string }>;
  selected_doc_ids: string[];
  fact_sheet: any[];
  evidence_findings: any[];
  arguments: any[];
  opposition: any[];
  risks: any[];
  precedents: any[];
  report: Record<string, string>;
  version: number;
  created_at: string;
  updated_at: string;
}

interface DocumentItem {
  id: string;
  title: string;
  filename: string;
  file_type: string;
  total_pages: number;
  status: string;
}

type TabType = 'facts' | 'evidence' | 'arguments' | 'opposition' | 'precedents' | 'risks' | 'report';

const safeArray = (val: any): string[] => {
  if (!val) return [];
  if (Array.isArray(val)) return val.map((x) => (typeof x === 'object' ? JSON.stringify(x) : String(x))).filter(Boolean);
  if (typeof val === 'string') {
    const trimmed = val.trim();
    if (!trimmed) return [];
    if (trimmed.includes('\n')) {
      return trimmed.split('\n').map((s) => s.trim().replace(/^[-•*]\s*/, '')).filter(Boolean);
    }
    if (trimmed.includes(';')) {
      return trimmed.split(';').map((s) => s.trim()).filter(Boolean);
    }
    return [trimmed];
  }
  return [String(val)];
};

export default function WarRoomPage() {
  // Session states
  const [sessions, setSessions] = useState<WarRoomSession[]>([]);
  const [currentSession, setCurrentSession] = useState<WarRoomSession | null>(null);
  const [availableDocs, setAvailableDocs] = useState<DocumentItem[]>([]);
  const [activeTab, setActiveTab] = useState<TabType>('facts');

  // Loading & interaction states
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [analyzingOp, setAnalyzingOp] = useState<string | null>(null);
  const [savingSession, setSavingSession] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Modals & Drawers
  const [showNewModal, setShowNewModal] = useState(false);
  const [showDocModal, setShowDocModal] = useState(false);
  const [showAddFactModal, setShowAddFactModal] = useState(false);
  const [showAddArgModal, setShowAddArgModal] = useState(false);
  const [showSessionDropdown, setShowSessionDropdown] = useState(false);

  // Form states for new session
  const [newTitle, setNewTitle] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [newCaseType, setNewCaseType] = useState('bail');
  const [newCourt, setNewCourt] = useState('');
  const [newUserPosition, setNewUserPosition] = useState('applicant');
  const [newOpposingParty, setNewOpposingParty] = useState('');

  // Form states for new fact
  const [factText, setFactText] = useState('');
  const [factCategory, setFactCategory] = useState('established_fact');
  const [factDocTitle, setFactDocTitle] = useState('');
  const [factPage, setFactPage] = useState<number | ''>('');

  // Form states for new argument
  const [argTitle, setArgTitle] = useState('');
  const [argClaim, setArgClaim] = useState('');
  const [argProvisions, setArgProvisions] = useState('');
  const [argReasoning, setArgReasoning] = useState('');

  // Usage info
  const [lastUsageInfo, setLastUsageInfo] = useState<{
    cache_hit: boolean;
    provider: string;
    model: string;
    tokens_used: number;
    duration_ms: number;
  } | null>(null);

  // Load sessions and documents on mount
  useEffect(() => {
    fetchSessions();
    fetchDocuments();
  }, []);

  const fetchSessions = async () => {
    try {
      setLoadingSessions(true);
      const res = await fetch(`${API_BASE_URL}/api/war-room`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setSessions(data);
        if (data.length > 0) {
          setCurrentSession(data[0]);
        }
      }
    } catch (err: any) {
      console.error('Failed to fetch sessions', err);
      setErrorMsg('Could not load War Room sessions. Check backend connection.');
    } finally {
      setLoadingSessions(false);
    }
  };

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/qa/documents`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setAvailableDocs(data.documents || []);
      }
    } catch (err) {
      console.error('Failed to load documents', err);
    }
  };

  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    try {
      const res = await fetch(`${API_BASE_URL}/api/war-room`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          title: newTitle.trim(),
          description: newDescription.trim(),
          case_type: newCaseType,
          court: newCourt.trim(),
          user_position: newUserPosition,
          opposing_party: newOpposingParty.trim(),
          selected_doc_ids: [],
        }),
      });

      if (res.ok) {
        const session = await res.json();
        setSessions((prev) => [session, ...prev]);
        setCurrentSession(session);
        setShowNewModal(false);
        setNewTitle('');
        setNewDescription('');
      } else {
        setErrorMsg('Failed to create War Room session.');
      }
    } catch (err) {
      setErrorMsg('Network error while creating session.');
    }
  };

  const handleUpdateSession = async (updates: Partial<WarRoomSession>) => {
    if (!currentSession) return;
    try {
      setSavingSession(true);
      const res = await fetch(`${API_BASE_URL}/api/war-room/${currentSession.id}`, {
        method: 'PATCH',
        headers: getAuthHeaders(),
        body: JSON.stringify(updates),
      });

      if (res.ok) {
        const updated = await res.json();
        setCurrentSession(updated);
        setSessions((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 2000);
      }
    } catch (err) {
      setErrorMsg('Failed to save session updates.');
    } finally {
      setSavingSession(false);
    }
  };

  const handleRunAnalysis = async (operation: TabType, targetId?: string) => {
    if (!currentSession) return;
    setAnalyzingOp(operation);
    setErrorMsg(null);

    try {
      const res = await fetch(`${API_BASE_URL}/api/war-room/${currentSession.id}/analyze`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          operation,
          target_id: targetId,
          force_refresh: false,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setLastUsageInfo({
          cache_hit: data.cache_hit,
          provider: data.provider,
          model: data.model,
          tokens_used: data.tokens_used,
          duration_ms: data.duration_ms,
        });

        // Re-fetch updated session state
        const refreshed = await fetch(`${API_BASE_URL}/api/war-room/${currentSession.id}`, {
          headers: getAuthHeaders(),
        });
        if (refreshed.ok) {
          const updatedSession = await refreshed.json();
          setCurrentSession(updatedSession);
          setSessions((prev) => prev.map((s) => (s.id === updatedSession.id ? updatedSession : s)));
        }
      } else {
        const errData = await res.json();
        setErrorMsg(errData.detail || `Analysis for ${operation} failed.`);
      }
    } catch (err: any) {
      setErrorMsg(`Analysis request failed: ${err.message || 'Server error'}`);
    } finally {
      setAnalyzingOp(null);
    }
  };

  const handleDeleteSession = async (id: string) => {
    if (!confirm('Are you sure you want to delete this War Room case? This action cannot be undone.')) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/war-room/${id}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const remaining = sessions.filter((s) => s.id !== id);
        setSessions(remaining);
        setCurrentSession(remaining.length > 0 ? remaining[0] : null);
      }
    } catch (err) {
      setErrorMsg('Failed to delete session.');
    }
  };

  const handleExportReport = async () => {
    if (!currentSession) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/war-room/${currentSession.id}/export`, {
        method: 'POST',
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Strategy_Report_${currentSession.title.replace(/\s+/g, '_')}.md`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        alert('Please generate the strategy report first before exporting.');
      }
    } catch (err) {
      alert('Failed to export report.');
    }
  };

  const toggleDocumentSelection = (docId: string) => {
    if (!currentSession) return;
    const currentSelected = currentSession.selected_doc_ids || [];
    const newSelected = currentSelected.includes(docId)
      ? currentSelected.filter((id) => id !== docId)
      : [...currentSelected, docId];

    handleUpdateSession({ selected_doc_ids: newSelected });
  };

  const handleAddCustomFact = () => {
    if (!currentSession || !factText.trim()) return;
    const newFact = {
      id: `custom-fact-${Date.now()}`,
      fact: factText.trim(),
      category: factCategory,
      source_doc_title: factDocTitle.trim() || undefined,
      page_number: factPage ? Number(factPage) : undefined,
      confidence: 1.0,
      is_reviewed: true,
      is_custom: true,
    };
    const updatedFacts = [...(currentSession.fact_sheet || []), newFact];
    handleUpdateSession({ fact_sheet: updatedFacts });
    setFactText('');
    setFactDocTitle('');
    setFactPage('');
    setShowAddFactModal(false);
  };

  const handleDeleteFact = (factId: string) => {
    if (!currentSession) return;
    const updated = (currentSession.fact_sheet || []).filter((f: any) => f.id !== factId);
    handleUpdateSession({ fact_sheet: updated });
  };

  const handleToggleFactReviewed = (factId: string) => {
    if (!currentSession) return;
    const updated = (currentSession.fact_sheet || []).map((f: any) =>
      f.id === factId ? { ...f, is_reviewed: !f.is_reviewed } : f
    );
    handleUpdateSession({ fact_sheet: updated });
  };

  const handleAddCustomArgument = () => {
    if (!currentSession || !argTitle.trim() || !argClaim.trim()) return;
    const newArg = {
      id: `custom-arg-${Date.now()}`,
      title: argTitle.trim(),
      main_claim: argClaim.trim(),
      supporting_facts: [],
      evidence_refs: [],
      applicable_provisions: argProvisions.split(',').map((p) => p.trim()).filter(Boolean),
      relevant_precedents: [],
      legal_reasoning: argReasoning.trim() || 'Doctrinal argument submitted by counsel.',
      potential_weaknesses: [],
      questions_to_investigate: [],
      is_reviewed: true,
      is_custom: true,
      created_at: new Date().toISOString(),
    };
    const updatedArgs = [...(currentSession.arguments || []), newArg];
    handleUpdateSession({ arguments: updatedArgs });
    setArgTitle('');
    setArgClaim('');
    setArgProvisions('');
    setArgReasoning('');
    setShowAddArgModal(false);
  };

  const handleDeleteArgument = (argId: string) => {
    if (!currentSession) return;
    const updated = (currentSession.arguments || []).filter((a: any) => a.id !== argId);
    handleUpdateSession({ arguments: updated });
  };

  return (
    <div className="min-h-screen bg-ink text-ivory flex flex-col font-sans selection:bg-oxblood selection:text-ivory">
      <Navbar />

      {/* Main Content Area */}
      <main className="flex-1 pt-24 pb-16 px-4 md:px-8 max-w-7xl mx-auto w-full">

        {/* ── Top Bar & Case Switcher ────────────────────────────────────── */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-6 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-olive border border-border text-brass">
              <Swords className="h-6 w-6 text-brass" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-mono tracking-wider uppercase text-brass/80 font-semibold px-2 py-0.5 rounded bg-brass/10 border border-brass/20">
                  Legal War Room
                </span>
                <span className="text-xs text-stone">AI Case Strategy & Adversarial Simulation</span>
              </div>
              <div className="relative mt-1 flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setShowSessionDropdown(!showSessionDropdown)}
                  className="group flex items-center gap-2 text-xl md:text-2xl font-serif font-semibold text-ivory hover:text-brass transition-colors"
                >
                  <span>{currentSession ? currentSession.title : 'Select or Create a Case'}</span>
                  <ChevronDown className="h-4 w-4 text-stone group-hover:text-brass transition-colors" />
                </button>

                {/* Session Selector Dropdown */}
                {showSessionDropdown && (
                  <div className="absolute top-full left-0 mt-2 w-80 max-h-96 overflow-y-auto doc-scroll rounded-xl border border-border bg-charcoal shadow-2xl p-2 z-50">
                    <div className="px-3 py-2 text-xs font-mono text-stone border-b border-border/50 uppercase tracking-wider">
                      Active Case Workspaces
                    </div>
                    {sessions.map((s) => (
                      <button
                        key={s.id}
                        type="button"
                        onClick={() => {
                          setCurrentSession(s);
                          setShowSessionDropdown(false);
                        }}
                        className={`w-full text-left px-3 py-2.5 rounded-lg text-sm flex items-center justify-between transition-colors ${
                          currentSession?.id === s.id
                            ? 'bg-olive text-brass font-medium border border-brass/30'
                            : 'text-stone hover:text-ivory hover:bg-olive/50'
                        }`}
                      >
                        <span className="truncate pr-2">{s.title}</span>
                        <span className="text-[10px] font-mono text-stone shrink-0 uppercase">{s.case_type}</span>
                      </button>
                    ))}
                    {sessions.length === 0 && (
                      <div className="px-3 py-4 text-center text-xs text-stone">No cases yet.</div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Action buttons on top right */}
          <div className="flex items-center gap-2.5 flex-wrap">
            <button
              type="button"
              onClick={() => setShowNewModal(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold bg-olive hover:bg-oxblood text-ivory border border-border hover:border-oxblood-light transition-all shadow-sm"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>New Case</span>
            </button>

            <button
              type="button"
              onClick={() => setShowDocModal(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold bg-olive hover:bg-white/10 text-ivory border border-border transition-colors"
            >
              <FileText className="h-3.5 w-3.5 text-brass" />
              <span>
                Evidence Docs ({currentSession?.selected_doc_ids?.length || 0})
              </span>
            </button>

            {currentSession && (
              <button
                type="button"
                onClick={handleExportReport}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold bg-brass/15 hover:bg-brass/25 text-brass border border-brass/30 transition-colors"
                title="Download strategy brief as Markdown"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Export Brief</span>
              </button>
            )}

            {currentSession && (
              <button
                type="button"
                onClick={() => handleDeleteSession(currentSession.id)}
                className="p-2 rounded-lg text-stone/60 hover:text-red-400 hover:bg-red-950/20 transition-colors border border-transparent hover:border-red-900/40"
                title="Delete this War Room case"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>

        {/* ── Error Banner ────────────────────────────────────────────────── */}
        {errorMsg && (
          <div className="my-4 p-3.5 rounded-lg bg-red-950/40 border border-red-800/60 text-red-200 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-red-400 shrink-0" />
              <span>{errorMsg}</span>
            </div>
            <button
              type="button"
              onClick={() => setErrorMsg(null)}
              className="text-red-400 hover:text-red-200"
            >
              &times;
            </button>
          </div>
        )}

        {/* ── Case Context Strip ──────────────────────────────────────────── */}
        {currentSession && (
          <div className="mt-4 p-4 rounded-xl bg-charcoal border border-border flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="px-2.5 py-1 rounded bg-olive text-stone border border-border">
                Forum: <strong className="text-ivory font-medium">{currentSession.court || 'Court of Record'}</strong>
              </span>
              <span className="px-2.5 py-1 rounded bg-olive text-stone border border-border">
                Standing:{' '}
                <strong className="text-brass font-medium uppercase">{currentSession.user_position}</strong>
              </span>
              <span className="px-2.5 py-1 rounded bg-olive text-stone border border-border">
                Domain:{' '}
                <strong className="text-ivory font-medium uppercase">{currentSession.case_type}</strong>
              </span>
              {currentSession.opposing_party && (
                <span className="px-2.5 py-1 rounded bg-olive text-stone border border-border">
                  Opposing: <strong className="text-ivory font-medium">{currentSession.opposing_party}</strong>
                </span>
              )}
            </div>

            {/* Token & Cache Efficiency Badge */}
            <div className="flex items-center gap-2 text-[11px] font-mono text-stone/80 shrink-0">
              {lastUsageInfo ? (
                <span className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-olive/80 border border-border">
                  {lastUsageInfo.cache_hit ? (
                    <>
                      <Zap className="h-3 w-3 text-verdigris" />
                      <span className="text-verdigris font-semibold">Cached (0 tokens)</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-3 w-3 text-brass" />
                      <span>{lastUsageInfo.tokens_used} tokens ({lastUsageInfo.duration_ms}ms)</span>
                    </>
                  )}
                </span>
              ) : (
                <span className="flex items-center gap-1 text-stone/60">
                  <Shield className="h-3 w-3 text-verdigris" /> Grounded Analysis Engine
                </span>
              )}

              {saveSuccess && (
                <span className="text-verdigris flex items-center gap-1 font-sans text-xs">
                  <Check className="h-3 w-3" /> Saved
                </span>
              )}
            </div>
          </div>
        )}

        {/* ── 7 Functional Navigation Tabs ─────────────────────────────────── */}
        {currentSession && (
          <div className="mt-6 flex border-b border-border overflow-x-auto no-scrollbar scrollbar-none gap-1">
            {[
              { id: 'facts', label: 'Fact Sheet & Gaps', icon: FileCheck, count: currentSession.fact_sheet?.length },
              { id: 'evidence', label: 'Evidence Analyzer', icon: Search, count: currentSession.evidence_findings?.length },
              { id: 'arguments', label: 'Argument Builder', icon: Shield, count: currentSession.arguments?.length },
              { id: 'opposition', label: 'Opposition Simulator', icon: Swords, count: currentSession.opposition?.length },
              { id: 'precedents', label: 'Legal Precedents', icon: BookOpen, count: currentSession.precedents?.length },
              { id: 'risks', label: 'Risks & Hazards', icon: AlertOctagon, count: currentSession.risks?.length },
              { id: 'report', label: 'Strategy Report', icon: FileText, count: Object.keys(currentSession.report || {}).length ? 1 : 0 },
            ].map(({ id, label, icon: Icon, count }) => (
              <button
                key={id}
                type="button"
                onClick={() => setActiveTab(id as TabType)}
                className={`flex items-center gap-2 px-4 py-3 text-xs md:text-sm font-medium border-b-2 transition-all whitespace-nowrap ${
                  activeTab === id
                    ? 'border-brass text-brass bg-olive/30 font-semibold'
                    : 'border-transparent text-stone hover:text-ivory hover:border-border'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
                {typeof count === 'number' && count > 0 && (
                  <span className="ml-1 text-[10px] font-mono px-1.5 py-0.2 rounded bg-olive border border-border text-stone">
                    {count}
                  </span>
                )}
              </button>
            ))}
          </div>
        )}

        {/* ── Tab Content Views ────────────────────────────────────────────── */}
        {currentSession ? (
          <div className="mt-6">

            {/* TAB 1: FACT SHEET & GAPS */}
            {activeTab === 'facts' && (
              <div className="space-y-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl bg-charcoal border border-border">
                  <div>
                    <h3 className="font-serif text-lg font-semibold text-ivory">Case Facts & Evidentiary Categorization</h3>
                    <p className="text-xs text-stone mt-0.5">
                      Distinguishes established facts with document page links from unverified allegations and critical gaps.
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setShowAddFactModal(true)}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium bg-olive hover:bg-olive/80 text-ivory border border-border flex items-center gap-1.5"
                    >
                      <Plus className="h-3 w-3" /> Add Fact
                    </button>
                    <button
                      type="button"
                      onClick={() => handleRunAnalysis('facts')}
                      disabled={analyzingOp === 'facts'}
                      className="btn-oxblood px-4 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm"
                    >
                      <RefreshCw className={`h-3.5 w-3.5 ${analyzingOp === 'facts' ? 'animate-spin' : ''}`} />
                      <span>{analyzingOp === 'facts' ? 'Extracting Facts...' : 'Extract Grounded Facts'}</span>
                    </button>
                  </div>
                </div>

                {/* Case Narrative editor */}
                <div className="p-4 rounded-xl bg-charcoal border border-border">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-xs font-semibold text-stone uppercase font-mono tracking-wider">
                      Case Narrative & Pleadings
                    </label>
                    <button
                      type="button"
                      onClick={() => handleUpdateSession({ description: currentSession.description })}
                      disabled={savingSession}
                      className="text-xs text-brass hover:underline flex items-center gap-1"
                    >
                      <Edit3 className="h-3 w-3" /> Save Changes
                    </button>
                  </div>
                  <textarea
                    rows={4}
                    value={currentSession.description}
                    onChange={(e) => setCurrentSession({ ...currentSession, description: e.target.value })}
                    className="w-full bg-olive/50 rounded-lg p-3 text-xs md:text-sm text-ivory border border-border focus:border-brass/60 focus:outline-none leading-relaxed"
                    placeholder="Enter case summary, FIR allegations, notice background, or disputed contractual facts..."
                  />
                </div>

                {/* Fact items grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {currentSession.fact_sheet?.map((fact: any) => {
                    const cat = (fact.category || '').toLowerCase();
                    const isProcedural = cat === 'procedural_event';
                    const isFinding = cat === 'court_finding';
                    const isHolding = cat === 'final_holding';
                    const isDoc = cat === 'documentary_evidence';
                    const isWitness = cat === 'witness_testimony';
                    const isAllegation = cat === 'allegation' || cat === 'unverified_allegation';

                    const badgeStyle = isHolding
                      ? 'bg-purple-950/50 text-purple-200 border-purple-800'
                      : isFinding
                      ? 'bg-verdigris/20 text-verdigris border-verdigris/40'
                      : isProcedural
                      ? 'bg-sky-950/50 text-sky-300 border-sky-800'
                      : isDoc
                      ? 'bg-olive text-brass border-brass/40'
                      : isWitness
                      ? 'bg-amber-950/40 text-amber-200 border-amber-800'
                      : isAllegation
                      ? 'bg-oxblood/30 text-oxblood-light border-oxblood/50'
                      : 'bg-stone/20 text-stone border-border';

                    const borderStyle = isHolding
                      ? 'border-purple-800/60'
                      : isFinding
                      ? 'border-verdigris/40'
                      : isProcedural
                      ? 'border-sky-800/60'
                      : isDoc
                      ? 'border-brass/40'
                      : isAllegation
                      ? 'border-oxblood/40'
                      : 'border-border';

                    return (
                      <div
                        key={fact.id}
                        className={`p-4 rounded-xl bg-charcoal border transition-all ${borderStyle}`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex flex-wrap items-center gap-1.5">
                            <span
                              className={`text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded font-semibold border ${badgeStyle}`}
                            >
                              {fact.category.replace(/_/g, ' ')}
                            </span>
                            {fact.verification_status && (
                              <span className={`text-[9px] font-mono uppercase px-1.5 py-0.5 rounded border ${
                                fact.verification_status === 'verified_from_primary_record'
                                  ? 'bg-verdigris/15 text-verdigris border-verdigris/30'
                                  : 'bg-olive text-stone border-border'
                              }`}>
                                {fact.verification_status.replace(/_/g, ' ')}
                              </span>
                            )}
                          </div>

                          <div className="flex items-center gap-2">
                            <button
                              type="button"
                              onClick={() => handleToggleFactReviewed(fact.id)}
                              className={`p-1 rounded text-xs transition-colors ${
                                fact.is_reviewed ? 'text-verdigris' : 'text-stone/40 hover:text-stone'
                              }`}
                              title={fact.is_reviewed ? 'Reviewed' : 'Mark as reviewed'}
                            >
                              <CheckCircle2 className="h-4 w-4" />
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDeleteFact(fact.id)}
                              className="p-1 rounded text-stone/40 hover:text-red-400 transition-colors"
                              title="Delete fact"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        </div>

                        <p className="mt-2.5 text-xs md:text-sm text-ivory/90 leading-relaxed font-sans">
                          {fact.fact}
                        </p>

                        {/* Attribution metadata & Reliability */}
                        <div className="mt-3 pt-2 border-t border-border/50 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-stone">
                          <span className="flex items-center gap-1.5">
                            <FileText className="h-3 w-3 text-brass" />
                            <span className="truncate max-w-[200px]">{fact.source_doc_title || 'Case Record'}</span>
                            {fact.source_reliability && (
                              <span className="text-[10px] text-stone/60">({fact.source_reliability.replace(/_/g, ' ')})</span>
                            )}
                          </span>
                          {fact.page_number && (
                            <span className="px-1.5 py-0.5 rounded bg-olive border border-border text-ivory font-mono">
                              p. {fact.page_number}
                            </span>
                          )}
                        </div>

                        {fact.excerpt && (
                          <p className="mt-2 p-2 rounded bg-olive/40 border border-border/50 text-[11px] text-stone italic font-legal">
                            &ldquo;{fact.excerpt}&rdquo;
                          </p>
                        )}

                        {fact.verification_status === 'verification_required' && (
                          <div className="mt-2 py-1 px-2 rounded bg-amber-950/20 border border-amber-900/40 text-[10px] text-amber-300 flex items-center gap-1.5 font-mono">
                            <AlertTriangle className="h-3 w-3 shrink-0 text-amber-400" />
                            <span>Verification Required: Uncorroborated assertion. Excluded from definitive legal findings.</span>
                          </div>
                        )}
                      </div>
                    );
                  })}

                  {(!currentSession.fact_sheet || currentSession.fact_sheet.length === 0) && (
                    <div className="col-span-full p-10 rounded-xl bg-charcoal border border-dashed border-border text-center">
                      <FileCheck className="h-8 w-8 text-stone/40 mx-auto mb-2" />
                      <p className="text-sm font-medium text-stone">No fact items generated yet.</p>
                      <p className="text-xs text-stone/60 mt-1 max-w-md mx-auto">
                        Click &ldquo;Extract Grounded Facts&rdquo; above to extract categorized facts and verify documentary evidence against allegations.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 2: EVIDENCE ANALYZER */}
            {activeTab === 'evidence' && (
              <div className="space-y-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl bg-charcoal border border-border">
                  <div>
                    <h3 className="font-serif text-lg font-semibold text-ivory">Document Evidence Analyzer</h3>
                    <p className="text-xs text-stone mt-0.5">
                      Scans exhibits for documentary support, detects factual inconsistencies, and spots missing proof.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRunAnalysis('evidence')}
                    disabled={analyzingOp === 'evidence'}
                    className="btn-oxblood px-4 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${analyzingOp === 'evidence' ? 'animate-spin' : ''}`} />
                    <span>{analyzingOp === 'evidence' ? 'Analyzing Evidence...' : 'Analyze Evidence'}</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 gap-4">
                  {currentSession.evidence_findings?.map((ev: any) => (
                    <div key={ev.id} className="p-4 rounded-xl bg-charcoal border border-border">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-olive border border-border text-brass">
                            {ev.evidence_type?.replace(/_/g, ' ') || 'FINDING'}
                          </span>
                          {ev.evidentiary_status && (
                            <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded border ${
                              ev.evidentiary_status === 'established' || ev.evidentiary_status === 'corroborated_by_record'
                                ? 'bg-verdigris/15 text-verdigris border-verdigris/30'
                                : 'bg-amber-950/40 text-amber-300 border-amber-800'
                            }`}>
                              {ev.evidentiary_status.replace(/_/g, ' ')}
                            </span>
                          )}
                          {ev.legal_relevance && (
                            <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-olive/60 text-stone border border-border">
                              {ev.legal_relevance.replace(/_/g, ' ')}
                            </span>
                          )}
                          <span className="text-xs text-stone ml-1">Impacts:</span>
                          <span className="text-xs font-semibold text-ivory">{ev.relevant_claim}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {ev.source_reliability && (
                            <span className="text-[10px] font-mono text-stone/70">
                              [{ev.source_reliability.replace(/_/g, ' ')}]
                            </span>
                          )}
                          {ev.confidence && (
                            <span className="text-[10px] font-mono text-verdigris">
                              {Math.round(ev.confidence * 100)}% Extraction Conf.
                            </span>
                          )}
                        </div>
                      </div>

                      <p className="mt-3 text-sm text-ivory font-sans leading-relaxed">{ev.finding}</p>

                      {ev.excerpt && (
                        <blockquote className="mt-2.5 p-2.5 rounded bg-olive/50 border-l-2 border-brass text-xs font-legal italic text-stone">
                          &ldquo;{ev.excerpt}&rdquo;
                        </blockquote>
                      )}

                      {ev.follow_up_question && (
                        <div className="mt-3 p-2.5 rounded bg-oxblood/10 border border-oxblood/30 flex items-start gap-2">
                          <HelpCircle className="h-4 w-4 text-oxblood-light shrink-0 mt-0.5" />
                          <div>
                            <span className="text-[10px] font-mono uppercase text-oxblood-light font-semibold">
                              Trial / Cross-Examination Follow-up:
                            </span>
                            <p className="text-xs text-ivory/90 mt-0.5">{ev.follow_up_question}</p>
                          </div>
                        </div>
                      )}

                      {(ev.evidentiary_status === 'unsupported' || ev.evidentiary_status === 'verification_required' || ev.evidence_type === 'missing_document') && (
                        <div className="mt-2.5 py-1 px-2.5 rounded bg-amber-950/20 border border-amber-900/40 text-[10px] text-amber-300 flex items-center gap-1.5 font-mono">
                          <AlertTriangle className="h-3 w-3 shrink-0 text-amber-400" />
                          <span>Missing Document / Evidentiary Gap: Not provided in record. Tracked without presuming existence.</span>
                        </div>
                      )}
                    </div>
                  ))}

                  {(!currentSession.evidence_findings || currentSession.evidence_findings.length === 0) && (
                    <div className="p-10 rounded-xl bg-charcoal border border-dashed border-border text-center">
                      <Search className="h-8 w-8 text-stone/40 mx-auto mb-2" />
                      <p className="text-sm font-medium text-stone">No evidentiary findings analyzed yet.</p>
                      <p className="text-xs text-stone/60 mt-1 max-w-md mx-auto">
                        Click &ldquo;Analyze Evidence&rdquo; to assess the probative value of your documents and flag inconsistencies.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 3: ARGUMENT BUILDER */}
            {activeTab === 'arguments' && (
              <div className="space-y-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl bg-charcoal border border-border">
                  <div>
                    <h3 className="font-serif text-lg font-semibold text-ivory">Affirmative Argument Builder</h3>
                    <p className="text-xs text-stone mt-0.5">
                      Synthesizes structured legal arguments connecting factual exhibits with statutory provisions and judicial doctrine.
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setShowAddArgModal(true)}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium bg-olive hover:bg-olive/80 text-ivory border border-border flex items-center gap-1.5"
                    >
                      <Plus className="h-3 w-3" /> Custom Argument
                    </button>
                    <button
                      type="button"
                      onClick={() => handleRunAnalysis('arguments')}
                      disabled={analyzingOp === 'arguments'}
                      className="btn-oxblood px-4 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm"
                    >
                      <RefreshCw className={`h-3.5 w-3.5 ${analyzingOp === 'arguments' ? 'animate-spin' : ''}`} />
                      <span>{analyzingOp === 'arguments' ? 'Building Arguments...' : 'Build Arguments'}</span>
                    </button>
                  </div>
                </div>

                <div className="space-y-4">
                  {currentSession.arguments?.map((arg: any, idx: number) => (
                    <div key={arg.id || idx} className="p-5 rounded-xl bg-charcoal border border-border space-y-3">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-brass/15 text-brass border border-brass/30 font-semibold">
                              Argument #{idx + 1}
                            </span>
                            {arg.is_custom && (
                              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-olive text-stone">
                                Custom
                              </span>
                            )}
                          </div>
                          <h4 className="mt-1.5 font-serif text-base font-semibold text-ivory">{arg.title}</h4>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() => handleRunAnalysis('arguments', arg.id)}
                            className="p-1.5 rounded text-stone/50 hover:text-brass transition-colors"
                            title="Regenerate this argument"
                          >
                            <RefreshCw className="h-3.5 w-3.5" />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDeleteArgument(arg.id)}
                            className="p-1.5 rounded text-stone/50 hover:text-red-400 transition-colors"
                            title="Delete argument"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>

                      {/* Legal Issue */}
                      {arg.legal_issue && (
                        <div className="text-xs text-stone leading-relaxed bg-olive/20 p-2.5 rounded border border-border/40">
                          <strong className="text-brass font-mono uppercase text-[10px] block mb-0.5">Legal Issue:</strong>
                          <span>{arg.legal_issue}</span>
                        </div>
                      )}

                      <div className="p-3 rounded-lg bg-olive/40 border border-border text-xs md:text-sm text-ivory leading-relaxed font-sans">
                        <strong className="text-brass font-medium">Core Claim:</strong> {arg.main_claim}
                      </div>

                      {/* Procedural Role Argument */}
                      {arg.procedural_role_argument && (
                        <div className="p-2.5 rounded bg-verdigris/10 border border-verdigris/30 text-xs text-ivory leading-relaxed">
                          <strong className="text-verdigris font-mono uppercase text-[10px] block mb-0.5">Role Advocacy Argument:</strong>
                          {arg.procedural_role_argument}
                        </div>
                      )}

                      {/* Statutory provisions tags */}
                      {safeArray(arg.applicable_provisions).length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5 pt-1">
                          <span className="text-[10px] font-mono text-stone uppercase mr-1">Statutes:</span>
                          {safeArray(arg.applicable_provisions).map((prov: string, pIdx: number) => (
                            <span
                              key={pIdx}
                              className="text-[11px] font-mono px-2 py-0.5 rounded bg-olive border border-border text-ivory"
                            >
                              {prov}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Precedents relied upon */}
                      {safeArray(arg.relevant_precedents).length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span className="text-[10px] font-mono text-stone uppercase mr-1">Precedents:</span>
                          {safeArray(arg.relevant_precedents).map((prec: string, prIdx: number) => (
                            <span
                              key={prIdx}
                              className="text-[11px] font-serif italic px-2 py-0.5 rounded bg-brass/10 border border-brass/25 text-brass"
                            >
                              {prec}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Legal doctrinal reasoning */}
                      <div className="text-xs text-stone/90 leading-relaxed pt-1">
                        <strong className="text-ivory font-medium">Doctrinal Application:</strong> {arg.legal_reasoning}
                      </div>

                      {/* Evidence Still Required */}
                      {safeArray(arg.evidence_still_required).length > 0 && (
                        <div className="text-[11px] font-mono text-stone bg-olive/30 p-2 rounded border border-border/40">
                          <span className="text-brass font-semibold">Evidence Still Required:</span>{' '}
                          {safeArray(arg.evidence_still_required).join('; ')}
                        </div>
                      )}

                      {/* Strongest Opposing Argument & Rebuttal */}
                      {arg.strongest_opposing_argument && (
                        <div className="p-2.5 rounded bg-oxblood/10 border border-oxblood/30 text-xs text-ivory/90 space-y-1">
                          <div>
                            <strong className="text-oxblood-light font-mono uppercase text-[10px]">Strongest Counter-Argument:</strong>{' '}
                            <span>{arg.strongest_opposing_argument}</span>
                          </div>
                          {arg.rebuttal_and_weaknesses && (
                            <div className="pt-1 border-t border-oxblood/20">
                              <strong className="text-verdigris font-mono uppercase text-[10px]">Evidence-Based Rebuttal:</strong>{' '}
                              <span>{arg.rebuttal_and_weaknesses}</span>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Potential Vulnerabilities alert */}
                      {safeArray(arg.potential_weaknesses).length > 0 && (
                        <div className="mt-2 p-2.5 rounded bg-amber-950/20 border border-amber-800/40 text-xs text-amber-200/90 flex items-start gap-2">
                          <AlertTriangle className="h-3.5 w-3.5 text-amber-400 shrink-0 mt-0.5" />
                          <div>
                            <span className="font-semibold text-amber-300">Potential Counter-Attack:</span>{' '}
                            {safeArray(arg.potential_weaknesses).join('; ')}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}

                  {(!currentSession.arguments || currentSession.arguments.length === 0) && (
                    <div className="p-10 rounded-xl bg-charcoal border border-dashed border-border text-center">
                      <Shield className="h-8 w-8 text-stone/40 mx-auto mb-2" />
                      <p className="text-sm font-medium text-stone">No arguments constructed yet.</p>
                      <p className="text-xs text-stone/60 mt-1 max-w-md mx-auto">
                        Click &ldquo;Build Arguments&rdquo; to formulate affirmative points tailored to your standing as {currentSession.user_position}.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 4: OPPOSITION SIMULATOR (DEVIL'S ADVOCATE) */}
            {activeTab === 'opposition' && (
              <div className="space-y-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl bg-charcoal border border-border">
                  <div>
                    <h3 className="font-serif text-lg font-semibold text-ivory">Opposition Simulator (Devil&apos;s Advocate)</h3>
                    <p className="text-xs text-stone mt-0.5">
                      Stress-tests your strategy from opposing counsel&apos;s perspective. Uncovers hostile precedents and exposes soft spots.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRunAnalysis('opposition')}
                    disabled={analyzingOp === 'opposition'}
                    className="btn-oxblood px-4 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${analyzingOp === 'opposition' ? 'animate-spin' : ''}`} />
                    <span>{analyzingOp === 'opposition' ? 'Simulating...' : 'Run Devil&apos;s Advocate Simulation'}</span>
                  </button>
                </div>

                <div className="space-y-4">
                  {currentSession.opposition?.map((opp: any, idx: number) => (
                    <div key={opp.id || idx} className="p-5 rounded-xl bg-charcoal border border-oxblood/40 space-y-3">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-oxblood/30 text-oxblood-light border border-oxblood/50 font-semibold">
                          Hostile Contention #{idx + 1}
                        </span>
                        <span className="text-xs text-stone">Anticipated Opposing Stance</span>
                      </div>

                      <h4 className="font-serif text-base font-semibold text-ivory">{opp.opposing_claim}</h4>

                      {/* Weaknesses in user position */}
                      {safeArray(opp.user_position_weaknesses).length > 0 && (
                        <div className="p-3 rounded-lg bg-olive/50 border border-border text-xs text-stone leading-relaxed">
                          <strong className="text-oxblood-light font-medium">Vulnerability in Client Case:</strong>{' '}
                          {safeArray(opp.user_position_weaknesses).join('; ')}
                        </div>
                      )}

                      {/* Hostile precedents */}
                      {safeArray(opp.adverse_precedents).length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span className="text-[10px] font-mono text-stone uppercase mr-1">Hostile Authorities:</span>
                          {safeArray(opp.adverse_precedents).map((ap: string, apIdx: number) => (
                            <span
                              key={apIdx}
                              className="text-[11px] font-serif italic px-2 py-0.5 rounded bg-red-950/40 border border-red-900/60 text-red-200"
                            >
                              {ap}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Suggested Rebuttals */}
                      {safeArray(opp.suggested_rebuttal_counterarguments).length > 0 && (
                        <div className="p-3 rounded-lg bg-verdigris/10 border border-verdigris/30 text-xs text-ivory flex items-start gap-2">
                          <CheckCircle2 className="h-4 w-4 text-verdigris shrink-0 mt-0.5" />
                          <div>
                            <span className="font-semibold text-verdigris uppercase font-mono text-[10px]">
                              Recommended Counter-Rebuttal:
                            </span>
                            <p className="mt-0.5">{safeArray(opp.suggested_rebuttal_counterarguments).join('; ')}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}

                  {(!currentSession.opposition || currentSession.opposition.length === 0) && (
                    <div className="p-10 rounded-xl bg-charcoal border border-dashed border-border text-center">
                      <Swords className="h-8 w-8 text-stone/40 mx-auto mb-2" />
                      <p className="text-sm font-medium text-stone">No opposition arguments simulated yet.</p>
                      <p className="text-xs text-stone/60 mt-1 max-w-md mx-auto">
                        Click &ldquo;Run Devil&apos;s Advocate Simulation&rdquo; to test your affirmative arguments against expected adversarial tactics.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 5: LEGAL PRECEDENT RESEARCH */}
            {activeTab === 'precedents' && (
              <div className="space-y-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl bg-charcoal border border-border">
                  <div>
                    <h3 className="font-serif text-lg font-semibold text-ivory">Judicial Precedent Retrieval</h3>
                    <p className="text-xs text-stone mt-0.5">
                      Queries 740+ authentic High Court & Supreme Court judgments from database with real CNRs, dates, and verbatim holding excerpts.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRunAnalysis('precedents')}
                    disabled={analyzingOp === 'precedents'}
                    className="btn-oxblood px-4 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${analyzingOp === 'precedents' ? 'animate-spin' : ''}`} />
                    <span>{analyzingOp === 'precedents' ? 'Searching Authorities...' : 'Search Precedents'}</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {currentSession.precedents?.map((prec: any, idx: number) => {
                    const isSupporting = prec.outcome_type === 'supporting';
                    const isAdverse = prec.outcome_type === 'adverse';

                    return (
                      <div
                        key={idx}
                        className={`p-4 rounded-xl bg-charcoal border transition-all ${
                          isSupporting
                            ? 'border-verdigris/40'
                            : isAdverse
                            ? 'border-oxblood/50'
                            : 'border-border'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <div className="flex flex-wrap items-center gap-1.5">
                              <span
                                className={`text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded font-semibold ${
                                  isSupporting
                                    ? 'bg-verdigris/20 text-verdigris border border-verdigris/30'
                                    : isAdverse
                                    ? 'bg-oxblood/20 text-oxblood-light border border-oxblood/40'
                                    : 'bg-olive text-stone border border-border'
                                }`}
                              >
                                {prec.outcome_type.toUpperCase()} PRECEDENT
                              </span>
                              {prec.verification_status && (
                                <span className={`text-[9px] font-mono uppercase px-1.5 py-0.5 rounded border ${
                                  prec.verification_status === 'verified_primary_source'
                                    ? 'bg-verdigris/15 text-verdigris border-verdigris/30'
                                    : 'bg-amber-950/40 text-amber-300 border-amber-800'
                                }`}>
                                  {prec.verification_status.replace(/_/g, ' ')}
                                </span>
                              )}
                            </div>
                            <h4 className="mt-2 font-serif text-sm font-semibold text-ivory">{prec.title}</h4>
                            {prec.citation && (
                              <span className="text-[11px] font-mono text-brass block mt-0.5">{prec.citation}</span>
                            )}
                          </div>

                          <span className="text-[10px] font-mono text-stone px-1.5 py-0.5 rounded bg-olive border border-border shrink-0">
                            {prec.decision_date || 'Date N/A'}
                          </span>
                        </div>

                        {prec.legal_issue && (
                          <div className="mt-2 text-xs text-stone font-sans">
                            <strong className="text-ivory/80 font-medium font-mono text-[10px] uppercase block">Legal Issue:</strong>
                            <p className="text-xs text-ivory/90 mt-0.5">{prec.legal_issue}</p>
                          </div>
                        )}

                        {prec.actual_holding && (
                          <div className="mt-2 p-2 rounded bg-olive/30 border border-border/50 text-xs text-ivory/90 font-sans">
                            <strong className="text-brass font-mono uppercase text-[10px] block">Judicial Holding:</strong>
                            <p className="mt-0.5">{prec.actual_holding}</p>
                            {prec.relevant_paragraphs && (
                              <span className="text-[10px] font-mono text-stone/70 block mt-1">Pinpoint: {prec.relevant_paragraphs}</span>
                            )}
                          </div>
                        )}

                        <div className="mt-2 flex items-center gap-2 text-xs text-stone font-sans">
                          <span>{prec.court}</span>
                          <span>&bull;</span>
                          <span className="font-mono text-brass text-[11px]">CNR: {prec.cnr}</span>
                        </div>

                        {/* Verbatim quote */}
                        <blockquote className="mt-2.5 p-2.5 rounded bg-olive/40 border border-border text-xs font-legal italic text-stone/90 leading-relaxed">
                          &ldquo;{prec.verbatim_excerpt}&rdquo;
                        </blockquote>

                        <p className="mt-2.5 text-xs text-stone font-sans leading-relaxed">
                          <strong className="text-ivory font-medium">Relevance:</strong> {prec.relevance_explanation}
                        </p>

                        {prec.verification_status !== 'verified_primary_source' && (
                          <div className="mt-2.5 py-1.5 px-2.5 rounded bg-amber-950/20 border border-amber-900/50 text-[11px] text-amber-300 flex items-center gap-1.5 font-mono">
                            <AlertTriangle className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                            <span>Verification Required: Authority not verified in primary Supreme Court repository.</span>
                          </div>
                        )}

                        <div className="mt-3 pt-2 border-t border-border/50 flex items-center justify-between text-[11px] text-stone">
                          <span className="font-mono text-stone/70">{prec.binding_persuasive_nature}</span>
                          {prec.source_url && (
                            <a
                              href={prec.source_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-brass hover:underline flex items-center gap-1 text-[11px]"
                            >
                              eCourts / Supreme Court Link <ExternalLink className="h-2.5 w-2.5" />
                            </a>
                          )}
                        </div>
                      </div>
                    );
                  })}

                  {(!currentSession.precedents || currentSession.precedents.length === 0) && (
                    <div className="col-span-full p-10 rounded-xl bg-charcoal border border-dashed border-border text-center">
                      <BookOpen className="h-8 w-8 text-stone/40 mx-auto mb-2" />
                      <p className="text-sm font-medium text-stone">No precedents retrieved yet.</p>
                      <p className="text-xs text-stone/60 mt-1 max-w-md mx-auto">
                        Click &ldquo;Search Precedents&rdquo; to retrieve verified Indian judicial rulings matched to your case issues.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 6: RISKS & HAZARDS */}
            {activeTab === 'risks' && (
              <div className="space-y-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl bg-charcoal border border-border">
                  <div>
                    <h3 className="font-serif text-lg font-semibold text-ivory">Risks & Vulnerabilities Matrix</h3>
                    <p className="text-xs text-stone mt-0.5">
                      Evaluates unsupported arguments, evidentiary gaps, and matters requiring formal legal review.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRunAnalysis('risks')}
                    disabled={analyzingOp === 'risks'}
                    className="btn-oxblood px-4 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${analyzingOp === 'risks' ? 'animate-spin' : ''}`} />
                    <span>{analyzingOp === 'risks' ? 'Assessing Risks...' : 'Assess Case Risks'}</span>
                  </button>
                </div>

                <div className="space-y-4">
                  {currentSession.risks?.map((r: any, idx: number) => {
                    const isHigh = r.severity === 'high';
                    return (
                      <div
                        key={r.id || idx}
                        className={`p-4 rounded-xl bg-charcoal border transition-all ${
                          isHigh ? 'border-red-900/60 bg-red-950/10' : 'border-border'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <span
                              className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded font-semibold ${
                                isHigh
                                  ? 'bg-red-950/50 text-red-300 border border-red-800'
                                  : 'bg-olive text-stone border border-border'
                              }`}
                            >
                              {r.severity} Risk
                            </span>
                            <span className="text-[11px] font-mono text-stone uppercase">{r.risk_type}</span>
                          </div>
                        </div>

                        <p className="mt-2.5 text-sm text-ivory font-sans leading-relaxed">{r.description}</p>

                        {safeArray(r.mitigation_steps).length > 0 && (
                          <div className="mt-3 p-3 rounded-lg bg-olive/40 border border-border text-xs text-stone space-y-1">
                            <strong className="text-verdigris font-medium uppercase font-mono text-[10px] block">
                              Mitigation Strategy:
                            </strong>
                            <ul className="list-disc list-inside space-y-0.5 text-ivory/80">
                              {safeArray(r.mitigation_steps).map((m: string, mIdx: number) => (
                                <li key={mIdx}>{m}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {safeArray(r.clarification_documents_needed).length > 0 && (
                          <div className="mt-2 text-[11px] font-mono text-stone">
                            <span className="text-brass">Missing Documents Needed:</span>{' '}
                            {safeArray(r.clarification_documents_needed).join(', ')}
                          </div>
                        )}
                      </div>
                    );
                  })}

                  {(!currentSession.risks || currentSession.risks.length === 0) && (
                    <div className="p-10 rounded-xl bg-charcoal border border-dashed border-border text-center">
                      <AlertOctagon className="h-8 w-8 text-stone/40 mx-auto mb-2" />
                      <p className="text-sm font-medium text-stone">No risk matrix generated yet.</p>
                      <p className="text-xs text-stone/60 mt-1 max-w-md mx-auto">
                        Click &ldquo;Assess Case Risks&rdquo; to identify potential evidentiary pitfalls before filing.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 7: STRATEGY REPORT */}
            {activeTab === 'report' && (
              <div className="space-y-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl bg-charcoal border border-border">
                  <div>
                    <h3 className="font-serif text-lg font-semibold text-ivory">Comprehensive Strategy Report</h3>
                    <p className="text-xs text-stone mt-0.5">
                      Synthesized brief combining factual chronology, arguments, devil&apos;s advocate stress test, and action plan.
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={handleExportReport}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-brass/20 text-brass border border-brass/40 flex items-center gap-1.5 hover:bg-brass/30 transition-colors"
                    >
                      <Download className="h-3.5 w-3.5" /> Download (.MD)
                    </button>
                    <button
                      type="button"
                      onClick={() => handleRunAnalysis('report')}
                      disabled={analyzingOp === 'report'}
                      className="btn-oxblood px-4 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm"
                    >
                      <RefreshCw className={`h-3.5 w-3.5 ${analyzingOp === 'report' ? 'animate-spin' : ''}`} />
                      <span>{analyzingOp === 'report' ? 'Generating Report...' : 'Synthesize Report'}</span>
                    </button>
                  </div>
                </div>

                {Object.keys(currentSession.report || {}).length > 0 ? (
                  <div className="p-6 md:p-8 rounded-xl bg-charcoal border border-border space-y-6 font-sans">
                    <div className="border-b border-border pb-4">
                      <div className="text-xs font-mono uppercase tracking-widest text-brass">
                        NyayaSarathi Case Intelligence
                      </div>
                      <h2 className="font-serif text-2xl font-bold text-ivory mt-1">{currentSession.title}</h2>
                      <div className="mt-2 flex flex-wrap gap-2 text-xs text-stone">
                        <span>Forum: {currentSession.court}</span>
                        <span>&bull;</span>
                        <span>Standing: {currentSession.user_position.toUpperCase()}</span>
                        <span>&bull;</span>
                        <span>Generated: {currentSession.report.generated_at || 'Recent'}</span>
                      </div>
                    </div>

                    {/* Section 1: Executive Summary */}
                    <div>
                      <h3 className="font-serif text-base font-semibold text-brass mb-1.5">1. Executive Summary</h3>
                      <p className="text-xs md:text-sm text-ivory/90 leading-relaxed bg-olive/30 p-3.5 rounded-lg border border-border/50">
                        {currentSession.report.executive_summary}
                      </p>
                    </div>

                    {/* Section 2: Parties & Procedural Posture */}
                    <div>
                      <h3 className="font-serif text-base font-semibold text-brass mb-1.5">2. Parties & Procedural Posture</h3>
                      <pre className="text-xs md:text-sm text-ivory/80 whitespace-pre-wrap font-sans bg-olive/30 p-3.5 rounded-lg border border-border/50">
                        {currentSession.report.parties_and_procedural_posture || currentSession.report.parties_and_issues}
                      </pre>
                    </div>

                    {/* Section 3: Verified Factual Chronology */}
                    <div>
                      <h3 className="font-serif text-base font-semibold text-brass mb-1.5">3. Verified Factual Chronology</h3>
                      <pre className="text-xs md:text-sm text-ivory/80 whitespace-pre-wrap font-sans bg-olive/30 p-3.5 rounded-lg border border-border/50">
                        {currentSession.report.verified_factual_chronology || currentSession.report.factual_chronology}
                      </pre>
                    </div>

                    {/* Section 4: Issues for Determination */}
                    {(currentSession.report.issues_for_determination || !currentSession.report.parties_and_procedural_posture) && (
                      <div>
                        <h3 className="font-serif text-base font-semibold text-brass mb-1.5">4. Issues for Determination</h3>
                        <pre className="text-xs md:text-sm text-ivory/80 whitespace-pre-wrap font-sans bg-olive/30 p-3.5 rounded-lg border border-border/50">
                          {currentSession.report.issues_for_determination || currentSession.report.parties_and_issues}
                        </pre>
                      </div>
                    )}

                    {/* Section 5: Evidence Matrix */}
                    <div>
                      <h3 className="font-serif text-base font-semibold text-brass mb-1.5">5. Evidence Matrix with Source References</h3>
                      <pre className="text-xs md:text-sm text-ivory/80 whitespace-pre-wrap font-sans bg-olive/30 p-3.5 rounded-lg border border-border/50 leading-relaxed">
                        {currentSession.report.evidence_matrix || 'Refer to the Evidence Analyzer tab for detailed evidentiary classification.'}
                      </pre>
                    </div>

                    {/* Section 6: Arguments & Counter-Arguments */}
                    <div>
                      <h3 className="font-serif text-base font-semibold text-brass mb-1.5">6. Arguments & Counter-Arguments</h3>
                      <pre className="text-xs md:text-sm text-ivory/80 whitespace-pre-wrap font-sans bg-olive/30 p-3.5 rounded-lg border border-border/50 leading-relaxed">
                        {currentSession.report.arguments_and_counterarguments || currentSession.report.affirmative_arguments}
                      </pre>
                    </div>

                    {/* Section 7: Relevant Verified Precedents */}
                    <div>
                      <h3 className="font-serif text-base font-semibold text-brass mb-1.5">7. Relevant Verified Precedents</h3>
                      <pre className="text-xs md:text-sm text-ivory/80 whitespace-pre-wrap font-sans bg-olive/30 p-3.5 rounded-lg border border-border/50 leading-relaxed">
                        {currentSession.report.precedent_landscape || 'Refer to the Precedents tab for full judicial holdings.'}
                      </pre>
                    </div>

                    {/* Section 8: Risks, Evidentiary Gaps & Unresolved Questions */}
                    <div>
                      <h3 className="font-serif text-base font-semibold text-brass mb-1.5">
                        8. Risks, Evidentiary Gaps & Unresolved Questions
                      </h3>
                      <pre className="text-xs md:text-sm text-ivory/80 whitespace-pre-wrap font-sans bg-olive/30 p-3.5 rounded-lg border border-border/50 leading-relaxed">
                        {currentSession.report.risks_evidentiary_gaps_questions || currentSession.report.opposition_stress_test}
                      </pre>
                    </div>

                    {/* Section 9: Practical Next Steps */}
                    <div>
                      <h3 className="font-serif text-base font-semibold text-brass mb-1.5">9. Practical Next Steps (Stage-Appropriate)</h3>
                      <pre className="text-xs md:text-sm text-ivory/80 whitespace-pre-wrap font-sans bg-olive/30 p-3.5 rounded-lg border border-border/50 leading-relaxed">
                        {currentSession.report.practical_next_steps || currentSession.report.action_plan}
                      </pre>
                    </div>

                    {/* Section 10: Limitations & Verification Warnings */}
                    <div>
                      <h3 className="font-serif text-base font-semibold text-brass mb-1.5">10. Limitations & Verification Warnings</h3>
                      <div className="p-3.5 rounded-lg bg-red-950/20 border border-red-900/40 text-xs md:text-sm text-red-200/90 leading-relaxed">
                        {currentSession.report.limitations_and_verification_warnings || currentSession.report.disclaimer || 'All legal findings require independent verification by practicing advocates.'}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="p-10 rounded-xl bg-charcoal border border-dashed border-border text-center">
                    <FileText className="h-8 w-8 text-stone/40 mx-auto mb-2" />
                    <p className="text-sm font-medium text-stone">No report synthesized yet.</p>
                    <p className="text-xs text-stone/60 mt-1 max-w-md mx-auto">
                      Click &ldquo;Synthesize Report&rdquo; to aggregate all verified facts, arguments, precedents, and opposition defenses into a unified strategy brief.
                    </p>
                  </div>
                )}
              </div>
            )}

          </div>
        ) : (
          /* Empty state when no sessions exist */
          <div className="mt-12 p-12 rounded-2xl bg-charcoal border border-dashed border-border text-center max-w-lg mx-auto">
            <Swords className="h-12 w-12 text-brass mx-auto mb-3" />
            <h3 className="font-serif text-xl font-semibold text-ivory">Welcome to Legal War Room</h3>
            <p className="text-xs text-stone mt-1.5 leading-relaxed">
              Create an AI-assisted case workspace to stress-test your claims, review documentary evidence, and formulate winning adversarial strategies.
            </p>
            <button
              type="button"
              onClick={() => setShowNewModal(true)}
              className="mt-6 btn-oxblood px-5 py-2.5 rounded-lg text-sm font-semibold inline-flex items-center gap-2 shadow-oxblood"
            >
              <Plus className="h-4 w-4" />
              <span>Create Your First Case</span>
            </button>
          </div>
        )}

      </main>

      {/* ── MODAL: Create New Case Workspace ──────────────────────────────── */}
      {showNewModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl bg-charcoal border border-border p-6 shadow-2xl relative">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <h3 className="font-serif text-lg font-semibold text-ivory">New Legal War Room Case</h3>
              <button
                type="button"
                onClick={() => setShowNewModal(false)}
                className="text-stone hover:text-ivory"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleCreateSession} className="mt-4 space-y-4">
              <div>
                <label className="text-xs font-mono text-stone uppercase block mb-1">Case Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Appellant v. Respondent"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full bg-olive rounded-lg px-3 py-2 text-sm text-ivory border border-border focus:border-brass focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-mono text-stone uppercase block mb-1">Court / Forum</label>
                  <input
                    type="text"
                    placeholder="e.g. Supreme Court of India / High Court / Sessions Court"
                    value={newCourt}
                    onChange={(e) => setNewCourt(e.target.value)}
                    className="w-full bg-olive rounded-lg px-3 py-2 text-sm text-ivory border border-border focus:border-brass focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs font-mono text-stone uppercase block mb-1">Case Type</label>
                  <select
                    value={newCaseType}
                    onChange={(e) => setNewCaseType(e.target.value)}
                    className="w-full bg-olive rounded-lg px-3 py-2 text-sm text-ivory border border-border focus:border-brass focus:outline-none"
                  >
                    <option value="bail">Bail / Anticipatory Bail</option>
                    <option value="criminal">Criminal Appeal / Revision</option>
                    <option value="civil">Civil Suit / Commercial</option>
                    <option value="writ_civil">Writ Petition (Art. 226/32)</option>
                    <option value="cheque_bounce">Section 138 NI Act</option>
                    <option value="property">Property & Possession</option>
                    <option value="family">Family / Matrimonial</option>
                    <option value="arbitration">Arbitration & Conciliation</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-mono text-stone uppercase block mb-1">Your Procedural Role</label>
                  <select
                    value={newUserPosition}
                    onChange={(e) => setNewUserPosition(e.target.value)}
                    className="w-full bg-olive rounded-lg px-3 py-2 text-sm text-ivory border border-border focus:border-brass focus:outline-none"
                  >
                    <option value="applicant">Applicant / Petitioner</option>
                    <option value="respondent">Respondent / Accused</option>
                    <option value="appellant">Appellant</option>
                    <option value="plaintiff">Plaintiff / Claimant</option>
                    <option value="defendant">Defendant</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-mono text-stone uppercase block mb-1">Opposing Party</label>
                  <input
                    type="text"
                    placeholder="e.g. Opposite Party / Prosecution / Respondent"
                    value={newOpposingParty}
                    onChange={(e) => setNewOpposingParty(e.target.value)}
                    className="w-full bg-olive rounded-lg px-3 py-2 text-sm text-ivory border border-border focus:border-brass focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-mono text-stone uppercase block mb-1">Initial Facts / Summary</label>
                <textarea
                  rows={3}
                  placeholder="Summarize the dispute, charges, or background facts..."
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  className="w-full bg-olive rounded-lg p-3 text-xs text-ivory border border-border focus:border-brass focus:outline-none"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowNewModal(false)}
                  className="px-4 py-2 rounded-lg text-xs font-medium text-stone hover:text-ivory"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-oxblood px-5 py-2 rounded-lg text-xs font-semibold shadow-sm"
                >
                  Create Case Workspace
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── MODAL: Select Evidence Documents ──────────────────────────────── */}
      {showDocModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-xl rounded-2xl bg-charcoal border border-border p-6 shadow-2xl relative max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <h3 className="font-serif text-lg font-semibold text-ivory">Select Evidence Documents</h3>
              <button
                type="button"
                onClick={() => setShowDocModal(false)}
                className="text-stone hover:text-ivory"
              >
                &times;
              </button>
            </div>

            <p className="text-xs text-stone mt-2">
              Attach uploaded documents to ground the War Room analysis strictly in page-level evidence.
            </p>

            <div className="mt-4 flex-1 overflow-y-auto doc-scroll space-y-2 pr-1">
              {availableDocs.map((doc) => {
                const isSelected = currentSession?.selected_doc_ids?.includes(doc.id);
                return (
                  <button
                    key={doc.id}
                    type="button"
                    onClick={() => toggleDocumentSelection(doc.id)}
                    className={`w-full p-3 rounded-lg border text-left flex items-center justify-between transition-colors ${
                      isSelected
                        ? 'bg-olive border-brass/60 text-ivory'
                        : 'bg-olive/40 border-border text-stone hover:text-ivory'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`h-4 w-4 rounded border flex items-center justify-center ${
                          isSelected ? 'bg-brass border-brass text-ink' : 'border-stone/40'
                        }`}
                      >
                        {isSelected && <Check className="h-3 w-3 stroke-[3]" />}
                      </div>
                      <div>
                        <div className="text-xs font-medium text-ivory truncate max-w-sm">{doc.title}</div>
                        <div className="text-[10px] font-mono text-stone mt-0.5">
                          {doc.filename} &bull; {doc.total_pages} pages
                        </div>
                      </div>
                    </div>
                    <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-charcoal text-stone">
                      {doc.file_type}
                    </span>
                  </button>
                );
              })}

              {availableDocs.length === 0 && (
                <div className="p-8 text-center text-xs text-stone border border-dashed border-border rounded-lg">
                  No uploaded documents found. Please upload documents in the Legal Research or OCR section first.
                </div>
              )}
            </div>

            <div className="mt-4 pt-3 border-t border-border flex justify-end">
              <button
                type="button"
                onClick={() => setShowDocModal(false)}
                className="btn-oxblood px-5 py-2 rounded-lg text-xs font-semibold"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── MODAL: Add Custom Fact ────────────────────────────────────────── */}
      {showAddFactModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl bg-charcoal border border-border p-6 shadow-2xl relative">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <h3 className="font-serif text-lg font-semibold text-ivory">Add Case Fact</h3>
              <button
                type="button"
                onClick={() => setShowAddFactModal(false)}
                className="text-stone hover:text-ivory"
              >
                &times;
              </button>
            </div>

            <div className="mt-4 space-y-3">
              <div>
                <label className="text-xs font-mono text-stone uppercase block mb-1">Fact Statement *</label>
                <textarea
                  rows={3}
                  value={factText}
                  onChange={(e) => setFactText(e.target.value)}
                  placeholder="Enter specific factual finding or recorded event..."
                  className="w-full bg-olive rounded-lg p-2.5 text-xs text-ivory border border-border focus:border-brass focus:outline-none"
                />
              </div>

              <div>
                <label className="text-xs font-mono text-stone uppercase block mb-1">Category</label>
                <select
                  value={factCategory}
                  onChange={(e) => setFactCategory(e.target.value)}
                  className="w-full bg-olive rounded-lg px-3 py-2 text-xs text-ivory border border-border focus:border-brass focus:outline-none"
                >
                  <option value="established_fact">Established Fact (Documented)</option>
                  <option value="unverified_allegation">Unverified Allegation (Pleaded)</option>
                  <option value="conflicting_information">Conflicting Information</option>
                  <option value="missing_critical_info">Missing Critical Info</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-xs font-mono text-stone uppercase block mb-1">Source Doc Title</label>
                  <input
                    type="text"
                    value={factDocTitle}
                    onChange={(e) => setFactDocTitle(e.target.value)}
                    placeholder="e.g. FIR No. 42"
                    className="w-full bg-olive rounded-lg px-3 py-2 text-xs text-ivory border border-border focus:border-brass focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs font-mono text-stone uppercase block mb-1">Page #</label>
                  <input
                    type="number"
                    value={factPage}
                    onChange={(e) => setFactPage(e.target.value === '' ? '' : Number(e.target.value))}
                    placeholder="e.g. 3"
                    className="w-full bg-olive rounded-lg px-3 py-2 text-xs text-ivory border border-border focus:border-brass focus:outline-none"
                  />
                </div>
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddFactModal(false)}
                  className="px-4 py-2 rounded-lg text-xs font-medium text-stone hover:text-ivory"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleAddCustomFact}
                  className="btn-oxblood px-5 py-2 rounded-lg text-xs font-semibold"
                >
                  Save Fact
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── MODAL: Add Custom Argument ─────────────────────────────────────── */}
      {showAddArgModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl bg-charcoal border border-border p-6 shadow-2xl relative">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <h3 className="font-serif text-lg font-semibold text-ivory">Add Affirmative Argument</h3>
              <button
                type="button"
                onClick={() => setShowAddArgModal(false)}
                className="text-stone hover:text-ivory"
              >
                &times;
              </button>
            </div>

            <div className="mt-4 space-y-3">
              <div>
                <label className="text-xs font-mono text-stone uppercase block mb-1">Argument Headline *</label>
                <input
                  type="text"
                  value={argTitle}
                  onChange={(e) => setArgTitle(e.target.value)}
                  placeholder="e.g. Core Legal Contention or Ground"
                  className="w-full bg-olive rounded-lg px-3 py-2 text-xs text-ivory border border-border focus:border-brass focus:outline-none"
                />
              </div>

              <div>
                <label className="text-xs font-mono text-stone uppercase block mb-1">Main Claim *</label>
                <textarea
                  rows={2}
                  value={argClaim}
                  onChange={(e) => setArgClaim(e.target.value)}
                  placeholder="State the core legal proposition..."
                  className="w-full bg-olive rounded-lg p-2.5 text-xs text-ivory border border-border focus:border-brass focus:outline-none"
                />
              </div>

              <div>
                <label className="text-xs font-mono text-stone uppercase block mb-1">Statutory Sections (comma-separated)</label>
                <input
                  type="text"
                  value={argProvisions}
                  onChange={(e) => setArgProvisions(e.target.value)}
                  placeholder="e.g. Applicable Statutory Sections or Articles"
                  className="w-full bg-olive rounded-lg px-3 py-2 text-xs text-ivory border border-border focus:border-brass focus:outline-none"
                />
              </div>

              <div>
                <label className="text-xs font-mono text-stone uppercase block mb-1">Legal Reasoning</label>
                <textarea
                  rows={3}
                  value={argReasoning}
                  onChange={(e) => setArgReasoning(e.target.value)}
                  placeholder="Explain how the law applies to these specific facts..."
                  className="w-full bg-olive rounded-lg p-2.5 text-xs text-ivory border border-border focus:border-brass focus:outline-none"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddArgModal(false)}
                  className="px-4 py-2 rounded-lg text-xs font-medium text-stone hover:text-ivory"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleAddCustomArgument}
                  className="btn-oxblood px-5 py-2 rounded-lg text-xs font-semibold"
                >
                  Save Argument
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <Footer />
    </div>
  );
}
