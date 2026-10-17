'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
  Activity,
  Filter,
  Search,
  ChevronLeft,
  ChevronRight,
  Loader2,
  RefreshCw,
  AlertCircle,
  FileText,
  Scale,
  Calendar,
  Lock,
  ExternalLink,
} from 'lucide-react';
import { RoleGuard } from '@/components/auth/RoleGuard';
import { fetchJudgeActivities, type JudgeActivityItem } from '@/lib/auth';

const ACTIVITY_TYPES = [
  'ALL',
  'LEGAL_RESEARCH',
  'DOCUMENT_UPLOAD',
  'OCR_ANALYSIS',
  'PREDICTION',
];

export default function JudgeActivityPage() {
  const [activities, setActivities] = useState<JudgeActivityItem[]>([]);
  const [total, setTotal] = useState(0);
  const [selectedType, setSelectedType] = useState('ALL');
  const [page, setPage] = useState(0);
  const limit = 20;

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadActivities = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchJudgeActivities(
        selectedType === 'ALL' ? undefined : selectedType,
        limit,
        page * limit
      );
      setActivities(data.items);
      setTotal(data.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve chamber activities.');
    } finally {
      setIsLoading(false);
    }
  }, [selectedType, page]);

  useEffect(() => {
    loadActivities();
  }, [loadActivities]);

  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <RoleGuard allowedRoles={['JUDGE', 'ADMIN']} portalName="Judicial Chamber Activity">
      <div className="min-h-screen bg-[#151716] pt-28 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto space-y-6">

          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-xs text-[#A9A49A]">
            <Link href="/judge/dashboard" className="hover:text-[#B59A68] transition-colors">
              Judge Chamber
            </Link>
            <span>/</span>
            <span className="text-[#F4EFE5]">Chamber Activity Feed</span>
          </div>

          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-[#3B3A33]/80 pb-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2.5 py-0.5 rounded text-[11px] font-mono uppercase tracking-wider bg-[#6E2634]/30 text-[#E25C6F] border border-[#6E2634]/60">
                  Judicial Privacy Enforced
                </span>
                <span className="text-[#A9A49A] text-xs">• Chamber-isolated log</span>
              </div>
              <h1 className="font-display text-3xl font-bold text-[#F4EFE5] tracking-tight">
                Chamber Research & Document Activity
              </h1>
              <p className="font-sans text-sm text-[#A9A49A] mt-1">
                Filter and review authorized legal research queries, document verifications, and ML predictions performed in your chamber.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={loadActivities}
                disabled={isLoading}
                className="flex items-center gap-2 rounded-xl border border-[#3B3A33] bg-[#1D211F] px-4 py-2 font-sans text-xs font-semibold text-[#F4EFE5] hover:border-[#B59A68]/60 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 text-[#B59A68] ${isLoading ? 'animate-spin' : ''}`} />
                <span>Refresh Feed</span>
              </button>

              <Link
                href="/legal-research"
                className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#6E2634] to-[#8A3545] border border-[#B59A68]/40 px-4 py-2 font-sans text-xs font-semibold text-[#F4EFE5] shadow-lg shadow-[#6E2634]/20 hover:brightness-110 transition-all"
              >
                <span>New Legal Research</span>
              </Link>
            </div>
          </div>

          {/* Privacy Notice Banner */}
          <div className="rounded-xl border border-[#3B3A33] bg-[#1D211F]/60 p-4 flex items-start gap-3 text-xs text-[#A9A49A]">
            <Lock className="w-4 h-4 text-[#B59A68] shrink-0 mt-0.5" />
            <p>
              <strong className="text-[#F4EFE5]">Privacy Protection Guarantee:</strong> In compliance with the NyayaSarathi judicial security model, judges are never granted unrestricted access to other citizens&apos; or private advocates&apos; legal inquiries. This feed displays activities initiated under your judicial credentials.
            </p>
          </div>

          {error && (
            <div className="rounded-xl border border-[#6E2634] bg-[#6E2634]/20 p-4 flex items-center gap-2 text-xs text-[#E25C6F]">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Filter Bar */}
          <div className="rounded-2xl border border-[#3B3A33] bg-[#1D211F]/70 p-4 flex flex-col sm:flex-row items-center justify-between gap-4 backdrop-blur-md">
            <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
              <span className="text-xs text-[#A9A49A] flex items-center gap-1 mr-1 shrink-0 font-mono">
                <Filter className="w-3 h-3 text-[#B59A68]" />
                Activity Type:
              </span>
              {ACTIVITY_TYPES.map((t) => (
                <button
                  key={t}
                  onClick={() => {
                    setSelectedType(t);
                    setPage(0);
                  }}
                  className={`px-3 py-1.5 rounded-lg text-xs font-mono uppercase font-semibold transition-colors shrink-0 ${
                    selectedType === t
                      ? 'bg-[#6E2634]/40 text-[#B59A68] border border-[#B59A68]/50 shadow-sm'
                      : 'text-[#A9A49A] hover:bg-white/[0.04] hover:text-[#F4EFE5]'
                  }`}
                >
                  {t.replace('_', ' ')}
                </button>
              ))}
            </div>

            <div className="text-xs font-mono text-[#A9A49A]">
              Activities Logged: <span className="font-bold text-[#F4EFE5]">{total}</span>
            </div>
          </div>

          {/* Activity Items List */}
          <div className="rounded-2xl border border-[#3B3A33] bg-[#1D211F]/60 overflow-hidden shadow-xl">
            {isLoading ? (
              <div className="py-16 text-center text-[#A9A49A]">
                <Loader2 className="w-7 h-7 animate-spin mx-auto mb-2 text-[#B59A68]" />
                <span>Loading chamber activities...</span>
              </div>
            ) : activities.length === 0 ? (
              <div className="py-16 text-center text-[#A9A49A] space-y-2">
                <Activity className="w-8 h-8 mx-auto text-[#3B3A33]" />
                <p>No activity records found matching this category.</p>
                <Link
                  href="/legal-research"
                  className="text-xs text-[#B59A68] hover:underline font-semibold"
                >
                  Conduct a legal research query to record bench activity
                </Link>
              </div>
            ) : (
              <div className="divide-y divide-[#3B3A33]/40">
                {activities.map((act) => (
                  <div key={act.id} className="p-5 hover:bg-white/[0.02] transition-colors space-y-2">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center gap-2.5">
                        <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-[#6E2634]/30 text-[#E25C6F] border border-[#6E2634]/50">
                          {act.activity_type}
                        </span>
                        <h3 className="text-sm font-semibold text-[#F4EFE5]">
                          {act.title}
                        </h3>
                      </div>
                      <span className="text-[11px] font-mono text-[#A9A49A] shrink-0">
                        {new Date(act.created_at).toLocaleString()}
                      </span>
                    </div>

                    {act.query_text && (
                      <div className="rounded-xl border border-[#3B3A33] bg-[#151716] p-3 text-xs text-[#A9A49A]">
                        <span className="text-[#B59A68] font-mono font-semibold">Query / Matter: </span>
                        <span className="text-[#F4EFE5]">&quot;{act.query_text}&quot;</span>
                      </div>
                    )}

                    {act.resource_id && (
                      <div className="text-[11px] font-mono text-[#A9A49A]">
                        Resource / Case ID: <span className="text-[#F4EFE5]">{act.resource_id}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Pagination Controls */}
            <div className="border-t border-[#3B3A33] p-4 flex items-center justify-between text-xs text-[#A9A49A] bg-[#151716]/40">
              <div>
                Showing <span className="font-semibold text-[#F4EFE5]">{activities.length}</span> of{' '}
                <span className="font-semibold text-[#F4EFE5]">{total}</span> activities
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0 || isLoading}
                  className="p-1.5 rounded-lg border border-[#3B3A33] bg-[#1D211F] text-[#F4EFE5] hover:border-[#B59A68]/50 disabled:opacity-40 transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="font-mono text-xs">
                  Page {page + 1} of {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                  disabled={page >= totalPages - 1 || isLoading}
                  className="p-1.5 rounded-lg border border-[#3B3A33] bg-[#1D211F] text-[#F4EFE5] hover:border-[#B59A68]/50 disabled:opacity-40 transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

        </div>
      </div>
    </RoleGuard>
  );
}
