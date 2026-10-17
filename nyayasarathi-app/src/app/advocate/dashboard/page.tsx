'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  Scale,
  BookOpen,
  FileText,
  Activity,
  Briefcase,
  Search,
  Sparkles,
  RefreshCw,
  AlertCircle,
  ArrowRight,
  ScanLine,
  Gavel,
  TrendingUp,
  Users,
} from 'lucide-react';
import { RoleGuard } from '@/components/auth/RoleGuard';
import { fetchAdvocateMetrics, type AdvocateMetrics } from '@/lib/auth';

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.08, duration: 0.5, ease: 'easeOut' as const } }),
};

const TOOLS = [
  { href: '/legal-research', icon: Search, label: 'Legal Research', desc: 'Search case law and statutes', color: '#4F8EF7' },
  { href: '/ocr', icon: ScanLine, label: 'Document OCR', desc: 'Extract text from legal PDFs', color: '#B59A68' },
  { href: '/predictor', icon: TrendingUp, label: 'Judgment Predictor', desc: 'AI-powered case outcome analysis', color: '#6BD28E' },
  { href: '/drafts', icon: FileText, label: 'Draft Generator', desc: 'Generate legal documents & petitions', color: '#A78BFA' },
];

export default function AdvocateDashboardPage() {
  const [metrics, setMetrics] = useState<AdvocateMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const m = await fetchAdvocateMetrics();
      setMetrics(m);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load advocate dashboard.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const stats = metrics
    ? [
        { label: 'Total Activities', value: metrics.total_activities, icon: Activity, color: '#4F8EF7' },
        { label: 'Legal Research', value: metrics.legal_research_count, icon: BookOpen, color: '#B59A68' },
        { label: 'Drafts Created', value: metrics.drafts_created, icon: FileText, color: '#A78BFA' },
        { label: 'Docs Analysed', value: metrics.documents_analysed, icon: ScanLine, color: '#6BD28E' },
        { label: 'AI Predictions', value: metrics.predictions_run, icon: Sparkles, color: '#F97316' },
      ]
    : [];

  return (
    <RoleGuard allowedRoles={['ADVOCATE', 'ADMIN']} portalName="Advocate Bar Portal">
      <div className="min-h-screen bg-[#151716] pt-28 pb-20 px-4 sm:px-6 lg:px-8">
        {/* Background Glows */}
        <div className="fixed inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-[#4F8EF7]/6 rounded-full blur-3xl" />
          <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-[#B59A68]/6 rounded-full blur-3xl" />
        </div>

        <div className="max-w-7xl mx-auto relative z-10 space-y-10">
          {/* Header */}
          <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 rounded-xl bg-[#4F8EF7]/20 border border-[#4F8EF7]/40 flex items-center justify-center">
                    <Briefcase className="w-5 h-5 text-[#4F8EF7]" />
                  </div>
                  <span className="text-xs font-mono uppercase tracking-widest text-[#4F8EF7] bg-[#4F8EF7]/10 px-3 py-1 rounded-full border border-[#4F8EF7]/30">
                    Advocate Portal
                  </span>
                </div>
                <h1 className="font-display text-3xl sm:text-4xl font-bold text-[#F4EFE5]">
                  {isLoading ? 'Loading...' : `Welcome, ${metrics?.advocate_name?.split(' ')[0] ?? 'Advocate'}`}
                </h1>
                <p className="font-sans text-sm text-[#A9A49A] mt-1">
                  {metrics?.organization} · {metrics?.designation}
                </p>
              </div>
              <button
                onClick={loadData}
                className="flex items-center gap-2 px-4 py-2 rounded-xl border border-[#3B3A33] bg-[#1D211F] text-xs font-semibold text-[#A9A49A] hover:text-[#F4EFE5] hover:border-[#4F8EF7]/50 transition-all"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </motion.div>

          {/* Error Banner */}
          {error && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="rounded-xl border border-[#6E2634]/40 bg-[#6E2634]/10 p-4 flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-[#E25C6F] flex-shrink-0" />
              <p className="text-sm text-[#F4EFE5]">{error}</p>
            </motion.div>
          )}

          {/* KPI Stats */}
          {!isLoading && metrics && (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
              {stats.map(({ label, value, icon: Icon, color }, i) => (
                <motion.div
                  key={label}
                  custom={i}
                  initial="hidden"
                  animate="visible"
                  variants={fadeUp}
                  className="rounded-2xl border border-[#2A2E2B] bg-[#1D211F]/80 p-5 relative overflow-hidden group hover:border-[#3B3A33] transition-all"
                >
                  <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity" style={{ background: `radial-gradient(ellipse at top left, ${color}08 0%, transparent 70%)` }} />
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center mb-3" style={{ backgroundColor: `${color}18`, border: `1px solid ${color}30` }}>
                    <Icon className="w-4 h-4" style={{ color }} />
                  </div>
                  <p className="text-2xl font-bold text-[#F4EFE5]">{value.toLocaleString()}</p>
                  <p className="text-xs text-[#A9A49A] mt-1">{label}</p>
                </motion.div>
              ))}
            </div>
          )}

          {/* Loading skeleton */}
          {isLoading && (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="rounded-2xl border border-[#2A2E2B] bg-[#1D211F]/80 p-5 animate-pulse h-28" />
              ))}
            </div>
          )}

          {/* Quick Tools */}
          <motion.section initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
            <h2 className="font-display text-lg font-semibold text-[#F4EFE5] mb-4 flex items-center gap-2">
              <Gavel className="w-5 h-5 text-[#B59A68]" />
              Legal Research Tools
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {TOOLS.map(({ href, icon: Icon, label, desc, color }, i) => (
                <motion.div key={label} custom={i + 3} initial="hidden" animate="visible" variants={fadeUp}>
                  <Link
                    href={href}
                    className="group flex flex-col gap-3 rounded-2xl border border-[#2A2E2B] bg-[#1D211F]/80 p-5 hover:border-[#3B3A33] transition-all relative overflow-hidden"
                  >
                    <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300" style={{ background: `radial-gradient(ellipse at top left, ${color}10 0%, transparent 70%)` }} />
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center relative z-10" style={{ backgroundColor: `${color}18`, border: `1px solid ${color}35` }}>
                      <Icon className="w-5 h-5" style={{ color }} />
                    </div>
                    <div className="relative z-10">
                      <p className="font-semibold text-[#F4EFE5] text-sm group-hover:text-white transition-colors">{label}</p>
                      <p className="text-xs text-[#A9A49A] mt-0.5">{desc}</p>
                    </div>
                    <ArrowRight className="w-4 h-4 text-[#A9A49A] group-hover:text-[#F4EFE5] group-hover:translate-x-1 transition-all relative z-10 self-end" />
                  </Link>
                </motion.div>
              ))}
            </div>
          </motion.section>

          {/* Navigation Links */}
          <motion.section initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }}>
            <h2 className="font-display text-lg font-semibold text-[#F4EFE5] mb-4 flex items-center gap-2">
              <Users className="w-5 h-5 text-[#B59A68]" />
              Advocate Navigation
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Link
                href="/advocate/activity"
                className="group flex items-center gap-4 rounded-2xl border border-[#2A2E2B] bg-[#1D211F]/80 p-5 hover:border-[#4F8EF7]/40 transition-all"
              >
                <div className="w-10 h-10 rounded-xl bg-[#4F8EF7]/15 border border-[#4F8EF7]/30 flex items-center justify-center">
                  <Activity className="w-5 h-5 text-[#4F8EF7]" />
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-[#F4EFE5] text-sm">Activity History</p>
                  <p className="text-xs text-[#A9A49A] mt-0.5">All your research and drafting sessions</p>
                </div>
                <ArrowRight className="w-4 h-4 text-[#A9A49A] group-hover:text-[#4F8EF7] group-hover:translate-x-1 transition-all" />
              </Link>

              <Link
                href="/advocate/nominate"
                className="group flex items-center gap-4 rounded-2xl border border-[#2A2E2B] bg-[#1D211F]/80 p-5 hover:border-[#B59A68]/40 transition-all"
              >
                <div className="w-10 h-10 rounded-xl bg-[#B59A68]/15 border border-[#B59A68]/30 flex items-center justify-center">
                  <Scale className="w-5 h-5 text-[#B59A68]" />
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-[#F4EFE5] text-sm">Judge Nomination</p>
                  <p className="text-xs text-[#A9A49A] mt-0.5">Judges can nominate peers to the bench</p>
                </div>
                <ArrowRight className="w-4 h-4 text-[#A9A49A] group-hover:text-[#B59A68] group-hover:translate-x-1 transition-all" />
              </Link>
            </div>
          </motion.section>
        </div>
      </div>
    </RoleGuard>
  );
}
