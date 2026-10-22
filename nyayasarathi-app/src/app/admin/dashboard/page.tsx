'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  Users,
  ShieldCheck,
  Scale,
  History,
  Activity,
  BookOpen,
  ArrowRight,
  TrendingUp,
  UserCheck,
  AlertCircle,
  RefreshCw,
  Clock,
} from 'lucide-react';
import { RoleGuard } from '@/components/auth/RoleGuard';
import { fetchAdminMetrics, type AdminMetrics } from '@/lib/auth';

export default function AdminDashboardPage() {
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchAdminMetrics();
      setMetrics(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve administrative metrics.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <RoleGuard allowedRoles={['ADMIN']} portalName="Administrative Operations Portal">
      <div className="min-h-screen bg-[#151716] pt-28 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto space-y-8">

          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-[#3B3A33]/80 pb-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2.5 py-0.5 rounded text-[11px] font-mono uppercase tracking-wider bg-[#6E2634]/30 text-[#B59A68] border border-[#B59A68]/30">
                  Judicial Administration
                </span>
                <span className="text-[#A9A49A] text-xs">• Real-time Metrics</span>
              </div>
              <h1 className="font-display text-3xl sm:text-4xl font-bold text-[#F4EFE5] tracking-tight">
                System Administrator Dashboard
              </h1>
              <p className="font-sans text-sm text-[#A9A49A] mt-1">
                Oversee platform role allocations, judicial clearance, system-wide metrics, and immutable audit logs.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={loadData}
                disabled={isLoading}
                className="flex items-center gap-2 rounded-xl border border-[#3B3A33] bg-[#1D211F] px-4 py-2 font-sans text-xs font-semibold text-[#F4EFE5] hover:border-[#B59A68]/60 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 text-[#B59A68] ${isLoading ? 'animate-spin' : ''}`} />
                <span>Refresh Data</span>
              </button>

              <Link
                href="/admin/users"
                className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#6E2634] to-[#8A3545] border border-[#B59A68]/40 px-4 py-2 font-sans text-xs font-semibold text-[#F4EFE5] shadow-lg shadow-[#6E2634]/20 hover:brightness-110 transition-all"
              >
                <UserCheck className="w-3.5 h-3.5 text-[#B59A68]" />
                <span>Manage User Roles</span>
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
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {/* Total Users */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="rounded-2xl border border-[#3B3A33] bg-[#1D211F]/70 p-6 backdrop-blur-md relative overflow-hidden group hover:border-[#B59A68]/40 transition-colors"
            >
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-sans uppercase tracking-wider text-[#A9A49A] font-semibold">
                  Total Accounts
                </span>
                <div className="w-10 h-10 rounded-xl bg-[#B59A68]/15 border border-[#B59A68]/30 flex items-center justify-center">
                  <Users className="w-5 h-5 text-[#B59A68]" />
                </div>
              </div>
              <div className="font-display text-3xl font-bold text-[#F4EFE5]">
                {isLoading ? '...' : metrics?.total_users ?? 0}
              </div>
              <div className="mt-2 flex items-center gap-2 text-xs text-[#A9A49A]">
                <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                <span>Active platform researchers</span>
              </div>
            </motion.div>

            {/* Advocate & Counsel Accounts */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.05 }}
              className="rounded-2xl border border-[#3B3A33] bg-[#1D211F]/70 p-6 backdrop-blur-md relative overflow-hidden group hover:border-[#B59A68]/40 transition-colors"
            >
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-sans uppercase tracking-wider text-[#A9A49A] font-semibold">
                  Advocates & Counsel
                </span>
                <div className="w-10 h-10 rounded-xl bg-[#B59A68]/15 border border-[#B59A68]/30 flex items-center justify-center">
                  <Scale className="w-5 h-5 text-[#B59A68]" />
                </div>
              </div>
              <div className="font-display text-3xl font-bold text-[#F4EFE5]">
                {isLoading ? '...' : (metrics?.role_counts?.ADVOCATE ?? 0)}
              </div>
              <div className="mt-2 text-xs text-[#A9A49A]">
                <span>Verified bar practitioners</span>
              </div>
            </motion.div>

            {/* Indexed Precedents */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.1 }}
              className="rounded-2xl border border-[#3B3A33] bg-[#1D211F]/70 p-6 backdrop-blur-md relative overflow-hidden group hover:border-[#B59A68]/40 transition-colors"
            >
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-sans uppercase tracking-wider text-[#A9A49A] font-semibold">
                  Court Precedents
                </span>
                <div className="w-10 h-10 rounded-xl bg-[#B59A68]/15 border border-[#B59A68]/30 flex items-center justify-center">
                  <BookOpen className="w-5 h-5 text-[#B59A68]" />
                </div>
              </div>
              <div className="font-display text-3xl font-bold text-[#F4EFE5]">
                {isLoading ? '...' : (metrics?.total_judgments ?? 0)}
              </div>
              <div className="mt-2 text-xs text-[#A9A49A]">
                <span>High & Supreme Court records</span>
              </div>
            </motion.div>

            {/* Research Operations */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.15 }}
              className="rounded-2xl border border-[#3B3A33] bg-[#1D211F]/70 p-6 backdrop-blur-md relative overflow-hidden group hover:border-[#B59A68]/40 transition-colors"
            >
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-sans uppercase tracking-wider text-[#A9A49A] font-semibold">
                  Activities Logged
                </span>
                <div className="w-10 h-10 rounded-xl bg-[#242925] border border-[#3B3A33] flex items-center justify-center">
                  <Activity className="w-5 h-5 text-[#71877A]" />
                </div>
              </div>
              <div className="font-display text-3xl font-bold text-[#F4EFE5]">
                {isLoading ? '...' : (metrics?.total_activities ?? 0)}
              </div>
              <div className="mt-2 text-xs text-[#A9A49A]">
                <span>OCR, Q&A, and case analyses</span>
              </div>
            </motion.div>
          </div>

          {/* Quick Access Portals */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Link
              href="/admin/users"
              className="group rounded-2xl border border-[#3B3A33] bg-[#1D211F]/50 p-6 hover:bg-[#1D211F] hover:border-[#B59A68]/50 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <UserCheck className="w-5 h-5 text-[#B59A68]" />
                  <h3 className="font-display text-lg font-semibold text-[#F4EFE5] group-hover:text-[#B59A68] transition-colors">
                    User Role Management
                  </h3>
                </div>
                <p className="font-sans text-xs text-[#A9A49A] leading-relaxed">
                  Search user directory, filter by role (USER, ADVOCATE, ADMIN), manage clearance levels, and enforce strict access boundaries.
                </p>
              </div>
              <div className="mt-4 flex items-center gap-1.5 text-xs font-semibold text-[#B59A68]">
                <span>Open User Directory</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>

            <Link
              href="/admin/audit-logs"
              className="group rounded-2xl border border-[#3B3A33] bg-[#1D211F]/50 p-6 hover:bg-[#1D211F] hover:border-[#B59A68]/50 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <History className="w-5 h-5 text-[#B59A68]" />
                  <h3 className="font-display text-lg font-semibold text-[#F4EFE5] group-hover:text-[#B59A68] transition-colors">
                    Role Mutation Audit Trail
                  </h3>
                </div>
                <p className="font-sans text-xs text-[#A9A49A] leading-relaxed">
                  Review durable, chronological audit records for every permission upgrade or revocation across the institution.
                </p>
              </div>
              <div className="mt-4 flex items-center gap-1.5 text-xs font-semibold text-[#B59A68]">
                <span>Inspect Audit Trail</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>

            <Link
              href="/advocate/dashboard"
              className="group rounded-2xl border border-[#3B3A33] bg-[#1D211F]/50 p-6 hover:bg-[#1D211F] hover:border-[#B59A68]/50 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Scale className="w-5 h-5 text-[#B59A68]" />
                  <h3 className="font-display text-lg font-semibold text-[#F4EFE5] group-hover:text-[#B59A68] transition-colors">
                    Advocate Command View
                  </h3>
                </div>
                <p className="font-sans text-xs text-[#A9A49A] leading-relaxed">
                  Preview research dockets, drafting tools, and legal activity analytics as seen by practicing bar advocates.
                </p>
              </div>
              <div className="mt-4 flex items-center gap-1.5 text-xs font-semibold text-[#B59A68]">
                <span>Switch to Advocate View</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>
          </div>

          {/* Role Distribution & Recent Role Changes */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Role Breakdown */}
            <div className="rounded-2xl border border-[#3B3A33] bg-[#1D211F]/60 p-6">
              <h3 className="font-display text-lg font-semibold text-[#F4EFE5] mb-4">
                Role Distribution
              </h3>
              <div className="space-y-4">
                {metrics?.role_counts && Object.entries(metrics.role_counts).map(([role, count]) => {
                  const total = metrics.total_users || 1;
                  const pct = Math.round((count / total) * 100);
                  const isJudge = role === 'JUDGE';
                  const isAdmin = role === 'ADMIN';

                  return (
                    <div key={role} className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-mono font-semibold text-[#F4EFE5] uppercase">
                          {role}
                        </span>
                        <span className="text-[#A9A49A]">
                          {count} ({pct}%)
                        </span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-[#151716] overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            isAdmin ? 'bg-[#B59A68]' : isJudge ? 'bg-[#6E2634]' : 'bg-[#71877A]'
                          }`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Recent Role Audit Preview */}
            <div className="lg:col-span-2 rounded-2xl border border-[#3B3A33] bg-[#1D211F]/60 p-6 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-display text-lg font-semibold text-[#F4EFE5]">
                    Recent Role Changes
                  </h3>
                  <Link
                    href="/admin/audit-logs"
                    className="text-xs font-medium text-[#B59A68] hover:underline"
                  >
                    View All
                  </Link>
                </div>

                {metrics?.recent_role_changes && metrics.recent_role_changes.length > 0 ? (
                  <div className="divide-y divide-[#3B3A33]/50">
                    {metrics.recent_role_changes.map((audit) => (
                      <div key={audit.id} className="py-3 flex items-center justify-between gap-4">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold text-[#F4EFE5]">
                              {audit.target_name || audit.target_email || 'User'}
                            </span>
                            <span className="text-[10px] font-mono text-[#A9A49A]">
                              ({audit.old_role} → <strong className="text-[#B59A68]">{audit.new_role}</strong>)
                            </span>
                          </div>
                          <p className="text-[11px] text-[#A9A49A] mt-0.5 truncate max-w-md">
                            Reason: {audit.reason || 'Administrative adjustment'}
                          </p>
                        </div>
                        <div className="text-right shrink-0">
                          <span className="text-[10px] font-mono text-[#A9A49A]">
                            {new Date(audit.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-12 text-center text-xs text-[#A9A49A]">
                    No role mutations recorded yet. Use the User Management portal to promote eligible users.
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Recent Registrations Table */}
          <div className="rounded-2xl border border-[#3B3A33] bg-[#1D211F]/60 p-6 overflow-hidden">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-display text-lg font-semibold text-[#F4EFE5]">
                Recent Account Registrations
              </h3>
              <Link
                href="/admin/users"
                className="text-xs font-medium text-[#B59A68] hover:underline"
              >
                Manage All Users
              </Link>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-[#F4EFE5]">
                <thead className="border-b border-[#3B3A33] text-[#A9A49A] font-mono uppercase text-[10px]">
                  <tr>
                    <th className="py-3 px-4">User</th>
                    <th className="py-3 px-4">Role</th>
                    <th className="py-3 px-4">Organization</th>
                    <th className="py-3 px-4">Registered</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#3B3A33]/40">
                  {metrics?.recent_users && metrics.recent_users.map((u) => (
                    <tr key={u.id} className="hover:bg-white/[0.02]">
                      <td className="py-3 px-4">
                        <div className="font-semibold text-[#F4EFE5]">{u.full_name || 'Anonymous'}</div>
                        <div className="text-[11px] text-[#A9A49A] font-mono">{u.email}</div>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                          u.role === 'ADMIN'
                            ? 'bg-[#B59A68]/20 text-[#B59A68] border border-[#B59A68]/40'
                            : u.role === 'JUDGE'
                            ? 'bg-[#6E2634]/30 text-[#E25C6F] border border-[#6E2634]/50'
                            : 'bg-white/5 text-[#A9A49A]'
                        }`}>
                          {u.role}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-[#A9A49A]">
                        {u.organization || 'General Public'}
                      </td>
                      <td className="py-3 px-4 text-[#A9A49A] font-mono">
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      </div>
    </RoleGuard>
  );
}
