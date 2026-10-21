'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
  History,
  Shield,
  Search,
  ChevronLeft,
  ChevronRight,
  Loader2,
  RefreshCw,
  AlertCircle,
  ArrowRight,
  User,
  Calendar,
  FileText,
} from 'lucide-react';
import { RoleGuard } from '@/components/auth/RoleGuard';
import { fetchRoleAuditHistory, type RoleAuditItem } from '@/lib/auth';

export default function AdminAuditLogsPage() {
  const [logs, setLogs] = useState<RoleAuditItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [targetIdFilter, setTargetIdFilter] = useState('');
  const limit = 20;

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadLogs = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchRoleAuditHistory(
        targetIdFilter.trim() || undefined,
        limit,
        page * limit
      );
      setLogs(data.items);
      setTotal(data.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve role audit logs.');
    } finally {
      setIsLoading(false);
    }
  }, [page, targetIdFilter]);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <RoleGuard allowedRoles={['ADMIN']} portalName="Role Change Audit Registry">
      <div className="min-h-screen bg-[#151716] pt-28 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto space-y-6">

          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-xs text-[#A9A49A]">
            <Link href="/admin/dashboard" className="hover:text-[#B59A68] transition-colors">
              Admin Dashboard
            </Link>
            <span>/</span>
            <span className="text-[#F4EFE5]">Audit Registry</span>
          </div>

          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-[#3B3A33]/80 pb-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2.5 py-0.5 rounded text-[11px] font-mono uppercase tracking-wider bg-[#6E2634]/30 text-[#B59A68] border border-[#B59A68]/30">
                  Compliance & Governance
                </span>
                <span className="text-[#A9A49A] text-xs">• Immutable Event Store</span>
              </div>
              <h1 className="font-display text-3xl font-bold text-[#F4EFE5] tracking-tight">
                Role Mutation Audit Registry
              </h1>
              <p className="font-sans text-sm text-[#A9A49A] mt-1">
                Forensic record of all role clearance elevations, revocations, acting administrators, and reasons.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={loadLogs}
                disabled={isLoading}
                className="flex items-center gap-2 rounded-xl border border-[#3B3A33] bg-[#1D211F] px-4 py-2 font-sans text-xs font-semibold text-[#F4EFE5] hover:border-[#B59A68]/60 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 text-[#B59A68] ${isLoading ? 'animate-spin' : ''}`} />
                <span>Refresh Logs</span>
              </button>

              <Link
                href="/admin/users"
                className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#6E2634] to-[#8A3545] border border-[#B59A68]/40 px-4 py-2 font-sans text-xs font-semibold text-[#F4EFE5] shadow-lg shadow-[#6E2634]/20 hover:brightness-110 transition-all"
              >
                <span>Manage Users</span>
              </Link>
            </div>
          </div>

          {error && (
            <div className="rounded-xl border border-[#6E2634] bg-[#6E2634]/20 p-4 flex items-center gap-2 text-xs text-[#E25C6F]">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Filter Bar */}
          <div className="rounded-2xl border border-[#3B3A33] bg-[#1D211F]/70 p-4 flex flex-col sm:flex-row items-center justify-between gap-4 backdrop-blur-md">
            <div className="relative w-full sm:w-96">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#A9A49A]" />
              <input
                type="text"
                value={targetIdFilter}
                onChange={(e) => {
                  setTargetIdFilter(e.target.value);
                  setPage(0);
                }}
                placeholder="Filter by target user UUID..."
                className="w-full rounded-xl border border-[#3B3A33] bg-[#151716] pl-10 pr-4 py-2 text-xs text-[#F4EFE5] placeholder-[#A9A49A]/60 focus:border-[#B59A68] focus:outline-none transition-colors font-mono"
              />
            </div>

            <div className="text-xs font-mono text-[#A9A49A]">
              Total Durable Records: <span className="font-bold text-[#F4EFE5]">{total}</span>
            </div>
          </div>

          {/* Audit Logs Table */}
          <div className="rounded-2xl border border-[#3B3A33] bg-[#1D211F]/60 overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-[#F4EFE5]">
                <thead className="border-b border-[#3B3A33] text-[#A9A49A] font-mono uppercase text-[10px] bg-[#151716]/60">
                  <tr>
                    <th className="py-3.5 px-4">Timestamp</th>
                    <th className="py-3.5 px-4">Target Account</th>
                    <th className="py-3.5 px-4">Clearance Transition</th>
                    <th className="py-3.5 px-4">Acting Administrator</th>
                    <th className="py-3.5 px-4">Stated Reason</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#3B3A33]/40">
                  {isLoading ? (
                    <tr>
                      <td colSpan={5} className="py-12 text-center text-[#A9A49A]">
                        <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-[#B59A68]" />
                        <span>Verifying forensic records...</span>
                      </td>
                    </tr>
                  ) : logs.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-12 text-center text-[#A9A49A]">
                        No role-change audit records found.
                      </td>
                    </tr>
                  ) : (
                    logs.map((log) => {
                      const isPromotion = log.new_role === 'ADVOCATE' || log.new_role === 'ADMIN';

                      return (
                        <tr key={log.id} className="hover:bg-white/[0.02] transition-colors">
                          <td className="py-3.5 px-4 text-[#A9A49A] font-mono whitespace-nowrap">
                            <div>{new Date(log.created_at).toLocaleDateString()}</div>
                            <div className="text-[10px] text-[#A9A49A]/60">
                              {new Date(log.created_at).toLocaleTimeString()}
                            </div>
                          </td>

                          <td className="py-3.5 px-4">
                            <div className="font-semibold text-[#F4EFE5]">
                              {log.target_name || 'Anonymous User'}
                            </div>
                            <div className="text-[11px] text-[#A9A49A] font-mono">
                              {log.target_email || log.target_user_id}
                            </div>
                          </td>

                          <td className="py-3.5 px-4 whitespace-nowrap">
                            <div className="flex items-center gap-1.5 font-mono text-[11px]">
                              <span className="px-2 py-0.5 rounded bg-[#151716] border border-[#3B3A33] text-[#A9A49A] uppercase">
                                {log.old_role}
                              </span>
                              <ArrowRight className="w-3 h-3 text-[#A9A49A]" />
                              <span
                                className={`px-2 py-0.5 rounded uppercase font-bold border ${
                                  isPromotion
                                    ? 'bg-[#6E2634]/30 text-[#E25C6F] border-[#6E2634]/60'
                                    : 'bg-[#242925] text-[#B59A68] border-[#B59A68]/40'
                                }`}
                              >
                                {log.new_role}
                              </span>
                            </div>
                          </td>

                          <td className="py-3.5 px-4">
                            <div className="font-semibold text-[#F4EFE5]">
                              {log.actor_name || 'System Administrator'}
                            </div>
                            <div className="text-[11px] text-[#A9A49A] font-mono">
                              {log.actor_email || log.actor_user_id}
                            </div>
                          </td>

                          <td className="py-3.5 px-4 text-[#A9A49A] max-w-xs">
                            <p className="truncate" title={log.reason || 'No reason specified'}>
                              {log.reason || <span className="italic text-[#A9A49A]/50">Administrative discretion</span>}
                            </p>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="border-t border-[#3B3A33] p-4 flex items-center justify-between text-xs text-[#A9A49A] bg-[#151716]/40">
              <div>
                Showing <span className="font-semibold text-[#F4EFE5]">{logs.length}</span> of{' '}
                <span className="font-semibold text-[#F4EFE5]">{total}</span> audit records
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
