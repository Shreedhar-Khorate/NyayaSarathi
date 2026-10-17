'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Activity,
  Search,
  FileText,
  ScanLine,
  TrendingUp,
  BookOpen,
  Filter,
  RefreshCw,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Clock,
} from 'lucide-react';
import { RoleGuard } from '@/components/auth/RoleGuard';
import { fetchAdvocateActivity, type AdvocateActivityItem } from '@/lib/auth';

const ACTIVITY_ICONS: Record<string, React.ElementType> = {
  LEGAL_RESEARCH: BookOpen,
  DOCUMENT_UPLOAD: ScanLine,
  OCR_ANALYSIS: ScanLine,
  PREDICTION: TrendingUp,
  DRAFTING: FileText,
  DEFAULT: Activity,
};

const ACTIVITY_COLORS: Record<string, string> = {
  LEGAL_RESEARCH: '#4F8EF7',
  DOCUMENT_UPLOAD: '#6BD28E',
  OCR_ANALYSIS: '#6BD28E',
  PREDICTION: '#F97316',
  DRAFTING: '#A78BFA',
  DEFAULT: '#B59A68',
};

const TYPES = [
  { value: '', label: 'All Activity' },
  { value: 'LEGAL_RESEARCH', label: 'Legal Research' },
  { value: 'DRAFTING', label: 'Drafting' },
  { value: 'OCR_ANALYSIS', label: 'OCR Analysis' },
  { value: 'DOCUMENT_UPLOAD', label: 'Document Upload' },
  { value: 'PREDICTION', label: 'AI Predictions' },
];

const PAGE_SIZE = 15;

function formatDate(dateStr: string) {
  try {
    return new Date(dateStr).toLocaleString('en-IN', {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  } catch {
    return dateStr;
  }
}

export default function AdvocateActivityPage() {
  const [items, setItems] = useState<AdvocateActivityItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [typeFilter, setTypeFilter] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetchAdvocateActivity(typeFilter || undefined, PAGE_SIZE, page * PAGE_SIZE);
      setItems(res.items);
      setTotal(res.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load activity.');
    } finally {
      setIsLoading(false);
    }
  }, [typeFilter, page]);

  useEffect(() => { load(); }, [load]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <RoleGuard allowedRoles={['ADVOCATE', 'ADMIN']} portalName="Advocate Activity Log">
      <div className="min-h-screen bg-[#151716] pt-28 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="fixed inset-0 pointer-events-none">
          <div className="absolute top-20 right-1/4 w-96 h-96 bg-[#4F8EF7]/5 rounded-full blur-3xl" />
        </div>

        <div className="max-w-5xl mx-auto relative z-10 space-y-8">
          {/* Header */}
          <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }}>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl bg-[#4F8EF7]/15 border border-[#4F8EF7]/35 flex items-center justify-center">
                <Activity className="w-5 h-5 text-[#4F8EF7]" />
              </div>
              <span className="text-xs font-mono uppercase tracking-widest text-[#4F8EF7] bg-[#4F8EF7]/10 px-3 py-1 rounded-full border border-[#4F8EF7]/25">
                Advocate Activity
              </span>
            </div>
            <h1 className="font-display text-3xl font-bold text-[#F4EFE5]">Activity Log</h1>
            <p className="text-sm text-[#A9A49A] mt-1">Your complete research and drafting session history</p>
          </motion.div>

          {/* Filters */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 text-[#A9A49A]">
              <Filter className="w-4 h-4" />
              <span className="text-xs font-semibold uppercase tracking-wide">Filter:</span>
            </div>
            {TYPES.map(({ value, label }) => (
              <button
                key={value}
                onClick={() => { setTypeFilter(value); setPage(0); }}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  typeFilter === value
                    ? 'bg-[#4F8EF7] text-white border border-[#4F8EF7]'
                    : 'bg-[#1D211F] text-[#A9A49A] border border-[#2A2E2B] hover:text-[#F4EFE5] hover:border-[#3B3A33]'
                }`}
              >
                {label}
              </button>
            ))}
            <button
              onClick={load}
              className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#2A2E2B] bg-[#1D211F] text-xs text-[#A9A49A] hover:text-[#F4EFE5] transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>

          {/* Error */}
          {error && (
            <div className="rounded-xl border border-[#6E2634]/40 bg-[#6E2634]/10 p-4 flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-[#E25C6F] flex-shrink-0" />
              <p className="text-sm text-[#F4EFE5]">{error}</p>
            </div>
          )}

          {/* Activity List */}
          <div className="space-y-2">
            {isLoading ? (
              [...Array(6)].map((_, i) => (
                <div key={i} className="rounded-xl border border-[#2A2E2B] bg-[#1D211F]/80 p-4 h-16 animate-pulse" />
              ))
            ) : items.length === 0 ? (
              <div className="rounded-2xl border border-[#2A2E2B] bg-[#1D211F]/80 p-12 text-center">
                <Search className="w-12 h-12 text-[#3B3A33] mx-auto mb-4" />
                <p className="text-[#A9A49A] font-sans text-sm">No activity records found.</p>
              </div>
            ) : (
              items.map((item, i) => {
                const Icon = ACTIVITY_ICONS[item.activity_type] ?? ACTIVITY_ICONS.DEFAULT;
                const color = ACTIVITY_COLORS[item.activity_type] ?? ACTIVITY_COLORS.DEFAULT;
                return (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.03 }}
                    className="flex items-start gap-4 rounded-xl border border-[#2A2E2B] bg-[#1D211F]/80 p-4 hover:border-[#3B3A33] transition-all group"
                  >
                    <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5" style={{ backgroundColor: `${color}18`, border: `1px solid ${color}30` }}>
                      <Icon className="w-4 h-4" style={{ color }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-[#F4EFE5] text-sm truncate">{item.title}</p>
                      {item.query_text && (
                        <p className="text-xs text-[#A9A49A] mt-0.5 truncate">"{item.query_text}"</p>
                      )}
                    </div>
                    <div className="flex flex-col items-end gap-1 flex-shrink-0">
                      <span className="text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded" style={{ backgroundColor: `${color}18`, color }}>
                        {item.activity_type.replace('_', ' ')}
                      </span>
                      <span className="flex items-center gap-1 text-[10px] text-[#6B6B60]">
                        <Clock className="w-3 h-3" />
                        {formatDate(item.created_at)}
                      </span>
                    </div>
                  </motion.div>
                );
              })
            )}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-2">
              <span className="text-xs text-[#A9A49A]">
                Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, total)} of {total}
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(p => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="w-8 h-8 rounded-lg border border-[#2A2E2B] bg-[#1D211F] flex items-center justify-center text-[#A9A49A] hover:text-[#F4EFE5] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-xs text-[#F4EFE5] font-mono">{page + 1} / {totalPages}</span>
                <button
                  onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                  disabled={page >= totalPages - 1}
                  className="w-8 h-8 rounded-lg border border-[#2A2E2B] bg-[#1D211F] flex items-center justify-center text-[#A9A49A] hover:text-[#F4EFE5] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </RoleGuard>
  );
}
