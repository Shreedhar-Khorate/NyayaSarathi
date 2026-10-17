'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
  Scale,
  Search,
  Filter,
  Calendar,
  Building2,
  ChevronLeft,
  ChevronRight,
  Loader2,
  RefreshCw,
  AlertCircle,
  ExternalLink,
  BookOpen,
  Info,
  Sparkles,
  Clock,
  CheckCircle2,
  FileText,
  User,
  Edit3,
} from 'lucide-react';
import { RoleGuard } from '@/components/auth/RoleGuard';
import {
  fetchJudgeCases,
  fetchJudgePrecedents,
  updateJudgeCaseStatus,
  type JudgeAssignedCaseItem,
  type PrecedentItem,
} from '@/lib/auth';

export default function JudgeCasesPage() {
  const [activeTab, setActiveTab] = useState<'docket' | 'precedents'>('docket');

  // Docket state
  const [assignedCases, setAssignedCases] = useState<JudgeAssignedCaseItem[]>([]);
  const [docketTotal, setDocketTotal] = useState(0);
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [selectedPriority, setSelectedPriority] = useState<string>('ALL');
  const [docketPage, setDocketPage] = useState(0);
  const [isUpdatingCase, setIsUpdatingCase] = useState<string | null>(null);

  // Precedents state
  const [precedents, setPrecedents] = useState<PrecedentItem[]>([]);
  const [precedentTotal, setPrecedentTotal] = useState(0);
  const [precedentSearch, setPrecedentSearch] = useState('');
  const [selectedYear, setSelectedYear] = useState<string>('ALL');
  const [precedentPage, setPrecedentPage] = useState(0);

  const limit = 15;
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Status update modal state
  const [editingCase, setEditingCase] = useState<JudgeAssignedCaseItem | null>(null);
  const [newStatus, setNewStatus] = useState('');
  const [newNotes, setNewNotes] = useState('');
  const [newHearingDate, setNewHearingDate] = useState('');

  // 1. Load Assigned Docket
  const loadDocket = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchJudgeCases(
        selectedStatus !== 'ALL' ? selectedStatus : undefined,
        selectedPriority !== 'ALL' ? selectedPriority : undefined,
        limit,
        docketPage * limit
      );
      setAssignedCases(data.items);
      setDocketTotal(data.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve bench docket.');
    } finally {
      setIsLoading(false);
    }
  }, [selectedStatus, selectedPriority, docketPage]);

  // 2. Load Precedents
  const loadPrecedents = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const yearNum = selectedYear !== 'ALL' ? parseInt(selectedYear, 10) : undefined;
      const data = await fetchJudgePrecedents(precedentSearch, yearNum, limit, precedentPage * limit);
      setPrecedents(data.items);
      setPrecedentTotal(data.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve precedents.');
    } finally {
      setIsLoading(false);
    }
  }, [precedentSearch, selectedYear, precedentPage]);

  useEffect(() => {
    if (activeTab === 'docket') {
      loadDocket();
    } else {
      const timer = setTimeout(() => {
        loadPrecedents();
      }, 250);
      return () => clearTimeout(timer);
    }
  }, [activeTab, loadDocket, loadPrecedents]);

  const handleUpdateStatus = async () => {
    if (!editingCase) return;
    setIsUpdatingCase(editingCase.id);
    setError(null);
    try {
      await updateJudgeCaseStatus(editingCase.id, newStatus, newNotes, newHearingDate);
      setSuccessMsg(`Case ${editingCase.case_number} status updated to ${newStatus}.`);
      setEditingCase(null);
      loadDocket();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update docket status.');
    } finally {
      setIsUpdatingCase(null);
    }
  };

  const docketPages = Math.ceil(docketTotal / limit) || 1;
  const precedentPages = Math.ceil(precedentTotal / limit) || 1;

  return (
    <RoleGuard allowedRoles={['JUDGE', 'ADMIN']} portalName="Judicial Bench Docket & Precedents">
      <div className="min-h-screen bg-[#151716] pt-28 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto space-y-6">

          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-xs text-[#A9A49A]">
            <Link href="/judge/dashboard" className="hover:text-[#B59A68] transition-colors">
              Judge Chamber
            </Link>
            <span>/</span>
            <span className="text-[#F4EFE5]">Bench Matters & Legal Precedents</span>
          </div>

          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-[#3B3A33]/80 pb-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2.5 py-0.5 rounded text-[11px] font-mono uppercase tracking-wider bg-[#6E2634]/30 text-[#E25C6F] border border-[#6E2634]/60">
                  Judicial Docket & Authorities
                </span>
                <span className="text-[#A9A49A] text-xs">• Verified Bench Records</span>
              </div>
              <h1 className="font-display text-3xl font-bold text-[#F4EFE5] tracking-tight">
                Court Matters & Legal Precedents
              </h1>
              <p className="font-sans text-sm text-[#A9A49A] mt-1">
                Manage persistent litigation assigned to your bench and research indexed High Court & Supreme Court authorities.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => (activeTab === 'docket' ? loadDocket() : loadPrecedents())}
                disabled={isLoading}
                className="flex items-center gap-2 rounded-xl border border-[#3B3A33] bg-[#1D211F] px-4 py-2 font-sans text-xs font-semibold text-[#F4EFE5] hover:border-[#B59A68]/60 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 text-[#B59A68] ${isLoading ? 'animate-spin' : ''}`} />
                <span>Refresh View</span>
              </button>
            </div>
          </div>

          {/* Feedback messages */}
          {error && (
            <div className="rounded-xl border border-[#6E2634] bg-[#6E2634]/20 p-4 flex items-center gap-3 text-sm text-[#E25C6F]">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}
          {successMsg && (
            <div className="rounded-xl border border-[#71877A] bg-[#71877A]/20 p-4 flex items-center justify-between text-sm text-[#A9A49A]">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-[#B59A68]" />
                <span className="text-[#F4EFE5]">{successMsg}</span>
              </div>
              <button onClick={() => setSuccessMsg(null)} className="text-xs text-[#A9A49A] hover:text-[#F4EFE5]">
                Dismiss
              </button>
            </div>
          )}

          {/* Navigation Tabs */}
          <div className="flex border-b border-[#3B3A33]">
            <button
              onClick={() => setActiveTab('docket')}
              className={`flex items-center gap-2.5 px-6 py-3 font-sans text-sm font-semibold border-b-2 transition-all ${
                activeTab === 'docket'
                  ? 'border-[#B59A68] text-[#F4EFE5] bg-[#1D211F]/60'
                  : 'border-transparent text-[#A9A49A] hover:text-[#F4EFE5] hover:bg-[#1D211F]/30'
              }`}
            >
              <Scale className={`w-4 h-4 ${activeTab === 'docket' ? 'text-[#B59A68]' : 'text-[#A9A49A]'}`} />
              <span>Assigned Bench Docket</span>
              <span className="ml-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-[#3B3A33] text-[#F4EFE5]">
                {docketTotal}
              </span>
            </button>

            <button
              onClick={() => setActiveTab('precedents')}
              className={`flex items-center gap-2.5 px-6 py-3 font-sans text-sm font-semibold border-b-2 transition-all ${
                activeTab === 'precedents'
                  ? 'border-[#B59A68] text-[#F4EFE5] bg-[#1D211F]/60'
                  : 'border-transparent text-[#A9A49A] hover:text-[#F4EFE5] hover:bg-[#1D211F]/30'
              }`}
            >
              <BookOpen className={`w-4 h-4 ${activeTab === 'precedents' ? 'text-[#B59A68]' : 'text-[#A9A49A]'}`} />
              <span>Legal Precedents Library</span>
              <span className="ml-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-[#3B3A33] text-[#F4EFE5]">
                {precedentTotal}
              </span>
            </button>
          </div>

          {/* ══════════════ TAB 1: ASSIGNED BENCH DOCKET ══════════════ */}
          {activeTab === 'docket' && (
            <div className="space-y-6">
              {/* Notice Banner */}
              <div className="rounded-xl border border-[#B59A68]/30 bg-[#B59A68]/10 p-4 flex items-start gap-3">
                <Info className="w-5 h-5 text-[#B59A68] shrink-0 mt-0.5" />
                <div className="text-xs text-[#A9A49A] space-y-1">
                  <p className="font-semibold text-[#F4EFE5]">
                    Presiding Judicial Bench Docket: Confidential & Isolated
                  </p>
                  <p>
                    These litigation matters are persistently assigned to your chamber. Changes to status, hearing dates, and bench notes are recorded in the judicial audit ledger.
                  </p>
                </div>
              </div>

              {/* Filters */}
              <div className="flex flex-wrap items-center gap-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-[#A9A49A] font-semibold">Status:</span>
                  <select
                    value={selectedStatus}
                    onChange={(e) => {
                      setSelectedStatus(e.target.value);
                      setDocketPage(0);
                    }}
                    className="rounded-xl border border-[#3B3A33] bg-[#1D211F] px-3 py-1.5 font-sans text-xs text-[#F4EFE5] focus:outline-none focus:border-[#B59A68]"
                  >
                    <option value="ALL">All Statuses</option>
                    <option value="ASSIGNED">ASSIGNED</option>
                    <option value="IN_REVIEW">IN_REVIEW</option>
                    <option value="HEARING_SCHEDULED">HEARING_SCHEDULED</option>
                    <option value="RESERVED">RESERVED</option>
                    <option value="DISPOSED">DISPOSED</option>
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs text-[#A9A49A] font-semibold">Priority:</span>
                  <select
                    value={selectedPriority}
                    onChange={(e) => {
                      setSelectedPriority(e.target.value);
                      setDocketPage(0);
                    }}
                    className="rounded-xl border border-[#3B3A33] bg-[#1D211F] px-3 py-1.5 font-sans text-xs text-[#F4EFE5] focus:outline-none focus:border-[#B59A68]"
                  >
                    <option value="ALL">All Priorities</option>
                    <option value="REGULAR">REGULAR</option>
                    <option value="URGENT">URGENT</option>
                    <option value="EXPEDITED">EXPEDITED</option>
                  </select>
                </div>
              </div>

              {/* Docket List */}
              {isLoading ? (
                <div className="p-16 flex flex-col items-center justify-center gap-3">
                  <Loader2 className="w-8 h-8 animate-spin text-[#B59A68]" />
                  <span className="text-xs font-mono text-[#A9A49A]">Loading assigned bench matters...</span>
                </div>
              ) : assignedCases.length === 0 ? (
                <div className="p-12 text-center rounded-2xl border border-dashed border-[#3B3A33] bg-[#1D211F]/30 space-y-3">
                  <Scale className="w-10 h-10 text-[#A9A49A]/50 mx-auto" />
                  <h3 className="font-display text-lg font-semibold text-[#F4EFE5]">
                    No Matters Assigned to Bench
                  </h3>
                  <p className="text-xs text-[#A9A49A] max-w-md mx-auto">
                    There are currently no active court cases assigned to your judicial profile. Contact the Judicial System Administrator to allocate matters to your docket.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-4">
                  {assignedCases.map((c) => (
                    <div
                      key={c.id}
                      className="rounded-2xl border border-[#3B3A33] bg-[#1D211F]/80 p-5 backdrop-blur-md hover:border-[#B59A68]/50 transition-all flex flex-col md:flex-row md:items-center md:justify-between gap-4"
                    >
                      <div className="space-y-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="px-2.5 py-0.5 rounded text-[11px] font-mono font-bold bg-[#B59A68]/20 text-[#B59A68] border border-[#B59A68]/40">
                            {c.case_number}
                          </span>
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-[#3B3A33] text-[#F4EFE5]">
                            {c.case_type}
                          </span>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                              c.priority === 'URGENT'
                                ? 'bg-[#6E2634] text-[#E25C6F]'
                                : 'bg-[#242925] text-[#A9A49A]'
                            }`}
                          >
                            {c.priority}
                          </span>
                          <span className="text-xs text-[#A9A49A]">• {c.court_name}</span>
                        </div>

                        <h3 className="font-display text-lg font-bold text-[#F4EFE5]">{c.title}</h3>

                        <div className="flex flex-wrap items-center gap-4 text-xs text-[#A9A49A]">
                          {c.petitioner && <span><strong className="text-[#F4EFE5]">Petitioner:</strong> {c.petitioner}</span>}
                          {c.respondent && <span><strong className="text-[#F4EFE5]">Respondent:</strong> {c.respondent}</span>}
                          {c.hearing_date && (
                            <span className="flex items-center gap-1 text-[#B59A68]">
                              <Calendar className="w-3.5 h-3.5" />
                              <span>Hearing: {c.hearing_date}</span>
                            </span>
                          )}
                        </div>

                        {c.notes && (
                          <div className="text-xs text-[#A9A49A] italic border-l-2 border-[#B59A68] pl-2 mt-1">
                            &ldquo;{c.notes}&rdquo;
                          </div>
                        )}
                      </div>

                      <div className="flex md:flex-col items-center md:items-end justify-between gap-3 shrink-0">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-mono font-bold tracking-wider uppercase ${
                            c.status === 'DISPOSED'
                              ? 'bg-[#71877A]/30 text-[#71877A] border border-[#71877A]'
                              : c.status === 'HEARING_SCHEDULED'
                              ? 'bg-[#B59A68]/30 text-[#B59A68] border border-[#B59A68]'
                              : 'bg-[#6E2634]/30 text-[#E25C6F] border border-[#6E2634]'
                          }`}
                        >
                          {c.status}
                        </span>

                        <button
                          onClick={() => {
                            setEditingCase(c);
                            setNewStatus(c.status);
                            setNewNotes(c.notes || '');
                            setNewHearingDate(c.hearing_date || '');
                          }}
                          className="flex items-center gap-1.5 text-xs font-semibold text-[#B59A68] hover:text-[#F4EFE5] transition-colors"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                          <span>Update Status</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Docket Pagination */}
              {docketPages > 1 && (
                <div className="flex items-center justify-between border-t border-[#3B3A33] pt-4">
                  <span className="text-xs text-[#A9A49A]">
                    Showing Page {docketPage + 1} of {docketPages} ({docketTotal} matters)
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setDocketPage((p) => Math.max(0, p - 1))}
                      disabled={docketPage === 0}
                      className="px-3 py-1.5 rounded-lg border border-[#3B3A33] bg-[#1D211F] text-xs text-[#F4EFE5] disabled:opacity-40"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setDocketPage((p) => Math.min(docketPages - 1, p + 1))}
                      disabled={docketPage >= docketPages - 1}
                      className="px-3 py-1.5 rounded-lg border border-[#3B3A33] bg-[#1D211F] text-xs text-[#F4EFE5] disabled:opacity-40"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ══════════════ TAB 2: LEGAL PRECEDENTS LIBRARY ══════════════ */}
          {activeTab === 'precedents' && (
            <div className="space-y-6">
              {/* Notice Banner */}
              <div className="rounded-xl border border-[#71877A]/30 bg-[#71877A]/10 p-4 flex items-start gap-3">
                <BookOpen className="w-5 h-5 text-[#71877A] shrink-0 mt-0.5" />
                <div className="text-xs text-[#A9A49A] space-y-1">
                  <p className="font-semibold text-[#F4EFE5]">
                    Public Precedents & Legal Research Library
                  </p>
                  <p>
                    Search across High Court and Supreme Court historical judgments. These records represent judicial authorities and citations, completely decoupled from your bench docket.
                  </p>
                </div>
              </div>

              {/* Search & Filter Bar */}
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                  <Search className="w-4 h-4 text-[#A9A49A] absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={precedentSearch}
                    onChange={(e) => {
                      setPrecedentSearch(e.target.value);
                      setPrecedentPage(0);
                    }}
                    placeholder="Search judgment title, court name, or legal principle..."
                    className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-[#3B3A33] bg-[#1D211F] text-xs text-[#F4EFE5] focus:outline-none focus:border-[#B59A68]"
                  />
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs text-[#A9A49A] font-semibold shrink-0">Year:</span>
                  <select
                    value={selectedYear}
                    onChange={(e) => {
                      setSelectedYear(e.target.value);
                      setPrecedentPage(0);
                    }}
                    className="rounded-xl border border-[#3B3A33] bg-[#1D211F] px-3 py-2.5 font-sans text-xs text-[#F4EFE5] focus:outline-none focus:border-[#B59A68]"
                  >
                    <option value="ALL">All Years</option>
                    <option value="2024">2024</option>
                    <option value="2023">2023</option>
                    <option value="2022">2022</option>
                    <option value="2021">2021</option>
                    <option value="2020">2020</option>
                  </select>
                </div>
              </div>

              {/* Precedents List */}
              {isLoading ? (
                <div className="p-16 flex flex-col items-center justify-center gap-3">
                  <Loader2 className="w-8 h-8 animate-spin text-[#B59A68]" />
                  <span className="text-xs font-mono text-[#A9A49A]">Loading legal precedents...</span>
                </div>
              ) : precedents.length === 0 ? (
                <div className="p-12 text-center rounded-2xl border border-dashed border-[#3B3A33] bg-[#1D211F]/30 space-y-2">
                  <BookOpen className="w-10 h-10 text-[#A9A49A]/50 mx-auto" />
                  <h3 className="font-display text-base font-semibold text-[#F4EFE5]">
                    No Precedents Found
                  </h3>
                  <p className="text-xs text-[#A9A49A]">Try adjusting your search terms or year filter.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-4">
                  {precedents.map((p, idx) => (
                    <div
                      key={p.cnr || idx}
                      className="rounded-2xl border border-[#3B3A33] bg-[#1D211F]/70 p-5 hover:border-[#B59A68]/40 transition-colors space-y-2"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#3B3A33] text-[#B59A68]">
                          CNR: {p.cnr}
                        </span>
                        {p.year && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#242925] text-[#A9A49A]">
                            {p.year}
                          </span>
                        )}
                        {p.case_type && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#242925] text-[#A9A49A]">
                            {p.case_type}
                          </span>
                        )}
                        <span className="text-xs text-[#A9A49A]">• {p.court || 'Court Precedent'}</span>
                      </div>

                      <h3 className="font-display text-base font-bold text-[#F4EFE5]">{p.title}</h3>

                      <div className="flex flex-wrap items-center gap-4 text-xs text-[#A9A49A]">
                        {p.judge && <span><strong className="text-[#F4EFE5]">Bench:</strong> {p.judge}</span>}
                        {p.decision_date && <span><strong className="text-[#F4EFE5]">Date:</strong> {p.decision_date}</span>}
                        {p.disposal_nature && (
                          <span className="text-[#B59A68]">
                            <strong>Disposal:</strong> {p.disposal_nature}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Precedents Pagination */}
              {precedentPages > 1 && (
                <div className="flex items-center justify-between border-t border-[#3B3A33] pt-4">
                  <span className="text-xs text-[#A9A49A]">
                    Showing Page {precedentPage + 1} of {precedentPages} ({precedentTotal} precedents)
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setPrecedentPage((p) => Math.max(0, p - 1))}
                      disabled={precedentPage === 0}
                      className="px-3 py-1.5 rounded-lg border border-[#3B3A33] bg-[#1D211F] text-xs text-[#F4EFE5] disabled:opacity-40"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setPrecedentPage((p) => Math.min(precedentPages - 1, p + 1))}
                      disabled={precedentPage >= precedentPages - 1}
                      className="px-3 py-1.5 rounded-lg border border-[#3B3A33] bg-[#1D211F] text-xs text-[#F4EFE5] disabled:opacity-40"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ══════════════ MODAL: UPDATE DOCKET STATUS ══════════════ */}
          {editingCase && (
            <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
              <div className="bg-[#1D211F] border border-[#3B3A33] rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
                <div className="flex items-center justify-between border-b border-[#3B3A33] pb-3">
                  <h3 className="font-display text-lg font-bold text-[#F4EFE5]">
                    Update Docket Status — {editingCase.case_number}
                  </h3>
                  <button onClick={() => setEditingCase(null)} className="text-[#A9A49A] hover:text-[#F4EFE5]">
                    ✕
                  </button>
                </div>

                <div className="space-y-3">
                  <div>
                    <label className="text-xs font-semibold text-[#A9A49A] block mb-1">Docket Status</label>
                    <select
                      value={newStatus}
                      onChange={(e) => setNewStatus(e.target.value)}
                      className="w-full rounded-xl border border-[#3B3A33] bg-[#151716] px-3 py-2 text-xs text-[#F4EFE5] focus:outline-none focus:border-[#B59A68]"
                    >
                      <option value="ASSIGNED">ASSIGNED (Initial Assignment)</option>
                      <option value="IN_REVIEW">IN_REVIEW (Chamber Brief Examination)</option>
                      <option value="HEARING_SCHEDULED">HEARING_SCHEDULED (Placed on Cause List)</option>
                      <option value="RESERVED">RESERVED (Judgment Reserved)</option>
                      <option value="DISPOSED">DISPOSED (Matter Concluded)</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-[#A9A49A] block mb-1">Next Hearing Date</label>
                    <input
                      type="date"
                      value={newHearingDate}
                      onChange={(e) => setNewHearingDate(e.target.value)}
                      className="w-full rounded-xl border border-[#3B3A33] bg-[#151716] px-3 py-2 text-xs text-[#F4EFE5] focus:outline-none focus:border-[#B59A68]"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-[#A9A49A] block mb-1">Judicial Bench Notes</label>
                    <textarea
                      rows={3}
                      value={newNotes}
                      onChange={(e) => setNewNotes(e.target.value)}
                      placeholder="Enter directions, bench observations, or hearing instructions..."
                      className="w-full rounded-xl border border-[#3B3A33] bg-[#151716] px-3 py-2 text-xs text-[#F4EFE5] focus:outline-none focus:border-[#B59A68]"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#3B3A33]">
                  <button
                    onClick={() => setEditingCase(null)}
                    className="px-4 py-2 rounded-xl border border-[#3B3A33] text-xs font-semibold text-[#A9A49A] hover:text-[#F4EFE5]"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleUpdateStatus}
                    disabled={isUpdatingCase !== null}
                    className="px-4 py-2 rounded-xl bg-gradient-to-r from-[#6E2634] to-[#8A3545] border border-[#B59A68]/40 text-xs font-semibold text-[#F4EFE5] hover:brightness-110 disabled:opacity-50"
                  >
                    {isUpdatingCase ? 'Saving...' : 'Save Docket Update'}
                  </button>
                </div>
              </div>
            </div>
          )}

        </div>
      </div>
    </RoleGuard>
  );
}
