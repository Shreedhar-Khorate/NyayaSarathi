'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Scale,
  User,
  Building2,
  Briefcase,
  Calendar,
  Shield,
  Edit3,
  CheckCircle2,
  Clock,
  Trash2,
  LogOut,
  ExternalLink,
  Loader2,
  AlertCircle,
  FileText,
  Search,
  Cpu,
  History,
  Camera,
  Upload,
} from 'lucide-react';
import { UserAvatar } from '@/components/ui/UserAvatar';
import {
  getUser,
  fetchMe,
  updateProfile,
  fetchUserHistory,
  deleteUserActivity,
  removeAuth,
  type UserProfile,
  type ActivityHistoryItem,
} from '@/lib/auth';

const EASE = [0.16, 1, 0.3, 1] as const;

export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [history, setHistory] = useState<ActivityHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isHistoryLoading, setIsHistoryLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'history'>('overview');
  const [historyFilter, setHistoryFilter] = useState<string>('ALL');

  // Form states
  const [fullName, setFullName] = useState('');
  const [organization, setOrganization] = useState('');
  const [designation, setDesignation] = useState('');
  const [avatarUrl, setAvatarUrl] = useState<string | null>('');
  const [isCompressingImage, setIsCompressingImage] = useState(false);
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      try {
        const p = await fetchMe();
        if (!p) {
          router.push('/login');
          return;
        }
        setProfile(p);
        setFullName(p.full_name || '');
        setOrganization(p.organization || '');
        setDesignation(p.designation || '');
        setAvatarUrl(p.avatar_url || '');

        // Load activity history
        loadHistory();
      } catch (err) {
        router.push('/login');
      } finally {
        setIsLoading(false);
      }
    }

    loadData();
  }, [router]);

  const loadHistory = async (filter?: string) => {
    setIsHistoryLoading(true);
    try {
      const type = filter && filter !== 'ALL' ? filter : undefined;
      const items = await fetchUserHistory(type);
      setHistory(items);
    } catch {
      // Graceful fallback
    } finally {
      setIsHistoryLoading(false);
    }
  };

  const handleFilterChange = (f: string) => {
    setHistoryFilter(f);
    loadHistory(f);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setFeedbackMsg({ type: 'error', text: 'Please select a valid image file (JPG, PNG, WebP).' });
      return;
    }

    // Limit original size to 10MB
    if (file.size > 10 * 1024 * 1024) {
      setFeedbackMsg({ type: 'error', text: 'Selected image is too large. Please select an image under 10MB.' });
      return;
    }

    setIsCompressingImage(true);
    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new Image();
      img.onload = () => {
        // High-quality canvas scaling to max 256x256
        const canvas = document.createElement('canvas');
        const maxDim = 256;
        let width = img.width;
        let height = img.height;

        if (width > height) {
          if (width > maxDim) {
            height = Math.round((height * maxDim) / width);
            width = maxDim;
          }
        } else {
          if (height > maxDim) {
            width = Math.round((width * maxDim) / height);
            height = maxDim;
          }
        }

        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.drawImage(img, 0, 0, width, height);
          const compressedDataUrl = canvas.toDataURL('image/jpeg', 0.85);
          setAvatarUrl(compressedDataUrl);
          setFeedbackMsg({ type: 'success', text: 'Photo ready to save! Click "Save Changes" to update.' });
        }
        setIsCompressingImage(false);
      };
      img.onerror = () => {
        setFeedbackMsg({ type: 'error', text: 'Unable to process the image file.' });
        setIsCompressingImage(false);
      };
      img.src = event.target?.result as string;
    };
    reader.onerror = () => {
      setFeedbackMsg({ type: 'error', text: 'Failed to read image file.' });
      setIsCompressingImage(false);
    };
    reader.readAsDataURL(file);
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setFeedbackMsg(null);
    try {
      const cleanAvatar = avatarUrl && avatarUrl.trim() ? avatarUrl.trim() : null;
      const updated = await updateProfile({
        full_name: fullName.trim(),
        organization: organization.trim(),
        designation: designation.trim(),
        avatar_url: cleanAvatar,
      });
      setProfile(updated);
      setIsEditing(false);
      setFeedbackMsg({ type: 'success', text: 'Profile updated successfully.' });
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Failed to update profile.' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteActivity = async (id: string) => {
    try {
      const ok = await deleteUserActivity(id);
      if (ok) {
        setHistory((prev) => prev.filter((item) => item.id !== id));
      }
    } catch {
      // Non-blocking
    }
  };

  const handleSignOut = () => {
    removeAuth();
    router.push('/login');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#151716] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#B59A68]" />
      </div>
    );
  }

  const roleBadgeColors: Record<string, string> = {
    ADMIN: 'border-[#8A3545] bg-[#6E2634]/30 text-[#F4EFE5]',
    USER: 'border-[#3B3A33] bg-[#1D211F] text-[#A9A49A]',
    ADVOCATE: 'border-[#B59A68]/60 bg-[#1D211F] text-[#F4EFE5]',
    DEACTIVATED_JUDGE: 'border-amber-500/30 bg-amber-500/10 text-amber-400 line-through',
  };

  return (
    <div className="min-h-screen bg-[#151716] text-[#F4EFE5] pb-24 selection:bg-[#6E2634] selection:text-[#F4EFE5]">
      {/* Background Architectural Grid */}
      <div
        className="pointer-events-none fixed inset-0 z-0 opacity-20 bg-[radial-gradient(#3B3A33_1px,transparent_1px)] [background-size:32px_32px]"
        aria-hidden="true"
      />

      {/* Hero Header */}
      <div className="relative z-10 border-b border-[#3B3A33]/60 bg-[#181C1A]/60 backdrop-blur-md pt-28 pb-10 px-6 sm:px-10 lg:px-16">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-5">
            {/* Avatar with Google/Gmail monogram fallback & photo upload */}
            <div className="relative group">
              <UserAvatar
                avatarUrl={profile?.avatar_url}
                name={profile?.full_name}
                email={profile?.email}
                size="xl"
                showOnlineBadge={true}
              />
              <button
                type="button"
                onClick={() => setIsEditing(true)}
                className="absolute inset-0 rounded-2xl bg-black/60 opacity-0 group-hover:opacity-100 flex flex-col items-center justify-center transition-opacity text-[10px] font-sans text-white/90 gap-1 backdrop-blur-xs cursor-pointer"
                title="Change Photo"
              >
                <Camera className="w-5 h-5 text-[#B59A68]" />
                <span>Change</span>
              </button>
            </div>

            <div>
              <div className="flex items-center gap-2.5 mb-1">
                <h1 className="font-display text-2xl sm:text-3xl font-medium text-[#F4EFE5]">
                  {profile?.full_name}
                </h1>
                <span
                  className={`text-[10px] font-mono uppercase px-2.5 py-0.5 rounded-full border ${
                    roleBadgeColors[profile?.role || 'USER'] || roleBadgeColors.USER
                  }`}
                >
                  {profile?.role}
                </span>
              </div>
              <p className="font-sans text-xs sm:text-sm text-[#A9A49A]">
                {profile?.email}
              </p>
              {(profile?.designation || profile?.organization) && (
                <p className="font-sans text-xs text-[#B59A68] mt-1 flex items-center gap-2">
                  <span>{profile?.designation}</span>
                  {profile?.organization && <span>&bull;</span>}
                  <span>{profile?.organization}</span>
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={() => setIsEditing(!isEditing)}
              className="flex items-center gap-2 rounded-xl border border-[#3B3A33] bg-[#1D211F] px-4 py-2.5 font-sans text-xs font-semibold text-[#F4EFE5] hover:bg-[#242925] hover:border-[#B59A68]/50 transition-colors"
            >
              <Edit3 className="w-3.5 h-3.5 text-[#B59A68]" />
              <span>{isEditing ? 'Cancel Edit' : 'Edit Profile'}</span>
            </button>
            <button
              onClick={handleSignOut}
              className="flex items-center gap-2 rounded-xl border border-[#8A3545]/40 bg-[#6E2634]/15 px-4 py-2.5 font-sans text-xs font-semibold text-[#F4EFE5] hover:bg-[#8A3545]/30 transition-colors"
            >
              <LogOut className="w-3.5 h-3.5 text-[#8A3545]" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="max-w-6xl mx-auto flex items-center gap-6 mt-8 border-t border-[#3B3A33]/40 pt-4">
          <button
            onClick={() => setActiveTab('overview')}
            className={`font-mono text-xs uppercase tracking-wider pb-1 transition-colors border-b-2 ${
              activeTab === 'overview'
                ? 'border-[#B59A68] text-[#B59A68] font-bold'
                : 'border-transparent text-[#A9A49A] hover:text-[#F4EFE5]'
            }`}
          >
            Profile Overview
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`font-mono text-xs uppercase tracking-wider pb-1 transition-colors border-b-2 flex items-center gap-2 ${
              activeTab === 'history'
                ? 'border-[#B59A68] text-[#B59A68] font-bold'
                : 'border-transparent text-[#A9A49A] hover:text-[#F4EFE5]'
            }`}
          >
            <span>Research & Document History</span>
            <span className="text-[10px] bg-[#1D211F] px-2 py-0.5 rounded-full border border-[#3B3A33]">
              {history.length}
            </span>
          </button>
        </div>
      </div>

      {/* Main Container */}
      <div className="relative z-10 max-w-6xl mx-auto px-6 sm:px-10 lg:px-16 mt-8">
        {feedbackMsg && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            className={`mb-6 p-4 rounded-xl border text-xs flex items-center gap-2.5 ${
              feedbackMsg.type === 'success'
                ? 'bg-[#34A853]/10 border-[#34A853]/40 text-[#34A853]'
                : 'bg-[#6E2634]/15 border-[#8A3545]/60 text-[#F4EFE5]'
            }`}
          >
            {feedbackMsg.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 shrink-0" />
            )}
            <span>{feedbackMsg.text}</span>
          </motion.div>
        )}

        {/* Tab 1: Overview */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Left Column: Details or Edit Form */}
            <div className="lg:col-span-8">
              {isEditing ? (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-[#181C1A]/80 border border-[#3B3A33] rounded-2xl p-6 sm:p-8 backdrop-blur-md"
                >
                  <h2 className="font-display text-lg font-medium text-[#F4EFE5] mb-5">
                    Update Profile Details
                  </h2>
                  <form onSubmit={handleUpdate} className="space-y-4">
                    <div>
                      <label className="block font-mono text-[11px] uppercase tracking-wider text-[#A9A49A] mb-1.5">
                        Full Name
                      </label>
                      <input
                        type="text"
                        required
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        className="w-full rounded-xl border border-[#3B3A33] bg-[#1D211F] px-4 py-2.5 font-sans text-sm text-[#F4EFE5] focus:border-[#B59A68] focus:outline-none"
                      />
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="block font-mono text-[11px] uppercase tracking-wider text-[#A9A49A] mb-1.5">
                          Organization / Court
                        </label>
                        <input
                          type="text"
                          value={organization}
                          onChange={(e) => setOrganization(e.target.value)}
                          placeholder="e.g. Supreme Court of India"
                          className="w-full rounded-xl border border-[#3B3A33] bg-[#1D211F] px-4 py-2.5 font-sans text-sm text-[#F4EFE5] focus:border-[#B59A68] focus:outline-none"
                        />
                      </div>
                      <div>
                        <label className="block font-mono text-[11px] uppercase tracking-wider text-[#A9A49A] mb-1.5">
                          Designation
                        </label>
                        <input
                          type="text"
                          value={designation}
                          onChange={(e) => setDesignation(e.target.value)}
                          placeholder="e.g. Advocate on Record"
                          className="w-full rounded-xl border border-[#3B3A33] bg-[#1D211F] px-4 py-2.5 font-sans text-sm text-[#F4EFE5] focus:border-[#B59A68] focus:outline-none"
                        />
                      </div>
                    </div>

                    {/* Avatar Customization: Upload Photo from Device or Use Gmail Initial */}
                    <div className="pt-2 pb-2">
                      <label className="block font-mono text-[11px] uppercase tracking-wider text-[#A9A49A] mb-2">
                        Profile Avatar & Photo
                      </label>

                      <div className="flex flex-col sm:flex-row sm:items-center gap-4 p-4 rounded-xl border border-[#3B3A33] bg-[#1D211F]/70">
                        {/* Live Avatar Preview */}
                        <div className="shrink-0">
                          <UserAvatar
                            avatarUrl={avatarUrl}
                            name={fullName || profile?.full_name}
                            email={profile?.email}
                            size="lg"
                          />
                        </div>

                        {/* Upload & Reset Buttons */}
                        <div className="space-y-2 flex-1">
                          <div className="flex flex-wrap items-center gap-2.5">
                            {/* Hidden native file input */}
                            <input
                              type="file"
                              ref={fileInputRef}
                              accept="image/png,image/jpeg,image/webp,image/gif"
                              onChange={handleFileSelect}
                              className="hidden"
                            />

                            <button
                              type="button"
                              onClick={() => fileInputRef.current?.click()}
                              disabled={isCompressingImage}
                              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#6E2634] hover:bg-[#8A3545] text-xs font-semibold text-[#F4EFE5] transition-colors shadow-sm disabled:opacity-50 cursor-pointer"
                            >
                              {isCompressingImage ? (
                                <>
                                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                  <span>Processing…</span>
                                </>
                              ) : (
                                <>
                                  <Upload className="w-3.5 h-3.5" />
                                  <span>Upload Photo from Device</span>
                                </>
                              )}
                            </button>

                            {avatarUrl && (
                              <button
                                type="button"
                                onClick={() => setAvatarUrl('')}
                                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-[#3B3A33] hover:border-[#B59A68]/50 bg-[#151716] text-xs font-medium text-[#A9A49A] hover:text-[#F4EFE5] transition-colors"
                              >
                                <span>Reset to Google Initial</span>
                              </button>
                            )}
                          </div>

                          <p className="font-sans text-[11px] text-[#A9A49A]/80 leading-normal">
                            Take or select a photo from your device (JPG, PNG, WebP) or click reset to show your distinct Google monogram logo.
                          </p>
                        </div>
                      </div>

                      {/* Optional URL input toggle */}
                      <details className="mt-2 text-xs group">
                        <summary className="font-mono text-[10px] uppercase text-[#A9A49A] hover:text-[#B59A68] cursor-pointer select-none">
                          Or specify image URL
                        </summary>
                        <div className="mt-2">
                          <input
                            type="url"
                            value={avatarUrl || ''}
                            onChange={(e) => setAvatarUrl(e.target.value)}
                            placeholder="https://..."
                            className="w-full rounded-xl border border-[#3B3A33] bg-[#1D211F] px-4 py-2 font-sans text-xs text-[#F4EFE5] focus:border-[#B59A68] focus:outline-none"
                          />
                        </div>
                      </details>
                    </div>

                    <div className="flex items-center gap-3 pt-3">
                      <button
                        type="submit"
                        disabled={isSaving}
                        className="flex items-center gap-2 rounded-xl bg-[#6E2634] hover:bg-[#8A3545] text-[#F4EFE5] px-6 py-2.5 font-sans text-sm font-semibold tracking-wide disabled:opacity-50 transition-colors shadow-md"
                      >
                        {isSaving ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>Saving Changes…</span>
                          </>
                        ) : (
                          <span>Save Changes</span>
                        )}
                      </button>
                      <button
                        type="button"
                        onClick={() => setIsEditing(false)}
                        className="px-5 py-2.5 rounded-xl border border-[#3B3A33] text-xs font-semibold text-[#A9A49A] hover:text-[#F4EFE5]"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                </motion.div>
              ) : (
                <div className="bg-[#181C1A]/80 border border-[#3B3A33] rounded-2xl p-6 sm:p-8 backdrop-blur-md space-y-6">
                  <h2 className="font-display text-lg font-medium text-[#F4EFE5]">
                    Account & Credentials
                  </h2>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-[#A9A49A] text-xs font-mono uppercase tracking-wider">
                        <Building2 className="w-3.5 h-3.5 text-[#B59A68]" />
                        <span>Organization / Chambers</span>
                      </div>
                      <p className="font-sans text-sm text-[#F4EFE5]">
                        {profile?.organization || 'Not specified'}
                      </p>
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-[#A9A49A] text-xs font-mono uppercase tracking-wider">
                        <Briefcase className="w-3.5 h-3.5 text-[#B59A68]" />
                        <span>Designation</span>
                      </div>
                      <p className="font-sans text-sm text-[#F4EFE5]">
                        {profile?.designation || 'Not specified'}
                      </p>
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-[#A9A49A] text-xs font-mono uppercase tracking-wider">
                        <Calendar className="w-3.5 h-3.5 text-[#B59A68]" />
                        <span>Member Since</span>
                      </div>
                      <p className="font-sans text-sm text-[#F4EFE5]">
                        {profile?.created_at
                          ? new Date(profile.created_at).toLocaleDateString(undefined, {
                              year: 'numeric',
                              month: 'long',
                              day: 'numeric',
                            })
                          : 'N/A'}
                      </p>
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-[#A9A49A] text-xs font-mono uppercase tracking-wider">
                        <Shield className="w-3.5 h-3.5 text-[#B59A68]" />
                        <span>Profile Status</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {profile?.profile_completed ? (
                          <span className="flex items-center gap-1.5 text-xs text-[#34A853]">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Completed & Verified</span>
                          </span>
                        ) : (
                          <span className="flex items-center gap-1.5 text-xs text-[#FBBC05]">
                            <AlertCircle className="w-3.5 h-3.5" />
                            <span>Incomplete — Action Required</span>
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Right Column: Quick Research Short-cuts */}
            <div className="lg:col-span-4 space-y-4">
              <div className="bg-[#181C1A]/80 border border-[#3B3A33] rounded-2xl p-6 backdrop-blur-md">
                <h3 className="font-mono text-xs uppercase tracking-wider text-[#B59A68] mb-4">
                  Quick Actions
                </h3>
                <div className="space-y-2.5">
                  <Link
                    href="/predictor"
                    className="w-full flex items-center justify-between p-3 rounded-xl border border-[#3B3A33]/70 bg-[#1D211F]/60 hover:bg-[#242925] hover:border-[#B59A68]/40 transition-colors text-xs font-semibold text-[#F4EFE5]"
                  >
                    <div className="flex items-center gap-2.5">
                      <Cpu className="w-4 h-4 text-[#B59A68]" />
                      <span>Judgment Predictor</span>
                    </div>
                    <ExternalLink className="w-3.5 h-3.5 text-[#A9A49A]" />
                  </Link>

                  <Link
                    href="/legal-research"
                    className="w-full flex items-center justify-between p-3 rounded-xl border border-[#3B3A33]/70 bg-[#1D211F]/60 hover:bg-[#242925] hover:border-[#B59A68]/40 transition-colors text-xs font-semibold text-[#F4EFE5]"
                  >
                    <div className="flex items-center gap-2.5">
                      <Search className="w-4 h-4 text-[#B59A68]" />
                      <span>Legal Research RAG</span>
                    </div>
                    <ExternalLink className="w-3.5 h-3.5 text-[#A9A49A]" />
                  </Link>

                  <Link
                    href="/ocr"
                    className="w-full flex items-center justify-between p-3 rounded-xl border border-[#3B3A33]/70 bg-[#1D211F]/60 hover:bg-[#242925] hover:border-[#B59A68]/40 transition-colors text-xs font-semibold text-[#F4EFE5]"
                  >
                    <div className="flex items-center gap-2.5">
                      <FileText className="w-4 h-4 text-[#B59A68]" />
                      <span>Legal Document OCR</span>
                    </div>
                    <ExternalLink className="w-3.5 h-3.5 text-[#A9A49A]" />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Activity History */}
        {activeTab === 'history' && (
          <div className="space-y-6">
            {/* Filter pills */}
            <div className="flex items-center gap-2 flex-wrap">
              {['ALL', 'LEGAL_RESEARCH', 'DOCUMENT_UPLOAD', 'PREDICTION', 'PROFILE_ONBOARDING'].map(
                (filter) => (
                  <button
                    key={filter}
                    onClick={() => handleFilterChange(filter)}
                    className={`font-mono text-xs px-3 py-1.5 rounded-full border transition-colors ${
                      historyFilter === filter
                        ? 'bg-[#B59A68]/20 border-[#B59A68] text-[#B59A68] font-bold'
                        : 'border-[#3B3A33] text-[#A9A49A] hover:bg-[#1D211F] hover:text-[#F4EFE5]'
                    }`}
                  >
                    {filter.replace('_', ' ')}
                  </button>
                )
              )}
            </div>

            {isHistoryLoading ? (
              <div className="py-16 flex items-center justify-center">
                <Loader2 className="w-6 h-6 animate-spin text-[#B59A68]" />
              </div>
            ) : history.length === 0 ? (
              <div className="bg-[#181C1A]/80 border border-[#3B3A33] rounded-2xl p-12 text-center backdrop-blur-md">
                <History className="w-10 h-10 text-[#A9A49A]/40 mx-auto mb-3" />
                <h3 className="font-display text-base text-[#F4EFE5] mb-1">
                  No activity recorded yet
                </h3>
                <p className="font-sans text-xs text-[#A9A49A] max-w-sm mx-auto mb-4">
                  Your legal research queries, document uploads, and case outcome predictions will be securely archived here.
                </p>
                <Link
                  href="/legal-research"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#6E2634] text-xs font-semibold text-[#F4EFE5] hover:bg-[#8A3545] transition-colors"
                >
                  <span>Start Legal Research</span>
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {history.map((item) => {
                  const activityIcons: Record<string, any> = {
                    LEGAL_RESEARCH: Search,
                    DOCUMENT_UPLOAD: FileText,
                    PREDICTION: Cpu,
                    PROFILE_ONBOARDING: User,
                  };
                  const Icon = activityIcons[item.activity_type] || History;

                  return (
                    <motion.div
                      key={item.id}
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="group bg-[#181C1A]/80 border border-[#3B3A33] rounded-xl p-4 flex items-center justify-between gap-4 hover:border-[#B59A68]/40 transition-colors"
                    >
                      <div className="flex items-center gap-4 min-w-0">
                        <div className="w-9 h-9 rounded-lg bg-[#1D211F] border border-[#3B3A33] flex items-center justify-center shrink-0">
                          <Icon className="w-4 h-4 text-[#B59A68]" />
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-[9px] uppercase px-1.5 py-0.5 rounded bg-[#1D211F] border border-[#3B3A33] text-[#A9A49A]">
                              {item.activity_type.replace('_', ' ')}
                            </span>
                            <span className="font-sans text-xs text-[#A9A49A] flex items-center gap-1">
                              <Clock className="w-3 h-3 text-[#A9A49A]/60" />
                              <span>{new Date(item.created_at).toLocaleString()}</span>
                            </span>
                          </div>
                          <p className="font-sans text-sm font-medium text-[#F4EFE5] truncate mt-1">
                            {item.title}
                          </p>
                          {item.query_text && (
                            <p className="font-sans text-xs text-[#A9A49A]/80 line-clamp-1 mt-0.5">
                              &ldquo;{item.query_text}&rdquo;
                            </p>
                          )}
                        </div>
                      </div>

                      <button
                        onClick={() => handleDeleteActivity(item.id)}
                        className="opacity-0 group-hover:opacity-100 p-2 rounded-lg text-[#A9A49A] hover:text-[#8A3545] hover:bg-[#6E2634]/20 transition-all shrink-0"
                        title="Delete history entry"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
