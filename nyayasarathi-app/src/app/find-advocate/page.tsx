'use client';

/**
 * NyayaSarathi — Find an Advocate Directory
 * Route: /find-advocate
 * Allows authenticated users to browse eligible advocates, search by name/specialization,
 * and initiate or resume secure 1-on-1 chat threads.
 */

import React, { useEffect, useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users,
  Search,
  MessageCircle,
  Briefcase,
  Building2,
  AlertCircle,
  RefreshCw,
  Loader2,
  CheckCircle2,
  Shield,
  ArrowRight,
  User,
  Sparkles,
} from 'lucide-react';
import { RoleGuard } from '@/components/auth/RoleGuard';
import { getUser } from '@/lib/auth';
import {
  fetchAdvocates,
  createOrGetConversation,
  type AdvocateProfile,
} from '@/lib/chat';
import { UserAvatar } from '@/components/ui/UserAvatar';

const EASE = [0.16, 1, 0.3, 1] as const;
const ALLOWED_ROLES = ['USER', 'ADVOCATE', 'ADMIN'];
let memoryAdvocatesCache: AdvocateProfile[] | null = null;

export default function FindAdvocatePage() {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [advocates, setAdvocates] = useState<AdvocateProfile[]>(() => memoryAdvocatesCache || []);
  const [loading, setLoading] = useState(() => !memoryAdvocatesCache);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [initiatingId, setInitiatingId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    setCurrentUser(getUser());
    loadAdvocates();
  }, []);

  const loadAdvocates = async () => {
    if (!memoryAdvocatesCache) {
      setLoading(true);
    }
    setError(null);
    try {
      const res = await fetchAdvocates();
      const list = res.advocates || [];
      memoryAdvocatesCache = list;
      setAdvocates(list);
    } catch (err: unknown) {
      if (!memoryAdvocatesCache) {
        setError(err instanceof Error ? err.message : 'Failed to load advocate directory.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleStartChat = async (advocateId: string) => {
    if (!currentUser?.id) {
      router.push('/login');
      return;
    }
    if (initiatingId) return; // Prevent duplicate clicks

    setInitiatingId(advocateId);
    setActionError(null);

    try {
      const conv = await createOrGetConversation(currentUser.id, advocateId);
      // Navigate to chat interface with conversation active
      router.push(`/chat?conversationId=${conv.id}`);
    } catch (err: unknown) {
      setActionError(
        err instanceof Error ? err.message : 'Unable to initiate chat with advocate.'
      );
      setInitiatingId(null);
    }
  };

  const filteredAdvocates = useMemo(() => {
    if (!searchQuery.trim()) return advocates;
    const q = searchQuery.toLowerCase().trim();
    return advocates.filter((a) => {
      const name = (a.full_name || '').toLowerCase();
      const org = (a.organization || '').toLowerCase();
      const des = (a.designation || '').toLowerCase();
      return name.includes(q) || org.includes(q) || des.includes(q);
    });
  }, [advocates, searchQuery]);

  return (
    <RoleGuard allowedRoles={ALLOWED_ROLES} portalName="Find an Advocate">
      <div className="min-h-screen bg-[#151716] pt-24 pb-16 px-4 sm:px-6 lg:px-8">
        {/* Ambient glow backgrounds */}
        <div className="fixed inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-1/4 left-1/3 w-[600px] h-[600px] bg-[#4F8EF7]/5 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-[#B59A68]/5 rounded-full blur-3xl" />
        </div>

        <div className="max-w-6xl mx-auto relative z-10">
          {/* Header section */}
          <motion.div
            initial={{ opacity: 0, y: -16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: EASE }}
            className="mb-8"
          >
            <div className="flex items-center gap-2 mb-2 font-mono text-[11px] uppercase tracking-[0.25em] text-[#4F8EF7]">
              <Users className="w-4 h-4 text-[#4F8EF7]" />
              <span>Verified Legal Counsel Directory</span>
            </div>
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
              <div>
                <h1 className="font-display text-3xl sm:text-4xl font-bold text-[#F4EFE5] tracking-tight">
                  Find an Advocate
                </h1>
                <p className="font-sans text-sm text-[#A9A49A] mt-1.5 max-w-2xl">
                  Connect directly with verified Advocates on Record and legal counsel. Initiate private, end-to-end confidential case messaging and document review.
                </p>
              </div>
              <button
                onClick={loadAdvocates}
                disabled={loading}
                className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl border border-[#3B3A33] bg-[#1D211F] text-xs font-semibold text-[#F4EFE5] hover:border-[#B59A68]/60 transition-colors shrink-0 disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 text-[#B59A68] ${loading ? 'animate-spin' : ''}`} />
                <span>Refresh Directory</span>
              </button>
            </div>
          </motion.div>

          {/* Search bar */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1, ease: EASE }}
            className="mb-8"
          >
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#A9A49A]" />
              <input
                id="advocate-search-input"
                type="text"
                placeholder="Search advocates by name, chamber, or designation (e.g. Supreme Court, Commercial Law)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-2xl border border-[#2A2E2B] bg-[#1D211F]/80 pl-11 pr-4 py-3.5 font-sans text-sm text-[#F4EFE5] placeholder-[#A9A49A]/60 focus:border-[#4F8EF7] focus:outline-none focus:ring-1 focus:ring-[#4F8EF7]/30 transition-all backdrop-blur-md"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-mono text-[#A9A49A] hover:text-[#F4EFE5]"
                >
                  Clear
                </button>
              )}
            </div>
          </motion.div>

          {/* Action error banner */}
          {actionError && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 p-4 rounded-xl border border-[#E25C6F]/40 bg-[#6E2634]/30 text-xs text-[#E25C6F] flex items-center justify-between"
            >
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{actionError}</span>
              </div>
              <button
                onClick={() => setActionError(null)}
                className="text-xs underline hover:text-[#F4EFE5]"
              >
                Dismiss
              </button>
            </motion.div>
          )}

          {/* Loading state */}
          {loading && (
            <div className="py-24 flex flex-col items-center justify-center text-center">
              <Loader2 className="w-8 h-8 text-[#4F8EF7] animate-spin mb-3" />
              <p className="text-sm font-semibold text-[#F4EFE5]">Loading Verified Advocates…</p>
              <p className="text-xs text-[#A9A49A] mt-1">Retrieving counsel credentials from Supabase directory</p>
            </div>
          )}

          {/* Error state */}
          {!loading && error && (
            <div className="p-8 rounded-2xl border border-[#6E2634]/50 bg-[#181C1A] text-center max-w-md mx-auto">
              <AlertCircle className="w-10 h-10 text-[#E25C6F] mx-auto mb-3" />
              <h3 className="text-base font-semibold text-[#F4EFE5] mb-1">Unable to Load Directory</h3>
              <p className="text-xs text-[#A9A49A] mb-4">{error}</p>
              <button
                onClick={loadAdvocates}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#6E2634] hover:bg-[#8A3545] text-xs font-semibold text-[#F4EFE5] transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Try Again</span>
              </button>
            </div>
          )}

          {/* Empty state: No advocates registered */}
          {!loading && !error && advocates.length === 0 && (
            <div className="p-12 rounded-2xl border border-[#2A2E2B] bg-[#181C1A] text-center max-w-md mx-auto">
              <Users className="w-12 h-12 text-[#3B3A33] mx-auto mb-3" />
              <h3 className="text-base font-semibold text-[#F4EFE5] mb-1">No Advocates Available Yet</h3>
              <p className="text-xs text-[#A9A49A]">
                There are currently no verified advocates listed in the directory. Please check back shortly or contact support.
              </p>
            </div>
          )}

          {/* Empty state: Search query yielded 0 results */}
          {!loading && !error && advocates.length > 0 && filteredAdvocates.length === 0 && (
            <div className="p-12 rounded-2xl border border-[#2A2E2B] bg-[#181C1A] text-center max-w-md mx-auto">
              <Search className="w-10 h-10 text-[#3B3A33] mx-auto mb-3" />
              <h3 className="text-base font-semibold text-[#F4EFE5] mb-1">No Matching Advocates</h3>
              <p className="text-xs text-[#A9A49A] mb-4">
                No advocates found matching &ldquo;{searchQuery}&rdquo;. Try another name or chamber keyword.
              </p>
              <button
                onClick={() => setSearchQuery('')}
                className="px-3.5 py-1.5 rounded-xl border border-[#3B3A33] text-xs font-semibold text-[#F4EFE5] hover:bg-[#1D211F]"
              >
                Clear Search Filter
              </button>
            </div>
          )}

          {/* Advocate Cards Grid */}
          {!loading && !error && filteredAdvocates.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {filteredAdvocates.map((adv, idx) => {
                const isInitiating = initiatingId === adv.id;
                const isSelf = currentUser?.id === adv.id;

                return (
                  <motion.div
                    key={adv.id}
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: idx * 0.04, ease: EASE }}
                    className="flex flex-col justify-between p-6 rounded-2xl border border-[#2A2E2B] bg-[#181C1A]/80 hover:bg-[#1D211F] hover:border-[#3B3A33] transition-all backdrop-blur-md shadow-sm group"
                  >
                    <div>
                      {/* Top badge & Avatar */}
                      <div className="flex items-start justify-between gap-3 mb-4">
                        <div className="flex items-center gap-3">
                          <UserAvatar
                            avatarUrl={adv.avatar_url}
                            name={adv.full_name}
                            email={adv.email}
                            size="md"
                          />
                          <div>
                            <h3 className="font-display text-base font-semibold text-[#F4EFE5] group-hover:text-[#4F8EF7] transition-colors leading-tight">
                              {adv.full_name}
                            </h3>
                            <span className="inline-flex items-center gap-1 mt-1 text-[10px] font-mono uppercase tracking-wider text-[#6BD28E] bg-[#6BD28E]/10 border border-[#6BD28E]/30 px-2 py-0.5 rounded-full">
                              <CheckCircle2 className="w-2.5 h-2.5" />
                              <span>Verified Advocate</span>
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Details */}
                      <div className="space-y-2 mb-6 pt-2 border-t border-[#2A2E2B]/60 text-xs">
                        <div className="flex items-center gap-2 text-[#A9A49A]">
                          <Building2 className="w-3.5 h-3.5 text-[#B59A68] shrink-0" />
                          <span className="truncate">{adv.organization || 'Independent Chambers'}</span>
                        </div>
                        <div className="flex items-center gap-2 text-[#A9A49A]">
                          <Briefcase className="w-3.5 h-3.5 text-[#4F8EF7] shrink-0" />
                          <span className="truncate">{adv.designation || 'Advocate on Record'}</span>
                        </div>
                        <div className="flex items-center gap-2 text-[#A9A49A]">
                          <Shield className="w-3.5 h-3.5 text-[#6BD28E] shrink-0" />
                          <span className="truncate">NyayaSarathi Verified Bar Member</span>
                        </div>
                      </div>
                    </div>

                    {/* Action button */}
                    <button
                      id={`chat-btn-${adv.id}`}
                      onClick={() => handleStartChat(adv.id)}
                      disabled={isInitiating || isSelf}
                      className={`w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl font-sans text-xs font-bold transition-all shadow-sm ${
                        isSelf
                          ? 'border border-[#3B3A33] bg-[#1D211F] text-[#A9A49A] cursor-not-allowed'
                          : 'bg-[#4F8EF7] hover:bg-[#3B7BE5] text-white active:scale-[0.98]'
                      } disabled:opacity-60`}
                    >
                      {isInitiating ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          <span>Opening Conversation…</span>
                        </>
                      ) : isSelf ? (
                        <span>Your Advocate Profile</span>
                      ) : (
                        <>
                          <MessageCircle className="w-3.5 h-3.5" />
                          <span>Chat with Advocate</span>
                          <ArrowRight className="w-3 h-3 ml-0.5 group-hover:translate-x-0.5 transition-transform" />
                        </>
                      )}
                    </button>
                  </motion.div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </RoleGuard>
  );
}
