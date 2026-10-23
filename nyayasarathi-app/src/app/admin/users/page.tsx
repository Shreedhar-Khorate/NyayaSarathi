'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users,
  Search,
  Filter,
  Shield,
  Scale,
  UserCheck,
  UserX,
  AlertCircle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Loader2,
  X,
  ArrowRight,
  RefreshCw,
  Building2,
  Briefcase,
  History,
} from 'lucide-react';
import { RoleGuard } from '@/components/auth/RoleGuard';
import { Navbar, Footer } from '@/components/layout/NavAndFooter';
import {
  fetchAdminUsers,
  updateUserRole,
  getUser,
  type AdminUserItem,
} from '@/lib/auth';

const ROLES = ['ALL', 'USER', 'ADVOCATE', 'ADMIN'];

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUserItem[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [selectedRole, setSelectedRole] = useState('ALL');
  const [page, setPage] = useState(0);
  const limit = 20;

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Modal State for Role Change
  const [targetUser, setTargetUser] = useState<AdminUserItem | null>(null);
  const [newRole, setNewRole] = useState<string>('ADVOCATE');
  const [reason, setReason] = useState<string>('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  const currentAdmin = getUser();

  const loadUsers = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchAdminUsers(
        search,
        selectedRole === 'ALL' ? undefined : selectedRole,
        limit,
        page * limit
      );
      setUsers(data.items);
      setTotal(data.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load user list.');
    } finally {
      setIsLoading(false);
    }
  }, [search, selectedRole, page]);

  useEffect(() => {
    const timer = setTimeout(() => {
      loadUsers();
    }, 250);
    return () => clearTimeout(timer);
  }, [loadUsers]);

  const handleOpenRoleModal = (user: AdminUserItem) => {
    setTargetUser(user);
    if (user.role === 'USER') {
      setNewRole('ADVOCATE');
    } else {
      setNewRole('USER');
    }
    setReason('');
    setModalError(null);
  };

  const handleCloseModal = () => {
    setTargetUser(null);
    setModalError(null);
  };

  const handleConfirmRoleChange = async () => {
    if (!targetUser) return;

    if (!reason.trim()) {
      setModalError('Please state an administrative reason for the audit trail.');
      return;
    }

    setIsUpdating(true);
    setModalError(null);

    try {
      await updateUserRole(targetUser.id, newRole, reason);
      setSuccessMsg(
        `Successfully changed role for ${targetUser.full_name || targetUser.email} to ${newRole}.`
      );
      handleCloseModal();
      loadUsers();
    } catch (err: unknown) {
      setModalError(err instanceof Error ? err.message : 'Role modification failed.');
    } finally {
      setIsUpdating(false);
    }
  };

  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <RoleGuard allowedRoles={['ADMIN']} portalName="User Role Management">
      <div className="min-h-screen bg-[#151716] flex flex-col justify-between">
        <Navbar />
        <div className="flex-1 pt-28 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto space-y-6">

          {/* Breadcrumb & Navigation */}
          <div className="flex items-center gap-2 text-xs text-[#A9A49A]">
            <Link href="/admin/dashboard" className="hover:text-[#B59A68] transition-colors">
              Admin Dashboard
            </Link>
            <span>/</span>
            <span className="text-[#F4EFE5]">User Management</span>
          </div>

          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-[#3B3A33]/80 pb-6">
            <div>
              <h1 className="font-display text-3xl font-bold text-[#F4EFE5] tracking-tight">
                User Role Management
              </h1>
              <p className="font-sans text-sm text-[#A9A49A] mt-1">
                Assign and revoke legal credentials, manage advocate clearances, and maintain platform security.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Link
                href="/admin/audit-logs"
                className="flex items-center gap-2 rounded-xl border border-[#3B3A33] bg-[#1D211F] px-4 py-2 font-sans text-xs font-semibold text-[#F4EFE5] hover:border-[#B59A68]/60 transition-colors"
              >
                <History className="w-3.5 h-3.5 text-[#B59A68]" />
                <span>View Audit History</span>
              </Link>
            </div>
          </div>

          {/* Alerts */}
          {successMsg && (
            <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 p-4 flex items-center justify-between text-xs text-emerald-400">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>{successMsg}</span>
              </div>
              <button onClick={() => setSuccessMsg(null)}>
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {error && (
            <div className="rounded-xl border border-[#6E2634] bg-[#6E2634]/20 p-4 flex items-center gap-2 text-xs text-[#E25C6F]">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Search & Filter Toolbar */}
          <div className="rounded-2xl border border-[#3B3A33] bg-[#1D211F]/70 p-4 flex flex-col sm:flex-row items-center gap-4 justify-between backdrop-blur-md">
            {/* Search */}
            <div className="relative w-full sm:w-96">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#A9A49A]" />
              <input
                type="text"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(0);
                }}
                placeholder="Search by advocate name or email..."
                className="w-full rounded-xl border border-[#3B3A33] bg-[#151716] pl-10 pr-4 py-2 text-xs text-[#F4EFE5] placeholder-[#A9A49A]/60 focus:border-[#B59A68] focus:outline-none transition-colors"
              />
            </div>

            {/* Role Filter Tabs */}
            <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
              <span className="text-xs text-[#A9A49A] flex items-center gap-1 mr-1 shrink-0 font-mono">
                <Filter className="w-3 h-3 text-[#B59A68]" />
                Role:
              </span>
              {ROLES.map((r) => (
                <button
                  key={r}
                  onClick={() => {
                    setSelectedRole(r);
                    setPage(0);
                  }}
                  className={`px-3 py-1.5 rounded-lg text-xs font-mono uppercase font-semibold transition-colors shrink-0 ${
                    selectedRole === r
                      ? 'bg-[#6E2634]/40 text-[#B59A68] border border-[#B59A68]/50 shadow-sm'
                      : 'text-[#A9A49A] hover:bg-white/[0.04] hover:text-[#F4EFE5]'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          {/* Users Table */}
          <div className="rounded-2xl border border-[#3B3A33] bg-[#1D211F]/60 overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-[#F4EFE5]">
                <thead className="border-b border-[#3B3A33] text-[#A9A49A] font-mono uppercase text-[10px] bg-[#151716]/60">
                  <tr>
                    <th className="py-3.5 px-4">User</th>
                    <th className="py-3.5 px-4">Role</th>
                    <th className="py-3.5 px-4">Organization & Chambers</th>
                    <th className="py-3.5 px-4">Registered</th>
                    <th className="py-3.5 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#3B3A33]/40">
                  {isLoading ? (
                    <tr>
                      <td colSpan={5} className="py-12 text-center text-[#A9A49A]">
                        <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-[#B59A68]" />
                        <span>Loading user directory...</span>
                      </td>
                    </tr>
                  ) : users.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-12 text-center text-[#A9A49A]">
                        No users found matching your filters.
                      </td>
                    </tr>
                  ) : (
                    users.map((u) => {
                      const isSelf = currentAdmin?.id === u.id;
                      const isAdmin = u.role === 'ADMIN';
                      const isAdvocate = u.role === 'ADVOCATE';

                      return (
                        <tr key={u.id} className="hover:bg-white/[0.02] transition-colors">
                          <td className="py-3.5 px-4">
                            <div className="font-semibold text-[#F4EFE5] flex items-center gap-2">
                              <span>{u.full_name || 'Anonymous User'}</span>
                              {isSelf && (
                                <span className="px-1.5 py-0.2 rounded text-[9px] font-mono bg-blue-500/20 text-blue-400 border border-blue-500/30">
                                  You
                                </span>
                              )}
                            </div>
                            <div className="text-[11px] text-[#A9A49A] font-mono">{u.email}</div>
                          </td>

                          <td className="py-3.5 px-4">
                            <span
                              className={`px-2.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                                isAdmin
                                  ? 'bg-[#B59A68]/20 text-[#B59A68] border border-[#B59A68]/40'
                                  : isAdvocate
                                  ? 'bg-[#6E2634]/30 text-[#E25C6F] border border-[#6E2634]/50'
                                  : 'bg-[#242925] text-[#A9A49A] border border-[#3B3A33]'
                              }`}
                            >
                              {u.role}
                            </span>
                          </td>

                          <td className="py-3.5 px-4 text-[#A9A49A]">
                            <div className="text-[#F4EFE5]">{u.organization || 'General Public'}</div>
                            <div className="text-[11px]">{u.designation || 'Researcher'}</div>
                          </td>

                          <td className="py-3.5 px-4 text-[#A9A49A] font-mono">
                            {new Date(u.created_at).toLocaleDateString()}
                          </td>

                          <td className="py-3.5 px-4 text-right">
                            {isAdmin ? (
                              <span className="text-[11px] text-[#A9A49A] italic">Protected Admin</span>
                            ) : (
                              <button
                                onClick={() => handleOpenRoleModal(u)}
                                className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all inline-flex items-center gap-1.5 bg-[#B59A68]/15 text-[#B59A68] hover:bg-[#B59A68]/30 border border-[#B59A68]/40"
                              >
                                <Shield className="w-3.5 h-3.5" />
                                <span>Modify Role</span>
                              </button>
                            )}
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
                Showing <span className="font-semibold text-[#F4EFE5]">{users.length}</span> of{' '}
                <span className="font-semibold text-[#F4EFE5]">{total}</span> users
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

          {/* Role Change Modal */}
          <AnimatePresence>
            {targetUser && (
              <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="w-full max-w-lg rounded-2xl border border-[#3B3A33] bg-[#1D211F] p-6 shadow-2xl space-y-5"
                >
                  {/* Modal Header */}
                  <div className="flex items-center justify-between border-b border-[#3B3A33] pb-4">
                    <div className="flex items-center gap-2.5">
                      <div className="w-9 h-9 rounded-xl bg-[#6E2634]/20 border border-[#B59A68]/40 flex items-center justify-center">
                        <Shield className="w-5 h-5 text-[#B59A68]" />
                      </div>
                      <div>
                        <h3 className="font-display text-lg font-bold text-[#F4EFE5]">
                          Modify User Role Clearance
                        </h3>
                        <p className="text-[11px] text-[#A9A49A]">
                          Action will be immutably recorded in the institutional audit log.
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={handleCloseModal}
                      className="text-[#A9A49A] hover:text-[#F4EFE5] transition-colors"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>

                  {modalError && (
                    <div className="rounded-xl border border-[#6E2634] bg-[#6E2634]/20 p-3 flex items-center gap-2 text-xs text-[#E25C6F]">
                      <AlertCircle className="w-4 h-4 shrink-0" />
                      <span>{modalError}</span>
                    </div>
                  )}

                  {/* Target Details */}
                  <div className="rounded-xl border border-[#3B3A33] bg-[#151716] p-4 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-[#A9A49A]">Target Account:</span>
                      <span className="font-semibold text-[#F4EFE5]">{targetUser.full_name || 'Anonymous'}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="text-[#A9A49A]">Email Address:</span>
                      <span className="text-[#B59A68]">{targetUser.email}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-[#A9A49A]">Current Clearance:</span>
                      <span className="font-mono font-bold uppercase text-[#E25C6F]">
                        {targetUser.role}
                      </span>
                    </div>
                  </div>

                  {/* New Role Selector */}
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-[#F4EFE5]">
                      Select Desired Role
                    </label>
                    <div className="grid grid-cols-3 gap-2.5">
                      <button
                        type="button"
                        onClick={() => setNewRole('USER')}
                        className={`p-3 rounded-xl border text-left transition-all ${
                          newRole === 'USER'
                            ? 'bg-[#6E2634]/30 border-[#B59A68] text-[#F4EFE5]'
                            : 'border-[#3B3A33] bg-[#151716] text-[#A9A49A] hover:border-[#B59A68]/40'
                        }`}
                      >
                        <div className="font-semibold text-xs flex items-center gap-1.5">
                          <Users className="w-3.5 h-3.5 text-[#71877A]" />
                          <span>USER</span>
                        </div>
                        <div className="text-[10px] text-[#A9A49A] mt-1">
                          Standard research clearance for citizens and researchers.
                        </div>
                      </button>

                      <button
                        type="button"
                        onClick={() => setNewRole('ADVOCATE')}
                        className={`p-3 rounded-xl border text-left transition-all ${
                          newRole === 'ADVOCATE'
                            ? 'bg-[#6E2634]/30 border-[#B59A68] text-[#F4EFE5]'
                            : 'border-[#3B3A33] bg-[#151716] text-[#A9A49A] hover:border-[#B59A68]/40'
                        }`}
                      >
                        <div className="font-semibold text-xs flex items-center gap-1.5">
                          <Briefcase className="w-3.5 h-3.5 text-[#B59A68]" />
                          <span>ADVOCATE</span>
                        </div>
                        <div className="text-[10px] text-[#A9A49A] mt-1">
                          Practicing counsel clearance for case dockets and filings.
                        </div>
                      </button>

                      <button
                        type="button"
                        onClick={() => setNewRole('ADMIN')}
                        className={`p-3 rounded-xl border text-left transition-all ${
                          newRole === 'ADMIN'
                            ? 'bg-[#6E2634]/30 border-[#B59A68] text-[#F4EFE5]'
                            : 'border-[#3B3A33] bg-[#151716] text-[#A9A49A] hover:border-[#B59A68]/40'
                        }`}
                      >
                        <div className="font-semibold text-xs flex items-center gap-1.5">
                          <Shield className="w-3.5 h-3.5 text-[#8A3545]" />
                          <span>ADMIN</span>
                        </div>
                        <div className="text-[10px] text-[#A9A49A] mt-1">
                          Platform administrator clearance with governance access.
                        </div>
                      </button>
                    </div>
                  </div>

                  {/* Reason Input */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-[#F4EFE5]">
                      Administrative Reason <span className="text-[#B59A68]">*</span>
                    </label>
                    <textarea
                      rows={3}
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                      placeholder="e.g. Verified Bar Council enrollment; Promoted to Senior Legal Counsel."
                      className="w-full rounded-xl border border-[#3B3A33] bg-[#151716] p-3 text-xs text-[#F4EFE5] placeholder-[#A9A49A]/50 focus:border-[#B59A68] focus:outline-none transition-colors"
                    />
                  </div>

                  {/* Modal Actions */}
                  <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#3B3A33]">
                    <button
                      type="button"
                      onClick={handleCloseModal}
                      disabled={isUpdating}
                      className="px-4 py-2 rounded-xl border border-[#3B3A33] text-xs font-semibold text-[#A9A49A] hover:text-[#F4EFE5] transition-colors"
                    >
                      Cancel
                    </button>

                    <button
                      type="button"
                      onClick={handleConfirmRoleChange}
                      disabled={isUpdating}
                      className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#6E2634] to-[#8A3545] border border-[#B59A68]/40 px-5 py-2 text-xs font-semibold text-[#F4EFE5] shadow-lg shadow-[#6E2634]/20 hover:brightness-110 disabled:opacity-50 transition-all"
                    >
                      {isUpdating && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                      <span>Confirm & Apply Change</span>
                    </button>
                  </div>
                </motion.div>
              </div>
            )}
          </AnimatePresence>
        </div>
        </div>
        <Footer />
      </div>
    </RoleGuard>
  );
}
