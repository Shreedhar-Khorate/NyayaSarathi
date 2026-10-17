'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Scale,
  Search,
  UserCheck,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  Shield,
  ChevronRight,
  Loader2,
  Info,
} from 'lucide-react';
import { RoleGuard } from '@/components/auth/RoleGuard';
import {
  fetchEligibleForJudgeship,
  judgePromoteToJudge,
  type EligibleUser,
} from '@/lib/auth';

function formatDate(dateStr: string) {
  try { return new Date(dateStr).toLocaleDateString('en-IN', { dateStyle: 'medium' }); }
  catch { return dateStr; }
}

export default function AdvocateNominatePage() {
  const [eligibles, setEligibles] = useState<EligibleUser[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [promoting, setPromoting] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [reason, setReason] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const load = async (q?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetchEligibleForJudgeship(q);
      setEligibles(res.items);
      setTotal(res.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load eligible users.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handlePromote = async (userId: string, userName: string) => {
    if (!reason.trim()) {
      setError('Please provide a nomination reason before promoting.');
      return;
    }
    setPromoting(userId);
    setError(null);
    setSuccessMsg(null);
    try {
      await judgePromoteToJudge(userId, reason);
      setSuccessMsg(`${userName} has been successfully appointed to the judiciary.`);
      setSelectedId(null);
      setReason('');
      await load(search);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Promotion failed.');
    } finally {
      setPromoting(null);
    }
  };

  return (
    <RoleGuard allowedRoles={['JUDGE', 'ADMIN']} portalName="Judicial Appointment Portal">
      <div className="min-h-screen bg-[#151716] pt-28 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="fixed inset-0 pointer-events-none">
          <div className="absolute top-1/4 left-1/3 w-[500px] h-[500px] bg-[#B59A68]/5 rounded-full blur-3xl" />
        </div>

        <div className="max-w-4xl mx-auto relative z-10 space-y-8">
          {/* Header */}
          <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }}>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl bg-[#B59A68]/15 border border-[#B59A68]/35 flex items-center justify-center">
                <Scale className="w-5 h-5 text-[#B59A68]" />
              </div>
              <span className="text-xs font-mono uppercase tracking-widest text-[#B59A68] bg-[#B59A68]/10 px-3 py-1 rounded-full border border-[#B59A68]/25">
                Judicial Appointment
              </span>
            </div>
            <h1 className="font-display text-3xl font-bold text-[#F4EFE5]">Nominate to the Bench</h1>
            <p className="text-sm text-[#A9A49A] mt-1">
              As a sitting judge, you may nominate qualified advocates or users to the judiciary.
            </p>
          </motion.div>

          {/* Security Notice */}
          <div className="rounded-xl border border-[#B59A68]/25 bg-[#B59A68]/8 p-4 flex gap-3">
            <Shield className="w-5 h-5 text-[#B59A68] flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-[#F4EFE5]">Judge-Only Judicial Appointment</p>
              <p className="text-xs text-[#A9A49A] mt-1">
                Only sitting judges can nominate peers to the JUDGE role. This action creates a permanent audit record.
                Admins cannot use this pathway — they have separate role management controls.
              </p>
            </div>
          </div>

          {/* Success */}
          {successMsg && (
            <motion.div initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} className="rounded-xl border border-[#6BD28E]/30 bg-[#6BD28E]/10 p-4 flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-[#6BD28E] flex-shrink-0" />
              <p className="text-sm text-[#F4EFE5]">{successMsg}</p>
            </motion.div>
          )}

          {/* Error */}
          {error && (
            <div className="rounded-xl border border-[#6E2634]/40 bg-[#6E2634]/10 p-4 flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-[#E25C6F] flex-shrink-0" />
              <p className="text-sm text-[#F4EFE5]">{error}</p>
            </div>
          )}

          {/* Reason Input */}
          <div className="rounded-2xl border border-[#2A2E2B] bg-[#1D211F]/80 p-5">
            <label className="block text-sm font-semibold text-[#F4EFE5] mb-2">
              Nomination Reason <span className="text-[#E25C6F]">*</span>
            </label>
            <textarea
              value={reason}
              onChange={e => setReason(e.target.value)}
              placeholder="State the basis for judicial appointment (e.g., 10 years of legal practice, expertise in constitutional law...)"
              rows={3}
              className="w-full rounded-xl border border-[#2A2E2B] bg-[#151716] px-4 py-3 text-sm text-[#F4EFE5] placeholder-[#6B6B60] focus:outline-none focus:border-[#B59A68]/60 focus:ring-1 focus:ring-[#B59A68]/30 resize-none transition-colors"
            />
          </div>

          {/* Search */}
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B6B60]" />
              <input
                type="text"
                value={search}
                onChange={e => setSearch(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && load(search)}
                placeholder="Search by name or email..."
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#2A2E2B] bg-[#1D211F] text-sm text-[#F4EFE5] placeholder-[#6B6B60] focus:outline-none focus:border-[#B59A68]/50 transition-colors"
              />
            </div>
            <button
              onClick={() => load(search)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-[#2A2E2B] bg-[#1D211F] text-xs font-semibold text-[#A9A49A] hover:text-[#F4EFE5] hover:border-[#B59A68]/40 transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              Search
            </button>
          </div>

          {/* Results */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs text-[#A9A49A] font-mono">{total} eligible candidate{total !== 1 ? 's' : ''} found</p>
              <div className="flex items-center gap-1.5 text-xs text-[#A9A49A]">
                <Info className="w-3.5 h-3.5" />
                <span>Select a candidate to nominate</span>
              </div>
            </div>

            <div className="space-y-3">
              {isLoading ? (
                [...Array(4)].map((_, i) => (
                  <div key={i} className="rounded-xl border border-[#2A2E2B] bg-[#1D211F]/80 p-4 h-20 animate-pulse" />
                ))
              ) : eligibles.length === 0 ? (
                <div className="rounded-2xl border border-[#2A2E2B] bg-[#1D211F]/80 p-12 text-center">
                  <UserCheck className="w-12 h-12 text-[#3B3A33] mx-auto mb-4" />
                  <p className="text-[#A9A49A] text-sm">No eligible candidates found.</p>
                </div>
              ) : (
                eligibles.map((user, i) => {
                  const isSelected = selectedId === user.id;
                  const isPromotingThis = promoting === user.id;
                  return (
                    <motion.div
                      key={user.id}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.04 }}
                      className={`rounded-xl border transition-all ${
                        isSelected
                          ? 'border-[#B59A68]/50 bg-[#B59A68]/8'
                          : 'border-[#2A2E2B] bg-[#1D211F]/80 hover:border-[#3B3A33]'
                      }`}
                    >
                      <button
                        className="w-full flex items-center gap-4 p-4 text-left"
                        onClick={() => setSelectedId(isSelected ? null : user.id)}
                      >
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#B59A68]/30 to-[#4F8EF7]/20 border border-[#B59A68]/30 flex items-center justify-center flex-shrink-0">
                          <span className="text-sm font-bold text-[#B59A68]">
                            {user.full_name.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-[#F4EFE5] text-sm">{user.full_name}</p>
                          <p className="text-xs text-[#A9A49A] truncate">{user.email}</p>
                          {user.organization && (
                            <p className="text-xs text-[#6B6B60] truncate">{user.organization}</p>
                          )}
                        </div>
                        <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
                          <span className={`text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded ${
                            user.role === 'ADVOCATE'
                              ? 'bg-[#4F8EF7]/15 text-[#4F8EF7] border border-[#4F8EF7]/30'
                              : 'bg-[#6B6B60]/15 text-[#A9A49A] border border-[#6B6B60]/30'
                          }`}>
                            {user.role}
                          </span>
                          <span className="text-[10px] text-[#6B6B60]">Since {formatDate(user.created_at)}</span>
                          <ChevronRight className={`w-4 h-4 text-[#6B6B60] transition-transform ${isSelected ? 'rotate-90' : ''}`} />
                        </div>
                      </button>

                      {/* Expanded nominate action */}
                      {isSelected && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          className="border-t border-[#B59A68]/20 px-4 pb-4 pt-3 flex items-center justify-between gap-4"
                        >
                          <p className="text-xs text-[#A9A49A]">
                            Appoint <strong className="text-[#F4EFE5]">{user.full_name}</strong> as a Judge?
                            This will create a permanent judicial audit record.
                          </p>
                          <button
                            onClick={() => handlePromote(user.id, user.full_name)}
                            disabled={!!promoting || !reason.trim()}
                            className="flex items-center gap-2 px-5 py-2 rounded-xl bg-[#B59A68] hover:bg-[#C9A87A] text-[#151716] text-xs font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
                          >
                            {isPromotingThis ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Scale className="w-4 h-4" />
                            )}
                            {isPromotingThis ? 'Nominating...' : 'Confirm Appointment'}
                          </button>
                        </motion.div>
                      )}
                    </motion.div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>
    </RoleGuard>
  );
}
