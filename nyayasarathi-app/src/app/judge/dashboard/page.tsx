'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  Scale,
  BookOpen,
  Activity,
  Briefcase,
  Building2,
  Calendar,
  ArrowRight,
  Shield,
  FileText,
  Search,
  Sparkles,
  RefreshCw,
  AlertCircle,
  ExternalLink,
} from 'lucide-react';
import { RoleGuard } from '@/components/auth/RoleGuard';
import {
  fetchJudgeMetrics,
  fetchJudgeActivities,
  type JudgeMetrics,
  type JudgeActivityItem,
} from '@/lib/auth';

export default function JudgeDashboardPage() {
  const [metrics, setMetrics] = useState<JudgeMetrics | null>(null);
  const [recentActivities, setRecentActivities] = useState<JudgeActivityItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [m, act] = await Promise.all([
        fetchJudgeMetrics(),
        fetchJudgeActivities(undefined, 5, 0),
      ]);
      setMetrics(m);
      setRecentActivities(act.items);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve judicial bench metrics.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <RoleGuard allowedRoles={['JUDGE', 'ADMIN']} portalName="Judicial Bench Operations">
      <div className="min-h-screen bg-[#151716] pt-28 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto space-y-8">

          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-[#3B3A33]/80 pb-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2.5 py-0.5 rounded text-[11px] font-mono uppercase tracking-wider bg-[#6E2634]/30 text-[#E25C6F] border border-[#6E2634]/60">
                  Judicial Chamber
                </span>
                <span className="text-[#A9A49A] text-xs">
                  • {metrics?.bench_designation || 'Presiding Judicial Bench'}
                </span>
              </div>
              <h1 className="font-display text-3xl sm:text-4xl font-bold text-[#F4EFE5] tracking-tight">
                {metrics?.judge_name || "Hon'ble Justice Chamber"}
              </h1>
              <p className="font-sans text-sm text-[#A9A49A] mt-1">
                {metrics?.court_jurisdiction || 'High Court of Judicature'} — Case Analysis & Decision Support
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={loadData}
                disabled={isLoading}
                className="flex items-center gap-2 rounded-xl border border-[#3B3A33] bg-[#1D211F] px-4 py-2 font-sans text-xs font-semibold text-[#F4EFE5] hover:border-[#B59A68]/60 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 text-[#B59A68] ${isLoading ? 'animate-spin' : ''}`} />
                <span>Refresh Chamber</span>
              </button>

              <Link
                href="/judge/cases"
                className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#6E2634] to-[#8A3545] border border-[#B59A68]/40 px-4 py-2 font-sans text-xs font-semibold text-[#F4EFE5] shadow-lg shadow-[#6E2634]/20 hover:brightness-110 transition-all"
              >
                <Scale className="w-3.5 h-3.5 text-[#B59A68]" />
                <span>Examine Bench Precedents</span>
              </Link>
            </div>
          </div>

          {error && (
            <div className="rounded-xl border border-[#6E2634] bg-[#6E2634]/20 p-4 flex items-center gap-3 text-sm text-[#E25C6F]">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Metric KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Accessible Precedents */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="rounded-2xl border border-[#3B3A33] bg-[#1D211F]/70 p-6 backdrop-blur-md relative overflow-hidden group hover:border-[#B59A68]/40 transition-colors"
            >
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-sans uppercase tracking-wider text-[#A9A49A] font-semibold">
                  Authorized Precedents
                </span>
                <div className="w-10 h-10 rounded-xl bg-[#B59A68]/15 border border-[#B59A68]/30 flex items-center justify-center">
                  <BookOpen className="w-5 h-5 text-[#B59A68]" />
                </div>
              </div>
              <div className="font-display text-3xl font-bold text-[#F4EFE5]">
                {isLoading ? '...' : metrics?.accessible_precedents ?? 0}
              </div>
              <div className="mt-2 text-xs text-[#A9A49A]">
                <span>Supreme Court & High Court indexed authorities</span>
              </div>
            </motion.div>

            {/* Bench Dockets */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.05 }}
              className="rounded-2xl border border-[#3B3A33] bg-[#1D211F]/70 p-6 backdrop-blur-md relative overflow-hidden group hover:border-[#B59A68]/40 transition-colors"
            >
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-sans uppercase tracking-wider text-[#A9A49A] font-semibold">
                  Bench Matters in Docket
                </span>
                <div className="w-10 h-10 rounded-xl bg-[#6E2634]/30 border border-[#6E2634] flex items-center justify-center">
                  <Scale className="w-5 h-5 text-[#E25C6F]" />
                </div>
              </div>
              <div className="font-display text-3xl font-bold text-[#F4EFE5]">
                {isLoading ? '...' : (metrics?.assigned_matters_count ?? 0)}
              </div>
              <div className="mt-2 text-xs text-[#A9A49A]">
                <span>Active litigation matters awaiting judgment</span>
              </div>
            </motion.div>

            {/* Judicial Research Activities */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.1 }}
              className="rounded-2xl border border-[#3B3A33] bg-[#1D211F]/70 p-6 backdrop-blur-md relative overflow-hidden group hover:border-[#B59A68]/40 transition-colors"
            >
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-sans uppercase tracking-wider text-[#A9A49A] font-semibold">
                  Bench Research Inquiries
                </span>
                <div className="w-10 h-10 rounded-xl bg-[#242925] border border-[#3B3A33] flex items-center justify-center">
                  <Activity className="w-5 h-5 text-[#71877A]" />
                </div>
              </div>
              <div className="font-display text-3xl font-bold text-[#F4EFE5]">
                {isLoading ? '...' : (metrics?.recent_research_activities ?? 0)}
              </div>
              <div className="mt-2 text-xs text-[#A9A49A]">
                <span>Confidential queries & case analysis in chamber</span>
              </div>
            </motion.div>
          </div>

          {/* Quick Bench Portals */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Link
              href="/judge/cases"
              className="group rounded-2xl border border-[#3B3A33] bg-[#1D211F]/50 p-6 hover:bg-[#1D211F] hover:border-[#B59A68]/50 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <BookOpen className="w-5 h-5 text-[#B59A68]" />
                  <h3 className="font-display text-lg font-semibold text-[#F4EFE5] group-hover:text-[#B59A68] transition-colors">
                    Bench Cases & Precedents
                  </h3>
                </div>
                <p className="font-sans text-xs text-[#A9A49A] leading-relaxed">
                  Search 740+ verified Indian court judgments, examine statutory mappings, and cross-reference disposal outcomes.
                </p>
              </div>
              <div className="mt-4 flex items-center gap-1.5 text-xs font-semibold text-[#B59A68]">
                <span>Browse Judgments</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>

            <Link
              href="/judge/activity"
              className="group rounded-2xl border border-[#3B3A33] bg-[#1D211F]/50 p-6 hover:bg-[#1D211F] hover:border-[#B59A68]/50 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Activity className="w-5 h-5 text-[#B59A68]" />
                  <h3 className="font-display text-lg font-semibold text-[#F4EFE5] group-hover:text-[#B59A68] transition-colors">
                    Judicial Activity Stream
                  </h3>
                </div>
                <p className="font-sans text-xs text-[#A9A49A] leading-relaxed">
                  View your filterable chamber session activity, past legal research queries, and document OCR inspections.
                </p>
              </div>
              <div className="mt-4 flex items-center gap-1.5 text-xs font-semibold text-[#B59A68]">
                <span>Open Activity Feed</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>

            <Link
              href="/predictor"
              className="group rounded-2xl border border-[#3B3A33] bg-[#1D211F]/50 p-6 hover:bg-[#1D211F] hover:border-[#B59A68]/50 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="w-5 h-5 text-[#B59A68]" />
                  <h3 className="font-display text-lg font-semibold text-[#F4EFE5] group-hover:text-[#B59A68] transition-colors">
                    Judgment Predictor Engine
                  </h3>
                </div>
                <p className="font-sans text-xs text-[#A9A49A] leading-relaxed">
                  Analyze litigation matters with calibrated ML outcome likelihood, citation verification, and precedent grounding.
                </p>
              </div>
              <div className="mt-4 flex items-center gap-1.5 text-xs font-semibold text-[#B59A68]">
                <span>Launch Predictor</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>
          </div>

          {/* Privacy Scoped Activity Overview */}
          <div className="rounded-2xl border border-[#3B3A33] bg-[#1D211F]/60 p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-display text-lg font-semibold text-[#F4EFE5]">
                  Recent Chamber Activities
                </h3>
                <p className="text-xs text-[#A9A49A]">
                  Scoped strictly to your judicial session. Private citizen research is protected.
                </p>
              </div>
              <Link
                href="/judge/activity"
                className="text-xs font-medium text-[#B59A68] hover:underline"
              >
                View Full Feed
              </Link>
            </div>

            {recentActivities.length > 0 ? (
              <div className="divide-y divide-[#3B3A33]/40">
                {recentActivities.map((act) => (
                  <div key={act.id} className="py-3.5 flex items-center justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-[#6E2634]/30 text-[#E25C6F] border border-[#6E2634]/50">
                          {act.activity_type}
                        </span>
                        <h4 className="text-xs font-semibold text-[#F4EFE5]">
                          {act.title}
                        </h4>
                      </div>
                      {act.query_text && (
                        <p className="text-[11px] text-[#A9A49A] font-mono italic max-w-xl truncate">
                          &quot;{act.query_text}&quot;
                        </p>
                      )}
                    </div>

                    <div className="text-right shrink-0">
                      <span className="text-[10px] font-mono text-[#A9A49A]">
                        {new Date(act.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-10 text-center text-xs text-[#A9A49A]">
                No recent chamber activities recorded. Legal research and document analyses conducted in your session will appear here.
              </div>
            )}
          </div>

        </div>
      </div>
    </RoleGuard>
  );
}
